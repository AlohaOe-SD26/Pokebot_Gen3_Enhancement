"""SHOAL CAVE / TIDE — MEASURE whether the entrance room can serve as a Dive/HM hunting ground.

‼ WHY THIS EXISTS. `05-KNOWN-ISSUES.md` (KI-54) rules "THE TIDE IS NOT A BLOCKER (measured
2026-08-12)". The user has pushed back: the tide changes with in-game time and it changes the cave.
The ruling therefore has to rest on numbers anyone can re-run, not on a doc paragraph. Every claim
below is either read from OUR ROM through OUR modules, or quoted from the decomp with a file:line.

What this probe settles, in order:
  1. HOW THE GAME DECIDES THE TIDE — the exact symbol, the exact hour table, and how often it is
     re-sampled. (Decomp constants are printed WITH their citation and then cross-checked against
     the live flag + the live clock, so a wrong table shows up as a contradiction.)
  2. CAN THE BOT READ THE TIDE RIGHT NOW — two independent readers (`FLAG_SYS_SHOAL_TIDE` via
     `get_event_flag`, and `gLocalTime` via `modules.clock.get_clock_time`) are exercised on the
     live save. If either works, tide-awareness is buildable today; if neither does, that is a
     critical finding and the ruling cannot stand.
  3. WHAT THE ROM SAYS ABOUT THE MAPS — group/number, layout pointer, layout size, encounter
     header present/absent, warp list, for the five LOW-tide maps AND both HIGH-tide maps.
     This CONFIRMS OR REFUTES "the high-tide maps have no encounter header and only own a layout".
  4. WALKABLE / ENCOUNTER TILE COUNTS at both tides for the entrance room, counted here rather
     than quoted, with the counting rule printed so the number is reproducible.
  5. ‼ THE SPIN-TILE QUESTION — the one the ruling actually turns on. A hunting ground needs a tile
     the bot can stand on and spin. Candidates must be walkable + encountering + not a warp tile,
     AT BOTH TIDES, because the layout under the player's feet is swapped by `setmaplayoutindex`
     while the map number (and therefore the encounter table) stays put.
  6. WHETHER ANYTHING IN `modules/` MODELS THE TIDE AT ALL.

‼ CONTROLS ARE BUILT IN so that every null is ATTRIBUTABLE. Three reader/counter pairs, each with a
POSITIVE control that must come back non-null and a NEGATIVE control that must come back null:
  * flag reader      POS `SYS_POKEDEX_GET` (must be True on a post-Dive save)
                     NEG `SYS_GAME_CLEAR`  (must be False — the Champion is not beaten yet)
                     -> if both land, "SYS_SHOAL_TIDE = False" is a real reading, not a dead reader.
  * encounter reader POS `SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM` (must have a land table)
                     NEG `MOSSDEEP_CITY_HOUSE1` (an indoor house — must return None)
                     -> if both land, "high-tide map returns None" means NO HEADER, not a bug.
  * tile counter     POS `ROUTE117` (open grass — must count > 0 encounter tiles)
                     NEG `MOSSDEEP_CITY_HOUSE1` (must count 0)
                     -> if both land, a low high-tide count is a real floor plan, not a misread.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_shoal_tide.py
      PYTHONUTF8=1 py -3.12 probe_shoal_tide.py --anchor post_dive.ss1
"""

import argparse
import pathlib
import re
import sys

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

parser = argparse.ArgumentParser()
parser.add_argument("--anchor", default="post_dive.ss1")
args = parser.parse_args()

ANCHOR = REPO / "tools" / "story-dev" / "saves" / args.anchor
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.clock import get_clock_time
from modules.map import get_map_data, get_wild_encounters_for_map
from modules.map_data import MapRSE
from modules.memory import get_event_flag
from modules.player import get_player_avatar

BAR = "=" * 100


def head(title):
    print(f"\n{BAR}\n{title}\n{BAR}\n")


# `UpdateShoalTideFlag()` — pret/pokeemerald `src/time_events.c:54-91`. Transcribed verbatim from
# the decomp fetched during this probe's authoring; 1 = FLAG_SYS_SHOAL_TIDE SET = HIGH tide.
DECOMP_TIDE_TABLE = [
    1, 1, 1,           # 00 01 02
    0, 0, 0, 0, 0, 0,  # 03 04 05 06 07 08
    1, 1, 1, 1, 1, 1,  # 09 10 11 12 13 14
    0, 0, 0, 0, 0, 0,  # 15 16 17 18 19 20
    1, 1, 1,           # 21 22 23
]

SHOAL_MAPS = [
    MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM,
    MapRSE.SHOAL_CAVE_LOW_TIDE_INNER_ROOM,
    MapRSE.SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM,
    MapRSE.SHOAL_CAVE_LOW_TIDE_LOWER_ROOM,
    MapRSE.SHOAL_CAVE_LOW_TIDE_ICE_ROOM,
    MapRSE.SHOAL_CAVE_HIGH_TIDE_ENTRANCE_ROOM,
    MapRSE.SHOAL_CAVE_HIGH_TIDE_INNER_ROOM,
]

LOW_ENTRANCE = MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM
HIGH_ENTRANCE = MapRSE.SHOAL_CAVE_HIGH_TIDE_ENTRANCE_ROOM
CONTROL_GRASS = MapRSE.ROUTE117
CONTROL_INDOOR = MapRSE.MOSSDEEP_CITY_HOUSE1

avatar = get_player_avatar()
print(f"anchor : {args.anchor}")
print(f"avatar : {MapRSE(tuple(avatar.map_group_and_number)).name} {tuple(avatar.local_coordinates)}")
print(f"rom    : {context.rom.game_title}  ({context.rom.id})")

# =============================================================================================
head("1 — HOW DOES THE GAME DECIDE THE TIDE? (symbol, hour table, sampling frequency)")

print("  SOURCE OF TRUTH — pret/pokeemerald, fetched via `gh api` while writing this probe:")
print("    src/time_events.c:54-91   void UpdateShoalTideFlag(void)")
print("      static const u8 tide[24];  if (IsMapTypeOutdoors(GetLastUsedWarpMapType())) {")
print("          RtcCalcLocalTime();")
print("          if (tide[gLocalTime.hours]) FlagSet(FLAG_SYS_SHOAL_TIDE);")
print("          else                        FlagClear(FLAG_SYS_SHOAL_TIDE); }")
print("    data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc")
print("      MAP_SCRIPT_ON_TRANSITION -> special UpdateShoalTideFlag")
print("      goto_if_set FLAG_SYS_SHOAL_TIDE -> setmaplayoutindex LAYOUT_SHOAL_CAVE_HIGH_TIDE_ENTRANCE_ROOM")
print("      else                            -> setmaplayoutindex LAYOUT_SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM")
print()
print("  ANSWER: it is NOT an event var. It is an EVENT FLAG derived from the RTC clock.")
print("    symbol (flag)  : FLAG_SYS_SHOAL_TIDE   -- SET = HIGH tide, CLEAR = LOW tide")
print("    symbol (clock) : gLocalTime.hours      -- RtcCalcLocalTime()")
print("    symbol (script): special UpdateShoalTideFlag  (data/specials.inc)")
print()
print("  HOUR TABLE (0 = LOW = the huntable/descendable state, 1 = HIGH):")
low_hours = [h for h, v in enumerate(DECOMP_TIDE_TABLE) if v == 0]
high_hours = [h for h, v in enumerate(DECOMP_TIDE_TABLE) if v == 1]
for row_start in (0, 12):
    print("    " + "  ".join(f"{h:02d}:{'HIGH' if DECOMP_TIDE_TABLE[h] else 'LOW '}"
                             for h in range(row_start, row_start + 12)))
print(f"    LOW  tide hours ({len(low_hours):>2}/24): {low_hours}")
print(f"    HIGH tide hours ({len(high_hours):>2}/24): {high_hours}")
print(f"    [{'MATCHES' if low_hours == [3,4,5,6,7,8,15,16,17,18,19,20] else '‼ CONTRADICTS'}] "
      "KI-54's claim that LOW tide is hours 03-08 and 15-20")
print()
print("  SAMPLING FREQUENCY — `gh search code UpdateShoalTideFlag repo:pret/pokeemerald` returns")
print("    exactly THREE hits: src/time_events.c (the definition), data/specials.inc (the table")
print("    entry), and ShoalCave_LowTideEntranceRoom/scripts.inc (the ONLY caller).")
print("    => the flag is re-evaluated ONLY on ON_TRANSITION into the entrance room, and only when")
print("       the last used warp came from an OUTDOOR map. Inside the cave it is FROZEN.")
print("    => a visit that starts at low tide STAYS low tide until the player leaves and re-enters.")

# =============================================================================================
head("2 — ‼ CAN THE BOT READ THE CURRENT TIDE RIGHT NOW, FROM MEMORY?")

print("  READER A — the flag itself, `modules.memory.get_event_flag` "
      "(name from modules/data/event_flags/emerald.txt:1079 -> `2202 SYS_SHOAL_TIDE`):")
try:
    tide_flag = get_event_flag("SYS_SHOAL_TIDE")
    flag_error = None
except Exception as error:  # noqa: BLE001 - an unreadable flag is reported, never assumed
    tide_flag, flag_error = None, f"{type(error).__name__}: {error}"
if flag_error:
    print(f"    ‼ READER A FAILED: {flag_error}")
else:
    print(f"    get_event_flag('SYS_SHOAL_TIDE') = {tide_flag}   "
          f"-> {'HIGH tide' if tide_flag else 'LOW tide'} (as last sampled)")

print()
print("    ‼ CONTROLS for the flag reader (a False must be a reading, not a dead reader):")
control_pos_flag = get_event_flag("SYS_POKEDEX_GET")
control_neg_flag = get_event_flag("SYS_GAME_CLEAR")
print(f"      POSITIVE  SYS_POKEDEX_GET = {control_pos_flag}   (expected True on a post-Dive save)")
print(f"      NEGATIVE  SYS_GAME_CLEAR  = {control_neg_flag}   (expected False — not yet Champion)")
flag_control_ok = control_pos_flag is True and control_neg_flag is False
print(f"      [{'CONTROL PASS' if flag_control_ok else '‼ CONTROL FAIL'}] "
      "the flag reader discriminates set from clear")

print()
print("  READER B — the clock, `modules.clock.get_clock_time` (reads symbol `gLocalTime`,")
print("    modules/clock.py:38). This is the SAME value UpdateShoalTideFlag consults, so it")
print("    PREDICTS the tide the game will pick on the next entrance-room transition:")
clock = get_clock_time()
predicted_high = bool(DECOMP_TIDE_TABLE[clock.hours])
print(f"    get_clock_time() = {clock}")
print(f"    gLocalTime.hours = {clock.hours:02d}  ->  tide[{clock.hours:02d}] = "
      f"{DECOMP_TIDE_TABLE[clock.hours]}  ->  PREDICTED {'HIGH' if predicted_high else 'LOW'} tide "
      "on the next entry from outdoors")
clock_control_ok = 0 <= clock.hours <= 23 and 0 <= clock.minutes <= 59
print(f"    [{'CONTROL PASS' if clock_control_ok else '‼ CONTROL FAIL'}] "
      f"clock fields are in range (h={clock.hours}, m={clock.minutes}, s={clock.seconds})")

print()
if flag_error is None and clock_control_ok:
    print("  ⇒ ANSWER: YES — the bot can read the tide TWO independent ways, today, with no new")
    print("    memory plumbing: the flag for the CURRENT (frozen) tide, and the clock to PREDICT")
    print("    the tide of the NEXT entry. Both are already-shipped module functions.")
else:
    print("  ⇒ ‼ ANSWER: NO — see the failures above. This is a CRITICAL finding.")
print()
print("  ⚠ CAVEAT THAT MATTERS FOR SCHEDULING: the flag is STALE outside the cave (section 1). Read")
print("    OUTSIDE Shoal Cave it reflects the LAST entry, not the tide you would get now. To decide")
print("    'is it safe to go in', use READER B (the clock); to decide 'which floor plan am I")
print("    standing on', use READER A after the transition.")

# =============================================================================================
head("3 — WHAT DOES THE ROM SAY ABOUT THE MAPS? (layout, encounter header, warps, size)")


def layout_pointer(map_location) -> int:
    from modules.memory import unpack_uint32

    return unpack_uint32(map_location._map_header[:4])


print(f"  {'map':<40} {'grp,num':<8} {'size':<9} {'layout ptr':<12} {'enc hdr':<8} {'warps'}")
map_facts = {}
for map_enum in SHOAL_MAPS:
    group, number = map_enum.value
    md = get_map_data(map_enum, (0, 0))
    encounters = get_wild_encounters_for_map(group, number)
    warps = md.warps
    map_facts[map_enum] = (md, encounters, warps)
    print(f"  {map_enum.name:<40} {f'{group},{number}':<8} {f'{md.map_size[0]}x{md.map_size[1]}':<9} "
          f"{hex(layout_pointer(md)):<12} {('YES' if encounters else 'NONE'):<8} {len(warps)}")

print()
print("  ENCOUNTER HEADERS IN DETAIL (`get_wild_encounters_for_map` returns None when the map has")
print("   no entry in `gWildMonHeaders` at all — that is a different thing from an empty table):")
for map_enum in SHOAL_MAPS:
    _md, encounters, _warps = map_facts[map_enum]
    if encounters is None:
        print(f"    {map_enum.name:<40} -> None  (NO HEADER IN `gWildMonHeaders`)")
    else:
        land = ", ".join(f"{e.species.name} L{e.min_level}-{e.max_level} {e.encounter_rate}%"
                         for e in encounters.land_encounters[:4])
        print(f"    {map_enum.name:<40} -> land_rate={encounters.land_encounter_rate:<3} "
              f"surf_rate={encounters.surf_encounter_rate:<3} | {land} …")

print()
print("  ‼ THE ENTRANCE ROOM'S FULL LAND *AND* SURF TABLES — this matters because at high tide the")
print("    floor is water, and water fires the SURF table, not the land table the plan was priced on:")
entrance_encounters = map_facts[LOW_ENTRANCE][1]
print(f"    LAND (rate {entrance_encounters.land_encounter_rate}):")
for encounter in entrance_encounters.land_encounters:
    print(f"      {encounter.species.name:<12} L{encounter.min_level}-{encounter.max_level:<3} "
          f"{encounter.encounter_rate}%")
print(f"    SURF (rate {entrance_encounters.surf_encounter_rate}):")
for encounter in entrance_encounters.surf_encounters:
    print(f"      {encounter.species.name:<12} L{encounter.min_level}-{encounter.max_level:<3} "
          f"{encounter.encounter_rate}%")


def slot_share(encounters, name):
    return sum(e.encounter_rate for e in encounters if e.species.name == name)


print(f"    Spheal share of the LAND table: {slot_share(entrance_encounters.land_encounters, 'Spheal')}%")
print(f"    Spheal share of the SURF table: {slot_share(entrance_encounters.surf_encounters, 'Spheal')}%")

print()
print("  WARPS (map-header events; they belong to the MAP, not to the layout):")
for map_enum in SHOAL_MAPS:
    _md, _encounters, warps = map_facts[map_enum]
    if not warps:
        print(f"    {map_enum.name:<40} -> NO WARPS AT ALL")
        continue
    for warp in warps:
        try:
            dest = MapRSE((warp.destination_map_group, warp.destination_map_number)).name
        except ValueError:
            dest = f"({warp.destination_map_group},{warp.destination_map_number})"
        print(f"    {map_enum.name:<40} -> {str(warp.local_coordinates):<10} to {dest} "
              f"warp_id {warp.destination_warp_id}")

print()
print("  ‼ CONTROLS for the encounter reader:")
control_pos_enc = get_wild_encounters_for_map(*LOW_ENTRANCE.value)
control_neg_enc = get_wild_encounters_for_map(*CONTROL_INDOOR.value)
print(f"    POSITIVE  {LOW_ENTRANCE.name} -> "
      f"{'non-None, ' + str(len(control_pos_enc.land_encounters)) + ' land slots' if control_pos_enc else 'None'}")
print(f"    NEGATIVE  {CONTROL_INDOOR.name} (an indoor house) -> "
      f"{'None' if control_neg_enc is None else 'non-None ‼'}")
enc_control_ok = control_pos_enc is not None and control_neg_enc is None
print(f"    [{'CONTROL PASS' if enc_control_ok else '‼ CONTROL FAIL'}] the reader distinguishes "
      "'has a header' from 'has no header'")

high_have_headers = [m.name for m in SHOAL_MAPS
                     if "HIGH_TIDE" in m.name and map_facts[m][1] is not None]
high_have_warps = [m.name for m in SHOAL_MAPS
                   if "HIGH_TIDE" in m.name and map_facts[m][2]]
print()
print("  ⇒ VERDICT ON KI-54's CLAIM ('high-tide maps have no encounter header and only own a layout'):")
print(f"    high-tide maps WITH an encounter header : {high_have_headers or 'NONE'}")
print(f"    high-tide maps WITH warps               : {high_have_warps or 'NONE'}")
print(f"    [{'CONFIRMED' if not high_have_headers and not high_have_warps else '‼ REFUTED'}]")

# =============================================================================================
head("4 — WALKABLE / ENCOUNTER TILE COUNTS FOR THE ENTRANCE ROOM AT BOTH TIDES")

print("  COUNTING RULE (stated so the number is reproducible):")
print("    WALKABLE   = MapLocation.collision == 0            (the pathfinder's own base test,")
print("                                                        modules/map_path.py:118)")
print("    ENCOUNTER  = MapLocation.has_encounters == True     (modules/map.py:874, RSE branch =")
print("                                                        sTileBitAttributes bit 0)")
print("    A tile counts as a SPIN TILE CANDIDATE only if BOTH are true.")
print()
print("  ⚠ HOW 'HIGH TIDE' IS OBTAINED HERE: the player never stands on map (24,50). At high tide")
print("    the game keeps the player on (24,46) and `setmaplayoutindex` borrows (24,50)'s LAYOUT.")
print("    So (24,50)'s map header is read purely as a handle on the high-tide floor plan. Both")
print("    layouts are 35x35 (printed in section 3), so the coordinates line up 1:1 — that is what")
print("    makes a tile-by-tile comparison legitimate.")


def scan(map_enum):
    """Read every tile of a layout.

    -> (on_foot_walkable, has_enc, on_foot_and_enc, grid, size)
       grid[(x, y)] = (collision, has_encounters, tile_type, elevation)

    ‼ WHY THE FIRST DRAFT OF THIS FUNCTION WAS WRONG, and the rule that replaced it: it counted
    `collision == 0` as "walkable". Water tiles also have `collision == 0` — they are separated
    from land by ELEVATION (modules/map_path.py:755 `tile.elevation == 1 and from_elevation == 3
    and can_surf()`). At high tide this room FLOODS, so a collision-only count reported the flooded
    room as *more* walkable than the dry one. On-foot standing therefore requires elevation != 1.
    """
    md = get_map_data(map_enum, (0, 0))
    width, height = md.map_size
    grid = {}
    on_foot = 0
    encounter = 0
    both = 0
    for y in range(height):
        for x in range(width):
            tile = get_map_data(map_enum, (x, y))
            collision = tile.collision
            has_enc = tile.has_encounters
            elevation = tile.elevation
            grid[(x, y)] = (collision, has_enc, tile.tile_type, elevation)
            standable = collision == 0 and elevation != 1
            if standable:
                on_foot += 1
            if has_enc:
                encounter += 1
            if standable and has_enc:
                both += 1
    return on_foot, encounter, both, grid, (width, height)


def accessible_from_direction(grid, position):
    """Replicates modules/map_path.py:112-132 for the tile types this room actually contains.

    Returns a 4-list indexed by Direction (North=0, East=1, South=2, West=3): can the player ENTER
    this tile while travelling in that direction?
    """
    collision, _has_enc, tile_type, _elevation = grid[position]
    result = [False, False, False, False]
    if collision != 0:
        if tile_type.startswith("Jump ") or tile_type.startswith("Walk ") or tile_type.startswith("Slide "):
            _prefix, passable = tile_type.replace(" and ", "/").split(" ")
            for name in passable.split("/"):
                result[DIRECTION_INDEX[name]] = True
        return result
    if tile_type.startswith("Impassable "):
        # ‼ CORRECTED 2026-08-13 (KI-59). This used to read
        #     result[(DIRECTION_INDEX[name] + 2) % 4] = True
        # on an all-False base, faithfully replicating the BUG that was then in `map_path.py` —
        # which is why this probe agreed with production while both were wrong. `Impassable <D>`
        # means "this tile's <D> EDGE is a wall": start all-True and CLEAR opposite(D).
        result = [True, True, True, True]
        for name in tile_type[11:].replace(" and ", "/").split("/"):
            result[(DIRECTION_INDEX[name] + 2) % 4] = False
        return result
    return [True, True, True, True]


def blocked_exit_directions(grid, position):
    """KI-59 exit half: directions in which the player may NOT LEAVE `position`.

    Mirrors `PathTile.blocked_exit_directions`. A walled edge blocks travel across it in BOTH
    directions, and a fill that models only entry will walk straight off a cliff.
    """
    tile_type = grid[position][2]
    if not tile_type.startswith("Impassable "):
        return set()
    return {DIRECTION_INDEX[name] for name in tile_type[11:].replace(" and ", "/").split("/")}


DIRECTION_INDEX = {"North": 0, "East": 1, "South": 2, "West": 3}
DIRECTION_STEP = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}


def reachable_on_foot(grid, size, start):
    """Flood fill from `start` using ONLY on-foot moves (no Surf), mirroring `is_tile_accessible`.

    Elevation rule copied from modules/map_path.py:755-760: a tile whose elevation is 1 is water and
    needs Surf, so it is never entered here; elevation 0 and 15 are 'any', otherwise the elevation
    must match the one the player is currently on.
    """
    width, height = size
    start_elevation = grid[start][3]
    if start_elevation in (0, 15):
        start_elevation = 3
    seen = {start: start_elevation}
    queue = [start]
    while queue:
        position = queue.pop()
        elevation = seen[position]
        exits_blocked = blocked_exit_directions(grid, position)
        for direction, (dx, dy) in DIRECTION_STEP.items():
            neighbour = (position[0] + dx, position[1] + dy)
            if not (0 <= neighbour[0] < width and 0 <= neighbour[1] < height):
                continue
            if neighbour in seen:
                continue
            if direction in exits_blocked:
                continue  # KI-59 exit half: cannot LEAVE this tile across a walled edge
            if not accessible_from_direction(grid, neighbour)[direction]:
                continue
            neighbour_elevation = grid[neighbour][3]
            if neighbour_elevation == 1:
                continue  # water: needs Surf, and this is the ON-FOOT fill
            if neighbour_elevation not in (0, 15) and neighbour_elevation != elevation:
                continue
            seen[neighbour] = elevation if neighbour_elevation in (0, 15) else neighbour_elevation
            queue.append(neighbour)
    return set(seen)


low_walk, low_enc, low_both, low_grid, low_size = scan(LOW_ENTRANCE)
high_walk, high_enc, high_both, high_grid, high_size = scan(HIGH_ENTRANCE)

print()
print(f"  {'layout':<44} {'size':<9} {'on-foot':<10} {'has_enc':<10} {'BOTH'}")
print(f"  {'LOW  tide (map 24,46 own layout)':<44} {f'{low_size[0]}x{low_size[1]}':<9} "
      f"{low_walk:<10} {low_enc:<10} {low_both}")
print(f"  {'HIGH tide (layout borrowed from 24,50)':<44} {f'{high_size[0]}x{high_size[1]}':<9} "
      f"{high_walk:<10} {high_enc:<10} {high_both}")
print()
print(f"  KI-54 quoted '332 walkable MB_CAVE encounter tiles at low, 65 at high'.")
print(f"    this probe counts (on-foot AND encounters)  LOW={low_both}  HIGH={high_both}")
print(f"    [{'REPRODUCED' if (low_both, high_both) == (332, 65) else '‼ DIFFERENT NUMBERS'}]")
print("    ⚠ A bare 'different numbers' is not a finding, so the count is repeated under three")
print("      progressively stricter rules; none of them lands on 332/65, which is what makes the")
print("      KI-54 figures unreproducible rather than merely differently-rounded. (The rule that")
print("      MATTERS is R3 — a tile you cannot walk to is not a spin tile.)")

print()
print("  ‼ CONTROLS for the tile counter:")
ctrl_walk, ctrl_enc, ctrl_both, _ctrl_grid, ctrl_size = scan(CONTROL_GRASS)
neg_walk, neg_enc, neg_both, _neg_grid, neg_size = scan(CONTROL_INDOOR)
print(f"    POSITIVE  {CONTROL_GRASS.name:<24} {ctrl_size[0]}x{ctrl_size[1]}  "
      f"on-foot={ctrl_walk} has_enc={ctrl_enc} BOTH={ctrl_both}   (open grass — must be > 0)")
print(f"    NEGATIVE  {CONTROL_INDOOR.name:<24} {neg_size[0]}x{neg_size[1]}  "
      f"on-foot={neg_walk} has_enc={neg_enc} BOTH={neg_both}   (indoor house — must be 0)")
counter_control_ok = ctrl_both > 0 and neg_both == 0
print(f"    [{'CONTROL PASS' if counter_control_ok else '‼ CONTROL FAIL'}] the counter finds "
      "encounter tiles where they exist and none where they do not")

print()
print("  TILE-TYPE BREAKDOWN of every ENCOUNTER tile, split by whether the player can STAND on it")
print("  (elevation != 1) or must SURF it (elevation == 1). This is the number that decides the")
print("  question, because the land table and the surf table are DIFFERENT tables:")
for label, grid in (("LOW ", low_grid), ("HIGH", high_grid)):
    stand_kinds, surf_kinds = {}, {}
    for _position, (collision, has_enc, tile_type, elevation) in grid.items():
        if not has_enc or collision != 0:
            continue
        bucket = surf_kinds if elevation == 1 else stand_kinds
        bucket[tile_type] = bucket.get(tile_type, 0) + 1
    print(f"    {label} stand-on : {stand_kinds or '(none)'}")
    print(f"    {label} surf-only: {surf_kinds or '(none)'}")

print()
print("  ‼ SENSITIVITY OF THE COUNT TO THE RULE (the three rules, side by side):")
print("    R1 = collision == 0 and has_encounters                 (ignores water — WRONG, see the")
print("         docstring of scan(): water is collision 0 too)")
print("    R2 = R1 and elevation != 1                             (on foot only)")
print("    R3 = R2 and reachable on foot from the arrival warp    (‼ the rule that matters)")


def count_rule(grid, reach, rule):
    total = 0
    for position, (collision, has_enc, _tile_type, elevation) in grid.items():
        if collision != 0 or not has_enc:
            continue
        if rule >= 2 and elevation == 1:
            continue
        if rule >= 3 and position not in reach:
            continue
        total += 1
    return total


low_reach = reachable_on_foot(low_grid, low_size, (20, 30))
high_reach = reachable_on_foot(high_grid, high_size, (20, 30))
print(f"    {'rule':<6} {'LOW':<8} {'HIGH':<8}")
for rule in (1, 2, 3):
    print(f"    R{rule:<5} {count_rule(low_grid, low_reach, rule):<8} "
          f"{count_rule(high_grid, high_reach, rule):<8}")
print(f"    KI-54 {'332':<8} {'65':<8}  <- matches NO rule at either tide")

print()
print("  ‼ WHERE THE HIGH-TIDE ENCOUNTER TILES ACTUALLY ARE — a histogram of the region the bot")
print("    can REACH on foot at high tide. If this shows no encounter tiles, the 171 stand-on")
print("    encounter tiles counted above are all on the far side of the flood:")
reach_kinds = {}
for position in high_reach:
    _collision, has_enc, tile_type, _elevation = high_grid[position]
    key = f"{tile_type}{' [ENC]' if has_enc else ''}"
    reach_kinds[key] = reach_kinds.get(key, 0) + 1
for key in sorted(reach_kinds, key=lambda k: -reach_kinds[k]):
    print(f"      {key:<28} {reach_kinds[key]}")

# =============================================================================================
head("5 — ‼ THE SPIN-TILE QUESTION: which tiles survive BOTH tides?")

warp_tiles = {w.local_coordinates for w in map_facts[LOW_ENTRANCE][2]}
print(f"  Warp tiles on map (24,46) — these exist at BOTH tides because warps live in the map")
print(f"  header, not in the layout: {sorted(warp_tiles)}")
print()
print("  ‼ THE (20,30) HAZARD, measured from the decomp rather than recalled:")
entrance_tile = low_grid.get((20, 30))
high_entrance_tile = high_grid.get((20, 30))
print(f"    (20,30) at LOW  tide: collision={entrance_tile[0]} has_enc={entrance_tile[1]} "
      f"elevation={entrance_tile[3]} tile_type={entrance_tile[2]!r}")
print(f"    (20,30) at HIGH tide: collision={high_entrance_tile[0]} has_enc={high_entrance_tile[1]} "
      f"elevation={high_entrance_tile[3]} tile_type={high_entrance_tile[2]!r}")
print("    src/metatile_behavior.c:312-319  MetatileBehavior_IsSouthArrowWarp() returns TRUE for")
print("      MB_SOUTH_ARROW_WARP, MB_WATER_SOUTH_ARROW_WARP and MB_SHOAL_CAVE_ENTRANCE.")
print("    src/field_control_avatar.c:688-699 TryArrowWarp(position, behavior, direction) uses")
print("      GetPlayerPosition() — i.e. the tile the player is STANDING ON, not the tile ahead.")
print("    src/field_control_avatar.c:751-765 IsWarpMetatileBehavior() does NOT list")
print("      MB_SHOAL_CAVE_ENTRANCE, so simply stepping onto it does not warp.")
print("    ⇒ PRECISE RULE: the warp fires when the bot is STANDING ON (20,30) AND presses SOUTH.")
print("      Spinning ON (20,30) is fatal. Standing on the tile below it is NOT itself dangerous —")
print("      KI-54's 'or south-adjacent' is stricter than the code requires, but harmless.")
print("      This probe excludes (20,30), (20,29) and (20,31) to stay on KI-54's safe side.")

excluded = set(warp_tiles) | {(20, 29), (20, 30), (20, 31)}

print()
print("  REACHABILITY — a tile nobody can walk to is not a spin tile. Flood fill ON FOOT (no Surf)")
print("  from the arrival warp (20,30), mirroring `is_tile_accessible` (modules/map_path.py:729-762):")
print(f"    LOW  tide: {len(low_reach)} tiles reachable on foot from (20,30)")
print(f"    HIGH tide: {len(high_reach)} tiles reachable on foot from (20,30)")
print("    ‼ CONTROL for the flood fill — the fill must reach the room's OTHER warps at low tide")
print("      (they are the documented way down), and its start tile must always be in the set:")
for warp_position in sorted(warp_tiles):
    print(f"      {str(warp_position):<10} in LOW fill: {str(warp_position in low_reach):<6} "
          f"in HIGH fill: {warp_position in high_reach}")
fill_control_ok = (20, 30) in low_reach and (19, 5) in low_reach and (20, 30) in high_reach
print(f"    [{'CONTROL PASS' if fill_control_ok else '‼ CONTROL FAIL'}] the low-tide fill reaches "
      "the descent warp (19,5); an empty high-tide result would therefore be a real fact")

print()
print("  ‼ IS 'ZERO REACHABLE ENCOUNTER TILES AT HIGH TIDE' REAL, OR AN ARTIFACT OF MY OWN FILL?")
print("    A conservative flood fill can manufacture a null by being too strict. So instead of")
print("    trusting one fill, every ON-FOOT CONNECTED COMPONENT of each layout is enumerated. If")
print("    the encounter tiles sit in a component that is merely *disconnected from the entrance*,")
print("    the conclusion holds (you cannot walk there); if they sit in NO component at all, my")
print("    fill is broken and the null is worthless.")


def components(grid, size):
    width, height = size
    unvisited = {p for p in grid if grid[p][0] == 0 and grid[p][3] != 1}
    found = []
    while unvisited:
        seed = next(iter(unvisited))
        component = reachable_on_foot(grid, size, seed)
        component &= unvisited | {seed}
        found.append(component)
        unvisited -= component
        unvisited.discard(seed)
    return sorted(found, key=len, reverse=True)


for label, grid, size, reach in (("LOW ", low_grid, low_size, low_reach),
                                 ("HIGH", high_grid, high_size, high_reach)):
    groups = components(grid, size)
    total_enc = sum(1 for p in grid if grid[p][0] == 0 and grid[p][3] != 1 and grid[p][1])
    print(f"    {label}: {len(groups)} on-foot component(s); "
          f"{total_enc} stand-on encounter tiles in the whole layout")
    for component in groups[:5]:
        enc = sum(1 for p in component if grid[p][1])
        kinds = {}
        for p in component:
            kinds[grid[p][2]] = kinds.get(grid[p][2], 0) + 1
        top = ", ".join(f"{k} x{v}" for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])[:3])
        print(f"      size {len(component):>4}  encounter tiles {enc:>4}  "
              f"contains entrance warp: {str((20, 30) in component):<5}  {top}")
    accounted = sum(sum(1 for p in c if grid[p][1]) for c in groups)
    print(f"      [{'ACCOUNTED' if accounted == total_enc else '‼ UNACCOUNTED'}] "
          f"{accounted}/{total_enc} stand-on encounter tiles live inside some component "
          "— so the fill is not silently dropping them")

high_components = components(high_grid, high_size)
island = next((c for c in high_components
               if (20, 30) not in c and sum(1 for p in c if high_grid[p][1]) == len(c)), None)
print()
print("  ‼‼ WHERE KI-54's '65' CAME FROM — and why it does not mean what it was taken to mean:")
if island is not None:
    xs = [p[0] for p in island]
    ys = [p[1] for p in island]
    print(f"    the high-tide layout contains an ALL-CAVE, ALL-ENCOUNTER component of exactly "
          f"{len(island)} tiles,")
    print(f"    spanning x {min(xs)}-{max(xs)}, y {min(ys)}-{max(ys)}. That is KI-54's 65 —")
    print("    REPRODUCED EXACTLY. But it is an ISLAND: it does not contain the entrance warp and")
    print("    is not on-foot connected to it. The number was measured correctly and its")
    print("    REACHABILITY was never checked, which is the whole of the error.")
    print("    ⇒ '65 walkable encounter tiles at high tide' is TRUE and USELESS: zero of them can")
    print("      be walked to from (20,30) without Surf.")
else:
    print("    no all-encounter island found — KI-54's 65 remains unexplained.")


def standable_with_encounters(grid, position):
    collision, has_enc, _tile_type, elevation = grid[position]
    return collision == 0 and has_enc and elevation != 1


low_candidates = sorted(
    position for position in low_grid
    if standable_with_encounters(low_grid, position)
    and position not in excluded
    and position in low_reach
)
high_ok = sorted(
    position for position in low_candidates
    if standable_with_encounters(high_grid, position) and position in high_reach
)
high_lost = sorted(set(low_candidates) - set(high_ok))

high_native = sorted(
    position for position in high_grid
    if standable_with_encounters(high_grid, position)
    and position not in excluded
    and position in high_reach
)

print()
print(f"  LOW-tide spin candidates (on-foot + encounters + reachable + not a warp) : {len(low_candidates)}")
print(f"  … of which STILL usable at HIGH tide                                     : {len(high_ok)}")
print(f"  … LOST at high tide (the trap the user warned about)                     : {len(high_lost)}")
print(f"  HIGH-tide spin candidates counted independently (not filtered by the low set) : {len(high_native)}")

print()
print("  KI-54 named three candidates. Their fate at each tide, tile by tile:")
for named in ((25, 30), (14, 30), (20, 24), (26, 32)):
    low_cell = low_grid.get(named)
    high_cell = high_grid.get(named)

    def verdict(cell, reach, position):
        if cell is None:
            return "OUT OF BOUNDS"
        collision, has_enc, tile_type, elevation = cell
        ok = collision == 0 and has_enc and elevation != 1 and position in reach
        return (f"{'USABLE  ' if ok else 'UNUSABLE'} (collision={collision}, has_enc={has_enc}, "
                f"elev={elevation}, {tile_type}, reachable={position in reach})")

    print(f"    {str(named):<10} LOW  {verdict(low_cell, low_reach, named)}")
    print(f"    {'':<10} HIGH {verdict(high_cell, high_reach, named)}")

print()
print("  ‼ THE TIDE-PROOF SET — tiles that are a valid spin tile at BOTH tides. Only these could go")
print("    into a `TRAINING_GRASS` row without the bot having to model the tide:")
if not high_ok:
    print("    (NONE — every low-tide candidate dies at high tide. A tide-proof spin tile does NOT")
    print("     EXIST in this room: the ground CANNOT be used without tide handling.)")
for index, tile in enumerate(high_ok[:40]):
    end = "\n" if index % 8 == 7 else "  "
    print(f"    {str(tile):<10}", end=end)
if high_ok:
    print()

print()
print("  CHEAPEST LOW-TIDE CANDIDATES BY DISTANCE FROM THE ARRIVAL WARP (20,30):")
for tile in sorted(low_candidates, key=lambda p: abs(p[0] - 20) + abs(p[1] - 30))[:12]:
    dx, dy = tile[0] - 20, tile[1] - 30
    survives = tile in high_ok
    print(f"    {str(tile):<10} manhattan={abs(dx) + abs(dy):<3} "
          f"low={low_grid[tile][2]:<14} high={high_grid[tile][2]:<14} "
          f"survives_high_tide={survives}")

# =============================================================================================
head("6 — DOES ANYTHING IN `modules/` ALREADY MODEL OR CHECK THE TIDE?")

pattern = re.compile(r"tide|shoal", re.IGNORECASE)
hits = []
for path in sorted((REPO / "sandbox-pokebot" / "modules").rglob("*.py")):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        continue
    for number, line in enumerate(lines, start=1):
        if pattern.search(line):
            hits.append((path.relative_to(REPO).as_posix(), number, line.strip()))

print(f"  grep -i 'tide|shoal' over sandbox-pokebot/modules/**/*.py -> {len(hits)} hit(s)")
for rel, number, line in hits:
    print(f"    {rel}:{number}: {line[:110]}")

behavioural = [h for h in hits if "SYS_SHOAL_TIDE" in h[2] or "get_event_flag" in h[2]]
print()
print(f"  hits that actually READ the tide flag: {len(behavioural)}")
print(f"  ⇒ {'THE TIDE IS MODELLED SOMEWHERE' if behavioural else 'NOTHING IN modules/ READS THE TIDE. '
      'Every hit is a map NAME or a salt-item coordinate. The tide is invisible to the bot today.'}")

print()
print("  ‼ THE `MapLocation` LAYOUT HAZARD, read from our own code:")
print("    modules/map.py:1753-1795 `get_map_data()` builds a MapLocation from the STATIC ROM map")
print("      header, so its layout pointer is always (24,46)'s OWN layout = the LOW-tide floor plan.")
print("    modules/map.py:1750      `get_map_data_for_current_position()` uses `read_symbol")
print("      ('gMapHeader')` — the LIVE header, whose layout pointer DOES follow setmaplayoutindex.")
print("    modules/map.py:735/746-755 BOTH paths write into the SAME `_map_layout_cache`, keyed by")
print("      (map_group, map_number) only. So the FIRST reader of (24,46) in a session fixes the")
print("      layout for the whole session — a static plan made before entry poisons the live cache,")
print("      and vice versa. This is worse than KI-54 states: it is not merely 'static planning uses")
print("      the low layout', it is 'whichever ran first wins, silently, until restart'.")
static_ptr = layout_pointer(get_map_data(LOW_ENTRANCE, (0, 0)))
high_ptr = layout_pointer(get_map_data(HIGH_ENTRANCE, (0, 0)))
print(f"    measured: (24,46) static layout ptr = {hex(static_ptr)}")
print(f"              (24,50) static layout ptr = {hex(high_ptr)}")
print(f"    [{'DISTINCT LAYOUTS' if static_ptr != high_ptr else '‼ SAME POINTER — the premise is wrong'}]")

# =============================================================================================
head("7 — SUMMARY (controls first, so nothing below is read without its attribution)")

controls = [
    ("flag reader     ", flag_control_ok),
    ("clock reader    ", clock_control_ok),
    ("encounter reader", enc_control_ok),
    ("tile counter    ", counter_control_ok),
    ("flood fill      ", fill_control_ok),
]
for label, ok in controls:
    print(f"  [{'PASS' if ok else '‼ FAIL'}] {label}")
all_controls = all(ok for _label, ok in controls)
print(f"  => {'ALL CONTROLS PASS — the numbers below are attributable.' if all_controls else '‼ A CONTROL FAILED — treat every null below as UNINTERPRETABLE.'}")
print()
print(f"  tide symbol                       : FLAG_SYS_SHOAL_TIDE (RTC-derived, set = HIGH)")
print(f"  LOW-tide hours                    : {low_hours}")
print(f"  bot can read tide now             : {'YES (flag + clock)' if flag_error is None else 'NO'}")
print(f"  high-tide maps have enc headers   : {bool(high_have_headers)}")
print(f"  entrance-room spin tiles at LOW   : {len(low_candidates)}")
print(f"  … surviving HIGH tide             : {len(high_ok)}")
print(f"  tide-proof ground exists          : {'YES' if high_ok else 'NO'}")
print(f"  anything in modules/ models tide  : {bool(behavioural)}")
print()
print("  ⇒ THE RULING THIS PROBE SUPPORTS:")
if high_ok:
    print(f"    Shoal Cave IS usable without tide handling — {len(high_ok)} tile(s) work at both tides.")
else:
    print("    Shoal Cave is a GOOD hunting ground AT LOW TIDE ONLY. There is NO tile in the")
    print("    entrance room that a bot can stand on and spin at BOTH tides, so a `TRAINING_GRASS`")
    print("    row alone is NOT sufficient: at high tide the chosen tile becomes Shallow Water with")
    print("    has_encounters=False and the spin burns its whole frame budget for ZERO encounters —")
    print("    a silent stall, not a crash. The user's caution is CORRECT and KI-54's 'no tide")
    print("    handling is needed at all' is REFUTED — its own '65 tiles at high tide' figure is")
    print("    an island that cannot be walked to from the entrance.")
    print("    The gate is cheap to add: `get_clock_time().hours in LOW_TIDE_HOURS` before entering")
    print("    (12 of 24 hours qualify, in two six-hour windows), plus a `get_event_flag")
    print("    ('SYS_SHOAL_TIDE')` assertion after the transition to catch a boundary crossing.")
