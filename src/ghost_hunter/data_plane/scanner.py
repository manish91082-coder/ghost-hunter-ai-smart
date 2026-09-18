from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import PoolState
from .rpc import MultiRPC


@dataclass(frozen=True)
class LogQuery:
    address: str | None
    topics: list[str | list[str] | None]
    from_block: int
    to_block: int


class AdaptiveLogScanner:
    """Scan logs with bounded ranges and shrink-on-error.

    Discovery is replayable: the same block range can be scanned again after a
    reorg without creating duplicate pool records in the normalized cache.
    """

    def __init__(self, rpc: MultiRPC, initial_range: int = 500, min_range: int = 1, max_range: int = 2000):
        self.rpc = rpc
        self.initial_range = initial_range
        self.min_range = min_range
        self.max_range = max_range

    async def scan(self, query: LogQuery) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        cursor = query.from_block
        span = min(self.initial_range, self.max_range)
        while cursor <= query.to_block:
            end = min(cursor + span - 1, query.to_block)
            params = [{
                "fromBlock": hex(cursor),
                "toBlock": hex(end),
                **({"address": query.address} if query.address else {}),
                **({"topics": query.topics} if query.topics else {}),
            }]
            try:
                logs = await self.rpc.call("eth_getLogs", params)
                out.extend(logs)
                cursor = end + 1
                if len(logs) < 1000:
                    span = min(self.max_range, max(span, int(span * 1.5)))
            except Exception:
                if span <= self.min_range:
                    raise
                span = max(self.min_range, span // 2)
        return out


class PoolDiscoveryAdapter:
    """Normalizes verified factory event logs into PoolState records.

    Concrete venue adapters supply their own decoder and state reader.
    """

    venue: str
    pool_type: str

    def decode_pool_created(self, log: dict[str, Any], block_number: int) -> PoolState:
        raise NotImplementedError

    async def read_pool_state(self, address: str, block_number: int) -> PoolState:
        raise NotImplementedError
