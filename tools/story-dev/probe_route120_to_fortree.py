"""MEASUREMENT ONLY. Live-emulator probe for the get_devon_scope Fortree-Kecleon-flush
hang: two independent long runs died burning ~16,700 frames spinning
`_navigate_riding_out(MapRSE.FORTREE_CITY, (24, 8), tries=6)` from ROUTE120 (5,15),
where `_leave_route120_north_bridge()` leaves the avatar after Steven's Devon Scope
scene. Hypothesis: ROUTE120 (5,15) -> FORTREE_CITY (24,8) is not plannable by
`calculate_path` (dual-elevation bridge tiles the planner reads as walls), same class
of bug `_hold_walk_route` already works around elsewhere in this file.

Reports:
  1. calculate_path ROUTE120(5,15) -> FORTREE_CITY(24,8): succeeds or exact exception.
     Also from wherever the save actually loads, if different.
  2. Is FORTREE_CITY (24,8) (and neighbours) walkable at all (collision/elevation)?
  3. Sweep of candidate destinations reachable/unreachable from ROUTE120(5,15),
     sampled evenly across each map (not just first-N-from-(0,0)).
  4. If unplannable, search for a 1-2 waypoint bridge that IS plannable end to end.
  5. ROUTE120's real connection data (west/north neighbours).

Run: py -3.12 tools/story-dev/probe_route120_to_fortree.py
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
_BUILD = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(_BUILD))

STATE = _REPO / "tools" / "story-dev" / "saves" / "devon_scope_got.ss1"
assert STATE.is_file(), f"missing state: {STATE}"

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

profile = load_profile_by_name("repro-fresh")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0
context.bot_mode = "Story"
context.emulator.load_save_state(STATE.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()
print(f"[loaded] {STATE}")

from modules.map import get_map_data, get_player_map_object
from modules.map_data import MapRSE
from modules.map_path import calculate_path, PathFindingError
from modules.player import get_player_avatar
from modules.memory import get_event_flag

# ---------------------------------------------------------------------------
# 0) Where did the save actually load?
# ---------------------------------------------------------------------------
print("=" * 78)
print("0) ACTUAL LOADED STATE")
avatar = get_player_avatar()
actual_map = tuple(avatar.map_group_and_number)
actual_pos = tuple(avatar.local_coordinates)
try:
    actual_map_enum = MapRSE(actual_map).name
except ValueError:
    actual_map_enum = f"<unknown {actual_map}>"
print(f"   map_group_and_number={actual_map} ({actual_map_enum})  local_coordinates={actual_pos}")
print(f"   facing={avatar.facing_direction!r}")
try:
    print(f"   RECEIVED_DEVON_SCOPE = {bool(get_event_flag('RECEIVED_DEVON_SCOPE'))}")
except Exception as e:
    print(f"   RECEIVED_DEVON_SCOPE = <err {e}>")

EXPECTED = (MapRSE.ROUTE120.value, (5, 15))
matches_expected = (actual_map == EXPECTED[0] and actual_pos == EXPECTED[1])
print(f"   matches expected ROUTE120 (5,15): {matches_expected}")

SOURCE_CANDIDATES = [("ROUTE120 (5,15) [expected]", (MapRSE.ROUTE120, (5, 15)))]
if not matches_expected:
    SOURCE_CANDIDATES.append((f"{actual_map_enum} {actual_pos} [actual loaded pos]", (actual_map, actual_pos)))

# ---------------------------------------------------------------------------
# 1) calculate_path straight shot(s)
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("1) calculate_path DIRECT: source -> FORTREE_CITY (24, 8)")
DEST = (MapRSE.FORTREE_CITY, (24, 8))
direct_results = {}
for label, src in SOURCE_CANDIDATES:
    try:
        path = calculate_path(src, DEST, avoid_encounters=True, avoid_scripted_events=False)
        print(f"   {label} -> FORTREE_CITY(24,8): SUCCESS, {len(path)} waypoints")
        print(f"      first 3: {[(w.direction.name, w.coordinates) for w in path[:3]]}")
        print(f"      last 3:  {[(w.direction.name, w.coordinates) for w in path[-3:]]}")
        direct_results[label] = True
    except PathFindingError as e:
        print(f"   {label} -> FORTREE_CITY(24,8): PathFindingError: {e}")
        direct_results[label] = False
    except Exception as e:
        print(f"   {label} -> FORTREE_CITY(24,8): {type(e).__name__}: {e}")
        direct_results[label] = False

# ---------------------------------------------------------------------------
# 2) Is the destination tile itself walkable?
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("2) FORTREE_CITY (24,8) AND NEIGHBOURS: walkability (collision/elevation/type)")


def describe_tile(map_enum, coords):
    try:
        md = get_map_data(map_enum, coords)
        return (
            f"collision={md.collision} elevation={md.elevation} "
            f"tile_type={md.tile_type!r} encounters={md.has_encounters} surfable={md.is_surfable}"
        )
    except Exception as e:
        return f"<err {type(e).__name__}: {e}>"


kecleon_obj = None
try:
    for o in __import__("modules.map", fromlist=["get_map_objects"]).get_map_objects():
        pass
except Exception:
    pass
try:
    from modules.map import get_map_objects

    objs = get_map_objects()
    print(f"   live map objects on current map ({actual_map_enum}): "
          f"{[tuple(o.current_coords) for o in objs] if actual_map == MapRSE.FORTREE_CITY.value else '<not currently on FORTREE_CITY, skipped>'}")
except Exception as e:
    print(f"   <object read err {e}>")

for dx, dy, label in [
    (0, 0, "(24,8) DESTINATION"),
    (1, 0, "(25,8) Kecleon spot"),
    (-1, 0, "(23,8) west neighbour"),
    (0, -1, "(24,7) north neighbour"),
    (0, 1, "(24,9) south neighbour"),
]:
    coords = (24 + dx, 8 + dy)
    print(f"   {label:26} {coords}: {describe_tile(MapRSE.FORTREE_CITY, coords)}")

# ---------------------------------------------------------------------------
# 3) Sweep candidate destinations, evenly sampled
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("3) SWEEP: reachability from ROUTE120 (5,15) to a range of candidate tiles")

route120_size = get_map_data(MapRSE.ROUTE120, (0, 0)).map_size
route119_size = get_map_data(MapRSE.ROUTE119, (0, 0)).map_size
fortree_size = get_map_data(MapRSE.FORTREE_CITY, (0, 0)).map_size
print(f"   map sizes: ROUTE120={route120_size} ROUTE119={route119_size} FORTREE_CITY={fortree_size}")


def evenly_spaced(size, n=6, margin=2):
    w, h = size
    xs = sorted({max(margin, min(w - 1 - margin, round(margin + i * (w - 1 - 2 * margin) / max(1, n - 1)))) for i in range(n)})
    ys = sorted({max(margin, min(h - 1 - margin, round(margin + i * (h - 1 - 2 * margin) / max(1, n - 1)))) for i in range(n)})
    return xs, ys


def sweep(map_enum, size, label, n=6):
    xs, ys = evenly_spaced(size, n=n)
    src = (MapRSE.ROUTE120, (5, 15))
    print(f"   --- {label}: {len(xs)}x{len(ys)} evenly spaced sample grid ---")
    ok, fail = [], []
    for y in ys:
        row = []
        for x in xs:
            try:
                calculate_path(src, (map_enum, (x, y)), avoid_encounters=True, avoid_scripted_events=False)
                row.append("OK  ")
                ok.append((x, y))
            except Exception:
                row.append("FAIL")
                fail.append((x, y))
        print(f"   y={y:>3}: " + " ".join(f"x{x}:{v}" for x, v in zip(xs, row)))
    print(f"   {label}: {len(ok)} OK / {len(fail)} FAIL out of {len(ok) + len(fail)} sampled")
    return ok, fail


ok120, fail120 = sweep(MapRSE.ROUTE120, route120_size, "ROUTE120 tiles")
ok119, fail119 = sweep(MapRSE.ROUTE119, route119_size, "ROUTE119 tiles")
okft, failft = sweep(MapRSE.FORTREE_CITY, fortree_size, "FORTREE_CITY tiles")

print("\n   Route 120 / Route 119 exits explicitly named in the code, individually checked:")
named = [
    ("ROUTE120 (13,15) Steven spot", MapRSE.ROUTE120, (13, 15)),
    ("ROUTE120 (14,15) approach", MapRSE.ROUTE120, (14, 15)),
    ("ROUTE120 (13,16) bridge-strand", MapRSE.ROUTE120, (13, 16)),
    ("ROUTE119 (17,34)", MapRSE.ROUTE119, (17, 34)),
    ("FORTREE_CITY (24,8) Kecleon-face", MapRSE.FORTREE_CITY, (24, 8)),
    ("FORTREE_CITY (22,11) gym door", MapRSE.FORTREE_CITY, (22, 11)),
    ("FORTREE_CITY (5,6) FortreeCity const", MapRSE.FORTREE_CITY, (5, 6)),
]
for label, m, t in named:
    try:
        calculate_path((MapRSE.ROUTE120, (5, 15)), (m, t), avoid_encounters=True, avoid_scripted_events=False)
        print(f"   {label:34} {t}: OK")
    except Exception as e:
        print(f"   {label:34} {t}: FAIL ({type(e).__name__}: {e})")

# ---------------------------------------------------------------------------
# 4) If direct fails, find a shortest 1-2 waypoint bridge
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("4) WAYPOINT BRIDGE SEARCH (only meaningful if step 1 failed)")
if all(direct_results.values()):
    print("   SKIPPED: direct path succeeded above, no bridge needed.")
else:
    src = (MapRSE.ROUTE120, (5, 15))
    # Candidate intermediate waypoints: everything that tested OK in the sweep,
    # tried in both legs (src->A succeeds AND A->dest succeeds).
    candidates = [(MapRSE.ROUTE120, xy) for xy in ok120] + \
                 [(MapRSE.ROUTE119, xy) for xy in ok119] + \
                 [(MapRSE.FORTREE_CITY, xy) for xy in okft]
    found = None
    for m, xy in candidates:
        try:
            calculate_path(src, (m, xy), avoid_encounters=True, avoid_scripted_events=False)
            calculate_path((m, xy), DEST, avoid_encounters=True, avoid_scripted_events=False)
            found = (m, xy)
            break
        except Exception:
            continue
    if found:
        m, xy = found
        print(f"   ONE-HOP bridge found: ROUTE120(5,15) -> {m.name}{xy} -> FORTREE_CITY(24,8)")
    else:
        print("   No one-hop bridge found among sampled OK tiles; trying named landmark tiles as hops.")
        for label, m, t in named:
            try:
                calculate_path(src, (m, t), avoid_encounters=True, avoid_scripted_events=False)
                calculate_path((m, t), DEST, avoid_encounters=True, avoid_scripted_events=False)
                print(f"   ONE-HOP bridge found via named tile: ROUTE120(5,15) -> {label} {t} -> FORTREE_CITY(24,8)")
                found = (m, t)
                break
            except Exception:
                continue
        if not found:
            print("   No one-hop bridge found via named landmarks either. A two-hop search would be needed"
                  " (not run automatically here — report as UNPROVEN bridge, needs manual waypoint hunting).")

# ---------------------------------------------------------------------------
# 5) ROUTE120's real connection data
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("5) ROUTE120 CONNECTIONS (real map header data)")
r120 = get_map_data(MapRSE.ROUTE120, (5, 15))
for c in r120.connections:
    try:
        dest_name = MapRSE((c.destination_map_group, c.destination_map_number)).name
    except ValueError:
        dest_name = f"<unknown {(c.destination_map_group, c.destination_map_number)}>"
    print(f"   {c.direction:>6} -> {dest_name} (offset={c.offset})")

print("\n" + "=" * 78)
print("6) FORTREE GYM DOOR (22,11) — same-class-of-bug check, after the (24,8) fix")
print("   (coordinator applied the Kecleon-flush fix: destination now FORTREE_CITY(25,7)")
print("    facing Down. Checking the very next leg: _navigate_riding_out(FORTREE_CITY,")
print("    (22,11), tries=6, label='Fortree Gym door').)")

from modules.map_path import _find_tile_by_local_coordinates, PathTile

DIRS = ["North", "East", "South", "West"]


def tile_facts(map_enum, coords, label):
    md = describe_tile(map_enum, coords)
    print(f"   {label:26} {coords}: {md}")
    try:
        pt: PathTile = _find_tile_by_local_coordinates(map_enum, coords)
        print(f"      accessible_from_direction (N,E,S,W)={pt.accessible_from_direction}  "
              f"warps_to={pt.warps_to}  dynamic_object_id={pt.dynamic_object_id}  "
              f"dynamic_collision_flag={pt.dynamic_collision_flag}")
    except Exception as e:
        print(f"      <pathtile err {type(e).__name__}: {e}>")


print("\n   6.1) (22,11) itself + neighbours: collision/elevation/tile_type/accessibility")
for dx, dy, label in [
    (0, 0, "(22,11) GYM DOOR"),
    (-1, 0, "(21,11) west neighbour"),
    (0, 1, "(22,12) south neighbour"),
    (1, 0, "(23,11) east neighbour"),
    (0, -1, "(22,10) north neighbour"),
]:
    tile_facts(MapRSE.FORTREE_CITY, (22 + dx, 11 + dy), label)

print("\n   6.2) is (22,11) a WARP tile? (raw map warp list, FORTREE_CITY)")
fortree_at_door = get_map_data(MapRSE.FORTREE_CITY, (22, 11))
door_warps = [w for w in fortree_at_door.warps if w.local_coordinates == (22, 11)]
if door_warps:
    for w in door_warps:
        try:
            dest_name = MapRSE((w.destination_map_group, w.destination_map_number)).name
        except ValueError:
            dest_name = f"<unknown {(w.destination_map_group, w.destination_map_number)}>"
        dest_loc = w.destination_location
        print(f"      WARP at (22,11) elevation={w.elevation} -> {dest_name} "
              f"warp_id={w.destination_warp_id} landing_local_position={dest_loc.local_position}")
else:
    print("      NOT a warp tile per the map's warp event list (no MapWarp at (22,11)).")
print("      All FORTREE_CITY warps near the gym (door search x=18-26,y=9-13):")
for w in fortree_at_door.warps:
    x, y = w.local_coordinates
    if 18 <= x <= 26 and 9 <= y <= 13:
        try:
            dest_name = MapRSE((w.destination_map_group, w.destination_map_number)).name
        except ValueError:
            dest_name = f"<unknown>"
        print(f"        warp @ {w.local_coordinates} elevation={w.elevation} -> {dest_name} "
              f"warp_id={w.destination_warp_id}")

print("\n   6.3) calculate_path to (22,11) from the two relevant sources")
GYM_DOOR = (MapRSE.FORTREE_CITY, (22, 11))
for label, src in [
    ("FORTREE_CITY (25,7) [post-Kecleon-flush stand tile]", (MapRSE.FORTREE_CITY, (25, 7))),
    ("ROUTE120 (5,15)", (MapRSE.ROUTE120, (5, 15))),
]:
    try:
        path = calculate_path(src, GYM_DOOR, avoid_encounters=True, avoid_scripted_events=False)
        print(f"      {label} -> (22,11): SUCCESS, {len(path)} waypoints, "
              f"last 3: {[(w.direction.name, w.coordinates, w.is_warp) for w in path[-3:]]}")
    except Exception as e:
        print(f"      {label} -> (22,11): FAIL ({type(e).__name__}: {e})")

print("\n   6.4) if (22,11) itself doesn't plan, do its neighbours (from (25,7))?")
for label, coords in [("(21,11)", (21, 11)), ("(22,12)", (22, 12)), ("(23,11)", (23, 11)), ("(22,10)", (22, 10))]:
    try:
        calculate_path((MapRSE.FORTREE_CITY, (25, 7)), (MapRSE.FORTREE_CITY, coords),
                        avoid_encounters=True, avoid_scripted_events=False)
        print(f"      (25,7) -> {label}: OK")
    except Exception as e:
        print(f"      (25,7) -> {label}: FAIL ({type(e).__name__})")

print("\n" + "=" * 78)
print("7) IS THE (22,11) FAILURE PERMANENT (like 24,8) OR JUST A STORY PRECONDITION?")
print("   This save (devon_scope_got.ss1) predates the gym-path Kecleon flush, so the")
print("   walkway chokepoint at (25,8) is still gated by its object's `flag_id`. Read")
print("   that flag straight off the map's object template (not guessed), then fault-")
print("   inject it True (reader-level, restored after) to simulate 'already flushed'")
print("   -- exactly the state get_devon_scope guarantees before do_fortree_gym runs.")

import modules.map_path as _map_path_mod

fortree0 = get_map_data(MapRSE.FORTREE_CITY, (0, 0))
kecleon_obj = next((o for o in fortree0.objects if tuple(o.local_coordinates) == (25, 8)), None)
if kecleon_obj is None:
    print("   <no object template at (25,8) found -- cannot fault-inject, reporting raw only>")
else:
    flag_num = kecleon_obj.flag_id
    from modules.memory import get_event_flag_by_number
    try:
        from modules.data.event_flags import get_event_flag_name  # may not exist; best effort
        flag_name = get_event_flag_name(flag_num)
    except Exception:
        flag_name = None
    print(f"   Kecleon object template @ (25,8): local_id={kecleon_obj.local_id} flag_id={flag_num}"
          f"{f' ({flag_name})' if flag_name else ''}")
    print(f"   current get_event_flag_by_number({flag_num}) = {get_event_flag_by_number(flag_num)}  "
          f"(False = not yet flushed, matches this save's story position)")

    checks = [
        ("(25,7) [post-flush stand tile] -> (22,11) door", (MapRSE.FORTREE_CITY, (25, 7)), (MapRSE.FORTREE_CITY, (22, 11))),
        ("(5,6) plaza -> (22,11) door", (MapRSE.FORTREE_CITY, (5, 6)), (MapRSE.FORTREE_CITY, (22, 11))),
        ("ROUTE120 (5,15) -> (22,11) door", (MapRSE.ROUTE120, (5, 15)), (MapRSE.FORTREE_CITY, (22, 11))),
    ]
    print("\n   BEFORE (flag as-loaded, Kecleon still standing):")
    for label, src, dst in checks:
        try:
            calculate_path(src, dst, avoid_encounters=True, avoid_scripted_events=False)
            print(f"      {label}: OK")
        except Exception as e:
            print(f"      {label}: FAIL ({type(e).__name__})")

    _orig_reader = _map_path_mod.get_event_flag_by_number
    _map_path_mod.get_event_flag_by_number = lambda n: True if n == flag_num else _orig_reader(n)
    _map_path_mod._maps.clear()
    print(f"\n   AFTER (fault-injected flag {flag_num} = True, simulating post-flush):")
    for label, src, dst in checks:
        try:
            path = calculate_path(src, dst, avoid_encounters=True, avoid_scripted_events=False)
            print(f"      {label}: OK ({len(path)} waypoints)")
        except Exception as e:
            print(f"      {label}: FAIL ({type(e).__name__}: {e})")
    _map_path_mod.get_event_flag_by_number = _orig_reader
    _map_path_mod._maps.clear()

print("\n" + "=" * 78)
print("DONE")
