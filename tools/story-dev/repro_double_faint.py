import pathlib as _pl
_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
_SAVES = _pl.Path(__file__).resolve().parent / "saves"
"""Reproduce the double-battle after-faint bug WITHOUT an emulator: in a double battle,
LevelUpLeadBattleStrategy.choose_new_lead_after_faint can return the party index of the
Pokemon ALREADY on the field (our other active battler) instead of a benched one, which
strands the real bot on the 'choose a Pokemon' menu.

Scenario: double battle, slots 0 and 1 are on the field. Slot 0 faints. The replacement
MUST come from slots 2-5. We assert it does NOT return slot 1 (the on-field partner)."""
import sys
from types import SimpleNamespace

sys.path.insert(0, _SANDBOX)

import modules.battle_strategies.level_up as lu


def mon(hp):
    return SimpleNamespace(current_hp=hp, is_egg=False)


# Party: slot0 FAINTED (on field), slot1 on-field partner (highest HP), slot2/3 benched.
PARTY = [mon(0), mon(30), mon(20), mon(10)]
lu.get_party = lambda: PARTY  # patch the name used inside level_up.py

# Double battle; our two active battlers are party indices 0 and 1.
battle_state = SimpleNamespace(
    is_double_battle=True,
    own_side=SimpleNamespace(
        left_battler=SimpleNamespace(party_index=0),
        right_battler=SimpleNamespace(party_index=1),
    ),
)

# Minimal mock 'self' so we don't need a real battle context; every mon can battle.
mock_self = SimpleNamespace(pokemon_can_battle=lambda p: True)

result = lu.LevelUpLeadBattleStrategy.choose_new_lead_after_faint(mock_self, battle_state)

print(f"choose_new_lead_after_faint -> party index {result}  (1-based slot {result + 1})")
if result == 1:
    print("BUG REPRODUCED: returned the ON-FIELD partner (slot 2) -> real bot would hang.")
elif result in (2, 3):
    print("FIXED: returned a BENCHED mon (slot 3+), correct.")
else:
    print(f"UNEXPECTED: {result}")
