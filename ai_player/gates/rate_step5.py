"""TEST SIDE (build step 5): the SEED SWEEP of the story player: how OFTEN chapter 1 is played through, and what each
fault arm costs. In-process (`gates/play_harness.py`), the cartridge's clock pinned, every run graded by the GAME's own
record (`play_harness.StoryRecorder`: save block 1's marks and the game's counters read by the harness's own code, never the
AI's eyes), the AI's told lines only cross-checked.

    py -3.12 ai_player/gates/rate_step5.py --purpose development|graded|replay --first-seed N [--seeds 12]
                                           [--plans CH1,NOTRAIN,NOHINTS,DEADREST,ERRANDS_OFF,STALL1,STALL2,PATIENCE,
                                                    PATIENCE_OLD,STOP,STOPDEAD] [--workers 8]
                                           [--frames 300000] [--evidence-tag step51] [--keep-runs]
    py -3.12 ai_player/gates/rate_step5.py --purpose graded --first-seed 901 --seeds 20 [same options] --register
                                           (pre-registers a graded range in `gates/ledger.json` with the numbers it will be
                                           graded by, BEFORE any run of it; plays nothing)

(Build step 5.2, the safety gates) EVERY SWEEP: `--purpose` and `--first-seed` have NO default (a graded sweep with
default arguments played development seed 1 and said nothing). THE SEED LEDGER (`gates/ledger.py`, G2): a graded run
plays only a range REGISTERED first with the sha256 of `registered_numbers` (BOUNDS, the constants, the plans, frames and
target) and overlapping no other entry; a development run may not spend a registered range; a replay is written and
reported as one. THE FROZEN-TREE WATCH (`provenance.FrozenTree`, G1): checked before and after every run; once the tree
moved, the remaining runs are skipped and the verdict is FAIL "the tree changed mid-run". THE DISK BUDGET
(`gates/disk_budget.py`, G5): no start with under 30 GB free; every run folder under ONE root, deleted after grading but
for the failing runs (all of them when the verdict is FAIL) and the newest 5 (`--keep-runs` keeps all: a verifier who will
recount from the raw logs passes it).

THE PLANS (each seed: a personality and a starter drawn by the seed number, so every personality and starter is played):
  CH1      a real New Game to the POKéDEX (`ch1_pokedex`): reached? frames; the rival beaten at the FIRST try (by the game:
           the trainer-battle counter when the rival's flag went up); TRAINED BY THE GAME (the step-5 verifier's round 2):
           inside the windows the AI's log says it roamed to train before the rival's flag, the game's own step counter
           (`play_harness` THE STEPS) and the wild battles the game says were WON there (THE BATTLES), and the AI's
           training steps (its roam reports); the wild battles won anywhere before the rival (reported: walks win battles
           too); its spin ratio; any stretch standing still under the catch-all reason; THE REST RULE (no roam fought on
           after a battle that left the party under its personality's heal_below, `roam_breaches`, with its occasions
           counted); the AI's battles lost (its report) == its TOLD losses (the play loop's lines) == the game's
           (gBattleOutcome LOST) in every run of every plan
  NOTRAIN  FAULT `no_training`: the same seeds, no training before a known fight (the heal before the fight KEPT: the
           fault removes the training only): the wild battles won before the rival (the mechanism), the game-side TRAINED
           check failing in EVERY seed (it tells training from none), the party's strongest level and the share of its
           HP left when the rival's flag went up, PAIRED by seed (the effect, the framework's party decoder at that
           frame), and the first-try win rate (REPORTED, not bounded: below)
  NOHINTS  FAULT `no_hints`: the same seeds, no hint ever used: reached or not within the budget, the frames, the reason
  DEADREST the fix REMOVED: a copy of the package with `revert_step5.py`'s mutant G36 (the navigator asks the rest rule only
           with a battle limit set, as it did until the step-5 verifier's round): the rest check must find the battles
           played on under heal_below that the real code no longer plays (CLAUDE.md rule 8: an arm with the fix removed)
  STOP, STOPDEAD  PHASE 2 (`STOP_PLANS`): every run above that the GAME recorded a battle lost in, replayed with MAX_LOSSES
           1 in a copy: STOP must end at that loss with the loop's reason; STOPDEAD (the loop's count also removed,
           revert_step5 G46: the verifier's V6) must not, and its report says 0 losses where the game lost
  ERRANDS_OFF  (build step 5.1) FAULT `no_errands`: the BEELINE control: no look-around, detour, new-map stop, chat or
           catching roam. The intent mix, the seed divergence and the frames to the POKéDEX must all move against CH1
  STALL1, STALL2  (build step 5.1) the step-5 verifier's two stalls RE-INTRODUCED in copies (`MUTANT_PLANS`): the stall
           property must FAIL in them, by both paths (the AI's record and the game's)
  PATIENCE, PATIENCE_OLD  (build step 5.1) a copy with `STORY_PATIENCE` = `SMALL_PATIENCE`, shorter than the training
           before the rival: with the real rule (progress resets it) the POKéDEX is reached; with the step-5 rule (G67: only a
           milestone resets it) the run stops "no progress for ..." while training
  STALL3   (the step-5.1 verifier's round: "the game-side second path does not cover battles") a copy whose battle skill
           waits 600 frames at the action menu: the stall property must FAIL by BOTH paths (the second path now reads a
           battle's own waits: `play_harness.waits_now`), on the Story's seeds
  LOSE3    (the verifier's round: "MAX_LOSSES 3 was never reached by an unaltered run") a copy whose decider, once its
           battler is L7, uses its status move every turn of a wild battle and never runs: the play loop's REAL MAX_LOSSES
           must end the run at the game's third loss, report == told == game == 3, on the Catcher's seeds
  CH2, CH2_OFF  (the step-5.1 verifier's SECOND round: "chapter 2's stall property rests on the AI's own eyes alone", and the
           live arm CH2T FAILED the intent-mix floor) CHAPTER 2 in the sweep: every CH1 (and ERRANDS_OFF) run that reached
           the POKéDEX goes on, in its own worker, from ITS OWN end state and world memory to WALLY's tutorial (`ch2_wally`),
           the same seed, personality and faults (`CHAPTER2`, `run_chain`): WALLY by the game, the stall property by BOTH
           paths (the game's second path now reads chapter 2's screens too: the mart's menus, the PETALBURG gym, WALLY's
           tutorial), the intent-mix floor and the curiosity the story did not need in EVERY run, a new place new to the
           memory it started from; CH2_OFF, the beeline's chapter 2, must fall under the floor (`chapter2_verdicts`)
(The step-5.1 verifier's second round) the INTENT MIX is honest: a goal's frames end at its END record (the play loop's
`goal_end`; a goal DROPPED for a scene no longer counts the scene after it), and a curiosity goal the story moved on in is
the story's in the errand share too (`intent_mix`). Every graded run keeps its tree (`provenance.snapshot_tree`).
(The verifier's round) THE ERRANDS' OWN METRICS, which the beeline control must NOT meet: the CURIOSITY THE STORY DID NOT
NEED in every run (`intent_mix` free_share: a curiosity goal in which a milestone passed, the rival's POKé BALL, is the
story's own), the control under it; OFF THE BEELINE (`off_beeline`: the tiles a run stood on that no control run stood on,
against the control's own leave-one-out spread) and how those tiles differ by seed; NO SPEEDRUN per paired seed as well as
pooled.
THE STALL PROPERTY (build step 5.1, the step-5 verifier's FAILURE): in every run of the real code no screen WAITED FOR A
PRESS `AWAIT_MAX` frames or more with none, whatever reason the AI gave: by the AI's own record (`hands/waiting.py`, its
eyes) AND by the game's second path (`play_harness.WaitRecorder`: the framework's own reads of the tasks that poll a
button and of a text waiting for A/B, and the controls' presses).
The verdicts are PRE-REGISTERED in `BOUNDS` (machine-checked) from the DEVELOPMENT sweeps of 2026-10-14 (`step5dev1` to
`step5dev8`, seeds 1-9); the graded sweep plays HELD-OUT seeds. The first graded sweep played seeds 101-110 (the tree
59521c7ebf62dc70); the step-5 verifier's round (2026-10-14) re-graded on NEW held-out seeds, 201-210, since its fixes
were developed while seeds 101-110's results were known; its round 2 on seeds 301-310; build step 5.1 (developed on seeds
1-9 again, `step51dev*`) on NEW held-out seeds 401-410; the step-5.1 verifier's round (developed on seeds 1-9 and 21-29,
`step51vdev*`) on NEW held-out seeds 501-520 (twenty: the two pre-registered arm comparisons the verifier measured within
the noise, the beeline's time and its divergence, get twice the pairs). That sweep FAILED two of this round's own new
checks, each by an error in the check, not in the AI: the training bound was taken from the BASE personality though 2 runs
had DRIFTED into the Story's (`train_steps_min_run`), and LOSE3 graded a run that never reached a third loss; both were
corrected (no AI code changed) and graded again on NEW held-out seeds 601-620; the failed sweep's evidence is kept in
`evidence/archive/dee96b6ddadb6b11/`. The step-5.1 verifier's SECOND round (developed on seeds 31-39 and 41-49,
`step51wdev1`, `step51wdev2`, `step51wdev3`, with chapter 2) was graded on NEW held-out seeds 701-720; that pass FAILED the
chapter-2 floor in one run (seed 706: a walk to a known gym door skipped its stops; kept in `evidence/archive/
d0c949e96d355afe/`), was fixed (developed on 61-72 and 81-92, `step51wdev4`, `step51wdev5`) and is graded again on NEW
held-out seeds 801-820. The last development sweep (step5dev8, the tree of that round)
measured: CH1 9 of 9 reached, 9 of 9 first-try, wild battles WON before the rival 12-27 a seed, training steps 120-240,
spins 11 in 1566 steps (0.70 %), the catch-all 0, the rest rule 0 breaches over 20 occasions, whiteouts 0 (3 in 9 in
step5dev6 and step5dev7, before the way home was known); NOTRAIN won wild battles 47 vs 162, the strongest level at the
rival paired by seed +1.9 levels (every seed +1 to +3), first-try 8 of 9 vs 9 of 9; DEADREST 37 battles fought on under
heal_below over 46 occasions (the real code 0). (NOHINTS was not re-swept in development: its switch still makes
`hint_known` refuse every hint, before the new wordless rule is reached; its bound is unchanged.) The win-rate drop the design predicted for NOTRAIN is NOT measurable at this fight (the rival's L5 starter is
beaten untrained 8 times in 9), so it is reported, and the effect is graded on the fight's margin instead.
(Build step 5.3, stage A1: B1 the Goodhart gate, N8 typed checks; `PROJECT KNOWLEDGE/ai-research-notes/
2026-10-22-BUILD-SPEC-step5.3-B1-N8.md`) NOTHING above changed in what is measured. EVERY check is TYPED
(`gates/grader_checks.py`): an id `R5.*` from its one table, a kind (GRADED and HONESTY count; DIAGNOSTIC and REPORTED never
do), a status (PASS, FAIL, or VACUOUS when it saw fewer samples than its floor, which fails unless waived in
`gates/grader_waivers.json`), and its inputs (game, harness, ai) declared honestly. A GRADED check that reads the AI is
listed in `gates/b1_debt.json` with its A2 plan, and the evidence prints it as a `B1 DEBT` line. The 5.2 P2 shares are
REPORTED by kind, no longer forced to PASS by their text. THE GRADER OWNS ITS VALUES: it imports nothing from the AI's code
(the G-3 rule, `gates/check_grader_imports.py`, checked before any sweep is registered or played). ERRANDS, ERRAND_KINDS,
ASIDE and GENERIC_BUSY are its own copies, and MAX_LOSSES is the harness's record of the run. A chapter-2 draw's known places
are the maps chapter 1's GAME screen stood on, and a map's key comes from the framework's `MapRSE`. PATIENCE_OLD is graded by
the game: it ended early without the POKéDEX.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.grader_checks import (  # noqa: E402
    Check, as_check, evidence_lines, grade, verdict as typed_verdict, verdict_row,
)
from ai_player.gates.provenance import keep_earlier, provenance, snapshot_tree  # noqa: E402

HARNESS = Path(__file__).resolve().parent / "play_harness.py"
#: (build step 5.2) the seed ledger's family of this sweep (its successors grade the same story on the same seeds)
LEDGER_FAMILY = "story"
#: (build step 5.2, G1 and G5) the sweep's frozen-tree watch and its run folders' root, set by `main` (None: a run made
#: outside a sweep, by a test or another driver, gets its own temporary folder and no watch)
_TREE = None
_FOLDERS = None
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
GAME_CLOCK = "2026-10-14T10:00"
WALL_CLOCK = "10:00"
PERSONALITIES = ("Story", "Catcher", "Trainer")
STARTERS = ("TREECKO", "TORCHIC", "MUDKIP")
PLANS = {"CH1": "", "NOTRAIN": "no_training", "NOHINTS": "no_hints", "DEADREST": "",
         # (build step 5.1) the BEELINE control (no look-around, detour, new-map stop, chat or catching roam); the two
         # STALLs re-introduced (each a copy with the fix reverted); the patience A/B (a copy with a SMALL patience, the real
         # rule, and the same with the step-5 rule back); (the verifier's round) a BATTLE's wait for a press stalled
         # (STALL3: the second path now reads battles) and the decider made to lose (LOSE3: the real MAX_LOSSES reached)
         "ERRANDS_OFF": "no_errands", "STALL1": "", "STALL2": "", "PATIENCE": "", "PATIENCE_OLD": "", "STALL3": "",
         "LOSE3": "",
         # (the step-5.1 verifier's second round: "chapter 2's stall property rests on the AI's own eyes alone", and the live
         # CH2T arm FAILED the intent-mix floor) CHAPTER 2 in the sweep: each run of the base plan that reached the
         # POKéDEX goes on from ITS OWN end state and world memory to WALLY's tutorial (`CHAPTER2`), graded by the game's
         # second path too; CH2_OFF is the beeline control's chapter 2 (from the ERRANDS_OFF runs' ends)
         "CH2": "", "CH2_OFF": "no_errands",
         # (build step 5.2, PRODUCTIVE CURIOSITY) the controls that CAN fail (`08` 2026-10-15: "every A/B needs a control that
         # CAN fail: an arm that does the wrong thing on purpose"): LOAF looks round and takes detours among places it has
         # stood on (the yield checks must FAIL it); BLOCKED never gives up a place it cannot get to (the pushing property
         # must FAIL it where it met someone in the way); GREEDY passes every curiosity draw with no cap in a row (the
         # spacing check must FAIL it)
         "LOAF": "", "BLOCKED": "", "GREEDY": ""}
#: (the step-5.1 verifier's second round) the chapter-2 plans: plan -> the chapter-1 plan whose runs' ends it starts from,
#: and its target
CHAPTER2 = {"CH2": "CH1", "CH2_OFF": "ERRANDS_OFF"}
CH2_TARGET = "ch2_wally"
#: (the step-5 verifier's round, 2026-10-14) a plan played by a COPY of the package with mutants of
#: `gates/revert_step5.py` applied: DEADREST is G36, the navigator asking the rest rule only with a battle limit set (the
#: verifier's DEAD FIX, as it was): the arm with the fix REMOVED (CLAUDE.md rule 8), graded by the same rest check.
#: (build step 5.1) STALL1 is G53 (the starter bag watched for the bag alone: the verifier's stall (a)); STALL2 is G55, G56,
#: G57 and G86 (`talk` waits out a scene's text, no settling after a map change, no second look after deciding, no first
#: look in `talk_to`: stall (b), every layer removed); PATIENCE is the real code with `STORY_PATIENCE` small enough that
#: the training before the rival outlasts it (`SMALL_PATIENCE`), PATIENCE_OLD the same with G67 (the step-5 rule: only a
#: milestone resets it)
MUTANT_PLANS = {"DEADREST": ["G36"], "STALL1": ["G53"], "STALL2": ["G55", "G56", "G57", "G86"],
                "PATIENCE": ["PATIENCE_SMALL"], "PATIENCE_OLD": ["PATIENCE_SMALL", "G67"],
                # (the verifier's round) STALL3: the battle skill waits 600 frames at the action menu before it acts (a
                # battle's wait for a press, which the second path did not read); LOSE3: once its strongest is L7, the
                # decider uses its status move (slot 1: Leer or Growl) every turn of a wild battle and never runs
                "STALL3": ["STALL3"], "LOSE3": ["LOSE3"],
                # (build step 5.2) the three controls of productive curiosity (`EXTRA_EDITS`)
                "LOAF": ["LOAF"], "BLOCKED": ["BLOCKED"], "GREEDY": ["GREEDY"]}
#: (the verifier's round) plans whose losses are the fault itself: never replayed by the phase-2 STOP plans; (the second
#: round) nor the chapter-2 plans (a STOP replay starts from a New Game); (build step 5.2) nor the curiosity controls
NO_PHASE2 = ("LOSE3", "CH2", "CH2_OFF", "LOAF", "BLOCKED", "GREEDY")
#: (build step 5.1) the plans of the REAL code (no fault, no mutant): the stall property, the goal-after-page check and
#: the losses must hold in each
REAL_PLANS = ("CH1", "NOTRAIN", "NOHINTS", "ERRANDS_OFF", "CH2", "CH2_OFF")
#: (build step 5.1) plans played only on the seeds of one personality: the patience A/B on the TRAINER's seeds, whose
#: training before the rival is the longest (the review's case: a long training stint toward a higher target)
PLAN_PERSONALITY = {"PATIENCE": "Trainer", "PATIENCE_OLD": "Trainer",
                    # (the verifier's round) the two new fault arms on one personality's seeds each: a fault's mechanism,
                    # not a rate (the Story's for the battle stall, the Catcher's for the losses)
                    "STALL3": "Story", "LOSE3": "Catcher",
                    # (build step 5.2) GREEDY's spacing failure is a mechanism, not a rate: the Catcher's seeds (the most
                    # curious taste)
                    "GREEDY": "Catcher"}
#: (the step-5 verifier's round 2, 2026-10-14: "no run reached the MAX_LOSSES stop", and the loop's count was unproven)
#: PHASE 2, the STOP plans: every run of the plans above whose GAME recorded a battle LOST is played again, the same seed,
#: faults and mutants, in a copy whose MAX_LOSSES is 1 (`CAP1`): STOP must end with "1 battles lost (MAX_LOSSES 1)" right
#: after that loss (within `STOP_WITHIN` frames of the game's record of it); STOPDEAD, the same with the loop's count
#: REMOVED too (revert_step5 G46, the verifier's V6), must NOT, and its report must say 0 losses where the game lost (the
#: ALL PLANS check's arm: it would catch the dead count). The plans are chosen by the game's own record, before they run.
STOP_PLANS = {"STOP": ["CAP1"], "STOPDEAD": ["CAP1", "G46"]}
#: (build step 5.1) the PATIENCE plans' patience (frames): see `BOUNDS` for why this number
SMALL_PATIENCE = 40_000
EXTRA_EDITS = {"CAP1": [("mode.py", "MAX_LOSSES = 3\n",
                         "MAX_LOSSES = 1  # gates/rate_step5.py's STOP plans: the first battle lost ends the run\n")],
               "PATIENCE_SMALL": [("mode.py", "STORY_PATIENCE = 120_000\n",
                                   f"STORY_PATIENCE = {SMALL_PATIENCE}  # gates/rate_step5.py's PATIENCE plans\n")],
               # (the verifier's round) a battle's action menu waited out 600 frames before the decision is carried out
               "STALL3": [("skills/battle.py", "            done = yield from _execute(hands, mind, decision, why)\n"
                                               "            if done is not None:\n                return done\n"
                                               "            continue\n        if kind == BATTLE_MOVE:\n",
                           "            yield from hands.pad.idle(600, \"MUTANT STALL3: the action menu waited out\")\n"
                           "            done = yield from _execute(hands, mind, decision, why)\n"
                           "            if done is not None:\n                return done\n"
                           "            continue\n        if kind == BATTLE_MOVE:\n")],
               # (the verifier's round) once trained (its battler L7 or more), every wild battle: the status move in slot 1
               # every turn, never a run: the battles are LOST, and the real MAX_LOSSES must end the run
               "LOSE3": [("brain/battle.py", "        values = self._values(own, foe, hp_share, look)\n"
                                              "        if battle.kind == \"wild\" and mem.want_catch:\n",
                          "        values = self._values(own, foe, hp_share, look)\n"
                          "        if battle.kind == \"wild\" and own.level >= 7:  # MUTANT LOSE3\n"
                          "            return Decision(\"fight\", \"MUTANT LOSE3: the status move every turn\", move_slot=1)\n"
                          "        if battle.kind == \"wild\" and mem.want_catch:\n")],
               # (build step 5.2, the step-5.1 review's finding 4: "the beeline A/Bs cannot fail") LOAF: an AI that LOAFS on
               # purpose: its looks round walk among tiles it has STOOD ON (nothing new to see) with no novelty window, and
               # its detours go to such a tile; everything else is the real code. The yield checks must FAIL it.
               "LOAF": [("brain/goals.py",
                         "        found = [t for t in candidates(nav, look, weights, None, jitter_on=not moving)\n"
                         "                 if t.kind in LOOK_KINDS and t.tile not in avoid]\n",
                         "        here_ = nav.where(look)  # MUTANT LOAF: a tile it has stood on, nothing new to see\n"
                         "        found = [Target(\"wander\", xy, \"MUTANT LOAF\") for xy in sorted(here_[0].visits)\n"
                         "                 if abs(xy[0] - here_[1][0]) + abs(xy[1] - here_[1][1]) >= 4] if here_ else []\n"),
                        ("brain/goals.py", "carry_on=look_carry, novelty_window=CURIOUS_NOVELTY)\n",
                         "carry_on=look_carry, novelty_window=10 ** 9)  # MUTANT LOAF\n"),
                        # (the verifier's round) nor the end of a look round that has seen nothing new for a while
                        ("brain/goals.py", "                    return look.frame - seen_clock[1] >= CURIOUS_NOVELTY\n",
                         "                    return False  # MUTANT LOAF\n"),
                        ("brain/goals.py",
                         "            found = [t for t in candidates(navigator, look, weights, None, jitter_on=True) if t.kind "
                         "in DETOUR_KINDS\n",
                         "            found = [t for t in [Target(\"frontier\", xy, \"MUTANT LOAF\") for xy in sorted(memory."
                         "visits)] if True\n")],
               # (build step 5.2, the review's finding 5) BLOCKED: an AI that never gives up a place it cannot get to: no
               # watch for someone in the way, no blocked place carried, no place a scene turned it back from carried, a
               # detour to any place (none given up at a scene), "some more" wherever, and the look round with neither its
               # novelty window nor its budget. The pushing property must FAIL it in the runs that MET someone standing in
               # the way of a curiosity walk (`person_blocks`). (The development sweep step52dev2 ran the first version,
               # 5.2's blocks alone removed and the look round's novelty window the navigator's 3,000 frames: under the
               # pushing bound in 12 of 12, its longest stretch 2,057 frames by the game: 5.1's navigator already ended
               # ONE stretch by its novelty window, so that arm tested the repeats, not a push. Reported in the README.)
               "BLOCKED": [("brain/goals.py",
                            "        if blocked is not None and watchers is not None and hasattr(nav, \"stats\"):\n",
                            "        if False:  # MUTANT BLOCKED\n"),
                           ("brain/goals.py", "            nav.carried_scene_walls = walls if blocked is None else {\n",
                            "            nav.carried_scene_walls = walls if True else {  # MUTANT BLOCKED\n"),
                           ("brain/goals.py", "                    self._blocked(milestone, key, tuple(tile), why)\n",
                            "                    pass  # MUTANT BLOCKED\n"),
                           ("brain/goals.py", "carry_on=look_carry, novelty_window=CURIOUS_NOVELTY)\n",
                            "carry_on=look_carry, novelty_window=10 ** 9)  # MUTANT BLOCKED\n"),
                           # (the verifier's round) nor the end of a look round that has seen nothing new for a while
                           ("brain/goals.py", "                    return look.frame - seen_clock[1] >= CURIOUS_NOVELTY\n",
                            "                    return False  # MUTANT BLOCKED\n"),
                           ("brain/goals.py",
                            "                      else goal.steps if goal.kind == \"explore\" else goal.steps or LOOK_AROUND_FRAMES)\n",
                            "                      else 10 ** 9 if goal.kind == \"explore\" else goal.steps or LOOK_AROUND_FRAMES)"
                            "  # MUTANT BLOCKED\n"),
                           ("brain/goals.py",
                            "                     and t.tile in reach and not _beside(t.tile, avoid) and not memory.outside(t.tile)]\n",
                            "                     and not memory.outside(t.tile)]  # MUTANT BLOCKED\n"),
                           ("brain/goals.py",
                            "            if chosen and getattr(nav, \"scene_hits\", {}).get(f\"{nav.world.current}|{chosen[-1].key}\"):\n",
                            "            if False:  # MUTANT BLOCKED\n"),
                           ("brain/goals.py",
                            "            nothing = self.left_to_see(look, world, milestone.id) if odds > 0 else None\n",
                            "            nothing = None  # MUTANT BLOCKED\n"),
                           # (the development sweep step52dev9: with the route fixes the arm reached someone in the way
                           # of a curiosity walk in 0 of its first 10 runs; they too give up a place it cannot get to,
                           # the world memory's unreached frontier and the in-map plan, so the arm removes them as well)
                           ("brain/navigator.py", "                    world.mark_unreached(world.current, target.tile)\n",
                            "                    pass  # MUTANT BLOCKED\n"),
                           ("brain/navigator.py",
                            "            walls = walls | frozenset(xy for xy in memory.tiles if memory.outside(xy))\n",
                            "            pass  # MUTANT BLOCKED\n")],
               # (build step 5.2, the review's finding 2) GREEDY: every curiosity draw passes and no cap in a row (the
               # quota's bypass, at its worst). The spacing checks must FAIL it. (The verifier's round: once a map's "left
               # to see" counted only what it could get to, GREEDY's looks round "some more" ran out, and the round's
               # development sweep step52vdev2 had it at 3 in a row in 4 of 4, never over the bound: the control could no
               # longer fail. It now also looks round "some more" without limit and whether or not anything is left that
               # it can walk to, until a look round there brought nothing (its map exhausted): its greed at its worst
               # again. The first version ignored the exhausted mark too, and step52vdev5's GREEDY seed 1250 chose 94 goals
               # in 2,738 frames, empty looks round of LITTLEROOT each ending at once, with no press between (the game's
               # second path saw a text wait 2,730 frames there, the AI's record 150: the one two-path disagreement);
               # set in development, before any graded run of the round.)
               "GREEDY": [("brain/goals.py", "CURIOUS_ODDS_CAP = 0.9\n", "CURIOUS_ODDS_CAP = 1.0  # MUTANT GREEDY\n"),
                          ("brain/goals.py", "CURIOUS_ROW_MAX = 2\n", "CURIOUS_ROW_MAX = 99  # MUTANT GREEDY\n"),
                          ("brain/goals.py",
                           "        return min(1.0, since / max(1, self.state.errands.bored_frames)), since\n",
                           "        return 1.0, since  # MUTANT GREEDY\n"),
                          ("brain/goals.py", "AGAIN_MAX = 2\n", "AGAIN_MAX = 99  # MUTANT GREEDY\n"),
                          ("brain/goals.py",
                           "            nothing = self.left_to_see(look, world, milestone.id) if odds > 0 else None\n",
                           "            nothing = self.memory.exhausted.get(f\"{world.current}|{milestone.id}\")  # MUTANT GREEDY\n")]}
STOP_REASON = "play: stuck: 1 battles lost (MAX_LOSSES 1)"
#: frames from the game's record of the loss (gBattleOutcome LOST) to the run's end: the whiteout's text and the warp home
#: (~1,500 frames), the goal under way unwinding, and the loop's next pass
STOP_WITHIN = 6000
# ---------------------------------------------------------------------- (build step 5.3, A1-2) GRADER-OWNED VALUES
# THE G-3 RULE (`gates/check_grader_imports.py`): this grader and `live_step5.py` import NOTHING from the AI's code
# (`ai_player.brain`, `personality`, `mode`, `hands`, ...), directly or through a gates module that hands on an AI value.
# Before 5.3 they imported the AI's ERRANDS, ERRAND_KINDS, ASIDE and MAX_LOSSES, so an edit of the code under test moved
# the grader's bounds with no change to the registered numbers (the B1 recon, §4). Each value below is the grader's OWN
# copy, with the AI's value of 2026-10-22, so A1 changes no outcome; a later change of the AI's value no longer reaches the
# grade. (`test_goals` asserted the grader's CURIOSITY_KINDS equal to the AI's: that equality WAS the Goodhart channel, and
# was deleted with this.)
#: the AI's catch-all idle reason, as the grader matches it (source: `ai_player/hands/dialogue.py` GENERIC_BUSY)
GENERIC_BUSY = "watching: the game is busy"


class GraderErrands(NamedTuple):
    """The two errand numbers a grader bound is taken from, per personality."""
    train_min_steps: int
    heal_below: float


#: the training minimum (`train_steps_min`, 0.9x of it) and the rest rule's threshold (`roam_breaches`) per personality
#: (source: `ai_player/personality.py` ERRANDS: train_min_steps 100/80/150, heal_below 0.5/0.6/0.45)
ERRANDS = {"Catcher": GraderErrands(100, 0.5), "Story": GraderErrands(80, 0.6), "Trainer": GraderErrands(150, 0.45)}
#: the goal kinds the intent mix counts as errands (source: `ai_player/brain/goals.py` ERRAND_KINDS)
ERRAND_KINDS = ("heal", "find_center", "shop", "train", "catch", "pick_up", "chat", "explore", "detour")
#: the goal key prefix of a goal put aside for a story goal (source: `ai_player/brain/goals.py` ASIDE)
ASIDE = "aside:"
#: the play loop's battles-lost stop, used only for a row that does not carry the HARNESS's record of it (`max_losses` in
#: the PLAY json, `play_harness.play`: the value the run actually played with) (source: `ai_player/mode.py` MAX_LOSSES)
MAX_LOSSES_DEFAULT = 3
#: PRE-REGISTERED (module docstring): set from the development sweeps (named in the README's step-5 section).
BOUNDS = {
    "CH1_REACHED_MIN": 0.8,  # at least this share of the CH1 seeds reach the POKéDEX within the budget
    "CH1_FIRST_TRY_MIN": 0.8,  # ... and beat the rival at the first try
    # (the step-5 verifier's round 2, 2026-10-14: "won >= 3 between the starter's mark and the rival's flag" was met by
    # NOTRAIN, which never trains, in 6 of 10 seeds: walks win battles too) every CH1 seed that beat the rival: inside the
    # windows its log says it ROAMED TO TRAIN before the rival's flag (`training_windows`), the GAME says at least this many
    # wild battles were WON (`play_harness` THE BATTLES) ...
    # RE-DERIVED (the step-5.1 verifier's round: "the training bounds (60 steps, 3 won) were carried over, not re-derived"),
    # from the two graded sweeps' rows (seeds 301-310 and 401-410, 20 CH1 runs, every one past the rival; their evidence
    # files `2026-10-14-step5-RATE.txt`, `2026-10-14-step51-RATE.txt`): WON inside the windows 4-18 (NOTRAIN 0 in all 20),
    # so 3 stays, now one under the measured minimum, not a carried number
    "CH1_WILD_WON_MIN": 3,
    # ... and the GAME's step counter rose at least this much there (`play_harness` THE STEPS); its roam reports must say
    # as much too. RE-DERIVED from the design's own rule, per personality: a person roams at least `train_min_steps` before
    # a known fight (`personality.py` Errands: Story 80, Catcher 100, Trainer 150), so the bound is that minimum times
    # `CH1_TRAIN_STEPS_SHARE` (72 / 90 / 135; the 10 % for a step the game's counter refuses as an impossible reading or a
    # roam an item ball stopped). Measured on the same 20 runs, the game's steps over the personality's minimum 1.04-1.95
    # (Story 88-170, Catcher 104-188, Trainer 161-293). Every one of the three is tighter than round 1's carried 60, which
    # is kept below only as the floor of `train_steps_min`
    "CH1_TRAIN_STEPS_MIN": 60,
    "CH1_TRAIN_STEPS_SHARE": 0.9,
    # (the step-5 verifier's round) the game's WHITEOUTS (battles LOST) over all the CH1 seeds together at most this: the
    # development sweeps measured 3 in 9 (step5dev6, step5dev7: every one a wild battle met at 2-5 HP, six of them on a walk
    # home that could not find the house) and 0 in 9 once the way home was known (step5dev8)
    "CH1_WHITEOUTS_MAX": 2,
    "CH1_SPIN_MAX": 0.02,  # the back-and-forth spins over all the seeds' training steps together
    "CH1_SPINS_PER_SEED": 5,  # ... and no seed over this many (step 4.1 round 3's `ROAM_SPINS_PER_SEED`)
    "NOTRAIN_WILD_LESS": True,  # NOTRAIN wins fewer wild battles before the rival than CH1, in total
    # NOTRAIN's effect, PAIRED by seed: the mean of (CH1's strongest level at the rival's flag - NOTRAIN's) at least this,
    # and no seed where NOTRAIN is 2 or more levels higher
    "NOTRAIN_LEVEL_PAIRED_MIN": 0.5,
    "NOHINTS_SLOWER": True,  # NOHINTS reaches the POKéDEX in fewer seeds, or later on average where both reach it
    # ---- BUILD STEP 5.1, PRE-REGISTERED 2026-10-14 from the development sweeps step51dev1-dev7 (seeds 1-9, 63 CH1 runs of
    # the real code, 36 of the beeline control, 9 + 9 of the two STALL copies, 3 + 3 of the patience copies), BEFORE the
    # graded sweep on the held-out seeds 401-410:
    # THE STALL PROPERTY: the longest a screen may wait for a press with none (frames). The pad's longest deliberate pause
    # before a press is its READING cap (`hands/pad.py` Pacing.read_max: 150 frames, the jitter inside it) and its thinking
    # pause (14-45 frames, before a menu's cursor moves): MEASURED, the longest stretch in every development run of the
    # real code was 150 frames by the AI's own record and 150 by the game's second path (a page read at the cap). 300 is
    # twice that cap: room for the gate's look and the second path's 10-frame sampling, and far under the measured stalls
    # (the starter's yes/no 600-644 frames in STALL1, the scene's text 1,153-1,196 in STALL2)
    "AWAIT_MAX": 300,
    # each STALL copy must fail the property in at least this many of its 10 runs (measured: STALL1 in 5 of 9, STALL2 in 3
    # of 9 development runs; at those rates 10 runs miss both with probability 0.1 % and 2 %)
    "STALL_ARM_HITS_MIN": 1,
    # THE INTENT MIX: in EVERY CH1 run at least this share of the goals' frames on errands (all of them: heal, shop, train,
    # find a centre, an item, catch, chat, look around, a detour; measured 0.34-0.57 by run) ...
    "MIX_MIN": 0.30,
    # ... and each PERSONALITY's mean share on CURIOSITY (look around, a detour, a chat, a catching roam, an item ball) at
    # least this (measured by personality 0.087-0.135 with the errands, 0.030-0.035 under the beeline control)
    "CURIOSITY_MIN": 0.06,
    # SEED DIVERGENCE: every pair of CH1 runs of one personality, the mean edit distance of their goal sequences and the
    # mean Jaccard distance of the tiles they stood on at least these (measured 0.53-0.58 and 0.46-0.48; the beeline control
    # 0.49 and 0.46: the goal sequences must also diverge MORE than the beeline control's, the paths are reported)
    "DIV_GOALS_MIN": 0.30,
    "DIV_TILES_MIN": 0.30,
    # ERRANDS_OFF MOVES THE MIX: CH1 - ERRANDS_OFF curiosity share paired by seed, mean at least this (measured 0.08, 0.09)
    "MIX_DROP_MIN": 0.04,
    # NO SPEEDRUN: the frames to the POKéDEX OUTSIDE the needs (training, healing, finding a centre, shopping: the beeline
    # control keeps those, and their length is the battles' dice), CH1 over ERRANDS_OFF pooled over the paired seeds, at
    # least this: ABOVE the beeline. MEASURED 1.047 and 1.053; the TOTAL frames to the POKéDEX measured 0.987 and 1.006,
    # within the training's noise, so the total is REPORTED, not bounded (the README's step-5.1 section says so)
    "SLOWER_THAN_BEELINE_MIN": 1.0,
    # ... and every CH1 run that reached the POKéDEX did so within this many frames (the budget)
    "DEX_FRAMES_MAX": 300_000,
    # THE PATIENCE A/B (Trainer seeds, `SMALL_PATIENCE` 40,000: measured, the real rule's longest stretch with no progress
    # 13,512-29,504 frames, the training stints 53,553-63,537 frames): the real rule reaches the POKéDEX in at least this
    # share, the step-5 rule stops 'no progress' in at least this share, at least once WHILE TRAINING (measured 3 of 3 and
    # 3 of 3, each stop with a training session the last goal)
    "PATIENCE_REACHED_MIN": 0.8,
    "PATIENCE_OLD_STOPS_MIN": 0.8,
    # ---- THE VERIFIER'S ROUND OF STEP 5.1 (2026-10-14), PRE-REGISTERED from the development sweeps of this round's AI code
    # (step51vdev1: seeds 1-9, CH1, ERRANDS_OFF, STALL3, LOSE3, before the look-around debt and the 6-tile detour;
    # step51vdev2: seeds 1-9 and 21-29, CH1 and ERRANDS_OFF, the AI code graded; only gates changed after it) BEFORE the
    # graded sweep on NEW held-out seeds 501-520 (seeds 401-410's results were known while these fixes were made). Seeds 11,
    # 12 and 13 were never played in process on this tree: they are the live arms'.
    # CURIOSITY THE STORY DID NOT NEED (`intent_mix` free_share: a curiosity goal in which a milestone passed is the
    # story's own, the rival's POKé BALL): in EVERY CH1 run at least this share of the goals' frames (the look-around debt,
    # `brain/goals.py` LOOK_DEBT, makes at least one look round of `look_frames`, 3,000 or more, in a run of under 150,000
    # frames: 0.02; MEASURED in step51vdev2 0.040-0.157 over 18 runs; step51vdev1, before the debt, 0.0023 in seed 4) ...
    "FREE_RUN_MIN": 0.02,
    # ... each personality's mean at least this (measured in step51vdev2, six personality means 0.069-0.131) ...
    "FREE_MEAN_MIN": 0.05,
    # ... and the beeline control UNDER the per-run bound in at least this share of its runs (the check separates the arms:
    # measured 0.0 in 18 of 18, and in all 10 control runs of the first round's graded sweep, recounted)
    "FREE_CONTROL_FAILS_MIN": 0.8,
    # OFF THE BEELINE (`off_beeline`): CH1 stood on more tiles no beeline run stood on than the control run of its seed did
    # (against the other control runs) in at least this share of the paired seeds, and pooled at least this many times
    # (measured in step51vdev2 7 of 9 at 1.73x and 9 of 9 at 4.11x; the first round's code, recounted on 401-410, 6 of 10 at
    # 1.30x: the broken detour; the beeline's own leave-one-out spread 1-67 tiles a run) ...
    "OFF_SEEDS_MIN": 0.6,
    "OFF_RATIO_MIN": 1.3,
    # NO SPEEDRUN WITHOUT THE GRASS'S DICE (`time_to_dex` outside_nb): CH1 over ERRANDS_OFF pooled at least this, and CH1
    # the slower in at least this share of the paired seeds (measured in step51vdev2 1.069 with 9 of 9 and 1.058 with 7 of
    # 9, the per-seed ratio's spread 0.035 and 0.076; the first round's code on 401-410, recounted, 1.065 with 8 of 10;
    # while the frames outside the needs WITH the battles measured 1.078 and 0.995: the old bound below 1.0 in one of five
    # samples, so it is kept, pre-registered, and its failure would be the grass's dice, which this check removes)
    "NOBATTLE_RATIO_MIN": 1.02,
    "NOBATTLE_SEEDS_MIN": 0.6,
    # THE ERRANDS DIFFER BY SEED: their decisions in order (`curiosity_sequence`), mean edit distance over the pairs of
    # CH1 runs of one personality at least this (measured in step51vdev2 0.739 and 0.664; the control has none: 0)
    "CUR_DIV_MIN": 0.5,
    # A STORY GOAL PUT ASIDE COMES BACK (`aside_streaks`): a streak of asides for one story goal lasts at most this many
    # frames: the aside ends at the first decision after `brain/goals.py` STORY_ASIDE_FRAMES (6,000), and the look round
    # under way then runs out its LOOK_AROUND_FRAMES (2,400), with room for one battle met in it (one more 2,400). The
    # live CH2 arm of step 5.1's first round measured 10 asides in a row, about 32,000 frames
    "ASIDE_STREAK_MAX": 10_800,
    # LOSE3 (CORRECTED after the graded sweep on 501-520, see `step51_verdicts`): the arm reaches the game's third loss in
    # at least this share of its runs (measured: 3 of 3 in development, 5 of 6 on 501-520)
    "LOSE3_REACH_MIN": 0.6,
    # ---- THE STEP-5.1 VERIFIER'S SECOND ROUND (2026-10-14): CHAPTER 2 in the sweep (`CHAPTER2`, `chapter2_verdicts`).
    # PRE-REGISTERED 2026-10-15 from the round's development sweeps (step51wdev1, seeds 31-39, before the fixes it found;
    # step51wdev2, seeds 41-49, and step51wdev3, seeds 51-59, the AI code graded but for the nurse's give-way and the
    # curiosity minimum, which only dev3 had) BEFORE the graded sweep on NEW held-out seeds 701-720. MIX_MIN and FREE_RUN_MIN
    # above hold in EVERY chapter-2 run too (measured, the honest share: 0.42-0.55 and 0.40-0.65; dev1's two runs stuck on the
    # unreachable door 0.82-0.85). WALLY's tutorial reached in at least this share of the chapter-2 runs (measured 9 of 9
    # twice; dev1 7 of 9, the two runs the door bug stopped) ...
    # (KEPT, 2026-10-15, after the first graded pass on 701-720 FAILED the floor in one run, seed 706, 28.7 %: its walk to a
    # known gym door skipped the go's own stops. Fixed, and the Story's balance raised 40 % -> 45 %, the Trainer's 45 % ->
    # 48 %; measured again on NEW development seeds, step51wdev4 (61-72, the old balance) and step51wdev5 (81-92, the code
    # graded): the floor 0.34-0.55 and 0.42-0.65, WALLY 12 of 12 twice, CH2_OFF under the floor 12 of 12, the chapter-2
    # time 1.494 with 12 of 12; NONE of these bounds changed. The final graded sweep plays NEW held-out seeds 801-820.)
    "CH2_REACHED_MIN": 0.8,
    # ... the game's whiteouts over the chapter-2 runs together at most this (measured 0 in 27) ...
    "CH2_WHITEOUTS_MAX": 2,
    # ... the beeline control's chapter 2 under MIX_MIN in at least this share of its runs (measured 8 of 9 and 7 of 9: in
    # chapter 2 no training fills the floor, so it separates the arms there) ...
    "CH2_OFF_UNDER_MIN": 0.6,
    # ... and NO SPEEDRUN in chapter 2 without the grass's dice: the AI's own frames to WALLY outside the needs and the
    # battles, CH2 over CH2_OFF pooled at least this, CH2 the slower in at least this share of the paired seeds (measured
    # 1.491 with 9 of 9 and 1.369 with 8 of 9: the bound well under both)
    "CH2_NOBATTLE_RATIO_MIN": 1.15,
    "CH2_NOBATTLE_SEEDS_MIN": 0.7,
    # ---- BUILD STEP 5.2, PRODUCTIVE CURIOSITY (the step-5.1 adversarial review, 2026-10-15: "it LOAFS"). Every number below
    # is PRE-REGISTERED from the development sweeps of this round (README "Build step 5.2"), BEFORE the graded sweep on NEW
    # held-out seeds 901-920, and the ledger holds their sha256 (`registered_numbers`). Curiosity is graded by what it
    # BROUGHT (by the GAME: `game_yield`) and how it is SPACED, never by a share of frames (the AI's own target must not be
    # the graded quantity); the old bounds above still hold but the shares of frames (`P2_REPORTED`), their curiosity
    # counted by yield (`intent_mix` unproductive). THE FINAL DEVELOPMENT SWEEP, step52dev9 (seeds 1085-1096, the code
    # graded but for the BLOCKED arm's last edits, measured apart in step52dev10): every 5.2 check below PASSED but BLOCKED's
    # reach (its fix since): the yield CH1 0.985, CH2 0.97, LOAF 0.203; the loafing at most 2,461 a run, LOAF over the bound
    # in 2 of 12; 2 curiosity goals in a row at most, GREEDY 4 in 4 of 4; detours 13 of the 15 that chose a place arrived,
    # the AI's word true in 23 of 23; the longest push 2,051 frames by the AI, 1,960 by the game.
    # THE YIELD: the share of the frames of the curiosity that SEES (a look round, a detour: `SEEING`; the story did not
    # need it) that BROUGHT something (by the game), pooled over each chapter's runs, at least this. (Development sweep
    # step52dev2, seeds 1001-1012, recounted with the rate rule `YIELD_TILE_RATE` over the frames outside battles, the
    # battles' time estimated there from the AI's action digests: CH1 0.85, CH2 0.96, the LOAF control 0.21. With the 8
    # tiles alone LOAF was 0.80 and could not fail, which is why the rate rule exists; over ALL curiosity, chats and catches
    # included, LOAF was 0.54, the real code's chats diluting it: that pooled share is reported, not bounded) ...
    "YIELD_RATE_MIN": 0.6,
    # ... and in EVERY run of the real code, at most this many frames of curiosity that brought nothing, its OWN time
    # outside the battles met in it (CH1M's loaf at OLDALE: about 7,500; step52dev2 recounted as above: the real code
    # 0-2,429 a run, most of it the detours past LITTLEROOT's twin, fixed since; LOAF 226-11,354, over 4,000 in 8 of 12;
    # step52dev4: two catching roams that met only known POKéMON, 25,003 frames, were 80-87 % battles, which are the game
    # played, not loafing, so the battles are taken out, and a catching roam gives the hunt up, `brain/goals.py`
    # HUNT_FRUITLESS) ...
    "LOAF_FRAMES_MAX": 4000,
    # ... while the LOAF control (`EXTRA_EDITS` LOAF: looks round and detours among tiles it has stood on) is under
    # YIELD_RATE_MIN pooled (its looks' own yield: step52dev6 0.31, dev3 0.09 recounted) and over that bound in at least
    # this many of its runs (the per-run bound CAN fail). (First pre-set as a SHARE, 0.5 of the runs, from the span frames;
    # once the loafing was counted outside battles, step52dev6 measured LOAF over it in 3 of 12 runs, 5,374-8,202 frames,
    # the rest 0-3,586: a run with few looks round loafs little whatever its rule, so the per-run bound's control is that
    # it is ever exceeded, and the YIELD carries the separation. Set in development, before any graded run.)
    "LOAF_FAILS_RUNS_MIN": 1,
    # THE SPACING: in EVERY run of the real code, at most this many curiosity goals in a row (the AI's own cap is
    # `CURIOUS_ROW_MAX` 2; the grader reads the goal sequence itself, where a goal DROPPED as it began, a scene starting
    # while it decided, still stands between two: measured 3 once in step52dev2, CH2 seed 1004; CH1M: six in a row) ...
    # (the streak's FRAMES were to be bounded too, 9,000: step52dev2 measured the real code's streaks at up to 30,135
    # frames, one catching roam of 21,000-28,000 frames being ONE goal, so frames measure the roam's battles, not the
    # spacing: REPORTED, not bounded, decided before any graded run)
    "SPACING_ROW_MAX": 3,
    # ... while the GREEDY control (every curiosity draw passes, no cap) is over it in at least this share of its runs
    # (step52dev2: 4 in a row in 4 of 4)
    "GREEDY_FAILS_MIN": 0.5,
    # DETOURS THAT ARRIVE: the share of the detours of the real code's runs that CHOSE a place where the GAME had the player
    # stand at it when they ended, pooled, at least this; and the AI's "reached" / "not reached" agrees with the game in
    # EVERY detour (no bound number: the truth). (step52dev3: 11 of the 16 that chose a place, 69 %; 7 more chose none,
    # "nothing off the way here that it can walk to", and are reported apart; of the 5 that did not arrive, 2 were stopped
    # by LITTLEROOT's twin, a detour now ended at the first scene, and 3 ran out their budget on the way)
    "ARRIVE_MIN": 0.5,
    # THE PUSHING PROPERTY: in EVERY run of the real code the longest free stretch of pressing that brought nothing new
    # (no tile seen, no map stood on, no battle), by the AI's record AND by the game's, under this (frames); the two paths
    # agree on it run by run. (First pre-set at 2,700 from step52dev2. The property then found THREE real loops, each fixed
    # and each its A/B in the README: 114,121 frames (scene walls carried, G229), 3,313 (a walk to a tile past the edge,
    # G268) and 3,372 / 9,261 (a frontier it could not reach kept "left to see", G272, G275). With them fixed, the
    # development sweeps step52dev8 and dev9 (the final code but for G275 in dev8) measured the real code's longest at
    # 1,813 and 2,051 frames by the AI's record (the game's 1,960), every real-code run of both; the longest NOT a loop in
    # any sweep, 3,224 (step52dev3,
    # chapter 2 seed 1023: grass it could not reach on ROUTE 102 with people in the way; the game's path said 720).
    # The bound is above that, and far under the BLOCKED control's 149,668-241,992) ...
    "PUSH_MAX": 4000,
    # ... and the BLOCKED control is over it, by both paths, in at least this many of its runs that MET someone standing in
    # the way of a curiosity walk at least BLOCKED_REACH_HITS times (`person_blocks`), and such a run happens in at least
    # BLOCKED_REACH_MIN of its runs (the control must REACH the state it tests: PF-4)
    "BLOCKED_REACH_HITS": 3,
    "BLOCKED_HITS_MIN": 1,
    "BLOCKED_REACH_MIN": 0.1,
    # ---- BUILD STEP 5.2, THE VERIFIER'S ROUND (2026-10-15): its two failures (the NOHINTS pushing, 20 of 20 graded runs on
    # 901-920; loafing credited as a talk, 127 chats that heard nothing new) are graded by the checks above, unchanged; what
    # changed is the AI and the game's yield of a talk (a message the game never showed before). One new check, set while
    # the round's first development sweep (step52vdev1, which did not grade it) was running, before any run graded it: no
    # run of a plan that goes by what the game says (every real plan but NOHINTS) ends "out of ideas" (`brain/goals.py`
    # lost_intent: a walk with no lead that found nothing left on any map it knows).
    "OUT_OF_IDEAS_LED_MAX": 0,
}
#: (build step 5.3, A1-3: the step-5.3 critic's Q5 item 4) the bounds that were LITERALS inside the verdict code, named so
#: `registered_numbers` hashes them: a literal edited between `--register` and the run moved no registered number before.
#: Each value is the literal it replaces (A1 changes no outcome). (#11 and #17's "b < a" read their BOUNDS keys instead.)
CODE_BOUNDS = {
    "CATCH_ALL_MAX": 0,  # #6 R5.CH1_CATCH_ALL: CH1's stretches standing still under the catch-all reason, at most
    "RECORDER_GAP": (0, 1),  # #9 R5.CH1_RECORDER: the game's battle counter less the recorder's battle ends, within
    "NOTRAIN_LEVEL_WORST": -2,  # #13 R5.NOTRAIN_LEVEL: no seed's CH1 - NOTRAIN strongest level at or under this
    "REST_BREACHES_MAX": 0,  # #8 R5.CH1_REST_RULE and #16's CH1 half: the real code's rest-rule breaches, at most
    "DEADREST_BREACHES_OVER": 0,  # #16 R5.DEADREST: the arm with the fix removed breaches the rest rule MORE than this
}


def plan_of(seed: int) -> tuple[str, str]:
    """The seed's personality and starter: every personality and every starter in turn (seed 1: Story, TREECKO; 2: Catcher,
    TORCHIC; 3: Trainer, MUDKIP; 4: Story, TORCHIC ...), so 9 consecutive seeds play each pair once."""
    index = seed - 1
    return PERSONALITIES[index % 3], STARTERS[(index + index // 3) % 3]


def copy_with(names: list[str]) -> Path:
    """The package copied with these edits applied (`revert_step5.make_copy`: every anchor must occur once): mutants of
    `revert_step5.MUTANTS` and this file's `EXTRA_EDITS`."""
    from ai_player.gates.revert_step5 import make_copy

    edits: list[tuple[str, str, str]] = []
    for name in names:
        edits += edits_of(name)
    return make_copy(edits)


def edits_of(name: str) -> list[tuple[str, str, str]]:
    """(Build step 5.3, A1-3) the edit TEXTS one plan edit applies: this file's `EXTRA_EDITS`, else `revert_step5.MUTANTS`'
    edits. ONE resolver for `copy_with` (what a copy is made with) and `mutant_edits` (what is hashed), so the registered
    texts are the applied texts by construction."""
    if name in EXTRA_EDITS:
        return EXTRA_EDITS[name]
    from ai_player.gates.revert_step5 import MUTANTS

    return MUTANTS[name][2]


def mutant_edits() -> dict[str, list[tuple[str, str, str]]]:
    """(Build step 5.3, A1-3: the step-5.3 critic's Q5 item 1) every edit TEXT a plan's copy is made with
    (`MUTANT_PLANS` and `STOP_PLANS`), by name. Before 5.3 only the NAMES were hashed, so an edit of G36's text in
    `revert_step5.py` changed what DEADREST plays with no change to the registered numbers."""
    names = {name for table in (MUTANT_PLANS, STOP_PLANS) for names in table.values() for name in names}
    return {name: edits_of(name) for name in sorted(names)}


def run_one(plan: str, seed: int, frames: int, target: str, root: Path = REPO, base: str | None = None,
            start: dict | None = None) -> dict:
    """One run of `plan` (a phase-2 STOP plan replays the run of plan `base`: its faults, in the copy `root`). (The step-5.1
    verifier's second round) every run saves its end state in its folder (`_end_state`, beside `world.jsonl`); a
    chapter-2 run (`CHAPTER2`) starts from `start`, the chapter-1 row it goes on from: its end state and world memory, the
    same seed, personality and starter."""
    personality, starter = plan_of(seed)
    # (build step 5.2, G1) the frozen-tree watch before the run: once the tree moved, no run is played on it
    if _TREE is not None and (_TREE.moved or not _TREE.check(f"before run {plan}{'(' + base + ')' if base else ''} seed {seed}")):
        return {"plan": plan, "seed": seed, "base": base, "skipped": True,
                "error": f"skipped: the tree changed mid-run ({_TREE.moves[0][:300]})"}
    prefix = f"ai_step5_{plan}{'_' + base if base else ''}_{seed}_"
    # (build step 5.2, G5) under the sweep's one root, deleted after grading (`SweepFolders.tidy`)
    folder = _FOLDERS.new(prefix) if _FOLDERS is not None else Path(tempfile.mkdtemp(prefix=prefix))
    fault = PLANS[base or plan]
    harness = root / "ai_player" / "gates" / "play_harness.py"
    begin = (["--state", start["_end_state"], "--world-in", start["_world"]] if start is not None
             else ["--fresh", "--starter", starter])
    if start is not None and start.get("_seen"):
        # (build step 5.2) the tiles its chapter 1's screen showed are no new tiles in chapter 2 (the game's second path)
        begin += ["--seen-in", start["_seen"]]
    command = [sys.executable, str(harness), *begin, "--seed", str(seed), "--frames", str(frames), "--personality",
               personality, "--target", target, "--game-clock", GAME_CLOCK, "--clock", WALL_CLOCK,
               "--run-dir", str(folder), "--save-end", str(folder / "end_state.ss1")] + (["--fault", fault] if fault else [])
    began = time.monotonic()
    env = {**os.environ, "PYTHONUTF8": "1"}
    if root != REPO:
        from ai_player.host.launcher import ENV_BUILD_ROOT, resolve_build_root

        env.update({ENV_BUILD_ROOT: str(resolve_build_root(None)), "PYTHONDONTWRITEBYTECODE": "1"})
    result = subprocess.run(command, cwd=str(root), capture_output=True, timeout=7200, env=env)
    if _TREE is not None:
        _TREE.check(f"after run {plan}{'(' + base + ')' if base else ''} seed {seed}")  # (G1) the verdict seals it
    text = result.stdout.decode("utf-8", errors="replace")
    line = next((l for l in text.splitlines() if l.startswith("PLAY ")), None)
    if line is None:
        return {"plan": plan, "seed": seed, "base": base, "_folder": str(folder),
                "error": (text + result.stderr.decode("utf-8", errors="replace"))[-2000:]}
    data = json.loads(line[5:])
    actions = []
    path = folder / "actions.jsonl"
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            try:
                actions.append(json.loads(raw))
            except json.JSONDecodeError:
                pass
    earlier = (start or {}).get("_reads") or []
    row = grade_run(plan, seed, personality, starter, data, actions, time.monotonic() - began, earlier=earlier,
                    world_in=(start or {}).get("_world"), seen_in=(start or {}).get("_seen"))
    # (build step 5.3, A1-1: critic Q1 on #40) the run's frame budget: a run that ended under it ended by itself
    row["budget"] = frames
    row.update({"_end_state": data.get("saved_end"), "_world": data.get("world_file"), "_folder": str(folder),
                "_reads": earlier + [r for r in actions if r.get("decision") == "read"], "_seen": data.get("seen_file")})
    return {**row, "base": base} if base else row


def run_chain(plan: str, seed: int, frames: int, target: str, root: Path, chapter2: list[str]) -> list[dict]:
    """(the step-5.1 verifier's second round) One run of `plan` and, for every chapter-2 plan of `chapter2` that goes on
    from it (`CHAPTER2`), that plan's run from ITS end state, when it reached the POKéDEX (by the game's flag): played one
    after the other in the same worker, so the chapter-2 runs start as soon as their chapter 1 ends."""
    rows = [run_one(plan, seed, frames, target, root)]
    first = rows[0]
    for follow in chapter2:
        if "error" not in first and first.get("reached") and first.get("_end_state") and first.get("_world"):
            rows.append(run_one(follow, seed, frames, CH2_TARGET, REPO, start=first))
        else:
            rows.append({"plan": follow, "seed": seed, "error": f"its chapter 1 ({plan}) did not reach the POKéDEX or left "
                                                                f"no end state: {first.get('reason') or first.get('error')}"
                                                                [:400], "skipped": True})
    return rows


def train_steps_min(personality: str) -> int:
    """(the step-5.1 verifier's round: the bound RE-DERIVED) The training steps a CH1 run of `personality` must have
    roamed before the rival: its own `train_min_steps` times `CH1_TRAIN_STEPS_SHARE`, never under `CH1_TRAIN_STEPS_MIN`."""
    import math

    errands = ERRANDS.get(personality, ERRANDS["Story"])
    return max(BOUNDS["CH1_TRAIN_STEPS_MIN"], math.ceil(errands.train_min_steps * BOUNDS["CH1_TRAIN_STEPS_SHARE"]))


def train_steps_min_run(row: dict) -> int:
    """The training-steps bound of ONE run: the lowest `train_steps_min` among the personalities it played AS during the
    rival's milestone (`rival_actives`: the ACTIVE personality of its goals there, `personality.py` DRIFT included), its
    base personality's when none is recorded. (CORRECTED 2026-10-14 after the graded sweep on seeds 501-520 FAILED it in 2
    of 20 runs, 506 and 516: both had DRIFTED into the Story personality during that milestone, and a person trains to
    the minimum of the personality it is acting as, 80 for the Story; the bound had been taken from the BASE personality.
    That sweep's evidence is kept, `evidence/archive/dee96b6ddadb6b11/`; the corrected bound is graded on new seeds.)"""
    # (the step-5.1 verifier's second round: "it is still the loosest reading, because which personality judged the run
    # 'trained' is not logged") the personality whose rule JUDGED it trained, now logged (`brain/goals.py` fight_prep
    # `judged_by`): its own minimum; the lowest of those it played as only for a log without it
    if row.get("rival_judge"):
        return train_steps_min(row["rival_judge"])
    actives = [p for p in row.get("rival_actives") or [] if p]
    return min(train_steps_min(p) for p in actives or [row.get("personality") or "Story"])


def trained_by_game(row: dict) -> bool:
    """THE TRAINED CHECK by the game (the step-5 verifier's round 2): inside the windows its log says it roamed to train
    before the rival's flag, the game's step counter rose at least the run's `train_steps_min_run` (the step-5.1
    verifier's round: re-derived, and corrected for DRIFT) and the game says at least `CH1_WILD_WON_MIN` wild battles were
    WON."""
    return (row.get("game_train_steps") or 0) >= train_steps_min_run(row) \
        and (row.get("game_train_won") or 0) >= BOUNDS["CH1_WILD_WON_MIN"]


def stop_verdicts(rows: dict[str, list[dict]]) -> list[Check]:
    """PHASE 2 (`STOP_PLANS`): the MAX_LOSSES stop, end to end in the game, and the arm with the loop's count removed.
    (Build step 5.3) HONESTY checks: the AI's reason and counts judged against the game's losses and the harness's frames."""
    out: list[Check] = []
    if "STOP" not in rows and "STOPDEAD" not in rows:
        return out
    bases = {(r["plan"], r["seed"]): r for plan, plan_rows in rows.items() if plan in PLANS and plan not in NO_PHASE2
             for r in plan_rows if "error" not in r}
    lost = sorted(key for key, r in bases.items() if r["losses_game"])
    for plan in ("STOP", "STOPDEAD"):
        if plan not in rows:
            continue
        played = [r for r in rows[plan] if "error" not in r]
        bad, lines = [], []
        for r in played:
            base = bases.get((r.get("base"), r["seed"]))
            after = r["frames"] - r["first_loss_f"] if r["first_loss_f"] is not None else None
            same = base is not None and base["first_loss_f"] == r["first_loss_f"]
            if plan == "STOP":
                ok = (r["reason"] == STOP_REASON and r["losses_game"] == 1 and r["losses_told"] == 1 and r["losses_ai"] == 1
                      and after is not None and 0 <= after <= STOP_WITHIN)
            else:
                ok = (r["reason"] != STOP_REASON and r["losses_game"] >= 1 and r["losses_ai"] == 0 and r["losses_told"] == 0
                      and after is not None and after > STOP_WITHIN)
            lines.append((r.get("base"), r["seed"], r["reason"], f"first loss f{r['first_loss_f']} (the base run's "
                          f"f{base['first_loss_f'] if base else '?'}: {'the same' if same else 'NOT the same'})",
                          f"ended {after} frames after it", f"losses report/told/game {r['losses_ai']}/{r['losses_told']}/"
                          f"{r['losses_game']}"))
            if not ok:
                bad.append((r.get("base"), r["seed"]))
        if plan == "STOP":
            text = (f"STOP (MAX_LOSSES 1 in a copy; every run of phase 1 the GAME recorded a loss in, replayed): each must "
                    f"end '{STOP_REASON}' within {STOP_WITHIN} frames of the game's record of its loss, told once, the "
                    f"game's losses 1")
        else:
            text = (f"STOPDEAD (MAX_LOSSES 1 AND the loop's count removed, revert_step5 G46): each must NOT stop there, "
                    f"going on past {STOP_WITHIN} frames, its report and told losses 0 while the game lost (the ALL PLANS "
                    f"check would catch it)")
        # (build step 5.3) n = phase 1's runs with a loss: none is VACUOUS (it was a FAIL "NONE (not exercised)")
        out.append(grade(f"R5.{plan}", bool(lost) and len(played) == len(lost) and not bad,
                    f"{text}: phase 1's runs with a loss {lost or 'NONE (not exercised)'}; played {len(played)}: {lines}; "
                    f"off: {bad or 'none'}", len(lost), 1))
    return out


def first_change(changes: list[dict], mark: str, to: int = 1) -> dict | None:
    return next((c for c in changes if c["mark"] == mark and c["to"] >= to), None)


def training_windows(actions: list[dict], fight: str = "ch1_rival_route103") -> list[tuple[int, int]]:
    """(the step-5 verifier's round 2) Where the AI's log says it was ROAMING TO TRAIN for `fight`: (first frame, last
    frame) of every roam of a `train` goal for it, from the roam's start ("roam N steps", after the walk to the grass) to
    its metrics record (a roam that ran out, or one a rest or an item ball stopped), else to the goal's last record. The
    GAME's counts inside them (`training_by_game`) are what tells training from none."""
    windows: list[tuple[int, int]] = []
    goal, start, last = None, None, None
    for r in actions:
        frame = r.get("frame")
        if r.get("decision") == "goal":
            if start is not None:
                windows.append((start, last))
            goal, start = r, None
            continue
        if frame is not None:
            last = frame
        if goal is None or goal.get("action") != "train" or (goal.get("extra") or {}).get("milestone") != fight:
            continue
        if r.get("decision") == "decide" and str(r.get("action", "")).startswith("roam ") and frame is not None:
            start = frame
        elif start is not None and r.get("decision") == "roam" and r.get("action") == "metrics":
            windows.append((start, last))
            start = None
    if start is not None:
        windows.append((start, last))
    return windows


def training_by_game(windows: list[tuple[int, int]], story: dict, offset: int, until: int | None) -> dict:
    """THE GAME's counts inside the AI's training windows (`training_windows`, its log's frames less `offset`, the frame of
    its first look: the recorder counts from the run's first frame) that began before frame `until` (the rival's flag): the
    steps its own counter rose (`play_harness.steps_counted`) and the wild battles it says were WON (gBattleOutcome 1 with
    no trainer flag), each ended inside a window (the recorder samples every `every` frames: that much slack after it)."""
    from ai_player.gates.play_harness import steps_counted

    every = story.get("every") or 30
    timeline = story.get("steps") or []
    steps = refused = 0
    won = []
    for start, end in windows:
        start, end = start - offset, end - offset
        if until is not None and start > until:
            continue
        counted, bad = steps_counted(timeline, start, end)
        steps += counted
        refused += bad
        won += [b["f"] for b in story.get("battles") or [] if not b["trainer"] and b["outcome"] == 1
                and start <= b["f"] <= end + every]
    return {"windows": len([w for w in windows if until is None or w[0] - offset <= until]), "steps": steps,
            "won": len(won), "refused": refused}


def roam_breaches(actions: list[dict]) -> tuple[list[tuple], int]:
    """(the step-5 verifier's DEAD FIX, 2026-10-14) From the AI's action log: every battle a TRAINING or CATCHING roam
    played AFTER an earlier battle of the same roam had ended with the party under the active personality's `heal_below`
    (the rest rule says the roam stops there, to heal), and how many battles ended under it in a roam (the opportunities:
    a check with none is vacuous). A roam begins at its "roam N steps" record and ends at the next goal; the walk to the
    grass before it is travel (no rest is asked there). (5.3 A1-2) `heal_below` is the grader-owned `ERRANDS`."""
    breaches, low_ends = [], 0
    goal, roaming, low = None, False, None
    for r in actions:
        if r.get("decision") == "goal":
            goal, roaming, low = r, False, None
            continue
        if goal is None or goal.get("action") not in ("train", "catch"):
            continue
        if r.get("decision") == "decide" and str(r.get("action", "")).startswith("roam "):
            roaming = True
            continue
        extra = r.get("extra") or {}
        if not roaming or r.get("decision") != "world" or "kind" not in extra:
            continue
        if low is not None:
            breaches.append((r.get("frame"), low, extra.get("outcome")))
        hp = extra.get("party_hp_end") or [0, 0]
        active = (goal.get("extra") or {}).get("active") or "Story"
        heal_below = ERRANDS[active].heal_below
        if hp[1] and hp[0] / hp[1] < heal_below and extra.get("outcome") != "lost":
            low_ends += 1
            low = f"f{r.get('frame')} ended at {hp[0]}/{hp[1]} (under the {active}'s {heal_below:.0%})"
    return breaches, low_ends


def await_stretches(actions: list[dict]) -> list[dict]:
    """(build step 5.1, the step-5 verifier's FAILURE) The AI's own record of every stretch a screen WAITED FOR A PRESS with
    none (`hands/waiting.py`: the eyes' look, never the busy reason it gave), `NOTE_FRAMES` or longer: [{frames, first,
    what, doing}]."""
    return [{"frames": (r.get("extra") or {}).get("frames", 0), "first": (r.get("extra") or {}).get("first"),
             "what": (r.get("extra") or {}).get("what"), "doing": (r.get("extra") or {}).get("doing")}
            for r in actions if r.get("decision") == "await"]


#: (the step-5.1 verifier's second round) frames after a goal's END record within which a milestone record is that goal's
#: (`goal_spans`): the loop's next pass reads the marks with no frame passing; 60 is room for a settle look
END_SLACK = 60


def goal_spans(actions: list[dict]) -> list[dict]:
    """(build step 5.1) Every goal the AI chose, with the frames it lasted: [{kind, key, frames, frame, map, story_moved,
    gap}] from the action log's goal records (the same in a live run and in the sweep). A goal lasts to its END record
    (`goal_end`, the play loop's, the step-5.1 verifier's second round: a goal DROPPED because a scene began while it decided
    was graded as the 11,019 frames of WALLY's scene that followed it in CH2T), else (a log without them) to the next goal or
    the run's last record; `gap`: the frames after its end that were no goal's (a scene the loop played, the settling).
    `story_moved` (the verifier's round): a milestone record came while it was the goal (in the log's order, after its
    record and before its end): the STORY moved on in it (the rival's POKé BALL picked up plays the rival's scene)."""
    goals = [r for r in actions if r.get("decision") == "goal"]
    end = max((r.get("frame") or 0 for r in actions if isinstance(r.get("frame"), int)), default=0)
    moved: list[bool] = []
    ends: list[int | None] = []
    for r in actions:
        if r.get("decision") == "goal":
            moved.append(False)
            ends.append(None)
        elif r.get("decision") == "goal_end" and ends and ends[-1] is None:
            ends[-1] = r.get("frame") if isinstance(r.get("frame"), int) else None
        elif r.get("decision") == "milestone" and moved:
            # the play loop writes a milestone's record on its next pass, right after the goal it passed in ended (no frame
            # passes between): a milestone within `END_SLACK` frames of the goal's end is the goal's; one a scene played
            # long after the goal ended is not (CH2T's dropped chat and WALLY's tutorial)
            frame = r.get("frame")
            if ends[-1] is None or (isinstance(frame, int) and frame <= ends[-1] + END_SLACK):
                moved[-1] = True
    out = []
    for this, nxt, story_moved, ended in zip(goals, goals[1:] + [None], moved, ends):
        start = this.get("frame") or 0
        following = (nxt.get("frame") or start) if nxt is not None else end
        stop = min(max(ended, start), following) if ended is not None else following
        extra = this.get("extra") or {}
        out.append({"kind": this.get("action"), "key": extra.get("key") or "", "frames": max(0, stop - start),
                    "frame": start, "map": extra.get("map"), "active": extra.get("active"), "story_moved": story_moved,
                    "gap": max(0, following - stop)})
    return out


def intent_mix(actions: list[dict], unproductive: set | None = None) -> dict:
    """(build step 5.1, the step-5 review's finding 1; design draft §7 "intent mix (time in explore, catch, train, story)")
    The share of the goals' FRAMES (and of their count) spent on ERRANDS (`brain/goals.py` ERRAND_KINDS: heal, shop, train,
    catch, an item, chat, looking around a new place, a detour) rather than the story's own steps. (The step-5.1 verifier's
    second round) a goal's frames end at its END record (`goal_spans`): what the loop played after a goal ended (a scene)
    is no goal's frames (`between_goals`, reported); and a curiosity goal the story moved on in is the story's, in the
    errand share as in the curiosity the story did not need (`story_own`). (Build step 5.2, the step-5.1 review's finding
    1: "`intent_mix` counts curiosity frames by goal kind, not by what the goal produced") `unproductive`: the frames (the
    goal records' frames) of the curiosity goals that BROUGHT nothing (`curiosity_rows`: by the GAME in the sweep, by the
    AI's own record in a live run): their frames are IDLE (`idle_frames`), neither errand nor curiosity, though still in
    the total. (5.3 A1-2) ERRAND_KINDS is the grader-owned copy."""
    spans = goal_spans(actions)
    frames: dict[str, int] = {}
    for span in spans:
        frames[span["kind"]] = frames.get(span["kind"], 0) + span["frames"]
    total = sum(frames.values())
    curious = sum(v for k, v in frames.items() if k in CURIOSITY_KINDS)
    # (the verifier's round: "the pick_up is the rival's POKé BALL, a step the story requires; it counts as curiosity in
    # BOTH arms") CURIOSITY THE STORY DID NOT NEED: a curiosity goal in which the story moved on is the story's own
    story_own = [(s["frame"], s["kind"], s["frames"]) for s in spans if s["kind"] in CURIOSITY_KINDS and s["story_moved"]]
    free = curious - sum(f for _, _, f in story_own)
    # (the step-5.1 verifier's second round: "MIX_MIN counts story-owned curiosity goals as errands") the ERRAND share
    # counts them as the story's too: a goal the story moved on in was the story's time, whatever its kind
    errand = sum(v for k, v in frames.items() if k in ERRAND_KINDS) - sum(f for _, _, f in story_own)
    # (build step 5.2) a curiosity goal that brought nothing is IDLE time: no errand, no curiosity
    idle = sum(s["frames"] for s in spans if s["kind"] in CURIOSITY_KINDS and not s["story_moved"]
               and unproductive is not None and s["frame"] in unproductive)
    curious, free, errand = curious - idle, free - idle, errand - idle
    count = sum(1 for s in spans if s["kind"] in ERRAND_KINDS)
    between = sum(s["gap"] for s in spans)
    return {"frames": dict(sorted(frames.items())), "errand_share": round(errand / total, 4) if total else 0.0,
            # (reported, not bounded) the same with the scenes the loop played between goals counted as the story's time
            "errand_share_with_scenes": round(errand / (total + between), 4) if total + between else 0.0,
            "errand_frames": errand, "curiosity_share": round(curious / total, 4) if total else 0.0,
            "free_share": round(free / total, 4) if total else 0.0, "free_frames": free, "story_own": story_own,
            "errand_goals": count, "goals": len(spans), "between_goals": between, "idle_frames": idle,
            "total_frames": total, "kinds": sorted({s["kind"] for s in spans if s["kind"] in ERRAND_KINDS})}


# ---------------------------------------------------------------------- build step 5.2: productive curiosity
#: (build step 5.2) the fewest NEW tiles a curiosity goal's span must show on the GAME's screen to be productive by its
#: tiles alone: the graders' own number, written here (the AI's is `brain/goals.py` YIELD_TILES_MIN; a check must not
#: read the code it grades: CLAUDE.md, the lessons' PF-6)
YIELD_TILES = 8
#: ... and, for a look round or a detour (`SEEING`: walks whose purpose is to see), at least this many per 1,000 frames of
#: its span OUTSIDE the game's battles (the graders' own number again; set from the development sweep step52dev2, where
#: with the 8 tiles alone the LOAF control's yield was 80 %: its looks round showed 0-11 new tiles per 1,000 frames outside
#: battles but for a few short ones, the real code's 14 and more)
YIELD_TILE_RATE = 20
SEEING = ("explore", "detour")
#: (build step 5.2) frames of slack after a goal's end in which the game's second-path samples still count as its (the
#: samples are 10 frames apart, the AI's frame offset may lag one look)
YIELD_SLACK = 30


def _timeline_rise(timeline: list[list[int]] | None, start: int, end: int) -> int:
    """How much a [frame, value] timeline (changes only) rose between frames `start` and `end`."""
    before = after = None
    for frame, value in timeline or ():
        if frame <= start:
            before = value
        if frame <= end:
            after = value
    if before is None or after is None:
        return 0
    return max(0, after - before)


def game_yield(places: dict | None, story: dict | None, start: int, end: int, kind: str = "") -> dict:
    """(build step 5.2) What the GAME says a goal's span [`start`, `end`] (the recorder's frames) BROUGHT: tiles its screen
    showed for the first time and maps first stood on (`play_harness.PlaceRecorder`), captures and item balls (the game's
    counters and flags, `play_harness.StoryRecorder`), and a talk (a text or a script that waited for A/B on the
    overworld, since the verifier's round only one that showed a PAGE the game had not shown before in the run; by whole
    MESSAGE before its second round);
    `productive` by the graders' own `YIELD_TILES` (and, for a goal of a `SEEING` `kind`, `YIELD_TILE_RATE`
    per 1,000 frames of the span outside the game's battles, `PlaceRecorder` battles). Never the AI's own reads."""
    places = places or {}
    end_s = end + YIELD_SLACK
    tiles = sum(n for frame, n in places.get("new_tiles") or () if start < frame <= end_s)
    first: dict[str, int] = {}
    for frame, stay in places.get("stays") or ():
        first.setdefault(stay, frame)
    maps = sum(1 for stay, frame in first.items() if start < frame <= end_s and frame != (places.get("stays") or [[0]])[0][0])
    caught = _timeline_rise((story or {}).get("captures"), start, end_s)
    items = _timeline_rise((story or {}).get("item_flags"), start, end_s)
    # a talk BEGUN in the span (a text still on screen from the goal before is not this goal's: measured on the development
    # smoke run of seed 1001, a 17-frame chat right after another was credited with the first one's text); (build step 5.2,
    # the verifier's round: "the game's second path credits ANY text begun in a goal's span as a talk", the nurse's welcome
    # right after a heal, a scripted stop met again) that showed a PAGE the game had never shown before in the run (the
    # recorder's third field: `play_harness.PlaceRecorder` pages; a record without it is no talk). (The verifier's second
    # round: whole messages were compared, so OLDALE's footprints man's talk, the last two pages of his own scene, was
    # credited 20 times while the AI's own record, and the verifier's page-by-page recount, said it told nothing new)
    talked = any(start <= text[0] <= end_s and len(text) > 2 and bool(text[2]) for text in places.get("texts") or ())
    # the span's OWN time: less the stretches the game was in a battle (each sample stands for `every` frames)
    every = int(places.get("every") or 10)
    battle = sum(max(0, min(end, b + every) - max(start, a)) for a, b in places.get("battles") or ())
    walking = max(0, end - start - battle)
    seen = tiles >= YIELD_TILES and (kind not in SEEING or tiles * 1000 >= YIELD_TILE_RATE * walking)
    return {"tiles": tiles, "maps": maps, "caught": caught, "items": items, "talked": talked, "walking": walking,
            "productive": bool(seen or maps or caught or items or talked)}


def loafing_frames(curious: list[dict]) -> int:
    """(build step 5.2) The LOAFING of a run (`curiosity_rows`): the curiosity goals' OWN time, outside the battles the game
    had in them (`walking`), where the game says they brought nothing. (The round's development sweep step52dev4: catching
    roams that met only known POKéMON were 80-87 % battles, which are the game played, not loafing.)"""
    return sum(row["walking"] for row in curious if not row["game"])


def position_at(places: dict | None, frame: int) -> tuple[str, int, int] | None:
    """(build step 5.2) Where the GAME had the player at `frame` (the recorder's frames): (map "group:number", x, y)."""
    where = None
    for at, stay, x, y in (places or {}).get("moves") or ():
        if at > frame:
            break
        where = (stay, x, y)
    return where


def curiosity_rows(actions: list[dict], data: dict, offset: int) -> list[dict]:
    """(build step 5.2, the step-5.1 review's findings 1 and 3) Every CURIOSITY goal of a run that the story did not need,
    with what it brought by the AI's own record (its END record's `yield`) and by the GAME (`game_yield` over its span, the
    AI's frames less `offset`); for a DETOUR, the place it chose (its yield's `place`), whether it SAID it reached it (its
    outcome: "reached ...") and whether the GAME had the player standing there when it ended (`position_at`)."""
    ends = {}
    goal_frames: list[int] = []
    for r in actions:
        if r.get("decision") == "goal":
            goal_frames.append(r.get("frame") or 0)
        elif r.get("decision") == "goal_end" and goal_frames:
            ends.setdefault(goal_frames[-1], r)
    rows = []
    places, story = data.get("places") or {}, data.get("story") or {}
    for span in goal_spans(actions):
        if span["kind"] not in CURIOSITY_KINDS or span["story_moved"]:
            continue
        end = ends.get(span["frame"]) or {}
        mine = (end.get("extra") or {}).get("yield") or {}
        if mine.get("dropped"):
            continue
        start, stop = span["frame"] - offset, span["frame"] + span["frames"] - offset
        game = game_yield(places, story, start, stop, span["kind"])
        # (step52dev4) its OWN time too, outside the battles met in it, by each path: a catching roam is 80-87 % battles
        row = {"kind": span["kind"], "frame": span["frame"], "frames": span["frames"], "ai": bool(mine.get("productive")),
               "game": game["productive"], "tiles_game": game["tiles"], "tiles_ai": mine.get("tiles"),
               "walking": game["walking"], "walking_ai": mine.get("walking", span["frames"]),
               # (the verifier's second round: "counted by both paths" was written of a talk neither path's verdict was
               # read for) a talk by each path: the AI had one (`talks`), it told something new (`talked`), the game's
               "talks_ai": bool(mine.get("talks")), "talked_ai": bool(mine.get("talked")), "talked_game": bool(game["talked"])}
        if span["kind"] == "detour":
            place = mine.get("place")
            said = str(end.get("reason") or "").startswith("reached")
            stood = position_at(places, stop + YIELD_SLACK)
            there = bool(place) and stood is not None and stood[0] == place[0] and (stood[1], stood[2]) == (place[1], place[2])
            row.update({"place": place, "said_reached": said, "game_reached": there,
                        "game": game["productive"] and there})
        rows.append(row)
    return rows


def curiosity_streaks(actions: list[dict]) -> list[tuple[int, int, int]]:
    """(build step 5.2, the step-5.1 review's finding 2: "it ran six curiosity goals in a row") Every STREAK of curiosity
    goals with no story or need goal between (a goal dropped for a scene neither ends nor joins one; a curiosity goal the
    story moved on in is the story's): (first frame, goals in it, frames from its first goal's start to its last's end)."""
    out, streak = [], []
    for span in goal_spans(actions):
        if span["kind"] in CURIOSITY_KINDS and not span["story_moved"]:
            streak.append(span)
            continue
        if streak:
            out.append((streak[0]["frame"], len(streak), streak[-1]["frame"] + streak[-1]["frames"] - streak[0]["frame"]))
            streak = []
    if streak:
        out.append((streak[0]["frame"], len(streak), streak[-1]["frame"] + streak[-1]["frames"] - streak[0]["frame"]))
    return out


def push_ai(actions: list[dict]) -> int:
    """(build step 5.2) The longest free stretch of pressing that brought nothing new, by the AI's own record
    (`hands/waiting.py` PushWatch: its end record's `pushes`, and every stretch it noted)."""
    end = next(((r.get("extra") or {}).get("pushes") or {} for r in reversed(actions) if r.get("decision") == "end"), {})
    noted = [(r.get("extra") or {}).get("frames", 0) for r in actions if r.get("decision") == "push"]
    return max([int(end.get("longest") or 0)] + noted)


def person_blocks(actions: list[dict]) -> int:
    """(build step 5.2, the BLOCKED arm's REACH) The most times, in one curiosity goal, the navigator met someone in the
    way of where it walked ("someone stands in the way ...", "someone is in the way at ...": the pad's idle records)."""
    most, count, inside = 0, 0, False
    for r in actions:
        if r.get("decision") == "goal":
            inside, count = r.get("action") in CURIOSITY_KINDS, 0
            continue
        reason = str(r.get("reason") or "")
        if inside and r.get("decision") == "idle" and ("someone stands in the way" in reason
                                                       or "someone is in the way at" in reason):
            count += 1
            most = max(most, count)
    return most


#: (build step 5.1) The errands a person does out of CURIOSITY, not need (no heal, shop or training: those the beeline
#: control keeps too): looking round a new place, a detour off the way, a chat, a catching roam, an item ball
CURIOSITY_KINDS = ("explore", "detour", "chat", "catch", "pick_up")


#: (build step 5.1) the NEEDS: errands the beeline control keeps too, whose length is the battles' dice
NEED_KINDS = ("train", "heal", "find_center", "shop")


def time_to_dex(actions: list[dict], milestone: str = "ch1_pokedex", since_start: bool = False) -> dict | None:
    """(the step-5.1 verifier's round: "the NO SPEEDRUN margin is within noise") The run's way to `milestone` in the AI's
    own frames (its log's MILESTONE line), split: the frames of its NEEDS goals (`NEED_KINDS`), and the frames a BATTLE was
    on screen outside them (the action digests' screen: the number and length of the battles met on a walk are the grass's
    dice, which swung the frames outside the needs by up to 37,000 in the development sweep step51vdev2). `outside_nb`:
    the frames outside the needs AND outside those battles, the AI's own walking, talking and looking. None: never
    reached."""
    end = next((r.get("frame") for r in actions if r.get("decision") == "tell"
                and f"MILESTONE {milestone} done at f" in str(r.get("reason"))), None)
    if end is None:
        return None
    spans = [s for s in goal_spans(actions) if s["frame"] < end]
    need_iv = [(s["frame"], min(s["frame"] + s["frames"], end)) for s in spans if s["kind"] in NEED_KINDS]
    need = sum(b - a for a, b in need_iv)
    timed = sorted((r["frame"], str(r.get("digest") or "")) for r in actions if isinstance(r.get("frame"), int))
    battle = 0
    for (frame, digest), (after, _) in zip(timed, timed[1:]):
        if frame >= end:
            break
        stop = min(after, end)
        if digest.split(" ")[1:2] == ["battle"] and stop > frame:
            inside = sum(max(0, min(stop, b) - max(frame, a)) for a, b in need_iv)
            battle += (stop - frame) - inside
    # (the step-5.1 verifier's second round) a chapter-2 run starts where its chapter 1 stopped: its way is counted from its
    # first record (`since_start`); chapter 1's from frame 0, as registered
    begin = (timed[0][0] if timed else 0) if since_start else 0
    return {"end": end, "begin": begin, "needs": need, "battles": battle, "outside": end - begin - need,
            "outside_nb": end - begin - need - battle}


def needs(row: dict) -> int:
    """The frames a run's goals spent on NEEDS (`NEED_KINDS`), from its intent mix."""
    return sum(frames for kind, frames in (row.get("mix") or {}).get("frames", {}).items() if kind in NEED_KINDS)


def goal_sequence(actions: list[dict], first: int = 60) -> list[str]:
    """The first `first` goals as `kind@map they were chosen on`: what the run DID, in order (the divergence metric)."""
    seq, here = [], "?"
    for r in actions:
        if r.get("decision") == "world" and str(r.get("reason", "")).startswith("MAP "):
            here = str(r.get("reason")).split(" -> ", 1)[1].split(" at ", 1)[0] if " -> " in str(r.get("reason")) else here
        if r.get("decision") == "goal":
            seq.append(f"{r.get('action')}@{here}")
            if len(seq) >= first:
                break
    return seq


def aside_streaks(actions: list[dict]) -> list[tuple[str, int, int, int]]:
    """(the step-5.1 verifier's round: "in CH2, 10 look_around goals in a row (about 32,000 frames) passed while the walk to
    PETALBURG waited out its cooldown") Every STREAK of goals put aside for one story goal (the goal manager's `aside:` key,
    `brain/goals.py` ASIDE): (the story goal's key, the first aside's frame, the frames until the next goal that is not that
    aside, how many asides in a row). (5.3 A1-2) ASIDE is the grader-owned copy."""
    spans = goal_spans(actions)
    out, i = [], 0
    while i < len(spans):
        key = spans[i]["key"]
        if not key.startswith(ASIDE):
            i += 1
            continue
        j = i
        while j < len(spans) and spans[j]["key"] == key:
            j += 1
        last = spans[j - 1]
        out.append((key[len(ASIDE):], spans[i]["frame"], last["frame"] + last["frames"] - spans[i]["frame"], j - i))
        i = j
    return out


def curiosity_sequence(actions: list[dict]) -> list[str]:
    """(the step-5.1 verifier's round) The ERRANDS' OWN decisions in order: every curiosity goal the story did not need
    (`intent_mix`'s free ones) as `kind@map it was chosen on`. The beeline control has none."""
    spans = iter(goal_spans(actions))
    seq, here = [], "?"
    for r in actions:
        if r.get("decision") == "world" and str(r.get("reason", "")).startswith("MAP "):
            here = str(r.get("reason")).split(" -> ", 1)[1].split(" at ", 1)[0] if " -> " in str(r.get("reason")) else here
        if r.get("decision") == "goal":
            span = next(spans, None)
            if span is not None and span["kind"] in CURIOSITY_KINDS and not span["story_moved"]:
                seq.append(f"{r.get('action')}@{here}")
    return seq


def sequence_divergence(rows: list[dict], key: str) -> dict:
    """The mean, over every pair of runs of one personality, of the edit distance of their `key` sequences over the
    longer one's length (two empty sequences: 0, the same); and the pairs that are the same."""
    pairs = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a["personality"] != b["personality"]:
                continue
            longest = max(len(a[key]), len(b[key]))
            pairs.append({"seeds": [a["seed"], b["seed"]],
                          "distance": round(edit_distance(a[key], b[key]) / longest, 3) if longest else 0.0})
    return {"pairs": pairs, "mean": round(sum(p["distance"] for p in pairs) / len(pairs), 3) if pairs else None,
            "same": [p["seeds"] for p in pairs if p["distance"] == 0]}


def edit_distance(a: list[str], b: list[str]) -> int:
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (x != y))
    return row[-1]


def visited_tiles(world_file: str | None) -> set[str]:
    """Every tile the AI stood on (its world memory's last snapshot: `world.jsonl`), as `MAP x,y`: the run's PATH."""
    if not world_file or not Path(world_file).is_file():
        return set()
    lines = [line for line in Path(world_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return set()
    data = json.loads(lines[-1])
    out = set()
    for memory in (data.get("maps") or {}).values():
        const = memory.get("const") or memory.get("name") or "?"
        out.update(f"{const} {xy}" for xy in (memory.get("visits") or {}))
    return out


def divergence(rows: list[dict]) -> dict:
    """(build step 5.1, design draft §7: "run-to-run divergence for different seeds"; §5 pillar 5 "two runs with different
    seeds must differ") For every PAIR of runs of one PERSONALITY: the edit distance of their goal sequences over the
    longer one's length (0 the same decisions in the same order, 1 nothing alike) and the Jaccard distance of the tiles
    they stood on (0 the same path, 1 no tile shared)."""
    pairs = []
    ok = [r for r in rows if "error" not in r and r.get("_sequence") is not None]
    for i, a in enumerate(ok):
        for b in ok[i + 1:]:
            if a["personality"] != b["personality"]:
                continue
            longest = max(len(a["_sequence"]), len(b["_sequence"]), 1)
            goals = edit_distance(a["_sequence"], b["_sequence"]) / longest
            union = a["_tiles"] | b["_tiles"]
            tiles = 1 - len(a["_tiles"] & b["_tiles"]) / len(union) if union else 0.0
            pairs.append({"seeds": [a["seed"], b["seed"]], "personality": a["personality"], "goals": round(goals, 3),
                          "tiles": round(tiles, 3)})

    def mean(key: str) -> float | None:
        return round(sum(p[key] for p in pairs) / len(pairs), 3) if pairs else None

    return {"pairs": pairs, "goals_mean": mean("goals"), "tiles_mean": mean("tiles"),
            "identical": [p["seeds"] for p in pairs if p["goals"] == 0 or p["tiles"] == 0]}


def off_beeline(rows: list[dict], control: list[dict]) -> dict:
    """(build step 5.1, the verifier's round: "the divergence comes mostly from battle dice and personality, not from the new
    errands": goals and paths diverge across seeds under the beeline control too) WHERE NO BEELINE WENT. For each run of
    `rows`, the tiles it stood on that NO run of the beeline `control` stood on (the control's union over the sweep's seeds:
    the beeline's corridor, dice and all); for a control run itself, the tiles no OTHER control run stood on (leave one out:
    the beeline's own seed-to-seed spread, the null the errands are measured against). And how much those tiles DIFFER
    between two runs of one personality (the mean pairwise Jaccard distance of the off-beeline sets): the divergence the
    ERRANDS add, where a fixed side trip would score near 0."""
    union_all: set[str] = set().union(*(r["_tiles"] for r in control)) if control else set()
    off = {r["seed"]: r["_tiles"] - union_all for r in rows}
    alone = {r["seed"]: len(r["_tiles"] - set().union(*(o["_tiles"] for o in control if o is not r))) for r in control}
    pairs = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a["personality"] != b["personality"]:
                continue
            union = off[a["seed"]] | off[b["seed"]]
            pairs.append({"seeds": [a["seed"], b["seed"]],
                          "distance": round(1 - len(off[a["seed"]] & off[b["seed"]]) / len(union), 3) if union else 0.0})
    return {"runs": {seed: len(tiles) for seed, tiles in off.items()}, "control": alone, "corridor": len(union_all),
            "pairs": pairs, "pairs_mean": round(sum(p["distance"] for p in pairs) / len(pairs), 3) if pairs else None}


def told_before(actions: list[dict]) -> list[tuple]:
    """(build step 5.1, the step-5 review's finding 6: "no live check confirms that every go goal with a map came after the
    page that named it") Every `go` goal WITH a map whose reason quotes a page ("the game said: '...'") must come AFTER a
    page the AI READ that holds the quoted words (its `read` records): the goals that do not, [(frame, quoted)]."""
    pages: list[tuple[int, str]] = []
    bad = []
    for r in actions:
        if r.get("decision") == "read":
            pages.append((r.get("frame") or 0, " ".join(str(r.get("reason") or "").split()).lower()))
            continue
        if r.get("decision") != "goal" or r.get("action") != "go" or not (r.get("extra") or {}).get("map"):
            continue
        found = re.search(r"the game said: '(.*?)'\)", str(r.get("reason") or "")) or \
            re.search(r'the game said: "(.*?)"\)', str(r.get("reason") or ""))
        if found is None:
            continue
        quoted = " ".join(found.group(1).strip(".").split()).lower().strip()
        quoted = quoted[3:] if quoted.startswith("...") else quoted
        if quoted and not any(quoted[:40] in page for frame, page in pages if frame <= (r.get("frame") or 0)):
            bad.append((r.get("frame"), quoted[:60]))
    return bad


def new_place_draws(actions: list[dict], known: set[str]) -> tuple[list, list]:
    """(the step-5.1 verifier's round, `live_step5.check_new_places`; the second round: in the sweep's chapter 2 too) Every
    look-around draw, made or not, as (frame, map), and those that name a map the world memory the run STARTED from had
    stood on (`known`): a carried-on run's home town is no new place."""
    named = []
    for r in actions:
        text = str(r.get("reason") or "")
        found = re.search(r"a new place, ([A-Z0-9_]+)", text)
        if found and ((r.get("decision") == "goal" and r.get("action") == "explore")
                      or (r.get("decision") == "tell" and "it goes on without looking round" in text)):
            named.append((r.get("frame"), found.group(1)))
    return named, [(frame, const) for frame, const in named if const in known]


#: (build step 5.3, A1-1: critic Q1 on #44 and #61) the framework's own table of the map constants (`MapRSE`), the
#: source of a map's "group:number" key for the GAME half of a new-place check: game data, read as text (no import of the
#: framework, which this offline grader must not need). Before 5.3 the key came from the AI's world.jsonl (`map_keys` of
#: its world file), so a const missing from the AI's memory was silently skipped and the check was AI against AI.
MAP_DATA = REPO / "sandbox-pokebot" / "modules" / "map_data.py"


@functools.lru_cache(maxsize=4)
def _maprse(source: str) -> dict[str, str]:
    text = Path(source).read_text(encoding="utf-8")
    body = text.split("class MapRSE(Enum):", 1)[1].split("\nclass ", 1)[0]
    return {name: f"{group}:{number}"
            for name, group, number in re.findall(r"^\s+([A-Z][A-Z0-9_]*)\s*=\s*\((\d+),\s*(\d+)\)", body, re.M)}


def map_keys(source: str | Path = MAP_DATA) -> dict[str, str]:
    """(build step 5.3, A1-1) Map constant -> key ("group:number", as the harness's stays and the AI's memory key it) by the
    framework's `MapRSE` enum in `source` (default `MAP_DATA`). (Build step 5.2 read it from an AI world file.)"""
    return dict(_maprse(str(source)))


def seen_maps(seen_file: str | None) -> set[str] | None:
    """(build step 5.3, A1-1: critic Q1 on #44) The maps (consts) the GAME's screen had the player stand on, free, in the
    run whose `play_harness.SEEN_FILE` this is (`PlaceRecorder.maps`: every seen tile is keyed by the map the player stood
    on): a chapter-2 run's start. None when there is no such file (the draws are then not judged, never judged against an
    empty set)."""
    from ai_player.gates.play_harness import read_seen

    if not seen_file or not Path(seen_file).is_file():
        return None
    by_key = {key: const for const, key in map_keys(MAP_DATA).items()}
    keys = {f"{tile[0]}:{tile[1]}" for tile in read_seen(seen_file)}
    return {by_key.get(key, key) for key in keys}


def left_before(actions: list[dict], data: dict, offset: int) -> tuple[list[tuple], int, int]:
    """(build step 5.2, the step-5.1 review's finding 6: "a known town called 'a new place'": CH1M after healing in OLDALE
    twice) Every look-around draw ("a new place, X") made on a map the GAME had had the player stand on in an EARLIER
    stay of this run (the second path's stays, `play_harness.PlaceRecorder`): ([(frame, map)], the draws judged, the draws
    SKIPPED: a const with no key in `MapRSE` or a draw before the first stay; build step 5.3 counts them, critic Q1)."""
    named, _ = new_place_draws(actions, set())
    keys = map_keys(MAP_DATA)
    stays = (data.get("places") or {}).get("stays") or []
    bad, judged, skipped = [], 0, 0
    for frame, const in named:
        key = keys.get(const)
        at = (frame or 0) - offset
        index = max((i for i, (start, _) in enumerate(stays) if start <= at), default=None)
        if key is None or index is None:
            skipped += 1
            continue
        judged += 1
        if any(stay == key for _, stay in stays[:index]) and stays[index][1] == key:
            bad.append((frame, const))
    return bad, judged, skipped


def new_place_left_before(actions: list[dict], data: dict, offset: int) -> list[tuple]:
    """The draws `left_before` finds: [(frame, map)]."""
    return left_before(actions, data, offset)[0]


def grade_run(plan: str, seed: int, personality: str, starter: str, data: dict, actions: list[dict], seconds: float,
              earlier: list[dict] | None = None, world_in: str | None = None, seen_in: str | None = None) -> dict:
    """One run's numbers, each by the game (the recorder) unless named as the AI's. (The step-5.1 verifier's second round)
    `earlier`: the pages READ in the run this one goes on from (its world memory carries them); `world_in`: the world
    memory it started from (a chapter-2 run's). (Build step 5.3, A1-1) `seen_in`: the GAME's seen tiles of the run this one
    goes on from (`play_harness.SEEN_FILE`): the maps it stood on there are the known places of a new-place draw (#44),
    no longer the AI's world memory; `world_in` is kept for the caller only."""
    changes = (data.get("story") or {}).get("changes") or []
    end = (data.get("story_truth") or {}).get("marks") or {}
    stats = (data.get("story_truth") or {}).get("stats") or {}
    dex = first_change(changes, "RECEIVED_POKEDEX_FROM_BIRCH")
    rival = first_change(changes, "DEFEATED_RIVAL_ROUTE103")
    # the trainer battles fought before the rival's flag went up, counted from the starter's first battle (the game's
    # counter): 1 = the rival beaten at the first try (Route 103 holds no other trainer the player can reach before it)
    starter_mark = first_change(changes, "VAR_BIRCH_LAB_STATE", 2)
    trainer_before = rival["stats"]["trainer_battles"] - (starter_mark["stats"]["trainer_battles"] if starter_mark else 0) \
        if rival else None
    wild_before = rival["stats"]["wild_battles"] - (starter_mark["stats"]["wild_battles"] if starter_mark else 0) \
        if rival else None
    rival_frame = rival["f"] if rival else None
    roams = [r for r in actions if r.get("decision") == "roam" and r.get("action") == "metrics"]
    roams_before = [r for r in roams if rival_frame is None or (r.get("frame") or 0) <= rival_frame]
    train_steps = sum((r.get("extra") or {}).get("steps", 0) for r in roams_before)
    spins = sum((r.get("extra") or {}).get("spins", 0) for r in roams)
    steps_all = sum((r.get("extra") or {}).get("steps", 0) for r in roams)
    generic = sum(1 for r in actions if r.get("decision") == "watch" and str(r.get("reason", "")).startswith(GENERIC_BUSY))
    party = (data.get("truth") or {}).get("party_exp") or []
    # the party when the rival's flag went up (the framework's decoder, `play_harness.party_now`): its strongest level and
    # the share of its HP the fight left (how hard the win was)
    at_rival = (rival or {}).get("party") or []
    level_at_rival = max((row[1] for row in at_rival), default=None)
    total = sum(row[3] for row in at_rival)
    hp_after_rival = round(sum(row[2] for row in at_rival) / total, 3) if total else None
    blips = len(((data.get("story") or {}).get("blips")) or [])
    # (the step-5 verifier's round) THE GAME's battles (the recorder's gBattleOutcome / gBattleTypeFlags): the wild battles
    # WON between the starter's mark (PROF. BIRCH's scripted battle is before it) and the rival's flag, and every battle
    # LOST in the run (a whiteout), against the AI's own count of its losses
    battles = (data.get("story") or {}).get("battles") or []
    since = starter_mark["f"] if starter_mark else 0
    won_before = [b for b in battles if not b["trainer"] and b["outcome"] == 1 and since < b["f"] <= (rival_frame or 0)] \
        if rival else []
    lost = [b for b in battles if b["outcome"] == 2]
    drew = [b for b in battles if b["outcome"] == 3]
    breaches, low_ends = roam_breaches(actions)
    # (the step-5 verifier's round 2) THE GAME inside the AI's training windows: the steps its counter rose there and the
    # wild battles it says were won there (an arm that never trains has no window: both 0); and the AI's TOLD losses (the
    # play loop's own lines, `mode.py` _count_losses), which only the loop's count writes
    offset = actions[0].get("frame") or 0 if actions else 0
    windows = training_windows(actions)
    by_game = training_by_game(windows, data.get("story") or {}, offset, rival_frame)
    told = sum(1 for r in actions if r.get("decision") == "tell" and str(r.get("reason", "")).startswith("a battle was LOST ("))
    # (build step 5.1) THE WAITS ON A PRESS: the AI's own record (its eyes, whatever reason it gave) and the GAME's (the
    # harness's second path); the INTENT MIX; the PATH and the goal SEQUENCE (seed divergence); the patience's resets and
    # the longest stretch between two of them (or milestones); every go goal after the page that told it
    awaits = await_stretches(actions)
    waits_game = data.get("waits_game") or {}
    report = data.get("report") or {}
    marks_at = sorted([m.get("pad_frames") or 0 for m in report.get("milestones") or []]
                      + [p.get("pad_frames") or 0 for p in report.get("progress") or []])
    gaps = [b - a for a, b in zip([0] + marks_at, marks_at + [data.get("frames") or 0])]
    spans_all = goal_spans(actions)
    trains = [s for s in spans_all if s["kind"] == "train"]
    train_span = (trains[-1]["frame"] + trains[-1]["frames"] - trains[0]["frame"]) if trains else 0
    # (the step-5.1 verifier's second round) whose rule judged the run TRAINED for the rival (the goal manager's
    # `fight_prep` `judged_by`, in its end record): the run's own training bound; and CHAPTER 2's numbers by the game: WALLY's
    # tutorial (VAR_PETALBURG_GYM_STATE >= 2 and HIDE_PETALBURG_CITY_WALLYS_MOM at the end) and when its var rose
    end_note = next(((r.get("extra") or {}) for r in reversed(actions)
                     if r.get("decision") == "end" and "fight_prep" in (r.get("extra") or {})), {})
    judge = ((end_note.get("fight_prep") or {}).get("ch1_rival_route103") or {}).get("judged_by")
    wally = first_change(changes, "VAR_PETALBURG_GYM_STATE", 2)
    known = seen_maps(seen_in)
    named, old_places = new_place_draws(actions, known or set())
    left_bad, left_judged, left_skipped = left_before(actions, data, offset)
    # (build step 5.2, PRODUCTIVE CURIOSITY) every curiosity goal the story did not need, what it brought by its own record
    # and by the GAME; the intent mix counts the ones that brought nothing (by the game) as IDLE; the streaks; the pushing
    # by both paths; the person-blocks met (the BLOCKED arm's reach); a known place called new, by the game's stays
    curious = curiosity_rows(actions, data, offset)
    unproductive = {row["frame"] for row in curious if not row["game"]}
    streaks = curiosity_streaks(actions)
    push_game = ((data.get("places") or {}).get("push") or {}).get("longest") or [0, 0, 0, 0]
    return {
        "curious": [(r["kind"][:3], r["frame"], r["frames"], int(r["ai"]), int(r["game"]), r["tiles_game"]) for r in curious],
        "curious_frames": sum(r["frames"] for r in curious),
        "productive_frames": sum(r["frames"] for r in curious if r["game"]),
        "loaf_frames": loafing_frames(curious),
        "loaf_frames_all": sum(r["frames"] for r in curious if not r["game"]),
        # (step52dev2) the curiosity that SEES (a look round, a detour): where loafing hides (a chat's talk and a roam's
        # catch are nearly always there, and diluted the pooled yield: LOAF 0.54 pooled, 0.21 of its looks)
        "seeing_frames": sum(r["frames"] for r in curious if r["kind"] in SEEING),
        "seeing_productive": sum(r["frames"] for r in curious if r["kind"] in SEEING and r["game"]),
        "yield_agree": sum(1 for r in curious if r["ai"] == r["game"]),
        "detours": [(r["frame"], r.get("place"), r["said_reached"], r["game_reached"]) for r in curious
                    if r["kind"] == "detour"],
        "streak_goals": max((s[1] for s in streaks), default=0), "streak_frames": max((s[2] for s in streaks), default=0),
        "streaks_long": [s for s in streaks if s[1] >= 3][:4],
        "push_ai": push_ai(actions), "push_game": push_game[2], "push_game_at": push_game[:2],
        "person_blocks": person_blocks(actions),
        "left_called_new": left_bad, "left_judged": left_judged, "left_skipped": left_skipped,
        "ask_nothing_said": sum(1 for r in actions if r.get("decision") == "goal" and "to ask at" in str(r.get("reason"))
                                and "nothing was said" in str(r.get("reason"))),
        "places_samples": (data.get("places") or {}).get("samples"),
        # (build step 5.2, the verifier's round) the run given up OUT OF IDEAS (its walk with no lead found nothing left on
        # any map it knows: `brain/goals.py` lost_intent); the chats the GAME says told it nothing new (their message shown
        # before, no tile, map, capture or item: the nurse right after a heal), as (frame, own frames); the game's message
        # reads that failed (`play_harness.PlaceRecorder` text_errors: each such text counted new)
        "out_of_ideas": "out of ideas" in str(data.get("reason") or ""),
        "chats_idle": [(r["frame"], r["walking"]) for r in curious if r["kind"] == "chat" and not r["game"]],
        # (the verifier's second round) every talk the AI had, and the ones whose "told something new" the two paths
        # disagree on, (frame, kind, the AI, the game)
        "talks_ai": sum(1 for r in curious if r["talks_ai"]),
        "talks_apart": [(r["frame"], r["kind"][:3], int(r["talked_ai"]), int(r["talked_game"])) for r in curious
                        if r["talks_ai"] and r["talked_ai"] != r["talked_game"]],
        "text_errors": (data.get("places") or {}).get("text_errors"),
        "rival_judge": judge, "wally": bool(end.get("HIDE_PETALBURG_CITY_WALLYS_MOM"))
        and (end.get("VAR_PETALBURG_GYM_STATE") or 0) >= 2, "wally_frame": wally["f"] if wally else None,
        "time_wally": time_to_dex(actions, CH2_TARGET, since_start=True), "place_draws": len(named), "old_places": old_places,
        # (build step 5.3) the draws the GAME half could judge (0 when the run it went on from left no seen tiles)
        "place_draws_judged": len(named) if known is not None else 0,
        "train_span": train_span, "last_goal": spans_all[-1]["kind"] if spans_all else None,
        "trains": len(trains),
        "await_ai_max": max((a["frames"] for a in awaits), default=0),
        "await_ai_long": [(a["first"], a["frames"], str(a["what"])[:40], str(a["doing"])[:60]) for a in awaits
                          if a["frames"] >= BOUNDS["AWAIT_MAX"]],
        "await_game_max": ((waits_game.get("longest") or [0, 0, 0])[2]) if waits_game else None,
        "await_game_long": [k for k in waits_game.get("kept") or [] if k[2] >= BOUNDS["AWAIT_MAX"]],
        "await_game_samples": waits_game.get("samples"),
        "mix": intent_mix(actions, unproductive),
        "progress_resets": len(report.get("progress") or []),
        "longest_without_progress": max(gaps, default=None),
        "told_before_bad": told_before([{**r, "frame": -1} for r in earlier or []] + actions),
        "_sequence": goal_sequence(actions), "_tiles": visited_tiles(data.get("world_file")),
        "curious_sequence": curiosity_sequence(actions), "asides": aside_streaks(actions), "time": time_to_dex(actions),
        "rival_actives": sorted({(r.get("extra") or {}).get("active") for r in actions if r.get("decision") == "goal"
                                 and (r.get("extra") or {}).get("milestone") == "ch1_rival_route103"} - {None}),
        "dropped_goals": sum(1 for g in report.get("goals") or [] if g.get("ok") is None and "dropped" in str(g.get("outcome"))),
        "plan": plan, "seed": seed, "personality": personality, "starter": starter, "reason": data.get("reason"),
        "frames": data.get("frames"), "seconds": round(seconds, 1),
        "reached": bool(end.get("RECEIVED_POKEDEX_FROM_BIRCH")), "dex_frame": dex["f"] if dex else None,
        "rival_beaten": bool(end.get("DEFEATED_RIVAL_ROUTE103")), "rival_frame": rival_frame,
        "train_windows": by_game["windows"], "game_train_steps": by_game["steps"], "game_train_won": by_game["won"],
        "game_steps_refused": by_game["refused"], "train_steps_before_rival": train_steps,
        "losses_game": len(lost), "losses_ai": ((data.get("report") or {}).get("losses")), "losses_told": told,
        # (build step 5.3, A1-2) the play loop's MAX_LOSSES as the HARNESS recorded it for this run (`play_harness.play`)
        "max_losses": data.get("max_losses"),
        "first_loss_f": lost[0]["f"] if lost else None, "last_loss_f": lost[-1]["f"] if lost else None,
        "trainer_battles_to_rival": trainer_before, "wild_before_rival": wild_before,
        "wild_won_before_rival": len(won_before) if rival else None,
        "spins": spins, "roam_steps": steps_all,
        "spin_ratio": round(spins / steps_all, 4) if steps_all else 0.0, "generic_idle": generic,
        "level_at_rival": level_at_rival, "hp_after_rival": hp_after_rival, "recorder_blips": blips,
        "starter_in_party": [row[1] for row in party[:1]], "levels": [row[3] for row in party], "drew_game": len(drew),
        "battles_ended": len(battles), "rest_breaches": breaches, "roam_low_ends": low_ends, "game_stats": stats,
    }


def summarise(plan: str, rows: list[dict]) -> dict:
    ok = [r for r in rows if "error" not in r]
    reached = [r for r in ok if r["reached"]]
    beaten = [r for r in ok if r["rival_beaten"]]
    first = [r for r in beaten if r["trainer_battles_to_rival"] == 1]
    return {"plan": plan, "runs": len(rows), "errors": len(rows) - len(ok), "reached": len(reached),
            "rival_beaten": len(beaten), "first_try": len(first),
            "wild_before_rival": [r["wild_before_rival"] for r in ok],
            "train_steps_before_rival": [r["train_steps_before_rival"] for r in ok],
            "dex_frames": [r["dex_frame"] for r in ok], "spin_ratios": [r["spin_ratio"] for r in ok],
            "generic_idle": sum(r["generic_idle"] for r in ok), "reasons": [r["reason"] for r in ok],
            "levels_at_rival": [r["level_at_rival"] for r in ok], "hp_after_rival": [r["hp_after_rival"] for r in ok],
            "wild_won_before_rival": [r["wild_won_before_rival"] for r in ok],
            "game_train_steps": [r["game_train_steps"] for r in ok], "game_train_won": [r["game_train_won"] for r in ok],
            "losses_game": [r["losses_game"] for r in ok], "losses_ai": [r["losses_ai"] for r in ok],
            "losses_told": [r["losses_told"] for r in ok],
            "rest_breaches": sum(len(r["rest_breaches"]) for r in ok), "roam_low_ends": sum(r["roam_low_ends"] for r in ok)}


def verdicts(summary: dict[str, dict], rows: dict[str, list[dict]]) -> list[Check]:
    """EVERY check of the sweep, typed (`grader_checks`, build step 5.3 A1-1), in the VERDICT view (`verdict_row`: each
    row's bool says whether it lets the verdict pass; `typed_verdict` is the verdict). Each COUNTED check (GRADED or
    HONESTY) gives its sample count and floor, so a counted check that saw nothing reads VACUOUS, never PASS (and FAILS the
    verdict unless `grader_waivers.json` waives it; a waived one still prints VACUOUS). A DIAGNOSTIC or REPORTED check
    never counts and may give no floor: such a check that saw nothing can print PASS (e.g. R5.ASIDE_BACK with no aside, n
    0, floor "-"), which says nothing about the verdict."""
    out = []
    ch1 = summary.get("CH1")
    if ch1:
        n = ch1["runs"]
        out.append(grade("R5.CH1_REACHED", ch1["reached"] >= BOUNDS["CH1_REACHED_MIN"] * n,
                         f"CH1: the POKéDEX reached (by the game's flag) in {ch1['reached']} of {n} (bound >= {BOUNDS['CH1_REACHED_MIN']:.0%})",
                         n, 1))
        out.append(grade("R5.CH1_FIRST_TRY", ch1["first_try"] >= BOUNDS["CH1_FIRST_TRY_MIN"] * n,
                    f"CH1: the rival beaten at the FIRST try (the game's trainer-battle counter) in {ch1['first_try']} of {n} "
                    f"(bound >= {BOUNDS['CH1_FIRST_TRY_MIN']:.0%})", n, 1))
        beaten = [r for r in rows["CH1"] if r.get("rival_beaten")]
        low = [(r["seed"], r["game_train_won"], r["game_train_steps"], r["train_steps_before_rival"]) for r in beaten
               if not trained_by_game(r) or r["train_steps_before_rival"] < train_steps_min_run(r)]
        out.append(grade("R5.CH1_TRAINED", bool(beaten) and not low,
                    f"CH1: every seed that beat the rival TRAINED first, BY THE GAME inside the windows its log says it "
                    f"roamed to train before the rival's flag (the step-5 verifier's round 2): the game's step counter rose "
                    f"at least the re-derived minimum of the personality it played as (the step-5.1 verifier's round: "
                    f"{ {p: train_steps_min(p) for p in PERSONALITIES} }; a run that DRIFTED during the rival's milestone: "
                    f"the lowest of those it played as) (seed, base, played as, bound, the game's steps) "
                    f"{[(r['seed'], r['personality'][0], ''.join(p[0] for p in r.get('rival_actives') or []), train_steps_min_run(r), r['game_train_steps']) for r in beaten]} and the game says "
                    f">= {BOUNDS['CH1_WILD_WON_MIN']} wild battles were WON there {[r['game_train_won'] for r in beaten]} "
                    f"(windows {[r['train_windows'] for r in beaten]}); and its roam reports say as many training steps "
                    f"{[r['train_steps_before_rival'] for r in beaten]}; short: {low or 'none'}", len(beaten), 1))
        out.append(grade("R5.CH1_WILD_WON", True,
                         f"CH1 (reported): wild battles WON anywhere between the starter's mark and the rival's flag (the "
                          f"game's outcomes; NOT a training check: walks win battles too) "
                          f"{[r['wild_won_before_rival'] for r in beaten]}, met (the game's counter) "
                          f"{[r['wild_before_rival'] for r in beaten]}; the game's steps refused as impossible readings "
                          f"{[r['game_steps_refused'] for r in beaten]}"))
        # step 4.1 round 3's criterion (`rate_step3.py` ROAM_SPINS_PER_SEED): the spins over the seeds TOGETHER under 2 % of
        # their training steps, and no seed over 5 (a per-seed "< 2 %" failed 18 % of 10-seed samples of the same roaming:
        # 2 spins in 100 steps is 2 %; this sweep's seed 7 of 2026-10-14, step5dev3, was exactly that)
        graded = [r for r in rows["CH1"] if "error" not in r]
        spins = sum(r.get("spins") or 0 for r in graded)
        steps = sum(r.get("roam_steps") or 0 for r in graded)
        pooled = spins / steps if steps else 1.0
        heavy = [(r["seed"], r.get("spins")) for r in graded if (r.get("spins") or 0) > BOUNDS["CH1_SPINS_PER_SEED"]]
        # (build step 5.3) no training step at all is VACUOUS (n = the steps), no longer a pooled ratio of 1.0
        out.append(grade("R5.CH1_SPINS", pooled < BOUNDS["CH1_SPIN_MAX"] and not heavy,
                    f"CH1: the back-and-forth spins over the seeds together {spins} in {steps} training steps ({pooled:.2%}, "
                    f"bound under {BOUNDS['CH1_SPIN_MAX']:.0%}), per seed {[r.get('spins') for r in graded]} (bound "
                    f"{BOUNDS['CH1_SPINS_PER_SEED']} each; over it {heavy or 'none'})", steps, 1))
        out.append(grade("R5.CH1_CATCH_ALL", ch1["generic_idle"] <= CODE_BOUNDS["CATCH_ALL_MAX"],
                         f"CH1: no stretch standing still under the catch-all reason: {ch1['generic_idle']} (bound <= "
                         f"{CODE_BOUNDS['CATCH_ALL_MAX']})", len(graded), 1))
        out.append(grade("R5.CH1_WHITEOUTS", sum(ch1["losses_game"]) <= BOUNDS["CH1_WHITEOUTS_MAX"],
                    f"CH1: the game's whiteouts (battles LOST, gBattleOutcome) over the seeds together {sum(ch1['losses_game'])} "
                    f"(bound <= {BOUNDS['CH1_WHITEOUTS_MAX']}), per seed {ch1['losses_game']}", len(graded), 1))
        # (the step-5 verifier's DEAD FIX) the rest rule FIRES: no roam played on after a battle that left the party under
        # its personality's heal_below; and it had occasions to (a check with none is vacuous: build step 5.3 types it,
        # n = the occasions)
        out.append(grade("R5.CH1_REST_RULE", ch1["rest_breaches"] <= CODE_BOUNDS["REST_BREACHES_MAX"]
                         and ch1["roam_low_ends"] >= 1,
                    f"CH1: THE REST RULE: battles a training or catching roam played after one that ended under the "
                    f"personality's heal_below {ch1['rest_breaches']} (bound <= {CODE_BOUNDS['REST_BREACHES_MAX']}), over {ch1['roam_low_ends']} such ends (the "
                    f"occasions; bound >= 1: not vacuous): "
                    f"{[(r['seed'], r['rest_breaches'][:2]) for r in graded if r['rest_breaches']] or 'none'}",
                    ch1["roam_low_ends"], 1))
        # the recorder saw every battle end (its count of ends == the game's battle counter, or one fewer if a battle was
        # under way when the run ended): the battle numbers above rest on it
        missed = [(r["seed"], r["battles_ended"], (r.get("game_stats") or {}).get("total_battles")) for r in graded
                  if (r.get("game_stats") or {}).get("total_battles") is None
                  or not CODE_BOUNDS["RECORDER_GAP"][0] <= r["game_stats"]["total_battles"] - r["battles_ended"]
                  <= CODE_BOUNDS["RECORDER_GAP"][1]]
        out.append(grade("R5.CH1_RECORDER", not missed,
                         f"CH1: the recorder saw every battle end (ends == GAME_STAT_TOTAL_BATTLES, or one fewer): "
                                f"{[(r['seed'], r['battles_ended']) for r in graded]}; off: {missed or 'none'}", len(graded), 1))
    # (the step-5 verifier's round: the AI's report said 0 losses after two whiteouts) every plan, every seed: the AI's
    # count of battles lost (its report, `mode.py` MAX_LOSSES) == the game's (battle outcomes LOST); and (round 2: the end
    # line recounted, so a loop that had stopped counting still agreed) its TOLD losses, which only the loop's count writes,
    # == the game's too. STOPDEAD is the arm with the loop's count REMOVED: graded below, never here.
    every = [r for plan, plan_rows in rows.items() if plan != "STOPDEAD" for r in plan_rows if "error" not in r]
    wrong = [(r["plan"], r["seed"], r["losses_ai"], r["losses_told"], r["losses_game"]) for r in every
             if not r["losses_ai"] == r["losses_told"] == r["losses_game"]]
    out.append(grade("R5.LOSSES_AGREE", bool(every) and not wrong,
                f"ALL PLANS: the AI's battles lost (its report) == its TOLD losses (the loop's lines) == the game's "
                f"(gBattleOutcome LOST) in {len(every) - len(wrong)} of {len(every)} runs; the game's losses by plan "
                f"{ {plan: sum(r['losses_game'] for r in plan_rows if 'error' not in r) for plan, plan_rows in rows.items()} }; "
                f"off (plan, seed, report, told, game): {wrong or 'none'}", len(every), 1))
    if ch1 and summary.get("NOTRAIN"):
        no = summary["NOTRAIN"]
        a = sum(x or 0 for x in ch1["wild_won_before_rival"])
        b = sum(x or 0 for x in no["wild_won_before_rival"])
        untrained = [r for r in rows["NOTRAIN"] if "error" not in r]
        # (build step 5.3, A1-3) the registered bound is READ: True is the claim "NOTRAIN wins fewer"; any other value
        # FAILS the check instead of switching it off (a bound is never loosened to pass)
        out.append(grade("R5.NOTRAIN_MECHANISM", BOUNDS["NOTRAIN_WILD_LESS"] is True and b < a,
                         f"NOTRAIN (the mechanism): wild battles WON before the rival (the game's outcomes) in all {a} "
                           f"(CH1) vs {b} (NOTRAIN) (bound NOTRAIN_WILD_LESS {BOUNDS['NOTRAIN_WILD_LESS']}: fewer)",
                         len(untrained), 1))
        # (the step-5 verifier's round 2: "won >= 3 before the rival" was met by NOTRAIN in 6 of 10 seeds) the game-side
        # TRAINED check must tell the arms apart: it passes for every CH1 seed that beat the rival (above) and FAILS for
        # every NOTRAIN seed (no training window: the game counted nothing there)
        passed = [(r["seed"], r["game_train_steps"], r["game_train_won"]) for r in untrained if trained_by_game(r)]
        trained = [r for r in rows["CH1"] if "error" not in r and r.get("rival_beaten")]
        out.append(grade("R5.NOTRAIN_TRAINED_CHECK", bool(untrained) and not passed,
                    f"THE TRAINED CHECK TELLS TRAINING FROM NONE (by the game): it passes for "
                    f"{sum(1 for r in trained if trained_by_game(r))} of {len(trained)} CH1 seeds and for {len(passed)} of "
                    f"{len(untrained)} NOTRAIN seeds (bound 0): NOTRAIN's training windows "
                    f"{[r['train_windows'] for r in untrained]}, the game's steps there "
                    f"{[r['game_train_steps'] for r in untrained]}, wild battles won there "
                    f"{[r['game_train_won'] for r in untrained]} (while it WON {no['wild_won_before_rival']} wild battles "
                    f"before the rival elsewhere: the count the old check used)", len(untrained), 1))

        def mean(values: list) -> float | None:
            values = [v for v in values if v is not None]
            return round(sum(values) / len(values), 3) if values else None

        # (the step-5 verifier: the HP comparison was a bare comparison of means, confounded by the missing heal before
        # the fight) PAIRED BY SEED: the same seed, personality and starter in both arms
        by_no = {r["seed"]: r for r in rows["NOTRAIN"] if "error" not in r}
        pairs = [(r, by_no[r["seed"]]) for r in rows["CH1"] if "error" not in r and r["seed"] in by_no]
        levels = [a["level_at_rival"] - b["level_at_rival"] for a, b in pairs
                  if a["level_at_rival"] is not None and b["level_at_rival"] is not None]
        hps = [round(a["hp_after_rival"] - b["hp_after_rival"], 3) for a, b in pairs
               if a["hp_after_rival"] is not None and b["hp_after_rival"] is not None]
        level_mean = mean(levels)
        out.append(grade("R5.NOTRAIN_LEVEL", bool(levels) and level_mean is not None
                         and level_mean >= BOUNDS["NOTRAIN_LEVEL_PAIRED_MIN"]
                         and not any(d <= CODE_BOUNDS["NOTRAIN_LEVEL_WORST"] for d in levels),
                    f"NOTRAIN (the effect, by the game's party at the rival's flag, PAIRED by seed): the strongest level "
                    f"CH1 - NOTRAIN {levels}, mean {level_mean} (bound >= {BOUNDS['NOTRAIN_LEVEL_PAIRED_MIN']}, and no seed "
                    f"at or under {CODE_BOUNDS['NOTRAIN_LEVEL_WORST']}: NOTRAIN 2 or more levels higher)", len(levels), 1))
        out.append(grade("R5.NOTRAIN_HP", True,
                         f"NOTRAIN (reported, not bounded): the HP share the rival's fight left, CH1 - NOTRAIN paired by "
                          f"seed {hps}, mean {mean(hps)} (both arms now heal before the fight: the fault removes the training "
                          f"only)", len(hps)))
        # the WIN RATE is REPORTED, not a pass condition: the development sweeps measured the rival (L5) beaten at the
        # first try 9 of 9 (CH1) and 8 of 9 (NOTRAIN) (step5dev4, seed 7's CH1 row a recorder phantom, fixed since), a
        # ceiling a 10-seed sample cannot resolve; the README's step-5 section says so
        out.append(grade("R5.NOTRAIN_FIRST_TRY", True,
                         f"NOTRAIN (reported, not bounded): the rival beaten at the first try {ch1['first_try']} of "
                          f"{ch1['runs']} (CH1) vs {no['first_try']} of {no['runs']} (NOTRAIN)", no["runs"]))
    if ch1 and summary.get("DEADREST"):
        dead = summary["DEADREST"]
        hit = [(r["seed"], len(r["rest_breaches"]), r["rest_breaches"][:1]) for r in rows["DEADREST"]
               if "error" not in r and r["rest_breaches"]]
        out.append(grade("R5.DEADREST", dead["rest_breaches"] > CODE_BOUNDS["DEADREST_BREACHES_OVER"]
                         and ch1["rest_breaches"] <= CODE_BOUNDS["REST_BREACHES_MAX"],
                    f"DEADREST (the fix REMOVED: mutant G36, the rest asked only with a battle limit): the rest check finds "
                    f"{dead['rest_breaches']} battles played on under heal_below over {dead['roam_low_ends']} occasions "
                    f"(bound > {CODE_BOUNDS['DEADREST_BREACHES_OVER']}: the check sees the dead fix) vs CH1 "
                    f"{ch1['rest_breaches']} (bound <= {CODE_BOUNDS['REST_BREACHES_MAX']}); seeds {hit or 'none'}; the "
                    f"game's whiteouts {sum(dead['losses_game'])} vs CH1 {sum(ch1['losses_game'])} (reported)",
                    dead["runs"] - dead["errors"], 1))
    if ch1 and summary.get("NOHINTS"):
        nh = summary["NOHINTS"]
        both = [(c, h) for c, h in zip(ch1["dex_frames"], nh["dex_frames"]) if c and h]
        slower = nh["reached"] < ch1["reached"] or (both and sum(h for _, h in both) > sum(c for c, _ in both))
        # (build step 5.3, A1-3) the registered bound is READ, as NOTRAIN_WILD_LESS above
        out.append(grade("R5.NOHINTS_SLOWER", BOUNDS["NOHINTS_SLOWER"] is True and bool(slower),
                         f"NOHINTS: reached {nh['reached']} of {nh['runs']} (CH1 {ch1['reached']}); where both "
                                  f"reached, frames {sum(h for _, h in both) if both else '-'} vs CH1 "
                                  f"{sum(c for c, _ in both) if both else '-'}; its ends {nh['reasons']} (bound "
                                  f"NOHINTS_SLOWER {BOUNDS['NOHINTS_SLOWER']}: fewer reached, or later)", nh["runs"], 1))
    out += stop_verdicts(rows)
    out += step51_verdicts(rows)
    out += chapter2_verdicts(rows)
    out += step52_verdicts(rows)
    return verdict_rows(out)


#: (build step 5.2, the step's own P2: "AI's own target must not be the graded quantity: grade YIELD and SPACING, not share
#: of frames"; the step-5.1 review: "THE CH2 FLOOR IS PARTLY THE AI'S OWN TARGET") the checks of a SHARE OF FRAMES, every
#: one of them the quantity 5.1's balance or its curiosity minimum aimed at, and their controls: REPORTED with the old
#: bound's own verdict beside them, no longer graded. (Decided in development, before any graded run of 5.2, and after
#: development runs had FAILED the old chapter-2 floor: it held in 10 of 11 chapter-2 runs of step52dev2 and 22 of 24 of
#: step52dev3 and dev4, the AI aiming at no share; the taste lowered for it in dev3 and dev4 was restored,
#: `personality.py` bored_frames.) What separates the AI from a beeline
#: stays graded: OFF THE BEELINE, NO SPEEDRUN, THE ERRANDS DIFFER BY SEED, the yield against LOAF, the spacing.
#: (Build step 5.3, A1-1) No longer a list of TEXT PREFIXES that a function forced to PASS: these are the ids of the seven
#: checks whose KIND is REPORTED with their old bound kept (`grader_checks.CHECKS` old_bound): a REPORTED check never counts,
#: and its old bound's verdict is printed beside it (`grader_checks.verdict_row`). The name is kept for `LESSONS.md` PF-14
#: until stage A1-4 re-points it.
P2_REPORTED = ("R5.CH1_INTENT_MIX", "R5.CH1_FREE", "R5.OFF_MOVES_MIX", "R5.BEELINE_FAILS_FREE", "R5.CH2_INTENT_MIX",
               "R5.CH2_FREE", "R5.CH2_OFF_UNDER")


def verdict_rows(results: list) -> list[Check]:
    """(Build step 5.3, A1-1) Every check of `verdicts` TYPED (`as_check`: a check of the table as it is; a legacy
    `(ok, text)` tuple typed by its title, refused when no title fits) and in the VERDICT view (`verdict_row`)."""
    return [verdict_row(as_check(item, "R5")) for item in results]


def step52_verdicts(rows: dict[str, list[dict]]) -> list[Check]:
    """(build step 5.2, PRODUCTIVE CURIOSITY) The new checks, each pre-registered in `BOUNDS`, each with the control that
    CAN fail it: the YIELD (LOAF), the SPACING (GREEDY), the PUSHING (BLOCKED), and the truth of what the AI says (the
    detours, a new place, the ask step). ERRANDS_OFF is reported beside them, a comparison, not their control. (Build step
    5.3, A1-1) Typed: the spacing, GREEDY, the ask step, out of ideas and the yield agreement are DIAGNOSTIC; the detours,
    a place left and the two paths' agreement HONESTY; each check's sample count is its n (the frames looked round for
    the yield, the detours that chose a place, the runs elsewhere)."""
    out: list[Check] = []

    def good(plan: str) -> list[dict]:
        return [r for r in rows.get(plan, []) if "error" not in r]

    real = [r for plan in REAL_PLANS for r in good(plan)]
    if not real:
        return out
    # THE YIELD of the curiosity that SEES (a look round, a detour), pooled by chapter; all curiosity's reported; and the
    # loafing in every run
    for plan in ("CH1", "CH2"):
        runs = good(plan)
        if not runs:
            continue
        seeing = sum(r["seeing_frames"] for r in runs)
        made = sum(r["seeing_productive"] for r in runs)
        rate = made / seeing if seeing else 0.0
        curious = sum(r["curious_frames"] for r in runs)
        pooled = sum(r["productive_frames"] for r in runs) / curious if curious else 0.0
        out.append(grade(f"R5.{plan}_YIELD", seeing > 0 and rate >= BOUNDS["YIELD_RATE_MIN"],
                    f"{plan}: CURIOSITY BY YIELD (the GAME's second path: a look round's or a detour's span showed "
                    f"{YIELD_TILES}+ new tiles and {YIELD_TILE_RATE} per 1,000 frames outside battles, or a map first stood "
                    f"on, a capture, an item ball, a talk; a detour only where it stood at its place): {made} of {seeing} "
                    f"frames of looking round and detours brought something, {rate:.1%} pooled (bound >= "
                    f"{BOUNDS['YIELD_RATE_MIN']:.0%}); by run (seed, productive, all) "
                    f"{[(r['seed'], r['seeing_productive'], r['seeing_frames']) for r in runs]}; (reported) all its "
                    f"curiosity {pooled:.1%} of {curious} frames", seeing, 1))
    loafing = [(r["plan"], r["seed"], r["loaf_frames"]) for r in real if r["loaf_frames"] > BOUNDS["LOAF_FRAMES_MAX"]]
    out.append(grade("R5.NO_LOAFING", not loafing,
                     f"NO LOAFING (every run of {list(REAL_PLANS)}, {len(real)} runs): the frames of curiosity that "
                             f"brought nothing (by the game), its own time outside battles, at most "
                             f"{BOUNDS['LOAF_FRAMES_MAX']} a run; the most {max(r['loaf_frames'] for r in real)}; over it: "
                             f"{loafing or 'none'}; (reported) with the battles in them, the most "
                             f"{max(r.get('loaf_frames_all', 0) for r in real)}", len(real), 1))
    agree = sum(r["yield_agree"] for r in real)
    total = sum(len(r["curious"]) for r in real)
    out.append(grade("R5.YIELD_AGREE", agree == total,
                     f"(reported) the AI's own word on its curiosity's yield agrees with the game's in {agree} of {total} "
                      f"goals", total))
    loaf = good("LOAF")
    if loaf:
        over = [r["seed"] for r in loaf if r["loaf_frames"] > BOUNDS["LOAF_FRAMES_MAX"]]
        seeing = sum(r["seeing_frames"] for r in loaf)
        rate = sum(r["seeing_productive"] for r in loaf) / seeing if seeing else 0.0
        out.append(grade("R5.LOAF", len(over) >= BOUNDS["LOAF_FAILS_RUNS_MIN"] and seeing > 0
                         and rate < BOUNDS["YIELD_RATE_MIN"],
                    f"LOAF (the control that CAN fail: looks round and detours among tiles it has stood on, `EXTRA_EDITS`): "
                    f"the yield of its looks round and detours {rate:.1%} pooled of {seeing} frames (must be under "
                    f"{BOUNDS['YIELD_RATE_MIN']:.0%}); over the per-run loafing bound in {len(over)} of {len(loaf)} runs "
                    f"(bound >= {BOUNDS['LOAF_FAILS_RUNS_MIN']}): {dict((r['seed'], r['loaf_frames']) for r in loaf)}",
                    len(loaf), 1))
    off = good("ERRANDS_OFF")
    if off:
        out.append(grade("R5.OFF_REPORTED", True,
                         f"(reported) ERRANDS_OFF, the beeline: its curiosity (item balls only) {sum(r['curious_frames'] for r in off)} "
                          f"frames, {sum(r['productive_frames'] for r in off)} productive; loafing "
                          f"{[r['loaf_frames'] for r in off]}", len(off)))
    # THE SPACING in every run; GREEDY over it
    spaced = [(r["plan"], r["seed"], r["streak_goals"], r["streak_frames"]) for r in real
              if r["streak_goals"] > BOUNDS["SPACING_ROW_MAX"]]
    out.append(grade("R5.SPACED", not spaced,
                     f"CURIOSITY SPACED (every run of {list(REAL_PLANS)}): at most {BOUNDS['SPACING_ROW_MAX']} curiosity "
                            f"goals in a row; the most {max(r['streak_goals'] for r in real)}; over: {spaced or 'none'}; "
                            f"(reported, not bounded: a streak's frames, a catching roam being one goal) the longest "
                            f"{max(r['streak_frames'] for r in real)} frames", len(real), 1))
    greedy = good("GREEDY")
    if greedy:
        over = [(r["seed"], r["streak_goals"], r["streak_frames"]) for r in greedy
                if r["streak_goals"] > BOUNDS["SPACING_ROW_MAX"]]
        out.append(grade("R5.GREEDY", len(over) >= BOUNDS["GREEDY_FAILS_MIN"] * len(greedy),
                    f"GREEDY (the control that CAN fail: every curiosity draw passes, no cap in a row): over the spacing "
                    f"bounds in {len(over)} of {len(greedy)} runs (bound >= {BOUNDS['GREEDY_FAILS_MIN']:.0%}): {over}",
                    len(greedy), 1))
    # DETOURS THAT ARRIVE, and what the AI says of them is true
    detours = [(r["plan"], r["seed"], *d) for r in real for d in r["detours"]]
    if detours:
        # (step52dev3) a detour that chose NO place ("not reached: nothing off the way here that it can walk to", 7 of 23
        # there, 17-29 frames each) walked nowhere: it is no detour that failed to arrive, and is reported apart
        placed = [d for d in detours if d[3]]
        there = [d for d in placed if d[5]]
        out.append(grade("R5.DETOURS_ARRIVE", bool(placed) and len(there) >= BOUNDS["ARRIVE_MIN"] * len(placed),
                    f"DETOURS THAT ARRIVE (by the game: the player stood at the place chosen when the detour ended): "
                    f"{len(there)} of the {len(placed)} that chose a place (bound >= {BOUNDS['ARRIVE_MIN']:.0%}); "
                    f"(reported) {len(detours) - len(placed)} more found no place off the way to walk to", len(placed), 1))
        lies = [d for d in detours if bool(d[4]) != bool(d[5])]
        out.append(grade("R5.DETOUR_WORD", not lies,
                         f"THE DETOUR'S WORD IS TRUE: its 'reached' / 'not reached' agrees with the game in "
                              f"{len(detours) - len(lies)} of {len(detours)} detours; apart (plan, seed, frame, place, said "
                              f"reached, the game): {lies[:6] or 'none'}", len(detours), 1))
    else:
        # (build step 5.3) no longer a forced FAIL: VACUOUS (n 0 of floor 1), which fails the verdict unless waived
        out.append(grade("R5.DETOURS_ARRIVE", False, "DETOURS THAT ARRIVE: no detour in the real code's runs (the check "
                                                     "is vacuous)", 0, 1))
    # THE PUSHING PROPERTY, both paths, every real run; the two paths agree; BLOCKED over it where it met someone
    bound = BOUNDS["PUSH_MAX"]
    pushing = [(r["plan"], r["seed"], r["push_ai"], r["push_game"], r["push_game_at"]) for r in real
               if r["push_ai"] >= bound or r["push_game"] >= bound]
    out.append(grade("R5.PUSHING", not pushing,
                     f"THE PUSHING PROPERTY (every run of {list(REAL_PLANS)}): the longest free stretch of pressing that "
                             f"brought nothing new, by the AI's record {max(r['push_ai'] for r in real)} frames, by the "
                             f"GAME's {max(r['push_game'] for r in real)} (bound under {bound}); over it: {pushing or 'none'}",
                     len(real), 1))
    every = [r for plan_rows in rows.values() for r in plan_rows if "error" not in r and "push_ai" in r]
    split = [(r["plan"], r["seed"], r["push_ai"], r["push_game"]) for r in every
             if (r["push_ai"] >= bound) != (r["push_game"] >= bound)]
    out.append(grade("R5.PUSH_PATHS_AGREE", not split,
                     f"THE TWO PATHS AGREE on the pushing verdict in {len(every) - len(split)} of {len(every)} runs; "
                           f"apart: {split or 'none'}", len(every), 1))
    blocked = good("BLOCKED")
    if blocked:
        reached = [r for r in blocked if r["person_blocks"] >= BOUNDS["BLOCKED_REACH_HITS"]]
        hit = [(r["seed"], r["push_ai"], r["push_game"]) for r in reached
               if r["push_ai"] >= bound and r["push_game"] >= bound]
        out.append(grade("R5.BLOCKED", len(hit) >= BOUNDS["BLOCKED_HITS_MIN"]
                         and len(reached) >= BOUNDS["BLOCKED_REACH_MIN"] * len(blocked),
                    f"BLOCKED (the control that CAN fail: it never gives up a place it cannot get to): it met someone in the "
                    f"way of a curiosity walk {BOUNDS['BLOCKED_REACH_HITS']}+ times in {len(reached)} of {len(blocked)} runs "
                    f"(bound >= {BOUNDS['BLOCKED_REACH_MIN']:.0%}: it REACHED the state tested); of them, over the pushing "
                    f"bound by BOTH paths in {len(hit)} (bound >= {BOUNDS['BLOCKED_HITS_MIN']}): {hit}; all its runs (seed, "
                    f"blocks, AI, game) {[(r['seed'], r['person_blocks'], r['push_ai'], r['push_game']) for r in blocked]}",
                    len(blocked), 1))
    # A KNOWN PLACE IS NEVER NEW (by the game's stays), and the ask step never walks with nothing said. (Build step 5.3,
    # critic Q1) the map's key is the framework's (`MapRSE`), no longer the AI's memory; the draws it could not judge are
    # counted (skipped), and n is the draws it JUDGED (A1-4: a sweep whose draws were all skipped saw nothing: VACUOUS)
    left = [(r["plan"], r["seed"], r["left_called_new"][:2]) for r in real if r["left_called_new"]]
    judged = sum(r.get("left_judged") or 0 for r in real)
    skipped = sum(r.get("left_skipped") or 0 for r in real)
    out.append(grade("R5.LEFT_NOT_NEW", not left,
                     f"A PLACE IT HAS LEFT IS NO NEW PLACE (the GAME's stays: a look-around draw on a map stood on in an "
                          f"earlier stay of the run): off {left or 'none'}; draws judged {judged}, skipped {skipped} (a "
                          f"const with no MapRSE key, or a draw before the first stay)", judged, 1))
    asked = [(r["plan"], r["seed"], r["ask_nothing_said"]) for r in real if r["ask_nothing_said"]]
    out.append(grade("R5.ASK_STEP", not asked,
                     f"THE ASK STEP WALKS TO ITS HOUSE ONLY WHEN TOLD (no 'to ask at ... nothing was said'): off "
                           f"{asked or 'none'}", len(real), 1))
    sampled = [(r["plan"], r["seed"]) for r in every if not r.get("places_samples")]
    out.append(grade("R5.PLACES_READ", not sampled,
                     f"THE GAME'S PLACES (second path) were read in every run: unread {sampled or 'none'}", len(every), 1))
    # (build step 5.2, the verifier's round) OUT OF IDEAS is the lost walk's last word, never a led one's: no run of a plan
    # that goes by what the game says ends with it (pre-registered `OUT_OF_IDEAS_LED_MAX`); NOHINTS's are reported
    led = [(r["plan"], r["seed"], str(r.get("reason"))[:120]) for r in real if r["plan"] != "NOHINTS" and r.get("out_of_ideas")]
    out.append(grade("R5.OUT_OF_IDEAS", len(led) <= BOUNDS["OUT_OF_IDEAS_LED_MAX"],
                f"OUT OF IDEAS ONLY WITH NO LEAD (the plans that go by what the game says: {[p for p in REAL_PLANS if p != 'NOHINTS']}): "
                f"runs ended 'out of ideas' {len(led)} (bound <= {BOUNDS['OUT_OF_IDEAS_LED_MAX']}): {led or 'none'}",
                len(real), 1))
    nohints = good("NOHINTS")
    if nohints:
        gave_up = [(r["seed"], r["frames"]) for r in nohints if r.get("out_of_ideas")]
        out.append(grade("R5.NOHINTS_IDEAS", True,
                         f"(reported) NOHINTS (no hint ever used) ended 'out of ideas' in {len(gave_up)} of {len(nohints)} runs "
                          f"(seed, frames): {gave_up}; the others: "
                          f"{[(r['seed'], str(r.get('reason'))[:60]) for r in nohints if not r.get('out_of_ideas')]}",
                          len(nohints)))
    idle = {plan: [c for r in good(plan) for c in r.get("chats_idle", [])] for plan in REAL_PLANS}
    out.append(grade("R5.CHATS_IDLE", True,
                     f"(reported) the chats the GAME says told it nothing new (count, own frames) by plan: "
                      f"{ {plan: (len(c), sum(f for _, f in c)) for plan, c in idle.items()} }; the game's message reads "
                      f"that failed: {sum(r.get('text_errors') or 0 for r in every)}", len(real)))
    # (the verifier's second round: the README said a talk was "counted by both paths" while the GAME's path, which grades
    # NO LOAFING, credited it in all 20 cases and the AI's in none; no line showed the two verdicts side by side)
    had = sum(r.get("talks_ai") or 0 for r in real)
    apart = [(r["plan"], r["seed"], *t) for r in real for t in r.get("talks_apart") or ()]
    out.append(grade("R5.TALKS_PATHS", True,
                     f"(reported) THE TWO PATHS ON THE TALKS (a chat's or a detour's talk the AI had: words never read by "
                      f"its record, a page never shown by the game's): they agree on 'told something new' in "
                      f"{had - len(apart)} of {had}; apart (plan, seed, frame, kind, the AI, the game): {apart[:12] or 'none'}",
                      had))
    return out


def chapter2_verdicts(rows: dict[str, list[dict]]) -> list[Check]:
    """(the step-5.1 verifier's second round) CHAPTER 2 in the sweep (`CHAPTER2`), each check pre-registered in `BOUNDS`:
    WALLY's tutorial by the game; the intent-mix floor and the curiosity the story did not need in EVERY run (the live CH2T
    arm FAILED the floor); a new place is new to the world memory it started from; the beeline control's chapter 2 under
    the floor (the floor has teeth in chapter 2) and faster to WALLY outside the needs. The stall property, the asides, the
    pages and the losses of these runs are graded with every real plan's above. (Build step 5.3, A1-1) Typed: the two
    shares of frames and CH2_OFF are REPORTED (their old bound's verdict kept); A NEW PLACE IS NEW is HONESTY, its game
    half the maps chapter 1's GAME screen stood on (`seen_maps`), no longer the AI's world memory."""
    out: list[Check] = []
    played = [r for r in rows.get("CH2", []) if "error" not in r]
    skipped = [(r["seed"], r["error"][:80]) for r in rows.get("CH2", []) if "error" in r]
    off = [r for r in rows.get("CH2_OFF", []) if "error" not in r]
    if not played:
        return out
    reached = [r for r in played if r["wally"]]
    out.append(grade("R5.CH2_WALLY", len(reached) >= BOUNDS["CH2_REACHED_MIN"] * len(played),
                f"CH2: WALLY's tutorial reached (the game: HIDE_PETALBURG_CITY_WALLYS_MOM and VAR_PETALBURG_GYM_STATE >= 2) in "
                f"{len(reached)} of {len(played)} chapter-2 runs (bound >= {BOUNDS['CH2_REACHED_MIN']:.0%}), each from its "
                f"own chapter 1's end; the frames {[(r['seed'], r['frames']) for r in played]}; not played (chapter 1 did "
                f"not reach the POKéDEX): {skipped or 'none'}; the ends of those that did not reach it "
                f"{[(r['seed'], r['reason'][:70]) for r in played if not r['wally']] or 'none'}", len(played), 1))
    shares = {r["seed"]: (r["personality"][0], r["mix"]["errand_share"]) for r in played}
    low = {s: v for s, v in shares.items() if v[1] < BOUNDS["MIX_MIN"]}
    out.append(grade("R5.CH2_INTENT_MIX", not low,
                     f"CH2: THE INTENT MIX, a FLOOR in EVERY chapter-2 run (the live CH2T arm FAILED it; honest: a "
                         f"goal ends at its end record, a curiosity goal the story moved on in is the story's): the share "
                         f"of the goals' frames on errands {dict(sorted(shares.items()))} (bound >= {BOUNDS['MIX_MIN']}); "
                         f"under: {low or 'none'}; reported, with the scenes between goals counted as the story's time: "
                         f"{ {r['seed']: r['mix'].get('errand_share_with_scenes') for r in played} }", len(played)))
    free = {r["seed"]: (r["personality"][0], r["mix"]["free_share"]) for r in played}
    short = {s: v for s, v in free.items() if v[1] < BOUNDS["FREE_RUN_MIN"]}
    out.append(grade("R5.CH2_FREE", not short,
                     f"CH2: CURIOSITY THE STORY DID NOT NEED in EVERY chapter-2 run {dict(sorted(free.items()))} "
                           f"(bound >= {BOUNDS['FREE_RUN_MIN']}); under: {short or 'none'}", len(played)))
    old = [(r["seed"], r["old_places"][:2]) for r in played if r["old_places"]]
    out.append(grade("R5.CH2_NEW_PLACE", not old,
                     f"CH2: A NEW PLACE IS NEW (every look-around draw names a map its chapter 1 had the player stand on by "
                         f"the GAME's screen, the seen tiles' maps, not the AI's world memory): draws "
                         f"{[(r['seed'], r['place_draws']) for r in played]}, judged {sum(r.get('place_draws_judged') or 0 for r in played)} "
                         f"(a run whose chapter 1 left no seen tiles is not judged); a known one called new: {old or 'none'}",
                     sum(r.get("place_draws_judged") or 0 for r in played), 1))
    whiteouts = sum(r["losses_game"] for r in played)
    out.append(grade("R5.CH2_WHITEOUTS", whiteouts <= BOUNDS["CH2_WHITEOUTS_MAX"],
                f"CH2: the game's whiteouts over the chapter-2 runs together {whiteouts} (bound <= "
                f"{BOUNDS['CH2_WHITEOUTS_MAX']}), per seed {[(r['seed'], r['losses_game']) for r in played if r['losses_game']]}",
                len(played), 1))
    if off:
        under = [r["seed"] for r in off if r["mix"]["errand_share"] < BOUNDS["MIX_MIN"]]
        out.append(grade("R5.CH2_OFF_UNDER", len(under) >= BOUNDS["CH2_OFF_UNDER_MIN"] * len(off),
                    f"CH2_OFF (the beeline control's chapter 2): under the intent-mix floor in {len(under)} of {len(off)} "
                    f"(bound >= {BOUNDS['CH2_OFF_UNDER_MIN']:.0%}: the floor separates the arms in chapter 2, where no "
                    f"training fills it): {dict(sorted((r['seed'], r['mix']['errand_share']) for r in off))}; its curiosity "
                    f"the story did not need {sorted({r['mix']['free_share'] for r in off})}", len(off)))
        by_off = {r["seed"]: r for r in off}
        pairs = [(r, by_off[r["seed"]]) for r in played if r["seed"] in by_off and r.get("time_wally")
                 and by_off[r["seed"]].get("time_wally")]
        outside = [(a["seed"], a["time_wally"]["outside_nb"], b["time_wally"]["outside_nb"]) for a, b in pairs]
        pooled = sum(x for _, x, _ in outside) / max(1, sum(y for _, _, y in outside)) if outside else 0.0
        slower = [s for s, x, y in outside if x > y]
        out.append(grade("R5.CH2_NOBATTLE", bool(outside) and pooled >= BOUNDS["CH2_NOBATTLE_RATIO_MIN"]
                         and len(slower) >= BOUNDS["CH2_NOBATTLE_SEEDS_MIN"] * len(outside),
                    f"CH2: NO SPEEDRUN, WITHOUT THE GRASS'S DICE: the AI's own frames to WALLY outside the needs and the "
                    f"battles met on the way, CH2 over CH2_OFF pooled {round(pooled, 3)} (bound >= "
                    f"{BOUNDS['CH2_NOBATTLE_RATIO_MIN']}), CH2 the slower in {len(slower)} of {len(outside)} paired seeds "
                    f"(bound >= {BOUNDS['CH2_NOBATTLE_SEEDS_MIN']:.0%}): (seed, CH2, CH2_OFF) {outside}", len(outside), 1))
    return out


def step51_verdicts(rows: dict[str, list[dict]]) -> list[Check]:
    """(build step 5.1) The new checks, each pre-registered in `BOUNDS` (module docstring). (Build step 5.3, A1-1) Typed:
    the asides, the go goals after their pages and THE ERRANDS DIFFER are DIAGNOSTIC; the shares of frames REPORTED;
    PATIENCE_OLD is graded by the GAME (the run ended early without the POKéDEX), its own word DIAGNOSTIC."""
    out: list[Check] = []
    bound = BOUNDS["AWAIT_MAX"]

    def good(plan: str) -> list[dict]:
        return [r for r in rows.get(plan, []) if "error" not in r]

    # THE STALL PROPERTY (the step-5 verifier's FAILURE): in every run of the real code, no screen waited for a press
    # `AWAIT_MAX` frames or more with none, by the AI's own record AND by the game's (the second path); whatever the reason
    real = [r for plan in REAL_PLANS for r in good(plan)]
    if real:
        long_ = [(r["plan"], r["seed"], r["await_ai_max"], r["await_game_max"], r["await_ai_long"][:1]) for r in real
                 if r["await_ai_max"] >= bound or (r["await_game_max"] or 0) >= bound]
        out.append(grade("R5.STALL", not long_,
                         f"THE STALL PROPERTY (every run of {list(REAL_PLANS)}, {len(real)} runs): the longest a screen "
                               f"waited for a press with none, by the AI's record {max(r['await_ai_max'] for r in real)} "
                               f"frames, by the GAME's (second path) {max((r['await_game_max'] or 0) for r in real)} "
                               f"(bound under {bound}, whatever reason was given); over it: {long_ or 'none'}", len(real), 1))
        missing = [(r["plan"], r["seed"]) for r in real if not r.get("await_game_samples")]
        out.append(grade("R5.STALL_SECOND_PATH", not missing,
                         f"THE STALL PROPERTY's second path read the game in every run (samples "
                                 f"{sorted({r.get('await_game_samples') or 0 for r in real})[:3]}...): unread {missing or 'none'}",
                         len(real), 1))
    for plan in ("STALL1", "STALL2", "STALL3"):
        runs = good(plan)
        if not runs:
            continue
        hit = [(r["seed"], r["await_ai_max"], r["await_game_max"]) for r in runs
               if r["await_ai_max"] >= bound and (r["await_game_max"] or 0) >= bound]
        out.append(grade(f"R5.{plan}", len(hit) >= BOUNDS["STALL_ARM_HITS_MIN"],
                    f"{plan} (the fix REVERTED in a copy, {MUTANT_PLANS[plan]}): the stall property FAILS (both paths at or "
                    f"over {bound}) in {len(hit)} of {len(runs)} runs (bound >= {BOUNDS['STALL_ARM_HITS_MIN']}): {hit}; "
                    f"what waited: {[r['await_ai_long'][:1] for r in runs if r['await_ai_long']][:3]}", len(runs), 1))
    # the two paths AGREE on the verdict run by run, in every plan
    every = [r for plan_rows in rows.values() for r in plan_rows if "error" not in r and r.get("await_game_max") is not None]
    split = [(r["plan"], r["seed"], r["await_ai_max"], r["await_game_max"]) for r in every
             if (r["await_ai_max"] >= bound) != (r["await_game_max"] >= bound)]
    if every:
        out.append(grade("R5.STALL_PATHS_AGREE", not split,
                         f"THE TWO PATHS AGREE on the stall verdict (AI record vs the game's) in {len(every) - len(split)} "
                               f"of {len(every)} runs; apart: {split or 'none'}", len(every), 1))
    # (the verifier's round) a story goal put aside comes back after a breather: no streak of asides longer than the bound
    if real:
        streaks = [(r["plan"], r["seed"], s) for r in real for s in r.get("asides") or []]
        long_asides = [s for s in streaks if s[2][2] > BOUNDS["ASIDE_STREAK_MAX"]]
        out.append(grade("R5.ASIDE_BACK", not long_asides,
                         f"A STORY GOAL PUT ASIDE COMES BACK (every run of {list(REAL_PLANS)}): streaks of goals "
                                     f"put aside for a story goal (plan, seed, (goal, first frame, frames, asides)) "
                                     f"{streaks[:12] or 'none (not exercised in this sweep)'}; longest "
                                     f"{max((s[2][2] for s in streaks), default=0)} frames (bound <= "
                                     f"{BOUNDS['ASIDE_STREAK_MAX']}); over it: {long_asides or 'none'}", len(streaks)))
    # every go goal with a map came after the page that told it (the review's finding 6)
    if real:
        bad = [(r["plan"], r["seed"], r["told_before_bad"][:2]) for r in real if r["told_before_bad"]]
        out.append(grade("R5.GO_AFTER_PAGE", not bad,
                         f"EVERY GO GOAL WITH A MAP CAME AFTER THE PAGE THAT TOLD IT (the AI's read records), {len(real)} "
                             f"runs: off {bad or 'none'}", len(real)))
    ch1, off = good("CH1"), good("ERRANDS_OFF")
    if ch1:
        # THE INTENT MIX (the review's finding 1): every personality spends at least its share of the goals' frames on errands
        by, curious = {}, {}
        for r in ch1:
            by.setdefault(r["personality"], []).append(r["mix"]["errand_share"])
            curious.setdefault(r["personality"], []).append(r["mix"]["curiosity_share"])
        low = {p: [s for s in shares if s < BOUNDS["MIX_MIN"]] for p, shares in by.items()}
        low = {p: s for p, s in low.items() if s}
        thin = {p: round(sum(s) / len(s), 4) for p, s in curious.items()
                if sum(s) / len(s) < BOUNDS["CURIOSITY_MIN"]}
        kinds = sorted({k for r in ch1 for k in r["mix"]["kinds"]})
        out.append(grade("R5.CH1_INTENT_MIX", not low and not thin and {"explore", "detour"} <= set(kinds),
                    f"THE INTENT MIX (CH1): the share of the goals' frames spent on errands, by personality "
                    f"{ {p: sorted(s) for p, s in by.items()} } (bound >= {BOUNDS['MIX_MIN']} in EVERY run: a FLOOR on needs "
                    f"and curiosity together, which the beeline control meets too, the verifier's round: the curiosity "
                    f"checks below are what separate the arms); on errands of CURIOSITY ({list(CURIOSITY_KINDS)}) {curious} "
                    f"(bound: each personality's mean >= {BOUNDS['CURIOSITY_MIN']}); the errand kinds played {kinds} (the "
                    f"look-around and the detour among them); under: {low or 'none'}, {thin or 'none'}", len(ch1)))
        # (the verifier's round: "per-run curiosity can be almost zero, because the bound is a per-personality mean", and
        # "the pick_up is the rival's POKé BALL, a step the story requires") CURIOSITY THE STORY DID NOT NEED, in EVERY run
        free = {r["seed"]: (r["personality"], r["mix"]["free_share"], r["mix"]["free_frames"]) for r in ch1}
        short = {seed: v for seed, v in free.items() if v[1] < BOUNDS["FREE_RUN_MIN"]}
        by_free: dict[str, list[float]] = {}
        for personality, share, _ in free.values():
            by_free.setdefault(personality, []).append(share)
        means = {p: round(sum(s) / len(s), 4) for p, s in by_free.items()}
        own = sorted({(k, f) for r in ch1 for _, k, f in r["mix"]["story_own"]})[:6]
        out.append(grade("R5.CH1_FREE", not short and all(m >= BOUNDS["FREE_MEAN_MIN"] for m in means.values()),
                    f"CURIOSITY THE STORY DID NOT NEED (CH1; a curiosity goal in which a milestone passed is the story's "
                    f"own: {len(own)} kinds/frames, e.g. {own[:3]}): the share of the goals' frames in EVERY run "
                    f"{ {s: v[1] for s, v in sorted(free.items())} } (bound >= {BOUNDS['FREE_RUN_MIN']} each), frames "
                    f"{ {s: v[2] for s, v in sorted(free.items())} }; each personality's mean {means} (bound >= "
                    f"{BOUNDS['FREE_MEAN_MIN']}); under: {short or 'none'}", len(ch1)))
        div = divergence(ch1)
        out.append(grade("R5.SEED_DIVERGENCE", div["goals_mean"] is not None and div["goals_mean"] >= BOUNDS["DIV_GOALS_MIN"]
                    and div["tiles_mean"] >= BOUNDS["DIV_TILES_MIN"] and not div["identical"],
                    f"SEED DIVERGENCE (CH1, every pair of runs of one personality; pillar 5: seeds differ; the beeline "
                    f"control's dice and personality meet this too, the verifier's round: the OFF-THE-BEELINE checks below "
                    f"are the errands' own): goal sequences {div['goals_mean']} "
                    f"(bound >= {BOUNDS['DIV_GOALS_MIN']}), paths {div['tiles_mean']} (bound >= {BOUNDS['DIV_TILES_MIN']}), "
                    f"identical pairs {div['identical'] or 'none'}; pairs {[(p['seeds'], p['goals'], p['tiles']) for p in div['pairs']]}",
                    len(div["pairs"]), 1))
    if ch1 and off:
        # the beeline control MOVES every metric: less errand time, less divergence, and the POKéDEX sooner
        by_off = {r["seed"]: r for r in off}
        pairs = [(r, by_off[r["seed"]]) for r in ch1 if r["seed"] in by_off]
        drops = [round(a["mix"]["curiosity_share"] - b["mix"]["curiosity_share"], 3) for a, b in pairs]
        mean_drop = sum(drops) / len(drops) if drops else 0.0
        out.append(grade("R5.OFF_MOVES_MIX", bool(drops) and mean_drop >= BOUNDS["MIX_DROP_MIN"],
                    f"ERRANDS_OFF MOVES THE INTENT MIX: CH1 - ERRANDS_OFF share of the frames on curiosity, paired by seed, "
                    f"{drops}, mean {mean_drop:.3f} (bound >= {BOUNDS['MIX_DROP_MIN']}); all errands (reported) "
                    f"{[round(a['mix']['errand_share'] - b['mix']['errand_share'], 3) for a, b in pairs]}", len(drops)))
        div_on, div_off = divergence(ch1), divergence(off)
        out.append(grade("R5.OFF_MOVES_DIVERGENCE", div_off["goals_mean"] is not None and div_on["goals_mean"] is not None
                    and div_on["goals_mean"] > div_off["goals_mean"],
                    f"ERRANDS_OFF MOVES THE DIVERGENCE: goal sequences {div_on['goals_mean']} (CH1) vs {div_off['goals_mean']} "
                    f"(ERRANDS_OFF, bound: CH1 more); paths {div_on['tiles_mean']} vs {div_off['tiles_mean']} (reported)",
                    min(len(div_on["pairs"]), len(div_off["pairs"])), 1))
        # (the verifier's round) the control FAILS the per-run curiosity bound: the check is not met by a beeline
        off_free = {r["seed"]: r["mix"]["free_share"] for r in off}
        failing = [s for s, share in off_free.items() if share < BOUNDS["FREE_RUN_MIN"]]
        out.append(grade("R5.BEELINE_FAILS_FREE", len(failing) >= BOUNDS["FREE_CONTROL_FAILS_MIN"] * len(off),
                    f"THE BEELINE FAILS THE CURIOSITY BOUND: ERRANDS_OFF runs under {BOUNDS['FREE_RUN_MIN']} (the curiosity "
                    f"the story did not need) {len(failing)} of {len(off)} (bound >= {BOUNDS['FREE_CONTROL_FAILS_MIN']:.0%}): "
                    f"{dict(sorted(off_free.items()))}", len(off)))
        # (the verifier's round) WHERE NO BEELINE WENT: the errands' own footprint, against the beeline's own spread
        beeline = off_beeline(ch1, off)
        paired = [(seed, beeline["runs"][seed], beeline["control"][seed]) for seed in sorted(beeline["runs"])
                  if seed in beeline["control"]]
        more = [p for p in paired if p[1] > p[2]]
        pooled = (sum(p[1] for p in paired) / max(1, sum(p[2] for p in paired))) if paired else 0.0
        out.append(grade("R5.OFF_BEELINE", bool(paired) and len(more) >= BOUNDS["OFF_SEEDS_MIN"] * len(paired)
                    and pooled >= BOUNDS["OFF_RATIO_MIN"],
                    f"OFF THE BEELINE (the tiles a run stood on that NO beeline-control run stood on; a control run against "
                    f"the OTHER control runs, its own spread): CH1 vs ERRANDS_OFF by seed {paired}; CH1 more in "
                    f"{len(more)} of {len(paired)} (bound >= {BOUNDS['OFF_SEEDS_MIN']:.0%}), pooled {round(pooled, 2)}x "
                    f"(bound >= {BOUNDS['OFF_RATIO_MIN']}); the corridor {beeline['corridor']} tiles", len(paired), 1))
        # (the verifier's round: "the divergence comes mostly from battle dice and personality, not from the new errands")
        # the ERRANDS' OWN divergence: their decisions in order (`curiosity_sequence`) differ between the seeds of one
        # personality, where the beeline control has none at all; where they took the player is reported beside it
        cur_on = sequence_divergence(ch1, "curious_sequence")
        cur_off = sequence_divergence(off, "curious_sequence")
        out.append(grade("R5.ERRANDS_DIFFER", cur_on["mean"] is not None and cur_on["mean"] >= BOUNDS["CUR_DIV_MIN"],
                    f"THE ERRANDS DIFFER BY SEED: the curiosity decisions in order (kind@map) of every pair of CH1 runs of "
                    f"one personality, mean edit distance {cur_on['mean']} (bound >= {BOUNDS['CUR_DIV_MIN']}; the same "
                    f"sequence in {cur_on['same'] or 'no pair'}); the beeline control's {cur_off['mean']} (none to differ); "
                    f"pairs {[(p['seeds'], p['distance']) for p in cur_on['pairs']]}; the CH1 sequences "
                    f"{ {r['seed']: r['curious_sequence'] for r in ch1} }; the off-the-beeline tiles' mean Jaccard distance "
                    f"between those pairs {beeline['pairs_mean']} (reported)", len(cur_on["pairs"])))
        both = [(a, b) for a, b in pairs if a["dex_frame"] and b["dex_frame"]]
        outside = [(a["dex_frame"] - needs(a), b["dex_frame"] - needs(b)) for a, b in both]
        ratio = sum(x for x, _ in outside) / sum(y for _, y in outside) if outside else 0.0
        slower = [(a["seed"], round(x / y, 3)) for (a, _), (x, y) in zip(both, outside) if y and x > y]
        total = (sum(a["dex_frame"] for a, _ in both) / sum(b["dex_frame"] for _, b in both)) if both else 0.0
        over = [r["seed"] for r in ch1 if r["reached"] and (r["dex_frame"] or 0) > BOUNDS["DEX_FRAMES_MAX"]]
        # (the verifier's round: "the NO SPEEDRUN margin is within noise") the decomposition, per paired seed: what the
        # errands ADD (their frames) and what the story's own goals TAKE LESS (a place looked round is walked faster later)
        story = [(a["seed"], (a["dex_frame"] - needs(a) - a["mix"]["free_frames"]) - (b["dex_frame"] - needs(b)
                                                                                    - b["mix"]["free_frames"]))
                 for a, b in both]
        added = [(a["seed"], a["mix"]["free_frames"]) for a, _ in both]
        out.append(grade("R5.NO_SPEEDRUN", bool(both) and ratio >= BOUNDS["SLOWER_THAN_BEELINE_MIN"] and not over,
                    f"NO SPEEDRUN (the time): the frames to the POKéDEX outside the needs (training, healing, finding a "
                    f"centre, shopping), CH1 over the beeline control (ERRANDS_OFF) pooled over the paired seeds "
                    f"{round(ratio, 3)} (bound >= {BOUNDS['SLOWER_THAN_BEELINE_MIN']}: above the beeline) {outside}; CH1 the "
                    f"slower in {len(slower)} of {len(both)} paired seeds {slower} (reported: the verifier's round measured "
                    f"this margin within the noise, and the decomposition says why: the errands ADD {added} frames, and the "
                    f"rest of the way to the POKéDEX took CH1 {story} frames more (+) or fewer (-) than the control: a place "
                    f"looked round is walked faster later. The no-speedrun claim rests on the behaviour checks above, the "
                    f"curiosity the story did not need in EVERY run and the beeline failing it); the TOTAL frames to the "
                    f"POKéDEX (reported) {round(total, 3)} {[(a['dex_frame'], b['dex_frame']) for a, b in both]}; within the "
                    f"budget ({BOUNDS['DEX_FRAMES_MAX']}): over it {over or 'none'}", len(both), 1))
        # (the verifier's round) THE SAME, WITHOUT THE GRASS'S DICE: outside the needs AND outside the battles met on the
        # way (`time_to_dex`), per paired seed and pooled
        timed = [(a["seed"], a["time"], b["time"]) for a, b in pairs if a.get("time") and b.get("time")]
        nb = [(seed, ta["outside_nb"], tb["outside_nb"], round(ta["outside_nb"] / tb["outside_nb"], 3))
              for seed, ta, tb in timed if tb["outside_nb"]]
        nb_pooled = sum(x[1] for x in nb) / sum(x[2] for x in nb) if nb else 0.0
        nb_slower = [x[0] for x in nb if x[3] > 1]
        out.append(grade("R5.NO_SPEEDRUN_DICE", bool(nb) and nb_pooled >= BOUNDS["NOBATTLE_RATIO_MIN"]
                    and len(nb_slower) >= BOUNDS["NOBATTLE_SEEDS_MIN"] * len(nb),
                    f"NO SPEEDRUN, WITHOUT THE GRASS'S DICE: the AI's own frames to the POKéDEX outside the needs AND outside "
                    f"the battles met on the way (its walking, talking and looking), CH1 over the beeline control pooled "
                    f"{round(nb_pooled, 3)} (bound >= {BOUNDS['NOBATTLE_RATIO_MIN']}) and per paired seed (seed, CH1, "
                    f"control, ratio) {nb}: CH1 the slower in {len(nb_slower)} of {len(nb)} (bound >= "
                    f"{BOUNDS['NOBATTLE_SEEDS_MIN']:.0%}); the battles' frames outside the needs (CH1, control) "
                    f"{[(seed, ta['battles'], tb['battles']) for seed, ta, tb in timed]}", len(nb), 1))
    # (the verifier's round: "MAX_LOSSES 3 was never reached by an unaltered run") LOSE3: the decider made to lose its wild
    # battles once trained (a copy: a status move every turn, never a run, mutant LOSE3); the play loop's REAL MAX_LOSSES (3)
    # must end the run at the game's third loss, its report, its told losses and the game's all 3
    lose = good("LOSE3")
    if lose:
        # (build step 5.3, A1-2) the play loop's MAX_LOSSES as the HARNESS recorded it for these runs (`max_losses` in the
        # PLAY json), no longer imported from the AI's `mode.py`; rows without that record (built before 5.3) read the
        # grader-owned copy; runs that recorded DIFFERENT values fail the check (one arm, one stop)
        recorded = sorted({r.get("max_losses") for r in lose} - {None})
        MAX_LOSSES = recorded[0] if recorded else MAX_LOSSES_DEFAULT
        want = f"play: stuck: {MAX_LOSSES} battles lost (MAX_LOSSES {MAX_LOSSES})"
        rows3 = [(r["seed"], r["reason"], r["losses_ai"], r["losses_told"], r["losses_game"], r["last_loss_f"], r["frames"])
                 for r in lose]
        # (CORRECTED 2026-10-14 after the graded sweep on 501-520 FAILED it in 1 of 6 runs: seed 503 lost twice, then met
        # a wild battle the mutant's status move could not lose within the battle skill's 150 menus, and the run ended on
        # its patience with 2 losses: a run that never reached a third loss tests nothing of the stop) the stop is graded on
        # every run the GAME recorded a THIRD loss in; the arm must reach one in at least LOSE3_REACH_MIN of its runs
        reached3 = [row for row in rows3 if row[4] >= MAX_LOSSES]
        bad3 = [row for row in reached3 if not (row[1] == want and row[2] == row[3] == row[4] == MAX_LOSSES
                                                and row[5] is not None and 0 <= row[6] - row[5] <= STOP_WITHIN)]
        out.append(grade("R5.LOSE3", bool(reached3) and not bad3 and len(recorded) <= 1
                         and len(reached3) >= BOUNDS["LOSE3_REACH_MIN"] * len(rows3),
                    f"LOSE3 (a copy whose decider loses its wild battles once trained, mutant LOSE3; the play loop's "
                    f"MAX_LOSSES {MAX_LOSSES} untouched, as the harness recorded it {recorded or 'nowhere: the grader copy'}): "
                    f"every run the GAME recorded a loss number {MAX_LOSSES} in "
                    f"({len(reached3)} of {len(rows3)}, bound >= {BOUNDS['LOSE3_REACH_MIN']:.0%}) ends {want!r} within "
                    f"{STOP_WITHIN} frames of it, its report == its told == the game's == {MAX_LOSSES}: (seed, reason, "
                    f"report, told, game, the game's last loss, the run's end) {rows3}; off: {bad3 or 'none'}", len(rows3), 1))
    pat, old = good("PATIENCE"), good("PATIENCE_OLD")
    if pat and old:
        reached = [r["seed"] for r in pat if r["reached"]]
        stopped = [r["seed"] for r in old if str(r["reason"]).startswith("play: stuck: no progress for")]
        spans = {r["seed"]: r["train_span"] for r in pat}
        long_spans = [s for s, span in spans.items() if (span or 0) > SMALL_PATIENCE]
        out.append(grade("R5.PATIENCE", len(reached) >= BOUNDS["PATIENCE_REACHED_MIN"] * len(pat) and bool(long_spans)
                    and all(s in reached for s in long_spans),
                    f"PATIENCE (STORY_PATIENCE {SMALL_PATIENCE} in a copy, the real rule): the POKéDEX reached in "
                    f"{len(reached)} of {len(pat)} (bound >= {BOUNDS['PATIENCE_REACHED_MIN']:.0%}); a TRAINING stint longer "
                    f"than the patience (first to last train goal, frames) in seeds {long_spans} (>= 1: not vacuous), each "
                    f"reached; spans {spans}; the ends {[r['reason'][:60] for r in pat if not r['reached']]}", len(pat), 1))
        # (build step 5.3, A1-1: critic Q1) PATIENCE_OLD is the CONTROL of the patience A/B, graded by the GAME and the
        # harness: the run ENDED EARLY (its frames under its budget) WITHOUT the POKéDEX (the game's flag); measured on ledger
        # #34 in 7 of 7 and 7 of 7. Its own word (the stop reason, the last goal a training session) is DIAGNOSTIC below.
        early = [r["seed"] for r in old if not r["reached"] and r.get("budget") is not None
                 and isinstance(r.get("frames"), int) and r["frames"] < r["budget"]]
        out.append(grade("R5.PATIENCE_OLD", len(early) >= BOUNDS["PATIENCE_OLD_STOPS_MIN"] * len(old),
                    f"PATIENCE_OLD (the same, with the step-5 rule: only a milestone resets the patience, G67): ended "
                    f"EARLY without the POKéDEX (the game's flag unset, the run's frames under its budget) in {len(early)} "
                    f"of {len(old)} (bound >= {BOUNDS['PATIENCE_OLD_STOPS_MIN']:.0%}): {early}; (seed, frames, budget) "
                    f"{[(r['seed'], r.get('frames'), r.get('budget')) for r in old]}; reached "
                    f"{[r['seed'] for r in old if r['reached']]}", len(old), 1))
        training = [r["seed"] for r in old if r["seed"] in stopped and r["last_goal"] == "train"]
        out.append(grade("R5.PATIENCE_OLD_WORD", len(stopped) >= BOUNDS["PATIENCE_OLD_STOPS_MIN"] * len(old)
                         and bool(training),
                    f"PATIENCE_OLD's own word: stopped "
                    f"'no progress for ...' in {len(stopped)} of {len(old)} (bound >= {BOUNDS['PATIENCE_OLD_STOPS_MIN']:.0%}): "
                    f"{stopped}, WHILE TRAINING (its last goal a training session) in {training} (>= 1: the review's case); "
                    f"its training sessions before the stop {[(r['seed'], r['trains']) for r in old]}", len(old)))
    return out


#: (build step 5.3, A1-3: the step-5.3 critic's Q5 items 5-7) the FILES a verdict depends on, hashed by content into
#: `registered_numbers`: the mark set the harness reads the story by (an AI file: `knowledge/milestones.json`) and its item
#: flags; the typing's two lists (`b1_debt.json`, `grader_waivers.json`); the framework's map table the place checks key
#: maps by (`MapRSE`, A1-2); and THE CHECK CODE itself, so a verdict function edited between `--register` and the run is
#: refused by the ledger (before 5.3 `ledger.begin` wrote the tree but compared only the numbers)
GATES_DIR = Path(__file__).resolve().parent
HASHED_FILES = {
    "ai_player/knowledge/milestones.json": REPO / "ai_player" / "knowledge" / "milestones.json",
    "ai_player/gates/fixtures/item_flags.json": GATES_DIR / "fixtures" / "item_flags.json",
    "ai_player/gates/b1_debt.json": GATES_DIR / "b1_debt.json",
    "ai_player/gates/grader_waivers.json": GATES_DIR / "grader_waivers.json",
    "sandbox-pokebot/modules/map_data.py": MAP_DATA,
    "ai_player/gates/rate_step5.py": GATES_DIR / "rate_step5.py",
    "ai_player/gates/live_step5.py": GATES_DIR / "live_step5.py",
    "ai_player/gates/play_harness.py": HARNESS,
    "ai_player/gates/window.py": GATES_DIR / "window.py",
    "ai_player/gates/grader_checks.py": GATES_DIR / "grader_checks.py",
    # (A1 fix round: the stage-A1 verifier's weak proof, "verdict inputs still unhashed") the other check code a verdict
    # calls: the harness's `truth` read (live L5.NAME_GENDER, L5.STARTER_OT, L5.BALLS), the purity checks and `classify_a`
    # (`live_step2`), the A press kinds `classify_a` uses (`probe_presses.gate_kind`) and `probe_eyes`, which
    # `probe_presses` imports at load (the verifier found each unhashed). (`revert_step5.make_copy` builds a plan's mutant COPY, the code that PLAYS, which `MUTANT_EDITS`
    # already hashes by its edit texts; no verdict calls it, so `revert_step5.py` is not hashed here.)
    "ai_player/gates/hands_harness.py": GATES_DIR / "hands_harness.py",
    "ai_player/gates/live_step2.py": GATES_DIR / "live_step2.py",
    "ai_player/gates/probe_presses.py": GATES_DIR / "probe_presses.py",
    "ai_player/gates/probe_eyes.py": GATES_DIR / "probe_eyes.py",
}
#: (build step 5.3, A1-3: Q5 item 5) the harness parameters a game-side number depends on, read from `play_harness.py`'s
#: OWN text (`harness_parameters`): (kind, where, name). "constant": a module constant; "default": a parameter's default in
#: a class's `__init__`; "cli": an `--option`'s default in `main` (the story recorder's period: this sweep passes none)
HARNESS_PARAMETERS = (("constant", None, "STEP_RATE"), ("constant", None, "PUSH_KEEP"), ("constant", None, "WAIT_KEEP"),
                      ("cli", "main", "--every"), ("default", "PlaceRecorder", "every"), ("default", "WaitRecorder", "every"))


def file_sha256(path: Path) -> str:
    """The sha256 of a file's content with its line ends made "\\n" (the same text checked out on another computer, whose
    git turns line ends into "\\r\\n", hashes the same). A missing file RAISES: a hash of nothing would register nothing."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def harness_parameters(path: Path | None = None) -> dict[str, int]:
    """(Build step 5.3, A1-3) each `HARNESS_PARAMETERS` value, read from the harness's source (`HARNESS`) by its syntax tree
    (the harness is not imported: it loads the emulator's framework). RAISES when one is missing, so a rename cannot drop
    a parameter from the hash without a word."""
    import ast

    tree = ast.parse(Path(path or HARNESS).read_text(encoding="utf-8"))
    found: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value.value
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    pairs = list(zip(item.args.args[len(item.args.args) - len(item.args.defaults):], item.args.defaults))
                    pairs += list(zip(item.args.kwonlyargs, item.args.kw_defaults))
                    for arg, default in pairs:
                        if isinstance(default, ast.Constant):
                            found[f"{node.name}.{arg.arg}"] = default.value
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            for call in ast.walk(node):
                if (isinstance(call, ast.Call) and getattr(call.func, "attr", None) == "add_argument" and call.args
                        and isinstance(call.args[0], ast.Constant)):
                    for keyword in call.keywords:
                        if keyword.arg == "default" and isinstance(keyword.value, ast.Constant):
                            found[f"main {call.args[0].value}"] = keyword.value.value
    out = {}
    for kind, where, name in HARNESS_PARAMETERS:
        key = name if kind == "constant" else f"{where}.{name}" if kind == "default" else f"{where} {name}"
        if key not in found:
            raise ValueError(f"play_harness.py no longer defines the harness parameter {key!r} (`HARNESS_PARAMETERS`)")
        out[key] = found[key]
    return out


def registered_numbers(plans: list[str], frames: int, target: str) -> dict:
    """(Build step 5.2, G2) EVERY number a sweep's verdict depends on, whose sha256 a graded range is REGISTERED with in the
    seed ledger (`gates/ledger.py`) before it runs: the bounds, the constants the checks use, the plans and their faults,
    and the run's frames and target. (Build step 5.3, A1-3: the step-5.3 critic's Q5) also the mutant edit TEXTS the plans
    are played with, the grader's other constants (and its A1-2 copies of the AI's values), the bounds that were literals
    in the verdict code (`CODE_BOUNDS`), the harness's parameters, and the sha256 of every file in `HASHED_FILES`, the
    check code included: `ledger.begin` refuses a graded run whose numbers differ from its registration, so an edit of any
    of these after `--register` is refused."""
    return {"BOUNDS": BOUNDS, "SMALL_PATIENCE": SMALL_PATIENCE, "STOP_WITHIN": STOP_WITHIN, "STOP_REASON": STOP_REASON,
            "GAME_CLOCK": GAME_CLOCK, "WALL_CLOCK": WALL_CLOCK, "PLANS": PLANS, "MUTANT_PLANS": MUTANT_PLANS,
            "STOP_PLANS": STOP_PLANS, "CHAPTER2": CHAPTER2, "CH2_TARGET": CH2_TARGET, "plans": plans, "frames": frames,
            "target": target,
            # (build step 5.2) the controls' own edits (an arm is what its copy does) and the yield's own numbers
            "EXTRA_EDITS": EXTRA_EDITS, "PLAN_PERSONALITY": PLAN_PERSONALITY, "YIELD_TILES": YIELD_TILES,
            "YIELD_SLACK": YIELD_SLACK, "YIELD_TILE_RATE": YIELD_TILE_RATE, "SEEING": SEEING, "P2_REPORTED": P2_REPORTED,
            # (build step 5.3, A1-3) Q5 item 1: the edit texts of every plan's copy
            "MUTANT_EDITS": mutant_edits(),
            # Q5 items 2 and 3: the grader's constants, and its own copies of the AI's values (A1-2)
            "END_SLACK": END_SLACK, "CURIOSITY_KINDS": CURIOSITY_KINDS, "NEED_KINDS": NEED_KINDS,
            "GENERIC_BUSY": GENERIC_BUSY, "REAL_PLANS": REAL_PLANS, "NO_PHASE2": NO_PHASE2,
            "PERSONALITIES": PERSONALITIES, "STARTERS": STARTERS, "ERRANDS": ERRANDS, "ERRAND_KINDS": ERRAND_KINDS,
            "ASIDE": ASIDE, "MAX_LOSSES_DEFAULT": MAX_LOSSES_DEFAULT,
            # Q5 item 4: the literals of the verdict code
            "CODE_BOUNDS": CODE_BOUNDS,
            # Q5 item 5: the harness's parameters (the recorders' periods, the step rate, what a stretch keeps)
            "HARNESS_PARAMETERS": harness_parameters(),
            # Q5 items 6 and 7: the mark set, the item flags, the two typing lists, the map table and THE CHECK CODE
            "FILES": {name: file_sha256(path) for name, path in HASHED_FILES.items()}}


def grader_imports_line() -> str:
    """(Build step 5.3, A1-2) THE G-3 RULE on the tree as it stands (`check_grader_imports.scan`): its one-line verdict,
    "GRADER IMPORTS: PASS ..." or "GRADER IMPORTS: FAIL ..." with every chain by which a grader reaches the AI's code."""
    from ai_player.gates.check_grader_imports import report, scan

    return report(scan())


def main() -> int:
    global _TREE, _FOLDERS
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    from ai_player.gates import ledger as seed_ledger
    from ai_player.gates.disk_budget import SweepFolders, preflight
    from ai_player.gates.provenance import line_digest, watch

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plans", default="CH1,NOTRAIN,NOHINTS,DEADREST,ERRANDS_OFF,STALL1,STALL2,STALL3,PATIENCE,"
                                           "PATIENCE_OLD,LOSE3,CH2,CH2_OFF,LOAF,BLOCKED,GREEDY,STOP,STOPDEAD")
    parser.add_argument("--seeds", type=int, default=12)
    # (build step 5.2, G2: "no default --first-seed for a graded run") neither has a default
    parser.add_argument("--purpose", required=True, choices=seed_ledger.PURPOSES,
                        help="graded: a range REGISTERED first (--register); development; replay: seeds already played")
    parser.add_argument("--first-seed", type=int, required=True)
    parser.add_argument("--register", action="store_true",
                        help="with --purpose graded: pre-register the range and the numbers it is graded by, play nothing")
    parser.add_argument("--keep-runs", action="store_true", help="keep every run folder (a verifier's recount needs them)")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--frames", type=int, default=300000)
    parser.add_argument("--target", default="ch1_pokedex")
    parser.add_argument("--evidence-tag", default="step52")
    args = parser.parse_args()
    plans = [p.strip() for p in args.plans.split(",") if p.strip()]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    if not seeds:
        parser.error("--seeds must be at least 1")
    unknown = [p for p in plans if p not in PLANS and p not in STOP_PLANS]
    if unknown:
        parser.error(f"unknown plans {unknown}")
    orphans = [p for p in plans if p in CHAPTER2 and CHAPTER2[p] not in plans]
    if orphans:
        parser.error(f"the chapter-2 plans {orphans} go on from {[CHAPTER2[p] for p in orphans]}: name those plans too")
    # (build step 5.3, A1-2, G-3) no sweep is registered or played while a grader takes a value from the AI's code
    import_line = grader_imports_line()
    print(import_line)
    if not import_line.startswith("GRADER IMPORTS: PASS"):
        return 2
    numbers_sha = seed_ledger.numbers_sha256(registered_numbers(plans, args.frames, args.target))
    if args.register:
        if args.purpose != "graded":
            parser.error("--register pre-registers a GRADED range: pass --purpose graded")
        try:
            entry = seed_ledger.register(LEDGER_FAMILY, "rate_step5", seeds[0], seeds[-1], numbers_sha,
                                         note=f"plans {plans}, frames {args.frames}, target {args.target}")
        except seed_ledger.Refused as refusal:
            print(f"LEDGER: REFUSED - {refusal}")
            return 2
        print(f"LEDGER: REGISTERED #{entry['id']}: graded seeds {seeds[0]}-{seeds[-1]}, the numbers' sha256 "
              f"{numbers_sha[:16]} ({seed_ledger.LEDGER}); nothing was played")
        return 0
    # (G5) the disk budget, before anything is played or written
    disk_ok, disk_line = preflight()
    if not disk_ok:
        print(disk_line)
        return 2
    code = provenance(REPO)
    # (G1) this driver checks and seals its own verdict (the watch started with the code line above)
    _TREE = watch(REPO, explicit=True)
    try:
        entry, ledger_lines = seed_ledger.begin(LEDGER_FAMILY, "rate_step5", args.purpose, seeds[0], seeds[-1], numbers_sha,
                                                line_digest(code), note=f"plans {plans}, tag {args.evidence_tag}")
    except seed_ledger.Refused as refusal:
        print(f"LEDGER: REFUSED - {refusal}")
        return 2
    _FOLDERS = SweepFolders(f"step5_{args.evidence_tag}")
    lines: list[str] = []

    def say(line: str) -> None:
        print(line, flush=True)
        lines.append(line)

    # (build step 5.3: the header names the step whose grader this is; the typed checks are 5.3's)
    say(f"AI PLAYER BUILD STEP 5.3 (TYPED CHECKS, stage A1) - THE SEED SWEEP: plans {plans}, seeds {seeds[0]}-{seeds[-1]}, "
        f"frames {args.frames}, game clock {GAME_CLOCK}, wall clock set {WALL_CLOCK}")
    say(f"pre-registered bounds: {json.dumps(BOUNDS)}; SMALL_PATIENCE {SMALL_PATIENCE}")
    say(f"code: {code}")
    # (the step-5.1 verifier's second round: "the dee96b tree was not kept") the tree this sweep runs on is kept
    say(f"tree kept: {snapshot_tree(REPO)}")
    for line in ledger_lines:
        say(line)
    say(f"the numbers this sweep is graded by: sha256 {numbers_sha} (`registered_numbers`)")
    say(disk_line)
    say(f"frozen-tree watch: {len(_TREE.stats)} files, files digest {_TREE.digest} (checked before and after every run)")
    # (the step-5.1 verifier's second round) a chapter-2 plan's runs are played after their chapter-1 run, in its worker
    follow = {base: [p for p in plans if CHAPTER2.get(p) == base] for base in plans}
    jobs = [(plan, seed) for plan in plans if plan in PLANS and plan not in CHAPTER2 for seed in seeds
            if plan not in PLAN_PERSONALITY or plan_of(seed)[0] == PLAN_PERSONALITY[plan]]
    rows: dict[str, list[dict]] = {plan: [] for plan in plans}
    copies: dict[tuple[str, str], Path] = {(plan, plan): copy_with(MUTANT_PLANS[plan]) for plan in plans if plan in MUTANT_PLANS}
    for (plan, _), root in copies.items():
        say(f"plan {plan}: a COPY of the package with mutants {MUTANT_PLANS[plan]} of revert_step5.py applied, at {root}")

    def play(jobs: list[tuple[str, str | None, int]]) -> None:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {}
            for plan, base, seed in jobs:
                root = copies.get((plan, base or plan), REPO)
                if base is None:
                    futures[pool.submit(run_chain, plan, seed, args.frames, args.target, root, follow.get(plan, []))] = seed
                else:
                    futures[pool.submit(lambda *a: [run_one(*a)], plan, seed, args.frames, args.target, root, base)] = seed
            for future, seed in futures.items():
                for row in future.result():
                    rows[row["plan"]].append(row)
                    shown = {k: v for k, v in row.items() if not k.startswith("_")}
                    say(f"  {row['plan']}{' (' + row['base'] + ')' if row.get('base') else ''} seed {seed}: "
                        f"{json.dumps(shown, ensure_ascii=False)[:3000]}")

    try:
        play([(plan, None, seed) for plan, seed in jobs])
        # PHASE 2 (`STOP_PLANS`): the runs the GAME recorded a loss in, replayed with MAX_LOSSES 1 (and without the loop's
        # count): chosen by the game's own record of phase 1, before they run
        stops = [plan for plan in plans if plan in STOP_PLANS]
        lost = sorted((r["plan"], r["seed"]) for plan in plans if plan in PLANS and plan not in NO_PHASE2
                      for r in rows[plan] if "error" not in r and r["losses_game"])
        if stops:
            say(f"PHASE 2: the runs of phase 1 the game recorded a battle LOST in: {lost or 'none'}; plans {stops}")
        for stop in stops:
            for base in sorted({base for base, _ in lost}):
                copies[(stop, base)] = copy_with(MUTANT_PLANS.get(base, []) + STOP_PLANS[stop])
                say(f"plan {stop} ({base}): a COPY with {MUTANT_PLANS.get(base, []) + STOP_PLANS[stop]} applied, at "
                    f"{copies[(stop, base)]}")
        play([(stop, base, seed) for stop in stops for base, seed in lost])
    finally:
        for root in copies.values():
            shutil.rmtree(root, ignore_errors=True)
    summary = {plan: summarise(plan, sorted(rows[plan], key=lambda r: r["seed"])) for plan in plans}
    for plan in plans:
        say(f"SUMMARY {plan}: {json.dumps(summary[plan], ensure_ascii=False)}")
    results = verdicts(summary, rows)
    # (build step 5.3, A1-1) one line per check (id, kind, status, n/floor, inputs), every B1 DEBT, every property the
    # grade no longer counts; THE VERDICT by kind (`grader_checks.verdict`): every GRADED and HONESTY check PASS
    for line in evidence_lines(results):
        say(line)
    verdict = typed_verdict(results)
    # (build step 5.2, G1) the frozen-tree watch seals the verdict: FAIL when the tree moved at any check
    verdict, frozen_line = _TREE.seal(verdict)
    say(frozen_line)
    # (G5) every run folder deleted but the failing runs (all of them when the sweep FAILED) and the newest
    every = [row for plan_rows in rows.values() for row in plan_rows if row.get("_folder")]
    failing = [Path(row["_folder"]) for row in every if verdict == "FAIL" or "error" in row]
    say(_FOLDERS.tidy(failing, keep_all=args.keep_runs))
    say(f"VERDICT: {verdict} ({seed_ledger.label(args.purpose)}, seeds {seeds[0]}-{seeds[-1]}, ledger #{entry['id']})")
    out = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{args.evidence_tag}-RATE.txt"
    keep_earlier(out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        seed_ledger.finish(entry["id"], verdict, out.relative_to(REPO).as_posix())
    except seed_ledger.Refused as refusal:
        print(f"LEDGER: could not complete entry #{entry['id']}: {refusal}")
    print(f"evidence: {out}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
