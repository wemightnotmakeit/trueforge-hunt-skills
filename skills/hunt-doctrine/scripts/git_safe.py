#!/usr/bin/env python3
"""git_safe — push to a repo that MULTIPLE writers share, without losing commits.

THE BUG THIS FIXES. hunt_sync's git_sync already does `pull --rebase --autostash` before
`push`, which is correct as far as it goes. But a rejected push was only LOGGED:

    p = subprocess.run([... "push" ...])
    if p.returncode == 0: log("git sync pushed")
    else:                 log(f"git push FAILED ...")      # <- commit stays unpublished

Between the pull and the push there is a window. Any other writer pushing inside that window
wins, our push is rejected non-fast-forward, and the commit sits local forever. With one
writer that window is almost never hit; with N sandboxes all pushing hunt-state (the doctrine
tells agents to push at turn end) it is hit routinely -- and the things lost are kill records
and candidate rows, i.e. exactly the memory the next run depends on.

THE FIX. Re-enter the pull-rebase-push loop on a REJECTION (a race we can win by retrying),
with bounded attempts and exponential backoff. Do not retry errors retrying cannot fix
(auth, network, no upstream) -- that just burns the window. NEVER force-push: a force-push
here would discard another writer's kills, which is the failure this function exists to prevent.

Self-test with a real bare repo + two clones: `python3 git_safe.py selftest`
"""
import subprocess
import sys
import time

REJECT_MARKERS = ("non-fast-forward", "fetch first", "rejected", "failed to push",
                  "Updates were rejected", "behind its remote")


def _git(repo, args, timeout=180):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, timeout=timeout)


def is_rejection(stderr):
    """True when the push failed because another writer got there first (retryable)."""
    s = (stderr or "").lower()
    return any(m.lower() in s for m in REJECT_MARKERS)


def sync_push(repo, message=None, attempts=5, base_delay=1.0, sleep=time.sleep, log=None):
    """Pull-rebase then push, retrying ONLY on a rejection.

    Returns (ok, detail). If `message` is given, any staged/working changes are committed
    first (idempotent: a clean tree is fine).
    """
    say = log or (lambda s: None)
    for i in range(1, attempts + 1):
        # 1. rebase onto whatever other writers published while we were working
        pl = _git(repo, ["pull", "--rebase", "--autostash"])
        if pl.returncode != 0:
            err = (pl.stderr or pl.stdout or "").strip()[:200]
            # a rebase CONFLICT is not a race we can retry away -- surface it loudly
            if "conflict" in err.lower() or "could not apply" in err.lower():
                return False, "rebase conflict (needs a human): %s" % err
            say("pull failed (retry): %s" % err)
            if i == attempts:
                return False, "pull failed: %s" % err
            sleep(base_delay * (2 ** (i - 1)))
            continue

        # 2. commit our work (no-op when clean)
        if message:
            _git(repo, ["add", "-A"])
            c = _git(repo, ["commit", "-m", message])
            if c.returncode != 0 and "nothing to commit" not in (c.stdout + c.stderr).lower():
                say("commit note: %s" % (c.stdout or c.stderr).strip()[:120])

        # 3. push
        p = _git(repo, ["push"])
        if p.returncode == 0:
            return True, "pushed on attempt %d" % i
        err = (p.stderr or p.stdout or "").strip()[:200]
        if not is_rejection(p.stderr):
            return False, "push failed (not a race, not retrying): %s" % err
        say("push rejected by another writer (attempt %d/%d) -- rebasing and retrying"
            % (i, attempts))
        if i < attempts:
            sleep(base_delay * (2 ** (i - 1)))
    return False, "exhausted %d attempts (a writer is pushing faster than we can retry)" % attempts


def _selftest():
    import os
    import shutil
    import tempfile
    p = f = 0

    def ck(name, cond, detail=""):
        nonlocal p, f
        if cond:
            p += 1; print("  PASS  %s" % name)
        else:
            f += 1; print("  FAIL  %s   %s" % (name, detail))

    d = tempfile.mkdtemp(prefix="gitsafe_")
    try:
        origin = os.path.join(d, "origin.git")
        subprocess.run(["git", "init", "--bare", "-b", "main", origin],
                       capture_output=True, text=True)
        a = os.path.join(d, "A"); b = os.path.join(d, "B")
        for w in (a, b):
            subprocess.run(["git", "clone", origin, w], capture_output=True, text=True)
            for kv in (("user.email", "t@t"), ("user.name", "t")):
                _git(w, ["config", kv[0], kv[1]])
        _git(a, ["commit", "--allow-empty", "-m", "init"])
        _git(a, ["push", "-u", "origin", "main"])

        # --- is_rejection classification (both directions) ----------------------
        ck("non-fast-forward is a rejection",
           is_rejection("! [rejected] main -> main (non-fast-forward)"))
        ck("fetch first is a rejection", is_rejection("error: failed to push some refs"))
        ck("auth error is NOT a rejection",
           not is_rejection("fatal: Authentication failed for 'https://x'"))
        ck("network error is NOT a rejection",
           not is_rejection("fatal: unable to access: Could not resolve host"))

        # --- the actual race: A and B both commit, both push --------------------
        open(os.path.join(a, "a.txt"), "w").write("from A")
        open(os.path.join(b, "b.txt"), "w").write("from B")
        # B first (fast-forward), so A's push WILL be rejected
        okB, dB = sync_push(b, message="B work", sleep=lambda s: None)
        okA, dA = sync_push(a, message="A work", sleep=lambda s: None,
                            log=lambda s: print("    [A]", s))
        ck("B pushed", okB, dB)
        ck("A pushed despite being behind (the race)", okA, dA)

        # --- nothing lost: BOTH writers' files are in origin --------------------
        chk = os.path.join(d, "chk")
        subprocess.run(["git", "clone", origin, chk], capture_output=True, text=True)
        names = sorted(os.listdir(chk))
        ck("A's file survived (no writer was clobbered)", "a.txt" in names, names)
        ck("B's file survived", "b.txt" in names, names)
        ck("history is linear (no merge commit, no force-push)",
           _git(chk, ["rev-list", "--count", "main"]).stdout.strip() == "3",
           _git(chk, ["rev-list", "--count", "main"]).stdout.strip())

        # --- clean tree is a no-op, not an error --------------------------------
        okC, dC = sync_push(a, message="nothing new", sleep=lambda s: None)
        ck("clean tree push succeeds", okC, dC)

        # --- a non-race failure stops immediately (does not burn attempts) ------
        bad = os.path.join(d, "bad"); os.makedirs(bad)
        subprocess.run(["git", "init", "-b", "main", bad], capture_output=True, text=True)
        okD, dD = sync_push(bad, attempts=3, sleep=lambda s: None)
        ck("non-race failure returns False", okD is False, dD)
        ck("non-race failure does NOT loop 3 times", "attempt 3" not in dD, dD)
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print("\n=== %d PASS / %d FAIL ===" % (p, f))
    return 1 if f else 0


if __name__ == "__main__":
    if "selftest" in sys.argv:
        sys.exit(_selftest())
    print(__doc__)
