# PLAYBOOK: accumulator-dos (unbounded accumulation → griefing / DoS)

CLASS: A per-key (per-user/per-message/per-chain) accumulation structure (queue, pending list, withdraw accumulator, claim list) that any cheap action can append to, while processing/resolving it is expensive or blocking. Attacker appends N cheap entries → system cannot process → withdrawals/claims/resolution stall (griefing DoS). Escalates to fund-loss when entries lock user value.

ARCHETYPES: bridges/XCM (withdraw accumulators, pending transfers), staking reward queues, batch auction order books, claim/payout lists, message queues with per-message fees.

## DETECT (in order)
1. Find append-only state: grep for Vec/queue/deque/BTreeMap/pending patterns in storage; look for `push`, `append`, `insert` on per-key structures.
2. For each: WHO can append? (any signed user / any relayer / any cross-chain message). At WHAT cost? (fee, deposit, gas only).
3. Find the PROCESS/RESOLVE path: who iterates the structure? Is it bounded per call? What happens when it grows — per-item cost, block gas limit, timeout, or "one bad item blocks all"?
4. Compare cost-to-append vs cost-to-process. Attack wins when append is O(1) cheap and process is O(n) expensive / blocking.
5. Check for caps, expiry, pruning, pagination, and fee-per-entry that scales with processing.

## EXPLOIT RECIPE
- Append the cheapest valid entries (min amount, min fee) from one or many accounts (watch per-account limits — if capped, use many accounts; that's still cheap).
- Grow to the point where the resolve/process path exceeds per-block limits or the queue's timeout.
- Demonstrate impact: pending withdrawals cannot complete, resolution stalls for all users, or processing permanently fails (locked funds).

## POC SHAPE (foundry, fork test)
1. Fork at pinned block. 2. Open/fund N attacker accounts. 3. Loop: append min-size entries. 4. Call the resolve/process path — assert it reverts / exceeds gas / leaves honest users' funds stuck. 5. Measure: entries needed vs cost per entry vs blocked value. 6. Negative control: same test against the FIXED build must pass (or bounded).

## REAL CASES
- **Hydration (Polkadot, XCM withdraw accumulator)** — per-(asset, dest-chain) accumulators grew unboundedly from cheap XCM messages; withdrawal processing became unviable. Fix bounded/limited growth (spec 447→448, commit 1753be74). Proof: pre-fix test FAIL (accumulated ~5e13 vs expected ~2e13) + post-fix control PASS. VERIFIED by fleet.

## KILL SIGNALS
- Append cost ≥ process cost per entry (no asymmetry).
- Entries auto-expire or are pruned in bounded time regardless of attacker.
- Hard cap enforced on the structure with a working eviction path.
- Process path paginated so growth only delays, never blocks (delay < materiality).
