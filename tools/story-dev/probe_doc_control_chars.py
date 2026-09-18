#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GATE — no INVISIBLE control character may sit in a PROJECT KNOWLEDGE document.

⛔⛔ WHY THIS EXISTS (2026-09-17). A changelog entry was written through a shell, and `\\b` inside the
shell-quoted string became a **literal 0x08 BACKSPACE BYTE** in the committed-bound document. Every
terminal rendered it as an empty pair of backticks, so it read as "the shell deleted my text" — the
wrong diagnosis. It was *present and invisible*. It surfaced only because an assertion string failed
to match and the bytes were inspected instead of the rendering.

‼‼ AND IT IS NOT THE FIRST. A sweep of every `PROJECT KNOWLEDGE/*.md` found a SECOND, older 0x08 in
`28-HANDOFF-ARCHIVE.md` — inside a sentence explaining that *"a literal control character in `.py`
source is a hard failure, because `\\b` compiled to a BACKSPACE twice in one day and the gate still
passed."* ⇒ **three independent sessions have now put a backspace byte into prose ABOUT the backspace
bug, and nothing caught any of them.**

⭐ THE GAP THIS CLOSES. Control characters in SOURCE are gated (`#24-p2headergate` (C)). Nothing
checked the DOCS. `lint_docs.py` and `audit_doc_consistency.py` both passed a file containing 0x08.

⭐ WHY IT IS SAFE TO ENFORCE — and note this is a property about the INPUT DOMAIN, not about the
checker's cleverness, which is the distinction `probe_retraction_coverage.py` got wrong the same day:
a Markdown document has no legitimate use for any C0 control character except TAB and NEWLINE. There
is nothing to judge, so there is nothing to mis-judge. A hit is a defect by construction.

RUN:  py -3.12 probe_doc_control_chars.py             # the gate (exit 0 = pass)
      py -3.12 probe_doc_control_chars.py --self-test # FAULT TEST
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

# ⛔ UTF-8 or the gate dies while printing its own finding (three gates carried that bug; see
# run_gates.py's header). Belt and braces: run_gates.py also forces a UTF-8 child.
sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "PROJECT KNOWLEDGE"

#: The ONLY control characters a Markdown document may contain.
ALLOWED = {"\n", "\t"}

#: Also rejected: DEL, and the zero-width / bidi characters that are invisible but not C0.
#: ‼ These are included because the failure MODE is identical — text that is present and unreadable —
#: even though the mechanism (copy-paste, a smart editor) differs from the shell-escape one.
EXTRA_BAD = {
    "\x7f": "DELETE",
    "​": "ZERO WIDTH SPACE",
    "‌": "ZERO WIDTH NON-JOINER",
    "‍": "ZERO WIDTH JOINER",
    "⁠": "WORD JOINER",
    "﻿": "ZERO WIDTH NO-BREAK SPACE (BOM)",
    "‪": "LEFT-TO-RIGHT EMBEDDING",
    "‫": "RIGHT-TO-LEFT EMBEDDING",
    "‭": "LEFT-TO-RIGHT OVERRIDE",
    "‮": "RIGHT-TO-LEFT OVERRIDE",
}


def _name(ch: str) -> str:
    if ch in EXTRA_BAD:
        return EXTRA_BAD[ch]
    try:
        return unicodedata.name(ch)
    except ValueError:
        return {0x08: "BACKSPACE", 0x00: "NUL", 0x1b: "ESCAPE", 0x0c: "FORM FEED",
                0x0d: "CARRIAGE RETURN"}.get(ord(ch), "C0 CONTROL")


def scan_text(text: str) -> list:
    """Return [(line, col, char)] for every illegal character.

    ‼ CRLF IS NORMALISED HERE, NOT IN THE CALLER — its own fault arm caught that. ARM 3 passed
    `"...\\r\\n..."` straight in and the CR was reported, because the normalisation lived in
    `scan_docs()` while the arm exercised `scan_text()`. The gate was right and the CONTRACT was
    split: a helper whose correctness depends on the caller pre-cleaning its input will eventually
    be called without it. A lone CR is still a finding (ARM 4) — only the CRLF PAIR is legitimate.
    """
    text = text.replace("\r\n", "\n")
    out = []
    line, col = 1, 1
    for ch in text:
        if ch == "\n":
            line, col = line + 1, 1
            continue
        if (ord(ch) < 32 and ch not in ALLOWED) or ch in EXTRA_BAD:
            out.append((line, col, ch))
        col += 1
    return out


def scan_docs() -> list:
    """Scan EVERY `.md` under PROJECT KNOWLEDGE, recursively.

    ⛔⛔ `rglob`, NOT `glob` — A TIER 1 REVIEWER CAUGHT THIS AND IT MATTERED. The first version used
    `DOCS.glob("*.md")`, which is NON-RECURSIVE: **34 of 192 files**. The 158 it skipped are almost
    entirely `ai-research-notes/` — **machine-relayed Gemini output, i.e. precisely the content most
    likely to reproduce this bug class next**, and load-bearing enough that
    `audit_doc_consistency.py`'s citation resolver reads it. Meanwhile the docstring claimed "every
    PROJECT KNOWLEDGE/*.md". ⇒ the gate was narrower than its own claim, in the one direction that
    matters. Recursing adds 0 findings today, so this is scope, not a regression.
    ‼ `lint_docs.py` shares the non-recursive convention, so this was inherited, not invented — which
    is exactly why it survived review until someone counted the files instead of reading the glob.
    """
    findings = []
    for p in sorted(DOCS.rglob("*.md")):
        # ‼ newline=""  so Python does NOT translate CRLF -> LF. A stray lone CR is a real finding
        # and universal-newline mode would silently hide it — the same "the tool cleaned it up for
        # you" trap that makes control characters hard to see in the first place.
        # ‼ `Path.read_text(newline=...)` only exists on 3.13+; this project runs 3.12, so open()
        # explicitly rather than silently losing the no-translation guarantee the comment above needs.
        with open(p, encoding="utf-8", errors="replace", newline="") as fh:
            text = fh.read()
        for line, col, ch in scan_text(text):   # scan_text normalises CRLF itself
            findings.append((p.name, line, col, ch))
    return findings


def _report(findings: list) -> int:
    bar = "=" * 92
    print(bar)
    print("DOC CONTROL CHARACTERS — invisible bytes in PROJECT KNOWLEDGE/*.md")
    print(bar)
    if not findings:
        print("  no control or invisible characters found.")
        print(bar)
        return 0
    for name, line, col, ch in findings:
        print("  %s:%d col %d  U+%04X  %s" % (name, line, col, ord(ch), _name(ch)))
    print(bar)
    print("  FAIL: %d invisible character(s)." % len(findings))
    print("  ⇒ These render as NOTHING in a terminal, so the document looks correct while being")
    print("    wrong. Verify with repr() or a byte scan — never by reading it.")
    # ‼ THE REMEDIATION IS PER-CAUSE. A reviewer flagged that a single "don't use a shell" message is
    # WRONG ADVICE for a BOM or a zero-width space, whose cause is an editor default or a paste — and
    # advice that does not fit the finding is how a reader learns to ignore the gate.
    if any(ord(c) < 32 or c == "\x7f" for *_, c in findings):
        print("  ⇒ C0/DEL: usual cause is prose written through a SHELL-QUOTED string, where an")
        print("    escape such as backslash-b becomes the byte it names. FIX: write the text from a")
        print("    FILE and run the file — never pass prose as a shell argument.")
    if any(c in EXTRA_BAD and ord(c) >= 32 for *_, c in findings):
        print("  ⇒ Zero-width / BOM / bidi: usual cause is a PASTE from a web page or an editor")
        print("    writing a byte-order mark. FIX: retype the span, or strip it explicitly; check")
        print("    the editor's encoding setting is UTF-8 WITHOUT BOM.")
    print(bar)
    return 1


def self_test() -> int:
    bar = "=" * 92
    print(bar)
    print("SELF-TEST (fault injection)")
    print(bar)
    ok = True

    real = scan_docs()
    print("  ARM 1  real docs clean               -> %d finding(s)  %s"
          % (len(real), "PASS" if not real else "FAIL"))
    if real:
        ok = False
        for f in real[:5]:
            print("         %s:%d U+%04X" % (f[0], f[1], ord(f[3])))

    # ARM 2 — the exact historical defect: a backspace between backticks.
    hit = scan_text("a line\nwith `" + chr(8) + "` in it\n")
    print("  ARM 2  injected BACKSPACE (0x08)     -> %d finding(s)  %s"
          % (len(hit), "PASS" if len(hit) == 1 else "FAIL"))
    if len(hit) != 1:
        ok = False
    elif hit[0][:2] != (2, 7):
        print("         ⚠ position reported %s, expected (2, 7)" % (hit[0][:2],))
        ok = False

    # ARM 3 — legitimate whitespace must NEVER fire (the false-positive arm).
    clean = scan_text("# Title\n\n\tindented\ttabs\r\nand text\n")
    print("  ARM 3  newlines/tabs/CRLF allowed    -> %d finding(s)  %s"
          % (len(clean), "PASS" if not clean else "FAIL"))
    if clean:
        ok = False

    # ARM 4 — a LONE carriage return is NOT legitimate and must fire.
    lone = scan_text("text with a lone \r return\n")
    print("  ARM 4  lone CR (not CRLF) caught     -> %d finding(s)  %s"
          % (len(lone), "PASS" if len(lone) == 1 else "FAIL"))
    if len(lone) != 1:
        ok = False

    # ARM 5 — invisible-but-not-C0 characters.
    zw = scan_text("zero​width\n")
    print("  ARM 5  zero-width space caught       -> %d finding(s)  %s"
          % (len(zw), "PASS" if len(zw) == 1 else "FAIL"))
    if len(zw) != 1:
        ok = False

    # ARM 6 — every character the gate rejects must be NAMEABLE, or its report is unreadable.
    unnamed = [c for c in [chr(8), chr(0), "\x1b", "​", "﻿"] if not _name(c)]
    print("  ARM 6  all rejects are nameable      -> %d unnamed  %s"
          % (len(unnamed), "PASS" if not unnamed else "FAIL"))
    if unnamed:
        ok = False

    print(bar)
    print("  SELF-TEST %s" % ("PASS" if ok else "FAIL"))
    print(bar)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    raise SystemExit(_report(scan_docs()))
