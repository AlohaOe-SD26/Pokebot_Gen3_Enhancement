r"""DOC CONSISTENCY GATE — the docs may not contradict themselves or the code. Exits 1.

WHY THIS EXISTS (2026-08-13, the cold-start audit)
--------------------------------------------------
`04-HANDOFF.md` answered all seven of the handoff quality-bar questions correctly — and its
NEXT-ACTIONS queue still told a fresh agent to BUILD ROOM 3, which the same file's banner reported
as driven and passing, 500 lines up. A KI header said "ARMED for Room 8" while its own body refuted
it. `24-PLAIN-ENGLISH-STATUS.md` — the file `00-README.md` sends cold readers to FIRST — was five
chapters stale. Numeric counts (gates, drift) disagreed across files. Every one of those sat NEXT TO
correct text, which is why no completeness check saw them: **completeness was checked; CONSISTENCY
was not.** Per CLAUDE.md's session-discipline rule 6, anything enforceable belongs in a GATE — this
is that gate, and it is Tier 0 of the DOC CONSISTENCY LAYER directive.

WHAT IT CHECKS (each prototyped against the live tree before being trusted; the design run found
two REAL rot instances on its first sweep — "DRIFT IS ZERO" in 02, and two stale "19 of 24"s):
  C1  GATE-COUNT claims ("17/17 gates", "N-gate suite", "the N needing no ROM", "gated by `X`")
      match `run_gates.py`'s GATES table, parsed via AST — never by counting lines, the table
      holds a multi-line comment.
  C2  DRIFT-COUNT claims match the MEASURED sandbox<->custom drift (byte-compare of ~200 .py
      files, ~0.06s — measuring is CHEAPER than the doc scan, so the gate never trusts the docs'
      own agreement). ‼ TWO PASSES, and the split is deliberate (2026-08-17, `#24-driftassertions`):
      pass 1 grades EXPECTATIONS on fence-stripped text; pass 2 grades CLAIM SHAPE on RAW text —
      currency-marked figures (`N … (LATEST)`, `is <N> again`, `should report N differing`) and
      NEGATIONS evaluated with INVERTED polarity (`not N` is stale precisely when drift IS N).
      ⛔ Pass 2's exemption is SPAN-scoped, never unit-scoped: a STATE table row here runs to
      ~8,000 chars, so one `*(Superseded …)*` would silence the whole page. See `_RETRACT_PAREN`.
  C3  ‼ THE HEADLINE CHECK: no `--driver X` may be queued as WORK-TO-DO in one place and reported
      COMPLETE/PASSING in another, within the same current-state file — unless the stale half is
      explicitly marked superseded. This is the exact defect the audit found.
  C4  LADDER claims ("N of 24 beats") agree with each other (the ladder only grows; any smaller
      numerator is stale).
  C5  ARTIFACT EXISTENCE: every `--driver X` cited in a current-state doc exists in
      `story_harness.py`'s argparse choices (unless its unit says it is the thing to BUILD);
      every cited `ai-research-notes/*.md` / `tools/story-dev/*.py` path exists.
  W1  (WARN only) KI headers whose status words a skimmer would misread against their own body —
      measured at ~4-in-5 false positives, so it is a human worklist, NEVER a failure.
  W2  (WARN only) `04-HANDOFF.md`'s "Last updated:" date vs its own newest git commit date.

DESIGN RULES THIS FILE KEEPS (all measured, none aesthetic):
  * ‼ CURRENT-STATE FILES ONLY may FAIL: 00-05 and 24. `06/07/08/28/31` are APPEND-ONLY HISTORY
    where stale numbers are CORRECT HISTORY — "All 16 gates PASS" in the changelog is a true
    statement about 2026-08-12. Scanning history produces only false positives.
  * ‼ THE SUPERSESSION EXEMPTION IS LOAD-BEARING, not lenience. This project's documented style
    keeps old text visible under markers ("Superseded text:", "*(superseded)*", "⛔ RETRACTED",
    "Older text follows"). A unit carrying one of those markers is EXEMPT — the gate polices
    claims presented as CURRENT, and only those.
  * Fenced code blocks are stripped before scanning (a driver name in an example fired C3 in
    fault-testing until this was added).
  * Tight phrase-bound regexes only. A loose `(\d+) gates?` matched "Route 121 gate" and
    "KI-59 gates the Regi arc"; a loose drift regex captured dates. Precision over coverage —
    a gate with false positives teaches the reader to bypass it (lint_docs' own rule).

FAULT TESTS (CLAUDE.md rule 6 — a gate must prove it fires AND prove it stays quiet):
    PYTHONUTF8=1 py -3.12 audit_doc_consistency.py --self-test
  A: the audit's exact bug reinjected (unmarked "NEXT: BUILD --driver X" beside "X PASS")
     -> MUST fail.  B: the same text marked superseded -> MUST stay quiet.  C: the same text
     inside a code fence -> MUST stay quiet.  D: a wrong gate count / drift count / ladder count
     injected -> MUST fail.  E: a fabricated driver cited as runnable -> MUST fail.
     D9-D18b: the CLAIM-SHAPE rules. ‼ Half of them are FALSE-POSITIVE controls, because this
     corpus carries 67 windows mentioning a drift figure and most are deliberately-preserved
     history — a stale figure QUOTED in prose about the problem (D14), a retraction parenthetical
     (D15) and ordinary English "not one" (D16) must all stay quiet, while D17 proves the
     exemption did NOT regress to unit scope.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 audit_doc_consistency.py
Exit: 0 clean, 1 on any FAIL (warnings never fail the run).
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
DOCS = REPO / "PROJECT KNOWLEDGE"

#: FAIL scope: current-state files only. History files are append-only and stale-by-design.
CURRENT_STATE = [
    "00-README.md", "01-VISION-AND-DESIGN.md", "02-ARCHITECTURE.md",
    "03-PUNCH-LIST.md", "04-HANDOFF.md", "05-KNOWN-ISSUES.md",
    "24-PLAIN-ENGLISH-STATUS.md",
]

FENCE_RE = re.compile(r"```.*?```", re.S)
TOKEN_RE = re.compile(r"--driver\s+([a-zA-Z0-9_]+)")

#: High-precision "this is queued work" vocabulary. `(?<![-\w])BUILD` kills `--build custom`.
BUILD_RE = re.compile(
    r"(?<![-\w])BUILD\b(?!\s+custom|\s+sandbox)"
    r"|\bdoes\s+not\s+exist(?:\s+yet)?\b"
    r"|\bthe\s+thing\s+to\s+(?:write|build)\b"
    r"|\bmust\s+be\s+(?:built|written)\b"
    r"|\bnot\s+(?:yet\s+)?(?:built|written|implemented)\b"
    r"|\bhas\s+not\s+been\s+built\b"
    r"|\bNEXT\s*[:>]", re.I)

DONE_RE = re.compile(
    r"ACCEPTANCE:\s*PASS"
    r"|\bIS\s+DRIVEN\b|\bDRIVEN\s+AND\s+PASSING\b"
    r"|✅\s*\*{0,2}DONE\b|\bDONE\s+\d{4}-\d\d-\d\d\b"
    r"|\bexists\s+and\s+passes\b|\bPASS\s*[x×]\s*\d", re.I)

#: ‼ The exemption that lets this project's keep-old-text-visible style survive the gate.
SUPERSEDE_RE = re.compile(
    r"\(supersed[^)]*\)|Superseded text:"
    r"|⛔\s*\*{0,2}RETRACTED|\bRETRACTED\b|\bIS OBSOLETE\b|\bis retired\b"
    r"|\bOlder (?:text|framing)\b|\bOriginal item follows\b|SUPERSEDED BY|SUPERSEDED 20\d\d"
    # This project's rename-provenance idiom: "THE OLD NAMES SURVIVE ON PURPOSE IN 06/07/08" — a
    # unit explaining that historical names are kept deliberately is DESCRIBING history, not
    # asserting a runnable artifact. Without this, the naming-correction block in 04-HANDOFF
    # (which cites the retired `--driver ch21dive` precisely to say it is retired) false-fires.
    r"|OLD NAMES SURVIVE|SURVIVE[SD]? ON PURPOSE", re.I)

UNIT_RE = re.compile(r"^(?:#{1,6}\s|\s*>?\s*(?:[-*+]\s|\d+[a-z]?\.\s|\|)|\s*$)", re.M)
MAXDIST = 250

#: How close a supersede marker must sit to a GATE-COUNT claim to exempt it (`#24-p4residuals` (g)).
#: ⛔ Deliberately NOT `MAXDIST`: the measured safe band is 40-250, and 250 leaves only an 8-char
#: margin over the nearest false positive, while 120 sits centred. Full measurement — 143 historical
#: commits, 4 true catches / 0 false positives — is in `check_gate_counts.exempt`'s docstring.
GATE_COUNT_SUPERSEDE_MAXDIST = 120


def _read(path: pathlib.Path) -> str:
    return FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), path.read_text(encoding="utf-8", errors="replace"))


def _line(text: str, i: int) -> int:
    return text[:i].count("\n") + 1


def _units(text: str) -> list[tuple[int, int]]:
    starts = sorted({m.start() for m in UNIT_RE.finditer(text)} | {0, len(text)})
    return [(starts[i], starts[i + 1]) for i in range(len(starts) - 1)]


# ---------------------------------------------------------------------------- ground truths
def real_gate_counts() -> tuple[int, int]:
    """(total, fast) from run_gates.py's GATES table, via AST — never by counting lines."""
    tree = ast.parse((REPO / "tools" / "story-dev" / "run_gates.py").read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "GATES":
            elts = node.value.elts
            fast = sum(1 for e in elts if ast.literal_eval(e)[1] is False)
            return len(elts), fast
    raise RuntimeError("GATES table not found in run_gates.py")


def real_driver_choices() -> set[str]:
    src = (REPO / "tools" / "story-dev" / "story_harness.py").read_text(encoding="utf-8-sig")
    m = re.search(r'add_argument\(\s*"--driver".*?choices=(\[[^\]]*\])', src, re.S)
    if not m:
        raise RuntimeError("--driver choices not found in story_harness.py")
    return set(ast.literal_eval(m.group(1)))


def promote_trees() -> tuple[str, ...]:
    """`promote.py`'s TREES tuple, via AST. ‼ The docs quote `promote.py --check`'s OUTPUT, so this
    gate must grade the SAME file set the tool reports. Two hand-maintained tuples that happen to
    agree today is not a guarantee — `D19` in `--self-test` fails if they ever diverge."""
    tree = ast.parse((REPO / "tools" / "story-dev" / "promote.py").read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "TREES" for t in node.targets):
            return tuple(ast.literal_eval(node.value))
    raise RuntimeError("TREES not found in promote.py")


#: ⛔ KEEP IN STEP WITH `promote.py`'s TREES — asserted by `--self-test` D19, not by hope.
_DRIFT_TREES = ("modules", "plugins")


def real_drift() -> tuple[int, list[str]]:
    """MEASURED sandbox<->custom drift. ~0.06s for ~200 files — cheaper than trusting the docs."""
    differing = []
    for sub in _DRIFT_TREES:
        base = REPO / "sandbox-pokebot" / sub
        for p in base.rglob("*.py"):
            rel = p.relative_to(REPO / "sandbox-pokebot")
            q = REPO / "custom-pokebot" / rel
            if not q.exists():
                differing.append(f"MISSING {rel}")
            elif p.read_bytes() != q.read_bytes():
                differing.append(str(rel))
    return len(differing), differing


# ---------------------------------------------------------------------------- checks
#: A line that INVOKES `run_gates.py` and states a count in its trailing shell comment.
#: ‼ ANCHORED ON A REAL INVOCATION — the line must START with a `py`/`python` command. The first
#: draft only required the line to CONTAIN "run_gates.py" plus a `#`, and it immediately produced
#: a FALSE POSITIVE on a punch-list table row where the issue tag `#24-impassabledirs` read as the
#: comment marker and "24" as the count. A gate with false positives teaches the reader to bypass
#: it, which is strictly worse than no gate (CLAUDE.md rule 6) — hence the anchor and the D1f
#: control below. `\d{1,2}` also keeps timings like `~130s` out of the capture.
#: Line 1 of a command: optional `VAR=value` env prefixes, an optional interpreter (`py`, `py3`,
#: `python`, `python3`, with or without a `-3.12`-style flag) or a bare `./`, then `run_gates.py`.
#: ‼ `(?:py|python)[0-9]*` rather than `(?:py|python)\b` — `\b` does NOT match inside "python3",
#: because a trailing digit is itself a word character. That let `python3`/`py3` through.
_RUNGATES_INVOKE = re.compile(
    r"^[ \t]*(?:[A-Za-z_][A-Za-z0-9_]*=\S+[ \t]+)*"
    r"(?:(?:py|python)[0-9]*(?:[ \t]+-[0-9.]+)?[ \t]+|\./)?"
    r"run_gates\.py\b", re.M)

#: A comment-only continuation line — this file wraps long command comments onto them constantly.
_COMMENT_ONLY_LINE = re.compile(r"^[ \t]*#")

#: The count inside a comment. `\d{1,2}` keeps timings like `~130s` out of the capture.
_COUNT_IN_COMMENT = re.compile(r"#[^\n]*?\b(?:all[ \t]+)?(\d{1,2})\b")


def check_gate_count_in_commands(files: dict[str, str]) -> list[str]:
    """‼ A COPY-PASTEABLE COMMAND COMMENT MAY NEVER CARRY A STALE GATE COUNT — no exemptions.

    WHY THIS EXISTS AS A SEPARATE CHECK. `check_gate_counts` above skips any block carrying a
    supersede marker, which is right for PROSE (a superseded sentence is history worth keeping)
    and **wrong for a command**: an agent copies the command and reads the number beside it, and
    the surrounding paragraph's status is irrelevant to that. On 2026-08-14 that gap hid FOUR
    stale counts at once — `04-HANDOFF.md` had `# THE STANDING SUITE — all 21,` (the older regex
    needed the word "gates" immediately after the number, and this line has a comma) and
    `02-ARCHITECTURE.md` had `# THE STANDING SUITE — 18 gates` sitting inside a block whose
    opening `⛔ CORRECTED` banner exempted the whole unit. Two independent blind spots, same shape.

    ⛔ THE APPEND-ONLY HISTORY FILES ARE OUT OF SCOPE by construction — this only ever sees the
    current-state files its caller passes, so an archived transcript quoting "all 17" stays legal.

    ‼‼ **IT MUST BE HANDED *RAW* TEXT, NOT `_read()`'s OUTPUT.** `_read()` blanks every ```-fence
    so the other checks do not fire on example text — but a runnable command lives INSIDE a fence,
    so fence-stripped input makes this check permanently blind. That is not hypothetical: the
    first version was wired to the stripped text, its 6-case self-test passed in both directions,
    and it **did not fire on a live re-injection of the real 18-gate bug**. Identical in shape to
    the P2 check's 2026-08-14 failure — *a self-test that exercises the DECISION and bypasses the
    PARSING proves nothing.* The self-test now includes a genuinely fenced case (D1h).
    """
    total, fast = real_gate_counts()
    out = []
    for name, text in files.items():
        lines = text.splitlines()
        for index, raw_line in enumerate(lines):
            if not _RUNGATES_INVOKE.match(raw_line):
                continue
            # ‼ THE COMMENT MAY WRAP. This file routinely continues a command's comment onto the
            # next `#`-only line, so the count is not always on the invocation line. An adversarial
            # probe demonstrated that as a live bypass — and one reformat away from hiding on this
            # check's own flagship example. Scan the invocation line PLUS its comment-only tail.
            block = [raw_line]
            for follower in lines[index + 1:]:
                if not _COMMENT_ONLY_LINE.match(follower):
                    break
                block.append(follower)
            found = _COUNT_IN_COMMENT.search("\n".join(block))
            if not found:
                continue                      # a command with no count claims nothing. Stay quiet.
            # ‼ `--quick` runs only the no-ROM subset, so its comment must be graded against the
            # FAST count. Grading it against the total was this check's second false positive
            # (caught live on `# the 14 needing no ROM`, where 14 was stale but 22 was never the
            # right answer either) — comparing against the wrong truth is still a broken check.
            quick = "--quick" in raw_line
            expected = fast if quick else total
            if int(found.group(1)) != expected:
                # ‼ The line number is the INVOCATION's (`index + 1`), not a match offset: `found`
                # matched against the joined block, so its offset means nothing in `text`.
                out.append(
                    f"{name}:{index + 1} is a RUNNABLE `run_gates.py"
                    f"{' --quick' if quick else ''}` command whose comment says {found.group(1)}; "
                    f"the {'no-ROM subset' if quick else 'suite'} has {expected}. ‼ No supersede "
                    f"marker exempts a command line: {raw_line.strip()[:90]!r}")
    return out


def check_gate_counts(files: dict[str, str]) -> list[str]:
    total, fast = real_gate_counts()
    # ‼‼ MARKDOWN EMPHASIS BETWEEN THE WORD AND THE NUMBER, ADDED 2026-08-17. `all **25** gates PASS`
    # was invisible to `\ball\s+(\d{1,2})\s+gates?` because `**` sits between `all ` and the digits —
    # and a Tier 2 cold-start audit found THREE such sites, one of them in the first paragraph of the
    # orientation block, in a file that four lines lower records "25" as an already-caught defect.
    # ⇒ Every number in this check now tolerates the `**`/`__` the docs bold their figures with.
    B = r"[*_]{0,2}"
    claims = re.compile(
        rf"{B}(\d{{1,2}}){B}\s*/\s*{B}(\d{{1,2}}){B}\s+gates?\b"
        r"|\bsuite\s+is\s+now\s+(\d{1,2})\b"
        # ‼ ADDED 2026-08-17 — THE SAME CLAIM-SHAPE BLIND SPOT THE DRIFT RULE HAD, in the check
        # right next to it. The rule above demands the word "now", so `the suite is 25 gates`
        # sailed straight through; a Tier 1 reviewer found it FOUR LINES above a correct
        # `26/26 gates PASS` in the same file. ⇒ A count claim does not need "now" to be a claim.
        rf"|\bsuite\s+is\s+{B}(\d{{1,2}}){B}\s+gates?\b"
        # `it has said 17, 18 … on its way to **25**` — a claim about the CURRENT total dressed up
        # as a history. The trailing figure is the one actually being asserted, and it went stale
        # while the very same file carried a correct `26/26` 480 lines away.
        r"|\bon its way to\s+\*{0,2}(\d{1,2})\b"
        rf"|\bALL\s+{B}(\d{{1,2}}){B}\s+GATES\b"
        rf"|\b{B}(\d{{1,2}}){B}[- ]gate\s+suite\b"
        r"|STANDING\s+SUITE\s*[—-]+\s*(?:all\s+)?(\d{1,2})\s+gates?"
        rf"|\ball\s+{B}(\d{{1,2}}){B}\s+gates?\s+PASS\b"
        # ‼ ADDED 2026-08-22 — a SEVENTH phrasing, found by a Tier 1 reviewer, not by this gate.
        # `04-HANDOFF.md:51` read "**both must exit 0; the suite is 28 gates**" and stayed stale
        # while line 57 — SIX LINES BELOW IT — was correctly updated to 29 in the same commit. Every
        # other phrasing in this file was added the same way: after it went stale undetected. ⇒ when
        # you change a count, the honest assumption is that this regex does not yet know your
        # sentence. *(Prior stale-phrasing incidents: a NOUN between subject and verb; digits
        # wrapped in markdown bold; "0 as of"; the word "zero" spelled out.)*
        rf"|\bthe\s+suite\s+is\s+{B}(\d{{1,2}}){B}\s+gates?\b", re.I)
    fastc = re.compile(r"\bthe\s+(\d{1,2})\s+needing\s+no\s+ROM\b", re.I)
    gated = re.compile(r"(?:gated\s+by|GATED\s+as|new\s+gate)\s+`?([a-z0-9_]+\.py)`?", re.I)
    out = []
    for name, text in files.items():
        units = _units(text)
        def exempt(i):
            """A supersede marker exempts a gate-count claim only if it is NEAR it.

            ‼‼ `#24-p4residuals` (g). This used to accept a marker ANYWHERE IN THE UNIT, and units
            here are big: measured across the 7 live docs, n=1543, median 216 chars, **max 30,945**,
            and the 41 units that actually carry a marker have a median of 1,084. So one "older
            framing" buried in a long annotated block exempted every number in it — including live
            orientation instructions. MEASURED CONSEQUENCE: `04-HANDOFF.md:51` read "the suite is 28
            gates" six lines above a correct 29 and this gate stayed SILENT. A human reviewer caught
            it; the check structurally could not.

            ⛔ THE OBVIOUS FIX WAS REFUTED BY MEASUREMENT. Porting the DRIFT check's span exemption
            (`_RETRACT_PAREN`, median 15 chars) looks right and is wrong twice: spans are tiny, and
            the drift port requires the marker to PRECEDE the claim — while this corpus writes
            gate-count retractions AFTER the figure ("…17/17 gates PASS. Original item follows.").
            Over 143 historical commits the span port produced a FALSE POSITIVE and failed 2 of 7
            fault cases. "Same line only" was also measured: strictly worse, it loses a true catch.

            ⇒ KEEP UNIT SCOPE, ADD DIRECTION-AGNOSTIC PROXIMITY. Measured over those 143 commits:
            **4 TRUE-STALE caught, 0 FALSE POSITIVES, 0 findings lost, 0 on the live tree**, and the
            reinjected `04-HANDOFF.md` defect is caught. The safe band is 40–250 (the nearest false
            positive's marker sits +36; the tightest true catch's nearest marker +258); 120 is
            centred, which is why it is not `MAXDIST`'s 250 — that leaves only an 8-char margin."""
            for a, b in units:
                if a <= i < b:
                    for mk in SUPERSEDE_RE.finditer(text[a:b]):
                        if abs((a + mk.start()) - i) <= GATE_COUNT_SUPERSEDE_MAXDIST:
                            return True
                    return False
            return False
        for m in claims.finditer(text):
            nums = [int(g) for g in m.groups() if g]
            if any(n != total for n in nums) and not exempt(m.start()):
                out.append(f"{name}:{_line(text, m.start())} claims {'/'.join(map(str, nums))} "
                           f"gates; run_gates.py has {total}: {m.group(0)!r}")
        for m in fastc.finditer(text):
            if int(m.group(1)) != fast and not exempt(m.start()):
                out.append(f"{name}:{_line(text, m.start())} claims {m.group(1)} no-ROM gates; "
                           f"real fast count is {fast}")
        for m in gated.finditer(text):
            script = m.group(1)
            if script.startswith(("repro_", "probe_", "audit_", "lint_", "verify_", "preflight")):
                src = (REPO / "tools" / "story-dev" / "run_gates.py").read_text(encoding="utf-8-sig")
                if f'"{script}"' not in src and not exempt(m.start()):
                    out.append(f"{name}:{_line(text, m.start())} says {script} is a gate; it is "
                               f"not in run_gates.py's GATES table")
    return out


#: ‼ SPELLED-OUT NUMBERS COUNT. A drift figure written as a WORD ("exactly THREE differing") went
#: stale for a day in TWO places — including inside the copy-run HOW TO RUN / TEST block — and this
#: check could not see either, because every pattern demanded `\d`. Two separate cold-start audits
#: had to find them by eye. Words are now first-class, and the docs additionally say "digits, not
#: words" at both sites so the next author does not reintroduce the blind spot.
_WORD_NUMBERS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_NUM = r"\d{1,2}|" + "|".join(_WORD_NUMBERS)

#: ‼ NOT part of a longer token. Without these lookarounds the `(LATEST)` rule below captured the
#: `17` out of `as of 2026-08-17 (LATEST)` and reported a claim of "drift=17".
_N = rf"(?<![\w\-.])({_NUM})(?![\w\-.])"

#: ⛔⛔ CLAIM-SHAPE DETECTION (2026-08-17, `#24-driftassertions`; ruling in `06-DECISIONS-LOG.md`).
#: THREE stale drift claims survived hand sweeps AND this gate, each caught by a different audit
#: agent, because the 2026-08-16 rule is scoped to the `expect` vocabulary and all three were
#: ASSERTIONS. ‼ The fix is NOT "check every number near the word drift": that was MEASURED over the
#: live corpus at **67** candidate windows, and the overwhelming majority are deliberately-preserved
#: history ("took drift to 0 AT THAT MOMENT", "0 as of 2026-08-15 (earlier)"). A gate that
#: red-flags the docs' own history is bypassed within a day — this project's rule 6.
#:
#: ⇒ THE RULE IS **MARKER ATTACHMENT**: a figure asserts something about TODAY only when a currency
#: marker is attached to the NUMBER ITSELF. Anchoring on LOCATION was rejected for the same reason
#: (the STATE table's drift cell deliberately carries several dated historical figures inline).
_CURRENCY = re.compile(
    # `✅ **0 as of 2026-08-16 (LATEST) — EVERYTHING IS PROMOTED**` — the STATE-cell idiom. VERBATIM
    # the claim that went stale unseen on 2026-08-16 while three other sites had been corrected.
    rf"{_N}[^\n]{{0,40}}?\(LATEST\)"
    # …and the same marker written the other way round, which is how the HOW TO RUN block spells it:
    # `# Expect as of 2026-08-17 (LATEST): 0 differing, 0 orphaned`.
    rf"|\(LATEST\)[^\n]{{0,24}}?{_N}"
    # `✅ **AND IT IS ZERO AGAIN as of 2026-08-17**` / `it is **1** again as of 2026-08-17` — the
    # 60-second-version and punch-list idioms. Both went stale unseen the same day. `again` is the
    # currency marker: it asserts a RETURN to a value, which is a statement about now.
    rf"|\bis\s*[*_]{{0,2}}\s*({_NUM})[*_]{{0,2}}\s+again\b"
    # `so promote.py --check should report **0 differing, 0 orphaned**` — 04-HANDOFF's second STATE
    # row states its live figure this way, which carries no `expect` token and no `(LATEST)`.
    # ⛔ PRESENT TENSE ONLY: `reported N differing` is a past measurement and must stay quiet.
    rf"|\b(?:should\s+report|reports)\s+[*_]{{0,2}}({_NUM})\s*[*_]{{0,2}}\s*differing\b", re.I)

#: ⛔ EVALUATED WITH INVERTED POLARITY — `drift is NOT n` is stale precisely when drift IS n.
#: MEASURED 2026-08-17: the shipped gate was blind to EVERY negation phrasing at BOTH drift values
#: (0 and 1), and so was every other `check_*` in this file — so the STATE row's record of a "false
#: positive on NOT ZERO" was false of the code, and its advice to "phrase the caveat carefully" was
#: steering authors INTO the blind spot. Never pattern-match the token; evaluate the claim.
_NEGATED = re.compile(rf"\bno(?:t|\s+longer)\s*[*_]{{0,2}}\s*{_N}", re.I)

#: The thing a figure can be a figure OF. ‼ Required within `_SUBJECT_WINDOW` chars of the match —
#: PROXIMITY, not "somewhere in the unit". MEASURED: unit scope produced two false positives on
#: ordinary English immediately, `"there are TWO unbound reads, not one"` and a bare `not 0`, in
#: units that merely mentioned drift elsewhere. Every real claim keeps its subject close: the
#: STATE cell writes `| sandbox ↔ custom drift | ✅ **0 as of …`, and the 60-second version wrote
#: `took drift to 0 AT THAT MOMENT. ⚠ **NOT ZERO as of 2026-08-17**`.
_DRIFT_SUBJECT = re.compile(r"\bdrift\b|\bdiffering\b|promote\.py\s+--check", re.I)
_SUBJECT_WINDOW = 90

#: Spans that QUOTE a figure rather than assert it — this file is now full of prose ABOUT stale
#: figures, and the gate red-flagged the original draft of the punch-list bullet describing them.
#: ‼ SPAN-based, never unit-based: the 60-second bullet carries a CURRENT claim and a QUOTED stale
#: one in the SAME unit, so exempting the unit would blind the gate to the half that matters.
#: ⛔ Applied to the TWO NEW RULES ONLY. The `expect` rule must keep seeing backticked figures —
#: the live HOW TO RUN line writes its expectation as `` `0 differing, 0 orphaned` ``.
_QUOTED = re.compile(r'"[^"\n]{0,300}"|“[^”\n]{0,300}”|`[^`\n]{0,300}`')

#: ⛔⛔ WHY THE NEW RULES DO **NOT** USE THE UNIT-LEVEL SUPERSEDE EXEMPTION — MEASURED 2026-08-17.
#: `04-HANDOFF.md`'s STATE drift cell is ONE markdown table row of **7,916 characters**, and it
#: carries a `*(Superseded …)*` parenthetical **283 chars** from its live `0 as of … (LATEST)`
#: claim. Unit-scoped exemption therefore silences the single most authoritative site in the tree —
#: the cell a cold start reads — along with `:168`'s live `0 differing, 0 orphaned` (marker 1,440
#: chars away). ⇒ ⛔ **THE EXEMPTION MUST BE SPAN-SCOPED, NOT UNIT-SCOPED**, or the gate is blind
#: exactly where it is needed. The three spans below are how this project actually writes a
#: withdrawn figure; `_near_marker` keeps the `Superseded text: **DRIFT IS ZERO AGAIN…**` prefix
#: idiom working without reaching across a 7,916-char row.
#: ‼ INNERMOST parentheticals only (`[^()\n]`): the live "AND IT IS ZERO AGAIN" claim sits inside an
#: OUTER `*( … )*` that also encloses a retraction, so an outermost match would exempt it too.
#: ‼ `*( … )*` FIRST — this project's own aside idiom, and it is the form that nests. Matching only
#: innermost `( … )` missed `*(Superseded: this cell read **N as of … (LATEST)** until …)*` entirely,
#: because `(LATEST)` sits inside it. Both forms are line-bounded and non-greedy: no backtracking.
_RETRACT_PAREN = re.compile(r"\*\([^\n]{0,800}?\)\*|\([^()\n]{0,600}\)")

#: Reported speech — "this line READ X UNTIL …", "BRIEFLY read", "SURVIVED a sweep". Applied ONLY
#: inside a parenthetical, which is where this project keeps its withdrawn figures visible.
_REPORTED = re.compile(
    r"\bread\b|\bsaid\b|\bclaim(?:ed|s|ing)?\b|\bbriefly\b|\buntil\b|\bpreviously\b|\bsurvived\b"
    r"|\bstale\b|\bwas true\b|\bhistorical\b|\bat that (?:moment|time)\b|\bformerly\b", re.I)

#: ⛔⛔ A RETRACTION MARKER GOVERNS TO THE END OF ITS SENTENCE — NOT A RADIUS. Both replaced rules
#: were BYPASSES found by an adversarial review and REPRODUCED before fixing:
#:   * a plain aside containing the ordinary words "read"/"until" exempted a live wrong figure
#:     sitting BEFORE them — `(as of …, the figure is 3 again — you can read the drift log until …)`;
#:   * a 120-char proximity window exempted a live claim because a marker retracting a DIFFERENT,
#:     EARLIER number sat nearby — `Drift was 5 (superseded), then corrected; … is 3 again`.
#: ⇒ Two rules, both claim-bound rather than neighbourhood-bound: the marker must PRECEDE the figure
#: it retracts, and outside a parenthetical it stops at the sentence break. Guarded by D20/D21.
#: ‼ `|` counts as a break: a STATE table row is one line, and each cell is its own statement.
_SENTENCE_BREAK = re.compile(r"[;!?\n|]|\.\s")
_SENTENCE_LOOKBACK = 400


def check_drift(files: dict[str, str], raw: dict[str, str] | None = None) -> list[str]:
    """`files` is fence-STRIPPED (legacy rules); `raw` keeps fences (the CLAIM-SHAPE rules).

    ‼ THE SPLIT IS DELIBERATE AND MEASURED. `_read()` blanks fenced blocks, and the HOW TO RUN
    block — one of only two sites `#24-driftassertions` says MAY carry a digit — states its figure
    INSIDE a fence (`# Expect as of <date> (LATEST): 0 differing, 0 orphaned`). The gate could not
    see the very line it is supposed to police. The legacy rules stay on stripped text because
    their phrasings recur in example commands; the new rules need the fences and pay for it with
    the quotation exemption (a fenced comment quotes `"Drift is 1"` as a past incident).
    """
    measured, _ = real_drift()
    claims = re.compile(
        # ‼ THE OPTIONAL NOUN, ADDED 2026-08-17. `The sandbox→custom drift FIGURE is 0` slipped past
        # for a day — the old rule demanded `drift` and `is` be ADJACENT — and a Tier 2 audit found
        # that phrasing sitting in the orientation block a cold reader is ORDERED to read first,
        # telling it nothing awaited a promotion while a promotion decision was in fact owed.
        rf"\bdrift\s+(?:figure\s+|count\s+|number\s+)?is\s+(?:now\s+|still\s+)?(?:exactly\s+)?({_NUM})\b"
        rf"|\bEXPECT\s+EXACTLY\s+({_NUM})\b"
        rf"|\bexpect(?:ed)?\s+(?:as of [^:]{{0,24}}:\s*)?exactly\s+({_NUM})\b"
        rf"|\bdrift\s+(?:unchanged\s+|measured\s+)?at\s+(?:exactly\s+)?({_NUM})\b"
        rf"|\bDRIFT\s+IS\s+({_NUM})\b"
        # ‼‼ THE NO-VERB, MARKUP-WRAPPED SHAPE — ADDED 2026-08-27 BY THE DEEP SANITY CHECK, WHICH
        # FOUND A LIVE STALE INSTANCE THIS GATE WAS GREEN OVER. `04-HANDOFF.md`'s State banner read
        # `drift **2** (...)` while the measurement was 8: every rule above demands a VERB or marker
        # between `drift` and the figure (`is`, `at`, `EXPECT`, `differing`, `it is N today`), and a
        # bare `drift **N**` matches none of them. ⛔ THE MARKUP IS REQUIRED, deliberately: a rule
        # for bare `drift 2` would fire on ordinary prose ("drift 2 files were promoted"), while
        # `drift **N**` is this project's own emphasis idiom for a CLAIM. Guarded by D29a-D29c.
        rf"|\bdrift\s+[*_]{{1,2}}({_NUM})[*_]{{1,2}}"
        rf"|\b({_NUM})\s+drifted\s+files?\b"
        # ‼‼ THE TOOL'S OWN OUTPUT FORMAT, ADDED 2026-08-16 — AND IT WAS THIS CHECK'S BLIND SPOT.
        # `promote.py --check` prints "N differing, M orphaned", so the docs quote THAT phrasing far
        # more often than "drift is N" — and none of the patterns above matched it. A stale
        # `0 differing` survived a 13-site hand sweep AND this gate, and an adversarial review had to
        # find it. Adding this rule then immediately surfaced THREE MORE the same sweep had missed,
        # all buried in very long STATE-table rows.
        # ⛔ SCOPED TO AN *EXPECTATION* ON PURPOSE (`expect`/`expects`/`expected` within ~70 chars).
        # A bare "N differing" also appears in HISTORICAL measurements ("compared afterwards: 0
        # differing, 0 missing" — 02-ARCHITECTURE), which are CORRECT and must stay quiet; flagging
        # those would make this gate noisy, and a noisy gate gets bypassed. **An EXPECTATION is a
        # claim about NOW; a measurement is a claim about THEN.** D8 below fault-tests exactly that.
        rf"|\bexpect(?:ed|s)?\b[^.\n]{{0,70}}?({_NUM})\s+differing\b"
        # ‼‼ `IT IS <N> TODAY` — ADDED 2026-08-17, AND IT HID A STALE FIGURE PAST A GREEN GATE.
        # This project's idiom for pinning a HISTORICAL promotion beside the CURRENT figure is
        # "drift was 0 at that point *(⚠ It is **4** today for UNRELATED sandbox-only files)*".
        # The subject word `drift` is in the sentence, so the ~90-char subject window is satisfied —
        # but no rule above matches "it is N today", because every one of them wanted the digit
        # ADJACENT to `drift`/`differing`. THREE such sites (two in `05-KNOWN-ISSUES.md`, one in
        # `03-PUNCH-LIST.md`) sat stale at 4 while the same session corrected every other site to 5,
        # and `run_gates.py` reported 27/27 over them. An independent Tier 1 reviewer found them.
        # ⇒ The pronoun carries the subject, so the RULE must carry it: unlike the `_CURRENCY` pass,
        # this pass does NOT apply `_DRIFT_SUBJECT`, so a bare `it is N today` would fire on any
        # sentence in the tree (D26d proved it — my first draft failed its own false-positive test).
        # ⛔ The gap is `[^\n]{0,200}` and NOT `[^.\n]`: both real sites put a SENTENCE BREAK between
        # the subject and the pronoun ("drift was 0 at that point.** *(⚠ It is **4** today …"), so a
        # period-excluding gap — the idiom every other rule here uses — matches neither of them.
        # ⛔ `\*{0,2}` because the figure is written both `**4** today` and `**4 today`.
        # Guarded by D26 / D26b / D26c / D26d, which test both signs.
        # ⛔ TWO CORRECTIONS, 2026-08-17 pass 2, both REPRODUCED by an agent before being fixed:
        #  (a) the subject was `(?:drift|differing)`, and the bare English word "differing" fired on
        #      prose with nothing to do with fork sync ("The two approaches keep differing … It is 1
        #      today by an unrelated clock"). This pass deliberately skips `_DRIFT_SUBJECT`, so the
        #      subject has to be carried by the PATTERN — and only `drift` actually means it.
        #  (b) the gap was `[^\n]` and so could not cross a line break, which hid the claim whenever
        #      this project's prose wrapped — which it does constantly. `[\s\S]` crosses, still
        #      bounded at 200 chars (~2 lines) so it cannot reach an unrelated paragraph.
        rf"|\bdrift\b[\s\S]{{0,200}}?\bit\s+(?:is|was)\s+\*{{0,2}}({_NUM})\*{{0,2}}\s+today\b",
        re.I)
    out: list[str] = []

    def value(m: re.Match) -> int:
        tok = next(g for g in m.groups() if g)
        return _WORD_NUMBERS[tok.lower()] if tok.lower() in _WORD_NUMBERS else int(tok)

    # ‼ CROSS-PASS DEDUP. The two passes read DIFFERENT texts (stripped vs raw), so their offsets
    # are not comparable — line numbers are. Measured: the project's own HOW TO RUN idiom,
    # `Expected as of <date> (LATEST): 0 differing`, matches a legacy rule AND a currency rule, and
    # was reported twice for one edit site. One claim, one finding; a gate that inflates its own
    # FAIL count trains the reader to skim it.
    seen: set[tuple[str, int, int]] = set()

    def report(name: str, text: str, m: re.Match, n: int, how: str) -> None:
        key = (name, _line(text, m.start()), n)
        if key in seen:
            return
        seen.add(key)
        out.append(f"{name}:{key[1]} {how} drift={n}; MEASURED drift is "
                   f"{measured}: {m.group(0)!r}")

    # ---- PASS 1: the legacy rules, on fence-stripped text.
    # ⛔ THE EXEMPTION IS POSITIONAL AS OF 2026-08-27 (deep sanity check). It used to be
    # UNIT-SCOPED: one `Superseded:` anywhere in a bullet silenced EVERY claim in it, including
    # claims written AFTER the marker — and that is how a stale `drift **2**` sat green in
    # `04-HANDOFF.md`'s State banner. Pass 2 already had the right rule ("a marker only retracts
    # what FOLLOWS it", see `_RETRACT_PAREN`); pass 1 now matches it. Guarded by D30a/D30b.
    for name, text in files.items():
        units = _units(text)
        for m in claims.finditer(text):
            n = value(m)
            unit = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
            # ⛔ A MARKER RETRACTS WHAT FOLLOWS ITS **START**, not what follows its end — and the
            # difference is not academic: the tree's commonest retraction is a PARENTHETICAL that
            # CONTAINS its claim, `(superseded: *drift is now 3 again*)`. Truncating the search at
            # the claim cuts that parenthetical in half, `SUPERSEDE_RE` (which needs the closing
            # paren) stops matching, and the retraction reads as a live claim — a false positive,
            # which this project rates worse than no gate. Caught by measuring against the live
            # tree before shipping this change; guarded permanently by D30b.
            exempt = any(
                unit[0] + mk.start() < m.start()
                for mk in SUPERSEDE_RE.finditer(text[slice(*unit)])
            )
            if n != measured and not exempt:
                report(name, text, m, n, "claims")

    # ---- PASS 2: the CLAIM-SHAPE rules (2026-08-17). Raw text so fenced figures are visible;
    # gated on a drift SUBJECT in the unit; exempted by SPAN, never by unit — see `_RETRACT_PAREN`.
    for name, text in (raw if raw is not None else files).items():
        units = _units(text)
        quoted = [(q.start(), q.end()) for q in _QUOTED.finditer(text)]
        # (start, end, offset of the FIRST retraction word) — a marker only retracts what FOLLOWS it.
        retracted = []
        for p in _RETRACT_PAREN.finditer(text):
            mk = SUPERSEDE_RE.search(p.group(0)) or _REPORTED.search(p.group(0))
            if mk:
                retracted.append((p.start(), p.end(), p.start() + mk.start()))

        def exempt_span(i: int, soft: bool = True, text: str = text) -> bool:
            """`soft=False` ⇒ only an EXPLICIT retraction silences this claim.

            ⛔⛔ WHY THE SOFT/HARD SPLIT (2026-08-17, found by a Tier 2 cold-start audit that
            MEASURED the figures instead of reading them). A single parenthetical here routinely
            carries a HISTORICAL clause and a CURRENT one:
                `… which took drift to 0 AT THAT MOMENT. ✅ AND IT IS ZERO AGAIN as of 2026-08-17`
            The soft marker `AT THAT MOMENT` sat **20 characters** before the live claim, so
            "a marker exempts what follows it" silenced the half that was actually asserting
            something about today — and that claim then went stale unseen, which is the FOURTH
            staleness incident on this exact line.
            ⇒ **An explicit CURRENCY marker outranks soft history vocabulary.** Only SUPERSEDE_RE —
            "Superseded", "RETRACTED", an explicit withdrawal — can silence a currency-marked claim.
            The soft `_REPORTED` list keeps its power over NEGATIONS, which really are usually
            quoted prose about the problem.
            """
            if any(a <= i < b for a, b in quoted):
                return True
            for a, b, mk in retracted:
                if a <= i < b and mk < i:
                    if soft or SUPERSEDE_RE.search(text[a:b]):
                        return True
            # Outside a parenthetical, a marker governs only to the end of ITS sentence.
            lo = max(0, i - _SENTENCE_LOOKBACK)
            breaks = list(_SENTENCE_BREAK.finditer(text, lo, i))
            start = breaks[-1].end() if breaks else lo
            return bool(SUPERSEDE_RE.search(text[start:i]))

        for rx, negated in ((_CURRENCY, False), (_NEGATED, True)):
            for m in rx.finditer(text):
                near = text[max(0, m.start() - _SUBJECT_WINDOW):m.end() + _SUBJECT_WINDOW]
                # ‼ `soft=negated`: a CURRENCY-marked figure is only silenced by an EXPLICIT
                # retraction; a negation may also be silenced by reported-speech vocabulary.
                if not _DRIFT_SUBJECT.search(near) or exempt_span(m.start(), soft=negated):
                    continue
                n = value(m)
                # ‼ POLARITY. A plain claim is stale when it DISAGREES with the measurement; a
                # NEGATION is stale when it AGREES with it ("NOT ZERO" while the figure is zero).
                if (n == measured) if negated else (n != measured):
                    report(name, text, m, n, "denies" if negated else "claims")

    # ---- PASS 3: the STATE-table drift row's HEADLINE (`#24-driftheadlineshape`, 2026-08-26).
    # WHY: on 2026-08-24 the drift cell listed THREE files while its headline still said 2 — the
    # body was right, the half that gets SKIMMED was wrong, and no pattern above matches
    # `**N as of <date>` (they want `drift is`, `differing` near an expectation, or `it is N
    # today`). A Tier 1 reviewer caught it; this file's own blind spot, now closed.
    # ‼ SCOPING IS POSITIONAL, NOT VOCABULARY. The cell's own documented convention is "today's
    # number is at the TOP of this cell; everything after it is history" — so the rule reads ONLY
    # THE FIRST `N as of <date>` in a drift-labelled table row and compares it to the measurement.
    # Historical figures deeper in the cell (`Previously 0 as of…`, `ZERO as of…`) are exempt by
    # POSITION — a DECLARED convention, not an inferred one (the 2026-08-23 lesson: an exemption
    # keyed on co-occurring words like `historical` is a hole; a position rule cannot be faked).
    # ⛔ Runs on the fence-STRIPPED text: a drift row quoted inside a fenced example must not fire
    # (D28e), and the real row is never fenced.
    drift_row = re.compile(r"^\|[^|\n]*\bdrift\b[^|\n]*\|(.*)$", re.I | re.M)
    # ⛔ `[*_]{0,2}` AFTER THE FIGURE — added 2026-08-27 (deep sanity check, proven BOTH ways in
    # process). Without it, an individually-bolded headline (`**9** as of <date>`) does not match,
    # so a WRONG headline goes unseen AND the scan falls through to a HISTORY figure deeper in the
    # cell and grades that instead — a false positive, which this project rates worse than no gate.
    # The idiom is real here (`It is **4** today`). Guarded by D28f/D28g.
    headline = re.compile(rf"\b({_NUM})\b[*_]{{0,2}}\s+as\s+of\s+\d{{4}}-\d{{2}}-\d{{2}}", re.I)
    for name, text in files.items():
        for row in drift_row.finditer(text):
            # pos/endpos so the match's offsets are ABSOLUTE in `text` — report() derives the
            # line number and the dedup key from m.start(), which a group-relative search breaks.
            m = headline.search(text, row.start(1), row.end(1))
            if m is None:
                continue
            n = value(m)
            if n != measured:
                report(name, text, m, n, "drift-row HEADLINE (first `N as of <date>` in the cell)")
    return out


#: ‼‼ PROMOTION-STATE PROSE — ADDED 2026-08-17, AND IT IS A DIFFERENT BLIND SPOT FROM `check_drift`.
#: `check_drift` grades FIGURES. It cannot see a sentence that says, in words, that work is still
#: waiting to be promoted. On the day five files were promoted, `check_drift` went green over
#: `05-KNOWN-ISSUES.md`'s KI-79 (*"⚠ SANDBOX-ONLY; a promotion is the USER's call"*, and *"gate #26
#: … FAILS against the unpromoted `custom` tree"*) and KI-81 (*"a RATCHET at baseline 36 (sandbox) /
#: 44 (custom, until the guards are promoted)"*) — all describing the work that had just gone over.
#: A Tier 1 reviewer found them. ⇒ **A cold agent reading those would believe a promotion decision
#: was still owed and re-litigate finished work** — the exact cost this layer exists to prevent.
#: ⛔ SCOPED TO drift == 0. When something genuinely IS sandbox-only the phrase is CORRECT and must
#: stay silent, so this rule only speaks when the tree says everything is promoted.
_PROMO_PENDING = re.compile(
    r"SANDBOX[- ]ONLY\s*[;:,—-]?\s*(?:and\s+)?(?:a\s+)?promotion\s+is\s+the\s+USER'?s?\s+call"
    r"|awaiting\s+a\s+user[- ]approved\s+promotion"
    r"|a\s+PROMOTION\s+DECISION\s+IS\s+OWED"
    # Both word orders occur in this tree; a Tier 2 audit found the second one live.
    r"|OWES?\s+A\s+PROMOTION\s+DECISION"
    r"|until\s+the\s+\w+\s+are\s+promoted"
    r"|against\s+the\s+unpromoted\s+`?custom`?\s+tree",
    re.I)
#: ⛔ WHAT THIS RULE DELIBERATELY DOES **NOT** MATCH, and why — say the limit rather than imply
#: coverage. A bare `sandbox-only` is NOT a claim shape: it appears legitimately all over the
#: history blocks ("promoted 2026-08-16; it was sandbox-only until then"), and matching it would
#: make this gate noisy enough to be bypassed — which is the one failure mode worse than the bug.
#: A Tier 2 audit found one such bare instance (`… COMMENT-ONLY cap correction), all sandbox-only.`)
#: that this rule cannot see. ⇒ **Prose sweeps still need a human or an agent; this gate catches the
#: FIVE unambiguous phrasings above, not every way English can say "not promoted yet".**


def check_promotion_prose(files: dict[str, str]) -> list[str]:
    """When drift is 0, no current-state file may say work is still WAITING to be promoted.

    ‼ This is the PROSE twin of `check_drift`, which only ever graded numbers. Both are needed:
    the figure and the sentence go stale independently, and on 2026-08-17 the figure was swept
    correctly to 0 while two KI entries kept telling readers a promotion was still owed.

    ⛔ EXEMPTIONS, because a noisy gate gets bypassed: a quoted/retracted span (this file is full of
    prose ABOUT stale claims), and any line that also carries an explicit PROMOTED marker — that is
    how a corrected entry reads once it records its own history.
    """
    measured, _ = real_drift()
    if measured != 0:
        return []  # the phrase is TRUE when something really is unpromoted
    out: list[str] = []
    for name, text in files.items():
        # ⛔⛔ QUOTED SPANS ARE EXEMPT — and this was NOT optional. The first draft of this rule
        # fired on TWO of its own kind of text: a `Historical note, superseded: *"Sandbox only —
        # promotion is the USER's call"*` and the retraction I had just written recording the old
        # wording verbatim. **A gate that fires on the document DESCRIBING the problem teaches the
        # reader to bypass it, which is strictly worse than no gate** (CLAUDE.md, rule 6). Spans are
        # computed over the WHOLE text because this project's prose wraps mid-quote.
        # ⛔ A LOCAL quoted-span regex that CROSSES NEWLINES. The shared `_QUOTED` forbids `\n`
        # inside a quote, which is right for the drift rules but wrong here: this project's prose
        # wraps mid-quotation, and the tightened rule immediately false-fired on
        # `Historical note, superseded: *"Sandbox only — promotion is the\n  USER's call.**` — a
        # quotation of a withdrawn claim, i.e. exactly what an exemption is for. Bounded at 300
        # chars so it cannot swallow the rest of the file.
        _QUOTED_ML = re.compile(r'"[^"]{0,300}"|“[^”]{0,300}”|`[^`]{0,300}`')
        quoted = [mm.span() for mm in _QUOTED_ML.finditer(text)]
        for m in _PROMO_PENDING.finditer(text):
            if any(a <= m.start() < b for a, b in quoted):
                continue
            ln = _line(text, m.start())
            # ‼ LOOK BACK A WINDOW, NOT A LINE. The same first draft missed a `superseded:` marker
            # that sat on the previous physical line because the sentence wrapped — line-scoped
            # exemptions are wrong for wrapped prose, which is most of this tree.
            lo = max(0, m.start() - 240)
            window = text[lo:m.end() + 240]
            # ⛔ The marker must START BEFORE the phrase it retracts (this project's ordering rule,
            # D20/D21), but it may CLOSE after it: `SUPERSEDE_RE`'s main form is `\(supersed[^)]*\)`
            # and the closing paren of `*(Superseded: this read SANDBOX-ONLY …)*` sits past the
            # match. A backward-only window therefore never sees the marker at all — P26d caught
            # exactly that in the first draft. Search BOTH ways, then enforce the ordering.
            if any(lo + mk.start() < m.start() for mk in SUPERSEDE_RE.finditer(window)):
                continue
            # ⛔⛔ THE EXEMPTION MUST BE PAST-TENSE, NOT MERELY NEIGHBOURING — TIGHTENED 2026-08-17
            # after a Tier 2 cold-start audit found THREE self-contradictions this rule had walked
            # straight past. The first draft exempted any match with `PROMOTED` within 240 chars,
            # and the offending lines say BOTH things at once:
            #     "✅ 0 as of 2026-08-17 — ALL FIVE PROMOTED … SANDBOX-ONLY, AWAITING A
            #      USER-APPROVED PROMOTION — not unexplained drift."
            # so the word that was supposed to prove the entry had been CORRECTED was in fact the
            # other half of the contradiction. ‼ A neighbourhood is not an argument (the same
            # lesson as `#24-driftassertions`' second bypass, re-earned on a different rule).
            # ⇒ What actually distinguishes a corrected entry is TENSE: it says "WAS sandbox-only",
            # "USED TO await", "NO LONGER". Require that cue immediately before the phrase.
            # ⛔⛔ THE CUE MUST LIVE IN THE CLAIM'S OWN CLAUSE — narrowed again 2026-08-17 (pass 2),
            # after an audit agent REPRODUCED a bypass: "The changelog entry WAS reworded yesterday
            # for clarity. SANDBOX-ONLY; a promotion is the USER's call." An unrelated `was` in the
            # previous sentence exempted a live PENDING claim. ‼ That is the SAME neighbourhood-vs-
            # claim mistake `#24-driftassertions` logged, and I made it twice in one day: first with
            # a 240-char `PROMOTED` window, then with this 60-char tense window. ⇒ walk back only to
            # the nearest sentence break, so the cue has to belong to the sentence it excuses.
            lo = max(0, m.start() - 200)
            clause = text[lo:m.start()]
            # ⛔ `:` IS NOT A SENTENCE BREAK HERE — it INTRODUCES the cue. Reproduced by an audit
            # agent: this project's canonical idiom is `Historical note: <claim>`, and cutting at
            # the colon stripped "Historical note" out of its own clause, so the withdrawn claim
            # was flagged as live. (The real KI-78 line escaped only because it also happens to be
            # inside quotes.) ‼ A break character that the idiom uses as a LEAD-IN cannot be used
            # to decide where the idiom ends.
            brk = list(re.finditer(r"[.;!?\n|]", clause))
            if brk:
                clause = clause[brk[-1].end():]
            if re.search(r"\b(?:was|were|used\s+to|formerly|no\s+longer|previously|had\s+been)\b"
                         r"|\bHistorical note\b", clause, re.I):
                continue
            out.append(
                f"{name}:{ln} says promotion is still PENDING ({m.group(0)[:52]!r}) but MEASURED "
                f"drift is 0 — everything is promoted")
    return out


def check_queue_vs_headline(files: dict[str, str]) -> list[str]:
    """‼ THE HEADLINE CHECK — no driver both queued as to-do and reported passing."""
    out = []
    for name, text in files.items():
        units = _units(text)
        per: dict[str, dict[str, list[int]]] = {}
        for m in TOKEN_RE.finditer(text):
            tok = m.group(1)
            a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
            seg, off = text[a:b], m.start() - a
            if SUPERSEDE_RE.search(seg):
                continue
            def nearest(rx):
                best = None
                for mm in rx.finditer(seg):
                    d = 0 if mm.start() <= off <= mm.end() else min(
                        abs(mm.start() - off), abs(mm.end() - off))
                    best = d if best is None or d < best else best
                return best
            nb, nd = nearest(BUILD_RE), nearest(DONE_RE)
            kind = None
            if nb is not None and (nd is None or nb < nd) and nb <= MAXDIST:
                kind = "BUILD"
            elif nd is not None and nd <= MAXDIST:
                kind = "DONE"
            if kind:
                per.setdefault(tok, {}).setdefault(kind, []).append(_line(text, m.start()))
        for tok, d in sorted(per.items()):
            if "BUILD" in d and "DONE" in d:
                out.append(f"{name}: --driver {tok} queued as WORK-TO-DO at line(s) {d['BUILD']} "
                           f"but reported COMPLETE/PASSING at line(s) {d['DONE']} — one of them "
                           f"is stale and unmarked")
    return out


#: ‼‼ ABSOLUTE CLAIMS THAT ARE KNOWN-FALSE UNLESS QUALIFIED, and the qualifier that rescues each.
#: WHY THIS EXISTS (2026-08-16): FIVE times in one session a correction landed in ONE of a claim's
#: TWO occurrences — and every time the survivor was in the SAME FILE, usually ABOVE the edited
#: line, so "I just read this file" felt like coverage. Prose could not catch that (the file is
#: perfectly self-consistent to a reader who stops at the first copy); a grep for the CLAIM can.
#: ⇒ To add one: put the absolute phrasing in `bad`, and a substring that makes it honest in `fix`.
QUALIFIED_CLAIMS = [
    # "nothing is parked" is an UNQUALIFIED ABSOLUTE about a fact that changes weekly. Only the
    # MID-TASK reading is durably checkable (no half-edited work, no /checkpoint debt); the broad
    # reading needs whatever is parked NAMED, so a reader can re-verify it.
    # ‼ The example this rule was born with (§Ch20 chapter assembly, parked and waiting) EXPIRED
    # when §Ch20 shipped 2026-08-24; the rule outlived it, which is the point — do NOT re-word the
    # message around whatever is parked TODAY, or it rots again. (Refreshed 2026-08-27.)
    {"bad": re.compile(r"nothing (?:is )?parked", re.I), "fix": re.compile(r"MID-TASK", re.I),
     "why": "'nothing parked' is an unqualified absolute — say 'nothing parked MID-TASK' (the "
            "checkable reading), or NAME what is parked so a reader can verify it."},
    # A doc can never truthfully assert its own pushed-ness: the sentence IS the uncommitted edit.
    {"bad": re.compile(r"(?:all work|everything) is (?:committed and )?pushed", re.I),
     "fix": re.compile(r"as of the commit carrying this line|trust `?git status`?", re.I),
     "why": "a doc cannot assert its own pushed-ness — the sentence is itself the uncommitted "
            "edit. Qualify with 'as of the commit carrying this line' / 'trust git status'."},
]


#: ⛔ A line that REFUTES the absolute is not ASSERTING it. Without this the gate fires on the very
#: prose written to correct the claim — and it DID, on its first run against the real docs, twice.
#: A gate with false positives teaches the reader to bypass it, which is worse than no gate
#: (CLAUDE.md rule 6). ‼ Deliberately narrow: only explicit refutation phrasings, so a genuine
#: assertion cannot hide behind a stray "not" elsewhere in the sentence.
_REFUTES_RE = re.compile(
    r"(?:does\s+)?\*{0,2}NOT\*{0,2}\s+(?:mean|the same as)|is\s+FALSE|read (?:it|this) as|"
    r"⛔\s*(?:was|were):|UNQUALIFIED ABSOLUTE",
    re.I,
)


def check_qualified_claims(files: dict[str, str]) -> list[str]:
    """‼ EVERY occurrence of a known-false absolute must carry its qualifier — not just the one
    someone remembered to fix. Scoped to the SAME LINE, deliberately: a qualifier 200 lines away
    does not help a cold start that stops reading at the first copy."""
    out = []
    for name, text in files.items():
        for i, line in enumerate(text.split("\n"), 1):
            if _REFUTES_RE.search(line):
                continue  # the line exists to DENY the claim; flagging it is a false positive
            for claim in QUALIFIED_CLAIMS:
                if claim["bad"].search(line) and not claim["fix"].search(line):
                    out.append(f"{name}:{i}: UNQUALIFIED ABSOLUTE — {claim['why']}")
    return out


def check_ladder(files: dict[str, str]) -> list[str]:
    claims = re.compile(r"(\d{1,2})\s+of\s+(\d{1,2})\s+beats?\b", re.I)
    found: list[tuple[str, int, int, int]] = []
    for name, text in files.items():
        units = _units(text)
        for m in claims.finditer(text):
            a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
            if SUPERSEDE_RE.search(text[a:b]):
                continue
            found.append((name, _line(text, m.start()), int(m.group(1)), int(m.group(2))))
    if not found:
        return []
    out = []
    top = max(n for _, _, n, _ in found)
    denom = {d for _, _, _, d in found}
    if len(denom) > 1:
        out.append(f"ladder DENOMINATORS disagree: {sorted(denom)} across {len(found)} claims")
    for name, line, n, _ in found:
        if n != top:
            out.append(f"{name}:{line} says the ladder is {n} of 24; the newest claim elsewhere "
                       f"is {top} of 24 — the ladder only grows, so this is stale")
    return out


def check_artifacts(files: dict[str, str]) -> list[str]:
    choices = real_driver_choices()
    path_re = re.compile(
        r"`((?:ai-research-notes|tools/story-dev)/[A-Za-z0-9._/\-]+\.(?:md|py))`")
    out = []
    for name, text in files.items():
        units = _units(text)
        for m in TOKEN_RE.finditer(text):
            tok = m.group(1)
            if tok in choices:
                continue
            a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
            seg = text[a:b]
            if SUPERSEDE_RE.search(seg) or BUILD_RE.search(seg):
                continue    # marked historical, or honestly described as the thing to build
            out.append(f"{name}:{_line(text, m.start())} cites --driver {tok}, which is not in "
                       f"story_harness.py choices and is not marked as to-build/superseded")
        for m in path_re.finditer(text):
            rel = m.group(1)
            p = (DOCS / rel) if rel.startswith("ai-research-notes/") else (REPO / rel)
            if not p.exists():
                a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
                if SUPERSEDE_RE.search(text[a:b]):
                    continue
                out.append(f"{name}:{_line(text, m.start())} cites `{rel}`, which does not exist")
    return out


def warn_ki_headers() -> list[str]:
    """WARN ONLY — measured at ~4-in-5 false positives; a worklist for a human, never a gate."""
    text = _read(DOCS / "05-KNOWN-ISSUES.md")
    out = []
    headers = list(re.finditer(r"^##+\s+(KI-\d+[a-z]?)\b(.*)$", text, re.M))
    for i, h in enumerate(headers):
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[h.end():body_end]
        head = h.group(2)
        # Suppressed when the header ALREADY carries nuance (a "half FIXED", a scoped REFUTED, a
        # correction) — the warning exists to flag headers a skimmer would misread, and a header
        # that names its own caveat is doing exactly what the rule asks.
        if re.search(r"\bOPEN\b|\bARMED\b|\bBLOCKED\b", head) and \
           not re.search(r"NOT\s+armed|REFUTED|CORRECTED|watch|\bFIXED\b|SUPERSEDED", head, re.I):
            hit = re.search(r"^\s*[-*>]?\s*[✅⛔‼]*\s*\*{0,2}"
                            r"(?:REFUTED|IS SAFE|CANNOT FIRE|(?<!NOT )(?<!not )FIXED\b)",
                            body, re.M)
            if hit:
                out.append(f"05-KNOWN-ISSUES.md:{_line(text, h.start())} {h.group(1)} header says "
                           f"OPEN/ARMED/BLOCKED but its body opens a line with a closed-status "
                           f"word — check the header still carries the caveat")
    return out


#: A body line that ANNOUNCES a closed/changed status. Deliberately narrow: it must be a marker
#: (✅/⛔/‼) or a bullet followed by a status word in caps, not a passing mention in prose.
_CLOSED_CLAIM_RE = re.compile(
    r"(?:[✅⛔]|^\s*[-*>]\s*)[^\n]{0,80}?"
    r"\b(?:FIXED|RESOLVED|CLOSED|REFUTED|LANDED|STAGE\s+\d+\s+LANDED|NO LONGER)\b",
    re.M,
)
#: A header that already carries nuance is doing what the rule asks — never flag it.
_HEADER_NUANCE_RE = re.compile(
    r"\bFIXED\b|\bRESOLVED\b|\bCLOSED\b|REFUTED|CORRECTED|SUPERSEDED|NOT\s+armed|"
    r"HALF|PARTLY|STAGE\s+\d|IN SANDBOX|watch",
    re.I,
)


def _ki_diff_hunks() -> "dict[str, tuple[bool, list[str]]] | None":
    """Per KI touched in the working diff: (was its HEADER line changed?, its ADDED body lines).

    Returns None when git cannot answer (offline, detached, file untracked) — an unavailable
    diff is not a documentation defect and must never fail the gate.
    """
    import subprocess

    rel = "PROJECT KNOWLEDGE/05-KNOWN-ISSUES.md"
    # ⛔⛔ A SKIPPED CHECK MUST NOT LOOK LIKE A PASSED ONE — narrowed and made LOUD 2026-08-17
    # (deep sanity check, pass 2). This used to be a bare `except Exception: return None`, and the
    # caller turns `None` into "no findings", which the gate turns into exit 0. So a missing `git`,
    # a 30-second timeout or a decode error would have SILENTLY disabled the whole KI header/body
    # pair check while the suite still printed PASS — the gate's own version of the comforting-zero
    # bug this project has logged twice. ‼ Now: only genuinely environmental failures are tolerated,
    # and every one of them PRINTS, so a degraded run is distinguishable from a clean one.
    try:
        diff = subprocess.run(["git", "diff", "-U0", "HEAD", "--", rel],
                              cwd=REPO, capture_output=True, text=True, timeout=30)
        if diff.returncode != 0:
            print(f"  WARN  KI-pair check SKIPPED — `git diff` exited {diff.returncode} "
                  f"(offline/detached is fine; a non-zero here is not a doc defect)")
            return None
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        print(f"  WARN  KI-pair check SKIPPED — {type(exc).__name__}: {str(exc)[:90]}. "
              f"⛔ This check did NOT run; a clean suite below does not cover it.")
        return None

    # ‼ ATTRIBUTE BY LINE NUMBER, NOT BY WHAT THE DIFF HAPPENS TO CONTAIN.
    # The first version of this tracked "which KI am I in" from ADDED header lines only — so a
    # BODY-ONLY edit (the exact case this gate exists for) belonged to no KI and the check stayed
    # silent. Its self-test passed because it exercised the DECISION while bypassing this PARSING.
    # Caught by a LIVE fault injection into the real file; the lesson is the project's own:
    # an instrument must be pointed at the thing it claims to measure, and only a live test proves
    # that. So: read the hunk's NEW-FILE line numbers and map them onto the section ranges of the
    # file as it stands now.
    text = _read(DOCS / "05-KNOWN-ISSUES.md")
    headers = [(m.start(), m.group(1), _line(text, m.start()))
               for m in re.finditer(r"^##+\s+(KI-\d+[a-z]?)\b", text, re.M)]
    if not headers:
        return None

    def _owner(line_no: int) -> "tuple[str, int] | None":
        """(KI name, its header's line number) for the section containing `line_no`."""
        found = None
        for _pos, name, hline in headers:
            if hline <= line_no:
                found = (name, hline)
            else:
                break
        return found

    touched: dict[str, tuple[bool, list[str]]] = {}
    new_line = 0
    for raw in diff.stdout.splitlines():
        hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
        if hunk:
            new_line = int(hunk.group(1))
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            line = raw[1:]
            owner = _owner(new_line)
            if owner is not None:
                name, hline = owner
                was_header, body = touched.get(name, (False, []))
                # The HEADER LINE ITSELF being among the added lines means the author touched it.
                if new_line == hline or re.match(r"^##+\s+KI-\d", line):
                    touched[name] = (True, body)
                else:
                    touched[name] = (was_header, body + [line])
            new_line += 1
        elif not raw.startswith("-"):
            new_line += 1
    return touched


#: ⛔⛔ A `check_ratchet_baseline_claims` USED TO LIVE HERE. IT WAS DELETED 2026-08-23, DELIBERATELY,
#: AND THE REASON IS THE MOST USEFUL THING IN THIS FILE.
#: It flagged prose asserting the abort-swallow ratchet was equal across forks when the probe's
#: `_BASELINES` said otherwise. The idea was sound and the implementation never converged:
#:   * its quoting exemption was written THREE times (mark parity -> pair containment -> proximity)
#:     and broken THREE times by three independent reviewers. v2 was MEASURED IDENTICAL to v1
#:     (0 mismatches / 2517 trials): a rewrite that changed the shape and not the truth table.
#:   * removing the exemption exposed the next layer: the equality test missed 7 of 7 genuine
#:     claims (a comma between the figure and the phrase defeated it) while firing on any nearby
#:     digit - dates, commit SHAs, line numbers, version strings.
#:   * its supersede/past-tense exemptions silenced ~5% of live lines via markers that were not
#:     about the claim - a bypass this very file had already documented and fixed for a SIBLING
#:     check, which the new one did not inherit.
#: A six-angle adversarial review returned SEVEN blockers on it. The decisive question was not
#: 'can I fix those?' but 'what does it protect?': it reads only CURRENT_STATE files, where the
#: phrase occurs a handful of times, all in prose ABOUT this check, and the harm it prevents is a
#: stale figure in a doc that already tells readers to run the probe instead.
#: ⇒ **REVIEW DEPTH AND IMPLEMENTATION EFFORT MUST SCALE WITH BLAST RADIUS.** Six rounds on a
#: documentation nicety is the wrong trade while a bot that plays Pokemon has open behavioural
#: items. A defect here costs a stale sentence; a defect in `early_game.py` costs a wrecked run.
#: ⇒ And the narrower engineering rule: **when a predicate needs a third exemption, the predicate
#: is wrong.** Judging author INTENT from local punctuation is not a solvable problem at this cost.
#: The stale-figure risk is now carried where it always actually was: the probe is the authority,
#: KI-81's header states the per-fork figures, and reviewers catch drift - which is how all four
#: original stale copies were found in the first place.


def check_touched_ki_pairs(_files: dict[str, str] | None = None) -> list[str]:
    """‼ THE P2 PAIR, ENFORCED — but only on KI entries THIS CHANGE ACTUALLY TOUCHES.

    WHY THIS EXISTS, AND WHY IT IS NOT `warn_ki_headers`. That warning scans the whole file and
    was measured at ~4-in-5 false positives, so it is advisory by design — and CLAUDE.md is
    explicit that a noisy gate is worse than none. **But the failure it is meant to catch happened
    anyway, on 2026-08-14, to the agent who had just written the rule down:** KI-78's body gained
    a "✅ STAGE 1 LANDED / FIXED" claim while its header still read *"OPEN, ARMED wherever a
    Nincada line is in the party"*, and its "where it is armed" bullet still described the replaced
    code. An adversarial reviewer caught it; no gate did.

    The fix is SCOPE, not sensitivity: a whole-file scan is noisy, but *"you edited this entry's
    body to announce it is fixed and did not touch its header"* is close to false-positive-free,
    because it only speaks about text the author is writing right now. Editing the header — in any
    way at all — satisfies it, which is exactly the P2 instruction ("editing one half means editing
    or explicitly re-confirming the other, IN THE SAME COMMIT").

    Fails CLOSED-safe: an unreadable diff yields no findings.
    """
    touched = _ki_diff_hunks()
    if not touched:
        return []
    text = _read(DOCS / "05-KNOWN-ISSUES.md")
    total_kis = len(re.findall(r"^##+\s+KI-\d+[a-z]?\b", text, re.M))
    out = []

    # ‼ NEVER FAIL SILENTLY OPEN. If a large fraction of entries read as "header touched", the diff
    # is a whole-file rewrite (line-ending churn, a re-encode, a reflow) and attribution is
    # meaningless — every entry would be exempted and the gate would print nothing, which is
    # indistinguishable from "you did it right". MEASURED 2026-08-14: a PowerShell `Set-Content`
    # that flipped LF to CRLF did exactly this, and the check went quiet on a fault that was
    # genuinely present. A check that cannot see must SAY it cannot see.
    if total_kis and sum(1 for changed, _ in touched.values() if changed) > max(3, total_kis // 2):
        return [
            f"05-KNOWN-ISSUES.md: {len(touched)} of {total_kis} KI entries read as header-touched "
            f"— that is a WHOLE-FILE REWRITE (line-ending or encoding churn), not an edit. The "
            f"KI header↔body pair check CANNOT ATTRIBUTE changes in this state and is reporting "
            f"that rather than passing silently. Re-save the file with its original line endings."
        ]
    for name, (header_changed, added) in sorted(touched.items()):
        # THE SYMMETRIC HALF, ADDED 2026-08-23 - and today's bug is its fault test.
        # The rule below polices "body edited, header not". THIS one polices the reverse: a HEADER
        # edited with NOTHING added inside that KI's OWN section. MEASURED CASE: the dated body line
        # written for KI-81 was inserted by matching the header STRING and prepending, which places
        # text ABOVE the header - so by this file's `##` convention it belonged to KI-79, and a
        # reader opening KI-81 would never have seen it. Tier 0 passed (the text existed and was
        # self-consistent) and a Tier 1 reviewer passed over it; the NEXT reviewer caught it, and its
        # wording is the rule: "the fix exists somewhere in the file is NOT a pass."
        # Attribution-driven, not string-driven: `_ki_diff_hunks` maps added lines onto section
        # ranges BY LINE NUMBER, so a paragraph one line above the header is attributed to the
        # PREVIOUS KI and this fires. That is the whole point.
        if header_changed and not added:
            out.append(
                f"05-KNOWN-ISSUES.md {name}: this change edits {name}'s HEADER but adds NO line "
                f"inside {name}'s OWN section (between its `##` header and the next one). P2 says "
                f"both halves move together. If you did write a body line, CHECK WHERE IT LANDED "
                f"- anchoring an insert on the header string puts it BEFORE the header, which "
                f"files it under the PREVIOUS KI. Add a dated line inside {name}, or re-confirm "
                f"the body in the same commit."
            )
            continue
        if header_changed or not added:
            continue
        claim = _CLOSED_CLAIM_RE.search("\n".join(added))
        if not claim:
            continue
        head = re.search(rf"^##+\s+{re.escape(name)}\b(.*)$", text, re.M)
        if head and _HEADER_NUANCE_RE.search(head.group(1)):
            continue  # the header already names its own caveat
        out.append(
            f"05-KNOWN-ISSUES.md {name}: this change adds a CLOSED-STATUS claim to the body "
            f"({claim.group(0).strip()[:60]!r}) but does NOT touch {name}'s header, and that "
            f"header carries no caveat. P2 says both halves move together — the header is the "
            f"half that gets skimmed. Edit the header, or re-confirm it in the same commit."
        )
    return out


def warn_handoff_date() -> list[str]:
    import subprocess
    text = (DOCS / "04-HANDOFF.md").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\*\*Last updated:\*\*\s*(\d{4}-\d\d-\d\d)", text)
    if not m:
        return ["04-HANDOFF.md has no 'Last updated:' line"]
    try:
        git_date = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", "PROJECT KNOWLEDGE/04-HANDOFF.md"],
            cwd=REPO, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:  # noqa: BLE001 - offline git is not a doc defect
        return []
    if git_date and git_date != m.group(1):
        return [f"04-HANDOFF.md 'Last updated: {m.group(1)}' but its newest commit is {git_date} "
                f"— the date line was not refreshed"]
    return []


# ---------------------------------------------------------------------------- self-test
def self_test() -> int:
    """FAULT-TEST the gate itself (CLAUDE.md rule 6): prove it fires, prove it stays quiet."""
    base = {"TEST.md": "## status\n\n* `--driver testx` ACCEPTANCE: PASS on the first drive.\n"}
    fails = 0

    def expect(label, findings, should_fire):
        nonlocal fails
        fired = bool(findings)
        ok = fired == should_fire
        print(f"  {'PASS' if ok else '‼ FAIL'}  {label}: "
              f"{'fired' if fired else 'quiet'} (expected {'fire' if should_fire else 'quiet'})")
        if not ok:
            fails += 1

    # (The R0-R24 block that used to sit here tested `check_ratchet_baseline_claims`, deleted
    # 2026-08-23 - see the long note at its former site. F-tests below belong to the KI-pair check.)

    # A: the audit's exact bug — unmarked queue item for a passing driver.
    t = base["TEST.md"] + "\n> 1. **NEXT: BUILD `--driver testx`** — not yet written.\n"
    expect("A  unmarked build-vs-pass contradiction", check_queue_vs_headline({"T": t}), True)
    # B: the same text, marked superseded — the exemption must hold.
    t = base["TEST.md"] + "\n> 1. *(superseded)* **NEXT: BUILD `--driver testx`** — not yet written.\n"
    expect("B  superseded marker exempts", check_queue_vs_headline({"T": t}), False)
    # C: the same text inside a code fence — stripped before scanning.
    raw = base["TEST.md"] + "\n```\nNEXT: BUILD --driver testx (not yet written)\n```\n"
    stripped = FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), raw)
    expect("C  code fence exempts", check_queue_vs_headline({"T": stripped}), False)
    # D: wrong counts must fire.
    total, fast = real_gate_counts()
    expect("D1 wrong gate count", check_gate_counts({"T": f"the {total + 1}-gate suite\n"}), True)
    expect("D2 right gate count", check_gate_counts({"T": f"the {total}-gate suite\n"}), False)
    # D1b-D1e: the COMMAND-COMMENT check. Both real 2026-08-14 shapes, plus the two controls that
    # keep it from becoming noise — a correct count, and a bare mention with no invocation.
    expect("D1b stale command count (comma form, no 'gates' word)",
           check_gate_count_in_commands(
               {"T": f"py -3.12 run_gates.py   # THE STANDING SUITE — all {total + 1}, exits\n"}), True)
    expect("D1c stale command count SURVIVES a supersede marker (the whole point)",
           check_gate_count_in_commands(
               {"T": f"⛔ SUPERSEDED — read below.\npy -3.12 run_gates.py  # {total + 1} gates\n"}), True)
    expect("D1d correct command count is quiet",
           check_gate_count_in_commands(
               {"T": f"py -3.12 run_gates.py   # THE STANDING SUITE — all {total}, exits\n"}), False)
    expect("D1e prose MENTIONING run_gates without a command comment is quiet",
           check_gate_count_in_commands(
               {"T": "`run_gates.py` is authoritative; it has said 17, 18 and 21 over time.\n"}), False)
    # D1f — THE FALSE POSITIVE THIS CHECK ACTUALLY PRODUCED on its first live run, kept as a
    # permanent control: a punch-list table row whose ISSUE TAG (`#24-...`) looked like a shell
    # comment introducing the count "24". Not a command; must stay silent.
    expect("D1f a table row with a `#24-` tag near run_gates.py is NOT a command",
           check_gate_count_in_commands(
               {"T": "| `#24-impassabledirs` | DONE — gated, see run_gates.py for the suite |\n"}), False)
    # D1g — a timing in the comment must not be mistaken for the count.
    expect("D1g a timing like ~130s is not read as a gate count",
           check_gate_count_in_commands(
               {"T": f"py -3.12 run_gates.py   # THE STANDING SUITE — {total} gates, ~130s\n"}), False)
    # D1h — ‼ THE PARSING HALF, and the reason this check exists at all. Every real command sits
    # inside a ```-fence, and `_read()` blanks fences. The first version was wired to that stripped
    # text: D1b-D1g all passed while the check could not see a single real command. This case feeds
    # a genuine fence, so a future rewiring to `files` fails here instead of going quietly blind.
    expect("D1h ‼ a stale count INSIDE a ``` fence is seen (the blind-parse regression guard)",
           check_gate_count_in_commands(
               {"T": f"prose above\n```\ncd tools/story-dev\npy -3.12 run_gates.py  # all "
                     f"{total + 1} gates\n```\nprose below\n"}), True)
    # D1i/D1j — `--quick` is the no-ROM SUBSET and must be graded against `fast`, never `total`.
    # Grading it against the total was this check's second live false positive.
    expect("D1i --quick graded against the FAST count, not the total",
           check_gate_count_in_commands(
               {"T": f"py -3.12 run_gates.py --quick   # the {fast} needing no ROM\n"}), False)
    expect("D1j --quick with a stale fast count still fires",
           check_gate_count_in_commands(
               {"T": f"py -3.12 run_gates.py --quick   # the {fast - 1} needing no ROM\n"}), True)
    # D1k-D1o — ‼ EVERY ONE OF THESE WAS A DEMONSTRATED BYPASS, found by an adversarial reviewer
    # who wrote a probe script against this function rather than trusting the self-test. They are
    # kept as cases because "I closed that gap" is a claim, and a claim needs a test.
    expect("D1k the count on a WRAPPED comment line is seen (was a bypass)",
           check_gate_count_in_commands(
               {"T": f"py -3.12 run_gates.py        # THE STANDING SUITE\n"
                     f"                             #   all {total + 1} gates, ~130s\n"}), True)
    expect("D1l `python3` is an interpreter (was a bypass: \\b does not match inside 'python3')",
           check_gate_count_in_commands(
               {"T": f"PYTHONUTF8=1 python3 run_gates.py   # all {total + 1} gates\n"}), True)
    expect("D1m `py3` likewise",
           check_gate_count_in_commands({"T": f"py3 run_gates.py   # all {total + 1} gates\n"}), True)
    expect("D1n a bare `./run_gates.py` with no interpreter",
           check_gate_count_in_commands({"T": f"./run_gates.py   # all {total + 1} gates\n"}), True)
    expect("D1o a command whose comment states NO count claims nothing and stays quiet",
           check_gate_count_in_commands(
               {"T": "py -3.12 run_gates.py --list    # what is in the suite\n"}), False)
    # ‼ D2b/D2c — `the suite is N gates` WITHOUT the word "now". This phrasing was invisible until
    # 2026-08-17, when a Tier 1 reviewer found a stale `25` four lines above a correct `26/26`.
    expect("D2b `the suite is <wrong> gates` (no `now`) -> fires",
           check_gate_counts({"T": f"both must exit 0; the suite is {total + 1} gates\n"}), True)
    expect("D2c the same phrasing with the RIGHT count -> quiet",
           check_gate_counts({"T": f"both must exit 0; the suite is {total} gates\n"}), False)
    expect("D2d `on its way to <wrong>` -> fires (a CURRENT total dressed as a history)",
           check_gate_counts({"T": f"it has said 17, 18 on its way to **{total + 1}**\n"}), True)
    expect("D2e `on its way to <right>` -> quiet",
           check_gate_counts({"T": f"it has said 17, 18 on its way to **{total}**\n"}), False)
    measured, _ = real_drift()
    expect("D3 wrong drift", check_drift({"T": f"drift is exactly {measured + 1}\n"}), True)
    expect("D4 right drift", check_drift({"T": f"drift is exactly {measured}\n"}), False)
    # ‼ THE "N differing" FORM (2026-08-16). D6/D7 prove it FIRES on a stale expectation and stays
    # quiet on a correct one. ⛔ D8 is the one that matters most: it proves the rule does NOT fire on
    # a HISTORICAL measurement, because that false positive is what would make this gate noisy
    # enough to be ignored — and a bypassed gate is strictly worse than no gate.
    expect("D6 stale `N differing` EXPECTATION -> fires",
           check_drift({"T": f"Expect {measured + 1} differing, 0 orphaned\n"}), True)
    expect("D7 correct `N differing` expectation -> quiet",
           check_drift({"T": f"Expect {measured} differing, 0 orphaned\n"}), False)
    expect("D8 HISTORICAL measurement (no `expect`) -> quiet",
           check_drift({"T": f"Every .py compared afterwards: {measured + 1} differing, 0 missing\n"}),
           False)
    # ‼‼ D9-D18 — CLAIM-SHAPE DETECTION (2026-08-17, `#24-driftassertions`). Every case below is a
    # VERBATIM shape from the tree, not an invented one: three stale claims survived hand sweeps AND
    # this gate on 2026-08-16/17 because it was scoped to the `expect` vocabulary and all three were
    # ASSERTIONS. ⛔ The false-positive controls (D14-D16) matter as much as the firing tests: the
    # corpus carries 67 windows mentioning a drift figure and most are deliberately-preserved
    # history, so a rule that red-flags the docs' own past gets bypassed within a day (rule 6).
    W = measured + 1                                     # a WRONG figure, whatever today's truth is
    _WORD = {v: k for k, v in _WORD_NUMBERS.items()}
    now, wrong = _WORD.get(measured, str(measured)), _WORD.get(W, str(W))
    expect("D9 stale STATE cell `N as of <date> (LATEST)` -> fires",
           check_drift({"T": f"| sandbox drift | **{W} as of 2026-08-17 (LATEST)** |\n"}), True)
    expect("D10 the same cell carrying TODAY's figure -> quiet",
           check_drift({"T": f"| sandbox drift | **{measured} as of 2026-08-17 (LATEST)** |\n"}), False)
    # The HOW TO RUN block writes the marker FIRST and lives inside a fence — `_read()` blanks
    # fences, so this shape was invisible until `check_drift` was given the raw text too.
    expect("D11 stale `(LATEST): N differing` (the fenced HOW TO RUN shape) -> fires",
           check_drift({"T": f"#   drift, expected as of 2026-08-17 (LATEST): {W} differing\n"}), True)
    expect("D12 stale `IT IS <N> AGAIN` (the 60-second idiom) -> fires",
           check_drift({"T": f"which took drift to 0 then. AND IT IS {wrong.upper()} AGAIN as of 2026-08-17.\n"}),
           True)
    expect("D12b the same idiom carrying TODAY's figure -> quiet",
           check_drift({"T": f"which took drift to 0 then. AND IT IS {now.upper()} AGAIN as of 2026-08-17.\n"}),
           False)
    # ⛔⛔ POLARITY, BOTH DIRECTIONS — the ruling in `06-DECISIONS-LOG.md`. A negation is stale
    # precisely when it AGREES with the measurement. MEASURED 2026-08-17: the shipped gate was blind
    # to every negation phrasing at BOTH drift values, so this pair is the whole point of the rule.
    expect("D13 negation that is FALSE (`drift is NOT <today's figure>`) -> fires",
           check_drift({"T": f"The sandbox->custom drift figure is NOT {now} — a ruling is owed.\n"}), True)
    expect("D13b negation that is TRUE (`drift is NOT <some other figure>`) -> quiet",
           check_drift({"T": f"The sandbox->custom drift figure is NOT {wrong} today.\n"}), False)
    # ‼ THE RECURSION HAZARD, and it is not hypothetical: this gate red-flagged the ORIGINAL draft of
    # the punch-list bullet commissioning this very rule. The docs QUOTE stale figures on purpose.
    expect("D14 a stale figure QUOTED inside prose about the problem -> quiet",
           check_drift({"T": f'The drift clause briefly read "NOT {now} … a ruling is owed", which was '
                             f'true for about an hour.\n'}), False)
    expect("D15 a withdrawn figure inside a RETRACTION parenthetical -> quiet",
           check_drift({"T": f"drift row *(Superseded: this cell read **{W} as of 2026-08-17 (LATEST)** "
                             f"until the promotion landed.)*\n"}), False)
    expect("D16 ordinary English `not one` near unrelated prose -> quiet (a MEASURED false positive)",
           check_drift({"T": "The drift discussion is elsewhere." + " padding." * 20 +
                             f" There are TWO unbound reads, not {now}.\n"}), False)
    # ⛔⛔ THE REGRESSION GUARD FOR THE TRAP THIS RULE NEARLY SHIPPED WITH. `04-HANDOFF.md`'s STATE
    # drift cell is ONE table row of 7,916 chars carrying a `*(Superseded …)*` 283 chars from its
    # LIVE claim. Unit-scoped exemption — which every OTHER check here uses correctly — silences the
    # single most authoritative site in the tree. If someone "tidies" this back to unit scope, D17
    # is what fails.
    expect("D17 a live claim far from a supersede marker in the SAME unit -> STILL fires",
           check_drift({"T": f"| sandbox drift | **{W} as of 2026-08-17 (LATEST)** |" + " x" * 120 +
                             " *(Superseded: an earlier round read three differing here.)*\n"}), True)
    expect("D18 stale `should report N differing` -> fires",
           check_drift({"T": f"so promote.py --check should report **{W} differing, 0 orphaned**\n"}), True)
    expect("D18b PAST tense `reported N differing` is a measurement -> quiet",
           check_drift({"T": f"promote.py --check reported {W} differing, 0 orphaned that day\n"}), False)
    # ⛔⛔ D20/D21 — TWO BYPASSES FOUND BY AN ADVERSARIAL REVIEW OF THE FIRST DRAFT AND REPRODUCED
    # BEFORE FIXING. Both were exemptions binding to the NEIGHBOURHOOD instead of to the CLAIM, and
    # both silently reopened exactly the failure this item exists to close. Their controls are D15
    # (a genuine retraction, marker FIRST) and D22 (the `Superseded text:` prefix idiom).
    expect("D20 an innocuous aside containing `read`/`until` AFTER the figure -> still fires",
           check_drift({"T": f"(as of 2026-08-17, the drift figure is {W} again — you can read the "
                             f"log until it is rotated out.)\n"}), True)
    expect("D21 a marker retracting a DIFFERENT, EARLIER number nearby -> still fires",
           check_drift({"T": f"Drift was 5 (superseded), then corrected; the sandbox drift is {W} "
                             f"again as of 2026-08-17.\n"}), True)
    expect("D22 the `Superseded text:` prefix idiom (marker FIRST, same sentence) -> quiet",
           check_drift({"T": f"Superseded text: **DRIFT IS {wrong.upper()} AGAIN AS OF 2026-08-13.**\n"}),
           False)
    # ⛔ D19 — the gate grades the docs against `real_drift()`, but the DOCS quote `promote.py
    # --check`'s output. If the two ever measure different file sets, this gate starts failing
    # correct documentation, which is the fastest way to teach everyone to bypass it.
    # ‼‼ D23-D25 — THE THREE SHAPES A TIER 2 COLD-START AUDIT FOUND STILL LIVE ON 2026-08-17, hours
    # after the claim-shape rules shipped. All three were in `04-HANDOFF.md`, two of them inside the
    # orientation block a cold reader is ORDERED to read FIRST, telling it no promotion decision was
    # owed while one was. ⇒ Shipping a rule is not the same as covering the corpus.
    expect("D23 `drift FIGURE is <wrong>` — a NOUN between `drift` and `is` -> fires",
           check_drift({"T": f"The sandbox->custom drift figure is {W} — everything is promoted\n"}), True)
    expect("D23b the same phrasing with TODAY's figure -> quiet",
           check_drift({"T": f"The sandbox->custom drift figure is {measured} today\n"}), False)
    # ⛔ D24 IS THE SUBTLE ONE. A parenthetical here routinely carries a HISTORICAL clause AND a
    # CURRENT one; the soft marker `AT THAT MOMENT` sat 20 chars before a live claim and silenced it.
    # An explicit CURRENCY marker must outrank soft history vocabulary.
    expect("D24 a CURRENT claim sharing a parenthetical with soft history -> still fires",
           check_drift({"T": f"*(the KI-65 fix took drift to 0 AT THAT MOMENT. AND IT IS {wrong.upper()} "
                             f"AGAIN as of 2026-08-17)*\n"}), True)
    expect("D25 …but an EXPLICIT retraction still silences it -> quiet",
           check_drift({"T": f"*(Superseded: this read AND IT IS {wrong.upper()} AGAIN as of "
                             f"2026-08-17)*\n"}), False)
    # ‼‼ D26 — THE SHAPE THAT HID A STALE FIGURE PAST 27/27 GREEN ON 2026-08-17. The subject word
    # sits in the sentence but the digit hangs off a PRONOUN, so every earlier rule missed it.
    # ⛔ D26c is the false-positive half and matters just as much: this file is full of prose ABOUT
    # stale figures, and a gate that fires on a retraction gets bypassed.
    expect("D26 `drift was 0 … It is <wrong> today` -> fires",
           check_drift({"T": f"drift was 0 at that point *(It is **{W}** today for other files)*\n"}),
           True)
    expect("D26b the same shape carrying TODAY's figure -> quiet",
           check_drift({"T": f"drift was 0 at that point *(It is **{measured}** today for other files)*\n"}),
           False)
    # ‼ D26c carries the word `drift` ON PURPOSE. Without it the rule cannot match at all, and the
    # test would pass for the WRONG REASON — proving nothing about the retraction path it names.
    expect("D26c an explicit RETRACTION of that shape -> quiet",
           check_drift({"T": f"*(Superseded: the drift cell read It is **{W}** today until corrected)*\n"}),
           False)
    expect("D26d the shape with NO drift subject in range -> quiet (not every 'it is N today' is drift)",
           check_drift({"T": f"The batch finished; it is {W} today by the run counter.\n"}), False)
    # ‼‼ D28 — THE DRIFT-ROW HEADLINE (`#24-driftheadlineshape`, 2026-08-26). The 2026-08-24
    # incident: the STATE-table cell listed three files while its FIRST figure — the half that
    # gets skimmed — still said 2, and no earlier rule matches `**N as of <date>`.
    # ⛔ D28b is the incident shape INVERTED (headline right, history wrong) and MUST stay quiet:
    # history inside the cell is exempt BY POSITION (first-match-only), so the gate cannot go
    # noisy over the cell's own archive tail.
    _row = ("| sandbox <-> custom drift | ⚠ **{} as of 2026-08-26, MEASURED** — files. "
            "✅ Previously **{} as of 2026-08-15** — promoted. |\n")
    expect("D28a drift-row headline disagrees with the measurement -> fires",
           check_drift({"T": _row.format(W, measured)}), True)
    expect("D28b headline RIGHT while a HISTORICAL figure deeper in the cell differs -> quiet",
           check_drift({"T": _row.format(measured, W)}), False)
    _wword = ("one" if measured != 1 else "two").upper()
    expect(f"D28c word-form headline (`{_wword} as of`) -> fires",
           check_drift({"T": _row.format(_wword, measured)}), True)
    expect("D28d a non-drift-labelled row with `N as of <date>` -> quiet",
           check_drift({"T": f"| batch status | {W} as of 2026-08-26, still running |\n"}), False)
    # D28f/D28g — the markup-wrapped headline (both directions), and D29a-c — the no-verb
    # `drift **N**` claim shape. Both families were added 2026-08-27 after the deep sanity check
    # proved the gate blind to a LIVE stale figure in this very file.
    _bold_row = ("| sandbox <-> custom drift | ⚠ **{}** as of 2026-08-26, MEASURED — files. "
                 "✅ Previously **{}** as of 2026-08-15 — promoted. |\n")
    expect("D28f bolded WRONG headline -> fires",
           check_drift({"T": _bold_row.format(W, measured)}), True)
    expect("D28g bolded RIGHT headline with a wrong HISTORY figure -> quiet",
           check_drift({"T": _bold_row.format(measured, W)}), False)
    expect("D29a no-verb `drift **N**` with a stale figure -> fires",
           check_drift({"T": f"State: main, drift **{W}** (`a.py` + `b.py`), nothing parked.\n"}), True)
    expect("D29b the same shape carrying TODAY's figure -> quiet",
           check_drift({"T": f"State: main, drift **{measured}** (`a.py`), nothing parked.\n"}), False)
    expect("D29c an UNMARKED-UP `drift N` in ordinary prose -> quiet (no false positive)",
           check_drift({"T": f"the drift {W} files were promoted last week by hand.\n"}), False)

    # D30a/D30b — PASS 1's exemption is POSITIONAL (2026-08-27). D30b is the one that matters:
    # the tree's commonest retraction is a parenthetical CONTAINING its claim, and an
    # end-truncated search would break it (measured against the live tree before shipping).
    expect("D30a a supersede marker AFTER the stale claim -> still fires",
           check_drift({"T": f"drift is {W} today. *(Superseded: an older note about something else.)*\n"}),
           True)
    expect("D30b a retraction parenthetical CONTAINING the claim -> quiet",
           check_drift({"T": f"promoted that day (superseded: *drift is now {W} again*) — history.\n"}),
           False)

    _fenced = "```\n" + _row.format(W, measured) + "```\n"
    _fstripped = FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), _fenced)
    expect("D28e the same row inside a code fence (stripped, as the gate calls it) -> quiet",
           check_drift({"T": _fstripped}), False)
    # ‼‼ P26 — THE PROSE TWIN OF THE DRIFT CHECK (added 2026-08-17). `check_drift` grades FIGURES
    # and went green over two KI entries that said IN WORDS that the just-promoted work was still
    # sandbox-only. ⛔ Scoped to drift == 0, so these only mean anything when nothing is pending;
    # if the tree ever has real drift, P26a is EXPECTED to go quiet and that is correct, not a
    # broken test — hence the guard below rather than a bare assertion.
    _dr, _ = real_drift()
    if _dr == 0:
        expect("P26a `SANDBOX-ONLY; a promotion is the USER's call` while drift is 0 -> fires",
               check_promotion_prose({"T": "the verdict reaches the caller. SANDBOX-ONLY; a promotion is the USER's call.\n"}),
               True)
        expect("P26b `against the unpromoted custom tree` while drift is 0 -> fires",
               check_promotion_prose({"T": "gate #26 which FAILS against the unpromoted `custom` tree.\n"}), True)
        expect("P26c the same line ALSO recording that it WAS promoted -> quiet (a corrected entry)",
               check_promotion_prose({"T": "was SANDBOX-ONLY; a promotion is the USER's call — ✅ PROMOTED 2026-08-17.\n"}),
               False)
        expect("P26d an explicit RETRACTION -> quiet",
               check_promotion_prose({"T": "*(Superseded: this read SANDBOX-ONLY; a promotion is the USER's call)*\n"}),
               False)
        expect("P26e ordinary prose with no promotion-pending claim -> quiet",
               check_promotion_prose({"T": "The guards were swept and the probe is a ratchet at 36.\n"}), False)
    expect("D19 this gate measures the SAME trees `promote.py` does",
           [] if promote_trees() == _DRIFT_TREES else
           [f"promote.py TREES={promote_trees()} but this gate scans {_DRIFT_TREES}"], False)
    # Q: known-false ABSOLUTES must carry their qualifier on the SAME LINE, in EVERY occurrence.
    # ‼ Q3/Q4 are the false-positive tests that decide whether this gate is usable: a gate that
    # fires on a doc DISCUSSING the phrase teaches everyone to bypass it.
    expect("Q1 bare 'nothing is parked' -> fires",
           check_qualified_claims({"T": "State: main, nothing parked, nothing running.\n"}), True)
    expect("Q2 qualified 'nothing parked MID-TASK' -> quiet",
           check_qualified_claims({"T": "State: main, nothing parked MID-TASK; Ch20 IS parked.\n"}), False)
    expect("Q3 two occurrences, only ONE qualified -> fires (the whole point)",
           check_qualified_claims({"T": "nothing parked MID-TASK, fine.\nlater: nothing is parked.\n"}), True)
    expect("Q4 'all work is pushed' WITH the git-status caveat -> quiet",
           check_qualified_claims({"T": "All work is pushed as of the commit carrying this line.\n"}),
           False)
    expect("Q5 bare 'everything is pushed' -> fires",
           check_qualified_claims({"T": "Everything is pushed and the tree is clean.\n"}), True)
    # ‼ Q6/Q7 are the fix for a REAL false positive this gate produced on its first live run: it
    # fired on the prose written to CORRECT the claim. A gate that punishes the correction is one
    # everybody learns to bypass.
    expect("Q6 a line REFUTING the absolute -> quiet (it denies, it does not assert)",
           check_qualified_claims({"T": 'That is NOT the same as "nothing is parked": Ch20 IS parked.\n'}),
           False)
    expect("Q7 refutation escape is NARROW — a stray 'not' does NOT excuse an assertion",
           check_qualified_claims({"T": "The box is not running and nothing is parked.\n"}), True)
    expect("D5 stale ladder", check_ladder({"T": "ladder runs 19 of 24 beats\nnow 20 of 24 beats\n"}), True)
    # E: fabricated driver cited as runnable must fire; marked-to-build must not.
    expect("E1 phantom driver", check_artifacts({"T": "run `--driver nosuchthing` now\n"}), True)
    expect("E2 to-build driver exempt",
           check_artifacts({"T": "NEXT: BUILD `--driver nosuchthing` — does not exist yet\n"}), False)

    # F: the P2 pair, diff-scoped (added 2026-08-14 after KI-78's body said FIXED while its
    #    header still said ARMED). The real check reads `git diff`; here the parsing and the
    #    decision are exercised directly, because a self-test must not depend on the working tree.
    def _decide(header_changed, added, header_text):
        """Mirror of the decision in `check_touched_ki_pairs`, over injected inputs.

        WARNING, AND IT IS THIS FILE'S OWN LOGGED LESSON: this is a MIRROR, so it can drift
        from the real function and keep passing. It covers the DECISION only; the ATTRIBUTION
        (which KI an added line belongs to, by line number) is what actually broke in the wild
        and is only provable by a LIVE arm. F6/F7 below therefore lock in the decision, and the
        three live arms recorded in `#24-p2headergate` lock in the parsing. Keep both.
        """
        if header_changed and not added:
            return ["would fire: header edited, nothing added inside this KI"]
        if header_changed or not added:
            return []
        if not _CLOSED_CLAIM_RE.search("\n".join(added)):
            return []
        if _HEADER_NUANCE_RE.search(header_text):
            return []
        return ["would fire"]

    # F6/F7 -- the SYMMETRIC branch added 2026-08-23 (#24-p2headergate). A Tier 1 reviewer noted
    # the new branch shipped with NO automated coverage, so a later edit could delete it silently.
    expect("F6 header edited with NO line added inside this KI -> fires",
           _decide(True, [], " — (OPEN)"), True)
    expect("F7 header edited WITH a line added inside this KI -> quiet",
           _decide(True, ["- **2026-08-23** — re-measured; baseline lowered."], " — (OPEN)"), False)
    expect("F1 body claims FIXED, header untouched and plain OPEN",
           _decide(False, ["- ✅ **FIXED** by Stage 1, A/B proven."], " — (2026-08-14, OPEN, ARMED)"),
           True)
    expect("F2 ...but the header was edited in the same change",
           _decide(True, ["- ✅ **FIXED** by Stage 1, A/B proven."], " — (OPEN, ARMED)"), False)
    expect("F3 ...or the header already carries the caveat",
           _decide(False, ["- ✅ **FIXED** in sandbox."],
                   " — (FIXED IN SANDBOX, ARMED IN CUSTOM until promoted)"), False)
    expect("F4 a body edit with no status claim is silent",
           _decide(False, ["- Added a citation for the decomp line."], " — (OPEN)"), False)
    # ‼ THE FALSE-POSITIVE CONTROL. CLAUDE.md rule 6: prove the gate does NOT fire on mere
    # mentions in prose — a gate that cries wolf teaches the reader to bypass it.
    expect("F5 prose that merely MENTIONS a fix does not fire",
           _decide(False, ["  the same egg bug that was fixed thirty lines above it on 2026-08-13",
                           "  (see the resolved KI-64 for the shape of this failure)"],
                   " — (OPEN)"), False)

    print(f"\nSELF-TEST {'PASS' if fails == 0 else 'FAIL'} ({fails} deviation(s))")
    return 0 if fails == 0 else 1


# ---------------------------------------------------------------------------- main
def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()

    files = {name: _read(DOCS / name) for name in CURRENT_STATE if (DOCS / name).exists()}
    failures: list[str] = []
    failures += check_gate_counts(files)
    # ‼ RAW text, deliberately: `_read()` blanks code fences, and every runnable command lives in
    # one. See this check's docstring — wiring it to `files` made it silently blind.
    raw_files = {name: (DOCS / name).read_text(encoding="utf-8", errors="replace")
                 for name in CURRENT_STATE if (DOCS / name).exists()}
    failures += check_gate_count_in_commands(raw_files)
    # ‼ BOTH texts: the legacy rules need fences STRIPPED, the claim-shape rules need them KEPT.
    # See check_drift's docstring — the authoritative `Expect …: 0 differing` line lives in a fence.
    failures += check_drift(files, raw_files)
    # ‼ The PROSE twin of check_drift — figures and sentences go stale independently (2026-08-17).
    failures += check_promotion_prose(files)
    failures += check_queue_vs_headline(files)
    failures += check_qualified_claims(files)
    failures += check_ladder(files)
    failures += check_artifacts(files)
    failures += check_touched_ki_pairs(files)
    warnings = warn_ki_headers() + warn_handoff_date()

    print("=" * 92)
    print("DOC CONSISTENCY AUDIT — current-state files vs the code and each other")
    print("=" * 92)
    for w in warnings:
        print(f"  WARN  {w}")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print(f"  all consistency checks PASS across {len(files)} current-state files"
              f"{f'  ({len(warnings)} warning(s) above are human worklist, not failures)' if warnings else ''}")
    print("=" * 92)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
