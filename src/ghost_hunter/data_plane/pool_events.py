from __future__ import annotations

from dataclasses import dataclass


def _word(data: str, index: int) -> str:
    raw = data[2:] if data.startswith("0x") else data
    start = index * 64
    end = start + 64
    if len(raw) < end:
        raise ValueError("event data is too short")
    return raw[start:end]


def _address_word(word: str) -> str:
    if len(word) != 64:
        raise ValueError("invalid ABI word")
    return "0x" + word[-40:]


def _topic_address(topic: str) -> str:
    raw = topic[2:] if topic.startswith("0x") else topic
    if len(raw) != 64:
        raise ValueError("indexed address topic must be one ABI word")
    return "0x" + raw[-40:]


def _uint_word(word: str) -> int:
    if len(word) != 64:
        raise ValueError("invalid uint ABI word")
    return int(word, 16)


@dataclass(frozen=True)
class PoolCreated:
    venue: str
    pool_type: str
    factory: str
    token0: str
    token1: str
    pool: str
    creation_index: int | None = None


def decode_quickswap_v2_pair_created(
    *,
    factory: str,
    topics: list[str],
    data: str,
) -> PoolCreated:
    if len(topics) != 3:
        raise ValueError("V2 PairCreated requires topic0, token0 and token1")
    token0 = _topic_address(topics[1])
    token1 = _topic_address(topics[2])
    pool = _address_word(_word(data, 0))
    creation_index = _uint_word(_word(data, 1))
    return PoolCreated("quickswap", "v2", factory.lower(), token0.lower(), token1.lower(), pool.lower(), creation_index)


def decode_quickswap_algebra_pool_created(
    *,
    factory: str,
    topics: list[str],
    data: str,
) -> PoolCreated:
    if len(topics) != 3:
        raise ValueError("Algebra Pool requires topic0, token0 and token1")
    token0 = _topic_address(topics[1])
    token1 = _topic_address(topics[2])
    pool = _address_word(_word(data, 0))
    return PoolCreated("quickswap", "algebra_v3", factory.lower(), token0.lower(), token1.lower(), pool.lower())
