# -*- coding: utf-8 -*-
"""GATE — a KI whose 05 HEADER says PROMOTED/FIXED/CLOSED may not be called NOT PROMOTED / STILL OPEN
in a LIVE clause of 04-HANDOFF.md.

⛔⛔ WHY THIS EXISTS: `#24-promotedpairgate`. SEVEN instances of one shape in a single day, every one
caught by cost (a diff advisory, a Tier 1 reviewer, a Tier 2 cold-start audit) and never by a check.
The shape is always identical: a fact lives in THREE places — a KI header, the handoff STATE row, and
the handoff BANNER — an increment updates the two it is already typing in, and the BANNER, the half a
cold reader meets FIRST and ACTS on, keeps the superseded claim. CLAUDE.md rule 6: *a rule already
broken twice is evidence that prose failed — write the gate instead.*

⛔⛔⛔ **THE OBVIOUS SHAPE OF THIS GATE IS ALREADY REFUTED, BY MEASUREMENT, AND THAT IS THE WHOLE
DESIGN CONSTRAINT.** The punch-list item records a dry run of the LINE-SCOPED version:
  * run 1 → **6 findings, ALL FALSE POSITIVES.** Every one came from `04-HANDOFF.md:386`, where the
    phrase *"the two drifting FILES are NOT promoted"* sat on the same LINE as six unrelated `KI-`
    numbers. In this tree a "line" runs to tens of thousands of characters and carries dozens of
    independent facts ⇒ *"a line mentioning KI-X that also contains NOT PROMOTED"* is a meaningless
    conjunction.
  * run 2, after the real defect at :386 was FIXED — i.e. after the document got strictly MORE
    accurate — findings went **6 → 23**, with **20 of the 23 from ONE line** (`:145`, the mega-line
    YOU-ARE-HERE history block).
  ⇒ **the line-scoped metric tracks LINE LENGTH, not correctness.** A measure that gets WORSE when
  the thing it measures gets BETTER is measuring the wrong quantity, and no amount of tuning the word
  list fixes it.

⭐ THE FIX IS A PRIMITIVE THIS TREE ALREADY OWNS. `probe_drift_restatement.py` hit the same wall
(line-global quote parity is meaningless at 30,045 chars) and solved it with a BOUNDED-RADIUS
enclosure test. The same idea is what "clause-scoped" means here: **the KI mention and the
contradicting status phrase must be near EACH OTHER**, not merely on one line. Distance is the
discriminator; line identity is not.

THE RULE.
  1. Read every `## KI-<n>` header in `05-KNOWN-ISSUES.md` (both `## KI-7 —` and ``## `KI-101` —``
     spellings ship in that file). A KI is CLOSED-ish if its header carries a positive status word
     (PROMOTED / FIXED / CLOSED / SOLVED / DONE) that is **not** negated right before it.
  2. In `04-HANDOFF.md`, for each mention of such a KI, look only inside a **CLAUSE WINDOW** of
     ±`RADIUS` characters for a contradicting phrase (NOT PROMOTED / UNPROMOTED / STILL OPEN /
     AWAITING A RULING / NOT YET PROMOTED).
  3. Three exemptions, each earned:
     a. **DATED RETRACTION** — the span sits inside an italic parenthetical `*( … )*`. ⛔ REQUIRED,
        not decorative: the item measured that this exemption alone suppressed **35** would-be false
        positives on this file's `*(This clause read …)*` style. Without it the gate is unusable.
     b. **QUOTED** — inside a `"…"` span: the document is DESCRIBING a past claim, not making one.
     c. **PAST TENSE** — a `was`/`until`/`previously`/`superseded`… marker inside the window.

⛔ WHAT THIS GATE DELIBERATELY DOES **NOT** DO. It does not read the punch list, and it does not try
to decide whether a KI is *really* fixed. It compares two documents' WORDS. That is narrow on
purpose: the failures it exists to catch were all word-level contradictions between two files, and a
broader gate would inherit the false-positive surface that killed the first design.

    PYTHONUTF8=1 py -3.12 probe_promoted_pair.py            # scan; exit 0 = PASS
    PYTHONUTF8=1 py -3.12 probe_promoted_pair.py --self-test # FAULT ARMS; exit 0 = all behaved
"""

import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
K = HERE.parent.parent / "PROJECT KNOWLEDGE"

#: The clause window, in characters, on EACH side of the KI mention. ⛔ THIS NUMBER IS THE GATE.
#: Too large and it degenerates into the line-scoped version that measured line length; too small and
#: it misses a real contradiction split by a sub-clause. 300 was chosen because the REAL defect
#: (KI-101: "…IS PROMOTED…" headline and "⛔ NOT PROMOTED — PROMOTION IS THE USER'S CALL" in the same
#: STATE cell) spanned ~250 chars, while the measured FALSE positive at :386 put its KI numbers
#: ~2,000+ chars from the phrase. The two populations are three orders of magnitude apart, so the
#: verdict is not sensitive to the exact value — which is the property a threshold should have.
RADIUS = 300

#: ⛔ BOTH HEADER SPELLINGS SHIP IN 05. `## KI-74 — …` and ``## `KI-101` — …`` are both live; a
#: pattern matching only the bare form silently skips every backticked KI, which includes the very
#: issue this gate was built for. Measured before writing the regex, not after.
HEADER = re.compile(r"^#{2,3}\s+`?KI-(\d+)`?\s*[—\-]", re.M)

POSITIVE = re.compile(r"(?<!NOT )(?<!NOT<b>)(?<!NEVER )\b(PROMOTED|FIXED|CLOSED|SOLVED)\b")
CONTRA = re.compile(r"(NOT\s+(?:YET\s+)?PROMOTED|UNPROMOTED|STILL\s+OPEN|AWAITING\s+A(?:\s+USER)?\s+RULING)",
                    re.I)
PAST = re.compile(r"(was|were|used to|until|previously|superseded|retracted|earlier|"
                  r"no longer|stood here|this read|this clause read|for four minutes)", re.I)

#: ⛔ A HEADER THAT DECLARES ITSELF MIXED IS OUT OF SCOPE — AND THIS EXCLUSION WAS EARNED BY A
#: MEASURED FALSE POSITIVE, NOT ANTICIPATED. First live run flagged `KI-76`, whose header reads
#: "🔶 **MIXED: ✅ SAFETY half FIXED …; ⚠ CORRECTNESS half UNFIXED**" against a handoff clause saying
#: "KI-76's correctness half is still OPEN". Those two documents AGREE. Firing on agreement is the
#: precise failure the punch-list item says makes a gate worse than none. ⇒ same family as the
#: CONTRA-in-header exclusion: a KI is in scope only when its header makes a CLEAN positive claim.
#: ⛔⛔ AND IT MUST NOT MATCH "PARTIALLY **ARCHIVED**" — A FALSE NEGATIVE I SHIPPED AND CAUGHT IN THE
#: SAME LIVE RUN. The first version of this exclusion matched `PARTIAL`, which silently removed
#: `KI-95` from scope: its header reads "✅ RESOLVED/FIXED, GATED #39, PROMOTED 2026-09-07. ⚠
#: **PARTIALLY ARCHIVED 2026-09-16…**". "Partially archived" is a fact about where the DOCUMENT
#: lives, not about whether the FIX is partial — and excluding it made the gate miss the one REAL
#: defect it had just found (a live "sandbox-only, unpromoted" against a PROMOTED header).
#: ‼ THE LESSON, and it is why this comment is long: I tuned to kill false positives and killed the
#: TRUE positive with them. Any exclusion added to silence noise must be re-checked against the
#: findings it is NOT supposed to silence — the arms below do that mechanically.
MIXED = re.compile(r"(MIXED|PARTLY|PARTIAL(?!LY\s+ARCHIVED)|half\b|halves)", re.I)


def _enclosed_by(line: str, i: int, open_d: str, close_d: str, radius: int) -> bool:
    """Is index `i` inside an `open_d … close_d` pair that both opens and closes within `radius`?

    ⛔ TRANSPLANTED FROM `probe_drift_restatement.py`, WHERE LINE-GLOBAL PARITY SHIPPED AS A FALSE
    NEGATIVE. Parity measured from the start of the line is meaningless when one Markdown line runs
    30,000+ characters. A quotation or an italic parenthetical is a LOCAL construct: bound the scan.
    """
    lo = line.rfind(open_d, max(0, i - radius), i)
    if lo == -1:
        return False
    hi = line.find(close_d, i)
    return hi != -1 and (hi - i) <= radius


def closed_kis(known_issues_text: str) -> "dict[str, str]":
    """{'KI-101': '<header line>'} for every KI whose HEADER claims a positive status."""
    out = {}
    for m in HEADER.finditer(known_issues_text):
        line_end = known_issues_text.find("\n", m.start())
        header = known_issues_text[m.start(): line_end if line_end != -1 else len(known_issues_text)]
        # ⛔ A HEADER THAT ITSELF SAYS "NOT PROMOTED" IS NOT CLEANLY CLOSED — AND INCLUDING IT WOULD
        # MAKE THE GATE FIRE ON AGREEMENT. Found by a fault arm before shipping: the header
        # "…(2026-09-01, FIXED in sandbox, NOT PROMOTED)" classified as closed, because `FIXED` is
        # genuinely positive. But such a header and a handoff clause saying NOT PROMOTED are
        # CONSISTENT — that is the two documents agreeing, which is the opposite of the defect.
        # ⇒ a KI is in scope only when its header is positive AND carries no contradiction of its own.
        if POSITIVE.search(header) and not CONTRA.search(header) and not MIXED.search(header):
            out[f"KI-{m.group(1)}"] = header
    return out


def violations(handoff_text: str, closed: "dict[str, str]") -> "list[tuple[int, str, str]]":
    """[(line_no, ki, context)] for every LIVE contradiction inside a clause window."""
    out = []
    for lineno, line in enumerate(handoff_text.splitlines(), 1):
        #: ⛔⛔ EVERY `KI-<n>` ON THE LINE, closed or not — because attribution needs the ones that are
        #: NOT in scope too. MEASURED FALSE POSITIVE that forced this: the first live run flagged
        #: `KI-65` (header "CLOSED … PROMOTED") on `:145`, where the words "still open" belong to
        #: **KI-66's** owner-filter half, discussed in the same breath. Without knowing where KI-66
        #: sits, the phrase gets pinned on whichever in-scope KI happens to be nearby — the same
        #: "meaningless conjunction" that killed the line-scoped design, just at a smaller radius.
        #: ⇒ a status phrase belongs to its NEAREST KI mention, and to no other.
        all_kis = [(mm.start(), mm.group(0)) for mm in re.finditer(r"KI-\d+", line)]
        for ki in closed:
            for m in re.finditer(re.escape(ki) + r"(?![\d])", line):
                lo = max(0, m.start() - RADIUS)
                hi = min(len(line), m.end() + RADIUS)
                window = line[lo:hi]
                c = CONTRA.search(window)
                if not c:
                    continue
                at = lo + c.start()
                # (0) ATTRIBUTION — is THIS KI the nearest one to the phrase? If another KI mention
                #     sits closer, the phrase is about that one and this is a coincidence of
                #     proximity. See the `all_kis` note above for the measured case (KI-65/KI-66).
                nearest = min(all_kis, key=lambda p: abs(p[0] - at), default=None)
                if nearest is not None and nearest[1] != ki:
                    continue
                # (a) dated retraction — an italic parenthetical. REQUIRED: 35 false positives.
                if _enclosed_by(line, at, "*(", ")*", RADIUS * 2):
                    continue
                # (b) the document is QUOTING a past claim rather than making one
                if _enclosed_by(line, at, "“", "”", RADIUS) or _enclosed_by(line, at, '"', '"', RADIUS):
                    continue
                # (c) past tense — dated history is honest; only LIVE claims are the defect
                if PAST.search(window):
                    continue
                out.append((lineno, ki, window[max(0, c.start() - 90): c.end() + 90]))
                break
    return out


# ------------------------------------------------------------------------------------------------
def self_test() -> int:
    """⛔ A GUARD NEVER SEEN TO FAIL IS NOT A GUARD — and this one must be seen NOT to fire, too.
    Arm 4 IS the punch-list item's stated acceptance test."""
    bar = "=" * 96
    print(bar); print("SELF-TEST — probe_promoted_pair.py"); print(bar)
    CLOSED = {"KI-101": "## `KI-101` — … ✅✅ **FIXED, DRIVEN AND PROMOTED TO BOTH FORKS**"}
    OPEN = {"KI-74": "## KI-74 — … STILL OPEN"}

    far = "x" * 2000
    ARMS = [
        ("FAULT: the REAL 2026-09-16 defect — a PROMOTED header vs a live NOT PROMOTED in one cell",
         CLOSED,
         "| drift | ✅ **THE `KI-101` FIX IS PROMOTED, USER-AUTHORISED.** — both files carrying the "
         "`KI-101` fix. ⛔ **NOT PROMOTED — PROMOTION IS THE USER'S CALL**, and this one touches the "
         "most-burned code in the tree.", True),
        ("FAULT: the STILL OPEN variant of the same shape",
         CLOSED,
         "`KI-101` is done and shipped. ⚠ Also note it is STILL OPEN pending a ruling.", True),
        ("PASS: a DATED RETRACTION must NOT fire (this exemption suppressed 35 false positives)",
         CLOSED,
         "✅ `KI-101` IS PROMOTED. *(This clause read “⛔ **NOT PROMOTED — PROMOTION IS THE USER'S "
         "CALL**” — RETRACTED 2026-09-16 once the promotion landed.)*", False),
        ("⭐ ACCEPTANCE (the item's own test): the :386 MEGA-LINE shape — KI numbers ~2,000 chars from "
         "the phrase — must NOT fire",
         CLOSED,
         "`KI-101` shipped and was promoted. " + far + " meanwhile the two drifting FILES are NOT "
         "PROMOTED, which is a separate matter entirely.", False),
        # ⛔ NOTE: scope filtering is `closed_kis`'s job, NOT `violations`'. An arm that hands
        # `violations` a dict directly bypasses the filter and proves nothing about scope — the first
        # draft of this arm did exactly that, "failed", and the failing thing was the TEST. The real
        # scope arms are the `closed_kis` block below. This one keeps only the half `violations` owns.
        ("PASS: an OPEN KI is not in the dict, so nothing to compare",
         {}, "`KI-74` is STILL OPEN and NOT PROMOTED — which is simply true.", False),
        ("PASS: past tense is honest history",
         CLOSED,
         "`KI-101` was NOT PROMOTED until this morning; it is promoted now.", False),
        ("PASS: a quotation is the document describing a past claim",
         CLOSED,
         "`KI-101` is promoted. The old row said “NOT PROMOTED — the user's call” and was wrong.",
         False),
        # ⛔ BOTH ARMS BELOW ARE MEASURED FALSE POSITIVES FROM THE FIRST LIVE RUN, not hypotheticals.
        ("PASS: ATTRIBUTION — the phrase belongs to the NEARER KI (the real :145 KI-65/KI-66 case)",
         {"KI-65": "## KI-65 — ✅✅✅ CLOSED 2026-08-16 (fixed, GATED #25, PROMOTED to both forks)"},
         "`KI-65` is closed and promoted; `KI-66`'s OWNER-filter half is still open and measured INERT.",
         False),
        ("FAULT: attribution must NOT let a real defect escape when the KI *is* the nearest",
         {"KI-65": "## KI-65 — ✅✅✅ CLOSED 2026-08-16 (fixed, GATED #25, PROMOTED to both forks)"},
         "`KI-65` is STILL OPEN, awaiting a decision — while KI-66 is unrelated here.", True),
    ]
    fails = []
    for name, closed, text, want in ARMS:
        got = bool(violations(text, closed))
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}\n          fires={got} expected={want}")
        if not ok:
            fails.append(name)

    # ⛔ SCOPE ARMS — these test `closed_kis`, which is what actually decides who is in scope.
    SCOPE = [
        ("an OPEN header is OUT of scope",
         "## KI-74 — the layout cache (2026-08-13, code-verified, STILL OPEN)", []),
        ("a plain OPEN header is OUT of scope",
         "## KI-77 — camera-range window (2026-08-13, MEASURED LIVE, OPEN)", []),
        ("a PROMOTED header is IN scope (backticked spelling)",
         "## `KI-101` — stale party order (2026-09-16, FIXED, DRIVEN AND PROMOTED TO BOTH FORKS)",
         ["KI-101"]),
        ("a PROMOTED header is IN scope (bare spelling)",
         "## KI-93 — the torment livelock (2026-09-06, ✅ FIXED and PROMOTED)", ["KI-93"]),
        # ⛔ FOUND BY A FAULT ARM BEFORE SHIPPING — see the note in `closed_kis`.
        ("a header that says FIXED *and* NOT PROMOTED is OUT of scope (agreement is not a defect)",
         "## KI-99 — a thing (2026-09-01, FIXED in sandbox, NOT PROMOTED)", []),
        # ⛔ MEASURED FALSE POSITIVE from the first live run — see the MIXED note above.
        ("a self-declared MIXED header is OUT of scope (the real KI-76 case)",
         "## KI-76 — slide model — 🔶 **MIXED: ✅ SAFETY half FIXED; ⚠ CORRECTNESS half UNFIXED**", []),
        ("a 'PARTLY FIXED' header is OUT of scope",
         "## KI-66 — ✅ PARTLY FIXED: the `_on_field` half is FIXED AND PROMOTED", []),
        # ⛔⛔ THE FALSE-NEGATIVE ARM. This header is REAL (KI-95) and it MUST stay in scope: it is a
        #   clean PROMOTED claim whose only "partial" word is about ARCHIVING the document. An
        #   exclusion that swallows it makes the gate miss the exact defect it was built to catch.
        ("‼ 'PARTIALLY ARCHIVED' is about the DOCUMENT and must stay IN scope (the real KI-95 case)",
         "## `KI-95` — ✅ RESOLVED/FIXED, GATED #39, PROMOTED 2026-09-07. ⚠ **PARTIALLY ARCHIVED "
         "2026-09-16: the PREAMBLE moved verbatim to `31-KNOWN-ISSUES-ARCHIVE.md`**", ["KI-95"]),
    ]
    for name, header, want in SCOPE:
        got = sorted(closed_kis(header))
        ok = got == sorted(want)
        print(f"  {'PASS' if ok else 'FAIL'}  SCOPE: {name}\n          closed_kis={got} expected={want}")
        if not ok:
            fails.append("scope: " + name)

    # ⛔ AND THE THRESHOLD ITSELF GETS AN ARM. If RADIUS were widened to line scope, arm 4 — the
    #   measured false positive that killed the first design — would start firing again. Prove the
    #   two populations really are separated by distance, not by luck.
    mega = "`KI-101` ok. " + "y" * 2000 + " the two drifting FILES are NOT PROMOTED."
    wide = RADIUS
    try:
        globals()["RADIUS"] = 10_000          # simulate the line-scoped design
        regressed = bool(violations(mega, CLOSED))
    finally:
        globals()["RADIUS"] = wide
    ok = regressed and not violations(mega, CLOSED)
    print(f"  {'PASS' if ok else 'FAIL'}  the CLAUSE window is what suppresses the mega-line, not luck")
    print(f"          line-scoped(10000) fires={regressed}  clause-scoped({RADIUS}) fires="
          f"{bool(violations(mega, CLOSED))}")
    if not ok:
        fails.append("clause window is not the discriminator")

    print()
    if fails:
        print(f"  ⛔ {len(fails)} arm(s) FAILED: {fails}"); print(bar); return 1
    print("  ✅ all arms behaved: it fires on the real defect and stays silent on all five"); print(bar)
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    bar = "=" * 96
    ki_path, ho_path = K / "05-KNOWN-ISSUES.md", K / "04-HANDOFF.md"
    closed = closed_kis(ki_path.read_text(encoding="utf-8", errors="replace"))
    found = violations(ho_path.read_text(encoding="utf-8", errors="replace"), closed)
    print(bar)
    print("GATE — a CLOSED KI may not be called NOT PROMOTED / STILL OPEN in a live handoff clause")
    print(f"  closed-ish KIs in 05: {len(closed)}   clause window: ±{RADIUS} chars")
    print(bar)
    if not found:
        print("  ✅ no live contradiction found.")
        print("  ‼ This is a WORD-LEVEL check between two files. It cannot tell you a KI is really")
        print("    fixed — only that the two documents do not contradict each other about it.")
        print(bar)
        return 0
    for lineno, ki, ctx in found:
        print(f"  ‼ {ho_path.name}:{lineno}  {ki}")
        print(f"      …{ctx.strip()}…")
    print(bar)
    print(f"  ⛔ {len(found)} live contradiction(s). Fix the stale half, or mark it with a dated")
    print("    retraction `*( … )*` if it is history.")
    print(bar)
    return 1


if __name__ == "__main__":
    sys.exit(main())
