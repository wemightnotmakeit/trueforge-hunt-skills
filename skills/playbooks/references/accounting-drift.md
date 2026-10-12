# PLAYBOOK: accounting-drift (value leak via rounding / ordering / fees)

CLASS: Share/balance/interest accounting where rounding direction, operation ordering, or non-standard token behavior lets value drift to an attacker: rounding harvests, first-depositor/inflation, fee-on-transfer mismatches, stale checkpoints, double-counting, insolvency via repeated small ops.

ARCHETYPES: vaults (ERC4626-style), lending pools, AMM LP accounting, staking derivatives, reward distributors, any shares↔assets conversion.

## DETECT (in order)
1. List EVERY balance mutation (deposit/withdraw/swap/reward/accrue). Build the invariant table: sum(user claims) == total accounted; shares × pricePerShare == assets.
2. Check rounding direction per op: deposits/withdrawals should round AGAINST the user (protocol-favoring) on both sides. Find any op rounding in user's favor.
3. Check ordering: state updates before/after transfers? (reentrancy + stale reads). Checkpoint updates BEFORE computing new rewards?
4. Check token assumptions: fee-on-transfer / rebasing / ERC777 hooks / non-standard decimals. Does accounting use balanceOf deltas or nominal amounts?
5. Loop test: can N repeated tiny ops (deposit→withdraw, claim→redeposit) monotonically grow attacker balance? Simulate mentally, then prove.

## EXPLOIT RECIPE
- Rounding harvest: loop the op that rounds in your favor (1 wei per iteration × many iterations / many accounts).
- First-depositor inflation: be first, donate to inflate share price, next depositor's shares round to zero / get diluted.
- Fee-on-transfer: deposit nominal, receive less, but shares minted on nominal → withdraw more than deposited.
- Stale checkpoint: trigger accrual after manipulating inputs so unaccrued state uses new values.

## POC SHAPE
1. Fork test, pinned block. 2. Attacker deposits X. 3. Loop exploit op K times (assert balance strictly grows OR honest users' withdrawable shrinks). 4. End state: attacker profit > 0 with honest user loss OR protocol insolvency (sum of claims > assets). 5. Negative control: fixed build → loop yields 0 profit.

## REAL CASES
- (fleet) Class ranked TIER 1: rounding/accounting bugs are provable in a single looped test — fastest critical PoC shape.
- Public patterns: ERC4626 inflation attacks (empty-vault donation), fee-on-transfer accounting mismatches, reward checkpoint ordering bugs.

## KILL SIGNALS
- All ops round protocol-favoring on both directions (verify the math by hand — don't trust comments).
- Loop profit bounded by dust (< materiality threshold) OR requires capital you can't retain.
- Token set is strictly standard ERC20 (no fee/rebasing/hooks) AND accounting uses deltas.
