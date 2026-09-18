from ghost_hunter.data_plane.protocols import VerifiedDeployment
from ghost_hunter.data_plane.deployment_verifier import (
    ALL_PAIRS_LENGTH_SELECTOR,
    OWNER_SELECTOR,
    verify_deployment,
)


def _deployment(pool_type="v2"):
    return VerifiedDeployment(
        venue="quickswap",
        pool_type=pool_type,
        chain_id=137,
        factory="0x" + "1" * 40,
        source_url="test",
        source_verified=True,
        event_signature="PairCreated(address,address,address,uint256)"
        if pool_type == "v2" else "Pool(address,address,address)",
    )


class FakeRPC:
    def __init__(self, *, chain_id=137, code="0x6000", owner="0x" + "0"*64, pairs="0x" + "0"*64):
        self.chain_id = chain_id
        self.code = code
        self.owner = owner
        self.pairs = pairs
        self.calls = []

    async def __call__(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId":
            return hex(self.chain_id)
        if method == "eth_getCode":
            return self.code
        if method == "eth_call":
            data = params[0]["data"]
            if data == OWNER_SELECTOR:
                return self.owner
            if data == ALL_PAIRS_LENGTH_SELECTOR:
                return self.pairs
        raise AssertionError(f"unexpected RPC call: {method} {params}")


async def test_quickswap_v2_runtime_verification_passes():
    rpc = FakeRPC()
    evidence = await verify_deployment(_deployment("v2"), rpc)
    assert evidence.verified
    assert evidence.code_present
    assert evidence.provider_agreement
    assert evidence.interface_checks == ("chain_id", "runtime_code", "owner()", "allPairsLength()")


async def test_wrong_chain_is_hard_rejected():
    evidence = await verify_deployment(_deployment(), FakeRPC(chain_id=1))
    assert not evidence.verified
    assert evidence.reason == "wrong_chain_id"


async def test_empty_runtime_code_is_hard_rejected():
    evidence = await verify_deployment(_deployment(), FakeRPC(code="0x"))
    assert not evidence.verified
    assert evidence.reason == "factory_has_no_runtime_code"


async def test_interface_failure_is_hard_rejected():
    evidence = await verify_deployment(_deployment(), FakeRPC(owner="0x"))
    assert not evidence.verified
    assert evidence.reason == "owner_interface_failed"


async def test_v3_requires_runtime_code_and_common_factory_interface():
    rpc = FakeRPC()
    evidence = await verify_deployment(_deployment("algebra_v3"), rpc)
    assert evidence.verified
    assert evidence.interface_checks == ("chain_id", "runtime_code", "owner()")
