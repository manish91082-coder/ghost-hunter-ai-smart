from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from .protocols import VerifiedDeployment

ZERO_ADDRESS = "0x" + "0" * 40

# Canonical Solidity selectors used only for read-only interface probes.
OWNER_SELECTOR = "0x8da5cb5b"
ALL_PAIRS_LENGTH_SELECTOR = "0x574f2ba3"


@dataclass(frozen=True)
class DeploymentEvidence:
    venue: str
    pool_type: str
    chain_id: int
    factory: str
    code_present: bool
    interface_checks: tuple[str, ...]
    provider_agreement: bool
    verified: bool
    reason: str


RpcCall = Callable[[str, list[object]], Awaitable[object]]


def _has_code(raw: object) -> bool:
    return isinstance(raw, str) and raw.startswith("0x") and len(raw) > 2


def _is_nonempty_hex(raw: object) -> bool:
    return isinstance(raw, str) and raw.startswith("0x") and len(raw) > 2


async def verify_deployment(
    deployment: VerifiedDeployment,
    rpc_call: RpcCall,
    *,
    expected_chain_id: int = 137,
) -> DeploymentEvidence:
    checks: list[str] = []

    chain_raw = await rpc_call("eth_chainId", [])
    try:
        chain_id = int(str(chain_raw), 16)
    except (TypeError, ValueError):
        return DeploymentEvidence(
            deployment.venue, deployment.pool_type, -1, deployment.factory,
            False, tuple(checks), False, False, "invalid_chain_id"
        )

    if chain_id != expected_chain_id or chain_id != deployment.chain_id:
        return DeploymentEvidence(
            deployment.venue, deployment.pool_type, chain_id, deployment.factory,
            False, tuple(checks), False, False, "wrong_chain_id"
        )
    checks.append("chain_id")

    code = await rpc_call("eth_getCode", [deployment.factory, "latest"])
    if not _has_code(code):
        return DeploymentEvidence(
            deployment.venue, deployment.pool_type, chain_id, deployment.factory,
            False, tuple(checks), False, False, "factory_has_no_runtime_code"
        )
    checks.append("runtime_code")

    # owner() is shared by the documented QuickSwap V2 factory and AlgebraFactory.
    owner = await rpc_call("eth_call", [{"to": deployment.factory, "data": OWNER_SELECTOR}, "latest"])
    if not _is_nonempty_hex(owner):
        return DeploymentEvidence(
            deployment.venue, deployment.pool_type, chain_id, deployment.factory,
            True, tuple(checks), False, False, "owner_interface_failed"
        )
    checks.append("owner()")

    if deployment.pool_type == "v2":
        pairs = await rpc_call(
            "eth_call",
            [{"to": deployment.factory, "data": ALL_PAIRS_LENGTH_SELECTOR}, "latest"],
        )
        if not _is_nonempty_hex(pairs):
            return DeploymentEvidence(
                deployment.venue, deployment.pool_type, chain_id, deployment.factory,
                True, tuple(checks), False, False, "allPairsLength_interface_failed"
            )
        checks.append("allPairsLength()")

    return DeploymentEvidence(
        deployment.venue,
        deployment.pool_type,
        chain_id,
        deployment.factory,
        True,
        tuple(checks),
        True,
        True,
        "verified",
    )
