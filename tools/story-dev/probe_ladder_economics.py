# -*- coding: utf-8 -*-
"""⭐ IS USER RULING 12 (train all six on the Fly ladder) ACHIEVABLE? (`#24-swaptrigger2`)

USER RULING 12 (2026-09-23) keeps all six mōn and trains the two stragglers on the new per-trainee
Fly ladder. The ruling says what is WANTED. This probe prices it — because a ruling cannot make an
impossible outcome possible, and the honest place to discover that is here rather than 20 hours into
a grind.

⭐⭐ WHAT THE LADDER IS SUPPOSED TO BUY, STATED SO IT CAN BE CHECKED RATHER THAN ASSUMED.
`estimate_frames_to_level` is known wrong by a **measured ~3.30×** (`story_harness.py:15416-15420`),
and that figure is a PRODUCT of two independent corrections:
    ×2.00  the **0.501 participant divisor** — two mōn in the battle split the exp
    ×1.65  ~2,368 frames per **WIN** against the estimator's 1,433 per **BATTLE**
‼ THE LADDER'S WHOLE THESIS IS THAT IT REMOVES THE FIRST FACTOR: a trainee fighting wilds it
out-levels never triggers the swap, so it SOLOS, so nothing splits the exp. ⇒ under the ladder the
correction should be **×1.65, not ×3.30**. This probe computes both so the difference is a number.

⛔⛔ AND THE THING THAT COULD STILL BREAK IT — TRIGGER 2, WHICH `max_wild_max` DOES NOT TOUCH.
`SwapTrainBattleStrategy.decide_turn` fires on `(underleveled or cant_continue)`. The out-level cap
kills `underleveled`. It does NOT kill `cant_continue`, which is
**HP below `battle.hp_threshold` OR no usable move**. When it fires, `_capable_finisher` picks the
strongest healthy mōn that out-levels the foe — and at a level-matched ground the foe is LOW, so
almost any L75 qualifies. The exp then splits exactly as before.
  * THE HP HALF is bounded by `hp_threshold` (default **20 %**) and a trainee that out-levels its
    wilds should rarely fall that far. That is a READING, not a measurement — it needs a drive.
  * ⭐ THE PP HALF IS ARITHMETIC, AND THIS PROBE SETTLES IT. `not any(move_is_usable)` fires only
    when EVERY move is at 0 PP. Each mōn's PP budget is readable from the save, so the number of
    battles before it fires is computable — and therefore so is the HEAL CADENCE that prevents it.
    ⇒ the leg's heal frequency is not a comfort feature; it is what BOUNDS trigger 2.

⚠ WHAT THIS IS AND IS NOT. It is an ECONOMIC model built from MEASURED constants and the REAL party
read out of a save. It is not a drive. Every figure below inherits the ±of its constants, and the
frames/battle constant is itself an average over a corpus. ⇒ treat a 2× margin as noise and a 10×
margin as a finding.

READ-ONLY: loads one save state, reads the party, does arithmetic. Nothing is walked or written.
"""
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

_ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
_BUILD = ("custom" if "--build" in sys.argv
          and sys.argv[sys.argv.index("--build") + 1] == "custom" else "sandbox")
sys.path.insert(0, str(_ROOT / f"{_BUILD}-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile

_p = load_profile(_ROOT / "sandbox-pokebot" / "profiles" / "repro-fresh")
context.profile = _p
context.config.load(_p.path, strict=False)
set_rom(_p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_p, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0

from modules.pokemon_party import get_party
from modules.story.training_areas import FRAMES_PER_WILD_BATTLE, xp_per_battle

SAVES = _ROOT / "tools" / "story-dev" / "saves"
FIXTURE = "post_ch24_atdoor_L75.ss1"
FLOOR = 65                      # USER RULING: every party member between L65 and L75
FPS = 59.7275                   # GBA

#: The measured corrections. ‼ Kept as SEPARATE factors, never as the combined 3.30, because the
#: entire question here is whether the ladder removes ONE of them.
PARTICIPANT_DIVISOR = 2.00      # two mōn in the battle split the exp (0.501 measured)
FRAMES_PER_WIN = 1.65           # ~2,368 frames per WIN vs the estimator's 1,433 per BATTLE

#: The ladder, as measured under the out-level cap. (rung, ground name, top wild level)
LADDER = [("L15-20", "ROUTE117", 20), ("L21-24", "ROUTE111", 24), ("L25-26", "ROUTE115", 26),
          ("L27", "ROUTE118", 27), ("L28-38", "ROUTE121", 38), ("L39-75", "VICTORY_ROAD_1F", 75)]

#: ⚠ ASSUMED, AND FLAGGED AS SUCH: turns per wild battle for a trainee that out-levels its foe.
#: 3 is deliberately CONSERVATIVE-LOW (fewer turns ⇒ MORE battles per PP budget ⇒ a LONGER heal
#: cadence ⇒ a friendlier answer). If the true figure is higher, trigger 2's PP half fires SOONER
#: than reported here, so this assumption cannot flatter the conclusion in the dangerous direction.
TURNS_PER_BATTLE = 3

#: Frames for one heal round trip. ⚠ ASSUMED. The measured `ch24caveheal` drive is the nearest
#: real analogue; a town heal from a route is cheaper. Reported separately so the reader can
#: re-price it rather than having it buried in a total.
FRAMES_PER_HEAL_TRIP = 4_000

print("=" * 108)
print(f"IS RULING 12 ACHIEVABLE? — pricing the Fly ladder from the REAL party   [build={_BUILD}]")
print("=" * 108)

context.emulator.load_save_state((SAVES / FIXTURE).read_bytes())
for _ in range(40):
    context.emulator.run_single_frame()
print(f"  party read from: {FIXTURE}")
print()


def _rung_for(level: int):
    """The ladder rung a mōn of this level trains on — the out-level rule: top wild <= level + 1."""
    best = None
    for rung, name, hi in LADDER:
        if hi <= level + 1:
            if best is None or hi > best[2]:
                best = (rung, name, hi)
    return best


party = get_party()
rows = []
for i, mon in enumerate(party):
    if mon is None or mon.level >= FLOOR:
        continue
    curve = mon.species.level_up_type
    need = curve.get_experience_needed_for_level(FLOOR) - mon.total_exp
    pp_budget = sum(m.pp for m in mon.moves if m is not None and m.move is not None)

    print(f"─── slot{i}  {mon.species.name}  L{mon.level} → L{FLOOR}   ({curve.value} curve)")
    print(f"      exp needed          : {need:,}")
    print(f"      total PP in moveset : {pp_budget}")

    # ⛔ THE GRIND IS NOT ONE GROUND — the trainee climbs rungs as it levels, and exp/battle RISES
    # with the rung. Pricing the whole climb at the FIRST rung would be pessimistic by several
    # times; pricing it at the LAST would be optimistic by more. Walk the rungs.
    solo_frames = two_way_frames = 0
    battles_total = 0
    lvl = mon.level
    exp = mon.total_exp
    per_rung = []
    while lvl < FLOOR:
        rung = _rung_for(lvl)
        if rung is None:
            print(f"      ⛔ NO RUNG for L{lvl} under the out-level rule — the ladder has a hole here")
            break
        _label, ground, hi = rung
        # level at which the NEXT rung opens (its top wild <= lvl+1), else the floor
        nxt = FLOOR
        for _r, _g, h in LADDER:
            if h > hi:
                need_lvl = h - 1
                if lvl < need_lvl < nxt:
                    nxt = need_lvl
        stop = min(nxt, FLOOR)
        exp_stop = curve.get_experience_needed_for_level(stop)
        chunk = max(0, exp_stop - exp)
        xp_per = xp_per_battle(hi)
        if xp_per <= 0:
            break
        b_solo = chunk / xp_per
        b_two = chunk / (xp_per / PARTICIPANT_DIVISOR)
        solo_frames += b_solo * FRAMES_PER_WILD_BATTLE * FRAMES_PER_WIN
        two_way_frames += b_two * FRAMES_PER_WILD_BATTLE * FRAMES_PER_WIN
        battles_total += b_solo
        per_rung.append((ground, lvl, stop, hi, xp_per, b_solo))
        exp = exp_stop
        lvl = stop
        if stop >= FLOOR:
            break

    for ground, a, b, hi, xp_per, nb in per_rung:
        print(f"        {ground:<16} L{a}→L{b}   wild L{hi}   {xp_per:6.1f} xp/battle"
              f"   {nb:9,.0f} battles")

    battles_between_heals = pp_budget / TURNS_PER_BATTLE
    heal_trips = battles_total / battles_between_heals if battles_between_heals else 0
    heal_frames = heal_trips * FRAMES_PER_HEAL_TRIP

    print(f"      ⇒ battles (solo)    : {battles_total:,.0f}")
    print(f"      ⇒ PP-bounded cadence: heal every {battles_between_heals:,.0f} battles "
          f"⇒ {heal_trips:,.0f} heal trips")
    print(f"      ⇒ SOLO  (ladder)    : {(solo_frames + heal_frames) / FPS / 3600:8.1f} h"
          f"   (grind {solo_frames / FPS / 3600:.1f} h + heals {heal_frames / FPS / 3600:.1f} h)")
    print(f"      ⇒ 2-WAY (swap fires): {(two_way_frames + heal_frames) / FPS / 3600:8.1f} h"
          f"   ⚠ what happens if trigger 2 fires every battle")
    print()
    rows.append((mon.species.name, (solo_frames + heal_frames) / FPS / 3600,
                 (two_way_frames + heal_frames) / FPS / 3600, heal_trips, battles_between_heals))

print("=" * 108)
if not rows:
    print("  ✅ NOBODY IS BELOW THE FLOOR on this fixture — ruling 12 is already satisfied here.")
    raise SystemExit(0)

solo_total = sum(r[1] for r in rows)
two_total = sum(r[2] for r in rows)
print(f"  TOTAL, both trainees:   SOLO (ladder) {solo_total:,.1f} h"
      f"     2-WAY (swap fires) {two_total:,.1f} h")
print()
print("  ⭐ WHAT THE LADDER BUYS, AS A NUMBER: the difference between those two columns is the")
print("     PARTICIPANT DIVISOR alone. Both already carry the ×1.65 frames-per-WIN correction.")
print()
print("  ⛔ THE HEAL CADENCE IS THE DESIGN CONSTRAINT, AND IT IS NOT NEGOTIABLE:")
for name, _s, _t, trips, cadence in rows:
    print(f"     {name:<10} must heal every ~{cadence:,.0f} battles or trigger 2's PP half fires")
    print(f"                on EVERY battle thereafter — ~{trips:,.0f} heal trips across the grind.")
print()
print("  ‼ WHAT IS STILL NOT MEASURED, AND NO ARITHMETIC HERE CAN SETTLE IT: the HP half of")
print("    trigger 2. `hp_threshold` is 20% and the trainee out-levels its wilds, so it SHOULD be")
print("    rare — but 'should' is a reading. A drive at a level-matched ground, counting which")
print("    branch fires, is the only thing that answers it.")
print("=" * 108)
