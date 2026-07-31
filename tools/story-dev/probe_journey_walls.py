"""#24-journey / KI-39 part 3: name the ACTUAL wall on each blocked corridor.

WHERE WE ARE. `probe_journey_why.py` measured, from Mauville (`rocksmash_taught.ss1`):
    ROUTE110  17/125 tiles reachable      ROUTE111  11/173      ROUTE117  22/41
    ROUTE112   0/76                       ROUTE116   0/73       VERDANTURF 14/23
All of those maps share `map_path` level 459 — i.e. `calculate_path` DOES try and fails at
TILE level. So KI-39's "no cross-map planning" story cannot be the explanation for most of
them; a partial-reachability result means the planner walked in and hit a wall.

`modules/story/early_game.py` already records the ground truth for one of them, in prose,
inside `travel_lavaridge_to_petalburg`'s docstring: the Mauville->Route 112 corridor runs up
Route 111's west junction (y67-99) and passes a **twin-rocks choke that needs ROCK SMASH**
at (18,101); the Go-Goggles desert seals y~61-88 further north and "never touches" it.

THE TEST. If the rock is the wall, then from Mauville the reachable part of Route 111 must
stop DEAD just south of it, and every tile north of the choke must be unreachable. That is a
falsifiable prediction with an exact coordinate, so measure it:
  * the reachable y-extent of column 18 (and its neighbours) on ROUTE111;
  * the same profile for ROUTE110 (to characterise ITS wall);
  * the tile facts at the choke, including `dynamic_collision_flag` — the field
    `calculate_path` uses to model an obstacle that an event flag can clear.

WHY IT MATTERS. The three causes need three DIFFERENT fixes, and building a generic journey
planner would fix none of them:
  (a) a dynamic obstacle the planner treats as permanent  -> clear it, or plan through it;
  (b) a capability gate (Go-Goggles desert)               -> honest refusal, not a planner;
  (c) a genuine warp-only link inside one region (Rusturf
      Tunnel) that `plan()` never supplies because start
      and goal share a region                              -> THIS is the real KI-39 bug.

Run: PYTHONUTF8=1 py -3.12 tools/story-dev/probe_journey_walls.py
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


def name_of(m) -> str:
    try:
        return MapRSE(tuple(m)).name
    except ValueError:
        return str(tuple(m))


def reachable(src, src_xy, dst, xy) -> bool:
    try:
        calculate_path((tuple(src), tuple(src_xy)), (tuple(dst), tuple(xy)))
        return True
    except Exception:  # noqa: BLE001
        return False


def path_tile_facts(m, xy) -> str:
    """The PATH-LEVEL view — what `calculate_path` itself believes about the tile.
    `dynamic_collision_flag` is the field that models a Rock-Smash rock / cut tree:
    the tile is impassable until that event flag is set."""
    try:
        t = _find_tile_by_local_coordinates(tuple(m), tuple(xy))
        return (f"elev={t.elevation} "
                f"accessible_from={[d.name for d in t.accessible_from_direction if t.accessible_from_direction[d]]} "
                f"dyn_collision_flag={t.dynamic_collision_flag} dyn_object_id={t.dynamic_object_id} "
                f"warps_to={'yes' if t.warps_to else 'no'}")
    except Exception as e:  # noqa: BLE001
        return f"<{type(e).__name__}: {e}>"


def column_profile(src, src_xy, m, x, y_range) -> None:
    """Which y values of column `x` are reachable? Prints a compact run-length map so a
    hard boundary is unmistakable."""
    marks = []
    for y in y_range:
        marks.append("#" if reachable(src, src_xy, m, (x, y)) else ".")
    line = "".join(marks)
    print(f"    x={x:<3} y{y_range[0]}..{y_range[-1]}  {line}")
    # Report the boundary explicitly — a wall of dots after a run of hashes is the claim.
    first_gap = None
    for i, c in enumerate(line):
        if c == "." and i > 0 and line[i - 1] == "#":
            first_gap = y_range[i]
            break
    if first_gap is not None:
        print(f"          -> reachable stops at y={first_gap - 1}; first blocked y={first_gap}")


def main() -> int:
    context.emulator.load_save_state((SAVES / "rocksmash_taught.ss1").read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    a = get_player_avatar()
    here, here_xy = tuple(a.map_group_and_number), tuple(a.local_coordinates)
    print(f"PLAYER {name_of(here)} {here_xy}\n")

    print("ROUTE111 — the Mauville->Route112 corridor. Prediction: a HARD stop at the")
    print("twin-rocks choke at (18,101), i.e. reachable y>=102, blocked y<=101.")
    print("=" * 78)
    r111 = MapRSE.ROUTE111.value
    for x in (17, 18, 19, 20):
        column_profile(here, here_xy, r111, x, list(range(139, 89, -1)))
    print()
    print("  TILE FACTS at the choke (calculate_path's own view):")
    for xy in ((18, 102), (18, 101), (18, 100), (18, 99), (19, 101), (17, 101)):
        print(f"    ROUTE111{xy}  {path_tile_facts(r111, xy)}")
    print()

    print("ROUTE110 — characterise ITS wall (KI-39 probed (12,60), which is deep south).")
    print("=" * 78)
    r110 = MapRSE.ROUTE110.value
    md = get_map_data(r110, (0, 0))
    print(f"  size={md.map_size}")
    for x in (12, 18, 24):
        column_profile(here, here_xy, r110, x, list(range(0, 40)))
    print()

    print("ROUTE116 / VERDANTURF — is the ONLY link the Rusturf Tunnel WARP?")
    print("=" * 78)
    v = MapRSE.VERDANTURF_TOWN.value
    r116 = MapRSE.ROUTE116.value
    print(f"  VERDANTURF declares a North connection to ROUTE116 (offset -80).")
    print(f"  Verdanturf (16,9) reachable from Mauville? "
          f"{reachable(here, here_xy, v, (16, 9))}")
    print("  From VERDANTURF (16,9), can calculate_path reach ROUTE116 by walking?")
    hits = 0
    for y in range(0, 40, 3):
        for x in range(0, 40, 4):
            if reachable(v, (16, 9), r116, (x, y)):
                hits += 1
    print(f"    reachable ROUTE116 sample tiles from Verdanturf: {hits}")
    print(f"  Rusturf Tunnel door VERDANTURF(8,1) reachable from Verdanturf? "
          f"{reachable(v, (16, 9), v, (8, 1))}")
    print(f"    tile facts: {path_tile_facts(v, (8, 1))}")
    print()
    print("  => If the sample is 0 while the tunnel door IS reachable, the declared")
    print("     North connection is not physically walkable and the real link is a WARP")
    print("     INSIDE ONE REGION — the case `WarpGraph.plan` can never serve, because it")
    print("     returns [] the moment start and goal share a region. THAT is KI-39.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
