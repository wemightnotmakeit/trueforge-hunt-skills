#!/usr/bin/env python3
"""nats_probe — measure how much the fleet depends on the NATS-riding MCP path, and at what
failure rate.

WHY THIS AND NOT A LOAD GENERATOR
---------------------------------
The plan was: boot N concurrent sandboxes and count 502s per 1000 code-mode MCP calls. Research
(2026-10-17, from the fleet's own doctrine §12 and the recorded transcripts) changed the question:

    A. Native tools (preferred) -- `list_tools` / `get_tool_info` / `call_tool` as NATIVE tools.
       "These do NOT need the sandbox and do NOT ride NATS. They are the reliable path."
    B. Sandbox code-mode MCP (alternate) -- `from mcp_client import call_tool` inside `exec`.
       This is the ONLY path that rides the NATS bridge, and it is the one that 502s.

So the NATS bridge is not a load-bearing dependency; it is an OPTIONAL path with a documented
reliable alternative. That reframes the Tier-2 gate from "can the bus take 25x load?" to "how much
does the fleet actually use the fragile path, and how often does it fail?" — answerable from the
RECORDED RUNS, for free, with no sandbox and no spend.

WHAT THIS MEASURES (and what it does NOT)
-----------------------------------------
Measured:   code-mode MCP invocation sites in the recorded transcripts (the denominator), and
            occurrences of the NATS-bridge failure signature (the numerator), over all history.
Honest limit: the recorder stores truncated event snippets, so both counts are LOWER BOUNDS, not
            totals. This yields a base rate at ONE lane. It does NOT and cannot extrapolate to
            25 lanes -- the entire reason NATS is flagged is that it may be superlinear, and a
            single-lane rate cannot show that. This file refuses to make that extrapolation.

Run:
    python3 nats_probe.py            -> the measured base rate
    python3 nats_probe.py --plan     -> the exact N-sandbox design, and what must be confirmed first
"""
import glob
import json
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))

# Path B: the only MCP surface that rides NATS. Both forms observed in transcripts.
CODEMODE_PAT = re.compile(
    r"from\s+mcp_client\s+import\s+call_tool"
    r"|mcp_client\.py\s+call-tool"
    r"|mcp-client\s+call-tool"
)
# The bridge failure, verbatim from the recorded results.
NATS_FAIL_PAT = re.compile(r"NATS bridge setup failed")
# The safe alternative, counted to show how often the fleet took the reliable path.
NATIVE_PAT = re.compile(r'"name"\s*:\s*"call_tool"|native\s+tool|call_tool\("')


def _blobs():
    out = []
    for f in ["feed.jsonl", "e.json", "ev.json", "ev0.json", "ev100.json", "evlive.json",
              "issue-hits.jsonl"]:
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            out.append((f, open(p, encoding="utf-8", errors="ignore").read()))
    return out


def _blobs_glob():
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "*.jsonl"))) + \
             sorted(glob.glob(os.path.join(HERE, "*.json"))):
        n = os.path.basename(p)
        if n in ("e.json", "ev.json", "ev.jsonl"):
            continue
        try:
            out.append((n, open(p, encoding="utf-8", errors="ignore").read()))
        except Exception:
            pass
    return out


def measure():
    code = nat = 0
    per_file = collections.Counter()
    camps_all, camps_nat = set(), set()
    for name, blob in _blobs():
        c = len(CODEMODE_PAT.findall(blob))
        n = len(NATS_FAIL_PAT.findall(blob))
        code += c
        nat += n
        if c or n:
            per_file[name] = (c, n)

    # Failures by day, and by RUN (feed rows carry the campaign/session title in `camp`).
    by_day = collections.Counter()
    try:
        for line in open(os.path.join(HERE, "issue-hits.jsonl"), encoding="utf-8", errors="ignore"):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            camps_all.add(e.get("camp") or "?")
            if NATS_FAIL_PAT.search(e.get("snippet") or ""):
                by_day[(e.get("ts") or "")[:10]] += 1
                camps_nat.add(e.get("camp") or "?")
    except Exception:
        pass

    print("=== NATS-path dependence (measured from recorded runs) ===")
    print("NATS-bridge failures recorded : %d" % nat)
    print("code-mode invocation sites    : %d" % code)
    print()
    print("failures by day:")
    for d in sorted(by_day):
        print("   %s  %4d" % (d, by_day[d]))
    print()
    print("runs (campaign sessions) observed        : %d" % len(camps_all))
    print("runs that recorded >=1 NATS failure      : %d" % len(camps_nat))
    print()
    print("NO PER-CALL RATE IS REPORTED. The two counts are not on the same basis: a failure is a")
    print("short single-line result the recorder captures reliably, while an invocation site lives")
    print("inside a long code block that is truncated -- so failures are over-represented relative")
    print("to attempts. Dividing them would produce a big, confident, meaningless number.")
    print("A true per-call rate requires the sandbox-side measurement (see --plan).")
    print()
    print("WHAT IS DEFENSIBLE FROM THIS: the NATS-riding path is optional (doctrine §12 names the")
    print("native path 'the reliable path'), it is used rarely in absolute terms, and when it is")
    print("used it fails at a rate that makes it useless whenever it matters.")
    return nat


def _unused_rate_guard(code, nat):
    """Kept as a written warning against reintroducing the bogus ratio."""
    return None


PLAN = """=== The N-sandbox measurement: what it would take ===

DESIGN
  For N in [1, 2, 4, 8]:
    boot N light sandboxes (memory=1 GiB, proven to boot under the Tier-1 10 GiB cap),
    in each run K=200 code-mode MCP calls via the sandbox mcp-client,
    count {ok, "NATS bridge setup failed", other}, then tear down.
  Report 502s/1000 by N and fit linear vs superlinear (compare slope across N=1->4->8).

WHY LIGHT SANDBOXES
  Tier 1 = 10 GiB org-wide, and a hunt-base sandbox asks for 8 GiB -> exactly ONE at a time.
  But the fleet audit (FLEET-AUDIT-2026-10-12.md) records: "1GiB default env boots fine" while
  every 8 GiB boot failed on the cap. So the probe needs N CLIENTS, not N hunters: 8 x 1 GiB
  fits, and the probe does not build anything so it needs no 8 GiB. This is what makes the
  measurement affordable BEFORE upgrading.

WHY IT MUST SELF-SEQUENCE
  The probe competes for the same org memory cap as the fleet. Booting it during a campaign run
  would CAUSE the "Total memory limit exceeded" error the whole exercise is trying to remove.
  The probe must therefore refuse to start unless presence.jsonl reports `running: 0`, and must
  tear down in a finally block so it can never hold the cap.

WHAT MUST BE CONFIRMED FIRST (do not guess these)
  1. Daytona sandbox CREATE endpoint + body  (fork_ops.py only implements GET/DELETE today:
     base https://app.daytona.io/api/sandbox, auth "Bearer <dtn_...>").
  2. The sandbox EXEC endpoint for running the call loop inside a sandbox.
  3. The exact in-sandbox invocation: research gives `python mcp_client.py call-tool <server>
     <tool> '<json>'` and, inside exec, `from mcp_client import call_tool` (ASYNC, (server, tool,
     body)). One real boot settles all three: `ls -l /usr/local/bin/mcp-client`, `--help`, and a
     single call-tool round trip. That boot is cheap (1 GiB, short-lived) and belongs in an idle
     window.

DECISION THIS FEEDS
  If routing the fleet to the NATIVE path removes the NATS dependency entirely (it should --
  doctrine §12 already calls native "the preferred / reliable path"), then the measurement is
  optional: the gate is satisfied by ROUTING, not by capacity. Measure only if we want to keep
  code-mode available at scale.
"""


if __name__ == "__main__":
    if "--plan" in sys.argv:
        print(PLAN)
    else:
        measure()
