"""Ground-truth tile dump of MOSSDEEP_CITY_GYM — every metatile behaviour on the floor.

WHY: no route plans from the gym entrance (6,34) to Tate & Liza at (23,7)/(24,7). Before theorising
about the warp graph again, read the map the way the BOT reads it: collision, elevation and the
metatile behaviour NAME for every tile in x=0..26, y=0..36. If there is anything exotic on that
floor (ice/slide, arrows, one-way, directional blockers, a second warp flavour), it shows up here as
a distinct behaviour name — not as a guess.

‼ The save MUST stand INSIDE the gym: `saves/in_mossdeep_gym.ss1`. Object templates and the map's
metatile data only resolve for the LOADED map, so probing from elsewhere yields garbage.

Read-only. Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gym_tiledump.py
"""

import pathlib
import sys
from collections import Counter, defaultdict

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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "in_mossdeep_gym.ss1"
GYM = MapRSE.MOSSDEEP_CITY_GYM
X0, X1, Y0, Y1 = 0, 26, 0, 36

line = "=" * 100

context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

print(line)
print("MOSSDEEP_CITY_GYM — tile-by-tile ground truth (save stands inside the gym)")
print(line)

try:
    player = get_map_data(GYM, (0, 0))
    print(f"map size: {player.map_size}   (probing x={X0}..{X1}, y={Y0}..{Y1})")
except Exception as exc:  # noqa: BLE001 — informational only
    print(f"map size unreadable: {exc!r}")

# ------------------------------------------------------------------ read the whole rectangle once
tiles: dict = {}
errors: dict = {}
for y in range(Y0, Y1 + 1):
    for x in range(X0, X1 + 1):
        try:
            t = get_map_data(GYM, (x, y))
            tiles[(x, y)] = {
                "collision": t.collision,
                "elevation": t.elevation,
                "tile_type": t.tile_type,
                "has_encounters": t.has_encounters,
            }
        except Exception as exc:  # noqa: BLE001 — off-map reads are recorded, not fatal
            errors[(x, y)] = repr(exc)

warps = {}
try:
    for index, warp in enumerate(get_map_data(GYM, (0, 0)).warps):
        warps[tuple(warp.local_coordinates)] = index
except Exception as exc:  # noqa: BLE001
    print(f"warp list unreadable: {exc!r}")

print(f"\ntiles read: {len(tiles)}   unreadable: {len(errors)}")
if errors:
    sample = list(errors.items())[:3]
    for coord, err in sample:
        print(f"   unreadable {coord}: {err}")

print(f"\n{len(warps)} warp events: {sorted((i, c) for c, i in warps.items())}")

# ------------------------------------------------------------------ 1. distinct behaviours
print("\n" + line)
print("1. DISTINCT metatile behaviours in x=0..26, y=0..36")
print(line)

counts = Counter(v["tile_type"] for v in tiles.values())
examples = defaultdict(list)
for coord in sorted(tiles, key=lambda c: (c[1], c[0])):
    beh = tiles[coord]["tile_type"]
    if len(examples[beh]) < 6:
        examples[beh].append(coord)

# collision/elevation spread per behaviour makes "is this walkable?" answerable at a glance
print(f"\n{'behaviour':<34}{'count':>7}   {'collisions':<14}{'elevations':<16}examples")
print("-" * 100)
for beh, n in counts.most_common():
    cols = sorted({tiles[c]["collision"] for c in tiles if tiles[c]["tile_type"] == beh})
    elev = sorted({tiles[c]["elevation"] for c in tiles if tiles[c]["tile_type"] == beh})
    print(f"{beh:<34}{n:>7}   {str(cols):<14}{str(elev):<16}{examples[beh]}")

enc = [c for c, v in tiles.items() if v["has_encounters"]]
print(f"\ntiles with has_encounters: {len(enc)}  {sorted(enc)[:10]}")

# ------------------------------------------------------------------ 2. the named tiles
print("\n" + line)
print("2. NAMED TILES of interest")
print(line)
NAMED = [(11, 5), (12, 34), (11, 34), (12, 33), (13, 33), (12, 35),
         (11, 3), (8, 12), (13, 32), (21, 10)]
print(f"\n{'tile':<12}{'collision':>10}{'elev':>7}   {'behaviour':<32}{'encounters':<12}warp?")
print("-" * 100)
for coord in NAMED:
    v = tiles.get(coord)
    if v is None:
        print(f"{str(coord):<12}{'UNREADABLE — ' + errors.get(coord, 'out of range')}")
        continue
    w = f"warp #{warps[coord]}" if coord in warps else ""
    print(f"{str(coord):<12}{v['collision']:>10}{v['elevation']:>7}   "
          f"{v['tile_type']:<32}{str(v['has_encounters']):<12}{w}")

# also dump the goal / entrance tiles, since they are the whole point
print("\n  (context: entrance + Tate & Liza tiles)")
for coord in [(6, 34), (23, 7), (24, 7), (23, 8), (24, 8)]:
    v = tiles.get(coord)
    if v is None:
        print(f"{str(coord):<12}UNREADABLE")
        continue
    w = f"warp #{warps[coord]}" if coord in warps else ""
    print(f"{str(coord):<12}{v['collision']:>10}{v['elevation']:>7}   "
          f"{v['tile_type']:<32}{str(v['has_encounters']):<12}{w}")

# ------------------------------------------------------------------ 3. ASCII map
print("\n" + line)
print("3. ASCII MAP")
print(line)

# Stable single-char code per NON-normal, NON-warp behaviour, assigned in first-seen order so the
# legend below is always complete for whatever the map actually contains.
SPECIAL_CHARS = "abcdefghijklmnopqrstuvwxyz"
special_map: dict = {}
for coord in sorted(tiles, key=lambda c: (c[1], c[0])):
    beh = tiles[coord]["tile_type"]
    if beh == "Normal" or "Warp" in beh or "Door" in beh or "Stairs" in beh or "Escalator" in beh:
        continue
    if beh not in special_map:
        special_map[beh] = SPECIAL_CHARS[len(special_map) % len(SPECIAL_CHARS)]


def char_for(coord) -> str:
    v = tiles.get(coord)
    if v is None:
        return " "
    beh = v["tile_type"]
    walk = v["collision"] == 0
    if coord in warps:
        return "W" if walk else "w"
    if beh in special_map:
        return special_map[beh] if walk else special_map[beh].upper()
    if "Warp" in beh or "Door" in beh or "Stairs" in beh or "Escalator" in beh:
        return "*" if walk else "+"
    return "." if walk else "#"


header = "     " + "".join(str(x % 10) for x in range(X0, X1 + 1))
print("\n" + header)
for y in range(Y0, Y1 + 1):
    row = "".join(char_for((x, y)) for x in range(X0, X1 + 1))
    print(f"{y:>4} {row}")
print(header)

print("\nLEGEND")
print("  .  walkable floor, behaviour 'Normal'")
print("  #  BLOCKED (collision != 0), behaviour 'Normal'")
print("  W  warp EVENT tile, walkable        w  warp EVENT tile, blocked")
print("  *  warp-ish BEHAVIOUR (Warp/Door/Stairs/Escalator) but no warp event, walkable")
print("  +  same, blocked")
if special_map:
    print("  -- non-Normal behaviours (lower-case = walkable, UPPER = blocked) --")
    for beh, ch in special_map.items():
        n = counts[beh]
        print(f"  {ch}/{ch.upper()}  {beh}   ({n} tile(s), e.g. {examples[beh][:4]})")
else:
    print("  (no non-Normal, non-warp behaviours found anywhere in the rectangle)")

# ------------------------------------------------------------------ elevation map (cheap, matters)
print("\n" + line)
print("3b. ELEVATION MAP (hex digit per tile; '#' = blocked, ' ' = unreadable)")
print(line)
print("\n" + header)
for y in range(Y0, Y1 + 1):
    row = ""
    for x in range(X0, X1 + 1):
        v = tiles.get((x, y))
        if v is None:
            row += " "
        elif v["collision"] != 0:
            row += "#"
        else:
            row += format(v["elevation"], "x") if v["elevation"] < 16 else "?"
    print(f"{y:>4} {row}")
print(header)

# ------------------------------------------------------------------ 4. collision values + the goal
print("\n" + line)
print("4. COLLISION VALUE HISTOGRAM (anything != 0 blocks; >1 is worth noticing)")
print(line)
col_counts = Counter(v["collision"] for v in tiles.values())
for c, n in sorted(col_counts.items()):
    ex = [k for k in sorted(tiles, key=lambda t: (t[1], t[0])) if tiles[k]["collision"] == c][:6]
    print(f"  collision={c}: {n:>5} tile(s)   e.g. {ex}")

print("\n  GOAL CHECK — are the Tate & Liza tiles even standable?")
for coord in [(23, 7), (24, 7)]:
    v = tiles[coord]
    nbrs = [(coord[0] + dx, coord[1] + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
    walk_nbrs = [n for n in nbrs if tiles.get(n) and tiles[n]["collision"] == 0]
    print(f"    {coord}: collision={v['collision']} -> "
          f"{'STANDABLE' if v['collision'] == 0 else 'NOT STANDABLE'};"
          f" walkable neighbours = {walk_nbrs}")

print("\n" + line)
print("done — read-only dump, nothing written")
print(line)
