import pytest

from ghost_hunter.data_plane.rpc import MultiRPC, RPCError, RPCProvider


def test_ordered_never_falls_back_to_quarantined_provider():
    quarantined = RPCProvider("quarantined", "https://quarantined.example", state="quarantined")
    disabled = RPCProvider("disabled", "https://disabled.example", state="disabled")
    rpc = MultiRPC([quarantined, disabled])

    with pytest.raises(RPCError, match="no usable RPC providers"):
        rpc._ordered()


def test_ordered_fails_closed_when_capability_is_unavailable():
    generic = RPCProvider("generic", "https://generic.example", capabilities={"eth_call"})
    trace = RPCProvider("trace", "https://trace.example", capabilities={"trace"}, state="quarantined")
    rpc = MultiRPC([generic, trace])

    with pytest.raises(RPCError, match="capability 'trace'"):
        rpc._ordered("trace")


def test_ordered_allows_unrestricted_provider_for_capability():
    generic = RPCProvider("generic", "https://generic.example")
    trace = RPCProvider("trace", "https://trace.example", capabilities={"trace"})
    rpc = MultiRPC([generic, trace])

    assert [p.name for p in rpc._ordered("trace")] == ["generic", "trace"]
