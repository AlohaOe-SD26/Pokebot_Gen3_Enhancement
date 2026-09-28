"""Regression: the after-faint recovery sweep must compare indices in the CURSOR's space (KI-34).

‼‼ PARTLY SUPERSEDED 2026-09-28 (`#27-ki47range`, KI-47) — READ THIS BEFORE THE REST.
The premise below that `alive_slots` is in REGULAR party order is WRONG. `party_in_menu = get_party()` is read with
the in-battle menu OPEN, and `OpenPartyMenuInBattle` has already permuted `gPlayerParty` into MENU order
(`UpdatePartyToBattleOrder`, decomp-checked), so KI-34's `_to_menu_order` converted menu slots a SECOND time. Measured
with `--driver ki47oor`: after one natural switch that sent the WRONG mon (arm `Swp`), and with the enemy's order
(left in `gBattlePartyCurrentOrder` by `SwitchPartyOrder` after an enemy send-out) it produced unreachable slots 4/5
at party 4: the KI-47 freeze (arm `Foor`). What the user saw in KI-34 (the bot picking an ON-FIELD mon) was real; its
cause was the RAW `_on_field` comparison that KI-66 fixed three weeks later. The chooser now decides by IDENTITY
(`modules/faint_chooser.py`); the gate is `probe_faint_chooser_identity.py`. What stays true here: the arithmetic of
`map_battle_party_index`, and the sweep's refusal-learning invariants asserted at the end.

FOUND BY THE USER, WATCHING THE SCREEN — not by telemetry:
    "the bot is selecting a live pokemon in the pokeparty, but its one that is already in the
     field (cannot select an already active pokemon to swap out/swap out for a fainted pokemon)"

That is impossible if `alive_slots` is correct — and it IS correct, in its own index space.
**The comparison was not.** Two party index spaces exist in a Gen-3 battle:

  * REGULAR party order      — what `get_party()` returns
  * IN-BATTLE party-menu order — what `gPartyMenu.slotId` reports; the two DIVERGE once mons
    have been switched in and out, i.e. exactly a double battle after a faint.

`BattleState.map_battle_party_index()` exists solely to convert between them.
`handle_fainted_pokemon` built `alive_slots` from `get_party()` (regular) and compared it
against a cursor read in MENU order — while its own PRIMARY path mapped correctly 60 lines
earlier. Only the recovery sweep never mirrored it.

MEASURED COST (bundle `20260730-062818`): `presses={'A': 289}` with a STATIC cursor, 3,975
give-ups in P3 alone, ~23,857,950 frames — about 7.8 complete runs — burned in one night, and
that lane finished 5 badge-earning runs against P2's 19.

No emulator needed: this drives the real `map_battle_party_index` with a hand-built battle
party order, and asserts on the source of the sweep.
"""
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules.battle_state import BattleState  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


def battle_state_with_order(order):
    """A BattleState whose in-battle party order is `order` (menu position -> party index).

    The ROM packs two 4-bit party indices per byte, high nibble first — the same layout
    `map_battle_party_index` decodes.
    """
    packed = bytearray(3)
    for menu_pos, party_index in enumerate(order):
        if menu_pos % 2 == 0:
            packed[menu_pos // 2] |= (party_index & 0xF) << 4
        else:
            packed[menu_pos // 2] |= party_index & 0xF
    bs = BattleState.__new__(BattleState)
    bs._battler_party_order = bytes(packed)
    return bs


print("== the identity case: orders agree, mapping is a no-op ==")
bs = battle_state_with_order([0, 1, 2, 3, 4, 5])
for i in range(6):
    check(bs.map_battle_party_index(i) == i, f"party {i} -> menu {i}")

print("\n== ‼ THE REAL CASE: orders DIVERGE after switches ==")
# Party order [2,0,1,3,...] means: menu slot 0 shows party mon 2, menu slot 1 shows party mon 0.
bs = battle_state_with_order([2, 0, 1, 3, 4, 5])
check(bs.map_battle_party_index(2) == 0, "party 2 is at MENU slot 0")
check(bs.map_battle_party_index(0) == 1, "party 0 is at MENU slot 1")
check(bs.map_battle_party_index(1) == 2, "party 1 is at MENU slot 2")

print("\n== ‼ THE BUG, reproduced as arithmetic ==")
# The scenario the user watched: party 0 and 2 are the ON-FIELD pair (0 just fainted), so the
# eligible bench in PARTY order is [1, 3]. Under the diverged order above, those live at MENU
# slots 2 and 3 — while MENU slot 1 is party mon 0, which is ON THE FIELD.
alive_party = [1, 3]
on_field_party = [0, 2]
alive_menu = sorted(bs.map_battle_party_index(i) for i in alive_party)
onfield_menu = sorted(bs.map_battle_party_index(i) for i in on_field_party)
print(f"     alive(party-order)={alive_party} -> alive(menu-order)={alive_menu}")
print(f"     on-field(party-order)={on_field_party} -> on-field(menu-order)={onfield_menu}")
cursor = 1  # the value actually logged in the wedge
check(cursor in alive_party,
      "OLD test `cursor in alive_slots` says slot 1 is SELECTABLE  <- the bug")
check(cursor not in alive_menu,
      "NEW test `cursor in alive_slots_menu` says slot 1 is NOT selectable  <- correct")
check(cursor in onfield_menu,
      "...because MENU slot 1 is an ON-FIELD mon — exactly what the user saw the bot pick")

print("\n== the sweep now compares in menu space ==")
src = (SANDBOX / "modules" / "battle_handler.py").read_text(encoding="utf-8")
# ‼ Slice to the SYNTACTIC UNIT, not a character count. A fixed +5000 window silently fell
# short once explanatory comments were added, failing three assertions on correct code — the
# same anchoring class of error recorded in 08-MISTAKES 2026-07-29/30.
i = src.index("party_in_menu = get_party()")
_end = src.find(chr(10) + "def ", i)
sweep = src[i:_end if _end != -1 else len(src)]
check("alive_slots_menu" in sweep, "the sweep builds a menu-order set")
# ‼ SUPERSEDED 2026-09-28 (`#27-ki47range`): this asserted that the sweep maps through `map_battle_party_index`. That
# premise was wrong (`party_in_menu` is ALREADY menu order) and the second map WAS the KI-47 freeze. The invariant now
# lives in the registered gate `probe_faint_chooser_identity.py` (W1: every conversion is confined to the fault arm
# `POKEBOT_KI47_FAULT_STALEMAP`); this repro no longer asserts it either way.
# ‼ ASSERT THE INVARIANT, NOT THE VARIABLE NAME (2026-07-31). These read
# `cursor in alive_slots_menu` literally and went red when the KI-38 fix routed the same
# comparison through `_candidates` — a menu-order set derived from `alive_slots_menu` minus
# the slots the game has actually REFUSED. The property that matters is unchanged: both
# branches compare the cursor against a MENU-ORDER set, never against party order. Third
# name/string-anchored assertion to break on correct code in two days; see 08-MISTAKES.
check("_candidates = alive_slots_menu - _refused" in sweep,
      "the candidate set is derived from the MENU-order set")
check('button = "A" if cursor in _candidates else "B"' in sweep,
      "the selection-popup branch tests that menu-order candidate set")
check("cursor not in _candidates" in sweep,
      "the cursor-walk branch tests that menu-order candidate set")
# ‼ The KI-38 fix's own termination guarantee: a refused slot must be REMEMBERED, or the
# cursor never moves off it and the loop presses A for ever (presses={'A': 273}).
check("_refused.add(_last_a_cursor)" in sweep,
      "a refused selection is recorded, so the cursor cannot re-try it for ever")
check("_candidates = {i for i in range(len(party_in_menu))} - _refused" in sweep,
      "…and if the model's set empties, it falls back to every unrefused slot")
check("cursor in alive_slots else" not in sweep and "cursor not in alive_slots:" not in sweep,
      "‼ no raw party-order comparison against the cursor survives")

print("\n== the OUTCOME is bounded, not just the frames ==")
import modules.battle_handler as bh  # noqa: E402

check(hasattr(bh, "FAINT_CHOOSER_GIVEUP_LIMIT"), "a per-battle give-up limit exists")
# ‼ ASSERT THE INVARIANT, NOT THE LITERAL (2026-07-30). This read `== 3` and broke the moment
# the value was deliberately retuned to 20 as the KI-38/KI-40 mitigation — a red sweep for a
# change that was correct. The number is empirical and expected to move again; what this repro
# actually guards is that the limit EXISTS, is FINITE (KI-36: the per-run frame budget cannot
# fire while a battle handler holds the flat stack, so unbounded means unbounded) and is
# generous enough not to abandon a battle after a few honest tries. Same brittleness class as
# repro_navigate_failfast's string assertion, fixed the same day — see 08-MISTAKES 2026-07-30.
check(
    isinstance(bh.FAINT_CHOOSER_GIVEUP_LIMIT, int)
    and 3 < bh.FAINT_CHOOSER_GIVEUP_LIMIT <= bh.FAINT_CHOOSER_GIVEUP_MAX,
    f"limit is finite and > the old too-tight 3 "
    f"(got {bh.FAINT_CHOOSER_GIVEUP_LIMIT}, max {bh.FAINT_CHOOSER_GIVEUP_MAX})",
)
check("_faint_chooser_giveups = 0" in src, "the counter resets per battle")
check("request_mode_recovery" in sweep,
      "on exceeding it, the run gets a RECOVERABLE derail via the battle-fault channel")
check("raise BotModeError" not in sweep,
      "‼ and it never RAISES from battle code — that would reach main_loop and force Manual")

print("\n== KI-36 net: the stall detector can END an in-battle wedge ==")
dl = (SANDBOX / "modules" / "debug_logger.py").read_text(encoding="utf-8")
check("_BATTLE_STALL_FAULT_AFTER" in dl, "a fault threshold exists")
import modules.debug_logger as dlm  # noqa: E402

check(dlm._BATTLE_STALL_FAULT_AFTER > dlm._BATTLE_STALL_DUMP_AFTER * 3,
      f"it is >3x the dump threshold ({dlm._BATTLE_STALL_FAULT_AFTER} vs {dlm._BATTLE_STALL_DUMP_AFTER})")
check("request_mode_recovery" in dl,
      "it hands over via the battle-fault channel, not by raising")
check("in_battle and _stall_frames == _BATTLE_STALL_FAULT_AFTER" in dl,
      "it fires ONCE, and only in battle")

print("")
print("== EVERY listener that can sit above the mode must honour a pending fault ==")
# Measured (user log 20260730-081347): handle_fainted_pokemon handed over correctly at
# f1,797,401 and NOTHING claimed it, because TrainerApproachListener.handle_trainer_approach
# was on top of the stack pressing B while the trainer script stayed active -- starving the
# mode of frames. The run sat at state=3 for 1,182,000 frames. In the sibling ENDLESS-RESET
# log the same handover was claimed ONE FRAME later, because there the mode was reachable.
lis = (SANDBOX / "modules" / "modes" / "_listeners.py").read_text(encoding="utf-8")
i_ta = lis.index("def handle_trainer_approach")
ta = lis[i_ta:lis.find(chr(10) + "class ", i_ta)]
check("battle_fault_pending()" in ta,
      "handle_trainer_approach checks battle_fault_pending()")
check("return" in ta, "…and RETURNS, popping back to the mode")
check("raise" not in ta, "…never raises (that would reach main_loop and force Manual)")
i_bl = lis.index("class BattleListener")
bl = lis[i_bl:i_ta]
check("battle_fault_pending()" in bl,
      "BattleListener still has the same guard it always had (the one this mirrors)")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
