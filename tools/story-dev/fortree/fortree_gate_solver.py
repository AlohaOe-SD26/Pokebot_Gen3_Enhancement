"""
Faithful re-implementation of pokeemerald's src/rotating_gate.c rotating-gate
puzzle logic (translated 1:1 from the decomp source, fetched verbatim via
`gh api repos/pret/pokeemerald/contents/src/rotating_gate.c`), combined with
the REAL Fortree City Gym static collision grid (decoded from
data/layouts/FortreeCity_Gym/map.bin, width=20 height=25 per
data/layouts/layouts.json), to BFS-solve the actual push sequence from the
gym entrance (15,24) to the Winona challenge tile (15,3).

Coordinate system: pokebot's `local_coordinates` == ObjectEvent.current_coords
== raw RAM value - 7 (modules/map.py current_coords property), which is the
SAME numbering as gSaveBlock1Ptr->pos and therefore the SAME numbering as the
unadjusted x,y in sRotatingGate_FortreePuzzleConfig. No MAP_OFFSET conversion
needed -- verified by cross-checking the entrance (15,24) and Winona tile
(15,3) both land on collision==0 cells in the decoded grid at those exact
coordinates.
"""
import struct
from collections import deque

MAP_BIN = r"C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\d0f92d0d-48bf-43f5-8546-c9ab8f27a963\scratchpad\fortree_gym_map.bin"
W, H = 20, 25

with open(MAP_BIN, "rb") as f:
    data = f.read()

# Static collision grid: collision != 0 => impassable wall (this never changes;
# only the *gate* dynamic-collision layer changes with orientation).
collision = [[0] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        val = struct.unpack_from("<H", data, (y * W + x) * 2)[0]
        collision[y][x] = (val >> 10) & 0x3

# ---- verbatim constants from src/rotating_gate.c ----
GATE_ARM_NORTH, GATE_ARM_EAST, GATE_ARM_SOUTH, GATE_ARM_WEST = 0, 1, 2, 3
ROTATE_NONE, ROTATE_ANTICLOCKWISE, ROTATE_CLOCKWISE = 0, 1, 2
GATE_ORIENTATION_MAX = 4
GATE_ROT_NONE = 255


def GATE_ROT(rotation_direction, arm, long_arm):
    return ((rotation_direction & 15) << 4) | ((arm & 7) << 1) | (long_arm & 1)


def GATE_ROT_CW(arm, long_arm):
    return GATE_ROT(ROTATE_CLOCKWISE, arm, long_arm)


def GATE_ROT_ACW(arm, long_arm):
    return GATE_ROT(ROTATE_ANTICLOCKWISE, arm, long_arm)


# DIR_* from include/constants/global.h
DIR_SOUTH, DIR_NORTH, DIR_WEST, DIR_EAST = 1, 2, 3, 4

RotationInfoNorth = [
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_CW(GATE_ARM_WEST, 1), GATE_ROT_CW(GATE_ARM_WEST, 0), GATE_ROT_ACW(GATE_ARM_EAST, 0), GATE_ROT_ACW(GATE_ARM_EAST, 1),
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
]
RotationInfoSouth = [
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_ACW(GATE_ARM_WEST, 1), GATE_ROT_ACW(GATE_ARM_WEST, 0), GATE_ROT_CW(GATE_ARM_EAST, 0), GATE_ROT_CW(GATE_ARM_EAST, 1),
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_NONE,
]
RotationInfoWest = [
    GATE_ROT_NONE, GATE_ROT_ACW(GATE_ARM_NORTH, 1), GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_ACW(GATE_ARM_NORTH, 0), GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_CW(GATE_ARM_SOUTH, 0), GATE_ROT_NONE, GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_CW(GATE_ARM_SOUTH, 1), GATE_ROT_NONE, GATE_ROT_NONE,
]
RotationInfoEast = [
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_CW(GATE_ARM_NORTH, 1), GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_CW(GATE_ARM_NORTH, 0), GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_ACW(GATE_ARM_SOUTH, 0), GATE_ROT_NONE,
    GATE_ROT_NONE, GATE_ROT_NONE, GATE_ROT_ACW(GATE_ARM_SOUTH, 1), GATE_ROT_NONE,
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

# Fortree City Gym puzzle config: (x, y, shape, initial_orientation)
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


def has_arm(shape, orientation, arm_info):
    arm = arm_info // 2
    is_long = arm_info % 2
    arm_orientation = (arm - orientation + 4) % 4
    return ArmLayout[shape][arm_orientation * 2 + is_long]


def can_rotate(gx, gy, shape, orientation, rotation_direction, use_bugfix=False):
    arm_pos = ArmPositionsACW if rotation_direction == ROTATE_ANTICLOCKWISE else ArmPositionsCW
    for i in (GATE_ARM_NORTH, GATE_ARM_EAST, GATE_ARM_SOUTH, GATE_ARM_WEST):
        for j in range(2):
            arm_index = 2 * ((orientation + i) % 4) + j
            if ArmLayout[shape][2 * i + j]:
                dx, dy = arm_pos[arm_index]
                cx, cy = gx + dx, gy + dy
                if not (0 <= cx < W and 0 <= cy < H):
                    return False  # out of map -> treat as solid
                c = collision[cy][cx]
                if use_bugfix:
                    if c != 0:
                        return False
                else:
                    if c == 1:
                        return False
    return True


def rotate_in_direction(orientation, rotation_direction):
    if rotation_direction == ROTATE_ANTICLOCKWISE:
        return GATE_ORIENTATION_MAX - 1 if orientation == 0 else orientation - 1
    else:
        return (orientation + 1) % GATE_ORIENTATION_MAX


def get_rotation_info(direction, cx, cy):
    table = {DIR_NORTH: RotationInfoNorth, DIR_SOUTH: RotationInfoSouth,
             DIR_WEST: RotationInfoWest, DIR_EAST: RotationInfoEast}[direction]
    return table[cy * 4 + cx]


def try_move(px, py, direction, orientations, use_bugfix=False):
    """Returns (allowed, nx, ny, new_orientations_or_None_if_unchanged, gate_index_rotated_or_None)."""
    dx, dy = {DIR_NORTH: (0, -1), DIR_SOUTH: (0, 1), DIR_WEST: (-1, 0), DIR_EAST: (1, 0)}[direction]
    nx, ny = px + dx, py + dy
    if not (0 <= nx < W and 0 <= ny < H):
        return False, px, py, None, None
    if collision[ny][nx] != 0:
        return False, px, py, None, None  # ordinary wall

    for i, (gx, gy, shape, _init) in enumerate(FORTREE_GATES):
        if gx - 2 <= nx <= gx + 1 and gy - 2 <= ny <= gy + 1:
            cx, cy = nx - gx + 2, ny - gy + 2
            info = get_rotation_info(direction, cx, cy)
            if info != GATE_ROT_NONE:
                rot_dir = (info & 0xF0) >> 4
                arm_info = info & 0xF
                orientation = orientations[i]
                if has_arm(shape, orientation, arm_info):
                    if can_rotate(gx, gy, shape, orientation, rot_dir, use_bugfix):
                        new_o = list(orientations)
                        new_o[i] = rotate_in_direction(orientation, rot_dir)
                        return True, nx, ny, tuple(new_o), i
                    else:
                        return False, px, py, None, None
            # else: GATE_ROT_NONE -> not blocked by this gate, fall through
            break  # only one gate box can contain a given tile (they don't overlap)
    return True, nx, ny, None, None


START = (15, 24)
TARGET = (15, 3)
INIT_ORIENTATIONS = tuple(g[3] for g in FORTREE_GATES)

DIRS = [("Up", DIR_NORTH), ("Down", DIR_SOUTH), ("Left", DIR_WEST), ("Right", DIR_EAST)]


def bfs(use_bugfix=False):
    start_state = (START[0], START[1], INIT_ORIENTATIONS)
    visited = {start_state}
    parent = {}
    q = deque([start_state])
    while q:
        state = q.popleft()
        px, py, orientations = state
        if (px, py) == TARGET:
            # reconstruct path
            path = []
            s = state
            while s in parent:
                s, label = parent[s]
                path.append(label)
            path.reverse()
            return path, len(visited)
        for label, direction in DIRS:
            allowed, nx, ny, new_o, gate_idx = try_move(px, py, direction, orientations, use_bugfix)
            if not allowed:
                continue
            no = new_o if new_o is not None else orientations
            new_state = (nx, ny, no)
            if new_state not in visited:
                visited.add(new_state)
                parent[new_state] = (state, label)
                q.append(new_state)
    return None, len(visited)


if __name__ == "__main__":
    for bugfix in (False, True):
        path, nvisited = bfs(use_bugfix=bugfix)
        print(f"use_bugfix={bugfix}: visited={nvisited} states")
        if path is None:
            print("  NO PATH FOUND")
        else:
            print(f"  SOLUTION ({len(path)} steps): {path}")

def replay_and_annotate(path):
    px, py = START
    orientations = INIT_ORIENTATIONS
    dirmap = {"Up": DIR_NORTH, "Down": DIR_SOUTH, "Left": DIR_WEST, "Right": DIR_EAST}
    annotated = []
    for label in path:
        d = dirmap[label]
        allowed, nx, ny, new_o, gate_idx = try_move(px, py, d, orientations, use_bugfix=False)
        assert allowed, f"illegal move replay at {(px,py)} dir {label}"
        tag = f"{label}" + (f"[ROTATE gate{gate_idx}]" if gate_idx is not None else "")
        annotated.append((tag, (nx, ny)))
        px, py = nx, ny
        if new_o is not None:
            orientations = new_o
    return annotated


def rle(path):
    out = []
    i = 0
    while i < len(path):
        j = i
        while j < len(path) and path[j] == path[i]:
            j += 1
        out.append(f"{path[i]} x{j-i}")
        i = j
    return out


if __name__ == "__main__":
    path, _ = bfs(use_bugfix=False)
    ann = replay_and_annotate(path)
    print("\n=== Annotated replay (dir, resulting pos, rotation events) ===")
    for tag, pos in ann:
        print(f"  {tag:28s} -> {pos}")
    print("\n=== Run-length encoded button sequence ===")
    print(", ".join(rle(path)))
