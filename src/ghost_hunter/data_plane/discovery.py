from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .cache import StateCache
from .models import PoolState, TokenState


@dataclass(frozen=True)
class VenueAdapterSpec:
    venue: str
    pool_types: tuple[str, ...]
    factory_addresses: tuple[str, ...]
    discovery_method: str


class DiscoveryEngine:
    """Protocol-neutral discovery coordinator.

    Concrete adapters are deliberately separate so a new Polygon venue can be added
    without changing the route graph or economics engine.
    """

    def __init__(self, cache: StateCache):
        self.cache = cache
        self.adapters: list[VenueAdapterSpec] = []

    def register(self, adapter: VenueAdapterSpec) -> None:
        self.adapters.append(adapter)

    def normalize_token(self, state: TokenState) -> None:
        self.cache.put_token(state)

    def normalize_pool(self, state: PoolState) -> None:
        self.cache.put_pool(state)

    def all_venues(self) -> tuple[str, ...]:
        return tuple(sorted({a.venue for a in self.adapters}))

    def adapters_for(self, pool_type: str) -> Iterable[VenueAdapterSpec]:
        return (a for a in self.adapters if pool_type in a.pool_types)
