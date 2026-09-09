"""REPRO — in a MULTI battle, the faint replacer must never offer the ALLY's Pokémon (KI-64).

‼‼ THIS EXISTS BECAUSE THE DRIVEN RUN PROVED NOTHING ABOUT IT. §Ch19's end-to-end PASS reported
`whiteouts=0` and **zero faints** — so `choose_new_lead_after_faint` was never called even once, and
the KI-64 fix rode along completely unexercised. A green happy-path run says nothing about an error
path; the branch only exists because something can go wrong, so this makes it go wrong on purpose.

THE BUG. `SPECIAL_BATTLE_STEVEN` (the Space Center) runs `FillPartnerParty`, which writes Steven's
max-IV **Metang L42 / Skarmory L43 / Aggron L44 into `gPlayerParty[3..5]`** and sets the party count
to 6. `get_party()` therefore returns SIX Pokémon, only the first three of which are ours. Both
replacement choosers excluded only the mons currently ON THE FIELD and ranked the rest by condition
— so three fresh high-level mons win outright and the chooser returns the ALLY's slot. The game then
refuses ("Can't switch with ALLY!") and the party menu is handed a target it can never accept.

‼ The guard needed already existed with ZERO callers anywhere in the tree:
`BattleState.is_double_battle_with_partner`. Written, never wired up.

WHAT THIS PROVES, AND HOW. A/B on the SAME fabricated input, no emulator, in milliseconds:
  * ARM A (the OLD rule — exclude only on-field): must return an ALLY slot (3..5). If it does not,
    this repro is not reproducing the bug and its PASS would be meaningless.
  * ARM B (the SHIPPED code): must return one of OUR slots (0..2).
The fixture is deliberately stacked the way the real battle is — the ally's mons are healthier and
higher level than ours — because a fixture where our mon happens to win anyway would pass under both
arms and prove nothing. That positive control is the whole point.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_multi_battle_partner.py
"""

import pathlib
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")

import types

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

BAR = "=" * 96


PLAYER_OT = 12345
STEVEN_OT = 61226   # any id that is not the player's; the real one is STEVEN_OTID


class FakeMon:
    """Only the attributes the choosers actually read — including the ORIGINAL TRAINER.

    ‼ The OT is the whole point of the second version of this repro. Position cannot identify the
    ally (the array gets permuted); the trainer who owns the Pokémon can."""

    def __init__(self, name, level, current_hp, total_hp, ot_id=PLAYER_OT):
        self.species = types.SimpleNamespace(name=name, types=[])
        self.level = level
        self.current_hp = current_hp
        self.total_hp = total_hp
        self.is_egg = False
        self.moves = []
        self.original_trainer = types.SimpleNamespace(id=ot_id)


def make_party():
    """Our three, damaged — then Steven's three, fresh. The real shape of the fight.

    ‼ OURS ARE DELIBERATELY THE WEAKER SIDE. That is what the anchor actually looks like coming out
    of the grunt gauntlet, and it is what makes the bug fire: any rule that ranks by condition
    prefers the ally."""
    return [
        FakeMon("Sceptile", 48, 40, 133),                    # 0 - ours, hurt
        FakeMon("Swellow", 40, 12, 112),                     # 1 - ours, badly hurt
        FakeMon("Mightyena", 44, 55, 130),                   # 2 - ours, hurt
        FakeMon("Metang", 42, 150, 150, ot_id=STEVEN_OT),    # 3 - STEVEN's, full
        FakeMon("Skarmory", 43, 160, 160, ot_id=STEVEN_OT),  # 4 - STEVEN's, full
        FakeMon("Aggron", 44, 170, 170, ot_id=STEVEN_OT),    # 5 - STEVEN's, full
    ]


def make_permuted_party():
    """‼ THE ARRAY AS IT ACTUALLY IS WHEN A REPLACEMENT IS CHOSEN — measured, not imagined.

    Opening the battle party menu runs `UpdatePartyToBattleOrder`, which PHYSICALLY PERMUTES
    `gPlayerParty`. From our own §Ch19 run log (`ch19d.log` f37745):

        [Sceptile|Mightyena|Swellow|Metang|Skarmory|Aggron]
     -> [Sceptile|Metang   |Mightyena|Swellow|Skarmory|Aggron]

    So index 1 is the ALLY's Metang and OUR Swellow has moved to index 3. Any `index < 3` rule
    offers the ally and hides one of ours — it inverts itself in exactly the state it was written
    for. The FIRST version of this repro used only the un-permuted order, which is why it happily
    passed a fix that was wrong."""
    return [
        FakeMon("Sceptile", 49, 40, 135),                    # 0 - ours
        FakeMon("Metang", 42, 150, 150, ot_id=STEVEN_OT),    # 1 - ‼ STEVEN's, at index 1
        FakeMon("Mightyena", 44, 55, 130),                   # 2 - ours
        FakeMon("Swellow", 40, 90, 112),                     # 3 - ‼ OURS, at index 3
        FakeMon("Skarmory", 43, 160, 160, ot_id=STEVEN_OT),  # 4 - STEVEN's
        FakeMon("Aggron", 44, 170, 170, ot_id=STEVEN_OT),    # 5 - STEVEN's
    ]


def fake_battle_state(party, *, with_partner: bool):
    """A stand-in for `BattleState` exposing exactly what the choosers touch.

    `left_battler` is our slot 0 (on the field, so legitimately excluded); `right_battler` is the
    ALLY's active mon at slot 3 — which is how the real battle is laid out, and which is why
    excluding "on-field only" still leaves slots 4 and 5 available to be wrongly chosen."""
    return types.SimpleNamespace(
        is_double_battle=True,
        is_double_battle_with_partner=with_partner,
        own_side=types.SimpleNamespace(
            left_battler=types.SimpleNamespace(party_index=0),
            right_battler=types.SimpleNamespace(party_index=3),
        ),
    )


def old_rule(party, battle_state):
    """‼ THE PRE-FIX LOGIC, TRANSCRIBED — the control arm.

    This is `DefaultBattleStrategy.choose_new_lead_after_faint` as it stood before KI-64: scan the
    WHOLE party, exclude only the two on-field battlers, take the highest current HP."""
    new_lead, best_hp = None, 0
    for index in range(len(party)):
        mon = party[index]
        if battle_state.is_double_battle and index in (
            battle_state.own_side.left_battler.party_index,
            battle_state.own_side.right_battler.party_index,
        ):
            continue
        if not mon.is_egg and mon.current_hp > 0 and mon.current_hp > best_hp:
            new_lead, best_hp = index, mon.current_hp
    return new_lead


print(BAR)
print("REPRO — KI-64: the multi-battle faint replacer must not offer the ALLY's Pokémon")
print(BAR)

party = make_party()
print("\nfixture party (index: who, level, hp) — ours are 0-2, Steven's are 3-5:")
for i, mon in enumerate(party):
    owner = "OURS " if i < 3 else "ALLY "
    print(f"  {i}  {owner} {mon.species.name:<10} L{mon.level:<3} {mon.current_hp}/{mon.total_hp}")
print("\non the field: our slot 0 and the ally's slot 3 (both excluded by BOTH arms)")

results = []

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\nARM A — the OLD rule (control). Must pick an ALLY slot, or this repro is broken.\n{BAR}")
state = fake_battle_state(party, with_partner=True)
picked_old = old_rule(party, state)
who = party[picked_old].species.name if picked_old is not None else "<none>"
side = "ALLY" if (picked_old is not None and picked_old >= 3) else "OURS"
print(f"  old rule returned slot {picked_old} ({who}) -> {side}")
arm_a_ok = picked_old is not None and picked_old >= 3
print(f"  {'[AS PREDICTED]' if arm_a_ok else '[‼ CONTROL FAILED]'} the bug reproduces: {arm_a_ok}")
if not arm_a_ok:
    print("  ‼ Without this, ARM B's pass would be meaningless — a fixture where our mon wins")
    print("    anyway passes under both arms and proves nothing.")
results.append(("A: old rule picks the ALLY (control)", arm_a_ok))

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\nARM B — the SHIPPED code. Must pick one of OURS.\n{BAR}")

import modules.battle_strategies.default as default_mod  # noqa: E402
import modules.player as player_mod  # noqa: E402

# ‼ `ally_party_indices` resolves the player's trainer id through `modules.player.get_player`,
# which needs a running emulator. It FAILS CLOSED (excludes nobody) when that read fails — correct
# in production, but here it would make every arm below silently test nothing. Patch the module
# attribute, because the function imports it at call time.
player_mod.get_player = lambda: types.SimpleNamespace(trainer_id=PLAYER_OT)

# ‼ Patch the name the module RESOLVES, not some other import of it. `choose_new_lead_after_faint`
# calls the module-global `get_party`, so that is the binding to replace.
default_mod.get_party = lambda: party

strategy = object.__new__(default_mod.DefaultBattleStrategy)
picked_new = default_mod.DefaultBattleStrategy.choose_new_lead_after_faint(strategy, state)
who = party[picked_new].species.name if picked_new is not None else "<none>"
side = "ALLY" if (picked_new is not None and picked_new >= 3) else "OURS"
print(f"  shipped code returned slot {picked_new} ({who}) -> {side}")
arm_b_ok = picked_new is not None and 0 <= picked_new < 3
print(f"  {'[AS PREDICTED]' if arm_b_ok else '[‼ FAIL]'} the fix holds: {arm_b_ok}")
results.append(("B: shipped code picks one of OURS", arm_b_ok))

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\nARM C — a NORMAL double battle must be UNAFFECTED (no over-correction).\n{BAR}")

# ‼ A fix that also changed ordinary double battles would be a regression wearing a fix's clothes.
# With no partner, all six are ours and slot 5 (highest HP, not on the field) is the RIGHT answer.
plain = fake_battle_state(party, with_partner=False)
picked_plain = default_mod.DefaultBattleStrategy.choose_new_lead_after_faint(strategy, plain)
print(f"  shipped code (no partner) returned slot {picked_plain} "
      f"({party[picked_plain].species.name if picked_plain is not None else '<none>'})")
arm_c_ok = picked_plain == 5
print(f"  {'[AS PREDICTED]' if arm_c_ok else '[‼ FAIL]'} unchanged for a plain double battle: {arm_c_ok}")
results.append(("C: plain double battle still picks the healthiest benched mon", arm_c_ok))

# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\nARM D — the PERMUTED array (what the chooser really sees). Must still pick OURS.\n{BAR}")

# ‼ THIS ARM EXISTS BECAUSE THE FIRST VERSION OF THIS REPRO PASSED A WRONG FIX. It only ever
# modelled the un-permuted order, so an `index < 3` cut looked correct. Opening the battle party
# menu permutes the array: the ally lands at index 1 and one of OURS at index 3.
perm = make_permuted_party()
default_mod.get_party = lambda: perm
perm_state = types.SimpleNamespace(
    is_double_battle=True,
    is_double_battle_with_partner=True,
    own_side=types.SimpleNamespace(
        left_battler=types.SimpleNamespace(party_index=0),
        right_battler=types.SimpleNamespace(party_index=1),   # the ally's active mon
    ),
)
picked_perm = default_mod.DefaultBattleStrategy.choose_new_lead_after_faint(strategy, perm_state)
who = perm[picked_perm].species.name if picked_perm is not None else "<none>"
ours = picked_perm is not None and perm[picked_perm].original_trainer.id == PLAYER_OT
print(f"  shipped code returned slot {picked_perm} ({who}) -> {'OURS' if ours else 'ALLY'}")
print(f"  ‼ a positional `index < 3` rule would have allowed slot 1 ({perm[1].species.name}, the "
      f"ALLY) and hidden slot 3 ({perm[3].species.name}, OURS)")
print(f"  {'[AS PREDICTED]' if ours else '[‼ FAIL]'} identity beats position: {ours}")
results.append(("D: permuted array still picks OURS (position would have failed)", ours))

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\nARM E — the class the STORY BOT actually uses, not the base class.\n{BAR}")

# ‼‼ THE FIRST FIX WAS DEAD CODE ON THE STORY PATH and this repro could not see it, because it
# asserted `DefaultBattleStrategy` directly. The real MRO is
#   StoryItemBattleStrategy -> LevelUpTravelBattleStrategy -> LevelUpLeadBattleStrategy -> Default
# and `LevelUpLeadBattleStrategy` has its OWN `choose_new_lead_after_faint`, so the base class
# version never ran. This is the playbook's rule about routing a class down a NEW code path: check
# what the framework actually calls, not what you returned.
import modules.battle_strategies.level_up as level_up_mod  # noqa: E402

level_up_mod.get_party = lambda: perm
level_up_mod.ally_party_indices = lambda bs, party=None: default_mod.ally_party_indices(bs, perm)
lead_strategy = object.__new__(level_up_mod.LevelUpLeadBattleStrategy)
lead_strategy.pokemon_can_battle = lambda mon: mon.current_hp > 0
picked_lead = level_up_mod.LevelUpLeadBattleStrategy.choose_new_lead_after_faint(
    lead_strategy, perm_state
)
who = perm[picked_lead].species.name if picked_lead is not None else "<none>"
lead_ours = picked_lead is not None and perm[picked_lead].original_trainer.id == PLAYER_OT
print(f"  LevelUpLeadBattleStrategy returned slot {picked_lead} ({who}) -> "
      f"{'OURS' if lead_ours else 'ALLY'}")
print(f"  {'[AS PREDICTED]' if lead_ours else '[‼ FAIL]'} the story path is guarded too: {lead_ours}")
results.append(("E: the story bot's OWN chooser also excludes the ally", lead_ours))

print(f"\n{BAR}\nSUMMARY\n{BAR}\n")
for label, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
passed = sum(1 for _label, ok in results if ok)
print(f"\n  {passed} / {len(results)} checks pass.")
if passed != len(results):
    print("\nRESULT: FAIL")
    raise SystemExit(1)
print("\nRESULT: ALL PASS — the ally's Pokémon can no longer be chosen as a replacement,")
print("        the bug is demonstrated to have been real, and plain doubles are unchanged.")
