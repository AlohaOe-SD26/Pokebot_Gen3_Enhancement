#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""No `yield` inside a `finally` anywhere on the story surface — it is a latent crash.

⛔ THE DEFECT, MEASURED 2026-09-11 (not theory — this script PROVES it at runtime below).
A generator that yields from inside a `finally` raises **`RuntimeError: generator ignored
GeneratorExit`** if it is closed while suspended inside the corresponding `try`:

    normal completion            -> fine
    closed while suspended       -> RuntimeError: generator ignored GeneratorExit
    exception propagating out    -> fine

CPython closes an abandoned generator automatically at garbage-collection time, so this fires on
perfectly ordinary paths: a mode switch, a discarded story run, an abort that drops the generator.

‼ WHY IT MATTERS HERE RATHER THAN IN GENERAL. This project's story code is ALL generators, and the
`try: …train… finally: restore_lead()` shape is the *obvious* way to guarantee cleanup — so the
mistake is attractive, not exotic. Two instances existed the day this gate was written:
  * `plugins/custom_modes/story_mode.py` — `#24-maintain`'s new maintenance step, caught BEFORE it
    ever ran.
  * `modules/story/victory_road.py` — ALREADY PROMOTED production code, whose comment read
    *"⛔ IN A `finally` ON PURPOSE"*. The intent (restore the lead on every path) was right; the
    mechanism was a latent crash. ⇒ **a deliberate-looking comment is not evidence of safety.**
The exposure is not a narrow window either: `train_team` can sit suspended for ~100k frames.

⭐ THE CORRECT SHAPE, and it is not much longer:

    try:
        yield from work()
    except GeneratorExit:
        raise                        # ⛔ never yield while being closed
    except BaseException:
        yield from cleanup()
        raise                        # ‼ never SWALLOW an abort (gate #27)
    else:
        yield from cleanup()

⚠ SCOPE: the STORY SURFACE (`modules/story/`, `plugins/custom_modes/`), because that is where this
project's generators live and where a crash strands a run. Upstream `modules/` is deliberately out
of scope — churning vendored code would make this gate noisy, and a noisy gate gets bypassed.
⚠ A `yield` in a `finally` inside a NON-generator function is impossible (it would make it one), so
every hit is by definition a generator.

Run:   cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_yield_in_finally.py
       --self-test   prove the DETECTOR works on known-good/known-bad snippets
Fault: POKEBOT_YIELDFINALLY_FAULT=1  — inject a synthetic offender; the gate MUST go red.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "sandbox-pokebot"
SCOPE = ("modules/story", "plugins/custom_modes")

FAULT = os.environ.get("POKEBOT_YIELDFINALLY_FAULT", "")


#: Nodes that open a NEW function scope. A `yield` inside one belongs to THAT function, not to the
#: generator whose `finally` we are inspecting.
_SCOPE_BOUNDARIES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)

#: Both try flavours. `try/except*` (PEP 654) parses to `ast.TryStar`, which is NOT an `ast.Try`.
#: `getattr` because `TryStar` only exists on Python 3.11+.
_TRY_NODES = tuple(t for t in (ast.Try, getattr(ast, "TryStar", None)) if t is not None)


def _walk_same_scope(node: ast.AST):
    """Like `ast.walk`, but does NOT descend into a nested function/lambda body.

    ⛔ ADDED after trying to DEFEAT this gate rather than only to satisfy it. A plain `ast.walk`
    flags this, and it is a FALSE POSITIVE:

        try:
            yield 1
        finally:
            def inner():
                yield 2          # <- belongs to `inner`, not to us; harmless
            register(inner)

    `inner` is its own generator; defining it during cleanup yields nothing from the enclosing one.
    ‼ A gate with false positives teaches the reader to bypass it, which this project rates as
    strictly worse than no gate (rule 6) — so the detector has to be right in BOTH directions, and
    the only way to find out was to attack it. Self-test S9 pins this.
    ⚠ A nested function with its OWN `try/finally` that yields is still caught — by the outer loop
    reaching that inner `ast.Try` node in its own right (self-test S10).
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _SCOPE_BOUNDARIES):
            continue
        yield child
        yield from _walk_same_scope(child)


def offenders(src: str) -> list[tuple[int, str]]:
    """Every `yield` / `yield from` that the enclosing generator would execute from a `finally`."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        # ⚠ `ast.TryStar` (`try/except*`, PEP 654) is a SEPARATE node type — `isinstance(x, ast.Try)`
        # is False for it, so an exception-group try was invisible to v1. There is no `except*`
        # anywhere in the tree today, so this was inert debt rather than a live miss; handled anyway
        # because "inert today" is a statement about today. (Found by a Tier 1 reviewer, 2026-09-11.)
        if not isinstance(node, _TRY_NODES):
            continue
        for stmt in node.finalbody:
            if isinstance(stmt, _SCOPE_BOUNDARIES):
                continue                      # a def/lambda in the finally is not OUR yield (S9)
            for sub in (stmt, *_walk_same_scope(stmt)):
                if isinstance(sub, (ast.Yield, ast.YieldFrom)):
                    out.append((sub.lineno,
                                "yield from" if isinstance(sub, ast.YieldFrom) else "yield"))
    return sorted(set(out))


# ---------------------------------------------------------------------------- the runtime proof
def prove_the_hazard() -> bool:
    """⛔ Demonstrate the RuntimeError rather than asserting it.

    A gate whose rationale is a claim about the language is worth more if it re-derives that claim
    every run — then the day the semantics change, the gate says so instead of quietly guarding
    against nothing.
    """
    def inner():
        yield "cleanup"

    def offender():
        try:
            yield "work"
        finally:
            yield from inner()

    g = offender()
    next(g)
    try:
        g.close()
    except RuntimeError:
        return True
    return False


def self_test() -> int:
    CASES = [
        ("S1 yield-from in finally            -> DETECTED",
         "def f():\n    try:\n        yield 1\n    finally:\n        yield from g()\n", 1),
        ("S2 bare yield in finally            -> DETECTED",
         "def f():\n    try:\n        yield 1\n    finally:\n        yield 2\n", 1),
        ("S3 nested inside an if in finally   -> DETECTED",
         "def f():\n    try:\n        yield 1\n    finally:\n        if x:\n            yield 2\n", 1),
        ("S4 the CORRECT shape                -> quiet",
         "def f():\n    try:\n        yield 1\n    except GeneratorExit:\n        raise\n"
         "    except BaseException:\n        yield from c()\n        raise\n    else:\n        yield from c()\n", 0),
        ("S5 finally with NO yield            -> quiet",
         "def f():\n    try:\n        yield 1\n    finally:\n        log('done')\n", 0),
        ("S6 yield in try/except, not finally -> quiet",
         "def f():\n    try:\n        yield 1\n    except E:\n        yield 2\n", 0),
        ("S7 a MENTION in a comment/string    -> quiet",
         "def f():\n    try:\n        yield 1\n    finally:\n        log('yield from x')\n", 0),
        # ⛔ S9-S12 came from trying to DEFEAT this gate, not from trying to satisfy it. S9 was a
        # genuine FALSE POSITIVE in v1 — and a gate that cries wolf is worse than no gate (rule 6).
        ("S9 a nested FUNCTION defined in the finally -> quiet (its yield is not ours)",
         "def f():\n    try:\n        yield 1\n    finally:\n        def inner():\n"
         "            yield 2\n        register(inner)\n", 0),
        ("S10 ...but that inner function's OWN try/finally IS still caught",
         "def outer():\n    def inner():\n        try:\n            yield 1\n"
         "        finally:\n            yield 2\n    return inner\n", 1),
        ("S11 a nested try INSIDE the finally still counts",
         "def f():\n    try:\n        yield 1\n    finally:\n        try:\n"
         "            yield 2\n        except E:\n            pass\n", 1),
        ("S12 a `with` inside the finally still counts",
         "def f():\n    try:\n        yield 1\n    finally:\n        with lock():\n"
         "            yield 2\n", 1),
        # ⚠ S13 — `try/except*` is an ast.TryStar, NOT an ast.Try. Inert today (no `except*` in the
        # tree) but it was a real hole in v1: "nothing uses it yet" is a statement about today.
        ("S13 an `except*` (exception-group) try is also caught",
         "def f():\n    try:\n        yield 1\n    except* ValueError:\n        pass\n"
         "    finally:\n        yield 2\n", 1),
    ]
    bad = 0
    for label, src, want in CASES:
        got = len(offenders(src))
        ok = got == want
        bad += 0 if ok else 1
        print(f"  {'PASS' if ok else '❌ FAIL'}  {label}  (found {got}, expected {want})")
    proved = prove_the_hazard()
    print(f"  {'PASS' if proved else '❌ FAIL'}  S8 the RuntimeError is REPRODUCED at runtime")
    bad += 0 if proved else 1
    print(f"\n  SELF-TEST {'PASS' if not bad else 'FAIL'} ({bad} deviation(s))")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()

    print("=" * 96)
    print("NO `yield` INSIDE A `finally` ON THE STORY SURFACE")
    print("=" * 96)

    if not prove_the_hazard():
        print("  ⛔ THE HAZARD DID NOT REPRODUCE on this interpreter — the rationale for this gate")
        print("     no longer holds. Investigate before deleting it; do not assume it is obsolete.")
        return 1
    print("  ✅ hazard reproduced at runtime: closing a suspended generator whose `finally` yields")
    print("     raises RuntimeError('generator ignored GeneratorExit')\n")

    found: list[tuple[str, int, str]] = []
    scanned = 0
    for rel in SCOPE:
        base = SANDBOX / rel
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            scanned += 1
            src = p.read_text(encoding="utf-8", errors="replace")
            if FAULT == "1" and not found:
                src += "\n\ndef _injected_offender():\n    try:\n        yield 1\n    finally:\n        yield 2\n"
            for line, kind in offenders(src):
                found.append((p.relative_to(SANDBOX).as_posix(), line, kind))

    print(f"  scanned {scanned} file(s) under {', '.join(SCOPE)}")
    if found:
        print(f"\n  ❌ FAIL — {len(found)} `yield` inside a `finally`:")
        for rel, line, kind in found:
            print(f"       {rel}:{line}  ({kind})")
        print("\n  ⇒ replace with except GeneratorExit: raise / except BaseException: <cleanup>; raise")
        print("     / else: <cleanup>. ⛔ Do NOT simply delete the cleanup — restoring the lead on the")
        print("     failure path is why the `finally` was reached for in the first place.")
        print("=" * 96)
        return 1

    print("  ✅ PASS — no story-surface generator yields from a `finally`.")
    print("=" * 96)
    if FAULT == "1":
        print("  ⛔⛔ FAULT ARM DID NOT REACH THE SCAN — this gate proves nothing.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
