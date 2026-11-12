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

THE MODEL OF A WALK ON FOOT (the game's own rules, pinned decomp; every one cited):
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
  * the HM obstacles (OBJ_EVENT_GFX_BREAKABLE_ROCK, OBJ_EVENT_GFX_PUSHABLE_BOULDER object events) are walls; every other
    object (an item ball, a person) is not: people step aside or are walked round, items are picked up;
  * stepping onto any WARP tile of the map uses it (ladders warp when stepped on; a door or a cave mouth is entered the
    same way); arriving by a warp puts the player ON its destination warp's tile, at that tile's elevation;
  * the shortest walk is counted in steps (a ledge jump is 2); between maps only warps are followed (no connection), from
    each dark map's arrival through every map reachable that way (a cave, its other floors, the place outside its mouth
    and that place's own doors).
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
destination (the goal is a MAP); a drop through a cracked floor or a hole is not a way; an HM obstacle is a wall; trainers and
people are not walls. The extractor's walk lengths are printed (`--show`) and kept under `_check` for the developers; the AI
never reads them.

THE OUTPUT (`knowledge/world/ways.json`, classified key by key in `gates/check_fairness.py` RULE B; read by ONE loader,
`knowledge/ways.py`):
  {"_source", "_files" (each input's sha256), "_kind", "_made_by", "_reader", "_notes", "_check" (walk lengths),
   "count", "maps": [{"id": "MAP_GRANITE_CAVE_B1F",
                      "ways": [{"from": [4, 21], "take": [28, 21], "leads_to": "MAP_GRANITE_CAVE_B2F",
                                "toward": ["MAP_GRANITE_CAVE_STEVENS_ROOM", ...],
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
          "in KNOWLEDGE_FIELDS (`_check` and the other `_` keys are the developers' meta, never read)")
NUM_PRIMARY = 512  # include/fieldmap.h:6 NUM_METATILES_IN_PRIMARY
ELEVATION_TRANSITION, ELEVATION_MULTI_LEVEL = 0, 15  # include/global.fieldmap.h (the two special elevations)
HM_OBSTACLES = ("OBJ_EVENT_GFX_BREAKABLE_ROCK", "OBJ_EVENT_GFX_PUSHABLE_BOULDER")
#: at most this many (map, arrival) nodes in one search: every loop is bounded (the whole game has ~1,600 warps)
MAX_NODES = 4000
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
    obstacles standing on it."""

    def __init__(self, entry: dict, layout: dict, src: Source, attrs: dict[str, str], names: dict[int, str],
                 attr_cache: dict[str, list[int]]) -> None:
        self.id = entry["id"]
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
        self.walls = {(int(o["x"]), int(o["y"])) for o in entry.get("object_events") or []
                      if o.get("graphics_id") in HM_OBSTACLES}

    def inside(self, xy: tuple[int, int]) -> bool:
        return 0 <= xy[0] < self.width and 0 <= xy[1] < self.height

    def enter(self, here: tuple[int, int], elev: int, direction: str, surfable: set[str]) -> tuple[tuple[int, int], int, int] | None:
        """One press of `direction` from `here` at elevation `elev` on foot: (the tile it ends on, the elevation then, its
        cost), or None when the game refuses it. A warp tile is entered whatever its collision (it is used)."""
        dx, dy = DIRS[direction]
        nxt = (here[0] + dx, here[1] + dy)
        if not self.inside(nxt):
            return None
        if self.behaviour[here] in LEAVE_BLOCKED[direction]:
            return None
        if nxt in self.warp_at and nxt not in self.walls:
            return nxt, elev, 1
        behaviour = self.behaviour[nxt]
        if behaviour in JUMPS:
            if JUMPS[behaviour] != direction:
                return None
            land = (nxt[0] + dx, nxt[1] + dy)
            if not self.inside(land) or land in self.walls:
                return None
            if land in self.warp_at:
                return land, elev, 2
            if not self._open(land, elev, direction, surfable):
                return None
            return land, self._after(nxt, land, elev), 2
        if behaviour in DIAGONAL_JUMPS or nxt in self.walls or not self._open(nxt, elev, direction, surfable):
            return None
        return nxt, self._after(here, nxt, elev), 1

    def _open(self, xy: tuple[int, int], elev: int, direction: str, surfable: set[str]) -> bool:
        behaviour = self.behaviour[xy]
        if self.collision[xy] != 0 or behaviour in surfable or behaviour in CRACKED or behaviour in ENTER_BLOCKED[direction]:
            return False
        tile = self.elevation[xy]
        # IsElevationMismatchAt (src/event_object_movement.c:7673)
        return elev == ELEVATION_TRANSITION or tile in (ELEVATION_TRANSITION, ELEVATION_MULTI_LEVEL) or tile == elev

    def _after(self, prev: tuple[int, int], cur: tuple[int, int], elev: int) -> int:
        """ObjectEventUpdateElevation (src/event_object_movement.c:7725)."""
        now, before = self.elevation[cur], self.elevation[prev]
        if now == ELEVATION_MULTI_LEVEL or before == ELEVATION_MULTI_LEVEL:
            return elev
        return now

    def walks_from(self, start: tuple[int, int], surfable: set[str]) -> dict[int, int]:
        """warp index -> the fewest steps from standing on `start` (an arrival warp's tile) onto that warp (the start's own
        warp included: stepped off and back on). Dijkstra over (tile, elevation); bounded by the map's tiles x 16."""
        origin = (start, self.elevation[start])
        best = {origin: 0}
        queue = [(0, start[1], start[0], origin[1])]
        found: dict[int, int] = {}
        while queue:
            cost, y, x, elev = heapq.heappop(queue)
            here = (x, y)
            if cost > best.get((here, elev), 1 << 30):
                continue
            for direction in DIRS:
                step = self.enter(here, elev, direction, surfable)
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
        return found


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


def extract(root: str) -> tuple[dict, dict]:
    """(the ways.json document, the developers' check: every way's walk length)."""
    src = Source(root)
    names, surfable = behaviours(src)
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
            grids[map_id] = Grid(entry, layout, src, attrs, names, attr_cache)
        return grids[map_id]

    walks: dict[tuple[str, int], dict[int, int]] = {}

    def walks_of(map_id: str, arrival: int) -> dict[int, int]:
        key = (map_id, arrival)
        if key not in walks:
            g = grid(map_id)
            walks[key] = {} if g is None or arrival >= len(g.warps) else g.walks_from(g.warps[arrival][0], surfable)
        return walks[key]

    dark = sorted(map_id for map_id, entry in maps.items() if entry.get("requires_flash") is True)
    out_maps, check = [], {}
    for map_id in dark:
        g = grid(map_id)
        if g is None:
            raise Refused(f"{map_id}: requires_flash but no layout")
        ways = []
        for arrival, (at, _, _) in enumerate(g.warps):
            # Dijkstra over (map, the warp arrived on); the first warp taken on `map_id` is carried with each node
            first_hop: dict[tuple[str, int], tuple[int, int, int]] = {}
            best = {(map_id, arrival): (0, 0)}
            queue = [(0, 0, (0, 0), map_id, arrival, -1)]
            reached: dict[str, tuple[int, int, tuple[int, int], int]] = {}
            popped = 0
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
                for taken, steps in sorted(walks_of(here_map, here_warp).items()):
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
                raise Refused(f"{map_id} from warp {arrival}: the search passed {MAX_NODES} nodes")
            grouped: dict[int, list[str]] = {}
            for dest, (cost, hops, _, first) in reached.items():
                grouped.setdefault(first, []).append(dest)
                check[f"{map_id}|{at[0]},{at[1]}|{dest}"] = cost
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
        out_maps.append({"id": map_id, "ways": ways})
    doc = {
        "_source": "pret/pokeemerald@" + src.sha,
        "_files": {p: src.used[p] for p in sorted(src.used)},
        "_kind": "static game knowledge (USER RULING 40): the way through each dark cave, a guide's level",
        "_made_by": MADE_BY,
        "_reader": READER,
        "_notes": ("per dark map (requires_flash), per warp the player can arrive by ('from'), the warp to take ('take', "
                   "leading to 'leads_to') as the first step of the shortest walk on foot toward each map in 'toward'; warps "
                   "only, no connection; HM obstacles are walls; a cracked floor is no way (see the extractor's docstring)"),
        "_check": {"walk_lengths": dict(sorted(check.items()))},
        "count": len(out_maps),
        "maps": out_maps,
    }
    return doc, check


def dump(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


#: (test side) the dark floors the grid MODEL of `gates/test_ways.py` is drawn from (`model`)
MODEL_MAPS = ("MAP_GRANITE_CAVE_B1F", "MAP_GRANITE_CAVE_B2F")
FIXTURE_DEFAULT = os.path.join(HERE, "fixtures", "granite_dark_model.json")
_LEDGE_CHARS = {"down": "v", "right": ">", "left": "<", "up": "^"}


def model(root: str) -> dict:
    """(TEST SIDE ONLY: never read by the AI) GRANITE CAVE B1F and B2F as `gates/test_world.py` GridGame rows, drawn by the
    SAME walk rules as the ways: a warp is 'S' (stepped on, it warps), a ledge its direction's character, a tile no walk on
    foot enters ('#': collision, water, a cracked floor, an HM obstacle) a wall, the rest floor '.'; and each warp's
    destination. Elevation is uniform on these floors (every walkable tile 3, every wall 0: `--show` prints it) so the
    model leaves it out. The unit A/B in `test_ways.py` ModelTests walks the real explorer through it in the dark."""
    src = Source(root)
    names, surfable = behaviours(src)
    attrs = tileset_attributes(src)
    maps, layouts = load_world(src)
    out: dict = {"_made_by": MADE_BY + " --fixture", "_source": "pret/pokeemerald@" + src.sha,
                 "_what": "test-side grid model of the dark floors (gates/test_ways.py); never read by the AI", "maps": {}}
    for map_id in MODEL_MAPS:
        g = Grid(maps[map_id], layouts[maps[map_id]["layout"]], src, attrs, names, {})
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
                elif (g.collision[xy] != 0 or behaviour in surfable or behaviour in CRACKED or xy in g.walls
                      or behaviour in DIAGONAL_JUMPS):
                    row += "#"
                else:
                    row += "."
                    elevations.add(g.elevation[xy])
            rows.append(row)
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
        print(f"{doc['count']} dark maps")
        return 0 if all(verdicts) else 1
    for path, body in ((args.out, text), (args.fixture, fixture)):
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    print(f"wrote {args.out}: {doc['count']} dark maps, {sum(len(m['ways']) for m in doc['maps'])} ways; and the test "
          f"side's model {args.fixture}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
