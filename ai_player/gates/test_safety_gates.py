"""FAULT TESTS of build step 5.2's SAFETY GATES (G1-G7). Test side.

    py -3.12 ai_player/gates/test_safety_gates.py        (exit 0 = every test passed; run by run_units.py)

Each gate is proven BOTH WAYS (CLAUDE.md session rule 6): it FIRES on the thing it guards, and it stays SILENT on a mere
mention of it (a comment, a docstring, a note, a document the code under test does not run).
  FrozenTreeTests     G1 `provenance.FrozenTree`: a scratch COPY of the package changed mid-sweep fails the verdict "the
                      tree changed mid-run" (an edit, an added file, an edit UNDONE before the end); docs, evidence, the
                      ledger and caches written mid-run do not; the BACKSTOP turns a driver that never seals its verdict
                      into exit 1 with its evidence amended.
  WiringTests         G1, G2, G5 wired: each graded driver CALLS its guards in the function that must (rate_step5's
                      run_one checks before AND after its run); a mention in a comment or docstring is no call.
  LedgerTests         G2 `ledger.py`: a graded run refuses no registration, changed numbers, a played range; a development
                      run may not spend a registered range; a replay only on played seeds, and says so; the real driver
                      has no default `--first-seed` or `--purpose` and refuses an unregistered graded range without
                      writing the ledger; a note that MENTIONS seeds overlaps nothing.
  CallCensusTests     G3 `call_census.py`: a new hook is listed with its one real site (not its mentions); a BODY-only, an
                      ARGUMENT-only or a COMMENT-anchored mutant does not cover it, a call-deleting or call-guarding one
                      does; an uncalled hook FAILS unless waived with a reason; on the real code G46 deletes
                      `_count_losses`' call and G36 guards `battle_rest`'s.
  FairnessTests       G4 `check_fairness.py`: an errand keyed on a mark, a flag read outside the door, a coordinate read,
                      a knowledge file read outside a loader, a hidden species fact, an unclassified knowledge key and a
                      stale door all FAIL; the same words in docstrings, comments, f-strings, dict displays and the
                      object's own fields do not; the real package PASSES.
  DiskBudgetTests     G5 `disk_budget.py`: under 30 GB free a sweep is refused (and the real rate_step5 plays and writes
                      nothing); a sweep's run folders are deleted but the failing and the newest; a profile's run folders
                      are pruned but this run's, the failing, the cited (by WHOLE name) and the newest.
  EvidenceReaderTests G6: one reader for every checker, on a file whose command is a multi-line `-c` script; an indented or
                      mid-line "code:" (a mention inside the script) is never read; the real G and M6 files.
  LessonsTests        G7 `check_lessons.py`: a lesson naming a gate, test or mutant that does not exist FAILS (and a typo);
                      the same names in a title or a Needs line do not; the real LESSONS.md PASSES.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import call_census, check_fairness, check_lessons, disk_budget  # noqa: E402
from ai_player.gates import ledger as seed_ledger  # noqa: E402
from ai_player.gates import prune_evidence  # noqa: E402
from ai_player.gates.provenance import FrozenTree, MID_RUN, code_digest, file_digest, keep_earlier  # noqa: E402

GATES = REPO / "ai_player" / "gates"
DIGEST = "d3d34871df0ac077"


def scratch_copy(root: Path) -> Path:
    """A scratch COPY of the package (no evidence, fixtures or caches) under `root`, the way a sweep imports it."""
    shutil.copytree(REPO / "ai_player", root / "ai_player",
                    ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures", "*.ss1"))
    return root


class Scratch(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ai_test_safety_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


# ---------------------------------------------------------------------- G1
def mini_sweep(tree: FrozenTree, runs: int, during=None) -> tuple[str, str, int]:
    """A sweep's shape (rate_step5): a check before and after each run, `during(i)` run between; the sealed verdict and
    how many runs were played."""
    played = 0
    for i in range(runs):
        if tree.moved or not tree.check(f"before run {i}"):
            continue
        played += 1
        if during is not None:
            during(i)
        tree.check(f"after run {i}")
    verdict, line = tree.seal("PASS")
    return verdict, line, played


def called_names(source: str) -> set[str]:
    """The names a module CALLS (`f(...)` or `x.f(...)`), by AST: a comment or a docstring calls nothing."""
    out = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            f = node.func
            out.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return out


class FrozenTreeTests(Scratch):
    def setUp(self) -> None:
        super().setUp()
        scratch_copy(self.root)
        self.mode = self.root / "ai_player" / "mode.py"

    def tree(self) -> FrozenTree:
        return FrozenTree(self.root, scope=("ai_player",))

    def test_control_an_untouched_tree_passes(self) -> None:
        verdict, line, played = mini_sweep(self.tree(), 4)
        self.assertEqual((verdict, played), ("PASS", 4), line)
        self.assertIn("FROZEN TREE: PASS", line)

    def test_an_edit_mid_sweep_fails_the_verdict_and_stops_the_runs(self) -> None:
        def edit(i: int) -> None:
            if i == 1:
                self.mode.write_text(self.mode.read_text(encoding="utf-8") + "\nX = 1\n", encoding="utf-8")
        verdict, line, played = mini_sweep(self.tree(), 5, edit)
        self.assertEqual(verdict, "FAIL")
        self.assertIn(MID_RUN, line)
        self.assertIn("ai_player/mode.py", line)
        self.assertIn("after run 1", line)
        self.assertEqual(played, 2, "no run is played on a moved tree")

    def test_an_added_module_fails(self) -> None:
        verdict, line, _ = mini_sweep(self.tree(), 3, lambda i: i == 0 and (self.root / "ai_player" / "brain" /
                                                                                "new_hook.py").write_text("X = 1\n"))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("added", line)

    def test_an_edit_undone_before_the_end_still_fails(self) -> None:
        original = self.mode.read_bytes()

        def edit_and_undo(i: int) -> None:
            if i == 0:
                self.mode.write_bytes(original + b"\n# edited\n")
                time.sleep(0.05)
                self.mode.write_bytes(original)  # the runs between played the edited file
        tree = self.tree()
        verdict, line, _ = mini_sweep(tree, 3, edit_and_undo)
        self.assertEqual(verdict, "FAIL", line)
        self.assertIn("rewritten with the start's bytes", line)

    def test_mentions_do_not_fire_docs_evidence_ledger_and_caches(self) -> None:
        def write_around(i: int) -> None:
            if i == 0:
                (self.root / "ai_player" / "README.md").write_text("the tree changed mid-run? no: a doc\n", encoding="utf-8")
                (self.root / "ai_player" / "evidence").mkdir(exist_ok=True)
                (self.root / "ai_player" / "evidence" / "x.txt").write_text("VERDICT: PASS\n", encoding="utf-8")
                (self.root / "ai_player" / "gates" / "ledger.json").write_text("{}\n", encoding="utf-8")
                cache = self.root / "ai_player" / "brain" / "__pycache__"
                cache.mkdir(exist_ok=True)
                (cache / "goals.cpython-312.pyc").write_bytes(b"cache")
        verdict, line, played = mini_sweep(self.tree(), 3, write_around)
        self.assertEqual((verdict, played), ("PASS", 3), line)

    def _driver(self, edit: bool) -> tuple[int, str, str]:
        script = self.root / "driver.py"
        script.write_text(
            "import sys\nfrom pathlib import Path\nroot = Path(sys.argv[1])\nsys.path.insert(0, str(root))\n"
            "from ai_player.gates import provenance as p\nprint('code:', p.provenance())\n"
            "if sys.argv[2] == 'edit':\n    t = root / 'ai_player' / 'mode.py'\n"
            "    t.write_text(t.read_text(encoding='utf-8') + '\\n# an edit mid-run\\n', encoding='utf-8')\n"
            "p.EVIDENCE.mkdir(parents=True, exist_ok=True)\nout = p.EVIDENCE / '2026-10-15-plant-X.txt'\n"
            "p.keep_earlier(out)\nout.write_text('PLANT\\nVERDICT: PASS\\n', encoding='utf-8')\nsys.exit(0)\n",
            encoding="utf-8")
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        done = subprocess.run([sys.executable, str(script), str(self.root), "edit" if edit else "none"], cwd=str(self.root),
                              capture_output=True, timeout=300, env=env)
        out = self.root / "ai_player" / "evidence" / "2026-10-15-plant-X.txt"
        return done.returncode, out.read_text(encoding="utf-8") if out.is_file() else "", done.stdout.decode("utf-8", "replace")

    def test_the_backstop_fails_a_driver_that_never_seals(self) -> None:
        code, text, stdout = self._driver(edit=True)
        self.assertEqual(code, 1, stdout)
        self.assertIn("VERDICT: PASS", text)
        self.assertIn(f"FROZEN TREE: FAIL - {MID_RUN}", text)
        self.assertIn("ai_player/mode.py", text)

    def test_the_backstop_control_an_untouched_driver_is_left_alone(self) -> None:
        code, text, stdout = self._driver(edit=False)
        self.assertEqual(code, 0, stdout)
        self.assertNotIn("FROZEN TREE", text)

    def test_a_mention_is_no_call(self) -> None:
        mention = '"""It calls watch(REPO), tree.check("x") and tree.seal(v)."""\n# tree.seal(verdict)\nx = 1\n'
        self.assertFalse({"watch", "check", "seal"} & called_names(mention))
        self.assertEqual(calls_in(mention + "def main():\n    # tree.check('x')\n    return 1\n", "main"), [])
        dead = "def main(tree):\n    if False and tree.check('x'):\n        return 0\n    if False:\n        tree.seal('v')\n"
        self.assertEqual(calls_in(dead, "main"), [], "a call in dead code is no call")


def calls_in(source: str, qualname: str) -> list[tuple[str, int]]:
    """(name, line) of every LIVE call inside one function and the functions nested in it, by AST, in line order: a call
    in dead code (`if False and check(...)`, the shape of a deleted guard) is no call (`call_census.live_calls`)."""
    from ai_player.gates.call_census import functions, live_calls

    names = [q for q in functions(source) if q == qualname or q.startswith(qualname + ".")]
    return sorted(((name, line) for q in names for name, line, _ in live_calls(source, q)), key=lambda c: c[1])


class WiringTests(unittest.TestCase):
    """(G1, G2, G5) Each graded driver CALLS its guards, in the function that must (the census's own lesson: a guard whose
    call is deleted passes every test of the guard). A mention is no call (`FrozenTreeTests.test_a_mention_is_no_call`)."""

    WANT = {
        ("rate_step5.py", "main"): {"watch", "seal", "begin", "finish", "preflight", "tidy", "SweepFolders"},
        ("live_step5.py", "main"): {"watch", "check", "seal", "prune_runs"},
        ("revert_step5.py", "main"): {"watch", "check", "seal"},
        ("run_units.py", "main"): {"watch", "check", "seal"},
        ("revert_safety_gates.py", "main"): {"watch", "check", "seal"},
        # (2026-11-05, the live_chain build's critic CH-01) the New Game chain held-out: the orchestrator begins and
        # finishes its ledger entry, refuses before it, watches and seals the tree; the child grades every leg's purity
        # and freshness, measures and deletes its world file, and applies the custody and continuation rules
        # (`test_live_chain.WiringTests` holds the full list, with a mutant per deleted call)
        ("live_chain.py", "run_batch"): {"watch", "check", "seal", "begin", "finish", "run_refusal", "schedule"},
        ("live_chain.py", "run_chain"): {"check_purity", "check_after_is_this_run", "finish_leg", "custody_problems",
                                         "continue_after"},
    }

    def test_each_driver_calls_its_guards_where_they_belong(self) -> None:
        for (name, function), want in self.WANT.items():
            with self.subTest(driver=name):
                called = {n for n, _ in calls_in((GATES / name).read_text(encoding="utf-8"), function)}
                self.assertTrue(want <= called, sorted(want - called))

    def test_a_sweep_checks_before_and_after_every_run(self) -> None:
        calls = calls_in((GATES / "rate_step5.py").read_text(encoding="utf-8"), "run_one")
        checks = [line for name, line in calls if name == "check"]
        runs = [line for name, line in calls if name == "run"]
        self.assertTrue(checks and runs and min(checks) < min(runs) < max(checks), calls)
        folder = [line for name, line in calls if name == "new"]
        self.assertTrue(folder, "the run's folder comes from the sweep's one root (SweepFolders.new)")


# ---------------------------------------------------------------------- G2
class LedgerTests(Scratch):
    def setUp(self) -> None:
        super().setUp()
        self.path = self.root / "ledger.json"
        self.path.write_text(json.dumps({"what": "test", "entries": [
            {"id": 1, "family": "story", "driver": "rate_step5", "purpose": "development", "first": 1, "last": 99,
             "status": "done", "note": "development by convention; the graded runs will use seeds 901-920 later"},
            {"id": 2, "family": "story", "driver": "rate_step5", "purpose": "graded", "first": 801, "last": 820,
             "status": "done", "bounds_sha256": None, "tree": DIGEST, "verdict": "PASS"}]}), encoding="utf-8")

    def begin(self, purpose: str, first: int, last: int, sha: str = "a" * 64):
        return seed_ledger.begin("story", "rate_step5", purpose, first, last, sha, "t" * 16, path=self.path)

    def test_a_graded_run_never_registered_is_refused(self) -> None:
        with self.assertRaises(seed_ledger.Refused) as caught:
            self.begin("graded", 901, 920)
        self.assertIn("never REGISTERED", str(caught.exception))

    def test_a_registered_range_runs_once_with_its_own_numbers(self) -> None:
        seed_ledger.register("story", "rate_step5", 901, 920, "a" * 64, path=self.path)
        entry, lines = self.begin("graded", 901, 920)
        self.assertEqual(entry["status"], "started")
        self.assertIn("GRADED, HELD-OUT seeds 901-920", lines[0])
        seed_ledger.finish(entry["id"], "PASS", "x.txt", path=self.path)
        with self.assertRaises(seed_ledger.Refused):
            self.begin("graded", 901, 920)  # a held-out seed is played once
        with self.assertRaises(seed_ledger.Refused):
            seed_ledger.register("story", "rate_step5", 915, 930, "a" * 64, path=self.path)

    def test_a_bound_changed_after_registration_is_refused(self) -> None:
        seed_ledger.register("story", "rate_step5", 901, 920, "a" * 64, path=self.path)
        with self.assertRaises(seed_ledger.Refused) as caught:
            self.begin("graded", 901, 920, sha="b" * 64)
        self.assertIn("changed after registration", str(caught.exception))
        # re-registered BEFORE any run: allowed, the old hash kept in its history
        entry = seed_ledger.register("story", "rate_step5", 901, 920, "b" * 64, path=self.path)
        self.assertEqual(entry["history"][0]["bounds_sha256"], "a" * 64)
        self.assertEqual(self.begin("graded", 901, 920, sha="b" * 64)[0]["status"], "started")

    def test_graded_runs_refuse_development_and_graded_seeds(self) -> None:
        for first, last in ((5, 14), (95, 104), (815, 825)):
            with self.subTest(seeds=(first, last)), self.assertRaises(seed_ledger.Refused):
                seed_ledger.register("story", "rate_step5", first, last, "a" * 64, path=self.path)

    def test_a_development_run_may_not_spend_a_registered_range(self) -> None:
        seed_ledger.register("story", "rate_step5", 901, 920, "a" * 64, path=self.path)
        with self.assertRaises(seed_ledger.Refused):
            self.begin("development", 910, 912)
        entry, lines = self.begin("development", 9001, 9003)
        self.assertIn("NOT a graded result", lines[0])
        self.assertEqual(seed_ledger.label("development"), "DEVELOPMENT, not graded")

    def test_a_replay_only_on_played_seeds_and_said_so(self) -> None:
        entry, lines = self.begin("replay", 801, 810)
        self.assertIn("a REPLAY, never a second measurement", lines[0])
        self.assertEqual(entry["replays"], [2])
        with self.assertRaises(seed_ledger.Refused):
            self.begin("replay", 950, 951)

    def test_a_note_that_mentions_seeds_overlaps_nothing(self) -> None:
        # entry 1's NOTE names 901-920: only its range (1-99) counts
        self.assertEqual(seed_ledger.register("story", "rate_step5", 901, 920, "a" * 64, path=self.path)["status"],
                         "registered")

    def test_the_real_ledger_is_well_formed_and_901_920_unplayed(self) -> None:
        """(Build step 5.2, part 1) 901-920 were the step's held-out range: no entry before its graded sweep. (Part 2)
        build step 5.2's graded sweep registered and played them: no OTHER entry names any of them (never developed on,
        never graded twice)."""
        data = seed_ledger.load()
        self.assertEqual(seed_ledger.check(data), [])
        named = [e for e in data["entries"] if e["first"] <= 920 and 901 <= e["last"]]
        self.assertTrue(all(e["purpose"] == "graded" and (e["first"], e["last"]) == (901, 920) for e in named), named)
        self.assertLessEqual(len(named), 1, named)

    def test_the_real_driver_has_no_default_purpose_or_first_seed(self) -> None:
        for args, missing in ((["--purpose", "graded"], "--first-seed"), (["--first-seed", "901"], "--purpose")):
            with self.subTest(missing=missing):
                done = subprocess.run([sys.executable, str(GATES / "rate_step5.py"), *args], capture_output=True,
                                      timeout=300, env={**os.environ, "PYTHONUTF8": "1"})
                self.assertEqual(done.returncode, 2)
                self.assertIn(missing, done.stderr.decode("utf-8", "replace"))

    def test_the_real_driver_refuses_an_unregistered_graded_range_and_writes_nothing(self) -> None:
        from ai_player.gates import rate_step5

        before = seed_ledger.LEDGER.read_bytes()
        argv = ["rate_step5.py", "--purpose", "graded", "--first-seed", "901", "--seeds", "20", "--plans", "CH1"]
        out = io.StringIO()

        def no_run(*args, **kwargs):  # the test's net: a broken refusal FAILS here, it never starts an emulator
            raise RuntimeError("an unregistered graded range played a run")
        with mock.patch.object(sys, "argv", argv), mock.patch.object(disk_budget, "preflight", lambda: (True, "ok")), \
                mock.patch.object(rate_step5, "run_chain", no_run), mock.patch.object(rate_step5, "run_one", no_run), \
                contextlib.redirect_stdout(out):
            code = rate_step5.main()
        self.assertEqual(code, 2, out.getvalue())
        self.assertIn("LEDGER: REFUSED", out.getvalue())
        self.assertEqual(seed_ledger.LEDGER.read_bytes(), before)


# ---------------------------------------------------------------------- G3
BASE = 'def caller(look):\n    return look\n\n\ndef main():\n    return caller(1)\n'
NOW = ('def hook(look):\n    return look + 1\n\n\n'
       'def caller(look):\n    """Calls hook() on the look (a mention)."""\n    # hook(look) is mentioned here\n'
       '    return hook(look)\n\n\ndef main():\n    return caller(1)\n')


class CallCensusTests(unittest.TestCase):
    def run_census(self, now: str = NOW, mutants: dict | None = None, waivers: list | None = None):
        files = {"brain/plant.py": now}
        return call_census.census(files, lambda rel: BASE, ["brain/plant.py"], mutants or {}, waivers or [])

    def finding(self, findings, name: str):
        return next(f for f in findings if f.callee == f"brain/plant.py:{name}")

    def test_a_new_hook_is_listed_with_its_one_real_site_not_its_mentions(self) -> None:
        hook = self.finding(self.run_census(), "hook")
        self.assertEqual(hook.why, "added")
        self.assertEqual([site for site, _ in hook.sites], ["brain/plant.py:8 in caller [call]"])  # the return, not 6-7
        self.assertTrue(hook.missing)

    def test_mutants_that_do_not_delete_the_call_cover_nothing(self) -> None:
        for name, edit in (("BODY", ("    return look + 1\n", "    return look\n")),
                           ("ARGUMENT", ("    return hook(look)\n", "    return hook(look + 0)\n")),
                           ("COMMENT", ("    # hook(look) is mentioned here\n", "    # gone\n"))):
            with self.subTest(mutant=name):
                hook = self.finding(self.run_census(mutants={name: [("brain/plant.py", *edit)]}), "hook")
                self.assertTrue(hook.missing, hook.sites)

    def test_a_mutant_that_deletes_or_guards_the_call_covers_it(self) -> None:
        for name, new, how in (("DELETE", "    return look\n", "deletes the call"),
                               ("DEAD", "    return hook(look) if False else look\n", "deletes the call"),
                               ("GUARD", "    return hook(look) if look is None else look\n", "guards the call off")):
            with self.subTest(mutant=name):
                hook = self.finding(self.run_census(mutants={name: [("brain/plant.py", "    return hook(look)\n", new)]}),
                                    "hook")
                self.assertFalse(hook.missing, hook.sites)
                self.assertIn(how, hook.sites[0][1])

    def test_a_mutant_covers_only_the_site_its_anchor_holds(self) -> None:
        now = NOW.replace("    return hook(look)\n", "    first = hook(look)\n    return hook(first)\n")
        mutants = {"SECOND": [("brain/plant.py", "    return hook(first)\n", "    return first\n")]}
        hook = self.finding(self.run_census(now, mutants), "hook")
        self.assertEqual([status.split(" ")[0] for _, status in hook.sites], ["MISSING:", "COVERED"], hook.sites)

    def test_an_uncalled_hook_fails_unless_waived_with_a_reason(self) -> None:
        now = NOW + "\n\ndef unused_hook():\n    return 2\n"
        delete = {"DELETE": [("brain/plant.py", "    return hook(look)\n", "    return look\n")]}
        unused = self.finding(self.run_census(now, delete), "unused_hook")
        self.assertTrue(unused.missing)
        self.assertIn("UNCALLED", unused.sites[0][1])
        short = [{"callee": "brain/plant.py:unused_hook", "caller": "*", "reason": "unused"}]
        self.assertTrue(self.finding(self.run_census(now, delete, short), "unused_hook").missing)
        reason = [{"callee": "brain/plant.py:unused_hook", "caller": "*",
                   "reason": "called by the framework's listener, at no site of ours"}]
        self.assertFalse(self.finding(self.run_census(now, delete, reason), "unused_hook").missing)

    def test_a_site_in_a_function_nested_inside_an_if_can_be_covered(self) -> None:
        """(Build step 5.2, found by the census of 5.2's own code: `GoalRunner._pursue.done`, defined inside an `if` of
        `_pursue`, was named as a site's caller and missing from `functions`, so no mutant could ever cover its sites.)"""
        base = "def hook(x):\n    return x\n\n\ndef outer(flag):\n    if flag:\n        def inner(y):\n            return y\n" \
               "        return inner(1)\n    return 0\n"
        now = base.replace("            return y\n", "            return hook(y)\n")
        self.assertIn("outer.inner", call_census.functions(now))  # FAULT half: the walk stopped at the `if`
        found = call_census.census({"brain/plant.py": now}, lambda rel: base, ["brain/plant.py"], {}, [])
        added = [f for f in found if f.callee == "brain/plant.py:hook" and "outer.inner" in f.why]
        self.assertEqual(len(added), 1, [(f.callee, f.why) for f in found])  # FAULT half: the new call not even listed
        self.assertTrue(added[0].missing)
        delete = {"DELETE": [("brain/plant.py", "            return hook(y)\n", "            return y\n")]}
        found = call_census.census({"brain/plant.py": now}, lambda rel: base, ["brain/plant.py"], delete, [])
        added = next(f for f in found if f.callee == "brain/plant.py:hook" and "outer.inner" in f.why)
        self.assertEqual([status.split(" ")[0] for _, status in added.sites], ["COVERED"], added.sites)

    def test_a_comment_or_docstring_change_is_no_change(self) -> None:
        base = 'def f(x):\n    """Old words."""\n    return x\n'
        now = 'def f(x):\n    """New words."""\n    # a comment\n    return x\n'
        self.assertEqual(call_census.census({"a.py": now}, lambda rel: base, ["a.py"], {}, []), [])

    def test_on_the_real_code_g46_deletes_and_g36_guards_their_calls(self) -> None:
        mutants = call_census.load_mutants()
        for rel, name, caller, want, how in (("mode.py", "_count_losses", "HandsBrain._play", "G46", "deletes the call"),
                                              ("brain/navigator.py", "battle_rest", None, "G36", "guards the call off")):
            with self.subTest(mutant=want):
                text = (REPO / "ai_player" / rel).read_text(encoding="utf-8")
                sites = [s for s in call_census.sites_of(name, rel, text) if s.kind == "call"
                         and (caller is None or s.caller == caller)]
                self.assertTrue(sites)
                found = [call_census.covering(s, name, text, mutants) for s in sites]
                self.assertTrue(any(f and f[0] == f"revert_step5:{want}" and f[1].startswith(how) for f in found), found)


# ---------------------------------------------------------------------- G4
class FairnessTests(Scratch):
    @classmethod
    def setUpClass(cls) -> None:
        knowledge = REPO / "ai_player" / "knowledge"
        data = json.loads((knowledge / "milestones.json").read_text(encoding="utf-8"))
        cls.flag_names = {name for m in data["milestones"] for name in (*m["done"]["flags"], *m["done"]["variables"])}
        cls.dev = check_fairness.developer_keys(knowledge=knowledge)
        cls.hidden = check_fairness.hidden_keys(knowledge=knowledge)
        cls.names = {p.name for p in knowledge.glob("*.json")}

    def scan(self, source: str, rel: str = "brain/errand_plant.py") -> list[str]:
        return check_fairness.scan_file(rel, source, self.flag_names, self.dev, self.hidden, self.names)

    def test_an_errand_keyed_on_a_mark_is_refused(self) -> None:
        found = self.scan("from ai_player.brain.goals import marks_of\n\n\ndef shop_errand(look):\n"
                          "    marks = marks_of(look)\n    return bool(marks) and marks.get('ADVENTURE_STARTED') == 1\n")
        self.assertTrue(any("marks_of" in f for f in found), found)
        self.assertTrue(any("'ADVENTURE_STARTED'" in f for f in found), found)

    def test_a_flag_read_outside_the_door_is_refused(self) -> None:
        for source in ("def heal_errand(look):\n    return dict(look.progress.marks).get('x')\n",
                       "def go(look):\n    return getattr(look.progress, 'flags')\n",
                       "def go(look):\n    return 'FLAG_RESCUED_BIRCH'\n"):
            with self.subTest(source=source):
                self.assertTrue([f for f in self.scan(source) if f.startswith("A ")], source)

    def test_a_coordinate_and_a_decomp_read_are_refused(self) -> None:
        found = self.scan("def clock(data):\n    return data['looks']['clock']['measured'][0]['x']\n")
        self.assertEqual(sorted(f.split("key ")[1].split(" ")[0] for f in found if f.startswith("B2")), ["'measured'", "'x'"])
        loader = self.scan("def load(info):\n    return info.get('decomp')\n", rel="knowledge/story.py")
        self.assertTrue([f for f in loader if "'decomp'" in f], loader)

    def test_a_knowledge_file_outside_a_loader_and_a_hidden_fact_are_refused(self) -> None:
        self.assertTrue([f for f in self.scan("PATH = 'knowledge/milestones.json'\n") if f.startswith("B1")])
        self.assertTrue([f for f in self.scan("def f(n):\n    return species_fact(n).catch_rate\n") if f.startswith("B3")])
        self.assertTrue([f for f in self.scan("def f(n):\n    fact = species_fact(n)\n    return fact.attack\n")
                         if f.startswith("B3")])
        self.assertTrue([f for f in self.scan("def f(n):\n    return info['catch_rate']\n", rel="knowledge/story.py")
                         if f.startswith("B2")])

    def test_mentions_never_fire(self) -> None:
        source = ('"""This errand never reads `look.progress.marks`, marks_of(), FLAG_ADVENTURE_STARTED, the '
                  'milestones.json measured x, or species_fact(n).catch_rate."""\n'
                  "# look.progress.flags, data['measured']['x'], 'ADVENTURE_STARTED'\n"
                  "__all__ = ['TRAINER_OUT_OF_SCOPE']\n'knowledge/milestones.json'\n\n\n"
                  "def documented():\n    \"\"\"FLAG_RESCUED_BIRCH\"\"\"\n    return 1\n\n\n"
                  "class Errand:\n    def __init__(self, marks):\n        self.marks = marks\n        self.flags = set()\n\n"
                  "    def go(self, x, v):\n        shown = {'x': 1, 'measured': 2}\n"
                  "        return self.marks, self.flags, f'measured {x} FLAG_ {v}', shown\n")
        self.assertEqual(self.scan(source), [])

    def test_the_play_time_is_read_only_through_its_doors(self) -> None:
        """(R1 + R2, build spec D18, RULE C) The game's play time is no screen fact: only the save code reads it. FAULT: a
        planted `.play_time` read (and its `getattr` form) in the goal manager fails, and so does a door no read goes
        through (stale); CONTROL: a docstring or comment mention, `self.play_time`, the keyword that DROPS it (`seen_now`'s
        `replace(progress, play_time=None)`) and a read inside a door pass, and the real package passes. (R1 + R2
        follow-up, spec D3) FAULT: the review's F2 (subscript), F3 (`asdict`), F7 (`.get`), F8 (match class keyword), F9
        (`astuple`), F11 (match mapping), a named constant, `attrgetter` and F12 (a positional class pattern, refused as
        RULE C and A even inside a door); CONTROL: a dict display's key, a docstring, an f-string's text, and inside a door
        the subscript and `case Progress(play_time=t)`. (U2 spec 2026-10-30 D15, RV-5) FAULT: `int` rebound by an
        assignment, a parameter, `case ... as int`, `except ... as int` or `import builtins` (here or in another module of
        the package), and `case int(a, b)` / `case int(n, real=1)`, keep `case int(...)` refused (mutants S46g, S46h);
        CONTROL: `case int(n)`, `case str(s)` and `case tuple(t)` pass, and so does the real package."""
        for source in ("def errand(look):\n    return look.progress.play_time[0] > 2\n",
                       "def errand(look):\n    return getattr(look.progress, 'play_time')\n"):
            with self.subTest(source=source):
                found = self.scan(source, rel="brain/goals.py")
                self.assertTrue([f for f in found if f.startswith("C ")], found)
        # (R1 + R2 follow-up, spec D3: the review's N-2) FAULT: the other forms that read it, each in the goal manager
        plants = {
            "F2 a subscript": "def errand(memory):\n    return memory.last_save['play_time']\n",
            "F3 asdict": "from dataclasses import asdict\n\n\ndef errand(look):\n    return asdict(look.progress)['x']\n",
            "F3b dataclasses.asdict": "import dataclasses\n\n\ndef errand(look):\n    return dataclasses.asdict(look.progress)\n",
            "F7 a .get": "def errand(memory):\n    return memory.last_save.get('play_time')\n",
            "F8 a match class keyword": "def errand(look):\n    match look.progress:\n        case object(play_time=t):\n"
                                        "            return t\n",
            "F9 astuple": "from dataclasses import astuple\n\n\ndef errand(look):\n    return astuple(look.progress)[-1]\n",
            "F11 a match mapping key": "def errand(line):\n    match line:\n        case {'play_time': t}:\n            return t\n",
            "a named constant": "FIELD = 'play_time'\n\n\ndef errand(line):\n    return line[FIELD]\n",
            "attrgetter": "from operator import attrgetter\n\n\ndef errand(look):\n    return attrgetter('play_time')(look.progress)\n",
            "F12 a positional class pattern": "def errand(look):\n    match look.progress:\n"
                                              "        case Progress(_, _, _, _, _, _, _, t):\n            return t\n",
        }
        for label, source in plants.items():
            with self.subTest(plant=label):
                found = self.scan(source, rel="brain/goals.py")
                self.assertTrue([f for f in found if f.startswith("C ")], found)
        # D3 (d): a positional class pattern is refused INSIDE a door too, and as RULE A as well (flags and marks)
        positional = plants["F12 a positional class pattern"]
        for rel in ("brain/goals.py", "brain/saving.py"):
            with self.subTest(positional_in=rel):
                found = self.scan(positional, rel=rel)
                self.assertTrue([f for f in found if f.startswith("C ") and "POSITION" in f], found)
                self.assertTrue([f for f in found if f.startswith("A ") and "POSITION" in f], found)
        # (U2 spec 2026-10-30 D15, RV-5) FAULT: a builtin's NAME rebound by any binding form makes `case int(t)` read a
        # class's first field (measured: `case type() as int` then `case int(t)` returns Progress's first field,
        # `s53/u2/review_proof/probe_matchas.out`), and a builtin pattern with two sub-patterns or a keyword is no
        # self-match: each stays refused as C and A (S46g removes the rebinding check; S46h collects `ast.Name` only)
        rebound = {
            "int = Progress": "from ai_player.eyes.observation import Progress\nint = Progress\n\n\ndef errand(look):\n"
                              "    match look.progress:\n        case int(t):\n            return t\n",
            "def f(int)": "def errand(look, int):\n    match look.progress:\n        case int(t):\n            return t\n",
            "case type() as int": "def errand(look):\n    match type(look.progress):\n        case type() as int:\n"
                                  "            pass\n    match look.progress:\n        case int(t):\n            return t\n",
            "except E as int": "def errand(look, step):\n    try:\n        step()\n    except ValueError as int:\n"
                               "        pass\n    match look.progress:\n        case int(t):\n            return t\n",
            "import builtins": "import builtins\n\n\ndef errand(look):\n    match look.progress:\n        case int(t):\n"
                               "            return t\n",
            "case int(a, b)": "def errand(look):\n    match look.progress:\n        case int(a, b):\n            return a\n",
            "case int(x=1)": "def errand(look):\n    match look.progress:\n        case int(n, real=1):\n            return n\n",
        }
        for label, source in rebound.items():
            with self.subTest(rebound=label):
                found = self.scan(source, rel="brain/goals.py")
                self.assertTrue([f for f in found if f.startswith("C ") and "POSITION" in f], found)
                self.assertTrue([f for f in found if f.startswith("A ") and "POSITION" in f], found)
        # CONTROL: a self-matching builtin with ONE sub-pattern, its name the builtin's, reads nothing and passes
        for builtin in ("int", "str", "tuple"):
            with self.subTest(self_match=builtin):
                source = f"def errand(x):\n    match x:\n        case {builtin}(v):\n            return v\n    return None\n"
                self.assertEqual(self.scan(source, rel="brain/goals.py"), [])
        # FAULT (package-wide): `builtins.int = ...` in ANY AI-side module rebinds it for every module
        self.assertTrue([f for f in check_fairness.scan_file("brain/goals.py", "def errand(x):\n    match x:\n"
                                                             "        case int(v):\n            return v\n",
                                                             self.flag_names, self.dev, self.hidden, self.names,
                                                             builtins_shared=True) if "POSITION" in f])
        package = self.root / "pkg_rv5"
        shutil.copytree(REPO / "ai_player", package, ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures",
                                                                                   "gates"))
        (package / "brain" / "plant_rv5.py").write_text("def errand(x):\n    match x:\n        case int(v):\n"
                                                        "            return v\n    return None\n", encoding="utf-8")
        ok, problems, _ = check_fairness.check(package)
        self.assertTrue(ok, problems)  # CONTROL: the self-match alone, in a real package copy, passes
        (package / "world" / "plant_builtins.py").write_text("import builtins\n\nbuiltins.int = object\n", encoding="utf-8")
        ok, problems, _ = check_fairness.check(package)
        self.assertFalse(ok)  # FAULT: another module rebinds the builtin for every module
        self.assertTrue(any("plant_rv5.py" in p and "POSITION" in p for p in problems), problems)
        mentions = ('"""It never reads look.progress.play_time."""\n# progress.play_time\n\n\n'
                    "class Clock:\n    def __init__(self):\n        self.play_time = None\n\n"
                    "    def read(self):\n        return self.play_time\n\n\n"
                    "def drop(progress):\n    return replace(progress, play_time=None)\n")
        self.assertEqual(self.scan(mentions, rel="brain/goals.py"), [])
        # CONTROL: a dict display's key builds a dict (no read); a docstring and an f-string's text are mentions
        controls = {
            "a dict display key": "def build(t):\n    return {'play_time': t}\n",
            "a docstring": "def build(t):\n    \"\"\"play_time\"\"\"\n    return t\n",
            "an f-string's text": "def build(t):\n    return f'play_time {t}'\n",
            "a keyword that drops it": "def drop(progress):\n    return replace(progress, play_time=None)\n",
        }
        for label, source in controls.items():
            with self.subTest(control=label):
                self.assertEqual(self.scan(source, rel="brain/goals.py"), [])
        # CONTROL: inside a door, the attribute, the subscript and the match class keyword pass
        self.assertEqual(self.scan("def policy(look):\n    return look.progress.play_time\n", rel="brain/saving.py"), [])
        self.assertEqual(self.scan(plants["F2 a subscript"], rel="brain/saving.py"), [])
        self.assertEqual(self.scan(plants["F8 a match class keyword"].replace("object(", "Progress("),
                                   rel="brain/saving.py"), [])
        ok, problems, _ = check_fairness.check()
        self.assertTrue(ok, problems)
        stale = check_fairness.PLAY_TIME_DOORS + [("mode.py", "HandsBrain._nowhere", "a door nothing reads through")]
        with mock.patch.object(check_fairness, "PLAY_TIME_DOORS", stale):
            ok, problems, _ = check_fairness.check()
        self.assertFalse(ok)
        self.assertTrue(any("HandsBrain._nowhere" in p and "stale" in p for p in problems), problems)

    def test_vars_and_named_getattr_are_purity_s(self) -> None:
        """(R1 + R2 follow-up, spec D3: THE TWO-GATE COVER) RULE C does not judge `vars(...)` or a `getattr` with a
        non-constant name, because the PURITY gate's rule (d) refuses both in the whole AI package. FAULT: each, planted in
        brain/, fails `check_purity.scan` rule (d) (and passes RULE C, which is why the cover is the purity gate's).
        CONTROL: the real package passes both gates."""
        from ai_player.gates import check_purity

        hook, build_root = check_purity.DEFAULT_HOOK, check_purity.DEFAULT_BUILD_ROOT
        if not hook.is_file() and os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT"):
            # a COPY of the package (revert_r1's mutants) has no framework beside it: the support root's, as test_check_purity
            build_root = Path(os.environ["AI_PLAYER_TEST_SUPPORT_ROOT"]) / "sandbox-pokebot"
            hook = build_root / "plugins" / "custom_modes" / "ai_player_mode.py"
        # (the name is built, so RULE C's constant form cannot see it: only the purity gate can)
        plants = {"vars": "def errand(look):\n    return vars(look.progress)\n",
                  "a named getattr": "FIELD = 'play' + '_time'\n\n\ndef errand(look):\n    return getattr(look.progress, FIELD)\n"}
        for label, source in plants.items():
            with self.subTest(plant=label):
                self.assertFalse([f for f in self.scan(source, rel="brain/goals.py") if f.startswith("C ")],
                                 "RULE C is not this form's gate")
                package = self.root / label.replace(" ", "_") / "ai_player"
                shutil.copytree(REPO / "ai_player", package, ignore=shutil.ignore_patterns("__pycache__", "evidence",
                                                                                           "fixtures"))
                (package / "brain" / "time_plant.py").write_text(source, encoding="utf-8")
                result = check_purity.scan(package, hook if hook.is_file() else None, build_root)
                hits = [v for v in result.violations if v.rule == "d" and "time_plant.py" in v.file]
                self.assertTrue(hits, check_purity.report(result))
        ok, problems, _ = check_fairness.check()
        self.assertTrue(ok, problems)
        real = check_purity.scan(check_purity.PACKAGE_DIR, hook if hook.is_file() else None, build_root)
        self.assertTrue(real.passed, check_purity.report(real))

    def test_an_unclassified_knowledge_key_fails_and_the_real_files_pass(self) -> None:
        knowledge = self.root / "knowledge"
        shutil.copytree(REPO / "ai_player" / "knowledge", knowledge, ignore=shutil.ignore_patterns("__pycache__", "*.py"))
        self.assertEqual(check_fairness.schema_problems(knowledge)[0], [])
        data = json.loads((knowledge / "milestones.json").read_text(encoding="utf-8"))
        data["trainers"]["JOSH"]["position"] = {"map": "RUSTBORO_CITY_GYM", "x": 5, "y": 7}
        (knowledge / "milestones.json").write_text(json.dumps(data), encoding="utf-8")
        problems = check_fairness.schema_problems(knowledge)[0]
        self.assertTrue(problems and "trainers.JOSH.position" in problems[0], problems)

    def test_the_real_package_passes_and_a_stale_door_fails(self) -> None:
        ok, problems, _ = check_fairness.check()
        self.assertTrue(ok, problems)
        package = self.root / "pkg"
        shutil.copytree(REPO / "ai_player", package, ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures",
                                                                                   "gates"))
        navigator = package / "brain" / "navigator.py"
        text = navigator.read_text(encoding="utf-8")
        self.assertEqual(text.count("{name for name, on in look.progress.flags if on}"), 1)
        navigator.write_text(text.replace("{name for name, on in look.progress.flags if on}", "set()"), encoding="utf-8")
        ok, problems, _ = check_fairness.check(package)
        self.assertFalse(ok)
        self.assertTrue(any("Novelty._flags" in p and "stale" in p for p in problems), problems)


# ---------------------------------------------------------------------- G5
class DiskBudgetTests(Scratch):
    def test_under_the_budget_a_sweep_is_refused(self) -> None:
        ok, line = disk_budget.preflight(paths=[self.root], measure=lambda p: 12.4)
        self.assertFalse(ok)
        for words in ("REFUSED", "12.4 GB free", "under the 30 GB", "Nothing was played"):
            self.assertIn(words, line)
        ok, line = disk_budget.preflight(paths=[self.root], measure=lambda p: 30.0)
        self.assertTrue(ok, line)

    def test_the_real_sweep_refuses_to_start_and_writes_nothing(self) -> None:
        from ai_player.gates import rate_step5

        before = seed_ledger.LEDGER.read_bytes()
        argv = ["rate_step5.py", "--purpose", "development", "--first-seed", "9001", "--seeds", "1", "--plans", "CH1"]
        out = io.StringIO()
        original = disk_budget.preflight
        refused = lambda: original(measure=lambda p: 5.0)  # noqa: E731
        reached = []

        def no_ledger(*args, **kwargs):  # a broken budget must FAIL this test, never spend seeds or start a run
            reached.append(args)
            raise seed_ledger.Refused("the test's net: a refused sweep reached the ledger")
        with mock.patch.object(sys, "argv", argv), mock.patch.object(disk_budget, "preflight", refused), \
                mock.patch.object(seed_ledger, "begin", no_ledger), contextlib.redirect_stdout(out):
            code = rate_step5.main()
        self.assertEqual(code, 2)
        self.assertIn("DISK BUDGET: REFUSED", out.getvalue())
        self.assertEqual(reached, [], "a refused sweep never reaches the ledger")
        self.assertEqual(seed_ledger.LEDGER.read_bytes(), before, "a refused sweep spends no seeds")

    def test_a_sweeps_run_folders_are_deleted_but_the_failing_and_the_newest(self) -> None:
        folders = disk_budget.SweepFolders("test", base=self.root)
        runs = []
        for i in range(10):
            run = folders.new(f"ai_step5_CH1_{i}_")
            (run / "actions.jsonl").write_text("x" * 1000, encoding="utf-8")
            os.utime(run, (time.time() - 1000 + i, time.time() - 1000 + i))
            runs.append(run)
        line = folders.tidy(failing=[runs[0], runs[1]], keep_newest=3)
        self.assertEqual(sorted(r.name for r in runs if r.exists()), sorted(r.name for r in [*runs[:2], *runs[-3:]]))
        self.assertIn("5 of 10 deleted", line)
        everything = disk_budget.SweepFolders("test2", base=self.root)
        kept = [everything.new("ai_x_") for _ in range(3)]
        everything.tidy(failing=[], keep_all=True)
        self.assertTrue(all(k.exists() for k in kept))
        gone = disk_budget.SweepFolders("test3", base=self.root)
        gone.new("ai_x_")
        gone.tidy(failing=[], keep_newest=0)
        self.assertFalse(gone.root.exists(), "an emptied sweep root goes too")

    def test_a_profiles_run_folders_are_pruned_by_the_policy(self) -> None:
        runs = self.root / "ai-test" / "ai_player_runs"
        made = {}
        clean = {"verdict": "CLEAN", "facts": {"exit_code": 0}}
        # CH2 and CH2M started in the same second (two drivers side by side): one name is a PART of the other
        for i, (name, verdict) in enumerate((("20261001-000000-CH2", clean), ("20261001-000000-CH2M", clean),
                                             ("20261001-000002-FAIL", {"verdict": "DIRTY", "facts": {"exit_code": 0}}),
                                             ("20261001-000003-NOVERDICT", None), ("20261001-000004-OLD", clean),
                                             ("20261001-000005-NEW1", clean), ("20261001-000006-NEW2", clean))):
            folder = runs / name
            folder.mkdir(parents=True)
            if verdict is not None:
                (folder / "purity.json").write_text(json.dumps(verdict), encoding="utf-8")
            os.utime(folder, (time.time() - 1000 + i, time.time() - 1000 + i))
            made[name] = folder
        cited = "the review cites sandbox-pokebot/profiles/ai-test/ai_player_runs/20261001-000000-CH2M/ai_player.log"
        self.assertIn("20261001-000000-CH2", cited, "the plant: CH2's name IS a substring of the cited text")
        gone, kept, line = disk_budget.prune_runs(runs, keep_newest=2, apply=True, cited=cited)
        # CH2 is NOT cited by a text naming CH2M (a whole name only), OLD is neither failing nor cited nor newest
        self.assertEqual(sorted(p.name for p in gone), ["20261001-000000-CH2", "20261001-000004-OLD"])
        self.assertEqual(sorted(p.name for p in runs.iterdir()), sorted(n for n in made if n not in
                                                                         ("20261001-000000-CH2", "20261001-000004-OLD")))
        self.assertIn("deleted", line)


# ---------------------------------------------------------------------- G6
def multi_line_c_file(digest: str, decoy: str) -> str:
    # a script long enough that the code line falls past BOTH old readers' limits (12 lines, 4000 characters)
    script = "\n".join(["import runpy", "import sys", "", "def _run(self):",
                        f"    note = 'code: HEAD 1; working-tree digest sha256:{decoy} (a MENTION inside the script)'",
                        "    return note"] + [f"    value_{i:03d} = 'a line of the -c script, quoted by the command line'"
                                              for i in range(70)])
    return (f"AI PLAYER BUILD STEP 0.1 - LIVE PROOF - ARM G\ndate: 2026-10-15 03:14:41\ncommand: python.exe -c \n{script}\n"
            f" ai-step01-debug -m AI Player\nseed: FRESH\n"
            f"code: HEAD b029673d; ai_player/ + hook has UNCOMMITTED changes: working-tree digest sha256:{digest} over git "
            f"diff HEAD\nexit code: 9\n")


class EvidenceReaderTests(Scratch):
    def test_one_reader_finds_a_code_line_pushed_down_by_a_multi_line_command(self) -> None:
        path = self.root / "2026-10-15-step01-G.txt"
        path.write_text(multi_line_c_file(DIGEST, "ffffffffffffffff"), encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        at = next(i for i, l in enumerate(text.splitlines()) if l.startswith("code: "))
        self.assertGreater(at, 12, "the plant puts the code line below line 12")
        self.assertGreater(text.find("\ncode: "), 4000, "and past the first 4000 characters")
        self.assertEqual(file_digest(path), DIGEST)
        self.assertEqual(prune_evidence.digest_of(path), DIGEST)
        kept = keep_earlier(path, "0123456789abcdef", self.root)
        # (#28-evidence-identity) the folder is the archive key `<digest>-<HEAD>`: still its digest, never no-digest
        self.assertEqual(kept.parent.name, f"{DIGEST}-b029673d", "archived under its digest, never no-digest")

    def test_fault_the_old_12_line_reader_misses_it_or_reads_the_mention(self) -> None:
        def old_reader(text: str) -> str | None:  # provenance.evidence_digests before G6, verbatim
            head = "\n".join(text.splitlines()[:12])
            at = head.find("working-tree digest sha256:")
            return head[at + 27:at + 27 + 16] if at >= 0 else None

        self.assertEqual(old_reader(multi_line_c_file(DIGEST, "ffffffffffffffff")), "ffffffffffffffff", "the MENTION read")
        plain = multi_line_c_file(DIGEST, "ffffffffffffffff").replace("working-tree digest sha256:ffffffffffffffff", "x")
        self.assertIsNone(old_reader(plain), "the G and M6 case: no digest at all")
        self.assertEqual(code_digest(plain), DIGEST)

    def test_a_mention_inside_the_script_is_never_read(self) -> None:
        self.assertEqual(code_digest(multi_line_c_file(DIGEST, "ffffffffffffffff")), DIGEST)
        self.assertIsNone(code_digest("  code: HEAD 1; working-tree digest sha256:ffffffffffffffff\nprint('code: x')\n"))
        self.assertIsNone(code_digest(f"code: HEAD {'a' * 40} (a full hash is no digest)\n"))
        self.assertEqual(code_digest(f"code: unknown (CalledProcessError)\n[VERIFY] code: ... sha256:{DIGEST} x\n"), DIGEST)

    def test_the_real_g_and_m6_files_and_every_evidence_file_agree(self) -> None:
        archived = REPO / "ai_player" / "evidence" / "archive" / "no-digest"
        for name in ("2026-10-15-step01-G.txt", "2026-10-15-step01-M6.txt"):
            if (archived / name).is_file():
                with self.subTest(file=name):
                    self.assertEqual(file_digest(archived / name), DIGEST)
                    self.assertEqual(prune_evidence.digest_of(archived / name), DIGEST)
        for path in (REPO / "ai_player" / "evidence").rglob("*.txt"):
            self.assertEqual(file_digest(path), prune_evidence.digest_of(path), path)


# ---------------------------------------------------------------------- G7
GOOD = ("### PL-99. A planted lesson.\n- **Origin:** 2026-10-14, 08 \"A FIX ASKED ONLY UNDER ANOTHER OPTION IS DEAD CODE\".\n"
        "- **Status:** GATED\n- **Enforced:** `gates/call_census.py`, `revert_step5:G46`, `rate_step5:BOUNDS.AWAIT_MAX`, "
        "`gates/test_evidence.py::KeepEarlierTests`, `ai_player/mode.py::SETTLE_FREE`.\n- **Retires:** never.\n")


class LessonsTests(unittest.TestCase):
    def problems(self, text: str) -> list[str]:
        return check_lessons.check(text, required=())[0]

    def test_a_planted_good_lesson_passes(self) -> None:
        self.assertEqual(self.problems(GOOD), [])

    def test_a_lesson_naming_what_does_not_exist_fails(self) -> None:
        for bad in ("`gates/no_such_gate.py`", "`revert_step5:G99999`", "`gates/test_safety_gates.py::NoSuchTests`",
                    "`gate/call_census.py`", "`rate_step5:BOUNDS.NO_SUCH_BOUND`", "`ai_player/mode.py::NO_SUCH_NAME`"):
            with self.subTest(reference=bad):
                found = self.problems(GOOD.replace("`gates/call_census.py`", bad))
                self.assertTrue(found and bad.strip("`") in found[0], found)

    def test_mentions_in_a_title_or_a_needs_line_do_not_fire(self) -> None:
        text = ("### PL-98. Someday `gates/no_such_gate.py` will check this.\n"
                "- **Origin:** 2026-10-15, REVIEW \"it loafs, and every metric pays for it\".\n- **Status:** PROSE ONLY\n"
                "- **Needs:** `gates/no_such_gate.py` and `revert_step9:G1`.\n- **Retires:** when built.\n")
        self.assertEqual(self.problems(text), [])

    def test_a_wrong_origin_a_gated_lesson_without_a_gate_and_a_prose_lesson_without_needs_fail(self) -> None:
        self.assertTrue(self.problems(GOOD.replace("A FIX ASKED ONLY UNDER", "A FIX NEVER WRITTEN UNDER")))
        no_gate = GOOD.split("- **Enforced:**")[0] + "- **Enforced:** the census.\n- **Retires:** never.\n"
        self.assertTrue(any("names no gate" in p for p in self.problems(no_gate)))
        prose = GOOD.replace("GATED", "PROSE ONLY")
        self.assertTrue(any("Needs" in p for p in self.problems(prose)))

    def test_the_real_lessons_list_passes(self) -> None:
        problems, counts = check_lessons.check(check_lessons.LESSONS.read_text(encoding="utf-8"))
        self.assertEqual(problems, [])
        self.assertGreater(sum(counts.values()), 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
