r"""GATE — A MODE-LEVEL BATTLE LATCH MUST NEVER BE TESTED AGAINST `None`.

WHY THIS EXISTS (2026-09-25 — it cost the FIRST full-chapter drive)
-------------------------------------------------------------------
`run_the_gauntlet` chains five §Ch24 legs. Its very first drive WON ALL FIVE FIGHTS
(`battles=5`, every one `BattleOutcome.Won`) and then failed:

    §Ch24 champion: the post-battle chain did not reach the Hall of Fame within 34362
    frames (bound 10,000).

`fight_the_champion` asked `battle_started_frame is not None` and `battle_ended_frame is not None`.
Those are **MODE-level** latches, set by EVERY battle. Driven alone the leg sees one battle and the
question is sound. Driven as the FIFTH leg, **four battles had already ended before it started**, so
both latches were pre-set, two of its stages fell through VACUOUSLY, and it went looking for the
Hall of Fame while Wallace was still being fought.

⇒ **THE GENERAL LESSON:** *a predicate that can be true BEFORE the code meant to make it true has
run is not a predicate — it is a constant.* A latch that survives across stages must be read
**relative to a baseline captured at the stage's own start**, never with `is not None`.

‼ AND THE TEMPTING WRONG FIX IS WHY THIS IS A GATE. Raising the bound would have "worked" — the
press loop would simply have kept going until the fight ended — and shipped a leg whose every
battle predicate was permanently satisfied before it ran, with a budget inflated to hide it. The
failure would have resurfaced later, somewhere else, looking unrelated.

WHAT IT CHECKS
  L1  In `modules/story/`, no `_mode_attr("battle_*_frame")` (or a bare `battle_*_frame` attribute
      read) is compared with `is None` / `is not None`. Relative comparisons (`_be >= _bs`,
      `battles > baseline`) are the correct form and are untouched.

⛔ AST, NEVER GREP: the distinction being enforced is between an IDENTITY-vs-None comparison and an
ORDERING comparison of the same two names, which no textual search can see.
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent / "sandbox-pokebot"
STORY = ROOT / "modules" / "story"

#: The latches that EVERY battle sets. Testing one against None asks "has ANY battle happened",
#: which is not the question any single leg means to ask.
LATCHES = {"battle_started_frame", "battle_ended_frame"}


def _names_a_latch(node: ast.AST) -> str | None:
    """Return the latch name if this expression reads one, else None."""
    if isinstance(node, ast.Call):
        fn = node.func
        if (getattr(fn, "attr", None) or getattr(fn, "id", None)) == "_mode_attr" and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and first.value in LATCHES:
                return str(first.value)
    if isinstance(node, ast.Attribute) and node.attr in LATCHES:
        return node.attr
    return None


def scan(path: Path) -> tuple[list[str], int]:
    tree = ast.parse(io.open(path, encoding="utf-8").read(), filename=str(path))
    bad: list[str] = []
    latch_reads = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) or isinstance(node, ast.Attribute):
            if _names_a_latch(node):
                latch_reads += 1
        if not isinstance(node, ast.Compare):
            continue
        for op, comparator in zip(node.ops, node.comparators):
            if not isinstance(op, (ast.Is, ast.IsNot)):
                continue
            if not (isinstance(comparator, ast.Constant) and comparator.value is None):
                continue
            latch = _names_a_latch(node.left)
            if latch:
                bad.append(
                    f"{path.name}:{node.lineno}  `{latch}` is tested against None. That asks "
                    f"'has ANY battle happened', and EVERY battle sets it — so in a chained run it "
                    f"is already true before this stage starts. Compare it RELATIVE to a baseline "
                    f"captured at this stage's own start."
                )
    return bad, latch_reads


def run() -> int:
    print("=" * 96)
    print("GATE — a MODE-LEVEL battle latch must never be tested against `None`")
    print("=" * 96)
    if not STORY.exists():
        print(f"  ‼ MISSING  {STORY} — cannot scan")
        print("RESULT: FAIL — scan root missing.")
        return 1

    violations: list[str] = []
    reads = 0
    files = sorted(STORY.glob("*.py"))
    for path in files:
        bad, n = scan(path)
        violations.extend(bad)
        reads += n
    print(f"  scanned {len(files)} file(s) under modules/story/; {reads} latch read(s) seen")

    if reads == 0:
        # ⛔ NON-VACUITY: if nothing reads a latch, this gate guards nothing and must say so
        # rather than printing a green light over a blind matcher.
        print("  ⛔ NO LATCH READS FOUND AT ALL — this gate is measuring nothing.")
        print("=" * 96)
        print("RESULT: FAIL — zero latch reads; the matcher is broken or the code moved.")
        return 1

    print("=" * 96)
    if violations:
        print(f"RESULT: FAIL — {len(violations)} absolute latch test(s):")
        for v in violations:
            print(f"  ⛔ {v}")
        return 1
    print(f"RESULT: ALL PASS — {reads} latch read(s), none tested against None.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
