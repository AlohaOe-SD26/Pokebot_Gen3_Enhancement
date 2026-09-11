#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compute `#24-maintain`'s A/B DISCRIMINATOR on a named fixture, BEFORE spending a drive on it.

⛔ WHY THIS EXISTS. This project's Tier 2 rule says an A/B item must COMPUTE THE DISCRIMINATOR on the
named fixture and SHOW THE ARMS DIFFER. It exists because a handed-off spec here once named a fixture
that made its own A/B **vacuous** — `team_max 39` against a threshold of `wild_max + 8 = 35`, so the
flag under test was identical in BOTH arms. That run would have printed "no difference" and read as a
**REFUTATION of a true finding**. A consistency check cannot see that: the document was perfectly
self-consistent and perfectly unusable.

⇒ Run this before driving. It answers one question: *for every boss target the band can roll, does
`decide_maintenance` ADMIT the mule, and by how much would its level move?*

‼ IT CALLS THE REAL PREDICATE from the real module — never a transcription. A tool that re-implements
the thing it is checking proves the transcription, not the code.

⭐ AND IT USES THE MULE'S OWN GROWTH CURVE. My first hand-computation used Zigzagoon (MediumFast) as
a stand-in; Marill is **Fast**, i.e. materially cheaper (7,165 vs 8,598 frames at catchup 14). The
direction was favourable and the substitution was still wrong — the same shape as publishing an
affordability table against GUESSED boss bands earlier the same day. Read the value, never recall it.

Usage:
    cd tools/story-dev
    PYTHONUTF8=1 py -3.12 probe_maintain_discriminator.py
    PYTHONUTF8=1 py -3.12 probe_maintain_discriminator.py --mule-level 13 --species Marill \
        --party 20,20,18,16 --band 20,24

Exit 0 when the A/B is non-vacuous for EVERY target in the band; 1 otherwise (so it can gate a drive).
⛔ It is NOT in `run_gates.py`: it describes a PLANNED experiment, not an invariant of the tree.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

from modules.story import training_areas as ta            # noqa: E402
from modules.pokemon import get_species_by_name           # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "_sm_disc", SANDBOX / "plugins" / "custom_modes" / "story_mode.py")
_sm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sm)

GAP = 6              # TRAIN_CATCHUP_GAP
BUDGET = _sm.StoryMode.MAINTAIN_MAX_FRAMES


def _wild_max(map_enum):
    return next((b[1] for m, _t, b in ta.TRAINING_GRASS if m == map_enum), None)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--party", default="20,20,18,16",
                    help="existing battler levels, comma separated (default: mauville_prewattson)")
    ap.add_argument("--mule-level", type=int, default=13, help="level --inject-hmmule stages")
    ap.add_argument("--species", default="Marill", help="mule species (its GROWTH CURVE is used)")
    ap.add_argument("--band", default="20,24", help="the boss config's band, lo,hi")
    args = ap.parse_args()

    existing = [int(x) for x in args.party.split(",") if x.strip()]
    lo, hi = (int(x) for x in args.band.split(","))
    mule_slot = len(existing)
    party = {i: lv for i, lv in enumerate(existing)}
    party[mule_slot] = args.mule_level

    curve = get_species_by_name(args.species).level_up_type

    def est(frm: int, to: int, wild: int) -> int:
        need = curve.get_experience_needed_for_level(to) - curve.get_experience_needed_for_level(frm)
        if need <= 0:
            return 0
        per = ta._CALIBRATED_AVG_WILD_BASE_EXP_YIELD * wild / 7
        return math.ceil(need / per) * ta.FRAMES_PER_WILD_BATTLE

    heal = {m: f"PC_{getattr(m, 'name', m)}" for m, _t, _b in ta.TRAINING_GRASS}

    print("=" * 100)
    print("`#24-maintain` A/B DISCRIMINATOR — computed on the fixture, before any drive")
    print("=" * 100)
    print(f"  party after injection : {party}   (mule = slot {mule_slot} @ L{args.mule_level})")
    print(f"  mule species/curve    : {args.species} / {curve}")
    print(f"  boss band             : ({lo},{hi})  → catchup {lo - GAP}..{hi - GAP}")
    print(f"  budget                : {BUDGET:,} frames\n")
    print(f"  {'target':>7}{'catchup':>9}  {'decide ->':<12}{'ground':<11}{'est frames':>12}  admitted?")
    print("  " + "-" * 84)

    admitted, refused, wrong_mon, levels = [], [], [], []
    for target in range(lo, hi + 1):
        slot, reason = _sm.decide_maintenance(
            battler_levels=dict(party),
            boss_target=target,
            catchup_gap=GAP,
            ground_for=ta.best_training_grass,
            wild_max_for=_wild_max,
            estimate_for=lambda s, to, wild, _p=party: est(_p[s], to, wild),
            heal_for=heal.get,
            budget=BUDGET,
        )
        catchup = target - GAP
        ground = ta.best_training_grass(args.mule_level)
        gname = getattr(ground[0], "name", "-") if ground else "NONE"
        frames = est(args.mule_level, catchup, _wild_max(ground[0])) if ground else None
        if slot is None:
            refused.append((target, reason))
            print(f"  {target:>7}{catchup:>9}  {'None':<12}{gname:<11}{'-':>12}  ⛔ NO — {reason[:32]}")
            continue
        if slot != mule_slot:
            wrong_mon.append((target, slot))
        admitted.append(target)
        levels.append(catchup)
        flag = "✅ YES" if slot == mule_slot else f"⚠ slot {slot}, NOT the mule"
        print(f"  {target:>7}{catchup:>9}  {'slot ' + str(slot):<12}{gname:<11}{frames:>12,}  {flag}")

    print()
    print("=" * 100)
    n = hi - lo + 1
    if len(admitted) == n and not wrong_mon:
        print("  ✅ NON-VACUOUS FOR EVERY TARGET THE BAND CAN ROLL.")
        print(f"     ARM-ON  ⇒ mule reaches L{min(levels)}..L{max(levels)} (target decides which)")
        print(f"     ARM-OFF ⇒ mule stays L{args.mule_level}, UNCHANGED")
        print("  ⛔ DISCRIMINATOR: the mule's level, READ BY PID. The arms cannot coincide.")
        print("  ‼ Still read the MAINTAIN log line before trusting a level delta — ARM-ON must say")
        print("     `start … L→L`, not `SKIPPED - …`. A computed admission is not an observed one.")
        print("=" * 100)
        return 0

    if wrong_mon:
        print(f"  ⛔⛔ WRONG MON on target(s) {[t for t, _s in wrong_mon]} — the grade would read a")
        print("     mon the run never intended to train. Fix the party or the mule level.")
    if refused:
        print(f"  ⛔ VACUOUS on target(s) {[t for t, _r in refused]}:")
        for t, r in refused:
            print(f"       target {t}: {r}")
        print("  ⇒ a roll landing there trains NOTHING, and the run would read as a REFUTATION of a")
        print("     true finding. PIN THE TARGET, or pick a different fixture/mule level.")
    print("=" * 100)
    return 1


if __name__ == "__main__":
    sys.exit(main())
