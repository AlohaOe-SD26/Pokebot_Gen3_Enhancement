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
    gate (S40), the fairness gate (S46), the options (S35b); and the R1 + R2 FOLLOW-UP's (its spec's section 6: S40c-g,
    S46c-f, L11-L18, M14, FX8, FX9, V6a-c, LV1, LV2; its fix round's ORDER and LV3; its second fix round's (verification VR-1) reorders of the guard's ends,
    ORDER-INT/AB/PARK/BUDGET and INT/AB/PARK/BUDGET/WALL-FIRST; the reset_refusal harness's need the framework, which a copy finds
    through `AI_PLAYER_TEST_SUPPORT_ROOT`, orchestrator ruling 9);
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
#: (R1 + R2 follow-up) the reset_refusal harness's tests: the REAL Session in a harness process, which needs the framework
#: (`AI_PLAYER_TEST_SUPPORT_ROOT` names it for a copy: test_host passes that one variable to its harness, ruling 9)
RESET_TEST = "test_host:ResetRefusalTests"
SESSION = "host/session.py"
RRT = "ResetRefusalTests."
LCT = "LauncherContinueTests."

#: name -> (prediction, the rule that is broken, [edits (file, anchor, replacement)], [tests that MUST fail] or the reason
#: (REDUNDANT), the suites it runs). The spec's hand-written mutants; `revert_r1_mutants.json` adds the rest (`_load`).
MUTANTS: dict[str, tuple] = {
    "R0": (CONTROL, "nothing: the unchanged copy", [], [],
           DEFAULT_SUITES + (PURITY_TEST, FAIRNESS_TEST, HOST_TEST, RESET_TEST)),
    # ---------------------------------------------------------------- the launcher and the host (spec section 6)
    "S27": (CAUGHT, "`--continue` keeps the .ss1 (also the live proof's LAUNCH-OLD)",
            [(LAUNCHER, "        if had:\n            dropped.unlink()\n", "        if False:\n            dropped.unlink()\n")],
            [LCT + "test_continue_removes_the_ss1_and_keeps_the_sav", LCT + "test_the_cart_is_told"], ("test_saving",)),
    "S33": (CAUGHT, "the end classes collapsed to the draft's \"no chosen end line -> allowed\" (findings M1, M2)",
            # (R1 + R2 follow-up: re-anchored on `judge_end`, which replaced `classify_end`; the same rule broken)
            [(LAUNCHER, "    session = book.last_session()\n    if session is None:\n"
                        "        return EndJudgement(\"UNKNOWN\", \"the memory file names no session\", False)\n",
              "    session = book.last_session()\n    if session is None:\n"
              "        return EndJudgement(\"UNKNOWN\", \"the memory file names no session\", False)\n"
              "    drafted = book.end_of(session[\"n\"])  # MUTANT S33\n"
              "    if drafted is None or not drafted.get(\"chosen\") or drafted.get(\"at_save\"):\n"
              "        return EndJudgement(\"KILLED\", \"MUTANT S33\", True)\n"
              "    return EndJudgement(\"CHOSEN\", \"MUTANT S33\", False)\n")],
            [LCT + "test_the_end_classes"], ("test_saving",)),
    "S34": (CAUGHT, "the launcher's `launch_end` line not written (finding M2)",
            # (U2 spec section 6) re-anchored on the call with its `frames` (D2); the same rule broken, the same test
            [(MAIN, "        record_launch(game, run_dir, result, read_verdict(run_dir), frames=args.frames)\n",
              "        pass  # MUTANT S34\n")],
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
    # ---------------------------------------------------------------- the R1 + R2 follow-up (spec 2026-10-29 section 6)
    "S40c": (CAUGHT, "N-1: `GeneratorExit`, `BaseException`, `BaseExceptionGroup`, `ExitStack` and `AsyncExitStack` out of "
                     "the play loop's exit names (back to the four)",
             [(PURITY, "\"KeyboardInterrupt\",\n                                  \"GeneratorExit\", \"BaseException\", "
                       "\"BaseExceptionGroup\", \"ExitStack\", \"AsyncExitStack\"})\n",
               "\"KeyboardInterrupt\"})  # MUTANT S40c\n")],
             ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    "S40d": (CAUGHT, "N-1: a bare `except:` allowed in the play loop",
             [(PURITY, "        if node.type is None and in_play_loop(self.key):\n", "        if False:  # MUTANT S40d\n")],
             ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    "S40e": (CAUGHT, "N-1: a `return`, `break` or `continue` in a `finally` allowed in the play loop",
             [(PURITY, "        if isinstance(node, ast.Return) or (isinstance(node, (ast.Break, ast.Continue)) and not in_loop):\n",
               "        if False:  # MUTANT S40e\n")],
             ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    "S40f": (CAUGHT, "N-1: `def __exit__`/`__aexit__` allowed in the play loop",
             [(PURITY, "        if node.name in EXIT_METHODS and in_play_loop(self.key):\n", "        if False:  # MUTANT S40f\n")],
             ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    "S40g": (CAUGHT, "N-1: a `yield`, `yield from` or `await` in a `finally` allowed in the play loop",
             [(PURITY, "        if isinstance(node, (ast.Yield, ast.YieldFrom, ast.Await)):\n", "        if False:  # MUTANT S40g\n")],
             ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    # ---------------------------------------------------------------- U2 (spec 2026-10-30 section 6; U2a scope)
    "S40h": (CAUGHT, "U2 D16 (RV-7): a `raise` in a `finally` allowed in the play loop (the Raise rule off)",
             [(PURITY, "        if isinstance(node, (ast.Raise, ast.Assert)):\n",
               "        if isinstance(node, (ast.Assert,)):  # MUTANT S40h\n")],
             ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    "S40i": (CAUGHT, "U2 D16 (RV-7): an `assert` in a `finally` allowed in the play loop (the Assert rule off)",
             [(PURITY, "        if isinstance(node, (ast.Raise, ast.Assert)):\n",
               "        if isinstance(node, (ast.Raise,)):  # MUTANT S40i\n")],
             ["PlayLoopExitTests.test_the_play_loop_cannot_exit"], (PURITY_TEST,)),
    "L11": (CAUGHT, "N-1 (D2): a refused reset or erase combination never latches the controller",
            [(CONTROLLER, "            self._refused = message\n", "            pass  # MUTANT L11\n")],
            ["ControllerTogetherTests.test_a_refusal_latches_the_controller",
             RRT + "test_a_refused_press_ends_the_run_on_the_next_frame",
             RRT + "test_a_refused_press_the_brain_catches_still_ends_the_run",
             RRT + "test_a_refused_press_then_a_brain_crash_ends_reset_refused"], (HOST_TEST, RESET_TEST)),
    "L12": (CAUGHT, "N-1 (D2): the latch's first statement removed (a press after a refusal goes through)",
            [(CONTROLLER, "        if self._refused is not None:\n", "        if False:  # MUTANT L12\n")],
            ["ControllerTogetherTests.test_a_refusal_latches_the_controller"], (HOST_TEST,)),
    "L13": (CAUGHT, "N-1 (D2): `reset-refused` classed INVOLUNTARY (the blocked reset gets its reload)",
            [(LAUNCHER, "_INVOLUNTARY = (\"crash\", \"frame-budget\", \"parked-manual\", \"abandoned\", \"interrupted\", "
                        "\"interrupted-unresponsive\")\n",
              "_INVOLUNTARY = (\"crash\", \"frame-budget\", \"parked-manual\", \"abandoned\", \"interrupted\", "
              "\"interrupted-unresponsive\", \"reset-refused\")  # MUTANT L13\n")],
            [LCT + "test_the_end_classes"], ("test_saving",)),
    "L14": (CAUGHT, "R-EXCEPT (D7): `read_launches`'s UnicodeDecodeError clause removed (a raw traceback, not a refusal)",
            [(LAUNCHER, "    except UnicodeDecodeError as error:  # (R1 + R2 follow-up, spec D7) a corrupted byte: refused "
                        "with words, never a traceback\n        raise LaunchError(f\"{path} cannot be read: it is not UTF-8 "
                        "({error})\") from error\n", "")],
            [LCT + "test_an_unreadable_launches_file_is_refused"], ("test_saving",)),
    "M14": (CAUGHT, "N-4 (D4): `read_book`'s ASCII check removed (both places: the header and the lines)",
            [("game_memory.py", "        first = json.loads(parts[0]) if parts[0].isascii() else None  # (D4) a non-ASCII "
                                "header is no header\n", "        first = json.loads(parts[0])  # MUTANT M14\n"),
             ("game_memory.py", "        if not text_line.isascii():\n", "        if False:  # MUTANT M14\n")],
            ["MemoryFileTests.test_a_non_ascii_middle_line_is_refused"], ("test_saving",)),
    "L15": (CAUGHT, "N-1 (D2): the guard's `_on_frame` never ends a latched run",
            [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n",
              "        self.frames_seen += 1\n        pass  # MUTANT L15\n")],
            [RRT + "test_a_refused_press_ends_the_run_on_the_next_frame",
             RRT + "test_a_refused_press_the_brain_catches_still_ends_the_run"], (RESET_TEST,)),
    "L16": (CAUGHT, "N-1 (D2): a brain crash or stray exit after a refusal ends as a crash or stray-exit, not reset-refused",
            [(SESSION, "                self._end_if_refused()  # a crash or a stray exit after a refused press is the refusal "
                       "(spec D2)\n",
              "                pass  # MUTANT L16\n")],
            [RRT + "test_a_refused_press_then_a_brain_crash_ends_reset_refused",
             RRT + "test_a_refused_press_then_a_stray_exit_ends_reset_refused"], (RESET_TEST,)),
    "L18": (CAUGHT, "N-1 (D2): a brain that RETURNS after a refusal ends brain-returned, not reset-refused",
            [(SESSION, "                    self._end_if_refused()  # the brain returned right after a refused press "
                       "(spec D2)\n",
              "                    pass  # MUTANT L18\n")],
            [RRT + "test_a_refused_press_then_the_brain_returns_ends_reset_refused"], (RESET_TEST,)),
    "ORDER": (CAUGHT, "N-1 (D2; fix round, review RV-1): `_on_frame` checks the latch AFTER the abandoned / parked / budget / "
                      "wall-clock ends, so a refused reset followed by a discarded or switched mode ends INVOLUNTARY (a "
                      "continue allowed) instead of reset-refused",
              [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n",
                "        self.frames_seen += 1\n"),
               (SESSION, "            self.lifecycle.finish(\"wall-clock\", EXIT_WALL_CLOCK)\n",
                "            self.lifecycle.finish(\"wall-clock\", EXIT_WALL_CLOCK)\n"
                "        self._end_if_refused()  # MUTANT ORDER\n")],
              [RRT + "test_a_refused_press_then_the_mode_is_discarded_ends_reset_refused",
               RRT + "test_a_refused_press_then_the_mode_switched_ends_reset_refused",
               # (second fix round, verification VR-1) the interrupt and the every-end-due cases catch it too
               RRT + "test_a_refused_press_then_an_interrupt_ends_reset_refused",
               RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    # (second fix round, verification VR-1) EVERY reorder of the guard's ends: ORDER-<X> moves the latch check to just
    # after end X's finish; <X>-FIRST copies end X's check AHEAD of the latch. Before VR-1's tests, ORDER-INT, INT-FIRST,
    # BUDGET-FIRST and WALL-FIRST survived every ResetRefusalTests case (interrupted, frame-budget and wall-clock all let
    # the launcher continue: INVOLUNTARY or BUDGET); the every-end-due case catches all nine.
    "ORDER-INT": (CAUGHT, "N-1 (D2; VR-1): `_on_frame` checks the latch just AFTER the interrupt's end, so a refused reset "
                          "followed by a Ctrl+C ends interrupted/130 (INVOLUNTARY: a continue allowed)",
                  [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n", "        self.frames_seen += 1\n"),
                   (SESSION, "            self.lifecycle.finish(\"interrupted\", EXIT_INTERRUPTED)\n",
                    "            self.lifecycle.finish(\"interrupted\", EXIT_INTERRUPTED)\n"
                    "        self._end_if_refused()  # MUTANT ORDER-INT\n")],
                  [RRT + "test_a_refused_press_then_an_interrupt_ends_reset_refused",
                   RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "ORDER-AB": (CAUGHT, "N-1 (D2; VR-1): `_on_frame` checks the latch just AFTER the abandoned end",
                 [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n", "        self.frames_seen += 1\n"),
                  (SESSION, "            self.lifecycle.finish(\"abandoned\", EXIT_PARKED)\n",
                   "            self.lifecycle.finish(\"abandoned\", EXIT_PARKED)\n"
                   "        self._end_if_refused()  # MUTANT ORDER-AB\n")],
                 [RRT + "test_a_refused_press_then_an_interrupt_ends_reset_refused",
                  RRT + "test_a_refused_press_then_the_mode_is_discarded_ends_reset_refused",
                  RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "ORDER-PARK": (CAUGHT, "N-1 (D2; VR-1): `_on_frame` checks the latch just AFTER the parked-manual end",
                   [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n", "        self.frames_seen += 1\n"),
                    (SESSION, "            self.lifecycle.finish(\"parked-manual\", EXIT_PARKED)\n",
                     "            self.lifecycle.finish(\"parked-manual\", EXIT_PARKED)\n"
                     "        self._end_if_refused()  # MUTANT ORDER-PARK\n")],
                   [RRT + "test_a_refused_press_then_an_interrupt_ends_reset_refused",
                    RRT + "test_a_refused_press_then_the_mode_is_discarded_ends_reset_refused",
                    RRT + "test_a_refused_press_then_the_mode_switched_ends_reset_refused",
                    RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "ORDER-BUDGET": (CAUGHT, "N-1 (D2; VR-1): `_on_frame` checks the latch just AFTER the frame-budget end",
                     [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n",
                       "        self.frames_seen += 1\n"),
                      (SESSION, "            self.lifecycle.finish(\"frame-budget\", EXIT_FRAME_BUDGET)\n",
                       "            self.lifecycle.finish(\"frame-budget\", EXIT_FRAME_BUDGET)\n"
                       "        self._end_if_refused()  # MUTANT ORDER-BUDGET\n")],
                     [RRT + "test_a_refused_press_then_an_interrupt_ends_reset_refused",
                      RRT + "test_a_refused_press_then_the_mode_is_discarded_ends_reset_refused",
                      RRT + "test_a_refused_press_then_the_mode_switched_ends_reset_refused",
                      RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "INT-FIRST": (CAUGHT, "N-1 (D2; VR-1): the interrupt's check put AHEAD of the latch in `_on_frame`",
                  [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n",
                    "        self.frames_seen += 1\n        if self.interrupted is not None:\n"
                    "            self.lifecycle.finish(\"interrupted\", EXIT_INTERRUPTED)  # MUTANT INT-FIRST\n"
                    "        self._end_if_refused()\n")],
                  [RRT + "test_a_refused_press_then_an_interrupt_ends_reset_refused",
                   RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "AB-FIRST": (CAUGHT, "N-1 (D2; VR-1): the abandoned check put AHEAD of the latch in `_on_frame`",
                 [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n",
                   "        self.frames_seen += 1\n        if self.lifecycle.abandoned:\n"
                   "            self.lifecycle.finish(\"abandoned\", EXIT_PARKED)  # MUTANT AB-FIRST\n"
                   "        self._end_if_refused()\n")],
                 [RRT + "test_a_refused_press_then_the_mode_is_discarded_ends_reset_refused",
                  RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "PARK-FIRST": (CAUGHT, "N-1 (D2; VR-1): the mode-switch check put AHEAD of the latch in `_on_frame`",
                   [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n",
                     "        self.frames_seen += 1\n        if context.bot_mode != MODE_NAME:\n"
                     "            self.lifecycle.finish(\"parked-manual\", EXIT_PARKED)  # MUTANT PARK-FIRST\n"
                     "        self._end_if_refused()\n")],
                   [RRT + "test_a_refused_press_then_the_mode_switched_ends_reset_refused",
                    RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "BUDGET-FIRST": (CAUGHT, "N-1 (D2; VR-1): the frame-budget check put AHEAD of the latch in `_on_frame` (frame-budget is "
                             "INVOLUNTARY: a continue allowed)",
                     [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n",
                       "        self.frames_seen += 1\n        if self.frames_seen > self.frame_cap:\n"
                       "            self.lifecycle.finish(\"frame-budget\", EXIT_FRAME_BUDGET)  # MUTANT BUDGET-FIRST\n"
                       "        self._end_if_refused()\n")],
                     [RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "WALL-FIRST": (CAUGHT, "N-1 (D2; VR-1): the wall-clock check put AHEAD of the latch in `_on_frame` (wall-clock is a "
                           "BUDGET end: a continue allowed after a save)",
                   [(SESSION, "        self.frames_seen += 1\n        self._end_if_refused()\n",
                     "        self.frames_seen += 1\n        if self.options.wall_deadline is not None and time.time() >= "
                     "self.options.wall_deadline:\n"
                     "            self.lifecycle.finish(\"wall-clock\", EXIT_WALL_CLOCK)  # MUTANT WALL-FIRST\n"
                     "        self._end_if_refused()\n")],
                   [RRT + "test_every_other_end_due_on_the_same_frame_still_ends_reset_refused"], (RESET_TEST,)),
    "L17": (CAUGHT, "N-1 (D2): `held` hands out the controller's own mutable set (the brain can empty it)",
            [(CONTROLLER, "        return frozenset(self._held)\n", "        return self._held  # MUTANT L17\n")],
            ["ControllerTogetherTests.test_the_held_set_cannot_be_changed_from_outside"], (HOST_TEST,)),
    "S46": (CAUGHT, "the play time read anywhere in the deciding code (D18: RULE C's door not asked)",
            [(FAIRNESS, "                if door is None:\n", "                if False:  # MUTANT S46\n")],
            ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46b": (CAUGHT, "a stale play-time door passes (RULE C's stale check deleted)",
             [(FAIRNESS, "        if (\"time\", file, function) not in used:\n", "        if False:  # MUTANT S46b\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46c": (CAUGHT, "N-2 (D3 (a)): RULE C's constant key form off (`x['play_time']`, `.get('play_time')`, a match mapping)",
             [(FAIRNESS, "            if isinstance(node, ast.Constant) and node.value == PLAY_TIME_FIELD",
               "            if False and isinstance(node, ast.Constant) and node.value == PLAY_TIME_FIELD")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46d": (CAUGHT, "N-2 (D3 (b)): RULE C's match class keyword form off (`case Progress(play_time=t)`)",
             [(FAIRNESS, "            if isinstance(node, ast.MatchClass) and PLAY_TIME_FIELD in node.kwd_attrs:\n",
               "            if False:  # MUTANT S46d\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46e": (CAUGHT, "N-2 (D3 (c)): RULE C's whole-object copy form off (`asdict`, `astuple`)",
             [(FAIRNESS, "            if isinstance(node, ast.Call) and _call_name(node) in WHOLE_COPY_CALLS:\n",
               "            if False:  # MUTANT S46e\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46f": (CAUGHT, "N-2 (D3 (d)): a class pattern with positional sub-patterns allowed in deciding code",
             [(FAIRNESS, "            if isinstance(node, ast.MatchClass) and node.patterns and not _self_match(node, bound, "
                         "builtins_touched):\n", "            if False:  # MUTANT S46f\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    # (U2 spec 2026-10-30 D15, RV-5) the self-matching builtin's exception, each of its conditions broken; S46i-S46k are the
    # builder's own (the `builtins` conditions and the one-sub-pattern / no-keyword conditions, each a guard of D15)
    "S46g": (CAUGHT, "U2 D15 (RV-5): the self-match exception ignores a REBOUND builtin name (`int = Progress`)",
             [(FAIRNESS, "and not node.kwd_patterns and node.cls.id not in bound and not builtins_touched)\n",
               "and not node.kwd_patterns and not builtins_touched)  # MUTANT S46g\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46h": (CAUGHT, "U2 D15 (RV-5): the binding pre-pass collects `ast.Name` stores only (`case type() as int` passes)",
             [(FAIRNESS, "        bound.update(_other_bindings(node))\n", "        pass  # MUTANT S46h\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46i": (CAUGHT, "U2 D15 (RV-5): a module that imports `builtins` keeps the self-match exception",
             [(FAIRNESS, "    builtins_touched = builtins_shared or _touches_builtins(tree)\n",
               "    builtins_touched = builtins_shared  # MUTANT S46i\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46j": (CAUGHT, "U2 D15 (RV-5): `builtins.int = X` in ANOTHER module of the package not seen by `check`",
             [(FAIRNESS, "                              builtins_shared=bool(shared))\n",
               "                              builtins_shared=False)  # MUTANT S46j\n")],
             ["FairnessTests.test_the_play_time_is_read_only_through_its_doors"], (FAIRNESS_TEST,)),
    "S46k": (CAUGHT, "U2 D15 (RV-5): the self-match exception takes any number of sub-patterns and keywords",
             [(FAIRNESS, "    return (isinstance(node.cls, ast.Name) and node.cls.id in SELF_MATCHING_BUILTINS and len(node.patterns) == 1\n"
                         "            and not node.kwd_patterns ",
               "    return (isinstance(node.cls, ast.Name) and node.cls.id in SELF_MATCHING_BUILTINS  # MUTANT S46k\n"
               "            and True ")],
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
    # (U2 spec section 6, a RULE CHANGE) the no-end-line refusal now holds for CHOSEN (and a BUDGET end whose launcher line
    # carries no verdict word, the interim's), never for a verified BUDGET end; the anchor is unchanged (it is that refusal)
    "L10": (CAUGHT, "a CHOSEN end with no `end` line allowed (fail open)",
            [(LAUNCHER, "    if end is None:\n        return (kind, f\"session {session['n']} ended '{reason}' with no end line",
              "    if False:  # MUTANT L10\n        return (kind, f\"session {session['n']} ended '{reason}' with no end line")],
            [LCT + "test_the_end_classes"], ("test_saving",)),
    # ---------------------------------------------------------------- U2 (spec 2026-10-30 section 6, U2a): the launcher table
    "U0": (CAUGHT, "U2: every frame-budget and soft-wall row back to the interim (`at_save` only; refused with no end line); "
                   "also the live U2-BUDGET-OLD and U2-WALL-OLD trees",
           [(LAUNCHER, "        allowed = kind == \"INVOLUNTARY\" or kind == \"BUDGET\" or at_save\n",
             "        allowed = kind == \"INVOLUNTARY\" or at_save  # MUTANT U0\n"),
            (LAUNCHER, "    if kind == \"BUDGET\" and clean is not None:\n",
             "    if kind == \"BUDGET\" and False:  # MUTANT U0\n")],
           [LCT + "test_the_end_classes"], ("test_saving",)),
    "U1": (CAUGHT, "U2: the harness BUDGET row back to `at_save`",
           [(LAUNCHER, "        allowed = kind == \"INVOLUNTARY\" or kind == \"BUDGET\" or at_save\n",
             "        allowed = kind == \"INVOLUNTARY\" or at_save  # MUTANT U1\n")],
           [LCT + "test_the_end_classes"], ("test_saving",)),
    "U2a": (CAUGHT, "U2: the verified `stopped` row back to `at_save`",
            [(LAUNCHER, "    if kind == \"BUDGET\" and clean is not None:\n",
              "    if kind == \"BUDGET\" and clean is not None and reason == \"wall-clock\":  # MUTANT U2a\n")],
            [LCT + "test_the_end_classes"], ("test_saving",)),
    "U3": (CAUGHT, "U2: `wall-clock` with no end line refused again",
           [(LAUNCHER, "    if kind == \"BUDGET\" and clean is not None:\n",
             "    if kind == \"BUDGET\" and clean is not None and (end is not None or reason != \"wall-clock\"):  # MUTANT U3\n")],
           [LCT + "test_the_end_classes"], ("test_saving",)),
    "U4": (CAUGHT, "U2: the launcher's hard kill with no verdict allowed always (the rejected design)",
           [(LAUNCHER, "f\"a kill (USER RULING 53: not a time limit; continued only right after a save)\", at_save,\n",
             "f\"a kill (USER RULING 53: not a time limit; continued only right after a save)\", True,  # MUTANT U4\n")],
           [LCT + "test_the_end_classes"], ("test_saving",)),
    "U4b": (CAUGHT, "U2 D3a: the hard-kill row before the verdict (HEAD's order)",
            [(LAUNCHER, "        if line.get(\"hard_kill\") and line.get(\"exit_reason\") is None:\n",
              "        if line.get(\"hard_kill\"):  # MUTANT U4b\n")],
            [LCT + "test_a_hard_kill_is_judged_by_its_verdict_first"], ("test_saving",)),
    "U4c": (CAUGHT, "U2a fix round F1: the interrupted row before the verdict (the pre-fix order)",
            # (U2a verification V1: re-anchored on the row as V1 left it; the same rule broken)
            [(LAUNCHER, "        if line.get(\"interrupted\") and line.get(\"exit_reason\") is None:\n",
              "        if line.get(\"interrupted\"):  # MUTANT U4c\n")],
            [LCT + "test_an_interrupt_is_judged_by_its_verdict_first"], ("test_saving",)),
    "U4d": (CAUGHT, "U2a verification V1: the interrupted row allow-lists the WORDS `interrupted` / "
                    "`interrupted-unresponsive` (F1's row, the code never checked: a brain-returned word plus a Ctrl+C "
                    "believed)",
            [(LAUNCHER, "        if line.get(\"interrupted\") and line.get(\"exit_reason\") is None:\n",
              "        if line.get(\"interrupted\") and line.get(\"exit_reason\") in (None, \"interrupted\", "
              "\"interrupted-unresponsive\"):  # MUTANT U4d\n")],
            [LCT + "test_an_interrupt_is_judged_by_its_verdict_first"], ("test_saving",)),
    # (U2a fix round F3) a NEW host end in KEYWORD form, every existing end kept: the pre-fix pin skipped the call and its
    # set-equality check still held, so only the keyword-aware pin catches it (a RE-CODED existing end is caught either
    # way, by the set check, so it would not discriminate the fix)
    "U12": (CAUGHT, "U2a fix round F3: a new host end added in KEYWORD form (`finish(\"new-end\", code=EXIT_PARKED)`), "
                    "outside both launcher tables",
            [(SESSION, "            self.lifecycle.finish(\"frame-budget\", EXIT_FRAME_BUDGET)\n",
              "            self.lifecycle.finish(\"frame-budget\", EXIT_FRAME_BUDGET)\n"
              "        if self.frames_seen < 0:  # MUTANT U12\n"
              "            self.lifecycle.finish(\"new-end\", code=EXIT_PARKED)\n")],
            [LCT + "test_the_host_codes_match_the_host"], ("test_saving",)),
    "U5": (CAUGHT, "U2 D2: `_ran_out` always True (a `play: stopped:` believed from the AI's own word)",
           [(LAUNCHER, "    frames = (line or {}).get(\"frames\")\n    real = (line or {}).get(\"real_frames\")\n",
             "    return True  # MUTANT U5\n")],
           [LCT + "test_a_stop_before_the_budget_is_the_ais_own_choice"], ("test_saving",)),
    "U6": (CAUGHT, "U2 D3: the host-code check skipped (the brain's text `crash`/`wall-clock` believed)",
           [(LAUNCHER, "    if reason in _HOST_CODES and code != _HOST_CODES[reason]:\n", "    if False:  # MUTANT U6\n")],
           [LCT + "test_a_host_reason_needs_its_host_code"], ("test_saving",)),
    "U7": (CAUGHT, "U2 D2: `record_launch` omits the four fields (frames, real_frames, verdict, verdict_code)",
           [(LAUNCHER, "            \"frames\": frames if verdict is not None else None,\n"
                       "            \"real_frames\": counters.get(\"real_frames\") if verdict is not None else None,\n"
                       "            \"verdict\": verdict.get(\"verdict\") if verdict is not None else None,\n"
                       "            \"verdict_code\": facts.get(\"exit_code\") if verdict is not None else None,\n", "")],
           [LCT + "test_the_launch_line_carries_the_counts"], ("test_saving",)),
    "U8": (CAUGHT, "U2 D2: `_ran_out` uses `>` (a stop at exactly its budget read as early)",
           [(LAUNCHER, "    return frames > 0 and real >= frames\n", "    return frames > 0 and real > frames  # MUTANT U8\n")],
           [LCT + "test_a_stop_before_the_budget_is_the_ais_own_choice"], ("test_saving",)),
    "U9": (CAUGHT, "U2 D3: the code judged by the PROCESS `exit_code`, not the instrument's `verdict_code`",
           [(LAUNCHER, "        code = line.get(\"verdict_code\") if line.get(\"verdict_code\") is not None else process\n",
             "        code = process  # MUTANT U9\n")],
           [LCT + "test_a_host_reason_needs_its_host_code"], ("test_saving",)),
    # (U2a verification V3) a 417df790 line (no `verdict_code`) reads the instrument's code from the run's verdict file;
    # U9b also DELETES the census's new `read_verdict` call site in `_classify_session`
    "U9b": (CAUGHT, "U2a verification V3: an older line's verdict file not read (the process code, the launcher's own 130 "
                    "or 124, judges a real host end NOT CLEAN for good)",
            [(LAUNCHER, "            filed = read_verdict(Path(run_dir)) if run_dir and Path(run_dir).is_dir() else None\n",
              "            filed = None  # MUTANT U9b\n")],
            [LCT + "test_an_older_line_reads_the_instruments_code_from_its_verdict_file"], ("test_saving",)),
    # (U2a verification V3) the census counts every `read_verdict` call of `_classify_session` once U9b's is added: the
    # verdict-file path's own read (no launcher line) deleted reads as a kill (KILLED, allowed) for any verdict
    "U9e": (CAUGHT, "U2a verification V3 (census): the verdict-file path's `read_verdict` call deleted (a session with "
                    "no launcher line judged KILLED whatever its verdict file says)",
            [(LAUNCHER, "        verdict = read_verdict(Path(run_dir))\n", "        verdict = None  # MUTANT U9e\n")],
            [LCT + "test_a_host_reason_needs_its_host_code"], ("test_saving",)),
    "U9c": (CAUGHT, "U2a verification V3: one NOT CLEAN sentence for every code source (the process code called the "
                    "instrument's)",
            [(LAUNCHER, "        if source == \"process\":  # (V3) no record of the instrument's: the process code only, "
                        "and the words say so\n",
              "        if False:  # MUTANT U9c\n")],
            [LCT + "test_an_older_line_reads_the_instruments_code_from_its_verdict_file"], ("test_saving",)),
    "U9d": (CAUGHT, "U2a verification V3: the mismatch told as \"the instrument recorded\" whatever recorded it",
            [(LAUNCHER, "    recorded = \"the instrument recorded\" if source == \"instrument\" else \"the run's verdict file "
                        "recorded\"\n",
              "    recorded = \"the instrument recorded\"  # MUTANT U9d\n")],
            [LCT + "test_an_older_line_reads_the_instruments_code_from_its_verdict_file"], ("test_saving",)),
    "U10": (CAUGHT, "U2 D3b: a BUDGET end's CLEAN check skipped (a BREACH wall-clock continued)",
            [(LAUNCHER, "        if clean != \"CLEAN\":\n", "        if False:  # MUTANT U10\n")],
            [LCT + "test_a_budget_end_needs_a_clean_verdict"], ("test_saving",)),
    "U11": (CAUGHT, "U2 D4: the harness branch chosen by the AI-written session `host` first",
            [(LAUNCHER, "    if line is None and session.get(\"host\") == \"harness\":\n",
              "    if session.get(\"host\") == \"harness\":  # MUTANT U11\n")],
            [LCT + "test_a_launcher_run_is_judged_by_its_line_whatever_host_says"], ("test_saving",)),
    # ---------------------------------------------------------------- U2 (spec 2026-10-30 section 6, U2a): what a continue drops
    "D1m": (CAUGHT, "U2 D13: `dropped_after` reports 0 (the latest stamp) for a session with no end line",
            [("game_memory.py", "            frames = None if end is None or not isinstance(since, int) else "
                                "int(end[\"frame\"]) - since\n",
              "            frames = 0 if end is None or not isinstance(since, int) else int(end[\"frame\"]) - since  "
              "# MUTANT D1m\n")],
            ["MemoryFileTests.test_u2_dropped_after"], ("test_saving",)),
    "D2m": (CAUGHT, "U2 D13: `dropped_maps` drops the `first_frame` filter (maps known before the save named as dropped)",
            [(LAUNCHER, "            if (first > since) if entry.get(\"own\") else (first >= since):\n",
              "            if True:  # MUTANT D2m\n")],
            [LCT + "test_u2_the_drop_uses_the_hosts_count_and_names_the_maps_after_the_save"], ("test_saving",)),
    "HM1": (CAUGHT, "U2a fix round F2: `_host_frames` takes each session's frames from the AI's own end line, not the "
                    "launcher line's `real_frames` (the host's count)",
            [(LAUNCHER, "        per.append(real - (entry[\"since\"] - base) if entry.get(\"own\") else real)\n",
              "        per.append(entry[\"frames\"])  # MUTANT HM1\n")],
            [LCT + "test_u2_the_drop_uses_the_hosts_count_and_names_the_maps_after_the_save",
             LCT + "test_u2_the_drop_offsets_a_save_inside_a_continued_session"], ("test_saving",)),
    "HM3": (CAUGHT, "U2a verification V2: the own session's offset without its `frame_base` (`real - since`: right only "
                    "for a session whose base is 0)",
            [(LAUNCHER, "        per.append(real - (entry[\"since\"] - base) if entry.get(\"own\") else real)\n",
              "        per.append(real - entry[\"since\"] if entry.get(\"own\") else real)  # MUTANT HM3\n")],
            [LCT + "test_u2_the_drop_offsets_a_save_inside_a_continued_session"], ("test_saving",)),
    "D3m": (CAUGHT, "U2 D13: `end_line` without `play_time` / `where`",
            [("game_memory.py", "    line[\"play_time\"] = _stamp_of(look) if look is not None else None\n"
                                "    line[\"where\"] = where_of(look) if look is not None else None\n", "")],
            ["MemoryFileTests.test_the_end_line_says_chosen_budget_and_at_save"], ("test_saving",)),
    "D4m": (CAUGHT, "U2 D13: the continued session line's `dropped` not written",
            [("mode.py", "        self._writer.session[\"dropped\"] = result.dropped\n", "        pass  # MUTANT D4m\n")],
            ["R1PlayTests.test_u2_the_ais_continue_tells_the_drop_and_no_map"], ("test_goals",)),
    "D5m": (CAUGHT, "U2 D13: `at_end` from the newest end line in the FILE, not the newest dropped session's",
            [("game_memory.py", "        newest_end = self.end_of(chosen[-1][\"n\"]) if chosen else None\n",
              "        newest_end = next((line for line in reversed(self.lines) if line[\"kind\"] == \"end\"), None)  "
              "# MUTANT D5m\n")],
            ["MemoryFileTests.test_u2_dropped_after"], ("test_saving",)),
    "D6m": (CAUGHT, "U2 D13: the drop set is cumulative (every session after the save, not after its latest continue)",
            [("game_memory.py", "        if continued:\n            chosen = [line for i, line in sessions if i >= "
                                "continued[-1]]\n",
              "        if False:  # MUTANT D6m\n            chosen = [line for i, line in sessions if i >= "
              "continued[-1]]\n")],
            ["MemoryFileTests.test_u2_dropped_after"], ("test_saving",)),
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
    "CH1": (CAUGHT, "N-3 (D11; orchestrator ruling 2): a continued writer chains its first save to the NEWEST save line "
                    "(the abandoned branch), not to the save it continued (also the live proof's CHAIN-OLD)",
            [("game_memory.py",
              "        self.parent: int | None = continued if book is not None and isinstance(continued, int) else None\n",
              "        self.parent: int | None = book.newest_save()['id'] if book is not None and isinstance(continued, int) "
              "else None  # MUTANT CH1\n")],
            ["MemoryFileTests.test_rebuild_follows_the_parent_across_a_continue"], ("test_saving",)),
    "V6a": (CAUGHT, "V2-6 (D6): `after_goal`'s save return removed (a save resets the curiosity row)",
            [("brain/goals.py", "        if goal.kind == \"save\":\n            # (D6) transparent: a reset by bookkeeping would let "
                                "C C save C C through CURIOUS_ROW_MAX\n            return None\n", "")],
            ["test_a_save_neither_ends_nor_joins_a_curiosity_row"], ("test_goals",)),
    "V6b": (CAUGHT, "V2-6 (D6): the grader's `curiosity_streaks` counts a save as a break",
            [("gates/rate_step5.py", "        if span[\"kind\"] == SAVE_KIND:\n            continue\n", "")],
            ["test_a_save_neither_ends_nor_joins_a_grader_streak"], ("test_goals",)),
    "V6c": (CAUGHT, "V2-6 (D6): the grader's `aside_streaks` counts a save as a break",
            [("gates/rate_step5.py", "    spans = [s for s in goal_spans(actions) if s[\"kind\"] != SAVE_KIND]\n",
              "    spans = goal_spans(actions)  # MUTANT V6c\n")],
            ["test_a_save_neither_ends_nor_joins_a_grader_streak"], ("test_goals",)),
    "LV1": (CAUGHT, "V2-1: `live_r1.verdict_line` omits the K-BETWEEN caveat (the headline without its caveat)",
            [("gates/live_r1.py", "    return (f\"LIVE R1 VERDICT: {result['verdict']}{between_caveat(summaries, seeds)} (failing: \"\n",
              "    return (f\"LIVE R1 VERDICT: {result['verdict']} (failing: \"  # MUTANT LV1\n")],
            ["LiveR1HeadlineTests.test_the_verdict_line_carries_the_caveat"], ("test_saving",)),
    "LV2": (CAUGHT, "V2-2: `live_r1.between_caveat` counts the midpoint arm's seeds but ignores whether they passed",
            [("gates/live_r1.py", "    passed = [seed for seed in counted if mid[seed].get(\"pass\")]\n",
              "    passed = list(counted)  # MUTANT LV2\n")],
            ["LiveR1HeadlineTests.test_the_caveat_counts_the_midpoint_passes_and_names_its_failing_seeds",
             "LiveR1HeadlineTests.test_the_verdict_line_carries_the_caveat"], ("test_saving",)),
    "LV3": (CAUGHT, "fix round, review RV-2: `live_r1.between_caveat` calls a midpoint that counted on SOME seeds (under the "
                    "floor) 'vacuous' (the headline contradicting itself: 'counted 2 of 4: vacuous; passed 2 of 2')",
            [("gates/live_r1.py", "    shortfall = \": vacuous\" if not counted else (\": below the floor\" if len(counted) < "
                                  "FLOOR else \"\")\n",
              "    shortfall = \": vacuous\" if len(counted) < FLOOR else \"\"  # MUTANT LV3\n")],
            ["LiveR1HeadlineTests.test_a_midpoint_counted_below_the_floor_is_not_called_vacuous"], ("test_saving",)),
    "FX8": (CAUGHT, "V2-5 (D5): `judge_end` drops the look-through's count and reason from its words",
            [(LAUNCHER, "            if looked:\n", "            if False:  # MUTANT FX8\n")],
            [LCT + "test_the_look_through_is_counted_and_told"], ("test_saving",)),
    "FX9": (CAUGHT, "V2-5 (D5): `memory_check` leaves `looked_through` 0",
            [(LAUNCHER, "    looked = len(judgement.looked_through)\n", "    looked = 0  # MUTANT FX9\n")],
            [LCT + "test_the_look_through_is_counted_and_told"], ("test_saving",)),
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
