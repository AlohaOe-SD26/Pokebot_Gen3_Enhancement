"""TEST SIDE: build the TRAINER-DEFEAT-TEXT fixture for live arm E10 (step 1, the verifier's waits defect).

    py -3.12 ai_player/gates/make_defeat_text_fixture.py [--out PATH]

WHY IT EXISTS: the eyes' "waits for a button" missed the text printer's RENDER_STATE_WAIT (state 1,
`include/text.h`), the state `{PAUSE_UNTIL_PRESS}` puts a printer in (`src/text.c`: `case
EXT_CTRL_CODE_PAUSE_UNTIL_PRESS: textPrinter->state = RENDER_STATE_WAIT;`, and `case RENDER_STATE_WAIT:
if (TextPrinterWait(textPrinter))`, which waits for `JOY_NEW(A_BUTTON | B_BUTTON)`). `src/battle_message.c`
appends EXT_CTRL_CODE_PAUSE_UNTIL_PRESS to every trainer's lose and win text, so the game waits like
this after EVERY trainer v1 beats, Roxanne included. No save in `tools/story-dev/saves/` stops there, so
this script MAKES one by playing: it loads `gates/fixtures/trainer_battle_r116.ss1` (Joey's battle on
Route 116 at its first decision) in a throwaway emulator and plays the battle with ordinary button
presses only (no memory write): at the action menu it chooses FIGHT, at the move menu it moves the
cursor to Quick Attack (slot 4: the Normal move, neutral against Machop) and chooses it, and it presses
A on a text that shows its down arrow. It stops on the FIRST frame on which text printer 0 (the battle's
message window) is in state 1, and saves the state there: the trainer's defeat text, waiting.

The controller's state is read only to choose a press (`gBattlerControllerFuncs[0]`, the menu cursors);
what the fixture is, is checked after the fact and printed: printer 0's state, the battle-string buffer
decoded with the probe's own charmap up to the printer's position, and the two bytes the printer just
consumed (EXT_CTRL_CODE_BEGIN 0xFC, EXT_CTRL_CODE_PAUSE_UNTIL_PRESS 0x09). Every press is listed with its
frame. The live driver pins the output by md5; a rebuild means re-pinning after reading the printout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.probe_eyes import _symbol, _u32, boot, own_text  # noqa: E402

SOURCE = Path(__file__).resolve().parent / "fixtures" / "trainer_battle_r116.ss1"
DEFAULT_OUT = Path(__file__).resolve().parent / "fixtures" / "trainer_defeat_text_r116.ss1"
PROFILE = "ai-step0-fixture"
MAX_FRAMES = 20_000  # bounded: the battle is three or four turns
PRESS_GAP = 8  # frames between two presses, so each press is a NEW press (JOY_NEW)
STALL_FRAMES = 120  # nothing changed this long and no rule applies: press A (a level-up box waits like this)
QUICK_ATTACK_SLOT = 3  # Grovyle's moves: Fury Cutter, Pursuit, Absorb, Quick Attack (step 1 evidence E5)
PRINTER_SIZE, PRINTER_ACTIVE, PRINTER_STATE = 0x24, 0x1B, 0x1C
RENDER_STATE_WAIT = 1
DOWN_ARROW_STATES = (2, 3)  # RENDER_STATE_CLEAR, RENDER_STATE_SCROLL_START
BATTLE_TYPE_TRAINER = 1 << 3


def printer0(read_symbol) -> tuple[int, int, int]:
    raw = read_symbol("sTextPrinters", 0, PRINTER_SIZE)
    return _u32(raw, 0), raw[PRINTER_ACTIVE], raw[PRINTER_STATE]


def build(out: Path) -> dict:
    context = boot(PROFILE)
    from modules.memory import GameState, get_game_state, read_symbol

    source = SOURCE.read_bytes()
    emulator = context.emulator
    emulator.load_save_state(source)
    presses: list[list] = []
    last_press = -PRESS_GAP
    last_change = 0
    previous = None
    found_at = None
    for step in range(MAX_FRAMES):
        char, active, state = printer0(read_symbol)
        controller = _symbol(_u32(read_symbol("gBattlerControllerFuncs", 0, 4), 0) - 1) or "?"
        if get_game_state() != GameState.BATTLE:
            raise SystemExit(f"the battle ended before a defeat text was seen (step {step}, state {get_game_state().name})")
        if active and state == RENDER_STATE_WAIT:
            found_at = emulator.get_frame_count()
            break
        now = (char, active, state, controller)
        if now != previous:
            previous, last_change = now, step
        button = None
        if step - last_press >= PRESS_GAP:
            if controller == "HandleInputChooseAction":
                cursor = read_symbol("gActionSelectionCursor", 0, 1)[0]
                button = "A" if cursor == 0 else ("Up" if cursor & 2 else "Left")
            elif controller == "HandleInputChooseMove":
                cursor = read_symbol("gMoveSelectionCursor", 0, 1)[0]
                if cursor == QUICK_ATTACK_SLOT:
                    button = "A"
                elif not cursor & 1:
                    button = "Right"
                else:
                    button = "Down"
            elif active and state in DOWN_ARROW_STATES:
                button = "A"
            elif step - last_change >= STALL_FRAMES:
                button = "A"
        if button is not None:
            emulator.press_button(button)
            presses.append([emulator.get_frame_count(), button, controller, state if active else None])
            last_press = step
        emulator.run_single_frame()
    if found_at is None:
        raise SystemExit(f"no text printer 0 in state 1 within {MAX_FRAMES} frames")
    data = emulator.get_save_state()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    char, active, state = printer0(read_symbol)
    from modules.game import get_symbol

    buffer_start = get_symbol("gDisplayedStringBattle")[0]
    shown = emulator.read_bytes(buffer_start, max(0, min(char - buffer_start, 0x12C)))
    flags = _u32(read_symbol("gBattleTypeFlags", size=4), 0)
    result = {
        "source": str(SOURCE.relative_to(REPO)),
        "source_md5": hashlib.md5(source).hexdigest(),
        "presses": presses,
        "found_at_frame": found_at,
        "out": str(out.relative_to(REPO)) if out.is_relative_to(REPO) else str(out),
        "out_md5": hashlib.md5(data).hexdigest(),
        "game_state": get_game_state().name,
        "battle_type_flags": flags,
        "trainer_battle": bool(flags & BATTLE_TYPE_TRAINER),
        "opponent": int.from_bytes(read_symbol("gTrainerBattleOpponent_A", size=2), "little"),
        "printer0": {"active": active, "state": state, "current_char": char,
                     "in_buffer": _symbol(char), "two_bytes_before": bytes(emulator.read_bytes(char - 2, 2)).hex()},
        "text_up_to_the_printer (probe charmap)": own_text(shown.replace(b"\xff", b"")),
        "battle_outcome": read_symbol("gBattleOutcome", size=1)[0],
    }
    # After the save (the fixture is already written): is it really waiting? 120 frames with no input.
    for _ in range(120):
        emulator.run_single_frame()
    result["after_120_idle_frames"] = dict(zip(("current_char", "active", "state"), printer0(read_symbol)))
    return result


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = build(args.out)
    print("FIXTURE " + json.dumps(result), flush=True)
    ok = result["trainer_battle"] and result["printer0"]["state"] == RENDER_STATE_WAIT
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
