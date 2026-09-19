# MATHEMATICAL ENGINE SPECIFICATION

## 1. Purpose

The mathematical engine is deterministic and independent of AI.

Its job is to answer one question for a concrete state, route and input amount:

**What is the exact executable output and net economic result?**

## 2. Common Route Equation

For route edges e_1 ... e_n:

x_0 = input amount

x_i = Swap_i(x_{i-1}, State_i)

GrossOutput = x_n

Every Swap_i must use pool-type-specific invariant mathematics.

## 3. V2 Constant Product

For reserves R_in, R_out and fee f:

amount_in_after_fee = amount_in * (1-f)

amount_out =
(amount_in_after_fee * R_out)
/
(R_in + amount_in_after_fee)

The implementation must use integer arithmetic matching on-chain rounding behavior.

## 4. Concentrated Liquidity

For V3/Algebra-style pools the engine must model:
- sqrt price
- active tick
- liquidity
- fee
- tick spacing
- initialized tick boundaries
- token ordering
- amount direction
- per-tick liquidity changes
- integer rounding

A quote must walk across tick boundaries when the input amount consumes active liquidity.

A single-price approximation is not execution truth.

## 5. StableSwap

The engine must implement the exact invariant required by each supported pool implementation, including:
- balances
- amplification parameter
- fee
- asset count
- implementation-specific rounding

Do not reuse V2 or V3 formulas for StableSwap.

## 6. Weighted / Composable Pools

For Balancer-like pools, implement the invariant and fee rules of the specific pool specialization.

Pool parameters are runtime state.

## 7. Fee Stack

For every route, separately model:
- pool swap fee
- protocol fee
- flash-loan fee
- router fee
- external execution fee
- gas
- other known route costs

No fee may be silently folded into another field.

## 8. Gas Economics

GasCostNative =
GasLimit * EffectiveGasPrice

GasCostUSD =
GasCostNative * NativeAssetUSD

The engine must distinguish:
- estimated gas
- simulation gas
- submitted gas limit
- actual gas used
- actual effective gas price

Actual receipt values are used for realized PnL.

## 9. Flash-Loan Repayment

For borrowed principal P and fee F:

Repayment = P + F

The executor must prove repayment before allowing residual profit extraction.

Flash liquidity is not assumed to be free or always available.

## 10. Slippage and Price Impact

Do not model slippage as a fixed percentage.

Price impact emerges from the pool invariant and input amount.

Execution minimums must be derived from exact state-aware calculations plus policy reserve.

## 11. Net Profit

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
ExpectedNetUSD > 0.20

The engine must also calculate:
- gross profit
- cost ratio
- profit per gas unit
- profit per unit of liquidity consumed
- sensitivity to input amount
- sensitivity to gas
- sensitivity to output price

## 12. Sensitivity Analysis

For each candidate, calculate the effect of:
- input amount +/- small perturbations
- gas price increase
- output price movement
- pool reserve/liquidity movement
- latency/state-age increase

A candidate whose edge collapses under tiny perturbations receives low robustness and may be rejected.

## 13. Amount Optimization

Profit(amount) is generally non-linear.

Search methods may include:
- coarse logarithmic scan
- bracketed local search
- ternary/golden search where unimodality is demonstrated
- discrete refinement
- boundary checks
- liquidity/tick boundary candidates

Never assume global unimodality without evidence.

## 14. Integer and Decimal Discipline

All on-chain token amounts are integer base units.

The engine must:
- preserve raw integer values
- use explicit token decimals only for presentation/conversion
- use checked arithmetic
- reproduce Solidity-style truncation/rounding
- avoid floating-point arithmetic in execution-critical calculations

USD conversion is a separate valuation layer.

## 15. Oracle / Valuation Discipline

USD is a reporting and policy unit, not a substitute for exact token math.

The system should retain:
- raw token amounts
- native asset value source
- stablecoin/reference valuation
- valuation timestamp
- valuation confidence

If USD valuation is uncertain beyond policy bounds:
**NO TRADE.**

## 16. Independent Verification

Every supported AMM implementation requires:
- reference test vectors
- boundary cases
- zero amount cases
- max/min liquidity cases
- rounding cases
- fee cases
- tick crossing cases
- revert-equivalent cases

The same mathematical result should be independently checked by a second implementation or on-chain simulation before production use.

## 17. Mathematical Invariants

Examples:
- output cannot exceed invariant-implied maximum
- repayment must be fully funded
- minimum output must be respected
- no unexpected token leaves the executor
- profit must be positive above policy threshold
- gas ceiling must hold
- route must match authorized route hash
- state block must be within freshness policy

The invariant layer is the final mathematical firewall.
