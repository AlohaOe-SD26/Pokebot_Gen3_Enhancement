"""§Ch17 increment 0 — recon the Lilycove AQUA HIDEOUT before a line of chapter code exists.

THE CHAPTER, from the decomp (2026-08-11):
  * entrance  `LILYCOVE_CITY (70,5)` -> `AQUA_HIDEOUT_1F` warp 0. ‼ Ch16's harbor scene **SETS**
    `FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1/2_BLOCKING_ENTRANCE` — HIDE flags SET means the two grunts
    are gone and the way in is open. That is the era gate, and it is checked here, not assumed.
  * `AquaHideout_B2F_EventScript_Matt` -> `TRAINER_MATT` -> on defeat runs
    `AquaHideout_B2F_EventScript_SubmarineEscape`, which sets **`FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE`**
    (+ `FLAG_HIDE_LILYCOVE_CITY_AQUA_GRUNTS`). **That flag is the chapter's acceptance.**
  * Matt stands at `AQUA_HIDEOUT_B2F (23,19)`.

‼ WHY THIS PROBE EXISTS, AND WHY IT IS THE SAME INSTRUMENT AS THE MAGMA ONE. B1F is a **WARP-PANEL
MAZE**: of its 25 warps, **21 lead back to B1F itself** (warps 4-24, including a 3x4 panel grid at
x=42/45/48, y=3..17). `calculate_path`'s own docstring says it *"is not able to use warps"*, so a
planner asked to cross B1F can only ever fail — exactly the shape that made KI-56 look like a
strand. The lesson from that chapter is reused rather than re-learned: build the WARP GRAPH, then
search it.

WHAT IT ANSWERS, before any chapter code is written:
  1. is the era right (entrance open, Matt not yet beaten)?
  2. is there a route `LILYCOVE_CITY -> ... -> a tile beside Matt`, and what is the hop sequence?
  3. which of B1F's three B2F warps ((18,1), (12,1), (3,3)) is actually the usable one?

‼ CONTROLS, because a graph search that prints a pretty route is indistinguishable from one that
invented it:
  * NAME CONTROL — every flag name must resolve in `modules.memory._event_flags`. An unknown name
    reads `False` **silently**, which here would read as "entrance still blocked" for ever.
  * ERA CONTROL — on the anchor, the two BLOCKING_ENTRANCE flags must be **set** (Ch16 ran) and
    `TEAM_AQUA_ESCAPED_IN_SUBMARINE` must be **unset** (Ch17 has not). A save failing either is
    the wrong era and every route below is about a different game.
  * PLANNER CONTROL — a trivially adjacent tile on 1F must plan, proving the planner answers at
    all for these maps rather than refusing everything.
  * REACHABILITY CONTROL — the search must reach `AQUA_HIDEOUT_B2F`. The game REQUIRES this beat,
    so a graph that cannot get there is a broken instrument, not a discovery (the lesson from
    KI-57: when a measurement implies the game soft-locks itself, suspect the measurement).

‼ WHAT THIS DOES NOT PROVE. `calculate_path` is STATIC: it cannot see the six Aqua grunts standing
in these corridors (`FLAG_HIDE_AQUA_HIDEOUT_GRUNTS`), and §Ch15 was bitten three times by trusting
a static answer about a dungeon. A route here means "worth driving", never "proven".

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_aqua_hideout_graph.py
Exit: 0 = controls held and a route is reported; 1 = a control failed, verdict withheld.
"""

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
from modules.memory import _event_flags, get_event_flag
from modules.player import get_player_avatar

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_harbor.ss1"

HIDEOUT_MAPS = [
    MapRSE.AQUA_HIDEOUT_1F,
    MapRSE.AQUA_HIDEOUT_B1F,
    MapRSE.AQUA_HIDEOUT_B2F,
]

ENTRANCE = (MapRSE.LILYCOVE_CITY, (70, 5))     # -> AQUA_HIDEOUT_1F warp 0
MATT_TILE = (23, 19)                           # AQUA_HIDEOUT_B2F
MATT_APPROACHES = [(22, 19), (24, 19), (23, 18), (23, 20)]

DONE_FLAG = "TEAM_AQUA_ESCAPED_IN_SUBMARINE"
ENTRANCE_FLAGS = (
    "HIDE_AQUA_HIDEOUT_1F_GRUNT_1_BLOCKING_ENTRANCE",
    "HIDE_AQUA_HIDEOUT_1F_GRUNT_2_BLOCKING_ENTRANCE",
)

line = "=" * 100

context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

avatar = get_player_avatar()
print(line)
print("§Ch17 recon — the Lilycove AQUA HIDEOUT warp graph")
print(line)
print(f"\nanchor: {ANCHOR.name}   avatar: "
      f"{MapRSE(tuple(avatar.map_group_and_number)).name} {tuple(avatar.local_coordinates)}")

ok = True

# ---------------------------------------------------------------- controls 1 + 2
print("\n" + line)
print("CONTROLS (era first — nothing below means anything on the wrong save)")
print(line)

print("\n  [1] NAME CONTROL — every flag name must resolve")
for name in (DONE_FLAG,) + ENTRANCE_FLAGS:
    known = name in _event_flags
    print(f"      {'OK  ' if known else 'FAIL'}  {name}")
    if not known:
        ok = False
if not ok:
    print("      => an unknown name reads False SILENTLY; the era check below would be a lie.")

print("\n  [2] ERA CONTROL — Ch16 done, Ch17 not")
done = get_event_flag(DONE_FLAG)
print(f"      {'OK  ' if not done else 'FAIL'}  {DONE_FLAG} = {done}   (must be False — the beat is unbuilt)")
if done:
    ok = False
for name in ENTRANCE_FLAGS:
    value = get_event_flag(name)
    print(f"      {'OK  ' if value else 'FAIL'}  {name} = {value}   (must be True — HIDE set = grunt gone)")
    if not value:
        ok = False

if not ok:
    print("\n" + line)
    print("A CONTROL FAILED — VERDICT WITHHELD. This is not the §Ch17 era.")
    print(line)
    raise SystemExit(1)


# ---------------------------------------------------------------- graph
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
            row["dest_map"] = None
            row["dest_tile"] = None
            row["dest_error"] = type(error).__name__
        out.append(row)
    return out


def can_walk(map_enum: MapRSE, start, end) -> bool:
    if start == end:
        return True
    try:
        calculate_path(get_map_data(map_enum, start), get_map_data(map_enum, end))
        return True
    except PathFindingError:
        return False
    except Exception:  # noqa: BLE001 — any refusal means "cannot walk it"
        return False


print("\n" + line)
print("THE WARP TABLE (from ROM)")
print(line)
all_warps: list[dict] = []
for map_enum in HIDEOUT_MAPS + [MapRSE.LILYCOVE_CITY]:
    warps = read_warps(map_enum)
    all_warps.extend(warps)
    shown = [w for w in warps if map_enum is not MapRSE.LILYCOVE_CITY or w["dest_map"] in set(HIDEOUT_MAPS)]
    if not shown:
        continue
    print(f"\n  {map_enum.name}" + ("  (only hideout-facing warps shown)" if map_enum is MapRSE.LILYCOVE_CITY else ""))
    for warp in shown:
        dest = warp["dest_map"].name if warp["dest_map"] else warp.get("dest_error", "?")
        same = "  <- SAME-MAP PANEL" if warp["dest_map"] is warp["map"] else ""
        print(f"      warp {warp['index']:>2}  {str(warp['tile']):<9} ->  {dest} {warp['dest_tile']}{same}")

hideout_set = set(HIDEOUT_MAPS)
nodes: set[tuple] = {ENTRANCE}
for warp in all_warps:
    if warp["map"] in hideout_set or warp["dest_map"] in hideout_set:
        nodes.add((warp["map"], warp["tile"]))
        if warp["dest_map"] is not None:
            nodes.add((warp["dest_map"], warp["dest_tile"]))
for approach in MATT_APPROACHES:
    nodes.add((MapRSE.AQUA_HIDEOUT_B2F, approach))

walk_edges = {n: set() for n in nodes}
warp_edges = {n: set() for n in nodes}

by_map: dict[MapRSE, list[tuple]] = {}
for node in nodes:
    by_map.setdefault(node[0], []).append(node)

print("\n" + line)
print("WALK EDGES (calculate_path, same map only — this planner cannot use warps)")
print(line)
for map_enum, map_nodes in sorted(by_map.items(), key=lambda kv: kv[0].name):
    if map_enum is MapRSE.LILYCOVE_CITY:
        continue
    pairs = 0
    for a in map_nodes:
        for b in map_nodes:
            if a == b:
                continue
            if can_walk(map_enum, a[1], b[1]):
                walk_edges[a].add(b)
                pairs += 1
    print(f"  {map_enum.name:<22} {len(map_nodes):>3} node(s), {pairs:>4} directed walk edge(s)")

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


# ---------------------------------------------------------------- controls 3 + 4
print("\n" + line)
print("CONTROLS (instrument)")
print(line)

print("\n  [3] PLANNER CONTROL — a trivially adjacent tile on 1F must plan")
adjacent_ok = can_walk(MapRSE.AQUA_HIDEOUT_1F, (13, 27), (14, 27))
print(f"      {'OK  ' if adjacent_ok else 'FAIL'}  1F (13,27) -> (14,27)")
if not adjacent_ok:
    ok = False

print("\n  [4] REACHABILITY CONTROL — the search MUST reach AQUA_HIDEOUT_B2F")
to_b2f = search(ENTRANCE, lambda n: n[0] is MapRSE.AQUA_HIDEOUT_B2F)
if to_b2f is None:
    print("      FAIL — the game requires this beat, so a graph that cannot get there is broken.")
    ok = False
else:
    print(f"      OK — B2F reached in {len(to_b2f) - 1} hop(s).")

if not ok:
    print("\n" + line)
    print("A CONTROL FAILED — VERDICT WITHHELD.")
    print(line)
    raise SystemExit(1)

# ---------------------------------------------------------------- the route
print("\n" + line)
print("THE ROUTE — Lilycove to Matt")
print(line)

print(f"\n  entrance -> B2F ({len(to_b2f) - 1} hops):")
print(f"          {render(to_b2f)}")

print(f"\n  and on to a tile beside Matt {MATT_TILE}:")
best = None
for approach in MATT_APPROACHES:
    node = (MapRSE.AQUA_HIDEOUT_B2F, approach)
    route = search(ENTRANCE, lambda n, target=node: n == target)
    status = f"{len(route) - 1} hops" if route else "unreachable"
    print(f"      approach {str(approach):<9} {status}")
    if route and best is None:
        best = (approach, route)

if best is None:
    print("\n  ‼ NO approach tile to Matt is reachable in the static graph. Since the game")
    print("    requires this fight, suspect the instrument or a live-only opening before")
    print("    concluding anything (KI-57's lesson).")
else:
    approach, route = best
    print(f"\n  ✅ USE {approach} — {len(route) - 1} hops:")
    print(f"          {render(route)}")

print("\n  ‼ STATIC ONLY. Six Aqua grunts stand in these corridors "
      "(`FLAG_HIDE_AQUA_HIDEOUT_GRUNTS`) and this planner cannot see one of them.")
print(line)
raise SystemExit(0)
