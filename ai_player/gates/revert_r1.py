"""MUTANT PROOF of R1 + R2 (the AI saves like a person, continues after a kill, and its memory survives; build spec
`PROJECT KNOWLEDGE/ai-research-notes/2026-10-29-R1R2-BUILD-SPEC.md` section 6): each rule of the REAL code, broken in a COPY
of the package, fails its PREDICTED tests, or the run says so.

    py -3.12 ai_player/gates/revert_r1.py [NAME,NAME] [--workers N] [--evidence-tag TAG]    (exit 0 = every prediction held)

The mechanism is `gates/revert_step5.py`'s (CLAUDE.md session discipline rule 6: a fault switch shows a test CAN fail, a
mutant shows the RULE in the real code carries weight): copy the package (no states, no evidence), apply ONE mutant's edits
(each anchor must occur exactly once), run the mutant's SUITES from the copy (`DEFAULT_SUITES`: `test_saving.py` and
`test_goals.py`; a mutant of the purity gate, the fairness gate or the controller names its own test), and check the
prediction: CAUGHT = the run has failing tests and EVERY predicted test is among them. The unchanged copy (R0) must pass
every suite any mutant runs. A mutant whose predicted list is empty is CAUGHT by any failing test of its suites.

THE MUTANTS, three kinds:
  * the spec's (section 6), hand-written below (`MUTANTS`): the launcher and the host (S27, S33-S37, S39, L*), the purity
    gate (S40), the fairness gate (S46), the options (S35b);
  * the build's earlier stages' (stages 1-3: S1-S26, S28-S32, S38, S41-S45, R3, X*, M*, N*), whose anchors and
    predictions were proven in those stages' scratch scripts, kept in `revert_r1_mutants.json` (`origin` says which);
  * the CALL-SITE CENSUS's (`gates/call_census.py`, LESSONS PF-2: "for every new hook, write the mutant that deletes its
    CALL"; orchestrator ruling 4: R1's census findings are closed by mutants, never by waivers): one mutant per call
    site of an R1 function, each DELETING that one call (a statement call becomes `pass`, a value `None`, a reference
    `None`), kept in `revert_r1_mutants.json` with the site it covers (`site`). Their predicted tests were RECORDED from
    their first run (the tests that failed then), so a later run proves the same tests still catch them.
`gates/call_census.py` reads every mutant here (`MUTANT_SOURCES`). Evidence: `ai_player/evidence/<date>-r1-REVERT.txt`.

THE ENVIRONMENT: `test_saving.py`'s host-eyes tests import the framework (`mgba`), which a worktree does not have:
`AI_PLAYER_TEST_SUPPORT_ROOT` (the folder holding `sandbox-pokebot/`) is kept from the environment when it is set, and is
this repository otherwise (as `revert_step5.py` sets it).
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
from ai_player.gates.provenance import keep_earlier, provenance  # noqa: E402

EVIDENCE = REPO / "ai_player" / "evidence"
DATA = Path(__file__).resolve().parent / "revert_r1_mutants.json"
TIMEOUT = 900
CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"
DEFAULT_SUITES = ("test_saving", "test_goals")
LAUNCHER, MAIN, OPTIONS, CONTROLLER = "host/launcher.py", "__main__.py", "options.py", "host/controller.py"
PURITY, FAIRNESS = "gates/check_purity.py", "gates/check_fairness.py"
PURITY_TEST = "test_check_purity:PlayLoopExitTests"
FAIRNESS_TEST = "test_safety_gates:FairnessTests"
HOST_TEST = "test_host:ControllerTogetherTests"
LCT = "LauncherContinueTests."

#: name -> (prediction, the rule that is broken, [edits (file, anchor, replacement)], [tests that MUST fail] or the reason
#: (REDUNDANT), the suites it runs). The spec's hand-written mutants; `revert_r1_mutants.json` adds the rest (`_load`).
MUTANTS: dict[str, tuple] = {
    "R0": (CONTROL, "nothing: the unchanged copy", [], [], DEFAULT_SUITES + (PURITY_TEST, FAIRNESS_TEST, HOST_TEST)),
    # ---------------------------------------------------------------- the launcher and the host (spec section 6)
    "S27": (CAUGHT, "`--continue` keeps the .ss1 (also the live proof's LAUNCH-OLD)",
            [(LAUNCHER, "        if had:\n            dropped.unlink()\n", "        if False:\n            dropped.unlink()\n")],
            [LCT + "test_continue_removes_the_ss1_and_keeps_the_sav", LCT + "test_the_cart_is_told"], ("test_saving",)),
    "S33": (CAUGHT, "the end classes collapsed to the draft's \"no chosen end line -> allowed\" (findings M1, M2)",
            [(LAUNCHER, "    session = book.last_session()\n    if session is None:\n"
                        "        return \"UNKNOWN\", \"the memory file names no session\", False\n",
              "    session = book.last_session()\n    if session is None:\n"
              "        return \"UNKNOWN\", \"the memory file names no session\", False\n"
              "    drafted = book.end_of(session[\"n\"])  # MUTANT S33\n"
              "    if drafted is None or not drafted.get(\"chosen\") or drafted.get(\"at_save\"):\n"
              "        return \"KILLED\", \"MUTANT S33\", True\n"
              "    return \"CHOSEN\", \"MUTANT S33\", False\n")],
            [LCT + "test_the_end_classes"], ("test_saving",)),
    "S34": (CAUGHT, "the launcher's `launch_end` line not written (finding M2)",
            [(MAIN, "        record_launch(game, run_dir, result, read_verdict(run_dir))\n", "        pass  # MUTANT S34\n")],
            [LCT + "test_every_run_gets_the_memory_path_and_the_cart"], ("test_saving",)),
    "S35": (CAUGHT, "`AI_PLAYER_WORLD` accepted by the launcher in continue mode (finding m4)",
            [(MAIN, "            if os.environ.get(ENV_WORLD, \"\").strip():\n", "            if False:  # MUTANT S35\n")],
            [LCT + "test_continue_refused_with_a_world_file_set"], ("test_saving",)),
    "S35b": (CAUGHT, "the brain's options accept a world file with a continue (D19)",
             [(OPTIONS, "        if self.continue_game and self.world_in is not None:\n",
               "        if False:  # MUTANT S35b\n")],
             [LCT + "test_continue_refused_with_a_world_file_set"], ("test_saving",)),
    "S36": (CAUGHT, "`--fresh` DELETES the memory instead of archiving it (D10)",
            [(LAUNCHER, "    archived = archive_memory(game) if game is not None else []\n",
              "    archived = [p.unlink() or p.name for p in (game.memory_jsonl, game.launches_jsonl) if p.exists()] "
              "if game is not None else []  # MUTANT S36\n")],
            [LCT + "test_fresh_archives_the_memory"], ("test_saving",)),
    "S37": (CAUGHT, "a start with no flag allowed on a game that has a memory file (finding F8)",
            [(LAUNCHER, "        if game is not None and game.memory_jsonl.exists():\n", "        if False:  # MUTANT S37\n")],
            [LCT + "test_no_flag_start_refused_when_memory_exists"], ("test_saving",)),
    "S39": (CAUGHT, "the controller allows START or SELECT with another button (finding G8)",
            [(CONTROLLER, "        if len(down) > 1 and down & _ALONE:\n", "        if False:  # MUTANT S39\n")],
            ["ControllerTogetherTests.test_start_or_select_never_with_another_button"], (HOST_TEST,)),
    "S40": (CAUGHT, "the purity gate allows `sys.exit` in brain/ (finding M2)",
            [(PURITY, "            \"exit\": frozenset({LIFECYCLE}),\n", "            \"exit\": ANY_FILE,  # MUTANT S40\n")],
            ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    "S40b": (CAUGHT, "the purity gate allows `exit`, `quit`, `SystemExit` and `KeyboardInterrupt` in the play loop",
             [(PURITY, "        if name in PLAY_LOOP_EXIT_NAMES and isinstance(node.ctx, ast.Load) and in_play_loop(self.key):\n",
               "        if False:  # MUTANT S40b\n")],
             ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    "S46": (CAUGHT, "the play time read anywhere in the deciding code (D18: RULE C's door not asked)",
            [(FAIRNESS, "                if door is None:\n", "                if False:  # MUTANT S46\n")],
            ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46b": (CAUGHT, "a stale play-time door passes (RULE C's stale check deleted)",
             [(FAIRNESS, "        if (\"time\", file, function) not in used:\n", "        if False:  # MUTANT S46b\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    # ---------------------------------------------------------------- the launcher's other guards (this stage's own)
    "L1": (CAUGHT, "a NEWER launches.jsonl accepted",
           [(LAUNCHER, "            if version > LAUNCHES_SCHEMA:\n", "            if False:  # MUTANT L1\n")],
           [LCT + "test_a_newer_memory_is_refused_byte_identical"], ("test_saving",)),
    "L2": (CAUGHT, "the launcher's hard kill not recorded as one",
           [(LAUNCHER, "            \"hard_kill\": bool(result.killed and not result.interrupted), "
                       "\"interrupted\": bool(result.interrupted),\n",
             "            \"hard_kill\": False, \"interrupted\": bool(result.interrupted),  # MUTANT L2\n")],
           [LCT + "test_the_launcher_writes_its_launch_end_line"], ("test_saving",)),
    "L3": (CAUGHT, "the cart is never told (every run `kept`, D17)",
           [(MAIN, "    env[ENV_CART] = \"continued\" if continuing else (\"empty\" if args.fresh or args.state else \"kept\")\n",
             "    env[ENV_CART] = \"kept\"  # MUTANT L3\n")],
           [LCT + "test_every_run_gets_the_memory_path_and_the_cart", LCT + "test_the_cart_is_told"], ("test_saving",)),
    "L4": (CAUGHT, "an inherited `AI_PLAYER_CONTINUE` reaches a run that is not a continue",
           [(MAIN, "    env.pop(ENV_CONTINUE, None)\n", "    pass  # MUTANT L4\n")],
           [LCT + "test_the_cart_is_told"], ("test_saving",)),
    "L5": (CAUGHT, "`--continue` without a cartridge save allowed (T7)",
           [(LAUNCHER, "        if not cart.is_file() or cart.stat().st_size == 0:\n", "        if False:  # MUTANT L5\n")],
           [LCT + "test_continue_refused_without_a_sav"], ("test_saving",)),
    "L6": (CAUGHT, "`--continue` on a profile ai_player did not create",
           [(LAUNCHER, "        if not (profile_dir / PROFILE_MARKER).is_file():\n            raise LaunchError(f\"refusing to "
                       "continue",
             "        if False:  # MUTANT L6\n            raise LaunchError(f\"refusing to continue")],
           [LCT + "test_continue_refused_on_a_foreign_profile"], ("test_saving",)),
    "L7": (CAUGHT, "the end class's refusal ignored by `memory_check` (RULING 52 in prose only)",
           [(LAUNCHER, "    if not allowed:\n        return ContinueCheck(False,",
             "    if False:  # MUTANT L7\n        return ContinueCheck(False,")],
           [LCT + "test_the_end_classes", LCT + "test_a_chosen_end_is_refused_by_the_cli"], ("test_saving",)),
    "L8": (CAUGHT, "the CLI starts a refused continue",
           [(MAIN, "            if not check.ok:\n", "            if False:  # MUTANT L8\n")],
           [LCT + "test_a_chosen_end_is_refused_by_the_cli"], ("test_saving",)),
    "L9": (CAUGHT, "a memory file with no save line can be continued",
           [(LAUNCHER, "    if newest is None:\n        return ContinueCheck(False, \"the memory file holds no save line",
             "    if False:  # MUTANT L9\n        return ContinueCheck(False, \"the memory file holds no save line")],
           [LCT + "test_continue_refused_without_memory"], ("test_saving",)),
    "L10": (CAUGHT, "a CHOSEN or BUDGET end with no `end` line allowed (fail open)",
            [(LAUNCHER, "    if end is None:\n        return (kind, f\"session {session['n']} ended '{reason}' with no end line",
              "    if False:  # MUTANT L10\n        return (kind, f\"session {session['n']} ended '{reason}' with no end line")],
            [LCT + "test_the_end_classes"], ("test_saving",)),
    # ---------------------------------------------------------------- the fix round (the adversarial review's R-1, R-2, R-4)
    "FX1": (CAUGHT, "R-1: a save's memory line built from the policy's state BEFORE the save (the save not in it)",
            [("mode.py", "        goals = goals_part(replace(manager.memory, **saving))\n",
              "        goals = goals_part(manager.memory)  # MUTANT FX1\n")],
            ["PlayLoopTests.test_r1_a_continue_from_a_leader_save_makes_no_second_save_before_the_talk"], ("test_goals",)),
    "FX2": (CAUGHT, "R-2: a continue stopped before its restore still a CHOSEN end",
            [("game_memory.py", "    held = bool(stopped_before_restore) and text.startswith(\"stuck:\")\n",
              "    held = False  # MUTANT FX2\n")],
            ["R1PlayTests.test_r1_a_continue_that_stops_on_a_bound_is_not_a_chosen_end",
             LCT + "test_a_continue_that_stopped_before_its_restore_is_looked_through"], DEFAULT_SUITES),
    "FX3": (CAUGHT, "R-2: the launcher never looks through a continue that stopped before its restore",
            [(LAUNCHER, "        if kind != \"CHOSEN\" or earlier is None or not _stopped_before_restore(book, session, reason):\n",
              "        if True:  # MUTANT FX3\n")],
            [LCT + "test_a_continue_that_stopped_before_its_restore_is_looked_through",
             "R1PlayTests.test_r1_a_continue_that_stops_on_a_bound_is_not_a_chosen_end"], DEFAULT_SUITES),
    "FX4": (CAUGHT, "R-2: the look-through ignores a session that played after its line",
            [(LAUNCHER, "    return not any(line[\"kind\"] in (\"save\", \"lost\") for line in book.lines[at + 1:])\n",
              "    return True  # MUTANT FX4\n")],
            [LCT + "test_a_continue_that_stopped_before_its_restore_is_looked_through"], ("test_saving",)),
    "FX5": (CAUGHT, "R-2: the look-through ignores the host's own record of the end",
            [(LAUNCHER, "    texts = [str(reason or \"\"), str(end.get(\"reason\") or \"\")]\n",
              "    texts = [str(end.get(\"reason\") or \"\")]  # MUTANT FX5\n")],
            [LCT + "test_a_continue_that_stopped_before_its_restore_is_looked_through"], ("test_saving",)),
    "FX6": (CAUGHT, "R-2: the spec's own stop (the save gone) marked retryable",
            [("skills/saving.py", "        return _stopped(hands, f\"the save is gone: {gone}\", page_words, page_kind)\n",
              "        return _stopped(hands, f\"the save is gone: {gone}\", page_words, page_kind, retry=True)  # MUTANT FX6\n")],
            ["CensusSiteTests.test_only_a_bound_or_a_failed_read_may_retry"], ("test_saving",)),
    "FX7": (CAUGHT, "R-4 (spec T4): save goals left in the intent mix's total",
            [("gates/rate_step5.py", "    spans = [s for s in every if s[\"kind\"] != SAVE_KIND]\n",
              "    spans = list(every)  # MUTANT FX7\n")],
            ["SecondRoundTests.test_a_save_goal_is_out_of_the_errand_share"], ("test_goals",)),
}


def _load() -> None:
    """The stage and census mutants of `revert_r1_mutants.json` (a missing file adds none: the census then says so)."""
    if not DATA.is_file():
        return
    for entry in json.loads(DATA.read_text(encoding="utf-8")).get("mutants", []):
        if entry["name"] in MUTANTS:
            raise SystemExit(f"revert_r1: mutant {entry['name']} is defined twice")
        what = entry["what"] + (f" [covers {entry['site']}]" if entry.get("site") else "")
        MUTANTS[entry["name"]] = (entry.get("prediction", CAUGHT), what, [tuple(e) for e in entry["edits"]],
                                  list(entry.get("expected") or []), tuple(entry.get("suites") or DEFAULT_SUITES))


_load()

DRIVER = '''
import importlib, json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
suites = json.loads(sys.argv[1])
loader = unittest.defaultTestLoader
tests = unittest.TestSuite()
files = []
for entry in suites:
    name, _, cls = entry.partition(":")
    module = importlib.import_module("ai_player.gates." + name)
    files.append(module.__file__)
    tests.addTests(loader.loadTestsFromTestCase(getattr(module, cls)) if cls else loader.loadTestsFromModule(module))
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(tests)
bad = {t.id().replace("ai_player.gates.", "", 1): kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors))
       for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "modules": files}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_r1_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            shutil.rmtree(root, ignore_errors=True)
            raise ValueError(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old[:160]!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_r1_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path, suites: tuple[str, ...]) -> tuple[dict | None, str]:
    support = os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or str(REPO)
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": support, "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_r1_tests.py"), json.dumps(list(suites))], cwd=str(root),
                              env=env, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as error:
        return None, f"TIMEOUT after {TIMEOUT}s: {error}"
    raw = done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")
    for line in raw.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):]), raw
    return None, raw


def _hit(bad: dict, test: str) -> bool:
    """Is the predicted `test` ("test", "Class.test" or "module.Class.test") among the failing ids ("module.Class.test",
    and a failing subTest's id has its parameters after a space)?"""
    return any(b == test or b.endswith("." + test) or b.startswith(test + " ") or ("." + test + " ") in b for b in bad)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    from ai_player.gates.provenance import snapshot_tree, unknown_mutants, watch

    unknown = unknown_mutants(sys.argv[1:], MUTANTS, ("--workers", "--evidence-tag"))
    if unknown:
        print(f"REFUSED: no mutant named {unknown} ({len(MUTANTS)} exist; usage: revert_r1.py [NAME[,NAME...]] "
              f"[--workers N] [--evidence-tag TAG]); nothing was run")
        return 2
    out = ["AI PLAYER R1 + R2 - MUTANT PROOF OF SAVING, CONTINUING AND THE MEMORY FILE (gates/revert_r1.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {provenance(REPO)}", f"tree kept: {snapshot_tree(REPO)}",
           "Each mutant breaks ONE rule (or deletes ONE call the census lists) in a copy; CAUGHT = the run fails and every "
           "predicted test is among the failing ones.", ""]
    argv = list(sys.argv[1:])
    workers = 6  # its ~420 mutants each run two suites (about 10 s): one at a time would take over an hour
    if "--workers" in argv:
        at = argv.index("--workers")
        workers = max(1, int(argv[at + 1]))
        del argv[at:at + 2]
    tag = "r1"
    if "--evidence-tag" in argv:
        at = argv.index("--evidence-tag")
        tag = argv[at + 1]
        del argv[at:at + 2]
    only = set(argv[0].split(",")) if argv else None
    chosen = [(name, spec) for name, spec in MUTANTS.items() if only is None or name in only]
    tree = watch(REPO, explicit=True)

    def attempt(item):
        if tree.moved or not tree.check(f"before mutant {item[0]}"):
            return None, f"NOT RUN: the tree changed mid-run ({tree.moves[0][:300]})", None
        try:
            root = make_copy(item[1][2])
        except ValueError as error:
            return None, f"NOT APPLIED: {error}", None
        try:
            return run(root, item[1][4]) + (root,)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(attempt, chosen))
    ok_all = True
    counts = {CAUGHT: 0, REDUNDANT: 0}
    for (name, (prediction, what, edits, expected, suites)), (result, raw, root) in zip(chosen, results):
        if result is None:
            ok = False
            line = f"[{name}] NO RESULT: {raw[-1500:]}"
        else:
            bad = result["bad"]
            ran_copy = all(root.name in module for module in result["modules"])
            failing = {t: bad[t] for t in sorted(bad)}
            if prediction == CONTROL:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] CONTROL, the unchanged copy: {result['ran']} tests of {list(suites)}, failing "
                        f"{sorted(bad) or 'none'} (ran the copy: {ran_copy}) -> {'PASS' if ok else 'FAIL'}")
            elif prediction == CAUGHT:
                caught = [t for t in expected if _hit(bad, t)]
                ok = ran_copy and bool(bad) and caught == list(expected)
                shown = dict(list(failing.items())[:6])
                more = f" (+{len(failing) - 6} more)" if len(failing) > 6 else ""
                line = (f"[{name}] BROKEN: {what}. Predicted CAUGHT by {list(expected) or 'any failing test'}. The copy ran "
                        f"{result['ran']} tests ({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {shown}{more} "
                        f"-> {'CAUGHT' if ok else 'NOT CAUGHT'}")
            else:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] BROKEN: {what}. Predicted REDUNDANT ALONE, because {expected} The copy ran "
                        f"{result['ran']} tests; failing: {failing or 'none'} -> {'as predicted' if ok else 'PREDICTION WRONG'}")
            if ok and prediction in counts:
                counts[prediction] += 1
        ok_all &= ok
        print(line, flush=True)
        out.append(line)
    verdict = "PASS" if ok_all else "FAIL"
    verdict, frozen_line = tree.seal(verdict)
    ok_all = verdict == "PASS"
    summary = (f"{counts[CAUGHT]} mutants CAUGHT as predicted, {counts[REDUNDANT]} REDUNDANT ALONE as predicted, of "
               f"{len(chosen) - (1 if any(n == 'R0' for n, _ in chosen) else 0)} run ({len(MUTANTS) - 1} defined)")
    out += ["", summary, frozen_line, f"OVERALL: {verdict}"]
    print(summary)
    print(frozen_line)
    print(f"OVERALL: {verdict}")
    if only is None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-{tag}-REVERT.txt"
        keep_earlier(path)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
