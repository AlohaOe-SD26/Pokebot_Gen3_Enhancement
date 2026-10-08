"""MUTANT PROOF of AI-player build step 3 (the world model and the navigator): each rule of the REAL code, broken in a
COPY of the package, fails its predicted test of `gates/test_world.py`, or is documented as REDUNDANT ALONE with the
reason.

    py -3.12 ai_player/gates/revert_step3.py [W1,W2] [--workers N]       (exit 0 = every prediction held)

WHY (CLAUDE.md session discipline rule 6): `test_world.py`'s fault halves patch a value (the crop off, an unknown tile
priced like a known one, a bump not remembered). That shows the tests CAN fail, not that each rule in the real code
carries weight. As `revert_step2.py` does for the hands, this copies the package to a temporary folder (no states, no
evidence), applies ONE mutant's edits there (each anchor must occur exactly once, or the run aborts), runs
`gates/test_world.py` from the copy (the framework from this repo: `AI_PLAYER_TEST_SUPPORT_ROOT`), and checks the
PREDICTION: CAUGHT (every named test fails) or REDUNDANT (no test fails; the reason is written next to it). The
unchanged copy (W0) must pass every test.
Evidence: `ai_player/evidence/<date>-step3-REVERT.txt`.

BUILD STEP 3.1 (the step-3 adversarial review): W30-W43 break the rules that answer its findings, one each (W30 the
map's ends from the coordinates; W31 a stale target kept, W32 no turn-back cost; W33 a repeating scene never held against
its target; W34 a bump walls every side, W35 one bump closes the way; W36 the eyes read the warp table, W37 a closed door
forgotten, W38 an exit used regardless of its look; W39 the gate's window from the eyes; W40 an unseen stand tile; W41 the
pre-empted presses miscounted; W42 a U-turn not counted by the reversal grader; W43 the way just come in kept as an
option, found by the step-3.1 sweep); W3, W4 and W18 follow the code they break (the anchors moved).

THE STEP-3.1 VERIFIER'S ROUND: W44-W51 (W44 a scene counted per target only, not per tile it began on; W45 a tile seen in
passing counted as progress; W46 a closed door never retried when the story moves on, W47 nor after a while; W48 progress
does not lift a scene's tiles; W49-W51 the live graders that now tell the fixed code from the reverted one: a stale drop
counted as an arrival, a crossing of any edge counted for every edge, the edge check without its non-vacuity). W33 and
W37 follow the code they break.

THE STEP-3.1 VERIFIER'S SECOND ROUND: W52-W60 (W52 a scene not known by its words: the twin twice on each of her tiles;
W53 new words heard not progress: May lifts nothing; W54 after the news the same scene needs two more meetings; W55 new
words from a scene that sent the player back counted as news; W56 the verifier's own `getattr(location, 'warps')` plant;
W57 the static warp-table check without its string-constant rule; W58 game_answer never asks LOCKED after a trial the game
did not step; W59 the live grader's locked arrival only without trials; W60 a pre-registered number that misses passes;
W61 arm CLOCKS letting a clock-sensitive launcher arm pre-register its frames).
W28 follows the code it breaks (the arrival branch now also takes a locked player with trials).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from ai_player.gates.provenance import provenance  # noqa: E402

EVIDENCE = REPO / "ai_player" / "evidence"
TIMEOUT = 900

CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"

_EXCLUDED = ("brain/navigator.py", "                if self.is_excluded(target):\n",
             "                if False:  # MUTANT W12: a chosen target already found unreachable is tried again\n")
_STILL = ("brain/navigator.py", "            if still > STILL_DECISIONS:\n",
          "            if False:  # MUTANT W13: no guard against decisions that let no frame pass\n")

#: name -> (prediction, the rule that is broken, [edits], tests that MUST fail (CAUGHT) or the reason (REDUNDANT)).
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str] | str]] = {
    "W0": (CONTROL, "nothing: the unchanged copy", [], []),
    "W1": (CAUGHT, "a ledge may be entered from any side (`step_from`: the jump direction not checked)",
           [("brain/navigator.py", "        if fact.ledge != direction:\n            return None\n",
             "        if False:  # MUTANT W1\n            return None\n")],
           ["PlannerTests.test_walls_people_ledges_and_warps"]),
    "W2": (CAUGHT, "a warp or a door is a walkable tile (walked THROUGH on the way somewhere: `TileFact.walkable`)",
           [("world/memory.py", "        return not (self.blocked or self.water or self.ledge is not None or self.warp or self.door)\n",
             "        return not (self.blocked or self.water or self.ledge is not None)  # MUTANT W2\n")],
           ["PlannerTests.test_walls_people_ledges_and_warps"]),
    "W3": (CAUGHT, "an unseen tile costs what a seen one does (`step_from`: UNKNOWN_COST -> 1)",
           [("brain/navigator.py", "        return (nxt, UNKNOWN_COST + retry) if allow_unknown else None\n",
             "        return (nxt, 1.0 + retry) if allow_unknown else None  # MUTANT W3\n")],
           ["PlannerTests.test_unknown_is_optimistic_but_dearer"]),
    "W4": (CAUGHT, "a bump is not remembered (`WorldMemory.learn_bump`)",
           [("world/memory.py", "        memory.bumped[key] = info\n", "        pass  # MUTANT W4\n")],
           ["WalkTests.test_a_hidden_wall_is_bumped_once_from_a_side_and_avoided"]),
    "W5": (CAUGHT, "novelty RESETS the intent's frame budget (design draft §10.4 forbids it)",
           [("brain/navigator.py", "            novel = novelty.update(look)\n",
             "            novel = novelty.update(look)\n            if novel:\n                start = pad.frames  # MUTANT W5\n")],
           ["IntentTests.test_the_budget_is_not_reset_by_novelty"]),
    "W6": (CAUGHT, "no ping-pong rule (one warp used again and again with nothing new)",
           [("brain/navigator.py", "                if len(frames) >= PINGPONG_USES and novelty.last <= frames[1]:\n",
             "                if False:  # MUTANT W6\n")],
           ["IntentTests.test_a_stairs_ping_pong_is_stuck_at_the_third_use"]),
    "W7": (CAUGHT, "no novelty window (nothing new for ever is not stuck)",
           [("brain/navigator.py", "            if look.frame - novelty.last >= intent.novelty_window:\n",
             "            if False:  # MUTANT W7\n")],
           ["IntentTests.test_nothing_new_is_stuck_within_the_window"]),
    "W8": (CAUGHT, "a map change is a connection whatever the looks between showed (no fade -> warp rule)",
           [("world/memory.py", "        if last.between:\n", "        if False:  # MUTANT W8\n")],
           ["ExitTests.test_stairs_mat_and_the_warp_graph"]),
    "W9": (CAUGHT, "watching a warp does not stop when the map has changed (`settle` waits for the player to be free, "
                   "through a scene that starts on arrival: the case that made the ping-pong invisible)",
           [("brain/navigator.py", "                    or self.world.current != key):\n", "                    ):  # MUTANT W9\n")],
           ["IntentTests.test_a_stairs_ping_pong_is_stuck_at_the_third_use"]),
    "W10": (CAUGHT, "flee presses A without reading the cursor on RUN",
            [("skills/flee.py", "        if ui.cursor == index:\n", "        if True:  # MUTANT W10\n")],
            ["FleeTests.test_run_is_reached_by_reading_the_cursor"]),
    "W11": (CAUGHT, "flee does not recognise a trainer battle (it tries to RUN from it)",
            [("skills/flee.py", "            if battle is not None and battle.kind == \"trainer\":\n",
              "            if False:  # MUTANT W11\n")],
            ["FleeTests.test_a_trainer_battle_is_out_of_scope_and_nothing_is_pressed"]),
    "W12": (CAUGHT, "a chosen target already found unreachable is tried again (each try begins with a 'deciding where to "
                    "go' pause, so frames pass and the run is not a hang: it walks nowhere until its budget, and never says "
                    "it is stuck)",
            [_EXCLUDED], ["IntentTests.test_an_unreachable_errand_is_stuck_not_a_loop"]),
    "W13": (REDUNDANT, "the guard against decisions that let no frame pass, alone",
            [_STILL],
            "every decision path in `Navigator.run` today lets a frame pass or ends the intent (a new target is followed by "
            "a thinking pause; an unreachable one is excluded and then refused by W12's check). The guard is a backstop "
            "for a future path that does neither; nothing reaches it now."),
    "W14": (CAUGHT, "Story's taste for roads gone (`WEIGHTS['Story'].road` 4.0 -> 0.5)",
            [("brain/explore.py", "    \"Story\": Weights(frontier=1.0, road=4.0,", "    \"Story\": Weights(frontier=1.0, road=0.5,")],
            ["ExploreTests.test_personalities"]),
    "W15": (CAUGHT, "Trainer's pull toward people gone (`WEIGHTS['Trainer'].people` 1.5 -> 0)",
            [("brain/explore.py", "grass=2.5, people=1.5,", "grass=2.5, people=0.0,")],
            ["ExploreTests.test_trainer_goes_toward_people"]),
    "W16": (CAUGHT, "roaming may step straight back to the tile it came from",
            [("skills/roam_train.py", "        forward = [o for o in options if o[2] != previous]\n",
              "        forward = options  # MUTANT W16\n")],
            ["RoamTests.test_roaming_covers_and_never_spins"]),
    "W17": (CAUGHT, "the way just come in is worth its 'something left there' bonus while this map has something to see "
                    "(the lab -> town -> lab ping-pong of the seed sweep's Catcher seed 1)",
            [("brain/explore.py", "        if target == came_from and here_left:\n", "        if False:  # MUTANT W17\n")],
            ["ExploreTests.test_not_straight_back_where_it_came_from"]),
    "W18": (CAUGHT, "a target excluded on one map is excluded on every map (the key without the map)",
            [("brain/navigator.py", "        self.excluded[f\"{self.world.current}|{target.key}\"] = why\n",
              "        self.excluded[target.key] = why  # MUTANT W18\n"),
             ("brain/navigator.py", "        return f\"{self.world.current}|{target.key}\" in self.excluded\n",
              "        return target.key in self.excluded  # MUTANT W18\n")],
            ["ExploreTests.test_an_exclusion_belongs_to_one_map"]),
    "W19": (CAUGHT, "roaming does not wait for a person in its only way on (it turns straight back: a spin)",
            [("skills/roam_train.py", "        if not forward and blocked and waited < PERSON_WAIT:\n",
              "        if False:  # MUTANT W19\n")],
            ["RoamTests.test_a_person_in_the_way_is_waited_for"]),
    # ---- the step-3 verifier's weak proofs (2026-10-08)
    "W20": (CAUGHT, "experience gained is not novelty (design draft §10.4 lists XP; the verifier found it uncounted)",
            [("brain/navigator.py", "            if gained:\n                new.append(f\"experience gained ({len(gained)} Pokemon)\")\n",
              "            if False:  # MUTANT W20\n                new.append(f\"experience gained ({len(gained)} Pokemon)\")\n")],
            ["NoveltyTests.test_experience_gained_is_progress"]),
    "W21": (CAUGHT, "a training step a battle began on is not counted as pressed (the verifier's 150 'tried' for 163 "
                    "roam presses)",
            [("skills/roam_train.py", "            report.interrupted += 1\n",
              "            report.interrupted += 1\n            report.attempts -= 1  # MUTANT W21\n")],
            ["RoamTests.test_steps_that_ran_into_a_battle_are_counted"]),
    "W22": (CAUGHT, "a training step a battle began on is never resolved (a step that DID move the player into the battle "
                    "is lost from the steps, the path and 'the tile it came from')",
            [("skills/roam_train.py", "        if pending is not None:\n", "        if False:  # MUTANT W22\n")],
            ["RoamTests.test_steps_that_ran_into_a_battle_are_counted"]),
    "W23": (CAUGHT, "no whim among equals: always the top score (the verifier: seeds 3 and 7 chose the same targets)",
            [("brain/explore.py", "        return pick(found, nav.rng)\n",
              "        return max(found, key=lambda target: (target.score, target.tile))  # MUTANT W23\n")],
            ["ExploreTests.test_seeds_choose_different_ways_on_the_same_town"]),
    # ---- the step-3 verifier's second round (2026-10-08)
    "W24": (CAUGHT, "the navigator does not TELL a novelty that is not a place (no `[AI-WORLD] novelty at f...` line: a live run "
                    "could not show which novelty moved the clock)",
            [("brain/navigator.py", "            if novelty.notable:\n", "            if False:  # MUTANT W24\n")],
            ["NoveltyTests.test_the_navigator_tells_the_experience_and_the_clock_it_moved"]),
    "W25": (CAUGHT, "the experience novelty is told without its IDENTITY (no PID, no totals: nothing to hold against the game's "
                    "own party)",
            [("brain/navigator.py", "                self.notable.append(\"experience gained (\" + \", \".join(\n"
                                    "                    f\"PID {pid:08x}: {self.experience[pid]} -> {experience[pid]}\" for pid in gained) + \")\")\n",
              "                self.notable.append(f\"experience gained ({len(gained)} Pokemon)\")  # MUTANT W25\n")],
            ["NoveltyTests.test_the_notable_novelty_names_the_pid_and_both_totals",
             "NoveltyTests.test_the_navigator_tells_the_experience_and_the_clock_it_moved"]),
    "W26": (CAUGHT, "game_answer's arrival takes no exit step after a door or stairs (STUCK's end tile would be the stairs)",
            [("gates/game_answer.py", "    dx, dy = EXIT_STEP.get(behaviour, (0, 0))\n", "    dx, dy = (0, 0)  # MUTANT W26\n")],
            ["GameAnswerTests.test_the_exit_step"]),
    "W27": (CAUGHT, "the ROAM grader calls a press pre-empted although the player TURNED (the facing not checked)",
            [("gates/live_step3.py",
              "            \"turned_before_the_battle\": any(facing_of(r) not in (None, facing_of(press)) for r in between + ([battle] if battle else []))}\n",
              "            \"turned_before_the_battle\": False}  # MUTANT W27\n")],
            ["GraderTests.test_a_preempted_press_and_three_that_were_not"]),
    "W28": (CAUGHT, "an INCONCLUSIVE game answer passes on the loaded map header alone (STUCK's weak proof)",
            [("gates/live_step3.py", "        if not arrival or kind is None or \"error\" in arrival:\n            run.check(False, ",
              "        if not arrival or kind is None or \"error\" in arrival:\n"
              "            run.check(bool(a.get(\"loaded_header_is_claimed_map\")),  # MUTANT W28\n                      ")],
            ["GraderTests.test_an_inconclusive_answer_with_nothing_else_fails"]),
    "W29": (CAUGHT, "a walking answer agrees with no trial predicting a step (a '0 steps, then a wall' line agrees with a "
                    "player who cannot move: found by the second round's graded run on STUCK's fault claim)",
            [("gates/game_answer.py", " and loaded_ok and any(t[\"predicted\"][\"steps\"] > 0 for t in trials)\n",
              " and loaded_ok  # MUTANT W29\n")],
            ["GameAnswerTests.test_a_walking_answer_needs_a_step"]),
    # ---- build step 3.1: the step-3 adversarial review's findings (2026-10-08)
    "W30": (CAUGHT, "finding 1: a map's top and left ends known from NEGATIVE coordinates again (`MapMemory.outside`: x < 0 or "
                    "y < 0), which no screen shows: Story chooses a 'road' that the same memory numbered +50 calls frontier",
            [("world/memory.py", "        return any(past_edge(self.edges, xy, side) for side in self.edges)\n",
              "        return xy[0] < 0 or xy[1] < 0 or any(past_edge(self.edges, xy, side) for side in self.edges)  # MUTANT W30\n")],
            ["ShiftTests.test_the_same_choice_with_every_coordinate_moved_by_50",
             "ShiftTests.test_a_tile_past_an_edge_never_crossed_is_not_a_road"]),
    "W31": (CAUGHT, "finding 2: a STALE frontier target is kept until it is walked onto (the walk there had shown everything "
                    "beside it)",
            [("brain/navigator.py", "                stale = stale_reason(memory, target) if memory is not None else None\n",
              "                stale = None  # MUTANT W31\n")],
            ["ReversalTests.test_reversals_are_near_zero_and_no_stale_target_is_walked_onto"]),
    "W32": (CAUGHT, "finding 2: no cost for turning back on a plan's first step (a target dropped as stale is replaced on the "
                    "move by one behind as often as ahead: back and forth)",
            [("brain/navigator.py", "        if not steps:\n            return {}\n",
              "        if True:  # MUTANT W32\n            return {}\n")],
            ["ReversalTests.test_reversals_are_near_zero_and_no_stale_target_is_walked_onto"]),
    "W33": (CAUGHT, "finding 3: a scene that keeps interrupting one target is never held against it (Littleroot's twin, again "
                    "and again until the novelty window)",
            [("brain/navigator.py", "        if len(hits) >= SCENE_REPEATS and novelty.last_progress <= hits[0]:\n",
              "        if False:  # MUTANT W33\n")],
            ["SceneTests.test_a_repeating_scene_gives_the_target_up"]),
    "W34": (CAUGHT, "finding 4: a bump walls the tile from EVERY side (the step-3 rule): a one-way tile is never crossed from "
                    "its open side",
            [("brain/navigator.py", "    tried = memory.bumps(nxt, direction)\n",
              "    tried = BUMP_GIVE_UP * max(memory.bumps(nxt, d) for d in DIRECTIONS)  # MUTANT W34\n")],
            ["WalkTests.test_a_one_way_tile_is_crossed_from_its_open_side"]),
    "W35": (CAUGHT, "finding 4: ONE bump closes the way in for good (no retry at a high cost when it is the only way)",
            [("world/memory.py", "BUMP_GIVE_UP = 2\n", "BUMP_GIVE_UP = 1  # MUTANT W35\n")],
            ["WalkTests.test_the_only_way_on_is_retried_before_it_is_given_up"]),
    "W36": (CAUGHT, "finding 5: the host's eyes read the map's WARP TABLE again (nothing on screen shows it)",
            [("host/eyes.py", "            signs = tuple(\n",
              "            warps = frozenset(w.local_coordinates for w in location.warps)  # MUTANT W36\n            signs = tuple(\n")],
            ["FrameworkFreeTests.test_the_ai_never_reads_the_warp_table"]),
    "W37": (CAUGHT, "finding 5: a door-looking tile that did not open is not remembered (every later intent tries it again)",
            [("world/memory.py", "            memory.closed[xy] = {\"frame\": frame, \"how\": how, \"story\": self.story}\n",
              "            pass  # MUTANT W37\n")],
            ["ExitTests.test_a_door_that_does_not_open_is_remembered_closed"]),
    "W38": (CAUGHT, "finding 5: an exit is not used the way it LOOKS (an arrow mat approached from any side)",
            [("brain/explore.py", "    asked = exit_press(fact.behavior) if fact is not None else None\n",
              "    asked = None  # MUTANT W38\n")],
            ["ExitTests.test_an_arrow_mat_is_used_by_its_arrow"]),
    "W39": (CAUGHT, "finding 6: the gate's crop check takes the window from the EYES' constants again (widening both passes)",
            [("gates/live_step3.py", "from ai_player.gates.window import on_screen_from as in_window  # noqa: E402\n",
              "from ai_player.world.memory import in_window  # noqa: E402  MUTANT W39\n")],
            ["WindowTests.test_a_tile_seen_from_8_columns_away_fails_the_gate_however_wide_the_eyes_are"]),
    "W40": (CAUGHT, "finding 8: an exit's stand tile taken from `distances` unchecked (an UNSEEN tile can be a target)",
            [("brain/explore.py", "        if stand not in reach or not memory.passable(stand):\n",
              "        if stand not in reach:  # MUTANT W40\n")],
            ["ApproachTests.test_every_candidate_is_a_seen_walkable_tile"]),
    "W41": (CAUGHT, "finding 9: every interrupted training press counted as pre-empted (the strict ratio would count steps that "
                    "DID move the player into a battle as not moving)",
            [("skills/roam_train.py", "    report.preempted = report.interrupted - moved_in\n",
              "    report.preempted = report.interrupted  # MUTANT W41\n")],
            ["RoamTests.test_steps_that_ran_into_a_battle_are_counted"]),
    "W43": (CAUGHT, "the way just come in stays an option while the map has somewhere new to go (found by the step-3.1 sweep: "
                    "TOWN-Catcher seed 8 went house -> town -> house once roads stopped being known from coordinates)",
            [("brain/explore.py", "    if any(t.kind in ONWARD_KINDS for t in out):\n", "    if False:  # MUTANT W43\n")],
            ["ExploreTests.test_not_straight_back_where_it_came_from"]),
    "W42": (CAUGHT, "finding 2's grader: a U-turn (three steps for one tile's worth of ground) not counted as a reversal",
            [("gates/live_step3.py", "            if abs(c[0] - start[0]) + abs(c[1] - start[1]) == 1 and len({start, a, b, c}) == 4:\n",
              "            if False:  # MUTANT W42\n")],
            ["GraderTests.test_reversals_in_the_looks_path"]),
    # ---- the step-3.1 verifier's round (2026-10-08)
    "W44": (CAUGHT, "a scene that sends the player back is counted per TARGET only, not per tile it began on (the explorer's "
                    "next target behind Littleroot's twin meets her again: measured live, seeds 1-6)",
            [("brain/navigator.py",
              "            if len(spots) >= SCENE_REPEATS and novelty.last_progress <= spots[0] and began not in walled:\n",
              "            if False:  # MUTANT W44\n")],
            ["SceneTests.test_an_explorer_sent_back_from_one_tile_stops_stepping_on_it"]),
    "W45": (CAUGHT, "'nothing new since the first scene' counts PLACES too (a tile seen while the scene pushed the player back "
                    "excused it: the measured seed 4, the twin 4 times for one target)",
            [("brain/navigator.py", "        if len(hits) >= SCENE_REPEATS and novelty.last_progress <= hits[0]:\n",
              "        if len(hits) >= SCENE_REPEATS and novelty.last <= hits[0]:  # MUTANT W45\n"),
             ("brain/navigator.py",
              "            if len(spots) >= SCENE_REPEATS and novelty.last_progress <= spots[0] and began not in walled:\n",
              "            if len(spots) >= SCENE_REPEATS and novelty.last <= spots[0] and began not in walled:  # MUTANT W45\n")],
            ["SceneTests.test_a_tile_seen_in_passing_is_not_progress"]),
    "W46": (CAUGHT, "a door found closed is never tried again when the story moves on (the verifier: closed for good)",
            [("world/memory.py", "                if then is not None and self.story is not None and self.story > then:\n",
              "                if False:  # MUTANT W46\n")],
            ["ExitTests.test_a_closed_door_is_tried_again_once_the_story_moves_on"]),
    "W47": (CAUGHT, "a door found closed is never tried again however long ago that was",
            [("world/memory.py", "                elif frame - int(info.get(\"frame\", frame)) >= CLOSED_RETRY_FRAMES:\n",
              "                elif False:  # MUTANT W47\n")],
            ["ExitTests.test_a_closed_door_is_tried_again_after_a_while"]),
    "W48": (CAUGHT, "progress during the intent does not lift the tiles a scene sent the player back from (the twin who lets a "
                    "player with a Pokemon pass is never tried again in the intent)",
            [("brain/navigator.py", "        self.scene_spots, self.scene_walls = {}, {}\n",
              "        pass  # MUTANT W48\n")],
            ["SceneTests.test_progress_lifts_the_tiles_a_scene_sent_the_player_back_from"]),
    "W49": (CAUGHT, "finding 2's live grader: a target dropped as stale on the way counted as walked onto (the grader would "
                    "fail the fixed code, or, read the other way, could not tell a drop from an arrival)",
            [("gates/live_step3.py",
              "        if any(key == extra.get(\"map\") and xy == tile and record[\"frame\"] <= frame <= after[\"frame\"] for key, xy, frame in dropped):\n",
              "        if False:  # MUTANT W49\n")],
            ["GraderTests.test_stale_arrivals_from_the_action_log_and_the_memory"]),
    "W50": (CAUGHT, "finding 1's live grader: a crossing of ANY edge of a map counts for every edge (ROUTE's loaded memory "
                    "crossed Route 101's bottom edge: a road past its top edge would then pass)",
            [("gates/live_step3.py", "        if side is not None and r[\"frame\"] < crossings.get((extra.get(\"map\"), side), 10**12):\n",
              "        if side is not None and r[\"frame\"] < min([f for (k, _), f in crossings.items() if k == extra.get(\"map\")] or [10**12]):  # MUTANT W50\n")],
            ["GraderTests.test_targets_past_an_edge_before_a_crossing_of_that_edge"]),
    "W51": (CAUGHT, "finding 1's live grader without its non-vacuity (the step-3.1 verifier: 'the check never fires': a run "
                    "with no target past an edge passed it)",
            [("gates/live_step3.py", "    run.check(bool(past) and not early,\n", "    run.check(not early,  # MUTANT W51\n")],
            ["GraderTests.test_targets_past_an_edge_before_a_crossing_of_that_edge"]),
    # ---- the step-3.1 verifier's second round (2026-10-08)
    "W52": (CAUGHT, "a scene is not known by its WORDS (counted per target and per tile only: the twin, who guards two tiles, "
                    "is met twice on EACH, 4 times in all: the verifier's finding)",
            [("brain/navigator.py", "            if words is not None:\n", "            if False:  # MUTANT W52\n")],
            ["SceneTests.test_one_scene_on_two_tiles_is_met_at_most_three_times"]),
    "W53": (CAUGHT, "new words heard are not progress (meeting May lifts nothing: the explorer never tries the twin again and "
                    "stops in May's house, 'nothing new')",
            [("brain/navigator.py", "                if stayed and novelty.heard(words, ended):\n",
              "                if False:  # MUTANT W53\n")],
            ["SceneTests.test_news_lifts_the_twin_and_once_more_gives_her_up_again"]),
    "W54": (CAUGHT, "after the news, the same scene must send the player back TWICE more before its tiles are given up again "
                    "(once is enough for a person who has already met her twice)",
            [("brain/navigator.py",
              "                again = said[\"lifted\"] is not None and novelty.last_progress <= said[\"lifted\"]\n",
              "                again = False  # MUTANT W54\n")],
            ["SceneTests.test_news_lifts_the_twin_and_once_more_gives_her_up_again"]),
    "W55": (CAUGHT, "new words are progress even from a scene that SENT the player back (a second girl's words at the next "
                    "tile would make the first one worth a try again)",
            [("brain/navigator.py", "                stayed = at is not None and after == at\n",
              "                stayed = True  # MUTANT W55\n")],
            ["SceneTests.test_different_words_are_different_scenes"]),
    "W56": (CAUGHT, "the verifier's own plant: the host's eyes read the warp table through getattr (the attribute-only check "
                    "passed it)",
            [("host/eyes.py", "            signs = tuple(\n",
              "            _w = frozenset(w.local_coordinates for w in getattr(location, 'warps'))  # MUTANT W56\n"
              "            signs = tuple(\n")],
            ["FrameworkFreeTests.test_the_ai_never_reads_the_warp_table"]),
    "W57": (CAUGHT, "the static warp-table check looks at attributes only again (the string-constant rule out)",
            [("gates/warp_reads.py",
              "        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in WARP_NAMES:\n",
              "        elif False:  # MUTANT W57\n")],
            ["FrameworkFreeTests.test_fault_the_verifiers_getattr_plant_is_caught"]),
    "W58": (CAUGHT, "game_answer does not ask whether the player is LOCKED when a trial the game did not step (SCENEX's end, "
                    "Birch's rescue scene, would read 'disagrees')",
            [("gates/game_answer.py", "    return any(t[\"predicted\"][\"steps\"] > 0 and t[\"game_steps\"] == 0",
              "    return False and any(t[\"predicted\"][\"steps\"] > 0 and t[\"game_steps\"] == 0  # MUTANT W58\n                    ")],
            ["GameAnswerTests.test_a_trial_the_game_did_not_step_asks_whether_the_player_is_locked"]),
    "W59": (CAUGHT, "the live grader answers a LOCKED player only when no trial ran (SCENEX's end on Route 101 then fails "
                    "the arrival it is about)",
            [("gates/live_step3.py", "    if a.get(\"inconclusive\") or (not a.get(\"agree\") and lock.get(\"locked\")):\n",
              "    if a.get(\"inconclusive\"):  # MUTANT W59\n")],
            ["GraderTests.test_a_locked_arrival_across_a_connection"]),
    "W60": (CAUGHT, "a pre-registered number that does not hold passes (the verifier: ROUTER's '4 walked onto' measured 5, "
                    "unsaid)",
            [("gates/live_step3.py", "        run.predictions.append((name, value, measured, measured == value))\n",
              "        run.predictions.append((name, value, measured, True))  # MUTANT W60\n")],
            ["GraderTests.test_a_pre_registered_number_that_does_not_hold_fails_the_arm"]),
    "W61": (CAUGHT, "arm CLOCKS lets a clock-sensitive launcher arm pre-register frames (a prediction that misses by the hour: "
                    "SCENEX9's at the graded run)",
            [("gates/live_step3.py", "    run.check(not mismatch and not unregistered and not registered_sensitive,\n",
              "    run.check(not mismatch and not unregistered,  # MUTANT W61\n")],
            ["GraderTests.test_the_clock_arm_registers_frames_only_where_every_clock_agrees"]),
}

DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_world
suite = unittest.defaultTestLoader.loadTestsFromModule(test_world)
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("test_world.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_world.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_step3_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_step3_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_step3_tests.py")], cwd=str(root), env=env, capture_output=True,
                              timeout=TIMEOUT)
    except subprocess.TimeoutExpired as error:
        return None, f"TIMEOUT after {TIMEOUT}s: {error}"
    raw = done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")
    for line in raw.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):]), raw
    return None, raw


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    out = ["AI PLAYER BUILD STEP 3 - MUTANT PROOF OF THE WORLD MODEL AND THE NAVIGATOR (gates/revert_step3.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
           f"code: {provenance(REPO)}",
           "Each mutant breaks ONE rule of the real code in a copy; CAUGHT = its predicted tests of gates/test_world.py fail; "
           "REDUNDANT = no test fails, and the reason the rule is redundant alone is stated.", ""]
    ok_all = True
    counts = {CAUGHT: 0, REDUNDANT: 0}
    # (the step-3.1 verifier's round) `--workers N`: the copies run N at a time (each its own folder and process); the
    # verdicts are written in the table's order
    argv = list(sys.argv[1:])
    workers = 1
    if "--workers" in argv:
        at = argv.index("--workers")
        workers = max(1, int(argv[at + 1]))
        del argv[at:at + 2]
    only = set(argv[0].split(",")) if argv else None
    chosen = [(name, spec) for name, spec in MUTANTS.items() if only is None or name in only]

    def attempt(item):
        root = make_copy(item[1][2])
        try:
            return run(root) + (root,)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        outcomes = list(pool.map(attempt, chosen))
    for (name, (prediction, what, edits, expected)), (result, raw, root) in zip(chosen, outcomes):
        if result is None:
            ok = False
            line = f"[{name}] NO RESULT: {raw[-1500:]}"
        else:
            bad = result["bad"]
            ran_copy = root.name in result["module"]
            failing = {t: bad[t] for t in sorted(bad)}
            if prediction == CONTROL:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] CONTROL, the unchanged copy: {result['ran']} tests, failing {sorted(bad) or 'none'} "
                        f"(ran the copy: {ran_copy}) -> {'PASS' if ok else 'FAIL'}")
            elif prediction == CAUGHT:
                # a test with sub-tests fails under its name + " (<the sub-test's parameters>)"
                caught = [t for t in expected if any(b == t or b.startswith(t + " (") for b in bad)]
                ok = ran_copy and caught == expected
                line = (f"[{name}] BROKEN: {what}. Predicted CAUGHT by {expected}. The copy ran {result['ran']} tests "
                        f"({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {failing} -> {'CAUGHT' if ok else 'NOT CAUGHT'}")
            else:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] BROKEN: {what}. Predicted REDUNDANT ALONE (no test fails), because {expected} The copy ran "
                        f"{result['ran']} tests ({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {failing or 'none'} -> "
                        f"{'NOT CAUGHT, as predicted (redundant alone)' if ok else 'PREDICTION WRONG'}")
            if ok and prediction in counts:
                counts[prediction] += 1
        ok_all &= ok
        print(line, flush=True)
        out.append(line)
    verdict = "PASS" if ok_all else "FAIL"
    summary = (f"{counts[CAUGHT]} mutants CAUGHT as predicted, {counts[REDUNDANT]} REDUNDANT ALONE as predicted (each with its reason), "
               f"of {len(MUTANTS) - 1}")
    out += ["", summary, f"OVERALL: {verdict}"]
    print(summary)
    print(f"OVERALL: {verdict}")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step3-REVERT.txt"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
