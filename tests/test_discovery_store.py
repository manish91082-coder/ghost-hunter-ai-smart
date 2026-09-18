import tempfile
from pathlib import Path

import pytest

from ghost_hunter.data_plane.store import DiscoveryRecord, DiscoveryStore


def record(store, key="v2:v2:0xpool:10", block_hash="h10", payload=None):
    payload = payload or {"pool": "0xpool", "block": 10}
    return DiscoveryRecord(
        key, "quickswap", "v2", "0xPOOL", 10, block_hash,
        "0xtx", 3, store.payload_hash(payload)
    ), payload


def test_missing_block_hash_is_rejected():
    with DiscoveryStore() as store:
        store.record_block(10, "h10", "h9")
        rec, payload = record(store, block_hash="")
        with pytest.raises(ValueError, match="block_hash"):
            store.record_discovery(rec, payload)


def test_discovery_is_idempotent_and_persisted_across_restart():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "discovery.sqlite"
        with DiscoveryStore(path) as store:
            store.record_block(10, "h10", "h9")
            rec, payload = record(store)
            assert store.record_discovery(rec, payload)
            assert not store.record_discovery(rec, payload)
        with DiscoveryStore(path) as reopened:
            assert reopened.get(rec.candidate_key) == rec
            assert len(reopened.canonical_records()) == 1


def test_payload_mutation_on_replay_fails_closed():
    with DiscoveryStore() as store:
        store.record_block(10, "h10", "h9")
        rec, payload = record(store)
        assert store.record_discovery(rec, payload)
        changed = {"pool": "0xchanged", "block": 10}
        with pytest.raises(ValueError, match="payload mismatch"):
            store.record_discovery(rec, changed)


def test_reorg_orphans_discoveries_from_fork_point():
    with DiscoveryStore() as store:
        store.record_block(10, "h10", "h9")
        rec, payload = record(store)
        store.record_discovery(rec, payload)
        assert store.rewind_from(10) == 1
        assert not store.canonical_records()
        assert store.orphaned_records()[0].status == "orphaned"
        store.record_block(10, "fork10", "h9")
        replacement = DiscoveryRecord(
            rec.candidate_key + ":replacement", "quickswap", "v2", "0xNEW",
            10, "fork10", "0xtx2", 4,
            store.payload_hash({"pool": "0xNEW", "block": 10})
        )
        assert store.record_discovery(replacement, {"pool": "0xNEW", "block": 10})
        assert len(store.canonical_records()) == 1


def test_block_hash_change_automatically_invalidates_old_chain():
    with DiscoveryStore() as store:
        store.record_block(10, "h10", "h9")
        rec, payload = record(store)
        store.record_discovery(rec, payload)
        store.record_block(10, "fork10", "h9")
        assert store.get(rec.candidate_key).status == "orphaned"
        assert not store.canonical_records()
