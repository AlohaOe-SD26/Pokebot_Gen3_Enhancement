"""KI-38: the party-menu cursor must never spin, must self-correct, and must report evidence.
NO EMULATOR — the real generator is driven against fake cursor memory.

WHY THIS IS THE PROJECT'S BIGGEST BATTLE DRAG. Batch11 (`x4-runs/20260804-062303`): the KI-47
net fired 8 times and **7 of them were this site** — `handle_fainted_pokemon` frozen at
`BattleScript_FaintedMonTryChoose`, i.e. ~7 recoverable derails per 180-minute batch.

‼ KI-38 WAS RECORDED AS "FIXED 2026-07-31" because hangs went 11/12 → 1/8. That measured how
often a wedge KILLED A RUN, not how often it HAPPENED. It never stopped happening — the same
error as `d7d493d8` being called live-validated on "no unrecovered errors" while finishing 0%
of runs.

‼ THE MODEL IS WRONG, WHICH IS WHY NO RETRY LIMIT EVER FIXED IT. `gPartyMenu[9]` is not a
plain party index: KI-38 recorded `cursors_seen=[0,2,3,7]` in a FOUR-mon party, so it also
takes values that are not Pokémon slots (7 is CANCEL). `cursor < target -> Down` then walks
the wrong way, or the value does not respond at all, and the stock `while True` spins for ever
(`presses={'Down': 3, 'A': 273}`).

This change does not pretend to fix the model — `#24-menutext` still is the fix. It bounds the
loop, self-corrects the commonest failure, and REPORTS `cursors_seen`, which is the evidence
`#24-menutext` needs and which every previous report of this bug lacked.
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


import modules.menuing as mn  # noqa: E402
import modules.battle_fault as bf  # noqa: E402
from modules.memory import GameState  # noqa: E402

PRESSES: list[str] = []


def install(cursor_fn, party_size=4, mode_instance=None):
    mn.get_party_size = lambda: party_size
    mn.get_current_party_menu_index = cursor_fn
    mn.get_game_state = lambda: GameState.PARTY_MENU
    mn.read_symbol = lambda *a, **k: b"\x00\x00"
    mn.unpack_uint16 = lambda b: 0
    mn.context = types.SimpleNamespace(
        emulator=types.SimpleNamespace(press_button=lambda b: PRESSES.append(b)),
        bot_mode_instance=mode_instance)
    bf.context = mn.context
    bf.clear_pending_fault()
    PRESSES.clear()


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


print("1. ‼ THE REAL CASE — cursor stuck on the CANCEL sentinel (7 in a 4-mon party)")
install(lambda: 7)
outcome, err, steps = drive(mn.scroll_to_party_menu_index(2))
check("it terminates (the stock `while True` spins here)", outcome != "hung",
      f"outcome={outcome} steps={steps}")
check("it raises rather than returning as if it succeeded", outcome == "raised", str(outcome))
if outcome == "raised":
    check("the error is NOT a NameError", not isinstance(err, NameError), repr(err))
    msg = str(err)
    check("it names KI-38", "KI-38" in msg)
    check("‼ it reports cursors_seen (the evidence #24-menutext needs)",
          "cursors seen: [7]" in msg, msg[:150])
    check("it reports the party size", "party size 4" in msg)
    check("it points at the real fix", "#24-menutext" in msg)

print("2. it does not hammer one key — it REVERSES when the cursor stops responding")
downs, ups = PRESSES.count("Down"), PRESSES.count("Up")
check("both directions were tried", downs > 0 and ups > 0, f"Down={downs} Up={ups}")
check("and it gave up in tens of presses, not hundreds", len(PRESSES) <= 45,
      f"{len(PRESSES)} presses (stock logged 'A': 273)")

print("3. a NORMAL scroll still works and is not slowed down")
state = {"c": 0}


def moving():
    return state["c"]


install(moving)
mn.context.emulator.press_button = lambda b: (PRESSES.append(b),
                                              state.__setitem__("c", state["c"] + (1 if b == "Down" else -1)))
outcome, err, steps = drive(mn.scroll_to_party_menu_index(2))
check("a reachable target completes", outcome == "done", f"{outcome} err={err!r}")
check("in exactly the needed presses", PRESSES.count("Down") == 2 and PRESSES.count("Up") == 0,
      str(PRESSES))

print("4. already-on-target returns immediately")
install(lambda: 3)
outcome, err, steps = drive(mn.scroll_to_party_menu_index(3))
check("no presses at all", outcome == "done" and not PRESSES, f"{outcome} presses={PRESSES}")

print("5. it prefers the recoverable channel when a mode opts in")
install(lambda: 7, mode_instance=types.SimpleNamespace(handles_battle_faults=True))
outcome, err, steps = drive(mn.scroll_to_party_menu_index(2))
check("it returns quietly", outcome == "done", f"{outcome} err={err!r}")
check("and parked a fault", bf.battle_fault_pending())
check("carrying cursors_seen", "cursors seen" in (bf.take_pending_fault() or ""))

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
