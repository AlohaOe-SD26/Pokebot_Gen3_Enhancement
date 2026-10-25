"""TEST SIDE (build step 5.3, stage A1): the typed checks (A1-1) and the grader-owned values (A1-2) of the step-5 graders.

    py -3.12 ai_player/gates/test_step53_a1.py        (unittest; offline, no ROM, about 2 s)

Every rule has a FAULT arm (the rule broken: the test must see it) and a CONTROL arm (the healthy path passes):
  TypedSweepTests   a whole synthetic sweep (`sweep()`: every plan, rows the 5.2 grader passed in full) reads PASS, every
                    rate check id appears once, and the kinds are the spec's (#40 GRADED, #44/#56/#61 HONESTY, the listed
                    DIAGNOSTIC and REPORTED ids); a VACUOUS check fails the sweep (R:1690's case); DIAGNOSTIC fails never do.
  CheckRuleTests    construction RAISES for a GRADED check naming `ai` outside b1_debt.json and for a HONESTY check without
                    both `ai` and `game`; the table and the two json files agree both ways (a stale debt or waiver refuses);
                    the import itself validates; a waiver with a reason lets a VACUOUS pass, none does not; the title, the
                    sample count and the untyped-text guards.
  GraderImportTests the G-3 walk: a grader's direct import of the AI, and the AI reached THROUGH a gates function, are
                    caught; a gates function that never reads its module's AI import is not; a mention is no import; the
                    tree as it stands passes; both drivers refuse to start on a breach.
  OwnedValueTests   A1-2: the AI's ERRANDS edited does not move the grader's bounds; LOSE3 grades the harness's recorded
                    MAX_LOSSES; PATIENCE_OLD by the game; #44 and #61 by the game's maps; the live arm's intent from its
                    own told line; a live arm's DIAGNOSTIC failure does not fail it.
`sweep()` is also what `2026-10-23` A1's comparison against the 5.2 grader used (report: the outcome table).
"""

from __future__ import annotations

import io
import json
import re
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

from ai_player.gates import grader_checks as gc  # noqa: E402
from ai_player.gates import rate_step5 as rs  # noqa: E402

BOUNDS = rs.BOUNDS
GATES = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------------------------------------------- the sweep
def row(plan: str, seed: int, personality: str = "Story", **more) -> dict:
    """One graded run's row as `rate_step5.grade_run` writes it, healthy for the 5.2 grader (every bound met)."""
    base = dict(
        plan=plan, seed=seed, personality=personality, starter="TREECKO", reason="play: done: ch1_pokedex reached",
        frames=150000, budget=300000, seconds=1.0, reached=True, dex_frame=140000, rival_beaten=True, rival_frame=100000,
        trainer_battles_to_rival=1, wild_before_rival=10, wild_won_before_rival=8, train_windows=2, game_train_steps=200,
        game_train_won=5, game_steps_refused=0, train_steps_before_rival=200, rival_actives=[personality],
        rival_judge=personality, spins=0, roam_steps=200, spin_ratio=0.0, generic_idle=0, level_at_rival=9,
        hp_after_rival=0.7, losses_game=0, losses_ai=0, losses_told=0, first_loss_f=None, last_loss_f=None, max_losses=3,
        rest_breaches=[], roam_low_ends=1, battles_ended=10, game_stats={"total_battles": 10}, await_ai_max=100,
        await_game_max=100, await_ai_long=[], await_game_samples=1000,
        # one streak of asides that came back (goal, first frame, frames, asides), under ASIDE_STREAK_MAX: the A1 fix
        # round's UngradedBoundTests tighten that bound, which moves R5.ASIDE_BACK only when an aside exists
        asides=[("go@ROUTE101", 1000, 3000, 2)], told_before_bad=[],
        mix={"errand_share": 0.5, "curiosity_share": 0.2, "kinds": ["detour", "explore", "train"], "free_share": 0.15,
             "free_frames": 20000, "story_own": [], "frames": {"train": 30000, "explore": 10000}},
        _sequence=[f"go@A{seed}", f"explore@B{seed}", f"train@C{seed}", f"detour@D{seed}"],
        _tiles={"CORRIDOR 1,1", "CORRIDOR 2,2"} | {f"MAP{seed} {i},{i}" for i in range(5)},
        curious_sequence=[f"explore@B{seed}", f"detour@D{seed}"], time={"outside_nb": 80000, "battles": 5000},
        train_span=50000, last_goal="go", trains=3, wally=False, time_wally=None, place_draws=0, place_draws_judged=0,
        old_places=[], seeing_frames=3000, seeing_productive=2600, curious_frames=4000, productive_frames=3600,
        loaf_frames=400, loaf_frames_all=500, yield_agree=1, curious=[("exp", 1, 1, 1, 1, 9)],
        detours=[(1, ["0:9", 1, 1], 1, 1)], streak_goals=2, streak_frames=3000, push_ai=900, push_game=950,
        push_game_at=[0, 0], person_blocks=0, left_called_new=[], left_judged=2, left_skipped=0, ask_nothing_said=0,
        places_samples=100, out_of_ideas=False, chats_idle=[], text_errors=0, talks_ai=0, talks_apart=[],
        # (build step 5.3, the re-sourcing build) the GAME reads the re-sourced checks grade by: tall-grass steps before
        # the rival (over the Story floor 70; NOTRAIN's are 30 below), the training stint, the frames to the POKéDEX less
        # the game's battles (ERRANDS_OFF's are 80,000 below: 1.25 slower), WALLY's (none in chapter 1)
        grass_before_rival=150, grass_stint=50000, dex_game={"frame": 140000, "no_battle": 100000, "at_end": False},
        wally_game=None)
    base.update(more)
    # the GAME's stood tiles (`game_stood`) are the same tiles as the row's `_tiles` unless a test gives its own
    base.setdefault("_stood", set(base["_tiles"]))
    return base


def sweep() -> dict[str, list[dict]]:
    """Every plan of the default sweep, on four seeds (two personalities, so every divergence check has pairs), each row
    healthy: the 5.2 grader (`git show a9df8b38:ai_player/gates/rate_step5.py`) passes all 67 of its checks on it."""
    people = {1: "Story", 2: "Story", 3: "Catcher", 4: "Catcher"}
    out: dict[str, list[dict]] = {}
    out["CH1"] = [row("CH1", s, p) for s, p in people.items()]
    # one CH1 run lost a battle: phase 2's STOP plans have a run to replay
    out["CH1"][0].update(losses_game=1, losses_ai=1, losses_told=1, first_loss_f=5000, last_loss_f=5000)
    out["NOTRAIN"] = [row("NOTRAIN", s, p, wild_won_before_rival=2, game_train_steps=0, game_train_won=0, train_windows=0,
                          level_at_rival=7, grass_before_rival=30) for s, p in people.items()]
    out["NOHINTS"] = [row("NOHINTS", s, p, reached=s % 2 == 0, out_of_ideas=s % 2 == 1) for s, p in people.items()]
    out["DEADREST"] = [row("DEADREST", s, p, rest_breaches=[(1, "f1 ended at 3/20", "won")]) for s, p in people.items()]
    out["ERRANDS_OFF"] = [row("ERRANDS_OFF", s, p, dex_frame=120000, time={"outside_nb": 60000, "battles": 5000},
                              dex_game={"frame": 120000, "no_battle": 80000, "at_end": False},
                              mix={"errand_share": 0.4, "curiosity_share": 0.0, "kinds": ["train"], "free_share": 0.0,
                                   "free_frames": 0, "story_own": [], "frames": {"train": 30000}},
                              _sequence=["go@A", "train@C", "go@E", f"go@F{s}"], _tiles={"CORRIDOR 1,1", "CORRIDOR 2,2",
                                                                                         f"OFF{s} 0,0"},
                              curious_sequence=[], curious_frames=0, productive_frames=0) for s, p in people.items()]
    for plan in ("STALL1", "STALL2", "STALL3"):
        out[plan] = [row(plan, 1, await_ai_max=400, await_game_max=400, await_ai_long=[(1, 400, "x", "y")])]
    out["PATIENCE"] = [row("PATIENCE", s, "Trainer") for s in (3, 6)]
    out["PATIENCE_OLD"] = [row("PATIENCE_OLD", s, "Trainer", reached=False, dex_frame=None, frames=90000, last_goal="train",
                               reason="play: stuck: no progress for 41000 frames") for s in (3, 6)]
    out["LOSE3"] = [row("LOSE3", s, "Catcher", reason="play: stuck: 3 battles lost (MAX_LOSSES 3)", losses_game=3,
                        losses_ai=3, losses_told=3, first_loss_f=600, last_loss_f=1000, frames=1600) for s in (2, 5)]
    out["CH2"] = [row("CH2", s, p, wally=True, frames=90000, place_draws=2, place_draws_judged=2,
                      mix={"errand_share": 0.4, "curiosity_share": 0.2, "kinds": ["explore"], "free_share": 0.1,
                           "free_frames": 9000, "story_own": [], "frames": {"explore": 9000}},
                      time_wally={"outside_nb": 50000},
                      # (the re-sourcing fix round, item 5) the GAME's frames to WALLY less its battles: 1.25 x CH2_OFF's
                      wally_game={"frame": 60000, "no_battle": 50000, "at_end": False}) for s, p in people.items()]
    out["CH2_OFF"] = [row("CH2_OFF", s, p, wally=True, mix={"errand_share": 0.1, "curiosity_share": 0.0, "kinds": [],
                                                          "free_share": 0.0, "free_frames": 0, "story_own": [],
                                                          "frames": {}},
                          time_wally={"outside_nb": 40000}, wally_game={"frame": 50000, "no_battle": 40000, "at_end": False})
                      for s, p in people.items()]
    # (the re-sourcing fix round, item 9) LOAF fails R5.NO_LOAFING by the GAME's push (both paths over: the paths agree)
    out["LOAF"] = [row("LOAF", s, p, loaf_frames=BOUNDS["LOAF_FRAMES_MAX"] + 1, seeing_productive=600,
                       push_ai=BOUNDS["LOAF_FRAMES_MAX"] + 50, push_game=BOUNDS["LOAF_FRAMES_MAX"] + 60)
                   for s, p in people.items()]
    out["BLOCKED"] = [row("BLOCKED", 1, person_blocks=5, push_ai=BOUNDS["PUSH_MAX"] + 9, push_game=BOUNDS["PUSH_MAX"] + 9),
                      row("BLOCKED", 2)]
    out["GREEDY"] = [row("GREEDY", s, "Catcher", streak_goals=BOUNDS["SPACING_ROW_MAX"] + 2) for s in (2, 5)]
    out["STOP"] = [row("STOP", 1, base="CH1", reason=rs.STOP_REASON, losses_game=1, losses_ai=1, losses_told=1,
                       first_loss_f=5000, frames=6000)]
    out["STOPDEAD"] = [row("STOPDEAD", 1, base="CH1", reason="play: done", losses_game=1, losses_ai=0, losses_told=0,
                           first_loss_f=5000, frames=5000 + rs.STOP_WITHIN + 1000)]
    return out


def grade_sweep(rows: dict[str, list[dict]], module=rs) -> list:
    summary = {plan: module.summarise(plan, sorted(plan_rows, key=lambda r: r["seed"])) for plan, plan_rows in rows.items()}
    return module.verdicts(summary, rows)


def by_id(results) -> dict:
    out: dict = {}
    for check in results:
        out.setdefault(check.id, []).append(check)
    return out


# ---------------------------------------------------------------------------------------------------------------- A1-1
class TypedSweepTests(unittest.TestCase):
    def test_a_healthy_sweep_passes_with_every_check_typed_once(self):
        results = grade_sweep(sweep())
        bad = [(c.id, c.status) for c in results if not gc.counts_ok(c)]
        self.assertEqual(gc.verdict(results), "PASS", bad)  # CONTROL
        ids = by_id(results)
        rate_ids = {key for key in gc.CHECKS if key.startswith("R5.")}
        self.assertEqual(set(ids), rate_ids)  # every check of the table, and no other
        self.assertEqual([key for key, found in ids.items() if len(found) != 1], [])
        # the tuple view of `verdicts` is the verdict: all(ok) == PASS
        self.assertTrue(all(ok for ok, _ in results))

    def test_the_kinds_are_the_specs(self):
        """BUILD-SPEC step 5.3 A1-1, its reclassifications (critic Q1) and live_step5's."""
        kind = {key: spec.kind for key, spec in gc.CHECKS.items()}
        self.assertEqual(kind["R5.PATIENCE_OLD"], gc.GRADED)  # #40 by the game
        self.assertEqual(gc.CHECKS["R5.PATIENCE_OLD"].inputs, frozenset({"game", "harness"}))
        for key in ("R5.CH2_NEW_PLACE", "R5.LEFT_NOT_NEW", "R5.DETOURS_ARRIVE", "L5.NAME_GENDER", "L5.TOLD_WILD"):
            self.assertEqual(kind[key], gc.HONESTY, key)
        for key in ("R5.SPACED", "R5.GREEDY", "R5.CH1_CATCH_ALL", "R5.ASIDE_BACK", "R5.GO_AFTER_PAGE", "R5.ERRANDS_DIFFER",
                    "R5.YIELD_AGREE", "R5.ASK_STEP", "R5.OUT_OF_IDEAS", "R5.PATIENCE_OLD_WORD", "L5.NO_LOAFING",
                    "L5.SPACED", "L5.PUSHING", "L5.ASK_STEP", "L5.POOLED_SPINS", "L5.REST_OCCASIONS",
                    # (A1 fix round, ruling F4) the live twins of #6, #26 and #27
                    "L5.CATCH_ALL", "L5.ASIDE_BACK", "L5.GO_AFTER_PAGE"):
            self.assertEqual(kind[key], gc.DIAGNOSTIC, key)
            self.assertTrue(gc.CHECKS[key].dropped, key)  # listed in the evidence as no longer graded
        self.assertEqual({key for key in kind if gc.CHECKS[key].old_bound}, set(rs.P2_REPORTED))
        self.assertTrue(all(kind[key] == gc.REPORTED for key in rs.P2_REPORTED))
        self.assertEqual(len(gc.CHECKS), len(set(gc.CHECKS)))

    def test_no_detour_is_vacuous_and_fails_the_sweep(self):
        """R:1690's forced FAIL is now VACUOUS (n 0 < floor 1), and fails the verdict (no waiver)."""
        rows = sweep()
        for plan in rs.REAL_PLANS:
            for r in rows[plan]:
                r["detours"] = []
        results = grade_sweep(rows)
        arrive = by_id(results)["R5.DETOURS_ARRIVE"][0]
        self.assertEqual((arrive.status, arrive.n, arrive.floor), (gc.VACUOUS, 0, 1))  # FAULT
        self.assertFalse(arrive[0])
        self.assertEqual(gc.verdict(results), "FAIL")
        self.assertEqual(by_id(grade_sweep(sweep()))["R5.DETOURS_ARRIVE"][0].status, gc.PASS)  # CONTROL

    def test_a_graded_failure_fails_and_a_diagnostic_one_does_not(self):
        rows = sweep()
        rows["CH1"][1]["streak_goals"] = BOUNDS["SPACING_ROW_MAX"] + 3  # CURIOSITY SPACED: DIAGNOSTIC now
        results = grade_sweep(rows)
        spaced = by_id(results)["R5.SPACED"][0]
        self.assertEqual(spaced.status, gc.FAIL)
        self.assertEqual(gc.verdict(results), "PASS")  # CONTROL: a DIAGNOSTIC failure never counts
        # NO LOAFING: GRADED (by the game's push since the re-sourcing fix round)
        rows["CH1"][1].update(push_ai=BOUNDS["LOAF_FRAMES_MAX"], push_game=BOUNDS["LOAF_FRAMES_MAX"])
        results = grade_sweep(rows)
        self.assertEqual(by_id(results)["R5.NO_LOAFING"][0].status, gc.FAIL)
        self.assertEqual(gc.verdict(results), "FAIL")  # FAULT

    def test_the_spins_with_no_step_are_vacuous_not_a_ratio_of_one(self):
        rows = sweep()
        for r in rows["CH1"]:
            r["roam_steps"] = 0
        spins = by_id(grade_sweep(rows))["R5.CH1_SPINS"][0]
        self.assertEqual(spins.status, gc.VACUOUS)

    def drive_main(self, rows: dict[str, list[dict]]) -> tuple[int, str]:
        """`rate_step5.main` end to end on synthetic CH1 rows, every side effect faked (no emulator, no ledger write, no
        disk check, the evidence in a temporary folder): its exit code and its evidence file."""
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

        def chain(plan, seed, frames, target, root, chapter2):
            return [dict(r) for r in rows[plan] if r["seed"] == seed]

        folder = Path(tempfile.mkdtemp(prefix="a1main_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        argv = ["rate_step5.py", "--purpose", "development", "--first-seed", "1", "--seeds", "4", "--plans", ",".join(rows),
                "--workers", "1", "--evidence-tag", "a1test"]
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
                mock.patch.object(rs, "run_chain", chain):
            code = rs.main()
        evidence = next(folder.glob("*-a1test-RATE.txt")).read_text(encoding="utf-8")
        return code, evidence

    def test_the_sweeps_verdict_is_the_typed_rule(self):
        """The driver's own VERDICT line is `grader_checks.verdict` (a GRADED failure fails it, a DIAGNOSTIC one does not)."""
        # (the re-sourcing build) NOTRAIN beside CH1: R5.CH1_TRAINED judges its Trainer and Catcher seeds PAIRED with
        # NOTRAIN, and a personality with runs but no pair never passes
        rows = {"CH1": sweep()["CH1"], "NOTRAIN": sweep()["NOTRAIN"]}
        code, evidence = self.drive_main(rows)
        self.assertEqual(code, 0, [line for line in evidence.splitlines() if line.startswith("  [") and "[PASS]" not in line])
        self.assertIn("VERDICT: PASS", evidence)  # CONTROL
        self.assertIn("  [PASS] R5.CH1_REACHED GRADED n/floor 4/1 inputs game: ", evidence)
        # (the re-sourcing fix round) the debt is EMPTY: no GRADED check reads the AI, so no B1 DEBT line is printed
        self.assertNotIn("B1 DEBT ", evidence)
        rows["CH1"][1]["streak_goals"] = BOUNDS["SPACING_ROW_MAX"] + 3  # DIAGNOSTIC: printed, not counted
        code, evidence = self.drive_main(rows)
        self.assertEqual(code, 0)
        self.assertIn("  [FAIL] R5.SPACED DIAGNOSTIC", evidence)
        rows["CH1"][1].update(push_ai=BOUNDS["LOAF_FRAMES_MAX"], push_game=BOUNDS["LOAF_FRAMES_MAX"])  # GRADED: fails it
        code, evidence = self.drive_main(rows)
        self.assertEqual(code, 1)  # FAULT
        self.assertIn("VERDICT: FAIL", evidence)

    def test_the_evidence_lines(self):
        results = grade_sweep(sweep())
        lines = gc.evidence_lines(results)
        self.assertTrue(any(line.startswith("  [PASS] R5.CH1_REACHED GRADED n/floor 4/1 inputs game: CH1:") for line in lines))
        debt = [line for line in lines if line.startswith("B1 DEBT ")]
        self.assertEqual({line.split()[2] for line in debt},
                         {c.id for c in results if c.kind == gc.GRADED and "ai" in c.inputs})
        dropped = {line.split()[3] for line in lines if line.startswith("NO LONGER GRADED ")}
        self.assertEqual(dropped, {c.id for c in results if gc.CHECKS[c.id].dropped})
        p2 = next(line for line in lines if " R5.CH2_INTENT_MIX " in line)
        self.assertIn("REPORTED", p2)
        self.assertIn("the old bound HELD", p2)


class CheckRuleTests(unittest.TestCase):
    DEBT = {"X.ONE": {"ai_input": "its log", "plan": "A2: re-source"}}

    def test_a_graded_check_that_reads_the_ai_must_be_debt(self):
        with self.assertRaises(gc.CheckError):  # FAULT
            gc.Check("X.ONE", gc.GRADED, gc.PASS, 1, 1, {"game", "ai"}, "t", debt={})
        gc.Check("X.ONE", gc.GRADED, gc.PASS, 1, 1, {"game", "ai"}, "t", debt=self.DEBT)  # CONTROL
        gc.Check("X.TWO", gc.GRADED, gc.PASS, 1, 1, {"game"}, "t", debt={})  # CONTROL: no AI input, no debt needed

    def test_a_honesty_check_names_both_halves(self):
        # (the 5.3 re-sourcing build, item 11: THE AMENDMENT to A1-1) the truth half is the game OR the harness
        for inputs in ({"ai"}, {"game"}, {"harness"}, {"game", "harness"}):
            with self.assertRaises(gc.CheckError, msg=inputs):  # FAULT
                gc.Check("X.H", gc.HONESTY, gc.PASS, 1, 1, inputs, "t", debt={})
        gc.Check("X.H", gc.HONESTY, gc.PASS, 1, 1, {"ai", "game"}, "t", debt={})  # CONTROL
        gc.Check("X.H", gc.HONESTY, gc.PASS, 1, 1, {"ai", "harness"}, "t", debt={})  # CONTROL: the amendment

    def test_unknown_kinds_inputs_and_statuses_refuse(self):
        for kind, status, inputs in (("GRADE", gc.PASS, {"game"}), (gc.GRADED, "OK", {"game"}),
                                     (gc.GRADED, gc.PASS, {"screen"}), (gc.GRADED, gc.PASS, set())):
            with self.assertRaises(gc.CheckError):
                gc.Check("X.K", kind, status, 1, 1, inputs, "t", debt={})

    def test_the_table_and_the_files_agree_both_ways(self):
        gc.validate(gc.CHECKS, gc.DEBT, gc.WAIVERS)  # CONTROL: as they stand (the debt EMPTY since the re-sourcing fix round)
        self.assertEqual(gc.DEBT, {})
        reads_ai = {**gc.CHECKS, "R5.ZZ_SYNTHETIC": gc._spec(gc.GRADED, "game+ai", "ZZ SYNTHETIC")}
        with self.assertRaises(gc.CheckError):  # FAULT: a GRADED AI-reading check not in the debt
            gc.validate(reads_ai, gc.DEBT, gc.WAIVERS)
        gc.validate(reads_ai, {"R5.ZZ_SYNTHETIC": {"ai_input": "x", "plan": "y"}}, gc.WAIVERS)  # CONTROL: listed
        with self.assertRaises(gc.CheckError):  # FAULT: a stale debt entry (a GAME check)
            gc.validate(gc.CHECKS, {**gc.DEBT, "R5.CH1_REACHED": {"ai_input": "x", "plan": "y"}}, gc.WAIVERS)
        with self.assertRaises(gc.CheckError):  # FAULT: a waiver for no check
            gc.validate(gc.CHECKS, gc.DEBT, {"R5.NOT_A_CHECK": {"reason": "x"}})

    def test_the_import_itself_validates(self):
        """The module refuses to load with a debt file that misses a check (the call at import, not just the function)."""
        source = (Path(gc.__file__)).read_text(encoding="utf-8")
        # (the re-sourcing fix round: the debt is EMPTY) the FAULT is now the table's side: R5.NO_LOAFING patched back to
        # reading the AI, with the real (empty) debt file. The stale-entry side is the second fault below
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "debt.json"
            debt = json.loads(gc.DEBT_FILE.read_text(encoding="utf-8"))
            self.assertEqual(debt["debt"], {})
            bad.write_text(json.dumps(debt), encoding="utf-8")
            patched = source.replace('DEBT_FILE = GATES / "b1_debt.json"', f"DEBT_FILE = Path({str(bad)!r})").replace(
                '"R5.NO_LOAFING": _spec(GRADED, G,', '"R5.NO_LOAFING": _spec(GRADED, G + "+" + A,')
            self.assertEqual(patched.count('"R5.NO_LOAFING": _spec(GRADED, G + "+" + A,'), 1)
            def load(text: str, name: str) -> None:
                module = types.ModuleType(name)
                module.__file__ = gc.__file__
                sys.modules[name] = module
                try:
                    exec(compile(text, name, "exec"), module.__dict__)
                finally:
                    sys.modules.pop(name, None)

            with self.assertRaisesRegex(ValueError, re.escape("R5.NO_LOAFING: a GRADED check that reads an AI input")) as raised:
                load(patched, "grader_checks_patched")  # FAULT (the patched module's own CheckError, a ValueError)
            self.assertEqual(type(raised.exception).__name__, "CheckError")
            stale = Path(folder) / "stale.json"
            stale.write_text(json.dumps({"debt": {"R5.NO_LOAFING": {"ai_input": "x", "plan": "y"}}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, re.escape("b1_debt.json lists 'R5.NO_LOAFING', which is not a GRADED")):
                load(source.replace('DEBT_FILE = GATES / "b1_debt.json"', f"DEBT_FILE = Path({str(stale)!r})"),
                     "grader_checks_stale")  # FAULT: a paid debt left in the file
            load(source.replace('DEBT_FILE = GATES / "b1_debt.json"', f"DEBT_FILE = Path({str(gc.DEBT_FILE)!r})"),
                 "grader_checks_good")  # CONTROL

    def test_the_files_refuse_an_entry_without_its_reason(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "w.json"
            path.write_text(json.dumps({"waivers": {"R5.CH1_REACHED": {"reason": " "}}}), encoding="utf-8")
            with self.assertRaises(gc.CheckError):
                gc.load_waivers(path)
            path.write_text(json.dumps({"debt": {"R5.NO_LOAFING": {"ai_input": "x"}}}), encoding="utf-8")
            with self.assertRaises(gc.CheckError):
                gc.load_debt(path)
            path.write_text(json.dumps({"waivers": {"R5.CH1_REACHED": {"reason": "known empty"}}}), encoding="utf-8")
            self.assertIn("R5.CH1_REACHED", gc.load_waivers(path))

    def test_vacuous_fails_unless_waived(self):
        empty = gc.grade("R5.CH1_REACHED", True, "CH1: the POKéDEX reached in 0 of 0", 0, 1)
        self.assertEqual(empty.status, gc.VACUOUS)  # FAULT: ok=True does not make it pass
        self.assertEqual(gc.verdict([empty], waivers={}), "FAIL")
        self.assertEqual(gc.verdict([empty], waivers={"R5.CH1_REACHED": {"reason": "r"}}), "PASS")  # CONTROL: waived
        self.assertTrue(gc.verdict_row(empty, {"R5.CH1_REACHED": {"reason": "r"}})[0])
        self.assertIn("(WAIVED)", gc.evidence_lines([empty], {"R5.CH1_REACHED": {"reason": "r"}})[0])
        self.assertEqual(gc.verdict([empty]), "FAIL")  # the real waiver file waives nothing
        full = gc.grade("R5.CH1_REACHED", True, "CH1: the POKéDEX reached in 1 of 1", 1, 1)
        self.assertEqual((full.status, gc.verdict([full])), (gc.PASS, "PASS"))  # CONTROL
        self.assertEqual(gc.verdict([]), "FAIL")  # no check at all

    def test_grade_needs_its_title_its_count_and_a_known_id(self):
        with self.assertRaises(gc.CheckError):
            gc.grade("R5.CH1_REACHED", True, "something else", 1, 1)  # FAULT: the text is another check's
        with self.assertRaises(gc.CheckError):
            gc.grade("R5.CH1_REACHED", True, "CH1: the POKéDEX reached")  # FAULT: a counted check with no n
        with self.assertRaises(gc.CheckError):
            gc.grade("R5.NO_SUCH", True, "x", 1, 1)
        gc.grade("R5.CH1_WILD_WON", True, "CH1 (reported): wild battles WON anywhere ...")  # CONTROL: REPORTED, no n

    def test_an_untyped_check_never_reaches_a_verdict(self):
        with self.assertRaises(gc.CheckError):  # FAULT
            gc.as_check((True, "A CHECK NOBODY TYPED"), "R5")
        typed = gc.as_check((False, "CH2: WALLY's tutorial ..."), "R5")  # CONTROL: a title resolves
        self.assertEqual((typed.id, typed.kind, typed.status), ("R5.CH2_WALLY", gc.GRADED, gc.FAIL))
        with self.assertRaises(gc.CheckError):  # a rate title is no live title
            gc.as_check((True, "CH2: WALLY's tutorial ..."), "L5")

    def test_the_two_tuple_views(self):
        p2 = gc.grade("R5.CH2_OFF_UNDER", False, "CH2_OFF (the beeline control's chapter 2): under ...", 4)
        self.assertFalse(p2[0])  # the sub-verdict view: its own (old bound's) outcome
        row_ = gc.verdict_row(p2)
        self.assertTrue(row_[0])  # the verdict view: a REPORTED check never fails the sweep
        self.assertTrue(row_.text.startswith("(reported, 5.2 P2: a share of frames is not graded; the old bound did NOT hold)"))
        graded = gc.verdict_row(gc.grade("R5.CH2_WALLY", False, "CH2: WALLY's tutorial reached in 0 of 4", 4, 1))
        self.assertFalse(graded[0])


# ---------------------------------------------------------------------------------------------------------------- A1-2 (G-3)
class GraderImportTests(unittest.TestCase):
    def tree(self, files: dict[str, str]) -> Path:
        folder = Path(tempfile.mkdtemp(prefix="g3_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        for name, text in files.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return folder

    HELPER = ("from ai_player.mode import MAX_LOSSES  # the harness runs the AI\n"
              "import json\n\n"
              "LIMIT = MAX_LOSSES\n\n"
              "def clean(x):\n    return json.dumps(x)\n\n"
              "def tainted(x):\n    from ai_player.personality import ERRANDS\n    return ERRANDS[x]\n\n"
              "def through(x):\n    return tainted(x) + 1\n\n"
              "def by_constant():\n    return LIMIT\n")

    def scan(self, grader: str) -> list[str]:
        from ai_player.gates.check_grader_imports import scan
        root = self.tree({"ai_player/gates/helper.py": self.HELPER, "ai_player/gates/grader.py": grader})
        return scan(root, ("ai_player.gates.grader",))

    def test_a_direct_import_of_the_ai_is_caught(self):
        found = self.scan("def f():\n    from ai_player.brain.goals import ASIDE\n    return ASIDE\n")
        self.assertEqual(len(found), 1)  # FAULT
        self.assertIn("ai_player.brain.goals.ASIDE", found[0])
        self.assertEqual(self.scan("from ai_player.options import ENV_SEED\nfrom ai_player.host import launcher\n"), [])

    def test_the_ai_reached_through_a_gates_function_is_caught(self):
        for name in ("tainted", "through", "by_constant", "LIMIT"):
            found = self.scan(f"from ai_player.gates.helper import {name}\n")
            self.assertTrue(found, name)  # FAULT: the value comes from the AI
        self.assertEqual(self.scan("from ai_player.gates.helper import clean\n"), [])  # CONTROL
        self.assertTrue(self.scan("from ai_player.options import DEFAULT_MART_ITEM\n"))  # not an ENV_ name

    def test_a_mention_is_no_import(self):
        grader = ('"""from ai_player.personality import ERRANDS"""\n'
                  "# from ai_player.mode import MAX_LOSSES\n"
                  "TEXT = 'from ai_player.brain.goals import ASIDE'\n")
        self.assertEqual(self.scan(grader), [])

    def test_the_tree_as_it_stands_passes(self):
        from ai_player.gates.check_grader_imports import report, scan
        self.assertEqual(scan(), [])
        self.assertTrue(report([]).startswith("GRADER IMPORTS: PASS"))

    def test_the_rate_driver_refuses_on_a_breach(self):
        argv = ["rate_step5.py", "--purpose", "development", "--first-seed", "1", "--plans", "CH1", "--register"]
        with mock.patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()) as shown, \
                mock.patch.object(rs, "grader_imports_line", lambda: "GRADER IMPORTS: FAIL (G-3)\n  x"):
            self.assertEqual(rs.main(), 2)  # FAULT: refused before the ledger is touched
        self.assertIn("GRADER IMPORTS: FAIL", shown.getvalue())
        with mock.patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()), \
                mock.patch("sys.stderr", io.StringIO()), \
                mock.patch.object(rs, "grader_imports_line", lambda: "GRADER IMPORTS: PASS"):
            with self.assertRaises(SystemExit):  # CONTROL: past the rule, to --register's own refusal (development)
                rs.main()

    def test_the_live_driver_refuses_on_a_breach(self):
        from ai_player.gates import live_step5 as ls

        class Started(Exception):
            pass

        def started(_):
            raise Started

        with mock.patch.object(sys, "argv", ["live_step5.py", "--arms", "CH1T"]), redirect_stdout(io.StringIO()), \
                mock.patch.object(rs, "grader_imports_line", lambda: "GRADER IMPORTS: FAIL (G-3)"), \
                mock.patch.object(ls, "tree_provenance", started):
            self.assertEqual(ls.main(), 2)  # FAULT
        with mock.patch.object(sys, "argv", ["live_step5.py", "--arms", "CH1T"]), redirect_stdout(io.StringIO()), \
                mock.patch.object(rs, "grader_imports_line", lambda: "GRADER IMPORTS: PASS"), \
                mock.patch.object(ls, "tree_provenance", started):
            with self.assertRaises(Started):  # CONTROL: past the rule
                ls.main()


# ---------------------------------------------------------------------------------------------------------------- A1-2 values
class OwnedValueTests(unittest.TestCase):
    def test_the_ais_errands_no_longer_move_the_graders_bounds(self):
        from ai_player import personality
        before = {p: rs.train_steps_min(p) for p in rs.PERSONALITIES}
        import dataclasses
        edited = {name: dataclasses.replace(errands, train_min_steps=999, heal_below=0.99)
                  for name, errands in personality.ERRANDS.items()}
        with mock.patch.dict(personality.ERRANDS, edited):
            self.assertEqual(personality.ERRANDS["Story"].heal_below, 0.99)  # the AI's value IS moved here
            self.assertEqual({p: rs.train_steps_min(p) for p in rs.PERSONALITIES}, before)
            records = [{"decision": "goal", "action": "train", "extra": {"active": "Story"}},
                       {"decision": "decide", "action": "roam 50 steps"},
                       {"decision": "world", "frame": 10, "extra": {"kind": "wild", "outcome": "won",
                                                                    "party_hp_end": [13, 20]}},
                       {"decision": "world", "frame": 20, "extra": {"kind": "wild", "outcome": "won",
                                                                    "party_hp_end": [13, 20]}}]
            self.assertEqual(rs.roam_breaches(records), ([], 0))  # 0.65 is over the grader's 0.6, whatever the AI's
        self.assertEqual(before, {"Story": 72, "Catcher": 90, "Trainer": 135})

    def lose3(self, **more) -> bool:
        rows = [row("LOSE3", s, "Catcher", losses_game=4, losses_ai=4, losses_told=4, last_loss_f=1000, frames=1600,
                    reason="play: stuck: 4 battles lost (MAX_LOSSES 4)", **more) for s in (2, 5)]
        return next(c for c in rs.step51_verdicts({"LOSE3": rows}) if c.id == "R5.LOSE3").status == gc.PASS

    def test_lose3_grades_the_harness_recorded_max_losses(self):
        self.assertTrue(self.lose3(max_losses=4))  # CONTROL: the copy played with 4, the harness says so
        self.assertFalse(self.lose3(max_losses=3))  # FAULT: the run's stop text disagrees with the recorded limit
        # (the re-sourcing build) both runs reached their cap, so the check has its floor of samples: the disagreeing
        # records alone fail it (a sweep where none reached the cap is VACUOUS, which fails the verdict too)
        rows = [row("LOSE3", 2, "Catcher", max_losses=3, losses_game=3, last_loss_f=1000, frames=1600),
                row("LOSE3", 5, "Catcher", max_losses=4, losses_game=4, last_loss_f=1000, frames=1600)]
        self.assertEqual(next(c for c in rs.step51_verdicts({"LOSE3": rows}) if c.id == "R5.LOSE3").status, gc.FAIL)

    def patience(self, **more) -> str:
        rows = sweep()
        for r in rows["PATIENCE_OLD"]:
            r.update(more)
        return next(c for c in rs.step51_verdicts(rows) if c.id == "R5.PATIENCE_OLD").status

    def test_patience_old_is_graded_by_the_game(self):
        self.assertEqual(self.patience(), gc.PASS)  # CONTROL
        self.assertEqual(self.patience(reason="play: done: something else"), gc.PASS)  # its word is not graded now
        self.assertEqual(self.patience(reached=True), gc.FAIL)  # FAULT: the POKéDEX reached
        self.assertEqual(self.patience(frames=300000), gc.FAIL)  # FAULT: it ran out its budget
        word = next(c for c in rs.step51_verdicts(sweep()) if c.id == "R5.PATIENCE_OLD_WORD")
        self.assertEqual((word.kind, word.status), (gc.DIAGNOSTIC, gc.PASS))

    def test_a_chapter2_draw_is_judged_by_the_games_maps(self):
        draw = [{"decision": "goal", "action": "explore", "frame": 100, "reason": "a new place, LITTLEROOT_TOWN: a person"}]
        with tempfile.TemporaryDirectory() as folder:
            seen = Path(folder) / "seen_tiles.json"
            seen.write_text(json.dumps(["0:9:5:5", "0:9:5:6"]), encoding="utf-8")
            row_ = rs.grade_run("CH2", 1, "Story", "TREECKO", {}, draw, 1.0, seen_in=str(seen))
            self.assertEqual((row_["old_places"], row_["place_draws_judged"]), ([(100, "LITTLEROOT_TOWN")], 1))  # FAULT
            seen.write_text(json.dumps(["0:10:5:5"]), encoding="utf-8")
            row_ = rs.grade_run("CH2", 1, "Story", "TREECKO", {}, draw, 1.0, seen_in=str(seen))
            self.assertEqual((row_["old_places"], row_["place_draws_judged"]), ([], 1))  # CONTROL
        row_ = rs.grade_run("CH2", 1, "Story", "TREECKO", {}, draw, 1.0)
        self.assertEqual(row_["place_draws_judged"], 0)  # no game half: not judged

    def test_a_place_left_counts_the_draws_it_could_not_judge(self):
        records = [{"decision": "goal", "action": "explore", "frame": 900, "reason": "a new place, OLDALE_TOWN: x"},
                   {"decision": "goal", "action": "explore", "frame": 950, "reason": "a new place, NOT_A_MAP: x"}]
        data = {"places": {"stays": [[0, "0:16"], [50, "0:10"], [400, "0:16"], [800, "0:10"]]}}
        self.assertEqual(rs.left_before(records, data, 0), ([(900, "OLDALE_TOWN")], 1, 1))
        self.assertEqual(rs.map_keys()["OLDALE_TOWN"], "0:10")  # the framework's MapRSE, not the AI's memory

    def live_run(self, told: str | None, name: str, gender: str):
        from ai_player.gates import live_step5 as ls
        run = ls.Run(ls.ARMS[0])
        if told is not None:
            run.records = [{"decision": "tell", "frame": 5, "reason": told}]
        run.after = {"name": name, "gender_name": gender}
        ls.grade_CH1(run)
        return next(c for c in run.checks if c.id == "L5.NAME_GENDER"), run

    TELL = ("intro: personality Story (named by the run; seed 17): gender GIRL (drawn with P(GIRL)=0.5), "
            "name 'MAY' (from GIRL's list)")

    def test_the_live_intent_is_the_runs_own_word(self):
        check, run = self.live_run(self.TELL, "MAY", "GIRL")
        self.assertEqual((check.kind, check.status), (gc.HONESTY, gc.PASS))  # CONTROL
        self.assertEqual(self.live_run(self.TELL, "BRENDAN", "BOY")[0].status, gc.FAIL)  # FAULT: the game disagrees
        self.assertEqual(self.live_run(None, "MAY", "GIRL")[0].status, gc.VACUOUS)  # FAULT: no word to judge
        self.assertTrue(all(isinstance(c, gc.Check) for c in run.checks))  # every live check typed, purity's included

    def test_a_live_arms_diagnostic_failure_does_not_fail_it(self):
        from ai_player.gates import live_step5 as ls
        run = ls.Run(ls.ARMS[0])
        run.check(True, "BOUNDED: 1 real frames <= the pre-registered 2", "L5.BOUNDED")
        run.check(False, "CURIOSITY SPACED: at most 9 curiosity goals in a row", "L5.SPACED", 1, None)
        self.assertTrue(run.passed)  # CONTROL
        run.check(False, "THE GAME (the bag): POKé BALLS {}", "L5.BALLS")
        self.assertFalse(run.passed)  # FAULT


# ---------------------------------------------------------------------------------------------------------------- A1-3
def numbers() -> dict:
    return rs.registered_numbers(["CH1", "NOTRAIN"], 300000, "ch1_pokedex")


def sha() -> str:
    from ai_player.gates import ledger
    return ledger.numbers_sha256(numbers())


class LedgerHashTests(unittest.TestCase):
    """A1-3 (the step-5.3 critic's Q5): every item the verdict depends on is in `registered_numbers`, so its sha moves when
    the item's SOURCE is edited (FAULT), and stays when nothing is (CONTROL); the ledger refuses a graded run registered
    before the check code changed."""

    #: (where it is edited in play_harness.py, the edit, the key of `harness_parameters`)
    HARNESS_EDITS = (("STEP_RATE = 8\n", "STEP_RATE = 9\n", "STEP_RATE"),
                     ("PUSH_KEEP = 300\n", "PUSH_KEEP = 301\n", "PUSH_KEEP"),
                     ("WAIT_KEEP = 60\n", "WAIT_KEEP = 61\n", "WAIT_KEEP"),
                     ('parser.add_argument("--every", type=int, default=30,',
                      'parser.add_argument("--every", type=int, default=31,', "main --every"),
                     ("def __init__(self, controls, every: int = 10, seen",
                      "def __init__(self, controls, every: int = 11, seen", "PlaceRecorder.every"),
                     ("def __init__(self, controls: HarnessControls, every: int = 10)",
                      "def __init__(self, controls: HarnessControls, every: int = 11)", "WaitRecorder.every"))

    def moved(self, key: str) -> None:
        """The sha moved, and `key` is among the items whose value moved (the edit reached the hash by its own name)."""
        self.assertNotEqual(sha(), self.before_sha, f"{key}: the sha did not move")
        after = {k: json.dumps(v, sort_keys=True, default=str) for k, v in numbers().items()}
        self.assertIn(key, {k for k in after if after[k] != self.before[k]})

    def setUp(self):
        # a SNAPSHOT (text): the numbers hold the module's own dicts, which a patch edits in place
        self.before = {k: json.dumps(v, sort_keys=True, default=str) for k, v in numbers().items()}
        self.before_sha = sha()

    def test_the_same_tree_gives_the_same_sha(self):
        self.assertEqual(sha(), self.before_sha)  # CONTROL: deterministic, nothing edited
        for key in ("MUTANT_EDITS", "END_SLACK", "CURIOSITY_KINDS", "NEED_KINDS", "GENERIC_BUSY", "REAL_PLANS", "NO_PHASE2",
                    "PERSONALITIES", "STARTERS", "ERRANDS", "ERRAND_KINDS", "ASIDE", "MAX_LOSSES_DEFAULT", "CODE_BOUNDS",
                    "HARNESS_PARAMETERS", "FILES"):
            self.assertIn(key, self.before)
        self.assertEqual(set(json.loads(self.before["FILES"])), set(rs.HASHED_FILES))
        for name in ("ai_player/gates/rate_step5.py", "ai_player/gates/live_step5.py", "ai_player/gates/play_harness.py",
                     "ai_player/gates/window.py", "ai_player/knowledge/milestones.json",
                     "ai_player/gates/fixtures/item_flags.json", "ai_player/gates/b1_debt.json",
                     "ai_player/gates/grader_waivers.json",
                     # (A1 fix round, F5a) the check code the stage-A1 verifier found unhashed; each one's edit moving
                     # the sha is `test_each_hashed_file_moves_the_sha_and_a_line_end_does_not` (it walks HASHED_FILES)
                     "ai_player/gates/hands_harness.py", "ai_player/gates/live_step2.py",
                     "ai_player/gates/probe_presses.py", "ai_player/gates/probe_eyes.py"):
            self.assertIn(name, rs.HASHED_FILES)  # the spec's list, every one
            self.assertTrue(Path(rs.HASHED_FILES[name]).is_file(), name)

    def test_a_mutant_edit_text_moves_the_sha(self):
        from ai_player.gates import revert_step5
        for name in ("G36", "G46", "G67"):
            with self.subTest(name), mock.patch.dict(revert_step5.MUTANTS):
                prediction, what, edits, tests = revert_step5.MUTANTS[name]
                revert_step5.MUTANTS[name] = (prediction, what, [(f, old, new + "#") for f, old, new in edits], tests)
                self.moved("MUTANT_EDITS")  # FAULT: before 5.3 only the NAME was hashed
        with mock.patch.dict(rs.EXTRA_EDITS, {"CAP1": [("mode.py", "MAX_LOSSES = 3\n", "MAX_LOSSES = 2\n")]}):
            self.moved("MUTANT_EDITS")

    def test_the_edits_hashed_are_the_edits_a_copy_is_made_with(self):
        from ai_player.gates import revert_step5
        hashed = rs.mutant_edits()
        for plan, names in {**rs.MUTANT_PLANS, **rs.STOP_PLANS}.items():
            with self.subTest(plan), mock.patch.object(revert_step5, "make_copy", side_effect=lambda edits: edits):
                self.assertEqual(rs.copy_with(names), [e for n in names for e in hashed[n]])

    def test_each_grader_constant_moves_the_sha(self):
        edits = {"END_SLACK": rs.END_SLACK + 1, "CURIOSITY_KINDS": rs.CURIOSITY_KINDS[:-1],
                 "NEED_KINDS": rs.NEED_KINDS[:-1], "GENERIC_BUSY": rs.GENERIC_BUSY + "!", "REAL_PLANS": rs.REAL_PLANS[:-1],
                 "NO_PHASE2": rs.NO_PHASE2[:-1], "PERSONALITIES": rs.PERSONALITIES[::-1], "STARTERS": rs.STARTERS[::-1],
                 "ERRANDS": {**rs.ERRANDS, "Story": rs.GraderErrands(81, 0.6)}, "ERRAND_KINDS": rs.ERRAND_KINDS[:-1],
                 "ASIDE": "aside;", "MAX_LOSSES_DEFAULT": rs.MAX_LOSSES_DEFAULT + 1}
        for name, value in edits.items():
            with self.subTest(name), mock.patch.object(rs, name, value):
                self.moved(name)

    def test_each_code_bound_moves_the_sha(self):
        for key in rs.CODE_BOUNDS:
            with self.subTest(key), mock.patch.dict(rs.CODE_BOUNDS, {key: "edited"}):
                self.moved("CODE_BOUNDS")

    def test_each_harness_parameter_moves_the_sha_and_a_missing_one_refuses(self):
        text = rs.HARNESS.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as folder:
            for old, new, key in self.HARNESS_EDITS:
                with self.subTest(key):
                    self.assertEqual(text.count(old), 1, old)
                    copy = Path(folder) / f"play_harness_{len(key)}_{key.replace(' ', '_')}.py"
                    copy.write_text(text.replace(old, new), encoding="utf-8")
                    self.assertNotEqual(rs.harness_parameters(copy)[key], rs.harness_parameters()[key])
                    with mock.patch.object(rs, "HARNESS", copy), \
                            mock.patch.dict(rs.HASHED_FILES, {"ai_player/gates/play_harness.py": copy}):
                        self.moved("HARNESS_PARAMETERS")
            gone = Path(folder) / "play_harness_gone.py"
            gone.write_text(text.replace("STEP_RATE = 8\n", "STEPS_RATE = 8\n"), encoding="utf-8")
            with self.assertRaises(ValueError):  # FAULT: a renamed parameter refuses instead of leaving the hash
                rs.harness_parameters(gone)

    def test_each_hashed_file_moves_the_sha_and_a_line_end_does_not(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, path in rs.HASHED_FILES.items():
                with self.subTest(name):
                    data = Path(path).read_bytes()
                    copy = Path(folder) / Path(name).name
                    copy.write_bytes(data + b"\n# edited\n")
                    with mock.patch.dict(rs.HASHED_FILES, {name: copy}):
                        self.moved("FILES")  # FAULT: the file's content edited
                    copy.write_bytes(data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
                    with mock.patch.dict(rs.HASHED_FILES, {name: copy}):
                        self.assertEqual(sha(), self.before_sha)  # CONTROL: the same text with other line ends
            with mock.patch.dict(rs.HASHED_FILES, {"ai_player/gates/window.py": Path(folder) / "missing.py"}), \
                    self.assertRaises(OSError):
                numbers()  # FAULT: a missing file is no hash of nothing

    def test_the_ledger_refuses_a_graded_run_once_the_check_code_changed(self):
        from ai_player.gates import ledger
        with tempfile.TemporaryDirectory() as folder:
            book = Path(folder) / "ledger.json"
            ledger.register("story", "rate_step5", 7001, 7002, self.before_sha, path=book)
            edited = Path(folder) / "rate_step5.py"
            edited.write_text(Path(rs.HASHED_FILES["ai_player/gates/rate_step5.py"]).read_text(encoding="utf-8")
                              .replace("\"CATCH_ALL_MAX\": 0,", "\"CATCH_ALL_MAX\": 0,  # edited", 1), encoding="utf-8")
            with mock.patch.dict(rs.HASHED_FILES, {"ai_player/gates/rate_step5.py": edited}):
                with self.assertRaises(ledger.Refused):  # FAULT: the verdict code changed after --register
                    ledger.begin("story", "rate_step5", "graded", 7001, 7002, sha(), None, path=book)
            entry, _ = ledger.begin("story", "rate_step5", "graded", 7001, 7002, sha(), None, path=book)  # CONTROL
            self.assertEqual(entry["status"], "started")


class LiteralBoundTests(unittest.TestCase):
    """A1-3: the literals of the verdict code (`CODE_BOUNDS`) and #11/#17's bound keys are READ by their checks, so the
    hash of each is the hash of what the check does: tightening each one FAILS its check on the healthy sweep (FAULT); the
    registered values PASS it (CONTROL)."""

    CASES = ((rs.CODE_BOUNDS, "CATCH_ALL_MAX", -1, ("R5.CH1_CATCH_ALL",)),
             (rs.CODE_BOUNDS, "RECORDER_GAP", (1, 1), ("R5.CH1_RECORDER",)),
             (rs.CODE_BOUNDS, "NOTRAIN_LEVEL_WORST", 2, ("R5.NOTRAIN_LEVEL",)),
             (rs.CODE_BOUNDS, "REST_BREACHES_MAX", -1, ("R5.CH1_REST_RULE", "R5.DEADREST")),
             (rs.CODE_BOUNDS, "DEADREST_BREACHES_OVER", 99, ("R5.DEADREST",)),
             (rs.BOUNDS, "NOTRAIN_WILD_LESS", False, ("R5.NOTRAIN_MECHANISM",)),
             (rs.BOUNDS, "NOHINTS_SLOWER", False, ("R5.NOHINTS_SLOWER",)))

    def test_each_named_literal_is_read_by_its_check(self):
        healthy = by_id(grade_sweep(sweep()))
        for table, key, value, ids in self.CASES:
            with self.subTest(key):
                for check_id in ids:
                    self.assertEqual(healthy[check_id][0].status, gc.PASS)  # CONTROL
                with mock.patch.dict(table, {key: value}):
                    edited = by_id(grade_sweep(sweep()))
                for check_id in ids:
                    self.assertEqual(edited[check_id][0].status, gc.FAIL, f"{key} -> {value}: {check_id}")  # FAULT


# ---------------------------------------------------------------------------------------------------------------- A1-4
def bound_readers(path: Path, call: str) -> dict[str, set]:
    """Which check ids read which `BOUNDS` key in a grader's source (by its syntax tree), per function: a read inside a
    `call(...)` whose first or third argument is a check id is that check's; a read in an assignment is the check's whose
    call uses the assigned name; a read inside a `.notes.append(...)` is no check's (a note); any other read (a helper's,
    a row's) is "?", taken as COUNTED (the conservative side: it cannot make a bound look ungraded)."""
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, set] = {}

    def keys_in(node) -> set:
        return {n.slice.value for n in ast.walk(node) if isinstance(n, ast.Subscript)
                and getattr(n.value, "id", None) == "BOUNDS" and isinstance(n.slice, ast.Constant)}

    def check_id(node) -> str | None:
        if not (isinstance(node, ast.Call) and (getattr(node.func, "id", None) == call
                                                or getattr(node.func, "attr", None) == call)):
            return None
        for arg in node.args[:1] + node.args[2:3]:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value[:3] in ("R5.", "L5."):
                return arg.value
        return None

    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        checks = [(node, check_id(node)) for node in ast.walk(fn) if check_id(node)]
        attributed: set[int] = set()
        for node, cid in checks:
            for key in keys_in(node):
                out.setdefault(key, set()).add(cid)
            # the assignments that REACH the call: for each name it uses, the last one to the name above it (a name is
            # reused: `over`), followed through the names THAT value uses (`low = {...}; low = {... low ...}`)
            todo = [(n.id, node.lineno) for n in ast.walk(node) if isinstance(n, ast.Name)]
            seen: set = set()
            while todo:
                name, line = todo.pop()
                before = [stmt for stmt in ast.walk(fn) if isinstance(stmt, ast.Assign) and stmt.lineno < line
                          and any(isinstance(t, ast.Name) and t.id == name for t in stmt.targets)]
                if not before:
                    continue
                stmt = max(before, key=lambda s: s.lineno)
                if id(stmt) in seen:
                    continue
                seen.add(id(stmt))
                for key in keys_in(stmt.value):
                    out.setdefault(key, set()).add(cid)
                attributed |= {id(n) for n in ast.walk(stmt.value)}
                todo += [(n.id, stmt.lineno) for n in ast.walk(stmt.value) if isinstance(n, ast.Name)]
            attributed |= {id(n) for n in ast.walk(node)}
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "append" \
                    and getattr(getattr(node.func, "value", None), "attr", None) == "notes":
                attributed |= {id(n) for n in ast.walk(node)}
        for node in ast.walk(fn):
            if id(node) not in attributed and isinstance(node, ast.Subscript) \
                    and getattr(node.value, "id", None) == "BOUNDS" and isinstance(node.slice, ast.Constant):
                out.setdefault(node.slice.value, set()).add("?")
    return out


class UngradedBoundTests(unittest.TestCase):
    """A1-4: `grader_checks.UNGRADED_BOUNDS` (the bounds only non-counting checks read, which a lesson may not call
    Enforced) is held to the code both ways: by the graders' syntax (it is exactly the keys whose every reader is a check
    that never counts), and by behaviour (tightening each one moves its own checks but not the healthy sweep's verdict;
    tightening a GRADED bound fails it)."""

    def test_the_table_is_exactly_the_bounds_no_counted_check_reads(self):
        readers: dict[str, set] = {}
        for path, call in ((GATES / "rate_step5.py", "grade"), (GATES / "live_step5.py", "check")):
            for key, ids in bound_readers(path, call).items():
                readers.setdefault(key, set()).update(ids)
        ungraded = {key for key, ids in readers.items()
                    if all(i != "?" and gc.CHECKS[i].kind not in gc.COUNTED for i in ids)}
        self.assertEqual(ungraded, set(gc.UNGRADED_BOUNDS))
        for key, ids in gc.UNGRADED_BOUNDS.items():
            self.assertEqual(set(ids), readers[key], key)
        # CONTROL: a bound read by counting checks and by one that does not count (R5.NO_LOAFING and R5.LOAF GRADED,
        # L5.NO_LOAFING DIAGNOSTIC) is not in the table. (Before the A1 fix round this control was ASIDE_STREAK_MAX, read by
        # a GRADED L5.ASIDE_BACK; ruling F4 made that check DIAGNOSTIC, so the bound is now ungraded and in the table.)
        # (the re-sourcing fix round) its readers now include R5.PUSH_PATHS_AGREE (HONESTY: the paths' verdicts at each push
        # bound) and the helper `game_loafed` ("?", taken as counted)
        self.assertEqual(readers["LOAF_FRAMES_MAX"], {"R5.NO_LOAFING", "R5.LOAF", "R5.PUSH_PATHS_AGREE", "L5.NO_LOAFING", "?"})
        self.assertNotIn("LOAF_FRAMES_MAX", gc.UNGRADED_BOUNDS)
        self.assertEqual(set(gc.UNGRADED_BOUNDS["ASIDE_STREAK_MAX"]), {"R5.ASIDE_BACK", "L5.ASIDE_BACK"})

    def test_tightening_an_ungraded_bound_moves_its_checks_but_not_the_verdict(self):
        healthy = grade_sweep(sweep())
        self.assertEqual(gc.verdict(healthy), "PASS")
        before = {c.id: c.status for c in healthy}
        for key, ids in gc.UNGRADED_BOUNDS.items():
            value = BOUNDS[key]
            # (the re-sourcing fix round) BLOCKED_REACH_HITS is a minimum too (blocks met at least this many times)
            tight = 10 ** 9 if key.endswith(("_MIN", "_HITS")) else -10 ** 9
            with self.subTest(key), mock.patch.dict(BOUNDS, {key: tight}):
                edited = grade_sweep(sweep())
                self.assertEqual(gc.verdict(edited), "PASS", key)  # it counts in no verdict
                moved = {c.id for c in edited if c.status != before.get(c.id)}
                rate_ids = {i for i in ids if i.startswith("R5.")}
                self.assertTrue(moved & rate_ids, f"{key} (= {value}) -> {tight} moved none of {rate_ids}: not read?")
        # CONTROL: a GRADED bound tightened the same way fails the sweep
        with mock.patch.dict(BOUNDS, {"LOAF_FAILS_RUNS_MIN": 10 ** 9}):
            self.assertEqual(gc.verdict(grade_sweep(sweep())), "FAIL")

    def test_check_lessons_resolves_check_ids_and_ungraded_bounds(self):
        from ai_player.gates import check_lessons
        with tempfile.TemporaryDirectory() as folder:
            doc = Path(folder) / "08.md"
            doc.write_text("the quoted origin\n", encoding="utf-8")

            def problems(enforced: str, reported: str = "", title: str = "a rule") -> list[str]:
                text = (f"### PF-1. {title}\n- **Origin:** 2026-10-23, 08 \"the quoted origin\"\n- **Status:** GATED\n"
                        f"- **Enforced:** {enforced}\n" + (f"- **Reported:** {reported}\n" if reported else "")
                        + "- **Retires:** never.\n")
                return check_lessons.check(text, documents={"08": doc}, required=())[0]

            # CONTROL: counting checks and a graded bound on Enforced; non-counting ones on Reported; a mention is prose
            self.assertEqual(problems("`R5.CH1_REACHED`, `L5.NAME_GENDER`, `rate_step5:BOUNDS.CH1_REACHED_MIN`",
                                      "`R5.CH1_FREE`, `R5.SPACED`, `rate_step5:BOUNDS.MIX_MIN`",
                                      title="R5.SPACED is mentioned in a title"), [])
            # FAULT: a REPORTED or DIAGNOSTIC check, an unknown id, or an ungraded bound called Enforced
            for token in ("`R5.CH1_INTENT_MIX`", "`R5.SPACED`", "`L5.POOLED_SPINS`", "`R5.NO_SUCH_CHECK`",
                          "`rate_step5:BOUNDS.MIX_MIN`", "`rate_step5:BOUNDS.SPACING_ROW_MAX`"):
                with self.subTest(enforced=token):
                    self.assertEqual(len(problems(f"`gates/ledger.py`, {token}")), 1, token)
            # FAULT: a counting check, a graded bound or a non-check named on the Reported line
            for token in ("`R5.CH1_REACHED`", "`rate_step5:BOUNDS.CH1_REACHED_MIN`", "`gates/ledger.py`",
                          "`R5.NO_SUCH_CHECK`"):
                with self.subTest(reported=token):
                    self.assertEqual(len(problems("`gates/ledger.py`", token)), 1, token)

    def test_the_import_refuses_an_ungraded_bound_whose_reader_counts(self):
        gc.validate(gc.CHECKS, gc.DEBT, gc.WAIVERS)  # CONTROL: the table as it stands
        for wrong in ("R5.CH1_REACHED", "R5.NO_SUCH_CHECK"):
            with self.subTest(wrong), mock.patch.dict(gc.UNGRADED_BOUNDS, {"MIX_MIN": ("R5.CH1_INTENT_MIX", wrong)}):
                with self.assertRaises(gc.CheckError):  # FAULT: a counting (or unknown) reader listed as ungraded
                    gc.validate(gc.CHECKS, gc.DEBT, gc.WAIVERS)


class A1WiringTests(unittest.TestCase):
    """The A1 calls that the tests above did not reach (each found by a call-deleting mutant that SURVIVED them, builder B,
    2026-10-23): the row fields `grade_run` and `run_one` write, LOSE3's one-limit rule, the live arm's untyped (purity)
    path, its map keys, its evidence file and its pooled DIAGNOSTIC lines, and the harness's record of MAX_LOSSES."""

    def test_lose3_fails_when_its_runs_recorded_two_limits(self):
        rows = sweep()["LOSE3"]  # both reached 3 losses and ended "MAX_LOSSES 3"
        status = lambda: next(c for c in rs.step51_verdicts({"LOSE3": rows}) if c.id == "R5.LOSE3").status
        for r in rows:
            r["max_losses"] = 3
        self.assertEqual(status(), gc.PASS)  # CONTROL: one arm, one stop
        rows[1]["max_losses"] = 4
        self.assertEqual(status(), gc.FAIL)  # FAULT: only the one-limit rule is broken (the limit read is 3, both ended so)

    def test_grade_run_writes_the_harness_limit_and_the_place_left(self):
        records = [{"decision": "watch", "frame": 0},  # the log's first frame is the run's offset
                   {"decision": "goal", "action": "explore", "frame": 900, "reason": "a new place, OLDALE_TOWN: x"},
                   {"decision": "goal", "action": "explore", "frame": 950, "reason": "a new place, NOT_A_MAP: x"}]
        data = {"max_losses": 5, "places": {"stays": [[0, "0:16"], [50, "0:10"], [400, "0:16"], [800, "0:10"]]}}
        row_ = rs.grade_run("CH1", 1, "Story", "TREECKO", data, records, 1.0)
        self.assertEqual(row_["max_losses"], 5)  # the PLAY json's record, as LOSE3 grades it
        self.assertEqual((row_["left_called_new"], row_["left_judged"], row_["left_skipped"]),
                         ([(900, "OLDALE_TOWN")], 1, 1))  # FAULT half: the draw on a map it had left
        row_ = rs.grade_run("CH1", 1, "Story", "TREECKO", {}, records, 1.0)
        self.assertEqual((row_["max_losses"], row_["left_called_new"], row_["left_judged"]), (None, [], 0))  # CONTROL

    def test_run_one_writes_the_frame_budget(self):
        play = types.SimpleNamespace(stdout=b"PLAY " + json.dumps({"seen_file": None}).encode(), stderr=b"")
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(rs.subprocess, "run", lambda *a, **k: play), \
                mock.patch.object(rs.tempfile, "mkdtemp", lambda prefix: str(Path(folder) / prefix)), \
                mock.patch.object(rs, "grade_run", lambda *a, **k: {"plan": "PATIENCE_OLD", "seed": 3}):
            (Path(folder) / "ai_step5_PATIENCE_OLD_3_").mkdir()
            self.assertEqual(rs.run_one("PATIENCE_OLD", 3, 123456, "ch1_pokedex")["budget"], 123456)

    def test_the_live_purity_path_is_typed(self):
        from ai_player.gates import live_step5 as ls
        run = ls.Run(ls.ARMS[0])
        run.check(True, "verdict file: verdict=ok, errors=0")  # live_step2.check_purity's call: no id, typed by title
        self.assertEqual([(c.id, c.kind) for c in run.checks], [("L5.PURITY_CLEAN", gc.GRADED)])
        with self.assertRaises(gc.CheckError):  # FAULT: a text no title starts never reaches the verdict
            run.check(True, "an untyped line")

    def new_place(self, left_from: str):
        from ai_player.gates import live_step5 as ls
        run = ls.Run(ls.ARMS[0])
        run.records = [{"decision": "world", "frame": 100, "extra": {"transition": [100, left_from]}},
                       {"decision": "goal", "action": "explore", "frame": 900, "reason": "a new place, OLDALE_TOWN: x"}]
        ls.check_new_places(run)
        return next(c for c in run.checks if c.id == "L5.NEW_PLACE").status

    def test_the_live_place_left_is_keyed_by_the_maps_table(self):
        self.assertEqual(self.new_place("0:16"), gc.PASS)  # CONTROL: it left LITTLEROOT, not OLDALE
        self.assertEqual(self.new_place("0:10"), gc.FAIL)  # FAULT: it had left OLDALE (MapRSE 0:10) and called it new

    def test_the_live_evidence_file_carries_every_typed_line(self):
        from ai_player.gates import live_step5 as ls
        run = ls.Run(ls.ARMS[0])
        run.check(True, "BOUNDED: 1 real frames <= the pre-registered 2", "L5.BOUNDED")
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(ls, "EVIDENCE_DIR", Path(folder)), \
                mock.patch.object(ls, "keep_earlier", lambda path: None):
            text = ls.write_evidence(run, "code", "test").read_text(encoding="utf-8")
        self.assertIn("  [PASS] L5.BOUNDED GRADED n/floor 1/1 inputs ", text)

    def drive_live(self, spins: int) -> tuple[int, str]:
        """`live_step5.main` for one CH1 arm, every side effect faked; the arm's own checks all PASS."""
        from ai_player.gates import live_step5 as ls
        tree = types.SimpleNamespace(stats={}, digest="d", moved=False, moves=[], check=lambda *a: True,
                                     seal=lambda verdict: (verdict, "FROZEN TREE: PASS"))

        def run_arm(arm, build_root, carried):
            run = ls.Run(arm)
            run.measures = {"spins": spins, "roam_steps": 100, "rest_occasions": 2}
            return run

        def grader(run):
            run.check(True, "BOUNDED: 1 real frames <= the pre-registered 2", "L5.BOUNDED")

        with mock.patch.object(sys, "argv", ["live_step5.py", "--arms", "CH1T"]), redirect_stdout(io.StringIO()) as shown, \
                mock.patch.object(rs, "grader_imports_line", lambda: "GRADER IMPORTS: PASS"), \
                mock.patch.object(ls, "tree_provenance", lambda repo: "code"), \
                mock.patch.object(ls, "watch", lambda *a, **k: tree), \
                mock.patch.object(ls, "snapshot_tree", lambda repo: "kept"), \
                mock.patch.object(ls, "run_arm", run_arm), mock.patch.dict(ls.GRADERS, {"CH1T": grader}), \
                mock.patch.object(ls, "write_evidence", lambda *a: Path("evidence.txt")), \
                mock.patch.object(ls, "leftover_processes", lambda: []):
            code = ls.main()
        return code, shown.getvalue()

    def test_the_live_pooled_checks_are_printed_and_never_counted(self):
        code, shown = self.drive_live(spins=0)
        self.assertEqual(code, 0)  # CONTROL
        self.assertIn("[LIVE5] [PASS] L5.POOLED_SPINS DIAGNOSTIC n/floor 100/1", shown)
        code, shown = self.drive_live(spins=50)
        self.assertIn("[LIVE5] [FAIL] L5.POOLED_SPINS DIAGNOSTIC n/floor 100/1", shown)  # printed ...
        self.assertEqual(code, 0)  # ... and NOT counted: the overall verdict stands on the arms' own checks
        self.assertIn("[LIVE5] OVERALL PASS", shown)

    def test_the_harness_records_the_max_losses_it_played_with(self):
        """`play_harness.play` needs the ROM, so this reads its SOURCE: the PLAY json's `max_losses` is the `MAX_LOSSES` the
        play loop imports from `ai_player.mode` inside `play` (the value the run played with; a copy's CAP1 edit included)."""
        import ast
        tree = ast.parse(rs.HARNESS.read_text(encoding="utf-8"))
        play = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "play")
        imported = {alias.name for n in ast.walk(play) if isinstance(n, ast.ImportFrom) and n.module == "ai_player.mode"
                    for alias in n.names}
        self.assertIn("MAX_LOSSES", imported)
        recorded = [v for n in ast.walk(play) if isinstance(n, ast.Dict) for k, v in zip(n.keys, n.values)
                    if isinstance(k, ast.Constant) and k.value == "max_losses"]
        self.assertEqual([getattr(v, "id", None) for v in recorded], ["MAX_LOSSES"])


# ---------------------------------------------------------------------------------------------------------------- A1 fix round
def no_draws(rows: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """The healthy sweep with NO look-around draw anywhere (the 5.3 A1 smoke's 6 real runs: place_draws 0, left_judged 0)."""
    for plan_rows in rows.values():
        for r in plan_rows:
            r.update(place_draws=0, place_draws_judged=0, old_places=[], left_called_new=[], left_judged=0, left_skipped=0)
    return rows


def check_of(results, check_id: str):
    return by_id(results)[check_id][0]


class AbsenceWaiverTests(unittest.TestCase):
    """(A1 fix round, the coordinator's ruling F1 on the stage-A1 verifier's failure 1) R5.LEFT_NOT_NEW (#61) and
    R5.CH2_NEW_PLACE (#44) keep their honest n (the draws JUDGED) and are WAIVED in `grader_waivers.json`: each is an
    absence guard, and a sweep where the AI drew no 'a new place' look round has nothing to judge. The evidence still prints
    them VACUOUS (waived), never PASS; a waived check that judged a wrong draw still FAILS; and nothing else is waived (a
    plan whose rows ALL errored still fails the sweep)."""

    ABSENCE = {"R5.LEFT_NOT_NEW", "R5.CH2_NEW_PLACE"}

    def test_the_waiver_file_waives_exactly_the_two_absence_guards(self):
        # (the 5.3 re-sourcing build, item 13: the re-sourcing plan's (c)) and L5.SHOPPED's no-claim VACUOUS, whose game
        # achievement is graded apart (`test_step53_rs.ShoppedTests`): nothing else is waived
        self.assertEqual(set(gc.WAIVERS), self.ABSENCE | {"L5.SHOPPED"})
        self.assertIn("L5.SHOPPED_GAME", gc.WAIVERS["L5.SHOPPED"]["reason"])
        self.assertEqual(gc.CHECKS["L5.SHOPPED"].kind, gc.HONESTY)
        for key in self.ABSENCE:
            reason = gc.WAIVERS[key]["reason"]
            self.assertIn("ABSENCE", reason, key)
            self.assertIn("Stage B", reason, key)  # who removes it, and when
            self.assertEqual(gc.CHECKS[key].kind, gc.HONESTY, key)

    def test_a_sweep_with_no_draw_reads_vacuous_waived_and_passes(self):
        results = grade_sweep(no_draws(sweep()))
        for key in sorted(self.ABSENCE):
            check = check_of(results, key)
            self.assertEqual((check.status, check.n, check.floor), (gc.VACUOUS, 0, 1), key)  # the honest n
            self.assertTrue(gc.waived(check), key)
        self.assertEqual(gc.verdict(results), "PASS")  # CONTROL: the 5.2 outcome, kept by the waiver
        self.assertTrue(all(ok for ok, _ in results))  # the verdict view agrees
        self.assertEqual(gc.verdict(results, waivers={}), "FAIL")  # FAULT: without the waiver the same sweep fails
        lines = gc.evidence_lines(results)
        for key in sorted(self.ABSENCE):
            line = next(line for line in lines if f" {key} " in line and line.startswith("  ["))
            self.assertTrue(line.startswith(f"  [VACUOUS] (WAIVED) {key} HONESTY n/floor 0/1 "), line)  # never PASS
        self.assertFalse([line for line in lines if line.startswith(("  [PASS] R5.LEFT_NOT_NEW", "  [PASS] R5.CH2_NEW_PLACE"))])

    def test_a_waived_guard_that_judged_a_wrong_draw_still_fails(self):
        rows = no_draws(sweep())
        rows["CH1"][0].update(left_called_new=[(900, "OLDALE_TOWN")], left_judged=1)
        results = grade_sweep(rows)
        self.assertEqual(check_of(results, "R5.LEFT_NOT_NEW").status, gc.FAIL)  # FAULT: the waiver covers VACUOUS only
        self.assertEqual(gc.verdict(results), "FAIL")
        rows = no_draws(sweep())
        rows["CH2"][0].update(old_places=[(100, "LITTLEROOT_TOWN")], place_draws=1, place_draws_judged=1)
        results = grade_sweep(rows)
        self.assertEqual(check_of(results, "R5.CH2_NEW_PLACE").status, gc.FAIL)  # FAULT
        self.assertEqual(gc.verdict(results), "FAIL")
        self.assertEqual(gc.verdict(grade_sweep(sweep())), "PASS")  # CONTROL: draws judged, none wrong

    def test_a_sweep_whose_runs_all_errored_still_fails(self):
        """The distinction ruling F1 keeps: a run that did not happen is no absence of a draw. Every row errored: the two
        absence guards are not emitted at all (their graders return early when no real run played), so their waivers
        cannot apply, and the sweep FAILS on its other VACUOUS checks, which no waiver covers."""
        rows = sweep()
        for plan_rows in rows.values():
            for r in plan_rows:
                r["error"] = "the run did not happen (synthetic)"
        results = grade_sweep(rows)
        unwaived = [c.id for c in results if c.kind in gc.COUNTED and c.status == gc.VACUOUS and not gc.waived(c)]
        self.assertTrue(unwaived)  # e.g. R5.LOSSES_AGREE, n = the runs that played
        self.assertEqual(gc.verdict(results), "FAIL")  # FAULT: the waiver does not pass a sweep that never ran
        self.assertFalse({c.id for c in results} & self.ABSENCE)  # not emitted: no waiver is in play


class SurvivingMutantTests(unittest.TestCase):
    """(A1 fix round, F2) the four guard mutants that SURVIVED the stage-A1 verifier, each now failing a SEMANTIC test:
    M17 (`validate`: a dropped property only on a DIAGNOSTIC check), M18 (no title is the start of another of its grader:
    `as_check` resolves by the start), M42 (#44's n is the draws judged, not the runs), M45 (R5.STOP's n is the runs with
    a loss, not max(1, ...))."""

    def test_m17_a_dropped_property_is_only_on_a_diagnostic_check(self):
        gc.validate(gc.CHECKS, gc.DEBT, gc.WAIVERS)  # CONTROL: the table as it stands
        import dataclasses
        for key in ("R5.CH1_REACHED", "R5.LOSSES_AGREE", "R5.CH1_WILD_WON"):  # GRADED, HONESTY, REPORTED
            with self.subTest(key):
                table = {**gc.CHECKS, key: dataclasses.replace(gc.CHECKS[key], dropped="a property nobody grades")}
                with self.assertRaisesRegex(gc.CheckError, re.escape(f"{key}: a dropped property on a")):  # FAULT
                    gc.validate(table, gc.DEBT, gc.WAIVERS)
        # why it matters: the evidence calls a dropped check "DIAGNOSTIC since 5.3 A1", which would be false of these
        table = {**gc.CHECKS, "R5.SPACED": dataclasses.replace(gc.CHECKS["R5.SPACED"], dropped="still a DIAGNOSTIC")}
        gc.validate(table, gc.DEBT, gc.WAIVERS)  # CONTROL: a DIAGNOSTIC check may name its dropped property

    def test_m18_no_title_is_the_start_of_another_of_its_grader(self):
        gc.validate(gc.CHECKS, gc.DEBT, gc.WAIVERS)  # CONTROL
        extra = gc._spec(gc.GRADED, "game", "CH1: the POKéDEX")  # the start of R5.CH1_REACHED's title
        with self.assertRaisesRegex(gc.CheckError, re.escape("title is the start of R5.CH1_REACHED's")):  # FAULT
            gc.validate({**gc.CHECKS, "R5.CH1_SHORT": extra}, gc.DEBT, gc.WAIVERS)
        # CONTROL: the same title in the OTHER grader is no clash (R5.SPACED and L5.SPACED already share one)
        self.assertEqual(gc.CHECKS["R5.SPACED"].title, gc.CHECKS["L5.SPACED"].title)
        gc.validate({**gc.CHECKS, "L5.CH1_SHORT": extra}, gc.DEBT, gc.WAIVERS)
        # why the rule exists: with such a pair, `as_check` cannot type the longer check's text (two titles start it)
        with mock.patch.dict(gc.CHECKS, {"R5.CH1_SHORT": extra}), self.assertRaises(gc.CheckError):
            gc.as_check((True, "CH1: the POKéDEX reached (by the game's flag) in 4 of 4"), "R5")
        self.assertEqual(gc.as_check((True, "CH1: the POKéDEX reached (by the game's flag) in 4 of 4"), "R5").id,
                         "R5.CH1_REACHED")

    def test_m42_the_new_place_n_is_the_draws_made_not_the_runs(self):
        """(Stage A2 carry-over 1 changed this row on purpose) n is the draws MADE, never the runs; draws made but none
        judged (chapter 1 left no seen tiles) is no longer a waived VACUOUS but a FAIL (`test_step53_a2` JudgedDrawTests)."""
        rows = sweep()
        for r in rows["CH2"]:
            r.update(place_draws=2, place_draws_judged=0)  # draws made, none judged: chapter 1 left no seen tiles
        check = check_of(grade_sweep(rows), "R5.CH2_NEW_PLACE")
        self.assertEqual((check.status, check.n), (gc.FAIL, 8))  # FAULT arm: 4 runs x 2 draws made, none judged
        check = check_of(grade_sweep(sweep()), "R5.CH2_NEW_PLACE")
        self.assertEqual((check.status, check.n), (gc.PASS, 8))  # CONTROL: 4 runs x 2 judged draws (not 4 runs)

    def test_m45_stop_n_is_the_runs_with_a_loss(self):
        check = check_of(grade_sweep(sweep()), "R5.STOP")
        self.assertEqual((check.status, check.n), (gc.PASS, 1))  # CONTROL: one phase-1 run lost, replayed
        rows = sweep()
        rows["CH1"][0].update(losses_game=0, losses_ai=0, losses_told=0, first_loss_f=None, last_loss_f=None)
        check = check_of(grade_sweep(rows), "R5.STOP")
        self.assertEqual((check.status, check.n), (gc.VACUOUS, 0))  # FAULT arm: no run with a loss, nothing to replay
        rows = sweep()
        rows["CH1"][1].update(losses_game=1, losses_ai=1, losses_told=1, first_loss_f=5000, last_loss_f=5000)
        rows["STOP"].append(row("STOP", 2, base="CH1", reason=rs.STOP_REASON, losses_game=1, losses_ai=1, losses_told=1,
                                first_loss_f=5000, frames=6000))
        check = check_of(grade_sweep(rows), "R5.STOP")
        self.assertEqual((check.status, check.n), (gc.PASS, 2))  # CONTROL: n counts them


def purity_run(exit_reason: str = "play: done: ch1_pokedex reached", pad: str = "presses=5 frames=100",
               foreign_presses: int = 0):
    """`live_step2.check_purity` on one synthetic launcher run, healthy unless an argument says otherwise. Only
    `exit_reason` (for a clean exit, the brain's own reason: `host/lifecycle.py`) and `pad` (the AI pad's own
    [AI-HANDS] outcome line) are AI-written; `foreign_presses` is the instrument's (the harness's)."""
    from ai_player.gates import live_step2
    from ai_player.gates import live_step5 as ls
    run = ls.Run(ls.ARMS[0])
    run.stdout = f"[AI-GATE] exit=0 verdict=PASS package={live_step2.REPO / 'ai_player'}"
    run.ai_log = f"[AI-HANDS] outcome=done {pad}"
    run.exit_code = 0
    counters = {key: 0 for key in live_step2.BREACH_COUNTERS}
    counters.update(ai_presses=10, real_frames=100, foreign_presses=foreign_presses)
    run.verdict = {"verdict": "CLEAN", "counters": counters,
                   "facts": {"exit_reason": exit_reason, "exit_code": 0, "package_root": str(live_step2.REPO)}}
    # (the 5.3 re-sourcing build, items 10 and 12) as `live_step5.grade_common` calls it: no wanted outcome (the outcome is
    # HONESTY against the game's proof, `check_outcome`, here a proof that holds); L5.PURITY_ENDED is re-made from the
    # harness's stop record
    live_step2.check_purity(run, None)
    ls.check_outcome(run, "ch1_pokedex", True, "the synthetic proof")
    return {c.id: c.status for c in run.checks}


#: the AI-written variations of a healthy purity run: each changes ONLY a field the AI wrote
AI_ONLY = {"the brain's reason names the wall clock": {"exit_reason": "wall-clock: the brain's own reason text"},
           "the brain's reason names another outcome": {"exit_reason": "play: stuck: no progress"},
           "the pad counts one press more": {"pad": "presses=6 frames=100"},
           "the pad counts one frame less": {"pad": "presses=5 frames=99"}}


def undeclared_ai_inputs() -> list[str]:
    """The purity checks whose STATUS an AI-only change moves while their declared inputs (`CHECKS`) omit `ai`."""
    healthy = purity_run()
    out = []
    for change in AI_ONLY.values():
        for key, status in purity_run(**change).items():
            if status != healthy[key] and gc.AI not in gc.CHECKS[key].inputs and key not in out:
                out.append(key)
    return out


class PurityInputTests(unittest.TestCase):
    """(A1 fix round, F3: the stage-A1 verifier's failure 3) L5.PURITY_ENDED read `exit_reason`, which for a clean exit is
    the BRAIN's text, so it declared `ai` and was B1 debt. (The 5.3 re-sourcing build, item 10) it is now REPORTED from the
    harness's own stop record, so the AI's text no longer moves it; and still no check whose status the AI's own text can
    move may declare its inputs without `ai` (L5.PURITY_OUTCOME, HONESTY, is moved by it and declares it)."""

    def test_the_healthy_run_passes_every_purity_check(self):
        healthy = purity_run()
        self.assertEqual(set(healthy.values()), {gc.PASS}, healthy)  # CONTROL: the fixture is healthy
        self.assertEqual(purity_run(foreign_presses=1)["L5.PURITY_BREACHES"], gc.FAIL)  # a harness-only change

    def test_the_ais_reason_no_longer_moves_the_ended_check(self):
        moved = purity_run(exit_reason="wall-clock: the brain's own reason text")
        self.assertEqual(moved["L5.PURITY_ENDED"], gc.PASS)  # the AI's text alone no longer moves it (exit code 0)
        self.assertEqual(moved["L5.PURITY_OUTCOME"], gc.FAIL)  # the AI's claim of a stop under the game's proof: a lie
        self.assertEqual((gc.CHECKS["L5.PURITY_ENDED"].kind, gc.CHECKS["L5.PURITY_ENDED"].inputs),
                         (gc.REPORTED, frozenset({"harness"})))
        self.assertNotIn("L5.PURITY_ENDED", gc.DEBT)  # its debt row left with the re-sourcing
        self.assertEqual(undeclared_ai_inputs(), [])  # CONTROL: every check the AI's text moves declares ai

    def test_a_check_declared_without_ai_that_the_ais_text_moves_is_found(self):
        import dataclasses
        game_only = dataclasses.replace(gc.CHECKS["L5.PURITY_OUTCOME"], kind=gc.REPORTED, inputs=frozenset({"game"}))
        with mock.patch.dict(gc.CHECKS, {"L5.PURITY_OUTCOME": game_only}):
            self.assertEqual(undeclared_ai_inputs(), ["L5.PURITY_OUTCOME"])  # FAULT: the outcome declared without ai

    def test_the_construction_rule_refuses_the_ai_input_without_its_debt(self):
        text = "ended by itself: exit_reason='play: done' exit_code=0 process=0 real_frames=100 (budget 2)"
        with self.assertRaisesRegex(gc.CheckError, re.escape("L5.PURITY_ENDED: a GRADED check that reads an AI input")):
            # FAULT: the stage-A1 declaration (GRADED, harness + ai) is refused now that its debt row has left the file
            gc.Check("L5.PURITY_ENDED", gc.GRADED, gc.PASS, None, None, {"harness", "ai"}, text)
        with self.assertRaises(gc.CheckError):  # FAULT: the table re-typed back to it refuses at validation
            import dataclasses
            gc.validate({**gc.CHECKS, "L5.PURITY_ENDED": dataclasses.replace(
                gc.CHECKS["L5.PURITY_ENDED"], kind=gc.GRADED, inputs=frozenset({"harness", "ai"}))}, gc.DEBT, gc.WAIVERS)
        built = gc.Check("L5.PURITY_ENDED", gc.REPORTED, gc.PASS, 1, None, {"harness"}, text)  # CONTROL: as re-typed
        self.assertEqual(built.inputs, frozenset({"harness"}))


class LiveTwinTests(unittest.TestCase):
    """(A1 fix round, ruling F4) L5.CATCH_ALL, L5.ASIDE_BACK and L5.GO_AFTER_PAGE are DIAGNOSTIC like their sweep twins
    (#6, #26, #27: no game form, so a debt row could never be paid): not in b1_debt.json, printed in the live evidence's
    no-longer-graded list, and a failure of one never fails an arm (a GRADED live failure does)."""

    TWINS = {"L5.CATCH_ALL": "R5.CH1_CATCH_ALL", "L5.ASIDE_BACK": "R5.ASIDE_BACK", "L5.GO_AFTER_PAGE": "R5.GO_AFTER_PAGE"}

    def test_each_twin_has_its_sweep_twins_kind_and_no_debt(self):
        for live, rate in self.TWINS.items():
            self.assertEqual((gc.CHECKS[live].kind, gc.CHECKS[rate].kind), (gc.DIAGNOSTIC, gc.DIAGNOSTIC), live)
            self.assertNotIn(live, gc.DEBT)
            self.assertTrue(gc.CHECKS[live].dropped, live)

    def test_the_live_evidence_lists_them_and_their_failure_does_not_fail_the_arm(self):
        from ai_player.gates import live_step5 as ls
        run = ls.Run(ls.ARMS[0])
        run.check(True, "BOUNDED: 1 real frames <= the pre-registered 2", "L5.BOUNDED")
        run.check(False, f"THE CATCH-ALL: 1 stretches standing still, NONE under the catch-all: [(5, 'x')]", "L5.CATCH_ALL")
        run.check(False, "EVERY GO GOAL WITH A MAP CAME AFTER THE PAGE THAT TOLD IT: off [x]", "L5.GO_AFTER_PAGE")
        run.check(False, "A STORY GOAL PUT ASIDE COMES BACK: over it [x]", "L5.ASIDE_BACK")
        self.assertTrue(run.passed)  # CONTROL: three DIAGNOSTIC failures, the arm passes
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(ls, "EVIDENCE_DIR", Path(folder)), \
                mock.patch.object(ls, "keep_earlier", lambda path: None):
            text = ls.write_evidence(run, "code", "test").read_text(encoding="utf-8")
        for live in self.TWINS:
            self.assertIn(f"NO LONGER GRADED {live} (FAIL, DIAGNOSTIC since 5.3 A1): ", text)
            self.assertNotIn(f"B1 DEBT {live} ", text)
        self.assertIn("AI PLAYER BUILD STEP 5.3", text.splitlines()[0])
        run.check(False, "NEVER WITHOUT A GOAL: 0 goals chosen", "L5.HAS_GOAL", 0)
        run.check(False, "THE GAME (the bag): POKé BALLS {}", "L5.BALLS")
        self.assertFalse(run.passed)  # FAULT: a GRADED live failure still fails the arm


class EvidenceWordingTests(unittest.TestCase):
    """(A1 fix round, F5b-d) the B1 DEBT lines print each plan once ("A2: A2:" before), the sweep's header names step 5.3,
    and #44's game half is exercised INSIDE `grade_run` from a chapter-1 seen-tiles file in `PlaceRecorder`'s format."""

    def test_a_b1_debt_line_prints_its_plan_once(self):
        # (the re-sourcing fix round) the real debt is EMPTY: the real sweep prints no B1 DEBT line, and the printing rule
        # is held on a synthetic debt row (a GRADED check reading the AI, listed with its plan)
        self.assertEqual([line for line in gc.evidence_lines(grade_sweep(sweep())) if line.startswith("B1 DEBT ")], [])
        debt = {"R5.ZZ_SYNTHETIC": {"ai_input": "its goal windows", "plan": "A2 decided: re-source to the game's push"}}
        made = gc.Check("R5.ZZ_SYNTHETIC", gc.GRADED, gc.PASS, 1, 1, {"game", "ai"}, "t", debt=debt)
        with mock.patch.dict(gc.CHECKS, {"R5.ZZ_SYNTHETIC": gc._spec(gc.GRADED, "game+ai", "ZZ SYNTHETIC")}):
            lines = [line for line in gc.evidence_lines(grade_sweep(sweep()) + [made], debt=debt)
                     if line.startswith("B1 DEBT ")]
        self.assertEqual(len(lines), 1)
        for line in lines:
            check_id = line.split()[2]
            self.assertNotIn("A2: A2:", line)  # FAULT shape (the stage-A1 smoke's 13 lines)
            self.assertTrue(line.endswith(f"; plan: {debt[check_id]['plan']}"), line)  # CONTROL: the plan, verbatim

    def test_the_sweeps_header_names_step_5_3(self):
        driver = TypedSweepTests("test_the_sweeps_verdict_is_the_typed_rule")
        try:
            code, evidence = driver.drive_main({"CH1": sweep()["CH1"]})
        finally:
            driver.doCleanups()  # its temporary evidence folder
        first = evidence.splitlines()[0]
        # (the A2 fix round, F5) the CURRENT stage: the A2 smoke's evidence still read "stage A1"
        self.assertTrue(first.startswith("AI PLAYER BUILD STEP 5.3 (TYPED CHECKS, stage A2) - THE SEED SWEEP"), first)
        self.assertNotIn("BUILD STEP 5.2", first)
        self.assertNotIn("stage A1", first)

    def test_a_dropped_check_may_print_pass_on_nothing_and_a_counted_one_may_not(self):
        """`verdicts()`'s docstring, as corrected (F5b)."""
        rows = sweep()
        for plan_rows in rows.values():
            for r in plan_rows:
                r["asides"] = []
        results = grade_sweep(rows)
        aside = check_of(results, "R5.ASIDE_BACK")
        self.assertEqual((aside.kind, aside.status, aside.n, aside.floor), (gc.DIAGNOSTIC, gc.PASS, 0, None))
        self.assertTrue(all(c.status != gc.PASS for c in results if c.kind in gc.COUNTED and c.floor is not None
                            and (c.n or 0) < c.floor))

    def chapter2(self, seen_in_chapter_1: set, draw: str) -> object:
        """One chapter-2 run graded by `grade_run` from its chapter 1's seen tiles, written as `play_harness.play` writes
        `PlaceRecorder.seen`; its numbers dropped into the healthy sweep's CH2 rows; the R5.CH2_NEW_PLACE check."""
        from ai_player.gates import play_harness as ph
        places = ph.PlaceRecorder(None, seen=seen_in_chapter_1)
        records = [{"decision": "goal", "action": "explore", "frame": 100, "reason": f"a new place, {draw}: a person"}]
        with tempfile.TemporaryDirectory() as folder:
            seen_file = Path(folder) / ph.SEEN_FILE
            seen_file.write_text(json.dumps(sorted(":".join(str(v) for v in tile) for tile in places.seen)),
                                 encoding="utf-8")  # play_harness.play's own line
            self.assertEqual(ph.read_seen(str(seen_file)), set(seen_in_chapter_1))
            graded = rs.grade_run("CH2", 1, "Story", "TREECKO", {}, records, 1.0, seen_in=str(seen_file))
        rows = sweep()
        for r in rows["CH2"]:
            r.update(place_draws=0, place_draws_judged=0, old_places=[])
        rows["CH2"][0].update({key: graded[key] for key in ("place_draws", "place_draws_judged", "old_places")})
        return check_of(grade_sweep(rows), "R5.CH2_NEW_PLACE")

    def test_chapter2_new_place_is_judged_by_chapter_1s_seen_maps(self):
        littleroot = {(0, 9, 5, 5), (0, 9, 6, 5)}  # MapRSE LITTLEROOT_TOWN = (0, 9)
        oldale = {(0, 10, 5, 5)}  # MapRSE OLDALE_TOWN = (0, 10)
        self.assertEqual(rs.map_keys()["LITTLEROOT_TOWN"], "0:9")
        check = self.chapter2(littleroot | oldale, "LITTLEROOT_TOWN")
        self.assertEqual((check.status, check.n), (gc.FAIL, 1))  # FAULT: a place chapter 1 stood on, called new
        check = self.chapter2(oldale, "LITTLEROOT_TOWN")
        self.assertEqual((check.status, check.n), (gc.PASS, 1))  # CONTROL: chapter 1 never stood there


if __name__ == "__main__":
    unittest.main()
