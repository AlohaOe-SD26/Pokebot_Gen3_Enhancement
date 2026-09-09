# -*- coding: utf-8 -*-
"""GATE — the sandbox↔custom DRIFT FIGURE may not be restated as a live fact outside ONE row.

⛔⛔ WHY THIS EXISTS: THIRTEEN INSTANCES, TWELVE RECURRENCES. This is the single most persistent doc defect in the tree.
`04-HANDOFF.md` self-documents recurrence #10 — *"THIS CLAUSE WAS THE 10th STALE COPY OF THE DRIFT
FIGURE and it survived both a nine-site sweep AND a green gate"* — and the edit that "fixed" it to 0
was itself wrong by the next day (#11). On 2026-09-08 a health check fixed the three instances an
audit had ENUMERATED, wrote a changelog entry claiming the class was remediated, and a Tier 1
reviewer immediately found a FOURTH — in the row that self-describes as *"the row a resuming session
reads FIRST"*, reading `Drift is 0 as of 2026-09-08` three lines below a row correctly saying `2`.
A follow-up pattern grep found a FIFTH (#12).

⭐ THE REMEDY IS NOT NEW — IT IS TRANSPLANTED. The project already solved this exact class for line
counts, and wrote down the reason:
    "⛔ NO COUNTS ARE QUOTED HERE — RUN `lint_docs.py`, WHICH PRINTS BOTH"
    "⛔⛔ A LINE-COUNT WRITTEN INTO THE FILE IT COUNTS IS STALE THE MOMENT IT IS WRITTEN."
Drift is the same shape and never got the same treatment. Now it has one, enforced.

THE RULE. In current-state docs (`01`-`05`), a digit adjacent to the whole word "drift" is a
VIOLATION unless it is one of three honest forms:
  1. THE STATE ROW — `04-HANDOFF.md`'s `| sandbox ↔ custom drift |` row. Exactly one place may carry
     a dated number, so a reader has somewhere to look.
  2. QUOTED — text inside double quotes, i.e. a document DESCRIBING a past claim rather than making
     one. ‼ This exclusion is load-bearing: `archive_doc_block.py`'s invariant C once shipped
     completely INERT because it tested text that legitimately echoed what it replaced.
  3. PAST-TENSE — preceded within 70 chars by `was`/`were`/`history`/`previously`/`took`/etc.
     Dated history is honest and must survive; only PRESENT-TENSE claims are the defect.

⛔ FALSE-POSITIVE SURFACE WAS MEASURED BEFORE SHIPPING, because a gate that cries wolf is rated worse
than no gate here (CLAUDE.md rule 6). A first draft matching `drift\\w*` flagged **5 lines, 3 of them
false** — `#24-driftassertions` and `#24-driftreduction` are ITEM SLUGS whose "digit" came from the
`#24` prefix. Whole-word matching (`(?<![\\w-])drift(?![\\w-])`) drops those. A second false positive
survived to the real scan: `02-ARCHITECTURE.md:135` — *"the drift loop is in `04-HANDOFF.md`"* — where
the digit was part of a FILENAME; backtick-parity now excludes it.

⭐⭐ WHAT THE GATE ACTUALLY FOUND, AND WHY THAT IS THE POINT: the audit listed **3** instances, a Tier 1
reviewer found a **4th**, a hand grep found a **5th** — and this gate then found **six more**, for
**13 total**. Among them `03-PUNCH-LIST.md:47` read *"drift is 5"* (live, wrong, in a sentence
describing "the next job"). ⇒ **every human- and agent-authored LIST of this defect was incomplete;
only the pattern was complete.** That is the case for gates over sweeps, restated with numbers.
All 13 were remediated — live claims point at the tool, dated history keeps its number plus an
explicit marker — so this gate ships at **0 findings with no per-file exemptions.**

Bare invocation scans `PROJECT KNOWLEDGE/0[1-5]-*.md`. Exit 0 = PASS.
"""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
K = HERE.parent.parent / "PROJECT KNOWLEDGE"

#: whole-word "drift" within a short span of a digit. ⛔ The lookarounds are what keep
#: `#24-driftassertions` (digit from the slug prefix) out — see the false-positive note above.
#: ⛔⛔ THE SPAN IS `[^.\n]` AND NOT `\W`, AND ITS FAULT ARM IS WHY. The first draft used
#: `\W{0,12}?`, which cannot cross `" is "` — `i` and `s` are WORD characters — so it matched
#: `drift 0` and `drift: 0` but **missed `Drift is 0`, the exact form of recurrences #11 and #12**.
#: It reported 2 real findings and looked healthy while BOTH fault arms silently failed to fire:
#: a gate that is inert against the defect it was built for. ‼ Same shape as `archive_doc_block.py`'s
#: invariant C. ⇒ never let a "findings > 0" result stand in for a working guard; read the arms.
PAT = re.compile(r"(?<![\w-])[Dd]rift(?![\w-])[^.\n]{0,14}?(\d+)")

#: past-tense / historical markers. Dated history is HONEST — only live restatements are the defect.
#: ‼ `reported`/`measured`/`claimed` are here because the marker often lands as a PAST-TENSE VERB
#: rather than the word "was" — `"promote.py --check` reported **drift 0**"`. The window scans only
#: BACKWARDS from the digit on purpose: widening it forwards would let an unrelated later "was"
#: excuse a live claim, which is the false NEGATIVE this gate cannot afford.
PAST = re.compile(r"(was|were|history|previously|led with|before that|earlier|reverted|took|"
                  r"forced|arms|at that time|as measured on|reported|measured|claimed)", re.I)

#: the ONE row permitted to carry a dated digit.
STATE_ROW = "sandbox ↔ custom drift"


def _enclosed_by(line: str, i: int, delim: str, radius: int) -> bool:
    """Is index `i` inside a `delim ... delim` pair that OPENS AND CLOSES within `radius` chars?

    ⛔⛔ THIS REPLACED LINE-GLOBAL PARITY, WHICH SHIPPED AS A FALSE NEGATIVE AND WAS CAUGHT BY A
    TIER 1 REVIEWER. The first version asked `line[:i].count('"') % 2 == 1` — parity measured from the
    START OF THE LINE. That is meaningless in this tree, where a single Markdown "line" routinely runs
    10,000-40,000 characters (`04-HANDOFF.md` self-documents a "39,825-character banner line").
    ‼ MEASURED: `03-PUNCH-LIST.md:47` is **30,045 chars** and carries **47** unrelated `"` before its
    live `drift is 7`. Odd parity ⇒ the gate concluded "inside a quotation" ⇒ a real, present-tense,
    WRONG claim was invisible — a 14th instance, in the very gate built to end the recurrence, while
    it reported "0 findings". ⭐ This is `KI-92` ("`audit_doc_consistency` is BLIND to drift claims
    buried in the banner line") reproducing itself one file over.
    ⇒ A quotation or code span is a LOCAL construct. Bound the scan: the opening delimiter must be
    within `radius` chars before `i`, and a closing one within `radius` after. An unrelated delimiter
    thousands of characters away can no longer flip a verdict.
    """
    lo = line.rfind(delim, max(0, i - radius), i)
    if lo == -1:
        return False
    hi = line.find(delim, i)
    return hi != -1 and (hi - i) <= radius


def violations(text: str) -> "list[tuple[int, str]]":
    """[(line_no, context)] for every LIVE restatement of the drift figure."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if STATE_ROW in line:
            continue
        for m in PAT.finditer(line):
            # inside a quotation -> the document is DESCRIBING a past claim, not making one
            if _enclosed_by(line, m.start(), '"', 200):
                continue
            # ⛔ THE DIGIT IS INSIDE A `code span` -> it is a FILENAME or symbol, not a measurement.
            # Measured false positive that made this necessary: `02-ARCHITECTURE.md:135` reads
            # "The drift loop is in `04-HANDOFF.md` under ..." and the matched digit was the `04`
            # of the FILENAME. A code span is short, so a tight radius is the exact discriminator.
            if _enclosed_by(line, m.end(1) - 1, "`", 60):
                continue
            if PAST.search(line[max(0, m.start() - 70):m.end()]):
                continue
            out.append((i, line[max(0, m.start() - 70):m.end() + 24]))
    return out


def self_test() -> "list[str]":
    """⛔ A GUARD NEVER SEEN TO FAIL IS NOT A GUARD. Arms 1-2 are the REAL defects (#11 and #12);
    arms 3-7 are the real shapes that must NOT fire, each of which a draft got wrong."""
    ARMS = [
        ("FAULT: the Tier-1 kick-back (#11) — unqualified, dated today",
         "`#24-ch23chain` is CLOSED. **Drift is 0 as of 2026-09-08** — MEASURED by the tool.", True),
        ("FAULT: the follow-up grep (#12) — a bare parenthetical",
         "custom is unpromoted, which is the USER's call — drift is 5)*.", True),
        # ⛔⛔ ARM 3 IS THE TIER 1 KICK-BACK (#14) AND THE REASON `_enclosed_by` EXISTS. The gate
        # shipped reporting "0 findings" while BLIND to this shape. The synthetic arms were all short
        # strings; this tree's real lines run 10k-40k chars, and `03-PUNCH-LIST.md:47` carries 47
        # unrelated `"` before its live `drift is 7`, so line-global quote parity said "quoted".
        # ‼ The 47 quotes and the 30k length are BOTH load-bearing — shrink either and the old
        # implementation passes, which is precisely why the original arms missed it.
        ("FAULT: a live claim late in a MEGA-LINE with odd stray-quote parity (the #14 false negative)",
         ('x "' * 47) + ("filler " * 3000) + "Both comments fixed; **drift is 7** (`seafloor_cavern.py`",
         True),
        ("NO-FIRE: dated history with an explicit past marker",
         "rollback tag `pre-promote-2026-09-08`. *(was: drift 5, sandbox-only.)*", False),
        ("NO-FIRE: an ITEM SLUG whose digit comes from the `#24` prefix",
         "see `#24-driftassertions` and `#24-driftreduction` for the split.", False),
        ("NO-FIRE: a document QUOTING a past claim in order to correct it",
         'This clause said "Drift is 0 as of 2026-09-08" while the row above said 2.', False),
        ("NO-FIRE: the one permitted STATE row",
         "| sandbox ↔ custom drift | ⚠ **2 as of 2026-09-08** — victory_road.py |", False),
        ("NO-FIRE: a digit belonging to a FILENAME inside a code span (measured false positive)",
         "⇒ **Do not trust this paragraph — MEASURE.** The drift loop is in `04-HANDOFF.md`.", False),
    ]
    failures = []
    for label, src, should_fire in ARMS:
        hit = bool(violations(src))
        if hit != should_fire:
            failures.append(f"{'DID NOT FIRE' if should_fire else 'FALSE POSITIVE'}: {label}")
    return failures


def main() -> int:
    print("=" * 94)
    print("GATE — the drift figure may not be restated as a live fact outside the STATE row")
    print("=" * 94)

    arm_failures = self_test()
    print(f"\n  self-test: {'PASS — 8 arms (3 fault, 5 no-fire)' if not arm_failures else 'FAILED'}")
    for f in arm_failures:
        print(f"    ⛔ {f}")

    hits = []
    scanned = 0
    for path in sorted(K.glob("0[1-5]-*.md")):
        scanned += 1
        for line_no, ctx in violations(path.read_text(encoding="utf-8", errors="replace")):
            hits.append(f"{path.name}:{line_no}  ...{ctx}")

    print(f"  scanned  : {scanned} current-state file(s)")
    print(f"  findings : {len(hits)}")
    for h in hits[:20]:
        print(f"    ⛔ {h}")

    print("\n" + "-" * 94)
    if arm_failures or hits:
        print("FAILED — a drift digit written into prose is stale the moment it is written.")
        print("         Point at `promote.py --check`, or mark the statement as dated history.")
        print("=" * 94)
        return 1
    print("✅ PASS — no live restatement of the drift figure; all 8 arms behave.")
    print("=" * 94)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
