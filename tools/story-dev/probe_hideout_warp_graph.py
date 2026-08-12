"""KI-56, question 2: is there a WALK-OUT of the Magma Hideout at all — and if so, why did the
bot not take it?

‼ WHY THIS EXISTS, AND WHY IT QUESTIONS KI-56's OWN STATED CAUSE. KI-56 records the bot stranded
on `MAGMA_HIDEOUT_1F (25,34)` with "no reachable exit warp", and attributes it to **Strength
boulders resetting on map reload**. Both halves of that were measured, but they were measured
SEPARATELY and the causal link between them was assumed:

  * the reachability failure came from `calculate_path`, which reads the **static ROM layout** and
    (per `probe_ch15_interior`'s own warning) cannot see live object events — so it never saw a
    boulder, in ANY position. A static component split cannot have been caused by boulders.
  * `calculate_path`'s docstring says it outright: *"This function supports paths across several
    maps, but only if they are connected. It is not able to use warps or fly."*

So "no path from 1F (25,34) to 1F (10,34)" does not mean "the bot is trapped". It means **those
two tiles are in different rooms of a map whose rooms are joined by WARPS**, and the planner that
was asked cannot use a warp. The Magma Hideout is exactly that shape: eight maps
(1F, 2F_1R/2R/3R, 3F_1R/2R/3R, 4F) where one floor is several disconnected chambers and you move
between them by going up and back down. §Ch15's own recon walks in via
`1F (10,34) -> warp (20,22) -> 2F_3R`, never touching (25,34).

If a warp route out exists, the fix is ROUTING (and cheap) rather than Escape Rope acquisition
(and expensive). This probe decides which.

WHAT IT BUILDS. A warp graph over the eight hideout maps plus JAGGED_PASS:
  * NODES  — every warp tile, and every tile a warp ARRIVES on.
  * WALK EDGES  — between two nodes on the same map, if `calculate_path` plans between them.
  * WARP EDGES  — from each warp tile to the node it arrives at (read from the ROM's warp table
    via `MapWarp.destination_location`, not from a hand-copied list).
Then it BFSes from the stranded tile to JAGGED_PASS and prints the route.

‼ CONTROLS, because a graph search that returns a pretty route is indistinguishable from one that
invented it, and because this probe is arguing AGAINST an existing written finding — the bar is
higher, not lower:
  * POSITIVE CONTROL (the strongest one available) — the same search, run INBOUND from the
    Jagged Pass door, must find `MAGMA_HIDEOUT_4F`. That route was **actually driven live** by
    §Ch15, so a graph that cannot reproduce a journey we know happened is a broken instrument and
    every other row is noise.
  * REPRODUCTION CONTROL — with WARP EDGES DELETED (walk-only), the search from (25,34) must FAIL
    to reach (10,34). That is precisely KI-56's measurement; reproducing it proves this probe's
    walk edges agree with the earlier finding, so any disagreement about the CONCLUSION cannot be
    blamed on a different collision model.
  * WARP-TABLE CONTROL — the three inbound hops §Ch15 drove must appear as warp edges with the
    destinations §Ch15 recorded. If the ROM warp table disagrees with a driven route, the reader
    is wrong.

‼ WHAT THIS DOES NOT PROVE. `calculate_path` is static: it cannot see the Team Magma grunts, and
it has called a `setmetatile`-sealed tile walkable before (§Ch15, Jagged Pass door). A route found
here means "worth driving", never "proven". The driven run is the proof. It also assumes boulders
do not block the returned route — true only because the returned route must be checked against the
live boulder positions, which the ANSWER section flags explicitly.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_hideout_warp_graph.py
Exit: 0 = controls held and a verdict is reported; 1 = a control failed, verdict withheld.
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

STRANDED_STATE = REPO / "sandbox-pokebot" / "profiles" / "ch16a" / "current_state.ss1"

HIDEOUT_MAPS = [
    MapRSE.MAGMA_HIDEOUT_1F,
    MapRSE.MAGMA_HIDEOUT_2F_1R,
    MapRSE.MAGMA_HIDEOUT_2F_2R,
    MapRSE.MAGMA_HIDEOUT_2F_3R,
    MapRSE.MAGMA_HIDEOUT_3F_1R,
    MapRSE.MAGMA_HIDEOUT_3F_2R,
    MapRSE.MAGMA_HIDEOUT_3F_3R,
    MapRSE.MAGMA_HIDEOUT_4F,
]

STRANDED_TILE = (MapRSE.MAGMA_HIDEOUT_1F, (25, 34))
HIDEOUT_DOOR_1F = (MapRSE.MAGMA_HIDEOUT_1F, (10, 34))   # the warp back to Jagged Pass
JAGGED_DOOR = (MapRSE.JAGGED_PASS, (16, 18))            # the hideout entrance, outside

#: The three hops §Ch15 actually DROVE, for the warp-table control.
DRIVEN_INBOUND = [
    ((MapRSE.MAGMA_HIDEOUT_1F, (20, 22)), MapRSE.MAGMA_HIDEOUT_2F_3R),
    ((MapRSE.MAGMA_HIDEOUT_2F_3R, (16, 13)), MapRSE.MAGMA_HIDEOUT_3F_3R),
    ((MapRSE.MAGMA_HIDEOUT_3F_3R, (16, 21)), MapRSE.MAGMA_HIDEOUT_4F),
]

context.emulator.load_save_state(STRANDED_STATE.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

line = "=" * 100


# ------------------------------------------------------------------ graph construction
def read_warps(map_enum: MapRSE) -> list[dict]:
    """Every warp on `map_enum`, with the node it arrives at, read from the ROM warp table."""
    out = []
    try:
        warps = get_map_data(map_enum, (0, 0)).warps
    except Exception as error:  # noqa: BLE001 — a probe reports, it does not crash
        print(f"  !! could not read warps for {map_enum.name}: {type(error).__name__}: {error}")
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
            row["dest_error"] = f"{type(error).__name__}: {str(error)[:60]}"
        out.append(row)
    return out


def can_walk(map_enum: MapRSE, start: tuple[int, int], end: tuple[int, int]) -> bool:
    if start == end:
        return True
    try:
        calculate_path(get_map_data(map_enum, start), get_map_data(map_enum, end))
        return True
    except PathFindingError:
        return False
    except Exception:  # noqa: BLE001
        return False


print(line)
print("KI-56 / probe_hideout_warp_graph — is there a WALK-OUT of the Magma Hideout?")
print(line)

print("\n1. THE WARP TABLE (read from ROM, per map)")
print("-" * 100)
all_warps: list[dict] = []
for map_enum in HIDEOUT_MAPS + [MapRSE.JAGGED_PASS]:
    warps = read_warps(map_enum)
    all_warps.extend(warps)
    if map_enum is MapRSE.JAGGED_PASS:
        warps = [w for w in warps if w["dest_map"] in set(HIDEOUT_MAPS)]
        if not warps:
            continue
        print(f"\n  {map_enum.name}  (only hideout-facing warps shown)")
    else:
        print(f"\n  {map_enum.name}")
    for warp in warps:
        dest = warp["dest_map"].name if warp["dest_map"] else warp.get("dest_error", "?")
        print(f"      warp {warp['index']}  at {str(warp['tile']):<10} ->  {dest} {warp['dest_tile']}")

# Nodes of interest: every warp tile, plus every arrival tile, plus the two anchors.
nodes: set[tuple[MapRSE, tuple[int, int]]] = set()
for warp in all_warps:
    if warp["map"] in set(HIDEOUT_MAPS) or warp["dest_map"] in set(HIDEOUT_MAPS):
        nodes.add((warp["map"], warp["tile"]))
        if warp["dest_map"] is not None:
            nodes.add((warp["dest_map"], warp["dest_tile"]))
nodes.add(STRANDED_TILE)
nodes.add(JAGGED_DOOR)

# WALK edges (same map) and WARP edges (across maps).
walk_edges: dict[tuple, set[tuple]] = {node: set() for node in nodes}
warp_edges: dict[tuple, set[tuple]] = {node: set() for node in nodes}

by_map: dict[MapRSE, list[tuple]] = {}
for node in nodes:
    by_map.setdefault(node[0], []).append(node)

print("\n2. WALK EDGES (calculate_path, same map only — this planner cannot use warps)")
print("-" * 100)
for map_enum, map_nodes in sorted(by_map.items(), key=lambda kv: kv[0].name):
    if map_enum is MapRSE.JAGGED_PASS:
        continue  # outdoors; we only need to arrive there
    pairs = 0
    for a in map_nodes:
        for b in map_nodes:
            if a is b or a == b:
                continue
            if can_walk(map_enum, a[1], b[1]):
                walk_edges[a].add(b)
                pairs += 1
    print(f"  {map_enum.name:<24} {len(map_nodes)} node(s), {pairs} directed walk edge(s)")

for warp in all_warps:
    source = (warp["map"], warp["tile"])
    if source in warp_edges and warp["dest_map"] is not None:
        destination = (warp["dest_map"], warp["dest_tile"])
        if destination in warp_edges:
            warp_edges[source].add(destination)


def search(start: tuple, goal_map: MapRSE, use_warps: bool = True) -> list[tuple] | None:
    """BFS over walk + (optionally) warp edges. Returns the node route, or None."""
    if start not in walk_edges:
        return None
    queue = deque([(start, [start])])
    seen = {start}
    while queue:
        node, route = queue.popleft()
        if node[0] is goal_map:
            return route
        neighbours = set(walk_edges.get(node, ()))
        if use_warps:
            neighbours |= set(warp_edges.get(node, ()))
        for nxt in neighbours:
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, route + [nxt]))
    return None


def render(route: list[tuple] | None) -> str:
    if route is None:
        return "NO ROUTE"
    return "\n          ".join(f"{node[0].name} {node[1]}" for node in route)


# ------------------------------------------------------------------ controls
print("\n" + line)
print("CONTROLS")
print(line)
ok = True

print("\n  [1] POSITIVE CONTROL — the ASCENT §Ch15 actually drove, (25,34) -> 4F, must be findable")
print("      ‼ the control is deliberately the ASCENT, not the whole inbound journey. The first")
print("        leg, 1F (10,34) -> (25,34), is opened by two STRENGTH PUSHES")
print("        (`MAGMA_HIDEOUT_1F_PUSHES`), and no static planner can model a push — asking the")
print("        graph to reproduce it would fail for a reason that says nothing about the graph.")
print("        From (25,34) upward the driven route is plain walking and warps, so it MUST appear.")
ascent = search(STRANDED_TILE, MapRSE.MAGMA_HIDEOUT_4F, use_warps=True)
if ascent is None:
    print("      FAIL — the graph cannot reproduce a journey that demonstrably happened.")
    print("      => the instrument is broken; every verdict below is noise.")
    ok = False
else:
    print(f"      OK — reached MAGMA_HIDEOUT_4F in {len(ascent) - 1} hop(s):")
    print(f"          {render(ascent)}")

print("\n  [2] REPRODUCTION CONTROL — walk-only, (25,34) must NOT reach the Jagged Pass exit")
walk_only = search(STRANDED_TILE, MapRSE.JAGGED_PASS, use_warps=False)
direct = can_walk(MapRSE.MAGMA_HIDEOUT_1F, STRANDED_TILE[1], HIDEOUT_DOOR_1F[1])
print(f"      walk-only route to JAGGED_PASS : {'FOUND (unexpected)' if walk_only else 'none'}")
print(f"      direct 1F (25,34) -> (10,34)   : {'plans (unexpected)' if direct else 'FAILS — matches KI-56'}")
if walk_only is not None or direct:
    print("      FAIL — this probe's walk edges disagree with KI-56's measurement.")
    ok = False
else:
    print("      OK — KI-56's measurement reproduced exactly.")

print("\n  [3] WARP-TABLE CONTROL — the three driven inbound hops must be in the ROM warp table")
for source, expected in DRIVEN_INBOUND:
    found = sorted({node[0].name for node in warp_edges.get(source, set())})
    agree = expected.name in found
    print(f"      {'OK  ' if agree else 'FAIL'}  {source[0].name} {source[1]} -> expected {expected.name}, table says {found or '[]'}")
    if not agree:
        ok = False

if not ok:
    print("\n" + line)
    print("A CONTROL FAILED — VERDICT WITHHELD.")
    print(line)
    raise SystemExit(1)

# ------------------------------------------------------------------ the answer
print("\n" + line)
print("VERDICT")
print(line)

out = search(STRANDED_TILE, MapRSE.JAGGED_PASS, use_warps=True)

# The full reachable set, so the verdict shows WHAT IS and IS NOT reachable rather than one
# bare yes/no. A "no route" that also reported nothing else reachable would just be a broken BFS.
reachable = {STRANDED_TILE}
queue = deque([STRANDED_TILE])
while queue:
    node = queue.popleft()
    for nxt in set(walk_edges.get(node, ())) | set(warp_edges.get(node, ())):
        if nxt not in reachable:
            reachable.add(nxt)
            queue.append(nxt)
print(f"\n  REACHABLE SET from {STRANDED_TILE[0].name} {STRANDED_TILE[1]} "
      f"— {len(reachable)} of {len(nodes)} node(s):")
for node in sorted(nodes, key=lambda n: (n[0].name, n[1])):
    mark = "reachable" if node in reachable else "  ---    UNREACHABLE"
    print(f"      {mark:<12} {node[0].name} {node[1]}")

print(f"\n  From the STRANDED tile {STRANDED_TILE[0].name} {STRANDED_TILE[1]}, using warps:")
if out is None:
    print("      NO ROUTE OUT EXISTS in the static warp graph.")
    print("      => KI-56's cause is CONFIRMED and its option 2 (a return-route study) is now")
    print("         formally DEAD: the bot can reach every chamber of the hideout EXCEPT the")
    print("         44-tile entrance pocket that holds the exit, because the two Strength")
    print("         pushes that merged them reset on map reload and both push-from tiles")
    print("         ((7,23) and (6,22)) are inside the pocket. There is no walk-out.")
    print("      => the fix must leave the map WITHOUT walking: Escape Rope.")
else:
    print(f"      A WALK-OUT EXISTS — {len(out) - 1} hop(s):")
    print(f"          {render(out)}")
    print("\n      => the strand is a ROUTING GAP, not topology. `calculate_path` cannot use")
    print("         warps, so a same-map request across two warp-joined rooms can only fail.")
    print("\n      ‼ NOT YET PROVEN: this is the STATIC layout. Before relying on it, the route")
    print("         must be driven, and checked against the live Strength-boulder positions")
    print("         (5,22)/(7,22)/(6,23) — KI-56 measured those reset, and this planner is blind")
    print("         to them.")

# ------------------------------------------------------------------ the way out
# ‼ THE DUNGEON SUPPLIES ITS OWN ESCAPE. `MagmaHideout_3F_3R/map.json` places an ITEM BALL
# holding an Escape Rope at (9,19) — inside the very room §Ch15 already walks through, and (per
# the reachable set above) still reachable from the stranded tile. That is almost certainly why
# Game Freak could ship a one-way boulder puzzle here at all.
print("\n" + line)
print("THE WAY OUT — the Escape Rope the dungeon itself provides")
print(line)

ITEM_BALL_MAP = MapRSE.MAGMA_HIDEOUT_3F_3R
ITEM_BALL_TILE = (9, 19)
#: ‼ THE DECOMP MISSPELLS THIS FLAG — "ECAPE", not "ESCAPE" — and `modules/data/event_flags/
#: emerald.txt` carries the typo through as flag 1059. The correctly-spelled name does NOT
#: exist, and an unknown flag name reads False SILENTLY, which is indistinguishable from
#: "the ball is still there". Spelled right, this check would be a permanent lie.
ITEM_BALL_FLAG = "ITEM_MAGMA_HIDEOUT_3F_3R_ECAPE_ROPE"

print(f"\n  item ball : {ITEM_BALL_MAP.name} {ITEM_BALL_TILE}  (Escape Rope)")
try:
    from modules.memory import _event_flags, get_event_flag

    known = ITEM_BALL_FLAG in _event_flags
    taken = get_event_flag(ITEM_BALL_FLAG)
    print(f"  flag      : {ITEM_BALL_FLAG}")
    print(f"              name resolves: {known}   (an unknown name reads False SILENTLY)")
    if not known:
        print("              !! NAME CONTROL FAILED — this flag reading is meaningless.")
    else:
        print(f"              already taken on the stranded save: {taken}")
except Exception as error:  # noqa: BLE001
    print(f"  flag      : unreadable ({type(error).__name__}: {error})")

# You cannot stand ON an item ball — it is an object event. Reach a tile beside it and press A.
approaches = [(9, 20), (9, 18), (8, 19), (10, 19)]
reachable_3f3r = [node for node in reachable if node[0] is ITEM_BALL_MAP]
print(f"\n  reachable 3F_3R nodes to start from: {[n[1] for n in reachable_3f3r] or 'NONE'}")
if not reachable_3f3r:
    print("      !! 3F_3R is not reachable from the stranded tile — the item ball is no use.")
else:
    for approach in approaches:
        hits = [node[1] for node in reachable_3f3r if can_walk(ITEM_BALL_MAP, node[1], approach)]
        verdict = f"reachable from {hits}" if hits else "NOT reachable from any reachable node"
        print(f"      approach tile {str(approach):<9} {verdict}")

print("\n  => IF an approach tile is reachable, the stranded bot can walk to the Escape Rope,")
print("     pick it up, and use it — landing at JAGGED_PASS (16,19), proven separately by")
print("     `probe_escape_warp.py`. That is a self-contained, faithful, no-detour escape.")
print("  ‼ STATIC ONLY. The driven run is the proof.")

print("\n" + line)
raise SystemExit(0)
