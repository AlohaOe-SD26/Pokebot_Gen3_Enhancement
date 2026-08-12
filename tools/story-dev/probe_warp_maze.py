"""Solve ANY Gen 3 warp-panel maze from the ROM warp table. The third dungeon earned this tool.

‼ WHY THIS IS GENERAL AND THE OTHERS WERE NOT. Three dungeons in a row have had the same shape —
a floor whose rooms are joined by warps rather than corridors, which **no planner in this codebase
can cross**, because `calculate_path`'s own docstring says it *"is not able to use warps"*:
  * the **Magma Hideout** (KI-56) — a same-map path failure that looked like a permanent strand;
  * the **Aqua Hideout** (§Ch17) — 21 of B1F's 25 warps return to B1F, plus a 3x4 panel grid;
  * the **Mossdeep Gym** (§Ch18) — 12 same-map warps in 6 pairs.
Each was solved by building the warp graph and searching it. This file is that method, written
once, with the controls that made the earlier answers trustworthy.

WHAT IT DOES: nodes are warp tiles and warp ARRIVAL tiles; WALK edges come from `calculate_path`
between nodes on one map; WARP edges come from the ROM warp table. Then BFS.

‼‼ THE PANEL-CROSSING RULE, WHICH IS THE ONE THING A NAIVE VERSION GETS WRONG. `calculate_path`
treats a warp panel as ordinary walkable ground, so it will happily plot a walk straight ACROSS
one — and the bot teleports mid-leg. §Ch17's first Master Ball run died exactly there: the leg
`(42,13) -> (48,13)` crosses `(45,13)`, itself a panel, and the bot ended up at `(45,9)`.
So a WALK EDGE ONLY COUNTS IF THE PATH'S INTERMEDIATE WAYPOINTS AVOID WARP TILES.
‼ And `Waypoint.is_warp` CANNOT be used for that test: `map_path.unroll_path` guards the warp
branch with `len(result) == 0`, so it is set only on the FINAL waypoint. Coordinates are compared
against the warp table instead.

‼ CONTROLS:
  * SELF-CHECK (`--maze aqua_hideout`) — the tool must reproduce the Aqua Hideout route that has
    already been DRIVEN to a PASS. That is a regression test on the generalisation itself: if this
    file ever stops producing that route, it broke, and the Mossdeep answer is not to be trusted.
  * PLANNER CONTROL — a known-adjacent pair on the start map must plan.
  * REACHABILITY CONTROL — the goal must be reachable. These are beats the GAME requires, so a
    "no route" is a broken instrument until proven otherwise (KI-57's lesson: when a measurement
    implies the game soft-locks itself, suspect the measurement).

‼ WHAT IT DOES NOT PROVE. Everything here is STATIC. Trainers and NPCs standing in the corridors
are invisible to `calculate_path`, and §Ch15 was bitten three times trusting a static answer about
a dungeon. A route means "worth driving"; the driven run is the proof.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_warp_maze.py --maze mossdeep_gym
      PYTHONUTF8=1 py -3.12 probe_warp_maze.py --maze aqua_hideout      # the self-check
      PYTHONUTF8=1 py -3.12 probe_warp_maze.py --list
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar

SAVES = REPO / "tools" / "story-dev" / "saves"

#: Every maze this tool knows. `goal_tiles` are tried in order; the first reachable one wins.
MAZES = {
    "aqua_hideout": {
        "anchor": SAVES / "post_harbor.ss1",
        "maps": [MapRSE.AQUA_HIDEOUT_1F, MapRSE.AQUA_HIDEOUT_B1F, MapRSE.AQUA_HIDEOUT_B2F],
        "outside": MapRSE.LILYCOVE_CITY,
        "start": (MapRSE.LILYCOVE_CITY, (70, 5)),
        "goal_tiles": [(MapRSE.AQUA_HIDEOUT_B2F, t) for t in ((24, 19), (22, 19), (23, 18), (23, 20))],
        "goal_label": "a tile beside Matt (23,19)",
        "planner_control": (MapRSE.AQUA_HIDEOUT_1F, (13, 27), (14, 27)),
        # ‼ THE SELF-CHECK. This exact prefix was DRIVEN to a PASS (§Ch17), so the tool must keep
        # producing it. Written as full (map, tile) NODES rather than bare tiles: the first version
        # compared tiles only, after filtering the maze maps in, and "failed" on a route that was
        # perfectly correct. A control that is ambiguous about what it compares cries wolf, and a
        # control that cries wolf gets ignored.
        "expected_prefix": [
            (MapRSE.LILYCOVE_CITY, (70, 5)),
            (MapRSE.AQUA_HIDEOUT_1F, (13, 27)),
            (MapRSE.AQUA_HIDEOUT_1F, (22, 1)),
            (MapRSE.AQUA_HIDEOUT_B1F, (29, 1)),
            (MapRSE.AQUA_HIDEOUT_B1F, (27, 4)),
            (MapRSE.AQUA_HIDEOUT_B1F, (3, 15)),
        ],
    },
    "mossdeep_gym": {
        # ‼‼ THE ANCHOR MUST STAND IN THE GYM, and that is not a convenience — it is the fix for
        # KI-58. `map_path.is_tile_accessible` blocks any tile whose object template is not in
        # `active_objects`, and `active_objects` comes from the CURRENTLY LOADED map. Reconning
        # this **36-object** gym from `post_aqua.ss1` (standing in the Aqua Hideout) turned all 21
        # TRICK_HOUSE_STATUE tiles into pessimistic walls and made a real route look impossible.
        # `in_mossdeep_gym.ss1` is captured by `--driver mossdeeptravel` on a PASS.
        "anchor": SAVES / "in_mossdeep_gym.ss1",
        "maps": [MapRSE.MOSSDEEP_CITY_GYM],
        "outside": MapRSE.MOSSDEEP_CITY,
        # ‼ START ON THE FLOOR TILE, NOT THE DOOR. `(6,35)`/`(7,35)` are the gym's two door tiles;
        # a search seeded on one found nothing, and the planner control `(6,35) -> (7,35)` FAILED
        # even though the tiles are adjacent — stepping onto a door fires it, so the planner will
        # not route between two of them. Same door-offset lesson as §Ch17's arrival assertion:
        # the tile you STAND on is one step off the warp.
        "start": (MapRSE.MOSSDEEP_CITY_GYM, (6, 34)),
        "goal_tiles": [(MapRSE.MOSSDEEP_CITY_GYM, t)
                       for t in ((23, 8), (24, 8), (25, 7), (23, 9), (24, 9))],
        "goal_label": "a tile beside Tate & Liza (23,7)/(24,7)",
        "planner_control": (MapRSE.MOSSDEEP_CITY_GYM, (6, 34), (7, 34)),
        "expected_prefix": None,
    },
}

parser = argparse.ArgumentParser()
parser.add_argument("--maze", default="mossdeep_gym", choices=sorted(MAZES))
parser.add_argument("--list", action="store_true", help="list known mazes and exit")
args = parser.parse_args()

if args.list:
    for name, cfg in MAZES.items():
        print(f"  {name:<16} {len(cfg['maps'])} map(s)   goal: {cfg['goal_label']}")
    raise SystemExit(0)

CFG = MAZES[args.maze]
line = "=" * 100

context.emulator.load_save_state(CFG["anchor"].read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

avatar = get_player_avatar()
print(line)
print(f"WARP MAZE — {args.maze}")
print(line)
print(f"\nanchor: {CFG['anchor'].name}   avatar: "
      f"{MapRSE(tuple(avatar.map_group_and_number)).name} {tuple(avatar.local_coordinates)}")
print(f"goal  : {CFG['goal_label']}")

WARP_TILES: dict = {}


def read_warps(map_enum: MapRSE) -> list[dict]:
    out = []
    try:
        warps = get_map_data(map_enum, (0, 0)).warps
    except Exception as error:  # noqa: BLE001 — a probe reports, it does not crash
        print(f"  !! could not read warps for {map_enum.name}: {type(error).__name__}")
        return out
    for index, warp in enumerate(warps):
        row = {"map": map_enum, "index": index, "tile": tuple(warp.local_coordinates)}
        try:
            destination = warp.destination_location
            row["dest_map"] = MapRSE(tuple(destination.map_group_and_number))
            row["dest_tile"] = tuple(destination.local_position)
        except Exception as error:  # noqa: BLE001
            row["dest_map"] = row["dest_tile"] = None
            row["dest_error"] = type(error).__name__
        out.append(row)
    return out


def can_walk(map_enum: MapRSE, start, end) -> bool:
    """A walk that does NOT step on a warp panel before its destination. See the module docstring."""
    if start == end:
        return True
    try:
        path = calculate_path(get_map_data(map_enum, start), get_map_data(map_enum, end))
    except PathFindingError:
        return False
    except Exception:  # noqa: BLE001 — any refusal means "cannot walk it"
        return False
    panels = WARP_TILES.get(map_enum, set())
    return not any(tuple(waypoint.coordinates) in panels for waypoint in path[:-1])


maze_maps = set(CFG["maps"])
all_warps: list[dict] = []
for map_enum in CFG["maps"] + [CFG["outside"]]:
    all_warps.extend(read_warps(map_enum))
for warp in all_warps:
    WARP_TILES.setdefault(warp["map"], set()).add(warp["tile"])

print("\n" + line)
print("THE WARP TABLE (from ROM)")
print(line)
for map_enum in CFG["maps"]:
    rows = [w for w in all_warps if w["map"] is map_enum]
    same = sum(1 for w in rows if w["dest_map"] is map_enum)
    print(f"\n  {map_enum.name}   {len(rows)} warp(s), {same} of them SAME-MAP panels")
    for warp in rows:
        dest = warp["dest_map"].name if warp["dest_map"] else warp.get("dest_error", "?")
        mark = "  <- PANEL" if warp["dest_map"] is map_enum else ""
        print(f"      warp {warp['index']:>2}  {str(warp['tile']):<9} ->  {dest} {warp['dest_tile']}{mark}")

nodes: set[tuple] = {CFG["start"]}
nodes.update(CFG["goal_tiles"])
for warp in all_warps:
    if warp["map"] in maze_maps or warp["dest_map"] in maze_maps:
        nodes.add((warp["map"], warp["tile"]))
        if warp["dest_map"] is not None:
            nodes.add((warp["dest_map"], warp["dest_tile"]))

walk_edges = {n: set() for n in nodes}
warp_edges = {n: set() for n in nodes}
by_map: dict = {}
for node in nodes:
    by_map.setdefault(node[0], []).append(node)

print("\n" + line)
print("WALK EDGES (panel-safe: a walk that crosses a panel does not count)")
print(line)
for map_enum, map_nodes in sorted(by_map.items(), key=lambda kv: kv[0].name):
    if map_enum not in maze_maps:
        continue
    pairs = 0
    for a in map_nodes:
        for b in map_nodes:
            if a == b:
                continue
            if can_walk(map_enum, a[1], b[1]):
                walk_edges[a].add(b)
                pairs += 1
    print(f"  {map_enum.name:<26} {len(map_nodes):>3} node(s), {pairs:>4} directed walk edge(s)")

for warp in all_warps:
    source = (warp["map"], warp["tile"])
    if source in warp_edges and warp["dest_map"] is not None:
        destination = (warp["dest_map"], warp["dest_tile"])
        if destination in warp_edges:
            warp_edges[source].add(destination)


def search(start, goal_test):
    if start not in walk_edges:
        return None
    queue = deque([(start, [start])])
    seen = {start}
    while queue:
        node, route = queue.popleft()
        if goal_test(node):
            return route
        for nxt in set(walk_edges.get(node, ())) | set(warp_edges.get(node, ())):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, route + [nxt]))
    return None


def render(route):
    return "NO ROUTE" if route is None else "\n          ".join(f"{n[0].name} {n[1]}" for n in route)


print("\n" + line)
print("CONTROLS")
print(line)
ok = True

pc_map, pc_a, pc_b = CFG["planner_control"]
adjacent = can_walk(pc_map, pc_a, pc_b)
print(f"\n  [1] PLANNER CONTROL — {pc_map.name} {pc_a} -> {pc_b}: {'OK' if adjacent else 'FAIL'}")
if not adjacent:
    ok = False

best = None
for goal in CFG["goal_tiles"]:
    route = search(CFG["start"], lambda n, g=goal: n == g)
    print(f"      goal {str(goal[1]):<9} {'unreachable' if route is None else f'{len(route) - 1} hops'}")
    if route is not None and best is None:
        best = (goal, route)
print(f"\n  [2] REACHABILITY CONTROL — {'OK' if best else 'FAIL'}")
if best is None:
    print("      ‼ the game REQUIRES this beat, so suspect the instrument before the game.")
    ok = False

if CFG["expected_prefix"] and best:
    want = CFG["expected_prefix"]
    got = best[1][:len(want)]
    same = got == want
    print("\n  [3] SELF-CHECK — the DRIVEN Aqua Hideout route must still be produced")
    for index, node in enumerate(want):
        actual = got[index] if index < len(got) else None
        shown = f"{actual[0].name} {actual[1]}" if actual else "<route too short>"
        want_shown = f"{node[0].name} {node[1]}"
        print(f"      {'OK  ' if actual == node else 'FAIL'}  want {want_shown:<34} got {shown}")
    if not same:
        ok = False

print("\n" + line)
print("VERDICT")
print(line)
if not ok:
    print("\n  A CONTROL FAILED — route withheld.")
    raise SystemExit(1)
goal, route = best
print(f"\n  ✅ {len(route) - 1} hops to {goal[0].name} {goal[1]}:")
print(f"          {render(route)}")
print("\n  ‼ STATIC. Trainers standing in these rooms are invisible to the planner.")
print(line)
raise SystemExit(0)
