"""§Ch21 — MEASURE the ROUTE128 -> dive -> UNDERWATER_ROUTE128 -> SEAFLOOR_CAVERN topology.

Everything printed here comes from OUR OWN ROM/map data (`modules.map.get_map_data`,
`modules.map.get_map_all_tiles`, `modules.map_path.calculate_path`) — nothing from recall.

Follows the shape of `probe_dive_routing.py` (same anchor + same imports).

Questions answered:
  1. Which ROUTE128 tiles are dive-capable? (the exact tile-type set `dive()` accepts,
     `modules/modes/util/higher_level_actions.py:693-697`)
  2. Where does UNDERWATER_ROUTE128 warp into the SEAFLOOR CAVERN, and what does
     UNDERWATER_SEAFLOOR_CAVERN warp back to? (KI-68 recorded `(6,7) -> UNDERWATER_ROUTE128`)
  3. Does a dive land on the SAME (x,y)? — answered from the map CONNECTION table
     (`MapConnection.direction == "Dive"/"Emerge"`, `modules/map.py:481-500`) not from assumption.
  4. Can `calculate_path` route WITHIN UNDERWATER_ROUTE128 from the landing tile to the warp tile?
  5. KI-59: how many `Impassable *` tiles are on UNDERWATER_ROUTE128 / SEAFLOOR_CAVERN_ROOM1, and
     do any sit on the route found in (4)?

CONTROLS (so a null result is attributable):
  * POSITIVE — a 1-step `calculate_path` on UNDERWATER_ROUTE128 between two adjacent open tiles.
    If that succeeds, the pathfinder + map metadata for this map work, and any failure in (4) is
    about the ROUTE, not about the harness.
  * NEGATIVE — a `calculate_path` into a known-blocked (collision != 0) tile, expected to raise.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch21_topology.py
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data, get_map_objects
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar

BAR = "=" * 100

# The exact set `dive()` accepts — copied from higher_level_actions.py:693-697, not invented.
DIVE_TILE_TYPES = ("Deep Water", "Interior Deep Water", "Semi-Deep Water", "Sootopolis Deep Water")


def head(title: str) -> None:
    print(f"\n{BAR}\n{title}\n{BAR}\n")


def scan(map_enum: MapRSE) -> list:
    """Every tile of a map, read through the normal reader."""
    return get_map_all_tiles(get_map_data(map_enum, (0, 0)))


avatar = get_player_avatar()
print("anchor: post_dive.ss1")
print(
    f"avatar: {MapRSE(tuple(avatar.map_group_and_number)).name} "
    f"{tuple(avatar.local_coordinates)}   (‼ asserted, not assumed — KI-60)"
)
print(f"live map objects loaded (these become blocked_coordinates in calculate_path): {len(get_map_objects())}")

# =================================================================================================
head("1 — ROUTE128: which tiles are DIVE-CAPABLE?")

r128_head = get_map_data(MapRSE.ROUTE128, (0, 0))
print(f"  ROUTE128 map_size = {r128_head.map_size}  (width, height)")
r128 = scan(MapRSE.ROUTE128)
print(f"  tiles read        = {len(r128)}")

types: dict[str, int] = {}
for t in r128:
    types[t.tile_type] = types.get(t.tile_type, 0) + 1
print("\n  tile-type histogram (all of ROUTE128):")
for name, count in sorted(types.items(), key=lambda kv: -kv[1]):
    print(f"      {count:5d}  {name}")

dive_tiles = [t for t in r128 if t.tile_type in DIVE_TILE_TYPES]
print(f"\n  DIVE-CAPABLE tiles (tile_type in {DIVE_TILE_TYPES}): {len(dive_tiles)}")
by_type: dict[str, list] = {}
for t in dive_tiles:
    by_type.setdefault(t.tile_type, []).append(tuple(t.local_position))
for name, coords in by_type.items():
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    print(f"\n    {name}: {len(coords)} tiles, x {min(xs)}..{max(xs)}, y {min(ys)}..{max(ys)}")
    for i in range(0, len(coords), 12):
        print("        " + " ".join(f"({x:2d},{y:2d})" for x, y in coords[i : i + 12]))

# =================================================================================================
head("2 — THE MAP CONNECTION TABLE: is the dive a same-coordinate transition?")

for label, enum in (("ROUTE128", MapRSE.ROUTE128), ("UNDERWATER_ROUTE128", MapRSE.UNDERWATER_ROUTE128)):
    data = get_map_data(enum, (0, 0))
    print(f"  {label}  size={data.map_size}  connections:")
    for c in data.connections:
        try:
            dest = MapRSE((c.destination_map_group, c.destination_map_number)).name
        except ValueError:
            dest = f"({c.destination_map_group},{c.destination_map_number})"
        print(f"      direction={c.direction:<8} offset={c.offset:<5} -> {dest}")
    print()

print("  ‼ A 'Dive'/'Emerge' connection carries NO coordinate remap — only an `offset` field that")
print("    the game ignores for dive warps (`SetWarpDestinationToDiveWarp` keeps the player's x/y).")
print("    So the landing tile is the SAME (x,y) IF the two maps are the same size. Measured below.")

r128_size = get_map_data(MapRSE.ROUTE128, (0, 0)).map_size
u128_head = get_map_data(MapRSE.UNDERWATER_ROUTE128, (0, 0))
u128_size = u128_head.map_size
print(f"\n  ROUTE128 size            = {r128_size}")
print(f"  UNDERWATER_ROUTE128 size = {u128_size}")
print(f"  SAME SIZE                = {r128_size == u128_size}")

# =================================================================================================
head("3 — UNDERWATER_ROUTE128: every warp, and the reverse direction from the cavern")

u128 = scan(MapRSE.UNDERWATER_ROUTE128)
u_types: dict[str, int] = {}
for t in u128:
    u_types[t.tile_type] = u_types.get(t.tile_type, 0) + 1
print(f"  tiles read = {len(u128)}")
print("  tile-type histogram:")
for name, count in sorted(u_types.items(), key=lambda kv: -kv[1]):
    print(f"      {count:5d}  {name}")

print("\n  WARPS ON UNDERWATER_ROUTE128:")
u128_warps = []
for w in u128_head.warps:
    try:
        dest = MapRSE((w.destination_map_group, w.destination_map_number)).name
    except ValueError:
        dest = f"({w.destination_map_group},{w.destination_map_number})"
    coords = tuple(w.local_coordinates)
    u128_warps.append((coords, dest, w.destination_warp_id))
    tile = get_map_data(MapRSE.UNDERWATER_ROUTE128, coords)
    print(
        f"      {coords} -> {dest} (dest warp id {w.destination_warp_id})   "
        f"tile_type={tile.tile_type!r} collision={tile.collision} elevation={tile.elevation}"
    )
if not u128_warps:
    print("      <NONE>")

for label, enum in (
    ("UNDERWATER_SEAFLOOR_CAVERN", MapRSE.UNDERWATER_SEAFLOOR_CAVERN),
    ("SEAFLOOR_CAVERN_ENTRANCE", MapRSE.SEAFLOOR_CAVERN_ENTRANCE),
    ("SEAFLOOR_CAVERN_ROOM1", MapRSE.SEAFLOOR_CAVERN_ROOM1),
):
    data = get_map_data(enum, (0, 0))
    print(f"\n  WARPS ON {label} (size={data.map_size}):")
    for w in data.warps:
        try:
            dest = MapRSE((w.destination_map_group, w.destination_map_number)).name
        except ValueError:
            dest = f"({w.destination_map_group},{w.destination_map_number})"
        tile = get_map_data(enum, tuple(w.local_coordinates))
        print(
            f"      {tuple(w.local_coordinates)} -> {dest} (dest warp id {w.destination_warp_id})   "
            f"tile_type={tile.tile_type!r} collision={tile.collision}"
        )
    print(f"    connections: {[(c.direction, c.offset) for c in data.connections] or 'NONE'}")

print("\n  ‼ KI-68 CLAIM UNDER TEST: 'UNDERWATER_SEAFLOOR_CAVERN (6,7) -> UNDERWATER_ROUTE128'")
usc = get_map_data(MapRSE.UNDERWATER_SEAFLOOR_CAVERN, (0, 0))
claim_hits = [
    w
    for w in usc.warps
    if tuple(w.local_coordinates) == (6, 7)
    and (w.destination_map_group, w.destination_map_number) == MapRSE.UNDERWATER_ROUTE128.value
]
print(f"    warps at (6,7) going to UNDERWATER_ROUTE128 : {len(claim_hits)}  -> "
      f"{'CONFIRMED' if claim_hits else 'REFUTED'}")

# The reverse: which UNDERWATER_ROUTE128 tile leads INTO the cavern?
cavern_group = MapRSE.UNDERWATER_SEAFLOOR_CAVERN.value
into_cavern = [
    (tuple(w.local_coordinates), w.destination_warp_id)
    for w in u128_head.warps
    if (w.destination_map_group, w.destination_map_number) == cavern_group
]
print(f"\n    REVERSE — UNDERWATER_ROUTE128 tiles warping into UNDERWATER_SEAFLOOR_CAVERN: {into_cavern or 'NONE'}")

# =================================================================================================
head("4 — THE LANDING TILE: is it the same (x,y), and is it usable?")

print("  For each dive-capable ROUTE128 tile, what is at the SAME (x,y) on UNDERWATER_ROUTE128?")
landing_ok = []
for t in dive_tiles:
    x, y = tuple(t.local_position)
    if x >= u128_size[0] or y >= u128_size[1]:
        print(f"      ({x:2d},{y:2d}) surface={t.tile_type:<16} -> OUT OF BOUNDS underwater")
        continue
    u = get_map_data(MapRSE.UNDERWATER_ROUTE128, (x, y))
    ok = u.collision == 0
    if ok:
        landing_ok.append((x, y))
    print(
        f"      ({x:2d},{y:2d}) surface={t.tile_type:<16} -> underwater tile_type={u.tile_type!r:<28} "
        f"collision={u.collision} elevation={u.elevation}  {'USABLE' if ok else 'BLOCKED'}"
    )
print(f"\n  landing tiles that are NOT blocked underwater: {len(landing_ok)} / {len(dive_tiles)}")

# =================================================================================================
head("5 — CONTROLS")

control_a = control_b = None
if landing_ok:
    lx, ly = landing_ok[0]
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = lx + dx, ly + dy
        if 0 <= nx < u128_size[0] and 0 <= ny < u128_size[1]:
            n = get_map_data(MapRSE.UNDERWATER_ROUTE128, (nx, ny))
            if n.collision == 0:
                control_a, control_b = (lx, ly), (nx, ny)
                break

if control_a is None:
    print("  POSITIVE CONTROL: could not be constructed (no usable landing tile) — see section 4.")
else:
    print(f"  POSITIVE CONTROL: calculate_path UNDERWATER_ROUTE128 {control_a} -> {control_b} (adjacent, open)")
    try:
        p = calculate_path((MapRSE.UNDERWATER_ROUTE128, control_a), (MapRSE.UNDERWATER_ROUTE128, control_b))
        print(f"      RESULT: OK, {len(p)} waypoint(s) -> {[(w.coordinates) for w in p]}")
    except Exception as error:  # noqa: BLE001 - the exception IS the result
        print(f"      RESULT: ‼ FAILED — {type(error).__name__}: {error}")

blocked = next((t for t in u128 if t.collision != 0), None)
if blocked is None:
    print("\n  NEGATIVE CONTROL: no collision!=0 tile exists on UNDERWATER_ROUTE128 — control skipped.")
elif control_a is not None:
    bc = tuple(blocked.local_position)
    print(f"\n  NEGATIVE CONTROL: calculate_path {control_a} -> {bc} (collision={blocked.collision}) — expect a raise")
    try:
        p = calculate_path((MapRSE.UNDERWATER_ROUTE128, control_a), (MapRSE.UNDERWATER_ROUTE128, bc))
        print(f"      RESULT: ‼ UNEXPECTEDLY OK, {len(p)} waypoint(s)")
    except Exception as error:  # noqa: BLE001
        print(f"      RESULT: raised as expected — {type(error).__name__}: {error}")

# =================================================================================================
head("6 — THE REAL QUESTION: can calculate_path route landing tile -> cavern warp tile?")

routes: dict[tuple, list] = {}
if not into_cavern:
    print("  ‼ No UNDERWATER_ROUTE128 warp into UNDERWATER_SEAFLOOR_CAVERN was found in section 3.")
    print("    Cannot be determined from data — nothing to route to.")
else:
    target = into_cavern[0][0]
    print(f"  destination = UNDERWATER_ROUTE128 {target} (the warp into the cavern)\n")
    for src in landing_ok:
        try:
            path = calculate_path((MapRSE.UNDERWATER_ROUTE128, src), (MapRSE.UNDERWATER_ROUTE128, target))
            routes[src] = path
            print(f"      {src} -> {target}: OK, {len(path)} waypoints")
        except PathFindingError as error:
            print(f"      {src} -> {target}: PathFindingError: {error}")
        except Exception as error:  # noqa: BLE001
            print(f"      {src} -> {target}: {type(error).__name__}: {error}")
    if not routes:
        print("\n  ‼ NO landing tile could route to the cavern warp.")

# =================================================================================================
head("7 — KI-59: `Impassable *` tiles, and do they sit on the route?")

for label, enum in (
    ("UNDERWATER_ROUTE128", MapRSE.UNDERWATER_ROUTE128),
    ("SEAFLOOR_CAVERN_ROOM1", MapRSE.SEAFLOOR_CAVERN_ROOM1),
):
    tiles = scan(enum)
    imp = [t for t in tiles if t.tile_type.startswith("Impassable ")]
    print(f"  {label}: {len(imp)} `Impassable *` tiles out of {len(tiles)}")
    kinds: dict[str, int] = {}
    for t in imp:
        kinds[t.tile_type] = kinds.get(t.tile_type, 0) + 1
    for name, count in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"      {count:4d}  {name}")
    if enum is MapRSE.UNDERWATER_ROUTE128:
        imp_coords = {tuple(t.local_position) for t in imp}
        if routes:
            for src, path in routes.items():
                on_route = [w.coordinates for w in path if tuple(w.coordinates) in imp_coords]
                print(f"      route from {src}: {len(path)} waypoints, {len(on_route)} on Impassable tiles {on_route}")
        else:
            print("      (no route found, so 'on the route' cannot be evaluated)")
    print()

# =================================================================================================
head("8 — RAW WARP RECORDS + the reverse question: what warps INTO the cavern maps?")

print("  ‼ Section 3 resolved warp destinations through `MapRSE(...)`. Here are the RAW group/number")
print("    bytes and the ARRIVAL tile (`MapWarp.destination_location`, map.py:551-570), so the")
print("    'both maps say UNDERWATER_ROUTE128' result cannot be a name-lookup artifact.\n")

for label, enum in (
    ("UNDERWATER_ROUTE128", MapRSE.UNDERWATER_ROUTE128),
    ("UNDERWATER_SEAFLOOR_CAVERN", MapRSE.UNDERWATER_SEAFLOOR_CAVERN),
    ("SEAFLOOR_CAVERN_ENTRANCE", MapRSE.SEAFLOOR_CAVERN_ENTRANCE),
):
    data = get_map_data(enum, (0, 0))
    print(f"  {label} (enum value {enum.value}):")
    for i, w in enumerate(data.warps):
        arrival = w.destination_location
        try:
            arrival_name = MapRSE((arrival.map_group, arrival.map_number)).name
        except ValueError:
            arrival_name = "?"
        print(
            f"      warp[{i}] at {tuple(w.local_coordinates)} elev={w.elevation} -> raw dest "
            f"group={w.destination_map_group} number={w.destination_map_number} "
            f"warp_id={w.destination_warp_id}  ARRIVES {arrival_name} {tuple(arrival.local_position)}"
        )
    print()

print("  REVERSE SCAN — every map in MapRSE whose warps point at the cavern maps:")
wanted = {
    MapRSE.UNDERWATER_SEAFLOOR_CAVERN.value: "UNDERWATER_SEAFLOOR_CAVERN",
    MapRSE.SEAFLOOR_CAVERN_ENTRANCE.value: "SEAFLOOR_CAVERN_ENTRANCE",
}
found_any = False
for candidate in MapRSE:
    try:
        data = get_map_data(candidate, (0, 0))
    except Exception:  # noqa: BLE001 - unreadable maps are not the subject here
        continue
    for w in data.warps:
        key = (w.destination_map_group, w.destination_map_number)
        if key in wanted:
            found_any = True
            print(f"      {candidate.name} {tuple(w.local_coordinates)} -> {wanted[key]} (warp id {w.destination_warp_id})")
if not found_any:
    print("      <NONE>")

print("\n  Connections on the cavern maps (a 'Dive'/'Emerge' connection is the OTHER way in/out):")
for label, enum in (
    ("UNDERWATER_SEAFLOOR_CAVERN", MapRSE.UNDERWATER_SEAFLOOR_CAVERN),
    ("SEAFLOOR_CAVERN_ENTRANCE", MapRSE.SEAFLOOR_CAVERN_ENTRANCE),
):
    data = get_map_data(enum, (0, 0))
    conns = []
    for c in data.connections:
        try:
            dest = MapRSE((c.destination_map_group, c.destination_map_number)).name
        except ValueError:
            dest = f"({c.destination_map_group},{c.destination_map_number})"
        conns.append((c.direction, c.offset, dest))
    print(f"      {label}: {conns or 'NONE'}")

# =================================================================================================
head("9 — ‼ THE LAST LEG: how does UNDERWATER_SEAFLOOR_CAVERN reach SEAFLOOR_CAVERN_ENTRANCE?")

print("  Section 8 found NO warp and NO connection from UNDERWATER_SEAFLOOR_CAVERN into the")
print("  ENTRANCE map. If that leg exists in the data at all it must be a tile behaviour or an")
print("  event, so both are dumped here rather than guessed at.\n")

usc_tiles = scan(MapRSE.UNDERWATER_SEAFLOOR_CAVERN)
usc_types: dict[str, int] = {}
for t in usc_tiles:
    usc_types[t.tile_type] = usc_types.get(t.tile_type, 0) + 1
print(f"  UNDERWATER_SEAFLOOR_CAVERN tile-type histogram ({len(usc_tiles)} tiles):")
for name, count in sorted(usc_types.items(), key=lambda kv: -kv[1]):
    print(f"      {count:4d}  {name}")
print("\n  non-'Normal' tiles, with coordinates:")
for t in usc_tiles:
    if t.tile_type != "Normal":
        print(f"      {tuple(t.local_position)} {t.tile_type!r} collision={t.collision} elevation={t.elevation}")

for label, enum in (
    ("UNDERWATER_SEAFLOOR_CAVERN", MapRSE.UNDERWATER_SEAFLOOR_CAVERN),
    ("SEAFLOOR_CAVERN_ENTRANCE", MapRSE.SEAFLOOR_CAVERN_ENTRANCE),
):
    data = get_map_data(enum, (0, 0))
    print(f"\n  {label} coord_events: {[(tuple(e.local_coordinates), e.type) for e in data.coord_events] or 'NONE'}")
    print(f"  {label} bg_events   : {[(tuple(e.local_coordinates), e.type) for e in data.bg_events] or 'NONE'}")

ent_tiles = scan(MapRSE.SEAFLOOR_CAVERN_ENTRANCE)
ent_water = [t for t in ent_tiles if "Water" in t.tile_type]
print(f"\n  SEAFLOOR_CAVERN_ENTRANCE water tiles ({len(ent_water)}):")
for t in ent_water:
    print(f"      {tuple(t.local_position)} {t.tile_type!r} collision={t.collision} elevation={t.elevation}")

head("VERDICT (data only — nothing here is a driven run)")
print(f"  dive-capable ROUTE128 tiles                : {len(dive_tiles)}")
print(f"  ROUTE128 / UNDERWATER_ROUTE128 same size   : {r128_size == u128_size}")
print(f"  UNDERWATER_ROUTE128 -> cavern warp tile(s) : {into_cavern or 'NONE'}")
print(f"  landing tiles usable underwater            : {len(landing_ok)} / {len(dive_tiles)}")
print(f"  landing tiles that route to the warp       : {len(routes)}")
print("\n‼ STATIC. This proves what the DATA says. It does not prove a driven run works.")
