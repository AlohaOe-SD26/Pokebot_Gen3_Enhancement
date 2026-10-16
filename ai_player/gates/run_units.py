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
(`check_lessons`) and the disk report (`disk_budget`)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
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
}


def digest() -> str:
    return line_digest(provenance(REPO)) or "unknown"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--suites", default=",".join(SUITES))
    parser.add_argument("--evidence", type=Path)
    # (build step 5.1, the step-5 verifier: the step-5 UNITS evidence carried step 4.1's title) the title names the step
    parser.add_argument("--title", default="AI PLAYER BUILD STEP 5.2 - THE STATIC GATE, THE UNIT SUITES AND THE SAFETY GATES")
    args = parser.parse_args()
    wanted = [s.strip() for s in args.suites.split(",") if s.strip()]
    unknown = [s for s in wanted if s not in SUITES]
    if unknown:
        print(f"unknown suites {unknown}: {list(SUITES)}")
        return 2
    code = provenance(REPO)
    tree = digest()
    # (build step 5.2, G1) the frozen-tree watch, started with the code line: checked after every suite, sealed at OVERALL
    frozen = watch(REPO, explicit=True)
    out = [args.title, f"code: {code}", "Each suite's START line names the digest it ran on (all the same as the code line "
                                         "above).", ""]
    ok_all = True
    for name in wanted:
        command, keep = SUITES[name]
        now = digest()
        started = time.strftime("%H:%M:%S")
        done = subprocess.run([sys.executable, *command], cwd=str(REPO), capture_output=True, timeout=3600,
                              env={**__import__("os").environ, "PYTHONUTF8": "1"})
        text = (done.stdout + done.stderr).decode("utf-8", "replace")
        lines = [l for l in text.splitlines() if l.strip()]
        if name.startswith("test_"):
            tail = [l for l in lines if l.startswith(("Ran ", "OK", "FAILED"))][-keep:]
        else:
            tail = lines[-keep:]
        still = frozen.check(f"after suite {name}")
        ok = done.returncode == 0 and now == tree and still
        ok_all &= ok
        out.append(f"== {name}: started {started} on sha256:{now}, exit {done.returncode} at {time.strftime('%H:%M:%S')}"
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
