"""TEST SIDE (build step 5.3, stage A2): the A1 carry-overs and the harness's GAME READS.

    py -3.12 ai_player/gates/test_step53_a2.py            (unittest; offline, no ROM, a few seconds)
    POKEBOT_A2_LIVE=1 py -3.12 ai_player/gates/test_step53_a2.py LiveKnownAnswerTests
                                                          (the known answers on the real emulator: the ROM, about 30 s)

Every guard has a FAULT arm (the rule broken: the test must see it) and a CONTROL arm (the healthy path passes).
  JudgedDrawTests      carry-over 1: R5.CH2_NEW_PLACE and R5.LEFT_NOT_NEW tell "no draw" (VACUOUS, waived) from "a draw
                       made but not judged" (a FAIL the waiver never covers, named on the check's line).
  PlansPlayedTests     carry-over 2: R5.PLANS_PLAYED (n = the plans asked for) FAILS naming every plan none of whose rows
                       played, for EACH of the sweep's plans (13 of 18 used to pass with every row errored).
  PuritySampleTests    carry-over 4: the 8 L5.PURITY_* checks carry a real n and floor, so they CAN read VACUOUS.
  BareIdTests          carry-over 5: `check_lessons` judges a check id written without backticks; the A1 and A2 test
                       files' `assertRaisesRegex` patterns are escaped.
  StoryBattleHpTests, TileRecorderTests, SpinTests, PlayLoopTests, LiveStopTests
                       the five reads' LOGIC offline (fakes for the framework): (i) the party at a battle's start and end,
                       ONE start per battle (a visit to the in-battle BAG or PARTY menu is the same battle: the A2 fix
                       round's latch on `gMain.inBattle`), (ii) the tile read only on a move, (iii) the press log, no
                       facing off the overworld, and the spins it makes countable, (iv) the frame equality and its visible
                       FAIL, (v) who ended the run, in both harnesses, and the frame-budget exit code tied to lifecycle's.
  LiveKnownAnswerTests the reads on the REAL game, each both ways (B3's rule, `2026-10-18-improvement-backlog.md` item B3): HP
                       after a damaging battle vs the same battle with the HP made full; a battle's START: one battle with
                       a bag and a party visit is ONE start with the HP from before the menus, two battles are TWO starts,
                       the second unlike what the first left; a grass tile vs a normal one; a tap and a hold, a spin vs a
                       move; the frame equality true and false under an injected frame. Skipped unless POKEBOT_A2_LIVE=1
                       (it needs the ROM).
"""

from __future__ import annotations

import ast
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import check_lessons  # noqa: E402
from ai_player.gates import grader_checks as gc  # noqa: E402
from ai_player.gates import live_step5 as l5  # noqa: E402
from ai_player.gates import play_harness as ph  # noqa: E402
from ai_player.gates import rate_step5 as rs  # noqa: E402
from ai_player.gates.hands_harness import HarnessControls  # noqa: E402
from ai_player.gates.test_step53_a1 import by_id, check_of, grade_sweep, no_draws, sweep  # noqa: E402

GATES = Path(__file__).resolve().parent
FIXTURES = GATES / "fixtures"


# ---------------------------------------------------------------------------------------------------------------- carry-over 1
class JudgedDrawTests(unittest.TestCase):
    def test_ch2_no_draw_is_waived_but_a_draw_not_judged_fails(self):
        check = check_of(grade_sweep(no_draws(sweep())), "R5.CH2_NEW_PLACE")
        self.assertEqual((check.status, check.n, check.floor), (gc.VACUOUS, 0, 1))  # CONTROL: no draw at all
        self.assertTrue(gc.waived(check))
        rows = no_draws(sweep())
        rows["CH2"][2].update(place_draws=1, place_draws_judged=0)  # its chapter 1 left no seen file (`known is None`)
        results = grade_sweep(rows)
        check = check_of(results, "R5.CH2_NEW_PLACE")
        self.assertEqual((check.status, check.n), (gc.FAIL, 1))  # FAULT: a draw made, not judged
        self.assertFalse(gc.waived(check))
        self.assertIn("DRAWS MADE BUT NOT JUDGED (a run whose chapter 1 left no seen tiles: a FAIL, never waived) "
                      "(seed, draws) [(3, 1)]", check.text)
        self.assertEqual(gc.verdict(results), "FAIL")
        line = next(x for x in gc.evidence_lines(results) if " R5.CH2_NEW_PLACE " in x and x.startswith("  ["))
        self.assertTrue(line.startswith("  [FAIL] R5.CH2_NEW_PLACE HONESTY n/floor 1/1 "), line)  # its own visible line
        check = check_of(grade_sweep(sweep()), "R5.CH2_NEW_PLACE")
        self.assertEqual((check.status, check.n), (gc.PASS, 8))  # CONTROL: every draw judged, none wrong

    def test_left_no_draw_is_waived_but_a_run_with_every_draw_skipped_fails(self):
        check = check_of(grade_sweep(no_draws(sweep())), "R5.LEFT_NOT_NEW")
        self.assertEqual((check.status, check.n), (gc.VACUOUS, 0))  # CONTROL: no draw
        self.assertTrue(gc.waived(check))
        rows = no_draws(sweep())
        rows["CH1"][1].update(left_judged=0, left_skipped=2)  # the game's stays could judge none of its draws
        results = grade_sweep(rows)
        check = check_of(results, "R5.LEFT_NOT_NEW")
        self.assertEqual((check.status, check.n), (gc.FAIL, 2))  # FAULT
        self.assertFalse(gc.waived(check))
        self.assertIn("DRAWS MADE BUT NOT JUDGED (a run whose every draw was skipped: a FAIL, never waived) "
                      "[('CH1', 2, 2)]", check.text)
        self.assertEqual(gc.verdict(results), "FAIL")
        rows = no_draws(sweep())
        rows["CH1"][1].update(left_judged=1, left_skipped=1)  # CONTROL: one skipped beside one judged
        check = check_of(grade_sweep(rows), "R5.LEFT_NOT_NEW")
        self.assertEqual((check.status, check.n), (gc.PASS, 2))
        self.assertEqual(gc.verdict(grade_sweep(rows)), "PASS")


# ---------------------------------------------------------------------------------------------------------------- carry-over 2
class PlansPlayedTests(unittest.TestCase):
    def test_a_healthy_sweep_played_every_plan(self):
        rows = sweep()
        check = check_of(grade_sweep(rows), "R5.PLANS_PLAYED")
        self.assertEqual((check.status, check.n, check.floor, check.kind), (gc.PASS, len(rows), 1, gc.GRADED))  # CONTROL
        self.assertEqual(check.inputs, frozenset({"harness"}))

    def test_every_plan_whose_rows_all_errored_fails_the_sweep_by_name(self):
        """The stage-A1 verifiers measured 13 of 18 plans PASSING with every row errored; now each one fails, named."""
        for plan in sweep():
            with self.subTest(plan=plan):
                rows = sweep()
                for r in rows[plan]:
                    r["error"] = "the run did not happen (synthetic)"
                results = grade_sweep(rows)
                check = check_of(results, "R5.PLANS_PLAYED")
                self.assertEqual(check.status, gc.FAIL)  # FAULT
                self.assertIn(f"'{plan}': ({len(rows[plan])}, 'the run did not happen (synthetic)')", check.text)
                self.assertEqual(gc.verdict(results), "FAIL")

    def test_a_plan_with_no_row_at_all_fails_and_one_played_row_is_enough(self):
        rows = sweep()
        rows["PATIENCE"] = []  # no seed of its personality
        check = check_of(grade_sweep(rows), "R5.PLANS_PLAYED")
        self.assertEqual(check.status, gc.FAIL)  # FAULT
        self.assertIn("'PATIENCE': (0, 'no row')", check.text)
        rows = sweep()
        rows["CH1"][0]["error"] = "one run errored"  # CONTROL: the plan still played
        self.assertEqual(check_of(grade_sweep(rows), "R5.PLANS_PLAYED").status, gc.PASS)


# ---------------------------------------------------------------------------------------------------------------- carry-over 4
def live_run(stdout: str = "", verdict: dict | None = None, ai_log: str = "") -> l5.Run:
    arm = l5.Arm("CH1T", "t", 1000, 60.0)
    return l5.Run(arm, stdout=stdout, verdict=verdict, ai_log=ai_log, exit_code=0)


PURITY = ("L5.PURITY_GATE", "L5.PURITY_CLEAN", "L5.PURITY_PRESSES", "L5.PURITY_FRAMES", "L5.PURITY_BREACHES",
          "L5.PURITY_ENDED", "L5.PURITY_OUTCOME", "L5.PURITY_PACKAGE")


def healthy_purity_run() -> l5.Run:
    counters = {key: 0 for key in l5.BREACH_COUNTERS}
    counters.update(ai_presses=20, real_frames=900)
    verdict = {"verdict": "CLEAN", "counters": counters,
               "facts": {"exit_reason": "play: done: ch1_pokedex reached", "exit_code": 0, "package_root": str(REPO)}}
    return live_run(stdout=f"[AI-GATE] exit=0 verdict=PASS package={REPO / 'ai_player'}\n", verdict=verdict,
                    ai_log="[AI-HANDS] outcome=x presses=10 frames=900\n")


class PuritySampleTests(unittest.TestCase):
    def test_every_purity_check_carries_its_real_count_and_passes(self):
        run = healthy_purity_run()
        l5.check_purity(run, "done: ch1_pokedex reached")
        found = {c.id: c for c in run.checks}
        self.assertEqual(set(found), set(PURITY))
        for key in PURITY:
            check = found[key]
            self.assertIsInstance(check.n, int, key)  # CONTROL: no n/floor "-" any more
            self.assertIsInstance(check.floor, int, key)
            self.assertEqual(check.status, gc.PASS, (key, check.n, check.floor, check.text))
        self.assertEqual((found["L5.PURITY_PRESSES"].n, found["L5.PURITY_FRAMES"].n), (10, 900))
        self.assertEqual((found["L5.PURITY_BREACHES"].n, found["L5.PURITY_BREACHES"].floor),
                         (len(l5.BREACH_COUNTERS), len(l5.BREACH_COUNTERS)))
        self.assertTrue(run.passed)

    def test_a_run_that_left_nothing_to_judge_reads_vacuous_not_fail(self):
        run = live_run()  # no gate line, no verdict file, no hands line
        l5.check_purity(run, "done: ch1_pokedex reached")
        statuses = {c.id: (c.status, c.n) for c in run.checks}
        self.assertEqual(statuses, {key: (gc.VACUOUS, 0) for key in PURITY})  # FAULT: nothing judged, said so
        self.assertFalse(run.passed)  # VACUOUS fails the verdict (no purity check is waived)
        lines = gc.evidence_lines(run.checks)
        self.assertTrue(any(x.startswith("  [VACUOUS] L5.PURITY_CLEAN GRADED n/floor 0/1 ") for x in lines), lines[:3])

    def test_an_untyped_check_with_no_sample_rule_is_refused(self):
        run = healthy_purity_run()
        with mock.patch.dict(l5.PURITY_SAMPLES, clear=True), self.assertRaises(gc.CheckError):  # FAULT
            run.check(True, "verdict file: verdict=CLEAN (want CLEAN)")
        run.check(True, "verdict file: verdict=CLEAN (want CLEAN)")  # CONTROL
        self.assertEqual((run.checks[-1].id, run.checks[-1].n), ("L5.PURITY_CLEAN", 1))


# ---------------------------------------------------------------------------------------------------------------- carry-over 5
LESSON = ("### PL-99. A planted lesson.\n- **Origin:** 2026-10-14, 08 \"A FIX ASKED ONLY UNDER ANOTHER OPTION IS DEAD CODE\".\n"
          "- **Status:** GATED\n- **Enforced:** `gates/call_census.py`, {enforced}.\n- **Retires:** never.\n")


class BareIdTests(unittest.TestCase):
    def problems(self, enforced: str) -> list[str]:
        return check_lessons.check(LESSON.format(enforced=enforced), required=())[0]

    def test_a_bare_check_id_is_judged_like_a_backticked_one(self):
        self.assertEqual(self.problems("`R5.CH1_REACHED`"), [])  # CONTROL: the ticked rule, unchanged
        self.assertEqual(self.problems("R5.CH1_REACHED"), [])  # CONTROL: a bare id of a counting check resolves
        found = self.problems("and R5.SPACED")  # FAULT: a DIAGNOSTIC check, bare, on an Enforced line
        self.assertEqual(len(found), 1, found)
        self.assertIn("Enforced names R5.SPACED (without backticks): R5.SPACED is DIAGNOSTIC", found[0])
        self.assertIn("no check R5.NO_SUCH_CHECK", self.problems("R5.NO_SUCH_CHECK")[0])  # FAULT: an unknown id refused
        self.assertEqual(self.problems("see gates/R5.SPACED_NOTES and XR5.SPACED"), [])  # CONTROL: glued to a path or a word

    def test_a_bare_id_on_a_reported_line_is_judged_too(self):
        text = LESSON.format(enforced="`R5.CH1_REACHED`") + "- **Reported:** R5.CH1_REACHED.\n"
        found = check_lessons.check(text, required=())[0]
        self.assertTrue(any("Reported names R5.CH1_REACHED (without backticks)" in p for p in found), found)  # FAULT
        text = LESSON.format(enforced="`R5.CH1_REACHED`") + "- **Reported:** R5.SPACED.\n"
        self.assertEqual(check_lessons.check(text, required=())[0], [])  # CONTROL

    def test_a_mention_outside_the_two_lines_never_fires(self):
        text = LESSON.format(enforced="`R5.CH1_REACHED`").replace("A planted lesson.", "A planted lesson about R5.SPACED.")
        self.assertEqual(check_lessons.check(text, required=())[0], [])  # CONTROL (rule 6: no false positive)

    def test_the_assert_raises_regex_patterns_escape_their_dots(self):
        def unescaped(source: str) -> list[int]:
            out = []
            for node in ast.walk(ast.parse(source)):
                if (isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "assertRaisesRegex"
                        and len(node.args) >= 2):
                    pattern = node.args[1]
                    escaped = (isinstance(pattern, ast.Call) and getattr(pattern.func, "attr", None) == "escape")
                    if not escaped and "." in ast.unparse(pattern):
                        out.append(node.lineno)
            return out

        for name in ("test_step53_a1.py", "test_step53_a2.py"):
            self.assertEqual(unescaped((GATES / name).read_text(encoding="utf-8")), [], name)  # CONTROL: the files
        self.assertEqual(unescaped('self.assertRaisesRegex(E, "R5.X: y")\n'), [1])  # FAULT: the A1 form


# ---------------------------------------------------------------------------------------------------------------- read i
class StoryBattleHpTests(unittest.TestCase):
    """`StoryRecorder` with the framework's reads replaced by a script of samples: (state, gBattleOutcome, party[,
    gMain.inBattle]). With no fourth value the game's battle flag is "the state is BATTLE" (a battle with no menu visit)."""

    def drive(self, samples: list[tuple]) -> dict:
        recorder = ph.StoryRecorder(context=None, every=1)
        script = iter(samples)
        current: dict = {}

        def truth(context, guard=False):
            sample = next(script)
            current.update(zip(("state", "outcome", "party"), sample))
            current["flag"] = sample[3] if len(sample) > 3 else sample[0] == "BATTLE"
            return {"marks": {}, "stats": {"steps": 0, "captures": 0}, "items": {}}

        with mock.patch.object(ph, "story_truth", truth), \
                mock.patch.object(ph, "battle_now", lambda: (current["outcome"], 0)), \
                mock.patch.object(ph, "game_state_now", lambda: current["state"]), \
                mock.patch.object(ph, "battle_flag_now", lambda: current["flag"]), \
                mock.patch.object(ph, "party_now", lambda: current["party"]):
            for _ in samples:
                recorder.after_frame()
        return recorder.result()

    def test_a_battle_start_and_end_carry_the_party_by_the_game(self):
        hurt, full = [["MUDKIP", 9, 19, 30]], [["MUDKIP", 9, 30, 30]]
        result = self.drive([("OVERWORLD", 1, full), ("BATTLE", 0, full), ("BATTLE", 0, hurt), ("BATTLE", 1, hurt),
                             ("OVERWORLD", 1, hurt)])
        self.assertEqual(result["battle_starts"], [[2, full]])  # the start, with the party as it began
        self.assertEqual([(b["f"], b["result"], b["party"]) for b in result["battles"]], [(4, "won", hurt)])

    def test_a_run_that_begins_in_a_battle_records_no_start(self):
        result = self.drive([("BATTLE", 0, [["X", 1, 1, 1]]), ("BATTLE", 1, [["X", 1, 1, 1]])])
        self.assertEqual(result["battle_starts"], [])  # CONTROL: it did not START here
        self.assertEqual(len(result["battles"]), 1)
        # ... and a run that begins in the in-battle BAG (the game's flag set, the state not BATTLE) neither
        bag = self.drive([("BAG_MENU", 0, [["X", 1, 1, 1]], True), ("BATTLE", 0, [["X", 1, 1, 1]], True),
                          ("BATTLE", 1, [["X", 1, 1, 1]], True), ("OVERWORLD", 1, [["X", 1, 1, 1]], False)])
        self.assertEqual(bag["battle_starts"], [])

    def test_a_visit_to_the_in_battle_bag_or_party_menu_is_the_same_battle(self):
        """THE A2 VERIFIER'S FAILURE (MEASURED live: two starts for one battle after a bag visit). The game's state leaves
        BATTLE for BAG_MENU / PARTY_MENU (and UNKNOWN between) and comes back, while `gMain.inBattle` stays set: ONE start,
        with the party from BEFORE the menu (the HP written while in the menu is no start's)."""
        before, potion, after = [["MUDKIP", 9, 19, 30]], [["MUDKIP", 9, 12, 30]], [["MUDKIP", 9, 12, 30]]
        result = self.drive([("OVERWORLD", 4, before, False), ("BATTLE_STARTING", 0, before, True),
                             ("BATTLE", 0, before, True), ("UNKNOWN", 0, before, True), ("BAG_MENU", 0, potion, True),
                             ("UNKNOWN", 0, potion, True), ("BATTLE", 0, potion, True), ("PARTY_MENU", 0, potion, True),
                             ("BATTLE", 0, after, True), ("BATTLE", 4, after, True), ("BATTLE_ENDING", 4, after, False),
                             ("OVERWORLD", 4, after, False)])
        self.assertEqual(result["battle_starts"], [[3, before]])  # FAULT arm of the latch: 3 starts without it
        self.assertEqual([(b["f"], b["result"], b["party"]) for b in result["battles"]], [(10, "ran", after)])

    def test_the_battle_flag_is_bit_1_of_gmain_0x439(self):
        """`battle_flag_now` reads `gMain` byte 0x439 bit 1 (`include/main.h`: oamLoadDisabled:1, inBattle:1, ...), the
        framework's symbol read faked. CONTROL: 0b10 (inBattle alone) is on, 0b11 too. FAULT: 0b01 (oamLoadDisabled
        alone) and 0b100 are off, and the read asks for exactly gMain, 0x439, 1 byte (the live known answers prove the
        bit on the real game: set through the bag and party menus, clear on the overworld)."""
        asked: list = []
        byte = {"value": 0}
        memory = types.ModuleType("modules.memory")

        def read_symbol(name, offset=0, size=0):
            asked.append((name, offset, size))
            return bytes([byte["value"]])

        memory.read_symbol = read_symbol
        seen = {}
        with mock.patch.dict(sys.modules, {"modules.memory": memory}):
            for value in (0b10, 0b11, 0b01, 0b100, 0):
                byte["value"] = value
                seen[value] = ph.battle_flag_now()
        self.assertEqual(seen, {0b10: True, 0b11: True, 0b01: False, 0b100: False, 0: False})
        self.assertEqual(set(asked), {("gMain", 0x439, 1)})

    def test_two_battles_are_two_starts_each_with_the_party_it_began_with(self):
        """CONTROL of the latch (it must CLOSE when the game says the battle is over), and B3's other way: the second
        battle's start party DIFFERS from what the first battle left (HP changed on the overworld between them), so a start
        is read at its own battle, never copied from the last end."""
        left, healed, hurt = [["MUDKIP", 9, 19, 30]], [["MUDKIP", 9, 25, 30]], [["MUDKIP", 9, 7, 30]]
        result = self.drive([("OVERWORLD", 4, left, False), ("BATTLE", 0, left, True), ("BATTLE", 1, left, True),
                             ("OVERWORLD", 1, left, False), ("OVERWORLD", 1, healed, False), ("BATTLE", 0, healed, True),
                             ("BATTLE", 0, hurt, True), ("BATTLE", 4, hurt, True), ("OVERWORLD", 4, hurt, False)])
        self.assertEqual(result["battle_starts"], [[2, left], [6, healed]])
        self.assertEqual([b["party"] for b in result["battles"]], [left, hurt])
        self.assertNotEqual(result["battle_starts"][1][1], result["battles"][0]["party"])  # unlike what battle 1 left


# ---------------------------------------------------------------------------------------------------------------- read ii
class TileRecorderTests(unittest.TestCase):
    def test_the_tile_is_read_only_on_a_move_and_grass_steps_are_counted(self):
        path = [None, ("0:16", 5, 15), ("0:16", 5, 15), ("0:16", 6, 15), ("0:16", 6, 15), ("0:16", 5, 15), None]
        kinds = {("0:16", 5, 15): "Tall Grass", ("0:16", 6, 15): "Normal"}
        frames = iter(path)
        at: dict = {}
        reads = []

        def tile_now():
            at["where"] = next(frames)
            return at["where"]

        def tile_type_now():
            reads.append(at["where"])
            return kinds[at["where"]]

        recorder = ph.TileRecorder()
        with mock.patch.object(ph, "tile_now", tile_now), mock.patch.object(ph, "tile_type_now", tile_type_now):
            for _ in path:
                recorder.after_frame()
        result = recorder.result()
        self.assertEqual(result["start"], [2, "0:16", 5, 15, "Tall Grass"])
        self.assertEqual(result["steps"], [[4, "0:16", 6, 15, "Normal"], [6, "0:16", 5, 15, "Tall Grass"]])
        self.assertEqual((result["moves"], result["grass_steps"]), (2, 1))  # the start is no step
        self.assertEqual(len(reads), 3)  # FAULT arm of the cost: one map read per position change, never per frame


# ---------------------------------------------------------------------------------------------------------------- read iii
class SpinTests(unittest.TestCase):
    def test_a_turn_on_the_spot_is_a_spin_and_a_step_is_a_move(self):
        log = [[10, "Right", "tap", 1, "Left", "0:16", 5, 15],  # facing Left, taps Right
               [14, "Right", "hold", 16, "Right", "0:16", 5, 15],  # turned, did not move: a SPIN
               [40, "Left", "hold", 16, "Right", "0:16", 6, 15],  # moved: a MOVE
               [70, "A", "tap", 1, None, None, None, None],  # in a battle: neither, and no break
               [90, "Up", "tap", 1, "Left", "0:16", 6, 15]]  # turned again on (6, 15): a SPIN across the battle press
        self.assertEqual(ph.spins_of(log), {"spins": 2, "moves": 1})  # FAULT arms: the turns on the spot
        same = [[1, "Right", "hold", 16, "Right", "0:16", 5, 15], [20, "Right", "hold", 16, "Right", "0:16", 6, 15]]
        self.assertEqual(ph.spins_of(same), {"spins": 0, "moves": 1})  # CONTROL: walking straight is no spin

    def test_every_press_is_logged_with_the_emulators_frame(self):
        emulator = FakeEmulator()
        controls = HarnessControls(emulator)
        for _ in controls.tap("A"):
            emulator.run_single_frame()
        for _ in controls.hold("Left", 3):
            emulator.run_single_frame()
        self.assertEqual([entry[:4] for entry in controls.log], [[0, "A", "tap", 1], [2, "Left", "hold", 3]])
        self.assertEqual(controls.presses, 2)  # the count the recorders compare is unchanged
        self.assertEqual(len(controls.log[0]), 8)

    def test_a_press_off_the_overworld_carries_no_facing_and_one_on_it_does(self):
        """(The A2 fix round, F3: the verifier replaced the overworld check in `press_context` by `if False:` and every
        offline test stayed green.) The framework's reads are faked (`modules.memory`, `modules.player`): the SAME player
        object, facing Left on (5, 15) of map 0:16. CONTROL: on the OVERWORLD the press carries that facing and position.
        FAULT: in a BATTLE (and a menu) the press carries None in all four, so `spins_of` skips it; without the check the
        battle's presses would carry the overworld facing, and a battle's A press between two turns would read as a pair."""
        from ai_player.gates import hands_harness as hh

        state = {"name": "OVERWORLD"}
        avatar = types.SimpleNamespace(facing_direction="Left", map_group_and_number=(0, 16), local_coordinates=(5, 15))
        memory = types.ModuleType("modules.memory")
        memory.get_game_state = lambda: types.SimpleNamespace(name=state["name"])
        player = types.ModuleType("modules.player")
        player.get_player_avatar = lambda: avatar
        emulator = FakeEmulator()
        controls = HarnessControls(emulator)
        with mock.patch.dict(sys.modules, {"modules.memory": memory, "modules.player": player}):
            self.assertEqual(hh.press_context(), ("Left", "0:16", 5, 15))  # CONTROL
            for name in ("BATTLE", "BAG_MENU"):
                state["name"] = name
                self.assertEqual(hh.press_context(), (None, None, None, None))  # FAULT arm: off the overworld
            for name in ("OVERWORLD", "BATTLE"):
                state["name"] = name
                for _ in controls.tap("A"):
                    emulator.run_single_frame()
        self.assertEqual([entry[4:] for entry in controls.log], [["Left", "0:16", 5, 15], [None, None, None, None]])
        self.assertEqual(controls.log_errors, 0)


# ---------------------------------------------------------------------------------------------------------------- reads iv, v
class FakeEmulator:
    def __init__(self, start: int = 1000) -> None:
        self.frames = start
        self.start = start
        self.buttons: list = []

    def get_frame_count(self) -> int:
        return self.frames - self.start

    def run_single_frame(self) -> None:
        self.frames += 1

    def press_button(self, button: str) -> None:
        self.buttons.append(("press", button))

    def hold_button(self, button: str) -> None:
        self.buttons.append(("hold", button))

    def release_button(self, button: str) -> None:
        self.buttons.append(("release", button))


class FakeRecorder:
    every = 30

    def __init__(self) -> None:
        self.frame = 0
        self.battle_starts: list = []
        self.battles: list = []

    def after_frame(self) -> None:
        self.frame += 1


def fake_ai(script):
    """Fake `ai_player.mode` and `ai_player.host.eyes` modules (the AI's code never runs here): `script(controls,
    emulator)` is the brain's play generator."""
    holder: dict = {}

    class Brain:
        def __init__(self, settings, sink, options) -> None:
            self.play_report = {}

        def play(self, controls, eyes):
            return script(controls, holder["emulator"])

    mode = types.ModuleType("ai_player.mode")
    mode.MAX_LOSSES, mode.BrainSettings, mode.HandsBrain = 3, (lambda frames: None), Brain
    eyes = types.ModuleType("ai_player.host.eyes")
    eyes.FrameworkEyes = lambda: None
    return holder, {"ai_player.mode": mode, "ai_player.host.eyes": eyes}


def play(script, frames: int = 100, recorder=None) -> tuple[dict, str]:
    holder, modules = fake_ai(script)
    emulator = FakeEmulator()
    holder["emulator"] = emulator
    context = types.SimpleNamespace(emulator=emulator)
    out = io.StringIO()
    with tempfile.TemporaryDirectory() as folder, mock.patch.dict(sys.modules, modules), redirect_stdout(out):
        result = ph.play(context, 1303, frames, Path(folder), None, None, "ch1_pokedex", set(), None, None,
                         recorder if recorder is not None else FakeRecorder())
        written = json.loads((Path(folder) / ph.READS_FILE).read_text(encoding="utf-8"))
    assert written == json.loads(json.dumps(result["game_reads"]))
    return result, out.getvalue()


def healthy(controls, emulator):
    yield from controls.tap("A")
    yield from controls.hold("Left", 16)
    yield from controls.wait(5)
    return "play: done (synthetic)"


class PlayLoopTests(unittest.TestCase):
    def test_a_healthy_run_adds_up_and_the_ai_ended_it(self):
        calls: list = []

        def unreadable():
            # the tile recorder's framework read, made to fail on every frame whatever else ran in this process (the A2
            # fix round: after LiveKnownAnswerTests booted the real framework, its reads SUCCEEDED here, and the count this
            # test reads, every frame a counted error, was 0 under POKEBOT_A2_LIVE=1)
            calls.append(1)
            raise RuntimeError("no framework (offline)")

        with mock.patch.object(ph, "tile_now", unreadable):
            result, printed = play(healthy)
        self.assertEqual(len(calls), 23)
        reads = result["game_reads"]
        self.assertEqual(reads["frames"], {"frame0": 0, "frame_end": 23, "harness_frames": 23, "recorder_frames": 23,
                                           "equal": True})  # CONTROL
        self.assertNotIn("HARNESS FAIL", printed)
        self.assertEqual(reads["stop"], {"by": "ai", "cause": "the AI's play loop returned", "frames_run": 23,
                                         "frame_budget": 111, "wall_clock_seconds": None})  # CONTROL: the AI's exit
        self.assertEqual(result["reason"], "play: done (synthetic)")
        self.assertEqual([entry[:4] for entry in reads["presses"]["log"]], [[0, "A", "tap", 1], [2, "Left", "hold", 16]])
        self.assertEqual(reads["presses"]["count"], 2)
        self.assertEqual(set(reads), {"battle_hp", "tiles", "presses", "frames", "stop"})
        # the tile recorder ran on EVERY frame the harness ran (offline each framework read fails, and is counted)
        self.assertEqual(reads["tiles"]["errors"], 23)

    def test_the_sweep_row_carries_the_stop_and_the_frame_check(self):
        """`rate_step5.run_one` copies the harness's stop and frame check into the row (recorded, never graded)."""
        play_json = {"game_reads": {"stop": {"by": "harness"}, "frames": {"equal": False}}, "saved_end": None,
                     "world_file": None, "seen_file": None}
        done = subprocess.CompletedProcess([], 0, ("PLAY " + json.dumps(play_json)).encode(), b"")
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(rs, "_FOLDERS", None), \
                mock.patch.object(rs.subprocess, "run", lambda *a, **k: done), \
                mock.patch.object(rs, "grade_run", lambda *a, **k: {}), \
                mock.patch.object(rs.tempfile, "mkdtemp", lambda prefix: folder):
            row = rs.run_one("CH1", 1303, 1000, "ch1_pokedex")
        self.assertEqual((row["harness_stop"], row["frames_equal"]), ("harness", False))

    def test_a_frame_run_behind_the_harness_is_a_visible_fail(self):
        def sneaky(controls, emulator):
            yield from controls.tap("A")
            emulator.run_single_frame()  # a frame the harness did not run (injected offset)
            yield from controls.wait(5)
            return "play: done (synthetic)"

        result, printed = play(sneaky)
        self.assertFalse(result["game_reads"]["frames"]["equal"])  # FAULT
        self.assertEqual((result["game_reads"]["frames"]["frame_end"], result["game_reads"]["frames"]["harness_frames"]),
                         (8, 7))
        self.assertIn("HARNESS FAIL: the frame count does not add up: frame0 0 + the harness's 7 frames != the emulator's "
                      "8 at the end", printed)

    def test_a_recorder_that_missed_a_frame_is_a_fail(self):
        class Skipping(FakeRecorder):
            calls = 0

            def after_frame(self) -> None:
                self.calls += 1
                if self.calls != 4:  # the 4th frame is not counted: an offset injected into the recorder
                    self.frame += 1

        result, printed = play(healthy, recorder=Skipping())
        self.assertFalse(result["game_reads"]["frames"]["equal"])  # FAULT: the stamps would be shifted
        self.assertIn("(the recorder saw 22)", printed)

    def test_a_brain_that_never_returns_is_stopped_by_the_harness(self):
        def endless(controls, emulator):
            while True:
                yield from controls.wait(1)

        result, printed = play(endless, frames=50)
        stop = result["game_reads"]["stop"]
        self.assertEqual((stop["by"], stop["frames_run"], stop["frame_budget"]), ("harness", 61, 61))  # FAULT arm
        self.assertEqual(result["reason"], "harness: the brain overran its budget")
        self.assertTrue(result["game_reads"]["frames"]["equal"])


class LiveStopTests(unittest.TestCase):
    """read v in the LAUNCHER harness (`live_step5.harness_stop`, `Run.driver_killed`), from the process's exit code and
    the driver's own kill, never the brain's reason."""

    def stop(self, code: int, killed: bool = False, reason: str = "play: done") -> dict:
        run = live_run(verdict={"facts": {"exit_reason": reason}, "counters": {"real_frames": 500}})
        run.exit_code, run.driver_killed, run.elapsed = code, killed, 12.0
        return l5.harness_stop(run)

    def test_each_way_a_launcher_run_ends(self):
        self.assertEqual(self.stop(0)["by"], "ai")  # CONTROL: the AI's own exit
        self.assertEqual(self.stop(0, reason="wall-clock")["by"], "ai")  # the brain's text changes nothing
        wall = self.stop(l5.launcher.WALL_CLOCK_EXIT)
        self.assertEqual((wall["by"], wall["cause"]), ("harness", "the launcher's wall clock (exit code 124)"))  # FAULT
        self.assertEqual(self.stop(4)["cause"], "the frame budget (exit code 4)")  # FAULT
        self.assertEqual(self.stop(-9, killed=True)["by"], "harness")  # FAULT: the driver's own wall clock
        self.assertEqual(self.stop(2)["by"], "other")
        self.assertEqual(self.stop(0)["real_frames"], 500)

    @staticmethod
    def exit_frame_budget(text: str) -> int:
        """`EXIT_FRAME_BUDGET` from `host/lifecycle.py`'s TEXT (never imported: the G-3 rule keeps the grader from the
        AI's host code, and this test reads it the same way). RAISES when the constant is not there (a rename must fail
        this test, not pass it)."""
        found = re.findall(r"^EXIT_FRAME_BUDGET\s*=\s*(\d+)\s*(?:#.*)?$", text, re.MULTILINE)
        if len(found) != 1:
            raise AssertionError(f"host/lifecycle.py: {len(found)} EXIT_FRAME_BUDGET assignments (want exactly 1)")
        return int(found[0])

    def test_the_frame_budget_exit_is_lifecycles_own(self):
        """(The A2 fix round, F4) `live_step5.FRAME_BUDGET_EXIT` is a hand copy of `host/lifecycle.py` EXIT_FRAME_BUDGET.
        CONTROL: the real file's value equals the copy. FAULT: a lifecycle whose value moved (7) reads 7, unequal; one
        without the constant raises."""
        real = (REPO / "ai_player" / "host" / "lifecycle.py").read_text(encoding="utf-8")
        self.assertEqual(self.exit_frame_budget(real), l5.FRAME_BUDGET_EXIT)  # CONTROL (and the tie itself)
        moved = re.sub(r"^EXIT_FRAME_BUDGET = \d+", "EXIT_FRAME_BUDGET = 7", real, flags=re.MULTILINE)
        self.assertNotEqual(self.exit_frame_budget(moved), l5.FRAME_BUDGET_EXIT)  # FAULT
        with self.assertRaises(AssertionError):
            self.exit_frame_budget(real.replace("EXIT_FRAME_BUDGET = ", "EXIT_FRAMES = "))

    def test_run_arm_records_the_stop_and_the_drivers_kill(self):
        class Proc:
            def __init__(self, timeout: bool) -> None:
                self.timeout, self.returncode = timeout, None

            def communicate(self, timeout=None):
                if self.timeout and timeout is not None:
                    raise subprocess.TimeoutExpired("x", timeout)
                self.returncode = -9 if self.timeout else 0
                return b"", None

        for timeout, want in ((False, ("ai", False)), (True, ("harness", True))):
            with self.subTest(timeout=timeout), tempfile.TemporaryDirectory() as folder:
                profile = Path(folder)
                (profile / l5.launcher.PROFILE_MARKER).write_text("x", encoding="utf-8")
                with mock.patch.object(l5.launcher, "ensure_profile", lambda root, name: (profile, None)), \
                        mock.patch.object(l5.launcher, "force_http_off", lambda p: None), \
                        mock.patch.object(l5.launcher, "kill_tree", lambda p: None), \
                        mock.patch.object(l5.launcher, "read_verdict", lambda d: None), \
                        mock.patch.object(l5.subprocess, "Popen", lambda *a, **k: Proc(timeout)):
                    run = l5.run_arm(l5.Arm("CH1T", "t", 100, 1.0), profile, {})
                self.assertEqual((run.measures["harness_stop"]["by"], run.driver_killed), want)


# ---------------------------------------------------------------------------------------------------------------- the real game
LIVE = os.environ.get("POKEBOT_A2_LIVE") == "1"


@unittest.skipUnless(LIVE, "the known answers on the real emulator: set POKEBOT_A2_LIVE=1 (needs the ROM)")
class LiveKnownAnswerTests(unittest.TestCase):
    """Each read on the REAL game, both ways. `route101_xp.ss1` (`fixtures/route101_xp.build.json`): a wild battle on
    ROUTE 101 saved on the first frame the foe's HP was 0, the player's MUDKIP at 19 of 30 HP, the player standing on
    (5, 15), tall grass, with (6, 15) beside it a normal tile."""

    @classmethod
    def setUpClass(cls) -> None:
        from ai_player.gates.hands_harness import PROFILE
        from ai_player.gates.probe_eyes import boot

        cls.context = boot(PROFILE)
        cls.emulator = cls.context.emulator

    def load(self) -> None:
        from modules.state_cache import state_cache

        self.emulator.load_save_state((FIXTURES / "route101_xp.ss1").read_bytes())
        # MEASURED 2026-10-24: the framework caches the party (and the player object) by the emulator's FRAME NUMBER
        # (`modules/state_cache.py` age_in_frames 0), and reloading the same state replays the same frame numbers, so the
        # second arm read the FIRST arm's party (19/30) at the same frame. A run never rewinds; a test that reloads must
        # forget the cache
        state_cache.reset()

    def run_gen(self, generator, recorders, limit: int) -> int:
        ran = 0
        for _ in generator:
            self.emulator.run_single_frame()
            ran += 1
            for recorder in recorders:
                recorder.after_frame()
            if ran >= limit:
                break
        return ran

    def end_battle(self, controls) -> object:
        while ph.game_state_now() != "OVERWORLD":
            yield from controls.tap("A")
            yield from controls.wait(6)
        yield from controls.wait(40)

    def test_i_party_hp_at_a_battles_end_hurt_and_full(self):
        from modules.game import get_symbol

        emulator = self.emulator

        class Pin:
            """TEST SIDE ONLY, the other way of the known answer: the MUDKIP's HP held full, after every frame, in both
            copies the game keeps in a battle, the party's (struct Pokemon hp @0x56, outside the encrypted substructs) and
            the battler's (struct BattlePokemon hp @0x28 of gBattleMons[0]). MEASURED 2026-10-24: ONE write of both, at the
            load, reads 30/30 at once and is overwritten before the battle ends (19/30 read again at its end)."""

            def after_frame(self) -> None:
                emulator.write_bytes(get_symbol("gPlayerParty")[0] + 0x56, (30).to_bytes(2, "little"))
                emulator.write_bytes(get_symbol("gBattleMons")[0] + 0x28, (30).to_bytes(2, "little"))

        for make_full, want in ((False, [["Mudkip", 9, 19, 30]]), (True, [["Mudkip", 9, 30, 30]])):
            with self.subTest(full=make_full):
                self.load()
                controls = HarnessControls(self.emulator)
                story = ph.StoryRecorder(self.context, every=30)
                self.run_gen(self.end_battle(controls), [Pin(), story] if make_full else [story], 3000)
                ends = [b["party"] for b in story.battles]
                print(f"[A2 LIVE i] full={make_full}: battle ends {[(b['f'], b['result'], b['party']) for b in story.battles]}")
                self.assertEqual(ends, [want])

    def test_ii_iii_grass_vs_normal_and_a_spin_vs_a_move(self):
        self.load()
        controls = HarnessControls(self.emulator)
        tiles = ph.TileRecorder()
        story = ph.StoryRecorder(self.context, every=30)

        def walk(controls):
            yield from self.end_battle(controls)
            yield from controls.tap("Right")  # facing Left on (5, 15): a turn on the spot
            yield from controls.wait(20)
            yield from controls.hold("Right", 16)  # facing Right: a step to (6, 15)
            yield from controls.wait(20)
            yield from controls.hold("Left", 24)  # back to (5, 15)
            yield from controls.wait(20)
            for _ in range(300):  # walk the grass until a wild battle starts
                if ph.game_state_now() == "BATTLE":
                    break
                yield from controls.hold("Right" if _ % 2 else "Left", 18)
                yield from controls.wait(4)
            yield from controls.wait(60)

        self.run_gen(walk(controls), [tiles, story], 20000)
        result = tiles.result()
        from modules.map import get_map_data

        truth = {(x, y): get_map_data((0, 16), (x, y)).tile_type for x, y in ((5, 15), (6, 15))}
        print(f"[A2 LIVE ii] start {result['start']}; first steps {result['steps'][:4]}; moves {result['moves']}, grass "
              f"steps {result['grass_steps']}; the map's own tiles {truth}")
        self.assertEqual(truth, {(5, 15): "Tall Grass", (6, 15): "Normal"})
        self.assertEqual(result["start"][1:], ["0:16", 5, 15, "Tall Grass"])  # grass
        self.assertEqual(result["steps"][0][1:], ["0:16", 6, 15, "Normal"])  # not grass
        self.assertEqual(result["steps"][1][1:], ["0:16", 5, 15, "Tall Grass"])
        walk_presses = [p for p in controls.log if p[1] != "A"]
        print(f"[A2 LIVE iii] the first presses of the walk {walk_presses[:3]}; spins/moves of them "
              f"{ph.spins_of(walk_presses[:3])}")
        self.assertEqual([p[2] for p in walk_presses[:3]], ["tap", "hold", "hold"])  # each press kind
        self.assertEqual(walk_presses[0][4:], ["Left", "0:16", 5, 15])
        self.assertEqual(walk_presses[1][4:], ["Right", "0:16", 5, 15])  # turned, not moved: a SPIN
        self.assertEqual(walk_presses[2][4:], ["Right", "0:16", 6, 15])  # moved: a MOVE
        self.assertEqual(ph.spins_of(walk_presses[:3]), {"spins": 1, "moves": 1})
        starts = story.battle_starts
        print(f"[A2 LIVE i] battle starts {starts}")
        # ONE start (the fixture's own battle began before the run: none for it), with the party's HP
        self.assertEqual([p for _, p in starts], [[["Mudkip", 9, 19, 30]]], starts)

    # ---- read i's START, both ways (the A2 fix round: the verifier's FAILURE and its two weak proofs)
    def walk_to_a_battle(self, controls) -> object:
        """Back and forth on the grass at (5, 15) until the game's state is BATTLE (bounded)."""
        for step in range(300):
            if ph.game_state_now() == "BATTLE":
                return
            yield from controls.hold("Right" if step % 2 else "Left", 18)
            yield from controls.wait(4)
        raise AssertionError("no wild battle in 300 steps of grass")

    def at_action_menu(self) -> bool:
        from modules.battle_state import get_battle_controller_callback

        return ph.game_state_now() == "BATTLE" and get_battle_controller_callback(0) == "HandleInputChooseAction"

    def to_action_menu(self, controls) -> object:
        """B through the battle's texts until the player's controller polls the action menu (B there does nothing)."""
        for _ in range(400):
            if self.at_action_menu():
                return
            yield from controls.tap("B")
            yield from controls.wait(6)
        raise AssertionError("the action menu never came")

    def choose(self, controls, target: int) -> object:
        """The action menu's cursor (`gActionSelectionCursor`: bit 0 the column, bit 1 the row: 0 FIGHT, 1 BAG, 2 POKéMON,
        3 RUN) moved to `target`, then A."""
        from modules.memory import read_symbol

        for _ in range(8):
            cursor = read_symbol("gActionSelectionCursor", 0, 1)[0]
            if cursor == target:
                break
            if (cursor ^ target) & 1:
                yield from controls.tap("Right" if target & 1 else "Left")
            else:
                yield from controls.tap("Down" if target & 2 else "Up")
            yield from controls.wait(8)
        yield from controls.tap("A")

    def visit(self, controls, target: int, menu: str, inside=None) -> object:
        """Open the in-battle menu at `target`, wait in it (well over one 30-frame story sample), `inside()` there, close
        it with B, and come back to the action menu."""
        yield from self.to_action_menu(controls)
        yield from self.choose(controls, target)
        for _ in range(600):
            if ph.game_state_now() == menu:
                break
            yield from controls.wait(1)
        else:
            raise AssertionError(f"the {menu} never opened")
        yield from controls.wait(90)
        if inside is not None:
            inside()
        yield from controls.tap("B")
        yield from controls.wait(30)
        yield from self.to_action_menu(controls)

    def run_away(self, controls) -> object:
        """RUN from the action menu (again if an escape fails), B through the texts, until the OVERWORLD (bounded)."""
        for _ in range(400):
            if ph.game_state_now() == "OVERWORLD":
                break
            if self.at_action_menu():
                yield from self.choose(controls, 3)
            else:
                yield from controls.tap("B")
            yield from controls.wait(8)
        else:
            raise AssertionError("the battle never gave way to the overworld")
        yield from controls.wait(60)

    def write_hp(self, hp: int) -> None:
        """TEST SIDE ONLY: the MUDKIP's HP in the party (struct Pokemon hp @0x56, outside the encrypted substructs)."""
        from modules.game import get_symbol

        self.emulator.write_bytes(get_symbol("gPlayerParty")[0] + 0x56, hp.to_bytes(2, "little"))

    def sampled(self, story) -> object:
        """A recorder on the story recorder's own 30-frame cadence: the game's state and `gMain.inBattle` at each sample
        (what the start rule saw), so the discriminator is computed on THIS fixture: the starts the old rule ("BATTLE after
        a sample that was not") would have recorded."""

        class Samples:
            def __init__(self) -> None:
                self.frame, self.states = 0, []

            def after_frame(self) -> None:
                self.frame += 1
                if self.frame % story.every == 0:
                    self.states.append((self.frame, ph.game_state_now(), ph.battle_flag_now()))

        return Samples()

    @staticmethod
    def old_rule_starts(states: list) -> int:
        return sum(1 for a, b in zip(states, states[1:]) if b[1] == "BATTLE" and a[1] != "BATTLE")

    def test_i_one_battle_with_a_bag_and_a_party_visit_is_one_start_with_the_hp_from_before(self):
        self.load()
        controls = HarnessControls(self.emulator)
        story = ph.StoryRecorder(self.context, every=30)
        samples = self.sampled(story)
        seen: dict = {}

        def in_bag() -> None:
            seen["in_bag"] = ph.party_now()
            self.write_hp(12)  # a different HP while in the menu: no start may carry it

        def drive(controls):
            yield from self.end_battle(controls)  # the fixture's battle (begun before the run): no start
            yield from self.walk_to_a_battle(controls)
            yield from self.to_action_menu(controls)
            seen["before"] = ph.party_now()
            yield from self.visit(controls, 1, "BAG_MENU", in_bag)
            yield from self.visit(controls, 2, "PARTY_MENU")
            yield from self.run_away(controls)

        self.run_gen(drive(controls), [samples, story], 20000)
        menus = [(f, s, flag) for f, s, flag in samples.states if s not in ("OVERWORLD",)]
        print(f"[A2 LIVE i-start bag] party before the menu {seen.get('before')}, in the bag {seen.get('in_bag')}; "
              f"sampled states in battle (frame, state, gMain.inBattle) {menus}")
        print(f"[A2 LIVE i-start bag] battle starts {story.battle_starts}; ends "
              f"{[(b['f'], b['result'], b['party']) for b in story.battles]}; the OLD rule's starts on these samples "
              f"{self.old_rule_starts(samples.states)}")
        states = [s for _, s, _ in samples.states]
        self.assertIn("BAG_MENU", states)  # the fixture exercised what broke the old rule (not vacuous) ...
        self.assertIn("PARTY_MENU", states)
        self.assertEqual(self.old_rule_starts(samples.states), 3)  # ... which would have recorded 3 starts here
        self.assertTrue(all(flag for _, s, flag in samples.states if s in ("BAG_MENU", "PARTY_MENU")))  # the flag held
        self.assertEqual(seen["before"], [["Mudkip", 9, 19, 30]])
        self.assertEqual(story.battle_starts and [p for _, p in story.battle_starts], [seen["before"]])  # ONE start
        self.assertEqual([b["result"] for b in story.battles], ["won", "ran"])  # the fixture's battle, then this one

    def test_i_two_battles_are_two_starts_and_a_start_unlike_what_the_last_battle_left(self):
        self.load()
        controls = HarnessControls(self.emulator)
        story = ph.StoryRecorder(self.context, every=30)
        samples = self.sampled(story)

        def drive(controls):
            yield from self.end_battle(controls)
            yield from self.walk_to_a_battle(controls)
            yield from self.run_away(controls)  # battle 1 leaves the MUDKIP at 19 of 30
            self.write_hp(25)  # on the overworld, between the battles: battle 2 must START at 25
            yield from controls.wait(30)
            yield from self.walk_to_a_battle(controls)
            yield from self.run_away(controls)

        self.run_gen(drive(controls), [samples, story], 30000)
        ends = [(b["f"], b["result"], b["party"]) for b in story.battles]
        print(f"[A2 LIVE i-start two] battle starts {story.battle_starts}; ends {ends}; flags off the battles "
              f"{sorted({flag for _, s, flag in samples.states if s == 'OVERWORLD'})}")
        self.assertEqual([p for _, p in story.battle_starts], [[["Mudkip", 9, 19, 30]], [["Mudkip", 9, 25, 30]]])
        self.assertEqual([r for _, r, _ in ends], ["won", "ran", "ran"])
        self.assertEqual(story.battle_starts[0][1], ends[0][2])  # battle 1 began with what the fixture's battle left ...
        self.assertNotEqual(story.battle_starts[1][1], ends[1][2])  # ... battle 2 NOT with what battle 1 left (B3)
        self.assertTrue(story.battle_starts[0][0] < ends[1][0] < story.battle_starts[1][0] < ends[2][0])
        self.assertEqual({flag for _, s, flag in samples.states if s == "OVERWORLD"}, {False})

    def test_iv_the_frame_equality_holds_and_an_injected_frame_breaks_it(self):
        self.load()
        frame0 = ph.frame_count(self.emulator)
        for _ in range(120):
            self.emulator.run_single_frame()
        check = ph.frame_check(frame0, 120, 120, ph.frame_count(self.emulator))
        print(f"[A2 LIVE iv] healthy {check}")
        self.assertTrue(check["equal"])  # CONTROL
        frame0 = ph.frame_count(self.emulator)
        for _ in range(120):
            self.emulator.run_single_frame()
        self.emulator.run_single_frame()  # an injected frame the harness did not count
        check = ph.frame_check(frame0, 120, 120, ph.frame_count(self.emulator))
        print(f"[A2 LIVE iv] injected {check}; line: {ph.frame_check_line(check)}")
        self.assertFalse(check["equal"])  # FAULT


if __name__ == "__main__":
    unittest.main()
