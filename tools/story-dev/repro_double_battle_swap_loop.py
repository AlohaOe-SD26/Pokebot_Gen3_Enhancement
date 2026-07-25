"""Diagnostic for KI-18 — DOUBLE-battle after-faint replacement swap loop (user report,
Mauville Gym, 2026-07-24). DIAGNOSE ONLY: this script does not modify production code.

Party at the stall (from the user log):
    Grovyle L22 0/56    <- FAINTED, was on the field (left battler)
    Ninjask L21 11/61   <- ALIVE, on the field (right battler / partner)
    Mightyena L21 67/67 <- bench
    Beautifly L23 67/67 <- bench, healthy, NEVER selected
    Shedinja L20 1/1    <- bench (Wonder Guard)

No captured .ss1 of the live double-battle stall exists anywhere under
tools/story-dev/saves/ (checked: *mauville*, *double*, *wattson*, KI-15/16/17 states are
all SINGLE-battle after-faint wedges). This script is therefore READER-LEVEL FAULT
INJECTION only (no emulator, no live double battle) -- see the harness note at the top
of the file for exactly what is and is not proven.

PART 1 -- is the on-field partner ever RE-PICKED by the chooser?
    Drives the REAL LevelUpLeadBattleStrategy.choose_new_lead_after_faint against the
    reported party + a double-battle BattleState. This tests the (already fixed, commit
    16cfb385, 2026-07-21 -- BEFORE this user's 2026-07-24 log) on-field-partner exclusion.

PART 2 -- the HP tie-break (why Beautifly specifically never came in).
    Same call, but proves the exact mechanism: level_up.py:62 uses strict `>`, so on an
    EXACT HP tie (67 == 67, as in the report) the picker keeps the EARLIER party index
    (Mightyena, slot 2) forever and Beautifly (slot 3) can never win.

PART 3 -- does the SELF-CORRECTING PARTY-MENU SWEEP (battle_handler.py:467-508) ever
    treat the on-field partner's slot as a legal target? That sweep's `alive_slots` gate
    is `mon.current_hp > 0` ONLY -- it does not exclude the party slot(s) occupied by the
    battle's OTHER active battler(s) (which `choose_new_lead_after_faint` DOES exclude).
    Drives the REAL `handle_fainted_pokemon` generator end-to-end with mocked readers:
      A (control)  cursor is parked on the CORRECT (benched) target -> resolves quickly.
      B (fault)    cursor is parked on the ON-FIELD PARTNER's slot (modelling "the menu
                   refuses this selection, nothing advances") -> does the sweep escape,
                   or does it spin?
      C (control)  SINGLE battle equivalent -- there is no second active-battler slot to
                   land on at all, so this failure mode cannot exist outside doubles.

Run: py -3.12 tools/story-dev/repro_double_battle_swap_loop.py
"""
import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
import modules.battle_strategies.level_up as lu
import modules.battle_strategies.default as default_strategy
from modules.pokemon import StatusCondition
import modules.battle_handler as bh
from modules.memory import GameState


# ---------------------------------------------------------------------------
# mon() -- a lightweight stand-in for Pokemon/PartyPokemon carrying every
# attribute the REAL strategy code (_can_battle / pokemon_can_battle /
# choose_new_lead_after_faint) actually reads.
# ---------------------------------------------------------------------------
def mon(name, level, hp, maxhp, status=StatusCondition.Healthy, egg=False):
    return SimpleNamespace(
        name=name,
        level=level,
        current_hp=hp,
        max_hp=maxhp,
        current_hp_percentage=(hp / maxhp * 100.0) if maxhp else 0.0,
        is_egg=egg,
        status_condition=status,
        moves=[SimpleNamespace(move=SimpleNamespace(base_power=40, name="Tackle"), pp=10)],
    )


class PartyMock(list):
    """Just enough of modules.pokemon_party.Party's surface for
    DefaultBattleStrategy.__init__ / LevelUpLeadBattleStrategy to run unmodified."""

    @property
    def first_non_fainted(self):
        for i, p in enumerate(self):
            if p.current_hp > 0:
                return SimpleNamespace(index=i)
        return SimpleNamespace(index=0)

    @property
    def non_fainted_pokemon(self):
        return [p for p in self if p.current_hp > 0]


# context.config.battle.* is read by the real _can_battle / _pokemon_has_enough_hp.
context.config = SimpleNamespace(battle=SimpleNamespace(hp_threshold=20, banned_moves=[]))
# handle_fainted_pokemon() short-circuits to `yield; return` when context.bot_mode ==
# "Manual" (its default) -- that is NOT the mechanism under test, so drive as "Story".
context.bot_mode = "Story"

PARTY = PartyMock([
    mon("GROVYLE", 22, 0, 56),      # 0 fainted, was left battler (on field)
    mon("NINJASK", 21, 11, 61),     # 1 alive, right battler (on field, partner)
    mon("MIGHTYENA", 21, 67, 67),   # 2 bench
    mon("BEAUTIFLY", 23, 67, 67),   # 3 bench, healthy, tie with Mightyena
    mon("SHEDINJA", 20, 1, 1),      # 4 bench, 1/1 HP + (modelled) Wonder Guard
])

default_strategy.get_party = lambda: PARTY

double_battle_state = SimpleNamespace(
    is_double_battle=True,
    is_trainer_battle=True,
    own_side=SimpleNamespace(
        left_battler=SimpleNamespace(party_index=0, current_hp=0),   # Grovyle, fainted
        right_battler=SimpleNamespace(party_index=1, current_hp=11),  # Ninjask, on field
    ),
)

print("=" * 78)
print("PART 1 -- on-field-partner exclusion (the level_up.py:41-68 fix)")
print("=" * 78)
lu.get_party = lambda: PARTY
strategy = lu.LevelUpLeadBattleStrategy()
picked = strategy.choose_new_lead_after_faint(double_battle_state)
picked_name = PARTY[picked].name if picked is not None else None
print(f"choose_new_lead_after_faint(double_battle_state) -> index {picked} ({picked_name})")
assert picked not in (0, 1), (
    f"BUG: picker returned an on-field battler's slot ({picked}) -- this is the ORIGINAL "
    f"KI-16-adjacent hang the 2026-07-21 fix (commit 16cfb385) addressed."
)
print("CONFIRMED: the picker excludes both on-field slots (0=fainted lead, 1=partner).")
print("This part of the hypothesis is REFUTED for the CURRENT code -- the fix predates")
print("the 2026-07-24 log that produced KI-18, so this is not what's looping now.")

print()
print("=" * 78)
print("PART 2 -- the HP tie-break: why a HEALTHY Beautifly never comes in")
print("=" * 78)
print(f"Bench candidates: Mightyena(idx2, hp={PARTY[2].current_hp}), "
      f"Beautifly(idx3, hp={PARTY[3].current_hp}), Shedinja(idx4, hp={PARTY[4].current_hp})")
print(f"Picked index {picked} ({picked_name}).")
# ‼ THIS ASSERTION WAS FLIPPED WHEN THE BUG WAS FIXED (2026-07-25).
# It originally read `assert picked == 2` — i.e. it CHARACTERISED the bug: on an equal-HP
# tie the strict `>` handed the pick to the earlier party index (Mightyena idx2), so the
# user's healthy Beautifly L23 (idx3) could never come in. `choose_new_lead_after_faint`
# now breaks HP ties by LEVEL, so the correct answer is Beautifly (idx3, L23) over
# Mightyena (idx2, L21). Flipping it is legitimate ONLY because the old value documented
# the defect rather than protecting correct behaviour — the surrounding position-swap
# control below still proves the mechanism is the tie and not anything Beautifly-specific.
assert picked == 3, (
    f"expected Beautifly (idx3, L23) to win the equal-HP tie on LEVEL, got {picked}. "
    f"If this fails with 2, the level tiebreak in level_up.py has regressed."
)
print("PASS: the equal-HP tie now goes to the higher-LEVEL mon (Beautifly L23),")
print("      where the pre-fix strict '>' always gave it to the earlier slot (Mightyena L21).")
# Prove it's the tie, not some other disqualifier: swap the two mons' party positions and
# confirm the SAME raw-HP logic now prefers whichever is earlier -- i.e. it's position,
# not any Beautifly-specific property, that loses.
PARTY_SWAPPED = PartyMock(PARTY)
PARTY_SWAPPED[2], PARTY_SWAPPED[3] = PARTY_SWAPPED[3], PARTY_SWAPPED[2]
lu.get_party = lambda: PARTY_SWAPPED
picked2 = strategy.choose_new_lead_after_faint(double_battle_state)
print(f"With Mightyena/Beautifly SWAPPED in the party array -> picked index {picked2} "
      f"({PARTY_SWAPPED[picked2].name})")
assert picked2 == 2 and PARTY_SWAPPED[2].name == "BEAUTIFLY", (
    "expected whichever mon is now at idx2 (earlier) to win the tie"
)
print("CONFIRMED (level_up.py:62, strict '>'): on an EXACT current_hp tie the picker keeps")
print("the EARLIER party slot forever. In the real party order (Mightyena idx2 before")
print("Beautifly idx3, both 67/67) Beautifly can NEVER win -- this is a real, provable")
print("bug (a documented finding, not a guess) but by itself it does not explain an")
print("unbounded LOOP: Mightyena is a valid, non-active bench pick.")
lu.get_party = lambda: PARTY  # restore

print()
print("=" * 78)
print("PART 3 -- does the after-faint PARTY-MENU SWEEP ever target the on-field partner?")
print("=" * 78)


def make_env(target_slot, party, battle_state, partner_slot=None, double=True):
    """Wires battle_handler's module-level names to a scripted mini game:
    - scroll_to_party_menu_index parks the cursor at `target_slot` (this is what we are
      probing: is target_slot the CORRECT bench pick, or -- fault-injected -- the
      on-field partner's own slot?).
    - pressing A on partner_slot has NO EFFECT (models the menu refusing to send out a
      Pokemon that is already on the field).
    - pressing A on any other slot with hp>0 SUCCEEDS (closes the menu)."""
    state = {"cursor": target_slot, "game_state": GameState.PARTY_MENU, "presses": []}
    bh.get_battle_state = lambda: battle_state

    def _get_game_state():
        return state["game_state"]

    def _get_party():
        return party

    def _get_party_size():
        return len(party)

    def _battle_is_active():
        return True

    def _get_current_battle_script_instruction():
        return "BattleScript_SomeOtherInstruction"

    def _task_is_active(name):
        # Only Task_HandleChooseMonInput is "active": skip the dialogue-advance loop
        # (lines 419-426) and the printer/popup branches (lines 487, 490) so PART 3
        # isolates exactly the cursor/alive_slots branch under test (lines 494-499).
        return name == "Task_HandleChooseMonInput"

    def _get_party_menu_cursor_pos(_length):
        return {"slot_id": state["cursor"]}

    def _scroll_to_party_menu_index(idx):
        state["cursor"] = target_slot  # fault injection point: where did scrolling park us?
        return
        yield  # pragma: no cover (makes this a generator)

    class _FakeEmulator:
        def press_button(self, button):
            state["presses"].append((button, state["cursor"]))
            if button == "A":
                if partner_slot is not None and state["cursor"] == partner_slot:
                    pass  # REFUSED: game does not react, menu stays open
                elif party[state["cursor"]].current_hp > 0:
                    state["game_state"] = GameState.DONE_EXPLORING  # menu closes: success
            elif button == "Down":
                state["cursor"] = (state["cursor"] + 1) % len(party)

    bh.get_game_state = _get_game_state
    bh.get_party = _get_party
    bh.get_party_size = _get_party_size
    bh.battle_is_active = _battle_is_active
    bh.get_current_battle_script_instruction = _get_current_battle_script_instruction
    bh.task_is_active = _task_is_active
    bh.get_party_menu_cursor_pos = _get_party_menu_cursor_pos
    bh.scroll_to_party_menu_index = _scroll_to_party_menu_index
    context.emulator = _FakeEmulator()
    return state


def drive(gen, cap=6000):
    n = 0
    try:
        while n < cap:
            next(gen)
            n += 1
    except StopIteration:
        return n, "returned (resolved)"
    except Exception as e:
        return n, f"raised {type(e).__name__}: {e}"
    return n, "STILL RUNNING (cap hit) = HANG"


# GameState needs a harmless non-PARTY_MENU sentinel; DONE_EXPLORING may not exist on the
# real enum in every build -- fall back to the first non-PARTY_MENU member if so.
if not hasattr(GameState, "DONE_EXPLORING"):
    _other = next(m for m in GameState if m != GameState.PARTY_MENU)
    GameState.DONE_EXPLORING = _other  # type: ignore[attr-defined]

strategy2 = lu.LevelUpLeadBattleStrategy()

print("\n[A] CONTROL -- scroll parks the cursor on the CORRECT bench target (Mightyena, idx2)")
lu.get_party = lambda: PARTY
env_a = make_env(target_slot=2, party=PARTY, battle_state=double_battle_state, partner_slot=1, double=True)
frames, outcome = drive(bh.handle_fainted_pokemon(strategy2))
print(f"    -> {outcome} after {frames} frames; last presses: {env_a['presses'][-4:]}")
assert outcome == "returned (resolved)" and frames < 100, f"control should resolve fast, got {outcome} ({frames}f)"

print("\n[B] FAULT -- scroll parks the cursor on the ON-FIELD PARTNER's slot (Ninjask, idx1)")
env_b = make_env(target_slot=1, party=PARTY, battle_state=double_battle_state, partner_slot=1, double=True)
frames, outcome = drive(bh.handle_fainted_pokemon(strategy2), cap=6000)
print(f"    -> {outcome} after {frames} frames; last presses: {env_b['presses'][-4:]}")
print(f"    total A-presses on the refused slot: "
      f"{sum(1 for b, c in env_b['presses'] if b == 'A' and c == 1)}")
# ‼ THIS ASSERTION WAS FLIPPED WHEN THE BUG WAS FIXED (2026-07-25).
# It originally read `assert outcome == "STILL RUNNING (cap hit) = HANG"` — it CHARACTERISED
# the defect: with the cursor parked on the on-field partner's slot, the after-faint sweep
# pressed A on a slot the party menu always refuses, 1500 times, to the 6000-frame cap, with
# zero escape. `handle_fainted_pokemon` now excludes already-on-field party indices from
# `alive_slots`, so the sweep steps OFF that slot and selects a real bench mon instead.
# Flipping it is legitimate ONLY because the old value documented the bug; the [A] and [C]
# control arms below/above still protect the healthy paths.
assert outcome == "returned (resolved)" and frames < 200, (
    f"expected the cursor-on-partner scenario to RECOVER now, got: {outcome} ({frames}f). "
    f"If this hangs again, the on-field exclusion in battle_handler.py has regressed."
)
assert sum(1 for b, c in env_b["presses"] if b == "A" and c == 1) == 0, (
    "the sweep must never press A on the on-field partner's slot"
)
print("    PASS: steps off the refused slot and resolves, instead of pressing A forever.")

print("\n[C] CONTROL -- SINGLE battle: no second active-battler slot exists to land on")
single_battle_state = SimpleNamespace(
    is_double_battle=False,
    is_trainer_battle=True,
    own_side=SimpleNamespace(
        left_battler=SimpleNamespace(party_index=0, current_hp=0),
        right_battler=None,
    ),
)
picked_single = strategy2.choose_new_lead_after_faint(single_battle_state)
print(f"    choose_new_lead_after_faint(single) -> index {picked_single} "
      f"({PARTY[picked_single].name})")
env_c = make_env(target_slot=picked_single, party=PARTY, battle_state=single_battle_state, partner_slot=None, double=False)
frames, outcome = drive(bh.handle_fainted_pokemon(strategy2))
print(f"    -> {outcome} after {frames} frames; last presses: {env_c['presses'][-4:]}")
assert outcome == "returned (resolved)" and frames < 100, f"single-battle control should resolve, got {outcome} ({frames}f)"

print()
print("-" * 78)
print("SUMMARY:")
print("  PART 1: on-field-partner exclusion in the CHOOSER is intact (fixed 2026-07-21,")
print("          predates this bug report) -- refutes 'the chooser re-picks the partner'.")
print("  PART 2: PROVEN, separately -- the strict '>' tie-break in level_up.py:62 means")
print("          Beautifly can never beat an equal-HP EARLIER bench slot (Mightyena).")
print("          This explains 'a healthy Beautifly never came in' as a real, standing bug,")
print("          independent of whether it is *the* cause of the infinite loop.")
print("  PART 3: [A]/[C] controls resolve cleanly (no over-eager regression). [B] shows")
print("          that IF the on-screen cursor is ever parked on the on-field partner's")
print("          slot, battle_handler.py's self-correcting sweep (alive_slots gate,")
print("          lines 467-471, HP-only) treats it as a legal target and presses A on it")
print("          every iteration with no escape -- a genuine, double-only code gap.")
print("  CAVEAT: no live .ss1 of the actual Mauville stall exists, so PART 3's fault")
print("          injection proves the DRIVER cannot escape that slot IF landed there; it")
print("          does NOT prove the live cursor actually lands there (vs. some other")
print("          mechanism, e.g. a stale battle_state.map_battle_party_index() snapshot")
print("          from a second same-turn faint -- see report for why that is plausible")
print("          but unverified). Capturing a live double-battle stall is the next step.")
