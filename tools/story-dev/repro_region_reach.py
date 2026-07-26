"""Proof for `modules/story/region_reach.py` (#24-regionreach, KI-24).

KI-24: `_training_area_allowed`'s tile-level `calculate_path` oracle reports
ROUTE118 unreachable from a verified Winona-era ROUTE120 save -- the real answer
to Winona -- because Routes 118/119/120 are the dual-elevation-bridge maps
`calculate_path` reads as walls. `region_reach.py` answers the same question from
the ROM's own MapConnections + warp graph instead. This script proves:

  1. What `devon_scope_got.ss1` ACTUALLY loads as (never trust a save's filename
     -- several saves in this directory have proven misnamed).
  2. THE KI-24 CASE FLIPS: from ROUTE120 with Surf, ROUTE118 is REACHABLE.
  3. FORTREE_CITY and ROUTE119 are also reachable from ROUTE120.
  4. With `can_surf=False` pinned, a water-gated map (DEWFORD_TOWN) becomes
     unreachable, and `why_unreachable` names the gate.
  5. A bogus map returns False with a clear reason, no raise.

Run: py -3.12 tools/story-dev/repro_region_reach.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

p = load_profile_by_name("repro-fresh")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)
from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"
context.emulator.load_save_state((REPO / "tools/story-dev/saves/devon_scope_got.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.map_data import MapRSE
from modules.memory import get_event_flag
from modules.player import get_player_location
from modules.pokemon_party import get_party
from modules.story.region_reach import hops_to, is_map_reachable, reachable_maps, why_unreachable

print("=" * 78)
print("0) VERIFY WHAT THIS SAVE ACTUALLY LOADS AS (never trust the filename)")
print("=" * 78)
map_enum, coords = get_player_location()
print(f"   standing at {map_enum.name} {coords}")
for mon in get_party():
    if mon is not None:
        moves = ", ".join(m.move.name for m in mon.moves if m is not None)
        print(f"   party: {mon.species.name} L{mon.level} moves=[{moves}]")
badge5 = get_event_flag("BADGE05_GET")
badge6 = get_event_flag("BADGE06_GET")
print(f"   BADGE05_GET (Balance, unlocks Surf) = {badge5}")
print(f"   BADGE06_GET (Feather/Winona)         = {badge6}")
assert map_enum is MapRSE.ROUTE120, f"expected ROUTE120, got {map_enum.name}"
assert badge5 and not badge6, f"expected post-Norman, pre-Winona save (badge5={badge5}, badge6={badge6})"
has_surf = get_party().has_pokemon_with_move("Surf")
print(f"   party knows Surf = {has_surf}")
assert has_surf, "expected a party mon to know Surf at this era"
print("   -> confirmed correct era: ROUTE120, Surf known, Badge5 set, Badge6 not.")

print()
print("=" * 78)
print("1) reachable_maps() from ROUTE120, live capability detection")
print("=" * 78)
maps = reachable_maps(MapRSE.ROUTE120)
print(f"   {len(maps)} reachable map(s). Sample: {sorted(maps)[:15]}")
assert maps, "expected a non-empty reachable set"

print()
print("=" * 78)
print("2) THE KI-24 CASE FLIPS: ROUTE118 is REACHABLE from ROUTE120 (real Winona answer)")
print("=" * 78)
route118_reachable = is_map_reachable(MapRSE.ROUTE118, MapRSE.ROUTE120)
print(f"   is_map_reachable(ROUTE118, from=ROUTE120) = {route118_reachable}")
print(f"   why_unreachable() if it were still broken would have said: "
      f"{why_unreachable(MapRSE.ROUTE118, MapRSE.ROUTE120)!r}")
assert route118_reachable, "KI-24 REGRESSION: ROUTE118 should be reachable from ROUTE120 with Surf"
print("   PASS -- this is the whole point of the task.")

print()
print("=" * 78)
print("3) FORTREE_CITY and ROUTE119 also reachable from ROUTE120")
print("=" * 78)
fortree_reachable = is_map_reachable(MapRSE.FORTREE_CITY, MapRSE.ROUTE120)
route119_reachable = is_map_reachable(MapRSE.ROUTE119, MapRSE.ROUTE120)
print(f"   FORTREE_CITY reachable = {fortree_reachable}")
print(f"   ROUTE119 reachable     = {route119_reachable}")
assert fortree_reachable, "FORTREE_CITY should be reachable from ROUTE120"
assert route119_reachable, "ROUTE119 should be reachable from ROUTE120"
assert MapRSE.FORTREE_CITY.value in maps
assert MapRSE.ROUTE119.value in maps
assert MapRSE.ROUTE118.value in maps
print("   PASS -- both present in reachable_maps() too.")

print()
print("=" * 78)
print("4) can_surf=False pinned -> a water-gated map (DEWFORD_TOWN) becomes unreachable,")
print("   and why_unreachable() names the gate")
print("=" * 78)
dewford_with_surf = is_map_reachable(MapRSE.DEWFORD_TOWN, MapRSE.ROUTE120, can_surf=True)
dewford_without_surf = is_map_reachable(MapRSE.DEWFORD_TOWN, MapRSE.ROUTE120, can_surf=False)
reason = why_unreachable(MapRSE.DEWFORD_TOWN, MapRSE.ROUTE120, can_surf=False)
print(f"   is_map_reachable(DEWFORD_TOWN, can_surf=True)  = {dewford_with_surf}")
print(f"   is_map_reachable(DEWFORD_TOWN, can_surf=False) = {dewford_without_surf}")
print(f"   why_unreachable(DEWFORD_TOWN, can_surf=False)  = {reason!r}")
assert dewford_with_surf, "DEWFORD_TOWN should be reachable with Surf"
assert not dewford_without_surf, "DEWFORD_TOWN should be UNREACHABLE without Surf"
assert "Surf" in reason, f"why_unreachable should name the Surf gate, got: {reason!r}"
assert "DEWFORD" in reason.upper(), f"why_unreachable should name the gated edge, got: {reason!r}"
print("   PASS -- capability gate flips reachability and is named.")

print()
print("=" * 78)
print("5) a bogus map returns False with a clear reason, no raise")
print("=" * 78)
bogus_ok = is_map_reachable("THIS_IS_NOT_A_REAL_MAP", MapRSE.ROUTE120)
bogus_reason = why_unreachable("THIS_IS_NOT_A_REAL_MAP", MapRSE.ROUTE120)
bogus_tuple_ok = is_map_reachable((250, 250), MapRSE.ROUTE120)
bogus_tuple_reason = why_unreachable((250, 250), MapRSE.ROUTE120)
print(f"   is_map_reachable('THIS_IS_NOT_A_REAL_MAP') = {bogus_ok}")
print(f"   why_unreachable('THIS_IS_NOT_A_REAL_MAP')   = {bogus_reason!r}")
print(f"   is_map_reachable((250, 250))                = {bogus_tuple_ok}")
print(f"   why_unreachable((250, 250))                 = {bogus_tuple_reason!r}")
assert bogus_ok is False
assert bogus_tuple_ok is False
assert "unknown map" in bogus_reason.lower()
assert "unknown map" in bogus_tuple_reason.lower()
print("   PASS -- no raise, both report an 'unknown map' reason.")

print()
print("=" * 78)
print("6) COST: hop distances from ROUTE120 -- coordinator follow-up")
print("=" * 78)
print("   Pure connectivity called 309 maps 'reachable' with Surf -- true, but useless as a")
print("   filter for 'where should I go catch a counter?' if it can't tell Route 118 (a few")
print("   hops away) from a far city (many regions away). Measuring the real hop counts:")
hops_route118 = hops_to(MapRSE.ROUTE118, MapRSE.ROUTE120)
hops_fortree = hops_to(MapRSE.FORTREE_CITY, MapRSE.ROUTE120)
hops_route119 = hops_to(MapRSE.ROUTE119, MapRSE.ROUTE120)
hops_mossdeep = hops_to(MapRSE.MOSSDEEP_CITY, MapRSE.ROUTE120)
hops_lilycove = hops_to(MapRSE.LILYCOVE_CITY, MapRSE.ROUTE120)
hops_pacifidlog = hops_to(MapRSE.PACIFIDLOG_TOWN, MapRSE.ROUTE120)
print(f"   ROUTE120 -> FORTREE_CITY:     {hops_fortree} hop(s)")
print(f"   ROUTE120 -> ROUTE119:         {hops_route119} hop(s)")
print(f"   ROUTE120 -> ROUTE118 (KI-24): {hops_route118} hop(s)")
print(f"   ROUTE120 -> LILYCOVE_CITY:    {hops_lilycove} hop(s)")
print(f"   ROUTE120 -> PACIFIDLOG_TOWN:  {hops_pacifidlog} hop(s)")
print(f"   ROUTE120 -> MOSSDEEP_CITY:    {hops_mossdeep} hop(s)")
assert hops_route118 is not None and hops_route118 <= 6, f"expected Route 118 to be a handful of hops, got {hops_route118}"
# HONEST FINDING (differs from the coordinator's "far cities are many more hops"
# expectation): under uniform 1-hop-per-edge weighting, LILYCOVE_CITY (2 hops) and
# MOSSDEEP_CITY (4 hops) are NOT dramatically farther than ROUTE118 (3 hops) --
# because a single ROM connection can span an entire giant sea route (Surf lets you
# cross Route 124/125/126/127/128 in one "hop" the same as a one-tile bridge).
# Hop count under this weighting is a map-transition count, not a walk-distance
# estimate; it still cleanly separates a genuinely distant map (PACIFIDLOG_TOWN,
# 10 hops) from the Route118/Fortree/Route119 cluster (1-3 hops), which is enough
# to pick a useful max_hops cap below -- but it will NOT, by itself, separate every
# "training detour" candidate from every "sail across the region" one for maps
# that sit a similarly small number of sea-route hops away. Reported here rather
# than papered over with a looser assertion.
assert hops_mossdeep is not None and hops_pacifidlog is not None and hops_pacifidlog > hops_mossdeep, (
    f"expected Pacifidlog to be farther than Mossdeep, got pacifidlog={hops_pacifidlog} mossdeep={hops_mossdeep}"
)
print("   PASS -- Route 118 stays a handful of hops; Pacifidlog (10) is genuinely far, but")
print("   Lilycove/Mossdeep landing close in hop count (see note above) is a real limit of")
print("   uniform edge weighting, not a bug -- reported honestly rather than asserted away.")

print()
print("=" * 78)
print("7) max_hops: 'reachable but distant' must be distinguishable from 'no path' / 'gated'")
print("=" * 78)
CAP = hops_route118  # tightest cap that keeps ROUTE118 in while excluding MOSSDEEP_CITY (one hop farther)
print(f"   using max_hops={CAP} (ROUTE118's own measured distance)")
mossdeep_within_cap = is_map_reachable(MapRSE.MOSSDEEP_CITY, MapRSE.ROUTE120, max_hops=CAP)
mossdeep_reason = why_unreachable(MapRSE.MOSSDEEP_CITY, MapRSE.ROUTE120, max_hops=CAP)
route118_within_cap = is_map_reachable(MapRSE.ROUTE118, MapRSE.ROUTE120, max_hops=CAP)
print(f"   is_map_reachable(MOSSDEEP_CITY, max_hops={CAP}) = {mossdeep_within_cap}")
print(f"   why_unreachable(MOSSDEEP_CITY, max_hops={CAP})  = {mossdeep_reason!r}")
print(f"   is_map_reachable(ROUTE118, max_hops={CAP})      = {route118_within_cap}")
assert mossdeep_within_cap is False, "MOSSDEEP_CITY should be beyond the cap"
assert "hops away" in mossdeep_reason and "limit" in mossdeep_reason, (
    f"expected a distance-and-limit reason, got: {mossdeep_reason!r}"
)
assert "no connection path" not in mossdeep_reason, (
    f"a max_hops refusal must not be confused with 'no path exists', got: {mossdeep_reason!r}"
)
assert route118_within_cap is True, "ROUTE118 should stay reachable within the cap"
print("   PASS -- distance-and-limit reason is distinct from 'no connection path'/'needs <gate>',")
print("   and Route 118 survives the same cap that excludes Mossdeep.")

print()
print("-" * 78)
print("ALL PASS: region_reach.py answers region-scale reachability from the ROM's own")
print("connection/warp data, flips the KI-24 ROUTE118 case, honours capability gates with")
print("a named reason, prices reachability in hops so distant-but-technically-reachable")
print("maps can be told apart from nearby ones, and fails safe (no raise) on bogus input.")

print()
print("=" * 78)
print("VICTORY ROAD GATE -- one edge closes the whole cluster (2026-07-26)")
print("=" * 78)
# ‼ Added because cost-based counter ranking made this DANGEROUS. Victory Road's
# Hariyama is L38-42 -- already above a mid-game team -- so its estimated training cost
# is ~0 and it ranks #1 the instant anything calls the map reachable. Probed: the ONLY
# boundary edge into the entire VICTORY_ROAD_* cluster is
# EVER_GRANDE_CITY (0,8) <-> VICTORY_ROAD_1F (24,43), and it was UNGATED. In Emerald that
# entrance is at the top of a WATERFALL. Before this, only the max_hops=4 distance bound
# kept it out of the live counter list -- luck, not a gate.
_vr_failures = []
for _name, _m, _want in (
    ("VICTORY_ROAD_1F", MapRSE.VICTORY_ROAD_1F, False),
    ("VICTORY_ROAD_B1F", MapRSE.VICTORY_ROAD_B1F, False),
    # The city itself is genuinely reachable by Surf -- the gate must close the cave,
    # not the coastline, or it would be a blunt instrument.
    ("EVER_GRANDE_CITY", MapRSE.EVER_GRANDE_CITY, True),
):
    _got = is_map_reachable(_m)
    _why = why_unreachable(_m)
    print(f"   {_name:20s} reachable={_got}  why={_why}")
    if _got != _want:
        _vr_failures.append(f"{_name}: expected reachable={_want}, got {_got} ({_why})")

_why_vr = why_unreachable(MapRSE.VICTORY_ROAD_1F)
if "Waterfall" not in _why_vr:
    _vr_failures.append(
        f"expected the refusal to NAME the missing capability, got {_why_vr!r} -- "
        "'gated by a capability' must stay distinguishable from 'no path exists'"
    )
assert not _vr_failures, "VICTORY ROAD GATE failures:\n  " + "\n  ".join(_vr_failures)
print("   PASS: the cave cluster is gated on Waterfall and says so; the city stays reachable.")
