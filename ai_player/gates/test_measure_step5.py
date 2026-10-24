"""TEST SIDE (build step 5.3, stage A2): `measure_step5.py`, the measurement of a kept development sweep, on SYNTHETIC run
folders whose answers are known.

    py -3.12 ai_player/gates/test_measure_step5.py        (unittest; offline, no ROM, about a second)

Every computed quantity has a CONTROL arm (a folder whose number is known) and a FAULT arm (the property it measures
broken, or the input it must refuse: the number must move, or the run must be refused). WHY synthetic: the quantities are
arithmetic over the harness's records, and a wrong window edge or a battle not taken out would print a plausible number
that no sweep could tell apart from a true one; a folder written here has one right answer.
  RunRecordTests      `rate_step5.run_one` leaves the run's whole PLAY record (`RUN_FILE`) in its folder (the defect this
                      builder found: the story recorder's marks, captures and item flags were in no file of a kept folder);
                      a folder without it is skipped by name, and a sweep with none measures NOTHING, loudly.
  WindowTests, SliceTests, BaseRateTests, GrassTests, BelowTests, SpinTests, GapTests
                      each quantity of the spec's A2 list, both ways.
  TableTests          the decision table: one row per `b1_debt.json` id (an id with no rule RAISES), the rules' verdicts both
                      ways, RULING rows, and the counts.
  ImportRuleTests     the G-3 rule holds for this module (`check_grader_imports.scan`), and fails on an AI import put in it.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import check_grader_imports as cgi  # noqa: E402
from ai_player.gates import measure_step5 as ms  # noqa: E402
from ai_player.gates import rate_step5 as rs  # noqa: E402

GRASS, NORMAL = "Tall Grass", "Normal"


def story(changes=(), frames=10_000, captures=(), item_flags=(), battles=()) -> dict:
    return {"every": 30, "frames": frames, "changes": [{"f": f, "mark": m, "to": to} for f, m, to in changes],
            "captures": [list(c) for c in captures], "item_flags": [list(i) for i in item_flags],
            "battles": [{"f": f, "outcome": o, "trainer": t} for f, o, t in battles]}


def write_run(root: Path, plan: str, seed: int, personality: str = "Story", *, story_rec: dict | None = None,
              places: dict | None = None, reads: dict | None = None, actions: list | None = None, base=None,
              play: dict | None = None) -> Path:
    """One synthetic kept run folder, as `rate_step5.run_one` and `play_harness.play` leave it."""
    folder = root / f"ai_step5_{plan}_{seed}_x"
    folder.mkdir(parents=True)
    record = {"story": story_rec or story(), "frames": (story_rec or story())["frames"], **(play or {})}
    (folder / rs.RUN_FILE).write_text(json.dumps({"plan": plan, "seed": seed, "base": base, "personality": personality,
                                                  "starter": "MUDKIP", "play": record}), encoding="utf-8")
    (folder / ms.PLACES_FILE).write_text(json.dumps({"every": 10, **(places or {})}), encoding="utf-8")
    (folder / ms.READS_FILE).write_text(json.dumps(reads or {}), encoding="utf-8")
    (folder / ms.ACTIONS_FILE).write_text("\n".join(json.dumps(a) for a in actions or []), encoding="utf-8")
    return folder


def one(**kwargs) -> dict:
    with tempfile.TemporaryDirectory() as root:
        folder = write_run(Path(root), kwargs.pop("plan", "CH1"), kwargs.pop("seed", 1), **kwargs)
        return ms.measure_run(ms.load_run(folder))


class RunRecordTests(unittest.TestCase):
    def test_run_one_leaves_the_whole_play_record_in_the_run_folder(self):
        """CONTROL: the folder holds `RUN_FILE` with the plan, seed and the PLAY record's story (the defect: it held none)."""
        play_json = {"story": {"changes": [{"f": 30, "mark": "X", "to": 1}]}, "game_reads": {"stop": {"by": "ai"}},
                     "saved_end": None, "world_file": None, "seen_file": None}
        done = subprocess.CompletedProcess([], 0, ("PLAY " + json.dumps(play_json)).encode(), b"")
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(rs, "_FOLDERS", None), \
                mock.patch.object(rs.subprocess, "run", lambda *a, **k: done), \
                mock.patch.object(rs, "grade_run", lambda *a, **k: {}), \
                mock.patch.object(rs.tempfile, "mkdtemp", lambda prefix: folder):
            rs.run_one("CH2", 1303, 1000, "ch2_wally")
            record = json.loads((Path(folder) / rs.RUN_FILE).read_text(encoding="utf-8"))
            run = ms.load_run(Path(folder))
        self.assertEqual((record["plan"], record["seed"], record["play"]["story"]["changes"][0]["f"]), ("CH2", 1303, 30))
        self.assertEqual((run["plan"], run["reads"]["stop"]["by"]), ("CH2", "ai"))  # the PLAY copy when no reads file

    def test_a_folder_without_the_record_is_skipped_by_name_and_nothing_measured_is_loud(self):
        """FAULT: a pre-A2 folder (no `RUN_FILE`) is never measured as an empty run: it is skipped and named, and a sweep
        of only such folders says NOTHING TO MEASURE with exit 1."""
        with tempfile.TemporaryDirectory() as root:
            old = Path(root) / "ai_step5_CH1_1_old"
            old.mkdir()
            (old / "places.json").write_text("{}", encoding="utf-8")
            runs, skipped = ms.load_sweep([Path(root)])
            out = io.StringIO()
            with redirect_stdout(out):
                code = ms.main([root])
            write_run(Path(root), "CH1", 2)
            runs2, skipped2 = ms.load_sweep([Path(root)])
        self.assertEqual((runs, skipped), ([], [str(old)]))
        self.assertEqual(code, 1)
        self.assertIn("NOTHING TO MEASURE", out.getvalue())
        self.assertEqual(([r["seed"] for r in runs2], len(skipped2)), ([2], 1))  # CONTROL


class WindowTests(unittest.TestCase):
    def test_the_non_battle_frames_of_each_inter_mark_window(self):
        """CONTROL: marks at 1000 and 3000 of a 5000-frame run, no battle: windows 1000, 2000, 2000. FAULT: a battle
        [1500, 1990] (sampled every 10: 500 frames) inside the second window takes 500 frames out of it alone."""
        marks = [(1000, "A", 1), (3000, "B", 1), (3000, "C", 1)]
        calm = one(story_rec=story(marks, frames=5000))
        fought = one(story_rec=story(marks, frames=5000), places={"battles": [[1500, 1990]]})
        self.assertEqual(calm["windows"], [1000, 2000, 2000])
        self.assertEqual(fought["windows"], [1000, 1500, 2000])


class SliceTests(unittest.TestCase):
    def test_each_criterion_lights_its_own_slice_and_a_slice_with_none_is_loafing(self):
        """CONTROL: five 1000-frame slices of a 6000-frame run, each productive by one criterion (tiles, page, battle,
        capture, item), and slice 5 by none (loafing). FAULT arms inside: 7 new tiles (under `SLICE_TILES`) and a text of
        a page seen before light nothing; the capture timeline's FIRST sample is its baseline, not a rise."""
        places = {"new_tiles": [[100, ms.SLICE_TILES], [5100, ms.SLICE_TILES - 1]],
                  "texts": [[1200, 1300, True], [5200, 5300, False]], "battles": [[2100, 2400]],
                  "stays": [[10, "0:9"]]}
        rec = story(frames=6000, captures=[(30, 0), (3500, 1)], item_flags=[(30, 4), (4500, 5)])
        m = one(story_rec=rec, places=places)
        self.assertEqual({k: m["slices"][k] for k in ("n", "tiles", "page", "battle", "capture", "item", "calm",
                                                      "productive", "loaf")},
                         {"n": 6, "tiles": 1, "page": 1, "battle": 1, "capture": 1, "item": 1, "calm": 5,
                          "productive": 4, "loaf": 1})
        self.assertEqual(m["slices"]["yield"], 0.8)
        rows = ms.slices(ms.load_run(write_run(Path(tempfile.mkdtemp()), "CH1", 9, story_rec=rec, places=places)))
        self.assertEqual([r["game"] for r in rows], [True, True, False, True, True, False])
        self.assertEqual([r["battle"] for r in rows], [False, False, True, False, False, False])

    def test_a_map_first_stood_on_is_a_tiles_slice_but_the_first_map_is_not(self):
        """CONTROL: a stay on a NEW map at 1500 lights slice 1's tiles; FAULT: the run's first map (at 10) lights none,
        and neither does coming BACK to it (at 2500), nor re-entering the second map (at 3500)."""
        m = one(story_rec=story(frames=4000),
                places={"stays": [[10, "0:9"], [1500, "0:16"], [2500, "0:9"], [3500, "0:16"]]})
        self.assertEqual((m["slices"]["tiles"], m["slices"]["productive"]), (1, 1))


class BaseRateTests(unittest.TestCase):
    @staticmethod
    def actions(start: int, end: int, kind: str = "explore") -> list[dict]:
        return [{"decision": "goal", "action": kind, "frame": start, "extra": {}},
                {"decision": "goal_end", "frame": end}, {"decision": "goal", "action": "story", "frame": end, "extra": {}},
                {"decision": "noop", "frame": 4000}]

    def test_slices_inside_the_ai_curiosity_span_are_split_from_the_base_rate(self):
        """CONTROL: the AI's look round spans emulator frames 50000-52000 and the harness's frame0 is 50000, so recorder
        slices 0-1 are INSIDE (both loafing) and 2-3 OUTSIDE (one productive): inside 0 of 2, base rate 1 of 2.
        FAULT: the same span stamped 2000 frames later (frame0 48000) moves the inside slices to 2-3."""
        places = {"new_tiles": [[2500, 20]], "stays": [[10, "0:9"]]}
        acts = [{**a, "frame": a["frame"] + 50000} for a in self.actions(0, 2000)]
        inside = one(story_rec=story(frames=4000), places=places, actions=acts, reads={"frames": {"frame0": 50000}})
        shifted = one(story_rec=story(frames=4000), places=places, actions=acts, reads={"frames": {"frame0": 48000}})
        self.assertEqual((inside["split"]["inside"]["calm"], inside["split"]["inside"]["productive"],
                          inside["split"]["outside"]["calm"], inside["split"]["outside"]["productive"]), (2, 0, 2, 1))
        self.assertEqual((shifted["split"]["inside"]["productive"], shifted["split"]["outside"]["productive"]), (1, 0))

    def test_a_curiosity_goal_the_story_moved_on_in_is_no_curiosity_span(self):
        """FAULT: a milestone inside the span makes it the story's own (`goal_spans` story_moved): no slice is inside."""
        acts = self.actions(0, 2000)
        acts.insert(1, {"decision": "milestone", "frame": 1000})
        m = one(story_rec=story(frames=4000), actions=acts, reads={"frames": {"frame0": 0}})
        self.assertEqual(m["split"]["inside"]["n"], 0)


class GrassTests(unittest.TestCase):
    STEPS = [[100, "0:16", 5, 15, GRASS], [600, "0:16", 5, 14, GRASS], [700, "0:16", 6, 14, NORMAL],
             [900, "0:17", 3, 3, GRASS], [1500, "0:17", 3, 4, GRASS]]

    def test_only_the_grass_steps_between_the_starter_and_the_rival_count(self):
        """CONTROL: starter's mark at 500, rival's flag at 1000: the grass steps at 600 and 900 (not 100, before the
        starter; not 700, normal; not 1500, after the rival) = 2; the stint 900 - 600 = 300."""
        rec = story([(500, "VAR_BIRCH_LAB_STATE", 2), (1000, "DEFEATED_RIVAL_ROUTE103", 1)], frames=2000)
        m = one(story_rec=rec, reads={"tiles": {"steps": self.STEPS, "grass_steps": 4}})
        self.assertEqual((m["grass_before_rival"], m["stint"]), (2, 300))

    def test_no_rival_flag_is_no_number_not_zero(self):
        """FAULT: the rival never beaten: None (a run that never met the rival did not train 0 steps for it)."""
        rec = story([(500, "VAR_BIRCH_LAB_STATE", 2)], frames=2000)
        m = one(story_rec=rec, reads={"tiles": {"steps": self.STEPS}})
        self.assertIsNone(m["grass_before_rival"])
        self.assertEqual(m["stint"], 900)  # to the run's end: 600 -> 1500


class MarkTimeTests(unittest.TestCase):
    def test_a_target_confirmed_or_held_at_the_end_vs_one_held_from_the_start(self):
        """CONTROL: WALLY's var confirmed at 6000, battle [1000, 1990] before it: frame 6000, no battle 5000. The smoke's
        case: no change recorded but the end marks hold it (the run ended before the second sample): the run's end, 8000,
        flagged `at_end`. FAULT: the START marks already held it (a chapter-2 run resumed past it): None, never the end."""
        places = {"battles": [[1000, 1990]]}
        held = {"story_truth": {"marks": {"VAR_PETALBURG_GYM_STATE": 2}}}
        confirmed = one(story_rec=story([(6000, "VAR_PETALBURG_GYM_STATE", 2)], frames=8000), places=places)
        at_end = one(story_rec=story([(5000, "VAR_PETALBURG_GYM_STATE", 1)], frames=8000), places=places, play=held)
        resumed = one(story_rec=story(frames=8000), places=places,
                      play={**held, "start_story": {"marks": {"VAR_PETALBURG_GYM_STATE": 2}}})
        self.assertEqual(confirmed["wally"], {"frame": 6000, "no_battle": 5000, "at_end": False})
        self.assertEqual(at_end["wally"], {"frame": 8000, "no_battle": 7000, "at_end": True})
        self.assertIsNone(resumed["wally"])


class BelowTests(unittest.TestCase):
    @staticmethod
    def reads(starts, ends) -> dict:
        return {"battle_hp": {"every": 30, "starts": starts, "ends": ends}}

    def test_a_start_at_full_hp_is_under_nothing(self):
        """CONTROL: a wild battle started at 20/20."""
        m = one(reads=self.reads([[100, [["Mudkip", 5, 20, 20]]]], [[400, "won", False, [["Mudkip", 5, 12, 20]]]]))
        self.assertEqual((m["below"]["wild"], m["below"]["below"], m["below"]["below_own"]),
                         (1, {"0.25": 0, "0.45": 0, "0.5": 0, "0.6": 0}, 0))

    def test_a_wild_start_at_forty_percent_is_counted_and_a_trainers_is_not(self):
        """FAULT: a wild battle started at 8/20 (0.4): under 0.45, 0.5 and 0.6, not 0.25; under the Story's heal_below
        0.6 and the Trainer's 0.45. A TRAINER's battle started at 2/20 is not a roam's: not counted. A start whose party
        was unreadable is counted apart."""
        reads = self.reads([[100, [["Mudkip", 5, 8, 20]]], [900, [["Mudkip", 5, 2, 20]]], [1500, None]],
                           [[400, "won", False, None], [1200, "won", True, None], [1800, "ran", False, None]])
        story_m = one(reads=reads, personality="Story")
        trainer = one(reads=reads, personality="Trainer")
        self.assertEqual((story_m["below"]["starts"], story_m["below"]["wild"], story_m["below"]["unread"]), (3, 2, 1))
        self.assertEqual(story_m["below"]["below"], {"0.25": 0, "0.45": 1, "0.5": 1, "0.6": 1})
        self.assertEqual((story_m["below"]["heal_below"], story_m["below"]["below_own"]), (0.6, 1))
        self.assertEqual((trainer["below"]["heal_below"], trainer["below"]["below_own"]), (0.45, 1))

    def test_starts_and_ends_that_do_not_alternate_are_no_number_never_a_count(self):
        """(The A2 fix round; the verifier's FAILURE) FAULT, the smoke's shape: one wild battle whose start was recorded
        again after a bag visit (the second at mid-fight HP, 4/20) pairs BOTH starts with the one end. Before the guard it
        counted 2 wild starts, 1 under 0.25; now the quantity is NO NUMBER, every count None. Also a start missing between
        two ends (S E E). CONTROL: start, end, start, end and one final open start (a run that ended in a battle) is
        counted as before, and a start and an end at the same sample put the start first."""
        doubled = self.reads([[100, [["Mudkip", 5, 20, 20]]], [400, [["Mudkip", 5, 4, 20]]]],
                             [[700, "ran", False, [["Mudkip", 5, 4, 20]]]])
        m = one(reads=doubled)
        self.assertEqual(m["below"]["no_number"], "NO NUMBER: starts and ends do not alternate (2 starts, 1 ends)")
        self.assertEqual({k: m["below"][k] for k in ("wild", "unread", "below", "below_own")},
                         {"wild": None, "unread": None, "below": None, "below_own": None})
        self.assertEqual((m["below"]["starts"], m["below"]["ends"]), (2, 1))
        lost = one(reads=self.reads([[100, [["Mudkip", 5, 20, 20]]]], [[400, "won", False, None], [900, "won", False, None]]))
        self.assertTrue(lost["below"]["no_number"])
        healthy = self.reads([[100, [["Mudkip", 5, 20, 20]]], [900, [["Mudkip", 5, 4, 20]]], [1500, [["Mudkip", 5, 2, 20]]]],
                             [[400, "won", False, None], [1200, "won", False, None]])
        h = one(reads=healthy)
        self.assertIsNone(h["below"]["no_number"])
        self.assertEqual((h["below"]["wild"], h["below"]["below"]["0.25"]), (3, 2))  # CONTROL: counted as before
        self.assertTrue(ms.alternate([[30]], [[30]]))  # a start and its end at one sample: the start first
        self.assertFalse(ms.alternate([], [[30]]))  # an end with no start before it
        self.assertTrue(ms.alternate([], []))


class SpinTests(unittest.TestCase):
    def test_moves_only_vs_a_turn_on_the_spot(self):
        """CONTROL: two steps (position changed each press): 0 spins, 2 moves. FAULT: a turn with no move: 1 spin; and a
        harness count that disagrees with the log is flagged (`agree` False)."""
        walk = [[1, "Up", "hold", 16, "Up", "0:1", 5, 5], [20, "Up", "hold", 16, "Up", "0:1", 5, 4],
                [40, "Up", "hold", 16, "Up", "0:1", 5, 3]]
        turn = walk + [[60, "Left", "tap", 1, "Left", "0:1", 5, 3]]
        a = one(reads={"presses": {"log": walk, "spins": 0}})
        b = one(reads={"presses": {"log": turn, "spins": 0}})
        self.assertEqual((a["spins"]["spins"], a["spins"]["moves"], a["spins"]["agree"], a["spins"]["ratio"]),
                         (0, 2, True, 0.0))
        self.assertEqual((b["spins"]["spins"], b["spins"]["agree"], b["spins"]["ratio"]), (1, False, 0.5))


class GapTests(unittest.TestCase):
    def test_paired_by_seed_and_pooled_by_means(self):
        """CONTROL: real seeds 1, 2 at 10, 20; control seeds 1, 3 at 4, 8: one pair (1, 10, 4, 6); pooled 15 - 6 = 9.
        FAULT: a None value is left out of both, never read as 0."""
        plans = {"CH1": [{"seed": 1, "q": 10}, {"seed": 2, "q": 20}, {"seed": 4, "q": 30}],
                 "NOTRAIN": [{"seed": 1, "q": 4}, {"seed": 3, "q": 8}, {"seed": 4, "q": None}]}
        g = ms.gap(plans, "CH1", "NOTRAIN", "q")
        self.assertEqual((g["pairs"], g["pooled"]), ([(1, 10, 4, 6)], 14.0))


def measured(plan: str, seed: int, **values) -> dict:
    """A measured row with only the fields a rule reads."""
    row = {"plan": plan, "seed": seed, "base": None, "personality": values.pop("personality", "Story"),
           "slices": {"yield": None, "loaf": 0}, "below": {"below_own": 0}, "await_game": 0, "push_game": 0,
           "grass_before_rival": None, "stint": None, "dex": None, "wally": None,
           "losses": {"game": 0, "ai": 0, "after_cap": None}, "stop_by": "ai", "spins": {"ratio": 0.0},
           "_stood": set(), "_maps": []}
    for key, v in values.items():
        if "." in key:
            head, tail = key.split(".")
            row[head] = {**row[head], tail: v}
        else:
            row[key] = v
    return row


class TableTests(unittest.TestCase):
    def test_every_debt_id_has_a_rule_and_an_id_without_one_raises(self):
        """CONTROL: the real `b1_debt.json` (39 ids) gets 39 rows whose counts add up to 39. FAULT: an id with no rule
        raises (a new debt row must get its measurement, never a silent hole)."""
        rows, counts = ms.decision_table({})
        self.assertEqual((len(rows), sum(counts.values())), (len(ms.debt_ids()), len(ms.debt_ids())))
        self.assertEqual(len(ms.debt_ids()), 39)
        self.assertEqual(sorted(ms.debt_ids()), sorted(ms.ROW_RULES))
        with self.assertRaisesRegex(KeyError, r"no measurement rule in measure_step5\.ROW_RULES: \['R5\.NEW_DEBT'\]"):
            ms.decision_table({}, ms.debt_ids() + ["R5.NEW_DEBT"])

    def test_training_separates_only_when_every_notrain_run_is_under_every_ch1_run(self):
        """CONTROL: CH1 30, 40 vs NOTRAIN 5, 12: SEPARATES. FAULT: NOTRAIN 35 overlaps: DOES NOT. A plan not measured:
        NO NUMBER."""
        ch1 = [measured("CH1", 1, grass_before_rival=30), measured("CH1", 2, grass_before_rival=40)]
        good = {"CH1": ch1, "NOTRAIN": [measured("NOTRAIN", 1, grass_before_rival=5),
                                        measured("NOTRAIN", 2, grass_before_rival=12)]}
        bad = {"CH1": ch1, "NOTRAIN": [measured("NOTRAIN", 1, grass_before_rival=35)]}
        self.assertEqual(ms.ROW_RULES["R5.CH1_TRAINED"](good)["verdict"], "SEPARATES")
        self.assertEqual(ms.ROW_RULES["R5.CH1_TRAINED"](bad)["verdict"], "DOES NOT")
        self.assertTrue(ms.ROW_RULES["R5.CH1_TRAINED"]({"CH1": ch1})["verdict"].startswith("NO NUMBER"))

    def test_the_rest_rule_needs_real_zero_and_deadrest_over_zero(self):
        """CONTROL: CH1 0, DEADREST 3: SEPARATES. FAULT: CH1 1 (the real code starts a battle low): DOES NOT."""
        dead = [measured("DEADREST", 1, **{"below.below_own": 3})]
        self.assertEqual(ms.rule_rest({"CH1": [measured("CH1", 1)], "DEADREST": dead})["verdict"], "SEPARATES")
        self.assertEqual(ms.rule_rest({"CH1": [measured("CH1", 1, **{"below.below_own": 1})], "DEADREST": dead})
                         ["verdict"], "DOES NOT")

    def test_the_rest_rule_never_reads_a_run_with_no_number_as_zero(self):
        """(The A2 fix round) FAULT: a CH1 run with no number (None: its starts and ends do not alternate) beside a CH1
        run at 0 was read as 0 (`v or 0`), so "real = 0" read SEPARATES; now it is NO NUMBER, naming the run. CONTROL: a
        counted real run over 0 still refutes it (DOES NOT) whatever is left out, and nothing left out reads as before."""
        dead = [measured("DEADREST", 1, **{"below.below_own": 3})]
        blind = {"CH1": [measured("CH1", 1), measured("CH1", 2, **{"below.below_own": None})], "DEADREST": dead}
        row = ms.rule_rest(blind)
        self.assertEqual(row["verdict"], "NO NUMBER: runs with no number decide it (real [2], DEADREST [])")
        self.assertIn("left out: real [2]", row["rule"])
        low = {"CH1": [measured("CH1", 1, **{"below.below_own": 2}), measured("CH1", 2, **{"below.below_own": None})],
               "DEADREST": dead}
        self.assertEqual(ms.rule_rest(low)["verdict"], "DOES NOT")
        dead_blind = {"CH1": [measured("CH1", 1)], "DEADREST": [measured("DEADREST", 1, **{"below.below_own": None})]}
        self.assertTrue(ms.rule_rest(dead_blind)["verdict"].startswith("NO NUMBER"))  # DEADREST > 0 unproven

    def test_the_stall_rows_by_the_games_path(self):
        """CONTROL: real 120, each arm 600: SEPARATES. FAULT: a real run at 300 (the bound): DOES NOT; an arm missing:
        NO NUMBER."""
        arms = {a: [measured(a, 1, await_game=600)] for a in ("STALL1", "STALL2", "STALL3")}
        self.assertEqual(ms.ROW_RULES["R5.STALL"]({"CH1": [measured("CH1", 1, await_game=120)], **arms})["verdict"],
                         "SEPARATES")
        self.assertEqual(ms.ROW_RULES["R5.STALL"]({"CH1": [measured("CH1", 1, await_game=300)], **arms})["verdict"],
                         "DOES NOT")
        self.assertTrue(ms.ROW_RULES["R5.STALL3"]({"CH1": [measured("CH1", 1)]})["verdict"].startswith("NO NUMBER"))

    def test_yield_separates_only_when_every_named_control_is_under(self):
        """CONTROL: CH1 0.9 against LOAF 0.4, GREEDY 0.5, ERRANDS_OFF 0.6: SEPARATES. FAULT: ERRANDS_OFF 0.95 (the
        critic's beeline, which yields MORE): DOES NOT, naming it."""
        base = {"CH1": [measured("CH1", 1, **{"slices.yield": 0.9})], "LOAF": [measured("LOAF", 1, **{"slices.yield": 0.4})],
                "GREEDY": [measured("GREEDY", 1, **{"slices.yield": 0.5})]}
        good = {**base, "ERRANDS_OFF": [measured("ERRANDS_OFF", 1, **{"slices.yield": 0.6})]}
        bad = {**base, "ERRANDS_OFF": [measured("ERRANDS_OFF", 1, **{"slices.yield": 0.95})]}
        self.assertEqual(ms.ROW_RULES["R5.CH1_YIELD"](good)["verdict"], "SEPARATES")
        row = ms.ROW_RULES["R5.CH1_YIELD"](bad)
        self.assertEqual(row["verdict"], "DOES NOT")
        self.assertIn("not: ['ERRANDS_OFF']", row["rule"])

    def test_greedy_is_no_yield_control_and_cannot_move_the_yield_row(self):
        """(The A2 fix round, F2) GREEDY is the SPACING control (`grader_checks` R5.GREEDY DIAGNOSTIC), not a yield
        control (the critic's Q3: LOAF and the beeline). The verifier's case: CH1 0.60/0.62 over LOAF 0.20/0.25 and
        ERRANDS_OFF 0.40/0.45 SEPARATES, and GREEDY at 0.70 (over every CH1 run) or absent changes nothing; it is never
        named on the rule. FAULT arm: GREEDY back in the named controls turns this very row to DOES NOT."""
        def plan(name, *ys):
            return [measured(name, s, **{"slices.yield": y}) for s, y in enumerate(ys, 1)]

        base = {"CH1": plan("CH1", 0.60, 0.62), "LOAF": plan("LOAF", 0.20, 0.25),
                "ERRANDS_OFF": plan("ERRANDS_OFF", 0.40, 0.45)}
        self.assertEqual(ms.YIELD_CONTROLS, ("LOAF", "ERRANDS_OFF"))
        for greedy in (None, plan("GREEDY", 0.70), plan("GREEDY", 0.10)):
            with self.subTest(greedy=greedy and greedy[0]["slices"]["yield"]):
                row = ms.ROW_RULES["R5.CH1_YIELD"]({**base, **({"GREEDY": greedy} if greedy else {})})
                self.assertEqual(row["verdict"], "SEPARATES")
                self.assertNotIn("GREEDY", row["rule"] + str(row["control"]))
        self.assertEqual(ms.rule_yield({**base, "GREEDY": plan("GREEDY", 0.70)}, "CH1", ["LOAF", "GREEDY", "ERRANDS_OFF"])
                         ["verdict"], "DOES NOT")  # what naming GREEDY did

    def test_loaf_pushing_ratio_lose_and_own_losses_both_ways(self):
        """Each remaining rule: CONTROL then FAULT."""
        real = [measured("CH1", 1, **{"slices.loaf": 5}, push_game=900)]
        self.assertEqual(ms.rule_loaf({"CH1": real, "LOAF": [measured("LOAF", 1, **{"slices.loaf": 9})]})["verdict"],
                         "SEPARATES")
        self.assertEqual(ms.rule_loaf({"CH1": real, "LOAF": [measured("LOAF", 1, **{"slices.loaf": 5})]})["verdict"],
                         "DOES NOT")
        self.assertEqual(ms.rule_push({"CH1": real, "BLOCKED": [measured("BLOCKED", 1, push_game=5000)]})["verdict"],
                         "SEPARATES")
        self.assertEqual(ms.rule_push({"CH1": real, "BLOCKED": [measured("BLOCKED", 1, push_game=3999)]})["verdict"],
                         "DOES NOT")
        pushy = [measured("CH1", 1, push_game=4000)]  # FAULT: the real code itself at the bound
        self.assertEqual(ms.rule_push({"CH1": pushy, "BLOCKED": [measured("BLOCKED", 1, push_game=5000)]})["verdict"],
                         "DOES NOT")
        slow = {"CH1": [measured("CH1", 1, dex={"frame": 120, "no_battle": 110})],
                "ERRANDS_OFF": [measured("ERRANDS_OFF", 1, dex={"frame": 100, "no_battle": 100})]}
        fast = {"CH1": [measured("CH1", 1, dex={"frame": 90, "no_battle": 90})], "ERRANDS_OFF": slow["ERRANDS_OFF"]}
        self.assertEqual(ms.ROW_RULES["R5.NO_SPEEDRUN_DICE"](slow)["verdict"], "SEPARATES")
        self.assertEqual(ms.ROW_RULES["R5.NO_SPEEDRUN_DICE"](fast)["verdict"], "DOES NOT")
        # FAULT: pooled 380/300 = 1.27 over the bound, but CH1 the slower in only 1 of 3 pairs (the seeds' share fails)
        lopsided = {"CH1": [measured("CH1", s, dex={"frame": v, "no_battle": v}) for s, v in ((1, 200), (2, 90), (3, 90))],
                    "ERRANDS_OFF": [measured("ERRANDS_OFF", s, dex={"frame": 100, "no_battle": 100}) for s in (1, 2, 3)]}
        self.assertEqual(ms.ROW_RULES["R5.NO_SPEEDRUN_DICE"](lopsided)["verdict"], "DOES NOT")
        lose = {"LOSE3": [measured("LOSE3", 2, **{"losses.after_cap": 400})],
                "STOPDEAD": [measured("STOPDEAD", 1, **{"losses.after_cap": 9000})]}
        self.assertEqual(ms.rule_lose(lose)["verdict"], "SEPARATES")
        lose["STOPDEAD"] = [measured("STOPDEAD", 1, **{"losses.after_cap": 100})]
        self.assertEqual(ms.rule_lose(lose)["verdict"], "DOES NOT")
        honest = {"CH1": [measured("CH1", 1, losses={"game": 1, "ai": 1})],
                  "STOPDEAD": [measured("STOPDEAD", 1, losses={"game": 1, "ai": 0})]}
        self.assertEqual(ms.rule_own_losses(honest)["verdict"], "SEPARATES")
        honest["CH1"] = [measured("CH1", 1, losses={"game": 2, "ai": 1})]
        self.assertEqual(ms.rule_own_losses(honest)["verdict"], "DOES NOT")

    def test_off_beeline_and_divergence_on_the_games_tiles(self):
        """CONTROL: CH1 stood on 5 tiles no beeline run stood on, each control run 1 alone: SEPARATES. FAULT: CH1 on the
        corridor only: DOES NOT. Divergence with no pair of one personality: NO NUMBER."""
        off = [measured("ERRANDS_OFF", 1, _stood={("a", 0, 0), ("x", 1, 1)}),
               measured("ERRANDS_OFF", 2, _stood={("a", 0, 0), ("y", 1, 1)})]
        far = {"CH1": [measured("CH1", 1, _stood={("a", 0, 0)} | {("z", i, 0) for i in range(5)})], "ERRANDS_OFF": off}
        near = {"CH1": [measured("CH1", 1, _stood={("a", 0, 0), ("x", 1, 1)})], "ERRANDS_OFF": off}
        row = ms.rule_off_beeline(far)
        self.assertEqual((row["verdict"], row["real"], row["control"]), ("SEPARATES", [(1, 5)], [(1, 1), (2, 1)]))
        self.assertEqual(ms.rule_off_beeline(near)["verdict"], "DOES NOT")
        self.assertTrue(ms.ROW_RULES["R5.SEED_DIVERGENCE"](far)["verdict"].startswith("NO NUMBER"))

    def test_ruling_rows_print_ruling_and_the_counts_add_up(self):
        """The plans that are a coordinator's ruling print RULING whatever was measured (6 of them)."""
        rows, counts = ms.decision_table({})
        self.assertEqual(sorted(r["id"] for r in rows if r["verdict"] == "RULING"),
                         sorted(["L5.PURITY_PRESSES", "L5.PURITY_FRAMES", "L5.PRESS_GATES", "L5.A_KINDS", "L5.BLIND",
                                 "L5.HAS_GOAL"]))
        self.assertEqual((counts["ruling"], counts["separates"]), (6, 0))

    def test_main_prints_every_block_and_the_table_counts(self):
        """CONTROL end to end: a two-run synthetic sweep prints the base rate, both plans, the gaps and a 39-row table."""
        with tempfile.TemporaryDirectory() as root:
            rec = story([(500, "VAR_BIRCH_LAB_STATE", 2), (1000, "DEFEATED_RIVAL_ROUTE103", 1)], frames=2000)
            write_run(Path(root), "CH1", 1, story_rec=rec, reads={"tiles": {"steps": GrassTests.STEPS}})
            write_run(Path(root), "NOTRAIN", 1, story_rec=rec, reads={"tiles": {"steps": GrassTests.STEPS[:1]}})
            out = io.StringIO()
            with redirect_stdout(out):
                code = ms.main([root, "--json", str(Path(root) / "m.json")])
            saved = json.loads((Path(root) / "m.json").read_text(encoding="utf-8"))
        text = out.getvalue()
        self.assertEqual(code, 0)
        for needle in ("THE REAL CODE'S BASE RATE", "PLAN CH1:", "PLAN NOTRAIN:", "GAPS", "CH1 - NOTRAIN grass_before_rival: "
                       "pairs [(1, 2, 0, 2)]", "R5.CH1_TRAINED: SEPARATES", "DECISION TABLE COUNTS:"):
            self.assertIn(needle, text)
        self.assertEqual(sum(saved["counts"].values()), 39)

    def test_main_prints_no_number_for_a_run_whose_starts_and_ends_do_not_alternate(self):
        """(The A2 fix round) end to end: the CH2 run's line and its plan line read NO NUMBER for the HP-fraction quantity
        (never a count), and the alternating CH2 run beside it keeps its count."""
        doubled = BelowTests.reads([[100, [["Mudkip", 5, 20, 20]]], [400, [["Mudkip", 5, 4, 20]]]],
                                   [[700, "ran", False, None]])
        fine = BelowTests.reads([[100, [["Mudkip", 5, 4, 20]]]], [[700, "ran", False, None]])
        with tempfile.TemporaryDirectory() as root:
            write_run(Path(root), "CH2", 1, reads=doubled)
            write_run(Path(root), "CH2", 2, reads=fine)
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(ms.main([root]), 0)
        text = out.getvalue()
        self.assertIn("CH2 seed 1 (Story): ", text)
        line1 = next(line for line in text.splitlines() if "CH2 seed 1 " in line)
        line2 = next(line for line in text.splitlines() if "CH2 seed 2 " in line)
        self.assertIn("battles started under each HP fraction: NO NUMBER: starts and ends do not alternate (2 starts, "
                      "1 ends);", line1)
        self.assertNotIn("under own heal_below", line1)  # no count printed for it
        self.assertIn("started 1 (wild 1, unread 0)", line2)  # CONTROL
        plan = next(line for line in text.splitlines() if line.startswith("PLAN CH2:"))
        self.assertIn("under own heal_below 1 (NO NUMBER, left out: seeds [1], starts and ends do not alternate)", plan)


class ImportRuleTests(unittest.TestCase):
    def test_the_g3_rule_holds_for_the_measurement_and_fails_on_an_ai_import(self):
        """CONTROL: `check_grader_imports.scan` over this module finds no chain to the AI's code. FAULT: the same source
        with one AI import added, in a scratch tree, is found."""
        self.assertEqual(cgi.scan(REPO, ("ai_player.gates.measure_step5",)), [])
        source = Path(ms.__file__).read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as root:
            gates = Path(root) / "ai_player" / "gates"
            gates.mkdir(parents=True)
            (gates / "measure_step5.py").write_text(source + "\nfrom ai_player.brain.goals import ERRAND_KINDS\n",
                                                    encoding="utf-8")
            problems = cgi.scan(Path(root), ("ai_player.gates.measure_step5",))
        self.assertTrue(any("ai_player.brain.goals.ERRAND_KINDS" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
