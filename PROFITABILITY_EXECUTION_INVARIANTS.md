# PROFITABILITY + EXECUTION INVARIANTS

## 1. Purpose

This document defines the hard mathematical and operational conditions that must hold before a candidate can reach the transaction builder.

## 2. Candidate States

A candidate moves through:

DISCOVERED
-> NORMALIZED
-> QUOTED
-> ECONOMICALLY_VALID
-> SIMULATION_VALID
-> SECURITY_VALID
-> AUTHORIZED
-> SUBMITTED
-> CONFIRMED
-> RECONCILED

Any failure moves to REJECTED or QUARANTINED.

## 3. Hard Profit Invariant

The candidate is eligible only if:

ExpectedNetUSD > 0.20

Strictly greater means exactly $0.20 does not pass.

## 4. Unknown-Cost Invariant

If any material cost is unknown:

NO TRADE

Examples:
- unknown flash fee
- unknown gas cost
- unknown protocol fee
- unknown route cost
- uncertain valuation
- uncertain token transfer behavior

## 5. Fresh-State Invariant

Every candidate stores:
- quote block
- pool-state versions
- simulation block
- quote timestamp
- simulation timestamp

If required state changed beyond policy tolerance:

INVALIDATE -> REQUOTE -> RESIMULATE

Never reuse an expired candidate.

## 6. Simulation Invariant

No live submission without a passing state-aware simulation.

Simulation must verify:
- route execution
- output minimums
- flash-loan callback
- repayment
- expected balance deltas
- gas estimate
- no unexpected revert

## 7. Atomic Profit Invariant

The transaction must fail atomically if:
- repayment cannot be completed
- required output is not achieved
- authorized route differs
- minimum profit invariant is violated

The executor must not leave partially executed debt or an unintended asset state.

## 8. Route Integrity

Before signing:
- route hash must match authorized candidate
- pool addresses must match allowlist
- token addresses must match allowlist
- function selectors must be expected
- calldata must be generated deterministically

Any mismatch:
**ABORT**

## 9. Gas Invariant

Submission requires:

estimated worst-case gas cost <= configured gas-loss budget

and

wallet_native_balance - worst_case_gas >= wallet_safety_floor

Actual receipt gas is reconciled after execution.

## 10. MEV Invariant

For strategy classes requiring private execution:

private submission health must pass.

If private path is unavailable, stale or unverified:

**NO TRADE**

The system must never claim that private submission eliminates all MEV risk. It is one control in a larger security model.

## 11. Approval Invariant

The executor may interact only with explicitly authorized token/pool/router contracts.

Unlimited approvals are prohibited by default.

Approvals must be:
- minimized
- tracked
- revocable
- audited

## 12. Token Behavior Invariant

Reject or quarantine tokens with unresolved:
- transfer tax
- rebasing behavior
- blacklist/pause behavior
- callback surprises
- non-standard transfer semantics
- proxy/upgrade uncertainty where material

## 13. Nonce Invariant

Exactly one authority owns the live nonce.

Handle:
- pending nonce
- confirmed nonce
- replacement
- timeout
- stuck transaction
- duplicate submission

A nonce race is a hard execution fault.

## 14. Wallet Invariant

The capital guardian enforces:
- native balance floor
- maximum transaction value
- maximum gas
- maximum simultaneous exposure
- daily/rolling loss limit
- emergency stop

## 15. Realized PnL Invariant

For a confirmed transaction:

RealizedPnL =
actual asset deltas
- flash repayment
- actual gas
- actual fees
- other realized costs

The system must not mark a trade profitable using a model-only number.

## 16. Loss Response

If realized PnL is negative:
1. stop the affected strategy
2. preserve complete evidence
3. classify failure
4. reproduce by simulation/fork where possible
5. identify violated assumption
6. add regression test
7. re-enable only after review

## 17. Revert Response

A revert is never treated as harmless.

The system records:
- gas consumed
- revert selector/reason if available
- state block
- route
- simulation result
- provider
- submission method

Repeated simulation-pass -> live-revert patterns trigger automatic quarantine.

## 18. Evidence Object

Every candidate must have a machine-readable evidence record:

candidate_id
strategy_id
route_id
state_block
pool_state_hashes
input_amount
output_amounts
all_fees
gas_estimate
flash_fee
expected_net_usd
robust_net_usd
simulation_result
security_result
authorization_result
tx_hash
receipt
realized_pnl
failure_class

## 19. No-Guarantee Rule

The architecture optimizes for profitable execution but does not assert guaranteed profit.

The only acceptable production claim is evidence-based:
- how often candidates pass
- how often simulations match execution
- realized PnL
- realized gas
- realized failure rate
- strategy-level statistics

## 20. Final Gate

Conceptually:

TRADE =
FreshState
AND ExactMathPass
AND FullCostKnown
AND SimulationPass
AND SecurityPass
AND RouteIntegrityPass
AND WalletGuardPass
AND PrivatePolicyPass
AND ExpectedNetUSD > 0.20
AND ConfidencePolicyPass

Otherwise:

NO TRADE
