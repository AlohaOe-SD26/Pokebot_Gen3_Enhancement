"""KI-59 — MEASURE the `Impassable *` tiles the pathfinder mis-models, before fixing anything.

`#24-impassabledirs`. Everything printed here is read from OUR OWN ROM/map data
(`modules.map.get_map_data`, `modules.map.get_map_all_tiles`) — nothing from recall, nothing
from the issue write-up.

WHY THIS EXISTS
  KI-59 says `modules/map_path.py`'s `Impassable *` branch is inverted. That branch is in SHARED
  pathfinding code used by every bot mode, so the rule is reproduce -> A/B -> prove. This probe is
  the REPRODUCE half: it establishes, from live data, (1) that such tiles exist and where,
  (2) the exact tile-type STRINGS involved (so a fix cannot KeyError on an unparsed one), and
  (3) what the current model claims about each one versus the candidate model.

‼ WHAT THIS PROBE MEASURED, 2026-08-13 (so a reader need not re-run it to know the headline):
  * 2,658 `Impassable *` tiles across all 518 maps; **2,257 are DORMANT** (collision != 0, so they
    never reach the buggy branch) and only **401 (15.1%) are LIVE**.
  * ⛔ **ZERO of the Seafloor Cavern's 115 are live** — all have `collision=1`. KI-59 was therefore
    NEVER a §Ch20/§Ch21 blocker, and the A/B four documents prescribed on `SEAFLOOR_CAVERN_ROOM1`
    would have measured a zero delta. (Those 115 sit in **seven of the nine rooms** — R6, R7, the
    ENTRANCE and UNDERWATER_SEAFLOOR_CAVERN have none.)
  * It is live chiefly on the **REGI TOMBS** (144), **SHOAL CAVE** (98) and **VICTORY ROAD** (58).
  * ⚠ These are **STATIC ROM layouts**. The Regi tombs, Shoal Cave's low-tide rooms and the Lilycove
    Contest Lobby all rewrite their own tiles at runtime (`setmetatile` / `setmaplayoutindex`), so
    their counts are the compiled floor plan, not what is on screen. **No `SEAFLOOR_CAVERN_ROOM*`
    script uses either command**, which is why the cavern conclusion is unaffected.
  * ⇒ **A/B the fix on `VICTORY_ROAD_1F`** (29 live, and it does NOT rewrite itself), with a
    Seafloor room as the NEGATIVE control.

WHAT IT DOES *NOT* DO
  It does not decide the fix and it does not patch anything. The direction-semantics question
  (clear the SAME direction, or clear the OPPOSITE one?) is settled from the decomp + from
  `map_path.py`'s own consumer, not from this probe. This probe only measures the blast radius.

ESTABLISHED FROM THE CONSUMER, NOT FROM THE VARIABLE NAME (`map_path.py:858`):
    is_tile_accessible(neighbour, direction, node.elevation)
  where `direction` indexes `potential_neighbours` (North -> (x, y-1)). So
  `accessible_from_direction[d]` means "may step ONTO this tile while MOVING in direction d".
  Corroborated by the waterfall branch (`:730`, North == going UP a waterfall) and the muddy-slope
  branch (`:735`, North == going UP the slope).

CONTROLS (so a null result is attributable):
  * POSITIVE — a map that MUST contain `Impassable *` tiles (the Seafloor Cavern rooms). If the
    scan finds zero there, the SCANNER is broken, not the map.
  * NEGATIVE — MOSSDEEP_CITY, recorded in KI-58 as having no `Impassable *` tiles at all. If that
    comes back non-zero, this probe's tile-type matching is wrong.
  * PARSE control — every distinct string is run through the EXACT parse the production code uses,
    so an unparseable name shows up here rather than as a KeyError in a live run.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_impassable_dirs.py
Exit: 0 always (this is a measurement probe, not a gate).
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data
from modules.map_data import MapRSE
from modules.map_path import Direction
from modules.player import get_player_avatar

BAR = "=" * 100

# ‼ The cavern rooms KI-59 says the bug is ARMED in, plus the two maps on the way in.
CAVERN_MAPS = [
    MapRSE.UNDERWATER_SEAFLOOR_CAVERN,
    MapRSE.SEAFLOOR_CAVERN_ENTRANCE,
    MapRSE.SEAFLOOR_CAVERN_ROOM1,
    MapRSE.SEAFLOOR_CAVERN_ROOM2,
    MapRSE.SEAFLOOR_CAVERN_ROOM3,
    MapRSE.SEAFLOOR_CAVERN_ROOM4,
    MapRSE.SEAFLOOR_CAVERN_ROOM5,
    MapRSE.SEAFLOOR_CAVERN_ROOM6,
    MapRSE.SEAFLOOR_CAVERN_ROOM7,
    MapRSE.SEAFLOOR_CAVERN_ROOM8,
    MapRSE.SEAFLOOR_CAVERN_ROOM9,
]

# NEGATIVE control — KI-58 recorded this map as having no `Impassable *` tiles.
CONTROL_MAPS = [MapRSE.MOSSDEEP_CITY]


def head(title: str) -> None:
    print(f"\n{BAR}\n{title}\n{BAR}\n")


def scan(map_enum: MapRSE) -> list:
    return get_map_all_tiles(get_map_data(map_enum, (0, 0)))


def parse_like_production(tile_type: str) -> tuple[list[str], str | None]:
    """The EXACT parse `map_path.py:128-131` performs. Returns (directions, error-or-None)."""
    raw = tile_type[11:].replace(" and ", "/").split("/")
    try:
        return [Direction[d].name for d in raw], None
    except KeyError as exc:
        return raw, f"KeyError {exc}"


def buggy_model_before_2026_08_13(dirs: list[str]) -> list[bool]:
    """‼ RENAMED 2026-08-13. This was called `current_model()` and its docstring said "what
    map_path.py builds TODAY" — which became FALSE the moment KI-59 was fixed, in a committed
    artifact whose whole job is to be believed. It is kept because the A/B write-ups quote its
    output; it is the HISTORICAL buggy model: start all-False, SET [opposite] True.
    ⇒ `fix_a_clear_opposite` below is what production does today."""
    acc = [False, False, False, False]
    for d in dirs:
        acc[Direction[d].opposite()] = True
    return acc


def fix_a_clear_opposite(dirs: list[str]) -> list[bool]:
    """FIX-A — start all-True, CLEAR [opposite].
    Reads `Impassable North` as "this tile's NORTH EDGE is walled", so the movement it forbids is
    SOUTHWARD entry (you would be crossing that edge)."""
    acc = [True, True, True, True]
    for d in dirs:
        acc[Direction[d].opposite()] = False
    return acc


def fix_b_clear_named(dirs: list[str]) -> list[bool]:
    """FIX-B — start all-True, CLEAR [the named direction].
    Reads `Impassable North` as "you may not travel NORTH onto this tile"."""
    acc = [True, True, True, True]
    for d in dirs:
        acc[Direction[d]] = False
    return acc


def fmt(acc: list[bool]) -> str:
    names = ["N", "E", "S", "W"]
    return "".join(names[i] if acc[i] else "-" for i in range(4))


avatar = get_player_avatar()
print("anchor: post_dive.ss1")
print(
    f"avatar: {MapRSE(tuple(avatar.map_group_and_number)).name} "
    f"{tuple(avatar.local_coordinates)}   (‼ asserted, not assumed — KI-60)"
)
print("‼ the avatar is NOT in the cavern; every map below is read by ENUM, not by standing on it.")

head("1. CENSUS — `Impassable *` tiles per map")

totals: dict[str, int] = {}
per_map: dict[str, list] = {}
grand = 0
for map_enum in CAVERN_MAPS + CONTROL_MAPS:
    tiles = scan(map_enum)
    hits = [t for t in tiles if t.tile_type.startswith("Impassable ")]
    per_map[map_enum.name] = hits
    grand += len(hits)
    tag = "  <- NEGATIVE control" if map_enum in CONTROL_MAPS else ""
    print(f"  {map_enum.name:<34} tiles={len(tiles):>5}  impassable={len(hits):>4}{tag}")
    for t in hits:
        totals[t.tile_type] = totals.get(t.tile_type, 0) + 1

print(f"\n  TOTAL `Impassable *` tiles across the cavern maps + control: {grand}")

control_hits = sum(len(per_map[m.name]) for m in CONTROL_MAPS)
cavern_hits = sum(len(per_map[m.name]) for m in CAVERN_MAPS)
print(f"  cavern={cavern_hits}   control={control_hits}")
print(f"  POSITIVE control (cavern > 0): {'PASS' if cavern_hits > 0 else '‼ FAIL — the SCANNER is broken'}")
print(f"  NEGATIVE control (control == 0): {'PASS' if control_hits == 0 else '‼ FAIL — matching is wrong'}")

head("2. THE DISTINCT STRINGS, and whether the PRODUCTION parse survives them")

if not totals:
    print("  (none found — nothing to parse)")
for tile_type, count in sorted(totals.items(), key=lambda kv: -kv[1]):
    dirs, err = parse_like_production(tile_type)
    if err:
        print(f"  {tile_type:<40} n={count:<5} ‼ PARSE FAILS: {err}   (a live run would crash here)")
    else:
        cur = buggy_model_before_2026_08_13(dirs)
        fa = fix_a_clear_opposite(dirs)
        fb = fix_b_clear_named(dirs)
        verdict = "A==B (this string cannot discriminate)" if fa == fb else "A != B — DISCRIMINATING"
        print(
            f"  {tile_type:<40} n={count:<5} dirs={'+'.join(dirs):<14} "
            f"pre-fix=[{fmt(cur)}]  fixA=[{fmt(fa)}]  fixB=[{fmt(fb)}]   {verdict}"
        )

head("3. WHAT EACH CANDIDATE SAYS THE CURRENT CODE GETS WRONG, weighted by real tile counts")

print("  Reading: for each distinct string, which MOVEMENT directions does each model permit?")
print("  A direction the candidate allows but `current` refuses is a legal move the planner")
print("  refuses TODAY (OVER-block). A direction `current` allows but the candidate refuses is an")
print("  ILLEGAL move the planner would happily walk into TODAY (UNDER-block).\n")
print("  ‼ An UNDER-block is the more dangerous half: the planner routes THROUGH a wall, the avatar")
print("    walks into it, and the failure surfaces as a movement timeout far from its cause.\n")

names = ["North", "East", "South", "West"]
for label, model in (("FIX-A (clear opposite)", fix_a_clear_opposite), ("FIX-B (clear named)", fix_b_clear_named)):
    over = under = 0
    print(f"  --- if {label} is correct ---")
    for tile_type, count in sorted(totals.items(), key=lambda kv: -kv[1]):
        dirs, err = parse_like_production(tile_type)
        if err:
            continue
        cur = buggy_model_before_2026_08_13(dirs)
        cand = model(dirs)
        overs = [names[i] for i in range(4) if cand[i] and not cur[i]]
        unders = [names[i] for i in range(4) if cur[i] and not cand[i]]
        over += len(overs) * count
        under += len(unders) * count
        print(
            f"    {tile_type:<32} n={count:<5} over={', '.join(overs) or '-':<20} "
            f"under={', '.join(unders) or '-'}"
        )
    print(f"    => tile-directions OVER-blocked today: {over}")
    print(f"    => tile-directions UNDER-blocked today: {under}\n")

head("4. WHERE THEY ARE — the per-room coordinates (for building the A/B route)")

for map_enum in CAVERN_MAPS:
    hits = per_map[map_enum.name]
    if not hits:
        continue
    coords = sorted(tuple(t.local_position) for t in hits)
    print(f"  {map_enum.name} ({len(coords)}):")
    line = "    "
    for i, c in enumerate(coords):
        line += f"{c} "
        if (i + 1) % 8 == 0:
            print(line)
            line = "    "
    if line.strip():
        print(line)

head("5. WHOLE-GAME BLAST RADIUS — every map in MapRSE (this is SHARED pathfinding code)")

print("  KI-59 is in code every bot mode uses, so 'it is fine in the cavern' is not enough. This")
print("  sweep answers: how many maps in the entire game carry `Impassable *` tiles, which strings")
print("  actually occur anywhere, and which maps we could reach TODAY to test the fix live.\n")

sweep_totals: dict[str, int] = {}
live_totals: dict[str, int] = {}
live_maps: dict[str, int] = {}
dormant = 0
maps_with: list[tuple[str, int, dict[str, int]]] = []
failed_maps: list[tuple[str, str]] = []

all_maps = list(MapRSE)
for map_enum in all_maps:
    try:
        tiles = scan(map_enum)
    except Exception as exc:  # a map we cannot read is a MEASUREMENT GAP, so it is reported, not hidden
        failed_maps.append((map_enum.name, f"{type(exc).__name__}: {exc}"))
        continue
    local: dict[str, int] = {}
    for t in tiles:
        if t.tile_type.startswith("Impassable "):
            local[t.tile_type] = local.get(t.tile_type, 0) + 1
            sweep_totals[t.tile_type] = sweep_totals.get(t.tile_type, 0) + 1
            # ‼ THE DECIDING SPLIT. `map_path.py:118` is `if tile.collision != 0:` and the
            # `Impassable *` handler at `:128` is its `elif`. So a tile with collision != 0
            # NEVER REACHES the buggy branch — it is already blocked outright. Only
            # collision == 0 tiles are actually mis-modelled.
            if t.collision == 0:
                live_totals[t.tile_type] = live_totals.get(t.tile_type, 0) + 1
                live_maps[map_enum.name] = live_maps.get(map_enum.name, 0) + 1
            else:
                dormant += 1
    if local:
        maps_with.append((map_enum.name, sum(local.values()), local))

print(f"  maps scanned OK : {len(all_maps) - len(failed_maps)} of {len(all_maps)}")
print(f"  maps unreadable : {len(failed_maps)}  (listed at the end — these are measurement GAPS)")
print(f"  maps WITH `Impassable *` tiles: {len(maps_with)}")
print(f"  total such tiles in the game   : {sum(sweep_totals.values())}\n")

print("  Distinct strings that actually occur ANYWHERE in the game:")
for tile_type, count in sorted(sweep_totals.items(), key=lambda kv: -kv[1]):
    dirs, err = parse_like_production(tile_type)
    if err:
        print(f"    {tile_type:<32} n={count:<6} ‼ PARSE FAILS: {err}")
        continue
    fa = fix_a_clear_opposite(dirs)
    fb = fix_b_clear_named(dirs)
    disc = "DISCRIMINATING" if fa != fb else "cannot discriminate A vs B"
    print(
        f"    {tile_type:<32} n={count:<6} pre-fix=[{fmt(buggy_model_before_2026_08_13(dirs))}] "
        f"fixA=[{fmt(fa)}] fixB=[{fmt(fb)}]  {disc}"
    )
print("\n  ‼ Any of the ten producible strings NOT listed above never occurs in this ROM, so no")
print("    real route depends on it. That bounds how much of the fix is actually exercised.")

head("6. ‼ THE DECIDING SPLIT — how many of those tiles REACH the buggy branch at all?")

print("  `map_path.py:118` is `if tile.collision != 0:` and the `Impassable *` handler at `:128` is")
print("  its `elif`. A tile with collision != 0 therefore NEVER reaches the handler — it is already")
print("  blocked outright and the inversion cannot affect it. Only collision == 0 tiles are LIVE.\n")

live_count = sum(live_totals.values())
total_count = sum(sweep_totals.values())
print(f"  `Impassable *` tiles in the game        : {total_count}")
print(f"  ... with collision != 0 (DORMANT)       : {dormant}")
print(f"  ... with collision == 0 (LIVE, buggy)   : {live_count}")
pct = (100.0 * live_count / total_count) if total_count else 0.0
print(f"  LIVE share: {pct:.2f}%\n")

if live_count == 0:
    print("  ⇒ ‼ KI-59 IS DORMANT IN THIS ROM. The inverted branch is real code, but NO tile in any")
    print("    of the 518 maps reaches it: every `Impassable *` tile is already collision-blocked.")
    print("    A fix would be a correctness cleanup with ZERO routing effect — and any A/B claiming")
    print("    to show a routing change would be measuring something else.")
else:
    print("  ⇒ The bug is LIVE on these maps (tile counts are collision == 0 only):")
    for name, n in sorted(live_maps.items(), key=lambda kv: -kv[1]):
        print(f"    {name:<44} {n}")
    print("\n  Distinct LIVE strings:")
    for tile_type, n in sorted(live_totals.items(), key=lambda kv: -kv[1]):
        print(f"    {tile_type:<32} n={n}")

print("\n  The maps carrying them (most first):")
for name, total, local in sorted(maps_with, key=lambda r: -r[1])[:40]:
    breakdown = ", ".join(f"{k[11:]}x{v}" for k, v in sorted(local.items()))
    print(f"    {name:<40} {total:>5}   {breakdown}")
if len(maps_with) > 40:
    print(f"    ... and {len(maps_with) - 40} more maps")

if failed_maps:
    print("\n  ‼ UNREADABLE MAPS (measurement gaps, not zeroes):")
    for name, err in failed_maps[:20]:
        print(f"    {name:<40} {err}")
    if len(failed_maps) > 20:
        print(f"    ... and {len(failed_maps) - 20} more")

head("7. PRE-REGISTERED HAZARDS FOR THE FIX (checked NOW, before any code changes)")

print("  H1. `_is_optional_blocker` is consulted ONLY by the LAST elif (`map_path.py:279`). An")
print("      `Impassable *` tile takes the EARLIER branch, so it never consults the blocker list.")
print("      Today that is harmless (such tiles come out mostly-False = blocked anyway). After the")
print("      fix they come out mostly-True, so an optional-blocker tile that is ALSO `Impassable`")
print("      would become WALKABLE and defeat its flag gate. Are any of them?\n")

BLOCKERS = [
    (MapRSE.SHOAL_CAVE_LOW_TIDE_INNER_ROOM, (31, 8), "RECEIVED_SHOAL_SALT_1"),
    (MapRSE.SHOAL_CAVE_LOW_TIDE_INNER_ROOM, (14, 26), "RECEIVED_SHOAL_SALT_2"),
    (MapRSE.SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM, (11, 11), "RECEIVED_SHOAL_SALT_3"),
    (MapRSE.SHOAL_CAVE_LOW_TIDE_LOWER_ROOM, (18, 2), "RECEIVED_SHOAL_SALT_4"),
]
h1_hits = 0
for map_enum, coords, flag in BLOCKERS:
    t = get_map_data(map_enum, coords)
    is_imp = t.tile_type.startswith("Impassable ")
    danger = is_imp and t.collision == 0
    h1_hits += 1 if danger else 0
    print(
        f"    {map_enum.name:<36} {str(coords):<9} {flag:<22} "
        f"type={t.tile_type!r} collision={t.collision}  "
        f"{'‼ AT RISK' if danger else 'safe (not a live Impassable tile)'}"
    )
print(f"\n    H1 verdict: {'PASS — no optional-blocker tile is a live Impassable tile' if h1_hits == 0 else f'‼ {h1_hits} AT RISK — the fix MUST intersect with _is_optional_blocker'}")

print("\n  H2. `Secret Base Breakable Door` (metatile 0xBE) is a DIRECTIONAL impassable in the decomp")
print("      (`MetatileBehavior_IsEastBlocked`/`IsWestBlocked` both return TRUE for it), but its")
print("      string does not start with `Impassable `, so it falls through to the generic")
print("      `[True]*4`. It is therefore UNDER-blocked today, and the fix should route it into the")
print("      same handler. Does it occur in this ROM at all?")
print("  H3. `Secret Base Impassable` (0xB9) is a FALSE FRIEND — it is NOT directional. Any fix")
print("      that widens the match from `startswith('Impassable ')` to `'Impassable' in ...` would")
print("      wrongly capture it. Counted here so the widening temptation is measurable.\n")

h2 = h3 = 0
h2_maps: dict[str, int] = {}
for map_enum in all_maps:
    try:
        tiles = scan(map_enum)
    except Exception:
        continue
    for t in tiles:
        if t.tile_type == "Secret Base Breakable Door":
            h2 += 1
            h2_maps[map_enum.name] = h2_maps.get(map_enum.name, 0) + 1
        elif t.tile_type == "Secret Base Impassable":
            h3 += 1
print(f"    `Secret Base Breakable Door` tiles in the game: {h2}   maps: {list(h2_maps)[:6]}")
print(f"    `Secret Base Impassable`     tiles in the game: {h3}")
print(f"    H2 verdict: {'no occurrences — fixing it is correctness-only, unexercised' if h2 == 0 else 'occurs; the fix should handle it'}")
print(f"    H3 verdict: {'no occurrences — the widening trap is theoretical here' if h3 == 0 else 'occurs; do NOT widen the prefix match'}")

head("DONE — measurement only. No code was changed by this probe.")
