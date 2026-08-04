"""KI-46: battle action selection must give up on an unrecognised state, not spin for ever.
NO EMULATOR — the real generator is driven against fake battle-state readers.

WHAT WENT WRONG (batch10, `x4-runs/20260803-164713`): lanes H2 and H8 both wedged for ~59
minutes. **H8 completed 0 runs in the whole 180-minute batch**; H2 managed 2 against 4-5
elsewhere. Both stacks stopped at `battle_action_selection.py:55` with **zero**
`_select_in_menu` dumps — so this is NOT KI-45. That fix was one instance of a pattern; this
is another one, at a different site.

The loop's exit conditions are sound (battle over, or the main callback moves on). But if the
battle stays ACTIVE in turn-action-selection while the CONTROLLER callback matches none of the
branches, control falls to a bare `else: yield; continue` and spins there indefinitely.

‼ BOTH EXISTING GUARDS ARE BLIND: the global watchdog needs an UNCHANGED progress signature
and a battle keeps changing it; the per-run frame budget is KI-36's documented "cannot fire
while a battle handler is on the stack".

‼ THIS TEST DRIVES THE REAL GENERATOR. Two repros in this project passed while the behaviour
was wrong because they asserted on source text; and the fix itself referenced `BotModeError`
without importing it, which would have raised NameError instead of the honest error. Only
executing the branch catches that.
"""

from __future__ import annotations

import pathlib
import sys
import types

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


import modules.battle_action_selection as bas  # noqa: E402
import modules.battle_fault as bf  # noqa: E402


def install(controller0="SomeUnknownCallback"):
    """Battle permanently active, in turn-action-selection, with an UNRECOGNISED controller."""
    bas.battle_is_active = lambda: True
    bas.get_main_battle_callback = lambda: "HandleTurnActionSelectionState"
    bas.get_battle_controller_callback = lambda i: controller0
    bas.get_battle_state = lambda: types.SimpleNamespace(
        is_safari_zone_encounter=False, is_double_battle=False,
        own_side=types.SimpleNamespace(left_battler=None, right_battler=None),
    )


def drive(gen, limit=50000):
    steps = 0
    try:
        while True:
            next(gen)
            steps += 1
            if steps > limit:
                return "hung", None, steps
    except StopIteration:
        return "done", None, steps
    except Exception as error:  # noqa: BLE001
        return "raised", error, steps


print("1. an unrecognised battle state terminates instead of spinning")
install()
bas.context = types.SimpleNamespace(bot_mode="Story", emulator=types.SimpleNamespace(
    press_button=lambda b: None), bot_mode_instance=None)
bf.context = bas.context
bf.clear_pending_fault()
outcome, err, steps = drive(bas.handle_battle_action_selection(strategy=None))
check("it terminates at all (the stock loop hangs here)", outcome != "hung",
      f"outcome={outcome} steps={steps}")
check("it RAISES when no mode can take the fault", outcome == "raised", f"outcome={outcome}")

print("2. ‼ it raises the HONEST error, not a NameError")
# The fix referenced BotModeError without importing it at module top. A NameError here would
# still "terminate", so check 1 alone would have passed while the diagnosis was destroyed.
if outcome == "raised":
    check("the exception is NOT a NameError", not isinstance(err, NameError), repr(err))
    msg = str(err)
    check("it names KI-46", "KI-46" in msg, msg[:70])
    check("‼ it reports the observed callbacks (that is the diagnosis)",
          "HandleTurnActionSelectionState" in msg and "SomeUnknownCallback" in msg, msg[:130])

print("3. the bound is ~10s, far under the 18,000-frame watchdog")
check("it gave up well under the watchdog window", steps < 2000, f"{steps} yields")

print("4. it prefers the RECOVERABLE channel when a mode opts in")
install()
mode = types.SimpleNamespace(handles_battle_faults=True)
bas.context = types.SimpleNamespace(bot_mode="Story", emulator=types.SimpleNamespace(
    press_button=lambda b: None), bot_mode_instance=mode)
bf.context = bas.context
bf.clear_pending_fault()
outcome, err, steps = drive(bas.handle_battle_action_selection(strategy=None))
check("it returns quietly instead of raising", outcome == "done", f"outcome={outcome} err={err!r}")
check("and it parked a fault for the mode to claim", bf.battle_fault_pending())
parked = bf.take_pending_fault() or ""
check("the parked reason carries the diagnosis", "KI-46" in parked, parked[:80])

print("5. ‼ a battle that ENDS normally is unaffected (no false positive)")
calls = {"n": 0}


def _active_then_over():
    calls["n"] += 1
    return calls["n"] < 50          # battle ends well before the bound


install()
bas.battle_is_active = _active_then_over
bas.context = types.SimpleNamespace(bot_mode="Story", emulator=types.SimpleNamespace(
    press_button=lambda b: None), bot_mode_instance=None)
bf.context = bas.context
bf.clear_pending_fault()
outcome, err, steps = drive(bas.handle_battle_action_selection(strategy=None))
check("it exits cleanly when the battle ends", outcome == "done", f"outcome={outcome} err={err!r}")
check("and parks NO fault", not bf.battle_fault_pending())

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
