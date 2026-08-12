"""KI-58, fourth pass: STOP MODELLING THE GYM AND JUST WALK IT.

‼ WHY THIS EXISTS. Three offline models now agree that MOSSDEEP_CITY_GYM has no route from the
entrance to Tate & Liza — which cannot be true, because the game requires that fight. Per this
project's own rule (KI-57): *when a measurement implies the game soft-locks itself, the measurement
is the suspect.* Three measurements saying the same wrong thing means the shared assumption is
wrong, and every one of them shares the same one — they ask `calculate_path` / the ROM warp table
what the map is like.

This probe asks the GAME. It presses buttons and records where the avatar actually ends up. It has
no map model at all: no collision reading, no warp table, no planner. It cannot be wrong about the
map for the same reason a person cannot be wrong about which room they walked into.

HOW IT WORKS — a breadth-first search over REAL positions:
  * a STATE is `(map_group_and_number, local_coordinates)`;
  * from a state, for each of the four directions, restore that state's emulator snapshot, press
    the direction, and let the game settle;
  * if the avatar ended up somewhere new, that is an EDGE — and if the map or the distance jumped,
    it was a WARP, discovered empirically rather than read from a table;
  * repeat until the goal is reached or the frontier is exhausted.

‼ IT PRESSES TWICE ON PURPOSE. In Gen 3 a direction press when facing another way TURNS the avatar
without moving it. A single press would therefore report "this direction is blocked" for every tile
the avatar was not already facing — a false wall on three sides of every step.

‼ CONTROLS:
  * KNOWN-GOOD — the search must find `(1,33)`, a tile `calculate_path` already reaches from the
    entrance in 10 waypoints. If the walker cannot reproduce a walk the planner does, the walker is
    broken and its map is worthless.
  * SNAPSHOT FIDELITY — restoring a state and reading the position back must return that exact
    state before any button is pressed, checked on every expansion. A save/restore that drifts
    would silently corrupt the whole graph.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gym_bruteforce.py
      PYTHONUTF8=1 py -3.12 probe_gym_bruteforce.py --budget 4000
"""

import argparse
import pathlib
import sys
from collections import deque

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

from modules.map import get_map_objects
from modules.map_data import MapRSE
from modules.player import get_player_avatar

parser = argparse.ArgumentParser()
parser.add_argument("--budget", type=int, default=3000, help="max direction probes")
parser.add_argument("--anchor", default="in_mossdeep_gym.ss1")
args = parser.parse_args()

ANCHOR = REPO / "tools" / "story-dev" / "saves" / args.anchor
GYM = MapRSE.MOSSDEEP_CITY_GYM.value
GOAL_TILES = {(23, 8), (24, 8), (23, 9), (24, 9), (25, 7), (22, 7)}
CONTROL_TILES = {(1, 33), (3, 28)}
DIRECTIONS = ("Up", "Down", "Left", "Right")

line = "=" * 96


def statues():
    """Where every non-player object currently STANDS.

    ‼‼ THIS IS THE HALF THE FIRST VERSION MISSED, AND IT IS WHY IT FOUND NOTHING. Mossdeep Gym is
    a **rotating-tile statue puzzle**, not a warp maze: nine `coord_events` are floor switches whose
    scripts call `moverotatingtileobjects`, and `MoveRotatingTileObjects`
    (`src/rotating_tile_puzzle.c:108`) shifts every statue standing on a coloured ARROW metatile one
    square in that arrow's direction — permanently, for the rest of the session. All 21
    TRICK_HOUSE_STATUE objects sit on arrow tiles, and they are what seal the corridors to the
    (11,3), (13,32) and (21,10) panels.

    So the walker was *changing the map while exploring it*: it stepped on switches, statues moved,
    and because its state key was only `(map, position)` two genuinely different worlds collapsed
    into one node and the search truncated at 35 tiles.

    ‼ We do NOT model the arrow bands. The game moves the statues; we just read where they ended up
    and make it part of the state. That keeps this probe model-free, which is its entire value."""
    try:
        return frozenset(
            tuple(obj.current_coords) for obj in get_map_objects() if "isPlayer" not in obj.flags
        )
    except Exception:  # noqa: BLE001 — an unreadable object list would silently merge states, so
        # return a sentinel that can never equal a real reading rather than an empty set.
        return frozenset({(-1, -1)})


def where():
    avatar = get_player_avatar()
    return (tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates), statues())


def settle(frames: int = 90):
    """Run until the avatar's position has been stable for a while (covers warp fades)."""
    last = None
    stable = 0
    for _ in range(frames):
        context.emulator.run_single_frame()
        try:
            now = where()
        except Exception:  # noqa: BLE001 — mid-warp the avatar can be unreadable; keep running
            stable = 0
            continue
        if now == last:
            stable += 1
            if stable >= 12:
                return now
        else:
            stable = 0
            last = now
    return last


def step(direction: str, origin):
    """Press `direction` and return where we ended up, having moved AT MOST ONE TILE.

    ‼ PRESS, SETTLE, AND ONLY THEN PRESS AGAIN — never twice blind. In Gen 3 a direction press
    turns the avatar in place when it is facing another way, so one blind press reports a false
    wall on three sides of every tile. But TWO blind presses move TWO tiles whenever the avatar
    already faced that way, which silently skips tiles — and skipping a tile in a warp maze means
    stepping straight over a panel and never recording it. The first version of this probe did
    exactly that: it found 0 warp edges and failed its own known-good control.

    So: press once and settle. If we did not move, we only turned — press again and settle."""
    context.emulator.press_button(direction)
    landed = settle()
    if landed == origin:
        context.emulator.press_button(direction)
        landed = settle()
    return landed


context.emulator.load_save_state(ANCHOR.read_bytes())
settle()
start = where()

print(line)
print("KI-58 brute force — walking the gym for real")
print(line)
print(f"\nanchor: {ANCHOR.name}")
print(f"start : {MapRSE(start[0]).name} {start[1]}")
print(f"goal  : any of {sorted(GOAL_TILES)}  (statue config is part of the state)")
print(f"budget: {args.budget} direction probes\n")

snapshots = {start: context.emulator.get_save_state()}
came_from = {start: None}
queue = deque([start])
edges = []
warp_edges = []
probes = 0
fidelity_failures = 0
goal_state = None

while queue and probes < args.budget and goal_state is None:
    state = queue.popleft()
    for direction in DIRECTIONS:
        if probes >= args.budget:
            break
        context.emulator.load_save_state(snapshots[state])
        settle(30)
        # ‼ SNAPSHOT FIDELITY CONTROL — restoring must put us back exactly where we were.
        if where() != state:
            fidelity_failures += 1
            continue
        probes += 1
        landed = step(direction, state)
        if landed is None or landed == state:
            continue
        moved = abs(landed[1][0] - state[1][0]) + abs(landed[1][1] - state[1][1])
        is_warp = landed[0] != state[0] or moved > 1
        edges.append((state, direction, landed, is_warp))
        if is_warp:
            warp_edges.append((state, direction, landed))
        if landed not in came_from:
            came_from[landed] = (state, direction)
            snapshots[landed] = context.emulator.get_save_state()
            queue.append(landed)
            if landed[0] == GYM and landed[1] in GOAL_TILES:
                goal_state = landed
                break

print(line)
print("CONTROLS")
print(line)
print(f"\n  [1] SNAPSHOT FIDELITY — restore-then-read mismatches: {fidelity_failures} "
      f"({'OK' if fidelity_failures == 0 else 'FAIL — the graph is corrupt'})")
reached_tiles = {st[1] for st in came_from if st[0] == GYM}
hit = sorted(CONTROL_TILES & reached_tiles)
print(f"  [2] KNOWN-GOOD — warp panels reached from the door: {hit or 'NONE'} "
      f"({'OK' if hit else 'FAIL — a walk-only pocket means the switches were never used'})")

print(f"\n  states visited: {len(came_from)}   direction probes: {probes}   "
      f"edges: {len(edges)}   WARP edges: {len(warp_edges)}")

print("\n" + line)
print("WARPS AS THE GAME ACTUALLY PERFORMS THEM")
print(line)
seen = set()
for state, direction, landed in warp_edges:
    key = (state, landed)
    if key in seen:
        continue
    seen.add(key)
    print(f"  {MapRSE(state[0]).name} {state[1]} --{direction}--> "
          f"{MapRSE(landed[0]).name} {landed[1]}")

# ---------------------------------------------------------------- planner vs the game
# ‼ THE MOST VALUABLE OUTPUT IN THIS FILE. The walker is empirical: it pressed a button and read
# where the avatar went. `calculate_path` is a model. Where they disagree, the model is wrong — and
# a model that hands the bot a route it physically cannot walk fails LATER, somewhere unrelated,
# which is the most expensive kind of bug this project has.
print("\n" + line)
print("PLANNER vs THE GAME — every disagreement is a planner bug")
print(line)
from modules.map import get_map_data  # noqa: E402 — imported here so the walk needs no map model
from modules.map_path import PathFindingError, calculate_path  # noqa: E402

walked = {st[1] for st in came_from if st[0] == GYM}
CHECK = [(1, 33), (3, 28), (1, 23), (7, 18), (8, 12), (9, 18), (23, 20), (20, 24),
         (11, 3), (11, 35), (13, 32), (21, 10), (23, 8)]
disagreements = 0
for target in CHECK:
    try:
        waypoints = len(calculate_path(get_map_data(MapRSE.MOSSDEEP_CITY_GYM, start[1]),
                                       get_map_data(MapRSE.MOSSDEEP_CITY_GYM, target)))
        planner = f"OK {waypoints}wp"
        planner_ok = True
    except PathFindingError:
        planner, planner_ok = "no path", False
    except Exception as error:  # noqa: BLE001 — an errored plan is reported, not hidden
        planner, planner_ok = f"ERR {type(error).__name__}", False
    walker_ok = target in walked
    verdict = "agree" if planner_ok == walker_ok else "‼ DISAGREE"
    if planner_ok != walker_ok:
        disagreements += 1
    print(f"  {str(target):<9} planner: {planner:<10} walker: {'reached' if walker_ok else 'NOT reached':<12} {verdict}")
print(f"\n  {disagreements} disagreement(s). Where they differ, THE WALKER IS RIGHT — it pressed the")
print("  button. A planner route the bot cannot walk is worse than no route, because it fails")
print("  later and somewhere else.")

# ---------------------------------------------------------------- picture
print("\n" + line)
print("WHAT THE BOT CAN ACTUALLY WALK FROM THE GYM DOOR")
print(line)
print("  o = walked   W = warp panel (never reached)   # = blocked   . = floor never reached\n")
header = "     " + "".join(str(x % 10) for x in range(0, 27))
print(header)
warp_tiles = {tuple(w.local_coordinates) for w in get_map_data(MapRSE.MOSSDEEP_CITY_GYM, (0, 0)).warps}
for y in range(0, 37):
    row = ""
    for x in range(0, 27):
        tile = (x, y)
        try:
            blocked = get_map_data(MapRSE.MOSSDEEP_CITY_GYM, tile).collision != 0
        except Exception:  # noqa: BLE001 — off-map reads draw as blocked
            blocked = True
        if tile in walked:
            row += "o"
        elif tile in warp_tiles:
            row += "W"
        elif blocked:
            row += "#"
        else:
            row += "."
    print(f"  {y:>2} {row}")
print(header)

print("\n" + line)
print("VERDICT")
print(line)
if goal_state is None:
    reached = sorted({st[1] for st in came_from if st[0] == GYM})
    print(f"\n  Goal NOT reached within {probes} probes. {len(reached)} gym tiles visited.")
    print(f"  Frontier left: {len(queue)} state(s) — rerun with a bigger --budget if non-zero.")
    print(f"  Visited tiles: {reached[:60]}{' ...' if len(reached) > 60 else ''}")
else:
    route = []
    node = goal_state
    while came_from[node] is not None:
        previous, direction = came_from[node]
        route.append((previous, direction, node))
        node = previous
    route.reverse()
    print(f"\n  ✅ REACHED {MapRSE(goal_state[0]).name} {goal_state[1]} in {len(route)} step(s):\n")
    for previous, direction, node in route:
        mark = "  <- WARP" if (node[0] != previous[0] or
                               abs(node[1][0] - previous[1][0]) + abs(node[1][1] - previous[1][1]) > 1) else ""
        print(f"      {MapRSE(previous[0]).name} {str(previous[1]):<9} {direction:<6} -> {str(node[1]):<9}{mark}")
print(line)
