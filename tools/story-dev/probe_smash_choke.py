"""#24-smashroute / KI-41: is the ROUTE111 choke DISCOVERABLE from game data, or must it
be a hand-verified table?

KI-41 measured that a Rock Smash rock at ROUTE111 (18,101) seals the Mauville -> Route 112
corridor, which is what actually keeps FIERY_PATH's Machop (the counter the ladder names)
out of reach. Before building anything, answer the design question that decides the shape of
the fix:

  (a) The obstacle is visible in map data — an object event carrying a Rock Smash script, or
      a tile the pathfinder tags with a `dynamic_collision_flag` / `dynamic_object_id`. Then
      a GENERAL "clear the obstacle blocking this corridor" routine is possible.
  (b) It is not distinguishable from ordinary terrain. Then the honest fix is a small
      hand-verified table of chokes, in the style of `region_reach.KNOWN_GATES`, where every
      entry says how it was verified.

Guessing between these is how this project produced the refuted gateway waypoints. Measure.

Also dumps the REACHABLE FRONTIER — the walkable tiles adjacent to the blocked ones — because
whatever the fix is, it needs a tile to stand on and a direction to face, and those must come
from data rather than from a docstring's prose.

Run: PYTHONUTF8=1 py -3.12 tools/story-dev/probe_smash_choke.py
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Manual"

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, _find_tile_by_local_coordinates, calculate_path
from modules.player import get_player_avatar

SAVES = REPO / "tools" / "story-dev" / "saves"
R111 = tuple(MapRSE.ROUTE111.value)


def reachable(src, src_xy, xy) -> bool:
    try:
        calculate_path((tuple(src), tuple(src_xy)), (R111, tuple(xy)))
        return True
    except (PathFindingError, Exception):
        return False


def main() -> int:
    context.emulator.load_save_state((SAVES / "rocksmash_taught.ss1").read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    a = get_player_avatar()
    here, here_xy = tuple(a.map_group_and_number), tuple(a.local_coordinates)
    print(f"PLAYER {MapRSE(here).name} {here_xy}\n")

    md = get_map_data(R111, (0, 0))
    print(f"ROUTE111 size={md.map_size}, {len(md.objects)} object events\n")

    print("A. OBJECT EVENTS near the choke (y 95..110) — the (a) hypothesis")
    print("=" * 78)
    found = 0
    for obj in md.objects:
        try:
            xy = tuple(obj.local_coordinates)
        except Exception:  # noqa: BLE001
            continue
        if not (95 <= xy[1] <= 110):
            continue
        found += 1
        print(f"  ({xy[0]:>2},{xy[1]:>3})  script={getattr(obj, 'script_symbol', '?')}  "
              f"flag={getattr(obj, 'flag', '?')}  kind={getattr(obj, 'kind', '?')}")
    if not found:
        print("  (none in that band)")
    print()

    print("B. WHAT THE PATHFINDER BELIEVES about the choke row")
    print("=" * 78)
    print("  (dyn_collision_flag / dyn_object_id are how map_path models a clearable obstacle)")
    for xy in [(x, y) for y in (103, 102, 101, 100, 99) for x in (17, 18, 19, 20)]:
        try:
            t = _find_tile_by_local_coordinates(R111, xy)
            acc = t.accessible_from_direction
            # `accessible_from_direction` is a plain sequence of bools indexed by Direction.
            acc_txt = "".join("NESW"[i] if v else "-" for i, v in enumerate(acc)) \
                if not hasattr(acc, "items") else str(acc)
            print(f"  ({xy[0]:>2},{xy[1]:>3}) elev={t.elevation:<3} acc={acc_txt:<5} "
                  f"dyn_flag={t.dynamic_collision_flag} dyn_obj={t.dynamic_object_id} "
                  f"collision={getattr(t, 'collision', '?')}")
        except Exception as e:  # noqa: BLE001
            print(f"  ({xy[0]:>2},{xy[1]:>3}) <{type(e).__name__}: {e}>")
    print()

    print("C. THE REACHABLE FRONTIER — where can the bot STAND to act on the choke?")
    print("=" * 78)
    frontier = []
    for x in range(14, 24):
        for y in range(98, 106):
            if reachable(here, here_xy, (x, y)):
                frontier.append((x, y))
    print(f"  reachable tiles in x14..23 / y98..105: {frontier}")
    if frontier:
        southmost = min(frontier, key=lambda t: -t[1])
        print(f"  northernmost (lowest y) reachable: {min(frontier, key=lambda t: t[1])}")
        print(f"  => a stand-tile must be one of these, and it must be ADJACENT to a blocked "
              f"tile in the direction of travel (north = decreasing y).")
    print()

    print("D. VERDICT")
    print("=" * 78)
    print("  If A listed a Rock Smash object event at/next to the blocked row, a GENERAL")
    print("  obstacle-clearing routine is possible: find the object, walk to the adjacent")
    print("  reachable tile, face it, use the move.")
    print("  If A is empty and B shows no dyn_* fields, the obstacle is indistinguishable")
    print("  from terrain at this level and the fix must be a hand-verified choke table")
    print("  (style: region_reach.KNOWN_GATES — every entry states how it was verified).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
