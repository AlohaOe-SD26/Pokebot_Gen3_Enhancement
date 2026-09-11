#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`#24-maintain` — every branch of `decide_maintenance`, and the PREDICTIONS filed before it existed.

⛔ WHY THIS EXISTS. The laggard is the measured #1 run-ender: `_prepare_for_fight` builds `to_train`
from ``party[i].level >= target - TRAIN_CATCHUP_GAP``, so a mon more than 6 levels below the boss
target is dropped from prep training ENTIRELY — and the target rises with every badge, so it can
never climb back in. 35% of badge moments carried a mon 15+ levels behind; §Ch23 then REFUSES to
train it because the estimated grind exceeds `MAX_TRAINING_FRAMES`, ending the run without spending
a frame. `decide_maintenance` stops the mon ever reaching that state.

⛔⛔ THE BOUNDARY THIS GATE DEFENDS, because a well-meaning maintainer WILL try to cross it.
`06-DECISIONS-LOG.md` 2026-09-10 REJECTED training a lagging mon to the BOSS's level: L40→L47 on the
only tabled ground costs 285,167 frames against a 250,000 ceiling, and a L33-40 ground cannot be won
at (measured: 69 battles, 0/43 HP, still L13). This item is the OTHER half of that slug and survives
only because it changes the two variables that arithmetic is sensitive to:
    target = `boss_target - TRAIN_CATCHUP_GAP`, NEVER the boss's level
    ground = keyed to the LAGGARD's level, NEVER the boss's
⇒ C7/C8 assert exactly that, so a future "why not just train it to the boss level?" edit must argue
with the measurement first.

PREDICTIONS GRADED HERE — `PROJECT KNOWLEDGE/ai-research-notes/2026-09-11-maintain-PREDICTIONS.md`,
filed BEFORE any code was written:
    P1 a staged laggard is maintained                     -> C3
    P2 ⛔ THE VACUITY CONJUNCT: the arms must DIFFER       -> C13 (a no-op could satisfy every other
                                                             case; C13 is the one it cannot)
    P3 the ground is the LAGGARD's, not the boss's        -> C8
    P4 a 30-behind mon is SKIPPED, not ground at          -> C5
    P5 an UNKNOWN cost fails safe                         -> C6
    P6 (lead restored) is a generator property, NOT testable here — graded by the driven run.
       ‼ Said out loud so nobody reads a green gate as covering it.

Run:   cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_maintenance_decision.py
Fault arms — MEASURED 2026-09-11, each reds EXACTLY its own case(s):
       POKEBOT_MAINTDEC_FAULT=gap       — decide on a gap vs the party MAX instead of the
                                          exclusion's own quantity  -> **C13** reds.
       POKEBOT_MAINTDEC_FAULT=cheap     — treat an UNKNOWN estimate as affordable -> **C6** reds.
       POKEBOT_MAINTDEC_FAULT=strongest — maintain the STRONGEST excluded mon -> **C1+C4** red.

⭐ THE `gap` ARM IS WORTH READING TWICE. I predicted it would red C1/C4 and it does NOT: with a
fixed party, "gap vs party max" and "target − 6" often pick the SAME mon, so every single-party case
stays green. Only **C13**, which holds the party fixed and VARIES THE BOSS TARGET, can see the
difference. ⇒ that is precisely what a vacuity conjunct is for, and it is the case a plausible-looking
wrong implementation would have survived. ‼ The prediction was wrong and the arm is right; the claim
here now states the MEASUREMENT, not my expectation of it.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

FAULT = os.environ.get("POKEBOT_MAINTDEC_FAULT", "")

# ⛔ Import the REAL predicate from the REAL module — never a copy. A gate over a transcribed
# duplicate proves the transcription, not the code (this project has paid for that twice).
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "_story_mode_for_probe", SANDBOX / "plugins" / "custom_modes" / "story_mode.py")
_mod = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_mod)
except Exception as error:  # noqa: BLE001
    print(f"  ⛔ could not import story_mode.py: {type(error).__name__}: {error}")
    raise SystemExit(2)
decide_maintenance = _mod.decide_maintenance

GAP = 6                 # TRAIN_CATCHUP_GAP
BUDGET = 150_000        # MAINTAIN_MAX_FRAMES


# --- stand-in world, deliberately tiny and explicit -------------------------------------------
def ground_for(level: int):
    """Mirrors the SHAPE of best_training_grass: a level -> (map, tile) or None."""
    if level < 2:
        return None
    if level <= 5:
        return ("ROUTE102", (10, 10))
    if level <= 11:
        return ("ROUTE116", (11, 7))
    if level <= 17:
        return ("ROUTE117", (20, 8))
    if level <= 22:
        return ("ROUTE111", (25, 55))
    if level <= 25:
        return ("ROUTE115", (6, 53))
    return ("ROUTE121", (44, 14))


WILD = {"ROUTE102": 5, "ROUTE116": 8, "ROUTE117": 14, "ROUTE111": 22, "ROUTE115": 26, "ROUTE121": 28}
HEAL = {k: f"PC_{k}" for k in WILD}


def make_estimate(cost):
    """cost may be an int, None (unknown), or a callable(slot, to, wild)."""
    if callable(cost):
        return cost
    return lambda slot, to, wild: cost


def call(levels, target, *, cost=10_000, grounds=ground_for, heal=HEAL.get, budget=BUDGET):
    if FAULT == "cheap":
        cost = 10_000 if cost is None else cost           # arm: UNKNOWN read as affordable
    kw = dict(
        battler_levels=levels,
        boss_target=target,
        catchup_gap=GAP,
        ground_for=grounds,
        wild_max_for=WILD.get,
        estimate_for=make_estimate(cost),
        heal_for=heal,
        budget=budget,
    )
    if FAULT == "gap":
        # arm: decide on a gap against the PARTY MAX rather than the exclusion's own quantity.
        # Mathematically different whenever the party max != the boss target, which is the norm.
        top = max(levels.values()) if levels else 0
        kw["boss_target"] = top
    slot, reason = decide_maintenance(**kw)
    if FAULT == "strongest" and slot is not None:
        excl = {s: l for s, l in levels.items() if l < kw["boss_target"] - GAP}
        if excl:
            slot = max(excl, key=lambda s: excl[s])
    return slot, reason


CASES: list[tuple[str, object, object]] = []


def case(label, got, want):
    CASES.append((label, got, want))


# C1 — the ordinary maintain: one mon below the floor, affordable
case("C1 a mon below the L(target-6) floor IS maintained",
     call({0: 28, 1: 27, 2: 21}, 34)[0], 2)

# C2 — nobody below the floor
case("C2 nobody below the floor -> no action",
     call({0: 30, 1: 29, 2: 28}, 34)[0], None)

# C3 — P1: a staged laggard 10 below is maintained
case("C3 [P1] a laggard 10 below the target is maintained",
     call({0: 34, 1: 33, 2: 24}, 34)[0], 2)

# C4 — the WEAKEST excluded mon, not just any
case("C4 the WEAKEST excluded mon is chosen",
     call({0: 34, 1: 20, 2: 26, 3: 15}, 34)[0], 3)

# C5 — P4: a 30-behind mon is refused on cost, not ground at
case("C5 [P4] a 30-behind mon is REFUSED on cost (not ground at)",
     call({0: 47, 1: 17}, 47, cost=400_000)[0], None)

# C6 — P5: UNKNOWN cost fails safe
case("C6 [P5] an UNKNOWN estimate fails SAFE (refuses)",
     call({0: 34, 1: 21}, 34, cost=None)[0], None)

# C7 — ⛔ the target is catchup, NEVER the boss level
_slot, _reason = call({0: 34, 1: 21}, 34)
case("C7 the stated target is L28 (= 34-6), NEVER the boss's L34",
     ("L21->L28" in _reason, "L34" in _reason.replace("boss", "")), (True, False))

# C8 — P3: the ground is keyed to the LAGGARD's level
_seen: list[int] = []
call({0: 34, 1: 21}, 34, grounds=lambda lvl: (_seen.append(lvl), ground_for(lvl))[1])
case("C8 [P3] ground_for is asked about the LAGGARD's level, not the boss's",
     (_seen[0] if _seen else None), 21)

# C9 — no ground for the level -> refuse
case("C9 no ground for that level -> refuses with a reason",
     call({0: 34, 1: 1}, 34, grounds=lambda lvl: None)[0], None)

# C10 — no heal centre -> refuse
case("C10 no heal centre mapped -> refuses",
     call({0: 34, 1: 21}, 34, heal=lambda m: None)[0], None)

# C11 — empty battler set (gate #48's shape: an empty set once certified a run READY)
case("C11 an EMPTY battler set -> no action, never a crash",
     call({}, 34)[0], None)

# C12 — exactly at the floor is NOT excluded (boundary: `>= catchup` admits it)
case("C12 a mon exactly AT the floor is not maintained (boundary)",
     call({0: 34, 1: 28}, 34)[0], None)

# C13 — ⛔⛔ THE VACUITY CONJUNCT (P2). A predicate that always returned None would pass C2/C5/C6/
# C9/C10/C11/C12; one that always returned slot 1 would pass C1/C3. This asserts the SAME party
# gives DIFFERENT answers at two boss targets — which only a predicate that actually reads its
# inputs can satisfy. ‼ Without this, a no-op could wear a green tick.
_low = call({0: 30, 1: 25}, 30)[0]      # floor 24 -> 25 is fine        -> None
_high = call({0: 30, 1: 25}, 34)[0]     # floor 28 -> 25 is below       -> 1
case("C13 [P2] ⛔ VACUITY: the same party decides DIFFERENTLY at two targets",
     (_low, _high), (None, 1))


def main() -> int:
    print("=" * 96)
    print("`#24-maintain` — decide_maintenance, all branches + the pre-registered predictions")
    print("=" * 96)
    if FAULT:
        print(f"  ⚠ FAULT ARM ACTIVE: POKEBOT_MAINTDEC_FAULT={FAULT}\n")
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
