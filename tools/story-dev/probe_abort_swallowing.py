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

⛔⛔ THIS IS A PROBE, NOT A GATE, AND THAT IS DELIBERATE. ⛔ NO COUNT IS QUOTED IN THIS DOCSTRING —
it said ~53 for a day after the real figure was 37, and a cold-start audit caught it. RUN THE PROBE.
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


#: Calls that make a handler abort-AWARE. `reraise_if_aborting` is the house idiom; `story_should_abort`
#: is the hand-written equivalent (`early_game.py:2305` reads `if story_should_abort(): raise`).
#: ‼ REFINEMENT (1), 2026-08-17 — and note WHERE it has to look. The hand guard lives in the HANDLER,
#: not the try BODY; a cold-start audit measured that searching the body removes ZERO sites.
_GUARD_CALLS = {"reraise_if_aborting", "story_should_abort"}


def _guards_abort(try_node: ast.Try) -> bool:
    for h in try_node.handlers:
        if "StoryAbort" in _handler_names(h):
            return True
        for n in ast.walk(h):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _GUARD_CALLS:
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
#: ‼ REFINEMENT (1), 2026-08-17: the HAND-WRITTEN guard. `early_game.py:2305` reads
#: `if story_should_abort(): raise` — semantically identical to `reraise_if_aborting`, and the probe
#: could not see it. ⛔ Note WHERE it sits: in the HANDLER. A cold-start audit measured that searching
#: the try BODY for this shape removes ZERO sites, which is why that mistake is cheap to repeat.
_HAND_GUARD = """
def f():
    try:
        yield from thing()
    except BotModeError as error:
        if story_should_abort():
            raise
        report(error)
"""
#: The control for it: the same shape WITHOUT the guard must still fire, so the new rule cannot be
#: passing everything that merely mentions the word.
_HAND_GUARD_ABSENT = """
def f():
    try:
        yield from thing()
    except BotModeError as error:
        if some_other_condition():
            raise
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
        ("HAND-WRITTEN guard `if story_should_abort(): raise` -> quiet", _HAND_GUARD, 0),
        ("the same shape with an UNRELATED condition -> still FIRES", _HAND_GUARD_ABSENT, 1),
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


#: ⛔⛔ A RATCHET, NOT A THRESHOLD — and this is what finally made this probe GATEABLE.
#: The 2026-08-17 triage measured that ~64% of the candidates are NOT this defect, so a gate that
#: demanded ZERO would be red on arrival over code that is correct as written — the fastest way to
#: teach everyone to ignore gates. And the "obvious" fix (prune by reachability) was REFUTED: see
#: the note above `_guards_abort`. So the gate asserts the only thing that is both true and useful —
#: **the number must never grow**. Same shape as `repro_no_silent_except.py`'s baseline, which is the
#: house pattern for exactly this situation: real debt, no clean zero, but no new debt either.
#: ‼ LOWER IT whenever sites are fixed (that is the ratchet turning); NEVER raise it. A raise means
#: someone added a new unguarded broad `except` around a `yield from` in the story path.
#: ‼ PER BUILD, because the guards are SANDBOX-ONLY until a promotion the USER has to approve.
#: A single number made the documented `--build custom` command exit 1 for a reason that is not a
#: regression — a cold-start audit ran it, got a red FAIL, and had nothing telling it that custom is
#: EXPECTED to be higher. ⛔ A gate that fails for an expected reason is one people learn to ignore.
#: ⇒ when the `#24-abortswallow` guards are promoted, custom's figure becomes sandbox's; lower it then.
#: ‼ THE FORKS NOW DIFFER ON PURPOSE, and that is why these are per-build.
#: sandbox 36 -> 31 on 2026-08-23 (`#24-abortrecoveryresiduals` (b)): five handlers that the
#: `#24-loopheadabort` fix had turned into reachable abort-swallowers were guarded with
#: `reraise_if_aborting(error)`. custom stays 36 because that fix is NOT promoted — drift is 1 and
#: the promotion decision is the USER's.
#: ⛔ CAUSATION PROVEN WITH A CONTROL ARM, because this file's own message demands it (a
#: misattribution on 2026-08-17 is why): stripping exactly those 5 guards and re-running gives
#: **36**; with them, **31**. The drop is the guards, not an unrelated cleanup.
_BASELINES = {"sandbox": 23, "custom": 23}  # EQUAL AGAIN 2026-08-24: the guards were PROMOTED
# ‼ 2026-08-24: custom went 36 -> 23 when `early_game.py` was PROMOTED (user-approved). The forks
#   are EQUAL again, and both now carry ZERO AST abort-swallowers. Verified by the three-point
#   A/B this project requires instead of a byte-compare: AST 8 -> 0, probe 36 -> 23, guards
#   9 -> 22 / loop-head checks 67 -> 84, plus a two-arm latch test loaded from `custom-pokebot`
#   itself (clear -> swallowed, set -> re-raised). Evidence:
#   evidence/2026-08-24-PROMOTION-{BEFORE,AFTER}-custom.stdout.txt
# ‼ sandbox went 31 -> 23 on 2026-08-23 when `#24-abortrecoveryresiduals` (c) guarded the EIGHT
#   PRE-EXISTING swallow sites (7 functions) that predate `#24-loopheadabort`. CONTROL-ARMED, not
#   assumed: with those guards removed the probe reads 31, with them present 23, so the drop is
#   attributable to exactly this change. An AST pass over the file now finds ZERO handlers that
#   can reach `_check_abort` without re-raising - the class is closed in sandbox.
#   ✅ DONE 2026-08-24: promoted (user-approved) and custom was lowered 36 -> 23 in the same commit.
# ‼ custom went 44 -> 36 when the `#24-abortswallow` guards were PROMOTED (2026-08-17,
# user-approved). ⛔ The attribution is not a guess: this probe's own warning is "do NOT claim the
# drop was caused by your change without an arm that removes it", and that arm EXISTS and is
# committed — `evidence/2026-08-17-PROMOTION-BEFORE-custom-all5.stdout.txt` measured 44 on custom
# with the guards ABSENT, minutes before the copy, with nothing else changing. Baseline lowered to
# lock the gain in; the two forks now sit at the same number, which is what promotion should mean.
BASELINE = _BASELINES[_BUILD]


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
    print("  ‼ CANDIDATE means 'could swallow a whiteout', NOT 'does'. Triage before fixing —")
    print("    ~64% were MEASURED (2026-08-17) not to be this defect. This narrows the list; it does")
    print("    not prove anything about a single site.")
    # ‼ THIS FOOTER IS WHAT AN AGENT READS AT THE MOMENT IT DECIDES WHAT TO DO, so it carries the
    # CURRENT plan — it twice carried a superseded one, and a cold-start audit flagged that as the
    # worst-placed of three such instructions.
    print("  ⛔ DO NOT try to drive this to ZERO, and ⛔ do not 'fix' a site because it is listed.")
    print("     It is a RATCHET: the number must never GROW. Lower BASELINE when sites are fixed.")
    if total > BASELINE:
        print("-" * 92)
        print(f"  ‼ FAIL — {total} candidate sites, ABOVE the baseline of {BASELINE}.")
        print("     A new broad `except` now wraps a `yield from` in the story path with no")
        print("     `StoryAbort` / `reraise_if_aborting` guard. Add the guard, or — if an abort")
        print("     genuinely cannot arrive there — say so IN THE HANDLER and raise BASELINE only")
        print("     with that reasoning written down.")
        print("=" * 92)
        return 1
    if total < BASELINE:
        print(f"  ✅ IMPROVED — {total} sites, below the baseline of {BASELINE}.")
        print(f"     ‼ LOWER `BASELINE` to {total} in this file to lock the gain in; a ratchet only")
        print("     ratchets if you turn it. ⛔ And do NOT claim the drop was caused by your change")
        print("     without an arm that removes it — that exact misattribution happened 2026-08-17.")
    else:
        print(f"  ✅ PASS — {total} sites, exactly at the baseline. No new debt.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    sys.exit(main())
