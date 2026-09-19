import pytest

from ghost_hunter.data_plane.scanner import AdaptiveLogScanner, LogQuery, scan_and_decode_pool_events
from ghost_hunter.data_plane.quickswap import QuickSwapAdapter
from ghost_hunter.data_plane.cache import StateCache
from ghost_hunter.data_plane.events import EVENTS


class FakeRPC:
    def __init__(self, logs):
        self.logs = logs

    async def call(self, method, params=None, **kwargs):
        assert method == "eth_getLogs"
        return self.logs


V2_FACTORY = "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"


def word(addr):
    return "0" * 24 + addr[2:].lower()


def topic(addr):
    return "0x" + word(addr)


@pytest.mark.asyncio
async def test_scanner_wires_verified_factory_and_topic_to_decoder():
    token0, token1, pool = "0x"+"1"*40, "0x"+"2"*40, "0x"+"3"*40
    logs = [{
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x"+word(pool)+f"{9:064x}",
        "blockNumber": "0x20",
    }]
    scanner = AdaptiveLogScanner(FakeRPC(logs), initial_range=10, min_range=1, max_range=10)
    adapter = QuickSwapAdapter(FakeRPC(logs), StateCache())
    decoded = await scan_and_decode_pool_events(
        scanner,
        LogQuery(V2_FACTORY, [EVENTS["v2_pair_created"].topic0], 32, 32),
        adapter,
        "v2",
    )
    assert len(decoded) == 1
    assert decoded[0].created.pool == pool


@pytest.mark.asyncio
async def test_scanner_discards_wrong_emitter_without_promoting_candidate():
    token0, token1, pool = "0x"+"1"*40, "0x"+"2"*40, "0x"+"3"*40
    logs = [{
        "address": "0x"+"9"*40,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x"+word(pool)+f"{9:064x}",
        "blockNumber": "0x20",
    }]
    scanner = AdaptiveLogScanner(FakeRPC(logs), initial_range=10, min_range=1, max_range=10)
    adapter = QuickSwapAdapter(FakeRPC(logs), StateCache())
    decoded = await scan_and_decode_pool_events(
        scanner,
        LogQuery(V2_FACTORY, [EVENTS["v2_pair_created"].topic0], 32, 32),
        adapter,
        "v2",
    )
    assert decoded == []
