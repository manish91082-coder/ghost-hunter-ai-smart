# PROJECT MEMORY

## Project Identity
- Repository: `manish91082-coder/ghost-hunter-ai-smart`
- Visibility: PUBLIC
- Default branch: `main`
- Repository ID: `1376339960`
- Project working name: Ghost Hunter AI Smart
- New project focus: Polygon PoS dynamic flash-loan arbitrage intelligence and controlled execution.
- Legacy repositories are isolated and must not be modified.

## Governing Objective
Build a production-grade, evidence-driven, AI-assisted but deterministic-verifier-controlled system that continuously discovers Polygon PoS liquidity venues, pools, pairs, routes and flash-loan arbitrage opportunities.

Economic eligibility gate:
**Expected verified net profit must be strictly greater than USD 0.20 after all modeled execution costs.**

The $0.20 threshold is an execution eligibility policy, not a guarantee that every submitted transaction will realize profit.

## Absolute Project Rules
1. All market-dependent values must be dynamic.
2. No static pair/pool list is authoritative.
3. Discover and reconcile pools continuously from on-chain events/state plus trusted indexers/APIs.
4. AI proposes; deterministic mathematics verifies; security policy authorizes; executor submits; independent reconciliation proves realized PnL.
5. Never submit a candidate whose exact simulation fails.
6. Never submit when required cost or state information is unknown.
7. Never bypass the safety gate to force a trade.
8. Never modify legacy repositories.
9. Every project-driving response must update durable project state in GitHub.
10. Every future AI agent must read PROJECT_STATUS.md and PROJECT_MEMORY.md before acting.
11. The command `next` means inspect -> decide -> execute permitted next step -> validate -> persist state -> report.
12. Historical chat claims never override current verified repository state.

## Profit Policy
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

The calculation must be amount-specific and state-specific. Percentage spread alone is insufficient.

## Zero-Gas-Loss Policy
A reverted blockchain transaction can still consume gas, so literal post-submission zero gas loss cannot be mathematically guaranteed.

The engineering target is:
- no submission without simulation
- exact state-aware preflight
- private transaction submission where supported
- atomic execution
- hard gas ceiling
- native-balance floor
- strict profitability invariant
- automatic rejection under uncertainty
- independent receipt and wallet-delta reconciliation

## Dynamic Market Rule
Dynamic inputs include:
- block/state
- gas
- pool reserves/liquidity/ticks/weights
- fee tiers
- token behavior
- flash-loan availability and fee
- route costs
- RPC/WSS latency
- private submission health
- wallet balance
- competition/market conditions

Adaptive Control (AC) may tune search and execution parameters within hard safety bounds, but cannot weaken the $0.20 gate, simulation requirement, security requirements, capital limits, or kill switch.

## Polygon Research Baseline
Current research indicates:
- Aave V3 is deployed on Polygon and exposes permissionless protocol interaction; flash-loan availability must be checked dynamically per reserve and current configuration. citeturn0search2turn0search6
- QuickSwap publishes Polygon V2/V3 deployment addresses and its V3 factory emits pool-creation events, supporting event-driven pool discovery. citeturn1search13turn1search14
- Balancer documents Polygon deployment contracts and exposes chain-specific pool APIs, including all-pools retrieval for chain 137. citeturn3search4turn3search9
- Uniswap's developer documentation exposes V3 subgraph entities including factory pool counts and pool state fields, but production truth should still be reconciled with on-chain state. citeturn3search7turn3search8
- Current third-party Polygon pool snapshots show substantial fragmentation across Uniswap V4/V3/V2, QuickSwap V2/V3, Balancer, SushiSwap, Curve, KyberSwap and other venues. These counts are snapshots, not permanent truth. citeturn3search14
- Polygon Private Mempool is documented by Polygon as a private transaction submission endpoint intended to protect transactions from frontrunning and sandwich attacks. It must be operationally verified before production use. citeturn1search0turn1search3
- Polygon documentation/material indicates fast block production/finality; the engine must measure actual inter-block timing rather than hard-code a two-second assumption. citeturn2search8

## Strategy Families Frozen for Initial Research
- Cross-DEX two-leg arbitrage
- V2/V3 and V3/V3 arbitrage
- Concentrated-liquidity fee-tier arbitrage
- Triangular arbitrage
- Multi-hop cross-venue arbitrage
- Stablecoin arbitrage
- Curve stable/FX routes
- Balancer weighted/composable routes
- State-change/backrun candidates subject to security policy
- ML/AI candidate ranking, never replacing deterministic verification

## Agentic Roles
The architecture defines specialized roles in `AGENT_ROLES.md`, including:
Master Orchestrator, Polygon Chain Scout, Venue Discovery, Token Intelligence, Pool State, Route Graph, Strategy Generator, Exact Math, Economic Auditor, Simulation, Adversarial Security, MEV/Private Orderflow, Execution Guardian, Wallet/Capital Guardian, Receipt/PnL Auditor, Adaptive Control, Research Scientist, Evidence/Provenance, Regression, and Incident Response.

## Repository Artifacts
- PROJECT_MEMORY.md
- PROJECT_STATUS.md
- SYSTEM_BLUEPRINT.md
- AGENT_ROLES.md
- STRATEGY_CATALOG.md
- DYNAMIC_ENGINE_SPEC.md

## Continuity Protocol
For every project-driving turn:
1. Verify GitHub state.
2. Read status and memory.
3. Execute only the justified next step.
4. Validate with evidence.
5. Update status.
6. Update memory when a durable rule/decision/context changes.
7. Update relevant project specification files.
8. Commit with a descriptive message.
9. Report exact changed files/commits and evidence.

## Wallet Constraint
User reports approximately $5–$6 of Polygon-native balance. This is a constrained execution budget. It must not be treated as sufficient justification for live trading. Early phases remain discovery, simulation, shadow and controlled validation until evidence supports progression.

## Historical Lessons Inherited
Earlier Ghost Hunter work established that the following are production blockers unless independently proven:
- synthetic/unproven V3 triangle opportunities
- incomplete or unsafe executor paths
- modeled PnL being mistaken for realized PnL
- weak slippage/router/callback controls
- unproven tuner causality
These are audit requirements for the new project, not assumptions of correctness.

## Last Memory Sync
- Date: 2026-09-19
- Timezone: Asia/Kolkata (IST)
- Reason: Polygon project scope, dynamic rule, agent architecture, strategy families, economic gate and current research baseline initialized.
