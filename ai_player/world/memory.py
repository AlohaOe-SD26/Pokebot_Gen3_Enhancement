"""The AI's MAP MEMORY (build step 3; design draft §2.3, §10.4, §10.7): what it has SEEN, map by map. Framework-free.

WHY A MEMORY BUILT ONLY FROM LOOKS (RULING 35, design draft §10.7 "perception like a person"): a person learns a
town by walking it. The eyes show a 15 x 11 window around the player (`eyes/view.py`); every tile that window has
ever shown is remembered here, with WHERE THE PLAYER STOOD when it was first seen (`TileFact.seen_from`), so "the
AI knows only what it saw" is a property a test can check on the memory itself (`gates/live_step3.py`: every
known tile lies inside the window of the place it was seen from; the CROP fault arm breaks exactly that). Nothing
here reads the game, the map's layout or the ROM's map data; the AI's own code fills it, one look at a time
(`WorldMemory.observe`, called on EVERY look the hands take: `hands/pad.py` Hands.watchers).

WHAT IT LEARNS, AND HOW
  * TILES: as the eyes report them (`eyes/observation.py` Tile): blocked (collision), water, tall grass, wild
    encounters, a ledge and its jump direction, a door, a warp, the elevation and the behaviour's name. A tile seen
    again with other facts is updated (a script can open a door: `setmetatile`).
  * VISITS: how often the player has stood on each tile (the roaming metric and the explorer's "least visited").
  * PEOPLE AND THINGS: where people (transient: they walk) and item balls were seen.
  * BUMPS: a tile the player tried to walk onto FROM ONE SIDE and did not move (`learn_bump`; the navigator decides
    it was not a person in the way): "a hidden wall". The eyes call such a tile walkable (collision 0) when what
    stops the player is something a person cannot see on a still screen either: an ELEVATION step
    (`src/event_object_movement.c` IsElevationMismatchAt: a tile of elevation 4 next to the player's 3), a one-way tile
    (IMPASSABLE_*: `IsMetatileDirectionallyImpassable` blocks some directions only). Since build step 3.1 (the step-3
    review's finding 4: "one bump = a permanent wall from every side") a bump is kept by (tile, DIRECTION): entering
    that tile that way costs much more after one bump (`navigator.BUMP_RETRY_COST`: tried again only when every other
    way is dearer) and is refused after `BUMP_GIVE_UP` bumps; entering it from another side is a fresh question, so a
    one-way tile is crossed the way it lets the player through. Standing on the tile no longer clears its bumps (one
    reaches a one-way tile from its open side).
  * MAP CHANGES (`Transition`), classified by what the looks showed in between: a WARP (a fade, the map loading,
    the position settling: a door, a mat, stairs) or a CONNECTION (seamless: the next look is already on the new
    map, the player walked off the edge). A warp becomes a link `(map, tile) -> (map, arrival)` in the WARP GRAPH,
    and the warp tile at or next to the arrival becomes the inferred way BACK (a person knows the door they came out
    of). A connection becomes a link with its OFFSET between the two maps' coordinates, and it teaches both maps'
    EDGES (`MapMemory.edges`: per side, the first coordinate OUTSIDE the map, learned only when a crossing was SEEN:
    build step 3.1, the step-3 review's finding 1. The memory used to call every tile at x < 0 or y < 0 "past the
    edge" from the coordinates alone, which a person cannot see: across a connection the screen shows the next map
    seamlessly, so a tile past an edge never crossed is just a tile, and the explorer treats it as the frontier it
    looks like. A test shifts every coordinate by +50 and expects the same choice: `gates/test_world.py`).
  * EXITS by how they LOOK (`eyes/view.py` EXIT_BEHAVIORS: doors, stairs, mats; build step 3.1, finding 5), and what a
    look cannot say is learned by USING them: where one leads (the warp graph) and that a door-looking tile does
    not open (`MapMemory.closed`: pressed into properly, nothing happened). NOT FOR GOOD (the step-3.1 verifier: "a
    door found closed stays closed for good ... could permanently hide a door that a flag opens"): a closed door is
    worth a try again once the STORY has moved on since it was found closed (one of the eyes' story flags newly set:
    the events a player has seen) or after `CLOSED_RETRY_FRAMES` (a person tries a locked door again later). The
    memory reopens it (`WorldMemory.observe`) and keeps what it reopened for the navigator to tell (`take_reopened`).
  * Who caused a change: the AI's own step or warp (the navigator says what it is doing: `intend`), or a SCENE (a
    script moved the player: Mom sending you back upstairs), recorded as `by`.

PERSISTENCE: `to_dict` / `from_dict`, one JSON object; the brain appends a snapshot line to `<run_dir>/world.jsonl`
(`ai_player/runlog.py` RecordFile: the gate's one file writer) at every map change and at the end, and a later run
can start from a file's last line (`read_world`, read mode only), so knowledge grows over a playthrough.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace

from ai_player.eyes.observation import Observation, Tile
from ai_player.eyes.view import VIEW_DOWN, VIEW_HALF_WIDTH, VIEW_UP

__all__ = [
    "ABSORB_EVERY",
    "AXIS",
    "CLOSED_RETRY_FRAMES",
    "DIRECTIONS",
    "LEDGE_DIRECTIONS",
    "OPPOSITE",
    "MapMemory",
    "TileFact",
    "Transition",
    "WorldMemory",
    "BUMP_GIVE_UP",
    "in_window",
    "learn_edges",
    "map_key",
    "moved",
    "past_edge",
    "read_world",
    "road_side",
]

#: The D-pad directions and the step each makes (local map coordinates: x right, y down).
DIRECTIONS: dict[str, tuple[int, int]] = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
OPPOSITE: dict[str, str] = {"up": "down", "down": "up", "left": "right", "right": "left"}
#: The coordinate a side's edge is measured on (0: x, 1: y), and which way "past it" lies (-1: smaller, +1: larger).
AXIS: dict[str, tuple[int, int]] = {"up": (1, -1), "down": (1, 1), "left": (0, -1), "right": (0, 1)}
#: A ledge's jump direction as the eyes name it (`eyes/view.py` LEDGE_DIRECTIONS) -> the D-pad direction that jumps
#: it. A diagonal ledge has no D-pad direction: the navigator treats it as a wall (none on v1's maps).
LEDGE_DIRECTIONS: dict[str, str] = {"north": "up", "south": "down", "west": "left", "east": "right"}
#: A look absorbs the window again when the player or the map changed, or at least this many frames after the last.
ABSORB_EVERY = 60
#: Bumps into one tile FROM ONE SIDE after which that way in is a wall (build step 3.1, finding 4): the first bump makes
#: it dear (`brain/navigator.py` BUMP_RETRY_COST: tried again only when every other way costs more), the second ends it.
BUMP_GIVE_UP = 2
#: (the step-3.1 verifier's round) Frames after which a door found closed is worth a try again even with no story news
#: (36,000: ten minutes of play at 60 frames a second).
CLOSED_RETRY_FRAMES = 36_000


def map_key(group: int, number: int) -> str:
    """A map's identity in the memory (and its JSON): "group:number"."""
    return f"{group}:{number}"


def moved(xy: tuple[int, int], direction: str) -> tuple[int, int]:
    dx, dy = DIRECTIONS[direction]
    return xy[0] + dx, xy[1] + dy


def past_edge(edges: dict[str, int], xy: tuple[int, int], side: str) -> bool:
    """Is `xy` past the map's `side` edge, as far as the AI KNOWS (an edge it has seen crossed; build step 3.1)?"""
    if side not in edges:
        return False
    axis, sign = AXIS[side]
    return xy[axis] <= edges[side] if sign < 0 else xy[axis] >= edges[side]


def road_side(memory: "MapMemory", xy: tuple[int, int]) -> str:
    """Which side of the map a road tile (past an edge the AI has seen crossed) lies on; "inside" if none."""
    return next((side for side in ("up", "down", "left", "right") if past_edge(memory.edges, xy, side)), "inside")


def in_window(seen_from: tuple[int, int], xy: tuple[int, int]) -> bool:
    """Was `xy` inside the on-screen window while the player stood on `seen_from`? (`eyes/view.py` in_view.)"""
    return abs(xy[0] - seen_from[0]) <= VIEW_HALF_WIDTH and -VIEW_UP <= xy[1] - seen_from[1] <= VIEW_DOWN


@dataclass(frozen=True)
class TileFact:
    """One tile as the eyes showed it, and when and from where it was first seen."""

    blocked: bool  # the eyes' `blocked` (collision != 0)
    water: bool
    grass: bool  # tall grass (`MetatileBehavior_IsPokeGrass`)
    encounter: bool  # wild Pokemon can appear here (land or water)
    ledge: str | None  # the D-pad direction that jumps it ("up", ...), "diagonal", or None
    door: bool
    warp: bool
    elevation: int
    behavior: str
    seen_frame: int
    seen_from: tuple[int, int]

    @classmethod
    def of(cls, tile: Tile, frame: int, seen_from: tuple[int, int]) -> "TileFact":
        ledge = None if tile.ledge is None else LEDGE_DIRECTIONS.get(tile.ledge, "diagonal")
        return cls(blocked=tile.blocked, water=tile.water, grass=tile.tall_grass, encounter=tile.encounter is not None,
                   ledge=ledge, door=tile.door, warp=tile.warp, elevation=tile.elevation, behavior=tile.behavior_name,
                   seen_frame=frame, seen_from=seen_from)

    def same_as(self, other: "TileFact") -> bool:
        """The same tile facts (when and from where it was seen aside)."""
        return (self.blocked, self.water, self.grass, self.encounter, self.ledge, self.door, self.warp, self.elevation,
                self.behavior) == (other.blocked, other.water, other.grass, other.encounter, other.ledge, other.door,
                                   other.warp, other.elevation, other.behavior)

    @property
    def walkable(self) -> bool:
        """A person would walk onto it: not a wall, not water, not a ledge, not an exit (a warp or a door is used on
        purpose, never walked through on the way somewhere)."""
        return not (self.blocked or self.water or self.ledge is not None or self.warp or self.door)

    def compact(self) -> list:
        letters = "".join(letter for letter, on in (("b", self.blocked), ("w", self.water), ("g", self.grass),
                                                    ("e", self.encounter), ("d", self.door), ("p", self.warp)) if on)
        return [letters, self.ledge or "", self.elevation, self.behavior, self.seen_frame, self.seen_from[0], self.seen_from[1]]

    @classmethod
    def from_compact(cls, data: list) -> "TileFact":
        letters, ledge, elevation, behavior, frame, fx, fy = data
        return cls(blocked="b" in letters, water="w" in letters, grass="g" in letters, encounter="e" in letters,
                   ledge=ledge or None, door="d" in letters, warp="p" in letters, elevation=int(elevation),
                   behavior=str(behavior), seen_frame=int(frame), seen_from=(int(fx), int(fy)))


def _xy(text: str) -> tuple[int, int]:
    x, y = text.split(",")
    return int(x), int(y)


def _text(xy: tuple[int, int]) -> str:
    return f"{xy[0]},{xy[1]}"


def _bump_key(text: str, info: dict) -> tuple[tuple[int, int], str]:
    """A persisted bump's key: "x,y|direction" (build step 3.1); a file written before keeps "x,y" and the direction in
    its info (every bump was recorded with the direction it came from)."""
    if "|" in text:
        where, direction = text.split("|")
        return _xy(where), direction
    return _xy(text), str(info.get("direction") or "?")


class MapMemory:
    """Everything the AI knows of ONE map, in that map's own local coordinates. Tiles past the map's edges are kept
    too (the screen shows the next map or the border there): they are where the roads lead."""

    def __init__(self, key: str, name: str = "", const: str | None = None) -> None:
        self.key = key
        self.name = name
        self.const = const
        self.tiles: dict[tuple[int, int], TileFact] = {}
        self.visits: dict[tuple[int, int], int] = {}
        #: (tile, the direction the player was moving when it did not get in) -> {"from", "first", "last", "bumps"}
        self.bumped: dict[tuple[tuple[int, int], str], dict] = {}
        #: exit-looking tiles that took the player nowhere when used properly (a closed door): tile -> {"frame", ...}
        self.closed: dict[tuple[int, int], dict] = {}
        self.people: dict[tuple[int, int], int] = {}  # tile -> the last frame a person was seen standing there
        self.items: dict[tuple[int, int], int] = {}  # item balls: tile -> the last frame seen
        self.objects_now: frozenset[tuple[int, int]] = frozenset()  # every object on the LAST look (people, balls, ...)
        #: per side ("up", "down", "left", "right"): the first coordinate OUTSIDE the map, learned at a crossing SEEN
        self.edges: dict[str, int] = {}
        self.first_frame: int | None = None
        self.arrivals: list[list] = []  # [frame, x, y, how]

    # ------------------------------------------------------------------ facts
    def fact(self, xy: tuple[int, int]) -> TileFact | None:
        return self.tiles.get(xy)

    def known(self, xy: tuple[int, int]) -> bool:
        return xy in self.tiles

    def outside(self, xy: tuple[int, int]) -> bool:
        """Past one of this map's edges, as far as the AI KNOWS: only an edge it has seen crossed (build step 3.1). The
        coordinates alone say nothing: a person cannot see where a map ends across a connection."""
        return any(past_edge(self.edges, xy, side) for side in self.edges)

    def passable(self, xy: tuple[int, int]) -> bool:
        """Known and walkable (a bump is a matter of which way in: `bumps`)."""
        fact = self.tiles.get(xy)
        return fact is not None and fact.walkable

    def bumps(self, xy: tuple[int, int], direction: str) -> int:
        """How often the player did not get onto `xy` moving `direction` (no person in the way)."""
        return int((self.bumped.get((xy, direction)) or {}).get("bumps", 0))

    def bumped_tiles(self) -> list[tuple[int, int]]:
        return sorted({xy for xy, _ in self.bumped})

    def unknown_neighbours(self, xy: tuple[int, int]) -> int:
        return sum(1 for direction in DIRECTIONS if moved(xy, direction) not in self.tiles)

    def frontier(self) -> list[tuple[int, int]]:
        """Seen tiles a person could walk to that border UNSEEN ones: walking there shows more of the map. Tiles past an
        edge the AI has seen crossed are left out (they are roads, `roads`)."""
        return sorted(xy for xy in self.tiles if self.passable(xy) and not self.outside(xy) and self.unknown_neighbours(xy))

    def roads(self) -> list[tuple[int, int]]:
        """Walkable tiles seen PAST an edge the AI has seen crossed: the next map (walking onto one leaves)."""
        return sorted(xy for xy in self.tiles if self.passable(xy) and self.outside(xy))

    def exits(self) -> list[tuple[int, int]]:
        """Tiles seen inside the map that LOOK like a way out (stairs, doors, mats: the eyes' `warp` and `door`, by the
        behaviour), less those found closed."""
        return sorted(xy for xy, fact in self.tiles.items()
                      if (fact.warp or fact.door) and not self.outside(xy) and xy not in self.closed)

    def grass(self) -> list[tuple[int, int]]:
        return sorted(xy for xy, fact in self.tiles.items() if fact.grass and self.passable(xy))

    # ------------------------------------------------------------------ learning
    def absorb(self, look: Observation, seen_from: tuple[int, int]) -> int:
        """Remember every tile of the look's view; returns how many were NEW."""
        view = look.view
        if view is None:
            return 0
        new = 0
        for row in view.rows:
            for tile in row:
                xy = (tile.x, tile.y)
                fact = TileFact.of(tile, look.frame, seen_from)
                old = self.tiles.get(xy)
                if old is None:
                    self.tiles[xy] = fact
                    new += 1
                elif not old.same_as(fact):
                    self.tiles[xy] = replace(fact, seen_frame=old.seen_frame, seen_from=old.seen_from)
        return new

    def see_objects(self, look: Observation) -> None:
        view = look.view
        if view is None:
            return
        here = []
        for seen in view.objects:
            if seen.source != "object":
                continue
            here.append((seen.x, seen.y))
            if seen.kind == "npc":
                self.people[(seen.x, seen.y)] = look.frame
            elif seen.kind == "item_ball":
                self.items[(seen.x, seen.y)] = look.frame
        self.objects_now = frozenset(here)

    def visit(self, xy: tuple[int, int]) -> None:
        # (build step 3.1) standing on a tile no longer clears its bumps: a one-way tile is reached from its open side,
        # and that says nothing about the side that refused the player
        self.visits[xy] = self.visits.get(xy, 0) + 1

    # ------------------------------------------------------------------ persistence
    def to_dict(self) -> dict:
        return {
            "key": self.key, "name": self.name, "const": self.const, "first_frame": self.first_frame,
            "tiles": {_text(xy): fact.compact() for xy, fact in sorted(self.tiles.items())},
            "tile_fields": ["flags (b blocked, w water, g grass, e encounters, d door, p warp)", "ledge", "elevation",
                            "behavior", "seen_frame", "seen_from_x", "seen_from_y"],
            "visits": {_text(xy): count for xy, count in sorted(self.visits.items())},
            "bumped": {f"{_text(xy)}|{direction}": info for (xy, direction), info in sorted(self.bumped.items())},
            "closed": {_text(xy): info for xy, info in sorted(self.closed.items())},
            "people": {_text(xy): frame for xy, frame in sorted(self.people.items())},
            "items": {_text(xy): frame for xy, frame in sorted(self.items.items())},
            "edges": dict(self.edges), "arrivals": list(self.arrivals),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MapMemory":
        memory = cls(str(data["key"]), str(data.get("name") or ""), data.get("const"))
        memory.first_frame = data.get("first_frame")
        memory.tiles = {_xy(k): TileFact.from_compact(v) for k, v in (data.get("tiles") or {}).items()}
        memory.visits = {_xy(k): int(v) for k, v in (data.get("visits") or {}).items()}
        memory.bumped = {_bump_key(k, v): dict(v) for k, v in (data.get("bumped") or {}).items()}
        memory.closed = {_xy(k): dict(v) for k, v in (data.get("closed") or {}).items()}
        memory.people = {_xy(k): int(v) for k, v in (data.get("people") or {}).items()}
        memory.items = {_xy(k): int(v) for k, v in (data.get("items") or {}).items()}
        memory.edges = {str(k): int(v) for k, v in (data.get("edges") or {}).items()}
        memory.arrivals = [list(a) for a in data.get("arrivals") or []]
        return memory


@dataclass(frozen=True)
class Transition:
    """One map change the AI saw: from where, to where, how (a warp or a connection), and who caused it."""

    frame: int
    source: str  # map key
    target: str
    how: str  # "warp" or "connection"
    by: str  # "ai" (its own step or warp) or "scene" (a script moved the player)
    tile: tuple[int, int] | None  # the warp tile used, or the last tile stood on before a connection
    arrival: tuple[int, int]
    direction: str | None

    def describe(self, names: dict[str, str]) -> str:
        what = f"the {self.how} at {self.tile}" if self.how == "warp" else f"the {self.direction} edge from {self.tile}"
        return (f"{names.get(self.source, self.source)} -> {names.get(self.target, self.target)} at {self.arrival}: "
                f"{what} ({'the AI' if self.by == 'ai' else 'a scene'}, f{self.frame})")


@dataclass
class _Last:
    """The last SETTLED look (the player's tile known, the overworld, no fade)."""

    key: str | None = None
    xy: tuple[int, int] | None = None
    facing: str | None = None
    frame: int = 0
    absorbed_frame: int = -10**9
    absorbed_at: tuple | None = None
    between: bool = False  # a look since then was NOT settled (a fade, the map loading, a battle, settling)
    intent: dict = field(default_factory=dict)


class WorldMemory:
    """The whole memory: every map, the warp graph, the connections, every map change; fed one look at a time."""

    def __init__(self) -> None:
        self.maps: dict[str, MapMemory] = {}
        #: The WARP GRAPH: "key|x,y" -> {"to", "arrival": [x, y] or None, "direction", "uses", "by", "first", "last"}.
        self.warps: dict[str, dict] = {}
        self.connections: list[dict] = []
        self.transitions: list[Transition] = []
        self.tiles_learned = 0  # every tile ever learned, all maps (the navigator's NOVELTY counter)
        self.looks = 0
        #: (the step-3.1 verifier's round) how many of the eyes' story flags were set on the last look that read them
        #: (None until one did): a closed door is retried once this has grown since it was found closed
        self.story: int | None = None
        #: closed doors reopened and not yet told: (frame, map key, tile, why) (`take_reopened`)
        self.reopened: list[tuple[int, str, tuple[int, int], str]] = []
        self._last = _Last()

    # ------------------------------------------------------------------ what the navigator tells it
    def intend(self, kind: str, direction: str | None = None, tile: tuple[int, int] | None = None) -> None:
        """What the AI is about to do: "step" (one tile in `direction`) or "warp" (use the exit `tile` going
        `direction`). A map change that follows is the AI's own; without an intent it was a scene's."""
        self._last.intent = {"kind": kind, "direction": direction, "tile": tile}

    def settle_intent(self) -> None:
        self._last.intent = {}

    # ------------------------------------------------------------------ reading
    @property
    def current(self) -> str | None:
        return self._last.key

    @property
    def position(self) -> tuple[int, int] | None:
        return self._last.xy

    def here(self) -> MapMemory | None:
        return None if self._last.key is None else self.maps.get(self._last.key)

    def names(self) -> dict[str, str]:
        return {key: (memory.const or memory.name or key) for key, memory in self.maps.items()}

    def visited(self, key: str) -> bool:
        memory = self.maps.get(key)
        return memory is not None and bool(memory.visits)

    def link_of(self, key: str, xy: tuple[int, int]) -> dict | None:
        return self.warps.get(f"{key}|{_text(xy)}")

    def links_from(self, key: str) -> list[tuple[str, dict]]:
        """Every known way out of map `key`: ("warp", link with its "tile") and ("connection", link). A connection is
        a shared edge, so one crossed from A to B is also known from B back to A (the opposite direction)."""
        out: list[tuple[str, dict]] = []
        for name, link in self.warps.items():
            source, where = name.split("|")
            if source == key:
                out.append(("warp", {**link, "tile": list(_xy(where))}))
        for connection in self.connections:
            if connection["source"] == key:
                out.append(("connection", connection))
            elif connection["target"] == key and connection.get("direction") in OPPOSITE:
                out.append(("connection", {**connection, "source": key, "target": connection["source"],
                                           "direction": OPPOSITE[connection["direction"]], "inferred": True}))
        return out

    def promise(self, key: str) -> int:
        """How much is left to see on map `key`, as far as the AI knows: its frontier tiles, its exits never used, and its
        roads on a side whose connection it does not know. 0 for a map it has seen all of (or never visited)."""
        memory = self.maps.get(key)
        if memory is None or not memory.visits:
            return 0
        sides = {link["direction"] for kind, link in self.links_from(key) if kind == "connection"}
        unused = [xy for xy in memory.exits() if self.link_of(key, xy) is None]
        roads = [xy for xy in memory.roads() if road_side(memory, xy) not in sides]
        return len(memory.frontier()) + len(unused) + len(roads)

    # ------------------------------------------------------------------ the one entry: a look
    def observe(self, look: Observation) -> None:
        """Learn from one look (called on EVERY look the hands take)."""
        self.looks += 1
        progress = look.progress
        if progress is not None:
            self.story = sum(1 for _, on in progress.flags if on)
        self._reopen(look.frame)
        player = look.player
        last = self._last
        screen = look.screen
        settled = (player is not None and not player.settling and player.x is not None
                   and screen.game_state == "OVERWORLD" and not screen.fading and look.view is not None)
        if not settled:
            # A fade, the map loading, a position settling: what a WARP looks like. A battle is not one (it ends on the
            # map it began on; its own fade-in back on the map is a fade, which changes nothing: same map).
            if not (screen.in_battle or screen.game_state.startswith("BATTLE")):
                last.between = True
            return
        key = map_key(player.map_group, player.map_number)
        memory = self.maps.get(key)
        if memory is None:
            memory = self.maps[key] = MapMemory(key, player.map_name, player.map_const)
            memory.first_frame = look.frame
        xy = (player.x, player.y)
        if last.key is not None and key != last.key:
            self._transition(look, key, xy, memory)
        if (key, xy) != last.absorbed_at or look.frame - last.absorbed_frame >= ABSORB_EVERY:
            self.tiles_learned += memory.absorb(look, xy)
            last.absorbed_at, last.absorbed_frame = (key, xy), look.frame
        memory.see_objects(look)
        if key != last.key or xy != last.xy:
            memory.visit(xy)
        last.key, last.xy, last.facing, last.frame, last.between = key, xy, player.facing, look.frame, False

    def _transition(self, look: Observation, key: str, xy: tuple[int, int], memory: MapMemory) -> None:
        last = self._last
        source = self.maps[last.key]
        intent = last.intent
        by = "ai" if intent else "scene"
        if last.between:
            # A WARP: a fade or the map loading came between the two settled looks.
            tile = None
            stood = source.fact(last.xy) if last.xy is not None else None
            if intent.get("kind") == "warp" and intent.get("tile") is not None:
                tile = tuple(intent["tile"])
            elif stood is not None and (stood.warp or stood.door):
                tile = last.xy
            elif last.xy is not None and last.facing in DIRECTIONS:
                front = moved(last.xy, last.facing)
                fact = source.fact(front)
                if fact is not None and (fact.warp or fact.door):
                    tile = front
            if tile is None:
                tile = last.xy
            direction = intent.get("direction") or last.facing
            name = f"{last.key}|{_text(tile)}"
            link = self.warps.get(name) or {"uses": 0, "first": look.frame}
            link.update({"to": key, "arrival": list(xy), "direction": direction, "by": by, "last": look.frame,
                         "inferred": False})
            link["uses"] = int(link.get("uses", 0)) + 1
            self.warps[name] = link
            change = Transition(look.frame, last.key, key, "warp", by, tile, xy, direction)
            memory.arrivals.append([look.frame, xy[0], xy[1], f"warp from {source.const or last.key} {tile}"])
            self._infer_way_back(look, key, xy, memory, last.key, tile)
        else:
            # A CONNECTION: seamless, the next settled look is already on the new map. The step that crossed it.
            direction = intent.get("direction") or last.facing
            frm = last.xy
            offset = None
            if frm is not None and direction in DIRECTIONS:
                crossed = moved(frm, direction)
                offset = [xy[0] - crossed[0], xy[1] - crossed[1]]
                learn_edges(source, memory, direction, frm, xy)
            self.connections.append({"source": last.key, "target": key, "direction": direction, "from": list(frm) if frm else None,
                                     "arrival": list(xy), "offset": offset, "by": by, "frame": look.frame})
            change = Transition(look.frame, last.key, key, "connection", by, frm, xy, direction)
            memory.arrivals.append([look.frame, xy[0], xy[1], f"walked in from {source.const or last.key} going {direction}"])
        self.transitions.append(change)
        self.settle_intent()

    def _infer_way_back(self, look: Observation, key: str, xy: tuple[int, int], memory: MapMemory, source: str,
                        tile: tuple[int, int]) -> None:
        """The warp tile at the arrival, or next to it (a door's mat is one step behind the player who walked out of
        it), leads back where the player came from, as far as a person can tell. Kept until the AI uses it."""
        self.tiles_learned += memory.absorb(look, xy)
        candidates = [xy] + [moved(xy, d) for d in ("up", "down", "left", "right")]
        for xy_back in candidates:
            fact = memory.fact(xy_back)
            if fact is not None and (fact.warp or fact.door):
                name = f"{key}|{_text(xy_back)}"
                if name not in self.warps:
                    self.warps[name] = {"to": source, "arrival": list(tile) if tile else None, "direction": None,
                                        "uses": 0, "by": "inferred", "first": look.frame, "last": look.frame,
                                        "inferred": True}
                return

    def learn_bump(self, frm: tuple[int, int], direction: str, frame: int) -> tuple[int, int] | None:
        """Moving `direction` from `frm` on the current map did not move the player, and no person was in the way: the
        tile does not let the player in THAT WAY (a hidden wall, or a one-way tile's closed side). Returns the tile."""
        memory = self.here()
        if memory is None:
            return None
        tile = moved(frm, direction)
        key = (tile, direction)
        info = memory.bumped.get(key) or {"from": list(frm), "direction": direction, "first": frame, "bumps": 0}
        info["bumps"] = int(info.get("bumps", 0)) + 1
        info["last"] = frame
        memory.bumped[key] = info
        return tile

    def close_exit(self, xy: tuple[int, int], how: str, frame: int) -> None:
        """An exit-looking tile of the current map that took the player nowhere when used properly (`how`: the press and
        how long): remembered as CLOSED (build step 3.1, finding 5: what a look cannot say is learned by using the
        exit), with how far the story was then (`story`), until `_reopen` (the step-3.1 verifier's round)."""
        memory = self.here()
        if memory is not None:
            memory.closed[xy] = {"frame": frame, "how": how, "story": self.story}

    def _reopen(self, frame: int) -> None:
        """(The step-3.1 verifier's round: a closed door was closed for good) Every door found closed is worth a try
        again once the story has moved on since (more of the eyes' story flags set than when it was found closed), or
        `CLOSED_RETRY_FRAMES` after it was found closed. What is reopened is kept in `reopened` for the navigator."""
        for key, memory in self.maps.items():
            for xy, info in list(memory.closed.items()):
                then = info.get("story")
                if then is not None and self.story is not None and self.story > then:
                    why = f"the story moved on since it was found closed ({then} -> {self.story} story flags set)"
                elif frame - int(info.get("frame", frame)) >= CLOSED_RETRY_FRAMES:
                    why = f"{frame - int(info['frame'])} frames since it was found closed (f{info['frame']})"
                else:
                    continue
                del memory.closed[xy]
                self.reopened.append((frame, key, xy, why))

    def take_reopened(self) -> list[tuple[int, str, tuple[int, int], str]]:
        """The closed doors reopened since the last call (the navigator tells them)."""
        out, self.reopened = self.reopened, []
        return out

    # ------------------------------------------------------------------ persistence
    def to_dict(self) -> dict:
        return {
            "maps": {key: memory.to_dict() for key, memory in sorted(self.maps.items())},
            "warps": dict(sorted(self.warps.items())),
            "connections": list(self.connections),
            "transitions": [[t.frame, t.source, t.target, t.how, t.by, list(t.tile) if t.tile else None, list(t.arrival),
                             t.direction] for t in self.transitions],
            "tiles_learned": self.tiles_learned,
        }

    def snapshot(self) -> str:
        """The memory as ONE line of JSON (the brain appends it to `<run_dir>/world.jsonl`)."""
        return json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "WorldMemory":
        world = cls()
        world.maps = {key: MapMemory.from_dict(value) for key, value in (data.get("maps") or {}).items()}
        world.warps = {key: dict(value) for key, value in (data.get("warps") or {}).items()}
        world.connections = [dict(c) for c in data.get("connections") or []]
        world.transitions = [Transition(int(t[0]), str(t[1]), str(t[2]), str(t[3]), str(t[4]), tuple(t[5]) if t[5] else None,
                                        (int(t[6][0]), int(t[6][1])), t[7]) for t in data.get("transitions") or []]
        world.tiles_learned = int(data.get("tiles_learned") or 0)
        # every crossing recorded teaches both maps' edges again: a memory written before build step 3.1 kept only the
        # right and bottom edges (the top and left came from the coordinates, which a person cannot see)
        for connection in world.connections:
            source, target = world.maps.get(connection.get("source")), world.maps.get(connection.get("target"))
            frm, arrival, direction = connection.get("from"), connection.get("arrival"), connection.get("direction")
            if source is not None and target is not None and frm and arrival and direction in DIRECTIONS:
                learn_edges(source, target, direction, (int(frm[0]), int(frm[1])), (int(arrival[0]), int(arrival[1])))
        return world


def learn_edges(source: MapMemory, target: MapMemory, direction: str, frm: tuple[int, int], arrival: tuple[int, int]) -> None:
    """A crossing SEEN: moving `direction` from `frm` on `source` landed on `arrival` on `target`. The tile crossed into
    is the first one outside `source` on that side; the tile behind the arrival, going back, the first one outside
    `target` on the opposite side (build step 3.1: all four sides, and only from a crossing)."""
    axis, _ = AXIS[direction]
    source.edges[direction] = moved(frm, direction)[axis]
    back = OPPOSITE[direction]
    target.edges[back] = moved(arrival, back)[AXIS[back][0]]


def read_world(path) -> WorldMemory | None:
    """The memory a run left: the LAST line of its `world.jsonl` (read only). None if the file holds no snapshot."""
    last = None
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    return None if last is None else WorldMemory.from_dict(json.loads(last))
