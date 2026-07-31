"""#24-journey / KI-39 follow-up: WHY does a DIRECTLY-CONNECTED neighbour fail to path?

`probe_journey_legs.py` (2026-07-31) refuted KI-39's stated cause. Measured from Mauville:
ROUTE110 and ROUTE111 are ONE `conn` hop away — no warp involved at all — and
`calculate_path` still returns "Could not find a path" (not "not on connected maps", which
is the different error it raises for a warp-only route, and which FIERY_PATH did produce).

So for those pairs the journey planner is NOT the missing piece. Something at TILE level is.
Three candidate explanations, and they need completely different fixes:

  1. The DESTINATION TILE is bad — unwalkable, water, or on the far side of a split. Then
     KI-39's whole measurement is an artefact of arbitrarily-chosen probe tiles and there is
     far less broken here than the handoff claims.
  2. The SOURCE side is sealed — you cannot leave Mauville in that direction at all (a gate
     BUILDING sits on the border, so the physical route is a warp even though the map headers
     declare an edge connection).
  3. A genuine mid-route wall (the Go-Goggles desert; a dual-elevation bridge).

This probe separates them by ASKING, not reasoning:
  * dump each map's connections + warps;
  * probe MANY destination tiles per map (every warp tile + a coarse grid), so "no path to
    (12,60)" cannot be mistaken for "no path to ROUTE110";
  * report each candidate tile's collision/elevation so an unwalkable target is obvious;
  * and report the two PathFindingError texts distinctly, since they mean different things.

Run: PYTHONUTF8=1 py -3.12 tools/story-dev/probe_journey_why.py
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
from modules.map_path import PathFindingError, _get_all_maps_metadata, calculate_path
from modules.player import get_player_avatar

SAVES = REPO / "tools" / "story-dev" / "saves"


def name_of(m) -> str:
    try:
        return MapRSE(tuple(m)).name
    except ValueError:
        return str(tuple(m))


def dump_map(m) -> None:
    md = get_map_data(tuple(m), (0, 0))
    print(f"  {name_of(m)} size={md.map_size}")
    for c in md.connections:
        print(f"     conn {c.direction:<7} -> "
              f"{name_of((c.destination_map_group, c.destination_map_number))} offset={c.offset}")
    for i, w in enumerate(md.warps):
        print(f"     warp #{i} at {tuple(w.local_coordinates)} -> "
              f"{name_of((w.destination_map_group, w.destination_map_number))}"
              f" id={w.destination_warp_id}")


def tile_facts(m, xy) -> str:
    try:
        t = get_map_data(tuple(m), tuple(xy))
        return (f"collision={getattr(t, 'collision', '?')} elev={getattr(t, 'elevation', '?')} "
                f"surf={getattr(t, 'is_surfable', '?')} encounter={getattr(t, 'has_encounters', '?')}")
    except Exception as e:  # noqa: BLE001
        return f"<{type(e).__name__}>"


def try_path(src, src_xy, dst, dst_xy):
    try:
        p = calculate_path((tuple(src), tuple(src_xy)), (tuple(dst), tuple(dst_xy)))
        return "OK", len(p)
    except PathFindingError as e:
        text = str(e)
        kind = "NOT-CONNECTED" if "not on connected maps" in text else "NO-PATH"
        return kind, 0
    except Exception as e:  # noqa: BLE001
        return f"ERR:{type(e).__name__}", 0


def candidate_tiles(m, step: int = 6) -> list[tuple[int, int]]:
    """Every warp tile plus a coarse grid — so a single bad probe tile cannot be
    mistaken for a whole unreachable map."""
    md = get_map_data(tuple(m), (0, 0))
    tiles = [tuple(w.local_coordinates) for w in md.warps]
    w, h = md.map_size
    for y in range(0, h, step):
        for x in range(0, w, step):
            tiles.append((x, y))
    seen, out = set(), []
    for t in tiles:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


TARGETS = [MapRSE.ROUTE110, MapRSE.ROUTE111, MapRSE.ROUTE112, MapRSE.ROUTE117,
           MapRSE.ROUTE116, MapRSE.VERDANTURF_TOWN, MapRSE.FIERY_PATH]


def main() -> int:
    context.emulator.load_save_state((SAVES / "rocksmash_taught.ss1").read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    avatar = get_player_avatar()
    here, here_xy = tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)
    print(f"PLAYER {name_of(here)} {here_xy}\n")

    print("MAP HEADERS")
    print("=" * 78)
    for m in [MapRSE.MAUVILLE_CITY, MapRSE.VERDANTURF_TOWN, MapRSE.ROUTE111, MapRSE.ROUTE112]:
        dump_map(m.value)
        print()

    meta = _get_all_maps_metadata()
    print("CONNECTION-COMPONENT (map_path `level`) — same level means calculate_path may try")
    print("=" * 78)
    for m in [MapRSE.MAUVILLE_CITY, *TARGETS]:
        lv = meta[tuple(m.value)].level if tuple(m.value) in meta else "?"
        off = meta[tuple(m.value)].offset if tuple(m.value) in meta else "?"
        print(f"  {name_of(m.value):<20} level={lv}  global_offset={off}")
    print()

    print("KI-39's PROBE TILES — are they even walkable?")
    print("=" * 78)
    for m, xy in ((MapRSE.ROUTE110, (12, 60)), (MapRSE.ROUTE116, (11, 7)),
                  (MapRSE.ROUTE111, (25, 55)), (MapRSE.ROUTE117, (31, 16)),
                  (MapRSE.FIERY_PATH, (18, 19))):
        print(f"  {name_of(m.value):<16}{xy}  {tile_facts(m.value, xy)}")
    print()

    print("HOW MANY TILES OF EACH MAP CAN calculate_path REACH FROM MAUVILLE (32,15)?")
    print("=" * 78)
    print("  (warp tiles + a 6-tile grid; 'reachable' means the SAME call navigate_to uses)")
    for target in TARGETS:
        tmap = tuple(target.value)
        tiles = candidate_tiles(tmap)
        results = {}
        best = None
        for xy in tiles:
            kind, n = try_path(here, here_xy, tmap, xy)
            results[kind] = results.get(kind, 0) + 1
            if kind == "OK" and (best is None or n < best[1]):
                best = (xy, n)
        summary = "  ".join(f"{k}={v}" for k, v in sorted(results.items()))
        line = f"  {name_of(tmap):<20} tiles={len(tiles):<4} {summary}"
        if best:
            line += f"   <- REACHABLE, e.g. {best[0]} in {best[1]} waypoints"
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
