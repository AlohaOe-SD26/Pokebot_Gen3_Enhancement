"""TEST SIDE: THE AGENT-FREE REGRESSION RUNNER (spec S4-1, 2026-10-21; backlog A2 + P7, round 2 N8's runner half).

    py -3.12 ai_player/gates/run_regression.py [--quick | --full] [--workers N] [--evidence] [--only NAME ...] [--list]
        --quick   the per-edit lane (target <= 25 s wall): the fast unit suites, in parallel; evidence only with --evidence
        --full    (the default) every unit suite (test_check_purity SHARDED by test method) and the six revert drivers,
                  in parallel up to --workers (default 6); always writes its evidence
        exit 0 PASS; 1 FAIL / VACUOUS / TIMEOUT / CRASH; 2 refused (a rate_*/live_* driver is running, or a bad
        argument): nothing is run and nothing is written

WHY. The AI player's 17 unit suites ran SERIALLY through `run_units.py` (6 m 13 s quiet, 9 m 28 s busy; test_check_purity
alone 265-382 s), the six revert drivers were run by hand one by one (on 2026-10-16 they were chained by a script that is
not in the tree), and a builder then read raw logs to learn the verdict. This runner chains them all, in parallel, and
ends each in ONE typed status, so a reader takes the <= 4 KB `<evidence>.summary.json` and calls an agent only on a
failure (recon note `PROJECT KNOWLEDGE/ai-research-notes/2026-10-21-A2-P7-recon.md`, Q1-Q6).

THE TYPED VERDICT (N8). PASS / FAIL / VACUOUS / TIMEOUT / CRASH / NOT-RUN, from the verdict lines the recon quotes ONLY
(`VERDICT_RULES`, printed by `--list`): unittest's `Ran N tests` + `OK`/`FAILED`, `VERDICT:`, `OVERALL:`, the revert
words, and each checker's own last line. Exit 0 with no recognised verdict line is CRASH, never PASS (a suite that
printed nothing it is known to print has proven nothing). `Ran 0 tests`, or a revert driver with zero mutant lines, is
VACUOUS. `OK (skipped=N)` stays PASS but prints `PASS (N skipped)`: a skip was silent before.

NEVER GRADED, NEVER THE ROM. The rate_* and live_* drivers need the ROM, and rate_step5 WRITES the seed ledger whose
graded seeds are single-use: they are listed NOT-RUN, never run. And the runner REFUSES to start (exit 2, nothing written)
while one of them is running: test_safety_gates compares the ledger's bytes before and after (recon Q3(d)), so a sweep
writing it would fail it spuriously, and two writers would race on `evidence/trees/<digest>.zip`.

THE FROZEN TREE (G1). `provenance.FrozenTree` over the hook scope, as run_units, PLUS the `covers:<suite>` digest of every
evidence group (git, `provenance.suite_trees`), both taken before the first suite and checked after EVERY suite: a change
makes that suite FAIL ("the tree changed mid-run") and the run FAIL. A suite run on another tree has proven nothing about
this one.

THE EVIDENCE (the remedy regression_due's docstring names). One file per suite_map.json suite the run covered, named for
its glob (`EVIDENCE_NAMES`), whose code line is `covers:<suite>`: a digest over EXACTLY the files regression_due checks
for that suite (`provenance.suite_line`, the same function regression_due recomputes), so a clean, fresh run reads `ok`.
The four revert drivers with no suite there (step11, step2, step3, step4) go into the units file's appendix. A run that
did not run every unit suite (--quick, --only) writes `<date>-regression-quick.txt` / `-partial.txt` instead, names no
suite_map glob matches: a partial run never clears `units`. Each file is written through `provenance.keep_earlier` (an
earlier tree's file is archived with its summary; #28-evidence-identity: "earlier tree" by IDENTITY, given this run's own
`covers:<suite>` code line, never by the digest alone, which is the same for every clean tree) and has its
`<stem>.summary.json` beside it; the UNITS file's summary
is the whole run's.

SHARDING (P7). The tests of a sharded module (test_check_purity) are the ones UNITTEST'S OWN LOADER collects
(`loader_names`: `TestLoader().loadTestsFromModule` on the module, imported in a fresh interpreter so a broken module
fails loudly), never a typed list and never a reading of the source. (S4-1 fix round, verifier F1: the first build read
the AST, which missed an aliased method, a TestCase imported under another name, an IsolatedAsyncioTestCase and a class
under an `if`, so a sharded module with two failing tests in such classes read PASS.) They are balanced longest-first over
shards by the measured table `run_regression_times.json`; a test missing from the table still runs. Before anything runs,
`plan_shards` checks that the shards name EXACTLY the loader's list (`check_partition`); on any mismatch, or when the
loader cannot read the module, the module runs UNSHARDED and its row says so (`ran UNSHARDED: <why>`). A sharded suite
whose shards ran another number of tests than the plan named is FAIL. The ROUND3 method (about 61 s) is the floor; its
subTests are not split.

A TIMEOUT KILLS EVERYTHING THE SUITE STARTED (S4-1 fix round, verifier F5). `taskkill /T` walks parent links, so it
misses a grandchild whose parent has already exited. On Windows every suite therefore starts SUSPENDED, is put in its
own Job Object with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE, and only then resumes (`_Job`, `run_command`): every process it
starts is in the job from birth. A timeout terminates the job; and when the suite ends normally the job is closed, so
a leftover process of a FINISHED suite dies too (it could otherwise write into the tree after the suite's frozen-tree
check). Elsewhere: a new session and `killpg`.

KNOWN LIMITS (said, not fixed; the S4-1 verify's weak proofs):
  - A covered file OUTSIDE the hook scope that a suite edits and then restores within that suite is not seen: the
    `covers:` digests are content digests, and the content is back. Inside the hook scope FrozenTree sees the rewrite.
  - unittest-kind and line-kind suites do not read `NOT CAUGHT` / `PREDICTION WRONG` words: their own output can carry
    them legitimately (test_run_regression prints its revert-word fixtures). Only revert-kind suites FAIL on them.
  - disk_budget is a REPORT: `DISK BUDGET: REFUSED ...` reads PASS (its line proves it ran to its end). A suite whose
    every test was skipped reads `PASS (N skipped)`, as the spec says.
  - The refusal probe sees a driver launched as `<path>/rate_*.py` / `live_*.py` or `-m <pkg>.rate_*` / `live_*`; one
    launched through `-c`, `runpy` or a renamed copy is not seen.
  - A test class defined INSIDE a module's `if __name__ == "__main__":` block is invisible to the loader (the module is
    imported, not run); a sharded run would skip it.
  - regression_due picks the newest same-date `*-units.txt` by mtime (its pre-existing `newest_evidence` rule): a
    copy that preserved an older file's mtime can make `units` read DUE although this runner's file is fresh.
  - Elsewhere than Windows there is no job object: a grandchild that left the process group survives a timeout.
  - `run_units.run_command` hands every command to `run_command` here (verify round 2): there is ONE suite runner, so
    the serial unit runner has the same timeout kill as this one.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import run_units  # noqa: E402
from ai_player.gates.provenance import (EVIDENCE, HOOK_SCOPE, MID_RUN, FrozenTree, keep_earlier,  # noqa: E402
                                        line, suite_trees, summary_of, tree_digest)

GATES = Path(__file__).resolve().parent
TIMES = GATES / "run_regression_times.json"
SUITE_MAP = REPO / "tools" / "workflows" / "suite_map.json"

PASS, FAIL, VACUOUS, TIMEOUT, CRASH, NOT_RUN = "PASS", "FAIL", "VACUOUS", "TIMEOUT", "CRASH", "NOT-RUN"
#: the worst status wins when a suite's shards are merged
SEVERITY = {PASS: 0, VACUOUS: 1, CRASH: 2, TIMEOUT: 3, FAIL: 4}
EXIT_PASS, EXIT_FAIL, EXIT_REFUSED = 0, 1, 2
SUMMARY_CAP = 4096
DEFAULT_WORKERS = 6
DEFAULT_TIMEOUT = 3600.0
#: a suite whose measured time x this exceeds the default timeout gets that instead (revert_step3: 2,014 s -> 7,049 s).
#: 3.5, not the first build's 2.5: the first real --full run (2026-10-21, beside the bot tuner's 12 lanes) took 4,339 s,
#: 86 % of 2.5x; 3.5x leaves that run at 62 %.
TIMEOUT_FACTOR = 3.5
GRADED = "graded / needs the ROM: run it deliberately"
GRADED_DRIVERS = ("rate_step3", "rate_step4", "rate_step5", "live_step0", "live_step1", "live_step2", "live_step3",
                  "live_step4", "live_step5")

# ------------------------------------------------------------------------------------------------- the verdict rules
#: A unittest run: `Ran N tests in Xs`, then `OK` / `OK (skipped=N)` / `FAILED (failures=N, ...)`; 3.12 prints
#: `NO TESTS RAN` (exit 5) for zero tests.
UT_RAN = re.compile(r"^Ran (?P<n>\d+) tests? in \d+(?:\.\d+)?s$", re.M)
UT_OK = re.compile(r"^OK(?: \((?P<info>[^)\n]*)\))?$", re.M)
UT_FAILED = re.compile(r"^FAILED \((?P<info>[^)\n]*)\)$", re.M)
UT_SKIPPED = re.compile(r"\bskipped=(\d+)")
#: A revert driver (revert_step*.py, revert_safety_gates.py): one line per mutant ending in its word, a CONTROL line
#: ending `-> PASS|FAIL`, `NO RESULT` for a copy that printed no result, then `OVERALL: PASS|FAIL`.
RV_OVERALL = re.compile(r"^OVERALL: (?P<word>PASS|FAIL)\b", re.M)
RV_MUTANT = re.compile(r"^\[(?P<name>[^\]\n]+)\] (?!CONTROL\b).*-> (?P<word>CAUGHT|NOT CAUGHT, as predicted "
                       r"\(redundant alone\)|NOT CAUGHT|as predicted|PREDICTION WRONG)$", re.M)
RV_CONTROL = re.compile(r"^\[[^\]\n]+\] CONTROL\b.*-> (?P<word>PASS|FAIL)$", re.M)
RV_NO_RESULT = re.compile(r"^\[[^\]\n]+\] (?:[^\n]*?: )?NO RESULT: ", re.M)
#: (S4-1 fix round, verifier F6) the words that FAIL a revert driver, ANYWHERE in ANY line, in any spacing and with any
#: suffix ("-> NOT CAUGHT (copy timed out)", a trailing space, two spaces): the first build matched them only in the
#: `$`-anchored RV_MUTANT form, so a variant line read PASS. The one exemption is a line that IS the exact pass form
#: "-> NOT CAUGHT, as predicted (redundant alone)" (RV_MUTANT, whole line). Upper case only: the drivers print the words
#: in capitals, and a lower-case "not caught" is prose (a docstring, a test name). This is applied to revert-kind suites
#: ONLY: a unittest or line suite's own output can carry the words legitimately (test_run_regression prints these very
#: fixtures), and those suites are read by their own verdict lines.
RV_ANY_BAD = re.compile(r"NOT\s+CAUGHT|PREDICTION\s+WRONG")
#: the provenance backstop's amended line (any driver), and a Python traceback
FROZEN_FAIL = re.compile(r"^FROZEN TREE: FAIL\b", re.M)
TRACEBACK = re.compile(r"^Traceback \(most recent call last\):$", re.M)

#: The checkers that are neither unittest nor revert drivers: (PASS line, FAIL line), each quoted from the recon's Q1
#: table and the drivers' own print calls. A PASS line with a FAIL line beside it is FAIL.
LINE_RULES: dict[str, tuple[str, str | None]] = {
    "check_purity": (r"^VERDICT: PASS$", r"^VERDICT: FAIL\b"),
    "extract_knowledge_check": (r"^\[KNOWLEDGE\] \S.*: up to date$", r"^\[KNOWLEDGE\] .*: DIFFERS from a fresh extraction$"),
    "extract_milestones_check": (r"^\[MILESTONES\] \S.* is up to date$",
                                 r"^\[MILESTONES\] .* DIFFERS from a fresh extraction$"),
    "ledger_check": (r"^LEDGER .*: \d+ entries; well formed -> PASS$", r"^LEDGER .*: \d+ entries; FAIL: "),
    "call_census": (r"^CALL-SITE CENSUS: PASS$", r"^CALL-SITE CENSUS: FAIL$"),
    "check_fairness": (r"^PERSON-FAIR DATA DOOR: PASS \(\d+ breaches\)$", r"^PERSON-FAIR DATA DOOR: FAIL\b"),
    "check_lessons": (r"^LESSONS CHECK: PASS \(\d+ problems\)$", r"^LESSONS CHECK: FAIL\b"),
    # a REPORT: it always exits 0 (recon Q1); its line proves it ran to its end
    "disk_budget": (r"^DISK BUDGET: \S", None),
}


def verdict_rules() -> dict[str, re.Pattern]:
    """Every compiled verdict regex by name (`--list` prints them; the tests run each on positives and negatives)."""
    rules = {"unittest Ran": UT_RAN, "unittest OK": UT_OK, "unittest FAILED": UT_FAILED, "revert OVERALL": RV_OVERALL,
             "revert mutant": RV_MUTANT, "revert bad word": RV_ANY_BAD, "revert CONTROL": RV_CONTROL,
             "revert NO RESULT": RV_NO_RESULT,
             "frozen-tree FAIL": FROZEN_FAIL, "traceback": TRACEBACK}
    for name, (good, bad) in LINE_RULES.items():
        rules[f"{name} PASS"] = re.compile(good, re.M)
        if bad:
            rules[f"{name} FAIL"] = re.compile(bad, re.M)
    return rules


@dataclass(frozen=True)
class Suite:
    """One suite: its arguments after the interpreter, how its verdict is read ("unittest", "revert" or "line"), its
    evidence group (a suite_map.json suite), and whether it is sharded by test method."""
    name: str
    command: tuple[str, ...]
    kind: str
    group: str = "units"
    sharded: bool = False


def _kind(name: str) -> str:
    if name.startswith("revert_"):
        return "revert"
    if name in LINE_RULES:
        return "line"
    if name.startswith("test_"):
        return "unittest"
    raise ValueError(f"suite {name!r} has no verdict rule: add it to LINE_RULES (a suite whose verdict cannot be read "
                     f"would read CRASH on every run)")


REVERTS = ("revert_step3", "revert_safety_gates", "revert_step5", "revert_step2", "revert_step11", "revert_step4")
#: evidence group -> the file stem it writes (`<date>-<stem>.txt`): each must match its suite's glob in suite_map.json
EVIDENCE_NAMES = {"units": "regression-units", "revert_step5": "regression-step5-revert",
                  "revert_safety_gates": "regression-revert-gates"}
QUICK = ("check_purity", "test_eyes", "test_hands", "test_battle", "test_evidence", "extract_knowledge_check",
         "test_goals", "extract_milestones_check", "ledger_check", "call_census", "check_fairness", "check_lessons",
         "disk_budget", "test_run_regression")


def all_suites() -> list[Suite]:
    """run_units' SUITES (the unit suites) and the six revert drivers, every one with a verdict rule."""
    out = [Suite(name, tuple(command), _kind(name), sharded=name == "test_check_purity")
           for name, (command, _) in run_units.SUITES.items()]
    for name in REVERTS:
        out.append(Suite(name, (str(GATES / f"{name}.py"),), "revert",
                         group=name if name in EVIDENCE_NAMES else "units"))
    return out


# --------------------------------------------------------------------------------------------- reading one output
@dataclass
class Reading:
    status: str
    tests: int | None = None
    skipped: int = 0
    failing: list[str] = field(default_factory=list)
    unit: str = "tests"


def _lines(pattern: re.Pattern, text: str) -> list[str]:
    return [m.group(0) for m in pattern.finditer(text)]


def classify(kind: str, name: str, code: int | None, text: str, timed_out: bool = False, error: str | None = None,
             timeout: float | None = None) -> Reading:
    """The ONE status of one finished command (see the module docstring). Pure: what the tests check."""
    if error:
        return Reading(CRASH, failing=[f"could not start: {error}"])
    text = "\n".join(text.splitlines())
    tail = [l for l in text.splitlines() if l.strip()][-3:]
    if timed_out:
        return Reading(TIMEOUT, failing=[f"no verdict within {timeout or 0:g} s: the process tree was killed"] + tail[-2:])
    verdict, count, skipped, bad, unit = None, None, 0, [], "tests"
    if kind == "unittest":
        ran = UT_RAN.findall(text)
        count = sum(int(n) for n in ran) if ran else None
        failed = list(UT_FAILED.finditer(text))
        oks = list(UT_OK.finditer(text))
        skipped = sum(int(n) for m in (oks + failed) for n in UT_SKIPPED.findall(m.group("info") or ""))
        if failed:
            verdict, bad = FAIL, [m.group(0) for m in failed] + [l for l in text.splitlines()
                                                                if l.startswith(("FAIL: ", "ERROR: "))]
        elif ran and oks:
            verdict = PASS
        elif ran and count == 0 and "NO TESTS RAN" in text:
            verdict = PASS  # read below as VACUOUS (Python 3.12 exits 5 for it)
    elif kind == "revert":
        unit = "mutants"
        mutants = list(RV_MUTANT.finditer(text))
        count = len(mutants)
        redundant = {m.group(0) for m in mutants if m.group("word").startswith("NOT CAUGHT, as predicted")}
        bad = ([l for l in text.splitlines() if RV_ANY_BAD.search(l) and l not in redundant]
               + [m.group(0) for m in RV_CONTROL.finditer(text) if m.group("word") == "FAIL"]
               + _lines(RV_NO_RESULT, text))
        words = [m.group("word") for m in RV_OVERALL.finditer(text)]
        if words:
            verdict = FAIL if FAIL in words else PASS
    else:
        unit = "lines"
        good, worse = LINE_RULES[name]
        goods = _lines(re.compile(good, re.M), text)
        bad = _lines(re.compile(worse, re.M), text) if worse else []
        count = len(goods)
        if bad:
            verdict = FAIL
        elif goods:
            verdict = PASS
    bad = bad + _lines(FROZEN_FAIL, text)
    if bad or verdict == FAIL:
        return Reading(FAIL, count, skipped, (bad or tail)[:3], unit)
    if code != 0:
        if kind == "unittest" and count == 0 and code == 5:
            return Reading(VACUOUS, 0, skipped, ["Ran 0 tests (NO TESTS RAN)"], unit)
        if verdict is None and TRACEBACK.search(text):
            return Reading(CRASH, count, skipped, ["a traceback and no verdict line"] + tail[-2:], unit)
        return Reading(FAIL, count, skipped, [f"exit {code}"] + tail[-2:], unit)
    if verdict is None:
        return Reading(CRASH, count, skipped, ["exit 0 with no recognised verdict line"] + tail[-2:], unit)
    if count == 0 and kind in ("unittest", "revert"):
        return Reading(VACUOUS, 0, skipped, [f"0 {unit}: the suite proved nothing"], unit)
    return Reading(PASS, count, skipped, [], unit)


# ------------------------------------------------------------------------------------------------- the shard planner
class PlanError(ValueError):
    pass


#: Run in a FRESH interpreter by `loader_names`: import the module as `py <module>.py` would see it (its folder first on
#: sys.path; under its own name, so its `if __name__ == "__main__":` block does not run), let unittest's own loader
#: collect it, and print one marked JSON line. `names` are what a shard passes on the command line (`<attribute>.<test>`,
#: resolved by `unittest.main` against the module, exactly as `loadTestsFromModule` walks `dir(module)`); `named_ids` are
#: their test ids, which must equal the loader's `ids` or the names do not describe what unittest would run.
_LOADER = r'''
import importlib.util, json, sys, unittest
from pathlib import Path
path = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(path.parent))
spec = importlib.util.spec_from_file_location(path.stem, path)
module = importlib.util.module_from_spec(spec)
sys.modules[path.stem] = module
spec.loader.exec_module(module)
loader = unittest.TestLoader()
def flat(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flat(test)
        else:
            yield test
ids = sorted(test.id() for test in flat(loader.loadTestsFromModule(module)))
names, named_ids = [], []
for attr in dir(module):
    obj = getattr(module, attr)
    if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj not in (unittest.TestCase,
                                                                                     unittest.FunctionTestCase):
        for test in flat(loader.loadTestsFromTestCase(obj)):
            names.append(attr + "." + test._testMethodName)
            named_ids.append(test.id())
print("\n" + MARK + json.dumps({"ids": ids, "names": names, "named_ids": sorted(named_ids)}))
'''
_LOADER_MARK = "@@RUN_REGRESSION_LOADER@@ "


def loader_names(module: Path, cwd: Path = REPO, timeout: float = 120.0) -> list[str]:
    """The `<attribute>.<test>` name of EVERY test `unittest.TestLoader().loadTestsFromModule` collects from `module`
    (S4-1 fix round, verifier F1: the loader is the source of truth, not the source text). Imported in a subprocess, so
    a broken module fails LOUDLY (PlanError with its traceback's tail) and never half-imports into this process. Raises
    PlanError when the module cannot be imported, when the loader collects tests the names cannot reproduce (a
    `load_tests` hook, say), or when it has no tests."""
    try:
        done = subprocess.run([sys.executable, "-c", _LOADER.replace("MARK", repr(_LOADER_MARK), 1), str(module)],
                              cwd=str(cwd), capture_output=True, timeout=timeout,
                              env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    except (OSError, subprocess.SubprocessError) as error:
        raise PlanError(f"unittest's loader could not be run on {module.name}: {type(error).__name__}: {error}")
    out = done.stdout.decode("utf-8", "replace")
    # the marked line is the loader script's LAST act: it is there only when the import and the collection succeeded
    marked = [l[len(_LOADER_MARK):] for l in out.splitlines() if l.startswith(_LOADER_MARK)]
    if not marked:
        tail = [l for l in (out + done.stderr.decode("utf-8", "replace")).splitlines() if l.strip()][-2:]
        raise PlanError(f"unittest's loader could not import {module.name} (exit {done.returncode}): {' | '.join(tail)}")
    data = json.loads(marked[-1])
    if data["named_ids"] != data["ids"]:
        only = sorted(set(data["ids"]) ^ set(data["named_ids"]))[:3]
        raise PlanError(f"unittest's loader collects tests that cannot be named one by one (a load_tests hook?): {only}")
    if not data["names"]:
        raise PlanError(f"{module.name} has no test methods")
    return list(data["names"])


def check_partition(methods: Iterable[str], shards: list[list[str]]) -> None:
    """Raise PlanError unless every method is named EXACTLY ONCE across the shards."""
    methods = list(methods)
    flat = [m for shard in shards for m in shard]
    dropped = sorted(set(methods) - set(flat))
    repeated = sorted({m for m in flat if flat.count(m) > 1})
    foreign = sorted(set(flat) - set(methods))
    if dropped or repeated or foreign:
        raise PlanError(f"the shard plan is not a partition of the module's methods: dropped {dropped}, repeated "
                        f"{repeated}, not in the module {foreign}")


def _assign(methods: list[str], cost: dict[str, float], n: int) -> list[list[str]]:
    """Longest-first: each method to the shard with the least time so far."""
    shards: list[list[str]] = [[] for _ in range(n)]
    loads = [0.0] * n
    for method in sorted(methods, key=lambda m: (-cost[m], m)):
        at = loads.index(min(loads))
        shards[at].append(method)
        loads[at] += cost[method]
    return shards


def plan_shards(module: Path, times: dict[str, float], workers: int, default: float = 2.0,
                names: list[str] | None = None, cwd: Path = REPO) -> list[list[str]]:
    """The shards of `module`'s tests (`names`, default: `loader_names`, unittest's own list): as many as their total
    time over the longest (the floor), at most `workers`, balanced by `times` (a test missing there costs `default`).
    Checked to be EXACTLY the loader's list before anything runs (`check_partition`; PlanError otherwise)."""
    methods = list(names) if names is not None else loader_names(module, cwd)
    if not methods:
        raise PlanError(f"{module.name} has no test methods")
    cost = {m: float(times.get(m, default)) for m in methods}
    n = max(1, min(workers, len(methods), math.ceil(sum(cost.values()) / max(max(cost.values()), 0.1))))
    shards = [sorted(s) for s in _assign(methods, cost, n) if s]
    check_partition(methods, shards)
    return shards


# --------------------------------------------------------------------------------------------------------- the run
@dataclass
class Job:
    suite: Suite
    argv: list[str]
    estimate: float
    timeout: float
    shard: int | None = None
    methods: tuple[str, ...] = ()
    #: how many tests this job must report (a shard: its methods); None = not checked (an unsharded run)
    planned: int | None = None
    #: said on the suite's row (a sharded suite that ran UNSHARDED, and why)
    note: str = ""


@dataclass
class Done:
    job: Job
    ran: run_units.Ran
    reading: Reading
    moved: str | None
    started: str


@dataclass
class Row:
    name: str
    status: str
    exit: int | None = None
    seconds: float = 0.0
    tests: int | None = None
    skipped: int = 0
    failing: list[str] = field(default_factory=list)
    shards: int | None = None
    unit: str = "tests"
    group: str = "units"
    note: str = ""
    output: list[tuple[str, str]] = field(default_factory=list)

    def word(self) -> str:
        return f"{self.status} ({self.skipped} skipped)" if self.status == PASS and self.skipped else self.status

    def summary(self) -> dict:
        if self.status == NOT_RUN:
            return {"name": self.name, "status": NOT_RUN, "note": self.note}
        return {"name": self.name, "status": self.status, "exit": self.exit, "seconds": round(self.seconds, 1),
                "tests": self.tests, "skipped": self.skipped, "failing": [f[:200] for f in self.failing[:3]]
                + ([f"(+{len(self.failing) - 3} more)"] if len(self.failing) > 3 else []), "shards": self.shards,
                **({"note": self.note[:200]} if self.note else {})}


@dataclass
class Config:
    """Everything a run depends on, so the tests run fake suites in a scratch folder through the real loop."""
    repo: Path = REPO
    lane: str = "full"
    workers: int = DEFAULT_WORKERS
    timeout: float = DEFAULT_TIMEOUT
    times: dict = field(default_factory=dict)
    evidence: Path | None = None
    probe: Callable[[], list[tuple[int, str]]] | None = None
    watch_scope: tuple[str, ...] = HOOK_SCOPE
    #: evidence group -> (its suite_map.json suite, the map's exclude): the `covers:<suite>` scopes; None = no git
    scopes: dict[str, tuple[dict, list]] | None = None
    command: str = ""
    date: str = ""
    printer: Callable[[str], None] = print
    #: the suites a complete units file needs (a units group lacking one is written as a partial file)
    unit_names: tuple[str, ...] = tuple(run_units.SUITES)


def jobs_for(suites: list[Suite], cfg: Config) -> list[Job]:
    """The work, longest first (revert_step3 starts FIRST: it is the wall floor)."""
    measured = cfg.times.get("suites", {})
    out = []
    for suite in suites:
        timeout = max(cfg.timeout, TIMEOUT_FACTOR * float(measured.get(suite.name, 0)))
        if suite.sharded:
            module = Path(suite.command[0])
            per = cfg.times.get(suite.name, {})
            default = float(cfg.times.get("default_method_s", 2.0))
            try:
                shards = plan_shards(module, per, cfg.workers, default, cwd=cfg.repo)
            except PlanError as why:
                # the plan cannot be proven to be what unittest would run: run what unittest would run, and say so
                est = float(measured.get(suite.name, sum(per.values()) or cfg.times.get("default_suite_s", 5.0)))
                out.append(Job(suite, [sys.executable, *suite.command], est, timeout,
                               note=f"ran UNSHARDED: {str(why)[:300]}"))
                continue
            for i, methods in enumerate(shards):
                est = sum(float(per.get(m, default)) for m in methods) + 1
                out.append(Job(suite, [sys.executable, *suite.command, *methods], est, cfg.timeout, i, tuple(methods),
                               planned=len(methods)))
        else:
            est = float(measured.get(suite.name, cfg.times.get("default_suite_s", 5.0)))
            out.append(Job(suite, [sys.executable, *suite.command], est, timeout))
    return sorted(out, key=lambda j: -j.estimate)


CREATE_SUSPENDED = 0x00000004
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9


class _Job:
    """(S4-1 fix round, verifier F5) A Windows Job Object that kills every process in it when it is closed
    (JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE). A process put in it passes membership on to every process it starts, so
    `kill()` (TerminateJobObject) reaches a grandchild whose parent has already exited, which `taskkill /T` (it walks
    parent links) cannot. Raises OSError when the job cannot be made or a process cannot join it."""

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        class Basic(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class Io(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOperationCount", "WriteOperationCount",
                                                         "OtherOperationCount", "ReadTransferCount",
                                                         "WriteTransferCount", "OtherTransferCount")]

        class Extended(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", Io), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        # private DLL objects: their argtypes never clash with another module's use of ctypes.windll
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._ntdll = ctypes.WinDLL("ntdll")
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.CreateJobObjectW.argtypes = (wintypes.LPVOID, wintypes.LPCWSTR)
        k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD)
        k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
        k32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        self._ntdll.NtResumeProcess.argtypes = (wintypes.HANDLE,)
        self._ntdll.NtResumeProcess.restype = ctypes.c_long
        self._k32, self._ctypes = k32, ctypes
        self.handle = k32.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = Extended()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(self.handle, _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, ctypes.byref(info),
                                           ctypes.sizeof(info)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def adopt(self, process: subprocess.Popen) -> None:
        """Put a process started with CREATE_SUSPENDED in the job, THEN let it run: it can start nothing outside it."""
        handle = int(process._handle)  # noqa: SLF001 - Popen's own process handle (Windows)
        if not self._k32.AssignProcessToJobObject(self.handle, handle):
            raise self._ctypes.WinError(self._ctypes.get_last_error())
        status = self._ntdll.NtResumeProcess(handle)
        if status != 0:
            raise OSError(f"NtResumeProcess failed with NTSTATUS {status & 0xFFFFFFFF:#010x}")

    def kill(self) -> None:
        """Terminate every process in the job now."""
        if self.handle:
            self._k32.TerminateJobObject(self.handle, 1)

    def close(self) -> None:
        """Close the job (idempotent): KILL_ON_JOB_CLOSE ends whatever is still in it."""
        if self.handle:
            handle, self.handle = self.handle, None
            self._k32.CloseHandle(handle)


def run_command(argv: list[str], cwd: Path, timeout: float, env: dict | None = None) -> run_units.Ran:
    """Run one suite command to its end or to `timeout` seconds (`run_units.run_command`'s contract: output to temporary
    FILES, never pipes; never raises for the command's sake). (S4-1 fix round, verifier F5) On Windows the command runs
    in its own `_Job` from birth, so a TIMEOUT kills every process it started, an orphaned grandchild too, and a leftover
    process of a suite that ended normally dies when the job closes. A job that cannot be made, or a process that
    cannot join it, comes back with `error` set (CRASH): a suite whose processes could not be bounded is not run."""
    start = time.monotonic()
    job = None
    if os.name == "nt":
        try:
            job = _Job()
        except OSError as error:
            return run_units.Ran(None, "", time.monotonic() - start, error=f"no job object: {error}")
    extra = {"creationflags": CREATE_SUSPENDED} if job else {"start_new_session": True}
    try:
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            try:
                process = subprocess.Popen(argv, cwd=str(cwd), stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                                           env=env, **extra)
            except OSError as error:
                return run_units.Ran(None, "", time.monotonic() - start, error=f"{type(error).__name__}: {error}")
            if job:
                try:
                    job.adopt(process)
                except OSError as error:
                    process.kill()
                    process.wait()
                    return run_units.Ran(None, "", time.monotonic() - start,
                                         error=f"the suite could not be held in a job object: {error}")
            timed_out = False
            try:
                code: int | None = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                if job:
                    job.kill()
                else:
                    run_units.kill_tree(process.pid)
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                code, timed_out = None, True
            out.seek(0)
            err.seek(0)
            text = (out.read() + err.read()).decode("utf-8", "replace")
    finally:
        if job:
            job.close()
    return run_units.Ran(code, text, time.monotonic() - start, timed_out)


def running_drivers() -> list[tuple[int, str]]:
    """(pid, command line) of every running process whose command line names a `rate_*.py` or `live_*.py` driver.
    Windows: `Get-CimInstance Win32_Process` through PowerShell; elsewhere `ps`. Raises when the list cannot be read
    (the caller REFUSES then: an unreadable process list cannot prove no sweep is running)."""
    if os.name == "nt":
        done = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                               "Get-CimInstance Win32_Process | Select-Object ProcessId,CommandLine | "
                               "ConvertTo-Json -Compress"], capture_output=True, timeout=60, check=True)
        data = json.loads(done.stdout.decode("utf-8", "replace") or "[]")
        rows = [(int(d.get("ProcessId") or 0), d.get("CommandLine") or "") for d in (data if isinstance(data, list)
                                                                                     else [data])]
    else:
        done = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True, timeout=60, check=True, text=True)
        rows = [(int(p), a) for p, _, a in (l.strip().partition(" ") for l in done.stdout.splitlines()) if p.isdigit()]
    return drivers_in(rows)


#: a `rate_*.py` / `live_*.py` file on the command line, or (S4-1 fix round, a verify weak proof) a module run as
#: `-m [pkg.]rate_*` / `-m [pkg.]live_*` (`py -m ai_player.gates.rate_step5`: no `.py` appears on that command line)
DRIVER = re.compile(r"(?<![A-Za-z0-9_])(?:rate|live)_[A-Za-z0-9_]+\.py(?![A-Za-z0-9_])"
                    r"|(?:^|\s)-m\s*[\"']?(?:[A-Za-z0-9_]+\.)*(?:rate|live)_[A-Za-z0-9_]+(?![A-Za-z0-9_.])")


def drivers_in(rows: Iterable[tuple[int, str]]) -> list[tuple[int, str]]:
    return [(pid, cmd) for pid, cmd in rows if pid != os.getpid() and DRIVER.search(cmd or "")]


def refusal(cfg: Config) -> str | None:
    """Why the run must not start (None: it may)."""
    try:
        found = (cfg.probe or running_drivers)()
    except Exception as error:  # noqa: BLE001 - an unreadable process list proves nothing: refuse
        return f"the process list could not be read ({type(error).__name__}: {error})"
    if found:
        shown = "; ".join(f"pid {pid}: {cmd[:160]}" for pid, cmd in found[:5])
        return (f"{len(found)} graded/live driver process(es) running ({shown}). test_safety_gates compares the seed "
                f"ledger's bytes and a sweep writes it: wait for it to end")
    return None


class TreeWatch:
    """The frozen tree (G1) for one run: `FrozenTree` over `watch_scope`, plus the `covers:<suite>` digests of the
    evidence groups (when `scopes` is given), both taken now and compared after every suite. Thread-safe."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.lock = threading.Lock()
        self.frozen = FrozenTree(cfg.repo, cfg.watch_scope, explicit=True)
        self.lines: dict[str, str] = {}
        self.start: dict[str, str] | None = None
        self.error = ""
        if cfg.scopes:
            try:
                self.start = self._digests(self.lines)
            except Exception as error:  # noqa: BLE001 - said in the code line; the frozen tree still watches
                self.error = f"{type(error).__name__}: {error}"
                self.lines = {g: f"unknown ({self.error})" for g in cfg.scopes}

    def _digests(self, lines: dict[str, str] | None = None) -> dict[str, str]:
        exclude = next(iter(self.cfg.scopes.values()))[1]
        trees = suite_trees(self.cfg.repo, {g: s for g, (s, _) in self.cfg.scopes.items()}, exclude)
        out = {}
        for group, (head, diff, untracked, changed) in trees.items():
            out[group] = f"{head}:{tree_digest(diff, untracked)[:16]}"
            if lines is not None:
                lines[group] = line(head, f"covers:{group}", diff, untracked, changed)
        return out

    def check(self, when: str) -> str | None:
        """None while the tree is the start's; else what moved."""
        with self.lock:
            moved = None if self.frozen.check(when) else self.frozen.moves[-1]
            if self.start is not None:
                try:
                    now = self._digests()
                except Exception as error:  # noqa: BLE001
                    now = {"git": f"unreadable ({type(error).__name__})"}
                if now != self.start:
                    diff = {g: (self.start.get(g), now.get(g)) for g in set(now) | set(self.start)
                            if self.start.get(g) != now.get(g)}
                    moved = (moved + "; " if moved else f"{when}: ") + f"covers digests moved {diff}"
            return moved


def run(suites: list[Suite], not_run: list[tuple[str, str]], cfg: Config) -> int:
    """Run `suites` (NOT-RUN rows: `not_run`), print the console verdict, write the evidence when `cfg.evidence` is
    set, and return the exit code."""
    say = cfg.printer
    why = refusal(cfg)
    if why is not None:
        say(f"REGRESSION: REFUSED - {why}. Nothing was run and nothing was written.")
        return EXIT_REFUSED
    started_at, t0 = time.strftime("%Y-%m-%dT%H:%M:%S"), time.monotonic()
    watch = TreeWatch(cfg)
    jobs = jobs_for(suites, cfg)
    env = {**os.environ, "PYTHONUTF8": "1"}

    def one(job: Job) -> Done:
        started = time.strftime("%H:%M:%S")
        ran = run_command(job.argv, cfg.repo, job.timeout, env=env)
        reading = classify(job.suite.kind, job.suite.name, ran.code, ran.text, ran.timed_out, ran.error, job.timeout)
        label = job.suite.name if job.shard is None else f"{job.suite.name} shard {job.shard + 1}"
        moved = watch.check(f"after {label}")
        return Done(job, ran, reading, moved, started)

    with ThreadPoolExecutor(max_workers=max(1, cfg.workers)) as pool:
        finished = list(pool.map(one, jobs))
    sealed, verdict_line = watch.frozen.seal("PASS")
    final = watch.check("at the verdict")
    moved = [d.moved for d in finished if d.moved] + ([final] if final else [])
    tree_moved = sealed != "PASS" or bool(moved)
    if tree_moved and sealed == "PASS":
        verdict_line = f"FROZEN TREE: FAIL - {MID_RUN}: {moved[0][:400]}"
    elif not tree_moved and watch.start is not None:
        verdict_line += f"; the covers digests of {', '.join(sorted(watch.start))} did not move either"
    rows = merge(suites, finished) + [Row(name, NOT_RUN, note=note) for name, note in not_run]
    wall = time.monotonic() - t0
    ran_rows = [r for r in rows if r.status != NOT_RUN]
    overall = (VACUOUS if not ran_rows else PASS if all(r.status == PASS for r in ran_rows) and not tree_moved
               else FAIL)
    for row in rows:
        say(console_line(row))
    say(verdict_line)
    headline = f"REGRESSION: {overall} ({cfg.lane}, {len(ran_rows)} suites, {wall:.1f} s wall)"
    say(headline)
    if cfg.evidence is None:
        say("evidence: none written (--evidence writes it; --full always does)")
    else:
        for txt, summary in write_evidence(rows, cfg, watch, verdict_line, headline, overall, started_at, wall):
            say(f"evidence: {txt}")
            say(f"summary:  {summary}")
    return EXIT_PASS if overall == PASS else EXIT_FAIL


def merge(suites: list[Suite], finished: list[Done]) -> list[Row]:
    """One row per suite (its shards merged: the worst status, the counts summed, the plan's method count checked)."""
    rows = []
    for suite in suites:
        mine = sorted((d for d in finished if d.job.suite is suite), key=lambda d: d.job.shard or 0)
        if not mine:
            continue
        status = max((d.reading.status for d in mine), key=SEVERITY.get)
        failing = [f for d in mine for f in d.reading.failing if d.reading.status != PASS]
        moved = [d.moved for d in mine if d.moved]
        if moved:
            status = FAIL
            failing = [f"{MID_RUN}: {moved[0][:300]}"] + failing
        counts = [d.reading.tests for d in mine if d.reading.tests is not None]
        tests = sum(counts) if counts else None
        planned = [d.job.planned for d in mine]
        if status == PASS and None not in planned:
            if tests != sum(planned):
                status, failing = FAIL, [f"the shards ran {tests} tests; the plan named {sum(planned)} methods"]
        codes = [d.ran.code for d in mine]
        sharded = mine[0].job.shard is not None
        rows.append(Row(suite.name, status, next((c for c in codes if c != 0), codes[0]),
                        max(d.ran.seconds for d in mine), tests, sum(d.reading.skipped for d in mine), failing,
                        len(mine) if sharded else None, mine[0].reading.unit, suite.group,
                        note=next((d.job.note for d in mine if d.job.note), ""),
                        output=[(f"shard {d.job.shard + 1}/{len(mine)}: {' '.join(d.job.methods)}"
                                 if sharded else "", d.ran.text) for d in mine]))
    return rows


def console_line(row: Row) -> str:
    if row.status == NOT_RUN:
        return f"  {NOT_RUN:<17} {row.name:<26} {row.note}"
    key = f"{row.tests} {row.unit}" if row.tests is not None else "-"
    shards = f", {row.shards} shards" if row.shards else ""
    more = f"  -- {row.failing[0][:160]}" if row.failing else ""
    note = f"  [{row.note[:200]}]" if row.note else ""
    return f"  {row.word():<17} {row.name:<26} {row.seconds:7.1f} s  {key}{shards}{note}{more}"


# ---------------------------------------------------------------------------------------------- summary + evidence
def capped_summary(data: dict, cap: int = SUMMARY_CAP) -> str:
    """`data` as JSON (one suite per line) of at most `cap` bytes: the lists are TRUNCATED WITH A COUNT, never cut
    mid-value. First each `failing` list shrinks, then suites are dropped (NOT-RUN first, then PASS, the failures kept
    longest) into `suites_omitted: {count, by status}`."""
    def dump(d: dict) -> str:
        text = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        return text.replace('},{"name"', '},\n{"name"')

    text = dump(data)
    if len(text.encode("utf-8")) <= cap:
        return text
    data = json.loads(json.dumps(data))
    for width, keep in ((160, 3), (100, 1), (60, 1), (0, 0)):
        for row in data["suites"]:
            if "failing" in row:
                lines = [f for f in row["failing"] if not f.startswith("(+")]
                row["failing"] = [f[:width] for f in lines[:keep]] + ([f"(+{len(lines) - keep} more)"]
                                                                      if len(lines) > keep else [])
        text = dump(data)
        if len(text.encode("utf-8")) <= cap:
            return text
    rank = {NOT_RUN: 0, PASS: 1}
    order = sorted(range(len(data["suites"])), key=lambda i: (rank.get(data["suites"][i]["status"], 2), -i))
    dropped: list[dict] = []
    while len(text.encode("utf-8")) > cap and order:
        dropped.append(data["suites"][order.pop(0)])
        kept = [r for r in data["suites"] if all(r is not d for d in dropped)]
        by = {}
        for r in dropped:
            by[r["status"]] = by.get(r["status"], 0) + 1
        data2 = {**data, "suites": kept, "suites_omitted": {"count": len(dropped), "by_status": by}}
        text = dump(data2)
    if len(text.encode("utf-8")) > cap:
        data["code_line"] = data.get("code_line", "")[:200]
        text = dump({**data, "suites": [], "suites_omitted": {"count": len(data["suites"])}})
    return text


def evidence_groups(rows: list[Row], cfg: Config) -> list[tuple[str, str, list[Row]]]:
    """(group, file stem, its rows) for each file this run writes. A units group missing a unit suite is a PARTIAL
    file whose name no suite_map glob matches: a partial run never clears `units`."""
    out = []
    for group, stem in EVIDENCE_NAMES.items():
        mine = [r for r in rows if r.group == group and r.status != NOT_RUN]
        if not mine:
            continue
        if group == "units":
            ran = {r.name for r in mine}
            if not set(cfg.unit_names) <= ran:
                stem = "regression-quick" if cfg.lane == "quick" else "regression-partial"
            mine = mine + [r for r in rows if r.status == NOT_RUN]
        out.append((group, stem, mine))
    return out


def write_evidence(rows: list[Row], cfg: Config, watch: TreeWatch, verdict_line: str, headline: str, overall: str,
                   started: str, wall: float) -> list[tuple[Path, Path]]:
    written = []
    folder = cfg.evidence
    folder.mkdir(parents=True, exist_ok=True)
    date = cfg.date or time.strftime("%Y-%m-%d")
    for group, stem, mine in evidence_groups(rows, cfg):
        code = watch.lines.get(group, "unknown (no suite_map scope for this run)")
        path = folder / f"{date}-{stem}.txt"
        text = [f"AI PLAYER REGRESSION - {cfg.lane} lane, evidence group `{group}` (gates/run_regression.py, spec S4-1)",
                f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {code}", f"command: {cfg.command}",
                "Each section is one suite: the runner's typed status, then the suite's raw output (indented).", ""]
        for row in mine:
            if row.status == NOT_RUN:
                continue
            appendix = " (appendix: a revert driver with no suite of its own in suite_map.json)" if (
                group == "units" and row.name.startswith("revert_")) else ""
            text.append(f"== {row.name}: {row.word()} (exit {row.exit}, {row.seconds:.1f} s, "
                        f"{row.tests if row.tests is not None else '-'} {row.unit}"
                        f"{f', {row.shards} shards' if row.shards else ''}){appendix}")
            text += [f"   note: {row.note}"] if row.note else []
            text += [f"   failing: {f}" for f in row.failing[:3]]
            for title, raw in row.output:
                if title:
                    text.append(f"   -- {title}")
                text += [f"    | {l}" for l in raw.splitlines()]
            text.append("")
        text += [f"NOT-RUN {r.name}: {r.note}" for r in mine if r.status == NOT_RUN]
        text += ["", verdict_line, headline]
        whole = group == "units"
        chosen = rows if whole else mine
        g_overall = overall if whole else (PASS if all(r.status == PASS for r in mine)
                                           and not verdict_line.startswith("FROZEN TREE: FAIL") else FAIL)
        summary = {"schema": 1, "lane": cfg.lane, "started": started, "wall_s": round(wall, 1), "code_line": code,
                   "overall": g_overall, "suites": [r.summary() for r in chosen]}
        # (#28-evidence-identity) by identity: this run's own `covers:<suite>` line (its HEAD, label and digest), so a
        # clean run on a newer commit with a changed covered file archives the earlier commit's file instead of writing
        # over it; an "unknown (...)" line has no identity and always archives
        keep_earlier(path, folder=folder, repo=cfg.repo, code=code)
        path.write_text("\n".join(text) + "\n", encoding="utf-8")
        target = summary_of(path)
        # LF only and the newline inside the cap: the FILE is at most SUMMARY_CAP bytes on Windows too
        target.write_text(capped_summary(summary, SUMMARY_CAP - 1) + "\n", encoding="utf-8", newline="\n")
        written.append((path, target))
    return written


# --------------------------------------------------------------------------------------------------------- the CLI
def load_times() -> dict:
    try:
        return json.loads(TIMES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    lane = parser.add_mutually_exclusive_group()
    lane.add_argument("--quick", action="store_true", help="the fast unit suites only (the per-edit lane)")
    lane.add_argument("--full", action="store_true", help="every unit suite (sharded) and the six reverts (default)")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--evidence", action="store_true", help="write the evidence and summaries (--full always does)")
    parser.add_argument("--only", nargs="+", metavar="NAME", help="run only these suites of the lane")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="per-suite seconds (default 3600)")
    parser.add_argument("--list", action="store_true", help="print the lanes, the shard plan and the verdict regexes")
    args = parser.parse_args(argv)
    name = "quick" if args.quick else "full"
    known = all_suites()
    missing = sorted(set(QUICK) - {s.name for s in known})
    if missing:
        raise SystemExit(f"QUICK names suites that do not exist: {missing}")
    lane_suites = [s for s in known if s.name in QUICK] if name == "quick" else known
    times = load_times()
    if args.list:
        for s in known:
            print(f"{s.name:<26} {s.kind:<9} group {s.group:<20} {'quick+full' if s.name in QUICK else 'full'}"
                  f"{'  (sharded)' if s.sharded else ''}")
        try:
            for i, shard in enumerate(plan_shards(GATES / "test_check_purity.py", times.get("test_check_purity", {}),
                                                  args.workers, float(times.get("default_method_s", 2.0)))):
                print(f"test_check_purity shard {i + 1}: {shard}")
        except PlanError as why:
            print(f"test_check_purity would run UNSHARDED: {why}")
        for driver in GRADED_DRIVERS:
            print(f"{driver:<26} NOT-RUN: {GRADED}")
        for rule, pattern in verdict_rules().items():
            print(f"regex {rule:<28} {pattern.pattern}")
        return EXIT_PASS
    if args.only:
        unknown = [o for o in args.only if o not in {s.name for s in lane_suites}]
        if unknown:
            print(f"REGRESSION: REFUSED - not suites of the {name} lane: {unknown} (--list names them)")
            return EXIT_REFUSED
    chosen = [s for s in lane_suites if not args.only or s.name in args.only]
    not_run = [(d, GRADED) for d in GRADED_DRIVERS]
    not_run += [(s.name, "not in the --quick lane") for s in known if name == "quick" and s.name not in QUICK]
    not_run += [(s.name, "not named by --only") for s in lane_suites if s not in chosen]
    smap = json.loads(SUITE_MAP.read_text(encoding="utf-8"))
    groups = {"units"} if name == "quick" else set(EVIDENCE_NAMES)
    cfg = Config(lane=name, workers=args.workers, timeout=args.timeout, times=times,
                 evidence=EVIDENCE if (args.evidence or name == "full") else None,
                 scopes={g: (smap["suites"][g], smap.get("exclude", [])) for g in sorted(groups)},
                 command="py -3.12 ai_player/gates/run_regression.py " + " ".join(argv if argv is not None
                                                                                  else sys.argv[1:]))
    return run(chosen, not_run, cfg)


if __name__ == "__main__":
    sys.exit(main())
