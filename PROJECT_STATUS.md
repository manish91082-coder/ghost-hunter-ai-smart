# PROJECT STATUS

## STATUS

### Verification Doctrine
**ZERO-DRIFT / MULTI-PASS VERIFICATION IS FROZEN.** Every implementation step must be audited repeatedly before being treated as complete. The target is 100 independent checks/passes where practical; this means repeated static inspection, invariant review, regression tests, failure-path tests, integration checks and re-audit, not a claim that one identical test was blindly executed 100 times. No step is promoted to execution merely because it passes once. Any discovered defect sends the step back to correction and re-verification.

**PHASE 0 + P0.5 COMPLETE; P1 DATA-PLANE HARDENING ACTIVE; QUICKSWAP DISCOVERY + DURABLE EVIDENCE + PROVIDER-DIVERSE RECONCILIATION ACTIVE**

## Repository
- `manish91082-coder/ghost-hunter-ai-smart`
- PUBLIC
- Default branch: `main`
- Repository ID: `1376339960`
- Legacy repositories: MUST NOT BE MODIFIED

## Zero-Cost Constraint
**ZERO-COST-FIRST IS FROZEN.** No paid service is a mandatory dependency. Local/open-source/free-tier resources are the development and shadow-mode baseline.

## RPC Fleet Rule
**AUTONOMOUS MULTI-RPC FLEET IS NOW FROZEN.** Keep many RPC/WSS endpoints in a persistent registry; never auto-delete an endpoint merely for failure/block/rate-limit/latency. Dynamically rotate, cooldown, quarantine, probe and restore endpoints without routine manual switching. Critical reads require provider-diverse reconciliation. See `RPC_FLEET_POLICY.md`.

## Current Goal
Build a dynamic Polygon PoS flash-loan arbitrage system that:
- discovers liquidity dynamically
- explores broad strategy permutations/combinations
- calculates exact amount-dependent economics
- reacts immediately to new state
- uses parallel/batched computation
- proves candidates before submission
- enforces expected verified net profit > $0.20
- independently proves realized PnL

## Completed
### Conceptual foundation
- [x] Master system concept
- [x] Mathematical engine specification
- [x] Strategy search-space/permutation model
- [x] Profitability and execution invariants
- [x] Zero-cost architecture

### P1 data-plane skeleton
- [x] Async multi-RPC provider abstraction
- [x] RPC health/failover and cooldown
- [x] Autonomous capability-aware RPC selection
- [x] Rate-limit-aware cooldown
- [x] Endpoint retention with no automatic deletion
- [x] Concurrent fleet health probes and automatic recovery
- [x] RPC fleet scoring by latency/failure/staleness
- [x] Reference-head block-lag detection with quarantine threshold
- [x] Secret-redacted fleet registry snapshot
- [x] Autonomous multi-RPC fleet governance policy frozen
- [x] Batch JSON-RPC support
- [x] Multi-provider quorum read primitive
- [x] Polygon chain-id validation
- [x] Dynamic block-head polling
- [x] Low-latency WSS new-head stream
- [x] Normalized block/token/pool/evidence models
- [x] Local state cache
- [x] Affected-pool lookup
- [x] Venue adapter boundary
- [x] Async parallel-read entry point
- [x] Zero-cost GitHub CI test workflow
- [x] src-layout package/build configuration
- [x] Adaptive event-log scanner
- [x] Verified event-topic registry boundary
- [x] Reorg/canonical-head guard
- [x] Discovery runtime design and tests
- [x] Source-verified QuickSwap Polygon V2 + Algebra V3 deployment manifest
- [x] Deployment manifest regression tests
- [x] Runtime deployment verifier with chain/code/interface hard gates
- [x] QuickSwap Algebra event signature corrected to documented `Pool(address,address,address)`
- [x] Canonical Keccak topic0 activation
- [x] Durable SQLite discovery/evidence store
- [x] Canonical block-hash anchoring for discoveries
- [x] Idempotent replay with payload-hash integrity
- [x] Reorg rollback/orphan marking and replacement-chain replay
- [x] Canonical ancestry coordinator with overlap-rescan trigger
- [x] Provider-diverse quorum selection for critical reads
- [x] Durable store wired into head orchestration
- [x] QuickSwap discovery persistence with block/log evidence
- [x] Critical QuickSwap factory reconciliation requires provider-diverse quorum
- [x] Configurable durable store path for process restart persistence

## Important Design Correction
WSS/polling is an acceleration path, not canonical truth. A new-head event must trigger immediate downstream work, while execution-critical state is re-read/reconciled before authorization.

The system must target low-latency reaction and parallelism, but must not promise a fixed sub-second execution time because provider latency, chain state and network conditions are dynamic.

## P1 Runtime Architecture
**NEW HEAD -> FAST INVALIDATION -> ADAPTIVE LOG SCAN -> POOL DISCOVERY -> TOKEN DISCOVERY -> STATE READ -> AFFECTED POOLS -> AFFECTED ROUTES -> CHEAP PREFILTER -> EXACT QUOTES**

Discovery primitives are now implemented. The next step is activating only protocol adapters whose deployment addresses and event ABIs are verified from canonical sources.

## Current Files Added/Changed
- `pyproject.toml`
- `.env.example`
- `src/ghost_hunter/__init__.py`
- `src/ghost_hunter/data_plane/__init__.py`
- `src/ghost_hunter/data_plane/models.py`
- `src/ghost_hunter/data_plane/rpc.py`
- `src/ghost_hunter/data_plane/chain.py`
- `src/ghost_hunter/data_plane/cache.py`
- `src/ghost_hunter/data_plane/discovery.py`
- `src/ghost_hunter/data_plane/orchestrator.py`
- `src/ghost_hunter/data_plane/wss.py`
- `tests/test_data_plane.py`
- `.github/workflows/data-plane-ci.yml`
- `README.md`
- `src/ghost_hunter/data_plane/events.py`
- `src/ghost_hunter/data_plane/scanner.py`
- `src/ghost_hunter/data_plane/reorg.py`
- `tests/test_discovery_runtime.py`
- `P1_DISCOVERY_RUNTIME_DESIGN.md`

## Safety
Live execution remains disabled in this phase. No transaction signer/executor has been introduced.

## Phase Plan
### P0 — Governance/Foundation
**COMPLETE**

### P0.5 — Conceptual Master Foundation
**COMPLETE**

### P1 — Polygon Data Plane
**IN PROGRESS**
Completed this step:
- autonomous many-RPC fleet manager upgrade
- reference-head lag classification and retained quarantine
- secret-redacted fleet registry snapshot
- adaptive log scanner
- verified event-topic boundary
- reorg guard
- discovery runtime design

Next:
- real venue/factory adapters
- event topic registry
- log scanner with adaptive ranges
- pool creation discovery
- token metadata/code-hash discovery
- pool state readers
- reorg handling
- persistent local store
- discovery reconciliation

### P2 — Exact Economics
- V2 math
- V3/Algebra math
- StableSwap
- Balancer/weighted math
- fee/gas/flash-loan engine
- amount optimization
- robustness analysis

### P3 — Strategy Engine
- route graph
- cycle enumeration
- permutation/combination search
- candidate deduplication
- amount/split optimization
- adaptive search

### P4 — Simulation/Security
- fork/eth_call/trace
- adversarial checks
- executor invariants

### P5 — Execution
- atomic executor
- private submission
- nonce manager
- wallet guardian
- kill switch

### P6 — Shadow/Paper
### P7 — Controlled Live
### P8+ — Autonomous Optimization

## 2026-09-19 — Verified Venue Deployment Manifest
- Researched official QuickSwap Polygon deployment documentation.
- Added source-verified deployment anchors for QuickSwap V2 factory and Polygon Algebra V3 factory.
- Kept pool discovery dynamic: no static pair/pool inventory was introduced.
- Added regression tests for chain ID, source verification and distinct factory identities.
- Important: deployment address verification is not the same as runtime contract-code/interface verification; that remains the next adapter gate.

## Project Log
### 2026-09-19 — Autonomous RPC Fleet Policy
- Frozen many-RPC/many-WSS architecture with automatic rotation and provider-diverse quorum.
- RPCs are retained when unhealthy; runtime uses cooldown/quarantine/probation and automatic recovery probes instead of deletion.
- Routine provider switching is explicitly no-manual-work.
- Next: persistent RPC/WSS fleet metrics and registry, then verified protocol adapters and deployment discovery, with multi-pass verification at each gate.

### 2026-09-19 — RPC/WSS Hardening Pass
- Removed score-order round-robin side effects; provider ordering is deterministic and score-driven.
- Health probes now compare successful provider heads against the freshest observed head and classify configurable lag.
- Registry snapshots redact URL query strings to avoid exposing query-based API keys.
- WSS probes now require JSON-RPC subscription confirmation.
- WSS head messages no longer distort network-latency EWMA.
- Hardening CI was triggered; latest relevant run remains in progress, so success is not yet claimed.

### 2026-09-19 — Verification Doctrine + RPC/WSS Audit
- User requirement locked: every project step must be repeatedly checked, tested and audited before promotion, with a target of 100 independent verification passes where practical.
- Verification includes static review, invariants, unit/regression tests, failure-path testing, integration checks and post-change re-audit.
- During this audit a duplicate `probe_all` implementation in WSS was detected and removed before treating the WSS step as complete.
- No live execution is enabled; passing tests never override safety/economic gates.

### 2026-09-19 — Autonomous RPC Fleet Runtime Upgrade
- Upgraded `MultiRPC` into an autonomous fleet manager with capability-aware routing and health scoring.
- Added rate-limit-aware cooldown, endpoint retention, concurrent recovery probes and automatic restoration.
- Failed/slow/rate-limited endpoints remain registered and are never automatically deleted.
- Added fleet registry snapshots for future persistent metrics/state storage.
- Added regression tests locking the no-delete rule.

### 2026-09-19 — P1 Discovery Runtime
- Added adaptive log scanning with range shrink/expand.
- Added verified event-topic registry boundary so guessed topics cannot become execution truth.
- Added canonical-head/reorg guard and overlap-rescan policy.
- Added discovery runtime design and tests.

### 2026-09-19 — P1 Data-Plane Skeleton
- Implemented async multi-provider RPC with batching and failover.
- Added quorum read primitive for critical consistency checks.
- Added dynamic block polling and WSS new-head acceleration.
- Added normalized state models, cache and venue discovery boundary.
- Added CI and package configuration.
- Corrected block interval observation so prior block state is retained.
- Kept live execution out of the data plane.

### 2026-09-19 — Conceptual Master Foundation
- Frozen the dynamic market graph, exact math, search-space and execution-invariant architecture.

## Last Updated
2026-09-19 | Asia/Kolkata (IST)


## 2026-09-19 — Runtime Deployment Verification Gate
- Added `deployment_verifier.py` for runtime verification of manifest deployment anchors.
- Verification now requires Polygon chain ID 137, non-empty runtime bytecode and successful documented read-only factory interface probes.
- QuickSwap V2 additionally requires `allPairsLength()`; Algebra V3 currently requires the common documented `owner()` probe plus runtime code.
- Verification evidence is fail-closed. Wrong chain, empty code or interface failure cannot activate a deployment.
- Corrected the Algebra V3 event signature in `events.py` from an incorrect placeholder to the documented `Pool(address,address,address)`.
- Canonical topic0 values are still intentionally not activated. The event registry remains fail-closed until a canonical Keccak-256 topic is independently verified.
- Web research confirmed QuickSwap's Polygon V2 factory and Algebra V3 factory addresses and the Algebra `Pool` event/read-only factory interface. 
- Local/CI regression validation is the next promotion gate; no live execution is enabled.


## 2026-09-19 — Canonical QuickSwap Event Topic + Decoder Gate
- Canonical QuickSwap Polygon V2 `PairCreated` topic0 was independently corroborated from PolygonScan factory logs: `0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9`.
- Canonical QuickSwap Polygon Algebra `Pool` topic0 was independently corroborated from PolygonScan factory logs: `0x91ccaa7a278130b65168c3a0c8d3bcae84cf5e43704342bd3ec0b59e59c036db`.
- Activated only these two verified topics in the event registry.
- Added fail-closed decoders for QuickSwap V2 `PairCreated` and Algebra `Pool`.
- Decoder tests cover exact topic length, indexed-address decoding, pool address decoding, V2 creation index and malformed-log rejection.
- Pool discovery remains runtime-driven. No static pool inventory was introduced.
- Next gate: wire the verified topics/decoders into the adaptive log scanner and add canonical-emitter filtering plus direct pool/token state reads.


## 2026-09-19 — QuickSwap Scanner + Runtime Pool Verification Gate
- Added `quickswap.py` as a fail-closed runtime adapter for the verified Polygon QuickSwap V2 and Algebra V3 factory deployments.
- Scanner integration now decodes only logs whose emitter and topic0 match the verified deployment/event pair; malformed or mismatched logs are discarded rather than promoted.
- Direct pool validation requires runtime code plus factory/token0/token1 consistency. V2 additionally reads reserves; Algebra reads the pool global-state ABI boundary.
- Added reconciliation hooks for V2 `getPair` and Algebra `poolByPair` using runtime factory calls.
- Added scanner/adapter regression tests for wrong emitter/topic, zero pool, factory mismatch and successful V2 state normalization.
- No live execution was enabled. The adapter is discovery/state infrastructure only.
- Next gate: strengthen ABI decoding and token metadata/code-hash normalization, add replay/idempotence and reconciliation tests, then persist discovery state.


## 2026-09-19 — Token Metadata Normalization Gate
- Hardened QuickSwap token discovery to require runtime bytecode and a valid uint256-compatible `decimals()` response.
- Added ABI string decoding for standard dynamic `name()`/`symbol()` responses with fail-soft handling for non-standard tokens.
- Token code is hashed into the normalized token state for identity/change detection.
- Added regression coverage for ABI string decoding and malformed empty responses.
- This remains discovery/state infrastructure; no transaction execution path was introduced.
- Next gate: make discovery replay/idempotence explicit and reconcile event-derived pools against factory `getPair`/`poolByPair` results before persistent storage.


## 2026-09-19 — Reconciliation + Replay Integrity Gate
- Added stable discovery candidate keys and cache-based idempotence checks.
- Added a fail-closed `reconcile_candidate()` gate requiring the factory's direct pair lookup to match the event-derived pool address.
- Added regression coverage for both matching and mismatching factory reconciliation and duplicate replay detection.
- This prevents an event-only pool candidate from becoming normalized state without independent factory agreement.
- Next gate: wire persisted discovery records into protocol event processing and require provider-diverse reconciliation for pool/token execution-critical reads.


## 2026-09-19 — Durable Discovery Evidence + Reorg Gate
- Added `src/ghost_hunter/data_plane/store.py` using Python standard-library SQLite, preserving the zero-cost-first constraint.
- Discovery records now require a canonical block number + block hash anchor before persistence; unanchored evidence is rejected.
- Candidate keys provide durable idempotence across process restarts. A replay with a changed payload hash fails closed.
- Block-hash replacement at a fork point automatically orphans discoveries at/after that height; replacement-chain discoveries can then be replayed against the new canonical block hash.
- Added tests for missing block hash, restart persistence, duplicate replay, payload mutation, explicit rewind, replacement block hash and orphan status.
- No transaction signer, private key, or live execution path was added.


## 2026-09-19 — Canonical Ancestry Coordinator Gate
- Hardened `ReorgGuard` so discontinuous/forked heads do not overwrite the last known canonical head.
- Added `CanonicalCoordinator` to couple ancestry validation with durable SQLite evidence and trigger overlap replay after a discontinuity.
- Added regression tests for non-advancing fork detection, durable rewind/replay and same-head idempotence.
- No live execution path was introduced.


## 2026-09-19 — Provider-Diverse Canonical Coordination Gate
- Hardened `MultiRPC.quorum_call()` to select distinct provider families rather than multiple endpoints from one provider family.
- Quorum now fails closed when the requested number of distinct provider families is unavailable or when fewer than quorum successful results agree.
- Added `provider_family` metadata with hostname fallback, preserving autonomous endpoint retention/rotation.
- Wired `CanonicalCoordinator` + durable `DiscoveryStore` into `DataPlane.run_heads()`; existing head-handler signature is preserved.
- Added regression tests for provider-family diversity and insufficient diversity.
- No live execution path was introduced.


## 2026-09-19 — Persistent Protocol Discovery Gate
- Extended QuickSwap discovery candidates with block hash and log index evidence when supplied by canonical RPC logs.
- Added `persist_candidate()` to persist verified candidates through the SQLite evidence store; missing block hash is rejected.
- QuickSwap factory `getPair`/`poolByPair` reconciliation now requires the provider-diverse quorum primitive in production `MultiRPC`.
- DataPlane store path is configurable so deployments can use a persistent SQLite file instead of the in-memory default.
- Added regression coverage for durable QuickSwap candidate persistence and idempotent replay.
- No transaction signer or live execution was introduced.


## 2026-09-19 — CI Failure Forensics + Regression Recovery Gate
- Screenshot review was cross-checked against the live GitHub Actions history for `main`; the visible red runs were genuine `data-plane-ci` failures, not a UI-only artifact.
- Forensic JUnit reporting was added to CI so failed pytest runs retain machine-readable evidence as a workflow artifact.
- The investigation found four concrete regressions:
  1. `tests/test_quickswap_adapter.py` had been accidentally truncated/corrupted to `[object Object]`; the complete regression suite was restored.
  2. `test_discovery_runtime.py` called the obsolete two-argument `rescan_start()`; the test was aligned to the current one-argument API.
  3. Discovery persistence canonicalizes pool addresses to lowercase; `DiscoveryRecord` now canonicalizes the dataclass value as well, preserving deterministic equality across restart.
  4. Replay payload errors now distinguish existing-record payload mutation from initial record hash mismatch; the fail-closed semantics remain intact.
- The Algebra event registry name was corrected from `PoolCreated` to the ABI event name `Pool`, matching the verified `Pool(address,address,address)` event.
- QuickSwap factory reconciliation was hardened to use provider-diverse quorum reads in production.
- Final verification evidence: GitHub Actions `data-plane-ci` run **#87** on commit `c6fe593cb79f00a732e2b6869f19c39bfb21d3c9` completed **SUCCESS**; pytest reported **44 tests, 0 failures, 0 errors, 0 skipped**.
- Live execution remains disabled.
- Next gate: integrate scanner -> canonical coordinator -> verified QuickSwap adapter -> quorum reconciliation -> exact-block pool/token state reads -> durable evidence persistence -> cache as one end-to-end adaptive event-processing path, then re-audit reorg/replay behavior.


## 2026-09-19 — 🔒 GitHub State Verification Gate LOCKED
- **NON-NEGOTIABLE RULE:** after every repository change, verify the live GitHub state before starting the next project step.
- Required sequence: `CHANGE -> PUSH -> GITHUB STATE CHECK -> CI TERMINAL RESULT -> FAILURE FORENSICS IF NEEDED -> GREEN GATE -> NEXT CHANGE`.
- Verification must use the exact promoted commit SHA and its corresponding GitHub Actions run/check.
- `queued` / `in_progress` means **NOT VERIFIED** and blocks progression.
- Any non-success terminal result blocks progression until diagnosed, repaired, and revalidated.
- Screenshots, previous green runs, commit existence, or local reasoning are never substitutes for the current-commit GitHub verification.
- Canonical rule file: `GITHUB_STATE_VERIFICATION_GATE.md`.
- Current gate status at time of lock: commit `49c3b41d491a87aaa4258ec10729ea92a5eb9f76`, Actions run #90 = **queued**, therefore **NOT YET VERIFIED**. No next implementation gate is to be promoted until run #90 reaches a successful terminal state.


## 2026-09-19 — End-to-End QuickSwap Canonical Promotion Gate
- Added a canonical single-block processing path: factory log scan -> fail-closed decode -> provider-diverse factory reconciliation -> exact-block pool reads -> exact-block token reads -> durable discovery evidence -> cache promotion.
- Pool/token cache promotion now occurs only after durable discovery persistence succeeds.
- Execution-critical pool/token reads use provider-diverse quorum at the candidate block.
- Discovery rejection reasons are retained in-memory for forensic inspection instead of being silently discarded by the adapter.
- Added regression coverage for the complete promotion path.
- CI forensic loop caught and corrected an ABI fixture encoding defect; no defect was promoted without a successful revalidation.
- Final verified baseline for this gate: commit `a97dce1f907c6bac7b043931763392c8114bf745`, GitHub Actions run #99 **SUCCESS**.
- Live execution remains disabled.
- Next gate: wire this canonical QuickSwap processing path into head/reorg orchestration with explicit replay context, then test restart/reorg replay end-to-end.


## 2026-09-19 — Head/Reorg Context Integration
- Added HeadContext and DataPlane.run_heads_context() so canonical acceptance and replay decisions are explicitly propagated to the processing layer.
- Preserved the existing run_heads(handler) API for compatibility.
- Added regression coverage proving a canonical head produces no replay request while a discontinuity propagates the coordinator's replay start.
- Verification: implementation commit 232af68fda87d360dd22be28fad3572ef8278dd1 passed Actions run #102; regression commit faf1bdcdf49a3abc31021162d6ed7993a3a7f2b0 passed Actions run #103.
- Next gate remains durable restart/reorg replay execution, including reconstructing canonical state from the SQLite store and replaying replacement blocks before promotion.


## 2026-09-19 — Automatic GitHub State Verification Gate
- Added `scripts/verify_repo_state.py` for exact tested-SHA and terminal Actions verification.
- Added `.github/workflows/repo-state-verifier.yml`, triggered after `data-plane-ci` completes on a `main` push; it fails closed and uploads `repo-state.json`.
- Added `TASK_REGISTRY.json` and the `GH-TASK-NNNN` commit-message convention for durable task identity.
- This governance infrastructure enforces the frozen GitHub verification gate and does not authorize live trading.
- `f2cd22beb720cd5ff244df8a6e3d79199114a62a` remains awaiting exact Actions verification because the connector's commit-run wrapper does not expose push-triggered runs.


## 2026-09-19 — Repository-Wide Ground-Truth Inspector
- Upgraded `scripts/verify_repo_state.py` from a single-run checker into a repository-wide read-only state inspector.
- It now reconciles main SHA, exact task identity, matching data-plane CI run, every job, artifacts, commit check-runs, commit statuses, PRs associated with the exact commit, all open PRs, all open issues, and recent main-branch workflow health.
- Added hourly scheduled and manual inspection while retaining exact post-CI `workflow_run.completed` verification.
- The inspector is fail-closed for the project GREEN gate and never mutates GitHub state.
