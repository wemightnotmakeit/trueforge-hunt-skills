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

## 15. THE GATE IS STRUCTURAL, NOT A SCORE (operator, 2026-10-16)

The fleet was self-censoring. A hunter whose own confidence felt low filed the lead as a kill to
DEAD.md, where it became invisible; anything between the hunter's floor and the campaigner's bar
was produced and then silently dropped. **Confidence is an uncalibrated self-report and must never
decide whether a candidate is examined at all.**

**The one observed instance, stated precisely** (Ondo/Tempo, `OndoTokenRouter.sol:254-271`,
`minPrice=0` live on chainId 4217): the hunter filed its own report **DRY (0 candidates ≥0.75)**, so
the candidate was never escalated and never examined by the verifier — it surfaced only because a
human read the raw report. **Honest caveat: that same candidate also dies independently on impact**
(the Tempo stack shows ~zero live usage, no USDY balance, FaR ~nil — BOARD.md, receipt-backed). So
this is an example of the gate **hiding a candidate from review**, NOT of a proven lost finding.
Do not claim the gate has cost us a submission until a candidate exists that passes every other
gate and was stopped by the score alone.

**Escalation predicate — mechanical, read off the candidate itself.** A candidate GOES TO THE
VERIFIER if it has all four of the following. This is the ONLY test:

| # | Element | Test |
|---|---|---|
| E1 | LOCUS | a concrete `file:line` at the pinned commit, or a deployed address + function selector |
| E2 | GUARD | the named check/validation the exploit must bypass, quoted from source |
| E3 | FALSIFIABLE CLAIM | the exploit predicts an observable — state the test that passes if true, and reverts/fails if false |
| E4 | IN SCOPE | the asset appears on the program's own list |
| E5 | PRECONDITION LIVENESS | who can create the vulnerable state on the LIVE deployment, with what permission and capital, cited to a live address or tx |

**E1–E4 decide ESCALATION. E5 decides SUBMISSION.** A candidate can pass E1-E4 and be verified
3/3 green in a fork test and still be unpublishable, because a fork test proves the *mechanism*,
not that a real attacker can *reach the state*. `vm.prank` / `vm.store` / hand-arranged fork state
make a green PoC that the program answers with "state not reachable in practice". The verifier
re-running the same harness is independent across EXECUTORS, not across ASSUMPTIONS: neither run
tests reachability on the live deployment. So the packet must state, in its own field, who can
create the precondition live — and if that cannot be cited, the candidate is a mechanism demo,
not a submission. This is necessary, not sufficient: reachability argued in prose is not proof.

Any candidate with E1–E4 is escalated **regardless of any confidence number**. Confidence ranks
the QUEUE (which candidate first). It never grants or denies PERMISSION.

**A KILL REQUIRES A FALSIFICATION RECEIPT.** A kill is legitimate only when it carries at least one
§10 attack WITH its result recorded: the dominance test (the gain is reachable without the
mechanism), the head-to-head delta (attacker and legitimate actor are indistinguishable), or the
docs-ledger sweep (the team documented the behaviour as intended, with the quote). "I could not
see how to exploit it", "confidence too low", "probably by design", an unreadable target, or a
timeout is **NOT a kill** — it is an **UNADJUDICATED candidate** and it returns to the queue.

The mechanical test, applied by the ledger on every build: **does the kill cite ANY artifact?** —
a file:line, an address or tx hash, a `.md`/`.txt`/`.json`/`.diff` artifact, a commit, a PR or
issue number, a job id, or one of the §10 attack names with a result. A kill that cites nothing is
listed under **UNADJUDICATED** in `MEMORY.md`. Saying "probably by design" without the quote is not
citing anything.

**Cold-case pass.** At the start of each wave, re-adjudicate every DEAD.md entry that carries no
falsification receipt against the current pin. The absence of a receipt is the trigger — no list
is kept, because none is needed.

Why this is permanent and target-free: every element is read off the artifact, not off a list or a
number. Nothing here names a protocol, a severity, or a threshold, so it cannot go stale when the
board rotates. The INDEPENDENT VERIFIER, not the generator, is the filter — and it is the only
party whose output may end a candidate.

## 16. TOLERANT PARSING — import fleetlib, do not hand-roll (operator, 2026-10-16)

Measured over 349 "Sandbox code error" hits, classified by the LAST line of the traceback:

| count | failure |
|---|---|
| 75 | `KeyError: 'result'` — assumes the exec envelope always has `result` |
| 28 | `Usage: cast index <KEY_TYPE> <KEY> <SLOT_NUMBER>` — wrong arity |
| 23 | `ValueError: invalid literal for int() with base 16: '0x'` — empty hex parsed as int |
| 12 | `KeyError: slice(None, 800, None)` — `x[:800]` applied to a dict |
| 11 | `KeyError: 'matches'` — assumed key on an API response |
| 9 | `ImportError: cannot import name 'list_tools' from 'mcp_client'` |

Every one is the SAME root cause: ad-hoc code ASSUMES a response shape and dies when the shape
differs, then burns turnaround retrying. A doc that says "do not repeat this" is weaker than a
function that cannot fail — §12 already documented the `list_tools` trap and it still fired 9 times.

`scripts/fleetlib.py` ships with this skill (sandbox path:
`/opt/tfy/skills/hunt-doctrine/scripts/fleetlib.py`).

```python
import sys; sys.path.insert(0, "/opt/tfy/skills/hunt-doctrine/scripts")
from fleetlib import env, jget, to_int, cut, cast_index

code, text, data = env(raw)            # never raises; missing 'result' -> (None, "", None)
items = jget(resp, "items", [])        # missing key -> default, never KeyError
v     = to_int("0x")                   # -> None   (was: ValueError crash)
head  = cut(big, 800)                  # str by chars; dict/list by ITEM COUNT
argv  = ["cast", "index"] + cast_index("address", "0xabc", 3)
```

Rules:
- Never index a tool/API response as `["result"]` / `["items"]` / `["matches"]` — use `env()` and
  `jget()` with an explicit default.
- Never `int(x, 16)` on a value that may be `'0x'`/`''`/`None` — use `to_int`.
- Never slice `x[:800]` unless `x` is known to be a string — use `cut`.
- A `NameError` (e.g. `ph_re`) is a typo in YOUR OWN snippet, not a tooling failure. Re-read the
  snippet before re-running it; do not reinterpret it as an infra problem.
- Self-test with `python3 .../scripts/test_fleetlib.py` if you doubt the helpers.

## 17. THE SEAM GATE — no hunter wave without a proven deploy-vs-repo difference (operator, 2026-10-16)

A hunter wave is the most expensive thing the fleet buys. The measured evidence says waves are
routinely spent on targets that cannot contain a bug: fBTC run21 spent 2 hunters and 15 kills to
discover `Deployed == HEAD` for all 5 in-scope contracts; GMX burned 17 kills and Onyx a full wave
on no-seam targets. The bench rate (3/10 clean hits) is the fleet's own best predictor of this.

**Rule: a hunter wave spawns only when at least one in-scope deployed contract differs from the
repo's HEAD for that contract.** "Differs" means one of:
1. the deployed bytecode is not the compiled HEAD source (self-verify: fetch verified source, compile
   at the declared version, compare runtime bytecode), or
2. the repo shows a fix/PR touching that file that is **not** in the deployed build (a merged-but-
   undeployed fix is the ENS E1 pattern — the proven producer of real findings), or
3. the deployed address has no verified source at all (unknown ≠ safe; it is probe-worthy, not
   wave-worthy, until the interface is known).

If no in-scope contract passes, the target is **PARKED with the receipt** and NO hunters spawn. The
`scout` already gathers exactly this data (impl pointers, `deployed==HEAD` checks, `impl_match`
fields) — the change is to make wave spawn **conditional** on it instead of recording it after the
spend. This is derived, not hardcoded: the predicate reads off the target, never off a name list.

Why this beats more lanes: lane volume multiplies whatever your hit rate already is. A wave on a
no-seam target has an expected yield near zero for full price, so gating it is worth more than N
extra lanes aimed the same way.

**Implemented — CALL IT, do not re-derive it:** `scripts/seam_gate.py` ships with this skill.

```python
import sys; sys.path.insert(0, "/opt/tfy/skills/hunt-doctrine/scripts")
from seam_gate import seam_decision
action, reason, passing = seam_decision(scout_contracts)   # action in {"spawn","block"}
```

`scout_contracts` is ONE dict per in-scope deployed contract:
`{address, name?, in_scope?, has_verified_source?, deployed_match?, repo_fix_undeployed?}`.

- `deployed_match=False` -> bytecode seam. `repo_fix_undeployed=True` -> the ENS E1 seam.
  `has_verified_source=False` -> unknown, which is probe-worthy, NOT safe.
- **Unknown (`None`) is not evidence of a seam.** The gate BLOCKS rather than inventing one, so a
  field you did not check can never manufacture a wave.
- It is indifferent to protocol names — the predicate reads the target's own facts, so it cannot
  go stale when the board rotates.
- It reproduces history: the fBTC configuration (all contracts `deployed_match`) returns **block**;
  the ENS E1 configuration (undeployed fix) returns **spawn**. Self-test:
  `python3 /opt/tfy/skills/hunt-doctrine/scripts/seam_gate.py selftest`.

## 18. PUSHING TO THE SHARED REPO — rebase, retry, NEVER force (operator, 2026-10-16)

`/opt/hunt-state` is ONE repo that MANY writers push: every sandbox at turn end, plus the
operator's sync daemon. Two writers cannot both be latest, so a push can be rejected inside the
window between your pull and your push. Losing that race silently loses your kill rows and
candidate edits — the memory the NEXT run depends on — while your turn still reports success. The
operator's daemon had exactly this bug: a rejected push was only logged, so the commit sat local
forever.

Rule when you push:
1. `git -C /opt/hunt-state pull --rebase --autostash` immediately before `push`.
2. If the push is rejected (non-fast-forward / "fetch first" / "Updates were rejected"), pull
   --rebase again and retry, with bounded attempts and backoff. A rejection is a race you can win.
   A rebase CONFLICT is not — stop and surface it rather than looping.
3. **NEVER `git push --force` / `--force-with-lease` on hunt-state.** A force-push discards
   another writer's kills, which is the exact loss this rule prevents.
4. Do not retry what retrying cannot fix (auth, DNS, no upstream) — report it.

Helper (ships with this skill):
`python3 /opt/tfy/skills/hunt-doctrine/scripts/git_safe.py selftest`, then
```python
import sys; sys.path.insert(0, "/opt/tfy/skills/hunt-doctrine/scripts")
from git_safe import sync_push
ok, why = sync_push("/opt/hunt-state", message="STATE: <campaign> turn end")
```

## 19. CHECK BEFORE YOU SPAWN — a re-issued worker is duplicate spend (operator, 2026-10-17)

Measured: in ONE run `redteam-lombard-c1` was spawned **24 times** and returned the same verdict
24 times; all-time the feed shows 187 spawns for 129 distinct workers, i.e. **58 duplicate
issues**. Each duplicate burns the single sandbox slot on work that was already done, and floods
the ledger with identical rows. Doctrine already called this a "re-spawn storm" — a warning did
not prevent it, so now there is a check.

Before spawning ANY worker:
```
python3 /opt/tfy/skills/hunt-doctrine/scripts/spawn_guard.py \
    --worker <name> --feed /opt/hunt-state/automation/feed.jsonl
```
It prints `{"action": "allow"|"block", "reason": ...}`. On **block, do not spawn** — the worker
is either still in flight, or has already returned its verdict for this run. On allow, proceed.

A worker MAY legitimately be re-spawned in a LATER run: the window is sized to one run and is
shorter than the 2h cadence. The guard is deliberately time-windowed rather than run-id-keyed
because the feed has no reliable run-start marker, and the window is a parameter so it can be
retuned if the cadence changes. Self-test: `python3 .../scripts/spawn_guard.py selftest`.

## 20. ROUTE THE MCP CALLS — never ride the NATS bridge from `exec` (operator, 2026-10-17)

There are two ways to call an MCP tool. Only one of them is reliable, and it is the one that does
NOT go near NATS:

- **Native tools — the reliable path.** Call `list_tools` / `get_tool_info` / `call_tool` as
  **native tool calls**. They do not need the sandbox and do not ride NATS.
- **Sandbox code-mode MCP — the fragile path.** `from mcp_client import call_tool` (ASYNC) inside
  `exec`, or `python mcp_client.py call-tool <server> <tool> '<json>'`. **This is the only path
  that rides the NATS bridge**, and the bridge fails with
  `NATS bridge setup failed; NATS bridge is required for MCP from Code Mode.`

**Measured (2026-10-17):** 233 recorded NATS-bridge failures, and the counts are rising —
18 · 61 · 14 · 23 · **35 on the most recent day**, the highest yet. The failures cluster in runs
that used code-mode MCP; runs that stayed on native tools did not hit it at all.

Rule: **do not call MCP from inside `exec`.** Use native tool calls. If you think you need a loop
or a conditional over MCP calls, batch native calls instead, or do the loop over data you already
have — a turn spent on a failed code-mode call costs more than the batching saves.

Diagnosis: `python3 /opt/tfy/skills/hunt-doctrine/scripts/nats_probe.py` (measures how much the
recorded runs depended on the fragile path). The companion `--plan` documents the N-sandbox load
measurement, which is only worth running if you decide you want code-mode available at scale.


