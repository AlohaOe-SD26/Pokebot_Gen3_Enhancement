"""GATE — a CLOSED punch-list item must never be described as OPEN by another item.

WHY THIS EXISTS. `03-PUNCH-LIST.md`'s own P5 rule ("an item's status here and the handoff's claim
about it move TOGETHER") has now been violated **three times in 2026-09, twice inside the SAME
item**, each time in the same shape: a CHILD item is closed, and a PARENT item keeps commanding the
finished work.

    2026-08-23  `#24-sanitycheck`  said "PASSES 4 AND 5 REMAIN" after pass 4 shipped
    2026-09-04  `#24-ch23victoryroad` said "`#24-ch23wally`, which is OPEN" after it closed
    2026-09-04  `#24-ch23victoryroad` said "Add the heal before building leg 7" after
                `#24-ch23healdescent` closed

⛔ **CLOSING A CHILD IS NOT UPDATING THE PARENT**, and three rounds of prose reminders did not make
it so. Rule #6 of SESSION DISCIPLINE: *"Anything enforceable belongs in a GATE, not in prose here. A
rule already broken twice is evidence that prose failed — write the gate instead."* This is that gate.

WHAT IT CHECKS (deliberately narrow, to stay false-positive-free):
  For every item whose OWN header marks it CLOSED/DONE, no OTHER item may refer to its slug with
  open-status language ("is OPEN", "still owed", "remains", "add ... before", "not yet", "awaiting").

⛔ WHAT IT DELIBERATELY DOES **NOT** CHECK: free-form staleness ("Leg 6 ships WITHOUT a heal step"),
which names no slug and cannot be distinguished from legitimate history without guessing. That third
failure shape stays a human/Tier-1 job, and this gate does not pretend otherwise — **a gate that
claims more than it checks is the same defect as a fault arm that cannot fire.**

‼ IT IGNORES the closed item's OWN body, and any line marked as history — a closed item may of
course narrate that it *used to be* open, and a dated postmortem quoting the old wording is not a
live instruction.

FAULT TEST (a gate that cannot fail is decoration):
    POKEBOT_CLOSEDREF_FAULT=inject   -> pretend a parent calls a CLOSED slug OPEN; MUST exit 1
    POKEBOT_CLOSEDREF_FAULT=history  -> pretend the same wording appears inside a HISTORY-marked
                                        line and inside the closed item's own body; MUST still
                                        exit 0 (proves it does not fire on mere mentions)

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_closed_item_refs.py
"""

from __future__ import annotations

import os
import pathlib
import re
import sys
# ⛔ A default Windows console is cp1252 and this file prints ‼/⛔ — without this the gate
# dies with UnicodeEncodeError AFTER its checks pass, i.e. it FALSELY REDS. Found by a
# Tier 1 reviewer running it bare; invisible to anyone who habitually sets PYTHONUTF8=1.
sys.stdout.reconfigure(encoding="utf-8")


ROOT = pathlib.Path(__file__).resolve().parents[2]
#: Optional path argument, so the gate can be pointed at a HISTORICAL copy of the file — that is
#: how it was shown to CATCH the three real 2026-09 failures rather than merely to pass today.
PUNCH = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1
         else ROOT / "PROJECT KNOWLEDGE" / "03-PUNCH-LIST.md")

#: A header marks its item CLOSED when it carries one of these. Kept literal and small on purpose.
CLOSED_MARKS = ("✅", "CLOSED", "DONE 20", "**DONE**")

#: ⛔⛔ AN EXPLICIT OPEN MARKER BEATS EVERY CLOSED SUBSTRING. Added 2026-09-05 after a MEASURED false
#: positive: `#24-e4healing`'s header is `### 🔜 ... (step 1 DONE 2026-09-04). Steps 2-4 ... REMAIN.`
#: — plainly OPEN, and the 🔜 says so — but the substring "DONE 20" inside "DONE 2026-09-04" made this
#: gate classify it CLOSED and then reject a correct cross-reference to it.
#: ⇒ ⭐ A PARTIALLY-DONE ITEM DESCRIBES ITS DONE PART IN ITS OWN HEADER; matching "DONE 20" against a
#: header therefore reads a progress note as a status. The status EMOJI is the status.
#: ‼ `CLAUDE.md` rule 6: a gate with false positives teaches the reader to bypass it, which is strictly
#: worse than no gate. This is that repair, not a workaround for an inconvenient failure.
OPEN_MARKS = ("🔜", "⬜", "🔶")

#: Language that asserts a slug is still outstanding. Each must be a CLAIM about status, never a
#: mere mention — "see `#24-foo`" is fine, "`#24-foo` is OPEN" is not.
OPEN_PATTERNS = (
    r"is\s+\*{0,2}OPEN",
    r"stays?\s+\*{0,2}OPEN",
    r"remains?\s+\*{0,2}(OPEN|UNTAKEN|owed)",
    r"still\s+\*{0,2}(OPEN|owed|untaken|pending)",
    r"awaiting",
    r"not\s+yet\s+(done|built|closed)",
    r"\bADD\b.{0,40}\bbefore\b",
)

#: A line carrying one of these is HISTORY, not a live instruction. ‼ This is what keeps the gate
#: quiet on dated postmortems — the thing that made earlier prose rules unbearable to work with.
HISTORY_MARKS = ("📦", "SUPERSEDED", "RETIRED", "was STALE", "used to", "for one commit",
                 "HISTORY", "formerly", "Formerly", "(was ", "P5 CAUGHT", "postmortem")

FAULT = os.environ.get("POKEBOT_CLOSEDREF_FAULT", "").strip()
SLUG = re.compile(r"`(#\d+[a-z0-9\-+]*)`")


def items(text: str) -> list[dict]:
    """Split the punch list into `### ` items: header line + body lines."""
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if l.startswith("### ")]
    out = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        header = lines[i]
        own = SLUG.findall(header)
        out.append({
            "header": header,
            "slug": own[0] if own else None,
            "body": lines[i + 1:end],
            "line": i + 1,
        })
    return out


def bullets(body: list[str]) -> list[tuple[int, str]]:
    """Group an item's body into LOGICAL units — a bullet plus its wrapped continuation lines.

    ⛔ THIS IS THE WHOLE CORRECTNESS OF THE GATE. Checking line by line misses any claim that wraps,
    which in a hand-wrapped 100-column markdown file is most of them.
    A new unit starts at a `-`/`*` bullet, a `>` quote, or a blank-line-separated paragraph;
    indented continuations belong to the unit above.
    """
    units: list[tuple[int, list[str]]] = []
    for i, line in enumerate(body):
        stripped = line.lstrip()
        starts_unit = (
            stripped.startswith(("- ", "* ", "> "))
            or (not units)
            or (not line.strip())
        )
        if starts_unit or not line.startswith(("      ", "\t", "  ")):
            units.append((i, [line]))
        else:
            units[-1][1].append(line)
    return [(i, "\n".join(ls)) for i, ls in units if "".join(ls).strip()]


def main() -> int:
    text = PUNCH.read_text(encoding="utf-8")
    parsed = items(text)

    closed = {it["slug"] for it in parsed
              if it["slug"]
              and any(m in it["header"] for m in CLOSED_MARKS)
              # ⛔ an explicit OPEN marker in the same header wins — see OPEN_MARKS above
              and not any(m in it["header"] for m in OPEN_MARKS)}

    if FAULT == "inject":
        # a parent describing a genuinely-closed slug as open, on a line with NO history marker
        victim = sorted(closed)[0] if closed else "#24-phantom"
        closed.add(victim)
        # ‼ INJECT THE **WRAPPED** SHAPE, because that is the shape that actually shipped: the verb
        # on one line, the qualifier and the slug on the next. A single-line injection is a test the
        # gate passes for the wrong reason — this arm exists to make that impossible.
        parsed.append({"header": "### 🔜 `#24-faultparent` — injected", "slug": "#24-faultparent",
                       "body": ["- [ ] some preamble text here. **Add the heal",
                                f"      before building leg 7** (see `{victim}`).*"],
                       "line": -1})
    elif FAULT == "history":
        victim = sorted(closed)[0] if closed else "#24-phantom"
        closed.add(victim)
        parsed.append({"header": "### 🔜 `#24-faulthistory` — injected", "slug": "#24-faulthistory",
                       "body": ["- [x] 📦 HISTORY: this once said **Add the heal",
                                f"      before building leg 7** (see `{victim}`), now retired."],
                       "line": -1})
        # and the closed item's OWN body may say it — that must never fire either
        for it in parsed:
            if it["slug"] == victim:
                it["body"] = list(it["body"]) + [f"- this item `{victim}` was OPEN until today"]

    if FAULT:
        print(f"‼ FAULT ARM ACTIVE: POKEBOT_CLOSEDREF_FAULT={FAULT}\n")

    print(f"items: {len(parsed)}   closed items: {len(closed)}")

    findings = []
    for it in parsed:
        # ⛔⛔ MATCH PER **BULLET**, NEVER PER LINE. Markdown WRAPS: the real 2026-09-04 failure read
        # "**Add the heal\n      before building leg 7** (see `#24-ch23healdescent`)" — the verb on
        # one line, the qualifier and the SLUG on the next. A line-by-line scan sees neither half
        # beside the other and reports a clean PASS. ‼ The first draft of this gate did exactly that,
        # and it "passed" its own fault test only because the injected case was a single line.
        # ⇒ **A FAULT TEST THAT DOES NOT REPRODUCE THE REAL SHAPE PROVES NOTHING.**
        for start, bullet in bullets(it["body"]):
            # ⛔⛔ FLATTEN BEFORE MATCHING. `.{0,40}` does NOT cross a newline without re.DOTALL, so
            # matching the raw bullet silently missed every WRAPPED claim — which is all of them in a
            # hand-wrapped file. The real 2026-09-04 failure wrapped between "Add the heal" and
            # "before building leg 7", and the gate reported a clean PASS on it TWICE (line-by-line,
            # once bullet-by-bullet-but-unflattened) before this line existed.
            # ‼ Both misses were found only by running the gate against a RECONSTRUCTION of the real
            # broken file. ⇒ **A GATE IS NOT PROVEN BY ITS OWN FAULT ARM; it is proven against the
            # actual defect it was written for.**
            flat = " ".join(bullet.split())
            if any(m in flat for m in HISTORY_MARKS):
                continue                                  # dated history, not a live claim
            for slug in SLUG.findall(flat):
                if slug not in closed or slug == it["slug"]:
                    continue                              # not closed, or the item talking about itself
                for pat in OPEN_PATTERNS:
                    if re.search(pat, flat, re.IGNORECASE):
                        findings.append(
                            f"{it['slug'] or it['header'][:40]} (line ~{it['line'] + start + 1}) "
                            f"calls CLOSED {slug} outstanding:\n        {flat[:170]}")
                        break
                else:
                    continue
                break

    print()
    if findings:
        print(f"❌ FAIL — {len(findings)} CLOSED item(s) described as outstanding by another item:")
        for f in findings:
            print(f"  • {f}")
        if not FAULT:
            print("\n⇒ CLOSING A CHILD IS NOT UPDATING THE PARENT. Fix the PARENT's wording, or mark "
                  "the line as history (📦 / SUPERSEDED / formerly) if it is a dated record.")
        return 1
    if FAULT == "inject":
        print("❌ THE FAULT ARM DID NOT TRIP THIS GATE — it cannot fail, so it proves nothing.")
        return 1
    if FAULT == "history":
        print("✅ PASS under the `history` arm — the gate correctly stayed quiet on a dated record "
              "and on the closed item's own body. That is the false-positive half of the test.")
        return 0
    print(f"✅ PASS — no CLOSED item is described as outstanding anywhere else in the punch list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
