from ghost_hunter.data_plane.discovery import VenueAdapterSpec, DiscoveryEngine
from ghost_hunter.data_plane.cache import StateCache
from ghost_hunter.data_plane.events import EventRegistry, EventTopic
from ghost_hunter.data_plane.reorg import CanonicalHead, ReorgGuard
from ghost_hunter.data_plane.scanner import AdaptiveLogScanner, LogQuery
from ghost_hunter.data_plane.wss import PolygonWSS, WSSProvider


def test_event_registry_requires_verified_topic():
    reg = EventRegistry()
    try:
        reg.register_verified(EventTopic("X", "X()", "bad"))
        assert False
    except ValueError:
        pass


def test_reorg_guard_detects_parent_mismatch():
    g = ReorgGuard()
    assert g.accept(CanonicalHead(10, "h10", "h9"))
    assert not g.accept(CanonicalHead(11, "fork11", "different"))
    assert g.rescan_start(11) == 0


def test_discovery_venues_are_deduplicated():
    d = DiscoveryEngine(StateCache())
    d.register(VenueAdapterSpec("demo", ("v2",), ("0xF",), "factory-events"))
    d.register(VenueAdapterSpec("demo", ("v3",), ("0xG",), "factory-events"))
    assert d.all_venues() == ("demo",)


def test_wss_fleet_retains_all_endpoints():
    providers = [WSSProvider("wss-a", "ws://a"), WSSProvider("wss-b", "ws://b")]
    fleet = PolygonWSS(providers)
    providers[0].record(False, 100.0)
    providers[0].record(False, 100.0)
    providers[0].record(False, 100.0)
    assert providers[0].state == "cooldown"
    assert len(fleet.providers) == 2


def test_wss_health_is_based_on_subscription_confirmation():
    provider = WSSProvider("wss-a", "ws://a")
    fleet = PolygonWSS([provider])
    assert fleet.providers[0].available


def test_quickswap_polygon_deployments_are_source_verified():
    from ghost_hunter.data_plane.protocols import verified_deployments

    deployments = verified_deployments(137)
    assert {d.pool_type for d in deployments} == {"v2", "algebra_v3"}
    assert all(d.source_verified for d in deployments)
    assert all(d.chain_id == 137 for d in deployments)
    assert len({d.factory.lower() for d in deployments}) == 2


from ghost_hunter.data_plane.reorg import CanonicalCoordinator, CanonicalHead, ReorgGuard
from ghost_hunter.data_plane.store import DiscoveryStore


def test_reorg_guard_does_not_advance_on_discontinuity():
    g = ReorgGuard()
    assert g.accept(CanonicalHead(10, "h10", "h9"))
    assert not g.accept(CanonicalHead(11, "fork11", "wrong"))
    assert g.head.number == 10


def test_coordinator_rewinds_on_fork_and_replays():
    with DiscoveryStore() as store:
        c = CanonicalCoordinator(store, overlap=3)
        assert c.observe(CanonicalHead(10, "h10", "h9")) == (True, None)
        assert c.observe(CanonicalHead(11, "fork11", "wrong")) == (False, 8)
        assert store.canonical_records() == []
        assert c.record_replayed_block(CanonicalHead(10, "fork10", "h9"))
        assert c.record_replayed_block(CanonicalHead(11, "fork11", "fork10"))


def test_same_head_is_idempotent():
    with DiscoveryStore() as store:
        c = CanonicalCoordinator(store)
        head = CanonicalHead(10, "h10", "h9")
        assert c.observe(head) == (True, None)
        assert c.observe(head) == (True, None)
