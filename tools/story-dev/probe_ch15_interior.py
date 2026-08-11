"""`#24-magmahideout` increments 2-3 recon: is the INTERIOR route to Maxie walkable?

THE ROUTE UNDER TEST (decomp-verified warp graph, §Ch15). Three warps from the door to 4F:

    JAGGED_PASS (16,18) -> 1F        [arrive 1F (10,34)]
    1F (20,22)          -> 2F_3R     [arrive 2F_3R (16,1)]
    2F_3R (16,13)       -> 3F_3R     [arrive 3F_3R (16,1)]
    3F_3R (16,21)       -> 4F        [arrive 4F (20,21)]
    4F: walk to Maxie at (16,21) and TALK - there is no coord trigger on 4F.

WHAT THIS MEASURES: for each hop, can `calculate_path` walk from the tile we ARRIVE on to the
next warp tile? Plus, on 4F, from the arrival tile to a tile ADJACENT to Maxie.

‼ NEVER NAVIGATE TO A WARP TILE AS A FINAL DESTINATION - walking onto one FIRES it, so the trip
ends a map further on and reports success (08-MISTAKES 2026-08-05). Here the warp tile IS the
intended destination of each leg, which is the one case where targeting it is correct: the leg's
success test is "did the map change", not "are we standing there". This probe measures the walk;
the executor must enter via `_enter_warp_by_navigation`, which tests the map change.

‼‼ AND READ EVERY 'OK' NARROWLY, FOR A REASON THIS CHAPTER JUST PAID FOR. `calculate_path` reads
the ROM's static LAYOUT. Jagged Pass's own door is walled shut at runtime by a `setmetatile` in
`JaggedPass_OnLoad`, and the static planner answered "2 waypoints" for that sealed tile anyway
(§Ch15). So a PASS here means "worth driving"; only the driven run decides. It also cannot see
the Team Magma grunts standing in these corridors - they are live object events.

‼ CONTROLS, because a probe that FAILs everything has found a symptom, not a cause:
  * per-map CONTROL: a short hop from the arrival tile to an adjacent tile, which must plan;
  * the STRENGTH BOULDER check on 1F - `obstacle_clearing.KNOWN_BUT_UNSUPPORTED` excludes
    Strength on purpose (a boulder is PUSHED, not removed, so the success test cannot see it),
    so a route that needs one is a route this bot cannot walk. Reported explicitly rather than
    left to be discovered at f200000.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch15_interior.py
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

SAVES = pathlib.Path(__file__).resolve().parent / "saves"
ANCHOR = "post_mtpyre.ss1"

line = "=" * 88

#: (map, arrival tile, next warp tile, what the next warp leads to)
LEGS = [
    (MapRSE.MAGMA_HIDEOUT_1F, (10, 34), (20, 22), "2F_3R"),
    (MapRSE.MAGMA_HIDEOUT_2F_3R, (16, 1), (16, 13), "3F_3R"),
    (MapRSE.MAGMA_HIDEOUT_3F_3R, (16, 1), (16, 21), "4F"),
]

#: 4F: arrive on the warp at (20,21); Maxie stands at (16,21) facing up. Candidate talk tiles,
#: nearest first - the executor faces him from whichever it can reach.
MAXIE_TILE = (16, 21)
MAXIE_APPROACHES = [(17, 21), (16, 22), (15, 21), (16, 20)]
FOUR_F_ARRIVAL = (20, 21)

#: 1F Strength boulders (decomp `MagmaHideout_1F/map.json`, OBJ_EVENT_GFX_PUSHABLE_BOULDER).
BOULDERS_1F = [(5, 22), (7, 22), (6, 23)]

context.emulator.load_save_state((SAVES / ANCHOR).read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()


def plan(map_enum: MapRSE, start, end) -> str:
    try:
        return f"OK, {len(calculate_path(get_map_data(map_enum, start), get_map_data(map_enum, end)))} waypoints"
    except PathFindingError as error:
        text = str(error)
        return f"FAIL [{'TOPOLOGY' if 'connected maps' in text else 'BLOCKED'}]"
    except Exception as error:  # noqa: BLE001
        return f"FAIL ({type(error).__name__}: {str(error)[:60]})"


def neighbour(tile):
    return (tile[0] + 1, tile[1])


print(line)
print("1. THE THREE WARP HOPS — arrival tile -> the next warp tile")
print(line)
all_ok = True
for map_enum, arrival, warp_tile, leads_to in LEGS:
    control = plan(map_enum, arrival, neighbour(arrival))
    result = plan(map_enum, arrival, warp_tile)
    all_ok = all_ok and result.startswith("OK")
    print(f"  {map_enum.name:<22} {arrival} -> {warp_tile} (-> {leads_to})")
    print(f"  {'':<22}   CONTROL {arrival} -> {neighbour(arrival)}: {control}")
    print(f"  {'':<22}   RESULT : {result}")

print()
print(line)
print("2. MAGMA_HIDEOUT_4F — from the arrival warp to a tile beside Maxie")
print(line)
print(f"  CONTROL {FOUR_F_ARRIVAL} -> {neighbour(FOUR_F_ARRIVAL)}: "
      f"{plan(MapRSE.MAGMA_HIDEOUT_4F, FOUR_F_ARRIVAL, neighbour(FOUR_F_ARRIVAL))}")
best = None
for tile in MAXIE_APPROACHES:
    result = plan(MapRSE.MAGMA_HIDEOUT_4F, FOUR_F_ARRIVAL, tile)
    facing = {
        (17, 21): "Left", (15, 21): "Right", (16, 22): "Up", (16, 20): "Down",
    }[tile]
    if best is None and result.startswith("OK"):
        best = (tile, facing)
    print(f"  {FOUR_F_ARRIVAL} -> {tile} (face {facing} at Maxie {MAXIE_TILE}): {result}")
print(f"  ‼ NEAREST WORKING TALK TILE: {best}")

print()
print(line)
print("3. THE STRENGTH BOULDERS ON 1F — are they on our leg?")
print(line)
print("  Strength is EXCLUDED from obstacle_clearing on purpose (a boulder is pushed, not")
print("  removed, so the success test cannot see it). A route needing one cannot be walked.")
for boulder in BOULDERS_1F:
    reach = plan(MapRSE.MAGMA_HIDEOUT_1F, (10, 34), boulder)
    print(f"  boulder {boulder}: from the 1F arrival {reach}")
print("  ⇒ Our 1F leg is (10,34) -> (20,22): the boulders sit at x=5-7, WEST of the arrival,")
print("    while the leg runs EAST and NORTH. Off-route by inspection; the driven run confirms.")

print()
print(line)
print(f"VERDICT: the three warp hops are {'ALL PLANNABLE' if all_ok else 'NOT all plannable'}"
      f"; 4F talk tile {best}.")
print("‼ Static only. The Jagged Pass door proved a static PASS can be a runtime WALL, and")
print("  live grunts are not modelled here. Grade the chapter on GROUDON_AWAKENED_MAGMA_HIDEOUT.")
print(line)
