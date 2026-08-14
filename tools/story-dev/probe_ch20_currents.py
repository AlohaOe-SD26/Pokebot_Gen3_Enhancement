"""§Ch20 — CAN OUR PLANNER CROSS A CURRENT MAZE? Rooms 6 and 7 of the Seafloor Cavern.

‼ THIS IS §Ch20's BIGGEST UNKNOWN. `map_path.py` has a `forced_movement_to` model for
`* Current` tiles, but **no chapter in this project has ever driven a current maze**. Rooms 6 and 7
are 108 and 117 forced-slide tiles. If the planner cannot route them, §Ch20 needs a solver (the
§Ch18 shape), not a `navigate_to`.

‼ WHY THIS CAN BE MEASURED FROM OUTSIDE THE CAVERN, unlike `probe_ch20_interior.py`'s section 4:
  `is_tile_accessible` blocks any tile whose object is not in `active_objects`, and reading a map
  the avatar is not standing on means NO object is loaded — which made the boulder rooms report
  false NO-PATHs. **Rooms 6 and 7 contain ZERO object events** (measured, `probe_ch20_interior.py`
  section 3b: `objects=0`, components 1 -> 1). So that artifact cannot apply here, and a result on
  these two rooms IS attributable.

‼ PRE-REGISTERED PREDICTIONS — written BEFORE the run, because this project has twice learned that
  a prediction written afterwards is a rationalisation. Source: the decomp recon note
  `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`, which ran a slide-aware search:
    P1  ROOM6 (11,21) -> (4,1)   REACHABLE      (the forward story leg)
    P2  ROOM6 (4,1)  -> (11,21)  NOT REACHABLE  (‼ Room 6 is ONE-WAY — the currents forbid it)
    P3  ROOM7 (3,23) -> (5,1)    REACHABLE      (Room 7 is the two-way alternative)
    P4  ROOM7 (5,1)  -> (3,23)   REACHABLE
  ‼ **P2 is the discriminating one.** If our planner says (4,1)->(11,21) is routable, it is NOT
  modelling the currents as one-way and any route it emits for these rooms is untrustworthy.
  ‼ And if ALL FOUR come back NO-PATH, the honest reading is "our planner cannot do currents at
  all", NOT "the decomp note is wrong" — a uniform failure is a statement about the instrument.

CONTROLS
  * POSITIVE — a 1-step route between two adjacent open tiles on the same map, so a failure in the
    long routes is about the ROUTE, not the harness.
  * NEGATIVE — a route into a collision tile, which must raise.
  * ATTRIBUTION — the current-tile census per room is printed, so a null result can be read.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch20_currents.py
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


def head(t):
    print(f"\n{BAR}\n{t}\n{BAR}\n")


def grid_of(m):
    return {tuple(t.local_position): t for t in get_map_all_tiles(get_map_data(m, (0, 0)))}


def route(m, src, dst):
    try:
        wp = calculate_path((m, src), (m, dst))
        return True, f"OK {len(wp)} waypoints", wp
    except PathFindingError as exc:
        return False, f"NO-PATH ({str(exc)[:50]})", None
    except Exception as exc:
        return False, f"ERROR {type(exc).__name__}: {str(exc)[:50]}", None


avatar = get_player_avatar()
print(f"anchor post_dive.ss1 — avatar {MapRSE(tuple(avatar.map_group_and_number)).name} "
      f"{tuple(avatar.local_coordinates)}  (‼ NOT in the cavern — see the docstring for why that is OK here)")

head("1. CURRENT CENSUS — and the object check that makes this measurable at all")

for m in (MapRSE.SEAFLOOR_CAVERN_ROOM6, MapRSE.SEAFLOOR_CAVERN_ROOM7):
    g = grid_of(m)
    md = get_map_data(m, (0, 0))
    currents: dict[str, int] = {}
    for t in g.values():
        if t.tile_type.endswith(" Current"):
            currents[t.tile_type] = currents.get(t.tile_type, 0) + 1
    objs = getattr(md, "objects", None) or []
    walk = sum(1 for t in g.values() if t.collision == 0)
    print(f"  {m.name}: walkable={walk}  current_tiles={sum(currents.values())}  objects={len(objs)}")
    for k, v in sorted(currents.items()):
        print(f"      {k:<22} {v}")
    if objs:
        print(f"      ‼ {len(objs)} OBJECT(S) PRESENT — the outside-the-map artifact APPLIES here after all,")
        print("        and every result below for this room is a LOWER BOUND, not a fact.")
    else:
        print("      objects=0 -> the `active_objects` artifact cannot apply; results are attributable.")

head("2. CONTROLS")

for m in (MapRSE.SEAFLOOR_CAVERN_ROOM6, MapRSE.SEAFLOOR_CAVERN_ROOM7):
    g = grid_of(m)
    opens = sorted(p for p, t in g.items() if t.collision == 0)
    # POSITIVE: two orthogonally adjacent open tiles
    pos = None
    for (x, y) in opens:
        if (x + 1, y) in g and g[(x + 1, y)].collision == 0:
            pos = ((x, y), (x + 1, y))
            break
    if pos:
        ok, msg, _ = route(m, *pos)
        print(f"  POSITIVE {m.name} {pos[0]} -> {pos[1]}: {msg}  {'PASS' if ok else '‼ FAIL — the harness is broken'}")
    blocked = sorted(p for p, t in g.items() if t.collision != 0)
    if blocked and opens:
        ok, msg, _ = route(m, opens[0], blocked[0])
        print(f"  NEGATIVE {m.name} {opens[0]} -> blocked {blocked[0]}: {msg}  "
              f"{'PASS' if not ok else '‼ FAIL — a path into rock was returned'}")

head("3. THE FOUR PRE-REGISTERED PREDICTIONS")

TESTS = [
    ("P1", MapRSE.SEAFLOOR_CAVERN_ROOM6, (11, 21), (4, 1), True, "forward story leg"),
    ("P2", MapRSE.SEAFLOOR_CAVERN_ROOM6, (4, 1), (11, 21), False, "‼ ONE-WAY: must FAIL"),
    ("P3", MapRSE.SEAFLOOR_CAVERN_ROOM7, (3, 23), (5, 1), True, "two-way alternative"),
    ("P4", MapRSE.SEAFLOOR_CAVERN_ROOM7, (5, 1), (3, 23), True, "two-way alternative, reverse"),
]

results = []
for tag, m, src, dst, expect_ok, why in TESTS:
    g = grid_of(m)
    ts = g.get(src)
    if ts is None or ts.collision != 0:
        print(f"  {tag} {m.name} {src}: ‼ SOURCE NOT WALKABLE (collision="
              f"{getattr(ts, 'collision', '?')}) — KI-60 says the result would be meaningless. SKIPPED")
        results.append((tag, None, expect_ok))
        continue
    ok, msg, wp = route(m, src, dst)
    verdict = "AS PREDICTED" if ok == expect_ok else "‼ PREDICTION FAILED"
    print(f"  {tag} {m.name} {src} -> {dst}  [{why}]")
    print(f"      predicted={'REACHABLE' if expect_ok else 'NOT reachable'}   got={msg}   {verdict}")
    results.append((tag, ok, expect_ok))
    if ok and wp:
        acts = {}
        for w in wp:
            a = getattr(w, "action", None)
            acts[str(a)] = acts.get(str(a), 0) + 1
        manhattan = abs(src[0] - dst[0]) + abs(src[1] - dst[1])
        # ‼ ATTRIBUTION: a plain walked route emits ~one waypoint per tile, so it can never be
        # SHORTER than the Manhattan distance. Fewer waypoints than Manhattan means individual
        # waypoints are covering multiple tiles — i.e. the planner really is using the
        # `forced_movement_to` SLIDE model, not routing around the currents on foot.
        slide_proof = (
            "‼ waypoints < Manhattan -> the SLIDE model is genuinely in use"
            if len(wp) < manhattan
            else "waypoints >= Manhattan -> this route may be plain walking; slides NOT demonstrated here"
        )
        print(f"      waypoint actions: {acts}")
        print(f"      len={len(wp)} vs Manhattan({src}->{dst})={manhattan}   {slide_proof}")

head("4. VERDICT")

fired = [(t, g, e) for t, g, e in results if g is not None]
hits = sum(1 for _t, g, e in fired if g == e)
print(f"  predictions that fired: {len(fired)}/4   matched: {hits}/{len(fired) if fired else 0}")

all_nopath = fired and all(g is False for _t, g, _e in fired)
if all_nopath:
    print("\n  ⛔ ALL FOUR CAME BACK NO-PATH. The honest reading is **our planner cannot route a")
    print("     current maze at all** — NOT that the decomp note is wrong. A uniform failure is a")
    print("     statement about the instrument. ⇒ §Ch20 needs a slide-aware SOLVER for rooms 6/7")
    print("     (the §Ch18 shape), not a `navigate_to`.")
elif hits == len(fired) and fired:
    print("\n  ✅ ALL PREDICTIONS MATCHED, INCLUDING THE DISCRIMINATING ONE (P2, the one-way).")
    print("     Our planner reproduces the currents' asymmetry independently of the decomp note.")
    print("     ⇒ rooms 6/7 can plausibly be driven with `navigate_to`. ‼ Still verify LIVE before")
    print("     building: a plan is not a walk, and the executor has never crossed a current.")
else:
    print("\n  ⚠ MIXED. Read each line above — a planner that gets P1 right and P2 wrong is")
    print("     OPTIMISTIC (it will emit routes the game refuses), which is the dangerous direction.")

head("DONE — measurement only. Nothing was changed.")
