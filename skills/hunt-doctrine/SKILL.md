---
name: hunt-doctrine
description: "The house rules for bounty hunting with a fleet: scope-first, seam-diff, dupe doctrine, execution gates, kill-recording. Use in every hunting role before acting on any lead."
---

# Hunt Doctrine (fleet edition)

## 0. The prime rules
1. **No reproduction command, no finding.** A claim without a green `forge test` (or equivalent raw output) on a pinned block is a lead, not a finding.
2. **A KILL is a result.** Record cleared surfaces in DEAD.md — dead ends prevent the fleet from re-deriving them. Never "forget" a kill to look productive.
3. **Never trust a summary — including your own.** For every external claim, require the handle (address, block, URL, SHA, path) and check it.
4. **Honest severity only.** Map to the program's own impact titles, verbatim. No upgrading to please.

## 1. Scope-first (before ANY hunting)
- Read the program page: assets (file-level if "primacy of rules"), impact list, known issues, KYC/fee gates, prohibited activities (no mainnet testing! local forks only).
- If scope lists FILE LINKS: that is the contract. Anything outside = not reportable, however buggy.
- If scope says "code involving runtime pallets" or similar: impact that LANDS on an in-scope component counts — argue it explicitly, never assume.
- Check the program's knownIssues list + the repo's public post-mortems before investing. An empty KI list is a green light, not a promise.

## 2. Seam-diff (the highest-yield pattern)
Deployed ≠ repo. The gap is where live bugs hide:
1. Get deployed version: explorer metadata, `spec_version`, impl slot, program dump.
2. Get repo HEAD + recent commits touching in-scope files.
3. Find fixes that are **merged but NOT deployed** — each is a documented, live vulnerability (the project proved the bug themselves).
4. Reproduce pre-fix behavior (worktree at the fix's parent) — the fix's own test often IS the PoC.

## 3. Dupe doctrine
- First-COMPLETE wins. Same file + one-fix-fixes-both = same finding (dupe).
- Sweep before building: known corpus, GitHub PRs/issues, program comments, and web search over Solodit's indexed pages (`site:solodit.cyfrin.io <mechanism>` — keyless; the Solodit API is now paid-tier). Record the sweep.
- Known-issue close needs the FULL mechanism + impact matched — "related" is not "same". If the fix is public but undeployed, the live vulnerable build is your counter.

## 4. Execution gates (every finding passes all four)
| Gate | Question | Evidence |
|---|---|---|
| G1 Scope | Is the asset in scope per the exact list? | quote the scope line |
| G2 Dupe | Is this mechanism already known/reported? | sweep receipt |
| G3 Repro | Does a one-command repro show the impact? | raw green output + pinned block |
| G4 Verify | Did a SECOND party re-run it from scratch? | verifier's raw output |

## 5. Impact amplification (before closing any MEDIUM)
Try to CHAIN: compose this bug with one other (same target or adjacent) into a CRITICAL impact before submitting — chains pay at the top severity and rarely get duplicated. If no chain exists after one honest pass, ship the medium alone.

## 6. Report craft
Title = vulnerability + impact. Impact section = the program's own impact title + funds-at-risk math.
PoC = the pinned repro command + raw output + negative control. Recommendation = minimal, honest.
Attach everything; explain nothing twice.

## 7. Tool guardrails (hard rules)
- **No live-network writes, ever:** `cast send`, `forge create`, `forge script --broadcast` only against local forks/anvil. If a PoC needs a mainnet state change, prove it on a pinned fork instead.
- **GitHub MCP = read tools only** for sweeps (search/read). Never `delete_file`, `create_or_update_file`, or push unless the task explicitly says so.
- **No secret exfil:** never print or send env vars/keys out of the sandbox; findings and logs only.

## 8. Anti-patterns (measured, real)
- **Analyzer anchoring:** asking a model "is this finding real?" makes it agree. Ask it to BREAK a named invariant instead.
- **Lexical anchoring:** suspicious names ≠ bugs. Judge by the invariant broken.
- **Bigger context ≠ better:** bulk belongs in on-demand files, not always-loaded prompts.
- **Tool-text reports:** Immunefi treats scanner-dump reports as spam. Findings must be human-crafted.

## 9. Turn economy & infra reality (2026-10-13, live incident)
- The server CANCELS turns at ~60 min (server-execution-timeout). Write state + post the <=5-line report by minute ~50. ONE bounded wave per turn (scout | hunt | verify+package) - never chain long waves.
- State hygiene: keep /opt/hunt-state/STATE.md (one page: board, active candidates, kill count, next actions) updated at turn END. Next turn reads STATE.md FIRST - re-orientation from raw context is the biggest silent time sink.
- Skills paths: CANONICAL = /opt/tfy/skills (TrueForge). Env v6 bakes an always-present copy: /opt/tf/skills (=symlink to /opt/hunt-cache/fleet-skills). If one path is empty, try the other; restore with `cp -r /opt/hunt-cache/fleet-skills/* /opt/tfy/skills/`. Check ONCE; never burn cycles searching.
- GITHUB_TOKEN exists only in sandboxes created AFTER the secret was attached. Repo sync is best-effort; /opt/hunt-state is canonical.

## 10. Falsification-first (verifier standard - campaign 2026-10-13 receipts)
Before ANY candidate may be called a survivor, it needs receipts for all three attacks:
1. HEAD-TO-HEAD DELTA (economic claims): measure value delivered to legit actor vs attacker under identical conditions. Delta = 0 -> KILL. (Receipt: v4lend autoCollect "1% skim" - owner-trigger vs attacker-trigger outflow measured IDENTICAL; documented keeper bounty -> <=Low.)
2. DOMINANCE TEST (capability claims): is the claimed gain reachable WITHOUT the mechanism? If yes -> KILL. (Receipt: claimed cap over-borrow of 201e18 reachable with ZERO withdrawal -> netting adds nothing.)
3. DOCS-LEDGER SWEEP (design-gap claims): grep docs/, audit-handoff files, AND the fix commit's own messages/comments for documented-by-design intent BEFORE claiming a design gap. (Receipt: 'netting' lines were the team's own accepted V4LE-122/127 fix; its comment defines FIFO flow attribution.)
Log ALL THREE attempts + results in the candidate packet - a candidate without falsification receipts is not a survivor.
