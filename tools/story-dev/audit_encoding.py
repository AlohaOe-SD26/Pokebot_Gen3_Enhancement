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


def repair_line(line: str) -> "str | None":
    """The reversal, returned ONLY when it provably reduces the damage (else None)."""
    if suspect_count(line) == 0:
        return None
    try:
        candidate = line.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
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
    print(f"\nSELF-TEST {'PASS' if fails == 0 else 'FAIL'} ({fails} deviation(s))")
    return 0 if fails == 0 else 1


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
    if not do_repair:
        if bad:
            print(f"\n  ‼ {bad} file(s) affected. Repair with:  py -3.12 audit_encoding.py --repair")
            print("  ⛔ AND STOP EDITING DOCS WITH POWERSHELL `Get-Content`/`Set-Content` —"
                  " that is what causes this. Use the Edit tool or Python with"
                  " explicit encoding='utf-8'.")
        else:
            print(f"  all {len(targets)} file(s) clean — no mojibake, no BOM")
    print("=" * 92)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
