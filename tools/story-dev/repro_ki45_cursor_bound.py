"""KI-45: a battle-menu cursor that never arrives must RAISE, not spin forever.
NO EMULATOR — the loop is driven against fake memory and a fake emulator.

WHAT WENT WRONG, TWICE:
  batch6 lane H4  —   866 STUCK dumps, 27 minutes silent, ~half the lane's output lost
  batch9 lane H6  — 1,430 STUCK dumps, **0 runs completed in a 180-minute batch**

Both parked in `battle_menuing._select_in_menu` via `scroll_to_move`, inside a trainer battle,
`controllable=False`. Stock code is `while True:` — it presses a direction until the cursor
read equals the target. If the menu is not actually open, or the read returns anything outside
0..3, no press can change it and the movement logic still picks a direction every iteration:
`current_index=5` with `target_index=0` hits `current_index > 1 and target_index <= 1` and
presses "Up" forever.

‼ NEITHER EXISTING GUARD CAN SEE IT. The global watchdog needs an UNCHANGED progress signature
and a menu loop keeps changing map/coords/state; the per-run frame budget is KI-36's
documented hole ("cannot fire while a battle handler is on the stack").

‼ THIS TEST DRIVES THE REAL GENERATOR. An earlier repro in this project asserted on source
text and passed while the behaviour was wrong; here the loop is actually stepped, so a
regression to `while True` hangs the test rather than passing it.
"""

from __future__ import annotations

import pathlib
import sys
import types

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


import modules.battle_menuing as bm  # noqa: E402

PRESSES: list[str] = []


def _fake_read(symbol, size=4):
    """A cursor stuck OUT OF RANGE — exactly the batch6/batch9 shape."""
    return bytes([5, 0, 0, 0])


class _FakeEmu:
    def press_button(self, b):
        PRESSES.append(b)


def drive(gen, limit=100000):
    """Step the generator to completion, returning ('done'|'raised', payload, steps)."""
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


print("1. a cursor that can never arrive RAISES instead of spinning")
bm.read_symbol = _fake_read
bm.context = types.SimpleNamespace(emulator=_FakeEmu(), bot_mode_instance=None)
PRESSES.clear()
outcome, err, steps = drive(bm._select_in_menu("gMoveSelectionCursor", 0))
check("it terminates at all (stock `while True` would hang here)", outcome != "hung",
      f"outcome={outcome} steps={steps}")
check("it RAISES rather than returning quietly", outcome == "raised", f"outcome={outcome}")
if outcome == "raised":
    msg = str(err)
    check("the error names KI-45", "KI-45" in msg, msg[:70])
    check("it names the cursor symbol", "gMoveSelectionCursor" in msg)
    check("‼ it reports the LAST CURSOR VALUE (that is the diagnosis)", "last read: 5" in msg,
          msg[:110])
    check("it says the menu is probably not open", "not open" in msg)

print("2. the bound is generous but far under the watchdog")
check("it gave up in well under 18,000 frames", steps < 1000, f"{steps} yields")
check("_MAX_CURSOR_STEPS is >= 20x a real selection (<=3 presses)",
      bm._MAX_CURSOR_STEPS >= 60, str(bm._MAX_CURSOR_STEPS))

print("3. a NORMAL selection still works and is not slowed down")
state = {"i": 3}


def _moving_read(symbol, size=4):
    return bytes([state["i"], 0, 0, 0])


class _MovingEmu:
    def press_button(self, b):
        PRESSES.append(b)
        # Emulate the cursor responding to the press.
        if b == "Up" and state["i"] > 1:
            state["i"] -= 2
        elif b == "Left" and state["i"] in (1, 3):
            state["i"] -= 1


bm.read_symbol = _moving_read
bm.context = types.SimpleNamespace(emulator=_MovingEmu(), bot_mode_instance=None)
PRESSES.clear()
outcome, err, steps = drive(bm._select_in_menu("gMoveSelectionCursor", 0))
check("a reachable target completes normally", outcome == "done", f"outcome={outcome} err={err}")
check("it took only a few presses", len(PRESSES) <= 4, f"presses={PRESSES}")

print("4. it prefers the RECOVERABLE channel when a mode opts in")
# `request_mode_recovery` returns True only for a mode with handles_battle_faults=True; the
# caller must then return quietly so the mode takes ONE derail instead of dropping to Manual.
bm.read_symbol = _fake_read
mode = types.SimpleNamespace(handles_battle_faults=True)
bm.context = types.SimpleNamespace(emulator=_FakeEmu(), bot_mode_instance=mode)
import modules.battle_fault as bf  # noqa: E402

bf.context = bm.context
bf.clear_pending_fault()
outcome, err, steps = drive(bm._select_in_menu("gMoveSelectionCursor", 0))
check("it returns quietly instead of raising", outcome == "done", f"outcome={outcome} err={err}")
check("and it parked a fault for the mode to claim", bf.battle_fault_pending())
parked = bf.take_pending_fault() or ""
check("the parked reason carries the diagnosis", "KI-45" in parked and "last read: 5" in parked,
      parked[:90])

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
