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
            assert reopened.canonical_token_snapshots() == [token().__class__("0xtoken", 18, "TOK", "code-10", 10, "quorum", 0.99)]
            assert reopened.canonical_pool_snapshots() == [pool().__class__("0xpool", "quickswap", "v2", "0xtoken", "0xother", 10, {"reserve0": 10, "reserve1": 20}, "state-10", "quorum", 0.99)]


def test_older_snapshot_cannot_replace_newer_snapshot():
    with DiscoveryStore() as store:
        store.record_block(9, "h9", "h8")
        store.record_block(10, "h10", "h9")
        assert store.record_token_snapshot(token(10, "NEW"))
        assert not store.record_token_snapshot(token(9, "OLD"))
        assert store.canonical_token_snapshots() == [token(10, "NEW").__class__("0xtoken", 18, "NEW", "code-10", 10, "quorum", 0.99)]

        assert store.record_pool_snapshot(pool(10))
        assert not store.record_pool_snapshot(pool(9, {"reserve0": 1, "reserve1": 2}))
        assert store.canonical_pool_snapshots() == [pool(10).__class__("0xpool", "quickswap", "v2", "0xtoken", "0xother", 10, {"reserve0": 10, "reserve1": 20}, "state-10", "quorum", 0.99)]


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
        assert store.canonical_token_snapshots() == [replacement_token.__class__("0xtoken", 18, "FORK", "code-10", 10, "quorum", 0.99)]
        assert store.canonical_pool_snapshots() == [replacement_pool.__class__("0xpool", "quickswap", "v2", "0xtoken", "0xother", 10, {"reserve0": 7, "reserve1": 11}, "state-10", "quorum", 0.99)]


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


def test_record_block_rejects_missing_or_mismatched_predecessor():
    with DiscoveryStore() as store:
        store.record_block(10, "h10", "h9")
        store.record_block(11, "h11", "h10")
        with pytest.raises(ValueError, match="predecessor"):
            store.record_block(12, "h12", "wrong-parent")


def test_latest_canonical_head_fails_on_deep_ancestry_corruption():
    with DiscoveryStore() as store:
        store.record_block(0, "h0", "genesis")
        store.record_block(1, "h1", "h0")
        store.record_block(2, "h2", "h1")
        store._db.execute("UPDATE blocks SET parent_hash='corrupt' WHERE number=2")
        store._db.commit()
        with pytest.raises(RuntimeError, match="inconsistent"):
            store.latest_canonical_head()

def test_reorg_restart_reconstructs_only_replacement_fork_state():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "reorg-restart.sqlite"

        with DiscoveryStore(path) as store:
            store.record_block(9, "h9", "h8")
            store.record_block(10, "old10", "h9")
            old_token = token(10, "OLD")
            old_pool = pool(10, {"reserve0": 100, "reserve1": 200})
            store.record_token_snapshot(old_token)
            store.record_pool_snapshot(old_pool)

            store.rewind_from(10)
            assert store.canonical_token_snapshots() == []
            assert store.canonical_pool_snapshots() == []

            store.record_block(10, "new10", "h9")
            store.record_block(11, "new11", "new10")
            new_token = token(11, "NEW")
            new_pool = pool(11, {"reserve0": 7, "reserve1": 11})
            assert store.record_token_snapshot(new_token)
            assert store.record_pool_snapshot(new_pool)
            assert store.latest_canonical_head() == (11, "new11", "new10")

            store._db.execute("UPDATE token_snapshots SET status='canonical' WHERE address=?", (old_token.address.lower(),))
            store._db.execute("UPDATE pool_snapshots SET status='canonical' WHERE address=?", (old_pool.address.lower(),))
            store._db.commit()

        with DiscoveryStore(path) as reopened:
            assert reopened.canonical_token_snapshots() == [
                new_token.__class__("0xtoken", 18, "NEW", "code-11", 11, "quorum", 0.99)
            ]
            assert reopened.canonical_pool_snapshots() == [
                new_pool.__class__(
                    "0xpool", "quickswap", "v2", "0xtoken", "0xother", 11,
                    {"reserve0": 7, "reserve1": 11}, "state-11", "quorum", 0.99
                )
            ]
            assert reopened.latest_canonical_head() == (11, "new11", "new10")
