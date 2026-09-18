from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

from .models import BlockState
from .rpc import MultiRPC


class PolygonChain:
    CHAIN_ID = 137

    def __init__(self, rpc: MultiRPC):
        self.rpc = rpc
        self.previous: BlockState | None = None

    async def chain_id(self) -> int:
        return int(await self.rpc.call("eth_chainId"), 16)

    async def latest_block(self) -> BlockState:
        raw = await self.rpc.call("eth_getBlockByNumber", ["latest", False])
        if raw is None:
            raise RuntimeError("latest block unavailable")
        state = BlockState(
            number=int(raw["number"], 16),
            hash=raw["hash"],
            parent_hash=raw["parentHash"],
            timestamp=int(raw["timestamp"], 16),
            base_fee=int(raw["baseFeePerGas"], 16) if raw.get("baseFeePerGas") else None,
            observed_at_ns=time.time_ns(),
        )
        self.previous = state
        return state

    async def measure_interval(self, current: BlockState) -> float | None:
        if self.previous is None:
            return None
        return max(0.0, current.timestamp - self.previous.timestamp)

    async def head_poll(self, interval_seconds: float = 0.25) -> AsyncIterator[BlockState]:
        last = None
        while True:
            block = await self.latest_block()
            if block.number != last:
                last = block.number
                yield block
            await asyncio.sleep(interval_seconds)
