# -*- coding: utf-8 -*-
"""GATE — does any RUNNABLE recipe in `04-HANDOFF.md` still name a fixture the manifest calls DEAD?

⛔⛔ WHY THIS IS A GATE AND NOT A PARAGRAPH. This is pair **P3** (`04-HANDOFF`'s HOW TO RUN / TEST
block ↔ what actually shipped), and it has now broken **twice in the same file**, the second time
inside a commit whose own subject line was about the first:

    2026-09-16  "I updated the banner and the punch list and left the RUN RECIPES a session behind,
                 which is a P3 break committed while documenting P3 breaks."
    2026-09-17  the banner, the queue head, the decisions log, the changelog, the punch list AND
                 FIXTURES.md5 were all re-pointed off `post_grind_L60.ss1` — and the HOW TO RUN
                 block still carried `--driver ch24grind post_training.ss1`, the literal command
                 that regrinds the dead branch. Caught by a Tier 1 reviewer, not by a check.

`CLAUDE.md` is explicit about what that means: *"Anything enforceable belongs in a GATE, not in
prose. A rule already broken twice is evidence that prose failed — write the gate instead."* The
cost is concrete and asymmetric: the recipes block is what a COLD READER copies and pastes, so a
stale line there does not mislead a reader for a minute — it spends **hours of emulator time** and
returns a party that cannot be used.

⭐ WHAT IT CHECKS. Every `*.ss1` named on a RUNNABLE line of the recipes block must
  (1) exist as a row in `saves/FIXTURES.md5`, and
  (2) NOT be marked dead there (`DEAD BRANCH`, `DO NOT GRIND`, `DO NOT USE`, `WRONG LINEAGE`).

‼‼ IT DELIBERATELY IGNORES COMMENT LINES, AND THAT IS THE HALF THAT KEEPS IT USABLE. The corrected
recipes block now WARNS about the dead fixture by name — *"THE FIXTURE BELOW WAS … AND THAT IS A
DEAD BRANCH"* — and a gate that fired on that would be firing on its own fix. `CLAUDE.md` again:
*"FAULT-TEST every gate: prove it fails when the thing it guards is broken, and prove it does NOT
fire on mere mentions in comments or docstrings. A gate with false positives teaches the reader to
bypass it, which is strictly worse than no gate."* ⇒ only lines that a shell would EXECUTE count.

⚠ `SUPERSEDED BY` is NOT in the dead list, on purpose. `post_b1f.ss1` is marked superseded and is
still legitimately runnable — it is the un-healed arm of a measured A/B. "Superseded as a starting
point" and "must never be run" are different claims, and conflating them would break a real recipe.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_runrecipe_fixtures.py
    POKEBOT_RECIPEGATE_FAULT=1 ...   # fault arm: also scan COMMENT lines, which MUST make it fail
Exit 0 if every runnable recipe names a live fixture; 1 otherwise.
"""
import os
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = pathlib.Path(__file__).resolve().parents[2]
HANDOFF = REPO / "PROJECT KNOWLEDGE" / "04-HANDOFF.md"
MANIFEST = REPO / "tools" / "story-dev" / "saves" / "FIXTURES.md5"
BAR = "=" * 96

#: Phrases that mean "this fixture must not be the START of a run". ⛔ NOT `SUPERSEDED BY` — see the
#: docstring: a superseded fixture can still be a legitimate A/B arm.
DEAD_MARKERS = ("DEAD BRANCH", "DO NOT GRIND", "DO NOT USE", "WRONG LINEAGE")

SS1 = re.compile(r"\b([A-Za-z0-9_\-]+\.ss1)\b")


def manifest_rows() -> dict:
    rows = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("  ", 3)
        if len(parts) < 3:
            continue
        rows[parts[1].strip()] = (parts[2].strip(), parts[3].strip() if len(parts) > 3 else "")
    return rows


def recipe_lines(scan_comments: bool) -> list:
    """The lines of every fenced block in the handoff, as (lineno, text).

    ⛔ RUNNABLE lines only unless the fault arm is set: a `#` line is documentation, and the
    corrected block documents the dead fixture BY NAME.
    """
    out, in_fence = [], False
    for n, raw in enumerate(HANDOFF.read_text(encoding="utf-8").splitlines(), start=1):
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            continue
        text = raw.strip()
        if not text:
            continue
        if text.startswith("#") and not scan_comments:
            continue
        out.append((n, text))
    return out


def main() -> int:
    fault = os.environ.get("POKEBOT_RECIPEGATE_FAULT", "").strip() == "1"
    print(BAR)
    print("  GATE — runnable recipes in 04-HANDOFF.md must not name a DEAD fixture")
    if fault:
        print("  ⚠ FAULT ARM: comment lines are being scanned too; this MUST fail.")
    print(BAR)

    rows = manifest_rows()
    lines = recipe_lines(scan_comments=fault)
    named, failures, warnings = {}, [], []
    for n, text in lines:
        for name in SS1.findall(text):
            named.setdefault(name, []).append(n)

    for name, where in sorted(named.items()):
        if name not in rows:
            # ⚠ A WARNING, NOT A FAILURE, AND THE ASYMMETRY IS DELIBERATE. "Named in a recipe but
            # never pinned" is a real gap — the `anchors chosen by NAME` shape that
            # `probe_anchor_inventory.py` exists for — but it is a DIFFERENT gap from the one this
            # gate was written to stop, and it pre-dates the gate. Making it fatal would force
            # unrelated pinning work as the price of landing this gate, and a gate that demands
            # unrelated work is one people learn to bypass. ⇒ report every time; block only on the
            # dead-fixture case.
            warnings.append(f"{name} (line(s) {where}) is NOT in FIXTURES.md5 — unpinned")
            print(f"  ⚠  {name:<28} NOT IN THE MANIFEST      lines {where}")
            continue
        kind, note = rows[name]
        hit = [m for m in DEAD_MARKERS if m in note.upper()]
        if hit:
            failures.append(f"{name} (line(s) {where}) is marked {hit} in FIXTURES.md5")
            print(f"  ⛔ {name:<28} MARKED {hit[0]:<14} lines {where}")
        else:
            print(f"  ok {name:<28} {kind:<9}             lines {where}")

    print(f"\n  {len(named)} fixture(s) named on {len(lines)} runnable recipe line(s).")
    if warnings:
        print(f"  ⚠ {len(warnings)} unpinned (reported, NOT blocking — see the note at the check):")
        for w in warnings:
            print(f"      {w}")
    print(BAR)
    if failures:
        print("  ⛔ A RECIPE A COLD READER WOULD COPY POINTS AT A FIXTURE THE MANIFEST CALLS DEAD:")
        for f in failures:
            print(f"      {f}")
        print("  ⇒ re-point the recipe. This is pair P3, and it has broken twice before.")
        print(BAR)
        return 1
    print("  ✅ every runnable recipe names a live fixture.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
