"""GATE — no cp1252 round-trip mojibake, and no UTF-8 BOM, in `PROJECT KNOWLEDGE/`.

‼‼ WHY THIS EXISTS. On 2026-08-14 an agent corrupted **946 sequences across 343 lines of
`04-HANDOFF.md`** — the project's single most important file — by splicing it with PowerShell:
`Get-Content` on Windows PowerShell 5.1 decodes with the system ANSI codepage, so a UTF-8 file
comes back as mojibake, and `Set-Content -Encoding utf8` then writes that damage back
permanently. The same round-trip had ALREADY happened once before, to `03-PUNCH-LIST.md`
("a UTF-8 BOM + 124 mojibake lines"), was repaired, and **was repeated anyway** — which is the
definition of a rule that needs a gate rather than a paragraph.
It is also silent: every doc gate passed the whole time, because none of them read bytes.

‼ AND THE FIRST DETECTOR WRITTEN FOR IT WAS BLIND. A hand-written list of known-bad sequences
('â€”', 'âœ…', …) reported `03-PUNCH-LIST.md` as **0 mojibake** while it in fact carried **29
corrupted lines**, because 'Ã—' (a mangled '×') was not on the list. A detector that can only
see what it was told to look for will report clean and be believed. So this one is
PATTERN-based, and it CONFIRMS every hit by round-tripping.

THE SIGNATURE. UTF-8 decoded as cp1252 and re-encoded produces a run beginning with one of
`Â Ã â ð Å Ëœ â€` followed by more non-ASCII. Detecting that shape alone would flag legitimate
prose, so a line is only reported when `line.encode('cp1252').decode('utf-8')` **succeeds AND
yields strictly fewer suspect runs** — i.e. when the repair provably improves it. That
confirmation is what keeps emoji, arrows and box-drawing (all over these docs) from firing it.

    PYTHONUTF8=1 py -3.12 audit_encoding.py                # gate: every PROJECT KNOWLEDGE/*.md
    PYTHONUTF8=1 py -3.12 audit_encoding.py --repair       # fix them in place
    PYTHONUTF8=1 py -3.12 audit_encoding.py --self-test    # fault-test the gate itself
    PYTHONUTF8=1 py -3.12 audit_encoding.py <file> [...]   # check specific files

Exit 0 = clean. Exit 1 = at least one file carries mojibake or a BOM.
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
DOCS = REPO / "PROJECT KNOWLEDGE"

#: A cp1252-mangled UTF-8 run: a Latin-1 lead byte followed by more non-ASCII.
SUSPECT = re.compile(r"[ÂÃâðÅËœ][-ÿ -⇿Œ-Ÿ]")


def suspect_count(text: str) -> int:
    return len(SUSPECT.findall(text))


#: ‼‼ THE FIVE BYTES cp1252 LEAVES UNDEFINED — 0x81, 0x8D, 0x8F, 0x90, 0x9D. Python REFUSES to
#: encode the matching characters; Windows PowerShell's decoder happily produced them. So a UTF-8
#: sequence containing one of those bytes round-tripped into text this gate could not re-encode:
#: `line.encode("cp1252")` RAISED, `repair_line` returned None, and the damage was reported CLEAN.
#: That is exactly how `## ⏱` and `## ⏭` (U+23F1 / U+23ED — UTF-8 middle byte 0x8F) survived in
#: `04-HANDOFF.md`, one of them on the NEXT ACTIONS heading, while this gate said "all 34 clean".
#: Found 2026-08-15 by an independent cross-doc sweep, NOT by the gate written for this failure.
#: ⇒ **a codec's REFUSAL to encode is not evidence of health.**
_CP1252_UNDEFINED = {"": 0x81, "": 0x8D, "": 0x8F, "": 0x90, "": 0x9D}


def _to_cp1252_bytes(line: str) -> "bytes | None":
    """Encode as cp1252, mapping the five UNDEFINED C1 characters back to their raw bytes.

    Returns None only when a character genuinely has no cp1252 byte — the honest "this was never
    a cp1252 round-trip" answer, as opposed to the codec simply refusing.
    """
    out = bytearray()
    for ch in line:
        raw = _CP1252_UNDEFINED.get(ch)
        if raw is not None:
            out.append(raw)
            continue
        try:
            out += ch.encode("cp1252")
        except UnicodeEncodeError:
            return None
    return bytes(out)


def repair_line(line: str) -> "str | None":
    """The reversal, returned ONLY when it provably reduces the damage (else None)."""
    if suspect_count(line) == 0:
        return None
    encoded = _to_cp1252_bytes(line)
    if encoded is None:
        return None
    try:
        candidate = encoded.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return candidate if suspect_count(candidate) < suspect_count(line) else None


def scan(path: pathlib.Path) -> "tuple[bool, list[tuple[int, str]]]":
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = (raw[3:] if bom else raw).decode("utf-8", errors="replace")
    hits = [(i + 1, line) for i, line in enumerate(text.split("\n"))
            if repair_line(line) is not None]
    return bom, hits


def repair(path: pathlib.Path) -> "tuple[bool, int]":
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = (raw[3:] if bom else raw).decode("utf-8")
    lines = text.split("\n")
    fixed = 0
    out = []
    for line in lines:
        replacement = repair_line(line)
        if replacement is not None:
            fixed += 1
            out.append(replacement)
        else:
            out.append(line)
    if fixed or bom:
        path.write_bytes("\n".join(out).encode("utf-8"))
    return bom, fixed


def self_test() -> int:
    """FAULT-TEST the gate (CLAUDE.md rule 6): prove it fires, and prove it stays QUIET."""
    fails = 0

    def expect(label, condition):
        nonlocal fails
        print(f"  {'PASS' if condition else '‼ FAIL'}  {label}")
        if not condition:
            fails += 1

    # FIRES: a real cp1252 round-trip of an em dash / marker.
    damaged = "the fix â€” proven â€¼ and gated"
    expect("A  fires on a genuine round-trip", repair_line(damaged) is not None)
    expect("A2 ...and repairs it to the original",
           repair_line(damaged) == "the fix — proven ‼ and gated")
    # QUIET: legitimate non-ASCII prose, which these docs are full of.
    for label, text in (
        ("B1 em dash + markers", "the fix — proven ‼ and gated ✅ ⛔ ⚠"),
        ("B2 arrows and maths", "A → B ⇒ C, 20×17, §Ch20, n≈30"),
        ("B3 emoji headings", "🚩 ROOM 8 — 📊 MEASURED 📚"),
        ("B4 plain ascii", "a perfectly ordinary line of text"),
        ("B5 box drawing", "┌───┬───┐ │ a │ b │ └───┴───┘"),
    ):
        expect(f"{label} stays quiet", repair_line(text) is None)
    # C1-C5 -- the CONTROL-CHARACTER guard (#24-p2headergate (C), added 2026-08-23). A Tier 1
    # reviewer noted it shipped wired into main() with NO automated coverage, so a later edit could
    # remove it and --self-test would still print PASS.
    expect("C1 backspace 0x08 is forbidden (the bug this exists for)", chr(8) in _CTRL_FORBIDDEN)
    expect("C2 vertical tab 0x0b is forbidden", chr(11) in _CTRL_FORBIDDEN)
    expect("C3 DEL 0x7f is forbidden", chr(127) in _CTRL_FORBIDDEN)
    expect("C4 tab / newline / CR are ALLOWED (the false-positive control)",
           not (_CTRL_FORBIDDEN & {chr(9), chr(10), chr(13)}))
    # C5 CALLS THE SHIPPED SCANNER. The first version re-implemented the predicate inline and never
    # called `scan_py_ctrl_chars` at all - so mutants that gutted the scanner body, or deleted the
    # function and its wiring outright, BOTH survived with a green self-test. A six-angle review
    # mutation-tested it and found that; the comment that used to sit here claimed the opposite.
    # ‼ THE FIXTURE MUST LIVE UNDER ONE OF `_PY_ROOTS` or the scan skips it and the test is vacuous
    # in a NEW way - which is why `REPO` is repointed rather than the fixture placed anywhere handy.
    import tempfile
    _saved_repo = REPO
    try:
        with tempfile.TemporaryDirectory() as _d:
            _root = pathlib.Path(_d) / "tools" / "story-dev"
            _root.mkdir(parents=True)
            (_root / "dirty.py").write_text(
                "x = 1" + chr(10) + "y = " + chr(8) + chr(10), encoding="utf-8")
            (_root / "clean.py").write_text(
                "x = 1" + chr(9) + chr(10) + "y = 2" + chr(13) + chr(10), encoding="utf-8")
            globals()["REPO"] = pathlib.Path(_d)
            _hits = scan_py_ctrl_chars()
        expect("C5 the SHIPPED scanner flags the 0x08 file and ONLY that file",
               _hits == ["tools/story-dev/dirty.py:2  0x08"])
    finally:
        globals()["REPO"] = _saved_repo

    print(f"\nSELF-TEST {'PASS' if fails == 0 else 'FAIL'} ({fails} deviation(s))")
    return 0 if fails == 0 else 1


#: ‼‼ THE SECOND SCOPE — .py FILES, ADDED 2026-08-16 BECAUSE THIS GATE WATCHED THE WRONG TREE.
#: On 2026-08-16 an agent editing `repro_boss_grass_gate.py` read it with `encoding="utf-8-sig"`
#: (which STRIPS a BOM if present) and wrote it back as `"﻿" + text` (which ADDS one
#: unconditionally). The file never had a BOM, so three bytes appeared that nobody asked for.
#: ⛔ **No gate saw it** — everything above scans `PROJECT KNOWLEDGE/*.md` only, so a BOM landing in
#: a GATE SCRIPT was invisible to the gate suite. CPython tolerates a source BOM, so nothing broke,
#: which is exactly what makes it easy to leave behind. A Tier 1 reviewer found it by diffing the
#: working tree.
#: ‼ THE RULE IS "NO **NEW** BOMs", NOT "NO BOMs": two files legitimately carry one today, and
#: rewriting them is a bigger change than this gate should force. So the baseline is PINNED, and
#: anything outside it that gains a BOM FAILS. Adding a file here must be a deliberate act.
_BOM_ALLOWED = {
    "tools/story-dev/livetest.py",
    "tools/story-dev/story_harness.py",
}

#: Where .py files are scanned for BOMs. Deliberately NOT the whole repo: `profiles/` and
#: `__pycache__` hold generated bytes nobody edits by hand.
#: The UTF-8 BOM, built from code points so THIS source file can never itself contain one.
_BOM_BYTES = bytes((0xEF, 0xBB, 0xBF))

_PY_ROOTS = ("tools/story-dev", "sandbox-pokebot", "custom-pokebot")
_PY_SKIP = {".git", "profiles", "__pycache__", "venv", ".venv", "roms"}


def scan_py_boms() -> "list[str]":
    """Repo-relative paths of .py files carrying a UTF-8 BOM that are NOT in the pinned baseline."""
    offenders = []
    for root in _PY_ROOTS:
        base = REPO / root
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if _PY_SKIP & set(path.parts):
                continue
            try:
                if path.read_bytes()[:3] != _BOM_BYTES:
                    continue
            except OSError:
                continue
            rel = path.relative_to(REPO).as_posix()
            if rel not in _BOM_ALLOWED:
                offenders.append(rel)
    return sorted(offenders)


#: CONTROL CHARACTERS IN SOURCE - added 2026-08-23 after \b compiled to a literal BACKSPACE
#: (0x08) TWICE IN ONE DAY, and BOTH times the gate containing it still printed PASS.
#: THE MECHANISM: \b is a REAL Python escape. \s, \d and \w are NOT valid escapes, so they
#: survive a non-raw string with only a SyntaxWarning. That asymmetry is the whole trap - the
#: neighbouring \s really is fine, the source LOOKS right, and only \b has been silently replaced
#: by a control character. The pattern then matches nothing, and a gate that matches nothing
#: reports PASS. A NO-OP WEARING A GREEN TICK IS WORSE THAN NO GATE: it also stops anyone looking.
#: HARD ZERO, NOT A RATCHET: measured 2026-08-23 over 725 .py files -- the FULL _PY_ROOTS scope
#: (tools/story-dev 259 + sandbox-pokebot 233 + custom-pokebot 233, minus _PY_SKIP) - ZERO hits.
#: There is no legitimate baseline to preserve, so any hit is a defect.
#: A Tier 1 reviewer caught the first draft of this comment claiming 631 - the count for a
#: NARROWER scope (the two forks' modules/ only) than the code actually scans. The number was
#: measured honestly and described the wrong thing. => STATE THE SCOPE WITH THE COUNT: a bare
#: figure cannot be checked against the code it claims to describe.
#: DELIBERATELY NOT A REGEX. A regex here would need the very escapes this check exists to police,
#: and could fail the same silent way. An explicit code-point set cannot.
#: ITS OWN WRITING PROVED THE POINT: the first attempt at this block was generated through a shell
#: heredoc, which ate a backslash level and put a REAL TAB inside the string below. Every backslash
#: here is now built with chr(92).
_CTRL_ALLOWED = frozenset([chr(9), chr(10), chr(13)])   # tab, newline, carriage return
_CTRL_FORBIDDEN = frozenset(
    chr(c) for c in list(range(0x00, 0x20)) + [0x7f] if chr(c) not in _CTRL_ALLOWED
)


def scan_py_ctrl_chars() -> "list[str]":
    """path:line and code point for every literal control character in scanned .py sources."""
    offenders: list[str] = []
    for root in _PY_ROOTS:
        base = REPO / root
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if _PY_SKIP & set(path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="strict")
            except (OSError, UnicodeDecodeError):
                continue  # undecodable is the BOM/mojibake checks' problem, not this one's
            if not _CTRL_FORBIDDEN.intersection(text):
                continue  # fast path: almost every file
            rel = path.relative_to(REPO).as_posix()
            for index, char in enumerate(text):
                if char in _CTRL_FORBIDDEN:
                    line = text.count("\n", 0, index) + 1
                    offenders.append(f"{rel}:{line}  0x{ord(char):02x}")
    return sorted(offenders)

def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    do_repair = "--repair" in sys.argv
    explicit = [pathlib.Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    targets = explicit or sorted(DOCS.glob("*.md"))

    print("=" * 92)
    print("ENCODING AUDIT — cp1252 round-trip mojibake and BOMs in PROJECT KNOWLEDGE/")
    print("=" * 92)
    bad = 0
    for path in targets:
        if do_repair:
            bom, fixed = repair(path)
            if bom or fixed:
                print(f"  REPAIRED  {path.name}: {fixed} line(s)"
                      f"{', BOM stripped' if bom else ''}")
            continue
        bom, hits = scan(path)
        if bom or hits:
            bad += 1
            print(f"  FAIL  {path.name}: {len(hits)} mojibake line(s)"
                  f"{', UTF-8 BOM' if bom else ''}")
            for number, line in hits[:5]:
                print(f"          line {number}: {line[:100]}")
            if len(hits) > 5:
                print(f"          ... and {len(hits) - 5} more")
    ctrl = [] if (do_repair or explicit) else scan_py_ctrl_chars()
    if ctrl:
        bad += len(ctrl)
        print(f"  FAIL  {len(ctrl)} literal CONTROL CHARACTER(s) in .py source:")
        for hit in ctrl[:10]:
            print(f"          {hit}")
        if len(ctrl) > 10:
            print(f"          ... and {len(ctrl) - 10} more")
        print("        Almost always a \\b that became a BACKSPACE (0x08) - a regex escape that")
        print("          did not survive a non-raw string or a shell heredoc. The pattern then")
        print("          matches NOTHING and its gate still prints PASS.")
        print("        Build it: _WB = chr(92) + 'b'. And NEVER review a regex by reading it -")
        print("          print the COMPILED .pattern and run a positive AND a negative list.")
    py_boms = [] if (do_repair or explicit) else scan_py_boms()
    if py_boms:
        bad += len(py_boms)
        print(f"  FAIL  {len(py_boms)} .py file(s) gained a UTF-8 BOM (not in the pinned baseline):")
        for rel in py_boms:
            print(f"          {rel}")
        print("        ⛔ Strip it: raw = p.read_bytes(); p.write_bytes(raw[3:])")
        print("        ‼ CAUSE: reading with encoding='utf-8-sig' (conditional) and writing")
        print("          back a BOM UNCONDITIONALLY. Preserve a BOM; never assert one.")

    if not do_repair:
        if bad:
            print(f"\n  ‼ {bad} file(s) affected. Repair with:  py -3.12 audit_encoding.py --repair")
            print("  ⛔ AND STOP EDITING DOCS WITH POWERSHELL `Get-Content`/`Set-Content` —"
                  " that is what causes this. Use the Edit tool or Python with"
                  " explicit encoding='utf-8'.")
        else:
            extra = "" if explicit else f", and no NEW BOM in any scanned .py (baseline: {len(_BOM_ALLOWED)} pinned)"
            print(f"  all {len(targets)} file(s) clean — no mojibake, no BOM{extra}")
    print("=" * 92)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
