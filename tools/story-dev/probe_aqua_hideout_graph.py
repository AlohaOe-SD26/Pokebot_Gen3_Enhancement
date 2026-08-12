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


#: map -> {every warp tile on it}, filled in from the ROM warp table below. Consulted by
#: `can_walk` so the graph never proposes a walk that steps on a panel en route.
WARP_TILES: dict = {}


def can_walk(map_enum: MapRSE, start, end) -> bool:
    """Is there a walk from `start` to `end` that does NOT step on a warp panel on the way?

    ‼‼ THE PANEL CHECK IS THE WHOLE POINT, AND IT WAS PAID FOR BY A DRIVEN RUN. `calculate_path`
    treats a warp panel as ordinary walkable ground. A first version of this probe returned a
    route whose leg `(42,13) -> (48,13)` walks straight through `(45,13)` — itself a panel — so
    the live bot was teleported to `(45,9)` mid-leg and the chapter failed one hop later with
    "Could not find a path from (45/9)". The graph was proposing walks the bot cannot perform.

    ‼ AND `Waypoint.is_warp` CANNOT BE USED FOR THIS, which cost a second attempt. In
    `map_path.unroll_path` the warp branch is guarded by `len(result) == 0`, so **`is_warp` is set
    only on the FINAL waypoint** — an intermediate panel is reported as ordinary ground by that
    flag too. The check therefore compares each waypoint's COORDINATES against the map's own warp
    table (`WARP_TILES`, read from ROM above).

    The destination is allowed to be a panel — firing it is the point of the hop — so only the
    waypoints before the last are tested."""
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

for warp in all_warps:
    WARP_TILES.setdefault(warp["map"], set()).add(warp["tile"])

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

# ---------------------------------------------------------------- side objectives
# ‼ THE MASTER BALL (`#24-masterball`). `AquaHideout_B1F/map.json` puts it at (15,9) — and puts
# **two ELECTRODE DISGUISED AS ITEM BALLS** immediately beside it at (16,9) and (16,10)
# (`AquaHideout_B1F_EventScript_Electrode1/2`). ‼ Their hide flags are re-cleared by
# `AquaHideout_B1F_OnResume`, so running from one brings it straight back.
#
# ‼‼ AND THE THING THAT WILL DECIDE THIS: those two Electrode are OBJECTS standing on tiles, and
# this probe runs with B1F **not loaded**, so `calculate_path` cannot see them. Any approach that
# routes through (16,9)/(16,10) will read as walkable here and FAIL live. So the useful answer is
# not "is the ball reachable" but "is it reachable from the WEST/NORTH side, away from them".
print("\n" + line)
print("SIDE OBJECTIVES — the item balls, and whether we can get at them")
print(line)

ITEM_BALLS = [
    ((15, 9), "MASTER BALL", "ITEM_AQUA_HIDEOUT_B1F_MASTER_BALL"),
    ((15, 10), "Nugget", "ITEM_AQUA_HIDEOUT_B1F_NUGGET"),
    ((29, 12), "Max Elixir", "ITEM_AQUA_HIDEOUT_B1F_MAX_ELIXIR"),
]
ELECTRODES = {(16, 9), (16, 10)}

for ball_tile, label, flag in ITEM_BALLS:
    print(f"\n  {label} at B1F {ball_tile}   flag={flag}")
    known = flag in _event_flags
    taken = get_event_flag(flag) if known else None
    print(f"      flag resolves: {known}   already taken: {taken}")
    if not known:
        print("      ‼ name does not resolve — it would read False for ever. Fix before use.")
    for dx, dy in ((-1, 0), (0, -1), (1, 0), (0, 1)):
        approach = (ball_tile[0] + dx, ball_tile[1] + dy)
        if approach in ELECTRODES:
            print(f"      approach {str(approach):<9} ‼ AN ELECTRODE STANDS HERE — not a tile, a battle")
            continue
        if any(approach == other for other, _, _ in ITEM_BALLS):
            print(f"      approach {str(approach):<9} another ITEM BALL stands here (an object, not floor)")
            continue
        # Which reachable node can walk to it?
        hits = [n[1] for n in nodes
                if n[0] is MapRSE.AQUA_HIDEOUT_B1F and can_walk(MapRSE.AQUA_HIDEOUT_B1F, n[1], approach)]
        print(f"      approach {str(approach):<9} walkable from B1F node(s): {hits or 'NONE'}")

print("\n  ‼ Read the MASTER BALL row narrowly: an approach that is 'walkable' here may still be")
print("    blocked live by an Electrode, and picking the ball up may mean fighting one. The")
print("    driven run is the proof.")

# ‼‼ THE MASTER BALL IS REACHED THROUGH THE NUGGET, NOT AROUND THE ELECTRODE. The four tiles form
# a 2x2 block: (15,9) Master Ball / (16,9) Electrode 1 / (15,10) Nugget / (16,10) Electrode 2.
# Both of the Master Ball's free neighbours are unreachable — but `(15,11)` reaches the NUGGET,
# and **an item ball is an object that DISAPPEARS when collected**. Take the Nugget, step onto the
# tile it vacated, and the Master Ball is then directly above. No Electrode ever needs to be faced,
# because facing Up from (15,10) targets (15,9), never (16,10).
print("\n" + line)
print("THE WAY TO THE MASTER BALL — via the Nugget's tile")
print(line)
STAGING = (MapRSE.AQUA_HIDEOUT_B1F, (23, 10))
route = search(ENTRANCE, lambda n: n == STAGING)
if route is None:
    print(f"\n  ‼ {STAGING[0].name} {STAGING[1]} is NOT reachable from the entrance — the plan fails")
    print("    at its first step. Re-derive before building anything on it.")
else:
    print(f"\n  entrance -> the staging node {STAGING[1]}: {len(route) - 1} hops")
    print(f"          {render(route)}")
    print(f"\n  then, on foot: {STAGING[1]} -> (15,11) -> face Up, take the NUGGET (15,10)")
    print( "                 -> step onto (15,10) -> face Up, take the MASTER BALL (15,9)")
    print(f"\n  sanity: (23,10) -> (15,11) walkable? {can_walk(MapRSE.AQUA_HIDEOUT_B1F, (23, 10), (15, 11))}")
    print( "  ‼ The second half CANNOT be verified statically: (15,10) only becomes standable")
    print( "    once the Nugget object is gone, and this planner sees the map with it still there.")

    # And the way BACK: the detour is only usable if the chapter can rejoin the Matt line.
    back = search(STAGING, lambda n: n == (MapRSE.AQUA_HIDEOUT_B2F, (24, 19)))
    print(f"\n  REJOIN — {STAGING[1]} onward to Matt's approach (24,19): "
          f"{'NO ROUTE' if back is None else f'{len(back) - 1} hops'}")
    if back is not None:
        print(f"          {render(back)}")
    else:
        print("      ‼ the detour would STRAND the chapter. Do not build it without a way back.")

    # Where the detour leaves the main line, so the chapter can be spliced rather than rewritten.
    main = [n[1] for n in (to_b2f or []) if n[0] is MapRSE.AQUA_HIDEOUT_B1F]
    detour = [n[1] for n in route if n[0] is MapRSE.AQUA_HIDEOUT_B1F]
    shared = []
    for a, b in zip(main, detour):
        if a != b:
            break
        shared.append(a)
    print(f"\n  the detour shares this B1F prefix with the Matt route: {shared}")
    print(f"  => splice the detour in after B1F {shared[-1] if shared else '(nothing)'}")
print(line)
raise SystemExit(0)
