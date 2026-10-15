"""The AI's MENU DRIVER (build step 2): move a cursor by READING it, choose by intent, type a name on the
naming keyboard, set the wall clock, and two services built from those: the Pokemon Center nurse and the
Poke Mart.

WHY THE CURSOR IS READ, NEVER COUNTED. A press count assumes the cursor starts where the counter thinks and
that every press lands. Neither is safe in Emerald: the naming keyboard's cursor stays on the LAST key
typed, the start menu remembers its last row (`sStartMenuCursorPos`), the wall clock's "Is this the correct
time?" opens on NO (`src/wallclock.c` CreateYesNoMenu(..., 1)), a script's yes/no ignores the D-pad for its
first 5 frames (`Task_HandleYesNoInput`), and a multichoice for 2 to 12 (`sProcessInputDelay`). So every move
here is: look, press ONE step toward the target, look again; and the A that confirms is pressed only when the
look right before it shows the cursor ON the target (that check is the press's gate, in the action log).

FAULT `blind_count` (`hands/pad.py` Faults): the naive driver moves by a press count from the top (and, on
the keyboard, from the top-left key for every letter), without reading. `gates/live_step2.py` runs it beside
the real driver on the keyboard, whose cursor starts wherever the previous letter left it.

Every loop is bounded; a routine that cannot finish returns False (or an outcome string) and says why in the
run's log. Nothing here waits without a reason (`hands/pad.py`).
"""

from __future__ import annotations

import time
from collections.abc import Generator

from ai_player.eyes.observation import Observation, SeenObject
from ai_player.eyes.screens import KEYBOARD_COLUMNS, KEYBOARD_PAGES, key_position
from ai_player.hands.dialogue import advance, awaits_press, dialogue_over, talk, talk_direction
from ai_player.hands.pad import Hands

__all__ = [
    "BLIND_GATE",
    "GAVE_WAY",
    "MART_CLERK_GFX",
    "NURSE_GFX",
    "answer_yes_no",
    "choose",
    "clock_hold_frames",
    "find_person",
    "item_key",
    "local_clock",
    "mart_buy",
    "move_cursor",
    "nurse_heal",
    "set_clock",
    "set_quantity",
    "type_name",
    "wait_for_ui",
]

#: What a person recognises a Pokemon Center nurse and a mart clerk by: their LOOK (`include/constants/
#: event_objects.h` OBJ_EVENT_GFX_NURSE 58, OBJ_EVENT_GFX_MART_EMPLOYEE 83). The eyes report every person as
#: an "npc" with its graphics id (`eyes/view.py` object_kind); recognising a uniform is the hands' business.
NURSE_GFX = 58
MART_CLERK_GFX = 83
#: The gate the blind-count FAULT writes on its presses.
BLIND_GATE = "NONE (FAULT blind count: pressed by count from the top, the cursor not read)"
#: (build step 5.1, the verifier's second round: the round's development sweep, seed 42, stood 1,203 frames in `talk` in
#: front of the nurse while "TREECKO fainted…" (the poison's faint on the way in) waited for A) what `nurse_heal` and
#: `mart_buy` return, with `give_way`, when a screen that waits for a press came before the talk: the caller plays it
GAVE_WAY = "a screen that waits for a press came before the talk: handed back"
#: Bounds.
WAIT_UI_BUDGET = 600  # frames for a menu to appear
MOVE_BUDGET = 60  # presses to bring a cursor to its target
CONFIRM_BUDGET = 45  # frames for a menu to react to its A
TYPE_BUDGET = 400  # presses to type a name
CLOCK_BUDGET = 3000  # frames to set the clock


def item_key(name: str) -> str:
    """An item name compared across the screen ("POKé BALL") and the bag's table ("Poké Ball")."""
    return "".join(c for c in name.casefold() if c.isalnum())


def wait_for_ui(hands: Hands, kind: str, why: str, budget: int = WAIT_UI_BUDGET) -> Generator[None, None, Observation | None]:
    """Watch until the `kind` menu is on screen AND takes input. Returns that look, or None (budget)."""
    for _ in range(budget):
        look = hands.look()
        ui = look.screen.ui
        if ui is not None and ui.kind == kind and ui.accepts_input:
            return look
        yield from hands.pad.busy(f"waiting for the {kind} to open ({why})")
    hands.tell(f"{why}: the {kind} did not open within {budget} frames")
    return None


def move_cursor(hands: Hands, kind: str, target: int, why: str) -> Generator[None, None, bool]:
    """Bring the `kind` menu's cursor to option `target`: look, one press toward it, look again. True when a
    look shows it there. (FAULT blind_count: press Down `target` times from the top and believe it.)
    It waits for the menu to take input by itself: inside `choose` that is redundant (choose waited first), but
    a direct call on a menu in its input delay would otherwise lose presses (`gates/revert_step2.py` H9)."""
    if hands.faults.blind_count:
        for _ in range(target):
            yield from hands.pad.press("Down", why, BLIND_GATE)
        return True
    for _ in range(MOVE_BUDGET):
        look = hands.look()
        ui = look.screen.ui
        if ui is None or ui.kind != kind:
            hands.tell(f"{why}: the {kind} closed while the cursor was being moved")
            return False
        if not ui.accepts_input or ui.cursor is None:
            yield from hands.pad.busy(f"waiting for the {kind} to take input")
            continue
        if ui.cursor == target:
            return True
        button = "Down" if ui.cursor < target else "Up"
        yield from hands.pad.press(button, why, f"{kind} cursor on {_name(ui.options, ui.cursor)}, wanted "
                                                f"{_name(ui.options, target)}: one step {button.lower()}")
    hands.tell(f"{why}: the {kind} cursor did not reach {target} in {MOVE_BUDGET} presses")
    return False


def _name(options: tuple[str, ...], index: int | None) -> str:
    if index is not None and 0 <= index < len(options):
        return f"{index} ({options[index]})"
    return str(index)


def choose(hands: Hands, kind: str, option: str | int, why: str, budget: int = WAIT_UI_BUDGET) -> Generator[None, None, bool]:
    """Choose `option` (its name, or its index) in the `kind` menu: wait for the menu, look at it for a moment,
    bring the cursor there (`move_cursor`), and press A only when the look right before the press shows the
    cursor ON it. Returns True once the menu has reacted (it closed or changed); an A the game dropped is
    pressed again (at most 3 times).

    The gate's look is the SAME frame as move_cursor's last one, so today its checks repeat move_cursor's: the
    cursor check stands on its own only if move_cursor is wrong (`gates/revert_step2.py` H3, caught by
    `test_the_press_gate_is_its_own_look`), and its accepts_input check is redundant alone (H11)."""
    look = yield from wait_for_ui(hands, kind, why, budget)
    if look is None:
        return False
    ui = look.screen.ui
    if isinstance(option, int):
        index = option
    elif option in ui.options:
        index = ui.options.index(option)
    else:
        hands.tell(f"{why}: {option!r} is not in the {kind} ({ui.options})")
        return False
    yield from hands.pad.idle(hands.pad.think_frames(), f"looking at the {kind}: {list(ui.options)}, cursor on "
                                                        f"{_name(ui.options, ui.cursor)}; wanted {_name(ui.options, index)}")
    for _ in range(3):
        if not (yield from move_cursor(hands, kind, index, why)):
            return False
        look = hands.look()  # THE GATE: the cursor is on the option, on the look right before the press
        ui = look.screen.ui
        if hands.faults.blind_count:
            # The naive driver is blind to the CURSOR only (the one thing the fault isolates): like the real driver
            # it waits for the menu to take input before its A. STEP 2.1: moving the gender menu's cursor slides
            # Birch's sprites, and the menu ignores input meanwhile (`eyes/screens.py` UI_BUSY_TASKS); an A pressed
            # into the slide was dropped, which the intro's old loop hid by choosing again (the review's item 6).
            if (yield from wait_for_ui(hands, kind, why)) is None:
                return False
            yield from hands.pad.press("A", why, BLIND_GATE)
        elif ui is not None and ui.kind == kind and ui.cursor == index and ui.accepts_input:
            yield from hands.pad.press("A", why, f"{kind} cursor on {_name(ui.options, index)}")
        else:
            continue
        for _ in range(CONFIRM_BUDGET):
            look = hands.look()
            ui = look.screen.ui
            if ui is None or ui.kind != kind:
                return True
            yield from hands.pad.busy(f"waiting for the {kind} to take the choice")
        if hands.faults.blind_count:
            return False
    hands.tell(f"{why}: the {kind} did not take the choice {_name(ui.options if ui else (), index)}")
    return False


def answer_yes_no(hands: Hands, yes: bool, why: str) -> Generator[None, None, bool]:
    """Answer the yes/no on screen by INTENT (the cursor is read: some open on NO)."""
    return (yield from choose(hands, "yes_no", "YES" if yes else "NO", why))


# ------------------------------------------------------------------------------------------- the keyboard
def type_name(hands: Hands, name: str, why: str) -> Generator[None, None, bool]:
    """Type `name` on the naming keyboard and confirm it on OK. Each key: switch the page with SELECT until the
    page shows the letter, step the cursor toward its key (the shorter way round, the row wraps), and press A
    only when the cursor is ON it; a wrong letter is deleted with B. The text typed so far is READ after every
    press. Returns True once the keyboard has closed with `text == name`. (The re-check of OK after the
    'think' pause is redundant alone, `gates/revert_step2.py` H5c: the cursor moves only on a press.)"""
    if hands.faults.blind_count:
        return (yield from _type_blind(hands, name, why))
    pressed_ok = False
    for _ in range(TYPE_BUDGET):
        look = hands.look()
        ui = look.screen.ui
        if ui is None or ui.kind != "naming":
            if pressed_ok:
                return True
            yield from hands.pad.busy("waiting for the naming keyboard")
            continue
        if not ui.accepts_input or ui.cursor_xy is None or ui.page not in KEYBOARD_PAGES or ui.text is None:
            yield from hands.pad.busy("waiting for the keyboard to take input")
            continue
        x, y = ui.cursor_xy
        text, page = ui.text, ui.page
        if text == name:
            ok = (KEYBOARD_COLUMNS[page], 2)
            if (x, y) != ok:
                yield from hands.pad.press("Start", why, f"keyboard: {text!r} is typed; START puts the cursor on OK")
                continue
            yield from hands.pad.idle(hands.pad.think_frames(), f"checking the name on the keyboard: {text!r}")
            look = hands.look()
            ui = look.screen.ui
            if ui is not None and ui.kind == "naming" and ui.text == name and ui.cursor_xy == ok:
                yield from hands.pad.press("A", why, f"keyboard: the text reads {name!r} and the cursor is on OK")
                pressed_ok = True
            continue
        if not name.startswith(text):
            yield from hands.pad.press("B", why, f"keyboard: {text!r} is not how {name!r} begins: B deletes a letter")
            continue
        char = name[len(text)]
        where = key_position(char)
        if where is None:
            hands.tell(f"{why}: no key types {char!r}")
            return False
        want_page, column, row = where
        if page != want_page:
            yield from hands.pad.press("Select", why, f"keyboard: {char!r} is on the {want_page} page, this is the {page} page")
            continue
        if x != column:
            columns = KEYBOARD_COLUMNS[page] + 1  # the keys, then the button column; the row wraps
            right, left = (column - x) % columns, (x - column) % columns
            button = "Right" if right <= left else "Left"
            yield from hands.pad.press(button, why, f"keyboard: cursor at ({x},{y}), {char!r} is at ({column},{row})")
            continue
        if y != row:
            down, up = (row - y) % 4, (y - row) % 4
            button = "Down" if down <= up else "Up"
            yield from hands.pad.press(button, why, f"keyboard: cursor at ({x},{y}), {char!r} is at ({column},{row})")
            continue
        yield from hands.pad.press("A", why, f"keyboard: cursor on {char!r} at ({x},{y}) of the {page} page")
    hands.tell(f"{why}: the name {name!r} was not typed within {TYPE_BUDGET} steps")
    return False


def _type_blind(hands: Hands, name: str, why: str) -> Generator[None, None, bool]:
    """FAULT blind_count: for every letter, switch pages by COUNT (the page it believes it is on), then press
    Right `column` times and Down `row` times as if the cursor were on the top-left key, then A; then START
    and A on OK. Nothing is read. (The game's cursor stays on the previous letter's key.)"""
    believed = "upper"  # NamingScreen_Init: the player's keyboard opens on the upper-case page
    order = ("symbols", "upper", "lower")  # SELECT cycles currentPage 0 -> 1 -> 2 -> 0
    look = yield from wait_for_ui(hands, "naming", why)
    if look is None:
        return False
    for char in name:
        where = key_position(char)
        if where is None:
            return False
        page, column, row = where
        while believed != page:
            yield from hands.pad.press("Select", why, BLIND_GATE)
            believed = order[(order.index(believed) + 1) % 3]
            yield from hands.pad.idle(30, "letting the page turn (counted, not read)")
        for _ in range(column):
            yield from hands.pad.press("Right", why, BLIND_GATE)
        for _ in range(row):
            yield from hands.pad.press("Down", why, BLIND_GATE)
        yield from hands.pad.press("A", why, BLIND_GATE)
    yield from hands.pad.press("Start", why, BLIND_GATE)
    yield from hands.pad.press("A", why, BLIND_GATE)
    for _ in range(WAIT_UI_BUDGET):
        look = hands.look()
        if look.screen.ui is None or look.screen.ui.kind != "naming":
            return True
        yield from hands.pad.busy("waiting for the keyboard to close")
    return False


# ------------------------------------------------------------------------------------------- the clock
def clock_hold_frames(minutes: int) -> int:
    """How long to HOLD the D-pad on the wall clock to turn the hand `minutes` minutes. `src/wallclock.c`:
    each minute the hand starts while the button is held, `tMoveSpeed` grows by one, and the hand turns
    `CalcMinHandDelta(speed)` degrees a frame (1 up to speed 10, 2 to 30, 3 to 60, then 6) until it reaches the
    next minute (6 degrees): 6, 3, 2, then 1 frames a minute."""
    frames = 0
    for minute in range(1, max(0, minutes) + 1):
        frames += 6 if minute <= 10 else 3 if minute <= 30 else 2 if minute <= 60 else 1
    return frames


def set_clock(hands: Hands, hours: int, minutes: int, why: str) -> Generator[None, None, bool]:
    """Set the wall clock to `hours`:`minutes` and confirm it. The time is READ from the clock (`MenuView`
    hours, minutes) after every move: a long HOLD while it is far (the hand speeds up, `clock_hold_frames`),
    then single short presses (each turns it exactly one minute: a press shorter than the 6 frames a minute
    takes), and A only when it reads the time wanted. "Is this the correct time?" opens on NO: YES is chosen
    by reading the cursor. True once the clock screen has closed after a YES. (The re-check of the time after
    the 'think' pause is redundant alone, `gates/revert_step2.py` H8b: the hand turns only while held.)"""
    want = (hours % 24) * 60 + minutes % 60
    confirmed = False
    for _ in range(CLOCK_BUDGET):
        look = hands.look()
        ui = look.screen.ui
        if ui is not None and ui.kind == "yes_no":
            confirmed = yield from answer_yes_no(hands, True, f"{why}: the clock reads {hours}:{minutes:02d}")
            if not confirmed:
                # STEP 2.1 (the step-2 review, item 6): a failed answer is reported at once, not retried until
                # CLOCK_BUDGET runs out (`answer_yes_no` has said why in the run's log).
                hands.tell(f"{why}: 'Is this the correct time?' could not be answered YES")
                return False
            continue
        if ui is None or ui.kind != "clock":
            if confirmed:
                return True
            yield from hands.pad.busy("waiting for the clock")
            continue
        if not ui.accepts_input or ui.hours is None or ui.minutes is None:
            yield from hands.pad.busy("watching the clock's hand turn")
            continue
        now = ui.hours * 60 + ui.minutes
        forward, backward = (want - now) % 1440, (now - want) % 1440
        if forward == 0:
            yield from hands.pad.idle(hands.pad.think_frames(), f"the clock reads {ui.hours}:{ui.minutes:02d}")
            look = hands.look()
            ui = look.screen.ui
            if ui is not None and ui.kind == "clock" and ui.accepts_input and ui.hours * 60 + ui.minutes == want:
                yield from hands.pad.press("A", why, f"clock reads {ui.hours}:{ui.minutes:02d}, the time wanted")
            continue
        button, distance = ("Right", forward) if forward <= backward else ("Left", backward)
        gate = f"clock reads {ui.hours}:{ui.minutes:02d}, wanted {hours}:{minutes:02d}: {distance} minutes {button.lower()}"
        if distance > 8:
            yield from hands.pad.hold(button, max(1, clock_hold_frames(distance - 4)), why, gate)
        else:
            yield from hands.pad.press(button, why, gate, hold=hands.pad.pacing.turn[0])
    hands.tell(f"{why}: the clock was not set within {CLOCK_BUDGET} frames")
    return False


# ------------------------------------------------------------------------------------------- services
def find_person(look: Observation, graphics_id: int) -> SeenObject | None:
    """The person on screen who LOOKS like `graphics_id` (the nurse's or the clerk's uniform), nearest first."""
    if look.view is None:
        return None
    people = [o for o in look.view.objects if o.source == "object" and o.graphics_id == graphics_id]
    people.sort(key=lambda o: abs(o.dx) + abs(o.dy))
    return people[0] if people else None


def nurse_heal(hands: Hands, why: str = "heal the party at the nurse", give_way: bool = False) -> Generator[None, None, str]:
    """Talk to the nurse in front of the player and accept the healing: advance her text (gated on the eyes'
    waits), answer her yes/no with YES by intent, advance to the end of the conversation, then CHECK: every
    party Pokemon at full HP on the eyes. Returns "healed", or what went wrong. (Build step 5.1, the verifier's second
    round) `give_way`: a screen that waits for a press before she is talked to is handed back at once (`GAVE_WAY`), never
    waited out (the step-2 default, False, is unchanged)."""
    look = hands.look()
    nurse = find_person(look, NURSE_GFX)
    if nurse is None or talk_direction(look, nurse) is None:
        return "no nurse in talking reach"
    hands.tell(f"{why}: the nurse at ({nurse.dx},{nurse.dy}); party HP "
               f"{[(m.species, m.hp, m.max_hp) for m in look.party or ()]}")
    if not (yield from talk(hands, nurse, why, give_way=give_way)):
        if give_way and awaits_press(hands.look()) is not None:
            return GAVE_WAY
        return "the nurse did not answer"
    for _ in range(6):
        outcome = yield from advance(hands, dialogue_over, why)
        if outcome == "done":
            break
        if outcome == "menu:yes_no":
            # STEP 2.1 (the step-2 review, item 6): a failed answer ends the skill at once with its reason, instead
            # of going round this loop until its 6 turns run out.
            if not (yield from answer_yes_no(hands, True, f"{why}: 'Would you like to rest your POKéMON?' YES")):
                return "the nurse's yes/no could not be answered YES"
            continue
        return f"the nurse's dialogue ended in {outcome}"
    else:
        return "the nurse's dialogue did not end"
    look = hands.look()
    party = look.party or ()
    if party and all(m.hp == m.max_hp for m in party):
        hands.tell(f"{why}: done; party HP {[(m.species, m.hp, m.max_hp) for m in party]}")
        return "healed"
    return f"the party is not at full HP after the nurse: {[(m.species, m.hp, m.max_hp) for m in party]}"


def set_quantity(hands: Hands, count: int, why: str) -> Generator[None, None, bool]:
    """Set the mart's "How many?" box to `count`, READING the quantity after every press (`src/menu_helpers.c`
    AdjustQuantityAccordingToDPadInput: Up +1, Down -1, Right +10, Left -10, wrapping between 1 and the
    maximum the money allows), then A when it reads `count`."""
    look = yield from wait_for_ui(hands, "mart_quantity", why)
    if look is None:
        return False
    for _ in range(MOVE_BUDGET):
        look = hands.look()
        ui = look.screen.ui
        if ui is None or ui.kind != "mart_quantity" or ui.quantity is None:
            hands.tell(f"{why}: the quantity box closed")
            return False
        if ui.max_quantity is not None and count > ui.max_quantity:
            hands.tell(f"{why}: {count} is more than the money allows ({ui.max_quantity})")
            return False
        if ui.quantity == count:
            yield from hands.pad.press("A", why, f"mart_quantity reads x{ui.quantity}, the number wanted")
            return True
        difference = count - ui.quantity
        if hands.faults.blind_count:
            button = "Up"
        elif difference >= 10:
            button = "Right"
        elif difference <= -10:
            button = "Left"
        else:
            button = "Up" if difference > 0 else "Down"
        yield from hands.pad.press(button, why, f"mart_quantity reads x{ui.quantity}, wanted x{count}")
    return False


def mart_buy(hands: Hands, item: str, count: int, why: str = "buy at the mart",
             give_way: bool = False) -> Generator[None, None, str]:
    """Buy `count` of `item` from the clerk in front of the player: talk; BUY; the item, by its NAME in the
    list; the quantity, read; YES to the price; then leave the list (B) and the shop menu (QUIT) and advance
    the goodbye. Then CHECK on the eyes: that item in the bag rose by exactly `count` and the money fell by
    `count` x its listed price. Returns "bought", or what went wrong. (Build step 5.1, the verifier's second round)
    `give_way`: as `nurse_heal`'s."""
    look = hands.look()
    clerk = find_person(look, MART_CLERK_GFX)
    if clerk is None or talk_direction(look, clerk) is None:
        return "no clerk in talking reach"
    key = item_key(item)
    before = _bag_count(look, key)
    money_before = look.progress.money if look.progress is not None else None
    hands.tell(f"{why}: {count} x {item}; the clerk at ({clerk.dx},{clerk.dy}); in the bag {before}, money {money_before}")
    if not (yield from talk(hands, clerk, why, give_way=give_way)):
        if give_way and awaits_press(hands.look()) is not None:
            return GAVE_WAY
        return "the clerk did not answer"
    bought = False
    price = None
    for _ in range(12):
        outcome = yield from advance(hands, dialogue_over, why)
        if outcome == "done":
            break
        if outcome == "menu:mart_menu":
            # STEP 2.1 (the step-2 review, item 6): a failed choice ends the skill at once with its reason, instead
            # of going round this loop until its 12 turns run out.
            wanted = "QUIT" if bought else "BUY"
            if not (yield from choose(hands, "mart_menu", wanted, f"{why}: the shop menu")):
                return f"could not choose {wanted} in the shop menu"
        elif outcome == "menu:mart_buy" and not bought:
            look = yield from wait_for_ui(hands, "mart_buy", why)
            names = [item_key(n) for n in look.screen.ui.options] if look is not None else []
            if key not in names:
                return f"{item} is not for sale here: {look and look.screen.ui.options}"
            row = names.index(key)
            prices = look.screen.ui.prices
            price = prices[row] if row < len(prices) else None
            if not (yield from choose(hands, "mart_buy", row, f"{why}: {item} in the list")):
                return "could not choose the item"
            outcome = yield from advance(hands, lambda l: l.screen.ui is not None and l.screen.ui.kind == "mart_quantity", why)
            if outcome not in ("done", "menu:mart_quantity"):
                return f"no quantity box: {outcome}"
            if not (yield from set_quantity(hands, count, f"{why}: how many")):
                return "could not set the quantity"
            outcome = yield from advance(hands, lambda l: l.screen.ui is not None and l.screen.ui.kind == "yes_no", why)
            if outcome not in ("done", "menu:yes_no"):
                return f"no price question: {outcome}"
            if not (yield from answer_yes_no(hands, True, f"{why}: the price is right")):
                return "the price question was not answered"
            bought = True
        elif outcome == "menu:mart_buy" and bought:
            yield from hands.pad.idle(hands.pad.think_frames(), "done buying: leaving the list")
            look = hands.look()
            if look.screen.ui is not None and look.screen.ui.kind == "mart_buy" and look.screen.ui.accepts_input:
                yield from hands.pad.press("B", why, "the item list is open: B leaves it (LIST_CANCEL)")
            for _ in range(WAIT_UI_BUDGET):
                look = hands.look()
                if look.screen.ui is None or look.screen.ui.kind != "mart_buy":
                    break
                yield from hands.pad.busy("waiting for the list to close")
        else:
            return f"unexpected in the mart: {outcome}"
    else:
        return "the mart conversation did not end"
    look = hands.look()
    after = _bag_count(look, key)
    money_after = look.progress.money if look.progress is not None else None
    hands.tell(f"{why}: done; {item} in the bag {before} -> {after}, money {money_before} -> {money_after}, listed price {price}")
    if before is None or after is None or after - before != count:
        return f"the bag holds {after} {item} (was {before}), not {count} more"
    if price is not None and money_before is not None and money_after is not None and money_before - money_after != count * price:
        return f"the money fell by {money_before - money_after}, not {count} x {price}"
    return "bought"


def _bag_count(look: Observation, key: str) -> int | None:
    if look.bag is None:
        return None
    return sum(quantity for name, quantity in look.bag.balls + look.bag.healing if item_key(name) == key)


def local_clock() -> tuple[int, int]:
    """The time a person would set: their own clock's (the computer's local time)."""
    now = time.localtime()
    return now.tm_hour, now.tm_min
