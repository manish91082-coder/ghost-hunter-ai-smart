import pytest

from ghost_hunter.data_plane.events import EVENTS
from ghost_hunter.data_plane.quickswap import (
    QuickSwapAdapter,
    ZERO_ADDRESS,
)
from ghost_hunter.data_plane.cache import StateCache


class FakeRPC:
    def __init__(self, values):
        self.values = values
        self.calls = []

    async def call(self, method, params=None, **kwargs):
        self.calls.append((method, params))
        key = (method, params[0]["to"] if params and isinstance(params[0], dict) and "to" in params[0] else None, params[0]["data"] if params and isinstance(params[0], dict) and "data" in params[0] else None)
        if key in self.values:
            value = self.values[key]
            if isinstance(value, Exception):
                raise value
            return value
        if method == "eth_getCode":
            return "0x6000"
        raise AssertionError(f"unexpected RPC call: {method} {params}")


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
        "topics": [EVENTS["v2_pair_created"].topic0, topic("0x"+"1"*40), topic("0x"+"2"*40)],
        "data": "0x" + word("0x"+"3"*40) + f"{1:064x}",
        "blockNumber": "0x10",
    }
    adapter.decode_log("v2", good)
    bad = dict(good, address=ALG_FACTORY)
    with pytest.raises(ValueError):
        adapter.decode_log("v2", bad)
    bad2 = dict(good, topics=["0x"+"f"*64] + good["topics"][1:])
    with pytest.raises(ValueError):
        adapter.decode_log("v2", bad2)


def test_zero_pool_rejected():
    adapter = make_adapter()
    log = {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic("0x"+"1"*40), topic("0x"+"2"*40)],
        "data": "0x" + word(ZERO_ADDRESS) + f"{1:064x}",
        "blockNumber": "0x10",
    }
    with pytest.raises(ValueError):
        adapter.decode_log("v2", log)


@pytest.mark.asyncio
async def test_v2_state_requires_factory_and_token_consistency():
    token0, token1, pool = "0x"+"1"*40, "0x"+"2"*40, "0x"+"3"*40
    values = {}
    adapter = make_adapter(values)
    candidate = adapter.decode_log("v2", {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x"+word(pool)+f"{7:064x}",
        "blockNumber": "0x10",
    })
    # The fake defaults to code, but must explicitly prove pool interfaces.
    adapter.rpc.values[("eth_call", pool, "0xc45a0155")] = "0x" + word(V2_FACTORY)
    adapter.rpc.values[("eth_call", pool, "0x0dfe1681")] = "0x" + word(token0)
    adapter.rpc.values[("eth_call", pool, "0xd21220a7")] = "0x" + word(token1)
    adapter.rpc.values[("eth_call", pool, "0x0902f1ac")] = "0x" + "0"*64 + "1"*64 + "0"*64
    state = await adapter.read_pool_state(candidate)
    assert state.state["reserve0"] == 0
    assert state.state["reserve1"] == int("1"*64, 16)
    assert adapter.cache.pools[pool].state_hash == state.state_hash


@pytest.mark.asyncio
async def test_pool_factory_mismatch_rejected():
    token0, token1, pool = "0x"+"1"*40, "0x"+"2"*40, "0x"+"3"*40
    adapter = make_adapter()
    candidate = adapter.decode_log("v2", {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x"+word(pool)+f"{1:064x}",
        "blockNumber": "0x10",
    })
    adapter.rpc.values[("eth_call", pool, "0xc45a0155")] = "0x"+word(ALG_FACTORY)
    adapter.rpc.values[("eth_call", pool, "0x0dfe1681")] = "0x"+word(token0)
    adapter.rpc.values[("eth_call", pool, "0xd21220a7")] = "0x"+word(token1)
    adapter.rpc.values[("eth_call", pool, "0x0902f1ac")] = "0x"+"0"*192
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
