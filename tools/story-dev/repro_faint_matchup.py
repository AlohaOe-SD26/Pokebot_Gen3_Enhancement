"""A/B proof for the matchup-aware after-faint chooser (user discussion 2026-07-23).

THE SCENARIO (straight from the user's Wattson log `...093417.log`): lead Grovyle
faints against Wattson's Magneton (Electric/Steel). Bench: Swellow (Normal/Flying,
full HP, Electric-WEAK), Ninjask (Bug/Flying, full HP, Electric-WEAK), Mightyena
(Dark, lower HP, Electric-NEUTRAL). The stock chooser picks by HP → Swellow into a
Thunderbolt. The story chooser must pick Mightyena (neutral) despite its lower HP.

Uses REAL game Species/Type objects (needs a ROM selected, no emulator frames), and
mocks only the battle_state/party containers — the same technique as
repro_double_faint.py.
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.pokemon import get_move_by_name, get_species_by_name

import plugins.custom_modes.story_mode as sm


def mon(species_name, hp, total, level, move_names):
    return SimpleNamespace(
        species=get_species_by_name(species_name),
        current_hp=hp,
        total_hp=total,
        level=level,
        is_egg=False,
        moves=[
            SimpleNamespace(move=get_move_by_name(n), pp=10) for n in move_names
        ],
    )


PARTY = [
    mon("Grovyle", 0, 80, 28, ["Absorb"]),                       # fainted lead
    mon("Swellow", 78, 78, 28, ["Wing Attack", "Quick Attack"]), # full HP, Electric-weak
    mon("Ninjask", 70, 70, 28, ["Fury Cutter"]),                 # full HP, Electric-weak
    mon("Mightyena", 45, 70, 20, ["Bite", "Tackle"]),            # lower HP, Dark = neutral
]

battle_state = SimpleNamespace(
    is_trainer_battle=True,
    is_double_battle=False,
    # ‼ `#24-brokenrepros` 2026-08-23. `default.py:36` reads `is_double_battle_with_partner`,
    # not `is_double_battle`, so this stub AttributeError'd. ⛔ The value is `False`, NOT `True`:
    # `battle_state.py:288` defines it as Double AND **InGamePartner** — an NPC partner (Steven),
    # not any double battle. ⛔ NOTE THIS FILE IS THE ODD ONE OUT: it is a SINGLE battle (Wattson,
    # solo Grovyle vs Magneton — see the docstring above; `is_double_battle=False`,
    # `right_battler=None`). So `False` here is correct TRIVIALLY, because the scenario is not a
    # double battle at all — NOT because it 'models the player's own two mons', which is its
    # SIBLING `repro_double_battle_swap_loop`'s Mauville Gym scenario. *(That sentence was
    # copy-pasted here on 2026-08-23 and a Tier 1 reviewer caught it contradicting this file's own
    # docstring. ⇒ when you paste a rationale between sibling scripts, RE-READ THE SCENARIO.)*
    # ‼ MEASURED (2026-08-23) — and UNLIKE `repro_double_battle_swap_loop`, THIS repro DOES
    # discriminate the value: flipping it to `True` makes the run CRASH with
    # `AttributeError: 'NoneType' object has no attribute 'get_frame_count'`, because this file
    # does not stub `get_party` and `ally_party_indices` then reaches the real `state_cache.party`
    # with no emulator attached. ⛔ STATE THE LIMIT EXACTLY: that proves the value CHANGES THE
    # PATH TAKEN. It does NOT by itself prove `False` is semantically right — that comes from
    # `battle_state.py:288` (Double AND InGamePartner).
    is_double_battle_with_partner=False,
    own_side=SimpleNamespace(left_battler=SimpleNamespace(party_index=0), right_battler=None),
    opponent=SimpleNamespace(
        left_battler=SimpleNamespace(species=get_species_by_name("Magneton")),
        right_battler=None,
    ),
)

# Patch the party source the chooser uses.
import modules.pokemon_party as pp

pp.get_party = lambda: PARTY

# --- A: the STOCK chooser (parent class) — reproduces the bug. ---
import modules.battle_strategies.level_up as lu

lu.get_party = lambda: PARTY
stock_self = SimpleNamespace(pokemon_can_battle=lambda p: True)
stock = lu.LevelUpLeadBattleStrategy.choose_new_lead_after_faint(stock_self, battle_state)
print(f"A (stock, HP-only):    picks slot {stock} = {PARTY[stock].species.name}")
assert stock == 1, "expected the stock chooser to pick full-HP Swellow (the bug)"

# --- B: the STORY chooser — must pick the Electric-neutral Mightyena. ---
class _Harness(sm.LevelUpTravelBattleStrategy):
    def __init__(self):  # skip parent battle-context setup
        pass


story = _Harness().choose_new_lead_after_faint(battle_state)
print(f"B (story, matchup):    picks slot {story} = {PARTY[story].species.name}")
assert story == 3, f"expected Mightyena (slot 3), got slot {story}"

# --- C: sanity — with no Electric threat (a Ground foe), Swellow is fine to send. ---
battle_state.opponent.left_battler = SimpleNamespace(species=get_species_by_name("Sandslash"))
c = _Harness().choose_new_lead_after_faint(battle_state)
print(f"C (story, vs Ground):  picks slot {c} = {PARTY[c].species.name}")
assert c in (1, 3), "vs Ground anything neutral is fine"
assert c == 1, f"expected Swellow (immune-ish Flying, full HP, higher level), got {PARTY[c].species.name}"

print("ALL PASS: stock reproduces the Thunderbolt-food bug; the story chooser fixes it and stays sane.")
