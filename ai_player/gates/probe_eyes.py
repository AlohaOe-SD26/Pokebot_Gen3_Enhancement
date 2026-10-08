"""TEST SIDE: load a save state, read GROUND TRUTH through a second path, and run the AI's eyes on the same frame.

    py -3.12 ai_player/gates/probe_eyes.py --state PATH [--profile NAME] [--settle 1] [--repeat 30] [--behaviour]
    prints one line: PROBE {json}

WHY A SECOND READ PATH (build step 1 proofs): an Observation is only worth something if it matches the
game, and "the eyes agree with themselves" proves nothing. So every fact the live arms grade is read
HERE by different code from different memory where the game keeps a second copy, by this file's OWN
decoder of the game's bytes (the decomp's struct layouts and charmap, no framework reader) where it
keeps none, or by the game's BEHAVIOUR (a press in this throwaway emulator, never in an AI run):

  fact        the eyes read                                   ground truth here
  map         save block 1 `location` (group, number);       the live header `gMapHeader` matched byte for
              name: the framework's `MapLocation.map_name`    byte against the ROM's `gMapGroups` table,
                                                              walked by THIS file; the name: the ROM header's
                                                              region-map section -> `gRegionMapEntries` ->
                                                              decoded with THIS file's charmap (the decomp's
                                                              charmap.txt), not the framework's decode_string
  position    the player object's currentCoords - 7           save block 1 `pos` (the game's own copy)
  facing      the object's facingDirection nibble             overworld: the player SPRITE's animation
                                                              (`gSprites[spriteId].animNum`, written by the
                                                              animation code, ANIM_STD_FACE_* order S,N,W,E)
                                                              and its OAM hFlip bit (sAnim_FaceEast is the
                                                              west frame flipped): what is drawn. In a battle
                                                              the overworld sprites are freed: no second copy
  party       their OWN decryption of `gPlayerParty`          the framework's `get_party()` (its own
                                                              decryption): species, level, HP, PID, every
                                                              move with PP and max PP, the status; and the
                                                              raw level byte
  battle      the framework's `BattleState` (gBattleMons)     the SECOND COPY: the party struct with the
                                                              battler's PID (`gPlayerParty` / `gEnemyParty`,
                                                              the framework's decryption: species, level,
                                                              HP, status, moves with PP) and the species
                                                              table's types. (This file's raw parse of
                                                              `gBattleMons` is the same bytes as the eyes:
                                                              CONSISTENCY only.) In battle: `gMain.inBattle`
                                                              (a bit the eyes do not read; they read callback1)
  trainer id  `gTrainerBattleOpponent_A`                      the trainer who STARTED the battle:
                                                              `gSpecialVar_LastTalked` (its local id) -> the
                                                              ROM object template of the map -> its script ->
                                                              the `trainerbattle` command's trainer argument;
                                                              and the ROM's `gTrainers[id]` party (species,
                                                              levels) == the live `gEnemyParty`, its name
                                                              decoded by this file's charmap
  objects     the eyes' crop over `get_map_objects()`        this file's raw parse of `gObjectEvents`
                                                              and its own window test; and WHAT IS DRAWN:
                                                              each object's sprite on screen (`gSprites`),
                                                              relative to the player's drawn tile
  tiles       the LIVE grid `gBackupMapLayout`                the ROM's ORIGINAL layout through the ROM
                                                              header (`MapLayout.map`), decoded by THIS file
                                                              (metatile, collision, elevation), the behaviour
                                                              from the ROM tilesets' attribute arrays (this
                                                              file), the warps from the ROM header's
                                                              `MapEvents` (this file); ledges and doors from
                                                              the FRAMEWORK's own behaviour-name table
                                                              (`MapLocation.tile_type`), not the eyes' tables
  progress    framework readers (`get_player().money`,        this file's decode of the save blocks: money
              `get_event_flag`, `get_pokedex`, `get_item_bag`)  XOR the encryption key, flag bits at the
                                                              decomp's flag ids, the three Pokedex copies
                                                              (owned / seen in save block 2, seen1 / seen2
                                                              in save block 1), the bag pockets (quantities
                                                              XOR the key) named from the ROM's `gItems` and
                                                              classed by its use functions
  waits for   the script's native `WaitForAorBPress`, or      BEHAVIOUR (`--behaviour`): from a reload of the
  a button    ANY of the 32 `sTextPrinters` in state WAIT /   state, 300 frames with NO input, then ONE press
              CLEAR / SCROLL_START (not under autoScroll)     of A: "waits" = nothing moves without the press,
                                                              and the press moves it; frame by frame, before
                                                              and after the press, the text that is still
                                                              PRINTING (its `currentChar` advancing by
                                                              itself) is the not-waiting control, and the
                                                              frames that sit still until the press moved
                                                              it are waiting (`behaviour`)
  map header  the live `gMapHeader` == map (group, number)'s  FAULT (`header_guard`): another map's ROM
  check       ROM header (`host/eyes.py` _map_facts)          header written over `gMapHeader` in THIS
                                                              emulator must be refused
  window      `eyes/view.py` (derived from the decomp)        MEASURED: the player sprite's screen
                                                              rectangle (`gSprites`, `gSpriteCoordOffset*`)
                                                              and the camera pans

It also times the eyes: `--repeat N` advances one frame N times (no input) and times one look per frame.
It WRITES memory once, in its own throwaway emulator (`header_guard`, a fault arm), and reloads the state
right after; it presses only in `behaviour`. No AI run is involved in either.
This file is test side (`ai_player/gates/`): the purity gate forbids the play loop to import it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.host.launcher import resolve_build_root  # noqa: E402

DEFAULT_PROFILE = "ai-step0-fixture"
DIRECTIONS = {1: "down", 2: "up", 3: "left", 4: "right"}  # include/constants/global.h DIR_SOUTH..DIR_EAST
OBJECT_EVENT_SIZE = 0x24
SPRITE_SIZE = 0x44  # include/sprite.h struct Sprite
WINDOW_X, WINDOW_UP, WINDOW_DOWN = 7, 5, 5  # what this file's own window test uses (see `window_from_sprite`)

#: THIS file's charmap (pret/pokeemerald `charmap.txt`, the single characters a map, item or trainer
#: name uses), so a name read here is not the framework's `decode_string`.
CHARMAP: dict[int, str] = {
    0x00: " ", 0x1B: "é", 0x2D: "&", 0x2E: "+", 0x5C: "(", 0x5D: ")", 0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-",
    0xAF: "·", 0xB0: "…", 0xB1: "“", 0xB2: "”", 0xB3: "‘", 0xB4: "’", 0xB5: "♂", 0xB6: "♀", 0xB8: ",", 0xB9: "×",
    0xBA: "/", 0xF0: ":",
    **{0xA1 + i: str(i) for i in range(10)},
    **{0xBB + i: chr(ord("A") + i) for i in range(26)},
    **{0xD5 + i: chr(ord("a") + i) for i in range(26)},
}
#: `include/global.h` struct SaveBlock1 / SaveBlock2 / struct Pokedex offsets (pret/pokeemerald).
SB1_POS, SB1_LOCATION, SB1_MONEY = 0x00, 0x04, 0x490
SB1_POCKETS = {"items": (0x560, 30), "key_items": (0x5D8, 30), "poke_balls": (0x650, 16), "tms_hms": (0x690, 64),
               "berries": (0x790, 46)}
SB1_SEEN1, SB1_FLAGS, SB1_SEEN2 = 0x988, 0x1270, 0x3B24
SB2_TRAINER_ID, SB2_DEX_OWNED, SB2_DEX_SEEN, SB2_KEY = 0x0A, 0x18 + 0x10, 0x18 + 0x44, 0xAC
DEX_FLAG_BYTES, NATIONAL_DEX_COUNT = 52, 386
#: `include/constants/flags.h` (pret/pokeemerald), by VALUE: the eyes name their flags through the
#: framework's flag table; this file reads the bits at the decomp's own ids.
DECOMP_FLAG_IDS: dict[str, int] = {
    "RESCUED_BIRCH": 0x52, "SYS_POKEMON_GET": 0x860, "DEFEATED_RIVAL_ROUTE103": 0x82,
    "RECEIVED_POKEDEX_FROM_BIRCH": 0x860 + 0x84, "SYS_POKEDEX_GET": 0x861, "ADVENTURE_STARTED": 0x74,
    "HIDE_PETALBURG_CITY_WALLYS_MOM": 0x2D8, "SYS_B_DASH": 0x860 + 0x60, "DEFEATED_RUSTBORO_GYM": 0x4F0,
    **{f"BADGE0{n}_GET": 0x860 + 6 + n for n in range(1, 9)},
}
#: `include/item.h` struct Item (0x2C bytes): name @0, pocket @0x1A, fieldUseFunc @0x1C, battleUsage
#: @0x20, battleUseFunc @0x24. `include/data.h` struct Trainer (0x28 bytes): partyFlags @0, name @4,
#: partySize @0x20, party @0x24; a party member is 8 bytes (16 with custom moves): level @2, species @4.
ITEM_SIZE, TRAINER_SIZE, TRAINERS_COUNT = 0x2C, 0x28, 855
F_TRAINER_PARTY_CUSTOM_MOVESET = 1
#: `data/script_cmd_table.inc`: SCR_OP_TRAINERBATTLE = 0x5c; `asm/macros/event.inc` trainerbattle:
#: .byte op, .byte type, .2byte trainer, .2byte local_id, ...
SCR_OP_TRAINERBATTLE = 0x5C
#: The player's overworld animation tables (`src/data/object_events/object_event_anims.h`): every one
#: starts with ANIM_STD_FACE_SOUTH, _NORTH, _WEST, _EAST and repeats that order in fours.
PLAYER_ANIM_TABLES = ("sAnimTable_BrendanMayNormal", "sAnimTable_AcroBike", "sAnimTable_Surfing", "sAnimTable_Standard")
ANIM_ORDER = ("down", "up", "left", "right")
#: The FRAMEWORK's own behaviour names (`modules/map.py` _get_tile_type_name) for a ledge and a door:
#: the truth for those two is that table, not the eyes' `eyes/view.py` one.
FRAMEWORK_LEDGES = {"Jump East": "east", "Jump West": "west", "Jump North": "north", "Jump South": "south",
                    "Jump North/East": "northeast", "Jump North/West": "northwest", "Jump South/East": "southeast",
                    "Jump South/West": "southwest"}
FRAMEWORK_DOORS = frozenset({"Door Warp", "Non-Animated Door", "Petalburg Gym Door", "Water Door"})


def own_text(data) -> str:
    """A Gen 3 string, decoded with THIS file's charmap, up to the terminator 0xFF."""
    out = []
    for byte in bytes(data):
        if byte == 0xFF:
            break
        out.append(CHARMAP.get(byte, f"<{byte:02X}>"))
    return "".join(out)


def _u16(data, offset: int) -> int:
    return int.from_bytes(bytes(data[offset:offset + 2]), "little")


def _s16(data, offset: int) -> int:
    return int.from_bytes(bytes(data[offset:offset + 2]), "little", signed=True)


def _u32(data, offset: int) -> int:
    return int.from_bytes(bytes(data[offset:offset + 4]), "little")


def boot(profile_name: str):
    build_root = resolve_build_root()
    sys.path.insert(0, str(build_root))
    from modules.context import context
    from modules.game import set_rom
    from modules.libmgba import LibmgbaEmulator
    from modules.profiles import load_profile_by_name

    profile = load_profile_by_name(profile_name)
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)
    context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)
    context.audio = False
    context.video = False
    context.emulation_speed = 0
    return context


def _s32(data, offset: int) -> int:
    return int.from_bytes(bytes(data[offset:offset + 4]), "little", signed=True)


def _symbol(address: int) -> str | None:
    from modules.game import get_symbol_name_before

    return get_symbol_name_before(address, pretty_name=True) if address else None


def sprite_id_of(event) -> int:
    """`struct ObjectEvent` spriteId @4."""
    return event[4]


def drawn_tile(sprite) -> tuple[int, int] | None:
    """Where a map object's TILE is drawn: the screen top-left of the bottom 16 x 16 of its sprite
    (`include/sprite.h` struct Sprite: x @0x20, y @0x22, x2 @0x24, y2 @0x26, centerToCornerVecX/Y @0x28/0x29,
    inUse bit 0 and coordOffsetEnabled bit 1 of @0x3E; drawn at x + x2 + centerToCornerVecX +
    gSpriteCoordOffsetX). None if the sprite is not in use."""
    from modules.memory import read_symbol

    if not sprite[0x3E] & 0x01:
        return None
    x, y = _s16(sprite, 0x20), _s16(sprite, 0x22)
    x2, y2 = _s16(sprite, 0x24), _s16(sprite, 0x26)
    c2c_x = int.from_bytes(bytes(sprite[0x28:0x29]), "little", signed=True)
    c2c_y = int.from_bytes(bytes(sprite[0x29:0x2A]), "little", signed=True)
    offset = bool(sprite[0x3E] & 0x02)
    off_x = _s16(read_symbol("gSpriteCoordOffsetX", size=2), 0) if offset else 0
    off_y = _s16(read_symbol("gSpriteCoordOffsetY", size=2), 0) if offset else 0
    left, top = x + x2 + c2c_x + off_x, y + y2 + c2c_y + off_y
    width, height = -2 * c2c_x, -2 * c2c_y
    return left + (width - 16) // 2, top + height - 16


def printer_text(context, current_char: int) -> dict:
    """The text a printer is showing, up to where it has got: the RAM buffer its `currentChar` points
    into (named by the symbol table), from that buffer's start, decoded by THIS file's charmap, and the
    two bytes it consumed last (FC 09 = EXT_CTRL_CODE_BEGIN, EXT_CTRL_CODE_PAUSE_UNTIL_PRESS)."""
    from modules.game import get_symbol, get_symbol_name_before

    name = get_symbol_name_before(current_char, pretty_name=True)
    try:
        start = get_symbol(name)[0]
    except Exception:  # noqa: BLE001 - a pointer into ROM or no symbol
        return {"buffer": name, "text": None, "last_two_bytes": None}
    length = max(0, min(current_char - start, 0x200))
    raw = bytes(context.emulator.read_bytes(start, length)) if length else b""
    return {"buffer": name, "text": " | ".join(own_text(part) for part in raw.split(b"\xff")),
            "last_two_bytes": bytes(context.emulator.read_bytes(current_char - 2, 2)).hex()}


class RomMaps:
    """The ROM's map table, walked by THIS file: `gMapGroups` (an array of pointers to arrays of
    pointers to `struct MapHeader`), each header's `MapLayout` and `MapEvents`, and the tilesets'
    metatile attributes (`include/global.fieldmap.h`). Everything here is ROM, read on demand."""

    def __init__(self, emulator) -> None:
        from modules.game import get_symbol

        self.emulator = emulator
        self.groups = get_symbol("gMapGroups")[0]
        self._headers: dict[tuple[int, int], bytes] = {}
        self._layouts: dict[tuple[int, int], dict] = {}
        self._events: dict[tuple[int, int], dict] = {}
        self._attributes: dict[int, bytes] = {}

    def header(self, key: tuple[int, int]) -> bytes:
        if key not in self._headers:
            group, number = key
            table = _u32(self.emulator.read_bytes(self.groups + 4 * group, 4), 0)
            pointer = _u32(self.emulator.read_bytes(table + 4 * number, 4), 0)
            self._headers[key] = bytes(self.emulator.read_bytes(pointer, 0x1C))
        return self._headers[key]

    def name(self, key: tuple[int, int]) -> str:
        """The region-map section of the ROM header -> `gRegionMapEntries[mapsec].name` (struct
        RegionMapLocation: x, y, width, height, then the name pointer @4), decoded by THIS file."""
        from modules.memory import read_symbol

        entry = read_symbol("gRegionMapEntries", self.header(key)[0x14] * 8, 8)
        return own_text(self.emulator.read_bytes(_u32(entry, 4), 32))

    def layout(self, key: tuple[int, int]) -> dict:
        if key not in self._layouts:
            raw = self.emulator.read_bytes(_u32(self.header(key), 0), 24)
            self._layouts[key] = {"width": _s32(raw, 0), "height": _s32(raw, 4), "map": _u32(raw, 12),
                                  "primary": _u32(raw, 16), "secondary": _u32(raw, 20)}
        return self._layouts[key]

    def events(self, key: tuple[int, int]) -> dict:
        if key not in self._events:
            pointer = _u32(self.header(key), 4)
            raw = self.emulator.read_bytes(pointer, 20)
            templates, warps = [], []
            if raw[0] and _u32(raw, 4):
                data = self.emulator.read_bytes(_u32(raw, 4), 24 * raw[0])
                for i in range(raw[0]):
                    t = data[24 * i:24 * (i + 1)]
                    templates.append({"local_id": t[0], "graphics_id": t[1], "x": _s16(t, 4), "y": _s16(t, 6),
                                      "script": _u32(t, 0x10), "flag": _u16(t, 0x14)})
            if raw[1] and _u32(raw, 8):
                data = self.emulator.read_bytes(_u32(raw, 8), 8 * raw[1])
                warps = [(_s16(data, 8 * i), _s16(data, 8 * i + 2)) for i in range(raw[1])]
            self._events[key] = {"templates": templates, "warps": warps}
        return self._events[key]

    def tile(self, key: tuple[int, int], x: int, y: int) -> dict | None:
        """One block of the ROM layout (`MapLayout.map`, u16 per tile: metatile id bits 0-9, collision
        10-11, elevation 12-15) and its behaviour (the low byte of the tileset's attribute)."""
        layout = self.layout(key)
        if not (0 <= x < layout["width"] and 0 <= y < layout["height"]):
            return None
        block = _u16(self.emulator.read_bytes(layout["map"] + 2 * (y * layout["width"] + x), 2), 0)
        metatile = block & 0x3FF
        if metatile < 512:
            tileset, index = layout["primary"], metatile
        else:
            tileset, index = layout["secondary"], metatile - 512
        if tileset not in self._attributes:
            pointer = _u32(self.emulator.read_bytes(tileset + 0x10, 4), 0)
            self._attributes[tileset] = bytes(self.emulator.read_bytes(pointer, 2 * 512))
        return {"metatile": metatile, "collision": (block >> 10) & 3, "elevation": (block >> 12) & 0xF,
                "behavior": _u16(self._attributes[tileset], 2 * index) & 0xFF}


def truth(context) -> dict:
    """Ground truth through the second path (see the module docstring)."""
    from modules.map import get_map_data
    from modules.map_data import MapRSE
    from modules.memory import read_symbol
    from modules.pokemon import Pokemon, get_species_by_index, get_type_by_index
    from modules.pokemon_party import get_party

    emulator = context.emulator
    out: dict = {"problems": []}
    avatar = read_symbol("gPlayerAvatar", size=0x24)
    object_id = avatar[5]
    events = read_symbol("gObjectEvents", size=OBJECT_EVENT_SIZE * 16)
    me = events[object_id * OBJECT_EVENT_SIZE:(object_id + 1) * OBJECT_EVENT_SIZE]
    save_block_1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    save_block_2 = _u32(read_symbol("gSaveBlock2Ptr", size=4), 0)
    sb1 = emulator.read_bytes(save_block_1, 8)
    trainer_id = _u32(emulator.read_bytes(save_block_2 + SB2_TRAINER_ID, 4), 0)
    x, y = _s16(sb1, SB1_POS), _s16(sb1, SB1_POS + 2)  # struct SaveBlock1: pos @0x00
    rom = RomMaps(emulator)

    # WHICH MAP IS LOADED, identified without the save block: the live header `gMapHeader` is a copy of
    # one map's ROM header, so find the map(s) of the ROM's own table (`gMapGroups`, walked by THIS file;
    # the (group, number) pairs listed by the framework's map enum) whose header is byte-identical. (The
    # player OBJECT's mapGroup/mapNum is NOT a second copy: it keeps the map the object was created on,
    # e.g. Rustboro after walking across the connection to Route 116. Recorded only as that warning,
    # measured on route116team.ss1.) The NAME: the ROM header's region-map section, decoded here.
    live_header = bytes(read_symbol("gMapHeader", size=0x1C))
    matches = []
    for member in MapRSE:
        key = tuple(member.value)
        try:
            if rom.header(key) == live_header and list(key) not in matches:
                matches.append(list(key))
        except Exception:  # noqa: BLE001 - a map the table does not hold
            continue
    here_key = tuple(matches[0]) if len(matches) == 1 else None
    out["map"] = {
        "header_matches": matches, "group": here_key[0] if here_key else None, "number": here_key[1] if here_key else None,
        "name": rom.name(here_key) if here_key else "?", "mapsec": live_header[0x14],
        "framework_name_NOT_TRUTH": get_map_data(here_key, (x, y)).map_name if here_key else "?",
        "player_object_map_NOT_TRUTH": [me[0x0A], me[0x09]],
    }
    out["position"] = [x, y]
    out["player_object_active"] = bool(me[0] & 1)
    out["trainer_id"] = trainer_id

    # FACING: what is DRAWN. The player's sprite (`gSprites[spriteId]`, struct Sprite: oam @0, anims
    # @0x08, animNum @0x2A, inUse bit 0 of @0x3E) runs the animation the object's facing chose; in the
    # player's tables ANIM_STD_FACE_SOUTH/NORTH/WEST/EAST = 0..3 and every later group of four keeps that
    # order, and sAnim_FaceEast is the WEST frame with hFlip (OAM attr1 bit 12). A battle frees the
    # overworld sprites: then there is no second copy, and `facing` is None (the object's byte is kept
    # only as `facing_object_byte_NOT_TRUTH`).
    sprite_id = me[4]
    sprite = read_symbol("gSprites", sprite_id * SPRITE_SIZE, SPRITE_SIZE)
    table = _symbol(_u32(sprite, 0x08))
    anim = sprite[0x2A]
    usable = bool(_u16(sprite, 0x3E) & 1) and table in PLAYER_ANIM_TABLES
    out["facing"] = ANIM_ORDER[anim % 4] if usable else None
    out["facing_sprite"] = {"sprite_id": sprite_id, "anim_table": table, "anim_num": anim,
                            "oam_hflip": bool(_u16(sprite, 2) & (1 << 12)), "usable": usable}
    out["facing_object_byte_NOT_TRUTH"] = DIRECTIONS.get(me[0x18] & 0x0F, "?")

    # objects: raw parse of gObjectEvents, this file's own window test, and WHAT IS DRAWN: each object's
    # sprite (`gSprites[spriteId]`) placed on screen, relative to the player's drawn tile, in tiles. The
    # sprite is a second copy of the position (the animation code moves it; the object holds coordinates).
    # Mid-step it lies between previousCoords (@0x14) and currentCoords (@0x10).
    player_drawn = drawn_tile(read_symbol("gSprites", sprite_id_of(me) * SPRITE_SIZE, SPRITE_SIZE))
    objects = []
    for slot in range(16):
        event = events[slot * OBJECT_EVENT_SIZE:(slot + 1) * OBJECT_EVENT_SIZE]
        flags = _u32(event, 0)
        if not flags & 1 or flags & (1 << 16):  # active; isPlayer
            continue
        ox, oy = _u16(event, 0x10) - 7, _u16(event, 0x12) - 7
        px, py = _u16(event, 0x14) - 7, _u16(event, 0x16) - 7
        dx, dy = ox - x, oy - y
        drawn = drawn_tile(read_symbol("gSprites", event[4] * SPRITE_SIZE, SPRITE_SIZE))
        objects.append({
            "slot": slot, "local_id": event[8], "graphics_id": event[5], "x": ox, "y": oy, "dx": dx, "dy": dy,
            "previous_dx_dy": [px - x, py - y], "invisible": bool(flags & (1 << 13)),
            "on_screen": -WINDOW_X <= dx <= WINDOW_X and -WINDOW_UP <= dy <= WINDOW_DOWN,
            "drawn": None if drawn is None or player_drawn is None else {
                "screen_tile_xy": [drawn[0], drawn[1]],
                "dx": (drawn[0] - player_drawn[0]) / 16, "dy": (drawn[1] - player_drawn[1]) / 16,
                "on_screen_240x160": 0 <= drawn[0] and drawn[0] + 16 <= 240 and drawn[1] + 16 > 0 and drawn[1] < 160,
            },
        })
    out["objects"] = objects
    out["player_drawn_tile"] = list(player_drawn) if player_drawn else None

    # TILES. Per tile of the window, two truths, neither of them the eyes' code or memory:
    #  * OWN: the ROM's ORIGINAL layout through the ROM header (`RomMaps.tile`: metatile, collision,
    #    elevation, behaviour) and the ROM header's warps, decoded by THIS file;
    #  * FRAMEWORK: `MapLocation` (its own decoder of the same ROM layout, and its own attribute and
    #    tile-flag lookups): collision, elevation, encounters, surfable, the behaviour's NAME, from which
    #    a ledge (`FRAMEWORK_LEDGES`) and a door (`FRAMEWORK_DOORS`) are read.
    # The eyes read the LIVE grid (`gBackupMapLayout`) and their own tables. Outside the map the screen
    # shows the NEXT map: the game copies its edge into the live grid (`src/fieldmap.c`
    # Fill{South,North,West,East}Connection), so such a tile is checked against the neighbour's own ROM
    # tile: south (x - offset, y - height), north (x - offset, neighbour height + y), west (neighbour
    # width + x, y - offset), east (x - width, y - offset). Corner tiles are not checked.
    tiles = []
    here = get_map_data(here_key, (0, 0)) if here_key else None
    width, height = here.map_size if here is not None else (0, 0)
    connections = {c.direction: c for c in here.connections} if here is not None else {}
    for dy in range(-WINDOW_UP, WINDOW_DOWN + 1):
        for dx in range(-WINDOW_X, WINDOW_X + 1):
            tx, ty = x + dx, y + dy
            inside_x, inside_y = 0 <= tx < width, 0 <= ty < height
            source, where, at = "map", here_key, (tx, ty)
            if here is None:
                continue
            if not (inside_x and inside_y):
                side = ("West" if tx < 0 else "East") if inside_y and not inside_x else (
                    ("North" if ty < 0 else "South") if inside_x and not inside_y else None)
                connection = connections.get(side) if side else None
                if connection is None:
                    continue
                where = (connection.destination_map_group, connection.destination_map_number)
                neighbour_w, neighbour_h = get_map_data(where, (0, 0)).map_size
                at = {"South": (tx - connection.offset, ty - height), "North": (tx - connection.offset, neighbour_h + ty),
                      "West": (neighbour_w + tx, ty - connection.offset), "East": (tx - width, ty - connection.offset)}[side]
                if not (0 <= at[0] < neighbour_w and 0 <= at[1] < neighbour_h):
                    continue
                source = f"connection {side} -> map {where} tile {at}"
            location = get_map_data(where, at)
            own = rom.tile(where, *at)
            tiles.append({"x": tx, "y": ty, "collision": location.collision, "elevation": location.elevation,
                          "encounters": location.has_encounters, "surfable": location.is_surfable,
                          "tall_grass": location.tile_type in ("Tall Grass", "Long Grass"), "tile_type": location.tile_type,
                          "ledge": FRAMEWORK_LEDGES.get(location.tile_type), "door": location.tile_type in FRAMEWORK_DOORS,
                          "own": own, "warp": tuple(at) in set(rom.events(where)["warps"]),
                          "warp_of_this_map": source == "map", "source": source})
    out["tiles"] = tiles

    # the screen: raw bytes, read by this file
    status = read_symbol("sGlobalScriptContextStatus", size=1)[0]
    script = read_symbol("sGlobalScriptContext", size=8)
    # The active TASKS (struct Task, 40 bytes: func @0, isActive @4), parsed here: the message box is drawn
    # by `Task_DrawFieldMessage`, a second sign of an open text box that the eyes do not use.
    raw_tasks = read_symbol("gTasks", size=40 * 16)
    task_names = sorted({
        _symbol(_u32(raw_tasks, 40 * i) - 1) for i in range(16) if raw_tasks[40 * i + 4] and _u32(raw_tasks, 40 * i)
    })
    main_struct = read_symbol("gMain", size=0x43A)
    party_menu = read_symbol("gPartyMenu", size=0x14)
    out["screen"] = {
        # gMain (`include/main.h` struct Main): callback1 @0, callback2 @4, and the `inBattle` BIT (bit 1 of
        # @0x439, set in CB2_InitBattleInternal, cleared when the battle frees its data): the eyes read
        # neither that bit nor this file's symbol lookups.
        "callback1": _symbol(_u32(main_struct, 0) - 1), "callback2": _symbol(_u32(main_struct, 4) - 1),
        "in_battle_bit": bool(main_struct[0x439] & 0x02),
        # `include/party_menu.h` struct PartyMenu: exitCallback @0, task @4, menuType bits 0-3 of @8
        # (`include/constants/party_menu.h`: 0 FIELD, 1 IN_BATTLE, ...). It keeps its last values after the
        # menu closes, so it says WHICH party menu, not WHETHER one is open (callback2 says that).
        "party_menu_type": party_menu[8] & 0x0F, "party_menu_task": _symbol(_u32(party_menu, 4) - 1),
        "tasks": task_names,
        "message_box_mode_SAME_BYTE_AS_EYES": read_symbol("sFieldMessageBoxMode", size=1)[0],
        "script_status": status, "script_mode": script[1], "script_native": _symbol(_u32(script, 4)),
        "text_printer_active_state_SAME_BYTES_AS_EYES": list(read_symbol("sTextPrinters", 0x1B, 2)),
        # `gTextFlags` byte 0 (bit-fields canABSpeedUpPrint, useAlternateDownArrow, autoScroll,
        # forceMidTextSpeed): measured here to pin the bit order the eyes assume (autoScroll = bit 2)
        "text_flags": read_symbol("gTextFlags", size=1)[0],
        # every active text printer, what it shows (this file's charmap) and the bytes it consumed last
        "active_printers": [
            {"printer": i, "state": p[0x1C], "current_char": _u32(p, 0), **printer_text(context, _u32(p, 0))}
            for i, p in ((i, read_symbol("sTextPrinters", 0x24 * i, 0x24)) for i in range(32)) if p[0x1B]
        ],
    }

    # party: the framework's own reader (independent decryption) + the raw level byte; the moves with
    # their PP and max PP and the status from the same reader (the eyes decrypt with their own code)
    party = []
    try:
        raw_party = read_symbol("gPlayerParty", size=600)
        for mon in get_party():
            raw = raw_party[mon.index * 100:(mon.index + 1) * 100]
            party.append({"slot": mon.index, "species": mon.species.name, "dex": mon.species.national_dex_number,
                          "level": mon.level, "raw_level": raw[84], "hp": mon.current_hp, "max_hp": mon.total_hp,
                          "pid": mon.personality_value, "ot_id": _u32(raw, 4), "is_egg": mon.is_egg,
                          "status": mon.status_condition.name, "moves": framework_moves(mon)})
    except Exception as error:  # noqa: BLE001
        out["problems"].append(f"party: {type(error).__name__}: {error}")
    out["party"] = party

    out["progress"] = own_progress(context, save_block_1, save_block_2)

    # battle: raw gBattleMons (struct BattlePokemon, 0x58 each: species @0, types @0x21/0x22, level @0x2A,
    # hp @0x28, maxHP @0x2C, personality @0x48), the battler count, absent flags and party indexes. The
    # raw parse is the SAME bytes the eyes read (CONSISTENCY). The TRUTH is the SECOND COPY the game keeps:
    # the party struct of the Pokemon with the SAME personality value (identity, never a slot: CLAUDE.md
    # rule 3), in `gPlayerParty` for the own side and `gEnemyParty` for the foe, decrypted by the
    # framework's `Pokemon`; its types from the species table (data, not gBattleMons). The battle engine
    # writes HP, PP and status back to that copy as they change (`BtlController_EmitSetMonData`).
    type_flags = _u32(read_symbol("gBattleTypeFlags", size=4), 0)
    count = read_symbol("gBattlersCount", size=1)[0]
    absent = read_symbol("gAbsentBattlerFlags", size=1)[0]
    indexes = read_symbol("gBattlerPartyIndexes", size=8)
    mons = read_symbol("gBattleMons", size=0x58 * 4)
    enemy_raw = read_symbol("gEnemyParty", size=600)
    enemy_mons = [Pokemon(enemy_raw[slot * 100:(slot + 1) * 100]) for slot in range(6)]
    player_mons = [Pokemon(raw_party[slot * 100:(slot + 1) * 100]) for slot in range(6)] if party else []
    battlers = []
    for battler in range(min(count, 4)):
        data = mons[battler * 0x58:(battler + 1) * 0x58]
        if absent & (1 << battler):
            continue
        species = get_species_by_index(_u16(data, 0))
        types = []
        for index in (data[0x21], data[0x22]):
            name = get_type_by_index(index).name
            if name not in types:
                types.append(name)
        side = "own" if battler % 2 == 0 else "foe"
        pid = _u32(data, 0x48)
        copies = [(slot, mon) for slot, mon in enumerate(player_mons if side == "own" else enemy_mons)
                  if not mon.is_empty and mon.is_valid and mon.personality_value == pid]
        second = None
        if len(copies) == 1:
            slot, mon = copies[0]
            second = {"party": "gPlayerParty" if side == "own" else "gEnemyParty", "slot": slot, "species": mon.species.name,
                      "level": mon.level, "hp": mon.current_hp, "max_hp": mon.total_hp, "status": mon.status_condition.name,
                      "types": [t.name for t in mon.species.types], "moves": framework_moves(mon)}
        battlers.append({"battler": battler, "side": side, "species": species.name,
                         "level": data[0x2A], "hp": _u16(data, 0x28), "max_hp": _u16(data, 0x2C), "types": types,
                         "party_index": _u16(indexes, 2 * battler), "pid": pid, "copies_with_this_pid": len(copies),
                         "second_copy": second})
    enemy = []
    for mon in enemy_mons:
        if not mon.is_empty and mon.is_valid:
            enemy.append([mon.species.name, mon.level])
    out["battle"] = {
        "type_flags": type_flags, "trainer": bool(type_flags & (1 << 3)),
        "opponent_trainer_id_SAME_BYTES_AS_EYES": _u16(read_symbol("gTrainerBattleOpponent_A", size=2), 0),
        "battlers": battlers, "enemy_party": enemy,
        # (the type flags keep the LAST battle's value on the overworld; only a battle running now counts)
        "trainer_truth": trainer_truth(context, rom, here_key, events, enemy)
        if type_flags & (1 << 3) and main_struct[0x439] & 0x02 else None,
    }
    return out


def framework_moves(mon) -> list[list]:
    """[name, pp, max pp] per move, from the framework's `Pokemon.moves` (its decryption, its PP-bonus maths)."""
    return [[slot.move.name, slot.pp, slot.total_pp] for slot in mon.moves if slot is not None]


def own_progress(context, save_block_1: int, save_block_2: int) -> dict:
    """Money, flags, the Pokedex and the bag, decoded by THIS file from the save blocks (offsets in the
    module constants, from pret/pokeemerald `include/global.h`)."""
    from modules.memory import read_symbol

    emulator = context.emulator
    key = _u32(emulator.read_bytes(save_block_2 + SB2_KEY, 4), 0)
    money = _u32(emulator.read_bytes(save_block_1 + SB1_MONEY, 4), 0) ^ key
    flags = emulator.read_bytes(save_block_1 + SB1_FLAGS, 300)
    flag_values = {name: bool(flags[fid // 8] >> (fid % 8) & 1) for name, fid in DECOMP_FLAG_IDS.items()}
    # The Pokedex (`src/pokedex.c` GetSetPokedexFlag): SEEN needs the bit in all three copies (save block 2
    # `seen`, save block 1 `seen1` and `seen2`); OWNED needs it in `owned` and in all three seen copies.
    owned_bits = emulator.read_bytes(save_block_2 + SB2_DEX_OWNED, DEX_FLAG_BYTES)
    seen_bits = emulator.read_bytes(save_block_2 + SB2_DEX_SEEN, DEX_FLAG_BYTES)
    seen1 = emulator.read_bytes(save_block_1 + SB1_SEEN1, DEX_FLAG_BYTES)
    seen2 = emulator.read_bytes(save_block_1 + SB1_SEEN2, DEX_FLAG_BYTES)

    def bit(data, index: int) -> bool:
        return bool(data[index // 8] >> (index % 8) & 1)

    seen = [i + 1 for i in range(NATIONAL_DEX_COUNT) if all(bit(b, i) for b in (seen_bits, seen1, seen2))]
    owned = [i + 1 for i in range(NATIONAL_DEX_COUNT) if all(bit(b, i) for b in (owned_bits, seen_bits, seen1, seen2))]
    owned_bit_only = sum(1 for i in range(NATIONAL_DEX_COUNT) if bit(owned_bits, i))
    # The bag: `struct ItemSlot` {u16 itemId; u16 quantity}, the quantity XOR the key's low half; each item
    # named from the ROM's `gItems` (this file's charmap) and classed by the ROM's own use functions.
    pockets: dict[str, list] = {}
    for pocket, (offset, slots) in SB1_POCKETS.items():
        data = emulator.read_bytes(save_block_1 + offset, 4 * slots)
        entries = []
        for i in range(slots):
            item, quantity = _u16(data, 4 * i), _u16(data, 4 * i + 2) ^ (key & 0xFFFF)
            if item == 0:
                continue
            entry = read_symbol("gItems", item * ITEM_SIZE, ITEM_SIZE)
            entries.append({"id": item, "name": own_text(entry[:14]), "quantity": quantity, "rom_pocket": entry[0x1A],
                            "field_use": _symbol(_u32(entry, 0x1C)), "battle_usage": entry[0x20],
                            "battle_use": _symbol(_u32(entry, 0x24))})
        pockets[pocket] = entries
    return {"money": money, "flags": flag_values, "dex_owned": len(owned), "dex_seen": len(seen), "owned_dex": owned,
            "dex_owned_bit_only": owned_bit_only, "bag": pockets}


def trainer_truth(context, rom: RomMaps, here_key, events: bytes, enemy: list) -> dict:
    """WHO started this battle, read WITHOUT `gTrainerBattleOpponent_A`: `src/battle_setup.c`
    ConfigureAndSetUpOneTrainerBattle sets `gSelectedObjectEvent` to the trainer's object and
    `gSpecialVar_LastTalked` to its local id, then runs its script, whose first command is
    `trainerbattle type, TRAINER_ID, ...`. So: the ROM object template of this map with that local id ->
    its script (ROM) -> the trainer argument. Then the ROM's `gTrainers[id]` (its name, by this file's
    charmap, and its party) against the LIVE `gEnemyParty`, and how many of the 855 trainers have that
    exact party (a party alone may not identify a trainer)."""
    from modules.memory import read_symbol
    from modules.pokemon import get_species_by_index

    emulator = context.emulator
    out: dict = {}
    last_talked = _u16(read_symbol("gSpecialVar_LastTalked", size=2), 0)
    selected = read_symbol("gSelectedObjectEvent", size=1)[0]
    out["last_talked_local_id"] = last_talked
    out["selected_object_local_id"] = events[selected * OBJECT_EVENT_SIZE + 8] if selected < 16 else None
    templates = [t for t in rom.events(here_key)["templates"] if t["local_id"] == last_talked] if here_key else []
    out["templates_with_that_local_id"] = len(templates)
    script_trainer = None
    if len(templates) == 1:
        script = emulator.read_bytes(templates[0]["script"], 6)
        out["script"] = {"address": templates[0]["script"], "symbol": _symbol(templates[0]["script"]),
                         "bytes": bytes(script).hex(), "op": script[0], "type": script[1]}
        if script[0] == SCR_OP_TRAINERBATTLE:
            script_trainer = _u16(script, 2)
    out["trainer_from_script"] = script_trainer

    def rom_trainer(tid: int) -> tuple[str, list]:
        entry = read_symbol("gTrainers", tid * TRAINER_SIZE, TRAINER_SIZE)
        size, pointer = entry[0x20], _u32(entry, 0x24)
        step = 16 if entry[0] & F_TRAINER_PARTY_CUSTOM_MOVESET else 8
        data = emulator.read_bytes(pointer, step * size) if size and pointer else b""
        party = [[get_species_by_index(_u16(data, step * i + 4)).name, data[step * i + 2]] for i in range(size)]
        return own_text(entry[4:15]), party

    if script_trainer is not None:
        name, party = rom_trainer(script_trainer)
        out["rom_trainer"] = {"id": script_trainer, "name": name, "party": party}
        out["trainers_with_this_party"] = [tid for tid in range(TRAINERS_COUNT) if rom_trainer(tid)[1] == enemy]
    return out


def window_from_sprite(context) -> dict:
    """MEASURE where the player is drawn: its sprite's top-left on screen (`include/sprite.h` struct Sprite,
    drawn at x + x2 + centerToCornerVecX + gSpriteCoordOffsetX when coordOffsetEnabled), and the camera's
    pans and pixel offsets. The player's TILE is the bottom 16 x 16 of its 16 x 32 sprite."""
    from modules.memory import read_symbol

    avatar = read_symbol("gPlayerAvatar", size=0x24)
    event = read_symbol("gObjectEvents", avatar[5] * OBJECT_EVENT_SIZE, OBJECT_EVENT_SIZE)
    sprite_id = event[4]
    sprite = read_symbol("gSprites", sprite_id * SPRITE_SIZE, SPRITE_SIZE)
    x, y = _s16(sprite, 0x20), _s16(sprite, 0x22)
    x2, y2 = _s16(sprite, 0x24), _s16(sprite, 0x26)
    c2c_x = int.from_bytes(bytes(sprite[0x28:0x29]), "little", signed=True)
    c2c_y = int.from_bytes(bytes(sprite[0x29:0x2A]), "little", signed=True)
    offset_enabled = bool(sprite[0x3E] & 0x02)
    off_x = _s16(read_symbol("gSpriteCoordOffsetX", size=2), 0)
    off_y = _s16(read_symbol("gSpriteCoordOffsetY", size=2), 0)
    left = x + x2 + c2c_x + (off_x if offset_enabled else 0)
    top = y + y2 + c2c_y + (off_y if offset_enabled else 0)
    width, height = -2 * c2c_x, -2 * c2c_y
    tile_left, tile_top = left + (width - 16) // 2, top + height - 16
    camera = read_symbol("sFieldCameraOffset", size=8)
    pan_x = _s16(read_symbol("sHorizontalCameraPan", size=2), 0)
    pan_y = _s16(read_symbol("sVerticalCameraPan", size=2), 0)
    # Every map column whose 16 px land on the 240 px screen, every row with any of its 16 px on 160 px.
    columns = [d for d in range(-16, 17) if 0 <= tile_left + 16 * d and tile_left + 16 * d + 16 <= 240]
    rows = [d for d in range(-16, 17) if tile_top + 16 * d + 16 > 0 and tile_top + 16 * d < 160]
    half_rows = [d for d in rows if tile_top + 16 * d < 0 or tile_top + 16 * d + 16 > 160]
    return {
        "sprite_id": sprite_id, "sprite_xy": [x, y], "sprite_xy2": [x2, y2], "center_to_corner": [c2c_x, c2c_y],
        "coord_offset_enabled": offset_enabled, "sprite_coord_offset": [off_x, off_y],
        "sprite_screen_rect": [left, top, width, height], "player_tile_screen_xy": [tile_left, tile_top],
        "camera_pan": [pan_x, pan_y], "camera_pixel_offset": [camera[0], camera[1]],
        "tile_columns_on_screen": [columns[0], columns[-1]] if columns else None,
        "tile_rows_on_screen": [rows[0], rows[-1]] if rows else None, "half_visible_rows": half_rows,
    }


#: The behaviour test (`--behaviour`): frames with no input before the press, the frames watched after it.
#: IDLE was 120 until 2026-10-07: on ki17_partymenu_wedge.ss1 the party menu's text takes ~108 frames to
#: print and then waits, so 120 idle frames left too few still frames to grade the wait (measured).
IDLE_FRAMES, AFTER_FRAMES, FROZEN_RUN = 300, 300, 30


def screen_snapshot() -> dict:
    """What would MOVE if the game were not waiting: every active text printer (`sTextPrinters[i]`,
    struct TextPrinter 0x24 bytes: currentChar @0, active @0x1B, state @0x1C), the message box mode, the
    main callback, the active tasks and the global script's position (`sGlobalScriptContext.scriptPtr`
    @8). Not compared: timers and the down arrow's animation, which run while a game waits."""
    from modules.memory import read_symbol

    printers = read_symbol("sTextPrinters", size=0x24 * 32)
    active = [[i, _u32(printers, 0x24 * i), printers[0x24 * i + 0x1C]] for i in range(32) if printers[0x24 * i + 0x1B]]
    raw_tasks = read_symbol("gTasks", size=40 * 16)
    tasks = sorted({_symbol(_u32(raw_tasks, 40 * i) - 1) for i in range(16) if raw_tasks[40 * i + 4] and _u32(raw_tasks, 40 * i)})
    script = read_symbol("sGlobalScriptContext", size=12)
    return {"printers": active, "box": read_symbol("sFieldMessageBoxMode", size=1)[0],
            "callback2": _symbol(_u32(read_symbol("gMain", size=8), 4) - 1), "tasks": tasks,
            "script_ptr": _u32(script, 8)}


def _entry(look, snapshot: dict) -> dict:
    return {"frame": look.frame, "waits": look.screen.waits_for_button, "reason": look.screen.wait_reason,
            "screen": look.screen.screen, "snapshot": snapshot}


def _no_menu(snapshot: dict) -> bool:
    return not any("YesNo" in t or "Multichoice" in t for t in snapshot["tasks"])


def _printing(timeline: list[dict]) -> list[list]:
    """Frames on which a text PRINTS by itself: a printer's `currentChar` changes on the NEXT frame, with
    no input. [frame, the eyes' waits, their reason, the printers (index, currentChar, state)]."""
    out = []
    for i, entry in enumerate(timeline[:-1]):
        now = {p[0]: p[1] for p in entry["snapshot"]["printers"]}
        later = {p[0]: p[1] for p in timeline[i + 1]["snapshot"]["printers"]}
        if any(later.get(k) != v for k, v in now.items() if k in later):
            out.append([entry["frame"], entry["waits"], entry["reason"], entry["snapshot"]["printers"]])
    return out


def behaviour(context, state: bytes) -> dict:
    """THE GAME'S BEHAVIOUR as the truth for "waits for a button" (this emulator only; the AI never
    presses in a watcher run). From a fresh load of the state: IDLE_FRAMES frames with NO input, then ONE
    press of A, then AFTER_FRAMES frames with no input, the eyes looking at EVERY frame of both:
      * `waits_truth` (the first look) = TEXT is on screen (a text printer is active), NOTHING moved on any
        idle frame, and the one press moved THAT text (a printer active before the press changed its
        `currentChar` or state, or closed). "The game reacts to A" alone is not it: on the overworld facing
        a person, A starts a dialogue (measured on dewford.ss1), and the game was not waiting for anything;
      * `text_moved_by_itself_at`: the first idle frame at which a text printer's `currentChar` changed
        with no input: the text was still PRINTING (not waiting) when the eyes looked;
      * PRINTING frames (idle and after the press): a text printer's `currentChar` changes on the NEXT
        frame, with no input: the game is printing, not waiting; the eyes must say waits=False there;
      * WAITING frames BEFORE the press (`idle_waiting_frames`, added 2026-10-07): the idle frames from
        which NOTHING moves until the press (at least FROZEN_RUN of them, a text printer active, no menu
        task), when the press then moved that text: the game sat still until A and A moved it. This is how
        a text that finishes printing DURING the idle frames and then waits is seen (the party menu's
        `{PAUSE_UNTIL_PRESS}` on ki17_partymenu_wedge.ss1); the eyes must say waits=True there;
      * after the press, a frame from which nothing moves for FROZEN_RUN frames while a text printer is
        active and no menu task runs is text waiting again (`frozen_text_frames`): waits=True there."""
    from ai_player.host.eyes import FrameworkEyes

    emulator = context.emulator
    emulator.load_save_state(state)
    eyes = FrameworkEyes()
    first = eyes.look()
    s0 = screen_snapshot()
    before = {p[0]: (p[1], p[2]) for p in s0["printers"]}
    idle = [_entry(first, s0)]
    moved_by_itself_at = None
    for _ in range(IDLE_FRAMES):
        emulator.run_single_frame()
        entry = _entry(eyes.look(), screen_snapshot())
        idle.append(entry)
        if moved_by_itself_at is None:
            now = {p[0]: p[1] for p in entry["snapshot"]["printers"]}
            if any(now.get(k, v[0]) != v[0] for k, v in before.items()):
                moved_by_itself_at = entry["frame"]
    s1 = idle[-1]["snapshot"]
    idle_still = all(entry["snapshot"] == s0 for entry in idle)
    text_flags_idle = read_text_flags()
    emulator.press_button("A")
    emulator.run_single_frame()
    timeline = []
    for _ in range(AFTER_FRAMES):
        timeline.append(_entry(eyes.look(), screen_snapshot()))
        emulator.run_single_frame()
    moved = any(entry["snapshot"] != s1 for entry in timeline)
    after_idle = {p[0]: (p[1], p[2]) for p in s1["printers"]}
    moved_text = any(
        any(k not in {p[0] for p in entry["snapshot"]["printers"]}
            or next(tuple(p[1:]) for p in entry["snapshot"]["printers"] if p[0] == k) != v
            for k, v in after_idle.items())
        for entry in timeline)
    # the idle frames that sat still until the press (the longest still run that ENDS at the press)
    still_until_press = []
    for entry in reversed(idle):
        if entry["snapshot"] != s1:
            break
        still_until_press.append(entry)
    still_until_press.reverse()
    idle_waiting = []
    if len(still_until_press) >= FROZEN_RUN and s1["printers"] and _no_menu(s1) and moved_text:
        idle_waiting = [[e["frame"], e["waits"], e["reason"], e["snapshot"]["printers"]] for e in still_until_press]
    frozen_text = []
    for i, entry in enumerate(timeline[:-1]):
        run = timeline[i:i + FROZEN_RUN]
        if (len(run) == FROZEN_RUN and all(r["snapshot"] == entry["snapshot"] for r in run) and entry["snapshot"]["printers"]
                and _no_menu(entry["snapshot"])):
            frozen_text.append([entry["frame"], entry["waits"], entry["reason"], entry["snapshot"]["printers"]])
    return {
        "first_look": {"frame": first.frame, "waits": first.screen.waits_for_button, "reason": first.screen.wait_reason,
                       "screen": first.screen.screen},
        "before_press": s0, "after_idle": s1, "idle_frames": IDLE_FRAMES, "idle_still": idle_still,
        "text_on_screen": bool(before), "text_moved_by_itself_at": moved_by_itself_at,
        "press_moved": moved, "press_moved_the_text": moved_text,
        "waits_truth": bool(before) and idle_still and moved_text,
        "text_flags_before_press": text_flags_idle,
        "text_before_press": [{"printer": p[0], "state": p[2], **printer_text(context, p[1])} for p in s1["printers"]],
        "first_change_after_press": next(({"frame": e["frame"], "snapshot": e["snapshot"]} for e in timeline if e["snapshot"] != s1), None),
        "idle_printing_frames": _printing(idle), "idle_waiting_frames": idle_waiting,
        "printing_frames": _printing(timeline), "frozen_text_frames": frozen_text,
        "timeline_digest": [[e["frame"], e["waits"], e["reason"], e["screen"], len(e["snapshot"]["printers"]), e["snapshot"]["box"]]
                            for e in (idle + timeline)[::20]],
    }


def read_text_flags() -> int:
    from modules.memory import read_symbol

    return read_symbol("gTextFlags", size=1)[0]


def header_guard(context, state: bytes) -> dict:
    """FAULT ARM of the eyes' map-header check (`host/eyes.py` _map_facts), in THIS throwaway emulator:
    a fresh look on the unchanged state, then ANOTHER map's ROM header written over `gMapHeader` and a
    fresh look again (fresh eyes: the check runs once per map). The first must report no header problem;
    the second must refuse ("is not map") and report no player. The state is reloaded afterwards."""
    from ai_player.host.eyes import FrameworkEyes
    from modules.game import get_symbol
    from modules.map_data import MapRSE

    emulator = context.emulator
    emulator.load_save_state(state)
    clean = FrameworkEyes().look()
    address = get_symbol("gMapHeader")[0]
    live = bytes(emulator.read_bytes(address, 0x1C))
    rom = RomMaps(emulator)
    other = None
    for member in MapRSE:
        try:
            if rom.header(tuple(member.value))[4:] != live[4:]:
                other = tuple(member.value)
                break
        except Exception:  # noqa: BLE001
            continue
    stale = None
    if other is not None:
        emulator.write_bytes(address, rom.header(other))
        stale = FrameworkEyes().look()
    emulator.load_save_state(state)
    return {
        "clean_header_problems": [p for p in clean.problems if "map header" in p],
        "clean_player": clean.player is not None,
        "stale_header_of_map": list(other) if other else None,
        "stale_header_problems": [p[:160] for p in stale.problems if "map header" in p] if stale else None,
        "stale_player": (stale.player is not None) if stale else None,
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--settle", type=int, default=1, help="frames to run after loading, before the reads")
    parser.add_argument("--repeat", type=int, default=0, help="time this many looks, one per frame")
    parser.add_argument("--behaviour", action="store_true", help="after everything else, the press test (module docstring)")
    args = parser.parse_args()

    context = boot(args.profile)
    data = args.state.read_bytes()
    context.emulator.load_save_state(data)
    seed_frame = context.emulator.get_frame_count()
    for _ in range(max(0, min(args.settle, 10_000))):
        context.emulator.run_single_frame()

    from ai_player.host.eyes import FrameworkEyes
    from modules.memory import get_game_state

    import ai_player.host.eyes as eyes_module
    from ai_player.eyes import view as rules

    result: dict = {"state_file": str(args.state), "md5": hashlib.md5(data).hexdigest(), "seed_frame": seed_frame,
                    "frame": context.emulator.get_frame_count(), "game_state": get_game_state().name,
                    # WHICH eyes ran (arm XW runs this file from a mutated copy of the package)
                    "eyes_code": {"module": eyes_module.__file__, "rules": rules.__file__,
                                  "wait_states": sorted(rules.TEXT_PRINTER_WAIT_STATES),
                                  "printer_count": rules.TEXT_PRINTER_COUNT}}
    result["truth"] = truth(context)
    try:
        result["window"] = window_from_sprite(context)
    except Exception as error:  # noqa: BLE001
        result["window"] = {"error": f"{type(error).__name__}: {error}"}
    eyes = FrameworkEyes()
    result["eyes"] = eyes.look().to_dict()
    uncropped = FrameworkEyes(crop=False).look()
    result["eyes_uncropped_objects"] = [] if uncropped.view is None else [
        {"kind": o.kind, "local_id": o.local_id, "graphics_id": o.graphics_id, "dx": o.dx, "dy": o.dy, "source": o.source}
        for o in uncropped.view.objects
    ]
    costs = []
    for _ in range(max(0, min(args.repeat, 10_000))):
        context.emulator.run_single_frame()
        start = time.perf_counter()
        eyes.look()
        costs.append((time.perf_counter() - start) * 1000.0)
    if costs:
        costs.sort()
        result["cost_ms"] = {"looks": len(costs), "mean": round(statistics.fmean(costs), 3),
                             "median": round(statistics.median(costs), 3), "min": round(costs[0], 3),
                             "p90": round(costs[int(0.9 * (len(costs) - 1))], 3), "max": round(costs[-1], 3)}
    try:
        result["header_guard"] = header_guard(context, data)
    except Exception as error:  # noqa: BLE001
        result["header_guard"] = {"error": f"{type(error).__name__}: {error}"}
    if args.behaviour:
        try:
            result["behaviour"] = behaviour(context, data)
        except Exception as error:  # noqa: BLE001
            result["behaviour"] = {"error": f"{type(error).__name__}: {error}"}
    print("PROBE " + json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
