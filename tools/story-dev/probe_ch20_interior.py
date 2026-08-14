"""§Ch20 — the AREA ATLAS for the SEAFLOOR CAVERN INTERIOR (rooms 1-9), measured not recalled.

`probe_ch20_topology.py` measured the way IN (Route 128 → dive → the entrance) and that leg is
driven. This probe measures the part nobody has looked at: **the interior**, which is what §Ch20
still has to cross.

Everything here is read through the normal reader (`modules.map.get_map_data`,
`get_map_all_tiles`) and the normal planner (`modules.map_path.calculate_path`) — the same code the
chapter will use, so a route that fails here fails for the chapter too.

QUESTIONS
  1. The WARP GRAPH: every warp in every cavern map, resolved to its destination map + arrival tile.
     Which rooms are dead ends? What is the traversal order from the entrance?
  2. Per room: size, walkable tile count, and how many connected COMPONENTS the walkable tiles form
     (‼ §Ch18's gym was six disconnected islands and every plain A* was right to say "no path" —
     a component count is the cheapest way to see that coming).
  3. STRENGTH BOULDERS and other object events per room — the thing a static route cannot model.
  4. Can `calculate_path` route, WITHIN each room, from that room's arrival tile to each of its
     other warp tiles? This is the question that decides whether §Ch20 is a route or a puzzle.

CONTROLS (so a null result is attributable)
  * Every source tile is asserted walkable before use — ‼ KI-60: `calculate_path` never validates
    its SOURCE, so a "path" out of solid rock reports OK and means nothing.
  * A NEGATIVE control: a path into a known collision tile, which must raise.
  * ‼ KI-74: these are STATIC ROM layouts. The cavern is not known to `setmetatile` itself, but the
    boulders are OBJECT events and DO move, so an in-room route is only valid for the boulder
    positions at the time it is planned. That caveat is printed with the results, not hidden.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch20_interior.py
Exit: 0 always (measurement probe, not a gate).
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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar

BAR = "=" * 100

ROOMS = [
    MapRSE.SEAFLOOR_CAVERN_ENTRANCE,
    MapRSE.SEAFLOOR_CAVERN_ROOM1,
    MapRSE.SEAFLOOR_CAVERN_ROOM2,
    MapRSE.SEAFLOOR_CAVERN_ROOM3,
    MapRSE.SEAFLOOR_CAVERN_ROOM4,
    MapRSE.SEAFLOOR_CAVERN_ROOM5,
    MapRSE.SEAFLOOR_CAVERN_ROOM6,
    MapRSE.SEAFLOOR_CAVERN_ROOM7,
    MapRSE.SEAFLOOR_CAVERN_ROOM8,
    MapRSE.SEAFLOOR_CAVERN_ROOM9,
]


def head(t):
    print(f"\n{BAR}\n{t}\n{BAR}\n")


def walkable(t) -> bool:
    return t.collision == 0


def grid_of(m):
    return {tuple(t.local_position): t for t in get_map_all_tiles(get_map_data(m, (0, 0)))}


avatar = get_player_avatar()
print(f"anchor post_dive.ss1 — avatar {MapRSE(tuple(avatar.map_group_and_number)).name} "
      f"{tuple(avatar.local_coordinates)} (‼ NOT in the cavern; maps are read by ENUM)")

head("1. THE WARP GRAPH — where each room actually connects")

graph: dict[str, list] = {}
for m in ROOMS:
    md = get_map_data(m, (0, 0))
    entries = []
    for w in md.warps:
        dest = w.destination_location
        try:
            dest_name = MapRSE(tuple(dest.map_group_and_number)).name
        except ValueError:
            dest_name = str(tuple(dest.map_group_and_number))
        entries.append((tuple(w.local_coordinates), dest_name, tuple(dest.local_position)))
    graph[m.name] = entries
    print(f"  {m.name}  ({len(entries)} warp(s))")
    for src, dn, dc in entries:
        print(f"      {str(src):<10} -> {dn} {dc}")

# Which rooms are reachable from the entrance, following warps only?
seen = {MapRSE.SEAFLOOR_CAVERN_ENTRANCE.name}
frontier = [MapRSE.SEAFLOOR_CAVERN_ENTRANCE.name]
order = []
while frontier:
    cur = frontier.pop(0)
    order.append(cur)
    for _src, dn, _dc in graph.get(cur, []):
        if dn.startswith("SEAFLOOR_CAVERN") and dn not in seen:
            seen.add(dn)
            frontier.append(dn)
print(f"\n  rooms reachable from the ENTRANCE by warps alone ({len(seen)}): {order}")
missing = [m.name for m in ROOMS if m.name not in seen]
print(f"  ‼ NOT reached by warp-graph alone: {missing or '(none)'}")
print("    (a room missing here is not necessarily unreachable — it may need an in-room route")
print("     across a boulder puzzle, which a warp graph cannot see. §Ch18's lesson.)")

head("2. PER-ROOM SHAPE — walkable tiles and CONNECTED COMPONENTS")

comps_by_room = {}
for m in ROOMS:
    g = grid_of(m)
    md = get_map_data(m, (0, 0))
    w, h = md.map_size
    walk = {p for p, t in g.items() if walkable(t)}
    # flood fill 4-way over walkable tiles only (collision-only model, deliberately naive)
    unseen = set(walk)
    comps = []
    while unseen:
        start = next(iter(unseen))
        stack, comp = [start], set()
        while stack:
            p = stack.pop()
            if p in comp:
                continue
            comp.add(p)
            unseen.discard(p)
            x, y = p
            for n in ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)):
                if n in unseen:
                    stack.append(n)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    comps_by_room[m.name] = comps
    sizes = [len(c) for c in comps[:6]]
    print(f"  {m.name:<28} size={w}x{h:<3} walkable={len(walk):<5} components={len(comps):<3} "
          f"largest={sizes}")
print("\n  ‼ A component count > 1 means plain A* is CORRECT to say 'no path' between them — the")
print("    link is a warp, a boulder push, or a mechanic. It is not a pathfinder bug (KI-58).")

head("2b. ELEVATION — why a 1-COMPONENT room can still be unroutable")

print("  `is_tile_accessible` refuses a step when `tile.elevation not in (0,15) and from_elevation")
print("  != 0 and tile.elevation != from_elevation` (`map_path.py`). So a room whose walkable tiles")
print("  form ONE collision-component can still be impassable to A* if it spans two elevations —")
print("  which is what a cave bridge/ledge looks like. Elevation 1 is WATER (needs Surf).\n")

for m in ROOMS:
    g = grid_of(m)
    hist: dict[int, int] = {}
    for p, t in g.items():
        if walkable(t):
            hist[t.elevation] = hist.get(t.elevation, 0) + 1
    warp_tiles = sorted({s for s, _dn, _dc in graph[m.name]})
    detail = []
    for wt in warp_tiles:
        t = g.get(wt)
        if t is None:
            detail.append(f"{wt}=MISSING")
        else:
            detail.append(f"{wt} elev={t.elevation} coll={t.collision} {t.tile_type!r}")
    print(f"  {m.name:<28} walkable-elevations={dict(sorted(hist.items()))}")
    for d in detail:
        print(f"      warp {d}")

head("3. OBJECT EVENTS PER ROOM — boulders and NPCs a static route cannot model")

for m in ROOMS:
    md = get_map_data(m, (0, 0))
    objs = getattr(md, "objects", None) or []
    if not objs:
        print(f"  {m.name:<28} (no object-event templates readable)")
        continue
    print(f"  {m.name:<28} {len(objs)} object template(s)")
    for o in objs[:12]:
        gid = getattr(o, "graphics_id", "?")
        coords = getattr(o, "local_coordinates", "?")
        kind = getattr(o, "trainer_type", "")
        print(f"      id={getattr(o, 'local_id', '?'):<3} gfx={gid:<28} at={coords} trainer={kind}")

head("3b. ‼ THE OBJECT ARTIFACT — why section 4's NO-PATHs are NOT map facts")

print("  `map_path.is_tile_accessible` blocks any tile whose `dynamic_object_id` is set and whose")
print("  object is NOT in `active_objects` — and `active_objects` comes from `get_map_objects()`,")
print("  i.e. the objects loaded RIGHT NOW. This probe reads the cavern while the avatar is in")
print("  MOSSDEEP, so NO cavern object is loaded and EVERY object-template tile is treated as")
print("  permanently blocked. ⇒ **A NO-PATH in section 4 may be the boulders, not the room.**")
print("  ‼ This is exactly the lie §Ch19 already caught once: a static model blamed the planner")
print("    (KI-59) for what were really NPCs, and `probe_ch19_route.py` was fixed to model live")
print("    objects so it could not tell it twice. Same trap, one chapter later.\n")
print("  Below: components over walkable tiles, and again with object-template tiles REMOVED.")
print("  A room that is 1 component but splits once objects are removed is a BOULDER PUZZLE —")
print("  and it must be solved against LIVE object positions, never planned statically.\n")


def components(tiles: set) -> list:
    unseen, comps = set(tiles), []
    while unseen:
        stack, comp = [next(iter(unseen))], set()
        while stack:
            p = stack.pop()
            if p in comp:
                continue
            comp.add(p)
            unseen.discard(p)
            x, y = p
            for n in ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)):
                if n in unseen:
                    stack.append(n)
        comps.append(comp)
    return sorted(comps, key=len, reverse=True)


for m in ROOMS:
    g = grid_of(m)
    md = get_map_data(m, (0, 0))
    walk = {p for p, t in g.items() if walkable(t)}
    objs = getattr(md, "objects", None) or []
    obj_tiles = set()
    for o in objs:
        c = getattr(o, "local_coordinates", None)
        if c is not None:
            obj_tiles.add(tuple(c))
    a = components(walk)
    b = components(walk - obj_tiles)
    verdict = ""
    if len(b) > len(a):
        verdict = f"  <- ‼ OBJECTS SPLIT IT {len(a)} -> {len(b)}: a BOULDER/NPC puzzle"
    print(f"  {m.name:<28} objects={len(obj_tiles):<3} components {len(a)} -> {len(b)}"
          f"  sizes={[len(c) for c in b[:5]]}{verdict}")

head("4. IN-ROOM ROUTABILITY — arrival tile -> every other warp tile, via the REAL planner")

print("  ⛔ READ 3b FIRST. Run from OUTSIDE the cavern, every object-template tile is blocked, so a")
print("     NO-PATH here is NOT evidence the room is impassable in a real run. Treat this section")
print("     as a LOWER BOUND on routability, and re-measure from inside the cavern before building.")
print("  ‼ KI-60: every SOURCE below is asserted walkable first — an unvalidated source makes a")
print("    'path' meaningless.\n")

# Build: for each room, the tiles we ARRIVE on (destinations of warps pointing into it).
arrivals: dict[str, set] = {m.name: set() for m in ROOMS}
for src_map, entries in graph.items():
    for _src, dn, dc in entries:
        if dn in arrivals:
            arrivals[dn].add(dc)

for m in ROOMS:
    g = grid_of(m)
    arr = sorted(arrivals[m.name])
    warp_tiles = sorted({s for s, _dn, _dc in graph[m.name]})
    if not arr:
        print(f"  {m.name}: no known arrival tile — skipped")
        continue
    print(f"  --- {m.name} --- arrivals={arr} warp_tiles={warp_tiles}")
    for a in arr:
        ta = g.get(a)
        if ta is None or not walkable(ta):
            print(f"      ‼ arrival {a} is NOT walkable (collision="
                  f"{getattr(ta, 'collision', '?')}, type={getattr(ta, 'tile_type', '?')!r}) — skipping")
            continue
        for wt in warp_tiles:
            if wt == a:
                continue
            try:
                path = calculate_path((m, a), (m, wt))
                print(f"      {a} -> {wt}: OK {len(path)} waypoints")
            except PathFindingError as exc:
                print(f"      {a} -> {wt}: NO-PATH ({str(exc)[:60]})")
            except Exception as exc:
                print(f"      {a} -> {wt}: ERROR {type(exc).__name__}: {str(exc)[:60]}")

head("NEGATIVE CONTROL — a route into solid rock must RAISE")

m = MapRSE.SEAFLOOR_CAVERN_ROOM1
g = grid_of(m)
blocked = sorted(p for p, t in g.items() if t.collision != 0)
arr = sorted(arrivals[m.name])
if blocked and arr:
    src, dst = arr[0], blocked[0]
    try:
        calculate_path((m, src), (m, dst))
        print(f"  ‼ FAIL — a path into blocked tile {dst} was returned. The planner or this probe is wrong.")
    except PathFindingError:
        print(f"  PASS — {src} -> blocked {dst} raised PathFindingError, as it must.")
    except Exception as exc:
        print(f"  PASS(ish) — raised {type(exc).__name__}: {str(exc)[:60]}")
else:
    print("  (no blocked tile or no arrival tile to test with)")

head("DONE — measurement only. Nothing was changed.")
