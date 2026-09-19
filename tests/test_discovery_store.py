import tempfile
from pathlib import Path

import pytest

from ghost_hunter.data_plane.models import PoolState, TokenState
from ghost_hunter.data_plane.store import DiscoveryStore


def token(block=10, symbol="TOK"):
    return TokenState("0xTOKEN", 18, symbol, f"code-{block}", block, "quorum", 0.99)


def pool(block=10, state=None):
    state = state or {"reserve0": block, "reserve1": block * 2}
    return PoolState(
        "0xPOOL", "quickswap", "v2", "0xTOKEN", "0xOTHER",
        block, state, f"state-{block}", "quorum", 0.99,
    )


def test_snapshots_persist_across_restart():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "snapshots.sqlite"
        with DiscoveryStore(path) as store:
            store.record_block(10, "h10", "h9")
            assert store.record_token_snapshot(token())
            assert store.record_pool_snapshot(pool())

        with DiscoveryStore(path) as reopened:
            assert reopened.canonical_token_snapshots() == [token()]
            assert reopened.canonical_pool_snapshots() == [pool()]


def test_older_snapshot_cannot_replace_newer_snapshot():
    with DiscoveryStore() as store:
        store.record_block(9, "h9", "h8")
        store.record_block(10, "h10", "h9")
        assert store.record_token_snapshot(token(10, "NEW"))
        assert not store.record_token_snapshot(token(9, "OLD"))
        assert store.canonical_token_snapshots() == [token(10, "NEW")]

        assert store.record_pool_snapshot(pool(10))
        assert not store.record_pool_snapshot(pool(9, {"reserve0": 1, "reserve1": 2}))
        assert store.canonical_pool_snapshots() == [pool(10)]


def test_reorg_orphans_snapshots_and_replacement_can_be_recorded():
    with DiscoveryStore() as store:
        store.record_block(10, "h10", "h9")
        store.record_token_snapshot(token())
        store.record_pool_snapshot(pool())

        store.rewind_from(10)
        assert store.canonical_token_snapshots() == []
        assert store.canonical_pool_snapshots() == []

        store.record_block(10, "fork10", "h9")
        replacement_token = token(10, "FORK")
        replacement_pool = pool(10, {"reserve0": 7, "reserve1": 11})
        assert store.record_token_snapshot(replacement_token)
        assert store.record_pool_snapshot(replacement_pool)
        assert store.canonical_token_snapshots() == [replacement_token]
        assert store.canonical_pool_snapshots() == [replacement_pool]


def test_snapshot_requires_canonical_block_anchor():
    with DiscoveryStore() as store:
        with pytest.raises(ValueError, match="anchored"):
            store.record_token_snapshot(token())
        with pytest.raises(ValueError, match="anchored"):
            store.record_pool_snapshot(pool())


def test_snapshot_state_hash_and_payload_survive_restart():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "snapshots.sqlite"
        expected = pool(10, {"sqrt_price": 123, "liquidity": 456})
        with DiscoveryStore(path) as store:
            store.record_block(10, "h10", "h9")
            assert store.record_pool_snapshot(expected)

        with DiscoveryStore(path) as reopened:
            actual = reopened.canonical_pool_snapshots()[0]
            assert actual.state == expected.state
            assert actual.state_hash == expected.state_hash
            assert actual.block_number == expected.block_number
