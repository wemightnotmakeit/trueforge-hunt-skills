---
name: fast-criticals
description: "Crack-order playbook: the fastest-to-prove critical bug classes, each with detection recipe, minimal PoC shape, and kill signal — plus where these bugs live (seam-diffs, fresh deploys, audit-fix waves). Use to choose what to hunt next and to drive candidate volume without losing accuracy."
---

# Fast Criticals — crack-order playbook

Ranked by time-to-provable-critical x likelihood it's critical. Work top-down. One class per hunter run.

## TIER 1 — provable critical in under a day

### 1. Seam-diff — a fix merged but not deployed
WHERE: repo HEAD vs deployed artifact (explorer metadata / spec_version / program dump / verified source). Then `git log --oneline <deploy-date>..HEAD -- <in-scope paths>`.
SIGNAL: fix commits dated AFTER the deploy touching in-scope code = a live, documented bug. The fix's own test IS the PoC.
PoC: worktree at the fix's parent commit; run the fix's regression test; expect FAIL pre-fix; control run PASS with fix.
EXAMPLES: Hydration XCM accumulator (spec 447 live, fix lands in 448); Raydium c613c87 owner check; gnosischain proxies still pre-fix.
KILL: fix is deployed -> not live -> record and move on.

### 2. Missing authorization on a privileged path
WHERE: every external entrypoint. EVM: missing onlyOwner/onlyRole, tx.origin auth, unprotected initialize/re-initialize, public setter of owner/fee/oracle/impl, a check dropped in a copy-pasted sibling. Solana: missing is_signer, missing owner check, PDA seed confusion, arbitrary CPI target, unchecked account owner.
TEST: call as a random funded address; compare against a protected sibling function.
PoC: `vm.prank(attacker); target.adminFn();` asserting success where it must revert.
KILL: a guard exists later in the function (read it to the end), or the function is permissionless by design.

### 3. Vault share inflation / first-depositor
WHERE: ERC4626-style vaults, LP mints, any asset<->share conversion, `totalAssets()` = balanceOf(asset).
TEST: empty vault: deposit 1 wei -> donate large amount -> victim deposit rounds to 0 shares; or attacker withdraws more than deposited.
PoC: fork test, 3 actors, assert victim shares == 0 or attacker profit > 0.
KILL: virtual shares/offset present (OZ v5 style) or minimum-deposit guard.

### 4. Rounding in the caller's favor (repeatable drain)
WHERE: every mul/div on balances/amounts in withdraw/claim/swap paths; grep `/` and `mul_div`; check ceil/floor direction line by line.
TEST: loop the operation N times; if the caller gains >= 1 unit per iteration -> drain.
PoC: loop 1000x, assert balance strictly increases.
KILL: rounding favors the protocol on every path (state each direction explicitly).

### 5. Accounting desync — accumulators not decremented
WHERE: every state var that gates an action (limits, debt, counters, reward accruals, health). List ALL paths that should update it; find the missing one.
SIGNAL: one-directional counters (only go up); deposit/repay paths skipping the decrement; floor-vs-ceil in emission accounting.
EXAMPLES: Hydration withdraw accumulator never offset by inbound -> all XCM withdrawals DoS-able; reward solvency floor-vs-ceil.
PoC: perform the symmetric operation (deposit after withdraw) and show the counter does not move.
KILL: the decrement exists on a shared inner path you missed.

### 6. Fresh code (<90 days) — the diff is the target
WHERE: explorer sorted by age; scope deltas (program page changes); a NEW instruction/function added to an OLD battle-tested program (redeploys); new collateral/market types; new feature flags.
TEST: audit the DIFF only — the old code is fine, the new 200 lines are not.
EXAMPLES: Raydium AMM v4 Sep-11 redeploy (#70 withdraw_excess_lamports + rewrite); CLMM limit orders + dynamic fee.
KILL: the new code is a rename/refactor with an in-repo equivalence test that passes.

## TIER 2 — 1-3 days, critical when hit

### 7. Oracle trust
WHERE: price source of every valuation/liquidation/borrow path. Spot DEX price? single source? staleness check? decimals (6 vs 18)? L2 sequencer uptime? TWAP window vs manipulation cost?
PoC: manipulate the spot source within one tx (flash-loan), assert mispricing.
KILL: Chainlink with staleness + sequencer checks, or TWAP >= 30min with deep liquidity.

### 8. Liquidation logic
WHERE: liquidation bonus math, partial-liquidation caps, bad-debt handling, liquidator incentives.
TEST: can a healthy position be liquidated? can an underwater one NOT be liquidated (DoS)? does bad debt stick to the protocol? can a liquidator self-liquidate for profit?
KILL: guards + caps + bonus < penalty on all paths.

### 9. Reentrancy (incl. read-only)
WHERE: external calls before state writes; ERC777/721/1155 callbacks; hooks; CPI re-entry (Solana); view functions consumed by third parties mid-tx.
PoC: attacker contract re-enters during the callback window; assert double-withdraw / stale read.
KILL: CEI respected + reentrancy guard + no third-party consumers of mid-state views.

### 10. Proxy / init / upgrade traps
WHERE: uninitialized implementation (callable directly?), re-initialization, storage layout collisions on upgrade, unprotected upgradeTo, initializer front-run.
KILL: initializer consumed on-chain and impl guarded.

### 11. Signature / permit replay
WHERE: ecrecover paths — nonce, chainid, domain separator, malleability (s vs s'), ecrecover(0), cross-contract replay.
KILL: full EIP-712 domain + nonce + deadline verified.

### 12. Bridge / messaging limits & replay
WHERE: rate limiters (does every path credit/decrement correctly?), message replay (chainid/nonce), validator trust, xcm/ccip/layerzero adapters.
EXAMPLES: Hydration class — the limit counts outflows but not the offsetting inflows.
KILL: symmetric accounting proven by test.

## TIER 3 — slower, still critical when hit
13. Economic/MEV: sandwichable user flows, JIT liquidity, auction manipulation, reward farming.
14. Governance: flash-loan voting, execution races, timelock bypass.
15. DoS of critical paths: unbounded loops, griefable queues, lock windows — "blocking users from accessing funds" is often High/Critical on impact lists.

## Where fast criticals live (target sourcing, scale order)
1. Seam-diffs (fix merged, not deployed) — highest certainty.
2. Scope deltas — programs adding assets (weekly board diff).
3. Fresh deploys < 90 days — new code, no audit mileage.
4. Audit-fix waves — the fix commits themselves (new bugs + unfixed siblings).
5. Migrations — v2->v3 with v1 still live.
6. Contests (Code4rena/Sherlock/Cantina) — dozens of contracts, fixed deadline, guaranteed evaluation.
7. Low-eyes ecosystems — new L1/L2s, Solana programs < $1B TVL.

## Throughput rules (recall without losing accuracy)
- Triage each (target x class) in <= 1 iteration against the TIER-1/2 recipes; deep-dive only hits.
- Breadth first: 8-12 parallel briefs per target beats 2 deep ones — kills are cheap, misses are not.
- Every survivor still passes: red-team -> poc-forge -> verifier. The gates are what keep accuracy at 100%.
- Log every kill to DEAD.md — a re-derived kill is wasted compute.
