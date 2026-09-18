import pytest

from ghost_hunter.data_plane.cache import StateCache
from ghost_hunter.data_plane.models import PoolState, TokenState
from ghost_hunter.data_plane.rpc import MultiRPC, RPCProvider


def test_cache_affected_pools():
    cache = StateCache()
    cache.put_token(TokenState("0xA", 18, "A", "hash", 1, "test", 1.0))
    cache.put_pool(PoolState("0xP", "demo", "v2", "0xA", "0xB", 1, {"r0": 1}, "h", "test", 1.0))
    assert len(cache.affected_pools({"0xa"})) == 1


def test_provider_order_is_score_driven():
    slow = RPCProvider("slow", "http://slow", ewma_latency_ms=500)
    fast = RPCProvider("fast", "http://fast", ewma_latency_ms=50)
    rpc = MultiRPC([slow, fast])
    assert [p.name for p in rpc._ordered()] == ["fast", "slow"]


def test_capability_filter_is_dynamic():
    generic = RPCProvider("generic", "http://generic")
    trace = RPCProvider("trace", "http://trace", capabilities={"trace"})
    rpc = MultiRPC([generic, trace])
    assert [p.name for p in rpc._ordered("trace")] == ["generic", "trace"]


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


def test_stale_provider_is_quarantined_but_retained():
    provider = RPCProvider("lagging", "https://rpc.example/?api_key=SECRET")
    for _ in range(3):
        provider.observe_block(100, 103, max_lag_blocks=2)
    assert provider.state == "quarantined"
    registry = MultiRPC([provider]).retained_registry()[0]
    assert "SECRET" not in registry["url"]
    assert "api_key" not in registry["url"]


@pytest.mark.asyncio
async def test_empty_provider_rejected():
    with pytest.raises(ValueError):
        MultiRPC([])


@pytest.mark.asyncio
async def test_quorum_requires_provider_family_diversity():
    a = RPCProvider("a1", "https://a1.example", provider_family="family-a")
    a2 = RPCProvider("a2", "https://a2.example", provider_family="family-a")
    b = RPCProvider("b", "https://b.example", provider_family="family-b")
    rpc = MultiRPC([a, a2, b])
    async def fake_post(provider, payload):
        return {"result": "0x1"}
    rpc._post = fake_post
    assert await rpc.quorum_call("eth_blockNumber", quorum=2) == "0x1"


@pytest.mark.asyncio
async def test_quorum_fails_when_only_one_provider_family_exists():
    a = RPCProvider("a1", "https://a1.example", provider_family="family-a")
    a2 = RPCProvider("a2", "https://a2.example", provider_family="family-a")
    rpc = MultiRPC([a, a2])
    with pytest.raises(Exception, match="diversity"):
        await rpc.quorum_call("eth_blockNumber", quorum=2)
