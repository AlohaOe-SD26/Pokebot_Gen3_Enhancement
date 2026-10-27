"""MUTANT PROOF of build step 5.2's SAFETY GATES (G1-G7): each gate, broken in a COPY of the package, fails its predicted
tests of `gates/test_safety_gates.py`. Test side.

    py -3.12 ai_player/gates/revert_safety_gates.py [S1,S2] [--workers N] [--evidence PATH]   (exit 0 = every prediction held)

WHY (`08-MISTAKES.md` 2026-10-14: "for every new hook, write the mutant that deletes its CALL, not just its body"; CLAUDE.md
session rule 6: fault-test every gate): a gate whose tests still pass when the gate is broken guards nothing. Each mutant
below breaks ONE rule of a gate (or deletes the CALL that wires it into a driver) in a copy made like `revert_step5.py`'s
(`make_copy`: each anchor must occur exactly once), runs `test_safety_gates.py` from the copy (the project's documents from
this repository: `AI_PLAYER_TEST_SUPPORT_ROOT`), and checks that exactly the predicted tests fail. S0, the unchanged copy,
must pass every test. The real-driver tests carry their own nets (a broken refusal fails them; it never starts a run).
A guard that cannot be broken without starting a real sweep (rate_step5's `preflight` CALL deleted) is checked statically
by `WiringTests` instead, and is not a mutant here.
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
from ai_player.gates.provenance import keep_earlier, provenance, watch  # noqa: E402

TIMEOUT = 900
CAUGHT, CONTROL = "CAUGHT", "CONTROL"
PROV, LEDGER, RATE5, CENSUS = "gates/provenance.py", "gates/ledger.py", "gates/rate_step5.py", "gates/call_census.py"
FAIR, DISK, PRUNE, LESSONS = "gates/check_fairness.py", "gates/disk_budget.py", "gates/prune_evidence.py", \
    "gates/check_lessons.py"
T = "FrozenTreeTests."
L, C, F, D, E, LS, W = "LedgerTests.", "CallCensusTests.", "FairnessTests.", "DiskBudgetTests.", "EvidenceReaderTests.", \
    "LessonsTests.", "WiringTests."

#: name -> (prediction, the rule that is broken, [edits (file under ai_player/, old, new)], the tests that MUST fail)
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str]]] = {
    "S0": (CONTROL, "nothing: the unchanged copy", [], []),
    # ---- G1, the frozen-tree watch
    "S1": (CAUGHT, "G1: the watch never sees a move",
           [(PROV, "            if not (added or removed or changed or rewritten):\n                return True\n",
             "            if True:  # MUTANT S1\n                return True\n")],
           [T + "test_an_edit_mid_sweep_fails_the_verdict_and_stops_the_runs", T + "test_an_added_module_fails",
            T + "test_an_edit_undone_before_the_end_still_fails", T + "test_the_backstop_fails_a_driver_that_never_seals"]),
    "S2": (CAUGHT, "G1: the sweep's CHECK before each run deleted (rate_step5.run_one)",
           [(RATE5, "    if _TREE is not None and (_TREE.moved or not _TREE.check(f\"before run ",
             "    if False and (_TREE.moved or not _TREE.check(f\"before run ")],
           [W + "test_a_sweep_checks_before_and_after_every_run"]),
    "S3": (CAUGHT, "G1: keep_earlier no longer CALLS the backstop",
           [(PROV, "        _backstop(path)\n", "        pass  # MUTANT S3\n")],
           [T + "test_the_backstop_fails_a_driver_that_never_seals"]),
    # ---- G2, the seed + bounds ledger
    "S4": (CAUGHT, "G2: a graded run's numbers are not compared with the registered ones",
           [(LEDGER, "            if entry[\"bounds_sha256\"] != bounds:\n                raise Refused(f\"the numbers",
             "            if False:  # MUTANT S4\n                raise Refused(f\"the numbers")],
           [L + "test_a_bound_changed_after_registration_is_refused"]),
    "S5": (CAUGHT, "G2: a registration may overlap seeds already played",
           [(LEDGER, "        other = [e for e in entries if e[\"family\"] == family and _overlap(e, first, last) and e not in same]\n",
             "        other = []  # MUTANT S5\n")],
           [L + "test_a_registered_range_runs_once_with_its_own_numbers",
            L + "test_graded_runs_refuse_development_and_graded_seeds"]),
    "S6": (CAUGHT, "G2: --first-seed has its default 1 again",
           [(RATE5, "    parser.add_argument(\"--first-seed\", type=int, required=True)\n",
             "    parser.add_argument(\"--first-seed\", type=int, default=1)  # MUTANT S6\n")],
           [L + "test_the_real_driver_has_no_default_purpose_or_first_seed"]),
    # ---- G3, the call-site census
    "S7": (CAUGHT, "G3: any mutant whose anchor holds a site covers it (the call need not go)",
           [(CENSUS, "        if len(after) < len(before):\n            return name, \"deletes the call\"\n",
             "        if True:  # MUTANT S7\n            return name, \"deletes the call\"\n")],
           [C + "test_mutants_that_do_not_delete_the_call_cover_nothing"]),
    "S8": (CAUGHT, "G3: a mutant covers every site of its caller, not only the one its anchor holds",
           [(CENSUS, "            if at >= 0 and at <= site.start and site.end <= at + len(old):\n",
             "            if at >= 0:  # MUTANT S8\n")],
           [C + "test_a_mutant_covers_only_the_site_its_anchor_holds"]),
    "S9": (CAUGHT, "G3: an uncalled hook is not listed",
           [(CENSUS, "                if not sites:\n                    reason = waived(finding.callee, None, waivers)\n",
             "                if False:  # MUTANT S9\n                    reason = waived(finding.callee, None, waivers)\n")],
           [C + "test_an_uncalled_hook_fails_unless_waived_with_a_reason"]),
    # (build step 5.2, found by the census of 5.2's own code) a function nested inside an `if` of another was invisible
    "S23": (CAUGHT, "G3: the walk for functions stops at an `if` (a hook added inside a nested function escapes the census)",
            [(CENSUS, "                visit(child, name)\n            else:\n                visit(child, prefix)\n",
              "                visit(child, name)  # MUTANT S23\n")],
            [C + "test_a_site_in_a_function_nested_inside_an_if_can_be_covered"]),
    # ---- G4, the person-fair data door
    "S10": (CAUGHT, "G4: the flag door lets every read through",
            [(FAIR, "            if field is not None and (rel, here, field) not in doors:\n",
              "            if False:  # MUTANT S10\n")],
            [F + "test_an_errand_keyed_on_a_mark_is_refused", F + "test_a_flag_read_outside_the_door_is_refused"]),
    "S11": (CAUGHT, "G4: developer-only knowledge keys are read freely",
            [(FAIR, "            if key is not None and key in dev_keys:\n", "            if False:  # MUTANT S11\n")],
            [F + "test_a_coordinate_and_a_decomp_read_are_refused"]),
    "S12": (CAUGHT, "G4: an unclassified knowledge key passes",
            [(FAIR, "        unclassified = [shown(p) for p in paths if classify(p, schema) is None]\n",
              "        unclassified = []  # MUTANT S12\n")],
            [F + "test_an_unclassified_knowledge_key_fails_and_the_real_files_pass"]),
    "S13": (CAUGHT, "G4: docstrings and string statements are read as values (a MENTION fires)",
            [(FAIR, "        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):\n"
                    "            out.add(id(node.value))\n",
              "        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):\n"
              "            pass  # MUTANT S13\n")],
            [F + "test_mentions_never_fire"]),
    # ---- G5, the disk budget
    "S14": (CAUGHT, "G5: the budget refuses nothing",
            [(DISK, "    low = {drive: free for drive, free in drives.items() if free < min_free_gb}\n",
              "    low = {}  # MUTANT S14\n")],
            [D + "test_under_the_budget_a_sweep_is_refused", D + "test_the_real_sweep_refuses_to_start_and_writes_nothing"]),
    "S15": (CAUGHT, "G5: a sweep's failing runs are deleted too",
            [(DISK, "        kept = [f for f in existing if f.resolve() in failing_set or f in newest]\n",
              "        kept = [f for f in existing if f in newest]  # MUTANT S15\n")],
            [D + "test_a_sweeps_run_folders_are_deleted_but_the_failing_and_the_newest"]),
    "S16": (CAUGHT, "G5: a run folder counts as cited when its name is a PART of a cited name (CH2 inside CH2M)",
            [(DISK, "        elif (folder.name in names if re.fullmatch(_NAME, folder.name) else\n",
              "        elif (any(folder.name in n for n in names) if re.fullmatch(_NAME, folder.name) else  # MUTANT S16\n")],
            [D + "test_a_profiles_run_folders_are_pruned_by_the_policy"]),
    # ---- G6, one evidence reader
    "S17": (CAUGHT, "G6: the reader looks at the first 12 lines only (the old provenance reader)",
            [(PROV, "    for found in CODE_LINE.finditer(text):\n",
              "    for found in CODE_LINE.finditer(\"\\n\".join(text.splitlines()[:12])):  # MUTANT S17\n")],
            [E + "test_one_reader_finds_a_code_line_pushed_down_by_a_multi_line_command",
             E + "test_fault_the_old_12_line_reader_misses_it_or_reads_the_mention",
             E + "test_a_mention_inside_the_script_is_never_read"]),
    "S18": (CAUGHT, "G6: prune_evidence reads with its own 4000-character limit again",
            [(PRUNE, "    return file_digest(path)\n",
              "    return code_digest(path.read_text(encoding=\"utf-8\", errors=\"replace\")[:4000])  # MUTANT S18\n")],
            [E + "test_one_reader_finds_a_code_line_pushed_down_by_a_multi_line_command"]),
    # (the prediction CORRECTED in development, 2026-10-15: the first run listed a third test, which reads a script whose
    # mention names no digest, so it cannot catch this mutant; the two below did, as now predicted)
    "S19": (CAUGHT, "G6: a code line need not start its line (an indented MENTION is read)",
            [(PROV, "CODE_LINE = re.compile(r\"^(?:\\[[A-Z0-9-]+\\] *)?code: (?P<rest>.*)$\", re.M)\n",
              "CODE_LINE = re.compile(r\"^.*?code: (?P<rest>.*)$\", re.M)  # MUTANT S19\n")],
            [E + "test_one_reader_finds_a_code_line_pushed_down_by_a_multi_line_command",
             E + "test_a_mention_inside_the_script_is_never_read"]),
    # ---- G7, the lessons list
    "S20": (CAUGHT, "G7: a reference to a file that does not exist resolves",
            [(LESSONS, "    if not path.exists():\n        return f\"{file} does not exist\"\n",
              "    if False:  # MUTANT S20\n        return f\"{file} does not exist\"\n")],
            [LS + "test_a_lesson_naming_what_does_not_exist_fails"]),
    "S21": (CAUGHT, "G7: the Needs line's names (gates still to be built) are resolved too (a MENTION fires)",
            [(LESSONS, "            tokens = [t for t in TICKED.findall(fields.get(\"Enforced\", \"\")) if looks_like_reference(t)]\n",
              "            tokens = [t for t in TICKED.findall(fields.get(\"Enforced\", \"\") + fields.get(\"Needs\", \"\")) "
              "if looks_like_reference(t)]  # MUTANT S21\n")],
            [LS + "test_the_real_lessons_list_passes"]),
    "S22": (CAUGHT, "G7: an Origin quote is not looked for in its document",
            [(LESSONS, "            if _norm(quote[\"text\"]) not in cache[doc]:\n", "            if False:  # MUTANT S22\n")],
            [LS + "test_a_wrong_origin_a_gated_lesson_without_a_gate_and_a_prose_lesson_without_needs_fail"]),
}

DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_safety_gates
suite = unittest.defaultTestLoader.loadTestsFromModule(test_safety_gates)
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("test_safety_gates.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_safety_gates.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_step52_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    # (step 5.3 A1 lane fix) rate_step5.main() hashes every file in HASHED_FILES before it refuses a run, and one of them
    # (the framework's map_data.py) lives outside the package: copy each such file, read from the list itself, so a file
    # added to the hash later cannot make the unchanged copy (S0) error again
    from ai_player.gates.rate_step5 import HASHED_FILES
    for relative in HASHED_FILES:
        if not relative.startswith("ai_player/"):
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / relative, root / relative)
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_safety_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_safety_tests.py")], cwd=str(root), env=env,
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
    # (KI-123, 2026-10-26) a filter naming no mutant (a typo, `--help`) REFUSES before anything runs or is written
    from ai_player.gates.provenance import unknown_mutants

    unknown = unknown_mutants(sys.argv[1:], MUTANTS, ("--workers", "--evidence"))
    if unknown:
        print(f"REFUSED: no mutant named {unknown} ({len(MUTANTS)} exist; usage: revert_safety_gates.py "
              f"[NAME[,NAME...]] [--workers N] [--evidence FILE]); nothing was run")
        return 2
    argv = list(sys.argv[1:])
    workers, evidence = 1, None
    if "--workers" in argv:
        at = argv.index("--workers")
        workers = max(1, int(argv[at + 1]))
        del argv[at:at + 2]
    if "--evidence" in argv:
        at = argv.index("--evidence")
        evidence = Path(argv[at + 1])
        del argv[at:at + 2]
    only = set(argv[0].split(",")) if argv else None
    chosen = [(name, spec) for name, spec in MUTANTS.items() if only is None or name in only]
    out = ["AI PLAYER BUILD STEP 5.2 - MUTANT PROOF OF THE SAFETY GATES (gates/revert_safety_gates.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {provenance(REPO)}",
           "Each mutant breaks ONE rule of a gate in a copy; CAUGHT = exactly its predicted tests of "
           "gates/test_safety_gates.py fail (and others may too: said).", ""]
    tree = watch(REPO, explicit=True)  # (G1) checked before each copy, sealed at OVERALL

    def attempt(item):
        if tree.moved or not tree.check(f"before mutant {item[0]}"):
            return None, f"NOT RUN: the tree changed mid-run ({tree.moves[0][:300]})", None
        root = make_copy(item[1][2])
        try:
            return run(root) + (root,)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(attempt, chosen))
    ok_all, caught = True, 0
    for (name, (prediction, what, _, expected)), (result, raw, root) in zip(chosen, results):
        if result is None:
            ok, line = False, f"[{name}] NO RESULT: {raw[-1500:]}"
        else:
            bad = result["bad"]
            ran_copy = root is not None and root.name in result["module"]
            if prediction == CONTROL:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] CONTROL, the unchanged copy: {result['ran']} tests, failing {sorted(bad) or 'none'} "
                        f"(ran the copy: {ran_copy}) -> {'PASS' if ok else 'FAIL'}")
            else:
                hit = [t for t in expected if any(b == t or b.startswith((t + " (", t + " [")) for b in bad)]
                ok = ran_copy and hit == expected
                caught += ok
                others = sorted(b for b in bad if not any(b == t or b.startswith((t + " (", t + " [")) for t in expected))
                line = (f"[{name}] BROKEN: {what}. Predicted CAUGHT by {expected}. The copy ran {result['ran']} tests "
                        f"({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {dict(sorted(bad.items()))}"
                        f"{'; beyond the prediction: ' + str(others) if others else ''} -> "
                        f"{'CAUGHT' if ok else 'NOT CAUGHT'}")
        ok_all &= ok
        print(line, flush=True)
        out.append(line)
    verdict, frozen_line = tree.seal("PASS" if ok_all else "FAIL")
    summary = f"{caught} mutants CAUGHT as predicted, of {len([c for c in chosen if c[1][0] == CAUGHT])}"
    out += ["", summary, frozen_line, f"OVERALL: {verdict}"]
    print(summary)
    print(frozen_line)
    print(f"OVERALL: {verdict}")
    if evidence is not None:
        keep_earlier(evidence)
        evidence.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"evidence: {evidence}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
