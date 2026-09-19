# -*- coding: utf-8 -*-
"""⭐ THE L65 FLOOR, PRICED PER MŌN — AND WHO CARRIES THE HMs. (`#24-levelgap`)

WHY THIS EXISTS. USER RULING 2026-09-18: *"all pokemon in the team need to be a level between 65-75,
but not all need to be the same level."* That is a **FLOOR ON EVERY MEMBER**, and the pinned §Ch24
parties carry a **Zigzagoon L19** and a **Castform L36**. Two readings follow, and they differ by
tens of hours: train everyone, or take the stragglers out of the team.

\u26d4\u26d4 BEFORE EITHER CAN BE PRICED HONESTLY, ONE SAFETY QUESTION HAS TO BE ANSWERED FROM THE SAVE
ITSELF: **does a straggler carry a field move the navigator needs?** Boxing the only Pok\u00e9mon that
knows Surf or Waterfall would not merely slow the run \u2014 it would strand it, because §Ch24's own
geography is gated on exactly those (`region_reach.KNOWN_GATES`, and Ever Grande is an island).
\u203c A party's MOVES are not recorded in any doc in this repo. They are only knowable by reading the
save, which is what this probe does.

\u2b50 IT ALSO PRICES THE RULING, per m\u014dn, using the project's own model with the **MEASURED 3.30\u00d7**
correction (`03-PUNCH-LIST.md:810-814` \u2014 \u00d72.00 for the unmodelled 0.501 participant divisor, \u00d71.65
for ~2,368 frames per WIN against the estimator's 1,433 per BATTLE).

\u26a0 WHAT THIS DOES NOT MODEL, so nobody reads more into the hours than is there: travel and heal legs
between rounds, whiteouts, PP stalls, and party aggregation (the 0.501 divisor already encodes SOME
sharing, so SUMMING the per-m\u014dn column would double-count). Every number is a FLOOR.

READ-ONLY: loads save states, reads party memory, does arithmetic. Nothing is walked or written.
"""
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

_ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(_ROOT / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

_p = load_profile_by_name("repro-fresh")
context.profile = _p
context.config.load(_p.path, strict=False)
set_rom(_p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_p, lambda: None)
context.audio = False
context.video = False

from modules.map_data import MapRSE
from modules.memory import get_game_state
from modules.player import get_player_avatar
from modules.pokemon_party import get_party
from modules.story.training_areas import estimate_frames_to_level

SAVES = _ROOT / "tools" / "story-dev" / "saves"

#: The candidate start states for a \u00a7Ch24 training leg.
FIXTURES = ["post_ch24_atdoor_L75.ss1", "post_ch24_atdoor.ss1", "post_league_lobby.ss1",
            "post_grind_L60.ss1"]

#: \u26d4 THE FIELD MOVES THE NAVIGATOR CAN DEPEND ON. Surf and Waterfall are the two that gate \u00a7Ch24's
#: own geography (Ever Grande is an island reached by Surf; the Victory Road approach is above a
#: waterfall). The rest matter for earlier chapters and for Victory Road's interior.
HM_MOVES = {"Cut", "Fly", "Surf", "Strength", "Flash", "Rock Smash", "Waterfall", "Dive"}
#: The two that would STRAND a \u00a7Ch24 run specifically.
CRITICAL_HMS = {"Surf", "Waterfall"}

FLOOR = 65          # the ruling's floor, on EVERY member
WILD = 40           # TRAIN_SPOT_1F's band max
CORRECTION = 3.30   # MEASURED estimator optimism
FPS = 60.0

print("=" * 112)
print("THE L65 FLOOR, PER M\u014cN \u2014 AND WHO CARRIES THE HMs")
print("=" * 112)

any_read = False
for fixture in FIXTURES:
    path = SAVES / fixture
    print()
    print(f"\u2500\u2500\u2500 {fixture}")
    if not path.exists():
        print("  \u26a0 SKIPPED \u2014 no such fixture")
        continue
    context.emulator.load_save_state(path.read_bytes())
    for _ in range(40):
        context.emulator.run_single_frame()

    # \u203c CHECK THE GAME STATE, NOT THE FILENAME. Several fixtures here are saved mid-battle ON
    # PURPOSE, and an overworld-only reading taken from one is meaningless.
    state = get_game_state().name
    try:
        av = get_player_avatar()
        where = f"{MapRSE(tuple(av.map_group_and_number)).name} {tuple(av.local_coordinates)}"
    except Exception:  # noqa: BLE001 - a failed read is still a reading
        where = "<unreadable>"
    print(f"  state={state}  at {where}")

    party = list(get_party())
    if not party:
        print("  \u26d4 EMPTY PARTY \u2014 nothing to audit")
        continue
    any_read = True

    print(f"  {'slot':<5} {'species':<12} {'lvl':<5} {'to L65':<12} {'field moves held':<34} moves")
    print("  " + "-" * 104)
    carriers = {}
    total_hours = 0.0
    worst = ("", 0.0)
    for i, mon in enumerate(party):
        moves = [lm.move.name for lm in mon.moves if lm.move is not None]
        hms = sorted(set(moves) & HM_MOVES)
        for h in hms:
            carriers.setdefault(h, []).append(mon.species.name)
        if mon.level >= FLOOR:
            cost = "already \u2265 65"
        else:
            raw = estimate_frames_to_level(mon, FLOOR, WILD)
            if raw is None:
                cost = "UNKNOWN"
            else:
                hours = (raw * CORRECTION) / FPS / 3600.0
                total_hours += hours
                if hours > worst[1]:
                    worst = (mon.species.name, hours)
                cost = f"{hours:>7.1f} h"
        flag = " \u26d4" if set(hms) & CRITICAL_HMS else ""
        print(f"  {i:<5} {mon.species.name:<12} {mon.level:<5} {cost:<12} "
              f"{(', '.join(hms) or '-') + flag:<34} {', '.join(moves)}")

    print()
    # \u26d4 THE SAFETY ANSWER, stated per move rather than per m\u014dn.
    for hm in sorted(CRITICAL_HMS):
        holders = carriers.get(hm, [])
        if not holders:
            print(f"  \u26a0 NOBODY IN THIS PARTY KNOWS {hm} \u2014 \u00a7Ch24's geography is gated on it "
                  f"(`region_reach.KNOWN_GATES`). Verify before trusting any route.")
        elif len(holders) == 1:
            print(f"  \u26d4\u26d4 {hm} IS HELD BY EXACTLY ONE M\u014cN: {holders[0]}. "
                  f"**Boxing it would strand the run.** Any 'remove the stragglers' plan must "
                  f"check this first \u2014 it is the difference between a slow run and a dead one.")
        else:
            print(f"  \u2705 {hm} is held by {len(holders)} m\u014dn ({', '.join(holders)}) \u2014 no single "
                  f"point of failure for this move.")

    # ⭐⭐ THE ACTIONABLE HALF: for each mōn BELOW the floor, is it safe to remove from the team?
    #    "Safe" here means NAVIGATIONALLY safe -- every field move it holds is held by someone else
    #    too. It says nothing about whether the bot CAN deposit, or whether the user WANTS to.
    print()
    print("  ⭐ IF 'BOX THE STRAGGLERS' IS EVER CHOSEN — WHO COULD SAFELY GO:")
    for mon in party:
        if mon.level >= FLOOR:
            continue
        held = sorted({lm.move.name for lm in mon.moves if lm.move is not None} & HM_MOVES)
        sole = [h for h in held if len(set(carriers.get(h, []))) <= 1]
        if not held:
            print(f"     ✅ {mon.species.name} L{mon.level} holds NO field move — navigationally "
                  f"free to remove.")
        elif not sole:
            print(f"     ✅ {mon.species.name} L{mon.level} holds {held}, and EVERY one is also "
                  f"held by another party member — navigationally free to remove.")
        else:
            print(f"     ⛔ {mon.species.name} L{mon.level} is the SOLE carrier of {sole} — "
                  f"removing it would strand the run.")
    # And the same question for the whole party, so a future reader sees the single points of failure.
    solo = {h: v[0] for h, v in carriers.items() if len(set(v)) == 1}
    if solo:
        print(f"  ‼ SINGLE POINTS OF FAILURE IN THIS PARTY: "
              + "; ".join(f"{h} ← {who}" for h, who in sorted(solo.items())))
    missing = sorted(HM_MOVES - set(carriers))
    if missing:
        print(f"  ℹ field moves NOBODY holds: {missing} "
              f"(fine only if no route this chapter needs them)")

    below = [m for m in party if m.level < FLOOR]
    if below:
        print(f"  \u2b50 {len(below)} of {len(party)} below the L65 floor: "
              f"{', '.join(f'{m.species.name} L{m.level}' for m in below)}")
        print(f"     summed per-m\u014dn cost \u2248 {total_hours:.1f} h \u26a0 (an OVER-estimate of wall-clock: "
              f"the 3.30\u00d7 correction already encodes ~0.501 participant sharing, so these do not "
              f"simply add) \u2014 dominated by **{worst[0]} at {worst[1]:.1f} h**.")
    else:
        print(f"  \u2705 EVERY MEMBER IS ALREADY AT OR ABOVE THE L65 FLOOR.")

print()
print("=" * 112)
if not any_read:
    print("  \u26d4 NO PARTY WAS READ \u2014 this run measured nothing.")
    raise SystemExit(1)
print("  \u203c WHAT THIS SETTLES: which m\u014dn are below the ruling's floor, what each would cost, and")
print("    \u2014 the safety half \u2014 whether any straggler is the sole carrier of a move the run needs.")
print("  \u203c WHAT IT DOES NOT SETTLE: whether the bot CAN deposit a m\u014dn at all, and whether the user")
print("    wants the party changed. Both are open; neither is this probe's to decide.")
print("=" * 112)
