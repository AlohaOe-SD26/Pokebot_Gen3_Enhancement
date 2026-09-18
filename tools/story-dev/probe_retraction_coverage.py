#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GATE — a RETRACTED claim must carry a marker at EVERY occurrence, not just the one being edited.

⛔⛔ WHY THIS EXISTS (2026-09-17). In ONE session I retracted three claims and, for each, left another
copy of the SAME sentence live somewhere else:
  1. `03-PUNCH-LIST.md` — a closed item still read "all three prerequisites still stand" after the
     count became four.                                          (found by a Tier 1 reviewer)
  2. `06-DECISIONS-LOG.md` — my own entry still carried "not a re-plumbing job" after I had retracted
     that sentence in two other files.                           (found only after a prompt to look)
  3. `04-HANDOFF.md` — "Grind past L62 toward ~L75 BEFORE building more legs" appears TWICE, verbatim;
     I marked one, called the other "historical", and was wrong. (found by a Tier 1 reviewer)

‼ THE ROOT CAUSE IS A CATEGORY ERROR, WHICH IS WHY PROSE COULD NOT FIX IT. "Is this copy historical?"
is a JUDGEMENT about surrounding prose. "Does a marker sit next to THIS copy?" is a FACT about bytes.
`08-MISTAKES.md` already carried the rule and I broke it anyway — CLAUDE.md §6: "a rule already broken
twice is evidence that prose failed — write the gate instead."
⇒ ⭐ THE ASSERTION: for every retracted claim, count(claim) == count(claim adjacent to a marker).

HOW IT WORKS. The house style for a retraction quotes the dead sentence in curly quotes near a
retraction keyword, e.g.  ⛔⛔ **SUPERSEDED 2026-09-17 — THIS CLAUSE READ "…"**.  So:
  1. find retraction MARKERS (a keyword) and harvest the quoted string that follows within a window;
  2. that quoted string IS the retracted claim;
  3. every occurrence of it, anywhere in the scanned docs, must have a keyword within WINDOW chars.
The marker's own quotation trivially satisfies (3) — which is the designed NEGATIVE control.

⛔ FALSE POSITIVES ARE THE FAILURE MODE THAT MATTERS. A gate that cries wolf gets bypassed, which is
strictly worse than no gate (CLAUDE.md §6). Hence MIN_CLAIM_LEN: short quoted fragments ("done",
"L62") are ignored, because only a distinctive full sentence can be matched safely.

RUN:  py -3.12 probe_retraction_coverage.py             # the gate (exit 0 = pass)
      py -3.12 probe_retraction_coverage.py --self-test # FAULT TEST — proves it fires when broken

⛔⛔ STATUS 2026-09-17 (late): **ADVISORY, NOT ENFORCING — AND ITS OWN SAFETY ARGUMENT WAS REFUTED.**
It shipped ENFORCING for about an hour on the claim that it "fails safe (misses, never false-alarms)".
A Tier 1 reviewer disproved that from BOTH directions in one pass, and I reproduced both myself:
  * **FALSE POSITIVE (refutes "fails safe").** A retraction keyword and an unrelated past-reference
    quotation can sit within the same window, so a still-LIVE sentence gets harvested as dead and
    every honest copy of it is then reported. Keyword-adjacency is not claim-relatedness.
  * **FALSE NEGATIVE ON ITS OWN MOTIVATING DEFECT.** Miss #3 above ("Grind past L62 …") is marked
    IN PLACE — the marker follows the live sentence — not re-quoted via "THIS clause READ …".
    `harvest_claims` only recognises the re-quotation idiom, so **the gate is structurally blind to
    the exact defect it was written for.** Verified: the sentence occurs 2x and is harvested 0x.
⇒ Both defects are filed on `#24-retractioncoverage` with the reviewer's exact repros as test cases.
⛔ DO NOT re-promote this to ENFORCING until both are fixed AND fault-tested against those repros.
‼ THE META-LESSON, which is the durable part: **a fault test proves the arms you thought of; it does
not prove the property you claimed.** I wrote four arms, all passed, and the property they were
supposed to establish ("fails safe") was false in two independent ways.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# ⛔ UTF-8 OR THE GATE DIES WHILE PRINTING ITS OWN FINDING. Measured by a Tier 1 reviewer: on a
# default Windows cp1252 console `_report()` raised UnicodeEncodeError on the "⇒" in its FIX text —
# after the violation was found, so the exit code survived but the guidance never printed. Three
# other gates had this exact bug (see run_gates.py's header). Belt and braces: run_gates.py also
# forces a UTF-8 child, but a human running this bare must get the message too.
sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "PROJECT KNOWLEDGE"

#: Files scanned. Current-state files are where a stale claim is ACTED ON; the append-only histories
#: are included because a retraction written there must also cover its own quotations.
SCAN = ["01-VISION-AND-DESIGN.md", "02-ARCHITECTURE.md", "03-PUNCH-LIST.md", "04-HANDOFF.md",
        "05-KNOWN-ISSUES.md", "06-DECISIONS-LOG.md", "07-CHANGELOG.md", "08-MISTAKES.md"]

#: A claim shorter than this cannot be matched safely — it would collide with ordinary prose.
#: TUNED, NOT GUESSED: at 45 the real tree is clean; lowering it toward ~20 starts matching common
#: phrases and the gate becomes a nuisance. Raise it if a false positive ever appears.
MIN_CLAIM_LEN = 45

#: How far from an occurrence a marker may sit and still be judged to cover it.
#: ‼ The 2026-09-17 miss had a marker ~208,000 chars away in the SAME line, so the window is
#: deliberately tight: a marker earlier in a 64,000-char line does NOT cover a copy far later.
WINDOW_AFTER = 900
WINDOW_BEFORE = 400

KEYWORDS = ("SUPERSEDED", "WITHDRAWN", "WITHDRAW", "RETRACTED", "RETRACTION", "CORRECTED",
            "REFUTED", "IS WRONG", "WAS WRONG", "IS FALSE", "WAS FALSE", "NO LONGER TRUE",
            "DO NOT ACT", "DO NOT RE-OPEN", "DO NOT REOPEN", "OUT OF DATE", "STALE")

#: Harvest the quoted sentence that a retraction marker is retracting.
#: ⛔⛔ v1 OF THIS REGEX WAS `[“”"](...)[“”"]` AND ITS FAULT TEST CAUGHT IT: a closing ” followed by a
#: later opening “ matched the prose BETWEEN two quotations, so it harvested 1,004 "claims" and the
#: real tree showed 199 false positives. A gate that cries wolf is worse than no gate (CLAUDE.md §6),
#: so the pattern is now anchored on the IDIOM instead of on punctuation: a retraction always says
#: what the text USED TO say — "THIS CLAUSE READ …", "it originally read …", "this said …".
#: ⇒ only a quote introduced by a past-tense read-verb counts, and the quote must open and close
#: properly (“…” with no “ or ” inside).
#: ⛔ v2 STILL HAD 17 FALSE POSITIVES, AND THE FAULT TEST CAUGHT THAT TOO. Anchoring on a bare
#: read-verb ("X reads …") matches ORDINARY CITATION as much as retraction — e.g. a live prevention
#: rule quoted in `08-MISTAKES.md`, or `06-DECISIONS-LOG.md` quoting a file's own instructions.
#: ⇒ v3 requires the PAST-REFERENCE idiom that only a retraction uses: a demonstrative or temporal
#: qualifier ("THIS clause read…", "it ORIGINALLY read…", "PREVIOUSLY said…", "USED TO read…").
#: That is the grammatical difference between "what X SAYS" (live) and "what X USED TO SAY" (dead).
_QUOTED = re.compile(
    r"(?:THIS|IT|ORIGINALLY|PREVIOUSLY|FORMERLY|ONCE|USED\s+TO|EARLIER|"
    r"THE\s+(?:CLAUSE|SENTENCE|LINE|ENTRY|ITEM|HEADLINE|BANNER|TEXT))"
    r"(?:\s+\w+){0,4}\s+(?:READ|SAID|CLAIMED|STATED|ASSERTED)\s*:?\s*"
    r"[*_`\s]{0,4}[“\"]([^“”\"]{%d,400})[”\"]" % MIN_CLAIM_LEN,
    re.IGNORECASE,
)


def _load() -> dict:
    out = {}
    for name in SCAN:
        p = DOCS / name
        if p.exists():
            out[name] = p.read_text(encoding="utf-8", errors="replace")
    return out


def _has_marker(text: str, start: int, end: int) -> bool:
    """Is there a retraction keyword NEXT TO this occurrence — excluding the claim's own text?

    ⛔⛔ THE EXCLUSION IS LOAD-BEARING AND ITS ABSENCE WAS CAUGHT BY THE FAULT TEST. v1 searched
    `text[start-BEFORE : end+AFTER]`, which INCLUDES the claim itself. Retracted sentences routinely
    contain a keyword ("…is STALE", "…WAS WRONG"), so such a claim EXCUSED ITSELF everywhere it
    appeared and ARM 2 (inject an unmarked copy) reported ZERO violations — the gate was blind to
    exactly the defect it exists to catch. ⇒ look only at the text BEFORE and AFTER the claim.
    """
    lo = max(0, start - WINDOW_BEFORE)
    hi = min(len(text), end + WINDOW_AFTER)
    window = (text[lo:start] + "\n" + text[end:hi]).upper()
    return any(k in window for k in KEYWORDS)


def harvest_claims(blobs: dict) -> set:
    """Every quoted string that sits next to a retraction keyword IS a retracted claim."""
    claims = set()
    for text in blobs.values():
        up = text.upper()
        for m in _QUOTED.finditer(text):
            c = m.group(1).strip()
            if len(c) < MIN_CLAIM_LEN or c.startswith("http"):
                continue
            # ⛔ BOTH SIGNALS REQUIRED. The past-reference idiom alone still admits ordinary
            # citation ("the entry said X, and that is still true"). A retraction KEYWORD must also
            # sit just before it — that is what makes the quoted text DEAD rather than merely old.
            lo = max(0, m.start() - WINDOW_BEFORE)
            if any(k in up[lo:m.start()] for k in KEYWORDS):
                claims.add(c)
    return claims


def check(blobs: dict) -> list:
    violations = []
    for claim in sorted(harvest_claims(blobs)):
        for name, text in blobs.items():
            at = text.find(claim)
            while at != -1:
                if not _has_marker(text, at, at + len(claim)):
                    line = text.count("\n", 0, at) + 1
                    violations.append((name, line, at, claim))
                at = text.find(claim, at + 1)
    return violations


def _report(violations: list) -> int:
    bar = "=" * 92
    print(bar)
    print("RETRACTION COVERAGE — every retracted claim must be marked at EVERY occurrence")
    print(bar)
    if not violations:
        print("  no unmarked copies of a retracted claim found.")
        print(bar)
        return 0
    for name, line, off, claim in violations:
        shown = claim[:150] + ("..." if len(claim) > 150 else "")
        print("  UNMARKED COPY  %s:%d (offset %d)" % (name, line, off))
        print("      claim: “%s”" % shown)
        print("      ⇒ a retraction marker exists elsewhere, but NOT within %d/%d chars of THIS copy."
              % (WINDOW_BEFORE, WINDOW_AFTER))
    print(bar)
    print("  FAIL: %d unmarked occurrence(s)." % len(violations))
    print("  FIX: put the same marker next to THIS copy. ⛔ Do not judge it 'historical' by reading")
    print("       around it — a marker earlier in the same line does not cover a copy far later.")
    print(bar)
    return 1


def self_test() -> int:
    """FAULT TEST. Prove the gate FIRES when broken and does NOT fire on the real tree."""
    bar = "=" * 92
    print(bar)
    print("SELF-TEST (fault injection)")
    print(bar)
    blobs = _load()
    ok = True

    # ARM 1 — the real tree must be clean.
    real = check(blobs)
    print("  ARM 1  real tree                     -> %d violation(s)  %s"
          % (len(real), "PASS" if not real else "FAIL"))
    if real:
        ok = False
        for v in real[:5]:
            print("         %s:%d “%s”" % (v[0], v[1], v[3][:90]))

    claims = sorted(harvest_claims(blobs), key=len, reverse=True)
    if not claims:
        print("  ARM 2  no retracted claims harvested -> CANNOT FAULT-TEST   FAIL")
        return 1
    victim = claims[0]

    # ARM 2 — inject an unmarked copy of a REAL retracted claim; the gate MUST fire.
    poisoned = dict(blobs)
    poisoned["__injected__.md"] = "Unrelated filler.\n\n" + victim + "\n\nMore filler.\n"
    hits = [v for v in check(poisoned) if v[0] == "__injected__.md"]
    print("  ARM 2  unmarked copy injected        -> %d violation(s)  %s"
          % (len(hits), "PASS" if hits else "FAIL"))
    if not hits:
        ok = False

    # ARM 3 — the SAME injected copy, but WITH a marker beside it, must NOT fire.
    excused = dict(blobs)
    excused["__injected__.md"] = ("⛔ SUPERSEDED 2026-01-01 — this claim was withdrawn: “"
                                  + victim + "”\n")
    hits3 = [v for v in check(excused) if v[0] == "__injected__.md"]
    print("  ARM 3  same copy, marker adjacent    -> %d violation(s)  %s"
          % (len(hits3), "PASS" if not hits3 else "FAIL"))
    if hits3:
        ok = False

    # ARM 4 — sub-threshold fragments must never be harvested (false-positive guard).
    short = [c for c in claims if len(c) < MIN_CLAIM_LEN]
    print("  ARM 4  sub-threshold claims harvested-> %d  %s"
          % (len(short), "PASS" if not short else "FAIL"))
    if short:
        ok = False

    # ARM 5 — THE REGEX ITSELF. ⛔ Required by this project's R-REGEX rule, which exists because
    # `\b` compiled to a literal backspace byte TWICE in one day and BOTH gates reported PASS: a
    # pattern carrying a control character matches nothing and wears a green tick. So the pattern is
    # inspected as bytes, and then exercised against an explicit POSITIVE and NEGATIVE list —
    # never reviewed by reading it. (Added after the diff-triggered hook surfaced the rule.)
    pat = _QUOTED.pattern
    ctrl = [(i, hex(ord(c))) for i, c in enumerate(pat) if ord(c) < 32]
    spliced = ("{%d,400}" % MIN_CLAIM_LEN) in pat
    print("  ARM 5a regex control chars           -> %d  %s"
          % (len(ctrl), "PASS" if not ctrl else "FAIL %s" % ctrl))
    print("  ARM 5b MIN_CLAIM_LEN spliced in      -> %s  %s"
          % (spliced, "PASS" if spliced else "FAIL"))
    if ctrl or not spliced:
        ok = False

    POSITIVE = [
        'the banner ⛔ SUPERSEDED — THIS CLAUSE READ “alpha beta gamma delta epsilon zeta eta '
        'theta iota kappa” and is dead',
        'WITHDRAWN: it originally read *"one two three four five six seven eight nine ten eleven '
        'twelve"* now gone',
        'CORRECTED — the entry previously said “aaa bbb ccc ddd eee fff ggg hhh iii jjj kkk lll '
        'mmm nnn ooo”.',
    ]
    NEGATIVE = [
        # a LIVE rule being quoted, with no retraction keyword anywhere near it
        'the rule reads “alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu”',
        # a genuine retraction whose quoted claim is too short to match safely
        'SUPERSEDED — THIS CLAUSE READ “too short”',
        # a retraction keyword with no quotation at all
        'WITHDRAWN. The design doc states that grass encounters matter a great deal for routing.',
    ]
    pos_bad = [t for t in POSITIVE if len(harvest_claims({"d.md": t})) != 1]
    neg_bad = [t for t in NEGATIVE if len(harvest_claims({"d.md": t})) != 0]
    print("  ARM 5c positive list (%d)             -> %d wrong  %s"
          % (len(POSITIVE), len(pos_bad), "PASS" if not pos_bad else "FAIL"))
    print("  ARM 5d negative list (%d)             -> %d wrong  %s"
          % (len(NEGATIVE), len(neg_bad), "PASS" if not neg_bad else "FAIL"))
    if pos_bad or neg_bad:
        ok = False
        for t in pos_bad + neg_bad:
            print("         %s" % t[:88])

    print(bar)
    print("  SELF-TEST %s   (harvested %d retracted claim(s); victim was %d chars)"
          % ("PASS" if ok else "FAIL", len(claims), len(victim)))
    print(bar)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    raise SystemExit(_report(check(_load())))
