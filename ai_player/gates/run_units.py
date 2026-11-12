"""TEST SIDE: the static gate and the unit suites on ONE tree, with the evidence file the README cites (step 4.1 round 3).

    py -3.12 ai_player/gates/run_units.py [--suites check_purity,test_battle,...] [--evidence PATH]

WHY (the step-4.1 verifier's second round: "Evidence-policy order broken ... 12 top-level evidence files ... were
overwritten"): the units' evidence (`<date>-step4-UNITS.txt`) was written by a shell redirect, which no guard of the gates
could see. This runner writes it through `provenance.keep_earlier` like every other evidence writer, and names on each
suite's START line the digest the suite ran on (all must equal the file's code line: a suite run on another tree is said).
Each suite runs in its own process; its exit code and its last lines are quoted. Exit 0 = every suite exit 0 on the same
tree. (Build step 5.2) The frozen-tree watch (`provenance.FrozenTree`, G1) is checked after every suite and seals OVERALL;
the safety gates run as suites: their fault tests (`test_safety_gates`), the seed ledger's form (`ledger_check`), the
call-site census against HEAD (`call_census`), the person-fair data door (`check_fairness`), the lessons list
(`check_lessons`) and the disk report (`disk_budget`).

(Spec S4-1, recon Q4) A HUNG SUITE NO LONGER KILLS THE RUNNER. `subprocess.run(..., timeout=3600)` raised
`TimeoutExpired` out of the loop, so a hung suite ended the runner with no evidence written at all, and on Windows the
kill it made reached only the direct child (a grandchild holding the output pipe could keep it waiting). `run_command`
(ONE runner: it hands each command to `run_regression.run_command`) writes the output to temporary files instead of
pipes, and on a timeout kills EVERY process the suite started (Windows: a Job Object, which also reaches a grandchild
whose parent already exited; elsewhere its process group); the suite is recorded `TIMEOUT` (a FAIL) and the run goes on
to its verdict and its evidence. `--timeout` sets the per-suite limit (default 3600 s)."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.provenance import keep_earlier, line_digest, provenance, watch  # noqa: E402

GATES = Path(__file__).resolve().parent
#: name -> (the command's arguments after the interpreter, how many of its last lines are quoted)
SUITES: dict[str, tuple[list[str], int]] = {
    "check_purity": ([str(GATES / "check_purity.py")], 1),
    "test_check_purity": ([str(GATES / "test_check_purity.py")], 2),
    "test_host": ([str(GATES / "test_host.py")], 2),
    "test_eyes": ([str(GATES / "test_eyes.py")], 2),
    "test_hands": ([str(GATES / "test_hands.py")], 2),
    "test_world": ([str(GATES / "test_world.py")], 2),
    "test_battle": ([str(GATES / "test_battle.py")], 2),
    "test_evidence": ([str(GATES / "test_evidence.py")], 2),
    "extract_knowledge_check": ([str(GATES / "extract_knowledge.py"), "--check"], 3),
    # build step 5: the goal manager's unit tests and the milestone table against its extractor
    "test_goals": ([str(GATES / "test_goals.py")], 2),
    "extract_milestones_check": ([str(GATES / "extract_milestones.py"), "--check"], 1),
    # build step 5.2, the safety gates: their fault tests (G1-G7), and each gate on the tree as it stands
    "test_safety_gates": ([str(GATES / "test_safety_gates.py")], 2),
    "ledger_check": ([str(GATES / "ledger.py"), "--check"], 1),
    "call_census": ([str(GATES / "call_census.py")], 2),
    "check_fairness": ([str(GATES / "check_fairness.py")], 2),
    "check_lessons": ([str(GATES / "check_lessons.py")], 2),
    "disk_budget": ([str(GATES / "disk_budget.py")], 2),
    # spec S4-1: the regression runner's own fault tests (fake suites in temp folders; under 5 s)
    "test_run_regression": ([str(GATES / "test_run_regression.py")], 2),
    # spec S3-4 slice 1 (KB2): the world files' extractor, its independent verifier and W1-W8 (about 10 s; the pinned
    # decomp clone is required: without it every test ERRORS, never a silent pass)
    "test_kb2": ([str(GATES / "test_kb2.py")], 2),
    # (P11-1, 2026-11-11) the way through a dark cave: the loader, the explorer's way, the offline model A/B (about 40 s)
    "test_ways": ([str(GATES / "test_ways.py")], 2),
    # build step 5.3, stage A1: the typed checks' unit tests (A1-1 to A1-4 and the A1 fix round; offline, about 7 s). Its
    # GraderImportTests.test_the_tree_as_it_stands_passes runs the G-3 rule (no grader takes a value from the AI's code)
    # on the tree as it stands, so this suite enforces G-3 too
    "test_step53_a1": ([str(GATES / "test_step53_a1.py")], 2),
    # build step 5.3, stage A2: the A1 carry-overs and the five game reads' logic (offline, about 2 s; its
    # LiveKnownAnswerTests skip unless POKEBOT_A2_LIVE=1, which needs the ROM)
    "test_step53_a2": ([str(GATES / "test_step53_a2.py")], 2),
    # build step 5.3, the re-sourcing build (builder 1): the re-sourced checks graded by the game or the harness alone,
    # each with its fault and control, and the development-only re-grade (offline, under 1 s)
    "test_step53_rs": ([str(GATES / "test_step53_rs.py")], 2),
    # build step 5.3, stage A2 (builder 2): the measurement of a kept development sweep (`measure_step5.py`) on synthetic
    # run folders with known answers, its decision table over every b1_debt.json id, and the G-3 rule for it (offline,
    # under 1 s)
    "test_measure_step5": ([str(GATES / "test_measure_step5.py")], 2),
    # build step 5.3, stage A1-2: the G-3 gate's own CLI (the two graders import no AI value, directly or through a
    # gates module; under 2 s)
    "check_grader_imports": ([str(GATES / "check_grader_imports.py")], 1),
    # R1 + R2 (build spec 2026-10-29 section 7): saving, continuing and the memory file (offline, about 7 s; its host-eyes
    # tests need the framework: `AI_PLAYER_TEST_SUPPORT_ROOT` names its folder when this tree has none), and the paths
    # gate (DP1: no machine path in the AI's code but its one resolver; under 1 s)
    "test_saving": ([str(GATES / "test_saving.py")], 2),
    "check_paths": ([str(GATES / "check_paths.py")], 1),
    # KI-128/KI-129's graded held-out driver (2026-10-31): every grader's FAULT and CONTROL on planted rows (offline,
    # about 4 s)
    "test_live_ki128": ([str(GATES / "test_live_ki128.py")], 2),
    # the anchor gate (08-MISTAKES 2026-11-09: a round broke revert_step3's W64 anchor and only the full lane saw it): every
    # mutant runner's anchors hit exactly once, no mutant run (under 1 s), and its CONTROL + FAULT tests (about 3 s)
    "check_anchors": ([str(GATES / "check_anchors.py")], 1),
    "test_check_anchors": ([str(GATES / "test_check_anchors.py")], 2),
}


DEFAULT_TIMEOUT = 3600


@dataclass
class Ran:
    """One finished command: its exit code (None when it timed out or never started), its stdout then its stderr, its
    wall seconds, whether it timed out (its process tree was killed), and why it could not start (None: it started)."""
    code: int | None
    text: str
    seconds: float
    timed_out: bool = False
    error: str | None = None


def kill_tree(pid: int) -> None:
    """Kill a process AND every process it started (Windows: `taskkill /T /F`; elsewhere its process group)."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, timeout=60)
        else:
            os.killpg(pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass


def run_command(argv: list[str], cwd: Path, timeout: float, env: dict | None = None) -> Ran:
    """Run `argv` to its end or to `timeout` seconds through the ONE suite runner, `run_regression.run_command`.
    (S4-1 verify round 2) This file used to keep its own copy, which killed with `taskkill /T` and so missed a
    grandchild whose parent had already exited (verifier F5); two runners meant one of them could keep the old gap.
    The import is lazy because run_regression imports this module (for `Ran` and `kill_tree`)."""
    from ai_player.gates.run_regression import run_command as shared_runner
    return shared_runner(argv, cwd, timeout, env)


def digest() -> str:
    return line_digest(provenance(REPO)) or "unknown"


def main(argv: list[str] | None = None, suites: dict[str, tuple[list[str], int]] | None = None) -> int:
    """`suites` replaces SUITES (the tests run fake suites through the real loop)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    table = SUITES if suites is None else suites
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--suites", default=",".join(table))
    parser.add_argument("--evidence", type=Path)
    # (build step 5.1, the step-5 verifier: the step-5 UNITS evidence carried step 4.1's title) the title names the step
    parser.add_argument("--title", default="AI PLAYER BUILD STEP 5.2 - THE STATIC GATE, THE UNIT SUITES AND THE SAFETY GATES")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="per-suite seconds (default 3600)")
    args = parser.parse_args(argv)
    wanted = [s.strip() for s in args.suites.split(",") if s.strip()]
    unknown = [s for s in wanted if s not in table]
    if unknown:
        print(f"unknown suites {unknown}: {list(table)}")
        return 2
    code = provenance(REPO)
    tree = digest()
    # (build step 5.2, G1) the frozen-tree watch, started with the code line: checked after every suite, sealed at OVERALL
    frozen = watch(REPO, explicit=True)
    out = [args.title, f"code: {code}", "Each suite's START line names the digest it ran on (all the same as the code line "
                                         "above).", ""]
    ok_all = True
    for name in wanted:
        command, keep = table[name]
        now = digest()
        started = time.strftime("%H:%M:%S")
        done = run_command([sys.executable, *command], REPO, args.timeout, env={**os.environ, "PYTHONUTF8": "1"})
        text = done.text
        lines = [l for l in text.splitlines() if l.strip()]
        if name.startswith("test_"):
            tail = [l for l in lines if l.startswith(("Ran ", "OK", "FAILED"))][-keep:]
        else:
            tail = lines[-keep:]
        if done.timed_out:
            # (spec S4-1) recorded and the run goes on: the old `subprocess.run` raised here and wrote no evidence
            tail = [f"TIMEOUT after {args.timeout:g} s: the suite's process tree was killed"] + lines[-keep:]
        elif done.error:
            tail = [f"COULD NOT START: {done.error}"]
        still = frozen.check(f"after suite {name}")
        ok = done.code == 0 and now == tree and still
        ok_all &= ok
        out.append(f"== {name}: started {started} on sha256:{now}, "
                   f"{'TIMEOUT' if done.timed_out else f'exit {done.code}'} at {time.strftime('%H:%M:%S')}"
                   f"{'' if now == tree else ' (ANOTHER TREE than the code line)'}"
                   f"{'' if still else ' (THE TREE CHANGED while it ran: ' + frozen.moves[-1][:200] + ')'}")
        out += [f"   {line}" for line in tail]
        print("\n".join(out[-(len(tail) + 1):]), flush=True)
    verdict, frozen_line = frozen.seal("PASS" if ok_all else "FAIL")
    ok_all = verdict == "PASS"
    out += ["", frozen_line, f"OVERALL: {'PASS (every suite exit 0)' if ok_all else 'FAIL'}"]
    print(frozen_line)
    print(out[-1])
    if args.evidence is not None:
        keep_earlier(args.evidence)
        args.evidence.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
