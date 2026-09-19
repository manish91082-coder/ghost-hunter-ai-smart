# RPC FLEET & AUTONOMOUS ROTATION POLICY

## Status
**FROZEN PROJECT RULE**

Ghost Hunter must use a large, provider-agnostic RPC fleet. RPC endpoints are runtime infrastructure, not a manually selected primary/backup pair.

## Non-Negotiable Rules
1. No single RPC is a mandatory dependency.
2. An RPC is **not deleted automatically** because it fails, rate-limits, blocks, becomes slow, disagrees, or temporarily goes offline.
3. Failed endpoints remain in the registry and move through health states such as ACTIVE, DEGRADED, COOLDOWN, QUARANTINED and PROBATION.
4. The runtime automatically retries/probes unhealthy endpoints and may return recovered endpoints to rotation.
5. Routine RPC operation requires **no manual provider switching**.
6. Execution-critical reads use independent-provider reconciliation/quorum plus direct state validation.
7. Secrets/API keys stay in environment/local secret storage, never committed to the public repository.
8. Paid RPC is never required by the core architecture. Free/public/free-tier endpoints may be pooled subject to provider terms and quotas.
9. Provider-specific limits must be respected. Rotation is for resilience and load distribution, not quota/ban evasion.
10. WSS and HTTP fleets are independently health-scored and rotated.

## Fleet Registry
Each endpoint should maintain:
- provider_id / endpoint_id
- HTTP/WSS capability
- supported methods/capabilities
- chain-id verification
- rolling success/failure counts
- EWMA latency
- rate-limit signals
- last success/failure
- latest observed block and block lag
- disagreement count
- cooldown/quarantine state
- next health-probe time
- provider quota/weight metadata when known

## Autonomous Selection
For every request, the RPC Fleet Manager chooses eligible endpoints dynamically using:
- health
- latency
- block freshness
- recent error/rate-limit history
- method capability
- provider diversity
- current in-flight load
- temporary cooldown
- criticality of the requested read

A provider that fails is skipped for the current operation, retained in the fleet, cooled down, health-probed later and automatically restored when it proves healthy.

## Critical Read Policy
Critical state must not trust one endpoint. The engine should request independent providers in parallel and require deterministic agreement according to the operation's quorum policy. Provider disagreement creates an evidence event and blocks execution until reconciled.

## Discovery / Auto-Onboarding
The architecture should support machine-readable endpoint configuration and automatic onboarding validation:
1. load configured candidate endpoints
2. verify Polygon chain ID 137
3. test required methods
4. measure latency/freshness
5. classify capabilities
6. admit healthy endpoint to rotation
7. retain unhealthy endpoint for later probes

Discovery of arbitrary public RPCs from the internet must never silently make them trusted execution sources. New endpoints enter probation first.

## No-Manual-Work Runtime
Normal runtime must autonomously:
- select/rotate RPCs
- fail over
- cool down and retry
- health probe
- restore recovered endpoints
- rebalance load
- detect stale heads
- detect provider disagreement
- maintain evidence/metrics
- choose HTTP vs WSS path
- trigger circuit breakers

Human intervention remains only for governance-level actions such as adding credentials, changing hard safety policy, or emergency shutdown.

## Implementation Direction
Upgrade current MultiRPC into an RPC Fleet Manager with persistent endpoint identity, weighted health scoring, capability-aware routing, background probes, rate-limit-aware cooldown, block-lag detection, provider-diverse quorum, WSS fleet rotation and local metrics persistence.
