from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .cache import StateCache
from .chain import PolygonChain
from .discovery import DiscoveryEngine
from .rpc import MultiRPC


@dataclass
class DataPlane:
    rpc: MultiRPC
    chain: PolygonChain
    cache: StateCache
    discovery: DiscoveryEngine

    @classmethod
    def build(cls, rpc: MultiRPC) -> "DataPlane":
        cache = StateCache()
        return cls(rpc, PolygonChain(rpc), cache, DiscoveryEngine(cache))

    async def bootstrap(self) -> int:
        chain_id = await self.chain.chain_id()
        if chain_id != PolygonChain.CHAIN_ID:
            raise RuntimeError(f"wrong chain: expected {PolygonChain.CHAIN_ID}, got {chain_id}")
        return chain_id

    async def run_heads(self, handler, poll_interval: float = 0.25) -> None:
        await self.bootstrap()
        async for block in self.chain.head_poll(poll_interval):
            await handler(block)

    async def parallel_reads(self, calls: list[tuple[str, list]]) -> list:
        return await self.rpc.batch(calls)
