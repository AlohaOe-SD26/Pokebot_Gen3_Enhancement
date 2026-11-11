"""The FIELD ITEM hand (boss preparation round 2, USER RULING 59, 2026-11-11): use a healing item from the BAG on one
Pokemon, by its PID, as a person does on the overworld: START -> BAG -> the ITEMS pocket -> the item -> USE -> that
Pokemon -> A, the message read, and again while it is still low; then out of the bag and the START menu.

WHY (spec `ai-research-notes/2026-11-09-BOSS-PREP-BP1-RAISE-SPEC.md` section 2.4): a person raising a weak Pokemon heals it
with a Potion when the POKéMON CENTER is far and the bag has one. Before round 2 the AI used an item only in a battle
(`skills/battle.py`); it never opened the bag on the field.

HOW, each press gated on the look right before it (`hands/menus.py` choose / move_cursor, as `hands/party_order.py`):
the START menu's "BAG" (`eyes/screens.py` START_MENU_ACTIONS); the bag (`bag`, its pocket `MenuView.pocket` from
`gBagPosition.pocket`, `BAG_POCKETS`): Left / Right until the pocket is "items" (`src/item_menu.c` SwitchBagPocket), at
most `POCKET_PRESSES`; the item's row by its NAME (the list as shown, `MenuView.options`); A opens its action list
(`bag_action`, `BAG_MENU_ACTIONS`); USE (`src/item_use.c` ItemUseOutOfBattle_Medicine opens the party menu "Use on which
POKéMON?", `PARTY_ACTION_USE_ITEM`); the member's row by its PID in the eyes' party; A; the message ("... HP was restored by
N points") read with A until the bag takes input again (`CB2_ReturnToBagMenu`). Repeated while the member is under `up_to`
of its max HP, fewer than `most` items are used and the item is left. Then B out of the bag and the START menu.

SUCCESS is read from the GAME as the eyes show it, all three: the member's HP ROSE (by its PID), the item's count FELL by
the number used, and the party's PIDs are the same multiset (CLAUDE.md rule 3: identity, never a slot or a count). Every
wait is bounded; a failure says why and leaves the screen free when it can.
"""

from __future__ import annotations

from collections.abc import Generator

from ai_player.eyes.observation import Observation
from ai_player.hands.dialogue import busy_reason, player_free
from ai_player.hands.menus import choose, item_key, move_cursor, wait_for_ui
from ai_player.hands.pad import Hands

__all__ = ["CLOSE_BUDGET", "MESSAGE_BUDGET", "POCKET_PRESSES", "use_on"]

#: Left / Right presses to reach the ITEMS pocket (five pockets: at most four steps, one spare)
POCKET_PRESSES = 5
#: frames for the item's message to be read and the bag to take input again
MESSAGE_BUDGET = 1500
#: frames, and B presses, to close the bag and the START menu
CLOSE_BUDGET = 1200
CLOSE_PRESSES = 8
BAG_OPTION = "BAG"
ITEMS_POCKET = "items"
USE_OPTION = "USE"


def _free(look: Observation) -> bool:
    return player_free(look) and not look.screen.fading and look.view is not None


def _pids(look: Observation) -> list[int]:
    return [m.pid for m in look.party or ()]


def _hp(look: Observation, pid: int) -> tuple[int, int] | None:
    mon = next((m for m in look.party or () if m.pid == pid), None)
    return (mon.hp, mon.max_hp) if mon is not None else None


def _count(look: Observation, name: str) -> int:
    if look.bag is None:
        return 0
    return sum(quantity for item, quantity in look.bag.healing if item_key(item) == item_key(name))


def _close(hands: Hands, why: str) -> Generator[None, None, bool]:
    """B on the bag or the START menu while one TAKES INPUT, until the field is free over two looks."""
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
        if ui is not None and ui.kind in ("bag", "start_menu", "bag_action", "party") and ui.accepts_input:
            if presses >= CLOSE_PRESSES:
                break
            yield from hands.pad.press("B", why, f"{ui.kind} takes input: B closes it")
            presses += 1
            continue
        if look.screen.waits_for_button and ui is None:
            yield from hands.pad.press("B", why, look.screen.wait_reason or "a text waits")
            presses += 1
            continue
        yield from hands.pad.busy(busy_reason(look))
    hands.tell(f"{why}: the menus did not close ({presses} B presses)")
    return False


def _to_pocket(hands: Hands, why: str) -> Generator[None, None, Observation | None]:
    """The bag on the ITEMS pocket, taking input: Left / Right read pocket by pocket. Returns that look, or None."""
    for _ in range(POCKET_PRESSES + 1):
        look = yield from wait_for_ui(hands, "bag", why)
        if look is None:
            return None
        ui = look.screen.ui
        if ui.pocket == ITEMS_POCKET:
            return look
        yield from hands.pad.press("Left", why, f"bag on the {ui.pocket} pocket, wanted {ITEMS_POCKET}: one pocket left")
    hands.tell(f"{why}: the bag did not show the {ITEMS_POCKET} pocket in {POCKET_PRESSES} presses")
    return None


def _read_message(hands: Hands, why: str) -> Generator[None, None, bool]:
    """After the item is used on the member: its message read (A on each page that WAITS, on the look right before the
    press) until the bag takes input again. False when it did not come back within `MESSAGE_BUDGET` frames."""
    start = hands.pad.frames
    while hands.pad.frames - start < MESSAGE_BUDGET:
        look = hands.look()
        ui = look.screen.ui
        if ui is not None and ui.kind == "bag" and ui.accepts_input:
            return True
        if look.screen.waits_for_button:
            yield from hands.pad.idle(hands.pad.reading_frames(len(look.screen.text or "")), f"{why}: reading the message")
            gate = hands.look()  # THE GATE: the page still waits, on the look right before the press
            if gate.screen.waits_for_button:
                yield from hands.pad.press("A", why, gate.screen.wait_reason or "a text waits")
            continue
        yield from hands.pad.busy(busy_reason(look))
    hands.tell(f"{why}: the bag did not come back after the item's message")
    return False


def use_on(hands: Hands, pid: int, items, up_to: float, most: int, why: str) -> Generator[None, None, tuple[bool, int, str]]:
    """Use field healing `items` (names, in the order to try) on the party member `pid` (module docstring) until it is at
    `up_to` of its max HP or `most` items are used. Returns (ok, items used, what happened); no press at all when the bag
    holds none of `items`, the member is not in the party, or the player is not free."""
    look = hands.look()
    before_pids = _pids(look)
    if pid not in before_pids:
        return False, 0, f"no Pokemon {pid:08x} in the party"
    held = [name for name in items if _count(look, name) > 0]
    if not held:
        return False, 0, f"the bag holds none of {list(items)}"
    if not _free(look):
        return False, 0, f"the player is not free ({busy_reason(look)}): no START menu now"
    hp_before = _hp(look, pid)
    counts_before = {name: _count(look, name) for name in items}
    member = next(m for m in look.party if m.pid == pid)
    used = 0
    said = "the item could not be used"
    yield from hands.pad.press("Start", why, "the player is free on the overworld: START opens the menu")
    if not (yield from choose(hands, "start_menu", BAG_OPTION, f"{why}: the bag")):
        yield from _close(hands, why)
        return False, 0, "BAG could not be chosen"
    while used < most:
        look = yield from _to_pocket(hands, why)
        if look is None:
            said = "the ITEMS pocket could not be shown"
            break
        now = _hp(look, pid)
        if now is None or now[0] >= up_to * now[1]:
            said = f"{member.species} is at {now[0] if now else '?'}/{now[1] if now else '?'}: enough"
            break
        ui = look.screen.ui
        rows = [i for wanted in items if _count(look, wanted) > 0
                for i, name in enumerate(ui.options) if item_key(name) == item_key(wanted)]
        if not rows:
            said = f"none of {list(items)} is left in the ITEMS pocket"
            break
        row = rows[0]
        name = ui.options[row]
        if not (yield from move_cursor(hands, "bag", row, f"{why}: {name}")):
            said = f"the bag's cursor did not reach {name}"
            break
        gate = hands.look()  # THE GATE: the cursor on the item, the list taking input
        ui = gate.screen.ui
        if ui is None or ui.kind != "bag" or ui.cursor != row or not ui.accepts_input:
            said = f"the bag's cursor is not on {name} before the press"
            break
        yield from hands.pad.press("A", why, f"bag cursor on {row} ({name})")
        if not (yield from choose(hands, "bag_action", USE_OPTION, f"{why}: USE {name}")):
            said = f"USE could not be chosen for {name}"
            break
        party = yield from wait_for_ui(hands, "party", f"{why}: use on which POKéMON?")
        if party is None:
            said = "the party did not open for the item"
            break
        slot = next((i for i, m in enumerate(party.party or ()) if m.pid == pid), None)
        if slot is None:
            said = f"{pid:08x} is not in the party the menu shows"
            break
        if not (yield from move_cursor(hands, "party", slot, f"{why}: {member.species}")):
            said = f"the party cursor did not reach {member.species}"
            break
        gate = hands.look()
        ui = gate.screen.ui
        if ui is None or ui.kind != "party" or ui.cursor != slot or not ui.accepts_input:
            said = f"the party cursor is not on {member.species} before the press"
            break
        yield from hands.pad.press("A", why, f"party cursor on {slot} ({member.species}): use the {name}")
        used += 1
        if not (yield from _read_message(hands, why)):
            said = f"the {name}'s message did not end in the bag"
            break
        said = f"{name} used on {member.species}"
    closed = yield from _close(hands, why)
    after = hands.look()
    hp_after = _hp(after, pid)
    fell = sum(counts_before[name] - _count(after, name) for name in items)
    same = sorted(_pids(after)) == sorted(before_pids)
    rose = hp_before is not None and hp_after is not None and hp_after[0] > hp_before[0]
    ok = used > 0 and rose and fell == used and same and closed
    hands.tell(f"{why}: {member.species} ({pid:08x}) {hp_before} -> {hp_after}; {used} item(s) used, the bag's count fell "
               f"by {fell}; the party's PIDs {'unchanged' if same else 'CHANGED'}; {said} -> {'OK' if ok else 'FAILED'}")
    return ok, used, f"{said}; {member.species} {hp_before} -> {hp_after}, {used} used, the count fell by {fell}"
