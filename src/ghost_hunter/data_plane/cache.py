from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .models import PoolState, TokenState


@dataclass
class StateCache:
    tokens: dict[str, TokenState]
    pools: dict[str, PoolState]

    def __init__(self) -> None:
        self.tokens = {}
        self.pools = {}

    @staticmethod
    def digest(value: Any) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    def put_token(self, state: TokenState) -> None:
        self.tokens[state.address.lower()] = state

    def put_pool(self, state: PoolState) -> None:
        self.pools[state.address.lower()] = state

    def affected_pools(self, addresses: set[str]) -> list[PoolState]:
        normalized = {a.lower() for a in addresses}
        return [
            p for p in self.pools.values()
            if p.token0.lower() in normalized or (p.token1 and p.token1.lower() in normalized)
        ]
