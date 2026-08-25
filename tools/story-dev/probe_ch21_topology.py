"""probe_ch21_topology.py — the STATIC recon that makes Ch21 (Sootopolis / Rayquaza) buildable.

Modelled on `probe_ch20_topology.py`, the instrument that made the Ch20 dive leg buildable.
Everything printed here comes from OUR OWN ROM/map data (`modules.map.get_map_data`,
`get_map_all_tiles`, `modules.map_path.calculate_path`) — NOTHING from recall, and nothing
from a research note.

WHY THIS EXISTS: a routing recon (2026-08-24) established the Sky Pillar staircase and the Cave
of Origin warps as HARD data out of `cache/warp_graph_BPEE0.json`, but left FOUR unknowns that
no static table in our tree can answer, every one of them on the critical path:
   1. WHICH ROUTE126 TILE CAN YOU DIVE ON?  — no coordinate exists anywhere in our tree
   2. Are ROUTE126 and UNDERWATER_ROUTE126 the SAME SIZE?  A dive lands on the same (x,y) ONLY
      if they are; that was MEASURED for Route 128 and is UNMEASURED for 126.
   3. WHICH UNDERWATER_SOOTOPOLIS_CITY TILE CAN YOU SURFACE ON?   <-- THE KI-72 TRAP
   4. Does UNDERWATER_ROUTE126 really warp to UNDERWATER_SOOTOPOLIS_CITY at (45,65)?

WHAT THIS PROBE DELIBERATELY DOES *NOT* ANSWER — READ BEFORE EXTENDING IT.

*** THREE OF THIS CHAPTER'S MAP REGIONS ARE LAYOUT-SWAPPED AT RUNTIME, SO NO TILE THIS PROBE
*** PRINTS FOR THEM DESCRIBES WHAT THE BOT WILL SEE. Measured 2026-08-24:
***   SKY_PILLAR_1F..TOP  -> LAYOUT_SKY_PILLAR_*_CLEAN   while VAR_SKY_PILLAR_STATE < 2
***   ROUTE131            -> LAYOUT_ROUTE131_SKY_PILLAR  UNCONDITIONALLY, in OnTransition.
***                          (36,6) is elevation 1 in the DEFAULT layout and elevation 3 in the
***                          swapped one -- i.e. the tower door reads as WATER here.
***   SOOTOPOLIS_CITY     -> a crisis layout chosen by SOOTOPOLIS_CITY_STATE
*** => WARPS are map-header data and are SAFE to read here. TILES are NOT. This probe asserts
*** only on warps, sizes and the two UNDERWATER maps (which do not swap).
*** => AND THE FIX IS NOT ALWAYS "GO LIVE": the decomp ships the swapped layouts as
*** data/layouts/<NAME>/map.bin, so decoding those bytes answers the question exactly. That is
*** how the Sky Pillar staircase was settled -- see
*** tools/story-dev/evidence/2026-08-24-skypillar-clean-reachability.txt.

The Sky Pillar's INTERIOR TILES CANNOT BE TRUSTED FROM A STATIC READ. Every floor swaps to a
`LAYOUT_SKY_PILLAR_*_CLEAN` at RUNTIME via `setmaplayoutindex` in its `OnTransition`, gated
`call_if_lt VAR_SKY_PILLAR_STATE, 2`. `get_map_data` reads the map header's DEFAULT layout —
i.e. the CRACKED, post-game one. So a static walkability check on 2F/4F would describe a layout
the story bot never sees, and would do it CONFIDENTLY. Sky Pillar WARPS are read below (they
live in the map header and do not swap); its FLOOR TILES are reported ONLY as a labelled
hazard, never asserted. Closing that needs a LIVE read while standing on the map at
`VAR_SKY_PILLAR_STATE < 2`.
This is the same class of error as KI-72: the tool answers, and the answer is about the
wrong map.

CONTROLS (so a null result is attributable, per playbook 0b):
  * POSITIVE — a 1-step `calculate_path` between two adjacent open tiles on UNDERWATER_ROUTE126.
    If that succeeds, the pathfinder + map metadata for this map work.
  * NEGATIVE — a `calculate_path` into a known-blocked tile, expected to RAISE.

ASSERTIONS: this probe EXITS 1 if any fail. `probe_dive_routing.py` was found in the pass-4
audit to have ZERO assertions while printing alarm lines under a PASS — do not repeat that here.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch21_topology.py
"""

import os
import pathlib
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

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
# The exact set `dive()` accepts — higher_level_actions.py:921-925, copied not invented.
DIVE_TILE_TYPES = ("Deep Water", "Interior Deep Water", "Semi-Deep Water", "Sootopolis Deep Water")
# The exact set `surface_from_dive()` REFUSES — higher_level_actions.py:946.
NO_SURFACE_TYPES = ("Underwater Blocked Above", "Seaweed No Surfacing")

FAILURES = []


def head(title):
    print("\n" + BAR + "\n" + title + "\n" + BAR + "\n")


def check(label, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print("  [" + tag + "] " + label + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILURES.append(label)


def scan(map_enum):
    return get_map_all_tiles(get_map_data(map_enum, (0, 0)))


def warps_of(map_enum):
    """Every warp on a map, BY ITS OWN COORDINATE.

    A WARP LIVES ON THE MAP, NOT ON THE TILE. The first draft of this function iterated
    `scan(map_enum)` and read `tile.warps`, which is the MAP-level property reached through the
    tile -- so all 6400 tiles of UNDERWATER_ROUTE126 reported the SAME warp, and the assertion
    "there is a warp at (45,65)" passed merely because the TILE (45,65) exists. That assertion
    COULD NOT FAIL: exactly the pass-4 "gate with zero assertions" defect, rebuilt by hand.
    `map_data.warps` is a list of `MapWarp`, each with its OWN `.local_coordinates`.
    """
    out = []
    for w in get_map_data(map_enum, (0, 0)).warps:
        try:
            dest = MapRSE((w.destination_map_group, w.destination_map_number)).name
        except Exception:
            dest = "UNKNOWN(%s,%s)" % (w.destination_map_group, w.destination_map_number)
        out.append((tuple(w.local_coordinates), dest, w.destination_warp_id))
    return out


avatar = get_player_avatar()
print("anchor: post_dive.ss1")
print("avatar: %s %s   (identity by ENUM, never the display label -- playbook 2b)"
      % (MapRSE(tuple(avatar.map_group_and_number)).name, tuple(avatar.local_coordinates)))

# =================================================================================================
head("1 -- ROUTE126: which tiles are DIVE-CAPABLE?  (unknown #1: no coordinate exists in our tree)")

r126_head = get_map_data(MapRSE.ROUTE126, (0, 0))
u126_head = get_map_data(MapRSE.UNDERWATER_ROUTE126, (0, 0))
r126_size, u126_size = tuple(r126_head.map_size), tuple(u126_head.map_size)
print("  ROUTE126            size=%s" % (r126_size,))
print("  UNDERWATER_ROUTE126 size=%s" % (u126_size,))
check("unknown #2: ROUTE126 and UNDERWATER_ROUTE126 are the SAME SIZE (a dive lands on the same x,y)",
      r126_size == u126_size, "%s vs %s" % (r126_size, u126_size))

r126 = scan(MapRSE.ROUTE126)
print("\n  ROUTE126 tile-type histogram (%d tiles):" % len(r126))
for name, n in Counter(t.tile_type for t in r126).most_common():
    print("      %6d  %s" % (n, name))
divable = [tuple(t.local_position) for t in r126 if t.tile_type in DIVE_TILE_TYPES]
print("\n  DIVE-CAPABLE ROUTE126 tiles: %d" % len(divable))
check("unknown #1: ROUTE126 has at least one dive-capable tile", len(divable) > 0)

near = sorted(divable, key=lambda c: (abs(c[0] - 45) + abs(c[1] - 65)))[:12]
print("  the 12 dive tiles NEAREST the (45,65) warp column, by manhattan distance:")
for c in near:
    print("      %s   dist=%d" % (c, abs(c[0] - 45) + abs(c[1] - 65)))

# =================================================================================================
head("2 -- UNDERWATER_ROUTE126: does (45,65) really warp to Sootopolis?  (unknown #4)")

u126_warps = warps_of(MapRSE.UNDERWATER_ROUTE126)
for pos, dest, wid in u126_warps:
    print("      %s -> %s (warp_id=%s)" % (pos, dest, wid))

# FAULT HOOK -- `POKEBOT_CH21PROBE_FAULT=warpcoord` looks for the warp at a coordinate that is
# NOT there, so this assertion MUST report FAIL and the probe MUST exit 1. It exists because the
# first draft of `warps_of` made this very assertion VACUOUS (see that function's docstring), and
# a PASS from an assertion that cannot fail is worse than no assertion at all. Prove it bites.
_want = (45, 65)
if os.environ.get("POKEBOT_CH21PROBE_FAULT") == "warpcoord":
    _want = (0, 0)
    print("  FAULT: looking for the warp at %s instead -- this assertion MUST fail." % (_want,))
hit = [w for w in u126_warps if w[0] == _want]
check("unknown #4: UNDERWATER_ROUTE126 has a warp AT (45,65)", bool(hit), str(hit[:1]))
check("unknown #4: ...and it leads to UNDERWATER_SOOTOPOLIS_CITY",
      bool(hit) and hit[0][1] == "UNDERWATER_SOOTOPOLIS_CITY", hit[0][1] if hit else "n/a")

# =================================================================================================
head("3 -- UNDERWATER_SOOTOPOLIS_CITY: WHERE CAN YOU SURFACE?  THE KI-72 TRAP (unknown #3)")

us_head = get_map_data(MapRSE.UNDERWATER_SOOTOPOLIS_CITY, (0, 0))
print("  size=%s" % (tuple(us_head.map_size),))
us = scan(MapRSE.UNDERWATER_SOOTOPOLIS_CITY)
print("\n  tile-type histogram (%d tiles):" % len(us))
for name, n in Counter(t.tile_type for t in us).most_common():
    flag = "   <-- CANNOT SURFACE HERE" if name in NO_SURFACE_TYPES else ""
    print("      %6d  %s%s" % (n, name, flag))
print("\n  warps:")
for pos, dest, wid in warps_of(MapRSE.UNDERWATER_SOOTOPOLIS_CITY):
    print("      %s -> %s (warp_id=%s)" % (pos, dest, wid))

surfaceable = [tuple(t.local_position) for t in us
               if t.tile_type not in NO_SURFACE_TYPES and t.collision == 0]
print("\n  => SURFACEABLE tiles (tile_type not blocked and collision==0): %d" % len(surfaceable))
for c in surfaceable[:20]:
    print("      %s" % (c,))
check("unknown #3: UNDERWATER_SOOTOPOLIS_CITY has at least one SURFACEABLE tile", len(surfaceable) > 0)
print("  (reported, not asserted) arrival tile (9,8) surfaceable = %s"
      % ((9, 8) in surfaceable))

# =================================================================================================
head("4 -- CONTROLS (so a null result above is attributable)")

all126 = scan(MapRSE.UNDERWATER_ROUTE126)
open126 = [t for t in all126 if t.collision == 0]
blocked126 = [t for t in all126 if t.collision != 0]
pos_ok = False
neg_ok = False
if len(open126) >= 2:
    a = tuple(open126[0].local_position)
    b = None
    for t in open126[1:]:
        c = tuple(t.local_position)
        if abs(c[0] - a[0]) + abs(c[1] - a[1]) == 1:
            b = c
            break
    if b:
        try:
            calculate_path((MapRSE.UNDERWATER_ROUTE126, a), (MapRSE.UNDERWATER_ROUTE126, b))
            pos_ok = True
        except Exception as e:
            print("      positive control RAISED: %s" % e)
        print("  POSITIVE control: 1-step path %s -> %s  ok=%s" % (a, b, pos_ok))
if blocked126 and open126:
    src = tuple(open126[0].local_position)
    dst = tuple(blocked126[0].local_position)
    try:
        calculate_path((MapRSE.UNDERWATER_ROUTE126, src), (MapRSE.UNDERWATER_ROUTE126, dst))
    except Exception:
        neg_ok = True
    print("  NEGATIVE control: path into blocked %s raised = %s" % (dst, neg_ok))
check("POSITIVE control: the pathfinder works on UNDERWATER_ROUTE126", pos_ok)
check("NEGATIVE control: pathing into a blocked tile RAISES", neg_ok)

# =================================================================================================
head("5 -- SOOTOPOLIS / CAVE OF ORIGIN / SKY PILLAR warps  (header data -- these do NOT swap)")

for enum in (MapRSE.SOOTOPOLIS_CITY, MapRSE.CAVE_OF_ORIGIN_ENTRANCE, MapRSE.CAVE_OF_ORIGIN_1F,
             MapRSE.CAVE_OF_ORIGIN_B1F, MapRSE.ROUTE131, MapRSE.SKY_PILLAR_ENTRANCE,
             MapRSE.SKY_PILLAR_OUTSIDE, MapRSE.SKY_PILLAR_1F, MapRSE.SKY_PILLAR_2F,
             MapRSE.SKY_PILLAR_3F, MapRSE.SKY_PILLAR_4F, MapRSE.SKY_PILLAR_5F,
             MapRSE.SKY_PILLAR_TOP):
    data = get_map_data(enum, (0, 0))
    print("  %s  size=%s" % (enum.name, tuple(data.map_size)))
    for pos, dest, wid in warps_of(enum):
        print("      %s -> %s (warp_id=%s)" % (pos, dest, wid))

soot_warps = warps_of(MapRSE.SOOTOPOLIS_CITY)
check("the routing recon's SOOTOPOLIS_CITY (31,16) -> CAVE_OF_ORIGIN_ENTRANCE is real",
      any(p == (31, 16) and d == "CAVE_OF_ORIGIN_ENTRANCE" for p, d, _ in soot_warps))

# =================================================================================================
head("6 -- SKY PILLAR INTERIOR: REPORTED AS A HAZARD, DELIBERATELY NOT ASSERTED")

print("  The tiles below are the map header's DEFAULT layout -- the CRACKED, POST-GAME one.")
print("  The story climb runs on LAYOUT_SKY_PILLAR_*_CLEAN, applied at RUNTIME by")
print("  `setmaplayoutindex` in each floor's OnTransition, gated `VAR_SKY_PILLAR_STATE < 2`.")
print("  => ANY conclusion drawn from these numbers is about a map the story bot never sees.")
print("  Closing this needs a LIVE read while standing on the floor at state < 2.\n")
for enum in (MapRSE.SKY_PILLAR_2F, MapRSE.SKY_PILLAR_4F):
    tiles = scan(enum)
    cracked = [tuple(t.local_position) for t in tiles if "Crack" in (t.tile_type or "")]
    print("  %s: %d tiles, %d with a 'Crack*' tile_type (DEFAULT layout -- NOT the story layout)"
          % (enum.name, len(tiles), len(cracked)))

# =================================================================================================
head("VERDICT")
if FAILURES:
    print("  %d ASSERTION(S) FAILED:" % len(FAILURES))
    for f in FAILURES:
        print("      - " + f)
    sys.exit(1)
print("  every assertion passed. The four routing unknowns are CLOSED except where marked.")
