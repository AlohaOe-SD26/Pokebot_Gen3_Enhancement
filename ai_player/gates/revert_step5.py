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
#: (build step 5.2) the sweep harness's second path of the places
PLAY = "gates/play_harness.py"

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
            [(GOALS, "            odds, odds_why = self.curious_odds(self.state.errands.chat, look.frame if frame is None else "
                     "frame)\n",
              "            odds, odds_why = self.curious_odds(0.2, look.frame if frame is None else frame)  # MUTANT G14\n")],
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
            # (R1, build stage 4) re-anchored: the call now hands on the memory file's `lost` line hook; the same deletion
            [(MODE, "            stop = self._count_losses(hands, nav, report, lost_line)\n",
              "            stop = None  # MUTANT G46\n")],
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
            [(GOALS, "            if draw < odds:\n                self.memory.passed_new = 0\n",
              "            if False:  # MUTANT G60\n                self.memory.passed_new = 0\n")],
            ["ExploreTests.test_looking_around_a_new_place_by_personality"]),
    "G61": (CAUGHT, "one look-around rate for every personality (the Story's not lower)",
            [(GOALS, "            odds, odds_why = self.curious_odds(errands.look_around, look.frame)\n",
              "            odds, odds_why = self.curious_odds(0.5, look.frame)  # MUTANT G61\n")],
            ["ExploreTests.test_looking_around_a_new_place_by_personality"]),
    # (re-predicted in build step 5.2, measured by its final full run: NOT CAUGHT) since 5.2 both askers of
    # `may_look_around` guard the beeline themselves: `next_goal` asks it only when `curious_ok()` (False under the
    # beeline control) and the walk's stop only when `stop_new` (False under it)
    "G62": (REDUNDANT, "the beeline control's switch ignored by the look-around",
            [(GOALS, '        if (self.errands_off or here is None or not OUTDOOR.match(const or "") or world.current in '
                     'self.memory.looked\n',
              '        if (here is None or not OUTDOOR.match(const or "") or world.current in self.memory.looked  # MUTANT G62\n')],
            "both askers guard the beeline control already: `next_goal` asks `may_look_around` only when `curious_ok()` "
            "is True, which it never is under `errands_off` (G153 deletes that call and is caught), and the walk's stop "
            "only when `stop_new`, False under it; the test `ExploreTests.test_one_draw_a_map_and_none_under_the_beeline_"
            "control` still holds with the switch removed here."),
    "G87": (CAUGHT, "a walk stops only on a map NEVER visited (step51dev2-4: the look-around's draw was rarely due)",
            [(GOALS, '                    if (nav.world.current not in manager.memory.looked\n',
              '                    if (nav.world.current not in manager.memory.looked\n'
              '                            and nav.world.current not in known_maps_before  # MUTANT G87\n'),
             (GOALS, '            stop_new = goal.kind in ("go", "look_around") and not manager.errands_off\n',
              '            stop_new = goal.kind in ("go", "look_around") and not manager.errands_off\n'
              '            known_maps_before = {key for key, memory in nav.world.maps.items() if memory.visits}  # MUTANT G87\n')],
            ["ExploreTests.test_a_walk_that_arrives_somewhere_new_stops_to_decide"]),
    "G63": (CAUGHT, "never a detour off the way",
            [(GOALS, "            odds, odds_why = self.curious_odds(errands.detour, look.frame)\n            if draw < odds:\n",
              "            odds, odds_why = self.curious_odds(errands.detour, look.frame)\n            if False:  # MUTANT G63\n")],
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
            [(GOALS, "                if told and self.been_to(world, step.map):\n",
              "                if True:  # MUTANT G70\n")],
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
            [(GOALS, "        if walls is not None:\n            nav.carried_scene_walls = walls if blocked is None else {\n",
              "        if False:  # MUTANT G88\n            nav.carried_scene_walls = walls if blocked is None else {\n")],
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
            [(GOALS, "                     and abs(t.tile[0] - at[0]) + abs(t.tile[1] - at[1]) >= DETOUR_MIN_TILES\n",
              "                     and True  # MUTANT G94\n")],
            ["VerifierRoundTests.test_a_detour_walks_to_a_place_off_the_way_and_swaps_one_it_cannot_reach"]),
    "G95": (CAUGHT, "a detour place it cannot reach is chosen again (no swap)",
            [(GOALS, "            if chosen and not navigator.is_excluded(chosen[-1]) and chosen[-1].tile not in avoid:\n",
              "            if chosen:  # MUTANT G95\n")],
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
             [(GOALS, "            if self.memory.passed_new >= LOOK_DEBT:\n",
               "            if False:  # MUTANT G102\n")],
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
    # (build step 5.2: the BALANCE is GONE, the step-5.1 review's finding 2; G111-G116 are re-pointed to its replacement,
    # BOREDOM, and the report the balance's count became; G136, the balance's curiosity minimum, is retired with it)
    "G111": (CAUGHT, "boredom never rises (every curiosity draw at the personality's own odds for ever)",
             [(GOALS, "        return min(1.0, since / max(1, self.state.errands.bored_frames)), since\n",
               "        return 0.0, since  # MUTANT G111\n")],
             ["SecondRoundTests.test_boredom_raises_the_odds_smoothly_and_capped",
              "SecondRoundTests.test_boredom_never_skips_the_dice",
              "SecondRoundTests.test_some_more_only_where_something_is_left_to_walk_to",
              "SecondRoundTests.test_a_walk_stops_where_a_bored_break_can_be_taken"]),
    "G112": (CAUGHT, "the report counts a curiosity goal the story moved on in as an errand (the graders do not)",
             [(GOALS, "        errand = goal.kind in ERRAND_KINDS and not (story_moved and goal.kind in CURIOSITY_KINDS)\n",
               "        errand = goal.kind in ERRAND_KINDS  # MUTANT G112\n")],
             ["ProductiveWiringTests.test_the_goal_managers_report_of_its_frames"]),
    "G113": (CAUGHT, "the report counts the goals before its first Pokemon",
             [(GOALS, "        if frames <= 0 or not self.memory.decided_with_party:\n",
               "        if frames <= 0:  # MUTANT G113\n")],
             ["ProductiveWiringTests.test_the_goal_managers_report_of_its_frames"]),
    "G114": (CAUGHT, "bored and no draw due, it goes on with the story (no look round some more)",
             [(GOALS, "        if (curious and here is not None and OUTDOOR.match(here_const or \"\") and not must_rest and step "
                      "is not None\n",
               "        if (False and curious and here is not None  # MUTANT G114\n")],
             ["SecondRoundTests.test_some_more_only_where_something_is_left_to_walk_to"]),
    "G115": (CAUGHT, "the looks round some more are unbounded (no AGAIN_MAX a map and milestone)",
             [(GOALS, "                and self.memory.again.get(again, 0) < AGAIN_MAX):\n",
               "                and True):  # MUTANT G115\n")],
             ["SecondRoundTests.test_some_more_only_where_something_is_left_to_walk_to"]),
    "G116": (CAUGHT, "a walk never stops where a bored break could be taken",
             [(GOALS, "                    if (nav.world.current != began_on and stop not in manager.memory.break_stops and "
                      "not manager.hurt(look)\n",
               "                    if (False and nav.world.current != began_on  # MUTANT G116\n")],
             ["SecondRoundTests.test_a_walk_stops_where_a_bored_break_can_be_taken"]),
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
    # ---- BUILD STEP 5.2, PRODUCTIVE CURIOSITY (the step-5.1 adversarial review, 2026-10-15: "it LOAFS"): each fix, and
    # (the lessons' PF-2, the call-site census) each new hook's CALL deleted or guarded off where it is asked
    # P1 curiosity by yield
    "G139": (CAUGHT, "the ask step walks to its house with nothing said (5.1: a visit was enough; the review's finding 6)",
             [(GOALS, "                if told and self.been_to(world, step.map):\n",
               "                if self.been_to(world, step.map):  # MUTANT G139\n")],
             ["HintTests.test_before_the_words_it_goes_to_ask_at_the_rivals_house"]),
    "G140": (CAUGHT, "a curiosity goal counts by its kind, whatever it brought (5.1's count: the review's finding 1)",
             [(GOALS, "    made[\"productive\"] = bool(reached and (seen or made[\"maps\"] or made[\"items\"] or made[\"caught\"] "
                      "or made[\"species\"]\n",
               "    made[\"productive\"] = True or bool(reached and (seen or made[\"maps\"] or made[\"items\"] or "
               "made[\"caught\"] or made[\"species\"]  # MUTANT G140\n")],
             ["ProductiveTests.test_a_curiosity_goal_counts_by_what_it_brought",
              "ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    "G141": (CAUGHT, "one new tile is a yield (CH1M's 3,012-frame look round of OLDALE showed one)",
             [(GOALS, "YIELD_TILES_MIN = 8\n", "YIELD_TILES_MIN = 1  # MUTANT G141\n")],
             ["ProductiveTests.test_a_curiosity_goal_counts_by_what_it_brought"]),
    "G142": (CAUGHT, "a detour is credited with what it saw on the way, reached or not (the review's finding 3)",
             [(GOALS, "    reached = goal.kind != \"detour\" or outcome.startswith(\"reached\")\n",
               "    reached = True  # MUTANT G142\n")],
             ["ProductiveTests.test_a_curiosity_goal_counts_by_what_it_brought"]),
    "G143": (CAUGHT, "the play loop never asks what a goal brought (`goal_yield` and the after-snapshot: their call deleted)",
             [(MODE, "            made = goal_yield(goal, before, yield_snapshot(after, world, runner, battle_clock.battle_frames), outcome,\n"
                     "                              hands.pad.frames - began)\n",
               "            made = {\"productive\": True}  # MUTANT G143\n")],
             ["ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    "G144": (CAUGHT, "the play loop's before-snapshot deleted (every count since nothing: everything productive)",
             [(MODE, "            before = yield_snapshot(seen, world, runner, battle_clock.battle_frames)\n",
               "            before = {key: 0 for key in (\"tiles\", \"maps\", \"items\", \"caught\", \"species\", \"pages\")}  "
               "# MUTANT G144\n")],
             ["ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    "G145": (CAUGHT, "an unproductive curiosity goal is still 'done' in the play loop (5.1: a look round that ran its time)",
             [(MODE, "            if goal.kind in CURIOSITY_KINDS and not made[\"productive\"]:\n                ok = False\n",
               "            if False:  # MUTANT G145\n                ok = False\n")],
             ["ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    "G146": (CAUGHT, "the play loop never tells the goal manager what a goal brought (`after_goal`: its call deleted)",
             [(MODE, "            manager.after_goal(goal, made, after.frame, milestone.id, moved_story)\n",
               "            pass  # MUTANT G146\n")],
             ["ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    "G147": (CAUGHT, "a productive curiosity goal does not reset the boredom clock",
             [(GOALS, "            self.memory.curious_since = frame\n", "            pass  # MUTANT G147\n")],
             ["SecondRoundTests.test_only_productive_curiosity_resets_the_boredom_clock"]),
    "G148": (CAUGHT, "ANY curiosity goal resets the boredom clock (5.1 counted curiosity by its frames)",
             [(GOALS, "        self.memory.curious_row += 1\n        brought = ",
               "        self.memory.curious_row += 1\n        self.memory.curious_since = frame  # MUTANT G148\n        brought = ")],
             ["SecondRoundTests.test_only_productive_curiosity_resets_the_boredom_clock"]),
    "G149": (CAUGHT, "a look round that brought nothing does not exhaust its map (CH2M: PETALBURG twice, one tile)",
             [(GOALS, "            self.memory.exhausted[f\"{goal.via}|{milestone_id}\"] = why\n", "            pass  # MUTANT G149\n")],
             ["ProductiveTests.test_what_brought_nothing_is_marked_and_not_tried_again",
              "ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    "G150": (CAUGHT, "a detour that did not get there blocks nothing (CH1C and CH1M chose (-7, 15) twice)",
             [(GOALS, "            self.blocked_on(milestone_id, place[0])[tile] = f\"a detour did not get there (f{frame})\"\n",
               "            pass  # MUTANT G150\n")],
             ["ProductiveTests.test_what_brought_nothing_is_marked_and_not_tried_again"]),
    # P2 boredom, not a quota; spacing
    "G151": (CAUGHT, "no cap on curiosity goals in a row (CH1M ran six)",
             [(GOALS, "        return not self.errands_off and self.memory.curious_row < CURIOUS_ROW_MAX\n",
               "        return not self.errands_off  # MUTANT G151\n")],
             ["SecondRoundTests.test_at_most_two_curiosity_goals_in_a_row"]),
    "G152": (CAUGHT, "the row of curiosity goals is never counted",
             [(GOALS, "        self.memory.curious_row += 1\n", "        pass  # MUTANT G152\n")],
             ["SecondRoundTests.test_only_productive_curiosity_resets_the_boredom_clock"]),
    "G153": (CAUGHT, "the decision never asks the row cap (`curious_ok`'s call in next_goal deleted)",
             [(GOALS, "        curious = self.curious_ok()\n", "        curious = not self.errands_off  # MUTANT G153\n")],
             ["SecondRoundTests.test_at_most_two_curiosity_goals_in_a_row"]),
    "G154": (CAUGHT, "a bored person SKIPS the dice (5.1's quota bypass back)",
             [(GOALS, "            if draw < odds:\n                self.memory.passed_new = 0\n",
               "            if draw < odds or self.boredom(look.frame)[0] >= 1.0:  # MUTANT G154\n"
               "                self.memory.passed_new = 0\n")],
             ["SecondRoundTests.test_boredom_never_skips_the_dice"]),
    "G155": (CAUGHT, "boredom's odds are not capped (a draw certain)",
             [(GOALS, "        top = max(base, CURIOUS_ODDS_CAP)\n", "        top = 1.0  # MUTANT G155\n")],
             ["SecondRoundTests.test_boredom_raises_the_odds_smoothly_and_capped"]),
    "G156": (CAUGHT, "the odds never ask boredom (`boredom`'s call in curious_odds deleted)",
             [(GOALS, "        bored, since = self.boredom(frame)\n        top = ",
               "        bored, since = 0.0, 0  # MUTANT G156\n        top = ")],
             ["SecondRoundTests.test_boredom_raises_the_odds_smoothly_and_capped"]),
    "G157": (CAUGHT, "the look-around draw never asks its odds (`curious_odds`'s call deleted: the base odds only)",
             [(GOALS, "            odds, odds_why = self.curious_odds(errands.look_around, look.frame)\n",
               "            odds, odds_why = errands.look_around, \"MUTANT G157\"\n")],
             ["SecondRoundTests.test_boredom_never_skips_the_dice"]),
    "G158": (CAUGHT, "the catch draw never asks its odds (`curious_odds`'s call deleted)",
             [(GOALS, "            odds, odds_why = self.curious_odds(errands.catch_seek, look.frame)\n",
               "            odds, odds_why = errands.catch_seek, \"MUTANT G158\"\n")],
             ["ProductiveWiringTests.test_boredom_raises_every_curiosity_draw"]),
    "G159": (CAUGHT, "the chat draw never asks its odds (`curious_odds`'s call deleted)",
             [(GOALS, "            odds, odds_why = self.curious_odds(self.state.errands.chat, look.frame if frame is None else "
                      "frame)\n",
               "            odds, odds_why = self.state.errands.chat, \"MUTANT G159\"\n")],
             ["ProductiveWiringTests.test_boredom_raises_every_curiosity_draw"]),
    "G160": (CAUGHT, "the detour draw never asks its odds (`curious_odds`'s call deleted)",
             [(GOALS, "            odds, odds_why = self.curious_odds(errands.detour, look.frame)\n",
               "            odds, odds_why = errands.detour, \"MUTANT G160\"\n")],
             ["ProductiveWiringTests.test_boredom_raises_every_curiosity_draw"]),
    "G161": (CAUGHT, "'some more' never asks boredom (`boredom`'s call deleted in next_goal)",
             [(GOALS, "            bored, since = self.boredom(look.frame)\n            odds = CURIOUS_ODDS_CAP * bored\n",
               "            bored, since = 0.0, 0  # MUTANT G161\n            odds = CURIOUS_ODDS_CAP * bored\n")],
             ["SecondRoundTests.test_some_more_only_where_something_is_left_to_walk_to"]),
    "G162": (CAUGHT, "the walk's break stop never asks boredom (`boredom`'s call deleted in the walk)",
             [(GOALS, "                        bored, since = manager.boredom(look.frame)\n",
               "                        bored, since = 0.0, 0  # MUTANT G162\n")],
             ["SecondRoundTests.test_a_walk_stops_where_a_bored_break_can_be_taken"]),
    "G163": (CAUGHT, "the walk's break stop never asks the row cap (`curious_ok`'s call deleted in the walk)",
             [(GOALS, "                            and manager.curious_ok()):\n", "                            and True):  # MUTANT G163\n")],
             ["ProductiveWiringTests.test_no_break_stop_after_two_curiosity_goals_in_a_row"]),
    "G164": (CAUGHT, "the chat is never drawn (`_chat_person`'s call deleted)",
             [(GOALS, "        chat = self._chat_person(look, world, look.frame, own.gfx if own is not None else ()) if curious "
                      "else None\n",
               "        chat = None  # MUTANT G164\n")],
             ["ErrandTests.test_chatting_rates_by_personality"]),
    # P1 "some more" only where something is left that it can walk to
    "G165": (CAUGHT, "'some more' anywhere (`left_to_see`'s call deleted: CH2M's PETALBURG, nothing left)",
             [(GOALS, "            nothing = self.left_to_see(look, world, milestone.id) if odds > 0 else None\n",
               "            nothing = None  # MUTANT G165\n")],
             ["SecondRoundTests.test_some_more_only_where_something_is_left_to_walk_to"]),
    "G166": (CAUGHT, "a map a look round EXHAUSTED is looked round again",
             [(GOALS, "        why = self.memory.exhausted.get(f\"{world.current}|{milestone_id}\")\n",
               "        why = None  # MUTANT G166\n")],
             ["SecondRoundTests.test_some_more_only_where_something_is_left_to_walk_to"]),
    "G167": (CAUGHT, "a frontier is 'left to see' though nobody lets it through (`_known_reach`'s call deleted)",
             [(GOALS, "        reach = _known_reach(here, (player.x, player.y), frozenset(set(here.people_now) | blocked))\n",
               "        reach = frontier  # MUTANT G167\n")],
             ["SecondRoundTests.test_some_more_only_where_something_is_left_to_walk_to"]),
    "G168": (CAUGHT, "'some more' at a frontier curiosity found blocked (`blocked_on`'s call deleted in left_to_see)",
             [(GOALS, "        blocked = set(self.blocked_on(milestone_id, world.current))\n",
               "        blocked = set()  # MUTANT G168\n")],
             ["ProductiveWiringTests.test_no_look_round_some_more_past_a_blocked_frontier"]),
    # P1 the look round only among new things
    "G169": (CAUGHT, "a look round may choose any place, the wander among what it has seen and the way back too (5.1)",
             [(GOALS, "                 if t.kind in LOOK_KINDS and t.tile not in avoid]\n",
               "                 if t.tile not in avoid]  # MUTANT G169\n")],
             ["ProductiveTests.test_a_look_round_chooses_only_new_things_and_ends_when_none_is_left"]),
    "G170": (CAUGHT, "a look round chooses a place curiosity found blocked",
             [(GOALS, "                 if t.kind in LOOK_KINDS and t.tile not in avoid]\n",
               "                 if t.kind in LOOK_KINDS]  # MUTANT G170\n")],
             ["ProductiveTests.test_a_look_round_chooses_only_new_things_and_ends_when_none_is_left"]),
    "G171": (CAUGHT, "a look round carries on from a blocked place",
             [(GOALS, "        if old.tile in blocked(nav.world.current):\n            return None\n        carried = ",
               "        if False:  # MUTANT G171\n            return None\n        carried = ")],
             ["ProductiveTests.test_a_look_round_chooses_only_new_things_and_ends_when_none_is_left"]),
    "G172": (CAUGHT, "a look round's novelty window is the navigator's 3,000 frames (CH1M ran it out twice at OLDALE)",
             [(GOALS, "carry_on=look_carry, novelty_window=CURIOUS_NOVELTY)\n",
               "carry_on=look_carry, novelty_window=3000)  # MUTANT G172\n")],
             ["ProductiveTests.test_a_look_round_chooses_only_new_things_and_ends_when_none_is_left"]),
    "G173": (CAUGHT, "the look round's choice never handed to the intent (`look_choose`'s reference deleted)",
             [(GOALS, "    return Intent(\"look round\", budget, look_choose, done, ",
               "    return Intent(\"look round\", budget, lambda nav, look: None, done, ")],
             ["ProductiveTests.test_a_look_round_chooses_only_new_things_and_ends_when_none_is_left"]),
    "G174": (CAUGHT, "the look round's carry-on never handed to the intent (`look_carry`'s reference deleted)",
             [(GOALS, "carry_on=look_carry, novelty_window=CURIOUS_NOVELTY)\n",
               "carry_on=None, novelty_window=CURIOUS_NOVELTY)  # MUTANT G174\n")],
             ["ProductiveTests.test_a_look_round_chooses_only_new_things_and_ends_when_none_is_left"]),
    "G175": (CAUGHT, "an explore goal walks 5.1's look around (`look_round_intent`'s call in _pursue deleted)",
             [(GOALS, "                intent = (look_round_intent(manager.state.active, budget, look_saw_nothing,\n"
                      "                                            lambda key: manager.blocked_on(milestone.id, key))\n"
                      "                          if goal.kind == \"explore\"\n",
               "                intent = (None  # MUTANT G175\n"
               "                          if False\n")],
             ["ProductiveWiringTests.test_an_explore_goal_looks_round_with_the_look_round_intent"]),
    "G176": (CAUGHT, "an explore goal's look round is handed no blocked places (`blocked_on`'s call deleted in _pursue)",
             [(GOALS, "                                            lambda key: manager.blocked_on(milestone.id, key))\n",
               "                                            lambda key: {})  # MUTANT G176\n")],
             ["ProductiveWiringTests.test_an_explore_goal_looks_round_with_the_look_round_intent"]),
    # P3 detours that arrive
    "G177": (CAUGHT, "the detour says 'reached' however it ended (5.1's 'looked at the ... at T')",
             [(GOALS, "        if not reached:\n            why = (\"the walk left the map\"",
               "        if False:  # MUTANT G177\n            why = (\"the walk left the map\"")],
             ["ProductiveTests.test_a_detour_says_whether_it_arrived"]),
    "G178": (CAUGHT, "a detour that did not arrive is 'done' (5.1: a budget that ran out was done)",
             [(GOALS, "            return outcome.startswith(\"reached\"), outcome\n",
               "            return outcome.startswith((\"reached\", \"not reached\")), outcome  # MUTANT G178\n")],
             ["ProductiveTests.test_a_detour_says_whether_it_arrived"]),
    "G179": (CAUGHT, "a detour may choose a place it cannot walk to (`_known_reach`'s call deleted in the detour)",
             [(GOALS, "            reach = _known_reach(memory, at, frozenset(set(memory.people_now) | set(avoid) | set(walled.get(memory.key, ()))))\n",
               "            reach = set(memory.tiles)  # MUTANT G179\n")],
             ["ProductiveTests.test_a_detour_chooses_only_a_place_it_can_walk_to"]),
    "G180": (CAUGHT, "a detour may choose a place past an edge it has seen crossed (`outside`'s call deleted)",
             [(GOALS, "                     and t.tile in reach and not _beside(t.tile, avoid) and not memory.outside(t.tile)]\n",
               "                     and t.tile in reach and not _beside(t.tile, avoid)]  # MUTANT G180\n")],
             ["ProductiveTests.test_a_detour_never_chooses_a_blocked_place_or_one_past_a_known_edge"]),
    "G181": (CAUGHT, "a detour is handed no blocked places (`blocked_on`'s call deleted in the detour)",
             [(GOALS, "        avoid = manager.blocked_on(milestone.id if milestone is not None else None, began_on)\n",
               "        avoid = {}  # MUTANT G181\n")],
             ["ProductiveTests.test_a_detour_never_chooses_a_blocked_place_or_one_past_a_known_edge"]),
    # (re-predicted after step52dev2: 5.2's first version checked `t.tile not in avoid`, REDUNDANT with the reach; the check
    # is now "not BESIDE a blocked place", which the reach does not guard)
    "G182": (CAUGHT, "a detour's own check of a blocked place, and of the tiles beside one, removed (`_beside`'s call deleted)",
             [(GOALS, "                     and t.tile in reach and not _beside(t.tile, avoid) and not memory.outside(t.tile)]\n",
               "                     and t.tile in reach and not memory.outside(t.tile)]  # MUTANT G182\n")],
             ["ProductiveTests.test_a_detour_never_chooses_a_place_beside_a_blocked_one"]),
    "G183": (CAUGHT, "the detour does not talk to the person it walked over to (the review's finding 3)",
             [(GOALS, "        if kind == \"people\" and whos[-1] is not None:\n",
               "        if False:  # MUTANT G183\n")],
             ["ProductiveTests.test_a_detour_to_a_person_talks_to_them"]),
    "G184": (CAUGHT, "the detour never looks for the person on arrival (`look`'s call deleted)",
             [(GOALS, "            look = hands.look()\n            person = next((o for o in (look.view.objects",
               "            look = types_mutant = None  # MUTANT G184\n            person = next((o for o in (() if True else look.view.objects")],
             ["ProductiveTests.test_a_detour_to_a_person_talks_to_them"]),
    "G185": (CAUGHT, "the detour never talks on arrival (`talk_to`'s call deleted)",
             [(GOALS, "                talk = yield from talk_to(hands, nav, person, f\"{goal.reason}: hello to the person it walked "
                      "over to\")\n",
               "                talk = \"MUTANT G185: no talk\"\n")],
             ["ProductiveTests.test_a_detour_to_a_person_talks_to_them"]),
    "G186": (REDUNDANT, "the detour's walk does not end when it leaves the map (its choice returns nothing there anyway)",
             [(GOALS, "                        lambda look: bool(reached) or nav.world.current != began_on or detour_turned_back(look),\n",
               "                        lambda look: bool(reached) or detour_turned_back(look),  # MUTANT G186\n")],
             "`detour_choose` returns None once the map changed, so the navigator stops the walk at once (\"nothing left to "
             "try\") and the outcome is the same \"not reached ... (the walk left the map)\"."),
    "G187": (CAUGHT, "the detour's choice never handed to the intent (`detour_choose`'s reference deleted)",
             [(GOALS, "        intent = Intent(f\"a detour ({goal.reason[:40]})\", goal.steps, detour_choose,\n",
               "        intent = Intent(f\"a detour ({goal.reason[:40]})\", goal.steps, lambda n, l: None,  # MUTANT G187\n")],
             ["ProductiveTests.test_a_detour_says_whether_it_arrived"]),
    "G188": (CAUGHT, "a detour goal is never walked (`_detour`'s call in _pursue deleted)",
             [(GOALS, "            outcome = yield from self._detour(goal, milestone)\n",
               "            outcome = \"not reached: MUTANT G188\"\n")],
             ["ProductiveTests.test_a_detour_says_whether_it_arrived"]),
    # P1/P3 someone who keeps standing in the way
    "G189": (CAUGHT, "nobody watches for someone standing in the way (`_PersonBlock` never made: 5.1's 61 people in the way)",
             [(GOALS, "        if blocked is not None and watchers is not None and hasattr(nav, \"stats\"):\n"
                      "            watch = _PersonBlock(nav, lambda key, tile, why: self._blocked(milestone, key, tile, why))\n",
               "        if False:  # MUTANT G189\n"
               "            watch = _PersonBlock(nav, lambda key, tile, why: self._blocked(milestone, key, tile, why))\n")],
             ["ProductiveTests.test_blocked_places_wall_curiosity_walks_only",
              "ProductiveWiringTests.test_someone_in_the_way_is_blocked_through_pursue"]),
    "G190": (CAUGHT, "the watch never blocks the place (`on_block`'s call deleted)",
             [(GOALS, "            self.on_block(plan.map, tile, f\"someone stood in the way",
               "            (lambda *ignored: None)(plan.map, tile, f\"someone stood in the way")],
             ["ProductiveTests.test_someone_in_the_way_again_and_again_blocks_the_place"]),
    "G191": (CAUGHT, "the watch blocks a place though the walk brought new tiles since (no new start of the count)",
             [(GOALS, "        if hit is None or nav.world.tiles_learned > hit[1]:\n", "        if hit is None:  # MUTANT G191\n")],
             ["ProductiveTests.test_someone_in_the_way_again_and_again_blocks_the_place"]),
    "G192": (CAUGHT, "the watch is handed no `_blocked` (its call deleted: nothing blocked through pursue)",
             [(GOALS, "            watch = _PersonBlock(nav, lambda key, tile, why: self._blocked(milestone, key, tile, why))\n",
               "            watch = _PersonBlock(nav, lambda key, tile, why: None)  # MUTANT G192\n")],
             ["ProductiveWiringTests.test_someone_in_the_way_is_blocked_through_pursue"]),
    "G193": (CAUGHT, "a place blocked is not a wall of the walk at once",
             [(GOALS, "            walls.setdefault(key, set()).add(tile)\n", "            pass  # MUTANT G193\n")],
             ["ProductiveWiringTests.test_a_blocked_place_is_a_wall_at_once_and_kept"]),
    "G194": (CAUGHT, "a place blocked is not kept for the milestone (`blocked_on`'s call deleted in _blocked)",
             [(GOALS, "        self.manager.blocked_on(milestone.id, key)[tile] = why\n", "        pass  # MUTANT G194\n")],
             ["ProductiveWiringTests.test_a_blocked_place_is_a_wall_at_once_and_kept"]),
    "G195": (CAUGHT, "the blocked places join the scene walls the STORY's walks carry",
             [(GOALS, "                    walls.setdefault(key, set()).update(set(tiles) - set((blocked or {}).get(key, {})))\n",
               "                    walls.setdefault(key, set()).update(tiles)  # MUTANT G195\n")],
             ["ProductiveTests.test_blocked_places_wall_curiosity_walks_only"]),
    "G196": (CAUGHT, "the blocked places are not walls of the curiosity walks",
             [(GOALS, "            nav.carried_scene_walls = walls if blocked is None else {\n",
               "            nav.carried_scene_walls = walls if True else {  # MUTANT G196\n")],
             ["ProductiveTests.test_blocked_places_wall_curiosity_walks_only"]),
    # P6 a known town is no new place
    "G197": (CAUGHT, "a town it has LEFT is 'a new place' again (`left_before`'s call deleted: CH1M's OLDALE)",
             [(GOALS, "        if self.left_before(world):\n", "        if False:  # MUTANT G197\n")],
             ["ProductiveTests.test_a_known_town_is_no_new_place"]),
    "G198": (CAUGHT, "no look round of a new place is ever drawn (`may_look_around`'s call in next_goal deleted)",
             [(GOALS, "        if curious and self.may_look_around(look, world, step):\n",
               "        if curious and False:  # MUTANT G198\n")],
             ["ExploreTests.test_looking_around_a_new_place_by_personality"]),
    "G199": (CAUGHT, "a walk never stops on a new outdoor map (`may_look_around`'s call in the walk deleted)",
             [(GOALS, "                            and manager.may_look_around(look, nav.world, manager.story_step(look, "
                      "nav.world, milestone))):\n",
               "                            and False):  # MUTANT G199\n")],
             ["ExploreTests.test_a_walk_that_arrives_somewhere_new_stops_to_decide"]),
    # P4 the pushing property: the AI's record
    "G200": (CAUGHT, "the push watch counts the time a text or a scene takes (no pause)",
             [(WAITING, "        if not free:\n            self._free_at = None  # paused",
               "        if False:\n            self._free_at = None  # MUTANT G200 paused")],
             ["ProductiveTests.test_the_push_watch_measures_pressing_that_brings_nothing_new"]),
    "G201": (CAUGHT, "something new never ends a pushing stretch (`_end_stretch`'s call guarded off)",
             [(WAITING, "        if battle or mark != self.mark:\n            self._end_stretch()\n",
               "        if battle:  # MUTANT G201\n            self._end_stretch()\n")],
             ["ProductiveTests.test_the_push_watch_measures_pressing_that_brings_nothing_new"]),
    "G202": (CAUGHT, "a stretch with no press is pushing too",
             [(WAITING, "        if pressed <= 0:\n            return\n        frames = stretch[\"frames\"]\n",
               "        if False:  # MUTANT G202\n            return\n        frames = stretch[\"frames\"]\n")],
             ["ProductiveTests.test_the_push_watch_measures_pressing_that_brings_nothing_new"]),
    "G203": (CAUGHT, "the run's last stretch is never closed (`_end_stretch`'s call in wind_up deleted)",
             [(WAITING, "this one's.)\"\"\"\n        self._end_stretch()\n", "this one's.)\"\"\"\n        pass  # MUTANT G203\n")],
             ["ProductiveWiringTests.test_the_push_watch_closes_its_last_stretch_when_wound_up"]),
    "G204": (CAUGHT, "the play brain never watches its pushing (`PushWatch`'s making and installing deleted)",
             [(MODE, "        pushes = PushWatch(lambda: hands.pad.presses, hands.note,\n"
                     "                           lambda: (world.tiles_learned, sum(1 for memory in world.maps.values() if "
                     "memory.visits)))\n        hands.watchers.append(pushes)\n",
               "        pushes = None  # MUTANT G204\n")],
             ["ProductiveWiringTests.test_the_play_loop_reports_pressing_that_brought_nothing"]),
    "G205": (CAUGHT, "the play brain's end never winds the watch up (`wind_up`'s call deleted: the last stretch lost)",
             [(MODE, "            pushes.wind_up()\n", "            pass  # MUTANT G205\n")],
             ["ProductiveWiringTests.test_the_play_loop_reports_pressing_that_brought_nothing"]),
    "G206": (CAUGHT, "the play brain's end never reports the pushing (`push_report`'s call deleted)",
             [(MODE, "            report[\"pushes\"] = pushes.push_report()\n", "            pass  # MUTANT G206\n")],
             ["ProductiveWiringTests.test_the_play_loop_reports_pressing_that_brought_nothing"]),
    # the hooks of the changed play loop and runner (the call-site census)
    "G207": (CAUGHT, "the play loop never decides (`next_goal`'s call deleted)",
             [(MODE, "            goal = manager.next_goal(look, world, milestone, index)\n",
               "            goal = Goal(\"look_around\", \"MUTANT G207\", milestone.id, key=\"look_around\")\n")],
             ["ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    "G208": (CAUGHT, "the play loop never pursues a goal (`pursue`'s call deleted)",
             [(MODE, "            ok, outcome = yield from runner.pursue(goal, milestone, index, current)\n",
               "            ok, outcome = False, \"MUTANT G208: not pursued\"\n")],
             ["PlayLoopTests.test_battles_lost_inside_goals_end_the_play_loop"]),
    "G209": (CAUGHT, "the play brain is never played (`_play`'s call in `_skill` deleted)",
             [(MODE, "            return (yield from self._play(hands, personality))\n",
               "            return \"MUTANT G209: no play\"\n")],
             ["ProductiveWiringTests.test_the_play_brain_is_played_through_its_skill"]),
    "G210": (CAUGHT, "a goal is never played by the runner (`_pursue`'s call in `pursue` deleted)",
             [(GOALS, "            return (yield from self._pursue(goal, milestone, index, current))\n",
               "            return False, \"MUTANT G210\"\n")],
             ["ProductiveTests.test_a_detour_says_whether_it_arrived"]),
    "G211": (CAUGHT, "a ball walked back to is never picked up (`pursue`'s call in `_back_to_ball` deleted)",
             [(GOALS, "        outcome = yield from self.pursue(replace(goal, target=ball, tile=None), milestone, index, current)\n",
               "        outcome = (False, \"not picked up: MUTANT G211\")\n")],
             ["ProductiveWiringTests.test_a_ball_seen_earlier_is_picked_up_through_pursue"]),
    "G212": (CAUGHT, "a story step's goal never made (`_story_step_goal`'s call deleted)",
             [(GOALS, "        goal = self._story_step_goal(look, world, milestone, step)\n",
               "        goal = Goal(\"look_around\", \"MUTANT G212\", milestone.id, key=\"look_around\")\n")],
             ["HintTests.test_after_the_words_it_goes_to_route_103_with_the_map"]),
    # the grader of productive curiosity (`rate_step5.py`) and its second path (`play_harness.py` PlaceRecorder)
    "G213": (CAUGHT, "the grader's intent mix counts curiosity that brought nothing (5.1's count by kind)",
             [(RATE5, "    curious, free, errand = curious - idle, free - idle, errand - idle\n",
               "    curious, free, errand = curious, free, errand  # MUTANT G213\n")],
             ["GraderYieldTests.test_the_intent_mix_counts_curiosity_that_brought_nothing_as_idle"]),
    "G214": (CAUGHT, "the game's yield takes one new tile for a yield",
             [(RATE5, "    seen = tiles >= YIELD_TILES and (kind not in SEEING or tiles * 1000 >= YIELD_TILE_RATE * walking)\n",
               "    seen = tiles >= 1 and (kind not in SEEING or tiles * 1000 >= YIELD_TILE_RATE * walking)  # MUTANT G214\n")],
             ["GraderYieldTests.test_the_game_says_what_a_span_brought"]),
    "G215": (CAUGHT, "the grader believes the detour's own word (the game's position never asked)",
             # (build step 5.3, the re-sourcing build, item 16(a)) re-pointed: arrival is now judged over [stop - slack, stop]
             [(RATE5, "            there = bool(place) and (place[0], place[1], place[2]) in stood\n",
               "            there = said  # MUTANT G215\n")],
             ["GraderYieldTests.test_the_grader_checks_a_detours_word_against_the_game"]),
    "G216": (CAUGHT, "the grader's streaks are never broken by a story goal (one streak of all curiosity)",
             [(RATE5, "            out.append((streak[0][\"frame\"], len(streak), streak[-1][\"frame\"] + streak[-1][\"frames\"] - "
                      "streak[0][\"frame\"]))\n            streak = []\n",
               "            pass  # MUTANT G216\n")],
             ["GraderYieldTests.test_the_grader_finds_curiosity_streaks"]),
    "G217": (CAUGHT, "the grader finds no place left before and called new",
             [(RATE5, "            bad.append((frame, const))\n", "            pass  # MUTANT G217\n")],
             ["GraderYieldTests.test_a_place_left_before_called_new_by_the_games_stays"]),
    "G218": (CAUGHT, "the grader reads no pushing from the AI's record",
             [(RATE5, "    return max([int(end.get(\"longest\") or 0)] + noted)\n", "    return 0  # MUTANT G218\n")],
             ["GraderYieldTests.test_the_grader_reads_pushing_and_person_blocks"]),
    "G219": (CAUGHT, "the BLOCKED arm's reach counts nothing",
             [(RATE5, "            count += 1\n            most = max(most, count)\n", "            pass  # MUTANT G219\n")],
             ["GraderYieldTests.test_the_grader_reads_pushing_and_person_blocks"]),
    "G220": (CAUGHT, "the game's second path counts a text's time as free (no pause)",
             [(PLAY, "        if not free:\n            self._free_at = None\n            return\n        presses = self.controls"
                     ".presses\n",
               "        if False:  # MUTANT G220\n            self._free_at = None\n            return\n        presses = "
               "self.controls.presses\n")],
             ["GraderYieldTests.test_the_game_side_recorder_of_places"]),
    "G221": (CAUGHT, "the game's second path never ends a stretch at new tiles",
             [(PLAY, "        if state == \"BATTLE\" or new:\n", "        if state == \"BATTLE\":  # MUTANT G221\n")],
             ["GraderYieldTests.test_the_game_side_recorder_of_places"]),
    # the walk's own `walk_done` (changed: the bored break stop) handed to each walk that uses it (its references deleted)
    "G222": (CAUGHT, "a walk to a gym is handed no stops (`walk_done`'s reference deleted in the gym walk)",
             [(GOALS, "                outcome = yield from self._to_building(goal, target_map, budget, walk_done)\n",
               "                outcome = yield from self._to_building(goal, target_map, budget, lambda look: False)  "
               "# MUTANT G222\n")],
             ["SecondRoundTests.test_a_walk_to_a_known_gym_door_keeps_the_gos_own_stops"]),
    "G223": (CAUGHT, "a walk to a map is handed no stops (`walk_done`'s reference deleted in the walk)",
             [(GOALS, "                outcome = yield from self._walk_on_after_battles(target_map, goal.reason, budget, "
                      "walk_done)\n",
               "                outcome = yield from self._walk_on_after_battles(target_map, goal.reason, budget, "
               "lambda look: False)  # MUTANT G223\n")],
             ["SecondRoundTests.test_a_walk_stops_where_a_bored_break_can_be_taken"]),
    "G224": (CAUGHT, "a look round is handed no stops (`walk_done`'s reference deleted in the look round)",
             [(GOALS, "                intent = (look_round_intent(manager.state.active, budget, look_saw_nothing,\n",
               "                intent = (look_round_intent(manager.state.active, budget, lambda look: False,  # MUTANT G224\n")],
             ["ProductiveWiringTests.test_an_explore_goal_looks_round_with_the_look_round_intent"]),
    "G225": (CAUGHT, "a look-around walk is handed no stops (`walk_done`'s reference deleted in travel_intent's call)",
             [(GOALS, "                          else travel_intent(None, manager.state.active, budget, walk_done, "
                      "stay=goal.kind == \"find\"))\n",
               "                          else travel_intent(None, manager.state.active, budget, lambda look: False, "
               "stay=goal.kind == \"find\"))  # MUTANT G225\n")],
             ["ProductiveWiringTests.test_a_look_around_walk_stops_for_an_item_ball"]),
    # the play loop's endings, whose `_play_end` (changed: its report of the pushing) they call, where a test drives them
    "G226": (CAUGHT, "the play loop does not end when its target is reached",
             [(MODE, "            if milestone is None or index > target:\n                return self._play_end(hands, story, "
                     "manager, runner, report, \"done\", f\"{options.target} reached\")\n",
               "            if False:  # MUTANT G226\n                return self._play_end(hands, story, "
               "manager, runner, report, \"done\", f\"{options.target} reached\")\n")],
             ["ProductiveWiringTests.test_the_play_loop_ends_when_its_target_is_reached"]),
    "G227": (CAUGHT, "the play loop does not end at MAX_LOSSES",
             [(MODE, "            if stop is not None:\n                return self._play_end(hands, story, manager, runner, report, "
                     "\"stuck\", stop)\n",
               "            if False:  # MUTANT G227\n                return self._play_end(hands, story, manager, runner, report, "
               "\"stuck\", stop)\n")],
             ["PlayLoopTests.test_battles_lost_inside_goals_end_the_play_loop"]),
    "G228": (CAUGHT, "the play loop does not end on its patience",
             [(MODE, "            if hands.pad.frames - changed_at > STORY_PATIENCE:\n                return self._play_end(hands, "
                     "story, manager, runner, report, \"stuck\",\n"
                     "                                      f\"no progress for {hands.pad.frames - changed_at} frames (no "
                     "milestone, battle won \"\n"
                     "                                      f\"training, level, new map, catch, item or heal; since "
                     "{milestone.title})\")\n",
               "            if False:  # MUTANT G228\n                return self._play_end(hands, "
               "story, manager, runner, report, \"stuck\",\n"
               "                                      f\"no progress for {hands.pad.frames - changed_at} frames (no "
               "milestone, battle won \"\n"
               "                                      f\"training, level, new map, catch, item or heal; since "
               "{milestone.title})\")\n")],
             ["PlayLoopTests.test_patience_ends_goals_that_never_move_the_story"]),
    # (R5, backlog item R5 "a FREE-SCREEN precondition", 2026-10-28) "done" waits for a free screen: each new call of the
    # settle before "done" and of the end record, DELETED (LESSONS PF-2; the call census lists their sites)
    "G347": (CAUGHT, "the run ends \"done\" on the pass's look whatever is on screen (the settle's call deleted)",
             [(MODE, "                yield from self._settle_before_done(hands, nav, look, options.target, report)\n",
               "                pass  # MUTANT G347\n")],
             ["PlayLoopTests.test_r5_done_plays_out_the_screen_first",
              "PlayLoopTests.test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so",
              "PlayLoopTests.test_r5_one_free_look_before_an_arrival_scene_is_not_a_free_screen"]),
    "G348": (CAUGHT, "no end records the screen it ends on (`_end_screen`'s call deleted)",
             [(MODE, "        screen = report[\"end_screen\"] = self._end_screen(hands, report, kind)\n",
               "        screen = report[\"end_screen\"] = {}  # MUTANT G348\n")],
             ["PlayLoopTests.test_r5_every_end_records_its_screen",
              "PlayLoopTests.test_r5_done_on_a_free_screen_plays_nothing_out"]),
    "G349": (CAUGHT, "one free look is taken for a free screen (the settle's decision pause and its second look deleted)",
             # (R5's fix round) re-anchored on the pause block as the fix round wrote it (its frames handed on through
             # `_settle_frames`, its budget cut said): the same deletion, the pause and the look after it
             [(MODE, "            pause, before = hands.pad.think_frames(), hands.pad.frames\n"
                     "            ended, _ = yield from self._settle_frames(hands, hands.pad.idle(\n"
                     "                pause, f\"deciding to stop here, {target} reached: does a scene begin?\"))\n"
                     "            paused += hands.pad.frames - before\n"
                     "            look = hands.look()\n"
                     "            if not ended:\n"
                     "                cut, stop = True, f\"the run's frame budget ran out ({self.settings.frames} frames)\"\n"
                     "                break\n"
                     "            if nav_free(look):\n"
                     "                break\n",
               "            break  # MUTANT G349\n")],
             ["PlayLoopTests.test_r5_one_free_look_before_an_arrival_scene_is_not_a_free_screen",
              "PlayLoopTests.test_r5_done_on_a_free_screen_plays_nothing_out"]),
    "G350": (CAUGHT, "a battle the settle before \"done\" lost is not counted (the settle's `_count_losses` call deleted)",
             # (R5's fix round) re-anchored: the count's result is now read (the MAX_LOSSES stop, R5-F5)
             # (R1, build stage 4) re-anchored again: the call hands on the `lost` line hook; the same deletion
             [(MODE, "                lost = self._count_losses(hands, nav, report, self._lost_line(hands))\n",
               "                lost = None  # MUTANT G350\n")],
             ["PlayLoopTests.test_r5_a_battle_the_settle_lost_is_counted",
              "PlayLoopTests.test_r5_the_last_allowed_loss_inside_the_settle_ends_it"]),
    "G351": (CAUGHT, "the settle before \"done\" is unbounded (LESSONS PL-4: `DONE_SETTLE_ROUNDS` not applied)",
             [(MODE, "        for _ in range(DONE_SETTLE_ROUNDS):\n", "        while True:  # MUTANT G351\n")],
             ["PlayLoopTests.test_r5_the_settle_is_bounded"]),
    # (R5's FIX ROUND, 2026-10-28) the adversarial review's findings (R5-F1, F2, F4, F5, F6) and the independent mutant
    # sweep's 13 survivors (S04-S56), each now caught by its own assertion of `test_goals.py` PlayLoopTests (`test_r5_*`)
    "G352": (CAUGHT, "the screen is never played out before \"done\" (the settle's `play_out` call deleted: the review's RV1)",
             [(MODE, "                ended, stop = yield from self._settle_frames(hands, play_out(hands, nav,\n"
                     "                                                                             f\"{target} reached: "
                     "what is on screen first\"))\n",
               "                ended, stop = True, None  # MUTANT G352\n")],
             ["PlayLoopTests.test_r5_done_plays_out_the_screen_first",
              "PlayLoopTests.test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so",
              "PlayLoopTests.test_r5_one_free_look_before_an_arrival_scene_is_not_a_free_screen",
              "PlayLoopTests.test_r5_the_measured_ch2_dad_chain_takes_three_rounds",
              "PlayLoopTests.test_r5_every_milestone_passed_a_box_is_played_out_first"]),
    "G353": (CAUGHT, "an end on a screen that did not free is not SAID (the settle's tell and note deleted: the review's RV2)",
             [(MODE, "            hands.tell(f\"[AI-GOALS] {target} reached, but the screen did not free",
               "            (f\"[AI-GOALS] {target} reached, but the screen did not free"),
              (MODE, "            hands.note(\"end_screen\", \"not free\", held, {",
               "            (\"end_screen\", \"not free\", held, {")],
             ["PlayLoopTests.test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so",
              "PlayLoopTests.test_r5_the_settle_is_bounded"]),
    "G354": (CAUGHT, "the settle's bound below the MEASURED chain's three rounds (`DONE_SETTLE_ROUNDS` 2: the review's R5-F2, "
                     "the sweep's S23)",
             [(MODE, "DONE_SETTLE_ROUNDS = 6\n", "DONE_SETTLE_ROUNDS = 2  # MUTANT G354\n")],
             ["PlayLoopTests.test_r5_the_measured_ch2_dad_chain_takes_three_rounds"]),
    "G355": (CAUGHT, "no settle when no milestone is read (every required one passed: the sweep's S04)",
             [(MODE, "            if milestone is None or index > target:\n"
                     "                # (R5, backlog item R5: a FREE SCREEN",
               "            if milestone is not None and index > target:  # MUTANT G355\n"
               "                # (R5, backlog item R5: a FREE SCREEN")],
             ["PlayLoopTests.test_r5_every_milestone_passed_a_box_is_played_out_first"]),
    "G356": (CAUGHT, "the frame budget cuts a reached target's play-out into \"stopped\" (the play-out handed on with no "
                     "budget guard: the review's R5-F1)",
             [(MODE, "                ended, stop = yield from self._settle_frames(hands, play_out(hands, nav,\n"
                     "                                                                             f\"{target} reached: "
                     "what is on screen first\"))\n",
               "                ended, stop = True, (yield from play_out(hands, nav, f\"{target} reached: what is on screen "
               "first\"))  # MUTANT G356\n")],
             ["PlayLoopTests.test_r5_the_frame_budget_never_cuts_a_reached_target_short_of_its_end"]),
    "G357": (CAUGHT, "the frame budget cuts a reached target's decision pause into \"stopped\" (the pause handed on with no "
                     "budget guard: R5-F1)",
             [(MODE, "            ended, _ = yield from self._settle_frames(hands, hands.pad.idle(\n"
                     "                pause, f\"deciding to stop here, {target} reached: does a scene begin?\"))\n",
               "            ended, _ = True, (yield from hands.pad.idle(pause, f\"deciding to stop here, {target} reached: "
               "does a scene begin?\"))  # MUTANT G357\n")],
             ["PlayLoopTests.test_r5_the_frame_budget_cuts_the_decisions_pause_too"]),
    "G358": (CAUGHT, "the settle fights on past MAX_LOSSES (its count's stop not heard: the review's R5-F5)",
             [(MODE, "                if lost is not None:\n                    stop = lost\n                    break\n",
               "                pass  # MUTANT G358\n")],
             ["PlayLoopTests.test_r5_the_last_allowed_loss_inside_the_settle_ends_it"]),
    "G359": (CAUGHT, "the milestones the settle's screens passed are not read (the review's R5-F6)",
             [(MODE, "        passed = between(first, look) if between is not None else []\n",
               "        passed = []  # MUTANT G359\n")],
             ["PlayLoopTests.test_r5_the_settle_names_the_milestones_its_screens_passed"]),
    "G360": (CAUGHT, "the end record reads the hands' LAST look, not a fresh one (the sweep's S37)",
             [(MODE, "        seen = hands.look()\n        free = nav_free(seen)\n",
               "        seen = hands.last  # MUTANT G360\n        free = nav_free(seen)\n")],
             ["PlayLoopTests.test_r5_a_stuck_end_reads_the_screen_as_it_is_at_the_end"]),
    "G361": (CAUGHT, "the end record is read AFTER the wait and push watchers close (the sweep's S56: R5's order unpinned)",
             [(MODE, "        screen = report[\"end_screen\"] = self._end_screen(hands, report, kind)\n"
                     "        # the losses are the LOOP's count (`_count_losses`, at the top of every pass and, since R5, after "
                     "each screen the\n"
                     "        # settle before \"done\" plays out), never recounted here: every way out of the loop leaves it "
                     "after that count, with\n"
                     "        # no battle in between, so a recount could only HIDE a loop that stopped counting (the step-5 "
                     "verifier's round 2:\n"
                     "        # with the loop's call removed, this recount made the sweep's \"the AI's battles lost == the "
                     "game's\" pass 40 of 40).\n"
                     "        # A disagreement is told, not mended.\n"
                     # (R1, build stage 4) re-anchored: the count adds a continue's restored losses (T5); the same move
                     "        logged = report.get(\"restored_losses\", 0) + battles_lost(runner.nav.battle_log)\n"
                     "        if logged != report[\"losses\"]:\n"
                     "            hands.tell(f\"the loop counted {report['losses']} battles lost, but the battle log holds "
                     "{logged}\")\n"
                     "        waits = getattr(self, \"_waits\", None)\n"
                     "        if waits is not None:\n"
                     "            waits.finish()\n"
                     "            report[\"waits\"] = waits.summary()\n"
                     "        pushes = getattr(self, \"_pushes\", None)\n"
                     "        if pushes is not None:\n"
                     "            # (build step 5.2) the longest free stretch of presses that brought nothing new\n"
                     "            pushes.wind_up()\n"
                     "            report[\"pushes\"] = pushes.push_report()\n",
               "        logged = report.get(\"restored_losses\", 0) + battles_lost(runner.nav.battle_log)\n"
               "        if logged != report[\"losses\"]:\n"
               "            hands.tell(f\"the loop counted {report['losses']} battles lost, but the battle log holds {logged}\")\n"
               "        waits = getattr(self, \"_waits\", None)\n"
               "        if waits is not None:\n"
               "            waits.finish()\n"
               "            report[\"waits\"] = waits.summary()\n"
               "        pushes = getattr(self, \"_pushes\", None)\n"
               "        if pushes is not None:\n"
               "            pushes.wind_up()\n"
               "            report[\"pushes\"] = pushes.push_report()\n"
               "        screen = report[\"end_screen\"] = self._end_screen(hands, report, kind)  # MUTANT G361\n")],
             ["PlayLoopTests.test_r5_the_end_look_closes_the_wait_record"]),
    "G362": (CAUGHT, "the settle's record of its frames is always 0 (the sweep's S26)",
             [(MODE, "\"frames\": hands.pad.frames - began, \"stop\": stop,", "\"frames\": 0, \"stop\": stop,")],
             ["PlayLoopTests.test_r5_done_plays_out_the_screen_first",
              "PlayLoopTests.test_r5_done_on_a_free_screen_plays_nothing_out"]),
    "G363": (CAUGHT, "the settle's record always says the screen freed (the sweep's S27)",
             [(MODE, "\"free\": free, \"budget\": cut,", "\"free\": True, \"budget\": cut,")],
             ["PlayLoopTests.test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so"]),
    "G364": (CAUGHT, "what holds the screen is not said when it did not free (`busy_reason` not read: the sweep's S35)",
             [(MODE, "            held = busy_reason(look)\n"
                     "            hands.tell(f\"[AI-GOALS] {target} reached, but the screen did not free",
               "            held = None  # MUTANT G364\n"
               "            hands.tell(f\"[AI-GOALS] {target} reached, but the screen did not free")],
             ["PlayLoopTests.test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so"]),
    "G365": (CAUGHT, "the end record has no frame (the sweep's S40)",
             [(MODE, "\"frame\": seen.frame}", "\"frame\": None}")],
             ["PlayLoopTests.test_r5_the_end_record_carries_the_end_frame",
              "PlayLoopTests.test_r5_the_end_look_closes_the_wait_record"]),
    "G366": (CAUGHT, "the end record has no settle frames (the sweep's S45)",
             [(MODE, "settle_frames=settle.get(\"frames\", 0)", "settle_frames=0")],
             ["PlayLoopTests.test_r5_done_plays_out_the_screen_first"]),
    "G367": (CAUGHT, "the end record has no pause (the sweep's S46)",
             [(MODE, "paused=settle.get(\"paused\", 0)", "paused=0")],
             ["PlayLoopTests.test_r5_done_on_a_free_screen_plays_nothing_out"]),
    "G368": (CAUGHT, "the \"end_screen\" note of a screen that did not free has no target, frame or play-outs (the sweep's "
                     "S53)",
             [(MODE, "\"not free\", held, {\"target\": target, \"stop\": stop, \"frame\": look.frame,\n"
                     "                                                        \"played\": played})",
               "\"not free\", held, {\"stop\": stop})  # MUTANT G368")],
             ["PlayLoopTests.test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so"]),
    "G369": (CAUGHT, "an unsettled end with no play-out stop says \"(None)\" (the told line's own words dropped: the sweep's "
                     "S54)",
             [(MODE, "{stop or 'a scene still plays'}", "{stop}")],
             ["PlayLoopTests.test_r5_the_settle_is_bounded"]),
    "G370": (CAUGHT, "the end LINE says NOT free without what holds the screen (the sweep's S55)",
             [(MODE, "'NOT free (' + str(screen.get('held_by')) + ')'", "'NOT free'")],
             ["PlayLoopTests.test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so"]),
    "G371": (CAUGHT, "the frame budget's cut of the settle is not SAID (its tell and note deleted: R5-F1)",
             [(MODE, "            hands.tell(f\"[AI-GOALS] {target} reached, but the run's frame budget ran out",
               "            (f\"[AI-GOALS] {target} reached, but the run's frame budget ran out"),
              (MODE, "            hands.note(\"end_screen\", \"budget\", held or \"free\", {",
               "            (\"end_screen\", \"budget\", held or \"free\", {")],
             ["PlayLoopTests.test_r5_the_frame_budget_never_cuts_a_reached_target_short_of_its_end",
              "PlayLoopTests.test_r5_the_frame_budget_cuts_the_decisions_pause_too"]),
    "G372": (CAUGHT, "the milestones the settle's screens passed are not told (the tell deleted: R5-F6)",
             [(MODE, "            hands.tell(f\"[AI-GOALS] what was on screen after {target} took the story further",
               "            (f\"[AI-GOALS] what was on screen after {target} took the story further")],
             ["PlayLoopTests.test_r5_the_settle_names_the_milestones_its_screens_passed"]),
    "G373": (CAUGHT, "the play loop gives the settle no reader of the story's milestones (`_passed_between` not set: R5-F6)",
             [(MODE, "        self._passed_between = lambda first, then: [m.id for m in story.milestones[max(current(first), "
                     "0):current(then)]]\n",
               "        pass  # MUTANT G373\n")],
             ["PlayLoopTests.test_r5_the_settle_names_the_milestones_its_screens_passed"]),
    # found by the round's development sweep step52dev2
    "G229": (CAUGHT, "a goal starts from the LAST intent's walls (seed 1010: PROF. BIRCH's walls kept into the rival's milestone)",
             [(GOALS, "            nav.scene_walls = {key: set(tiles) for key, tiles in nav.carried_scene_walls.items()}\n",
               "            pass  # MUTANT G229\n")],
             ["ProductiveWiringTests.test_a_goal_starts_from_its_milestones_walls_not_the_last_intents"]),
    "G230": (CAUGHT, "the beeline control picks up no item ball (step52dev2's beeline stuck in 12 of 12)",
             [(GOALS, "        items = self.memory.curious_row < CURIOUS_ROW_MAX\n", "        items = self.curious_ok()  # MUTANT G230\n")],
             ["ProductiveWiringTests.test_the_beeline_still_picks_up_an_item_ball"]),
    "G231": (CAUGHT, "a place a scene turned a look round back from is not blocked for curiosity (call deleted)",
             [(GOALS, "                    self._blocked(milestone, key, tuple(tile), why)\n",
               "                    pass  # MUTANT G231\n")],
             ["ProductiveTests.test_a_place_a_scene_turned_a_look_round_back_from_is_blocked_for_curiosity"]),
    "G232": (CAUGHT, "a detour may choose the tile beside a blocked place (the same corner)",
             [(GOALS, "    return any(abs(tile[0] - x) <= BESIDE and abs(tile[1] - y) <= BESIDE for x, y in places)\n",
               "    return tuple(tile) in set(places)  # MUTANT G232\n")],
             ["ProductiveTests.test_a_detour_never_chooses_a_place_beside_a_blocked_one"]),
    # (re-made after step52dev3: 5.2's first version gave the place up in `detour_choose`, which the navigator does not
    # call after a scene, so both of dev3's such detours met the scene twice; the detour's DONE now asks)
    "G233": (CAUGHT, "a detour walks on after a scene stopped the way to its place (`detour_turned_back`'s call deleted)",
             [(GOALS, "                        lambda look: bool(reached) or nav.world.current != began_on or detour_turned_back(look),\n",
               "                        lambda look: bool(reached) or nav.world.current != began_on,  # MUTANT G233\n")],
             ["ProductiveTests.test_a_detour_ends_at_the_first_scene_on_the_way"]),
    "G234": (CAUGHT, "a detour's reach ignores the tiles a scene sent the player back from",
             [(GOALS, "            walled = getattr(navigator, \"scene_walls\", None) or {}\n",
               "            walled = {}  # MUTANT G234\n")],
             ["ProductiveTests.test_a_detour_reaches_round_the_tiles_a_scene_sent_it_back_from"]),
    "G235": (CAUGHT, "a detour may choose the tile beside a place it tried in this detour (`_beside`'s call deleted)",
             [(GOALS, "                     and not _beside(t.tile, [old.tile for old in chosen])\n",
               "                     and all(t.tile != old.tile for old in chosen)  # MUTANT G235\n")],
             ["ProductiveTests.test_a_detour_swaps_a_place_it_cannot_reach_for_another_corner"]),
    "G236": (CAUGHT, "a look round or a detour is productive by 8 tiles whatever its length (the AI's rate rule removed)",
             [(GOALS, "                                                 or made[\"tiles\"] * 1000 >= YIELD_TILE_RATE * walking)\n",
               "                                                 or True)  # MUTANT G236\n")],
             ["ProductiveTests.test_a_look_round_is_worth_only_what_it_showed_for_its_time"]),
    "G237": (CAUGHT, "the play loop hands the yield no frames (`goal_yield` called without the goal's length)",
             [(MODE, "            made = goal_yield(goal, before, yield_snapshot(after, world, runner, battle_clock.battle_frames), outcome,\n"
                     "                              hands.pad.frames - began)\n",
               "            made = goal_yield(goal, before, yield_snapshot(after, world, runner, battle_clock.battle_frames), "
               "outcome)  # MUTANT G237\n")],
             ["ProductiveWiringTests.test_the_play_loop_judges_a_look_round_by_its_length"]),
    "G238": (CAUGHT, "the grader's game yield counts a look round by 8 tiles whatever its length",
             [(RATE5, "    seen = tiles >= YIELD_TILES and (kind not in SEEING or tiles * 1000 >= YIELD_TILE_RATE * walking)\n",
               "    seen = tiles >= YIELD_TILES  # MUTANT G238\n")],
             ["GraderYieldTests.test_the_game_judges_a_look_round_by_its_length"]),
    "G239": (CAUGHT, "the grader hands the game yield no kind (every span judged as a chat would be)",
             [(RATE5, "        game = game_yield(places, story, start, stop, span[\"kind\"])\n",
               "        game = game_yield(places, story, start, stop)  # MUTANT G239\n")],
             ["GraderYieldTests.test_the_game_judges_a_look_round_by_its_length"]),
    "G240": (CAUGHT, "the navigator keeps no record of the places a scene made it give up",
             [(NAV, "            self.scene_given_up.append((key.split(\"|\", 1)[0], target.tile, why))\n",
               "            pass  # MUTANT G240\n")],
             ["ProductiveTests.test_the_navigator_keeps_the_places_a_scene_made_it_give_up"]),
    "G241": (CAUGHT, "the battle clock misses a battle's opening and closing phases (only `in_battle` read)",
             [(WAITING, "        if look.screen.in_battle or look.screen.game_state in BATTLE_STATES:\n",
               "        if look.screen.in_battle:  # MUTANT G241\n")],
             ["ProductiveTests.test_the_battle_clock_counts_the_frames_a_battle_was_on_screen"]),
    "G242": (CAUGHT, "the battle clock counts across a look out of a battle (never reset)",
             [(WAITING, "        else:\n            self._at = None\n", "        else:\n            pass  # MUTANT G242\n")],
             ["ProductiveTests.test_the_battle_clock_counts_the_frames_a_battle_was_on_screen"]),
    "G243": (CAUGHT, "a look round's own time counts the battles met in it",
             [(GOALS, "    walking = max(0, frames - made.get(\"battle_frames\", 0))\n",
               "    walking = max(0, frames)  # MUTANT G243\n")],
             ["ProductiveTests.test_a_look_round_is_worth_only_what_it_showed_for_its_time"]),
    "G244": (CAUGHT, "the play loop's before-snapshot is handed no battle clock (its reading deleted)",
             [(MODE, "            before = yield_snapshot(seen, world, runner, battle_clock.battle_frames)\n",
               "            before = yield_snapshot(seen, world, runner)  # MUTANT G244\n")],
             ["ProductiveWiringTests.test_the_play_loop_takes_the_battles_out_of_a_look_rounds_time"]),
    "G245": (CAUGHT, "the play loop's after-snapshot is handed no battle clock (its reading deleted)",
             [(MODE, "            made = goal_yield(goal, before, yield_snapshot(after, world, runner, battle_clock.battle_frames), outcome,\n",
               "            made = goal_yield(goal, before, yield_snapshot(after, world, runner), outcome,  # MUTANT G245\n")],
             ["ProductiveWiringTests.test_the_play_loop_takes_the_battles_out_of_a_look_rounds_time"]),
    "G246": (CAUGHT, "the play brain makes no battle clock (`BattleClock`'s call deleted: one that counts nothing)",
             [(MODE, "        battle_clock = BattleClock()\n",
               "        battle_clock = type(\"NoClock\", (), {\"battle_frames\": 0, \"__call__\": lambda self, look: None})()"
               "  # MUTANT G246\n")],
             ["ProductiveWiringTests.test_the_play_loop_takes_the_battles_out_of_a_look_rounds_time"]),
    "G247": (CAUGHT, "the battle clock is never told a look (its watcher's install deleted)",
             [(MODE, "        hands.watchers.append(battle_clock)\n", "        pass  # MUTANT G247\n")],
             ["ProductiveWiringTests.test_the_play_loop_installs_its_battle_clock"]),
    "G248": (CAUGHT, "the game's yield counts the battles inside a look round's span as its time",
             [(RATE5, "    walking = max(0, end - start - battle)\n", "    walking = max(0, end - start)  # MUTANT G248\n")],
             ["GraderYieldTests.test_the_game_judges_a_look_round_by_its_length"]),
    "G249": (CAUGHT, "the game's second path records no battles",
             [(PLAY, "                self.battles.append(self._battle)\n", "                pass  # MUTANT G249\n")],
             ["GraderYieldTests.test_the_game_side_recorder_of_places"]),
    "G250": (CAUGHT, "the sweep grades the yield of ALL curiosity, chats and catches diluting the looks' (step52dev2)",
             [(RATE5, "        seeing = sum(r[\"seeing_frames\"] for r in runs)\n        made = sum(r[\"seeing_productive\"] for r in runs)\n",
               "        seeing = sum(r[\"curious_frames\"] for r in runs)  # MUTANT G250\n"
               "        made = sum(r[\"productive_frames\"] for r in runs)\n")],
             ["GraderYieldTests.test_the_step52_verdicts_and_their_controls"]),
    "G261": (CAUGHT, "a catching roam never gives a fruitless hunt up (`hunt_fruitless`'s call deleted)",
             [(GOALS, "                                      else hunt_fruitless(look) if hunt else None)\n",
               "                                      else None)  # MUTANT G261\n")],
             ["ProductiveTests.test_a_catching_roam_gives_the_hunt_up_after_fruitless_battles"]),
    "G262": (CAUGHT, "a species first seen does not start the hunt's count again",
             [(GOALS, "                since[\"dex\"], since[\"battles\"] = dex, len(nav.battle_log)\n",
               "                since[\"dex\"] = dex  # MUTANT G262\n")],
             ["ProductiveTests.test_a_catching_roam_gives_the_hunt_up_after_fruitless_battles"]),
    "G263": (CAUGHT, "a catch goal's roam is never handed the hunt rule (as a training roam)",
             [(GOALS, "            self.roam_hooks(hunt=goal.kind == \"catch\")\n", "            self.roam_hooks()  # MUTANT G263\n")],
             ["ProductiveTests.test_a_catch_goal_asks_the_hunt_rule_and_training_does_not"]),
    "G265": (CAUGHT, "a training or catching roam is handed no hooks at all (`roam_hooks`'s call deleted)",
             [(GOALS, "            self.roam_hooks(hunt=goal.kind == \"catch\")\n", "            pass  # MUTANT G265\n")],
             ["ProductiveTests.test_a_catch_goal_asks_the_hunt_rule_and_training_does_not"]),
    # G266 and G267 RETIRED (build step 5.3, A1-4; `LESSONS.md` PF-14): both broke `p2_reported`, the function that forced
    # the 5.2 shares of frames to PASS by their text, and it is gone. A share is now a REPORTED check by KIND
    # (`grader_checks.CHECKS`), never counted, and its old bound's verdict is printed by `grader_checks.verdict_row`. A
    # deletion of that path's calls is caught by `test_step53_a1.py` (test_the_evidence_lines,
    # test_the_sweeps_verdict_is_the_typed_rule) and SecondRoundTests.test_the_shares_of_frames_are_reported_not_graded.
    # (found by the pushing property, step52dev6, seed 1049: a walk to grass seen past OLDALE's edge flip-flopped across
    # ROUTE 101 and LITTLEROOT for 3,313 frames)
    "G268": (CAUGHT, "a walk to a tile walks on after it left the tile's map (`left_the_map`'s call deleted)",
             [(NAV, "                        lambda look: bool(reached) or left_the_map(look), lambda target: reached.append(True))\n",
               "                        lambda look: bool(reached), lambda target: reached.append(True))  # MUTANT G268\n")],
             ["ProductiveTests.test_a_walk_to_a_tile_ends_when_it_leaves_the_map"]),
    "G269": (CAUGHT, "a walk that left its map says nothing of it (the run's own outcome returned)",
             [(NAV, "        if not reached and began[0] is not None and self.world.current != began[0]:\n"
                    "            return f\"left the map: {self.world.names().get(began[0], began[0])} for {self._map_name()} "
                    "({outcome})\"\n",
               "        pass  # MUTANT G269\n")],
             ["ProductiveTests.test_a_walk_to_a_tile_ends_when_it_leaves_the_map"]),
    "G270": (CAUGHT, "a roam whose walk to grass crossed onto the next map gives up (no walk to that map's own grass)",
             [(ROAM, "        if not outcome.startswith(\"left the map\") or attempt:\n",
               "        if True:  # MUTANT G270\n")],
             ["ProductiveTests.test_a_roam_walks_on_to_the_grass_of_the_map_it_crossed_onto"]),
    # (found by the pushing property, step52dev4, chapter-2 seed 1026: 3,372 frames of crossing OLDALE's top edge)
    "G272": (CAUGHT, "a tile of this map is planned to through the next map's tiles past a crossed edge",
             [(NAV, "            walls = walls | frozenset(xy for xy in memory.tiles if memory.outside(xy))\n",
               "            pass  # MUTANT G272\n")],
             ["ProductiveTests.test_a_tile_of_this_map_is_walked_to_over_tiles_of_this_map"]),
    "G273": (CAUGHT, "a road past the edge is walled off too (the outside walled whatever the target)",
             [(NAV, "        if memory.edges and not memory.outside(target.tile):\n            walls = walls | frozenset(",
               "        if memory.edges:  # MUTANT G273\n            walls = walls | frozenset(")],
             ["ProductiveTests.test_a_tile_of_this_map_is_walked_to_over_tiles_of_this_map"]),
    # (found by the pushing property, step52dev6, the beeline's chapter 2 of seed 1050: ROUTE 103 and OLDALE crossed 186
    # times, 9,261 frames; with G272's fix alone 198 times, 10,683 frames: the explorer went back for a frontier it could
    # not reach)
    "G275": (CAUGHT, "a frontier no walk found a way to stays 'left to see' (`mark_unreached`'s call deleted)",
             [(NAV, "                    world.mark_unreached(world.current, target.tile)\n",
               "                    pass  # MUTANT G275\n")],
             ["ProductiveTests.test_a_frontier_it_found_no_way_to_is_not_left_to_see"]),
    "G276": (CAUGHT, "a map's promise counts the frontier no walk found a way to",
             [(WORLD, "        frontier = [xy for xy in memory.frontier() if gone.get(xy) != len(memory.tiles)]\n",
               "        frontier = memory.frontier()  # MUTANT G276\n")],
             ["ProductiveTests.test_a_frontier_it_found_no_way_to_is_not_left_to_see"]),
    "G274": (CAUGHT, "the navigator never plans a step (`_next_step`'s call deleted: every target unreachable)",
             [(NAV, "        direction = self._next_step(memory, here, target, walls)\n",
               "        direction = None  # MUTANT G274\n")],
             ["ProductiveTests.test_a_walk_to_a_tile_ends_when_it_leaves_the_map"]),
    "G271": (CAUGHT, "a training or catching goal never roams (`roam_train`'s call in the goal runner deleted)",
             [(GOALS, "                outcome = yield from roam_train(hands, nav, goal.steps, goal.reason)\n",
               "                outcome = \"roamed: MUTANT G271\"\n")],
             ["ProductiveTests.test_a_catch_goal_asks_the_hunt_rule_and_training_does_not"]),
    "G264": (CAUGHT, "the loafing counts the battles in a curiosity goal (`loafing_frames` by the span's frames)",
             [(RATE5, "    return sum(row[\"walking\"] for row in curious if not row[\"game\"])\n",
               "    return sum(row[\"frames\"] for row in curious if not row[\"game\"])  # MUTANT G264\n")],
             ["GraderYieldTests.test_loafing_is_the_own_time_of_curiosity_that_brought_nothing"]),
    "G251": (CAUGHT, "the same corner is one tile round, not `BESIDE` 2 (step52dev3's (5, -4) after (3, -3))",
             [(GOALS, "BESIDE = 2\n", "BESIDE = 1  # MUTANT G251\n")],
             ["ProductiveTests.test_a_detour_never_chooses_a_place_beside_a_blocked_one"]),
    "G252": (CAUGHT, "a detour a scene ended does not say so (its outcome the navigator's 'done')",
             [(GOALS, "                   else \"a scene stopped the way there\" if turned else outcome)\n",
               "                   else outcome)  # MUTANT G252\n")],
             ["ProductiveTests.test_a_detour_ends_at_the_first_scene_on_the_way"]),
    # (step52dev3: the Trainer's chapter 2, seed 1017, a walk of 25,408 frames and 17 battles with no decision between)
    "G253": (CAUGHT, "a battle on a walk is never a moment to stop (`walk_battle_break`'s call deleted)",
             [(GOALS, "                if goal.kind == \"go\" and stop_new and walk_battle_break(look):\n                    return True\n",
               "                pass  # MUTANT G253\n")],
             ["SecondRoundTests.test_a_walk_may_stop_for_a_break_after_a_battle"]),
    "G254": (CAUGHT, "the battle break's draw is thrown again at every look (no once per battle)",
             [(GOALS, "                battles_at[0] = count\n", "                pass  # MUTANT G254\n")],
             ["SecondRoundTests.test_a_walk_may_stop_for_a_break_after_a_battle"]),
    "G255": (CAUGHT, "the battle break ignores boredom (its odds the cap at once)",
             [(GOALS, "                if draw >= CURIOUS_ODDS_CAP * bored:\n                    return False\n                arrived.append(f\"{BREAK_STOP}: after a battle",
               "                if draw >= CURIOUS_ODDS_CAP:  # MUTANT G255\n                    return False\n                arrived.append(f\"{BREAK_STOP}: after a battle")],
             ["SecondRoundTests.test_a_walk_may_stop_for_a_break_after_a_battle"]),
    "G256": (CAUGHT, "the battle break never asks the row cap (`curious_ok`'s call deleted there)",
             [(GOALS, "                if manager.hurt(look) or not manager.curious_ok():\n                    return False\n                bored, since",
               "                if manager.hurt(look):  # MUTANT G256\n                    return False\n                bored, since")],
             ["SecondRoundTests.test_a_walk_may_stop_for_a_break_after_a_battle"]),
    "G257": (CAUGHT, "the battle break never asks boredom (`boredom`'s call deleted there)",
             [(GOALS, "                bored, since = manager.boredom(look.frame)\n                draw = manager.rng.random()\n"
                      "                if draw >= CURIOUS_ODDS_CAP * bored:\n",
               "                bored, since = 1.0, 0  # MUTANT G257\n                draw = manager.rng.random()\n"
               "                if draw >= CURIOUS_ODDS_CAP * bored:\n")],
             ["SecondRoundTests.test_a_walk_may_stop_for_a_break_after_a_battle"]),
    # (step52dev3: the BLOCKED control pushed for 136,370-244,940 free frames by the game, 0-1,758 by the AI's record)
    "G258": (CAUGHT, "an open pushing stretch is never told (`_tell_open`'s call deleted: a run cut off loses it)",
             [(WAITING, "            self.current[\"last\"] = look.frame\n            self._tell_open()\n",
               "            self.current[\"last\"] = look.frame  # MUTANT G258\n")],
             ["ProductiveTests.test_the_push_watch_tells_a_stretch_that_is_still_going_on"]),
    "G259": (CAUGHT, "an open stretch is told at every look past PUSH_NOTE (what was told never kept)",
             [(WAITING, "        stretch[\"told\"] = stretch[\"frames\"]\n", "        pass  # MUTANT G259\n")],
             ["ProductiveTests.test_the_push_watch_tells_a_stretch_that_is_still_going_on"]),
    "G260": (CAUGHT, "the arrival share counts a detour that chose no place as one that did not arrive",
             [(RATE5, "        placed = [d for d in detours if d[3]]\n", "        placed = list(detours)  # MUTANT G260\n")],
             ["GraderYieldTests.test_the_step52_verdicts_and_their_controls"]),
    # ---- (build step 5.2, THE VERIFIER'S ROUND, 2026-10-15) its two failures: the NOHINTS pushing (a ping-pong through
    # OLDALE's house door goal after goal) and loafing credited as a talk (the nurse re-healing a full party); every new
    # hook's CALL deleted too (the census, G3)
    "G277": (CAUGHT, "a warp's ping-pong is not kept past its intent (`_remember_pingpong`'s call deleted)",
             [(NAV, "                    self._remember_pingpong(name)\n", "                    pass  # MUTANT G277\n")],
             ["VerifierRound52Tests.test_a_ping_pong_is_kept_past_its_intent"]),
    "G278": (CAUGHT, "the navigator never marks what its reach shows no way to (`cut_off`'s call deleted)",
             [(NAV, "                self.cut_off(look)\n", "                pass  # MUTANT G278\n")],
             ["VerifierRound52Tests.test_the_navigator_marks_what_it_cannot_get_to_before_it_chooses"]),
    "G279": (CAUGHT, "a frontier stood on whose unseen side stays unseen is kept (`_seen_out`'s call deleted)",
             [(NAV, "                self._seen_out(target, result)\n", "                pass  # MUTANT G279\n")],
             ["VerifierRound52Tests.test_a_frontier_stood_on_whose_unseen_side_stays_unseen_is_given_up"]),
    "G280": (CAUGHT, "what the reach shows no way to is computed and never marked (`mark_cut_off`'s call deleted)",
             [(NAV, "        self.world.mark_cut_off(memory.key, cut)\n", "        pass  # MUTANT G280\n")],
             ["VerifierRound52Tests.test_what_its_reach_shows_no_way_to_is_not_left_to_see",
              "VerifierRound52Tests.test_the_navigator_marks_what_it_cannot_get_to_before_it_chooses"]),
    "G281": (CAUGHT, "a frontier stood on is given up for the intent but stays 'left to see' (`mark_unreached`'s call deleted)",
             [(NAV, "            self.world.mark_unreached(memory.key, target.tile)\n", "            pass  # MUTANT G281\n")],
             ["VerifierRound52Tests.test_a_frontier_stood_on_whose_unseen_side_stays_unseen_is_given_up"]),
    "G282": (CAUGHT, "a kept ping-pong never compared with what has been seen since (`stamp`'s call in ponged_now deleted)",
             [(NAV, "        return self.ponged.get(f\"{self.world.current}|{target.exit[0]},{target.exit[1]}\") == self.world.stamp()\n",
               "        return self.ponged.get(f\"{self.world.current}|{target.exit[0]},{target.exit[1]}\") == None  # MUTANT G282\n")],
             ["VerifierRound52Tests.test_a_ping_pong_is_kept_past_its_intent"]),
    "G283": (CAUGHT, "a ping-pong kept with no record of what had been seen (`stamp`'s call in _remember_pingpong deleted)",
             [(NAV, "            self.ponged[name] = self.world.stamp()\n", "            self.ponged[name] = ()  # MUTANT G283\n")],
             ["VerifierRound52Tests.test_a_ping_pong_is_kept_past_its_intent"]),
    "G284": (CAUGHT, "out of ideas never matched with what has been seen since (`stamp`'s call in next_goal deleted)",
             [(GOALS, "                and self.memory.lost_end == (milestone.id, world.stamp())):\n",
               "                and self.memory.lost_end == (milestone.id, None)):  # MUTANT G284\n")],
             ["VerifierRound52Tests.test_out_of_ideas_gives_the_run_up"]),
    "G285": (CAUGHT, "out of ideas remembered with no record of what had been seen (`stamp`'s call in _out_of_ideas deleted)",
             [(GOALS, "        self.manager.memory.lost_end = (milestone.id, self.nav.world.stamp())\n",
               "        self.manager.memory.lost_end = (milestone.id, None)  # MUTANT G285\n")],
             ["VerifierRound52Tests.test_a_walk_with_no_lead_uses_the_lost_walk"]),
    "G286": (CAUGHT, "a lost walk never asks where something is left (`left_anywhere`'s call deleted: always out of ideas)",
             [(GOALS, "    left = [(key, n) for key, n in nav.world.left_anywhere() if key != nav.world.current]\n",
               "    left = []  # MUTANT G286\n")],
             ["VerifierRound52Tests.test_a_walk_with_no_lead_heads_for_what_is_left_and_else_is_out_of_ideas"]),
    "G287": (CAUGHT, "a lost walk never looks for the way to what is left (`lost_way`'s call deleted)",
             [(GOALS, "            way, left = lost_way(nav, look, weights, moving)\n",
               "            way, left = None, []  # MUTANT G287\n")],
             ["VerifierRound52Tests.test_a_walk_with_no_lead_heads_for_what_is_left_and_else_is_out_of_ideas"]),
    "G288": (CAUGHT, "a lost walk takes any place as worth going to (`worth_going`'s call deleted: the seen-all wander)",
             [(GOALS, "        if located is not None and not any(worth_going(t) for t in found):\n",
               "        if located is not None and not any(True for t in found):  # MUTANT G288\n")],
             ["VerifierRound52Tests.test_a_walk_with_no_lead_heads_for_what_is_left_and_else_is_out_of_ideas"]),
    "G289": (CAUGHT, "a lost walk goes back through a ping-pong's door (`ponged_now`'s call deleted)",
             [(GOALS, "        found = [t for t in found if not nav.ponged_now(t)] or found\n",
               "        found = found  # MUTANT G289\n")],
             ["VerifierRound52Tests.test_a_lost_walk_never_goes_back_through_a_ping_pong_door_unless_it_is_the_only_way"]),
    "G290": (CAUGHT, "a walk with no lead is the old walk (`lost_intent`'s call, with its out-of-ideas word, deleted)",
             [(GOALS, "                          else lost_intent(manager.state.active, budget, walk_done,\n"
                      "                                           lambda why: self._out_of_ideas(milestone, why, lost_why))\n"
                      "                          if goal.kind in (\"go\", \"look_around\") and goal.key.startswith(LOST_KEYS)\n",
               "")],
             ["VerifierRound52Tests.test_a_walk_with_no_lead_uses_the_lost_walk"]),
    "G291": (CAUGHT, "the lost walk chooses nothing (its own choice and carry-on handed to no intent)",
             [(GOALS, "    return Intent(\"look around\", budget, lost_choose, done, carry_on=lost_carry)\n",
               "    return Intent(\"look around\", budget, lambda nav, look: None, done)  # MUTANT G291\n")],
             ["VerifierRound52Tests.test_a_walk_with_no_lead_heads_for_what_is_left_and_else_is_out_of_ideas",
              "VerifierRound52Tests.test_a_lost_walk_never_goes_back_through_a_ping_pong_door_unless_it_is_the_only_way"]),
    "G292": (CAUGHT, "the goal manager watches no look (`notice`'s install deleted: nobody ever spoke)",
             [(MODE, "        hands.watchers.append(manager.notice)\n", "        pass  # MUTANT G292\n")],
             ["VerifierRound52Tests.test_the_play_brain_turns_the_new_rules_on"]),
    "G293": (CAUGHT, "whom it met is never written with the world memory",
             [(WORLD, "            out[\"spoke\"] = sorted(self.spoke)\n", "            pass  # MUTANT G293\n")],
             ["VerifierRound52Tests.test_whom_it_met_is_kept_with_the_world_memory"]),
    "G294": (CAUGHT, "whom it met is never read back with the world memory (a later session forgets)",
             [(WORLD, "        world.spoke = {str(who) for who in data.get(\"spoke\") or []}  # (build step 5.2, the verifier's round)\n",
               "        pass  # MUTANT G294\n")],
             ["VerifierRound52Tests.test_whom_it_met_is_kept_with_the_world_memory"]),
    "G295": (CAUGHT, "a talk is a yield by its label, whatever it told (the verifier's 127 chats that heard nothing new)",
             [(GOALS, "    made[\"talked\"] = bool(talk and made.get(\"pages\"))\n", "    made[\"talked\"] = bool(talk)  # MUTANT G295\n")],
             ["ProductiveTests.test_a_curiosity_goal_counts_by_what_it_brought",
              "ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    "G296": (CAUGHT, "the chat chooser ignores who has spoken (the nurse chatted with right after the heal)",
             [(GOALS, "            if key in self.memory.spoke:\n", "            if False:  # MUTANT G296\n")],
             ["VerifierRound52Tests.test_someone_who_spoke_is_remembered_and_never_chatted_with"]),
    "G297": (CAUGHT, "nobody is ever remembered as having spoken",
             [(GOALS, "                    self.memory.spoke.add(f\"{key}|{seen.local_id}\")\n", "                    pass  # MUTANT G297\n")],
             ["VerifierRound52Tests.test_someone_who_spoke_is_remembered_and_never_chatted_with"]),
    "G298": (CAUGHT, "only someone face to face has spoken (the nurse and the clerk across their counter missed)",
             [(GOALS, "SPOKE_REACH = 2\n", "SPOKE_REACH = 1  # MUTANT G298\n")],
             ["VerifierRound52Tests.test_someone_who_spoke_is_remembered_and_never_chatted_with"]),
    "G299": (CAUGHT, "anyone near has spoken, not only the person straight ahead",
             [(GOALS, "                        and (seen.dx, seen.dy) in [(ahead[0] * n, ahead[1] * n) for n in range(1, SPOKE_REACH + 1)]):\n",
               "                        and abs(seen.dx) + abs(seen.dy) <= SPOKE_REACH):  # MUTANT G299\n")],
             ["VerifierRound52Tests.test_someone_who_spoke_is_remembered_and_never_chatted_with"]),
    "G300": (CAUGHT, "out of ideas never gives the run up (the NOHINTS runs' push until the patience)",
             [(GOALS, "        if (goal.key.startswith(LOST_KEYS) and self.memory.lost_end is not None\n",
               "        if (False and self.memory.lost_end is not None  # MUTANT G300\n")],
             ["VerifierRound52Tests.test_out_of_ideas_gives_the_run_up"]),
    "G301": (CAUGHT, "the play loop does not end a run given up (it pursues 'give_up' as a goal)",
             [(MODE, "            if goal.kind == \"give_up\":\n", "            if False:  # MUTANT G301\n")],
             ["VerifierRound52Tests.test_the_play_loop_ends_a_run_given_up"]),
    "G302": (CAUGHT, "the goal manager keeps whom it met in a set of its own (a later session forgets)",
             [(MODE, "        manager.memory.spoke = world.spoke\n", "        pass  # MUTANT G302\n")],
             ["VerifierRound52Tests.test_the_play_brain_turns_the_new_rules_on"]),
    "G303": (CAUGHT, "the play brain's navigator keeps no ping-pong past its intent (the earlier brains' rule)",
             [(MODE, "        nav.ponged = {}\n", "        pass  # MUTANT G303\n")],
             ["VerifierRound52Tests.test_the_play_brain_turns_the_new_rules_on"]),
    "G304": (CAUGHT, "the play brain's navigator marks nothing it cannot get to (the earlier brains' rule)",
             [(MODE, "        nav.mark_cut = True\n", "        pass  # MUTANT G304\n")],
             ["VerifierRound52Tests.test_the_play_brain_turns_the_new_rules_on"]),
    "G305": (CAUGHT, "a map's promise counts what the reach showed no way to (OLDALE_TOWN_HOUSE1's two tiles for ever)",
             [(WORLD, "            unused = [xy for xy in unused if xy not in cut]\n            frontier = [xy for xy in frontier if xy not in cut]\n",
               "            pass  # MUTANT G305\n")],
             ["VerifierRound52Tests.test_what_its_reach_shows_no_way_to_is_not_left_to_see"]),
    "G306": (CAUGHT, "someone standing in the way is a wall of what it can get to (a person in a gap cuts off all beyond)",
             [(NAV, "        reach = distances(memory, here, self.walls(memory, here) - memory.people_now, self.grass_cost)\n",
               "        reach = distances(memory, here, self.walls(memory, here), self.grass_cost)  # MUTANT G306\n")],
             ["VerifierRound52Tests.test_what_its_reach_shows_no_way_to_is_not_left_to_see"]),
    "G307": (CAUGHT, "a lost walk tries a frontier no walk found a way to again (seed 903: OLDALE's nine, 41 times each)",
             [(GOALS, "                 if keeps_going(world, t, None) and not (t.kind == \"frontier\" and gone.get(t.tile) == tiles)]\n",
               "                 if keeps_going(world, t, None)]  # MUTANT G307\n")],
             ["VerifierRound52Tests.test_a_walk_with_no_lead_heads_for_what_is_left_and_else_is_out_of_ideas"]),
    "G308": (CAUGHT, "a lost walk with only ping-pong doors left goes nowhere they lead (the 'only way left' dropped)",
             [(GOALS, "        found = [t for t in found if not nav.ponged_now(t)] or found\n",
               "        found = [t for t in found if not nav.ponged_now(t)]  # MUTANT G308\n")],
             ["VerifierRound52Tests.test_a_lost_walk_never_goes_back_through_a_ping_pong_door_unless_it_is_the_only_way"]),
    "G309": (CAUGHT, "the game's yield credits ANY text begun in a span as a talk (the verifier's weak proof)",
             [(RATE5, "    talked = any(start <= text[0] <= end_s and len(text) > 2 and bool(text[2]) for text in places.get(\"texts\") or ())\n",
               "    talked = any(start <= text[0] <= end_s for text in places.get(\"texts\") or ())  # MUTANT G309\n")],
             ["GraderYieldTests.test_the_game_says_what_a_span_brought"]),
    # (re-anchored in the verifier's second round, where the recorder went from whole messages to pages)
    "G310": (CAUGHT, "the game's second path calls every message new",
             [(PLAY, "                unseen = not pages or any(page not in self.pages for page in pages)\n",
               "                unseen = True  # MUTANT G310\n")],
             ["GraderYieldTests.test_the_game_side_recorder_of_places",
              "GraderYieldTests.test_a_talk_is_new_only_with_a_page_never_shown"]),
    "G311": (CAUGHT, "the game's second path forgets the pages of the run it goes on from (chapter 1's for chapter 2)",
             [(PLAY, "        self.pages: set[str] = set(pages or ())\n", "        self.pages: set[str] = set()  # MUTANT G311\n")],
             ["GraderYieldTests.test_the_game_side_recorder_of_places",
              "GraderYieldTests.test_a_talk_is_new_only_with_a_page_never_shown"]),
    # (the verifier's SECOND round: "PlaceRecorder compares WHOLE messages", so OLDALE's footprints man's talk, the last two
    # pages of his own scene, was a new message 20 times in the graded sweep; and the run's opening window was credited to
    # its first goal, seven truck chats of 16-44 frames)
    "G333": (CAUGHT, "the game's second path compares WHOLE messages again (the verifier's second round's FAILURE)",
             [(PLAY, "                unseen = not pages or any(page not in self.pages for page in pages)\n"
                     "                self.pages.update(pages or ())\n",
               "                unseen = not pages or \" \".join(pages) not in self.pages  # MUTANT G333\n"
               "                self.pages.update([\" \".join(pages)] if pages else ())\n")],
             ["GraderYieldTests.test_a_talk_is_new_only_with_a_page_never_shown"]),
    "G334": (CAUGHT, "a text is new only when EVERY page is new (one new page among old ones is no talk)",
             [(PLAY, "                unseen = not pages or any(page not in self.pages for page in pages)\n",
               "                unseen = not pages or all(page not in self.pages for page in pages)  # MUTANT G334\n")],
             ["GraderYieldTests.test_a_talk_is_new_only_with_a_page_never_shown"]),
    "G335": (CAUGHT, "the recorder never reads the message's pages (`shown_pages`'s call deleted)",
             [(PLAY, "                    pages = shown_pages()\n", "                    pages = None  # MUTANT G335\n")],
             ["GraderYieldTests.test_the_game_side_recorder_of_places",
              "GraderYieldTests.test_a_talk_is_new_only_with_a_page_never_shown"]),
    "G336": (CAUGHT, "the pages shown are never kept (every talk new for ever)",
             [(PLAY, "                self.pages.update(pages or ())\n", "                pass  # MUTANT G336\n")],
             ["GraderYieldTests.test_the_game_side_recorder_of_places",
              "GraderYieldTests.test_a_talk_is_new_only_with_a_page_never_shown"]),
    "G337": (CAUGHT, "the run's opening window is credited to its first goal (the truck chats)",
             [(PLAY, "                if self.opening is None:\n"
                     "                    # (the verifier's second round) the screen the run began on: seen, and no goal's yield\n"
                     "                    self.opening = len(fresh)\n"
                     "                elif fresh:\n",
               "                if fresh:  # MUTANT G337\n")],
             ["GraderYieldTests.test_the_game_side_recorder_of_places"]),
    "G338": (CAUGHT, "a scroll (0xFA, the box waits for a press) does not end a page",
             [(PLAY, "PAGE_BREAKS = (0xFA, 0xFB)\n", "PAGE_BREAKS = (0xFB,)  # MUTANT G338\n")],
             ["GraderYieldTests.test_a_message_is_cut_into_pages_where_the_box_waits_for_a_press"]),
    "G339": (CAUGHT, "a control code's argument byte is read as a break (`split_pages`'s skipping deleted)",
             [(PLAY, "        elif byte == CONTROL_CODE and at < len(data):\n", "        elif False:  # MUTANT G339\n")],
             ["GraderYieldTests.test_a_message_is_cut_into_pages_where_the_box_waits_for_a_press"]),
    "G340": (CAUGHT, "the buffer is read past the string's end (an older message's tail made a page)",
             [(PLAY, "        if byte == STRING_END:\n            break\n", "        if False:  # MUTANT G340\n            break\n")],
             ["GraderYieldTests.test_a_message_is_cut_into_pages_where_the_box_waits_for_a_press"]),
    # (the verifier's second round, its weak proof "NOHINTS 938's explore at f70318 is 0 tiles by the game, 50 by the AI":
    # a diagnostic replay measured the player walking while the framework's `is_waiting_for_input` said a text waited, a
    # finished script's leftover native pointer)
    "G341": (CAUGHT, "a finished script's leftover WaitForAorBPress pointer is a wait (the context's mode not asked)",
             [(PLAY, "    if mode == NATIVE_MODE and native == WAIT_NATIVE:\n", "    if native == WAIT_NATIVE:  # MUTANT G341\n")],
             ["GraderYieldTests.test_a_script_waits_only_while_it_runs_its_wait"]),
    "G342": (CAUGHT, "the places' second path reads a wait by the framework's read again (`text_waits_now`'s call deleted)",
             [(PLAY, "    waiting = text_waits_now()\n",
               "    waiting = bool(__import__(\"modules.tasks\", fromlist=[\"x\"]).is_waiting_for_input())  # MUTANT G342\n")],
             ["GraderYieldTests.test_both_recorders_read_a_wait_by_the_harness_s_own_rule"]),
    "G343": (CAUGHT, "the stall's second path reads a wait by the framework's read again (`text_waits_now`'s call deleted)",
             [(PLAY, "    return \"a text or script waits for A/B\" if text_waits_now() else None\n",
               "    return \"a text or script waits for A/B\" if __import__(\"modules.tasks\", fromlist=[\"x\"]).is_waiting_for_input() "
               "else None  # MUTANT G343\n")],
             ["GraderYieldTests.test_both_recorders_read_a_wait_by_the_harness_s_own_rule"]),
    # (the verifier's second round: "counted by both paths" was written of a talk whose two verdicts no line showed)
    "G345": (CAUGHT, "the game's word on a talk is taken from the AI's own record (the two paths made one)",
             [(RATE5, "\"talked_game\": bool(game[\"talked\"])}\n", "\"talked_game\": bool(mine.get(\"talked\"))}  # MUTANT G345\n")],
             ["GraderYieldTests.test_the_two_paths_on_the_talks_are_put_side_by_side"]),
    "G346": (CAUGHT, "the talks the two paths disagree on are never reported",
             [(RATE5, "    apart = [(r[\"plan\"], r[\"seed\"], *t) for r in real for t in r.get(\"talks_apart\") or ()]\n",
               "    apart = []  # MUTANT G346\n")],
             ["GraderYieldTests.test_the_two_paths_on_the_talks_are_put_side_by_side"]),
    "G344": (CAUGHT, "the harness's read never applies its own rule (`text_waits`'s call deleted)",
             [(PLAY, "    return text_waits(script.mode, script.native_function_name, (active, state))\n",
               "    return bool(__import__(\"modules.tasks\", fromlist=[\"x\"]).is_waiting_for_input())  # MUTANT G344\n")],
             ["GraderYieldTests.test_both_recorders_read_a_wait_by_the_harness_s_own_rule"]),
    "G312": (CAUGHT, "a frontier stood on is marked but not given up for the intent",
             [(NAV, "            self.exclude(target, \"arrived: the unseen beside it stayed unseen\")\n", "            pass  # MUTANT G312\n")],
             ["VerifierRound52Tests.test_a_frontier_stood_on_whose_unseen_side_stays_unseen_is_given_up"]),
    "G313": (CAUGHT, "a talk that told nothing new is not said (its goal reported as having brought nothing at all)",
             [(GOALS, "                            + ([\"a talk that told it nothing new\"] if made.get(\"talks\") and not made.get(\"talked\") else [])\n",
               "                            + []  # MUTANT G313\n")],
             ["ProductiveTests.test_the_play_loop_judges_a_curiosity_goal_by_its_yield"]),
    # (found by the round's first development sweep, step52vdev1: three of four chapter-1 runs gave up inside the moving
    # truck; seed 1201 gave up at the start of PROF. BIRCH's milestone over a road the milestone before had cut off)
    "G314": (CAUGHT, "the play loop never tells the navigator the story moved on (`story_moved`'s call deleted)",
             [(MODE, "                nav.story_moved()\n", "                pass  # MUTANT G314\n")],
             ["VerifierRound52Tests.test_the_story_moving_on_forgets_what_it_could_not_get_to"]),
    "G315": (CAUGHT, "the story moving on keeps the marks of what it could not get to (`forget_marks`'s call deleted)",
             [(NAV, "        marks = self.world.forget_marks()\n", "        marks = 0  # MUTANT G315\n")],
             ["VerifierRound52Tests.test_the_story_moving_on_forgets_what_it_could_not_get_to"]),
    "G316": (CAUGHT, "the story moving on keeps the ping-pongs",
             [(NAV, "            self.ponged.clear()\n", "            pass  # MUTANT G316\n")],
             ["VerifierRound52Tests.test_the_story_moving_on_forgets_what_it_could_not_get_to"]),
    # (found by the round's second development sweep, step52vdev2: CH1 seed 1209's look round after the footprints man's
    # first word, 2,003 frames toward his corner; and remembering every speaker had halved the chats with new words)
    "G318": (CAUGHT, "a scene that turned a curiosity walk back once blocks nothing (the goal runner's read deleted)",
             [(GOALS, "                for key, tile, why in given_up[given_from:] + turned[turned_from:]:\n",
               "                for key, tile, why in given_up[given_from:]:  # MUTANT G318\n")],
             ["VerifierRound52Tests.test_a_scene_that_turned_a_curiosity_walk_back_once_blocks_its_tile"]),
    "G327": (CAUGHT, "a scene that turned a STORY walk back is not blocked for curiosity (`blocked_on`'s call deleted)",
             [(GOALS, "                    self.manager.blocked_on(milestone.id, key)[tuple(tile)] = why\n",
               "                    pass  # MUTANT G327\n")],
             ["VerifierRound52Tests.test_a_scene_that_turned_a_curiosity_walk_back_once_blocks_its_tile"]),
    # (found by the round's fifth development sweep, step52vdev5: CH2 seed 1242, PETALBURG's guide met at a third tile)
    "G328": (CAUGHT, "'some more' counts what lies past the corner a scene blocked (`_scene_corners`'s call deleted there)",
             [(GOALS, "        blocked |= _scene_corners(self.blocked_on(milestone_id, world.current))  # (the verifier's round)\n",
               "        pass  # MUTANT G328\n")],
             ["VerifierRound52Tests.test_curiosity_keeps_out_of_the_corner_a_scene_turned_it_back_from"]),
    "G329": (CAUGHT, "a curiosity walk carries no corners (the walk round into the same scene)",
             [(GOALS, "                key: set(walls.get(key, set())) | set(blocked.get(key, {})) | corners.get(key, set())\n",
               "                key: set(walls.get(key, set())) | set(blocked.get(key, {}))  # MUTANT G329\n")],
             ["VerifierRound52Tests.test_curiosity_keeps_out_of_the_corner_a_scene_turned_it_back_from"]),
    "G332": (CAUGHT, "a curiosity walk's corners never computed (`_scene_corners`'s call in pursue deleted)",
             [(GOALS, "        corners = ({key: _scene_corners(places) - set((walls or {}).get(key, set())) for key, places in blocked.items()}\n",
               "        corners = ({key: set() for key, places in blocked.items()}  # MUTANT G332\n")],
             ["VerifierRound52Tests.test_curiosity_keeps_out_of_the_corner_a_scene_turned_it_back_from"]),
    "G330": (CAUGHT, "the corners join the story's own walls after a curiosity walk",
             [(GOALS, "                    walls[key] -= corners.get(key, set())\n", "                    pass  # MUTANT G330\n")],
             ["VerifierRound52Tests.test_curiosity_keeps_out_of_the_corner_a_scene_turned_it_back_from"]),
    "G331": (CAUGHT, "a corner round a place someone stood in the way of too (not only a scene's)",
             [(GOALS, "        if str(why).startswith(SCENE_BLOCKS):\n", "        if True:  # MUTANT G331\n")],
             ["VerifierRound52Tests.test_curiosity_keeps_out_of_the_corner_a_scene_turned_it_back_from"]),
    "G319": (CAUGHT, "the navigator keeps no record of where a scene turned the player back",
             [(NAV, "            self.scene_turned.append((scene_map, began, f\"a scene began here and turned it back (f{frame})\"))\n",
               "            pass  # MUTANT G319\n")],
             ["VerifierRound52Tests.test_a_scene_that_turned_a_curiosity_walk_back_once_blocks_its_tile"]),
    "G320": (CAUGHT, "every speaker is remembered, a scene's too (PROF. BIRCH's chats with new words lost)",
             [(GOALS, "        if (self.memory.hearing and screen.waits_for_button and screen.text and not screen.in_battle\n",
               "        if (screen.waits_for_button and screen.text and not screen.in_battle  # MUTANT G320\n")],
             ["VerifierRound52Tests.test_someone_who_spoke_is_remembered_and_never_chatted_with"]),
    "G321": (CAUGHT, "the goal runner never says a service talk or a chat is the goal (nobody is ever remembered)",
             [(GOALS, "        self.manager.memory.hearing = goal.kind in HEARD_KINDS\n", "        pass  # MUTANT G321\n")],
             ["VerifierRound52Tests.test_a_service_talk_or_a_chat_is_heard_and_other_goals_are_not"]),
    # (found by the round's third development sweep, step52vdev3: NOHINTS seed 1223, OLDALE <-> ROUTE 103 across the edge)
    "G322": (CAUGHT, "a map a lost walk found nothing worth going to on keeps its promise (`mark_spent`'s call deleted)",
             [(GOALS, "            world.mark_spent(world.current)\n", "            pass  # MUTANT G322\n")],
             ["VerifierRound52Tests.test_a_map_a_lost_walk_found_nothing_worth_going_to_on_is_spent"]),
    "G323": (CAUGHT, "a map's promise counts what a lost walk found it could not have (`spent` not asked)",
             [(WORLD, "        if self.spent.get(key) == len(memory.tiles):\n            return 0",
               "        if False:  # MUTANT G323\n            return 0")],
             ["VerifierRound52Tests.test_a_map_a_lost_walk_found_nothing_worth_going_to_on_is_spent"]),
    "G324": (CAUGHT, "the story moving on keeps the spent maps",
             [(WORLD, "        self.unreached, self.cut_off, self.spent = {}, {}, {}\n",
               "        self.unreached, self.cut_off = {}, {}  # MUTANT G324\n")],
             ["VerifierRound52Tests.test_a_map_a_lost_walk_found_nothing_worth_going_to_on_is_spent"]),
    # (found by the round's third development sweep, step52vdev3: CH2 seed 1220, a look round of ROUTE 102's grass that ran
    # its budget through 21 battles, 9 new tiles)
    "G325": (CAUGHT, "a look round never stops at the walk's own stops (`walk_done`'s call in look_saw_nothing deleted)",
             [(GOALS, "                    if walk_done(look):\n                        return True\n"
                      "                    now = (nav.world.tiles_learned",
               "                    pass  # MUTANT G325\n                    now = (nav.world.tiles_learned")],
             ["VerifierRound52Tests.test_a_look_round_is_over_when_it_has_seen_nothing_new_battles_or_not"]),
    "G326": (CAUGHT, "a look round goes on while its battles bring experience and nothing new is seen (5.2 part 2)",
             [(GOALS, "                    return look.frame - seen_clock[1] >= CURIOUS_NOVELTY\n",
               "                    return False  # MUTANT G326\n")],
             ["VerifierRound52Tests.test_a_look_round_is_over_when_it_has_seen_nothing_new_battles_or_not"]),
    "G317": (CAUGHT, "a player SHUT IN (no way out known: the moving truck) is out of ideas (`shut_in`'s call deleted)",
             [(GOALS, "            if not left and not shut_in(world):\n", "            if not left:  # MUTANT G317\n")],
             ["VerifierRound52Tests.test_a_walk_with_no_lead_heads_for_what_is_left_and_else_is_out_of_ideas"]),
    # (R1 + R2, build stage 4, build spec 2026-10-29 section 6: "loop-wiring mutants G374 and up, each deleting one new
    # call (PF-2), CAUGHT by the PlayLoopTests") the save goal, the end save, the continue branch, the restore, the restore
    # record, the end line, the lost line, the registry watcher, `_story_menu`'s save branches, and the guards around them
    "G374": (CAUGHT, "no save goal at block 1b (`_save_goal`'s call deleted)",
             [(GOALS, "        saving = None if hurt else self._save_goal(look, here_const, milestone)\n",
               "        saving = None  # MUTANT G374\n")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_big_moment", "PlayLoopTests.test_r1_no_save_goal_while_hurt"]),
    "G375": (CAUGHT, "a save goal while the party is hurt (block 1b's hurt guard deleted)",
             [(GOALS, "        saving = None if hurt else self._save_goal(look, here_const, milestone)\n",
               "        saving = self._save_goal(look, here_const, milestone)  # MUTANT G375\n")],
             ["PlayLoopTests.test_r1_no_save_goal_while_hurt"]),
    "G376": (CAUGHT, "no save right before the leader (block 8's `_leader_save` call deleted)",
             [(GOALS, "        leader = self._leader_save(look, world, milestone, step, goal)\n",
               "        leader = None  # MUTANT G376\n")],
             ["PlayLoopTests.test_r1_a_save_before_the_leader_takes_the_story_goals_place"]),
    "G377": (CAUGHT, "the goal runner never plays a save goal (its save branch deleted)",
             [(GOALS, "        if goal.kind == \"save\":\n            # (R1, build spec 2026-10-29 section 3 (d)) the save goal",
               "        if False:  # MUTANT G377\n            # (R1, build spec 2026-10-29 section 3 (d)) the save goal")],
             ["PlayLoopTests.test_r1_the_runner_plays_a_save_goal_through_its_saver"]),
    "G378": (CAUGHT, "no save before the game is put down (the end save's call deleted)",
             [(MODE, "                yield from self._save_before_done(hands, report)\n", "                pass  # MUTANT G378\n")],
             ["PlayLoopTests.test_r1_the_end_save_when_due"]),
    "G379": (CAUGHT, "a continue run plays a NEW game (the continue branch deleted)",
             [(MODE, "            if self._continuing:\n                return (yield from self._continue(hands, personality))\n",
               "            if False:  # MUTANT G379\n                return (yield from self._continue(hands, personality))\n")],
             ["R1PlayTests.test_r1_a_continue_restores_as_of_its_save_before_the_first_look",
              "R1PlayTests.test_r1_a_continue_that_stops_ends_stuck_with_a_chosen_end"]),
    "G380": (CAUGHT, "a continue plays on with a FRESH memory (the restore not handed to the play loop)",
             [(MODE, "        return (yield from self._play(hands, personality, restored=restored))\n",
               "        return (yield from self._play(hands, personality))  # MUTANT G380\n")],
             ["R1PlayTests.test_r1_a_continue_restores_as_of_its_save_before_the_first_look"]),
    "G381": (CAUGHT, "the goal manager's memory not restored (`restore_goals`'s call deleted)",
             [(MODE, "            manager.memory = restore_goals(manager.memory, restored.goals)",
               "            pass  # MUTANT G381")],
             ["PlayLoopTests.test_r1_the_loss_count_is_restored_and_each_loss_is_a_line"]),
    "G382": (CAUGHT, "the personality and the battle mind not restored (their calls deleted)",
             [(MODE, "            restore_personality(state, restored.personality)\n            restore_battle(mind, restored.battle)\n",
               "            pass  # MUTANT G382\n")],
             ["PlayLoopTests.test_r1_the_loss_count_is_restored_and_each_loss_is_a_line"]),
    "G383": (CAUGHT, "the battles lost before the save not restored (T5)",
             [(MODE, "            report[\"losses\"] = report[\"restored_losses\"] = restored.losses\n",
               "            pass  # MUTANT G383\n")],
             ["PlayLoopTests.test_r1_the_loss_count_is_restored_and_each_loss_is_a_line"]),
    "G384": (CAUGHT, "the restore record's session line not written (finding F2)",
             [(MODE, "        written = self._writer.write_session()\n", "        written = True  # MUTANT G384\n")],
             ["R1PlayTests.test_r1_a_continue_restores_as_of_its_save_before_the_first_look"]),
    "G385": (CAUGHT, "the restore record's world snapshot not written (finding F2)",
             [(MODE, "        self._save_world(f\"restored from save {record['id']}\")\n", "        pass  # MUTANT G385\n")],
             ["R1PlayTests.test_r1_a_continue_restores_as_of_its_save_before_the_first_look"]),
    "G386": (CAUGHT, "a continue starts with an EMPTY world memory (the restored world not given)",
             [(MODE, "        self._start_world(hands, self._choices, personality.name, restored.world)\n",
               "        self._start_world(hands, self._choices, personality.name)  # MUTANT G386\n")],
             ["R1PlayTests.test_r1_a_continue_restores_as_of_its_save_before_the_first_look"]),
    "G387": (CAUGHT, "no `end` line (`_end_memory`'s call deleted, D12 (a))",
             [(MODE, "        self._end_memory(hands, outcome, last)\n", "        pass  # MUTANT G387\n")],
             ["R1PlayTests.test_r1_the_end_line_says_chosen_budget_and_at_save",
              "R1PlayTests.test_r1_a_continue_that_stops_ends_stuck_with_a_chosen_end"]),
    "G388": (CAUGHT, "no `lost` line (the loop's hook not handed to `_count_losses`, D12 (e))",
             [(MODE, "        lost_line = self._lost_line(hands)\n", "        lost_line = None  # MUTANT G388\n")],
             ["PlayLoopTests.test_r1_the_loss_count_is_restored_and_each_loss_is_a_line"]),
    "G389": (CAUGHT, "no Pokemon registry (the watcher's registration deleted, L3 (a)-(b))",
             [(MODE, "        hands.watchers.append(lambda seen: registry.observe(\n"
                     "            seen, caught=bool(nav.battle_log) and nav.battle_log[-1][2] == \"caught\"))\n",
               "        pass  # MUTANT G389\n")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_big_moment"]),
    "G390": (CAUGHT, "the loop presses A through a save page (`_story_menu`'s save branch deleted, finding F6)",
             [(MODE, "        if kind in (\"save_dialog\", \"save_yes_no\", \"start_menu\"):\n",
               "        if False:  # MUTANT G390\n")],
             ["PlayLoopTests.test_r1_a_save_dialog_met_by_the_loop_gets_no_press",
              "PlayLoopTests.test_r1_a_start_menu_left_open_is_closed"]),
    "G391": (CAUGHT, "a big story moment makes no save due (`_after_milestones`' call deleted)",
             [(MODE, "            self._after_milestones([passed.id for passed in story.milestones[max(last[0], 0):index]])\n",
               "            pass  # MUTANT G391\n")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_big_moment", "PlayLoopTests.test_r1_the_end_save_when_due"]),
    "G392": (CAUGHT, "a heal at a POKéMON CENTER makes no save due (`_after_heal`'s call deleted)",
             [(MODE, "            self._after_heal(goal, ok)\n", "            pass  # MUTANT G392\n")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_center_heal"]),
    "G393": (CAUGHT, "a continue's eyes carry no frame base (D7: the wrap deleted)",
             [(MODE, "            eyes = _RebasedEyes(eyes, self._frame_base)\n", "            pass  # MUTANT G393\n")],
             ["R1PlayTests.test_r1_a_continue_restores_as_of_its_save_before_the_first_look"]),
    "G394": (CAUGHT, "a memory file that refuses the run is ignored (the refusal's end deleted)",
             [(MODE, "        if refused is not None:\n            outcome = refused\n",
               "        if False:  # MUTANT G394\n            outcome = refused\n")],
             ["R1PlayTests.test_r1_a_newer_memory_file_refuses_the_run_byte_identical",
              "R1PlayTests.test_r1_a_new_game_on_an_existing_memory_is_refused"]),
    "G395": (CAUGHT, "the goal manager never asks the save policy (its wiring deleted)",
             [(MODE, "        manager.saving = self._policy\n", "        pass  # MUTANT G395\n")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_big_moment"]),
    "G396": (CAUGHT, "the save goal's player not wired (`runner.saver` deleted)",
             [(MODE, "        runner.saver = lambda goal: self._save(hands, goal.reason, report)\n", "        pass  # MUTANT G396\n")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_big_moment"]),
    "G397": (CAUGHT, "a stuck save is played past (the loop's stuck-save end deleted)",
             [(MODE, "            if goal.kind == \"save\" and outcome.startswith(\"stuck:\"):\n",
               "            if False:  # MUTANT G397\n")],
             ["PlayLoopTests.test_r1_an_unwritten_save_line_ends_the_run"]),
    "G398": (CAUGHT, "a continued game meeting the title plays the New Game intro",
             [(MODE, "                if self._continued is not None:\n", "                if False:  # MUTANT G398\n")],
             ["PlayLoopTests.test_r1_continue_mode_never_plays_the_intro"]),
    "G399": (CAUGHT, "a continue takes a personality of its own, not its game's",
             [(MODE, "self._remembered_personality() or options.personality)", "options.personality)  # MUTANT G399")],
             ["R1PlayTests.test_r1_a_continue_restores_as_of_its_save_before_the_first_look"]),
    "G400": (CAUGHT, "a continue's restored losses not counted under the new ones (T5)",
             [(MODE, "        lost = report.get(\"restored_losses\", 0) + battles_lost(nav.battle_log)\n",
               "        lost = battles_lost(nav.battle_log)  # MUTANT G400\n")],
             ["PlayLoopTests.test_r1_the_loss_count_is_restored_and_each_loss_is_a_line"]),
    "G401": (CAUGHT, "a new game started over a game that has a memory file",
             [(MODE, "        elif self._book is not None:\n", "        elif False:  # MUTANT G401\n")],
             ["R1PlayTests.test_r1_a_new_game_on_an_existing_memory_is_refused"]),
    "G402": (CAUGHT, "the no-save CONTROL saves anyway (D14)",
             [(MODE, "        self._saving = path is not None and not getattr(options, \"fault_no_save\", False)\n",
               "        self._saving = path is not None  # MUTANT G402\n")],
             ["R1PlayTests.test_r1_a_new_game_on_an_existing_memory_is_refused"]),
    "G403": (CAUGHT, "`at_save` true after a press that followed the save (D12 (a))",
             [(MODE, "        at_save = self._at_save_presses is not None and hands.pad.presses == self._at_save_presses\n",
               "        at_save = self._at_save_presses is not None  # MUTANT G403\n")],
             ["R1PlayTests.test_r1_the_end_line_says_chosen_budget_and_at_save"]),
    "G404": (CAUGHT, "OVERWRITE answered as if the cart were never its own (D17's cart not handed to the skill)",
             [(MODE, "own_cart(getattr(self.options, \"cart\", None), self._saves_made > 0)",
               "own_cart(None, False)")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_big_moment"]),
    "G405": (CAUGHT, "a save's frames counted as the story's (T4: `spent[\"save\"]` deleted)",
             [(GOALS, "        if goal.kind == \"save\":\n            # (R1, build spec T4)",
               "        if False:  # MUTANT G405\n            # (R1, build spec T4)")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_big_moment"]),
    "G406": (CAUGHT, "the save machinery never started (`_start_saving`'s call deleted)",
             [(MODE, "        self._start_saving(hands, manager, state, mind, runner, starter, report)\n",
               "        pass  # MUTANT G406\n")],
             ["PlayLoopTests.test_r1_a_save_goal_after_a_big_moment", "PlayLoopTests.test_r1_the_end_save_when_due"]),
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
    # (KI-123, 2026-10-26) a filter naming no mutant (a typo, `--help`) REFUSES before anything runs or is written
    from ai_player.gates.provenance import unknown_mutants

    unknown = unknown_mutants(sys.argv[1:], MUTANTS, ("--workers", "--evidence-tag"))
    if unknown:
        print(f"REFUSED: no mutant named {unknown} ({len(MUTANTS)} exist; usage: revert_step5.py [NAME[,NAME...]] "
              f"[--workers N] [--evidence-tag TAG]); nothing was run")
        return 2
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
    tag = "step52"  # (build step 5.1; 5.2's since its part 2) the evidence file's tag
    if "--evidence-tag" in argv:
        at = argv.index("--evidence-tag")
        tag = argv[at + 1]
        del argv[at:at + 2]
    only = set(argv[0].split(",")) if argv else None
    chosen = [(name, spec) for name, spec in MUTANTS.items() if only is None or name in only]
    from ai_player.gates.provenance import watch

    # (build step 5.2, G1) the frozen-tree watch (started by the code line above): every mutant copies the tree as it is
    # when it starts, so it is checked before each copy and sealed at OVERALL
    tree = watch(REPO, explicit=True)

    def attempt(item):
        if tree.moved or not tree.check(f"before mutant {item[0]}"):
            return None, f"NOT RUN: the tree changed mid-run ({tree.moves[0][:300]})", None
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
    verdict, frozen_line = tree.seal(verdict)  # (build step 5.2, G1)
    ok_all = verdict == "PASS"
    summary = f"{counts[CAUGHT]} mutants CAUGHT as predicted, {counts[REDUNDANT]} REDUNDANT ALONE as predicted, of {len(MUTANTS) - 1}"
    out += ["", summary, frozen_line, f"OVERALL: {verdict}"]
    print(summary)
    print(frozen_line)
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
