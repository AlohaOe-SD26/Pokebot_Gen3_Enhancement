"""WHAT THE GAME ACTUALLY WALKS ON — the LIVE map grid (`gBackupMapLayout`), vs what we plan on.

‼ WHY THIS EXISTS. On 2026-09-01 the first §Ch21 leg-3 drive walked out of the Sootopolis Poke
Center toward the dive tile and JAMMED at SOOTOPOLIS_CITY (31,42) with
`UnreachableDestinationError: the field is idle and we are still at (31,42), so retrying cannot
change the result`. Our planner had happily returned a route through that tile.

There are THREE ways our tile reader can disagree with the game, and the tree only had instruments
for the first two:
  1. `setmaplayoutindex` — the map swaps to a different LAYOUT at runtime. Covered by
     `probe_ch21_route131_live.py` (Route 131) and by leg 3's own `_route131_layout_reading`.
  2. loaded OBJECTS standing on tiles. Covered by `get_map_objects()`.
  3. ⛔ `setmetatile` — a script REWRITES INDIVIDUAL TILES in the live map grid. **NOTHING in this
     tree could see that**, and it is invisible in principle to every reader we own:
     `MapLocation._metatile_attributes` (map.py:769-771) dereferences
     `self._map_layout[12:16]`, the blockdata pointer, which points into **ROM**. `setmetatile`
     writes into `sBackupMapData` in **RAM**. A ROM read can never observe a RAM write.

That is KI-74, and `SootopolisCity_OnLoad` uses it to close TEN doors at VAR_SOOTOPOLIS_CITY_STATE
== 3 — the exact state leg 3 runs in.

⇒ THIS PROBE READS THE GRID THE GAME ITSELF READS. `gBackupMapLayout` is
`{ s32 width; s32 height; u16 *map; }`; the map is the live block grid including a border margin.
Every difference it reports against `get_map_data` is a tile where the bot's model of the world is
wrong — whatever the cause.

--------------------------------------------------------------------------------------------
CONTROLS (a probe that finds nothing must be distinguishable from one that cannot see)
--------------------------------------------------------------------------------------------
C1  THE OFFSET IS CALIBRATED, NOT ASSUMED. The border margin is searched over candidate offsets
    and the one with the HIGHEST agreement against `get_map_data` wins. A probe that hardcoded
    MAP_OFFSET and got it wrong would report every tile as "different" — which is
    indistinguishable from a real catastrophic divergence.
C2  THE WINNING OFFSET MUST AGREE ALMOST EVERYWHERE. If the best agreement is not overwhelming,
    we are not reading the grid we think we are, and every difference below is noise.
C3  The avatar's own tile must be walkable in the live grid — it is standing there.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_live_mapgrid.py <save.ss1> [MAP_NAME]
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
context.bot_mode = "Story"

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import read_symbol, unpack_uint32
from modules.player import get_player_avatar


def live_grid() -> tuple[int, int, dict[tuple[int, int], int], int]:
    """(width, height, {(gx,gy): block}, best_offset) read from `gBackupMapLayout`."""
    header = read_symbol("gBackupMapLayout", 0, 12)
    width = unpack_uint32(header[0:4])
    height = unpack_uint32(header[4:8])
    pointer = unpack_uint32(header[8:12])
    raw = context.emulator.read_bytes(pointer, width * height * 2)
    grid = {}
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 2
            grid[(x, y)] = raw[offset] | (raw[offset + 1] << 8)
    return width, height, grid, pointer


def collision_of(block: int) -> int:
    return (block & 0x0C00) >> 10


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: probe_live_mapgrid.py <save.ss1> [MAP_NAME]")
        return 2
    save = pathlib.Path(sys.argv[1])
    if not save.is_absolute():
        for base in (pathlib.Path(__file__).resolve().parent / "saves", pathlib.Path.cwd()):
            if (base / save).exists():
                save = base / save
                break
    print("=" * 100)
    print("THE LIVE MAP GRID (gBackupMapLayout) vs OUR PLANNER'S VIEW (get_map_data)")
    print("=" * 100)
    print(f"save: {save}")
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    avatar = get_player_avatar()
    here = tuple(avatar.local_coordinates)
    map_value = tuple(avatar.map_group_and_number)
    map_enum = MapRSE(map_value)
    print(f"standing on {map_enum.name} {here}")

    width, height, grid, pointer = live_grid()
    map_width, map_height = get_map_data(map_enum, (0, 0)).map_size
    print(f"gBackupMapLayout: {width} x {height} at 0x{pointer:08X}   "
          f"(the MAP itself is {map_width} x {map_height})")

    # ---- C1: calibrate the border offset instead of assuming MAP_OFFSET ----------------------
    print("")
    print("-" * 100)
    print("CONTROL 1 — calibrate the border offset (never assume it)")
    print("-" * 100)
    sample = [(x, y) for x in range(0, map_width, 2) for y in range(0, map_height, 2)]
    ours = {}
    for tile in sample:
        try:
            ours[tile] = get_map_data(map_enum, tile).collision
        except Exception:
            continue
    best = (None, -1.0)
    for offset in range(0, 9):
        hits = 0
        for (x, y), collision in ours.items():
            block = grid.get((x + offset, y + offset))
            if block is not None and collision_of(block) == collision:
                hits += 1
        rate = hits / max(1, len(ours))
        marker = ""
        if rate > best[1]:
            best = (offset, rate)
            marker = "  <- best so far"
        print(f"  offset {offset}: agreement {hits}/{len(ours)} = {rate:.1%}{marker}")
    offset, rate = best
    c2_ok = rate >= 0.95
    print(f"  ⇒ border offset = {offset} at {rate:.1%}   "
          f"{'PASS' if c2_ok else 'FAIL — we are not reading the grid we think we are'}")
    if not c2_ok:
        print("‼ CONTROLS FAILED — every difference below would be noise. Stopping.")
        return 1

    # ---- C3 ----------------------------------------------------------------------------------
    standing = collision_of(grid.get((here[0] + offset, here[1] + offset), 0x0400))
    print(f"  CONTROL 3 — the avatar's own tile {here} is collision {standing} in the LIVE grid "
          f"{'PASS' if standing == 0 else 'FAIL'}")

    # ---- the differences ----------------------------------------------------------------------
    print("")
    print("=" * 100)
    print("DIFFERENCES — tiles where the GAME and OUR PLANNER disagree about walkability")
    print("=" * 100)
    worse, better = [], []
    for y in range(map_height):
        for x in range(map_width):
            block = grid.get((x + offset, y + offset))
            if block is None:
                continue
            live = collision_of(block)
            try:
                planned = get_map_data(map_enum, (x, y)).collision
            except Exception:
                continue
            if live == planned:
                continue
            (worse if (planned == 0 and live != 0) else better).append((x, y))
    print(f"  ⛔ WE THINK OPEN, THE GAME SAYS WALL  : {len(worse)} tiles  <- these are the DANGEROUS ones")
    print(f"     {sorted(worse)}")
    print(f"  ✅ we think wall, the game says open  : {len(better)} tiles")
    print(f"     {sorted(better)}")

    # ---- does it explain the jam? --------------------------------------------------------------
    # ⛔⛔ THIS SECTION IS OPT-IN, AND THAT IS A FIX (2026-09-18). Three defects, all hit in one run
    # while diffing VICTORY_ROAD_B1F, AFTER the grid comparison above had already printed its answer:
    #   1. the default target was a hardcoded `(29, 53)` — the Sootopolis coordinate this probe was
    #      born investigating. B1F is 46x31, so y=53 does not exist and the run ended in a traceback.
    #   2. `except PathFindingError` did not catch it: an out-of-bounds tile raises **IndexError**
    #      from `_get_map_metadata(...).get_tile()`, not a routing error.
    #   3. the argv positions COLLIDED — the usage line documents `<save.ss1> [MAP_NAME]` (argv 1, 2)
    #      while the target was read from argv[2]/argv[3], so naming a map and a target at the same
    #      time fed the map NAME to `int()`.
    # ‼ The damage was not the crash, it was WHERE the crash sat: after the real finding, so the run
    # looked failed when its answer was already correct and complete. A tool that answers and THEN
    # dies teaches the reader to distrust the answer.
    target = None
    if len(sys.argv) > 4:
        try:
            target = (int(sys.argv[3]), int(sys.argv[4]))
        except ValueError:
            print(f"\n  ⚠ ignoring un-parseable target {sys.argv[3]!r} {sys.argv[4]!r} "
                  f"— usage: probe_live_mapgrid.py <save.ss1> [MAP_NAME] [X] [Y]")
    if target is None:
        print("")
        print("  (no target given — skipping the route check. Pass X and Y after the map name to")
        print("   plan a route and see which of the disagreeing tiles it crosses.)")
        return 0
    print("")
    print("=" * 100)
    print(f"DOES THIS EXPLAIN THE JAM? the planned route from {here} to {target}")
    print("=" * 100)
    try:
        path = calculate_path((map_enum, here), (map_enum, target))
    except PathFindingError as error:
        print(f"  NO ROUTE ({error})")
        return 0
    except (IndexError, ValueError) as error:
        # An out-of-bounds tile is a USER error, not a routing result — say so instead of dying.
        print(f"  ⛔ TARGET {target} IS NOT A TILE ON THIS MAP ({type(error).__name__}: {error}).")
        print(f"     The grid comparison above is unaffected and its result stands.")
        return 0
    tiles = [tuple(w.coordinates) for w in path]
    print(f"  {len(path)} waypoints: {tiles}")
    hazards = [t for t in tiles if t in set(worse)]
    print(f"  ⛔ waypoints the GAME calls WALLS: {hazards if hazards else 'NONE'}")
    if hazards:
        first = tiles.index(hazards[0])
        print(f"  ⇒ the first one is waypoint {first} at {hazards[0]}; the bot would jam on the "
              f"tile BEFORE it, i.e. {tiles[first - 1] if first else here}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
