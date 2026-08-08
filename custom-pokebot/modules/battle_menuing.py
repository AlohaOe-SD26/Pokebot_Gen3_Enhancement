from typing import Generator

from modules.context import context
from modules.debug import debug
from modules.memory import read_symbol


#: ‼ KI-45 — BOUND FOR THE CURSOR SCROLL. STOCK HAD `while True:` AND IT HUNG WHOLE LANES.
#:
#: Measured twice: batch6 lane H4 (866 STUCK dumps, 27 minutes silent, ~half the lane's output
#: lost) and batch9 lane H6 (1,430 dumps, **0 runs completed in a 180-minute batch**). Both
#: parked here, in a trainer battle, with `controllable=False`.
#:
#: WHY IT CANNOT SELF-CORRECT. The loop presses a direction until the cursor read equals the
#: target. If the menu is not actually open — or the read returns anything outside 0..3 — no
#: press can ever change it, and the movement logic still picks a direction every iteration:
#: a `current_index` of 5 with `target_index` 0 hits `current_index > 1 and target_index <= 1`
#: and presses "Up" forever.
#:
#: ‼ AND NEITHER EXISTING GUARD CAN SEE IT. The global watchdog needs an UNCHANGED progress
#: signature and a menu loop keeps changing map/coords/state; the per-run frame budget is
#: KI-36's documented hole ("cannot fire while a battle handler is on the stack"). This bound
#: is the only thing standing between a stuck cursor and an infinite lane.
#:
#: 60 iterations is ~180 frames (each does one press plus two yields). A real selection needs
#: at most three presses, so this is ~20x headroom and still ~1% of the 18,000-frame watchdog.
_MAX_CURSOR_STEPS = 60


def _select_in_menu(cursor_symbol: str, target_index: int, use_third_byte: bool = False) -> Generator:
    if target_index < 0 or target_index > 3:
        raise ValueError(f"Menu index must be a number between 0 and 3. '{target_index}' given.")

    first_iteration = True
    steps = 0
    last_index = None
    while True:
        if steps >= _MAX_CURSOR_STEPS:
            # ‼ RAISE, DO NOT SPIN AND DO NOT SILENTLY GIVE UP. Report through the designed
            # channel so a mode that opted in takes ONE recoverable derail instead of the
            # whole run dropping to Manual (see `modules/battle_fault`). The reason carries
            # the last cursor value BECAUSE THAT IS THE DIAGNOSIS — an out-of-range value
            # means the menu was not open, a stuck in-range value means the presses are not
            # landing. Without it, the next reader is back to guessing, which is how this
            # cost two lanes before anyone looked.
            reason = (
                f"KI-45: cursor '{cursor_symbol}' never reached index {target_index} after "
                f"{steps} steps (last read: {last_index}). The menu is probably not open."
            )
            from modules.battle_fault import request_mode_recovery
            from modules.modes import BotModeError

            if request_mode_recovery(reason):
                return
            raise BotModeError(reason)
        steps += 1
        current_index = read_symbol(cursor_symbol, size=4)

        # In double battles, for the right-side Pokémon the 3rd byte of the index is used,
        # otherwise it's the 1st byte.
        if use_third_byte:
            current_index = current_index[2]
        else:
            current_index = current_index[0]
        last_index = current_index

        if current_index == target_index:
            # If this function is called when the cursor is already pointing at the target,
            # in some edge cases we need to wait another frame until the UI becomes responsive.
            # This is _usually_ not necessary, but waiting that extra frame fixes the edge
            # case so here we go.
            if first_iteration:
                yield
            break
        else:
            if current_index in (1, 3) and target_index in (0, 2):
                context.emulator.press_button("Left")
            elif current_index in (0, 2) and target_index in (1, 3):
                context.emulator.press_button("Right")
            elif current_index > 1 and target_index <= 1:
                context.emulator.press_button("Up")
            else:
                context.emulator.press_button("Down")
        yield
        yield
        first_iteration = False


@debug.track
def scroll_to_battle_action(action_index: int) -> Generator:
    yield from _select_in_menu("gActionSelectionCursor", action_index)


@debug.track
def scroll_to_move(move_index: int, is_right_side_pokemon: bool = False) -> Generator:
    yield from _select_in_menu("gMoveSelectionCursor", move_index, is_right_side_pokemon)
