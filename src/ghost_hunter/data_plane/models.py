from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class BlockState:
    number: int
    hash: str
    parent_hash: str
    timestamp: int
    base_fee: int | None
    observed_at_ns: int


@dataclass(frozen=True)
class ProviderObservation:
    provider: str
    method: str
    latency_ms: float
    ok: bool
    error: str | None = None
    block_number: int | None = None


@dataclass(frozen=True)
class TokenState:
    address: str
    decimals: int | None
    symbol: str | None
    code_hash: str | None
    block_number: int
    source: str
    confidence: float


@dataclass(frozen=True)
class PoolState:
    address: str
    venue: str
    pool_type: str
    token0: str
    token1: str | None
    block_number: int
    state: Mapping[str, Any]
    state_hash: str
    source: str
    confidence: float


@dataclass
class EvidenceRecord:
    evidence_id: str
    block_number: int
    block_hash: str
    source: str
    observed_at_ns: int
    payload_hash: str
    fields: dict[str, Any] = field(default_factory=dict)
