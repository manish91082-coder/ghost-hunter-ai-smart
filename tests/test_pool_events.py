import pytest

from ghost_hunter.data_plane.pool_events import (
    decode_quickswap_algebra_pool_created,
    decode_quickswap_v2_pair_created,
)
from ghost_hunter.data_plane.events import EVENTS, EventRegistry


V2_FACTORY = "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"
ALG_FACTORY = "0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28"


def _topic(address):
    return "0x" + "0" * 24 + address[2:].lower()


def _word(address):
    return "0" * 24 + address[2:].lower()


def test_verified_topics_are_exactly_32_bytes():
    assert EVENTS["v2_pair_created"].topic0 == "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
    assert EVENTS["v3_pool_created"].topic0 == "0x91ccaa7a278130b65168c3a0c8d3bcae84cf5e43704342bd3ec0b59e59c036db"
    reg = EventRegistry()
    reg.register_verified(EVENTS["v2_pair_created"])
    reg.register_verified(EVENTS["v3_pool_created"])
    assert len(reg.topic("PairCreated")) == 66
    assert len(reg.topic("Pool")) == 66


def test_v2_pair_created_decoder():
    t0 = "0x" + "1" * 40
    t1 = "0x" + "2" * 40
    pair = "0x" + "3" * 40
    data = "0x" + _word(pair) + f"{7:064x}"
    decoded = decode_quickswap_v2_pair_created(
        factory=V2_FACTORY,
        topics=[EVENTS["v2_pair_created"].topic0, _topic(t0), _topic(t1)],
        data=data,
    )
    assert decoded.pool == pair
    assert decoded.token0 == t0
    assert decoded.token1 == t1
    assert decoded.creation_index == 7


def test_algebra_pool_decoder():
    t0 = "0x" + "1" * 40
    t1 = "0x" + "2" * 40
    pool = "0x" + "3" * 40
    decoded = decode_quickswap_algebra_pool_created(
        factory=ALG_FACTORY,
        topics=[EVENTS["v3_pool_created"].topic0, _topic(t0), _topic(t1)],
        data="0x" + _word(pool),
    )
    assert decoded.pool == pool
    assert decoded.token0 == t0
    assert decoded.token1 == t1


@pytest.mark.parametrize("decoder,topics,data", [
    (decode_quickswap_v2_pair_created, [], "0x"),
    (decode_quickswap_algebra_pool_created, [], "0x"),
])
def test_pool_decoders_fail_closed_on_malformed_logs(decoder, topics, data):
    with pytest.raises(ValueError):
        decoder(factory=V2_FACTORY, topics=topics, data=data)
