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


## Verification Doctrine (2026-09-19)
- Every implementation step is subject to repeated audit/test passes before promotion.
- Target: 100 independent checks/passes where practical, using different verification dimensions rather than blindly repeating one identical test.
- Required dimensions: static code inspection, invariants, unit/regression tests, failure-path tests, integration checks, state/reorg checks, security/economic review and post-change re-audit.
- A discovered defect blocks promotion until corrected and re-verified.
- No live execution is allowed to bypass this gate.
- Goal alignment is mandatory: every step must have a direct, documented contribution to the final autonomous Polygon arbitrage objective.


## 2026-09-19 RPC/WSS Hardening Sync
- Fixed RPC provider ordering side effects.
- Added freshest-head reference comparison and retained quarantine for repeated lag.
- Redacted URL query strings in registry snapshots.
- Required actual WSS subscription confirmation for health.
- Removed per-message processing time from WSS latency scoring.
- Latest hardening CI was still in progress at sync time; no success claim made.


## 2026-09-19 Verified Venue Manifest Sync
- Added src/ghost_hunter/data_plane/protocols.py.
- QuickSwap Polygon V2 factory: 0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32.
- QuickSwap Polygon Algebra V3 factory: 0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28.
- These are deployment anchors sourced from official QuickSwap documentation, not static pool lists.
- Next gate: runtime eth_getCode/interface validation, event-topic verification and pool-creation discovery before an adapter becomes authoritative.


## 2026-09-19 Runtime Deployment Verification Sync
- Added `src/ghost_hunter/data_plane/deployment_verifier.py`.
- Deployment activation now requires chain ID 137, non-empty `eth_getCode`, and documented read-only interface probes.
- V2 requires `owner()` and `allPairsLength()`; Algebra V3 requires `owner()` after runtime code validation.
- Failure is fail-closed: wrong chain, empty code or interface failure returns unverified evidence.
- Corrected the Algebra V3 factory event signature to `Pool(address,address,address)` based on official QuickSwap documentation.
- Topic0 activation remains blocked until canonical Ethereum Keccak-256 verification is available. No guessed hash was inserted.


## 2026-09-19 Canonical Event Topic Sync
- Activated QuickSwap V2 `PairCreated(address,address,address,uint256)` topic0: `0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9`.
- Activated QuickSwap Algebra `Pool(address,address,address)` topic0: `0x91ccaa7a278130b65168c3a0c8d3bcae84cf5e43704342bd3ec0b59e59c036db`.
- Topic values were corroborated from actual Polygon factory transaction logs, while official QuickSwap documentation confirms the event signatures and deployment addresses.
- Added `pool_events.py` with fail-closed ABI-word decoders for both events.
- Static pool inventories remain forbidden; only factory-emitted runtime discoveries may create pool candidates.


## 2026-09-19 QuickSwap Scanner Adapter Sync
- Added `quickswap.py` as a fail-closed runtime discovery adapter for verified Polygon QuickSwap V2 and Algebra V3 deployments.
- Factory emitter and event topic0 are checked before a pool-created log can become a candidate.
- Direct pool verification requires runtime bytecode and factory/token0/token1 consistency. V2 reads reserves; Algebra reads the documented pool global-state boundary.
- Added factory reconciliation calls for V2 `getPair` and Algebra `poolByPair`.
- Added scanner integration and regression tests for wrong emitter/topic, zero pool and factory mismatch.
- No static pool inventory and no live transaction execution were introduced.


## 2026-09-19 Token Metadata Normalization Sync
- QuickSwap token discovery now normalizes standard ABI-encoded `name()` and `symbol()` strings instead of storing raw ABI payloads.
- `decimals()` remains mandatory for math readiness and is bounded to uint8-compatible values.
- Runtime token bytecode is hashed for identity/change detection.
- Non-standard optional metadata is fail-soft; missing material state still blocks downstream math.
- Added regression coverage for dynamic ABI string decoding.


## 2026-09-19 Reconciliation + Replay Integrity Sync
- Added stable QuickSwap discovery candidate keys.
- Added cache-based idempotence gate so replayed pool-creation events do not blindly create duplicate normalized records.
- Added fail-closed factory reconciliation: event-derived pool address must equal the factory's direct pair lookup result.
- Added regression tests for agreement, disagreement and duplicate replay.
- Persistent block-hash/evidence records and multi-provider reconciliation remain future gates.


## 2026-09-19 Durable Discovery Evidence + Reorg Sync
- Added a zero-cost SQLite-backed `DiscoveryStore` for durable pool-discovery/evidence records.
- Canonical discoveries are anchored to block number + block hash; missing or mismatched anchors fail closed.
- Replay is idempotent by candidate key and payload-hash integrity is enforced.
- Reorg handling marks discoveries at/after a replaced block height as orphaned and allows replacement-chain replay after the new block is recorded.
- Added restart, replay, payload-integrity and block-hash replacement regression tests.
- Next: wire the store into the discovery orchestrator and strengthen provider-diverse canonical reconciliation.


## 2026-09-19 Canonical Ancestry Coordinator Sync
- Reorg detection now preserves the last canonical head on discontinuity instead of silently replacing it.
- Added `CanonicalCoordinator` to rewind durable evidence at the fork range and request an overlap rescan before replacement-chain replay.
- Added regression tests for fork handling and same-head idempotence.
- Next: integrate canonical coordination into the head/discovery orchestrator and add provider-diverse reconciliation.


## 2026-09-19 Provider-Diverse Canonical Coordination Sync
- Critical quorum reads now require distinct provider families, preventing two endpoints from the same infrastructure family from masquerading as independent consensus.
- Provider family is explicit when configured, otherwise derived from endpoint hostname.
- Canonical coordinator and durable discovery store are now constructed by the data-plane orchestrator and invoked for each observed head.
- Existing head-handler API was preserved after verification to avoid an integration regression.
- Next: persist protocol discovery records directly from verified event processing and require diverse quorum for execution-critical pool/token reads.


## 2026-09-19 Persistent Protocol Discovery Sync
- QuickSwap candidates now retain block hash/log index evidence where present.
- Verified candidates can be persisted through the durable SQLite store, with canonical block anchoring and idempotent replay.
- Critical factory reconciliation is routed through provider-diverse quorum in the production MultiRPC implementation; lack of diversity fails closed.
- DataPlane accepts a configurable SQLite store path for restart persistence.
- Next: integrate persistence into the actual adaptive event-processing path and expand verified venue adapters only after deployment/ABI/runtime evidence gates.


## 2026-09-19 — CI Forensic Recovery
- Live Actions history was verified for `main`; recent red `data-plane-ci` runs were genuine pytest failures.
- CI now persists a JUnit pytest artifact on every run, including failures, enabling evidence-driven forensic debugging.
- Restored the accidentally truncated QuickSwap adapter regression suite, aligned the reorg test with the current `rescan_start()` API, canonicalized persisted pool addresses, and corrected replay payload error semantics.
- Corrected the Algebra event registry key to the verified ABI event name `Pool`.
- QuickSwap factory `getPair/poolByPair` reconciliation now uses provider-diverse quorum in production.
- Final green evidence: run #87, commit `c6fe593cb79f00a732e2b6869f19c39bfb21d3c9`, **44 pytest tests passed, 0 failed, 0 errors, 0 skipped**.
- Next execution gate is end-to-end adaptive event processing with exact-block provider-diverse pool/token reads and durable evidence persistence.


## 2026-09-19 — 🔒 GitHub State Verification Gate LOCKED
- The project now has a permanent non-negotiable rule: **every repository change must be followed by live GitHub state verification before the next implementation step begins**.
- Verification must target the exact promoted `main` commit SHA and its corresponding GitHub Actions run.
- Queued/in-progress is not verified. Any non-success terminal result blocks progression until repaired and revalidated.
- Screenshots, previous green runs, commit existence, or local reasoning cannot substitute for current-commit GitHub verification.
- Canonical rule file: `GITHUB_STATE_VERIFICATION_GATE.md`.
- Gate lock itself was validated: run #90 for the rule-file commit completed successfully; run #91 for the status-file commit also completed successfully.


## 2026-09-19 — End-to-End QuickSwap Canonical Promotion Gate
- Implemented canonical single-block QuickSwap promotion: scan -> decode -> quorum reconciliation -> exact-block pool/token state -> durable evidence -> cache promotion.
- Cache promotion is delayed until persistence succeeds.
- Execution-critical pool/token reads use provider-diverse quorum.
- Adapter retains rejection reasons for forensic inspection.
- CI caught an ABI fixture defect during the gate; it was corrected and the repaired commit passed.
- Verified implementation baseline: `a97dce1f907c6bac7b043931763392c8114bf745`, Actions run #99 **SUCCESS**.
- Status documentation commit `92a12a45c7df8c4be70d86b5c271d75596a63c73` was independently verified by Actions run #100 **SUCCESS**.
- Next gate: connect canonical QuickSwap processing to head/reorg orchestration with explicit replay context and end-to-end restart/reorg replay tests.


## 2026-09-19 — Head/Reorg Context Integration
- HeadContext and DataPlane.run_heads_context() now propagate canonical/replay decisions explicitly while preserving the legacy run_heads handler API.
- Regression commit faf1bdcdf49a3abc31021162d6ed7993a3a7f2b0 passed Actions run #103.
- Status update commit 2221d698e8cdc762da9b4b90fed27e8870536a40 passed Actions run #104.
- Next gate: durable restart/reorg replay execution and canonical-state reconstruction from SQLite before discovery promotion.


## 2026-09-19 Automatic Verification Infrastructure Sync
- Added exact-state GitHub Actions verification after `data-plane-ci` completion, with machine-readable `repo-state.json` and fail-closed gates.
- Added `TASK_REGISTRY.json` and `GH-TASK-NNNN` task identity.
- This infrastructure enforces the frozen verification gate and is not live-execution authorization.


## 2026-09-19 Ground-Truth State Inspector Sync
- Upgraded the GitHub verifier into a repository-wide state inspector covering exact SHA, Actions, jobs, artifacts, check-runs, statuses, PRs, issues and recent workflow health.
- Added hourly scheduled inspection and manual dispatch while retaining exact post-CI workflow verification.
- Task identity is derived from the immutable `GH-TASK-NNNN` commit-message token, avoiding recursive status commits.
- The inspector is read-only and fail-closed and is now the machine ground-truth layer for deciding whether the next implementation step may begin.


## 2026-09-19 Verifier Static Audit Correction
- Post-commit static inspection caught a Python f-string quoting defect in the repository-wide inspector. The defect is being corrected before any GREEN claim.


## 2026-09-19 Verifier Self-Check Isolation
- Hardened the repository inspector so its own in-progress check cannot create a false failure while the inspector is running. Underlying CI/checks remain mandatory.


## 2026-09-19 Verifier Failure Forensics
- Screenshot evidence showed data-plane CI #110 green but repo-state-verifier #4 red for GH-TASK-0003.
- Hardened self-check exclusion by verifier run ID and exact-SHA checkout for workflow-run verification.
- No GREEN promotion occurs until corrected verifier is terminal-success.
