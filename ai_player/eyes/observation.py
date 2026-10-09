"""What the AI sees in one look: the immutable `Observation` (build step 1, design draft §2.1).

WHY IMMUTABLE AND WHY A SNAPSHOT: the game changes between two frames (`PROJECT KNOWLEDGE/
27-INJECTION-SURFACE.md`: state can change between two yields), so the brain must never hold a live
view of memory it could misread later. The eyes build a frozen copy at one frame, stamp it with that
frame number, and the brain looks again when it needs to know more. Everything here is plain data
(numbers, strings, tuples): JSON-able for the action log, comparable in tests, and free of the
framework, so a standalone build keeps it unchanged.

WHAT IS AND IS NOT IN IT (§10.7, "perception like a person"):
  * the tiles and objects INSIDE the on-screen window only (`eyes/view.py` explains the window); an
    object the game keeps loaded off screen is not here, and a hidden item never is. Every person on
    the overworld is an "npc": nothing on screen marks a trainer before it engages (step 1.1);
  * the party, the bag's balls and healing items, money, badges, the Pokedex counts and a small set
    of story flags: a player knows all of these from the menus; the Pokemon in the PC boxes
    (`storage`: who they are and whose, the PC's menus show it), so a catch sent to a box is seen;
  * the player's trainer ID is the VISIBLE 16-bit one (the trainer card's "IDNo."), and so is every
    Pokemon's OT id: ownership is decided on it, and the SECRET id, shown nowhere, is never reported;
  * in battle, both sides' active Pokemon. The FOE is seen as a person sees it (step 1.1): its HP as
    the HP BAR (`BattleMon.hp_bar`, filled pixels of 48; `hp` and `max_hp` are None), and only the
    moves it has USED in this battle (`eyes/view.py` foe_move_seen), with no PP. The player's own
    battlers keep their numbers and all their moves (the player's healthbox and move menu show them);
  * `problems`: what could not be read this frame (a torn party read, no player avatar on the title
    screen). An Observation is always returned; a part that could not be read is None and says why
    here. ‼ None and EMPTY differ: `party` None = not read (the title screen, a torn read), `party`
    () = read, and the player has no Pokemon (a New Game before the starter). Code that counts must
    never read None as 0 (step 1.1: `memory_log.py` took a catch's `dest` from the party COUNT).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ai_player.eyes.view import HP_BAR_PIXELS

__all__ = [
    "BagSummary",
    "BattleMon",
    "BattleView",
    "MenuView",
    "MonSummary",
    "MoveSlot",
    "Observation",
    "PlayerState",
    "Progress",
    "ScreenState",
    "SeenObject",
    "StoredMon",
    "Tile",
    "View",
]


@dataclass(frozen=True)
class Tile:
    """One map tile on screen. `x`, `y` are local map coordinates (they can be negative or past the
    map's size: the screen shows the neighbouring map there); `dx`, `dy` are relative to the player."""

    x: int
    y: int
    dx: int
    dy: int
    metatile: int
    behavior: int
    behavior_name: str
    collision: int  # 0 = passable; anything else blocks (`MapGridGetCollisionAt`)
    elevation: int
    blocked: bool  # collision != 0
    water: bool  # surfable (`sTileBitAttributes` TILE_FLAG_SURFABLE)
    encounter: str | None  # "land" / "water": wild Pokemon can appear here; None: they cannot
    tall_grass: bool  # tall or long grass (`MetatileBehavior_IsPokeGrass`)
    ledge: str | None  # the direction of the jump, if this tile is a ledge
    door: bool
    warp: bool  # the tile LOOKS like a way out by its behaviour (a door, stairs, a ladder, an escalator, an arrow mat, a
    #             hole: `eyes/view.py` EXIT_BEHAVIORS; build step 3.1: no longer the ROM's warp table)
    half_visible: bool  # the top and bottom rows of the window show half a tile

    def flags(self) -> str:
        """The derived facts in a few letters (the action log's compact form): b blocked, w water,
        l land encounters, s water encounters, g tall grass, d door, p warp, h half visible, and the
        ledge's jump direction as > < ^ v (or / for a diagonal)."""
        letters = ""
        if self.blocked:
            letters += "b"
        if self.water:
            letters += "w"
        if self.encounter == "land":
            letters += "l"
        if self.encounter == "water":
            letters += "s"
        if self.tall_grass:
            letters += "g"
        if self.door:
            letters += "d"
        if self.warp:
            letters += "p"
        if self.half_visible:
            letters += "h"
        if self.ledge is not None:
            letters += {"east": ">", "west": "<", "north": "^", "south": "v"}.get(self.ledge, "/")
        return letters

    def compact(self) -> list:
        """[x, y, metatile, behavior, collision, elevation, flags]: everything, in ~25 bytes of JSON."""
        return [self.x, self.y, self.metatile, self.behavior, self.collision, self.elevation, self.flags()]

    def glyph(self) -> str:
        if self.dx == 0 and self.dy == 0:
            return "@"
        if self.door:
            return "D"
        if self.warp:
            return "W"
        if self.ledge is not None:
            return {"east": ">", "west": "<", "north": "^", "south": "v"}.get(self.ledge, "/")
        if self.water:
            return "~"
        if self.blocked:
            return "#"
        if self.tall_grass:
            return '"'
        if self.encounter is not None:
            return ":"
        return "."


@dataclass(frozen=True)
class SeenObject:
    """A thing on screen: a person, a Pokemon, an item ball, a cut tree, a sign."""

    kind: str  # item_ball, npc (every person), cut_tree, smash_rock, boulder, berry_tree, sign
    x: int
    y: int
    dx: int
    dy: int
    local_id: int  # the map's id for an object event; -1 for a sign
    graphics_id: int  # -1 for a sign
    facing: str | None
    elevation: int
    source: str  # "object" (gObjectEvents) or "bg_event" (an interactable tile of the map)


@dataclass(frozen=True)
class View:
    """The on-screen window around the player: `rows` top to bottom, each left to right."""

    left: int
    right: int
    up: int
    down: int
    rows: tuple[tuple[Tile, ...], ...]
    objects: tuple[SeenObject, ...]
    cropped: bool  # False only under the FAULT switch AI_PLAYER_FAULT_NO_CROP

    def tile(self, dx: int, dy: int) -> Tile | None:
        row = dy + self.up
        column = dx + self.left
        if 0 <= row < len(self.rows) and 0 <= column < len(self.rows[row]):
            return self.rows[row][column]
        return None

    def ascii(self) -> tuple[str, ...]:
        """The window as text, one string per row: tiles, with objects drawn over them."""
        marks = {}
        for seen in self.objects:
            marks[(seen.dx, seen.dy)] = {
                "item_ball": "o", "npc": "n", "cut_tree": "t", "smash_rock": "r",
                "boulder": "b", "berry_tree": "B", "sign": "s",
            }.get(seen.kind, "?")
        lines = []
        for row in self.rows:
            lines.append("".join(marks.get((tile.dx, tile.dy), tile.glyph()) if (tile.dx, tile.dy) != (0, 0) else "@" for tile in row))
        return tuple(lines)


@dataclass(frozen=True)
class PlayerState:
    map_group: int
    map_number: int
    map_name: str  # the region-map name the bot's logs use ("ROUTE 101"); interiors share their town's
    map_const: str | None  # the map's own name ("ROUTE_101", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F")
    x: int | None  # None while `settling`
    y: int | None
    facing: str  # down, up, left, right
    movement: str  # walking, running, mach_bike, acro_bike, surfing, underwater
    elevation: int
    avatar_flags: int
    #: The player's VISIBLE trainer id (16 bits: the trainer card's "IDNo.", what a person sees). Ownership
    #: is `MonSummary.ot_id == trainer_id`. (Until step 1.1 this was the full 32-bit id, secret half included.)
    trainer_id: int
    #: True while a WARP settles: the save block already holds the new map and its arrival tile while the
    #: player object still stands on the old map's tile (`eyes/view.py` settled_position). Then `x` and `y`
    #: are None and there is no view: the position is unknown, never one map's tile with the other's name.
    settling: bool = False


@dataclass(frozen=True)
class MoveSlot:
    name: str
    type: str
    power: int
    pp: int | None  # None: not shown to the player (a foe's move)
    max_pp: int | None


@dataclass(frozen=True)
class MonSummary:
    slot: int  # party slot, 0-5
    species: str
    dex: int  # national Pokedex number
    level: int
    hp: int
    max_hp: int
    status: str
    types: tuple[str, ...]
    moves: tuple[MoveSlot, ...]
    pid: int  # personality value: the IDENTITY of this Pokemon (CLAUDE.md rule 3: never a slot)
    ot_id: int  # its original trainer's VISIBLE id (16 bits, the summary screen's "IDNo.")
    is_egg: bool
    experience: int = 0  # total experience points (the summary screen's "EXP. POINTS"); step 3: novelty counts a gain
    #: BUILD STEP 4: (attack, defense, speed, sp. attack, sp. defense), as the summary screen's SKILLS page shows them
    #: (`include/pokemon.h` struct Pokemon @90..@98: the unencrypted stats the party struct keeps). () = not read.
    stats: tuple[int, ...] = ()


@dataclass(frozen=True)
class StoredMon:
    """A Pokemon in a PC box: who it is (PID) and whose (the VISIBLE OT id). Read from the box's
    unencrypted header, so the eyes decrypt nothing for it (`host/eyes.py` _storage)."""

    box: int  # 0-13
    slot: int  # 0-29
    pid: int
    ot_id: int
    is_egg: bool


@dataclass(frozen=True)
class BagSummary:
    balls: tuple[tuple[str, int], ...]  # (item name, quantity) for every ball in the bag
    healing: tuple[tuple[str, int], ...]  # medicine and berries usable to heal HP or a status
    ball_total: int


@dataclass(frozen=True)
class Progress:
    money: int
    badges: tuple[str, ...]  # the BADGE0n_GET flags that are set
    dex_owned: int
    dex_seen: int
    owned_dex: tuple[int, ...]  # national numbers owned (the scorer's `[DEX]` line names the new ones)
    flags: tuple[tuple[str, bool], ...]  # `eyes/view.py` STORY_FLAGS, each with its value


@dataclass(frozen=True)
class BattleMon:
    species: str
    dex: int
    level: int
    hp: int | None  # None for a FOE: a person sees its HP bar, not its numbers
    max_hp: int | None
    hp_bar: int  # filled pixels of the 48-pixel HP bar (`eyes/view.py` hp_bar_pixels): what is drawn
    status: str
    types: tuple[str, ...]  # the LIVE types (Color Change, Camouflage, ... change them)
    #: The player's own battler: all its moves with PP. A FOE: only the moves it has USED in this battle
    #: (seen on screen, `eyes/view.py` foe_move_seen), without PP; the rest are unknown, as for a person.
    moves: tuple[MoveSlot, ...]
    #: BUILD STEP 4: WHICH of the player's Pokemon is out, by identity (its PID; CLAUDE.md rule 3: never a slot): a
    #: person knows which of their own Pokemon they sent out. None for a FOE (nothing on screen shows a PID).
    pid: int | None = None
    #: BUILD STEP 4: WHERE it stands: the battler position (`include/constants/battle.h` B_POSITION_*: 0 the player's
    #: left, 1 the foe's left, 2 the player's right, 3 the foe's right; a single battle uses 0 and 1), as a person sees
    #: which Pokemon stands where in a double battle.
    battler: int | None = None


@dataclass(frozen=True)
class BattleView:
    kind: str  # "wild" or "trainer"
    double: bool
    type_flags: int  # gBattleTypeFlags
    opponent_trainer_id: int | None  # gTrainerBattleOpponent_A in a trainer battle
    own: tuple[BattleMon, ...]
    foe: tuple[BattleMon, ...]


@dataclass(frozen=True)
class MenuView:
    """BUILD STEP 2: the interactive thing on screen that takes the D-pad and A/B, and WHERE ITS CURSOR IS
    (`eyes/screens.py` read_ui says how each is recognised and read). A person sees which option is
    highlighted; the hands move a cursor by reading this, never by counting presses."""

    kind: str  # yes_no, gender, main_menu, start_menu, multichoice, mart_menu, mart_buy, mart_quantity,
    #            naming, clock, bag, party, title, intro_movie; build step 3: battle_action; build step 4: battle_move,
    #            battle_yes_no, move_forget, party_action, bag_action (`eyes/screens.py` read_ui)
    options: tuple[str, ...] = ()  # top to bottom, as shown ("" where the name is not known)
    cursor: int | None = None  # the highlighted option (an index into `options`), or the bag / party row
    #: False while the thing is not taking input yet (a window still opening, a page swapping, the clock's hand
    #: still turning): a press now would be dropped, so the hands wait for True.
    accepts_input: bool = True
    page: str | None = None  # naming: "upper", "lower" or "symbols"
    cursor_xy: tuple[int, int] | None = None  # naming: (column, row); column == the page's count = the buttons
    text: str | None = None  # naming: what is typed so far
    max_chars: int | None = None  # naming
    hours: int | None = None  # clock
    minutes: int | None = None  # clock
    quantity: int | None = None  # mart_quantity: "x NN"
    max_quantity: int | None = None  # mart_quantity: what the money (or the bag) allows
    prices: tuple[int, ...] = ()  # mart_buy: each item's price, as the list shows it
    pocket: str | None = None  # bag: the open pocket
    #: BUILD STEP 4: which of the player's battlers a battle menu is FOR (battle_action, battle_move, battle_target: the
    #: battler position, 0 or 2 in a double battle; 0 in a single one); in battle_target the cursor is a battler position
    battler: int | None = None


@dataclass(frozen=True)
class ScreenState:
    game_state: str  # the framework's GameState name (OVERWORLD, BATTLE, PARTY_MENU, ...)
    screen: str  # overworld, battle, text, menu, transition, title, other
    menu: str | None  # start_menu, yes_no, multichoice, bag, party, summary, ...
    text_box_open: bool  # the overworld message box is up (`sFieldMessageBoxMode`)
    waits_for_button: bool  # the game is waiting for A or B (a script's waitbuttonpress, or a text printer's wait)
    in_battle: bool
    #: WHY it waits, when it does: "script waitbuttonpress", or "text printer N WAIT / CLEAR / SCROLL_START"
    #: (`eyes/view.py` text_printer_wait: WAIT is `{PAUSE_UNTIL_PRESS}`, no arrow; the other two show it), or
    #: (build step 2) "task NAME (A or B)": a task that polls the buttons with no text printer waiting
    #: (`eyes/screens.py` TASK_WAITS).
    wait_reason: str | None = None
    #: BUILD STEP 2: the interactive thing on screen and its cursor (`MenuView`), or None.
    ui: MenuView | None = None
    #: BUILD STEP 2: the message on screen as far as it has PRINTED (`eyes/screens.py` decode_text; a
    #: paragraph break is "¶"): the field / intro / shop message (`gStringVar4`), the battle's
    #: (`gDisplayedStringBattle`) or a string printed straight from the ROM; with no printer active, the
    #: last message printed, while a wait, a menu or the field box shows it (`host/eyes.py` _text has the rule
    #: and its limit); None otherwise.
    text: str | None = None
    #: BUILD STEP 2: an overworld script is running (`sGlobalScriptContextStatus` is not CONTEXT_SHUTDOWN),
    #: and the player's field controls are locked (`sLockFieldControls`, `src/script.c`). While either holds,
    #: an A press next to a person is not "start talking" (the museum-greeter lesson, `08-MISTAKES.md`).
    script_running: bool = False
    controls_locked: bool = False
    #: STEP 2.1: the screen is FADING (`gPaletteFade.active`): a person sees it darken or brighten, and no press
    #: hurries it.
    fading: bool = False
    #: STEP 2.1: WHAT PLAYS, in a person's words, when the game runs by itself ("Professor Birch's speech", "the
    #: wall clock", "the map loading"): `eyes/screens.py` scene_of. The hands name it when they stand still, so no
    #: idle stretch is logged under a catch-all reason. None when no table names it.
    scene: str | None = None


@dataclass(frozen=True)
class Observation:
    frame: int
    screen: ScreenState
    player: PlayerState | None
    view: View | None
    party: tuple[MonSummary, ...] | None  # None = NOT READ (see the module docstring); () = no Pokemon
    bag: BagSummary | None
    progress: Progress | None
    battle: BattleView | None
    last_battle_outcome: int  # gBattleOutcome: 0 while a battle runs; the result after it
    problems: tuple[str, ...]
    cost_ms: float  # how long this look took
    #: Every Pokemon in the 14 PC boxes (None = not read). Step 1.1: a catch sent to a box is SEEN here.
    storage: tuple[StoredMon, ...] | None = None

    #: The compact columns of a stored Pokemon in the action log.
    STORAGE_FIELDS = ("box", "slot", "pid", "ot_id", "is_egg")

    def to_dict(self, compact: bool = True) -> dict:
        """JSON-able. The view carries its picture (`ascii`), for people reading the log. COMPACT (the
        action log's form) writes each tile as `Tile.compact()` instead of 17 named fields: a full
        record is ~42 KB, a compact one a tenth of that, and nothing is lost (names and booleans are
        derived from the numbers and the flags). The PC boxes are written as rows too
        (`STORAGE_FIELDS`)."""
        data = asdict(self)
        if self.view is not None:
            data["view"]["ascii"] = list(self.view.ascii())
            if compact:
                del data["view"]["rows"]
                data["view"]["tiles"] = [tile.compact() for row in self.view.rows for tile in row]
                data["view"]["tile_fields"] = ["x", "y", "metatile", "behavior", "collision", "elevation", "flags"]
        if compact and self.storage is not None:
            data["storage"] = [[m.box, m.slot, m.pid, m.ot_id, int(m.is_egg)] for m in self.storage]
            data["storage_fields"] = list(self.STORAGE_FIELDS)
        return data

    def digest(self) -> str:
        """One line a person can read: where, what, who."""
        parts = [f"f{self.frame}", self.screen.screen]
        if self.screen.menu:
            parts.append(f"menu={self.screen.menu}")
        if self.screen.waits_for_button:
            parts.append(f"waits=A/B({self.screen.wait_reason})" if self.screen.wait_reason else "waits=A/B")
        ui = self.screen.ui
        if ui is not None:
            parts.append(f"ui={ui.kind}" + ("" if ui.accepts_input else "(busy)") + _ui_detail(ui))
        player = self.player
        if player is not None:
            parts.append(f"{player.map_name}({player.map_group},{player.map_number})")
            where = "xy=settling" if player.settling else f"xy=({player.x},{player.y})"
            parts.append(f"{where} facing={player.facing} {player.movement}")
        if self.party is None:
            parts.append("party=?")
        elif self.party:
            parts.append("party=[" + ",".join(f"{m.species}:L{m.level} {m.hp}/{m.max_hp}" for m in self.party) + "]")
        if self.storage:
            parts.append(f"boxed={len(self.storage)}")
        if self.battle is not None:
            foe = ",".join(f"{m.species}:L{m.level} bar {m.hp_bar}/{HP_BAR_PIXELS}" for m in self.battle.foe)
            parts.append(f"battle={self.battle.kind} foe=[{foe}]")
            if self.battle.opponent_trainer_id is not None:
                parts.append(f"trainer={self.battle.opponent_trainer_id}")
        if self.view is not None:
            seen = ",".join(f"{o.kind}({o.dx},{o.dy})" for o in self.view.objects)
            parts.append(f"sees=[{seen}]")
        if self.progress is not None:
            parts.append(f"dex={self.progress.dex_owned}/{self.progress.dex_seen} money={self.progress.money} badges={len(self.progress.badges)}")
        if self.problems:
            parts.append(f"problems={len(self.problems)}")
        parts.append(f"cost={self.cost_ms:.2f}ms")
        return " ".join(parts)


def _ui_detail(ui: MenuView) -> str:
    """The cursor of a `MenuView` in a few characters, for the one-line digest."""
    if ui.kind == "naming":
        return f"[{ui.page} at {ui.cursor_xy} text={ui.text!r}]"
    if ui.kind == "clock":
        return f"[{ui.hours}:{ui.minutes:02d}]" if ui.hours is not None and ui.minutes is not None else ""
    if ui.kind == "mart_quantity":
        return f"[x{ui.quantity} max {ui.max_quantity}]"
    if ui.cursor is not None and 0 <= ui.cursor < len(ui.options):
        return f"[{ui.options[ui.cursor]}]"
    if ui.cursor is not None:
        return f"[{ui.cursor}]"
    return ""
