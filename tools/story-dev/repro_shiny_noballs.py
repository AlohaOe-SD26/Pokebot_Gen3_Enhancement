import pathlib as _pl
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
"""A/B proof (no emulator) for the SHINY catch policy (user directive 2026-07-22):
when the last usable Poké Ball is gone MID-battle,
  - the ordinary StoryCatchStrategy FLEES (correct for team-catching), but
  - the new StoryShinyCatchStrategy must FIGHT ON (never flee a shiny, never Manual).
We mock the battle state + ball lookup and compare the two strategies' decisions on
the SAME input."""
import sys
from types import SimpleNamespace

sys.path.insert(0, _SANDBOX)

from modules.battle_strategies import TurnAction  # noqa: E402
import plugins.custom_modes.story_mode as sm  # noqa: E402


def learned_move(power=40, pp=10):
    return SimpleNamespace(move=SimpleNamespace(base_power=power, name="Tackle"), pp=pp)


active = SimpleNamespace(moves=[learned_move(), None, None, None])
battle_state = SimpleNamespace(
    is_trainer_battle=False,
    own_side=SimpleNamespace(active_battler=active),
    opponent=SimpleNamespace(active_battler=SimpleNamespace()),
)

# Patch BattleStrategyUtil inside story_mode so no real battle context is needed:
# report the first move as strongest & usable.
class _FakeUtil:
    def __init__(self, _):
        pass

    def get_strongest_move_against(self, a, b):
        return 0

    def move_is_usable(self, m):
        return True


sm.BattleStrategyUtil = _FakeUtil

expected_flee = TurnAction.run_away()
expected_fight = TurnAction.use_move(0)


def decide(strategy_cls):
    s = strategy_cls.__new__(strategy_cls)  # skip __init__ (needs game context)
    s._get_best_poke_ball = lambda bs: None  # the fault injection: NO usable ball
    return strategy_cls.decide_turn(s, battle_state)


old = decide(sm.StoryCatchStrategy)
new = decide(sm.StoryShinyCatchStrategy)
print(f"out-of-balls mid-battle: StoryCatchStrategy -> {old}")
print(f"out-of-balls mid-battle: StoryShinyCatchStrategy -> {new}")

ok_old = old == expected_flee
ok_new = new == expected_fight
print(f"A (parent flees, unchanged): {'PASS' if ok_old else 'FAIL'}")
print(f"B (shiny variant fights on): {'PASS' if ok_new else 'FAIL'}")
sys.exit(0 if (ok_old and ok_new) else 1)
