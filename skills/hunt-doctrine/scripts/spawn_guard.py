#!/usr/bin/env python3
"""spawn_guard — stop the orchestrator re-issuing a worker it already ran.

THE MEASURED BUG (2026-10-17 run): `redteam-lombard-c1` was spawned TWENTY-THREE times and
returned the SAME verdict 23 times. The campaigner re-issued one worker over and over, burning
the single sandbox slot on duplicate work and flooding the ledger with identical rows. Doctrine
already warns about this as a re-spawn storm, but a warning is not a gate: nothing checked
before issuing.

WHY A TIME WINDOW AND NOT A RUN ID. The feed has no reliable "run start" marker, and a worker
MAY legitimately be re-spawned in a LATER run. Runs fire on a 2h cadence and a single run
finishes well inside it, so "spawned within the last WINDOW_MIN minutes" cleanly means "already
run in this run" and a re-spawn in the next run falls outside it. The window is a parameter,
not a magic constant, and the reasoning is stated so it can be retuned if the cadence changes.

CLI (what the orchestrator calls before spawning):
    python3 spawn_guard.py --worker redteam-lombard-c1 \
        --feed /opt/hunt-state/automation/feed.jsonl
    -> {"action":"block"|"allow","reason":"..."}

    python3 spawn_guard.py selftest   -> exit 0 = semantics correct
"""
import json
import re
import sys
import time

WINDOW_MIN = 100.0          # > any single run segment; < the 2h cron cadence


def _parse_ts(s):
    """'2026-10-17T01:30:12' (feed uses naive UTC) -> epoch seconds, or None."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return time.mktime(time.strptime(s[:len(fmt) + 2].rstrip("Z"), fmt.rstrip("Z")))\
                - time.timezone
        except Exception:
            pass
    try:                                   # last resort: trim to seconds and retry
        return time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
    except Exception:
        return None


# A RETRY IS THE SAME WORKER UNDER A NEW NAME. Measured 2026-10-17: a run errored and the fleet
# re-issued it as `-r24b`, so a name-EXACT guard saw a brand-new worker and allowed the re-spawn.
# Retry suffixes must be stripped before identity is compared. Only RETRY markers are stripped --
# `-c1`, `-H4`, `-r3` inside a campaign id are part of the name, not a retry counter.
_RETRY_SUFFIX = re.compile(r"-(?:r\d+[a-z]?|b\d*)$", re.I)

def normalize_worker(name):
    """'hunter-blue-seamdiff-r24b' -> 'hunter-blue-seamdiff'; unchanged when no retry suffix."""
    n = (name or "").strip()
    prev = None
    while prev != n:
        prev = n
        n = _RETRY_SUFFIX.sub("", n)
    return n


def spawn_verdict(worker, events, window_min=WINDOW_MIN, now=None):
    """Return (action, reason, detail). action in {"allow","block"}.

    events: feed records (dicts) with `ts`, `kind` ("spawn"/"verdict"), `title`.
    Identity is compared on the NORMALIZED name, so a retry under a new suffix is the same worker.
    """
    now = now if now is not None else time.time()
    cutoff = now - window_min * 60.0
    target = normalize_worker(worker)
    mine = []
    for e in events or []:
        if normalize_worker(e.get("title") or "") != target:
            continue
        t = _parse_ts(e.get("ts") or "")
        if t is None or t < cutoff:
            continue
        mine.append(e)

    if not mine:
        return "allow", "no spawn of %s in the last %.0f min" % (worker, window_min), {}

    spawns = [e for e in mine if e.get("kind") == "spawn"]
    verdicts = [e for e in mine if e.get("kind") == "verdict"]
    detail = {"spawns": len(spawns), "verdicts": len(verdicts)}

    if verdicts:
        return ("block",
                "%s already ran and returned %d verdict(s) in this run - do not re-issue"
                % (worker, len(verdicts)), detail)
    if spawns:
        return ("block",
                "%s is already in flight (%d spawn(s), no verdict yet) - wait, do not re-issue"
                % (worker, len(spawns)), detail)
    return "allow", "%s has other activity but no spawn in this run" % worker, detail


def _selftest():
    import datetime as _dt
    p = f = 0

    def ck(name, cond, detail=""):
        nonlocal p, f
        if cond:
            p += 1; print("  PASS  %s" % name)
        else:
            f += 1; print("  FAIL  %s   %s" % (name, detail))

    NOW = 1_800_000_000.0

    def ts(min_ago):
        return _dt.datetime.utcfromtimestamp(NOW - min_ago * 60).strftime("%Y-%m-%dT%H:%M:%S")

    def ev(kind, worker, min_ago):
        return {"kind": kind, "title": worker, "ts": ts(min_ago)}

    W = "redteam-lombard-c1"

    # --- clean slate allows -----------------------------------------------------
    ck("no history -> allow", spawn_verdict(W, [], now=NOW)[0] == "allow")

    # --- in flight: one spawn, no verdict -> block -------------------------------
    r = spawn_verdict(W, [ev("spawn", W, 5)], now=NOW)
    ck("already in flight -> block", r[0] == "block", r)
    ck("reason says in flight", "in flight" in r[1], r[1])

    # --- already done: verdict present -> block ---------------------------------
    r = spawn_verdict(W, [ev("spawn", W, 20), ev("verdict", W, 18)], now=NOW)
    ck("already verdicted -> block", r[0] == "block", r)
    ck("reason says already ran", "already ran" in r[1], r[1])

    # --- THE MEASURED STORM: 23 spawns -> still exactly one block ---------------
    storm = [ev("spawn", W, 18) for _ in range(23)] + [ev("verdict", W, 16) for _ in range(23)]
    r = spawn_verdict(W, storm, now=NOW)
    ck("23x storm -> block", r[0] == "block", r)
    ck("storm counts are reported", r[2].get("spawns") == 23 and r[2].get("verdicts") == 23, r[2])

    # --- a LATER run may re-spawn (outside the window) --------------------------
    r = spawn_verdict(W, [ev("spawn", W, 130), ev("verdict", W, 128)], now=NOW)
    ck("previous run (outside window) -> allow", r[0] == "allow", r)

    # --- boundary: just inside the window blocks, just outside allows -----------
    ck("just inside window -> block", spawn_verdict(W, [ev("spawn", W, 95)], now=NOW)[0] == "block")
    ck("just outside window -> allow", spawn_verdict(W, [ev("spawn", W, 105)], now=NOW)[0] == "allow")

    # --- another worker is unaffected -------------------------------------------
    r = spawn_verdict("hunter-other", [ev("spawn", W, 5)], now=NOW)
    ck("different worker unaffected", r[0] == "allow", r)

    # --- window is a parameter, not a constant ----------------------------------
    ck("window is tunable",
       spawn_verdict(W, [ev("spawn", W, 130)], window_min=200, now=NOW)[0] == "block")

    # --- a verdict with no spawn still blocks (worker clearly ran) --------------
    ck("verdict-only -> block", spawn_verdict(W, [ev("verdict", W, 3)], now=NOW)[0] == "block")

    # --- MEASURED 2026-10-17: a retry under a new suffix must be the SAME worker ---------
    ck("normalize strips -r24", normalize_worker("scout-blue-manifest-r24") == "scout-blue-manifest")
    ck("normalize strips -r24b", normalize_worker("hunter-blue-seamdiff-r24b") == "hunter-blue-seamdiff")
    ck("normalize strips -b", normalize_worker("hunter-x-b") == "hunter-x")
    ck("normalize leaves campaign ids alone (redteam-lombard-c1)",
       normalize_worker("redteam-lombard-c1") == "redteam-lombard-c1")
    ck("normalize leaves seat ids alone (hunter-H4-economic)",
       normalize_worker("hunter-H4-economic") == "hunter-H4-economic")
    ck("normalize leaves plain names alone", normalize_worker("hunter-gmx-logic") == "hunter-gmx-logic")
    r = spawn_verdict("scout-blue-manifest-r24b", [ev("spawn", "scout-blue-manifest-r24", 5)], now=NOW)
    ck("retry under a new suffix -> BLOCK (was allowed)", r[0] == "block", r)
    r = spawn_verdict("hunter-blue-seamdiff-r24b",
                      [ev("spawn", "hunter-blue-seamdiff-r24", 5), ev("report", "hunter-blue-seamdiff-r24", 4)],
                      now=NOW)
    ck("errored run re-issued as -b -> BLOCK", r[0] == "block", r)

    print("\n=== %d PASS / %d FAIL ===" % (p, f))
    return 1 if f else 0


def _load(path):
    out = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        pass
    except Exception:
        pass
    return out


if __name__ == "__main__":
    if "selftest" in sys.argv:
        sys.exit(_selftest())
    if "--worker" in sys.argv:
        w = sys.argv[sys.argv.index("--worker") + 1]
        feed = "/opt/hunt-state/automation/feed.jsonl"
        if "--feed" in sys.argv:
            feed = sys.argv[sys.argv.index("--feed") + 1]
        action, reason, detail = spawn_verdict(w, _load(feed))
        print(json.dumps({"action": action, "reason": reason, "detail": detail}, indent=2))
        sys.exit(0)
    print(__doc__)
