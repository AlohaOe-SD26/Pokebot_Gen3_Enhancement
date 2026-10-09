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

BUILD STEP 3.1 (the step-3 adversarial review), each with its fault half and a mutant in `gates/revert_step3.py`:
  ShiftTests          (finding 1) the same memory with every coordinate moved by +50 gives the same choice; a tile past an
                      edge never crossed is no road. MemoryTests: edges learned at a crossing, also from an old memory.
  ReversalTests       (finding 2) on the town model, 12 seeds: reversals near zero and no stale frontier target walked
                      onto; FAULTS: no turn-back cost (>= 15), no stale drop (targets walked onto, >= 8).
  SceneTests          (finding 3) a repeating scene gives its target up after the second; FAULT: until the novelty window.
  WalkTests           (finding 4) a bump belongs to its side: a hidden wall bumped at most once per side, a ONE-WAY tile
                      crossed from its open side, the only way on retried once before it is given up; FAULTS: a bump
                      walls every side, one bump closes the way.
  ExitTests           (finding 5) a door that does not open is remembered CLOSED across intents; an arrow mat is used by
                      its arrow. FrameworkFreeTests: no host file reads a map's warp table; the exit looks.
  WindowTests         (finding 6) the gate's crop check flags a tile seen 8 columns away however wide the eyes' window.
  ApproachTests       (finding 8) every candidate is a SEEN walkable tile, an exit's stand tile included.
  RoamTests           (finding 9) both ratios and the pre-empted presses, against the model's own counts.
  GraderTests         (finding 2's grader) `live_step3.reversals` and `walk_path` on the review's own examples.

THE STEP-3.1 VERIFIER'S ROUND, each with its fault half and a mutant (W44-W51):
  SceneTests          the EXPLORER sent back twice from one tile stops stepping on it (FAULT: the next target behind it meets
                      the scene again); a tile seen in passing is not progress; progress lifts the tile (`StoryGame`).
  ExitTests           a closed door is tried again once the story moves on, or after `CLOSED_RETRY_FRAMES`.
  GraderTests         `live_step3.stale_arrivals` (a stale drop is no arrival), `edge_targets` per EDGE and its non-vacuity,
                      `scenes_by_tile`.

THE STEP-3.1 VERIFIER'S SECOND ROUND, each with its fault half and a mutant (W52-W60):
  FrameworkFreeTests  the warp-table check catches the verifier's own `getattr(location, 'warps')` plant, `hasattr`, a dict
                      key and `MapWarp` (a string constant names it), and does NOT fire on a docstring or a comment that
                      mentions `location.warps`. (A RAW read names nothing: `gates/warp_reads.py`'s scan, arm WARPREAD.)
  SceneTests          a scene known by its WORDS (`GridGame` triggers may say something): the same words on a gap two tiles
                      wide are one scene, met at most 3 times (FAULT: by tile only, 4); different words are two scenes; the
                      rule directly; NEWS (`NewsGame`: new words from a scene that left the player be) lifts the twin and
                      once more gives her up again (FAULTS: news not progress, 2; once not enough, 4); `Novelty.heard`.
  GameAnswerTests     a trial the game did not step at all asks whether the player is LOCKED (`stopped_trials`).
  GraderTests         a locked player answered by THE ARRIVAL across a connection (SCENEX's end on Route 101); a
                      pre-registered number that does not hold FAILS its arm (`check_predictions`); arm CLOCKS registers
                      launcher frames only where every clock agrees (`grade_CLOCKS`: W61).

THE STEP-4 VERIFIER'S ROUND (its FAILURE: step 3.2's finding 4, "the churn is still there"), each with its fault half and a
mutant (W79-W87):
  ChurnTests          a frontier seen past is CARRIED ON by the same decision (`brain/explore.py` carry_on): straight beyond
                      it; a place two tiles aside is another place (W81); something clearly better that comes into view
                      ends the decision (W80: carried on whatever comes); never a place beside or behind the player (W85);
                      on the town model 12 seeds make about a decision per 8 steps where the step-3.2 rule (W79) made one
                      per step, the walks no more than a tenth longer.
  GraderTests         one loop is ONE ring and a LAP ring has a leg walked beyond its shortest way (W82, W83); the churn
                      measure and its bounds (W84); `stale_arrivals` on the place a decision was carried on to (W86); the
                      twin after news at most once on EACH tile (W87).
  ExitTests           a DOORMAT is one way out: its other tile, the same look across its arrow, leads back too (W88).
"""

from __future__ import annotations

import ast
import contextlib
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
from ai_player.world.memory import WorldMemory, read_world  # noqa: E402
from ai_player.gates.window import on_screen_from  # noqa: E402  (the gate's own window: build step 3.1, finding 6)

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
                 scene_on=None, crop: bool = True, leaving=None, stubborn=None, triggers=None) -> None:
        self.maps = maps
        self.map, self.pos = start[0], start[1]
        self.warps = warps or {}
        self.links = links or {}
        self.people = people or {}
        self.leaving = leaving or {}
        self.scene_on = scene_on or {}
        #: (build step 3.1) (map, tile) -> how many ATTEMPTS (one per 8 frames held) a 'T' tile refuses before it opens
        self.stubborn = stubborn or {}
        self.refused: dict = {}
        #: (build step 3.1) (map, tile) -> (frames, (x, y)): stepping onto it starts a scene that ends by putting the
        #: player on (x, y) (Littleroot's twin pushing a player with no Pokemon back from the road)
        self.triggers = triggers or {}
        self.push_to = None
        self.scenes_run = 0
        #: (the step-3.1 verifier's second round) a trigger may say something: (frames, back, WORDS); the scene's page is
        #: then on screen, waiting for a press, while it runs (the twin's "Um, um, um!")
        self.scene_text: str | None = None
        self.scene_log: list[tuple[str, tuple[int, int]]] = []  # (map, the trigger tile) of every scene run
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
        self.trail: list[tuple[str, tuple[int, int]]] = [(self.map, self.pos)]  # (map, tile) after every step taken

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
            if not self.scene and self.push_to is not None:
                self.pos, self.push_to = self.push_to, None
            if not self.scene:
                self.scene_text = None
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
            self.trail.append((self.map, self.pos))
            return
        if c in "#~HDX" or target in self.people_now():
            self.bump()
            return
        # 'N': a ONE-WAY tile (IMPASSABLE_SOUTH_AND_NORTH: `src/event_object_movement.c` IsMetatileDirectionallyImpassable
        # refuses entering it and leaving it going north or south; east and west are open)
        if button in ("Up", "Down") and "N" in (c, here):
            self.bump()
            return
        if c == "T" and self.refused.get((self.map, target), 0) < self.stubborn.get((self.map, target), 0):
            self.refused[(self.map, target)] = self.refused.get((self.map, target), 0) + 1
            self.bump()
            return
        if c in LEDGES:
            if LEDGES[c][1] != (dx, dy):
                self.bump()
                return
            self.pos = (target[0] + dx, target[1] + dy)
            self.moving, self.steps = 32, self.steps + 1
            self.trail.append((self.map, self.pos))
            return
        self.pos = target
        self.moving, self.steps = 16, self.steps + 1
        self.trail.append((self.map, self.pos))
        if c == "S":
            self.start_warp(target)
        if (self.map, target) in self.triggers:
            frames, back, *words = self.triggers[(self.map, target)]
            self.scene, self.push_to, self.moving = frames, back, 0
            self.scene_text = words[0] if words else None
            self.scenes_run += 1
            self.scene_log.append((self.map, target))

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
        words = self.scene_text if self.scene else None
        return ScreenState(game_state="OVERWORLD", screen="text" if words else "overworld", menu=None,
                           text_box_open=bool(words), waits_for_button=bool(words), in_battle=False,
                           wait_reason="text printer 0 WAIT" if words else None, text=words,
                           script_running=bool(self.scene), controls_locked=bool(self.scene),
                           fading=bool(self.warp_out or self.warp_in))

    def player(self) -> PlayerState:
        settling = self.warp_in > 8
        index = sorted(self.maps).index(self.map)
        return PlayerState(map_group=0, map_number=index, map_name=self.map, map_const=self.map,
                           x=None if settling else self.pos[0], y=None if settling else self.pos[1], facing=self.facing,
                           movement="walking", elevation=3, avatar_flags=0, trainer_id=1, settling=settling)

    def tile(self, x: int, y: int, dx: int, dy: int) -> Tile:
        c = self.char(self.map, (x, y))
        names = {".": "NORMAL", "#": "NORMAL", '"': "TALL_GRASS", "~": "POND_WATER", "D": "ANIMATED_DOOR",
                 "S": "NON_ANIMATED_DOOR", "M": "SOUTH_ARROW_WARP", "H": "NORMAL", "N": "IMPASSABLE_SOUTH_AND_NORTH",
                 "T": "NORMAL", "X": "ANIMATED_DOOR"}
        ledge = LEDGES[c][0] if c in LEDGES else None
        # the eyes' `warp` is the LOOK (build step 3.1): 'X' looks like a door and is one with no warp (a closed door)
        return Tile(x=x, y=y, dx=dx, dy=dy, metatile=0, behavior=0, behavior_name=names.get(c, "JUMP"),
                    collision=1 if c in "#DX" else 0, elevation=3, blocked=c in "#DX", water=c == "~",
                    encounter="land" if c == '"' else None, tall_grass=c == '"', ledge=ledge, door=c in "DSX",
                    warp=c in "DSMX", half_visible=abs(dy) == 5)

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

    # ---- build step 3.1, the step-3 review's finding 5: no warp TABLE on the AI's side
    @staticmethod
    def warp_table_reads(source: str) -> list[str]:
        """Every place a source NAMES a map's warp events (`gates/warp_reads.py` warp_table_reads: an attribute, a string
        constant such as `getattr(location, 'warps')`'s, the framework's `MapWarp`). (The step-3.1 verifier's second
        round: the attribute alone let a `getattr` read through.) A RAW read names nothing: `gates/warp_reads.py`'s scan,
        live arm WARPREAD, records every read the real eyes make and is the guard for that."""
        from ai_player.gates.warp_reads import warp_table_reads

        return warp_table_reads(source)

    def test_the_ai_never_reads_the_warp_table(self) -> None:
        """A tile is an exit by how it LOOKS (`eyes/view.py` EXIT_BEHAVIORS); the ROM's warp table is test side only.
        `host/` holds the only files that read the game (every other AI file is framework-free: the test above), so
        none of them may read a map's warps (`world/memory.py`'s own `WorldMemory.warps` is the AI's learned warp
        GRAPH, built from map changes it saw: not a read)."""
        files = sorted((PACKAGE / "host").glob("*.py"))
        self.assertTrue(files)
        for path in files:
            with self.subTest(file=path.name):
                self.assertEqual(self.warp_table_reads(path.read_text(encoding="utf-8")), [])

    def test_fault_a_planted_warp_table_read_is_caught(self) -> None:
        source = (PACKAGE / "host/eyes.py").read_text(encoding="utf-8") + "\nwarps = frozenset(w.local_coordinates for w in location.warps)\n"
        self.assertEqual(len(self.warp_table_reads(source)), 1)

    def test_fault_the_verifiers_getattr_plant_is_caught(self) -> None:
        """The step-3.1 verifier planted exactly this in `_map_facts` and the attribute-only check passed it."""
        eyes = (PACKAGE / "host/eyes.py").read_text(encoding="utf-8")
        planted = eyes.replace("            signs = tuple(\n",
                               "            _w = frozenset(w.local_coordinates for w in getattr(location, 'warps'))\n"
                               "            signs = tuple(\n", 1)
        self.assertNotEqual(planted, eyes, "the plant's anchor is in host/eyes.py")
        self.assertEqual(self.warp_table_reads(planted), ["line %d: the string 'warps'" % (
            planted.splitlines().index("            _w = frozenset(w.local_coordinates for w in getattr(location, 'warps'))") + 1)])
        for spelled in ("hasattr(location, 'warp_events')", "data['warpCount']", "from modules.map import MapWarp"):
            with self.subTest(spelled=spelled):
                self.assertTrue(self.warp_table_reads(f"x = {spelled}\n" if "import" not in spelled else spelled + "\n"))

    def test_a_mention_in_a_docstring_or_a_comment_is_not_a_read(self) -> None:
        """(CLAUDE.md rule 6: a gate must not fire on mere mentions) the host's own docstring says the warp table is no
        longer read, and names `location.warps`; a comment may too."""
        source = ('"""The eyes no longer read `location.warps` (the warps of the map)."""\n'
                  "# location.warps used to be read here; getattr(location, 'warps') neither\n"
                  "x = 'the map has warps'\n")
        self.assertEqual(self.warp_table_reads(source), [])

    def test_an_exit_is_known_by_its_look(self) -> None:
        from ai_player.eyes.view import BEHAVIOR, DOOR_BEHAVIORS, EXIT_BEHAVIORS

        looks = {name for name, value in BEHAVIOR.items() if value in EXIT_BEHAVIORS}
        for name in ("ANIMATED_DOOR", "NON_ANIMATED_DOOR", "LADDER", "UP_ESCALATOR", "DOWN_ESCALATOR", "SOUTH_ARROW_WARP",
                     "NORTH_ARROW_WARP", "EAST_ARROW_WARP", "WEST_ARROW_WARP", "MT_PYRE_HOLE", "AQUA_HIDEOUT_WARP"):
            self.assertIn(name, looks)
        self.assertTrue(DOOR_BEHAVIORS <= EXIT_BEHAVIORS)
        for name in ("NORMAL", "TALL_GRASS", "CAVE", "BRIDGE_OVER_OCEAN", "COUNTER"):
            self.assertNotIn(name, looks, "plain ground (and the bridges that share the Union Room exit's behaviour)")


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
        outside = [xy for xy, fact in memory.tiles.items() if not on_screen_from(fact.seen_from, xy)]
        self.assertGreater(len(memory.tiles), 165)
        self.assertEqual(outside, [], "every known tile lies inside the window of the tile it was seen from")
        self.assertNotIn((39, 10), memory.tiles, "the far wall was never on screen")

    def test_fault_the_crop_off_learns_what_no_window_showed(self) -> None:
        world = self.walk(crop=False)
        memory = world.here()
        outside = [xy for xy, fact in memory.tiles.items() if not on_screen_from(fact.seen_from, xy)]
        self.assertGreater(len(outside), 100)
        self.assertIn((39, 10), memory.tiles)

    MAPS = {"A": ["##.##", "#...#", "#...#", "#...#", "#####"], "B": ["#...#", "#...#"]}
    LINKS = {("A", "up"): ("B", (0, 2)), ("B", "down"): ("A", (0, -2))}

    def test_visits_frontier_roads_and_persistence(self) -> None:
        """(build step 3.1, the step-3 review's finding 1) a tile past an edge is a ROAD only once a crossing of that
        edge has been SEEN: before it, (2, -1) is a tile like any other (the coordinates say nothing a person sees)."""
        game = GridGame(self.MAPS, ("A", (2, 3)), links=self.LINKS)
        hands, nav, world, _, _ = rig(game)
        drive(nav.go_to((2, 1), "to the gap", 600))
        memory = world.here()
        self.assertEqual(memory.visits[(2, 1)], 1)
        self.assertIn((2, -1), memory.tiles, "seen: the screen shows the next map past the top edge")
        self.assertEqual((memory.roads(), memory.outside((2, -1)), memory.edges), ([], False, {}),
                         "no crossing seen yet: no edge known, so nothing is 'past' it")
        drive(nav.run(explore_intent("B", "Story", 2000), "cross"))
        keys = {name: key for key, name in world.names().items()}
        a, b = world.maps[keys["A"]], world.maps[keys["B"]]
        self.assertEqual((a.edges, b.edges), ({"up": -1}, {"down": 2}), "both maps' edges, learned at the crossing")
        self.assertIn((2, -1), a.roads(), "now a walkable tile past A's known top edge is a road")
        self.assertNotIn((2, 5), a.roads(), "past an edge the AI has not crossed, a tile is not known to be another map's")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "world.jsonl"
            path.write_text(world.snapshot() + "\n", encoding="utf-8")
            again = read_world(path)
        self.assertEqual(again.to_dict(), world.to_dict())

    def test_an_old_memory_learns_its_edges_from_its_crossings(self) -> None:
        """A memory written before build step 3.1 kept only the right and bottom edges: read back, every crossing it
        recorded teaches both maps' edges again (the fixtures' `route101_south.world.jsonl` is such a file)."""
        game = GridGame(self.MAPS, ("A", (2, 3)), links=self.LINKS)
        hands, nav, world, _, _ = rig(game)
        drive(nav.run(explore_intent("B", "Story", 2000), "cross"))
        data = world.to_dict()
        for value in data["maps"].values():
            value["edges"] = {side: edge for side, edge in value["edges"].items() if side in ("right", "down")}
        again = WorldMemory.from_dict(data)
        self.assertEqual({key: m.edges for key, m in again.maps.items()}, {key: m.edges for key, m in world.maps.items()})


def shifted_world(world: WorldMemory, d: int) -> WorldMemory:
    """The same memory with EVERY coordinate of every map moved by (+d, +d): tiles, where they were seen from, visits,
    bumps, closed exits, people, items, edges, arrivals, warp links, connections, map changes, the player's tile. Every
    map moves by the same amount, so a connection's offset is unchanged. A person's knowledge is the same: only the
    numbering moved."""
    def s(text: str) -> str:
        x, y = text.split(",")
        return f"{int(x) + d},{int(y) + d}"

    def p(xy):
        return None if xy is None else [xy[0] + d, xy[1] + d]

    data = json.loads(world.snapshot())
    for m in data["maps"].values():
        m["tiles"] = {s(k): v[:5] + [v[5] + d, v[6] + d] for k, v in m["tiles"].items()}
        for field_name in ("visits", "people", "items", "closed"):
            m[field_name] = {s(k): v for k, v in m.get(field_name, {}).items()}
        m["bumped"] = {f"{s(k.split('|')[0])}|{k.split('|')[1]}": {**v, "from": p(v.get("from"))} for k, v in m["bumped"].items()}
        m["edges"] = {side: edge + d for side, edge in m["edges"].items()}
        m["arrivals"] = [[a[0], a[1] + d, a[2] + d, a[3]] for a in m["arrivals"]]
    data["warps"] = {f"{k.split('|')[0]}|{s(k.split('|')[1])}": {**v, "arrival": p(v.get("arrival"))} for k, v in data["warps"].items()}
    data["connections"] = [{**c, "from": p(c.get("from")), "arrival": p(c.get("arrival"))} for c in data["connections"]]
    data["transitions"] = [t[:5] + [p(t[5]), p(t[6]), t[7]] for t in data["transitions"]]
    out = WorldMemory.from_dict(data)
    out._last.key, out._last.xy = world._last.key, tuple(p(world._last.xy)) if world._last.xy else None
    for key, memory in out.maps.items():
        memory.objects_now = frozenset((x + d, y + d) for x, y in world.maps[key].objects_now)
    return out


class ShiftTests(unittest.TestCase):
    """(build step 3.1, the step-3 review's finding 1, HIGH) The explorer knew where a map ENDS from NEGATIVE
    coordinates (`MapMemory.outside`: x < 0 or y < 0) and valued those tiles as ROADS: knowledge no screen shows, and
    only on the top and left edges. A person's choices cannot depend on how the tiles are NUMBERED: the same memory
    with every coordinate moved by +50 must give the same choice. FAULT (the old rule: `memory.outside` from the
    coordinates): Story goes for a 'road' at y < 0 in one and a frontier in the other."""

    TOWN = ["##..##########", "#............#", "#............#", "#............#", "#............#", "##############"]

    def choices(self, crossed: bool, seeds=range(1, 7)) -> list[tuple]:
        maps = {"TOWN": self.TOWN, "ROUTE": ["#..#"] * 12}
        links = {("TOWN", "up"): ("ROUTE", (-1, 12)), ("ROUTE", "down"): ("TOWN", (1, -12))}
        out = []
        for seed in seeds:
            game = GridGame(maps, ("TOWN", (6, 2)), links=links)
            hands, nav, world, notes, lines = rig(game, seed=seed)
            world.observe(game.look())
            if crossed:  # a crossing of the top edge SEEN before (the edge is then known, and shifts with the rest)
                world.here().edges["up"] = -1
            look = game.look()
            moved_world = shifted_world(world, 50)
            nav2 = Navigator(Hands(None, None, random.Random(1), random.Random(f"{seed}:choices"), None, lambda line: None),
                             moved_world, random.Random(f"{seed}:choices"), WEIGHTS["Story"].grass_cost, "Story")
            look2 = replace(look, player=replace(look.player, x=look.player.x + 50, y=look.player.y + 50))
            nav.rng = random.Random(f"{seed}:choices")
            first = choose_target(nav, look, WEIGHTS["Story"])
            second = choose_target(nav2, look2, WEIGHTS["Story"])
            out.append((seed, (first.kind, first.tile, round(first.score, 6)),
                        (second.kind, (second.tile[0] - 50, second.tile[1] - 50), round(second.score, 6))))
        return out

    def test_the_same_choice_with_every_coordinate_moved_by_50(self) -> None:
        for crossed in (False, True):
            for seed, first, second in self.choices(crossed):
                with self.subTest(crossed=crossed, seed=seed):
                    self.assertEqual(first, second, "the choice depends on how the tiles are numbered")

    def test_a_tile_past_an_edge_never_crossed_is_not_a_road(self) -> None:
        kinds = {first[0] for _, first, _ in self.choices(False)}
        self.assertNotIn("road", kinds, "no crossing seen: nothing on screen says the map ends there")
        self.assertEqual({first[0] for _, first, _ in self.choices(True)}, {"road"}, "a crossing seen: Story goes for the road")


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

    def test_a_hidden_wall_is_bumped_once_from_a_side_and_avoided(self) -> None:
        """(build step 3.1, finding 4: a bump belongs to the SIDE it came from) A wall the eyes call floor, met on three
        errands: from each side at most ONCE (a person does not know an unseen obstacle is closed from every side), and
        never pressed into again from a side that refused the player."""
        game, world, outcome, notes, nav = self.errands()
        self.assertTrue(outcome.startswith("done"), outcome)
        bumped = world.here().bumped
        self.assertTrue(bumped and {xy for xy, _ in bumped} == {(4, 3)}, bumped)
        self.assertEqual({key: info["bumps"] for key, info in bumped.items()}, {key: 1 for key in bumped}, "once per side")
        self.assertEqual(game.bumps, nav.stats.bumps)
        self.assertEqual(nav.stats.bumps, len(bumped), "one bump per side tried")
        self.assertLessEqual(game.bump_frames, 40 * len(bumped), "about one bump's worth of walking in place per side")
        for (tile, direction), info in bumped.items():
            later = [r for r in notes.records if str(r["reason"]).startswith(f"walk {direction}:") and "-> (4, 3)" in r["reason"]
                     and r["frame"] > info["last"]]
            self.assertEqual(later, [], f"pressed into (4, 3) going {direction} after that side refused the player")
        self.assertEqual(game.pos, (5, 3))

    def test_fault_without_learning_it_bumps_again_and_again(self) -> None:
        game, world, outcome, notes, nav = self.errands(learn=False)
        self.assertTrue(outcome.startswith("stuck"), outcome)
        self.assertGreater(nav.stats.bumps, 10)
        self.assertGreater(game.bump_frames, 1000, "it walked in place against the same tile for most of a minute")

    #: A ONE-WAY tile 'N' (IMPASSABLE_SOUTH_AND_NORTH, as the player's room has at (1, 4)): closed going north or south,
    #: open going east or west; the eyes call it floor.
    ONE_WAY = ["#######", "#.....#", "#.....#", "#..N..#", "#######"]

    def one_way(self):
        game = GridGame({"ROOM": self.ONE_WAY}, ("ROOM", (3, 1)))
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(goto_intent([(3, 3), (5, 3), (1, 3)], 6000), "errands"), budget=40_000)
        return game, world, outcome, notes, nav

    def test_a_one_way_tile_is_crossed_from_its_open_side(self) -> None:
        """Errand 1 is the one-way tile ITSELF, straight below the start: walked into going down, it refuses (one bump,
        that side only), and it is reached from the side. Errands 2 and 3 cross it east and west: 2 steps each, not 4
        round it. FAULT (the old rule: one bump = a wall from every side): the tile is unreachable, the intent stuck."""
        game, world, outcome, notes, nav = self.one_way()
        self.assertTrue(outcome.startswith("done"), outcome)
        self.assertEqual(sorted(world.here().bumped), [((3, 3), "down")], "one bump, from the north")
        across = [r for r in notes.records if str(r["reason"]).startswith("walk ") and "toward the goto at (1, 3)" in r["reason"]]
        self.assertEqual(len(across), 4, f"errand 3, (5, 3) -> (1, 3): 4 steps straight through the one-way tile: "
                                         f"{[r['reason'][:40] for r in across]}")
        self.assertEqual(game.pos, (1, 3))

    def test_fault_a_bump_from_one_side_walls_every_side(self) -> None:
        with mock.patch.object(memory_module.MapMemory, "bumps",
                               lambda self, xy, direction: max([i["bumps"] for (t, _), i in self.bumped.items() if t == xy] or [0]) * 2):
            game, world, outcome, notes, nav = self.one_way()
        self.assertTrue(outcome.startswith("stuck"), outcome)
        self.assertNotEqual(game.pos, (3, 3), "never got onto the one-way tile")

    #: A corridor whose only way on is a tile 'T' that refuses the first attempts (a hidden thing that moves away):
    #: 4 attempts are the navigator's whole first hold (STEP_HOLD_MAX 32 frames, an attempt every 8), so it learns a bump.
    CORRIDOR = ["#######", "#..T..#", "#######"]

    def corridor(self, refusals: int):
        game = GridGame({"HALL": self.CORRIDOR}, ("HALL", (1, 1)), stubborn={("HALL", (3, 1)): refusals})
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(goto_intent([(5, 1)], 4000), "along the hall"), budget=20_000)
        return game, world, outcome, nav

    def test_the_only_way_on_is_retried_before_it_is_given_up(self) -> None:
        """'Retry at high cost before giving up': after ONE bump the way in is dear, not closed, so when it is the only
        way the navigator presses again; the second refusal from that side closes it (`BUMP_GIVE_UP`), and an errand
        with no other way is stuck, not a loop. FAULT (one bump = closed): a way that opened is never tried again.
        (Build step 3.2: the bump is FORGOTTEN once the way let the player through: 0 left, where step 3.1 kept 1.)"""
        game, world, outcome, nav = self.corridor(refusals=4)
        self.assertTrue(outcome.startswith("done"), outcome)
        self.assertEqual((nav.stats.bumps, world.here().bumps((3, 1), "right"), game.pos), (1, 0, (5, 1)),
                         "refused once (a bump learned), retried as the only way, through, and the bump forgotten")
        game, world, outcome, nav = self.corridor(refusals=99)
        self.assertTrue(outcome.startswith("stuck"), outcome)
        self.assertEqual((nav.stats.bumps, world.here().bumps((3, 1), "right")), (memory_module.BUMP_GIVE_UP,) * 2,
                         f"given up after {memory_module.BUMP_GIVE_UP} refusals from that side, no loop")

    def test_fault_one_bump_closes_the_way(self) -> None:
        with mock.patch.object(navigator_module, "BUMP_GIVE_UP", 1):
            game, world, outcome, nav = self.corridor(refusals=4)
        self.assertTrue(outcome.startswith("stuck"), outcome)
        self.assertEqual(game.pos, (2, 1))

    # ---- build step 3.2, the step-3.1 review's MEDIUM finding 3: "a bump is never forgotten after walking through that way"
    #: The short way east is through 'T' (3, 1), a tile that refuses its first attempts (something in the way that moved
    #: on); the way round below is 8 steps. A person stands in the way round at first (`leaving`), so the first errand
    #: has to try the short way again after its bump.
    LOOP = ["#######", "#..T..#", "#.###.#", "#.....#", "#######"]

    def loop(self, forget: bool = True):
        game = GridGame({"HALL": self.LOOP}, ("HALL", (1, 1)), stubborn={("HALL", (3, 1)): 4},
                        leaving={("HALL", (3, 3)): 10**9})
        hands, nav, world, notes, lines = rig(game)
        with (contextlib.nullcontext() if forget else mock.patch.object(WorldMemory, "forget_bump", lambda self, key, xy, d: None)):
            first = drive(nav.run(goto_intent([(5, 1), (1, 1)], 6000), "east and back"), budget=40_000)
            bumps = (nav.stats.bumps, world.here().bumps((3, 1), "right"))
            game.leaving = {}  # the person in the way round has gone
            steps = game.steps
            second = drive(nav.run(goto_intent([(5, 1)], 3000), "east again"), budget=20_000)
        return first, second, bumps, game.steps - steps, game, lines

    def test_a_bump_is_forgotten_when_the_way_lets_the_player_through(self) -> None:
        """Errand 1 bumps into 'T' going east (one bump, learned), has no other way, tries again and gets through: the
        bump going east is FORGOTTEN, and said. The next errand east takes the short way straight through it: 4 steps.
        FAULT (never forgotten: mutant W64): the tile is still 'bumped once' going east, dearer by `BUMP_RETRY_COST`, so the
        next errand walks the 8 steps round."""
        first, second, bumps, steps, game, lines = self.loop()
        self.assertTrue(first.startswith("done") and second.startswith("done"), (first, second))
        self.assertEqual(bumps, (1, 0), "one bump, and it is forgotten once the way let the player through")
        self.assertTrue(any("let the player through now: forgotten" in line for line in lines), lines[-6:])
        self.assertEqual(steps, 4, f"straight through: {game.trail[-6:]}")

    def test_fault_a_bump_never_forgotten_sends_the_player_round(self) -> None:
        first, second, bumps, steps, game, lines = self.loop(forget=False)
        self.assertEqual(bumps, (1, 1))
        self.assertEqual(steps, 8, f"round below: {game.trail[-9:]}")

    def test_a_tile_that_looks_different_drops_its_bumps(self) -> None:
        """What bumping a tile taught is about THAT tile: when it looks different (a script opened a door, moved a rock),
        its bumps are dropped, and kept for the navigator to tell. The same look again keeps them. FAULT (kept: mutant
        W65)."""
        game = GridGame({"ROOM": ["#######", "#.....#", "#######"]}, ("ROOM", (1, 1)))
        world = WorldMemory()
        world.observe(game.look())
        world.learn_bump((1, 1), "right", 10)
        world.learn_bump((3, 1), "left", 12)
        world.observe(replace(game.look(), frame=100))  # looked at again: nothing changed
        self.assertEqual((world.here().bumps((2, 1), "right"), world.take_dropped_bumps()), (1, []))
        game.maps["ROOM"] = ["#######", '#.".".#', "#######"]  # (2, 1) and (4, 1) now look like tall grass
        world.observe(replace(game.look(), frame=200))
        self.assertEqual(world.here().bumps((2, 1), "right"), 0)
        self.assertEqual(world.here().bumped, {})
        self.assertEqual(world.take_dropped_bumps(), [(200, world.current, (2, 1), ["left", "right"])])


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

    def test_a_doormat_is_one_way_out(self) -> None:
        """(the step-4 verifier's round) Into the house's DOWN floor from the town's door: the player arrives above the mat
        (8, 4); the mat's other tile (9, 4), the same look side by side across its arrow, leads back too (`mat_tiles`), so
        neither is an exit "not used yet" (measured live: the explorer left May's house by the mat's other tile before going
        upstairs to May). And a mat USED leads its other tile there too. FAULT (mutant W88: a doormat tile by tile): (9, 4)
        unknown, the explorer's "door"."""
        game = self.house()
        game.map, game.pos = "TOWN", (4, 4)
        game.trail = [(game.map, game.pos)]
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(explore_intent("DOWN", "Story", 4000), "go in"))
        self.assertTrue(outcome.startswith("done"), outcome)
        keys = {map_name: key for key, map_name in world.names().items()}
        back = {xy: (world.warps.get(f"{keys['DOWN']}|{xy}") or {}).get("to") for xy in ("8,4", "9,4")}
        self.assertEqual(back, {"8,4": keys["TOWN"], "9,4": keys["TOWN"]}, back)
        doors = [c for c in candidates(nav, game.look(), WEIGHTS["Story"]) if c.kind == "door" and c.exit in ((8, 4), (9, 4))]
        self.assertEqual(doors, [], "the doormat's other tile is not an exit not used yet")
        used = WorldMemory()
        down = used.maps["0:0"] = memory_module.MapMemory("0:0", "DOWN", "DOWN")
        mat = memory_module.TileFact(False, False, False, False, None, False, True, 3, "SOUTH_ARROW_WARP", 10, (8, 3))
        down.tiles[(8, 4)], down.tiles[(9, 4)] = mat, replace(mat)
        down.tiles[(7, 4)] = replace(mat, warp=False, behavior="NORMAL")
        self.assertEqual(memory_module.mat_tiles(down, (8, 4)), [(9, 4)], "across the arrow, the same look, not the floor")
        self.assertEqual(memory_module.mat_tiles(down, (7, 4)), [], "a floor tile is no mat")

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

    # ---- build step 3.1, the step-3 review's finding 5: exits by their LOOK, the rest learned by using them
    #: A hall with one door-looking tile in its top wall, 'X' (2, 1), that does not open (no warp: a closed door).
    DOORS = {"TOWN": ["#######", "##X####", "#.....#", "#.....#", "#######"]}

    def doors(self, remember: bool = True) -> tuple[WorldMemory, list[list]]:
        """Two intents in a row; the presses into the door in each."""
        game = GridGame(self.DOORS, ("TOWN", (2, 3)))
        hands, nav, world, notes, lines = rig(game)
        tries = []
        with (contextlib.nullcontext() if remember else mock.patch.object(WorldMemory, "close_exit", lambda self, xy, how, frame: None)):
            for intent in range(2):
                notes.records.clear()
                drive(nav.run(explore_intent(None, "Story", 1200), "look around"), budget=40_000)
                tries.append([r for r in notes.records if str(r["reason"]).startswith("use the door at (2, 1)")])
        return world, tries

    def test_a_door_that_does_not_open_is_remembered_closed(self) -> None:
        """The closed door is tried in the first intent the way a door is used (from below, pressing up), and then
        remembered CLOSED: not an exit any more (`MapMemory.exits`), so a later intent never tries it. FAULT (not
        remembered): the next intent tries it again (an exclusion lasts one intent)."""
        world, tries = self.doors()
        town = world.here()
        self.assertIn((2, 1), town.closed, f"{town.closed}")
        self.assertNotIn((2, 1), town.exits())
        self.assertTrue(tries[0] and all(r["action"].startswith("hold Up") for r in tries[0]), "used the way a door looks to be")
        self.assertEqual(tries[1], [], "the second intent never pressed into the closed door")

    def test_fault_a_closed_door_not_remembered_is_tried_again(self) -> None:
        world, tries = self.doors(remember=False)
        self.assertIn((2, 1), world.here().exits(), "still an exit to the memory")
        self.assertTrue(tries[0] and tries[1], "tried again in the second intent")

    # ---- the step-3.1 verifier's round: "a door found closed stays closed for good (MapMemory.closed has no expiry)"
    def story_doors(self, flag_at: int | None) -> tuple[WorldMemory, list[list], list[str]]:
        """The closed door of `doors`, two intents, the story flags on every look; `flag_at`: a story flag set from that
        frame on (between the two intents), or None."""
        game = StoryGame(self.DOORS, ("TOWN", (2, 3)))
        game.events = {} if flag_at is None else {flag_at: "FLAG_SOMETHING_HAPPENED"}
        hands, nav, world, notes, lines = rig(game)
        tries = []
        for intent in range(2):
            notes.records.clear()
            drive(nav.run(explore_intent(None, "Story", 1200), "look around"), budget=40_000)
            tries.append([r for r in notes.records if str(r["reason"]).startswith("use the door at (2, 1)")])
        return world, tries, lines

    def test_a_hidden_story_flag_alone_does_not_reopen_a_door(self) -> None:
        """(build step 3.2, the step-3.1 review's LOW finding 5: "doors reopen on hidden story-flag counts") A story flag
        set between the two intents is a bit in the save, nothing a person SEES: the door found closed stays closed and
        the second intent does not try it. (Step 3.1 reopened it here.) FAULT (the hidden count is news again: mutant
        W69): tried again."""
        world, tries, lines = self.story_doors(flag_at=1300)
        self.assertTrue(tries[0], "tried in the first intent")
        self.assertEqual(tries[1], [], "the second intent never pressed into it")
        self.assertIn((2, 1), world.here().closed)
        self.assertFalse(any("worth a try again" in line for line in lines), lines[-4:])

    def news_doors(self, words_at: int | None) -> tuple[WorldMemory, list[list], list[str]]:
        """`doors`' two intents, with NEWS a person could see between them (`NewsGame`: from `words_at` on, the next
        moment the player stands still, a scene says words never heard before)."""
        game = NewsGame(self.DOORS, ("TOWN", (2, 3)))
        game.news = {} if words_at is None else {words_at: "The door next to you creaked."}
        hands, nav, world, notes, lines = rig(game)
        tries = []
        for intent in range(2):
            notes.records.clear()
            drive(nav.run(explore_intent(None, "Story", 1200), "look around"), budget=40_000)
            tries.append([r for r in notes.records if str(r["reason"]).startswith("use the door at (2, 1)")])
        return world, tries, lines

    def test_a_closed_door_is_tried_again_after_news_a_person_could_see(self) -> None:
        """Found closed in the first intent; words never heard before between the two (something a person SEES happen):
        the door is worth a try again, and the second intent tries it. FAULT (no reopening on news: mutant W46): never
        tried again, the door hidden until the time rule."""
        world, tries, lines = self.news_doors(1300)
        self.assertTrue(tries[0] and tries[1], f"tried in both intents: {[len(t) for t in tries]}")
        self.assertTrue(any("worth a try again: news since it was found closed: words never read before" in line
                            for line in lines), lines[-6:])

    def test_news_is_what_a_person_could_see(self) -> None:
        """`WorldMemory`'s NEWS, one look at a time, each reopening the closed door: words never read before on the
        overworld; a map never stood on before; a Pokemon of the player's never seen before (by PID). NOT news: the same
        words again, a battle's words, a story flag newly set (a bit of the save), the party first read."""
        maps = {"TOWN": self.DOORS["TOWN"], "IN": ["#####", "#...#", "#####"]}

        def mon(pid: int) -> MonSummary:
            return MonSummary(slot=0, species="Mudkip", dex=258, level=5, hp=20, max_hp=20, status="ok", types=("Water",),
                              moves=(), pid=pid, ot_id=1, is_egg=False)

        def closed():
            game = GridGame(maps, ("TOWN", (2, 3)))
            world = WorldMemory()
            world.observe(replace(game.look(), party=(mon(1),), storage=()))
            world.close_exit((2, 1), "pressed up", 50)
            return game, world

        def says(look: Observation, words: str, battle: bool = False) -> Observation:
            screen = replace(look.screen, waits_for_button=True, text=words, text_box_open=True, in_battle=battle,
                             game_state="BATTLE" if battle else "OVERWORLD")
            return replace(look, screen=screen)

        def reopened(world: WorldMemory, look: Observation) -> bool:
            world.observe(look)
            world.observe(replace(look, frame=look.frame + 1))  # the next look reopens what this one's news allows
            return (2, 1) not in world.maps[map_key(0, 1)].closed

        from ai_player.eyes.observation import Progress
        from ai_player.world.memory import map_key

        game, world = closed()
        self.assertTrue(reopened(world, says(replace(game.look(), frame=100), "A sign: LITTLEROOT TOWN")), "new words")
        game, world = closed()
        world.observe(says(replace(game.look(), frame=60), "A sign: LITTLEROOT TOWN"))
        world.close_exit((2, 1), "pressed up", 70)
        self.assertFalse(reopened(world, says(replace(game.look(), frame=100), "A sign: LITTLEROOT TOWN")), "the same words")
        game, world = closed()
        self.assertFalse(reopened(world, says(replace(game.look(), frame=100), "Wild ZIGZAGOON appeared!", battle=True)),
                         "a battle's words")
        game, world = closed()
        game.map, game.pos = "IN", (2, 1)
        self.assertTrue(reopened(world, replace(game.look(), frame=100)), "a new map")
        game, world = closed()
        self.assertTrue(reopened(world, replace(game.look(), frame=100, party=(mon(1), replace(mon(2), slot=1)), storage=())),
                        "a new Pokemon")
        game, world = closed()
        flags = Progress(money=0, badges=(), dex_owned=0, dex_seen=0, owned_dex=(), flags=(("FLAG_SOMETHING", True),))
        self.assertFalse(reopened(world, replace(game.look(), frame=100, progress=flags)), "a story flag is no news")
        self.assertEqual(world.news, 0)

    def test_a_closed_door_is_tried_again_after_a_while(self) -> None:
        """With no story news a closed door is worth a try again `CLOSED_RETRY_FRAMES` after it was found closed (a
        person tries a locked door again later), not before. FAULT (no time rule: mutant W47): closed for good."""
        game = GridGame(self.DOORS, ("TOWN", (2, 3)))
        world = WorldMemory()
        world.observe(game.look())
        world.close_exit((2, 1), "pressed up", 100)
        self.assertNotIn((2, 1), world.here().exits())
        world.observe(replace(game.look(), frame=100 + memory_module.CLOSED_RETRY_FRAMES - 1))
        self.assertNotIn((2, 1), world.here().exits(), "not yet")
        self.assertEqual(world.take_reopened(), [])
        world.observe(replace(game.look(), frame=100 + memory_module.CLOSED_RETRY_FRAMES))
        self.assertIn((2, 1), world.here().exits(), "worth a try again")
        reopened = world.take_reopened()
        self.assertEqual([(key, xy) for _, key, xy, _ in reopened], [(world.current, (2, 1))])

    def test_an_arrow_mat_is_used_by_its_arrow(self) -> None:
        """An arrow mat (`SOUTH_ARROW_WARP`) is approached so that its ARROW is pressed (`navigator.exit_press`), even
        when another side's press would also go into a wall."""
        memory = PlannerTests().memory_of(["#####", "#...#", "#..M#", "#####"])
        approaches = explore_module._approaches(memory, (3, 2), {(3, 1): 1.0, (2, 2): 1.0})
        self.assertEqual([(stand, direction) for stand, direction, _ in approaches], [((3, 1), "down")])


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

    def test_a_trial_the_game_did_not_step_asks_whether_the_player_is_locked(self) -> None:
        """(the step-3.1 verifier's second round) SCENEX's end on Route 101: "Down: 1 step, then the map becomes
        Littleroot" predicted, 0 counted, no map loaded (Birch's rescue scene holds the player): LOCKED is asked."""
        from ai_player.gates.game_answer import stopped_trials

        def trial(predicted: int, counted: int, changed: bool = False, battle: bool = False) -> dict:
            return {"predicted": {"steps": predicted}, "game_steps": counted, "map_changed": changed, "battle": battle}

        self.assertTrue(stopped_trials([trial(1, 0), trial(0, 0)]), "Route 101's arrival: Down 1 predicted, 0 counted")
        self.assertFalse(stopped_trials([trial(0, 0)]), "a wall right beside: nothing to tell")
        self.assertFalse(stopped_trials([trial(3, 2)]), "a wrong claim walks, just not as predicted")
        self.assertFalse(stopped_trials([trial(1, 0, changed=True)]), "a map loaded: it moved")
        self.assertFalse(stopped_trials([trial(1, 0, battle=True)]), "a battle met: that trial says nothing")


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

    def test_reversals_in_the_looks_path(self) -> None:
        """(build step 3.1, finding 2) `live_step3.reversals` on the review's own two examples, and `walk_path` from
        action-log digests: a warp between two looks starts a new stretch (no reversal is counted across it)."""
        from ai_player.gates import live_step3

        town = [("0:9", xy) for xy in [(11, 8), (11, 7), (12, 7), (12, 6), (11, 6)]]
        self.assertEqual([(r["kind"], r["tiles"]) for r in live_step3.reversals(town)],
                         [("u-turn", [[11, 7], [12, 7], [12, 6], [11, 6]])], "TOWN (11,7) -> (12,7) -> (12,6) -> (11,6)")
        route = [("0:16", xy) for xy in [(16, 9), (17, 9), (18, 9), (17, 9), (17, 8)]]
        self.assertEqual([(r["kind"], r["tiles"]) for r in live_step3.reversals(route)],
                         [("back", [[17, 9], [18, 9], [17, 9]])], "ROUTE (17,9) -> (18,9) -> (17,9)")
        self.assertEqual(live_step3.reversals([("0:9", (x, 5)) for x in range(8)]), [], "a straight walk")
        self.assertEqual(live_step3.reversals([("0:9", (3, 5)), ("0:9", (4, 5)), ("1:4", (3, 5))]), [], "across a map change")

        def rec(frame, xy, to=None, key="0,9", decision="x"):
            walk = to is not None
            gate = (f"walk {'up' if to[1] < xy[1] else 'down' if to[1] > xy[1] else 'left' if to[0] < xy[0] else 'right'}: "
                    f"({xy[0]}, {xy[1]}) -> ({to[0]}, {to[1]}) (seen NORMAL)") if walk else "watching: a scene plays"
            return {"frame": frame, "decision": decision, "action": "hold Up 8f" if walk else "busy 30f", "reason": gate,
                    "digest": f"f{frame} overworld LITTLEROOT TOWN({key}) xy=({xy[0]},{xy[1]}) facing=up walking"}

        records = [rec(1, (5, 9), (5, 8)), rec(2, (5, 8), (5, 7)), rec(3, (5, 7), (5, 6)),
                   rec(4, (5, 7)),  # a bump: the step to (5, 6) never happened (no look shows it)
                   rec(5, (5, 7), (5, 8)),  # straight back: the AI's own A -> B -> A
                   rec(6, (5, 8)), rec(7, (5, 9)),  # a SCENE moves the player (no walking press): not the AI's step
                   rec(8, (5, 9), (5, 8)),  # begins where the scene left it: a new stretch, nothing compared across it
                   rec(85, (5, 8)),  # the look that shows that step done
                   rec(9, (2, 2), (2, 3), "1,4"), rec(10, (2, 3), (2, 2), "1,4"), rec(11, (2, 2), key="1,4")]
        run = live_step3.Run(live_step3.ARMS[0], records=records)
        self.assertEqual(live_step3.walk_path(run), [[("0:9", (5, 9)), ("0:9", (5, 8)), ("0:9", (5, 7)), ("0:9", (5, 8))],
                                                     [("0:9", (5, 9)), ("0:9", (5, 8))],
                                                     [("1:4", (2, 2)), ("1:4", (2, 3)), ("1:4", (2, 2))]])
        steps, found = live_step3.path_reversals(run)
        self.assertEqual((steps, [(r["map"], r["kind"]) for r in found]), (6, [("0:9", "back"), ("1:4", "back")]))

    # ---- build step 3.2, the step-3.1 review's HIGH finding 2: "the reversal metric cannot see laps"
    def test_laps_in_a_walk(self) -> None:
        """`live_step3.laps`: back on a tile 4..12 steps after the player last stood there, the same map, NOTHING NEW
        between (no tile of that map first seen, no novelty told, from the press that LEFT the tile to the press that
        came back onto it): a lap. A 2-step A -> B -> A is a reversal's (`reversals`); 14 steps is a walk round a block.
        FAULT (nothing new not asked: mutant W70): the round that showed a new tile is a lap too."""
        from ai_player.gates import live_step3

        def stretch(tiles: list) -> list:
            # a stretch's first tile carries its first step's press frame (`walk_stretches`), every step 16 frames on
            return [("0:9", tiles[0], 100)] + [("0:9", xy, 100 + 16 * i) for i, xy in enumerate(tiles[1:])]

        ring = stretch([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])  # round one tile: 4 steps, presses f100..f148
        self.assertEqual([(lap["tile"], lap["steps"]) for lap in live_step3.laps(ring, {}, [])], [([0, 0], 4)])
        self.assertEqual(len(live_step3.laps(ring, {"0:9": [10, 90]}, [150])), 1, "seen before it left, told after it came back")
        self.assertEqual(live_step3.laps(ring, {"0:9": [10, 120]}, []), [], "a tile first seen on the way round: not a lap")
        self.assertEqual(live_step3.laps(ring, {}, [130]), [], "a novelty told on the way round: not a lap")
        self.assertTrue(live_step3.laps(ring, {"1:4": [120]}, []), "a tile first seen on another map is not new HERE")
        self.assertEqual(live_step3.laps(stretch([(0, 0), (1, 0), (0, 0)]), {}, []), [], "A -> B -> A is a reversal")
        block = [(x, 0) for x in range(5)] + [(4, y) for y in (1, 2, 3)] + [(x, 3) for x in (3, 2, 1, 0)] + [(0, 2), (0, 1), (0, 0)]
        self.assertEqual(live_step3.laps(stretch(block), {}, []), [], "14 steps round a block is not a lap round a room")
        twelve = [(x, 0) for x in range(5)] + [(4, 1), (4, 2)] + [(x, 2) for x in (3, 2, 1, 0)] + [(0, 1), (0, 0)]
        self.assertEqual([lap["steps"] for lap in live_step3.laps(stretch(twelve), {}, [])], [12])

    def test_rings_in_a_walk(self) -> None:
        """(the step-3.2 verifier's round: "the new CYCLE check (`laps`) does not tell the fix from the revert ... every one
        is exempted by 'new tile between'") `live_step3.rings`: back on a tile 4..12 steps later having walked ROUND (every
        tile between once), WHATEVER was seen on the way; an out-and-back (A B C B A) is a turn back, not a ring. The
        verifier's own example from the reverted SCENEXL is one. FAULT (mutant W76: the round not asked): the out-and-back
        counts."""
        from ai_player.gates import live_step3

        def stretch(tiles: list) -> list:
            return [("0:9", tiles[0], 100)] + [("0:9", xy, 100 + 16 * i) for i, xy in enumerate(tiles[1:])]

        ring = stretch([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        self.assertEqual([(r["tile"], r["steps"]) for r in live_step3.rings(ring)], [([0, 0], 4)])
        self.assertEqual(live_step3.laps(ring, {"0:9": [10, 120]}, []), [], "laps: a tile seen on the way exempts it")
        self.assertEqual(len(live_step3.rings(ring)), 1, "rings: it is a ring whatever was seen on the way")
        self.assertEqual(live_step3.rings(stretch([(0, 0), (1, 0), (2, 0), (1, 0), (0, 0)])), [], "out and back: a turn back")
        self.assertEqual(live_step3.rings(stretch([(0, 0), (1, 0), (0, 0)])), [], "A -> B -> A")
        block = [(x, 0) for x in range(5)] + [(4, y) for y in (1, 2, 3)] + [(x, 3) for x in (3, 2, 1, 0)] + [(0, 2), (0, 1), (0, 0)]
        self.assertEqual(live_step3.rings(stretch(block)), [], "14 steps round a block")
        verifier = [(5, 3), (5, 2), (4, 2), (3, 2), (3, 3), (2, 3), (2, 4), (2, 5), (3, 5), (4, 5), (5, 5), (5, 4), (5, 3)]
        self.assertEqual([r["steps"] for r in live_step3.rings(stretch(verifier))], [12], "the verifier's SCENEXL ring")

    def test_a_ring_that_saw_new_tiles_is_counted_by_the_report(self) -> None:
        """`live_step3.lap_report` on an action log that walks round a pillar while a tile is first seen on the way: no lap
        (nothing new between fails), ONE ring. FAULT (mutant W77: rings only where nothing new was seen, `laps`' rule):
        none."""
        from ai_player.gates import live_step3

        rows = ["#####", "#...#", "#.#.#", "#...#", "#####"]
        world = self.room_world(rows, seen_late={(3, 3): 230})
        loop = [(1, 1), (2, 1), (3, 1), (3, 2), (3, 3), (2, 3), (1, 3), (1, 2), (1, 1)]
        steps = [(200 + 16 * i, a, b) for i, (a, b) in enumerate(zip(loop, loop[1:]))]
        run = live_step3.Run(live_step3.ARMS[0], records=self.walk_records([(190, (1, 1), (1, 1), None)], steps), world=world)
        report = live_step3.lap_report(run)
        self.assertEqual((len(report["laps"]), len(report["rings"])), (0, 1), (report["laps"], report["rings"]))

    def test_journeys_join_the_targets_chosen_on_the_move(self) -> None:
        """(the step-3.2 verifier's round: "steps-vs-shortest is measured per DECISION ... near 0 by construction wherever
        targets churn") `live_step3.journeys`: a target chosen standing and every target chosen ON THE MOVE whose walk
        begins where the last ended are ONE journey: three one-step walks out and back are 3 steps from (1, 2) to (1, 3)
        where the shortest is 1. FAULT (mutant W78: never joined): three journeys, each its own shortest."""
        from ai_player.gates import live_step3

        def walk(frame, frm, to, on_the_move):
            return {"map": "0:9", "from": list(frm), "to": list(to), "walked": 1, "frame": frame, "on_the_move": on_the_move,
                    "detour": None, "end_frame": frame + 8}

        trips = live_step3.journeys([walk(10, (1, 2), (1, 3), None), walk(30, (1, 3), (1, 4), True),
                                     walk(50, (1, 4), (1, 3), True), walk(70, (5, 5), (5, 6), True)])
        self.assertEqual([(t["from"], t["to"], t["walked"], t["targets"]) for t in trips],
                         [([1, 2], [1, 3], 3, 3), ([5, 5], [5, 6], 1, 1)], "a walk that does not begin where the last ended is another")
        standing = live_step3.journeys([walk(10, (1, 2), (1, 3), None), walk(30, (1, 3), (1, 4), None)])
        self.assertEqual(len(standing), 2, "a target chosen STANDING begins a journey")

    @staticmethod
    def room_world(rows: list[str], seen_late: dict | None = None, bumped: dict | None = None) -> dict:
        """A world.jsonl snapshot of one map "0:9" from character rows ('.' floor seen at f10, '#' wall, '>' a ledge
        jumped going right), `seen_late`: tile -> the frame it was first seen; `bumped`: "x,y|direction" -> first frame."""
        tiles = {}
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                letters, ledge = ("b", "") if c == "#" else ("", "right") if c == ">" else ("", "")
                tiles[f"{x},{y}"] = [letters, ledge, 3, "NORMAL", (seen_late or {}).get((x, y), 10), 0, 0]
        return {"maps": {"0:9": {"tiles": tiles, "bumped": {k: {"first": f, "bumps": 1} for k, f in (bumped or {}).items()}}}}

    def test_the_shortest_known_way(self) -> None:
        """`live_step3.known_shortest`: over the tiles the memory had seen BY the frame asked, a wall, a ledge (only in its
        jump direction, landing beyond), a way in learned blocked by a bump by then (per side). FAULTS: when a tile was
        first seen not asked (mutant W71); the bumps not asked (W72)."""
        from ai_player.gates import live_step3

        rows = ["#####", "#...#", "#.#.#", "#...#", "#####"]  # round a pillar (2, 2): (1, 2) -> (3, 2) is 4 steps
        self.assertEqual(live_step3.known_shortest(self.room_world(rows), "0:9", (1, 2), (3, 2), 100), 4)
        late = {(2, 1): 500, (2, 3): 500}
        self.assertIsNone(live_step3.known_shortest(self.room_world(rows, late), "0:9", (1, 2), (3, 2), 100), "not seen yet")
        self.assertEqual(live_step3.known_shortest(self.room_world(rows, late), "0:9", (1, 2), (3, 2), 600), 4)
        bumps = self.room_world(rows, bumped={"2,1|right": 50, "2,3|right": 50})
        self.assertIsNone(live_step3.known_shortest(bumps, "0:9", (1, 2), (3, 2), 100), "both ways in bumped from that side")
        self.assertEqual(live_step3.known_shortest(bumps, "0:9", (1, 2), (3, 2), 40), 4, "a bump learned later was not known")
        self.assertEqual(live_step3.known_shortest(bumps, "0:9", (3, 2), (1, 2), 100), 4, "the other side of the same tiles is open")
        ledge = ["#####", "#...#", "#.>.#", "#...#", "#####"]
        self.assertEqual(live_step3.known_shortest(self.room_world(ledge), "0:9", (1, 2), (3, 2), 100), 1, "jumped")
        self.assertEqual(live_step3.known_shortest(self.room_world(ledge), "0:9", (3, 2), (1, 2), 100), 4, "not against it")

    @staticmethod
    def walk_records(decisions: list[tuple], steps: list[tuple]) -> list[dict]:
        """An action log: `decisions` (frame, player, target, detour) and `steps` (frame, from, to): each step a walking
        press whose look stands on its `from`, and a last look on the last step's `to`."""
        def press(frame, frm, to):
            d = "up" if to[1] < frm[1] else "down" if to[1] > frm[1] else "left" if to[0] < frm[0] else "right"
            return {"frame": frame, "decision": "x", "action": "hold Up 8f", "reason": f"walk {d}: ({frm[0]}, {frm[1]}) -> "
                    f"({to[0]}, {to[1]}) (seen NORMAL)", "digest": f"f{frame} overworld LITTLEROOT TOWN(0,9) xy=({frm[0]},{frm[1]}) facing=up"}

        records = [{"frame": f, "decision": "decide", "action": "target frontier", "reason": "x",
                    "extra": {"map": "0:9", "kind": "frontier", "target": list(t), "player": list(p), "detour": d}}
                   for f, p, t, d in decisions] + [press(*s) for s in steps]
        last = steps[-1][2]
        records.append({"frame": steps[-1][0] + 16, "decision": "watch", "action": "busy 1f", "reason": "x",
                        "digest": f"f{steps[-1][0] + 16} overworld LITTLEROOT TOWN(0,9) xy=({last[0]},{last[1]}) facing=up"})
        return sorted(records, key=lambda r: r["frame"])

    def test_the_walk_to_each_target_against_the_shortest_known_way(self) -> None:
        """`live_step3.target_walks` / `lap_report`: from the tile it decided on to where the walk ended (the next decision),
        the steps walked against the shortest known way: a walk round the pillar the long way, 6 steps where 4 would do, is
        2 beyond; a decision with a DETOUR (by design) is reported, not graded; `check_laps` holds a run to its bounds and
        FAILS a run with nothing graded (it would say nothing: mutant W73)."""
        from ai_player.gates import live_step3

        rows = ["######", "#....#", "#.#..#", "#....#", "######"]
        world = self.room_world(rows)
        long_way = [(1, 2), (1, 3), (2, 3), (3, 3), (4, 3), (4, 2), (3, 2)]  # 6 steps; round the top is 4
        steps = [(200 + 16 * i, a, b) for i, (a, b) in enumerate(zip(long_way, long_way[1:]))]
        detoured = [(400 + 16 * i, a, b) for i, (a, b) in enumerate(zip([(3, 2), (3, 1), (2, 1)], [(3, 1), (2, 1), (1, 1)]))]
        records = self.walk_records([(190, (1, 2), (3, 2), None), (390, (3, 2), (1, 1), [3, 1])], steps + detoured)
        run = live_step3.Run(live_step3.ARMS[0], records=records, world=world)
        walks = live_step3.target_walks(run)
        self.assertEqual([(w["from"], w["to"], w["walked"], w["shortest"], w["excess"]) for w in walks],
                         [([1, 2], [3, 2], 6, 4, 2), ([3, 2], [1, 1], 3, 3, 0)])
        report = live_step3.lap_report(run)
        self.assertEqual((report["graded"], report["excess"], report["worst"], len(report["detoured"])), (1, 2, 2, 1))
        verdicts = []
        for bound, data in (({"laps": 0, "excess": 2, "worst": 2}, records), ({"laps": 0, "excess": 1, "worst": 2}, records),
                            ({"laps": 0, "excess": 2, "worst": 1}, records), ({"laps": 0, "excess": 9, "worst": 9}, records[-2:])):
            graded = live_step3.Run(live_step3.ARMS[0], records=data, world=world)
            live_step3.check_laps(graded, bound)
            verdicts.append(graded.passed)
        self.assertEqual(verdicts, [True, False, False, False], "within; excess over; worst over; nothing graded")

    # ---- the step-3.1 verifier's round: the live graders that now tell the fixed code from the reverted one
    @staticmethod
    def decide(frame, kind, target, player, key="0:9", reason="1 unseen tile(s) beside it"):
        return {"frame": frame, "decision": "decide", "action": f"target {kind} {tuple(target)}", "reason": reason,
                "extra": {"map": key, "kind": kind, "target": list(target), "player": list(player)},
                "digest": f"f{frame} overworld LITTLEROOT TOWN({key.replace(':', ',')}) xy=({player[0]},{player[1]}) facing=up"}

    def test_stale_arrivals_from_the_action_log_and_the_memory(self) -> None:
        """`live_step3.stale_arrivals`: a frontier target whose NEXT decision is made standing on it, with no stale drop
        between, was walked onto; whether everything beside it had been seen by then comes from the memory's own
        first-seen frames. A target dropped as stale on the way (the fix) is not one. FAULT (the drop not looked for:
        mutant W49): the dropped target counts as walked onto."""
        from ai_player.gates import live_step3

        world = WorldMemory()
        memory = world.maps["0:9"] = memory_module.MapMemory("0:9", "T", "LITTLEROOT_TOWN")
        fact = memory_module.TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 10, (5, 9))
        for xy in [(5, 4), (5, 6), (4, 5), (6, 5), (8, 4), (8, 6), (7, 5), (9, 5)]:
            memory.tiles[xy] = fact
        memory.tiles[(5, 4)] = replace(fact, seen_frame=45)  # seen on the way, before the arrival at f50
        records = [self.decide(10, "frontier", (5, 5), (5, 9)), self.decide(50, "frontier", (8, 5), (5, 5)),
                   {"frame": 60, "decision": "world", "action": "say", "reason": "the frontier at (8, 5) is not worth going to "
                    "any more: everything beside it has been seen on the way", "extra": {"stale": [8, 5], "kind": "frontier", "map": "0:9"}},
                   self.decide(70, "frontier", (2, 2), (8, 5))]
        run = live_step3.Run(live_step3.ARMS[0], records=records, world=world.to_dict())
        chosen, arrived = live_step3.stale_arrivals(run)
        self.assertEqual(chosen, 3)
        self.assertEqual([(a["target"], a["arrived"], a["everything_beside_it_seen"]) for a in arrived], [([5, 5], 50, True)])
        memory.tiles[(5, 4)] = replace(fact, seen_frame=55)  # first seen only AFTER the arrival: it was not stale then
        run = live_step3.Run(live_step3.ARMS[0], records=records, world=world.to_dict())
        self.assertEqual([a["everything_beside_it_seen"] for a in live_step3.stale_arrivals(run)[1]], [False])

    def test_a_carried_on_target_is_the_one_walked_onto(self) -> None:
        """(the step-4 verifier's round) A decision CARRIED ON (`brain/explore.py` carry_on) walks to the last place it was
        carried on to: the next decision made standing there is an arrival at THAT place (whose sides are then graded),
        not at the place first decided on. FAULT (mutant W86: the carry-ons not read): the arrival is missed."""
        from ai_player.gates import live_step3

        world = WorldMemory()
        memory = world.maps["0:9"] = memory_module.MapMemory("0:9", "T", "LITTLEROOT_TOWN")
        fact = memory_module.TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 10, (5, 9))
        for xy in [(5, 3), (5, 5), (4, 4), (6, 4)]:
            memory.tiles[xy] = fact
        records = [self.decide(10, "frontier", (5, 5), (5, 9)),
                   {"frame": 30, "decision": "world", "action": "say", "reason": "the frontier at (5, 5) is seen past now (x): the "
                    "same decision carries on to the frontier at (5, 4)", "extra": {"carry_on": [5, 4], "from": [5, 5], "map": "0:9"}},
                   self.decide(60, "frontier", (2, 2), (5, 4))]
        run = live_step3.Run(live_step3.ARMS[0], records=records, world=world.to_dict())
        chosen, arrived = live_step3.stale_arrivals(run)
        self.assertEqual([(a["target"], a["arrived"], a["everything_beside_it_seen"]) for a in arrived], [([5, 4], 60, True)])

    def edge_run(self, decides: list[dict], connections: list[dict]):
        from ai_player.gates import live_step3

        return live_step3.Run(live_step3.ARMS[0], records=decides, world={"maps": {}, "connections": connections})

    def test_targets_past_an_edge_before_a_crossing_of_that_edge(self) -> None:
        """`live_step3.edge_targets` / `check_no_road_before_a_crossing`: a target past a map's REAL edge (the ROM's size,
        here pinned) before a crossing of THAT edge was seen; a road among them fails the check, and so does a run with
        none at all (it would say nothing: the step-3.1 verifier's "never fires"). A crossing of ANOTHER edge (ROUTE's
        loaded memory crossed Route 101's bottom edge) says nothing about the top one. FAULTS: the crossing per map
        (mutant W50), the check without its non-vacuity (mutant W51)."""
        from ai_player.gates import live_step3

        sizes = {"0:9": [20, 20], "0:16": [20, 20]}
        bottom = {"source": "0:9", "target": "0:16", "direction": "up", "frame": 10}  # Littleroot -> Route 101's BOTTOM edge
        top = {"source": "0:16", "target": "0:10", "direction": "up", "frame": 100}  # Route 101's TOP edge
        honest = [self.decide(50, "frontier", (11, -1), (11, 2), "0:16"), self.decide(60, "frontier", (11, 5), (11, 7), "0:16"),
                  self.decide(150, "frontier", (11, -2), (11, 0), "0:16")]
        road = self.decide(70, "road", (12, -1), (11, 2), "0:16", "a road leads up, off this map")
        with mock.patch.dict(live_step3._MAP_SIZES, sizes):
            past, crossings = live_step3.edge_targets(self.edge_run(honest + [road], [bottom, top]))
            self.assertEqual([(t["target"], t["kind"], t["side"]) for t in past], [([11, -1], "frontier", "up"), ([12, -1], "road", "up")],
                             "past the TOP edge before its crossing at f100 (the bottom edge's crossing at f10 says nothing)")
            self.assertEqual([t["target"] for t in live_step3.road_claims(past)], [[12, -1]])
            verdicts = []
            for records in (honest, honest + [road], [honest[1]]):
                run = self.edge_run(records, [bottom, top])
                live_step3.check_no_road_before_a_crossing(run)
                verdicts.append(run.passed)
        self.assertEqual(verdicts, [True, False, False], "honest: pass; a road before the crossing: fail; nothing past an edge: fail")
        self.assertEqual(live_step3.past_real_edge((20, 3), [20, 20]), "right")
        self.assertIsNone(live_step3.past_real_edge((19, 19), [20, 20]))

    def test_scenes_by_the_tile_they_began_on(self) -> None:
        """`live_step3.scenes_by_tile`: the AI's own `began`, and the tile of the look of the walking press the scene cut
        short (the second reading the SCENEX grade compares)."""
        from ai_player.gates import live_step3

        press = {"frame": 5, "decision": "x", "action": "hold Up 8f", "reason": "walk up: (10, 1) -> (10, 0) (seen NORMAL)",
                 "digest": "f5 overworld LITTLEROOT TOWN(0,9) xy=(10,1) facing=up"}
        scene = {"frame": 900, "decision": "world", "action": "say", "reason": "a scene stopped the way to the frontier at (9, -4) "
                 "(time 1 for this target)", "extra": {"scene_for": [9, -4], "kind": "frontier", "began": [10, 1], "after": [10, 2]}}
        found = live_step3.scenes_by_tile([press, scene])
        self.assertEqual(list(found), [(10, 1)])
        self.assertEqual((found[(10, 1)][0]["pressed_from"], found[(10, 1)][0]["target"]), ((10, 1), (9, -4)))

    def test_an_inconclusive_answer_with_nothing_else_fails(self) -> None:
        from ai_player.gates import live_step3

        run = live_step3.Run(live_step3.ARMS[0], after={"map": [1, 0], "pos": [8, 3]},
                             answer={"inconclusive": True, "loaded_header_is_claimed_map": True, "plans": {}})
        live_step3.check_game_answer(run)
        self.assertFalse(run.passed, run.checks)

    def test_a_pre_registered_number_that_does_not_hold_fails_the_arm(self) -> None:
        """(the step-3.1 verifier's second round: "A PRE-REGISTERED PREDICTION DID NOT HOLD AND THIS IS NOT SAID ANYWHERE":
        ROUTER predicted 4 stale targets walked onto, measured 5, and its check asked only for >= 1) `check_predictions`
        compares every number `PREDICTED` registers with the run's own: all equal passes; one off FAILS and says which."""
        from ai_player.gates import live_step3

        arm = next(a for a in live_step3.ARMS if a.name == "ROUTER")
        predicted = {"ROUTER": {"frames": 2083, "presses": 108, "stale_walked": 4}}
        run = live_step3.Run(arm, harness={"frames": 2083, "presses": 108})
        run.measure("stale_walked", 5)
        live_step3.check_predictions(run, predicted)
        self.assertFalse(run.passed, run.checks)
        self.assertIn("stale_walked 4 != 5", run.checks[-1][1])
        run = live_step3.Run(arm, harness={"frames": 2083, "presses": 108})
        run.measure("stale_walked", 4)
        live_step3.check_predictions(run, predicted)
        self.assertTrue(run.passed, run.checks)
        run = live_step3.Run(arm, harness={"frames": 2083, "presses": 108})
        live_step3.check_predictions(run, {})
        self.assertEqual(run.checks, [], "an arm with no registered numbers gets no check")

    def test_the_clock_arm_registers_frames_only_where_every_clock_agrees(self) -> None:
        """(the step-3.1 verifier's second round, found by its graded run: SCENEX9 played 15,959 frames where its development
        run played 14,462, because the game reads the host's clock) `grade_CLOCKS`: an arm whose runs at every instant are
        the same may pre-register its launcher frames, and must, at those frames; an arm that changes with the clock is
        exactly a declared clock-sensitive one, registers none, and its claims hold at every instant. FAULTS: a sensitive arm
        not declared; a stable arm registered at other frames; a sensitive arm registered at all; a twin rule broken at one
        instant."""
        from ai_player.gates import live_step3

        def rows(scenex_second: tuple = (3, 0), excess_second: int = 0, rings_second: int = 0, ones_second: float = 0.2) -> list[dict]:
            out = []
            for when in ("t1", "t2"):
                out.append({"arm": "HOUSE", "when": when, "frames": 3176, "presses": 36})
                segments = [3, 0] if when == "t1" else list(scenex_second)
                # (build step 3.2) the lap metrics of a clock-sensitive SCENEX arm at each instant (`LAP_BOUNDS`); (the
                # step-3.2 verifier's round) its rings too; (the step-4 verifier's round) its LAP rings and its churn
                out.append({"arm": "SCENEX", "when": when, "frames": 16293 if when == "t1" else 14344, "presses": 489,
                            "twin_segments": segments, "map": [0, 16], "var": 2, "laps": 0, "lap_graded": 40,
                            "lap_excess": 0 if when == "t1" else excess_second, "lap_worst": 0 if when == "t1" else excess_second,
                            "rings": 0 if when == "t1" else rings_second, "lap_rings": 0 if when == "t1" else rings_second,
                            "walks": 30, "move_per_100": 10.0, "ones_share": 0.2 if when == "t1" else ones_second,
                            "journey_share": 0.3})
            return out

        def grade(data: list[dict], sensitive=("SCENEX",), predicted=None) -> bool:
            arm = next(a for a in live_step3.ARMS if a.name == "CLOCKS")
            run = live_step3.Run(arm, harness={"rows": data})
            with mock.patch.object(live_step3, "CLOCK_SENSITIVE", sensitive), \
                    mock.patch.object(live_step3, "PREDICTED", predicted or {"HOUSE": {"frames": 3176}}):
                live_step3.grade_CLOCKS(run)
            return run.passed

        self.assertTrue(grade(rows()), "HOUSE stable and registered at 3176; SCENEX varies, declared, unregistered")
        self.assertFalse(grade(rows(), sensitive=()), "a clock-sensitive arm nobody declared")
        self.assertFalse(grade(rows(), predicted={"HOUSE": {"frames": 3000}}), "a stable arm registered at other frames")
        self.assertFalse(grade(rows(), predicted={"HOUSE": {"frames": 3176}, "SCENEX": {"frames": 16293}}),
                         "a clock-sensitive arm registered with frames")
        self.assertFalse(grade(rows(scenex_second=(4, 0))), "the twin rule broken at one instant")
        with mock.patch.dict(live_step3.LAP_BOUNDS, {"SCENEX": {"laps": 0, "excess": 2, "worst": 2, "lap_rings": 0}}):
            self.assertTrue(grade(rows(excess_second=2)), "(build step 3.2) the lap bounds held at every instant")
            self.assertFalse(grade(rows(excess_second=3)), "(build step 3.2) a lap bound broken at one instant")
            self.assertFalse(grade(rows(rings_second=1)), "(the step-3.2 verifier's round) a LAP ring at one instant")
            self.assertFalse(grade(rows(ones_second=0.6)), "(the step-4 verifier's round) the churn bound broken at one instant")

    def test_a_lap_ring_has_a_leg_walked_round(self) -> None:
        """(the step-4 verifier's round) `live_step3.rings` counts ONE LOOP ONCE (a walk that goes on along the loop it has
        just closed is not a second ring), and a ring is a LAP RING (`lap_ring`) when one of its legs (the walks to each
        decision inside it, `ring_legs`) walked beyond the shortest known way to its own target; a loop whose every leg was
        the shortest way to its own target (out to a place, the shortest way back by the next column) is an excursion.
        FAULTS: every ring a lap ring (mutant W82); the same loop counted twice (W83)."""
        from ai_player.gates import live_step3

        def stretch(tiles: list) -> list:
            return [("0:9", tiles[0], 100)] + [("0:9", xy, 100 + 16 * i) for i, xy in enumerate(tiles[1:])]

        loop = [(1, 1), (2, 1), (2, 2), (1, 2), (1, 1), (2, 1)]  # round once, then one step on along the same round
        self.assertEqual(len(live_step3.rings(stretch(loop))), 1, "one loop, one ring")
        ring = live_step3.rings(stretch(loop))[0]
        out_and_back = [{"map": "0:9", "frame": 100, "end_frame": 116, "excess": 0, "detour": None},
                        {"map": "0:9", "frame": 120, "end_frame": 148, "excess": 0, "detour": None}]
        self.assertFalse(live_step3.lap_ring(ring, out_and_back), "every leg the shortest way to its own target: an excursion")
        walked_round = [{"map": "0:9", "frame": 100, "end_frame": 148, "excess": 2, "detour": None}]
        self.assertTrue(live_step3.lap_ring(ring, walked_round), "a leg 2 beyond its shortest way: a lap ring")
        detour = [{"map": "0:9", "frame": 100, "end_frame": 148, "excess": 2, "detour": [2, 2]}]
        self.assertFalse(live_step3.lap_ring(ring, detour), "a leg with a detour (by design) is said, not held against it")
        elsewhere = [{"map": "1:4", "frame": 100, "end_frame": 148, "excess": 3, "detour": None},
                     {"map": "0:9", "frame": 500, "end_frame": 600, "excess": 3, "detour": None}]
        self.assertFalse(live_step3.lap_ring(ring, elsewhere), "legs on another map or at another time are not this ring's")

    def test_after_news_the_twin_once_on_each_tile(self) -> None:
        """(the step-4 verifier's round) `live_step3.once_a_tile_after_news`: after each news she may send the player back once
        on each tile (the rule gives every tile she began on up at its first meeting after the news, a tile first met after
        it included); twice on one tile after the same news fails. FAULT (mutant W87: at most once IN ALL after each news,
        the check the development sweep's seed 10 failed though the rule did what it says)."""
        from ai_player.gates import live_step3

        self.assertTrue(live_step3.once_a_tile_after_news([{"10,1": 2}, {"10,1": 1, "11,1": 1}]))
        self.assertTrue(live_step3.once_a_tile_after_news([{"10,1": 2, "11,1": 1}, {"11,1": 1}, {}]))
        self.assertFalse(live_step3.once_a_tile_after_news([{"10,1": 2}, {"10,1": 2}]))
        self.assertFalse(live_step3.once_a_tile_after_news([{"10,1": 2}, {}, {"11,1": 2}]))

    def test_the_churn_of_decisions(self) -> None:
        """(the step-4 verifier's round, finding 4) `live_step3.churn` / `check_churn` on a synthetic action log: two
        decisions, the second ON THE MOVE, three places carried on (one where the step-3.2 rule would have gone elsewhere),
        one stale target dropped because something clearly better came into view; the bounds hold the run (the one-step
        walks' share over the bound FAILS it)."""
        from ai_player.gates import live_step3

        rows = ["#######", "#.....#", "#.....#", "#######"]
        world = self.room_world(rows)
        steps = [(200 + 16 * i, (1 + i, 1), (2 + i, 1)) for i in range(4)] + [(300, (5, 1), (5, 2))]
        records = self.walk_records([(190, (1, 1), (2, 1), None), (290, (5, 1), (5, 2), None)], steps)
        records[[i for i, r in enumerate(records) if r.get("decision") == "decide"][1]]["extra"]["on_the_move"] = True
        say = lambda frame, reason, extra: {"frame": frame, "decision": "world", "action": "say", "reason": reason, "extra": extra}
        records += [say(210, "the frontier at (2, 1) is seen past now (x): the same decision carries on", {"carry_on": [3, 1]}),
                    say(226, "the frontier at (3, 1) is seen past now (x): the same decision carries on", {"carry_on": [4, 1],
                                                                                                   "step32_would": [1, 2]}),
                    say(242, "the frontier at (4, 1) is seen past now (x): the same decision carries on", {"carry_on": [5, 1]}),
                    say(285, "the frontier at (5, 1) is not worth going to any more: x; choosing again on the move",
                        {"stale": [5, 1], "refused": "the door at (5, 2) is worth 9.0 from here, clearly more than the "
                                                     "frontier at (5, 0) it would carry on to (5.0)"})]
        records.sort(key=lambda r: r["frame"])
        run = live_step3.Run(live_step3.ARMS[0], records=records, world=world)
        c = live_step3.churn(run)
        self.assertEqual((c["decisions"], c["on_the_move"], c["carried"], c["would"], c["dropped"], c["refused_better"]),
                         (2, 1, 3, 1, 1, 1))
        self.assertEqual((c["steps"], c["walks"], c["ones"]), (5, 2, 1))
        verdicts = []
        for bound in ({"move_per_100": 25.0, "ones": 0.5, "journey_share": 0.5}, {"move_per_100": 25.0, "ones": 0.4, "journey_share": 0.5}):
            graded = live_step3.Run(live_step3.ARMS[0], records=records, world=world)
            live_step3.check_churn(graded, None, bound)
            verdicts.append(graded.passed)
        self.assertEqual(verdicts, [True, False], "within; one-step walks over the bound")

    def test_a_locked_arrival_across_a_connection(self) -> None:
        """(the step-3.1 verifier's second round) SCENEX's end: a walking trial the game did not step, LOCKED, and THE
        ARRIVAL across the pre-registered edge (Littleroot (11, 0) up -> Route 101 (11, 19)) agrees: PASS; the same with
        the crossing not the pre-registered one, or the fault claim agreeing, or the player not locked: FAIL."""
        from ai_player.gates import live_step3

        arm = next(a for a in live_step3.ARMS if a.name == "SCENEX")
        lock = {"locked": True, "held_frames": 120, "held": {"Up": {"game_steps": 0, "moved": False, "map_changed": False}}}
        trial = {"direction": "Down", "agree": False, "game_steps": 0, "map_changed": False, "loaded_map": [0, 16],
                 "predicted": {"steps": 1, "ends": "map", "map": [0, 9]}}

        def grade(crossing=([0, 9], [11, 0], "Up"), locked=True, fault_agrees=False) -> bool:
            arrival = {"connection": {"map": crossing[0], "tile": crossing[1], "direction": crossing[2], "offset": 0},
                       "map": [0, 16], "landing": [11, 19], "landing_behaviour": "Normal", "exit_step": [0, 0], "tile": [11, 19],
                       "agrees": True, "raw_landing_is_the_claim": True}
            answer = {"inconclusive": False, "agree": False, "trials": [trial], "loaded_header_is_claimed_map": True,
                      "locked": {**lock, "locked": locked}, "arrival": arrival, "agree_by_arrival": locked,
                      "ruled_out": [[10, 19]], "plans": {}}
            world = {"transitions": [[34718, "0:9", "0:16", "connection", "ai", [11, 0], [11, 19], "up"]], "maps": {}}
            run = live_step3.Run(arm, after={"map": [0, 16], "pos": [11, 19]}, answer=answer, world=world,
                                 answer_fault={"agree_by_arrival": False, "agree": fault_agrees})
            live_step3.check_game_answer(run)
            return run.passed

        self.assertTrue(grade(), "locked, the pre-registered crossing, the fault claim disagrees")
        self.assertFalse(grade(crossing=([0, 9], [10, 0], "Up")), "another crossing than the pre-registered one")
        self.assertFalse(grade(locked=False), "not locked: the walking answer disagrees and nothing else answers")
        self.assertFalse(grade(fault_agrees=True), "the fault claim agrees by walking")


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

    #: (build step 3.1) the route north is TALL, as Route 101 is: the 15 x 11 window never shows its end, so the tiles at
    #: its top row are frontier (a road known only once crossed: the step-3 review's finding 1)
    ROUTE_ROWS = 12

    def run_town(self, crop: bool, seed: int = 3):
        maps = {"TOWN": self.TOWN, "ROUTE": ["#..#"] * self.ROUTE_ROWS}
        links = {("TOWN", "up"): ("ROUTE", (-1, self.ROUTE_ROWS)), ("ROUTE", "down"): ("TOWN", (1, -self.ROUTE_ROWS))}
        game = GridGame(maps, ("TOWN", (18, 16)), links=links, crop=crop)
        hands, nav, world, notes, lines = rig(game, seed=seed)
        outcome = drive(nav.run(explore_intent("ROUTE", "Story", 12000), "leave town"))
        decisions = [r["extra"] for r in notes.records if r["decision"] == "decide"]
        self.world = world
        #: (build step 3.2, the step-4 verifier's round) the places a decision was CARRIED ON to (`brain/explore.py` carry_on)
        self.carried = [r["extra"] for r in notes.records if r["decision"] == "world" and (r["extra"] or {}).get("carry_on")]
        return outcome, decisions, game

    def test_every_target_was_seen(self) -> None:
        for seed in (1, 2, 3):
            outcome, decisions, game = self.run_town(crop=True, seed=seed)
            self.assertTrue(outcome.startswith("done"), outcome)
            self.assertTrue(decisions)
            for extra in decisions:
                self.assertTrue(extra["known"] and on_screen_from(tuple(extra["seen_from"]), tuple(extra["target"])), extra)
            self.assertTrue(decisions[0]["in_window"], "the first target is on screen")

    def test_fault_the_crop_off_beelines_to_a_place_it_could_not_see(self) -> None:
        for seed in (1, 2, 3):
            real, real_decisions, real_game = self.run_town(crop=True, seed=seed)
            real_carried = list(self.carried)
            outcome, decisions, game = self.run_town(crop=False, seed=seed)
            self.assertTrue(outcome.startswith("done"), outcome)
            first = decisions[0]
            # (build step 3.1) no crossing seen: the place past the top edge is frontier, the far end of what the
            # uncropped eyes showed (its top row), not a 'road'
            self.assertEqual(first["kind"], "frontier")
            self.assertLess(first["target"][1], -5, f"the first target {first['target']} is past anything a window showed")
            self.assertFalse(first["in_window"], f"the first target {first['target']} is off the screen")
            # the beeline: ONE decision, and the true shortest walk onto the road tile it CROSSED at, give or take the
            # seeded detour (`navigator.DETOUR_P`: a tile beside the way, at most 4 steps more) (the step count alone
            # does not tell a beeline: see live_step3 CROP)
            crossed = self.world.connections[0]["from"]
            detours = sum(1 for d in decisions if d.get("detour"))
            self.assertEqual(len(decisions), 1, decisions)
            self.assertTrue(self.shortest(crossed[0]) <= game.steps <= self.shortest(crossed[0]) + 4 * detours,
                            f"a beeline: {game.steps} steps, the true shortest walk over the edge {self.shortest(crossed[0])}, "
                            f"{detours} detour(s)")
            # (build step 3.2) the honest walk RE-TARGETS on what it sees, the beeline does not. Its LENGTH is no
            # discriminator (as live_step3's CROP says): with the heading kept on the move, the honest explorer reaches
            # this model's road in about the beeline's steps (measured 2026-10-08: seeds 1-6, 35-38 steps against 35-37).
            # (The step-4 verifier's round) a decision is now CARRIED ON as the view opens rather than made again, so the
            # re-targets are its decisions and its carry-ons (measured 2026-10-09, seeds 1-3: 4 decisions and 23-25
            # carry-ons; the beeline 1 decision and 0 carry-ons)
            moves, beeline = len(real_decisions) + len(real_carried), len(decisions) + len(self.carried)
            self.assertGreater(moves, 5 * beeline, f"seed {seed}: {len(real_decisions)} decisions, {len(real_carried)} carried on; "
                                                    f"the beeline {len(decisions)}, {len(self.carried)}")


class WindowTests(unittest.TestCase):
    """(build step 3.1, the step-3 review's finding 6) The gate's crop check writes the screen's window as LITERALS
    (`gates/window.py`: 7 columns each side, 5 rows each way), never the eyes' VIEW_* constants: widen the eyes' window
    and the gate must still flag a tile seen from 8 columns away. FAULT (the gate takes the eyes' constants, as
    `world/memory.py` in_window does): the widened eyes pass their own check."""

    @staticmethod
    def check(run_world: dict) -> list[tuple[bool, str]]:
        from ai_player.gates import live_step3

        run = live_step3.Run(live_step3.ARMS[0], world=run_world, records=[])
        live_step3.check_crop(run)
        return run.checks

    def test_a_tile_seen_from_8_columns_away_fails_the_gate_however_wide_the_eyes_are(self) -> None:
        world = WorldMemory()
        memory = world.maps["0:1"] = memory_module.MapMemory("0:1", "M", "M")
        fact = memory_module.TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (10, 10))
        memory.tiles[(17, 10)] = fact  # 7 columns away: on screen
        memory.tiles[(18, 10)] = replace(fact)  # 8 columns away: never on screen
        data = world.to_dict()
        for widened in (False, True):
            with self.subTest(widened=widened):
                # the eyes' window widened to 9 columns each side, where the gate used to read it (`world/memory.py`
                # in_window's VIEW_HALF_WIDTH): a gate that measures the eyes against themselves now passes (18, 10)
                with (mock.patch.object(memory_module, "VIEW_HALF_WIDTH", 9) if widened else contextlib.nullcontext()):
                    checks = self.check(data)
                crop = next(text for ok, text in checks if text.startswith("THE CROP"))
                self.assertFalse(next(ok for ok, text in checks if text.startswith("THE CROP")), crop)
                self.assertIn("(18, 10)", crop)

    def test_the_window_is_the_screen(self) -> None:
        from ai_player.gates import window

        self.assertEqual((window.SCREEN_HALF_WIDTH, window.SCREEN_UP, window.SCREEN_DOWN), (7, 5, 5))
        self.assertTrue(on_screen_from((10, 10), (17, 15)) and on_screen_from((10, 10), (3, 5)))
        self.assertFalse(on_screen_from((10, 10), (18, 10)) or on_screen_from((10, 10), (10, 16)))


class ReversalTests(unittest.TestCase):
    """(build step 3.1, the step-3 review's finding 2, HIGH) STALE TARGETS: the navigator kept a frontier target until it
    ARRIVED, though the walk there had shown everything beside it, and then turned back: TOWN "(11,7) -> (12,7) -> (12,6)
    -> (11,6)", ROUTE "(17,9) -> (18,9) -> (17,9)". Now a stale target is dropped on the move (`stale_reason`) and the
    next plan pays `TURN_BACK_COST` for going back the way it came (`Navigator.turn_costs`). REVERSALS (`live_step3.
    reversals`: A -> B -> A, or a U-turn's third step) are graded on the town model, 12 seeds. MEASURED 2026-10-08 before
    the rules (`gates/revert_step3.py` W30, W31 and this file's faults): both rules 2 reversals in 730 steps; the stale
    drop alone 28 in 677 (it re-decides on the move, toward places behind as often as ahead); the turn-back cost alone
    12 in 788 (arrivals clear the heading); neither (step 3) 12 in 788.
    (BUILD STEP 3.2, measured 2026-10-08 on this model, 12 seeds) with the plan charged once and FOLLOWED and the HEADING
    kept on the move (`brain/explore.py` pick_on_the_move): 0 reversals in 429 steps (the walks to the road 41% shorter).
    The turn-back cost ALONE no longer carries this model (0 without it: the heading rule keeps the walk going); the
    step-3.1 choice ON THE MOVE (a whim) without it: 28 in 677, the fault half below. Where the turn charge now carries
    weight is the decision's own plan: `LapTests`."""

    SEEDS = range(1, 13)

    @staticmethod
    def walk(seed: int):
        from ai_player.gates.live_step3 import reversals

        arrivals: list[tuple] = []
        original = navigator_module.Navigator.toward

        def toward(nav, target, look, why):
            result = yield from original(nav, target, look, why)
            if result == "arrived" and target.kind == "frontier":
                memory = nav.world.here()
                arrivals.append((target.tile, memory.unknown_neighbours(target.tile) if memory else None))
            return result

        with mock.patch.object(navigator_module.Navigator, "toward", toward):
            outcome, decisions, game = CropTests().run_town(crop=True, seed=seed)
        assert outcome.startswith("done"), outcome
        return reversals(game.trail), game.steps, arrivals

    def totals(self) -> tuple[int, int, list]:
        found, steps, arrivals = [], 0, []
        for seed in self.SEEDS:
            r, s, a = self.walk(seed)
            found += r
            steps += s
            arrivals += a
        return len(found), steps, arrivals

    def test_reversals_are_near_zero_and_no_stale_target_is_walked_onto(self) -> None:
        count, steps, arrivals = self.totals()
        self.assertLessEqual(count, 3, f"{count} reversals in {steps} steps over {len(self.SEEDS)} seeds")
        self.assertEqual(arrivals, [], "a frontier target walked onto: the walk there had already shown it (stale)")

    def test_fault_without_the_turn_back_cost_the_stale_drop_reverses_often(self) -> None:
        """(build step 3.2) the step-3.1 fault, as it now has to be stated: no turn-back cost AND the choice on the move
        a WHIM again (the step-3.1 rule): the stale drop re-decides toward places behind as often as ahead (measured
        2026-10-08 on this code: 12 reversals in 662 steps, against 0 in 429; on the step-3.1 code, with its plan charged
        at every step, 28 in 677). With the heading kept on the move, no turn-back cost alone gives 0 here."""
        # (build step 3.2, the step-4 verifier's round) and no carry-on: the step-3.1 explorer re-decided at every stale
        # step (with the decision carried on, the whim on the move is rarely asked: 0 reversals in 469 steps)
        with mock.patch.object(navigator_module, "TURN_BACK_COST", 0.0), \
                mock.patch.object(explore_module, "choose_target", whim_on_the_move(explore_module.choose_target)), \
                mock.patch.object(sys.modules[__name__], "explore_intent", no_carry_on(explore_module.explore_intent)):
            count, steps, arrivals = self.totals()
        self.assertGreaterEqual(count, 8, f"{count} reversals in {steps} steps")

    def test_fault_without_the_stale_drop_targets_are_walked_onto_and_reversed_from(self) -> None:
        with mock.patch.object(navigator_module, "stale_reason", lambda memory, target: None):
            count, steps, arrivals = self.totals()
        self.assertGreaterEqual(count, 8, f"{count} reversals in {steps} steps")
        self.assertTrue(arrivals and all(unknown == 0 for _, unknown in arrivals),
                        f"every frontier target walked onto, everything beside it seen: {arrivals[:4]}")


def whim_on_the_move(original):
    """FAULT (the step-3.1 rule, `revert_step3.py` W66): a target chosen ON THE MOVE is picked like one chosen standing,
    on a whim among equals with the score's jitter (`Navigator.choosing_on_the_move` ignored)."""

    def choose(nav, look, weights, goal=None):
        nav.choosing_on_the_move = False
        return original(nav, look, weights, goal)

    return choose


def revisits(trail: list, low: int = 4, high: int = 12) -> list[tuple]:
    """(build step 3.2) Every step back onto a tile of the same map `low`..`high` steps after the player last stood there,
    in a model's trail (`GridGame.trail`; its maps are all on screen, so nothing new is seen between: a LAP, as
    `live_step3.laps` grades it)."""
    out, last = [], {}
    for j, place in enumerate(trail):
        i = last.get(place)
        last[place] = j
        if i is not None and low <= j - i <= high:
            out.append((place, j - i))
    return out


class LapTests(unittest.TestCase):
    """(build step 3.2, the step-3.1 adversarial review's HIGH finding 1) "The turn-back cost is charged on EVERY replan,
    so the AI walks LAPS instead of turning back (SCENEX: 8 steps around a room where 2 would do)." MEASURED 2026-10-08 on
    the memory SCENEX seed 3 held at f20190 (pinned clock): at (6, 18), walking left past the corner of a house, the
    target the door's stand tile (7, 17), up-right behind it; the step-3.1 plan was down, right, up, up, then, charged
    again at the next tile, left, up, right, right, up: 10 steps where 2 would do. `CORNER` is that corner. Now turning
    round is charged ONCE, by the decision (where to go: `TURN_BACK_COST`; its first plan: `TURN_ROUND_COST`, a
    tie-breaker), and the plan is FOLLOWED. FAULTS: the step-3.1 rule (mutant W62); the plan not followed (W63); no
    turn-back cost at all (W32); never switching to a clearly better way (W74)."""

    #: (6, 1) is the house's corner (a wall), (7, 1) the door's stand tile beside it; the player on (6, 2), walking LEFT
    #: (it came from (8, 2) through (7, 2)). The whole room is on screen from there: nothing new is seen while walking.
    CORNER = ["#############", "#.....#.....#", "#...........#", "#...........#", "#############"]

    def corner(self, seed: int = 3):
        game = GridGame({"TOWN": self.CORNER}, ("TOWN", (6, 2)))
        hands, nav, world, notes, lines = rig(game, seed=seed)
        world.observe(game.look())
        nav.recent = [(world.current, "left"), (world.current, "left")]
        game.trail = [("TOWN", (7, 2)), ("TOWN", (6, 2))]
        outcome = drive(nav.run(goto_intent([(7, 1)], 3000), "to the door behind"), budget=20_000)
        return game, outcome, nav

    def test_a_target_behind_is_reached_by_turning_back(self) -> None:
        """Turning back costs the decision 1 tile in its plan, going round costs 2 more steps (and a U-turn): it turns
        back, 2 steps, and walks no lap. Every seed (the path noise)."""
        for seed in range(1, 9):
            game, outcome, nav = self.corner(seed)
            self.assertTrue(outcome.startswith("done"), outcome)
            self.assertEqual((game.steps, revisits(game.trail[1:])), (2, []), f"seed {seed}: {game.trail}")

    def test_fault_the_turn_back_cost_on_every_replan_walks_a_lap(self) -> None:
        """FAULT (the step-3.1 rule: every step's plan charged `TURN_BACK_COST` for turning round, no plan followed): a lap
        round the room, back on a tile it stood on 8 steps before, 10 steps in all (the measured SCENEX walk)."""
        with mock.patch.object(navigator_module.Navigator, "_next_step", step31_next_step):
            game, outcome, nav = self.corner()
        self.assertTrue(outcome.startswith("done"), outcome)
        self.assertGreaterEqual(game.steps, 8, game.trail)
        self.assertTrue(revisits(game.trail[1:]), f"no lap: {game.trail}")

    #: (build step 3.2, the plan FOLLOWED) a room; the player stepped DOWN from (5, 2) onto (5, 3); the target (7, 2) is
    #: up-right of it: three ways of 3 steps (right right up; right up right: a U round (6, 2); up right right: straight
    #: back). The house's 2F as HOUSE seed 3 met it (a frontier gone stale one step down, the stairs behind).
    ROOM = ["##########", "#........#", "#........#", "#........#", "#........#", "##########"]

    def room(self, seed: int):
        game = GridGame({"ROOM": self.ROOM}, ("ROOM", (5, 3)))
        hands, nav, world, notes, lines = rig(game, seed=seed)
        world.observe(game.look())
        nav.recent = [(world.current, "down")]
        game.trail = [("ROOM", (5, 2)), ("ROOM", (5, 3))]
        outcome = drive(nav.run(goto_intent([(7, 2)], 2000), "to the stairs"), budget=12_000)
        return game, outcome, nav

    def turned_round(self, seeds=range(1, 21)) -> list:
        """The seeds whose walk turned round (A -> B -> A or a U-turn, `live_step3.reversals`) where an equally short way
        that does not existed."""
        from ai_player.gates.live_step3 import reversals

        out = []
        for seed in seeds:
            game, outcome, nav = self.room(seed)
            assert outcome.startswith("done") and game.steps == 3, (outcome, game.trail)
            if reversals(game.trail):
                out.append((seed, game.trail[1:]))
        return out

    def test_the_decisions_plan_is_followed_and_turns_round_only_to_break_a_tie(self) -> None:
        """Three ways of the same length: the decision's plan takes the one that does not turn round (its 1-tile charge
        breaks the tie the path noise would otherwise break), and FOLLOWS it: 20 seeds, none turns round. FAULTS: the plan
        redone at every step without a charge (mutant W63: the next step's tie falls to the noise); no turn charge at all
        (W32)."""
        self.assertEqual(self.turned_round(), [])

    def test_fault_replanned_every_step_it_turns_round_for_nothing(self) -> None:
        with mock.patch.object(navigator_module, "PLAN_SWITCH_MARGIN", -1.0):  # every fresh plan replaces the plan
            self.assertTrue(self.turned_round(), "no seed turned round with the plan replaced at every step")
        with mock.patch.object(navigator_module, "TURN_ROUND_COST", 0.0), mock.patch.object(navigator_module, "TURN_BACK_COST", 0.0):
            self.assertTrue(self.turned_round(), "no seed turned round with no turn charge at all")

    #: (build step 3.2) a shortcut that comes into view: the straight way along the bottom row is UNSEEN in its middle
    #: (priced optimistically, 3 a tile), so the decision's plan goes round by the top (20 steps); one step on, the middle
    #: is seen to be floor: the straight way is 13 against 19 left.
    LOOP = ["###############", "#.............#", "#.###########.#", "#.###########.#", "#.###########.#", "#.............#",
            "###############"]

    def test_a_shortcut_that_comes_into_view_is_taken(self) -> None:
        """`PLAN_SWITCH_MARGIN`: a fresh plan clearly better than what is left of the plan followed (by more than the
        margin) replaces it, uncharged: down to the bottom row, not on round the top. FAULT (never switch: mutant W74):
        the plan round the top is kept."""
        middle = {(x, 5) for x in range(3, 12)}
        memory = PlannerTests().memory_of(self.LOOP, {(x, y) for x in range(15) for y in range(7)} - middle)
        world = WorldMemory()
        world.maps[memory.key] = memory
        world._last.key = memory.key
        nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world, random.Random(1))
        target = Target("goto", (13, 5), "the far end")
        first = nav._next_step(memory, (1, 5), target, frozenset())
        self.assertEqual((first, len(nav.plan.path)), ("up", 20), "round the top: 20 steps against 30 through the unseen")
        nav.plan.path.pop(0)
        nav.plan.at = (1, 4)
        full = PlannerTests().memory_of(self.LOOP)
        for xy in middle:
            memory.tiles[xy] = full.tiles[xy]
        self.assertEqual(nav._next_step(memory, (1, 4), target, frozenset()), "down")
        self.assertEqual((nav.stats.switches, nav.plan.charged, len(nav.plan.path)), (1, False, 13))


def step31_next_step(self, memory, here, target, walls):
    """FAULT (the step-3.1 rule, `revert_step3.py` W62): every step planned afresh, charged `TURN_BACK_COST` for
    turning straight back or completing a U-turn on its first step (no pair charge: step 3.1 had none)."""
    turns = {key: value for key, value in self.turn_costs().items() if isinstance(key, str)}
    path = astar(memory, here, {target.tile}, walls, self.grass_cost, self.noise_for(target), first=turns)
    return path[0] if path else None


class HeadingTests(unittest.TestCase):
    """(build step 3.2, the step-3.1 adversarial review's MEDIUM finding 4) "The AI changes target almost every step (22 of
    23 dropped as stale)", each re-picked on a WHIM among equals. A target chosen ON THE MOVE now keeps the heading
    (`explore.pick_on_the_move`): the best place AHEAD unless another is better by more than `CHOICE_MARGIN`, and no draw.
    FAULTS: the whim on the move (mutant W66), the heading not preferred (W67)."""

    #: the player on (5, 5) walking RIGHT: a place ahead, one behind, one beside
    PLACES = [Target("frontier", (9, 5), "ahead", 10.0), Target("frontier", (1, 5), "behind", 13.0),
              Target("frontier", (5, 1), "beside", 12.5)]

    def test_the_heading_is_kept_unless_another_place_is_clearly_better(self) -> None:
        from ai_player.brain.explore import CHOICE_MARGIN, ahead, pick_on_the_move

        self.assertEqual(pick_on_the_move(self.PLACES, (5, 5), "right").tile, (9, 5), "3 points behind the best: kept")
        clearly = [self.PLACES[0], replace(self.PLACES[1], score=10.0 + CHOICE_MARGIN + 0.5), self.PLACES[2]]
        self.assertEqual(pick_on_the_move(clearly, (5, 5), "right").tile, (1, 5), "beaten by more than the margin")
        self.assertEqual(pick_on_the_move(self.PLACES, (5, 5), "up").tile, (5, 1), "walking up: the place ahead is (5, 1)")
        self.assertEqual(pick_on_the_move(self.PLACES[1:], (5, 5), "right").tile, (1, 5), "nothing ahead: the best")
        self.assertEqual(pick_on_the_move(list(reversed(self.PLACES)), (5, 5), "right"), pick_on_the_move(self.PLACES, (5, 5), "right"))
        self.assertFalse(ahead((5, 5), (5, 1), "right"), "beside is not ahead")

    def test_no_draw_on_the_move(self) -> None:
        """The same memory, the same heading, 20 different choice seeds: ON THE MOVE every seed chooses the same place
        (no whim, no jitter); STANDING they choose among several (the whim among equals stays where it belongs). FAULT
        (the whim on the move: W66): the seeds differ on the move too."""
        moving = self.choices(True)
        self.assertEqual(len(moving), 1, moving)
        self.assertGreater(len(self.choices(False)), 1)

    @staticmethod
    def choices(on_the_move: bool) -> set:
        field = ["#" * 31] + ["#" + "." * 29 + "#" for _ in range(15)] + ["#" * 31]
        out = set()
        for seed in range(20):
            game = GridGame({"FIELD": field}, ("FIELD", (15, 8)))
            hands, nav, world, notes, lines = rig(game, seed=seed)
            world.observe(game.look())
            nav.recent = [(world.current, "right")]
            nav.choosing_on_the_move = on_the_move
            out.add(choose_target(nav, game.look(), WEIGHTS["Story"]).tile)
        return out


def no_carry_on(original):
    """FAULT (the step-3.2 rule, `revert_step3.py` W79): an explore intent whose decisions are never carried on: a stale
    target is dropped and a new one chosen on the move at every stale step."""

    def make(*args, **kwargs):
        intent = original(*args, **kwargs)
        intent.carry_on = None
        return intent

    return make


class ChurnTests(unittest.TestCase):
    """(build step 3.2, the step-4 verifier: "finding 4 ... is NOT fixed: ... 22 of 23 dropped as stale ... decisions on
    the move 35 of 47 ... 28 of the 47 walks a single step"). A frontier tile at the screen's edge is seen past as soon as
    the player steps toward it, so the step-3.2 explorer re-decided at nearly every step. Now the DECISION is carried on
    (`brain/explore.py` carry_on): the place it meant moves on with the view, and a new decision is made only when nothing
    of it is left there or something clearly better came into view (`CARRY_SWITCH_MARGIN`). FAULTS: no carry-on (the
    step-3.2 rule: W79), no margin (carried on for good: W80), a carry-on that slides ALONG the screen's edge (W81)."""

    #: an open field taller and wider than the window: the player on (15, 20) walking UP
    FIELD = ["#" * 31] + ["#" + "." * 29 + "#" for _ in range(28)] + ["#" * 31]

    def walked_up(self, field=None, personality: str = "Story"):
        """The player on (15, 20) looks, steps up to (15, 19) and looks again: the frontier tile (15, 15) at the top of the
        first window (its unseen side up, (15, 14)) is now seen past."""
        game = GridGame({"FIELD": field or self.FIELD}, ("FIELD", (15, 20)))
        hands, nav, world, notes, lines = rig(game, personality=personality)
        world.observe(game.look())
        game.frame += 100
        game.pos = (15, 19)
        world.observe(game.look())
        nav.recent = [(world.current, "up")]
        nav.carry_note = {}
        return nav, game, world

    def test_the_decision_carries_on_as_the_view_opens(self) -> None:
        from ai_player.brain.explore import carry_on
        from ai_player.brain.navigator import stale_reason

        nav, game, world = self.walked_up()
        old = Target("frontier", (15, 15), "1 unseen tile(s) beside it", 10.0)
        self.assertIsNotNone(stale_reason(world.here(), old), "the step showed what was beside it")
        carried = carry_on(nav, game.look(), WEIGHTS["Story"], old)
        self.assertEqual((carried.kind, carried.tile), ("frontier", (15, 14)), "the place moved on: straight beyond it")
        self.assertIn("carried on from (15, 15)", carried.reason)

    def test_a_place_aside_is_another_place(self) -> None:
        """With the way straight on walled ((14..16, 14) walls), the nearest frontier past the stale tile lies two tiles
        aside, (13, 14): a frontier sliding ALONG the screen's edge, another place: no carry-on, the reason said. FAULT (W81:
        any tile further up, however far aside): carried on to it."""
        from ai_player.brain.explore import carry_on

        field = list(self.FIELD)
        field[14] = field[14][:14] + "###" + field[14][17:]
        nav, game, world = self.walked_up(field)
        old = Target("frontier", (15, 15), "x", 10.0)
        self.assertIsNone(carry_on(nav, game.look(), WEIGHTS["Story"], old))
        self.assertIn("nothing of it left", nav.carry_note.get("refused", ""))
        loose = lambda o, t, sides: any((t[0] - o[0]) * DIRS_LOWER[d][0] + (t[1] - o[1]) * DIRS_LOWER[d][1] >= 1 for d in sides)
        with mock.patch.object(explore_module, "further", loose):
            slid = carry_on(nav, game.look(), WEIGHTS["Story"], old)
        self.assertIsNotNone(slid, "the fault carries on along the edge")
        self.assertGreaterEqual(abs(slid.tile[0] - 15), 2, slid)

    def test_something_clearly_better_ends_the_decision(self) -> None:
        """A Catcher's frontier on TALL GRASS comes into view two columns aside (worth far more to it than the plain tile
        straight on): the decision is not carried on, and the reason names the grass. FAULT (W80, no margin: a decision is
        carried on whatever comes into view): carried on to the plain tile."""
        from ai_player.brain.explore import carry_on

        field = list(self.FIELD)
        field[14] = field[14][:17] + '"' + field[14][18:]
        nav, game, world = self.walked_up(field, personality="Catcher")
        old = Target("frontier", (15, 15), "x", 10.0)
        self.assertIsNone(carry_on(nav, game.look(), WEIGHTS["Catcher"], old))
        self.assertIn("clearly more", nav.carry_note.get("refused", ""))
        self.assertIn("(17, 14)", nav.carry_note.get("refused", ""))
        with mock.patch.object(explore_module, "CARRY_SWITCH_MARGIN", 999.0):
            held = carry_on(nav, game.look(), WEIGHTS["Catcher"], old)
        self.assertEqual(held.tile, (15, 14))

    def test_never_carried_behind_the_player(self) -> None:
        from ai_player.brain.explore import beyond

        self.assertTrue(beyond((15, 19), (15, 15), (15, 14)))
        self.assertTrue(beyond((15, 19), (15, 15), (16, 14)))
        self.assertFalse(beyond((15, 19), (15, 15), (15, 21)), "behind the player")
        self.assertFalse(beyond((15, 19), (15, 15), (18, 19)), "straight beside the player is not on its side")

    @staticmethod
    def town(fault=None) -> tuple[int, int, int, int]:
        """CropTests' town, 12 seeds: (decisions, decisions on the move, steps, runs that reached the road)."""
        decisions = moving = steps = done = 0
        for seed in range(1, 13):
            context = (mock.patch.object(sys.modules[__name__], "explore_intent", fault(explore_module.explore_intent))
                       if fault else contextlib.nullcontext())
            with context:
                outcome, found, game = CropTests().run_town(crop=True, seed=seed)
            decisions += len(found)
            moving += sum(1 for d in found if d.get("on_the_move"))
            steps += game.steps
            done += outcome.startswith("done")
        return decisions, moving, steps, done

    def test_few_decisions_and_no_longer_walk_on_the_town(self) -> None:
        """MEASURED 2026-10-09 on this model: 54 decisions (42 on the move) in 452 steps over 12 seeds, against 338 (326 on
        the move) in 429 with the step-3.2 rule (the fault half): a decision per 8 steps where it was one per step, and the
        walks to the road no more than a tenth longer."""
        decisions, moving, steps, done = self.town()
        fd, fm, fs, fdone = self.town(no_carry_on)
        self.assertEqual((done, fdone), (12, 12))
        self.assertLessEqual(decisions, 80, f"{decisions} decisions ({moving} on the move) in {steps} steps")
        self.assertGreaterEqual(fd, 250, f"FAULT: {fd} decisions ({fm} on the move) in {fs} steps")
        self.assertLessEqual(steps, 1.1 * fs, f"{steps} steps against the step-3.2 rule's {fs}")


DIRS_LOWER = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


class SceneTests(unittest.TestCase):
    """(build step 3.1, the step-3 review's finding 3) A REPEATING SCENE: stepping on a tile starts a scene that puts the
    player back (Littleroot's twin with a player who has no Pokemon: `LittlerootTown_EventScript_NeedPokemonTrigger*`,
    VAR_LITTLEROOT_TOWN_STATE 0). The target kept being chosen, and the ping-pong rule counts warps only, so the scene ran
    again and again until the novelty window (~50 s). Now a target interrupted `SCENE_REPEATS` times by a scene, nothing
    new since the first, is given up. FAULT (no such rule): the scene runs again and again, `stuck: nothing new`."""

    #: The only way north is the tile (2, 2), whose scene puts the player back on (2, 3).
    HALL = ["#####", "##.##", "##.##", "#...#", "#...#", "#####"]

    def run_hall(self, repeats: int | None = None):
        game = GridGame({"TOWN": self.HALL}, ("TOWN", (2, 4)), triggers={("TOWN", (2, 2)): (90, (2, 3))})
        hands, nav, world, notes, lines = rig(game)
        intent = goto_intent([(2, 1)], 20000)
        if repeats is None:
            outcome = drive(nav.run(intent, "past the trigger"), budget=80_000)
        else:
            with mock.patch.object(navigator_module, "SCENE_REPEATS", repeats):
                outcome = drive(nav.run(intent, "past the trigger"), budget=80_000)
        return game, outcome, hands, notes

    def test_a_repeating_scene_gives_the_target_up(self) -> None:
        game, outcome, hands, notes = self.run_hall()
        self.assertTrue(outcome.startswith("stuck: the goto at (2, 1) cannot be reached (a scene stopped the way there 2 "
                                           "times"), outcome)
        self.assertEqual(game.scenes_run, 2)
        self.assertLess(hands.pad.frames, 1500, "given up within seconds, not the novelty window")

    def test_fault_without_the_rule_the_scene_repeats_until_the_novelty_window(self) -> None:
        game, outcome, hands, notes = self.run_hall(repeats=10**6)
        self.assertTrue(outcome.startswith("stuck: nothing new"), outcome)
        self.assertGreaterEqual(game.scenes_run, 8)
        self.assertGreaterEqual(hands.pad.frames, NOVELTY_WINDOW)

    def test_a_scene_that_brings_something_new_is_not_held_against_the_target(self) -> None:
        """A scene on the way that is NOT a repeat (it shows something new: a new map, a flag) does not count against
        the target: the TOWN arm's Running Shoes scene."""
        world = WorldMemory()
        nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world, random.Random(1))
        world._last.key = "0:1"
        novelty = mock.Mock(last=80, last_progress=80)
        target = Target("frontier", (3, 4), "x")
        key = f"0:1|{target.key}"
        self.assertFalse(nav._scene_met(key, target, 90, novelty))
        novelty.last = novelty.last_progress = 150  # something new after the first scene (a flag: progress)
        self.assertFalse(nav._scene_met(key, target, 200, novelty), "new since the first: kept")
        self.assertFalse(nav.is_excluded(target))
        self.assertTrue(nav._scene_met(key, target, 300, mock.Mock(last=80, last_progress=80)), "nothing new since the first: given up")
        self.assertTrue(nav.is_excluded(target))

    # ---- the step-3.1 verifier's round: the rule on targets the EXPLORER chose
    def test_a_tile_seen_in_passing_is_not_progress(self) -> None:
        """'Nothing new since the first' is PROGRESS (a story flag, a Pokemon, items, experience), not a tile that came on
        screen while the scene pushed the player back (measured 2026-10-08 from `littleroot_twin.ss1`, explorer seed 4:
        one new tile after the first scene, and the twin was met 4 times for ONE target). FAULT (any novelty, places
        included, excuses the scene: mutant W45): the target is kept."""
        world = WorldMemory()
        nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world, random.Random(1))
        world._last.key = "0:1"
        target = Target("frontier", (3, 4), "x")
        key = f"0:1|{target.key}"
        self.assertFalse(nav._scene_met(key, target, 90, mock.Mock(last=80, last_progress=80), "0:1", (3, 6), (3, 7)))
        passing = mock.Mock(last=150, last_progress=80)  # a tile seen at f150, no progress since f80
        self.assertTrue(nav._scene_met(key, target, 300, passing, "0:1", (3, 6), (3, 7)), "a tile in passing: given up")
        self.assertEqual(nav.scene_walls, {"0:1": {(3, 6)}}, "and the tile the scene began on is not stepped on again")

    #: A tall field to the north, its only way in a gap (4, 15) whose scene puts the player back on (4, 16) (Littleroot's
    #: twin): the field is taller than the window, so the EXPLORER keeps finding new frontier tiles behind the gap.
    FIELD = ["#########"] + ["#.......#" for _ in range(14)] + ["####.####"] + ["#.......#" for _ in range(3)] + ["#########"]

    def explore_field(self, game=None):
        game = game or GridGame({"TOWN": self.FIELD}, ("TOWN", (4, 17)), triggers={("TOWN", (4, 15)): (90, (4, 16))})
        hands, nav, world, notes, lines = rig(game)
        outcome = drive(nav.run(explore_intent(None, "Story", 9000), "explore"), budget=60_000)
        return game, outcome, nav, notes, lines

    def test_an_explorer_sent_back_from_one_tile_stops_stepping_on_it(self) -> None:
        """The explorer's targets behind the twin CHANGE (a frontier tile given up, the next one chosen behind the same
        gap: measured live, seeds 1-6), so a count per target alone lets the same scene run again and again. Counted per
        TILE it began on, the gap is not stepped on again after the second push back: exactly 2 scenes, and the gap is
        a wall for the rest of the intent. FAULT (no count per tile: mutant W44): the scene runs again for the next target."""
        game, outcome, nav, notes, lines = self.explore_field()
        self.assertEqual(game.scenes_run, 2, f"{game.scenes_run} scenes: {[l for l in lines if 'scene' in l][:6]}")
        self.assertEqual(nav.scene_walls.get(nav.world.current), {(4, 15)})
        later = [r for r in notes.records if str(r["reason"]).startswith("walk ") and "-> (4, 15)" in r["reason"]
                 and r["frame"] > max(nav.scene_spots[f"{nav.world.current}|4,15"])]
        self.assertEqual(later, [], "stepped toward the gap after it was given up")

    def test_fault_without_the_count_per_tile_the_scene_runs_again(self) -> None:
        with mock.patch.object(navigator_module, "SCENE_REPEATS", 2), \
                mock.patch.object(navigator_module.Navigator, "walls", lambda self, memory, here: frozenset(memory.objects_now - {here})):
            game, outcome, nav, notes, lines = self.explore_field()
        self.assertGreaterEqual(game.scenes_run, 3, f"{game.scenes_run} scenes")

    # ---- the step-3.1 verifier's second round: "the twin guards two tiles, so the explorer meets her 4 times in total"
    #: The same field with a gap TWO tiles wide, (4, 15) and (5, 15), guarded by ONE scene (the same words on both tiles,
    #: each pushing the player back one tile): Littleroot's twin and her two coord events, (10, 1) and (11, 1).
    FIELD2 = (["#########"] + ["#.......#" for _ in range(14)] + ["####..###"] + ["#.......#" for _ in range(3)]
              + ["#########"])
    TWIN_WORDS = "Um, um, um! If you go outside and go in the grass, wild POKéMON will jump out."

    def explore_wide_gap(self, words: tuple[str, str] | None = None):
        first, second = words or (self.TWIN_WORDS, self.TWIN_WORDS)
        game = GridGame({"TOWN": self.FIELD2}, ("TOWN", (4, 17)),
                        triggers={("TOWN", (4, 15)): (90, (4, 16), first), ("TOWN", (5, 15)): (90, (5, 16), second)})
        return self.explore_field(game)

    def test_one_scene_on_two_tiles_is_met_at_most_three_times(self) -> None:
        """A person knows the girl by what she SAYS: the same words on the gap's two tiles are ONE scene. Twice with
        nothing new and EVERY tile she began on is not stepped on again: at most 3 meetings (twice on one tile, then a
        side-step onto the other, where the same words close both), never 2 a tile. FAULT (scenes known by tile only:
        mutant W52 and `test_fault_...` below): 4, twice on each tile."""
        game, outcome, nav, notes, lines = self.explore_wide_gap()
        tiles = sorted({tile for _, tile in game.scene_log})
        self.assertLessEqual(game.scenes_run, 3, f"{game.scenes_run} scenes: {game.scene_log}")
        self.assertGreaterEqual(game.scenes_run, 2, "the scene was met (not vacuous)")
        self.assertEqual(nav.scene_walls.get(nav.world.current), set(tiles),
                         f"every tile the same scene began on is given up: {nav.scene_walls} vs {tiles}")
        self.assertTrue(any("the same scene" in line for line in lines), lines[-8:])
        self.assertFalse(any(xy[1] < 15 for name, xy in game.trail), "never got past her")

    def test_fault_scenes_known_by_tile_only_meet_her_twice_a_tile(self) -> None:
        with mock.patch.object(navigator_module, "scene_words", lambda pages: None):
            game, outcome, nav, notes, lines = self.explore_wide_gap()
        per_tile = {tile: sum(1 for _, t in game.scene_log if t == tile) for _, tile in game.scene_log}
        self.assertEqual(game.scenes_run, 4, f"{game.scenes_run} scenes: {per_tile}")
        self.assertEqual(sorted(per_tile.values()), [2, 2])

    def test_different_words_are_different_scenes(self) -> None:
        """Two DIFFERENT scenes on the two tiles (different words) are not one: each is held against its own tile only
        (twice each), as before the words rule."""
        game, outcome, nav, notes, lines = self.explore_wide_gap(("Um, um, um!", "Wait! It's dangerous!"))
        self.assertEqual(game.scenes_run, 4, f"{game.scenes_run} scenes: {game.scene_log}")
        self.assertFalse(any("the same scene" in line for line in lines))

    def test_the_words_rule_directly(self) -> None:
        """`Navigator._scene_met` with words: the same words from two tiles, nothing new since the first: both tiles
        walled at the second; different words: neither; progress since the first: neither; no words: per tile only."""

        def fresh() -> Navigator:
            world = WorldMemory()
            nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world,
                            random.Random(1))
            world._last.key = "0:9"
            return nav

        target = Target("frontier", (10, -4), "x")
        key = f"0:9|{target.key}"
        still = mock.Mock(last=80, last_progress=80)
        nav = fresh()
        nav._scene_met(key, target, 100, still, "0:9", (10, 1), (10, 2), "Um, um, um!")
        nav._scene_met(f"0:9|{Target('frontier', (11, -4), 'y').key}", Target("frontier", (11, -4), "y"), 200, still,
                       "0:9", (11, 1), (11, 2), "Um, um, um!")
        self.assertEqual(nav.scene_walls, {"0:9": {(10, 1), (11, 1)}}, "the same words twice: every tile she began on")
        nav = fresh()
        nav._scene_met(key, target, 100, still, "0:9", (10, 1), (10, 2), "Um, um, um!")
        nav._scene_met(key, target, 200, still, "0:9", (11, 1), (11, 2), "Something else.")
        self.assertEqual(nav.scene_walls.get("0:9", set()), set(), "different words: two scenes, once each")
        nav = fresh()
        nav._scene_met(key, target, 100, still, "0:9", (10, 1), (10, 2), "Um, um, um!")
        nav._scene_met(key, target, 200, mock.Mock(last=150, last_progress=150), "0:9", (11, 1), (11, 2), "Um, um, um!")
        self.assertEqual(nav.scene_walls.get("0:9", set()), set(), "progress since the first: tried again")
        nav = fresh()
        nav._scene_met(key, target, 100, still, "0:9", (10, 1), (10, 2), None)
        nav._scene_met(key, target, 200, still, "0:9", (11, 1), (11, 2), None)
        self.assertEqual(nav.scene_walls.get("0:9", set()), set(), "no words: counted per tile only (once each)")

    # ---- the step-3.1 verifier's second round: "what happens after the twin": NEWS lifts her, once more is enough
    NEWS = "Oh, hello. And you are?"

    def explore_with_news(self):
        game = NewsGame({"TOWN": self.FIELD}, ("TOWN", (4, 17)), triggers={("TOWN", (4, 15)): (90, (4, 16), self.TWIN_WORDS)})
        game.news = {2500: self.NEWS}  # after the twin's second push back (~2 x 350 frames in)
        return self.explore_field(game)

    def test_news_lifts_the_twin_and_once_more_gives_her_up_again(self) -> None:
        """New words heard in a scene that left the player be (May in her house) are PROGRESS: the tiles the twin sent
        the player back from are worth a try again; met ONCE more with her same words and nothing new since the news,
        they are given up again at once. 3 meetings: twice, the news, once. FAULTS: new words not progress (mutant W53):
        never tried again, 2; once is not enough after the news (mutant W54): twice more, 4."""
        game, outcome, nav, notes, lines = self.explore_with_news()
        twin = [t for _, t in game.scene_log if t == (4, 15)]
        self.assertEqual(len(twin), 3, f"{game.scene_log} {[l for l in lines if 'scene' in l or 'words' in l][-8:]}")
        self.assertTrue(any("new words heard" in line and "Oh, hello" in line for line in lines), lines[-10:])
        self.assertTrue(any("worth a try again" in line for line in lines))
        self.assertTrue(any("again after the news" in line for line in lines), lines[-10:])
        self.assertEqual(nav.scene_walls.get(nav.world.current), {(4, 15)})

    def test_fault_news_is_not_progress_the_twin_is_never_tried_again(self) -> None:
        with mock.patch.object(navigator_module.Novelty, "heard", lambda self, words, frame: False):
            game, outcome, nav, notes, lines = self.explore_with_news()
        self.assertEqual(len([t for _, t in game.scene_log if t == (4, 15)]), 2, game.scene_log)

    def test_the_words_are_progress_once(self) -> None:
        """`Novelty.heard`: new words are progress dated at the frame given (the scene's end), the same words again are
        not, no words are not."""
        world = WorldMemory()
        look = GridGame({"A": ["...."]}, ("A", (0, 0))).look()
        novelty = Novelty(world, look)
        self.assertTrue(novelty.heard("Huh? Who... Who are you?", 900))
        self.assertEqual((novelty.last, novelty.last_progress), (900, 900))
        self.assertFalse(novelty.heard("Huh? Who... Who are you?", 1500))
        self.assertFalse(novelty.heard(None, 1600))
        self.assertEqual((novelty.last, novelty.last_progress), (900, 900))

    def test_scene_words_is_the_first_page_waited_on(self) -> None:
        from ai_player.brain.navigator import scene_words

        self.assertEqual(scene_words([None, "Um, um,\num!¶If you go", "later"]), "If you go")
        self.assertEqual(scene_words(["Um, um,\num!"]), "Um, um, um!")
        self.assertIsNone(scene_words([]))
        self.assertIsNone(scene_words(["   "]))

    def test_progress_lifts_the_tiles_a_scene_sent_the_player_back_from(self) -> None:
        """Progress during the intent (a story flag: the twin lets a player WITH a Pokemon pass) makes the gap worth a
        try again: the explorer then walks through it into the field. FAULT (never lifted: mutant W48): it never does."""
        game = StoryGame({"TOWN": self.FIELD}, ("TOWN", (4, 17)), triggers={("TOWN", (4, 15)): (90, (4, 16))})
        game.events = {2500: "FLAG_RECEIVED_POKEMON"}  # after the second push back (~2 x 350 frames in), the story moves on
        game, outcome, nav, notes, lines = self.explore_field(game)
        self.assertEqual(game.scenes_run, 2, f"{game.scenes_run} scenes")
        self.assertTrue(any("worth a try again" in line for line in lines), lines[-6:])
        self.assertTrue(any(xy[1] < 15 for name, xy in game.trail), "walked through the gap once the story moved on")


class NewsGame(GridGame):
    """(the step-3.1 verifier's second round) The grid model with NEWS: from frame F on (`news`: F -> words), the next
    moment the player stands still a scene with those words plays and leaves the player where it found them (May's "Who
    are you?" in her house: no flag the eyes call a story flag, only words never heard before)."""

    news: dict = {}

    def tick(self, button: str | None, new: bool) -> None:
        due = [f for f in sorted(self.news) if f <= self.frame]
        if due and not (self.scene or self.moving or self.warp_out or self.warp_in or self.pending):
            self.scene, self.scene_text, self.push_to = 90, self.news.pop(due[0]), None
            self.scenes_run += 1
            self.scene_log.append((self.map, ("news", self.pos)))
        super().tick(button, new)


class StoryGame(GridGame):
    """(the step-3.1 verifier's round) The grid model with STORY FLAGS on every look (`Observation.progress`): `events`
    frame -> a flag set from that frame on; a trigger tile stops pushing back once a flag is set (the twin lets a player
    with a Pokemon pass)."""

    events: dict = {}

    def flags(self) -> tuple:
        return tuple((name, self.frame >= frame) for frame, name in sorted(self.events.items()))

    def attempt(self, button: str) -> None:
        if any(on for _, on in self.flags()):
            self.triggers = {}
        super().attempt(button)

    def look(self) -> Observation:
        from ai_player.eyes.observation import Progress

        progress = Progress(money=0, badges=(), dex_owned=0, dex_seen=0, owned_dex=(), flags=self.flags())
        return replace(super().look(), progress=progress)


class ApproachTests(unittest.TestCase):
    """(build step 3.1, the step-3 review's finding 8) An exit's STAND tile came from `distances`, which holds UNSEEN tiles
    too (allow_unknown), so a door's target could be a tile the AI had never seen. Every candidate the explorer offers
    must be a SEEN, walkable tile. FAULT (the stand tile not checked): a door's target is unseen."""

    #: A door (4, 1) in the top wall of a hall; the player at the hall's west end. The hall's middle (3..7, 2), the
    #: door's only stand tile (4, 2) among them, was never seen: only `distances`' optimism reaches it.
    ROOM = ["#########", "####D####", "#.......#", "#########"]

    def memory_with_unseen_stand(self):
        game = GridGame({"TOWN": self.ROOM, "IN": ["###", "#.#", "###"]}, ("TOWN", (1, 2)), crop=False,
                        warps={("TOWN", (4, 1)): ("IN", (1, 1))})
        hands, nav, world, notes, lines = rig(game)
        world.observe(game.look())
        memory = world.here()
        for xy in [(x, 2) for x in range(3, 8)]:
            del memory.tiles[xy]
        return nav, game.look(), memory

    def test_every_candidate_is_a_seen_walkable_tile(self) -> None:
        nav, look, memory = self.memory_with_unseen_stand()
        found = candidates(nav, look, WEIGHTS["Story"])
        self.assertTrue(found)
        unseen = [(c.kind, c.tile) for c in found if not memory.passable(c.tile)]
        self.assertEqual(unseen, [], "a candidate on a tile the AI never saw")
        self.assertNotIn("door", {c.kind for c in found}, "the door's only stand tile (4, 2) is unseen: not yet a target")
        for seed in range(1, 6):  # and over random memories of the explore model
            game = GridGame({"FIELD": ExploreTests.FIELD, "IN": ["###", "#.#", "###"]}, ("FIELD", (5, 6)), crop=True,
                            warps={("FIELD", (5, 5)): ("IN", (1, 1))})
            hands, nav2, world2, notes, lines = rig(game, seed=seed)
            drive(nav2.run(explore_intent(None, "Story", 600 + 97 * seed), "look around"), budget=20_000)
            mem = world2.here()
            self.assertEqual([c for c in candidates(nav2, game.look(), WEIGHTS["Story"]) if not mem.passable(c.tile)], [])

    def test_fault_the_stand_tile_not_checked_gives_an_unseen_target(self) -> None:
        nav, look, memory = self.memory_with_unseen_stand()
        with mock.patch.object(memory_module.MapMemory, "passable",
                               lambda self, xy: True if xy not in self.tiles else (self.tiles[xy].walkable)):
            found = candidates(nav, look, WEIGHTS["Story"])
        doors = [c for c in found if c.kind == "door"]
        self.assertTrue(doors and not memory.known(doors[0].tile), f"the door's target {doors} is a tile never seen")


class ExploreTests(unittest.TestCase):
    #: The explore model's field (also `ApproachTests`): a road north, tall grass, a door.
    FIELD = ["####..####", "#........#", '#..""""..#', '#..""""..#', "#........#", "#....D...#", "#........#", "##########"]

    def setup(self, personality: str, seed: int = 3):
        rows = ["####..####", "#........#", '#..""""..#', '#..""""..#', "#........#", "#....D...#", "#........#", "##########"]
        maps = {"FIELD": rows, "NORTH": ["#..#", "#..#"]}
        links = {("FIELD", "up"): ("NORTH", (-3, 2)), ("NORTH", "down"): ("FIELD", (3, -2))}
        game = GridGame(maps, ("FIELD", (5, 6)), links=links, crop=False)
        hands, nav, world, notes, lines = rig(game, seed=seed, personality=personality)
        world.observe(game.look())
        # the road north is a ROAD because a crossing of that edge was SEEN before (build step 3.1, finding 1: without
        # one, a tile past an edge is just a tile, `ShiftTests`)
        world.here().edges["up"] = -1
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
        found = candidates(nav, game.look(), WEIGHTS["Catcher"])
        self.assertTrue(any(c.kind == "frontier" for c in found), "the town has somewhere new to go")
        # (build step 3.1) while there is somewhere NEW on this map, the way just come in is no option at all (it used
        # to be one worth `Weights.back`: once roads stopped being known from the coordinates, a far frontier scored
        # below it and the AI went house -> town -> house: the step-3.1 sweep's TOWN-Catcher seed 8)
        self.assertEqual([c for c in found if c.kind == "back"], [], "the door just come out of is not a candidate")
        # with nothing new left on the map, it is one again (worth `Weights.back`: a dead end is left by its door)
        with mock.patch.object(explore_module, "ONWARD_KINDS", ()):
            back = [c for c in candidates(nav, game.look(), WEIGHTS["Catcher"]) if c.kind == "back"]
        self.assertTrue(back and "just come from" in back[0].reason, back)
        self.assertLessEqual(back[0].score, VALUE_TILES * WEIGHTS["Catcher"].back + 1.5)

    def test_not_back_to_a_floor_seen_all_of_while_the_town_has_more(self) -> None:
        """(the step-4 verifier's round) Up the house, down, out into a town too wide for one screen, and back into the house:
        the stairs lead to a floor SEEN ALL OF, the doormat to the town with things left to see; the stairs are no option
        (measured live: once a doormat counted as one way out, the stairs one step away outscored the doormat four steps away
        and the AI went up and down until the ping-pong rule: the sweep's CROP seed 1). FAULT (mutant W89: the rule off):
        the stairs are a candidate again."""
        house = ExitTests().house()
        maps = dict(house.maps)
        maps["TOWN"] = ["#" * 31, "#" + "." * 29 + "#", "####D" + "#" * 26, "#" + "." * 29 + "#", "#" + "." * 29 + "#", "#" * 31]
        game = GridGame(maps, ("UP", (2, 2)), warps=house.warps)
        hands, nav, world, notes, lines = rig(game)
        self.assertTrue(drive(nav.run(explore_intent("TOWN", "Story", 8000), "out")).startswith("done"))
        self.assertTrue(drive(nav.run(goto_intent([(4, 3)], 2000), "to the door")).startswith("done"))
        target = Target("door", (4, 3), "back in", exit=(4, 2), direction="up")
        self.assertEqual(drive(nav.use_exit(target, "back in")), "used")
        drive(nav.settle("in"))
        keys = {name: key for key, name in world.names().items()}
        self.assertEqual(world.current, keys["DOWN"])
        self.assertGreater(world.promise(keys["TOWN"]), 0, "the town has things left to see")
        self.assertEqual(world.promise(keys["UP"]), 0, "the upper floor is seen all of")

        def ways(found):
            return sorted((t.kind, t.exit, t.reason.split(",")[-1].strip()) for t in found if t.kind == "back")

        found = candidates(nav, game.look(), WEIGHTS["Story"])
        self.assertTrue(any(t.kind == "back" and t.exit in ((8, 4), (9, 4)) for t in found), ways(found))
        self.assertFalse(any(t.exit == (8, 1) for t in found), f"the stairs to a floor seen all of: {ways(found)}")
        with mock.patch.object(explore_module, "not_back_to_seen_all", lambda found: found):
            faulty = candidates(nav, game.look(), WEIGHTS["Story"])
        self.assertTrue(any(t.exit == (8, 1) for t in faulty), ways(faulty))

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
                # (build step 3.1, the step-3 review's finding 9) BOTH ratios: the back-and-forth spins (the criterion)
                # and every press that did not move the player; the pre-empted presses are exactly the interrupted
                # ones that did not move it (at_once: none; else: all)
                self.assertEqual((m["reversals"], m["in_place"]), (spin_count(path), m["not_moved"]))
                self.assertEqual(m["spins"], m["reversals"] + m["in_place"])
                self.assertEqual(m["preempted"], m["interrupted"] - moved_in, m)
                self.assertEqual(m["non_moving"], m["in_place"] + m["preempted"])
                self.assertEqual(m["strict_ratio"], round(m["non_moving"] / m["attempts"], 6))
                self.assertEqual(m["attempts"] - m["non_moving"], m["steps"], "every press moved the player or did not")


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
