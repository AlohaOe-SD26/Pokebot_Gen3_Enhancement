"""LIVE PROOF of AI-player build step 3 (the WORLD MODEL and the AI's OWN NAVIGATOR): the AI walks out of the
player's house, through Littleroot, up Route 101 to Oldale, roams a grass patch and flees what it meets, ITSELF,
through the real launcher, under the purity instrument; plus the fault arms that show each rule carries weight.

    py -3.12 ai_player/gates/live_step3.py [--arms HOUSE,TOWN,ROUTE,ROAM,CROP,STUCK,BUMP,BUMPR,TRN,XP,XPR] [--seed 3]

Each launcher arm runs `py -3.12 -m ai_player run` (the gate first, the purity instrument, the verdict file) with a
WORLD brain (`AI_PLAYER_BRAIN=explore|roam|goto`, `ai_player/mode.py` HandsBrain, `ai_player/brain/`) and the pinned
seed 3. The grade has four parts, each check quoting both values:
  1. PURITY (`live_step2.check_purity`): the gate passed on the real package; the verdict file CLEAN; `ai_presses` == 2 x
     the pad's own presses and > 0; the pad's frames == the instrument's `real_frames`; every breach counter 0
     (`foreign_*`, `ai_writes`, `ai_loads`, `ai_bot_calls`: the bot's pathfinder never ran); the run ended by itself.
  2. THE GAME, by a SECOND PATH from the state the run LEFT (`gates/hands_harness.py truth`: save block 1's map and
     `pos`, its flags and the intro's variable, the game's OWN step and battle counters `gameStats[]` XOR the key, the
     party by the framework's `get_party()`), never the AI's eyes; the same on the fixture BEFORE the run; and the state
     graded is asserted to be this run's (written after it started, its frame the start's + the run's real frames, its
     md5 not the fixture's).
  3. THE PERCEPTION RULE (design draft §10.7, the crop): the AI's own memory (`<run_dir>/world.jsonl`, its last snapshot)
     knows ONLY tiles that were inside the 15 x 11 window of the tile it stood on when it first saw them; every target
     it chose (the action log's `decide` records) was such a tile.
  4. THE HANDS (`live_step2.check_gates`' rules, for walking): every press names its gate; every A is a text WAIT, a MENU
     confirm (incl. the battle's RUN) or a TALK by its look; every WALKING hold (gate "walk ...", "keep walking ...",
     "use the ...", "roam ...") is pressed on a look of the overworld with nothing waiting and no menu; no idle stretch
     under the catch-all reason; every walking hold is `CHUNK_FRAMES` long, every other press 3-7 frames.
  5. (since the step-3 verifier) THE GAME'S ANSWER to where the player stands (`gates/game_answer.py`), every arm but
     TRN: from the state the run left, holding a direction makes the game's own step counter and the map it LOADS do
     what the ROM's layout at save block 1's claimed tile predicts (a different KIND of evidence from the `pos` the eyes
     read too); the same probe claiming a neighbouring tile it rules out must DISAGREE (its fault-test). A tile with no
     clean line (people beside it) is INCONCLUSIVE and says so; (since the verifier's second round) it then FAILS
     unless the game is LOCKED and the ROM's ARRIVAL from the last warp the AI used is the claimed tile (STUCK).

PRE-REGISTERED PREDICTIONS (2026-10-08, written before the graded runs, from in-process development runs of the same
code on the same starts: `gates/hands_harness.py`, seed 3; the fixtures from `gates/make_step3_fixtures.py`):
HOUSE  `house_2f_clockset.ss1` (the player's room, clock set, VAR_LITTLEROOT_INTRO_STATE 6), explore to LITTLEROOT_TOWN,
       Story. PREDICT "explore: done: explore to LITTLEROOT_TOWN"; the stairs (7,1) used pressing up (2F -> 1F, a warp by
       the AI), the TV scene on 1F read through (A only on its waits), the mat used pressing down (1F -> LITTLEROOT_TOWN);
       truth map [1,1] -> [0,9], VAR 6 -> 7 (the scene played), steps 9 -> 29; dev 3,344 frames, 52 presses, 18 steps.
TOWN   `pokedex_done.ss1` (Birch's lab, Mudkip), explore to ROUTE101, Story, knowing NOTHING. PREDICT done; the lab's mat
       used pressing down, Littleroot explored from the frontier it saw, Mom's Running Shoes scene read through
       (SYS_B_DASH False -> True), the north road walked onto: a CONNECTION Littleroot (x, 0) up -> Route 101 (x, 19);
       truth map [1,4] -> [0,16]; dev 4,961 frames, 43 steps, 7 decisions, steps 576 -> 621.
ROUTE  `route101_south.ss1` + its memory `route101_south.world.jsonl` (the TOWN walk, played by the AI itself), explore to
       OLDALE_TOWN, Story. PREDICT done; the memory LOADED (3 maps); the road back south known as the way to a visited
       map (not taken); a CONNECTION Route 101 (x, 0) up -> Oldale (x, 19); truth map [0,16] -> [0,10]; every wild battle
       met FLED (the game's wild-battle count rises by exactly the AI's fled count: dev 10 -> 10, none met), the party's
       HP unchanged; dev 975 frames, 49 steps.
ROAM   `route101_south.ss1`, roam 150 training steps, Catcher, knowing nothing. PREDICT "roam: roamed: ..."; 150 training
       steps, spin ratio < 2% (dev 0.007: 1 spin), distinct tiles >= 40 (dev 84), >= 1 wild encounter, every one fled (dev
       9); the game's own counters: steps rise by >= 150 (dev 621 -> 779), wild battles by exactly the AI's encounters
       (dev 10 -> 19); the end tile by save block 1 == the AI's last path tile; truth map still [0,16].
CROP   FAULT `AI_PLAYER_FAULT_NO_CROP=1` (the eyes show the WHOLE map), the TOWN start and goal. PREDICT done, purity CLEAN;
       the HARM to the perception rule, visible in the memory: tiles known from OUTSIDE every window (dev: most of 1,946);
       the first target on LITTLEROOT_TOWN a ROAD off the screen (dev: (10,-1) from (7,16)); fewer decisions and fewer
       steps than TOWN (dev 2 and 26 vs 7 and 43): a beeline.
STUCK  `clock_room.ss1` (the clock NOT set), explore to LITTLEROOT_TOWN. Going down, Mom sends the player back up
       (`LittlerootTown_BrendansHouse_1F_EventScript_GoUpstairsToSetClock`): an unreachable goal. PREDICT "explore: stuck:
       ping-pong: the warp ... used 3 times ... with nothing new since its second use", well within the budget (dev 1,519
       of 12,000 frames), the stairs used by the AI exactly 3 times and the scene's warps back recorded as the scene's;
       truth VAR_LITTLEROOT_INTRO_STATE still 5, FLAG_SET_WALL_CLOCK still False.
BUMP   `house_2f_clockset.ss1`, goto (0,4) then (2,4) then (0,4). The tile (1,4) is IMPASSABLE_SOUTH_AND_NORTH with collision
       0: the eyes call it walkable. PREDICT done; ONE bump, moving down from (1,3) into (1,4), learned blocked; afterwards
       no press toward (1,4) again: errand 2, (0,4) -> (2,4), whose only 2-step way is through (1,4), takes 4 steps round
       it; the truth of WHY by a second path (the ROM layout read by the framework's MapLocation: behaviour and collision
       at (1,4)); end tile [0,4] by save block 1; dev 371 frames, 15 steps.
BUMPR  REVERT of BUMP: a COPY of the package whose `WorldMemory.learn_bump` remembers nothing, in-process
       (`hands_harness.py` from the copy). PREDICT the HARM: the same tile bumped again and again (>= 10 BUMP lines on
       (1,4)), errand 1 never done, the intent "stuck: nothing new ..." within its budget.
TRN    `trainer_battle_r116.ss1` (a trainer battle on Route 116 just begun): a trainer battle is out of scope for step 3.
       PREDICT "explore: stuck: a trainer battle: out of scope ..." with NO press on the action menu (dev: 1 A, on the
       battle's opening text wait), 596 frames.
Evidence: `ai_player/evidence/<date>-step3-<ARM>.txt`. Exit 0 only if every arm passed and no emulator is left.

AFTER THE FIRST GRADED RUN (2026-10-08, said here rather than folded into the predictions above): every arm passed its
pre-registered checks except TRN, on two checks of the GRADER, not of the AI: `check_hands` demanded walking holds of
an arm that by design never walks (the battle is on screen from the first frame). The check now takes `walking=False`
for TRN (no walking hold at all is then REQUIRED). BUMPR measured 94 bumps into (1,4) and gave up after 3,123 frames.
The memory's novelty counter now also counts the tiles absorbed when the way back is inferred at an arrival (they were
learned uncounted); it moved the CROP arm's count of learned tiles (1,946 -> 3,136) and no trajectory (every arm's
frames and presses equal its dev run's: HOUSE 3,344 / 52, TOWN 4,961 / 101, ROUTE 975 / 99, ROAM 12,210 / 375, CROP
4,640 / 71, STUCK 1,519 / 40, BUMP 371 / 33).
THEN A SEED SWEEP (in-process, 10 seeds per plan, `evidence/<date>-step3-RATE.txt`) found two explorer flaws and a
roaming one, fixed before the final graded run (README "Found while building"): a lab -> town -> lab ping-pong (Catcher
seed 1, Trainer seed 6: the way just come in is now worth only `Weights.back` while this map has something to see, and
an exclusion belongs to its map), and roaming's only reversals at the corner where Route 101's boy wanders (it now waits
for a person in its only way on, and keeps 2 tiles from people; the worst seed was 3 spins in 151). That moved arm
ROAM's trajectory: dev seed 3 now 16,646 frames, 399 presses, 78 distinct tiles, 1 spin, 13 wild battles fled (game
counter 10 -> 23), steps 621 -> 779; its pass criteria are unchanged. The other arms' trajectories did not move.

AFTER THE STEP-3 VERIFIER (2026-10-08, its five weak proofs; PRE-REGISTERED before this round's graded run, from
in-process development runs of the same code on the same starts: `gates/rate_step3.py` seeds 1-10 and, for seed 3, a
`hands_harness.py --save-end` run of each arm with `gates/game_answer.py` on its end state):
  * the WHIM AMONG EQUALS (`brain/explore.py` pick) moves the explorer's trajectories; HOUSE and TOWN now accept map
    changes between the first and the last (a seed may look into a room or a house); their other criteria stand.
    HOUSE seed 3 is unchanged: 3,344 frames, 52 presses, targets 2F frontier (5,7), the stairs (7,2), the mat (8,7).
    TOWN seed 3: PREDICT 4,969 frames, 92 presses, 37 steps, targets lab frontier (6,10), the door (6,11), town
    frontiers (14,18), (13,11), (12,6), (10,1), the road (11,-2). ROUTE seed 3: PREDICT 2,083 frames, 108 presses, 51
    steps, ONE wild battle met and fled (the game's count +1: the flee is now non-vacuous on this arm too), 6 targets.
    CROP seed 3: PREDICT 4,640 frames, 79 presses, its first town target the road (11,-1) from (7,17). STUCK seed 3:
    unchanged (1,519 frames, 40 presses). BUMP, BUMPR, TRN do not choose targets: unchanged.
  * CROP: the walk's length is no longer a check (a note: an honest TOWN seed can be as short); the first town target
    is checked NOT SEEN (not inside the window of the tile it was first seen from), not "not in the window now" (the
    sweep's honest TOWN seeds 4 and 6 chose a frontier seen from the lab's door, not in the window of the tile they
    stood on). `rate_step3.py` CROP-SEP: both discriminators over 10 TOWN and 10 CROP seeds.
  * ROAM: PREDICT the same trajectory (roaming does not use the explorer's choice): 16,646 frames, 399 presses; 150
    training steps, 163 presses = ATTEMPTS, 13 interrupted by a battle (pre-empted: they did not move the player), 1
    spin: 1/150 = 0.0067 over the training steps; the same re-derived from the digests; the game's step counter 621 ->
    779, + 1 step in flight == 9 walk moves + 150.
  * THE GAME'S ANSWER: PREDICT agree on HOUSE (Down 3 steps to a wall, Left 5 to the map's edge; rules out 5 of the 5
    tiles beside it the player could stand on), TOWN and CROP (Down: 1 step and the map becomes LITTLEROOT_TOWN; Left /
    Right: 1 step to a wall), ROUTE (Down: 1 step into ROUTE101; Left 7 to a wall), ROAM (Down 1, Right 3 to a wall;
    Up meets a wild battle and is skipped; rules out all 8), BUMP (Down 3 to the map's edge, Left 0); each fault claim
    disagrees. STUCK: INCONCLUSIVE (Mom beside the player, the stairs above), the loaded header the 1F's.

AFTER THE STEP-3 VERIFIER'S SECOND ROUND (2026-10-08, its five weak proofs; PRE-REGISTERED before this round's graded
run, from in-process development runs of the same code on the same starts, seed 3: `hands_harness.py` for XP, a COPY
for XPR, `game_answer.py` on STUCK's and XP's end states). The evidence header now carries `predictions:` (sha256 of
this docstring, read at the start of the run: `predictions_ref`). No trajectory of the arms above moves (the new
novelty line is told, it takes no frame): HOUSE 3,344 / 52, TOWN 4,969 / 92, ROUTE 2,083 / 108, ROAM 16,646 / 399,
CROP 4,640 / 79, STUCK 1,519 / 40, BUMP 371 / 33, TRN 596 frames.
  * CROP: TRUTH (save block 1) map [1,4] (the lab) -> [0,16] ROUTE101, now a check (it rested on the outcome string).
  * STUCK: an INCONCLUSIVE answer no longer passes on the loaded header alone. PREDICT: no walking line (as before); LOCKED:
    each direction held 120 frames from the state left counts 0 steps, the tile and the map unchanged (Mom's scene:
    `lockall`, a `msgbox` waiting); THE ARRIVAL by the ROM: the warp the AI used last, [1,1] (7,1) (the 2F stairs:
    `STUCK_WARP`), lands on [1,0] (8,2), a Non-Animated Door, the exit step (0,1) leaves the player on (8,3) == save block
    1's claim; the AI pressed nothing from that arrival on; the fault claim (7,3) disagrees (by the arrival, and its
    own walking trial: the controls are locked).
  * ROAM: the 13 presses that did not move the player are PRE-EMPTED: the battle on screen 16 pad frames after each (the
    press's own two chunks), no move and NO TURN before it (6 of the 13 pressed away from the way the player faced), 13
    distinct battles, 0 presses that left the player standing without one. The strictest reading (every press that did
    not move the player a spin), reported as a NOTE: 14/163 = 0.0859; the criterion stays 1/150 (the design's spin).
  * XP (new): `route101_xp.ss1` (`make_step3_fixtures.py --only xp`: the AI's own errands, then test-side presses to a
    SECOND wild battle, Wurmple L2, saved the frame its HP reached 0; the first battle levelled the Mudkip up, a stats box
    the AI cannot read yet: step 4), goto 120 errands between (6,15) and (7,15) with its own memory loaded. PREDICT
    "goto: stuck: nothing new ... for 3000 frames, the last at f71924: experience gained (1 Pokemon)", 3,600 frames, 137
    presses; ONE novelty line, "experience gained (PID 550a9be6: 441 -> 456)", the clock f71324 -> f71924 (600 frames
    on, once "battle: the battle ended"); the framework's get_party: PID 550a9be6 441 -> 456; wild battles 12 -> 12;
    291 tiles learned at the start and the end; the end tile (7,15) by save block 1 and the game's answer (Up 8 steps to
    a ledge, Right 4 to a wall).
  * XPR (new): REVERT of XP, in-process from a COPY whose `Novelty.update` ignores experience. PREDICT "goto: stuck:
    nothing new ... for 3032 frames, the last at f71324: none", 3,032 frames, 113 presses, no novelty line, the game's
    experience 441 -> 456 all the same; the A/B: 3,032 frames against XP's 3,600 (the gain moved the verdict 568 later).
  * NOT FIXABLE HERE: a proof that the predictions were written before a first look at a graded run needs a commit made
    before it, and this round's worker may make none. `predictions:` shows the predictions a run read; a re-run by
    someone else after reading them (the step-3 verifier's) is the replication.
AFTER THIS ROUND'S FIRST GRADED RUN (2026-10-08, `predictions: sha256:e30501a3689e2b1d`; said here, not folded into
the above): every arm met its predictions, frames and presses included, except ONE check of STUCK, a fault-test of the
INSTRUMENT: the probe claiming (7, 3) had one clean line, "Up: 0 steps, then a wall", and on a state where a scene
holds the controls the game counted 0 steps, so its walking answer AGREED ("by walking True (want False, not True)").
A prediction of no step cannot tell a player before a wall from one who cannot move: `game_answer.py`
`walking_agrees` now also requires a trial that predicts a STEP (unit test `test_a_walking_answer_needs_a_step`, mutant
W29). Every other arm's walking answer has a moving trial (HOUSE Down 3, TOWN and CROP Down 1, ROUTE Down 1, ROAM Down
1 / Right 3, BUMP Down 3, XP Up 8 / Right 4): PREDICT no other change; STUCK's fault claim now "by walking False".
THE SECOND GRADED RUN (`predictions: sha256:0e3682c982d6d2d4`): all 11 arms PASS, every frame and press count as
predicted (HOUSE 3,344 / 52, TOWN 4,969 / 92, ROUTE 2,083 / 108, ROAM 16,646 / 399, CROP 4,640 / 79, STUCK 1,519 / 40,
BUMP 371 / 33, TRN 596 / 1, XP 3,600 / 137, XPR 3,032 / 113, BUMPR 3,123 / 386), STUCK's fault claim "by the arrival
False, by walking False". This docstring was then edited only to say so and to correct grading part 5's sentence on
an INCONCLUSIVE answer; the final run reads the edited text (its own `predictions:` digest) and predicts the same.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.brain.navigator import CHUNK_FRAMES  # noqa: E402
from ai_player.gates.live_step2 import (  # noqa: E402
    check_purity, classify_a, clean_env, make_copy, run_json, truth_of,
)
from ai_player.gates.provenance import provenance as tree_provenance  # noqa: E402
from ai_player.hands.dialogue import GENERIC_BUSY  # noqa: E402
from ai_player.host import launcher  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_BRAIN, ENV_FAULT_NO_CROP, ENV_GOAL_MAP, ENV_GOTO, ENV_PERSONALITY, ENV_ROAM_STEPS, ENV_SEED, ENV_WORLD,
)
from ai_player.world.memory import WorldMemory, in_window  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
GATES = Path(__file__).resolve().parent
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
EVIDENCE_TAG = "step3"
HARNESS = GATES / "hands_harness.py"
#: The step-3 verifier's weak proof 3: the GAME's answer to where the player stands, by its behaviour.
GAME_ANSWER = GATES / "game_answer.py"
#: Arms that end where the player cannot walk (TRN: in a battle): no behavioural answer.
NO_ANSWER = ("TRN",)
PROFILE = "ai-step3-world"
SEED = 3
FRAME_SLACK = 5
SELFTEST_LINE = "[SELFTEST] not run"
#: (path, md5) PINNED.
FIXTURES: dict[str, tuple[Path, str]] = {
    "house_2f_clockset.ss1": (GATES / "fixtures" / "house_2f_clockset.ss1", "2cc0b61450870d34646f7583bfd0c787"),
    "pokedex_done.ss1": (SAVES / "pokedex_done.ss1", "380fba7a4bf4afdf2fc9a0ad158de29e"),
    "route101_south.ss1": (GATES / "fixtures" / "route101_south.ss1", "81bf318a1532c5364f60064530f9984b"),
    "route101_south.world.jsonl": (GATES / "fixtures" / "route101_south.world.jsonl", "dae9c609f1b55ad76fd7f310d9cc35f5"),
    "clock_room.ss1": (GATES / "fixtures" / "clock_room.ss1", "5d1d0ce0974470bf11040fc39f832041"),
    "trainer_battle_r116.ss1": (GATES / "fixtures" / "trainer_battle_r116.ss1", "f55f3c2ec6efb9fb20363e8ca92b73ba"),
    "route101_xp.ss1": (GATES / "fixtures" / "route101_xp.ss1", "ac5bc2645ad980386be12d2b4a8704e6"),
    "route101_xp.world.jsonl": (GATES / "fixtures" / "route101_xp.world.jsonl", "ce8287a37f03394b19fcb3e28f964feb"),
}
#: Maps by (group, number) (`data/maps/map_groups.json`; the truth reads save block 1's location).
LITTLEROOT, ROUTE101, OLDALE, LAB, HOUSE_1F, HOUSE_2F = [0, 9], [0, 16], [0, 10], [1, 4], [1, 0], [1, 1]
#: BUMP's errands and its learned tile (2F of the player's house; `data/maps/LittlerootTown_BrendansHouse_2F`).
BUMP_ERRANDS, BUMP_TILE = "0,4;2,4;0,4", (1, 4)
#: The prefixes of a WALKING gate (`brain/navigator.py`, `skills/roam_train.py`).
WALK_GATES = ("walk ", "keep walking ", "use the ", "roam ")
#: BUMPR: the bump is told and NOT remembered (`world/memory.py` WorldMemory.learn_bump).
BUMPR_MUTATION = ("world/memory.py", "        memory.bumped[tile] = info\n",
                  "        pass  # MUTANT BUMPR: the bump is not remembered\n")
#: (the step-3 verifier's second round) STUCK: the warp the AI used last, PRE-REGISTERED (the 2F stairs), whose ROM
#: arrival `gates/game_answer.py --after-warp` predicts; the arms answered that way.
STUCK_WARP = ([1, 1], [7, 1])
ARRIVAL_ARMS = ("STUCK",)
#: XP: errands back and forth between two KNOWN floor tiles beside the battle's grass (`make_step3_fixtures.py` xp:
#: the AI's own memory saw their windows), more than the novelty window can hold, so the intent ends "stuck: nothing
#: new" and its CLOCK is the subject; XPR: experience gained is not novelty (`brain/navigator.py` Novelty.update).
XP_ERRANDS = ";".join(["6,15", "7,15"] * 60)
XPR_MUTATION = ("brain/navigator.py", "            if gained:\n                new.append(f\"experience gained ({len(gained)} Pokemon)\")\n",
                "            if False:  # MUTANT XPR: experience gained is not novelty\n"
                "                new.append(f\"experience gained ({len(gained)} Pokemon)\")\n")
#: The navigator's novelty line (`brain/navigator.py` Navigator.run) and its stuck reason.
NOVELTY_PREFIX = "novelty at f"
STUCK_NOTHING_NEW = re.compile(r"stuck: nothing new \(.*?\) for (\d+) frames, the last at f(\d+): (.*?) \(\d+ steps")


@dataclass
class Arm:
    name: str
    title: str
    brain: str
    fixture: str
    frames: int
    wall: float
    env: dict[str, str] = field(default_factory=dict)
    kind: str = "launcher"  # or "harness" (in-process, from a COPY of the package)
    args: tuple[str, ...] = ()
    mutations: tuple = ()
    doc: str = ""


@dataclass
class Run:
    arm: Arm
    command: list[str] = field(default_factory=list)
    exit_code: int = -1
    elapsed: float = 0.0
    started: float = 0.0
    stdout: str = ""
    run_dir: Path | None = None
    verdict: dict | None = None
    records: list[dict] = field(default_factory=list)
    ai_log: str = ""
    before: dict | None = None
    after: dict | None = None
    state_mtime: float | None = None
    world: dict | None = None
    harness: dict | None = None
    answer: dict | None = None  # gates/game_answer.py on the state left, for save block 1's claim
    answer_fault: dict | None = None  # the same probe claiming a neighbouring tile it rules out: must disagree
    checks: list[tuple[bool, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)

    @property
    def outcome(self) -> str:
        return ((self.verdict or {}).get("facts") or {}).get("exit_reason") or (self.harness or {}).get("reason") or ""

    @property
    def presses(self) -> list[dict]:
        return [r for r in self.records if str(r.get("action", "")).startswith(("press ", "hold "))]


STORY = {ENV_PERSONALITY: "Story"}
ARMS: list[Arm] = [
    Arm("HOUSE", "leave the player's house: down the stairs, out the door into Littleroot", "explore", "house_2f_clockset.ss1",
        12000, 600.0, {ENV_GOAL_MAP: "LITTLEROOT_TOWN", **STORY}, doc="gates/make_step3_fixtures.py (house_2f_clockset.build.json)"),
    Arm("TOWN", "from Birch's lab, knowing nothing of Littleroot, explore to the road to Route 101", "explore", "pokedex_done.ss1",
        20000, 900.0, {ENV_GOAL_MAP: "ROUTE101", **STORY}, doc="tools/story-dev/saves/pokedex_done.ss1 (Birch's lab, the Pokedex got)"),
    Arm("ROUTE", "explore Route 101 to Oldale Town (a map connection), fleeing any wild battle, from the TOWN walk's memory",
        "explore", "route101_south.ss1", 24000, 900.0,
        {ENV_GOAL_MAP: "OLDALE_TOWN", ENV_WORLD: str(FIXTURES["route101_south.world.jsonl"][0]), **STORY},
        doc="gates/make_step3_fixtures.py (route101_south.build.json): the AI's own TOWN walk, its state and its memory"),
    Arm("ROAM", "roam-train 150 steps through Route 101's grass, fleeing every wild battle", "roam", "route101_south.ss1",
        40000, 1200.0, {ENV_ROAM_STEPS: "150", ENV_PERSONALITY: "Catcher"}, doc="as ROUTE (the state only: it knows nothing)"),
    Arm("CROP", "FAULT the crop off (the eyes show the whole map): the TOWN start and goal", "explore", "pokedex_done.ss1", 20000,
        900.0, {ENV_GOAL_MAP: "ROUTE101", ENV_FAULT_NO_CROP: "1", **STORY}, doc="as TOWN"),
    Arm("STUCK", "an unreachable goal: out of the house with the clock not set (Mom sends the player back up)", "explore",
        "clock_room.ss1", 12000, 600.0, {ENV_GOAL_MAP: "LITTLEROOT_TOWN", **STORY},
        doc="gates/make_clock_fixture.py (clock_room.build.json): VAR_LITTLEROOT_INTRO_STATE 5"),
    Arm("BUMP", "errands in the player's room across a tile the eyes call walkable: bumped once, then avoided", "goto",
        "house_2f_clockset.ss1", 6000, 600.0, {ENV_GOTO: BUMP_ERRANDS, **STORY}, doc="as HOUSE"),
    Arm("BUMPR", "REVERT of BUMP: bump learning off in a COPY: the same tile bumped again and again", "goto",
        "house_2f_clockset.ss1", 6000, 600.0, kind="harness", args=("--goto", BUMP_ERRANDS, "--personality", "Story"),
        mutations=(BUMPR_MUTATION,), doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)"),
    Arm("TRN", "a trainer battle (out of scope for step 3): the reason, no press on the battle's menu", "explore",
        "trainer_battle_r116.ss1", 6000, 600.0, {ENV_GOAL_MAP: "OLDALE_TOWN", **STORY},
        doc="gates/make_trainer_fixture.py: a trainer battle on Route 116 just begun"),
    Arm("XP", "a wild battle won (the experience not yet given), then errands over KNOWN tiles: the experience is the intent's "
        "only novelty, and it moves the intent's clock", "goto", "route101_xp.ss1", 8000, 600.0,
        {ENV_GOTO: XP_ERRANDS, ENV_WORLD: str(FIXTURES["route101_xp.world.jsonl"][0]), **STORY},
        doc="gates/make_step3_fixtures.py --only xp (route101_xp.build.json): the AI's own errands, then test-side presses "
            "to a second wild battle whose foe's HP just reached 0"),
    Arm("XPR", "REVERT of XP: experience is not novelty, in a COPY: no novelty line, the clock never moves", "goto",
        "route101_xp.ss1", 8000, 600.0, kind="harness",
        args=("--goto", XP_ERRANDS, "--personality", "Story", "--world-in", str(FIXTURES["route101_xp.world.jsonl"][0])),
        mutations=(XPR_MUTATION,), doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)"),
]


# ---------------------------------------------------------------------- running
def run_arm(arm: Arm, build_root: Path) -> Run:
    run = Run(arm)
    profile_dir, _ = launcher.ensure_profile(build_root, PROFILE)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {PROFILE} is not ai_player-owned; refusing to touch it")
    launcher.force_http_off(profile_dir)
    cheats = profile_dir / "game_cheats.yml"
    if cheats.exists():
        cheats.unlink()
    run.before, raw = truth_of(FIXTURES[arm.fixture][0])
    if run.before is None:
        run.notes.append(f"truth of the fixture failed: {raw[-1500:]}")
    run.run_dir = profile_dir / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    run.command = [sys.executable, "-m", "ai_player", "run", "--profile", PROFILE, "--frames", str(arm.frames),
                   "--wall-seconds", f"{arm.wall:g}", "--build-root", str(build_root), "--run-dir", str(run.run_dir),
                   "--state", str(FIXTURES[arm.fixture][0])]
    env = clean_env({ENV_BRAIN: arm.brain, ENV_SEED: str(SEED), **arm.env})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    run.started = time.time()
    began = time.monotonic()
    proc = subprocess.Popen(run.command, cwd=str(REPO), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, creationflags=flags)
    try:
        raw_out, _ = proc.communicate(timeout=arm.wall + 240)
    except subprocess.TimeoutExpired:
        launcher.kill_tree(proc)
        raw_out, _ = proc.communicate()
        raw_out = (raw_out or b"") + b"\n[DRIVER] the run overran the driver's own wall clock; process tree killed\n"
    run.elapsed = time.monotonic() - began
    run.exit_code = proc.returncode if proc.returncode is not None else -9
    run.stdout = raw_out.decode("utf-8", errors="replace")
    run.verdict = launcher.read_verdict(run.run_dir)
    actions = run.run_dir / "actions.jsonl"
    if actions.is_file():
        run.records = [json.loads(line) for line in actions.read_text(encoding="utf-8").splitlines() if line.strip()]
    log = run.run_dir / "ai_player.log"
    if log.is_file():
        run.ai_log = log.read_text(encoding="utf-8", errors="replace")
    run.world = last_world(run.run_dir / "world.jsonl")
    state = profile_dir / launcher.STATE_FILE
    if state.is_file():
        run.state_mtime = state.stat().st_mtime
        run.after, raw = truth_of(state)
        if run.after is None:
            run.notes.append(f"truth of the state left behind failed: {raw[-1500:]}")
        elif arm.name not in NO_ANSWER:
            warp = last_ai_warp(run) if arm.name in ARRIVAL_ARMS else None
            run.answer, run.answer_fault = game_answer(state, run.after, warp)
    return run


def last_ai_warp(run: Run) -> tuple[list[int], list[int]] | None:
    """The warp the AI used LAST, by its own memory (map key "g:n", the warp tile): what `game_answer.py --after-warp`
    is asked about (the grader also checks it is the pre-registered `STUCK_WARP`)."""
    used = [t for t in transitions(run) if t[3] == "warp" and t[4] == "ai" and t[5] is not None]
    if not used:
        return None
    group, number = (int(v) for v in str(used[-1][1]).split(":"))
    return [group, number], [int(v) for v in used[-1][5]]


def game_answer(state: Path, truth: dict, after_warp: tuple[list[int], list[int]] | None = None) -> tuple[dict, dict | None]:
    """`gates/game_answer.py` on the state a run left, for save block 1's claim (map, pos); then, as its FAULT-TEST
    (CLAUDE.md rule 6), the same probe claiming the first neighbouring tile it rules out, which must disagree.
    `after_warp` (map, tile): also ask where the ROM says that warp leaves the player (`--after-warp`)."""

    def ask(xy) -> dict:
        command = [sys.executable, str(GAME_ANSWER), str(state), *(str(v) for v in truth["map"]), *(str(v) for v in xy)]
        if after_warp is not None:
            command += ["--after-warp", *(str(v) for v in after_warp[0]), *(str(v) for v in after_warp[1])]
        data, raw = run_json(command, "ANSWER", clean_env({}), 300)
        return data if data is not None else {"error": raw[-1500:]}

    answer = ask(truth["pos"])
    wrong = (answer.get("ruled_out") or [None])[0]
    return answer, (ask(wrong) if wrong is not None else None)


def run_harness_arm(arm: Arm) -> Run:
    """`gates/hands_harness.py` once, from a COPY of the package with the arm's mutations (in-process: the skills' code)."""
    run = Run(arm)
    root = make_copy(arm.mutations)
    run.run_dir = Path(tempfile.mkdtemp(prefix=f"ai_step3_{arm.name}_"))
    run.command = [sys.executable, str(root / "ai_player" / "gates" / HARNESS.name), arm.brain, "--state",
                   str(FIXTURES[arm.fixture][0]), "--seed", str(SEED), "--frames", str(arm.frames), *arm.args,
                   "--run-dir", str(run.run_dir)]
    run.started = time.time()
    began = time.monotonic()
    try:
        run.harness, raw = run_json(run.command, "HANDS", clean_env({launcher.ENV_BUILD_ROOT: str(REPO / "sandbox-pokebot")}), arm.wall)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if run.harness is None:
        run.notes.append(f"the harness printed no HANDS line: {raw[-2000:]}")
    actions = run.run_dir / "actions.jsonl"
    if actions.is_file():
        run.records = [json.loads(line) for line in actions.read_text(encoding="utf-8").splitlines() if line.strip()]
    run.world = last_world(run.run_dir / "world.jsonl")
    run.elapsed = time.monotonic() - began
    run.exit_code = 0 if run.harness is not None else 1
    return run


def last_world(path: Path) -> dict | None:
    if not path.is_file():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(lines[-1]) if lines else None


# ---------------------------------------------------------------------- shared checks
def check_after_is_this_run(run: Run) -> None:
    """The state graded is the one THIS run wrote (as `live_step2.check_after_is_this_run`, for this driver's fixtures)."""
    after = run.after or {}
    before_md5 = FIXTURES[run.arm.fixture][1]
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    start_frame = (run.before or {}).get("frame") or 0
    frame = after.get("frame")
    written = run.state_mtime is not None and run.state_mtime >= run.started - 1.0
    near = isinstance(frame, int) and frames > 0 and abs(frame - (start_frame + frames)) <= FRAME_SLACK
    run.check(bool(after) and written and near and after.get("state_md5") != before_md5,
              f"the state graded is the one THIS run wrote: written "
              f"{'%.1fs after the run started' % (run.state_mtime - run.started) if run.state_mtime else 'NEVER'}; frame {frame} "
              f"== start {start_frame} + {frames} real frames (+-{FRAME_SLACK}); md5 {after.get('state_md5')} (fixture {before_md5})")


def selftest_after_check() -> list[str]:
    """FAULT-TEST of `check_after_is_this_run` on synthetic runs (CLAUDE.md rule 6): its own state passes; a stale one,
    a frame off by 3000, no file and the fixture's own bytes fail."""
    arm = ARMS[0]
    md5 = FIXTURES[arm.fixture][1]

    def verdict(mtime, frame, state_md5) -> bool:
        run = Run(arm, started=1000.0, state_mtime=mtime, verdict={"counters": {"real_frames": 3344}},
                  before={"frame": 15268}, after=None if frame is None else {"frame": frame, "state_md5": state_md5})
        check_after_is_this_run(run)
        return run.passed

    cases = [("its own state", verdict(1500.0, 18612, "abc"), True),
             ("a stale state (mtime before the start)", verdict(900.0, 18612, "abc"), False),
             ("a frame +3000", verdict(1500.0, 21612, "abc"), False),
             ("no state file", verdict(None, None, "abc"), False),
             ("the fixture's own bytes", verdict(1500.0, 18612, md5), False)]
    return [f"{name}: passed={got}, want {want}" for name, got, want in cases if got != want]


def memory_of(run: Run) -> WorldMemory | None:
    return WorldMemory.from_dict(run.world) if run.world else None


def check_crop(run: Run, expect_inside: bool = True) -> int:
    """THE PERCEPTION RULE on the AI's own memory: every known tile lay inside the window of the tile it was first seen
    from. Returns how many did not."""
    world = memory_of(run)
    if world is None:
        run.check(False, "the AI's memory (world.jsonl) was written")
        return -1
    tiles = [(memory.const or key, xy, fact.seen_from) for key, memory in world.maps.items() for xy, fact in memory.tiles.items()]
    outside = [(name, xy, frm) for name, xy, frm in tiles if not in_window(frm, xy)]
    if expect_inside:
        run.check(bool(tiles) and not outside,
                  f"THE CROP, on the AI's own memory: all {len(tiles)} known tiles of {len(world.maps)} maps lie inside the 15 x 11 "
                  f"window of the tile they were first seen from (outside: {outside[:3] or 'none'})")
    decisions = [r for r in run.records if r.get("decision") == "decide" and (r.get("extra") or {}).get("target") is not None]
    unseen = [(r["frame"], (r["extra"] or {}).get("target"), (r["extra"] or {}).get("seen_from")) for r in decisions
              if not ((r["extra"] or {}).get("known") and in_window(tuple(r["extra"]["seen_from"]), tuple(r["extra"]["target"])))]
    if expect_inside:
        run.check(bool(decisions) and not unseen,
                  f"every one of the {len(decisions)} targets the AI chose was a tile it had SEEN, inside the window it was seen "
                  f"from (not: {unseen[:3] or 'none'})")
    return len(outside)


def check_hands(run: Run, walking: bool = True) -> None:
    """Every press has a gate; every A is a wait, a menu confirm or a talk by its look; every walking hold is pressed on
    a look of the overworld with nothing waiting and no menu, and is CHUNK_FRAMES long (`walking`: the arm walks at
    all; TRN does not); no catch-all idle."""
    presses = run.presses
    no_gate = [p for p in presses if not p.get("reason")]
    run.check(bool(presses) and not no_gate, f"{len(presses)} presses in the action log, every one with its gate (without: {len(no_gate)})")
    kinds: dict[str, int] = {}
    wrong = []
    for press in (p for p in presses if p["action"].startswith("press A ")):
        kind, ok = classify_a(press)
        kinds[kind] = kinds.get(kind, 0) + 1
        if not ok:
            wrong.append((press["frame"], kind, press["reason"][:60], (press.get("digest") or "")[:90]))
    run.check(not wrong, f"EVERY A press is a WAIT, a MENU confirm (the battle's RUN included) or a TALK by its look: "
                         f"{dict(sorted(kinds.items())) or 'none pressed'}; any other: {wrong[:4] or 'none'}")
    walks = [p for p in presses if str(p.get("reason", "")).startswith(WALK_GATES)]
    bad_walk = [(p["frame"], p["reason"][:50], (p.get("digest") or "")[:100]) for p in walks
                if not str(p.get("digest", "")).split()[1:2] == ["overworld"] or "waits=A/B" in (p.get("digest") or "")
                or " ui=" in (p.get("digest") or "")]
    run.check((bool(walks) == walking) and not bad_walk,
              f"{len(walks)} walking holds (want {'some' if walking else 'none'}), each pressed on a look of the OVERWORLD with "
              f"nothing waiting and no menu (any other: {bad_walk[:3] or 'none'})")
    lengths = sorted({(p.get("extra") or {}).get("hold") for p in walks})
    others = [(p.get("extra") or {}).get("hold") for p in presses if p not in walks and p["action"].startswith("press ")]
    run.check(lengths == ([CHUNK_FRAMES] if walking else []) and all(h is not None and 1 <= h <= 7 for h in others),
              f"pace: every walking hold {CHUNK_FRAMES} frames (seen {lengths}), every other press 1-7 frames "
              f"(seen {sorted(set(others))})")
    idle = [r for r in run.records if r.get("decision") == "watch"]
    generic = [(r["frame"], r["reason"]) for r in idle if str(r.get("reason", "")).startswith(GENERIC_BUSY)]
    run.check(not generic, f"{len(idle)} stretches standing still, NONE under the catch-all {GENERIC_BUSY!r}: {generic[:3] or 'none'}; "
                           f"reasons {sorted({re.sub(r'[0-9]+', '#', str(r['reason']))[:50] for r in idle})[:10]}")
    walk_gates: dict[str, int] = {}
    for press in walks:
        key = press["reason"].split(":")[0].split(" (")[0]
        key = re.sub(r"[0-9]+", "#", key)
        walk_gates[key] = walk_gates.get(key, 0) + 1
    run.notes.append(f"walking holds by gate: {json.dumps(dict(sorted(walk_gates.items())), ensure_ascii=False)}")


def transitions(run: Run) -> list[list]:
    return (run.world or {}).get("transitions") or []


def names(run: Run) -> dict[str, str]:
    world = memory_of(run)
    return world.names() if world is not None else {}


def describe_transitions(run: Run) -> str:
    n = names(run)
    return "; ".join(f"{n.get(t[1], t[1])} -> {n.get(t[2], t[2])} {t[3]} by {t[4]} tile {t[5]} arrival {t[6]} {t[7]}"
                     for t in transitions(run)) or "none"


def world_lines(run: Run) -> list[str]:
    return [line for line in run.ai_log.splitlines() if line.startswith("[AI-WORLD]")]


def stats(truth: dict | None, key: str) -> int | None:
    return ((truth or {}).get("game_stats") or {}).get(key)


def map_name_of(record: dict) -> str | None:
    """The map key ("group:number") of a record's look: its digest says "REGION NAME(g,n) xy=..."."""
    match = re.search(r"\((\d+),(\d+)\) xy=", record.get("digest") or "")
    return None if match is None else f"{match.group(1)}:{match.group(2)}"


def walk_steps_on(run: Run, key: str) -> int:
    """How many steps (a "walk ..." gate: the first chunk of a step) the AI pressed on one map, from its action log."""
    return sum(1 for p in run.presses if str(p.get("reason", "")).startswith("walk ") and map_name_of(p) == key)


def describe_trial(trial: dict) -> str:
    p = trial["predicted"]
    want = (f"{p['steps']} step(s), then the map becomes {p['map']}" if p["ends"] == "map"
            else f"{p['steps']} step(s), then a stop at {p.get('at')} ({p.get('why')})")
    got = (f"{trial['game_steps']} step(s) (the game's counter), map {'changed to ' + str(trial['loaded_map']) if trial['map_changed'] else 'unchanged'}")
    return f"hold {trial['direction']}: the ROM predicts {want}; the game: {got} -> {'agrees' if trial['agree'] else 'DISAGREES'}"


def check_game_answer(run: Run) -> None:
    """THE GAME'S ANSWER to where the player stands (`gates/game_answer.py`; the step-3 verifier's weak proof 3: the
    truth's `pos` is the memory the eyes read too): holding a direction from the state the run left, the game's own
    step counter and the map it loads must do what the ROM's layout at save block 1's claimed tile predicts; the same
    probe claiming a neighbouring tile it rules out must DISAGREE (its fault-test)."""
    a, after = run.answer or {}, run.after or {}
    claim = f"{after.get('map')} {after.get('pos')}"
    if not a or "error" in a:
        run.check(False, f"THE GAME'S ANSWER for {claim}: the probe failed: {str(a.get('error'))[-300:]}")
        return
    trials = a.get("trials") or []
    fault = run.answer_fault or {}
    if a.get("inconclusive"):
        # (the step-3 verifier's second round: an INCONCLUSIVE answer used to pass on the loaded map header alone, so
        # STUCK's end tile had no behavioural confirmation. It no longer passes without one.)
        why = "; ".join(f"{d}: {p.get('why')}" for d, p in (a.get("plans") or {}).items())
        arrival, lock = a.get("arrival") or {}, a.get("locked") or {}
        held = "; ".join(f"{d}: {h['game_steps']} steps, moved {h['moved']}, map changed {h['map_changed']}"
                         for d, h in (lock.get("held") or {}).items())
        if not arrival:
            run.check(False, f"THE GAME'S ANSWER for {claim}: INCONCLUSIVE (no clean line from this tile: {why}) and no other "
                             f"answer asked for: the end tile has NO behavioural confirmation")
            return
        changes = transitions(run)
        last = changes[-1] if changes else None
        after_it = [(p["frame"], p["reason"][:50]) for p in run.presses if last is not None and p["frame"] >= last[0]]
        warp = [arrival.get("warp", {}).get("map"), arrival.get("warp", {}).get("tile")]
        run.check(bool(a.get("agree_by_arrival")) and warp == list(STUCK_WARP) and last is not None and not after_it
                  and fault.get("agree_by_arrival") is False and fault.get("agree") is not True,
                  f"THE GAME'S ANSWER for save block 1's claim {claim} (no walking line: {why}): (1) LOCKED: each direction held "
                  f"{lock.get('held_frames')} frames from the state left moves nothing and counts no step ({held}) -> locked "
                  f"{lock.get('locked')}: the player cannot have moved since; (2) THE ARRIVAL by the ROM: the warp the AI used last "
                  f"{warp} (pre-registered {list(STUCK_WARP)}) lands on {arrival.get('map')} {arrival.get('landing')} "
                  f"({arrival.get('landing_behaviour')}), and the exit step {arrival.get('exit_step')} leaves the player on "
                  f"{arrival.get('tile')} -> agrees {arrival.get('agrees')}; the loaded map (gMapHeader) is the claimed map's: "
                  f"{a.get('loaded_header_is_claimed_map')}; (3) the AI pressed NOTHING from that arrival (f{last[0] if last else '?'}) "
                  f"on: {after_it or 'none'}; FAULT-TEST: the probe claiming {(a.get('ruled_out') or [None])[0]} instead -> "
                  f"by the arrival {fault.get('agree_by_arrival')}, by walking {fault.get('agree')} (want False, not True)")
        return
    standable = 8 - len(a.get("neighbours_that_are_walls") or [])
    wrong = (a.get("ruled_out") or [None])[0]
    run.check(bool(a.get("agree")) and fault.get("agree") is False,
              f"THE GAME'S ANSWER to save block 1's claim {claim}, by its behaviour from the state left (gates/game_answer.py): "
              f"{' | '.join(describe_trial(t) for t in trials)}; the map the game LOADED (gMapHeader) is the claimed map's ROM "
              f"header: {a.get('loaded_header_is_claimed_map')}; the trials rule out {len(a.get('ruled_out') or [])} of the "
              f"{standable} neighbouring tiles the player could stand on {a.get('ruled_out')}; FAULT-TEST: the probe claiming "
              f"{wrong} instead: {' | '.join(describe_trial(t) for t in fault.get('trials') or []) or fault} -> agree="
              f"{fault.get('agree')} (want False)")


# ---------------------------------------------------------------------- graders
def grade_common(run: Run, want_prefix: str, walking: bool = True) -> None:
    check_purity(run, None)
    run.check(run.outcome.startswith(want_prefix), f"the brain's outcome: {run.outcome[:200]!r} (want it to begin {want_prefix!r})")
    check_after_is_this_run(run)
    check_hands(run, walking)
    if run.arm.name not in NO_ANSWER:
        check_game_answer(run)
    run.notes.append("the AI's [AI-WORLD] lines:\n    " + "\n    ".join(line[:300] for line in world_lines(run)))
    run.notes.append(f"map changes (from the memory): {describe_transitions(run)}")


def grade_HOUSE(run: Run) -> None:
    grade_common(run, "explore: done: explore to LITTLEROOT_TOWN")
    before, after = run.before or {}, run.after or {}
    run.check(before.get("map") == HOUSE_2F and before.get("VAR_LITTLEROOT_INTRO_STATE") == 6,
              f"NON-VACUITY (the fixture): map {before.get('map')} (the player's 2F {HOUSE_2F}), VAR_LITTLEROOT_INTRO_STATE "
              f"{before.get('VAR_LITTLEROOT_INTRO_STATE')} (6: the clock set, the TV scene still to come)")
    run.check(after.get("map") == LITTLEROOT and after.get("VAR_LITTLEROOT_INTRO_STATE") == 7,
              f"TRUTH after (save block 1): map {after.get('map')} == LITTLEROOT_TOWN {LITTLEROOT} at {after.get('pos')}; "
              f"VAR_LITTLEROOT_INTRO_STATE {after.get('VAR_LITTLEROOT_INTRO_STATE')} == 7 (the TV scene was played through)")
    moves = [t for t in transitions(run)]
    n = names(run)
    chain = [(n.get(t[1]), n.get(t[2]), t[3], t[4]) for t in moves]
    # (since the whim among equals, a seed may look round 1F, or go back up, before it leaves: the first and the last
    # map change are the claim, and every change between is the AI's own warp)
    run.check(len(chain) >= 2 and chain[0] == ("LITTLEROOT_TOWN_BRENDANS_HOUSE_2F", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", "warp", "ai")
              and chain[-1] == ("LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", "LITTLEROOT_TOWN", "warp", "ai")
              and all(c[2:] == ("warp", "ai") for c in chain),
              f"the AI's own memory: down the stairs and out the door, each a WARP it used itself: {chain}")
    a = [p for p in run.presses if p["action"].startswith("press A ")]
    run.check(len(a) >= 3, f"the TV scene read through: {len(a)} A presses, each on a wait (above)")
    check_crop(run)
    s0, s1 = stats(before, "steps"), stats(after, "steps")
    run.notes.append(f"the game's own step counter: {s0} -> {s1}")


def grade_TOWN(run: Run) -> None:
    grade_common(run, "explore: done: explore to ROUTE101")
    before, after = run.before or {}, run.after or {}
    run.check(before.get("map") == LAB and after.get("map") == ROUTE101,
              f"TRUTH (save block 1): map {before.get('map')} (Birch's lab {LAB}) -> {after.get('map')} (ROUTE101 {ROUTE101}) at "
              f"{after.get('pos')}")
    b0, b1 = (before.get("flags") or {}).get("SYS_B_DASH"), (after.get("flags") or {}).get("SYS_B_DASH")
    run.check(b0 is False and b1 is True, f"TRUTH: SYS_B_DASH {b0} -> {b1}: Mom's Running Shoes scene was played through on the way")
    n = names(run)
    chain = [(n.get(t[1]), n.get(t[2]), t[3], t[4], t[7]) for t in transitions(run)]
    # (since the whim among equals a seed may look into a house on the way: the first and the last map change are the
    # claim; a change between is a warp into or out of a building, the AI's or a scene's)
    run.check(len(chain) >= 2 and chain[0][:4] == ("LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB", "LITTLEROOT_TOWN", "warp", "ai")
              and chain[-1] == ("LITTLEROOT_TOWN", "ROUTE101", "connection", "ai", "up")
              and all(c[2] == "warp" for c in chain[1:-1]),
              f"the AI's own memory: out of the lab by a WARP, then off the north edge: a CONNECTION going up: {chain}")
    world = memory_of(run)
    connection = next((c for c in (world.connections if world is not None else []) if n.get(c.get("target")) == "ROUTE101"), {})
    run.check(bool(connection) and connection.get("offset") is not None and connection["arrival"][1] == 19,
              f"the connection learned with its offset: {connection}")
    check_crop(run)
    s0, s1 = stats(before, "steps"), stats(after, "steps")
    ai_steps = walk_steps_on(run, "0:9") + walk_steps_on(run, "1:4") + walk_steps_on(run, "0:16")
    run.check(isinstance(s0, int) and isinstance(s1, int) and s1 - s0 >= ai_steps > 0,
              f"the game's OWN step counter (gameStats[GAME_STAT_STEPS]): {s0} -> {s1} (+{(s1 or 0) - (s0 or 0)}) >= the AI's "
              f"walking steps {ai_steps} (a scene's movements count too)")
    run.notes.append(f"TOWN: {walk_steps_on(run, '0:9')} walking steps on LITTLEROOT_TOWN; decisions "
                     f"{sum(1 for r in run.records if r.get('decision') == 'decide')}")


def grade_ROUTE(run: Run) -> None:
    grade_common(run, "explore: done: explore to OLDALE_TOWN")
    before, after = run.before or {}, run.after or {}
    run.check(before.get("map") == ROUTE101 and after.get("map") == OLDALE,
              f"TRUTH (save block 1): map {before.get('map')} (ROUTE101) -> {after.get('map')} (OLDALE_TOWN {OLDALE}) at {after.get('pos')}")
    first = next((line for line in world_lines(run) if "memory from" in line), "")
    run.check("route101_south.world.jsonl" in first and ": 3 maps (" in first,
              f"the memory of the TOWN walk was LOADED (knowledge grows over a playthrough): {first[:200]}")
    n = names(run)
    chain = [(n.get(t[1]), n.get(t[2]), t[3], t[4], t[7]) for t in transitions(run)]
    run.check(chain and chain[-1] == ("ROUTE101", "OLDALE_TOWN", "connection", "ai", "up"),
              f"the last map change: Route 101's north edge, a CONNECTION going up: {chain}")
    south = [r for r in run.records if r.get("decision") == "decide" and (r.get("extra") or {}).get("kind") in ("road",)
             and (r.get("extra") or {}).get("target", [0, 0])[1] >= 20 and (r.get("extra") or {}).get("map") == "0:16"]
    run.check(not south, f"the road back south (to Littleroot, known from the loaded memory) was never chosen as a new road: {south[:2] or 'none'}")
    w0, w1 = stats(before, "wild_battles"), stats(after, "wild_battles")
    fled = sum(1 for line in world_lines(run) if line.startswith("[AI-WORLD] battle: fled"))
    met = sum(1 for line in world_lines(run) if line.startswith("[AI-WORLD] battle:"))
    run.check(isinstance(w0, int) and isinstance(w1, int) and w1 - w0 == met == fled,
              f"every wild battle met was FLED: the game's own wild-battle count {w0} -> {w1} (+{(w1 or 0) - (w0 or 0)}) == the "
              f"battles the AI met {met} == fled {fled}")
    p0, p1 = before.get("party"), after.get("party")
    run.check(bool(p0) and [m[0] for m in p0] == [m[0] for m in p1 or []] and all(m[1] > 0 for m in p1 or []),
              f"the party (get_party): {p0} -> {p1}: nobody fainted")
    check_crop(run)


def roam_record(run: Run) -> dict:
    return next(((r.get("extra") or {}) for r in run.records if r.get("decision") == "roam"), {})


def xy_of(record: dict) -> tuple[int, int] | None:
    """The player's tile in a record's look (its digest says "... xy=(x,y) ...")."""
    match = re.search(r"xy=\((-?\d+),(-?\d+)\)", record.get("digest") or "")
    return None if match is None else (int(match.group(1)), int(match.group(2)))


def roam_rederived(run: Run) -> dict:
    """The roaming metrics RE-DERIVED from the action log alone, not from the skill's own bookkeeping (the step-3
    verifier recomputed them from the looks' digests): the tile on the look before each training step's press (`roam
    ...`, the first chunk of a step), and the tile on the look of the metrics record after the last. A press after
    which the tile changed MOVED the player; one after which it did not is INTERRUPTED if a battle was met before the
    next press (the encounter is rolled at the end of the step before: it pre-empts this one), else it walked in place
    (a spin). Spins = those + the reversals (A -> B -> A) of the derived path. Also the walk to the grass before the
    first training step: the moves of its "walk ..." presses."""
    presses = [p for p in run.presses if str(p.get("reason", "")).startswith("roam ")]
    metrics_record = next((r for r in run.records if r.get("decision") == "roam"), {})
    seq = [xy_of(p) for p in presses] + [xy_of(metrics_record)]
    frames = [p["frame"] for p in presses] + [metrics_record.get("frame") or 10**12]
    battles = [r["frame"] for r in run.records if r.get("decision") == "world" and str(r.get("reason", "")).startswith("battle:")]
    path, interrupted, in_place = ([seq[0]] if seq and seq[0] is not None else []), 0, 0
    preempted: list[dict] = []
    for i in range(len(presses)):
        if seq[i + 1] != seq[i]:
            path.append(seq[i + 1])
        elif any(frames[i] <= f <= frames[i + 1] for f in battles):
            interrupted += 1
            preempted.append(preemption(run, presses[i]))
        else:
            in_place += 1
    reversals = sum(1 for k in range(2, len(path)) if path[k] == path[k - 2])
    first = presses[0]["frame"] if presses else 0
    walks = [p for p in run.presses if str(p.get("reason", "")).startswith("walk ") and p["frame"] < first]
    walk_seq = [xy_of(p) for p in walks] + ([seq[0]] if seq else [])
    walk_moves = sum(1 for a, b in zip(walk_seq, walk_seq[1:]) if a != b)
    return {"presses": len(presses), "steps": len(path) - 1, "path": path, "interrupted": interrupted, "in_place": in_place,
            "reversals": reversals, "spins": reversals + in_place, "walk_presses": len(walks), "walk_moves": walk_moves,
            "distinct": len(set(path)), "battles_logged": len(battles), "preempted": preempted}


def facing_of(record: dict) -> str | None:
    match = re.search(r"facing=(\w+)", record.get("digest") or "")
    return None if match is None else match.group(1)


def preemption(run: Run, press: dict) -> dict:
    """(the step-3 verifier's second round: "the ROAM spin ratio does not count the presses a battle pre-empted as
    spins ... a choice of definition") What one training press that did not move the player looked like, from the
    action log alone: the first record after it whose look is IN A BATTLE, how many pad frames after the press that
    was (`pad_frame`: the pad's own count), whether any look between showed the player on another tile or FACING
    another way (a press the game took would at least have turned the player toward a direction it did not face),
    and the direction pressed against the one faced."""
    index = run.records.index(press)
    battle = next((r for r in run.records[index + 1:] if (r.get("digest") or "").split()[1:2] == ["battle"]), None)
    between = run.records[index + 1:run.records.index(battle)] if battle is not None else []
    pressed = str(press.get("action", "")).split()[1].lower() if str(press.get("action", "")).startswith("hold ") else None
    start = (press.get("extra") or {}).get("pad_frame")
    seen = (battle.get("extra") or {}).get("pad_frame") if battle is not None else None
    return {"frame": press["frame"], "tile": xy_of(press), "pressed": pressed, "facing": facing_of(press),
            "battle_frame": battle["frame"] if battle is not None else None,
            "battle_after_pad_frames": None if seen is None or start is None else seen - start,
            "moved_before_the_battle": any(xy_of(r) not in (None, xy_of(press)) for r in between + ([battle] if battle else [])),
            "turned_before_the_battle": any(facing_of(r) not in (None, facing_of(press)) for r in between + ([battle] if battle else []))}


def grade_ROAM(run: Run) -> None:
    grade_common(run, "roam: roamed:")
    before, after = run.before or {}, run.after or {}
    metrics = roam_record(run)
    steps, attempts, spins = metrics.get("steps"), metrics.get("attempts"), metrics.get("spins")
    ratio = spins / steps if steps else None
    derived = roam_rederived(run)
    run.check(steps == 150 and ratio is not None and ratio < 0.02,
              f"ROAMING: {steps} training steps (want 150), spin ratio {spins}/{steps} = {ratio} over the TRAINING STEPS (the "
              f"stricter denominator; want < 0.02: back and forth on the same 1-2 tiles, or walking in place); over every "
              f"press {spins}/{attempts} = {metrics.get('spin_ratio_of_attempts')}")
    run.check(attempts == derived["presses"] and metrics.get("interrupted") == derived["interrupted"],
              f"ATTEMPTS == every training step PRESSED (the verifier: 150 'tried' for 163 roam presses): the AI's attempts "
              f"{attempts} == the `roam ...` presses in the action log {derived['presses']}; of them interrupted by a battle "
              f"{metrics.get('interrupted')} == re-derived {derived['interrupted']} (a battle logged between the press and the next)")
    run.check(steps == derived["steps"] and spins == derived["spins"] and [list(xy) for xy in derived["path"]] == metrics.get("path"),
              f"RE-DERIVED from the looks' digests alone (not the skill's bookkeeping): {derived['steps']} steps that moved the "
              f"player, {derived['reversals']} reversals + {derived['in_place']} in place = {derived['spins']} spins, "
              f"{derived['distinct']} distinct tiles; the path from the digests == the AI's path: "
              f"{[list(xy) for xy in derived['path']] == metrics.get('path')}")
    # (the step-3 verifier's second round) the presses that did NOT move the player, by what the game did with them. The
    # design's spin (draft §4: "walking in place is never a training action"; §7 criterion 9: "spin ratio under 2% of
    # training steps"; HUMAN-PLAY-DESIGN pillar 3) is a press that walks in place or back and forth. A press is
    # PRE-EMPTED, not spun, only when the evidence says the game never acted on it: the battle (rolled at the END of
    # the step before, on the tile just stepped onto) is on screen within the press's own two chunks (2 x
    # CHUNK_FRAMES pad frames: the press was still being held when the battle took the screen), the player stood on
    # the same tile AND faced the same way until the battle (a press the game took turns the player at once, or moves
    # it 8 frames in: measured 2026-10-08), and each battle accounts for ONE press. Anything else is counted as a spin
    # (`in_place`, asserted 0 here).
    pre = derived["preempted"]
    late = [p for p in pre if p["battle_after_pad_frames"] is None or p["battle_after_pad_frames"] > 2 * CHUNK_FRAMES]
    acted = [p for p in pre if p["moved_before_the_battle"] or p["turned_before_the_battle"]]
    battles_matched = {p["battle_frame"] for p in pre}
    other_way = sum(1 for p in pre if p["pressed"] != p["facing"])
    delays = sorted({p["battle_after_pad_frames"] for p in pre})
    run.check(derived["in_place"] == 0 and not late and not acted and len(battles_matched) == len(pre) == derived["interrupted"]
              and len(pre) <= (metrics.get("encounters") or 0),
              f"every press that did not move the player was PRE-EMPTED by a battle, not spun: {len(pre)} such presses, the "
              f"battle on screen {delays} pad frames after each (want <= {2 * CHUNK_FRAMES}: within the press's own two chunks; "
              f"late: {late[:2] or 'none'}); the player on the same tile and FACING the same way until the battle in every one "
              f"(else: {acted[:2] or 'none'}), {other_way} of them pressed AWAY from the way it faced (a press the game took "
              f"would have turned it); {len(battles_matched)} distinct battles for {len(pre)} presses (one each), of the "
              f"{metrics.get('encounters')} met; presses that left the player standing with NO battle: {derived['in_place']}")
    worst = (spins or 0) + len(pre)
    run.notes.append(f"THE STRICTEST READING, reported and NOT a criterion (the design's spin is walking in place or back and "
                     f"forth; a pre-empted press is neither, by the check above): counting every press that did not move the "
                     f"player as a spin, {worst}/{attempts} presses = {round(worst / attempts, 4) if attempts else None}")
    run.check((metrics.get("distinct") or 0) >= 40, f"distinct tiles covered: {metrics.get('distinct')} (want >= 40); the "
                                                    f"most-visited tile {metrics.get('most_visited')} times")
    s0, s1 = stats(before, "steps"), stats(after, "steps")
    # the run stops 8 frames into its last step (when the eyes see the tile change) and the game counts a step at its
    # END: `gates/game_answer.py` lets the saved state run on with no input and reports the step(s) still in flight
    flight = (run.answer or {}).get("steps_in_flight")
    run.check(isinstance(s0, int) and isinstance(s1, int) and isinstance(flight, int)
              and s1 + flight - s0 == derived["walk_moves"] + (steps or 0),
              f"the game's OWN step counter: {s0} -> {s1} (+{(s1 or 0) - (s0 or 0)}), + {flight} step in flight when the state "
              f"was saved (counted by the game once it ends) == the walk to the grass {derived['walk_moves']} (of "
              f"{derived['walk_presses']} walk presses) + the {steps} training steps")
    w0, w1 = stats(before, "wild_battles"), stats(after, "wild_battles")
    run.check(isinstance(w0, int) and isinstance(w1, int) and w1 - w0 == metrics.get("encounters") == metrics.get("fled")
              and (metrics.get("encounters") or 0) >= 1,
              f"encounters: the game's OWN wild-battle count {w0} -> {w1} (+{(w1 or 0) - (w0 or 0)}) == the AI's encounters "
              f"{metrics.get('encounters')} == fled {metrics.get('fled')}, and >= 1")
    path = [tuple(xy) for xy in metrics.get("path") or []]
    run.check(after.get("map") == ROUTE101 and path and list(path[-1]) == after.get("pos"),
              f"TRUTH: still on ROUTE101 ({after.get('map')}), the end tile by save block 1 {after.get('pos')} == the AI's last path "
              f"tile {list(path[-1]) if path else None}")
    check_crop(run)


def grade_CROP(run: Run, town: Run | None) -> None:
    grade_common(run, "explore: done: explore to ROUTE101")
    before, after = run.before or {}, run.after or {}
    # (the step-3 verifier's second round: CROP's success rested on the navigator's own outcome string; the game's
    # answer confirmed save block 1's claim but nothing compared that claim with ROUTE101)
    run.check(before.get("map") == LAB and after.get("map") == ROUTE101,
              f"TRUTH (save block 1): map {before.get('map')} (Birch's lab {LAB}) -> {after.get('map')} (ROUTE101 {ROUTE101}) at "
              f"{after.get('pos')}: the faulted run did reach the goal")
    outside = check_crop(run, expect_inside=False)
    world = memory_of(run)
    total = sum(len(m.tiles) for m in world.maps.values()) if world else 0
    run.check(outside > 100, f"the FAULT's harm to the perception rule, in the memory: {outside} of {total} known tiles lie OUTSIDE the "
                             f"window of the tile they were first seen from (the real arms: 0)")
    decisions = [(r.get("extra") or {}) for r in run.records if r.get("decision") == "decide"]
    first_town = next((d for d in decisions if d.get("map") == "0:9"), {})
    # SEEN = inside the window of the tile it was first seen from (the perception rule); the record's `in_window` is
    # "inside the window NOW", which an honest target seen two steps ago need not be (the sweep: TOWN seeds 4 and 6)
    seen = bool(first_town.get("known") and first_town.get("seen_from")
                and in_window(tuple(first_town["seen_from"]), tuple(first_town["target"])))
    run.check(first_town.get("kind") == "road" and not seen,
              f"the first target on LITTLEROOT_TOWN: a {first_town.get('kind')} at {first_town.get('target')} from "
              f"{first_town.get('player')}, first 'seen' from {first_town.get('seen_from')}: inside that window: {seen} (a road it "
              f"could not have seen; in the window now: {first_town.get('in_window')})")
    # NOT A CHECK (the step-3 verifier): the walk's LENGTH does not tell a cropped run from an uncropped one. An honest
    # TOWN seed can be as short (the seed sweep's Story seed 1: 26 steps, CROP's own total), so the two checks above
    # (tiles known from outside every window; a first target on the town it could not have seen) are the
    # discriminators, and `gates/rate_step3.py` measures them over 10 seeds of each (CROP-SEP in its evidence).
    steps = walk_steps_on(run, "0:9")
    if town is not None:
        real = walk_steps_on(town, "0:9")
        real_decisions = sum(1 for r in town.records if r.get("decision") == "decide")
        run.notes.append(f"for the record, NOT a discriminator: {steps} walking steps and {len(decisions)} decisions on the way "
                         f"(the real TOWN arm of this session, the same seed: {real} and {real_decisions})")
    else:
        run.notes.append(f"for the record, NOT a discriminator: {steps} walking steps on LITTLEROOT_TOWN, {len(decisions)} decisions")


def grade_STUCK(run: Run) -> None:
    grade_common(run, "explore: stuck: ping-pong:")
    before, after = run.before or {}, run.after or {}
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    run.check(0 < frames < run.arm.frames // 2, f"no hang: it gave up by itself after {frames} of {run.arm.frames} frames")
    n = names(run)
    ai = [t for t in transitions(run) if t[4] == "ai" and n.get(t[1]) == "LITTLEROOT_TOWN_BRENDANS_HOUSE_2F"]
    scene = [t for t in transitions(run) if t[4] == "scene"]
    run.check(len(ai) == 3 and len(scene) >= 2,
              f"the stairs used by the AI exactly 3 times ({[t[0] for t in ai]}), the scene's warps back recorded as the scene's "
              f"({len(scene)}): no door ping-pong past the rule")
    run.check(after.get("VAR_LITTLEROOT_INTRO_STATE") == 5 and after.get("FLAG_SET_WALL_CLOCK") is False
              and (after.get("map") or [None])[0] == 1,
              f"TRUTH: VAR_LITTLEROOT_INTRO_STATE {after.get('VAR_LITTLEROOT_INTRO_STATE')} (5), FLAG_SET_WALL_CLOCK "
              f"{after.get('FLAG_SET_WALL_CLOCK')} (False), map {after.get('map')} (still the house): nothing advanced")
    check_crop(run)


def rom_tile(state: Path, map_key: tuple[int, int], xy: tuple[int, int]) -> dict:
    """The SECOND PATH for BUMP: the ROM layout's facts at a tile, read by the framework's `MapLocation` (test side)."""
    code = ("import json,sys;from pathlib import Path;sys.path.insert(0,r'%s');from ai_player.gates.probe_eyes import boot;"
            "c=boot('ai-step0-fixture');c.emulator.load_save_state(Path(r'%s').read_bytes());c.emulator.run_single_frame();"
            "from modules.map import get_map_data;t=get_map_data(%r,%r);"
            "print('ROM '+json.dumps({'behaviour':t.tile_type,'collision':t.collision,'elevation':t.elevation}))"
            % (REPO, state, map_key, xy))
    data, raw = run_json([sys.executable, "-c", code], "ROM", clean_env({}), 300)
    return data or {"error": raw[-500:]}


def grade_BUMP(run: Run) -> None:
    grade_common(run, "goto: done:")
    after = run.after or {}
    world = memory_of(run)
    bumped = {key: list(memory.bumped) for key, memory in (world.maps.items() if world else [])}
    run.check(bumped == {"1:1": [BUMP_TILE]}, f"exactly one tile learned blocked by bumping: {bumped} (want {{'1:1': [{BUMP_TILE}]}})")
    bump_lines = [line for line in world_lines(run) if "BUMP:" in line]
    run.check(len(bump_lines) == 1 and f"{BUMP_TILE} is learned blocked" in bump_lines[0],
              f"ONE bump: {bump_lines[0][:220] if bump_lines else 'none'}")
    learned_at = next((r["frame"] for r in run.records if r.get("decision") == "world" and "BUMP:" in str(r.get("reason"))), None)
    toward = [(p["frame"], p["reason"][:60]) for p in run.presses if f"-> {BUMP_TILE}" in str(p.get("reason"))
              and str(p.get("reason")).startswith("walk ")]
    later = [t for t in toward if learned_at is not None and t[0] > learned_at]
    run.check(len(toward) == 1 and not later,
              f"pressed toward {BUMP_TILE} once (the bump, f{toward[0][0] if toward else '?'}) and NEVER after it was learned "
              f"(f{learned_at}): later {later or 'none'}")
    decisions = [r for r in run.records if r.get("decision") == "decide"]
    errand2 = [p for p in run.presses if str(p.get("reason", "")).startswith("walk ") and "toward the goto at (2, 4)" in p["reason"]]
    run.check(len(errand2) == 4, f"errand 2, (0,4) -> (2,4): {len(errand2)} steps (the only 2-step way is through {BUMP_TILE}: "
                                 f"avoided, round it in 4): {[p['reason'][:40] for p in errand2]}")
    rom = rom_tile(FIXTURES[run.arm.fixture][0], (1, 1), BUMP_TILE)
    run.check(rom.get("collision") == 0 and "Impassable" in str(rom.get("behaviour")),
              f"WHY, by a second path (the ROM layout via the framework's MapLocation): {BUMP_TILE} has collision {rom.get('collision')} "
              f"(the eyes call it walkable) and behaviour {rom.get('behaviour')!r} (it blocks a step from the north)")
    run.check(after.get("pos") == [0, 4] and after.get("map") == HOUSE_2F,
              f"TRUTH (save block 1): the last errand's tile [0, 4] == {after.get('pos')} on {after.get('map')}")
    run.notes.append(f"decisions: {[(r['frame'], r['action']) for r in decisions]}")
    check_crop(run)


def grade_BUMPR(run: Run) -> None:
    data = run.harness or {}
    run.check(str(data.get("reason", "")).startswith("goto: stuck"), f"the run's outcome: {str(data.get('reason'))[:200]!r} (want goto: stuck ...)")
    bumps = [line for line in data.get("lines") or [] if "BUMP:" in line and f"{BUMP_TILE} is learned blocked" in line]
    run.check(len(bumps) >= 10, f"HARM: {len(bumps)} bumps into the same tile {BUMP_TILE} (want >= 10): the bump is not remembered")
    truth = data.get("truth") or {}
    run.check(truth.get("pos") != [0, 4], f"errand 1 was never done: the player ended at {truth.get('pos')}, not (0, 4)")
    run.check(isinstance(data.get("frames"), int) and data["frames"] < run.arm.frames,
              f"no hang: it gave up within its budget: {data.get('frames')} of {run.arm.frames} frames")


def grade_TRN(run: Run) -> None:
    grade_common(run, "explore: stuck: a trainer battle: out of scope", walking=False)
    menu = [p for p in run.presses if "battle_action" in str(p.get("reason"))]
    run.check(not menu, f"NOTHING pressed on the battle's action menu: {[(p['frame'], p['reason'][:50]) for p in menu][:3] or 'none'}")
    after = run.after or {}
    run.check(stats(run.before, "trainer_battles") == stats(after, "trainer_battles"),
              f"the game's trainer-battle count unchanged ({stats(run.before, 'trainer_battles')} -> {stats(after, 'trainer_battles')}): "
              f"the battle was begun in the fixture, not by the AI")


def novelty_records(run: Run) -> list[dict]:
    """The navigator's novelty records (`[AI-WORLD] novelty at f...`: a novelty that is not a place, and the clock)."""
    return [r for r in run.records if r.get("decision") == "world" and str(r.get("reason", "")).startswith(NOVELTY_PREFIX)]


def intent_start(run: Run) -> int | None:
    """The frame of the intent's first look (its record "intent '...'": the novelty clock's starting value)."""
    record = next((r for r in run.records if r.get("decision") == "world" and str(r.get("reason", "")).startswith("intent ")), None)
    return None if record is None else record.get("frame")


def exp_of(truth: dict | None) -> dict[str, int]:
    """PID (hex) -> total experience, by the framework's own decoder (`hands_harness.py` truth: `party_exp`)."""
    return {row[0]: row[2] for row in (truth or {}).get("party_exp") or []}


def grade_XP(run: Run) -> None:
    """(the step-3 verifier's second round: "no live run has yet shown an intent's novelty clock reset by an XP gain")"""
    grade_common(run, "goto: stuck: nothing new")
    before, after = run.before or {}, run.after or {}
    e0, e1 = exp_of(before), exp_of(after)
    run.check(before.get("game_state") == "BATTLE" and len(e0) == 1,
              f"NON-VACUITY (the fixture, by the framework): a battle on screen ({before.get('game_state')}), the party "
              f"{before.get('party_exp')}: its experience not yet given")
    records = novelty_records(run)
    start = intent_start(run)
    record = records[0] if len(records) == 1 else {}
    extra = record.get("extra") or {}
    frame, clock = record.get("frame"), extra.get("clock")
    pid = next(iter(e1), None)
    want = f"experience gained (PID {pid}: {e0.get(pid)} -> {e1.get(pid)})"
    run.check(len(records) == 1 and extra.get("novelty") == [want],
              f"the AI told ONE novelty in the whole intent, and it is the experience, by IDENTITY: {[r.get('reason') for r in records]} "
              f"(want exactly [{want!r}]: the PID and both totals the framework's get_party() reads before and after)")
    ended = next((r["frame"] for r in run.records if r.get("decision") == "world" and str(r.get("reason", "")).startswith("battle:")), None)
    run.check(clock == [start, frame] and isinstance(ended, int) and ended <= frame and isinstance(start, int) and frame - start >= 300,
              f"the intent's CLOCK moved from its start f{start} to the experience gain f{frame} ({clock}), {None if not isinstance(frame, int) or not isinstance(start, int) else frame - start} "
              f"frames on, once the battle was over (f{ended}) and the AI looked at the party again")
    match = STUCK_NOTHING_NEW.search(run.outcome)
    end = after.get("frame")
    quiet, last = (int(match.group(1)), int(match.group(2))) if match else (None, None)
    run.check(match is not None and last == frame and "experience gained" in match.group(3) and quiet >= 3000
              and isinstance(end, int) and abs(end - (last + quiet)) <= FRAME_SLACK and isinstance(start, int) and end - start > quiet,
              f"BEHAVIOUR: the intent ended 'stuck: nothing new' {quiet} frames after the LAST novelty f{last} "
              f"({match.group(3) if match else '?'!r}), at f{end} (the state's frame, +-{FRAME_SLACK}): "
              f"{None if not isinstance(end, int) or not isinstance(start, int) else end - start} frames after the intent's start: "
              f"the experience gain bought it {None if not isinstance(frame, int) or not isinstance(start, int) else frame - start} frames")
    run.check(bool(e0) and bool(e1) and pid in e0 and e1[pid] > e0[pid],
              f"TRUTH (the framework's get_party, total_exp by PID): {e0} -> {e1}: the game gave the experience")
    w0, w1 = stats(before, "wild_battles"), stats(after, "wild_battles")
    met = [line for line in world_lines(run) if line.startswith("[AI-WORLD] battle:")]
    run.check(w0 == w1 and len(met) == 1 and "the battle ended" in met[0],
              f"the battle was the fixture's (the game's wild-battle count {w0} -> {w1}), ended by the AI reading it out: {met}")
    first = next((line for line in world_lines(run) if "memory from" in line), "")
    last_line = next((line for line in world_lines(run) if "memory at the end" in line), "")
    count = lambda line: (re.search(r"(\d+) tiles learned", line) or [None, None])[1]  # noqa: E731
    run.check("route101_xp.world.jsonl" in first and count(first) is not None and count(first) == count(last_line),
              f"NO PLACE was new (the memory of the AI's own errands was LOADED and knew every tile it saw): tiles learned "
              f"{count(first)} at the start, {count(last_line)} at the end")
    check_crop(run)


def grade_XPR(run: Run, xp: Run | None) -> None:
    data = run.harness or {}
    reason = str(data.get("reason", ""))
    match = STUCK_NOTHING_NEW.search(reason)
    lines = [line for line in data.get("lines") or [] if "] novelty at f" in line]
    truth = data.get("truth") or {}
    run.check(match is not None and match.group(3) == "none" and not lines,
              f"HARM: with experience not novelty the intent never saw anything new: {reason[:220]!r}; novelty lines: {lines or 'none'}")
    if match is not None:
        quiet, last = int(match.group(1)), int(match.group(2))
        run.check(abs(truth.get("frame", 0) - (last + quiet)) <= FRAME_SLACK,
                  f"stuck {quiet} frames after the intent's START f{last} (the clock never moved), at f{truth.get('frame')}")
    if xp is not None and match is not None:
        xp_end, xp_start = (xp.after or {}).get("frame"), intent_start(xp)
        here = truth.get("frame", 0) - int(match.group(2))
        there = (xp_end - xp_start) if isinstance(xp_end, int) and isinstance(xp_start, int) else None
        run.check(there is not None and here < there - 300,
                  f"A/B on the same fixture and seed: the intent lasted {here} frames here and {there} with the experience counted "
                  f"(XP): the gain alone moved the stuck verdict {None if there is None else there - here} frames later")
    run.check(exp_of(truth) and any(exp_of(truth)[k] > v for k, v in exp_of(data.get("start_truth")).items() if k in exp_of(truth)),
              f"the game DID give the experience here too (get_party): {exp_of(data.get('start_truth'))} -> {exp_of(truth)}: the "
              f"mutant ignored it")


GRADERS = {"HOUSE": grade_HOUSE, "TOWN": grade_TOWN, "ROUTE": grade_ROUTE, "ROAM": grade_ROAM, "STUCK": grade_STUCK,
           "BUMP": grade_BUMP, "BUMPR": grade_BUMPR, "TRN": grade_TRN, "XP": grade_XP}


# ---------------------------------------------------------------------- evidence
def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def predictions_ref(source: Path = Path(__file__)) -> str:
    """(the step-3 verifier's second round: "I cannot check that the predictions were pre-registered before the graded
    run, because the tree is uncommitted") The PRE-REGISTERED predictions this run is graded against, pinned: sha256 of
    this file's module docstring, read from the file at the START of the run, before any arm. A reviewer recomputes it
    (`py -3.12 -c "import ast,hashlib;print(hashlib.sha256(ast.get_docstring(ast.parse(open(PATH,encoding='utf-8').read()),
    clean=False).encode()).hexdigest()[:16])"`): equal means the predictions in the file now are the ones this run read,
    unedited since. WHAT IT CANNOT SHOW: that they were written before a first look at a graded run; only a commit
    made before the run can (this round's worker may make no commit), or a re-run by someone else after reading them
    (the step-3 verifier did exactly that, and every arm's frames and presses equalled the predictions)."""
    import ast

    text = ast.get_docstring(ast.parse(source.read_text(encoding="utf-8")), clean=False) or ""
    return (f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]} of live_step3.py's docstring ({len(text)} "
            f"characters), read at the start of this run")


def write_evidence(run: Run, code_ref: str, tag: str, predictions: str = "") -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{tag}-{run.arm.name}.txt"
    fixture = FIXTURES[run.arm.fixture]
    env = " ".join(f"{k}={v}" for k, v in {ENV_BRAIN: run.arm.brain, ENV_SEED: str(SEED), **run.arm.env}.items())
    if run.arm.kind != "launcher":
        env = f"none (a test-side script in its own throwaway emulator, from a COPY of the package; seed {SEED})"
    out = [
        f"AI PLAYER BUILD STEP 3 (THE WORLD MODEL AND THE NAVIGATOR) - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"code: {code_ref}",
        f"predictions: {predictions or predictions_ref()}",
        f"fixture: {fixture[0].relative_to(REPO).as_posix()} md5={md5_of(fixture[0])}",
        f"fixture documentation: {run.arm.doc or '-'}",
        f"command: {' '.join(run.command)}",
        f"env: {env}",
        f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s   run dir: {run.run_dir}",
        f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
        SELFTEST_LINE,
        "checks (pre-registered in ai_player/gates/live_step3.py's docstring; each quotes both values):",
        *[f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks],
    ]
    if run.notes:
        out += ["", "---- notes ----", *run.notes]
    if run.verdict is not None:
        out += ["", "---- the instrument's verdict file (purity.json) ----", json.dumps(run.verdict, indent=2, sort_keys=True)]
    if run.before is not None:
        out += ["", "---- TRUTH of the fixture BEFORE the run (gates/hands_harness.py truth) ----", json.dumps(run.before, sort_keys=True, ensure_ascii=False)]
    if run.after is not None:
        out += ["", "---- TRUTH of the state the run LEFT (gates/hands_harness.py truth) ----", json.dumps(run.after, sort_keys=True, ensure_ascii=False)]
    if run.answer is not None:
        out += ["", "---- THE GAME'S ANSWER for save block 1's claim, by its behaviour from the state left (gates/game_answer.py) ----",
                json.dumps(run.answer, sort_keys=True, ensure_ascii=False)]
    if run.answer_fault is not None:
        out += ["", "---- its FAULT-TEST: the same probe claiming the first neighbouring tile it rules out (must disagree) ----",
                json.dumps(run.answer_fault, sort_keys=True, ensure_ascii=False)]
    if run.harness is not None:
        harness = {k: run.harness.get(k) for k in ("brain", "seed", "reason", "frames", "presses", "seconds")}
        out += ["", "---- the run, in-process from a COPY of the package (gates/hands_harness.py) ----", json.dumps(harness, ensure_ascii=False),
                "the brain's lines:", *[f"  {line[:400]}" for line in run.harness.get("lines") or []],
                "TRUTH at the end:", json.dumps(run.harness.get("truth"), ensure_ascii=False, sort_keys=True)]
    if run.world is not None:
        world = WorldMemory.from_dict(run.world)
        n = world.names()
        out += ["", "---- the AI's memory at the end (world.jsonl, its last snapshot): maps, links, bumps ----"]
        for key, memory in world.maps.items():
            out.append(f"  {key} {memory.const}: {len(memory.tiles)} tiles known, {len(memory.visits)} stood on, bumped "
                       f"{sorted(memory.bumped)}, edges {memory.edges}, arrivals {memory.arrivals}")
        for name, link in sorted(world.warps.items()):
            out.append(f"  warp {name} ({n.get(name.split('|')[0])}) -> {n.get(link.get('to'))} {link}")
        for connection in world.connections:
            out.append(f"  connection {connection}")
    if run.records:
        out += ["", f"---- the action log: {len(run.records)} records (frame | decision | action | gate or reason | digest) ----"]
        for r in run.records:
            if r.get("decision") in ("start", "end"):
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {r.get('reason')} | {r.get('digest')}")
            else:
                extra = r.get("extra") or {}
                brief = {k: extra[k] for k in ("target", "kind", "player", "in_window", "seen_from", "map", "hold") if k in extra}
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {str(r.get('reason'))[:200]} | "
                           f"{(r.get('digest') or '')[:200]} {json.dumps(brief) if brief else ''}")
    if run.stdout:
        keep = [line for line in run.stdout.splitlines() if line.startswith(("[AI-", "[DRIVER]"))]
        out += ["", "---- evidence lines from stdout ([AI-*]) ----", *[line[:500] for line in keep]]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def leftover_processes() -> list[str]:
    try:
        import psutil
    except ImportError:
        return []
    found = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except Exception:  # noqa: BLE001
            continue
        if ("pokebot.py" in cmd and PROFILE in cmd) or ("hands_harness.py" in cmd and "ai_step3_" in cmd) or "game_answer.py" in cmd:
            found.append(f"pid {proc.info['pid']}: {cmd[:160]}")
    return found


def main() -> int:
    global SEED, SELFTEST_LINE
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Live proof of AI-player build step 3 (the world model and the navigator).")
    parser.add_argument("--arms", default=",".join(a.name for a in ARMS))
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--evidence-tag", default=None)
    args = parser.parse_args()
    SEED = args.seed
    tag = args.evidence_tag or (EVIDENCE_TAG if SEED == 3 else f"{EVIDENCE_TAG}-seed{SEED}")
    broken = selftest_after_check()
    SELFTEST_LINE = (f"[SELFTEST] check_after_is_this_run on 5 synthetic runs (its own: pass; a stale mtime, a frame +3000, no file, "
                     f"the fixture's md5: fail): {'PASS' if not broken else 'FAIL ' + str(broken)}")
    print(SELFTEST_LINE)
    if broken:
        return 2
    wanted = [name.strip() for name in args.arms.split(",") if name.strip()]
    unknown = [name for name in wanted if name not in GRADERS and name not in ("CROP", "XPR")]
    if unknown:
        print(f"unknown arms: {unknown}")
        return 2
    for name, (path, md5) in FIXTURES.items():
        actual = md5_of(path) if path.is_file() else "MISSING"
        if actual != md5:
            print(f"ABORT: fixture {name} has md5 {actual}, pinned {md5}")
            return 2
    build_root = launcher.resolve_build_root()
    code_ref = tree_provenance(REPO)
    predictions = predictions_ref()
    print(f"predictions: {predictions}")
    results: list[Run] = []
    town: Run | None = None
    xp: Run | None = None
    for arm in [a for a in ARMS if a.name in wanted]:
        print(f"\n=== ARM {arm.name}: {arm.title} ===", flush=True)
        run = run_harness_arm(arm) if arm.kind == "harness" else run_arm(arm, build_root)
        if arm.name == "CROP":
            grade_CROP(run, town)
        elif arm.name == "XPR":
            grade_XPR(run, xp)
        else:
            GRADERS[arm.name](run)
        if arm.name == "TOWN":
            town = run
        if arm.name == "XP":
            xp = run
        evidence = write_evidence(run, code_ref, tag, predictions)
        results.append(run)
        print(f"ARM {arm.name}: {'PASS' if run.passed else 'FAIL'}  (exit {run.exit_code}, {run.elapsed:.1f}s) -> {evidence.relative_to(REPO)}")
        for ok, text in run.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {text[:400]}")
    leftovers = leftover_processes()
    print("\n=== SUMMARY ===")
    for run in results:
        print(f"  ARM {run.arm.name:<6} {'PASS' if run.passed else 'FAIL'}  {run.arm.title}")
    print(f"  leftover emulator processes: {leftovers or 'none'}")
    ok = all(run.passed for run in results) and not leftovers
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
