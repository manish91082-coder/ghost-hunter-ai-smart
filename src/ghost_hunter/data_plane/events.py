from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventTopic:
    name: str
    signature: str
    topic0: str


# Topic0 values are intentionally not hard-coded until generated/verified from
# canonical ABI sources. The registry accepts verified values at runtime.
EVENTS = {
    "v2_pair_created": EventTopic(
        "PairCreated",
        "PairCreated(address,address,address,uint256)",
        "",
    ),
    "v3_pool_created": EventTopic(
        "PoolCreated",
        "Pool(address,address,address)",
        "",
    ),
    "balancer_pool_registered": EventTopic(
        "PoolRegistered",
        "PoolRegistered(bytes32,address,address[])",
        "",
    ),
}


class EventRegistry:
    def __init__(self) -> None:
        self._topics: dict[str, EventTopic] = {}

    def register_verified(self, event: EventTopic) -> None:
        if not event.topic0.startswith("0x") or len(event.topic0) != 66:
            raise ValueError("topic0 must be a verified 32-byte keccak topic")
        self._topics[event.name] = event

    def topic(self, name: str) -> str:
        return self._topics[name].topic0
