import pytest

from ghost_hunter.data_plane.cache import StateCache
from ghost_hunter.data_plane.models import PoolState, TokenState
from ghost_hunter.data_plane.rpc import MultiRPC, RPCProvider


def test_cache_affected_pools():
    cache = StateCache()
    cache.put_token(TokenState("0xA", 18, "A", "hash", 1, "test", 1.0))
    cache.put_pool(PoolState("0xP", "demo", "v2", "0xA", "0xB", 1, {"r0": 1}, "h", "test", 1.0))
    assert len(cache.affected_pools({"0xa"})) == 1


def test_provider_round_robin_order():
    rpc = MultiRPC([RPCProvider("a", "http://a"), RPCProvider("b", "http://b")])
    assert [p.name for p in rpc._ordered()] == ["a", "b"]
    assert [p.name for p in rpc._ordered()] == ["a", "b"]


def test_failed_provider_is_retained_and_cooled_down():
    provider = RPCProvider("a", "http://a")
    for _ in range(3):
        provider.record(False, 100.0)
    assert provider.state == "cooldown"
    assert provider in MultiRPC([provider]).providers


def test_rate_limited_provider_is_retained():
    provider = RPCProvider("a", "http://a")
    provider.record(False, 100.0, error_kind="rate_limit")
    assert provider.state == "cooldown"
    assert provider.url == "http://a"


@pytest.mark.asyncio
async def test_empty_provider_rejected():
    with pytest.raises(ValueError):
        MultiRPC([])
