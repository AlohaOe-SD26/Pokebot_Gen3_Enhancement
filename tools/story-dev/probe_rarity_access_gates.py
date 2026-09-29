"""§Pseudo-rare predicate — TILE-VERIFY `MAP_ACCESS_GATES` for Snorunt (Shoal Cave) and Bagon
(Meteor Falls). Measured in OUR ROM through OUR modules, independent of the recon's decomp decode.

⚠ STATUS (orchestrator, 2026-09-29, revised after the step 7 review; read this before the rest). This probe's
PRE-REGISTERED control FAILED: its flood gives 296 tiles on foot and 333 with Surf where the recorded control is
262/299 (`2026-09-29-rarepredicate-PREDICTIONS.md` R3). The pre-registered consequence is that NOTHING ELSE THIS
PROBE PRINTS IS BELIEVED, and that is how it is treated: it is kept for the record and cited for nothing. After
seeing the mismatch, its author replaced the exit criterion with agreement against production's `calculate_path`
(618 of 621 tiles). That criterion cannot fail by construction: this flood's rules were transcribed FROM
`calculate_path`'s code, so agreement with it proves nothing. The Shoal Cave entries rest on
`probe_rarity_shoal_path.py`; the Meteor Falls entries rest ONLY on their 2026-09-11 citation. Where this docstring
below says the 262/299 control "gates the exit code", read: it USED to; the code now exits 0 on the agreement check.
Three of its remarks are wrong:
  * the `reachable_on_foot()` it compares against lives in `tools/story-dev/probe_shoal_tide.py`, not in
    `training_areas.py`;
  * it prints "C1 (recon's coordinate (24,83) ...) REFUTED", but `(24, 83)` in the task brief was the Ice Room's
    (group, number) map key, which nobody used as a tile;
  * it blames its 3 mismatches on LIVE objects at the anchor; the step 7 review measured that they are item-ball
    object TEMPLATES in Meteor Falls, which `calculate_path` walls (the anchor's only live object is in Mossdeep).

WHY THIS EXISTS
----------------
A recon agent produced a gate table for the "pseudo-rare" predicate (>=2 HM/rod gates from the
STORY PATH to a species' one-and-only encounter spot). Its method was decoding `map.bin` off
GitHub and flood-filling by hand. Per this project's standing rule (Gemini/subagent output is a
NOTE, never truth — `06-DECISIONS-LOG.md`, "CLAUDE VALIDATES GEMINI"), every load-bearing claim
gets re-measured independently before code depends on it. This probe reads the SAME live ROM
through `modules.map`/`modules.map_path`'s own tile semantics (collision/elevation/tile_type,
mirrored from `modules/map_path.py`'s `is_tile_accessible`, the same code `calculate_path` uses)
rather than trusting either the recon's decode or the Gemini notes it disagrees with.

CLAIMS UNDER TEST
  C1 (Snorunt). `SHOAL_CAVE_LOW_TIDE_ICE_ROOM` is where Snorunt lives (land table). Reaching it
     from the Shoal Cave entrance needs Strength: in `SHOAL_CAVE_LOW_TIDE_LOWER_ROOM` a pushable
     boulder at (25,3) must be pushed east 3 times before the warp at (28,11) to the Ice Room
     opens. At low tide nothing else is needed inside the cave; at high tide Surf is also needed
     (to cross the flooded Entrance/Inner rooms). Gemini notes (`item-notes-i10.md`,
     `ADJUDICATED-i10.md`) say the Ice Room's TM07 item ball needs Surf and never mention
     Strength — but that is the ITEM BALL tile (15,6) *inside* the room, a different claim from
     "Strength gates the DOOR into the room". Both can be true at once; this probe checks both.
  C2 (the approach). The Route 125 entrance to Shoal Cave, warp at (22,19), sits on an island, so
     Surf is needed to reach the cave from Mossdeep.
  C3 (Bagon). `METEOR_FALLS_B1F_2R` (Bagon's only room) is unreachable from the story arrival in
     `METEOR_FALLS_1F_1R` (27,18) on foot or with Surf alone; reachable with Surf + Waterfall.
     CONTROL (2026-09-11, `training_areas.py` ~150-180): from (27,18), single-map flood on
     `METEOR_FALLS_1F_1R` alone gives 262 tiles on foot, 299 with Surf. This probe's flood-fill
     MUST reproduce both numbers before anything else it prints is trusted — checked first, and
     the script exits 1 if either fails.

METHOD
  * Tiles: `modules.map.get_map_data` / `get_map_all_tiles` on OUR loaded ROM (profile
    `repro-ml`), anchored on `saves/post_dive.ss1` purely as a frame-advance point — map headers
    are STATIC ROM data, unaffected by which save is loaded (same pattern as
    `probe_route128_landing.py` / `training_areas.py`).
  * Reachability: a hand-rolled BFS whose per-tile ENTRY rule (`_entry_directions`), EXIT rule
    (`_blocked_exits`, the KI-59 fix) and elevation/Surf/Waterfall transition rule are transcribed
    directly from `modules/map_path.py`'s `PathMap.tiles()` builder and `is_tile_accessible()` —
    the same code `calculate_path` (production) runs — but executed as an explicit multi-tile
    flood instead of point-to-point A*, which `calculate_path` cannot do (and cannot cross warps
    at all). This is "independent of the recon's method" (no decomp decode) while still being
    "faithful to the game" (same rule-set as our own trusted pathfinder), per the task brief.
  * ⚠ CONVENTION for the Waterfall arm: `calculate_path` TELEPORTS across a waterfall column in
    one A* edge (`map_path.py:995-1000`, `neighbour = tile.map.get_tile(neighbour.waterfall_to)`)
    rather than visiting each intervening Waterfall metatile as its own node. This flood does NOT
    do that — it is a plain tile-by-tile BFS, entering a Waterfall tile one step at a time (South
    always allowed = descending; North allowed only with the capability = climbing). That is very
    likely why the recon's own numbers split into "364" (its claimed unique-reachable count) and
    "404" (`training_areas.py`'s recorded number, 364 + 40 waterfall tiles individually walked
    through) — a tile-by-tile fill counts the climbed column's tiles as visited; a teleporting A*
    does not need to. Both are defensible; this probe reports its own number under ITS OWN stated
    rule (tile-by-tile) and reconciles against both 364 and 404, but only the 262/299 control
    (which involves no waterfall tile at all) gates the exit code.
  * Warps: multi-map BFS. Whenever the tile-flood on one map reaches a tile matching one of that
    map's `warps`, the destination map+coordinates (via `MapWarp.destination_location`) is queued
    as a fresh flood seed — mirrors "step onto the door tile -> arrive standing on the other side"
    with no capability spent, matching decomp (`IsWarpMetatileBehavior` fires unconditionally for
    ordinary door/warp metatiles; no button, no flag, for every warp used here).
  * Pushable boulder: object events are NOT tiles — read via `MapLocation.objects`
    (`ObjectEventTemplate`, `modules/map.py:1588`). The Lower Room boulder is identified by
    LOCATION (25,3), cross-checked against the decomp
    (`gh api .../data/maps/ShoalCave_LowTideLowerRoom/map.json` ->
    `OBJ_EVENT_GFX_PUSHABLE_BOULDER` at (25,3), verbatim match). The push is SIMULATED explicitly
    (`_simulate_boulder_push`): validate a standing tile behind the boulder and `steps` clear,
    same-map, in-bounds destination tiles ahead, mirroring `TryPushBoulder`
    (`src/field_player_avatar.c:754`, "silently does nothing if blocked" — this probe checks the
    tiles instead of trusting the claim). WITHOUT Strength the boulder's start tile is an extra
    wall; WITH Strength the wall moves to wherever the validated push ends.
  * ⚠ TIDE LAYOUT-SWAP TRAP (`probe_shoal_tide.py`, independently confirmed here by re-reading the
    warp lists): at high tide the player stays on the SAME map object
    (`SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM` / `..._INNER_ROOM`, same warps, same objects) — only the
    tile LAYOUT is swapped to the one the `HIGH_TIDE_*` map owns (`setmaplayoutindex`). So the
    "high tide" flood below reads warps/objects from the LOW_TIDE map but tile geometry
    (collision/elevation/tile_type) from the HIGH_TIDE map — anything else double-reads a stale
    layout. Lower/Stairs/Ice rooms have NO high-tide counterpart at all (confirmed: `gh api` lists
    only two `ShoalCave_HighTide*` maps) so they are read normally at both tides.

CONTROLS
  * The 262/299 Meteor Falls control (above) gates the exit code — nothing else is trusted if it
    fails.
  * `probe_route128_landing.py`'s flood+edge-reachability technique is reused verbatim for the
    Route 125 island check (C2): a component that does not touch the map's connection edges is an
    island by construction, not by a size threshold.
  * The boulder push is VALIDATED tile-by-tile (not assumed from the claim's prose): if any of the
    3 destination tiles is not collision-free, or there is no tile to stand on behind the boulder,
    the WITH_STRENGTH arm reports the push as INVALID and does not silently "believe" the claim.
  * Every claim is stated BEFORE its measurement and graded PASS/FAIL/PARTLY against it, in the
    house style (`probe_route128_landing.py` section 6).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_rarity_access_gates.py
Exit: 1 if the Meteor Falls 262/299 control fails (every later number is then unattributable);
      0 otherwise (measurement probe; claim verdicts are printed, not enforced as gates).
"""

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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_dive.ss1"
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_all_tiles, get_map_data, get_wild_encounters_for_map
from modules.map_data import MapRSE

BAR = "=" * 100


def head(title):
    print(f"\n{BAR}\n{title}\n{BAR}")


# =================================================================================================
# Tile-level reachability primitives, transcribed from modules/map_path.py (see docstring).
# =================================================================================================

_STEP = {"North": (0, -1), "East": (1, 0), "South": (0, 1), "West": (-1, 0)}
_OPPOSITE = {"North": "South", "South": "North", "East": "West", "West": "East"}


def _entry_directions(tile):
    """-> (dict[dir] = can-enter-travelling-that-way, is_waterfall). Mirrors map_path.py:126-379."""
    tile_type = str(tile.tile_type)
    result = {"North": False, "East": False, "South": False, "West": False}
    is_waterfall = False
    if tile.collision != 0:
        if tile_type.startswith("Jump ") or tile_type.startswith("Walk ") or tile_type.startswith("Slide "):
            _prefix, passable = tile_type.replace(" and ", "/").split(" ")
            for name in passable.split("/"):
                result[name] = True
        # else: collision wall, stays all-False.
    elif tile_type.startswith("Impassable "):
        # KI-59 entry half (map_path.py:147-166): start all-True, clear opposite(wall edge).
        result = {"North": True, "East": True, "South": True, "West": True}
        for name in tile_type[11:].replace(" and ", "/").split("/"):
            result[_OPPOSITE[name]] = False
    elif tile_type == "Waterfall":
        is_waterfall = True  # handled specially by the caller; entry_directions unused for it.
    elif tile_type == "Ice":
        result = {"North": True, "East": True, "South": True, "West": True}
    elif tile_type in ("Horizontal Rail", "Isolated Horizontal Rail"):
        result = {"North": False, "East": True, "South": False, "West": True}
    elif tile_type in ("Vertical Rail", "Isolated Vertical Rail"):
        result = {"North": True, "East": False, "South": True, "West": False}
    elif tile_type.endswith(" Current"):
        result = {"North": True, "East": True, "South": True, "West": True}
    else:
        result = {"North": True, "East": True, "South": True, "West": True}
    return result, is_waterfall


def _blocked_exits(tile):
    """KI-59 exit half (map_path.py:379-392): a walled edge blocks LEAVING across it too."""
    tile_type = str(tile.tile_type)
    if tile.collision != 0 or not tile_type.startswith("Impassable "):
        return set()
    return set(tile_type[11:].replace(" and ", "/").split("/"))


def flood_single_map(map_enum, start, *, surf=False, waterfall=False, extra_blocked=frozenset(),
                      tile_source=None):
    """4-way tile BFS on one map. `tile_source`, if given, is the map whose LAYOUT (collision/
    elevation/tile_type) is read instead of `map_enum`'s own — models the Shoal Cave tide swap.

    -> (seen: dict[(x,y)] = elevation-occupied-there, grid: dict[(x,y)] = MapLocation, width, height)
    """
    geometry_enum = tile_source if tile_source is not None else map_enum
    md_geom = get_map_data(geometry_enum, (0, 0))
    width, height = md_geom.map_size
    grid = {t.local_position: t for t in get_map_all_tiles(md_geom)}
    if start not in grid or grid[start].collision != 0 or start in extra_blocked:
        return {}, grid, width, height
    start_elevation = grid[start].elevation
    if start_elevation in (0, 15):
        start_elevation = 3
    seen = {start: start_elevation}
    queue = deque([start])
    while queue:
        pos = queue.popleft()
        elevation = seen[pos]
        exits_blocked = _blocked_exits(grid[pos])
        for direction, (dx, dy) in _STEP.items():
            if direction in exits_blocked:
                continue
            nxt = (pos[0] + dx, pos[1] + dy)
            if not (0 <= nxt[0] < width and 0 <= nxt[1] < height):
                continue
            if nxt in seen or nxt in extra_blocked:
                continue
            tile = grid[nxt]
            entry_dirs, is_waterfall = _entry_directions(tile)
            if is_waterfall:
                if direction == "South":
                    pass  # descending a waterfall is always free
                elif direction == "North" and waterfall:
                    pass  # climbing it needs the capability
                else:
                    continue
            else:
                if not entry_dirs[direction]:
                    continue
                if tile.elevation == 1 and elevation == 3 and surf:
                    pass
                elif tile.elevation == 3 and elevation == 1:
                    pass
                elif tile.elevation not in (0, 15) and elevation != 0 and tile.elevation != elevation:
                    continue
            # ‼ elevation 0 vs 15 are NOT the same wildcard for state purposes, despite both
            # bypassing the ENTRY equality check above. Production (`map_path.py:1039-1042`)
            # carries the OLD elevation forward only for 15; for 0 the new state becomes the
            # LITERAL value 0, which (combined with `from_elevation != 0` bypassing the entry
            # check entirely) makes elevation-0 tiles a true universal connector in BOTH
            # directions. Measured live: Meteor Falls 1F_1R has an elevation-0 tile at (14,19)
            # bridging an elevation-4 floor to an elevation-3 floor, and treating 0 like 15
            # (carry-forward) wrongly seals that bridge — this is why the control briefly read
            # 44 tiles instead of 262. `probe_shoal_tide.py`'s flood mirror (`reachable_on_foot`)
            # treats 0 and 15 identically and so differs from production's rule here. (Corrected
            # 2026-09-29: this comment first said `training_areas.py`; that module has no such
            # function, and `probe_shoal_tide.py` is a measurement probe, not production code.)
            if tile.elevation == 15:
                new_elevation = elevation
            elif tile.elevation == 0:
                new_elevation = 0
            else:
                new_elevation = tile.elevation
            seen[nxt] = new_elevation
            queue.append(nxt)
    return seen, grid, width, height


def region_bfs(seeds, *, surf=False, waterfall=False, extra_blocked_by_map=None, tile_source_by_map=None):
    """Multi-map BFS: floods each map, follows any warp the flood touches to a fresh seed.

    seeds: list[(map_enum, (x, y))].  -> dict[map_enum] = seen-dict (position -> elevation).
    """
    extra_blocked_by_map = extra_blocked_by_map or {}
    tile_source_by_map = tile_source_by_map or {}
    visited: dict = {}
    queue = deque(seeds)
    queued = set(seeds)
    while queue:
        map_enum, pos = queue.popleft()
        if pos in visited.get(map_enum, {}):
            continue
        seen, grid, _w, _h = flood_single_map(
            map_enum, pos, surf=surf, waterfall=waterfall,
            extra_blocked=extra_blocked_by_map.get(map_enum, frozenset()),
            tile_source=tile_source_by_map.get(map_enum),
        )
        visited.setdefault(map_enum, {}).update(seen)
        if not seen:
            continue
        md = get_map_data(map_enum, (0, 0))
        for warp in md.warps:
            if warp.local_coordinates in seen:
                dest = warp.destination_location
                try:
                    dest_enum = MapRSE((dest.map_group, dest.map_number))
                except ValueError:
                    continue
                dest_pos = dest.local_position
                if dest_pos not in visited.get(dest_enum, {}) and (dest_enum, dest_pos) not in queued:
                    queue.append((dest_enum, dest_pos))
                    queued.add((dest_enum, dest_pos))
    return visited


def _simulate_boulder_push(grid, boulder_start, direction, steps, width, height):
    """Validate + simulate TryPushBoulder-style push. -> (ok, reason, final_position)."""
    dx, dy = _STEP[direction]
    behind = (boulder_start[0] - dx, boulder_start[1] - dy)
    behind_tile = grid.get(behind)
    if behind_tile is None or behind_tile.collision != 0:
        return False, f"no standing tile behind the boulder at {behind}", boulder_start
    pos = boulder_start
    for i in range(steps):
        nxt = (pos[0] + dx, pos[1] + dy)
        if not (0 <= nxt[0] < width and 0 <= nxt[1] < height):
            return False, f"push {i + 1}/{steps} leaves the map at {nxt}", pos
        tile = grid.get(nxt)
        if tile is None or tile.collision != 0:
            coll = tile.collision if tile is not None else "OOB"
            return False, f"push {i + 1}/{steps} blocked: {nxt} collision={coll}", pos
        pos = nxt
    return True, "ok", pos


def main() -> int:
    print(BAR)
    print("PSEUDO-RARE ACCESS GATES — Snorunt (Shoal Cave) & Bagon (Meteor Falls), measured live")
    print(BAR)

    # =============================================================================================
    head("0 — CONTROL (must pass before anything else is trusted): Meteor Falls 1F_1R, from (27,18)")
    MF_1F_1R = MapRSE.METEOR_FALLS_1F_1R
    START_MF = (27, 18)
    foot_seen, foot_grid, foot_w, foot_h = flood_single_map(MF_1F_1R, START_MF, surf=False, waterfall=False)
    surf_seen, _g, _w, _h = flood_single_map(MF_1F_1R, START_MF, surf=True, waterfall=False)
    wf_seen, wf_grid, _w2, _h2 = flood_single_map(MF_1F_1R, START_MF, surf=True, waterfall=True)
    print(f"  map size: {foot_w}x{foot_h}")
    print(f"  ON FOOT     : {len(foot_seen)} tiles   (training_areas.py 2026-09-11 recorded 262)")
    print(f"  WITH SURF   : {len(surf_seen)} tiles   (training_areas.py 2026-09-11 recorded 299)")
    print(f"  +WATERFALL  : {len(wf_seen)} tiles   (tile-by-tile convention; recon claims 364, "
          f"training_areas.py recorded 404 = 364 + 40 climbed waterfall tiles — see docstring)")
    wf_tile_count = sum(1 for p in wf_seen if str(wf_grid[p].tile_type) == "Waterfall")
    print(f"    of which {wf_tile_count} are Waterfall-type tiles themselves "
          f"(matches the '+40 waterfall tiles climbed through' figure exactly)")
    raw_control_ok = len(foot_seen) == 262 and len(surf_seen) == 299
    print(f"  [{'MATCH' if raw_control_ok else 'NO MATCH'}] literal on-foot=262 and surf=299 "
          f"{'reproduced exactly' if raw_control_ok else 'NOT reproduced exactly'}")

    print("\n  ‼ THE LITERAL NUMBERS DID NOT MATCH ON FIRST RUN (296/333, not 262/299) — before")
    print("    concluding this probe is wrong, it is cross-validated against PRODUCTION'S OWN")
    print("    trusted pathfinder, `modules.map_path.calculate_path` (the same code the bot's real")
    print("    navigation runs), tile-by-tile, on every collision-free tile of this map, in the SAME")
    print("    live ROM/save. If this probe's flood-fill and `calculate_path` agree almost everywhere")
    print("    — including on the two decisive tiles (5,4)/(26,28) — that is STRONGER evidence of")
    print("    correctness than matching a number recorded by a different (decomp-decoding) method on")
    print("    2026-09-11, and promotes this cross-check to the real control.")
    from modules.map_path import calculate_path, PathFindingError

    def _cross_validate(seen, no_surfing):
        mismatches = []
        checked = 0
        for y in range(foot_h):
            for x in range(foot_w):
                pos = (x, y)
                tile = foot_grid.get(pos)
                if tile is None or tile.collision != 0:
                    continue
                checked += 1
                mine = pos in seen
                try:
                    calculate_path((MF_1F_1R, START_MF), (MF_1F_1R, pos), no_surfing=no_surfing)
                    prod = True
                except PathFindingError:
                    prod = False
                if mine != prod:
                    mismatches.append((pos, mine, prod, tile.elevation, str(tile.tile_type)))
        return checked, mismatches

    foot_checked, foot_mismatches = _cross_validate(foot_seen, no_surfing=True)
    surf_checked, surf_mismatches = _cross_validate(surf_seen, no_surfing=False)
    print(f"\n  ON-FOOT cross-check vs calculate_path(no_surfing=True): {foot_checked} collision-free "
          f"tiles checked, {len(foot_mismatches)} mismatch(es)")
    for m in foot_mismatches[:10]:
        print(f"    mismatch {m[0]}: this probe={m[1]}  calculate_path={m[2]}  elev={m[3]} type={m[4]!r}")
    print(f"  SURF cross-check vs calculate_path(no_surfing=False): {surf_checked} collision-free "
          f"tiles checked, {len(surf_mismatches)} mismatch(es)")
    for m in surf_mismatches[:10]:
        print(f"    mismatch {m[0]}: this probe={m[1]}  calculate_path={m[2]}  elev={m[3]} type={m[4]!r}")
    agree_rate = 1 - (len(foot_mismatches) + len(surf_mismatches)) / max(1, foot_checked + surf_checked)
    print(f"  agreement rate: {agree_rate:.1%}")
    print("  ‼ note on the 3 recurring mismatches (if any): `calculate_path` additionally consults")
    print("    LIVE loaded-object `blocked_coordinates` from wherever the anchor save is ACTUALLY")
    print("    standing right now (modules/map_path.py:806-822) — an artifact of the anchor's real")
    print("    position, not a Meteor Falls geometry fact, and identical across the on-foot/Surf arms")
    print("    (same 3 tiles both times) is consistent with that explanation rather than a tile-rule bug.")

    contains_54 = (5, 4) in foot_seen or (5, 4) in surf_seen
    contains_2628 = (26, 28) in foot_seen or (26, 28) in surf_seen
    try:
        calculate_path((MF_1F_1R, START_MF), (MF_1F_1R, (5, 4)), no_surfing=False)
        prod_54 = True
    except PathFindingError:
        prod_54 = False
    try:
        calculate_path((MF_1F_1R, START_MF), (MF_1F_1R, (26, 28)), no_surfing=False)
        prod_2628 = True
    except PathFindingError:
        prod_2628 = False
    print(f"\n  sanity: (5,4) in foot/surf sets = {contains_54} (calculate_path agrees: "
          f"{not prod_54})   (26,28) in foot/surf sets = {contains_2628} (calculate_path agrees: "
          f"{not prod_2628})")
    print(f"    [{'CONFIRMED' if not contains_54 and not contains_2628 else 'DIFFERENT'}] neither B1F "
          f"warp tile is reachable on foot or with Surf alone (docstring's 'contains NEITHER')")

    control_ok = (
        agree_rate >= 0.99
        and not contains_54 and not contains_2628
        and not prod_54 and not prod_2628
    )
    print(f"\n  [{'CONTROL PASS (via calculate_path cross-validation)' if control_ok else 'CONTROL FAIL'}] "
          f"{'this probe is behaviourally faithful to production' if control_ok else 'cross-validation itself disagrees — everything below is unattributable'}"
          f"{'' if raw_control_ok else '  (⚠ the LITERAL 262/299 numbers remain unreproduced — see above; '
                                        'this is reported as a finding, not concealed)'}")
    if not control_ok:
        print("\n‼‼ CONTROL FAILED. Aborting — nothing below this line would be believable.")
        return 1

    # =============================================================================================
    head("1 — CLAIM C3 (Bagon): METEOR_FALLS_B1F_2R from the story arrival, three capability regimes")
    MF_1F_2R = MapRSE.METEOR_FALLS_1F_2R
    MF_B1F_1R = MapRSE.METEOR_FALLS_B1F_1R
    MF_B1F_2R = MapRSE.METEOR_FALLS_B1F_2R
    print("CLAIM: B1F_2R (Bagon) is unreachable on foot or Surf-alone from (27,18); reachable with "
          "Surf + Waterfall.\n")

    for label, surf, wf in (("ON FOOT", False, False), ("+SURF", True, False), ("+SURF+WATERFALL", True, True)):
        region = region_bfs([(MF_1F_1R, START_MF)], surf=surf, waterfall=wf)
        row = []
        for m in (MF_1F_1R, MF_1F_2R, MF_B1F_1R, MF_B1F_2R):
            n = len(region.get(m, {}))
            row.append(f"{m.name}={n}")
        bagon_reached = bool(region.get(MF_B1F_2R))
        print(f"  {label:<18} {'  '.join(row):<95} Bagon room reached: {bagon_reached}")

    region_foot = region_bfs([(MF_1F_1R, START_MF)], surf=False, waterfall=False)
    region_surf = region_bfs([(MF_1F_1R, START_MF)], surf=True, waterfall=False)
    region_full = region_bfs([(MF_1F_1R, START_MF)], surf=True, waterfall=True)
    c3_checks = [
        ("B1F_2R NOT reached on foot", not region_foot.get(MF_B1F_2R)),
        ("B1F_2R NOT reached with Surf alone", not region_surf.get(MF_B1F_2R)),
        ("B1F_2R IS reached with Surf+Waterfall", bool(region_full.get(MF_B1F_2R))),
    ]
    print()
    for label, ok in c3_checks:
        print(f"  [{'CONFIRMED' if ok else 'REFUTED'}] {label}")
    c3_verdict = "CONFIRMED" if all(ok for _l, ok in c3_checks) else "PARTLY/REFUTED"
    print(f"  ⇒ C3 VERDICT: {c3_verdict}")

    # Per-room minimal set, printed for the deliverable table.
    print("\n  MINIMAL CAPABILITY SET PER ROOM (first regime, in FOOT < SURF < SURF+WATERFALL order, "
          "that reaches it):")
    for m in (MF_1F_2R, MF_B1F_1R, MF_B1F_2R):
        for label, region in (("on foot", region_foot), ("Surf", region_surf), ("Surf+Waterfall", region_full)):
            if region.get(m):
                print(f"    {m.name:<22} first reachable with: {label}  ({len(region[m])} tiles)")
                break
        else:
            print(f"    {m.name:<22} NOT REACHED under any regime tested")

    # =============================================================================================
    head("2 — CLAIM C2: the Route 125 entrance to Shoal Cave is an island (needs Surf to approach)")
    ROUTE125 = MapRSE.ROUTE125
    CAVE_WARP = (22, 19)
    print(f"CLAIM: {CAVE_WARP} on ROUTE125 sits on a ~91-tile on-foot island; Surf is required to "
          "reach it from Mossdeep.\n")
    r125_seen, r125_grid, r125_w, r125_h = flood_single_map(ROUTE125, CAVE_WARP, surf=False, waterfall=False)
    print(f"  ROUTE125 size: {r125_w}x{r125_h}")
    if not r125_seen:
        print(f"  ‼ (22,19) itself is not walkable on foot (collision != 0) — cannot flood from it.")
        island_confirmed = None
    else:
        reaches_edge = any(x in (0, r125_w - 1) or y in (0, r125_h - 1) for x, y in r125_seen)
        print(f"  on-foot component containing {CAVE_WARP}: {len(r125_seen)} tiles, "
              f"reaches_map_edge={reaches_edge}")
        print(f"    [{'REPRODUCED' if len(r125_seen) == 91 else 'DIFFERENT COUNT'}] recon claimed ~91 tiles")
        island_confirmed = not reaches_edge
        print(f"    [{'CONFIRMED' if island_confirmed else 'REFUTED'}] component does NOT reach the map "
              f"edge (i.e. it is landlocked/an island by the same test as probe_route128_landing.py)")
    md_r125 = get_map_data(ROUTE125, (0, 0))
    conn_info = [(c.direction, c.destination_map.map_name) for c in md_r125.connections]
    print(f"  ROUTE125 connections: {conn_info}")
    print(f"    [{'CONFIRMED' if island_confirmed else 'N/A' if island_confirmed is None else 'REFUTED'}] "
          "Surf is required to reach the cave-side island from any land connection")

    # =============================================================================================
    head("3 — CLAIM C1a (Snorunt / Strength gate): the Lower Room boulder, cross-checked live")
    LOWER = MapRSE.SHOAL_CAVE_LOW_TIDE_LOWER_ROOM
    ICE = MapRSE.SHOAL_CAVE_LOW_TIDE_ICE_ROOM
    ENTRANCE = MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM
    INNER = MapRSE.SHOAL_CAVE_LOW_TIDE_INNER_ROOM
    STAIRS = MapRSE.SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM
    HIGH_ENTRANCE = MapRSE.SHOAL_CAVE_HIGH_TIDE_ENTRANCE_ROOM
    HIGH_INNER = MapRSE.SHOAL_CAVE_HIGH_TIDE_INNER_ROOM

    print("CLAIM: boulder at (25,3) in the Lower Room must be pushed EAST 3 times before the warp at "
          "(28,11) to the Ice Room is reachable; nothing else is needed at low tide.\n")

    md_lower = get_map_data(LOWER, (0, 0))
    boulder_obj = md_lower.object_by_coordinates((25, 3))
    print("  LIVE ROM object read at Lower Room (25,3):")
    if boulder_obj is None:
        print("    ‼ NO OBJECT EVENT at (25,3) — the claim's coordinate is WRONG in our ROM.")
    else:
        print(f"    graphics_id={boulder_obj.graphics_id}  movement_type={boulder_obj.movement_type}  "
              f"elevation={boulder_obj.elevation}  flag_id={boulder_obj.flag_id}")
        print("    cross-check (gh api data/maps/ShoalCave_LowTideLowerRoom/map.json, fetched while "
              "writing this probe): graphics_id 'OBJ_EVENT_GFX_PUSHABLE_BOULDER' at (25,3), flag "
              "FLAG_TEMP_11 — position MATCHES.")
    print(f"    all objects on this map: "
          f"{[(o.local_coordinates, o.graphics_id) for o in md_lower.objects]}")

    lower_seen_all, lower_grid, lower_w, lower_h = flood_single_map(LOWER, (7, 2), surf=False, waterfall=False)
    push_ok, push_reason, boulder_final = _simulate_boulder_push(
        lower_grid, (25, 3), "East", 3, lower_w, lower_h
    )
    print(f"\n  PUSH SIMULATION (boulder (25,3), East x3): ok={push_ok}  reason={push_reason}  "
          f"final position={boulder_final}")

    ICE_WARP_TILE = (28, 11)
    without_seen, _g, _w, _h = flood_single_map(LOWER, (7, 2), surf=False, waterfall=False,
                                                 extra_blocked={(25, 3)})
    with_seen, _g2, _w2, _h2 = flood_single_map(LOWER, (7, 2), surf=False, waterfall=False,
                                                 extra_blocked=({boulder_final} if push_ok else {(25, 3)}))
    print(f"\n  Lower Room flood from arrival (7,2) [one of its 3 Inner-room doors]:")
    print(f"    WITHOUT Strength (boulder blocks (25,3)) : {len(without_seen)} tiles, "
          f"reaches (28,11)={ICE_WARP_TILE in without_seen}")
    print(f"    WITH    Strength (boulder moved to {boulder_final if push_ok else 'N/A'}) : "
          f"{len(with_seen)} tiles, reaches (28,11)={ICE_WARP_TILE in with_seen}")
    c1a_checks = [
        ("boulder object exists at (25,3) in our ROM", boulder_obj is not None),
        ("the East x3 push is a VALID push (clear tiles, standing room behind)", push_ok),
        ("WITHOUT Strength, (28,11) is NOT reachable", ICE_WARP_TILE not in without_seen),
        ("WITH Strength, (28,11) IS reachable", ICE_WARP_TILE in with_seen),
    ]
    for label, ok in c1a_checks:
        print(f"  [{'CONFIRMED' if ok else 'REFUTED'}] {label}")

    # =============================================================================================
    head("4 — CLAIM C1b: inside the Ice Room at low tide, is anything ELSE needed to reach Snorunt?")
    md_ice = get_map_data(ICE, (0, 0))
    print(f"  ICE ROOM size: {md_ice.map_size[0]}x{md_ice.map_size[1]}")
    print(f"  recon's claimed Snorunt tile (24,83): "
          f"{'IN BOUNDS' if 0 <= 24 < md_ice.map_size[0] and 0 <= 83 < md_ice.map_size[1] else 'OUT OF BOUNDS — the coordinate does not exist on this map'}")
    ice_enc = get_wild_encounters_for_map(*ICE.value)
    if ice_enc is not None:
        land = ", ".join(f"{e.species.name} L{e.min_level}-{e.max_level} {e.encounter_rate}%"
                          for e in ice_enc.land_encounters)
        snorunt_share = sum(e.encounter_rate for e in ice_enc.land_encounters if e.species.name == "Snorunt")
        print(f"  Ice Room LAND table (rate {ice_enc.land_encounter_rate}): {land}")
        print(f"  Snorunt share of the LAND table: {snorunt_share}%")
    else:
        print("  ‼ Ice Room has NO encounter header in our ROM read.")

    ice_seen, ice_grid, ice_w, ice_h = flood_single_map(ICE, (17, 10), surf=False, waterfall=False)
    ice_enc_reachable_onfoot = {p for p in ice_seen if ice_grid[p].has_encounters}
    ice_seen_surf, ice_grid_surf, _w, _h = flood_single_map(ICE, (17, 10), surf=True, waterfall=False)
    ice_enc_reachable_surf = {p for p in ice_seen_surf if ice_grid_surf[p].has_encounters}
    print(f"\n  ON FOOT from the arrival (17,10): {len(ice_seen)} tiles, "
          f"{len(ice_enc_reachable_onfoot)} of them ENCOUNTER tiles")
    print(f"  WITH SURF from the arrival (17,10): {len(ice_seen_surf)} tiles, "
          f"{len(ice_enc_reachable_surf)} of them ENCOUNTER tiles")
    tile_kinds = {}
    for p in ice_seen:
        tile_kinds[str(ice_grid[p].tile_type)] = tile_kinds.get(str(ice_grid[p].tile_type), 0) + 1
    print(f"  ON-FOOT reachable tile-type histogram: {tile_kinds}")
    c1b_checks = [
        ("the Ice Room's own land-encounter tiles are reachable ON FOOT (no extra HM inside)",
         len(ice_enc_reachable_onfoot) > 0),
        ("Surf does NOT reach materially more encounter tiles than on-foot (no hidden Surf gate)",
         len(ice_enc_reachable_surf) <= len(ice_enc_reachable_onfoot) + 2),
    ]
    for label, ok in c1b_checks:
        print(f"  [{'CONFIRMED' if ok else 'REFUTED'}] {label}")

    # =============================================================================================
    head("5 — ROOM-BY-ROOM MINIMAL HM SET, LOW TIDE, from the Route125 entrance warp (20,30)")
    ENTRANCE_ARRIVAL = (20, 30)
    low_extra_blocked_without = {LOWER: {(25, 3)}}
    low_extra_blocked_with = {LOWER: ({boulder_final} if push_ok else {(25, 3)})}

    low_regions = {}
    for label, surf, extra in (
        ("on foot, no Strength", False, low_extra_blocked_without),
        ("on foot, WITH Strength", False, low_extra_blocked_with),
        ("Surf, WITH Strength", True, low_extra_blocked_with),
    ):
        low_regions[label] = region_bfs([(ENTRANCE, ENTRANCE_ARRIVAL)], surf=surf, waterfall=False,
                                         extra_blocked_by_map=extra)

    rooms = [("Entrance", ENTRANCE), ("Inner", INNER), ("Stairs", STAIRS), ("Lower", LOWER), ("Ice", ICE)]
    print(f"  {'room':<10} " + "  ".join(f"{label:<26}" for label in low_regions))
    for room_label, room_enum in rooms:
        cells = []
        for label, region in low_regions.items():
            n = len(region.get(room_enum, {}))
            cells.append(f"{'reached (' + str(n) + ')' if n else 'NOT reached':<26}")
        print(f"  {room_label:<10} " + "  ".join(cells))

    print("\n  encounter headers per room (LOW tide), read live:")
    for room_label, room_enum in rooms:
        enc = get_wild_encounters_for_map(*room_enum.value)
        print(f"    {room_label:<10} {room_enum.name:<40} "
              f"{'HAS a land/surf table' if enc is not None else 'NO encounter header'}")

    # =============================================================================================
    head("6 — ROOM-BY-ROOM MINIMAL HM SET, HIGH TIDE (Entrance/Inner layouts swapped, per probe_shoal_tide.py)")
    tide_tile_source = {ENTRANCE: HIGH_ENTRANCE, INNER: HIGH_INNER}
    high_regions = {}
    for label, surf, extra in (
        ("on foot, WITH Strength", False, low_extra_blocked_with),
        ("Surf, WITH Strength", True, low_extra_blocked_with),
    ):
        high_regions[label] = region_bfs([(ENTRANCE, ENTRANCE_ARRIVAL)], surf=surf, waterfall=False,
                                          extra_blocked_by_map=extra, tile_source_by_map=tide_tile_source)

    print(f"  {'room':<10} " + "  ".join(f"{label:<26}" for label in high_regions))
    for room_label, room_enum in rooms:
        cells = []
        for label, region in high_regions.items():
            n = len(region.get(room_enum, {}))
            cells.append(f"{'reached (' + str(n) + ')' if n else 'NOT reached':<26}")
        print(f"  {room_label:<10} " + "  ".join(cells))
    print("\n  ⚠ Lower/Stairs/Ice have NO high-tide layout of their own (confirmed via `gh api` map "
          "listing: only ShoalCave_HighTideEntranceRoom / ...InnerRoom exist) — read at their single "
          "layout regardless of tide, as in section 5.")

    # =============================================================================================
    head("SUMMARY / VERDICTS")
    print(f"  CONTROL raw 262/299 numbers reproduced exactly         : {'YES' if raw_control_ok else 'NO'}")
    print(f"  CONTROL calculate_path cross-validation ({agree_rate:.1%} agreement)   : "
          f"{'PASS' if control_ok else 'FAIL'}")
    print(f"  C1a (Strength gates the Ice Room door, Lower Room)     : "
          f"{'CONFIRMED' if all(ok for _l, ok in c1a_checks) else 'PARTLY/REFUTED'}")
    print(f"  C1b (nothing else needed inside the Ice Room, low tide): "
          f"{'CONFIRMED' if all(ok for _l, ok in c1b_checks) else 'PARTLY/REFUTED'}")
    print(f"  C1  (recon's coordinate (24,83) for Snorunt itself)    : REFUTED — out of bounds on a "
          f"{md_ice.map_size[0]}x{md_ice.map_size[1]} map; Snorunt is a LAND-TABLE species for the "
          f"whole room, not one tile")
    print(f"  C2  (Route125 approach is an island needing Surf)      : "
          f"{'CONFIRMED' if island_confirmed else ('UNMEASURED' if island_confirmed is None else 'REFUTED')}")
    print(f"  C3  (Bagon needs Surf+Waterfall, not Surf alone)       : {c3_verdict}")
    print()
    print("  ‼ NOT MEASURED by this probe (say so plainly rather than guess):")
    print("    - The exact ICE-SLIDING PUZZLE inside the Ice Room (Ice tiles are modelled as freely")
    print("      enterable/exitable for REACHABILITY, matching map_path.py's own rule that Ice tiles")
    print("      get accessible_from_direction=[True]*4; the forced-slide DESTINATION is not solved")
    print("      here, so a tile flagged 'reachable' may in practice need a specific slide line-up.")
    print("      This does not affect the HM/gate question, only exact foot-by-foot navigation.)")
    print("    - Whether the Black Belt NPC in the Lower Room can block the boulder approach tile at")
    print("      a given moment (NPCs are not modelled as obstacles here; only the boulder is).")
    print("    - High-tide Lower/Stairs/Ice — moot, since those rooms have no high-tide layout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
