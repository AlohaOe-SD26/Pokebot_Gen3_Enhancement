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
  * PEOPLE AND THINGS: where people (transient: they walk) and item balls were seen. (Step 4.1 round 2, finding 7)
    WHO each person is (`persons`: the figure the eyes follow on screen, by its object's local id, and where it stood
    last), which people are standing on the screen NOW (`people_now`), and which the player has MET: stood within
    `MEET_RADIUS` tiles of them (`met`), as a person who walks up to someone has seen them close.
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
    worth a try again once there is NEWS since it was found closed, or after `CLOSED_RETRY_FRAMES` (a person tries a
    locked door again later). The memory reopens it (`WorldMemory.observe`) and keeps what it reopened for the navigator
    to tell (`take_reopened`). NEWS (build step 3.2, the step-3.1 review's LOW finding 5: "doors reopen on hidden
    story-flag counts"): what a PERSON could see change, never a count of the save's flags: words never read before on
    the overworld (`heard`: a person who is told something new may find a door open), a map never stood on before, a
    Pokemon of the player's never seen before (by PID). `news`, the count, and `heard` persist with the memory.
  * BUMPS ARE FORGOTTEN (build step 3.2, the step-3.1 review's MEDIUM finding 3: "a bump is never forgotten after
    walking through that way"): a step that gets the player into a tile going `d` deletes that tile's bump for `d`
    (`forget_bump`, called by the navigator, which saw the step); a tile whose LOOK changes (its facts: `absorb`) drops
    every bump learned there (what was learned was about the old tile), kept for the navigator to tell
    (`take_dropped_bumps`).
  * A DOORMAT IS ONE WAY OUT (the step-4 verifier's round): the tiles of an arrow mat side by side across its arrow, with
    the same look (`mat_tiles`), lead where the tile used or arrived on leads (measured 2026-10-09: the explorer left May's
    house by the mat's other tile, taken for an exit not used yet, before going upstairs to May).
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
from ai_player.eyes.screens import page_text
from ai_player.eyes.view import VIEW_DOWN, VIEW_HALF_WIDTH, VIEW_UP

__all__ = [
    "ABSORB_EVERY",
    "AXIS",
    "CLOSED_RETRY_FRAMES",
    "DIRECTIONS",
    "LEDGE_DIRECTIONS",
    "MAT_ACROSS",
    "MAT_WIDTH",
    "OPPOSITE",
    "MapMemory",
    "TileFact",
    "Transition",
    "WorldMemory",
    "BUMP_GIVE_UP",
    "MEET_RADIUS",
    "in_window",
    "learn_edges",
    "map_key",
    "mat_tiles",
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
#: (step 4.1 round 2, the step-4 review's finding 7) A person is MET once the player has stood within this many tiles
#: (Manhattan) of where they stood: close enough to have seen them (a trainer among them would have seen the player).
#: MEASURED 2026-10-09 (development sweep, TOWN-Trainer, seeds 1-10 and 101-110, in-process, the clock pinned): with 2, a
#: person who stepped aside as the player came up was walked after again (journeys 0.32 of their steps beyond the shortest
#: known way); with 3, 0.28.
MEET_RADIUS = 3


#: (the step-4 verifier's round) An arrow mat's look -> the axis it lies ACROSS (a south mat is a row of tiles side by side)
MAT_ACROSS: dict[str, tuple[str, str]] = {"SOUTH_ARROW_WARP": ("left", "right"), "NORTH_ARROW_WARP": ("left", "right"),
                                          "EAST_ARROW_WARP": ("up", "down"), "WEST_ARROW_WARP": ("up", "down")}
#: The widest doormat a person takes for one way out (the game's are two tiles wide)
MAT_WIDTH = 3


def mat_tiles(memory: "MapMemory", xy: tuple[int, int]) -> list[tuple[int, int]]:
    """(the step-4 verifier's round) The other tiles of the DOORMAT `xy` is part of, as a person sees it: tiles beside it
    across its arrow (`MAT_ACROSS`), seen, with the same look, at most `MAT_WIDTH` in all. [] for anything that is not an
    arrow mat (two doors side by side are two doors)."""
    fact = memory.fact(xy)
    sides = MAT_ACROSS.get(fact.behavior) if fact is not None else None
    if not sides:
        return []
    out: list[tuple[int, int]] = []
    for side in sides:
        here = xy
        while len(out) < MAT_WIDTH - 1:
            here = moved(here, side)
            other = memory.fact(here)
            if other is None or other.behavior != fact.behavior:
                break
            out.append(here)
    return out


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
        #: (step 4.1 round 2, finding 7) WHO: a person on screen (the figure the eyes follow: its object's local id on this
        #: map) -> (x, y, the last frame seen there); and the people the player has MET (`MEET_RADIUS`): id -> the frame
        self.persons: dict[int, tuple[int, int, int]] = {}
        self.met: dict[int, int] = {}
        self.items: dict[tuple[int, int], int] = {}  # item balls: tile -> the last frame seen
        self.objects_now: frozenset[tuple[int, int]] = frozenset()  # every object on the LAST look (people, balls, ...)
        #: (step 4.1 round 2) the PEOPLE among them: tiles a person stood on in the last look (they walk on)
        self.people_now: frozenset[tuple[int, int]] = frozenset()
        #: per side ("up", "down", "left", "right"): the first coordinate OUTSIDE the map, learned at a crossing SEEN
        self.edges: dict[str, int] = {}
        self.first_frame: int | None = None
        self.arrivals: list[list] = []  # [frame, x, y, how]
        #: (build step 3.2) bumps dropped because their tile's look changed, not yet told: (frame, tile, directions)
        self.dropped: list[tuple[int, tuple[int, int], list[str]]] = []

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
        """Remember every tile of the look's view; returns how many were NEW. (Chapter 6 stops round 7, N6-1) A tile in the
        dark (None: outside the lit circle of a dark map) is not seen, so not learned; what was learned before stays."""
        view = look.view
        if view is None:
            return 0
        new = 0
        for row in view.rows:
            for tile in row:
                if tile is None:
                    continue
                xy = (tile.x, tile.y)
                fact = TileFact.of(tile, look.frame, seen_from)
                old = self.tiles.get(xy)
                if old is None:
                    self.tiles[xy] = fact
                    new += 1
                elif not old.same_as(fact):
                    self.tiles[xy] = replace(fact, seen_frame=old.seen_frame, seen_from=old.seen_from)
                    # (build step 3.2) the tile looks different now (a script opened a door, moved a rock): what bumping
                    # it taught was about the old tile
                    sides = [direction for (where, direction) in self.bumped if where == xy]
                    for direction in sides:
                        del self.bumped[(xy, direction)]
                    if sides:
                        self.dropped.append((look.frame, xy, sorted(sides)))
        return new

    def see_objects(self, look: Observation) -> None:
        view = look.view
        if view is None:
            return
        here, people = [], []
        player = look.player
        at = (player.x, player.y) if player is not None and player.x is not None else None
        for seen in view.objects:
            if seen.source != "object":
                continue
            here.append((seen.x, seen.y))
            if seen.kind == "npc":
                self.people[(seen.x, seen.y)] = look.frame
                people.append((seen.x, seen.y))
                # (step 4.1 round 2, finding 7) who it is, where they stand now, and whether the player is beside them
                self.persons[seen.local_id] = (seen.x, seen.y, look.frame)
                if at is not None and abs(at[0] - seen.x) + abs(at[1] - seen.y) <= MEET_RADIUS:
                    self.met.setdefault(seen.local_id, look.frame)
            elif seen.kind == "item_ball":
                self.items[(seen.x, seen.y)] = look.frame
        self.objects_now = frozenset(here)
        self.people_now = frozenset(people)

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
            "persons": {str(who): list(where) for who, where in sorted(self.persons.items())},
            "met": {str(who): frame for who, frame in sorted(self.met.items())},
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
        memory.persons = {int(k): (int(v[0]), int(v[1]), int(v[2])) for k, v in (data.get("persons") or {}).items()}
        memory.met = {int(k): int(v) for k, v in (data.get("met") or {}).items()}
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
        #: (build step 3.2, the step-3.1 review's finding 5: the closed doors reopened on a hidden count of story flags)
        #: NEWS a person could see, counted: words never read before on the overworld, a map never stood on before, a
        #: Pokemon never seen before; a closed door is retried once this has grown since it was found closed. `heard`: the
        #: words read so far (persisted with `news`); `pids`: the Pokemon seen so far (the first look's are not news);
        #: `news_log`: the newest news, what and when (for the navigator's line)
        self.news = 0
        self.heard: set[str] = set()
        self.pids: set[int] | None = None
        self.news_log: list[tuple[int, str]] = []
        #: (build step 5.2, found by the pushing property in the round's development sweeps: step52dev4 and dev6, ROUTE 103
        #: and OLDALE crossed 186-198 times in one walk) map key -> frontier tile -> how many tiles the map had when a walk
        #: found NO way to it over the tiles it knows (`mark_unreached`): left out of the map's `promise` until the map shows
        #: something new
        self.unreached: dict[str, dict[tuple[int, int], int]] = {}
        #: (build step 5.2, the verifier's round: the graded NOHINTS runs went OLDALE -> OLDALE_TOWN_HOUSE1 -> OLDALE for up
        #: to 98 goals in a row, each ended by the ping-pong rule, because the house's two frontier tiles, which no walk from
        #: its door can get to, were "2 things left to see" for ever) map key -> (how many tiles the map had, the frontier
        #: tiles and unused exits the navigator's own reach, from where the player stood, showed NO way to:
        #: `Navigator.cut_off`): left out of the map's `promise` until the map shows something new. Recomputed (replaced)
        #: at every decision on the map, so a way that opens (a scene's walls lifted) counts again at the next one.
        self.cut_off: dict[str, tuple[int, frozenset]] = {}
        #: (build step 5.2, the verifier's round; its development sweep step52vdev3, NOHINTS seed 1223: a walk with no lead
        #: went OLDALE -> ROUTE 103 -> OLDALE across the edge, each map "where something is left" seen from the other, and on
        #: each nothing worth going to, for 3,395 frames) map key -> how many tiles the map had when a walk with no lead stood
        #: on it and found NOTHING there worth going to (`mark_spent`): its `promise` is 0 until the map shows something new
        self.spent: dict[str, int] = {}
        #: (build step 5.2, the verifier's round: 60 POKéMON CENTER nurses and 46 MART clerks "chatted" with right after
        #: the heal or the shop that had just talked to them, and 21 chats with OLDALE's footprints man right after his own
        #: scene had stopped a look round, every one hearing nothing new) "map key|local id" of the people who have SPOKEN
        #: to the player: someone standing straight in front of it, at most two tiles away (a counter between), while words
        #: were on the overworld screen (`brain/goals.py` GoalManager.notice). A person does not walk up to say hello to
        #: someone who has just spoken to them. Kept with the memory (a later session remembers whom it met); written only
        #: when it holds something, so the earlier brains' snapshots are unchanged.
        self.spoke: set[str] = set()
        #: closed doors reopened and not yet told: (frame, map key, tile, why) (`take_reopened`)
        self.reopened: list[tuple[int, str, tuple[int, int], str]] = []
        #: BUILD STEP 5: (map key, (x, y)) -> "pokemon_center" / "mart": a door the play brain RECOGNISED by its look
        #: (`brain/goals.py` GoalManager.notice), kept with the memory so a later run remembers where the centre was (the
        #: chapter-2 development run of 2026-10-14 started from chapter 1's memory, had walked past OLDALE's centre, and
        #: went home to MOM to heal). Written only when it holds something, so the earlier brains' snapshots are unchanged.
        self.landmarks: dict[tuple[str, tuple[int, int]], str] = {}
        #: (chapter 6 NS2, 2026-11-06) RIDES: "from map key|person id|to map key" -> what the AI saw when answering YES to a
        #: person's offer of a trip carried it, by scenes only, to another map (`brain/rides.py` RideWatch): "from", "to",
        #: "arrival" (where the controls came back), "who" (the person's local id), "gfx", "tile" (where they stood),
        #: "words" (the question answered), "place" (the town it offered), "via" (the maps the scene passed), "first",
        #: "last", "uses", and "closed" ({"news", "frame", "why"}) while one failed and nothing new has been seen since
        #: (`close_ride`). A way a person knows: walk up to them, talk, say YES (`rides_from`). Written only when it holds
        #: something, so the earlier brains' snapshots are unchanged.
        self.rides: dict[str, dict] = {}
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

    def record_ride(self, ride: dict) -> dict:
        """(chapter 6 NS2) A RIDE seen (`brain/rides.py` RideWatch): kept by (from, who, to), its uses counted; seen again,
        it is open again (`close_ride` undone) and its words, the person's tile and the arrival are the newest."""
        name = f"{ride['from']}|{ride['who']}|{ride['to']}"
        kept = self.rides.get(name) or {"uses": 0, "first": ride.get("frame")}
        kept.update({key: value for key, value in ride.items() if key != "frame"})
        kept["uses"] = int(kept.get("uses", 0)) + 1
        kept["last"] = ride.get("frame")
        kept.pop("closed", None)
        self.rides[name] = kept
        return kept

    def rides_from(self, key: str) -> list[tuple[str, dict]]:
        """(chapter 6 NS2) The rides from map `key` a person would try now: [(its name, the ride)], every one not put aside
        (`close_ride`: a failed one waits for news, or `CLOSED_RETRY_FRAMES` frames, as a closed door does)."""
        out = []
        for name, ride in sorted(self.rides.items()):
            if ride.get("from") != key:
                continue
            closed = ride.get("closed")
            if closed is not None and self.news <= int(closed.get("news", 0)) and \
                    self._last.frame - int(closed.get("frame", 0)) < CLOSED_RETRY_FRAMES:
                continue
            out.append((name, ride))
        return out

    def close_ride(self, name: str, why: str, frame: int) -> None:
        """(chapter 6 NS2) The ride `name` was tried and did not carry the player (the person was not there, asked
        something else, or the scene ended elsewhere): put aside until there is news (`rides_from`)."""
        ride = self.rides.get(name)
        if ride is not None:
            ride["closed"] = {"news": self.news, "frame": frame, "why": why}

    def promise(self, key: str) -> int:
        """How much is left to see on map `key`, as far as the AI knows: its frontier tiles, its exits never used, and its
        roads on a side whose connection it does not know. 0 for a map it has seen all of (or never visited). (Build step
        5.2) A frontier tile a walk found no way to is left out while the map has shown nothing new since (`unreached`):
        a person who could not get there does not go back for it (the explorer on OLDALE chose "back to ROUTE 103, where 1
        thing is left to see", ROUTE 103's one frontier it could not reach, and on ROUTE 103 "back to OLDALE", for 10,683
        frames of pressing with nothing new). (The verifier's round) neither is a frontier tile or an unused exit that the
        navigator's reach, at its last decision on the map, showed no way to (`cut_off`, `Navigator.cut_off`)."""
        memory = self.maps.get(key)
        if memory is None or not memory.visits:
            return 0
        if self.spent.get(key) == len(memory.tiles):
            return 0  # (the verifier's round) a walk with no lead stood here and found nothing worth going to
        sides = {link["direction"] for kind, link in self.links_from(key) if kind == "connection"}
        unused = [xy for xy in memory.exits() if self.link_of(key, xy) is None]
        roads = [xy for xy in memory.roads() if road_side(memory, xy) not in sides]
        gone = self.unreached.get(key, {})
        frontier = [xy for xy in memory.frontier() if gone.get(xy) != len(memory.tiles)]
        # (build step 5.2, the verifier's round) nor what the navigator's reach showed no way to, while the map is unchanged
        count, cut = self.cut_off.get(key, (None, frozenset()))
        if count == len(memory.tiles):
            unused = [xy for xy in unused if xy not in cut]
            frontier = [xy for xy in frontier if xy not in cut]
        return len(frontier) + len(unused) + len(roads)

    def mark_unreached(self, key: str, tile: tuple[int, int]) -> None:
        """(build step 5.2) A walk found no way to the frontier `tile` of map `key` over the tiles it knows (`promise`)."""
        memory = self.maps.get(key)
        if memory is not None:
            self.unreached.setdefault(key, {})[tuple(tile)] = len(memory.tiles)

    def mark_cut_off(self, key: str, tiles) -> None:
        """(build step 5.2, the verifier's round) The frontier tiles and unused exits of map `key` that the navigator's reach
        from where the player stands shows NO way to (`Navigator.cut_off`), replacing what was marked there before: left out
        of `promise` while the map shows nothing new."""
        memory = self.maps.get(key)
        if memory is not None:
            self.cut_off[key] = (len(memory.tiles), frozenset(tuple(tile) for tile in tiles))

    def forget_marks(self) -> int:
        """(build step 5.2, the verifier's round; found by its first development sweep, step52vdev1: chapter-1 seed 1201 gave
        up "out of ideas" in the rival's bedroom at the start of PROF. BIRCH's milestone, because LITTLEROOT's road north,
        cut off by the twin's scene in the milestone before, was still marked) The STORY moved on (a milestone passed): what
        a walk found no way to (`unreached`) and what the reach showed no way to (`cut_off`) are forgotten: a person tries a
        way again once the story has moved (the twin steps aside). Returns how many marks were dropped."""
        dropped = (sum(len(marks) for marks in self.unreached.values()) + sum(len(cut) for _, cut in self.cut_off.values())
                   + len(self.spent))
        self.unreached, self.cut_off, self.spent = {}, {}, {}
        return dropped

    def mark_spent(self, key: str) -> None:
        """(build step 5.2, the verifier's round) A walk with no lead stood on map `key` and found nothing there worth going
        to: what `promise` counted there cannot be had as things are (`spent`), until the map shows something new."""
        memory = self.maps.get(key)
        if memory is not None:
            self.spent[key] = len(memory.tiles)

    def stamp(self) -> tuple[int, int, int]:
        """(build step 5.2, the verifier's round) What the memory has seen so far, counted: tiles learned, maps stood on,
        news (words never read, a Pokemon never seen). The same stamp: nothing new seen anywhere since."""
        return self.tiles_learned, sum(1 for memory in self.maps.values() if memory.visits), self.news

    def left_anywhere(self) -> list[tuple[str, int]]:
        """(build step 5.2, the verifier's round) Every map it has stood on with something still left to see there that it
        could get to as far as it knows (`promise` > 0): [(map key, how much)], nearest first is the caller's business."""
        return [(key, left) for key in sorted(self.maps) if (left := self.promise(key)) > 0]

    # ------------------------------------------------------------------ the one entry: a look
    def observe(self, look: Observation) -> None:
        """Learn from one look (called on EVERY look the hands take)."""
        self.looks += 1
        self._news(look)
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
            if self.maps:
                self._tell_news(look.frame, f"a new place: {player.map_const or player.map_name or key}")
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
            # (the step-4 verifier's round) the rest of the DOORMAT used leads where it led (`mat_tiles`)
            for xy_mat in mat_tiles(source, tile):
                other = f"{last.key}|{_text(xy_mat)}"
                if other not in self.warps:
                    self.warps[other] = {"to": key, "arrival": list(xy), "direction": direction, "uses": 0, "by": "inferred",
                                         "first": look.frame, "last": look.frame, "inferred": True}
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
                # (the step-4 verifier's round) a DOORMAT is one way out however wide it is: the tiles beside the one the
                # player stands on, across the mat's arrow, with the same look, lead back too (measured 2026-10-09: the
                # sweep's SCENE-EXPLORE seeds 6 and 10 left May's house by the doormat's other tile, (1, 8), taken for "an
                # exit not used yet", before going upstairs to May, and never met her)
                for xy_mat in [xy_back] + mat_tiles(memory, xy_back):
                    name = f"{key}|{_text(xy_mat)}"
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

    def forget_bump(self, key: str | None, xy: tuple[int, int], direction: str) -> dict | None:
        """(build step 3.2, the step-3.1 review's finding 3) A step got the player into `xy` going `direction` on map
        `key`: a bump learned there that way is wrong now (a person who walked through stops thinking it is a wall), and
        is forgotten. Returns what was forgotten, or None.
        (chapter 6 NS6, 2026-11-06) NOT a way learned by SLIDING BACK (`learn_slide`): getting into such a tile is exactly
        what happens before the slide, so getting in proves nothing; it is forgotten only when the tile HOLDS the player
        (`forget_slide`)."""
        memory = self.maps.get(key) if key is not None else None
        if memory is None:
            return None
        if (memory.bumped.get((xy, direction)) or {}).get("slid"):
            return None
        return memory.bumped.pop((xy, direction), None)

    def learn_slide(self, key: str | None, xy: tuple[int, int], direction: str, frame: int) -> dict | None:
        """(chapter 6 NS6, 2026-11-06) A STEP UNDONE: the player stepped into `xy` going `direction` on map `key`, and was
        carried straight back to where the step began without pressing back (a MUDDY SLOPE, pinned decomp
        `src/field_player_avatar.c` ForcedMovement_MuddySlope: on foot the player slides south). What a person sees: they
        walk up, and slide down again. It counts as a failed step that way, exactly like a bump (`bumps`: dear after one,
        refused at `BUMP_GIVE_UP`), marked `slid` so the step that gets in before each slide does not forget it
        (`forget_bump`). Kept with the memory like every bump, so a later session knows it too. Returns what is kept."""
        memory = self.maps.get(key) if key is not None else None
        if memory is None:
            return None
        info = memory.bumped.get((xy, direction)) or {"from": list(moved(xy, OPPOSITE[direction])), "direction": direction,
                                                      "first": frame, "bumps": 0}
        info["bumps"] = int(info.get("bumps", 0)) + 1
        info["last"] = frame
        info["slid"] = True
        memory.bumped[(xy, direction)] = info
        return info

    def forget_slide(self, key: str | None, xy: tuple[int, int], direction: str) -> dict | None:
        """(chapter 6 NS6) The tile `xy`, entered going `direction`, HELD the player: it walked on from there by itself. A
        slide learned there that way is wrong now, and is forgotten. Returns what was forgotten, or None."""
        memory = self.maps.get(key) if key is not None else None
        if memory is None or not (memory.bumped.get((xy, direction)) or {}).get("slid"):
            return None
        return memory.bumped.pop((xy, direction), None)

    def take_dropped_bumps(self) -> list[tuple[int, str, tuple[int, int], list[str]]]:
        """(build step 3.2) The bumps dropped because their tile's look changed, since the last call: (frame, map key,
        tile, directions) (the navigator tells them)."""
        out = []
        for key, memory in self.maps.items():
            out += [(frame, key, xy, sides) for frame, xy, sides in memory.dropped]
            memory.dropped = []
        return out

    def _tell_news(self, frame: int, what: str) -> None:
        self.news += 1
        self.news_log = (self.news_log + [(frame, what)])[-8:]

    def _news(self, look: Observation) -> None:
        """(build step 3.2, the step-3.1 review's finding 5) NEWS a person could see on this look (the class docstring):
        a page of words never read before, on the overworld (a battle's lines are not news: they name every wild Pokemon
        met), or a Pokemon of the player's never seen before (by PID; the first look that reads them is the baseline).
        A new map is told where it is first stood on (`observe`)."""
        screen = look.screen
        if screen.waits_for_button and screen.text and not screen.in_battle and screen.game_state == "OVERWORLD":
            words = " ".join((page_text(screen.text) or "").split())
            if words and words not in self.heard:
                self.heard.add(words)
                self._tell_news(look.frame, f"words never read before: {words[:40]!r}")
        if look.party is not None and look.storage is not None:
            pids = {mon.pid for mon in look.party} | {mon.pid for mon in look.storage}
            if self.pids is not None and pids - self.pids:
                self._tell_news(look.frame, f"a new Pokemon (PID {', '.join(f'{pid:08x}' for pid in sorted(pids - self.pids))})")
            self.pids = pids if self.pids is None else self.pids | pids

    def close_exit(self, xy: tuple[int, int], how: str, frame: int) -> None:
        """An exit-looking tile of the current map that took the player nowhere when used properly (`how`: the press and
        how long): remembered as CLOSED (build step 3.1, finding 5: what a look cannot say is learned by using the
        exit), with how much NEWS there had been then (`news`, build step 3.2), until `_reopen`."""
        memory = self.here()
        if memory is not None:
            memory.closed[xy] = {"frame": frame, "how": how, "news": self.news}

    def _reopen(self, frame: int) -> None:
        """(The step-3.1 verifier's round: a closed door was closed for good) Every door found closed is worth a try
        again once there is NEWS since (build step 3.2: something a person could see, `_news`; it was a count of the
        save's story flags, which a person cannot), or `CLOSED_RETRY_FRAMES` after it was found closed. What is reopened
        is kept in `reopened` for the navigator."""
        for key, memory in self.maps.items():
            for xy, info in list(memory.closed.items()):
                then = info.get("news")
                if then is not None and self.news > int(then):
                    why = f"news since it was found closed: {self.news_log[-1][1] if self.news_log else self.news}"
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
        out = {
            "maps": {key: memory.to_dict() for key, memory in sorted(self.maps.items())},
            "warps": dict(sorted(self.warps.items())),
            "connections": list(self.connections),
            "transitions": [[t.frame, t.source, t.target, t.how, t.by, list(t.tile) if t.tile else None, list(t.arrival),
                             t.direction] for t in self.transitions],
            "tiles_learned": self.tiles_learned,
            # (build step 3.2) the news a person could see, counted, and the words read so far (`_news`)
            "news": self.news, "heard": sorted(self.heard), "news_log": [list(item) for item in self.news_log],
        }
        if self.landmarks:  # (build step 5) only when the play brain recognised a door: earlier snapshots unchanged
            out["landmarks"] = {f"{key}|{xy[0]},{xy[1]}": kind for (key, xy), kind in sorted(self.landmarks.items())}
        if self.spoke:  # (build step 5.2, the verifier's round) only when someone has spoken to the player: the same
            out["spoke"] = sorted(self.spoke)
        if self.rides:  # (chapter 6 NS2) only when a ride was seen: the same
            out["rides"] = {name: dict(ride) for name, ride in sorted(self.rides.items())}
        return out

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
        # (build step 3.2) the news so far; a door closed in a memory written before (its "story", a count of the save's
        # flags, is not news a person sees) is worth a try again at the next news from here on
        world.news = int(data.get("news") or 0)
        world.heard = {str(words) for words in data.get("heard") or []}
        world.news_log = [(int(item[0]), str(item[1])) for item in data.get("news_log") or []]
        for place, kind in (data.get("landmarks") or {}).items():  # (build step 5) "key|x,y" -> kind
            key, _, xy = str(place).rpartition("|")
            x, _, y = xy.partition(",")
            world.landmarks[(key, (int(x), int(y)))] = str(kind)
        world.spoke = {str(who) for who in data.get("spoke") or []}  # (build step 5.2, the verifier's round)
        # (chapter 6 NS2) the rides seen; a memory written before has none (and loads as before)
        world.rides = {str(name): dict(ride) for name, ride in (data.get("rides") or {}).items() if isinstance(ride, dict)}
        for memory in world.maps.values():
            for info in memory.closed.values():
                info.setdefault("news", world.news)
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
