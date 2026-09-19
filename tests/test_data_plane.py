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


@pytest.mark.asyncio
async def test_reorg_replay_end_to_end_reconstructs_and_processes_replacement_chain(tmp_path):
    """Exercise live discontinuity -> durable rewind -> replacement replay end-to-end."""
    from ghost_hunter.data_plane.models import BlockState
    from ghost_hunter.data_plane.orchestrator import DataPlane
    from ghost_hunter.data_plane.reorg import CanonicalCoordinator
    from ghost_hunter.data_plane.store import DiscoveryStore

    store = DiscoveryStore(tmp_path / "e2e-replay.sqlite")
    for number, block_hash, parent_hash in [
        (7, "h7", "h6"),
        (8, "old8", "h7"),
        (9, "old9", "old8"),
        (10, "old10", "old9"),
    ]:
        store.record_block(number, block_hash, parent_hash)

    class FakeChain:
        CHAIN_ID = 137

        async def chain_id(self):
            return 137

        async def head_poll(self, _interval):
            yield BlockState(11, "new11", "new10", 0, None, 0)

        async def block_by_number(self, number):
            return {
                8: BlockState(8, "new8", "h7", 0, None, 0),
                9: BlockState(9, "new9", "new8", 0, None, 0),
                10: BlockState(10, "new10", "new9", 0, None, 0),
                11: BlockState(11, "new11", "new10", 0, None, 0),
            }[number]

    coordinator = CanonicalCoordinator(store, overlap=3)
    plane = DataPlane.__new__(DataPlane)
    plane.chain = FakeChain()
    plane.store = store
    plane.cache = StateCache()
    plane.canonical = coordinator
    plane.scanner = None
    plane.quickswap = None

    processed = []
    async def process(block):
        processed.append(block.number)

    plane._process_canonical_block = process

    seen = []
    async def handler(block):
        seen.append(block.number)

    await plane.run_heads(handler, poll_interval=0)

    assert processed == [8, 9, 10, 11]
    assert seen == [8, 9, 10, 11]
    assert store.latest_canonical_head() == (11, "new11", "new10")
    assert coordinator.guard.head == coordinator.guard.head.__class__(11, "new11", "new10")


@pytest.mark.asyncio
async def test_reorg_replay_runs_real_quickswap_persistence_path(tmp_path):
    """Exercise replay through the real QuickSwap adapter and durable evidence store."""
    from ghost_hunter.data_plane.models import BlockState, PoolState, TokenState
    from ghost_hunter.data_plane.orchestrator import DataPlane
    from ghost_hunter.data_plane.pool_events import PoolCreated
    from ghost_hunter.data_plane.quickswap import DiscoveryCandidate, QuickSwapAdapter
    from ghost_hunter.data_plane.reorg import CanonicalCoordinator
    from ghost_hunter.data_plane.store import DiscoveryStore

    store = DiscoveryStore(tmp_path / "quickswap-replay.sqlite")
    for number, block_hash, parent_hash in [
        (7, "h7", "h6"),
        (8, "old8", "h7"),
        (9, "old9", "old8"),
        (10, "old10", "old9"),
    ]:
        store.record_block(number, block_hash, parent_hash)

    old_candidate = DiscoveryCandidate(
        PoolCreated(
            "quickswap", "v2", "0x" + "1" * 40,
            "0x" + "2" * 40, "0x" + "3" * 40, "0x" + "4" * 40, 1
        ),
        8, "oldtx", "old8", 0,
    )
    store.record_discovery_bundle(
        __import__("ghost_hunter.data_plane.store", fromlist=["DiscoveryRecord"]).DiscoveryRecord(
            candidate_key="old",
            venue="quickswap", pool_type="v2", pool_address=old_candidate.created.pool,
            block_number=8, block_hash="old8", transaction_hash="oldtx", log_index=0,
            payload_hash=store.payload_hash({"old": True}),
        ),
        {"old": True},
        PoolState("0x" + "4" * 40, "quickswap", "v2", "0x" + "2" * 40, "0x" + "3" * 40,
                  8, {"reserve0": 1, "reserve1": 2}, "oldpool", "test", 1.0),
        (
            TokenState("0x" + "2" * 40, 18, "T0", "oldcode0", 8, "test", 1.0),
            TokenState("0x" + "3" * 40, 18, "T1", "oldcode1", 8, "test", 1.0),
        ),
    )

    class FakeChain:
        async def chain_id(self):
            return 137

        async def head_poll(self, _interval):
            yield BlockState(11, "new11", "new10", 0, None, 0)

        async def block_by_number(self, number):
            return {
                8: BlockState(8, "new8", "h7", 0, None, 0),
                9: BlockState(9, "new9", "new8", 0, None, 0),
                10: BlockState(10, "new10", "new9", 0, None, 0),
                11: BlockState(11, "new11", "new10", 0, None, 0),
            }[number]

    class FakeScanner:
        async def scan(self, query):
            if query.from_block == 8:
                return [{"blockHash": "new8", "transactionHash": "newtx", "logIndex": "0x0"}]
            return []

    adapter = QuickSwapAdapter.__new__(QuickSwapAdapter)
    adapter.cache = StateCache()
    adapter.rejections = []
    adapter.deployments = []
    adapter._by_key = {}
    adapter.rpc = None

    candidate = DiscoveryCandidate(
        PoolCreated(
            "quickswap", "v2", "0x" + "1" * 40,
            "0x" + "2" * 40, "0x" + "3" * 40, "0x" + "5" * 40, 2
        ),
        8, "newtx", "new8", 0,
    )
    adapter.log_query = lambda pool_type, start, end: {
        "address": "0x" + "1" * 40, "topics": ["0xtopic"],
        "fromBlock": hex(start), "toBlock": hex(end),
    }
    adapter.decode_log = lambda pool_type, log: candidate

    async def reconcile(_candidate):
        return _candidate.created
    async def pool_state(_candidate, *, promote_cache=True):
        return PoolState(
            "0x" + "5" * 40, "quickswap", "v2", "0x" + "2" * 40, "0x" + "3" * 40,
            8, {"reserve0": 10, "reserve1": 20}, "newpool", "test", 1.0
        )
    async def token_state(address, block_number, *, promote_cache=True):
        return TokenState(address.lower(), 18, "T0" if address.endswith("2" * 40) else "T1",
                          "newcode", block_number, "test", 1.0)

    adapter.reconcile_candidate = reconcile
    adapter.read_pool_state = pool_state
    adapter._token_state = token_state

    coordinator = CanonicalCoordinator(store, overlap=3)
    plane = DataPlane(
        rpc=None, chain=FakeChain(), cache=adapter.cache,
        discovery=None, store=store, canonical=coordinator,
        scanner=FakeScanner(), quickswap=adapter,
    )
    seen = []

    async def record_block(block):
        seen.append(block.number)

    await plane.run_heads(record_block, poll_interval=0)

    assert seen == [8, 9, 10, 11]
    assert store.latest_canonical_head() == (11, "new11", "new10")
    assert store.canonical_records()
    assert all(record.block_hash == "new8" for record in store.canonical_records())
    assert any(record.block_hash == "old8" for record in store.orphaned_records())


@pytest.mark.asyncio
async def test_deep_reorg_replaces_orphaned_lower_height_snapshots_and_restart_restores(tmp_path):
    """A deep reorg must allow a lower-height replacement to replace orphaned state."""
    from ghost_hunter.data_plane.store import DiscoveryStore

    db_path = tmp_path / "snapshot-reorg.sqlite"
    store = DiscoveryStore(db_path)
    for number, block_hash, parent_hash in [
        (7, "h7", "h6"),
        (8, "old8", "h7"),
        (9, "old9", "old8"),
        (10, "old10", "old9"),
    ]:
        store.record_block(number, block_hash, parent_hash)

    pool_address = "0x" + "4" * 40
    token0 = "0x" + "2" * 40
    token1 = "0x" + "3" * 40
    old_pool = PoolState(
        pool_address, "quickswap", "v2", token0, token1, 10,
        {"reserve0": 100, "reserve1": 200}, "old-pool", "test", 1.0,
    )
    old_token0 = TokenState(token0, 18, "OLD0", "old-code0", 10, "test", 1.0)
    old_token1 = TokenState(token1, 18, "OLD1", "old-code1", 10, "test", 1.0)
    assert store.record_pool_snapshot(old_pool) is True
    assert store.record_token_snapshot(old_token0) is True
    assert store.record_token_snapshot(old_token1) is True

    store.rewind_from(8)
    assert store.canonical_pool_snapshots() == []
    assert store.canonical_token_snapshots() == []

    for number, block_hash, parent_hash in [
        (8, "new8", "h7"),
        (9, "new9", "new8"),
        (10, "new10", "new9"),
        (11, "new11", "new10"),
    ]:
        store.record_block(number, block_hash, parent_hash)

    new_pool = PoolState(
        pool_address, "quickswap", "v2", token0, token1, 8,
        {"reserve0": 10, "reserve1": 20}, "new-pool", "test", 1.0,
    )
    new_token0 = TokenState(token0, 18, "NEW0", "new-code0", 8, "test", 1.0)
    new_token1 = TokenState(token1, 18, "NEW1", "new-code1", 8, "test", 1.0)
    assert store.record_pool_snapshot(new_pool) is True
    assert store.record_token_snapshot(new_token0) is True
    assert store.record_token_snapshot(new_token1) is True

    pools = store.canonical_pool_snapshots()
    tokens = store.canonical_token_snapshots()
    assert [(p.address, p.block_number, p.state_hash) for p in pools] == [
        (pool_address, 8, "new-pool")
    ]
    assert {(t.address, t.block_number, t.code_hash) for t in tokens} == {
        (token0, 8, "new-code0"),
        (token1, 8, "new-code1"),
    }

    restarted = DiscoveryStore(db_path)
    cache = StateCache()
    cache.restore(restarted.canonical_token_snapshots(), restarted.canonical_pool_snapshots())

    assert restarted.latest_canonical_head() == (11, "new11", "new10")
    assert cache.pools[pool_address].block_number == 8
    assert cache.pools[pool_address].state_hash == "new-pool"
    assert cache.tokens[token0].block_number == 8
    assert cache.tokens[token0].code_hash == "new-code0"
    assert cache.tokens[token1].block_number == 8
    assert cache.tokens[token1].code_hash == "new-code1"


@pytest.mark.asyncio
async def test_quickswap_persistence_failure_aborts_deep_reorg_replay(tmp_path):
    """Durable evidence failure must roll back the whole replay, not be downgraded to a rejection."""
    from ghost_hunter.data_plane.models import BlockState, PoolState, TokenState
    from ghost_hunter.data_plane.orchestrator import DataPlane
    from ghost_hunter.data_plane.pool_events import PoolCreated
    from ghost_hunter.data_plane.quickswap import (
        DiscoveryCandidate,
        DiscoveryPersistenceError,
        QuickSwapAdapter,
    )
    from ghost_hunter.data_plane.reorg import CanonicalCoordinator
    from ghost_hunter.data_plane.store import DiscoveryStore

    class FailingStore(DiscoveryStore):
        def record_discovery_bundle(self, *args, **kwargs):
            raise RuntimeError("simulated durable write failure")

    store = FailingStore(tmp_path / "persistence-failure.sqlite")
    for number, block_hash, parent_hash in [
        (7, "h7", "h6"),
        (8, "old8", "h7"),
        (9, "old9", "old8"),
        (10, "old10", "old9"),
    ]:
        store.record_block(number, block_hash, parent_hash)

    class FakeChain:
        async def chain_id(self):
            return 137

        async def head_poll(self, _interval):
            yield BlockState(11, "new11", "new10", 0, None, 0)

        async def block_by_number(self, number):
            return {
                8: BlockState(8, "new8", "h7", 0, None, 0),
                9: BlockState(9, "new9", "new8", 0, None, 0),
                10: BlockState(10, "new10", "new9", 0, None, 0),
                11: BlockState(11, "new11", "new10", 0, None, 0),
            }[number]

    class FakeScanner:
        async def scan(self, query):
            if query.from_block == 8:
                return [{
                    "blockHash": "new8",
                    "transactionHash": "newtx",
                    "logIndex": "0x0",
                }]
            return []

    adapter = QuickSwapAdapter.__new__(QuickSwapAdapter)
    adapter.cache = StateCache()
    adapter.rejections = []
    adapter.deployments = []
    adapter._by_key = {}
    adapter.rpc = None

    candidate = DiscoveryCandidate(
        PoolCreated(
            "quickswap", "v2", "0x" + "1" * 40,
            "0x" + "2" * 40, "0x" + "3" * 40, "0x" + "5" * 40, 2
        ),
        8, "newtx", "new8", 0,
    )
    adapter.log_query = lambda pool_type, start, end: {
        "address": "0x" + "1" * 40,
        "topics": ["0xtopic"],
        "fromBlock": hex(start),
        "toBlock": hex(end),
    }
    adapter.decode_log = lambda pool_type, log: candidate

    async def reconcile(_candidate):
        return _candidate.created

    async def pool_state(_candidate, *, promote_cache=True):
        return PoolState(
            "0x" + "5" * 40, "quickswap", "v2",
            "0x" + "2" * 40, "0x" + "3" * 40, 8,
            {"reserve0": 10, "reserve1": 20}, "new-pool", "test", 1.0,
        )

    async def token_state(address, block_number, *, promote_cache=True):
        return TokenState(
            address.lower(), 18,
            "T0" if address.endswith("2" * 40) else "T1",
            "new-code", block_number, "test", 1.0,
        )

    adapter.reconcile_candidate = reconcile
    adapter.read_pool_state = pool_state
    adapter._token_state = token_state

    coordinator = CanonicalCoordinator(store, overlap=3)
    plane = DataPlane(
        rpc=None, chain=FakeChain(), cache=adapter.cache,
        discovery=None, store=store, canonical=coordinator,
        scanner=FakeScanner(), quickswap=adapter,
    )

    with pytest.raises(DiscoveryPersistenceError):
        await plane.run_heads(lambda _block: None, poll_interval=0)

    assert store.latest_canonical_head() == (7, "h7", "h6")
    assert store.canonical_records() == []
    assert adapter.cache.pools == {}
    assert adapter.cache.tokens == {}
