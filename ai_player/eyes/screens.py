"""The AI's PERCEPTION OF MENUS AND TEXT (build step 2): which interactive thing is on screen, where its
cursor is, and what text has printed. Framework-free.

WHY THIS FILE (build step 2, the hands): a person at the screen sees WHICH menu is open and WHICH option is
highlighted, reads the text in the box, and sees the letters on the naming keyboard. The hands
(`ai_player/hands/`) move a cursor by READING it, never by counting presses (a press the game drops while a
window opens, or a menu that remembers its last position, makes a count wrong), and they press A on text
only when the game waits for it. This file turns the raw numbers `ai_player/host/eyes.py` reads into that
picture; it reads nothing itself. Every table names the pret/pokeemerald source it was copied from.

HOW A MENU IS RECOGNISED: by the TASK that processes its input (`gTasks[].func`), the same way the game
itself runs it. A menu's cursor struct outlives the menu (`sMenu` keeps its last values after the window
closes), so a cursor is reported only while its menu's input task is active.

WHAT IS READ FOR EACH (the host reads the bytes; `read_ui` interprets them):
  * yes/no, the gender menu, the mart's BUY/SELL/QUIT, a script's multichoice: `sMenu` (`src/menu.c`
    struct Menu: cursorPos @2 (s8), minCursorPos @3, maxCursorPos @4); `CreateYesNoMenu` and
    `InitMenuInUpperLeftCornerNormal` fill it, `Menu_ProcessInputNoWrap` moves it;
  * the main menu: its task's data (`src/main_menu.c`: tMenuType data[0], tCurrItem data[1]);
  * the start menu: `sStartMenuCursorPos`, `sNumStartMenuActions`, `sCurrentStartMenuActions`;
  * the naming keyboard: `sNamingScreen` (`src/naming_screen.c` struct NamingScreenData: textBuffer
    @0x1800, state @0x1E10, currentPage @0x1E22, cursorSpriteId @0x1E23, template @0x1E28) and the cursor
    SPRITE's data[0] / data[1] (its column and row: `SetCursorPos` stores them there);
  * the wall clock: its task's data (`src/wallclock.c`: tMinuteHandAngle data[0], tHours data[2],
    tMinutes data[3]);
  * the mart's buy list: `sMartInfo` (itemList @8, itemCount @0xC, martType @0xF) and `sShopData`
    (selectedRow @0x2006, scrollOffset @0x2008, maxQuantity @0x200A); the quantity: its task's data[1];
  * the bag: `gBagPosition` (pocket @5, cursorPosition[5] @8, scrollPosition[5] @0x12); the party menu:
    `gPartyMenu.slotId` @9.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ai_player.eyes.observation import MenuView

__all__ = [
    "BAG_POCKETS",
    "CHARMAP",
    "GENDER_OPTIONS",
    "KEYBOARD_COLUMNS",
    "KEYBOARD_PAGES",
    "MAIN_MENU_OPTIONS",
    "NAMING_STATE_HANDLE_INPUT",
    "PARAGRAPH",
    "SCENE_CALLBACKS",
    "SCENE_STATES",
    "SCENE_TASKS",
    "SHOP_OPTIONS",
    "START_MENU_ACTIONS",
    "TASK_WAITS",
    "UI_TASKS",
    "YES_NO",
    "decode_text",
    "encode_char",
    "key_position",
    "page_text",
    "read_ui",
    "scene_of",
    "task_wait",
]

# --------------------------------------------------------------------------------------------- text
#: pret/pokeemerald `charmap.txt`: the characters of English text (the accented letters a few names use,
#: digits, punctuation, A-Z, a-z). 0x53 0x54 is "PKMN" in two glyphs; 0xB7 is the money sign the game prints.
CHARMAP: dict[int, str] = {
    0x00: " ", 0x01: "À", 0x02: "Á", 0x03: "Â", 0x04: "Ç", 0x05: "È", 0x06: "É", 0x07: "Ê", 0x08: "Ë", 0x09: "Ì",
    0x0B: "Î", 0x0C: "Ï", 0x0D: "Ò", 0x0E: "Ó", 0x0F: "Ô", 0x10: "Œ", 0x11: "Ù", 0x12: "Ú", 0x13: "Û", 0x14: "Ñ",
    0x15: "ß", 0x16: "à", 0x17: "á", 0x19: "ç", 0x1A: "è", 0x1B: "é", 0x1C: "ê", 0x1D: "ë", 0x1E: "ì", 0x20: "î",
    0x21: "ï", 0x22: "ò", 0x23: "ó", 0x24: "ô", 0x25: "œ", 0x26: "ù", 0x27: "ú", 0x28: "û", 0x29: "ñ", 0x2D: "&",
    0x2E: "+", 0x34: "Lv", 0x35: "=", 0x36: ";", 0x51: "¿", 0x52: "¡", 0x53: "PK", 0x54: "MN", 0x5A: "Í", 0x5B: "%",
    0x5C: "(", 0x5D: ")", 0x68: "â", 0x6F: "í", 0x77: " ", 0x85: "<", 0x86: ">",  # 0x77 UNK_SPACER (money box)
    0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-", 0xAF: "·", 0xB0: "…", 0xB1: "“", 0xB2: "”", 0xB3: "‘", 0xB4: "’",
    0xB5: "♂", 0xB6: "♀", 0xB7: "₽", 0xB8: ",", 0xB9: "×", 0xBA: "/", 0xF0: ":",
    **{0xA1 + i: str(i) for i in range(10)},
    **{0xBB + i: chr(ord("A") + i) for i in range(26)},
    **{0xD5 + i: chr(ord("a") + i) for i in range(26)},
}
_ENCODE: dict[str, int] = {}
for _code, _char in sorted(CHARMAP.items(), reverse=True):
    if len(_char) == 1:
        _ENCODE[_char] = _code
_ENCODE["'"] = 0xB4  # charmap.txt: '\'' = B4, the same glyph as ’
#: The mark this file writes for a paragraph break (`\p`, 0xFB): the box is cleared and a new page begins.
PARAGRAPH = "¶"
#: `src/string_util.c` GetExtCtrlCodeLength: how many bytes an extended control code (0xFC, code, args)
#: takes, the 0xFC included is NOT counted here (the table counts the code and its arguments).
_EXT_CTRL_LENGTHS = (1, 2, 2, 2, 4, 2, 2, 1, 2, 1, 1, 3, 2, 2, 2, 1, 3, 2, 2, 2, 2, 1, 1, 1, 1)
_NEWLINE, _SCROLL, _PARAGRAPH, _EXT_CTRL, _PLACEHOLDER, _EOS = 0xFE, 0xFA, 0xFB, 0xFC, 0xFD, 0xFF


def decode_text(data: Iterable[int], limit: int | None = None) -> str:
    """A Gen-3 string as a person reads it: letters as letters, a line break (`\\n`, `\\l`) as a space, a
    paragraph break as PARAGRAPH, control codes (colours, pauses, sounds) left out, an unknown glyph as
    `<XX>`. Stops at the terminator 0xFF or after `limit` bytes."""
    raw = bytes(data) if limit is None else bytes(data)[:limit]
    out: list[str] = []
    index = 0
    while index < len(raw):
        byte = raw[index]
        if byte == _EOS:
            break
        if byte in (_NEWLINE, _SCROLL):
            out.append(" ")
        elif byte == _PARAGRAPH:
            out.append(PARAGRAPH)
        elif byte == _EXT_CTRL:
            code = raw[index + 1] if index + 1 < len(raw) else 0
            index += 1 + (_EXT_CTRL_LENGTHS[code] if code < len(_EXT_CTRL_LENGTHS) else 1)
            continue
        elif byte == _PLACEHOLDER:
            index += 2
            continue
        else:
            out.append(CHARMAP.get(byte, f"<{byte:02X}>"))
        index += 1
    return "".join(out)


def encode_char(char: str) -> int | None:
    """The game's byte for one character, or None if the charmap above has none."""
    return _ENCODE.get(char)


def page_text(text: str | None) -> str | None:
    """The PAGE of a message that is on screen now: what printed since the last paragraph break. A printer
    waiting at a paragraph break (RENDER_STATE_CLEAR) has already consumed the `\\p`, so a text that ENDS with
    the break still shows the page before it (measured on Birch's speech, 2026-10-07: the page read as "")."""
    if text is None:
        return None
    body = text.rstrip()
    if body.endswith(PARAGRAPH):
        body = body[:-len(PARAGRAPH)]
    return body.rsplit(PARAGRAPH, 1)[-1].strip()


# --------------------------------------------------------------------------------------------- the keyboard
#: `src/naming_screen.c` sKeyboardChars, by the PAGE a person sees (`currentPage`: KBPAGE_SYMBOLS 0,
#: KBPAGE_LETTERS_UPPER 1, KBPAGE_LETTERS_LOWER 2; Select cycles 0 -> 1 -> 2 -> 0, `MainState_WaitPageSwap`).
#: Each page is 4 rows; a space in a row is an EMPTY key on the lower/upper pages (`__("abcdef .")`: the
#: 7th key is a space character on screen too, and typing it types a space).
KEYBOARD_PAGES: dict[str, tuple[str, str, str, str]] = {
    "symbols": ("01234   ", "56789   ", "!?♂♀/-  ", "…“”‘'   "),
    "upper": ("ABCDEF .", "GHIJKL ,", "MNOPQRS ", "TUVWXYZ "),
    "lower": ("abcdef .", "ghijkl ,", "mnopqrs ", "tuvwxyz "),
}
#: `sPageColumnCounts`: the column index EQUAL to the count is the button column (PAGE, BACK, OK in rows 0-2).
KEYBOARD_COLUMNS: dict[str, int] = {"symbols": 6, "upper": 8, "lower": 8}
_PAGE_BY_ID = ("symbols", "upper", "lower")
#: Task_NamingScreen's `state` while it handles input (`src/naming_screen.c` STATE_HANDLE_INPUT).
NAMING_STATE_HANDLE_INPUT = 2


def key_position(char: str) -> tuple[str, int, int] | None:
    """(page, column, row) of the key that types `char`, preferring the letter pages; None if no key types it."""
    for page in ("upper", "lower", "symbols"):
        for row, keys in enumerate(KEYBOARD_PAGES[page]):
            column = keys.find(char)
            if column >= 0 and column < KEYBOARD_COLUMNS[page]:
                return page, column, row
    return None


# --------------------------------------------------------------------------------------------- menus
#: The interactive things a person recognises, by the task that runs them (`gTasks[].func` names).
UI_TASKS: dict[str, str] = {
    "Task_HandleYesNoInput": "yes_no",  # src/script_menu.c (a script's yesnobox / msgbox MSGBOX_YESNO)
    "Task_CallYesOrNoCallback": "yes_no",  # src/menu_helpers.c (the mart's "Okay?")
    "Task_NewGameBirchSpeech_ProcessNameYesNoMenu": "yes_no",  # src/main_menu.c ("So it's NAME?")
    "Task_SetClock_HandleConfirmInput": "yes_no",  # src/wallclock.c ("Is this the correct time?", default NO)
    "Task_NewGameBirchSpeech_ChooseGender": "gender",  # src/main_menu.c
    "Task_HandleMultichoiceInput": "multichoice",  # src/script_menu.c
    "Task_HandleMultichoiceGridInput": "multichoice",
    "Task_ShopMenu": "mart_menu",  # src/shop.c (BUY / SELL / QUIT)
    "Task_BuyMenu": "mart_buy",  # src/shop.c (the item list)
    "Task_BuyHowManyDialogueHandleInput": "mart_quantity",  # src/shop.c ("How many?")
    "Task_SetClock_HandleInput": "clock",  # src/wallclock.c
    "StartMenuTask": "start_menu",  # src/start_menu.c (runs HandleStartMenuInput)
    "Task_HandleMainMenuInput": "main_menu",  # src/main_menu.c
    "Task_HighlightSelectedMainMenuItem": "main_menu",
    "Task_TitleScreenPhase3": "title",  # src/title_screen.c: A or START goes to the main menu
}
YES_NO = ("YES", "NO")  # src/strings.c gText_YesNo "YES\nNO"
GENDER_OPTIONS = ("BOY", "GIRL")  # src/main_menu.c sMenuActions_Gender (gText_BirchBoy, gText_BirchGirl)
SHOP_OPTIONS = {0: ("BUY", "SELL", "QUIT"), 1: ("BUY", "QUIT"), 2: ("BUY", "QUIT")}  # by MartInfo.martType
#: src/main_menu.c Task_HandleMainMenuAPressed, by tMenuType (HAS_NO_SAVED_GAME 0, HAS_SAVED_GAME 1,
#: HAS_MYSTERY_GIFT 2, HAS_MYSTERY_EVENTS 3).
MAIN_MENU_OPTIONS = {
    0: ("NEW GAME", "OPTION"),
    1: ("CONTINUE", "NEW GAME", "OPTION"),
    2: ("CONTINUE", "NEW GAME", "MYSTERY GIFT", "OPTION"),
    3: ("CONTINUE", "NEW GAME", "MYSTERY GIFT", "MYSTERY EVENTS", "OPTION"),
}
#: src/start_menu.c sStartMenuItems, by MENU_ACTION_* (the PLAYER entry shows the player's name).
START_MENU_ACTIONS = ("POKéDEX", "POKéMON", "BAG", "POKéNAV", "PLAYER", "SAVE", "OPTION", "EXIT", "RETIRE",
                      "PLAYER", "REST", "RETIRE", "BAG")
#: include/item_menu.h: the pockets in `gBagPosition.pocket` order (ITEMS_POCKET ... KEYITEMS_POCKET).
BAG_POCKETS = ("items", "poke_balls", "tms_hms", "berries", "key_items")
#: Tasks that poll A or B themselves with NO text printer waiting, so the text-printer rule cannot see the
#: wait: each `func` and what it waits for (`gTasks[].func` names).
TASK_WAITS: dict[str, str] = {
    "Task_NewGameBirchSpeech_WaitPressBeforeNameChoice": "A or B",  # src/main_menu.c, after "...your name?"
    "Task_ReturnToItemListAfterItemPurchase": "A or B",  # src/shop.c, "Here you go! Thank you very much."
    "Task_ReturnToItemListAfterDecorationPurchase": "A or B",  # src/shop.c
    "Task_ViewClock_HandleInput": "A or B",  # src/wallclock.c (looking at a clock already set)
    "Task_WaitForBatteryDryErrorWindow": "A",  # src/main_menu.c (no RTC battery)
    "Task_WaitForSaveFileErrorWindow": "A",  # src/main_menu.c (a corrupted save)
}


def task_wait(tasks: Iterable[str]) -> str | None:
    """Which TASK waits for a button with no text printer waiting (`TASK_WAITS`), as a wait reason."""
    for name in sorted(tasks):
        if name in TASK_WAITS:
            return f"task {name} ({TASK_WAITS[name]})"
    return None


# --------------------------------------------------------------------------------------------- scenes
#: STEP 2.1 (the step-2 verifier: 530 frames of Birch's opening were logged under the catch-all "the game is
#: busy (main_menu)"). WHAT PLAYS while nothing takes input and nothing waits, in a person's words: the hands
#: name it whenever they stand still (`hands/dialogue.py` busy_reason). Measured 2026-10-07 on every stretch
#: the four step-2 skills stood still under the catch-all (`gates/live_step2.py` now fails a real run that logs
#: one). Looked up in this order: the main callback (`gMain.callback2`: the screen the game is on), then a task
#: (`gTasks[].func` name prefix), then the framework's game state.
#: By the main callback, its symbol name:
SCENE_CALLBACKS: dict[str, str] = {
    "NULL": "the game starting up",  # gMain.callback2 0: the first frames after power-on
    "CB2_InitCopyrightScreenAfterBootup": "the copyright screen",  # src/intro.c
    "CB2_NewGameBirchSpeech_ReturnFromNamingScreen": "Professor Birch's speech",  # src/main_menu.c
    "CB2_NewGame": "a new game loading",  # src/overworld.c (the truck's map is built)
    "CB2_InitBuyMenu": "the mart's item list",  # src/shop.c (opening)
    "CB2_BuyMenu": "the mart's item list",  # src/shop.c (its messages, closing)
    "CB2_StartWallClock": "the wall clock",  # src/wallclock.c (opening)
    "CB2_WallClock": "the wall clock",  # src/wallclock.c (fading in, the exit)
    "ReturnFromStartWallClock": "the wall clock",  # src/wallclock.c (closing)
    "CB2_ReturnToField": "the map loading",  # src/overworld.c (back from a full-screen menu)
    "CB2_ReturnToFieldLocal": "the map loading",
    "CB2_ReturnToFieldContinueScript": "the map loading",
    "CB2_ReturnToFieldContinueScriptPlayMapMusic": "the map loading",
    "CB2_ReturnToFieldFadeFromBlack": "the map loading",
    "CB2_LoadMap": "the map loading",
    "CB2_DoChangeMap": "the map loading",
}
#: By a task's name PREFIX (first match), when the callback names no scene:
SCENE_TASKS: tuple[tuple[str, str], ...] = (
    ("Task_NewGameBirchSpeech", "Professor Birch's speech"),  # src/main_menu.c: its timers, fades, slides
    ("Task_MainMenuCheck", "the main menu"),  # src/main_menu.c Task_MainMenuCheckSaveFile / ...CheckBattery
    ("Task_DisplayMainMenu", "the main menu"),
    ("Task_HandleMainMenuAPressed", "the main menu"),  # its fade out after NEW GAME
    ("Task_SetClock", "the wall clock"),  # src/wallclock.c: fading in, the exit
    ("Task_ExitBuyMenu", "the mart's item list"),  # src/shop.c
    ("Task_PokecenterHeal", "the nurse healing the party"),  # src/field_specials.c (the machine, the jingle)
)
#: By the framework's game state, last:
SCENE_STATES: dict[str, str] = {
    "TITLE_SCREEN": "the opening (the intro movie, the title screen)",
    "MAIN_MENU": "the main menu",
    "NAMING_SCREEN": "the naming keyboard",
    "BATTLE_STARTING": "a battle starting",
    "BATTLE_ENDING": "a battle ending",
    "EVOLUTION": "an evolution",
    "EGG_HATCH": "an egg hatching",
    "WHITEOUT": "the whiteout",
    "BAG_MENU": "the bag",
    "PARTY_MENU": "the party menu",
}


def scene_of(game_state: str, tasks: Iterable[str], callback: str | None) -> str | None:
    """What plays (`SCENE_CALLBACKS`, then `SCENE_TASKS`, then `SCENE_STATES`), or None. `callback` is the main
    callback's symbol name ("NULL" when it is 0), or None when no table entry matches it."""
    if callback is not None and callback in SCENE_CALLBACKS:
        return SCENE_CALLBACKS[callback]
    names = sorted(tasks)
    for prefix, words in SCENE_TASKS:
        if any(name.startswith(prefix) for name in names):
            return words
    return SCENE_STATES.get(game_state)


def _s8(value: int) -> int:
    return value - 256 if value >= 128 else value


def _u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "little")


def _s16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "little", signed=True)


def read_ui(game_state: str, tasks: Mapping[str, bytes], raw: Mapping[str, object]) -> MenuView | None:
    """The interactive thing on screen, from the active tasks (`func` name -> its 32 data bytes) and the raw
    reads the host made for it (`raw`, keys below). None when nothing on screen takes a menu input. Order:
    a whole-screen state first (naming, bag, party), then the task tables, most specific first."""
    if game_state == "NAMING_SCREEN" or "Task_NamingScreen" in tasks:
        naming = raw.get("naming")
        if isinstance(naming, dict):
            page = _PAGE_BY_ID[naming["page"]] if naming["page"] < len(_PAGE_BY_ID) else f"page{naming['page']}"
            enabled = naming["state"] == NAMING_STATE_HANDLE_INPUT and naming.get("input_enabled", False)
            return MenuView(kind="naming", page=page, cursor_xy=(naming["x"], naming["y"]), text=naming["text"],
                            max_chars=naming.get("max_chars"), accepts_input=enabled)
        return MenuView(kind="naming", accepts_input=False)
    if game_state == "BAG_MENU":
        bag = raw.get("bag")
        if isinstance(bag, dict):
            pocket = bag["pocket"]
            name = BAG_POCKETS[pocket] if pocket < len(BAG_POCKETS) else f"pocket{pocket}"
            return MenuView(kind="bag", pocket=name, cursor=bag["cursor"] + bag["scroll"])
        return MenuView(kind="bag", accepts_input=False)
    if game_state == "PARTY_MENU":
        slot = raw.get("party_slot")
        return MenuView(kind="party", cursor=slot if isinstance(slot, int) else None)
    menu = raw.get("menu")  # sMenu, 12 bytes
    for task, kind in sorted(UI_TASKS.items()):
        if task not in tasks:
            continue
        data = tasks[task]
        if kind in ("yes_no", "gender", "mart_menu", "multichoice") and isinstance(menu, (bytes, bytearray)):
            cursor = _s8(menu[2])
            if kind == "yes_no":
                options = YES_NO
                # src/script_menu.c Task_HandleYesNoInput ignores input until tRight (data[2]) reaches 5
                accepts = _s16(data, 4) >= 5 if task == "Task_HandleYesNoInput" else True
            elif kind == "gender":
                options, accepts = GENDER_OPTIONS, True
            elif kind == "mart_menu":
                options = SHOP_OPTIONS.get(int(raw.get("mart_type") or 0), SHOP_OPTIONS[0])
                accepts = True
            else:
                count = _s8(menu[4]) + 1
                names = raw.get("multichoice_options")
                options = tuple(names) if isinstance(names, (list, tuple)) and len(names) == count else ("",) * max(count, 0)
                accepts = not raw.get("multichoice_delay")
            return MenuView(kind=kind, options=options, cursor=cursor, accepts_input=accepts)
        if kind == "main_menu":
            menu_type = _s16(data, 0)
            options = MAIN_MENU_OPTIONS.get(menu_type, ())
            return MenuView(kind=kind, options=options, cursor=_s16(data, 2),
                            accepts_input=task == "Task_HandleMainMenuInput")
        if kind == "title":
            return MenuView(kind=kind, options=("PRESS START",), cursor=0)
        if kind == "clock":
            angle = _s16(data, 0)
            return MenuView(kind=kind, hours=_s16(data, 4), minutes=_s16(data, 6), accepts_input=angle % 6 == 0)
        if kind == "mart_buy":
            shop = raw.get("shop")
            names = raw.get("mart_items")
            if isinstance(shop, dict) and isinstance(names, (list, tuple)):
                prices = tuple(raw.get("mart_prices") or ())
                return MenuView(kind=kind, options=tuple(names) + ("CANCEL",), prices=prices,
                                cursor=shop["row"] + shop["scroll"])
            return MenuView(kind=kind, accepts_input=False)
        if kind == "mart_quantity":
            shop = raw.get("shop")
            max_quantity = shop["max_quantity"] if isinstance(shop, dict) else None
            return MenuView(kind=kind, quantity=_s16(data, 2), max_quantity=max_quantity)
        if kind == "start_menu":
            start = raw.get("start_menu")
            if isinstance(start, dict):
                actions = start["actions"]
                options = tuple(START_MENU_ACTIONS[a] if a < len(START_MENU_ACTIONS) else f"action{a}" for a in actions)
                return MenuView(kind=kind, options=options, cursor=start["cursor"])
            return MenuView(kind=kind, accepts_input=False)
    if game_state == "TITLE_SCREEN" and tasks:
        # The intro movie (src/intro.c MainCB2_Intro: any new key, once no palette fade runs, ends it) and the
        # title's first two phases (src/title_screen.c Task_TitleScreenPhase1/2: A, B, START or SELECT skips
        # the logo animation). The copyright screen before them runs no task.
        return MenuView(kind="intro_movie", options=("SKIP",), cursor=0)
    return None
