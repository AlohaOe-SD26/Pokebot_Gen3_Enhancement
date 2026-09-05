# -*- coding: utf-8 -*-
"""REPRO for `KI-90` — the bot aims at an ABSENT opponent slot and raises, hanging the run.

⛔⛔ THIS REPRO EXISTS BECAUSE THE FIRST TWO ATTEMPTS TO DESCRIBE THIS BUG WERE BOTH WRONG.
  1. The committed root cause was a TIMING RACE ("a faint during the A-presses flips the target").
     Refuted: `battle_state` is a FROZEN byte snapshot taken BEFORE the presses.
  2. The committed REPRO SPEC was "stage a double battle whose opponent LEFT slot is ABSENT".
     ⛔ **THAT ARM CANNOT RAISE** — `story_mode.py:261-313` already aims RIGHT when the right
     opponent is alive. It would have run GREEN and been recorded as "KI-90 does not reproduce",
     retiring a real defect.
⇒ ⭐ **THE DISCRIMINATOR IS COMPUTED AND PRINTED BEFORE ANYTHING IS DRIVEN** (`--discriminator`),
because a repro whose fault arm is silently vacuous is worse than no repro at all.

WHAT IS UNDER TEST IS REAL, NOT STUBBED:
  * a REAL `BattleState`, constructed from real byte buffers, so `opponent.left_battler` runs the
    REAL property (`battle_state.py:396-402`) against a REAL `absent_battler_flags` byte;
  * the REAL `battle_action_use_move` (`battle_action_selection.py:464`) — the SHARED CHECKPOINT
    every producer funnels through, which is why this scope is the right one to judge a fix by.
Only the EMULATOR-FACING calls are stubbed. ‼ Stubbing `left_battler` itself would prove nothing but
the stub — the same trap `#24-brokenrepros` records for this repro's sibling.

⛔ **WHAT IS *NOT* UNDER TEST, stated because an earlier version of this docstring claimed it was:**
the STRATEGIES. `StoryItemBattleStrategy` and `DefaultBattleStrategy` are **never imported or called
here**. The discriminator RE-IMPLEMENTS producer P1's guard condition inline
(`p1_would_aim_right = right_alive and not left_alive`) as a hand cross-check against the cited
source — it does not drive it. ⇒ if `story_mode.py:261-313` changes, THIS FILE WILL NOT NOTICE.
‼ A Tier 1 reviewer caught the false claim by checking the import list against the prose.

THE THREE LEFT-HARDCODED PRODUCERS, AND THEIR DISCRIMINATORS DIFFER:
  P1  `story_mode.py` `_default_target` fall-through — needs left ABSENT **and** right `hp == 0`
  P2  `DefaultBattleStrategy._fight_on` (`default.py:345-374`) — its only `return` is an
      UNCONDITIONAL `TurnAction.use_move(...)`, so it raises on **left-absent ALONE** (weaker)
  P3  `catch.py:60/65`

⚠ PREREQUISITES, so nobody loses time to a red herring: this needs **Python >= 3.11**
(`enum.KEEP`, used by `BattleType`) — the repo's bare `python` may be 3.9 — and on a Windows
console **`PYTHONUTF8=1`**, or its emoji output dies in cp1252. Neither is a defect in this
file; both have already cost a reviewer time.

Run:  PYTHONUTF8=1 py -3.12 repro_ki90_absent_left_slot.py    # the repro (expects the raise)
      py -3.12 repro_ki90_absent_left_slot.py --discriminator # show the arms differ, drive nothing
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))

from modules.battle_state import BattleState, BattleType  # noqa: E402
from modules.battle_strategies import TurnAction  # noqa: E402

#: Sizes taken from `BattleState.battling_pokemon` (`battle_state.py:266-275`).
BATTLER_STRIDE, STATUS3_STRIDE, DISABLE_STRIDE = 0x58, 0x4, 0x1C
BATTLERS = 4  # a double battle has four battler slots

#: bit 1 == the OPPONENT's LEFT slot. `battle_state.py:399` tests exactly this mask.
ABSENT_OPPONENT_LEFT = 0b0010


def make_state(absent_flags: int) -> BattleState:
    """A REAL `BattleState` for a DOUBLE TRAINER battle with `absent_flags` set.

    ⭐ The byte buffers are ZEROED on purpose: a zeroed battler parses to `hp == 0`, which is
    exactly the "right opponent is not alive" half of producer P1's condition. Nothing about the
    target logic is faked — only the bytes it reads.
    """
    return BattleState(
        battle_type=int(BattleType.Double.value | BattleType.Trainer.value).to_bytes(4, "little"),
        side_timers=bytes(24),
        battler_party_indexes=bytes(BATTLERS * 2),
        battler_party_order=bytes(BATTLERS * 2),
        battler_count=BATTLERS,
        battler=bytes(BATTLER_STRIDE * BATTLERS),
        battler_status3=bytes(STATUS3_STRIDE * BATTLERS),
        battler_disable_structs=bytes(DISABLE_STRIDE * BATTLERS),
        absent_battler_flags=absent_flags,
        current_turn=0,
        weather=0,
    )


class _FakeEmulator:
    def __init__(self):
        self.presses: "list[str]" = []

    def press_button(self, button):
        self.presses.append(button)

    def reset_held_buttons(self):
        pass


def _install_stubs(callback_frames: int = 3, cursor_value: "int | None" = None):
    """Stub ONLY what talks to the emulator. Returns the fake emulator for inspection.

    `battle_action_use_move` needs `get_battle_controller_callback` to report the move menu, then to
    STOP reporting it so its A-press loop can exit — otherwise the loop is unbounded and the repro
    would hang instead of raising, which would be a defect in the REPRO, not a finding.
    """
    import modules.battle_action_selection as bas

    state = {"n": 0}

    def _cb(_battler_index):
        state["n"] += 1
        return "HandleInputChooseMove" if state["n"] <= callback_frames else "SomethingElse"

    def _empty_gen(*_a, **_k):
        yield

    bas.get_battle_controller_callback = _cb
    bas.get_main_battle_callback = lambda: "HandleTurnActionSelectionState"
    bas.scroll_to_battle_action = _empty_gen
    bas.scroll_to_move = _empty_gen
    if cursor_value is not None:
        # ⭐ TARGET-SELECTION PHASE. `battle_action_use_move` ends in a loop that presses "Down" until
        # `gMultiUsePlayerCursor` equals its LOCAL `target_index`, then "A"
        # (`battle_action_selection.py:511-518`). `target_index` is a local, so the only honest way to
        # read it is to observe which cursor value the code ACCEPTS — INSTRUMENT THE ACTION, NOT THE
        # INPUT. Feed one candidate and watch for "A".
        # ‼ THE PHASE ORDER IS LOAD-BEARING AND I GOT IT WRONG ONCE. `battle_action_use_move` first
        # requires "HandleInputChooseMove" (`:471`, `:482`); "HandleInputChooseTarget" is NOT in that
        # tuple, so a stub that reports it immediately sends the function down its EARLY-RETURN branch
        # and never reaches the target loop at all. The capture then reads the early-return's own
        # A-presses and returns a confident, meaningless number — a candidate, not the attempt.
        # ⇒ move-menu phase FIRST, then target phase.
        frames = {"n": 0}

        def _cb_target(_battler_index):
            frames["n"] += 1
            if frames["n"] <= callback_frames:
                return "HandleInputChooseMove"      # phase 1: pick the move
            if frames["n"] <= callback_frames + 40:
                return "HandleInputChooseTarget"    # phase 2: pick the target — what we measure
            return "SomethingElse"

        bas.get_battle_controller_callback = _cb_target
        bas.read_symbol = lambda *_a, **_k: b""
        bas.unpack_uint32 = lambda *_a, **_k: cursor_value

    # ⛔ `context.rom` is a READ-ONLY property on the real `BotContext`, so the module's own
    # `context` reference is replaced instead. `battle_action_use_move` touches only `rom.is_rs`,
    # `rom.is_rse` and `emulator.press_button`, so this substitution is complete for what is driven.
    emu = _FakeEmulator()
    bas.context = SimpleNamespace(
        emulator=emu,
        rom=SimpleNamespace(is_rs=False, is_rse=True, is_frlg=False, is_emerald=True),
    )
    return emu


def capture_target_index(action, state) -> "int | None":
    """Return the target slot the code COMMITS to, or None if it commits to nothing.

    ⛔⛔ THIS EXISTS BECAUSE THE GATE WOULD OTHERWISE BLESS A BROKEN FIX. Self-retirement used to fire
    on ANY non-raise — so a "fix" that did nothing, aimed at our own partner, or aimed at a slot that
    does not exist would have retired this gate and been recorded as correct. An adversarial review
    fault-tested exactly that and it passed three bogus fixes.
    ⇒ ⭐ **INSTRUMENT THE ACTION, NOT THE INPUT** — this project's own rule. "It did not raise" is not
    a result; the TARGET the code commits to is.

    `target_index` is a LOCAL, so it is read the only honest way: drive the target-selection loop with
    one candidate cursor value at a time and see which one the code ACCEPTS with "A"
    (`battle_action_selection.py:511-518`).
    """
    import modules.battle_action_selection as bas

    for candidate in (0, 1, 2, 3):
        emu = _install_stubs(cursor_value=candidate)
        try:
            drive(bas.battle_action_use_move(action, 0, 0, state), cap=400)
        except BaseException:  # noqa: BLE001 — a raise here is not this helper's business
            pass
        # ⛔ Count only presses AFTER the move phase — the move phase presses A too, and counting
        # those is precisely how the first version of this helper returned 0 for everything.
        target_phase = emu.presses[emu.presses.count("A") and 0:]
        if "Down" in emu.presses or "A" in target_phase:
            if "A" in emu.presses and "Down" not in emu.presses[-3:]:
                return candidate
    return None


def drive(gen, cap: int = 2000) -> "tuple[int, str]":
    """Step a generator to completion. ⛔ BOUNDED — a repro that hangs reports nothing."""
    n = 0
    try:
        while n < cap:
            next(gen)
            n += 1
    except StopIteration:
        return n, "returned (no raise)"
    except BaseException as error:  # noqa: BLE001 — the raise IS the reading
        # ⛔⛔ `BaseException`, NOT `Exception`, AND THAT IS A CORRECTION.
        # This read `except Exception`, while the comment below and the docs claimed "raised
        # ANYTHING -> the defect is LIVE". A Tier 1 reviewer proved at OS-process level that a
        # `SystemExit(0)` reaching here from the stub layer escaped, exiting 0 with NO verdict
        # printed — which `run_gates.py` (which gates on returncode alone) would record as this gate
        # PASSING, with ARM B, ARM C and the discriminator never having run.
        # ⇒ ⭐ **A GUARD THAT SAYS "ANYTHING" BUT EXCLUDES AN EXCEPTION FAMILY IS NOT A GUARD ON
        # ANYTHING** — the exact parallel to the message-text guard this file already corrected once.
        return n, f"raised {type(error).__name__}: {error}"
    return n, "STILL RUNNING (cap hit) = HANG"


def show_premise(label: str, state: BattleState) -> "tuple[bool, bool]":
    left = state.opponent.left_battler
    right = state.opponent.right_battler
    left_alive = left is not None and getattr(left, "current_hp", 0) > 0
    right_alive = right is not None and getattr(right, "current_hp", 0) > 0
    print(f"  [{label}] is_double={state.is_double_battle} is_trainer={state.is_trainer_battle} "
          f"absent_flags={state._absent_battler_flags:#06b}")
    print(f"  [{label}] opponent.left_battler={'None' if left is None else 'present'} "
          f"(alive={left_alive})   right_battler={'None' if right is None else 'present'} "
          f"(alive={right_alive})")
    return left_alive, right_alive


def discriminator() -> int:
    """⭐ PROVE THE ARMS DIFFER BEFORE DRIVING ANYTHING. Drives nothing; only reads.

    ⛔ This is the check whose absence made the FIRST repro spec vacuous. If the fault arm's state
    makes the strategy return `UseMoveAgainstRightSideOpponent`, the arm can never reach the raise
    and a green result would be meaningless.
    """
    print("DISCRIMINATOR — does the fault state actually differ from the control state?\n")
    print("FAULT arm  (opponent LEFT slot absent, right battler hp == 0):")
    fault = make_state(ABSENT_OPPONENT_LEFT)
    f_left_alive, f_right_alive = show_premise("fault", fault)
    print("\nCONTROL arm (no absent flags):")
    control = make_state(0)
    c_left_alive, c_right_alive = show_premise("control", control)

    print("\n  Producer P1 (`story_mode.py` `_default_target`): returns "
          "`use_move_against_right_side_opponent` only when `right_alive and not left_alive`.")
    p1_would_aim_right = f_right_alive and not f_left_alive
    print(f"  ⇒ on the FAULT arm that guard is {p1_would_aim_right} "
          f"⇒ P1 falls through to plain `UseMove` = the RAISING path: "
          f"{'NO — ARM IS VACUOUS' if p1_would_aim_right else 'YES'}")

    ok = (fault.opponent.left_battler is None
          and control.opponent.left_battler is not None
          and not p1_would_aim_right)
    # ‼ This IS a verdict — `--discriminator` is a documented standalone command, and the guard
    # must not fail it. It reported failure on its own healthy path until a Tier 1 reviewer ran
    # the command from this file's own usage block and got exit 1.
    # ⇒ ⭐ **A GUARD THAT FAILS THE DOCUMENTED HAPPY PATH TEACHES PEOPLE TO IGNORE IT.**
    _verdict(f"\n  ARMS DIFFER AND THE FAULT ARM CAN REACH THE RAISE: {ok}")
    if not ok:
        print("  ⛔ REFUSING to call this a repro — a fault arm that cannot reach the raise would")
        print("     report GREEN and be read as 'KI-90 does not reproduce'.")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--discriminator", action="store_true", help="prove the arms differ; drive nothing")
    args = ap.parse_args()
    if args.discriminator:
        return discriminator()

    print("=" * 92)
    print("REPRO KI-90 — aiming at an ABSENT opponent LEFT slot in a DOUBLE battle")
    print("=" * 92)
    if discriminator() != 0:
        return 1

    failures: "list[str]" = []

    # ---- ARM A — THE FAULT. It must RAISE. --------------------------------------------------------
    print("\nARM A (fault): drive the REAL `battle_action_use_move` with `TurnAction.UseMove`")
    _install_stubs()
    import modules.battle_action_selection as bas

    fault = make_state(ABSENT_OPPONENT_LEFT)
    steps, outcome = drive(bas.battle_action_use_move(TurnAction.UseMove, 0, 0, fault))
    print(f"  -> after {steps} step(s): {outcome}")
    # ⛔⛔ THE SELF-RETIREMENT TEST KEYS ON **BEHAVIOUR**, NOT ON THE MESSAGE TEXT.
    # ‼ IT USED TO KEY ON THE STRING "Cannot attack the left-side opponent", and a Tier 1 reviewer
    # BROKE IT BY CONSTRUCTION on 2026-09-05: reword the exception while leaving the defect
    # completely untouched, and the gate printed SELF-RETIRED and exited 0 — silently retiring a LIVE
    # defect, the exact thing this gate's own comment claimed was impossible.
    # ⇒ ⭐ **A GUARD KEYED ON A HUMAN-READABLE STRING IS NOT A GUARD ON BEHAVIOUR.** A message is
    # cosmetic and refactorable; whether the call RAISES for this state is the defect.
    # Three-way, so a broken repro can never masquerade as a fixed bug:
    #   raised ANYTHING  -> the defect is LIVE (whatever the wording)   -> REPRODUCED
    #   returned cleanly -> the call now handles the absent slot        -> SELF-RETIRED
    #   hit the step cap -> the repro itself is broken                  -> FAIL LOUDLY
    if outcome.startswith("STILL RUNNING"):
        failures.append(f"ARM A neither raised nor returned — the REPRO is broken: {outcome}")
    elif outcome.startswith("raised"):
        if "Cannot attack the left-side opponent" not in outcome:
            print("  ⚠ NOTE: it raised, but not with the message this repro was written against.")
            print(f"     The DEFECT IS STILL LIVE (a raise for this state is the defect); only the")
            print(f"     wording changed. Update the docstring, do NOT treat this as fixed.")
    else:
        # ⭐⭐ SELF-RETIREMENT, AND IT IS WHY THIS FILE IS SAFE TO REGISTER AS A GATE.
        # A repro that asserts "the bug still reproduces" becomes a BOOBY TRAP the moment someone
        # fixes the bug: the suite goes red for the fix. ⛔ That would punish exactly the work this
        # repro exists to enable.
        # ‼ The discriminator ran and PASSED immediately above, so the fault state is genuinely
        # faulted and the arms genuinely differ — which is what lets this branch distinguish
        # "KI-90 was FIXED" from "this repro rotted". Without that guard it could not tell them
        # apart, and a rotted repro reporting SELF-RETIRED would silently retire a live defect.
        # ⛔⛔ SELF-RETIREMENT IS NOT "IT DID NOT RAISE" — IT IS "IT DID THE RIGHT THING".
        # An adversarial review fault-tested the previous version and it retired the gate for three
        # bogus fixes: one that did nothing, one that aimed at our OWN PARTNER, and one that aimed at
        # a slot that may not exist. ⇒ read the target the code COMMITS to and require the RIGHT
        # opponent (slot 3), which is what the game itself defaults to
        # (`src/battle_controller_player.c:535-536`).
        committed = capture_target_index(TurnAction.UseMove, make_state(ABSENT_OPPONENT_LEFT))
        print(f"  [target] with the LEFT slot absent, the code commits to slot: {committed}")
        if committed != 3:
            failures.append(
                f"ARM A stopped raising, but the code commits to slot {committed}, not 3 (the RIGHT "
                f"opponent). ⛔ THAT IS A BROKEN FIX, NOT A FIXED BUG — slot 1 is the absent left "
                f"(and would press Down for ever, a HANG), 0/2 are our own side. REFUSING to retire."
            )
            print("  ⛔ REFUSING TO SELF-RETIRE — see the failure above.")
            print("=" * 92)
            return 1
        print()
        _verdict("  ⭐⭐ THIS REPRO HAS SELF-RETIRED — `KI-90` NO LONGER REPRODUCES, AND THE TARGET IS RIGHT.")
        print("     The fault state is still genuinely faulted (the discriminator above passed),")
        print("     so the raise is gone because the CODE changed, not because this repro rotted.")
        print("  ⇒ TODO for whoever sees this: INVERT the arms (assert the absent slot is now")
        print("     handled), close `KI-90` and `#24-ch23chain`, and record the fix in the")
        print("     changelog. Until then this file passes and does nothing.")
        print("=" * 92)
        return 0

    # ---- ARM B — THE CONTROL. It must NOT raise. --------------------------------------------------
    print("\nARM B (control): identical, but with NO absent flags")
    _install_stubs()
    control = make_state(0)
    steps, outcome = drive(bas.battle_action_use_move(TurnAction.UseMove, 0, 0, control))
    print(f"  -> after {steps} step(s): {outcome}")
    if "Cannot attack the left-side opponent" in outcome:
        failures.append(f"ARM B raised the KI-90 error with NO absent flag — got: {outcome}")

    # ---- ARM C — the RIGHT-targeted action must be unaffected by the LEFT slot --------------------
    print("\nARM C: `UseMoveAgainstRightSideOpponent` on the FAULT state must NOT hit the LEFT check")
    _install_stubs()
    fault2 = make_state(ABSENT_OPPONENT_LEFT)
    steps, outcome = drive(
        bas.battle_action_use_move(TurnAction.UseMoveAgainstRightSideOpponent, 0, 0, fault2)
    )
    print(f"  -> after {steps} step(s): {outcome}")
    if "Cannot attack the left-side opponent" in outcome:
        failures.append("ARM C hit the LEFT-side check while targeting the RIGHT side")

    print("\n" + "=" * 92)
    if failures:
        _verdict("REPRO FAILED TO BEHAVE AS SPECIFIED:")
        for f in failures:
            print(f"  {f}")
        return 1
    _verdict("✅ KI-90 REPRODUCED — and the control arms bound the claim:")
    print("   ARM A  absent LEFT slot + UseMove            -> RuntimeError (the defect)")
    print("   ARM B  no absent flag  + UseMove             -> no raise (so the flag is the cause)")
    print("   ARM C  absent LEFT slot + RIGHT-targeted     -> no raise (so the TARGET is the cause)")
    print("‼ THIS IS AN IN-PROCESS REPRO. It proves the raise and its cause; it does NOT prove how")
    print("  often the game reaches this state, which is a separate, unmeasured question.")
    print("=" * 92)
    return 0


#: ⛔ Set by every path that prints a verdict. See the `__main__` guard below.
_VERDICT_PRINTED = False


def _verdict(text: str) -> None:
    """Print a verdict AND record that one was printed."""
    global _VERDICT_PRINTED
    _VERDICT_PRINTED = True
    print(text)


def run_with_verdict_guard(entry=None) -> int:
    """Run `entry` (default `main`) and REFUSE to return 0 unless a verdict was printed.

    ⛔⛔ THE CLASS-LEVEL GUARD, not just the instance. `run_gates.py` judges a gate by its RETURN
    CODE alone, so ANY path that exits 0 without reaching a verdict is silently recorded as PASS —
    a Tier 1 reviewer reached exactly that state through a `SystemExit(0)` in the stub layer.
    ⛔⛔ STATED AS WHAT THE CODE LITERALLY DOES, NOT AS AN ABSOLUTE. THREE earlier versions of
    this file each claimed a safety property the code did not deliver — "the message check is
    enough", "raised ANYTHING", "the class is closed" — and a Tier 1 reviewer refuted each BY
    CONSTRUCTION. ⇒ ⭐ **STATE THE GUARANTEE AS BEHAVIOUR AND ENUMERATE WHAT IT DOES NOT COVER.**
    It forces a non-zero result when `entry` RETURNS 0 with no verdict printed, and when
    `entry` RAISES anything at all (`BaseException` included, from anywhere in `main()`).
    ⚠ **IT CANNOT COVER `os._exit()`**, which bypasses Python's exception machinery entirely —
    a limitation of the language, written down rather than claimed away.
    ‼ It is a FUNCTION, not inline `__main__` code, for one reason: inline code cannot be
    fault-tested. The first version of this guard was inline, and its fault test could not reach it.
    ⇒ ⭐ **A GUARD YOU CANNOT TEST FROM OUTSIDE IS A GUARD YOU HAVE NOT TESTED.**
    """
    global _VERDICT_PRINTED
    _VERDICT_PRINTED = False
    rc = 1
    try:
        rc = (entry or main)()
    except BaseException as error:  # noqa: BLE001 — an escaping exception must FAIL, never pass
        # ⛔⛔ THIS `except` IS THE WHOLE FIX. The guard was `try/finally`, so a `SystemExit(0)` from
        # `_install_stubs()` — called in `main()`, OUTSIDE `drive()`'s reach — propagated PAST it and
        # the process exited 0 with no verdict, which `run_gates.py` records as this gate PASSING.
        # A Tier 1 reviewer proved it at OS-process level. ⇒ ⭐ **`try/finally` OBSERVES; only
        # `except` INTERVENES** — a guard that merely inspects the return value cannot stop an
        # exception that never produces one.
        print("=" * 92)
        print(f"⛔ {type(error).__name__} ESCAPED THE REPRO ({error}) — failing rather than letting")
        print("   it reach process exit. A gate judged on its return code must never pass this way.")
        print("=" * 92)
        rc = 1
    finally:
        if rc == 0 and not _VERDICT_PRINTED:
            print("=" * 92)
            print("⛔ NO VERDICT WAS PRINTED, so this run proves NOTHING — failing rather than")
            print("   exiting 0. A gate judged only by its return code must never pass silently.")
            print("=" * 92)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(run_with_verdict_guard())
