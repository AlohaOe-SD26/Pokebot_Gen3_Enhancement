"""REPRO for #24-whiteout — a map that keeps wiping us must stop being treated as XP.

EVIDENCE (live batch 20260725-194810, run01): **25 whiteouts on ROUTE110 in one run** —
wipe, respawn in the Slateport Poké Center, walk back north, wipe again, 25 times. It was
the largest single loss cluster in the batch (31 of 66 losses batch-wide). Nothing noticed
and nothing adapted.

WHY. With no `train_team` session running, `on_battle_started` falls through to
`LevelUpTravelBattleStrategy`, which fights every wild to level the lead. Its own comment
says it "flees only at low HP, which the training loop covers by healing" — but a TRAVEL
leg has no training loop and therefore no healing, so HP only ever drops across
consecutive encounters until the party wipes.

WHAT THIS PROVES (pure decision test, no emulator — the stand-in style of
`repro_boss_plateau.py`): the REAL `StoryMode.on_battle_started` is driven with the real
instance state and its strategy choice is asserted.

  1. Fresh map, wild encounter                  -> LevelUpTravelBattleStrategy (unchanged)
  2. Below the threshold (2 defeats)            -> still fights (no hair-trigger)
  3. At the threshold (3 defeats), wild         -> RunAwayStrategy = SURVIVAL MODE
  4. Same 3 defeats, but a TRAINER battle       -> NOT fled (a trainer battle cannot be
                                                   fled; the boss/gym path is untouched)
  5. Same 3 defeats, but `train_team` running   -> SwapTrainBattleStrategy (the grind it
                                                   was sent to do is not starved)
  6. A DIFFERENT map with no defeats            -> fights normally (per-map, not global)
  7. The real run01 escalation (25 defeats)     -> fled, i.e. 22 of those 25 whiteouts
                                                   would never have happened

Run: py -3.12 tools/story-dev/repro_survival_mode.py
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

import modules.battle_strategies.default as default_strategy_module
import modules.story.early_game as early_game
from modules.battle_strategies.run_away import RunAwayStrategy
from modules.map_data import MapRSE
import plugins.custom_modes.story_mode as sm

# Every strategy inherits DefaultBattleStrategy.__init__, which reads the live party off
# the emulator. This test is about the DECISION, not the emulator, so stand the party in.
# Patched in the module where the name is BOUND (`from ... import get_party` copies the
# reference, so patching modules.pokemon_party would not be seen here).
default_strategy_module.get_party = lambda: SimpleNamespace(
    first_non_fainted=SimpleNamespace(index=0)
)

ROUTE110 = tuple(MapRSE.ROUTE110.value)
ROUTE103 = tuple(MapRSE.ROUTE103.value)

failures = []


def check(label, cond):
    print(f"    {'PASS' if cond else 'FAIL'}  {label}")
    if not cond:
        failures.append(label)


class FakeStory:
    """Only the instance state `on_battle_started` actually reads."""

    SURVIVAL_WHITEOUT_THRESHOLD = sm.StoryMode.SURVIVAL_WHITEOUT_THRESHOLD

    def __init__(self, defeats, here=ROUTE110):
        self._defeat_counts = dict(defeats)
        self._here = here
        self._catch_team_target = 4

    def _location_key(self):
        return self._here

    # never catch, so the test isolates the fight/flee decision
    def _should_catch(self, encounter):
        return False

    on_battle_started = sm.StoryMode.on_battle_started


WILD = SimpleNamespace(is_shiny=False, pokemon=SimpleNamespace(species=SimpleNamespace(name="Electrike")))
TRAINER = None  # the framework passes None for trainer battles


def strategy_name(story, encounter):
    return type(story.on_battle_started(encounter)).__name__


# `swap_train_active` is module state inside early_game; drive it explicitly.
def set_training(active: bool):
    early_game.set_swap_train(active)


set_training(False)

print("=" * 78)
print("CASE 1 -- fresh map, wild encounter -> normal fighting strategy")
print("=" * 78)
s = strategy_name(FakeStory({}), WILD)
print(f"    -> {s}")
check("unchanged default on a clean map", s == "LevelUpTravelBattleStrategy")

print()
print("=" * 78)
print("CASE 2 -- BELOW threshold (2 defeats) -> still fights (no hair-trigger)")
print("=" * 78)
s = strategy_name(FakeStory({ROUTE110: 2}), WILD)
print(f"    -> {s}")
check("2 defeats is not enough to change behaviour", s == "LevelUpTravelBattleStrategy")

print()
print("=" * 78)
print("CASE 3 -- AT threshold (3 defeats), wild -> SURVIVAL MODE (flee)")
print("=" * 78)
s = strategy_name(FakeStory({ROUTE110: 3}), WILD)
print(f"    -> {s}")
check("wild battles are fled once the map has demonstrably wiped us", s == RunAwayStrategy.__name__)

print()
print("=" * 78)
print("CASE 4 -- same 3 defeats, but a TRAINER battle -> NOT fled")
print("=" * 78)
s = strategy_name(FakeStory({ROUTE110: 3}), TRAINER)
print(f"    -> {s}")
check(
    "a trainer battle is never fled (un-fleeable; boss/gym path untouched)",
    s != RunAwayStrategy.__name__,
)

print()
print("=" * 78)
print("CASE 5 -- same 3 defeats, but train_team is RUNNING -> swap-train, not flee")
print("=" * 78)
set_training(True)
s = strategy_name(FakeStory({ROUTE110: 3}), WILD)
set_training(False)
print(f"    -> {s}")
check(
    "an active grind is not starved by survival mode",
    s == "SwapTrainBattleStrategy",
)

print()
print("=" * 78)
print("CASE 6 -- a DIFFERENT map with no defeats -> fights normally (per-map)")
print("=" * 78)
s = strategy_name(FakeStory({ROUTE110: 25}, here=ROUTE103), WILD)
print(f"    -> {s}")
check("the memory is per-map, not global", s == "LevelUpTravelBattleStrategy")

print()
print("=" * 78)
print("CASE 7 -- the REAL run01 escalation (25 defeats on ROUTE110) -> fled")
print("=" * 78)
s = strategy_name(FakeStory({ROUTE110: 25}), WILD)
print(f"    -> {s}")
check(
    "22 of run01's 25 ROUTE110 whiteouts would never have happened",
    s == RunAwayStrategy.__name__,
)

print()
print("-" * 78)
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS: a repeatedly-lethal map switches from 'level the lead' to 'get through',")
print("without touching trainer battles, the boss path, or an active training grind.")
