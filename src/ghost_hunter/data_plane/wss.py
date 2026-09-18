from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import AsyncIterator

import websockets

from .models import BlockState


@dataclass
class WSSProvider:
    name: str
    url: str
    timeout_seconds: float = 3.0
    failures: int = 0
    successes: int = 0
    ewma_latency_ms: float | None = None
    cooldown_until: float = 0.0
    state: str = "active"
    last_block: int | None = None
    last_success_at: float | None = None
    last_failure_at: float | None = None

    @property
    def available(self) -> bool:
        return time.monotonic() >= self.cooldown_until and self.state not in {"quarantined", "disabled"}

    def record(self, ok: bool, latency_ms: float) -> None:
        alpha = 0.25
        self.ewma_latency_ms = latency_ms if self.ewma_latency_ms is None else alpha * latency_ms + (1 - alpha) * self.ewma_latency_ms
        now = time.monotonic()
        if ok:
            self.successes += 1
            self.failures = max(0, self.failures - 1)
            self.last_success_at = now
            if self.state in {"cooldown", "probation"}:
                self.state = "active"
        else:
            self.failures += 1
            self.last_failure_at = now
            if self.failures >= 3:
                self.state = "cooldown"
                self.cooldown_until = now + min(60.0, 2.0 ** min(self.failures, 6))

    @property
    def score(self) -> float:
        return (self.ewma_latency_ms or 1000.0) + min(self.failures, 10) * 15.0


class PolygonWSS:
    """Autonomous retained WSS fleet.

    WSS endpoints are never deleted automatically. A failed stream is rotated out,
    cooldown-probed and restored when healthy. WSS is an acceleration signal only.
    """

    def __init__(self, providers: list[WSSProvider], timeout_seconds: float = 3.0):
        if not providers:
            raise ValueError("no WSS providers configured")
        self.providers = providers
        self.timeout_seconds = timeout_seconds

    def _ordered(self) -> list[WSSProvider]:
        candidates = [p for p in self.providers if p.available] or [p for p in self.providers if p.state != "disabled"]
        if not candidates:
            raise RuntimeError("no WSS providers available")
        return sorted(candidates, key=lambda p: p.score)

    async def heads(self) -> AsyncIterator[BlockState]:
        while True:
            provider = self._ordered()[0]
            started = time.perf_counter()
            try:
                async with websockets.connect(provider.url, open_timeout=provider.timeout_seconds) as ws:
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["newHeads"]}))
                    provider.record(True, (time.perf_counter() - started) * 1000)
                    async for message in ws:
                        received = time.perf_counter()
                        data = json.loads(message)
                        result = data.get("params", {}).get("result")
                        if not result:
                            continue
                        number = int(result["number"], 16)
                        provider.last_block = number
                        provider.record(True, (time.perf_counter() - received) * 1000)
                        yield BlockState(
                            number=number,
                            hash=result["hash"],
                            parent_hash=result["parentHash"],
                            timestamp=int(result["timestamp"], 16),
                            base_fee=None,
                            observed_at_ns=time.time_ns(),
                        )
            except Exception:
                provider.record(False, (time.perf_counter() - started) * 1000)
                await asyncio.sleep(min(5.0, max(0.25, provider.cooldown_until - time.monotonic())))

    async def probe_all(self) -> list[dict[str, object]]:
        """Open/close subscriptions concurrently to test retained WSS endpoints."""
        sem = asyncio.Semaphore(min(8, len(self.providers)))

        async def probe(provider: WSSProvider) -> dict[str, object]:
            async with sem:
                started = time.perf_counter()
                try:
                    async with websockets.connect(provider.url, open_timeout=provider.timeout_seconds) as ws:
                        await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["newHeads"]}))
                        provider.record(True, (time.perf_counter() - started) * 1000)
                        return {"name": provider.name, "state": provider.state, "ok": True, "latency_ms": provider.ewma_latency_ms}
                except Exception as exc:
                    provider.record(False, (time.perf_counter() - started) * 1000)
                    return {"name": provider.name, "state": provider.state, "ok": False, "error": str(exc)}
