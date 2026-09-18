# Ghost Hunter AI Smart

**Polygon PoS dynamic flash-loan arbitrage intelligence and controlled execution platform.**

## Mission

Continuously discover executable Polygon liquidity, search large strategy permutation/combination spaces, calculate exact amount-dependent economics, prove candidates by simulation, and execute only when every deterministic safety and profitability gate passes.

Hard economic gate:

**Expected verified net profit > USD 0.20 after all known costs and required reserve.**

This is an eligibility threshold, not a guarantee of realized profit.

## Architecture

DISCOVER -> NORMALIZE -> LIQUIDITY GRAPH -> SIGNALS -> ROUTE/AMOUNT SEARCH -> EXACT MATH -> FULL ECONOMICS -> SIMULATE -> SECURITY -> PROFIT GATE -> AUTHORIZE -> EXECUTE -> RECEIPT -> REALIZED PnL -> LEARN

AI proposes. Deterministic mathematics verifies. Security policy authorizes. Independent reconciliation proves realized PnL.

## Zero-Cost-First

Local compute, open-source libraries, free RPC/API tiers where available, local state storage and fork/shadow testing are the default. No paid service is a mandatory dependency.

## Current phase: P1 Data Plane

The first runtime layer provides:
- async multi-provider JSON-RPC
- batch RPC calls
- provider health/failover
- quorum reads for critical state
- Polygon chain validation
- dynamic block-head polling
- normalized token/pool models
- local state cache
- venue adapter boundary

The data plane is designed for low-latency parallel reads and event-driven downstream recalculation. It does not enable live execution yet.

## Documents

- CONCEPTUAL_MASTER_PLAN.md
- MATHEMATICAL_ENGINE_SPEC.md
- STRATEGY_SEARCH_SPACE.md
- PROFITABILITY_EXECUTION_INVARIANTS.md
- ZERO_COST_ARCHITECTURE.md
- PROJECT_STATUS.md
- PROJECT_MEMORY.md
