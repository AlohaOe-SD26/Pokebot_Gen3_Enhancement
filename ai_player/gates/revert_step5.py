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
           [(GOALS, "            target = max(milestone.fight_levels) + errands.train_margin\n",
             "            target = max(milestone.fight_levels)  # MUTANT G7\n")],
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
            [(GOALS, "        known = self._known_interiors(world, CENTER_SUFFIX)\n", "        known = []  # MUTANT G10\n")],
            ["ErrandTests.test_hurt_heals_at_a_known_centre_else_at_home_else_not"]),
    "G11": (CAUGHT, "one heal threshold for every personality (half its HP)",
            [(GOALS, "        hurt = has_party and share is not None and (must_rest or share < errands.heal_below)\n",
              "        hurt = has_party and share is not None and (must_rest or share < 0.5)  # MUTANT G11\n")],
            ["ErrandTests.test_heal_thresholds_by_personality"]),
    "G12": (CAUGHT, "POKé BALLS shopped for before the adventure has started",
            [(GOALS, '        if (has_party and marks.get("ADVENTURE_STARTED") and balls < errands.balls_low\n',
              "        if (has_party and balls < errands.balls_low  # MUTANT G12\n")],
            ["ErrandTests.test_shopping_by_each_personalitys_ball_threshold"]),
    "G13": (CAUGHT, "an item ball seen is not picked up before the story goes on",
            [(GOALS, "        if ball is not None and has_party:\n", "        if False:  # MUTANT G13\n")],
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
    "G30": (CAUGHT, "a hint taken as known while hints are on, without its words (the verifier's V2)",
            [(GOALS, "        if milestone.hint_words:\n            return heard_words(heard, milestone.hint_words)\n",
              "        return True  # MUTANT G30\n")],
            ["HintTests.test_a_go_whose_words_are_unheard_explores_with_no_map",
             "HintTests.test_a_wordless_hint_heads_only_for_a_place_it_has_been"]),
    "G31": (CAUGHT, "a hint with no words heads for a place the AI has never been",
            [(GOALS, "        place = place or milestone.hint_map\n", "        return True  # MUTANT G31\n")],
            ["HintTests.test_a_wordless_hint_heads_only_for_a_place_it_has_been"]),
    "G32": (CAUGHT, "the data names a map the game never says (ROUTE 102 for MOM's 'PETALBURG GYM', the verifier's case)",
            [(DATA, '   "waypoint": "ROUTE102",\n   "maps": [\n    "OLDALE_TOWN",\n    "ROUTE102"\n   ],\n   "steps": [\n'
                    '    {\n     "do": "go",\n     "map": "PETALBURG_CITY"\n    }\n   ],\n   "hint": {\n'
                    '    "said": "MOM, on the TV: Look! It\'s PETALBURG GYM! Maybe DAD will be on!",\n'
                    '    "words": "PETALBURG",\n    "map": "PETALBURG_CITY",\n',
              '   "waypoint": "ROUTE102",\n   "maps": [\n    "OLDALE_TOWN",\n    "ROUTE102"\n   ],\n   "steps": [\n'
              '    {\n     "do": "go",\n     "map": "ROUTE102"\n    }\n   ],\n   "hint": {\n'
              '    "said": "MOM, on the TV: Look! It\'s PETALBURG GYM! Maybe DAD will be on!",\n'
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
            [(GOALS, "        nav.grass_cost = max(own, HURT_GRASS_COST)\n", "        nav.grass_cost = own  # MUTANT G41\n")],
            ["RestTests.test_the_walk_to_heal_keeps_out_of_the_grass_and_restores_the_taste"]),
    "G42": (CAUGHT, "every SCENE link refused, a door MOM walked the player through included (no way home: step5dev7 seed 3)",
            [(EXPLORE, '            if kind == "warp" and not looks_like_exit(world, key, link.get("tile")):\n',
              '            if kind == "warp" and (link.get("by") == "scene" or not looks_like_exit(world, key, '
              'link.get("tile"))):  # MUTANT G42\n')],
            ["WayTests.test_a_door_a_scene_walked_the_player_through_is_a_way"]),
    "G43": (CAUGHT, "a heal put aside after failing stays aside though the party is in danger",
            [(GOALS, "                if where is not None and (allowed or must_rest):\n",
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
    "G49": (CAUGHT, "the goal's reason quotes the milestone's STORED line, not the page the AI read",
            [(GOALS, '                said = (f"the game said: {quote(page, milestone.hint_words)!r}" if page is not None\n',
              '                said = (f"the game said: {milestone.hint_said[:90]!r}" if page is not None  # MUTANT G49\n')],
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
    out = ["AI PLAYER BUILD STEP 5 - MUTANT PROOF OF THE STORY PLAYER (gates/revert_step5.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {provenance(REPO)}",
           "Each mutant breaks ONE rule of the real code in a copy; CAUGHT = its predicted tests of gates/test_goals.py fail.", ""]
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
        path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step5-REVERT.txt"
        keep_earlier(path)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
