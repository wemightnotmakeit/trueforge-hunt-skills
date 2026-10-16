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

**A FAILED COMMAND IS NOT EVIDENCE OF ABSENCE (measured failure).** `git log <parent>..HEAD -- <files>`
returning nothing is only meaningful if the clone SUCCEEDED and the command actually RAN. A flaky
clone (`fatal: early EOF`) or a command in a non-repo prints nothing / errors, and reporting that as
"seam width is zero" is a **false zero** — the worst output you can produce, because it looks like
rigorous work and it is filed as a kill. A real CEI reentrancy fix was missed exactly this way.
Before ANY negative claim: confirm the clone landed (`git rev-parse HEAD`), confirm the file exists at
that path (`git log --oneline -1 -- <file>`), and only then conclude. If the clone failed, that is a
TOOLING failure to report and route around (`local_worker`), never a narrow seam.

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

## 11. Fork-ops + scheduled runs (live 2026-10-13)
- **fork-ops** = MCP tool `fork_run` / `fork_status` / `fork_jobs` — executes forge tests on the operator
  PC (unrestricted network). Sandbox blocked (RPC, solc gap, compile fail)? Route the proof through
  fork-ops; its raw output is valid evidence (same bar: no output, no finding).
- **Scheduled campaigns**: the fleet runs under a TrueForge schedule ("auto-campaign"). Every scheduled
  run MUST end around minute 50 with: state synced (BOARD/DEAD/STATE + hunt-state push), kills recorded,
  and a loud report of any survivor. The next scheduled run resumes from your artifacts — leave nothing
  only in your head.

## 12. Tool surface & MCP API (read BEFORE your first tool call)
There are TWO different tool surfaces. Confusing them burns your turn wall and returns NOTHING.

**A. Native tools (preferred — no sandbox, no import).** Call these directly as tools:
- `list_tools` — discover tools on a server: `{"mcp_server": "<name>"}`
- `get_tool_info` — inspect one tool's schema
- `call_tool` — invoke it
These do NOT need the sandbox and do NOT ride NATS. They are the reliable path.

**B. Sandbox code-mode MCP (alternate — rides NATS).** Inside `exec`, in Python:
```python
from mcp_client import call_tool          # ASYNC
result = await call_tool("<server>", "<tool>", { ... })   # (server, tool, body)
```
CLI form: `python mcp_client.py call-tool <server> <tool> '<json>'`

**The two errors that keep killing runs — do not repeat them:**
- `from mcp_client import call_tool, list_tools` -> **ImportError**. `mcp_client` has NO `list_tools` symbol. Only `call_tool`.
- `python mcp_client.py list-tools ...` -> **argparse error**. `call-tool` is the ONLY subcommand.

If you need to DISCOVER tools, use the native `list_tools` tool. Never try to list tools through `mcp_client`.

**Failure budget (hard rule).** If a tool call fails TWICE, stop and switch surface (sandbox <-> native
<-> fork-ops). Record the failure in STATE.md and continue. Burning all 8 turns retrying one broken
import produces zero output and looks, from the outside, exactly like laziness. It is not: it is a
tooling dead end, and the fix is to route around it and say so.

## 13. The local bridge (sandbox egress is NOT your limit)
The sandbox is network-restricted, but there is an **unrestricted machine behind it**. Use it
instead of giving up on a blocked fetch:

- **`local_worker`** (fork-ops MCP) — spawns the LOCAL agent on the operator PC with the FULL
  toolset and **unrestricted network**. Use it for: fetching a URL the sandbox cannot reach
  (Cloudflare/bot-wall/timeout), pulling a blocked resource, or any multi-step local operation.
  `{"task": "<precise instruction>"}` -> job_id -> poll `fork_status`.
- **`fork_run`** (fork-ops MCP) — runs a Foundry test suite on the operator PC: unrestricted RPC,
  local foundry, any solc version. Use it when the sandbox cannot compile, lacks solc, or cannot
  reach the RPC. Its raw output is valid evidence (same bar: no output, no finding).
- **`cleanup_sandboxes`** — call it if you are blocked by "Total memory limit exceeded" (the org
  cap is 10 GiB and one sandbox is 8 GiB, so exactly ONE sandbox agent runs at a time; a leaked
  sandbox from a previous run will block you).

**If a fetch fails in the sandbox, the answer is `local_worker`, not "source unavailable".**
Saying "the source is behind Cloudflare so I could not proceed" is a self-inflicted dead end.

## 14. READ-FIRST / WRITE-LAST (memory across runs)

You wake as a **fresh session every run**. You have no memory of the last one. The fleet's
memory therefore does not live in you — it lives in files you must read before you think and
write before you stop. This is not optional and not target-specific.

**On boot, before scoring anything, you MUST read:**
1. `/opt/hunt-state/MEMORY.md` — the generated read-first contract: where we stand, the
   **DO-NOT-RE-DERIVE** list of killed mechanisms (with kill dates), and the
   **ALREADY-PAID-FOR-TWICE** list.
2. `/opt/hunt-state/LEDGER.md` — the full ledger (candidates, kills, reasons).
3. `/opt/hunt-state/DEAD.md` and `CANDIDATES.md` — the raw sources the ledger is built from.

**Rules that follow from it:**
- Nothing under **DO-NOT-RE-DERIVE** may be re-derived *unless the code changed since its kill
  date*. Re-deriving a kill is the single most expensive mistake this fleet makes — it costs a
  whole sandbox wave and produces nothing new.
- Nothing under **ALREADY-PAID-FOR-TWICE** may be hunted again, at all.
- A candidate or a kill that is **not written down did not happen**. Write it the moment a hunter
  returns — before the sandbox can die mid-run. Deferring ledger writes loses candidates.
- Record **what bug, named by mechanism** — not *who looked*. A row says
  "IRMLinearKink does not bound kink_", never "hunter-euler-h3".

`MEMORY.md` is **generated** from `DEAD.md` / `CANDIDATES.md` / `FINDINGS.md` — never hand-edit
it. Keep those three truthful and the memory maintains itself.


