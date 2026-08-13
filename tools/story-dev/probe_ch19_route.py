"""§Ch19 — WHY does Mossdeep City refuse to path from the Pokémon Center to the Space Center door?

‼ THIS PROBE EXISTS BECAUSE THE FIRST DRIVEN RUN OF §Ch19 FAILED, and the failure had two
completely different possible causes that a single `calculate_path` call cannot tell apart:

    (a) THE CITY IS GENUINELY DISCONNECTED at this point in the story — the intended route really
        does run through the forced Team Magma cutscene, and the chapter must go there first; or
    (b) OUR PLANNER IS WRONG — KI-59 records that `map_path` INVERTS `Impassable *` directions and
        therefore OVER-BLOCKS every such tile. A false "no path" looks exactly like a real one.

The measured failure (`--driver spacecenter1`, 2026-08-12):
    UnreachableDestinationError: Could not reach (64,16) on MOSSDEEP_CITY: the field is idle and we
    are still at (28,17)  ->  Could not find a path from (28/17) to (64/16).

‼ AND THE HAZARD PROBE ALREADY MADE (a) DOUBTFUL. `probe_ch19_hazards.py` H5 got the SAME
PathFindingError reading the ROM collision layer for a map the player was NOT standing on — i.e.
with the five Magma NPCs NOT modelled as obstacles at all. So whatever blocks the route is in the
STATIC collision data, not the NPC wall the design assumed. That is the thing to identify.

THE DISCRIMINATING MEASUREMENT (the KI-39 lesson: make ONE measurement that could tell the
hypotheses apart, and sample MANY tiles rather than one):
  1. Flood-fill the city from the player's REAL tile using the raw per-tile `collision` byte and
     our OWN BFS — a model that knows nothing about `Impassable *` direction semantics.
  2. Ask `calculate_path` — the bot's actual planner — about the same targets.
  3. COMPARE. A tile that our BFS reaches and the planner refuses is a PLANNER defect (KI-59).
     A tile neither reaches is a genuinely separated component, and the route must go elsewhere.
  4. Print an ASCII map so the boundary is visible rather than inferred, and resolve the Space
     Center door from the WARP TABLE instead of trusting the coordinate in the groundwork.

‼ KI-60: `calculate_path` never validates its SOURCE tile, so every answer here is evidence about
the DESTINATION only. The player's position is therefore ASSERTED and printed, never assumed.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch19_route.py
      PYTHONUTF8=1 py -3.12 probe_ch19_route.py --anchor post_mossdeep_gym.ss1
"""

import argparse
import collections
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import get_event_var
from modules.player import get_player_avatar

parser = argparse.ArgumentParser()
parser.add_argument("--anchor", default="post_mossdeep_gym.ss1")
parser.add_argument("--from-tile", default="", help="override the source tile, as X,Y")
args = parser.parse_args()

ANCHOR = REPO / "tools" / "story-dev" / "saves" / args.anchor
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

CITY = MapRSE.MOSSDEEP_CITY
BAR = "=" * 100


def head(title):
    print(f"\n{BAR}\n{title}\n{BAR}\n")


avatar = get_player_avatar()
real_tile = tuple(avatar.local_coordinates)
real_map = tuple(avatar.map_group_and_number)
print(f"anchor: {args.anchor}")
print(f"avatar: {MapRSE(real_map).name} {real_tile}   (‼ asserted, not assumed — KI-60)")
assert real_map == CITY.value, f"anchor is not in Mossdeep City, it is on {MapRSE(real_map).name}"

source = real_tile
if args.from_tile:
    source = tuple(int(v) for v in args.from_tile.split(","))
    print(f"‼ source OVERRIDDEN to {source} — this is a HYPOTHETICAL, not where the bot stands.")

print(f"VAR_MOSSDEEP_CITY_STATE         = {get_event_var('MOSSDEEP_CITY_STATE')}")
print(f"VAR_MOSSDEEP_SPACE_CENTER_STATE = {get_event_var('MOSSDEEP_SPACE_CENTER_STATE')}")

# ---------------------------------------------------------------------------------------------
head("1 — THE SPACE CENTER DOOR, READ FROM THE WARP TABLE (not from the groundwork's constant)")

city = get_map_data(CITY, (0, 0))
width, height = city.map_size
print(f"MOSSDEEP_CITY size = {width} x {height}\n")

door_tiles = []
for warp in city.warps:
    try:
        dest = MapRSE((warp.destination_map_group, warp.destination_map_number)).name
    except Exception:  # noqa: BLE001 - an unresolvable destination is still worth printing
        dest = f"?{(warp.destination_map_group, warp.destination_map_number)}"
    tile = tuple(warp.local_coordinates)
    mark = ""
    if "SPACE_CENTER" in dest:
        door_tiles.append(tile)
        mark = "   <== SPACE CENTER"
    if "STEVENS_HOUSE" in dest:
        mark = "   <== Steven's house"
    print(f"  warp {tile!s:>10} -> {dest}{mark}")

print(f"\nSpace Center door tile(s) from the warp table: {door_tiles}")
print("groundwork's SPACE_CENTER_DOOR = (64, 15), approach (64, 16)")

# ---------------------------------------------------------------------------------------------
head("2 — OUR OWN FLOOD FILL over the raw `collision` byte (knows nothing about Impassable dirs)")


# ‼‼ THE LIVE NPCs ARE PART OF THE MAP, AND LEAVING THEM OUT MADE THIS PROBE LIE.
# First version of this probe modelled collision ONLY, found that (64,16) was reachable while the
# planner refused, and concluded "KI-59 shape — the planner over-blocks". That was WRONG, and it
# is the playbook's own named trap: *a known bug in a tool is a seductive explanation for anything
# that tool reports*. The boring explanation was the right one — `map_path.py:710-717` puts every
# LOADED object's current and previous tile into `blocked_coordinates`, and the five Team Magma
# NPCs stand on the only land bridge at x=44, y=23-26 (plus Maxie at (45,25)). The planner was
# correct; my model was missing an actor.
# ‼ This only shows up when the player is STANDING ON the map — `get_map_objects()` returns the
# LOADED objects, so a probe run against a map the avatar is not on sees none of them and silently
# measures a different world. `probe_ch19_hazards.py` H5 says exactly that about itself.
try:
    from modules.map import get_map_objects

    npc_tiles = {
        tuple(obj.current_coords)
        for obj in get_map_objects()
        if "isPlayer" not in obj.flags
    }
except Exception as error:  # noqa: BLE001 - report it; never silently model an empty world
    npc_tiles = set()
    print(f"‼ could not read live objects ({type(error).__name__}) — NPC blocking NOT modelled")

print(f"live NPCs on this map (blocked by the planner): {len(npc_tiles)} -> {sorted(npc_tiles)}\n")


def passable(tile, *, with_npcs=True):
    """Collision-0 AND (optionally) not standing under a live NPC.

    Two models on purpose: `with_npcs=True` is what the bot's planner effectively sees, and
    `with_npcs=False` is the static map. Running BOTH is what distinguishes "an NPC wall the story
    intends" from "our planner over-blocks a tile" — the two hypotheses this probe exists to separate."""
    x, y = tile
    if not (0 <= x < width and 0 <= y < height):
        return False
    if with_npcs and tile in npc_tiles:
        return False
    try:
        return get_map_data(CITY, tile).collision == 0
    except Exception:  # noqa: BLE001 - an unreadable tile is treated as a wall, and counted below
        return False


seen = {source}
queue = collections.deque([source])
while queue:
    x, y = queue.popleft()
    for step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nxt = (x + step[0], y + step[1])
        if nxt not in seen and passable(nxt):
            seen.add(nxt)
            queue.append(nxt)

print(f"flood fill from {source}: {len(seen)} tile(s) reachable under a collision-only model")
for door in door_tiles:
    below = (door[0], door[1] + 1)
    print(f"  door {door}: in-component={door in seen}   approach {below}: in-component={below in seen}")

# ---------------------------------------------------------------------------------------------
head("3 — WHAT THE REAL PLANNER SAYS about the same targets (this is what the bot uses)")

TRIGGER_LINE = [(42, 21), (41, 22), (41, 23), (41, 24), (40, 25), (40, 26)]
targets = [(t, "trigger-line") for t in TRIGGER_LINE]
targets += [(d, "space-center-door") for d in door_tiles]
targets += [((d[0], d[1] + 1), "door-approach") for d in door_tiles]

rows = []
for tile, label in targets:
    try:
        path = calculate_path(get_map_data(CITY, source), get_map_data(CITY, tile))
        verdict = f"OK {len(path)} waypoint(s)"
    except PathFindingError as error:
        verdict = f"PathFindingError ({str(error)[:60]})"
    except Exception as error:  # noqa: BLE001
        verdict = f"{type(error).__name__}: {str(error)[:60]}"
    mine = "reachable" if tile in seen else "NOT-reachable"
    flag = ""
    if tile in seen and not verdict.startswith("OK"):
        flag = "   ‼ DISAGREEMENT — my BFS reaches it, the planner refuses (KI-59 shape)"
    rows.append((tile, label, mine, verdict, flag))
    print(f"  {tile!s:>10} {label:<18} bfs={mine:<14} planner={verdict}{flag}")

# ---------------------------------------------------------------------------------------------
head("4 — THE MAP, so the boundary is SEEN rather than inferred")

print("legend:  @ player   D space-center door   T cutscene trigger tile   . reachable(bfs)")
print("         # wall     ? unreachable-but-walkable (a separate component)\n")

x0, x1 = max(0, min(source[0], *[d[0] for d in door_tiles]) - 4), min(width, max(source[0], *[d[0] for d in door_tiles]) + 6)
y0, y1 = max(0, min(source[1], *[d[1] for d in door_tiles]) - 6), min(height, max(source[1], *[d[1] for d in door_tiles]) + 14)

print("      " + "".join(str((x // 10) % 10) for x in range(x0, x1)))
print("      " + "".join(str(x % 10) for x in range(x0, x1)))
for y in range(y0, y1):
    line = []
    for x in range(x0, x1):
        tile = (x, y)
        if tile == source:
            line.append("@")
        elif tile in door_tiles:
            line.append("D")
        elif tile in TRIGGER_LINE:
            line.append("T")
        elif tile in seen:
            line.append(".")
        elif passable(tile):
            line.append("?")
        else:
            line.append("#")
    print(f"  {y:3d} " + "".join(line))

# ---------------------------------------------------------------------------------------------
head("5 — WHY does the planner refuse? Walk MY path and dump what the planner cares about")

# ‼ MY BFS IS DELIBERATELY OVER-PERMISSIVE (collision only), so "my BFS reaches it" is NOT yet a
# planner defect. The planner additionally honours ELEVATION TRANSITIONS and `Impassable *`
# directions. The playbook records both shapes:
#   * a BRIDGE / dual-elevation span reads as walls to `calculate_path` (Route 119, Lavaridge) —
#     the documented workaround is a HELD-INPUT walk, not a planner fix;
#   * KI-59, where `map_path` inverts `Impassable *` and over-blocks.
# Dumping elevation + tile type along my own path is what tells those two apart, and it is the
# difference between "design a detour" and "fix the shared planner".
parent = {source: None}
seen2 = {source}
queue = collections.deque([source])
while queue:
    cur = queue.popleft()
    for step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nxt = (cur[0] + step[0], cur[1] + step[1])
        if nxt not in seen2 and passable(nxt):
            seen2.add(nxt)
            parent[nxt] = cur
            queue.append(nxt)

TARGET = (64, 16)
if TARGET not in parent:
    print(f"  {TARGET} is not in my component either — nothing to walk.")
else:
    chain = []
    node = TARGET
    while node is not None:
        chain.append(node)
        node = parent[node]
    chain.reverse()
    print(f"  my BFS path {source} -> {TARGET} is {len(chain)} tile(s). Elevation transitions:\n")
    prev_elev = None
    transitions = 0
    for tile in chain:
        data = get_map_data(CITY, tile)
        elev = data.elevation
        if prev_elev is not None and elev != prev_elev:
            transitions += 1
            print(f"    {tile!s:>10} elev {prev_elev} -> {elev:<3} collision={data.collision} "
                  f"type={data.tile_type!r}   <== ELEVATION CHANGE")
        prev_elev = elev
    print(f"\n  elevation changes along the path: {transitions}")
    elevs = sorted({get_map_data(CITY, t).elevation for t in chain})
    print(f"  distinct elevations on the path: {elevs}")
    # An elevation of 0 means "transition tile" (walkable from any elevation) in Gen 3; 15 is
    # the "same as anything" marker. Anything else must MATCH to be walkable between tiles.
    print("  (Gen 3: elevation 0 = a transition tile, 15 = matches anything; two different "
          "non-zero, non-15 elevations cannot be walked between directly.)")

head("VERDICT")

door_ok = any(d in seen for d in door_tiles)
trigger_ok = any(t in seen for t in TRIGGER_LINE)
disagreements = [r for r in rows if r[4]]

print(f"  trigger line reachable by BFS : {trigger_ok}")
print(f"  space-center door reachable by BFS : {door_ok}")
print(f"  planner/BFS disagreements : {len(disagreements)}")
for tile, label, _mine, verdict, _flag in disagreements:
    print(f"      {tile} ({label}) — planner said {verdict}")
print()
if disagreements:
    print("  ⇒ At least one target is walkable under plain collision but REFUSED by the planner.")
    print("    That is KI-59's shape (Impassable-* inversion) and must be confirmed against the")
    print("    specific tiles before the chapter is designed around a detour it may not need.")
elif not door_ok and trigger_ok:
    print("  ⇒ The city really IS separated at this point in the story: the door is in a different")
    print("    component from the player, and the trigger line is not. The chapter must ride the")
    print("    forced cutscene FIRST and only then plan to the door — which is what the §Ch19")
    print("    hazard note prescribed and what `walk_into_the_space_center()` does NOT do today.")
else:
    print("  ⇒ Neither hypothesis is cleanly supported; read the map above before designing.")
