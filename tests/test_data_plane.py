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


@pytest.mark.asyncio
async def test_head_context_replays_replacement_chain_on_discontinuity():
    from ghost_hunter.data_plane.models import BlockState
    from ghost_hunter.data_plane.orchestrator import DataPlane, HeadContext

    class FakeChain:
        CHAIN_ID = 137
        async def chain_id(self):
            return 137
        async def head_poll(self, _interval):
            yield BlockState(10, "h10", "h9", 0, None, 0)
            yield BlockState(11, "h11", "wrong", 0, None, 0)
        async def block_by_number(self, number):
            return {
                8: BlockState(8, "h8", "h7", 0, None, 0),
                9: BlockState(9, "h9", "h8", 0, None, 0),
                10: BlockState(10, "h10", "h9", 0, None, 0),
                11: BlockState(11, "h11", "h10", 0, None, 0),
            }[number]

    class FakeCanonical:
        def __init__(self):
            self.calls = 0
        def observe(self, head):
            self.calls += 1
            return (True, None) if self.calls == 1 else (False, 8)

        def record_replayed_block(self, head):
            return True

    plane = DataPlane.__new__(DataPlane)
    plane.chain = FakeChain()
    plane.canonical = FakeCanonical()

    seen = []
    async def handler(ctx):
        seen.append(ctx)

    await plane.run_heads_context(handler, poll_interval=0)
    assert all(isinstance(item, HeadContext) for item in seen)
    assert [item.block.number for item in seen] == [10, 8, 9, 10, 11]
    assert all(item.accepted and item.replay_start is None for item in seen)


@pytest.mark.asyncio
async def test_replay_rejects_replacement_chain_with_wrong_terminal_hash():
    from ghost_hunter.data_plane.models import BlockState
    from ghost_hunter.data_plane.orchestrator import DataPlane

    class FakeChain:
        CHAIN_ID = 137
        async def chain_id(self):
            return 137
        async def block_by_number(self, number):
            return {
                8: BlockState(8, "h8", "h7", 0, None, 0),
                9: BlockState(9, "h9", "h8", 0, None, 0),
            }[number]

    class FakeCanonical:
        def record_replayed_block(self, _head):
            raise AssertionError("canonical state must not be changed before final-chain validation")

    plane = DataPlane.__new__(DataPlane)
    plane.chain = FakeChain()
    plane.canonical = FakeCanonical()
    seen = []

    async def handler(block):
        seen.append(block)

    with pytest.raises(RuntimeError, match="observed canonical head"):
        await plane.replay_range(8, 9, handler, expected_end_hash="unexpected")
    assert seen == []


@pytest.mark.asyncio
async def test_head_context_replay_fails_closed_when_observed_head_hash_differs():
    from ghost_hunter.data_plane.models import BlockState
    from ghost_hunter.data_plane.orchestrator import DataPlane

    class FakeChain:
        CHAIN_ID = 137
        async def chain_id(self):
            return 137
        async def head_poll(self, _interval):
            yield BlockState(10, "h10", "h9", 0, None, 0)
            # The observed rejected head is fork11, but deterministic replay
            # returns a different block at the same height.
            yield BlockState(11, "observed-fork11", "wrong", 0, None, 0)
        async def block_by_number(self, number):
            return {
                8: BlockState(8, "h8", "h7", 0, None, 0),
                9: BlockState(9, "h9", "h8", 0, None, 0),
                10: BlockState(10, "h10", "h9", 0, None, 0),
                11: BlockState(11, "different11", "h10", 0, None, 0),
            }[number]

    class FakeCanonical:
        def __init__(self):
            self.calls = 0
        def observe(self, head):
            self.calls += 1
            return (True, None) if self.calls == 1 else (False, 8)

        def record_replayed_block(self, _head):
            raise AssertionError("mismatched replay must not reach canonical persistence")

    plane = DataPlane.__new__(DataPlane)
    plane.chain = FakeChain()
    plane.canonical = FakeCanonical()

    seen = []
    async def handler(ctx):
        seen.append(ctx)

    with pytest.raises(RuntimeError, match="observed canonical head"):
        await plane.run_heads_context(handler, poll_interval=0)
    assert len(seen) == 1
    assert seen[0].block.number == 10


@pytest.mark.asyncio
async def test_replay_handler_failure_rolls_back_partial_canonical_promotion(tmp_path):
    from ghost_hunter.data_plane.models import BlockState
    from ghost_hunter.data_plane.orchestrator import DataPlane
    from ghost_hunter.data_plane.reorg import CanonicalCoordinator
    from ghost_hunter.data_plane.store import DiscoveryStore

    store = DiscoveryStore(tmp_path / "replay.sqlite")
    for number, block_hash, parent_hash in [
        (7, "h7", "h6"),
        (8, "old8", "h7"),
        (9, "old9", "old8"),
        (10, "old10", "old9"),
    ]:
        store.record_block(number, block_hash, parent_hash)
    coordinator = CanonicalCoordinator(store, overlap=3)
    accepted, replay_start = coordinator.observe(BlockState(11, "fork11", "wrong", 0, None, 0))
    assert accepted is False
    assert replay_start == 8

    class FakeChain:
        async def chain_id(self):
            return 137

        async def block_by_number(self, number):
            return {
                8: BlockState(8, "new8", "h7", 0, None, 0),
                9: BlockState(9, "new9", "new8", 0, None, 0),
                10: BlockState(10, "new10", "new9", 0, None, 0),
                11: BlockState(11, "new11", "new10", 0, None, 0),
            }[number]

    plane = DataPlane.__new__(DataPlane)
    plane.chain = FakeChain()
    plane.store = store
    plane.cache = StateCache()
    plane.canonical = coordinator

    seen = []

    async def handler(block):
        seen.append(block.number)
        if block.number == 9:
            raise RuntimeError("processing failed")

    with pytest.raises(RuntimeError, match="processing failed"):
        await plane.replay_range(8, 11, handler, expected_end_hash="new11")

    assert seen == [8, 9]
    assert store.latest_canonical_head() == (7, "h7", "h6")
    assert coordinator.guard.head == coordinator.guard.head.__class__(7, "h7", "h6")
    assert store.canonical_records() == []
