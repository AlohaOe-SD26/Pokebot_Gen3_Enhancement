"""Proof for the FODDER-GRASS prep fix (user report 2026-07-24: the bot ground L3-4
wilds with a L27-31 team before Norman, i.e. forever).

WHAT IT PROVES
  1. The DECISION table `_prepare_for_fight` now makes, per boss, against the real
     ROM encounter data + the real reachability predicate:
       - NORMAN  (L31 team, standing in Petalburg, local grass Route 102 L3-4)
             -> local patch is FODDER and nothing better is reachable pre-Surf
             -> SKIP the grind (the boss re-attempt is the trainer)
       - WATTSON / ROXANNE / an early team -> UNCHANGED "train locally"
             (the whole point of the conservative gap: proven-good prep must not move)
  2. The picker's disqualifiers really disqualify: HM-gated areas are refused while no
     party mon knows Surf, and the conservative `allow=None` default refuses any area
     carrying a prerequisite at all.
  3. Every heal centre paired with a training area is actually reachable FROM that
     area's tile (else the bot walks the region every time HP dips — the cave-heal
     lesson, 2026-07-22).

Run: py -3.12 tools/story-dev/repro_fodder_grass.py
"""
import pathlib, sys

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

import modules.map as _map
import modules.player as _player
from modules.map_data import MapRSE, PokemonCenter
from modules.map_path import calculate_path
from modules.story.training_areas import TRAINING_GRASS, AREA_PREREQ, best_training_area
import plugins.custom_modes.story_mode as sm

GAP = sm.StoryMode.FODDER_LEVEL_GAP
_orig_pos = _map.get_map_data_for_current_position
_orig_loc = _player.get_player_location

#: Where "standing in <town>" concretely means: that town's Poké Center door. A real,
#: walkable, story-relevant tile — so a tile-level oracle gets a genuine position to plan
#: from instead of a bare map id. (These are the same tiles §3 below paths TO, so they are
#: independently exercised.)
_STAND_TILE = {
    MapRSE.PETALBURG_CITY: PokemonCenter.PetalburgCity,
    MapRSE.MAUVILLE_CITY: PokemonCenter.MauvilleCity,
    MapRSE.RUSTBORO_CITY: PokemonCenter.RustboroCity,
    MapRSE.FALLARBOR_TOWN: PokemonCenter.FallarborTown,
}


def _stand_at(town):
    """Place the player in `town` for the decision under test.

    ‼ PATCH EVERY READER OF "WHERE AM I" (incident 2026-07-25). This helper used to patch
    ONLY `modules.map.get_map_data_for_current_position`. But the predicate under test,
    `_training_area_allowed`, took a SECOND reading of the player's position from
    `modules.player.get_player_location()` before calling `calculate_path` — and that one
    stayed LIVE. So case 5 ("L31 team in Fallarbor") never simulated Fallarbor at all: it
    asked `calculate_path` about the SAVE's real position, `(PETALBURG_CITY, (7,6))`, got a
    `PathFindingError`, and this test recorded that refusal as a *Fallarbor* verdict —
    asserting `SKIP GRIND` for a position it had never put the player in.

    That is the dangerous kind of test bug: a partial mock does not fail loudly, it silently
    exercises the real world and calls it a pass. It went unnoticed because the verdict it
    produced was plausible, and it vetoed a CORRECT change (the `#24-regionreach` switch)
    by making the fix look like a regression.

    So: patch both readers, and keep them consistent with each other. If a future branch
    reads position from a third source, add it HERE — do not let it read live.
    """
    map_enum, tile = _STAND_TILE[town].value
    # The two mocks below must describe the SAME place. Asserting it here is what stops
    # this helper from drifting back into a partial/inconsistent stub.
    assert map_enum is town, f"_STAND_TILE[{town.name}] resolves to {map_enum.name}, not {town.name}"

    class _F:
        map_group_and_number = tuple(town.value)

    _map.get_map_data_for_current_position = lambda: _F()
    _player.get_player_location = lambda: (map_enum, tile)


def _stand_down():
    """Restore every reader `_stand_at` patched (all of them — see above)."""
    _map.get_map_data_for_current_position = _orig_pos
    _player.get_player_location = _orig_loc


def decide(team, local_map, at):
    """Mirror of the decision _prepare_for_fight makes; returns a verdict string."""
    _stand_at(at)
    local = sm._wild_land_max(local_map)
    if local is None or local + GAP >= team:
        return f"TRAIN LOCALLY in {local_map.name} (max L{local}, team L{team})"
    floor = max(local, team - GAP)
    pick = best_training_area(team, min_wild_max=floor, allow=sm._training_area_allowed)
    if pick:
        return f"RELOCATE to {pick[0].name} L{pick[2][0]}-{pick[2][1]}"
    return f"SKIP GRIND (local max L{local} is fodder for L{team}; nothing better reachable)"


print("=" * 74)
print("1) DECISION TABLE")
cases = [
    ("NORMAN  L31 in Petalburg", 31, MapRSE.ROUTE102, MapRSE.PETALBURG_CITY, "SKIP GRIND"),
    ("WATTSON L24 in Mauville ", 24, MapRSE.ROUTE117, MapRSE.MAUVILLE_CITY, "TRAIN LOCALLY"),
    ("ROXANNE L17 in Rustboro ", 17, MapRSE.ROUTE116, MapRSE.RUSTBORO_CITY, "TRAIN LOCALLY"),
    ("early   L9  in Rustboro ", 9, MapRSE.ROUTE116, MapRSE.RUSTBORO_CITY, "TRAIN LOCALLY"),
    # ‼ RE-BASELINED 2026-07-25 — this expectation was "SKIP GRIND", and that was a MOCK
    # ARTEFACT, not a behaviour. `_stand_at()` patched only one of the two position readers
    # (see its docstring), so this case asked `calculate_path` about the save's REAL position
    # — (PETALBURG_CITY,(7,6)) — and recorded its `PathFindingError` as a Fallarbor verdict.
    # It never simulated Fallarbor at all.
    #   THE FEATURE DID NOT CHANGE; THE TEST DID. Three independent sources agree Route 111
    #   IS reachable from Fallarbor:
    #     1. calculate_path(FALLARBOR_TOWN(14,7) -> ROUTE111(25,55))  succeeds;
    #     2. region_reach measures it at 2 hops;
    #     3. training_areas.py's own comment on that entry: "reachable from Fallarbor, NOT
    #        from Mauville/Rustboro/Petalburg".
    # And it is the right ANSWER too: Route 111's L19-22 band is not fodder for a L31 team
    # (gap 9 < FODDER_LEVEL_GAP 12), so relocating there beats skipping the grind.
    ("L31 team in Fallarbor   ", 31, MapRSE.ROUTE102, MapRSE.FALLARBOR_TOWN, "RELOCATE to ROUTE111"),
]
for label, team, local, at, expect in cases:
    got = decide(team, local, at)
    ok = got.startswith(expect)
    print(f"  {label} -> {got}")
    assert ok, f"{label}: expected {expect!r}, got {got!r}"
_stand_down()
print("   all decisions as expected (NORMAN fixed; proven-good prep unchanged)")

print("\n2) DISQUALIFIERS")
_stand_at(MapRSE.PETALBURG_CITY)
assert not sm._party_can_surf(), "this save should have no Surf user yet"
for m, t, band in TRAINING_GRASS:
    if AREA_PREREQ.get(m) == "surf":
        assert not sm._training_area_allowed(m, t, "surf"), f"{m.name} must be refused without Surf"
print(f"   surf-gated areas refused while no party mon knows Surf: "
      f"{[m.name for m in AREA_PREREQ if AREA_PREREQ[m]=='surf']}")
assert best_training_area(31, min_wild_max=4) is None or \
    AREA_PREREQ.get(best_training_area(31, min_wild_max=4)[0]) is None, \
    "conservative allow=None must never propose a prerequisite-carrying area"
print("   conservative allow=None default proposes no prerequisite-carrying area")
_stand_down()

print("\n3) HEAL CENTRES REACHABLE FROM THEIR TRAINING TILE")
print("   (Surf-gated areas are SKIPPED: this save has no Surf user, so no water route")
print("    can path — they need re-verification from a post-Surf checkpoint.)")
heal = sm._training_area_heal_map()
bad = []
for m, t, band in TRAINING_GRASS:
    if t is None or m not in heal:
        continue
    if AREA_PREREQ.get(m) == "surf":
        print(f"   {m.name:16} L{band[0]:>2}-{band[1]:<2} -> {heal[m].name:16} PENDING (surf-gated)")
        continue
    pc_map, pc_tile = heal[m].value
    try:
        calculate_path((m, t), (pc_map, pc_tile), avoid_encounters=False, avoid_scripted_events=False)
        status = "OK"
    except Exception:
        status = "UNREACHABLE"
        bad.append((m.name, heal[m].name))
    print(f"   {m.name:16} L{band[0]:>2}-{band[1]:<2} -> {heal[m].name:16} {status}")
assert not bad, f"heal centre unreachable from its training tile: {bad}"

print("\n" + "-" * 74)
print("ALL PASS: fodder grass is skipped (or relocated from) without disturbing the "
      "prep that already works; disqualifiers hold; every heal centre is reachable.")
