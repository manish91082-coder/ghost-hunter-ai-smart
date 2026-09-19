from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .cache import StateCache
from .chain import PolygonChain
from .discovery import DiscoveryEngine
from .rpc import MultiRPC, RPCError
from .reorg import CanonicalCoordinator, CanonicalHead
from .scanner import AdaptiveLogScanner
from .quickswap import QuickSwapAdapter
from .store import DiscoveryStore


@dataclass(frozen=True)
class HeadContext:
    block: object
    accepted: bool
    replay_start: int | None


@dataclass
class DataPlane:
    rpc: MultiRPC
    chain: PolygonChain
    cache: StateCache
    discovery: DiscoveryEngine
    store: DiscoveryStore
    canonical: CanonicalCoordinator
    scanner: AdaptiveLogScanner | None = None
    quickswap: QuickSwapAdapter | None = None

    @classmethod
    def build(cls, rpc: MultiRPC, store_path: str = ":memory:") -> "DataPlane":
        cache = StateCache()
        store = DiscoveryStore(store_path)
        scanner = AdaptiveLogScanner(rpc)
        quickswap = QuickSwapAdapter(rpc, cache)
        return cls(rpc, PolygonChain(rpc), cache, DiscoveryEngine(cache), store, CanonicalCoordinator(store), scanner, quickswap)

    async def bootstrap(self) -> int:
        chain_id = await self.chain.chain_id()
        if chain_id != PolygonChain.CHAIN_ID:
            raise RuntimeError(f"wrong chain: expected {PolygonChain.CHAIN_ID}, got {chain_id}")
        # Durable snapshots are the restart baseline. Test doubles used by
        # isolated orchestration tests may not construct the full store/cache;
        # the production path always supplies both through DataPlane.build().
        if hasattr(self, "store") and hasattr(self, "cache"):
            self.store.latest_canonical_head()
            self.cache.restore(
                self.store.canonical_token_snapshots(),
                self.store.canonical_pool_snapshots(),
            )
        return chain_id

    async def _process_canonical_block(self, block) -> None:
        """Run discovery only after the block is canonical and durable."""
        if self.scanner is not None and self.quickswap is not None:
            await self.quickswap.process_block(self.scanner, self.store, block.number)

    async def run_heads(self, handler, poll_interval: float = 0.25) -> None:
        await self.bootstrap()
        async for block in self.chain.head_poll(poll_interval):
            accepted, replay_start = self.canonical.observe(
                CanonicalHead(block.number, block.hash, block.parent_hash)
            )
            if not accepted:
                if replay_start is None:
                    raise RuntimeError("canonical discontinuity requires a replay start")
                async def replay_handler(replayed_block):
                    await self._process_canonical_block(replayed_block)
                    await handler(replayed_block)
                await self.replay_range(replay_start, block.number, replay_handler, expected_end_hash=block.hash)
                continue
            await self._process_canonical_block(block)
            await handler(block)

    async def replay_range(
        self,
        start: int,
        end: int,
        handler,
        expected_end_hash: str | None = None,
    ) -> None:
        """Replay an exact inclusive range only after validating the whole chain.

        When a replay is triggered by a rejected live head, ``expected_end_hash``
        binds the replacement chain to that observed head. Validation happens
        before canonical persistence or handler invocation so a mismatched RPC
        view cannot partially promote an untrusted replacement chain.
        """
        if start < 0 or end < start:
            raise ValueError("invalid replay range")
        await self.bootstrap()
        blocks = []
        previous_hash: str | None = None
        for number in range(start, end + 1):
            block = await self.chain.block_by_number(number)
            if block.number != number:
                raise RuntimeError("replay returned the wrong block number")
            if previous_hash is not None and block.parent_hash != previous_hash:
                raise RuntimeError("replay chain is discontinuous")
            blocks.append(block)
            previous_hash = block.hash
        if expected_end_hash is not None and (not blocks or blocks[-1].hash != expected_end_hash):
            raise RuntimeError("replay chain does not match observed canonical head")

        for block in blocks:
            accepted = self.canonical.record_replayed_block(
                CanonicalHead(block.number, block.hash, block.parent_hash)
            )
            if not accepted:
                raise RuntimeError("replay block rejected by canonical coordinator")
            await handler(block)

    async def run_heads_context(self, handler, poll_interval: float = 0.25) -> None:
        """Run heads while explicitly propagating canonical/replay decisions."""
        await self.bootstrap()
        async for block in self.chain.head_poll(poll_interval):
            accepted, replay_start = self.canonical.observe(
                CanonicalHead(block.number, block.hash, block.parent_hash)
            )
            if not accepted:
                if replay_start is None:
                    raise RuntimeError("canonical discontinuity requires a replay start")
                async def replay_handler(replayed_block):
                    await self._process_canonical_block(replayed_block)
                    await handler(
                        HeadContext(
                            block=replayed_block,
                            accepted=True,
                            replay_start=None,
                        )
                    )
                await self.replay_range(replay_start, block.number, replay_handler)
                continue
            await self._process_canonical_block(block)
            await handler(HeadContext(block=block, accepted=True, replay_start=None))

    async def critical_read(self, method: str, params: list | None = None, quorum: int = 2) -> object:
        return await self.rpc.quorum_call(method, params, quorum=quorum)

    async def parallel_reads(self, calls: list[tuple[str, list]]) -> list:
        return await self.rpc.batch(calls)
