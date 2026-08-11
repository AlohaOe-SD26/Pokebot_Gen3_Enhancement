"""`#24-magmahideout` increment 1 recon: is the TRAVEL LEG to the hideout door plannable,
and — the question nobody has asked yet — can the JAGGED PASS DESCENT reach the door's
approach tile?

WHAT IS ALREADY KNOWN (`12-STORYMODE-DESIGN.md` §Ch15, `probe_magma_anchor.py`):
  * the door is `JAGGED_PASS (16,18)`, its only entry `(16,19)` is cleared by flag 847, and
    from `(16,20)` the door is **2 waypoints** in the anchor's era. VERIFIED.
  * ‼ **but `(16,20)` was never shown to be reachable from where the bot ARRIVES.** Jagged
    Pass is entered from the TOP (Mt. Chimney, tiles (13,5)/(14,5)) and descends by one-way
    ledges. The 2026-08-10 measurement that said the door was unreachable was taken from
    `(14,9)` on a PRE-EMBLEM save, so it measured the guard, not the terrain — which leaves
    the post-Emblem descent UNMEASURED in both directions. That is this probe's headline.

WHAT IT MEASURES, with the build anchor `post_mtpyre.ss1` loaded so NPC state is the real one:
  1. DESCENT — from each plausible arrival tile below the top warps, can the planner reach
     `(16,20)`, and then the door `(16,18)`?
  2. OVERLAND — the connection-only spans the travel leg will ask for in one call each:
     ROUTE122 -> MAUVILLE_CITY (the heal stop) and MAUVILLE_CITY -> ROUTE112 (the cable-car
     station side). These are the spans `_navigate_riding_out` must satisfy.
  3. The MAP-LEVEL graph route, printed for the record.

‼ CONTROLS — a probe that returns FAIL for everything has found a symptom, not a cause
(`08-MISTAKES` 2026-07-31), so every group carries a case that MUST pass:
  * DESCENT control: arrival tile -> the pass's own bottom exit approach `(14,39)`. The bot
    does this walk today in `do_jagged_descent()`, so a FAIL here means the probe is wrong,
    not the map.
  * OVERLAND control: a short intra-map span on ROUTE122 that cannot fail.

‼ AND READ IT NARROWLY. `calculate_path` is static: it reads dual-elevation terrain and
ledges as walls and has called a reachable place unreachable before (KI-24). A FAIL is
"unproven", not "impossible"; a PASS is "worth driving", not "proven". The driven run decides.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch15_travel.py
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

SAVES = pathlib.Path(__file__).resolve().parent / "saves"
ANCHOR = "post_mtpyre.ss1"

_CONNECTION_DIRECTIONS = {"North", "South", "East", "West"}
_DYNAMIC_WARP_MARKER = 127

line = "=" * 88


def span(from_map: MapRSE, start: tuple[int, int], to_map: MapRSE, end: tuple[int, int]) -> str:
    """One `calculate_path` question, reported as the planner answered it."""
    try:
        a = get_map_data(from_map, start)
        b = get_map_data(to_map, end)
        return f"OK, {len(calculate_path(a, b))} waypoints"
    except PathFindingError as error:
        text = str(error)
        # The two failure strings mean DIFFERENT things and the difference decides the fix
        # (§Ch14a): "not on connected maps" = topology; "could not find a path" = blocked.
        kind = "TOPOLOGY" if "connected maps" in text else "BLOCKED"
        return f"FAIL [{kind}] ({text[:90]})"
    except Exception as error:  # noqa: BLE001 - a probe reports, it does not crash
        return f"FAIL ({type(error).__name__}: {str(error)[:80]})"


def build_map_graph():
    """Map-level graph: connection edges both ways, warp edges directed.

    Copied deliberately from `probe_journey_legs.py` rather than imported — that module runs
    its own measurement at import time, and a probe that silently runs another probe is how
    a reader stops being able to tell which numbers came from where.
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
            add(node, "warp", (w.destination_map_group, w.destination_map_number), tuple(w.local_coordinates))
    return node_set, edges


def bfs_route(edges, start, goal):
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


def name_of(m) -> str:
    try:
        return MapRSE(tuple(m)).name
    except ValueError:
        return str(tuple(m))


# --- load the anchor so NPC/flag state is the era we build in -------------------------
context.emulator.load_save_state((SAVES / ANCHOR).read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

JAGGED = MapRSE.JAGGED_PASS
DOOR = (16, 18)
APPROACH = (16, 20)
BOTTOM_EXIT_APPROACH = (14, 39)   # the tile `do_jagged_descent()` walks to today — the control
# Arrival candidates below the two top warps (13,5)/(14,5) -> the bot lands on one of these.
ARRIVALS = [(13, 6), (14, 6), (13, 7), (14, 7), (14, 9)]

print(line)
print(f"1. THE DESCENT — can the pass's TOP reach the door approach? (anchor {ANCHOR})")
print(line)
print(f"  {'from':<10} {'-> ' + str(BOTTOM_EXIT_APPROACH) + ' CONTROL':<34} {'-> ' + str(APPROACH):<34} -> {DOOR}")
descent_ok = False
control_ok = False
for arrival in ARRIVALS:
    ctl = span(JAGGED, arrival, JAGGED, BOTTOM_EXIT_APPROACH)
    app = span(JAGGED, arrival, JAGGED, APPROACH)
    dr = span(JAGGED, arrival, JAGGED, DOOR)
    control_ok = control_ok or ctl.startswith("OK")
    descent_ok = descent_ok or app.startswith("OK")
    print(f"  {str(arrival):<10} {ctl:<34} {app:<34} {dr}")
print(f"  DESCENT CONTROL {'PASS' if control_ok else 'FAIL'} — the known-walked bottom exit"
      f" {'plans' if control_ok else 'does NOT plan, so this probe cannot be trusted'}")
print(f"  ‼ RESULT: the door approach {APPROACH} is"
      f" {'PLANNABLE from the descent' if descent_ok else 'NOT plannable from the descent'}.")

print()
print(line)
print("2. THE OVERLAND SPANS — what the travel leg asks `_navigate_riding_out` for")
print(line)
R122_DOOR_APPROACH = (22, 30)     # below the Mt. Pyre door; Ch14 already stands here
MAUVILLE_PC_APPROACH = (22, 6)    # below the PC door (22,5) — the heal stop
R112_STATION_APPROACH = (28, 28)  # below the cable-car station door (28,27)
CHIMNEY_DESCENT = (21, 40)        # the tile `do_jagged_descent()` uses before warping Down

R112_FIERY_NORTH = (22, 11)       # below Fiery Path's north door (22,10) — `ride_cable_car_to_summit`
LAVARIDGE_PC_APPROACH = (9, 7)    # the south side of the mountain, for the split test

checks = [
    ("CONTROL  R122 short hop", MapRSE.ROUTE122, R122_DOOR_APPROACH, MapRSE.ROUTE122, (22, 31)),
    ("R122 -> MAUVILLE (heal)", MapRSE.ROUTE122, R122_DOOR_APPROACH, MapRSE.MAUVILLE_CITY, MAUVILLE_PC_APPROACH),
    ("MAUVILLE -> R112 stn", MapRSE.MAUVILLE_CITY, MAUVILLE_PC_APPROACH, MapRSE.ROUTE112, R112_STATION_APPROACH),
    # ‼ Route 112 is ONE map split by the volcano: its north half (Route 111 side) and south
    # half (Lavaridge / cable-car side) are joined only by the FIERY PATH tunnel. These four
    # spans decide whether the travel leg must tunnel, or can walk Route 112 end to end —
    # a different chapter route, so it is measured rather than assumed.
    ("MAUVILLE -> R112 north", MapRSE.MAUVILLE_CITY, MAUVILLE_PC_APPROACH, MapRSE.ROUTE112, R112_FIERY_NORTH),
    ("R112 north -> R112 stn", MapRSE.ROUTE112, R112_FIERY_NORTH, MapRSE.ROUTE112, R112_STATION_APPROACH),
    ("LAVARIDGE -> R112 stn", MapRSE.LAVARIDGE_TOWN, LAVARIDGE_PC_APPROACH, MapRSE.ROUTE112, R112_STATION_APPROACH),
    ("R112 stn -> R112 stn", MapRSE.ROUTE112, R112_STATION_APPROACH, MapRSE.ROUTE112, (28, 29)),
]
overland_control = False
for label, m1, t1, m2, t2 in checks:
    result = span(m1, t1, m2, t2)
    if label.startswith("CONTROL"):
        overland_control = result.startswith("OK")
    print(f"  {label:<26} {t1} -> {t2}  {result}")
print(f"  OVERLAND CONTROL {'PASS' if overland_control else 'FAIL'}")

print()
print(line)
print("3. MAP-LEVEL ROUTE (for the record) — MT_PYRE_SUMMIT -> JAGGED_PASS")
print(line)
_nodes, edges = build_map_graph()
route = bfs_route(edges, tuple(MapRSE.MT_PYRE_SUMMIT.value), tuple(MapRSE.JAGGED_PASS.value))
if route is None:
    print("  no route found in the map graph")
else:
    print(f"  {len(route)} hops:")
    for kind, nxt, coords, cur in route:
        print(f"    {name_of(cur):<28} --{kind:<4}{'' if coords is None else str(coords):<9}--> {name_of(nxt)}")
    print("  ‼ The graph does NOT model one-way ledges: any route entering JAGGED_PASS from")
    print("    ROUTE112 (the bottom) is a PHANTOM — the pass cannot be climbed. The build")
    print("    route is fixed by hand through MT_CHIMNEY for exactly this reason.")
print(f"  (the built descent uses MT_CHIMNEY {CHIMNEY_DESCENT} -> warp Down -> JAGGED_PASS)")
print(line)
