# -*- coding: utf-8 -*-
"""⭐ WHICH FLY DESTINATIONS ARE ACTUALLY UNLOCKED ON THE §Ch24 FIXTURES? (`#24-levelgap` piece 2)

WHY THIS GATES THE DESIGN. USER RULING 2026-09-19: train each m\u014dn at a level-appropriate ground,
**flying** to reach it. The ladder that satisfies it needs six grounds, each anchored at its heal
centre (`_training_area_heal_map()`):

    ROUTE117 \u2190 Verdanturf | ROUTE111 \u2190 Fallarbor | ROUTE115 \u2190 Rustboro
    ROUTE118 \u2190 Mauville   | ROUTE121 \u2190 Lilycove  | VICTORY_ROAD_1F \u2190 Ever Grande

\u26d4 **A FLY DESTINATION THE PARTY HAS NEVER VISITED IS NOT ON THE REGION MAP**, and
`fly_to_destination` raises on exactly that (`pokemon_league.py`, third guard:
`get_event_flag(destination.get_flag_name())`). \u21d2 if a rung's anchor town is locked, that rung
**cannot be reached by Fly at all** and the ladder has a hole \u2014 which would be a far better thing to
learn from a flag read than from a drive that walks into it.

\u203c THE SAME GUARD BLOCK GIVES THE OTHER TWO PRECONDITIONS, so they are read here too: a party member
must know **Fly**, and **BADGE06** must be held.

\u26a0 WHAT THIS DOES **NOT** ANSWER, stated so the result is not over-read: whether the LAST MILE from
each landing to each spin tile is walkable. That needs the bot to actually be standing at the
landing, so it is a drive question, not a flag question. This probe answers reachability of the
TOWN, nothing further.

READ-ONLY: loads save states, reads flags and the party. Nothing is walked or written.
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

from modules.map_data import MapRSE, PokemonCenter
from modules.memory import get_event_flag, get_game_state
from modules.player import get_player_avatar
from modules.pokemon_party import get_party

SAVES = _ROOT / "tools" / "story-dev" / "saves"
FIXTURES = ["post_ch24_atdoor_L75.ss1", "post_league_lobby.ss1", "post_grind_L60.ss1"]

#: The ladder, as measured by `probe_training_ladder.py` under the out-level cap, paired with the
#: heal centre each ground is anchored at. \u203c ANCHORED ON THE HEAL CENTRE, NOT THE NEAREST TOWN \u2014
#: ROUTE111's nearest town is Mauville, which is the WRONG SIDE of the Go-Goggles desert and the
#: most-failed walk in this tree; its heal centre is Fallarbor, which is correct.
LADDER = [
    ("L15-20", MapRSE.ROUTE117, PokemonCenter.VerdanturfTown),
    ("L21-24", MapRSE.ROUTE111, PokemonCenter.FallarborTown),
    ("L25-26", MapRSE.ROUTE115, PokemonCenter.RustboroCity),
    ("L27", MapRSE.ROUTE118, PokemonCenter.MauvilleCity),
    ("L28-38", MapRSE.ROUTE121, PokemonCenter.LilycoveCity),
    ("L39-75", MapRSE.VICTORY_ROAD_1F, PokemonCenter.EvergrandeCity),
]

print("=" * 104)
print("WHICH FLY DESTINATIONS ARE UNLOCKED ON THE \u00a7Ch24 FIXTURES?")
print("=" * 104)

try:
    from modules.region_map import FlyDestinationRSE
except Exception as error:  # noqa: BLE001 - if the enum moved, say so rather than guess
    print(f"  \u26d4 COULD NOT IMPORT FlyDestinationRSE: {type(error).__name__}: {error}")
    raise SystemExit(1)

#: town name (as PokemonCenter member) -> the FlyDestinationRSE member, matched by NAME.
#: \u203c Matched, not assumed: if a name does not line up the probe SAYS so instead of silently
#: skipping a rung, because a silently skipped rung is exactly the hole this exists to find.
def _fly_for(center) -> "object | None":
    want = center.name.lower().replace("city", "").replace("town", "")
    for d in FlyDestinationRSE:
        got = d.name.lower().replace("city", "").replace("town", "")
        if got == want:
            return d
    return None


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
    any_read = True

    state = get_game_state().name
    try:
        av = get_player_avatar()
        where = f"{MapRSE(tuple(av.map_group_and_number)).name}"
    except Exception:  # noqa: BLE001
        where = "<unreadable>"
    party = get_party()
    flyer = party.first_pokemon_with_move("Fly")
    badge06 = get_event_flag("BADGE06_GET")
    print(f"  state={state}  at {where}")
    print(f"  Fly knower : {flyer.species.name if flyer else '\u26d4 NOBODY'}"
          f"     BADGE06_GET = {badge06}")
    if flyer is None or not badge06:
        print("  \u26d4 Fly is unusable on this fixture regardless of destinations \u2014 the first two")
        print("     guards already fail. The ladder cannot be flown from here.")

    print()
    print(f"  {'rung':<9} {'ground':<18} {'anchor town':<18} {'fly enum':<18} unlocked?")
    print("  " + "-" * 92)
    holes = []
    for rung, ground, center in LADDER:
        dest = _fly_for(center)
        if dest is None:
            print(f"  {rung:<9} {ground.name:<18} {center.name:<18} "
                  f"{'\u26d4 NO ENUM MATCH':<18} \u2014")
            holes.append((rung, center.name, "no FlyDestinationRSE member matched"))
            continue
        try:
            ok = bool(get_event_flag(dest.get_flag_name()))
        except Exception as error:  # noqa: BLE001 - a failed flag read IS the reading
            print(f"  {rung:<9} {ground.name:<18} {center.name:<18} {dest.name:<18} "
                  f"\u26d4 read failed: {type(error).__name__}")
            holes.append((rung, center.name, f"flag read failed: {error}"))
            continue
        mark = "\u2705 unlocked" if ok else "\u26d4 LOCKED \u2014 rung unreachable by Fly"
        print(f"  {rung:<9} {ground.name:<18} {center.name:<18} {dest.name:<18} {mark}")
        if not ok:
            holes.append((rung, center.name, "destination flag is not set"))

    print()
    if holes:
        print(f"  \u26d4\u26d4 {len(holes)} RUNG(S) OF THE LADDER CANNOT BE FLOWN TO FROM THIS FIXTURE:")
        for rung, town, why in holes:
            print(f"     {rung:<9} needs {town} \u2014 {why}")
        print("     \u21d2 the per-trainee ladder has a HOLE here. Either those m\u014dn cannot be trained")
        print("       level-appropriately, or the leg must walk instead of fly, or the fixture is")
        print("       not representative of a real playthrough. Decide before building the leg.")
    else:
        print("  \u2705\u2705 EVERY LADDER RUNG'S ANCHOR TOWN IS UNLOCKED \u2014 the ladder is flyable end to end")
        print("     from this fixture (town reachability only; the last mile is a drive question).")

print()
print("=" * 104)
if not any_read:
    print("  \u26d4 NO FIXTURE WAS READ \u2014 this run measured nothing.")
    raise SystemExit(1)
print("  \u203c SCOPE: this answers whether each ANCHOR TOWN is on the region map. It does NOT answer")
print("    whether the walk from a landing to a spin tile succeeds \u2014 that needs a drive, and")
print("    ROUTE111's walk in particular is the most-failed in this tree (1,041 logged drops).")
print("=" * 104)
