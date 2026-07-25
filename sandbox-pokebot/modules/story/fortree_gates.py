"""Fortree City Gym "rotating gate" puzzle solver.

Ported 1:1 from pokeemerald's `src/rotating_gate.c` (verbatim source captured at
`tools/story-dev/fortree/rotating_gate.c`, via `gh api repos/pret/pokeemerald/
contents/src/rotating_gate.c`), following the verified standalone port at
`tools/story-dev/fortree/fortree_gate_solver.py` -- do NOT redesign the tables
or the algorithm, only adapt I/O to pokebot's live-memory reader and its
"Up"/"Down"/"Left"/"Right" direction convention.

Live validation (2026-07-24 probe against the running emulator, save
`tools/story-dev/saves/fortree_gym_wedge.ss1`): at (4,19) with the initial
gate orientations, this model agrees 4/4 with the real game -- North blocked,
South allowed -> (4,20), West allowed -> (3,19), East blocked. `solve()` finds
an 83-move route from (4,19) and a 97-move route from the gym entrance
(15,24), both to Winona's challenge tile (15,3).

Orientation reset: `RotatingGate_InitPuzzle` -> `RotatingGate_ResetAllGateOrientations`
runs from `MAP_SCRIPT_ON_TRANSITION` on every warp INTO this map, resetting all
8 gates back to their `FORTREE_GATES` initial orientation. So a fresh plan from
the entrance is valid on every attempt, and re-entering after leaving is a
guaranteed clean reset -- `do_fortree_gym` uses this to recover if `solve()`
ever returns `None` from the live state.

Orientation is live-readable with no new memory reader: the puzzle overlays
the 8 gates' orientation bytes onto VAR_TEMP_0..VAR_TEMP_3 as a `u8*`
(`RotatingGate_GetGateOrientation` indexes `(u8 *)GetVarPointer(VAR_TEMP_0)`),
so gate `i`'s orientation is the low byte of `TEMP_{i//2}` if `i` is even, the
high byte if `i` is odd -- see `read_orientations()` below.

Static collision (the walls/floor layer) NEVER changes; only the gates'
*dynamic* arm layer changes, and that is fully captured by `orientations`.
`_get_collision_grid()` reads it once from the live map via
`modules.map.get_map_data` (never from a file under `tools/`) and caches it,
since re-reading ~500 tiles from the emulator on every `solve()` call/replan
would be wasteful for state that is provably static.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.memory import get_event_var

GYM = MapRSE.FORTREE_CITY_GYM

# ---- verbatim constants from src/rotating_gate.c ----
GATE_ARM_NORTH, GATE_ARM_EAST, GATE_ARM_SOUTH, GATE_ARM_WEST = 0, 1, 2, 3
ROTATE_NONE, ROTATE_ANTICLOCKWISE, ROTATE_CLOCKWISE = 0, 1, 2
GATE_ORIENTATION_MAX = 4
GATE_ROT_NONE = 255


def _gate_rot(rotation_direction: int, arm: int, long_arm: int) -> int:
    return ((rotation_direction & 15) << 4) | ((arm & 7) << 1) | (long_arm & 1)


def _gate_rot_cw(arm: int, long_arm: int) -> int:
    return _gate_rot(ROTATE_CLOCKWISE, arm, long_arm)


def _gate_rot_acw(arm: int, long_arm: int) -> int:
    return _gate_rot(ROTATE_ANTICLOCKWISE, arm, long_arm)


# DIR_* from include/constants/global.h
DIR_SOUTH, DIR_NORTH, DIR_WEST, DIR_EAST = 1, 2, 3, 4

RotationInfoNorth = [
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
    _gate_rot_cw(GATE_ARM_WEST, 1), _gate_rot_cw(GATE_ARM_WEST, 0), _gate_rot_acw(GATE_ARM_EAST, 0), _gate_rot_acw(GATE_ARM_EAST, 1),
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
]
RotationInfoSouth = [
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
    _gate_rot_acw(GATE_ARM_WEST, 1), _gate_rot_acw(GATE_ARM_WEST, 0), _gate_rot_cw(GATE_ARM_EAST, 0), _gate_rot_cw(GATE_ARM_EAST, 1),
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
]
RotationInfoWest = [
    GATE_ROT_NONE, _gate_rot_acw(GATE_ARM_NORTH, 1), GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, _gate_rot_acw(GATE_ARM_NORTH, 0), GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, _gate_rot_cw(GATE_ARM_SOUTH, 0), GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, _gate_rot_cw(GATE_ARM_SOUTH, 1), GATE_ROT_NONE, GATE_ROT_NONE,
]
RotationInfoEast = [
    GATE_ROT_NONE, GATE_ROT_NONE, _gate_rot_cw(GATE_ARM_NORTH, 1), GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, _gate_rot_cw(GATE_ARM_NORTH, 0), GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, _gate_rot_acw(GATE_ARM_SOUTH, 0), GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, _gate_rot_acw(GATE_ARM_SOUTH, 1), GATE_ROT_NONE,
]

ArmPositionsCW = [(0, -1), (1, -2), (0, 0), (1, 0), (-1, 0), (-1, 1), (-1, -1), (-2, -1)]
ArmPositionsACW = [(-1, -1), (-1, -2), (0, -1), (1, -1), (0, 0), (0, 1), (-1, 0), (-2, 0)]

# shape indices
L1, L2, L3, L4, T1, T2, T3, T4 = range(8)

ArmLayout = [
    [1, 0, 1, 0, 0, 0, 0, 0],  # L1
    [1, 1, 1, 0, 0, 0, 0, 0],  # L2
    [1, 0, 1, 1, 0, 0, 0, 0],  # L3
    [1, 1, 1, 1, 0, 0, 0, 0],  # L4
    [1, 0, 1, 0, 1, 0, 0, 0],  # T1
    [1, 1, 1, 0, 1, 0, 0, 0],  # T2
    [1, 0, 1, 1, 1, 0, 0, 0],  # T3
    [1, 0, 1, 0, 1, 1, 0, 0],  # T4 (unused in practice per config, kept for completeness)
]

# Fortree City Gym puzzle config: (x, y, shape, initial_orientation) -- verbatim
# from sRotatingGate_FortreePuzzleConfig, and in the SAME gate-index order as
# the VAR_TEMP_0..3 byte array read_orientations() decodes.
FORTREE_GATES = [
    (6, 7, T2, 1),   # GATE_ORIENTATION_90 = 1
    (9, 15, T2, 2),  # 180
    (3, 19, T2, 1),  # 90
    (2, 6, T1, 1),   # 90
    (9, 12, T1, 0),  # 0
    (6, 23, T1, 0),  # 0
    (12, 22, T1, 0),  # 0
    (6, 3, L4, 2),   # 180
]

N_GATES = len(FORTREE_GATES)

_DIRS = [("Up", DIR_NORTH), ("Down", DIR_SOUTH), ("Left", DIR_WEST), ("Right", DIR_EAST)]


def read_orientations() -> tuple[int, ...]:
    """Read the live orientation of all 8 Fortree gym gates.

    `RotatingGate_GetGateOrientation` indexes `(u8 *)GetVarPointer(VAR_TEMP_0)`
    by gate id, i.e. the 8 gate-orientation bytes are packed 2-per-u16 across
    VAR_TEMP_0..VAR_TEMP_3 -- gate `i`'s byte is the low byte of `TEMP_{i//2}`
    when `i` is even, the high byte when `i` is odd.
    """
    return tuple((get_event_var(f"TEMP_{i // 2}") >> (8 * (i % 2))) & 0xFF for i in range(N_GATES))


_collision_grid_cache: dict[int, tuple[list, int, int]] = {}


def _get_collision_grid() -> tuple[list, int, int]:
    """Static collision grid for the gym (never changes -- only the gates'
    dynamic arm layer does, and that lives entirely in `orientations`).
    Cached per ROM so `solve()` doesn't re-read ~500 tiles from the emulator
    on every call/replan."""
    from modules.context import context

    rom_id = context.rom.id
    if rom_id not in _collision_grid_cache:
        w, h = get_map_data(GYM.value, (0, 0)).map_size
        grid = [[get_map_data(GYM.value, (x, y)).collision for x in range(w)] for y in range(h)]
        _collision_grid_cache[rom_id] = (grid, w, h)
    return _collision_grid_cache[rom_id]


def has_arm(shape: int, orientation: int, arm_info: int) -> int:
    arm = arm_info // 2
    is_long = arm_info % 2
    arm_orientation = (arm - orientation + 4) % 4
    return ArmLayout[shape][arm_orientation * 2 + is_long]


def can_rotate(
    gx: int, gy: int, shape: int, orientation: int, rotation_direction: int, grid: list, w: int, h: int, use_bugfix: bool = False
) -> bool:
    arm_pos = ArmPositionsACW if rotation_direction == ROTATE_ANTICLOCKWISE else ArmPositionsCW
    for i in (GATE_ARM_NORTH, GATE_ARM_EAST, GATE_ARM_SOUTH, GATE_ARM_WEST):
        for j in range(2):
            arm_index = 2 * ((orientation + i) % 4) + j
            if ArmLayout[shape][2 * i + j]:
                dx, dy = arm_pos[arm_index]
                cx, cy = gx + dx, gy + dy
                if not (0 <= cx < w and 0 <= cy < h):
                    return False  # out of map -> treat as solid
                c = grid[cy][cx]
                if use_bugfix:
                    if c != 0:
                        return False
                else:
                    if c == 1:
                        return False
    return True


def rotate_in_direction(orientation: int, rotation_direction: int) -> int:
    if rotation_direction == ROTATE_ANTICLOCKWISE:
        return GATE_ORIENTATION_MAX - 1 if orientation == 0 else orientation - 1
    else:
        return (orientation + 1) % GATE_ORIENTATION_MAX


def get_rotation_info(direction: int, cx: int, cy: int) -> int:
    table = {
        DIR_NORTH: RotationInfoNorth,
        DIR_SOUTH: RotationInfoSouth,
        DIR_WEST: RotationInfoWest,
        DIR_EAST: RotationInfoEast,
    }[direction]
    return table[cy * 4 + cx]


def try_move(
    px: int,
    py: int,
    direction: int,
    orientations: tuple,
    grid: list,
    w: int,
    h: int,
    use_bugfix: bool = False,
    blocked: frozenset = frozenset(),
) -> tuple:
    """Returns (allowed, nx, ny, new_orientations_or_None_if_unchanged, gate_index_rotated_or_None).

    `blocked` is an optional set of (x, y) tiles to treat as impassable exactly
    like `grid[y][x] != 0` -- used by callers to feed in LIVE object positions
    (NPCs), which the ported decomp model has no notion of (the decomp only
    ever consults `MapGridGetCollisionAt`, i.e. static collision). This is
    deliberately checked at the same point as the static-wall check, and
    NOWHERE ELSE -- in particular `can_rotate`'s swept-arm-tile check below is
    untouched, since in the decomp a gate's rotation is gated on STATIC
    collision only (`RotatingGate_CanRotate` also only calls
    `MapGridGetCollisionAt`); inventing an NPC constraint there would diverge
    from the validated behaviour."""
    dx, dy = {DIR_NORTH: (0, -1), DIR_SOUTH: (0, 1), DIR_WEST: (-1, 0), DIR_EAST: (1, 0)}[direction]
    nx, ny = px + dx, py + dy
    if not (0 <= nx < w and 0 <= ny < h):
        return False, px, py, None, None
    if grid[ny][nx] != 0:
        return False, px, py, None, None  # ordinary wall
    if (nx, ny) in blocked:
        return False, px, py, None, None  # live object (e.g. an NPC) standing there

    for i, (gx, gy, shape, _init) in enumerate(FORTREE_GATES):
        if gx - 2 <= nx <= gx + 1 and gy - 2 <= ny <= gy + 1:
            cx, cy = nx - gx + 2, ny - gy + 2
            info = get_rotation_info(direction, cx, cy)
            if info != GATE_ROT_NONE:
                rot_dir = (info & 0xF0) >> 4
                arm_info = info & 0xF
                orientation = orientations[i]
                if has_arm(shape, orientation, arm_info):
                    if can_rotate(gx, gy, shape, orientation, rot_dir, grid, w, h, use_bugfix):
                        new_o = list(orientations)
                        new_o[i] = rotate_in_direction(orientation, rot_dir)
                        return True, nx, ny, tuple(new_o), i
                    else:
                        return False, px, py, None, None
            # else: GATE_ROT_NONE -> not blocked by this gate, fall through
            break  # only one gate box can contain a given tile (they don't overlap)
    return True, nx, ny, None, None


def solve(
    start_xy: tuple[int, int],
    orientations: tuple[int, ...],
    goal_xy: tuple[int, int] = (15, 3),
    max_states: int = 200_000,
    blocked: frozenset = frozenset(),
) -> Optional[list[str]]:
    """BFS over `(x, y, orientations)` states from `start_xy`/`orientations` to
    `goal_xy`, using the live collision grid + `FORTREE_GATES` config. Returns
    a list of "Up"/"Down"/"Left"/"Right" moves (possibly empty if already at
    `goal_xy`), or `None` if `goal_xy` is unreachable from this exact state.

    `blocked` is an optional set of (x, y) tiles (e.g. live NPC positions) to
    treat as impassable in addition to static collision -- see `try_move` for
    exactly what this does and doesn't affect. Passing the default empty set
    reproduces the plain ported-decomp behaviour exactly (validated: 4/4 push
    agreement at (4,19), 83-move route from (4,19), 97-move route from the
    gym entrance (15,24)).

    `max_states` bounds the search so a pathological configuration cannot spin
    forever; the reference solver (`fortree_gate_solver.bfs`) converges long
    before this on the real puzzle."""
    grid, w, h = _get_collision_grid()
    start_state = (start_xy[0], start_xy[1], tuple(orientations))
    visited = {start_state}
    parent = {}
    q = deque([start_state])
    states_explored = 0
    while q:
        state = q.popleft()
        px, py, o = state
        if (px, py) == tuple(goal_xy):
            path = []
            s = state
            while s in parent:
                s, label = parent[s]
                path.append(label)
            path.reverse()
            return path
        states_explored += 1
        if states_explored > max_states:
            return None
        for label, direction in _DIRS:
            allowed, nx, ny, new_o, _gate_idx = try_move(px, py, direction, o, grid, w, h, blocked=blocked)
            if not allowed:
                continue
            no = new_o if new_o is not None else o
            new_state = (nx, ny, no)
            if new_state not in visited:
                visited.add(new_state)
                parent[new_state] = (state, label)
                q.append(new_state)
    return None
