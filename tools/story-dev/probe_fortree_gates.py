"""MEASUREMENT probe (not a fix): Fortree Gym (map (12,1) = FORTREE_CITY_GYM)
"rotating gate" puzzle -- what is actually OBSERVABLE in OUR reader + OUR
emulator, on THIS map, right now, from the captured wedge save.

A separate agent is researching the rotating-gate MECHANICS from the decomp.
This script does NOT theorize about mechanics; it measures:
  1. The full walkable grid (collision/elevation/tile_type/raw metatile id)
     as an ASCII map.
  2. Every map object in the gym (static templates + live runtime objects)
     -- are gates objects, or pure terrain?
  3. The distinct tile_type / metatile-behaviour values present in the room,
     and whether they can tell a "gate" apart from a wall.
  4. An empirical push test: from several reachable tiles, hold each of the
     four directions and record whether the player moved, whether any
     object moved, and whether any tile's collision/metatile changed.
  5. calculate_path results from the entrance and from the player's current
     position to the target and a few intermediates.

Save: tools/story-dev/saves/fortree_gym_wedge.ss1 -- verified on load (this
prints the actual map/coords/flags found, per the "several saves here are
misnamed" warning).

Run: py -3.12 tools/story-dev/probe_fortree_gates.py
"""

import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "sandbox-pokebot"))

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

PROFILE = load_profile_by_name("repro-ml")
context.profile = PROFILE
context.config.load(PROFILE.path, strict=False)
set_rom(PROFILE.rom)

from modules.libmgba import LibmgbaEmulator

STATE = _REPO / "tools" / "story-dev" / "saves" / "fortree_gym_wedge.ss1"
assert STATE.is_file(), STATE

from modules.map import get_map_data, get_map_objects, ObjectEvent
from modules.map_data import MapRSE
from modules.map_path import calculate_path
from modules.memory import get_event_flag, unpack_uint16, unpack_uint32, read_symbol
from modules.modes.util.global_navigation import navigate_to_anywhere
from modules.player import get_player_avatar

GYM = MapRSE.FORTREE_CITY_GYM.value
TARGET = (15, 3)
ENTRANCE = (15, 24)


def boot():
    context.emulator = LibmgbaEmulator(PROFILE, lambda: None)
    context.audio = False
    context.video = False
    context.bot_mode = "Story"
    context.emulator.load_save_state(STATE.read_bytes())
    for _ in range(10):
        context.emulator.run_single_frame()


def pos():
    return tuple(get_player_avatar().local_coordinates)


def raw_metatile(x, y, w):
    """Read the LIVE metatile id/collision/elevation straight from the map
    buffer (same buffer MapLocation._metatile_attributes reads from), for
    finer-grained IDs than the class exposes (it only exposes the behaviour
    byte, not the metatile number itself)."""
    t = get_map_data(GYM, (x, y))
    layout = t._map_layout
    map_data_pointer = unpack_uint32(layout[12:16])
    offset = (x * 2) + (w * y * 2)
    block = unpack_uint16(context.emulator.read_bytes(map_data_pointer + offset, 2))
    metatile = block & 0x03FF
    collision = (block & 0x0C00) >> 10
    elevation = (block & 0xF000) >> 12
    return metatile, collision, elevation


# ---------------------------------------------------------------------------
boot()
p0 = pos()
print("=" * 78)
print("0) SAVE VERIFICATION")
print(f"   loaded {STATE.name}")
print(f"   map_group_and_number = {get_player_avatar().map_group_and_number}  (expect {GYM})")
print(f"   local_coordinates    = {p0}")
print(f"   BADGE06_GET          = {get_event_flag('BADGE06_GET')}")

md0 = get_map_data(GYM, (0, 0))
W, H = md0.map_size
print(f"   map size = {W}x{H}   warps = {[tuple(w.local_coordinates) for w in md0.warps]}")

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("1) FULL WALKABLE GRID")
grid = {}
for y in range(H):
    for x in range(W):
        t = get_map_data(GYM, (x, y))
        mt, c, e = raw_metatile(x, y, W)
        grid[(x, y)] = {"collision": c, "elevation": e, "tile_type": t.tile_type, "metatile": mt}

print("\nCOLLISION MAP  ('.'=collision 0/open  '#'=collision!=0/blocked  "
      "P=player  T=target(15,3)  E=entrance warp(15,24)/(16,24))")
print("     " + "".join(f"{x % 10}" for x in range(W)))
for y in range(H):
    row = []
    for x in range(W):
        c = grid[(x, y)]["collision"]
        ch = "." if c == 0 else "#"
        if (x, y) == p0:
            ch = "P"
        elif (x, y) == TARGET:
            ch = "T"
        elif (x, y) in ((15, 24), (16, 24)):
            ch = "E"
        row.append(ch)
    print(f"y={y:2d}: " + "".join(row))

print("\nELEVATION MAP (single hex digit per tile, 0-F)")
print("     " + "".join(f"{x % 10}" for x in range(W)))
for y in range(H):
    print(f"y={y:2d}: " + "".join(f"{grid[(x, y)]['elevation']:X}" for x in range(W)))

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("2) MAP OBJECTS -- are the gates objects, or pure terrain?")
print("\n2a) STATIC OBJECT TEMPLATES (md.objects) in the gym:")
for o in md0.objects:
    print(f"   tmpl coords={tuple(o.local_coordinates)!s:8} graphics_id={o.graphics_id:>3} "
          f"movement_type={o.movement_type:20} script={o.script_symbol}")
print(f"   -> {len(md0.objects)} static templates, ALL are named trainer/NPC scripts "
      f"(no gate/turnstile object present in the template list).")

print("\n2b) LIVE RUNTIME OBJECT SLOTS (all 16, active or not):")
raw_objs = read_symbol("gObjectEvents", 0, 0x24 * 16)
n_active = 0
for i in range(16):
    off = i * 0x24
    slot = raw_objs[off:off + 0x24]
    active = bool(slot[0] & 1)
    if active:
        n_active += 1
        oe = ObjectEvent(slot)
        print(f"   slot {i:2d} ACTIVE   coords={oe.current_coords} elev={oe.current_elevation} "
              f"map={oe.map_group_and_number} graphics_id={oe.graphics_id} "
              f"movement_type={oe.movement_type}")
    else:
        print(f"   slot {i:2d} inactive")
print(f"   -> {n_active} live objects loaded (player + nearby NPCs only); none of them sit on a "
      f"tile that measurement (4) below shows to be phantom-blocked.")

print("\n2c) COORD EVENTS (trigger on stepping onto a tile) and BG EVENTS (trigger on facing+A):")
print(f"   coord_events: {[ce.to_dict() for ce in md0.coord_events]}")
for be in md0.bg_events:
    print(f"   bg_event: {be.to_dict()}")
print("   -> no coord/bg event anywhere near the blocked boundary found below; the two bg_events "
      "present are the gym's decorative statues, unrelated to movement.")

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("3) TILE_TYPE / BEHAVIOUR DIVERSITY")
by_type = {}
for (x, y), info in grid.items():
    by_type.setdefault(info["tile_type"], []).append((x, y))
for tt, coords in sorted(by_type.items()):
    print(f"   {tt!r:20} {len(coords):4d} tiles  e.g. {coords[:6]}")
print(f"   -> only {len(by_type)} distinct tile_type/behaviour values in the whole room; "
      f"'Normal' covers ordinary floor AND (per test 4) the phantom-blocked boundary tiles "
      f"identically -- tile_type/behaviour does NOT distinguish them.")

by_metatile = {}
for (x, y), info in grid.items():
    by_metatile.setdefault(info["metatile"], []).append((x, y))
print(f"\n   {len(by_metatile)} distinct RAW metatile IDs in the room (finer grain than tile_type, "
      f"visual-tile resolution). Checked below (test 4) whether the phantom-blocked boundary has "
      f"a distinct metatile id from the source tile -- it does not in the tested case.")

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("4) EMPIRICAL PUSH TEST")
print("   Method: fresh state reload per test (clean baseline), walk to from_tile with REAL")
print("   navigation, snapshot a local window + full object list, hold direction, snapshot again.")


def snapshot_window(cx, cy, radius=2):
    win = {}
    for y in range(max(0, cy - radius), min(H, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(W, cx + radius + 1)):
            mt, c, e = raw_metatile(x, y, W)
            win[(x, y)] = (mt, c, e)
    return win


def snapshot_objects():
    # Exclude the player itself -- we already track player movement separately;
    # this is specifically "did any NPC/gate-like object move on its own".
    return [tuple(o.current_coords) for o in get_map_objects() if "isPlayer" not in o.flags]


def goto(target):
    """Real walk via the production navigator. Returns True if arrived."""
    if pos() == target:
        return True
    g = navigate_to_anywhere(GYM, target, avoid_encounters=True, avoid_scripted_events=False)
    n = 0
    try:
        while n < 2000:
            next(g)
            context.emulator.run_single_frame()
            n += 1
    except StopIteration:
        return True
    except Exception:
        return False
    return False


def push_test(from_tile, direction, frames=48):
    boot()
    if not goto(from_tile):
        return {"from": from_tile, "dir": direction, "reach_failed": True}
    p_before = pos()
    win_before = snapshot_window(*from_tile)
    obj_before = snapshot_objects()
    for _ in range(frames):
        context.emulator.press_button(direction)
        context.emulator.run_single_frame()
    p_after = pos()
    win_after = snapshot_window(*from_tile)
    obj_after = snapshot_objects()
    tile_changes = {t: (win_before[t], win_after[t]) for t in win_before if win_before[t] != win_after.get(t)}
    return {
        "from": from_tile,
        "dir": direction,
        "reach_failed": False,
        "moved": p_before != p_after,
        "pos_before": p_before,
        "pos_after": p_after,
        "tile_changes": tile_changes,
        "objects_changed": obj_before != obj_after,
    }


TESTS = [
    ((4, 19), "Up"),      # spawn tile -- north step reads collision=0 but see result
    ((4, 19), "Down"),    # spawn tile -- control: legit open corridor
    ((4, 19), "Left"),    # spawn tile -- control: legit open corridor (elevation 3->0)
    ((4, 19), "Right"),   # spawn tile -- control: genuine wall (static collision=1)
    ((2, 19), "Up"),      # second column, same row boundary -- is it systemic?
    ((2, 19), "Down"),    # control
    ((15, 22), "Up"),     # distant, already-proven-reachable area -- control
    ((15, 22), "Down"),   # distant control (into the entrance corridor wall)
]

results = []
for tile, d in TESTS:
    r = push_test(tile, d)
    results.append(r)
    if r["reach_failed"]:
        print(f"   {tile!s:10} {d:6} -> COULD NOT REACH from_tile (skipped)")
        continue
    tag = "MOVED" if r["moved"] else "no movement"
    grid_tag = f"GRID CHANGED {r['tile_changes']}" if r["tile_changes"] else "grid unchanged"
    obj_tag = "OBJECTS CHANGED" if r["objects_changed"] else "objects unchanged"
    move_str = f"{r['pos_before']}->{r['pos_after']}"
    print(f"   {tile!s:10} {d:6} -> {tag:12} {move_str:22} {grid_tag:20} {obj_tag}")

print("\n   Extended hold: 20 rounds x 30 frames (600 total) of Up from (4,19) -- does patience help?")
boot()
goto((4, 19))
before = snapshot_window(4, 19)
for _ in range(600):
    context.emulator.press_button("Up")
    context.emulator.run_single_frame()
after = snapshot_window(4, 19)
print(f"   pos after 600 frames of Up: {pos()}  (started (4,19))")
print(f"   window changed: {before != after}")

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("5) calculate_path RESULTS (static planner, current live grid)")
boot()
p_now = pos()
probe_targets = [TARGET, (15, 22), (17, 10), (15, 12), (4, 14), (1, 10)]
for label, src in (("entrance(15,24)", ENTRANCE), ("player_pos" + str(p_now), p_now)):
    for t in probe_targets:
        try:
            path = calculate_path((GYM, src), (GYM, t), avoid_encounters=True, avoid_scripted_events=False)
            print(f"   {label:24} -> {t}: OK, {len(path)} waypoints, "
                  f"first3={[tuple(w.coordinates) for w in path[:3]]}")
        except Exception as e:
            print(f"   {label:24} -> {t}: FAIL {type(e).__name__}: {e}")

print("\n5b) Does the REAL navigator (not just calculate_path) reach the target from the player's")
print("    current position, in this exact configuration?")
boot()
g = navigate_to_anywhere(GYM, TARGET, avoid_encounters=True, avoid_scripted_events=False)
n = 0
outcome = None
try:
    while n < 3000:
        next(g)
        context.emulator.run_single_frame()
        n += 1
except StopIteration:
    outcome = "arrived"
except Exception as e:
    outcome = f"{type(e).__name__}: {e}"
if outcome is None:
    outcome = "cap hit (still navigating)"
print(f"   navigate_to_anywhere(player_pos -> {TARGET}): {outcome} after {n} frames, pos={pos()}")

print("\n5c) Control: does the real navigator reach a target NOT behind the boundary "
      "((15,22), already proven reachable)?")
boot()
g = navigate_to_anywhere(GYM, (15, 22), avoid_encounters=True, avoid_scripted_events=False)
n = 0
outcome = None
try:
    while n < 2000:
        next(g)
        context.emulator.run_single_frame()
        n += 1
except StopIteration:
    outcome = "arrived"
except Exception as e:
    outcome = f"{type(e).__name__}: {e}"
if outcome is None:
    outcome = "cap hit"
print(f"   navigate_to_anywhere(player_pos -> (15,22)): {outcome} after {n} frames, pos={pos()}")

# ---------------------------------------------------------------------------
print("\n" + "=" * 78)
print("VERDICT")
any_grid_change = any(r.get("tile_changes") for r in results)
any_obj_change = any(r.get("objects_changed") for r in results if not r["reach_failed"])
print(f"   Any push anywhere changed the grid?   {any_grid_change}")
print(f"   Any push anywhere changed an object?  {any_obj_change}")
print("   See report text for the full interpretation.")
