# PROJECT MEMORY

## Project Identity
- Repository: `manish91082-coder/ghost-hunter-ai-smart`
- Visibility: PUBLIC
- Default branch: `main`
- Repository ID: `1376339960`
- Project: Ghost Hunter AI Smart
- Target chain: Polygon PoS (chain ID 137)
- Legacy repositories must never be modified for this project.

## Mission
Build a self-directed, continuously recalculating Polygon flash-loan arbitrage intelligence and controlled execution system.

The system should autonomously decide what to inspect, what to discard, what to calculate next and what to simulate, within hard deterministic safety/economic policies.

Hard economic gate:
**Expected verified net profit > USD 0.20 after all known costs and required reserve.**

This threshold is not a guarantee of realized profit.

## Non-Negotiable Rules
1. Market-dependent data is dynamic.
2. Static pool/pair counts are never authoritative.
3. AI may search, rank, learn and propose, but deterministic math and security policy have final authority.
4. Exact state-aware simulation is required before live submission.
5. Unknown material cost/state means NO TRADE.
6. Reverts can consume gas; zero post-submission gas loss is not mathematically guaranteed.
7. Avoidable gas loss must be minimized through preflight, simulation, hard gas limits, wallet floors and atomic invariants.
8. Required private execution means no trade when the private path is unavailable or unverified.
9. No live execution in P1.
10. ZERO-COST-FIRST is mandatory.
11. `next` means inspect -> decide -> execute -> validate -> persist -> report.
12. Every project-driving turn updates durable GitHub state.
13. RPC/WSS infrastructure is a large autonomous fleet, not a primary/backup pair.
14. Never auto-delete an RPC merely because it fails, rate-limits, blocks, lags or becomes slow. Retain it and use health-state rotation, cooldown/quarantine, probes and automatic recovery.
15. Routine RPC selection/failover/recovery requires no manual switching.

## Self-Decision Architecture
The eventual runtime is designed as a closed control loop:

OBSERVE
-> DISCOVER
-> NORMALIZE
-> BUILD GRAPH
-> GENERATE CANDIDATES
-> PRIORITIZE
-> EXACT CALCULATE
-> OPTIMIZE AMOUNT
-> SIMULATE
-> ADVERSARIAL CHECK
-> AUTHORIZE
-> EXECUTE
-> RECONCILE
-> LEARN
-> ADAPT

No human decision is required for ordinary runtime candidate selection. Human/governance control remains the owner of hard policy, capital limits, emergency stop and deployment approval.

## Autonomous RPC Fleet
- many HTTP RPC and WSS endpoints are supported concurrently
- provider-agnostic persistent endpoint registry
- health/latency/freshness/rate-limit/capability scoring
- automatic rotation and load balancing
- cooldown/quarantine/probation rather than deletion
- automatic background recovery probes and restoration
- provider-diverse quorum for execution-critical reads
- WSS and HTTP fleets independently rotated
- new endpoints enter probation before becoming trusted execution sources
- provider terms/quotas are respected; rotation is resilience, not quota evasion
- full policy: `RPC_FLEET_POLICY.md`

## Low-Latency Architecture
Use:
- WSS new-head events
- async IO
- batch JSON-RPC
- parallel independent reads
- affected-pool/affected-route recomputation instead of global recomputation
- provider health scoring and failover
- local in-memory state cache
- persistent local state later

A WSS event is an acceleration signal. Execution-critical state is revalidated against RPC/on-chain state.

The target is low-latency reaction, not an impossible fixed sub-second guarantee.

## Discovery Runtime Added
- adaptive log scanner with bounded range expansion/shrink-on-error
- verified event-topic registry boundary
- canonical-head/reorg guard
- replayable overlap-rescan design
- protocol-neutral pool discovery adapter interface

Event topics are not activated from guesses. Canonical ABI/deployment verification is required before a venue becomes authoritative.

## Data-Plane Implementation Completed
- multi-provider async JSON-RPC
- batch calls
- quorum consistency primitive
- provider failure cooldown
- Polygon chain validation
- dynamic head polling
- WSS head subscription
- normalized BlockState/TokenState/PoolState/EvidenceRecord
- state cache
- affected pool lookup
- venue adapter interface
- CI/test scaffold

## Conceptual Search Space
Candidate dimensions include:
- flash/start asset
- token pair and direction
- venue
- pool
- pool type
- fee tier
- hop count
- route order
- cycle length
- input amount
- amount splits
- concentrated-liquidity boundaries
- gas state
- state freshness
- submission path
- historical execution profile

Search funnel:
**structural filter -> conservative upper bound -> exact quote -> amount optimization -> full economics -> simulation -> adversarial security -> authorization.**

## Strategy Families
- cross-venue two-leg
- V2/V2
- V2/V3
- V3/V2
- V3/V3
- fee-tier
- triangular
- multi-hop
- stablecoin
- concentrated-liquidity
- StableSwap
- weighted/composable
- state-change/backrun subject to policy
- router disagreement signal
- ML/statistical ranking

## Mathematical Authority
Execution-critical calculations must use integer base units and on-chain-compatible rounding.

Pool-specific math:
- V2 constant product
- V3/Algebra concentrated liquidity
- StableSwap
- weighted/composable pools

AI never replaces exact math.

## Durable Artifacts
Conceptual:
- CONCEPTUAL_MASTER_PLAN.md
- MATHEMATICAL_ENGINE_SPEC.md
- STRATEGY_SEARCH_SPACE.md
- PROFITABILITY_EXECUTION_INVARIANTS.md

Core:
- PROJECT_MEMORY.md
- PROJECT_STATUS.md
- SYSTEM_BLUEPRINT.md
- AGENT_ROLES.md
- STRATEGY_CATALOG.md
- DYNAMIC_ENGINE_SPEC.md
- ZERO_COST_ARCHITECTURE.md

P1 implementation:
- pyproject.toml
- .env.example
- src/ghost_hunter/data_plane/*
- tests/test_data_plane.py
- .github/workflows/data-plane-ci.yml

## Wallet Constraint
Approximately $5-$6 POL is treated as constrained future validation capital. It is not development funding. Early operation remains simulation/shadow/paper.

## Last Memory Sync
2026-09-19 | Asia/Kolkata
Reason: Autonomous many-RPC/many-WSS fleet policy frozen. Unhealthy endpoints are retained and automatically rotated/cooldown-probed/restored; routine provider management is no-manual-work. Next implementation upgrade adds capability-aware health scoring, block-lag/rate-limit detection, recovery probes and WSS fleet rotation before/alongside verified protocol adapters.


## 2026-09-19 RPC Fleet Implementation Sync
- `MultiRPC` is now an autonomous fleet manager rather than a simple primary/backup client.
- Endpoint state is retained across failures; cooldown, rate-limit backoff, quarantine/probation semantics and recovery probing are runtime states, not deletion.
- Requests are routed by health/latency/capability score; critical quorum reads use provider-diverse selection.
- Fleet-wide health probes run concurrently with bounded probe concurrency.
- Regression tests explicitly lock the no-automatic-delete requirement.
- Next infrastructure increment: persistent fleet metrics/registry and independent HTTP/WSS fleet rotation.
