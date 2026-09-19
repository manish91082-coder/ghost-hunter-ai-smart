import json
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


@pytest.mark.asyncio
async def test_quorum_call_accepts_equivalent_mapping_results(monkeypatch):
    first = RPCProvider("first", "https://first.example")
    second = RPCProvider("second", "https://second.example")
    rpc = MultiRPC([first, second])

    async def fake_post(provider, payload):
        if provider is first:
            return {"jsonrpc": "2.0", "id": 1, "result": {"b": 2, "a": 1}}
        return {"jsonrpc": "2.0", "id": 2, "result": {"a": 1, "b": 2}}

    monkeypatch.setattr(rpc, "_post", fake_post)
    result = await rpc.quorum_call("eth_call", quorum=2)
    assert result == {"b": 2, "a": 1}
