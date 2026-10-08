"""REVERT PROOF of AI-player build step 1.1: each fix, reverted in a COPY of the package, fails its test.

    py -3.12 ai_player/gates/revert_step11.py        (exit 0 = every prediction held)

WHY (CLAUDE.md session discipline rule 6, "fault-test every gate"; the step-0.1 mutant pattern): a test
that passes proves nothing until it is shown to FAIL when the thing it guards is broken. For every fix of
step 1.1 this script copies the real package to a temporary folder, applies ONE revert there (each anchor
must occur exactly once, or the run aborts), runs `gates/test_eyes.py` from the copy (the framework and
the learner's scorer from this repo, `AI_PLAYER_TEST_SUPPORT_ROOT`), and checks that the PREDICTED tests
fail. The unchanged copy (R0) must pass every test, so a failure means the revert, not the copy.
Each revert restores the PRE-FIX behaviour (quoted from the step-1 code where it existed). The live
reverts of the host-side fixes are `gates/live_step1.py` arms WARP (finding 4) and SW (finding 6).
Evidence: `ai_player/evidence/<date>-step11-REVERT.txt`.
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
TIMEOUT = 300

#: name -> (finding, what the revert restores, [(file, anchor, replacement)], tests that MUST fail).
REVERTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str]]] = {
    "R0": ("control", "nothing: the unchanged copy", [], []),
    "R1": ("1 Wally", "a [CATCH] on gBattleOutcome == Caught alone (the step-1 rule: `if outcome == \"Caught\":`)",
           [("memory_log.py", "        if not new:\n", "        if False:  # MUTANT R1: a catch on the outcome alone\n")],
           ["CatchTests.test_wally_tutorial_is_not_a_player_catch",
            "CatchTests.test_someone_elses_pokemon_is_not_the_players_catch"]),
    "R2a": ("2 stale foe", "the foe of the battle's FIRST look (the step-1 `battle = start.battle`)",
            [("memory_log.py", "                record[\"latest\"] = observation  # the refresh: the first look can show the previous battle's foe\n",
              "                pass  # MUTANT R2a: no refresh\n")],
            ["BattleLineTests.test_the_foe_is_refreshed_on_every_in_battle_look"]),
    "R2b": ("2 InProgress", "end at the first look out of the battle screen, whatever gBattleOutcome says",
            [("memory_log.py", "        if record is None or observation.screen.in_battle or observation.last_battle_outcome == 0:\n",
              "        if record is None or observation.screen.in_battle:  # MUTANT R2b\n")],
            ["BattleLineTests.test_no_result_no_end_and_never_in_progress"]),
    "R3a": ("3 foe HP", "the foe's exact HP numbers",
            [("host/eyes.py", "hp=hp if own else None, max_hp=max_hp if own else None,", "hp=hp, max_hp=max_hp,  # MUTANT R3a\n           ")],
            ["PerceptionTests.test_a_foe_is_seen_as_a_person_sees_it"]),
    "R3b": ("3 foe moves", "every move of the foe, used or not",
            [("host/eyes.py", "for slot in mon.moves if slot is not None and (own or foe_move_seen(slot.pp, slot.total_pp))",
              "for slot in mon.moves if slot is not None  # MUTANT R3b\n")],
            ["PerceptionTests.test_a_foe_is_seen_as_a_person_sees_it"]),
    "R3c": ("3 trainer label", "the step-1 rule: a person whose template has a trainer type is a \"trainer\"",
            [("eyes/view.py", "def object_kind(graphics_id: int) -> str:", "def object_kind(graphics_id: int, is_trainer: bool) -> str:"),
             ("eyes/view.py", "    return GFX_KINDS.get(graphics_id, \"npc\")", "    return GFX_KINDS.get(graphics_id, \"trainer\" if is_trainer else \"npc\")"),
             ("eyes/view.py", "\"item_ball\": \"o\", \"npc\": \"n\",", "\"item_ball\": \"o\", \"trainer\": \"T\", \"npc\": \"n\","),
             ("host/eyes.py", "kind=object_kind(event.graphics_id),", "kind=object_kind(event.graphics_id, event.trainer_type != \"None\"),")],
            ["PerceptionTests.test_every_person_is_an_npc"]),
    "R3d": ("3 secret id", "the full 32-bit OT id (visible | secret << 16)",
            [("host/eyes.py", "ot_id=visible_id(raw.ot_id)", "ot_id=raw.ot_id")],
            ["PerceptionTests.test_ids_are_the_visible_16_bits"]),
    "R4": ("4 warp", "the object's tile always (the step-1 position)",
           [("eyes/view.py", "    return object_xy if object_xy == saved_xy else None", "    return object_xy  # MUTANT R4")],
           ["SettlingTests.test_the_rule"]),
    # R4x / R4y: PARTIAL reverts (added after the step-2 verifier's V4: x compared, y ignored, passed every test
    # while the only negative case differed in x). Each compares ONE coordinate; each must be caught.
    "R4x": ("4 warp, x only", "a rule that compares x and ignores y (the verifier's V4)",
            [("eyes/view.py", "    return object_xy if object_xy == saved_xy else None",
              "    return object_xy if object_xy[0] == saved_xy[0] else None  # MUTANT R4x")],
            ["SettlingTests.test_the_rule"]),
    "R4y": ("4 warp, y only", "a rule that compares y and ignores x",
            [("eyes/view.py", "    return object_xy if object_xy == saved_xy else None",
              "    return object_xy if object_xy[1] == saved_xy[1] else None  # MUTANT R4y")],
            ["SettlingTests.test_the_rule"]),
    "R5a":("5 None vs ()", "an unread party counts as an EMPTY one (the step-1 `party=tuple(party or ())`)",
            [("memory_log.py", "        if observation.party is not None:\n            self._last_party = observation.party\n",
              "        self._last_party = observation.party if observation.party is not None else ()  # MUTANT R5a\n")],
            ["PartyNoneTests.test_an_unread_party_is_not_an_empty_one_for_the_starter"]),
    "R5b": ("5 dest by count", "the step-1 `dest = \"party\" if len(observation.party) > len(start.party) else \"box\"`",
            [("memory_log.py", "        dest = owned_after[pid] if pid is not None else \"?\"\n",
              "        dest = \"party\" if len(observation.party or ()) > len(start.party or ()) else \"box\"  # MUTANT R5b\n")],
            ["CatchTests.test_dest_is_by_pid_even_when_the_first_look_could_not_read_the_party"]),
    # R5c: STEP 2.1 (the step-2 verifier's weak proof, its V3): the HOST half of finding 5 had no test that failed on
    # its revert. Now PartyNoneTests runs the host's own `_party` on a fake emulator memory.
    "R5c": ("5 torn slot (host)", "the host returns the slots it could read when one is torn (a party one Pokemon short)",
            [("host/eyes.py", "        return None if torn else party\n", "        return party  # MUTANT R5c\n")],
            ["PartyNoneTests.test_a_torn_slot_makes_the_whole_party_none"]),
    "R6": ("6 script wait", "neither the status nor the mode checked: a finished script's leftover WaitForAorBPress reads as "
                            "waiting (each check alone refuses it; the live arm SW-X1 removes both too)",
           [("eyes/view.py", "    return status != SCRIPT_CONTEXT_SHUTDOWN and mode == \"Native\" and native_function == _WAIT_FOR_BUTTON_NATIVE",
             "    return native_function == _WAIT_FOR_BUTTON_NATIVE  # MUTANT R6")],
           ["ScriptWaitTests.test_the_rule"]),
}

#: Runs the copy's test_eyes.py and prints one JSON line with every test id and its result.
DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_eyes
suite = unittest.defaultTestLoader.loadTestsFromModule(test_eyes)
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("test_eyes.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_eyes.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_step11_revert_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "fixtures"))
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"revert anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_step11_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    done = subprocess.run([sys.executable, str(root / "run_step11_tests.py")], cwd=str(root), env=env, capture_output=True,
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
    out = [f"AI PLAYER BUILD STEP 1.1 - REVERT PROOF (gates/revert_step11.py)", f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
           f"code: {provenance(REPO)}", ""]
    ok_all = True
    for name, (finding, what, edits, must_fail) in REVERTS.items():
        root = make_copy(edits)
        try:
            result, raw = run(root)
        finally:
            shutil.rmtree(root, ignore_errors=True)
        if result is None:
            ok = False
            line = f"[{name}] finding {finding}: NO RESULT: {raw[-1500:]}"
        else:
            bad = result["bad"]
            ran_copy = root.name in result["module"]  # the copy's own temporary folder (8.3 names differ in full paths)
            if name == "R0":
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] CONTROL, the unchanged copy: {result['ran']} tests, failing {sorted(bad) or 'none'} "
                        f"(ran the copy: {ran_copy}) -> {'PASS' if ok else 'FAIL'}")
            else:
                caught = [t for t in must_fail if t in bad]
                ok = ran_copy and caught == must_fail
                line = (f"[{name}] finding {finding}: REVERTED to {what}. Predicted to fail: {must_fail}. The copy ran "
                        f"{result['ran']} tests ({'the copy' if ran_copy else 'NOT THE COPY'}); failing: "
                        f"{ {t: bad[t] for t in sorted(bad)} } -> {'CAUGHT' if ok else 'NOT CAUGHT'}")
        ok_all &= ok
        print(line, flush=True)
        out.append(line)
    verdict = "PASS" if ok_all else "FAIL"
    out += ["", f"OVERALL: {verdict}"]
    print(f"OVERALL: {verdict}")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step11-REVERT.txt"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
