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
  F1-F8  THE **HEAL-WALK** FAILURE MUST ALSO ABANDON (added 2026-09-12). `heal_in_pokemon_center`
         LAUNDERS every walk error into a fresh exception after 8 ride-outs, so it can NEVER raise
         `UnreachableDestinationError` — which is why the D-handler could not see it and the run
         died instead (MEASURED: 15 ON vs 3 OFF). `HealWalkFailedError` is caught, the latch is
         re-checked first, the lead is restored, and it RETURNS. ⛔ F3/F8 forbid the trap: it must
         NOT be a subclass of `UnreachableDestinationError` and must NOT call
         `_note_training_unreachable` — that handler blacklists the TRAINING GROUND, so a Poké
         Center failure would strike an innocent grass tile out for the rest of the run.
  F9-F10 THE RETRY RIDES OUT **ONLY GENUINE SCRIPTED EVENTS**. Measured 2026-09-12 from the A/B
         debug logs: 63 real scripted interruptions (ALL cleared on attempt 1) vs **128
         deterministic reachability refusals** retried 8x each and then reported under a headline
         naming a cutscene that never existed. F9 gates the TEXT COUPLING to `walking.py`'s message
         — if it drifts, every scripted event would classify as “blocked” and none would ever be
         ridden out again, which is strictly worse than the bug being fixed.
  H1     ⛔⛔ THE LEAD ROTATION IS GUARDED FOR SLOT 0 (added 2026-09-12 — **this gate was FULLY
         GREEN while the bug was live**, which is its own attack-(f) answered against itself).
         `_rotate_lead_safely` drives the party menu SWITCH option = a **SWAP**, and the driver does
         `for _ in range(slot - 1)` — slot 0 gives `range(-1)`, ZERO Downs, so it presses Right then
         A and confirms a swap against whatever the cursor is on. Slot 0 IS reachable:
         `decide_maintenance` breaks ties toward the LOWEST index. Five other call sites in the tree
         already guarded this (`counter_hunt.py:767`, `early_game.py:1703/1861/2080`,
         `victory_road.py:2061`); the errand did not copy it.
  G1-G2  THE SHIPPED DEFAULT AND ITS REGISTRY ROW AGREE. ⛔ NOT “assert it is ON” — the user may rule
         either way and the switch is also the A/B arm. What must never happen is the CODE and the
         DOC disagreeing about what ships.

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
       POKEBOT_MAINTREACH_FAULT=healbare  — revert the heal raise to a bare  -> F7 red
                                            `BotModeError` (the pre-fix shape)
         ⛔ THIS ARM WAS BROKEN WHEN FIRST WRITTEN AND THE GATE SAID SO. It used `replace(...,1)`,
         and once a SECOND `HealWalkFailedError` raise site existed it reverted one and left the
         other — F7 (“is the good type raised anywhere?”) still passed, and the gate printed
         “⛔⛔ A FAULT ARM WAS ACTIVE AND NOTHING FAILED”. Fixed twice over: the arm replaces ALL
         occurrences, and F7 now asserts the NEGATIVE too (no bare `BotModeError` survives).
         ⭐ **Presence of the good thing is not absence of the bad thing.**
       POKEBOT_MAINTREACH_FAULT=markerdrift — reword walking.py's message   -> F9 red
       POKEBOT_MAINTREACH_FAULT=regdrift  — registry row disagrees with the -> G2 red
                                            code's shipped default
       POKEBOT_MAINTREACH_FAULT=norotguard — `if slot != 0:` -> `if True:`   -> H1 red
                                            (the pre-fix shape: rotate unconditionally)
         ⚠ A REAL SOURCE MUTATION, not a flipped verdict — the first version of this arm just set
         the verdict variable False, which proves the ASSERTION can fail but not that the CHECK
         detects a real change. Corrupting the source is the stronger arm here.
"""
from __future__ import annotations

import ast
import io
import os
import re
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
elif FAULT == "norotguard":
    # ⛔ A REAL SOURCE MUTATION, not a flipped verdict. `if True:` keeps the block structure (so the
    # AST still parses and the call is still inside an `If`) while destroying the thing H1 tests —
    # which is exactly the pre-fix shape: the rotation runs unconditionally, including for slot 0.
    _src = _src.replace("            if slot != 0:", "            if True:", 1)
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

# ---------------------------------------------------------------------------------------------
# F — the HEAL-WALK failure must ALSO abandon (2026-09-12), and must NOT poison the grass memory
# ---------------------------------------------------------------------------------------------
_hw = _by.get("HealWalkFailedError")
CASES.append(("F1 — a NARROW `except HealWalkFailedError` handler exists in the errand",
              _hw is not None, True))
CASES.append(("F2 — its FIRST statement re-checks the abort latch (the 8-ride-out raise is "
              "OUTSIDE any try, so the error carries no abort identity)",
              bool(_hw) and isinstance(_hw.body[0], ast.Expr)
              and "reraise_if_aborting" in _calls(_hw.body[0]), True))
CASES.append(("F3 — ⛔ it does NOT call `_note_training_unreachable` (the grass was fine; the POKÉ "
              "CENTER broke — blaming the ground is a false diagnosis with a run-long cost)",
              bool(_hw) and "_note_training_unreachable" not in _calls(_hw), True))
CASES.append(("F4 — it RETURNS (abandons) and never re-raises",
              bool(_hw)
              and any(isinstance(m, ast.Return) for m in ast.walk(_hw))
              and not any(isinstance(m, ast.Raise) for m in ast.walk(_hw)), True))
CASES.append(("F5 — it restores the strong lead before returning",
              bool(_hw) and "_lead_strongest_battler" in _calls(_hw), True))
CASES.append(("F6 — `HealWalkFailedError` precedes `except BaseException` (first match wins)",
              _names.index("HealWalkFailedError") < _names.index("BaseException")
              if "HealWalkFailedError" in _names else False, True))

# F7/F8 — the raise site and the hierarchy, read from the helper's own source.
_hla_path = SANDBOX / "modules" / "modes" / "util" / "higher_level_actions.py"
_hla = io.open(_hla_path, encoding="utf-8").read()
if FAULT == "healbare":
    # ⛔ REPLACE **ALL**, NOT THE FIRST. The first version of this arm passed `1` and the gate stayed
    # GREEN under it — because `heal_in_pokemon_center` now raises `HealWalkFailedError` from TWO
    # sites (the 8-ride-out give-up AND the not-a-scripted-event fast fail), so reverting one left
    # the other and F7's "is it raised anywhere?" test still answered yes.
    # ‼ This is the documented arm-misses-its-target shape (`probe_late_boss_configs.py`, 2026-09-10)
    # and it was caught only because the arm was RUN and its verdict READ — the gate reported
    # "A FAULT ARM WAS ACTIVE AND NOTHING FAILED", which is the line that exists for exactly this.
    _hla = _hla.replace("raise HealWalkFailedError(", "raise BotModeError(")
_hla_tree = ast.parse(_hla)
_heal_fn = next((n for n in ast.walk(_hla_tree)
                 if isinstance(n, ast.FunctionDef) and n.name == "heal_in_pokemon_center"), None)
_raised = {getattr(m.exc.func, "id", None)
           for m in ast.walk(_heal_fn) if isinstance(m, ast.Raise) and isinstance(m.exc, ast.Call)}
CASES.append(("F7 — EVERY raise in `heal_in_pokemon_center` is `HealWalkFailedError`, and none is a "
              "bare `BotModeError` (a bare one is invisible to the errand and kills the run)",
              # ⛔ Asserted as "no bare BotModeError survives", NOT as "HealWalkFailedError appears
              # somewhere". The weaker form passed under the `healbare` arm while one raise site had
              # been reverted — presence of the good type says nothing about absence of the bad one.
              "HealWalkFailedError" in _raised and "BotModeError" not in _raised, True))
_cls = next((n for n in ast.walk(_hla_tree)
             if isinstance(n, ast.ClassDef) and n.name == "HealWalkFailedError"), None)
_bases = {b.id for b in (_cls.bases if _cls else []) if isinstance(b, ast.Name)}
CASES.append(("F8 — ⛔ it subclasses `BotModeError` and NOT `UnreachableDestinationError` — a "
              "subclass of that type would hit the handler that blacklists the training ground",
              _bases, {"BotModeError"}))

# F9/F10 — the retry must ride out ONLY genuine scripted events (measured 2026-09-12: 63 scripted
# interruptions, ALL cleared on attempt 1, vs 128 deterministic reachability refusals retried 8x
# each and then reported under a FALSE "a scripted event kept interrupting" headline).
_walking = io.open(SANDBOX / "modules" / "modes" / "util" / "walking.py", encoding="utf-8").read()
_marker = "unexpectedly triggered a scripted event"
if FAULT == "markerdrift":
    _walking = _walking.replace(_marker, "ran into an unexpected cutscene", 1)
CASES.append(("F9 — the retry's marker text still matches walking.py's raise (a TEXT coupling that "
              "drifts would classify every scripted event as 'blocked' and never ride one out)",
              _marker in _walking and _marker in _hla, True))

_heal_handlers = [h for h in ast.walk(_heal_fn) if isinstance(h, ast.ExceptHandler)
                  if isinstance(h.type, ast.Name) and h.type.id == "BotModeError"]
_retry_h = _heal_handlers[0] if _heal_handlers else None
_guards_marker = bool(_retry_h) and any(
    isinstance(m, ast.If) and "_SCRIPTED_EVENT_MARKER" in ast.dump(m.test)
    and any(isinstance(r, ast.Raise) for r in ast.walk(m))
    for m in ast.walk(_retry_h))
CASES.append(("F10 — a NON-scripted failure raises immediately instead of being ridden out 8× "
              "(riding out a scene cannot change map geometry)",
              _guards_marker, True))

# ---------------------------------------------------------------------------------------------
# G — the SHIPPED DEFAULT and its registry entry must agree (pair discipline, in a gate)
# ---------------------------------------------------------------------------------------------
# ⛔ NOT "assert the default is ON". The user can rule either way and the switch must keep working
# in BOTH directions (it is also the A/B arm). What must never happen is the CODE and the REGISTRY
# disagreeing — that is how a reader learns the wrong shipped behaviour from the doc a reader reads.
_default = re.search(r'environ\.get\(\s*"POKEBOT_MAINTAIN"\s*,\s*"([^"]*)"', _src)
_reg = io.open(ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md",
               encoding="utf-8").read()
_reg_row = next((l for l in _reg.split("\n") if l.startswith("| `POKEBOT_MAINTAIN` |")), "")
if FAULT == "regdrift":
    _reg_row = _reg_row.replace("`1` (ON", "`0` (OFF")
_reg_says_on = "`1` (ON" in _reg_row
CASES.append(("G1 — the code's shipped default for POKEBOT_MAINTAIN is readable",
              bool(_default), True))
CASES.append(("G2 — code default and 29-DISABLED-FEATURES-REGISTRY agree on what ships "
              "(a doc that misstates the shipped default teaches every future reader wrongly)",
              bool(_default) and ((_default.group(1) == "1") == _reg_says_on), True))

# ---------------------------------------------------------------------------------------------
# H — the lead rotation must be GUARDED for slot 0 (added 2026-09-12 after an adversarial review
# found this gate FULLY GREEN while the bug was live — that is attack (f) answered against itself)
# ---------------------------------------------------------------------------------------------
# ⛔ `_rotate_lead_safely` drives the party menu's SWITCH option, which is a SWAP. Its arithmetic is
# `for _ in range(slot - 1)`, so slot 0 gives `range(-1)` — ZERO Downs — and it presses Right then A,
# confirming a swap against whatever the cursor is on. Slot 0 IS reachable: `decide_maintenance`
# breaks ties toward the lowest index. Five other call sites in the tree already guard this.
_rot = next((m for m in ast.walk(_fn)
             if isinstance(m, ast.Call) and getattr(m.func, "id", None) == "_rotate_lead_safely"),
            None)
_guarded_rot = False
if _rot is not None:
    for m in ast.walk(_fn):
        if isinstance(m, ast.If) and any(c is _rot for c in ast.walk(m)):
            t = ast.dump(m.test)
            if "NotEq" in t and "slot" in t and "0" in t:
                _guarded_rot = True
                break
# (the `norotguard` arm mutates the SOURCE above, not this verdict — see the FAULT block)
CASES.append(("H1 — the lead rotation is guarded by `if slot != 0` (rotating TO slot 0 is a "
              "destructive SWAP, not a no-op, and slot 0 wins ties in decide_maintenance)",
              _guarded_rot, True))

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
