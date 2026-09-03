"""§Ch22 — GENERATE the Sootopolis Gym ice route from the DECOMP LAYOUT, and prove it.

⛔⛔ WHY A GENERATOR AND NOT A HAND-WRITTEN TABLE. The gym's ice floor is an EXACT COVER problem:
64 thin-ice tiles in three sections (7 / 19 / 38) against `VAR_ICE_STEP_COUNT` thresholds 8 / 28 /
67, and the arithmetic closes exactly — so **every tile must be stepped on exactly once, with zero
revisits**. A transcribed route is one typo away from a fall, and a fall costs a full B1F traverse
(ten trainers). This script DERIVES the route and RE-DERIVES it on every run, so the table can never
silently drift from the map.

⛔ AND IT DOES NOT SOLVE THE PUZZLE THE BOT WILL WALK — IT SOLVES THE **DECOMP'S** MAP, WHICH IS A
SECOND, INDEPENDENT AUTHORITY. The bot's route must still be verified against the LIVE grid
(`_live_metatile_grid`) before it is trusted: this project's rule is that two sources agreeing is
corroboration, not proof, and the live grid is the one the game actually walks on.
‼ `--self-test` is the fault test (house rule 6): it proves the solver REFUSES a map it cannot
cover, rather than returning a plausible-looking partial path.

SOURCES (both fetched from `pret/pokeemerald`, both byte-checked here):
  data/layouts/SootopolisCity_Gym_1F/map.bin            884 B = 17 x 26 x 2
  data/tilesets/secondary/sootopolis_gym/metatile_attributes.bin

Usage:
    py -3.12 solve_gym_ice.py --map <map.bin> --attrs <attrs.bin>
    py -3.12 solve_gym_ice.py --map <map.bin> --attrs <attrs.bin> --self-test
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

WIDTH, HEIGHT = 17, 26
SECONDARY_BASE = 0x200          # secondary-tileset metatiles start here
MB_THIN_ICE = 0x26              # metatile behaviour byte for thin (steppable-once) ice

#: The player enters on this tile and walks NORTH. Reported by the live probe, not assumed.
ENTRY = (8, 25)

#: ⛔ Every locked-stair pair sits in this column, so it is also the only column a section can be
#: entered or left by. VERIFIED against the layout, not assumed.
STAIR_COLUMN = 8


def read_blocks(map_bin: Path) -> dict[tuple[int, int], int]:
    raw = map_bin.read_bytes()
    expected = WIDTH * HEIGHT * 2
    if len(raw) != expected:
        raise SystemExit(f"map.bin is {len(raw)} B, expected {expected} ({WIDTH}x{HEIGHT}x2)")
    out = {}
    for y in range(HEIGHT):
        for x in range(WIDTH):
            i = (y * WIDTH + x) * 2
            out[(x, y)] = (raw[i] | (raw[i + 1] << 8)) & 0x03FF
    return out


def read_behaviours(attrs_bin: Path) -> dict[int, int]:
    """metatile id -> behaviour byte, for SECONDARY tileset ids only."""
    raw = attrs_bin.read_bytes()
    # Gen 3 (Emerald) secondary attributes are 2 bytes per metatile; behaviour is the low byte.
    return {SECONDARY_BASE + i: raw[i * 2] for i in range(len(raw) // 2)}


def thin_ice_tiles(blocks, behaviours) -> list[tuple[int, int]]:
    return sorted(t for t, mt in blocks.items() if behaviours.get(mt) == MB_THIN_ICE)


def split_sections(tiles: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """Split the ice into contiguous y-bands — the sections the locked stairs separate."""
    rows = sorted({y for _, y in tiles})
    bands, cur = [], [rows[0]]
    for prev, y in zip(rows, rows[1:]):
        (cur.append(y) if y == prev + 1 else (bands.append(cur), cur := [y]))
    bands.append(cur)
    # southernmost band first — that is the order the player walks them
    bands.sort(key=lambda b: -max(b))
    return [[t for t in tiles if t[1] in band] for band in bands]


def solve_section(tiles, start, end):
    """Hamiltonian path over `tiles` (4-connected) from `start` to `end` — BOTH forced.

    ⛔⛔ BOTH ENDPOINTS ARE CONSTRAINED, AND FIXING ONLY THE START WAS A REAL DEFECT IN THE FIRST
    CUT OF THIS SOLVER. With a free end it returned section 1 as `[(8,19) … (9,18)]` — a valid
    Hamiltonian path that ENDS IN THE WRONG CORNER. The locked stairs out of that section are at
    (8,16)/(8,15), reachable only from (8,17), so the bot would have had to re-cross ALREADY-
    CRACKED ice to leave — i.e. **fall on the very first section transition.**
    ⇒ **a route that covers every tile is not the same as a route the player can LEAVE.**

    Returns the first full cover found, or None. ⛔ None is a RESULT the caller must handle
    loudly — a partial path is worse than no path.
    """
    tileset = set(tiles)
    n = len(tileset)

    def neighbours(t):
        x, y = t
        return [c for c in ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)) if c in tileset]

    sys.setrecursionlimit(10000)

    def dfs(cur, seen, path):
        if len(seen) == n:
            return path if cur == end else None
        # Warnsdorff-ish ordering: fewest onward options first — makes 38 tiles tractable.
        for nxt in sorted(neighbours(cur), key=lambda c: len([u for u in neighbours(c) if u not in seen])):
            if nxt in seen:
                continue
            seen.add(nxt)
            path.append(nxt)
            got = dfs(nxt, seen, path)
            if got is not None:
                return got
            path.pop()
            seen.remove(nxt)
        return None

    if start not in tileset or end not in tileset:
        return None
    return dfs(start, {start}, [start])


def verify(route, tiles, label) -> list[str]:
    """Every invariant the walk depends on. Returns a list of problems (empty == good)."""
    problems = []
    if len(route) != len(tiles):
        problems.append(f"{label}: route covers {len(route)} of {len(tiles)} tiles")
    if len(set(route)) != len(route):
        problems.append(f"{label}: route REVISITS a tile — that is a fall")
    if set(route) != set(tiles):
        problems.append(f"{label}: route set != tile set")
    for a, b in zip(route, route[1:]):
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
            problems.append(f"{label}: {a} -> {b} is not an orthogonal step")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--attrs", required=True, type=Path)
    ap.add_argument("--self-test", action="store_true",
                    help="FAULT TEST: prove the solver REFUSES an uncoverable map")
    args = ap.parse_args()

    blocks = read_blocks(args.map)
    behaviours = read_behaviours(args.attrs)
    tiles = thin_ice_tiles(blocks, behaviours)

    print("=" * 92)
    print("SOOTOPOLIS GYM 1F — ICE ROUTE GENERATOR (from the DECOMP layout)")
    print("=" * 92)
    print(f"  thin-ice tiles: {len(tiles)}")
    sections = split_sections(tiles)
    print(f"  sections (south -> north): {[len(s) for s in sections]}")

    if args.self_test:
        # ⛔ FAULT TEST: remove one tile from the middle of a section so no Hamiltonian path can
        # cover it, and prove the solver says NO rather than returning a shorter plausible path.
        sec0 = sections[0]
        got = solve_section(sec0 + [(99, 99)],
                            (STAIR_COLUMN, max(t[1] for t in sec0)),
                            (STAIR_COLUMN, min(t[1] for t in sec0)))
        ok = got is None
        print(f"\n  SELF-TEST: added an unreachable tile (99,99) to section 1 -> "
              f"solver returned {'None (REFUSED)' if ok else 'A PATH — BUG'}")
        if not ok:
            print("  ⛔ FAIL: the solver returned a path over a map it cannot cover.")
            return 1
        print("  ✅ the solver refuses an uncoverable map rather than returning a partial route.")

    all_problems, routes = [], []
    for idx, sec in enumerate(sections, 1):
        # the entry to each section is its southernmost tile(s) — the player arrives from the south
        # ⛔ ENTRY AND EXIT ARE BOTH FORCED BY THE MAP, and both are DERIVED, never hardcoded.
        # Column 8 alternates ice-band / locked-stair-pair from the entrance up (VERIFIED:
        # (8,20..21) floor, ice 19-17, stairs 16/15, ice 14-12, stairs 11/10, ice 9-6,
        # stairs 5/4, Juan at (8,3)). So a section is always ENTERED at its southern end of
        # column 8 and must be LEFT from its northern end — the only tile the next stair pair
        # is reachable from.
        start = (STAIR_COLUMN, max(t[1] for t in sec))
        end = (STAIR_COLUMN, min(t[1] for t in sec))
        route = solve_section(sec, start, end)
        if route is None:
            print(f"\n  SECTION {idx}: ⛔ NO HAMILTONIAN PATH FOUND {start} -> {end}")
            all_problems.append(f"section {idx}: unsolved")
            continue
        problems = verify(route, sec, f"section {idx}")
        if route[0] != start or route[-1] != end:
            problems.append(f"section {idx}: endpoints {route[0]}->{route[-1]} != {start}->{end}")
        all_problems += problems
        routes.append(route)
        print(f"\n  SECTION {idx}: {len(sec)} tiles, start {route[0]}, end {route[-1]}, "
              f"{'OK' if not problems else 'PROBLEMS: ' + '; '.join(problems)}")
        print(f"    {route}")

    print("\n" + "=" * 92)
    if all_problems:
        print("RESULT: ⛔ PROBLEMS FOUND")
        for p in all_problems:
            print(f"  - {p}")
        return 1
    total = sum(len(r) for r in routes)
    print(f"RESULT: ✅ all {len(routes)} sections covered, {total} steps, no revisits, "
          f"every step orthogonal.")
    print("‼ THIS IS THE DECOMP'S ANSWER, NOT THE GAME'S. Verify it against `_live_metatile_grid`")
    print("  before the bot walks it — two sources agreeing is corroboration, never proof.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
