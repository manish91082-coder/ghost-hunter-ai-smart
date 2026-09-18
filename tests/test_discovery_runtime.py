from ghost_hunter.data_plane.discovery import VenueAdapterSpec, DiscoveryEngine
from ghost_hunter.data_plane.cache import StateCache
from ghost_hunter.data_plane.events import EventRegistry, EventTopic
from ghost_hunter.data_plane.reorg import CanonicalHead, ReorgGuard
from ghost_hunter.data_plane.scanner import AdaptiveLogScanner, LogQuery


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
    assert g.rescan_start(11, 12) == 0


def test_discovery_venues_are_deduplicated():
    d = DiscoveryEngine(StateCache())
    d.register(VenueAdapterSpec("demo", ("v2",), ("0xF",), "factory-events"))
    d.register(VenueAdapterSpec("demo", ("v3",), ("0xG",), "factory-events"))
    assert d.all_venues() == ("demo",)
