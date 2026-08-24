"""GATE — every §Ch20 constant in the production chapter must equal the DRIVEN harness constant.

WHY THIS EXISTS, and it is not hypothetical. On 2026-08-24, while assembling
`modules/story/seafloor_cavern.py`, a **fabricated `ROOM8_PUSHES` table** was written into
production code. It had the right shape — nine rows, and row 9 correctly faced `Left` because a
warning had drawn attention to that row — and **eight of the nine rows were wrong**. It was invented
from a spec that CITED the source line range without quoting it.

⛔ THE COST IF IT HAD SHIPPED. `ROOM8_PUSHES` drives nine `strength_push` calls in a room where
pushing a boulder onto `(5,3)` PERMANENTLY seals the `(5,2)` door to Room 9. A wrong sequence does
not fail loudly: it jams, burns the one jam-recovery attempt, and fails ~25 minutes into a drive —
or worse, seals the exit and looks like a pathfinding bug.

⇒ THE RULE THIS ENFORCES: **A FILE:LINE CITATION IS A POINTER, NOT THE CONTENT.** If a constant was
proven by a drive, the production copy must be character-identical to the thing that was driven.

WHAT IT CHECKS
  * every tile constant listed in `PAIRS` matches the harness value (the harness is AUTHORITATIVE —
    it is what actually executed and passed `ACCEPTANCE: PASS`);
  * `ROOM8_PUSHES` and `ROOM2_PUSHES` are element-for-element identical to the driven tables;
  * ⛔ and it FAILS LOUD if it cannot FIND a harness constant, rather than passing vacuously — a
    check that silently skips what it cannot parse is the "gate that could not fail" this project
    has already found three times.

Run:  PYTHONUTF8=1 py -3.12 repro_ch20_constants.py
      PYTHONUTF8=1 py -3.12 repro_ch20_constants.py --self-test
"""

import ast
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
HARNESS = REPO / "tools" / "story-dev" / "story_harness.py"
MODULE = REPO / "sandbox-pokebot" / "modules" / "story" / "seafloor_cavern.py"

#: (name in the chapter module, name in the harness). They differ where the harness scopes a
#: constant to one driver class and the module needs a globally unique name.
PAIRS = [
    ("DIVE_TILE", "DIVE_TILE"),
    ("CAVERN_DOOR", "CAVERN_DOOR"),
    ("POOL_TILE", "POOL_TILE"),
    ("CAVERN_EXIT", "CAVERN_EXIT"),
    ("ENTRANCE_WATER", "ENTRANCE_WATER"),
    ("ROOM1_WARP_UP", "ROOM1_WARP_UP"),
    ("ROCK_APPROACH", "ROCK_APPROACH"),
    ("BOULDER1_APPROACH", "BOULDER1_APPROACH"),
    ("BOULDER2_APPROACH", "BOULDER2_APPROACH"),
    ("ROOM2_DOOR", "ROOM2_DOOR"),
    ("ROOM2_SMASH_APPROACH", "ROOM2_SMASH_APPROACH"),
    ("ROOM6_DOOR", "ROOM6_DOOR"),
    ("ROOM6_EXIT", "ROOM6_EXIT"),
    ("ROOM6_ENTRY", "ROOM6_ENTRY"),
    ("ROOM3_ARRIVAL", "ROOM3_ARRIVAL"),
    ("ROOM3_EXIT", "ROOM3_EXIT"),
    ("ROOM3_SIGHT_TILE", "ROOM3_SIGHT_TILE"),
    ("ROOM8_STAGING", "ROOM8_STAGING"),
    ("ROOM9_DOOR", "ROOM9_DOOR"),
    ("ROOM9_ARRIVAL", "ROOM9_ARRIVAL"),
    ("ROOM9_TRIGGER", "ROOM9_TRIGGER"),
    ("ROUTE128_LANDING", "ROUTE128_LANDING"),
    ("ESCAPE_STAND", "ESCAPE_STAND"),
    ("ESCAPE_WATER", "ESCAPE_WATER"),
    ("OCEAN_PROBE", "OCEAN_PROBE"),
    ("ROOM1_CORRIDOR_PROBE", "CORRIDOR_PROBE"),
    ("ROOM8_RETREAT", "ROOM3_RETREAT"),
]

TABLES = ["ROOM8_PUSHES", "ROOM2_PUSHES"]


def _strip_comments(text: str) -> str:
    return re.sub(r"#[^\n]*", "", text)


def _harness_scalar(source: str, name: str):
    """The harness's value for a scalar tuple constant, or None if it is not there."""
    match = re.search(rf"^\s+{re.escape(name)} = (\([^)]*\))\s*(?:#|$)", source, re.M)
    if not match:
        return None
    try:
        return ast.literal_eval(match.group(1))
    except (ValueError, SyntaxError):
        return None


def _harness_table(source: str, name: str):
    """The harness's value for a tuple-of-tuples table, single-line OR multi-line, else None.

    ‼ THE SINGLE-LINE FORM IS TRIED FIRST, AND THAT ORDER IS LOAD-BEARING. The first version tried
    the multi-line pattern first; with `re.S` its `.*?` ran past a single-line table's own closing
    paren to the next `\\n    )` in the file, swallowed unrelated source, failed to parse, and
    returned None — which this gate then reported as "NOT FOUND in story_harness.py".
    ⇒ it accused the harness of having lost a constant that was sitting right there.
    Caught by the gate's own self-test on the day it was written (case B), which is the entire
    reason a gate gets a self-test before it gets trusted.
    """
    line = re.search(rf"^\s+{re.escape(name)} = (\(\(.*\))\s*(?:#|$)", source, re.M)
    if line:
        try:
            return ast.literal_eval(line.group(1))
        except (ValueError, SyntaxError):
            return None
    match = re.search(rf"^\s+{re.escape(name)} = \((.*?)\n\s*\)", source, re.M | re.S)
    if not match:
        return None
    body = _strip_comments(match.group(1)).strip().rstrip(",")
    try:
        return ast.literal_eval("(" + body + ")")
    except (ValueError, SyntaxError):
        return None


def check() -> list[str]:
    findings: list[str] = []
    if not MODULE.exists():
        return [f"{MODULE.relative_to(REPO)} does not exist — the chapter module is gone or moved."]
    source = HARNESS.read_text(encoding="utf-8", errors="replace")

    sys.path.insert(0, str(REPO / "sandbox-pokebot"))
    try:
        from modules.story import seafloor_cavern as chapter
    except Exception as error:  # noqa: BLE001 - an unimportable module is a finding, not a crash
        return [f"could not import modules.story.seafloor_cavern: {type(error).__name__}: {error}"]

    for mine, theirs in PAIRS:
        want = _harness_scalar(source, theirs)
        if want is None:
            # ⛔ LOUD, never skipped. A constant that vanished from the harness means the driven
            # source moved and this gate has stopped comparing anything for that row.
            findings.append(
                f"{theirs!r} NOT FOUND in story_harness.py — this gate can no longer verify "
                f"{mine!r}. Re-point it at the driven source rather than deleting the row."
            )
            continue
        got = getattr(chapter, mine, None)
        if got is None:
            findings.append(f"seafloor_cavern.{mine} is MISSING (harness has {theirs} = {want}).")
        elif tuple(got) != tuple(want):
            findings.append(
                f"seafloor_cavern.{mine} = {got} but the DRIVEN harness {theirs} = {want}. "
                f"The harness is authoritative — it is what passed ACCEPTANCE."
            )

    for name in TABLES:
        want = _harness_table(source, name)
        if want is None:
            findings.append(f"{name!r} NOT FOUND in story_harness.py — this gate cannot verify it.")
            continue
        got = getattr(chapter, name, None)
        if got is None:
            findings.append(f"seafloor_cavern.{name} is MISSING.")
        elif tuple(tuple(row) for row in got) != tuple(tuple(row) for row in want):
            findings.append(
                f"seafloor_cavern.{name} DIFFERS from the driven table. "
                f"module={got} driven={want}. ⛔ Replace it WHOLESALE; do not diff-merge."
            )
    return findings


def self_test() -> int:
    """FAULT-TEST both directions: it must fire on a wrong value, and stay quiet on the real tree."""
    fails = 0

    def expect(label, condition):
        nonlocal fails
        print(f"  {'PASS' if condition else '‼ FAIL'}  {label}")
        if not condition:
            fails += 1

    source = HARNESS.read_text(encoding="utf-8", errors="replace")
    expect("A  the driven ROOM8_PUSHES parses to 9 rows",
           len(_harness_table(source, "ROOM8_PUSHES") or ()) == 9)
    expect("A2 ...and its 9th row faces Left (the seal-the-exit row)",
           (_harness_table(source, "ROOM8_PUSHES") or (((0, 0), ""),) * 9)[8][1] == "Left")
    expect("B  ROOM2_PUSHES parses to exactly 3 rows",
           len(_harness_table(source, "ROOM2_PUSHES") or ()) == 3)
    expect("C  a scalar parses", _harness_scalar(source, "ROOM9_TRIGGER") == (17, 42))
    # ⛔ THE ONE THAT MATTERS: a missing harness name must be LOUD, not skipped.
    expect("D  a name absent from the harness returns None (so check() reports it)",
           _harness_scalar(source, "NO_SUCH_CONSTANT_XYZ") is None
           and _harness_table(source, "NO_SUCH_TABLE_XYZ") is None)
    expect("E  the live tree is clean", check() == [])
    print(f"\nSELF-TEST {'PASS' if fails == 0 else 'FAIL'} ({fails} deviation(s))")
    return 0 if fails == 0 else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    print("=" * 92)
    print("§Ch20 CONSTANT PARITY — the production chapter vs the DRIVEN harness")
    print("=" * 92)
    findings = check()
    for line in findings:
        print(f"  FAIL  {line}")
    if findings:
        print(f"\n  ‼ {len(findings)} constant(s) diverge from what was actually driven.")
        print("  ⛔ A FILE:LINE CITATION IS A POINTER, NOT THE CONTENT — open the source and copy it.")
    else:
        print(f"  all {len(PAIRS)} constants and {len(TABLES)} push tables match the driven source")
    print("=" * 92)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
