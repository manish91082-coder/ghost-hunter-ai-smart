from __future__ import annotations

import asyncio
import itertools
import time
from dataclasses import dataclass
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

    @property
    def healthy(self) -> bool:
        return time.monotonic() >= self.cooldown_until

    def record(self, ok: bool, latency_ms: float) -> None:
        alpha = 0.25
        if self.ewma_latency_ms is None:
            self.ewma_latency_ms = latency_ms
        else:
            self.ewma_latency_ms = alpha * latency_ms + (1 - alpha) * self.ewma_latency_ms
        if ok:
            self.successes += 1
            self.failures = max(0, self.failures - 1)
        else:
            self.failures += 1
            if self.failures >= 3:
                self.cooldown_until = time.monotonic() + min(30.0, 2 ** min(self.failures, 5))


class MultiRPC:
    """Async JSON-RPC client with batch calls, health tracking and failover."""

    def __init__(self, providers: list[RPCProvider], max_batch: int = 50):
        if not providers:
            raise ValueError("at least one RPC provider is required")
        self.providers = providers
        self.max_batch = max_batch
        self._rr = itertools.count()

    def _ordered(self) -> list[RPCProvider]:
        healthy = [p for p in self.providers if p.healthy]
        if not healthy:
            healthy = self.providers
        start = next(self._rr) % len(healthy)
        return healthy[start:] + healthy[:start]

    async def _post(self, provider: RPCProvider, payload: Any) -> Any:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=provider.timeout_seconds) as client:
                response = await client.post(provider.url, json=payload)
                response.raise_for_status()
                data = response.json()
            latency = (time.perf_counter() - started) * 1000
            provider.record(True, latency)
            return data
        except Exception as exc:
            latency = (time.perf_counter() - started) * 1000
            provider.record(False, latency)
            raise RPCError(f"{provider.name}: {exc}") from exc

    async def call(self, method: str, params: list[Any] | None = None) -> Any:
        request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        errors: list[str] = []
        for provider in self._ordered():
            try:
                data = await self._post(provider, request)
                if "error" in data:
                    raise RPCError(str(data["error"]))
                return data["result"]
            except Exception as exc:
                errors.append(str(exc))
        raise RPCError("all RPC providers failed: " + " | ".join(errors))

    async def batch(self, calls: list[tuple[str, list[Any]]]) -> list[Any]:
        results: list[Any] = []
        for offset in range(0, len(calls), self.max_batch):
            chunk = calls[offset : offset + self.max_batch]
            payload = [
                {"jsonrpc": "2.0", "id": offset + i + 1, "method": method, "params": params}
                for i, (method, params) in enumerate(chunk)
            ]
            errors: list[str] = []
            chunk_result = None
            for provider in self._ordered():
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

    async def quorum_call(self, method: str, params: list[Any] | None = None, quorum: int = 2) -> Any:
        """Query multiple providers and require agreement on execution-critical reads."""
        providers = [p for p in self.providers if p.healthy] or self.providers
        selected = providers[: max(quorum, 1)]
        values = await asyncio.gather(
            *(self._post(p, {"jsonrpc": "2.0", "id": i + 1, "method": method, "params": params or []})
              for i, p in enumerate(selected)),
            return_exceptions=True,
        )
        good = [v.get("result") for v in values if isinstance(v, dict) and "result" in v]
        if not good:
            raise RPCError("quorum read returned no successful results")
        if len(set(map(str, good))) != 1:
            raise RPCError(f"provider disagreement for {method}")
        return good[0]
