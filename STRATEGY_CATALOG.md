# STRATEGY CATALOG — POLYGON FLASH-LOAN ENGINE

## Strategy Family A — Direct Cross-DEX Arbitrage
Borrow A -> swap A/B on venue X -> swap B/A on venue Y -> repay A.

Variants:
- V2/V2
- V2/V3
- V3/V2
- V3/V3
- Algebra/V2
- StableSwap/V2
- StableSwap/V3

## Strategy Family B — V3 Fee-Tier Arbitrage
Same token pair across multiple concentrated-liquidity pools with different fee tiers.

The engine must account for:
- current sqrtPriceX96
- liquidity
- active tick
- tick spacing
- fee
- amount-dependent price impact

## Strategy Family C — Triangular Arbitrage
A -> B -> C -> A.

The graph engine searches cycles and rejects cycles whose exact post-fee result does not exceed the threshold.

## Strategy Family D — Multi-Hop Cross-Venue
A -> B -> C -> D -> A, where each edge may use a different venue and pool type.

The route optimizer must compare:
- fewer hops / lower gas
- more hops / better price
- pool depth
- failure probability

## Strategy Family E — Stablecoin Arbitrage
USDC/USDT/DAI/other verified stable assets and Polygon-native stablecoin pools.

Stable routes require additional depeg and oracle-risk checks.

## Strategy Family F — Concentrated-Liquidity Micro-Arbitrage
Detect small price dislocations near active ticks.

Candidate generation must be amount-aware because the opportunity can disappear as trade size changes.

## Strategy Family G — Balancer Multi-Asset Paths
Weighted/composable stable pools may provide non-two-token routing opportunities.

Pool weights and balances must be read dynamically.

## Strategy Family H — Curve Stable / FX Paths
Curve pools on Polygon can expose stable and FX liquidity. These routes require pool-type-specific invariant math.

## Strategy Family I — Cross-Source Router Disagreement
Compare direct pool math with aggregator quotes as an independent signal, but never trust an aggregator quote as the sole execution truth.

## Strategy Family J — Backrun / State-Change Arbitrage
Detect state changes from confirmed or eligible orderflow and calculate whether a resulting price dislocation can be captured without violating the project's anti-sandwich policy.

## Strategy Family K — Liquidation-Adjacent Opportunities
Only if a mathematically atomic, fully collateralized, legally/technically acceptable path exists. These remain a later-stage strategy class.

## Strategy Family L — Statistical / ML Candidate Ranking
AI ranks candidates using:
- liquidity
- historical fill probability
- volatility
- route stability
- gas
- competition
- expected edge persistence
- simulation confidence

ML ranking cannot replace exact deterministic profit calculation.

## Strategy Rejection Classes
A candidate is rejected when:
- net profit <= $0.20
- any cost is unknown
- simulation reverts
- required liquidity is unavailable
- state is stale
- token behavior is uncertain
- price impact exceeds policy
- private submission unavailable for a strategy requiring confidentiality
- wallet gas floor would be violated
- contract/route not allowlisted
- realized-probability confidence is below policy

## Profit Formula
ExpectedNetUSD =
GrossOutputUSD
- PrincipalRepaymentUSD
- FlashLoanFeeUSD
- DEXFeesUSD
- GasCostUSD
- SlippageCostUSD
- RouteCostUSD
- ProtocolFeesUSD
- SafetyReserveUSD

Eligibility:
ExpectedNetUSD > 0.20

The engine must calculate at the exact candidate amount, not from percentage spread alone.

## Critical Reality Rule
A positive theoretical spread does not imply executable profit. The final authority is exact state-aware simulation plus independent realized balance reconciliation.
