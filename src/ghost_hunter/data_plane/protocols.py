from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerifiedDeployment:
    venue: str
    pool_type: str
    chain_id: int
    factory: str
    source_url: str
    source_verified: bool
    event_signature: str


# Addresses are sourced from the protocol's published Polygon deployment page.
# They are deployment anchors, not a static pool list. Pools remain runtime-discovered.
VERIFIED_DEPLOYMENTS: tuple[VerifiedDeployment, ...] = (
    VerifiedDeployment(
        venue="quickswap",
        pool_type="v2",
        chain_id=137,
        factory="0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
        source_url="https://docs.quickswap.exchange/overview/contracts-and-addresses",
        source_verified=True,
        event_signature="PairCreated(address,address,address,uint256)",
    ),
    VerifiedDeployment(
        venue="quickswap",
        pool_type="algebra_v3",
        chain_id=137,
        factory="0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28",
        source_url="https://docs.quickswap.exchange/technical-reference/smart-contracts/v3/factory",
        source_verified=True,
        event_signature="Pool(address,address,address)",
    ),
)


def verified_deployments(chain_id: int = 137) -> tuple[VerifiedDeployment, ...]:
    return tuple(d for d in VERIFIED_DEPLOYMENTS if d.chain_id == chain_id)
