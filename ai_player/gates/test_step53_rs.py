"""TEST SIDE (build step 5.3, queue item 3 (4): THE RE-SOURCING BUILD, builder 1): the re-sourced checks of `rate_step5.py`,
each graded by the GAME or the HARNESS alone (USER RULING 35), and the development-only RE-GRADE.

    py -3.12 ai_player/gates/test_step53_rs.py        (unittest; offline, no ROM, about 2 s)

The plan these tests prove is `PROJECT KNOWLEDGE/ai-research-notes/2026-10-25-step5.3-resourcing-plan.md` (its items are the
A2 decision addendum's work list). Every rule has a FAULT arm (the rule broken: the check must FAIL) and a CONTROL arm (the
healthy path passes), and each guard's call-deleting mutant is caught here (the builder's report lists them):
  TrainedTests      item 1: R5.CH1_TRAINED by the tall-grass steps (Story floor; Trainer/Catcher paired with NOTRAIN) and
                    R5.NOTRAIN_TRAINED_CHECK (NOTRAIN's Story runs under the floor); the AI's windows are no longer read.
  StallTests        item 2: R5.STALL and STALL1-3 by the game's wait path alone.
  BeelineTests      item 3: R5.OFF_BEELINE on the game's stood tiles.
  NoSpeedrunTests   item 4: R5.NO_SPEEDRUN_DICE on the game's frames to the POKéDEX less the game's battle frames.
  Lose3Tests        item 6: R5.LOSE3's game/harness half (a floor of 2 runs that reached the cap) and R5.LOSE3_WORD.
  PatienceTests     item 7: R5.PATIENCE on the dex half alone.
  DetourTests       item 16(a): arrival judged over [end - slack, end], never after the end.
  RegradeTests      part C: a re-grade refuses every purpose but `regrade` and every source but a finished development
                    entry; a re-grade of a synthetic kept folder equals the original grade; the control arms.
BUILDER 2 (items 10-15 and 17; `live_step5.py` on synthetic launcher runs, no emulator):
  PurityEndedTests     item 10: L5.PURITY_ENDED REPORTED from the harness's stop record (one known answer per stop cause).
  PurityHonestyTests   item 11: THE AMENDMENT (a HONESTY truth half may be the harness); the pad's counts as HONESTY.
  PurityOutcomeTests   item 12: the brain's outcome claim against the game's proof, both ways; no claim is VACUOUS.
  ShoppedTests         item 13 and the plan's (c): L5.SHOPPED_GAME GRADED by the game; the told purchases HONESTY.
  AchievementTests     the plan's rule (e): L5.CAUGHT, L5.HEALED, L5.ITEMS known answers both ways.
  ReportedFormTests    item 14: rows 20-27 REPORTED, each game form printed beside its controls and equal to the measure's.
  DiagnosticTests      item 15: rows 29-39 DIAGNOSTIC; a failing one moves no verdict; re-typed GRADED, the import refuses.
  DebtTests            item 17: `b1_debt.json` EMPTY; the refusal both ways on the real table.
THE FIX ROUND (the verifier's failures F1-F6 and weak proofs; every mutant run with fresh bytecode):
  PairedPooledTests       F3: the POOLED half of `paired_rule` fails on its own (every seed just above NOTRAIN); R7: a run
                          with no tile read is named in R5.CH1_TRAINED's text.
  NoSpeedrunHalvesTests   F4: each half of R5.NO_SPEEDRUN_DICE (the pooled bound, the seeds share) fails on its own.
  Ch2NoBattleTests        item 5: R5.CH2_NOBATTLE by the game's frames to WALLY less its battles; each half; AI not read.
  PushLoafTests           items 8, 9, 16(b): PUSHING, BLOCKED, NO_LOAFING, LOAF by the game's push; BLOCKED_REACH
                          DIAGNOSTIC; PUSH_PATHS_AGREE by the paths' verdicts within the sampling band at each bound.
  RegradeFidelityTests    V5 (a chapter-2 folder graded from its chapter-1 row), V26 (no run.json: an error row that
                          fails R5.PLANS_PLAYED), V27 (CONTROL_ARMS exactly), V7 (pooled_slices).
  ShopCounterReadTests    R5: `play_harness.story_truth` reads GAME_STAT_SHOPPED (index 38).
  (ShoppedTests above carries R5's ball-throw, prize-money and whiteout arms and F5's missing-read guards.)
STAGE B STEP 1 (2026-10-27, where the STOP checks get their runs; the DECISION in
`ai-research-notes/2026-10-26-stageB-stop-runs-design.md`):
  StopRunsTests      phase 2 replays LOSE3's runs beside every natural loss (`phase2_lost`); a sweep with NO natural loss
                     gives R5.STOP and R5.STOPDEAD their runs (VACUOUS before); the natural replays unchanged; the replays
                     matched by identity; the texts count replays by source; R5.LOSE3's control arm FAILS on 2+ STOPDEAD runs.
  StopRunsMainTests  `main` plays those replays (nothing played: the runners faked), each in a copy with LOSE3's mutant and
                     the STOP plan's edits.
STAGE B STEP 3 (2026-10-27, the FINAL bounds; `ai-research-notes/2026-10-27-step5.3-stageB-bounds.md`):
  StageBBoundsTests  every graded bound the re-sourced checks read PINNED at its final value (`STAGE_B_FINAL`), each placed
                     between the real code's worst development number and its control's nearest (`STAGE_B_PLACED`), no
                     paired ratio under 1.03; LOAF_FRAMES_MAX on ledger #39's numbers through the verdict code.
"""

from __future__ import annotations

import dataclasses
import json
import math
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import grader_checks as gc  # noqa: E402
from ai_player.gates import rate_step5 as rs  # noqa: E402
from ai_player.gates.test_step53_a1 import grade_sweep, row, sweep  # noqa: E402

BOUNDS = rs.BOUNDS


def status(results, check_id: str) -> str:
    found = [c for c in results if c.id == check_id]
    assert len(found) == 1, (check_id, [c.id for c in results])
    return found[0].status


def grass_rows(ch1: dict[int, tuple[str, int]], notrain: dict[int, tuple[str, int]]) -> dict[str, list[dict]]:
    """CH1 and NOTRAIN rows whose only difference is the GAME's grass steps before the rival, per seed (personality, steps)."""
    return {"CH1": [row("CH1", s, p, grass_before_rival=g) for s, (p, g) in ch1.items()],
            "NOTRAIN": [row("NOTRAIN", s, p, grass_before_rival=g) for s, (p, g) in notrain.items()]}


#: ledger #39's grass steps before the rival (the measure json), per seed: CH1 and NOTRAIN
#: (read back from the kept folders by this build's re-grade, `2026-10-25-step53rs1-REGRADE.txt`)
DEV_CH1 = {1307: ("Catcher", 168), 1308: ("Trainer", 254), 1309: ("Story", 177), 1310: ("Catcher", 196),
           1311: ("Trainer", 373), 1312: ("Story", 120), 1313: ("Catcher", 122), 1314: ("Trainer", 278),
           1315: ("Story", 106), 1316: ("Catcher", 185), 1317: ("Trainer", 265), 1318: ("Story", 102)}
DEV_NO = {1307: ("Catcher", 124), 1308: ("Trainer", 124), 1309: ("Story", 32), 1310: ("Catcher", 144),
          1311: ("Trainer", 128), 1312: ("Story", 23), 1313: ("Catcher", 99), 1314: ("Trainer", 150),
          1315: ("Story", 38), 1316: ("Catcher", 150), 1317: ("Trainer", 151), 1318: ("Story", 37)}


class TrainedTests(unittest.TestCase):
    def trained(self, ch1, notrain) -> tuple[str, str]:
        results = grade_sweep(grass_rows(ch1, notrain))
        return status(results, "R5.CH1_TRAINED"), status(results, "R5.NOTRAIN_TRAINED_CHECK")

    def test_the_development_rows_pass_and_notrain_fails_the_story_floor(self):
        self.assertEqual(self.trained(DEV_CH1, DEV_NO), (gc.PASS, gc.PASS))  # CONTROL

    def test_a_story_run_under_the_floor_fails(self):
        low = {**DEV_CH1, 1309: ("Story", 38)}
        self.assertEqual(self.trained(low, DEV_NO)[0], gc.FAIL)  # FAULT: 38 steps
        edge = {**DEV_CH1, 1309: ("Story", BOUNDS["TRAINED_GRASS_STORY_MIN"])}
        self.assertEqual(self.trained(edge, DEV_NO)[0], gc.PASS)  # CONTROL: at the floor passes

    def test_a_pooled_ratio_of_one_fails_trainer_and_catcher(self):
        for personality in ("Trainer", "Catcher"):
            with self.subTest(personality=personality):
                same = {s: (p, DEV_NO[s][1] if p == personality else g) for s, (p, g) in DEV_CH1.items()}
                self.assertEqual(self.trained(same, DEV_NO)[0], gc.FAIL)  # FAULT: CH1 == NOTRAIN

    def test_the_share_fails_when_ch1_is_above_notrain_on_under_half_the_seeds(self):
        # six Trainer seeds: CH1 far above on 2 (pooled well over 1.3), just under on 4 -> 2 of 6 < 50 %
        ch1 = {1: ("Trainer", 900), 2: ("Trainer", 900), 3: ("Trainer", 140), 4: ("Trainer", 140), 5: ("Trainer", 140),
               6: ("Trainer", 140)}
        no = {s: ("Trainer", 150) for s in ch1}
        self.assertEqual(self.trained(ch1, no)[0], gc.FAIL)  # FAULT: the share
        ch1[3] = ("Trainer", 160)  # 3 of 6 above: exactly the 50 % share
        self.assertEqual(self.trained(ch1, no)[0], gc.PASS)  # CONTROL

    def test_the_stall2_1308_shape_passes_under_the_paired_rule(self):
        # a Trainer seed walking 139 against its own NOTRAIN's 124 (under another seed's NOTRAIN 151): paired, it passes
        shape = {**DEV_CH1, 1308: ("Trainer", 139), 1308 + 100: ("Trainer", 300)}
        no = {**DEV_NO, 1308: ("Trainer", 124), 1308 + 100: ("Trainer", 151)}
        self.assertEqual(self.trained(shape, no)[0], gc.PASS)  # CONTROL

    def test_a_personality_with_runs_but_no_pair_never_passes(self):
        no = {s: v for s, v in DEV_NO.items() if v[0] != "Catcher"}
        self.assertEqual(self.trained(DEV_CH1, no)[0], gc.FAIL)  # FAULT: Catcher unjudgeable

    def test_the_ais_training_windows_are_no_longer_read(self):
        rows = grass_rows(DEV_CH1, DEV_NO)
        for r in rows["CH1"]:
            r.update(game_train_steps=0, game_train_won=0, train_steps_before_rival=0, train_windows=0, rival_judge=None)
        self.assertEqual(status(grade_sweep(rows), "R5.CH1_TRAINED"), gc.PASS)  # the AI's records say nothing now

    def test_notrain_at_the_story_floor_fails_the_control_check(self):
        no = {**DEV_NO, 1309: ("Story", BOUNDS["TRAINED_GRASS_STORY_MIN"])}
        self.assertEqual(self.trained(DEV_CH1, no)[1], gc.FAIL)  # FAULT: the control met the floor
        none = {s: v for s, v in DEV_NO.items() if v[0] != "Story"}
        self.assertEqual(self.trained(DEV_CH1, {**none, **{s: v for s, v in DEV_NO.items() if v[0] == "Story"}})[1],
                         gc.PASS)  # CONTROL

    def test_notrain_against_itself_fails_by_construction(self):
        rule = rs.paired_rule(grass_rows(DEV_NO, DEV_NO)["CH1"], grass_rows(DEV_NO, DEV_NO)["NOTRAIN"], "Trainer")
        self.assertEqual((rule["pooled"], rule["above"], rule["ok"]), (1.0, 0, False))

    def test_the_grass_read_counts_tall_grass_between_the_marks(self):
        data = {"story": {"changes": [{"mark": "VAR_BIRCH_LAB_STATE", "to": 2, "f": 100},
                                      {"mark": "DEFEATED_RIVAL_ROUTE103", "to": 1, "f": 900}]},
                "game_reads": {"tiles": {"steps": [[50, "0:16", 1, 1, "Tall Grass"], [200, "0:16", 1, 2, "Tall Grass"],
                                                   [300, "0:16", 1, 3, "Normal"], [900, "0:16", 1, 4, "Tall Grass"],
                                                   [901, "0:16", 1, 5, "Tall Grass"]]}}}
        self.assertEqual(rs.grass_before_rival(data), 2)  # 200 and 900: after the starter's mark, up to the flag
        self.assertIsNone(rs.grass_before_rival({**data, "game_reads": {}}))  # no tile read: not judged
        self.assertEqual(rs.grass_stint(data), 700)


class StallTests(unittest.TestCase):
    def test_a_real_run_at_the_bound_by_the_game_fails(self):
        rows = sweep()
        rows["NOHINTS"][0]["await_game_max"] = BOUNDS["AWAIT_MAX"]
        self.assertEqual(status(rs.step51_verdicts(rows), "R5.STALL"), gc.FAIL)  # FAULT
        self.assertEqual(status(rs.step51_verdicts(sweep()), "R5.STALL"), gc.PASS)  # CONTROL

    def test_the_ais_record_is_no_longer_read(self):
        rows = sweep()
        rows["CH1"][0]["await_ai_max"] = 900  # the AI's path alone over the bound
        self.assertEqual(status(rs.step51_verdicts(rows), "R5.STALL"), gc.PASS)

    def test_a_stall_arm_fails_only_by_the_games_path(self):
        for plan in ("STALL1", "STALL2", "STALL3"):
            with self.subTest(plan=plan):
                rows = sweep()
                rows[plan] = [row(plan, s, await_ai_max=600, await_game_max=150) for s in (1, 2)]
                self.assertEqual(status(rs.step51_verdicts(rows), f"R5.{plan}"), gc.FAIL)  # FAULT: every game value 150
                rows[plan][1].update(await_ai_max=0, await_game_max=600)
                self.assertEqual(status(rs.step51_verdicts(rows), f"R5.{plan}"), gc.PASS)  # CONTROL: one by the game


class BeelineTests(unittest.TestCase):
    def test_ch1_on_the_beeline_by_the_game_fails(self):
        rows = sweep()
        corridor = set().union(*(r["_stood"] for r in rows["ERRANDS_OFF"]))
        for r in rows["CH1"]:
            r["_stood"] = set(list(corridor)[:2])  # the game: only tiles a beeline run stood on (its AI memory wide)
        self.assertEqual(status(rs.step51_verdicts(rows), "R5.OFF_BEELINE"), gc.FAIL)  # FAULT
        self.assertEqual(status(rs.step51_verdicts(sweep()), "R5.OFF_BEELINE"), gc.PASS)  # CONTROL

    def test_the_ais_world_memory_is_no_longer_read(self):
        rows = sweep()
        for r in rows["CH1"]:
            r["_tiles"] = set()  # the AI's memory says nothing off the beeline; the game says plenty
        self.assertEqual(status(rs.step51_verdicts(rows), "R5.OFF_BEELINE"), gc.PASS)

    def test_a_control_run_counts_against_the_other_control_runs(self):
        rows = sweep()
        found = rs.off_beeline(rs.on_game_tiles(rows["CH1"]), rs.on_game_tiles(rows["ERRANDS_OFF"]))
        self.assertEqual(set(found["control"].values()), {1})  # its own OFFn tile: not zeroed by itself

    def test_game_stood_reads_moves_steps_and_start(self):
        data = {"places": {"moves": [[10, "0:9", 1, 1]]},
                "game_reads": {"tiles": {"start": [0, "0:9", 0, 0, "Normal"], "steps": [[20, "0:9", 2, 2, "Normal"]]}}}
        self.assertEqual(rs.game_stood(data), {"0:9 0,0", "0:9 1,1", "0:9 2,2"})


class NoSpeedrunTests(unittest.TestCase):
    def test_a_ratio_of_one_fails(self):
        rows = sweep()
        for r in rows["ERRANDS_OFF"]:
            r["dex_game"] = dict(rows["CH1"][0]["dex_game"])
        self.assertEqual(status(rs.step51_verdicts(rows), "R5.NO_SPEEDRUN_DICE"), gc.FAIL)  # FAULT
        self.assertEqual(status(rs.step51_verdicts(sweep()), "R5.NO_SPEEDRUN_DICE"), gc.PASS)  # CONTROL

    def test_a_run_slower_only_by_its_battles_fails(self):
        def data(dex_f, battles):
            return {"story": {"changes": [{"mark": "RECEIVED_POKEDEX_FROM_BIRCH", "to": 1, "f": dex_f}]},
                    "places": {"every": 10, "battles": battles}}

        ch1 = rs.frames_to_mark(data(140000, [[10000, 29990]]), "RECEIVED_POKEDEX_FROM_BIRCH")
        off = rs.frames_to_mark(data(120000, []), "RECEIVED_POKEDEX_FROM_BIRCH")
        self.assertEqual((ch1["no_battle"], off["no_battle"]), (120000, 120000))
        rows = sweep()
        for r in rows["CH1"]:
            r["dex_game"] = ch1
        for r in rows["ERRANDS_OFF"]:
            r["dex_game"] = off
        self.assertEqual(status(rs.step51_verdicts(rows), "R5.NO_SPEEDRUN_DICE"), gc.FAIL)  # FAULT: battles subtracted

    def test_the_ais_digests_are_no_longer_read(self):
        rows = sweep()
        for r in rows["CH1"]:
            r["time"] = {"outside_nb": 1, "battles": 0}  # the AI's own digests say it beelined
        self.assertEqual(status(rs.step51_verdicts(rows), "R5.NO_SPEEDRUN_DICE"), gc.PASS)

    def test_a_target_confirmed_only_at_the_end(self):
        data = {"story": {"changes": [], "frames": 5000}, "story_truth": {"marks": {"VAR_PETALBURG_GYM_STATE": 2}},
                "start_story": {"marks": {"VAR_PETALBURG_GYM_STATE": 1}}, "places": {"battles": []}}
        self.assertEqual(rs.frames_to_mark(data, "VAR_PETALBURG_GYM_STATE", 2)["at_end"], True)
        data["start_story"]["marks"]["VAR_PETALBURG_GYM_STATE"] = 2  # it held the mark when it began: not reached here
        self.assertIsNone(rs.frames_to_mark(data, "VAR_PETALBURG_GYM_STATE", 2))


def lose3(*shapes) -> list[dict]:
    """LOSE3 rows: (seed, the game's losses, frames from its last loss to the run's end, reason, report)."""
    want = "play: stuck: 3 battles lost (MAX_LOSSES 3)"
    return [row("LOSE3", s, "Catcher", losses_game=g, losses_ai=rep, losses_told=rep, last_loss_f=1000, frames=1000 + after,
                reason=reason or want, max_losses=3) for s, g, after, reason, rep in shapes]


class Lose3Tests(unittest.TestCase):
    def check(self, rows, check_id="R5.LOSE3") -> str:
        return status(rs.step51_verdicts({"LOSE3": rows}), check_id)

    def test_the_development_shape_passes_and_a_late_end_fails(self):
        dev = [(1307, 3, 655, None, 3), (1310, 3, 651, None, 3), (1313, 2, 200000, "play: stuck: no progress", 2),
               (1316, 3, 664, None, 3)]
        self.assertEqual(self.check(lose3(*dev)), gc.PASS)  # CONTROL: 1313 never reached the cap: left out of n
        late = dev[:1] + [(1310, 3, rs.STOP_WITHIN + 1, None, 3)] + dev[2:]
        self.assertEqual(self.check(lose3(*late)), gc.FAIL)  # FAULT: 6,001 frames after the third loss

    def test_a_loss_past_the_cap_fails(self):
        self.assertEqual(self.check(lose3((1, 3, 600, None, 3), (2, 4, 600, None, 4))), gc.FAIL)  # FAULT: went on

    def test_under_the_floor_is_vacuous(self):
        self.assertEqual(self.check(lose3((1, 3, 600, None, 3), (2, 2, 9000, "x", 2))), gc.VACUOUS)  # 1 of floor 2
        self.assertEqual(self.check(lose3((1, 3, 600, None, 3), (2, 3, 600, None, 3))), gc.PASS)

    def test_the_ai_half_is_honesty(self):
        good = lose3((1, 3, 600, None, 3), (2, 3, 600, None, 3))
        self.assertEqual(self.check(good, "R5.LOSE3_WORD"), gc.PASS)  # CONTROL
        self.assertEqual(gc.CHECKS["R5.LOSE3_WORD"].kind, gc.HONESTY)
        no_cap = lose3((1, 3, 600, "play: stuck: no progress for 9 frames", 3), (2, 3, 600, None, 3))
        self.assertEqual(self.check(no_cap, "R5.LOSE3_WORD"), gc.FAIL)  # FAULT: a reason without the cap
        self.assertEqual(self.check(no_cap), gc.PASS)  # ... which the graded half no longer reads
        wrong = lose3((1, 3, 600, None, 2), (2, 3, 600, None, 3))
        self.assertEqual(self.check(wrong, "R5.LOSE3_WORD"), gc.FAIL)  # FAULT: a report of 2 against the game's 3


class PatienceTests(unittest.TestCase):
    def check(self, reached: list[bool]) -> str:
        rows = {"PATIENCE": [row("PATIENCE", s, "Trainer", reached=ok, train_span=0) for s, ok in enumerate(reached)]}
        return status(rs.step51_verdicts(rows), "R5.PATIENCE")

    def test_the_dex_share(self):
        self.assertEqual(self.check([True] * 4), gc.PASS)  # CONTROL: the dev rows (and the AI's span 0 is not read)
        self.assertEqual(self.check([True] * 4 + [False] * 2), gc.PASS)  # CONTROL: 4 of 6
        self.assertEqual(self.check([True] * 3 + [False] * 3), gc.FAIL)  # FAULT: 3 of 6
        self.assertEqual(self.check([False] * 4), gc.FAIL)  # FAULT: PATIENCE_OLD's shape graded as PATIENCE


class DetourTests(unittest.TestCase):
    RECORDS = [{"decision": "goal", "action": "detour", "frame": 84159},
               {"decision": "goal_end", "action": "detour", "frame": 84492, "reason": "reached the frontier at (0, 10)",
                "extra": {"yield": {"productive": True, "place": ["0:10", 0, 10, "frontier"]}}},
               {"decision": "watch", "frame": 84600}]

    def test_an_end_on_the_place_reads_arrived_though_a_scene_moved_it_after(self):
        # NOTRAIN 1318: on (0, 10) from 84485 to 84510, moved to (1, 10) at 84511 (19 frames after the end)
        data = {"places": {"moves": [[84490, "0:10", 0, 10], [84520, "0:10", 1, 10]]},
                "game_reads": {"tiles": {"start": [0, "0:10", 5, 5, "Normal"],
                                         "steps": [[84485, "0:10", 0, 10, "Normal"], [84511, "0:10", 1, 10, "Normal"]]}}}
        row_ = rs.curiosity_rows(self.RECORDS, data, 0)[0]
        self.assertEqual((row_["said_reached"], row_["game_reached"]), (True, True))  # FAULT case of the old lookup

    def test_a_never_arrived_detour_still_reads_false(self):
        data = {"game_reads": {"tiles": {"start": [0, "0:10", 5, 5, "Normal"],
                                         "steps": [[84000, "0:10", 3, 10, "Normal"], [84530, "0:10", 0, 10, "Normal"]]}}}
        self.assertFalse(rs.curiosity_rows(self.RECORDS, data, 0)[0]["game_reached"])  # CONTROL: arrived only after
        self.assertEqual(rs.stood_during(data, 84462, 84492), {("0:10", 3, 10)})

    def test_a_place_reached_only_after_the_end_is_not_arrived(self):
        # (the fix round, re-made mutant B1-M13 survived: a window [end, end + slack]) the player steps onto the place 8
        # frames AFTER the detour's end: the detour did not arrive (never a frame after the end)
        data = {"game_reads": {"tiles": {"start": [0, "0:10", 5, 5, "Normal"],
                                         "steps": [[84000, "0:10", 3, 10, "Normal"], [84500, "0:10", 0, 10, "Normal"]]}}}
        self.assertFalse(rs.curiosity_rows(self.RECORDS, data, 0)[0]["game_reached"])  # FAULT case of a late window
        early = {"game_reads": {"tiles": {"start": [0, "0:10", 5, 5, "Normal"],
                                          "steps": [[84000, "0:10", 3, 10, "Normal"], [84480, "0:10", 0, 10, "Normal"]]}}}
        self.assertTrue(rs.curiosity_rows(self.RECORDS, early, 0)[0]["game_reached"])  # CONTROL: 12 frames before


class RegradeTests(unittest.TestCase):
    LEDGER = {"entries": [{"id": 39, "driver": "rate_step5", "purpose": "development", "status": "done", "first": 1307,
                           "last": 1318, "evidence": "e.txt"},
                          {"id": 40, "driver": "rate_step5", "purpose": "graded", "status": "done", "first": 961,
                           "last": 980}]}

    @staticmethod
    def play() -> dict:
        return {"story": {"changes": [{"mark": "VAR_BIRCH_LAB_STATE", "to": 2, "f": 50,
                                       "stats": {"trainer_battles": 0, "wild_battles": 0}},
                                      {"mark": "DEFEATED_RIVAL_ROUTE103", "to": 1, "f": 500, "party": [[0, 9, 20, 30]],
                                       "stats": {"trainer_battles": 1, "wild_battles": 3}},
                                      {"mark": "RECEIVED_POKEDEX_FROM_BIRCH", "to": 1, "f": 800,
                                       "stats": {"trainer_battles": 1, "wild_battles": 3}}], "battles": [], "frames": 1000},
                "story_truth": {"marks": {"DEFEATED_RIVAL_ROUTE103": 1, "RECEIVED_POKEDEX_FROM_BIRCH": 1}}, "frames": 1000,
                "reason": "play: done", "seconds": 2.0, "report": {"losses": 0},
                "waits_game": {"longest": [0, 0, 150], "samples": 9}, "max_losses": 3,
                "places": {"moves": [[10, "0:16", 1, 1]], "push": {"longest": [0, 0, 500, 5]}, "samples": 9, "every": 10,
                           "battles": [[200, 290]]},
                "game_reads": {"tiles": {"start": [0, "0:16", 1, 0, "Normal"], "steps": [[100, "0:16", 1, 1, "Tall Grass"]]},
                               "stop": {"by": "ai"}, "frames": {"equal": True}}}

    def kept(self, root: Path) -> list[dict]:
        actions = [{"decision": "goal", "action": "go", "frame": 0}, {"decision": "watch", "frame": 900}]
        folder = root / "ai_step5_CH1_1307_abc"
        folder.mkdir()
        (folder / rs.RUN_FILE).write_text(json.dumps({"plan": "CH1", "seed": 1307, "base": None, "personality": "Catcher",
                                                      "starter": "TREECKO", "play": self.play()}), encoding="utf-8")
        (folder / "actions.jsonl").write_text("\n".join(json.dumps(a) for a in actions), encoding="utf-8")
        return actions

    def test_a_graded_purpose_and_a_non_development_source_refuse(self):
        with tempfile.TemporaryDirectory() as root:
            self.kept(Path(root))
            for purpose in ("graded", "development", "replay"):
                with self.subTest(purpose=purpose), self.assertRaisesRegex(ValueError, "never"):
                    rs.regrade(Path(root), 39, purpose, 300000, self.LEDGER)  # FAULT: a re-grade is never graded
            for entry in (40, 41):
                with self.subTest(entry=entry), self.assertRaisesRegex(ValueError, "not a finished development"):
                    rs.regrade(Path(root), entry, rs.REGRADE, 300000, self.LEDGER)  # FAULT: graded / unknown source
            lines, _ = rs.regrade(Path(root), 39, rs.REGRADE, 300000, self.LEDGER)  # CONTROL
        self.assertTrue(lines[0].startswith("RE-GRADE (DEVELOPMENT ONLY") and "ledger #39" in lines[0])
        self.assertTrue(lines[-1].startswith("RE-GRADE VERDICT: ") and "ledger #39" in lines[-1])

    def test_phase_2_is_judged_by_the_rule_the_sweep_was_played_under(self):
        # (stage B step 1's verifier: a re-grade of ledger #39 read FAIL for LOSE3 replays that sweep never played) an
        # entry before FORCED_REPLAYS_FROM_ENTRY is re-graded with `forced` False, a later one with True
        ledger = {"entries": [dict(self.LEDGER["entries"][0]),
                              dict(self.LEDGER["entries"][0], id=rs.FORCED_REPLAYS_FROM_ENTRY)]}
        seen = []
        real = rs.verdicts
        with tempfile.TemporaryDirectory() as root, \
                mock.patch.object(rs, "verdicts", lambda s, r, forced=True: seen.append(forced) or real(s, r, forced)):
            self.kept(Path(root))
            lines, _ = rs.regrade(Path(root), 39, rs.REGRADE, 300000, ledger)
            self.assertEqual(seen[0], False)  # FAULT arm of the old behaviour: #39 judged by the new rule
            self.assertTrue(any("LOSE3's forced losses replayed: no" in line for line in lines))
            seen.clear()
            lines, _ = rs.regrade(Path(root), rs.FORCED_REPLAYS_FROM_ENTRY, rs.REGRADE, 300000, ledger)
            self.assertEqual(seen[0], True)  # CONTROL: a sweep played under the rule is judged by it
            self.assertTrue(any("LOSE3's forced losses replayed: yes" in line for line in lines))

    def test_an_empty_root_refuses(self):
        with tempfile.TemporaryDirectory() as root, self.assertRaisesRegex(ValueError, "no kept run folder"):
            rs.regrade(Path(root), 39, rs.REGRADE, 300000, self.LEDGER)

    def test_a_regrade_of_a_kept_folder_equals_the_original_grade(self):
        with tempfile.TemporaryDirectory() as root:
            actions = self.kept(Path(root))
            kept = rs.kept_rows(Path(root), 300000)["CH1"][0]
        direct = rs.grade_run("CH1", 1307, "Catcher", "TREECKO", self.play(), actions, 2.0)
        direct["budget"] = 300000
        # the GAME reads `grade_run` records for the re-sourced checks (each call's deletion must show here): one grass
        # step between the marks, the tiles stood on, the dex at 800 less the battle's 100 frames
        self.assertEqual((direct["grass_before_rival"], direct["grass_stint"], direct["_stood"]),
                         (1, 0, {"0:16 1,0", "0:16 1,1"}))
        self.assertEqual(direct["dex_game"], {"frame": 800, "no_battle": 700, "at_end": False})
        self.assertIsNone(direct["wally_game"])
        public = {k: v for k, v in kept.items() if not k.startswith("_")}
        want = {k: v for k, v in direct.items() if not k.startswith("_")}
        self.assertEqual({k: public[k] for k in want}, want)
        self.assertEqual(kept["_stood"], direct["_stood"])
        self.assertEqual((public["harness_stop"], public["frames_equal"]), ("ai", True))
        statuses = [(c.id, c.status, c.text) for c in grade_sweep({"CH1": [kept]})]
        self.assertEqual(statuses, [(c.id, c.status, c.text) for c in grade_sweep({"CH1": [{**direct, **{
            k: kept[k] for k in ("harness_stop", "frames_equal")}}]})])

    def test_the_cli_refuses_a_graded_regrade_and_a_register(self):
        for argv in (["--purpose", "graded", "--first-seed", "1", "--runs", "x", "--ledger-entry", "39"],
                     ["--purpose", rs.REGRADE, "--runs", "x", "--ledger-entry", "39", "--register"],
                     ["--purpose", rs.REGRADE, "--runs", "x"]):
            with self.subTest(argv=argv), mock.patch.object(sys, "argv", ["rate_step5.py", *argv]), \
                    mock.patch("sys.stderr"), self.assertRaises(SystemExit) as done:
                rs.main()
            self.assertEqual(done.exception.code, 2)

    def test_a_missing_game_push_read_is_none_never_zero(self):
        # (the small weak proofs, 2026-10-25) FAULT: a run with no `places.push` read was given push_game 0, which passed
        # the push checks silently; it is None now (left out of their n and named)
        actions = [{"decision": "goal", "action": "go", "frame": 0}]
        play = self.play()
        del play["places"]["push"]
        missing = rs.grade_run("CH1", 1307, "Catcher", "TREECKO", play, actions, 2.0)
        self.assertEqual((missing["push_game"], missing["push_game_at"]), (None, None))
        # CONTROL: a read of no stretch at all is a real 0, not a missing read
        play["places"]["push"] = {"longest": [0, 0, 0, 0]}
        self.assertEqual(rs.grade_run("CH1", 1307, "Catcher", "TREECKO", play, actions, 2.0)["push_game"], 0)

    def test_the_cli_regrades_a_kept_root_and_writes_regrade_evidence(self):
        from ai_player.gates import ledger

        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as out:
            self.kept(Path(root))
            argv = ["rate_step5.py", "--purpose", rs.REGRADE, "--runs", root, "--ledger-entry", "39", "--evidence-tag", "t"]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(ledger, "load", lambda *a, **k: self.LEDGER), \
                    mock.patch.object(rs, "EVIDENCE_DIR", Path(out)), mock.patch.object(rs, "keep_earlier", lambda p: None), \
                    mock.patch("sys.stdout"):
                code = rs.main()  # CONTROL: routed to the re-grade's own parser, nothing played
            files = list(Path(out).glob("*-t-REGRADE.txt"))
            self.assertIn(code, (0, 1))
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0].read_text(encoding="utf-8").startswith("RE-GRADE (DEVELOPMENT ONLY"))

    def test_the_regrade_parser_takes_only_the_regrade_purpose(self):
        # FAULT: its own parser refuses a graded purpose at the command line (exit 2), before any folder is read
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit) as done:
            rs.regrade_main(["--purpose", "graded", "--runs", "x", "--ledger-entry", "39"])
        self.assertEqual(done.exception.code, 2)

    def test_every_control_arm_fails_the_healthy_sweep_and_a_harmless_control_is_shown(self):
        arms = rs.control_arms(sweep())
        self.assertEqual({(c, k) for c, k, _, _ in arms}, {(c, k) for c, _, k in rs.CONTROL_ARMS})
        self.assertEqual([a[:3] for a in arms if a[2] == gc.PASS], [])  # every control FAILS or is VACUOUS
        rows = sweep()
        rows["STALL1"] = [row("STALL1", 1, await_game_max=100)]  # a control that does not stall
        shown = {(c, k): s for c, k, s, _ in rs.control_arms(rows)}
        self.assertEqual(shown[("R5.STALL", "STALL1")], gc.PASS)  # FAULT: the arm reports it, never hides it


# ================================================================================ THE FIX ROUND (items 5, 8, 9, 16(b); F3-F5)
def dex_rows(ch1: list[int], off: list[int], key: str = "dex_game", plans: tuple[str, str] = ("CH1", "ERRANDS_OFF")):
    """The healthy sweep with the GAME's no-battle frames under `key` set per seed (1-4) for the real plan and its beeline."""
    rows = sweep()
    for plan, values in zip(plans, (ch1, off)):
        for r, value in zip(rows[plan], values):
            r[key] = {"frame": value + 5000, "no_battle": value, "at_end": False}
    return rows


class PairedPooledTests(unittest.TestCase):
    """F3: the POOLED half of `paired_rule` (TRAINED_RATIO_TRAINER_MIN 1.3, TRAINED_RATIO_CATCHER_MIN 1.1) has its own
    fault: every seed of the personality just above NOTRAIN holds the share half (4 of 4) and must still FAIL."""

    def test_the_pooled_half_fails_when_every_seed_is_only_just_above(self):
        for personality in ("Trainer", "Catcher"):
            with self.subTest(personality=personality):
                close = {s: (p, DEV_NO[s][1] + 1 if p == personality else g) for s, (p, g) in DEV_CH1.items()}
                rows = grass_rows(close, DEV_NO)
                rule = rs.paired_rule(rows["CH1"], rows["NOTRAIN"], personality)
                self.assertEqual((rule["above"], len(rule["pairs"])), (4, 4))  # the share half HOLDS
                self.assertLess(rule["pooled"], rule["need"])
                self.assertEqual(status(grade_sweep(rows), "R5.CH1_TRAINED"), gc.FAIL)  # FAULT: pooled ~1.01
                need = BOUNDS[f"TRAINED_RATIO_{personality.upper()}_MIN"]
                at = {s: (p, math.ceil(DEV_NO[s][1] * need) if p == personality else g) for s, (p, g) in DEV_CH1.items()}
                self.assertEqual(status(grade_sweep(grass_rows(at, DEV_NO)), "R5.CH1_TRAINED"), gc.PASS)  # CONTROL

    def test_a_run_without_a_tile_read_is_named_never_silently_left_out(self):
        # R7: a run that beat the rival with no tile read is left out of n AND named in the check's text
        rows = grass_rows(DEV_CH1, DEV_NO)
        rows["CH1"][0]["grass_before_rival"] = None  # seed 1307
        check = [c for c in grade_sweep(rows) if c.id == "R5.CH1_TRAINED"][0]
        self.assertIn("no grass read (not judged) [1307]", check.text)  # FAULT shape: it is named
        self.assertEqual(check.n, 11)
        healthy = [c for c in grade_sweep(grass_rows(DEV_CH1, DEV_NO)) if c.id == "R5.CH1_TRAINED"][0]
        self.assertIn("no grass read (not judged) none", healthy.text)  # CONTROL
        self.assertEqual(healthy.n, 12)


class NoSpeedrunHalvesTests(unittest.TestCase):
    """F4: both halves of R5.NO_SPEEDRUN_DICE have their own fault: the POOLED bound (NOBATTLE_RATIO_MIN) with CH1 slower on
    every seed, and the SEEDS share (NOBATTLE_SEEDS_MIN) with a pooled ratio far over the bound."""

    def check(self, ch1: list[int]) -> str:
        return status(rs.step51_verdicts(dex_rows(ch1, [80000] * 4)), "R5.NO_SPEEDRUN_DICE")

    def test_the_pooled_bound(self):
        self.assertEqual(self.check([80800] * 4), gc.FAIL)  # FAULT: 1.01, slower in 4 of 4
        self.assertEqual(self.check([84800] * 4), gc.PASS)  # CONTROL: 1.06

    def test_the_seeds_share(self):
        self.assertEqual(self.check([160000, 160000, 79000, 79000]), gc.FAIL)  # FAULT: pooled 1.49, slower in 2 of 4
        self.assertEqual(self.check([160000, 160000, 81000, 79000]), gc.PASS)  # CONTROL: 3 of 4 (>= 60 %)

    def test_a_tie_is_not_slower(self):
        # (the fix round's verifier: `x[3] > 1` mutated to `>= 1` survived) a seed at exactly the beeline's frames is not
        # "the slower", so two ties leave CH1 the slower in 2 of 4
        self.assertEqual(self.check([160000, 160000, 80000, 80000]), gc.FAIL)  # FAULT: pooled 1.5, 2 ties, 2 of 4
        self.assertEqual(self.check([160000, 160000, 80100, 80000]), gc.PASS)  # CONTROL: one tie broken, 3 of 4

    def test_slower_by_the_frames_not_the_rounded_ratio(self):
        # (the small weak proofs, 2026-10-25) 80,010 against 80,000 is slower, though its ratio rounds to 1.0 for print
        self.assertEqual(self.check([160000, 160000, 80010, 80010]), gc.PASS)  # was FAIL: 2 of 4 by the rounded ratio


class Ch2NoBattleTests(unittest.TestCase):
    """Item 5: R5.CH2_NOBATTLE by the GAME's frames to WALLY's var less its battle frames, paired with CH2_OFF; the AI's own
    digests (`time_wally`) are no longer read; each half (pooled CH2_NOBATTLE_RATIO_MIN, seeds CH2_NOBATTLE_SEEDS_MIN) fails."""

    def check(self, ch2: list[int], off: list[int] | None = None, rows=None) -> str:
        rows = rows or dex_rows(ch2, off or [40000] * 4, "wally_game", ("CH2", "CH2_OFF"))
        return status(rs.chapter2_verdicts(rows), "R5.CH2_NOBATTLE")

    def test_the_development_shape_passes_and_a_ratio_of_one_fails(self):
        self.assertEqual(self.check([46200] * 4), gc.PASS)  # CONTROL: 1.155 (the dev pooled), slower in 4 of 4
        self.assertEqual(self.check([40000] * 4), gc.FAIL)  # FAULT: ratio 1.0

    def test_the_pooled_bound(self):
        self.assertEqual(self.check([40400] * 4), gc.FAIL)  # FAULT: 1.01, slower in 4 of 4
        self.assertEqual(self.check([42400] * 4), gc.PASS)  # CONTROL: 1.06

    def test_the_seeds_share(self):
        self.assertEqual(self.check([80000, 80000, 39000, 39000]), gc.FAIL)  # FAULT: pooled 1.49, slower in 2 of 4
        self.assertEqual(self.check([80000, 80000, 41000, 39000]), gc.PASS)  # CONTROL: 3 of 4 (>= 70 %)

    def test_a_tie_is_not_slower(self):
        # (the fix round's verifier's counterexample: `x[3] > 1` mutated to `>= 1` survived) a tie is not "the slower"
        self.assertEqual(self.check([80000, 80000, 40000, 40000]), gc.FAIL)  # FAULT: pooled 1.5, 2 ties, 2 of 4
        self.assertEqual(self.check([80000, 80000, 40100, 40100]), gc.PASS)  # CONTROL: the ties broken, 4 of 4

    def test_slower_by_the_frames_not_the_rounded_ratio(self):
        # (the small weak proofs, 2026-10-25) 40,010 against 40,000 is slower, though its ratio rounds to 1.0 for print
        self.assertEqual(self.check([80000, 80000, 40010, 40010]), gc.PASS)  # was FAIL: 2 of 4 by the rounded ratio

    def test_the_ais_digests_are_no_longer_read(self):
        rows = dex_rows([46200] * 4, [40000] * 4, "wally_game", ("CH2", "CH2_OFF"))
        for r in rows["CH2"]:
            r["time_wally"] = {"outside_nb": 1}  # the AI's own digests say it beelined; the game says it did not
        self.assertEqual(self.check([], rows=rows), gc.PASS)
        for plan in ("CH2", "CH2_OFF"):
            for r in rows[plan]:
                r["wally_game"] = None  # no game read at all: nothing to judge
        self.assertEqual(self.check([], rows=rows), gc.VACUOUS)

    def test_ch2_off_in_ch2s_slot_fails_by_construction(self):
        arms = {(c, k): s for c, k, s, _ in rs.control_arms(sweep())}
        self.assertEqual(arms[("R5.CH2_NOBATTLE", "CH2_OFF")], gc.FAIL)
        self.assertIn(("R5.CH2_NOBATTLE", "CH2_OFF"), rs.BY_CONSTRUCTION)
        # (stage B step 3) the beeline in CH1's slot is OFF_BEELINE's own denominator: it fails by construction, labelled
        self.assertEqual(arms[("R5.OFF_BEELINE", "ERRANDS_OFF")], gc.FAIL)
        self.assertIn(("R5.OFF_BEELINE", "ERRANDS_OFF"), rs.BY_CONSTRUCTION)


class PushLoafTests(unittest.TestCase):
    """Items 8 and 9: R5.PUSHING, R5.BLOCKED, R5.NO_LOAFING and R5.LOAF on the GAME's push (`push_game`) alone; BLOCKED's
    reach is the DIAGNOSTIC R5.BLOCKED_REACH. Item 16(b): R5.PUSH_PATHS_AGREE compares the two paths' verdicts at each
    graded push bound within the game path's sampling band."""

    def results(self, plan: str, rows_of_plan: list[dict]) -> list:
        return rs.step52_verdicts({**sweep(), plan: rows_of_plan})

    def test_a_missing_game_push_read_is_left_out_and_named(self):
        # (the small weak proofs, 2026-10-25) a run with no game push read is left out of each push check's n and named in
        # its text, never counted as 0; with every read missing each push check reads VACUOUS (and nothing raises)
        one = [row("NOHINTS", 1, push_ai=10, push_game=None)] + sweep()["NOHINTS"][1:]
        results = self.results("NOHINTS", one)
        for check in ("R5.PUSHING", "R5.NO_LOAFING"):
            found = next(c for c in results if c.id == check)
            self.assertEqual(found.status, gc.PASS)  # CONTROL: the other runs are still judged
            self.assertIn("('NOHINTS', 1)", found.text)
            self.assertEqual(found.n, next(c for c in rs.step52_verdicts(sweep()) if c.id == check).n - 1)
        none = {plan: [dict(r, push_game=None, push_game_at=None) for r in plan_rows] for plan, plan_rows in sweep().items()}
        results = rs.step52_verdicts(none)
        for check in ("R5.PUSHING", "R5.NO_LOAFING", "R5.LOAF", "R5.BLOCKED", "R5.PUSH_PATHS_AGREE"):
            self.assertEqual(status(results, check), gc.VACUOUS, check)  # FAULT: before, a missing read passed as 0

    def test_no_loafing_by_the_game(self):
        bound = BOUNDS["LOAF_FRAMES_MAX"]
        self.assertEqual(status(rs.step52_verdicts(sweep()), "R5.NO_LOAFING"), gc.PASS)  # CONTROL
        at = [row("CH1", 1, push_ai=bound, push_game=bound)] + sweep()["CH1"][1:]
        self.assertEqual(status(self.results("CH1", at), "R5.NO_LOAFING"), gc.FAIL)  # FAULT: the game at the bound
        under = [row("CH1", 1, push_ai=bound - 1, push_game=bound - 1)] + sweep()["CH1"][1:]
        self.assertEqual(status(self.results("CH1", under), "R5.NO_LOAFING"), gc.PASS)  # CONTROL: one under
        ch2_1311 = [row("CH2", 1311, loaf_frames=4430, push_ai=760, push_game=760)]
        self.assertEqual(status(self.results("CH2", ch2_1311), "R5.NO_LOAFING"), gc.PASS)  # the AI windows not read

    def test_loaf_by_the_game(self):
        bound = BOUNDS["LOAF_FRAMES_MAX"]
        under = [row("LOAF", s, loaf_frames=bound + 1, seeing_productive=600) for s in (1, 2, 3)]
        self.assertEqual(status(self.results("LOAF", under), "R5.LOAF"), gc.FAIL)  # FAULT: every run under, by the game
        one_over = under[:2] + [row("LOAF", 3, push_ai=bound + 50, push_game=bound)]
        self.assertEqual(status(self.results("LOAF", one_over), "R5.LOAF"), gc.PASS)  # CONTROL: one run at the bound
        self.assertEqual(gc.CHECKS["R5.LOAF"].inputs, frozenset({"game"}))

    def test_pushing_by_the_game(self):
        bound = BOUNDS["PUSH_MAX"]
        game = [row("NOHINTS", 1, push_ai=bound, push_game=bound)] + sweep()["NOHINTS"][1:]
        self.assertEqual(status(self.results("NOHINTS", game), "R5.PUSHING"), gc.FAIL)  # FAULT
        ai = [row("NOHINTS", 1, push_ai=bound, push_game=10)] + sweep()["NOHINTS"][1:]
        results = self.results("NOHINTS", ai)
        self.assertEqual(status(results, "R5.PUSHING"), gc.PASS)  # the AI's record alone is no longer read ...
        self.assertEqual(status(results, "R5.PUSH_PATHS_AGREE"), gc.FAIL)  # ... it is judged against the game instead

    def test_blocked_by_the_game_and_its_reach_diagnostic(self):
        bound = BOUNDS["PUSH_MAX"]
        under = [row("BLOCKED", s, person_blocks=5, push_ai=bound + 9, push_game=640) for s in (1, 2)]
        self.assertEqual(status(self.results("BLOCKED", under), "R5.BLOCKED"), gc.FAIL)  # FAULT: all under by the game
        shape = [row("BLOCKED", 1, person_blocks=0, push_ai=978, push_game=640),  # 1310: met nobody, 640
                 row("BLOCKED", 2, person_blocks=0, push_ai=156288, push_game=156790)]
        results = self.results("BLOCKED", shape)
        self.assertEqual(status(results, "R5.BLOCKED"), gc.PASS)  # CONTROL: one over; the reach is not read
        self.assertEqual(status(results, "R5.BLOCKED_REACH"), gc.FAIL)  # its reach failed ...
        self.assertEqual(gc.CHECKS["R5.BLOCKED_REACH"].kind, gc.DIAGNOSTIC)
        self.assertEqual(gc.verdict([c for c in grade_sweep({**sweep(), "BLOCKED": shape})]), "PASS")  # ... uncounted
        # (the fix round's verifier: `>= bound` mutated to `> bound` survived) a push of exactly the bound is over it
        level = [row("BLOCKED", 1, person_blocks=0, push_ai=bound, push_game=bound),
                 row("BLOCKED", 2, person_blocks=0, push_ai=978, push_game=640)]
        self.assertEqual(status(self.results("BLOCKED", level), "R5.BLOCKED"), gc.PASS)  # CONTROL at equality

    def test_the_two_paths_agree_within_the_sampling_band(self):
        self.assertFalse(rs.push_apart(3950, 4030, 4000))  # LOAF 1310: the same stretch, apart only by sampling
        self.assertFalse(rs.push_apart(2950, 3040, 3000))  # the same near the loafing bound
        self.assertTrue(rs.push_apart(4000, 10, 4000))  # FAULT: one at the bound, the other far
        self.assertTrue(rs.push_apart(4300, 3500, 4000))  # FAULT: one inside the band, the other 12 % under
        self.assertFalse(rs.push_apart(1200, 1500, 4000))  # CONTROL: both under: the verdicts agree
        loaf_1310 = [row("LOAF", 1310, push_ai=3950, push_game=4030)] + sweep()["LOAF"][1:]
        self.assertEqual(status(self.results("LOAF", loaf_1310), "R5.PUSH_PATHS_AGREE"), gc.PASS)  # the shape on ledger #39
        loafing_only = [row("LOAF", 1, push_ai=2500, push_game=3500)] + sweep()["LOAF"][1:]
        self.assertEqual(status(self.results("LOAF", loafing_only), "R5.PUSH_PATHS_AGREE"), gc.FAIL)  # apart at 3000 only


class RegradeFidelityTests(unittest.TestCase):
    """V5: a chapter-2 kept folder is re-graded from ITS chapter-1 row (the start link: its seen tiles judge the draws);
    V26: a kept folder with no run.json is an error row that fails R5.PLANS_PLAYED, never skipped; V27: CONTROL_ARMS is
    exactly the re-sourced checks' named controls."""

    def write(self, root: Path, name: str, plan: str, play: dict, actions: list[dict]) -> None:
        folder = root / name
        folder.mkdir()
        (folder / rs.RUN_FILE).write_text(json.dumps({"plan": plan, "seed": 1307, "base": None, "personality": "Catcher",
                                                      "starter": "TREECKO", "play": play}), encoding="utf-8")
        (folder / "actions.jsonl").write_text("\n".join(json.dumps(a) for a in actions), encoding="utf-8")

    def test_a_chapter2_folder_is_graded_from_its_chapter1_row(self):
        with tempfile.TemporaryDirectory() as root:
            seen = Path(root) / "seen_tiles.json"
            seen.write_text(json.dumps(["0:9:1:1"]), encoding="utf-8")
            ch1 = {**RegradeTests.play(), "seen_file": str(seen)}
            draw = [{"decision": "goal", "action": "explore", "frame": 10, "reason": "a new place, ROUTE102: a look"},
                    {"decision": "watch", "frame": 900}]
            self.write(Path(root), "ai_step5_CH1_1307_a", "CH1", ch1, [{"decision": "goal", "action": "go", "frame": 0}])
            self.write(Path(root), "ai_step5_CH2_1307_b", "CH2", RegradeTests.play(), draw)
            kept = rs.kept_rows(Path(root), 300000)["CH2"][0]
            direct = rs.grade_run("CH2", 1307, "Catcher", "TREECKO", RegradeTests.play(), draw, 2.0, seen_in=str(seen))
        self.assertEqual((kept["place_draws"], kept["place_draws_judged"]), (1, 1))  # judged against chapter 1's tiles
        self.assertEqual(kept["_seen"], None)  # its own seen file (none); the start's is what judged it
        public = {k: v for k, v in kept.items() if not k.startswith("_")}
        self.assertEqual({k: public[k] for k in direct if not k.startswith("_")},
                         {k: v for k, v in direct.items() if not k.startswith("_")})

    def test_a_folder_without_its_run_file_is_an_error_row(self):
        with tempfile.TemporaryDirectory() as root:
            self.write(Path(root), "ai_step5_CH1_1307_a", "CH1", RegradeTests.play(), [])
            good = rs.kept_rows(Path(root), 300000)
            (Path(root) / "ai_step5_CH1_1308_broken").mkdir()
            rows = rs.kept_rows(Path(root), 300000)
        self.assertNotIn("?", good)
        self.assertEqual(rows["?"], [{"plan": "?", "seed": 0, "error": f"no {rs.RUN_FILE} in ai_step5_CH1_1308_broken"}])
        self.assertEqual(status([rs.plans_played(rows)], "R5.PLANS_PLAYED"), gc.FAIL)  # FAULT: the broken folder shows
        self.assertEqual(status([rs.plans_played(good)], "R5.PLANS_PLAYED"), gc.PASS)  # CONTROL

    def test_the_control_arms_are_exactly_the_named_controls(self):
        self.assertEqual(set(rs.CONTROL_ARMS), {
            ("R5.CH1_TRAINED", "CH1", "NOTRAIN"), ("R5.STALL", "CH1", "STALL1"), ("R5.STALL", "CH1", "STALL2"),
            ("R5.STALL", "CH1", "STALL3"), ("R5.OFF_BEELINE", "CH1", "ERRANDS_OFF"),
            ("R5.NO_SPEEDRUN_DICE", "CH1", "ERRANDS_OFF"), ("R5.LOSE3", "LOSE3", "STOPDEAD"),
            ("R5.PATIENCE", "PATIENCE", "PATIENCE_OLD"), ("R5.CH2_NOBATTLE", "CH2", "CH2_OFF"),
            ("R5.PUSHING", "CH1", "BLOCKED"), ("R5.NO_LOAFING", "CH1", "LOAF")})
        arms = {(c, k): s for c, k, s, _ in rs.control_arms(sweep())}
        self.assertEqual(arms[("R5.PATIENCE", "PATIENCE_OLD")], gc.FAIL)
        self.assertEqual((arms[("R5.PUSHING", "BLOCKED")], arms[("R5.NO_LOAFING", "LOAF")]), (gc.FAIL, gc.FAIL))

    def test_pooled_slices(self):
        # V7 (REPORTED text only): productive calm slices over calm slices, pooled; none read is None
        runs = [{"slices_game": {"calm": 10, "productive": 6}}, {"slices_game": {"calm": 30, "productive": 9}}, {}]
        self.assertEqual(rs.pooled_slices(runs), round(15 / 40, 4))
        self.assertIsNone(rs.pooled_slices([{}, {"slices_game": {"calm": 0, "productive": 0}}]))


class ShopCounterReadTests(unittest.TestCase):
    """R5: the harness reads the game's purchase counter GAME_STAT_SHOPPED (index 38 of save block 1's gameStats, XOR the
    save block 2 key) in `play_harness.story_truth`, past the 20 counters it read before."""

    def test_story_truth_reads_the_purchase_counter(self):
        from ai_player.gates import play_harness as ph
        sb1, sb2, key = 0x2000, 0x8000, 0x55AA55AA
        counters = [0] * 64
        counters[38], counters[11] = 7 ^ key, 3 ^ key

        def read_bytes(address: int, size: int) -> bytes:
            if address == sb1 + ph.SB1_GAME_STATS:
                return b"".join(v.to_bytes(4, "little") for v in counters)[:size]
            if address == sb2 + ph.SB2_KEY:
                return key.to_bytes(4, "little")
            return bytes(size)

        def read_symbol(name, offset=0, size=4):
            return {"gSaveBlock1Ptr": sb1, "gSaveBlock2Ptr": sb2}.get(name, 1).to_bytes(4, "little")

        memory = type(sys)("modules.memory")
        memory.read_symbol = read_symbol
        context = type("C", (), {"emulator": type("E", (), {"read_bytes": staticmethod(read_bytes)})()})()
        with mock.patch.dict(sys.modules, {"modules": type(sys)("modules"), "modules.memory": memory}):
            out = ph.story_truth(context)
        self.assertEqual((out["stats"]["shopped"], out["stats"]["captures"]), (7, 3))
        self.assertEqual(ph.STATS["shopped"], 38)


# ===================================================================================================== BUILDER 2 (items 10-17)
# The launcher's checks (`live_step5.py`) on synthetic launcher runs: every input a field of `Run`, no emulator.
from ai_player.gates import live_step2  # noqa: E402
from ai_player.gates import live_step5 as l5  # noqa: E402
from ai_player.gates import measure_step5 as ms  # noqa: E402

#: the purity checks of `live_step2.check_purity` and the one `live_step5.check_outcome` makes
PURITY_IDS = ("L5.PURITY_GATE", "L5.PURITY_CLEAN", "L5.PURITY_PRESSES", "L5.PURITY_FRAMES", "L5.PURITY_BREACHES",
              "L5.PURITY_ENDED", "L5.PURITY_OUTCOME", "L5.PURITY_PACKAGE")


def live_run(arm: str = "CH1T", reason: str | None = "play: done: ch1_pokedex reached", exit_code: int = 0,
             pad: str = "presses=5 frames=100", ai_presses: int = 10, real_frames: int = 100, after: dict | None = None,
             before: dict | None = None, records=(), driver_killed: bool = False) -> l5.Run:
    """One synthetic launcher run of arm `arm`, healthy for the purity checks unless an argument says otherwise. `reason` is
    the verdict file's exit reason (for a clean exit the BRAIN's own text) and `pad` the AI pad's own outcome line: the
    AI-written fields; `exit_code`, `driver_killed`, the instrument's counters and the truth reads are the harness's."""
    run = l5.Run(next(a for a in l5.ARMS if a.name == arm))
    run.stdout = f"[AI-GATE] exit=0 verdict=PASS package={live_step2.REPO / 'ai_player'}"
    run.ai_log = f"[AI-HANDS] outcome=done {pad}"
    run.exit_code, run.driver_killed = exit_code, driver_killed
    counters = {key: 0 for key in live_step2.BREACH_COUNTERS}
    counters.update(ai_presses=ai_presses, real_frames=real_frames)
    facts = {"exit_code": exit_code, "package_root": str(live_step2.REPO)}
    if reason is not None:
        facts["exit_reason"] = reason
    run.verdict = {"verdict": "CLEAN", "counters": counters, "facts": facts}
    run.after, run.before, run.records = after, before, list(records)
    return run


def checks_of(run: l5.Run, check_id: str) -> list:
    return [c for c in run.checks if c.id == check_id]


def one(run: l5.Run, check_id: str):
    found = checks_of(run, check_id)
    assert len(found) == 1, (check_id, [c.id for c in run.checks])
    return found[0]


def purity(run: l5.Run, target: str = "ch1_pokedex", proof: bool = True) -> l5.Run:
    """The purity checks as `live_step5.grade_common` and the graders make them: `check_purity` with no wanted outcome,
    then the outcome judged against the game's proof."""
    live_step2.check_purity(run, None)
    l5.check_outcome(run, target, proof, "the synthetic proof")
    return run


#: (item 10) the read's known answers, one per stop cause: (the run's harness fields, who, a word of its cause)
STOP_CAUSES = (({"driver_killed": True, "exit_code": -9}, "harness", "driver's own wall clock"),
               ({"exit_code": 124}, "harness", "launcher's wall clock"),
               ({"exit_code": l5.FRAME_BUDGET_EXIT}, "harness", "frame budget"),
               ({"exit_code": 3}, "other", "exit code 3"),
               ({"exit_code": 0}, "ai", "exited by itself"))


class PurityEndedTests(unittest.TestCase):
    """Item 10 (addendum row 28): L5.PURITY_ENDED is REPORTED from the HARNESS's own stop record, never the brain's text."""

    def test_each_stop_cause_reads_that_cause(self):
        for fields, by, cause in STOP_CAUSES:
            with self.subTest(by=by, cause=cause):
                run = purity(live_run(**fields))
                stop = l5.harness_stop(run)
                self.assertEqual(stop["by"], by)  # FAULT x4 (each harness cause is not `ai`) and CONTROL (exit 0)
                self.assertIn(cause, stop["cause"])
                ended = one(run, "L5.PURITY_ENDED")
                self.assertEqual((ended.kind, ended.inputs), (gc.REPORTED, frozenset({"harness"})))
                self.assertEqual(ended.status, gc.PASS if by == "ai" else gc.FAIL)
                self.assertIn(f"by {by}", ended.text)

    def test_the_brains_own_text_no_longer_moves_it(self):
        """The A1 verifier's case: an exit-0 run whose BRAIN reason names the wall clock read FAIL by the old text check."""
        run = purity(live_run(reason="wall-clock: the brain's own reason text"))
        ended = one(run, "L5.PURITY_ENDED")
        self.assertEqual(ended.status, gc.PASS)  # the harness says the AI exited by itself
        self.assertIn("the HARNESS's own stop record", ended.text)
        killed = purity(live_run(driver_killed=True, exit_code=-9))  # a healthy-looking reason, the driver's kill
        self.assertEqual(one(killed, "L5.PURITY_ENDED").status, gc.FAIL)

    def test_a_reported_line_by_the_driver_never_changes_the_verdict(self):
        run = live_run(driver_killed=True, exit_code=-9)
        run.checks.append(gc.grade("L5.BOUNDED", True, "BOUNDED: 1 real frames <= 2", 1, 1))
        run.checks.append(l5.ended_check(run, "ended by itself: (synthetic)"))
        self.assertEqual(run.checks[-1].status, gc.FAIL)
        self.assertTrue(run.passed)  # CONTROL: REPORTED never counts


def honest(**changes) -> dict:
    return {c.id: c for c in purity(live_run(**changes)).checks}


class PurityHonestyTests(unittest.TestCase):
    """Item 11 (addendum rows 16-17, RULING rows): THE AMENDMENT (a HONESTY truth half may be the harness) and the two
    purity counts as HONESTY: the AI pad's counts judged against the instrument's."""

    def test_the_amendment_admits_the_harness_as_the_truth_half(self):
        for inputs in ({"ai"}, {"harness"}, {"game", "harness"}):
            with self.subTest(inputs=inputs), self.assertRaises(gc.CheckError):  # FAULT: no AI claim, or no truth half
                gc.Check("X.H", gc.HONESTY, gc.PASS, 1, 1, inputs, "t", debt={})
        for inputs in ({"ai", "harness"}, {"ai", "game"}, {"ai", "game", "harness"}):
            self.assertEqual(gc.Check("X.H", gc.HONESTY, gc.PASS, 1, 1, inputs, "t", debt={}).inputs, inputs)  # CONTROL
        self.assertEqual(gc.rule_problems("X.H", gc.HONESTY, frozenset({"ai"}), {})[0][:5], "X.H: ")

    def test_the_purity_counts_are_honesty_and_judge_the_pad_against_the_instrument(self):
        healthy = honest()
        for key in ("L5.PURITY_PRESSES", "L5.PURITY_FRAMES"):
            self.assertEqual((healthy[key].kind, healthy[key].inputs, healthy[key].status),
                             (gc.HONESTY, frozenset({"ai", "harness"}), gc.PASS), key)  # CONTROL
        self.assertEqual(honest(pad="presses=6 frames=100")["L5.PURITY_PRESSES"].status, gc.FAIL)  # FAULT: 2 x 6 != 10
        self.assertEqual(honest(ai_presses=12)["L5.PURITY_PRESSES"].status, gc.FAIL)  # FAULT: the instrument's side
        self.assertEqual(honest(pad="presses=5 frames=99")["L5.PURITY_FRAMES"].status, gc.FAIL)  # FAULT: 99 != 100
        self.assertNotIn("L5.PURITY_PRESSES", gc.DEBT)
        self.assertNotIn("L5.PURITY_FRAMES", gc.DEBT)


class PurityOutcomeTests(unittest.TestCase):
    """Item 12 (addendum row 18): the brain's exit reason is a CLAIM judged BOTH WAYS against the game's proof."""

    def outcome(self, reason: str | None, proof: bool, **fields):
        return one(purity(live_run(reason=reason, **fields), proof=proof), "L5.PURITY_OUTCOME")

    def test_the_claim_and_the_proof_must_agree_both_ways(self):
        reached, stuck = "play: done: ch1_pokedex reached", "play: stuck: no progress for 41000 frames"
        self.assertEqual(self.outcome(reached, True).status, gc.PASS)  # CONTROL: reached, and the game shows it
        self.assertEqual(self.outcome(stuck, False).status, gc.PASS)  # CONTROL: a stop, and the game shows none
        self.assertEqual(self.outcome(reached, False).status, gc.FAIL)  # FAULT: "reached" with no proof
        self.assertEqual(self.outcome(stuck, True).status, gc.FAIL)  # FAULT: a proof under "stuck"
        other = self.outcome("play: done: ch2_wally reached", True)  # another target's claim is no claim of this one
        self.assertEqual(other.status, gc.FAIL)
        self.assertEqual((other.kind, other.inputs), (gc.HONESTY, frozenset({"ai", "game"})))

    def test_no_claim_is_vacuous_and_fails_the_verdict(self):
        for reason, fields in ((None, {}), ("play: done: ch1_pokedex reached", {"exit_code": 124})):
            with self.subTest(reason=reason, fields=fields):
                check = self.outcome(reason, True, **fields)
                self.assertEqual((check.status, check.n), (gc.VACUOUS, 0))  # the harness's stop is not the AI's word
                self.assertFalse(gc.counts_ok(check))  # unwaived

    def test_each_grader_judges_the_claim_against_its_own_proof_once(self):
        proofs = {name: 1 for name in ("RECEIVED_POKEDEX_FROM_BIRCH", "SYS_POKEDEX_GET", "ADVENTURE_STARTED",
                                       "DEFEATED_RIVAL_ROUTE103", "SET_WALL_CLOCK", "RESCUED_BIRCH", "SYS_POKEMON_GET")}
        for marks, want in ((proofs, gc.PASS), ({}, gc.FAIL)):
            with self.subTest(chapter=1, proof=bool(marks)):
                run = live_run("CH1T", after={"story": {"marks": marks}})
                l5.grade_CH1(run)
                self.assertEqual(one(run, "L5.PURITY_OUTCOME").status, want)
        wally = {"HIDE_PETALBURG_CITY_WALLYS_MOM": 1, "VAR_PETALBURG_GYM_STATE": 2}
        for marks, want in ((wally, gc.PASS), ({"VAR_PETALBURG_GYM_STATE": 1}, gc.FAIL)):
            with self.subTest(chapter=2, proof=bool(marks)):
                run = live_run("CH2", reason="play: done: ch2_wally reached", after={"story": {"marks": marks}})
                l5.grade_CH2(run)
                self.assertEqual(one(run, "L5.PURITY_OUTCOME").status, want)

    def test_the_old_constant_string_check_is_refused(self):
        """`check_purity` given a wanted outcome makes the old check (the AI's text against a constant), which no longer
        has a sample rule: it is refused, never typed HONESTY."""
        with self.assertRaisesRegex(gc.CheckError, "L5" + re.escape(".PURITY_OUTCOME: an untyped check")):
            live_step2.check_purity(live_run(), "done: ch1_pokedex reached")


def ch2_run(told: int = 1, money=(3000, 2000), balls=({"POKé BALL": 0}, {"POKé BALL": 5}), captures=(0, 2), new=2,
            heals=(0, 1), items=({}, {"ITEM_ROUTE102_POTION": 1}), shopped=(4, 5)) -> l5.Run:
    """A synthetic CH2 launcher run whose GAME reads are given: money and balls from start to end, the game's purchase
    counter GAME_STAT_SHOPPED (`shopped`; None leaves the read out), captures and new PIDs with the player's OT, POKéMON
    CENTER uses, item-ball flags; and `told` told purchases (the AI's word)."""
    def counters(i: int) -> dict:
        out = {"captures": captures[i], "used_pokecenter": heals[i]}
        if shopped[i] is not None:
            out["shopped"] = shopped[i]
        return out

    before = {"money": money[0], "balls": balls[0], "party_exp": [[1, "MUDKIP", 9, 9]], "boxes": [],
              "story": {"stats": counters(0), "items": items[0], "marks": {}}}
    after = {"money": money[1], "balls": balls[1], "player_tid": 7, "party_ot": [[1, 7]] + [[100 + i, 7] for i in range(new)],
             "boxes": [], "story": {"stats": counters(1), "items": items[1],
                                    "marks": {"HIDE_PETALBURG_CITY_WALLYS_MOM": 1, "VAR_PETALBURG_GYM_STATE": 2}}}
    records = [{"decision": "tell", "frame": 100 + i, "reason": "shop: done; POKé BALL in the bag (5 bought)"}
               for i in range(told)]
    run = live_run("CH2", reason="play: done: ch2_wally reached", after=after, before=before, records=records)
    l5.grade_CH2(run)
    return run


class ShoppedTests(unittest.TestCase):
    """Item 13 and the plan's (c): "it shopped" GRADED by the game alone (L5.SHOPPED_GAME); the told purchases HONESTY
    against that same read; no claim is a waived VACUOUS. (The fix round, R5) the read is the game's own purchase counter
    GAME_STAT_SHOPPED: the money-and-bag form misjudged a run that threw more balls than it bought, or won prize money
    (the ball-throw and prize-money arms below), and a whiteout's lost money plus an item-ball POKé BALL (the no-purchase
    arm). Sweep control: none, by the plan's rule (e): an ACHIEVEMENT (a before/after change at "at least one") of a
    launcher arm, which the sweep never runs; its null, a run with no purchase, is built here directly."""

    def statuses(self, **shape) -> tuple:
        run = ch2_run(**shape)
        game, told = one(run, "L5.SHOPPED_GAME"), one(run, "L5.SHOPPED")
        return game.status, told.status, gc.counts_ok(told)

    def test_a_told_purchase_the_game_shows_passes(self):
        run = ch2_run()
        self.assertEqual((one(run, "L5.SHOPPED_GAME").kind, one(run, "L5.SHOPPED").kind), (gc.GRADED, gc.HONESTY))
        self.assertEqual(one(run, "L5.SHOPPED_GAME").inputs, frozenset({"game"}))
        self.assertEqual(self.statuses(), (gc.PASS, gc.PASS, True))  # CONTROL

    def test_a_told_purchase_the_game_does_not_show_fails_both(self):
        self.assertEqual(self.statuses(shopped=(4, 4)), (gc.FAIL, gc.FAIL, False))  # FAULT: the counter unchanged
        # FAULT (the old form's false PASS): money fell at a whiteout and an item ball gave a POKé BALL, no purchase
        self.assertEqual(self.statuses(shopped=(4, 4), money=(3000, 1500), balls=({}, {"POKé BALL": 1})),
                         (gc.FAIL, gc.FAIL, False))

    def test_a_catcher_that_threw_more_balls_than_it_bought_still_shopped(self):
        # the ball-throw arm: bought 5 (money fell), threw 7 of 10 (the bag 10 -> 8): the old form read "did not shop"
        self.assertEqual(self.statuses(balls=({"POKé BALL": 10}, {"POKé BALL": 8})), (gc.PASS, gc.PASS, True))
        self.assertFalse(l5.game_shopped({"money": 3000, "balls": {"POKé BALL": 10}, "story": {"stats": {"shopped": 4}}},
                                         {"money": 2000, "balls": {"POKé BALL": 8}, "story": {"stats": {"shopped": 4}}})
                         ["shopped"])  # FAULT twin: the same bag and money with no purchase counted is no shopping

    def test_a_run_that_won_more_prize_money_than_it_spent_still_shopped(self):
        # the prize-money arm: money 3000 -> 4200 over the run (a trainer's prize after buying): the old form read "no"
        self.assertEqual(self.statuses(money=(3000, 4200)), (gc.PASS, gc.PASS, True))

    def test_no_claim_is_a_waived_vacuous_and_the_game_still_grades_it(self):
        self.assertEqual(self.statuses(told=0), (gc.PASS, gc.VACUOUS, True))  # shopped without saying so: no lie
        self.assertEqual(self.statuses(told=0, shopped=(4, 4)), (gc.FAIL, gc.VACUOUS, True))
        run = ch2_run(told=0, shopped=(4, 4))
        self.assertFalse(run.passed)  # FAULT: neither shopped nor claimed: the GAME check fails the arm

    def test_a_missing_read_is_vacuous_unwaived(self):
        for shape in ((None, 5), (4, None)):
            with self.subTest(shopped=shape):
                game = one(ch2_run(shopped=shape), "L5.SHOPPED_GAME")
                self.assertEqual((game.status, game.n), (gc.VACUOUS, 0))
                self.assertFalse(gc.counts_ok(game))
        # a truth with no counter, but money down and balls up (the old form's PASS): still nothing to judge
        game = one(ch2_run(shopped=(None, None)), "L5.SHOPPED_GAME")
        self.assertEqual((game.status, game.n), (gc.VACUOUS, 0))

    def test_the_reads_guard_a_missing_value(self):
        # F5 (the verifier's surviving mutant `else None` -> `else 0`): a missing read is None, never a count of 0
        self.assertIsNone(l5.balls_total({}))
        self.assertIsNone(l5.balls_total({"balls": "unreadable: KeyError"}))
        self.assertEqual(l5.balls_total({"balls": {"POKé BALL": 3, "GREAT BALL": 2}}), 5)  # CONTROL
        self.assertIsNone(l5.shop_count({"story": {"stats": {}}}))
        self.assertIsNone(l5.shop_count({"story": {"stats": {"shopped": "x"}}}))
        self.assertEqual(l5.shop_count({"story": {"stats": {"shopped": 0}}}), 0)  # CONTROL: a real 0 is a read
        self.assertEqual(l5.game_shopped({"story": {"stats": {"shopped": 0}}},
                                         {"story": {"stats": {"shopped": 1}}})["bought"], 1)


class AchievementTests(unittest.TestCase):
    """The plan's rule (e): L5.CAUGHT, L5.HEALED, L5.ITEMS (and L5.SHOPPED_GAME, above) are game-only ACHIEVEMENT checks,
    GRADED with no sweep control because each has a known-answer fault test both ways (here) and a caught mutant."""

    def test_caught(self):
        self.assertEqual(one(ch2_run(), "L5.CAUGHT").status, gc.PASS)  # CONTROL: +2 captures, 2 new PIDs
        self.assertEqual(one(ch2_run(captures=(0, 0), new=0), "L5.CAUGHT").status, gc.FAIL)  # FAULT: none
        self.assertEqual(one(ch2_run(captures=(0, 2), new=0), "L5.CAUGHT").status, gc.FAIL)  # FAULT: no new PID

    def test_healed(self):
        self.assertEqual(one(ch2_run(), "L5.HEALED").status, gc.PASS)  # CONTROL
        self.assertEqual(one(ch2_run(heals=(1, 1)), "L5.HEALED").status, gc.FAIL)  # FAULT

    def test_items(self):
        self.assertEqual(one(ch2_run(), "L5.ITEMS").status, gc.PASS)  # CONTROL: CH2 pre-registered >= 1
        self.assertEqual(one(ch2_run(items=({}, {})), "L5.ITEMS").status, gc.FAIL)  # FAULT: no item ball
        self.assertEqual(one(ch2_run(items=({"A": 1}, {"A": 1})), "L5.ITEMS").status, gc.FAIL)  # FAULT: held before

    def test_each_is_graded_by_the_game_alone(self):
        for key in ("L5.CAUGHT", "L5.HEALED", "L5.ITEMS", "L5.SHOPPED_GAME"):
            self.assertEqual((gc.CHECKS[key].kind, gc.CHECKS[key].inputs), (gc.GRADED, frozenset({"game"})), key)


# ------------------------------------------------------------------------------------------------ item 14: the REPORTED rows
REPORTED_ROWS = ("R5.CH1_SPINS", "R5.CH1_REST_RULE", "R5.DEADREST", "R5.SEED_DIVERGENCE", "R5.OFF_MOVES_DIVERGENCE",
                 "R5.NO_SPEEDRUN", "R5.CH1_YIELD", "R5.CH2_YIELD")


def play_data(seed: int = 0) -> dict:
    """A synthetic PLAY json (what `play_harness.play` writes and `grade_run` reads): every game read the REPORTED forms use."""
    return {
        "frames": 5000, "reason": "play: done", "story": {
            "frames": 5000, "changes": [], "battles": [], "captures": [[0, 0], [2500, 1]], "item_flags": [[0, 0]]},
        "places": {"every": 10, "battles": [[1100, 1890]], "stays": [[0, "0:9"], [3000, "0:16"], [4200, "0:9"]],
                   "new_tiles": [[50, 9], [3100, 3]], "texts": [[4100, "x", True]], "moves": [[0, "0:9", 1, 1]],
                   "push": {"longest": [0, 0, 0, 0]}},
        "game_reads": {"presses": {"spins": 2 + seed, "moves": 40, "log": []},
                       # two starts under the Story's heal_below 0.6; the second is a TRAINER's (its end says so), which a
                       # roam's rest rule does not cover: 1 counted
                       "battle_hp": {"starts": [[1100, [["MUDKIP", 9, 5, 30]]], [4500, [["MUDKIP", 9, 6, 30]]]],
                                     "ends": [[1890, "won", False, None], [4800, "won", True, None]]},
                       "tiles": {"start": [0, "0:9", 1, 1], "steps": [[10, "0:9", 2, 1, "Normal"]]}}}


def as_measured_run(data: dict, personality: str = "Story") -> dict:
    """The same run as `measure_step5.load_run` returns it (the measure reads the same files)."""
    return {"plan": "CH1", "seed": 1, "personality": personality, "play": data, "places": data["places"],
            "reads": data["game_reads"], "actions": []}


class ReportedFormTests(unittest.TestCase):
    """Item 14 (addendum rows 20-27): REPORTED, each printing its GAME form with its controls beside it; the old AI-form
    outcome is its status, which never counts."""

    def test_the_rows_are_reported_and_out_of_the_debt(self):
        for key in REPORTED_ROWS:
            self.assertEqual(gc.CHECKS[key].kind, gc.REPORTED, key)
            self.assertIn("game", gc.CHECKS[key].inputs, key)
            self.assertNotIn(key, gc.DEBT, key)

    def test_a_failing_shaped_reported_row_leaves_the_verdict_and_typed_graded_it_would_fail(self):
        rows = sweep()
        for r in rows["CH1"]:
            r["seeing_productive"] = 500  # CH1's yield at LOAF's (600 of 3000 is under YIELD_RATE_MIN)
        results = grade_sweep(rows)
        self.assertEqual(status(results, "R5.CH1_YIELD"), gc.FAIL)
        self.assertEqual(gc.verdict(results), "PASS")  # CONTROL: the typing keeps it out of the verdict
        graded = {**gc.CHECKS, "R5.CH1_YIELD": gc.Spec(gc.GRADED, frozenset({"game"}), gc.CHECKS["R5.CH1_YIELD"].title)}
        with mock.patch.dict(gc.CHECKS, graded):
            self.assertEqual(gc.verdict(grade_sweep(rows)), "FAIL")  # FAULT: the same row typed GRADED fails it

    def test_every_reported_row_prints_its_game_form_beside_its_controls(self):
        rows = sweep()
        game = {"spins_game": (3, 100), "under_heal_game": 2, "_maps": ["0:9", "0:16"],
                "slices_game": {"calm": 10, "productive": 6, "yield": 0.6}}
        for plan_rows in rows.values():
            for r in plan_rows:
                r.update(game)
        results = {c.id: c for c in grade_sweep(rows)}
        words = {"R5.CH1_SPINS": "CH1 [(1, (3, 100)),", "R5.CH1_REST_RULE": "DEADREST [(1, 2),",
                 "R5.DEADREST": "CH1 [(1, 2),", "R5.SEED_DIVERGENCE": "ERRANDS_OFF [(1, 3),",
                 "R5.OFF_MOVES_DIVERGENCE": "ERRANDS_OFF [(1, 2),", "R5.NO_SPEEDRUN": "pooled CH1/ERRANDS_OFF 1.167",
                 "R5.CH1_YIELD": "LOAF [(1, 0.6),", "R5.CH2_YIELD": "CH2_OFF [(1, 0.6),"}
        for key, word in words.items():
            with self.subTest(key):
                text = results[key].text
                self.assertIn("REPORTED since the 5.3 re-sourcing", text)
                self.assertIn(f"addendum row {20 + REPORTED_ROWS.index(key)}", text)
                self.assertIn(word, text)
        self.assertIn("pooled 0.03", results["R5.CH1_SPINS"].text)  # 4 seeds x 3 / 400
        self.assertIn("pooled 8", results["R5.CH1_REST_RULE"].text)
        self.assertIn("mean pair distance 0.0", results["R5.OFF_MOVES_DIVERGENCE"].text)

    def test_the_game_reads_equal_the_measures(self):
        data = play_data()
        run = as_measured_run(data, "Story")
        self.assertEqual(rs.spins_by_game(data), (2, 40))
        self.assertEqual(rs.started_under_heal(data, "Story"), ms.battles_below(run)["below_own"])
        self.assertEqual(rs.started_under_heal(data, "Story"), 1)  # 5/30 under 0.6; the trainer's start is not counted
        self.assertEqual(rs.map_order(data), ms.map_order(run))
        counts = ms.slice_counts(ms.slices(run))
        self.assertEqual(rs.slice_yield(data), {"calm": counts["calm"], "productive": counts["productive"],
                                                "yield": counts["yield"]})
        self.assertEqual(rs.slice_yield(data), {"calm": 4, "productive": 4, "yield": 1.0})
        a, b = {"personality": "Story", "_stood": {"x", "y"}, "_maps": ["a", "b"]}, \
            {"personality": "Story", "_stood": {"y", "z"}, "_maps": ["a", "c", "d"]}
        for key in ("_stood", "_maps"):
            self.assertEqual(rs.pairs_divergence([a, b], key),
                             ms._pairs_divergence([{**a, key: a[key]}, {**b, key: b[key]}], key), key)

    def test_a_battle_record_that_does_not_alternate_is_no_number(self):
        data = play_data()
        data["game_reads"]["battle_hp"]["starts"].insert(1, [1200, [["MUDKIP", 9, 5, 30]]])  # a start counted twice
        self.assertIsNone(rs.started_under_heal(data, "Story"))  # FAULT: never a count
        self.assertIsNone(ms.battles_below(as_measured_run(data))["below_own"])

    def test_a_slice_with_nothing_new_is_calm_and_not_productive(self):
        data = play_data()
        data["places"].update(new_tiles=[], texts=[], stays=[[0, "0:9"]])
        data["story"].update(captures=[[0, 0]])
        self.assertEqual(rs.slice_yield(data), {"calm": 4, "productive": 0, "yield": 0.0})  # FAULT: loafing reads 0
        data["places"]["new_tiles"] = [[2100, rs.YIELD_TILES - 1]]
        self.assertEqual(rs.slice_yield(data)["productive"], 0)  # under YIELD_TILES new tiles is not productive
        data["places"]["new_tiles"] = [[2100, rs.YIELD_TILES]]
        self.assertEqual(rs.slice_yield(data)["productive"], 1)  # CONTROL

    def test_grade_run_records_the_reported_forms(self):
        out = rs.grade_run("CH1", 1, "Story", "MUDKIP", play_data(), [], 1.0)
        self.assertEqual((out["spins_game"], out["under_heal_game"], out["_maps"], out["slices_game"]["calm"]),
                         ((2, 40), 1, ["0:9", "0:16", "0:9"], 4))


# ---------------------------------------------------------------------------------------------- item 15: the DIAGNOSTIC rows
DIAGNOSTIC_ROWS = ("L5.PRESS_GATES", "L5.A_KINDS", "L5.BLIND", "L5.HAS_GOAL", "L5.STALL", "L5.NEW_PLACE", "L5.TRAINED",
                   "L5.REST_RULE", "L5.OWN_LOSSES", "L5.OWN_TRAINING", "L5.SPINS")


class DiagnosticTests(unittest.TestCase):
    """Item 15 (addendum rows 29-39): the kind and the inputs re-typed, nothing else."""

    def test_the_rows_are_diagnostic_with_their_dropped_property(self):
        for key in DIAGNOSTIC_ROWS:
            spec = gc.CHECKS[key]
            self.assertEqual((spec.kind, spec.inputs, spec.since), (gc.DIAGNOSTIC, frozenset({"ai"}), gc.RESOURCING), key)
            self.assertTrue(spec.dropped, key)
            self.assertNotIn(key, gc.DEBT, key)

    def test_a_failing_diagnostic_row_never_changes_a_live_verdict_and_says_so(self):
        run = live_run(after={"story": {"marks": {}}})
        run.check(True, "BOUNDED: 1 real frames <= 2", "L5.BOUNDED")
        run.check(False, "ROAMING, NOT SPINNING: 9 spins over 10 training steps", "L5.SPINS")
        self.assertTrue(run.passed)  # CONTROL: a DIAGNOSTIC failure never counts
        lines = gc.evidence_lines(run.checks)
        self.assertIn("NO LONGER GRADED L5.SPINS (FAIL, DIAGNOSTIC since 5.3 re-sourcing): ", "\n".join(lines))
        self.assertNotIn("NO LONGER GRADED L5.BOUNDED", "\n".join(lines))  # a GRADED one is no dropped property

    def test_re_typed_graded_one_refuses_the_import(self):
        import dataclasses
        for key in DIAGNOSTIC_ROWS:
            with self.subTest(key), self.assertRaises(gc.CheckError):  # FAULT: GRADED, reads ai, no debt row
                gc.validate({**gc.CHECKS, key: dataclasses.replace(gc.CHECKS[key], kind=gc.GRADED, dropped="")},
                            gc.DEBT, gc.WAIVERS)

    def test_the_healthy_sweep_verdict_is_unchanged_by_the_re_typing(self):
        results = grade_sweep(sweep())
        self.assertEqual(gc.verdict(results), "PASS")  # CONTROL (the sweep has no L5 check: nothing of it moves)
        self.assertEqual([c.id for c in results if c.id.startswith("L5.")], [])


# ------------------------------------------------------------------------------------------------ item 17: the debt file
#: (the fix round) the last 5 rows, the addendum's items 5, 8 and 9, built here: re-sourced to the GAME
FIX_ROUND_PAID = ("R5.CH2_NOBATTLE", "R5.NO_LOAFING", "R5.LOAF", "R5.PUSHING", "R5.BLOCKED")
#: ALL 39 rows of A2's debt: builder 1's 10, builder 2's 24 and the fix round's 5
DEBT_PAID = ("R5.CH1_TRAINED", "R5.NOTRAIN_TRAINED_CHECK", "R5.STALL", "R5.STALL1", "R5.STALL2", "R5.STALL3",
             "R5.OFF_BEELINE", "R5.NO_SPEEDRUN_DICE", "R5.LOSE3", "R5.PATIENCE") + REPORTED_ROWS + DIAGNOSTIC_ROWS + (
    "L5.PURITY_PRESSES", "L5.PURITY_FRAMES", "L5.PURITY_ENDED", "L5.PURITY_OUTCOME", "L5.SHOPPED") + FIX_ROUND_PAID


class DebtTests(unittest.TestCase):
    """Item 17: `b1_debt.json` ends EMPTY, and the refusal holds both ways on the real table and the real file."""

    def test_the_debt_is_empty_and_no_graded_check_reads_the_ai(self):
        self.assertEqual(len(DEBT_PAID), 39)
        self.assertEqual(gc.DEBT, {})  # EMPTY
        self.assertEqual({k for k, s in gc.CHECKS.items() if s.kind == gc.GRADED and "ai" in s.inputs}, set())
        for key in FIX_ROUND_PAID:
            self.assertEqual((gc.CHECKS[key].kind, gc.CHECKS[key].inputs), (gc.GRADED, frozenset({"game"})), key)

    def test_a_debt_row_for_a_check_that_no_longer_reads_ai_as_graded_is_refused(self):
        gc.validate(gc.CHECKS, gc.DEBT, gc.WAIVERS)  # CONTROL: as they stand
        for key in DEBT_PAID:
            with self.subTest(key), self.assertRaisesRegex(gc.CheckError, "b1_debt" + re.escape(f".json lists '{key}'")):
                gc.validate(gc.CHECKS, {**gc.DEBT, key: {"ai_input": "x", "plan": "y"}}, gc.WAIVERS)  # FAULT: stale

    def test_a_graded_check_still_reading_ai_without_its_row_is_refused(self):
        # the other way: each fix-round check re-typed back to reading the AI, with the real (empty) debt, is refused;
        # listed in the debt, it constructs (CONTROL)
        for key in FIX_ROUND_PAID:
            reads_ai = {**gc.CHECKS, key: dataclasses.replace(gc.CHECKS[key], inputs=frozenset({"game", "ai"}))}
            with self.subTest(key), self.assertRaisesRegex(gc.CheckError, re.escape(f"{key}: a GRADED check")):
                gc.validate(reads_ai, gc.DEBT, gc.WAIVERS)  # FAULT
            gc.validate(reads_ai, {key: {"ai_input": "x", "plan": "y"}}, gc.WAIVERS)  # CONTROL


# ====================================================== STAGE B STEP 1 (2026-10-27): where the STOP checks get their runs
#: LOSE3's plan list before stage B step 1: LOSE3 was in `NO_PHASE2` (the "before the change" arm of these tests)
OLD_NO_PHASE2 = ("LOSE3",) + rs.NO_PHASE2
#: the Catcher seeds among 1-6 (`plan_of`): LOSE3 plays only there (`PLAN_PERSONALITY`)
CATCHER = (2, 5)


def lose3_base(seed: int) -> dict:
    """A phase-1 LOSE3 run that reached its third loss (the harness's max_losses 3)."""
    return row("LOSE3", seed, "Catcher", reason="play: stuck: 3 battles lost (MAX_LOSSES 3)", losses_game=3, losses_ai=3,
               losses_told=3, first_loss_f=600, last_loss_f=1000, frames=1600, max_losses=3)


def stop_replay(seed: int, base: str = "LOSE3", first: int = 600) -> dict:
    """STOP's replay (CAP1): it ends at its first loss, its report, told and game losses 1, the harness's max_losses 1."""
    return row("STOP", seed, "Catcher", base=base, reason=rs.STOP_REASON, losses_game=1, losses_ai=1, losses_told=1,
               first_loss_f=first, last_loss_f=first, frames=first + 1200, max_losses=1)


def dead_replay(seed: int, base: str = "LOSE3", first: int = 600, losses: int = 4) -> dict:
    """STOPDEAD's replay (CAP1 + G46): the loop's count removed, so it never stops on its losses and goes on (LOSE3's
    decider keeps losing: the game's losses past the cap), its report and told losses 0."""
    return row("STOPDEAD", seed, "Catcher", base=base, reason="play: stuck: no progress for 120000 frames",
               losses_game=losses, losses_ai=0, losses_told=0, first_loss_f=first, last_loss_f=first + 8000,
               frames=first + 130000, max_losses=1)


def no_natural_loss(replays: bool = True) -> dict[str, list[dict]]:
    """A sweep with NO natural loss (the shape of ledger #40): CH1 on seeds 1-6 never lost; LOSE3 on the Catcher seeds lost
    3 times each (forced); with `replays`, phase 2's STOP and STOPDEAD replays of exactly those LOSE3 runs."""
    out = {"CH1": [row("CH1", s, rs.plan_of(s)[0]) for s in range(1, 7)], "LOSE3": [lose3_base(s) for s in CATCHER]}
    out["STOP"] = [stop_replay(s) for s in CATCHER] if replays else []
    out["STOPDEAD"] = [dead_replay(s) for s in CATCHER] if replays else []
    return out


def check_of(rows, check_id: str):
    found = [c for c in rs.stop_verdicts(rows) + rs.step51_verdicts(rows) if c.id == check_id]
    assert len(found) == 1, (check_id, [c.id for c in found])
    return found[0]


class StopRunsTests(unittest.TestCase):
    """Stage B step 1 (`ai-research-notes/2026-10-26-stageB-stop-runs-design.md`, DECISION 2026-10-27, option B): phase 2's
    STOP and STOPDEAD replay LOSE3's runs too (LOSE3 left `NO_PHASE2`), beside every natural loss, through ONE rule
    (`phase2_lost`) that `main` plays and `stop_verdicts` grades; the replays are matched by identity; the texts count
    replays by source. Mutants (each run in a scratch copy with fresh bytecode): LOSE3 back into `NO_PHASE2`; `main`'s
    `phase2_lost` call deleted; `stop_verdicts`' `phase2_lost` call deleted; the identity match back to a count."""

    def test_a_sweep_with_no_natural_loss_gives_stop_and_stopdead_their_runs(self):
        rows = no_natural_loss()
        self.assertEqual(rs.phase2_lost(rows), [("LOSE3", 2), ("LOSE3", 5)])
        for check_id in ("R5.STOP", "R5.STOPDEAD"):
            check = check_of(rows, check_id)
            self.assertEqual((check.status, check.n), (gc.PASS, 2), check.text)  # CONTROL: both have their runs
        # FAULT (before the change): LOSE3 in NO_PHASE2, so phase 2 chose nothing and played nothing: both VACUOUS
        with mock.patch.object(rs, "NO_PHASE2", OLD_NO_PHASE2):
            before = no_natural_loss(replays=False)
            self.assertEqual(rs.phase2_lost(before), [])
            for check_id in ("R5.STOP", "R5.STOPDEAD"):
                check = check_of(before, check_id)
                self.assertEqual((check.status, check.n), (gc.VACUOUS, 0), check.text)

    def test_the_natural_loss_replays_are_unchanged(self):
        # CONTROL: on the healthy sweep the natural losses the OLD rule chose are all still chosen, in the same order,
        # and the only new ones are LOSE3's
        rows = sweep()
        rows["DEADREST"][2].update(losses_game=1, losses_ai=1, losses_told=1, first_loss_f=7000, last_loss_f=7000)
        with mock.patch.object(rs, "NO_PHASE2", OLD_NO_PHASE2):
            old = rs.phase2_lost(rows)
        new = rs.phase2_lost(rows)
        self.assertEqual(old, [("CH1", 1), ("DEADREST", 3)])
        self.assertEqual([k for k in new if k[0] not in rs.FORCED_LOSS_PLANS], old)
        self.assertEqual([k for k in new if k[0] in rs.FORCED_LOSS_PLANS], [("LOSE3", 2), ("LOSE3", 5)])
        # the never-replayed plans stay out: a chapter-2 or curiosity-control run that lost is not chosen
        rows["CH2"][0].update(losses_game=1)
        rows["LOAF"][0].update(losses_game=1)
        self.assertEqual(rs.phase2_lost(rows), new)
        # the real code's R5.STOP passes and R5.STOPDEAD reads as the control it is, natural and forced replays together
        rows = sweep()
        for check_id in ("R5.STOP", "R5.STOPDEAD"):
            check = check_of(rows, check_id)
            self.assertEqual((check.status, check.n), (gc.PASS, 3), check.text)
        # FAULT: a STOPDEAD replay that STOPPED (the count not removed) fails it; a STOP replay that went on fails STOP
        stopped = sweep()
        stopped["STOPDEAD"][1] = {**stop_replay(2), "plan": "STOPDEAD"}
        self.assertEqual(check_of(stopped, "R5.STOPDEAD").status, gc.FAIL)
        went_on = sweep()
        went_on["STOP"][2] = {**dead_replay(5), "plan": "STOP"}
        self.assertEqual(check_of(went_on, "R5.STOP").status, gc.FAIL)

    def test_a_sweep_played_before_the_rule_is_judged_by_its_own_rule(self):
        # (stage B step 1's verifier) a sweep played with LOSE3 kept out of phase 2: its LOSE3 runs lost and were never
        # replayed. The new rule FAILS it for replays it was never asked to play; its own rule (`forced` False) does not
        rows = no_natural_loss(replays=False)
        for check_id in ("R5.STOP", "R5.STOPDEAD"):
            self.assertEqual(check_of(rows, check_id).status, gc.FAIL)  # the new rule on an old sweep
            old = [c for c in rs.stop_verdicts(rows, forced=False) if c.id == check_id][0]
            self.assertEqual((old.status, old.n), (gc.VACUOUS, 0), old.text)  # its own rule: nothing it had to replay
            self.assertIn("RE-GRADE of a sweep played before", old.text)
        self.assertEqual(rs.phase2_lost(rows, forced=False), [])
        self.assertEqual(rs.phase2_lost(no_natural_loss()), [("LOSE3", 2), ("LOSE3", 5)])  # CONTROL: the default
        # and through the whole grader, as `regrade` calls it: `verdicts` hands `forced` on to the stop checks
        summary = {plan: rs.summarise(plan, sorted(plan_rows, key=lambda r: r["seed"])) for plan, plan_rows in rows.items()}
        whole = {c.id: c.status for c in rs.verdicts(summary, rows, False)}
        self.assertEqual((whole["R5.STOP"], whole["R5.STOPDEAD"]), (gc.VACUOUS, gc.VACUOUS))

    def test_the_replays_are_matched_by_identity_not_count(self):
        # FAULT: LOSE3 5's replay is missing and a run that never lost (CH1 3) was replayed instead: the COUNT is right
        # (2 of 2), the identity is not
        rows = no_natural_loss()
        for plan in ("STOP", "STOPDEAD"):
            rows[plan] = [r for r in rows[plan] if r["seed"] != 5] + [
                {**(stop_replay if plan == "STOP" else dead_replay)(3, base="CH1"), "personality": "Trainer"}]
            check = check_of(rows, f"R5.{plan}")
            self.assertEqual((check.status, check.n), (gc.FAIL, 2), check.text)
            self.assertIn("not replayed: [('LOSE3', 5)]", check.text)
            self.assertIn("replayed without a phase-1 loss: [('CH1', 3)]", check.text)
        # CONTROL: the right runs, in any order, pass
        rows = no_natural_loss()
        rows["STOP"].reverse()
        self.assertEqual(check_of(rows, "R5.STOP").status, gc.PASS)

    def test_the_texts_count_the_replays_by_source(self):
        text = check_of(no_natural_loss(), "R5.STOP").text
        self.assertIn("by source: 0 NATURAL (the real decider lost), 2 FORCED by LOSE3's decider (the stop exercised on "
                      "forced wild losses ONLY)", text)
        text = check_of(sweep(), "R5.STOPDEAD").text
        self.assertIn("by source: 1 NATURAL (the real decider lost), 2 FORCED by LOSE3's decider)", text)

    def test_lose3s_control_arm_fails_with_two_or_more_stopdead_runs(self):
        def arm(rows):
            found = [a for a in rs.control_arms(rows) if a[:2] == ("R5.LOSE3", "STOPDEAD")]
            self.assertEqual(len(found), 1)
            return found[0]

        rows = no_natural_loss()
        self.assertEqual(check_of(rows, "R5.LOSE3").status, gc.PASS)  # CONTROL: the real cap stops LOSE3 itself
        _, _, state, text = arm(rows)
        self.assertEqual(state, gc.FAIL, text)  # the control FAILS, on its own 2 runs (floor 2)
        self.assertIn("(2 of 2; floor 2 such runs", text)
        self.assertIn("off: [2, 5]", text)
        # FAULT (before the change): with no natural loss STOPDEAD played nothing, so the control arm did not even run;
        # with ONE natural loss (ledger #39's DEADREST 1314) it read VACUOUS, 1 run against the floor of 2
        with mock.patch.object(rs, "NO_PHASE2", OLD_NO_PHASE2):
            self.assertEqual([a for a in rs.control_arms(no_natural_loss(replays=False)) if a[0] == "R5.LOSE3"], [])
            one = no_natural_loss(replays=False)
            one["CH1"][0].update(losses_game=1, losses_ai=1, losses_told=1, first_loss_f=5000, last_loss_f=5000)
            one["STOPDEAD"] = [dead_replay(1, base="CH1", first=5000, losses=1)]
            self.assertEqual(arm(one)[2], gc.VACUOUS)


class StopRunsMainTests(unittest.TestCase):
    """`main` plays phase 2 from `phase2_lost`: a sweep with no natural loss replays LOSE3's runs in both STOP plans, each in
    a copy with LOSE3's mutant AND the STOP plan's edits (nothing played: `run_chain`, `run_one` and `copy_with` faked)."""

    def drive(self, rows: dict[str, list[dict]]) -> tuple[int, str, list, list]:
        import io
        from contextlib import redirect_stdout

        from ai_player.gates import disk_budget, ledger, provenance

        class Tree:
            stats, digest, moved, moves = {}, "d", False, []

            def check(self, label):
                return True

            def seal(self, verdict):
                return verdict, "FROZEN TREE: unchanged (faked)"

        class Folders:
            def __init__(self, tag):
                pass

            def tidy(self, failing, keep_all=False):
                return "SWEEP FOLDERS: (faked)"

        played, made = [], []

        def chain(plan, seed, frames, target, root, chapter2):
            return [dict(r) for r in rows[plan] if r["seed"] == seed]

        def one(plan, seed, frames, target, root, base):
            played.append((plan, base, seed))
            return dict(next(r for r in rows[plan] if r["seed"] == seed and r.get("base") == base))

        def copy(names):
            made.append(list(names))
            return Path(tempfile.gettempdir()) / f"stopruns_fake_copy_{len(made)}"  # never created; rmtree ignores it

        folder = Path(tempfile.mkdtemp(prefix="stopruns_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        argv = ["rate_step5.py", "--purpose", "development", "--first-seed", "1", "--seeds", "6", "--plans",
                "CH1,LOSE3,STOP,STOPDEAD", "--workers", "1", "--evidence-tag", "stopruns"]
        with mock.patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()), \
                mock.patch.object(disk_budget, "preflight", lambda: (True, "DISK: (faked)")), \
                mock.patch.object(disk_budget, "SweepFolders", Folders), \
                mock.patch.object(provenance, "watch", lambda repo, explicit=True: Tree()), \
                mock.patch.object(provenance, "line_digest", lambda code: "x"), \
                mock.patch.object(ledger, "begin", lambda *a, **k: ({"id": 0}, ["LEDGER: (faked)"])), \
                mock.patch.object(ledger, "finish", lambda *a, **k: None), \
                mock.patch.object(rs, "provenance", lambda repo: "code (faked)"), \
                mock.patch.object(rs, "snapshot_tree", lambda repo: "(faked)"), \
                mock.patch.object(rs, "keep_earlier", lambda out: None), \
                mock.patch.object(rs, "EVIDENCE_DIR", folder), mock.patch.object(rs, "REPO", folder), \
                mock.patch.object(rs, "run_chain", chain), mock.patch.object(rs, "run_one", one), \
                mock.patch.object(rs, "copy_with", copy), \
                mock.patch.object(rs, "_FOLDERS", None), mock.patch.object(rs, "_TREE", None):
            # (the verifier's weak proof) `main` sets the module globals `_FOLDERS` and `_TREE`: patched, so the fakes do
            # not leak into later tests in the same process
            code = rs.main()
        evidence = next(folder.glob("*-stopruns-RATE.txt")).read_text(encoding="utf-8")
        return code, evidence, sorted(played), made

    def test_a_sweep_with_no_natural_loss_plays_lose3s_replays(self):
        code, evidence, played, made = self.drive(no_natural_loss())
        self.assertEqual(played, [("STOP", "LOSE3", 2), ("STOP", "LOSE3", 5), ("STOPDEAD", "LOSE3", 2),
                                  ("STOPDEAD", "LOSE3", 5)])
        self.assertEqual(made, [["LOSE3"], ["LOSE3", "CAP1"], ["LOSE3", "CAP1", "G46"]])
        self.assertIn("PHASE 2: the runs of phase 1 the game recorded a battle LOST in: [('LOSE3', 2), ('LOSE3', 5)]; "
                      "plans ['STOP', 'STOPDEAD']", evidence)
        for check_id in ("R5.STOP", "R5.STOPDEAD"):
            self.assertIn(f"  [PASS] {check_id} HONESTY n/floor 2/1 ", evidence)
        # (the verdict itself is not asserted: CH1 without NOTRAIN cannot pass R5.CH1_TRAINED's pairing, by design)
        # FAULT (before the change): LOSE3 in NO_PHASE2, nothing replayed, both VACUOUS, the verdict FAIL
        with mock.patch.object(rs, "NO_PHASE2", OLD_NO_PHASE2):
            code, evidence, played, made = self.drive(no_natural_loss())
        self.assertEqual(played, [])
        self.assertIn("PHASE 2: the runs of phase 1 the game recorded a battle LOST in: none", evidence)
        for check_id in ("R5.STOP", "R5.STOPDEAD"):
            self.assertIn(f"  [VACUOUS] {check_id} HONESTY n/floor 0/1 ", evidence)


#: (STAGE B step 3, 2026-10-27) the FINAL value of every graded bound the re-sourced checks read, as stage B set it from
#: development numbers alone (`ai-research-notes/2026-10-27-step5.3-stageB-bounds.md`); STOP_WITHIN is a module constant
STAGE_B_FINAL = {"TRAINED_GRASS_STORY_MIN": 70, "TRAINED_RATIO_TRAINER_MIN": 1.3, "TRAINED_RATIO_CATCHER_MIN": 1.1,
                 "TRAINED_SHARE_MIN": 0.5, "AWAIT_MAX": 300, "STALL_ARM_HITS_MIN": 1, "OFF_SEEDS_MIN": 0.6,
                 "OFF_RATIO_MIN": 1.3, "NOBATTLE_RATIO_MIN": 1.05, "NOBATTLE_SEEDS_MIN": 0.6, "LOSE3_REACH_MIN": 2,
                 "PATIENCE_REACHED_MIN": 0.6, "CH2_NOBATTLE_RATIO_MIN": 1.05, "CH2_NOBATTLE_SEEDS_MIN": 0.7,
                 "PUSH_MAX": 4000, "BLOCKED_HITS_MIN": 1, "LOAF_FRAMES_MAX": 3000, "LOAF_FAILS_RUNS_MIN": 1,
                 "PUSH_AGREE_BAND": 0.05, "STOP_WITHIN": 6000}
#: (key, the real code's WORST development number, the named control's NEAREST, the real code's side): "low" = the real
#: code is under the bound and the control at or over it (control <= ... the real code < bound <= control); "high" = the
#: real code at or over it and the control under it (control < bound <= real). Ledger #39's re-grade unless noted:
STAGE_B_PLACED = (
    ("TRAINED_GRASS_STORY_MIN", 102, 38, "high"),  # CH1 Story 102-177; NOTRAIN Story 23-38
    ("TRAINED_RATIO_TRAINER_MIN", 2.116, 1.0, "high"),  # CH1/NOTRAIN pooled; NOTRAIN/NOTRAIN 1.0 by construction
    ("TRAINED_RATIO_CATCHER_MIN", 1.298, 1.0, "high"),
    ("AWAIT_MAX", 150, 600, "low"),  # the real plans' 72 runs (and #40/#41) 150; STALL1's lowest failing run 600
    ("OFF_RATIO_MIN", 2.23, 1.0, "high"),  # the beeline against itself (leave-one-out) pools to exactly 1.0
    ("NOBATTLE_RATIO_MIN", 1.124, 1.028, "high"),  # the highest pseudo-null (STALL1/CH1), over the 1.0 by construction
    ("CH2_NOBATTLE_RATIO_MIN", 1.155, 1.0, "high"),  # no pseudo-null reaches WALLY
    ("PATIENCE_REACHED_MIN", 1.0, 0.0, "high"),  # PATIENCE 4 of 4; PATIENCE_OLD 0 of 4
    ("PUSH_MAX", 1910, 156790, "low"),  # the real plans' longest; BLOCKED's lowest failing run
    ("LOAF_FRAMES_MAX", 1910, 3120, "low"),  # LOAF's lowest failing run (of 4,640, 4,030, 3,120)
    ("STOP_WITHIN", 684, 63486, "low"))  # LOSE3/STOP's slowest end after the cap (#41); STOPDEAD's nearest (#39, 1314)
#: the paired ratio bounds: none under the largest pseudo-null shift measured (addendum stage-B rules, W7)
STAGE_B_PAIRED = ("TRAINED_RATIO_TRAINER_MIN", "TRAINED_RATIO_CATCHER_MIN", "OFF_RATIO_MIN", "NOBATTLE_RATIO_MIN",
                  "CH2_NOBATTLE_RATIO_MIN")
PAIRED_FLOOR = 1.03


class StageBBoundsTests(unittest.TestCase):
    """STAGE B step 3 (2026-10-27): the FINAL bounds, PINNED, and each PLACED between the real code and its control on the
    development numbers it was set from. WHY: until `--register` hashes them, nothing holds a value where stage B put it;
    a later edit that loosens a bound toward a control (or past the real code) would only show in a graded FAIL or never.
    A pin follows its value and is never weaker (the build's rule). FAULT arms: a moved value is named; a value placed
    outside its development margins, or a paired bound under 1.03, is refused. CONTROL: the module's values pass all three."""

    @staticmethod
    def values() -> dict:
        return {**{k: BOUNDS[k] for k in STAGE_B_FINAL if k in BOUNDS}, "STOP_WITHIN": rs.STOP_WITHIN}

    @staticmethod
    def drift(values: dict) -> dict:
        """Every stage-B key whose value differs from its pin, as key -> (pinned, now); a missing key is a drift too."""
        return {k: (v, values.get(k)) for k, v in STAGE_B_FINAL.items() if values.get(k) != v}

    @staticmethod
    def misplaced(values: dict) -> list:
        """Every placed key whose value is NOT strictly between its control and the real code (the real code on its side)."""
        out = []
        for key, real, control, side in STAGE_B_PLACED:
            value = values.get(key)
            inside = value is not None and (real < value <= control if side == "low" else control < value <= real)
            if not inside:
                out.append((key, value, real, control))
        return out

    @staticmethod
    def under_floor(values: dict) -> list:
        return [k for k in STAGE_B_PAIRED if values.get(k) is None or values[k] < PAIRED_FLOOR]

    def test_the_final_values_are_pinned(self):
        self.assertEqual(self.drift(self.values()), {})  # CONTROL
        self.assertEqual(set(STAGE_B_FINAL) - set(self.values()), set())  # every pinned key exists
        with mock.patch.dict(BOUNDS, {"LOAF_FRAMES_MAX": 4000, "CH2_NOBATTLE_RATIO_MIN": 1.15}):  # FAULT: two moved
            self.assertEqual(self.drift(self.values()), {"LOAF_FRAMES_MAX": (3000, 4000),
                                                         "CH2_NOBATTLE_RATIO_MIN": (1.05, 1.15)})
        with mock.patch.object(rs, "STOP_WITHIN", 60000):  # FAULT: the module constant moved
            self.assertEqual(self.drift(self.values()), {"STOP_WITHIN": (6000, 60000)})

    def test_each_value_sits_between_the_real_code_and_its_control(self):
        self.assertEqual(self.misplaced(self.values()), [])  # CONTROL
        # FAULT: LOAF past its lowest failing run (it would pass a LOAF run of 3,120), the stall bound under the real
        # code's 150, the no-speedrun ratio under the highest pseudo-null
        moved = {**self.values(), "LOAF_FRAMES_MAX": 3200, "AWAIT_MAX": 150, "NOBATTLE_RATIO_MIN": 1.028}
        self.assertEqual([m[0] for m in self.misplaced(moved)], ["AWAIT_MAX", "NOBATTLE_RATIO_MIN", "LOAF_FRAMES_MAX"])
        self.assertEqual([m[0] for m in self.misplaced({})], [p[0] for p in STAGE_B_PLACED])  # nothing read: all refused

    def test_no_paired_bound_is_under_the_floor(self):
        self.assertEqual(self.under_floor(self.values()), [])  # CONTROL
        self.assertEqual(self.under_floor({**self.values(), "TRAINED_RATIO_CATCHER_MIN": 1.02}),
                         ["TRAINED_RATIO_CATCHER_MIN"])  # FAULT

    def test_the_development_numbers_grade_as_the_note_says(self):
        """The final LOAF_FRAMES_MAX on ledger #39's own numbers through the verdict code, R5.NO_LOAFING being the row whose
        control sits nearest its bound (LOAF's 3,120, 120 over it): the real code's worst runs PASS, LOAF's three failing
        runs FAIL, and so does the nearest alone. (The full re-grade, every row and control, is the note's evidence.)"""
        def graded(plan_rows: dict, check_id: str) -> str:
            return status(grade_sweep({**sweep(), **plan_rows}), check_id)
        real = [row("CH1", s, p, push_game=g, push_ai=g) for s, (p, g) in
                {1307: ("Catcher", 1290), 1308: ("Trainer", 1450), 1309: ("Story", 1910)}.items()]
        loaf = [row("CH1", s, p, push_game=g, push_ai=g) for s, (p, g) in
                {1307: ("Catcher", 4640), 1310: ("Catcher", 4030), 1313: ("Catcher", 3120)}.items()]
        self.assertEqual(graded({"CH1": real}, "R5.NO_LOAFING"), gc.PASS)  # CONTROL: the real code's worst, 1,910
        self.assertEqual(graded({"CH1": loaf}, "R5.NO_LOAFING"), gc.FAIL)  # FAULT: LOAF's three failing runs
        self.assertEqual(graded({"CH1": loaf[2:]}, "R5.NO_LOAFING"), gc.FAIL)  # ... and its nearest one alone (3,120)


if __name__ == "__main__":
    unittest.main()
