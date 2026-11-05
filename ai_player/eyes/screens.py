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

BUILD STEP 5 (the story): PROF. BIRCH's BAG, the STARTER choice (`src/starter_choose.c`): `Task_HandleStarterChooseInput` takes
A, Left and Right, its cursor is the task's own `tStarterSelection` (data[0]: 0 TREECKO, 1 TORCHIC, 2 MUDKIP, `sStarterMon`;
it starts on 1); while the cursor slides (`Task_MoveStarterChooseCursor`, `Task_CreateStarterLabel`) or a ball opens
(`Task_StarterChoose`, `Task_WaitForStarterSprite`, `Task_AskConfirmStarter`) the screen takes no input. "Do you choose this
POKéMON?" is a YES/NO made by `CreateYesNoMenu` and polled by `Task_HandleConfirmStarterInput` through
`Menu_ProcessInputNoWrapClearOnChoose`: the cursor in `sMenu`, as every other yes/no here.

R1 (the AI saves its game; build spec 2026-10-29, section 3 (a), E1-E6), each rule from the pinned decomp:
  * THE START MENU AND THE SAVE DIALOG: THE TASK DECIDES FIRST (`_start_menu_view`). `ShowStartMenu` makes a task that
    runs `StartMenuTask` while the menu is BUILT (`src/start_menu.c` CreateStartMenuTask / InitStartMenuStep) and then
    `Task_ShowStartMenu`, which on its first frame (data[0] 0) sets `gMenuCallback = HandleStartMenuInput` and from then on
    calls `gMenuCallback()` every frame (`:561-580`). The save dialog runs INSIDE that task: A on SAVE sets
    `gMenuCallback` to `StartMenuSaveCallback`, then `SaveStartCallback` (`InitSave`), then `SaveCallback`, which runs
    `sSaveDialogCallback` (`:721-729`, `:809-831`); its question callbacks `SaveConfirmInputCallback` and
    `SaveOverwriteInputCallback` poll the YES/NO through `sMenu` (`:984-1084`). NEITHER callback is ever cleared: a B on
    the menu leaves `gMenuCallback` at `HandleStartMenuInput` after the task is gone (`:629-634`), a NO leaves
    `sSaveDialogCallback` at an input callback (`:1024-1028`, `:1070-1074`), and a successful save leaves both. So a
    callback is read only while `Task_ShowStartMenu` runs and only once its data[0] is past 0, and the save callback only
    while `gMenuCallback` is `SaveCallback`: a stale value never reads as "takes input".
  * the save's YES/NO is its own kind, `save_yes_no`, never `yes_no`, so no scene's answer rule can answer it; every other
    frame of the dialog (a page printing, the write, "saved the game.") is a `save_dialog` that takes no input, its words
    the `text` (`host/eyes.py` _text, printer 0) and a paragraph's wait the text printer's own (`ScreenState.waits_for_button`).
    The one wait no printer shows: `SaveReturnErrorCallback` with `sSaveDialogTimer` at 0 polls `JOY_HELD(A_BUTTON)`
    (`SaveErrorTimer`, `:964-976`): `save_dialog_wait`.
  * THE MAIN MENU's ERROR PAGES (`src/main_menu.c:649-660`, `:723-737`) print on window 7 by printer 7
    (`CreateMainMenuErrorWindow`); while their task runs the page is printer 7's string (`ERROR_PAGE_TASKS`, `host/eyes.py`).
  * THE CONTINUE WINDOW's TIME: `MainMenu_FormatSavegameTime` draws `playTimeHours:playTimeMinutes` of the save the boot
    loaded (`:2147-2152`): the main menu's view carries it (`hours`, `minutes`) when it offers CONTINUE (tMenuType >= 1).

CHAPTER 5 (2026-11-05, the instructed-choice skill): THE POKéNAV's three menus (`pokenav_menu`, `pokenav_list`,
`pokenav_options`), the wait after a call (`pokenav_wait`) and its scene (`SCENE_CALLBACKS`): `POKENAV_INPUT_STATE` has the
decomp source. A GRID multichoice (`Task_HandleMultichoiceGridInput`) is its own kind, `multichoice_grid` (it was
`multichoice` until then): its cursor moves in 2-D.
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
    "ERROR_PAGE_PRINTER",
    "ERROR_PAGE_TASKS",
    "PARTY_MENU_ACTIONS",
    "GENDER_OPTIONS",
    "KEYBOARD_COLUMNS",
    "KEYBOARD_PAGES",
    "MAIN_MENU_OPTIONS",
    "MATCH_CALL_NAMES",
    "MATCH_CALL_OPTIONS",
    "NAMING_STATE_HANDLE_INPUT",
    "PARAGRAPH",
    "POKENAV_CALL_EXIT_HANDLER",
    "POKENAV_INPUT_STATE",
    "POKENAV_LIST_HANDLER",
    "POKENAV_MENU_HANDLERS",
    "POKENAV_MENU_OPTIONS",
    "POKENAV_OPTIONS_HANDLER",
    "SAVE_DIALOG_CALLBACKS",
    "SAVE_INPUT_CALLBACKS",
    "SAVE_MENU_CALLBACKS",
    "SCENE_CALLBACKS",
    "SCENE_STATES",
    "SCENE_TASKS",
    "SHOP_OPTIONS",
    "STARTER_OPTIONS",
    "START_MENU_ACTIONS",
    "TASK_WAITS",
    "UI_BUSY_TASKS",
    "UI_TASKS",
    "YES_NO",
    "decode_text",
    "encode_char",
    "key_position",
    "page_text",
    "pokenav_view",
    "pokenav_wait",
    "read_ui",
    "save_dialog_wait",
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
    # (chapter 5, the instructed-choice skill) a GRID of options (`src/script_menu.c` Task_HandleMultichoiceGridInput, the
    # Rustboro school's blackboard): its cursor moves in 2-D, so it is its own kind, never a list a 1-D cursor walks
    # (`skills/instructed.py` refuses it). Until 2026-11-05 it was reported as "multichoice".
    "Task_HandleMultichoiceGridInput": "multichoice_grid",
    "Task_ShopMenu": "mart_menu",  # src/shop.c (BUY / SELL / QUIT)
    "Task_BuyMenu": "mart_buy",  # src/shop.c (the item list)
    "Task_BuyHowManyDialogueHandleInput": "mart_quantity",  # src/shop.c ("How many?")
    "Task_SetClock_HandleInput": "clock",  # src/wallclock.c
    "StartMenuTask": "start_menu",  # src/start_menu.c (BUILDS the menu; R1: takes no input, `_start_menu_view`)
    "Task_ShowStartMenu": "start_menu",  # src/start_menu.c (R1: runs gMenuCallback: the menu's input, the save dialog)
    "Task_HandleMainMenuInput": "main_menu",  # src/main_menu.c
    "Task_HighlightSelectedMainMenuItem": "main_menu",
    "Task_TitleScreenPhase3": "title",  # src/title_screen.c: A or START goes to the main menu
    # BUILD STEP 5 (the module docstring): PROF. BIRCH's bag
    "Task_HandleStarterChooseInput": "choose_starter",  # src/starter_choose.c (tStarterSelection data[0])
    "Task_HandleConfirmStarterInput": "yes_no",  # src/starter_choose.c ("Do you choose this POKéMON?", sMenu)
}
#: BUILD STEP 5: the starter choice's options, left to right (`src/starter_choose.c` sStarterMon).
STARTER_OPTIONS = ("TREECKO", "TORCHIC", "MUDKIP")
#: STEP 2.1: tasks during which a menu STAYS ON SCREEN but takes no input, by the menu's kind. Found by the step-2
#: review's item 6 (a failed choice now ends the skill): moving the gender menu's cursor switches its task to a
#: sprite slide (`src/main_menu.c` Task_NewGameBirchSpeech_ChooseGender: `if (gender2 != tPlayerGender) ...
#: gTasks[taskId].func = Task_NewGameBirchSpeech_SlideOutOldGenderSprite`, then SlideInNewGenderSprite, then
#: back to ChooseGender), and the eyes reported the menu CLOSED: `move_cursor` gave up after its one Down, and the
#: intro's old loop chose again on its next turn and hid it (measured 2026-10-08, seed 3, frame ~5,370).
UI_BUSY_TASKS: dict[str, str] = {
    "Task_NewGameBirchSpeech_SlideOutOldGenderSprite": "gender",
    "Task_NewGameBirchSpeech_SlideInNewGenderSprite": "gender",
    # BUILD STEP 5: the bag's cursor sliding, a ball opening, the question being asked (`src/starter_choose.c`)
    "Task_StarterChoose": "choose_starter",
    "Task_MoveStarterChooseCursor": "choose_starter",
    "Task_CreateStarterLabel": "choose_starter",
    "Task_WaitForStarterSprite": "choose_starter",
    "Task_AskConfirmStarter": "choose_starter",
    "Task_DeclineStarter": "choose_starter",
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


#: R1 (module docstring): the main menu's error pages are printed by text printer 7 (`src/main_menu.c` CreateMainMenuErrorWindow:
#: `AddTextPrinterParameterized(7, ...)`), and these tasks wait on them (`Task_WaitForSaveFileErrorWindow`: "The save file has
#: been erased..." or "The save file is corrupted..."; `Task_WaitForBatteryDryErrorWindow`: "The internal battery has run dry").
ERROR_PAGE_TASKS = ("Task_WaitForSaveFileErrorWindow", "Task_WaitForBatteryDryErrorWindow")
ERROR_PAGE_PRINTER = 7
#: R1: the values of `gMenuCallback` the start menu's rule names (`src/start_menu.c`, every one a ROM function the symbol table
#: names; `host/eyes.py` resolves them ONCE with `get_symbol`, the thumb bit off). Any other value is "another callback" (an
#: item's fade, the Pokedex opening): the menu takes no input.
SAVE_MENU_CALLBACKS = ("HandleStartMenuInput", "StartMenuSaveCallback", "SaveStartCallback", "SaveCallback")
#: R1: the values of `sSaveDialogCallback` (`src/start_menu.c:937-1159`), read only while `gMenuCallback` is SaveCallback.
SAVE_DIALOG_CALLBACKS = ("SaveConfirmSaveCallback", "SaveYesNoCallback", "SaveConfirmInputCallback", "SaveFileExistsCallback",
                         "SaveConfirmOverwriteDefaultNoCallback", "SaveConfirmOverwriteCallback", "SaveOverwriteInputCallback",
                         "SaveSavingMessageCallback", "SaveDoSaveCallback", "SaveSuccessCallback",
                         "SaveReturnSuccessCallback", "SaveErrorCallback", "SaveReturnErrorCallback")
#: R1: the save dialog's callbacks that poll its YES/NO (`Menu_ProcessInputNoWrapClearOnChoose`, the cursor in `sMenu`).
SAVE_INPUT_CALLBACKS = ("SaveConfirmInputCallback", "SaveOverwriteInputCallback")


def save_dialog_wait(save_callback: str | None, timer: int | None) -> str | None:
    """R1: the one wait of the save dialog no text printer shows: after "Save error." has printed, `SaveReturnErrorCallback`
    counts `sSaveDialogTimer` down and then takes A HELD (`src/start_menu.c` SaveErrorTimer: `else if (JOY_HELD(A_BUTTON))`)."""
    if save_callback == "SaveReturnErrorCallback" and timer == 0:
        return "task Task_ShowStartMenu (A: the save error page, SaveReturnErrorCallback)"
    return None


def _start_menu_view(tasks: Mapping[str, bytes], raw: Mapping[str, object]) -> MenuView:
    """R1 (module docstring; build spec E1): the start menu and the save dialog, THE TASK DECIDING FIRST, then the callbacks:
      1. `StartMenuTask` runs (the menu is being built): the menu, taking no input, whatever `gMenuCallback` says;
      2. `Task_ShowStartMenu` on its first frame (data[0] 0, before it sets `gMenuCallback`): the same;
      3. `gMenuCallback` is `HandleStartMenuInput`: the menu, taking input;
      4. `StartMenuSaveCallback` or `SaveStartCallback` (the two frames before `InitSave`): a save_dialog, no input;
      5. `SaveCallback` with a question's input callback: `save_yes_no`, its cursor `sMenu`'s, taking input;
      6. `SaveCallback`, any other save callback: a save_dialog, no input (its words are the `text`);
      7. any other `gMenuCallback` (an item's fade): the menu, taking no input."""
    start = raw.get("start_menu")
    options: tuple[str, ...] = ()
    cursor = None
    if isinstance(start, dict):
        options = tuple(START_MENU_ACTIONS[a] if a < len(START_MENU_ACTIONS) else f"action{a}" for a in start["actions"])
        cursor = start["cursor"]
    menu_view = MenuView(kind="start_menu", options=options, cursor=cursor, accepts_input=False)
    if "StartMenuTask" in tasks or "Task_ShowStartMenu" not in tasks:
        return menu_view  # rule 1 (and a reader that saw neither task: never "takes input")
    if _s16(tasks["Task_ShowStartMenu"], 0) == 0:
        return menu_view  # rule 2
    callback = raw.get("menu_callback")
    if callback == "HandleStartMenuInput":
        return replace(menu_view, accepts_input=isinstance(start, dict))  # rule 3 (no options read: not "takes input")
    if callback in ("StartMenuSaveCallback", "SaveStartCallback"):
        return MenuView(kind="save_dialog", accepts_input=False)  # rule 4
    if callback == "SaveCallback":
        menu = raw.get("menu")
        if raw.get("save_callback") in SAVE_INPUT_CALLBACKS and isinstance(menu, (bytes, bytearray)):
            cursor = _s8(menu[2])
            return MenuView(kind="save_yes_no", options=YES_NO, cursor=cursor if cursor in (0, 1) else None)  # rule 5
        return MenuView(kind="save_dialog", accepts_input=False)  # rule 6
    return menu_view  # rule 7


# --------------------------------------------------------------------------------------------- the POKéNAV (chapter 5)
#: (chapter 5, 2026-11-05, the instructed-choice skill; the recon of the MATCH CALL tutorial, s53/ch5stops/menu) The POKéNAV
#: runs no menu task the tables above know: `Task_Pokenav` (`src/pokenav.c`) calls the CURRENT menu's handler every frame
#: while its state (data[0]) is 3, and runs a looped task (an animation, a list being built, a call's message) in its other
#: states, when no key is read. `host/eyes.py` follows `gPokenavResources` (EWRAM) to its substructs:
#:   1, MAIN_MENU_HANDLER (`src/pokenav_menu_handler.c` struct Pokenav_Menu: menuType u16 @0, cursorPos s16 @2, callback @0xC);
#:   5, MATCH_CALL_MAIN (`src/pokenav_match_call_list.c` struct Pokenav_MatchCallMenu: optionCursorPos u16 @0, maxOptionId
#:      u16 @2, matchCallOptions (ROM u8[]) @4, numRegistered u16 @0xA, callback @0x18, matchCallEntries[] @0x1C, each
#:      {isSpecialTrainer u8, mapSec u8, headerId u16});
#:   17, LIST (`src/pokenav_list.c` struct PokenavList: windowState @0x888 {windowTopIndex u16 @0, selectedIndexOffset u16 @6}).
#: Each handler is NAMED by the symbol table's reverse lookup (`get_symbol_name`): `HandleMainMenuInput` and
#: `HandleConditionMenuInput` are static functions in TWO files each (`src/main_menu.c` too), so the forward table cannot
#: name them. ONLY the kind, the options, the cursor and whether it takes input reach the brain, never a handler's name
#: (`...Tutorial` would tell a hidden mode).
POKENAV_INPUT_STATE = 3
#: `src/pokenav_menu_handler.c` sMenuItems, by menuType (DEFAULT, UNLOCK_MC, UNLOCK_MC_RIBBONS, CONDITION,
#: CONDITION_SEARCH), as the buttons' pictures read.
POKENAV_MENU_OPTIONS: dict[int, tuple[str, ...]] = {
    0: ("HOENN MAP", "CONDITION", "SWITCH OFF"),
    1: ("HOENN MAP", "CONDITION", "MATCH CALL", "SWITCH OFF"),
    2: ("HOENN MAP", "CONDITION", "MATCH CALL", "RIBBONS", "SWITCH OFF"),
    3: ("PARTY", "SEARCH", "CANCEL"),
    4: ("COOL", "BEAUTY", "CUTE", "SMART", "TOUGH", "CANCEL"),
}
#: The menu handlers that read the D-pad and A/B (`src/pokenav_menu_handler.c`; upper case, as `get_symbol_name` names
#: them). The tutorial's two (critic MENU-5): a build that knew only `HandleMainMenuInput` would see the whole tutorial
#: as "not taking input". Any other callback (`GetMenuId`, `CB2_ReturnToMainMenu`, ...) is a transition: no menu.
POKENAV_MENU_HANDLERS = frozenset({"HANDLEMAINMENUINPUT","HANDLEMAINMENUINPUTTUTORIAL",
                                   "HANDLEMAINMENUINPUTENDTUTORIAL", "HANDLECONDITIONMENUINPUT",
                                   "HANDLECONDITIONSEARCHMENUINPUT", "HANDLECANTOPENRIBBONSINPUT"})
#: `src/pokenav_match_call_list.c`: the list's handler, its CALL / CHECK / CANCEL list's, and the wait after a call.
POKENAV_LIST_HANDLER = "CB2_HANDLEMATCHCALLINPUT"
POKENAV_OPTIONS_HANDLER = "CB2_HANDLEMATCHCALLOPTIONSINPUT"
POKENAV_CALL_EXIT_HANDLER = "CB2_HANDLECALLEXITINPUT"
#: `include/pokenav.h` MATCH_CALL_OPTION_CALL 0, _CHECK 1, _CANCEL 2 (`src/strings.c` gText_Call, gText_Check, gText_Cancel6).
MATCH_CALL_OPTIONS = ("CALL", "CHECK", "CANCEL")
#: The NAME a MATCH CALL entry shows, by `include/pokenav.h` MC_HEADER_* (`src/pokenav_match_call_data.c` sMatchCallHeaders:
#: the `.name` strings of `src/strings.c`, e.g. gText_MrStoneMatchCallName "MR. STONE", gText_NormanMatchCallName "DAD";
#: a leader's `.name` is NULL and the list shows its trainer's name). The entry's description column ("DEVON PRES") is not
#: part of the name.
MATCH_CALL_NAMES = ("MR. STONE", "PROF. BIRCH", "BRENDAN", "MAY", "WALLY", "DAD", "MOM", "STEVEN", "SCOTT", "ROXANNE",
                    "BRAWLY", "WATTSON", "FLANNERY", "WINONA", "TATE&LIZA", "JUAN", "SIDNEY", "PHOEBE", "GLACIA",
                    "DRAKE", "WALLACE")


def pokenav_view(pokenav: object) -> MenuView | None:
    """(chapter 5) The POKéNAV's menu on screen, from `host/eyes.py`'s raw read (`raw["pokenav"]`: `state`, Task_Pokenav's
    data[0]; `menu` {type, cursor, handler}; `mc` {handler, option_cursor, options, entries, list_cursor}): the MATCH CALL
    list (`pokenav_list`, the cursor windowTopIndex + selectedIndexOffset), an entry's CALL / CHECK / CANCEL
    (`pokenav_options`, the cursor optionCursorPos) or a main / condition menu (`pokenav_menu`, the cursor cursorPos). It
    TAKES INPUT only while its handler is the current one AND `Task_Pokenav` reads keys (state 3). None while a call plays,
    after one (a wait: `pokenav_wait`), on a check page, the map or any transition."""
    if not isinstance(pokenav, dict):
        return None
    taking = pokenav.get("state") == POKENAV_INPUT_STATE
    mc = pokenav.get("mc")
    if isinstance(mc, dict):
        handler = mc.get("handler")
        if handler == POKENAV_LIST_HANDLER:
            names = tuple(mc.get("entries") or ())
            cursor = mc.get("list_cursor")
            valid = isinstance(cursor, int) and 0 <= cursor < len(names)
            return MenuView(kind="pokenav_list", options=names, cursor=cursor if valid else None,
                            accepts_input=taking and valid)
        if handler == POKENAV_OPTIONS_HANDLER:
            names = tuple(MATCH_CALL_OPTIONS[i] if 0 <= i < len(MATCH_CALL_OPTIONS) else f"option{i}"
                          for i in mc.get("options") or ())
            cursor = mc.get("option_cursor")
            valid = isinstance(cursor, int) and 0 <= cursor < len(names)
            return MenuView(kind="pokenav_options", options=names, cursor=cursor if valid else None,
                            accepts_input=taking and valid)
        return None
    menu = pokenav.get("menu")
    if isinstance(menu, dict) and menu.get("handler") in POKENAV_MENU_HANDLERS:
        options = POKENAV_MENU_OPTIONS.get(menu.get("type"), ())
        cursor = menu.get("cursor")
        valid = isinstance(cursor, int) and 0 <= cursor < len(options)
        return MenuView(kind="pokenav_menu", options=options, cursor=cursor if valid else None, accepts_input=taking and valid)
    return None


def pokenav_wait(pokenav: object) -> str | None:
    """(chapter 5, E5) The one POKéNAV wait no text printer shows: a call has ended (its last page printed) and
    `CB2_HandleCallExitInput` reads A or B (`src/pokenav_match_call_list.c`), while `Task_Pokenav` reads keys (state 3).
    Measured 2026-11-05: 830 frames of this screen were reported "not waiting" (f859067-f859897 of the recon)."""
    if not isinstance(pokenav, dict) or pokenav.get("state") != POKENAV_INPUT_STATE:
        return None
    mc = pokenav.get("mc")
    if isinstance(mc, dict) and mc.get("handler") == POKENAV_CALL_EXIT_HANDLER:
        return "task Task_Pokenav (A or B: the call has ended)"
    return None


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
    # BUILD STEP 5 (measured 2026-10-14, `probe_callbacks` from the chapter-1 sweep's RESCUED_BIRCH state: the frames the
    # play brain stood still on under the catch-all, 3 + 85 + 8 per run): the starter choice opening and closing, and
    # the first battle's own start (`src/starter_choose.c`, `src/battle_setup.c` CB2_GiveStarter / CB2_StartFirstBattle)
    "CB2_ChooseStarter": "the starter choice opening",
    "CB2_StarterChoose": "the starter choice",
    "CB2_GiveStarter": "the first battle starting",
    "CB2_StartFirstBattle": "the first battle starting",
    "CB2_SetUpReshowBattleScreenAfterMenu": "the battle coming back",  # src/battle_main.c / src/reshow_battle_screen.c
    "CB2_SetUpReshowBattleScreenAfterMenu2": "the battle coming back",
    "CB2_ReshowBattleScreenAfterMenu": "the battle coming back",  # src/reshow_battle_screen.c
    "ReshowBattleScreenAfterMenu": "the battle coming back",
    # (step 4.1, measured 2026-10-09 by the HEAL arm: one frame each named no scene, the hands' catch-all) a Potion's way
    # from the bag to the party menu and back to the battle (`src/party_menu.c`)
    "ChooseMonForInBattleItem": "the party menu opening (for an item)",
    "CB2_SetUpExitToBattleScreen": "the battle coming back",
    # (chapter 5, E6, 2026-11-05) the POKéNAV: opened by the MATCH CALL tutorial's script (`src/pokenav.c`
    # CB2_InitPokenavForTutorial), from the START menu (CB2_InitPokeNav) and running (CB2_Pokenav). Measured: 567 recon
    # records of the tutorial read scene None, so an unchanging POKéNAV frame got the unnamed stall allowance
    "CB2_InitPokenavForTutorial": "the POKéNAV",
    "CB2_InitPokeNav": "the POKéNAV",
    "CB2_Pokenav": "the POKéNAV",
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
    if "Task_Pokenav" in tasks:
        # (chapter 5) the POKéNAV's menus (`pokenav_view`): before 2026-11-05 the eyes saw nothing on these screens
        return pokenav_view(raw.get("pokenav"))
    menu = raw.get("menu")  # sMenu, 12 bytes
    for task, kind in sorted(UI_TASKS.items()):
        if task not in tasks:
            continue
        data = tasks[task]
        if kind == "choose_starter":
            # BUILD STEP 5: the bag's three balls, the cursor the task's tStarterSelection (data[0])
            cursor = _s16(data, 0)
            return MenuView(kind=kind, options=STARTER_OPTIONS,
                            cursor=cursor if 0 <= cursor < len(STARTER_OPTIONS) else None)
        if kind in ("yes_no", "gender", "mart_menu", "multichoice", "multichoice_grid") and isinstance(menu, (bytes, bytearray)):
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
            # R1 (E6): the CONTINUE window's TIME, when the menu offers CONTINUE (tMenuType >= 1): `host/eyes.py` reads
            # SaveBlock2's playTimeHours / playTimeMinutes, the two fields `MainMenu_FormatSavegameTime` draws
            saved = raw.get("save_time") if menu_type >= 1 else None
            hours, minutes = saved if isinstance(saved, tuple) and len(saved) == 2 else (None, None)
            return MenuView(kind=kind, options=options, cursor=_s16(data, 2),
                            accepts_input=task == "Task_HandleMainMenuInput", hours=hours, minutes=minutes)
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
            return _start_menu_view(tasks, raw)  # R1: the task decides first, then the callbacks (E1)
    for task, kind in sorted(UI_BUSY_TASKS.items()):  # STEP 2.1: on screen, not taking input
        if task in tasks:
            if kind == "choose_starter":  # BUILD STEP 5: the same task, its cursor in its own data[0]
                cursor = _s16(tasks[task], 0)
                return MenuView(kind=kind, options=STARTER_OPTIONS,
                                cursor=cursor if 0 <= cursor < len(STARTER_OPTIONS) else None, accepts_input=False)
            cursor = _s8(menu[2]) if isinstance(menu, (bytes, bytearray)) else None
            return MenuView(kind=kind, options=GENDER_OPTIONS if kind == "gender" else (), cursor=cursor, accepts_input=False)
    if game_state == "TITLE_SCREEN" and tasks:
        # The intro movie (src/intro.c MainCB2_Intro: any new key, once no palette fade runs, ends it) and the
        # title's first two phases (src/title_screen.c Task_TitleScreenPhase1/2: A, B, START or SELECT skips
        # the logo animation). The copyright screen before them runs no task.
        return MenuView(kind="intro_movie", options=("SKIP",), cursor=0)
    return None
