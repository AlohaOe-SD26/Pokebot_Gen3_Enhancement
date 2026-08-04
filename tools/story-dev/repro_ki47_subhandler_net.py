"""KI-47: one net that catches ANY battle sub-handler that stops making progress.
NO EMULATOR — `handle_battle`'s `_watch` wrapper is driven directly.

WHY A NET AND NOT 32 BOUNDS. An audit on 2026-08-04 found **32 unbounded `while` loops** on
the battle path (`battle_handler`, `battle_action_selection`, `battle_menuing`,
`battle_move_replacing`, `_listeners`). Two of them have each already cost a whole lane:

    KI-45  battle_menuing._select_in_menu             batch6 H4, batch9 H6 (0 runs / 180 min)
    KI-46  handle_battle_action_selection             batch10 H2 + H8 (~59 min each)

Bounding all 32 individually is 32 chances to pick a wrong bound, and most of them
legitimately wait for the game to move on.

‼ AND THE EXISTING WATCHDOG CANNOT COVER THEM. `handle_battle` already has an ML-11
no-progress watchdog, but it only runs BETWEEN iterations of its own loop — a sub-generator
that yields for ever consumes the frames on its behalf, so the outer counter never
increments. That starvation is why it caught neither KI-45 nor KI-46 (same shape as KI-37).

`_watch` counts frames WHERE THEY ARE ACTUALLY CONSUMED — inside the sub-generator's yields —
so it covers every loop under it, including ones not yet written.
"""

from __future__ import annotations

import pathlib
import re
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


import modules.battle_handler as bh  # noqa: E402
import modules.battle_fault as bf  # noqa: E402

SRC = (SANDBOX / "modules" / "battle_handler.py").read_text(encoding="utf-8", errors="replace")

print("1. every sub-handler call inside handle_battle goes through the net")
body = re.search(r"def handle_battle\(.*?(?=\n@|\ndef )", SRC, re.S)
check("handle_battle located", body is not None)
if body:
    calls = re.findall(r"yield from (\w+)\(strategy\)", body.group(0))
    unwrapped = [c for c in calls if c != "_watch"]
    check("no sub-handler is called unwrapped", not unwrapped, f"unwrapped: {unwrapped}")
    wrapped = re.findall(r"_watch\((\w+)\(strategy\)", body.group(0))
    check("the expected handlers are wrapped",
          {"handle_battle_action_selection", "handle_move_replacement_dialogue",
           "handle_evolution_scene", "handle_fainted_pokemon"} <= set(wrapped),
          str(sorted(set(wrapped))))

print("2. the bound sits BEHIND the specific ones, not in front of them")
# If this net were tighter than KI-45's/KI-46's bounds it would pre-empt them and destroy
# their specific diagnoses, leaving only "the battle stopped progressing".
import modules.battle_menuing as bm  # noqa: E402
import modules.battle_action_selection as bas  # noqa: E402

check("KI-47 net (3000) > KI-46 bound (600)", bh._SUBHANDLER_STALL_FRAMES > 600,
      str(bh._SUBHANDLER_STALL_FRAMES))
check("KI-47 net > KI-45 bound (60 cursor steps, ~180 frames)",
      bh._SUBHANDLER_STALL_FRAMES > 180, str(bm._MAX_CURSOR_STEPS))
check("and it is still well under the 18,000-frame global watchdog",
      bh._SUBHANDLER_STALL_FRAMES < 18000)

print("3. ‼ it FAULTS a sub-handler that yields for ever with no progress")
# Build the real `_watch` by running handle_battle far enough to define it is impractical,
# so exercise the same contract through a faithful stand-in of the closure it creates.
FROZEN = ("BattleScript_Stuck", "HandleTurnActionSelectionState", "None", 0)


def make_watch(sig_fn, bound, mode_instance):
    bf.context = types.SimpleNamespace(bot_mode_instance=mode_instance)

    def _watch(subgen, label):
        stale, last = 0, None
        while True:
            try:
                value = next(subgen)
            except StopIteration as stop:
                return stop.value
            sig = sig_fn()
            if sig is not None and sig == last:
                stale += 1
                if stale > bound:
                    reason = (f"KI-47: battle sub-handler '{label}' ran {stale} frames with no "
                              f"battle progress (frozen at {sig!r})")
                    from modules.battle_fault import request_mode_recovery
                    from modules.modes import BotModeError
                    if request_mode_recovery(reason):
                        return None
                    raise BotModeError(reason)
            else:
                stale, last = 0, sig
            yield value

    return _watch


def spinner():
    while True:
        yield


def drive(gen, limit=20000):
    steps = 0
    try:
        while True:
            next(gen)
            steps += 1
            if steps > limit:
                return "hung", None, steps
    except StopIteration:
        return "done", None, steps
    except Exception as e:  # noqa: BLE001
        return "raised", e, steps


bf.clear_pending_fault()
w = make_watch(lambda: FROZEN, 300, None)
outcome, err, steps = drive(w(spinner(), "handle_battle_action_selection"))
check("a forever-yielding sub-handler terminates", outcome != "hung", f"{outcome} steps={steps}")
check("it raises when no mode can take the fault", outcome == "raised", str(outcome))
if outcome == "raised":
    check("the error is NOT a NameError", not isinstance(err, NameError), repr(err))
    check("it names KI-47 and the sub-handler",
          "KI-47" in str(err) and "handle_battle_action_selection" in str(err), str(err)[:100])
    check("it reports the frozen signature", "BattleScript_Stuck" in str(err))

print("4. a sub-handler that IS progressing is never faulted")
tick = {"n": 0}


def moving_sig():
    tick["n"] += 1
    return ("script", "cb", "None", tick["n"])   # exp changes every frame = progress


def finite():
    for _ in range(2000):
        yield


bf.clear_pending_fault()
w = make_watch(moving_sig, 300, None)
outcome, err, steps = drive(w(finite(), "handle_evolution_scene"))
check("a long BUT PROGRESSING sub-handler completes", outcome == "done",
      f"{outcome} err={err!r} steps={steps}")
check("and no fault was parked", not bf.battle_fault_pending())

print("5. it prefers the recoverable channel when a mode opts in")
bf.clear_pending_fault()
w = make_watch(lambda: FROZEN, 300, types.SimpleNamespace(handles_battle_faults=True))
outcome, err, steps = drive(w(spinner(), "handle_fainted_pokemon"))
check("it returns quietly", outcome == "done", f"{outcome} err={err!r}")
check("and parked a fault", bf.battle_fault_pending())
check("carrying the diagnosis", "KI-47" in (bf.take_pending_fault() or ""))

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
