"""KI-57: draw the ground truth around the Slateport Harbor door, instead of spot-checking it.

‼ WHY THIS EXISTS. KI-57 established that Capt. Stern is parked on `SLATEPORT_CITY (28,13)` by
`SlateportCity_EventScript_MovePeopleForSternInterview`, which `OnTransition` runs whenever
`VAR_SLATEPORT_CITY_STATE == 1` — a var **§Ch15's own Maxie script sets** (decomp-verified:
`MagmaHideout_4F/scripts.inc` does `clearflag FLAG_HIDE_SLATEPORT_CITY_CAPTAIN_STERN` /
`setvar VAR_SLATEPORT_CITY_STATE, 1`). So completing Ch15 spawns Ch16's blocker.

But KI-57 was written from ~15 individual `calculate_path` spot-checks, and those left a
conclusion that **cannot be true**: that the harbor door is sealed. In the real game this is
exactly the moment the player must walk into that harbor, and Game Freak did not ship a scene that
locks its own next beat. When a measurement implies the game is broken, the measurement is
usually the thing that is broken — so this probe stops sampling and draws the whole neighbourhood.

WHAT IT DRAWS, over a bounding box around the door: one character per tile, from the map data the
bot itself reads —
    `.` walkable      `#` blocked (collision)     `~` surfable water
    `O` a live OBJECT standing there              `D` the harbor door warp (28,12)
    `W` any other warp                            `P` the player
Then, for every walkable tile ADJACENT to the door, it asks the planner whether the bot can
actually get there from where it is standing. That is the question KI-57 needs answered and the
one a picture makes obvious.

‼ CONTROLS, because a hand-rolled collision reading is a second opinion, not a fact:
  * PLANNER AGREEMENT — the drawn walkability must AGREE with `calculate_path` on a sample of
    tiles (reachable ones must plan, blocked ones must not). A picture that disagrees with the
    planner the bot actually uses is decoration, and is reported as untrusted.
  * OBJECT CONTROL — the three NPCs KI-57 named (`(28,13)` Stern, `(28,14)` Gabby, `(29,13)` Ty)
    must appear as `O` in the drawing. If they do not, this is not the era KI-57 measured.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_slateport_harbor_map.py
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

from modules.map import get_map_data, get_map_objects
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar

FAILURE_STATE = REPO / "tools" / "story-dev" / "saves" / "stalls" / "ch16b-f20252.ss1"
CITY = MapRSE.SLATEPORT_CITY
DOOR = (28, 12)

X0, X1 = 20, 43
Y0, Y1 = 3, 22

line = "=" * 100

context.emulator.load_save_state(FAILURE_STATE.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

avatar = get_player_avatar()
PLAYER = tuple(avatar.local_coordinates)
print(line)
print("KI-57 — the ground around the Slateport Harbor door")
print(line)
print(f"\nstate: {FAILURE_STATE.name}   avatar: "
      f"{MapRSE(tuple(avatar.map_group_and_number)).name} {PLAYER}")

# ---------------------------------------------------------------- gather
occupied: dict[tuple[int, int], str] = {}
for obj in get_map_objects():
    try:
        occupied[tuple(obj.current_coords)] = str(getattr(obj, "local_id", "?"))
    except Exception as error:  # noqa: BLE001 — one unreadable object must not hide the rest
        print(f"  (an object was unreadable: {type(error).__name__})")

warps: dict[tuple[int, int], str] = {}
for index, warp in enumerate(get_map_data(CITY, (0, 0)).warps):
    warps[tuple(warp.local_coordinates)] = str(index)

walkable: dict[tuple[int, int], bool] = {}
grid: dict[tuple[int, int], str] = {}
for y in range(Y0, Y1 + 1):
    for x in range(X0, X1 + 1):
        tile = (x, y)
        try:
            data = get_map_data(CITY, tile)
            collision = data.collision
            surfable = data.is_surfable
        except Exception:  # noqa: BLE001 — off-map tiles are drawn as unknown, not fatal
            grid[tile] = " "
            walkable[tile] = False
            continue
        free = collision == 0
        walkable[tile] = free and tile not in occupied
        if tile == PLAYER:
            grid[tile] = "P"
        elif tile == DOOR:
            grid[tile] = "D"
        elif tile in occupied:
            grid[tile] = "O"
        elif tile in warps:
            grid[tile] = "W"
        elif surfable:
            grid[tile] = "~"
        elif free:
            grid[tile] = "."
        else:
            grid[tile] = "#"

# ---------------------------------------------------------------- draw
print(f"\n`.` walkable   `#` blocked   `~` water   `O` object   `D` harbor door   `W` warp   `P` player")
print()
header = "     " + "".join(str(x % 10) for x in range(X0, X1 + 1))
print(header)
for y in range(Y0, Y1 + 1):
    row = "".join(grid[(x, y)] for x in range(X0, X1 + 1))
    print(f"  {y:>2} {row}")
print(header)

print("\n  live objects in the box:")
for tile in sorted(t for t in occupied if X0 <= t[0] <= X1 and Y0 <= t[1] <= Y1):
    print(f"      id={occupied[tile]:<3} at {tile}")
print("\n  warps in the box:")
for tile in sorted(t for t in warps if X0 <= t[0] <= X1 and Y0 <= t[1] <= Y1):
    print(f"      warp {warps[tile]:<3} at {tile}")


# ---------------------------------------------------------------- the question
def plan(start, end) -> str:
    try:
        return f"OK, {len(calculate_path(get_map_data(CITY, start), get_map_data(CITY, end)))} wp"
    except PathFindingError:
        return "FAIL"
    except Exception as error:  # noqa: BLE001 — a probe reports, it does not crash
        return f"ERR {type(error).__name__}"


print("\n" + line)
print("CAN THE BOT REACH ANY TILE THAT TOUCHES THE DOOR?")
print(line)
door_neighbours = [(DOOR[0] + dx, DOOR[1] + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
usable = []
for tile in door_neighbours:
    mark = grid.get(tile, "?")
    reach = plan(PLAYER, tile)
    if reach.startswith("OK"):
        usable.append(tile)
    print(f"      {str(tile):<9} drawn as '{mark}'   from player {PLAYER}: {reach}")

# ---------------------------------------------------------------- controls
print("\n" + line)
print("CONTROLS")
print(line)
ok = True

print("\n  [1] OBJECT CONTROL — KI-57's three NPCs must be standing where it said")
for tile, who in (((28, 13), "Capt. Stern"), ((28, 14), "Gabby"), ((29, 13), "Ty")):
    present = tile in occupied
    print(f"      {'OK  ' if present else 'FAIL'}  {str(tile):<9} {who:<12} object present: {present}")
    if not present:
        ok = False
if not ok:
    print("      => this is NOT the era KI-57 measured; nothing above is comparable.")

print("\n  [2] PLANNER AGREEMENT — the drawing must agree with `calculate_path`")
sample = [(27, 13), (27, 14), (28, 15), (29, 14), (28, 13), (28, 14), (29, 13), (27, 12), (29, 12)]
agree = 0
for tile in sample:
    drawn_free = walkable.get(tile, False)
    planned = plan(PLAYER, tile).startswith("OK")
    # A drawn-blocked tile must not plan. A drawn-free tile MAY still fail (it can be walkable
    # but cut off), so only the blocked direction is a hard contradiction.
    contradiction = (not drawn_free) and planned
    if not contradiction:
        agree += 1
    print(f"      {'OK  ' if not contradiction else 'FAIL'}  {str(tile):<9} "
          f"drawn_walkable={drawn_free!s:<5} planner_reaches={planned}")
    if contradiction:
        ok = False
print(f"      {agree}/{len(sample)} consistent")

print("\n" + line)
print("READING")
print(line)
if not ok:
    print("  A CONTROL FAILED — the drawing is not trustworthy. Do not act on it.")
elif usable:
    print(f"  ‼ THE DOOR IS REACHABLE after all, via {usable}.")
    print("    KI-57's 'the plug seals the door' reading was WRONG — it came from spot-checks")
    print("    that happened to miss the open side. Fix the CONSTANT to one of these tiles.")
else:
    print("  No tile touching the door is reachable from where the bot stands.")
    print("  ‼ Before concluding the door is sealed, note the bot is standing where a WHITEOUT")
    print("    left it. Re-ask this from a tile the bot would normally arrive on — a scene the")
    print("    game requires cannot be unreachable in the era the game itself creates.")
print(line)
