# -*- coding: utf-8 -*-
"""GATE — a punch-list item may not tick a numbered step `[x]` and ALSO say that step "remains".

‼‼ THE BUG THIS EXISTS TO PREVENT, WHICH HAPPENED TWICE IN 24 HOURS ON THE SAME ITEM.
`#24-e4healing` has a numbered checklist AND a cell header AND a STATUS line — three places stating
the same fact. On 2026-09-13 step 3 shipped: the checklist was ticked, the STATUS line was not, and a
Tier 1 reviewer caught the contradiction. On 2026-09-14 step 4 was answered: the checklist entry was
ticked (`- [x] **4. ANSWERED …**`) and BOTH the cell header (*"REMAINING: step 2 … and step 4"*) and
the STATUS line (*"steps 2 and 4 remain"*) were left stale — caught again, by another reviewer.

⛔ CLAUDE.md's own rule: *"anything enforceable belongs in a GATE, not in prose here. A rule already
broken twice is evidence that prose failed — write the gate instead."* P5 is prose. This is the gate.
⇒ It encodes exactly one property, mechanically checkable:
      IF an item's checklist says `- [x] **N.` for step N,
      THEN no OTHER line in that same item may assert that step N still remains.

⛔ WHAT IT DELIBERATELY DOES NOT DO. It does not judge whether the tick is CORRECT, does not read
the handoff, and does not diff anything. Narrow and mechanical beats broad and noisy: a gate with
false positives teaches the reader to bypass it, which is strictly worse than no gate.

⛔ RETRACTED QUOTES ARE NOT VIOLATIONS. This tree marks corrections by QUOTING the old wording
(*(This read "steps 2 and 4 remain" until 2026-09-14)*), so a naive scan would fire on every correctly
repaired line. A hit is ignored when a dated retraction marker sits in the same clause.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_punchlist_step_status.py
"""
import io
import pathlib
import re
import sys

# ⛔ `parents[2]`, not `[1]`: this file is `<repo>/tools/story-dev/…`, so [0]=story-dev, [1]=tools,
# [2]=repo root. The first draft used [1] and printed "not found" — which the gate correctly
# reported rather than silently passing on zero input. ‼ A gate that cannot find its subject must
# FAIL LOUDLY; "no violations in a file I never opened" is the most dangerous PASS there is.
DOC = pathlib.Path(__file__).resolve().parents[2] / "PROJECT KNOWLEDGE" / "03-PUNCH-LIST.md"

ITEM = re.compile(r"^#{2,4}\s")                       # an item cell starts at a heading
TICKED = re.compile(r"^\s*-\s*\[x\]\s*\*\*(\d+)\.", re.I)
UNTICKED = re.compile(r"^\s*-\s*\[ \]\s*\*\*(\d+)\.")
# "steps 2 and 4 remain" / "step 4 remains" / "REMAINING: ... step 4" / "**and step 4** (…)"
REMAINS = [
    re.compile(r"steps?\s+(?:\d+(?:\s*,\s*\d+)*\s+and\s+)?(\d+)\s+remain", re.I),
    re.compile(r"steps?\s+(\d+)(?:\s+and\s+\d+)?\s+remain", re.I),
    re.compile(r"REMAINING:[^.]{0,120}?\bstep\s+(\d+)", re.I),
    re.compile(r"\*\*and step (\d+)\*\*", re.I),
]
RETRACTED = re.compile(
    r"(this (?:line|clause|cell|item|read)|until 20\d\d-\d\d-\d\d|UPDATED 20\d\d-\d\d-\d\d"
    r"|RETRACTED|SUPERSEDED|formerly|historical)", re.I)
# Split a mega-line into clauses so a retraction elsewhere on the line cannot vouch for this claim.
CLAUSE = re.compile(r"(?<=[.!?])\s+|\*\(|\)\*|—|;")


def main() -> int:
    if not DOC.exists():
        print(f"‼ {DOC} not found")
        return 1
    lines = io.open(DOC, encoding="utf-8", newline="").read().split("\n")

    # ---- carve the file into item cells -------------------------------------------------------
    starts = [i for i, s in enumerate(lines) if ITEM.match(s)] + [len(lines)]
    violations = []
    checked = 0
    for a, b in zip(starts, starts[1:]):
        block = lines[a:b]
        ticked = {}
        for j, s in enumerate(block):
            m = TICKED.match(s)
            if m:
                ticked[m.group(1)] = a + j + 1
        if not ticked:
            continue
        checked += 1
        for j, s in enumerate(block):
            if TICKED.match(s) or UNTICKED.match(s):
                continue  # the checklist itself is the source of truth, not a competing claim
            for clause in CLAUSE.split(s):
                if not clause or RETRACTED.search(clause):
                    continue
                for pat in REMAINS:
                    for m in pat.finditer(clause):
                        step = m.group(1)
                        if step in ticked:
                            violations.append(
                                (a + j + 1, step, ticked[step], clause.strip()[:150]))

    print("=" * 92)
    print("PUNCH-LIST STEP-STATUS GATE — a ticked step may not also 'remain'")
    print("=" * 92)
    print(f"  item cells with a numbered checklist: {checked}")
    if not violations:
        print(f"  RESULT: PASS — no ticked step is contradicted elsewhere in its own item.")
        return 0
    for line, step, tick_line, text in violations:
        print(f"  FAIL  03-PUNCH-LIST.md:{line} says step {step} REMAINS, but the same item ticks "
              f"it `[x]` at :{tick_line}")
        print(f"        …{text}…")
    print()
    print(f"‼ {len(violations)} contradiction(s). ⛔ Fix the STALE half — and remember the tick is "
          f"usually the fresh one.")
    print("  If the old wording must be kept for the audit trail, QUOTE it inside a dated "
          "retraction *(this read \"…\" until YYYY-MM-DD)* and this gate will ignore it.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
