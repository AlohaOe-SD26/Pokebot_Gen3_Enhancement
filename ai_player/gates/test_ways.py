"""UNIT PROOFS of P11-1, THE WAY THROUGH A DARK CAVE (2026-11-11). Test side.

    py -3.12 -B ai_player/gates/test_ways.py        (exit 0 = every test passed)

THE CHANGE (`PROJECT KNOWLEDGE/ai-research-notes/2026-11-09-P11-1-DARK-CAVE-DIAGNOSIS.md`, option B with A folded in): on a
DARK map (`requires_flash`) the explorer gets a place at the ladder the static fact (`knowledge/world/ways.json`, written by
`gates/extract_ways.py`, read by `knowledge/ways.py`) names as the way on from the ladder it arrived by toward the intent's
goal; planned through the unseen at the navigator's `UNKNOWN_COST` and redone as the lit circle shows the walls; once in
sight, that ladder (and only that one) outranks the frontier. The AI still sees only the lit circle.

  LoaderTests        the dark maps are exactly maps.json's requires_flash maps; GRANITE CAVE's three ways (B1F (4, 21) ->
                     (28, 21), B2F (28, 21) -> (29, 13), B1F (29, 13) -> (25, 13)) toward STEVEN's room; (round 2) THE WAY
                     THROUGH with no goal: the same three, and (round 2b) NEVER STRAIGHT BACK: none from STEVEN's side, no
                     mark is the warp arrived by and following the marks never cycles (VICTORY ROAD's did); the
                     walk lengths agree with the diagnosis's independent reader (dark_sim P3: 42, 61, 4); the file and the
                     grid model are exactly the extractor's output from the pinned clone (ERRORS without it); FAULT (the
                     file missing): no dark map, no way (the live FAULT arm's code).
  CandidateTests     on the dark model: the fact only ADDS a `way` place (every other place is the same with the fact
                     removed: the FAULT arm is today's explorer); it outranks every frontier; (round 2) NO goal (the live
                     walk toward STEVEN, "not told yet") gives the way through, a goal the fact does not lead toward gives
                     no way; a LIT map: the same places with and without the fact (CONTROL); an unnamed ladder in sight
                     stays a `door` (A is not applied to it: B1F's unnamed (8, 5), reachable from the arrival, leads to a
                     dead end on B2F); the named ladder in sight is a `way` with its press; the latest arrival counts and
                     survives a restore; a `way` walked toward while unseen is stale once seen (navigator.stale_reason).
  ModelTests         THE OFFLINE A/B (the live A/B's shape, on the decomp-drawn model `fixtures/granite_dark_model.json`,
                     the real explorer, the 3x3 lit window, five seeds; bounds MEASURED first, see the class): FIX B2F
                     (28, 21) -> (29, 13) at most 135 steps toward STEVEN and (round 2) GOAL-LESS, FAULT far longer in
                     total; FIX's last B1F stay at most 6 steps; every FIX leg leaves by the named ladder.
  BoundTests         an UNREACHABLE way (the ladder walled off in the model): no hang, the way is given up once the walls
                     are seen (its decisions bounded), and the intent goes on with the frontier.
  FairnessTests      the new world file is classified leaf by leaf; a developer key PLANTED under a way FAILS RULE B (the
                     gate mutant); the loader reading a developer key FAILS B2; deciding code naming ways.json FAILS B1; a
                     mention does not fire; the developer-only keys are exactly those of the base (nothing un-refused); the
                     loader reads only `maps`, `id`, `ways`, `from`, `take`, `leads_to`, `toward`.
"""

from __future__ import annotations

import ast
import json
import os
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
        data = json.loads((WORLD / "maps.json").read_text(encoding="utf-8"))
        flash = sorted(str(m["id"]).removeprefix("MAP_") for m in data["maps"] if m.get("requires_flash"))
        self.assertEqual(len(flash), 7)
        self.assertEqual(sorted(ways_module._ways()), flash)
        for const in flash:
            self.assertTrue(ways_module.dark(const), const)
        for lit in (F1, "ROUTE106", "DEWFORD_TOWN_GYM", "PETALBURG_WOODS", None, ""):
            self.assertFalse(ways_module.dark(lit), lit)

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
        # toward B2F itself from B1F's (4, 21), the nearer ladder (8, 5) is the way (24 steps): the fact is by destination
        self.assertEqual(ways_module.way_on(B1F, (4, 21), lambda name: name == B2F).take, (8, 5))

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
        """DECIDED (A only for the ladder the fact names): from B1F's arrival (4, 21) the unnamed ladder (8, 5) is reachable
        on foot (24 steps) and leads to a part of B2F whose only way on is that ladder back up (the fact's own data, below):
        a seasoned player's 'a lit ladder beats the frontier' applied to EVERY ladder would take it. So an unnamed ladder
        in sight keeps today's value (`Weights.door`), and the named one in sight is the `way`, with its press."""
        data = {m["id"]: m for m in json.loads((WORLD / "ways.json").read_text(encoding="utf-8"))["maps"]}
        dead_end = [w for w in data[f"MAP_{B2F}"]["ways"] if w["from"] == [8, 5]]
        self.assertEqual({tuple(w["take"]) for w in dead_end}, {(8, 5)})  # B2F's (8, 5): its own ladder only
        reach = {tuple(w["take"]) for w in data[f"MAP_{B1F}"]["ways"] if w["from"] == [4, 21]}
        self.assertIn((8, 5), reach)  # reachable from the arrival (4, 21)
        game = model_game((F1, (2, 1)))
        hands, nav, world, notes, lines = rig(game, seed=5)
        arrive(game, nav, (1, 1))
        self.assertEqual((game.map, game.pos), (B1F, (4, 21)))
        game.pos = (8, 6)  # as if it had walked there: the ladder (8, 5) comes into the lit window
        look = game.look()
        world.observe(look)
        found = candidates(nav, look, WEIGHTS["Story"], self.goal(STEVEN), jitter_on=False)
        at_85 = [t for t in found if t.exit == (8, 5)]
        self.assertEqual([t.kind for t in at_85], ["door"], found)
        self.assertEqual([t.kind for t in found if t.kind == "way"], ["way"])
        self.assertEqual([t.tile for t in found if t.kind == "way"], [(28, 21)])
        self.assertGreater(max(t.score for t in found if t.kind == "way"), max(t.score for t in at_85))
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
    FIX's first B1F stay 46-70 against FAULT 122-224 (FAULT took the dead-end ladder (8, 5) in 2 of 5); the last B1F stay
    FIX 4 against FAULT 34-42. The live pass lines are the diagnosis's (B2F about 120, the last stay 6)."""

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
    def add(rel: str, text: str):
        def do(pkg):
            path = pkg / rel
            path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
        return do

    def test_the_file_is_classified_leaf_by_leaf_and_a_planted_developer_key_fails(self):
        from ai_player.gates import check_fairness as cf_
        self.assertIn("world/ways.json", cf_.world_files())
        schema = cf_.KNOWLEDGE_FIELDS["world/ways.json"]
        for container in ("maps", "maps[]", "maps[].ways", "maps[].ways[]"):
            self.assertFalse(schema[container][2], container)  # never a subtree: it would classify any plant
        self.assertEqual(self.plant(lambda pkg: None), [])  # CONTROL: the copy is clean

        def under_a_way(pkg):
            path = pkg / "knowledge" / "world" / "ways.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["maps"][0]["ways"][0]["script"] = "GraniteCave_B1F_EventScript_Secret"
            path.write_text(json.dumps(doc), encoding="utf-8")
        found = self.plant(under_a_way)
        self.assertTrue(any("world/ways.json" in f and "UNCLASSIFIED" in f and "maps[].ways[].script" in f for f in found),
                        found)

        def under_a_map(pkg):
            path = pkg / "knowledge" / "world" / "ways.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["maps"][0]["layout_tiles"] = [[0, 1]]
            path.write_text(json.dumps(doc), encoding="utf-8")
        found = self.plant(under_a_map)
        self.assertTrue(any("UNCLASSIFIED" in f and "maps[].layout_tiles" in f for f in found), found)

    def test_the_loader_and_the_deciding_code_are_gated(self):
        found = self.plant(self.add("knowledge/ways.py", '\n\ndef leak(way):\n    return way["flag"], way.get("x")\n'))
        self.assertEqual(sorted(f.split("key ")[1].split(" ")[0] for f in found if f.startswith("B2")), ["'flag'", "'x'"])
        found = self.plant(self.add("brain/explore.py", '\n\nWAYS = "knowledge/world/ways.json"\n'))
        self.assertTrue(any(f.startswith("B1") and "ways.json" in f for f in found), found)
        mention = '\n\ndef told():\n    """It never reads ways.json\'s way["flag"]."""\n    return "x"\n'
        self.assertEqual(self.plant(self.add("knowledge/ways.py", mention)), [])
        self.assertEqual(self.plant(self.add("brain/explore.py", mention)), [])

    def test_no_developer_key_is_lost_and_the_loader_reads_only_its_keys(self):
        from ai_player.gates import check_fairness as cf_
        loaders = {k: v for k, v in cf_.LOADERS.items() if k != "knowledge/ways.py"}
        with_ways = cf_.developer_keys(knowledge=KNOWLEDGE), cf_.hidden_keys(knowledge=KNOWLEDGE)
        with mock.patch.object(cf_, "LOADERS", loaders):
            without = cf_.developer_keys(knowledge=KNOWLEDGE), cf_.hidden_keys(knowledge=KNOWLEDGE)
        self.assertEqual(with_ways, without)
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
