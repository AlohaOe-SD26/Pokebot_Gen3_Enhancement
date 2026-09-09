"""GATE — no UNDEFINED NAME may exist in the story surface. Exits 1.

‼ WHY THIS EXISTS. Python resolves a name at RUNTIME, so a function that references a name it never
imported is a perfectly valid module that raises `NameError` only when that branch is reached. This
codebase imports its helpers INSIDE functions (to keep `early_game.py` importable), which makes the
mistake easy and its blast radius branch-shaped: the happy path is green and the error path dies.

It has now bitten this project FOUR times:
  * the HM-learner branch (2026-07-23) and survival mode (2026-07-26) — both `UnboundLocalError`
    from using a module-level name in a method that imports locally, the second time with the
    warning commented sixteen lines above;
  * §Ch19's `fight_alongside_steven` (2026-08-12) — called `_ch14_say` without importing it, so the
    leg died the moment it reached Steven, after a five-minute drive to get there;
  * ‼ and `modules/battle_move_replacing.py:280` (KI-65), where `party_index` is unbound inside the
    "HM moves can't be forgotten" recovery — wrapped in `except Exception: move_to_forget = 4`,
    i.e. DECLINE. That branch's whole purpose is to re-pick a different slot, and it has never once
    executed. The `except` returns a legal-looking outcome, so nothing ever looked wrong.

The first three cost a run each. The fourth is a live defect that no test noticed, and pyflakes
named it in under a second. So this is a gate rather than advice.

SCOPE IS DELIBERATELY THE STORY SURFACE, NOT THE WHOLE TREE. Upstream `modules/` carries ~10
`TYPE_CHECKING`-only annotation names that pyflakes reports and that are harmless at runtime; a gate
that reports those every run would be ignored within a week, which is the failure mode this project
has already documented for noisy gates. Our own code is held to ZERO.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_undefined_names.py
"""

import argparse
import pathlib
import re
import subprocess
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


# ‼ `--build` — added 2026-08-23 (`#24-p4residuals` (e)). This gate hardcoded
# `sandbox-pokebot`, so the identical defect landing in `custom-pokebot` — THE FORK THAT
# SHIPS — was invisible to it. Default stays `sandbox` so nothing about the standing suite
# changes; `--build custom` is for verifying a promotion. Idiom copied from
# `repro_pid_identity_key.py`, which already had it.
_ap = argparse.ArgumentParser(add_help=True)
_ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"],
                 help="which fork to test (default sandbox; use custom to verify a promotion)")
_ARGS, _ = _ap.parse_known_args()

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / f"{_ARGS.build}-pokebot"
# ‼ REFUSE LOUDLY when the target is absent. This used to hand the missing directory
# straight to `subprocess` and die with a bare `NotADirectoryError` — failing for the wrong
# stated reason. Its sibling `repro_no_silent_except.py` already refused explicitly.
if not BUILD.is_dir():
    raise SystemExit(f"‼ nothing to scan under {BUILD} — refusing to report success")

#: Our code — the files this project writes. Held to ZERO undefined names.
OWNED = [
    "modules/story",
    "plugins/custom_modes",
]

#: ‼ THE HARNESS EARNED ITS PLACE HERE THE FIRST TIME IT WAS SCANNED (2026-08-12). It was outside
#: the gate because it lives in `tools/`, not in the build — and it contained
#: `os.environ.get(...)` in a method that never imported `os`, so `MagmaHideoutMode`'s anchor
#: capture raised `NameError` **only on the SUCCESS path**: every failing run returned before
#: reaching it, and a passing one would have died at the exact moment it had something worth
#: saving. A driver is code we write and drive for hours; it belongs under the same rule as the bot.
EXTRA_FILES = ["story_harness.py"]

#: ‼ Matches only real undefined-name findings. pyflakes also emits
#: "'from x import *' used; unable to detect undefined names", which contains the same words and is
#: NOT a finding — grepping for the bare phrase counts those and turns a clean run into a failure.
UNDEFINED = re.compile(r": undefined name '")

print("=" * 96)
print("GATE — undefined names in the story surface (a NameError waiting for the right branch)")
print("=" * 96)

HERE = pathlib.Path(__file__).parent
targets = [str(BUILD / path) for path in OWNED]
targets += [str(HERE / name) for name in EXTRA_FILES if (HERE / name).is_file()]
try:
    result = subprocess.run(
        [sys.executable, "-m", "pyflakes", *targets],
        capture_output=True,
        text=True,
        cwd=str(BUILD),
    )
except FileNotFoundError:
    print("‼ pyflakes is not installed — this gate cannot run, which is NOT a pass.")
    print("  install with:  py -3.12 -m pip install pyflakes")
    raise SystemExit(1)

lines = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
findings = [line for line in lines if UNDEFINED.search(line)]

# ‼ PRINT WHAT WAS SEARCHED. A gate that scanned nothing and a gate that found nothing print the
# same word otherwise — the lesson from `audit_flag_names.py`, which silently checked two files.
scanned = sorted(p for path in OWNED for p in (BUILD / path).rglob("*.py"))
scanned += [HERE / name for name in EXTRA_FILES if (HERE / name).is_file()]
print(f"\nscanned {len(scanned)} file(s) under {OWNED} + {EXTRA_FILES}")
print(f"pyflakes emitted {len(lines)} diagnostic(s); {len(findings)} of them are undefined names\n")

if findings:
    print("UNDEFINED NAMES (each one is a NameError the moment its branch is reached):")
    for line in findings:
        print(f"  {line}")
    print("\nRESULT: FAIL")
    raise SystemExit(1)

print("RESULT: ALL PASS — no undefined names in the story surface.")
print("\n‼ Note the deliberate scope: upstream `modules/` still reports ~10 TYPE_CHECKING-only")
print("  annotation names (harmless) AND `battle_move_replacing.py:280 party_index` (KI-65, a REAL")
print("  latent defect that is NOT fixed). Widening this gate means fixing KI-65 first.")
