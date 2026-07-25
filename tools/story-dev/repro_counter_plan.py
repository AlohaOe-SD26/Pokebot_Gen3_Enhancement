"""Proof for the KI-23 counter-species PLANNER (`modules/story/counter_plan.py`,
punch-list #24-counters).

`_boss_plan_is_hopeless` (story_mode.py) turns "no super-effective answer to Winona's
Flying team" into a list of needed attacking types (Electric/Rock/Ice). This module is
the NEXT step: turn "I need Ice" into "catch a <species> on <map> at <tile>, level band
L<x>-<y>". This script proves it against REAL game data (a running emulator + the real
ROM encounter tables), the same way `repro_fodder_grass.py` does.

WHAT IT PROVES
  1. What `saves/norman_done.ss1` ACTUALLY loads as (never trust a save's filename --
     several saves in this directory have proven misnamed).
  2. For the real Winona answer (["Rock", "Electric", "Ice"]), at least one REACHABLE
     candidate is returned, naming species/map/tile/level band.
  2c. The SAME query re-run from a WINONA-ERA save (`devon_scope_got.ss1`, verified
      post-Badge5/Surf, pre-Badge6) -- since 1/2 above used an EARLIER save
      (`norman_done.ss1`, no Surf yet), showing the answer depends on story position
      and specifically whether Route 118's Electrike flips to reachable once Surf is
      in the party.
  3. Candidates are sorted with reachable ones first.
  4. `allow=None` (the conservative default) never returns a candidate whose map
     carries an AREA_PREREQ entry -- mirrors `best_training_area`'s own contract.
  5. An empty/nonsense type list returns [] and never raises.

Run: py -3.12 tools/story-dev/repro_counter_plan.py
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
context.emulator.load_save_state((REPO / "tools/story-dev/saves/norman_done.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.player import get_player_location
from modules.pokemon_party import get_party
from modules.story.counter_plan import find_counter_candidates, summarise_candidates
from modules.story.training_areas import AREA_PREREQ
import plugins.custom_modes.story_mode as sm

print("=" * 78)
print("0) VERIFY WHAT THIS SAVE ACTUALLY LOADS AS (never trust the filename)")
print("=" * 78)
map_enum, coords = get_player_location()
party = get_party()
print(f"   standing at {map_enum.name} {coords}")
for mon in party:
    if mon is not None:
        print(f"   party: {mon.species.name} L{mon.level} ({mon.current_hp}/{mon.total_hp} HP)")

print()
print("=" * 78)
print('1) find_counter_candidates(["Rock", "Electric", "Ice"]) -- the real Winona answer')
print("=" * 78)
print("   1a) with the LIVE reachability predicate (_training_area_allowed) from this")
print("       save's ACTUAL position (Petalburg, no party mon knows Surf yet):")
cands_live = find_counter_candidates(
    ["Rock", "Electric", "Ice"], allow=sm._training_area_allowed, max_results=10
)
print(f"       {len(cands_live)} candidate(s):")
print("       " + summarise_candidates(cands_live).replace("\n", "\n       "))
live_reachable = [c for c in cands_live if c["reachable"]]
# HONEST FINDING: from THIS real save's real position, the only tiled Electric map
# (Route 118) is surf-gated, and this run has not taught Surf to any party mon yet
# (`_party_can_surf()` is False here -- same save `repro_fodder_grass.py` uses and
# asserts this on). Every other Rock/Electric/Ice land encounter in the whole-game
# index lacks a TRAINING_GRASS-verified tile, so the live predicate (which needs a
# concrete tile to path to) fails closed on them too -- by design, same as
# `best_training_area`. Result: 0 LIVE-reachable candidates from this exact save/
# position. This is a real TRAINING_GRASS coverage gap (no verified Rock/Ice tile
# exists yet, and Route 118's Electrike/Manectric need Surf), not a planner bug --
# reported here rather than hidden.
print(f"       -> {len(live_reachable)} reachable from THIS live position (see note above).")

print()
print("   1b) with allow=None (the conservative default -- see bullet 3 below), which")
print("       permits any area WITHOUT a documented AREA_PREREQ gate:")
cands_default = find_counter_candidates(["Rock", "Electric", "Ice"], max_results=10)
print(f"       {len(cands_default)} candidate(s):")
print("       " + summarise_candidates(cands_default).replace("\n", "\n       "))
assert cands_default, "expected at least one candidate for Rock/Electric/Ice"
reachable_default = [c for c in cands_default if c["reachable"]]
assert reachable_default, f"expected at least one REACHABLE candidate, got: {cands_default}"
first = reachable_default[0]
assert first["species_name"], "candidate must name a species"
assert first["map_enum"] is not None, "candidate must name a map"
assert first["level_band"] != (None, None), "candidate must carry a level band"
print(
    f"       -> PICK: {first['species_name']} on {first['map_enum'].name} "
    f"(tile {first['tile']}, L{first['level_band'][0]}-{first['level_band'][1]})"
)
print("PASS: at least one reachable candidate, fully named (species/map/tile/level band).")

print()
print("=" * 78)
print("1c) SAME query, re-run from a WINONA-ERA save (coordinator follow-up)")
print("=" * 78)
print("    `norman_done.ss1` (used above) is EARLIER than the moment _boss_plan_is_hopeless")
print("    actually fires (at/around Fortree) -- it predates Surf being taught at all. Re-run")
print("    from `devon_scope_got.ss1`, verifying what IT actually loads as first.")
context.emulator.load_save_state((REPO / "tools/story-dev/saves/devon_scope_got.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.memory import get_event_flag

map_enum3, coords3 = get_player_location()
party3 = get_party()
print(f"    standing at {map_enum3.name} {coords3}")
for mon in party3:
    if mon is not None:
        print(f"    party: {mon.species.name} L{mon.level}")
badge5 = get_event_flag("BADGE05_GET")  # Balance Badge (Norman) -- gates Surf usability
badge6 = get_event_flag("BADGE06_GET")  # Feather Badge (Winona)
print(f"    BADGE05_GET (Norman/Balance, unlocks Surf usability) = {badge5}")
print(f"    BADGE06_GET (Winona/Feather)                          = {badge6}")
print(f"    _party_can_surf() = {sm._party_can_surf()}")
assert badge5 and not badge6, (
    f"expected a post-Norman, pre-Winona save (badge5={badge5}, badge6={badge6}) -- "
    "wrong era, do not trust the reachability result below"
)
assert sm._party_can_surf(), "expected a party mon to know Surf at this era"
print("    -> confirmed correct era: Surf usable, Winona not yet beaten.")

cands_winona_era = find_counter_candidates(
    ["Rock", "Electric", "Ice"], allow=sm._training_area_allowed, max_results=15
)
reach_winona_era = [c for c in cands_winona_era if c["reachable"]]
print(f"    {len(cands_winona_era)} candidate(s), {len(reach_winona_era)} reachable:")
print("    " + summarise_candidates(cands_winona_era).replace("\n", "\n    "))

electrike = next((c for c in cands_winona_era if c["species_name"] == "Electrike"), None)
print(
    f"    -> Route 118 Electrike: "
    f"{'reachable' if electrike and electrike['reachable'] else 'STILL UNREACHABLE'}"
    f"{'' if electrike else ' (not even in the list)'}"
)
if not reach_winona_era:
    print(
        "    HONEST FINDING: still 0 reachable, even at the correct era (Surf known,\n"
        "    Badge5 set, Badge6 not). This is NOT the same failure as 1a -- badges/Surf are\n"
        "    no longer the blocker. Isolated hop-by-hop with calculate_path directly: the real\n"
        "    ROM MapConnections DO chain ROUTE120<->FORTREE_CITY<->ROUTE119<->ROUTE118 with no\n"
        "    warp required, yet calculate_path fails even a same-map ROUTE119 walk 130 tiles\n"
        "    long from the player's actual (distant) position. That points at the KI-20\n"
        "    camera-window limitation (`get_map_objects()`/dynamic-collision tiles are only\n"
        "    populated near the live player, so a distant tile gated on one can look\n"
        "    incorrectly blocked) rather than a genuine in-game obstacle -- plausible, but NOT\n"
        "    independently root-caused here, and `calculate_path`/`_training_area_allowed`\n"
        "    are outside this task's files, so it is reported rather than patched.\n"
        "    CONCLUSION for the coordinator's question: the coverage gap is NOT simply 'no\n"
        "    Rock/Ice tile exists' (Route 118 Electrike is a real, in-story-order-reachable\n"
        "    answer) -- it is that the reachability PREDICATE this planner reuses cannot yet\n"
        "    prove that reachability from long range. counter_plan.py itself is working\n"
        "    correctly against whatever `allow` it is given."
    )

print()
print("=" * 78)
print("2) candidates are sorted with reachable ones first")
print("=" * 78)
print("   Proven on the actual Winona candidate list from 1a (allow=_training_area_allowed),")
print("   which since the KI-24 fix contains BOTH reachable and unreachable entries -- so the")
print("   sort proof is non-vacuous on the set we actually care about. A WIDER type set from")
print("   the same live position/predicate is also sorted, as a larger-sample check.")


def _assert_reachable_first(cands, label):
    reach_flags = [c["reachable"] for c in cands]
    first_false = reach_flags.index(False) if False in reach_flags else len(reach_flags)
    assert all(reach_flags[:first_false]), f"{label}: not sorted reachable-first: {reach_flags}"
    assert not any(reach_flags[first_false:]), f"{label}: not sorted reachable-first: {reach_flags}"
    print(f"   {label}: reachable flags in returned order: {reach_flags}")


_assert_reachable_first(cands_live, "Winona set (1a, live predicate)")

# ‼ NON-VACUITY LIVES HERE NOW (moved 2026-07-25). "Sorted reachable-first" is trivially true
# of an all-True or an all-False list, so the sort proof needs a set that genuinely contains
# both. That set is the WINONA list -- the one this planner exists to answer.
#
# It used to be asserted over a deliberately WIDE type set instead, as
#     assert False in [c["reachable"] for c in wide_cands]
# purely because the Winona list was VACUOUSLY all-False under the pre-KI-24 predicate
# (tile-level calculate_path rejected all 10 candidates). That workaround then broke the moment
# the predicate was fixed: the wide set became all-True and "at least one unreachable" had
# nothing to find.
#
# The shape of that assertion was the real mistake. **A test that requires a FAILURE to occur
# inverts as soon as the failure is fixed** -- it makes the suite get redder the more we repair.
# Assert the PROPERTY the test needs (both branches exercised, so the ordering claim has
# content), not a symptom of whatever was broken when it was written.
_live_flags = [c["reachable"] for c in cands_live]
assert True in _live_flags and False in _live_flags, (
    "the Winona candidate list must contain BOTH reachable and unreachable entries, or the "
    f"reachable-first sort proof above is vacuous. Got: {_live_flags}"
)
print(f"   non-vacuous: the Winona set spans both branches ({_live_flags.count(True)} reachable, "
      f"{_live_flags.count(False)} not)")

wide_cands = find_counter_candidates(
    ["Rock", "Electric", "Ice", "Normal", "Bug", "Grass"],
    allow=sm._training_area_allowed,
    max_results=25,
)
_assert_reachable_first(wide_cands, "wider type set (live predicate, same position)")
print("PASS: every returned True precedes every returned False, in both lists.")

print()
print("=" * 78)
print("3) allow=None (conservative default) never returns a prerequisite-carrying candidate")
print("=" * 78)
cands_default = find_counter_candidates(["Rock", "Electric", "Ice"], max_results=50)
gated = [c for c in cands_default if AREA_PREREQ.get(c["map_enum"]) is not None]
print(f"   {len(cands_default)} candidate(s) under allow=None; {len(gated)} carry a prerequisite")
assert not gated, f"allow=None returned prerequisite-carrying candidates: {gated}"
print("PASS: no prerequisite-carrying candidate returned under the conservative default.")

print()
print("=" * 78)
print("4) empty / nonsense type list -> [] and no raise")
print("=" * 78)
assert find_counter_candidates([]) == []
assert find_counter_candidates(None) == []
assert find_counter_candidates(["ThisIsNotARealType"]) == []
print("PASS: [] and ['ThisIsNotARealType'] both return [] without raising.")

print()
print("-" * 78)
print("ALL PASS: counter_plan finds a reachable, fully-specified catch target for the real")
print("Winona type answer, sorts reachable-first, honours the allow=None contract, and")
print("fails safe on empty/nonsense input.")
