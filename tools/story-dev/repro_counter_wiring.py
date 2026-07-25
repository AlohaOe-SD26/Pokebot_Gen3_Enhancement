"""Proof for the KI-23 chain WIRING (punch-list #24-counters):
`_boss_plan_is_hopeless` (diagnosis) -> `counter_plan.find_counter_candidates`
(ranked catch targets) -> `region_reach.is_map_reachable` (region-scale reachability),
connected in `story_mode._counter_catch_message` / `story_mode._counter_area_allowed`.

Three proven pieces existed with nothing joining them: a user's overnight run lost to
Winona 41 times with a party far above her levels because it had no super-effective
answer to Flying, and even once the diagnosis (KI-23) and the two planners (KI-24,
KI-24b) existed separately, the raised BotModeError still only named TYPES, never a
concrete target.

WHAT THIS PROVES
  1. (no emulator) `_counter_catch_message` with the planner STUBBED to return
     candidates -> the message contains a species name AND a map name.
  2. (no emulator) planner stubbed to return [] -> message still names the needed
     types (graceful degradation, not a crash).
  3. (no emulator) planner stubbed to RAISE -> message still names the needed types
     and NO exception escapes -- the important one: a planner crash must never turn
     a diagnosed stop into an undiagnosed one.
  4. (live, real ROM data) from the verified Winona-era save `devon_scope_got.ss1`,
     call `find_counter_candidates(["Rock", "Electric", "Ice"], allow=_counter_area_allowed,
     max_results=10)` and print the real candidate list -- the whole point of the
     chain is whether Route 118 Electrike now appears as REACHABLE (KI-24's own
     motivating case), where the OLD `_training_area_allowed` predicate reported zero
     reachable candidates from this exact save (see `repro_counter_plan.py` case 1c).

Run: py -3.12 tools/story-dev/repro_counter_wiring.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

# ---------------------------------------------------------------------------
# Part A -- pure wiring proof, no emulator: drive the real
# `story_mode._counter_catch_message` with `modules.story.counter_plan` stubbed.
# ---------------------------------------------------------------------------
import modules.story.counter_plan as counter_plan_module
import plugins.custom_modes.story_mode as sm

WINONA_CFG = {"name": "Winona", "ace_types": ("Flying",)}
NEEDED = ["Rock", "Electric", "Ice"]

print("=" * 78)
print("CASE 1 -- planner returns candidates -> message names a species AND a map")
print("=" * 78)
class _FakeMapEnum:
    pretty_name = "Route 118"
    name = "ROUTE118"


FAKE_CANDIDATES = [
    {
        "species_name": "Electrike",
        "types": ["Electric"],
        "map_enum": _FakeMapEnum(),
        "tile": (29, 15),
        "level_band": (24, 26),
        "encounter_rate": 30,
        "reachable": True,
        "score": 1_000_000_000.0,
    }
]
counter_plan_module.find_counter_candidates = lambda needed, allow=None, max_results=5: FAKE_CANDIDATES
msg1 = sm._counter_catch_message(WINONA_CFG, 6, NEEDED)
print(f"   message: {msg1!r}")
assert "Electrike" in msg1, f"expected species name 'Electrike' in message: {msg1!r}"
assert "Route 118" in msg1, f"expected map name 'Route 118' in message: {msg1!r}"
for t in NEEDED:
    assert t in msg1, f"expected needed type {t!r} still named in message: {msg1!r}"
print("PASS: message names the concrete candidate (species + map) and still lists the needed types.")

print()
print("=" * 78)
print("CASE 2 -- planner returns [] -> message still names the needed types (graceful degradation)")
print("=" * 78)
counter_plan_module.find_counter_candidates = lambda needed, allow=None, max_results=5: []
msg2 = sm._counter_catch_message(WINONA_CFG, 6, NEEDED)
print(f"   message: {msg2!r}")
for t in NEEDED:
    assert t in msg2, f"expected needed type {t!r} in message: {msg2!r}"
assert "Nearest reachable counters" not in msg2, f"empty candidate list should not append a counters clause: {msg2!r}"
print("PASS: empty candidate list degrades gracefully to the type-only diagnosis.")

print()
print("=" * 78)
print("CASE 3 -- planner RAISES -> message still names the needed types, NO exception escapes")
print("=" * 78)


def _boom(needed, allow=None, max_results=5):
    raise RuntimeError("simulated planner failure (KI-23 wiring must survive this)")


counter_plan_module.find_counter_candidates = _boom
msg3 = sm._counter_catch_message(WINONA_CFG, 6, NEEDED)  # must NOT raise
print(f"   message: {msg3!r}")
for t in NEEDED:
    assert t in msg3, f"expected needed type {t!r} in message: {msg3!r}"
print("PASS: a raising planner never escapes -- the type-only diagnosis still comes through.")

print()
print("-" * 78)
print("PART A ALL PASS: the wiring is fail-safe in all three planner outcomes.")
print("-" * 78)

# Restore the real function before Part B actually uses it against real ROM data.
import importlib

importlib.reload(counter_plan_module)

# ---------------------------------------------------------------------------
# Part B -- LIVE check against real ROM data: does the fixed reachability oracle
# actually surface Route 118 Electrike as reachable from the Winona-era save?
# ---------------------------------------------------------------------------
print()
print("=" * 78)
print("PART B -- LIVE: devon_scope_got.ss1, find_counter_candidates + _counter_area_allowed")
print("=" * 78)

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

from modules.memory import get_event_flag
from modules.player import get_player_location
from modules.pokemon_party import get_party
from modules.story.counter_plan import find_counter_candidates, summarise_candidates

print("0) VERIFY WHAT THIS SAVE ACTUALLY LOADS AS (never trust the filename)")
map_enum, coords = get_player_location()
print(f"   standing at {map_enum.name} {coords}")
for mon in get_party():
    if mon is not None:
        print(f"   party: {mon.species.name} L{mon.level}")
badge5 = get_event_flag("BADGE05_GET")
badge6 = get_event_flag("BADGE06_GET")
print(f"   BADGE05_GET (Balance, unlocks Surf) = {badge5}")
print(f"   BADGE06_GET (Winona/Feather)         = {badge6}")
print(f"   _party_can_surf() = {sm._party_can_surf()}")

print()
print('1) find_counter_candidates(["Rock", "Electric", "Ice"], allow=sm._counter_area_allowed, max_hops=4)')
cands = find_counter_candidates(NEEDED, allow=sm._counter_area_allowed, max_results=10)
print(f"   {len(cands)} candidate(s):")
print("   " + summarise_candidates(cands).replace("\n", "\n   "))

electrike = next((c for c in cands if c["species_name"] == "Electrike"), None)
if electrike is not None:
    print(
        f"   -> Route 118 Electrike found: reachable={electrike['reachable']}, "
        f"map={electrike['map_enum'].name}, tile={electrike['tile']}, "
        f"level_band={electrike['level_band']}, rate={electrike['encounter_rate']}%"
    )
else:
    print("   -> Route 118 Electrike NOT in the candidate list at all.")

reachable = [c for c in cands if c["reachable"]]
print(f"   -> {len(reachable)}/{len(cands)} candidates reachable via _counter_area_allowed.")
print()
print("-" * 78)
if electrike is not None and electrike["reachable"]:
    print("CHAIN CONFIRMED: Route 118 Electrike -- the real Winona answer -- now appears")
    print("REACHABLE through _counter_area_allowed (region_reach), where the OLD")
    print("_training_area_allowed predicate reported 0 reachable candidates from this")
    print("exact save (see repro_counter_plan.py case 1c). Gap closed.")
else:
    print("HONEST FINDING: Route 118 Electrike did NOT come back reachable here -- report")
    print("this rather than assume the chain works. See the candidate list above.")
print("-" * 78)
