"""§Ch21 LEG 3 PRE-BUILD GATE — does ROUTE 131 really swap its layout, and does the planned route
walk into live rock? Answered from OUR OWN ROM, offline, with no network.

‼ WHY THIS EXISTS. `Route131_OnTransition` calls `setmaplayoutindex LAYOUT_ROUTE131_SKY_PILLAR`
**unconditionally**, while `map_path` plans on the ROM map header's DEFAULT layout. So on the
approach map the planner and the avatar are looking at two different maps. A recon pass put the
divergence at "116 tiles open-in-default are walls live" and concluded that the documented 35-wp
fallback **walks into solid rock** — but every byte of that rested on decomp blobs fetched over
HTTP, and this environment is known to silently corrupt binary fetches (playbook §N).

⛔⛔ AND THE SET MATTERS MORE THAN THE NUMBER. On 2026-08-27 a probe blocked the POST-GAME crack set,
reported "no crack-free route", and that shipped as a BLOCKER — while the story runs on a layout
where 33 of those 38 tiles are solid ground. The measurement was right and the QUESTION was wrong.
So every number below names which set it belongs to:

    SET A = the ROM map header's DEFAULT layout for ROUTE131.
            This is what `get_map_data()` / `PathMap.tiles` / `calculate_path` read. `map.py:751`
            dereferences `self._map_header[:4]`, and that header comes from the static ROM
            `gMapGroups` table (`map.py:1774-1789`) — never from the live `gMapHeader`.
    SET B = the layout the game actually loads at runtime on ROUTE131.
            `setmaplayoutindex` writes `gSaveBlock1Ptr->mapLayoutId` and the live `gMapHeader`
            only; it never touches the ROM table we read.

⇒ THE PLANNER IS NOT WRONG, IT IS LOOKING AT SET A. The question is only ever: does a route
computed on SET A stay walkable on SET B?

--------------------------------------------------------------------------------------------
HOW SET B IS FOUND WITHOUT TRUSTING A NETWORK FETCH
--------------------------------------------------------------------------------------------
`gMapLayouts` resolves in our ROM (verified). It is an array of pointers to 24-byte layout
structs; `map.py:746-755,851` gives the field offsets we reuse here (width [0:4], height [4:8],
blockdata [12:16]). So: enumerate every layout, keep the ones with ROUTE131's exact dimensions,
and identify SET A by matching production's own `get_map_data` collision readings. Whatever other
same-sized layout exists is the swap candidate, and it is reported — never assumed.

⛔ NON-CIRCULARITY. The candidate is NOT selected by looking for the tiles the recon predicted.
It is selected by dimensions alone, and then the predicted tiles are CHECKED against it. If the
recon were wrong, this probe would say so rather than confirm itself.

--------------------------------------------------------------------------------------------
CONTROLS (a probe that finds nothing is indistinguishable from one that cannot see)
--------------------------------------------------------------------------------------------
C1  the layout scan must find ROUTE131's own default layout and agree with `get_map_data`
    collision on a sample of tiles — an expected AGREEMENT RATE, not merely "found something".
C2  the SET A decode must reproduce THREE numbers production already measured independently:
    `(40,20)->(28,15)` = 35 waypoints, `(40,19)->(28,15)` = 16, and `(40,19)` reading as a WALL.
    ‼ This is the integrity check that a length check cannot give: a corrupted or mis-strided
    blob cannot reproduce three separate production numbers by accident.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch21_route131_live.py
Self-test:  POKEBOT_R131_FAULT=stride  ... same ...   # mis-strides the decode; C2 must go RED
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.memory import read_symbol, unpack_uint32

ROUTE131 = MapRSE.ROUTE131

#: Production's own measurements, taken by `calculate_path` on 2026-08-27/28. C2 requires the
#: SET A decode to reproduce all three. ⛔ Do not "fix" these to match a decode — they are the
#: oracle, and a mismatch means the DECODE is wrong.
PROD_35 = 35          # (40,20) -> (28,15), waypoints
PROD_16 = 16          # (40,19) -> (28,15), waypoints
PROD_BLIND = (40, 19)  # reads 'Normal' / collision 1 in SET A — which is why step 6 must be blind

#: The route's ROUTE131 legs, as measured. Intersecting these with the divergence set is the
#: whole point of the gate.
STAGING = (28, 15)
SWIM_END = (40, 20)
DOOR = (36, 6)

_FAULT = _os.environ.get("POKEBOT_R131_FAULT", "").strip()


def rom_read(address: int, length: int) -> bytes:
    return context.emulator.read_bytes(address, length)


def layout_structs(max_layouts: int = 1024) -> list[tuple[int, int, int, int]]:
    """(index, width, height, blockdata_pointer) for every plausible layout in `gMapLayouts`."""
    table = read_symbol("gMapLayouts", 0, 4 * max_layouts)
    out = []
    for index in range(max_layouts):
        pointer = unpack_uint32(table[index * 4:index * 4 + 4])
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
        out.append((index, width, height, blockdata))
    return out


def collision_grid(blockdata: int, width: int, height: int) -> dict[tuple[int, int], int]:
    """collision = (block >> 10) & 3, exactly as `map.py` decodes it."""
    stride = 3 if _FAULT == "stride" else 2      # ‼ the fault hook mis-strides the decode
    raw = rom_read(blockdata, width * height * stride)
    grid = {}
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * stride
            value = raw[offset] | (raw[offset + 1] << 8)
            grid[(x, y)] = (value >> 10) & 3
    return grid


def bfs(grid: dict[tuple[int, int], int], src, dst, banned=frozenset()) -> int | None:
    """Shortest 4-neighbour step count over collision-0 tiles, or None."""
    if grid.get(src, 1) != 0:
        seen = {src}          # allow starting on a blocked tile (the blind-step case)
    else:
        seen = {src}
    queue = deque([(src, 0)])
    while queue:
        (x, y), dist = queue.popleft()
        if (x, y) == dst:
            return dist
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in seen or nxt in banned:
                continue
            if grid.get(nxt, 1) != 0:
                continue
            seen.add(nxt)
            queue.append((nxt, dist + 1))
    return None


def main() -> int:
    print("=" * 94)
    print("§Ch21 LEG 3 PRE-BUILD GATE — ROUTE 131, SET A vs SET B, from OUR OWN ROM (no network)")
    print("=" * 94)

    width, height = get_map_data(ROUTE131, (0, 0)).map_size
    print(f"\nROUTE131 map_size = {(width, height)}")

    layouts = layout_structs()
    same_size = [row for row in layouts if row[1] == width and row[2] == height]
    print(f"layouts in `gMapLayouts` with plausible headers : {len(layouts)}")
    print(f"of those, EXACTLY ROUTE131's dimensions          : {len(same_size)}  "
          f"(indices {[r[0] for r in same_size]})")
    print("  ⛔ candidates are selected by DIMENSIONS ALONE — never by looking for the tiles the")
    print("     recon predicted. The prediction is CHECKED against them below, not used to find them.")

    # ---------------------------------------------------------------- C1
    print("\n" + "-" * 94)
    print("CONTROL 1 — which same-sized layout is SET A? (agreement with production's own reads)")
    print("-" * 94)
    sample = [(x, y) for y in range(0, height, 3) for x in range(0, width, 3)]
    prod = {}
    for tile in sample:
        try:
            prod[tile] = getattr(get_map_data(ROUTE131, tile), "collision", None)
        except Exception:
            pass
    best, best_rate = None, -1.0
    for index, w, h, blockdata in same_size:
        grid = collision_grid(blockdata, w, h)
        hits = sum(1 for t, c in prod.items() if c is not None and grid.get(t) == c)
        rate = hits / max(1, len(prod))
        print(f"  layout #{index:<4d} agreement with get_map_data over {len(prod)} sampled tiles: "
              f"{hits}/{len(prod)} = {rate:.1%}")
        if rate > best_rate:
            best, best_rate = (index, w, h, blockdata), rate
    c1_ok = best_rate >= 0.99
    print(f"  ⇒ SET A = layout #{best[0]} at {best_rate:.1%}  {'PASS' if c1_ok else 'FAIL'}")

    set_a = collision_grid(best[3], best[1], best[2])

    # ---------------------------------------------------------------- C2
    print("\n" + "-" * 94)
    print("CONTROL 2 — the SET A decode must reproduce THREE independent production numbers")
    print("-" * 94)
    d35 = bfs(set_a, SWIM_END, STAGING)
    d16 = bfs(set_a, PROD_BLIND, STAGING)
    blind_is_wall = set_a.get(PROD_BLIND) != 0
    c2a, c2b, c2c = d35 == PROD_35, d16 == PROD_16, blind_is_wall
    print(f"  (40,20)->(28,15) : decode {d35}  production {PROD_35}   {'MATCH' if c2a else 'MISMATCH'}")
    print(f"  (40,19)->(28,15) : decode {d16}  production {PROD_16}   {'MATCH' if c2b else 'MISMATCH'}")
    print(f"  (40,19) is a WALL in SET A : {blind_is_wall}            "
          f"{'MATCH' if c2c else 'MISMATCH'}")
    c2_ok = c2a and c2b and c2c
    print(f"  ⇒ {'PASS — the decode agrees with the emulator oracle in three places' if c2_ok else 'FAIL'}")

    if not (c1_ok and c2_ok):
        print("\n‼ CONTROLS FAILED — every measurement below is UNTRUSTED. Do not act on it.")
        return 1
    print("\n  ALL CONTROLS PASS.")

    # ------------------------------------------------------- SET B AND THE DIVERGENCE
    print("\n" + "-" * 94)
    print("MEASUREMENT 1 — SET B, and the divergence, per direction")
    print("-" * 94)
    others = [row for row in same_size if row[0] != best[0]]
    if not others:
        print("  ‼ NO other same-sized layout exists in this ROM. The swap premise is NOT")
        print("    confirmed here, and leg 3 must not be built on it. Report and stop.")
        return 1
    for index, w, h, blockdata in others:
        set_b = collision_grid(blockdata, w, h)
        open_a_wall_b = sorted(t for t in set_a if set_a[t] == 0 and set_b.get(t, 1) != 0)
        wall_a_open_b = sorted(t for t in set_a if set_a[t] != 0 and set_b.get(t, 1) == 0)
        door_open = set_b.get(DOOR) == 0
        print(f"\n  candidate layout #{index}:")
        print(f"    open in A, WALL in B (the dangerous direction) : {len(open_a_wall_b)}")
        print(f"    WALL in A, open in B (the blind-step direction): {len(wall_a_open_b)}")
        print(f"    the blind step {PROD_BLIND} is open in B        : "
              f"{set_b.get(PROD_BLIND) == 0}")
        print(f"    the tower door {DOOR} is open in B             : {door_open}")
        if set_b.get(PROD_BLIND) != 0:
            print("    ⇒ this candidate does NOT explain the blind step; it is probably not SET B.")
            continue

        # ------------------------------------------------ THE PAYOFF: does the route hit rock?
        bad = set(open_a_wall_b)
        print(f"\n    ROUTE AUDIT against this candidate (the {len(bad)} dangerous tiles):")
        for label, src, dst in [("swim end -> staging, from (40,20) [the FALLBACK]", SWIM_END, STAGING),
                                ("blind step -> staging, from (40,19) [the ROUTE]", PROD_BLIND, STAGING)]:
            free = bfs(set_a, src, dst)
            avoid = bfs(set_a, src, dst, banned=bad)
            if free is None:
                print(f"      {label}: SET A has no route at all")
                continue
            forced = avoid is None or avoid > free
            verdict = ("‼ FORCED THROUGH LIVE ROCK — no tie-break can dodge it"
                       if forced else "clean: an equal-cost live-safe route exists")
            print(f"      {label}")
            print(f"        SET A distance {free}; avoiding the dangerous set {avoid}  -> {verdict}")

        live_to_door = bfs(set_b, STAGING, DOOR)
        a_to_door = bfs(set_a, STAGING, DOOR)
        print(f"\n    (28,15) -> the door {DOOR}: SET A {a_to_door}   SET B {live_to_door}")
        print("      ⇒ if SET A is None and SET B is a number, the final approach MUST be hand-walked:")
        print("        the planner cannot see the door at all, and any call it makes there is unsafe.")

    print("\n" + "=" * 94)
    print("READ NARROWLY. This is a STATIC comparison of two ROM layouts. It does NOT prove which")
    print("one ROUTE131 loads at runtime — `setmaplayoutindex` writes only the live `gMapHeader`,")
    print("which cannot be read without standing on the map. ⛔ The first leg-3 drive must carry the")
    print("`CH21_LAYOUT_PROBE` reading on ROUTE131 and settle that premise as a byproduct.")
    print("=" * 94)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
