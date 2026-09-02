"""§Ch21 LEG 3 — WHICH 16-STEP HAND-WALKED TAIL? ROUTE131 (28,15) -> the door (36,6), from OUR ROM.

‼ WHY THIS EXISTS. `probe_ch21_route131_live.py` (the PRE-BUILD GATE, 2026-08-28) proved the
SET A / SET B divergence and printed `(28,15) -> the door: SET A None   SET B 17`. It answered
"the final approach MUST be hand-walked" — and it stopped there, because its `bfs()` returns a
DISTANCE, never a PATH. So the tree contains a proven step COUNT and no proven step LIST.

The leg-3 BUILD SPEC then arrived carrying **TWO DIFFERENT 16-step tails**, one per critic, each
claiming production provenance:

    CRITIC 1  ... (34,15) (34,14) (35,14) (36,14) then UP the x=36 column, dismounting at (36,8)
    CRITIC 2  ... (34,15) (34,14) then UP the x=34 column to (34,7), dismounting at (34,8),
                  then RIGHT (35,7) (36,7)

Both are internally contiguous under this codebase's `Up == y-1` (walking.py:580-588). Both end at
(36,7). ⛔ They cannot both be "the" tail, and the difference is not cosmetic: these are BLIND
steps on a map where our planner reads the WRONG LAYOUT, so a wrong tile is a silent wall-jam at
the end of a one-shot ~50,000-frame swim with no fallback route. Critic 2 itself refuted the
provenance claim ("a control on the default layout cannot validate a route on the swapped one").

⇒ THIS PROBE ADJUDICATES THEM AGAINST THE ONLY ORACLE THAT MATTERS HERE: our own ROM's SET B
bytes. It reports per tile: collision + elevation + metatile BEHAVIOUR NAME, in BOTH sets. It also
emits an INDEPENDENT BFS path over SET B, so the two proposals are graded against a third reading
rather than against each other.

⛔ READ NARROWLY, exactly as the gate does. This is a STATIC comparison of two ROM layouts. It
does NOT prove which layout ROUTE131 loads at runtime; `setmaplayoutindex` writes only the live
`gMapHeader`. The first leg-3 drive still owes the runtime reading.

--------------------------------------------------------------------------------------------
CONTROLS (a probe that finds nothing must be distinguishable from one that cannot see)
--------------------------------------------------------------------------------------------
C1  SET A is re-identified by AGREEMENT with production's own `get_map_data` collision reads.
C2  the SET A decode must reproduce THREE numbers production measured independently:
    (40,20)->(28,15) = 35, (40,19)->(28,15) = 16, and (40,19) reading as a WALL in SET A.
C3  SET B is the same-sized layout that OPENS the blind step (40,19) AND opens the door (36,6).
C4  ‼ NEW, AND LOAD-BEARING FOR THIS PROBE SPECIFICALLY: SET A and SET B must share BOTH tileset
    pointers. Behaviour NAMES are decoded through the layout's own tilesets (map.py:795-810); if
    the two layouts used different tilesets, every behaviour name printed for SET B would be
    decoded against the wrong attribute table and would be quietly meaningless. The PRE-BUILD
    GATE never needed this because it only ever compared COLLISION bits.

FAULT HOOKS (⛔ a gate that cannot fail is not a gate — every one of these is exercised):
    POKEBOT_R131TAIL_FAULT=stride    mis-strides the block decode  -> C2 MUST go RED
    POKEBOT_R131TAIL_FAULT=swapsets  audits the tails against SET A instead of SET B
                                     -> the TAIL AUDIT MUST report walls (it is the tails' whole
                                        premise that SET A calls them walls)
    POKEBOT_R131TAIL_FAULT=bendtail  corrupts one tile of CRITIC 1's list
                                     -> the CONTIGUITY check MUST name that step index

Run:        cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch21_route131_tail.py
Self-test:  POKEBOT_R131TAIL_FAULT=stride|swapsets|bendtail  ... same ...
"""

import os as _os
import pathlib
import sys
from collections import deque

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"

from modules.map import get_map_data, _get_tile_type_name
from modules.map_data import MapRSE
from modules.memory import read_symbol, unpack_uint16, unpack_uint32

ROUTE131 = MapRSE.ROUTE131

# --- production's own oracle numbers (the same three the PRE-BUILD GATE uses) -------------------
# ⛔ Do NOT "fix" these to match a decode. They are the oracle; a mismatch means the DECODE is wrong.
PROD_35 = 35
PROD_16 = 16
PROD_BLIND = (40, 19)

STAGING = (28, 15)
DOOR = (36, 6)

# --- the two candidate tails, transcribed VERBATIM from the BUILD SPEC --------------------------
# ‼ Transcribed as (direction, expected_tile) pairs so CONTIGUITY is CHECKED rather than assumed:
# under walking.py:580-588, Up == (x, y-1), Down == (x, y+1), Left == (x-1, y), Right == (x+1, y).
CRITIC1_DIRS = ("Right",) * 6 + ("Up", "Right", "Right") + ("Up",) * 7
CRITIC1_TILES = (
    (29, 15), (30, 15), (31, 15), (32, 15), (33, 15), (34, 15),
    (34, 14), (35, 14), (36, 14),
    (36, 13), (36, 12), (36, 11), (36, 10), (36, 9), (36, 8), (36, 7),
)

CRITIC2_DIRS = ("Right",) * 6 + ("Up",) * 8 + ("Right", "Right")
CRITIC2_TILES = (
    (29, 15), (30, 15), (31, 15), (32, 15), (33, 15), (34, 15),
    (34, 14), (34, 13), (34, 12), (34, 11), (34, 10), (34, 9), (34, 8), (34, 7),
    (35, 7), (36, 7),
)

_FAULT = _os.environ.get("POKEBOT_R131TAIL_FAULT", "").strip()

if _FAULT == "bendtail":
    _bent = list(CRITIC1_TILES)
    _bent[7] = (35, 13)          # was (35,14): now unreachable from (34,14) by a single "Right"
    CRITIC1_TILES = tuple(_bent)

DIRECTION_DELTA = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}

#: A tile outside the grid must read as a WALL, never as walkable. 0x0400 sets collision bits to 1.
OFF_MAP = 0x0400


def rom_read(address: int, length: int) -> bytes:
    return context.emulator.read_bytes(address, length)


def layout_structs(max_layouts: int = 1024) -> list[tuple[int, int, int, bytes]]:
    """(index, width, height, the whole 24-byte struct) for every plausible layout in gMapLayouts."""
    table = read_symbol("gMapLayouts", 0, 4 * max_layouts)
    out = []
    for index in range(max_layouts):
        pointer = unpack_uint32(table[index * 4 : index * 4 + 4])
        if not (0x08000000 <= pointer < 0x0A000000):
            continue
        try:
            struct = rom_read(pointer, 24)
        except Exception:
            continue
        width = unpack_uint32(struct[0:4])
        height = unpack_uint32(struct[4:8])
        blockdata = unpack_uint32(struct[12:16])
        if not (1 <= width <= 200 and 1 <= height <= 200):
            continue
        if not (0x08000000 <= blockdata < 0x0A000000):
            continue
        out.append((index, width, height, struct))
    return out


def block_grid(struct: bytes, width: int, height: int) -> dict[tuple[int, int], int]:
    """The 16-bit block value per tile, decoded EXACTLY as `map.py` does it.

    ‼ THE BORDER FALLBACK MIRRORS `map.py:772-777`: any block whose metatile id reads 0x3FF is
    replaced by the layout's BORDER block ORed with 0xC00 — collision 3, a WALL. It changes nothing
    on the tiles this probe actually reads (Route 131 has no in-bounds 0x3FF block), and it is here
    only so the decode is FAITHFUL rather than merely sufficient.
    ⛔ HONEST PROVENANCE, because a comment that credits the wrong fix is worse than none: this
    fallback was added as a GUESS at why CONTROL 1 first read 90.0% instead of the gate's 100.0%,
    and the guess was WRONG — it changed nothing. The real cause was that CONTROL 1's own SAMPLE
    ran y up to 42 on a 40-tall map, so 28 out-of-bounds tiles compared production's border block
    against a key this grid does not have. The control was broken, not the decode. (Project rule:
    when a probe fails, read the failing line before touching the thing under test.)
    """
    stride = 3 if _FAULT == "stride" else 2      # the fault hook mis-strides the decode
    blockdata = unpack_uint32(struct[12:16])
    border_pointer = unpack_uint32(struct[8:12])
    border = [unpack_uint16(rom_read(border_pointer + i * 2, 2)) for i in range(4)]
    raw = rom_read(blockdata, width * height * stride)
    grid = {}
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * stride
            block = raw[offset] | (raw[offset + 1] << 8)
            if (block & 0x03FF) == 0x03FF:                       # map.py:772
                i = ((x + 1) & 1) + (((y + 1) & 1) * 2)          # map.py:773-775
                block = border[i] | 0xC00                        # map.py:777
            grid[(x, y)] = block
    return grid


def collision_of(block: int) -> int:
    return (block & 0x0C00) >> 10       # map.py:780


def elevation_of(block: int) -> int:
    return (block & 0xF000) >> 12       # map.py:781


def behaviour_name(struct: bytes, block: int) -> str:
    """The metatile BEHAVIOUR name, decoded through THIS layout's own tilesets (map.py:786-810)."""
    metatile = block & 0x03FF
    metatiles_in_primary = 512          # the emerald branch of map.py:787-796
    attributes_size = 2
    attributes_offset = 0x10
    if metatile < metatiles_in_primary:
        tileset_pointer = unpack_uint32(struct[16:20])
        attribute_offset = metatile * attributes_size
    else:
        tileset_pointer = unpack_uint32(struct[20:24])
        attribute_offset = (metatile - metatiles_in_primary) * attributes_size
    attributes_pointer = unpack_uint32(rom_read(tileset_pointer + attributes_offset, 4))
    attribute = unpack_uint16(rom_read(attributes_pointer + attribute_offset, 2))
    return _get_tile_type_name(attribute & 0xFF)


def bfs_path(grid: dict[tuple[int, int], int], src, dst) -> list[tuple[int, int]] | None:
    """Shortest 4-neighbour PATH over collision-0 tiles (the source may itself be blocked)."""
    previous = {src: None}
    queue = deque([src])
    while queue:
        current = queue.popleft()
        if current == dst:
            out = []
            while current is not None:
                out.append(current)
                current = previous[current]
            return list(reversed(out))[1:]      # drop the source; emit the STEPS
        x, y = current
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in previous:
                continue
            if collision_of(grid.get(nxt, OFF_MAP)) != 0:
                continue
            previous[nxt] = current
            queue.append(nxt)
    return None


def bfs_distance(grid, src, dst) -> int | None:
    seen = {src}
    queue = deque([(src, 0)])
    while queue:
        (x, y), dist = queue.popleft()
        if (x, y) == dst:
            return dist
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in seen:
                continue
            if collision_of(grid.get(nxt, OFF_MAP)) != 0:
                continue
            seen.add(nxt)
            queue.append((nxt, dist + 1))
    return None


def audit_tail(label, dirs, tiles, grid_b, struct_b, grid_a, struct_a) -> dict:
    """Grade one proposed tail. Prints the per-tile table and returns a verdict dict."""
    print("")
    print(f"  --- {label} : {len(dirs)} directions, {len(tiles)} tiles ---")
    verdict = {
        "label": label,
        "length_ok": len(dirs) == len(tiles),
        "contiguous": True,
        "walkable_b": True,
        "blind_steps": [],
        "elevation_changes": [],
    }

    if not verdict["length_ok"]:
        print(f"    ⛔ LENGTH MISMATCH: {len(dirs)} directions vs {len(tiles)} tiles — the list is "
              f"unusable as written; zip() would SILENTLY TRUNCATE to the shorter one.")

    print(f"    {'#':>2}  {'dir':<6} {'tile':<9} {'--- SET B ---':<40} {'--- SET A ---':<34} note")
    here = STAGING
    for index, (direction, tile) in enumerate(zip(dirs, tiles)):
        dx, dy = DIRECTION_DELTA[direction]
        implied = (here[0] + dx, here[1] + dy)
        contiguous = implied == tile
        if not contiguous:
            verdict["contiguous"] = False

        block_b = grid_b.get(tile, OFF_MAP)
        block_a = grid_a.get(tile, OFF_MAP)
        coll_b, elev_b = collision_of(block_b), elevation_of(block_b)
        coll_a, elev_a = collision_of(block_a), elevation_of(block_a)
        name_b = behaviour_name(struct_b, block_b)
        name_a = behaviour_name(struct_a, block_a)

        if coll_b != 0:
            verdict["walkable_b"] = False
        if coll_a != 0 and coll_b == 0:
            verdict["blind_steps"].append((index, tile))

        note = ""
        if not contiguous:
            note = f"⛔ NOT CONTIGUOUS — '{direction}' from {here} gives {implied}, not {tile}"
        elif coll_b != 0:
            note = "⛔ WALL in the audited set"
        elif coll_a != 0:
            note = "blind (the other set calls it a wall)"

        # A surf DISMOUNT shows up as an ELEVATION CHANGE between consecutive tiles.
        if index > 0:
            previous_elevation = elevation_of(grid_b.get(tiles[index - 1], OFF_MAP))
            if previous_elevation != elev_b:
                verdict["elevation_changes"].append(
                    (index, tiles[index - 1], tile, previous_elevation, elev_b)
                )
                note = (note + "  " if note else "") + f"‼ ELEVATION {previous_elevation} -> {elev_b}"

        print(f"    {index:>2}  {direction:<6} {str(tile):<9} "
              f"coll={coll_b} elev={elev_b:<2} {name_b:<24} "
              f"coll={coll_a} elev={elev_a:<2} {name_a:<16} {note}")
        here = tile

    verdict["ends_at"] = here
    print(f"    ⇒ ends at {here}; contiguous={verdict['contiguous']} "
          f"walkable_in_audited_set={verdict['walkable_b']} "
          f"blind_steps={len(verdict['blind_steps'])} "
          f"elevation_changes={len(verdict['elevation_changes'])}")
    return verdict


def main() -> int:
    print("=" * 104)
    print("§Ch21 LEG 3 — THE HAND-WALKED TAIL, ADJUDICATED FROM OUR OWN ROM (offline, no network)")
    print("=" * 104)
    if _FAULT:
        print(f"‼ FAULT HOOK ACTIVE: POKEBOT_R131TAIL_FAULT={_FAULT} — this run is a SELF-TEST.")

    width, height = get_map_data(ROUTE131, (0, 0)).map_size
    print("")
    print(f"ROUTE131 map_size = {(width, height)}")

    candidates = [row for row in layout_structs() if (row[1], row[2]) == (width, height)]
    print(f"same-sized layouts in `gMapLayouts` : {len(candidates)}  "
          f"(indices {[row[0] for row in candidates]})")
    print("  ⛔ candidates are selected by DIMENSIONS ALONE — never by looking for the tiles the")
    print("     recon predicted. The prediction is CHECKED against them below, not used to find them.")

    # ---- C1 -------------------------------------------------------------------------------------
    print("")
    print("-" * 104)
    print("CONTROL 1 — SET A is the layout that AGREES with production's own get_map_data")
    print("-" * 104)
    # ⛔ IN-BOUNDS ONLY, AND ASSERTED. An earlier draft sampled y up to 42 on a 40-tall map; the 28
    # out-of-bounds tiles read as production's BORDER block (collision 3) and dragged a perfectly
    # good decode down to 90.0%, which read as "the decode is wrong". A control fed illegal inputs
    # reports a defect in the wrong component.
    sample = [(x, y) for x in range(2, width - 2, 2) for y in range(2, height - 2, 2)]
    out_of_bounds = [t for t in sample if not (0 <= t[0] < width and 0 <= t[1] < height)]
    if out_of_bounds:
        print(f"  ⛔ {len(out_of_bounds)} sampled tiles are OUT OF BOUNDS for a {width}x{height} "
              f"map — the control is invalid. Fix the sample, not the decode.")
        return 1
    production = {}
    for tile in sample:
        try:
            production[tile] = get_map_data(ROUTE131, tile).collision
        except Exception:
            continue
    grids = {}
    structs = {}
    best = (None, -1.0)
    for index, w, h, struct in candidates:
        grid = block_grid(struct, w, h)
        grids[index] = grid
        structs[index] = struct
        hits = sum(1 for tile, coll in production.items()
                   if collision_of(grid.get(tile, OFF_MAP)) == coll)
        rate = hits / len(production)
        print(f"  layout #{index:<4d} agreement over {len(production)} sampled tiles: "
              f"{hits}/{len(production)} = {rate:.1%}")
        if rate > best[1]:
            best = (index, rate)
    set_a_index, set_a_rate = best
    c1_ok = set_a_rate >= 0.99
    print(f"  ⇒ SET A = layout #{set_a_index} at {set_a_rate:.1%}   {'PASS' if c1_ok else 'FAIL'}")

    grid_a, struct_a = grids[set_a_index], structs[set_a_index]

    # ---- C2 -------------------------------------------------------------------------------------
    print("")
    print("-" * 104)
    print("CONTROL 2 — the SET A decode must reproduce THREE production numbers")
    print("-" * 104)
    d35 = bfs_distance(grid_a, (40, 20), STAGING)
    d16 = bfs_distance(grid_a, PROD_BLIND, STAGING)
    blind_is_wall = collision_of(grid_a.get(PROD_BLIND, OFF_MAP)) != 0
    c2a, c2b, c2c = d35 == PROD_35, d16 == PROD_16, blind_is_wall
    print(f"  (40,20)->(28,15) : decode {d35}  production {PROD_35}   {'MATCH' if c2a else 'MISMATCH'}")
    print(f"  (40,19)->(28,15) : decode {d16}  production {PROD_16}   {'MATCH' if c2b else 'MISMATCH'}")
    print(f"  (40,19) is a WALL in SET A : {blind_is_wall}            {'MATCH' if c2c else 'MISMATCH'}")
    c2_ok = c2a and c2b and c2c
    print(f"  ⇒ {'PASS — the decode agrees with the emulator oracle in three places' if c2_ok else 'FAIL'}")

    # ---- C3 -------------------------------------------------------------------------------------
    print("")
    print("-" * 104)
    print("CONTROL 3 — SET B is the same-sized layout that opens the blind step AND the tower door")
    print("-" * 104)
    set_b_index = None
    for index in grids:
        if index == set_a_index:
            continue
        opens_blind = collision_of(grids[index].get(PROD_BLIND, OFF_MAP)) == 0
        opens_door = collision_of(grids[index].get(DOOR, OFF_MAP)) == 0
        print(f"  layout #{index:<4d} opens blind step {PROD_BLIND}: {opens_blind}   "
              f"opens door {DOOR}: {opens_door}")
        if opens_blind and opens_door:
            set_b_index = index
    c3_ok = set_b_index is not None
    print(f"  ⇒ SET B = layout #{set_b_index}   "
          f"{'PASS' if c3_ok else 'FAIL — no candidate explains the route'}")

    if not (c1_ok and c2_ok and c3_ok):
        print("")
        print("‼ CONTROLS FAILED — every measurement below is UNTRUSTED. Do not act on it.")
        return 1

    grid_b, struct_b = grids[set_b_index], structs[set_b_index]

    # ---- C4 -------------------------------------------------------------------------------------
    print("")
    print("-" * 104)
    print("CONTROL 4 — SET A and SET B must share BOTH tilesets, or SET B's behaviour NAMES lie")
    print("-" * 104)
    primary_a, secondary_a = unpack_uint32(struct_a[16:20]), unpack_uint32(struct_a[20:24])
    primary_b, secondary_b = unpack_uint32(struct_b[16:20]), unpack_uint32(struct_b[20:24])
    print(f"  SET A tilesets: primary 0x{primary_a:08X}  secondary 0x{secondary_a:08X}")
    print(f"  SET B tilesets: primary 0x{primary_b:08X}  secondary 0x{secondary_b:08X}")
    c4_ok = (primary_a, secondary_a) == (primary_b, secondary_b)
    if c4_ok:
        print("  ⇒ PASS — identical, so a behaviour name decoded on SET B means what it says.")
    else:
        print("  ⇒ ‼ DIFFERENT — behaviour NAMES below are decoded per-layout and must NOT be")
        print("       compared across sets. COLLISION and ELEVATION remain valid either way.")

    # ---- M1 -------------------------------------------------------------------------------------
    print("")
    print("=" * 104)
    print("MEASUREMENT 1 — an INDEPENDENT shortest path (28,15) -> (36,6) over SET B")
    print("=" * 104)
    independent = bfs_path(grid_b, STAGING, DOOR)
    if independent is None:
        print("  ⛔ NO PATH over SET B — the whole hand-walked-tail premise is wrong. STOP.")
        return 1
    print(f"  {len(independent)} steps: {independent}")
    print("  ⛔ THIS IS ONE OF SEVERAL EQUAL-COST PATHS, NOT 'the' TAIL. It is a THIRD READING,")
    print("     offered so the two proposals are graded against something other than each other.")

    # ---- M2 -------------------------------------------------------------------------------------
    print("")
    print("=" * 104)
    print("MEASUREMENT 2 — the two proposed tails, tile by tile")
    if _FAULT == "swapsets":
        print("  ‼ FAULT swapsets: auditing against SET A. The tails MUST show walls — that is")
        print("    their entire premise, and an audit that passes here cannot fail anywhere.")
    print("=" * 104)
    if _FAULT == "swapsets":
        audited_grid, audited_struct, other_grid, other_struct = grid_a, struct_a, grid_b, struct_b
    else:
        audited_grid, audited_struct, other_grid, other_struct = grid_b, struct_b, grid_a, struct_a

    v1 = audit_tail("CRITIC 1 (x=36 column, dismount at (36,8))", CRITIC1_DIRS, CRITIC1_TILES,
                    audited_grid, audited_struct, other_grid, other_struct)
    v2 = audit_tail("CRITIC 2 (x=34 column, dismount at (34,8))", CRITIC2_DIRS, CRITIC2_TILES,
                    audited_grid, audited_struct, other_grid, other_struct)

    # ---- VERDICT ---------------------------------------------------------------------------------
    print("")
    print("=" * 104)
    print("VERDICT")
    print("=" * 104)
    for verdict in (v1, v2):
        usable = (verdict["length_ok"] and verdict["contiguous"] and verdict["walkable_b"]
                  and verdict["ends_at"] == (36, 7))
        print(f"  {verdict['label']:<46} {'USABLE' if usable else '⛔ NOT USABLE':<14}"
              f" ends {verdict['ends_at']}, {len(verdict['blind_steps'])} blind, "
              f"{len(verdict['elevation_changes'])} elevation changes")
        for change in verdict["elevation_changes"]:
            print(f"      elevation change at step {change[0]}: {change[1]} -> {change[2]} "
                  f"(elev {change[3]} -> {change[4]})")

    print("")
    print(f"  the door step (36,7) -> {DOOR}: SET B collision = "
          f"{collision_of(grid_b.get(DOOR, OFF_MAP))}, behaviour = "
          f"{behaviour_name(struct_b, grid_b.get(DOOR, OFF_MAP))}")
    print(f"  the SAME tile in SET A       : collision = "
          f"{collision_of(grid_a.get(DOOR, OFF_MAP))}, behaviour = "
          f"{behaviour_name(struct_a, grid_a.get(DOOR, OFF_MAP))}")

    print("")
    print("=" * 104)
    print("READ NARROWLY. A tail that is USABLE here is walkable on SET B's BYTES. It is NOT yet")
    print("proven that ROUTE131 LOADS SET B at runtime — that reading is owed by the first drive.")
    print("=" * 104)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
