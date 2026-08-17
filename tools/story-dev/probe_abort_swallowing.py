"""PROBE — where can a WHITEOUT (`StoryAbort`) be swallowed by a broad `except`? NO EMULATOR.

‼‼ WHY THIS EXISTS. `StoryAbort` is a `BotModeError`, which is an `Exception`
(`modules/modes/_interface.py:229`). So **every** `except Exception:` and `except BotModeError:`
catches a whiteout. KI-67 identified exactly this and fixed it in the two CHAPTER retry loops that
had been observed failing (`space_center.py:962-977`, `mossdeep_gym.py:534-551`), where the fix is
two guards:

    except StoryAbort:
        raise                        # the abort while the ORIGINAL object is in flight
    except BotModeError as error:
        reraise_if_aborting(error)   # one whose identity an inner loop destroyed

⛔ **THE CLASS WAS NEVER SWEPT.** This probe measures how many other places have the same shape.
Why it matters, in KI-67's own words: the abort latch is cleared ONLY by `StoryMode.run`, so code
that catches the abort and retries IN PLACE runs straight into the next `_check_abort()` — burning
its whole retry budget in a handful of frames and reporting failures that never happened.

⛔⛔ THIS IS A PROBE, NOT A GATE, AND THAT IS DELIBERATE. It currently reports ~53 candidate sites.
Adding it to `run_gates.py` today would make the suite red on pre-existing debt, and a gate that is
red on arrival teaches everyone to ignore it. ⇒ **triage the sites, fix them, THEN promote this to a
gate** (the same path `repro_no_silent_except.py` took, which records its own pre-existing count and
enforces "no worse than").

THE RULE, AND ITS LIMITS — read before believing a number:
  FLAGGED when a `try` block (a) contains a `yield from`, i.e. it DRIVES A GENERATOR and can
  therefore receive an abort raised by a `_check_abort()` deep inside a wait loop; AND (b) has a
  handler catching `Exception` / `BotModeError` / `BaseException` / bare; AND (c) no sibling
  handler catches `StoryAbort` and no handler calls `reraise_if_aborting`.
  ⚠ **FLAGGED IS "COULD SWALLOW", NOT "DOES SWALLOW".** A site is a false positive if no
  `_check_abort()` is actually reachable through that particular `yield from`. This probe does not
  and cannot prove reachability — it narrows 500+ handlers to a list a human can triage.
  ⚠ It also cannot see a guard expressed some other way (a custom re-raise helper, a comparison on
  `type(error)`). Three sites were hand-checked when this was written; see the KI.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_abort_swallowing.py
      PYTHONUTF8=1 py -3.12 probe_abort_swallowing.py --list        # every site, file:line
      PYTHONUTF8=1 py -3.12 probe_abort_swallowing.py --self-test   # prove the rule fires + is quiet
      PYTHONUTF8=1 py -3.12 probe_abort_swallowing.py --build custom  # measure the OTHER fork
‼ `--build custom` is what makes a PROMOTION MEASURABLE instead of assumed: a byte-compare only ever
proves a file was COPIED, never that the fork's OWN handlers gained the guard. Run it before and
after the copy and the number must MOVE. (2026-08-16: custom read 53 before, 45 after.)
Exit codes: 0 always (it is a PROBE — it measures, it does not fail the build).
"""

from __future__ import annotations

import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]

#: ‼ `--build custom` EXISTS SO A PROMOTION CAN BE MEASURED, NOT ASSUMED. A byte-compare only proves
#: a file was COPIED; running THIS probe against `custom-pokebot` before and after proves the fork's
#: OWN handlers gained the guard. That is the discriminator for promoting a KI-81 fix.
_BUILD = "custom" if "--build" in sys.argv and sys.argv[sys.argv.index("--build") + 1] == "custom" else "sandbox"
BUILD = REPO / f"{_BUILD}-pokebot"

#: Deliberately narrow: the story path and the heal helper, i.e. the code that runs while a
#: whiteout can happen. Upstream mirror code is never scanned (project directive).
SCAN = [
    BUILD / "modules" / "story",
    BUILD / "modules" / "modes" / "util" / "higher_level_actions.py",
]

BROAD = {"Exception", "BotModeError", "BaseException"}


def _handler_names(handler: ast.ExceptHandler) -> list[str]:
    t = handler.type
    if t is None:
        return ["<bare>"]
    if isinstance(t, ast.Name):
        return [t.id]
    if isinstance(t, ast.Tuple):
        return [e.id for e in t.elts if isinstance(e, ast.Name)]
    return []


def _drives_generator(try_node: ast.Try) -> bool:
    """A `yield from` in the TRY BODY — the only way an abort from a wait loop can arrive here."""
    for stmt in try_node.body:
        for n in ast.walk(stmt):
            if isinstance(n, ast.YieldFrom):
                return True
    return False


def _guards_abort(try_node: ast.Try) -> bool:
    for h in try_node.handlers:
        if "StoryAbort" in _handler_names(h):
            return True
        for n in ast.walk(h):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id == "reraise_if_aborting"
            ):
                return True
    return False


def scan_source(src: str) -> list[tuple[int, str]]:
    """(lineno, caught-names) for every try that drives a generator, catches broadly, unguarded."""
    out = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Try) or not _drives_generator(node):
            continue
        broad = [n for h in node.handlers for n in _handler_names(h) if n in BROAD or n == "<bare>"]
        if broad and not _guards_abort(node):
            out.append((node.lineno, "/".join(sorted(set(broad)))))
    return out


_GOOD = """
def f():
    try:
        yield from thing()
    except StoryAbort:
        raise
    except BotModeError as error:
        reraise_if_aborting(error)
        report(error)
"""
_BAD = """
def f():
    try:
        yield from thing()
    except Exception as error:
        report(error)
"""
_NO_YIELD = """
def f():
    try:
        thing()
    except Exception as error:
        report(error)
"""


def self_test() -> int:
    """‼ FAULT-TEST (CLAUDE.md rule 6): prove it FIRES when the guard is missing, and prove it stays
    QUIET both when the guard is present and when the try drives no generator (no false positive on
    ordinary telemetry handlers, which is what would make this probe ignorable)."""
    cases = [
        ("guarded (StoryAbort + reraise_if_aborting) -> quiet", _GOOD, 0),
        ("unguarded broad except around `yield from` -> FIRES", _BAD, 1),
        ("broad except with NO `yield from` -> quiet (not our business)", _NO_YIELD, 0),
    ]
    bad = 0
    print("=" * 92)
    print("SELF-TEST — the rule must fire when the guard is missing and stay quiet otherwise")
    print("=" * 92)
    for label, src, expected in cases:
        got = len(scan_source(src))
        ok = got == expected
        bad += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'}  {label}  (found={got}, expected={expected})")
    print("=" * 92)
    print(f"SELF-TEST {'PASS' if not bad else 'FAIL'} ({bad} deviation(s))")
    print("=" * 92)
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    show_all = "--list" in sys.argv

    files: list[pathlib.Path] = []
    for target in SCAN:
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            files += sorted(target.rglob("*.py"))

    print("=" * 92)
    print(f"PROBE [{_BUILD}-pokebot] — broad `except` around a `yield from` NOT guarding StoryAbort")
    print("=" * 92)
    total = 0
    per_file: list[tuple[int, str, list[tuple[int, str]]]] = []
    for f in files:
        hits = scan_source(f.read_text(encoding="utf-8"))
        if hits:
            per_file.append((len(hits), f.relative_to(BUILD).as_posix(), hits))
            total += len(hits)
    per_file.sort(reverse=True)

    for n, path, hits in per_file:
        print(f"  {n:>3}  {path}")
        if show_all:
            for lineno, caught in hits:
                print(f"          {path}:{lineno}   catches {caught}")

    print("-" * 92)
    print(f"  files scanned : {len(files)}")
    print(f"  CANDIDATE sites: {total}")
    print("  ‼ CANDIDATE means 'could swallow a whiteout', NOT 'does'. A site is a false positive")
    print("    if no `_check_abort()` is reachable through its `yield from`. This probe narrows the")
    print("    list for a human; it does not prove reachability. Triage before fixing.")
    print("  ⛔ NOT a gate yet — a gate red on arrival gets ignored. Fix the sites, then promote it.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    sys.exit(main())
