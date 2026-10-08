"""MUTANT PROOF of AI-player build step 2 (the hands): each check of the REAL hands code, broken in a COPY of
the package, fails its predicted test, or is documented as REDUNDANT ALONE with the reason.

    py -3.12 ai_player/gates/revert_step2.py        (exit 0 = every prediction held)

WHY (CLAUDE.md session discipline rule 6, "fault-test every gate"): `gates/test_hands.py`'s fault halves mostly
flip the FAULT switches (`Faults(ungated_a=True)`, `Faults(blind_count=True)`). That shows the tests catch a
NAIVE driver, not that each check in the REAL code carries weight. The step-2 verifier mutated the real code
(its H1-H10) and found most checks caught, but four not caught and not documented: advance()'s two wait checks
(each redundant alone), choose()'s `cursor == index` and move_cursor()'s `accepts_input`. This script makes
that audit a standing gate: for every mutant it copies the package to a temporary folder (no `.ss1` states,
no evidence), applies the edits there (each anchor must occur exactly once, or the run aborts), runs
`gates/test_hands.py` from the copy (the framework from this repo: `AI_PLAYER_TEST_SUPPORT_ROOT`), and checks
the PREDICTION:
  CAUGHT     every named test fails (other tests may fail too; all are printed);
  REDUNDANT  NO test fails, and the reason the check is redundant ALONE is written next to it (as live_step1's
             SW-R1 / SW-R2 document the script wait's two halves). A redundant check stays in the code: each is
             the GATE of a press (the look right before it, logged), and the reason names what would make it
             load-bearing.
The unchanged copy (H0) must pass every test, so a failure means the mutant, not the copy.
Evidence: `ai_player/evidence/<date>-step2-REVERT.txt`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from ai_player.gates.provenance import provenance  # noqa: E402  (the evidence's code line, since step 3's verifier)

EVIDENCE = REPO / "ai_player" / "evidence"
TIMEOUT = 600

CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"

# -- the edits (file, anchor, replacement); each anchor must occur exactly once in its file ------------------
_ADVANCE_OUTER = ("hands/dialogue.py", "        if look.screen.waits_for_button:\n            page = page_text(look.screen.text)\n",
                  "        if True:  # MUTANT H2-outer\n            page = page_text(look.screen.text)\n")
_ADVANCE_GATE = ("hands/dialogue.py", "            if look.screen.waits_for_button and look.screen.ui is None:\n",
                 "            if look.screen.ui is None:  # MUTANT H2-gate\n")
_CLOCK_OUTER = ("hands/menus.py", "        if forward == 0:\n", "        if True:  # MUTANT H8a: A without the time read first\n")
_CLOCK_GATE = ("hands/menus.py", " and ui.accepts_input and ui.hours * 60 + ui.minutes == want:\n",
               " and ui.accepts_input:  # MUTANT H8b\n")

#: name -> (prediction, the check that is broken, [edits], tests that MUST fail (CAUGHT) or the reason (REDUNDANT)).
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str] | str]] = {
    "H0": (CONTROL, "nothing: the unchanged copy", [], []),
    # ---- hands/dialogue.py: advance
    "H1": (CAUGHT, "advance() does not stop at a menu (the choice is the caller's)",
           [("hands/dialogue.py", "        if ui is not None:\n            return f\"menu:{ui.kind}\"\n",
             "        if False:  # MUTANT H1\n            return f\"menu:{ui.kind}\"\n")],
           ["DialogueTests.test_a_only_on_waits_and_never_on_the_choice"]),
    "H2-outer": (CAUGHT, "advance()'s FIRST wait check (the look that starts the reading) removed",
                 [_ADVANCE_OUTER], ["DialogueTests.test_each_page_is_read_after_it_has_printed"]),
    "H2-gate": (REDUNDANT, "advance()'s SECOND wait check (the gate: the look right before the A) removed",
                [_ADVANCE_GATE],
                "the first check saw the wait one reading delay earlier, and a wait the eyes report ends ONLY on a "
                "press: RENDER_STATE_WAIT / CLEAR / SCROLL_START call TextPrinterWait / TextPrinterWaitWithDownArrow, "
                "which poll JOY_NEW(A_BUTTON | B_BUTTON) (src/text.c; under autoScroll they time out, but the eyes "
                "report NO wait then, eyes/view.py text_printer_wait), the script's WaitForAorBPress polls A and B "
                "(src/scrcmd.c), and each TASK_WAITS task polls JOY_NEW with no timeout (src/main_menu.c, src/shop.c, "
                "src/wallclock.c). Load-bearing only if a wait could end by itself during the AI's reading delay."),
    "H2-both": (CAUGHT, "both of advance()'s wait checks removed", [_ADVANCE_OUTER, _ADVANCE_GATE],
                ["DialogueTests.test_a_only_on_waits_and_never_on_the_choice"]),
    "H6": (CAUGHT, "talk() does not wait for the player to be free (the museum-greeter rule)",
           [("hands/dialogue.py", "            if player_free(look):\n                break\n", "            break  # MUTANT H6\n")],
           ["TalkTests.test_no_a_while_a_script_runs"]),
    "H10": (CAUGHT, "talk() does not turn to face the person first",
            [("hands/dialogue.py", "        if look.player.facing != direction:\n", "        if False:  # MUTANT H10\n")],
            ["TalkTests.test_no_a_while_a_script_runs"]),
    # ---- hands/menus.py: cursors
    "H3": (CAUGHT, "choose()'s gate does not check the cursor is ON the option",
           [("hands/menus.py", "        elif ui is not None and ui.kind == kind and ui.cursor == index and ui.accepts_input:\n",
             "        elif ui is not None and ui.kind == kind and ui.accepts_input:  # MUTANT H3\n")],
           ["CursorTests.test_the_press_gate_is_its_own_look"]),
    "H11": (REDUNDANT, "choose()'s gate does not check the menu takes input",
            [("hands/menus.py", "        elif ui is not None and ui.kind == kind and ui.cursor == index and ui.accepts_input:\n",
              "        elif ui is not None and ui.kind == kind and ui.cursor == index:  # MUTANT H11\n")],
            "the gate's look is the SAME frame as move_cursor()'s last look, which returned True only on a look that "
            "took input (its accepts_input check comes before its cursor check). Load-bearing only if frames passed "
            "between the two looks; CursorTests.test_the_press_gate_is_its_own_look gives choose() a move_cursor that "
            "lies, but on a menu that takes input, so it cannot see this half."),
    "H4": (CAUGHT, "move_cursor() does not read the cursor (says it is there)",
           [("hands/menus.py", "        if ui.cursor == target:\n            return True\n", "        return True  # MUTANT H4\n")],
           ["YesNoTests.test_the_clock_question_opens_on_no_and_the_ai_says_yes",
            "CursorTests.test_a_menu_whose_cursor_starts_elsewhere",
            "CursorTests.test_move_cursor_waits_for_input_by_itself"]),
    "H9": (CAUGHT, "move_cursor() does not wait for the menu to take input",
           [("hands/menus.py", "        if not ui.accepts_input or ui.cursor is None:\n",
             "        if ui.cursor is None:  # MUTANT H9\n")],
           ["CursorTests.test_move_cursor_waits_for_input_by_itself"]),
    # ---- hands/menus.py: the keyboard
    "H4b": (CAUGHT, "type_name() does not move the cursor to the key (A on whatever key it is on)",
            [("hands/menus.py", "        if x != column:\n", "        if False:  # MUTANT H4b\n"),
             ("hands/menus.py", "        if y != row:\n", "        if False:  # MUTANT H4b\n")],
            ["KeyboardTests.test_types_rosa_from_the_opening_keyboard",
             "KeyboardTests.test_types_rosa_from_a_cursor_left_mid_name"]),
    "H5": (CAUGHT, "type_name() does not delete a wrong letter with B",
           [("hands/menus.py", "        if not name.startswith(text):\n", "        if False:  # MUTANT H5\n")],
           ["KeyboardTests.test_a_wrong_letter_is_deleted_with_b"]),
    "H5b": (CAUGHT, "type_name() does not put the cursor on OK (START) before the last A",
            [("hands/menus.py", "            if (x, y) != ok:\n", "            if False:  # MUTANT H5b\n")],
            ["KeyboardTests.test_types_rosa_from_the_opening_keyboard",
             "KeyboardTests.test_types_rosa_from_a_cursor_left_mid_name"]),
    "H5c": (REDUNDANT, "type_name()'s gate on OK does not re-check the cursor is on OK",
            [("hands/menus.py", " and ui.text == name and ui.cursor_xy == ok:\n", " and ui.text == name:  # MUTANT H5c\n")],
            "the check right above it saw the cursor on OK one 'think' pause earlier, and the keyboard's cursor moves "
            "only as the result of a press (src/naming_screen.c: every SetCursorPos caller is the D-pad's "
            "HandleDpadMovement, SELECT's page turn, START's MoveCursorToOKButton, or MainState_MoveToOKButton after "
            "the A that fills the name): the AI pressed nothing during its own pause. Load-bearing only if the cursor "
            "could move by itself."),
    # ---- hands/menus.py: the quantity and the clock
    "H7": (CAUGHT, "set_quantity() presses A without reading the quantity",
           [("hands/menus.py", "        if ui.quantity == count:\n", "        if True:  # MUTANT H7\n")],
           ["QuantityTests.test_reads_the_quantity"]),
    "H8a": (CAUGHT, "set_clock() tries to confirm without the outer time check (never moves the hand)",
            [_CLOCK_OUTER], ["ClockTests.test_sets_the_time_and_says_yes"]),
    "H8b": (REDUNDANT, "set_clock()'s gate does not re-check the time read",
            [_CLOCK_GATE],
            "the outer check read the wanted time one 'think' pause earlier, with the hand ON a minute (input "
            "accepted), and the hand moves only while Left/Right is held (src/wallclock.c "
            "Task_SetClock_HandleInput): the AI held nothing during its own pause. Load-bearing only if the clock "
            "could turn by itself."),
    "H8": (CAUGHT, "set_clock() confirms without reading the time at all (both checks)",
           [_CLOCK_OUTER, _CLOCK_GATE], ["ClockTests.test_sets_the_time_and_says_yes"]),
    # ---- hands/pad.py
    "HP": (CAUGHT, "the pad presses without a gate",
           [("hands/pad.py", "        if not gate:\n            raise PadError(f\"a press of {button} without a gate ({why})\")\n",
             "        pass  # MUTANT HP\n")],
           ["PadTests.test_a_press_needs_a_gate"]),
    "HB": (CAUGHT, "the reading delay is not bounded",
           [("hands/pad.py", "        return int(min(max(raw, pacing.read_base), pacing.read_max))\n",
             "        return int(raw)  # MUTANT HB\n")],
           ["PadTests.test_reading_delay_is_bounded_and_grows_with_the_text"]),
    # ---- host/eyes.py: the pointer range checks (the only host change of step 2)
    "HR": (CAUGHT, "a cartridge pointer is read without its range check",
           [("host/eyes.py", "    if not (ROM_START <= address and address + length <= ROM_END and length >= 0):\n",
             "    if False:  # MUTANT HR\n")],
           ["ScreenReadTests.test_a_followed_pointer_is_range_checked_before_any_read"]),
    "HE": (CAUGHT, "an EWRAM pointer is read without its range check",
           [("host/eyes.py", "    if not (EWRAM_START <= address and address + length <= EWRAM_END and length >= 0):\n",
             "    if False:  # MUTANT HE\n")],
           ["ScreenReadTests.test_a_followed_pointer_is_range_checked_before_any_read"]),
    # ---- STEP 2.1: the named busy reasons and the A-press classes
    "HS": (CAUGHT, "busy_reason() does not name the scene (the step-2 catch-all comes back)",
           [("hands/dialogue.py", "    if screen.scene is not None:\n", "    if False:  # MUTANT HS\n")],
           ["SceneTests.test_busy_names_what_it_watches"]),
    "HSo": (CAUGHT, "scene_of() never asks the main callback (back from the clock reads 'the wall clock', a map load has no name)",
            [("eyes/screens.py", "    if callback is not None and callback in SCENE_CALLBACKS:\n",
              "    if False:  # MUTANT HSo\n")],
            ["SceneTests.test_scene_lookup_order"]),
    "HK": (CAUGHT, "classify_a() takes any open menu as the one the gate names",
           [("gates/live_step2.py", '        return kind, re.search(rf" ui={re.escape(menu or \'\')}\\[", digest) is not None and "waits=A/B" not in digest\n',
             '        return kind, " ui=" in digest and "(busy)" not in digest and "waits=A/B" not in digest  # MUTANT HK\n')],
           ["PressKindTests.test_the_classes_and_their_faults"]),
    # ---- STEP 2.1, the step-2 review's items 1-6 (item 7 is revert_step11.py R5c)
    "HST": (CAUGHT, "advance() has no stall detector (item 1: an unknown prompt is watched for the whole budget)",
            [("hands/dialogue.py", "        if still > stall_limit(look):\n", "        if False:  # MUTANT HST\n")],
            ["StallTests.test_an_unknown_prompt_is_stuck_after_300_frames",
             "StallTests.test_a_scene_the_eyes_name_is_watched_longer"]),
    "HSTn": (CAUGHT, "one stall limit for every screen (a scene the eyes name is not watched longer)",
             [("hands/dialogue.py", "    return STALL_FRAMES_SCENE if look.screen.scene is not None else STALL_FRAMES\n",
               "    return STALL_FRAMES  # MUTANT HSTn\n")],
             ["StallTests.test_a_scene_the_eyes_name_is_watched_longer"]),
    "HSTk": (CAUGHT, "the stall count does not restart when the screen changes",
             [("hands/dialogue.py", "        if now != seen:\n            seen, still = now, 0\n",
               "        if seen is None:  # MUTANT HSTk\n            seen, still = now, 0\n")],
             ["StallTests.test_a_screen_that_changes_is_never_stuck"]),
    "HPV": (CAUGHT, "the evidence's CODE line carries no digest of the working tree (item 2)",
            [("gates/provenance.py", "    digest = tree_digest(diff, untracked)[:16]\n", "    digest = \"(none)\"  # MUTANT HPV\n")],
            ["ProvenanceTests.test_two_different_trees_give_two_lines"]),
    "HPF": (CAUGHT, "the pad counts a press's frames only once it has finished (item 3: the pre-2.1 count)",
            [("hands/pad.py", "            for _ in frames:\n                self.frames += 1\n                yield\n",
              "            passed = 0\n            for _ in frames:\n                passed += 1\n                yield\n"
              "            self.frames += passed  # MUTANT HPF\n")],
            ["PadFrameTests.test_frames_are_counted_as_they_pass"]),
    "HPI": (CAUGHT, "live_step2 does not compare the pad's frames with the instrument's real_frames (item 3)",
            [("gates/live_step2.py", "    run.check(pad_frames is not None and pad_frames == counters.get(\"real_frames\"),\n",
              "    run.check(True,  # MUTANT HPI\n")],
            ["PadFrameTests.test_the_driver_compares_the_pad_with_the_instrument"]),
    "HFD": (CAUGHT, "a running palette fade does not mean 'not taking input' (item 4)",
            [("eyes/screens.py", "    if ui is not None and ui.accepts_input and raw.get(\"fading\"):\n", "    if False:  # MUTANT HFD\n")],
            ["FadeTests.test_nothing_takes_input_while_a_fade_runs", "FadeTests.test_the_intro_waits_out_a_fade_before_start"]),
    "HFG": (CAUGHT, "the intro's START gate does not check the screen takes input (item 4)",
            [("skills/intro.py", "            if ui is not None and ui.kind == kind and ui.accepts_input:\n",
              "            if ui is not None and ui.kind == kind:  # MUTANT HFG\n")],
            ["FadeTests.test_the_intro_waits_out_a_fade_before_start"]),
    "HFW": (REDUNDANT, "the intro does not wait for the movie or the title to take input before its 'think' (item 4)",
            [("skills/intro.py", "            look = yield from _until_it_takes_input(hands, kind)\n",
              "            look = hands.look()  # MUTANT HFW\n")],
            "the START gate re-checks `accepts_input` on its own look after the 'think' (HFG is that check, and it is "
            "caught), so without the wait no START lands in a fade either: the AI only goes round the intro's loop once "
            "more per fade, spending one of its INTRO_MENU_STEPS turns. The wait stays: it names the stretch it watches "
            "('the intro_movie is not taking input yet') and keeps those turns for the menus."),
    "HGS": (CAUGHT, "the gender menu reads as CLOSED while Birch's sprites slide (found through item 6)",
            [("eyes/screens.py", "    for task, kind in sorted(UI_BUSY_TASKS.items()):  # STEP 2.1: on screen, not taking input\n",
              "    for task, kind in ():  # MUTANT HGS\n")],
            ["GenderSlideTests.test_girl_is_chosen_through_the_slide",
             "GenderSlideTests.test_the_slide_reads_as_the_menu_not_taking_input"]),
    "HNQ": (CAUGHT, "the name question is a SUBSTRING test again (item 5: 'Kai' is in 'So it's Kaiden?')",
            [("skills/intro.py", "    return match.group(\"name\") == name\n", "    return name in question  # MUTANT HNQ\n")],
            ["NameQuestionTests.test_the_name_is_compared_exactly",
             "NameQuestionTests.test_a_question_naming_another_name_is_answered_no"]),
    "HNK": (CAUGHT, "an unreadable name question is answered NO (item 5: the pre-2.1 re-typing loop)",
            [("skills/intro.py", "            agrees = typed if names is None else names\n",
              "            agrees = bool(names)  # MUTANT HNK\n")],
            ["NameQuestionTests.test_an_unreadable_question_relies_on_the_keyboard"]),
    "HF1": (CAUGHT, "the intro ignores a failed NEW GAME choice (item 6)",
            [("skills/intro.py", "            if not (yield from choose(hands, \"main_menu\", \"NEW GAME\", \"a new game\")):\n"
              "                return \"intro: NEW GAME could not be chosen on the main menu\"\n",
              "            yield from choose(hands, \"main_menu\", \"NEW GAME\", \"a new game\")  # MUTANT HF1\n")],
            ["SubSkillFailureTests.test_the_intro_reports_each_failure_at_once"]),
    "HF2": (CAUGHT, "the intro ignores a failed gender choice (item 6)",
            [("skills/intro.py", "            if not (yield from choose(hands, \"gender\", gender, f\"the personality chose {gender}\")):\n"
              "                return f\"intro: {gender} could not be chosen on the gender menu\"\n",
              "            yield from choose(hands, \"gender\", gender, f\"the personality chose {gender}\")  # MUTANT HF2\n")],
            ["SubSkillFailureTests.test_the_intro_reports_each_failure_at_once"]),
    "HF3": (CAUGHT, "the intro ignores a name it could not type (item 6)",
            [("skills/intro.py", "            if not typed:\n                return f\"intro: the name {name!r} could not be typed on the keyboard\"\n",
              "            pass  # MUTANT HF3\n")],
            ["SubSkillFailureTests.test_the_intro_reports_each_failure_at_once"]),
    "HF4": (CAUGHT, "the intro ignores a name question it could not answer (item 6)",
            [("skills/intro.py", "            if not (yield from answer_yes_no(hands, agrees, because)):\n"
              "                return \"intro: the name question could not be answered\"\n",
              "            yield from answer_yes_no(hands, agrees, because)  # MUTANT HF4\n")],
            ["SubSkillFailureTests.test_the_intro_reports_each_failure_at_once"]),
    "HF5": (CAUGHT, "the nurse ignores a yes/no it could not answer (item 6)",
            [("hands/menus.py", "            if not (yield from answer_yes_no(hands, True, f\"{why}: 'Would you like to rest your POKéMON?' YES\")):\n"
              "                return \"the nurse's yes/no could not be answered YES\"\n",
              "            yield from answer_yes_no(hands, True, f\"{why}: 'Would you like to rest your POKéMON?' YES\")  # MUTANT HF5\n")],
            ["SubSkillFailureTests.test_the_nurse_reports_a_failed_yes_no_at_once"]),
    "HF6": (CAUGHT, "the mart ignores a shop-menu choice it could not make (item 6)",
            [("hands/menus.py", "            if not (yield from choose(hands, \"mart_menu\", wanted, f\"{why}: the shop menu\")):\n"
              "                return f\"could not choose {wanted} in the shop menu\"\n",
              "            yield from choose(hands, \"mart_menu\", wanted, f\"{why}: the shop menu\")  # MUTANT HF6\n")],
            ["SubSkillFailureTests.test_the_mart_reports_a_failed_choice_at_once"]),
    "HF7": (CAUGHT, "the clock ignores a 'correct time?' it could not answer (item 6)",
            [("hands/menus.py", "            if not confirmed:\n", "            if False:  # MUTANT HF7\n")],
            ["SubSkillFailureTests.test_the_clock_reports_a_failed_yes_no_at_once"]),
}

#: Runs the copy's test_hands.py and prints one JSON line with every test id and its result.
DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_hands
suite = unittest.defaultTestLoader.loadTestsFromModule(test_hands)
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("test_hands.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_hands.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_step2_mutant_"))
    # the recorded screens (gates/fixtures/*.json) are copied: the tests replay them; the states (*.ss1) are not
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_step2_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    done = subprocess.run([sys.executable, str(root / "run_step2_tests.py")], cwd=str(root), env=env, capture_output=True,
                          timeout=TIMEOUT)
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
    out = ["AI PLAYER BUILD STEP 2 - MUTANT PROOF OF THE HANDS (gates/revert_step2.py)", f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
           f"code: {provenance(REPO)}",
           "Each mutant breaks ONE check of the real code in a copy; CAUGHT = its predicted tests fail; REDUNDANT = no test "
           "fails, and the reason the check is redundant alone is stated.", ""]
    ok_all = True
    counts = {CAUGHT: 0, REDUNDANT: 0}
    for name, (prediction, what, edits, expected) in MUTANTS.items():
        root = make_copy(edits)
        try:
            result, raw = run(root)
        finally:
            shutil.rmtree(root, ignore_errors=True)
        if result is None:
            ok = False
            line = f"[{name}] NO RESULT: {raw[-1500:]}"
        else:
            bad = result["bad"]
            ran_copy = root.name in result["module"]
            failing = {t: bad[t] for t in sorted(bad)}
            if prediction == CONTROL:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] CONTROL, the unchanged copy: {result['ran']} tests, failing {sorted(bad) or 'none'} "
                        f"(ran the copy: {ran_copy}) -> {'PASS' if ok else 'FAIL'}")
            elif prediction == CAUGHT:
                caught = [t for t in expected if t in bad]
                ok = ran_copy and caught == expected
                line = (f"[{name}] BROKEN: {what}. Predicted CAUGHT by {expected}. The copy ran {result['ran']} tests "
                        f"({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {failing} -> {'CAUGHT' if ok else 'NOT CAUGHT'}")
            else:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] BROKEN: {what}. Predicted REDUNDANT ALONE (no test fails), because {expected} The copy ran "
                        f"{result['ran']} tests ({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {failing or 'none'} -> "
                        f"{'NOT CAUGHT, as predicted (redundant alone)' if ok else 'PREDICTION WRONG'}")
            if ok and prediction in counts:
                counts[prediction] += 1
        ok_all &= ok
        print(line, flush=True)
        out.append(line)
    verdict = "PASS" if ok_all else "FAIL"
    summary = (f"{counts[CAUGHT]} mutants CAUGHT as predicted, {counts[REDUNDANT]} REDUNDANT ALONE as predicted (each with its reason), "
               f"of {len(MUTANTS) - 1}")
    out += ["", summary, f"OVERALL: {verdict}"]
    print(summary)
    print(f"OVERALL: {verdict}")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step2-REVERT.txt"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
