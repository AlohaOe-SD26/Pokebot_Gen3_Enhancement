"""MEASUREMENT ONLY. Live-emulator probe for derail #5 in
`_leave_route120_north_bridge()`: `_hold_walk_route([("Up", (13, 15)), ("Left",
(5, 15))], stop_on_script=False)` never reaches (13,15) from the save's actual
load position (13,16).

Reports (per the coordinator's 5-point brief, 2026-07-24):
  1. What map OBJECTS sit on/near (13,15) and (12,16) — is anything occupying
     Steven's own tile?
  2. Tile facts (collision/elevation/tile_type/accessible_from_direction) for
     (13,15), (13,16), (12,15), (14,15).
  3. Does the objects picture change over ~2000 frames of zero input (Steven
     mid-walk-away)?
  4. From a FRESH RELOAD each time: hold Up/Left/Down/Right ~120 frames from
     (13,16) and report resulting coords — what's physically possible?
  5. calculate_path (13,16) -> (5,15) and (13,16) -> (13,15).

Run: py -3.12 tools/story-dev/probe_route120_stevenbridge.py
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


def fresh_emulator():
    context.emulator = LibmgbaEmulator(profile, lambda: None)
    context.audio = False
    context.video = False
    context.emulation_speed = 0
    context.bot_mode = "Story"
    context.emulator.load_save_state(STATE.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()


fresh_emulator()

from modules.map import get_map_data, get_map_objects
from modules.map_data import MapRSE
from modules.map_path import calculate_path, PathFindingError, _find_tile_by_local_coordinates, PathTile
from modules.player import get_player_avatar
from modules.memory import get_event_flag

avatar = get_player_avatar()
actual_map = tuple(avatar.map_group_and_number)
actual_pos = tuple(avatar.local_coordinates)
print("=" * 78)
print("0) ACTUAL LOADED STATE")
print(f"   map_group_and_number={actual_map} ({MapRSE(actual_map).name if actual_map in [m.value for m in MapRSE] else '?'})"
      f"  local_coordinates={actual_pos}  facing={avatar.facing_direction!r}")
print(f"   RECEIVED_DEVON_SCOPE = {bool(get_event_flag('RECEIVED_DEVON_SCOPE'))}")

# ---------------------------------------------------------------------------
# 1) Map objects near (13,15)/(12,16)
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("1) MAP OBJECTS on ROUTE120 (all of them, plus a callout for near-Steven tiles)")
objs = get_map_objects()
print(f"   {len(objs)} live objects on the current map:")
for o in objs:
    try:
        print(f"   local_id={o.local_id:>3} current_coords={tuple(o.current_coords)} "
              f"facing={o.facing_direction} movement_type={o.movement_type} "
              f"graphics_id={o.graphics_id}")
    except Exception as e:
        print(f"   <object read err {type(e).__name__}: {e}>")

for tile in [(13, 15), (12, 16), (13, 16)]:
    occ = [o.local_id for o in objs if tuple(o.current_coords) == tile]
    print(f"   occupant(s) of {tile}: {occ if occ else 'NONE'}")

# object TEMPLATES (static definitions, incl. Steven / BridgeKecleon) near this spot
print("\n   Object TEMPLATES near (13,15)/(12,16) (static map data, not live state):")
md0 = get_map_data(MapRSE.ROUTE120, (0, 0))
for t in md0.objects:
    x, y = t.local_coordinates
    if abs(x - 13) <= 2 and abs(y - 15) <= 2:
        print(f"   template local_id={t.local_id} coords=({x},{y}) script={t.script_symbol} "
              f"flag_id={t.flag_id} movement_type={t.movement_type} graphics_id={t.graphics_id}")

# ---------------------------------------------------------------------------
# 2) Tile facts
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("2) TILE FACTS: (13,15) (13,16) (12,15) (14,15) (5,15)")


def tile_facts(map_enum, coords, label):
    try:
        md = get_map_data(map_enum, coords)
        base = (f"collision={md.collision} elevation={md.elevation} "
                f"tile_type={md.tile_type!r} encounters={md.has_encounters} surfable={md.is_surfable}")
    except Exception as e:
        base = f"<md err {type(e).__name__}: {e}>"
    try:
        pt: PathTile = _find_tile_by_local_coordinates(map_enum, coords)
        extra = (f" accessible_from_direction(N,E,S,W)={pt.accessible_from_direction} "
                 f"warps_to={pt.warps_to} dynamic_object_id={pt.dynamic_object_id} "
                 f"dynamic_collision_flag={pt.dynamic_collision_flag}")
    except Exception as e:
        extra = f" <pathtile err {type(e).__name__}: {e}>"
    print(f"   {label:28} {coords}: {base}{extra}")


for coords, label in [
    ((13, 15), "(13,15) Steven spot"),
    ((13, 16), "(13,16) where we load"),
    ((12, 15), "(12,15) west of Steven"),
    ((14, 15), "(14,15) approach tile"),
    ((5, 15), "(5,15) held-walk target"),
    ((12, 16), "(12,16) BridgeKecleon"),
]:
    tile_facts(MapRSE.ROUTE120, coords, label)

# ---------------------------------------------------------------------------
# 3) Does the objects picture change over time (Steven mid-walk-away)?
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("3) OBJECT POSITIONS OVER ~2000 FRAMES, ZERO INPUT")
checkpoints = [0, 60, 200, 500, 1000, 2000]
last = 0
for cp in checkpoints:
    for _ in range(cp - last):
        context.emulator.run_single_frame()
    last = cp
    objs = get_map_objects()
    pos_avatar = tuple(get_player_avatar().local_coordinates)
    on_steven_tile = [o.local_id for o in objs if tuple(o.current_coords) == (13, 15)]
    print(f"   frame {cp:>5}: player={pos_avatar}  objects={[(o.local_id, tuple(o.current_coords)) for o in objs]}"
          f"  occupant(13,15)={on_steven_tile if on_steven_tile else 'NONE'}")

# ---------------------------------------------------------------------------
# 4) Fresh-reload directional holds from (13,16)
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("4) FRESH-RELOAD DIRECTIONAL HOLDS FROM (13,16), 120 FRAMES EACH")
for direction in ["Up", "Left", "Down", "Right"]:
    fresh_emulator()
    start_pos = tuple(get_player_avatar().local_coordinates)
    context.emulator.reset_held_buttons()
    for _ in range(120):
        context.emulator.hold_button(direction)
        context.emulator.run_single_frame()
    context.emulator.reset_held_buttons()
    for _ in range(10):
        context.emulator.run_single_frame()
    end_pos = tuple(get_player_avatar().local_coordinates)
    end_map = tuple(get_player_avatar().map_group_and_number)
    print(f"   hold {direction:<6} 120f from {start_pos}: -> map={end_map} pos={end_pos}"
          f"  moved={end_pos != start_pos}")

# reload clean state for the remaining path checks
fresh_emulator()

# ---------------------------------------------------------------------------
# 5) calculate_path from (13,16)
# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("5) calculate_path FROM (13,16)")
for label, dst in [
    ("(13,16) -> (5,15) [held-walk final target]", (MapRSE.ROUTE120, (5, 15))),
    ("(13,16) -> (13,15) [Steven's tile]", (MapRSE.ROUTE120, (13, 15))),
]:
    try:
        path = calculate_path((MapRSE.ROUTE120, (13, 16)), dst, avoid_encounters=True, avoid_scripted_events=False)
        print(f"   {label}: SUCCESS, {len(path)} waypoints, "
              f"first 3: {[(w.direction.name, w.coordinates) for w in path[:3]]}")
    except PathFindingError as e:
        print(f"   {label}: PathFindingError: {e}")
    except Exception as e:
        print(f"   {label}: {type(e).__name__}: {e}")

print("\n" + "=" * 78)
print("DONE")
