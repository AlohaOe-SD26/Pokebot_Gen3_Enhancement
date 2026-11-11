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
    # =================================================================================== ROUND 2 (USER RULING 59, 2026-11-11)
    # the spec's section 5.2 (`ai-research-notes/2026-11-09-BOSS-PREP-BP1-RAISE-SPEC.md`), then the builder's additions
    # (partner_worn_off and the wiring mutants that delete a call the round added); predictions hashed before the first run
    # (s53/bp1r2/STATE.md)
    # ---- R1 the trainee's floor (V-M1)
    "trainee_floor_off": (CAUGHT, "(V-M1) BP-1's `hurt`: a trainee under its floor does not make the party rest",
                          [(GOALS, "        trainee_low = self._trainee_low(look, bp_plan)\n        worn = self._partner_worn(look, bp_plan)\n",
                            "        trainee_low = None  # MUTANT trainee_floor_off\n        worn = self._partner_worn(look, bp_plan)\n")],
                          ["TraineeFloorTests.test_r1a_r1b_under_the_floor_heals", "TraineeFloorTests.test_r1g_the_sequence"]),
    "raise_guard_off": (CAUGHT, "(V-M1) the raise goal made with the trainee under its floor",
                        [(GOALS, "        if low is not None and not self.bp_faults.raise_guard_off:\n",
                          "        if False:  # MUTANT raise_guard_off\n")],
                        ["TraineeFloorTests.test_r1f_the_raise_goal_waits_under_the_floor"]),
    "partner_worn_off": (CAUGHT, "(the builder's addition) a worn knock-out partner does not make the party rest",
                         [(GOALS, "        worn = self._partner_worn(look, bp_plan)\n        if self.bp_faults.trainee_floor_off:\n",
                           "        worn = None  # MUTANT partner_worn_off\n        if self.bp_faults.trainee_floor_off:\n")],
                         ["PartnerWornTests.test_a_worn_partner_heals"]),
    "no_partner_rest": (CAUGHT, "the raise roam does not stop for a worn partner (the call deleted)",
                        [(GOALS, "                return (stop or trainee_rest(look, trainee, heal_below, active)\n"
                                 "                        or partner_worn(look, trainee, manager.bp_faults))\n",
                          "                return stop or trainee_rest(look, trainee, heal_below, active)  # MUTANT no_partner_rest\n")],
                        ["PartnerWornTests.test_the_raise_roam_rests"]),
    # ---- R3 the raise's turn in a battle
    "raise_never_switch": (CAUGHT, "no switch-training: a trainee that cannot win safely runs (no partner asked)",
                           [(BATTLE, "            partner = None if self.faults.raise_never_switch else self.raise_partner(look, foe)\n",
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
                          [(BATTLE, "            safe, why = fight_safe(member, foe.species, foe.level, bar, mon.hp, "
                                    "tuple(m.name for m in foe.moves if m.name),\n                                   faults)\n",
                            "            safe, why = True, \"MUTANT partner_unchecked\"\n")],
                          ["RaiseTurnTests.test_r3e_no_partner_runs"]),
    "safe_full_hp": (CAUGHT, "`fight_safe` judges the trainee at its FULL HP, not its HP now",
                     [(BP, "    now = member.max_hp if faults.safe_full_hp else hp\n",
                       "    now = member.max_hp  # MUTANT safe_full_hp\n")],
                     ["RaiseTurnTests.test_r3h_judged_at_its_hp_now"]),
    "hits_unbounded": (CAUGHT, "`fight_safe` asks no bound on the trainee's hits",
                       [(BP, "    safe = (faults.hits_unbounded or hits <= RAISE_MAX_HITS) and left >= member.max_hp * TRAINEE_FLOOR\n",
                         "    safe = left >= member.max_hp * TRAINEE_FLOOR  # MUTANT hits_unbounded\n")],
                       ["RaiseTurnTests.test_r3i_a_five_hit_fight_is_not_safe",
                        "FightSafeTests.test_r4a_r4b_wurmple_and_cascoon_never_safe"]),
    "run_first": (CAUGHT, "the old order of a wild battle's choice: the run rule before the raise's turn",
                  [(BATTLE, "        if battle.kind == \"wild\" and not self.faults.run_first:\n",
                    "        if False:  # MUTANT run_first\n"),
                   (BATTLE, "        if battle.kind == \"wild\" and self.faults.run_first:\n",
                    "        if battle.kind == \"wild\":  # MUTANT run_first\n")],
                  ["RaiseTurnTests.test_r3k_the_raise_turn_before_the_run_rule"]),
    "replacement_trainee_ok": (CAUGHT, "the replacement after a faint may be the trainee while another member can fight",
                               [(BATTLE, "        if (self.purpose == \"raise\" and self.trainee is not None and not "
                                         "self.faults.replacement_trainee_ok\n                and any(m.pid != self.trainee "
                                         "for m in able)):\n",
                                 "        if False:  # MUTANT replacement_trainee_ok\n")],
                               ["RaiseTurnTests.test_r3j_the_replacement_is_never_the_trainee_while_another_can_fight"]),
    "second_switch": (CAUGHT, "the raise's switch made again on a later turn (three would share): its guard and its mode both",
                      [(BATTLE, "                or (mem.raise_switched and not self.faults.second_switch)):\n",
                        "                or (mem.raise_switched and False)):  # MUTANT second_switch\n"),
                       (BATTLE, "        if self.faults.second_switch and mem.raise_mode in (\"switch\", \"rescue\"):\n",
                        "        if mem.raise_mode in (\"switch\", \"rescue\"):  # MUTANT second_switch\n")],
                      ["RaiseTurnTests.test_r3m_no_second_switch"]),
    "trainee_sent_last": (CAUGHT, "\"Use next POKéMON?\" answered YES with only the trainee left (its check deleted)",
                          [(BATTLE, "            if (self.purpose == \"raise\" and self.trainee is not None and not "
                                    "self.faults.trainee_sent_last\n                    and self._only_the_trainee(look)):\n",
                            "            if False:  # MUTANT trainee_sent_last\n")],
                          ["RaiseTurnTests.test_r3l_use_next_with_only_the_trainee"]),
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
                      [(GOALS, "            return \"raise\" if self.bp_faults.one_raise_key else f\"raise:{place}\"\n",
                        "            return \"raise\"  # MUTANT one_raise_key\n")],
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
