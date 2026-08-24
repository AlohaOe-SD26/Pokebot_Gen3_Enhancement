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
  3. At the threshold (3 defeats), wild         -> a flee strategy = SURVIVAL MODE
  4. Same 3 defeats, but a TRAINER battle       -> NOT fled (a trainer battle cannot be
                                                   fled; the boss/gym path is untouched)
  5. Same 3 defeats, but `train_team` running   -> SwapTrainBattleStrategy (the grind it
                                                   was sent to do is not starved)
  6. A DIFFERENT map with no defeats            -> fights normally (per-map, not global)
  7. The real run01 escalation (25 defeats)     -> fled, i.e. 22 of those 25 whiteouts
                                                   would never have happened
  8. The flee strategy must not trip fight()'s post-battle lead rotation (crashed run03
     of batch 20260726-052205 before StoryFleeStrategy existed)

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


def flees(story, encounter):
    """The PROPERTY under test: does this battle get fled? Asserted via the flee-strategy
    base class, not a class name -- the concrete class changed once already (see CASE 8)."""
    return isinstance(story.on_battle_started(encounter), RunAwayStrategy)


def strategy_of(story, encounter):
    """The strategy OBJECT, so a case can assert on its TYPE without calling
    `on_battle_started` twice -- it prints, and a second call is a second decision."""
    return story.on_battle_started(encounter)


def fights_normally(strategy):
    """The PROPERTY for the "survival mode did NOT engage" cases: the ordinary TRAVEL strategy.

    ‼ `#24-brokenrepros`, 2026-08-23. CASES 1/2/6 used to read `== "LevelUpTravelBattleStrategy"`
    and had been dead-failing: the code returns `StoryItemBattleStrategy`, which SUBCLASSES
    `LevelUpTravelBattleStrategy` (`story_mode.py:417` -> `:118`). The behaviour never changed --
    only the leaf class name did, when the item-using subclass shipped. ⛔ The CHECK was wrong, not
    the subject. `flees()` two functions up had ALREADY learned this ("not a class name -- the
    concrete class changed once already") and the lesson was never applied to the fight side.

    ⛔⛔ AND THE OBVIOUS FIX IS WRONG TOO -- MEASURED BEFORE APPLYING IT:
        issubclass(SwapTrainBattleStrategy, LevelUpTravelBattleStrategy) -> True
    so a bare `isinstance(strategy, LevelUpTravelBattleStrategy)` would make CASES 1/2/6 pass even
    if the code wrongly swap-trained, and would stop discriminating CASE 5's distinct outcome.
    ⇒ the property is "a travel strategy that is NOT the swap-train one".
    """
    return (isinstance(strategy, sm.LevelUpTravelBattleStrategy)
            and not isinstance(strategy, sm.SwapTrainBattleStrategy))


# `swap_train_active` is module state inside early_game; drive it explicitly.
def set_training(active: bool):
    early_game.set_swap_train(active)


set_training(False)

print("=" * 78)
print("CASE 1 -- fresh map, wild encounter -> normal fighting strategy")
print("=" * 78)
st = strategy_of(FakeStory({}), WILD)
print(f"    -> {type(st).__name__}")
check("unchanged default on a clean map", fights_normally(st))

print()
print("=" * 78)
print("CASE 2 -- BELOW threshold (2 defeats) -> still fights (no hair-trigger)")
print("=" * 78)
st = strategy_of(FakeStory({ROUTE110: 2}), WILD)
print(f"    -> {type(st).__name__}")
check("2 defeats is not enough to change behaviour", fights_normally(st))

print()
print("=" * 78)
print("CASE 3 -- AT threshold (3 defeats), wild -> SURVIVAL MODE (flee)")
print("=" * 78)
story = FakeStory({ROUTE110: 3})
print(f"    -> {strategy_name(story, WILD)}")
check("wild battles are fled once the map has demonstrably wiped us", flees(story, WILD))

print()
print("=" * 78)
print("CASE 4 -- same 3 defeats, but a TRAINER battle -> NOT fled")
print("=" * 78)
story = FakeStory({ROUTE110: 3})
print(f"    -> {strategy_name(story, TRAINER)}")
check(
    "a trainer battle is never fled (un-fleeable; boss/gym path untouched)",
    not flees(story, TRAINER),
)

print()
print("=" * 78)
print("CASE 5 -- same 3 defeats, but train_team is RUNNING -> swap-train, not flee")
print("=" * 78)
set_training(True)
st = strategy_of(FakeStory({ROUTE110: 3}), WILD)
set_training(False)
print(f"    -> {type(st).__name__}")
check(
    # Converted from a leaf-name compare in the SAME round, for the SAME reason: leaving a
    # fragile name check beside the one that just broke is how the next one goes stale.
    "an active grind is not starved by survival mode",
    isinstance(st, sm.SwapTrainBattleStrategy),
)

print()
print("=" * 78)
print("CASE 6 -- a DIFFERENT map with no defeats -> fights normally (per-map)")
print("=" * 78)
st = strategy_of(FakeStory({ROUTE110: 25}, here=ROUTE103), WILD)
print(f"    -> {type(st).__name__}")
check("the memory is per-map, not global", fights_normally(st))

print()
print("=" * 78)
print("CASE 7 -- the REAL run01 escalation (25 defeats on ROUTE110) -> fled")
print("=" * 78)
story = FakeStory({ROUTE110: 25})
print(f"    -> {strategy_name(story, WILD)}")
check(
    "22 of run01's 25 ROUTE110 whiteouts would never have happened",
    flees(story, WILD),
)

print()
print("=" * 78)
print("CASE 8 -- the flee strategy must NOT trip fight()'s post-battle lead rotation")
print("=" * 78)
# ‼ REGRESSION GUARD. Batch 20260726-052205 run03 CRASHED here: stock
# RunAwayStrategy.choose_new_lead_after_battle() returns False (annotated `int | None`),
# and BattleListener.fight() rotates whenever that value `is not None` -- so it rotated
# to party index `False` and RotatePokemon raised
#   RuntimeError: Cannot rotate Pokemon #False with itself
# right after "Got away safely!", dropping the run to Manual. Harmless upstream only
# because the framework drove RunAwayStrategy from run_away_from_battle(), which does
# not rotate; survival mode returns it from on_battle_started, which does.
flee = FakeStory({ROUTE110: 3}).on_battle_started(WILD)
verdict = flee.choose_new_lead_after_battle()
print(f"    -> {type(flee).__name__}.choose_new_lead_after_battle() = {verdict!r}")
check(
    "flee strategy returns None (fight() then skips rotation entirely)",
    verdict is None,
)
check(
    "and it is NOT the stock RunAwayStrategy, whose False would rotate to index False",
    type(flee) is not RunAwayStrategy and isinstance(flee, RunAwayStrategy),
)
print(f"    (stock RunAwayStrategy still returns {RunAwayStrategy().choose_new_lead_after_battle()!r} "
      "-- upstream left untouched)")

print()
print("-" * 78)
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS: a repeatedly-lethal map switches from 'level the lead' to 'get through',")
print("without touching trainer battles, the boss path, or an active training grind.")
