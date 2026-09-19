# DYNAMIC ENGINE & AC CONTROL SPECIFICATION

## Objective
हर market-dependent variable को runtime पर discover/refresh करना है। कोई static snapshot production truth नहीं है।

## Dynamic Inputs

### Chain
- latest block
- block timestamp
- gas base fee / effective gas conditions
- priority fee policy
- RPC latency
- WSS latency
- reorg/finality state
- pending transaction visibility
- private mempool availability

### Pool
- reserves
- sqrt price
- active tick
- liquidity
- fee
- token balances
- amplification / weights where applicable
- pool status
- recent swaps
- state block number

### Token
- decimals
- code hash
- balance
- allowance
- transfer success
- transfer tax/fee behavior
- pause/blacklist signals
- metadata confidence

### Flash Loan
- lender availability
- reserve liquidity
- flash fee
- asset eligibility
- callback constraints
- current pool state

### Execution
- gas estimate
- gas ceiling
- nonce
- wallet native balance
- private submission health
- deadline
- min-output
- expected state block

## Adaptive Parameters
AC may dynamically tune:
- candidate scan depth
- route hop limit
- candidate amount
- confidence threshold
- simulation refresh frequency
- gas cap within policy
- pool minimum-liquidity filter
- stale-state timeout
- RPC provider selection
- parallelism
- search priority
- strategy ranking weights

## Hard Policy Parameters
AC may NOT autonomously weaken:
- minimum net profit > $0.20
- wallet safety floor
- contract allowlist
- maximum gas-loss budget
- simulation requirement
- private submission requirement where mandated
- deterministic verification requirement
- emergency kill switch

## Per-Block Control Loop

At each new block:
1. ingest block
2. update changed pools only
3. update gas
4. update token/pool state
5. invalidate stale quotes
6. regenerate affected routes
7. exact quote
8. calculate economics
9. simulate only candidates above a cheap prefilter
10. adversarial checks
11. final authorization
12. submit privately if all gates pass
13. verify receipt
14. reconcile actual wallet deltas
15. update learning state

Do not assume exactly 2 seconds. Treat block arrival as event-driven and measure actual inter-block time.

## Event-Driven Priority
A full global recomputation every block is wasteful.

Use:
BLOCK -> CHANGED POOLS -> AFFECTED TOKENS -> AFFECTED ROUTES -> CANDIDATES.

This reduces compute and latency while preserving freshness.

## Quote Freshness
Every candidate stores:
- state block
- state timestamp
- pool state hashes/version
- quote timestamp
- simulation block
- submission timestamp

If state moves beyond policy tolerance, candidate is invalidated.

## Zero-Trust Evidence Object
Every candidate receives:
candidate_id
strategy_id
route
pool addresses
token addresses
state block
input amount
exact outputs
all fees
gas estimate
flash fee
expected net profit
simulation result
security checks
confidence
authorization decision
transaction hash
receipt
realized PnL

## AC Feedback Loop
Success -> learn which conditions produced stable execution.
Skip -> learn which filters were too broad/tight.
Revert -> quarantine exact state pattern.
Loss -> immediate forensic review; strategy may be disabled automatically.
Profit -> record realized result, not just predicted result.

## Dynamic Strategy Formula
The system does not seek a fixed formula that guarantees profit.

It seeks a continuously recalculated decision function:

TRADE =
(
FreshState
AND ExactSimulationPass
AND SecurityPass
AND PrivateSubmissionAvailable
AND WalletGuardPass
AND ExpectedNetUSD > 0.20
AND Confidence >= DynamicThreshold
)

Otherwise:
NO TRADE

## Research Extension
Future strategy modules must implement:
- discover()
- quote()
- exact_cost()
- simulate()
- adversarial_check()
- authorize()
- execute()
- reconcile()

No strategy enters production without all seven interfaces.
