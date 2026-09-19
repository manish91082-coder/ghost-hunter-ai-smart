# AGENTIC ROLE SYSTEM

## Orchestration Principle
The system uses specialized agents, but all agents operate under a deterministic policy and evidence layer.

### 1. MASTER ORCHESTRATOR
Owns objective, phase progression, task allocation, checkpoints and recovery.

### 2. POLYGON CHAIN SCOUT
Discovers chain configuration, blocks, gas, RPC/WSS health, logs and network conditions.

### 3. VENUE DISCOVERY AGENT
Discovers DEX factories, routers, pools, fee tiers, pool types and deployment changes.

### 4. TOKEN INTELLIGENCE AGENT
Maintains token metadata, decimals, code hash, transfer behavior, tax/fee anomalies and trust state.

### 5. POOL STATE AGENT
Maintains fresh reserves/liquidity/ticks/weights/amplification and pool-specific state.

### 6. ROUTE GRAPH AGENT
Builds a continuously changing graph of token-to-token executable edges.

### 7. STRATEGY GENERATOR AGENT
Generates candidate strategies:
- two-venue arbitrage
- V2/V3 arbitrage
- V3/V3 fee-tier arbitrage
- triangular arbitrage
- stablecoin loops
- multi-hop routes
- concentrated-liquidity range opportunities
- weighted/stable pool opportunities
- cross-router path combinations

### 8. EXACT MATH ENGINE
Deterministic only. Calculates exact amount-out, fees, price impact, tick movement, pool math and repayment.

### 9. ECONOMIC AUDITOR
Calculates:
Gross edge
- DEX fees
- flash-loan fee
- gas
- route cost
- slippage
- protocol fee
- safety reserve
= expected net profit

Only strict net profit > $0.20 passes.

### 10. SIMULATION AGENT
Runs eth_call / trace / fork simulation and verifies:
- no revert
- expected balances
- repayment
- profit
- gas estimate
- state assumptions

### 11. ADVERSARIAL SECURITY AGENT
Tests:
- sandwich exposure
- stale state
- changed reserves
- changed ticks
- callback abuse
- malicious token behavior
- reentrancy surfaces
- allowance abuse
- arbitrary external call paths
- nonce races
- replacement transaction hazards

### 12. MEV / PRIVATE ORDERFLOW AGENT
Selects the safest supported submission path. Polygon Private Mempool is the primary candidate and must be verified operationally before production use.

### 13. EXECUTION GUARDIAN
Final deterministic authorization gate. It cannot be overridden by the AI strategy generator.

### 14. WALLET & CAPITAL GUARDIAN
Controls native balance floor, approvals, spend limits, nonce ownership and emergency shutdown.

### 15. RECEIPT / PnL AUDITOR
Independently computes realized PnL from receipt + logs + wallet balance deltas. Modeled PnL is never accepted as realized PnL.

### 16. ADAPTIVE CONTROL / AC AGENT
AC is defined here as Adaptive Calculation & Control:
- continuously retunes non-market-controlled parameters
- changes search breadth, route limits, confidence thresholds and gas policy within hard safety bounds
- never changes the $0.20 minimum-net-profit policy without an explicit governance change
- learns from failed, skipped and successful candidates

### 17. RESEARCH SCIENTIST AGENT
Studies new pool math, DEX mechanics, arbitrage literature, MEV behavior and new Polygon venues.

### 18. EVIDENCE & PROVENANCE AGENT
Every important claim receives source/state/evidence metadata.

### 19. REGRESSION AGENT
Runs deterministic tests against known historical blocks, synthetic edge cases and prior failures.

### 20. INCIDENT RESPONSE AGENT
Detects anomalies and can force:
PAUSE -> QUARANTINE -> DIAGNOSTIC -> RECOVERY.

## Authority Hierarchy
1. Safety / capital limits
2. Deterministic verifier
3. Execution policy
4. Evidence layer
5. Strategy engine
6. AI optimization

Lower layers cannot override higher layers.
