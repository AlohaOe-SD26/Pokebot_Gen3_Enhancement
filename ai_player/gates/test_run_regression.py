"""FAULT tests for the regression runner `run_regression.py` (spec S4-1): every guard must FAIL when the rule it keeps is
broken, and stay quiet on the healthy path.

    py -3.12 ai_player/gates/test_run_regression.py          (under 5 s: run_units and the --quick lane run it)

WHY (CLAUDE.md session rule 6): the runner turns many raw logs into ONE typed word per suite, so a wrong reading is a
wrong verdict nobody re-reads. Each test here runs FAKE suites (tiny scripts in a temporary folder, never the real
suites, never a rate_* or live_* driver, never the seed ledger) through the REAL loop, and has a FAULT arm (the rule
broken: the guard must fire) and a CONTROL arm (the healthy path passes):
  T1 statuses        PASS, FAIL (exit 1), FAIL (exit 0 with `NOT CAUGHT`), VACUOUS, PASS (N skipped), TIMEOUT (its child
                     process killed too), CRASH (exit 0, no verdict line); exit code and overall verdict.
  T2 parallel        4 fakes sleeping SLEEP s finish in < 2.5 x SLEEP with 4 workers; with 1 worker they take >= 4 x SLEEP.
                     (The spec's 2 s sleeps would make this file take > 8 s against its own 5 s budget: the proportions
                     are kept, the sleep is SLEEP.)
  T3 shard planner   on the REAL test_check_purity module every method is named exactly once; a planner that drops one is
                     refused; a new method in a synthetic module lands in a shard with no edit to the time table.
  T4 frozen tree     a fake that edits a watched file makes its suite and the run FAIL "the tree changed mid-run".
  T5 refusal         a probe reporting a rate_step5.py process -> exit 2 and nothing written; an empty probe runs.
  T6 summary         schema 1, valid JSON, <= 4 KB with 40 failing suites (lists truncated with a count); `overall` agrees
                     with the console line.
  T7 pairing         keep_earlier and prune_evidence --retire move a `.txt`'s `.summary.json` with it.
  T8 scope           a `covers:<suite>` code line reads `ok` in regression_due on a throw-away git repo; a covered edit is
                     DUE, an uncovered one stays ok; a `covers:` label of an unknown suite is DUE.
  T9 run_units       a suite past its timeout is recorded TIMEOUT, the runner finishes and writes its evidence.
  RX regexes         every verdict regex matches its positives (real tails quoted in the recon) and none of its negatives.
The slow runs start together in `setUpModule` (threads), so the file's wall time is about the longest of them.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools" / "workflows"))

from ai_player.gates import prune_evidence, run_regression as rr  # noqa: E402
from ai_player.gates.provenance import glob_regex, keep_earlier, suite_line, summary_of  # noqa: E402

SLEEP = 0.6
OLD, NEW = "8b742931d35fa205", "0123456789abcdef"
TMP = Path(tempfile.mkdtemp(prefix="ai_test_regression_"))
RESULTS: dict[str, object] = {}
THREADS: list[threading.Thread] = []


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    return path


def fake(folder: Path, name: str, body: str, kind: str = "unittest", group: str = "units") -> rr.Suite:
    """A fake suite: a tiny script whose output imitates a real suite's verdict lines."""
    return rr.Suite(name, (str(write(folder / f"{name}.py", "import sys, time, subprocess\n" + textwrap.dedent(body))),),
                    kind, group)


UT_OK = "print('Ran 3 tests in 0.010s', file=sys.stderr); print('', file=sys.stderr); print('OK', file=sys.stderr)\n"


def config(folder: Path, names, **kw) -> tuple[rr.Config, list[str]]:
    said: list[str] = []
    cfg = rr.Config(repo=folder, lane="full", workers=kw.pop("workers", 8), timeout=kw.pop("timeout", 30.0), times={},
                    evidence=kw.pop("evidence", folder / "evidence"), probe=kw.pop("probe", lambda: []),
                    watch_scope=kw.pop("watch_scope", ("pkg",)), scopes=None, command="test", date="2026-10-21",
                    printer=said.append, unit_names=tuple(names), **kw)
    return cfg, said


def background(key: str, fn) -> None:
    def go() -> None:
        start = time.monotonic()
        try:
            RESULTS[key] = fn()
        except BaseException as error:  # noqa: BLE001 - re-raised by the test that reads it
            RESULTS[key] = error
        if os.environ.get("RR_TIMES"):
            print(f"[{key}] {time.monotonic() - start:.2f} s", file=sys.stderr)
    thread = threading.Thread(target=go, daemon=True)
    thread.start()
    THREADS.append(thread)


def result(key: str):
    for thread in THREADS:
        thread.join(60)
    value = RESULTS[key]
    if isinstance(value, BaseException):
        raise value
    return value


def alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


# ------------------------------------------------------------------------------------------- the background runs
def t1_run():
    folder = TMP / "t1"
    child = folder / "child.pid"
    suites = [
        fake(folder, "ok", UT_OK),
        fake(folder, "exit1", UT_OK + "sys.exit(1)\n"),
        fake(folder, "notcaught", "print('[M1] BROKEN: x. Predicted CAUGHT by [t]. The copy ran 3 tests (the copy); "
                                  "failing: {} -> NOT CAUGHT'); print('OVERALL: PASS')\n", kind="revert"),
        fake(folder, "vacuous", "print('Ran 0 tests in 0.000s', file=sys.stderr); print('OK', file=sys.stderr)\n"),
        fake(folder, "skips", "print('Ran 4 tests in 0.010s', file=sys.stderr); print('OK (skipped=2)', file=sys.stderr)\n"),
        fake(folder, "hang", f"""
            kid = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
            open({str(child)!r}, 'w').write(str(kid.pid))
            time.sleep(60)
            """),
        fake(folder, "crash", "print('hello, I printed no verdict')\n"),
    ]
    cfg, said = config(folder, [s.name for s in suites], timeout=2.0)
    code = rr.run(suites, [("rate_step5", rr.GRADED)], cfg)
    pid = int(child.read_text()) if child.is_file() else None
    deadline = time.monotonic() + 3
    while pid is not None and alive(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    return code, said, folder, pid, pid is not None and alive(pid)


def t1_control():
    folder = TMP / "t1c"
    suites = [fake(folder, "ok", UT_OK)]
    cfg, said = config(folder, ["ok"])
    return rr.run(suites, [], cfg), said, folder


def t2(workers: int):
    folder = TMP / f"t2w{workers}"
    suites = [fake(folder, f"s{i}", f"time.sleep({SLEEP})\n" + UT_OK) for i in range(4)]
    cfg, said = config(folder, [s.name for s in suites], workers=workers, evidence=None)
    start = time.monotonic()
    code = rr.run(suites, [], cfg)
    return code, time.monotonic() - start, said


def t4(touch: bool):
    folder = TMP / ("t4f" if touch else "t4c")
    target = write(folder / "pkg" / "a.py", "A = 1\n")
    body = f"open({str(target)!r}, 'a').write('B = 2\\n')\n" if touch else f"open({str(target)!r}).read()\n"
    suites = [fake(folder / "suites", "edits" if touch else "reads", body + UT_OK)]
    cfg, said = config(folder, [s.name for s in suites])
    return rr.run(suites, [], cfg), said, folder


def t5(probe):
    folder = TMP / ("t5f" if probe else "t5c")
    suites = [fake(folder / "suites", "ok", UT_OK)]
    cfg, said = config(folder, ["ok"], probe=lambda: probe)
    return rr.run(suites, [], cfg), said, folder


SHARDED_MODULE = """
import sys, unittest
class A(unittest.TestCase):
    def test_one(self): pass
    def test_two(self): pass
class B(unittest.TestCase):
    def test_three(self): pass
if __name__ == "__main__":
    if {lie}:
        print("Ran 2 tests in 0.001s", file=sys.stderr); print("OK", file=sys.stderr)
    else:
        unittest.main()
"""


def t3_sharded(lie: bool):
    folder = TMP / ("t3l" if lie else "t3h")
    module = write(folder / "test_sharded.py", SHARDED_MODULE.format(lie=lie))
    suite = rr.Suite("sharded", (str(module),), "unittest", sharded=True)
    cfg, said = config(folder, ["sharded"], evidence=None)
    return rr.run([suite], [], cfg), said


RUN_UNITS_WRAPPER = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from ai_player.gates import run_units
suites = {"hang": ([sys.argv[2]], 2), "quick": ([sys.argv[3]], 2)}
sys.exit(run_units.main(sys.argv[4:], suites=suites))
"""


def t9(names: str):
    folder = TMP / f"t9-{names.replace(',', '-')}"
    wrapper = write(folder / "wrap.py", RUN_UNITS_WRAPPER)
    hang = write(folder / "hang.py", "import time\ntime.sleep(60)\n")
    quick = write(folder / "quick.py", UT_OK.replace("sys.", "__import__('sys')."))
    evidence = folder / "units.txt"
    done = subprocess.run([sys.executable, str(wrapper), str(REPO), str(hang), str(quick), "--suites", names,
                           "--evidence", str(evidence), "--timeout", "1"], capture_output=True, timeout=60,
                          env={**os.environ, "PYTHONUTF8": "1"})
    text = evidence.read_text(encoding="utf-8") if evidence.is_file() else None
    return done.returncode, (done.stdout + done.stderr).decode("utf-8", "replace"), text


def setUpModule() -> None:  # noqa: N802
    background("t1", t1_run)
    background("t1c", t1_control)
    background("t2p", lambda: t2(4))
    background("t2s", lambda: t2(1))
    background("t4f", lambda: t4(True))
    background("t4c", lambda: t4(False))
    background("t5f", lambda: t5([(4242, "C:\\Python312\\python.exe ai_player/gates/rate_step5.py --purpose development")]))
    background("t5c", lambda: t5([]))
    background("t9f", lambda: t9("hang,quick"))
    background("t9c", lambda: t9("quick"))
    background("t8", t8_run)
    background("t3h", lambda: t3_sharded(False))
    background("t3l", lambda: t3_sharded(True))


def tearDownModule() -> None:  # noqa: N802
    for thread in THREADS:
        thread.join(60)
    shutil.rmtree(TMP, ignore_errors=True)


def row_of(said: list[str], name: str) -> str:
    return next(l for l in said if l.split()[1:2] == [name] or f" {name} " in l)


def summary(folder: Path) -> dict:
    return json.loads((folder / "evidence" / "2026-10-21-regression-units.summary.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------------- T1
class StatusTests(unittest.TestCase):
    def test_t1_fault_each_broken_suite_gets_its_status(self) -> None:
        code, said, folder, pid, child_alive = result("t1")
        statuses = {r["name"]: r["status"] for r in summary(folder)["suites"]}
        self.assertEqual(statuses, {"ok": "PASS", "exit1": "FAIL", "notcaught": "FAIL", "vacuous": "VACUOUS",
                                    "skips": "PASS", "hang": "TIMEOUT", "crash": "CRASH", "rate_step5": "NOT-RUN"},
                         "\n".join(said))
        self.assertEqual(code, rr.EXIT_FAIL)
        self.assertIn("REGRESSION: FAIL (full, 7 suites,", "\n".join(said))
        self.assertIn("PASS (2 skipped)", row_of(said, "skips"))
        skips = next(r for r in summary(folder)["suites"] if r["name"] == "skips")
        self.assertEqual((skips["tests"], skips["skipped"]), (4, 2))

    def test_t1_fault_a_timed_out_suites_child_process_is_killed_too(self) -> None:
        code, said, folder, pid, child_alive = result("t1")
        self.assertIsNotNone(pid, "the hanging fake never started its child")
        self.assertFalse(child_alive, f"the timed-out suite's child {pid} is still running")

    def test_t1_control_a_passing_suite_passes_and_exits_0(self) -> None:
        code, said, folder = result("t1c")
        self.assertEqual(code, rr.EXIT_PASS, "\n".join(said))
        self.assertEqual(summary(folder)["overall"], "PASS")

    def test_t1_exit_codes_are_distinct(self) -> None:
        self.assertEqual(len({rr.EXIT_PASS, rr.EXIT_FAIL, rr.EXIT_REFUSED}), 3)
        self.assertEqual((rr.EXIT_PASS, rr.EXIT_FAIL, rr.EXIT_REFUSED), (0, 1, 2))

    def test_t1_classify_table(self) -> None:
        """The pure reader on outputs no fake runs (FAULT rows must not read PASS; CONTROL rows must)."""
        c = rr.classify
        cases = [
            ("CONTROL unittest", c("unittest", "x", 0, "Ran 5 tests in 0.1s\n\nOK\n"), "PASS"),
            ("FAULT unittest FAILED line, exit 0", c("unittest", "x", 0, "Ran 5 tests in 0.1s\nFAILED (failures=1)"), "FAIL"),
            ("FAULT 3.12 NO TESTS RAN (exit 5)", c("unittest", "x", 5, "Ran 0 tests in 0.000s\n\nNO TESTS RAN"), "VACUOUS"),
            ("FAULT a traceback, no verdict, exit 1", c("unittest", "x", 1, "Traceback (most recent call last):\n  x\nE"),
             "CRASH"),
            ("FAULT could not start", c("unittest", "x", None, "", error="FileNotFoundError: no"), "CRASH"),
            ("CONTROL revert", c("revert", "r", 0, "[R0] CONTROL, the unchanged copy: 3 tests, failing none (ran the "
                                                   "copy: True) -> PASS\n[M1] BROKEN: y -> CAUGHT\nOVERALL: PASS"), "PASS"),
            ("CONTROL redundant as predicted", c("revert", "r", 0, "[M1] BROKEN: y -> NOT CAUGHT, as predicted "
                                                                   "(redundant alone)\nOVERALL: PASS"), "PASS"),
            ("FAULT zero mutants", c("revert", "r", 0, "[R0] CONTROL, x -> PASS\nOVERALL: PASS"), "VACUOUS"),
            ("FAULT PREDICTION WRONG", c("revert", "r", 0, "[M1] y -> PREDICTION WRONG\nOVERALL: PASS"), "FAIL"),
            ("FAULT CONTROL FAIL", c("revert", "r", 0, "[R0] CONTROL, x -> FAIL\n[M1] y -> CAUGHT\nOVERALL: PASS"), "FAIL"),
            ("FAULT NO RESULT", c("revert", "r", 0, "[M1] NO RESULT: boom\n[M2] y -> CAUGHT\nOVERALL: PASS"), "FAIL"),
            ("FAULT backstop amended", c("revert", "r", 0, "[M1] y -> CAUGHT\nOVERALL: PASS\nFROZEN TREE: FAIL - x"), "FAIL"),
            ("CONTROL line rule", c("line", "check_lessons", 0, "LESSONS CHECK: PASS (0 problems)"), "PASS"),
            ("FAULT line FAIL word", c("line", "check_lessons", 1, "LESSONS CHECK: FAIL (2 problems)"), "FAIL"),
            ("FAULT line PASS and FAIL lines", c("line", "extract_knowledge_check", 0,
                                                "[KNOWLEDGE] a.json: up to date\n[KNOWLEDGE] b.json: DIFFERS from a "
                                                "fresh extraction"), "FAIL"),
            ("FAULT unknown output exit 0", c("line", "call_census", 0, "something else"), "CRASH"),
            ("FAULT a PASS line but exit 1", c("line", "call_census", 1, "CALL-SITE CENSUS: PASS"), "FAIL"),
            ("FAULT timeout", c("unittest", "x", None, "Ran 1 tests in 1s\n\nOK", timed_out=True), "TIMEOUT"),
        ]
        for label, reading, want in cases:
            with self.subTest(label):
                self.assertEqual(reading.status, want, reading)

    def test_t1_every_suite_has_a_verdict_rule(self) -> None:
        """CONTROL: the real list builds; FAULT: a checker with no rule is refused when the list is built."""
        names = {s.name for s in rr.all_suites()}
        self.assertTrue({"check_purity", "test_check_purity", "revert_step3", "test_run_regression"} <= names)
        with self.assertRaises(ValueError):
            rr._kind("a_new_checker")


# ------------------------------------------------------------------------------------------------------- T2
class ParallelTests(unittest.TestCase):
    def test_t2_control_four_workers_run_together(self) -> None:
        code, seconds, said = result("t2p")
        self.assertEqual(code, rr.EXIT_PASS, "\n".join(said))
        self.assertLess(seconds, 2.5 * SLEEP, f"4 fakes of {SLEEP} s with 4 workers took {seconds:.2f} s")

    def test_t2_fault_one_worker_runs_them_one_by_one(self) -> None:
        code, seconds, said = result("t2s")
        self.assertEqual(code, rr.EXIT_PASS, "\n".join(said))
        self.assertGreaterEqual(seconds, 4 * SLEEP, f"4 fakes of {SLEEP} s with 1 worker took only {seconds:.2f} s")

    def test_t2_the_longest_suite_starts_first(self) -> None:
        cfg = rr.Config(times={"suites": {"a": 1, "b": 2014, "c": 50}}, timeout=3600)
        jobs = rr.jobs_for([rr.Suite(n, ("x.py",), "unittest") for n in "abc"], cfg)
        self.assertEqual([j.suite.name for j in jobs], ["b", "c", "a"])
        self.assertEqual(jobs[0].timeout, 2.5 * 2014)
        self.assertEqual(jobs[1].timeout, 3600)


# ------------------------------------------------------------------------------------------------------- T3
def scan_methods(path: Path) -> list[str]:
    """An INDEPENDENT reading (line-based, not AST) of a module's `Class.test*` methods, to check the planner."""
    out, current = [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("class "):
            current = raw[6:].split("(")[0].split(":")[0].strip()
        elif raw.startswith("    def test") and current:
            out.append(f"{current}.{raw[8:].split('(')[0]}")
    return out


class ShardTests(unittest.TestCase):
    PURITY = Path(__file__).resolve().parent / "test_check_purity.py"

    def test_t3_control_every_real_method_is_named_exactly_once(self) -> None:
        times = rr.load_times().get("test_check_purity", {})
        shards = rr.plan_shards(self.PURITY, times, workers=6)
        flat = [m for s in shards for m in s]
        self.assertEqual(sorted(flat), sorted(scan_methods(self.PURITY)))
        self.assertEqual(len(flat), len(set(flat)))
        self.assertGreater(len(shards), 1, "test_check_purity was not split")

    def test_t3_fault_a_planner_that_drops_a_method_is_refused(self) -> None:
        real = rr._assign
        try:
            rr._assign = lambda methods, cost, n: [s[:-1] if i == 0 else s for i, s in enumerate(real(methods, cost, n))]
            with self.assertRaises(rr.PlanError):
                rr.plan_shards(self.PURITY, {}, workers=4)
            rr._assign = lambda methods, cost, n: [s + real(methods, cost, n)[0][:1] if i == 1 else s
                                                   for i, s in enumerate(real(methods, cost, n))]
            with self.assertRaises(rr.PlanError):
                rr.plan_shards(self.PURITY, {}, workers=4)
        finally:
            rr._assign = real

    def test_t3_control_a_sharded_suite_runs_each_method_once(self) -> None:
        code, said = result("t3h")
        self.assertEqual(code, rr.EXIT_PASS, "\n".join(said))
        line = row_of(said, "sharded")
        self.assertIn("3 tests, 3 shards", line)

    def test_t3_fault_shards_that_ran_another_number_of_tests_fail(self) -> None:
        code, said = result("t3l")
        self.assertEqual(code, rr.EXIT_FAIL, "\n".join(said))
        self.assertIn("the shards ran 6 tests; the plan named 3 methods", row_of(said, "sharded"))

    def test_t3_a_new_method_lands_in_a_shard_with_no_table_edit(self) -> None:
        module = write(TMP / "t3" / "test_synthetic.py", """
            import unittest
            class Base(unittest.TestCase):
                def test_inherited(self): pass
            class A(Base):
                def test_known(self): pass
                def test_brand_new(self): pass
                def helper(self): pass
            class NotATest:
                def test_ignored(self): pass
            """)
        shards = rr.plan_shards(module, {"A.test_known": 10.0}, workers=4)
        flat = sorted(m for s in shards for m in s)
        self.assertEqual(flat, ["A.test_brand_new", "A.test_inherited", "A.test_known", "Base.test_inherited"])


# ------------------------------------------------------------------------------------------------------- T4
class FrozenTreeTests(unittest.TestCase):
    def test_t4_fault_a_suite_that_edits_the_tree_fails_the_run(self) -> None:
        code, said, folder = result("t4f")
        row = next(r for r in summary(folder)["suites"] if r["name"] == "edits")
        self.assertEqual(row["status"], "FAIL", "\n".join(said))
        self.assertIn("the tree changed mid-run", row["failing"][0])
        self.assertEqual(code, rr.EXIT_FAIL)
        self.assertTrue(any(l.startswith("FROZEN TREE: FAIL") for l in said), "\n".join(said))

    def test_t4_control_a_read_only_suite_passes(self) -> None:
        code, said, folder = result("t4c")
        self.assertEqual(code, rr.EXIT_PASS, "\n".join(said))
        self.assertTrue(any(l.startswith("FROZEN TREE: PASS") for l in said))


# ------------------------------------------------------------------------------------------------------- T5
class RefusalTests(unittest.TestCase):
    def test_t5_fault_a_running_rate_driver_refuses_and_writes_nothing(self) -> None:
        code, said, folder = result("t5f")
        self.assertEqual(code, rr.EXIT_REFUSED, "\n".join(said))
        self.assertFalse((folder / "evidence").exists(), "evidence was written by a refused run")
        self.assertIn("REFUSED", said[0])

    def test_t5_control_an_empty_probe_runs(self) -> None:
        code, said, folder = result("t5c")
        self.assertEqual(code, rr.EXIT_PASS, "\n".join(said))
        self.assertTrue((folder / "evidence" / "2026-10-21-regression-units.summary.json").is_file())

    def test_t5_the_probe_filter_and_an_unreadable_probe(self) -> None:
        rows = [(1, "py -3.12 ai_player/gates/rate_step5.py --purpose graded"), (2, "python live_step0.py"),
                (3, "py -3.12 ai_player/gates/run_regression.py"), (4, "py tools/workflows/regression_due.py"),
                (5, "py generate_x.py"), (6, "py my_rate_step5.py"), (os.getpid(), "rate_step5.py")]
        self.assertEqual([p for p, _ in rr.drivers_in(rows)], [1, 2])

        def broken():
            raise OSError("no process list")
        self.assertIsNotNone(rr.refusal(rr.Config(probe=broken)))
        self.assertIsNone(rr.refusal(rr.Config(probe=lambda: [])))


# ------------------------------------------------------------------------------------------------------- T6
class SummaryTests(unittest.TestCase):
    def forty(self) -> tuple[Path, dict, int]:
        folder = TMP / "t6"
        rows = [rr.Row(f"suite_{i:02d}", "FAIL", 1, 12.5, 30, 0,
                       [f"FAIL: test_number_{j} of suite {i} " + "x" * 150 for j in range(5)], group="units")
                for i in range(40)]
        cfg, _ = config(folder, [r.name for r in rows])
        watch = rr.TreeWatch(cfg)
        uncapped = {"schema": 1, "suites": [r.summary() for r in rows]}
        written = rr.write_evidence(rows, cfg, watch, "FROZEN TREE: PASS", "REGRESSION: FAIL (full, 40 suites, 1 s wall)",
                                    "FAIL", "2026-10-21T00:00:00", 1.0)
        return written[0][1], uncapped, len(json.dumps(uncapped).encode("utf-8"))

    def test_t6_fault_forty_failing_suites_stay_under_4_kb_with_counts(self) -> None:
        path, uncapped, raw_size = self.forty()
        self.assertGreater(raw_size, rr.SUMMARY_CAP, "the arm is vacuous: the uncapped summary already fits")
        size = path.stat().st_size
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertLessEqual(size, rr.SUMMARY_CAP, f"the summary file is {size} bytes")
        self.assertEqual(data["schema"], 1)
        kept = len(data["suites"])
        self.assertGreater(kept, 0)
        self.assertEqual(kept + data["suites_omitted"]["count"], 40)
        self.assertEqual(data["suites_omitted"]["by_status"], {"FAIL": 40 - kept})
        for row in data["suites"]:
            self.assertTrue(any(f.startswith("(+") for f in row["failing"]), row)  # truncated WITH a count

    def test_t6_control_a_small_summary_is_whole_and_agrees_with_the_console(self) -> None:
        code, said, folder = result("t1c")
        data = summary(folder)
        self.assertNotIn("suites_omitted", data)
        self.assertEqual(data["schema"], 1)
        console = next(l for l in said if l.startswith("REGRESSION: "))
        self.assertTrue(console.startswith(f"REGRESSION: {data['overall']} "), console)
        code, said, folder, _, _ = result("t1")
        console = next(l for l in said if l.startswith("REGRESSION: "))
        self.assertTrue(console.startswith(f"REGRESSION: {summary(folder)['overall']} "), console)
        for key in ("lane", "started", "wall_s", "code_line", "overall", "suites"):
            self.assertIn(key, data)


# ------------------------------------------------------------------------------------------------------- T7
def evidence_file(folder: Path, name: str, digest: str, title: str = "TITLE") -> Path:
    path = write(folder / name, f"{title}\ncode: HEAD abc1234; covers:units has UNCOMMITTED changes (the code under test "
                                f"is the working tree): working-tree digest sha256:{digest} over git diff HEAD\n")
    summary_of(path).write_text('{"schema": 1}\n', encoding="utf-8")
    return path


def orphans(folder: Path) -> list[str]:
    """Top-level summaries whose `.txt` is not beside them."""
    return [p.name for p in folder.glob("*.summary.json") if not (folder / (p.name[:-len(".summary.json")] + ".txt"))
            .is_file()]


class PairingTests(unittest.TestCase):
    def test_t7_control_keep_earlier_moves_the_summary_with_its_txt(self) -> None:
        folder = TMP / "t7k"
        path = evidence_file(folder, "2026-10-21-regression-units.txt", OLD)
        target = keep_earlier(path, current=NEW, folder=folder)
        self.assertEqual(orphans(folder), [])
        self.assertTrue(summary_of(target).is_file(), "the summary did not follow its .txt into the archive")
        again = evidence_file(folder, "2026-10-21-regression-units.txt", OLD, title="A LATER RUN OF THE SAME TREE")
        second = keep_earlier(again, current=NEW, folder=folder)
        self.assertEqual(second.name, "2026-10-21-regression-units.1.txt")
        self.assertTrue(summary_of(second).is_file())
        self.assertEqual(orphans(folder), [])
        # the same bytes again: the .txt is absorbed by its archived twin, and its summary must not stay behind
        twin = evidence_file(folder, "2026-10-21-regression-units.txt", OLD)
        summary_of(twin).write_text('{"schema": 1, "a": "different summary"}\n', encoding="utf-8")
        self.assertEqual(keep_earlier(twin, current=NEW, folder=folder), target)
        self.assertEqual(orphans(folder), [])
        self.assertFalse(summary_of(twin).exists(), "the absorbed .txt's summary stayed at the top level")

    def test_t7_fault_moving_only_the_txt_leaves_an_orphan(self) -> None:
        folder = TMP / "t7f"
        path = evidence_file(folder, "x.txt", OLD)
        (folder / "archive").mkdir()
        shutil.move(str(path), str(folder / "archive" / "x.txt"))  # the old keep_earlier / --retire
        self.assertEqual(orphans(folder), ["x.summary.json"])

    def test_t7_prune_retire_takes_the_summary_with_the_txt(self) -> None:
        folder = TMP / "t7p"
        cited_txt = evidence_file(folder, "2026-10-21-regression-units.txt", OLD)
        uncited_txt = evidence_file(folder, "2026-10-21-regression-quick.txt", OLD)
        other = evidence_file(folder, "2026-10-21-other.txt", NEW)
        text = "the run 2026-10-21-regression-units.txt passed"
        moves, candidates = prune_evidence.retire_plan(folder, folder / "archive", OLD, text)
        self.assertEqual(sorted(s.name for s, _ in moves), sorted([cited_txt.name, summary_of(cited_txt).name]))
        self.assertTrue(all(t.parent == folder / "archive" / OLD for _, t in moves))
        self.assertEqual(sorted(p.name for p in candidates), sorted([uncited_txt.name, summary_of(uncited_txt).name]))
        self.assertNotIn(summary_of(other), candidates)
        self.assertTrue(prune_evidence.cited(summary_of(cited_txt), text))
        self.assertFalse(prune_evidence.cited(summary_of(uncited_txt), text))


class SnapshotTests(unittest.TestCase):
    """(spec S4-1 section 4, recon Q3(d)) `snapshot_tree` writes under a temporary name and replaces it into place."""

    def test_snapshot_writes_a_temporary_name_then_replaces(self) -> None:
        import zipfile

        from ai_player.gates import provenance

        result("t1c")  # joins every background run first: the patches below are process-wide
        folder = TMP / "snap"
        opened: list[str] = []
        real_zip, real_read = zipfile.ZipFile, provenance.read_tree

        class Spy(real_zip):
            def __init__(self, file, mode="r", *a, **k):
                if mode == "w":
                    opened.append(Path(file).name)
                super().__init__(file, mode, *a, **k)
        try:
            zipfile.ZipFile = Spy
            provenance.read_tree = lambda repo, scope=None: ("abc1234", b"diff --git a/x b/x\n", {"u.py": b"U"}, 1)
            target = provenance.snapshot_tree(TMP, folder)
        finally:
            zipfile.ZipFile, provenance.read_tree = real_zip, real_read
        self.assertIsNotNone(target)
        self.assertEqual(len(opened), 1)
        self.assertNotEqual(opened[0], target.name, "the zip was written in place: two writers could interleave")
        self.assertEqual([p.name for p in folder.iterdir()], [target.name], "a temporary file was left behind")
        self.assertEqual(provenance.tree_files(target)[0], target.stem, "the kept tree does not recompute to its name")


# ------------------------------------------------------------------------------------------------------- T8
def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", *args],
                          cwd=str(repo), capture_output=True, check=True, text=True).stdout


def t8_run() -> dict[str, tuple[bool, str]]:
    """The T8 scenario on a throw-away git repo: each step's regression_due row, by step name (run in the background:
    its many read-only git calls are the slowest part of this file)."""
    import regression_due as rd

    repo = TMP / "t8"
    for rel, body in {"ai_player/__init__.py": "", "ai_player/a.py": "A = 1\n", "ai_player/doc.md": "# d\n",
                      "other/b.py": "B = 1\n", "LESSONS.md": "# L\n"}.items():
        write(repo / rel, body)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "c1")
    exclude = ["ai_player/evidence/**", "**/*.md", "map.json"]
    units = {"evidence": ["*-units.txt"], "covers": ["ai_player/**"], "reads": ["LESSONS.md"]}
    smap = {"evidence_dir": "ai_player/evidence", "exclude": exclude,
            "suites": {"units": units, "ghost": {"evidence": ["*-ghost.txt"], "covers": ["ai_player/**"]}}}
    (repo / "map.json").write_text(json.dumps(smap), encoding="utf-8")
    steps: dict[str, tuple[bool, str]] = {}

    def rows():
        return {n: (due, why) for n, due, why in rd.assess(repo, rd.load_map(repo / "map.json", repo))}

    def evidence(name: str, suite: str) -> None:
        write(repo / "ai_player" / "evidence" / name, f"TITLE\ncode: {suite_line(repo, suite, units, exclude)}\n")

    evidence("2026-10-21-regression-units.txt", "units")
    evidence("2026-10-21-x-ghost.txt", "nosuch")
    r = rows()
    steps["fresh"], steps["ghost"] = r["units"], r["ghost"]
    (repo / "other" / "b.py").write_text("B = 2\n", encoding="utf-8")
    steps["uncovered edit"] = rows()["units"]
    (repo / "ai_player" / "doc.md").write_text("# d2\n", encoding="utf-8")
    steps["excluded doc edit"] = rows()["units"]
    (repo / "ai_player" / "a.py").write_text("A = 2\n", encoding="utf-8")
    steps["covered edit"] = rows()["units"]
    (repo / "ai_player" / "a.py").write_text("A = 1\n", encoding="utf-8")
    steps["covered edit undone"] = rows()["units"]
    (repo / "LESSONS.md").write_text("# L2\n", encoding="utf-8")
    steps["reads edit"] = rows()["units"]
    return steps


class ScopeTests(unittest.TestCase):
    def test_t8_control_a_fresh_covers_label_reads_ok_and_uncovered_edits_keep_it(self) -> None:
        steps = result("t8")
        for step in ("fresh", "uncovered edit", "excluded doc edit", "covered edit undone"):
            with self.subTest(step):
                self.assertFalse(steps[step][0], steps[step][1])

    def test_t8_fault_a_covered_or_read_edit_is_due_and_an_unknown_suite_label_too(self) -> None:
        steps = result("t8")
        self.assertTrue(steps["covered edit"][0] and "a.py" in steps["covered edit"][1], steps["covered edit"])
        self.assertTrue(steps["reads edit"][0] and "LESSONS.md" in steps["reads edit"][1], steps["reads edit"])
        self.assertTrue(steps["ghost"][0] and "unknown scope label" in steps["ghost"][1], steps["ghost"])

    def test_t8_the_evidence_names_match_the_shipped_suite_map(self) -> None:
        smap = json.loads(rr.SUITE_MAP.read_text(encoding="utf-8"))
        for group, stem in rr.EVIDENCE_NAMES.items():
            with self.subTest(group):
                name = f"2026-10-21-{stem}.txt"
                self.assertTrue(any(glob_regex(g.lower()).match(name) for g in smap["suites"][group]["evidence"]), name)
                others = [s for s, v in smap["suites"].items() if s != group
                          and any(glob_regex(g.lower()).match(name) for g in v["evidence"])]
                self.assertEqual(others, [], f"{name} would also be read as evidence of {others}")
        for partial in ("regression-quick", "regression-partial"):
            name = f"2026-10-21-{partial}.txt"
            self.assertFalse(any(glob_regex(g.lower()).match(name) for s in smap["suites"].values()
                                 for g in s["evidence"]), f"a partial run's {name} would clear a suite")


# ------------------------------------------------------------------------------------------------------- T9
class RunUnitsTimeoutTests(unittest.TestCase):
    def test_t9_fault_a_hung_suite_is_timeout_and_the_evidence_is_written(self) -> None:
        code, out, text = result("t9f")
        self.assertEqual(code, 1, out)
        self.assertIsNotNone(text, "run_units wrote no evidence after a hung suite:\n" + out)
        self.assertIn("== hang:", text)
        self.assertIn("TIMEOUT", text)
        self.assertIn("== quick:", text)
        self.assertIn("OVERALL: FAIL", text)

    def test_t9_control_a_quick_suite_passes(self) -> None:
        code, out, text = result("t9c")
        self.assertEqual(code, 0, out)
        self.assertIn("OVERALL: PASS", text)


# ------------------------------------------------------------------------------------------------------- RX
POSITIVE = {
    "unittest Ran": ["Ran 29 tests in 264.396s", "Ran 107 tests in 0.916s", "Ran 1 test in 0.001s"],
    "unittest OK": ["OK", "OK (skipped=2)"],
    "unittest FAILED": ["FAILED (failures=1)", "FAILED (failures=1, errors=2, skipped=1)"],
    "revert OVERALL": ["OVERALL: PASS", "OVERALL: FAIL"],
    "revert mutant": ["[G46] BROKEN: losses counted on the main path only. Predicted CAUGHT by ['t']. The copy ran 120 "
                      "tests (the copy); failing: {'t': 'AssertionError'} -> CAUGHT",
                      "[R1] finding 3: REVERTED to x. Predicted to fail: ['t']. The copy ran 9 tests (the copy); "
                      "failing: {} -> NOT CAUGHT",
                      "[M2] BROKEN: y. Predicted REDUNDANT ALONE, because z The copy ran 5 tests; failing: none -> "
                      "NOT CAUGHT, as predicted (redundant alone)",
                      "[M3] BROKEN: y. Predicted REDUNDANT ALONE, because z The copy ran 5 tests; failing: none -> "
                      "as predicted", "[M4] BROKEN: y ... -> PREDICTION WRONG"],
    "revert CONTROL": ["[R0] CONTROL, the unchanged copy: 120 tests, failing none (ran the copy: True) -> PASS",
                       "[S0] CONTROL, the unchanged copy: 0 tests, failing ['x'] (ran the copy: False) -> FAIL"],
    "revert NO RESULT": ["[M3] NO RESULT: Traceback (most recent call last):", "[R2] finding 7: NO RESULT: boom"],
    "frozen-tree FAIL": ["FROZEN TREE: FAIL - the tree changed mid-run: after suite x: 1 changed ['a.py']"],
    "traceback": ["Traceback (most recent call last):"],
    "check_purity PASS": ["VERDICT: PASS"], "check_purity FAIL": ["VERDICT: FAIL"],
    "extract_knowledge_check PASS": ["[KNOWLEDGE] types.json: up to date", "[KNOWLEDGE] species.json: up to date"],
    "extract_knowledge_check FAIL": ["[KNOWLEDGE] moves.json: DIFFERS from a fresh extraction"],
    "extract_milestones_check PASS": ["[MILESTONES] ai_player\\knowledge\\milestones.json is up to date"],
    "extract_milestones_check FAIL": ["[MILESTONES] ai_player\\knowledge\\milestones.json DIFFERS from a fresh extraction"],
    "ledger_check PASS": ["LEDGER ledger.json: 34 entries; well formed -> PASS"],
    "ledger_check FAIL": ["LEDGER ledger.json: 34 entries; FAIL: entry 3 has no purpose"],
    "call_census PASS": ["CALL-SITE CENSUS: PASS"], "call_census FAIL": ["CALL-SITE CENSUS: FAIL"],
    "check_fairness PASS": ["PERSON-FAIR DATA DOOR: PASS (0 breaches)"],
    "check_fairness FAIL": ["PERSON-FAIR DATA DOOR: FAIL (2 breaches)"],
    "check_lessons PASS": ["LESSONS CHECK: PASS (0 problems)"], "check_lessons FAIL": ["LESSONS CHECK: FAIL (1 problems)"],
    "disk_budget PASS": ["DISK BUDGET: C:\\ 30.0 GB free (a sweep needs 30 GB to start)"],
}
NEGATIVE = {
    "unittest Ran": ["  Ran 3 tests in 1s", "Ran tests", "Ran 3 tests in 1s and more"],
    "unittest OK": ["OKAY", " OK", "OK (skipped=2) later", "LOOKS OK"],
    "unittest FAILED": ["FAILED", "TEST FAILED (x)", "  FAILED (failures=1)"],
    "revert OVERALL": ["[VERIFY] OVERALL PASS", "  OVERALL: PASS", "[LIVE5] OVERALL PASS: arm PASS"],
    "revert mutant": ["[R0] CONTROL, the unchanged copy: 1 tests, failing none (ran the copy: True) -> PASS",
                      "summary -> CAUGHT", "[M1] y -> CAUGHT later", "3 mutants CAUGHT as predicted, of 3"],
    "revert CONTROL": ["[M1] BROKEN: y -> CAUGHT", "CONTROL -> PASS"],
    "revert NO RESULT": ["the copy said NO RESULT: x", " [M1] NO RESULT: x"],
    "frozen-tree FAIL": ["FROZEN TREE: PASS - the tree did not change", "  FROZEN TREE: FAIL - x"],
    "traceback": ["  Traceback (most recent call last):", "Traceback"],
    "check_purity PASS": ["VERDICT: FAIL", "VERDICT: PASS (GRADED, seeds 941-960, ledger #34)"],
    "check_purity FAIL": ["VERDICT: PASS", "VERDICT: FAILED_X"],
    "extract_knowledge_check PASS": ["[KNOWLEDGE] moves.json: DIFFERS from a fresh extraction", "[KNOWLEDGE] : up to date"],
    "extract_knowledge_check FAIL": ["[KNOWLEDGE] types.json: up to date"],
    "extract_milestones_check PASS": ["[MILESTONES] wrote x: 3 milestones", "[MILESTONES] m.json DIFFERS from a fresh extraction"],
    "extract_milestones_check FAIL": ["[MILESTONES] m.json is up to date"],
    "ledger_check PASS": ["LEDGER ledger.json: 34 entries; FAIL: x", "LEDGER ledger.json: well formed -> PASS"],
    "ledger_check FAIL": ["LEDGER ledger.json: 34 entries; well formed -> PASS"],
    "call_census PASS": ["CALL-SITE CENSUS: FAIL", "CALL-SITE CENSUS since HEAD: 0 AI files changed"],
    "call_census FAIL": ["CALL-SITE CENSUS: PASS", "CALL-SITE CENSUS: FAILED"],
    "check_fairness PASS": ["PERSON-FAIR DATA DOOR: FAIL (2 breaches)", "PERSON-FAIR DATA DOOR: PASS"],
    "check_fairness FAIL": ["PERSON-FAIR DATA DOOR: PASS (0 breaches)"],
    "check_lessons PASS": ["LESSONS CHECK: FAIL (1 problems)", "LESSONS LESSONS.md: 54 lessons"],
    "check_lessons FAIL": ["LESSONS CHECK: PASS (0 problems)"],
    "disk_budget PASS": ["%TEMP%/ai_* folders: 19288 (`--temp` for their sizes)", "DISK BUDGET:"],
}


class RegexTests(unittest.TestCase):
    def test_rx_every_verdict_regex_on_its_positives_and_negatives(self) -> None:
        rules = rr.verdict_rules()
        self.assertEqual(set(rules), set(POSITIVE), "every verdict regex needs positives here (and vice versa)")
        self.assertEqual(set(rules), set(NEGATIVE), "every verdict regex needs negatives here (and vice versa)")
        for name, pattern in rules.items():
            print(f"regex {name}: {pattern.pattern}", file=sys.stderr)
            for text in POSITIVE[name]:
                with self.subTest(rule=name, positive=text):
                    self.assertIsNotNone(pattern.search(text))
            for text in NEGATIVE[name]:
                with self.subTest(rule=name, negative=text):
                    self.assertIsNone(pattern.search(text))


if __name__ == "__main__":
    unittest.main(verbosity=2)
