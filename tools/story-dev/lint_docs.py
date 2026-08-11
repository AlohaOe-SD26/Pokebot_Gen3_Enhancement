"""Enforce the PROJECT KNOWLEDGE documentation rules MECHANICALLY. No emulator — seconds.

‼‼ WHY THIS EXISTS — the central finding of the 2026-08-11 review
(`PROJECT KNOWLEDGE/26-REVIEW-AND-HARDENING-PLAN-2026-08-11.md`):

    Of 164 logged mistakes in 26 days, **at least 12 are self-admitted REPEATS**, and several were
    committed while the author knew the rule — *"having already written the rule against it"*,
    *"an hour after writing a rule against exactly that"*, *"the second time"*, *"THIRD removal-
    shaped feature in a week"*.

**An advisory rule in a document has a measurably poor prevention rate.** What actually held were
the rules converted into code that REFUSES — 87 `repro_*.py`, 51 hard-failing scripts, and
`gemini_relay.py`, whose own comment records that a doc rule failed where code succeeded.

This linter converts `CLAUDE.md`'s documentation rules into that shape. It **exits 1**.

‼ DESIGN RULE: PRECISION OVER COVERAGE. A linter with false positives gets ignored, and an ignored
linter is an advisory rule with extra steps. Every check here is exact and mechanically decidable;
fuzzy things (is this claim supported? is this rate meaningful?) are deliberately left to humans and
reported as INFO, never as failures.

RULES ENFORCED (failures):
  R1  a CURRENT-STATE file (01-05) must contain no `# HISTORY` block
  R2  a CURRENT-STATE file must contain at most ONE "START HERE" / "YOU ARE HERE" banner
  R3  a CURRENT-STATE file must stay under its line budget
  R4  no two PROJECT KNOWLEDGE docs may share a leading NN- number
  R5  every file named in 00-README's reading order must exist

REPORTED AS INFO (never fails the run):
  I1  count of completed `- [x]` items sitting in the punch list
  I2  count of `- [~]` partial items that do not say what remains

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 lint_docs.py
      PYTHONUTF8=1 py -3.12 lint_docs.py --list   # show every offending line, for fixing
"""

from __future__ import annotations

import pathlib
import re
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[2]
DOCS = REPO / "PROJECT KNOWLEDGE"

# ‼ From CLAUDE.md: "01, 02, 03, 04, 05 are CURRENT-STATE files: edit them in place so they always
# describe present reality. Remove stale content." 06/07/08 are APPEND-ONLY history and are exempt.
CURRENT_STATE = ("01-", "02-", "03-", "04-", "05-")

# Budgets are generous — the point is to catch an ARCHIVE forming inside a current-state file, not
# to police prose. 04-HANDOFF was 3,239 lines with only its first 163 current when this was written.
LINE_BUDGET = {"01-": 700, "02-": 700, "03-": 3600, "04-": 900, "05-": 3000}

BANNER_RE = re.compile(r"^#{1,3}\s.*\b(START HERE|YOU ARE HERE)\b", re.I | re.M)
HISTORY_RE = re.compile(r"^#{1,2}\s+(?:‼\s*)?HISTORY\b", re.I | re.M)

failures: list[str] = []
infos: list[str] = []
show = "--list" in sys.argv


def fail(rule: str, msg: str) -> None:
    failures.append(f"{rule}  {msg}")


docs = sorted(p for p in DOCS.glob("*.md"))
if not docs:
    raise SystemExit(f"lint cannot run: no docs found under {DOCS}")

print("=" * 92)
print("DOCUMENTATION LINT — CLAUDE.md's rules, enforced instead of advised")
print("=" * 92)

# ---------- R4: number collisions ----------
by_number: dict[str, list[str]] = defaultdict(list)
for p in docs:
    m = re.match(r"^(\d{2})-", p.name)
    if m:
        by_number[m.group(1)].append(p.name)
for num, names in sorted(by_number.items()):
    if len(names) > 1:
        fail("R4", f"doc number {num}- is used by {len(names)} files: {', '.join(names)}")

# ---------- R1/R2/R3: current-state hygiene ----------
print("\nCURRENT-STATE FILES (01-05) — must describe PRESENT reality")
print(f"  {'file':<44}{'lines':>7}{'budget':>8}  {'HISTORY':>8}{'banners':>9}")
for p in docs:
    prefix = p.name[:3]
    if prefix not in CURRENT_STATE:
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.count("\n") + 1
    budget = LINE_BUDGET.get(prefix, 1500)
    hist = HISTORY_RE.findall(text)
    banners = BANNER_RE.findall(text)
    flag = ""
    if hist:
        fail("R1", f"{p.name}: {len(hist)} `# HISTORY` block(s) inside a CURRENT-STATE file")
        flag = " <-"
    if len(banners) > 1:
        fail("R2", f"{p.name}: {len(banners)} START-HERE/YOU-ARE-HERE banners (max 1) — a reader "
                   f"cannot tell which is current")
        flag = " <-"
    if lines > budget:
        fail("R3", f"{p.name}: {lines} lines exceeds its {budget}-line budget — an archive is "
                   f"forming inside a current-state file")
        flag = " <-"
    print(f"  {p.name:<44}{lines:>7}{budget:>8}  {len(hist):>8}{len(banners):>9}{flag}")
    if show and (hist or len(banners) > 1):
        for m in HISTORY_RE.finditer(text):
            print(f"      HISTORY @ line {text[:m.start()].count(chr(10)) + 1}: {m.group(0)[:70]}")
        for m in BANNER_RE.finditer(text):
            print(f"      BANNER  @ line {text[:m.start()].count(chr(10)) + 1}: {m.group(0)[:70]}")

# ---------- R5: the reading order must point at real files ----------
readme = DOCS / "00-README.md"
if readme.is_file():
    named = set(re.findall(r"`(\d{2}-[A-Za-z0-9._-]+\.md)`", readme.read_text(encoding="utf-8")))
    existing = {p.name for p in docs}
    for name in sorted(named - existing):
        fail("R5", f"00-README's reading order names `{name}`, which does not exist")

# ---------- INFO ----------
punch = DOCS / "03-PUNCH-LIST.md"
if punch.is_file():
    t = punch.read_text(encoding="utf-8", errors="replace")
    done = len(re.findall(r"^- \[x\]", t, re.M))
    partial = re.findall(r"^- \[~\] (.+)$", t, re.M)
    vague = [x for x in partial if not re.search(r"remain|outstanding|todo|left to|still", x, re.I)]
    infos.append(f"I1  {done} completed `[x]` items are sitting in the punch list (a CURRENT-STATE "
                 f"file). Consider moving closed ones to 07-CHANGELOG.")
    infos.append(f"I2  {len(vague)} of {len(partial)} `[~]` partial items do not say what REMAINS "
                 f"on their headline (the marker is load-bearing — see 03's own note).")

print("\nINFO (never fails the run)")
for i in infos:
    print(f"  {i}")

print("\n" + "=" * 92)
if failures:
    print(f"FAILED — {len(failures)} rule violation(s):")
    for f in failures:
        print(f"  {f}")
    print("\n‼ These are CLAUDE.md's own rules. Re-run with --list to see the offending lines.")
    print("  Move stale content to an append-only file; do not delete hard-won detail.")
    sys.exit(1)
print("ALL DOCUMENTATION RULES PASS.")
