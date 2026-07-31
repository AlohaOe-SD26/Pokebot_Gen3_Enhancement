"""#24-journey / KI-39: does DECOMPOSING a journey at its warps make every leg pathable?

THE QUESTION. KI-39 measured that `navigate_to_anywhere` cannot reach ROUTE110 / ROUTE116 /
ROUTE111 from Mauville, and attributed it to `calculate_path` "only spanning directly-
connected maps". ‼ That attribution is WRONG on its face — `map_path.py` assigns every
edge-connected map a global offset and a shared `level`, and its own docstring says "supports
paths across several maps, but only if they are connected". So the real failure has to be one
of two DIFFERENT things, and they need opposite fixes:

  (a) the trip genuinely needs a WARP (a gate building, a tunnel, a cave passage), which
      `calculate_path` cannot cross and `plan()` never supplies because the whole overworld
      is one region and the same-region branch is taken; or
  (b) the maps ARE connection-joined but no walkable tile path exists (the Go-Goggles desert
      splitting Route 111; the dual-elevation bridges `calculate_path` reads as walls).

THE EXPERIMENT. Build a MAP-level graph (connection edges + warp edges — the granularity
`WarpGraph.plan` throws away by collapsing to regions), BFS it, then split the route at its
warps. Between two consecutive warps every hop is a plain connection walk, i.e. exactly what
`calculate_path` is built for. So the journey decomposes into:

    GOTO(warp1.from_map, warp1.from_coords) -> [warp fires] -> GOTO(warp2...) -> ... -> GOTO(target)

and each GOTO is measured with THE SAME `calculate_path` the production path uses. If every
leg passes where the direct call fails, the executor is just "walk the legs" and #24-journey
is a planner change, not a pathfinder change.

‼ WHY THIS IS NOT THE REFUTED GATEWAY IDEA. `probe_counter_gateway.py` (refuted 2026-07-30)
routed to a hand-picked gateway with `navigate_to_anywhere`, which took the SAME broken
same-region branch and failed identically. This does not call `navigate_to_anywhere` at all —
it plans over the map graph itself and measures the individual legs.

Run: PYTHONUTF8=1 py -3.12 tools/story-dev/probe_journey_legs.py
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
context.bot_mode = "Manual"

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar

SAVES = REPO / "tools" / "story-dev" / "saves"

_CONNECTION_DIRECTIONS = {"North", "South", "East", "West"}
_DYNAMIC_WARP_MARKER = 127


def name_of(m: tuple) -> str:
    try:
        return MapRSE(tuple(m)).name
    except ValueError:
        return str(tuple(m))


# ---------------------------------------------------------------------------
# The MAP-level graph (this is the thing WarpGraph.plan collapses away)
# ---------------------------------------------------------------------------
def build_map_graph():
    """nodes -> list of (kind, to_map, from_coords|None).

    `kind` is 'conn' or 'warp'. Connection edges are added BOTH ways (you can always
    walk back the way you came, even if only one header declares it). Warp edges are
    directed — a return trip only exists if the far side declares its own warp.
    """
    nodes = []
    for member in MapRSE:
        try:
            get_map_data(member.value, (0, 0))
        except (ValueError, KeyError):
            continue
        nodes.append(tuple(member.value))
    node_set = set(nodes)

    edges: dict[tuple, list[tuple]] = {}

    def add(a, kind, b, coords):
        if a in node_set and b in node_set:
            edges.setdefault(a, []).append((kind, b, coords))

    for node in nodes:
        md = get_map_data(node, (0, 0))
        for c in md.connections:
            if c.direction not in _CONNECTION_DIRECTIONS:
                continue
            dest = (c.destination_map_group, c.destination_map_number)
            add(node, "conn", dest, None)
            add(dest, "conn", node, None)
        for w in md.warps:
            if w.destination_map_group == _DYNAMIC_WARP_MARKER and w.destination_map_number == _DYNAMIC_WARP_MARKER:
                continue
            dest = (w.destination_map_group, w.destination_map_number)
            add(node, "warp", dest, tuple(w.local_coordinates))
    return node_set, edges


def bfs_route(edges, start, goal):
    """Fewest-hop map route as a list of (kind, to_map, from_coords)."""
    if start == goal:
        return []
    seen = {start}
    q = deque([(start, [])])
    while q:
        cur, path = q.popleft()
        for kind, nxt, coords in edges.get(cur, []):
            if nxt in seen:
                continue
            new = path + [(kind, nxt, coords, cur)]
            if nxt == goal:
                return new
            seen.add(nxt)
            q.append((nxt, new))
    return None


def route_to_legs(route, target_map, target_coords):
    """Split the map route at its WARPS.

    Between warps every hop is a connection walk, which `calculate_path` handles natively,
    so the only tiles we must name are the warp tiles themselves plus the final target.
    """
    legs = []
    for kind, to_map, coords, from_map in route:
        if kind == "warp":
            legs.append(("walk-to-warp", from_map, coords, to_map))
    legs.append(("walk-to-target", target_map, target_coords, None))
    return legs


def try_path(src_map, src_coords, dst_map, dst_coords):
    try:
        p = calculate_path((src_map, src_coords), (dst_map, dst_coords))
        return True, f"OK {len(p)} waypoints"
    except PathFindingError as e:
        return False, f"PathFindingError: {str(e)[:110]}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:110]}"


def same_level(a, b):
    """Are the two maps in the same connection component, per map_path's own model?"""
    try:
        from modules.map_path import _get_maps

        maps = _get_maps()
        return maps[tuple(a)].level == maps[tuple(b)].level
    except Exception as e:  # noqa: BLE001
        return f"<{type(e).__name__}: {e}>"


# ---------------------------------------------------------------------------
CASES = [
    # KI-39's own table, measured from `rocksmash_taught.ss1` (Mauville 32,15).
    ("ROUTE117 (31,16) — directly connected  [KI-39: OK 72 wp]", MapRSE.ROUTE117, (31, 16)),
    ("ROUTE110 (12,60) — KI-39: FAIL", MapRSE.ROUTE110, (12, 60)),
    ("ROUTE116 (11,7)  — KI-39: FAIL", MapRSE.ROUTE116, (11, 7)),
    ("ROUTE111 (25,55) — KI-39: FAIL (desert split)", MapRSE.ROUTE111, (25, 55)),
    # THE ONE THAT IS KILLING RUNS: the counter chain names Machop @ FIERY_PATH and
    # cannot act because this trip does not plan.
    ("FIERY_PATH (18,19) — the counter the ladder names", MapRSE.FIERY_PATH, (18, 19)),
]


def main() -> int:
    state = SAVES / "rocksmash_taught.ss1"
    context.emulator.load_save_state(state.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    avatar = get_player_avatar()
    here = tuple(avatar.map_group_and_number)
    here_coords = tuple(avatar.local_coordinates)
    print(f"STATE  {state.name}")
    print(f"PLAYER {name_of(here)} {here_coords}\n")

    print("Building the map-level graph (connections + warps)...")
    node_set, edges = build_map_graph()
    n_conn = sum(1 for vs in edges.values() for k, *_ in vs if k == "conn")
    n_warp = sum(1 for vs in edges.values() for k, *_ in vs if k == "warp")
    print(f"  {len(node_set)} maps, {n_conn} connection edges, {n_warp} warp edges\n")

    for label, target, coords in CASES:
        tmap = tuple(target.value)
        print("=" * 78)
        print(label)
        print("-" * 78)
        print(f"  same connection component (map_path level)? {same_level(here, tmap)}")

        ok, why = try_path(here, here_coords, tmap, coords)
        print(f"  DIRECT calculate_path       : {'PASS' if ok else 'FAIL'}  {why}")
        if ok:
            print("  -> direct works; no journey planning needed for this pair.\n")
            continue

        route = bfs_route(edges, here, tmap)
        if route is None:
            print("  MAP-LEVEL BFS               : no route at all (graph gap)\n")
            continue
        hops = " -> ".join(f"{name_of(m)}[{k}]" for k, m, _c, _f in route)
        print(f"  MAP-LEVEL BFS ({len(route)} hops)      : {name_of(here)} -> {hops}")

        legs = route_to_legs(route, tmap, coords)
        print(f"  DECOMPOSED INTO {len(legs)} LEG(S) (split at warps):")
        cursor_map, cursor_coords = here, here_coords
        all_ok = True
        for i, (kind, lmap, lcoords, lands_on) in enumerate(legs, 1):
            ok_leg, why_leg = try_path(cursor_map, cursor_coords, lmap, lcoords)
            arrow = f" -> lands on {name_of(lands_on)}" if lands_on else ""
            print(f"    leg {i} [{kind:<14}] {name_of(cursor_map)}{cursor_coords} "
                  f"=> {name_of(lmap)}{lcoords}{arrow}")
            print(f"            {'PASS' if ok_leg else 'FAIL'}  {why_leg}")
            if not ok_leg:
                all_ok = False
                break
            # After a warp leg we are on the far side; after the final leg we are done.
            if lands_on is not None:
                # Arrival tile = the destination warp's own coords; approximate with the
                # far map's matching warp, which is what the game actually does.
                cursor_map = tuple(lands_on)
                cursor_coords = None
                try:
                    dest_warps = get_map_data(cursor_map, (0, 0)).warps
                    cursor_coords = tuple(dest_warps[0].local_coordinates) if dest_warps else (0, 0)
                except Exception:  # noqa: BLE001
                    cursor_coords = (0, 0)
        print(f"  VERDICT: {'ALL LEGS PATH' if all_ok else 'a leg failed — see above'}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
