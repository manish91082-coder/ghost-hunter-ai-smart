from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .cache import StateCache
from .chain import PolygonChain
from .discovery import DiscoveryEngine
from .rpc import MultiRPC, RPCError
from .reorg import CanonicalCoordinator, CanonicalHead
from .store import DiscoveryStore


@dataclass
class DataPlane:
    rpc: MultiRPC
    chain: PolygonChain
    cache: StateCache
    discovery: DiscoveryEngine
    store: DiscoveryStore
    canonical: CanonicalCoordinator

    @classmethod
    def build(cls, rpc: MultiRPC) -> "DataPlane":
        cache = StateCache()
        store = DiscoveryStore()
        return cls(rpc, PolygonChain(rpc), cache, DiscoveryEngine(cache), store, CanonicalCoordinator(store))

    async def bootstrap(self) -> int:
        chain_id = await self.chain.chain_id()
        if chain_id != PolygonChain.CHAIN_ID:
            raise RuntimeError(f"wrong chain: expected {PolygonChain.CHAIN_ID}, got {chain_id}")
        return chain_id

    async def run_heads(self, handler, poll_interval: float = 0.25) -> None:
        await self.bootstrap()
        async for block in self.chain.head_poll(poll_interval):
            self.canonical.observe(CanonicalHead(block.number, block.hash, block.parent_hash))
            await handler(block)

    async def critical_read(self, method: str, params: list | None = None, quorum: int = 2) -> object:
        return await self.rpc.quorum_call(method, params, quorum=quorum)

    async def parallel_reads(self, calls: list[tuple[str, list]]) -> list:
        return await self.rpc.batch(calls)
