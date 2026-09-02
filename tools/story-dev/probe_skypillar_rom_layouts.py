"""SKY PILLAR — THE **CLEAN** (STORY) LAYOUTS FOR ALL SIX FLOORS, FROM **OUR OWN ROM**, OFFLINE.

‼ WHY THIS EXISTS, AND WHY IT IS NOT A DUPLICATE OF `probe_skypillar_clean_layout.py`.
That probe fetches the DECOMP's shipped `SkyPillar_{2F,3F,4F}_Clean/map.bin` over HTTP. It answers
a real question and it should be kept — but it has two limits that block §Ch21 leg 4:

  1. ⛔ **IT COVERS THREE FLOORS.** It decodes 2F, 3F and 4F only (`:113-115`). It has NEVER seen
     `1F_Clean`, `5F_Clean` or `Top_Clean`. Four separate cold-start audits named the resulting gap:
     the atlas claims `SKY_PILLAR_TOP` has "31 tiles the static planner believes are OPEN that are
     WALLS on CLEAN", and **the named tool cannot check that map at all.**
  2. ⛔ **ITS DIMENSIONS ARE WRONG FOR HALF THE CHAPTER.** It hardcodes `W = H = 14` with the
     comment *"every Sky Pillar floor is 14x14"*. MEASURED from our ROM 2026-09-01, that is FALSE:
     1F-5F are 14x14, but **`SKY_PILLAR_TOP` is 27x24**, `SKY_PILLAR_ENTRANCE` 18x18 and
     `SKY_PILLAR_OUTSIDE` 28x23. An audit called extending it "a 3-line change"; it is not — a
     14x14 decode of TOP reads 392 bytes where 1,296 are needed. (Its length guard would catch it,
     which is why that probe fails loudly rather than lying — but it cannot be extended as-is.)

⇒ THIS PROBE READS THE LAYOUTS OUT OF THE ROM WE ACTUALLY RUN, with no network at all. That is the
project's stated preference (the playbook records that this environment silently corrupts binary
HTTP fetches) and it is strictly better evidence: the decomp describes what pret ships, our ROM is
what the bot plays.

--------------------------------------------------------------------------------------------
HOW A "CLEAN" LAYOUT IS IDENTIFIED WITHOUT BEING TOLD ITS INDEX
--------------------------------------------------------------------------------------------
`SkyPillar_<F>_OnTransition` runs `setmaplayoutindex LAYOUT_SKY_PILLAR_<F>_CLEAN` behind
`call_if_lt VAR_SKY_PILLAR_STATE, 2`, so the story climb runs on a DIFFERENT layout from the one
`get_map_data` / `calculate_path` read. We do not have the constant's value here, and dimensions
alone cannot find it — **eleven** layouts in this ROM are 14x14.

So the CLEAN twin is identified by CONTENT:

    DEFAULT  = the same-sized layout whose collision agrees with production's own `get_map_data`
    CLEAN    = among candidates whose CRACKED set is a SUBSET of DEFAULT's, the one with the
               HIGHEST collision agreement with DEFAULT

⛔ **THE FIRST VERSION OF THIS TEST FOUND NOTHING ON ALL SIX FLOORS, AND THAT NULL RESULT WAS THE
FINDING.** It asked for a candidate whose METATILE diff was a subset of DEFAULT's cracked tiles —
i.e. it assumed *"clean" = "the default with its cracks paved over"*. **It is not.** MEASURED
2026-09-01: the CLEAN layouts differ from their defaults in **COLLISION on ~7% of tiles**; they are
different floor plans, not a crack patch. That 7% is exactly the hazard leg 4 faces, so the wrong
assumption would have hidden the thing this probe exists to find. It was caught by this project's
own rule — *a probe that finds nothing is indistinguishable from one that cannot see* — so the null
was diagnosed rather than reported.

‼ AND BE PRECISE ABOUT WHICH HALF DISCRIMINATES. The `anycand` fault arm below MEASURED that the
crack-subset filter is **NOT** the discriminator: agreement alone selects the same six layouts. The
filter stays because it is cheap and it is what "clean" MEANS — but the honest description is
"ranked by AGREEMENT, filtered by cracks", never "identified by cracks".

⛔ THE WINNING MARGIN CAN BE THIN (2F: 93.4% vs 92.9%), SO THE MARGIN IS NOT WHAT IS TRUSTED. The
assignment is validated as a **BIJECTION** (control C5): six floors must select six DISTINCT
layouts, none of which is any floor's DEFAULT. That global constraint is what makes a 0.5% margin
safe, and it is CHECKED, not assumed. Every candidate's crack count and agreement is printed, so a
reader can watch the test discriminate rather than take its word.

--------------------------------------------------------------------------------------------
CONTROLS (a probe that finds nothing must be distinguishable from one that cannot see)
--------------------------------------------------------------------------------------------
C1  For every floor, the DEFAULT must be found at ~100% collision agreement with `get_map_data`.
C2  ‼ THE ONE THAT MAKES THIS TRUSTWORTHY — the ROM method must REPRODUCE the network method on the
    three floors both can see: `2F_Clean` has **0** cracked tiles and `4F_Clean` has **5**, at
    exactly `(0,3) (1,3) (6,4) (7,4) (9,4)`. That is the committed oracle in
    `evidence/2026-08-24-skypillar-clean-reachability.txt:16-18`, produced by an INDEPENDENT
    instrument over the decomp's own bytes. Agreement across two instruments on three floors is
    what licenses believing this one on the three floors only it can see.
C3  NEGATIVE CONTROL — `SKY_PILLAR_ENTRANCE` and `SKY_PILLAR_OUTSIDE` do NOT swap layouts, so they
    must have **no** CLEAN twin. A method that "finds" one everywhere has found nothing.
C4  DEFAULT and CLEAN must share both tileset pointers, or the behaviour NAMES decoded from CLEAN
    are read against the wrong attribute table and are meaningless.
C5  ‼ THE ASSIGNMENT MUST BE A BIJECTION — six floors, six DISTINCT clean layouts, none of them a
    DEFAULT. This is what makes a thin agreement margin safe.

FAULT HOOKS (⛔ a gate that cannot fail is not a gate — and one of these MEASURED ME WRONG):
    POKEBOT_SPROM_FAULT=stride     mis-strides the block decode -> C1, C2, C4 and C5 all go RED.
    POKEBOT_SPROM_FAULT=noagree    drops the AGREEMENT ranking and takes the FIRST crack-subset
                                   candidate in index order -> C5's BIJECTION must go RED (2F then
                                   selects #321, which is 1F's DEFAULT). ⇒ the agreement ranking is
                                   the load-bearing half of the selector.
    POKEBOT_SPROM_FAULT=anycand    drops the crack-subset filter, leaving agreement alone.
                                   ‼‼ **THIS ARM DOES NOT FIRE — IT PASSES EVERY CONTROL, AND THAT
                                   IS A MEASURED RESULT, NOT A BROKEN ARM.** It was written to
                                   prove the crack filter was doing the discriminating; it proved
                                   the OPPOSITE. ⛔ It is KEPT DELIBERATELY as the standing evidence
                                   for that claim — delete it and the next reader will re-assert
                                   that the crack filter is what does the work.

Run:        cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_skypillar_rom_layouts.py
Self-test:  POKEBOT_SPROM_FAULT=stride|noagree   (both must go RED)
            POKEBOT_SPROM_FAULT=anycand          (must PASS — see above)
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

_FAULT = _os.environ.get("POKEBOT_SPROM_FAULT", "").strip()

#: The floors that SWAP (1F-5F + TOP), then the two that do NOT (the negative control).
CLIMB_FLOORS = ["SKY_PILLAR_1F", "SKY_PILLAR_2F", "SKY_PILLAR_3F",
                "SKY_PILLAR_4F", "SKY_PILLAR_5F", "SKY_PILLAR_TOP"]
NO_SWAP_FLOORS = ["SKY_PILLAR_ENTRANCE", "SKY_PILLAR_OUTSIDE"]

#: C2's oracle, from `evidence/2026-08-24-skypillar-clean-reachability.txt:16-18` — produced by
#: `probe_skypillar_clean_layout.py` over the DECOMP's bytes, i.e. a genuinely independent
#: instrument. ⛔ Do NOT "fix" these to match a decode; they are the oracle.
ORACLE_CLEAN_CRACKS = {
    "SKY_PILLAR_2F": set(),
    "SKY_PILLAR_4F": {(0, 3), (1, 3), (6, 4), (7, 4), (9, 4)},
}

OFF_MAP = 0x0400          # a tile outside the grid reads as a WALL, never as walkable
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else '‼ FAIL'}  {label}" + (f"   {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


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
        width, height = unpack_uint32(struct[0:4]), unpack_uint32(struct[4:8])
        blockdata = unpack_uint32(struct[12:16])
        if not (1 <= width <= 200 and 1 <= height <= 200):
            continue
        if not (0x08000000 <= blockdata < 0x0A000000):
            continue
        out.append((index, width, height, struct))
    return out


def block_grid(struct: bytes, width: int, height: int) -> dict[tuple[int, int], int]:
    """The 16-bit block per tile, decoded EXACTLY as `map.py` does — border fallback included.

    ‼ The border rule (`map.py:772-777`) is not optional: a block whose metatile id reads 0x3FF is
    replaced by the layout's BORDER block ORed with 0xC00, i.e. a WALL. Omitting it makes a decode
    disagree with production on exactly the tiles nobody samples.
    """
    stride = 3 if _FAULT == "stride" else 2
    blockdata = unpack_uint32(struct[12:16])
    border_pointer = unpack_uint32(struct[8:12])
    border = [unpack_uint16(rom_read(border_pointer + i * 2, 2)) for i in range(4)]
    raw = rom_read(blockdata, width * height * stride)
    grid = {}
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * stride
            block = raw[offset] | (raw[offset + 1] << 8)
            if (block & 0x03FF) == 0x03FF:
                block = border[((x + 1) & 1) + (((y + 1) & 1) * 2)] | 0xC00
            grid[(x, y)] = block
    return grid


def collision_of(block: int) -> int:
    return (block & 0x0C00) >> 10


def metatile_of(block: int) -> int:
    return block & 0x03FF


def behaviour_name(struct: bytes, block: int) -> str:
    """The metatile BEHAVIOUR name, decoded through THIS layout's own tilesets (map.py:786-810)."""
    metatile = metatile_of(block)
    if metatile < 512:                                     # the emerald branch of map.py:787-796
        tileset_pointer, attribute_offset = unpack_uint32(struct[16:20]), metatile * 2
    else:
        tileset_pointer, attribute_offset = unpack_uint32(struct[20:24]), (metatile - 512) * 2
    attributes_pointer = unpack_uint32(rom_read(tileset_pointer + 0x10, 4))
    return _get_tile_type_name(unpack_uint16(rom_read(attributes_pointer + attribute_offset, 2)) & 0xFF)


def cracked_tiles(struct: bytes, grid: dict) -> set[tuple[int, int]]:
    """Tiles whose BEHAVIOUR is 'Cracked Floor'. ⛔ Behaviour, not a hardcoded metatile id — the id
    differs per tileset, and `probe_skypillar_clean_layout.py` had to pin one (0x236) by hand."""
    return {tile for tile, block in grid.items() if behaviour_name(struct, block) == "Cracked Floor"}


def bfs(grid: dict, src, dst=None, banned=frozenset()):
    """Step count to `dst`, or the reachable set when `dst is None`. Bounded by the grid itself."""
    if collision_of(grid.get(src, OFF_MAP)) != 0:
        return None
    seen, queue = {src}, deque([(src, 0)])
    while queue:
        (x, y), dist = queue.popleft()
        if dst is not None and (x, y) == dst:
            return dist
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in seen or nxt in banned:
                continue
            if collision_of(grid.get(nxt, OFF_MAP)) != 0:
                continue
            seen.add(nxt)
            queue.append((nxt, dist + 1))
    return None if dst is not None else seen


def resolve(map_name: str, layouts):
    """(default_index, default_struct, default_grid, clean_index, clean_struct, clean_grid, report)."""
    map_enum = getattr(MapRSE, map_name)
    width, height = get_map_data(map_enum, (0, 0)).map_size
    candidates = [row for row in layouts if (row[1], row[2]) == (width, height)]

    # ---- the DEFAULT is whichever candidate agrees with production ------------------------------
    # ⛔ IN-BOUNDS SAMPLE, ASSERTED. A sample that runs past the map reads production's BORDER block
    # and drags a perfectly good decode down — that exact bug cost a debugging cycle on 2026-09-01.
    sample = [(x, y) for x in range(1, width - 1) for y in range(1, height - 1)]
    production = {}
    for tile in sample:
        try:
            production[tile] = get_map_data(map_enum, tile).collision
        except Exception:
            continue
    best, best_rate, grids = None, -1.0, {}
    for index, w, h, struct in candidates:
        grids[index] = block_grid(struct, w, h)
        hits = sum(1 for tile, coll in production.items()
                   if collision_of(grids[index].get(tile, OFF_MAP)) == coll)
        rate = hits / max(1, len(production))
        if rate > best_rate:
            best, best_rate = (index, struct), rate
    default_index, default_struct = best
    default_grid = grids[default_index]

    # ---- identify the CLEAN twin -----------------------------------------------------------------
    # ⛔ AN EARLIER VERSION OF THIS TEST FOUND NOTHING, AND THE REASON IS ITSELF A FINDING. It asked
    # for a candidate whose METATILE diff was a subset of the default's cracked tiles — i.e. it
    # assumed "clean" means "the default with the cracks paved over". **It does not.** MEASURED
    # 2026-09-01: the CLEAN layouts differ from their defaults in COLLISION on ~7% of tiles, so they
    # are genuinely different floor plans, not a crack patch. (That 7% IS the hazard leg 4 faces:
    # it is where our planner thinks a tile is open and the story layout says wall.)
    #
    # The test that works, and why each half is needed:
    #   (a) the candidate's CRACKED set must be a SUBSET of the default's — that is what "clean"
    #       means, and it alone eliminates every other floor's layout;
    #   (b) among those, take the HIGHEST collision agreement — the twin of a floor still resembles
    #       that floor far more than any other map does.
    # ⛔ (b)'s margin can be THIN (2F: 93.4% vs 92.9%), so the assignment is NOT trusted on the
    # margin alone — `main()` validates it as a BIJECTION: six floors must select six DISTINCT
    # layouts, none of which is another floor's default. That constraint is what makes a 0.5%
    # margin safe, and it is checked, not assumed.
    default_cracks = cracked_tiles(default_struct, default_grid)
    rows, clean, best_agree = [], None, -1.0
    for index, w, h, struct in candidates:
        if index == default_index:
            continue
        candidate_cracks = cracked_tiles(struct, grids[index])
        subset = candidate_cracks <= default_cracks
        agree = sum(1 for t in default_grid
                    if collision_of(grids[index].get(t, OFF_MAP)) == collision_of(default_grid[t]))
        agree /= max(1, len(default_grid))
        if _FAULT == "anycand":
            subset = True                # drop the crack filter; agreement alone decides
        rows.append((index, len(candidate_cracks), subset, agree))
        if _FAULT == "noagree":
            # drop the AGREEMENT ranking: take the FIRST crack-subset candidate in index order
            if subset and clean is None:
                clean, best_agree = (index, struct, grids[index]), agree
        elif subset and agree > best_agree:
            clean, best_agree = (index, struct, grids[index]), agree
    return (default_index, default_struct, default_grid,
            clean, default_cracks, best_rate, rows, width, height)


def main() -> int:
    print("=" * 104)
    print("SKY PILLAR — THE CLEAN (STORY) LAYOUTS FOR ALL SIX FLOORS, FROM OUR OWN ROM (no network)")
    print("=" * 104)
    if _FAULT:
        print(f"‼ FAULT HOOK ACTIVE: POKEBOT_SPROM_FAULT={_FAULT} — this run is a SELF-TEST.")

    layouts = layout_structs()
    print(f"\nplausible layouts in `gMapLayouts`: {len(layouts)}")

    results = {}
    print("\n" + "-" * 104)
    print("PER-FLOOR RESOLUTION  (⛔ every candidate's diff size is shown, so the test is visible)")
    print("-" * 104)
    for name in CLIMB_FLOORS + NO_SWAP_FLOORS:
        if not hasattr(MapRSE, name):
            check(f"{name} exists in MapRSE", False, "NOT FOUND")
            continue
        (d_index, d_struct, d_grid, clean, d_cracks, rate, rows, w, h) = resolve(name, layouts)
        # ⛔ the agreement RATE is stored, not recomputed later: calling `resolve` twice would let
        # C1 grade a different run than the one whose numbers are printed above it.
        results[name] = (d_index, d_struct, d_grid, clean, d_cracks, w, h, rate)
        c_index = clean[0] if clean else None
        print(f"\n  {name}  ({w}x{h})")
        print(f"    DEFAULT = layout #{d_index}  (agreement with get_map_data {rate:.1%}); "
              f"cracked tiles in DEFAULT: {len(d_cracks)}")
        for index, n_cracks, subset, agree in rows:
            mark = "  <- CLEAN twin" if index == c_index else ""
            print(f"      candidate #{index:<4d} cracks={n_cracks:<3d} "
                  f"cracks-subset-of-default={str(subset):<5s} collision_agree={agree:.1%}{mark}")
        if clean:
            c_cracks = cracked_tiles(clean[1], clean[2])
            print(f"    ⇒ CLEAN = layout #{c_index}; cracked tiles REMAINING on CLEAN: "
                  f"{len(c_cracks)}  {sorted(c_cracks) if c_cracks else ''}")
        else:
            print("    ⇒ no CLEAN twin found")

    # ---- C1 ------------------------------------------------------------------------------------
    print("\n" + "-" * 104)
    print("CONTROL 1 — every floor's DEFAULT is identified by agreement with production")
    print("-" * 104)
    for name in CLIMB_FLOORS + NO_SWAP_FLOORS:
        if name not in results:
            continue
        d_index, d_struct, d_grid, clean, d_cracks, w, h, rate = results[name]
        check(f"{name}: DEFAULT #{d_index} agrees with get_map_data", rate >= 0.99, f"{rate:.1%}")

    # ---- C2 — THE ONE THAT LICENSES THE WHOLE PROBE ---------------------------------------------
    print("\n" + "-" * 104)
    print("CONTROL 2 — the ROM method must REPRODUCE the independent DECOMP method on 2F and 4F")
    print("-" * 104)
    print("  oracle: evidence/2026-08-24-skypillar-clean-reachability.txt:16-18")
    for name, expected in ORACLE_CLEAN_CRACKS.items():
        if name not in results or results[name][3] is None:
            check(f"{name}: CLEAN twin found at all", False, "no CLEAN twin")
            continue
        clean = results[name][3]
        got = cracked_tiles(clean[1], clean[2])
        check(f"{name}: CLEAN has {len(expected)} cracked tile(s), exactly {sorted(expected)}",
              got == expected, f"got {len(got)}: {sorted(got)}")

    # ---- C3 — the negative control ----------------------------------------------------------------
    print("\n" + "-" * 104)
    print("CONTROL 3 — NEGATIVE: the two maps that do NOT swap must have no CLEAN twin")
    print("-" * 104)
    for name in NO_SWAP_FLOORS:
        if name not in results:
            continue
        check(f"{name}: no CLEAN twin (it does not swap layouts)", results[name][3] is None,
              f"found #{results[name][3][0]}" if results[name][3] else "")

    # ---- C4 --------------------------------------------------------------------------------------
    print("\n" + "-" * 104)
    print("CONTROL 4 — DEFAULT and CLEAN must share both tilesets, or CLEAN's behaviour names lie")
    print("-" * 104)
    for name in CLIMB_FLOORS:
        if name not in results or results[name][3] is None:
            continue
        d_struct, clean = results[name][1], results[name][3]
        same = (unpack_uint32(d_struct[16:20]), unpack_uint32(d_struct[20:24])) == \
               (unpack_uint32(clean[1][16:20]), unpack_uint32(clean[1][20:24]))
        check(f"{name}: DEFAULT and CLEAN share both tilesets", same)

    # ---- C5 - THE CONSTRAINT THAT MAKES A THIN MARGIN SAFE ---------------------------------------
    print("")
    print("-" * 104)
    print("CONTROL 5 — the DEFAULT->CLEAN assignment must be a BIJECTION (six floors, six distinct")
    print("            layouts, none of them a DEFAULT). ⛔ 2F's winning margin is 0.5%; THIS is why")
    print("            that is safe, not the margin.")
    print("-" * 104)
    defaults = {results[n][0] for n in CLIMB_FLOORS if n in results}
    cleans = [results[n][3][0] for n in CLIMB_FLOORS if n in results and results[n][3]]
    print(f"  DEFAULT indices: {sorted(defaults)}")
    print(f"  CLEAN   indices: {sorted(cleans)}")
    check("every climb floor resolved a CLEAN twin", len(cleans) == len(CLIMB_FLOORS),
          f"{len(cleans)}/{len(CLIMB_FLOORS)}")
    check("the CLEAN twins are DISTINCT (no layout claimed by two floors)",
          len(set(cleans)) == len(cleans))
    check("no CLEAN twin is also some floor's DEFAULT", not (set(cleans) & defaults),
          f"overlap {sorted(set(cleans) & defaults)}" if set(cleans) & defaults else "")

    if FAILURES:
        print("\n‼ CONTROLS FAILED — every measurement below is UNTRUSTED. Do not act on it.")
        for f in FAILURES:
            print(f"    - {f}")
        return 1
    print("\n  ALL CONTROLS PASS.")

    # ---- THE MEASUREMENT LEG 4 NEEDS -------------------------------------------------------------
    print("\n" + "=" * 104)
    print("MEASUREMENT — DEFAULT vs CLEAN, per floor: what our planner gets WRONG on the story climb")
    print("=" * 104)
    print("  'we think OPEN / game says WALL' is the DANGEROUS direction: the planner routes into rock.")
    for name in CLIMB_FLOORS:
        if name not in results:
            continue
        d_index, d_struct, d_grid, clean, d_cracks, w, h, rate = results[name]
        if clean is None:
            print(f"\n  {name}: no CLEAN twin — the planner is CORRECT on this floor.")
            continue
        c_grid = clean[2]
        open_d_wall_c = sorted(t for t in d_grid
                               if collision_of(d_grid[t]) == 0 and collision_of(c_grid.get(t, OFF_MAP)) != 0)
        wall_d_open_c = sorted(t for t in d_grid
                               if collision_of(d_grid[t]) != 0 and collision_of(c_grid.get(t, OFF_MAP)) == 0)
        c_cracks = cracked_tiles(clean[1], c_grid)
        print(f"\n  {name}  (DEFAULT #{d_index} -> CLEAN #{clean[0]})")
        print(f"    ⛔ we think OPEN, the game says WALL : {len(open_d_wall_c)}  {open_d_wall_c if len(open_d_wall_c) <= 40 else '(too many to list)'}")
        print(f"    ✅ we think WALL, the game says open : {len(wall_d_open_c)}  {wall_d_open_c if len(wall_d_open_c) <= 40 else '(too many to list)'}")
        print(f"    cracked on DEFAULT {len(d_cracks)}  ->  cracked on CLEAN {len(c_cracks)}  {sorted(c_cracks)}")

    # ---- MEASUREMENT 2 — CAN THE BOT ACTUALLY WALK THE CLIMB, AND THE DESCENT? --------------------
    # ⛔ THE WHOLE POINT: a WALKING bot FALLS on entry to a cracked tile, so every leg below is
    # computed with the CLEAN layout's own cracks BANNED. A leg that reports NO PATH is a leg that
    # REQUIRES A DELIBERATE FALL — `calculate_path` can never propose one (it does not model
    # "Cracked Floor" at all), so it must be an explicit chapter step.
    # ‼ Coordinates are warp EVENT tiles from `evidence/2026-08-27-ch21-skypillar-probe.stdout.txt`
    # MEASUREMENT 1. Where the avatar RESTS after each warp is UNVERIFIED and is per-warp — only a
    # drive settles it, and this project has been bitten twice by assuming otherwise.
    print("")
    print("=" * 104)
    print("MEASUREMENT 2 — the ASCENT and DESCENT on the CLEAN layouts, with CRACKS BANNED")
    print("=" * 104)
    print("  A 'NO PATH' row is NOT a bug: it is where a DELIBERATE FALL is mandatory.")
    legs = [
        ("ASCENT ", "SKY_PILLAR_1F", (6, 13), (10, 1), "arrive from OUTSIDE -> up to 2F"),
        ("ASCENT ", "SKY_PILLAR_2F", (10, 1), (3, 1), "arrive from 1F -> up to 3F"),
        ("ASCENT ", "SKY_PILLAR_3F", (3, 1), (11, 1), "arrive from 2F -> up to 4F via (11,1)"),
        ("ASCENT ", "SKY_PILLAR_4F", (11, 1), (3, 1), "arrive from 3F -> up to 5F  <-- the FALL leg"),
        ("ASCENT ", "SKY_PILLAR_5F", (3, 1), (10, 1), "arrive from 4F -> up to TOP"),
        ("DESCENT", "SKY_PILLAR_5F", (10, 1), (3, 1), "arrive from TOP -> down to 4F"),
        ("DESCENT", "SKY_PILLAR_4F", (3, 1), (7, 1), "arrive from 5F -> down to 3F via (7,1)"),
        ("DESCENT", "SKY_PILLAR_4F", (3, 1), (11, 1), "arrive from 5F -> down to 3F via (11,1)"),
        ("DESCENT", "SKY_PILLAR_3F", (7, 1), (3, 1), "arrive from 4F(7,1) -> down to 2F"),
        ("DESCENT", "SKY_PILLAR_3F", (11, 1), (3, 1), "arrive from 4F(11,1) -> down to 2F"),
        ("DESCENT", "SKY_PILLAR_2F", (3, 1), (10, 1), "arrive from 3F -> down to 1F"),
        ("DESCENT", "SKY_PILLAR_1F", (10, 1), (6, 13), "arrive from 2F -> down to OUTSIDE"),
    ]
    for kind, name, src, dst, note in legs:
        if name not in results or results[name][3] is None:
            print(f"  {kind}  {name:<16} {src} -> {dst}   (no CLEAN layout resolved)")
            continue
        clean = results[name][3]
        cracks = cracked_tiles(clean[1], clean[2])
        walk = bfs(clean[2], src, dst, banned=cracks)
        free = bfs(clean[2], src, dst)
        verdict = f"{walk} steps" if walk is not None else "⛔ NO PATH (a FALL is required)"
        extra = "" if walk == free else f"   [ignoring cracks: {free}]"
        print(f"  {kind}  {name:<16} {str(src):<8} -> {str(dst):<8} {verdict}{extra}   {note}")

    # ---- MEASUREMENT 3 — CAN THE BOT REACH THE TILE IT MUST FALL THROUGH? ------------------------
    # A fall is an EXPLICIT step onto a cracked tile, so what matters is whether the bot can stand
    # NEXT TO one and step in. Cracks are banned as through-tiles (a walking bot falls on entry), so
    # the question is: with cracks banned, is any NEIGHBOUR of the launch tile reachable?
    print("")
    print("=" * 104)
    print("MEASUREMENT 3 — the DELIBERATE FALLS: can the bot stand beside the tile and step in?")
    print("=" * 104)
    falls = [
        ("ASCENT ", "SKY_PILLAR_4F", (11, 1), [(6, 4), (7, 4)],
         "the atlas's ascent fall; ⛔ (9,4) is a DECOY - it drops into 3F's MAIN region, not the pocket"),
        ("ASCENT ", "SKY_PILLAR_4F", (11, 1), [(9, 4)],
         "the DECOY, measured here only so its reachability is not mistaken for correctness"),
        ("DESCENT", "SKY_PILLAR_4F", (3, 1), [(0, 3), (1, 3)],
         "the atlas's descent fall, needed because 3F(7,1) cannot reach 3F(3,1)"),
    ]
    for kind, name, src, targets, note in falls:
        if name not in results or results[name][3] is None:
            continue
        clean = results[name][3]
        grid, cracks = clean[2], cracked_tiles(clean[1], clean[2])
        reachable = bfs(grid, src, None, banned=cracks) or set()
        for target in targets:
            neighbours = [(target[0] + dx, target[1] + dy)
                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            standable = [t for t in neighbours if t in reachable]
            is_crack = target in cracks
            print(f"  {kind}  {name} from {src}: launch tile {target} "
                  f"is_cracked={is_crack}  standable neighbours={standable or 'NONE'}")
        print(f"          {note}")

    print("")
    print("=" * 104)
    print("READ NARROWLY. This is a STATIC comparison of ROM layouts. It shows WHICH layout the")
    print("story runs on and where our planner disagrees with it. It does NOT prove which layout is")
    print("loaded at any given moment — only a live read of `gBackupMapLayout` does that, and")
    print("`sootopolis._live_wall_tiles()` is the instrument for it.")
    print("=" * 104)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
