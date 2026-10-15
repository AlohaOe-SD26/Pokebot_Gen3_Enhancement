"""MUTANT PROOF of AI-player build step 5 (the story player): each rule of the REAL code, broken in a COPY of the package,
fails its predicted test of `gates/test_goals.py`, or is documented as REDUNDANT ALONE with the reason.

    py -3.12 ai_player/gates/revert_step5.py [G1,G2] [--workers N]       (exit 0 = every prediction held)

The mechanism is `gates/revert_step4.py`'s (CLAUDE.md session discipline rule 6: a fault switch shows a test CAN fail, a
mutant shows the RULE in the real code carries weight): copy the package (no states, no evidence), apply ONE mutant's edits
(each anchor must occur exactly once), run `gates/test_goals.py` from the copy, and check the prediction. The unchanged copy
(G0) must pass every test. Evidence: `ai_player/evidence/<date>-step5-REVERT.txt`.
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
from ai_player.gates.provenance import keep_earlier, provenance  # noqa: E402

EVIDENCE = REPO / "ai_player" / "evidence"
TIMEOUT = 600
CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"
GOALS, STORY, PERSON, SKILL, EXPLORE, VIEW, WORLD = ("brain/goals.py", "knowledge/story.py", "personality.py",
                                                     "skills/story.py", "brain/explore.py", "eyes/view.py",
                                                     "world/memory.py")
NAV, MODE, DATA, ROAM = "brain/navigator.py", "mode.py", "knowledge/milestones.json", "skills/roam_train.py"
#: (build step 5.1)
DIALOGUE, WAITING, BATTLE, RATE5 = "hands/dialogue.py", "hands/waiting.py", "brain/battle.py", "gates/rate_step5.py"

#: name -> (prediction, the rule that is broken, [edits], tests that MUST fail (CAUGHT) or the reason (REDUNDANT)).
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str] | str]] = {
    "G0": (CONTROL, "nothing: the unchanged copy", [], []),
    "G1": (CAUGHT, "a milestone's VARS are not checked (only its flags)",
           [(STORY, "                and all(marks[name] >= value for name, value in self.variables))",
             "                and True)  # MUTANT G1")],
           ["MilestoneTests.test_vars_count_at_least", "MilestoneTests.test_chapter_1_in_order_from_the_marks"]),
    "G2": (CAUGHT, "a proof NOT READ counts as done",
           [(STORY, "        if any(name not in marks for name in needed):\n            return None\n",
             "        if any(name not in marks for name in needed):\n            return True  # MUTANT G2\n")],
           ["MilestoneTests.test_a_proof_not_read_is_never_progress"]),
    "G3": (CAUGHT, "a WAYPOINT never passes on its map",
           [(GOALS, "            if milestone.waypoint is not None and visited(milestone.waypoint):\n",
             "            if False:  # MUTANT G3\n")],
           ["MilestoneTests.test_the_intro_is_passed_by_its_waypoint_the_truck",
            "MilestoneTests.test_the_route102_waypoint_passes_on_its_map"]),
    "G4": (CAUGHT, "the player's gender ignored (every player a BOY)",
           [(STORY, '        self.gender = gender if gender in ("BOY", "GIRL") else "BOY"\n',
             '        self.gender = "BOY"  # MUTANT G4\n')],
           ["MilestoneTests.test_the_players_gender_swaps_the_houses"]),
    "G5": (CAUGHT, "a hint used without its words being READ",
           [(GOALS, "    return any(_names(page, words) is not None for page in heard)\n",
             "    return True  # MUTANT G5\n")],
           ["HintTests.test_heard_words_is_case_and_space_blind_and_needs_the_words",
            "HintTests.test_before_the_words_it_goes_to_ask_at_the_rivals_house"]),
    "G6": (CAUGHT, "the no-hints FAULT ignored",
           [(GOALS, "        if self.hints_off:\n            return False\n", "        if False:  # MUTANT G6\n            return False\n")],
           ["HintTests.test_hints_off_never_uses_the_words"]),
    "G7": (CAUGHT, "the training target is the fight's level itself (no personality margin)",
           [(GOALS, "        return max(levels) + self.state.errands.train_margin\n",
             "        return max(levels)  # MUTANT G7\n")],
           ["ErrandTests.test_training_targets_by_personality_before_the_rival"]),
    "G8": (CAUGHT, "no minimum of training steps before a fight",
           [(GOALS, '            short = level < target or prep["steps"] < errands.train_min_steps\n',
             "            short = level < target  # MUTANT G8\n")],
           ["ErrandTests.test_it_trains_its_minimum_steps_even_above_the_target"]),
    "G9": (CAUGHT, "the no-training FAULT ignored",
           [(GOALS, "        if fight_next and not self.train_off and not hurt:\n",
             "        if fight_next and not hurt:  # MUTANT G9\n")],
           ["ErrandTests.test_train_off_never_trains"]),
    "G10": (CAUGHT, "a POKéMON CENTER it knows is not where it heals (home first)",
            [(GOALS, '        nearest = self._nearest_place(world, CENTER_SUFFIX, "pokemon_center", "POKéMON CENTER")\n',
              "        nearest = None  # MUTANT G10\n")],
            ["ErrandTests.test_hurt_heals_at_a_known_centre_else_at_home_else_not"]),
    "G11": (CAUGHT, "one heal threshold for every personality (half its HP)",
            [(GOALS, "        hurt = has_party and share is not None and (must_rest or share < errands.heal_below)\n",
              "        hurt = has_party and share is not None and (must_rest or share < 0.5)  # MUTANT G11\n")],
            ["ErrandTests.test_heal_thresholds_by_personality"]),
    # (build step 5.1: step 5's G12, "shopped before FLAG_ADVENTURE_STARTED", broke a rule that is gone: the AI no longer
    # reads that flag; it shops by the mart's LIST, and G12 now breaks THAT rule)
    "G12": (CAUGHT, "a mart whose LIST had no POKé BALLS is shopped at again before the story moved on",
            [(GOALS, "            return self.memory.no_balls.get(const, -1) < index\n", "            return True  # MUTANT G12\n")],
            ["PersonFairTests.test_the_mart_is_shopped_by_its_list"]),
    "G13": (CAUGHT, "an item ball seen is not picked up before the story goes on",
            [(GOALS, "        if ball is not None:\n", "        if False:  # MUTANT G13\n")],
            ["ErrandTests.test_an_item_ball_comes_before_the_story"]),
    "G14": (CAUGHT, "one chat rate for every personality",
            [(GOALS, "            if draw < self.state.errands.chat:\n", "            if draw < 0.2:  # MUTANT G14\n")],
            ["ErrandTests.test_chatting_rates_by_personality"]),
    "G15": (CAUGHT, "a drift never comes back to the base",
            [(PERSON, "        if self.drift_until is not None and steps >= self.drift_until:\n",
              "        if False:  # MUTANT G15\n")],
            ["DriftTests.test_drifts_are_bounded_and_always_come_back"]),
    "G16": (CAUGHT, "the drift chance ignored (every draw drifts)",
            [(PERSON, "        if roll >= DRIFT_CHANCE:\n", "        if False:  # MUTANT G16\n")],
            ["DriftTests.test_the_drift_rate_follows_its_chance"]),
    "G17": (CAUGHT, "drift switched on when told off",
            [(PERSON, "        if not self.drift_on or self.drift_until is not None:\n",
              "        if self.drift_until is not None:  # MUTANT G17\n")],
            ["DriftTests.test_no_drift_when_off"]),
    "G18": (CAUGHT, "the favourite drawn from every species, not the wild ones",
            [(PERSON, "    return choices.choice(wild_species())\n",
              "    return choices.choice(wild_species() + ('Treecko', 'Mew', 'Deoxys') * 40)  # MUTANT G18\n")],
            ["ChoiceTests.test_the_favourite_is_a_wild_species_and_varies"]),
    "G19": (CAUGHT, "a nickname answered YES",
            [(SKILL, '    ("nickname", False, "a nickname: this player keeps the name a Pokemon has"),\n',
              '    ("nickname", True, "MUTANT G19"),\n')],
            ["ChoiceTests.test_questions_by_their_words"]),
    "G20": (CAUGHT, "a story question NOT recognised answered NO (the explorer's rule)",
            [(SKILL, '    return True, f"a question in the story ({words[:60]!r}): YES, a person goes along with what the game asks"\n',
              '    return False, "MUTANT G20"\n'),
             (SKILL, '    ("good idea to go see", True, "PROF. BIRCH\'s suggestion to go see the rival: a person goes along with it"),\n',
              "")],
            ["ChoiceTests.test_questions_by_their_words"]),
    "G21": (CAUGHT, "a scene's map change from where the player stood taken as a way to walk (the first chapter-1 run's fix "
                    "reverted)",
            [(EXPLORE, '            if kind == "warp" and not looks_like_exit(world, key, link.get("tile")):\n',
              '            if False:  # MUTANT G21\n')],
            ["WayTests.test_a_scenes_map_change_is_no_way_to_walk",
             "WayTests.test_a_door_a_scene_walked_the_player_through_is_a_way"]),
    "G26": (CAUGHT, "only a SCENE's map change refused: a 'warp' remembered from a tile that is no door taken as a way (the "
                    "chapter-1 sweep's seed 7 reverted), and a door a scene walked the player through refused",
            [(EXPLORE, '            if kind == "warp" and not looks_like_exit(world, key, link.get("tile")):\n',
              '            if kind == "warp" and link.get("by") == "scene":  # MUTANT G26\n')],
            ["WayTests.test_a_scenes_map_change_is_no_way_to_walk",
             "WayTests.test_a_door_a_scene_walked_the_player_through_is_a_way"]),
    "G27": (CAUGHT, "someone seen earlier on this map is not looked for where they stood",
            [(GOALS, '            if seen is not None and self._allowed(f"seek:{step.look}"):\n',
              "            if False:  # MUTANT G27\n")],
            ["HintTests.test_the_rival_seen_earlier_on_this_map_is_sought_where_she_stood"]),
    "G28": (CAUGHT, "the doors it recognised are not kept with the world memory",
            [(WORLD, "        if self.landmarks:  # (build step 5) only when the play brain recognised a door: earlier snapshots unchanged\n",
              "        if False:  # MUTANT G28\n")],
            ["WayTests.test_the_doors_it_recognised_are_kept_with_the_world_memory"]),
    "G29": (CAUGHT, "a building never seen is not looked for in its own town",
            [(GOALS, "        return town if town is not None and not there else None\n", "        return None  # MUTANT G29\n")],
            ["WayTests.test_a_building_never_seen_is_looked_for_in_its_own_town"]),
    "G22": (CAUGHT, "a room upstairs looked for out in the open",
            [(GOALS, "    if goal_const is not None and not OUTDOOR.match(goal_const):\n", "    if False:  # MUTANT G22\n")],
            ["WayTests.test_a_map_never_seen_is_looked_for_out_in_the_open"]),
    "G23": (CAUGHT, "a house already seen walked back into on the way",
            [(GOALS, '    return inside is None or bool(OUTDOOR.match(inside.const or "")) or inside.const == goal_map\n',
              "    return True  # MUTANT G23\n")],
            ["WayTests.test_a_house_already_seen_is_not_walked_back_into_on_the_way"]),
    "G24": (CAUGHT, "the milestone marks read one bit off",
            [(VIEW, "        out.append((name, (flag_bytes[number // 8] >> (number % 8)) & 1 if number // 8 < len(flag_bytes) else 0))\n",
              "        out.append((name, (flag_bytes[number // 8] >> ((number + 1) % 8)) & 1 if number // 8 < len(flag_bytes) else 0))  # G24\n")],
            ["TableTests.test_marks_decode_bits_and_u16s"]),
    "G25": (CAUGHT, "the starter the run names ignored (a draw instead)",
            [(PERSON, '        return named.upper(), "named by the run"\n', '        pass  # MUTANT G25\n')],
            ["ChoiceTests.test_the_starter_named_or_drawn"]),
    # ---- the step-5 verifier's round (2026-10-14): each rule it found unproven or dead, now with its own test
    # (build step 5.1: the hint rule is now per STEP, `step_known`; G30 and G31 break it there)
    "G30": (CAUGHT, "a step's map taken as known while hints are on, without its words (the verifier's V2)",
            [(GOALS, "        if step.told:\n            return heard_words(heard, step.told)\n",
              "        return True  # MUTANT G30\n")],
            ["HintTests.test_a_go_whose_words_are_unheard_explores_with_no_map",
             "HintTests.test_a_wordless_hint_heads_only_for_a_place_it_has_been"]),
    "G31": (CAUGHT, "a step with no words heads for a place the AI has never been",
            [(GOALS, "        return self.been_to(world, step.map)\n", "        return True  # MUTANT G31\n")],
            ["HintTests.test_a_wordless_hint_heads_only_for_a_place_it_has_been"]),
    "G32": (CAUGHT, "the data names a map the game never says (ROUTE 102 for MOM's 'PETALBURG GYM', the verifier's case)",
            [(DATA, '   "waypoint": "ROUTE102",\n   "optional": false,\n   "maps": [\n    "OLDALE_TOWN",\n    "ROUTE102"\n   ],\n'
                    '   "steps": [\n    {\n     "do": "go",\n     "map": "PETALBURG_CITY",\n     "told": "PETALBURG"\n    }\n   ],\n'
                    '   "hint": {\n    "said": "MOM, on the TV: Look! It\'s PETALBURG GYM! Maybe DAD will be on!",\n'
                    '    "words": "PETALBURG",\n    "map": "PETALBURG_CITY",\n',
              '   "waypoint": "ROUTE102",\n   "optional": false,\n   "maps": [\n    "OLDALE_TOWN",\n    "ROUTE102"\n   ],\n'
              '   "steps": [\n    {\n     "do": "go",\n     "map": "ROUTE102",\n     "told": "PETALBURG"\n    }\n   ],\n'
              '   "hint": {\n    "said": "MOM, on the TV: Look! It\'s PETALBURG GYM! Maybe DAD will be on!",\n'
              '    "words": "PETALBURG",\n    "map": "ROUTE102",\n')],
            ["HintTests.test_every_hint_map_is_named_by_what_the_game_says"]),
    "G33": (CAUGHT, "no bound on the training sessions before a fight (the verifier's V4)",
            [(GOALS, '            if short and prep["sessions"] < TRAIN_SESSIONS and self._allowed("train"):\n',
              '            if short and self._allowed("train"):  # MUTANT G33\n')],
            ["ErrandTests.test_training_is_bounded_by_its_sessions"]),
    "G34": (CAUGHT, "the no-training FAULT also removes the heal before the fight (the NOTRAIN arm's confound)",
            [(GOALS, '            ready = self.train_off or bool(self.prep(milestone).get("ready"))\n',
              '            ready = bool(self.prep(milestone).get("ready"))  # MUTANT G34\n')],
            ["ErrandTests.test_the_no_training_fault_still_heals_before_the_fight"]),
    "G35": (CAUGHT, "the training rest ignores the personality's heal_below (needs_rest alone)",
            [(GOALS, "    if share is not None and share < heal_below:\n", "    if False:  # MUTANT G35\n")],
            ["RestTests.test_the_training_rest_stops_under_each_personalitys_heal_below",
             "RestTests.test_a_training_roam_installs_the_rest_and_clears_it"]),
    "G36": (CAUGHT, "the navigator asks the rest only with a battle limit set (the verifier's DEAD FIX, V3)",
            [(NAV, "                rest = self.battle_rest(self.hands.look()) if self.battle_rest is not None else None\n",
              "                rest = self.battle_rest(self.hands.look()) if self.battle_limit is not None and self.battle_rest "
              "else None  # MUTANT G36\n")],
            ["RestTests.test_the_navigator_asks_the_rest_with_no_battle_limit"]),
    "G37": (CAUGHT, "the battle's kind read on its first frame, before the battle view exists (prep['wild'] always 0)",
            [(NAV, '                kind = kinds[0] if kinds else "?"\n',
              '                kind = look.battle.kind if look.battle is not None else "?"  # MUTANT G37\n')],
            ["RestTests.test_the_battles_kind_is_the_one_shown_during_the_battle"]),
    "G38": (CAUGHT, "a battle lost inside a goal not counted (the verifier's 'battles lost 0' after two whiteouts)",
            [(GOALS, '    return sum(1 for _, _, outcome in battle_log if outcome == "lost")\n',
              "    return 0  # MUTANT G38\n")],
            ["LossTests.test_losses_inside_goals_count_and_end_the_run"]),
    "G39": (CAUGHT, "MAX_LOSSES never ends the run",
            [(MODE, '        if report["losses"] >= MAX_LOSSES:\n', "        if False:  # MUTANT G39\n")],
            ["LossTests.test_losses_inside_goals_count_and_end_the_run"]),
    "G40": (CAUGHT, "the training roam installs no rest rule",
            [(GOALS, "        nav.battle_rest = lambda look: training_rest(look, heal_below, active)\n",
              "        nav.battle_rest = lambda look: None  # MUTANT G40\n")],
            ["RestTests.test_a_training_roam_installs_the_rest_and_clears_it"]),
    "G41": (CAUGHT, "the walk to heal goes through the grass at the personality's own cost",
            [(GOALS, "        own = nav.grass_cost\n        nav.grass_cost = max(own, HURT_GRASS_COST)\n",
              "        own = nav.grass_cost\n        nav.grass_cost = own  # MUTANT G41\n")],
            ["RestTests.test_the_walk_to_heal_keeps_out_of_the_grass_and_restores_the_taste"]),
    "G42": (CAUGHT, "every SCENE link refused, a door MOM walked the player through included (no way home: step5dev7 seed 3)",
            [(EXPLORE, '            if kind == "warp" and not looks_like_exit(world, key, link.get("tile")):\n',
              '            if kind == "warp" and (link.get("by") == "scene" or not looks_like_exit(world, key, '
              'link.get("tile"))):  # MUTANT G42\n')],
            ["WayTests.test_a_door_a_scene_walked_the_player_through_is_a_way"]),
    "G43": (CAUGHT, "a heal put aside after failing stays aside though the party is in danger",
            [(GOALS, "                if where is not None and (allowed or (must_rest and retries < DANGER_RETRIES)):\n",
              "                if where is not None and allowed:  # MUTANT G43\n")],
            ["ErrandTests.test_a_party_in_danger_heals_again_and_nobody_trains_hurt"]),
    "G45": (CAUGHT, "a walk to an item ball that a battle ate is given up at once (the graded CH2 arm's lost POTION)",
            [(GOALS, '                len(nav.battle_log) > battles and not outcome.startswith("picked up"))\n',
              "                False)  # MUTANT G45\n")],
            ["RestTests.test_an_item_walk_a_battle_ate_is_tried_again"]),
    "G44": (CAUGHT, "it trains while hurt",
            [(GOALS, "        if fight_next and not self.train_off and not hurt:\n",
              "        if fight_next and not self.train_off:  # MUTANT G44\n")],
            ["ErrandTests.test_a_party_in_danger_heals_again_and_nobody_trains_hurt"]),
    # ---- the step-5 verifier's round 2 (2026-10-14): its two mutants that no test caught, and the four weak rules it named
    "G46": (CAUGHT, "the play loop no longer counts the battles lost (the verifier's V6: the loop's _count_losses call None)",
            [(MODE, "            stop = self._count_losses(hands, nav, report)\n", "            stop = None  # MUTANT G46\n")],
            ["PlayLoopTests.test_battles_lost_inside_goals_end_the_play_loop"]),
    "G47": (CAUGHT, "STORY_PATIENCE checked only when the player is free (the verifier's V4: the old rule)",
            [(MODE, "            if hands.pad.frames - changed_at > STORY_PATIENCE:\n",
              "            if nav_free(look) and hands.pad.frames - changed_at > STORY_PATIENCE:  # MUTANT G47\n")],
            ["PlayLoopTests.test_patience_ends_a_screen_that_never_frees"]),
    "G48": (CAUGHT, "a hint's words matched as a SUBSTRING ('LAB' in 'available', 'BAG' in 'baggage', 'clock' in "
                    "\"o'clock\")",
            [(GOALS, '    return re.search(rf"(?<![{_WORD_CHARS}]){want}(?![{_WORD_CHARS}])", " ".join(page.split()).lower())\n',
              '    return re.search(want, " ".join(page.split()).lower())  # MUTANT G48\n')],
            ["HintTests.test_heard_words_match_whole_words"]),
    "G49": (CAUGHT, "the goal's reason quotes the STORED words, not the page the AI read",
            [(GOALS, 'f"the game said: {quote(page, step.told)!r}" if page',
              'f"the game said: {step.told!r} (MUTANT G49)" if page')],
            ["HintTests.test_the_reason_quotes_the_page_it_read"]),
    "G50": (CAUGHT, "a roam with a battler counts every battle that ended with no stop as FLED (the verifier's '4 fled' "
                    "for 5 won)",
            [(ROAM, '        self.fled += outcome == "ran"\n', "        self.fled += stop is None  # MUTANT G50\n")],
            ["RestTests.test_a_roam_with_a_battler_counts_how_its_battles_ended"]),
    "G51": (CAUGHT, "the page quoted is the first in order, not the one read most recently",
            [(GOALS, "    return min(found, key=lambda page: (-recent.get(page, -1), page))\n",
              "    return min(found)  # MUTANT G51\n")],
            ["HintTests.test_the_reason_quotes_the_page_it_read"]),
    "G52": (CAUGHT, "the goal manager keeps no record of the pages it read",
            [(GOALS, "                self.memory.pages[page] = look.frame\n", "                pass  # MUTANT G52\n")],
            ["HintTests.test_notice_keeps_the_pages_read_on_the_overworld"]),
    # ---- BUILD STEP 5.1 (the step-5 verifier's FAILURE, the adversarial review's findings, the small items): every fix
    # reverted in a copy, each predicted CAUGHT by its own test
    "G53": (CAUGHT, "the starter bag watched for the bag ALONE (the stall: the yes/no after the A waited 600 frames)",
            [(SKILL, "    look = yield from bag_or_its_question(hands, why)\n",
              "    from ai_player.hands.menus import wait_for_ui\n"
              "    look = yield from wait_for_ui(hands, \"choose_starter\", why)  # MUTANT G53\n")],
            ["PacingTests.test_the_bag_hands_its_question_back_at_once"]),
    "G54": (CAUGHT, "`talk` waits out a screen that waits for a press even when told to give way",
            [(DIALOGUE, "            waiting = awaits_press(look) if give_way else None\n",
              "            waiting = None  # MUTANT G54\n")],
            ["PacingTests.test_talk_gives_a_scene_its_screen_back",
             "PacingTests.test_a_scene_that_begins_while_it_turns_to_talk_is_played"]),
    "G55": (CAUGHT, "`talk_to` does not ask `talk` to give way (the step-5 call: the 1,200-frame stall in the lab)",
            [(SKILL, "    if not (yield from talk(hands, seen, why, give_way=True)):\n",
              "    if not (yield from talk(hands, seen, why)):  # MUTANT G55\n")],
            ["PacingTests.test_a_scene_that_begins_while_it_turns_to_talk_is_played"]),
    "G56": (CAUGHT, "a goal chosen on the frame a map change lands (no settling)",
            [(MODE, "            if arrived is not None and 0 <= look.frame - arrived < SETTLE_FREE:\n",
              "            if False:  # MUTANT G56\n")],
            ["PlayLoopTests.test_the_screen_settles_after_a_map_change_before_a_goal"]),
    "G57": (CAUGHT, "a goal pursued though a scene began while it decided",
            [(MODE, "            seen = hands.look()\n            if not nav_free(seen):\n",
              "            seen = hands.look()\n            if False:  # MUTANT G57\n")],
            ["PlayLoopTests.test_a_goal_waits_when_a_scene_began_while_it_decided"]),
    "G58": (CAUGHT, "the wait watch does not end a stretch at a press (two waits read as one)",
            [(WAITING, '        if stretch is not None and (waiting is None or presses != stretch["presses"]):\n',
              "        if stretch is not None and waiting is None:  # MUTANT G58\n")],
            ["PacingTests.test_the_wait_watch_measures_every_stretch_whatever_the_reason"]),
    "G59": (CAUGHT, "a menu that takes input is not a wait for a press (only a text is)",
            [(DIALOGUE, '    if screen.ui is not None and screen.ui.accepts_input:\n        return f"the {screen.ui.kind} takes input"\n',
              "")],
            ["PacingTests.test_the_wait_watch_measures_every_stretch_whatever_the_reason"]),
    "G60": (CAUGHT, "no look-around on a new place (the step-5 beeline)",
            [(GOALS, "            if draw < errands.look_around or self.memory.passed_new >= LOOK_DEBT or owed:\n",
              "            if False:  # MUTANT G60\n")],
            ["ExploreTests.test_looking_around_a_new_place_by_personality"]),
    "G61": (CAUGHT, "one look-around rate for every personality (the Story's not lower)",
            [(GOALS, "            if draw < errands.look_around or self.memory.passed_new >= LOOK_DEBT or owed:\n",
              "            if draw < 0.5 or self.memory.passed_new >= LOOK_DEBT or owed:  # MUTANT G61\n")],
            ["ExploreTests.test_looking_around_a_new_place_by_personality"]),
    "G62": (CAUGHT, "the beeline control's switch ignored by the look-around",
            [(GOALS, '        if (self.errands_off or here is None or not OUTDOOR.match(const or "") or world.current in '
                     'self.memory.looked\n',
              '        if (here is None or not OUTDOOR.match(const or "") or world.current in self.memory.looked  # MUTANT G62\n')],
            ["ExploreTests.test_one_draw_a_map_and_none_under_the_beeline_control"]),
    "G87": (CAUGHT, "a walk stops only on a map NEVER visited (step51dev2-4: the look-around's draw was rarely due)",
            [(GOALS, '                    if (nav.world.current not in manager.memory.looked\n',
              '                    if (nav.world.current not in manager.memory.looked\n'
              '                            and nav.world.current not in known_maps_before  # MUTANT G87\n'),
             (GOALS, '            stop_new = goal.kind in ("go", "look_around") and not manager.errands_off\n',
              '            stop_new = goal.kind in ("go", "look_around") and not manager.errands_off\n'
              '            known_maps_before = {key for key, memory in nav.world.maps.items() if memory.visits}  # MUTANT G87\n')],
            ["ExploreTests.test_a_walk_that_arrives_somewhere_new_stops_to_decide"]),
    "G63": (CAUGHT, "never a detour off the way",
            [(GOALS, "            if draw < errands.detour or owed:\n", "            if False:  # MUTANT G63\n")],
            ["ExploreTests.test_a_detour_now_and_then_while_travelling"]),
    "G64": (CAUGHT, "item balls only with a party (step 5: the rival's POKé BALL needed a scripted step)",
            [(GOALS, "        if ball is not None:\n", "        if ball is not None and has_party:  # MUTANT G64\n")],
            ["ExploreTests.test_curiosity_finds_an_item_ball_before_the_party"]),
    "G65": (CAUGHT, "an item ball seen earlier is never walked back to",
            [(GOALS, "        if remembered is not None and self._allowed(",
              "        if False and remembered is not None and self._allowed(")],
            ["ExploreTests.test_an_item_ball_seen_earlier_is_walked_back_to"]),
    "G66": (CAUGHT, "a walk that arrives somewhere new goes straight on (no new-map stop)",
            [(GOALS, '            stop_new = goal.kind in ("go", "look_around") and not manager.errands_off\n',
              "            stop_new = False  # MUTANT G66\n")],
            ["ExploreTests.test_a_walk_that_arrives_somewhere_new_stops_to_decide"]),
    "G67": (CAUGHT, "PATIENCE_OLD: real progress does not reset the patience (only a milestone does: the review's finding 2)",
            [(MODE, '                           f"(it had waited {hands.pad.frames - changed_at} frames)")\n'
                    "                changed_at = hands.pad.frames\n",
              '                           f"(it had waited {hands.pad.frames - changed_at} frames)")\n'
              "                pass  # MUTANT G67\n")],
            ["PlayLoopTests.test_progress_while_training_keeps_the_patience"]),
    "G68": (CAUGHT, "every heal resets the patience (heal, get hurt, heal again would never end)",
            [(MODE, '                if seen.get("heals_counted", 0) >= HEAL_RESETS_MAX:\n',
              "                if False:  # MUTANT G68\n")],
            ["PlayLoopTests.test_progress_counts_a_heal_at_most_a_few_times_a_milestone"]),
    "G69": (CAUGHT, "one word heard for the milestone opens every step's map (the review's 'next door' case)",
            [(GOALS, "            return heard_words(heard, step.told)\n",
              '            return heard_words(heard, step.told) or heard_words(heard, "next door")  # MUTANT G69\n')],
            ["PersonFairTests.test_each_step_needs_its_own_words"]),
    "G70": (CAUGHT, "the ask step goes to its map with no check (step 5)",
            [(GOALS, "                if self.step_known(step, world.heard, world):\n"
                     "                    return Goal(\"go\", f\"{milestone.title}: to ask at",
              "                if True:  # MUTANT G70\n"
              "                    return Goal(\"go\", f\"{milestone.title}: to ask at")],
            ["PersonFairTests.test_asking_goes_only_where_it_has_been"]),
    "G71": (CAUGHT, "the data scripts 'use the rival's POKé BALL' again (the review's finding 3)",
            [(DATA, '     "told": "is upstairs, I think",\n     "file": "data/maps/LittlerootTown_MaysHouse_1F/scripts.inc"\n    }\n   ],\n',
              '     "told": "is upstairs, I think",\n     "file": "data/maps/LittlerootTown_MaysHouse_1F/scripts.inc"\n    },\n'
              '    {\n     "do": "use",\n     "map": "<rival_house_2f>",\n     "look": "rivals_poke_ball"\n    }\n   ],\n')],
            ["ExploreTests.test_curiosity_finds_an_item_ball_before_the_party"]),
    "G72": (CAUGHT, "a fight nobody names trained for by its data levels (the review's finding 4)",
            [(GOALS, "        if milestone.fight_named:\n", "        if True:  # MUTANT G72\n")],
            ["PersonFairTests.test_only_a_named_fight_is_trained_for_before_it_is_seen"]),
    "G73": (CAUGHT, "the training target from the WEAKEST level (the verifier's min() mutant)",
            [(GOALS, "        return max(levels) + self.state.errands.train_margin\n",
              "        return min(levels) + self.state.errands.train_margin  # MUTANT G73\n")],
            ["PersonFairTests.test_only_a_named_fight_is_trained_for_before_it_is_seen",
             "PersonFairTests.test_the_training_goal_names_the_strongest_level"]),
    "G74": (CAUGHT, "an optional milestone (the gym's trainers) is the current one until its trainers are beaten",
            [(GOALS, "            if milestone.optional:\n                continue\n            if milestone.done(marks) is True:\n",
              "            if milestone.done(marks) is True:  # MUTANT G74\n")],
            ["PersonFairTests.test_roxanne_is_proven_by_the_badge_alone",
             "PersonFairTests.test_the_training_goal_names_the_strongest_level"]),
    "G76": (CAUGHT, "home is a place to heal by a flag a person cannot see (step 5: FLAG_RESCUED_BIRCH)",
            [(GOALS, "        why = self.home_heals(world)\n", '        why = "MUTANT G76: RESCUED_BIRCH"\n')],
            ["PersonFairTests.test_home_heals_once_mom_said_so_or_it_saw_her"]),
    "G77": (CAUGHT, "a heal MOM was seen to give is not learned",
            [(GOALS, "            manager.memory.home_heals += 1\n", "            pass  # MUTANT G77\n")],
            ["PersonFairTests.test_it_learns_that_mom_heals_by_seeing_it"]),
    "G78": (CAUGHT, "a story goal that keeps failing is chosen again at once (no cooldown: the review's finding 5)",
            [(GOALS, '        if goal.kind == "intro" or self._allowed(goal.key):\n', "        if True:  # MUTANT G78\n")],
            ["LoopGoalTests.test_a_failing_story_goal_yields_with_a_reason"]),
    "G79": (CAUGHT, "every milestone passed is told 'done' (a waypoint pass quoting proofs that do not hold)",
            [(MODE, '                if proven:\n                    how = "done"\n',
              '                if True:\n                    how = "done"  # MUTANT G79\n')],
            ["SmallTests.test_milestone_lines_say_how_a_milestone_passed"]),
    "G80": (CAUGHT, "the battle line says it WANTS a species with no ball in the bag",
            [(BATTLE, '        wish = ("it WANTS it" if balls else "it would like it, but it has no POKé BALL") if self.memory.want_catch \\\n',
              '        wish = "it WANTS it" if self.memory.want_catch \\\n')],
            ["SmallTests.test_a_battle_line_says_no_ball_when_there_is_none"]),
    "G82": (CAUGHT, "in danger and knowing no place to heal, it walks on (the step-5.1 sweep's three whiteouts)",
            [(GOALS, '                if where is None and must_rest and self._allowed("find_center"):\n',
              "                if False:  # MUTANT G82\n")],
            ["PersonFairTests.test_in_danger_with_nowhere_known_it_looks_for_a_center"]),
    "G83": (CAUGHT, "travelling LOW it fights unless its temperament's first-turn draw says run (step 4)",
            [(BATTLE, "        elif hp_share < self.temper.run_low and bar > 0.3:\n", "        elif False:  # MUTANT G83\n")],
            ["PersonFairTests.test_travelling_low_it_runs_whatever_its_temperament"]),
    "G84": (CAUGHT, "a hurt walk goes through the tall grass at the personality's own cost (only the walk to heal kept out)",
            [(GOALS, "        if hurt:\n            nav.grass_cost = max(own, HURT_GRASS_COST)\n",
              "        if hurt:\n            pass  # MUTANT G84\n")],
            ["PersonFairTests.test_a_hurt_walk_keeps_out_of_the_grass"]),
    "G85": (CAUGHT, "it looks round a new place while the story's own thing calls there (PROF. BIRCH: 'Don't leave me')",
            [(GOALS, "        return not self._story_here(step, world)\n", "        return True  # MUTANT G85\n")],
            ["PersonFairTests.test_no_look_around_where_the_story_calls"]),
    # (first registered REDUNDANT ALONE, "`talk` with give_way returns at once on the same screen": the mutant proof found
    # the prediction WRONG, 2026-10-14: when the scene has taken the person off the screen, `talk_to` without its first
    # check answers "the npc is not on screen any more" and never plays the scene. It is also a layer of STALL2)
    "G86": (CAUGHT, "`talk_to` does not play a scene that is ON SCREEN already before it talks (its first check)",
            [(SKILL, "    if not nav_free(look):\n        # (build step 5.1) a scene began on the last steps of the walk: it is played "
                     "first, never waited out\n",
              "    if False:  # MUTANT G86\n")],
            ["PacingTests.test_talk_to_plays_the_scene_that_began"]),
    "G88": (CAUGHT, "every walk starts with no scene walls (step51dev5's twin loop: the patience ran out in Littleroot)",
            [(GOALS, "        if walls is not None:\n            nav.carried_scene_walls = walls\n",
              "        if walls is not None:\n            pass  # MUTANT G88\n")],
            ["SceneWallTests.test_scene_walls_carry_within_a_milestone"]),
    "G89": (CAUGHT, "the navigator ignores the scene walls it is handed (each intent starts with none)",
            [(NAV, "        if self.carried_scene_walls:\n            self.scene_walls = ",
              "        if False:\n            self.scene_walls = ")],
            ["SceneWallTests.test_the_navigator_starts_from_the_walls_it_is_handed"]),
    "G81": (CAUGHT, "the grader's 'go after the page that told it' check finds nothing",
            [(RATE5, "        if quoted and not any(quoted[:40] in page for frame, page in pages if frame <= (r.get(\"frame\") or 0)):\n",
              "        if False:  # MUTANT G81\n")],
            ["SmallTests.test_the_step5_regexes_with_both_cases"]),
    # ---- the step-5.1 verifier's round (2026-10-14): its two mutants that no test caught (MY3, MY4), and every fix of
    # the round
    "G90": (CAUGHT, "it looks round a new place while in danger (the verifier's MY3: README B's 'never in danger', no test)",
            [(GOALS, "        if mons and (any(m.hp <= 0 for m in mons) or needs_rest(look.party) is not None):\n"
                     "            return False\n",
              "        if False:  # MUTANT G90\n            return False\n")],
            ["VerifierRoundTests.test_no_look_around_while_in_danger"]),
    "G91": (CAUGHT, "the starter bag's 'bag is gone' return disabled (the verifier's MY4: it fired in no graded run)",
            [(SKILL, "        if ui is None and look.screen.game_state != \"CHOOSE_STARTER\":\n            return look\n",
              "        if False:  # MUTANT G91\n            return look\n")],
            ["VerifierRoundTests.test_the_bag_gone_is_handed_back_at_once"]),
    "G92": (CAUGHT, "a map its carried world memory knew is a 'new place' again (the verifier: CH2T 'explore a new place, "
                    "LITTLEROOT_TOWN')",
            [(GOALS, "                or world.current in (self.memory.known_before or ()) or (step is not None and step.do == "
                     "\"intro\")):\n",
              "                or (step is not None and step.do == \"intro\")):  # MUTANT G92\n")],
            ["VerifierRoundTests.test_a_resumed_run_looks_round_only_new_places"]),
    "G93": (CAUGHT, "the detour walks to the explorer's own target, which the walk makes stale (11 of 12 CH1 detours failed at "
                    "once)",
            [(GOALS, "            chosen.append(Target(\"wander\", place.tile, f\"a detour: a look at the {place.kind} at "
                     "{place.tile} \"\n"
                     "                                                       f\"({place.reason})\", place.score))\n",
              "            chosen.append(place)  # MUTANT G93\n")],
            ["VerifierRoundTests.test_a_detour_walks_to_a_place_off_the_way_and_swaps_one_it_cannot_reach"]),
    "G94": (CAUGHT, "a detour may be a step away (no DETOUR_MIN_TILES)",
            [(GOALS, "                     and (at is None or abs(t.tile[0] - at[0]) + abs(t.tile[1] - at[1]) >= "
                     "DETOUR_MIN_TILES)]\n",
              "                     ]  # MUTANT G94\n")],
            ["VerifierRoundTests.test_a_detour_walks_to_a_place_off_the_way_and_swaps_one_it_cannot_reach"]),
    "G95": (CAUGHT, "a detour place it cannot reach is chosen again (no swap)",
            [(GOALS, "            if chosen and not navigator.is_excluded(chosen[-1]):\n", "            if chosen:  # MUTANT G95\n")],
            ["VerifierRoundTests.test_a_detour_walks_to_a_place_off_the_way_and_swaps_one_it_cannot_reach"]),
    "G96": (CAUGHT, "a story goal put aside waits its DECISIONS only (the verifier: ten looks round, 32,000 frames, in CH2)",
            [(GOALS, "        if left < ASIDE_LOOK_MIN:\n", "        if False:  # MUTANT G96\n")],
            ["VerifierRoundTests.test_a_story_goal_put_aside_comes_back_after_its_frames"]),
    "G97": (CAUGHT, "a walk whose budget its battles ate is a failed walk (no walking on: CH2's two walks put aside)",
            [(GOALS, "GO_BATTLE_EXTENSIONS = 2\n", "GO_BATTLE_EXTENSIONS = 0  # MUTANT G97\n")],
            ["VerifierRoundTests.test_a_walk_whose_battles_ate_its_budget_walks_on"]),
    "G98": (CAUGHT, "a draw that chose no errand is not told (the log holds only the draws that chose one)",
            [(GOALS, "        if self.say is not None:\n            self.say(line)\n", "        pass  # MUTANT G98\n")],
            ["VerifierRoundTests.test_a_draw_that_chooses_nothing_is_told"]),
    "G99": (CAUGHT, "the grader counts the rival's POKé BALL as curiosity (the verifier: it is the story's, in BOTH arms)",
            [(RATE5, "    free = curious - sum(f for _, _, f in story_own)\n", "    free = curious  # MUTANT G99\n")],
            ["VerifierRoundTests.test_the_grader_counts_curiosity_the_story_did_not_need"]),
    "G100": (CAUGHT, "the grader's off-the-beeline tiles ignore the beeline's corridor (every tile a run stood on)",
             [(RATE5, "    off = {r[\"seed\"]: r[\"_tiles\"] - union_all for r in rows}\n",
               "    off = {r[\"seed\"]: set(r[\"_tiles\"]) for r in rows}  # MUTANT G100\n")],
             ["VerifierRoundTests.test_the_grader_finds_where_no_beeline_went"]),
    "G102": (CAUGHT, "new places gone past without a look never make it look round the next (one draw each, whatever came "
                     "before: the development sweep's Story seed 4, 212 frames of curiosity)",
             [(GOALS, "            if draw < errands.look_around or self.memory.passed_new >= LOOK_DEBT or owed:\n",
               "            if draw < errands.look_around or owed:  # MUTANT G102\n")],
             ["VerifierRoundTests.test_after_passing_new_places_it_looks_round_the_next"]),
    "G103": (CAUGHT, "the grader's aside streaks find nothing (the verifier's 32,000 frames of asides would pass)",
             [(RATE5, "        out.append((key[len(ASIDE):], spans[i][\"frame\"], last[\"frame\"] + last[\"frames\"] - "
                      "spans[i][\"frame\"], j - i))\n",
               "        pass  # MUTANT G103\n")],
             ["VerifierRoundTests.test_the_grader_measures_a_streak_of_asides"]),
    "G104": (CAUGHT, "the grader's battle-free time counts the battles inside the needs a second time",
             [(RATE5, "            battle += (stop - frame) - inside\n", "            battle += stop - frame  # MUTANT G104\n")],
             ["VerifierRoundTests.test_the_grader_takes_the_battles_out_of_the_time"]),
    "G105": (CAUGHT, "the training bound by the BASE personality, whatever it drifted into (the graded sweep on 501-520's "
                     "two failures)",
             [(RATE5, "    actives = [p for p in row.get(\"rival_actives\") or [] if p]\n",
               "    actives = []  # MUTANT G105\n")],
             ["VerifierRoundTests.test_the_training_bound_follows_the_personality_it_played_as"]),
    "G106": (CAUGHT, "LOSE3 graded on every run, a run that never reached a third loss included (501-520's seed 503)",
             [(RATE5, "        reached3 = [row for row in rows3 if row[4] >= MAX_LOSSES]\n",
               "        reached3 = list(rows3)  # MUTANT G106\n")],
             ["VerifierRoundTests.test_the_lose3_check_grades_the_runs_that_reached_a_third_loss"]),
    "G101": (CAUGHT, "the training bound is round 1's carried 60 steps for every personality (the verifier: not re-derived)",
             [(RATE5, "    return max(BOUNDS[\"CH1_TRAIN_STEPS_MIN\"], math.ceil(errands.train_min_steps * "
                      "BOUNDS[\"CH1_TRAIN_STEPS_SHARE\"]))\n",
               "    return BOUNDS[\"CH1_TRAIN_STEPS_MIN\"]  # MUTANT G101\n")],
             ["VerifierRoundTests.test_the_training_bound_is_rederived_by_personality"]),
    # ---- the step-5.1 verifier's SECOND round (2026-10-14): `test_goals.py` SecondRoundTests (and PlayLoopTests' V9)
    "G107": (CAUGHT, "a GYM's door is not recognised by its look (CH2T searched PETALBURG CITY door by door)",
             [(GOALS, "                elif gym is not None and tile.metatile in gym.metatile:\n",
               "                elif False:  # MUTANT G107\n")],
             ["SecondRoundTests.test_a_gym_door_is_recognised_by_its_look"]),
    "G108": (CAUGHT, "a walk to a GYM is a walk like any other (no door walked into once seen)",
             [(GOALS, "            if goal.kind == \"go\" and is_gym(target_map):\n", "            if False:  # MUTANT G108\n")],
             ["SecondRoundTests.test_a_walk_to_a_gym_goes_in_by_its_door_once_seen"]),
    "G109": (CAUGHT, "a place it has been IN before any door it has seen, however far (step 5's rule: CH2T walked back to "
                     "OLDALE)",
             [(GOALS, "        return min(options, key=lambda option: option[:3])[3] if options else None\n",
               "        return min(options, key=lambda option: (option[1], option[0], option[2]))[3] if options else None"
               "  # MUTANT G109\n")],
             ["SecondRoundTests.test_the_nearest_place_to_heal_and_to_shop"]),
    "G110": (CAUGHT, "hurt in a town whose centre it has not seen, it walks back to the one it knows (no look here first)",
             [(GOALS, "                if (where is not None and town is not None and self._place_key(world, where) not in "
                      "(None, world.current)\n",
               "                if (False and where is not None and town is not None  # MUTANT G110\n")],
             ["SecondRoundTests.test_a_towns_own_centre_is_looked_for_before_walking_back"]),
    "G111": (CAUGHT, "the BALANCE is never owed (the Story's chapter 2 at 16 % errands)",
             [(GOALS, "        if total < BALANCE_MIN_FRAMES:\n            return None\n",
               "        if True:  # MUTANT G111\n            return None\n")],
             ["SecondRoundTests.test_the_balance_owes_a_break_from_the_story",
              "SecondRoundTests.test_an_owed_break_passes_the_draws",
              "SecondRoundTests.test_with_no_draw_due_an_owed_break_looks_round_here_some_more",
              "SecondRoundTests.test_a_walk_stops_where_the_owed_break_can_be_taken"]),
    "G112": (CAUGHT, "the balance counts a curiosity goal the story moved on in as an errand (the graders do not)",
             [(GOALS, "        errand = goal.kind in ERRAND_KINDS and not (story_moved and goal.kind in CURIOSITY_KINDS)\n",
               "        errand = goal.kind in ERRAND_KINDS  # MUTANT G112\n")],
             ["SecondRoundTests.test_the_balance_owes_a_break_from_the_story"]),
    "G113": (CAUGHT, "the balance counts the goals before its first Pokemon",
             [(GOALS, "        if frames <= 0 or not self.memory.decided_with_party:\n",
               "        if frames <= 0:  # MUTANT G113\n")],
             ["SecondRoundTests.test_the_balance_owes_a_break_from_the_story"]),
    "G114": (CAUGHT, "with a break owed and no draw due, it goes on with the story (no look round some more)",
             [(GOALS, "        if (owed and here is not None and OUTDOOR.match(here_const or \"\") and not must_rest and step is "
                      "not None\n",
               "        if (False and owed and here is not None  # MUTANT G114\n")],
             ["SecondRoundTests.test_with_no_draw_due_an_owed_break_looks_round_here_some_more"]),
    "G115": (CAUGHT, "the looks round some more are unbounded (no AGAIN_MAX a map and milestone)",
             [(GOALS, "                and self.memory.again.get(again, 0) < AGAIN_MAX):\n",
               "                and True):  # MUTANT G115\n")],
             ["SecondRoundTests.test_with_no_draw_due_an_owed_break_looks_round_here_some_more"]),
    "G116": (CAUGHT, "a walk never stops where an owed break could be taken",
             [(GOALS, "                    if (nav.world.current != began_on and stop not in manager.memory.owed_stops and "
                      "not manager.hurt(look)\n",
               "                    if (False and nav.world.current != began_on  # MUTANT G116\n")],
             ["SecondRoundTests.test_a_walk_stops_where_the_owed_break_can_be_taken"]),
    "G117": (CAUGHT, "the verifier's V3: a walk whose battles ate its budget walks on ONCE, not GO_BATTLE_EXTENSIONS times",
             [(GOALS, "            for _ in range(GO_BATTLE_EXTENSIONS):\n",
               "            for _ in range(1):  # MUTANT G117 (the verifier's V3)\n")],
             ["SecondRoundTests.test_a_walk_walks_on_twice_when_its_battles_ate_it_twice"]),
    "G118": (CAUGHT, "the verifier's V9: SETTLE_FREE 1 (a goal chosen as a scene begins after a map change)",
             [(MODE, "SETTLE_FREE = 30\n", "SETTLE_FREE = 1  # MUTANT G118 (the verifier's V9)\n")],
             ["PlayLoopTests.test_a_scene_soon_after_a_map_change_comes_before_any_goal"]),
    "G119": (CAUGHT, "a level gained is the party's SUM rising (WALLY's lent Zigzagoon: '10 -> 15')",
             [(MODE, "               \"levels\": seen[\"gained\"],\n",
               "               \"levels\": sum(m.level for m in mons) if mons is not None else before.get(\"levels\"),"
               "  # MUTANT G119\n")],
             ["SecondRoundTests.test_a_level_is_gained_by_one_pokemon_not_by_the_partys_sum"]),
    "G120": (CAUGHT, "which personality judged the run trained is not logged",
             [(GOALS, "                prep[\"judged_by\"] = self.state.active\n", "                pass  # MUTANT G120\n")],
             ["SecondRoundTests.test_whose_rule_judged_the_run_trained_is_logged"]),
    "G121": (CAUGHT, "the training bound ignores the judge (the lowest of the personalities played as: the loosest reading)",
             [(RATE5, "    if row.get(\"rival_judge\"):\n        return train_steps_min(row[\"rival_judge\"])\n",
               "    if False:  # MUTANT G121\n        return train_steps_min(row[\"rival_judge\"])\n")],
             ["SecondRoundTests.test_the_training_bound_is_the_judges_own"]),
    "G122": (CAUGHT, "the grader ignores a goal's END record (a dropped chat counted as WALLY's 11,019-frame scene)",
             [(RATE5, "        elif r.get(\"decision\") == \"goal_end\" and ends and ends[-1] is None:\n",
               "        elif False:  # MUTANT G122\n")],
             ["SecondRoundTests.test_the_grader_ends_a_goal_at_its_end_record"]),
    "G123": (CAUGHT, "the errand share counts the story's own curiosity as errands (the verifier: MIX_MIN inflated)",
             [(RATE5, "    errand = sum(v for k, v in frames.items() if k in ERRAND_KINDS) - sum(f for _, _, f in story_own)\n",
               "    errand = sum(v for k, v in frames.items() if k in ERRAND_KINDS)  # MUTANT G123\n")],
             ["SecondRoundTests.test_the_grader_ends_a_goal_at_its_end_record"]),
    "G124": (CAUGHT, "a DROPPED goal's end is not recorded (the scene after it graded as the goal's)",
             [(MODE, "                hands.note(\"goal_end\", goal.kind, \"dropped: a scene began while it decided\",\n",
               "                hands.note(\"dropped_MUTANT_G124\", goal.kind, \"dropped: a scene began while it decided\",\n")],
             ["PlayLoopTests.test_a_goal_waits_when_a_scene_began_while_it_decided"]),
    "G125": (CAUGHT, "the sweep's chapter-2 floor check finds nothing",
             [(RATE5, "    low = {s: v for s, v in shares.items() if v[1] < BOUNDS[\"MIX_MIN\"]}\n",
               "    low = {}  # MUTANT G125\n")],
             ["SecondRoundTests.test_the_chapter2_checks"]),
    "G126": (CAUGHT, "looking for a town's own centre goes on past its door",
             [(GOALS, "                                                       lambda look: moved_on(look) or "
                      "manager.center_seen_on(goal.via),\n",
               "                                                       lambda look: moved_on(look),  # MUTANT G126\n")],
             ["SecondRoundTests.test_looking_for_a_towns_centre_ends_when_its_door_is_seen"]),
    # ---- found by the round's development sweep (step51wdev1, seeds 31-39), each fix with its mutant
    "G127": (CAUGHT, "a door seen across a map's edge counts as that map's (seeds 33 and 38 stopped on their patience)",
             [(GOALS, "            if kind != landmark or key not in world.maps or world.maps[key].outside(tile):\n",
               "            if kind != landmark or key not in world.maps:  # MUTANT G127\n")],
             ["SecondRoundTests.test_a_door_seen_across_a_maps_edge_is_not_that_maps"]),
    "G128": (CAUGHT, "a door it cannot walk into is never forgotten",
             [(GOALS, "            if outcome.startswith(DOOR_UNUSABLE):\n", "            if False:  # MUTANT G128\n")],
             ["SecondRoundTests.test_a_door_that_cannot_be_walked_into_is_forgotten"]),
    "G129": (CAUGHT, "in danger a heal put aside is tried again for ever (no DANGER_RETRIES)",
             [(GOALS, "                if where is not None and (allowed or (must_rest and retries < DANGER_RETRIES)):\n",
               "                if where is not None and (allowed or must_rest):  # MUTANT G129\n")],
             ["SecondRoundTests.test_a_heal_in_danger_is_tried_again_only_a_few_times"]),
    "G130": (CAUGHT, "the person the story's step names may be a 'chat' (DAD, seeds 37 and 39)",
             [(GOALS, "                    or person.graphics_id in story_gfx):\n", "                    or False):  # MUTANT G130\n")],
             ["SecondRoundTests.test_the_storys_own_person_is_no_chat"]),
    "G131": (CAUGHT, "a look round put aside is a full look round however little of the breather is left (seed 32)",
             [(GOALS, "                    milestone.id, steps=min(LOOK_AROUND_FRAMES, left), key=f\"{ASIDE}{goal.key}\")\n",
               "                    milestone.id, steps=LOOK_AROUND_FRAMES, key=f\"{ASIDE}{goal.key}\")  # MUTANT G131\n")],
             ["SecondRoundTests.test_an_aside_lasts_the_breather_not_longer"]),
    "G132": (CAUGHT, "the scenes between goals are no time in the AI's balance",
             [(MODE, "                manager.spent(BETWEEN_GOALS, hands.pad.frames - ended[0])\n",
               "                pass  # MUTANT G132\n")],
             ["SecondRoundTests.test_a_scene_between_goals_is_the_storys_time_in_the_balance"]),
    "G133": (CAUGHT, "its first POKé BALLS are left to the taste's draw (seed 31's Story player caught nothing in chapter 2)",
             [(GOALS, "            first = look.progress is not None and look.progress.dex_owned <= 1\n",
               "            first = False  # MUTANT G133\n")],
             ["SecondRoundTests.test_its_first_poke_balls_are_tried"]),
    "G136": (CAUGHT, "the balance keeps nothing for curiosity (chapter 1's training fills it with needs)",
             [(GOALS, "        if curious < errands.curious_min * total:\n", "        if False:  # MUTANT G136\n")],
             ["SecondRoundTests.test_the_balance_keeps_some_of_it_for_curiosity"]),
    # ---- found by the graded sweep on 701-720 (it FAILED the chapter-2 floor in seed 706, 28.7 %)
    "G137": (CAUGHT, "a walk to a gym whose door is known goes straight in, past the go's own stops (seed 706)",
             [(GOALS, "        if door is not None and nav.world.current != door[0]:\n",
               "        if False:  # MUTANT G137\n")],
             ["SecondRoundTests.test_a_walk_to_a_known_gym_door_keeps_the_gos_own_stops"]),
    "G138": (CAUGHT, "a town looked round once is taken to have no centre, however much of it is left to see (seed 706)",
             [(GOALS, "                        and not (world.current in self.memory.explored and world.promise(world.current) <= 0)):\n",
               "                        and world.current not in self.memory.explored):  # MUTANT G138\n")],
             ["SecondRoundTests.test_a_towns_own_centre_is_looked_for_before_walking_back"]),
    "G134": (CAUGHT, "the nurse waits out a screen that waits for a press (seed 42's 1,203 frames: the poison's faint)",
             [("hands/menus.py", "    if not (yield from talk(hands, nurse, why, give_way=give_way)):\n",
               "    if not (yield from talk(hands, nurse, why)):  # MUTANT G134\n")],
             ["SecondRoundTests.test_the_nurse_and_the_clerk_give_way_to_a_waiting_screen"]),
    "G135": (CAUGHT, "the clerk waits out a screen that waits for a press",
             [("hands/menus.py", "    if not (yield from talk(hands, clerk, why, give_way=give_way)):\n",
               "    if not (yield from talk(hands, clerk, why)):  # MUTANT G135\n")],
             ["SecondRoundTests.test_the_nurse_and_the_clerk_give_way_to_a_waiting_screen"]),
}

DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_goals
suite = unittest.defaultTestLoader.loadTestsFromModule(test_goals)
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("test_goals.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_goals.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_step5_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_step5_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_step5_tests.py")], cwd=str(root), env=env, capture_output=True,
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
    from ai_player.gates.provenance import snapshot_tree

    out = ["AI PLAYER BUILD STEP 5.1 - MUTANT PROOF OF THE STORY PLAYER (gates/revert_step5.py: G1-G52 step 5's, G53-G106 "
           "step 5.1's, G107-G126 the step-5.1 verifier's second round's)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {provenance(REPO)}",
           f"tree kept: {snapshot_tree(REPO)} (the step-5.1 verifier's second round)",
           "Each mutant breaks ONE rule of the real code in a copy; CAUGHT = its predicted tests of gates/test_goals.py fail.", ""]
    argv = list(sys.argv[1:])
    workers = 1
    if "--workers" in argv:
        at = argv.index("--workers")
        workers = max(1, int(argv[at + 1]))
        del argv[at:at + 2]
    tag = "step51"  # (build step 5.1) the evidence file's tag
    if "--evidence-tag" in argv:
        at = argv.index("--evidence-tag")
        tag = argv[at + 1]
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
        results = list(pool.map(attempt, chosen))
    ok_all = True
    counts = {CAUGHT: 0, REDUNDANT: 0}
    for (name, (prediction, what, edits, expected)), (result, raw, root) in zip(chosen, results):
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
                caught = [t for t in expected if any(b == t or b.startswith((t + " (", t + " [")) for b in bad)]
                ok = ran_copy and caught == expected
                line = (f"[{name}] BROKEN: {what}. Predicted CAUGHT by {expected}. The copy ran {result['ran']} tests "
                        f"({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {failing} -> {'CAUGHT' if ok else 'NOT CAUGHT'}")
            else:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] BROKEN: {what}. Predicted REDUNDANT ALONE, because {expected} The copy ran {result['ran']} "
                        f"tests; failing: {failing or 'none'} -> {'as predicted' if ok else 'PREDICTION WRONG'}")
            if ok and prediction in counts:
                counts[prediction] += 1
        ok_all &= ok
        print(line, flush=True)
        out.append(line)
    verdict = "PASS" if ok_all else "FAIL"
    summary = f"{counts[CAUGHT]} mutants CAUGHT as predicted, {counts[REDUNDANT]} REDUNDANT ALONE as predicted, of {len(MUTANTS) - 1}"
    out += ["", summary, f"OVERALL: {verdict}"]
    print(summary)
    print(f"OVERALL: {verdict}")
    if only is None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-{tag}-REVERT.txt"
        keep_earlier(path)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
