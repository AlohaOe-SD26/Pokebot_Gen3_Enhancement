"""MUTANT PROOF of boss preparation BP-1 (USER RULING 58, 2026-11-09): each rule of the real code, broken in a COPY of the
package, fails its predicted test of `gates/test_bossprep.py`, or is documented as REDUNDANT ALONE (offline) with the reason.

    py -3.12 -B ai_player/gates/revert_bossprep.py [M1,M2] [--workers N]       (exit 0 = every prediction held)

The `revert_step4.py` pattern: copy the package (no states, no evidence), apply ONE mutant's edits (each anchor must occur
exactly once, or the run aborts; `gates/check_anchors.py` checks every anchor in seconds), run `gates/test_bossprep.py` from
the copy, check the PREDICTION: CAUGHT (every named test fails) or REDUNDANT (no test fails; the reason stated). The
unchanged copy (P0) must pass every test. The spec's mutants (section 5.2) keep their names; the wiring mutants (a call
deleted: `gates/call_census.py` counts them) are named for what they delete. The predictions were written and this file's
sha256 recorded (s53/bp1/STATE.md) BEFORE its first run. Evidence: `ai_player/evidence/<date>-bossprep-REVERT.txt`.
ROUND 2 (USER RULING 59, 2026-11-11): the round-2 spec's section 5.2 mutants (`trainee_floor_off` ... `count_fainted`,
one of them in the gate-side model `gates/exp_rule.py`) and the builder's eight (`partner_worn_off`, `no_partner_rest`,
`no_own_fight`, `partner_unchecked`, `no_potion_branch`, `no_use_on`, `no_lead_runner`, `no_settle_on_spend`); a mutant
whose rule is two conditions (`run_first`, `second_switch`, `potion_revives`, `relead_unbounded`) edits both, so it is the
rule switched off and not one half of it. Predictions written and this file's sha256 recorded (s53/bp1r2/STATE.md)
BEFORE the first run.
ROUND 3 (2026-11-11, the trainee safe throughout an active plan: the round-2 verifier's V2-M1, V2-M2, V2-m3, the lead's
design D1-D5): 28 mutants (the rescue, the partner line, the guard outside raise battles, four of the verifier's REDUNDANT
mutants given a test, the shift question's context); eight round-2 anchors moved by the round's edits were re-anchored
(their predictions kept; three gained a round-3 test). The driver also runs `gates/test_hands.py` FieldItemTests (the field
item hand's PID check); test names are "Class.test" in both. Predictions written and this file's sha256 recorded
(s53/bp1r3/STATE.md) BEFORE the first run.
ROUND 4 (2026-11-11, the round-3 verifier's V3-M1, V3-M2, V3-m1 to V3-m4; the lead's design E1-E6): the round's mutants (a
heal only when it can change the decision, the last resort's order, trainer battles, the seam, PP, and the verifier's
REDUNDANT mutants given a test, in their shapes on this tree); eleven earlier anchors moved by the round's edits were
re-anchored, their predictions kept (`guard_turn1_only` now deletes the whole later-turn protection, which E2's last resort
would otherwise re-find, and gained a round-4 test). Predictions written and this file's sha256 recorded (s53/bp1r4/STATE.md)
BEFORE the first run.
ROUND 4, THE SECOND RUN (2026-11-12, the second builder): the first run (P0 + 155) MISSED ONE prediction, `own_fallback_unmade`
(predicted caught, NOT caught: the named test's rescue is made by the run branch's call, not the one the mutant deletes; its
record is evidence/2026-11-11-bossprep-REVERT.txt, OVERALL FAIL). The call is live, so it got its own test, and this file
four more mutants: `run_fallback_unmade` (the run branch's call), `fallback_hp_only` and `fallback_matchup_only` (the two
factors of the choice among members that cannot win), `land_slots_any_availability`. P0 + 159. Predictions written and this
file's NEW sha256 recorded (s53/bp1r4/STATE.md) BEFORE the second run.
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
#: (round 2) the gate-side experience model (`gates/exp_rule.py`: test side, never the AI's); the battle skill (the live
#: #118 learn-move loop's fix)
EXP = "gates/exp_rule.py"
SKILL = "skills/battle.py"
#: (round 3) the field item hand (its tests are `gates/test_hands.py` FieldItemTests, run beside test_bossprep's)
ITEM = "hands/field_item.py"

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
                 # (round 4) re-anchored: the budget is read by `_plan_spent` (the decision's early check and the raise goal)
                 [(GOALS, "        spent = spent_reason(record, personality)\n        if spent is not None:\n            return spent\n",
                   "        spent = None  # MUTANT no_bound\n        if spent is not None:\n            return spent\n")],
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
    # =================================================================================== ROUND 2 (USER RULING 59, 2026-11-11)
    # the spec's section 5.2 (`ai-research-notes/2026-11-09-BOSS-PREP-BP1-RAISE-SPEC.md`), then the builder's additions
    # (partner_worn_off and the wiring mutants that delete a call the round added); predictions hashed before the first run
    # (s53/bp1r2/STATE.md)
    # ---- R1 the trainee's floor (V-M1)
    "trainee_floor_off": (CAUGHT, "(V-M1) BP-1's `hurt`: a trainee under its floor does not make the party rest",
                          [(GOALS, "        trainee_low = self._trainee_low(look, bp_plan)\n        worn = self._partner_worn(look, bp_plan, world)\n",
                            "        trainee_low = None  # MUTANT trainee_floor_off\n        worn = self._partner_worn(look, bp_plan, world)\n")],
                          ["TraineeFloorTests.test_r1a_r1b_under_the_floor_heals", "TraineeFloorTests.test_r1g_the_sequence"]),
    "raise_guard_off": (CAUGHT, "(V-M1) the raise goal made with the trainee under its floor",
                        [(GOALS, "        if low is not None and not self.bp_faults.raise_guard_off:\n",
                          "        if False:  # MUTANT raise_guard_off\n")],
                        ["TraineeFloorTests.test_r1f_the_raise_goal_waits_under_the_floor"]),
    "partner_worn_off": (CAUGHT, "(the builder's addition) a worn knock-out partner does not make the party rest",
                         [(GOALS, "        worn = self._partner_worn(look, bp_plan, world)\n        if self.bp_faults.trainee_floor_off:\n",
                           "        worn = None  # MUTANT partner_worn_off\n        if self.bp_faults.trainee_floor_off:\n")],
                         ["PartnerWornTests.test_a_worn_partner_heals"]),
    "no_partner_rest": (CAUGHT, "the raise roam does not stop for a worn partner (the call deleted)",
                        # (round 4) re-anchored: trainee_rest now takes the faults (E5's PP stop)
                        [(GOALS, "                return (stop or trainee_rest(look, trainee, heal_below, active, manager.bp_faults)\n"
                                 "                        or partner_worn(look, trainee, manager.bp_faults, raise_map))\n",
                          "                return stop or trainee_rest(look, trainee, heal_below, active, manager.bp_faults)  # MUTANT\n")],
                        ["PartnerWornTests.test_the_raise_roam_rests", "PartnerLineTests.test_the_raise_roam_rests_on_its_map"]),
    # ---- R3 the raise's turn in a battle
    "raise_never_switch": (CAUGHT, "no switch-training: a trainee that cannot win safely runs (no partner asked)",
                           # (round 4) re-anchored: the partner is asked only on a "mix" map (`raise_switch`)
                           [(BATTLE, "            partner = None if self.faults.raise_never_switch or not switching else "
                                     "self.raise_partner(look, foe)\n",
                             "            partner = None  # MUTANT raise_never_switch\n")],
                           ["RaiseTurnTests.test_r3a_switch_training", "RaiseTurnTests.test_r3k_the_raise_turn_before_the_run_rule"]),
    "raise_always_switch": (CAUGHT, "the trainee switched out even when it wins safely (no own fights)",
                            [(BATTLE, "            if safe and not self.faults.raise_always_switch:\n",
                              "            if False:  # MUTANT raise_always_switch\n")],
                            ["RaiseTurnTests.test_r3b_control_an_own_fight", "RaiseTurnTests.test_r3d_the_rescue_once"]),
    "no_own_fight": (CAUGHT, "the trainee's own fight never judged (`fight_safe`'s call in the raise turn deleted)",
                     [(BATTLE, "            safe, why = fight_safe(trainee, foe.species, foe.level, bar, trainee.hp,\n"
                               "                                   tuple(m.name for m in foe.moves if m.name), faults)\n",
                       "            safe, why = False, \"MUTANT no_own_fight\"\n")],
                     ["RaiseTurnTests.test_r3b_control_an_own_fight"]),
    "partner_unchecked": (CAUGHT, "a healthy member taken as the partner without asking whether it wins safely",
                          [(BATTLE, "            safe, why = partner_fit(member, foe.species, foe.level, bar, mon.hp, "
                                    "tuple(m.name for m in foe.moves if m.name),\n                                    faults)\n",
                            "            safe, why = True, \"MUTANT partner_unchecked\"\n")],
                          ["RaiseTurnTests.test_r3e_no_partner_runs"]),
    "safe_full_hp": (CAUGHT, "`fight_safe` judges the trainee at its FULL HP, not its HP now",
                     [(BP, "    now = member.max_hp if faults.safe_full_hp else hp\n",
                       "    now = member.max_hp  # MUTANT safe_full_hp\n")],
                     ["RaiseTurnTests.test_r3h_judged_at_its_hp_now"]),
    "hits_unbounded": (CAUGHT, "`fight_safe` asks no bound on the trainee's hits",
                       [(BP, "    safe = (faults.hits_unbounded or hits <= RAISE_MAX_HITS) and left >= floor\n",
                         "    safe = left >= floor  # MUTANT hits_unbounded\n")],
                       ["RaiseTurnTests.test_r3i_a_five_hit_fight_is_not_safe",
                        "FightSafeTests.test_r4a_r4b_wurmple_and_cascoon_never_safe"]),
    "run_first": (CAUGHT, "the old order of a wild battle's choice: the run rule before the raise's turn",
                  [(BATTLE, "        if battle.kind == \"wild\" and not self.faults.run_first:\n",
                    "        if False:  # MUTANT run_first\n"),
                   (BATTLE, "        if battle.kind == \"wild\" and self.faults.run_first:\n",
                    "        if battle.kind == \"wild\":  # MUTANT run_first\n")],
                  ["RaiseTurnTests.test_r3k_the_raise_turn_before_the_run_rule"]),
    "replacement_trainee_ok": (CAUGHT, "the replacement after a faint may be the trainee while another member can fight",
                               [(BATTLE, "        if (protected is not None and not self.faults.replacement_trainee_ok\n"
                                         "                and any(m.pid != protected for m in able)):\n",
                                 "        if False:  # MUTANT replacement_trainee_ok\n")],
                               ["RaiseTurnTests.test_r3j_the_replacement_is_never_the_trainee_while_another_can_fight",
                                "GuardTests.test_g5_never_sent_in_while_another_can_fight"]),
    "second_switch": (CAUGHT, "the raise's switch made again on a later turn (three would share): its guard and its mode both",
                      [(BATTLE, "                or (mem.raise_switched and not self.faults.second_switch)):\n",
                        "                or (mem.raise_switched and False)):  # MUTANT second_switch\n"),
                       (BATTLE, "        if self.faults.second_switch and mem.raise_mode in (\"switch\", \"rescue\"):\n",
                        "        if mem.raise_mode in (\"switch\", \"rescue\"):  # MUTANT second_switch\n")],
                      ["RaiseTurnTests.test_r3m_no_second_switch"]),
    "trainee_sent_last": (CAUGHT, "\"Use next POKéMON?\" answered YES with only the trainee left (its check deleted)",
                          [(BATTLE, "            if not self.faults.trainee_sent_last and self._only_the_trainee(look):\n",
                            "            if False:  # MUTANT trainee_sent_last\n")],
                          ["RaiseTurnTests.test_r3l_use_next_with_only_the_trainee",
                           "GuardTests.test_g5_never_sent_in_while_another_can_fight"]),
    # ---- R5 the heal choice
    "potion_always": (CAUGHT, "the potion goal chosen even with a POKéMON CENTER near",
                      [(GOALS, "        if near and not faults.potion_always:\n", "        if False:  # MUTANT potion_always\n")],
                      ["HealChoiceTests.test_r5a_a_centre_near"]),
    "centre_always": (CAUGHT, "the potion goal never chosen (its call in the heal step deleted)",
                      [(GOALS, "                potion = self._potion_goal(look, world, milestone, bp_plan, trainee_low, worn, fainted, share)\n",
                        "                potion = None  # MUTANT centre_always\n")],
                      ["HealChoiceTests.test_r5b_a_centre_far"]),
    "potion_revives": (CAUGHT, "the potion goal chosen for a FAINTED trainee",
                       [(GOALS, "        if not trainee_low.startswith(\"low\") and not (faults.potion_revives and trainee_low == \"fainted\"):\n",
                         "        if not trainee_low.startswith(\"low\") and not (True and trainee_low == \"fainted\"):  # MUTANT\n"),
                        (GOALS, "        if (others_fainted or (fainted and not faults.potion_revives) or needs_rest(look.party) is not None\n",
                         "        if (others_fainted or (fainted and not True) or needs_rest(look.party) is not None  # MUTANT\n")],
                       ["HealChoiceTests.test_r5d_fainted"]),
    "no_potion_branch": (CAUGHT, "the runner never plays a potion goal (`_potion`'s call deleted)",
                         [(GOALS, "            return (yield from self._potion(goal))\n", "            pass  # MUTANT no_potion_branch\n")],
                         ["HealChoiceTests.test_the_potion_runner_calls_the_hand"]),
    "no_use_on": (CAUGHT, "the potion goal never uses the field item hand (its call deleted)",
                  [(GOALS, "        ok, used, why = yield from use_on(self.hands, goal.pid, FIELD_POTIONS, POTION_TO, POTIONS_PER_GOAL, goal.reason)\n",
                    "        ok, used, why = False, 0, \"MUTANT no_use_on\"\n        yield\n")],
                  ["HealChoiceTests.test_the_potion_runner_calls_the_hand"]),
    # ---- R6 the raise map (BP1-L1, BP1-L2)
    "map_by_trainee": (CAUGHT, "(BP1-L1) BP-1's map rule: the highest top level at most the trainee's level + 2",
                       [(GOALS, "        if self.bp_faults.map_by_trainee:\n", "        if True:  # MUTANT map_by_trainee\n")],
                       ["RaiseMapTests.test_r6a_the_partners_cap", "RaiseMapTests.test_r6b_r6c_r6d_the_caps"]),
    "one_raise_key": (CAUGHT, "(BP1-L2) one cooldown key for every raise map",
                      [(GOALS, "        return \"raise\" if self.bp_faults.one_raise_key else f\"raise:{place}\"\n",
                        "        return \"raise\"  # MUTANT one_raise_key\n")],
                      ["RaiseMapTests.test_r6e_a_map_that_fails_twice_is_put_aside",
                       "PlanTests.test_the_story_run_gets_a_raise_goal"]),
    # ---- R7 the budget's counting (V-m3)
    "frames_uncounted": (CAUGHT, "(V-m3) a raise session's frames not counted",
                         [(GOALS, "            if not faults.frames_uncounted:\n                record[\"frames\"] += hands.pad.frames - began\n",
                           "            if False:  # MUTANT frames_uncounted\n                record[\"frames\"] += hands.pad.frames - began\n")],
                         ["BudgetCountingTests.test_r7a_frames"]),
    "stalls_never": (CAUGHT, "(V-m3) the stall count never grows",
                     [(GOALS, "            record[\"stalls\"] = 0 if (gained or faults.stalls_never) else record[\"stalls\"] + 1\n",
                       "            record[\"stalls\"] = 0  # MUTANT stalls_never\n")],
                     ["BudgetCountingTests.test_r7b_r7c_r7d_stalls_by_exp"]),
    "stall_by_level": (CAUGHT, "(V-m3) BP-1's stall: a session with no LEVEL gained",
                       [(GOALS, "            if faults.stall_by_level:\n                gained = start_level",
                         "            if True:  # MUTANT stall_by_level\n                gained = start_level")],
                       ["BudgetCountingTests.test_r7b_r7c_r7d_stalls_by_exp"]),
    "heal_frames_uncounted": (CAUGHT, "(V-m3) the heal, find_center and potion goals of an active plan not counted (the call "
                                      "deleted)",
                              [(GOALS, "        plan_record = self._plan_heal_record(goal)\n",
                                "        plan_record = None  # MUTANT heal_frames_uncounted\n")],
                              ["BudgetCountingTests.test_r7f_heal_frames_count_while_active"]),
    "base_to_active": (CAUGHT, "(V-m3) the plan and its budget by the ACTIVE personality, not the base",
                       [(GOALS, "        personality = self.state.active if self.bp_faults.base_to_active else self.state.base\n"
                                "        signature =",
                         "        personality = self.state.active  # MUTANT base_to_active\n        signature =")],
                       ["BudgetCountingTests.test_r7g_the_base_personality_decides"]),
    # ---- R8 the lead after a plan ends (V-m5)
    "restore_never": (CAUGHT, "(V-m5) a plan that ended leaves the trainee first (the settle's call deleted)",
                      [(GOALS, "        settle = self._settle_goal(look, index) if has_party and not hurt else None\n",
                        "        settle = None  # MUTANT restore_never\n")],
                      ["LeadAfterTests.test_r8a_the_usual_lead_restored", "LeadAfterTests.test_r8e_after_the_boss_is_beaten"]),
    "restore_always": (CAUGHT, "(V-m5) the usual lead restored without the re-judge",
                       [(GOALS, "        if which == \"E1\" and not faults.restore_always:\n",
                         "        if False:  # MUTANT restore_always\n")],
                       ["LeadAfterTests.test_r8b_control_the_trainee_kept"]),
    "relead_unbounded": (CAUGHT, "(V-m5, V4) no bound on failed lead goals: the settle's and the done plan's",
                         [(GOALS, "        if record.get(\"relead_fails\", 0) >= RELEAD_FAILS_MAX and not faults.relead_unbounded:\n",
                           "        if False:  # MUTANT relead_unbounded\n"),
                          (GOALS, "        if not faults.relead_unbounded and not faults.lead_ignores_budget and "
                                  "record.get(\"relead_fails\", 0) >= RELEAD_FAILS_MAX:\n",
                           "        if False:  # MUTANT relead_unbounded\n")],
                         ["LeadAfterTests.test_r8c_relead_bounded", "LeadAfterTests.test_r8d_the_done_plans_relead_is_bounded"]),
    "lead_ignores_budget": (CAUGHT, "(V-m5, V4) the done plan's re-lead ignores the reorder and lead bounds",
                            [(GOALS, "        if not faults.lead_ignores_budget and (record.get(\"reorder_fails\", 0) >= "
                                     "bounds[\"reorder_fails\"]\n",
                              "        if False and (record.get(\"reorder_fails\", 0) >= bounds[\"reorder_fails\"]  # MUTANT\n")],
                            ["LeadAfterTests.test_r8d_the_done_plans_relead_is_bounded"]),
    "no_lead_runner": (CAUGHT, "the runner never plays a lead goal (`_lead`'s call deleted)",
                       [(GOALS, "            return (yield from self._lead(goal))\n", "            pass  # MUTANT no_lead_runner\n")],
                       ["LeadAfterTests.test_the_lead_runner_counts_and_settles"]),
    "no_settle_on_spend": (CAUGHT, "(E1) a plan spent without its lead left to settle",
                           [(BP, "    record[\"settle\"] = \"pending\"\n", "    pass  # MUTANT no_settle_on_spend\n")],
                           ["BudgetTests.test_a_spent_budget_ends_the_raise"]),
    # ---- R9 the party's fixed damage against an immune type (V-m1)
    "no_immunity_own": (CAUGHT, "(V-m1) the party's fixed damage scored against a type immune to it",
                        [(BP, "    if fact is not None and not faults.no_immunity_own and type_multiplier(fact.type, "
                              "types_of(boss.species)) == 0:\n        return 0\n",
                          "    if False:  # MUTANT no_immunity_own\n        return 0\n")],
                        ["OwnImmunityTests.test_night_shade"]),
    # ---- R2 the gate-side experience model
    "count_fainted": (CAUGHT, "the model counts a FAINTED participant (its share halves the survivor's)",
                      [(EXP, "    via = sum(1 for a in alive if a or count_fainted)\n", "    via = len(alive)  # MUTANT count_fainted\n")],
                      ["ExpModelTests.test_the_hand_values"]),
    # ---- (added 2026-11-11 after the live A/B #118 found the learn-move loop; predictions re-hashed before the run)
    "no_learning_kept": (CAUGHT, "the learner's page not kept apart from the 40-page window (the live #118 loop's first half)",
                         [(SKILL, "            self.learning = (found.group(1).strip().casefold(), found.group(2).strip().casefold())\n",
                           "            pass  # MUTANT no_learning_kept\n")],
                         ["LearnerTests.test_the_learner_named_by_its_page"]),
    "learner_page_off": (CAUGHT, "the page kept apart never read: the window, then the battler",
                         [(SKILL, "    if (not faults.learner_by_battler and pages.learning is not None\n",
                           "    if (False and pages.learning is not None  # MUTANT learner_page_off\n")],
                         ["LearnerTests.test_the_learner_named_by_its_page"]),
    "learner_knowledge_off": (CAUGHT, "a battle met at the question names the battler, not the member taught the move now",
                              [(SKILL, "    if mon is None and not faults.learner_by_battler:\n        mon = _learns_now(party, move)\n",
                                "    if False:  # MUTANT learner_knowledge_off\n        mon = _learns_now(party, move)\n")],
                              ["LearnerTests.test_met_at_the_question"]),
    "forget_recheck_off": (CAUGHT, "the forget screen's four moves not checked against the member the choice was made for",
                           [(SKILL, "    if (learn is not None and learn.learn and learn.forget is not None and len(names) == 5 "
                                    "and not faults.forget_unchecked\n",
                             "    if (False and learn is not None and learn.learn and learn.forget is not None  # MUTANT\n")],
                           ["LearnerTests.test_the_forget_screen_rechecks"]),
    # =================================================================================== ROUND 3 (2026-11-11)
    # the trainee SAFE throughout an active plan (the round-2 verifier's V2-M1, V2-M2, V2-m3; the lead's design D1-D5);
    # predictions written and this file's sha256 recorded (s53/bp1r3/STATE.md) BEFORE the first run
    # ---- D1 (V2-M1): the raise battle's rescue
    "run_no_rescue": (CAUGHT, "(V2-M1) a refused run in a raise battle answered with \"run again\", never the rescue (the "
                              "rescue's calls deleted)",
                      # (round 4) re-anchored: the rescue and, with nobody that wins, the last resort (E2) both deleted
                      [(BATTLE, "                rescue = self.rescue_member(look, foe, desperate=low and self.faults.fallback_first)\n"
                                "                if rescue is not None:\n                    mem.raise_mode = \"rescue\"\n"
                                "                    if self.raise_modes:\n                        self.raise_modes[-1] = \"rescue\"\n"
                                "                    return self._raise_rescue(rescue, hp_share, \"the run was refused\")\n"
                                "                last, decision = self._last_resort(look, own, foe, \"raising: the run was refused\", "
                                "desperate=low,\n                                                   run_ok=False)\n"
                                "                if last == \"fight\":\n                    mem.raise_mode = \"own\"\n"
                                "                    return decision\n                if last == \"fallback\":\n"
                                "                    mem.raise_mode = \"rescue\"\n                    if self.raise_modes:\n"
                                "                        self.raise_modes[-1] = \"rescue\"\n"
                                "                    return self._raise_rescue(decision, hp_share, \"the run was refused\")\n",
                        "                pass  # MUTANT run_no_rescue\n")],
                      ["RescueTests.test_r3n_a_refused_run_under_the_floor_is_rescued",
                       "RescueTests.test_r3o_a_refused_run_above_the_floor_goes_to_a_member_that_can_win",
                       "RescueTests.test_r3r_under_the_floor_any_member_that_can_come_in"]),
    "turn1_no_rescue": (CAUGHT, "(V2-M1) a trainee under its floor on its first decision with no partner runs (the "
                                "rescue's calls deleted)",
                        # (round 4) re-anchored: the rescue's call (a member that wins) deleted; E2's last resort stays
                        [(BATTLE, "                rescue = self.rescue_member(look, foe, desperate=self.faults.fallback_first)\n"
                                  "                if rescue is not None:\n                    mem.raise_mode = \"rescue\"\n"
                                  "                    self.raise_modes.append(mem.raise_mode)\n"
                                  "                    return self._raise_rescue(rescue, hp_share, f\"{head}: under its floor and no "
                                  "partner wins safely\")\n",
                          "                pass  # MUTANT turn1_no_rescue\n")],
                        ["RescueTests.test_r3s_under_the_floor_on_its_first_decision"]),
    "own_no_rescue": (CAUGHT, "an own fight gone badly is never rescued (the rescue's calls deleted)",
                      # (round 4) re-anchored: the rescue's call (a member that wins) deleted, the rest of the own branch kept
                      [(BATTLE, "            rescue = self.rescue_member(look, foe, desperate=self.faults.fallback_first)\n"
                                "            if rescue is not None:\n                mem.raise_mode = \"rescue\"\n"
                                "                if self.raise_modes:\n                    self.raise_modes[-1] = \"rescue\"\n"
                                "                return self._raise_rescue(rescue, hp_share, \"an own fight went badly\")\n",
                        "            pass  # MUTANT own_no_rescue\n")],
                      ["RaiseTurnTests.test_r3d_the_rescue_once", "RescueTests.test_the_own_fights_rescue_needs_only_a_win"]),
    "rescue_unchecked": (CAUGHT, "(V2-M1) the rescue takes any member that can come in as one that can win (its fight_safe "
                                 "call deleted)",
                         [(BATTLE, "            wins, why = fight_safe(member, foe.species, foe.level, bar, mon.hp, seen, faults, keep=0)\n",
                           "            wins, why = True, \"MUTANT rescue_unchecked\"\n")],
                         ["RescueTests.test_r3p_run_again_when_nobody_can_win"]),
    "rescue_needs_partner": (CAUGHT, "(V2-M1) the rescue asks round 2's partner line (half its HP, a third kept), not a win",
                             [(BATTLE, "        if self.faults.rescue_needs_partner:\n",
                               "        if True:  # MUTANT rescue_needs_partner\n")],
                             ["RescueTests.test_r3o_a_refused_run_above_the_floor_goes_to_a_member_that_can_win",
                              "RescueTests.test_the_own_fights_rescue_needs_only_a_win"]),
    "rescue_keep_third": (CAUGHT, "(V2-M1) the rescue's \"can win\" asks a third kept after the worst case (keep 0 lost)",
                          [(BATTLE, "            wins, why = fight_safe(member, foe.species, foe.level, bar, mon.hp, seen, faults, keep=0)\n",
                            "            wins, why = fight_safe(member, foe.species, foe.level, bar, mon.hp, seen, faults)  # MUTANT\n")],
                          ["RescueTests.test_r3o_a_refused_run_above_the_floor_goes_to_a_member_that_can_win"]),
    "rescue_no_fallback": (CAUGHT, "(V2-M1, V2-M2) under its floor with nobody sure to win, no member that can come in",
                           [(BATTLE, "        if not desperate or self.faults.rescue_no_fallback:\n",
                             "        if True:  # MUTANT rescue_no_fallback\n")],
                           ["RescueTests.test_r3r_under_the_floor_any_member_that_can_come_in"]),
    "keep_zero_floor": (CAUGHT, "(V2-M1) `fight_safe(keep=0)` asks a third kept anyway (the rescue's line is the partner's)",
                        [(BP, "    floor = member.max_hp * keep if keep > 0 else 1  # (round 3) keep 0: still standing, at 1 HP or more\n",
                          "    floor = member.max_hp * TRAINEE_FLOOR  # MUTANT keep_zero_floor\n")],
                        ["RescueTests.test_can_win_is_fight_safe_with_keep_zero",
                         "RescueTests.test_r3o_a_refused_run_above_the_floor_goes_to_a_member_that_can_win"]),
    # ---- D1 (V2-M1): the rest line is the partner line
    "partner_half_line": (CAUGHT, "(V2-M1) the raise rests at round 2's flat half, not by the partner line on its map",
                          [(BP, "    slots = land_slots(raise_map) if raise_map and not faults.partner_half_line else ()\n",
                            "    slots = ()  # MUTANT partner_half_line\n")],
                          ["PartnerLineTests.test_the_rest_line_is_the_battles_partner_line",
                           "PartnerLineTests.test_the_line_against_the_strongest_slot",
                           "PartnerLineTests.test_the_party_rests_before_the_next_raise",
                           "PartnerLineTests.test_the_raise_roam_rests_on_its_map"]),
    "partner_line_unchecked": (CAUGHT, "(V2-M1) the rest line never asks the partner line of the map's wild Pokemon (its call "
                                       "deleted)",
                               [(BP, "        fit, why = partner_fit(member, species, level, 1.0, partner.hp, (), faults)\n",
                                 "        fit, why = True, \"MUTANT partner_line_unchecked\"\n")],
                               ["PartnerLineTests.test_the_rest_line_is_the_battles_partner_line",
                                "PartnerLineTests.test_the_line_against_the_strongest_slot",
                                "PartnerLineTests.test_the_party_rests_before_the_next_raise"]),
    "partner_fit_half_only": (CAUGHT, "(V2-M1) the partner line asks only half its HP, not a safe win (its fight_safe call "
                                      "deleted)",
                              [(BP, "    return fight_safe(member, foe_species, foe_level, bar_share, hp, seen_moves, faults)\n",
                                "    return True, \"MUTANT partner_fit_half_only\"\n")],
                              ["RaiseTurnTests.test_r3e_no_partner_runs", "PartnerLineTests.test_the_line_against_the_strongest_slot"]),
    "partner_fit_no_half": (CAUGHT, "(V2-M1) the partner line without its half-HP rule (the verifier's `partner_any_hp`)",
                            [(BP, "    if hp < member.max_hp / 2:\n        return False, f\"{member.species} is under half its HP",
                              "    if False:  # MUTANT partner_fit_no_half\n        return False, f\"{member.species} is under half its HP")],
                            ["PartnerLineTests.test_half_its_hp_is_part_of_the_line",
                             "PartnerWornTests.test_a_worn_partner_heals"]),
    "no_raise_place": (CAUGHT, "(V2-M1) the decision's rest line not told the map the next raise goes to",
                       [(GOALS, "        place = self._raise_place(look, world, record) if world is not None else None\n",
                         "        place = None  # MUTANT no_raise_place\n")],
                       ["PartnerLineTests.test_the_party_rests_before_the_next_raise"]),
    "roam_no_map": (CAUGHT, "(V2-M1) the raise session's roam not told its map (its rest falls back to the half line)",
                    [(GOALS, "            self.roam_hooks(trainee=pid, after_battle=watch.after, raise_map=goal.map)\n",
                      "            self.roam_hooks(trainee=pid, after_battle=watch.after)  # MUTANT roam_no_map\n")],
                    ["PartnerLineTests.test_the_raise_session_gives_its_map_to_the_rest"]),
    # ---- D2 (V2-M2): the trainee protected in every other battle of an active plan
    "guard_off": (CAUGHT, "(V2-M2) no protection outside a raise battle (the guard's turn guarded off in _decide)",
                  [(BATTLE, "        if not self.faults.guard_off:\n            # (boss preparation round 3, V2-M2) an ACTIVE plan's "
                            "trainee in a battle that is not a raise battle (a heal walk,\n            # a pick-up, travel, a "
                            "trainer's battle): kept out of harm FIRST, before a catch, a run or a heal (FAULT\n            # "
                            "`guard_off`: round 2, where it led them as any Pokemon and fainted in 5 of them in 6 live runs)\n"
                            "            decision = self._guard_turn(look, own, foe, hp_share)\n",
                    "        if False:  # MUTANT guard_off\n            decision = self._guard_turn(look, own, foe, hp_share)\n")],
                  ["GuardTests.test_g1_the_heal_walk", "GuardTests.test_g2_a_wild_fight_it_would_not_win_safely",
                   "GuardTests.test_g3_a_trainers_battle", "GuardTests.test_g4_a_later_turn_under_the_floor"]),
    "guard_no_switch": (CAUGHT, "(V2-M2) the first decision's protection never names a member to take its place (the "
                                "rescue's call deleted)",
                        # (round 4) re-anchored: the turn-1 call now asks only for a member that wins (E2)
                        [(BATTLE, "            rescue = self.rescue_member(look, foe, desperate=low and self.faults.fallback_first)\n"
                                  "            if rescue is None:\n                last, decision = self._last_resort(",
                          "            rescue = None  # MUTANT guard_no_switch\n"
                          "            if rescue is None:\n                last, decision = self._last_resort(")],
                        ["GuardTests.test_g1_the_heal_walk", "GuardTests.test_g2_a_wild_fight_it_would_not_win_safely",
                         "GuardTests.test_g3_a_trainers_battle"]),
    "guard_floor_only": (CAUGHT, "(V2-M2) a wild battle's turn-1 protection asks only the floor, not a safe win (its "
                                 "fight_safe call deleted)",
                         [(BATTLE, "                    safe, why = fight_safe(trainee, foe.species, foe.level, foe.hp_bar / "
                                   "HP_BAR_PIXELS, trainee.hp,\n                                           tuple(m.name for m "
                                   "in foe.moves if m.name), faults)\n",
                           "                    safe, why = True, \"MUTANT guard_floor_only\"\n")],
                         ["GuardTests.test_g2_a_wild_fight_it_would_not_win_safely"]),
    "guard_turn1_only": (CAUGHT, "(V2-M2) no rescue on a later turn under the floor (a refused run answered with a run): the "
                                 "rescue's call deleted",
                         # (round 4) re-anchored: the whole later-turn protection deleted (the rescue's call alone is
                         # re-found by E2's last resort, whose fallback asks first for a member that wins)
                         [(BATTLE, "        if self.faults.guard_turn1_only or not low:\n            return None\n"
                                   "        rescue = self.rescue_member(look, foe, desperate=self.faults.fallback_first)\n",
                           "        if self.faults.guard_turn1_only or not low:\n            return None\n"
                           "        return None  # MUTANT guard_turn1_only\n"
                           "        rescue = self.rescue_member(look, foe, desperate=self.faults.fallback_first)\n")],
                         ["GuardTests.test_g4_a_later_turn_under_the_floor",
                          "LastResortTests.test_with_none_that_wins_a_wild_battle_runs"]),
    "guard_switch_back": (CAUGHT, "(V2-M2) the protected trainee may be the member switched IN for a matchup",
                          [(BATTLE, "            out = out | {protected}  # (round 3, V2-M2) a protected trainee is never the member "
                                    "switched IN for a matchup\n",
                            "            pass  # MUTANT guard_switch_back\n")],
                          ["GuardTests.test_g6_never_switched_in_for_a_matchup"]),
    "guard_unset": (CAUGHT, "(V2-M2) the goal runner never tells the battle brain whom to protect (round 2)",
                    [(GOALS, "        guard = self._guard_for(goal)\n        self.mind.guard = guard\n",
                      "        guard = None  # MUTANT guard_unset\n        self.mind.guard = guard\n")],
                    ["GuardRunnerTests.test_a_heal_walk_is_guarded"]),
    "guard_in_boss_fight": (CAUGHT, "(V2-M2) the protection kept on in the boss fight itself",
                            # (round 4) re-anchored: the rule now lives in `_boss_fight` (the guard's and the seam's)
                            [(GOALS, "        if manager.bp_faults.guard_in_boss_fight or manager.bp_boss is None:\n"
                                     "            return False\n",
                              "        if True:  # MUTANT guard_in_boss_fight\n            return False\n")],
                            ["GuardRunnerTests.test_the_boss_fight_and_the_raise_are_left_out"]),
    "guard_in_raise": (CAUGHT, "(V2-M2) the guard set in a raise goal too (its own rules are the raise's)",
                       # (round 4) re-anchored: `_guard_for` reads `_boss_fight` and `_plan_trainee`
                       [(GOALS, "        if goal.kind == \"raise\" or self._boss_fight(goal):\n",
                         "        if self._boss_fight(goal):  # MUTANT guard_in_raise\n")],
                       ["GuardRunnerTests.test_the_boss_fight_and_the_raise_are_left_out"]),
    "guard_inactive_plan": (CAUGHT, "(V2-M2) the guard set for a plan that is not active (spent or done)",
                            # (round 4) re-anchored: the plan's state is read by `_plan_trainee`
                            [(GOALS, "        if record is None or record.get(\"status\") != \"active\" or record.get(\"trainee\") is None:\n"
                                     "            return None\n        return int(record[\"trainee\"])\n",
                              "        if record is None or record.get(\"trainee\") is None:  # MUTANT guard_inactive_plan\n"
                              "            return None\n        return int(record[\"trainee\"])\n")],
                            ["GuardRunnerTests.test_a_heal_walk_is_guarded"]),
    # ---- D3 (V2-m3): the verifier's REDUNDANT mutants, each now with a test (its own edit, its own name)
    "run_no_retry": (CAUGHT, "(the verifier's) after a refused run with nobody to rescue, the raise turn gives up (a fight)",
                     [(BATTLE, "            mem.runs += 1\n            return Decision(\"run\", \"raising: still no member to knock "
                               "it out: run again\")\n",
                       "            return None  # MUTANT run_no_retry\n")],
                     ["RescueTests.test_r3p_run_again_when_nobody_can_win"]),
    "settle_any_lead": (CAUGHT, "(the verifier's) E1/E3 restore the usual lead even when the trainee is not first",
                        [(GOALS, "        if faults.restore_never or before is None or before == trainee or usual is None or "
                                 "usual.hp <= 0 \\\n                or party[0].pid != trainee:\n",
                          "        if faults.restore_never or before is None or before == trainee or usual is None or "
                          "usual.hp <= 0:  # MUTANT\n")],
                        ["SettleNotFirstTests.test_the_trainee_not_first"]),
    "use_on_no_pid_check": (CAUGHT, "(the verifier's) the field item hand's PID-multiset check removed",
                            [(ITEM, "    same = sorted(_pids(after)) == sorted(before_pids)\n",
                              "    same = True  # MUTANT use_on_no_pid_check\n")],
                            ["FieldItemTests.test_a_party_whose_pids_changed_fails"]),
    "learning_any_move": (CAUGHT, "(the verifier's) the page kept apart used even when it names ANOTHER move",
                          [(SKILL, "            and move_key(pages.learning[1]) == move_key(printed)):\n",
                            "            and True):  # MUTANT learning_any_move\n")],
                          ["LearnerKeptPageTests.test_a_kept_page_for_another_move"]),
    # ---- D5: the shift question's context
    "shift_context_pages_only": (CAUGHT, "the shift question answered from the window's last 4 pages without the screen's "
                                         "whole message",
                                 [(SKILL, "    return \" \".join(pages.pages[-4:] + [look.screen.text or \"\"])\n",
                                   "    return \" \".join(pages.pages[-4:])  # MUTANT shift_context_pages_only\n")],
                                 ["ShiftContextTests.test_the_foe_is_in_the_screens_text_not_the_window"]),
    # =================================================================================== ROUND 4 (2026-11-11)
    # the round-3 verifier's V3-M1, V3-M2, V3-m1 to V3-m4 (the lead's design E1-E6); predictions written and this file's
    # sha256 recorded (s53/bp1r4/STATE.md) BEFORE the first run
    # ---- E1 (V3-M1): a heal only when it can change the decision
    "partner_full_unchecked": (CAUGHT, "(V3-M1) the raise rests for a partner that fails its line even healed (the healed "
                                       "line's call in partner_worn deleted: round 3's heal loop)",
                               [(BP, "    healed = None if faults.partner_full_unchecked else partner_line_full(look, trainee, "
                                     "raise_map, faults)\n",
                                 "    healed = None  # MUTANT partner_full_unchecked\n")],
                               ["FullPartnerTests.test_no_rest_for_a_partner_a_heal_cannot_make_fit"]),
    "mode_unchecked": (CAUGHT, "(V3-M1) every map a switch-training map (the healed line's call in mode_on deleted)",
                       [(GOALS, "        healed = partner_line_full(look, trainee, place, self.bp_faults)\n",
                         "        healed = None  # MUTANT mode_unchecked\n")],
                       ["FullPartnerTests.test_h1_a_full_partner_unfit_on_route116_never_heals",
                        "FullPartnerTests.test_raise_mode_and_the_own_map"]),
    "full_line_off": (CAUGHT, "(V3-M1) the healed partner taken as fit everywhere (the judgement's call deleted)",
                      [(BP, "    return _full_line(_healed(member), raise_map, faults)\n",
                        "    return True, \"MUTANT full_line_off\"\n")],
                      ["FullPartnerTests.test_h1_a_full_partner_unfit_on_route116_never_heals",
                       "FullPartnerTests.test_the_healed_line_per_map"]),
    "healed_not_full": (CAUGHT, "(V3-M1) the 'healed' partner judged as it is now (the heal's call deleted)",
                        [(BP, "    return _full_line(_healed(member), raise_map, faults)\n",
                          "    return _full_line(member, raise_map, faults)  # MUTANT healed_not_full\n")],
                        ["FullPartnerTests.test_the_healed_line_per_map", "PPTests.test_a_partner_out_of_pp_rests_the_raise"]),
    "healed_pp_kept": (CAUGHT, "(V3-M1, V3-m3) the heal restores HP but not PP",
                       [(BP, "                          moves=tuple(replace(m, pp=m.max_pp) if m.max_pp is not None else m for "
                             "m in summary.moves))\n",
                         "                          moves=summary.moves)  # MUTANT healed_pp_kept\n")],
                       ["PPTests.test_a_partner_out_of_pp_rests_the_raise"]),
    "full_line_uncached": (CAUGHT, "(E1) the healed line judged again at every ask (not once per map and partner)",
                           [(BP, "@functools.lru_cache(maxsize=512)\ndef _full_line(", "def _full_line(")],
                           ["FullPartnerTests.test_the_healed_line_per_map"]),
    "choice_ignores_mode": (CAUGHT, "(V3-M1) the raise goes to the first map whatever its mode (the loop's mode call deleted)",
                            [(GOALS, "            mode, why = self.mode_on(look, place, trainee.pid)\n            if mode == \"mix\":\n",
                              "            mode, why = \"mix\", \"\"  # MUTANT choice_ignores_mode\n            if mode == \"mix\":\n")],
                            ["FullPartnerTests.test_h1_a_full_partner_unfit_on_route116_never_heals",
                             "FullPartnerTests.test_a_worn_partner_rests_before_the_mix_map"]),
    "own_fallback_mix": (CAUGHT, "(V3-M1) with no map where the partner is fit, the first map raised on as a switch-training "
                                 "map (the fallback's mode call deleted)",
                         [(GOALS, "        mode, why = self.mode_on(look, allowed[0], trainee.pid)\n",
                           "        mode, why = \"mix\", \"MUTANT own_fallback_mix\"\n")],
                         ["FullPartnerTests.test_raise_mode_and_the_own_map"]),
    "no_mode_in_session": (CAUGHT, "(V3-M1) the raise session never asks its map's mode (switch-training on an own map)",
                           [(GOALS, "            mode, mode_why = manager.mode_on(hands.last if hands.last is not None else look, "
                                    "goal.map, pid)\n",
                             "            mode, mode_why = \"mix\", \"MUTANT no_mode_in_session\"\n")],
                           ["FullPartnerTests.test_the_raise_session_takes_its_mode_from_the_map"]),
    "own_map_switches": (CAUGHT, "(V3-M1) a raise battle switch-trains on an own map",
                         [(BATTLE, "            switching = self.raise_switch or self.faults.own_map_switches\n",
                           "            switching = True  # MUTANT own_map_switches\n")],
                         ["FullPartnerTests.test_own_mode_has_no_switch_training"]),
    "spend_check_unhooked": (CAUGHT, "(V3-M1) the budget not checked before the rest (the early check's call deleted)",
                             [(GOALS, "            self._spend_if_over(look, world, bp_plan)\n",
                               "            pass  # MUTANT spend_check_unhooked\n")],
                             ["FullPartnerTests.test_an_exceeded_budget_while_worn_spends_the_plan"]),
    "spend_check_blind": (CAUGHT, "(V3-M1) the early check never finds the plan spent (its _plan_spent call deleted)",
                          [(GOALS, "        spent = self._plan_spent(look, world, record, personality)\n        if spent is not None:\n"
                                   "            self._spend(record, name, spent)\n",
                            "        spent = None  # MUTANT spend_check_blind\n        if spent is not None:\n"
                            "            self._spend(record, name, spent)\n")],
                          ["FullPartnerTests.test_an_exceeded_budget_while_worn_spends_the_plan"]),
    "raise_goal_no_budget": (CAUGHT, "the raise goal's own budget check deleted (its _plan_spent call)",
                             [(GOALS, "        spent = self._plan_spent(look, world, record, personality) if trainee is not None else "
                                      "spent_reason(record,\n",
                               "        spent = None if trainee is not None else spent_reason(record,  # MUTANT\n")],
                             ["FullPartnerTests.test_the_raise_goal_checks_the_budget_too"]),
    "no_grass_unspent": (CAUGHT, "the early check never spends for 'no grass within reach' (only the budget)",
                         [(GOALS, "        if trainee is not None and not self.raise_maps(world, self.raise_cap(look, trainee)[0]):\n",
                           "        if False:  # MUTANT no_grass_unspent\n")],
                         ["FullPartnerTests.test_no_grass_spends_before_any_rest"]),
    "raise_goal_no_choice": (CAUGHT, "the raise goal's map choice never made (its _raise_choice call deleted: the raise "
                                     "waits forever)",
                             [(GOALS, "        choice = self._raise_choice(look, world, record)\n        if choice is None:\n"
                                      "            cap, _ = self.raise_cap(look, trainee)\n",
                               "        choice = None  # MUTANT raise_goal_no_choice\n        if choice is None:\n"
                               "            cap, _ = self.raise_cap(look, trainee)\n")],
                             ["PlanTests.test_the_story_run_gets_a_raise_goal"]),
    # ---- E6 (V3-m4): `_raise_place` against a map put aside, one rule with `_raise_goal`
    "choice_ignores_aside": (CAUGHT, "(V3-m4) a raise map put aside still chosen (and asked by the rest line)",
                             [(GOALS, "        allowed = [place for place in maps if self._allowed(self._raise_key(place))]\n",
                               "        allowed = list(maps)  # MUTANT choice_ignores_aside\n")],
                             ["CoverageTests.test_the_rest_line_asks_the_map_the_raise_goes_to",
                              "RaiseMapTests.test_r6e_a_map_that_fails_twice_is_put_aside"]),
    "place_own_rule": (CAUGHT, "(V3-m4, the verifier's v_raise_place_ignores_aside's shape) `_raise_place` keeps round 3's "
                               "own copy of the rule (its _raise_choice call deleted)",
                       [(GOALS, "        choice = self._raise_choice(look, world, record)\n        return choice[0] if choice is not "
                                "None else None\n",
                         "        trainee = next((m for m in look.party or () if m.pid == record.get(\"trainee\")), None)  # MUTANT\n"
                         "        if trainee is None:\n            return None\n"
                         "        cap, _ = self.raise_cap(look, trainee)\n"
                         "        return next((p for p in self.raise_maps(world, cap) if self._allowed(self._raise_key(p))), None)\n")],
                       ["FullPartnerTests.test_a_worn_partner_rests_before_the_mix_map"]),
    # ---- E2 (V3-M2): no member sure to win
    "no_own_sure_win": (CAUGHT, "(V3-M2) (a) deleted: the trainee's own sure win never asked (its fight_safe call)",
                        [(BATTLE, "                wins, wins_why = fight_safe(me, foe.species, foe.level, foe.hp_bar / "
                                  "HP_BAR_PIXELS, me.hp,\n                                            tuple(m.name for m in "
                                  "foe.moves if m.name), faults, keep=0)\n",
                          "                wins, wins_why = False, \"MUTANT no_own_sure_win\"\n")],
                        ["LastResortTests.test_the_6413_fixture_fights", "LastResortTests.test_a_later_turn_its_own_sure_win",
                         "LastResortTests.test_a_raise_battle_under_its_floor_its_own_sure_win"]),
    "no_last_run": (CAUGHT, "(V3-M2) (b) deleted: a wild battle never run from before a member that cannot win is sent",
                    [(BATTLE, "            if run_ok and battle is not None and battle.kind == \"wild\" and self.memory.runs < "
                              "MAX_RUN_TRIES:\n",
                      "            if False:  # MUTANT no_last_run\n")],
                    ["LastResortTests.test_with_none_that_wins_a_wild_battle_runs",
                     "LastResortTests.test_an_own_raise_fight_gone_badly_with_no_winner"]),
    "last_resort_fallback_only": (CAUGHT, "(V3-M2) round 3's order: (a) and (b) both skipped, a member that cannot win sent "
                                          "at once",
                                  [(BATTLE, "        if not self.faults.fallback_first:\n            me = member_now(look, own.pid)\n",
                                    "        if False:  # MUTANT last_resort_fallback_only\n            me = member_now(look, own.pid)\n")],
                                  ["LastResortTests.test_the_6413_fixture_fights",
                                   "LastResortTests.test_with_none_that_wins_a_wild_battle_runs"]),
    "no_fallback_at_all": (CAUGHT, "(V3-M2) (c) deleted: under its floor, with nobody that wins and no run left, no member "
                                   "that can come in",
                           [(BATTLE, "        if desperate:\n            fallback = self.rescue_member(look, foe, desperate=True)\n",
                             "        if False:  # MUTANT no_fallback_at_all\n            fallback = self.rescue_member(look, foe, desperate=True)\n")],
                           ["LastResortTests.test_a_trainer_battle_goes_to_the_member_that_can_come_in",
                            "LastResortTests.test_the_floor_boundary",
                            "RescueTests.test_r3r_under_the_floor_any_member_that_can_come_in"]),
    "guard_no_last_resort": (CAUGHT, "(V3-M2) the guard's turn 1 never asks the last resort (its call deleted)",
                             [(BATTLE, "                last, decision = self._last_resort(look, own, foe, f\"{head}: {reason}\", "
                                       "desperate=low, run_ok=True)\n",
                               "                last, decision = \"none\", None  # MUTANT guard_no_last_resort\n")],
                             ["LastResortTests.test_the_6413_fixture_fights",
                              "LastResortTests.test_with_none_that_wins_a_wild_battle_runs"]),
    "guard_later_no_last_resort": (CAUGHT, "(V3-M2) the guard's later turn never asks the last resort (its call deleted)",
                                   [(BATTLE, "            last, decision = self._last_resort(look, own, foe, f\"{head}: under its "
                                             "floor ({hp_share:.0%})\", desperate=True,\n"
                                             "                                               run_ok=mem.runs == 0)\n",
                                     "            last, decision = \"none\", None  # MUTANT guard_later_no_last_resort\n")],
                                   ["LastResortTests.test_with_none_that_wins_a_wild_battle_runs"]),
    "raise1_no_last_resort": (CAUGHT, "(V3-M2) the raise's turn 1 under its floor never asks the last resort (its call "
                                      "deleted)",
                              [(BATTLE, "                last, decision = self._last_resort(look, own, foe, f\"raising "
                                        "{trainee.species}: {head}: under its floor\",\n"
                                        "                                                   desperate=False, run_ok=False)  "
                                        "# (b), the run, is the path below\n",
                                "                last, decision = \"none\", None  # MUTANT raise1_no_last_resort\n")],
                              ["LastResortTests.test_a_raise_battle_under_its_floor_its_own_sure_win"]),
    "run_no_last_resort": (CAUGHT, "(V3-M2) a refused raise run never asks the last resort (its call deleted)",
                           [(BATTLE, "                last, decision = self._last_resort(look, own, foe, \"raising: the run was "
                                     "refused\", desperate=low,\n                                                   run_ok=False)\n",
                             "                last, decision = \"none\", None  # MUTANT run_no_last_resort\n")],
                           ["RescueTests.test_r3r_under_the_floor_any_member_that_can_come_in",
                            "LastResortTests.test_a_refused_raise_run_its_own_sure_win_first"]),
    "own_no_last_resort": (CAUGHT, "(V3-M2) an own raise fight gone badly never asks the last resort (its call deleted)",
                           [(BATTLE, "            last, decision = self._last_resort(look, own, foe, \"raising: an own fight "
                                     "went badly\", desperate=mem.runs > 0,\n"
                                     "                                               run_ok=mem.runs == 0)\n",
                             "            last, decision = \"none\", None  # MUTANT own_no_last_resort\n")],
                           ["LastResortTests.test_an_own_raise_fight_gone_badly_with_no_winner"]),
    # (round 4, the second builder, 2026-11-12) mutant run 1 MISSED this one: predicted caught by LastResortTests.
    # test_an_own_raise_fight_gone_badly_with_no_winner, whose rescue is made by the RUN branch's call (the own branch's run
    # sets the mode to "run"); the own branch's call is reached only by a fight that became an own fight AFTER a refused
    # run, the fixture of the test named now. `run_fallback_unmade` deletes the run branch's call.
    "own_fallback_unmade": (CAUGHT, "(V3-M2) after a refused run in an own fight gone badly, (c)'s switch never made (its "
                                    "_raise_rescue call deleted)",
                            [(BATTLE, "                return self._raise_rescue(decision, hp_share, \"an own fight went badly, and "
                                      "a run was refused\")\n",
                              "                return None  # MUTANT own_fallback_unmade\n")],
                            ["LastResortTests.test_an_own_fight_begun_after_a_refused_run_gone_badly"]),
    "run_fallback_unmade": (CAUGHT, "(V3-M2) after a refused raise run with no member that wins and no own sure win, (c)'s "
                                    "switch never made (the run branch's _raise_rescue call deleted): it runs again",
                            [(BATTLE, "                    return self._raise_rescue(decision, hp_share, \"the run was refused\")\n",
                              "                    pass  # MUTANT run_fallback_unmade\n")],
                            ["LastResortTests.test_an_own_raise_fight_gone_badly_with_no_winner",
                             "LastResortTests.test_a_refused_raise_run_its_own_sure_win_first",
                             "RescueTests.test_r3r_under_the_floor_any_member_that_can_come_in"]),
    # ---- E3 (V3-m1): trainer battles
    "guard_wild_only": (CAUGHT, "(V3-m1) the turn-1 protection's safe-win test in wild battles only (round 3)",
                        [(BATTLE, "            if reason is None and (battle.kind == \"wild\" or not self.faults.guard_wild_only):\n",
                          "            if reason is None and battle.kind == \"wild\":  # MUTANT guard_wild_only\n")],
                        ["GuardTests.test_g3_a_trainers_battle",
                         "TrainerGuardTests.test_g6_a_trainer_battle_outside_a_raise_switches"]),
    "guard_not_in_raise": (CAUGHT, "(V3-m1) a raise goal's trainer battle unguarded (the protected member's call deleted: "
                                   "round 3's guard alone)",
                           [(BATTLE, "        protected = self._guard_whom(battle)\n",
                             "        protected = None if self.purpose == \"raise\" else self.guard  # MUTANT guard_not_in_raise\n")],
                           ["TrainerGuardTests.test_g8_a_raise_goals_trainer_battle",
                            "TrainerGuardTests.test_g9_a_raise_goals_trainer_battle_later_turn"]),
    "guarded_any_kind": (CAUGHT, "(V3-m1) the guard also takes a raise's WILD battles from the raise's own turn",
                         [(BATTLE, "        if self.faults.guard_not_in_raise or battle is None or battle.kind == \"wild\":\n",
                           "        if self.faults.guard_not_in_raise or battle is None:  # MUTANT guarded_any_kind\n")],
                         ["TrainerGuardTests.test_a_wild_raise_battle_is_still_the_raises"]),
    # ---- E4 (V3-m2): the seam between goals
    "seam_kept": (CAUGHT, "(V3-m2) nothing reset at a goal's end (the reset's call deleted: round 3)",
                  [(GOALS, "            self.between_goals(goal)\n", "            pass  # MUTANT seam_kept\n")],
                  ["SeamTests.test_a_scene_battle_right_after_a_raise_goal",
                   "SeamTests.test_a_scene_battle_right_after_a_heal_goal"]),
    "seam_purpose_kept": (CAUGHT, "(V3-m2) a raise's purpose left to the battles after it",
                          [(GOALS, "        if getattr(mind, \"purpose\", None) == \"raise\":\n            mind.purpose = \"travel\"\n",
                            "        if False:  # MUTANT seam_purpose_kept\n            mind.purpose = \"travel\"\n")],
                          ["SeamTests.test_a_scene_battle_right_after_a_raise_goal"]),
    "seam_no_plan_guard": (CAUGHT, "(V3-m2) no guard between goals (the plan's trainee never read: its call deleted)",
                           [(GOALS, "        guard = None if goal is not None and self._boss_fight(goal) else self._plan_trainee()\n",
                             "        guard = None  # MUTANT seam_no_plan_guard\n")],
                           ["SeamTests.test_a_scene_battle_right_after_a_raise_goal",
                            "SeamTests.test_a_scene_battle_right_after_a_heal_goal"]),
    "seam_boss_guarded": (CAUGHT, "(V3-m2) the battle the boss fight's talk hands back guarded (its _boss_fight call deleted)",
                          [(GOALS, "        guard = None if goal is not None and self._boss_fight(goal) else self._plan_trainee()\n",
                            "        guard = self._plan_trainee()  # MUTANT seam_boss_guarded\n")],
                          ["SeamTests.test_after_the_boss_fight_the_guard_stays_off"]),
    "seam_say_kept": (CAUGHT, "(V3-m2) the guard's line left on between goals with no guard",
                      [(GOALS, "        mind.say = self.tell if guard is not None else None\n        if guard is not None:\n"
                               "            mind.bp_faults = manager.bp_faults\n",
                        "        pass  # MUTANT seam_say_kept\n        if guard is not None:\n"
                        "            mind.bp_faults = manager.bp_faults\n")],
                      ["SeamTests.test_a_scene_battle_right_after_a_heal_goal"]),
    "guard_no_plan_trainee": (CAUGHT, "(V3-m2) `_guard_for` never reads the plan's trainee (its call deleted)",
                              [(GOALS, "        return self._plan_trainee()\n\n    def _plan_trainee(self)",
                                "        return None  # MUTANT guard_no_plan_trainee\n\n    def _plan_trainee(self)")],
                              ["GuardRunnerTests.test_a_heal_walk_is_guarded"]),
    "guard_boss_unasked": (CAUGHT, "(V3-m2) `_guard_for` never asks whether the goal is the boss fight (its call deleted)",
                           [(GOALS, "        if goal.kind == \"raise\" or self._boss_fight(goal):\n",
                             "        if goal.kind == \"raise\":  # MUTANT guard_boss_unasked\n")],
                           ["GuardRunnerTests.test_the_boss_fight_and_the_raise_are_left_out"]),
    # ---- E5 (V3-m3): PP
    "pp_ignored_fight_safe": (CAUGHT, "(V3-m3) a move at 0 PP counted in fight_safe (the PP call deleted)",
                              [(BP, "    usable = [name for name in member.moves if faults.pp_ignored or _pp_left(member, name)]\n",
                                "    usable = list(member.moves)  # MUTANT pp_ignored_fight_safe\n")],
                              ["PPTests.test_fight_safe_counts_pp", "PPTests.test_the_own_fight_judgement_counts_pp",
                               "PPTests.test_a_partner_out_of_pp_rests_the_raise"]),
    "no_pp_session_end": (CAUGHT, "(V3-m3) a raise session goes on with the trainee out of PP (its check guarded off)",
                          [(BP, "    if trainee is not None and not faults.pp_ignored and out_of_pp(member_now(look, pid)):\n",
                            "    if False:  # MUTANT no_pp_session_end\n")],
                          ["PPTests.test_the_raise_session_ends_out_of_pp"]),
    "no_pp_heal": (CAUGHT, "(V3-m3) the party never heals for the trainee out of PP (its check guarded off)",
                   [(GOALS, "        if not self.bp_faults.pp_ignored and out_of_pp(member_now(look, trainee.pid)):\n",
                     "        if False:  # MUTANT no_pp_heal\n")],
                   ["PPTests.test_the_party_heals_out_of_pp"]),
    "pp_count_off": (CAUGHT, "(V3-m3) out of PP whenever it has a move that hurts (the PP call deleted)",
                     [(BP, "    return bool(hurting) and not any(_pp_left(member, name) for name in hurting)\n",
                       "    return bool(hurting)  # MUTANT pp_count_off\n")],
                     ["PPTests.test_out_of_pp"]),
    "pp_any_move": (CAUGHT, "(V3-m3) out of PP as soon as ONE move that hurts is",
                    [(BP, "    return bool(hurting) and not any(_pp_left(member, name) for name in hurting)\n",
                      "    return bool(hurting) and not all(_pp_left(member, name) for name in hurting)  # MUTANT\n")],
                    ["PPTests.test_out_of_pp"]),
    "pp_left_always": (CAUGHT, "(V3-m3) every move usable whatever its PP",
                       [(BP, "    return move is None or move.pp is None or move.pp > 0\n", "    return True  # MUTANT pp_left_always\n")],
                       ["PPTests.test_fight_safe_counts_pp", "PPTests.test_out_of_pp"]),
    "no_trainee_rest_call": (CAUGHT, "the raise roam's trainee rule never asked (its call deleted)",
                             [(GOALS, "                return (stop or trainee_rest(look, trainee, heal_below, active, manager.bp_faults)\n",
                               "                return (stop or None  # MUTANT no_trainee_rest_call\n")],
                             ["PPTests.test_the_raise_session_ends_out_of_pp"]),
    # ---- E6 (V3-m4): the verifier's REDUNDANT mutants, each now with a test (their shapes, on this tree)
    "guard_switch_unbounded": (CAUGHT, "(V3-m4) the guard's one protective switch a battle unbounded",
                               [(BATTLE, "        if protected is None or battle is None or battle.double or own.pid != protected "
                                         "or mem.guard_switched:\n",
                                 "        if protected is None or battle is None or battle.double or own.pid != protected:  # MUTANT\n")],
                               ["CoverageTests.test_the_guard_switches_once_a_battle"]),
    "guard_doubles": (CAUGHT, "(V3-m4) the guard acts in a double battle",
                      [(BATTLE, "        if protected is None or battle is None or battle.double or own.pid != protected "
                                "or mem.guard_switched:\n",
                        "        if protected is None or battle is None or own.pid != protected or mem.guard_switched:  # MUTANT\n")],
                      ["CoverageTests.test_no_guard_in_a_double_battle"]),
    "rescue_matchup_first": (CAUGHT, "(V3-m4) the rescue's choice among members that win by matchup first, not the healthiest",
                             [(BATTLE, "            key = (mon.hp / max(1, mon.max_hp), matchup(mon.types, mon.moves, mon.level, "
                                       "foe, self.faults)[0], mon.level,\n",
                               "            key = (matchup(mon.types, mon.moves, mon.level, foe, self.faults)[0], mon.hp / "
                               "max(1, mon.max_hp), mon.level,  # MUTANT\n")],
                             ["CoverageTests.test_the_rescue_takes_the_healthiest_winner"]),
    "rescue_sent_since": (CAUGHT, "(V3-m4) the rescue may name a member already sent in this turn",
                          [(BATTLE, "        skip = {self._protected()} | standing | self.sent_since | set(self.refused) | "
                                    "set(exclude or ())\n",
                            "        skip = {self._protected()} | standing | set(self.refused) | set(exclude or ())  # MUTANT\n")],
                          ["CoverageTests.test_the_rescue_skips_a_member_sent_this_turn"]),
    "guard_floor_inclusive": (CAUGHT, "(V3-m4) the guard's floor inclusive (exactly a third counts as under it)",
                              [(BATTLE, "        low = hp_share < TRAINEE_FLOOR\n        head = f\"the plan's trainee",
                                "        low = hp_share <= TRAINEE_FLOOR  # MUTANT\n        head = f\"the plan's trainee")],
                              ["LastResortTests.test_the_floor_boundary"]),
    "say_always": (CAUGHT, "(V3-m4) the battle brain's guard line set for every non-raise goal, guard or not",
                   [(GOALS, "            self.mind.say = self.tell if guard is not None else None\n",
                     "            self.mind.say = self.tell  # MUTANT say_always\n")],
                   ["CoverageTests.test_the_guards_line_and_faults_only_with_a_guard"]),
    "no_bp_faults_for_guard": (CAUGHT, "(V3-m4) a guarded goal does not hand the boss preparation's faults to the battle brain",
                               [(GOALS, "            if guard is not None:\n                self.mind.bp_faults = manager.bp_faults\n",
                                 "            if guard is not None:\n                pass  # MUTANT no_bp_faults_for_guard\n")],
                               ["CoverageTests.test_the_guards_line_and_faults_only_with_a_guard"]),
    "boss_fight_any_talk": (CAUGHT, "(V3-m4) the boss fight's exclusion takes ANY talk of the boss's milestone",
                            [(GOALS, "        return (goal.milestone == manager.bp_boss[0] and goal.kind in (\"talk\", \"use\") and "
                                     "goal.look is not None\n                and goal.key == f\"{goal.kind}:{goal.look}\")\n",
                              "        return (goal.milestone == manager.bp_boss[0] and goal.kind in (\"talk\", \"use\") and "
                              "goal.look is not None)  # MUTANT\n")],
                            ["CoverageTests.test_the_boss_fights_own_key",
                             "SeamTests.test_after_the_boss_fight_the_guard_stays_off"]),
    # (the second builder, 2026-11-12) the last two of the verifier's 13 REDUNDANT mutants, and the fallback's other factor
    "fallback_hp_only": (CAUGHT, "(V3-m4) the member sent when none is sure to win chosen by its HP alone (no matchup)",
                         [(BATTLE, "            score = (matchup(mon.types, mon.moves, mon.level, foe, self.faults)[0]\n"
                                   "                     * (0.5 + 0.5 * mon.hp / max(1, mon.max_hp)))\n",
                           "            score = (0.5 + 0.5 * mon.hp / max(1, mon.max_hp))  # MUTANT fallback_hp_only\n")],
                         ["CoverageTests.test_the_fallback_takes_the_best_matched"]),
    "fallback_matchup_only": (CAUGHT, "(V3-m4) the member sent when none is sure to win chosen by its matchup alone (its HP "
                                      "not weighed)",
                              [(BATTLE, "            score = (matchup(mon.types, mon.moves, mon.level, foe, self.faults)[0]\n"
                                        "                     * (0.5 + 0.5 * mon.hp / max(1, mon.max_hp)))\n",
                                "            score = matchup(mon.types, mon.moves, mon.level, foe, self.faults)[0]  # MUTANT\n")],
                              ["CoverageTests.test_the_fallback_takes_the_best_matched"]),
    "land_slots_any_availability": (CAUGHT, "(V3-m4) land_slots also reads the land tables a player does not meet in normal "
                                            "play (its availability filter deleted)",
                                    [("knowledge/seasoned.py",
                                      "            if entry[\"availability\"] != \"normal\":\n                continue\n"
                                      "            slots = ((entry.get(\"methods\") or {}).get(\"land\") or {}).get(\"slots\") or ()\n"
                                      "            const = str(entry[\"map\"]).removeprefix(\"MAP_\")\n"
                                      "            for slot in slots:\n",
                                      "            slots = ((entry.get(\"methods\") or {}).get(\"land\") or {}).get(\"slots\") or ()\n"
                                      "            const = str(entry[\"map\"]).removeprefix(\"MAP_\")  # MUTANT\n"
                                      "            for slot in slots:\n")],
                                    ["CoverageTests.test_land_slots_reads_normal_play_only"]),
}

DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_bossprep, test_hands
suite = unittest.defaultTestLoader.loadTestsFromModule(test_bossprep)
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_hands.FieldItemTests))
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {".".join(t.id().split(".")[-2:]): kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
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
