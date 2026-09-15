#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classify every sandbox<->custom drifting file as COMMENT-ONLY or a REAL behaviour change.

⛔ WHY THIS EXISTS. `promote.py --check` answers "how many files differ". It does NOT answer the
question a promotion decision actually turns on: **does this difference change what the bot DOES?**
On 2026-09-11 a comment block added to `training_areas.py` took drift 0 -> 1, and the handoff had to
carry the claim "COMMENT-ONLY". That claim rested on an unlogged one-off `ast.dump()` comparison I
ran in a scratch file — a Tier 1 reviewer correctly flagged it as evidence nobody could reproduce.
⇒ **A claim the docs make should be re-derivable by running something committed.** This is that
something.

⛔ IT IS DELIBERATELY NOT A GATE. Drift is not an invariant — it is a NORMAL state between a sandbox
change and a user-authorised promotion. A gate here would be red for entirely correct reasons, and a
gate that is red by design teaches the reader to bypass it (`CLAUDE.md` rule 6). It is an instrument:
run it when you need to describe drift, or before proposing a promotion.

⚠ WHAT "COMMENT-ONLY" MEANS AND DOES NOT MEAN. Identical ASTs mean the two files parse to the same
program: comments, docstring-external formatting, blank lines and line wrapping may differ; nothing
the interpreter executes does. ‼ **A DOCSTRING IS NOT A COMMENT** — it is a string literal and it
lives in the AST, so a docstring edit correctly reports as a REAL difference. That is intentional:
this project reads docstrings as behaviour contracts.

Run:
    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_comment_only_drift.py
Fault arm (proves the comparison can FAIL, so a PASS means something):
    POKEBOT_COMMENTDRIFT_FAULT=1 PYTHONUTF8=1 py -3.12 probe_comment_only_drift.py
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "sandbox-pokebot"
CUSTOM = ROOT / "custom-pokebot"

#: Mirror of `promote.py`'s comparison scope. Kept narrow on purpose: root scripts, profiles/ and
#: *.yml are runtime state and are EXPECTED to differ, so including them would bury the signal.
SCOPE = ("modules", "plugins")

FAULT = os.environ.get("POKEBOT_COMMENTDRIFT_FAULT", "")


def _bytes_norm(path: Path) -> bytes:
    """Newline-normalised bytes — same rule as `promote.py._digest`."""
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _norm(path: Path) -> str | None:
    """AST dump with positions discarded. Returns None if the file cannot be parsed."""
    try:
        return ast.dump(ast.parse(path.read_text(encoding="utf-8")), include_attributes=False)
    except (SyntaxError, UnicodeDecodeError) as error:
        print(f"    !! could not parse {path}: {error}")
        return None


def main() -> int:
    if not SANDBOX.is_dir() or not CUSTOM.is_dir():
        print("  ⛔ sandbox-pokebot / custom-pokebot not found — nothing to compare.")
        return 2

    differing: list[Path] = []
    for sub in SCOPE:
        for src in sorted((SANDBOX / sub).rglob("*.py")):
            if "__pycache__" in src.parts:
                continue
            rel = src.relative_to(SANDBOX)
            dst = CUSTOM / rel
            if not dst.exists():
                differing.append(rel)
                continue
            if src.read_bytes() != dst.read_bytes():
                differing.append(rel)

    print("=" * 92)
    print("COMMENT-ONLY DRIFT CLASSIFIER — sandbox-pokebot vs custom-pokebot")
    print("=" * 92)
    print(f"  scope: {' + '.join(s + '/' for s in SCOPE)}, *.py only")
    print(f"  drifting files: {len(differing)}")
    if not differing:
        print("\n  ✅ NO DRIFT. The two forks' compared trees are byte-identical.")
        print("=" * 92)
        return 0

    cosmetic, real, unreadable, eol_only = [], [], [], []
    for rel in differing:
        src, dst = SANDBOX / rel, CUSTOM / rel
        if not dst.exists():
            real.append((rel, "exists only in sandbox — a NEW module, never cosmetic"))
            continue
        # ⛔ CLASSIFY LINE-ENDING-ONLY *BEFORE* THE AST COMPARE, AND AS ITS OWN CLASS (2026-09-15).
        #   Such a pair DOES have identical ASTs, so it used to land in COMMENT-ONLY — true, and
        #   misleading: "the comments differ" sends a reader hunting for a textual difference that
        #   is not there. git stores ONE blob for both copies.
        # ‼ `FAULT != "1"` so the fault arm below still reaches its target: the fault corrupts the
        #   AST compare, and a short-circuit above it would leave the fault silently un-firing —
        #   exactly the failure that arm's own comment says it was written to avoid.
        if FAULT != "1" and _bytes_norm(src) == _bytes_norm(dst):
            eol_only.append(rel)
            continue
        a, b = _norm(dst), _norm(src)
        if FAULT == "1" and rel.as_posix().endswith(".py") and a is not None:
            # ⛔ Anchor the fault on the COMPARISON, not on the file's text: an earlier attempt at a
            # fault arm in this project edited source text and silently missed its target, then
            # printed a PASS. Corrupting one side of the compare cannot miss.
            a = a + ",FAULT_INJECTED"
        if a is None or b is None:
            unreadable.append(rel)
        elif a == b:
            cosmetic.append(rel)
        else:
            real.append((rel, "ASTs differ"))

    if eol_only:
        print(f"\n  〜 LINE-ENDING-ONLY — identical bytes modulo CRLF/LF, ONE git blob ({len(eol_only)}):")
        for rel in eol_only:
            print(f"       {rel.as_posix()}")
        print("       ⇒ NOT drift at all. Do not promote; git would record an empty commit.")
    if cosmetic:
        print(f"\n  \U0001f4dd COMMENT-ONLY — ASTs identical, zero behaviour difference ({len(cosmetic)}):")
        for rel in cosmetic:
            print(f"       {rel.as_posix()}")
        print("       ⇒ promoting these is OPTIONAL and COSMETIC.")
    if real:
        print(f"\n  ⚠ REAL BEHAVIOUR DIFFERENCE ({len(real)}):")
        for rel, why in real:
            print(f"       {rel.as_posix()}  ({why})")
        print("       ⇒ ⛔ promotion is the USER's call, and must be verified by DRIVING `--build custom`.")
    if unreadable:
        print(f"\n  ⛔ COULD NOT CLASSIFY ({len(unreadable)}): " + ", ".join(r.as_posix() for r in unreadable))

    print("=" * 92)
    if FAULT == "1":
        if cosmetic:
            print("  ⛔⛔ FAULT ARM DID NOT REACH THE COMPARISON — this probe proves nothing.")
            return 1
        print("  ✅ FAULT ARM: with one side corrupted, NOTHING classifies as comment-only — it has teeth.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
