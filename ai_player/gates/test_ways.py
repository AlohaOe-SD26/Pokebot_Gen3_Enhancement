"""UNIT PROOFS of P11-1, THE WAY THROUGH A DARK CAVE (2026-11-11). Test side.

    py -3.12 -B ai_player/gates/test_ways.py        (exit 0 = every test passed)

THE CHANGE (`PROJECT KNOWLEDGE/ai-research-notes/2026-11-09-P11-1-DARK-CAVE-DIAGNOSIS.md`, option B with A folded in): on a
DARK map (`requires_flash`) the explorer gets a place at the ladder the static fact (`knowledge/world/ways.json`, written by
`gates/extract_ways.py`, read by `knowledge/ways.py`) names as the way on from the ladder it arrived by toward the intent's
goal; planned through the unseen at the navigator's `UNKNOWN_COST` and redone as the lit circle shows the walls; once in
sight, that ladder (and only that one) outranks the frontier. The AI still sees only the lit circle.

  LoaderTests        the dark maps are the requires_flash maps the file SHIPS, and every other one is LEFT OUT with its
                     reasons (P11-2: GRANITE CAVE B1F and B2F shipped; no VICTORY ROAD way, the walk does not know the
                     HMs); GRANITE CAVE's three ways (B1F (4, 21) -> (28, 21), B2F (28, 21) -> (29, 13), B1F (29, 13) ->
                     (25, 13)) toward STEVEN's room, and toward B2F itself from (4, 21) the way is (28, 21) as well (P11-2:
                     the muddy slope only goes down); (round 2) THE WAY THROUGH with no goal: the same three, and (round 2b)
                     NEVER STRAIGHT BACK: none from STEVEN's side, no mark is the warp arrived by and following the marks
                     never cycles (VICTORY ROAD's did); the walk lengths agree with the diagnosis's independent reader
                     (dark_sim P3: 42, 61, 4); the file and the grid model are exactly the extractor's output from the
                     pinned clone (ERRORS without it); FAULT (the file missing): no dark map, no way (the live FAULT arm's
                     code).
  ExtractorTests     (P11-2, the P11-1 verifier's V1 and V4) the extractor's walk on the pinned layouts: the muddy slope
                     only goes DOWN on foot (B1F's north part slides into its south part and is never reached from it;
                     FAULT: the slope rule taken out, (8, 5) is reached from (4, 21) again); a forced movement it does not
                     model, or ways that depend on the HMs, LEAVE the map out, loudly, naming the map and the tile (a
                     hand-made grid with ice: FAULT and CONTROL); GRANITE CAVE B2F's breakable rocks are met and change
                     none of its ways (the HM check is not vacuous there); the grid model draws the slope one way.
  CandidateTests     on the dark model: the fact only ADDS a `way` place (every other place is the same with the fact
                     removed: the FAULT arm is today's explorer); it outranks every frontier; (round 2) NO goal (the live
                     walk toward STEVEN, "not told yet") gives the way through, a goal the fact does not lead toward gives
                     no way; a LIT map: the same places with and without the fact (CONTROL); an unnamed ladder in sight
                     stays a `door` (A is not applied to it: from B1F's live arrival (4, 21) the only other ladder in reach
                     is the one it came down by; from the slope's other side, (4, 21) is in reach and leads back to 1F,
                     away from STEVEN's room); the named ladder in sight is a `way` with its press; (P11-2, V2) the route's
                     first hop keeps the route's role where it is also the way's ladder, so `goals.lost_way` still finds
                     it (the verifier's VP1); the latest arrival counts and survives a restore; a `way` walked toward
                     while unseen is stale once seen (navigator.stale_reason).
  ModelTests         THE OFFLINE A/B (the live A/B's shape, on the decomp-drawn model `fixtures/granite_dark_model.json`,
                     the real explorer, the 3x3 lit window, five seeds; bounds MEASURED first, see the class): FIX B2F
                     (28, 21) -> (29, 13) at most 135 steps toward STEVEN and (round 2) GOAL-LESS, FAULT far longer in
                     total; FIX's last B1F stay at most 6 steps; every FIX leg leaves by the named ladder.
  BoundTests         an UNREACHABLE way (the ladder walled off in the model): no hang, the way is given up once the walls
                     are seen (its decisions bounded), and the intent goes on with the frontier.
  FairnessTests      the new world file is classified leaf by leaf; a developer key PLANTED under a way FAILS RULE B (the
                     gate mutant), beside the other leaves and (P11-2, the verifier's V3 and its VM1) NESTED inside one; the
                     loader reading a developer key FAILS B2, (P11-2, V5) `_check`'s walk lengths included; deciding code
                     naming ways.json FAILS B1; a mention does not fire; no developer-only key of the base is lost (nothing
                     un-refused) and the file adds exactly the names under `_check`; the loader reads only `maps`, `id`,
                     `ways`, `from`, `take`, `leads_to`, `toward`, `through`. (P11-2's closing pass, the P11-2 verifier's
                     VV1 and VV3) no entry of the file is a subtree: a key nested inside EVERY leaf fails, `maps[].id` and
                     `_check`'s children included; no map const is a developer-only key name (they are values under
                     `_check`), so deciding code that reads one as a key is not refused, while B2 still refuses a loader
                     that reads `_check`, its walk lengths, its maps left out or its HM obstacles.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SUPPORT = Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO)
for entry in (str(REPO), str(SUPPORT / "sandbox-pokebot")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from ai_player.brain import explore as explore_module  # noqa: E402
from ai_player.brain.explore import WAY_THROUGH, WEIGHTS, candidates, explore_intent  # noqa: E402
from ai_player.brain.navigator import Target, stale_reason  # noqa: E402
from ai_player.gates.test_world import GridGame, drive, rig  # noqa: E402
from ai_player.knowledge import ways as ways_module  # noqa: E402

KNOWLEDGE = REPO / "ai_player" / "knowledge"
WORLD = KNOWLEDGE / "world"
MODEL = json.loads((Path(__file__).resolve().parent / "fixtures" / "granite_dark_model.json").read_text(encoding="utf-8"))
B1F, B2F, F1 = "GRANITE_CAVE_B1F", "GRANITE_CAVE_B2F", "GRANITE_CAVE_1F"
STEVEN = "GRANITE_CAVE_STEVENS_ROOM"
DARK = (B1F, B2F)
#: a lit stub of 1F (the model's only lit map): its stairs at (1, 1) lead down to B1F's (4, 21), as 1F's (17, 11) does
F1_ROWS = ["#####", "#S..#", "#...#", "#...#", "#####"]


class DarkGame(GridGame):
    """`test_world.GridGame` with the DARK of `eyes/view.py` (chapter 6 round 7, N6-1): on a dark map only the 3x3 window
    round the player is seen (the 24 px circle: the 8 neighbours at 16 and 22.6 px, the next ring at 32 px), every other
    tile is None and `View.lit` is 24; a warp 'S' looks like a LADDER (stepped on, it warps)."""

    def tile(self, x, y, dx, dy):
        tile = super().tile(x, y, dx, dy)
        if self.char(self.map, (x, y)) == "S":
            return replace(tile, behavior_name="LADDER", door=False)
        return tile

    def view(self):
        full = super().view()
        if full is None or self.map not in DARK:
            return full
        rows = tuple(tuple(t if t is not None and abs(t.dx) <= 1 and abs(t.dy) <= 1 else None for t in row)
                     for row in full.rows)
        return replace(full, rows=rows, objects=(), lit=24)


def model_game(start: tuple[str, tuple[int, int]], walls: dict[str, set] | None = None) -> DarkGame:
    """The decomp-drawn model of B1F and B2F (`extract_ways.py --fixture`) with 1F's lit stub; `walls`: tiles made walls."""
    maps = {name: list(entry["rows"]) for name, entry in MODEL["maps"].items()}
    for name, tiles in (walls or {}).items():
        for x, y in tiles:
            row = maps[name][y]
            maps[name][y] = row[:x] + "#" + row[x + 1:]
    maps[F1] = list(F1_ROWS)
    warps = {}
    for name, entry in MODEL["maps"].items():
        for x, y, dest, dest_id in entry["warps"]:
            if dest in MODEL["maps"]:
                dx, dy, _, _ = MODEL["maps"][dest]["warps"][dest_id]
                warps[(name, (x, y))] = (dest, (dx, dy))
            elif dest == F1 and (x, y) == (4, 21):
                warps[(name, (x, y))] = (F1, (1, 1))
            elif dest == F1:
                warps[(name, (x, y))] = (F1, (3, 3))  # B1F's (25, 13): up to 1F's north (the stub's corner)
    warps[(F1, (1, 1))] = (B1F, (4, 21))
    return DarkGame(maps, start, warps=warps)


def no_fact():
    """THE FAULT: the way-through fact removed (`knowledge/ways.py` reads a missing file: no dark map), as the live FAULT
    arm's code does with `knowledge/world/ways.json` deleted."""
    return mock.patch.dict(ways_module._CACHE, {"ways": {}})


def arrive(game: DarkGame, nav, ladder: tuple[int, int]) -> None:
    """Use `ladder` (beside the player) with the AI's own navigator (`use_exit`, pressing toward it), so the world memory
    records the arrival on the map below as a real run's does."""
    here = game.pos
    direction = {(1, 0): "right", (-1, 0): "left", (0, 1): "down", (0, -1): "up"}[
        (ladder[0] - here[0], ladder[1] - here[1])]
    drive(nav.use_exit(Target("goto", here, "arrive", exit=ladder, direction=direction), "arrive"), 20_000)
    drive(nav.settle("arrived"), 20_000)
    nav.hands.look()


def place_of(nav, game) -> tuple:
    look = game.look()
    return nav.where(look)


class LoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        ways_module._CACHE.clear()

    def test_the_dark_maps_are_the_requires_flash_maps(self):
        """The dark maps the file holds are the requires_flash maps it SHIPS; (P11-2) every other requires_flash map is LEFT
        OUT with its reasons under `_check.left_out` (the extractor refuses a forced movement its walk does not model and
        ways that depend on the HMs; what it neither models nor refuses is listed in its docstring), never silently
        missing and never both. Today GRANITE CAVE B1F and B2F are shipped; VICTORY ROAD B1F and B2F and the three unused
        CAVE OF ORIGIN maps are left out, and so are no dark map to the AI (its explorer decides there, as before P11-1)."""
        data = json.loads((WORLD / "maps.json").read_text(encoding="utf-8"))
        flash = sorted(str(m["id"]).removeprefix("MAP_") for m in data["maps"] if m.get("requires_flash"))
        self.assertEqual(len(flash), 7)
        # (P11-2's closing pass, VV3) [map, reasons] pairs, the map const a value
        left_out = dict(json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))["_check"]["left_out"])
        gone = sorted(str(name).removeprefix("MAP_") for name in left_out)
        self.assertEqual(sorted(ways_module._ways()), [B1F, B2F])
        self.assertEqual(sorted([*ways_module._ways(), *gone]), flash)  # each one shipped or left out, never both
        self.assertEqual(gone, ["CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP1", "CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP2",
                                "CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP3", "VICTORY_ROAD_B1F", "VICTORY_ROAD_B2F"])
        for name, reasons in left_out.items():
            self.assertTrue(reasons and all(isinstance(r, str) and r for r in reasons), name)
        for const in (B1F, B2F):
            self.assertTrue(ways_module.dark(const), const)
        for lit in (F1, "ROUTE106", "DEWFORD_TOWN_GYM", "PETALBURG_WOODS", None, "", *gone):
            self.assertFalse(ways_module.dark(lit), lit)

    def test_no_victory_road_way_is_shipped_until_the_walk_knows_the_hms(self):
        """(P11-2, the P11-1 verifier's V4; the lead's call F4) VICTORY ROAD's maps leave the file until the walk knows the HMs
        the player can use (the AI cannot reach them yet): their on-foot ways differ from the ways of a player who can use the
        field HMs, so the extractor REFUSES them with that reason. No VICTORY ROAD way is shipped and neither is a dark map to
        the AI, so P11-1's on-foot mark from B1F (42, 25) toward (30, 25) is gone (a player with Surf, Strength and Rock Smash
        goes on by (8, 3): the verifier's indep_graph --hms)."""
        doc = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))
        self.assertFalse([m["id"] for m in doc["maps"] if "VICTORY_ROAD" in m["id"]])
        for const in ("VICTORY_ROAD_B1F", "VICTORY_ROAD_B2F"):
            with self.subTest(const=const):
                reasons = dict(doc["_check"]["left_out"])[f"MAP_{const}"]
                self.assertTrue([r for r in reasons if r.startswith("HMs: its ways depend on the HMs the player can use")],
                                reasons)
                self.assertFalse(ways_module.dark(const))
                self.assertIsNone(ways_module.way_through(const, (42, 25)))
                self.assertIsNone(ways_module.way_on(const, (42, 25), lambda name: True))

    def test_granite_caves_three_ways_toward_steven(self):
        wanted = (lambda name: name == STEVEN)
        for const, arrival, take, leads in ((B1F, (4, 21), (28, 21), B2F), (B2F, (28, 21), (29, 13), B1F),
                                            (B1F, (29, 13), (25, 13), F1)):
            with self.subTest(const=const, arrival=arrival):
                way = ways_module.way_on(const, arrival, wanted)
                self.assertIsNotNone(way)
                self.assertEqual((way.take, way.leads_to, way.toward), (take, leads, STEVEN))
        self.assertIsNone(ways_module.way_on(B1F, (4, 21), lambda name: False))  # nothing wanted
        self.assertIsNone(ways_module.way_on(B1F, (5, 21), wanted))  # not an arrival (a fall, a scene)
        self.assertIsNone(ways_module.way_on(F1, (35, 3), wanted))  # a lit map
        # (P11-2, the P11-1 verifier's V1) toward B2F itself from B1F's (4, 21) the way is (28, 21) too (42 steps): the
        # nearer ladder (8, 5) lies above the muddy slope at (9, 9)-(9, 10), which on foot only goes down
        # (src/field_player_avatar.c:567-581), so no walk on foot from (4, 21) reaches it. Round 1 shipped (8, 5) here
        way = ways_module.way_on(B1F, (4, 21), lambda name: name == B2F)
        self.assertEqual((way.take, way.leads_to, way.toward), ((28, 21), B2F, B2F))

    def test_the_walk_lengths_agree_with_the_diagnosis_reader(self):
        """The extractor's walk on foot and the diagnosis's independent model (`dark_sim.py` P3, collision bits only) agree
        on GRANITE CAVE's three legs: 42 + 61 + 4 = 107 steps from B1F's (4, 21) to 1F (#107 measured 50-90, 61/63/61,
        4/4/4)."""
        lengths = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))["_check"]["walk_lengths"]
        b1f, b2f, last = (lengths[f"MAP_{B1F}|4,21|MAP_{STEVEN}"], lengths[f"MAP_{B2F}|28,21|MAP_{STEVEN}"],
                          lengths[f"MAP_{B1F}|29,13|MAP_{STEVEN}"])
        self.assertEqual((b1f - b2f, b2f - last), (42, 61))  # each leg is the difference of two walks toward STEVEN
        self.assertEqual(lengths[f"MAP_{B1F}|29,13|MAP_{F1}"], 4)
        self.assertEqual(last - 4, 37)  # 1F's (35, 3) to STEVEN's room, a lit map

    def test_the_way_through_with_no_goal(self):
        """(round 2) THE WAY THROUGH, goal-less: from each arrival, the way toward the farthest map it leads to. From the
        entrance side it is the way on toward STEVEN's room on every floor. (Round 2b) NEVER STRAIGHT BACK: from his side
        (B1F's (25, 13), down from 1F's north) the farthest map is ROUTE 106 back up the ladder arrived by, so there is NO way
        through (the explorer decides, as before P11-1); likewise B2F's (29, 13), the crossing walked backwards."""
        for const, arrival, take, far in ((B1F, (4, 21), (28, 21), STEVEN), (B2F, (28, 21), (29, 13), STEVEN),
                                          (B1F, (29, 13), (25, 13), "ROUTE106"), (B1F, (8, 5), (28, 21), STEVEN)):
            with self.subTest(const=const, arrival=arrival):
                way = ways_module.way_through(const, arrival)
                self.assertIsNotNone(way)
                self.assertEqual((way.take, way.toward), (take, far))
        self.assertIsNone(ways_module.way_through(B1F, (25, 13)))  # (round 2b) the way through would step straight back
        self.assertIsNone(ways_module.way_through(B2F, (29, 13)))  # (round 2b) likewise
        self.assertIsNone(ways_module.way_through(B1F, (5, 21)))  # not an arrival
        self.assertIsNone(ways_module.way_through(F1, (35, 3)))  # a lit map
        data = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))
        for entry in data["maps"]:  # at most one way through per arrival, toward a map that way leads to
            arrivals = {tuple(w["from"]) for w in entry["ways"]}
            for start in arrivals:
                marked = [w for w in entry["ways"] if tuple(w["from"]) == start and w["through"]]
                self.assertLessEqual(len(marked), 1, (entry["id"], start))
                for way in marked:
                    self.assertIn(way["through"], way["toward"])

    def test_the_way_through_never_steps_back_nor_cycles(self):
        """(round 2b, 2026-11-11) FOLLOW THE WAY THROUGH from every arrival of every dark map: take the marked way, land on
        its warp's destination (maps.json `dest_map` / `dest_warp_id`: the next map's arrival), go on while that map is dark
        and has a way through from there. No mark steps straight back onto the warp arrived by, and no walk comes back to an
        arrival it already left: a goal-less AI following the fact never bounces. (Reproduced first on round 2a's file: 21 of
        29 marks stepped back and 11 starts ended in a cycle, VICTORY ROAD B1F (30, 25) <-> B2F (30, 25) and GRANITE CAVE's
        (29, 2) pocket; `s53/p11r1/through_cycles.py`.) CONTROL: GRANITE CAVE's crossing from B1F (4, 21) is (28, 21),
        (29, 13), (25, 13), and ends on 1F's (35, 3)."""
        ways = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))
        maps = {m["id"]: m for m in json.loads((WORLD / "maps.json").read_text(encoding="utf-8"))["maps"]}
        through = {(entry["id"], tuple(w["from"])): tuple(w["take"]) for entry in ways["maps"] for w in entry["ways"]
                   if w["through"]}
        self.assertTrue(through)

        def land(map_id: str, tile: tuple[int, int]) -> tuple[str, tuple[int, int]] | None:
            warp = next((w for w in maps[map_id]["warps"] if (w["x"], w["y"]) == tile), None)
            if warp is None or warp["dest_map"] not in maps:
                return None
            dest = maps[warp["dest_map"]]["warps"][int(warp["dest_warp_id"])]
            return warp["dest_map"], (dest["x"], dest["y"])

        walks = {}
        for start, take in sorted(through.items()):
            with self.subTest(start=start):
                self.assertNotEqual(take, start[1], f"{start}: the way through steps straight back")
                node, left = start, []
                while node in through:
                    self.assertNotIn(node, left, f"{start}: the walk comes back to {node} ({left})")
                    left.append(node)
                    node = land(node[0], through[node])
                    if node is None:
                        break
                walks[start] = ([n[1] for n in left], node)
        self.assertEqual(walks[(f"MAP_{B1F}", (4, 21))],
                         ([(4, 21), (28, 21), (29, 13)], (f"MAP_{F1}", (35, 3))))  # CONTROL: the crossing

    def test_the_file_is_the_extractors_output_from_the_pinned_decomp(self):
        """(round 2, 2026-11-11, the resumed builder) The shipped fact (`world/ways.json`) and the test side's grid model
        (`fixtures/granite_dark_model.json`) are EXACTLY what `gates/extract_ways.py` computes from the pinned clone (its
        `--check`, in process, under a second): a hand edit, a stale file, or a changed rule of the extractor (the way
        through's "farthest", a walk rule) fails here, so the fact the AI reads stays the decomp's. Without the pinned clone
        (`tools/decomp.pin`; env POKEBOT_DECOMP) this test ERRORS, never a silent pass (test_kb2's convention)."""
        from ai_player.gates import extract_ways as extractor
        root = extractor.resolve_decomp(None)
        doc, _lengths = extractor.extract(root)
        self.assertEqual((WORLD / "ways.json").read_text(encoding="utf-8"), extractor.dump(doc))
        fixture = Path(__file__).resolve().parent / "fixtures" / "granite_dark_model.json"
        self.assertEqual(fixture.read_text(encoding="utf-8"), extractor.dump(extractor.model(root)))

    def test_fault_the_file_missing_is_no_dark_map(self):
        with mock.patch.object(ways_module, "_FILE", WORLD / "no_such_ways.json"):
            ways_module._CACHE.clear()
            self.assertFalse(ways_module.dark(B1F))
            self.assertIsNone(ways_module.way_on(B1F, (4, 21), lambda name: True))
            self.assertIsNone(ways_module.way_through(B1F, (4, 21)))
        ways_module._CACHE.clear()
        self.assertTrue(ways_module.dark(B1F))


def hand_grid(rows: list[str], warps: list[tuple[int, int]], rocks: tuple = ()):
    """(P11-2, test side) A hand-made `extract_ways.Grid` for the walk's rules alone, no layout read: '#' a wall
    (collision 1), '.' floor, 'S' a warp's floor, 'I' MB_ICE (a forced movement the walk does not model), 'M'
    MB_MUDDY_SLOPE, 'C' MB_CRACKED_FLOOR, 'v' MB_JUMP_SOUTH (a ledge), every tile at elevation 3; `warps` the warp tiles
    (each to MAP_ELSEWHERE); `rocks` the tiles a breakable rock stands on."""
    from ai_player.gates import extract_ways as ex
    g = object.__new__(ex.Grid)
    g.id, g.width, g.height = "MAP_HAND_MADE", len(rows[0]), len(rows)
    g.forced = frozenset({"MB_ICE", ex.MUDDY_SLOPE})
    kinds = {"#": "MB_NORMAL", ".": "MB_NORMAL", "S": "MB_NORMAL", "I": "MB_ICE", "M": ex.MUDDY_SLOPE,
             "C": "MB_CRACKED_FLOOR", "v": "MB_JUMP_SOUTH"}
    g.collision = {(x, y): int(c == "#") for y, row in enumerate(rows) for x, c in enumerate(row)}
    g.elevation = {xy: 3 for xy in g.collision}
    g.behaviour = {(x, y): kinds[c] for y, row in enumerate(rows) for x, c in enumerate(row)}
    g.warps = [(xy, "MAP_ELSEWHERE", "0") for xy in warps]
    g.warp_at = {xy: index for index, xy in enumerate(warps)}
    g.walls = {xy: "OBJ_EVENT_GFX_BREAKABLE_ROCK" for xy in rocks}
    return g


class ExtractorTests(unittest.TestCase):
    """(P11-2, the P11-1 verifier's V1 and V4; the lead's calls F1 and F4) The extractor's walk on foot models the muddy
    slope (one way, down) and REFUSES what it does not model: a dark map whose walk lands on another forced movement, or
    whose ways depend on the HMs the player can use, is left out of the file, loudly, naming the map and the tile."""

    @staticmethod
    def pinned():
        from ai_player.gates import extract_ways as ex
        root = ex.resolve_decomp(None)
        src = ex.Source(root)
        names, surfable = ex.behaviours(src)
        return ex, src, names, surfable, ex.forced_behaviours(src), ex.tileset_attributes(src), ex.load_world(src)

    def test_the_muddy_slope_only_goes_down_on_foot(self):
        """GRANITE CAVE B1F's slope (9, 9)-(9, 10), on the pinned layout, with the extractor's own walk: a step onto its top
        from (9, 8) slides the player to (9, 11), off the slope (3 steps); a step up from (9, 11) is slid straight back. So
        from the arrival (4, 21) the walk reaches its own ladder and (28, 21), never (8, 5) or (12, 3); from the north
        side's (8, 5) it reaches (4, 21) and (28, 21), down the slope. The forced-movement table is the decomp's
        (src/field_player_avatar.c sForcedMovementTestFuncs). FAULT: the same grid with no forced movement, and (8, 5) is
        reached from (4, 21) again, P11-1's shipped way: the test sees the rule."""
        ex, src, names, surfable, forced, attrs, (maps, layouts) = self.pinned()
        self.assertTrue({ex.MUDDY_SLOPE, "MB_ICE", "MB_WALK_EAST", "MB_SLIDE_SOUTH", "MB_WATERFALL",
                         "MB_TRICK_HOUSE_PUZZLE_8_FLOOR", "MB_SECRET_BASE_SPIN_MAT"} <= forced, sorted(forced))

        def b1f(rules):
            entry = maps["MAP_GRANITE_CAVE_B1F"]
            return ex.Grid(entry, layouts[entry["layout"]], src, attrs, names, {}, rules)

        def reached(grid, start):
            return {grid.warps[index][0] for index in grid.walks_from(start, surfable)[0]}

        g = b1f(forced)
        self.assertEqual([xy for xy, b in sorted(g.behaviour.items()) if b == ex.MUDDY_SLOPE], [(9, 9), (9, 10)])
        down = g.enter((9, 8), g.elevation[(9, 8)], "down", surfable)
        self.assertEqual((down[0], down[2]), ((9, 11), 3))
        self.assertEqual(g.enter((9, 11), g.elevation[(9, 11)], "up", surfable)[0], (9, 11))  # slid straight back
        self.assertEqual(reached(g, (4, 21)), {(4, 21), (28, 21)})
        self.assertTrue({(4, 21), (28, 21), (8, 5)} <= reached(g, (8, 5)))
        self.assertIn((8, 5), reached(b1f(frozenset()), (4, 21)))  # FAULT: no forced movement, the slope walked up

    def test_a_forced_movement_it_does_not_model_stops_the_walk_and_refuses_the_map(self):
        """A hand-made map: the walk from the warp (1, 1) to the warp (4, 1) crosses (3, 1). With MB_ICE there (a forced
        movement the walk does not model) the walk on foot STOPS on it, records it, and the refusal names the behaviour,
        the map and the tile; the every-HM walk walks on over it (it only looks for more ways). CONTROL: floor at (3, 1),
        the walk reaches (4, 1) and meets nothing. A slope ('M') above a wall stays where the wall stops it (DoForcedMovement:
        a collision ends the forced move); one above floor slides down onto it; one above a south ledge jumps it (the
        forced move's COLLISION_LEDGE_JUMP); one above a cracked floor drops the player through it: no way. (P11-2's closing
        pass, the P11-2 verifier's VV4: its mutants VMe and VMf survived every test) One above a WARP slides onto it and
        uses it, the slid tile counted; one above a breakable ROCK leaves the player resting on the slope on foot, the rock
        met, while the every-HM walk (the rock gone) slides on onto the rock's tile."""
        from ai_player.gates import extract_ways as ex
        ice = hand_grid(["######", "#S.I.S", "######"], [(1, 1), (5, 1)])
        found, met = ice.walks_from((1, 1), set())
        self.assertEqual(sorted(found), [0])  # only its own warp: the ice stops the walk on foot
        self.assertEqual(met, {("forced", "MAP_HAND_MADE", (3, 1), "MB_ICE")})
        why = ex.refusals(([], {}, set(met)), ([], {}, set()))
        self.assertEqual(why, ["FORCED MOVEMENT its walk does not model: MB_ICE at (3, 1) on MAP_HAND_MADE"])
        self.assertEqual(sorted(ice.walks_from((1, 1), set(), hms=True)[0]), [0, 1])  # the every-HM walk walks on
        control = hand_grid(["######", "#S...S", "######"], [(1, 1), (5, 1)])
        self.assertEqual(control.walks_from((1, 1), set()), ({0: 2, 1: 4}, frozenset()))
        self.assertEqual(ex.refusals(([], {}, set()), ([], {}, set())), [])
        slope = hand_grid(["#.#", "#M#", "#.#", "#M#", "###"], [])
        self.assertEqual(slope.enter((1, 0), 3, "down", set())[0::2], ((1, 2), 2))  # slid off the slope onto floor
        self.assertEqual(slope.enter((1, 2), 3, "down", set())[0::2], ((1, 3), 1))  # the wall under it stops the slide
        ledge = hand_grid(["#.#", "#M#", "#v#", "#.#", "###"], [])
        self.assertEqual(ledge.enter((1, 0), 3, "down", set())[0::2], ((1, 3), 3))  # the ledge under the slope is jumped
        crack = hand_grid(["#.#", "#M#", "#C#", "#.#", "###"], [])
        self.assertIsNone(crack.enter((1, 0), 3, "down", set()))  # slid onto a cracked floor: a drop, no way
        # (closing pass, VV4) a warp under the slope is used (DoForcedMovement: a warp south of it is stepped on), the slid
        # tile counted: 2 steps, never a rest on the slope (VMe)
        warp = hand_grid(["#.#", "#M#", "#S#", "###"], [(1, 2)])
        self.assertEqual(warp.enter((1, 0), 3, "down", set())[0::2], ((1, 2), 2))
        # a breakable rock under the slope stops the slide on foot (a collision ends the forced move) and is met; never slid
        # through (VMf); in the every-HM walk the rock is gone and the slide goes on onto its tile
        rock = hand_grid(["#.#", "#M#", "#.#", "#.#", "###"], [], rocks=((1, 2),))
        met: set = set()
        self.assertEqual(rock.enter((1, 0), 3, "down", set(), met=met)[0::2], ((1, 1), 1))
        self.assertEqual(met, {("hm", "MAP_HAND_MADE", (1, 2), "OBJ_EVENT_GFX_BREAKABLE_ROCK")})
        self.assertEqual(rock.enter((1, 0), 3, "down", set(), hms=True)[0::2], ((1, 2), 2))

    def test_ways_that_depend_on_the_hms_refuse_the_map_and_an_obstacle_that_changes_nothing_is_a_wall(self):
        """The HM check: a hand-made map whose only way to the warp (4, 1) is through a breakable rock at (3, 1): on foot no
        way, with every HM a way; the refusal names the HMs and the rock's tile. CONTROL: the rock in a side pocket the walk
        meets but never needs: the same ways and walk lengths both ways, no refusal. Equal ways with a SHORTER walk with
        every HM refuse too (a shorter walk could start by another ladder). And on the pinned layouts the check is not
        vacuous: GRANITE CAVE B2F's walk meets its seven breakable rocks and is shipped (they change none of its ways),
        while VICTORY ROAD's ways change and it is left out."""
        from ai_player.gates import extract_ways as ex
        blocked = hand_grid(["######", "#S..S#", "######"], [(1, 1), (4, 1)], rocks=((3, 1),))
        foot, foot_met = blocked.walks_from((1, 1), set())
        every = blocked.walks_from((1, 1), set(), hms=True)[0]
        self.assertEqual((sorted(foot), sorted(every)), ([0], [0, 1]))
        way = {"from": [1, 1], "take": [4, 1], "leads_to": "MAP_ELSEWHERE", "toward": ["MAP_ELSEWHERE"], "through": None}
        why = ex.refusals(([], {}, set(foot_met)), ([way], {"MAP_HAND_MADE|1,1|MAP_ELSEWHERE": 3}, set()))
        self.assertEqual(len(why), 1)
        self.assertTrue(why[0].startswith("HMs: its ways depend on the HMs the player can use"), why)
        self.assertIn("OBJ_EVENT_GFX_BREAKABLE_ROCK at (3, 1) on MAP_HAND_MADE", why[0])
        side = hand_grid(["#####", "#S.S#", "##.##", "#####"], [(1, 1), (3, 1)], rocks=((2, 2),))
        self.assertEqual(side.walks_from((1, 1), set())[0], side.walks_from((1, 1), set(), hms=True)[0])
        self.assertIn(("hm", "MAP_HAND_MADE", (2, 2), "OBJ_EVENT_GFX_BREAKABLE_ROCK"), side.walks_from((1, 1), set())[1])
        self.assertEqual(ex.refusals(([way], {"k": 4}, set()), ([way], {"k": 4}, set())), [])  # CONTROL: the same
        shorter = ex.refusals(([way], {"k": 4}, set()), ([way], {"k": 3}, set()))
        self.assertTrue(shorter and shorter[0].startswith("HMs:") and "4 steps on foot, 3 with every HM" in shorter[0], shorter)
        doc = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))
        rocks = dict(doc["_check"]["hm_obstacles"])[f"MAP_{B2F}"]
        self.assertEqual(len([r for r in rocks if r.startswith("OBJ_EVENT_GFX_BREAKABLE_ROCK") and r.endswith(f"MAP_{B2F}")]), 7)
        self.assertIn(f"MAP_{B2F}", [m["id"] for m in doc["maps"]])
        _, src, names, surfable, forced, attrs, (maps, layouts) = self.pinned()
        route = maps["MAP_ROUTE104"]  # a cuttable tree is an HM obstacle too (none on a dark map's walk)
        trees = ex.Grid(route, layouts[route["layout"]], src, attrs, names, {}, forced).walls
        self.assertIn("OBJ_EVENT_GFX_CUTTABLE_TREE", set(trees.values()))

    def test_every_refusal_is_said_loudly_naming_the_map_and_the_tile(self):
        """Every mode of the extractor prints the refusals (`loud`): VICTORY ROAD B1F's walk lands on the HALL OF FAME's
        ice (a forced movement the walk does not model) and its ways depend on the HMs; each line names the map refused, the
        behaviour or obstacle, its map and its tile."""
        from ai_player.gates import extract_ways as ex
        doc = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))
        lines = ex.loud(doc)
        self.assertEqual(len(lines), sum(len(reasons) for _map, reasons in doc["_check"]["left_out"]))
        vr = [line for line in lines if line.startswith("REFUSED MAP_VICTORY_ROAD_B1F: ")]
        self.assertTrue(any("FORCED MOVEMENT its walk does not model: MB_ICE at (6, 11) on "
                            "MAP_EVER_GRANDE_CITY_HALL_OF_FAME" in line for line in vr), vr)
        self.assertTrue(any("HMs:" in line and "OBJ_EVENT_GFX_" in line and " at (" in line for line in vr), vr)

    def test_the_grid_model_draws_the_slope_one_way(self):
        """The test side's model (`extract_ways.model`) draws B1F's slope as a south ledge at its top, (9, 9), floor at
        (9, 10): from (9, 8) a press down lands on (9, 10), from (9, 10) a press up is refused, as the game slides a player
        back. Round 1's fixture drew both tiles as floor, a two-way slope."""
        rows = MODEL["maps"][B1F]["rows"]
        self.assertEqual((rows[9][9], rows[10][9], rows[9][8], rows[9][10]), ("v", ".", "#", "#"))
        game = model_game((B1F, (9, 8)))
        game.attempt("Down")
        self.assertEqual(game.pos, (9, 10))
        game.attempt("Up")
        self.assertEqual(game.pos, (9, 10))
        self.assertEqual(game.bumps, 1)


class CandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        ways_module._CACHE.clear()

    def on_b2f(self):
        game = model_game((B1F, (27, 21)))
        hands, nav, world, notes, lines = rig(game, seed=5)
        arrive(game, nav, (28, 21))
        self.assertEqual((game.map, game.pos), (B2F, (28, 21)))
        return game, nav, world

    def goal(self, name):
        return lambda memory, key: memory is not None and memory.const == name

    def test_the_fact_only_adds_the_way_and_it_outranks_the_frontier(self):
        game, nav, world = self.on_b2f()
        look = game.look()
        found = candidates(nav, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        with no_fact():
            today = candidates(nav, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        ways = [t for t in found if t.kind == "way"]
        self.assertEqual(len(ways), 1, found)
        self.assertEqual((ways[0].tile, ways[0].exit), ((29, 13), None))  # the unseen ladder itself, walked toward
        self.assertTrue(ways[0].reason.startswith(WAY_THROUGH), ways[0].reason)
        self.assertEqual([t for t in found if t.kind != "way"], today)  # FAULT arm = today's places exactly
        self.assertFalse([t for t in today if t.kind == "way"])
        best_other = max(t.score for t in found if t.kind != "way")
        self.assertGreater(ways[0].score, best_other + 20, found)

    def test_no_goal_is_the_way_through_an_unwanted_goal_none_a_lit_map_unchanged(self):
        """(round 2) With NO goal (the live walk toward STEVEN, "by looking around: not told yet") the way is THE WAY
        THROUGH (here the same ladder as toward STEVEN); with a goal the fact leads nowhere toward (a traveller bound
        elsewhere) there is no way; a LIT map: the same places with and without the fact."""
        game, nav, world = self.on_b2f()
        look = game.look()
        found = candidates(nav, look, WEIGHTS["Story"], None, jitter_on=False)
        ways = [t for t in found if t.kind == "way"]
        self.assertEqual([t.tile for t in ways], [(29, 13)], found)
        self.assertIn(f"toward {STEVEN}", ways[0].reason)
        with no_fact():
            today = candidates(nav, look, WEIGHTS["Story"], None, jitter_on=False)
        self.assertEqual([t for t in found if t.kind != "way"], today)  # FAULT arm = today's places exactly
        found = candidates(nav, look, WEIGHTS["Story"], self.goal("PETALBURG_CITY"), jitter_on=False)
        self.assertFalse([t for t in found if t.kind == "way"], found)
        # CONTROL, a LIT map (1F's stub): the same places with and without the fact
        lit = model_game((F1, (2, 2)))
        hands, nav2, world2, notes, lines = rig(lit, seed=5)
        drive(nav2.go_to((3, 3), "walk", 2000), 20_000)
        look = lit.look()
        with_fact = candidates(nav2, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        with no_fact():
            without = candidates(nav2, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        self.assertEqual(with_fact, without)
        self.assertTrue(with_fact)

    def test_an_unnamed_ladder_in_sight_stays_a_door_the_named_one_is_the_way(self):
        """DECIDED (A only for the ladder the fact names), with its TRUE reason (P11-2, the P11-1 verifier's V1): from
        B1F's arrival (4, 21), down from 1F (the live crossing), the only ladders within reach on foot are (4, 21) itself,
        the one it came down by, and (28, 21), the named one: B1F's north part ((8, 5), (12, 3)) lies above the muddy slope,
        which on foot only goes down (round 1's "(8, 5) is reachable on foot (24 steps)" was the extractor's two-way slope).
        So on the forward crossing no unnamed ladder is ever in sight. One is on the slope's other side: arrived at B1F's
        (8, 5), up from B2F's dead end, a walk goes down the slope into the south part, where the unused ladder (4, 21) leads
        back up to 1F, away from STEVEN's room (the fact's way from (8, 5) is (28, 21)); a seasoned player's 'a lit ladder
        beats the frontier' applied to EVERY ladder would take it. So an unnamed ladder in sight keeps today's value
        (`Weights.door`), and the named one in sight is the `way`, with its press."""
        data = {m["id"]: m for m in json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))["maps"]}
        reach = {tuple(w["take"]) for w in data[f"MAP_{B1F}"]["ways"] if w["from"] == [4, 21]}
        self.assertEqual(reach, {(4, 21), (28, 21)})  # the live arrival: the ladder it came by and the named one, no other
        north = {tuple(w["take"]): w for w in data[f"MAP_{B1F}"]["ways"] if w["from"] == [8, 5]}
        self.assertEqual(sorted(north), [(4, 21), (8, 5), (28, 21)])  # the slope's other side reaches (4, 21) ...
        self.assertNotIn(f"MAP_{STEVEN}", north[(4, 21)]["toward"])  # ... which leads away from STEVEN's room
        self.assertEqual(north[(28, 21)]["through"], f"MAP_{STEVEN}")
        game = model_game((B2F, (8, 6)))
        hands, nav, world, notes, lines = rig(game, seed=5)
        arrive(game, nav, (8, 5))
        self.assertEqual((game.map, game.pos), (B1F, (8, 5)))
        game.pos = (4, 20)  # as if it had walked there, down the slope: the unused ladder (4, 21) comes into the lit window
        look = game.look()
        world.observe(look)
        found = candidates(nav, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        at_421 = [t for t in found if t.exit == (4, 21)]
        self.assertEqual([t.kind for t in at_421], ["door"], found)
        self.assertEqual([t.kind for t in found if t.kind == "way"], ["way"])
        self.assertEqual([t.tile for t in found if t.kind == "way"], [(28, 21)])
        self.assertGreater(max(t.score for t in found if t.kind == "way"), max(t.score for t in at_421))
        # the NAMED ladder in sight: B1F's (29, 13) arrival, the way (25, 13) seen four tiles west
        game2 = model_game((B2F, (28, 13)))
        hands, nav2, world2, notes, lines = rig(game2, seed=5)
        arrive(game2, nav2, (29, 13))
        self.assertEqual((game2.map, game2.pos), (B1F, (29, 13)))
        game2.pos = (26, 13)
        look = game2.look()
        world2.observe(look)
        found = candidates(nav2, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        named = [t for t in found if t.exit == (25, 13)]
        self.assertEqual([t.kind for t in named], ["way"], found)
        self.assertIsNotNone(named[0].direction)
        self.assertEqual(max(found, key=lambda t: t.score), named[0])
        with no_fact():
            today = candidates(nav2, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        self.assertEqual([t.kind for t in today if t.exit == (25, 13)], ["door"])  # FAULT: today's 0.8

    def test_the_routes_first_hop_keeps_its_role_where_it_is_the_way(self):
        """(P11-2, the P11-1 verifier's V2 and its probe VP1, now a unit test) On B1F, back up from B2F by (28, 21) with B2F
        not seen all of, the walk with no lead (`goals.lost_way`: toward a known map with something left, B2F) keeps the
        ROUTE by (28, 21): an exit that is both the route's first hop and the way's ladder (the fact's way toward B2F from
        there is (28, 21) itself) keeps the route's role, so the places are today's exactly (the fact adds nothing where the
        AI's memory already knows the way). Before P11-2 the exit became a `way` and lost_way, which walks routes only,
        answered None (VP1: "WITH the fact: lost_way -> None")."""
        from ai_player.brain.goals import lost_way
        game = model_game((B1F, (27, 21)))
        hands, nav, world, notes, lines = rig(game, seed=5)
        arrive(game, nav, (28, 21))
        self.assertEqual((game.map, game.pos), (B2F, (28, 21)))
        drive(nav.go_to((28, 20), "step off the ladder", 2000), 20_000)
        arrive(game, nav, (28, 21))
        self.assertEqual((game.map, game.pos), (B1F, (28, 21)))
        look = game.look()
        found, left = lost_way(nav, look, WEIGHTS["Story"], False)
        with no_fact():
            today, left_today = lost_way(nav, look, WEIGHTS["Story"], False)
        self.assertIsNotNone(found)
        self.assertEqual((found.kind, found.tile, found.exit), ("route", (27, 21), (28, 21)), found)
        self.assertEqual((today.kind, today.tile, today.exit, today.reason), (found.kind, found.tile, found.exit, found.reason))
        self.assertEqual((left, left_today), ([("0:2", left[0][1])], [("0:2", left[0][1])]))  # B2F, something left
        keys = {key for key, _ in world.left_anywhere() if key != world.current}
        self.assertEqual(ways_module.way_on(B1F, (28, 21), lambda name: name == B2F).take, (28, 21))  # the way: the same
        goal = (lambda memory, key: key in keys)
        with_fact = candidates(nav, look, WEIGHTS["Story"], goal, jitter_on=False)
        with no_fact():
            without = candidates(nav, look, WEIGHTS["Story"], goal, jitter_on=False)
        self.assertEqual(with_fact, without)  # FIX = FAULT here
        self.assertEqual([(t.kind, t.exit) for t in with_fact if t.exit == (28, 21)], [("route", (28, 21))])

    def test_the_latest_arrival_counts_and_survives_a_restore(self):
        """The way is from the arrival of THIS stay (the memory's LATEST transition onto the map): B1F is stood on twice on
        the way to STEVEN, by (4, 21) first and by (29, 13) after B2F, and the second stay's way is (25, 13), not the first
        stay's (28, 21). The arrival is in the memory a run saves and restores (`WorldMemory.to_dict` / `from_dict`): a
        run continued on a dark map (the live A/B's start) knows it."""
        from ai_player.world.memory import WorldMemory
        game = model_game((B2F, (28, 13)))
        hands, nav, world, notes, lines = rig(game, seed=5)
        arrive(game, nav, (29, 13))
        world.transitions.insert(0, replace(world.transitions[-1], frame=0, arrival=(4, 21)))  # an earlier stay
        look = game.look()
        found = candidates(nav, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        self.assertEqual([t.tile for t in found if t.kind == "way"], [(25, 13)], found)
        restored = WorldMemory.from_dict(json.loads(world.snapshot()))
        self.assertEqual(restored.transitions[-1].arrival, (29, 13))
        self.assertEqual(restored.transitions[-1].target, world.current)

    def test_a_way_walked_toward_unseen_is_stale_once_seen(self):
        game, nav, world = self.on_b2f()
        memory = world.here()
        unseen = Target("way", (29, 13), WAY_THROUGH)
        self.assertIsNone(stale_reason(memory, unseen))
        near = Target("way", (28, 20), WAY_THROUGH)  # a tile already seen
        self.assertEqual(stale_reason(memory, near), "the way on is in sight now")
        self.assertIsNone(stale_reason(memory, replace(near, exit=(28, 20), direction="up")))  # the exit form never


def leg(start, ladder, seed: int, fact: bool, walls=None, budget: int = 60_000, goal_map: str | None = STEVEN):
    """One dark stay of the real explorer on the model: arrive by `ladder` (from `start`, beside it), then explore toward
    `goal_map` (STEVEN's room; None: GOAL-LESS, as the live walk toward STEVEN is, "by looking around: not told yet") until
    the map changes. Returns (steps on the arrival map, the map and the tile it left by, the decide records' kinds, the
    intent's outcome, the game)."""
    game = model_game(start, walls)
    hands, nav, world, notes, lines = rig(game, seed=seed)
    arrive(game, nav, ladder)
    here = game.map
    began = len(game.trail)

    def left(look):
        player = look.player
        return player is not None and not player.settling and player.map_const != here

    intent = explore_intent(goal_map, "Story", budget, done=left)
    if fact:
        outcome = drive(nav.run(intent, "the leg"), budget + 20_000)
    else:
        with no_fact():
            outcome = drive(nav.run(intent, "the leg"), budget + 20_000)
    walked = [t for t in game.trail[began:] if t[0] == here]
    steps = len(walked)  # every trail entry is one step taken, the last onto the ladder it left by
    out_of = walked[-1][1] if walked else None
    kinds = [r["extra"].get("kind") for r in notes.records if r["decision"] == "decide"]
    return steps, game.map, out_of, kinds, outcome, game


class ModelTests(unittest.TestCase):
    """THE OFFLINE A/B on the decomp-drawn model, seeds 1-5 (one model trajectory per seed: a check of the RULE, not a
    rate). MEASURED FIRST (2026-11-11, `s53/p11r1/model_legs_v1.out`), the bounds below are set from it: FIX B2F 121-129
    steps (the diagnosis's model P2 said 99; the real navigator keeps a plan until it fails and adds its per-tile noise:
    with `UNKNOWN_COST` 2 it walks 101, with 5, 151: `model_variants.out`), FAULT 123-249 (two seeds found the way by luck);
    the last B1F stay FIX 4 against FAULT 34-42. FIX's first B1F stay 46-70 against FAULT 86-200, every FAULT leaving by
    (28, 21): RE-MEASURED (P11-2, `s53/p11r2/model_legs_p11r2.out`) on the model with B1F's muddy slope drawn ONE WAY, as
    the game has it (on foot it only goes down: `extract_ways.py`), so B1F's north part is out of reach from (4, 21). Round
    1's "FAULT 122-224, taking the dead-end ladder (8, 5) in 2 of 5" walked UP a slope the model drew as two-way floor: an
    artifact of the model (the P11-1 verifier's V1). The B2F and last-stay legs never touch the slope (unchanged). The live
    pass lines are the diagnosis's (B2F about 120, the last stay 6)."""

    SEEDS = (1, 2, 3, 4, 5)

    def setUp(self) -> None:
        ways_module._CACHE.clear()

    def test_b2f_fix_against_fault(self):
        fixes, faults = [], []
        for seed in self.SEEDS:
            with self.subTest(seed=seed):
                fix = leg((B1F, (27, 21)), (28, 21), seed, True)
                fault = leg((B1F, (27, 21)), (28, 21), seed, False)
                self.assertEqual((fix[1], fix[2]), (B1F, (29, 13)), fix[4])  # left by the named ladder
                self.assertLessEqual(fix[0], 135, fix[4])
                self.assertEqual(fix[3], ["way", "way"])  # one decision walked through the dark, one the ladder in sight
                self.assertNotIn("way", fault[3])
                fixes.append(fix[0])
                faults.append(fault[0])
        self.assertGreaterEqual(sum(faults), 1.4 * sum(fixes), (fixes, faults))
        self.assertGreaterEqual(sum(1 for f in faults if f >= 150), 2, faults)

    def test_b2f_goal_less_fix_against_fault(self):
        """(round 2) THE LIVE CASE: the walk toward STEVEN has no goal map ("by looking around: not told yet"); FIX walks
        the way through, FAULT is today's explorer. Measured first (`model_legs_v2.out`): the same steps as toward STEVEN
        (FIX 121-129, FAULT 123-249)."""
        fixes, faults = [], []
        for seed in self.SEEDS:
            with self.subTest(seed=seed):
                fix = leg((B1F, (27, 21)), (28, 21), seed, True, goal_map=None)
                fault = leg((B1F, (27, 21)), (28, 21), seed, False, goal_map=None)
                self.assertEqual((fix[1], fix[2]), (B1F, (29, 13)), fix[4])
                self.assertLessEqual(fix[0], 135, fix[4])
                self.assertEqual(fix[3], ["way", "way"])
                self.assertNotIn("way", fault[3])
                fixes.append(fix[0])
                faults.append(fault[0])
        self.assertGreaterEqual(sum(faults), 1.4 * sum(fixes), (fixes, faults))

    def test_the_last_b1f_stay(self):
        for seed in self.SEEDS:
            with self.subTest(seed=seed):
                fix = leg((B2F, (28, 13)), (29, 13), seed, True)
                fault = leg((B2F, (28, 13)), (29, 13), seed, False)
                self.assertEqual((fix[1], fix[2]), (F1, (25, 13)), fix[4])  # left by the named ladder
                self.assertLessEqual(fix[0], 6, fix[4])
                self.assertGreaterEqual(fault[0], 20, fault[4])  # FAULT: the frontier first, the lit ladder last

    def test_the_first_b1f_stay_leaves_by_the_named_ladder(self):
        fixes, faults = [], []
        for seed in self.SEEDS:
            with self.subTest(seed=seed):
                fix = leg((F1, (2, 1)), (1, 1), seed, True)
                fault = leg((F1, (2, 1)), (1, 1), seed, False)
                self.assertEqual((fix[1], fix[2]), (B2F, (28, 21)), fix[4])
                self.assertLessEqual(fix[0], 80, fix[4])
                fixes.append(fix[0])
                faults.append(fault[0])
        self.assertGreaterEqual(sum(faults), 1.5 * sum(fixes), (fixes, faults))


class BoundTests(unittest.TestCase):
    def setUp(self) -> None:
        ways_module._CACHE.clear()

    def test_an_unreachable_way_is_given_up_and_never_loops(self):
        """B2F's exit (29, 13) walled off in the model (its whole corner): the way is planned toward through the unseen
        while a plan is known, given up once the lit circle has shown the walls (no plan known: no place), and the intent
        goes on with the frontier; it ends within its budget (no hang) with the way's decisions bounded."""
        walls = {B2F: {(x, y) for x in range(26, 31) for y in range(11, 16)} - {(29, 13)}}
        steps, left_map, out_of, kinds, outcome, game = leg((B1F, (27, 21)), (28, 21), 1, True, walls=walls, budget=40_000)
        self.assertIn("way", kinds)
        last_way = max(i for i, k in enumerate(kinds) if k == "way")
        self.assertLess(last_way, len(kinds) - 1, kinds[-10:])  # the way given up: later decisions are other places
        self.assertLessEqual(kinds.count("way"), 30, kinds.count("way"))
        self.assertNotEqual((left_map, out_of), (B1F, (29, 13)))
        self.assertTrue(outcome.startswith(("budget", "stuck", "done")), outcome)


class FairnessTests(unittest.TestCase):
    def plant(self, edit) -> list[str]:
        from ai_player.gates import check_fairness as cf_
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "ai_player"
            shutil.copytree(REPO / "ai_player", pkg, ignore=shutil.ignore_patterns(
                "__pycache__", "evidence", "gates", "*.ss1", "eyes", "host"))
            edit(pkg)
            return cf_.check(pkg)[1]

    @staticmethod
    def rule_b(edit) -> list[str]:
        """(P11-2's closing pass) RULE B's problems for the shipped ways.json, edited by `edit`, alone in a knowledge folder
        of its own (`schema_problems` walks only the world files that exist): seconds for every leaf's plant."""
        from ai_player.gates import check_fairness as cf_
        doc = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))
        edit(doc)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "world").mkdir()
            (Path(tmp) / "world" / "ways.json").write_text(json.dumps(doc), encoding="utf-8")
            return cf_.schema_problems(Path(tmp))[0]

    @staticmethod
    def add(rel: str, text: str):
        def do(pkg):
            path = pkg / rel
            path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
        return do

    def test_the_file_is_classified_leaf_by_leaf_and_a_planted_developer_key_fails(self):
        """A developer key planted under a way FAILS RULE B as a SIBLING of its leaves and (P11-2, the P11-1 verifier's V3:
        its mutant VM1 passed the gate) NESTED inside a leaf (a dict with a walk length added to `toward`): the five leaves
        hold scalars or lists of scalars, so none is a subtree and a key below one is unclassified. (P11-2's closing pass,
        the P11-2 verifier's VV1: its plant VF1, a developer key nested inside `maps[].id`, PASSED RULE B) NO entry of the
        file is a subtree: a dict nested inside EVERY leaf fails, `maps[].id`, `count`, the META leaves and (VV3) `_check`'s
        children included; a key planted directly under `_check`, under its walk lengths (a bare map const) or under
        `_files` (no path) is unclassified too. CONTROL: a VALUE that mentions a developer key is no key and passes."""
        from ai_player.gates import check_fairness as cf_
        self.assertIn("world/ways.json", cf_.world_files())
        schema = cf_.KNOWLEDGE_FIELDS["world/ways.json"]
        for container in ("maps", "maps[]", "maps[].ways", "maps[].ways[]"):
            self.assertFalse(schema[container][2], container)  # never a subtree: it would classify any plant

        def the_way(doc):
            return next(w for m in doc["maps"] if m["id"] == f"MAP_{B1F}" for w in m["ways"]
                        if w["from"] == [4, 21] and w["take"] == [28, 21])

        def nest(value):  # a developer key nested inside a scalar leaf (the verifier's VF1 shape)
            return {"value": value, "walk_lengths": {"x": 1}}

        def first(mapping):
            return sorted(mapping)[0]

        def put(doc, path, value):
            *parents, last = path
            for key in parents:
                doc = doc[key]
            doc[last] = value

        doc0 = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))
        walk0, file0 = first(doc0["_check"]["walk_lengths"]), first(doc0["_files"])
        # (the leaf, the plant, the UNCLASSIFIED path RULE B must name): one per schema entry that holds a value
        plants = [
            ("maps[].id", lambda d: put(d, ("maps", 0, "id"), nest(d["maps"][0]["id"])), "maps[].id.walk_lengths"),
            ("maps[].ways[].from", lambda d: the_way(d)["from"].append({"steps": 107}), "maps[].ways[].from[].steps"),
            ("maps[].ways[].take", lambda d: the_way(d)["take"].append({"steps": 107}), "maps[].ways[].take[].steps"),
            ("maps[].ways[].leads_to", lambda d: the_way(d).update(leads_to=nest(the_way(d)["leads_to"])),
             "maps[].ways[].leads_to.walk_lengths"),
            ("maps[].ways[].toward", lambda d: the_way(d)["toward"].append({"map": f"MAP_{STEVEN}", "steps": 107}),
             "maps[].ways[].toward[].steps"),  # the P11-1 verifier's VM1, byte for byte
            ("maps[].ways[].through", lambda d: the_way(d).update(through=nest(the_way(d)["through"])),
             "maps[].ways[].through.walk_lengths"),
            ("count", lambda d: put(d, ("count",), nest(d["count"])), "count.walk_lengths"),
            *[("_*", (lambda key: lambda d: put(d, (key,), nest(d[key])))(key), f"{key}.walk_lengths")
              for key in ("_source", "_kind", "_made_by", "_reader", "_notes")],
            ("_files", lambda d: put(d, ("_files", "walk_lengths"), 1), "_files.walk_lengths"),
            ("_files.*/*", lambda d: put(d, ("_files", file0), nest(d["_files"][file0])), f"_files.{file0}.walk_lengths"),
            ("_check", lambda d: put(d, ("_check", "by_map"), {f"MAP_{B1F}": 1}), "_check.by_map"),  # the VV3 shape
            ("_check.walk_lengths", lambda d: put(d, ("_check", "walk_lengths", f"MAP_{B1F}"), 42),
             f"_check.walk_lengths.MAP_{B1F}"),
            ("_check.walk_lengths.MAP_*|*,*|MAP_*",
             lambda d: put(d, ("_check", "walk_lengths", walk0), nest(d["_check"]["walk_lengths"][walk0])),
             f"_check.walk_lengths.{walk0}.walk_lengths"),
            ("_check.left_out", lambda d: d["_check"]["left_out"].append({"map": f"MAP_{B1F}", "why": []}),
             "_check.left_out[].map"),
            ("_check.hm_obstacles", lambda d: d["_check"]["hm_obstacles"][0][1].append({"map": f"MAP_{B1F}"}),
             "_check.hm_obstacles[][][].map"),
        ]
        for leaf, edit, path in plants:  # the plant FIRST (what the gate does), then the entry's flag
            with self.subTest(leaf=leaf, path=path):
                found = self.rule_b(edit)
                self.assertTrue(any("UNCLASSIFIED" in f and repr(path) in f for f in found), found)
                self.assertFalse(schema.get(leaf, ("", "", True))[2], leaf)
        self.assertEqual(self.rule_b(lambda d: None), [])  # CONTROL: the shipped file, unplanted
        mention = self.rule_b(lambda d: (the_way(d)["toward"].append("walk_lengths"),
                                         d.update(_notes=d["_notes"] + " never the walk_lengths")))
        self.assertEqual(mention, [])  # CONTROL: a value that names a developer key is no key
        # every entry that holds a value has its plant above, and (closing pass) no entry of the file is a subtree
        self.assertEqual(sorted({leaf for leaf, _, _ in plants}),
                         sorted(p for p in schema if p not in ("maps", "maps[]", "maps[].ways", "maps[].ways[]")))
        self.assertEqual([pattern for pattern, entry in schema.items() if entry[2]], [])
        self.assertEqual(self.plant(lambda pkg: None), [])  # CONTROL: the copy is clean

        def under_a_way(pkg):
            path = pkg / "knowledge" / "world" / "ways.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["maps"][0]["ways"][0]["script"] = "GraniteCave_B1F_EventScript_Secret"
            path.write_text(json.dumps(doc), encoding="utf-8")
        found = self.plant(under_a_way)
        self.assertTrue(any("world/ways.json" in f and "UNCLASSIFIED" in f and "maps[].ways[].script" in f for f in found),
                        found)

        def inside_a_leaf(pkg):  # (P11-2) the verifier's VM1, byte for byte its plant: a walk length nested in `toward`
            path = pkg / "knowledge" / "world" / "ways.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            way = next(w for m in doc["maps"] if m["id"] == f"MAP_{B1F}" for w in m["ways"]
                       if w["from"] == [4, 21] and w["take"] == [28, 21])
            way["toward"].append({"map": f"MAP_{STEVEN}", "steps": 107})
            path.write_text(json.dumps(doc), encoding="utf-8")
        found = self.plant(inside_a_leaf)
        self.assertTrue(any("world/ways.json" in f and "UNCLASSIFIED" in f and "maps[].ways[].toward[].steps" in f
                            for f in found), found)

        def under_a_map(pkg):
            path = pkg / "knowledge" / "world" / "ways.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["maps"][0]["layout_tiles"] = [[0, 1]]
            path.write_text(json.dumps(doc), encoding="utf-8")
        found = self.plant(under_a_map)
        self.assertTrue(any("UNCLASSIFIED" in f and "maps[].layout_tiles" in f for f in found), found)

    def test_the_loader_and_the_deciding_code_are_gated(self):
        """B2 refuses the loader reading a developer key, and (P11-2, the P11-1 verifier's V5: its mutant VM2 passed the
        gate, `_check` being META) the extractor's walk lengths under `_check`, now DEVELOPER with all under it, its maps
        left out and its HM obstacles. (P11-2's closing pass, the P11-2 verifier's VV3: its VB2 was refused) Deciding code
        that reads a MAP CONST as a key is NOT refused: the map consts are values under `_check`, never developer-only key
        names, so B2 lost nothing and refuses no map const."""
        found = self.plant(self.add("knowledge/ways.py", '\n\ndef leak(way):\n    return way["flag"], way.get("x")\n'))
        self.assertEqual(sorted(f.split("key ")[1].split(" ")[0] for f in found if f.startswith("B2")), ["'flag'", "'x'"])
        found = self.plant(self.add("knowledge/ways.py", '\n\ndef lengths(data):\n    return data["_check"]["walk_lengths"]\n'))
        self.assertEqual(sorted(f.split("key ")[1].split(" ")[0] for f in found if f.startswith("B2")),
                         ["'_check'", "'walk_lengths'"])
        found = self.plant(self.add("knowledge/ways.py", '\n\ndef left(data):\n    return data.get("_check", {}).get("left_out")\n'))
        self.assertEqual(sorted(f.split("key ")[1].split(" ")[0] for f in found if f.startswith("B2")),
                         ["'_check'", "'left_out'"])
        found = self.plant(self.add("knowledge/ways.py", '\n\ndef met(data):\n    return data["_check"]["hm_obstacles"]\n'))
        self.assertEqual(sorted(f.split("key ")[1].split(" ")[0] for f in found if f.startswith("B2")),
                         ["'_check'", "'hm_obstacles'"])
        probe = ('\n\ndef _probe(table):\n    return table.get("MAP_GRANITE_CAVE_B1F"), table["MAP_VICTORY_ROAD_B1F"], '
                 'table.get("MAP_CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP1")\n')
        self.assertEqual(self.plant(self.add("brain/explore.py", probe)), [])  # (closing pass, VV3) no map const refused
        found = self.plant(self.add("brain/explore.py", '\n\nWAYS = "knowledge/world/ways.json"\n'))
        self.assertTrue(any(f.startswith("B1") and "ways.json" in f for f in found), found)
        mention = ('\n\ndef told():\n    """It never reads ways.json\'s way["flag"] or data["_check"]["walk_lengths"]."""\n'
                   '    return "x"\n')
        self.assertEqual(self.plant(self.add("knowledge/ways.py", mention)), [])
        self.assertEqual(self.plant(self.add("brain/explore.py", mention)), [])

    def test_no_developer_key_is_lost_and_the_loader_reads_only_its_keys(self):
        """The ways file un-refuses no developer-only key of the base (a world file's AI names never excuse a name
        elsewhere) and touches no hidden key; (P11-2, V5) what it ADDS to the developer-only names is exactly the names
        under its `_check` (the walk lengths, the maps left out, the HM obstacles met: never read by the AI). The loader
        reads only its keys (an AST pin)."""
        from ai_player.gates import check_fairness as cf_
        loaders = {k: v for k, v in cf_.LOADERS.items() if k != "knowledge/ways.py"}
        with_ways = cf_.developer_keys(knowledge=KNOWLEDGE), cf_.hidden_keys(knowledge=KNOWLEDGE)
        with mock.patch.object(cf_, "LOADERS", loaders):
            without = cf_.developer_keys(knowledge=KNOWLEDGE), cf_.hidden_keys(knowledge=KNOWLEDGE)
        self.assertEqual(without[0] - with_ways[0], set())  # no developer-only key is lost
        self.assertEqual(with_ways[1], without[1])  # the hidden keys are untouched
        check = json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))["_check"]
        under = {"_check"} | {key for path in cf_.key_paths(check) for key in path if key != "[]"}
        self.assertEqual(with_ways[0] - without[0], under)
        self.assertTrue({"_check", "walk_lengths", "left_out", "hm_obstacles"} <= under)
        # (P11-2's closing pass, the P11-2 verifier's VV3) no map const is a developer-only key name: under `_check` each is
        # a VALUE (seven were names on 1cf3ae6a, so B2 refused deciding code that reads a map const as a key)
        self.assertEqual(sorted(k for k in with_ways[0] if re.fullmatch(r"MAP_[A-Z0-9_]+", k)), [])
        source = (KNOWLEDGE / "ways.py").read_text(encoding="utf-8")
        keys = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                keys.add(node.slice.value)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args \
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                keys.add(node.args[0].value)
        self.assertEqual(keys - {"ways"}, {"maps", "id", "from", "take", "leads_to", "toward", "through"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
