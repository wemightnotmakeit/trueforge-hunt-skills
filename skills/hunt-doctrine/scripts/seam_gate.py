#!/usr/bin/env python3
"""seam_gate — should we spend a hunter wave on this target?

DOCTRINE SECTION 17, AS CODE. A hunter wave is the most expensive thing the fleet buys, and
the ledger shows waves routinely spent on targets that cannot contain a bug: fBTC run21 spent
2 hunters + 15 kills to discover `Deployed == HEAD` for all 5 in-scope contracts; GMX burned
17 kills and Onyx a full wave on no-seam targets.

The rule: spawn a wave ONLY when at least one IN-SCOPE deployed contract differs from the
repo, in one of three ways. Otherwise PARK the target with the receipt and spend nothing.

This is DERIVED, never hardcoded: it reads the target's own scout facts (bytecode match, an
undeployed fix, or missing verified source). No protocol name, severity or allow-list exists
in this file, so it cannot go stale when the board rotates.

CLI (what the orchestrator calls):
    python3 seam_gate.py --json '[{"address":"0x..","deployed_match":true}, ...]'
    -> {"action":"block"|"spawn","reason":"...","passing":[...]}

    python3 seam_gate.py selftest   -> exit 0 = semantics correct
"""
import json
import sys


def seam_decision(contracts):
    """Decide whether a hunter wave may spawn.

    contracts: list of dicts, each describing ONE in-scope deployed contract:
        address            (str)  the deployed address (for the receipt)
        name               (str)  optional label
        in_scope           (bool) default True; out-of-scope contracts are ignored
        has_verified_source(bool|None) False => no verified source at all
        deployed_match     (bool|None) True => deployed bytecode == compiled repo HEAD
        repo_fix_undeployed(bool|None) True => repo has a fix/PR for this file NOT deployed

    Returns (action, reason, passing) with action in {"spawn","block"}.
    """
    contracts = contracts or []
    passing = []
    considered = 0
    for c in contracts:
        if c.get("in_scope") is False:
            continue
        considered += 1
        why = None
        # (c) UNKNOWN source is probe-worthy, not safe: you cannot rule a contract out by
        #     failing to look at it. Expressed as has_verified_source explicitly False.
        if c.get("has_verified_source") is False:
            why = "no verified source (unknown != safe: probe it)"
        # (b) a merged-but-UNDEPLOYED fix is the ENS E1 pattern — the proven producer of
        #     real findings (fix exists in repo, live build predates it).
        elif c.get("repo_fix_undeployed") is True:
            why = "repo fix not present in the deployed build (undeployed-fix seam)"
        # (a) deployed bytecode differs from compiled HEAD source.
        elif c.get("deployed_match") is False:
            why = "deployed bytecode != compiled repo HEAD (bytecode seam)"
        if why:
            passing.append({"address": c.get("address"), "name": c.get("name"), "why": why})

    if not considered:
        return "block", "no in-scope contracts were probed - nothing to justify a wave", passing
    if passing:
        return "spawn", "%d/%d in-scope contract(s) show a seam" % (len(passing), considered), passing
    return "block", ("all %d in-scope contract(s) are deployed==HEAD with no undeployed fix "
                     "- PARK with the receipt, do not spend hunters" % considered), passing


def _selftest():
    p = f = 0

    def ck(name, cond, detail=""):
        nonlocal p, f
        if cond:
            p += 1; print("  PASS  %s" % name)
        else:
            f += 1; print("  FAIL  %s   %s" % (name, detail))

    # --- the waste case: deployed == HEAD everywhere -> BLOCK -------------------
    r = seam_decision([{"address": "0xA", "deployed_match": True},
                       {"address": "0xB", "deployed_match": True}])
    ck("all deployed==HEAD -> block", r[0] == "block", r)
    ck("block reason names PARK", "PARK" in r[1], r[1])

    # --- bytecode seam -> SPAWN -------------------------------------------------
    r = seam_decision([{"address": "0xA", "deployed_match": True},
                       {"address": "0xB", "deployed_match": False}])
    ck("one bytecode seam -> spawn", r[0] == "spawn", r)
    ck("spawn reason counts passing", "1/2" in r[1], r[1])
    ck("passing names the address", r[2][0]["address"] == "0xB", r[2])

    # --- the ENS E1 pattern: undeployed fix -------------------------------------
    r = seam_decision([{"address": "0xA", "deployed_match": True,
                        "repo_fix_undeployed": True}])
    ck("undeployed fix -> spawn (the E1 pattern)", r[0] == "spawn", r)
    ck("reason identifies undeployed-fix seam", "undeployed-fix" in r[2][0]["why"], r[2])

    # --- unknown source is probe-worthy, not safe -------------------------------
    r = seam_decision([{"address": "0xA", "has_verified_source": False}])
    ck("no verified source -> spawn (unknown != safe)", r[0] == "spawn", r)

    # --- None means UNKNOWN, and unknown alone must NOT fabricate a seam --------
    # (a field we did not check is not evidence of a difference)
    r = seam_decision([{"address": "0xA", "deployed_match": None, "has_verified_source": None}])
    ck("all-unknown -> block (no invented seam)", r[0] == "block", r)

    # --- out-of-scope contracts cannot justify a wave ---------------------------
    r = seam_decision([{"address": "0xOUT", "in_scope": False, "deployed_match": False}])
    ck("out-of-scope seam does not justify a wave", r[0] == "block", r)

    # --- empty input must not spawn ---------------------------------------------
    ck("no contracts -> block", seam_decision([])[0] == "block")
    ck("None contracts -> block", seam_decision(None)[0] == "block")

    # --- the gate must be indifferent to names (no hardcoded targets) -----------
    a = seam_decision([{"address": "0xA", "name": "ENS", "deployed_match": False}])
    b = seam_decision([{"address": "0xA", "name": "SomeOtherProtocol", "deployed_match": False}])
    ck("decision ignores the protocol name", a[0] == b[0] == "spawn")

    print("\n=== %d PASS / %d FAIL ===" % (p, f))
    return 1 if f else 0


if __name__ == "__main__":
    if "selftest" in sys.argv:
        sys.exit(_selftest())
    if "--json" in sys.argv:
        payload = sys.argv[sys.argv.index("--json") + 1]
        action, reason, passing = seam_decision(json.loads(payload))
        print(json.dumps({"action": action, "reason": reason, "passing": passing}, indent=2))
        sys.exit(0)
    print(__doc__)
