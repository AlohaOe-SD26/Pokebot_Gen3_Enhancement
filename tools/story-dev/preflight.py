"""ONE command to run before touching anything. Aggregates the project's hard gates and EXITS 1.

‼‼ WHY. The 2026-08-11 review found that **at least 12 of 164 logged mistakes are self-admitted
REPEATS**, several committed while the author knew the rule — *"having already written the rule
against it"*. An advisory rule in a document has a measurably poor prevention rate; the rules that
held were the ones converted into **code that refuses**. This is the front door for those.

WHAT IT CHECKS (each is a hard gate unless marked):
  1. **GIT SYNC** — behind / ahead / diverged / dirty. `CLAUDE.md`'s session-start ritual says
     BEHIND → pull first, and AHEAD or DIVERGED → **STOP and report to the user**, because it means
     a previous session ended without completing its wrap-up and reconciling that is the USER's
     call. A SessionStart hook already attempts this; this makes it blocking.
  2. **FIXTURES** — `verify_fixtures.py`: every PINNED save still byte-identical. Closes the family
     that cost three separate results in one day.
  3. **DOCS** — `lint_docs.py`: CLAUDE.md's own documentation rules.
  4. **BATCH FREEZE** (advisory, loud) — is an `x4_headless` batch writing right now? If so,
     `sandbox-pokebot/` and `tools/story-dev/` must NOT be edited: restarted lanes re-import from
     disk. Docs stay safe.

‼ DESIGN: it SHELLS OUT to the existing scripts rather than reimplementing them, so each stays
independently runnable and there is exactly one definition of each rule.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 preflight.py
      PYTHONUTF8=1 py -3.12 preflight.py --quiet    # only failures
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")

import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
QUIET = "--quiet" in sys.argv

hard_failures: list[str] = []
warnings: list[str] = []


def run(cmd: list[str], cwd: pathlib.Path) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as error:  # noqa: BLE001
        # ‼ A gate that cannot RUN must fail, not pass. "I broke" is not "no problem" — that
        # distinction is its own mistake family in 08-MISTAKES.
        return 99, f"{type(error).__name__}: {error}"


def section(title: str) -> None:
    if not QUIET:
        print(f"\n{title}")
        print("-" * len(title))


print("=" * 88)
print("PREFLIGHT — run this before touching anything")
print("=" * 88)

# ---------------------------------------------------------------- 1. GIT SYNC
section("1. GIT SYNC")
rc, out = run(["git", "status", "--porcelain=v1", "-b"], REPO)
if rc != 0:
    hard_failures.append(f"git status failed: {out.strip()[:160]}")
else:
    lines = out.splitlines()
    branch_line = lines[0] if lines else ""
    dirty = [l for l in lines[1:] if l.strip()]
    ahead = "ahead" in branch_line
    behind = "behind" in branch_line
    if not QUIET:
        print(f"  {branch_line.strip()}")
        # ‼ NAME THEM, DO NOT JUST COUNT THEM (2026-08-16). A bare count cannot tell a cold start
        # whether the dirt is EXPECTED — `party_accounting_ledger.jsonl` is TRACKED and every
        # `story_harness.py` drive appends to it — or something nobody meant to leave behind. A
        # Tier 2 agent hit exactly that: a WARN telling it to "review with the user before pulling",
        # against a handoff STATE row promising a clean tree, and no way to reconcile the two.
        print(f"  uncommitted files: {len(dirty)}")
        for entry in dirty[:10]:
            note = ""
            if "party_accounting_ledger" in entry:
                note = "   <- EXPECTED after any driver run; COMMIT it, never `git checkout --` it"
            print(f"      {entry.strip()}{note}")
        if len(dirty) > 10:
            print(f"      ... and {len(dirty) - 10} more")
    if behind and ahead:
        hard_failures.append(
            "git is DIVERGED from the remote. ‼ CLAUDE.md: STOP and report to the user — this "
            "means a previous session ended without its wrap-up. Never auto-push, build on, or "
            "discard it."
        )
    elif ahead:
        hard_failures.append(
            "git is AHEAD of the remote (unpushed commits). ‼ CLAUDE.md: STOP and report — "
            "reconciling unpushed work is the USER's call."
        )
    elif behind:
        hard_failures.append(
            "git is BEHIND the remote. Pull first — the remote is the truth, because a completed "
            "wrap-up always ends with a confirmed push."
        )
    if dirty:
        warnings.append(
            f"{len(dirty)} uncommitted file(s). Review with the user before pulling; never discard "
            f"local work to make a pull succeed."
        )

# ---------------------------------------------------------------- 2. FIXTURES
section("2. FIXTURES (PINNED saves byte-identical)")
rc, out = run([sys.executable, "verify_fixtures.py"], HERE)
if not QUIET:
    for l in out.splitlines():
        if l.strip().startswith(("OK", "‼", "drifted", "MISSING", "ALL")):
            print(f"  {l.strip()[:100]}")
if rc == 99:
    hard_failures.append(f"verify_fixtures.py could not RUN: {out[:160]}")
elif rc != 0:
    hard_failures.append(
        "a PINNED save fixture has DRIFTED. Do not trust any result resting on it. A driver "
        "probably overwrote it — RECOVER it; only use --update if the change was intended."
    )

# ---------------------------------------------------------------- 3. DOCS
section("3. DOCUMENTATION RULES")
rc, out = run([sys.executable, "lint_docs.py"], HERE)
if not QUIET:
    for l in out.splitlines():
        if l.strip().startswith(("R1", "R2", "R3", "R4", "R5", "ALL DOCUMENTATION")):
            print(f"  {l.strip()[:100]}")
if rc == 99:
    hard_failures.append(f"lint_docs.py could not RUN: {out[:160]}")
elif rc != 0:
    hard_failures.append("documentation rules are violated — run `py -3.12 lint_docs.py --list`.")

# ---------------------------------------------------------------- 4. BATCH FREEZE
section("4. BATCH FREEZE (is a batch writing right now?)")
runs = HERE / "x4-runs"
live = None
if runs.is_dir():
    newest = None
    for d in runs.iterdir():
        if not d.is_dir():
            continue
        try:
            mt = max((f.stat().st_mtime for f in d.rglob("*") if f.is_file()), default=0)
        except Exception:  # noqa: BLE001
            mt = 0
        if newest is None or mt > newest[1]:
            newest = (d, mt)
    if newest and newest[1] > 0:
        age_min = (time.time() - newest[1]) / 60.0
        if not QUIET:
            print(f"  newest batch dir: {newest[0].name}  (last write {age_min:.1f} min ago)")
        # ‼ EVIDENCE-BASED, not process-list based: a live batch writes constantly. 5 minutes is
        # comfortably longer than any gap between lane writes and short enough to not linger.
        if age_min < 5:
            live = newest[0].name
            warnings.append(
                f"‼ A BATCH APPEARS TO BE RUNNING ({live}, written {age_min:.1f} min ago). "
                f"DO NOT edit `sandbox-pokebot/` — restarted lanes re-import from disk. "
                f"`tools/story-dev/` and docs ARE safe, with one exception: do not edit "
                f"`x4_headless.py` itself, since it spawns and restarts the lanes."
            )
    elif not QUIET:
        print("  no batch directories found")

# ---------------------------------------------------------------- verdict
print("\n" + "=" * 88)
for w in warnings:
    print(f"WARN  {w}")
if hard_failures:
    print(f"\n‼ PREFLIGHT FAILED — {len(hard_failures)} blocking issue(s):")
    for f in hard_failures:
        print(f"  * {f}")
    print("\nFix these before doing anything else. They are the gates that repeat mistakes slip past.")
    sys.exit(1)
print("PREFLIGHT PASS" + ("  (see WARN above)" if warnings else ""))
print("=" * 88)
