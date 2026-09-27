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

_ROOT = _pl.Path(__file__).resolve().parents[2]
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

#: ⛔⛔ NO HARDCODED LADDER. v1 transcribed one and got FOUR OF SIX RUNGS WRONG, because it copied
#: the TRAINEE-LEVEL ranges out of `probe_training_ladder.py` ("ROUTE117 L15-20") and used them as
#: WILD-LEVEL TOPS. Those are different quantities: ROUTE117's real band is (13, 14), ROUTE121's is
#: (25, 28), and VICTORY_ROAD_1F's is (36, 40) -- not 20 / 38 / 75.
#: Since `xp_per_battle()` is linear in the WILD level, the two rungs that carry the climb were
#: priced 1.36x and 1.875x too rich, and every hour figure derived from them was UNDERSTATED.
#: ⇒ THE FIX IS STRUCTURAL, NOT ARITHMETIC: ask the PRODUCTION PICKER. `best_training_area` is the
#: function the bot itself uses, `TRAINING_GRASS` is the table it reads, and a probe that models
#: them instead of calling them is measuring its own model. A transcribed table cannot disagree
#: with production loudly -- it disagrees silently.
def _rung_for(level: int):
    """(ground, top-wild) the PRODUCTION picker chooses for a trainee at this level, or None.

    ‼ `allow=_ALLOW_ALL` deliberately: this probe prices the LADDER's arithmetic, not its
    reachability, and reachability is measured separately by `probe_fly_disjunct.py` (gate #68).
    Passing `allow=None` would silently drop every area carrying an `AREA_PREREQ` -- including
    VICTORY_ROAD_1F and both surf rungs -- and quietly price a SHORTER ladder than the bot walks.
    """
    from modules.story.training_areas import best_training_area

    best = best_training_area(level, max_wild_max=level + 1, allow=_ALLOW_ALL)
    if best is None:
        return None
    map_enum, _tile, (_lo, hi) = best
    return map_enum.name, hi


def _ALLOW_ALL(_map_enum, _tile, _prereq) -> bool:
    return True

#: ✅ MEASURED 2026-09-23, was an assumption: **1.83 turns per wild battle** — 53 `decide_turn` calls
#: over 29 battles, `--driver ch24swaptrigger` at ROUTE117 with a L19 trainee.
#: ‼ THE ORIGINAL ASSUMPTION OF 3 WAS CONSERVATIVE, AND ITS COMMENT MISLABELLED THE DIRECTION.
#: More turns drain PP FASTER ⇒ fewer battles per budget ⇒ a SHORTER cadence ⇒ a HARSHER answer.
#: Assuming 3 against a real 1.83 therefore understated the PP budget (27 battles vs ~44) — safe,
#: but the old comment called 3 “conservative-LOW” and reasoned the opposite way round. Corrected
#: rather than quietly replaced, because the reasoning was the wrong shape even though the number
#: erred in the right direction.
TURNS_PER_BATTLE = 1.83

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
        ground, hi = rung
        # ⭐ WHERE DOES THIS RUNG END? Ask the picker, do not model it: step the level until it
        # answers with a DIFFERENT ground. That way the probe's rung boundaries are the bot's rung
        # boundaries by construction, whatever the table says today.
        stop = FLOOR
        for probe_lvl in range(lvl + 1, FLOOR + 1):
            nxt_rung = _rung_for(probe_lvl)
            if nxt_rung is not None and nxt_rung[0] != ground:
                stop = probe_lvl
                break
        stop = min(stop, FLOOR)
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
