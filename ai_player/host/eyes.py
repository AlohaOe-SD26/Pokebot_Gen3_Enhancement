"""The AI's EYES, framework half: the ONLY file where the AI reads the game (build step 1).

WHY A HOST FILE (RULING 37 Q1; design draft §2.1): the brain is framework-free and sees the game only
through the abstract `Eyes` interface (`ai_player/mode.py`). This class implements it on top of the
framework's MEMORY READS, through the read-only doors `gates/check_purity.py` lists for this file and
for no other (each door says what it reads and why it cannot act). A standalone build replaces this
one file; the vocabulary (`eyes/observation.py`) and the perception rules (`eyes/view.py`) stay.

WHAT EACH LOOK DOES, AND WHY THIS WAY
  * one frame, one snapshot: `look()` reads everything it reports between two frames and returns a
    frozen `Observation` stamped with the emulator's frame counter. It never advances, peeks at or
    rewinds a frame, and never writes: the party is decoded by the AI's own `eyes/party.py` from the
    raw `gPlayerParty` bytes instead of through the framework's `get_party()`, because `get_party()`
    LOOKS AHEAD a frame (`peek_frame`) when it meets a half-written party, and keeps a telemetry tally.
    A person cannot look into the next frame; a torn party read is reported in `problems`, and the AI
    looks again next time;
  * the tiles come from the game's LIVE grid, `gBackupMapLayout` (the map plus a 7-tile margin that
    holds the neighbouring maps): the very grid the camera draws and the player walks on, so a
    door a script opened (`setmetatile`) or the next route across a map edge is seen as it is
    on screen. The framework's `MapLocation` reads the ROM's original layout instead;
  * only what is ON SCREEN is reported: tiles of the 15 x 11 window, objects and signs inside it
    (`eyes/view.py` derives the window from the decomp; `gates/live_step1.py` arm GEO measures it).
    Objects the game keeps loaded off screen and hidden items are left out. The FAULT switch
    `AI_PLAYER_FAULT_NO_CROP` (crop=False) turns the crop off, so a test can prove it is load-bearing;
  * ROM data (tileset attributes, the tile-flag table, a map's signs) never changes, so it
    is read once per tileset or map and kept; everything that lives in RAM is read every look;
  * "waits for a button" reads all 32 text printers and `gTextFlags` (`eyes/view.py` text_printer_wait
    has the decomp's rule), and says WHY in `ScreenState.wait_reason`.

STEP 1.1 (the step-1 adversarial review), each rule in `eyes/view.py` with its reason:
  * PERCEPTION LIKE A PERSON: the foe's HP is its HP BAR (`hp_bar_pixels`), its moves only those it
    has used this battle (`foe_move_seen`), every overworld person is an "npc", and the player's id and
    every OT id are the VISIBLE 16 bits (`visible_id`): the secret id is never reported;
  * A WARP SETTLES before the position is reported (`settled_position`): the player object's tile and
    save block 1's `pos` must agree, or the position is unknown (None) and there is no view;
  * the party is None when it was not read (a torn slot makes the WHOLE party None: a party short of
    one Pokemon would read as a Pokemon gone), and () when the player has none;
  * the PC boxes are read every look (`Observation.storage`: PID and visible OT id from each box
    Pokemon's unencrypted header), so a catch sent to a box is seen by identity;
  * a foe battler is reported only if it belongs to THIS battle's enemy party, by PID (`_battle`): for
    the first frames of a battle `gBattleMons` still holds the previous battle's;
  * found by the step-1.1 live arms: while `gMain.vblankCallback` is NULL the save blocks may be moving
    (`_save_blocks_may_be_moving`), and a read there can be torn, so the save-block parts are not read.

BUILD STEP 2 (the hands), each rule in `eyes/screens.py` with its decomp source:
  * every active task's DATA is read with its name, and the open MENU and its cursor are reported
    (`ScreenState.ui`, a `MenuView`): yes/no, the gender menu, multichoice, the main and start menus, the
    mart's menu, item list and "How many?", the naming keyboard, the wall clock, the bag, the party menu, the
    title and the intro movie; the bytes a menu needs are read only while ITS input task runs;
  * a TASK that polls A/B with no text printer waiting is a wait too (`eyes/screens.py` TASK_WAITS: the
    "What's your name?" pause, the mart's "Here you go!"), so the hands can gate on it;
  * the TEXT on screen (`ScreenState.text`), decoded by the AI's own charmap; whether a script runs and the
    field controls are locked (`script_running`, `controls_locked`: an A then is not "start talking");
  * ‼ every pointer the eyes FOLLOW is range-checked first (`_rom_bytes`, `_ewram_bytes`): the framework's
    `read_bytes` does not bound a cartridge read, and a garbage pointer there killed the process.

BUILD STEP 3 (the world model and the navigator), READ ONLY: the doors of steps 1 and 2, plus ONE new read-only door,
`modules.game.get_symbol_name` (a dict lookup by address; the gate's door says why `get_symbol` cannot do it), used
only for the first point below:
  * in a battle, the ACTION menu (FIGHT / BAG / POKéMON / RUN) and its cursor (`_battle_action`:
    `gBattlerControllerFuncs[0]` NAMED by the symbol table through the new door, `gActionSelectionCursor[0]`), so the
    AI's own flee skill can choose RUN by reading the cursor (`eyes/screens.py` has the decomp source);
  * each party Pokemon's total EXPERIENCE (`MonSummary.experience`, the growth substructure @4 of the bytes `_party`
    already decodes: no new read), so the navigator's progress counts experience gained (design draft §10.4);
  * under the FAULT switch `AI_PLAYER_FAULT_NO_CROP` the view now holds EVERY tile of the live grid (the map
    and its margin), not only the 15 x 11 window: the CROP arm of `gates/live_step3.py` gives the navigator
    tiles a person could not see and shows its behaviour change. On the happy path the window is unchanged.

BUILD STEP 3.1 (the step-3 review's finding 5), ONE READ LESS: a tile's `warp` is now how it LOOKS (`eyes/view.py`
EXIT_BEHAVIORS), and the map's warp-event table is no longer read here (it was the only source of `warp`, and nothing on
screen shows it). The table is read on the TEST side only (`gates/live_step3.py` arm EXITS, `gates/probe_eyes.py`). Its
guard (the step-3.1 verifier's second round) is behavioural too: `gates/warp_reads.py` (arm WARPREAD) records every read
these eyes make and checks none touches any map's warp array, whatever the code that asked for it looks like.

BUILD STEP 4 (the AI's own battles), READ ONLY, no new door (the doors of steps 1-3; `eyes/screens.py` has the decomp
source of every rule):
  * the MOVE grid, the TARGET choice of a double battle and the battle's YES/NO (`_battle_menus`: the controller function
    of the battler whose turn it is, NAMED through `get_symbol_name`, and its cursor byte), for each battler at its
    POSITION (0 and 2 in a double battle, from `gBattlersCount`);
  * a battle-script command that waits for a key with no text printer waiting (`_battle_script_opcode`, `_battle_wait`:
    the level-up stats box) and the evolution scene's and the summary screen's move-forget states (`_evolution_yes_no`,
    `_move_forget`), so every press in a battle has its gate;
  * the bag's ITEM LIST by pocket and the party menu's action list (`_pocket_items`, `_bag_actions`, `_party_actions`),
    read only while their input task runs; a party Pokemon's five STATS (`MonSummary.stats`, bytes 90-98 of the party
    record `_party` already reads) and each battler's PID and position (`BattleMon.pid`, `.battler`).

COST: `gates/live_step1.py` and `gates/test_eyes.py` measure `cost_ms` (it is in every Observation).
"""

from __future__ import annotations

import time

from modules.battle_state import battle_is_active, get_battle_state
from modules.context import context
from modules.game import get_symbol, get_symbol_name
from modules.items import get_item_bag
from modules.map import get_map_data_for_current_position, get_map_objects
from modules.map_data import get_map_enum
from modules.memory import get_event_flag, get_game_state, read_symbol
from modules.player import get_player
from modules.pokedex import get_pokedex
from modules.pokemon import get_move_by_index, get_species_by_index
from modules.tasks import get_global_script_context, get_tasks

from ai_player.eyes.observation import (
    BagSummary,
    BattleMon,
    BattleView,
    MonSummary,
    MoveSlot,
    Observation,
    PlayerState,
    Progress,
    ScreenState,
    SeenObject,
    StoredMon,
    Tile,
    View,
)
from ai_player.eyes.screens import (
    BATTLE_SCRIPT_WAITS,
    BATTLE_YES_NO_OPCODES,
    SCENE_CALLBACKS,
    decode_text,
    read_ui,
    scene_of,
    task_wait,
)
from ai_player.eyes.view import (
    BADGE_FLAGS,
    DOOR_BEHAVIORS,
    EXIT_BEHAVIORS,
    LEDGE_DIRECTIONS,
    SCRIPT_CONTEXT_SHUTDOWN,
    STORY_FLAGS,
    TALL_GRASS_BEHAVIORS,
    TEXT_PRINTER_COUNT,
    TEXT_PRINTER_WAIT_STATES,
    TILE_FLAG_HAS_ENCOUNTERS,
    TILE_FLAG_SURFABLE,
    VIEW_DOWN,
    VIEW_HALF_WIDTH,
    VIEW_UP,
    behavior_name,
    classify_screen,
    facing_name,
    foe_move_seen,
    hp_bar_pixels,
    in_view,
    movement_mode,
    object_kind,
    script_waits_for_button,
    settled_position,
    status_name,
    text_printer_wait,
    visible_id,
)
from ai_player.eyes.party import PARTY_MON_SIZE, decode_party_mon, present_pids
from ai_player.host.attribution import seal_module

__all__ = ["MAP_OFFSET", "FrameworkEyes"]

#: The virtual map's margin around the real map (`include/fieldmap.h` MAP_OFFSET).
MAP_OFFSET = 7
#: `include/fieldmap.h` NUM_METATILES_IN_PRIMARY / NUM_METATILES_TOTAL.
METATILES_IN_PRIMARY = 512
METATILES_TOTAL = 1024
#: `include/global.fieldmap.h`: a grid block's metatile id, collision and elevation bits, and the
#: "undefined" block outside the grid.
MAPGRID_METATILE_ID_MASK = 0x03FF
MAPGRID_UNDEFINED = 0x03FF
#: A behaviour value outside every tileset (`GetMetatileAttributesById` returns MB_INVALID).
MB_INVALID = 0xFF
#: `struct ObjectEvent` size, and the party's slots.
OBJECT_EVENT_SIZE = 0x24
PARTY_SIZE = 6
#: `include/pokemon_storage_system.h` struct PokemonStorage: `currentBox` @0, then `boxes[14][30]` of
#: `struct BoxPokemon` @0x0004 (80 bytes each, `include/pokemon.h`). A box Pokemon's header is NOT
#: encrypted: personality @0, otId @4, and the bit-field byte @19 (isBadEgg bit 0, hasSpecies bit 1, isEgg
#: bit 2; `SetBoxMonData(MON_DATA_SPECIES)` sets hasSpecies, `ZeroBoxMonData` clears the slot).
STORAGE_BOXES_AT, STORAGE_BOXES, STORAGE_SLOTS, BOX_MON_SIZE = 0x0004, 14, 30, 80
BOX_MON_FLAGS_AT, BOX_MON_HAS_SPECIES, BOX_MON_IS_EGG = 19, 0x02, 0x04
#: `include/main.h` struct Main: callback2 @0x04, vblankCallback @0x0C.
GMAIN_CALLBACK2, GMAIN_VBLANK_CALLBACK = 0x04, 0x0C
#: STEP 2.1: `include/palette.h` struct PaletteFadeControl: after `u32 multipurpose1` and the u16 bit-fields
#: delayCounter:6 / y:5 / targetY:5 (offset 4), the next u16 holds blendColor:15 then `active:1`, so the fade is
#: running while bit 7 of byte 7 is set (the bot's `modules/menuing.py` reads the same bit, as teaching only).
PALETTE_FADE_ACTIVE_BYTE, PALETTE_FADE_ACTIVE_BIT = 0x07, 0x80
#: The problem a look reports while the save blocks may be moving (`FrameworkEyes._save_blocks_may_be_moving`).
SAVE_BLOCKS_MOVING = ("between screens: gMain.vblankCallback is NULL, as while MoveSaveBlocks_ResetHeap moves the save "
                      "blocks and the PC boxes (a copy that can span a frame); the player, boxes, bag and progress are not "
                      "read this frame")
#: `include/text.h` struct TextPrinter: 0x24 bytes; `active` @0x1B, `state` @0x1C (`sTextPrinters`).
TEXT_PRINTER_SIZE, TEXT_PRINTER_ACTIVE, TEXT_PRINTER_STATE = 0x24, 0x1B, 0x1C
#: `include/global.fieldmap.h` struct MapHeader (0x1C bytes). Its first field, the layout pointer, is
#: re-pointed at load (`gMapHeader.mapLayout = GetMapLayout()`, `src/overworld.c`), so it may differ from
#: the ROM's; every other byte is the ROM header's, copied (`gMapHeader = *Overworld_GetMapHeaderByGroupAndId`).
MAP_HEADER_SIZE, MAP_HEADER_COPIED_FROM = 0x1C, 4
#: `include/constants/battle.h` BATTLE_TYPE_TRAINER, BATTLE_TYPE_SAFARI.
BATTLE_TYPE_TRAINER = 1 << 3
BATTLE_TYPE_SAFARI = 1 << 7
#: BUILD STEP 2 (`eyes/screens.py` has each source). The tasks whose menu keeps its cursor in `sMenu`.
_SMENU_TASKS = frozenset({
    "Task_HandleYesNoInput", "Task_CallYesOrNoCallback", "Task_NewGameBirchSpeech_ProcessNameYesNoMenu",
    "Task_SetClock_HandleConfirmInput", "Task_NewGameBirchSpeech_ChooseGender", "Task_HandleMultichoiceInput",
    "Task_HandleMultichoiceGridInput", "Task_ShopMenu",
    # STEP 2.1 (`eyes/screens.py` UI_BUSY_TASKS): the gender menu stays on screen while its sprites slide
    "Task_NewGameBirchSpeech_SlideOutOldGenderSprite", "Task_NewGameBirchSpeech_SlideInNewGenderSprite",
})
#: `src/shop.c` struct MartInfo: itemList @8, itemCount @0xC (u16), martType @0xF; struct ShopData:
#: tilemapBuffers[4][0x400] (0x2000 bytes), totalCost @0x2000, itemsShowed @0x2004, selectedRow @0x2006,
#: scrollOffset @0x2008, maxQuantity @0x200A.
MART_INFO_ITEM_LIST, MART_INFO_ITEM_COUNT, MART_INFO_TYPE, SHOP_DATA_SELECTED_ROW = 0x08, 0x0C, 0x0F, 0x2006
#: `include/item.h` struct Item (0x2C bytes): name[ITEM_NAME_LENGTH = 14] @0, price @0x10.
ITEM_SIZE, ITEM_NAME_LENGTH, ITEM_PRICE = 0x2C, 14, 0x10
#: `src/naming_screen.c` struct NamingScreenData: textBuffer @0x1800, state @0x1E10, currentPage @0x1E22,
#: cursorSpriteId @0x1E23, template @0x1E28 (struct NamingScreenTemplate: maxChars @1); Task_HandleInput's
#: tState data[0] is INPUT_STATE_ENABLED (1) while the keyboard takes input.
NAMING_TEXT_BUFFER, NAMING_STATE, NAMING_PAGE, NAMING_CURSOR_SPRITE, NAMING_TEMPLATE = 0x1800, 0x1E10, 0x1E22, 0x1E23, 0x1E28
NAMING_INPUT_ENABLED = 1
#: `include/sprite.h` struct Sprite (0x44 bytes): data[8] @0x2E.
SPRITE_SIZE, SPRITE_DATA = 0x44, 0x2E
#: `include/party_menu.h` struct PartyMenu: slotId (s8) @9.
PARTY_MENU_SLOT_ID = 9
#: `include/constants/items.h` ITEMS_COUNT (377 in Emerald), `include/sprite.h` MAX_SPRITES (64).
ITEMS_COUNT, MAX_SPRITES = 377, 64
#: ‼ BUILD STEP 2, found by the first run of the new eyes: the framework's `read_bytes` bounds EWRAM and IWRAM
#: reads (it raises), but NOT a read in the cartridge (bank 8 and up: a raw memmove from the ROM buffer at
#: `address - 0x08000000`). A GARBAGE pointer there is an access violation that kills the whole process: the
#: naming screen's freshly allocated `sNamingScreen->template` held one for a frame (measured 2026-10-07, a
#: Windows "access violation" in `read_bytes`). So every pointer the eyes FOLLOW is checked to lie inside
#: the 16 MiB cartridge (pret/pokeemerald `pokeemerald.gba` is 16,777,216 bytes) or inside EWRAM first.
ROM_START, ROM_END = 0x08000000, 0x09000000
EWRAM_START, EWRAM_END = 0x02000000, 0x0203FFFF
#: BUILD STEP 4 (`eyes/screens.py` module docstring has the decomp source of each). `include/battle.h` struct
#: BattleScripting: drawlvlupboxState @0x1E, learnMoveState @0x1F (`sLVLBOX_STATE`, `sLEARNMOVE_STATE`).
BATTLE_SCRIPTING_LVLUP_BOX_STATE, BATTLE_SCRIPTING_LEARN_MOVE_STATE = 0x1E, 0x1F
#: `src/evolution_scene.c`: tState EVOSTATE_REPLACE_MOVE, tLearnMoveState MVSTATE_HANDLE_YES_NO.
EVOSTATE_REPLACE_MOVE, MVSTATE_HANDLE_YES_NO = 22, 4
#: `src/pokemon_summary_screen.c` struct PokemonSummaryScreenData: summary.moves @0x84 (0x70 + 0x14), newMove @0x40C4,
#: firstMoveIndex @0x40C6 (0xBC + 4 pages x 2 x 0x400 u16 tilemap buffers = 0x40BC, then mode ... newMove).
SUMMARY_MOVES, SUMMARY_NEW_MOVE = 0x84, 0x40C4
#: `src/party_menu.c` struct PartyMenuInternal: task @0, exitCallback @4, a u32 of bit-fields @8, windowId[3] @0xC,
#: actions[8] @0xF, numActions @0x17.
PARTY_INTERNAL_ACTIONS = 0x0F
#: `include/item_menu.h` struct BagMenu: newScreenCallback @0, tilemapBuffer[0x800] @4, spriteIds[12] @0x804,
#: windowIds[10] @0x810, toSwapPos @0x81A, a bit-field byte @0x81B, unused1[2] @0x81C, two task ids @0x81E,
#: contextMenuItemsPtr @0x820, contextMenuItemsBuffer[4] @0x824, contextMenuNumItems @0x828.
BAG_MENU_CONTEXT_ITEMS = 0x820
#: The bag's action-list tasks (`src/item_menu.c`): their cursor is `sMenu`'s.
_BAG_ACTION_TASKS = frozenset({"Task_ItemContext_SingleRow", "Task_ItemContext_MultipleRows"})
#: The player's battle controller functions that take input (`src/battle_controller_player.c`), upper case as named.
_PLAYER_INPUT_FUNCTIONS = frozenset({"HANDLEINPUTCHOOSEACTION", "HANDLEINPUTCHOOSEMOVE", "HANDLEINPUTCHOOSETARGET",
                                     "PLAYERHANDLEYESNOINPUT"})
#: The framework's StatusCondition names, as the eyes name them (`eyes/view.py` status_name).
_BATTLE_STATUS = {
    "Healthy": "ok", "Sleep": "sleep", "Poison": "poison", "Burn": "burn", "Freeze": "freeze",
    "Paralysis": "paralysis", "BadPoison": "toxic",
}
#: The framework's facing names.
_OBJECT_FACING = {"Down": "down", "Up": "up", "Left": "left", "Right": "right"}
#: Game states where there is no save loaded yet, so no player, party or bag to read.
_NO_GAME_YET = frozenset({"TITLE_SCREEN", "MAIN_MENU"})


def _u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "little")


def _s16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "little", signed=True)


def _u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "little")


def _s32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "little", signed=True)


def _rom_bytes(address: int, length: int) -> bytes:
    """`length` bytes of the CARTRIDGE at a pointer the game holds, refused (an exception the look reports)
    unless the whole range lies inside the cartridge: see ROM_START."""
    if not (ROM_START <= address and address + length <= ROM_END and length >= 0):
        raise RuntimeError(f"not a cartridge pointer: 0x{address:08X} (+{length})")
    return context.emulator.read_bytes(address, length)


def _rom_string(pointer: int) -> str:
    """The ROM string a text printer's `currentChar` points into, from its start up to that character. A ROM
    string ends with EOS (0xFF), so it starts right after the previous EOS (looked for in the 256 bytes before);
    a finished printer points one past its own EOS (`src/text.c` RenderText: `currentChar++` before the switch)."""
    back = min(256, pointer - ROM_START)
    raw = bytes(_rom_bytes(pointer - back, back))
    body = raw[:-1] if raw.endswith(b"\xff") else raw
    return decode_text(body[body.rfind(b"\xff") + 1:])


def _ewram_bytes(address: int, length: int) -> bytes:
    """`length` bytes of EWRAM at a pointer the game holds (a heap allocation), refused unless it is one."""
    if not (EWRAM_START <= address and address + length <= EWRAM_END and length >= 0):
        raise RuntimeError(f"not an EWRAM pointer: 0x{address:08X} (+{length})")
    return context.emulator.read_bytes(address, length)


class FrameworkEyes:
    """Implements `ai_player.mode.Eyes` inside the framework. Construction reads nothing (the purity
    unit tests build a Session with no emulator); the first `look()` does."""

    def __init__(self, crop: bool = True) -> None:
        self.crop = crop
        self.looks = 0
        self._checked_rom = False
        self._tile_bits: bytes | None = None
        self._attributes: dict[int, bytes] = {}
        self._maps: dict[tuple[int, int], tuple] = {}
        self._scene_callbacks: dict[int, str] | None = None  # STEP 2.1: address (thumb bit off) -> symbol name

    # ------------------------------------------------------------------ the one public call
    def look(self) -> Observation:
        start = time.perf_counter()
        if not self._checked_rom:
            if not context.rom.is_emerald:
                raise RuntimeError("the AI's eyes know Pokemon Emerald's memory layout only")
            self._checked_rom = True
        problems: list[str] = []
        frame = context.emulator.get_frame_count()
        if frame == 0:
            # A fresh boot before its first frame: the game has not run, and the framework's per-frame
            # caches answer None for this frame (measured: every reader failed on a None).
            self.looks += 1
            return Observation(
                frame=0, screen=ScreenState(game_state="UNKNOWN", screen="other", menu=None, text_box_open=False,
                                            waits_for_button=False, in_battle=False,
                                            scene=SCENE_CALLBACKS["NULL"]),
                player=None, view=None, party=None, bag=None, progress=None, battle=None, last_battle_outcome=0,
                problems=("no frame has run yet (frame 0): there is nothing to see",),
                cost_ms=round((time.perf_counter() - start) * 1000.0, 3),
            )
        screen = self._screen(problems)
        player = view = party = storage = bag = progress = battle = None
        outcome = 0
        if screen.game_state not in _NO_GAME_YET:
            moving = self._guarded("vblank callback", problems, self._save_blocks_may_be_moving)
            if moving:
                problems.append(SAVE_BLOCKS_MOVING)
            else:
                player = self._guarded("player", problems, self._player)
                storage = self._guarded("storage", problems, self._storage)
                bag = self._guarded("bag", problems, self._bag)
                progress = self._guarded("progress", problems, self._progress)
            party = self._guarded("party", problems, lambda: self._party(problems))
            outcome = self._guarded("battle outcome", problems, lambda: read_symbol("gBattleOutcome", size=1)[0]) or 0
            # No view while the position is settling: the window would be centred on a tile of the old map.
            if player is not None and not player.settling and screen.game_state == "OVERWORLD":
                view = self._guarded("view", problems, lambda: self._view(player))
            if screen.in_battle and screen.game_state == "BATTLE":
                battle = self._guarded("battle", problems, self._battle)
        self.looks += 1
        return Observation(
            frame=frame,
            screen=screen,
            player=player,
            view=view,
            party=None if party is None else tuple(party),  # None = not read; () = no Pokemon
            bag=bag,
            progress=progress,
            battle=battle,
            last_battle_outcome=int(outcome),
            problems=tuple(problems),
            cost_ms=round((time.perf_counter() - start) * 1000.0, 3),
            storage=storage,
        )

    @staticmethod
    def _save_blocks_may_be_moving() -> bool:
        """True while `gMain.vblankCallback` is NULL. `MoveSaveBlocks_ResetHeap` (`src/load_save.c`, run by
        `CB2_InitBattle` at every battle start and by every map load) NULLs it, copies both save blocks and
        the PC boxes to the heap, moves the save-block pointers, copies them back, and only then restores
        it. The copy is long enough to span a frame boundary: measured 2026-10-07 at a trainer battle's end
        (`gates/probe_step11.py trainer`), on the frame the pointers moved, save block 1's last Pokedex copy
        (`seen2`) was half restored and the Pokedex read 0 owned for that frame, which wrote
        `[DEX] owned 5 -> 0` and `0 -> 5`; at a battle start the same frame made the map-header check refuse.
        Other transition frames NULL it too (about 15 around a battle's start and end, measured), so this
        withholds a little more than the move itself: the screen is between two screens on all of them."""
        return _u32(read_symbol("gMain", GMAIN_VBLANK_CALLBACK, 4), 0) == 0

    @staticmethod
    def _guarded(what: str, problems: list[str], read):
        """One part of a look. A part that cannot be read this frame is None and says why: a look
        never raises, so the brain always gets an Observation."""
        try:
            return read()
        except Exception as error:  # noqa: BLE001 - reported in the Observation, never swallowed silently
            problems.append(f"{what}: {type(error).__name__}: {error}")
            return None

    # ------------------------------------------------------------------ the screen
    def _screen(self, problems: list[str]) -> ScreenState:
        game_state = "UNKNOWN"
        try:
            game_state = get_game_state().name
        except Exception as error:  # noqa: BLE001
            problems.append(f"game state: {type(error).__name__}: {error}")
        in_battle = bool(self._guarded("battle active", problems, battle_is_active)) or game_state in (
            "BATTLE", "BATTLE_STARTING", "BATTLE_ENDING")
        text_box_mode = self._guarded("message box", problems, lambda: read_symbol("sFieldMessageBoxMode", size=1)[0]) or 0
        # Build step 2: each active task's data too (a menu's cursor lives in its task, `eyes/screens.py`).
        task_data = self._guarded("tasks", problems, lambda: {task.symbol: bytes(task.data) for task in get_tasks()}) or {}
        tasks = frozenset(task_data)
        reason = self._guarded("button wait", problems, self._waits_for_button)
        if reason is None:
            reason = task_wait(tasks)  # build step 2: a task polling A/B with no text printer waiting
        if reason is None and game_state == "BATTLE":
            reason = self._guarded("battle wait", problems, self._battle_wait)  # build step 4: the level-up stats box
        kind, menu = classify_screen(game_state, in_battle, text_box_mode, tasks)
        # STEP 2.1: what a person sees when nothing takes input (`eyes/screens.py` scene_of): a fade, and the scene.
        # Read BEFORE the menu since the step-2 review (item 4): while a fade runs nothing takes input
        # (`eyes/screens.py` read_ui), so the menu's `accepts_input` needs it. The same read as before, moved up.
        fading = self._guarded("palette fade", problems, lambda: bool(
            read_symbol("gPaletteFade", PALETTE_FADE_ACTIVE_BYTE, 1)[0] & PALETTE_FADE_ACTIVE_BIT))
        ui = self._guarded("menu cursor", problems, lambda: self._ui(game_state, task_data, bool(fading)))
        shown = reason is not None or ui is not None or text_box_mode != 0
        text = self._guarded("text", problems, lambda: self._text(shown))
        status = self._guarded("script status", problems, lambda: read_symbol("sGlobalScriptContextStatus", size=1)[0])
        locked = self._guarded("field controls", problems, lambda: read_symbol("sLockFieldControls", size=1)[0])
        callback = self._guarded("main callback", problems, self._callback_name)
        scene = scene_of(game_state, tasks, callback)
        return ScreenState(game_state=game_state, screen=kind, menu=menu, text_box_open=text_box_mode != 0,
                           waits_for_button=reason is not None, in_battle=in_battle, wait_reason=reason, ui=ui, text=text,
                           script_running=status is not None and status != SCRIPT_CONTEXT_SHUTDOWN,
                           controls_locked=bool(locked), fading=bool(fading), scene=scene)

    def _callback_name(self) -> str | None:
        """STEP 2.1: `gMain.callback2` named, when it is one of `SCENE_CALLBACKS` ("NULL" when it is 0), else
        None. The table's names are resolved ONCE with `get_symbol` (a symbol-table lookup); a name the table
        does not hold is skipped."""
        if self._scene_callbacks is None:
            found: dict[int, str] = {}
            for name in SCENE_CALLBACKS:
                if name == "NULL":
                    continue
                try:
                    found[get_symbol(name)[0] & ~1] = name
                except Exception:  # noqa: BLE001 - a callback this ROM's symbol table does not name
                    continue
            self._scene_callbacks = found
        address = _u32(read_symbol("gMain", GMAIN_CALLBACK2, 4), 0)
        if address == 0:
            return "NULL"
        return self._scene_callbacks.get(address & ~1)

    # ------------------------------------------------------------------ build step 2: menus, cursors, text
    def _ui(self, game_state: str, tasks: dict[str, bytes], fading: bool = False):
        """The bytes `eyes/screens.py` read_ui needs for the menu that is open, read only for THAT menu (its
        input task is active). Every read is a symbol or a pointer the decomp names (`eyes/screens.py`).
        `fading` (step 2.1, the review's item 4) is this look's palette fade, read by `_screen`: no extra read."""
        raw: dict = {"fading": fading}
        if tasks.keys() & _SMENU_TASKS:
            raw["menu"] = bytes(read_symbol("sMenu", 0, 12))
        if "Task_ShopMenu" in tasks:
            raw["mart_type"] = read_symbol("sMartInfo", MART_INFO_TYPE, 1)[0]
        if "Task_HandleMultichoiceInput" in tasks or "Task_HandleMultichoiceGridInput" in tasks:
            data = tasks.get("Task_HandleMultichoiceInput") or tasks.get("Task_HandleMultichoiceGridInput")
            raw["multichoice_options"] = self._multichoice_names(int.from_bytes(data[14:16], "little", signed=True))
            raw["multichoice_delay"] = read_symbol("sProcessInputDelay", size=1)[0]
        if "Task_BuyMenu" in tasks or "Task_BuyHowManyDialogueHandleInput" in tasks:
            pointer = _u32(read_symbol("sShopData", size=4), 0)
            if pointer:
                shop = _ewram_bytes(pointer + SHOP_DATA_SELECTED_ROW, 5)
                raw["shop"] = {"row": _u16(shop, 0), "scroll": _u16(shop, 2), "max_quantity": shop[4]}
            if "Task_BuyMenu" in tasks:
                raw["mart_items"], raw["mart_prices"] = self._mart_items()
        if "StartMenuTask" in tasks:
            count = min(read_symbol("sNumStartMenuActions", size=1)[0], 9)
            actions = read_symbol("sCurrentStartMenuActions", 0, 9)
            raw["start_menu"] = {"cursor": read_symbol("sStartMenuCursorPos", size=1)[0], "actions": list(actions[:count])}
        if game_state == "NAMING_SCREEN" or "Task_NamingScreen" in tasks:
            raw["naming"] = self._naming(tasks)
        if game_state == "BAG_MENU":
            position = read_symbol("gBagPosition", 0, 0x1C)
            pocket = position[5]
            if pocket < 5:
                raw["bag"] = {"pocket": pocket, "cursor": _u16(position, 8 + 2 * pocket),
                              "scroll": _u16(position, 0x12 + 2 * pocket),
                              "items": self._pocket_items(pocket)}  # build step 4: the list as shown
            if tasks.keys() & _BAG_ACTION_TASKS:
                raw["menu"] = bytes(read_symbol("sMenu", 0, 12))
                raw["bag_action"] = {"actions": self._bag_actions()}
        if game_state == "PARTY_MENU":
            slot = read_symbol("gPartyMenu", PARTY_MENU_SLOT_ID, 1)[0]
            raw["party_slot"] = slot - 256 if slot >= 128 else slot
            raw["party_tasks_known"] = True  # build step 4: the list takes input only while its task runs
            if "Task_HandleSelectionMenuInput" in tasks:
                raw["menu"] = bytes(read_symbol("sMenu", 0, 12))
                raw["party_action"] = {"actions": self._party_actions()}
        if game_state == "BATTLE":
            raw.update(self._battle_menus(fading))
        if game_state == "EVOLUTION" and "Task_EvolutionScene" in tasks:
            raw["battle_yes_no"] = self._evolution_yes_no(tasks["Task_EvolutionScene"], fading)
        if game_state == "POKEMON_SUMMARY_SCREEN" and "Task_HandleReplaceMoveInput" in tasks:
            raw["move_forget"] = self._move_forget(fading)
        return read_ui(game_state, tasks, raw)

    # ------------------------------------------------------------------ build step 4: the battle's menus (read only)
    def _battle_menus(self, fading: bool) -> dict:
        """The battle's ACTION menu (build step 3), its MOVE grid and its YES/NO box (`eyes/screens.py` module docstring
        has the decomp source of each). One name lookup of the player's controller function (`get_symbol_name`, the
        step-3 door) serves all three; the yes/no of a battle SCRIPT is told by the opcode the script engine stands on
        (`gBattlescriptCurrInstr`, a ROM pointer, range-checked) and that command's own input state.

        THE ACTION MENU (build step 3, read only): the player's battler is 0 (`B_POSITION_PLAYER_LEFT`); its controller
        function is `gBattlerControllerFuncs[0]`, NAMED by the symbol table at its address (the thumb bit off:
        `get_symbol_name`; `get_symbol` cannot be used, the name is static in two files, the gate's door says which), and
        the menu takes input while it is `HandleInputChooseAction`; the cursor is `gActionSelectionCursor[0]`. A Safari
        battle's controller has a function of the same name for ITS menu (BALL / POKéBLOCK / GO NEAR / RUN), so a Safari
        battle is not this menu (`gBattleTypeFlags` BATTLE_TYPE_SAFARI)."""
        safari = bool(_u32(read_symbol("gBattleTypeFlags", size=4), 0) & BATTLE_TYPE_SAFARI)
        funcs = read_symbol("gBattlerControllerFuncs", 0, 16)
        # the player's battlers: 0 (left, the only one in a single battle) and 2 (right, a double battle's second);
        # the one whose controller runs an INPUT function is the one choosing (`src/battle_controller_player.c`)
        battler, name = 0, ""
        count = read_symbol("gBattlersCount", size=1)[0]  # 2 in a single battle: battler 2's slot may hold an old function
        for position in ((0, 2) if count > 2 else (0,)):
            function = _u32(funcs, 4 * position)
            found = (get_symbol_name(function & ~1) if function else "").upper()
            if found in _PLAYER_INPUT_FUNCTIONS:
                battler, name = position, found
                break
        out = {"battle_action": {"choosing": name == "HANDLEINPUTCHOOSEACTION" and not safari,
                                 "cursor": read_symbol("gActionSelectionCursor", battler, 1)[0], "battler": battler}}
        if name == "HANDLEINPUTCHOOSEMOVE" and not safari:
            battling = get_battle_state().battling_pokemon
            moves = [slot.move.name if slot is not None else "" for slot in battling[battler].moves] if battler < len(battling) else []
            out["battle_move"] = {"choosing": True, "cursor": read_symbol("gMoveSelectionCursor", battler, 1)[0],
                                  "moves": moves, "battler": battler}
        if name == "HANDLEINPUTCHOOSETARGET" and not safari:
            battling = get_battle_state().battling_pokemon
            out["battle_target"] = {"choosing": True, "cursor": read_symbol("gMultiUsePlayerCursor", size=1)[0],
                                    "names": [mon.species.name for mon in battling], "battler": battler}
        if name == "PLAYERHANDLEYESNOINPUT":
            out["battle_yes_no"] = {"open": True, "cursor": read_symbol("gMultiUsePlayerCursor", size=1)[0],
                                    "accepts": not fading, "source": "the player's battle controller"}
            return out
        opcode, _ = self._battle_script_opcode()
        if opcode in BATTLE_YES_NO_OPCODES:
            communication = read_symbol("gBattleCommunication", 0, 2)
            if opcode in (0x5A, 0x5B):
                state = read_symbol("gBattleScripting", BATTLE_SCRIPTING_LEARN_MOVE_STATE, 1)[0]
            else:
                state = communication[0]
            if state == 1:
                out["battle_yes_no"] = {"open": True, "cursor": communication[1], "accepts": not fading,
                                        "source": f"the battle script's {BATTLE_YES_NO_OPCODES[opcode]}"}
        return out

    @staticmethod
    def _battle_script_opcode() -> tuple[int | None, int]:
        """(the opcode at `gBattlescriptCurrInstr`, the pointer), or (None, pointer) when it does not point into the ROM."""
        pointer = _u32(read_symbol("gBattlescriptCurrInstr", size=4), 0)
        if not ROM_START <= pointer < ROM_END:
            return None, pointer
        return _rom_bytes(pointer, 1)[0], pointer

    def _battle_wait(self) -> str | None:
        """BUILD STEP 4: a battle-script command that waits for a key with no text printer waiting (`eyes/screens.py`
        BATTLE_SCRIPT_WAITS: the level-up stats box), as a wait reason; None otherwise."""
        opcode, _ = self._battle_script_opcode()
        if opcode not in BATTLE_SCRIPT_WAITS:
            return None
        states, what = BATTLE_SCRIPT_WAITS[opcode]
        if read_symbol("gBattleScripting", BATTLE_SCRIPTING_LVLUP_BOX_STATE, 1)[0] in states:
            return what
        return None

    @staticmethod
    def _evolution_yes_no(data: bytes, fading: bool) -> dict:
        """The evolution scene's learn-a-move yes/no (`src/evolution_scene.c`): Task_EvolutionScene's tState data[0] ==
        EVOSTATE_REPLACE_MOVE (22) and tLearnMoveState data[6] == MVSTATE_HANDLE_YES_NO (4); cursor gBattleCommunication[1]."""
        if _s16(data, 0) != EVOSTATE_REPLACE_MOVE or _s16(data, 12) != MVSTATE_HANDLE_YES_NO:
            return {"open": False}
        return {"open": True, "cursor": read_symbol("gBattleCommunication", 1, 1)[0], "accepts": not fading,
                "source": "the evolution scene"}

    @staticmethod
    def _move_forget(fading: bool) -> dict:
        """The summary screen's forget-a-move list (`src/pokemon_summary_screen.c` struct PokemonSummaryScreenData through
        the pointer `sMonSummaryScreen`: summary.moves[4] @0x84, newMove @0x40C4, firstMoveIndex @0x40C6), the move names
        from the game's table (`get_move_by_index`, a lookup)."""
        pointer = _u32(read_symbol("sMonSummaryScreen", size=4), 0)
        block = _ewram_bytes(pointer + SUMMARY_MOVES, 8)
        tail = _ewram_bytes(pointer + SUMMARY_NEW_MOVE, 4)
        ids = [_u16(block, 2 * i) for i in range(4)] + [_u16(tail, 0)]
        return {"moves": [get_move_by_index(i).name if i else "" for i in ids], "cursor": tail[2], "accepts": not fading}

    @staticmethod
    def _party_actions() -> list[int]:
        """`src/party_menu.c` struct PartyMenuInternal (through `sPartyMenuInternal`): actions[8] @0xF, numActions @0x17."""
        pointer = _u32(read_symbol("sPartyMenuInternal", size=4), 0)
        block = _ewram_bytes(pointer + PARTY_INTERNAL_ACTIONS, 9)
        return list(block[:min(block[8], 8)])

    @staticmethod
    def _bag_actions() -> list[int]:
        """`include/item_menu.h` struct BagMenu (through `gBagMenu`): contextMenuItemsPtr @0x820 (a ROM table, or the
        EWRAM buffer @0x824), contextMenuNumItems @0x828."""
        pointer = _u32(read_symbol("gBagMenu", size=4), 0)
        block = _ewram_bytes(pointer + BAG_MENU_CONTEXT_ITEMS, 9)
        items, count = _u32(block, 0), min(block[8], 6)
        if ROM_START <= items < ROM_END:
            return list(_rom_bytes(items, count))
        return list(_ewram_bytes(items, count))

    @staticmethod
    def _pocket_items(pocket: int) -> list[str]:
        """The open pocket's items as the bag LISTS them: its slots holding something, in order (`get_item_bag`, the
        step-1 door: save block 1's pockets, a decode)."""
        bag = get_item_bag()
        slots = (bag.items, bag.poke_balls, bag.tms_hms, bag.berries, bag.key_items)[pocket]
        return [slot.item.name for slot in slots if slot.quantity > 0]

    def _naming(self, tasks: dict[str, bytes]) -> dict | None:
        """`src/naming_screen.c` struct NamingScreenData (via the pointer `sNamingScreen`), and the cursor
        sprite's data[0] / data[1], where `SetCursorPos` stores the cursor's column and row."""
        pointer = _u32(read_symbol("sNamingScreen", size=4), 0)
        if not pointer:
            return None
        text = _ewram_bytes(pointer + NAMING_TEXT_BUFFER, 16)
        block = _ewram_bytes(pointer + NAMING_STATE, 0x1C)
        state, page, sprite_id = block[0], block[NAMING_PAGE - NAMING_STATE], block[NAMING_CURSOR_SPRITE - NAMING_STATE]
        template = _u32(block, NAMING_TEMPLATE - NAMING_STATE)
        # While the screen is being set up the allocation still holds garbage: no template, no sprite yet.
        max_chars = _rom_bytes(template + 1, 1)[0] if ROM_START <= template < ROM_END else None
        if sprite_id >= MAX_SPRITES:
            raise RuntimeError(f"the naming screen's cursor sprite id {sprite_id} is not a sprite (setting up)")
        sprite = read_symbol("gSprites", sprite_id * SPRITE_SIZE + SPRITE_DATA, 4)
        handler = tasks.get("Task_HandleInput")
        return {"state": state, "page": page, "x": _s16(sprite, 0), "y": _s16(sprite, 2), "text": decode_text(text),
                "max_chars": max_chars, "input_enabled": handler is not None and _s16(handler, 0) == NAMING_INPUT_ENABLED}

    def _multichoice_names(self, list_id: int) -> list[str]:
        """`src/script_menu.c` sMultichoiceLists[id] = {const struct MenuAction *list; u8 count;} (ROM), each
        MenuAction {const u8 *text; func}: the option texts, decoded by the AI's own charmap."""
        _, table_size = get_symbol("sMultichoiceLists")
        if not 0 <= list_id < table_size // 8:
            return []
        entry = read_symbol("sMultichoiceLists", 8 * list_id, 8)
        actions, count = _u32(entry, 0), entry[4]
        names = []
        for index in range(min(count, 16)):
            text = _u32(_rom_bytes(actions + 8 * index, 4), 0)
            names.append(decode_text(_rom_bytes(text, 24)))
        return names

    def _mart_items(self) -> tuple[list[str], list[int]]:
        """The items for sale (`sMartInfo.itemList`, ROM u16s, `itemCount` of them), each named and priced from
        the ROM's `gItems` (`include/item.h` struct Item: name[14] @0, price @0x10), decoded by the AI's own
        charmap. (The list draws the price `>> IsPokeNewsActive(POKENEWS_SLATEPORT)`: half while Slateport's
        sale is on; not modelled.)"""
        info = read_symbol("sMartInfo", 0, 0x10)
        items, count = _u32(info, MART_INFO_ITEM_LIST), min(_u16(info, MART_INFO_ITEM_COUNT), 64)
        ids = _rom_bytes(items, 2 * count) if count else b""
        names, prices = [], []
        for index in range(count):
            item_id = _u16(ids, 2 * index)
            if item_id >= ITEMS_COUNT:
                raise RuntimeError(f"the mart lists item {item_id}, which is not an item")
            item = read_symbol("gItems", item_id * ITEM_SIZE, ITEM_SIZE)
            names.append(decode_text(item[:ITEM_NAME_LENGTH]))
            prices.append(_u16(item, ITEM_PRICE))
        return names, prices

    @staticmethod
    def _text(shown: bool) -> str | None:
        """The message on screen, decoded by the AI's own charmap (`eyes/screens.py`).
          * While a printer is ACTIVE (a waiting one first): as far as it has printed, up to its next character
            (`currentChar`): from the start of `gStringVar4` (field, intro and shop messages are expanded there
            before they print) or `gDisplayedStringBattle` when it points into one, or from the start of the
            ROM string it points into (a text printed straight from the ROM: `_rom_string`).
          * When no printer is active but something still SHOWS the last message (`shown`: a wait, a menu such
            as the yes/no under its question, the field box): what PRINTER 0 (the message window of the field,
            the intro and the wall clock) printed last: the newest message of the buffer it points into
            (`gStringVar4` whole: a shop message printed by another window was expanded there too), or the ROM
            string it points into (the wall clock's "Is this the correct time?" is printed straight from the
            ROM; an earlier rule that took any printer pointing into `gStringVar4` reported a stale message
            there, measured 2026-10-07).
          * Otherwise None.
        ‼ Limit: with no printer active, "the last message" can be an OLD one when a menu opens with no
        message of its own (the start menu): `text` is what was printed last, not proof it is still drawn."""
        raw = read_symbol("sTextPrinters", 0, TEXT_PRINTER_SIZE * TEXT_PRINTER_COUNT)
        buffers = (get_symbol("gStringVar4"), get_symbol("gDisplayedStringBattle"))
        candidates = []
        for index in range(TEXT_PRINTER_COUNT):
            at = index * TEXT_PRINTER_SIZE
            active, state = raw[at + TEXT_PRINTER_ACTIVE], raw[at + TEXT_PRINTER_STATE]
            if active:
                candidates.append((state not in TEXT_PRINTER_WAIT_STATES, index, _u32(raw, at)))
        for _, _, pointer in sorted(candidates):
            for base, size in buffers:
                if base <= pointer <= base + size:
                    return decode_text(context.emulator.read_bytes(base, pointer - base)) if pointer > base else ""
            if ROM_START <= pointer < ROM_END:
                return _rom_string(pointer)
        if shown:
            last = _u32(raw, 0)  # printer 0: the message window of the field, the intro and the wall clock
            for base, size in buffers:
                if base <= last <= base + size:
                    return decode_text(context.emulator.read_bytes(base, size))
            if ROM_START <= last < ROM_END:
                return _rom_string(last)
        return None

    @staticmethod
    def _waits_for_button() -> str | None:
        """WHY the game waits for A or B, or None: a running script waiting in `waitbuttonpress`
        (`eyes/view.py` script_waits_for_button: its native function is WaitForAorBPress and the context
        is not shut down, since a finished script leaves its last native function behind), or ANY active
        text printer in a state that moves on only when A or B is pressed (`eyes/view.py`
        text_printer_wait: WAIT, the `{PAUSE_UNTIL_PRESS}` of every trainer's defeat text, and CLEAR /
        SCROLL_START, the down arrow), unless `gTextFlags` says autoScroll."""
        status = read_symbol("sGlobalScriptContextStatus", size=1)[0]
        script = get_global_script_context()
        if script_waits_for_button(status, script.mode, script.native_function_name):
            return "script waitbuttonpress"
        raw = read_symbol("sTextPrinters", 0, TEXT_PRINTER_SIZE * TEXT_PRINTER_COUNT)
        printers = [(index, raw[index * TEXT_PRINTER_SIZE + TEXT_PRINTER_ACTIVE], raw[index * TEXT_PRINTER_SIZE + TEXT_PRINTER_STATE])
                    for index in range(TEXT_PRINTER_COUNT)]
        return text_printer_wait(printers, read_symbol("gTextFlags", size=1)[0])

    # ------------------------------------------------------------------ the player
    def _player(self) -> PlayerState | None:
        avatar = read_symbol("gPlayerAvatar", size=0x24)
        flags, object_id = avatar[0], avatar[5]
        player_object = read_symbol("gObjectEvents", object_id * OBJECT_EVENT_SIZE, OBJECT_EVENT_SIZE)
        if not player_object[0] & 0x01:
            raise RuntimeError(f"the player's object event {object_id} is not active")
        save_block_1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
        # struct SaveBlock1: pos (s16 x, s16 y) @0, location (mapGroup, mapNum, warpId, ...) @4.
        saved = context.emulator.read_bytes(save_block_1, 6)
        group, number = saved[4], saved[5]
        name, const = self._map_names(group, number)
        # The position is reported only when the object's tile and the save block's agree (step 1.1):
        # mid-warp the save block is already the NEW map while the object stands on the OLD map's tile.
        position = settled_position((_s16(player_object, 0x10) - MAP_OFFSET, _s16(player_object, 0x12) - MAP_OFFSET),
                                    (_s16(saved, 0), _s16(saved, 2)))
        # The VISIBLE id (the trainer card's IDNo.): the framework's `trainer_id` is that half only. A
        # Pokemon's OT id is reported as its visible half too (`_mon`), so ownership compares like with like,
        # and the secret half is never in an Observation (step 1.1).
        trainer = get_player().trainer_id
        return PlayerState(
            map_group=group,
            map_number=number,
            map_name=name,
            map_const=const,
            x=None if position is None else position[0],
            y=None if position is None else position[1],
            facing=facing_name(player_object[0x18] & 0x0F),
            movement=movement_mode(flags),
            elevation=player_object[0x0B] & 0x0F,
            avatar_flags=flags,
            trainer_id=visible_id(trainer),
            settling=position is None,
        )

    def _map_names(self, group: int, number: int) -> tuple[str, str | None]:
        return self._map_facts(group, number)[:2]

    def _map_facts(self, group: int, number: int) -> tuple:
        """(region-map name, map constant, interactable tiles) of a map, read once: a map's
        header and events are ROM data. They are read through the LIVE header (`gMapHeader`, via
        `get_map_data_for_current_position`), and (group, number) comes from save block 1, so the two are
        first checked to be the SAME map: the live header must equal map (group, number)'s own ROM header
        (`_rom_map_header`, the ROM table `gMapGroups`), byte for byte after the layout pointer. That is the
        check that can fail: a header left from another map. (Until 2026-10-07 this compared the save
        block's map with `get_map_data_for_current_position()`'s, which takes it from the same save block
        bytes: a check that could not fail, found by the step-1 verifier. Its fault arm is the probe's
        `header_guard`, a stale header written in the probe's own emulator.) A failed check is reported
        in `problems` and nothing is kept, so the next look checks again."""
        key = (group, number)
        if key not in self._maps:
            live = read_symbol("gMapHeader", size=MAP_HEADER_SIZE)
            rom = self._rom_map_header(group, number)
            if live[MAP_HEADER_COPIED_FROM:] != rom[MAP_HEADER_COPIED_FROM:]:
                raise RuntimeError(f"the live map header (gMapHeader) is not map {key}'s ROM header (gMapGroups[{group}][{number}]): "
                                   f"live {bytes(live).hex()} rom {bytes(rom).hex()}")
            location = get_map_data_for_current_position()
            if location is None:
                raise RuntimeError("no player avatar to place the map header")
            try:
                const = get_map_enum(key).name
            except ValueError:
                const = None
            # (build step 3.1, the step-3 review's finding 5) the map's WARP events are no longer read: nothing on screen
            # shows the warp table. A tile is an exit by how it LOOKS (`_tile`: EXIT_BEHAVIORS), and the AI learns the
            # rest by using them (`world/memory.py`); the table is read on the TEST side only (`gates/`).
            signs = tuple(
                (event.local_coordinates, event.elevation) for event in location.bg_events if event.kind == "Script"
            )
            self._maps[key] = (location.map_name, const, signs)
        return self._maps[key]

    @staticmethod
    def _rom_map_header(group: int, number: int) -> bytes:
        """Map (group, number)'s header as the ROM holds it: `gMapGroups[group]` points to the group's
        table of header pointers (`include/global.fieldmap.h`, `data/maps/map_groups.inc`). Three ROM reads,
        each pointer checked to be a cartridge pointer first (build step 2: see ROM_START)."""
        table = _u32(read_symbol("gMapGroups", 4 * group, 4), 0)
        pointer = _u32(_rom_bytes(table + 4 * number, 4), 0)
        return _rom_bytes(pointer, MAP_HEADER_SIZE)

    # ------------------------------------------------------------------ the view
    def _view(self, player: PlayerState) -> View:
        layout = read_symbol("gBackupMapLayout", size=12)
        width, height, grid = _s32(layout, 0), _s32(layout, 4), _u32(layout, 8)
        header = read_symbol("gMapHeader", size=0x1C)
        map_layout = _rom_bytes(_u32(header, 0), 24)
        border = _rom_bytes(_u32(map_layout, 8), 8)
        primary = self._tileset_attributes(_u32(map_layout, 16))
        secondary = self._tileset_attributes(_u32(map_layout, 20))
        tile_bits = self._tile_flags()
        _, _, signs = self._map_facts(player.map_group, player.map_number)
        if self.crop:
            up, down, left_of, right_of = VIEW_UP, VIEW_DOWN, VIEW_HALF_WIDTH, VIEW_HALF_WIDTH
        else:
            # FAULT `AI_PLAYER_FAULT_NO_CROP` only (build step 3, the CROP arm): the WHOLE live grid, the map and its
            # margin, so a test can show that the navigator, given tiles a person could not see, plans differently.
            # The same read-only reads as the window, over every row and column of `gBackupMapLayout`.
            up, down = player.y + MAP_OFFSET, height - 1 - (player.y + MAP_OFFSET)
            left_of, right_of = player.x + MAP_OFFSET, width - 1 - (player.x + MAP_OFFSET)
        rows = []
        for dy in range(-up, down + 1):
            vy = player.y + MAP_OFFSET + dy
            left = player.x + MAP_OFFSET - left_of
            count = left_of + right_of + 1
            inside = 0 <= vy < height and 0 <= left and left + count <= width
            raw = context.emulator.read_bytes(grid + 2 * (vy * width + left), 2 * count) if inside else b""
            row = []
            for column in range(count):
                vx = left + column
                if inside:
                    block = _u16(raw, 2 * column)
                elif 0 <= vx < width and 0 <= vy < height:
                    block = _u16(context.emulator.read_bytes(grid + 2 * (vy * width + vx), 2), 0)
                else:
                    block = MAPGRID_UNDEFINED
                row.append(self._tile(player, vx - MAP_OFFSET, vy - MAP_OFFSET, block, border, primary, secondary,
                                      tile_bits, dy))
            rows.append(tuple(row))
        objects = self._objects(player) + self._signs(player, signs)
        return View(left=left_of, right=right_of, up=up, down=down, rows=tuple(rows), objects=tuple(objects),
                    cropped=self.crop)

    @staticmethod
    def _tile(player: PlayerState, x: int, y: int, block: int, border: bytes, primary: bytes, secondary: bytes,
              tile_bits: bytes, dy: int) -> Tile:
        """One grid block, decoded as `src/fieldmap.c` does (`MapGridGetCollisionAt`, `...ElevationAt`,
        `...MetatileIdAt`, `GetMetatileAttributesById`). `warp`: the tile LOOKS like a way out (its behaviour is in
        `eyes/view.py` EXIT_BEHAVIORS: a door, stairs, a ladder, an escalator, an arrow mat, a hole; build step 3.1),
        not "the ROM's warp table has an event here", which nothing on screen shows."""
        if block == MAPGRID_UNDEFINED:
            vx, vy = x + MAP_OFFSET, y + MAP_OFFSET
            border_index = ((vx + 1) & 1) + (((vy + 1) & 1) << 1)
            metatile = _u16(border, 2 * border_index) & MAPGRID_METATILE_ID_MASK
            collision, elevation = 1, 0
        else:
            metatile = block & MAPGRID_METATILE_ID_MASK
            collision = (block >> 10) & 0x3
            elevation = (block >> 12) & 0xF
        if metatile < METATILES_IN_PRIMARY:
            attribute = _u16(primary, 2 * metatile)
        elif metatile < METATILES_TOTAL:
            attribute = _u16(secondary, 2 * (metatile - METATILES_IN_PRIMARY))
        else:
            attribute = MB_INVALID
        behavior = attribute & 0xFF
        bits = tile_bits[behavior] if behavior < len(tile_bits) else 0
        water = bool(bits & TILE_FLAG_SURFABLE)
        encounter = None
        if bits & TILE_FLAG_HAS_ENCOUNTERS:
            encounter = "water" if water else "land"
        return Tile(
            x=x, y=y, dx=x - player.x, dy=y - player.y, metatile=metatile, behavior=behavior,
            behavior_name=behavior_name(behavior), collision=collision, elevation=elevation,
            blocked=collision != 0, water=water, encounter=encounter, tall_grass=behavior in TALL_GRASS_BEHAVIORS,
            ledge=LEDGE_DIRECTIONS.get(behavior), door=behavior in DOOR_BEHAVIORS, warp=behavior in EXIT_BEHAVIORS,
            half_visible=dy == -VIEW_UP or dy == VIEW_DOWN,
        )

    def _tileset_attributes(self, tileset: int) -> bytes:
        """`struct Tileset` .metatileAttributes (offset 0x10): one u16 per metatile. ROM, read once."""
        if tileset not in self._attributes:
            pointer = _u32(_rom_bytes(tileset + 0x10, 4), 0)
            self._attributes[tileset] = _rom_bytes(pointer, 2 * METATILES_IN_PRIMARY)
        return self._attributes[tileset]

    def _tile_flags(self) -> bytes:
        """`sTileBitAttributes`, the ROM table of what each behaviour allows (encounters, surfing)."""
        if self._tile_bits is None:
            self._tile_bits = read_symbol("sTileBitAttributes")
        return self._tile_bits

    def _objects(self, player: PlayerState) -> list[SeenObject]:
        seen = []
        for event in get_map_objects():
            flags = event.flags
            if "isPlayer" in flags or "invisible" in flags:
                continue  # the player is not an object it sees; an invisible object is not seen at all
            x, y = event.current_coords
            if self.crop and not in_view(player.x, player.y, x, y):
                continue
            seen.append(SeenObject(
                kind=object_kind(event.graphics_id), x=x, y=y, dx=x - player.x,
                dy=y - player.y, local_id=event.local_id, graphics_id=event.graphics_id,
                facing=_OBJECT_FACING.get(event.facing_direction), elevation=event.current_elevation, source="object",
            ))
        return seen

    def _signs(self, player: PlayerState, signs: tuple) -> list[SeenObject]:
        """Interactable tiles of the map (`MapBgEvent` kind Script: signposts, PCs, bookshelves). Hidden
        items are never here: nobody can see them."""
        seen = []
        for (x, y), elevation in signs:
            if self.crop and not in_view(player.x, player.y, x, y):
                continue
            seen.append(SeenObject(kind="sign", x=x, y=y, dx=x - player.x, dy=y - player.y, local_id=-1,
                                   graphics_id=-1, facing=None, elevation=elevation, source="bg_event"))
        return seen

    # ------------------------------------------------------------------ the party (decoded here)
    def _party(self, problems: list[str]) -> list[MonSummary] | None:
        """The party, or None when it could not be read. ONE bad slot makes the whole party None (step
        1.1): a party returned without that slot would look one Pokemon short, and a reader that counts
        it (a catch's destination did, until step 1.1) would see a Pokemon leave and come back. Every bad
        slot is still named in `problems`."""
        count = min(read_symbol("gPlayerPartyCount", size=1)[0], PARTY_SIZE)
        raw = read_symbol("gPlayerParty", size=PARTY_MON_SIZE * PARTY_SIZE)
        party: list[MonSummary] = []
        torn = False
        for slot in range(count):
            data = raw[slot * PARTY_MON_SIZE:(slot + 1) * PARTY_MON_SIZE]
            try:
                mon = self._mon(slot, data)
            except Exception as error:  # noqa: BLE001 - one bad slot must not hide the others' problems
                mon = f"{type(error).__name__}: {error}"
            if isinstance(mon, str):
                problems.append(f"party slot {slot + 1}: {mon}")
                torn = True
                continue
            party.append(mon)
        return None if torn else party

    @staticmethod
    def _mon(slot: int, data: bytes) -> MonSummary | str:
        """One party slot: decoded by the AI's own `eyes/party.py`, then named from the game's data
        tables (`get_species_by_index`, `get_move_by_index`: lookups, no memory read)."""
        raw = decode_party_mon(bytes(data))
        if isinstance(raw, str):
            return raw
        species = get_species_by_index(raw.species_id)
        moves = []
        for index, move_id in enumerate(raw.moves):
            if move_id == 0:
                continue
            move = get_move_by_index(move_id)
            bonus = (raw.pp_bonuses >> (2 * index)) & 0x3
            moves.append(MoveSlot(name=move.name, type=move.type.name, power=move.base_power, pp=raw.pp[index],
                                  max_pp=move.pp + (move.pp * 20 * bonus) // 100))
        return MonSummary(
            slot=slot, species=species.name, dex=species.national_dex_number, level=raw.level, hp=raw.hp,
            max_hp=raw.max_hp, status=status_name(raw.status_bits), types=tuple(t.name for t in species.types),
            moves=tuple(moves), pid=raw.personality, ot_id=visible_id(raw.ot_id), is_egg=raw.is_egg,
            experience=raw.experience, stats=raw.stats,
        )

    # ------------------------------------------------------------------ the PC boxes
    @staticmethod
    def _storage() -> tuple[StoredMon, ...]:
        """Every Pokemon in the 14 PC boxes, from each slot's unencrypted header (no decryption: ~0.1 ms
        for 420 slots): the PID (identity), the VISIBLE OT id, whether it is an egg. One read of the boxes
        (33,600 bytes) through the save block's storage pointer `gPokemonStoragePtr`."""
        base = _u32(read_symbol("gPokemonStoragePtr", size=4), 0)
        count = STORAGE_BOXES * STORAGE_SLOTS
        raw = context.emulator.read_bytes(base + STORAGE_BOXES_AT, BOX_MON_SIZE * count)
        stored = []
        for index in range(count):
            at = index * BOX_MON_SIZE
            flags = raw[at + BOX_MON_FLAGS_AT]
            if not flags & BOX_MON_HAS_SPECIES:
                continue
            stored.append(StoredMon(box=index // STORAGE_SLOTS, slot=index % STORAGE_SLOTS, pid=_u32(raw, at),
                                    ot_id=visible_id(_u32(raw, at + 4)), is_egg=bool(flags & BOX_MON_IS_EGG)))
        return tuple(stored)

    # ------------------------------------------------------------------ bag, money, badges, Pokedex
    @staticmethod
    def _bag() -> BagSummary:
        bag = get_item_bag()
        balls = tuple((slot.item.name, slot.quantity) for slot in bag.poke_balls if slot.quantity > 0)
        healing = tuple(
            (slot.item.name, slot.quantity)
            for slot in list(bag.items) + list(bag.berries)
            if slot.quantity > 0 and "healing" in (slot.item.field_use.value, slot.item.battle_use.value)
        )
        return BagSummary(balls=balls, healing=healing, ball_total=sum(quantity for _, quantity in balls))

    @staticmethod
    def _progress() -> Progress:
        pokedex = get_pokedex()
        owned = tuple(sorted(species.national_dex_number for species in pokedex.owned_species))
        return Progress(
            money=get_player().money,
            badges=tuple(flag for flag in BADGE_FLAGS if get_event_flag(flag)),
            dex_owned=len(owned),
            dex_seen=len(pokedex.seen_species),
            owned_dex=owned,
            flags=tuple((name, bool(get_event_flag(name))) for name, _ in STORY_FLAGS),
        )

    # ------------------------------------------------------------------ battle
    def _battle(self) -> BattleView:
        """Both sides. A FOE battler is reported only if it is a Pokemon of THIS battle's enemy party, by
        identity (its PID is an occupied slot's of `gEnemyParty`, which the game fills before the battle
        begins): `gBattleMons` is filled a few frames INTO the battle (`src/battle_main.c`
        BattleIntroGetMonsData), and until then it holds the PREVIOUS battle's battlers. Measured 2026-10-07
        on `route116team.ss1`, walking into a wild Poochyena: for 9 frames of state BATTLE `gBattleMons`
        still held the previous battle's Abra (PID 85BC0236; gEnemyParty[0] was Poochyena, PID B11EC02B).
        A person sees no foe until it is sent out; the eyes report none either (step 1.1)."""
        state = get_battle_state()
        type_flags = _u32(read_symbol("gBattleTypeFlags", size=4), 0)
        trainer = bool(type_flags & BATTLE_TYPE_TRAINER)
        opponent = _u16(read_symbol("gTrainerBattleOpponent_A", size=2), 0) if trainer else None
        enemies = present_pids(read_symbol("gEnemyParty", size=PARTY_MON_SIZE * PARTY_SIZE))
        # BUILD STEP 4: each battler's POSITION (the framework's `active_battlers` lists a side's present battlers in
        # position order, 0 then 2 for the player, 1 then 3 for the foe, skipping an absent one: `gAbsentBattlerFlags`)
        count = read_symbol("gBattlersCount", size=1)[0]
        absent = read_symbol("gAbsentBattlerFlags", size=1)[0]
        own_at = [p for p in (0, 2) if p < count and not absent & (1 << p)]
        foe_at = [p for p in (1, 3) if p < count and not absent & (1 << p)]
        own = [self._battle_mon(mon, own=True, battler=at) for mon, at in zip(state.own_side.active_battlers, own_at)]
        foe = [self._battle_mon(mon, own=False, battler=at) for mon, at in zip(state.opponent.active_battlers, foe_at)
               if mon.personality_value in enemies]
        return BattleView(
            kind="trainer" if trainer else "wild",
            double=state.is_double_battle,
            type_flags=type_flags,
            opponent_trainer_id=opponent,
            own=tuple(own),
            foe=tuple(foe),
        )

    @staticmethod
    def _battle_mon(mon, own: bool, battler: int | None = None) -> BattleMon:
        """One battler. The player's OWN: its numbers and every move with PP (its healthbox and move menu
        show them). A FOE, as a person sees it (step 1.1): the HP BAR only (`hp`, `max_hp` None), and only
        the moves it has USED in this battle, with no PP (`eyes/view.py` foe_move_seen)."""
        hp, max_hp = mon.current_hp, mon.total_hp
        moves = tuple(
            MoveSlot(name=slot.move.name, type=slot.move.type.name, power=slot.move.base_power,
                     pp=slot.pp if own else None, max_pp=slot.total_pp if own else None)
            for slot in mon.moves if slot is not None and (own or foe_move_seen(slot.pp, slot.total_pp))
        )
        return BattleMon(
            species=mon.species.name, dex=mon.species.national_dex_number, level=mon.level,
            hp=hp if own else None, max_hp=max_hp if own else None, hp_bar=hp_bar_pixels(hp, max_hp),
            status=_BATTLE_STATUS.get(mon.status_permanent.name, mon.status_permanent.name),
            types=tuple(t.name for t in mon.types), moves=moves,
            pid=mon.personality_value if own else None,  # build step 4: which of the player's Pokemon is out
            battler=battler,  # build step 4: where it stands
        )


seal_module(__name__)
