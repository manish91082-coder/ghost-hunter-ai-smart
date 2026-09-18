import pytest

from ghost_hunter.data_plane.events import EVENTS
from ghost_hunter.data_plane.quickswap import QuickSwapAdapter, ZERO_ADDRESS
from ghost_hunter.data_plane.cache import StateCache


class FakeRPC:
    def __init__(self, values):
        self.values = values
        self.calls = []
        self.pair_result = None

    async def call(self, method, params=None, **kwargs):
        self.calls.append((method, params))
        key = (
            method,
            params[0]["to"] if params and isinstance(params[0], dict) and "to" in params[0] else None,
            params[0]["data"] if params and isinstance(params[0], dict) and "data" in params[0] else None,
        )
        if key in self.values:
            value = self.values[key]
            if isinstance(value, Exception):
                raise value
            return value
        if method == "eth_call" and params and isinstance(params[0], dict):
            to = params[0].get("to")
            data = params[0].get("data", "")
            if to == V2_FACTORY and isinstance(data, str) and data.startswith("0xe6a43905") and self.pair_result is not None:
                return self.pair_result
        if method == "eth_getCode":
            return "0x6000"
        raise AssertionError(f"unexpected RPC call: {method} {params}")

    async def quorum_call(self, method, params=None, quorum=2, **kwargs):
        return await self.call(method, params, **kwargs)


def word(addr):
    return "0" * 24 + addr[2:].lower()


def topic(addr):
    return "0x" + word(addr)


V2_FACTORY = "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"
ALG_FACTORY = "0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28"


def make_adapter(values=None):
    return QuickSwapAdapter(FakeRPC(values or {}), StateCache())


def test_log_query_is_factory_and_verified_topic():
    adapter = make_adapter()
    q = adapter.log_query("v2", 10, 20)
    assert q["address"].lower() == V2_FACTORY.lower()
    assert q["topics"] == [EVENTS["v2_pair_created"].topic0]


def test_wrong_emitter_and_topic_fail_closed():
    adapter = make_adapter()
    good = {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic("0x" + "1" * 40), topic("0x" + "2" * 40)],
        "data": "0x" + word("0x" + "3" * 40) + f"{1:064x}",
        "blockNumber": "0x10",
    }
    adapter.decode_log("v2", good)
    with pytest.raises(ValueError):
        adapter.decode_log("v2", dict(good, address=ALG_FACTORY))
    with pytest.raises(ValueError):
        adapter.decode_log("v2", dict(good, topics=["0x" + "f" * 64] + good["topics"][1:]))


def test_zero_pool_rejected():
    adapter = make_adapter()
    log = {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic("0x" + "1" * 40), topic("0x" + "2" * 40)],
        "data": "0x" + word(ZERO_ADDRESS) + f"{1:064x}",
        "blockNumber": "0x10",
    }
    with pytest.raises(ValueError):
        adapter.decode_log("v2", log)


@pytest.mark.asyncio
async def test_v2_state_requires_factory_and_token_consistency():
    token0, token1, pool = "0x" + "1" * 40, "0x" + "2" * 40, "0x" + "3" * 40
    adapter = make_adapter()
    candidate = adapter.decode_log("v2", {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x" + word(pool) + f"{7:064x}",
        "blockNumber": "0x10",
    })
    adapter.rpc.values[("eth_call", pool, "0xc45a0155")] = "0x" + word(V2_FACTORY)
    adapter.rpc.values[("eth_call", pool, "0x0dfe1681")] = "0x" + word(token0)
    adapter.rpc.values[("eth_call", pool, "0xd21220a7")] = "0x" + word(token1)
    adapter.rpc.values[("eth_call", pool, "0x0902f1ac")] = "0x" + "0" * 64 + "1" * 64 + "0" * 64
    state = await adapter.read_pool_state(candidate)
    assert state.state["reserve0"] == 0
    assert state.state["reserve1"] == int("1" * 64, 16)
    assert adapter.cache.pools[pool].state_hash == state.state_hash


@pytest.mark.asyncio
async def test_pool_factory_mismatch_rejected():
    token0, token1, pool = "0x" + "1" * 40, "0x" + "2" * 40, "0x" + "3" * 40
    adapter = make_adapter()
    candidate = adapter.decode_log("v2", {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x" + word(pool) + f"{1:064x}",
        "blockNumber": "0x10",
    })
    adapter.rpc.values[("eth_call", pool, "0xc45a0155")] = "0x" + word(ALG_FACTORY)
    adapter.rpc.values[("eth_call", pool, "0x0dfe1681")] = "0x" + word(token0)
    adapter.rpc.values[("eth_call", pool, "0xd21220a7")] = "0x" + word(token1)
    adapter.rpc.values[("eth_call", pool, "0x0902f1ac")] = "0x" + "0" * 192
    with pytest.raises(ValueError, match="factory mismatch"):
        await adapter.read_pool_state(candidate)


def encode_string(value):
    raw = value.encode()
    padded = raw + b"\x00" * ((32 - len(raw) % 32) % 32)
    return "0x" + (32).to_bytes(32, "big").hex() + len(raw).to_bytes(32, "big").hex() + padded.hex()


def test_token_metadata_string_decoder():
    adapter = make_adapter()
    assert adapter._decode_string(encode_string("USDC")) == "USDC"
    assert adapter._decode_string("0x") is None


@pytest.mark.asyncio
async def test_factory_reconciliation_must_match_event_pool():
    token0, token1, pool = "0x" + "1" * 40, "0x" + "2" * 40, "0x" + "3" * 40
    other = "0x" + "4" * 40
    adapter = make_adapter()
    candidate = adapter.decode_log("v2", {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x" + word(pool) + f"{1:064x}",
        "blockNumber": "0x10",
    })
    adapter.rpc.pair_result = "0x" + word(pool)
    assert (await adapter.reconcile_candidate(candidate)).pool == pool
    adapter.rpc.pair_result = "0x" + word(other)
    with pytest.raises(ValueError, match="reconciliation mismatch"):
        await adapter.reconcile_candidate(candidate)


def test_discovery_is_idempotent_after_pool_is_cached():
    adapter = make_adapter()
    token0, token1, pool = "0x" + "1" * 40, "0x" + "2" * 40, "0x" + "3" * 40
    candidate = adapter.decode_log("v2", {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x" + word(pool) + f"{1:064x}",
        "blockNumber": "0x10",
    })
    assert not adapter.already_discovered(candidate)
    adapter.cache.pools[pool] = object()
    assert adapter.already_discovered(candidate)
    assert len(adapter.candidate_key(candidate)) == 4


def test_persist_candidate_requires_canonical_block_evidence():
    from ghost_hunter.data_plane.store import DiscoveryStore

    adapter = make_adapter()
    token0, token1, pool = "0x" + "1" * 40, "0x" + "2" * 40, "0x" + "3" * 40
    candidate = adapter.decode_log("v2", {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x" + word(pool) + f"{1:064x}",
        "blockNumber": "0xa",
        "blockHash": "h10",
        "transactionHash": "0xtx",
        "logIndex": "0x3",
    })
    with DiscoveryStore() as store:
        store.record_block(10, "h10", "h9")
        assert adapter.persist_candidate(candidate, store, {"pool": pool})
        assert not adapter.persist_candidate(candidate, store, {"pool": pool})

@pytest.mark.asyncio
async def test_process_block_persists_before_cache_promotion():
    from ghost_hunter.data_plane.scanner import AdaptiveLogScanner
    from ghost_hunter.data_plane.store import DiscoveryStore

    token0, token1, pool = "0x" + "1" * 40, "0x" + "2" * 40, "0x" + "3" * 40
    log = {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x" + word(pool) + f"{7:064x}",
        "blockNumber": "0x10",
        "blockHash": "h10",
        "transactionHash": "0xtx",
        "logIndex": "0x1",
    }
    adapter = make_adapter()
    adapter.rpc.pair_result = "0x" + word(pool)
    adapter.rpc.values[("eth_call", pool, "0xc45a0155")] = "0x" + word(V2_FACTORY)
    adapter.rpc.values[("eth_call", pool, "0x0dfe1681")] = "0x" + word(token0)
    adapter.rpc.values[("eth_call", pool, "0xd21220a7")] = "0x" + word(token1)
    adapter.rpc.values[("eth_call", pool, "0x0902f1ac")] = "0x" + "0" * 128 + "0" * 64
    adapter.rpc.values[("eth_call", token0, "0x313ce567")] = f"{18:064x}"
    adapter.rpc.values[("eth_call", token1, "0x313ce567")] = f"{6:064x}"

    scanner = AdaptiveLogScanner(adapter.rpc, initial_range=1, min_range=1, max_range=1)
    scanner.rpc.logs = [log] if hasattr(scanner.rpc, "logs") else None
    async def scan(query):
        return [log] if query.from_block == 16 and query.to_block == 16 else []
    scanner.scan = scan

    with DiscoveryStore() as store:
        store.record_block(16, "h10", "h9")
        assert await adapter.process_block(scanner, store, 16) == 1, adapter.rejections
        assert len(store.canonical_records()) == 1
        assert pool.lower() in adapter.cache.pools
        assert token0.lower() in adapter.cache.tokens
        assert token1.lower() in adapter.cache.tokens
