"""The PARTY ORDER hand (boss preparation BP-1, 2026-11-09): put one Pokemon, by its PID, FIRST in the party, as a person
does through the field menus: START -> POKéMON -> that Pokemon -> SWITCH -> the first slot -> A, then out again.

WHY (the BP-1 spec section 3.1): a Pokemon being RAISED must lead, so the wild battles of its raise are its own (the
game sends out the first healthy Pokemon of the party). Before BP-1 the AI never reordered its party: the field's party
menu was never opened.

HOW, each press gated on the look right before it (`hands/menus.py` choose / move_cursor): the START menu's "POKéMON"
(`eyes/screens.py` START_MENU_ACTIONS); the party list (`party`, its cursor `gPartyMenu.slotId`; while two Pokemon are
being switched the cursor that moves is `slotId2`, `src/party_menu.c` GetCurrentPartySlotPtr: the eyes read it then,
`host/eyes.py`); the action list (`party_action`: SUMMARY, SWITCH, CANCEL, ...); the first slot; then B out of the party
menu (the field's party menu returns to the START menu, `CB2_ReturnToFieldWithOpenMenu`) and B out of the START menu.

SUCCESS is read from the GAME's party as the eyes show it: the first slot's PID is `pid`, and the party's PIDs are the
same multiset as before (CLAUDE.md rule 3: identity, never a slot or a count). Every wait is bounded; a failure says why
and leaves the screen free when it can.
"""

from __future__ import annotations

from collections.abc import Generator

from ai_player.eyes.observation import Observation
from ai_player.hands.dialogue import busy_reason, player_free
from ai_player.hands.menus import choose, move_cursor, wait_for_ui
from ai_player.hands.pad import Hands

__all__ = ["CLOSE_BUDGET", "SWAP_BUDGET", "lead_with"]

#: frames for the swap's animation to end (the two slots slide out and in: `Task_SlideSelectedSlotsOffscreen`)
SWAP_BUDGET = 600
#: frames, and B presses, to close the party menu and the START menu
CLOSE_BUDGET = 900
CLOSE_PRESSES = 6
POKEMON_OPTION = "POKéMON"


def _free(look: Observation) -> bool:
    return player_free(look) and not look.screen.fading and look.view is not None


def _pids(look: Observation) -> list[int]:
    return [m.pid for m in look.party or ()]


def _close(hands: Hands, why: str) -> Generator[None, None, bool]:
    """B on the party menu or the START menu while one TAKES INPUT, until the field is free over two looks."""
    presses = 0
    start = hands.pad.frames
    while hands.pad.frames - start < CLOSE_BUDGET:
        look = hands.look()
        if _free(look):
            yield from hands.pad.idle(hands.pad.think_frames(), f"{why}: the menus are closed")
            if _free(hands.look()):
                return True
            continue
        ui = look.screen.ui
        if ui is not None and ui.kind in ("party", "start_menu", "party_action") and ui.accepts_input:
            if presses >= CLOSE_PRESSES:
                break
            yield from hands.pad.press("B", why, f"{ui.kind} takes input: B closes it")
            presses += 1
            continue
        yield from hands.pad.busy(busy_reason(look))
    hands.tell(f"{why}: the menus did not close ({presses} B presses)")
    return False


def lead_with(hands: Hands, pid: int, why: str) -> Generator[None, None, bool]:
    """Put the party member `pid` first (module docstring). True when the game's first slot holds it and the party's
    PIDs are unchanged as a multiset; no press at all when it already leads."""
    look = hands.look()
    before = _pids(look)
    if before and before[0] == pid:
        return True
    if pid not in before:
        hands.tell(f"{why}: no Pokemon {pid:08x} in the party ({[f'{p:08x}' for p in before]})")
        return False
    if not _free(look):
        hands.tell(f"{why}: the player is not free ({busy_reason(look)}): no START menu now")
        return False
    index = before.index(pid)
    name = look.party[index].species
    yield from hands.pad.press("Start", why, "the player is free on the overworld: START opens the menu")
    if not (yield from choose(hands, "start_menu", POKEMON_OPTION, f"{why}: the party")):
        yield from _close(hands, why)
        return False
    if (yield from wait_for_ui(hands, "party", why)) is None:
        yield from _close(hands, why)
        return False
    if not (yield from move_cursor(hands, "party", index, f"{why}: {name}")):
        yield from _close(hands, why)
        return False
    gate = hands.look()  # THE GATE: the cursor on the member, the list taking input, on the look right before the press
    ui = gate.screen.ui
    if ui is None or ui.kind != "party" or ui.cursor != index or not ui.accepts_input:
        hands.tell(f"{why}: the party cursor is not on {name} before the press")
        yield from _close(hands, why)
        return False
    yield from hands.pad.press("A", why, f"party cursor on {index} ({name})")
    if not (yield from choose(hands, "party_action", "SWITCH", f"{why}: SWITCH {name}")):
        yield from _close(hands, why)
        return False
    # the switch's second choice: the list takes input again, its moving cursor on the member (`slotId2`)
    if (yield from wait_for_ui(hands, "party", why)) is None or not (yield from move_cursor(hands, "party", 0,
                                                                                            f"{why}: to the first slot")):
        yield from _close(hands, why)
        return False
    gate = hands.look()
    ui = gate.screen.ui
    if ui is None or ui.kind != "party" or ui.cursor != 0 or not ui.accepts_input:
        hands.tell(f"{why}: the party cursor is not on the first slot before the press")
        yield from _close(hands, why)
        return False
    yield from hands.pad.press("A", why, f"party cursor on 0: {name} goes first")
    swapped = None
    start = hands.pad.frames
    while hands.pad.frames - start < SWAP_BUDGET:
        look = hands.look()
        pids = _pids(look)
        ui = look.screen.ui
        if pids and pids[0] == pid and ui is not None and ui.kind == "party" and ui.accepts_input:
            swapped = pids
            break
        yield from hands.pad.busy(f"{why}: the two Pokemon change places")
    closed = yield from _close(hands, why)
    after = _pids(hands.look())
    ok = swapped is not None and closed and after and after[0] == pid and sorted(after) == sorted(before)
    hands.tell(f"{why}: {name} ({pid:08x}) {'leads now' if ok else 'is NOT first'}; the party's PIDs "
               f"{'unchanged' if sorted(after) == sorted(before) else 'CHANGED'} "
               f"({[f'{p:08x}' for p in before]} -> {[f'{p:08x}' for p in after]})")
    return bool(ok)
