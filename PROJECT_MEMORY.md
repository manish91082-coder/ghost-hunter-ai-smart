# PROJECT MEMORY

## Project Identity
- Repository: `manish91082-coder/ghost-hunter-ai-smart`
- Visibility: PUBLIC
- Default branch: `main`
- Repository ID: `1376339960`
- Project working name: Ghost Hunter AI Smart
- Focus: Polygon PoS dynamic flash-loan arbitrage intelligence and controlled execution.
- Legacy repositories are isolated and must not be modified.

## Governing Objective
Build a production-grade, evidence-driven, AI-assisted but deterministic-verifier-controlled system that continuously discovers Polygon liquidity venues, pools, pairs, routes and flash-loan arbitrage opportunities.

Hard economic eligibility gate:
**Expected verified net profit must be strictly greater than USD 0.20 after all modeled execution costs.**

This is an eligibility threshold, not a guarantee of realized profit.

## Absolute Rules
1. All market-dependent values are dynamic.
2. No static pair/pool list is authoritative.
3. Discovery must reconcile on-chain events/state with trusted secondary sources.
4. AI proposes; deterministic mathematics verifies; security policy authorizes; executor submits; independent reconciliation proves realized PnL.
5. Never submit without passing exact state-aware simulation.
6. Never submit when a material cost or required state is unknown.
7. Never bypass safety gates to force a trade.
8. Never modify legacy repositories.
9. Every project-driving response updates durable project state in GitHub.
10. Every future project agent reads PROJECT_STATUS.md and PROJECT_MEMORY.md before acting.
11. `next` means inspect -> decide -> execute permitted next step -> validate -> persist -> report.
12. Historical chat claims never override current verified repository state.
13. ZERO-COST-FIRST is non-negotiable.

## Profit Model
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
**ExpectedNetUSD > 0.20**

The calculation is exact, amount-specific and state-specific.

## Zero-Gas-Loss Interpretation
A reverted transaction can consume gas. Literal post-submission zero gas loss cannot be guaranteed.

Engineering objective:
- exact preflight
- simulation
- private submission where required
- atomic execution
- hard gas ceiling
- native-balance floor
- strict profitability invariant
- automatic rejection under uncertainty
- independent receipt/PnL reconciliation

## Conceptual System Model
The system is a dynamic market graph plus deterministic proof engine.

Core loop:
**CHAIN STATE -> DISCOVERY -> NORMALIZATION -> LIQUIDITY GRAPH -> SIGNALS -> ROUTE/AMOUNT SEARCH -> EXACT MATH -> FULL ECONOMICS -> SIMULATION -> ADVERSARIAL CHECK -> PROFIT GATE -> AUTHORIZATION -> EXECUTION -> RECEIPT -> REALIZED PnL -> LEARNING**

## Mathematical Model
Supported pool math families:
- V2 constant-product
- V3/Algebra concentrated liquidity
- StableSwap
- weighted/composable pools

Execution-critical math:
- integer base units
- explicit on-chain rounding
- amount-dependent price impact
- dynamic fees
- dynamic liquidity/state
- exact repayment

Floating point is not authoritative.

## Strategy Search Space
The engine explores combinations of:
- flash/start asset
- token pairs
- venue/pool
- pool type
- fee tier
- direction
- hop count
- route ordering
- cycle length
- amount
- amount split
- concentrated-liquidity boundaries
- gas state
- state freshness
- submission method
- historical execution profile

Because full enumeration is combinatorially expensive, a staged search funnel is mandatory:
**structural filter -> conservative upper bound -> exact quote -> amount optimization -> full economics -> simulation -> adversarial security -> authorization.**

## Strategy Families
Initial and future families include:
- two-leg cross-venue
- V2/V2
- V2/V3
- V3/V2
- V3/V3
- fee-tier arbitrage
- triangular
- multi-hop
- stablecoin
- concentrated-liquidity micro-arbitrage
- StableSwap
- weighted/composable
- state-change/backrun subject to policy
- router disagreement as a signal
- ML/statistical ranking

Signals never authorize execution.

## Amount Optimization
Profit is generally non-linear with trade size.

The optimizer may evaluate:
- logarithmic samples
- liquidity-derived boundaries
- fee/gas break-even points
- tick boundaries
- local maxima
- discrete refinement

No global-optimum assumption is accepted without evidence.

## Robustness
Track:
- ExpectedNetUSD
- RobustNetUSD
- sensitivity to amount
- gas
- price movement
- liquidity/state movement
- latency

A fragile edge can be rejected even if its raw expected profit passes.

## Hard Execution Invariants
Reject if:
- profit <= $0.20
- material cost unknown
- stale state
- simulation failure
- route mismatch
- unallowlisted contract
- wallet/gas floor failure
- unresolved token behavior
- required private path unavailable
- security check failure
- nonce conflict

## Realized PnL
Predicted, simulated and realized PnL remain separate.

Realized PnL is derived independently from:
- receipt
- gas used/effective price
- token balance deltas
- native balance delta
- flash repayment
- actual fees

A model number can never be relabeled as realized profit.

## Zero-Cost Architecture
Mandatory development path:
- local compute
- Python/Node.js
- Docker
- open-source libraries
- SQLite/DuckDB/JSONL/Parquet
- local/fork simulation
- free RPC/API tiers where available
- local/free AI where useful

No paid dependency is mandatory.

## Wallet Constraint
User reports approximately $5-$6 POL. Treat this as constrained future validation capital. Early work remains local, simulated, forked, shadow and paper based.

## Durable Artifacts
- PROJECT_MEMORY.md
- PROJECT_STATUS.md
- SYSTEM_BLUEPRINT.md
- AGENT_ROLES.md
- STRATEGY_CATALOG.md
- DYNAMIC_ENGINE_SPEC.md
- ZERO_COST_ARCHITECTURE.md
- CONCEPTUAL_MASTER_PLAN.md
- MATHEMATICAL_ENGINE_SPEC.md
- STRATEGY_SEARCH_SPACE.md
- PROFITABILITY_EXECUTION_INVARIANTS.md

## Continuity Protocol
For every project-driving turn:
1. verify repository state
2. read status/memory
3. choose the justified next step
4. execute permitted work
5. validate
6. update relevant specs
7. update status
8. update memory when durable decisions change
9. commit
10. report exact evidence

## Last Memory Sync
2026-09-19 | Asia/Kolkata
Reason: conceptual master foundation completed and P1 data-plane implementation identified as the next execution step.
