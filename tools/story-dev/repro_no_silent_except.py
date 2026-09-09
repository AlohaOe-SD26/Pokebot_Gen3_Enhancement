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

import argparse
import ast
import pathlib
import re
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
# ⚠ THE BASELINES BELOW WERE MEASURED AGAINST **sandbox**. `--build custom` will report
# different counts and may go red — that is the point of looking, not a broken gate.
_ap = argparse.ArgumentParser(add_help=True)
_ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"],
                 help="which fork to test (default sandbox; use custom to verify a promotion)")
_ARGS, _ = _ap.parse_known_args()

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / f"{_ARGS.build}-pokebot"

SCAN = [
    BUILD / "modules" / "story",
    BUILD / "modules" / "battle_strategies",
    BUILD / "modules" / "battle_action_selection.py",
    # ‼ ADDED 2026-08-14 — THE HEAL / PC PATH. `higher_level_actions.heal_in_pokemon_center`
    # piggybacks three PC actions (rotation deposit, KI-63 slot-freeing deposit, hunted-counter
    # withdraw), and **all three swallowed every exception silently**. The middle of that path is
    # exactly where the user-observed Slugma/Winona derail became unobservable: the withdraw
    # skipped on an empty input set and said nothing, so "nothing to do" and "it threw" were the
    # same silence. This directory was out of scope, so no gate could ever have said so.
    # Cost of admission, measured before adding: 17 handlers here, 9 silent — 3 of which were
    # those piggybacks and are now loud. The ratchet below absorbs the remaining 6 as recorded
    # debt and forbids a seventh.
    BUILD / "modules" / "modes" / "util",
]

REPORTERS = ("log", "print", "debug_logger", "console", "logger", "warn", "_say", "_ch14_say",
             # `_piggyback_report` (higher_level_actions.py) announces a PC-action outcome on the
             # heal path to the console and the run log. Listed so those handlers count as LOUD on
             # their merits, not merely excused by their `# noqa` prose.
             "_piggyback_report")
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
        if len(prose.strip()) >= 12 and not _DISMISSIVE_RE.search(prose):
            return True, "justified by comment"
    return False, "SILENT"


#: ‼ A DENYLIST, NOT AN ALLOWLIST — and that choice is MEASURED, not stylistic.
#: `#24-p4residuals` (d): the comment escape accepted ANY prose of 12+ characters, so
#: `# whatever man just move on` laundered a genuinely silent handler.
#: ⛔ THE OBVIOUS FIX — require a keyword like `expected`/`deliberate`/`report` — WAS REFUTED BY
#: MEASUREMENT before it shipped. All 60 handlers currently justified by comment were read: **0 are
#: filler, 60 are genuine**, because this codebase justifies in DOMAIN PROSE ("an unreadable map
#: must never end the fight"), not in keywords. An allowlist newly failed 43 of them — every one a
#: false positive — including `early_game.py`'s KI-81 abort guard, which literally re-raises, and
#: seven sites whose `reraise_if_aborting(error)` is a CONDITIONAL re-raise the AST cannot see. It
#: also broke the ratchet on all four roots (148 -> 191). A permanently-red check gets switched off,
#: which is the exact failure this file's own header was written to avoid.
#: ⇒ Invert it: keep the length test and reject only comments that are DISMISSIVE. Measured effect:
#: **0 of the 60 newly fail**, the ratchet is unchanged, and the motivating hole is closed.
_DISMISSIVE_RE = re.compile(
    r"\b(todo|fixme|xxx|hack|whatever|idk|shrug)\b"
    r"|\bwho\s+cares\b|\bno\s+idea\b|\bmove\s+along\b"
    r"|\bdon'?t\s+care\b|\bjust\s+move\s+on\b|\?\?\?",
    re.I,
)


if "--self-test" in sys.argv:
    # ‼ PROVE THE COMMENT ESCAPE BOTH REJECTS AND ACCEPTS. Added 2026-08-23 with the denylist,
    # because a gate never seen red is an assumption — and this one nearly shipped as a no-op: an
    # earlier draft's `\b` word boundaries were eaten by shell escaping and became literal backspace
    # bytes, so the pattern matched only `???`. It LOOKED correct in the diff. Only running it said
    # otherwise. ⇒ every predicate ships with the two lists below.
    _MUST_REJECT = ["# whatever man just move on", "# TODO fix this later", "# hack: ignore this",
                    "# ???", "# idk why this fails", "# don't care about this one",
                    "# fixme later", "# move along", "# XXX", "# who cares"]
    _MUST_KEEP = ["# an unreadable map must never end the fight",
                  "# Fail CLOSED: an unreadable table must never widen where the bot may walk",
                  "# telemetry must never break the teach",
                  "# a probe reports, it does not crash",
                  "# An unknown/unreadable milestone must never crash detection",
                  "# a scripted event (the tutorial) interrupted the walk — expected",
                  # ‼ NEAR-MISSES: real words that CONTAIN a denylisted token. These are why the
                  # pattern is word-bounded; without `\b` they would be rejected as dismissive.
                  "# the hackathon build is unaffected",
                  "# shrugged off by the caller downstream"]
    _bad = 0
    print("SELF-TEST — the comment justification escape, both directions")
    for _s in _MUST_REJECT:
        if not _DISMISSIVE_RE.search(_s):
            print(f"  ‼ FAIL accepted a dismissive comment: {_s}")
            _bad += 1
    for _s in _MUST_KEEP:
        if _DISMISSIVE_RE.search(_s):
            print(f"  ‼ FAIL rejected a GENUINE justification: {_s}")
            _bad += 1
    # and the length floor must still reject a bare suppression code
    if _DISMISSIVE_RE.search("# noqa: BLE001"):
        print("  ‼ FAIL the denylist fired on a bare suppression code")
        _bad += 1
    print(f"  {len(_MUST_REJECT)} reject-cases, {len(_MUST_KEEP)} keep-cases, {_bad} failure(s)")
    sys.exit(1 if _bad else 0)


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
BASELINE = 138   # re-measured 2026-08-27 (was 148, 10 handlers of SLACK — the deep sanity check caught it).
                 # LOWER when handlers are cleaned up; never raise.
#: ⛔⛔ 149 -> 148 IS A CORRECTION OF A STALE RATCHET, **NOT** A GAIN FROM `#24-abortswallow`.
#: The first version of this comment claimed `counter_hunt.py`'s training handler "stopped being
#: silent when it grew a latch-keyed re-raise". ‼ THAT WAS FABRICATED, and an adversarial review
#: disproved it with the one thing that settles a causal claim — A CONTROL ARM. Reverting BOTH
#: edited story files and re-running yields **148 either way**; the handler in question already
#: had a `console.print` and was never in the silent list. The count had been 148 since some
#: earlier, undocumented cleanup, and the label simply lagged.
#: ⇒ The 8-site abort-guard fix is proven by `probe_abort_swallowing.py` (45 -> 37). It is NOT
#: proven by this gate, and the two must not be conflated.
#: ‼ A ratchet only ratchets if you turn it — an un-lowered baseline silently re-permits debt —
#: but turning it is not evidence that YOUR change earned the notch.

# ‼‼ THE BASELINE ROSE 140 → 149 ON 2026-08-14, AND THAT IS A SCOPE EXTENSION, NOT NEW DEBT.
# `modules/modes/util/` was added to SCAN (see the note there) and brought 9 PRE-EXISTING silent
# handlers with it. Not one line of new code was written silent.
#
# ⛔ A RAISED TOTAL IS EXACTLY HOW A RATCHET GETS DEFEATED: 9 units of headroom in the total would
# let someone add 9 silent handlers back in `modules/story/` and still see PASS. So the budget is
# enforced PER SCAN ROOT as well as in total, and the original roots keep their own old numbers.
# A widened scope may admit the debt it inherits and nothing else.
#
# ‼ EVERY NUMBER BELOW WAS MEASURED, NOT ESTIMATED. The first draft of this dict carried four
# plausible-looking invented figures (119/21/0/9) that summed to the right total and were wrong in
# every entry — caught only by measuring. A per-root budget nobody measured is worse than none,
# because it looks rigorous. Re-measure with `--roots` after any cleanup.
PER_ROOT_BASELINE = {
    "modules/story": 123,          # re-measured 2026-08-27 (was 133, slack)
    "modules/battle_strategies": 4,
    "modules/battle_action_selection.py": 3,
    "modules/modes/util": 8,          # inherited 2026-08-14; re-measured 2026-08-27 (was 9, slack)
}

by_file: dict[str, int] = {}
for o in offenders:
    by_file[o.split(":")[0]] = by_file.get(o.split(":")[0], 0) + 1

print("\n  worst files (cleanup targets):")
for _name, _n in sorted(by_file.items(), key=lambda kv: -kv[1])[:5]:
    print(f"    {_n:>4}  {_name}")

# ‼ PER-ROOT ENFORCEMENT — the half that stops a widened scope hiding a regression.
_root_counts: dict[str, int] = {label: 0 for label in PER_ROOT_BASELINE}
_unattributed: list[str] = []
for _o in offenders:
    _path = _o.split(":")[0].replace("\\", "/")
    _match = None
    # ‼ SEGMENT-ANCHORED, NOT SUBSTRING. A plain `"/modules/story" in path` also matches
    # `modules/story_milestones.py` — a real sibling file that would be silently attributed to the
    # `modules/story` budget the moment it entered scope. Found by an adversarial review while it
    # was still only latent. Compare whole path SEGMENTS so a prefix cannot masquerade as a root.
    _segments = _path.split("/")
    for _label in PER_ROOT_BASELINE:                      # longest label wins, so a file-scan root
        _want = _label.split("/")                         # cannot be shadowed by a dir root
        if any(_segments[i:i + len(_want)] == _want for i in range(len(_segments))):
            if _match is None or len(_label) > len(_match):
                _match = _label
    if _match is None:
        _unattributed.append(_o)
    else:
        _root_counts[_match] += 1

print("\n  per scan root (budget enforced separately — a widened scope may not fund old debt):")
for _label, _budget in PER_ROOT_BASELINE.items():
    _n = _root_counts[_label]
    _flag = "  <- OVER" if _n > _budget else ("  (improved)" if _n < _budget else "")
    print(f"    {_n:>4} / {_budget:<4} {_label}{_flag}")

print("\n" + "=" * 92)
# ‼ A check that cannot attribute must SAY so, never pass (standing rule, 2026-08-14). If an
# offender belongs to no known root, the per-root budget is not actually policing everything.
if _unattributed:
    print(f"FAILED — {len(_unattributed)} offender(s) belong to no known scan root, so the")
    print("  per-root budget is not policing them. Add the root to PER_ROOT_BASELINE.")
    for _o in _unattributed[:5]:
        print(f"    {_o}")
    sys.exit(1)
_over = {lbl: (_root_counts[lbl], b) for lbl, b in PER_ROOT_BASELINE.items() if _root_counts[lbl] > b}
if _over:
    print("FAILED — a scan root went OVER its own budget, even if the total did not:")
    for _label, (_n, _b) in _over.items():
        print(f"    {_label}: {_n} > {_b}")
    print("  ⛔ This is the case a total-only ratchet misses — new debt in one root funded by")
    print("     headroom another root brought in. Re-run with --list to find it.")
    sys.exit(1)
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
