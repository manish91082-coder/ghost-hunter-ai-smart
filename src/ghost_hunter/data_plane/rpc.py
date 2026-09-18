from __future__ import annotations

import asyncio
import itertools
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


class RPCError(RuntimeError):
    pass


@dataclass
class RPCProvider:
    name: str
    url: str
    timeout_seconds: float = 3.0
    failures: int = 0
    successes: int = 0
    ewma_latency_ms: float | None = None
    cooldown_until: float = 0.0
    last_success_at: float | None = None
    last_failure_at: float | None = None
    last_block: int | None = None
    consecutive_stale: int = 0
    rate_limited_until: float = 0.0
    state: str = "active"
    capabilities: set[str] = field(default_factory=set)

    @property
    def healthy(self) -> bool:
        now = time.monotonic()
        return now >= self.cooldown_until and now >= self.rate_limited_until

    @property
    def available(self) -> bool:
        return self.healthy and self.state not in {"quarantined", "disabled"}

    @property
    def score(self) -> float:
        latency = self.ewma_latency_ms or 1000.0
        return latency + min(self.failures, 10) * 10.0 + min(self.consecutive_stale, 10) * 20.0

    def record(self, ok: bool, latency_ms: float, *, error_kind: str | None = None) -> None:
        alpha = 0.25
        self.ewma_latency_ms = latency_ms if self.ewma_latency_ms is None else alpha * latency_ms + (1 - alpha) * self.ewma_latency_ms
        now = time.monotonic()
        if ok:
            self.successes += 1
            self.failures = max(0, self.failures - 1)
            self.last_success_at = now
            self.state = "active"
            return
        self.failures += 1
        self.last_failure_at = now
        if error_kind == "rate_limit":
            self.rate_limited_until = now + min(120.0, 5.0 * 2 ** min(self.failures, 5))
            self.state = "cooldown"
        elif self.failures >= 3:
            self.cooldown_until = now + min(60.0, 2.0 ** min(self.failures, 6))
            self.state = "cooldown"

    def observe_block(self, block_number: int, reference_block: int | None = None) -> None:
        self.last_block = block_number
        if reference_block is not None and reference_block - block_number > 0:
            self.consecutive_stale += 1
            if self.consecutive_stale >= 3:
                self.state = "quarantined"
        else:
            self.consecutive_stale = 0

    def restore_if_ready(self) -> None:
        if self.state in {"cooldown", "probation"} and self.healthy:
            self.state = "active"


class MultiRPC:
    """Autonomous Polygon RPC fleet. Endpoints are retained, rotated, cooled down and recovered."""

    def __init__(self, providers: list[RPCProvider], max_batch: int = 50, *, max_parallel_probes: int = 8):
        if not providers:
            raise ValueError("at least one RPC provider is required")
        self.providers = providers
        self.max_batch = max_batch
        self.max_parallel_probes = max_parallel_probes
        self._rr = itertools.count()

    def _ordered(self, capability: str | None = None) -> list[RPCProvider]:
        candidates = [p for p in self.providers if p.available and (capability is None or not p.capabilities or capability in p.capabilities)]
        if not candidates:
            candidates = [p for p in self.providers if p.state != "disabled"]
        if not candidates:
            raise RPCError("no usable RPC providers remain")
        return sorted(candidates, key=lambda p: (p.score, next(self._rr)))

    async def _post(self, provider: RPCProvider, payload: Any) -> Any:
        started = time.perf_counter()
        error_kind = None
        try:
            async with httpx.AsyncClient(timeout=provider.timeout_seconds) as client:
                response = await client.post(provider.url, json=payload)
                if response.status_code == 429:
                    error_kind = "rate_limit"
                response.raise_for_status()
                data = response.json()
            provider.record(True, (time.perf_counter() - started) * 1000)
            return data
        except Exception as exc:
            provider.record(False, (time.perf_counter() - started) * 1000, error_kind=error_kind)
            raise RPCError(f"{provider.name}: {exc}") from exc

    async def call(self, method: str, params: list[Any] | None = None, *, capability: str | None = None) -> Any:
        request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        errors: list[str] = []
        for provider in self._ordered(capability):
            try:
                data = await self._post(provider, request)
                if "error" in data:
                    raise RPCError(str(data["error"]))
                return data["result"]
            except Exception as exc:
                errors.append(str(exc))
        raise RPCError("all RPC providers failed: " + " | ".join(errors))

    async def batch(self, calls: list[tuple[str, list[Any]]], *, capability: str | None = None) -> list[Any]:
        results: list[Any] = []
        for offset in range(0, len(calls), self.max_batch):
            chunk = calls[offset:offset + self.max_batch]
            payload = [{"jsonrpc": "2.0", "id": offset + i + 1, "method": method, "params": params} for i, (method, params) in enumerate(chunk)]
            errors: list[str] = []
            chunk_result = None
            for provider in self._ordered(capability):
                try:
                    data = await self._post(provider, payload)
                    by_id = {item["id"]: item for item in data}
                    chunk_result = []
                    for i in range(len(chunk)):
                        item = by_id[offset + i + 1]
                        if "error" in item:
                            raise RPCError(str(item["error"]))
                        chunk_result.append(item["result"])
                    break
                except Exception as exc:
                    errors.append(str(exc))
            if chunk_result is None:
                raise RPCError("all RPC providers failed for batch: " + " | ".join(errors))
            results.extend(chunk_result)
        return results

    async def quorum_call(self, method: str, params: list[Any] | None = None, quorum: int = 2, *, capability: str | None = None) -> Any:
        providers = self._ordered(capability)[:max(quorum, 1)]
        values = await asyncio.gather(*(self._post(p, {"jsonrpc": "2.0", "id": i + 1, "method": method, "params": params or []}) for i, p in enumerate(providers)), return_exceptions=True)
        good = [v.get("result") for v in values if isinstance(v, dict) and "result" in v]
        if not good:
            raise RPCError("quorum read returned no successful results")
        if len(set(map(str, good))) != 1:
            raise RPCError(f"provider disagreement for {method}")
        return good[0]

    async def health_snapshot(self) -> list[dict[str, Any]]:
        """Probe every retained endpoint concurrently; failures never delete endpoints."""
        semaphore = asyncio.Semaphore(self.max_parallel_probes)

        async def probe(provider: RPCProvider) -> dict[str, Any]:
            async with semaphore:
                try:
                    block = await self._post(provider, {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []})
                    number = int(block["result"], 16)
                    provider.observe_block(number)
                    provider.restore_if_ready()
                    return {"name": provider.name, "state": provider.state, "block": number, "latency_ms": provider.ewma_latency_ms, "failures": provider.failures}
                except Exception as exc:
                    return {"name": provider.name, "state": provider.state, "error": str(exc), "failures": provider.failures}

        return await asyncio.gather(*(probe(p) for p in self.providers))

    def add_provider(self, provider: RPCProvider) -> None:
        if any(p.name == provider.name or p.url == provider.url for p in self.providers):
            return
        self.providers.append(provider)

    def retained_registry(self) -> list[dict[str, Any]]:
        return [{"name": p.name, "url": p.url, "state": p.state, "successes": p.successes, "failures": p.failures, "latency_ms": p.ewma_latency_ms, "last_block": p.last_block} for p in self.providers]
