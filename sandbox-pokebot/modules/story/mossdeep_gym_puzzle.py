"""The Mossdeep Gym rotating-tile statue puzzle — a SIMULATOR, so the bot can plan without pressing.

‼ WHY A SIMULATOR AND NOT A WALKER. The gym's six walkable islands are joined only by warp pads,
and the corridors to three of those pads are sealed by statues. Freeing them takes ~14 switch
presses spread across four islands, and the shortest known route is ~116 steps. A search that has
to press a real button per edge cannot go that deep, and a search whose state is only
`(map, position)` silently merges genuinely different worlds — that is exactly how
`probe_gym_bruteforce.py` found 35 tiles and concluded, wrongly, that the gym has no route to its
own leaders (KI-58).

So we simulate. The ARROWS are map layout: baked into ROM, never moving. Only the objects move.

‼‼ THE MOVEMENT RULE IS A RIGID, SIMULTANEOUS ROTATION — every object on a matching arrow moves,
whether or not its destination looks occupied. A 2x2 pad's four arrows form a closed 4-cycle, so the
objects on it rotate as one and nothing ever actually collides.

‼ A WRONG MODEL WAS BUILT HERE FIRST, AND IT IS WORTH KNOWING WHY. KI-58 recorded the yellow press
at (3,30) as a *set* of before/after positions with no object identities attached. Reading "(1,29)
and (5,29) left; (2,29) and (5,30) are now occupied" invites the inference that only two objects
moved and the rest were blocked — which yields a plausible sliding-block puzzle with an occupancy
check, and a direction mapping to match. Both were wrong. Re-measuring with the identities kept
(`probe_gym_simulate.py`, keyed on `local_id`) shows all six objects moved one step around the
cycle:

    id 2  (1,30) -> (2,30)      id 4  (4,29) -> (4,30)
    id 10 (2,30) -> (2,29)      id 12 (4,30) -> (5,30)
    id 11 (1,29) -> (1,30)      id 13 (5,29) -> (4,29)

Fitting both candidate rules against that identity-keyed data: rigid rotation scores 6/6, the
ordered slide 2/6. ⇒ **A set of positions cannot tell you who moved where.** Any measurement meant to
settle a movement rule has to carry object identity, or it will confirm whichever story you brought.

‼ THE STATE IS THE FULL TUPLE OF POSITIONS, not "5 counters mod 4" as the KI-58 note suggests. The
counter abstraction happens to work for a pad holding three objects, but the yellow pad at
(4,20)-(5,21) holds only TWO, and pads are shared between colours nowhere — so the honest, general
state is simply where every object is. It is hashable and small, and it costs nothing.

‼ TRAINERS SLIDE TOO. Objects with `trainer_type != "None"` stand on arrow pads as well (seven of
them), and the game moves whatever object is on a matching arrow. Filtering to `graphics_id == 224`
statues would mispredict every pad that holds a trainer.

ENCODING, derived from the ROM dump rather than assumed (`tools/story-dev/probe_gym_arrows.py`):
  * arrow metatiles occupy 0x250..0x27F, eight ids per colour band;
  * band = (metatile - 0x250) // 8  ->  0 Yellow, 1 Blue, 2 Green, 3 Purple, 4 Red;
  * code = (metatile - 0x250) %  8  ->  0 Right, 1 Down, 2 Left, 3 Up, and 4/5 = that colour's
    FLOOR SWITCH rather than an arrow.
The direction mapping is the one that scores 6/6 against the identity-keyed live press above. The
dir-4/5 tiles reproduce KI-58's independently-obtained switch list exactly, which is a free
cross-check on the whole decoding.
"""

from typing import NamedTuple

ARROW_BASE = 0x250
ARROW_TOP = 0x27F

#: metatile code -> (dx, dy). Codes 4 and 5 are switches, not arrows, and are absent on purpose.
DIRECTION_DELTAS: dict[int, tuple[int, int]] = {0: (1, 0), 1: (0, 1), 2: (-1, 0), 3: (0, -1)}

#: colour band -> human name. Only used for logging; the solver works in band numbers.
COLOUR_NAMES: dict[int, str] = {0: "Yellow", 1: "Blue", 2: "Green", 3: "Purple", 4: "Red"}

#: codes that mark a colour's floor switch instead of an arrow.
SWITCH_CODES = frozenset({4, 5})

STATUE_GRAPHICS_ID = 224


class GymObject(NamedTuple):
    """One object template, in the order `MoveRotatingTileObjects` iterates them."""

    local_id: int
    graphics_id: int
    start: tuple[int, int]
    is_statue: bool
    is_trainer: bool


class MossdeepGymPuzzle:
    """Static map facts plus the movement rule. Positions live in the state tuple, not in here.

    A STATE is a tuple of `(x, y)` positions, one per object, in template order — the same order the
    game iterates. Keeping it a tuple makes it hashable, so it can key a search directly."""

    def __init__(
        self,
        objects: list[GymObject],
        arrows: dict[tuple[int, int], tuple[int, int]],
        switches: dict[tuple[int, int], int],
        collision: dict[tuple[int, int], int],
    ):
        self.objects = objects
        #: tile -> (colour band, direction code) for the 0..3 codes only
        self.arrows = arrows
        #: tile -> colour band, for the nine floor switches
        self.switches = switches
        #: tile -> collision value straight from the map grid (0 == walkable)
        self.collision = collision

    @property
    def initial_state(self) -> tuple[tuple[int, int], ...]:
        return tuple(obj.start for obj in self.objects)

    def press(self, state: tuple[tuple[int, int], ...], colour: int) -> tuple[tuple[int, int], ...]:
        """Apply one `moverotatingtileobjects <colour>`.

        ‼ THE UPDATE IS SIMULTANEOUS, AND DELIBERATELY HAS NO OCCUPANCY CHECK — see the module
        docstring. Every destination is computed from the state as it was BEFORE the press. Adding
        a "don't move into an occupied tile" guard here scores 2/6 against the game.

        :raises RuntimeError: if two objects would land on the same tile. That cannot happen while
            the arrows form closed cycles, so it means the arrow field was misread — and silently
            merging two objects would hand the solver a phantom free tile to route through."""
        moved = list(state)
        for index, position in enumerate(state):
            arrow = self.arrows.get(position)
            if arrow is None or arrow[0] != colour:
                continue
            dx, dy = DIRECTION_DELTAS[arrow[1]]
            moved[index] = (position[0] + dx, position[1] + dy)
        if len(set(moved)) != len(moved):
            collisions = sorted({tile for tile in moved if moved.count(tile) > 1})
            raise RuntimeError(
                f"rotating {COLOUR_NAMES.get(colour, colour)} put two objects on {collisions}; "
                "the arrow field is misread"
            )
        return tuple(moved)

    def occupied_tiles(self, state: tuple[tuple[int, int], ...]) -> set[tuple[int, int]]:
        """Tiles an object stands on, and which the player therefore cannot enter."""
        return set(state)

    def is_walkable(self, tile: tuple[int, int], state: tuple[tuple[int, int], ...]) -> bool:
        """‼ Walkability here is COLLISION *plus* the live objects — the objects are the puzzle.

        A planner that reads only the ROM collision layer sees the corridors as permanently sealed,
        which is precisely the false 'no route' that cost this project four wrong conclusions."""
        return self.collision.get(tile, 1) == 0 and tile not in state


def build_puzzle_from_emulator() -> MossdeepGymPuzzle:
    """Read the arrow field, the switches, the object templates and the collision layer from ROM.

    ‼ `MapLocation.objects` reads the map header's event list, which lives in ROM, so it always
    returns the ORIGINAL template positions — never the mutated ones. That is what we want as a
    starting state. The mutated, live positions come from `get_map_objects()`, and the two are
    deliberately different things."""
    from modules.map import get_map_data
    from modules.map_data import MapRSE
    from modules.memory import unpack_uint16, unpack_uint32
    from modules.context import context

    gym = MapRSE.MOSSDEEP_CITY_GYM
    origin = get_map_data(gym, (0, 0))
    width, height = origin.map_size

    # The raw metatile id is computed inside `map.py` (line 779) but not returned. Re-reading the
    # two bytes here keeps a SHARED module untouched for the sake of one puzzle.
    map_data_pointer = unpack_uint32(origin._map_layout[12:16])

    def metatile_id(x: int, y: int) -> int:
        offset = (x * 2) + (width * y * 2)
        block = unpack_uint16(context.emulator.read_bytes(map_data_pointer + offset, 2))
        return block & 0x03FF

    arrows: dict[tuple[int, int], tuple[int, int]] = {}
    switches: dict[tuple[int, int], int] = {}
    collision: dict[tuple[int, int], int] = {}
    for y in range(height):
        for x in range(width):
            tile = (x, y)
            collision[tile] = get_map_data(gym, tile).collision
            metatile = metatile_id(x, y)
            if not (ARROW_BASE <= metatile <= ARROW_TOP):
                continue
            band, code = divmod(metatile - ARROW_BASE, 8)
            if code in SWITCH_CODES:
                switches[tile] = band
            else:
                arrows[tile] = (band, code)

    objects = [
        GymObject(
            local_id=template.local_id,
            graphics_id=template.graphics_id,
            start=template.local_coordinates,
            is_statue=template.graphics_id == STATUE_GRAPHICS_ID,
            is_trainer=template.trainer_type != "None",
        )
        for template in origin.objects
    ]

    return MossdeepGymPuzzle(objects=objects, arrows=arrows, switches=switches, collision=collision)
