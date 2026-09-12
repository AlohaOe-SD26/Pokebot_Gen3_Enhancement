#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`#24-maintain` — the maintenance errand must REFUSE grounds it cannot walk to, and ABANDON
rather than kill the run when it discovers one anyway.

⛔⛔ WHY THIS EXISTS — MEASURED, NOT FEARED. The 2026-09-12 two-arm A/B (32 lanes x 310 min each,
`x4-runs/20260911-175201` ARM-ON vs `x4-runs/20260911-230219` ARM-OFF) priced the omission:

      metric                         ARM-ON          ARM-OFF
      runs completed                 552             243
      MEDIAN run duration            5.35 min        35.18 min   (6.6x SHORTER)
      badges won PER RUN             0.72            2.25        (3.1x WORSE)
        (398 over 552 runs)          (547 over 243 runs) — n=945 badge events
      `Could not reach (9,2) ROUTE102`  319             0
      `... ROUTE117 / 103 / 101`     40 / 27 / 20    0 / 0 / 0

⇒ the feature was net-HARMFUL, and every one of those 406 deaths was the SAME shape: `_prepare_for_
fight` asked `best_training_grass(level)` for a ground, that picker chose on LEVEL FIT ALONE with no
idea where the player was STANDING, and the walk then raised `UnreachableDestinationError`, which
the errand re-raised into `_play`'s derail recovery and took the whole run down with it.

⭐ THE DIAGNOSIS THAT MATTERED, and it was wrong twice before it was right:
  * First reading blamed `Cannot reach PETALBURG_CITY ... from ROUTE104` (1,745 hits). That line is
    **derail #2** — a CONSEQUENCE of the auto-restart after derail #1. Counting it measured the
    symptom. ⇒ **count PRIMARY derails (`derail #1`), never the loudest line.**
  * Second reading blamed ROUTE111 `(25,55)`, the known Go-Goggles-gated tile. But ROUTE111 appears
    in BOTH arms (145 vs 79) ⇒ it is pre-existing and NOT what the feature broke. The ROUTE102/117/
    103/101 family is ARM-ON-only. ⇒ **a cause present in the control is not the cause under test.**
  * The real mechanism: the bot stood on **ROUTE104 NORTH**, the far side of Petalburg Woods, and
    was sent to `ROUTE102 (9,2)` on the SOUTH side. Route 104 is ONE map split in two by the woods,
    so `region_reach.is_map_reachable` — which is MAP-granular — correctly answers "yes" and cannot
    see the split. ⇒ the story-stage predicate alone could never have caught this; the per-run
    `_training_blocked` MEMORY is what closes it, and maintenance simply never wrote to it.

WHAT IS GATED HERE
  A1-A4  ADDITIVE GUARANTEE — `allow=None` filters NOTHING, so `decide_maintenance`'s injected
         `ground_for` and gate #55's expectations are untouched by this fix. ⛔ Asserted as
         "no-allow == allow-that-accepts-everything", NOT against a hardcoded table, because a
         table recomputed from the code under test proves only that the code equals itself.
  B1-B2  THE FILTER BITES — rejecting the ground the picker would have chosen changes the answer.
  C1     TOTAL REFUSAL -> `None`, so `decide_maintenance` returns its honest "no ground serves that
         level" SKIP instead of unpacking `None` into a `TypeError`.
  D1-D6  THE HANDLER SHAPE in `_maintain_lagging_battler` (static, because exercising it live needs
         a ROM and ~100k frames): the narrow `except UnreachableDestinationError` exists, re-checks
         the abort latch FIRST (gate #27 / KI-67 — `StoryAbort` IS a `BotModeError`), records the
         ground via `_note_training_unreachable` so the run SELF-HEALS, and RETURNS instead of
         re-raising — while `GeneratorExit` still passes straight through and the broad
         `except BaseException` still re-raises unconditionally.
  E1     THE DECISION AND THE PICK SHARE ONE PREDICATE — `ground_for=` must not be the raw
         `best_training_grass`, or the errand is approved against a band it will then refuse.

Run:   cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_maintain_unreachable.py
Fault arms — each reds EXACTLY its own case(s); ⛔ a gate nobody has fault-tested is decoration:
       POKEBOT_MAINTREACH_FAULT=nofilter  — picker ignores `allow`            -> B2,C1 red
         ⭐ I PREDICTED THIS ARM WOULD ALSO RED **B1** AND IT DOES NOT — recorded because the
         reason matters: B1 asserts what the UNFILTERED picker chooses (ROUTE102), so it is
         deliberately blind to the filter and MUST survive this arm. A case that cannot fail for
         the arm's reason is not a weak case here, it is the control: B1 is what makes B2's
         "the answer changed" meaningful rather than vacuous.
       POKEBOT_MAINTREACH_FAULT=nolatch   — drop `reraise_if_aborting` first  -> D2 red
       POKEBOT_MAINTREACH_FAULT=reraise   — handler re-raises instead of      -> D3 red
                                            returning (the pre-fix behaviour)
       POKEBOT_MAINTREACH_FAULT=nomemory  — drop `_note_training_unreachable` -> D6 red
"""
from __future__ import annotations

import ast
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

FAULT = os.environ.get("POKEBOT_MAINTREACH_FAULT", "").strip().lower()

STORY_MODE = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"

from modules.story.training_areas import AREA_PREREQ, best_training_grass  # noqa: E402


def _pick(level, allow=None):
    """The picker under test — or a deliberately broken one under the `nofilter` arm."""
    if FAULT == "nofilter":
        return best_training_grass(level)  # ignores `allow` — the pre-fix behaviour
    return best_training_grass(level, allow=allow)


# ---------------------------------------------------------------------------------------------
# A / B / C — the pure picker
# ---------------------------------------------------------------------------------------------
CASES: list[tuple[str, object, object]] = []

ACCEPT_ALL = lambda m, t, p: True          # noqa: E731
REJECT_ALL = lambda m, t, p: False         # noqa: E731

for _lv in (4, 8, 13, 20, 27):
    CASES.append((
        f"A — L{_lv}: allow=None filters NOTHING (identical to accept-everything)",
        best_training_grass(_lv),
        best_training_grass(_lv, allow=ACCEPT_ALL),
    ))

_L4 = best_training_grass(4)
_CHOSEN4 = _L4[0] if _L4 else None
CASES.append((
    "B1 — the unfiltered L4 pick is ROUTE102 (the ground 319 runs died walking to)",
    _CHOSEN4.name if _CHOSEN4 else None,
    "ROUTE102",
))
CASES.append((
    "B2 — rejecting that ground changes the answer (the filter actually bites)",
    _pick(4, allow=lambda m, t, p: m is not _CHOSEN4) != _L4,
    True,
))
CASES.append((
    "C1 — rejecting EVERY ground returns None (so decide_maintenance SKIPs, never TypeErrors)",
    _pick(4, allow=REJECT_ALL),
    None,
))
CASES.append((
    "C2 — the predicate is handed the AREA_PREREQ for the map it is judging",
    _pick(27, allow=lambda m, t, p: p == AREA_PREREQ.get(m)) == best_training_grass(27),
    True,
))


# ---------------------------------------------------------------------------------------------
# D — the handler shape, read out of the real source
# ---------------------------------------------------------------------------------------------
_src = io.open(STORY_MODE, encoding="utf-8").read()

# Fault arms mutate the SOURCE under test, so each proves its own case discriminates.
if FAULT == "nolatch":
    _src = _src.replace("            reraise_if_aborting(error)\n", "", 1)
elif FAULT == "nomemory":
    _src = _src.replace("            self._note_training_unreachable(grass_map, grass_tile)\n", "", 1)
elif FAULT == "reraise":
    _src = _src.replace(
        '                f"skipping maintenance and carrying on.[/]"\n            )\n            return\n',
        '                f"skipping maintenance and carrying on.[/]"\n            )\n            raise\n',
        1,
    )

_tree = ast.parse(_src)
_fn = next(n for n in ast.walk(_tree)
           if isinstance(n, ast.FunctionDef) and n.name == "_maintain_lagging_battler")

# The try/except that wraps the errand: the one carrying a GeneratorExit handler.
_try = next(n for n in ast.walk(_fn)
            if isinstance(n, ast.Try) and any(
                isinstance(h.type, ast.Name) and h.type.id == "GeneratorExit" for h in n.handlers))
_names = [h.type.id if isinstance(h.type, ast.Name) else None for h in _try.handlers]
_by = {n: h for n, h in zip(_names, _try.handlers)}
_ude = _by.get("UnreachableDestinationError")


def _calls(node) -> set:
    out = set()
    for m in ast.walk(node):
        if isinstance(m, ast.Call):
            f = m.func
            out.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", None))
    return out


CASES.append(("D1 — a NARROW `except UnreachableDestinationError` handler exists",
              _ude is not None, True))
CASES.append(("D2 — its FIRST statement re-checks the abort latch (gate #27 / KI-67)",
              bool(_ude) and isinstance(_ude.body[0], ast.Expr)
              and "reraise_if_aborting" in _calls(_ude.body[0]), True))
CASES.append(("D3 — it RETURNS (abandons the errand) and never re-raises",
              bool(_ude)
              and any(isinstance(m, ast.Return) for m in ast.walk(_ude))
              and not any(isinstance(m, ast.Raise) for m in ast.walk(_ude)), True))
CASES.append(("D4 — `except GeneratorExit` is FIRST and only re-raises",
              _names[0] == "GeneratorExit"
              and all(isinstance(s, ast.Raise) for s in _by["GeneratorExit"].body), True))
CASES.append(("D5 — the broad `except BaseException` STILL re-raises unconditionally",
              any(isinstance(m, ast.Raise) for m in ast.walk(_by["BaseException"])), True))
CASES.append(("D6 — the handler records the ground so the run SELF-HEALS",
              bool(_ude) and "_note_training_unreachable" in _calls(_ude), True))

# E — one predicate for the decision and the pick.
_decide = next((m for m in ast.walk(_fn)
                if isinstance(m, ast.Call)
                and getattr(m.func, "id", None) == "decide_maintenance"), None)
_ground_kw = next((k.value for k in (_decide.keywords if _decide else []) if k.arg == "ground_for"),
                  None)
CASES.append(("E1 — `ground_for=` is the FILTERED ground, not raw best_training_grass",
              getattr(_ground_kw, "id", None), "_maint_ground"))


def main() -> int:
    print("=" * 96)
    print("  #24-maintain — unreachable-ground refusal + fail-soft abandonment")
    if FAULT:
        print(f"  ⛔ FAULT ARM ACTIVE: {FAULT}")
    print("=" * 96)
    bad = 0
    for label, got, want in CASES:
        ok = got == want
        bad += 0 if ok else 1
        print(f"  {'PASS' if ok else '❌ FAIL'}  {label}")
        if not ok:
            print(f"            got {got!r}, expected {want!r}")
    print("=" * 96)
    if bad:
        print(f"  ❌ {bad} of {len(CASES)} case(s) FAILED")
        print("=" * 96)
        return 1
    print(f"  ✅ ALL {len(CASES)} CASES PASS")
    if FAULT:
        print("  ⛔⛔ A FAULT ARM WAS ACTIVE AND NOTHING FAILED — this gate proves nothing.")
        print("=" * 96)
        return 1
    print("=" * 96)
    return 0


if __name__ == "__main__":
    sys.exit(main())
