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


def mon(hp, level=10):
    # ‼ `level` is REQUIRED (08-MISTAKES 2026-07-30). This stub had only `current_hp`
    # and `is_egg`; when the KI-18 level tiebreaker landed (2026-07-25) and
    # `level_up.py:73` started scoring `(current_hp, level)`, every run of this script
    # died with `AttributeError: 'SimpleNamespace' object has no attribute 'level'` —
    # and the suite recorded it as "environmental, needs a real mgba" for days. It needs
    # no emulator at all. Case 2 below now COVERS that tiebreaker, so the stub and the
    # scoring rule can no longer drift apart silently.
    return SimpleNamespace(current_hp=hp, is_egg=False, level=level)


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

failures = []


def choose(party, label, expected):
    lu.get_party = lambda: party  # patch the name used inside level_up.py
    result = lu.LevelUpLeadBattleStrategy.choose_new_lead_after_faint(mock_self, battle_state)
    ok = result in expected
    print(
        f"  {'PASS' if ok else 'FAIL'}  {label}\n"
        f"        -> party index {result} (1-based slot {result + 1 if result is not None else '?'}), "
        f"expected one of {expected}"
    )
    if not ok:
        failures.append(label)
    return result


print("=" * 78)
print("CASE 1 — the original bug: never return the ON-FIELD partner")
print("=" * 78)
# slot0 FAINTED (on field), slot1 on-field partner (highest HP), slot2/3 benched.
r = choose([mon(0), mon(30), mon(20), mon(10)], "slot 1 is on the field, so it is ineligible", (2, 3))
if r == 1:
    print("        BUG REPRODUCED: returned the ON-FIELD partner -> the real bot hangs on the menu.")

print()
print("=" * 78)
print("CASE 2 — KI-18 level tiebreaker (the change that broke this script's stub)")
print("=" * 78)
# The user's exact observation: Beautifly L23 (67/67, later slot) never came in while
# Mightyena L21 (67/67, earlier slot) kept winning the tie. Equal HP must break by LEVEL,
# not by slot order — so the LATER, higher-level slot 3 must win.
choose(
    [mon(0), mon(30), mon(67, level=21), mon(67, level=23)],
    "equal HP, higher level in the LATER slot -> level breaks the tie, not slot order",
    (3,),
)

print()
print("=" * 78)
print(f"RESULT: {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'}")
for f in failures:
    print(f"  FAILED: {f}")
print("=" * 78)
sys.exit(1 if failures else 0)
