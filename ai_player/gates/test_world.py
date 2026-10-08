"""UNIT PROOFS of AI-player build step 3 (the WORLD MODEL and the AI's OWN NAVIGATOR). Test side.

    py -3.12 ai_player/gates/test_world.py        (exit 0 = every test passed)

THE GRID MODEL. The navigator is driven, frame by frame, against `GridGame`: a small overworld made of character
maps that reacts to the D-pad the way the measured game does (`gates/live_step3.py` plays the real one): a held
direction moves the player one tile 8 frames in, then one every 16 while held (measured 2026-10-08 on
`pokedex_done.ss1`); a wall, water or a person stops it (a bump: the player walks in place); a ledge is jumped in its
direction only; a DOOR in a wall warps when pressed into from the tile below; STAIRS warp when stepped on; an arrow MAT
warps when pressed toward its arrow while stood on; walking off an edge with a connection lands on the next map (no
fade); a warp fades out, changes the map (the position settling for 2 frames) and fades in. A HIDDEN wall ('H') is
reported by the eyes as floor (what the real eyes do for an elevation step or a one-way tile) and blocks. The eyes
are cropped to the 15 x 11 window, or (the CROP fault, as `AI_PLAYER_FAULT_NO_CROP` does live) show the whole map. A
model is not the game: the live arms play the real one; these tests pin the RULES, each with its FAULT half.

  FrameworkFreeTests  the step-3 files import nothing from the framework or the host; FAULT: a planted import is caught.
  MemoryTests         the memory learns ONLY what was on screen (every tile inside the window of the tile it was seen
                      from); FAULT: with the crop off the same walk learns tiles from outside every window. Visits,
                      the frontier, roads past an edge, persistence (a snapshot read back is the same memory).
  PlannerTests        A* over the memory: unknown tiles optimistic but dearer than known ones, walls and people
                      refused, a ledge one way only (and landing beyond it), never through a warp; seeded noise varies
                      the path, never its length bound; FAULT: an unknown tile priced like a known one plans straight
                      through the unseen.
  WalkTests           the navigator walks a seen room to a tile; a HIDDEN wall is bumped ONCE, learned blocked, and
                      avoided on every later errand (the unique short way through it is never pressed again); FAULT:
                      with bump learning off it bumps the same tile again and again and the intent ends stuck.
  ExitTests           a door (pressed into from below), stairs (stepped on) and a mat (pressed on) are used; the warp
                      graph records each link and infers the way back; a road off the edge is a CONNECTION with its
                      offset and both maps' edges; a scene's warp is the scene's (`by`).
  IntentTests         progress is NOVELTY only, and the budget is NOT reset by it (a map that keeps showing new tiles
                      still ends at the budget); a room with nothing new ends "stuck: nothing new" within its window;
                      a stairs PING-PONG (a scene sends the player back up every time) ends "stuck: ping-pong" at the
                      third use; an unreachable errand ends stuck, never a loop with no frame passing.
  NoveltyTests        (the step-3 verifier) EXPERIENCE gained is novelty, by PID; a torn party read is neither a loss nor
                      a gain; FAULT: with experience ignored, the same looks are nothing new. (Its second round) the
                      navigator TELLS a novelty that is not a place, with the PID, both totals and the clock it moved; an
                      intent whose only novelty is an experience gain ends stuck a window after the GAIN; FAULT: a window
                      after its START, with no novelty told (the live arms XP / XPR play the real one).
  GameAnswerTests     (the second round) `game_answer.py`'s arrival rule: the exit step after a warp, by its behaviour.
  GraderTests         (the second round) `live_step3.py` on synthetic logs: a press a battle PRE-EMPTED (the battle within
                      its two chunks, no move, no turn) is told from one the game took; an INCONCLUSIVE answer with
                      nothing else FAILS.
  CropTests           the real explorer's every target is a tile it had SEEN, inside the window it was seen from;
                      FAULT (the crop off): the first target is a road it could not have seen, and the walk to it is the
                      true shortest walk onto that road (a beeline), shorter than exploring.
  ExploreTests        the PERSONALITY weights: on one memory with a road, a door and tall grass, Story goes for the road,
                      Catcher and Trainer for the grass, Trainer toward people; the door just come out of is worth only
                      `Weights.back` while this map has something to see (found by the seed sweep: a lab -> town -> lab
                      ping-pong); a target excluded on one map is not excluded on another; NEVER IDLE: with nothing new
                      in sight it wanders to the least-visited tile. (The step-3 verifier) A WHIM AMONG EQUALS: places
                      within `CHOICE_MARGIN` are picked by seed, the better more often, a clear winner always; on one
                      town, eight seeds head off in different directions; FAULT (margin 0): every seed picks the same /
                      heads north.
  RoamTests           roaming through a grass patch: the spin ratio stays < 2%, the distinct tiles grow, the walk
                      never steps straight back unless it must (3 seeds x 200 steps in an open meadow: none); a person in
                      the only way on is WAITED for (a ring of grass; FAULT: no wait, it turns straight back); FAULT: a
                      naive two-tile spin is measured as ~100% spin. (The step-3 verifier) With WILD ENCOUNTERS
                      (`EncounterGame`, both timings): every roam press is an attempt, the training steps are the model's
                      own steps, the path stays one tile a step across every battle.
  FleeTests           the battle's action menu: RUN is reached by READING the 2 x 2 cursor (Right, Down, A) and only
                      pressed on it; a TRAINER battle returns the reason with no press on the menu.
"""

from __future__ import annotations

import ast
import json
import os
import random
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
from ai_player.brain import navigator as navigator_module  # noqa: E402
from ai_player.brain.explore import (  # noqa: E402
    VALUE_TILES, WEIGHTS, candidates, choose_target, explore_intent, goto_intent, pick,
)
from ai_player.brain.navigator import (  # noqa: E402
    NOVELTY_WINDOW, PINGPONG_USES, UNKNOWN_COST, Intent, Navigator, Novelty, Target, astar, step_from,
)
from ai_player.eyes.observation import (  # noqa: E402
    BattleMon, BattleView, MenuView, MonSummary, Observation, PlayerState, ScreenState, SeenObject, Tile, View,
)
from ai_player.eyes.screens import BATTLE_ACTIONS  # noqa: E402
from ai_player.hands.pad import Faults, Hands  # noqa: E402
from ai_player.skills.flee import RUN, TRAINER_OUT_OF_SCOPE, flee  # noqa: E402
from ai_player.skills import roam_train as roam_module  # noqa: E402
from ai_player.skills.roam_train import roam_train, spin_count  # noqa: E402
from ai_player.world import memory as memory_module  # noqa: E402
from ai_player.world.memory import WorldMemory, in_window, read_world  # noqa: E402

PACKAGE = REPO / "ai_player"
#: The files build step 3 added (each must stay framework-free and host-free).
STEP3_FILES = ("world/__init__.py", "world/memory.py", "brain/__init__.py", "brain/navigator.py", "brain/explore.py",
               "skills/roam_train.py", "skills/flee.py")
DIRS = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
LEDGES = {"v": ("south", (0, 1)), ">": ("east", (1, 0)), "<": ("west", (-1, 0)), "^": ("north", (0, -1))}


# ------------------------------------------------------------------------------------------- the grid model
class GridGame:
    """The overworld model (module docstring). `maps`: name -> rows; `warps`: (map, (x, y)) -> (map, (x, y));
    `links`: (map, side) -> (map, (dx, dy)) added to a tile past that side; `people`: map -> tiles; `scene_on`:
    map -> (frames, (map, (x, y))): arriving there starts a scene that sends the player to that place."""

    def __init__(self, maps: dict[str, list[str]], start: tuple[str, tuple[int, int]], warps=None, links=None, people=None,
                 scene_on=None, crop: bool = True, leaving=None) -> None:
        self.maps = maps
        self.map, self.pos = start[0], start[1]
        self.warps = warps or {}
        self.links = links or {}
        self.people = people or {}
        self.leaving = leaving or {}
        self.scene_on = scene_on or {}
        self.crop = crop
        self.facing = "down"
        self.frame = 0
        self.held: str | None = None
        self.charge = 0
        self.moving = 0
        self.warp_out = 0
        self.warp_in = 0
        self.pending = None
        self.scene = 0
        self.scene_to = None
        self.bumps = 0
        self.bumping = False
        self.bump_frames = 0
        self.steps = 0
        self.pressed: list[tuple[int, str, str, tuple[int, int]]] = []  # (frame, map, button, from)

    # ---------------------------------------------------------------- the rules
    def char(self, name: str, xy: tuple[int, int]) -> str:
        rows = self.maps[name]
        x, y = xy
        if 0 <= y < len(rows) and 0 <= x < len(rows[0]):
            return rows[y][x]
        side = "up" if y < 0 else "down" if y >= len(rows) else "left" if x < 0 else "right"
        link = self.links.get((name, side))
        if link is None:
            return "#"
        other, (dx, dy) = link
        rows2 = self.maps[other]
        x2, y2 = x + dx, y + dy
        return rows2[y2][x2] if 0 <= y2 < len(rows2) and 0 <= x2 < len(rows2[0]) else "#"

    def people_now(self) -> set:
        """The people standing on this map now: `people` stay; `leaving` ((map, tile) -> frame) stand until that frame."""
        here = set(self.people.get(self.map, set()))
        here |= {xy for (name, xy), until in self.leaving.items() if name == self.map and self.frame < until}
        return here

    def inside(self, name: str, xy: tuple[int, int]) -> bool:
        rows = self.maps[name]
        return 0 <= xy[1] < len(rows) and 0 <= xy[0] < len(rows[0])

    def tick(self, button: str | None, new: bool) -> None:
        self.frame += 1
        if new and button is not None:
            self.pressed.append((self.frame, self.map, button, self.pos))
            self.bumping = False
        if self.warp_out:
            self.warp_out -= 1
            if not self.warp_out:
                self.map, self.pos = self.pending
                self.pending = None
                self.warp_in = 10
                if self.map in self.scene_on:
                    frames, self.scene_to = self.scene_on[self.map]
                    self.scene = frames
            return
        if self.warp_in:
            self.warp_in -= 1
            return
        if self.scene:
            self.scene -= 1
            if not self.scene and self.scene_to is not None:
                self.pending, self.scene_to = self.scene_to, None
                self.warp_out = 20
            return
        direction = button if button in DIRS else None
        if direction != self.held:
            self.held, self.charge = direction, 0
        if self.moving:
            self.moving -= 1
            if self.moving or direction is None:
                return
            self.attempt(direction)
            return
        if direction is None:
            return
        self.facing = direction.lower()
        self.charge += 1
        if self.charge >= 8:
            self.charge = 0
            self.attempt(direction)

    def attempt(self, button: str) -> None:
        dx, dy = DIRS[button]
        self.facing = button.lower()
        here = self.char(self.map, self.pos)
        target = (self.pos[0] + dx, self.pos[1] + dy)
        c = self.char(self.map, target)
        if here == "M" and button == "Down" and (c == "#" or not self.inside(self.map, target)):
            self.start_warp(self.pos)
            return
        if c == "D" and button == "Up":
            self.start_warp(target)
            return
        if not self.inside(self.map, target) and c != "#":
            side = "up" if target[1] < 0 else "down" if target[1] >= len(self.maps[self.map]) else "left" if target[0] < 0 else "right"
            other, (ox, oy) = self.links[(self.map, side)]
            self.map, self.pos = other, (target[0] + ox, target[1] + oy)
            self.moving, self.steps = 16, self.steps + 1
            return
        if c in "#~HD" or target in self.people_now():
            self.bump()
            return
        if c in LEDGES:
            if LEDGES[c][1] != (dx, dy):
                self.bump()
                return
            self.pos = (target[0] + dx, target[1] + dy)
            self.moving, self.steps = 32, self.steps + 1
            return
        self.pos = target
        self.moving, self.steps = 16, self.steps + 1
        if c == "S":
            self.start_warp(target)

    def bump(self) -> None:
        """Walking in place against something: one BUMP per press held against it (as a person counts them); every
        attempt (one per 8 frames held) adds to `bump_frames`."""
        if not self.bumping:
            self.bumps += 1
        self.bumping = True
        self.bump_frames += 8

    def start_warp(self, tile: tuple[int, int]) -> None:
        self.pending = self.warps[(self.map, tile)]
        self.warp_out = 20

    # ---------------------------------------------------------------- what the eyes report
    def screen(self) -> ScreenState:
        return ScreenState(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False,
                           waits_for_button=False, in_battle=False, script_running=bool(self.scene),
                           controls_locked=bool(self.scene), fading=bool(self.warp_out or self.warp_in))

    def player(self) -> PlayerState:
        settling = self.warp_in > 8
        index = sorted(self.maps).index(self.map)
        return PlayerState(map_group=0, map_number=index, map_name=self.map, map_const=self.map,
                           x=None if settling else self.pos[0], y=None if settling else self.pos[1], facing=self.facing,
                           movement="walking", elevation=3, avatar_flags=0, trainer_id=1, settling=settling)

    def tile(self, x: int, y: int, dx: int, dy: int) -> Tile:
        c = self.char(self.map, (x, y))
        names = {".": "NORMAL", "#": "NORMAL", '"': "TALL_GRASS", "~": "POND_WATER", "D": "ANIMATED_DOOR",
                 "S": "NON_ANIMATED_DOOR", "M": "SOUTH_ARROW_WARP", "H": "NORMAL"}
        ledge = LEDGES[c][0] if c in LEDGES else None
        return Tile(x=x, y=y, dx=dx, dy=dy, metatile=0, behavior=0, behavior_name=names.get(c, "JUMP"),
                    collision=1 if c in "#D" else 0, elevation=3, blocked=c in "#D", water=c == "~",
                    encounter="land" if c == '"' else None, tall_grass=c == '"', ledge=ledge, door=c in "DS",
                    warp=c in "DSM", half_visible=abs(dy) == 5)

    def view(self) -> View | None:
        if self.warp_in > 8:
            return None
        px, py = self.pos
        if self.crop:
            left = right = 7
            up = down = 5
        else:
            rows = self.maps[self.map]
            left, right, up, down = px + 7, len(rows[0]) - 1 - px + 7, py + 7, len(rows) - 1 - py + 7
        rows = tuple(tuple(self.tile(px + dx, py + dy, dx, dy) for dx in range(-left, right + 1)) for dy in range(-up, down + 1))
        objects = tuple(SeenObject("npc", x, y, x - px, y - py, 1, 7, "down", 3, "object")
                        for x, y in sorted(self.people_now())
                        if not self.crop or (abs(x - px) <= 7 and abs(y - py) <= 5))
        return View(left=left, right=right, up=up, down=down, rows=rows, objects=objects, cropped=self.crop)

    def look(self) -> Observation:
        return Observation(frame=self.frame, screen=self.screen(), player=self.player(), view=self.view(), party=(),
                           bag=None, progress=None, battle=None, last_battle_outcome=0, problems=(), cost_ms=0.0)


class GridControls:
    """The brain's `Controls` on a model. Back-to-back holds of one button are ONE continuous hold, as with the
    emulator (`host/controller.py`: the release and the next hold happen between the same two frames)."""

    def __init__(self, game) -> None:
        self.game = game
        self.last: str | None = None

    def wait(self, frames: int):
        for _ in range(frames):
            self.last = None
            self.game.tick(None, False)
            yield

    def tap(self, button: str):
        yield from self.hold(button, 1)
        yield from self.wait(1)

    def hold(self, button: str, frames: int):
        for _ in range(frames):
            new = button != self.last
            self.last = button
            self.game.tick(button, new)
            yield


class GridEyes:
    def __init__(self, game) -> None:
        self.game = game

    def look(self) -> Observation:
        return self.game.look()


class Notes:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, look, decision: str, action: str, reason: str, extra: dict | None = None) -> None:
        self.records.append({"frame": None if look is None else look.frame, "decision": decision, "action": action,
                             "reason": reason, "extra": extra or {}})


def rig(game, seed: int = 3, personality: str = "Story", world: WorldMemory | None = None):
    notes, lines = Notes(), []
    hands = Hands(GridEyes(game), GridControls(game), random.Random(f"{seed}:pacing"), random.Random(f"{seed}:choices"),
                  notes, lines.append, Faults())
    world = world or WorldMemory()
    hands.watchers.append(world.observe)
    nav = Navigator(hands, world, hands.choices, WEIGHTS[personality].grass_cost, personality)
    return hands, nav, world, notes, lines


def drive(generator, budget: int = 60_000):
    for _ in range(budget):
        try:
            next(generator)
        except StopIteration as done:
            return done.value
    raise AssertionError("the generator did not end within the budget")


ROOM = [  # a room with a hidden wall at (4, 3): the short way from (3, 3) to (5, 3) is through it
    "#########",
    "#.......#",
    "#.......#",
    "#...H...#",
    "#.......#",
    "#########",
]


# ------------------------------------------------------------------------------------------- tests
class FrameworkFreeTests(unittest.TestCase):
    @staticmethod
    def foreign_imports(source: str) -> list[str]:
        found = []
        for node in ast.walk(ast.parse(source)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            found += [n for n in names if n.split(".")[0] in ("modules", "plugins", "mgba") or n.startswith("ai_player.host")]
        return found

    def test_step3_files_import_no_framework_and_no_host(self) -> None:
        for relative in STEP3_FILES:
            with self.subTest(file=relative):
                self.assertEqual(self.foreign_imports((PACKAGE / relative).read_text(encoding="utf-8")), [])

    def test_fault_a_planted_import_is_caught(self) -> None:
        planted = (PACKAGE / "brain/navigator.py").read_text(encoding="utf-8") + "\nfrom modules.map_path import calculate_path\n"
        self.assertEqual(self.foreign_imports(planted), ["modules.map_path"])


class MemoryTests(unittest.TestCase):
    def walk(self, crop: bool) -> WorldMemory:
        wide = ["#" * 40] + ["#" + "." * 38 + "#" for _ in range(20)] + ["#" * 40]
        game = GridGame({"FIELD": wide}, ("FIELD", (3, 10)), crop=crop)
        hands, nav, world, _, _ = rig(game)
        drive(nav.go_to((30, 10), "walk east", 4000))
        return world

    def test_only_what_was_on_screen(self) -> None:
        world = self.walk(crop=True)
        memory = world.here()
        outside = [xy for xy, fact in memory.tiles.items() if not in_window(fact.seen_from, xy)]
        self.assertGreater(len(memory.tiles), 165)
        self.assertEqual(outside, [], "every known tile lies inside the window of the tile it was seen from")
        self.assertNotIn((39, 10), memory.tiles, "the far wall was never on screen")

    def test_fault_the_crop_off_learns_what_no_window_showed(self) -> None:
        world = self.walk(crop=False)
        memory = world.here()
        outside = [xy for xy, fact in memory.tiles.items() if not in_window(fact.seen_from, xy)]
        self.assertGreater(len(outside), 100)
        self.assertIn((39, 10), memory.tiles)

    def test_visits_frontier_roads_and_persistence(self) -> None:
        maps = {"A": ["##.##", "#...#", "#...#", "#...#", "#####"], "B": ["#...#", "#...#"]}
        game = GridGame(maps, ("A", (2, 3)), links={("A", "up"): ("B", (0, 2)), ("B", "down"): ("A", (0, -2))})
        hands, nav, world, _, _ = rig(game)
        drive(nav.go_to((2, 1), "to the gap", 600))
        memory = world.here()
        self.assertEqual(memory.visits[(2, 1)], 1)
        self.assertIn((2, -1), memory.roads(), "a walkable tile past the top edge (y < 0) is a road")
        self.assertNotIn((2, -1), memory.frontier())
        self.assertNotIn((2, 5), memory.roads(), "past an edge the AI has not crossed, a tile is not known to be another map's")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "world.jsonl"
            path.write_text(world.snapshot() + "\n", encoding="utf-8")
            again = read_world(path)
        self.assertEqual(again.to_dict(), world.to_dict())


class PlannerTests(unittest.TestCase):
    def memory_of(self, rows: list[str], seen: set | None = None):
        game = GridGame({"M": rows}, ("M", (1, 1)), crop=False)
        world = WorldMemory()
        world.observe(game.look())
        memory = world.here()
        if seen is not None:
            for xy in list(memory.tiles):
                if xy not in seen:
                    del memory.tiles[xy]
        return memory

    def test_walls_people_ledges_and_warps(self) -> None:
        memory = self.memory_of(["#######", "#..v..#", "#..#..#", "#.....#", "#S....#", "#######"])
        self.assertIsNone(step_from(memory, (3, 3), "up", frozenset(), 0.0))  # a wall
        self.assertEqual(step_from(memory, (3, 0), "down", frozenset(), 0.0), None)  # (3, 1) is a ledge: lands on the wall
        self.assertIsNone(step_from(memory, (2, 1), "right", frozenset(), 0.0), "a ledge is not entered sideways")
        self.assertIsNone(step_from(memory, (1, 3), "down", frozenset(), 0.0), "stairs are used on purpose, not walked through")
        self.assertIsNone(step_from(memory, (2, 3), "right", frozenset({(3, 3)}), 0.0), "a person is a wall for now")
        ledge = self.memory_of(["#####", "#...#", "#.v.#", "#...#", "#####"])
        self.assertEqual(step_from(ledge, (2, 1), "down", frozenset(), 0.0), ((2, 3), 2.0), "jumped: lands beyond the ledge")

    UNSEEN = {(4, 1), (4, 2), (5, 1), (5, 2)}  # a 2 x 2 block never on screen, with a seen way round below it

    def test_unknown_is_optimistic_but_dearer(self) -> None:
        rows = ["##########", "#........#", "#........#", "#........#", "##########"]
        memory = self.memory_of(rows, {(x, y) for x in range(10) for y in range(5)} - self.UNSEEN)
        self.assertEqual(step_from(memory, (3, 2), "right", frozenset(), 0.0), ((4, 2), UNKNOWN_COST), "optimistic: walkable")
        path = astar(memory, (3, 2), {(6, 2)}, frozenset(), 0.0)
        self.assertEqual(path, ["down", "right", "right", "right", "up"], "5 seen tiles (5) beat 2 unseen ones (1 + 2 x 3)")
        # an unseen tile with no way round is crossed (it may well be walkable: that is how the AI explores)
        corridor = self.memory_of(["#####", "#...#", "#####"], {(1, 1), (3, 1)} | {(x, y) for x in range(5) for y in (0, 2)})
        self.assertEqual(astar(corridor, (1, 1), {(3, 1)}, frozenset(), 0.0), ["right", "right"])

    def test_fault_an_unknown_tile_priced_like_a_known_one(self) -> None:
        rows = ["##########", "#........#", "#........#", "#........#", "##########"]
        memory = self.memory_of(rows, {(x, y) for x in range(10) for y in range(5)} - self.UNSEEN)
        with mock.patch.object(navigator_module, "UNKNOWN_COST", 1.0):
            naive = astar(memory, (3, 2), {(6, 2)}, frozenset(), 0.0)
        self.assertEqual(naive, ["right", "right", "right"], "priced like a known tile: straight through the unseen")

    def test_seeded_noise_varies_the_path_not_its_length(self) -> None:
        rows = ["#" * 12] + ["#" + "." * 10 + "#" for _ in range(8)] + ["#" * 12]
        memory = self.memory_of(rows)
        paths = set()
        for seed in range(12):
            nav = Navigator(Hands(None, None, random.Random(1), random.Random(seed), None, lambda l: None), WorldMemory(),
                            random.Random(seed))
            path = astar(memory, (1, 1), {(9, 7)}, frozenset(), 0.0, nav.noise_for(Target("goto", (9, 7), "x")))
            self.assertLessEqual(len(path), 14 + 4)
            paths.add(tuple(path))
        self.assertGreater(len(paths), 3, f"12 seeds gave {len(paths)} different paths")


class WalkTests(unittest.TestCase):
    def errands(self, learn: bool = True):
        game = GridGame({"ROOM": ROOM}, ("ROOM", (2, 3)))
        hands, nav, world, notes, lines = rig(game)
        if learn:
            outcome = drive(nav.run(goto_intent([(5, 3), (2, 3), (5, 3)], 6000), "errands"))
        else:  # FAULT: the bump is told, and NOT remembered
            with mock.patch.object(WorldMemory, "learn_bump", lambda self, frm, direction, frame: (frm[0] + 1, frm[1])):
                outcome = drive(nav.run(goto_intent([(5, 3), (2, 3), (5, 3)], 6000), "errands"))
        return game, world, outcome, notes, nav

    def test_a_hidden_wall_is_bumped_once_and_avoided(self) -> None:
        game, world, outcome, notes, nav = self.errands()
        self.assertTrue(outcome.startswith("done"), outcome)
        self.assertEqual(list(world.here().bumped), [(4, 3)])
        self.assertEqual((game.bumps, nav.stats.bumps), (1, 1), "bumped once")
        self.assertLessEqual(game.bump_frames, 40, "about one bump's worth of walking in place")
        into = [r for r in notes.records if str(r["reason"]).startswith("walk") and "-> (4, 3)" in r["reason"]]
        self.assertEqual(len(into), 1, f"pressed toward the hidden wall once only: {[r['reason'][:60] for r in into]}")
        self.assertEqual(game.pos, (5, 3))

    def test_fault_without_learning_it_bumps_again_and_again(self) -> None:
        game, world, outcome, notes, nav = self.errands(learn=False)
        self.assertTrue(outcome.startswith("stuck"), outcome)
        self.assertGreater(nav.stats.bumps, 10)
        self.assertGreater(game.bump_frames, 1000, "it walked in place against the same tile for most of a minute")


class ExitTests(unittest.TestCase):
    def house(self, scene: bool = False):
        maps = {
            "UP": ["#########", "#######S#", "#.......#", "#.......#", "#########"],
            "DOWN": ["###########", "########S##", "#.........#", "#.........#", "#.......MM#", "###########"],
            "TOWN": ["#########", "#.......#", "####D####", "#.......#", "#.......#", "#########"],
        }
        warps = {("UP", (7, 1)): ("DOWN", (8, 2)), ("DOWN", (8, 1)): ("UP", (7, 2)), ("DOWN", (8, 4)): ("TOWN", (4, 3)),
                 ("DOWN", (9, 4)): ("TOWN", (4, 3)), ("TOWN", (4, 2)): ("DOWN", (8, 3))}
        scene_on = {"DOWN": (60, ("UP", (7, 2)))} if scene else None
        return GridGame(maps, ("UP", (2, 2)), warps=warps, scene_on=scene_on)

    def test_stairs_mat_and_the_warp_graph(self) -> None:
        game = self.house()
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(explore_intent("TOWN", "Story", 8000), "leave the house"))
        self.assertTrue(outcome.startswith("done"), outcome)
        self.assertEqual(game.map, "TOWN")
        keys = {map_name: key for key, map_name in world.names().items()}
        self.assertIn(f"{keys['UP']}|7,1", world.warps)
        self.assertEqual(world.warps[f"{keys['UP']}|7,1"]["to"], keys["DOWN"])
        self.assertEqual(world.warps[f"{keys['UP']}|7,1"]["by"], "ai")
        self.assertTrue(any(name.startswith(keys["DOWN"]) and link["inferred"] for name, link in world.warps.items()),
                        "the stairs at the arrival are inferred as the way back up")
        self.assertEqual([t.how for t in world.transitions], ["warp", "warp"])

    def test_a_door_is_pressed_into_from_below(self) -> None:
        maps = {"TOWN": ["#########", "#.......#", "####D####", "#.......#", "#.......#", "#########"],
                "IN": ["#####", "#...#", "#####"]}
        game = GridGame(maps, ("TOWN", (2, 4)), warps={("TOWN", (4, 2)): ("IN", (2, 1))})
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(explore_intent("IN", "Story", 4000), "go in"))
        self.assertTrue(outcome.startswith("done"), outcome)
        presses = [r for r in notes.records if str(r["reason"]).startswith("use the door at (4, 2)")]
        self.assertTrue(presses and all(r["action"].startswith("hold Up") for r in presses))

    def test_a_road_is_a_connection_with_its_offset_and_edges(self) -> None:
        maps = {"TOWN": ["####..####", "#........#", "#........#", "##########"], "ROUTE": ["#..#", "#..#", "#..#"]}
        links = {("TOWN", "up"): ("ROUTE", (-3, 3)), ("ROUTE", "down"): ("TOWN", (3, -3))}
        game = GridGame(maps, ("TOWN", (2, 2)), links=links)
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(explore_intent("ROUTE", "Story", 4000), "leave town"))
        self.assertTrue(outcome.startswith("done"), outcome)
        connection = world.connections[0]
        self.assertEqual((connection["direction"], connection["offset"]), ("up", [-3, 3]))
        route = world.here()
        self.assertEqual(route.edges.get("down"), 3, "the route's bottom edge learned at the crossing")
        self.assertEqual(world.transitions[0].how, "connection")

    def test_a_scenes_warp_is_the_scenes(self) -> None:
        game = self.house(scene=True)
        hands, nav, world, notes, lines = rig(game)
        drive(nav.run(explore_intent("TOWN", "Story", 6000), "leave the house"))
        bys = [(t.how, t.by) for t in world.transitions]
        self.assertIn(("warp", "scene"), bys, bys)
        self.assertIn(("warp", "ai"), bys, bys)


class IntentTests(unittest.TestCase):
    def test_the_budget_is_not_reset_by_novelty(self) -> None:
        wide = ["#" * 200] + ["#" + "." * 198 + "#" for _ in range(12)] + ["#" * 200]
        game = GridGame({"PLAIN": wide}, ("PLAIN", (3, 6)))
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(explore_intent(None, "Story", 900), "explore"))
        self.assertTrue(outcome.startswith("budget"), outcome)
        self.assertLessEqual(hands.pad.frames, 900 + 100, "ended at its budget, new tiles every step notwithstanding")
        self.assertGreater(world.tiles_learned, 300, "it WAS seeing new tiles all along")

    def test_nothing_new_is_stuck_within_the_window(self) -> None:
        room = ["#######", "#.....#", "#.....#", "#######"]
        game = GridGame({"CELL": room}, ("CELL", (2, 1)))
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(explore_intent(None, "Story", 20000), "explore"))
        self.assertTrue(outcome.startswith("stuck"), outcome)
        self.assertLess(hands.pad.frames, NOVELTY_WINDOW + 800)

    def test_a_stairs_ping_pong_is_stuck_at_the_third_use(self) -> None:
        game = ExitTests().house(scene=True)
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(explore_intent("TOWN", "Story", 20000), "leave the house"))
        self.assertTrue(outcome.startswith("stuck: ping-pong"), outcome)
        uses = [t for t in world.transitions if t.by == "ai"]
        self.assertEqual(len(uses), PINGPONG_USES)
        self.assertLess(hands.pad.frames, 6000)

    def test_an_unreachable_errand_is_stuck_not_a_loop(self) -> None:
        game = GridGame({"ROOM": ROOM}, ("ROOM", (2, 3)))
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(goto_intent([(0, 0)], 3000), "into the wall"), budget=10000)
        self.assertTrue(outcome.startswith("stuck"), outcome)


class NoveltyTests(unittest.TestCase):
    """EXPERIENCE GAINED is progress (design draft §10.4 lists it; the step-3 verifier found it uncounted): a party
    Pokemon's total experience rising, by PID. A party not read (a torn read: None) is not a loss and not a gain."""

    @staticmethod
    def look(frame: int, experience: int | None) -> Observation:
        base = GridGame({"CELL": ["#####", "#...#", "#####"]}, ("CELL", (1, 1))).look()
        if experience is None:
            return replace(base, frame=frame, party=None)
        mon = MonSummary(slot=0, species="Mudkip", dex=258, level=5, hp=20, max_hp=20, status="ok", types=("Water",),
                         moves=(), pid=77, ot_id=1, is_egg=False, experience=experience)
        return replace(base, frame=frame, party=(mon,))

    def updates(self) -> tuple[list, Novelty]:
        world = WorldMemory()
        first = self.look(10, 135)
        world.observe(first)
        novelty = Novelty(world, first)
        return [novelty.update(self.look(frame, value)) for frame, value in ((20, 135), (30, None), (40, 160), (50, 160))], novelty

    def test_experience_gained_is_progress(self) -> None:
        seen, novelty = self.updates()
        self.assertEqual(seen, [[], [], ["experience gained (1 Pokemon)"], []])
        self.assertEqual(novelty.last, 40, "the newest novelty is the experience gained at f40")

    def test_fault_without_experience_a_battle_won_is_nothing_new(self) -> None:
        with mock.patch.object(Novelty, "_experience", staticmethod(lambda look: None)):
            seen, novelty = self.updates()
        self.assertEqual(seen, [[], [], [], []])
        self.assertEqual(novelty.last, 10)

    # ---- the step-3 verifier's second round: "no live run has yet shown an intent's novelty clock reset by an XP gain"
    # (the live proof is `live_step3.py` arm XP and its revert XPR; these pin the rule the arms rest on)
    def test_the_notable_novelty_names_the_pid_and_both_totals(self) -> None:
        world = WorldMemory()
        first = self.look(10, 135)
        world.observe(first)
        novelty = Novelty(world, first)
        notable = []
        for frame, value in ((20, 135), (30, None), (40, 160), (50, 160)):
            novelty.update(self.look(frame, value))
            notable.append(list(novelty.notable))
        self.assertEqual(notable, [[], [], ["experience gained (PID 0000004d: 135 -> 160)"], []])

    @staticmethod
    def xp_walk() -> tuple[str, list[dict], int]:
        """Errands back and forth across a room walked once before (a warm-up intent: everything in sight is known);
        the party's experience rises at `XpGame.GAIN_AT` (a battle won elsewhere): the ONLY novelty of the intent."""
        game = XpGame({"CELL": ["#######", "#.....#", "#######"]}, ("CELL", (1, 1)))
        hands, nav, world, notes, lines = rig(game)
        drive(nav.run(goto_intent([(5, 1), (1, 1)], 3000), "a warm-up: see the room"), budget=10_000)
        assert game.frame < XpGame.GAIN_AT, game.frame
        notes.records.clear()
        outcome = drive(nav.run(goto_intent([(5, 1), (1, 1)] * 200, 20000), "errands"), budget=40_000)
        told = [r for r in notes.records if r["decision"] == "world" and str(r["reason"]).startswith("novelty at f")]
        return outcome, told, hands.pad.frames

    def test_the_navigator_tells_the_experience_and_the_clock_it_moved(self) -> None:
        outcome, told, frames = self.xp_walk()
        self.assertEqual(len(told), 1, told)
        self.assertEqual(told[0]["extra"]["novelty"], ["experience gained (PID 550a9be6: 100 -> 130)"])
        start, gain = told[0]["extra"]["clock"]
        self.assertGreaterEqual(gain, XpGame.GAIN_AT)
        self.assertLess(start, XpGame.GAIN_AT)
        self.assertTrue(outcome.startswith("stuck: nothing new"), outcome)
        self.assertIn(f"the last at f{gain}: experience gained", outcome)
        self.assertGreaterEqual(frames, gain + NOVELTY_WINDOW, "stuck a whole window after the GAIN, not after the start")

    def test_fault_without_experience_the_clock_never_moves(self) -> None:
        real = self.xp_walk()[2]
        with mock.patch.object(Novelty, "_experience", staticmethod(lambda look: None)):
            outcome, told, frames = self.xp_walk()
        self.assertEqual(told, [])
        self.assertRegex(outcome, r"the last at f\d+: none \(")
        self.assertLess(frames, real - 300, "stuck a window after the START: the gain did not count")


class XpGame(GridGame):
    """The grid model with a party of one whose experience rises at `GAIN_AT` (a battle won off-screen)."""

    GAIN_AT = 600

    def look(self) -> Observation:
        mon = MonSummary(slot=0, species="Mudkip", dex=258, level=9, hp=19, max_hp=30, status="ok", types=("Water",),
                         moves=(), pid=0x550A9BE6, ot_id=1, is_egg=False, experience=100 if self.frame < self.GAIN_AT else 130)
        return replace(super().look(), party=(mon,))


class GameAnswerTests(unittest.TestCase):
    """(the step-3 verifier's second round) `gates/game_answer.py`'s ARRIVAL rule, pure: after a warp, the exit task
    walks one step for a door or a non-animated door (south), north for a deep-south warp, none otherwise
    (`src/overworld.c` GetAdjustedInitialDirection, `src/field_screen_effect.c` SetUpWarpExitTask)."""

    def test_the_exit_step(self) -> None:
        from ai_player.gates.game_answer import exit_tile

        self.assertEqual(exit_tile((8, 2), "Non-Animated Door"), (8, 3), "the house's stairs: STUCK's end tile")
        self.assertEqual(exit_tile((6, 12), "Door Warp"), (6, 13))
        self.assertEqual(exit_tile((4, 4), "Deep South Warp"), (4, 3))
        self.assertEqual(exit_tile((6, 12), "Normal"), (6, 12), "a plain warp (a mat): no step")

    def test_a_walking_answer_needs_a_step(self) -> None:
        """Found by the graded run: on a state where a scene holds the controls, a claim whose only clean line is "0
        steps, then a wall" agreed; such a line cannot tell standing before a wall from not moving at all."""
        from ai_player.gates.game_answer import walking_agrees

        def trial(steps: int, agree: bool) -> dict:
            return {"predicted": {"steps": steps}, "agree": agree}

        self.assertFalse(walking_agrees([trial(0, True)], True), "STUCK's fault claim (7, 3): Up 0 steps, 0 counted")
        self.assertTrue(walking_agrees([trial(0, True), trial(3, True)], True), "BUMP: Left 0 and Down 3")
        self.assertFalse(walking_agrees([trial(3, False)], True))
        self.assertFalse(walking_agrees([trial(3, True)], False), "the loaded map is not the claimed one")
        self.assertFalse(walking_agrees([], True), "no trial: inconclusive")


class GraderTests(unittest.TestCase):
    """(the step-3 verifier's second round) `gates/live_step3.py`'s graders on synthetic action logs: a press a battle
    PRE-EMPTED is told from one the game took (a turn, a move, a battle too late); an INCONCLUSIVE game answer with no
    other answer FAILS (it used to pass on the map header alone)."""

    @staticmethod
    def records(facing_after: str, battle_after: int, moved: bool = False) -> list[dict]:
        def rec(frame, decision, action, reason, xy, facing, kind="overworld", pad=0):
            return {"frame": frame, "decision": decision, "action": action, "reason": reason, "extra": {"pad_frame": pad, "hold": 8},
                    "digest": f"f{frame} {kind} ROUTE 101(0,16) xy=({xy[0]},{xy[1]}) facing={facing} walking"}

        return [rec(100, "train", "hold Right 8f", "roam right: (4, 14) -> (5, 14)", (4, 14), "up", pad=500),
                rec(108, "train", "hold Right 8f", "keep walking right: the step", (5, 14) if moved else (4, 14), facing_after, pad=508),
                rec(100 + battle_after, "watch", "busy 100f", "watching: a battle starting", (4, 14), facing_after, "battle", 500 + battle_after)]

    def preemption(self, *args, **kwargs) -> dict:
        from ai_player.gates import live_step3

        run = live_step3.Run(live_step3.ARMS[0], records=self.records(*args, **kwargs))
        return live_step3.preemption(run, run.records[0])

    def test_a_preempted_press_and_three_that_were_not(self) -> None:
        good = self.preemption("up", 16)
        self.assertEqual((good["battle_after_pad_frames"], good["moved_before_the_battle"], good["turned_before_the_battle"]),
                         (16, False, False))
        self.assertTrue(self.preemption("right", 16)["turned_before_the_battle"], "the press turned the player: taken")
        self.assertTrue(self.preemption("up", 16, moved=True)["moved_before_the_battle"], "the press moved it: taken")
        self.assertEqual(self.preemption("up", 40)["battle_after_pad_frames"], 40, "a battle long after the press")

    def test_an_inconclusive_answer_with_nothing_else_fails(self) -> None:
        from ai_player.gates import live_step3

        run = live_step3.Run(live_step3.ARMS[0], after={"map": [1, 0], "pos": [8, 3]},
                             answer={"inconclusive": True, "loaded_header_is_claimed_map": True, "plans": {}})
        live_step3.check_game_answer(run)
        self.assertFalse(run.passed, run.checks)


class CropTests(unittest.TestCase):
    #: A town with a wall across it (gaps at the left and right ends) and its road out at the top LEFT; the player starts
    #: at the bottom right. The shortest way is through the RIGHT gap; a person who has seen nothing yet cannot know it.
    TOWN = (["##..##################"] + ["#" + "." * 20 + "#" for _ in range(8)] + ["#.##################.#"]
            + ["#" + "." * 20 + "#" for _ in range(8)] + ["#" * 22])

    def shortest(self, column: int | None = None) -> int:
        """The true shortest walk from the start onto the road (a tile past the top edge: one step beyond row 0), on the
        model's own map (breadth first); `column`: onto the road tile of that column."""
        rows, start, frontier, seen = self.TOWN, (18, 16), [((18, 16), 0)], {(18, 16)}
        while frontier:
            (x, y), d = frontier.pop(0)
            if y == 0 and rows[y][x] == "." and column in (None, x):
                return d + 1
            for dx, dy in DIRS.values():
                nxt = (x + dx, y + dy)
                if 0 <= nxt[1] < len(rows) and 0 <= nxt[0] < len(rows[0]) and rows[nxt[1]][nxt[0]] == "." and nxt not in seen:
                    seen.add(nxt)
                    frontier.append((nxt, d + 1))
        raise AssertionError("no way")

    def run_town(self, crop: bool, seed: int = 3):
        maps = {"TOWN": self.TOWN, "ROUTE": ["#..#"] * 3}
        links = {("TOWN", "up"): ("ROUTE", (-1, 3)), ("ROUTE", "down"): ("TOWN", (1, -3))}
        game = GridGame(maps, ("TOWN", (18, 16)), links=links, crop=crop)
        hands, nav, world, notes, lines = rig(game, seed=seed)
        outcome = drive(nav.run(explore_intent("ROUTE", "Story", 12000), "leave town"))
        decisions = [r["extra"] for r in notes.records if r["decision"] == "decide"]
        return outcome, decisions, game

    def test_every_target_was_seen(self) -> None:
        for seed in (1, 2, 3):
            outcome, decisions, game = self.run_town(crop=True, seed=seed)
            self.assertTrue(outcome.startswith("done"), outcome)
            self.assertTrue(decisions)
            for extra in decisions:
                self.assertTrue(extra["known"] and in_window(tuple(extra["seen_from"]), tuple(extra["target"])), extra)
            self.assertTrue(decisions[0]["in_window"], "the first target is on screen")

    def test_fault_the_crop_off_beelines_to_a_road_it_could_not_see(self) -> None:
        for seed in (1, 2, 3):
            real, real_decisions, real_game = self.run_town(crop=True, seed=seed)
            outcome, decisions, game = self.run_town(crop=False, seed=seed)
            self.assertTrue(outcome.startswith("done"), outcome)
            first = decisions[0]
            self.assertEqual(first["kind"], "road")
            self.assertFalse(first["in_window"], f"the first target {first['target']} is off the screen")
            # the road has two tiles, within the whim's margin of each other (`explore.pick`): the beeline is the true
            # shortest walk onto the road tile it CHOSE (the step count alone does not tell a beeline: see live_step3 CROP)
            self.assertEqual(game.steps, self.shortest(first["target"][0]), "a beeline: the true shortest walk to its road")
            self.assertGreater(real_game.steps, game.steps, f"seed {seed}: exploring takes longer than the beeline")


class ExploreTests(unittest.TestCase):
    def setup(self, personality: str, seed: int = 3):
        rows = ["####..####", "#........#", '#..""""..#', '#..""""..#', "#........#", "#....D...#", "#........#", "##########"]
        maps = {"FIELD": rows, "NORTH": ["#..#", "#..#"]}
        links = {("FIELD", "up"): ("NORTH", (-3, 2)), ("NORTH", "down"): ("FIELD", (3, -2))}
        game = GridGame(maps, ("FIELD", (5, 6)), links=links, crop=False)
        hands, nav, world, notes, lines = rig(game, seed=seed, personality=personality)
        world.observe(game.look())
        return nav, game.look()

    def test_personalities(self) -> None:
        for seed in (1, 2, 3, 4, 5):
            picks = {}
            for personality in ("Story", "Catcher", "Trainer"):
                nav, look = self.setup(personality, seed)
                picks[personality] = choose_target(nav, look, WEIGHTS[personality]).kind
            self.assertEqual(picks, {"Story": "road", "Catcher": "grass", "Trainer": "grass"}, f"seed {seed}")

    def test_trainer_goes_toward_people(self) -> None:
        corridor = ["#" * 31] + ["#" + "." * 29 + "#" for _ in range(3)] + ["#" * 31]
        for seed in (1, 2, 3, 4, 5):
            sides = {}
            for personality in ("Trainer", "Story"):
                game = GridGame({"HALL": corridor}, ("HALL", (15, 2)), people={"HALL": {(21, 2)}})
                hands, nav, world, notes, lines = rig(game, seed=seed, personality=personality)
                world.observe(game.look())
                target = choose_target(nav, game.look(), WEIGHTS[personality])
                sides[personality] = "people" if target.tile[0] > 15 else "empty"
            self.assertEqual(sides["Trainer"], "people", f"seed {seed}: {sides}")

    def test_not_straight_back_where_it_came_from(self) -> None:
        """Out of a building whose last unseen corner it cannot reach, into a town with plenty unseen: the door back is
        worth only `Weights.back` (no 'something left there' bonus) while the town has something to see. The rule was
        added after the seed sweep's Catcher seed 1 went lab -> town -> lab -> town (2026-10-08)."""
        building = ["##############", "#.......#....#", "#.......#....#", "#.......#....#", "#..M#####....#", "##############"]
        town = ["#######################", "#.....................#", "##########D############"] + \
               ["#.....................#" for _ in range(10)] + ["#######################"]
        warps = {("B", (3, 4)): ("TOWN", (10, 3)), ("TOWN", (10, 2)): ("B", (3, 3))}
        game = GridGame({"B": building, "TOWN": town}, ("B", (3, 2)), warps=warps)
        hands, nav, world, notes, lines = rig(game, personality="Catcher")
        outcome = drive(nav.run(explore_intent("TOWN", "Catcher", 3000), "out of the building"))
        self.assertTrue(outcome.startswith("done"), outcome)
        keys = {name: key for key, name in world.names().items()}
        self.assertGreater(world.promise(keys["B"]), 0, "the building keeps an unseen corner it cannot reach")
        self.assertGreater(world.promise(keys["TOWN"]), 0)
        back = [c for c in candidates(nav, game.look(), WEIGHTS["Catcher"]) if c.kind == "back"]
        self.assertTrue(back, "the door back is a candidate")
        self.assertIn("just come from", back[0].reason)
        self.assertLessEqual(back[0].score, VALUE_TILES * WEIGHTS["Catcher"].back + 1.5)

    def test_an_exclusion_belongs_to_one_map(self) -> None:
        world = WorldMemory()
        nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world, random.Random(1))
        target = Target("frontier", (3, 4), "x")
        world._last.key = "0:1"
        nav.exclude(target)
        self.assertTrue(nav.is_excluded(target))
        world._last.key = "0:2"
        self.assertFalse(nav.is_excluded(target), "the tile (3, 4) of another map is another tile")

    def test_never_idle_it_wanders(self) -> None:
        room = ["#######", "#.....#", "#.....#", "#######"]
        game = GridGame({"CELL": room}, ("CELL", (2, 1)))
        hands, nav, world, notes, lines = rig(game)
        world.observe(game.look())
        target = choose_target(nav, game.look(), WEIGHTS["Story"])
        self.assertEqual(target.kind, "wander", target)

    #: Three frontier places within the margin of each other, a door 10 points behind.
    WHIM = [Target("frontier", (1, 1), "a", 20.0), Target("frontier", (9, 1), "b", 18.0),
            Target("frontier", (5, 9), "c", 17.0), Target("door", (3, 3), "d", 10.0)]

    def test_a_whim_among_equals(self) -> None:
        """Places about as good (within `CHOICE_MARGIN`) are picked on a seeded whim, the better more often; a place
        far behind never; a clear winner (a route to the goal) always."""
        picks = [pick(self.WHIM, random.Random(seed)).tile for seed in range(40)]
        self.assertEqual(set(picks), {(1, 1), (9, 1), (5, 9)}, picks)
        self.assertGreater(picks.count((1, 1)), picks.count((5, 9)), "the best is picked more often than the worst near one")
        route = self.WHIM + [Target("route", (0, 5), "r", 95.0)]
        self.assertEqual({pick(route, random.Random(seed)).kind for seed in range(40)}, {"route"})
        self.assertEqual(pick(self.WHIM, random.Random(5)), pick(list(reversed(self.WHIM)), random.Random(5)),
                         "the draw does not depend on the candidates' order: a seed replays")

    def test_fault_no_whim_every_seed_picks_the_same(self) -> None:
        with mock.patch.object(explore_module, "CHOICE_MARGIN", 0.0):
            picks = {pick(self.WHIM, random.Random(seed)).tile for seed in range(40)}
        self.assertEqual(picks, {(1, 1)})

    @staticmethod
    def headings(margin: float | None = None) -> tuple[set[str], list]:
        """Eight seeds on CropTests' town (start (18, 16)): the HEADING of each seed's first target (its larger axis
        from the start), and the first targets."""
        headings, firsts = set(), []
        for seed in range(1, 9):
            if margin is None:
                outcome, decisions, game = CropTests().run_town(crop=True, seed=seed)
            else:
                with mock.patch.object(explore_module, "CHOICE_MARGIN", margin):
                    outcome, decisions, game = CropTests().run_town(crop=True, seed=seed)
            assert outcome.startswith("done"), outcome
            dx, dy = decisions[0]["target"][0] - 18, decisions[0]["target"][1] - 16
            headings.add(("left" if dx < 0 else "right") if abs(dx) > abs(dy) else ("up" if dy < 0 else "down"))
            firsts.append(tuple(decisions[0]["target"]))
        return headings, firsts

    def test_seeds_choose_different_ways_on_the_same_town(self) -> None:
        """The verifier's observation (TOWN seeds 3 and 7 chose the same targets), on the model: the same start, eight
        seeds. With the whim, seeds head off in different DIRECTIONS (a CHOICE, not path noise: measured 2026-10-08,
        first targets west (11, 16), (11, 17), (11, 11) and north (17, 11), (20, 11))."""
        headings, firsts = self.headings()
        self.assertGreaterEqual(len(headings), 2, f"first targets {firsts}")

    def test_fault_no_whim_every_seed_heads_the_same_way(self) -> None:
        """FAULT (CHOICE_MARGIN 0: only the score's jitter): every seed's first target is north, (17..19, 11), the
        verifier's 'same targets' in the model."""
        headings, firsts = self.headings(margin=0.0)
        self.assertEqual(headings, {"up"}, f"first targets {firsts}")


class RoamTests(unittest.TestCase):
    def test_roaming_covers_and_never_spins(self) -> None:
        """An open meadow (every tile has two ways on or more): the walk must NEVER step straight back (a reversal there
        is never forced), and covers it. Three seeds, 200 steps each."""
        rows = ["##############"] + ['#' + '"' * 12 + '#' for _ in range(6)] + ["##############"]
        for seed in (1, 2, 3):
            game = GridGame({"MEADOW": rows}, ("MEADOW", (1, 1)))
            hands, nav, world, notes, lines = rig(game, seed=seed, personality="Catcher")
            outcome = drive(roam_train(hands, nav, 200), budget=200_000)
            self.assertTrue(outcome.startswith("roamed"), outcome)
            metrics = next(r["extra"] for r in notes.records if r["decision"] == "roam")
            path = [tuple(xy) for xy in metrics["path"]]
            self.assertEqual(metrics["steps"], 200)
            self.assertEqual(spin_count(path), 0, f"seed {seed}: a step straight back in an open meadow")
            self.assertLess(metrics["spins"] / metrics["attempts"], 0.02, metrics)
            self.assertGreaterEqual(metrics["distinct"], 65)

    RING = ["#######", '#"""""#', '#"###"#', '#"""""#', "#######"]  # a ring of grass one tile wide

    def ring(self, wait: bool):
        """A person stands in the ring until frame 120, then steps out (the walk reaches them at about frame 50): with the
        wait the walk lets them pass; with no wait (the FAULT: PERSON_WAIT 0) it turns straight back."""
        game = GridGame({"RING": self.RING}, ("RING", (1, 1)), leaving={("RING", (3, 3)): 120})
        hands, nav, world, notes, lines = rig(game, personality="Catcher")
        if wait:
            outcome = drive(roam_train(hands, nav, 40))
        else:
            with mock.patch.object(roam_module, "PERSON_WAIT", 0):
                outcome = drive(roam_train(hands, nav, 40))
        metrics = next(r["extra"] for r in notes.records if r["decision"] == "roam")
        waits = [r for r in notes.records if str(r["reason"]).startswith("someone stands in the way")]
        return outcome, [tuple(xy) for xy in metrics["path"]], waits

    def test_a_person_in_the_way_is_waited_for(self) -> None:
        outcome, path, waits = self.ring(wait=True)
        self.assertTrue(outcome.startswith("roamed"), outcome)
        self.assertTrue(waits, "it waited for the person")
        self.assertEqual(spin_count(path), 0, f"no step straight back: {path}")

    def test_fault_without_the_wait_it_turns_back(self) -> None:
        outcome, path, waits = self.ring(wait=False)
        self.assertFalse(waits)
        self.assertGreater(spin_count(path), 0, "turned straight back at the person")

    def test_fault_a_two_tile_spin_is_measured(self) -> None:
        spin = [(1, 1), (2, 1)] * 60
        self.assertGreater(spin_count(spin) / len(spin), 0.95)
        self.assertEqual(spin_count([(1, 1), (2, 1), (3, 1), (3, 2)]), 0)
        self.assertEqual(spin_count([(1, 1), (1, 1)], not_moved=3), 3)

    def test_steps_that_ran_into_a_battle_are_counted(self) -> None:
        """The step-3 verifier: `attempts` left out the training steps a wild battle began on (150 'tried', 163 roam
        presses). On `EncounterGame` (an encounter every 5th step onto grass, as Emerald rolls it: at the step's end,
        before a next step held on into it), the report must agree with the model's OWN counts and the action log:
        ATTEMPTS == every `roam ...` press; TRAINING STEPS == the model's steps; INTERRUPTED == the presses a battle
        pre-empted (or, `at_once`, that moved the player into a battle: then also counted as TRAINING STEPS); every
        encounter fled; the path continuous (one tile a step); the spin ratio over training steps."""
        rows = ["##############"] + ['#' + '"' * 12 + '#' for _ in range(6)] + ["##############"]
        for at_once in (False, True):
            with self.subTest(at_once=at_once):
                game = EncounterGame({"MEADOW": rows}, ("MEADOW", (1, 1)), every=5, at_once=at_once)
                hands, nav, world, notes, lines = rig(game, seed=2, personality="Catcher")
                outcome = drive(roam_train(hands, nav, 60), budget=200_000)
                self.assertTrue(outcome.startswith("roamed"), outcome)
                m = next(r["extra"] for r in notes.records if r["decision"] == "roam")
                presses = [r for r in notes.records if str(r["reason"]).startswith("roam ") and r["action"].startswith("hold ")]
                path = [tuple(xy) for xy in m["path"]]
                self.assertGreaterEqual(game.battles, 5, "encounters happened")
                self.assertEqual((m["encounters"], m["fled"]), (game.battles, game.battles))
                self.assertEqual(m["attempts"], len(presses), "every roam press is an attempt")
                self.assertEqual(m["steps"], game.steps, "the model's own step count")
                self.assertEqual(m["steps"], len(path) - 1)
                moved_in = m["interrupted"] if at_once else 0  # the interrupted presses that moved the player
                self.assertEqual(m["attempts"], m["steps"] + m["interrupted"] - moved_in + m["not_moved"], m)
                self.assertTrue(1 <= m["interrupted"] <= game.battles, m)
                self.assertTrue(all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:])), path)
                self.assertEqual(spin_count(path), 0, "no step straight back across a battle (the tile it came from kept)")
                self.assertEqual(m["spin_ratio"], round(m["spins"] / m["steps"], 6))


class BattleModel:
    """`src/battle_controller_player.c` HandleInputChooseAction on a 2 x 2 cursor; RUN ends the battle after a text."""

    def __init__(self, kind: str) -> None:
        self.kind, self.cursor, self.frame, self.done, self.after = kind, 0, 0, False, 0
        self.pressed: list[tuple[str, int]] = []

    def tick(self, button: str | None, new: bool) -> None:
        self.frame += 1
        if self.after:
            self.after -= 1
            if not self.after:
                self.done = True
            return
        if not new or button is None:
            return
        self.pressed.append((button, self.cursor))
        if button == "Right" and not self.cursor & 1:
            self.cursor ^= 1
        elif button == "Left" and self.cursor & 1:
            self.cursor ^= 1
        elif button == "Down" and not self.cursor & 2:
            self.cursor ^= 2
        elif button == "Up" and self.cursor & 2:
            self.cursor ^= 2
        elif button == "A" and self.cursor == RUN:
            self.after = 40

    def look(self) -> Observation:
        mon = BattleMon("Wurmple", 265, 2, None, None, 48, "ok", ("Bug",), ())
        if self.done:
            screen = ScreenState(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False,
                                 waits_for_button=False, in_battle=False)
            player = PlayerState(0, 0, "R", "R", 1, 1, "down", "walking", 3, 0, 1)
            return Observation(self.frame, screen, player, View(0, 0, 0, 0, ((Tile(1, 1, 0, 0, 0, 0, "NORMAL", 0, 3, False, False, None, False, None, False, False, False),),), (), True),
                               (), None, None, None, 4, (), 0.0)
        ui = None if self.after else MenuView(kind="battle_action", options=BATTLE_ACTIONS, cursor=self.cursor)
        screen = ScreenState(game_state="BATTLE", screen="battle", menu=None, text_box_open=False, waits_for_button=False,
                             in_battle=True, ui=ui, scene="a battle")
        battle = BattleView(self.kind, False, 8 if self.kind == "trainer" else 4, 322 if self.kind == "trainer" else None, (), (mon,))
        return Observation(self.frame, screen, None, None, (), None, None, battle, 0, (), 0.0)


class EncounterGame(GridGame):
    """`GridGame` plus WILD ENCOUNTERS as Emerald rolls them: at the END of every `every`-th step onto tall grass a
    wild battle begins (before any next step, so a step held on into it is pre-empted and does not move the player),
    played by `BattleModel` (its 2 x 2 action menu, fled with RUN). `at_once`: the battle begins the moment the step
    lands instead, so the navigator's walk sees the battle before it sees the move (the step DID move the player: what
    the roam's `pending` resolution is for)."""

    def __init__(self, *args, every: int = 6, at_once: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.every, self.grass_steps, self.due, self.battle, self.battles = every, 0, False, None, 0
        self.at_once = at_once

    def attempt(self, button: str) -> None:
        before = self.steps
        super().attempt(button)
        if self.steps > before and self.char(self.map, self.pos) == '"':
            self.grass_steps += 1
            self.due = self.grass_steps % self.every == 0
            if self.due and self.at_once:
                self.moving, self.due = 0, False
                self.battle = BattleModel("wild")
                self.battles += 1

    def tick(self, button: str | None, new: bool) -> None:
        if self.battle is not None:
            self.battle.frame = self.frame
            self.battle.tick(button, new)
            self.frame = self.battle.frame
            if self.battle.done:
                self.battle = None
            return
        if self.due and self.moving == 1:
            self.frame += 1
            self.moving, self.due = 0, False
            self.battle = BattleModel("wild")
            self.battles += 1
            return
        super().tick(button, new)

    def look(self) -> Observation:
        if self.battle is None:
            return super().look()
        self.battle.frame = self.frame
        return self.battle.look()


class FleeTests(unittest.TestCase):
    def hands(self, model):
        return Hands(GridEyes(model), GridControls(model), random.Random("1:pacing"), random.Random("1:choices"), Notes(),
                     lambda line: None, Faults())

    def test_run_is_reached_by_reading_the_cursor(self) -> None:
        model = BattleModel("wild")
        outcome = drive(flee(self.hands(model)))
        self.assertEqual(outcome, "fled")
        self.assertEqual([b for b, _ in model.pressed], ["Right", "Down", "A"])
        self.assertEqual(model.pressed[-1], ("A", RUN), "A only on RUN")

    def test_a_trainer_battle_is_out_of_scope_and_nothing_is_pressed(self) -> None:
        model = BattleModel("trainer")
        outcome = drive(flee(self.hands(model)))
        self.assertEqual(outcome, TRAINER_OUT_OF_SCOPE)
        self.assertEqual(model.pressed, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
