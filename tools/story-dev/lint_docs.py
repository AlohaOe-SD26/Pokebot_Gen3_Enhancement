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

# ---------- R6: every POKEBOT_* flag in bot code must be in the registry ----------
# ‼‼ FAMILY C — the family with the worst measured cost in this project's history. A flag pinned at
# 0 is usually a RESULT ("this was measured harmful"), not a leftover, and those results were
# living in code comments where nobody looks before PROPOSING a feature. On 2026-08-11 that cost a
# recommendation: "roster hygiene before bosses" was proposed as new work when it had already been
# built, measured harmful and pinned off (KI-54). Only a manual pre-build check caught it.
section_r6 = DOCS / "29-DISABLED-FEATURES-REGISTRY.md"
# ‼ WIDENED 2026-08-14 — THE OLD SCAN HAD A PROVEN HOLE, found by a cold-start audit, and it is
# rule 6's exact shape: a gate that was never fault-tested against how flags are ACTUALLY written.
# The old regex matched only `environ.get("POKEBOT_…")` literals, so it was blind to:
#   * `os.getenv("POKEBOT_ENCOUNTER_BENCHMARK")`          (stats.py — different accessor)
#   * `_TURBO_ENV = "POKEBOT_STORY_DEBUG_TURBO"`          (story_mode.py — name held in a constant,
#     the accessor never sees the literal; intro.py's POKEBOT_RNG_DECORRELATION_FRAMES likewise)
#   * `pokebot.py` / `tools/story-dev` flags               (outside the scan roots entirely)
# FIVE live flags were undocumented while the gate printed "11 flag(s) in code, 11 documented" and
# exited 0. The scan now matches ANY quoted POKEBOT_* string literal — accessor-agnostic, constant-
# agnostic — and adds pokebot.py + tools/story-dev to the roots. Comments/docstrings mentioning a
# flag also match; that is deliberate overreach in the SAFE direction: the registry documents the
# flag either way, and a phantom mention would surface as an undocumented "flag" worth deleting.
flag_re = re.compile(r'["\'](POKEBOT_[A-Z0-9_]+)["\']')
found: set[str] = set()
# ‼ BOTH FORKS — widened 2026-08-22, deep sanity check PASS 4 (INFRASTRUCTURE).
# R6 scanned ONLY `sandbox-pokebot`, so `custom-pokebot` — THE FORK THAT SHIPS — was invisible:
# 234 .py files, none of them ever read by the registry guard. A kill-switch living only in the
# promoted fork would have been documented nowhere and R6 would still have passed.
# ⚠ MEASURED BEFORE WIDENING, so this is provably non-breaking: custom's flag set is a SUBSET of
# sandbox's (17 ⊆ 21), i.e. the widened scan finds no new undocumented flag today. It is a guard
# against tomorrow, not a repair of today — which is exactly when a scope gap is cheapest to close.
bot_roots = [REPO / "sandbox-pokebot" / "modules", REPO / "sandbox-pokebot" / "plugins",
             REPO / "custom-pokebot" / "modules", REPO / "custom-pokebot" / "plugins",
             REPO / "tools" / "story-dev"]
_single_files = [REPO / "sandbox-pokebot" / "pokebot.py", REPO / "custom-pokebot" / "pokebot.py"]
for _f in _single_files:
    if _f.is_file():
        found |= set(flag_re.findall(_f.read_text(encoding="utf-8", errors="replace")))
for root in bot_roots:
    if not root.is_dir():
        continue
    for py in root.rglob("*.py"):
        # ‼ `evidence/` IS NOT BOT CODE — excluded 2026-08-22 (deep sanity check PASS 4).
        # Committed evidence includes fault-injection drivers that deliberately contain SYNTHETIC
        # flag names (`POKEBOT_TOTALLY_UNDOCUMENTED_FLAG` and friends) to prove R6 can fire. R6
        # scanned them and demanded registry rows for flags no bot will ever read — a gate firing
        # on its own test fixtures, which is the false-positive shape this project rates as worse
        # than no gate. Caught by running the suite BEFORE committing the evidence, not after.
        if "evidence" in py.parts or "__pycache__" in py.parts:
            continue
        try:
            found |= set(flag_re.findall(py.read_text(encoding="utf-8", errors="replace")))
        except Exception as error:  # noqa: BLE001 — an unreadable file is reported, never skipped
            fail("R6", f"could not read {py.name} while scanning for flags: {type(error).__name__}")

print("\nFEATURE FLAGS (POKEBOT_*) — every one must be in 29-DISABLED-FEATURES-REGISTRY.md")
if not section_r6.is_file():
    fail("R6", "29-DISABLED-FEATURES-REGISTRY.md is missing")
elif not found:
    # ‼ A scan that finds nothing must not silently pass — that is the silent-zero family.
    fail("R6", "found ZERO POKEBOT_* flags in the bot code — the scan is probably broken, "
               "since the project is known to use them")
else:
    registry = section_r6.read_text(encoding="utf-8", errors="replace")
    missing = sorted(f for f in found if f not in registry)
    print(f"  {len(found)} flag(s) in code, {len(found) - len(missing)} documented")
    for f in missing:
        fail("R6", f"`{f}` is used in bot code but is NOT in the registry — a flag pinned off is "
                   f"usually a MEASUREMENT, and it must be findable before someone re-proposes it")

    # ‼ THE REVERSE DIRECTION — added 2026-08-22, deep sanity check PASS 4.
    # R6 only ever asked "is every flag in the code documented?". The opposite rot was unguarded:
    # a registry row whose flag NO CODE READS ANY MORE. That row keeps warning future agents off
    # work that has already been deleted, which is the same cost as a stale prevention rule — and
    # `/reconcile`'s own charter says a rule whose hazard is gone must be retired, because leaving
    # it active wastes the context of everyone who reads it.
    # ⚠ MEASURED FIRST: zero orphans today (21 in code, 21 in the registry, both directions), so
    # this ships green and is a guard against future rot, not a repair.
    documented = set(re.findall(r"`(POKEBOT_[A-Z0-9_]+)`", registry))
    orphaned = sorted(f for f in documented if f not in found)
    for f in orphaned:
        fail("R6", f"`{f}` has a registry row but NO code in either fork reads it — the feature is "
                   f"gone and the row now misleads. Retire the row (or restore the reader).")

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
