#!/usr/bin/env python3
"""TEST SIDE (P11-1, 2026-11-11): THE WAY THROUGH EVERY DARK CAVE, from the pinned decomp's layouts.

    py -3.12 -B ai_player/gates/extract_ways.py            # writes ai_player/knowledge/world/ways.json from the PINNED clone
    py -3.12 -B ai_player/gates/extract_ways.py --check    # re-extracts in memory; exit 1 if the file differs
    py -3.12 -B ai_player/gates/extract_ways.py --show     # prints every dark map's ways and the walk lengths (no write)

INTENT (USER RULING 40, a SEASONED player; P11-1, `PROJECT KNOWLEDGE/ai-research-notes/2026-11-09-P11-1-DARK-CAVE-DIAGNOSIS.md`
option B): on a DARK map (`requires_flash`: the screen shows only a small lit circle round the player) a person who has
played Emerald before knows the WAY THROUGH at a guide's level: "from the ladder you come down by, the ladder on is east;
on B2F the ladder up is north". They do not know every rock. So this file ships, per dark map and per ladder the player
can ARRIVE by, which ladder (or exit) of that map is the first step of the shortest walk toward each map the cave leads
to, and nothing more: no tile map, no step list, no collision, no route beyond the first ladder (the AI still SEES only
the lit circle, round 7's rule, and its world memory learns only what it saw).

WHY (the diagnosis, measured on #111 against #107): in the dark the explorer had no way to know which of B1F's seven
ladders leads on, so B2F's exit ladder, 8 tiles north of the arrival, was lit only at the END of a 274-349-step blind
search; the extra steps met 3x to 17x the wild battles.

THE MODEL OF A WALK ON FOOT (the game's own rules, pinned decomp; each rule it models is cited, and what it does not model it
REFUSES, below: P11-1's "every one cited" missed the muddy slope, a rule the game applies that the walk did not, so one shipped
way was unreachable on foot, the P11-1 verifier's V1):
  * a map's grid is `data/layouts/<layout>/map.bin` (u16 per tile: metatile id bits 0-9, collision bits 10-11, elevation
    bits 12-15: include/global.fieldmap.h:7-9); a tile's BEHAVIOUR is its metatile's attribute (bits 0-7,
    include/global.fieldmap.h:39) from the layout's primary tileset (ids < 512, include/fieldmap.h:6) or secondary one,
    their `metatile_attributes.bin` found through src/data/tilesets/headers.h and metatiles.h;
  * a step is refused onto a tile with collision != 0, onto surfable water (sTileBitAttributes TILE_FLAG_SURFABLE,
    src/metatile_behavior.c: walking needs no HM here), onto a CRACKED FLOOR (on foot it turns into a hole under the
    player and drops them: src/field_tasks.c CrackedFloorPerStepCallback, src/field_control_avatar.c:512), across a
    one-way wall (src/event_object_movement.c:4697 IsMetatileDirectionallyImpassable with the MetatileBehavior_Is*Blocked
    tables), outside the map (no connection is followed: caves have none), and on an ELEVATION mismatch
    (src/event_object_movement.c:7673 IsElevationMismatchAt; the player's elevation follows ObjectEventUpdateElevation,
    :7725);
  * a LEDGE (MB_JUMP_EAST/WEST/NORTH/SOUTH) is jumped only in its own direction, landing one tile beyond it;
  * (P11-2, 2026-11-11) FORCED MOVEMENT: a player standing on one of the behaviours of src/field_player_avatar.c:144-163
    (sForcedMovementTestFuncs, parsed from the pinned clone with each test's MB_ names from src/metatile_behavior.c:
    `forced_behaviours`) is moved by the GAME before the pad is read (PlayerStep :332-350 calls
    TryDoMetatileBehaviorForcedMovement first; GetForcedMovementByMetatileBehavior :412-427 tests the tile the player
    stands on). The walk models ONE of them, the MUDDY SLOPE: ForcedMovement_MuddySlope (:567-581) moves the player SOUTH
    unless they move north at the Mach Bike's top speed, and on foot GetPlayerSpeed (src/bike.c:1022-1037) is NORMAL or FAST,
    never FASTEST, so ON FOOT A SLOPE ONLY GOES DOWN: a step that lands on a slope slides south, a tile a step, until the
    player stands off the slope, or the tile south refuses them (DoForcedMovement :443-471: a collision stops the forced move
    and the pad moves the player from that tile; a ledge south of it is jumped; a warp south of it is used); a slide onto a
    cracked floor drops the player (no way, as a cracked floor is none). GRANITE CAVE B1F's (9, 9) and (9, 10) are the only
    slope tiles of the dark caves: B1F's north part ((8, 5), (12, 3)) slides down into its south part ((4, 21), (28, 21)) and
    is never reached from it on foot (the project measured it live too: `fixtures/granite_b1f_slope.build.json`);
  * the HM obstacles (OBJ_EVENT_GFX_BREAKABLE_ROCK, OBJ_EVENT_GFX_PUSHABLE_BOULDER, and, P11-2, OBJ_EVENT_GFX_CUTTABLE_TREE
    object events) are walls on foot; every other object (an item ball, a person) is not: people step aside or are walked
    round, items are picked up;
  * stepping onto any WARP tile of the map uses it (ladders warp when stepped on; a door or a cave mouth is entered the
    same way); arriving by a warp puts the player ON its destination warp's tile, at that tile's elevation;
  * the shortest walk is counted in steps (a ledge jump is 2, a slid tile 1); between maps only warps are followed (no
    connection), from each dark map's arrival through every map reachable that way (a cave, its other floors, the place
    outside its mouth and that place's own doors).
WHAT IT DOES NOT MODEL, IT REFUSES (P11-2, the lead's call, `06-DECISIONS-LOG.md` 2026-11-11 "The fix round after BP-1 round 3
and P11-1", item 5): a dark map is LEFT OUT of the file, never shipped as a guess, when the walks its ways are drawn from
(on the dark map and on every map its search goes through)
  * land on a FORCED MOVEMENT behaviour other than the muddy slope (ice, a forced walk, a slide, a current, a waterfall, a
    mat): the walk stops there and the map is refused, naming the behaviour, the map and the tile; or
  * meet an HM obstacle (or water) THAT CHANGES ITS WAYS: the walk does not know which field HMs the player can use, so each
    dark map's search is made twice, ON FOOT and as a player who could use EVERY field HM (`hms`: a rock smashed, a boulder
    gone, a tree cut, every surfable water, current and waterfall tile crossed at any elevation; Dive and connections are
    never followed). That second walk only ever ADDS ways or SHORTENS walks (taking an obstacle away, or opening water, opens
    tiles and closes none; pushing a boulder can only reach what removing it reaches; a forced movement it does not model is
    walked as floor, which reaches every tile a slide would), so when its ways AND its walk lengths equal the on-foot ones,
    no HM the player could hold changes the answer, and the HM obstacles met are modelled exactly as walls; otherwise the map
    is refused, naming the first way that differs and the HM obstacles its walk met. (One case it would not cover, which no
    pinned layout has: a muddy slope above an HM obstacle, where on foot the player rests on the slope and, the obstacle
    gone, slides on. Any difference still refuses the map; only "equal, so no HM matters" would be unproven there.)
  Each refusal is printed (REFUSED, the map and the tile) by every mode of this file, and kept for the developers under
  `_check.left_out`; the HM obstacles each dark map's walk met are under `_check.hm_obstacles`. A map left out is no dark map
  to the AI (`knowledge/ways.py` dark: False), so the explorer decides there exactly as before P11-1. Today: VICTORY ROAD B1F
  and B2F are left out (their ways depend on the HMs; B1F's walk also reaches the Hall of Fame's ice), and so are the three
  unused CAVE OF ORIGIN maps (their ways depend on Surf at SOOTOPOLIS); GRANITE CAVE B1F and B2F are shipped (their walks
  meet B2F's seven breakable rocks, which change none of their ways or walk lengths).
THE WAY OUT OF A DARK MAP toward map D from arrival A is the FIRST warp of map M taken on the shortest such walk from A to
any arrival on D (ties: fewer warps, then the warp's coordinates). Grouped: one entry per (arrival, warp to take) with every
map D it is the way toward. A map D is listed only once per arrival.
THE WAY THROUGH (round 2, 2026-11-11: the first live A/B, #114, found the AI's walk toward STEVEN GOAL-LESS, "by looking
around: not told yet", so a way keyed only on the intent's goal never fired): per arrival, the way toward the FARTHEST map it
leads to (the longest of those shortest walks; ties by the map's name) is marked `through` with that map, what a guide calls
"the way through the cave": from GRANITE CAVE's entrance side it is the way on toward STEVEN's room. (Round 2b) NEVER
STRAIGHT BACK: when that way is the warp the player ARRIVED by (a pocket, a dead end on foot, or the far end already behind:
from B1F (25, 13), down from STEVEN's side, the farthest map is ROUTE 106 back up and over 1F's ledge), there is NO way
through from that arrival (`through` null on all its ways) and the AI's own explorer decides, as before P11-1: marks that
stepped back made a goal-less walk bounce for ever between two ladders (VICTORY ROAD B1F (30, 25) <-> B2F (30, 25); found
by `s53/p11r1/through_cycles.py`, now `test_ways.py` LoaderTests.test_the_way_through_never_steps_back_nor_cycles).

LIMITS (said, not hidden): connections are not followed, so a map reached only across a map's EDGE (DEWFORD from ROUTE 106)
has no entry and the AI falls back to what it knew before (its memory's own route); a dark map's own other part is no
destination (the goal is a MAP); a drop through a cracked floor or a hole is not a way; trainers and people are not walls;
the walk is ON FOOT (a bike climbs the slope and crosses cracked floors at speed: never modelled). The extractor's walk
lengths are printed (`--show`) and kept under `_check` for the developers; the AI never reads them (`gates/check_fairness.py`
classifies `_check` and all under it DEVELOPER, P11-2, so RULE B2 refuses a loader that reads one).

THE OUTPUT (`knowledge/world/ways.json`, classified key by key in `gates/check_fairness.py` RULE B; read by ONE loader,
`knowledge/ways.py`):
  {"_source", "_files" (each input's sha256), "_kind", "_made_by", "_reader", "_notes",
   "_check" (the developers' checks: "walk_lengths", "left_out" (each refused map -> why), "hm_obstacles" (each dark map ->
   the HM obstacles its walk met)),
   "count", "maps": [{"id": "MAP_GRANITE_CAVE_B1F",
                      "ways": [{"from": [4, 21], "take": [28, 21], "leads_to": "MAP_GRANITE_CAVE_B2F",
                                "toward": ["MAP_GRANITE_CAVE_B2F", "MAP_GRANITE_CAVE_STEVENS_ROOM"],
                                "through": "MAP_GRANITE_CAVE_STEVENS_ROOM"}, ...]}, ...]}
("through" is null on every other way of that arrival, and on all of them when the way through would step straight back.)
No key is named x, y, route, path or steps (W6's spirit: a fact, not a script); the coordinates are a pair under "from"
and "take", RULING 45's "coordinates kept" (the same coordinates `maps.json` already holds for every warp).
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from extract_world import Refused, resolve_decomp  # noqa: E402  (the pinned clone, tools/decomp.pin)

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT_DEFAULT = os.path.join(REPO, "ai_player", "knowledge", "world", "ways.json")
MADE_BY = "ai_player/gates/extract_ways.py"
READER = ("read by ONE loader, ai_player/knowledge/ways.py (P11-1): which maps are dark, and per arrival ladder the "
          "ladder to take toward a map; check_fairness.py declares it in LOADERS and classifies every key path of this file "
          "in KNOWLEDGE_FIELDS (`_check` and all under it DEVELOPER, the other `_` keys META: never read)")
NUM_PRIMARY = 512  # include/fieldmap.h:6 NUM_METATILES_IN_PRIMARY
ELEVATION_TRANSITION, ELEVATION_MULTI_LEVEL = 0, 15  # include/global.fieldmap.h (the two special elevations)
#: the HM obstacles (object events): walls on foot; gone in the every-HM walk (`hms`). (P11-2) the cuttable tree added: it
#: was walked through as "another object" (no dark map's walk meets one: they stand on routes and in the woods)
HM_OBSTACLES = ("OBJ_EVENT_GFX_BREAKABLE_ROCK", "OBJ_EVENT_GFX_PUSHABLE_BOULDER", "OBJ_EVENT_GFX_CUTTABLE_TREE")
#: (P11-2) the one FORCED MOVEMENT the walk models (`Grid._forced`): src/field_player_avatar.c:567-581
MUDDY_SLOPE = "MB_MUDDY_SLOPE"
#: at most this many (map, arrival) nodes in one search: every loop is bounded (the whole game has ~1,600 warps)
MAX_NODES = 4000
#: (P11-2) at most this many tiles slid in one forced movement (a slope is a few tiles; the bound only ends a loop)
MAX_SLIDE = 64
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
#: the game's direction -> the behaviours that block LEAVING a tile that way (gOppositeDirectionBlockedMetatileFuncs) and
#: ENTERING a tile that way (gDirectionBlockedMetatileFuncs), src/event_object_movement.c:893-905 with
#: src/metatile_behavior.c MetatileBehavior_Is{North,South,East,West}Blocked
_NORTH = ("MB_IMPASSABLE_NORTH", "MB_IMPASSABLE_NORTHEAST", "MB_IMPASSABLE_NORTHWEST", "MB_IMPASSABLE_SOUTH_AND_NORTH")
_SOUTH = ("MB_IMPASSABLE_SOUTH", "MB_IMPASSABLE_SOUTHEAST", "MB_IMPASSABLE_SOUTHWEST", "MB_IMPASSABLE_SOUTH_AND_NORTH")
_EAST = ("MB_IMPASSABLE_EAST", "MB_IMPASSABLE_NORTHEAST", "MB_IMPASSABLE_SOUTHEAST", "MB_IMPASSABLE_WEST_AND_EAST",
         "MB_SECRET_BASE_BREAKABLE_DOOR")
_WEST = ("MB_IMPASSABLE_WEST", "MB_IMPASSABLE_NORTHWEST", "MB_IMPASSABLE_SOUTHWEST", "MB_IMPASSABLE_WEST_AND_EAST",
         "MB_SECRET_BASE_BREAKABLE_DOOR")
LEAVE_BLOCKED = {"down": _SOUTH, "up": _NORTH, "left": _WEST, "right": _EAST}
ENTER_BLOCKED = {"down": _NORTH, "up": _SOUTH, "left": _EAST, "right": _WEST}
JUMPS = {"MB_JUMP_EAST": "right", "MB_JUMP_WEST": "left", "MB_JUMP_NORTH": "up", "MB_JUMP_SOUTH": "down"}
DIAGONAL_JUMPS = ("MB_JUMP_NORTHEAST", "MB_JUMP_NORTHWEST", "MB_JUMP_SOUTHEAST", "MB_JUMP_SOUTHWEST")
CRACKED = ("MB_CRACKED_FLOOR", "MB_CRACKED_FLOOR_HOLE")


class Source:
    """The pinned clone's files, read once each, every one's sha256 kept for `_files`."""

    def __init__(self, root: str) -> None:
        self.root = root
        self.used: dict[str, str] = {}
        self.sha = resolve_sha(root)

    def raw(self, rel: str) -> bytes:
        with open(os.path.join(self.root, rel), "rb") as handle:
            data = handle.read()
        self.used[rel] = hashlib.sha256(data).hexdigest()
        return data

    def text(self, rel: str) -> str:
        return self.raw(rel).decode("utf-8")


def resolve_sha(root: str) -> str:
    import subprocess
    done = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True)
    return done.stdout.strip() or "unknown"


def _strip(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def behaviours(src: Source) -> tuple[dict[int, str], set[str]]:
    """(number -> MB_ name, the surfable MB_ names): include/constants/metatile_behaviors.h's enum (implicit values from 0)
    and src/metatile_behavior.c's sTileBitAttributes (TILE_FLAG_SURFABLE)."""
    body = _strip(src.text("include/constants/metatile_behaviors.h"))
    enum = body[body.index("enum {") + len("enum {"):body.index("};")]
    names, value = {}, 0
    for item in (part.strip() for part in enum.split(",")):
        if not item:
            continue
        if "=" in item:
            name, _, expr = item.partition("=")
            item, value = name.strip(), int(expr.strip(), 0)
        names[value] = item
        value += 1
    table = _strip(src.text("src/metatile_behavior.c"))
    surfable = set(re.findall(r"\[(MB_\w+)\]\s*=\s*[^,\n]*TILE_FLAG_SURFABLE", table))
    if not surfable or "MB_DEEP_WATER" not in surfable:
        raise Refused("src/metatile_behavior.c: no TILE_FLAG_SURFABLE behaviour found (the table moved?)")
    return names, surfable


def forced_behaviours(src: Source) -> frozenset[str]:
    """(P11-2) Every behaviour the game moves a player standing on: the tests of src/field_player_avatar.c's
    sForcedMovementTestFuncs (:144-163), each test's MB_ names read from its body in src/metatile_behavior.c. Refused when
    the table or a test cannot be read, or when the muddy slope is not among them (the code moved: the model would guess)."""
    player = _strip(src.text("src/field_player_avatar.c"))
    table = re.search(r"sForcedMovementTestFuncs\s*\[[^\]]*\]\s*\)\s*\(u8\)\s*=\s*\{(.*?)\};", player, flags=re.S)
    if table is None:
        raise Refused("src/field_player_avatar.c: no sForcedMovementTestFuncs table (the code moved?)")
    tests = re.findall(r"\b(\w+)\b", table.group(1))
    behaviour_c = _strip(src.text("src/metatile_behavior.c"))
    out: set[str] = set()
    for test in tests:
        body = re.search(r"bool8\s+" + re.escape(test) + r"\s*\(u8\s+\w+\)\s*\{(.*?)\n\}", behaviour_c, flags=re.S)
        found = set(re.findall(r"\bMB_\w+", body.group(1))) if body else set()
        if not found:
            raise Refused(f"src/metatile_behavior.c: the forced-movement test {test} names no MB_ behaviour")
        out |= found
    if MUDDY_SLOPE not in out:
        raise Refused("src/field_player_avatar.c: the muddy slope is no forced movement (the code moved?)")
    return frozenset(out)


def tileset_attributes(src: Source) -> dict[str, str]:
    """gTileset_X -> the path of its metatile_attributes.bin (src/data/tilesets/headers.h, metatiles.h)."""
    headers = src.text("src/data/tilesets/headers.h")
    metatiles = src.text("src/data/tilesets/metatiles.h")
    attr_paths = dict(re.findall(r"const u16 (gMetatileAttributes_\w+)\[\] = INCBIN_U16\(\"([^\"]+)\"\)", metatiles))
    out = {}
    for name, block in re.findall(r"const struct Tileset (gTileset_\w+) =\s*\{(.*?)\};", headers, flags=re.S):
        found = re.search(r"\.metatileAttributes = (gMetatileAttributes_\w+)", block)
        if found and found.group(1) in attr_paths:
            out[name] = attr_paths[found.group(1)]
    return out


class Grid:
    """One map's layout as the game reads it: per tile (collision, elevation, behaviour name), its warps, and the HM
    obstacles standing on it (`walls`: tile -> the obstacle's graphics)."""

    def __init__(self, entry: dict, layout: dict, src: Source, attrs: dict[str, str], names: dict[int, str],
                 attr_cache: dict[str, list[int]], forced: frozenset[str] = frozenset()) -> None:
        self.id = entry["id"]
        self.forced = forced
        self.width, self.height = int(layout["width"]), int(layout["height"])
        raw = src.raw(layout["blockdata_filepath"])
        values = [raw[i] | raw[i + 1] << 8 for i in range(0, len(raw), 2)]
        if len(values) != self.width * self.height:
            raise Refused(f"{layout['blockdata_filepath']}: {len(values)} tiles, not {self.width}x{self.height}")

        def table(tileset: str) -> list[int]:
            path = attrs.get(tileset)
            if path is None:
                raise Refused(f"no metatile attributes found for {tileset}")
            if path not in attr_cache:
                data = src.raw(path)
                attr_cache[path] = [data[i] | data[i + 1] << 8 for i in range(0, len(data), 2)]
            return attr_cache[path]

        primary, secondary = table(layout["primary_tileset"]), table(layout["secondary_tileset"])
        self.collision: dict[tuple[int, int], int] = {}
        self.elevation: dict[tuple[int, int], int] = {}
        self.behaviour: dict[tuple[int, int], str] = {}
        for index, value in enumerate(values):
            xy = (index % self.width, index // self.width)
            metatile = value & 0x03FF
            attr = primary[metatile] if metatile < NUM_PRIMARY else (
                secondary[metatile - NUM_PRIMARY] if metatile - NUM_PRIMARY < len(secondary) else 0)
            self.collision[xy] = (value & 0x0C00) >> 10
            self.elevation[xy] = (value & 0xF000) >> 12
            self.behaviour[xy] = names.get(attr & 0x00FF, f"MB_{attr & 0xFF}")
        self.warps = [((int(w["x"]), int(w["y"])), str(w["dest_map"]), str(w["dest_warp_id"]))
                      for w in entry.get("warp_events") or []]
        self.warp_at = {}
        for index, (xy, _, _) in enumerate(self.warps):
            self.warp_at.setdefault(xy, index)
        self.walls = {(int(o["x"]), int(o["y"])): str(o["graphics_id"]) for o in entry.get("object_events") or []
                      if o.get("graphics_id") in HM_OBSTACLES}

    def inside(self, xy: tuple[int, int]) -> bool:
        return 0 <= xy[0] < self.width and 0 <= xy[1] < self.height

    def _walled(self, xy: tuple[int, int], hms: bool, met: set | None) -> bool:
        """(P11-2) Does an HM obstacle stand on `xy` and stop this walk? On foot yes (and it is recorded in `met` as met on the
        walk); in the every-HM walk (`hms`) it is gone."""
        if xy not in self.walls:
            return False
        if met is not None:
            met.add(("hm", self.id, xy, self.walls[xy]))
        return not hms

    def enter(self, here: tuple[int, int], elev: int, direction: str, surfable: set[str], hms: bool = False,
              met: set | None = None) -> tuple[tuple[int, int], int, int] | None:
        """One press of `direction` from `here` at elevation `elev` on foot: (the tile it ends on, the elevation then, its
        cost), or None when the game refuses it. A warp tile is entered whatever its collision (it is used). (P11-2) A step
        that lands on a forced-movement behaviour is moved on by the game (`_forced`). `hms`: the every-HM walk (module
        docstring); `met`: collects what the walk met that it judges (an HM obstacle, a forced movement it does not model)."""
        dx, dy = DIRS[direction]
        nxt = (here[0] + dx, here[1] + dy)
        if not self.inside(nxt):
            return None
        if self.behaviour[here] in LEAVE_BLOCKED[direction]:
            return None
        if nxt in self.warp_at and (nxt not in self.walls or hms):
            return nxt, elev, 1
        behaviour = self.behaviour[nxt]
        if behaviour in JUMPS:
            if JUMPS[behaviour] != direction:
                return None
            land = (nxt[0] + dx, nxt[1] + dy)
            if not self.inside(land) or self._walled(land, hms, met):
                return None
            if land in self.warp_at:
                return land, elev, 2
            if not self._open(land, elev, direction, surfable, hms):
                return None
            return self._forced(land, self._after(nxt, land, elev), 2, surfable, hms, met)
        from_water = hms and self.behaviour[here] in surfable
        if behaviour in DIAGONAL_JUMPS or self._walled(nxt, hms, met) or not self._open(nxt, elev, direction, surfable, hms,
                                                                                         from_water):
            return None
        return self._forced(nxt, self._after(here, nxt, elev), 1, surfable, hms, met)

    def _forced(self, tile: tuple[int, int], elev: int, cost: int, surfable: set[str], hms: bool,
                met: set | None) -> tuple[tuple[int, int], int, int] | None:
        """(P11-2) Where the GAME moves a player who has just stepped onto `tile` (module docstring, FORCED MOVEMENT): a muddy
        slope slides them south (src/field_player_avatar.c:567-581) until off it or refused (:443-471: a collision ends the
        forced move, a ledge south is jumped, a warp south is used); a slide onto a cracked floor is a drop (None). Any OTHER
        forced-movement behaviour is not modelled: it is recorded in `met` and, on foot, the walk stops (None) and the
        extractor refuses the map; the every-HM walk walks on over it (it only looks for MORE ways)."""
        for _ in range(MAX_SLIDE):
            behaviour = self.behaviour[tile]
            if behaviour not in self.forced:
                return tile, elev, cost
            if behaviour != MUDDY_SLOPE:
                if met is not None:
                    met.add(("forced", self.id, tile, behaviour))
                return (tile, elev, cost) if hms else None
            below = (tile[0], tile[1] + 1)
            if not self.inside(below):
                return tile, elev, cost
            if below in self.warp_at and (below not in self.walls or hms):
                return below, elev, cost + 1
            if self._walled(below, hms, met):
                return tile, elev, cost
            under = self.behaviour[below]
            if under in JUMPS:
                land = (below[0], below[1] + 1)
                if JUMPS[under] != "down" or not self.inside(land) or self._walled(land, hms, met):
                    return tile, elev, cost
                if land in self.warp_at:
                    return land, elev, cost + 2
                if not self._open(land, elev, "down", surfable, hms):
                    return tile, elev, cost
                tile, elev, cost = land, self._after(below, land, elev), cost + 2
                continue
            if under in CRACKED and not hms:
                return None
            if under in DIAGONAL_JUMPS or not self._open(below, elev, "down", surfable, hms):
                return tile, elev, cost
            tile, elev, cost = below, self._after(tile, below, elev), cost + 1
        raise Refused(f"{self.id}: a forced movement from {tile} slid more than {MAX_SLIDE} tiles")

    def _open(self, xy: tuple[int, int], elev: int, direction: str, surfable: set[str], hms: bool = False,
              from_water: bool = False) -> bool:
        behaviour = self.behaviour[xy]
        if hms and behaviour in surfable:
            return True  # (P11-2, the every-HM walk) any water, current or waterfall tile is crossed, at any elevation
        if self.collision[xy] != 0 or behaviour in surfable or behaviour in CRACKED or behaviour in ENTER_BLOCKED[direction]:
            return False
        if from_water:
            return True  # (P11-2, the every-HM walk) off the water onto any open tile, at any elevation
        tile = self.elevation[xy]
        # IsElevationMismatchAt (src/event_object_movement.c:7673)
        return elev == ELEVATION_TRANSITION or tile in (ELEVATION_TRANSITION, ELEVATION_MULTI_LEVEL) or tile == elev

    def _after(self, prev: tuple[int, int], cur: tuple[int, int], elev: int) -> int:
        """ObjectEventUpdateElevation (src/event_object_movement.c:7725)."""
        now, before = self.elevation[cur], self.elevation[prev]
        if now == ELEVATION_MULTI_LEVEL or before == ELEVATION_MULTI_LEVEL:
            return elev
        return now

    def walks_from(self, start: tuple[int, int], surfable: set[str], hms: bool = False) -> tuple[dict[int, int], frozenset]:
        """(warp index -> the fewest steps from standing on `start` (an arrival warp's tile) onto that warp (the start's own
        warp included: stepped off and back on), what the walk met (`enter`)). Dijkstra over (tile, elevation); bounded by
        the map's tiles x 16. `hms`: the every-HM walk."""
        origin = (start, self.elevation[start])
        best = {origin: 0}
        queue = [(0, start[1], start[0], origin[1])]
        found: dict[int, int] = {}
        met: set = set()
        while queue:
            cost, y, x, elev = heapq.heappop(queue)
            here = (x, y)
            if cost > best.get((here, elev), 1 << 30):
                continue
            for direction in DIRS:
                step = self.enter(here, elev, direction, surfable, hms, met)
                if step is None:
                    continue
                nxt, nelev, extra = step
                total = cost + extra
                if nxt in self.warp_at:
                    # a warp tile is USED on stepping onto it (the start's own too, stepped off and back on): no walk goes
                    # on from it, so it is recorded, never searched from
                    index = self.warp_at[nxt]
                    found[index] = min(found.get(index, total), total)
                    continue
                if total < best.get((nxt, nelev), 1 << 30):
                    best[(nxt, nelev)] = total
                    heapq.heappush(queue, (total, nxt[1], nxt[0], nelev))
        return found, frozenset(met)


def load_world(src: Source) -> tuple[dict[str, dict], dict[str, dict]]:
    """(map id -> its map.json, layout id -> its layouts.json entry)."""
    maps = {}
    base = os.path.join(src.root, "data", "maps")
    for folder in sorted(os.listdir(base)):
        rel = f"data/maps/{folder}/map.json"
        if os.path.isfile(os.path.join(src.root, rel)):
            entry = json.loads(src.text(rel))
            maps[str(entry["id"])] = entry
    layouts = {str(l["id"]): l for l in json.loads(src.text("data/layouts/layouts.json"))["layouts"] if "id" in l}
    return maps, layouts


def _met_text(item: tuple) -> str:
    _kind, map_id, tile, what = item
    return f"{what} at {tuple(tile)} on {map_id}"


def refusals(foot: tuple[list, dict, set], with_hms: tuple[list, dict, set]) -> list[str]:
    """(P11-2) Why a dark map's ways are not shipped (module docstring, WHAT IT DOES NOT MODEL, IT REFUSES): [] when the
    on-foot walk met no forced movement it does not model AND the every-HM walk gives the same ways and walk lengths."""
    ways, lengths, met = foot
    out: list[str] = []
    forced = sorted((m for m in met if m[0] == "forced"), key=lambda m: (m[1], m[2], m[3]))
    if forced:
        more = f" (and {len(forced) - 1} more forced-movement tile(s))" if len(forced) > 1 else ""
        out.append(f"FORCED MOVEMENT its walk does not model: {_met_text(forced[0])}{more}")
    hm_ways, hm_lengths, _hm_met = with_hms
    if hm_ways != ways or hm_lengths != lengths:
        first = next((f"from {tuple(w['from'])} on foot take {tuple(w['take'])} toward {w['toward']} through {w['through']}"
                      for w in ways if w not in hm_ways), None)
        if first is None:
            first = next((f"with every HM a way from {tuple(w['from'])} take {tuple(w['take'])} toward {w['toward']}"
                          for w in hm_ways if w not in ways), None)
        if first is None:
            key = next(k for k in sorted(set(lengths) | set(hm_lengths)) if lengths.get(k) != hm_lengths.get(k))
            first = f"the walk {key}: {lengths.get(key)} steps on foot, {hm_lengths.get(key)} with every HM"
        obstacles = sorted({_met_text(m) for m in met if m[0] == "hm"})
        shown = "; ".join(obstacles[:3]) + (f" (and {len(obstacles) - 3} more)" if len(obstacles) > 3 else "")
        out.append(f"HMs: its ways depend on the HMs the player can use, which the walk does not know: {first}; the HM "
                   f"obstacles its walk on foot met: {shown or 'none (water: Surf, Waterfall)'}")
    return out


def extract(root: str) -> tuple[dict, dict]:
    """(the ways.json document, the developers' check: every shipped way's walk length)."""
    src = Source(root)
    names, surfable = behaviours(src)
    forced = forced_behaviours(src)
    attrs = tileset_attributes(src)
    maps, layouts = load_world(src)
    grids: dict[str, Grid] = {}
    attr_cache: dict[str, list[int]] = {}

    def grid(map_id: str) -> Grid | None:
        if map_id not in grids:
            entry = maps.get(map_id)
            layout = layouts.get(str(entry.get("layout"))) if entry else None
            if entry is None or layout is None or "blockdata_filepath" not in layout:
                return None
            grids[map_id] = Grid(entry, layout, src, attrs, names, attr_cache, forced)
        return grids[map_id]

    walks: dict[tuple[str, int, bool], tuple[dict[int, int], frozenset]] = {}

    def walks_of(map_id: str, arrival: int, hms: bool) -> tuple[dict[int, int], frozenset]:
        key = (map_id, arrival, hms)
        if key not in walks:
            g = grid(map_id)
            walks[key] = ({}, frozenset()) if g is None or arrival >= len(g.warps) else g.walks_from(
                g.warps[arrival][0], surfable, hms)
        return walks[key]

    def search(map_id: str, arrival: int, hms: bool) -> tuple[dict[str, tuple[int, int, tuple[int, int], int]], set]:
        """Dijkstra over (map, the warp arrived on); the first warp taken on `map_id` is carried with each node. Returns
        (each map reached -> (its walk, warps, the tie, the first warp)), and everything its walks met."""
        best = {(map_id, arrival): (0, 0)}
        queue = [(0, 0, (0, 0), map_id, arrival, -1)]
        reached: dict[str, tuple[int, int, tuple[int, int], int]] = {}
        met: set = set()
        popped = 0
        here_root = grid(map_id)
        while queue and popped < MAX_NODES:
            cost, hops, tie, here_map, here_warp, first = heapq.heappop(queue)
            if (cost, hops) > best.get((here_map, here_warp), (1 << 30, 0)):
                continue
            popped += 1
            if here_map != map_id and here_map not in reached:
                reached[here_map] = (cost, hops, tie, first)
            here_grid = grid(here_map)
            if here_grid is None:
                continue
            found, seen = walks_of(here_map, here_warp, hms)
            met |= seen
            for taken, steps in sorted(found.items()):
                _, dest_map, dest_id = here_grid.warps[taken]
                if not dest_id.isdigit() or dest_map in ("MAP_DYNAMIC", "MAP_NONE"):
                    continue
                nfirst = taken if first < 0 else first
                ntie = here_grid.warps[nfirst][0] if first < 0 else tie
                node = (dest_map, int(dest_id))
                score = (cost + steps, hops + 1)
                if score < best.get(node, (1 << 30, 0)):
                    best[node] = score
                    heapq.heappush(queue, (cost + steps, hops + 1, (ntie[1], ntie[0]) if first < 0 else tie,
                                           dest_map, int(dest_id), nfirst))
        if popped >= MAX_NODES:
            at = here_root.warps[arrival][0] if here_root is not None else arrival
            raise Refused(f"{map_id} from warp {arrival} at {at}: the search passed {MAX_NODES} nodes")
        return reached, met

    def ways_of(map_id: str, hms: bool) -> tuple[list, dict, set]:
        """(the ways of dark map `map_id`, their walk lengths, everything its walks met), on foot or with every HM."""
        g = grid(map_id)
        ways: list = []
        lengths: dict[str, int] = {}
        met: set = set()
        for arrival, (at, _, _) in enumerate(g.warps):
            reached, seen = search(map_id, arrival, hms)
            met |= seen
            grouped: dict[int, list[str]] = {}
            for dest, (cost, hops, _, first) in reached.items():
                grouped.setdefault(first, []).append(dest)
                lengths[f"{map_id}|{at[0]},{at[1]}|{dest}"] = cost
            # THE WAY THROUGH (round 2, 2026-11-11): the way toward the FARTHEST map this arrival leads to (the cave's far
            # end: GRANITE CAVE's is STEVEN's room from the entrance, the way out from his side), ties by the map's name
            far = max(reached.items(), key=lambda item: (item[1][0], item[0]))[0] if reached else None
            # (round 2b, 2026-11-11) NEVER STRAIGHT BACK: no way through when the farthest map's first step is the warp the
            # player ARRIVED by (a pocket or a dead end on foot, or the cave's far end already behind them). Following such
            # marks from arrival to arrival bounced for ever (VICTORY ROAD B1F (30, 25) <-> B2F (30, 25), GRANITE CAVE's
            # (29, 2) pocket: 11 starts of 29 ended in a cycle, `s53/p11r1/through_cycles.py`); there the AI's own explorer
            # decides, as before P11-1. GRANITE CAVE's crossing (4, 21) -> (28, 21) -> (29, 13) -> (25, 13) never steps back
            if far is not None and reached[far][3] == arrival:
                far = None
            for first, dests in sorted(grouped.items(), key=lambda item: g.warps[item[0]][0]):
                take, leads_to, _ = g.warps[first]
                ways.append({"from": [at[0], at[1]], "take": [take[0], take[1]], "leads_to": leads_to,
                             "toward": sorted(dests), "through": far if far in dests else None})
        return ways, lengths, met

    dark = sorted(map_id for map_id, entry in maps.items() if entry.get("requires_flash") is True)
    out_maps, check, left_out, obstacles = [], {}, {}, {}
    for map_id in dark:
        if grid(map_id) is None:
            raise Refused(f"{map_id}: requires_flash but no layout")
        foot = ways_of(map_id, False)
        # (P11-2) WHAT IT DOES NOT MODEL, IT REFUSES (module docstring): the map is left out, never shipped as a guess
        why = refusals(foot, ways_of(map_id, True))
        obstacles[map_id] = sorted({_met_text(m) for m in foot[2] if m[0] == "hm"})
        if why:
            left_out[map_id] = why
            continue
        out_maps.append({"id": map_id, "ways": foot[0]})
        check.update(foot[1])
    doc = {
        "_source": "pret/pokeemerald@" + src.sha,
        "_files": {p: src.used[p] for p in sorted(src.used)},
        "_kind": "static game knowledge (USER RULING 40): the way through each dark cave, a guide's level",
        "_made_by": MADE_BY,
        "_reader": READER,
        "_notes": ("per dark map (requires_flash), per warp the player can arrive by ('from'), the warp to take ('take', "
                   "leading to 'leads_to') as the first step of the shortest walk on foot toward each map in 'toward'; warps "
                   "only, no connection; HM obstacles are walls; a cracked floor is no way; a muddy slope only goes down; a "
                   "dark map whose walk meets a forced movement the walk does not model, or whose ways depend on the HMs, is "
                   "LEFT OUT (_check.left_out; see the extractor's docstring)"),
        "_check": {"walk_lengths": dict(sorted(check.items())), "left_out": dict(sorted(left_out.items())),
                   "hm_obstacles": dict(sorted(obstacles.items()))},
        "count": len(out_maps),
        "maps": out_maps,
    }
    return doc, check


def dump(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def loud(doc: dict) -> list[str]:
    """(P11-2) The refusals, one line each, as every mode prints them (module docstring)."""
    return [f"REFUSED {map_id}: {why}" for map_id, reasons in doc["_check"]["left_out"].items() for why in reasons]


#: (test side) the dark floors the grid MODEL of `gates/test_ways.py` is drawn from (`model`)
MODEL_MAPS = ("MAP_GRANITE_CAVE_B1F", "MAP_GRANITE_CAVE_B2F")
FIXTURE_DEFAULT = os.path.join(HERE, "fixtures", "granite_dark_model.json")
_LEDGE_CHARS = {"down": "v", "right": ">", "left": "<", "up": "^"}


def model(root: str) -> dict:
    """(TEST SIDE ONLY: never read by the AI) GRANITE CAVE B1F and B2F as `gates/test_world.py` GridGame rows, drawn by the
    SAME walk rules as the ways: a warp is 'S' (stepped on, it warps), a ledge its direction's character, a tile no walk on
    foot enters ('#': collision, water, a cracked floor, an HM obstacle) a wall, the rest floor '.'; and each warp's
    destination. Elevation is uniform on these floors (every walkable tile 3, every wall 0: `--show` prints it) so the
    model leaves it out. (P11-2, the verifier's V1) A MUDDY SLOPE only goes down on foot (`Grid._forced`): GridGame has no
    slope, so a slope column is drawn as a SOUTH LEDGE 'v' at its top tile and floor below it: stepped onto from above, the
    player lands on the tile under the ledge and walks on down; from below it is refused, as the game's slope slides them
    back. That is the game's one way only when no side of the column is open and the tile under it is floor: any other
    slope is REFUSED (never drawn as a guess). The unit A/B in `test_ways.py` ModelTests walks the real explorer through it
    in the dark."""
    src = Source(root)
    names, surfable = behaviours(src)
    forced = forced_behaviours(src)
    attrs = tileset_attributes(src)
    maps, layouts = load_world(src)
    out: dict = {"_made_by": MADE_BY + " --fixture", "_source": "pret/pokeemerald@" + src.sha,
                 "_what": "test-side grid model of the dark floors (gates/test_ways.py); never read by the AI", "maps": {}}
    for map_id in MODEL_MAPS:
        g = Grid(maps[map_id], layouts[maps[map_id]["layout"]], src, attrs, names, {}, forced)
        elevations = set()
        rows = []
        for y in range(g.height):
            row = ""
            for x in range(g.width):
                xy = (x, y)
                behaviour = g.behaviour[xy]
                if xy in g.warp_at:
                    row += "S"
                elif behaviour in JUMPS:
                    row += _LEDGE_CHARS[JUMPS[behaviour]]
                elif behaviour == MUDDY_SLOPE and g.behaviour.get((x, y - 1)) != MUDDY_SLOPE:
                    row += "v"  # (P11-2) the top of a slope column: one way, down (the docstring)
                elif behaviour in forced and behaviour != MUDDY_SLOPE:
                    raise Refused(f"{map_id}: forced movement {behaviour} at {xy}, which the model does not draw")
                elif (g.collision[xy] != 0 or behaviour in surfable or behaviour in CRACKED or xy in g.walls
                      or behaviour in DIAGONAL_JUMPS):
                    row += "#"
                else:
                    row += "."
                    elevations.add(g.elevation[xy])
            rows.append(row)
        for (x, y), behaviour in sorted(g.behaviour.items()):
            if behaviour != MUDDY_SLOPE:
                continue
            sides = [rows[y][x + dx] if 0 <= x + dx < g.width else "#" for dx in (-1, 1)]
            bottom = y + 1
            while bottom < g.height and g.behaviour[(x, bottom)] == MUDDY_SLOPE:
                bottom += 1
            if sides != ["#", "#"] or bottom >= g.height or rows[bottom][x] != ".":
                raise Refused(f"{map_id}: the muddy slope at {(x, y)} has an open side or no floor under its column: the "
                              f"model cannot draw its one way faithfully")
        if not elevations <= {3}:
            raise Refused(f"{map_id}: the model leaves elevation out, but its floor has elevations {sorted(elevations)}")
        out["maps"][map_id.removeprefix("MAP_")] = {
            "rows": rows,
            "warps": [[xy[0], xy[1], dest.removeprefix("MAP_"), int(dest_id)] for xy, dest, dest_id in g.warps]}
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--decomp", help="a pinned clone elsewhere (its HEAD must equal tools/decomp.pin)")
    parser.add_argument("--out", default=OUT_DEFAULT)
    parser.add_argument("--check", action="store_true", help="re-extract; exit 1 if the file differs")
    parser.add_argument("--show", action="store_true", help="print the ways and walk lengths; write nothing")
    parser.add_argument("--fixture", default=FIXTURE_DEFAULT, help="(test side) the grid model's file (`model`)")
    args = parser.parse_args()
    try:
        root = resolve_decomp(args.decomp)
        doc, check = extract(root)
        fixture = dump(model(root))
    except Refused as error:
        print(f"REFUSED: {error}")
        return 2
    text = dump(doc)
    for line in loud(doc):
        print(line)
    if args.show:
        for entry in doc["maps"]:
            print(entry["id"])
            for way in entry["ways"]:
                lengths = {d: check.get(f"{entry['id']}|{way['from'][0]},{way['from'][1]}|{d}") for d in way["toward"]}
                print(f"  from {tuple(way['from'])} take {tuple(way['take'])} -> {way['leads_to']}: {lengths}")
        return 0
    if args.check:
        verdicts = []
        for path, want in ((args.out, text), (args.fixture, fixture)):
            try:
                with open(path, encoding="utf-8") as handle:
                    old = handle.read()
            except OSError:
                old = None
            verdicts.append(old == want)
            print(f"extract_ways --check: {'SAME' if old == want else 'DIFFERS'} ({path})")
        print(f"{doc['count']} dark maps shipped, {len(doc['_check']['left_out'])} left out")
        return 0 if all(verdicts) else 1
    for path, body in ((args.out, text), (args.fixture, fixture)):
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    print(f"wrote {args.out}: {doc['count']} dark maps, {sum(len(m['ways']) for m in doc['maps'])} ways "
          f"({len(doc['_check']['left_out'])} left out); and the test side's model {args.fixture}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
