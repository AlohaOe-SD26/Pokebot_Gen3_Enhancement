"""repro_flee_trap_delegate.py — `#26-fleefreeze`: the trapped-flee DELEGATION, proven both ways.

‼ WHAT THIS PROVES, AND WHAT IT DOES NOT. The production fix is one branch in
`LevelUpLeadBattleStrategy._escape` (`modules/battle_strategies/level_up.py`): when
`get_best_escape_method()` returns None (escape IMPOSSIBLE — trapped), delegate to the inherited,
trap-aware KI-52 `_handle_flee` instead of blindly returning `TurnAction.run_away()` (which the
game refuses at selection time — `BattleScript_PrintCantEscapeFromBattle` — freezing the handler
until KI-47 nets it; MEASURED killing 3 of 8 lanes in batch 20260826-063456).
  * THIS FILE proves the DECISION LAYER: the escape-possible path is unchanged, the
    escape-impossible path delegates (never `run_away()`), and the old behaviour is refutable.
  * `_handle_flee`'s INTERNALS (rotate else fight) are NOT re-proven here — they carry their own
    KI-52 history and tests.
  * The LIVE trap (a real Fire-Spin-wrapped sub-threshold lead) is STOCHASTIC: the 2026-08-26
    repro drive exercised the ordinary case cleanly (turn-0 flee at 13/130 HP -> RanAway, 154
    frames) but the trap did not fire. The live arm arrives free with the post-fix validation
    batch (it fired in 3 of 8 lanes over 5 hours on the old code); until then, the live-trap
    branch is DECISION-LAYER-PROVEN ONLY, and the docs say so.

METHOD: no emulator. The strategy object is real; `BattleStrategyUtil.get_best_escape_method` is
monkeypatched per arm (None = trapped, sentinel-tuple = escapable), and `_handle_flee` is replaced
by a recording sentinel — so the assertion is about the WIRING, on the real class, via the real
MRO, with zero simulation of battle internals.

ARMS (each must discriminate):
  A ORDINARY : escape possible -> `_escape` returns the util's method; the sentinel NOT called.
  B TRAPPED  : escape impossible -> the sentinel IS called (right battle_state, a reason naming
               the trap) and its return is passed through unchanged.
  C OLD-BEHAVIOUR CONTROL: in arm B, the result must NOT be `TurnAction.run_away()`'s shape —
               the exact value the bug returned. A refactor restoring it fails HERE.

EXIT: 0 all pass, 1 any fail.  Run: PYTHONUTF8=1 py -3.12 repro_flee_trap_delegate.py
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.battle_strategies import TurnAction  # noqa: E402
from modules.battle_strategies import _util as util_mod  # noqa: E402
from modules.battle_strategies.level_up import LevelUpLeadBattleStrategy  # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label, ("  -- " + detail) if detail else ""))
    if not ok:
        FAILURES.append(label)


class _FakeBattleState:
    """Only what `_escape` itself touches: it is passed through, never introspected here."""

    is_trainer_battle = False


REAL_GBEM = util_mod.BattleStrategyUtil.get_best_escape_method
# __init__ reads the LIVE party (needs an emulator); _escape touches NOTHING __init__ sets
# (verified by reading _escape: it builds a util and calls two methods). __new__ skips it.
strategy = LevelUpLeadBattleStrategy.__new__(LevelUpLeadBattleStrategy)
state = _FakeBattleState()

sentinel_calls = []
SENTINEL_RETURN = ("SENTINEL_ACTION", "SENTINEL_ARG")


def sentinel_handle_flee(battle_state, util, reason, legacy=False):
    sentinel_calls.append({"battle_state": battle_state, "reason": reason, "legacy": legacy})
    return SENTINEL_RETURN


strategy._handle_flee = sentinel_handle_flee

print("REPRO — #26-fleefreeze: the trapped-flee delegation, decision layer")
print("=" * 90)

# ---- ARM A: ORDINARY (escape possible) — the path must be BYTE-UNCHANGED ------------------------
ESCAPABLE = (TurnAction.run_away()[0], None)  # a real escape method, as the util would return


def gbem_escapable(self):
    return ESCAPABLE


util_mod.BattleStrategyUtil.get_best_escape_method = gbem_escapable
try:
    result_a = strategy._escape(state)
finally:
    util_mod.BattleStrategyUtil.get_best_escape_method = REAL_GBEM
check("ARM A (ordinary): escape possible -> the util's method is returned unchanged",
      result_a == ESCAPABLE, repr(result_a))
check("ARM A (ordinary): the delegate was NOT called", not sentinel_calls, str(sentinel_calls))

# ---- ARM B: TRAPPED (escape impossible) — must DELEGATE -----------------------------------------
def gbem_trapped(self):
    return None


util_mod.BattleStrategyUtil.get_best_escape_method = gbem_trapped
try:
    result_b = strategy._escape(state)
finally:
    util_mod.BattleStrategyUtil.get_best_escape_method = REAL_GBEM
check("ARM B (trapped): the KI-52 delegate WAS called exactly once", len(sentinel_calls) == 1)
if sentinel_calls:
    call = sentinel_calls[0]
    check("ARM B: the delegate got the real battle_state", call["battle_state"] is state)
    check("ARM B: the reason names the TRAP (a future reader must see WHY in the log)",
          "trap" in call["reason"].lower(), repr(call["reason"]))
check("ARM B: the delegate's return is passed through unchanged",
      result_b == SENTINEL_RETURN, repr(result_b))

# ---- ARM C: THE OLD BEHAVIOUR IS REFUTABLE ------------------------------------------------------
check("ARM C (control): the trapped result is NOT `TurnAction.run_away()` — the exact value the "
      "bug returned; a refactor restoring the blind fallback fails HERE",
      result_b != TurnAction.run_away(), repr(result_b))

print("=" * 90)
if FAILURES:
    print("RESULT: FAIL — %d problem(s)" % len(FAILURES))
    sys.exit(1)
print("RESULT: ALL PASS — escape-possible unchanged; escape-impossible delegates; the old "
      "behaviour is refuted by construction.")
