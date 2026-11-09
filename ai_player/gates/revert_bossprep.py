"""MUTANT PROOF of boss preparation BP-1 (USER RULING 58, 2026-11-09): each rule of the real code, broken in a COPY of the
package, fails its predicted test of `gates/test_bossprep.py`, or is documented as REDUNDANT ALONE (offline) with the reason.

    py -3.12 -B ai_player/gates/revert_bossprep.py [M1,M2] [--workers N]       (exit 0 = every prediction held)

The `revert_step4.py` pattern: copy the package (no states, no evidence), apply ONE mutant's edits (each anchor must occur
exactly once, or the run aborts; `gates/check_anchors.py` checks every anchor in seconds), run `gates/test_bossprep.py` from
the copy, check the PREDICTION: CAUGHT (every named test fails) or REDUNDANT (no test fails; the reason stated). The
unchanged copy (P0) must pass every test. The spec's mutants (section 5.2) keep their names; the wiring mutants (a call
deleted: `gates/call_census.py` counts them) are named for what they delete. The predictions were written and this file's
sha256 recorded (s53/bp1/STATE.md) BEFORE its first run. Evidence: `ai_player/evidence/<date>-bossprep-REVERT.txt`.
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
TIMEOUT = 900
CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"
BP, GOALS, BATTLE, ORDER, EYES = ("brain/bossprep.py", "brain/goals.py", "brain/battle.py", "hands/party_order.py",
                                  "host/eyes.py")

#: name -> (prediction, the rule that is broken, [edits], tests that MUST fail (CAUGHT) or the reason (REDUNDANT)).
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str] | str]] = {
    "P0": (CONTROL, "nothing: the unchanged copy", [], []),
    # ---- T1 the two halves
    "types_only": (CAUGHT, "the attack half valued with no types (every matchup x1, no STAB)",
                   [(BP, "    battle_faults = BattleFaults(ignore_types=True) if faults.types_only else BattleFaults()\n",
                     "    battle_faults = BattleFaults(ignore_types=True)  # MUTANT types_only\n")],
                   ["TwoHalvesTests.test_dustox_l18_against_brawly", "VerdictClassTests.test_the_calibration_runs"]),
    "moves_only": (CAUGHT, "the threat half ignored (a damaging boss move does 0 but fixed damage)",
                   [(BP, "    if faults.moves_only:\n        return 0\n", "    if True:  # MUTANT moves_only\n        return 0\n")],
                   ["VerdictClassTests.test_the_calibration_runs", "PlanTests.test_c1_options"]),
    "fp_always": (CAUGHT, "Focus Punch never fails (hit first, it still lands)",
                  [(BP, "    if fact.effect == \"FOCUS_PUNCH\" and member_damaging and not faults.fp_always:\n",
                    "    if False:  # MUTANT fp_always\n")],
                  ["TwoHalvesTests.test_fault_fp_always"]),
    "name_tie": (CAUGHT, "the boss's tied moves by NAME (the spec script's tie-break), not the faster one",
                 [(BP, "            dmg_in, p_foe, _used = max(options, key=(lambda o: (o[0], o[2])) if faults.name_tie else None)\n",
                   "            dmg_in, p_foe, _used = max(options, key=lambda o: (o[0], o[2]))  # MUTANT name_tie\n")],
                 ["VerdictClassTests.test_the_calibration_runs", "NameTieTests.test_the_spec_numbers_with_the_name_tie_break"]),
    # ---- T2 fixed damage
    "fixed_resisted": (CAUGHT, "Seismic Toss scaled by the type chart (M1's fault)",
                       [(BP, "        if faults.fixed_resisted:\n", "        if True:  # MUTANT fixed_resisted\n")],
                       ["FixedDamageTests.test_seismic_toss_is_the_level", "PlanTests.test_c1_options"]),
    "no_immunity": (CAUGHT, "fixed damage hits a type immune to its move's type",
                    [(BP, "        if mult == 0 and not faults.no_immunity:\n", "        if False:  # MUTANT no_immunity\n")],
                    ["FixedDamageTests.test_seismic_toss_is_the_level"]),
    # ---- T3 the classes
    "strongest_level": (CAUGHT, "today's rule (the strongest level against the top level + the margin) as the verdict",
                        [(BP, "    if faults.strongest_level:\n", "    if True:  # MUTANT strongest_level\n")],
                        ["VerdictClassTests.test_the_calibration_runs", "VerdictClassTests.test_fault_strongest_level_is_todays_rule"]),
    "no_sitrus": (CAUGHT, "the boss's held berry ignored (RULING 44's item unread)",
                  [(BP, "        berry = None if faults.no_sitrus else BERRY_HP.get(boss.held_item or \"\")\n",
                    "        berry = None  # MUTANT no_sitrus\n")],
                  ["VerdictClassTests.test_fault_no_sitrus", "VerdictClassTests.test_the_calibration_runs"]),
    "flail_flat": (CAUGHT, "Reversal at its printed power (1), not by its user's HP",
                   [(BP, "    if fact.effect == \"FLAIL\" and not faults.flail_flat:\n", "    if False:  # MUTANT flail_flat\n")],
                   ["TwoHalvesTests.test_the_verdict_powers", "VerdictClassTests.test_fault_no_sitrus"]),
    # ---- T4 projection
    "no_projection": (CAUGHT, "a member at a higher level keeps its species and moves (M3's fault)",
                      [(BP, "    if faults.no_projection:\n", "    if True:  # MUTANT no_projection\n")],
                      ["ProjectionTests.test_wurmple_and_cascoon", "PlanTests.test_c1_options"]),
    # ---- T5 the plan
    "eligible_cocoon": (CAUGHT, "a member with no damaging move may be raised (a Harden-only cocoon)",
                        [(BP, "        if not _damaging(member) and not faults.eligible_cocoon:\n",
                          "        if False:  # MUTANT eligible_cocoon\n")],
                        ["PlanTests.test_c1_options"]),
    "cost_by_level_gap": (CAUGHT, "the cost is the levels to gain, not their squares",
                          [(BP, "                cost = level - member.level if faults.cost_by_level_gap else level * level - member.level * member.level\n",
                            "                cost = level - member.level  # MUTANT cost_by_level_gap\n")],
                          ["PlanTests.test_c1_options"]),
    "rechoose": (CAUGHT, "no commit (m10): an active plan is chosen again at every verdict run that reads NOT READY",
                 [(GOALS, "            return\n        if record[\"status\"] != \"none\" or verdict.cls != NOT_READY:\n            return\n",
                   "        if verdict.cls != NOT_READY:  # MUTANT rechoose\n            return\n")],
                 ["PlanTests.test_fault_rechoose_the_plan_is_committed"]),
    # ---- T6 the trainee rule (M4)
    "rest_by_strongest": (CAUGHT, "the raise's rest keyed on the strongest (today's training_rest), not the trainee",
                          [(BP, "    trainee = next((m for m in look.party or () if m.pid == pid and not m.is_egg), None)\n",
                            "    trainee = None  # MUTANT rest_by_strongest\n")],
                          ["TraineeRuleTests.test_the_rest_is_the_trainees",
                           "TraineeRuleTests.test_the_roam_hooks_install_the_trainee_rest"]),
    "switch_in_raise": (CAUGHT, "a raise battle switches to a stronger member (the experience split)",
                        [(BATTLE, "        if self.purpose == \"raise\":\n            return None  # (BP-1, M4)",
                          "        if False:\n            return None  # MUTANT switch_in_raise (BP-1, M4)")],
                        ["TraineeRuleTests.test_no_switch_while_raising"]),
    "catch_in_raise": (CAUGHT, "a raise battle throws a ball at a species it wants",
                       [(BATTLE, "            self.memory.want_catch = self.wishes[foe.species] and self.purpose != \"raise\"\n",
                         "            self.memory.want_catch = self.wishes[foe.species]  # MUTANT catch_in_raise\n")],
                       ["TraineeRuleTests.test_no_catch_while_raising"]),
    "raise_travels": (CAUGHT, "a raise battle run from as a travel's, not a training's",
                      [(BATTLE, "        if self.purpose in (\"train\", \"raise\"):  # (BP-1) raising runs exactly as training does\n",
                        "        if self.purpose == \"train\":  # MUTANT raise_travels\n")],
                      ["TraineeRuleTests.test_a_raise_runs_as_training_does"]),
    "no_raise_rest": (CAUGHT, "the trainee's rest never installed in the raise's roam (the hook deleted)",
                      [(GOALS, "            nav.battle_rest = raise_rest\n", "            pass  # MUTANT no_raise_rest\n")],
                      ["TraineeRuleTests.test_the_roam_hooks_install_the_trainee_rest"]),
    "no_raise_purpose": (CAUGHT, "a raise goal's battles fought with purpose train (no M4 rules)",
                         [(GOALS, "        self.mind.purpose = (\"raise\" if goal.kind == \"raise\" else\n",
                           "        self.mind.purpose = (\"train\" if goal.kind == \"raise\" else  # MUTANT no_raise_purpose\n")],
                         ["TraineeRuleTests.test_a_raise_goal_is_played_by_the_raise_with_its_purpose"]),
    "no_raise_branch": (CAUGHT, "the runner never plays a raise goal (`_raise`'s call deleted)",
                        [(GOALS, "            return (yield from self._raise(goal, moved_on))\n",
                          "            pass  # MUTANT no_raise_branch\n")],
                        ["TraineeRuleTests.test_a_raise_goal_is_played_by_the_raise_with_its_purpose"]),
    # (added 2026-11-09 after the live A/B #112 found the stale first look; predictions re-hashed before the run)
    "stale_lead": (CAUGHT, "the raise battle's lead read on its FIRST look (the last battle's battler), not at the action menu",
                   [(BP, "        if ui is None or ui.kind != \"battle_action\":\n            return  # before the first action menu",
                     "        if False:\n            return  # MUTANT stale_lead: before the first action menu")],
                   ["TraineeRuleTests.test_the_raise_watch"]),
    "no_lead_first": (CAUGHT, "the raise does not put the trainee first (the hand's call deleted)",
                      [(GOALS, "            if not (yield from lead_with(hands, pid, f\"{goal.reason}: the trainee first\")):\n",
                        "            if False:  # MUTANT no_lead_first\n")],
                      ["TraineeRuleTests.test_the_raise_puts_the_trainee_first_or_ends"]),
    # ---- T7 the budget (M5)
    "no_bound": (CAUGHT, "the budget never spent: an endless grind",
                 [(GOALS, "        spent = spent_reason(record, personality)\n        trainee = next(",
                   "        spent = None  # MUTANT no_bound\n        trainee = next(")],
                 ["BudgetTests.test_a_spent_budget_ends_the_raise"]),
    "two_budgets": (CAUGHT, "step 5's training runs beside an active raise (two budgets, m11)",
                    [(GOALS, "        if fight_next and not self.train_off and not hurt and not self.raising_for(milestone.id):\n",
                      "        if fight_next and not self.train_off and not hurt:  # MUTANT two_budgets\n")],
                    ["BudgetTests.test_no_training_beside_an_active_raise"]),
    # ---- T8 persistence and the loss
    "not_persisted": (CAUGHT, "the record kept outside the game memory: a continue loses it",
                      [(GOALS, "        record = self.prep(boss_ms).setdefault(\"bp\", new_record()) if acts else None\n",
                        "        record = self.__dict__.setdefault(\"_lost\", {}).setdefault(boss_ms.id, new_record()) if acts else None  # MUTANT\n"),
                       (GOALS, "        prep = self.memory.fight_prep.get(milestone_id or \"\")\n        return prep.get(\"bp\") if prep else None\n",
                        "        return self.__dict__.get(\"_lost\", {}).get(milestone_id or \"\")  # MUTANT not_persisted\n")],
                      ["PersistenceTests.test_a_continue_keeps_the_record"]),
    "same_plan": (CAUGHT, "after a loss the failed plan may be chosen again",
                  [(GOALS, "        choice, how = choose_plan(rng, near_best(personality), found, record[\"failed\"])\n",
                    "        choice, how = choose_plan(rng, near_best(personality), found, ())  # MUTANT same_plan\n")],
                  ["PersistenceTests.test_a_loss_after_a_done_plan_chooses_another"]),
    "no_boss_lost": (CAUGHT, "a loss on the leader's gym never reaches the record (the call deleted)",
                     [(GOALS, "                self.manager.boss_lost(self.hands.last if self.hands.last is not None else self.hands.look())\n",
                       "                pass  # MUTANT no_boss_lost\n")],
                     ["PersistenceTests.test_a_loss_through_pursue"]),
    # ---- T9 the next boss, the scope
    "current_only": (CAUGHT, "the next leader only when the CURRENT milestone is its fight (today's fight_next)",
                     [(BP, "        if faults.current_only:\n            return None\n",
                       "        return None  # MUTANT current_only\n")],
                     ["NextBossTests.test_the_next_leader", "PlanTests.test_the_story_run_gets_a_raise_goal"]),
    "act_on_all": (CAUGHT, "every leader acted on (ACT_ON ignored)",
                   [(GOALS, "        acts = name in ACT_ON and named is boss_ms\n", "        acts = named is boss_ms  # MUTANT act_on_all\n")],
                   ["NextBossTests.test_act_on_all_would_raise_for_roxanne"]),
    "act_in_ch5": (CAUGHT, "acted on in chapter 5 (the next-named-fight guard deleted): chapters 1-5 change",
                   [(GOALS, "        acts = name in ACT_ON and named is boss_ms\n", "        acts = name in ACT_ON  # MUTANT act_in_ch5\n")],
                   ["NextBossTests.test_chapter_5_plays_as_before"]),
    "no_verdict_run": (CAUGHT, "the verdict never runs in a decision (its call deleted)",
                       [(GOALS, "        bp_plan = self.boss_prep(look, index) if has_party else None\n",
                         "        bp_plan = None  # MUTANT no_verdict_run\n")],
                       ["PlanTests.test_the_story_run_gets_a_raise_goal"]),
    "no_raise_goal": (CAUGHT, "the raise goal never chosen (its call deleted)",
                      [(GOALS, "            raised = self._raise_goal(look, world, bp_plan)\n", "            raised = None  # MUTANT no_raise_goal\n")],
                      ["PlanTests.test_the_story_run_gets_a_raise_goal"]),
    "no_lead_goal": (CAUGHT, "the trainee never put back in the lead on the gym (its call deleted)",
                     [(GOALS, "            relead = self._lead_goal(look, here_const, bp_plan)\n", "            relead = None  # MUTANT no_lead_goal\n")],
                     ["TraineeRuleTests.test_the_lead_goal_on_the_leaders_gym"]),
    # ---- T10 / T11
    "reorder_by_slot": (REDUNDANT, "the hand given the member's slot shifted by one",
                        [(ORDER, "    if not (yield from move_cursor(hands, \"party\", index, f\"{why}: {name}\")):\n",
                          "    if not (yield from move_cursor(hands, \"party\", index + 1, f\"{why}: {name}\")):  # MUTANT\n")],
                        "no offline test drives the field's party menu (it needs the game's screens); T10 kills it LIVE "
                        "(gates/probe_bossprep.py lead on a copy carrying this edit: s53/bp1 live mutants)."),
    "eyes_slot_id": (REDUNDANT, "the eyes read slotId while switching (the moving cursor is slotId2)",
                     [(EYES, "            slot = ids[1] if ids[2] == PARTY_ACTION_SWITCH else ids[0]\n",
                       "            slot = ids[0]  # MUTANT eyes_slot_id\n")],
                     "the eyes' memory read needs the framework; T10 kills it LIVE (probe_bossprep.py lead on a copy)."),
    "storage_read": (CAUGHT, "the verdict reads the PC boxes (m5)",
                     [(BP, "    for mon in look.party or ():\n        if mon.is_egg:\n",
                       "    for mon in (look.party or ()) + tuple(look.storage or ()):  # MUTANT storage_read\n        if mon.is_egg:\n")],
                     ["LoaderTests.test_no_box_and_no_hidden_name_in_bossprep"]),
    "loader_prefix": (CAUGHT, "a learnset move read with its MOVE_ prefix: no move maps",
                      [("knowledge/seasoned.py", "    return move_named(str(symbol).removeprefix(\"MOVE_\").replace(\"_\", \" \"))\n",
                        "    return move_named(str(symbol).replace(\"_\", \" \"))  # MUTANT loader_prefix\n")],
                      ["LoaderTests.test_every_learnset_move_and_evolution_target_maps", "ProjectionTests.test_wurmple_and_cascoon"]),
}

DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_bossprep
suite = unittest.defaultTestLoader.loadTestsFromModule(test_bossprep)
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("test_bossprep.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_bossprep.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_bossprep_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_bossprep_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_bossprep_tests.py")], cwd=str(root), env=env,
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
    out = ["AI PLAYER BOSS PREPARATION BP-1 - MUTANT PROOF (gates/revert_bossprep.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
           f"code: {provenance(REPO)}",
           "Each mutant breaks ONE rule of the real code in a copy; CAUGHT = its predicted tests of gates/test_bossprep.py "
           "fail; REDUNDANT = no test fails, and the reason the rule is redundant alone (offline) is stated.", ""]
    argv = list(sys.argv[1:])
    workers = 1
    if "--workers" in argv:
        at = argv.index("--workers")
        workers = max(1, int(argv[at + 1]))
        del argv[at:at + 2]
    only = set(argv[0].split(",")) if argv else None
    chosen = [(name, spec) for name, spec in MUTANTS.items() if only is None or name in only]

    def attempt(item):
        root = make_copy(item[1][2])
        try:
            return run(root) + (root,)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(attempt, chosen))
    ok_all = True
    counts = {CAUGHT: 0, REDUNDANT: 0}
    for (name, (prediction, what, edits, expected)), (result, raw, root) in zip(chosen, results):
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
                caught = [t for t in expected if any(b == t or b.startswith((t + " (", t + " [")) for b in bad)]
                ok = ran_copy and caught == expected
                line = (f"[{name}] BROKEN: {what}. Predicted CAUGHT by {expected}. The copy ran {result['ran']} tests "
                        f"({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {failing} -> {'CAUGHT' if ok else 'NOT CAUGHT'}")
            else:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] BROKEN: {what}. Predicted REDUNDANT ALONE, because {expected} The copy ran {result['ran']} "
                        f"tests; failing: {failing or 'none'} -> {'as predicted' if ok else 'PREDICTION WRONG'}")
            if ok and prediction in counts:
                counts[prediction] += 1
        ok_all &= ok
        print(line, flush=True)
        out.append(line)
    verdict = "PASS" if ok_all else "FAIL"
    summary = (f"{counts[CAUGHT]} mutants CAUGHT as predicted, {counts[REDUNDANT]} REDUNDANT ALONE as predicted, "
               f"of {len(MUTANTS) - 1}")
    out += ["", summary, f"OVERALL: {verdict}"]
    print(summary)
    print(f"OVERALL: {verdict}")
    if only is None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-bossprep-REVERT.txt"
        keep_earlier(path)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
