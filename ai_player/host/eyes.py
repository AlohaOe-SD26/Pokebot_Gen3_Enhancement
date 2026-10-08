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
  * ROM data (tileset attributes, the tile-flag table, a map's warps and signs) never changes, so it
    is read once per tileset or map and kept; everything that lives in RAM is read every look;
  * "waits for a button" reads all 32 text printers and `gTextFlags` (`eyes/view.py` text_printer_wait
    has the decomp's rule), and says WHY in `ScreenState.wait_reason`.

COST: `gates/live_step1.py` and `gates/test_eyes.py` measure `cost_ms` (it is in every Observation).
"""

from __future__ import annotations

import time

from modules.battle_state import battle_is_active, get_battle_state
from modules.context import context
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
    Tile,
    View,
)
from ai_player.eyes.view import (
    BADGE_FLAGS,
    DOOR_BEHAVIORS,
    LEDGE_DIRECTIONS,
    STORY_FLAGS,
    TALL_GRASS_BEHAVIORS,
    TEXT_PRINTER_COUNT,
    TILE_FLAG_HAS_ENCOUNTERS,
    TILE_FLAG_SURFABLE,
    VIEW_DOWN,
    VIEW_HALF_WIDTH,
    VIEW_UP,
    behavior_name,
    classify_screen,
    facing_name,
    in_view,
    movement_mode,
    object_kind,
    status_name,
    text_printer_wait,
)
from ai_player.eyes.party import PARTY_MON_SIZE, decode_party_mon
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
#: `src/script.c`: the global script context's status, and its mode.
CONTEXT_SHUTDOWN = 2
#: `include/text.h` struct TextPrinter: 0x24 bytes; `active` @0x1B, `state` @0x1C (`sTextPrinters`).
TEXT_PRINTER_SIZE, TEXT_PRINTER_ACTIVE, TEXT_PRINTER_STATE = 0x24, 0x1B, 0x1C
#: `include/global.fieldmap.h` struct MapHeader (0x1C bytes). Its first field, the layout pointer, is
#: re-pointed at load (`gMapHeader.mapLayout = GetMapLayout()`, `src/overworld.c`), so it may differ from
#: the ROM's; every other byte is the ROM header's, copied (`gMapHeader = *Overworld_GetMapHeaderByGroupAndId`).
MAP_HEADER_SIZE, MAP_HEADER_COPIED_FROM = 0x1C, 4
#: `include/constants/battle.h` BATTLE_TYPE_TRAINER.
BATTLE_TYPE_TRAINER = 1 << 3
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
                                            waits_for_button=False, in_battle=False),
                player=None, view=None, party=(), bag=None, progress=None, battle=None, last_battle_outcome=0,
                problems=("no frame has run yet (frame 0): there is nothing to see",),
                cost_ms=round((time.perf_counter() - start) * 1000.0, 3),
            )
        screen = self._screen(problems)
        player = view = party = bag = progress = battle = None
        outcome = 0
        if screen.game_state not in _NO_GAME_YET:
            player = self._guarded("player", problems, self._player)
            party = self._guarded("party", problems, lambda: self._party(problems))
            bag = self._guarded("bag", problems, self._bag)
            progress = self._guarded("progress", problems, self._progress)
            outcome = self._guarded("battle outcome", problems, lambda: read_symbol("gBattleOutcome", size=1)[0]) or 0
            if player is not None and screen.game_state == "OVERWORLD":
                view = self._guarded("view", problems, lambda: self._view(player))
            if screen.in_battle and screen.game_state == "BATTLE":
                battle = self._guarded("battle", problems, self._battle)
        self.looks += 1
        return Observation(
            frame=frame,
            screen=screen,
            player=player,
            view=view,
            party=tuple(party or ()),
            bag=bag,
            progress=progress,
            battle=battle,
            last_battle_outcome=int(outcome),
            problems=tuple(problems),
            cost_ms=round((time.perf_counter() - start) * 1000.0, 3),
        )

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
        tasks = self._guarded("tasks", problems, lambda: frozenset(task.symbol for task in get_tasks())) or frozenset()
        reason = self._guarded("button wait", problems, self._waits_for_button)
        kind, menu = classify_screen(game_state, in_battle, text_box_mode, tasks)
        return ScreenState(game_state=game_state, screen=kind, menu=menu, text_box_open=text_box_mode != 0,
                           waits_for_button=reason is not None, in_battle=in_battle, wait_reason=reason)

    @staticmethod
    def _waits_for_button() -> str | None:
        """WHY the game waits for A or B, or None: a running script waiting in `waitbuttonpress` (its native
        function is WaitForAorBPress and the context is not shut down: a finished script leaves its last
        native function behind), or ANY active text printer in a state that moves on only when A or B is
        pressed (`eyes/view.py` text_printer_wait: WAIT, the `{PAUSE_UNTIL_PRESS}` of every trainer's
        defeat text, and CLEAR / SCROLL_START, the down arrow), unless `gTextFlags` says autoScroll."""
        status = read_symbol("sGlobalScriptContextStatus", size=1)[0]
        script = get_global_script_context()
        if status != CONTEXT_SHUTDOWN and script.mode == "Native" and script.native_function_name == "WaitForAorBPress":
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
        location = context.emulator.read_bytes(save_block_1 + 4, 2)
        group, number = location[0], location[1]
        name, const = self._map_names(group, number)
        # The FULL id, as a Pokemon's OT field stores it: the visible id in the low half, the secret id in
        # the high half. (The framework's `trainer_id` is the visible half only; comparing it with an OT
        # field never matches, which a probe caught on the first fixture.)
        owner = get_player()
        trainer = owner.trainer_id | (owner.secret_id << 16)
        return PlayerState(
            map_group=group,
            map_number=number,
            map_name=name,
            map_const=const,
            x=_s16(player_object, 0x10) - MAP_OFFSET,
            y=_s16(player_object, 0x12) - MAP_OFFSET,
            facing=facing_name(player_object[0x18] & 0x0F),
            movement=movement_mode(flags),
            elevation=player_object[0x0B] & 0x0F,
            avatar_flags=flags,
            trainer_id=trainer,
        )

    def _map_names(self, group: int, number: int) -> tuple[str, str | None]:
        return self._map_facts(group, number)[:2]

    def _map_facts(self, group: int, number: int) -> tuple:
        """(region-map name, map constant, warp tiles, interactable tiles) of a map, read once: a map's
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
            warps = frozenset(warp.local_coordinates for warp in location.warps)
            signs = tuple(
                (event.local_coordinates, event.elevation) for event in location.bg_events if event.kind == "Script"
            )
            self._maps[key] = (location.map_name, const, warps, signs)
        return self._maps[key]

    @staticmethod
    def _rom_map_header(group: int, number: int) -> bytes:
        """Map (group, number)'s header as the ROM holds it: `gMapGroups[group]` points to the group's
        table of header pointers (`include/global.fieldmap.h`, `data/maps/map_groups.inc`). Three ROM reads."""
        table = _u32(read_symbol("gMapGroups", 4 * group, 4), 0)
        pointer = _u32(context.emulator.read_bytes(table + 4 * number, 4), 0)
        return context.emulator.read_bytes(pointer, MAP_HEADER_SIZE)

    # ------------------------------------------------------------------ the view
    def _view(self, player: PlayerState) -> View:
        layout = read_symbol("gBackupMapLayout", size=12)
        width, height, grid = _s32(layout, 0), _s32(layout, 4), _u32(layout, 8)
        header = read_symbol("gMapHeader", size=0x1C)
        map_layout = context.emulator.read_bytes(_u32(header, 0), 24)
        border = context.emulator.read_bytes(_u32(map_layout, 8), 8)
        primary = self._tileset_attributes(_u32(map_layout, 16))
        secondary = self._tileset_attributes(_u32(map_layout, 20))
        tile_bits = self._tile_flags()
        _, _, warps, signs = self._map_facts(player.map_group, player.map_number)
        rows = []
        for dy in range(-VIEW_UP, VIEW_DOWN + 1):
            vy = player.y + MAP_OFFSET + dy
            left = player.x + MAP_OFFSET - VIEW_HALF_WIDTH
            count = 2 * VIEW_HALF_WIDTH + 1
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
                                      tile_bits, warps, dy))
            rows.append(tuple(row))
        objects = self._objects(player) + self._signs(player, signs)
        return View(left=VIEW_HALF_WIDTH, right=VIEW_HALF_WIDTH, up=VIEW_UP, down=VIEW_DOWN, rows=tuple(rows),
                    objects=tuple(objects), cropped=self.crop)

    @staticmethod
    def _tile(player: PlayerState, x: int, y: int, block: int, border: bytes, primary: bytes, secondary: bytes,
              tile_bits: bytes, warps: frozenset, dy: int) -> Tile:
        """One grid block, decoded as `src/fieldmap.c` does (`MapGridGetCollisionAt`, `...ElevationAt`,
        `...MetatileIdAt`, `GetMetatileAttributesById`)."""
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
            ledge=LEDGE_DIRECTIONS.get(behavior), door=behavior in DOOR_BEHAVIORS, warp=(x, y) in warps,
            half_visible=dy == -VIEW_UP or dy == VIEW_DOWN,
        )

    def _tileset_attributes(self, tileset: int) -> bytes:
        """`struct Tileset` .metatileAttributes (offset 0x10): one u16 per metatile. ROM, read once."""
        if tileset not in self._attributes:
            pointer = _u32(context.emulator.read_bytes(tileset + 0x10, 4), 0)
            self._attributes[tileset] = context.emulator.read_bytes(pointer, 2 * METATILES_IN_PRIMARY)
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
                kind=object_kind(event.graphics_id, event.trainer_type != "None"), x=x, y=y, dx=x - player.x,
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
    def _party(self, problems: list[str]) -> list[MonSummary]:
        count = min(read_symbol("gPlayerPartyCount", size=1)[0], PARTY_SIZE)
        raw = read_symbol("gPlayerParty", size=PARTY_MON_SIZE * PARTY_SIZE)
        party = []
        for slot in range(count):
            data = raw[slot * PARTY_MON_SIZE:(slot + 1) * PARTY_MON_SIZE]
            try:
                mon = self._mon(slot, data)
            except Exception as error:  # noqa: BLE001 - one bad slot must not hide the others
                mon = f"{type(error).__name__}: {error}"
            if isinstance(mon, str):
                problems.append(f"party slot {slot + 1}: {mon}")
                continue
            party.append(mon)
        return party

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
            moves=tuple(moves), pid=raw.personality, ot_id=raw.ot_id, is_egg=raw.is_egg,
        )

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
        state = get_battle_state()
        type_flags = _u32(read_symbol("gBattleTypeFlags", size=4), 0)
        trainer = bool(type_flags & BATTLE_TYPE_TRAINER)
        opponent = _u16(read_symbol("gTrainerBattleOpponent_A", size=2), 0) if trainer else None
        return BattleView(
            kind="trainer" if trainer else "wild",
            double=state.is_double_battle,
            type_flags=type_flags,
            opponent_trainer_id=opponent,
            own=tuple(self._battle_mon(mon) for mon in state.own_side.active_battlers),
            foe=tuple(self._battle_mon(mon) for mon in state.opponent.active_battlers),
        )

    @staticmethod
    def _battle_mon(mon) -> BattleMon:
        moves = tuple(
            MoveSlot(name=slot.move.name, type=slot.move.type.name, power=slot.move.base_power, pp=slot.pp,
                     max_pp=slot.total_pp)
            for slot in mon.moves if slot is not None
        )
        return BattleMon(
            species=mon.species.name, dex=mon.species.national_dex_number, level=mon.level, hp=mon.current_hp,
            max_hp=mon.total_hp, status=_BATTLE_STATUS.get(mon.status_permanent.name, mon.status_permanent.name),
            types=tuple(t.name for t in mon.types), moves=moves,
        )


seal_module(__name__)
