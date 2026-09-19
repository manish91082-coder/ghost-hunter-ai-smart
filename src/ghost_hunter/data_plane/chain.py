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

    @staticmethod
    def _block_state(raw: dict) -> BlockState:
        if raw is None:
            raise RuntimeError("block unavailable")
        return BlockState(
            number=int(raw["number"], 16),
            hash=raw["hash"],
            parent_hash=raw["parentHash"],
            timestamp=int(raw["timestamp"], 16),
            base_fee=int(raw["baseFeePerGas"], 16) if raw.get("baseFeePerGas") else None,
            observed_at_ns=time.time_ns(),
        )

    async def block_by_number(self, number: int) -> BlockState:
        if number < 0:
            raise ValueError("block number must be non-negative")
        raw = await self.rpc.call("eth_getBlockByNumber", [hex(number), False])
        return self._block_state(raw)

    async def latest_block(self) -> BlockState:
        raw = await self.rpc.call("eth_getBlockByNumber", ["latest", False])
        return self._block_state(raw)

    def commit_observation(self, state: BlockState) -> float | None:
        previous = self.previous
        self.previous = state
        if previous is None:
            return None
        return max(0.0, state.timestamp - previous.timestamp)

    async def head_poll(self, interval_seconds: float = 0.20) -> AsyncIterator[BlockState]:
        last_number: int | None = None
        while True:
            block = await self.latest_block()
            if block.number != last_number:
                last_number = block.number
                self.commit_observation(block)
                yield block
            await asyncio.sleep(interval_seconds)
