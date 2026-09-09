# -*- coding: utf-8 -*-
"""GATE: a CLOSED item header must not sit over its own still-open body.

⛔⛔ WHY THIS EXISTS — IT COST FIVE TIER 1 ROUNDS IN ONE SESSION (2026-09-05).
`03-PUNCH-LIST.md`'s `#24-ch23victoryroad` was caught TWICE, in OPPOSITE directions:
  * first its header said *"ONLY THE CHAPTER ORCHESTRATOR + SEGMENT 23 WIRING REMAIN"* while that
    work had shipped in the same commit — an UNDERclaim commanding a rebuild of finished work;
  * so it was promoted to *"✅ … DO NOT REBUILD ANY OF IT"* — and that OVERclaimed, because the same
    item's body still read *"LEG 3's OWED ARMS (still open)"* and *"the three live checks … are
    still owed"*, with no tracked slug for either.
⇒ ⭐ **FIXING AN UNDERCLAIM BY ASSERTING THE OPPOSITE IS NOT A FIX — IT IS THE SAME BUG POINTED THE
OTHER WAY.** The project's own pair-P2 rule already had the answer: *a heading is a claim about every
bullet beneath it; when their statuses differ the heading must say MIXED.*

⛔ THE EXISTING GATES DID NOT COVER THIS, WHICH IS THE WHOLE POINT:
  * `audit_doc_consistency.check_touched_ki_pairs` checks **KI** headers in `05-KNOWN-ISSUES.md`;
  * `probe_closed_item_refs` checks a closed item described as outstanding **BY ANOTHER ITEM**;
  * ⇒ nobody checked a punch-list header against **ITS OWN BODY**. A checklist protects exactly what
    it enumerates, and this was the gap between two checklists.

WHAT IT ENFORCES (deliberately narrow — a noisy gate teaches people to bypass it):
  a `### ✅` / CLOSED item header may not have, anywhere in its own body, a line asserting open work
  ("still open", "still owed", "REMAINS:", "not built", "TODO", …) UNLESS that line is marked as
  history (`superseded`, `formerly`, `📦`, `historical`, `was:`) or sits inside a ``` fence.
  🔶 MIXED headers are EXEMPT — that marker is the documented correct answer for a mixed item.
  🔜 OPEN headers are EXEMPT in this direction: an open item may freely contain finished bullets, and
  under-claiming "open" is the SAFE side of the asymmetry (a Tier 1 reviewer made this point).

Run:  py -3.12 probe_item_header_body.py            # gate
      py -3.12 probe_item_header_body.py --self-test # fault-prove it
      py -3.12 probe_item_header_body.py --list      # show every header it classified
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
# ⛔ A default Windows console is cp1252 and this file prints ‼/⛔ — without this the gate
# dies with UnicodeEncodeError AFTER its checks pass, i.e. it FALSELY REDS. Found by a
# Tier 1 reviewer running it bare; invisible to anyone who habitually sets PYTHONUTF8=1.
sys.stdout.reconfigure(encoding="utf-8")


ROOT = pathlib.Path(__file__).resolve().parents[2]
TARGETS = [ROOT / "PROJECT KNOWLEDGE" / "03-PUNCH-LIST.md"]

#: A header is CLOSED if it carries one of these. ⛔ Keep this list SHORT and literal — inferring
#: "closed" from prose is how a gate starts guessing, and a guessing gate is a bypassed gate.
CLOSED_MARKS = ("### ✅", "### ✅✅", "### ✔")
#: The documented answer for an item whose bullets disagree. Exempt by design, not by oversight.
MIXED_MARKS = ("### 🔶",)

#: Phrases that assert work is still outstanding.
OPEN_WORK = re.compile(
    r"(still\s+open|still\s+owed|still\s+remain|REMAINS\s*:|is\s+UNBUILT|are\s+UNBUILT"
    r"|not\s+yet\s+built|NOT\s+BUILT|TODO\b|must\s+be\s+built|remains?\s+to\s+be\s+(built|done))",
    re.IGNORECASE,
)

#: A line carrying any of these is a HISTORICAL record, not a live claim. ‼ This is the half that
#: keeps the gate honest: the fix for a stale claim is usually to QUOTE it and mark it, not delete
#: it, and a gate that punished that would push people toward deleting hard-won detail.
HISTORY = re.compile(
    r"(superseded|formerly|📦|historical|\bwas\s*:|\bOLD\s*:|\(was\b|retired|ARCHIVED)",
    re.IGNORECASE,
)


def scan(text: str) -> "list[tuple[str, int, str]]":
    """Return [(header, line_no, offending_line)] for CLOSED headers over open-work body lines."""
    lines = text.splitlines()
    header_idx = [i for i, l in enumerate(lines) if l.startswith("### ")]
    problems: "list[tuple[str, int, str]]" = []
    for a, b in zip(header_idx, header_idx[1:] + [len(lines)]):
        head = lines[a]
        if head.startswith(MIXED_MARKS) or not head.startswith(CLOSED_MARKS):
            continue
        in_fence = False
        for i in range(a + 1, b):
            line = lines[i]
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if OPEN_WORK.search(line) and not HISTORY.search(line):
                problems.append((head, i + 1, line.strip()))
    return problems


def classify(text: str) -> "dict[str, int]":
    lines = text.splitlines()
    out = {"closed": 0, "mixed": 0, "other": 0}
    for l in lines:
        if not l.startswith("### "):
            continue
        if l.startswith(MIXED_MARKS):
            out["mixed"] += 1
        elif l.startswith(CLOSED_MARKS):
            out["closed"] += 1
        else:
            out["other"] += 1
    return out


def self_test() -> int:
    """⛔ FAULT-PROVE BOTH DIRECTIONS: it must FIRE on the real defect and STAY SILENT on history."""
    failures: "list[str]" = []

    def check(name: str, doc: str, want_hits: int):
        got = len(scan(doc))
        if got != want_hits:
            failures.append(f"{name}: expected {want_hits} hit(s), got {got}")

    # 1. THE REAL DEFECT — this is verbatim the shape that shipped and was caught by Tier 1.
    check("closed-over-open", "### ✅ `#x` — DONE, DO NOT REBUILD\n\n"
          "⛔⛔ **LEG 3's OWED ARMS (still open):** `STALERESPAWN`, a real `BADSTEP`.\n", 1)
    # 2. NO FALSE POSITIVE on a marked historical quotation — the fix pattern this project uses.
    check("closed-over-superseded", "### ✅ `#x` — DONE\n\n"
          "*(superseded: this read \"LEG 3's OWED ARMS (still open)\" before the fix.)*\n", 0)
    # 3. MIXED is the documented answer and must never fire.
    check("mixed-exempt", "### 🔶 `#x` — MIXED, read each bullet\n\n"
          "🔜 **STILL OPEN:** the chain still remains blocked.\n", 0)
    # 4. An OPEN item may say anything — under-claiming is the safe side.
    check("open-exempt", "### 🔜 `#x` — open\n\nREMAINS: the whole thing.\n", 0)
    # 5. A fenced code block is evidence, not a claim.
    check("fence-exempt", "### ✅ `#x` — DONE\n\n```\nTODO not built\n```\n", 0)
    # 6. Two independent offences in one item are both reported.
    check("two-hits", "### ✅ `#x` — DONE\n\nstill owed: a thing.\nAnd it is NOT BUILT.\n", 2)
    # 7. The offence must be attributed to the CLOSED item, not leak into the next one.
    two = ("### ✅ `#a` — DONE\n\nclean body.\n\n### 🔜 `#b` — open\n\nstill open: fine here.\n")
    check("no-leak-across-headers", two, 0)

    if failures:
        print("SELF-TEST FAILED:")
        for f in failures:
            print(f"  {f}")
        return 1
    print("SELF-TEST PASS — 7 arms:")
    print("  FIRES on a closed header over 'still open' body text (the real 2026-09-05 defect);")
    print("  SILENT on a superseded/quoted history line, on 🔶 MIXED, on 🔜 open items,")
    print("  and on fenced code; reports BOTH offences in one item; no leak across headers.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true", help="fault-prove the gate")
    ap.add_argument("--list", action="store_true", help="show how each header was classified")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    bad = 0
    for path in TARGETS:
        text = path.read_text(encoding="utf-8")
        if args.list:
            c = classify(text)
            print(f"{path.name}: closed={c['closed']} mixed={c['mixed']} other={c['other']}")
        for head, line_no, offender in scan(text):
            bad += 1
            print(f"❌ {path.name}:{line_no} — a CLOSED header sits over open-work text in its OWN body")
            print(f"     header : {head[:110]}")
            print(f"     body   : {offender[:110]}")
    print("=" * 92)
    if bad:
        print(f"FAILED — {bad} closed item(s) whose own body still asserts open work.")
        print("  ⇒ Either mark the line as history (superseded / formerly / 📦), or change the header")
        print("    to 🔶 MIXED with per-bullet markers AND give the residual its own tracked slug.")
        print("  ⛔ Do NOT just delete the sentence — the residual is real work; an untracked")
        print("     residual is the `#24-orphans` shape this file has already paid for twice.")
        return 1
    print("PASS — no CLOSED punch-list header sits over its own still-open body.")
    print("  ‼ This is a NARROW gate: it does not check 🔜 items, other files, or whether a")
    print("    residual's slug actually exists. It closes ONE gap between two other checklists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
