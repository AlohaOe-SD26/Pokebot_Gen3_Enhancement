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
    `gPartyMenu.slotId` @9;
  * BUILD STEP 3, the battle's ACTION menu (FIGHT / BAG / POKéMON / RUN): a battle runs no task for it; the
    player's battle CONTROLLER does (`src/battle_controller_player.c`: `gBattlerControllerFuncs[battler]` is
    `HandleInputChooseAction` while the menu takes input), and its cursor is `gActionSelectionCursor[battler]`
    (a 2 x 2 grid: bit 0 the column, bit 1 the row; HandleInputChooseAction: Left/Right toggle bit 0 only from
    the other column, Up/Down bit 1 only from the other row). Measured 2026-10-08 on `oldale.ss1` (a wild
    battle): the function is HandleInputChooseAction from the first frame the menu is drawn, the cursor 0 ->
    Right 1 -> Down 3 (RUN), A, "Got away safely!".

BUILD STEP 4 (the AI's own battles), each recognised by what RUNS its input, as the game itself does:
  * the MOVE menu (FIGHT's 2 x 2 grid of the battler's moves): `gBattlerControllerFuncs[0]` is `HandleInputChooseMove`
    (`src/battle_controller_player.c`), its cursor `gMoveSelectionCursor[0]` (bit 0 the column, bit 1 the row; a move slot
    with no move is skipped by the D-pad, `gNumberOfMovesToChoose`);
  * the battle's YES/NO box (`battle_yes_no`, opens on YES unless said): (a) a BATTLE SCRIPT command polling it, by the
    opcode at `gBattlescriptCurrInstr` and that command's own state (`src/battle_script_commands.c`: `yesnobox` 0x67 and
    `trygivecaughtmonnick` 0xF3 take input in gBattleCommunication[0] == 1; `yesnoboxlearnmove` 0x5A and
    `yesnoboxstoplearningmove` 0x5B in gBattleScripting.learnMoveState == 1), cursor gBattleCommunication[1]: "Use next
    POKéMON?", "... is about to use ... Will PLAYER change POKéMON?", "Delete a move to make room for ...?", "Stop learning
    ...?", "Give a nickname to the captured ...?"; (b) the player CONTROLLER's `PlayerHandleYesNoInput` (opens on NO), cursor
    `gMultiUsePlayerCursor`; (c) the EVOLUTION scene's learn-a-move question (`src/evolution_scene.c` Task_EvolutionScene,
    tState EVOSTATE_REPLACE_MOVE 22 and tLearnMoveState MVSTATE_HANDLE_YES_NO 4), cursor gBattleCommunication[1];
    the question is the message on screen (`ScreenState.text`, `gDisplayedStringBattle`);
  * the level-up STATS BOX waits for any key (`Cmd_drawlvlupbox` 0x6C, drawlvlupboxState 6 and 8: `if (gMain.newKeys != 0)`):
    a WAIT, not a menu (`BATTLE_SCRIPT_WAITS`): step 3's known limit "a level-up's stats box is not read as a wait";
  * the summary screen's FORGET-A-MOVE list (`move_forget`, `src/pokemon_summary_screen.c` Task_HandleReplaceMoveInput):
    the four moves and the new one (`sMonSummaryScreen->summary.moves` @0x84, `newMove` @0x40C4), the cursor
    `firstMoveIndex` @0x40C6 (Up/Down wrap through all five; A forgets the one under the cursor, the fifth keeps them all);
  * the party menu's ACTION list after a Pokemon is chosen (`party_action`, `src/party_menu.c`
    Task_HandleSelectionMenuInput): `sPartyMenuInternal->actions[numActions]` (@0xF, @0x17) named by `PARTY_MENU_ACTIONS`,
    the cursor in `sMenu`; the party menu takes input only while `Task_HandleChooseMonInput` runs;
  * the bag's pocket LIST (the open pocket's items in order, then CLOSE BAG) and its USE / CANCEL list (`bag_action`,
    `src/item_menu.c` Task_ItemContext_SingleRow / MultipleRows: `gBagMenu->contextMenuItemsPtr` @0x820 and
    `contextMenuNumItems` @0x828, named by `BAG_MENU_ACTIONS`, the cursor in `sMenu`); the list takes input while
    `Task_BagMenu_HandleInput` runs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace

from ai_player.eyes.observation import MenuView

__all__ = [
    "BAG_MENU_ACTIONS",
    "BAG_POCKETS",
    "BATTLE_ACTIONS",
    "BATTLE_SCRIPT_WAITS",
    "BATTLE_YES_NO_OPCODES",
    "CHARMAP",
    "CLOSE_BAG",
    "PARTY_MENU_ACTIONS",
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
    "UI_BUSY_TASKS",
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
#: STEP 2.1: tasks during which a menu STAYS ON SCREEN but takes no input, by the menu's kind. Found by the step-2
#: review's item 6 (a failed choice now ends the skill): moving the gender menu's cursor switches its task to a
#: sprite slide (`src/main_menu.c` Task_NewGameBirchSpeech_ChooseGender: `if (gender2 != tPlayerGender) ...
#: gTasks[taskId].func = Task_NewGameBirchSpeech_SlideOutOldGenderSprite`, then SlideInNewGenderSprite, then
#: back to ChooseGender), and the eyes reported the menu CLOSED: `move_cursor` gave up after its one Down, and the
#: intro's old loop chose again on its next turn and hid it (measured 2026-10-08, seed 3, frame ~5,370).
UI_BUSY_TASKS: dict[str, str] = {
    "Task_NewGameBirchSpeech_SlideOutOldGenderSprite": "gender",
    "Task_NewGameBirchSpeech_SlideInNewGenderSprite": "gender",
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
#: BUILD STEP 3: the battle's action menu, by `gActionSelectionCursor` (`src/battle_controller_player.c`
#: HandleInputChooseAction: B_ACTION_USE_MOVE 0 top-left, B_ACTION_USE_ITEM 1 top-right, B_ACTION_SWITCH 2
#: bottom-left, B_ACTION_RUN 3 bottom-right; `src/battle_bg.c` sText_... "FIGHT", "BAG", "POKéMON", "RUN").
BATTLE_ACTIONS = ("FIGHT", "BAG", "POKéMON", "RUN")
#: BUILD STEP 4: the battle-script commands that poll the battle's yes/no box, by opcode
#: (`include/constants/battle_script_commands.h`), and the state in which each takes input (module docstring).
BATTLE_YES_NO_OPCODES: dict[int, str] = {
    0x5A: "yesnoboxlearnmove",  # gBattleScripting.learnMoveState == 1
    0x5B: "yesnoboxstoplearningmove",  # gBattleScripting.learnMoveState == 1
    0x67: "yesnobox",  # gBattleCommunication[MULTIUSE_STATE] == 1
    0xF3: "trygivecaughtmonnick",  # gBattleCommunication[MULTIUSE_STATE] == 1
}
#: BUILD STEP 4: battle-script commands that wait for a key with no text printer waiting: opcode -> (the states of the
#: command that wait, what waits). `Cmd_drawlvlupbox` (0x6C): states 6 and 8 wait `if (gMain.newKeys != 0)` (page 1
#: and page 2 of the level-up stats box).
BATTLE_SCRIPT_WAITS: dict[int, tuple[tuple[int, ...], str]] = {
    0x6C: ((6, 8), "battle level-up stats box (any key)"),
}
#: BUILD STEP 4: `src/party_menu.c` enum MENU_* -> `sCursorOptions[].text` (`src/strings.c`): the party menu's action
#: list; MENU_FIELD_MOVES (19) + FIELD_MOVE_* -> the field move's name.
PARTY_MENU_ACTIONS: tuple[str, ...] = (
    "SUMMARY", "SWITCH", "CANCEL", "ITEM", "GIVE", "TAKE", "MAIL", "TAKE", "READ", "CANCEL", "SHIFT", "SEND OUT",
    "ENTER", "NO ENTRY", "STORE", "REGISTER", "TRADE", "TRADE", "TOSS",
    "CUT", "FLASH", "ROCK SMASH", "STRENGTH", "SURF", "FLY", "DIVE", "WATERFALL", "TELEPORT", "DIG", "SECRET POWER",
    "MILK DRINK", "SOFTBOILED", "SWEET SCENT",
)
#: BUILD STEP 4: `src/item_menu.c` enum ACTION_* -> `sItemMenuActions[].text`: the bag's item action list (in a battle,
#: `sContextMenuItems_BattleUse` = USE (ACTION_BATTLE_USE), CANCEL).
BAG_MENU_ACTIONS: tuple[str, ...] = ("USE", "TOSS", "REGISTER", "GIVE", "CANCEL", "USE", "CHECK", "WALK", "DESELECT",
                                     "CHECK TAG", "CONFIRM", "SHOW", "GIVE", "CONFIRM", "")
#: The bag list's last row (`gText_CloseBag`).
CLOSE_BAG = "CLOSE BAG"
#: Tasks that poll A or B themselves with NO text printer waiting, so the text-printer rule cannot see the
#: wait: each `func` and what it waits for (`gTasks[].func` names).
TASK_WAITS: dict[str, str] = {
    "Task_NewGameBirchSpeech_WaitPressBeforeNameChoice": "A or B",  # src/main_menu.c, after "...your name?"
    "Task_ReturnToItemListAfterItemPurchase": "A or B",  # src/shop.c, "Here you go! Thank you very much."
    "Task_ReturnToItemListAfterDecorationPurchase": "A or B",  # src/shop.c
    "Task_ViewClock_HandleInput": "A or B",  # src/wallclock.c (looking at a clock already set)
    "Task_WaitForBatteryDryErrorWindow": "A",  # src/main_menu.c (no RTC battery)
    "Task_WaitForSaveFileErrorWindow": "A",  # src/main_menu.c (a corrupted save)
    # BUILD STEP 4: after a catch of a species new to the Pokedex, the battle shows its Pokedex page
    # (`Cmd_displaydexinfo` -> DisplayCaughtMonDexPage) and waits `if (JOY_NEW(A_BUTTON | B_BUTTON))`
    "Task_HandleCaughtMonPageInput": "A or B",  # src/pokedex.c
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
    # BUILD STEP 3 (flee.py): a battle's own animations (a Pokemon sent out, the healthboxes sliding in) run with
    # nothing the eyes report changing for up to ~80 frames (measured 2026-10-08 on `oldale.ss1`); named, so the
    # hands' stall detector gives a battle the named-scene allowance and the busy reason is never the catch-all.
    "BattleMainCB2": "a battle",  # src/battle_main.c (gMain.callback2 for the whole battle)
    # BUILD STEP 4 (measured 2026-10-08: the callbacks the battle brain stood still on under the catch-all, a ball thrown
    # from the bag on `oldale.ss1`): the bag opening, and the battle drawn again after a menu
    "CB2_Bag": "the bag",  # src/item_menu.c (setting the bag up)
    "CB2_InitPartyMenu": "the party menu opening",  # src/party_menu.c (measured 2026-10-08: a switch on Route 116)
    "CB2_SetUpReshowBattleScreenAfterMenu": "the battle coming back",  # src/battle_main.c / src/reshow_battle_screen.c
    "CB2_SetUpReshowBattleScreenAfterMenu2": "the battle coming back",
    "CB2_ReshowBattleScreenAfterMenu": "the battle coming back",  # src/reshow_battle_screen.c
    "ReshowBattleScreenAfterMenu": "the battle coming back",
    # (step 4.1, measured 2026-10-09 by the HEAL arm: one frame each named no scene, the hands' catch-all) a Potion's way
    # from the bag to the party menu and back to the battle (`src/party_menu.c`)
    "ChooseMonForInBattleItem": "the party menu opening (for an item)",
    "CB2_SetUpExitToBattleScreen": "the battle coming back",
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
    "POKEMON_SUMMARY_SCREEN": "the summary screen",  # build step 4 (a move to forget is chosen there)
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
    a whole-screen state first (naming, bag, party), then the task tables, most specific first.

    STEP 2.1 (the step-2 review, item 4): while a palette fade RUNS (`raw["fading"]`, `gPaletteFade.active`) NOTHING
    on screen takes input (`accepts_input` False), whatever its own rule says. The decomp: the intro movie ends on a
    key only `if (gMain.newKeys != 0 && !gPaletteFade.active)` (`src/intro.c` MainCB2_Intro); while the title screen
    fades in, `CB2_InitTitleScreen` runs no task at all, so its logo task cannot see a key (`src/title_screen.c`,
    state 5: `if (!UpdatePaletteFade())`); the main menu, the naming keyboard, the shop and the wall clock each start
    taking input only `if (!gPaletteFade.active)` (`src/main_menu.c`, `src/naming_screen.c`, `src/shop.c`,
    `src/wallclock.c`). A press the game drops is not a press a person makes on purpose: measured 2026-10-08, the
    intro's FIRST Start (seed 3, frame 211) was pressed on a look that said "intro_movie, fading". Measured on the
    four step-2 skills (seed 3): a menu was on screen during a fade only as the intro movie (2 looks), the title (1)
    and the naming keyboard (35, already not taking input), so the rule moves nothing else."""
    ui = _read_ui(game_state, tasks, raw)
    if ui is not None and ui.accepts_input and raw.get("fading"):
        return replace(ui, accepts_input=False)
    return ui


def _read_ui(game_state: str, tasks: Mapping[str, bytes], raw: Mapping[str, object]) -> MenuView | None:
    """`read_ui` before its fade rule: what each menu's own input rule says."""
    action = raw.get("battle_action")  # BUILD STEP 3: the battle's action menu (module docstring)
    if isinstance(action, dict) and action.get("choosing"):
        cursor = action.get("cursor")
        return MenuView(kind="battle_action", options=BATTLE_ACTIONS,
                        cursor=cursor if isinstance(cursor, int) and 0 <= cursor < len(BATTLE_ACTIONS) else None,
                        battler=action.get("battler"))
    # BUILD STEP 4 (module docstring): the move grid, its TARGET choice (a double battle), the battle's yes/no box (a
    # battle script's, the controller's or the evolution scene's), the summary screen's forget-a-move list, the party
    # menu's and the bag's action lists
    move = raw.get("battle_move")
    if isinstance(move, dict) and move.get("choosing"):
        names = tuple(move.get("moves") or ())
        cursor = move.get("cursor")
        return MenuView(kind="battle_move", options=names,
                        cursor=cursor if isinstance(cursor, int) and 0 <= cursor < len(names) else None,
                        battler=move.get("battler"))
    target = raw.get("battle_target")
    if isinstance(target, dict) and target.get("choosing"):
        # a double battle's target: the cursor is a battler POSITION (0 the player's left, 1 the foe's left, 2 the
        # player's right, 3 the foe's right), the options the species standing there (`src/battle_controller_player.c`
        # HandleInputChooseTarget: Left/Up and Right/Down step through sTargetIdentities, skipping the absent)
        names = tuple(target.get("names") or ())
        cursor = target.get("cursor")
        return MenuView(kind="battle_target", options=names,
                        cursor=cursor if isinstance(cursor, int) and 0 <= cursor < len(names) else None,
                        battler=target.get("battler"))
    yes_no = raw.get("battle_yes_no")
    if isinstance(yes_no, dict) and yes_no.get("open"):
        cursor = yes_no.get("cursor")
        return MenuView(kind="battle_yes_no", options=YES_NO, cursor=cursor if cursor in (0, 1) else None,
                        accepts_input=bool(yes_no.get("accepts", True)))
    forget = raw.get("move_forget")
    if isinstance(forget, dict):
        names = tuple(forget.get("moves") or ())
        cursor = forget.get("cursor")
        return MenuView(kind="move_forget", options=names,
                        cursor=cursor if isinstance(cursor, int) and 0 <= cursor < len(names) else None,
                        accepts_input=bool(forget.get("accepts", True)))
    party_action = raw.get("party_action")
    if isinstance(party_action, dict) and isinstance(raw.get("menu"), (bytes, bytearray)):
        names = tuple(PARTY_MENU_ACTIONS[a] if 0 <= a < len(PARTY_MENU_ACTIONS) else f"action{a}"
                      for a in party_action.get("actions") or ())
        cursor = _s8(raw["menu"][2])
        return MenuView(kind="party_action", options=names, cursor=cursor if 0 <= cursor < len(names) else None)
    bag_action = raw.get("bag_action")
    if isinstance(bag_action, dict) and isinstance(raw.get("menu"), (bytes, bytearray)):
        names = tuple(BAG_MENU_ACTIONS[a] if 0 <= a < len(BAG_MENU_ACTIONS) else f"action{a}"
                      for a in bag_action.get("actions") or ())
        cursor = _s8(raw["menu"][2])
        return MenuView(kind="bag_action", options=names, cursor=cursor if 0 <= cursor < len(names) else None)
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
            # BUILD STEP 4: the open pocket's list as shown (its items, then CLOSE BAG), and input only while the list's
            # task runs (a pocket switching, a message or the action list take it away). Without the item names (an
            # earlier reader), as before.
            items = bag.get("items")
            options = tuple(items) + (CLOSE_BAG,) if isinstance(items, (list, tuple)) else ()
            accepts = "Task_BagMenu_HandleInput" in tasks if "items" in bag else True
            return MenuView(kind="bag", pocket=name, cursor=bag["cursor"] + bag["scroll"], options=options,
                            accepts_input=accepts)
        return MenuView(kind="bag", accepts_input=False)
    if game_state == "PARTY_MENU":
        slot = raw.get("party_slot")
        # BUILD STEP 4: the party list takes input only while `Task_HandleChooseMonInput` runs (`src/party_menu.c`); a
        # message ("Choose a POKéMON.", "... is already in battle!") or the action list take it away. Measured only for
        # the battle's party menu; a reader without the task list sees it as before (taking input).
        accepts = "Task_HandleChooseMonInput" in tasks if raw.get("party_tasks_known") else True
        return MenuView(kind="party", cursor=slot if isinstance(slot, int) else None, accepts_input=accepts)
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
    for task, kind in sorted(UI_BUSY_TASKS.items()):  # STEP 2.1: on screen, not taking input
        if task in tasks:
            cursor = _s8(menu[2]) if isinstance(menu, (bytes, bytearray)) else None
            return MenuView(kind=kind, options=GENDER_OPTIONS if kind == "gender" else (), cursor=cursor, accepts_input=False)
    if game_state == "TITLE_SCREEN" and tasks:
        # The intro movie (src/intro.c MainCB2_Intro: any new key, once no palette fade runs, ends it) and the
        # title's first two phases (src/title_screen.c Task_TitleScreenPhase1/2: A, B, START or SELECT skips
        # the logo animation). The copyright screen before them runs no task.
        return MenuView(kind="intro_movie", options=("SKIP",), cursor=0)
    return None
