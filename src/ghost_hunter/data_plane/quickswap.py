from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cache import StateCache
from .events import EVENTS
from .models import PoolState, TokenState
from .pool_events import (
    PoolCreated,
    decode_quickswap_algebra_pool_created,
    decode_quickswap_v2_pair_created,
)
from .protocols import VerifiedDeployment, verified_deployments
from .rpc import MultiRPC
from .store import DiscoveryRecord, DiscoveryStore

ZERO_ADDRESS = "0x" + "0" * 40
FACTORY_SELECTOR = "0xc45a0155"
TOKEN0_SELECTOR = "0x0dfe1681"
TOKEN1_SELECTOR = "0xd21220a7"
DECIMALS_SELECTOR = "0x313ce567"
SYMBOL_SELECTOR = "0x95d89b41"
NAME_SELECTOR = "0x06fdde03"
TOTAL_SUPPLY_SELECTOR = "0x18160ddd"
RESERVES_SELECTOR = "0x0902f1ac"
POOL_BY_PAIR_SELECTOR = "0xd9a641e1"
GLOBAL_STATE_SELECTOR = "0xe76c01e4"


@dataclass(frozen=True)
class DiscoveryCandidate:
    created: PoolCreated
    block_number: int
    transaction_hash: str | None
    block_hash: str | None = None
    log_index: int | None = None


def _hex(raw: Any) -> str:
    if not isinstance(raw, str) or not raw.startswith("0x"):
        raise ValueError("RPC result is not hex")
    return raw


def _address(raw: Any) -> str:
    value = _hex(raw)
    if len(value) < 42:
        raise ValueError("RPC result cannot contain an address")
    return "0x" + value[-40:]


def _uint(raw: Any) -> int:
    value = _hex(raw)
    if len(value) < 66:
        raise ValueError("RPC result is not a 32-byte word")
    return int(value[-64:], 16)


def _abi_word(address: str) -> str:
    normalized = address.lower()
    if len(normalized) != 42 or not normalized.startswith("0x"):
        raise ValueError("invalid address")
    return "0x" + ("0" * 24) + normalized[2:]


def _is_zero(address: str) -> bool:
    return address.lower() == ZERO_ADDRESS


def _state_hash(state: dict[str, Any]) -> str:
    return StateCache.digest(state)


class QuickSwapAdapter:
    """Fail-closed runtime adapter for verified QuickSwap Polygon factories."""

    def __init__(self, rpc: MultiRPC, cache: StateCache | None = None) -> None:
        self.rpc = rpc
        self.cache = cache or StateCache()
        self.deployments = verified_deployments(137)
        self._by_key = {(d.venue, d.pool_type): d for d in self.deployments}

    def deployment(self, pool_type: str) -> VerifiedDeployment:
        try:
            return self._by_key[("quickswap", pool_type)]
        except KeyError as exc:
            raise ValueError(f"unsupported QuickSwap pool type: {pool_type}") from exc

    def log_query(self, pool_type: str, from_block: int, to_block: int) -> dict[str, Any]:
        deployment = self.deployment(pool_type)
        topic = EVENTS["v2_pair_created" if pool_type == "v2" else "v3_pool_created"].topic0
        return {
            "address": deployment.factory,
            "topics": [topic],
            "fromBlock": hex(from_block),
            "toBlock": hex(to_block),
        }

    def decode_log(self, pool_type: str, log: dict[str, Any]) -> DiscoveryCandidate:
        deployment = self.deployment(pool_type)
        if str(log.get("address", "")).lower() != deployment.factory.lower():
            raise ValueError("factory emitter mismatch")
        topics = log.get("topics")
        data = log.get("data", "0x")
        expected = EVENTS["v2_pair_created" if pool_type == "v2" else "v3_pool_created"].topic0
        if not isinstance(topics, list) or not topics or str(topics[0]).lower() != expected.lower():
            raise ValueError("event topic mismatch")
        if pool_type == "v2":
            created = decode_quickswap_v2_pair_created(factory=deployment.factory, topics=topics, data=data)
        elif pool_type == "algebra_v3":
            created = decode_quickswap_algebra_pool_created(factory=deployment.factory, topics=topics, data=data)
        else:
            raise ValueError("unsupported QuickSwap pool type")
        if _is_zero(created.pool) or _is_zero(created.token0) or _is_zero(created.token1):
            raise ValueError("zero address in pool discovery")
        if created.token0.lower() == created.token1.lower():
            raise ValueError("identical pool tokens")
        block_number = int(str(log.get("blockNumber", "0x0")), 16)
        return DiscoveryCandidate(created, block_number, log.get("transactionHash"), log.get("blockHash"), int(str(log["logIndex"]), 16) if log.get("logIndex") is not None else None)

    async def _read(self, address: str, selector: str, extra: str = "") -> str:
        return _hex(await self.rpc.call("eth_call", [{"to": address, "data": selector + extra}, "latest"]))

    @staticmethod
    def _decode_string(raw: str) -> str | None:
        try:
            data = bytes.fromhex(_hex(raw)[2:])
            if len(data) >= 64:
                offset = int.from_bytes(data[:32], "big")
                if offset + 32 <= len(data):
                    length = int.from_bytes(data[offset:offset + 32], "big")
                    start = offset + 32
                    end = start + length
                    if end <= len(data):
                        return data[start:end].decode("utf-8", errors="strict")
            if len(data) >= 32:
                length = int.from_bytes(data[:32], "big")
                if 32 + length <= len(data):
                    return data[32:32 + length].decode("utf-8", errors="strict")
        except (ValueError, UnicodeDecodeError):
            return None
        return None
    async def _token_state(self, address: str, block_number: int) -> TokenState:
        code = await self.rpc.call("eth_getCode", [address, hex(block_number)])
        if not isinstance(code, str) or len(code) <= 2:
            raise ValueError("token has no runtime code")
        decimals = _uint(await self.rpc.call("eth_call", [{"to": address, "data": DECIMALS_SELECTOR}, hex(block_number)]))
        if decimals > 255:
            raise ValueError("token decimals out of bounds")
        symbol = None
        name = None
        total_supply = None
        try:
            symbol = self._decode_string(
                await self.rpc.call("eth_call", [{"to": address, "data": SYMBOL_SELECTOR}, hex(block_number)])
            )
        except Exception:
            pass
        try:
            name = self._decode_string(
                await self.rpc.call("eth_call", [{"to": address, "data": NAME_SELECTOR}, hex(block_number)])
            )
        except Exception:
            pass
        try:
            total_supply = _uint(
                await self.rpc.call("eth_call", [{"to": address, "data": TOTAL_SUPPLY_SELECTOR}, hex(block_number)])
            )
        except Exception:
            pass
        state = {"name": name, "symbol": symbol, "total_supply": total_supply}
        token = TokenState(
            address=address.lower(),
            decimals=decimals,
            symbol=symbol,
            code_hash=StateCache.digest(code),
            block_number=block_number,
            source="quickswap_direct",
            confidence=1.0,
        )
        self.cache.put_token(token)
        return token

    async def read_pool_state(self, candidate: DiscoveryCandidate) -> PoolState:
        pool = candidate.created.pool
        block_tag = hex(candidate.block_number)
        code = await self.rpc.call("eth_getCode", [pool, block_tag])
        if not isinstance(code, str) or len(code) <= 2:
            raise ValueError("pool has no runtime code")

        factory = _address(await self.rpc.call("eth_call", [{"to": pool, "data": FACTORY_SELECTOR}, block_tag]))
        token0 = _address(await self.rpc.call("eth_call", [{"to": pool, "data": TOKEN0_SELECTOR}, block_tag]))
        token1 = _address(await self.rpc.call("eth_call", [{"to": pool, "data": TOKEN1_SELECTOR}, block_tag]))
        if factory.lower() != candidate.created.factory.lower():
            raise ValueError("pool factory mismatch")
        if token0.lower() != candidate.created.token0.lower() or token1.lower() != candidate.created.token1.lower():
            raise ValueError("pool token metadata mismatch")
        if token0.lower() >= token1.lower():
            raise ValueError("pool token ordering is not canonical")

        state: dict[str, Any] = {
            "factory": factory.lower(),
            "token0": token0.lower(),
            "token1": token1.lower(),
            "code_hash": StateCache.digest(code),
        }
        if candidate.created.pool_type == "v2":
            reserves = _hex(await self.rpc.call("eth_call", [{"to": pool, "data": RESERVES_SELECTOR}, block_tag]))
            if len(reserves) < 194:
                raise ValueError("invalid V2 reserves ABI result")
            state["reserve0"] = int(reserves[2:66], 16)
            state["reserve1"] = int(reserves[66:130], 16)
            state["reserve_timestamp"] = int(reserves[130:194], 16)
        elif candidate.created.pool_type == "algebra_v3":
            global_state = _hex(await self.rpc.call("eth_call", [{"to": pool, "data": GLOBAL_STATE_SELECTOR}, block_tag]))
            if len(global_state) < 66:
                raise ValueError("invalid Algebra globalState result")
            state["global_state_raw"] = global_state
        else:
            raise ValueError("unsupported pool type")

        pool_state = PoolState(
            address=pool.lower(),
            venue="quickswap",
            pool_type=candidate.created.pool_type,
            token0=token0.lower(),
            token1=token1.lower(),
            block_number=candidate.block_number,
            state=state,
            state_hash=_state_hash(state),
            source="quickswap_direct",
            confidence=1.0,
        )
        self.cache.put_pool(pool_state)
        return pool_state

    def candidate_key(self, candidate: DiscoveryCandidate) -> tuple[str, str, str, int]:
        return (candidate.created.venue, candidate.created.pool_type, candidate.created.pool.lower(), candidate.block_number)

    def already_discovered(self, candidate: DiscoveryCandidate) -> bool:
        return candidate.created.pool.lower() in self.cache.pools

    async def reconcile_candidate(self, candidate: DiscoveryCandidate) -> PoolCreated:
        factory_pool = await self.reconcile_pool_by_pair(candidate.created.pool_type, candidate.created.token0, candidate.created.token1, candidate.block_number)
        if factory_pool.lower() != candidate.created.pool.lower():
            raise ValueError("factory reconciliation mismatch")
        return candidate.created
    async def reconcile_pool_by_pair(self, pool_type: str, token0: str, token1: str, block_number: int) -> str:
        deployment = self.deployment(pool_type)
        if pool_type == "v2":
            selector = "0xe6a43905"
        elif pool_type == "algebra_v3":
            selector = POOL_BY_PAIR_SELECTOR
        else:
            raise ValueError("unsupported QuickSwap pool type")
        raw = await self.rpc.quorum_call(
            "eth_call",
            [{"to": deployment.factory, "data": selector + _abi_word(token0)[2:] + _abi_word(token1)[2:]}, hex(block_number)],
            quorum=2,
        )
        pool = _address(raw)
        if _is_zero(pool):
            return ZERO_ADDRESS
        return pool

    def persist_candidate(self, candidate: DiscoveryCandidate, store: DiscoveryStore, payload: Any) -> bool:
        if not candidate.block_hash: raise ValueError("discovery block_hash is required for persistence")
        key = ":".join(map(str, self.candidate_key(candidate)))
        record = DiscoveryRecord(candidate_key=key, venue=candidate.created.venue, pool_type=candidate.created.pool_type, pool_address=candidate.created.pool.lower(), block_number=candidate.block_number, block_hash=candidate.block_hash, transaction_hash=candidate.transaction_hash, log_index=candidate.log_index, payload_hash=store.payload_hash(payload))
        return store.record_discovery(record, payload)
