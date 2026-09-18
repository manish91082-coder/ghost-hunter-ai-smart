# STRATEGY SEARCH SPACE — PERMUTATION, COMBINATION AND ROUTE EXPLORATION

## 1. Objective

The strategy engine must explore a large combinatorial space without blindly enumerating every mathematically possible path.

The problem is a constrained graph-search problem.

## 2. Dimensions of the Search Space

A candidate can vary across:

1. starting asset
2. flash-loan asset
3. venue
4. pool
5. pool type
6. token direction
7. fee tier
8. hop count
9. route ordering
10. input amount
11. amount split
12. cycle length
13. stable/non-stable path
14. concentrated-liquidity state
15. gas environment
16. submission method
17. block/state freshness
18. optional backrun trigger
19. candidate confidence
20. historical execution profile

This creates a combinatorial explosion.

## 3. Route Families

### A. Two-edge cycles
A -> B -> A

Across:
- same venue / different pools
- different venues
- different pool types
- different fee tiers

### B. Three-edge cycles
A -> B -> C -> A

### C. Four-edge cycles
A -> B -> C -> D -> A

### D. Multi-hop cycles
A -> token_1 -> ... -> token_n -> A

Hop count is policy-bounded dynamically by AC.

## 4. Venue Combinations

For a token pair with N executable pools:

Pairwise combinations are approximately:

C(N,2) = N(N-1)/2

But each pair may have:
- direction
- fee tier
- amount range
- pool type

The engine therefore stores canonical route signatures to remove economic duplicates.

## 5. Amount Search

For each route, amounts form another dimension.

Use:
- logarithmic candidate amounts
- liquidity-derived boundaries
- fee-break-even amount
- gas-break-even amount
- local maximum candidates
- tick boundary candidates
- exact refinement around promising points

## 6. Split-Route Search

Future route families may split capital across parallel pools.

Example:

A -> {Pool 1 + Pool 2 in parallel} -> B

The system should treat split routing as an optimization problem:

maximize NetProfit(x_1,...,x_k)

subject to:
sum(x_i) = X

and each pool's liquidity/invariant constraints.

This is a later-stage optimization because it increases simulation and execution complexity.

## 7. Triangular Graph Search

Use directed edges and cycle detection.

Reject cycles that:
- repeat a pool unnecessarily
- contain unsupported tokens
- contain stale state
- cannot repay flash liquidity
- cannot theoretically exceed the economic threshold

## 8. Multi-Venue / Multi-Protocol Search

A route can combine:
- constant-product pool
- concentrated-liquidity pool
- stable-swap pool
- weighted pool

The route engine must call the correct quote adapter for each edge.

## 9. Signal Families

Candidate generation can use:

### Price discrepancy
Different executable prices for the same pair.

### Fee-tier discrepancy
Different concentrated-liquidity tiers produce different net execution prices.

### Liquidity migration
Large state changes alter relative prices.

### Block-state dislocation
A confirmed state update creates a temporary discrepancy.

### Router disagreement
Aggregators disagree with direct pool mathematics.

### Statistical anomaly
Observed price/flow behavior deviates from historical patterns.

Signals generate candidates only. They never authorize trades.

## 10. Candidate Deduplication

Canonical signature should include:
- chain
- starting token
- ordered pools
- ordered tokens
- direction
- strategy family
- flash source
- amount bucket

Equivalent routes should not consume repeated simulation budget.

## 11. Search Funnel

The engine should prioritize:

Tier 0: structural validity

Tier 1: cheap upper-bound profit

Tier 2: deterministic exact quote

Tier 3: amount optimization

Tier 4: full cost model

Tier 5: state-aware simulation

Tier 6: adversarial security

Tier 7: authorization

This is the central method for exploring a huge search space with limited free compute.

## 12. Upper-Bound Profit Filter

Before expensive simulation, calculate a conservative upper bound.

If even the optimistic bound cannot exceed $0.20 after unavoidable costs:

**discard without simulation.**

The upper bound must never be used as proof of profit.

## 13. Adaptive Search

AC may change:
- max hops
- token universe
- pool universe
- amount samples
- number of candidate routes
- simulation concurrency
- strategy priority

AC may not lower:
- $0.20 threshold
- safety floor
- simulation requirement
- allowlists
- security policy

## 14. Opportunity Scoring

Candidate ranking can consider:
- expected net profit
- robust net profit
- liquidity headroom
- gas efficiency
- state freshness
- historical fill rate
- latency
- competition
- simulation confidence
- route complexity

A score only determines search order. It does not override the hard gate.

## 15. Future Mathematical Extensions

Potential advanced families:
- multi-pool split optimization
- convex/continuous route optimization where mathematically valid
- discrete tick-boundary optimization
- stochastic execution-risk modeling
- online bandit allocation of compute
- graph neural network candidate ranking
- reinforcement learning for search allocation

These are optimization layers, not replacements for deterministic execution math.

## 16. Saturation Rule

The strategy engine may add new strategy families only when:
- the strategy has a formal interface
- exact economics exist
- simulation exists
- adversarial checks exist
- regression tests exist
- evidence demonstrates incremental coverage

No strategy is accepted merely because it looks profitable on a spreadsheet.
