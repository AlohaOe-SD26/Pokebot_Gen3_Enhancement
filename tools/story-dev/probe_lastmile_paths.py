# -*- coding: utf-8 -*-
"""⭐ CAN THE BOT WALK THE LAST MILE FROM EACH ANCHOR TOWN TO EACH SPIN TILE? (`#24-levelgap`)

WHY NOW. The per-trainee Fly ladder needs six last miles: land in a town, walk to the ground's spin
tile. ✅ Already measured (`probe_fly_unlocked.py`): every anchor town is UNLOCKED on the §Ch24
fixtures, Swellow knows Fly, BADGE06 is held. ⇒ the remaining question is the WALK.

\u2b50 AND IT IS COMPUTABLE WITHOUT FLYING, because `calculate_path(source, destination, ...)` takes an
**explicit source** (`modules/map_path.py`). So every last mile can be asked for statically.

\u26d4\u26d4 THE ORIGIN HERE IS A **PROXY**, AND THE RESULT IS THEREFORE ASYMMETRIC \u2014 READ THIS BEFORE
QUOTING ANY NUMBER. The true Fly landing tile is not recorded anywhere in this repo (it comes from
the game's heal-location table). This probe uses each town's `PokemonCenter` DOOR tile instead,
because Fly in RSE lands the player at the town's heal location, which is at or beside that door.
\u21d2 **A FAILURE IS ALARMING** \u2014 if no path exists from the door, one from a tile a few steps away is
unlikely to exist either, and the rung is in trouble.
\u21d2 **A SUCCESS IS PROVISIONAL** \u2014 it shows the ground is reachable from inside the town, not that it
is reachable from the exact tile Fly delivers to. Do NOT record a PASS here as "the walk is proven".

\u26a0 A SECOND LIMIT, STATED: `calculate_path` **cannot use warps or Fly** (its own docstring). A route
that requires stepping through a door will be reported unreachable even though a human walks it
easily. That is a property of the instrument, not of the map \u2014 so a FAIL here means "not reachable
by connected-map walking", which is exactly what the bot's navigator can do unaided, and nothing
more.

READ-ONLY: loads one save state for ROM context, then computes paths. Nothing is walked or written.
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
from modules.map_path import PathFindingError, calculate_path

SAVES = _ROOT / "tools" / "story-dev" / "saves"
#: A late-game save, so any story-gated obstacle is already cleared. The PARTY does not matter here
#: — `calculate_path` is geometry, not capability.
FIXTURE = "post_ch24_atdoor_L75.ss1"

#: rung, ground, spin tile, anchor Poké Center (the PROXY origin — see the docstring).
LADDER = [
    ("L15-20", MapRSE.ROUTE117, (31, 16), PokemonCenter.VerdanturfTown),
    ("L21-24", MapRSE.ROUTE111, (25, 55), PokemonCenter.FallarborTown),
    ("L25-26", MapRSE.ROUTE115, (6, 53), PokemonCenter.RustboroCity),
    ("L27", MapRSE.ROUTE118, (29, 15), PokemonCenter.MauvilleCity),
    ("L28-38", MapRSE.ROUTE121, (44, 14), PokemonCenter.LilycoveCity),
    ("L39-75", MapRSE.VICTORY_ROAD_1F, (15, 39), PokemonCenter.EvergrandeCity),
]

print("=" * 108)
print("THE LAST MILE: anchor town \u2192 spin tile, computed from a PROXY origin (the Pok\u00e9 Center door)")
print("=" * 108)

path = SAVES / FIXTURE
if not path.exists():
    raise SystemExit(f"\u26d4 MISSING FIXTURE: {path}")
context.emulator.load_save_state(path.read_bytes())
for _ in range(40):
    context.emulator.run_single_frame()
print(f"  ROM context from: {FIXTURE}")
print(f"  \u203c origins are PROXIES (Pok\u00e9 Center doors), not measured Fly landings \u2014 a FAIL is")
print(f"    alarming, a PASS is provisional. `calculate_path` also cannot use warps or Fly.")
print()

print(f"  {'rung':<9} {'ground':<18} {'from (proxy)':<34} {'to':<10} result")
print("  " + "-" * 100)
fails, passes = [], []
for rung, ground, tile, center in LADDER:
    src_map, src_tile = center.value
    src = f"{src_map.name}{tuple(src_tile)}"
    try:
        wp = calculate_path((src_map, tuple(src_tile)), (ground, tuple(tile)))
        n = len(wp)
        # ⛔ A path that never leaves the origin map is not a "last mile" -- say which maps it crosses.
        maps = []
        for w in wp:
            nm = tuple(w.map)
            if not maps or maps[-1] != nm:
                maps.append(nm)
        names = " -> ".join(MapRSE(m).name for m in maps[:4]) + (" -> ..." if len(maps) > 4 else "")
        print(f"  {rung:<9} {ground.name:<18} {src:<34} {str(tuple(tile)):<10} \u2705 {n} wp")
        print(f"  {'':<9} {'':<18} {'':<34} {'':<10}    via {names}")
        passes.append((rung, ground.name, n))
    except PathFindingError as error:
        print(f"  {rung:<9} {ground.name:<18} {src:<34} {str(tuple(tile)):<10} \u26d4 NO PATH")
        print(f"  {'':<9} {'':<18} {'':<34} {'':<10}    {str(error)[:82]}")
        fails.append((rung, ground.name, str(error)))
    except Exception as error:  # noqa: BLE001 - any other failure IS the reading
        print(f"  {rung:<9} {ground.name:<18} {src:<34} {str(tuple(tile)):<10} "
              f"\u26a0 {type(error).__name__}")
        fails.append((rung, ground.name, f"{type(error).__name__}: {error}"))

print()
print("=" * 108)
print(f"  walkable from the proxy origin: {len(passes)}/{len(LADDER)}")
if fails:
    print()
    print(f"  \u26d4\u26d4 {len(fails)} RUNG(S) HAVE NO CONNECTED-MAP PATH FROM THEIR ANCHOR TOWN:")
    for rung, name, why in fails:
        print(f"     {rung:<9} {name:<18} {why[:70]}")
    print()
    print("     \u21d2 EACH NEEDS A REASON BEFORE THE LEG IS BUILT. Two innocent explanations exist and")
    print("       must be told apart: (a) the route legitimately crosses a WARP, which this")
    print("       instrument cannot use and the bot's `navigate_to_anywhere` CAN; or (b) the ground")
    print("       is genuinely cut off from its anchor, which would make that rung unbuildable.")
    print("     \u26d4 Do NOT assume (a). VICTORY_ROAD_1F is the known warp case; the others are not.")
else:
    print("  \u2705 every rung has a connected-map path from inside its anchor town (provisional \u2014 the")
    print("     origin is a proxy and the true Fly landing is still unrecorded).")
print("=" * 108)
