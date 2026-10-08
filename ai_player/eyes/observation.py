"""What the AI sees in one look: the immutable `Observation` (build step 1, design draft §2.1).

WHY IMMUTABLE AND WHY A SNAPSHOT: the game changes between two frames (`PROJECT KNOWLEDGE/
27-INJECTION-SURFACE.md`: state can change between two yields), so the brain must never hold a live
view of memory it could misread later. The eyes build a frozen copy at one frame, stamp it with that
frame number, and the brain looks again when it needs to know more. Everything here is plain data
(numbers, strings, tuples): JSON-able for the action log, comparable in tests, and free of the
framework, so a standalone build keeps it unchanged.

WHAT IS AND IS NOT IN IT (§10.7, "perception like a person"):
  * the tiles and objects INSIDE the on-screen window only (`eyes/view.py` explains the window); an
    object the game keeps loaded off screen is not here, and a hidden item never is;
  * the party, the bag's balls and healing items, money, badges, the Pokedex counts and a small set
    of story flags: a player knows all of these from the menus;
  * in battle, both sides' active Pokemon. ‼ The FOE's exact HP and its moves are more than a person
    sees (the HP bar, and the moves only once used); they are reported because the build plan asks
    for them, and the battle decider (step 4) must treat foe HP as a fraction and foe moves as
    unknown until seen;
  * `problems`: what could not be read this frame (a torn party read, no player avatar on the title
    screen). An Observation is always returned; a part that could not be read is None or empty,
    and says why here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

__all__ = [
    "BagSummary",
    "BattleMon",
    "BattleView",
    "MonSummary",
    "MoveSlot",
    "Observation",
    "PlayerState",
    "Progress",
    "ScreenState",
    "SeenObject",
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
    warp: bool  # a warp of the current map is on this tile (a door, stairs, a ladder, a cave mouth)
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

    kind: str  # item_ball, trainer, npc, cut_tree, smash_rock, boulder, berry_tree, sign
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
                "item_ball": "o", "trainer": "T", "npc": "n", "cut_tree": "t", "smash_rock": "r",
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
    x: int
    y: int
    facing: str  # down, up, left, right
    movement: str  # walking, running, mach_bike, acro_bike, surfing, underwater
    elevation: int
    avatar_flags: int
    trainer_id: int  # the player's FULL trainer id (visible | secret << 16), as a Pokemon's OT field holds it


@dataclass(frozen=True)
class MoveSlot:
    name: str
    type: str
    power: int
    pp: int
    max_pp: int


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
    ot_id: int  # its original trainer's id
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
    hp: int
    max_hp: int
    status: str
    types: tuple[str, ...]  # the LIVE types (Color Change, Camouflage, ... change them)
    moves: tuple[MoveSlot, ...]


@dataclass(frozen=True)
class BattleView:
    kind: str  # "wild" or "trainer"
    double: bool
    type_flags: int  # gBattleTypeFlags
    opponent_trainer_id: int | None  # gTrainerBattleOpponent_A in a trainer battle
    own: tuple[BattleMon, ...]
    foe: tuple[BattleMon, ...]


@dataclass(frozen=True)
class ScreenState:
    game_state: str  # the framework's GameState name (OVERWORLD, BATTLE, PARTY_MENU, ...)
    screen: str  # overworld, battle, text, menu, transition, title, other
    menu: str | None  # start_menu, yes_no, multichoice, bag, party, summary, ...
    text_box_open: bool  # the overworld message box is up (`sFieldMessageBoxMode`)
    waits_for_button: bool  # the game is waiting for A or B (a script's waitbuttonpress, or a text printer's wait)
    in_battle: bool
    #: WHY it waits, when it does: "script waitbuttonpress", or "text printer N WAIT / CLEAR / SCROLL_START"
    #: (`eyes/view.py` text_printer_wait: WAIT is `{PAUSE_UNTIL_PRESS}`, no arrow; the other two show it).
    wait_reason: str | None = None


@dataclass(frozen=True)
class Observation:
    frame: int
    screen: ScreenState
    player: PlayerState | None
    view: View | None
    party: tuple[MonSummary, ...]
    bag: BagSummary | None
    progress: Progress | None
    battle: BattleView | None
    last_battle_outcome: int  # gBattleOutcome: 0 while a battle runs; the result after it
    problems: tuple[str, ...]
    cost_ms: float  # how long this look took

    def to_dict(self, compact: bool = True) -> dict:
        """JSON-able. The view carries its picture (`ascii`), for people reading the log. COMPACT (the
        action log's form) writes each tile as `Tile.compact()` instead of 17 named fields: a full
        record is ~42 KB, a compact one a tenth of that, and nothing is lost (names and booleans are
        derived from the numbers and the flags)."""
        data = asdict(self)
        if self.view is not None:
            data["view"]["ascii"] = list(self.view.ascii())
            if compact:
                del data["view"]["rows"]
                data["view"]["tiles"] = [tile.compact() for row in self.view.rows for tile in row]
                data["view"]["tile_fields"] = ["x", "y", "metatile", "behavior", "collision", "elevation", "flags"]
        return data

    def digest(self) -> str:
        """One line a person can read: where, what, who."""
        parts = [f"f{self.frame}", self.screen.screen]
        if self.screen.menu:
            parts.append(f"menu={self.screen.menu}")
        if self.screen.waits_for_button:
            parts.append(f"waits=A/B({self.screen.wait_reason})" if self.screen.wait_reason else "waits=A/B")
        player = self.player
        if player is not None:
            parts.append(f"{player.map_name}({player.map_group},{player.map_number})")
            parts.append(f"xy=({player.x},{player.y}) facing={player.facing} {player.movement}")
        if self.party:
            parts.append("party=[" + ",".join(f"{m.species}:L{m.level} {m.hp}/{m.max_hp}" for m in self.party) + "]")
        if self.battle is not None:
            foe = ",".join(f"{m.species}:L{m.level} {m.hp}/{m.max_hp}" for m in self.battle.foe)
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
