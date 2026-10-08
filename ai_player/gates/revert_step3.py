"""MUTANT PROOF of AI-player build step 3 (the world model and the navigator): each rule of the REAL code, broken in a
COPY of the package, fails its predicted test of `gates/test_world.py`, or is documented as REDUNDANT ALONE with the
reason.

    py -3.12 ai_player/gates/revert_step3.py        (exit 0 = every prediction held)

WHY (CLAUDE.md session discipline rule 6): `test_world.py`'s fault halves patch a value (the crop off, an unknown tile
priced like a known one, a bump not remembered). That shows the tests CAN fail, not that each rule in the real code
carries weight. As `revert_step2.py` does for the hands, this copies the package to a temporary folder (no states, no
evidence), applies ONE mutant's edits there (each anchor must occur exactly once, or the run aborts), runs
`gates/test_world.py` from the copy (the framework from this repo: `AI_PLAYER_TEST_SUPPORT_ROOT`), and checks the
PREDICTION: CAUGHT (every named test fails) or REDUNDANT (no test fails; the reason is written next to it). The
unchanged copy (W0) must pass every test.
Evidence: `ai_player/evidence/<date>-step3-REVERT.txt`.
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
from ai_player.gates.provenance import provenance  # noqa: E402

EVIDENCE = REPO / "ai_player" / "evidence"
TIMEOUT = 900

CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"

_EXCLUDED = ("brain/navigator.py", "                if self.is_excluded(target):\n",
             "                if False:  # MUTANT W12: a chosen target already found unreachable is tried again\n")
_STILL = ("brain/navigator.py", "            if still > STILL_DECISIONS:\n",
          "            if False:  # MUTANT W13: no guard against decisions that let no frame pass\n")

#: name -> (prediction, the rule that is broken, [edits], tests that MUST fail (CAUGHT) or the reason (REDUNDANT)).
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str] | str]] = {
    "W0": (CONTROL, "nothing: the unchanged copy", [], []),
    "W1": (CAUGHT, "a ledge may be entered from any side (`step_from`: the jump direction not checked)",
           [("brain/navigator.py", "        if fact.ledge != direction:\n            return None\n",
             "        if False:  # MUTANT W1\n            return None\n")],
           ["PlannerTests.test_walls_people_ledges_and_warps"]),
    "W2": (CAUGHT, "a warp or a door is a walkable tile (walked THROUGH on the way somewhere: `TileFact.walkable`)",
           [("world/memory.py", "        return not (self.blocked or self.water or self.ledge is not None or self.warp or self.door)\n",
             "        return not (self.blocked or self.water or self.ledge is not None)  # MUTANT W2\n")],
           ["PlannerTests.test_walls_people_ledges_and_warps"]),
    "W3": (CAUGHT, "an unseen tile costs what a seen one does (`step_from`: UNKNOWN_COST -> 1)",
           [("brain/navigator.py", "        return (nxt, UNKNOWN_COST) if allow_unknown else None\n",
             "        return (nxt, 1.0) if allow_unknown else None  # MUTANT W3\n")],
           ["PlannerTests.test_unknown_is_optimistic_but_dearer"]),
    "W4": (CAUGHT, "a bump is not remembered (`WorldMemory.learn_bump`)",
           [("world/memory.py", "        memory.bumped[tile] = info\n", "        pass  # MUTANT W4\n")],
           ["WalkTests.test_a_hidden_wall_is_bumped_once_and_avoided"]),
    "W5": (CAUGHT, "novelty RESETS the intent's frame budget (design draft §10.4 forbids it)",
           [("brain/navigator.py", "            novel = novelty.update(look)\n",
             "            novel = novelty.update(look)\n            if novel:\n                start = pad.frames  # MUTANT W5\n")],
           ["IntentTests.test_the_budget_is_not_reset_by_novelty"]),
    "W6": (CAUGHT, "no ping-pong rule (one warp used again and again with nothing new)",
           [("brain/navigator.py", "                if len(frames) >= PINGPONG_USES and novelty.last <= frames[1]:\n",
             "                if False:  # MUTANT W6\n")],
           ["IntentTests.test_a_stairs_ping_pong_is_stuck_at_the_third_use"]),
    "W7": (CAUGHT, "no novelty window (nothing new for ever is not stuck)",
           [("brain/navigator.py", "            if look.frame - novelty.last >= intent.novelty_window:\n",
             "            if False:  # MUTANT W7\n")],
           ["IntentTests.test_nothing_new_is_stuck_within_the_window"]),
    "W8": (CAUGHT, "a map change is a connection whatever the looks between showed (no fade -> warp rule)",
           [("world/memory.py", "        if last.between:\n", "        if False:  # MUTANT W8\n")],
           ["ExitTests.test_stairs_mat_and_the_warp_graph"]),
    "W9": (CAUGHT, "watching a warp does not stop when the map has changed (`settle` waits for the player to be free, "
                   "through a scene that starts on arrival: the case that made the ping-pong invisible)",
           [("brain/navigator.py", "                    or self.world.current != key):\n", "                    ):  # MUTANT W9\n")],
           ["IntentTests.test_a_stairs_ping_pong_is_stuck_at_the_third_use"]),
    "W10": (CAUGHT, "flee presses A without reading the cursor on RUN",
            [("skills/flee.py", "        if ui.cursor == index:\n", "        if True:  # MUTANT W10\n")],
            ["FleeTests.test_run_is_reached_by_reading_the_cursor"]),
    "W11": (CAUGHT, "flee does not recognise a trainer battle (it tries to RUN from it)",
            [("skills/flee.py", "            if battle is not None and battle.kind == \"trainer\":\n",
              "            if False:  # MUTANT W11\n")],
            ["FleeTests.test_a_trainer_battle_is_out_of_scope_and_nothing_is_pressed"]),
    "W12": (CAUGHT, "a chosen target already found unreachable is tried again (each try begins with a 'deciding where to "
                    "go' pause, so frames pass and the run is not a hang: it walks nowhere until its budget, and never says "
                    "it is stuck)",
            [_EXCLUDED], ["IntentTests.test_an_unreachable_errand_is_stuck_not_a_loop"]),
    "W13": (REDUNDANT, "the guard against decisions that let no frame pass, alone",
            [_STILL],
            "every decision path in `Navigator.run` today lets a frame pass or ends the intent (a new target is followed by "
            "a thinking pause; an unreachable one is excluded and then refused by W12's check). The guard is a backstop "
            "for a future path that does neither; nothing reaches it now."),
    "W14": (CAUGHT, "Story's taste for roads gone (`WEIGHTS['Story'].road` 4.0 -> 0.5)",
            [("brain/explore.py", "    \"Story\": Weights(frontier=1.0, road=4.0,", "    \"Story\": Weights(frontier=1.0, road=0.5,")],
            ["ExploreTests.test_personalities"]),
    "W15": (CAUGHT, "Trainer's pull toward people gone (`WEIGHTS['Trainer'].people` 1.5 -> 0)",
            [("brain/explore.py", "grass=2.5, people=1.5,", "grass=2.5, people=0.0,")],
            ["ExploreTests.test_trainer_goes_toward_people"]),
    "W16": (CAUGHT, "roaming may step straight back to the tile it came from",
            [("skills/roam_train.py", "        forward = [o for o in options if o[2] != previous]\n",
              "        forward = options  # MUTANT W16\n")],
            ["RoamTests.test_roaming_covers_and_never_spins"]),
    "W17": (CAUGHT, "the way just come in is worth its 'something left there' bonus while this map has something to see "
                    "(the lab -> town -> lab ping-pong of the seed sweep's Catcher seed 1)",
            [("brain/explore.py", "        if target == came_from and here_left:\n", "        if False:  # MUTANT W17\n")],
            ["ExploreTests.test_not_straight_back_where_it_came_from"]),
    "W18": (CAUGHT, "a target excluded on one map is excluded on every map (the key without the map)",
            [("brain/navigator.py", "        self.excluded.add(f\"{self.world.current}|{target.key}\")\n",
              "        self.excluded.add(target.key)  # MUTANT W18\n"),
             ("brain/navigator.py", "        return f\"{self.world.current}|{target.key}\" in self.excluded\n",
              "        return target.key in self.excluded  # MUTANT W18\n")],
            ["ExploreTests.test_an_exclusion_belongs_to_one_map"]),
    "W19": (CAUGHT, "roaming does not wait for a person in its only way on (it turns straight back: a spin)",
            [("skills/roam_train.py", "        if not forward and blocked and waited < PERSON_WAIT:\n",
              "        if False:  # MUTANT W19\n")],
            ["RoamTests.test_a_person_in_the_way_is_waited_for"]),
    # ---- the step-3 verifier's weak proofs (2026-10-08)
    "W20": (CAUGHT, "experience gained is not novelty (design draft §10.4 lists XP; the verifier found it uncounted)",
            [("brain/navigator.py", "            if gained:\n                new.append(f\"experience gained ({len(gained)} Pokemon)\")\n",
              "            if False:  # MUTANT W20\n                new.append(f\"experience gained ({len(gained)} Pokemon)\")\n")],
            ["NoveltyTests.test_experience_gained_is_progress"]),
    "W21": (CAUGHT, "a training step a battle began on is not counted as pressed (the verifier's 150 'tried' for 163 "
                    "roam presses)",
            [("skills/roam_train.py", "            report.interrupted += 1\n",
              "            report.interrupted += 1\n            report.attempts -= 1  # MUTANT W21\n")],
            ["RoamTests.test_steps_that_ran_into_a_battle_are_counted"]),
    "W22": (CAUGHT, "a training step a battle began on is never resolved (a step that DID move the player into the battle "
                    "is lost from the steps, the path and 'the tile it came from')",
            [("skills/roam_train.py", "        if pending is not None:\n", "        if False:  # MUTANT W22\n")],
            ["RoamTests.test_steps_that_ran_into_a_battle_are_counted"]),
    "W23": (CAUGHT, "no whim among equals: always the top score (the verifier: seeds 3 and 7 chose the same targets)",
            [("brain/explore.py", "        return pick(found, nav.rng)\n",
              "        return max(found, key=lambda target: (target.score, target.tile))  # MUTANT W23\n")],
            ["ExploreTests.test_seeds_choose_different_ways_on_the_same_town"]),
    # ---- the step-3 verifier's second round (2026-10-08)
    "W24": (CAUGHT, "the navigator does not TELL a novelty that is not a place (no `[AI-WORLD] novelty at f...` line: a live run "
                    "could not show which novelty moved the clock)",
            [("brain/navigator.py", "            if novelty.notable:\n", "            if False:  # MUTANT W24\n")],
            ["NoveltyTests.test_the_navigator_tells_the_experience_and_the_clock_it_moved"]),
    "W25": (CAUGHT, "the experience novelty is told without its IDENTITY (no PID, no totals: nothing to hold against the game's "
                    "own party)",
            [("brain/navigator.py", "                self.notable.append(\"experience gained (\" + \", \".join(\n"
                                    "                    f\"PID {pid:08x}: {self.experience[pid]} -> {experience[pid]}\" for pid in gained) + \")\")\n",
              "                self.notable.append(f\"experience gained ({len(gained)} Pokemon)\")  # MUTANT W25\n")],
            ["NoveltyTests.test_the_notable_novelty_names_the_pid_and_both_totals",
             "NoveltyTests.test_the_navigator_tells_the_experience_and_the_clock_it_moved"]),
    "W26": (CAUGHT, "game_answer's arrival takes no exit step after a door or stairs (STUCK's end tile would be the stairs)",
            [("gates/game_answer.py", "    dx, dy = EXIT_STEP.get(behaviour, (0, 0))\n", "    dx, dy = (0, 0)  # MUTANT W26\n")],
            ["GameAnswerTests.test_the_exit_step"]),
    "W27": (CAUGHT, "the ROAM grader calls a press pre-empted although the player TURNED (the facing not checked)",
            [("gates/live_step3.py",
              "            \"turned_before_the_battle\": any(facing_of(r) not in (None, facing_of(press)) for r in between + ([battle] if battle else []))}\n",
              "            \"turned_before_the_battle\": False}  # MUTANT W27\n")],
            ["GraderTests.test_a_preempted_press_and_three_that_were_not"]),
    "W28": (CAUGHT, "an INCONCLUSIVE game answer passes on the loaded map header alone (STUCK's weak proof)",
            [("gates/live_step3.py", "        if not arrival:\n            run.check(False, ",
              "        if not arrival:\n            run.check(bool(a.get(\"loaded_header_is_claimed_map\")),  # MUTANT W28\n                      ")],
            ["GraderTests.test_an_inconclusive_answer_with_nothing_else_fails"]),
    "W29": (CAUGHT, "a walking answer agrees with no trial predicting a step (a '0 steps, then a wall' line agrees with a "
                    "player who cannot move: found by the second round's graded run on STUCK's fault claim)",
            [("gates/game_answer.py", " and loaded_ok and any(t[\"predicted\"][\"steps\"] > 0 for t in trials)\n",
              " and loaded_ok  # MUTANT W29\n")],
            ["GameAnswerTests.test_a_walking_answer_needs_a_step"]),
}

DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_world
suite = unittest.defaultTestLoader.loadTestsFromModule(test_world)
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("test_world.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_world.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_step3_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_step3_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_step3_tests.py")], cwd=str(root), env=env, capture_output=True,
                              timeout=TIMEOUT)
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
    out = ["AI PLAYER BUILD STEP 3 - MUTANT PROOF OF THE WORLD MODEL AND THE NAVIGATOR (gates/revert_step3.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
           f"code: {provenance(REPO)}",
           "Each mutant breaks ONE rule of the real code in a copy; CAUGHT = its predicted tests of gates/test_world.py fail; "
           "REDUNDANT = no test fails, and the reason the rule is redundant alone is stated.", ""]
    ok_all = True
    counts = {CAUGHT: 0, REDUNDANT: 0}
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    for name, (prediction, what, edits, expected) in MUTANTS.items():
        if only is not None and name not in only:
            continue
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
                # a test with sub-tests fails under its name + " (<the sub-test's parameters>)"
                caught = [t for t in expected if any(b == t or b.startswith(t + " (") for b in bad)]
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
    path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step3-REVERT.txt"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
