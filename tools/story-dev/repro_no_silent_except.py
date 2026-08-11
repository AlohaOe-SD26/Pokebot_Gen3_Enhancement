"""A guard that cannot tell "no" from "I broke" is worse than no guard. NO EMULATOR — AST scan.

‼‼ THE FAMILY THIS CLOSES (family **B** of the 2026-08-11 review). Every one of these is a real
entry in `08-MISTAKES.md`:

* *"A silent `except` turned a scope bug into 252 wasted encounters"* (2026-07-23)
* *"A bare `except Exception` around 'bookkeeping' hid a NameError for two batches"* (2026-08-03)
* *"A test stub missing a constant disabled the logic under test, SILENTLY — **the second time**"*
  (2026-07-30)
* *"`get_item_bag().tm_hm_case` raised AttributeError, the `except` swallowed it, and the probe
  announced 'HM06 is not in the bag' on a save that has it"* (2026-08-09)
* *"`box_views()` failed with TypeError for two days and `find_in_box` swallowed it, so 'the mon
  isn't there' and 'we cannot see the box' printed identically"*

**The shape is always the same**: an exception handler that neither re-raises nor says anything, so
a BROKEN reader reports a clean negative and the negative is believed.

WHAT THIS ENFORCES. In the scanned modules, every `except` block must do at least ONE of:
  1. **re-raise** (`raise`) — the error is not swallowed;
  2. **say something** — a `log(...)`, `debug_logger.*`, `print(...)`, `console.print(...)`, or
     assign to an `error`/`_error`-shaped variable that is then reported;
  3. **carry an explicit justification comment** — `# noqa: BLE001` with prose, which this project
     already uses well ("telemetry must never break the teach", "a probe reports, it does not
     crash"). This makes that existing convention LOAD-BEARING instead of optional.

‼ SCOPE IS DELIBERATELY NARROW — the story modules and battle strategies, i.e. the code where a
swallowed error becomes a wrong measurement or a wedged run. Upstream mirror code is NOT scanned:
`40cakes repo/` is pristine by directive and we do not lint someone else's project.

‼ AND IT IS A **REPRO**, not a linter, on purpose: it lives with the 87 other `repro_*.py`, runs in
the same gate, and exits non-zero.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_no_silent_except.py
      PYTHONUTF8=1 py -3.12 repro_no_silent_except.py --list   # every offender with file:line
"""

from __future__ import annotations

import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / "sandbox-pokebot"

SCAN = [
    BUILD / "modules" / "story",
    BUILD / "modules" / "battle_strategies",
    BUILD / "modules" / "battle_action_selection.py",
]

REPORTERS = ("log", "print", "debug_logger", "console", "logger", "warn", "_say", "_ch14_say")
SHOW = "--list" in sys.argv


def handler_is_loud(node: ast.ExceptHandler, src_lines: list[str]) -> tuple[bool, str]:
    """Does this handler re-raise, report, or carry an explicit justification?"""
    # (1) re-raises anywhere in the block
    for n in ast.walk(node):
        if isinstance(n, ast.Raise):
            return True, "re-raises"
    # (2) reports — any call whose name/attribute root looks like a reporter
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            name = ""
            if isinstance(f, ast.Name):
                name = f.id
            elif isinstance(f, ast.Attribute):
                name = f.attr
                root = f.value
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name):
                    name = f"{root.id}.{f.attr}"
            if any(r in name for r in REPORTERS):
                return True, f"reports via {name}()"
    # (3) an explicit justification comment ANYWHERE IN THE HANDLER, not just on the `except` line.
    # ‼ THE FIRST DRAFT ONLY CHECKED THE `except` LINE and reported 158 of 203 handlers as silent
    # — including `chapters.py:68`, which carries a perfectly good two-line justification *inside*
    # the block ("An unknown/unreadable milestone must never crash detection"). A check with that
    # many false positives gets switched off, and a switched-off check is an advisory rule with
    # extra steps — which is the very thing this file exists to replace.
    start = node.lineno - 1
    end = getattr(node, "end_lineno", node.lineno) or node.lineno
    for raw in src_lines[start:end]:
        if "#" not in raw:
            continue
        prose = raw.split("#", 1)[1]
        for token in ("noqa:", "BLE001", "noqa"):
            prose = prose.replace(token, "")
        # require real prose, not a bare suppression code
        if len(prose.strip()) >= 12:
            return True, "justified by comment"
    return False, "SILENT"


offenders: list[str] = []
scanned = 0
handlers = 0

files: list[pathlib.Path] = []
for target in SCAN:
    if target.is_file():
        files.append(target)
    elif target.is_dir():
        files += sorted(target.rglob("*.py"))

print("=" * 92)
print("NO SILENT EXCEPT — a guard that cannot tell \"no\" from \"I broke\" is worse than no guard")
print("=" * 92)

if not files:
    raise SystemExit(f"‼ nothing to scan under {BUILD} — refusing to report success")

for f in files:
    try:
        src = f.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except Exception as error:  # noqa: BLE001 — an unparseable file is reported, never skipped silently
        offenders.append(f"{f.relative_to(REPO)}: COULD NOT PARSE ({type(error).__name__})")
        continue
    scanned += 1
    lines = src.split("\n")
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            handlers += 1
            loud, why = handler_is_loud(node, lines)
            if not loud:
                offenders.append(f"{f.relative_to(REPO)}:{node.lineno}")

print(f"\n  files scanned      : {scanned}")
print(f"  except handlers    : {handlers}")
print(f"  SILENT handlers    : {len(offenders)}")

if offenders and SHOW:
    print("\n  offenders:")
    for o in offenders:
        print(f"    {o}")

# ‼‼ THIS IS A RATCHET, NOT A CLEAN-SLATE GATE — and that choice is the whole reason it works.
#
# The honest measurement is that **140 of 203** handlers in this code are silent (69%). Shipping
# that as a pass/fail gate would leave the suite RED from the first run until someone fixed 140
# handlers — and a permanently-red check gets switched off. A switched-off check is an advisory
# rule with extra steps, which is exactly what the 2026-08-11 review found does NOT work.
#
# So the contract is **"no new debt"**: the count may never RISE. Lowering `BASELINE` is a
# deliberate, reviewable one-line diff that records real cleanup. That makes this family strictly
# non-worsening TODAY, rather than theoretically fixed some day.
BASELINE = 140   # measured 2026-08-11. LOWER when handlers are cleaned up; never raise.

by_file: dict[str, int] = {}
for o in offenders:
    by_file[o.split(":")[0]] = by_file.get(o.split(":")[0], 0) + 1

print("\n  worst files (cleanup targets):")
for _name, _n in sorted(by_file.items(), key=lambda kv: -kv[1])[:5]:
    print(f"    {_n:>4}  {_name}")

print("\n" + "=" * 92)
if len(offenders) > BASELINE:
    print(f"FAILED — silent handlers went UP: {len(offenders)} > baseline {BASELINE}.")
    print("  A NEW silent `except` was added. Each must do ONE of: re-raise, report")
    print("  (log/print/debug_logger), or carry an explicit `# noqa: BLE001 — <why>` justification.")
    print("  Re-run with --list to find it.")
    sys.exit(1)
if len(offenders) < BASELINE:
    print(f"IMPROVED — {len(offenders)} silent handler(s), below the baseline of {BASELINE}.")
    print(f"  ‼ LOWER `BASELINE` to {len(offenders)} in this file to lock the gain in.")
    sys.exit(0)
print(f"PASS — {len(offenders)} silent handler(s), exactly at the baseline. No new debt.")
print("  ‼ This is a RATCHET, not a clean bill of health: 69% of handlers here are still silent.")
