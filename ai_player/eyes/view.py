"""The AI's PERCEPTION RULES: what is on screen, and what a tile or an object IS. Framework-free.

Everything here is a fact about Pokemon Emerald copied from pret/pokeemerald (each table names its
source file), or a rule about what a PERSON at the screen can see. `ai_player/host/eyes.py` reads the
raw numbers from the game and calls these functions; nothing here reads anything.

THE GBA VIEW (design draft §10.7: "eyes.py crops tiles and objects to the on-screen view, about ±7 by
±5 tiles"). Derived from the decomp, then MEASURED live (`gates/live_step1.py` arm GEO):

  * The screen is 240 x 160 pixels (`include/gba/defines.h` DISPLAY_WIDTH/HEIGHT) and a map tile (a
    metatile) is 16 x 16, so 15 columns by 10 rows fit.
  * The overworld BG holds metatile (j, i) of the VIRTUAL map at `(gSaveBlock1Ptr->pos.x + j,
    pos.y + i)` (`src/field_camera.c` DrawWholeMapViewInternal). The virtual map pads the map by
    MAP_OFFSET = 7 on every side (`include/fieldmap.h`), and `pos` is the player's MAP coordinate, so
    the player is BG metatile (7, 7).
  * The BG is scrolled by HOFS = xPixelOffset + sHorizontalCameraPan and VOFS = yPixelOffset +
    sVerticalCameraPan + 8 (`FieldUpdateBgTilemapScroll`); `InstallCameraPanAheadCallback` sets the
    pans to 0 and 32, and the only code that changes them while walking is unreachable
    (`gUnusedBikeCameraAheadPanback` is FALSE). Standing still: HOFS = 0, VOFS = 40.
  * So metatile column j is drawn at screen x = 16*j and row i at screen y = 16*i - 40. The player's
    tile (7, 7) is at screen (112..127, 72..87): column 7 of 0..14, with rows i = 2..12 on screen.
  * Relative to the player: dx = -7..+7 (15 columns, all whole), dy = -5..+5 (11 rows; the rows
    dy = -5 and dy = +5 show only HALF a tile, screen y 0..7 and 152..159). Sprites agree: an object
    at the player's tile is drawn with its feet at screen y 72..87 (`SetSpritePosToMapCoords` + the
    (8, 16) spawn offset + `gSpriteCoordOffsetY = gTotalCameraPixelOffsetY - 32 - 8`,
    `UpdateCameraPanning`).
  * While the camera scrolls one tile (a step), a 16th column / 12th row slides in partially. The
    crop is the standing-still window; it does not chase the in-between pixels of a step.
  * The game itself keeps objects ALIVE well outside that window: it spawns them within
    [pos.x - 2, pos.x + 17] x [pos.y, pos.y + 16] of the virtual map (`TrySpawnObjectEvents`,
    `RemoveObjectEventIfOutsideView`), i.e. dx = -9..+10 and dy = -7..+9 around the player. That is
    WHY the crop exists: `gObjectEvents` holds things a person cannot see yet.
"""

from __future__ import annotations

from collections.abc import Iterable

__all__ = [
    "BADGE_FLAGS",
    "BATTLE_TYPE_WALLY_TUTORIAL",
    "BEHAVIOR",
    "BEHAVIOR_NAMES",
    "DOOR_BEHAVIORS",
    "EXIT_BEHAVIORS",
    "GFX_KINDS",
    "GLYPHS",
    "HP_BAR_PIXELS",
    "LEDGE_DIRECTIONS",
    "MENU_STATES",
    "MENU_TASKS",
    "MILESTONE_FLAGS",
    "MILESTONE_VARS",
    "OUTCOME_CAUGHT",
    "OUTCOME_NAMES",
    "RENDER_STATE_NAMES",
    "SAVE_BLOCK_1_FLAGS",
    "SAVE_BLOCK_1_FLAG_BYTES",
    "SAVE_BLOCK_1_VARS",
    "SCRIPT_CONTEXT_SHUTDOWN",
    "STORY_FLAGS",
    "TALL_GRASS_BEHAVIORS",
    "TEXT_FLAG_AUTO_SCROLL",
    "TEXT_PRINTER_COUNT",
    "TEXT_PRINTER_WAIT_STATES",
    "TILE_FLAG_HAS_ENCOUNTERS",
    "TILE_FLAG_SURFABLE",
    "VIEW_DOWN",
    "VIEW_HALF_WIDTH",
    "VARS_START",
    "VIEW_UP",
    "behavior_name",
    "classify_screen",
    "facing_name",
    "foe_move_seen",
    "hp_bar_pixels",
    "in_view",
    "milestone_marks",
    "movement_mode",
    "object_kind",
    "script_waits_for_button",
    "settled_position",
    "status_name",
    "text_printer_wait",
    "view_offsets",
    "visible_id",
]

# ------------------------------------------------------------------------------------------- the window
#: Columns left and right of the player that are on screen (derivation in the module docstring).
VIEW_HALF_WIDTH = 7
#: Rows above and below the player that are on screen; the outermost row on each side is HALF visible.
VIEW_UP = 5
VIEW_DOWN = 5


def in_view(player_x: int, player_y: int, x: int, y: int) -> bool:
    """Is map tile (x, y) on screen while the player stands on (player_x, player_y)?"""
    dx, dy = x - player_x, y - player_y
    return -VIEW_HALF_WIDTH <= dx <= VIEW_HALF_WIDTH and -VIEW_UP <= dy <= VIEW_DOWN


def view_offsets() -> tuple[tuple[int, int], ...]:
    """Every (dx, dy) of the window, row by row from the top-left."""
    return tuple(
        (dx, dy) for dy in range(-VIEW_UP, VIEW_DOWN + 1) for dx in range(-VIEW_HALF_WIDTH, VIEW_HALF_WIDTH + 1)
    )


# ------------------------------------------------------------------------------------------- tiles
#: Every metatile behaviour, by value (`include/constants/metatile_behaviors.h`, the enum from MB_NORMAL
#: = 0 to MB_UNUSED_EF = 0xEF; the MB_ prefix dropped). Generated from the header, not typed by hand.
BEHAVIOR_NAMES: tuple[str, ...] = (
    "NORMAL", "SECRET_BASE_WALL", "TALL_GRASS", "LONG_GRASS", "UNUSED_04", "UNUSED_05", "DEEP_SAND", "SHORT_GRASS",
    "CAVE", "LONG_GRASS_SOUTH_EDGE", "NO_RUNNING", "INDOOR_ENCOUNTER", "MOUNTAIN_TOP", "BATTLE_PYRAMID_WARP",
    "MOSSDEEP_GYM_WARP", "MT_PYRE_HOLE", "POND_WATER", "INTERIOR_DEEP_WATER", "DEEP_WATER", "WATERFALL",
    "SOOTOPOLIS_DEEP_WATER", "OCEAN_WATER", "PUDDLE", "SHALLOW_WATER", "UNUSED_SOOTOPOLIS_DEEP_WATER",
    "NO_SURFACING", "UNUSED_SOOTOPOLIS_DEEP_WATER_2", "STAIRS_OUTSIDE_ABANDONED_SHIP", "SHOAL_CAVE_ENTRANCE",
    "UNUSED_1D", "UNUSED_1E", "UNUSED_1F", "ICE", "SAND", "SEAWEED", "UNUSED_23", "ASHGRASS", "FOOTPRINTS",
    "THIN_ICE", "CRACKED_ICE", "HOT_SPRINGS", "LAVARIDGE_GYM_B1F_WARP", "SEAWEED_NO_SURFACING",
    "REFLECTION_UNDER_BRIDGE", "UNUSED_2C", "UNUSED_2D", "UNUSED_2E", "UNUSED_2F", "IMPASSABLE_EAST",
    "IMPASSABLE_WEST", "IMPASSABLE_NORTH", "IMPASSABLE_SOUTH", "IMPASSABLE_NORTHEAST", "IMPASSABLE_NORTHWEST",
    "IMPASSABLE_SOUTHEAST", "IMPASSABLE_SOUTHWEST", "JUMP_EAST", "JUMP_WEST", "JUMP_NORTH", "JUMP_SOUTH",
    "JUMP_NORTHEAST", "JUMP_NORTHWEST", "JUMP_SOUTHEAST", "JUMP_SOUTHWEST", "WALK_EAST", "WALK_WEST", "WALK_NORTH",
    "WALK_SOUTH", "SLIDE_EAST", "SLIDE_WEST", "SLIDE_NORTH", "SLIDE_SOUTH", "TRICK_HOUSE_PUZZLE_8_FLOOR",
    "UNUSED_49", "UNUSED_4A", "UNUSED_4B", "UNUSED_4C", "UNUSED_4D", "UNUSED_4E", "UNUSED_4F", "EASTWARD_CURRENT",
    "WESTWARD_CURRENT", "NORTHWARD_CURRENT", "SOUTHWARD_CURRENT", "UNUSED_54", "UNUSED_55", "UNUSED_56",
    "UNUSED_57", "UNUSED_58", "UNUSED_59", "UNUSED_5A", "UNUSED_5B", "UNUSED_5C", "UNUSED_5D", "UNUSED_5E",
    "UNUSED_5F", "NON_ANIMATED_DOOR", "LADDER", "EAST_ARROW_WARP", "WEST_ARROW_WARP", "NORTH_ARROW_WARP",
    "SOUTH_ARROW_WARP", "CRACKED_FLOOR_HOLE", "AQUA_HIDEOUT_WARP", "LAVARIDGE_GYM_1F_WARP", "ANIMATED_DOOR",
    "UP_ESCALATOR", "DOWN_ESCALATOR", "WATER_DOOR", "WATER_SOUTH_ARROW_WARP", "DEEP_SOUTH_WARP", "UNUSED_6F",
    "BRIDGE_OVER_OCEAN", "BRIDGE_OVER_POND_LOW", "BRIDGE_OVER_POND_MED", "BRIDGE_OVER_POND_HIGH",
    "PACIFIDLOG_VERTICAL_LOG_TOP", "PACIFIDLOG_VERTICAL_LOG_BOTTOM", "PACIFIDLOG_HORIZONTAL_LOG_LEFT",
    "PACIFIDLOG_HORIZONTAL_LOG_RIGHT", "FORTREE_BRIDGE", "UNUSED_79", "BRIDGE_OVER_POND_MED_EDGE_1",
    "BRIDGE_OVER_POND_MED_EDGE_2", "BRIDGE_OVER_POND_HIGH_EDGE_1", "BRIDGE_OVER_POND_HIGH_EDGE_2", "UNUSED_BRIDGE",
    "BIKE_BRIDGE_OVER_BARRIER", "COUNTER", "UNUSED_81", "UNUSED_82", "PC", "CABLE_BOX_RESULTS_1", "REGION_MAP",
    "TELEVISION", "POKEBLOCK_FEEDER", "UNUSED_88", "SLOT_MACHINE", "ROULETTE", "CLOSED_SOOTOPOLIS_DOOR",
    "TRICK_HOUSE_PUZZLE_DOOR", "PETALBURG_GYM_DOOR", "RUNNING_SHOES_INSTRUCTION", "QUESTIONNAIRE",
    "SECRET_BASE_SPOT_RED_CAVE", "SECRET_BASE_SPOT_RED_CAVE_OPEN", "SECRET_BASE_SPOT_BROWN_CAVE",
    "SECRET_BASE_SPOT_BROWN_CAVE_OPEN", "SECRET_BASE_SPOT_YELLOW_CAVE", "SECRET_BASE_SPOT_YELLOW_CAVE_OPEN",
    "SECRET_BASE_SPOT_TREE_LEFT", "SECRET_BASE_SPOT_TREE_LEFT_OPEN", "SECRET_BASE_SPOT_SHRUB",
    "SECRET_BASE_SPOT_SHRUB_OPEN", "SECRET_BASE_SPOT_BLUE_CAVE", "SECRET_BASE_SPOT_BLUE_CAVE_OPEN",
    "SECRET_BASE_SPOT_TREE_RIGHT", "SECRET_BASE_SPOT_TREE_RIGHT_OPEN", "UNUSED_9E", "UNUSED_9F", "BERRY_TREE_SOIL",
    "UNUSED_A1", "UNUSED_A2", "UNUSED_A3", "UNUSED_A4", "UNUSED_A5", "UNUSED_A6", "UNUSED_A7", "UNUSED_A8",
    "UNUSED_A9", "UNUSED_AA", "UNUSED_AB", "UNUSED_AC", "UNUSED_AD", "UNUSED_AE", "UNUSED_AF", "SECRET_BASE_PC",
    "SECRET_BASE_REGISTER_PC", "SECRET_BASE_SCENERY", "SECRET_BASE_TRAINER_SPOT", "SECRET_BASE_DECORATION",
    "HOLDS_SMALL_DECORATION", "UNUSED_B6", "SECRET_BASE_NORTH_WALL", "SECRET_BASE_BALLOON",
    "SECRET_BASE_IMPASSABLE", "SECRET_BASE_GLITTER_MAT", "SECRET_BASE_JUMP_MAT", "SECRET_BASE_SPIN_MAT",
    "SECRET_BASE_SOUND_MAT", "SECRET_BASE_BREAKABLE_DOOR", "SECRET_BASE_SAND_ORNAMENT",
    "IMPASSABLE_SOUTH_AND_NORTH", "IMPASSABLE_WEST_AND_EAST", "SECRET_BASE_HOLE", "HOLDS_LARGE_DECORATION",
    "SECRET_BASE_TV_SHIELD", "PLAYER_ROOM_PC_ON", "SECRET_BASE_DECORATION_BASE", "SECRET_BASE_POSTER", "UNUSED_C8",
    "UNUSED_C9", "UNUSED_CA", "UNUSED_CB", "UNUSED_CC", "UNUSED_CD", "UNUSED_CE", "UNUSED_CF", "MUDDY_SLOPE",
    "BUMPY_SLOPE", "CRACKED_FLOOR", "ISOLATED_VERTICAL_RAIL", "ISOLATED_HORIZONTAL_RAIL", "VERTICAL_RAIL",
    "HORIZONTAL_RAIL", "UNUSED_D7", "UNUSED_D8", "UNUSED_D9", "UNUSED_DA", "UNUSED_DB", "UNUSED_DC", "UNUSED_DD",
    "UNUSED_DE", "UNUSED_DF", "PICTURE_BOOK_SHELF", "BOOKSHELF", "POKEMON_CENTER_BOOKSHELF", "VASE", "TRASH_CAN",
    "SHOP_SHELF", "BLUEPRINT", "CABLE_BOX_RESULTS_2", "WIRELESS_BOX_RESULTS", "TRAINER_HILL_TIMER",
    "SKY_PILLAR_CLOSED_DOOR", "UNUSED_EB", "UNUSED_EC", "UNUSED_ED", "UNUSED_EE", "UNUSED_EF",
)
#: name -> value, so no value below is typed by hand.
BEHAVIOR: dict[str, int] = {name: value for value, name in enumerate(BEHAVIOR_NAMES)}

#: `sTileBitAttributes` bits (`src/metatile_behavior.c`). The table itself is READ from the ROM by the
#: host side (it is game data); these are the meanings of its bits.
TILE_FLAG_HAS_ENCOUNTERS = 1 << 0
TILE_FLAG_SURFABLE = 1 << 1

#: The grass a wild Pokemon jumps out of (`MetatileBehavior_IsPokeGrass`: tall grass and long grass).
TALL_GRASS_BEHAVIORS = frozenset({BEHAVIOR["TALL_GRASS"], BEHAVIOR["LONG_GRASS"]})
#: A ledge: the direction the player JUMPS when walking onto it that way (`MetatileBehavior_IsJump*`).
LEDGE_DIRECTIONS: dict[int, str] = {
    BEHAVIOR["JUMP_EAST"]: "east", BEHAVIOR["JUMP_WEST"]: "west",
    BEHAVIOR["JUMP_NORTH"]: "north", BEHAVIOR["JUMP_SOUTH"]: "south",
    BEHAVIOR["JUMP_NORTHEAST"]: "northeast", BEHAVIOR["JUMP_NORTHWEST"]: "northwest",
    BEHAVIOR["JUMP_SOUTHEAST"]: "southeast", BEHAVIOR["JUMP_SOUTHWEST"]: "southwest",
}
#: What a person reads as a DOOR (`MetatileBehavior_IsDoor` is ANIMATED_DOOR + PETALBURG_GYM_DOOR; the
#: plain and the underwater doors look like doors too).
DOOR_BEHAVIORS = frozenset(
    {BEHAVIOR["ANIMATED_DOOR"], BEHAVIOR["NON_ANIMATED_DOOR"], BEHAVIOR["PETALBURG_GYM_DOOR"], BEHAVIOR["WATER_DOOR"]}
)
#: What a person reads as a WAY OUT by how the tile LOOKS (build step 3.1, the step-3 review's finding 5: the eyes used
#: to mark a tile a warp from the ROM's warp-event table, which nothing on screen shows): every door above, and the
#: stairs (`NON_ANIMATED_DOOR`), ladders, escalators, arrow mats, holes in the floor, the gyms' warp pads, and the
#: drawn entrances. The GAME ITSELF fires a warp event on a step only for these looks: `src/field_control_avatar.c`
#: IsWarpMetatileBehavior (a door, a ladder, an escalator, a non-animated door, the Lavaridge, Aqua Hideout, Mossdeep
#: and Mt Pyre warps; and MB_BRIDGE_OVER_OCEAN, re-used by the Union Room's exit only and left out here: 608 bridge
#: tiles on Routes 110 and 119 carry it), IsArrowWarpMetatileBehavior (the four arrow mats, the water arrow, the Shoal
#: Cave entrance) and TryDoorWarp; a cracked floor is a fall (`MetatileBehavior_IsCrackedFloorHole`). MEASURED
#: 2026-10-08 over the 518 maps of the ROM (`gates/exit_looks.py`, a test-side scan of every map's warp events; arm
#: EXITS of `gates/live_step3.py`): 1,193 of the 1,313 warp tiles carry one of these looks; the other 120 look like
#: plain ground or water (94 NORMAL, e.g. Petalburg Gym's rooms) and are, by the rule above, places scripts, Fly, Dig
#: or Dive put the player, never a tile a step warps from (no warp tile with a step-warp look is missed). Every warp
#: tile of Littleroot, Route 101 and Oldale, their buildings included, carries one. What a look cannot say is LEARNED
#: BY USING THE EXIT: where it leads (the warp graph, `world/memory.py`), and that a door-looking tile does not open
#: (395 tiles of these looks have no warp: a closed door, the Pokemon Centers' 2F doors, Petalburg Gym's sliding
#: doors): pressed into properly and taking the player nowhere, it is remembered as CLOSED (`MapMemory.closed`) and
#: not chosen as a way out while it stays so: it is tried again once one of the eyes' story flags is newly set since it
#: was found closed, or after `world/memory.py` CLOSED_RETRY_FRAMES (36,000 frames; the step-3.1 verifier's round).
EXIT_BEHAVIORS = DOOR_BEHAVIORS | frozenset(BEHAVIOR[name] for name in (
    "LADDER", "UP_ESCALATOR", "DOWN_ESCALATOR", "EAST_ARROW_WARP", "WEST_ARROW_WARP", "NORTH_ARROW_WARP",
    "SOUTH_ARROW_WARP", "WATER_SOUTH_ARROW_WARP", "DEEP_SOUTH_WARP", "CRACKED_FLOOR_HOLE", "MT_PYRE_HOLE",
    "AQUA_HIDEOUT_WARP", "LAVARIDGE_GYM_1F_WARP", "LAVARIDGE_GYM_B1F_WARP", "MOSSDEEP_GYM_WARP", "BATTLE_PYRAMID_WARP",
    "TRICK_HOUSE_PUZZLE_DOOR", "STAIRS_OUTSIDE_ABANDONED_SHIP", "SHOAL_CAVE_ENTRANCE", "SKY_PILLAR_CLOSED_DOOR",
))


def behavior_name(value: int) -> str:
    return BEHAVIOR_NAMES[value] if 0 <= value < len(BEHAVIOR_NAMES) else f"INVALID_{value:02X}"


# ------------------------------------------------------------------------------------------- objects
#: Graphics ids a person recognises as a THING rather than a person (`include/constants/event_objects.h`).
GFX_KINDS: dict[int, str] = {
    59: "item_ball",  # OBJ_EVENT_GFX_ITEM_BALL
    60: "berry_tree",  # OBJ_EVENT_GFX_BERRY_TREE
    61: "berry_tree",  # OBJ_EVENT_GFX_BERRY_TREE_EARLY_STAGES
    62: "berry_tree",  # OBJ_EVENT_GFX_BERRY_TREE_LATE_STAGES
    82: "cut_tree",  # OBJ_EVENT_GFX_CUTTABLE_TREE
    86: "smash_rock",  # OBJ_EVENT_GFX_BREAKABLE_ROCK
    87: "boulder",  # OBJ_EVENT_GFX_PUSHABLE_BOULDER
}


def object_kind(graphics_id: int) -> str:
    """What a person would call this object: a THING by its look (`GFX_KINDS`), otherwise a person,
    "npc". ‼ Step 1.1 (the step-1 review, "perception like a person"): until then a person whose map
    template has a trainer type was labelled "trainer". Nothing on screen says so: a trainer looks like
    any other person until it spots the player and walks up (the "!" and the approach are what a player
    sees), so a label read from the object's trainer type told the AI who would fight before the game
    showed it. The battle itself is seen (`BattleView.kind`), and that is when the AI learns it."""
    return GFX_KINDS.get(graphics_id, "npc")


#: `facingDirection` values (`include/constants/global.h` DIR_SOUTH = 1 ... DIR_EAST = 4).
_FACING = {1: "down", 2: "up", 3: "left", 4: "right"}


def facing_name(direction: int) -> str:
    return _FACING.get(direction, "?")


#: `gPlayerAvatar.flags` (`include/global.fieldmap.h` PLAYER_AVATAR_FLAG_*), checked in this order.
_AVATAR_MODES = ((1 << 4, "underwater"), (1 << 3, "surfing"), (1 << 1, "mach_bike"), (1 << 2, "acro_bike"), (1 << 7, "running"))


def movement_mode(avatar_flags: int) -> str:
    for bit, name in _AVATAR_MODES:
        if avatar_flags & bit:
            return name
    return "walking"


# ------------------------------------------------------------------------------------------- the party
def status_name(bits: int) -> str:
    """A party Pokemon's status byte (`include/constants/battle.h` STATUS1_*): sleep turns in bits 0-2,
    then poison, burn, freeze, paralysis, toxic."""
    if bits & 0x80:
        return "toxic"
    if bits & 0x40:
        return "paralysis"
    if bits & 0x20:
        return "freeze"
    if bits & 0x10:
        return "burn"
    if bits & 0x08:
        return "poison"
    if bits & 0x07:
        return "sleep"
    return "ok"


#: `gBattleOutcome` (`include/constants/battle.h` B_OUTCOME_*), named as the bot's logs name them
#: (`modules/battle_state.py` BattleOutcome), because the learner's scorer reads `res=Won`. 0 means NO
#: result yet: `BattleStartClearSetData` (`src/battle_main.c`, run by `BeginBattleIntro`, the battle's
#: first main function) sets it to 0, and the battle scripts set the result as the battle ends.
OUTCOME_NAMES: dict[int, str] = {
    0: "InProgress", 1: "Won", 2: "Lost", 3: "Draw", 4: "RanAway", 5: "PlayerTeleported", 6: "OpponentFled",
    7: "Caught", 8: "NoSafariBallsLeft", 9: "Forfeited", 10: "OpponentTeleported", 128: "LinkBattleRanAway",
}
#: B_OUTCOME_CAUGHT. ‼ It does NOT mean the PLAYER caught something: Wally's tutorial
#: (`BATTLE_TYPE_WALLY_TUTORIAL`) ends with `BattleScript_WallyBallThrow` (`data/battle_scripts_2.s`):
#: `printstring STRINGID_GOTCHAPKMNCAUGHTWALLY; setbyte gBattleOutcome, B_OUTCOME_CAUGHT; finishturn`, with
#: no `givecaughtmon`, so the Ralts goes to Wally. A player's catch runs `givecaughtmon` BEFORE the same
#: `setbyte` (`BattleScript_SuccessBallThrow`), so it shows as a NEW Pokemon of the player's in the party
#: or a box: `ai_player/memory_log.py` logs a catch only on that.
OUTCOME_CAUGHT = 7
#: `include/constants/battle.h`: `#define BATTLE_TYPE_WALLY_TUTORIAL (1 << 9)`.
BATTLE_TYPE_WALLY_TUTORIAL = 1 << 9

# ------------------------------------------------------------------------------------------- the battle
#: The width of a battle HP bar in pixels: `src/battle_interface.c` `#define B_HEALTHBAR_PIXELS 48`.
HP_BAR_PIXELS = 48


def hp_bar_pixels(hp: int, max_hp: int) -> int:
    """How many of the HP bar's 48 pixels are filled: what a person SEES of a foe's HP (perception like a
    person, step 1.1; the foe's numbers are not on screen). `src/battle_interface.c` GetScaledHPFraction:
    `result = hp * scale / maxhp; if (result == 0 && hp > 0) return 1;` (C integer division, both
    non-negative). This is the bar the game settles on; while it drains it shows values in between."""
    if max_hp <= 0:
        return 0
    filled = hp * HP_BAR_PIXELS // max_hp
    if filled == 0 and hp > 0:
        return 1
    return filled


def foe_move_seen(pp: int, max_pp: int) -> bool:
    """Has the foe USED this move in this battle, i.e. has the screen shown "Foe X used MOVE!"? A foe's
    Pokemon starts every battle with full PP (wild: `CreateMon`; trainer: `CreateNPCTrainerParty`), and
    the battle takes PP only in `ppreduce`, which the move scripts run right after `attackstring`, the
    command that prints "used MOVE!" (`data/battle_scripts_1.s`: `attackcanceler; accuracycheck ...;
    attackstring; ppreduce`; a move that missed runs `attackstring; ppreduce` in
    `BattleScript_PrintMoveMissed`). Checked 2026-10-07 over all 134 `ppreduce` of that file: 121 follow
    `attackstring` directly; 6 follow it a few commands later (Mirror Move, Rampage, Leech Seed, Rollout,
    Beat Up, Uproar); 5 come right before a path that prints it in the same turn (Substitute, the three
    `..._PPLoss` ability scripts, `BattleScript_SolarBeamOnFirstTurn`); 2 take PP with a message of their
    own instead of "used MOVE!", which names the move to a player anyway: a two-turn move's charging turn
    ("X took in sunlight!", `BattleScriptFirstChargingTurn`) and a Focus Punch that lost focus
    (`BattleScript_EffectFocusPunch`). So a move with PP below its
    maximum is a move the player has seen used (`gates/live_step1.py` arm E10 compares it with the
    "Foe X used MOVE!" texts of the battle, replayed). Moves never used stay unknown, as for a person.
    (Known misses: Struggle takes no PP; a Leppa Berry that restores PP hides that move again.)"""
    return pp < max_pp


def visible_id(full_ot_id: int) -> int:
    """The trainer ID a PERSON sees (the summary screen's "IDNo.", the trainer card): the low 16 bits of
    the 32-bit OT field. The high half is the SECRET id, shown nowhere; the eyes never report it."""
    return full_ot_id & 0xFFFF


def settled_position(object_xy: tuple[int, int], saved_xy: tuple[int, int]) -> tuple[int, int] | None:
    """The player's position, or None while it is SETTLING. `object_xy` is the player object's
    `currentCoords` minus MAP_OFFSET (where the object stands on the map it was built for), `saved_xy` is
    save block 1's `pos` (the game's own copy, written together with the map in `WarpIntoMap`). At rest
    and while walking they agree on every frame (measured 2026-10-07 on a 700-frame walk into Dewford's
    door: 0 of the walking frames differ). During a warp the save block holds the NEW map and its arrival
    tile while the object still stands on the OLD map's tile (6 frames of CHANGE_MAP, measured): reporting
    the object's tile with the save block's map would MIX two maps, so the position is unknown then."""
    return object_xy if object_xy == saved_xy else None

# ------------------------------------------------------------------------------------------- progress
#: The badge flags (`include/constants/flags.h` FLAG_BADGE01_GET ...), as the framework's flag table names them.
BADGE_FLAGS: tuple[str, ...] = tuple(f"BADGE0{n}_GET" for n in range(1, 9))
#: The story flags v1 needs to know where it is on the way to badge 1 (RULING 37 Q3: Ch1 intro to the
#: Pokedex, Ch2 Oldale to Petalburg and Wally, Ch3 Route 104 / Petalburg Woods / Rustboro, Ch4 Roxanne).
#: Each name is checked against `sandbox-pokebot/modules/data/event_flags/emerald.txt` by
#: `gates/test_eyes.py` (the framework's `get_event_flag` returns False SILENTLY for a phantom name), and
#: each id against `include/constants/flags.h`. Each MEANING was checked (2026-10-07) against the decomp
#: script that SETS the flag (`setflag FLAG_...`, named per entry): a flag named after an event is not
#: always set by it. ‼ Ch2 was `THANKED_FOR_PLAYING_WITH_WALLY` until that check: it is set only when the
#: player talks to Wally's DAD in Wally's house (`PetalburgCity_WallysHouse_EventScript_WallysDad`), an
#: optional chat, so it read False on every fixture, even with six badges (this project's ML-9, made a
#: second time). The tutorial itself sets only VARIABLES (`VAR_PETALBURG_CITY_STATE` 2 -> 3); the flag
#: below is the one flag its scene sets. Ch3 has NO entry: the Petalburg Woods scene ends in a variable
#: (`VAR_PETALBURG_WOODS_STATE`) and a trainer flag, not a story flag; reaching Rustboro shows in the map.
STORY_FLAGS: tuple[tuple[str, str], ...] = (
    ("RESCUED_BIRCH", "Ch1: Birch saved from the Zigzagoon on Route 101 (0x52; Route101/scripts.inc)"),
    ("SYS_POKEMON_GET", "Ch1: the player has a Pokemon (the starter) (SYSTEM_FLAGS + 0x0; Route101/scripts.inc)"),
    ("DEFEATED_RIVAL_ROUTE103", "Ch1: the rival beaten on Route 103 (0x82; Route103/scripts.inc)"),
    ("RECEIVED_POKEDEX_FROM_BIRCH", "Ch1: the Pokedex from Birch (SYSTEM_FLAGS + 0x84; ProfessorBirchsLab/scripts.inc)"),
    ("SYS_POKEDEX_GET", "Ch1: the Pokedex menu is enabled (SYSTEM_FLAGS + 0x1; ProfessorBirchsLab/scripts.inc)"),
    ("ADVENTURE_STARTED", "Ch1/Ch2: 'RECEIVED Pokedex'; the Oldale Mart sells Poke Balls after it (0x74; ProfessorBirchsLab)"),
    ("HIDE_PETALBURG_CITY_WALLYS_MOM", "Ch2: Norman's scene sent the player out with Wally: the catching tutorial "
     "has BEGUN (0x2D8; PetalburgCity_Gym_EventScript_BeginWallyTutorial, with VAR_PETALBURG_CITY_STATE = 2). It "
     "plays as one cutscene that ends back in the gym, so once the player can move again it is DONE"),
    ("SYS_B_DASH", "the Running Shoes: the player can run (SYSTEM_FLAGS + 0x60; LittlerootTown/scripts.inc)"),
    ("DEFEATED_RUSTBORO_GYM", "Ch4: Roxanne beaten (0x4F0; RustboroCity_Gym/scripts.inc)"),
    ("BADGE01_GET", "Ch4: the Stone Badge (SYSTEM_FLAGS + 0x7; RustboroCity_Gym/scripts.inc)"),
)
#: BUILD STEP 5 (the goal manager, `brain/goals.py`): the MILESTONE MARKS, what proves each of badge 1's milestones
#: (`knowledge/milestones.json`, extracted and checked against pret/pokeemerald by `gates/extract_milestones.py --verify`):
#: save block 1's event FLAGS by number (a trainer's defeated flag is TRAINER_FLAGS_START 0x500 + its id) and VARS by number
#: (0x4000 + their index in `vars[]`). Read as two plain byte ranges of save block 1 (`host/eyes.py` _marks), reported in
#: `Progress.marks`, and kept APART from `STORY_FLAGS` ON PURPOSE: those feed the navigator's novelty (a flag newly set is
#: progress), and adding these there would move every earlier step's pre-registered walk (e.g. meeting the rival sets
#: `HIDE_LITTLEROOT_TOWN_*_2F_POKE_BALL`, a progress the step-3.1 scene rules were measured without). `gates/test_goals.py`
#: checks this table equals the milestones' proofs, number by number.
MILESTONE_FLAGS: tuple[tuple[str, int], ...] = (
    ("SET_WALL_CLOCK", 0x51), ("RESCUED_BIRCH", 0x52), ("ADVENTURE_STARTED", 0x74), ("DEFEATED_RIVAL_ROUTE103", 0x82),
    ("HIDE_PETALBURG_CITY_WALLYS_MOM", 0x2D8), ("DEFEATED_RUSTBORO_GYM", 0x4F0), ("TRAINER_JOSH", 0x640),
    ("TRAINER_TOMMY", 0x641), ("SYS_POKEMON_GET", 0x860), ("SYS_POKEDEX_GET", 0x861), ("BADGE01_GET", 0x867),
    ("VISITED_LITTLEROOT_TOWN", 0x86F), ("VISITED_OLDALE_TOWN", 0x870), ("VISITED_PETALBURG_CITY", 0x876),
    ("VISITED_RUSTBORO_CITY", 0x879), ("RECEIVED_POKEDEX_FROM_BIRCH", 0x8E4),
    # (chapter 5, 2026-11-01: RUSTBORO after the badge; numbers checked by `gates/extract_milestones.py --verify`)
    ("INTERACTED_WITH_DEVON_EMPLOYEE_GOODS_STOLEN", 0x9F), ("RECOVERED_DEVON_GOODS", 0x8F),
    ("TRAINER_GRUNT_RUSTURF_TUNNEL", 0x510), ("RETURNED_DEVON_GOODS", 0x90), ("RECEIVED_POKENAV", 0xBC),
    ("SYS_POKENAV_GET", 0x862), ("HAS_MATCH_CALL", 0x12F), ("ADDED_MATCH_CALL_TO_POKENAV", 0x130),
    ("ENABLE_RIVAL_MATCH_CALL", 0xFD), ("DEFEATED_RIVAL_RUSTBORO", 0xD3),
    # (chapters 6-7, 2026-11-05: MR. BRINEY's boat and the DEWFORD GYM; numbers checked by `gates/extract_milestones.py --verify`;
    # no variable is new. A proof the eyes do not read is never progress: `Story.done` is None for it and the story would stop)
    ("MR_BRINEY_SAILING_INTRO", 0x93), ("VISITED_DEWFORD_TOWN", 0x871), ("RECEIVED_OLD_ROD", 0x101),
    ("DELIVERED_STEVEN_LETTER", 0xBD), ("REGISTERED_STEVEN_POKENAV", 0x131), ("RECEIVED_HM_FLASH", 0x6D),
    ("TRAINER_TAKAO", 0x5B3), ("TRAINER_JOCELYN", 0x6A9), ("TRAINER_LAURA", 0x6AA), ("TRAINER_BRENDEN", 0x73C),
    ("TRAINER_CRISTIAN", 0x73E), ("TRAINER_LILITH", 0x73D), ("DEFEATED_DEWFORD_GYM", 0x4F1), ("BADGE02_GET", 0x868),
    ("RECEIVED_EXP_SHARE", 0x110),
)
MILESTONE_VARS: tuple[tuple[str, int], ...] = (
    ("BIRCH_LAB_STATE", 0x4084), ("PETALBURG_GYM_STATE", 0x4085), ("LITTLEROOT_RIVAL_STATE", 0x408D),
    ("LITTLEROOT_INTRO_STATE", 0x4092), ("PETALBURG_WOODS_STATE", 0x4098),
    # (chapter 5, 2026-11-01)
    ("RUSTBORO_CITY_STATE", 0x405A), ("RUSTURF_TUNNEL_STATE", 0x409A), ("BRINEY_HOUSE_STATE", 0x4090),
    ("DEVON_CORP_3F_STATE", 0x408F), ("ROUTE104_STATE", 0x4063),
)
#: `include/global.h` struct SaveBlock1: flags[NUM_FLAG_BYTES = 300] @0x1270, vars[NUM_VARS = 256] (u16) @0x139C.
SAVE_BLOCK_1_FLAGS = 0x1270
SAVE_BLOCK_1_FLAG_BYTES = 300
SAVE_BLOCK_1_VARS = 0x139C
VARS_START = 0x4000


def milestone_marks(flag_bytes: bytes, var_bytes: bytes) -> tuple[tuple[str, int], ...]:
    """The MILESTONE marks from save block 1's raw flag and var bytes: each flag 0 or 1, each var its value (u16)."""
    out: list[tuple[str, int]] = []
    for name, number in MILESTONE_FLAGS:
        out.append((name, (flag_bytes[number // 8] >> (number % 8)) & 1 if number // 8 < len(flag_bytes) else 0))
    for name, number in MILESTONE_VARS:
        index = 2 * (number - VARS_START)
        out.append((name, int.from_bytes(var_bytes[index:index + 2], "little") if index + 2 <= len(var_bytes) else 0))
    return tuple(out)

# ------------------------------------------------------------------------------------------- the screen
#: Task names (`src/start_menu.c`, `src/script_menu.c`) that mean a menu is open over the overworld.
#: (Chapter 5 gap round, 2026-11-05, the verifier's F5: a NAME only, no behaviour.) This COARSE table feeds
#: `ScreenState.menu` and still calls the grid `multichoice`, while the menu the skills act on, `ScreenState.ui` from
#: `eyes/screens.py` read_ui (E7), calls it `multichoice_grid`. No skill or brain code reads `menu`; `observation.py`'s
#: digest prints it (a log string).
MENU_TASKS: dict[str, str] = {
    "StartMenuTask": "start_menu",
    "Task_ShowStartMenu": "start_menu",
    "Task_HandleYesNoInput": "yes_no",
    "Task_HandleMultichoiceInput": "multichoice",
    "Task_HandleMultichoiceGridInput": "multichoice",
}
#: Whole-screen states (the framework's `GameState` names) a person reads as a menu or a screen of its own.
MENU_STATES: dict[str, str] = {
    "BAG_MENU": "bag",
    "PARTY_MENU": "party",
    "POKEMON_SUMMARY_SCREEN": "summary",
    "NAMING_SCREEN": "naming",
    "POKE_STORAGE": "pc_storage",
    "CHOOSE_STARTER": "choose_starter",
    "MAIN_MENU": "main_menu",
}
#: A text printer's `state` (`include/text.h`, the enum from RENDER_STATE_HANDLE_CHAR = 0).
RENDER_STATE_NAMES: tuple[str, ...] = ("HANDLE_CHAR", "WAIT", "CLEAR", "SCROLL_START", "SCROLL", "WAIT_SE", "PAUSE")
#: The states in which a printer moves on ONLY when A or B is newly pressed (`src/text.c` RenderText):
#:   * WAIT = 1: `case RENDER_STATE_WAIT: if (TextPrinterWait(textPrinter))`; a text enters it at
#:     `{PAUSE_UNTIL_PRESS}` (`case EXT_CTRL_CODE_PAUSE_UNTIL_PRESS: textPrinter->state = RENDER_STATE_WAIT`),
#:     with NO down arrow. `src/battle_message.c` appends that code to every trainer's lose and win text,
#:     and to "{B_PLAYER_NAME} whited out!"; the party menu's "is already in battle!" (measured on
#:     `ki17_partymenu_wedge.ss1`, printer 6) and "has no energy left to battle!" and the field's Repel,
#:     Itemfinder and bike messages end with it too (`src/strings.c`);
#:   * CLEAR = 2 (`\p`) and SCROLL_START = 3 (`\l`): `TextPrinterWaitWithDownArrow`, the down arrow.
#: Both waits test `JOY_NEW(A_BUTTON | B_BUTTON)`, unless `gTextFlags.autoScroll` is set (then they
#: time out by themselves, `TextPrinterWaitAutoMode`). ‼ Until 2026-10-07 this set was {2, 3}: the eyes
#: said "not waiting" at every trainer's defeat text (found by the step-1 verifier from the decomp;
#: `gates/live_step1.py` arms E10, E7 and XW prove the fix and fail on its revert).
TEXT_PRINTER_WAIT_STATES = frozenset({1, 2, 3})
#: How many text printers the game runs: `RunTextPrinters` (`src/text.c`) renders EVERY active one of
#: `sTextPrinters[WINDOWS_MAX]` (32) each frame, and a printer's index is its window's id. Printer 0 is
#: the field message box and the battle's message window, but the party menu's message is printer 6
#: (measured on `ki17_partymenu_wedge.ss1`), so the eyes read all of them (until 2026-10-07: printer 0 only).
TEXT_PRINTER_COUNT = 32
#: `gTextFlags.autoScroll` (`include/text.h` TextFlags, bit-fields from bit 0: canABSpeedUpPrint,
#: useAlternateDownArrow, autoScroll, forceMidTextSpeed; the order is measured in a battle by
#: `gates/live_step1.py`). Set by `messageautoscroll`, `ShowFieldAutoScrollMessage` and link/recorded battles.
TEXT_FLAG_AUTO_SCROLL = 1 << 2


#: `src/script.c` the global script context's status (`sGlobalScriptContextStatus`): CONTEXT_RUNNING 0,
#: CONTEXT_WAITING 1, CONTEXT_SHUTDOWN 2.
SCRIPT_CONTEXT_SHUTDOWN = 2
#: The script's native function while it waits in `waitbuttonpress` (`src/scrcmd.c` ScrCmd_waitbuttonpress
#: -> `SetupNativeScript(ctx, WaitForAorBPress)`; `WaitForAorBPress` returns TRUE on `JOY_NEW(A_BUTTON)`
#: or `JOY_NEW(B_BUTTON)`).
_WAIT_FOR_BUTTON_NATIVE = "WaitForAorBPress"


def script_waits_for_button(status: int, mode: str, native_function: str | None) -> bool:
    """Is the overworld SCRIPT waiting in `waitbuttonpress`? Its context runs a native function, and that
    function is WaitForAorBPress, AND the context is not shut down. A finished script leaves its last native
    function behind (measured 2026-10-07: `dewford.ss1` idles with status 2 = shut down, mode Stopped and
    native WaitForAorBPress, and nothing waits there). The mode check and the status check EACH refuse that
    leftover (`src/script.c`: a script that ends stops its context, `SCRIPT_MODE_STOPPED`, and the run loop
    then shuts it down): `gates/live_step1.py` arm SW removes both (SW-X1, caught on the fixture's first
    frame) and each alone (SW-R1, SW-R2, not caught): neither is load-bearing alone; together they are.
    This is the wait at the END of most dialogues and of every
    sign (`Std_MsgboxSign`, `Std_MsgboxDefault`: `message; waitmessage; waitbuttonpress`): the text has
    finished printing, its printer is inactive and the message box's mode is already HIDDEN, though the
    box is still on screen (`gates/live_step1.py` arm SW captures it on Dewford's sign).
    `mode` is the framework's ScriptContext mode name ("Native", "Bytecode", "Stopped")."""
    return status != SCRIPT_CONTEXT_SHUTDOWN and mode == "Native" and native_function == _WAIT_FOR_BUTTON_NATIVE


def text_printer_wait(printers: Iterable[tuple[int, int, int]], text_flags: int) -> str | None:
    """Which text waits for A or B: `printers` is (index, active, state) for each text printer, and
    `text_flags` the byte `gTextFlags`. Returns the reason ("text printer 6 WAIT") or None. Under
    autoScroll no printer waits for a button (each wait times out by itself)."""
    if text_flags & TEXT_FLAG_AUTO_SCROLL:
        return None
    for index, active, state in printers:
        if active and state in TEXT_PRINTER_WAIT_STATES:
            name = RENDER_STATE_NAMES[state] if state < len(RENDER_STATE_NAMES) else str(state)
            return f"text printer {index} {name}"
    return None

#: One character per tile and object, for the human-readable picture of the view (`View.ascii`).
GLYPHS: dict[str, str] = {
    "player": "@", "blocked": "#", "water": "~", "tall_grass": '"', "encounter": ":", "door": "D", "warp": "W",
    "floor": ".", "item_ball": "o", "npc": "n", "cut_tree": "t", "smash_rock": "r", "boulder": "b",
    "berry_tree": "B", "sign": "s",
}


def classify_screen(game_state: str, in_battle: bool, text_box_mode: int, active_tasks: Iterable[str]) -> tuple[str, str | None]:
    """(screen, menu) from what is on the screen: `battle`, `menu`, `text`, `overworld`, `transition`,
    `title` or `other`, and the name of the open menu if one is. A whole-screen menu wins over the battle
    it was opened from (the party menu during a battle FILLS the screen; `in_battle` still says so)."""
    if game_state in MENU_STATES:
        return "menu", MENU_STATES[game_state]
    if in_battle or game_state in ("BATTLE", "BATTLE_STARTING", "BATTLE_ENDING"):
        return "battle", None
    if game_state == "OVERWORLD":
        for task in sorted(active_tasks):
            if task in MENU_TASKS:
                return "menu", MENU_TASKS[task]
        if text_box_mode != 0:
            return "text", None
        return "overworld", None
    if game_state == "CHANGE_MAP":
        return "transition", None
    if game_state == "TITLE_SCREEN":
        return "title", None
    return "other", None
