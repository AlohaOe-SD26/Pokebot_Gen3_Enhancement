"""MUTANT PROOF of P11-1, THE WAY THROUGH A DARK CAVE (2026-11-11): each rule of the real code, broken in a COPY of the
package, fails its predicted tests of `gates/test_ways.py` (and, for the one shared call it censuses, `gates/test_world.py`),
or is documented as REDUNDANT ALONE (offline) with the reason.

    py -3.12 -B ai_player/gates/revert_p11.py [M1,M2] [--workers N]       (exit 0 = every prediction held)

The `revert_bossprep.py` pattern: copy the package (no states, no evidence), apply ONE mutant's edits (each anchor must occur
exactly once, or the run aborts; `gates/check_anchors.py` checks every anchor in seconds), run the two suites from the copy,
check the PREDICTION: CAUGHT (every named test fails) or REDUNDANT (no test fails; the reason stated). The unchanged copy
(P0) must pass every test. The wiring mutants (a call deleted or guarded off: `gates/call_census.py` counts them) are named
for what they delete. The predictions were written and this file's sha256 recorded (`s53/p11r1/STATE.md`) BEFORE its first
run. Evidence: `ai_player/evidence/<date>-p11-REVERT.txt`.

VERSION 2 (round 2, 2026-11-11, the resumed builder; v1 sha256 b16f47b3 ran once, PASS, on round 1's code): round 2 made the
way GOAL-LESS too (`dark_way` asks `way_through` with no goal: the live walk toward STEVEN is goal-less, #114), so three v1
anchors stopped hitting exactly once (`check_anchors.py` FAILED them) and one predicted test was renamed. v2 re-anchors them
(the rules unchanged), adds the round-2 rules (the goal-less branch, `way_through`, the `through` mark, its fairness leaf, the
extractor's "farthest" rule and the shipped file against a fresh extraction), and copies `tools/decomp.pin` into each copy
(the extractor test reads the PINNED clone: POKEBOT_DECOMP must name it, or P0 ERRORS, never a silent pass). v2's
predictions were written and its sha256 recorded (`s53/p11r1/prediction_mutants_v2.sha256`) before its first run.

VERSION 3 (round 2b, 2026-11-11): the way through NEVER STEPS STRAIGHT BACK (the extractor marks none where the farthest
map's first step is the warp arrived by: round 2a's marks made 11 of 29 goal-less walks cycle, VICTORY ROAD's B1F/B2F
(30, 25) pair among them). v3 = v2's table unchanged plus two mutants of that rule (the extractor's guard deleted; a mark
that steps back planted in the shipped file). v2's run 1 is NOT evidence: this runner copies the package once PER MUTANT,
and the worktree was edited (round 2b) while that run was in flight, so its copies mixed two trees. v3's predictions were
written and its sha256 recorded (`s53/p11r1/prediction_mutants_v3.sha256`) before its first run, on a frozen tree.

VERSION 4 (P11-2, 2026-11-11, the fix round after the P11-1 verifier's CONDITIONAL PASS): v3's table, three of its anchors
re-anchored where P11-2 rewrote the line (`a_for_every_ladder` and `no_named_in_sight`: the way's branch now comes after the
route's, V2; `fair_no_through`: the leaf is no subtree now, V3), plus the P11-2 rules: the muddy slope (V1: the slide, its
ledge and its cracked floor), the refusal of what the walk does not model (an unmodelled forced movement stops the walk and
is recorded; the decomp's forced-movement table; the HM check, its walk lengths and its every-HM walk; a cuttable tree is an
HM obstacle; the refused map is left out and said loudly; the model draws the slope one way), the route's first hop keeping
its role (V2), the five leaves no subtree (V3) and `_check` DEVELOPER, first in its schema (V5). v4's predictions were
written and its sha256 recorded (`s53/p11r2/prediction_mutants_v4.sha256`) before its first run, on a frozen tree.

VERSION 5 (P11-2, 2026-11-11): v4's run 1 (sha256 f5e5d81d, on the frozen tree) held 47 of its 48 predictions and read
OVERALL FAIL: `forced_not_recorded` was CAUGHT by two of the three tests predicted (the extraction-equality test and the
hand-made forced-movement test), not by the third, the loud test, which reads the SHIPPED file's refusals, and a mutant of
the extractor's code leaves the shipped file as it is (the equality test is what ties the two). The prediction was wrong,
not the test; v5 is v4 with that one prediction corrected (and one docstring paragraph of the extractor reworded), its
sha256 recorded (`s53/p11r2/prediction_mutants_v5.sha256`) before its first run, on a frozen tree.
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
TIMEOUT = 1200
CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"
EXPLORE, NAV, WAYS, FAIR = "brain/explore.py", "brain/navigator.py", "knowledge/ways.py", "gates/check_fairness.py"
#: (v2) the extractor and the file it ships
EXTRACT, WAYS_FILE = "gates/extract_ways.py", "knowledge/world/ways.json"
#: (v2) the round-2 tests: the goal-less way (the live case), and the shipped file against a fresh extraction
GOAL_LESS = ["test_ways.CandidateTests.test_no_goal_is_the_way_through_an_unwanted_goal_none_a_lit_map_unchanged",
             "test_ways.ModelTests.test_b2f_goal_less_fix_against_fault"]
THROUGH = "test_ways.LoaderTests.test_the_way_through_with_no_goal"
EXTRACTED = "test_ways.LoaderTests.test_the_file_is_the_extractors_output_from_the_pinned_decomp"
#: (v4, P11-2) the extractor's own tests, the fairness tests and the route's first hop (V2, the verifier's VP1)
SLOPE = "test_ways.ExtractorTests.test_the_muddy_slope_only_goes_down_on_foot"
FORCED = "test_ways.ExtractorTests.test_a_forced_movement_it_does_not_model_stops_the_walk_and_refuses_the_map"
HM_CHECK = "test_ways.ExtractorTests.test_ways_that_depend_on_the_hms_refuse_the_map_and_an_obstacle_that_changes_nothing_is_a_wall"
LOUD = "test_ways.ExtractorTests.test_every_refusal_is_said_loudly_naming_the_map_and_the_tile"
LEAVES = "test_ways.FairnessTests.test_the_file_is_classified_leaf_by_leaf_and_a_planted_developer_key_fails"
GATED = "test_ways.FairnessTests.test_the_loader_and_the_deciding_code_are_gated"
DEV_KEYS = "test_ways.FairnessTests.test_no_developer_key_is_lost_and_the_loader_reads_only_its_keys"
ROUTE_HOP = "test_ways.CandidateTests.test_the_routes_first_hop_keeps_its_role_where_it_is_the_way"
#: the tests every "no way at all" mutant fails (the way never offered on the model)
NO_WAY = ["test_ways.CandidateTests.test_the_fact_only_adds_the_way_and_it_outranks_the_frontier",
          "test_ways.CandidateTests.test_the_latest_arrival_counts_and_survives_a_restore",
          "test_ways.ModelTests.test_b2f_fix_against_fault",
          "test_ways.ModelTests.test_the_last_b1f_stay",
          "test_ways.ModelTests.test_the_first_b1f_stay_leaves_by_the_named_ladder",
          "test_ways.BoundTests.test_an_unreachable_way_is_given_up_and_never_loops"]

#: name -> (prediction, the rule that is broken, [edits], tests that MUST fail (CAUGHT) or the reason (REDUNDANT)).
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str] | str]] = {
    "P0": (CONTROL, "nothing: the unchanged copy", [], []),
    # ---- the wiring: the way is asked for in every decision, and the loader answers
    "no_way_call": (CAUGHT, "the way never asked for in a decision (`dark_way`'s call in `candidates` deleted)",
                    [(EXPLORE, "    way = dark_way(nav, memory, goal)\n", "    way = None  # MUTANT no_way_call\n")],
                    NO_WAY + ["test_ways.CandidateTests.test_an_unnamed_ladder_in_sight_stays_a_door_the_named_one_is_the_way"]
                    + GOAL_LESS),
    "way_on_deleted": (CAUGHT, "the fact never read in `dark_way` (`way_on`'s call deleted)",
                       [(EXPLORE, "    return way_on(memory.const, arrival, toward_goal)\n",
                         "    return None  # MUTANT way_on_deleted\n")],
                       NO_WAY + ["test_ways.CandidateTests.test_an_unnamed_ladder_in_sight_stays_a_door_the_named_one_is_the_way"]),
    "no_dark_check": (REDUNDANT, "`dark_way` asks for a way on a LIT map too (its own `dark` check deleted)",
                      # (v2) re-anchored: round 2 split v1's `if goal is None or not dark(...)` into the dark check and the
                      # goal-less branch
                      [(EXPLORE, "    if not dark(memory.const):\n        return None\n    world = nav.world\n",
                        "    world = nav.world  # MUTANT no_dark_check\n")],
                      "`way_on` and (round 2) `way_through` each check `dark` themselves and answer None on a lit map; "
                      "`dark_way`'s own check only skips the arrival search there (work, not behaviour)."),
    # ---- (v2, round 2) the GOAL-LESS way: the live walk toward STEVEN has no goal map (#114: the way never fired)
    "no_way_through": (CAUGHT, "round 1 restored: with NO goal no way (the goal-less branch answers None, not `way_through`)",
                       [(EXPLORE, "    if goal is None:\n        return way_through(memory.const, arrival)\n",
                         "    if goal is None:\n        return None  # MUTANT no_way_through\n")],
                       GOAL_LESS),
    "goal_ignored": (CAUGHT, "the way through whatever the goal (the goal-less branch taken with a goal too): a traveller "
                             "bound elsewhere is sent through the cave",
                     [(EXPLORE, "    if goal is None:\n        return way_through(memory.const, arrival)\n",
                       "    if True:  # MUTANT goal_ignored\n        return way_through(memory.const, arrival)\n")],
                     ["test_ways.CandidateTests.test_no_goal_is_the_way_through_an_unwanted_goal_none_a_lit_map_unchanged"]),
    "dark_never": (CAUGHT, "the loader knows no dark map (`dark` answers False: `_ways`' call deleted)",
                   [(WAYS, "    return (const or \"\") in _ways()\n", "    return False  # MUTANT dark_never\n")],
                   ["test_ways.LoaderTests.test_the_dark_maps_are_the_requires_flash_maps",
                    "test_ways.LoaderTests.test_granite_caves_three_ways_toward_steven",
                    "test_ways.LoaderTests.test_fault_the_file_missing_is_no_dark_map",
                    "test_ways.CandidateTests.test_the_fact_only_adds_the_way_and_it_outranks_the_frontier",
                    "test_ways.ModelTests.test_the_last_b1f_stay", THROUGH] + GOAL_LESS),
    "way_on_dark_unchecked": (CAUGHT, "`way_on` reads the table of a map it does not hold (its `dark` check deleted)",
                              # (v2) re-anchored on the docstring's last line: round 2's `way_through` has the same check
                              [(WAYS, "    floor, a scene), or when no map it leads toward is wanted.\"\"\"\n"
                                      "    if not dark(const) or arrival is None:\n",
                                "    floor, a scene), or when no map it leads toward is wanted.\"\"\"\n"
                                "    if arrival is None:  # MUTANT way_on_dark_unchecked\n")],
                              ["test_ways.LoaderTests.test_granite_caves_three_ways_toward_steven",
                               "test_ways.LoaderTests.test_fault_the_file_missing_is_no_dark_map"]),
    "ways_table_empty": (CAUGHT, "`way_on` reads no way (`_ways`' call in it deleted): every dark map, no way on",
                         # (v2) re-anchored: round 2's table rows carry a fifth field, the way through
                         [(WAYS, "    for start, take, leads_to, toward, _through in _ways()[const or \"\"]:\n",
                           "    for start, take, leads_to, toward, _through in []:  # MUTANT ways_table_empty\n")],
                         ["test_ways.LoaderTests.test_granite_caves_three_ways_toward_steven",
                          "test_ways.CandidateTests.test_the_fact_only_adds_the_way_and_it_outranks_the_frontier",
                          "test_ways.ModelTests.test_the_last_b1f_stay"]),
    # ---- (v2, round 2) `way_through`: the loader's answer with no goal
    "way_through_dark_unchecked": (CAUGHT, "`way_through` reads the table of a map it does not hold (its `dark` check "
                                           "deleted)",
                                   [(WAYS, "    hold.\"\"\"\n    if not dark(const) or arrival is None:\n",
                                     "    hold.\"\"\"\n    if arrival is None:  # MUTANT way_through_dark_unchecked\n")],
                                   [THROUGH, "test_ways.LoaderTests.test_fault_the_file_missing_is_no_dark_map"]),
    "through_table_empty": (CAUGHT, "`way_through` reads no way (`_ways`' call in it deleted): goal-less, no way anywhere",
                            [(WAYS, "    for start, take, leads_to, _toward, through in _ways()[const or \"\"]:\n",
                              "    for start, take, leads_to, _toward, through in []:  # MUTANT through_table_empty\n")],
                            [THROUGH] + GOAL_LESS),
    "through_unmarked": (CAUGHT, "`way_through` ignores the `through` mark: the arrival's FIRST way (by the ladder's "
                                 "coordinates), on B1F (4, 21) the ladder straight back up, on B2F (28, 21) the same",
                         [(WAYS, "        if start == here and through is not None:\n",
                           "        if start == here:  # MUTANT through_unmarked\n")],
                         [THROUGH] + GOAL_LESS),
    # ---- the goal: the way toward what the intent wants, nothing else
    "any_destination": (CAUGHT, "the first way of the arrival whatever the goal (`wanted` not asked): B1F's and B2F's "
                                "first ways lead straight back up",
                        [(WAYS, "            if wanted(name):\n", "            if True:  # MUTANT any_destination\n")],
                        # (v2) round 2 renamed the candidate test (its unwanted-goal half is the one that fails here)
                        ["test_ways.LoaderTests.test_granite_caves_three_ways_toward_steven",
                         "test_ways.CandidateTests.test_no_goal_is_the_way_through_an_unwanted_goal_none_a_lit_map_unchanged",
                         "test_ways.ModelTests.test_b2f_fix_against_fault"]),
    "arrival_first": (CAUGHT, "the way from the FIRST arrival on the map, not this stay's (the memory's oldest transition)",
                      [(EXPLORE, "    arrival = next((change.arrival for change in reversed(world.transitions) if change.target == "
                                 "memory.key), None)\n",
                        "    arrival = next((change.arrival for change in world.transitions if change.target == memory.key), "
                        "None)  # MUTANT arrival_first\n")],
                      ["test_ways.CandidateTests.test_the_latest_arrival_counts_and_survives_a_restore"]),
    # ---- option A folded in: the NAMED ladder in sight outranks the frontier; no other ladder does
    # (v4) re-anchored: P11-2 put the route's branch first (V2), so the way's is an `elif` now; (v4) the unnamed ladder of
    # the test is (4, 21) seen from the slope's other side (P11-1's (8, 5) is out of reach of (4, 21) on foot, V1)
    "a_for_every_ladder": (CAUGHT, "option A for EVERY unused ladder in sight on a dark map (the decision reverted): from "
                                   "B1F's north side, (4, 21), back up to 1F, taken for the way",
                           [(EXPLORE, "        elif way is not None and exit_tile == way.take:\n",
                             "        elif way is not None and link is None:  # MUTANT a_for_every_ladder\n")],
                           ["test_ways.CandidateTests.test_an_unnamed_ladder_in_sight_stays_a_door_the_named_one_is_the_way"]),
    "no_named_in_sight": (CAUGHT, "the named ladder in sight is a plain door (option A dropped)",
                          [(EXPLORE, "        elif way is not None and exit_tile == way.take:\n",
                            "        elif False:  # MUTANT no_named_in_sight\n")],
                          ["test_ways.CandidateTests.test_an_unnamed_ladder_in_sight_stays_a_door_the_named_one_is_the_way",
                           "test_ways.ModelTests.test_the_last_b1f_stay",
                           "test_ways.ModelTests.test_b2f_fix_against_fault"]),
    # ---- option B: the way not in sight, walked toward through the unseen
    "no_aims": (CAUGHT, "no place for the way while it is unseen (`way_aims`' call deleted)",
                [(EXPLORE, "        aims = way_aims(memory, way.take, reach)\n", "        aims = set()  # MUTANT no_aims\n")],
                ["test_ways.CandidateTests.test_the_fact_only_adds_the_way_and_it_outranks_the_frontier",
                 "test_ways.CandidateTests.test_the_latest_arrival_counts_and_survives_a_restore",
                 "test_ways.ModelTests.test_b2f_fix_against_fault",
                 "test_ways.BoundTests.test_an_unreachable_way_is_given_up_and_never_loops"]),
    "no_unseen_plan": (CAUGHT, "the unseen way never planned (the plan's calls guarded off: in_map_walls, astar, path_cost, "
                               "moved)",
                       [(EXPLORE, "        if aims:\n            planned = in_map_walls(memory, walls, None)\n"
                                  "            path = astar(memory, here, aims, planned, weights.grass_cost)\n"
                                  "            cost = path_cost(memory, here, path, planned, weights.grass_cost) if path else None\n"
                                  "            if cost is not None:\n                end = here\n"
                                  "                for direction in path:\n                    end = moved(end, direction)\n",
                         "        if False:  # MUTANT no_unseen_plan\n            planned = in_map_walls(memory, walls, None)\n"
                         "            path = astar(memory, here, aims, planned, weights.grass_cost)\n"
                         "            cost = path_cost(memory, here, path, planned, weights.grass_cost) if path else None\n"
                         "            if cost is not None:\n                end = here\n"
                         "                for direction in path:\n                    end = moved(end, direction)\n")],
                       ["test_ways.CandidateTests.test_the_fact_only_adds_the_way_and_it_outranks_the_frontier",
                        "test_ways.CandidateTests.test_the_latest_arrival_counts_and_survives_a_restore",
                        "test_ways.ModelTests.test_b2f_fix_against_fault",
                        "test_ways.BoundTests.test_an_unreachable_way_is_given_up_and_never_loops"]),
    "way_value_door": (CAUGHT, "the way worth a door's 0.8 (it no longer outranks the frontier)",
                       [(EXPLORE, "WAY_VALUE = 15.0\n", "WAY_VALUE = 0.8  # MUTANT way_value_door\n")],
                       ["test_ways.CandidateTests.test_the_fact_only_adds_the_way_and_it_outranks_the_frontier",
                        "test_ways.CandidateTests.test_an_unnamed_ladder_in_sight_stays_a_door_the_named_one_is_the_way",
                        "test_ways.ModelTests.test_b2f_fix_against_fault"]),
    "way_not_onward": (REDUNDANT, "`way` not one of ONWARD_KINDS",
                       [(EXPLORE, "ONWARD_KINDS = (\"frontier\", \"road\", \"door\", \"route\", \"grass\", \"people\", \"way\")\n",
                         "ONWARD_KINDS = (\"frontier\", \"road\", \"door\", \"route\", \"grass\", \"people\")  # MUTANT\n")],
                       "ONWARD_KINDS only drops the exit just come in by (and `goals.worth_going` only counts) when NO other "
                       "onward place exists; on a dark map with a way there is always a frontier or the way's exit, and the "
                       "way outranks that exit anyway (150 points against `Weights.back`)."),
    # ---- the navigator: a way seen is chosen again
    "no_stale_rule": (CAUGHT, "a way walked toward while unseen is never stale once seen (its rule deleted)",
                      [(NAV, "    if target.kind == \"way\" and target.exit is None and memory.known(target.tile):\n",
                        "    if False:  # MUTANT no_stale_rule\n")],
                      ["test_ways.CandidateTests.test_a_way_walked_toward_unseen_is_stale_once_seen"]),
    "no_stale_call": (CAUGHT, "the run loop never asks `stale_reason` (its call deleted: revert_step3's W31, here for the "
                              "census site of the changed function)",
                      [(NAV, "                stale = stale_reason(memory, target) if memory is not None else None\n",
                        "                stale = None  # MUTANT no_stale_call\n")],
                      ["test_world.ReversalTests.test_reversals_are_near_zero_and_no_stale_target_is_walked_onto"]),
    "no_frontier_stale": (CAUGHT, "a frontier seen past is never stale (the frontier rule's `known` call guarded off: the "
                                  "census site P11-1's second `known` call in `stale_reason` lists)",
                          [(NAV, "    if target.kind == \"frontier\" and memory.known(target.tile) and not "
                                 "memory.unknown_neighbours(target.tile):\n",
                            "    if False:  # MUTANT no_frontier_stale\n")],
                          ["test_world.ReversalTests.test_reversals_are_near_zero_and_no_stale_target_is_walked_onto"]),
    # ---- the fairness gate
    "fair_subtree": (CAUGHT, "ways.json's `maps[].ways[]` classified as a SUBTREE (a developer key planted under a way passes)",
                     [(FAIR, "        \"maps[].ways[]\": (AI, \"one way on\", False),\n",
                       "        \"maps[].ways[]\": (AI, \"one way on\", True),  # MUTANT fair_subtree\n")],
                     ["test_ways.FairnessTests.test_the_file_is_classified_leaf_by_leaf_and_a_planted_developer_key_fails"]),
    "fair_no_loader": (CAUGHT, "ways.json's loader undeclared (RULE B never walks the file; B1 forgets its name)",
                       [(FAIR, "    \"knowledge/ways.py\": (\"world/ways.json\",),\n", "    # MUTANT fair_no_loader\n")],
                       ["test_ways.FairnessTests.test_the_file_is_classified_leaf_by_leaf_and_a_planted_developer_key_fails",
                        "test_ways.FairnessTests.test_the_loader_and_the_deciding_code_are_gated"]),
    # (v2, round 2) the new leaf unclassified: RULE B finds `maps[].ways[].through` on the CLEAN copy (both tests assert the
    # gate's findings on a clean or mention-only copy are empty)
    "fair_no_through": (CAUGHT, "ways.json's round-2 leaf `maps[].ways[].through` unclassified",
                        # (v4) re-anchored: the leaf is no subtree since P11-2 (V3)
                        [(FAIR, "        \"maps[].ways[].through\": (AI, \"the cave's far end when this is THE WAY THROUGH "
                                "from that arrival (a guide's 'the way \"\n"
                                "                                      \"through the cave'), else null\", False),\n",
                          "        # MUTANT fair_no_through\n")],
                        ["test_ways.FairnessTests.test_the_file_is_classified_leaf_by_leaf_and_a_planted_developer_key_fails",
                         "test_ways.FairnessTests.test_the_loader_and_the_deciding_code_are_gated"]),
    # ---- (v2) the extractor and the file it ships: the file must be the pinned decomp's extraction, exactly
    "extract_far_nearest": (CAUGHT, "the extractor marks the way toward the NEAREST map as the way through (its `max` made "
                                    "`min`): from B1F (4, 21) the ladder back up to 1F",
                            [(EXTRACT, "            far = max(reached.items(), key=lambda item: (item[1][0], item[0]))[0] if "
                                       "reached else None\n",
                              "            far = min(reached.items(), key=lambda item: (item[1][0], item[0]))[0] if "
                              "reached else None  # MUTANT extract_far_nearest\n")],
                            [EXTRACTED]),
    "extract_through_everywhere": (CAUGHT, "the extractor marks EVERY way of an arrival as the way through",
                                   [(EXTRACT, "\"toward\": sorted(dests), \"through\": far if far in dests else None})\n",
                                     "\"toward\": sorted(dests), \"through\": far})  # MUTANT extract_through_everywhere\n")],
                                   [EXTRACTED]),
    "file_hand_edit": (CAUGHT, "the shipped ways.json edited by hand (one developer meta value; the AI's behaviour unchanged)",
                       [(WAYS_FILE, " \"_made_by\": \"ai_player/gates/extract_ways.py\",\n",
                         " \"_made_by\": \"a hand edit\",\n")],
                       [EXTRACTED]),
    # ---- (v3, round 2b) NEVER STRAIGHT BACK: the way through is never the warp the player arrived by
    "extract_back_allowed": (CAUGHT, "the extractor's never-straight-back guard deleted (round 2a's marks: 21 of 29 step "
                                     "back, 11 walks cycle); the shipped file no longer matches its extraction",
                             [(EXTRACT, "            if far is not None and reached[far][3] == arrival:\n"
                                        "                far = None\n",
                               "            pass  # MUTANT extract_back_allowed\n")],
                             [EXTRACTED]),
    "file_back_mark": (CAUGHT, "the shipped file marks GRANITE CAVE B1F's (29, 2) pocket ladder, from (29, 2), as the way "
                               "through (straight back down where the player came up)",
                       [(WAYS_FILE, "     \"take\": [\n      29,\n      2\n     ],\n"
                                    "     \"leads_to\": \"MAP_GRANITE_CAVE_B2F\",\n"
                                    "     \"toward\": [\n      \"MAP_GRANITE_CAVE_B2F\"\n     ],\n     \"through\": null\n",
                         "     \"take\": [\n      29,\n      2\n     ],\n"
                         "     \"leads_to\": \"MAP_GRANITE_CAVE_B2F\",\n"
                         "     \"toward\": [\n      \"MAP_GRANITE_CAVE_B2F\"\n     ],\n"
                         "     \"through\": \"MAP_GRANITE_CAVE_B2F\"\n")],
                       ["test_ways.LoaderTests.test_the_way_through_never_steps_back_nor_cycles", EXTRACTED]),
    # ---- (v4, P11-2) V1: THE MUDDY SLOPE, one way on foot (src/field_player_avatar.c:567-581)
    "slope_two_way": (CAUGHT, "the muddy slope walked as plain floor (P11-1's walk: (8, 5) reached from (4, 21) again)",
                      [(EXTRACT, "            if behaviour not in self.forced:\n                return tile, elev, cost\n",
                        "            if behaviour not in self.forced or behaviour == MUDDY_SLOPE:  # MUTANT slope_two_way\n"
                        "                return tile, elev, cost\n")],
                      [EXTRACTED, SLOPE, FORCED]),
    "slide_ledge_blocked": (CAUGHT, "a south ledge under a slope stops the slide instead of being jumped",
                            [(EXTRACT, "                if JUMPS[under] != \"down\" or not self.inside(land) or "
                                       "self._walled(land, hms, met):\n",
                              "                if True:  # MUTANT slide_ledge_blocked\n")],
                            [FORCED]),
    "slide_onto_crack_walks_on": (CAUGHT, "a slide onto a cracked floor stops on the slope instead of dropping the player",
                                  [(EXTRACT, "            if under in CRACKED and not hms:\n                return None\n",
                                    "            if False:  # MUTANT slide_onto_crack_walks_on\n                return None\n")],
                                  [FORCED]),
    # ---- (v4) V1/V4: WHAT THE WALK DOES NOT MODEL, IT REFUSES
    "forced_walks_on": (CAUGHT, "on foot, a forced movement the walk does not model is walked on as floor (it is still "
                                "recorded)",
                        [(EXTRACT, "                return (tile, elev, cost) if hms else None\n",
                          "                return tile, elev, cost  # MUTANT forced_walks_on\n")],
                        [FORCED]),
    "forced_not_recorded": (CAUGHT, "a forced movement the walk does not model is not recorded: VICTORY ROAD B1F loses its "
                                    "FORCED MOVEMENT reason (the Hall of Fame's ice)",
                            [(EXTRACT, "                    met.add((\"forced\", self.id, tile, behaviour))\n",
                              "                    pass  # MUTANT forced_not_recorded\n")],
                            # (v5) not LOUD: it reads the shipped file, which this mutant of the extractor's code leaves as
                            # it is (v4's prediction listed it and missed; the equality test is what ties the two)
                            [EXTRACTED, FORCED]),
    "forced_table_only_slope": (CAUGHT, "the decomp's forced-movement table read as the slope alone (ice, slides, currents "
                                        "and mats walked as floor)",
                                [(EXTRACT, "        out |= found\n",
                                  "        out |= found & {MUDDY_SLOPE}  # MUTANT forced_table_only_slope\n")],
                                [EXTRACTED, SLOPE]),
    "hm_check_off": (CAUGHT, "the HM check never refuses (VICTORY ROAD B2F and the three CAVE OF ORIGIN maps shipped on "
                             "their on-foot ways)",
                     [(EXTRACT, "    if hm_ways != ways or hm_lengths != lengths:\n",
                       "    if False:  # MUTANT hm_check_off\n")],
                     [EXTRACTED, HM_CHECK]),
    "hm_lengths_ignored": (CAUGHT, "the HM check compares the ways only, not the walk lengths (a shorter walk with an HM "
                                   "could start by another ladder)",
                           [(EXTRACT, "    if hm_ways != ways or hm_lengths != lengths:\n",
                             "    if hm_ways != ways:  # MUTANT hm_lengths_ignored\n")],
                           [HM_CHECK]),
    "hm_walk_on_foot": (CAUGHT, "the every-HM walk keeps the HM obstacles as walls (it opens only the water)",
                        [(EXTRACT, "        return not hms\n", "        return True  # MUTANT hm_walk_on_foot\n")],
                        [HM_CHECK]),
    "cut_tree_not_obstacle": (CAUGHT, "a cuttable tree walked through as 'another object' (P11-1's HM obstacles)",
                              [(EXTRACT, "HM_OBSTACLES = (\"OBJ_EVENT_GFX_BREAKABLE_ROCK\", \"OBJ_EVENT_GFX_PUSHABLE_BOULDER\", "
                                         "\"OBJ_EVENT_GFX_CUTTABLE_TREE\")\n",
                                "HM_OBSTACLES = (\"OBJ_EVENT_GFX_BREAKABLE_ROCK\", \"OBJ_EVENT_GFX_PUSHABLE_BOULDER\")  "
                                "# MUTANT cut_tree_not_obstacle\n")],
                              [HM_CHECK]),
    "loud_silent": (CAUGHT, "the refusals are no longer said (every mode prints nothing for them)",
                    [(EXTRACT, "    return [f\"REFUSED {map_id}: {why}\" for map_id, reasons in doc[\"_check\"][\"left_out\"]."
                               "items() for why in reasons]\n",
                      "    return []  # MUTANT loud_silent\n")],
                    [LOUD]),
    "refusal_ships_anyway": (CAUGHT, "a refused map is recorded as left out AND shipped (its guess emitted)",
                             [(EXTRACT, "            left_out[map_id] = why\n            continue\n",
                               "            left_out[map_id] = why  # MUTANT refusal_ships_anyway\n")],
                             [EXTRACTED]),
    "model_slope_floor": (CAUGHT, "the test side's model draws the slope as floor again (P11-1's two-way fixture)",
                          [(EXTRACT, "                elif behaviour == MUDDY_SLOPE and g.behaviour.get((x, y - 1)) != MUDDY_SLOPE:\n",
                            "                elif False:  # MUTANT model_slope_floor\n")],
                          [EXTRACTED]),
    "model_slope_unchecked": (REDUNDANT, "the model's check that a slope column has walls both sides and floor under it "
                                         "deleted",
                              [(EXTRACT, "            if sides != [\"#\", \"#\"] or bottom >= g.height or rows[bottom][x] != "
                                         "\".\":\n",
                                "            if False:  # MUTANT model_slope_unchecked\n")],
                              "on the pinned layouts the only slope column of the modelled floors (GRANITE CAVE B1F (9, 9)-"
                              "(9, 10)) has walls both sides and floor under it, so the check never fires there; it "
                              "guards a future layout the model could not draw one way."),
    # ---- (v4) V2: the route's first hop keeps the route's role where it is also the way's ladder (the verifier's VP1)
    "route_hop_becomes_way": (CAUGHT, "the way's branch before the route's again (P11-1's order): the exit becomes a `way` "
                                      "and lost_way, which walks routes only, answers None",
                              [(EXPLORE, "        if first_hop is not None and first_hop[0] == \"warp\" and "
                                         "tuple(first_hop[1][\"tile\"]) == exit_tile:\n",
                                "        if way is not None and exit_tile == way.take:  # MUTANT route_hop_becomes_way\n"
                                "            kind, value, why = \"way\", WAY_VALUE, f\"{way_why}: in sight\"\n"
                                "        elif first_hop is not None and first_hop[0] == \"warp\" and "
                                "tuple(first_hop[1][\"tile\"]) == exit_tile:\n")],
                              [ROUTE_HOP]),
    # ---- (v4) V3: the five leaves are no subtree; V5: `_check` DEVELOPER, first in its schema
    "fair_leaf_subtree": (CAUGHT, "ways.json's leaf `maps[].ways[].toward` a subtree again (a key nested inside it passes "
                                  "RULE B: the verifier's VM1)",
                          [(FAIR, "        \"maps[].ways[].toward\": (AI, \"the maps it is the way on toward (a guide: 'the "
                                  "ladder east is the way to STEVEN')\",\n                                 False),\n",
                            "        \"maps[].ways[].toward\": (AI, \"the maps it is the way on toward (a guide: 'the ladder "
                            "east is the way to STEVEN')\",\n                                 True),  # MUTANT\n")],
                          [LEAVES]),
    "fair_check_meta": (CAUGHT, "`_check` classified META again (its walk lengths readable by a loader: the verifier's VM2)",
                        [(FAIR, "        \"_check\": (DEVELOPER, \"the extractor's own checks (walk lengths, the dark maps it "
                                "left out and why, the HM obstacles \"\n                              \"its walks met): the "
                                "developers' proof, never read by the AI\", True),\n",
                          "        # MUTANT fair_check_meta\n")],
                        [GATED, DEV_KEYS]),
    "fair_check_after_meta": (CAUGHT, "`_check` listed AFTER `_*` (an exact pattern is matched in order, so `_*` classifies "
                                      "it META)",
                              [(FAIR, "        \"_check\": (DEVELOPER, \"the extractor's own checks (walk lengths, the dark "
                                      "maps it left out and why, the HM obstacles \"\n                              \"its walks "
                                      "met): the developers' proof, never read by the AI\", True),\n        \"_*\": (META, "
                                      "\"where the file came from (the pinned decomp, each input's sha256, the extractor, its "
                                      "notes)\", True),\n",
                                "        \"_*\": (META, \"where the file came from (the pinned decomp, each input's sha256, "
                                "the extractor, its notes)\", True),\n        \"_check\": (DEVELOPER, \"the extractor's own "
                                "checks: MUTANT fair_check_after_meta\", True),\n")],
                              [GATED, DEV_KEYS]),
}

DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_ways, test_world
suite = unittest.TestSuite()
for module in (test_ways, test_world):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("ai_player.gates.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_ways.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_p11_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    # (v2) the extractor test resolves the pinned clone through `tools/decomp.pin` beside the package (extract_world.PIN_FILE)
    (root / "tools").mkdir()
    shutil.copy2(REPO / "tools" / "decomp.pin", root / "tools" / "decomp.pin")
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_p11_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_p11_tests.py")], cwd=str(root), env=env,
                              capture_output=True, timeout=TIMEOUT)
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
    out = ["AI PLAYER P11-1, THE WAY THROUGH A DARK CAVE - MUTANT PROOF (gates/revert_p11.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
           f"code: {provenance(REPO)}",
           "Each mutant breaks ONE rule of the real code in a copy; CAUGHT = its predicted tests of gates/test_ways.py (and "
           "test_world.py) fail; REDUNDANT = no test fails, and the reason the rule is redundant alone (offline) is stated.",
           ""]
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
    summary = (f"{counts[CAUGHT]} mutants CAUGHT as predicted, {counts[REDUNDANT]} REDUNDANT ALONE as predicted, "
               f"of {len(MUTANTS) - 1}")
    out += ["", summary, f"OVERALL: {verdict}"]
    print(summary)
    print(f"OVERALL: {verdict}")
    if only is None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-p11-REVERT.txt"
        keep_earlier(path)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
