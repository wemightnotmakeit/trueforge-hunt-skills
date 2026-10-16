#!/usr/bin/env python3
"""fleetlib — the tolerant-parse layer for sandbox code-mode work.

WHY THIS EXISTS (measured, 2026-10-16). Classifying 349 "Sandbox code error" hits from
issue-hits.jsonl by the last line of their traceback gives:

     75  KeyError: 'result'                       <- assumes the exec envelope has 'result'
     28  Usage: cast index <KEY_TYPE> <KEY> <SLOT>  <- cast index called with wrong arity
     23  NameError: name 'ph_re' is not defined     <- (lint the code; not a lib fix)
     23  ValueError: invalid literal for int() with base 16: '0x'   <- empty hex parsed as int
     12  KeyError: slice(None, 800, None)          <- x[:800] applied to a dict
     11  KeyError: 'matches'                       <- assumed key on an API response
      9  ImportError: cannot import name 'list_tools' from 'mcp_client'

Every one of the top classes is the SAME root cause: ad-hoc code assumes the shape of a
tool/API response and crashes when the shape differs. The model then burns turn budget
retrying instead of doing work. This module makes those accesses total: it returns a
default instead of raising, so a surprise shape costs one line, not one turn.

Doctrine §12 already documents the list_tools trap and it still happened 9 times — a doc
the model must remember is weaker than a function that cannot fail.
"""

__all__ = ["env", "jget", "to_int", "cut", "cast_index", "is_hex"]


def env(raw):
    """Unwrap the sandbox exec envelope. NEVER raises.

    The observed envelope is:
        {"success": true, "response": {"exitCode": N, "result": "<text or JSON>"}}
    but error paths vary, and code that does `r["result"]` dies when it is absent
    (75 of 349 observed failures). Returns (exit_code, text, data) where:
        exit_code : int | None
        text      : str   (always a string; '' when absent)
        data      : parsed JSON if `text` is JSON, else None
    Accepts str, bytes, dict, or the raw tool-call wrapper.
    """
    if raw is None:
        return None, "", None
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8", "replace")
        except Exception:
            return None, "", None
    if isinstance(raw, str):
        s = raw.strip()
        try:
            import json
            obj = json.loads(s)
        except Exception:
            return None, raw, None
        return env(obj)
    if isinstance(raw, dict):
        # a tool-call wrapper may nest the payload in content
        if "response" in raw and isinstance(raw["response"], dict):
            resp = raw["response"]
            code = resp.get("exitCode", resp.get("exit_code"))
            text = resp.get("result", resp.get("output", ""))
            if not isinstance(text, str):
                text = _as_text(text)
            return _maybe_int(code), text, _try_json(text)
        if "result" in raw or "output" in raw or "exitCode" in raw:
            code = raw.get("exitCode", raw.get("exit_code"))
            text = raw.get("result", raw.get("output", ""))
            if not isinstance(text, str):
                text = _as_text(text)
            return _maybe_int(code), text, _try_json(text)
        if "content" in raw:                      # tool.response shape
            return env(raw["content"])
        return None, _as_text(raw), raw           # a bare JSON object IS the data
    return None, _as_text(raw), None


def jget(obj, path, default=None):
    """Nested access that returns `default` instead of raising KeyError.

    path: 'a.b.0.c' or ['a','b',0,'c']. Works on dicts and lists.
    """
    if isinstance(path, str):
        parts = [p for p in path.split(".") if p != ""]
    else:
        parts = list(path)
    cur = obj
    for p in parts:
        if isinstance(cur, dict):
            if p in cur:
                cur = cur[p]
                continue
            # tolerate int keys written as strings
            try:
                if int(p) in cur:
                    cur = cur[int(p)]
                    continue
            except (TypeError, ValueError):
                pass
            return default
        if isinstance(cur, (list, tuple)):
            try:
                cur = cur[int(p)]
                continue
            except (TypeError, ValueError, IndexError):
                return default
        return default
    return cur


def is_hex(x):
    """True only for a usable 0x-prefixed hex string (rejects '', '0x', None)."""
    if not isinstance(x, str):
        return False
    s = x[2:] if x[:2].lower() == "0x" else x
    if not s:
        return False
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def to_int(x, base=None, default=None):
    """Total int conversion. '0x' / '' / None -> default (never ValueError).

    23 observed failures came from int('0x', 16) on an empty hex string.
    """
    if x is None or isinstance(x, bool):
        return default
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        s = x.strip().replace("_", "")
        if s == "":
            return default
        neg = s.startswith("-")
        if neg:
            s = s[1:]
        try:
            v = int(s, base) if base else (int(s, 16) if s[:2].lower() == "0x" else int(s, 10))
        except ValueError:
            return default
        return -v if neg else v
    try:
        return int(x)
    except (TypeError, ValueError):
        return default


def cut(x, n=800):
    """`x[:n]` that also works when x is a dict or list (12 observed KeyErrors).

    A dict is sliced by ITEM COUNT and rendered as text; a str by CHARS.
    """
    if x is None:
        return ""
    if isinstance(x, str):
        return x[:n]
    if isinstance(x, (list, tuple)):
        return list(x)[:n]
    if isinstance(x, dict):
        keys = list(x.keys())[:n]
        return {k: x[k] for k in keys}
    return _as_text(x)[:n]


def cast_index(key_type, key, slot):
    """Correct `cast index` invocation.

    Observed failure mode: `Usage: cast index <KEY_TYPE> <KEY> <SLOT_NUMBER>` (28 hits) --
    callers passed the wrong arity. This returns the exact argv list.
        cmd = ["cast", "index"] + cast_index("address", "0xabc...", 3)
    """
    return [str(key_type), str(key), str(int(slot))]


# ---- internals -------------------------------------------------------------
def _as_text(x):
    if isinstance(x, str):
        return x
    try:
        import json
        return json.dumps(x)
    except Exception:
        return str(x)


def _maybe_int(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return v
    return to_int(v)


def _try_json(text):
    if not isinstance(text, str):
        return None
    s = text.strip()
    if not s or s[0] not in "[{":
        return None
    try:
        import json
        return json.loads(s)
    except Exception:
        return None
