#!/usr/bin/env python3
"""Smoke tests for fleetlib. Every case is a REAL failure from issue-hits.jsonl.

Run:  python3 test_fleetlib.py        -> exit 0 = all pass, 1 = failures
No pytest dependency (the sandbox may not have it).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleetlib as F

P = F_ = 0


def check(name, cond, detail=""):
    global P, F_
    if cond:
        P += 1
        print("  PASS  %s" % name)
    else:
        F_ += 1
        print("  FAIL  %s   %s" % (name, detail))


print("=== fleetlib smoke ===")

# --- env(): the 75x KeyError: 'result' class ---------------------------------
real = '{"success":true,"response":{"exitCode":0,"result":"hello"}}'
code, text, data = F.env(real)
check("env: real envelope exitCode", code == 0, repr(code))
check("env: real envelope text", text == "hello", repr(text))

# the actual failure: no 'result' key at all
noresult = '{"success":true,"response":{"exitCode":1}}'
code, text, data = F.env(noresult)          # must NOT raise KeyError
check("env: missing 'result' does not raise", code == 1, repr(code))
check("env: missing 'result' -> empty text", text == "", repr(text))

check("env: None safe", F.env(None) == (None, "", None), repr(F.env(None)))
check("env: plain text safe", F.env("not json")[1] == "not json")
check("env: dict passthrough", F.env({"exitCode": 0, "result": "x"})[0] == 0)
check("env: content wrapper", F.env({"content": real})[1] == "hello")
check("env: bytes safe", F.env(real.encode())[1] == "hello")
check("env: JSON result is parsed",
      F.env('{"success":true,"response":{"exitCode":0,"result":"{\\"a\\":1}"}}')[2] == {"a": 1})

# --- jget(): the 11x KeyError: 'matches' class -------------------------------
d = {"items": [1, 2, 3], "meta": {"total": 9}}
check("jget: missing key -> default", F.jget(d, "nope", []) == [])
check("jget: dotted path", F.jget(d, "meta.total") == 9)
check("jget: list index in path", F.jget(d, "items.1") == 2)
check("jget: deep miss -> default", F.jget(d, "meta.absent.deep", "X") == "X")
check("jget: list path miss -> default", F.jget(d, "items.99", -1) == -1)
check("jget: non-dict -> default", F.jget(None, "a.b", "d") == "d")

# --- to_int(): the 23x ValueError: int('0x', 16) class -----------------------
check("to_int: '0x' -> None (the observed crash)", F.to_int("0x") is None)
check("to_int: '' -> None", F.to_int("") is None)
check("to_int: None -> None", F.to_int(None) is None)
check("to_int: '0xff' -> 255", F.to_int("0xff") == 255)
check("to_int: 123 -> 123", F.to_int(123) == 123)
check("to_int: '-0x10' -> -16", F.to_int("-0x10") == -16)
check("to_int: 'abc' -> default", F.to_int("abc", default=-7) == -7)
check("to_int: bool is NOT 1", F.to_int(True) is None)

# --- cut(): the 12x KeyError: slice(None, 800, None) class -------------------
check("cut: dict does not raise", isinstance(F.cut({"a": 1, "b": 2}, 1), dict))
check("cut: dict slices by item count", F.cut({"a": 1, "b": 2}, 1) == {"a": 1})
check("cut: str slices by chars", F.cut("abcdef", 3) == "abc")
check("cut: list slices", F.cut([1, 2, 3, 4], 2) == [1, 2])
check("cut: None -> ''", F.cut(None) == "")
check("cut: large dict bounded", len(F.cut({str(i): i for i in range(5000)})) == 800)

# --- cast_index(): the 28x usage-error class --------------------------------
check("cast_index: 3 args, no usage error", F.cast_index("address", "0xabc", 3) == ["address", "0xabc", "3"])
check("cast_index: slot cast to str", all(isinstance(x, str) for x in F.cast_index("bytes32", "0x0", 0)))

# --- is_hex edges ------------------------------------------------------------
check("is_hex: '0x' False", F.is_hex("0x") is False)
check("is_hex: '' False", F.is_hex("") is False)
check("is_hex: '0xff' True", F.is_hex("0xff") is True)
check("is_hex: None False", F.is_hex(None) is False)

# --- end-to-end: the three literal crashing expressions, now safe ------------
resp = {"success": True, "response": {"exitCode": 0}}          # no 'result'
code, text, data = F.env(resp)
check("E2E: r['result'] crash avoided", text == "")
apiresp = {"items": {"weird": "shape"}}                       # items is a dict
check("E2E: d['items'][:800] crash avoided", isinstance(F.cut(F.jget(apiresp, "items", []), 800), (dict, list)))
check("E2E: int('0x',16) crash avoided", F.to_int("0x") is None)

print("\n=== %d PASS / %d FAIL ===" % (P, F_))
sys.exit(1 if F_ else 0)
