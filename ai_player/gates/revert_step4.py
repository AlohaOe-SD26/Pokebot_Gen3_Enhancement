"""MUTANT PROOF of AI-player build step 4 (the AI's own battles): each rule of the REAL code, broken in a COPY of the
package, fails its predicted test of `gates/test_battle.py`, or is documented as REDUNDANT ALONE with the reason.

    py -3.12 ai_player/gates/revert_step4.py [B1,B2] [--workers N]       (exit 0 = every prediction held)

WHY (CLAUDE.md session discipline rule 6): `test_battle.py`'s fault halves switch a rule off through a FAULT switch or a
patched constant. That shows the tests CAN fail, not that each rule in the real code carries weight. As
`revert_step3.py` does for the navigator, this copies the package (no states, no evidence), applies ONE mutant's edits
(each anchor must occur exactly once, or the run aborts), runs `gates/test_battle.py` from the copy (the framework from
this repo), and checks the PREDICTION: CAUGHT (every named test fails) or REDUNDANT (no test fails; the reason is stated).
The unchanged copy (B0) must pass every test. Evidence: `ai_player/evidence/<date>-step4-REVERT.txt`.
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
TIMEOUT = 600
CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"
BATTLE, SKILL, FLEE, SCREENS, FACTS = "brain/battle.py", "skills/battle.py", "skills/flee.py", "eyes/screens.py", "knowledge/facts.py"

#: name -> (prediction, the rule that is broken, [edits], tests that MUST fail (CAUGHT) or the reason (REDUNDANT)).
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str] | str]] = {
    "B0": (CONTROL, "nothing: the unchanged copy", [], []),
    "B1": (CAUGHT, "the type chart ignored in a move's worth (every matchup x1)",
           [(BATTLE, "    effectiveness = 1.0 if faults.ignore_types else type_multiplier(mtype, foe_types)\n",
             "    effectiveness = 1.0  # MUTANT B1\n")],
           ["TypeTests.test_the_effective_move_is_chosen", "ValueTests.test_worth_is_type_stab_power_and_hit"]),
    "B2": (CAUGHT, "STAB ignored",
           [(BATTLE, "    bonus = 1.0 if faults.ignore_types else stab(mtype, user_types)\n", "    bonus = 1.0  # MUTANT B2\n")],
           ["ValueTests.test_worth_is_type_stab_power_and_hit"]),
    "B3": (CAUGHT, "no recoil penalty",
           [(BATTLE, "    penalty = 0.0 if faults.ignore_recoil else recoil_penalty(fact, base, hp_share, full, risk)\n",
             "    penalty = 0.0  # MUTANT B3\n")],
           ["RecoilTests.test_take_down_at_full_hp_water_gun_when_low",
            "RecordedRecoilTests.test_fault_overkill_take_down_at_full_hp_and_at_20_percent_never_when_its_recoil_would_faint_it"]),
    "B4": (CAUGHT, "the recoil penalty does not grow as the user's HP falls",
           [(BATTLE, "    weight = 0.5 + 2.5 * (1.0 - max(0.0, min(1.0, hp_share)))\n", "    weight = 0.5  # MUTANT B4\n")],
           ["RecoilTests.test_the_penalty_grows_as_hp_falls", "RecoilTests.test_take_down_at_full_hp_water_gun_when_low"]),
    "B5": (CAUGHT, "a status move valued like a damaging one (33)",
           [(BATTLE, "        return MoveValue(slot, move.name, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, True)\n",
             "        return MoveValue(slot, move.name, 33.0, 33.0, 1.0, 1.0, 1.0, 0.0, 0.0, False)  # MUTANT B5\n")],
           ["ChoiceTests.test_never_a_status_move_by_habit", "ValueTests.test_a_status_move_is_worth_nothing_in_a_fight"]),
    "B6": (CAUGHT, "the single best move every time (no draw among the about-as-good)",
           [(BATTLE, "        near = [v for v in hurting if v.value >= floor]\n",
             "        near = [max(hurting, key=lambda v: v.value)]  # MUTANT B6\n")],
           ["ChoiceTests.test_about_equal_moves_are_both_drawn_a_clear_winner_always",
            "TypeTests.test_fault_types_ignored_never_choose_it"]),
    "B7": (CAUGHT, "a weakening move that could knock the foe out is used (no KO check)",
           [(BATTLE, "            if bar - high > KO_MARGIN:\n", "            if True:  # MUTANT B7\n")],
           ["CatchTests.test_every_move_could_knock_it_out_so_throw_at_once"]),
    "B8": (CAUGHT, "a Poke Ball every time (never a better ball for a hard catch)",
           [(BATTLE, "        if cues:\n            for better in GREAT_BALLS:\n",
             "        if False:  # MUTANT B8\n            for better in GREAT_BALLS:\n")],
           ["CatchTests.test_the_ball_by_what_a_person_sees_not_the_catch_rate"]),
    "B9": (CAUGHT, "no bound on the balls thrown in one battle",
           [(BATTLE, "        if not balls or mem.throws >= MAX_THROWS:\n", "        if not balls:  # MUTANT B9\n")],
           ["CatchTests.test_at_most_max_throws"]),
    "B10": (CAUGHT, "every wild species counted as new (the Pokedex's owned list not read)",
            [(BATTLE, "        self.memory.new_species = battle.kind == \"wild\" and foe.dex not in owned\n",
              "        self.memory.new_species = battle.kind == \"wild\"  # MUTANT B10\n")],
            ["CatchTests.test_an_owned_species_is_fought"]),
    "B11": (CAUGHT, "a Pokemon far above the foe's level switched out for a bad matchup (no level guard)",
            [(BATTLE, "        if not badly or own.level >= foe.level + margin:\n", "        if not badly:  # MUTANT B11\n")],
            ["SwitchTests.test_not_when_it_far_outlevels_the_foe"]),
    "B12": (CAUGHT, "a switch in a double battle",
            [(BATTLE, "        if look.battle is not None and look.battle.double:\n            return None  # step 4 does not switch "
                      "in a double battle (`_fight_double`)\n", "")],
            ["SwitchTests.test_not_twice_against_one_foe_and_not_in_a_double_battle"]),
    "B13": (CAUGHT, "a fainted Pokemon chosen to go in",
            [(BATTLE, "            if member.hp <= 0 or member.is_egg or member.pid in out:\n",
              "            if member.is_egg or member.pid in out:  # MUTANT B13\n")],
            ["SwitchTests.test_the_replacement_is_the_best_healthy_member_by_pid"]),
    "B14": (CAUGHT, "training never runs (low HP, a far stronger foe)",
            [(BATTLE, "        if self.purpose == \"train\":\n", "        if False:  # MUTANT B14\n")],
            ["RunTests.test_training_runs_when_low_or_outmatched"]),
    "B15": (CAUGHT, "a healing item in any battle (not only an important one)",
            [(BATTLE, "        if battle.kind == \"trainer\":\n            decision = self._heal(",
              "        if True:  # MUTANT B15\n            decision = self._heal(")],
            ["HealTests.test_not_in_a_wild_battle_nor_when_the_foe_is_about_to_fall"]),
    "B16": (CAUGHT, "\"Use next POKéMON?\" always answered NO",
            [(BATTLE, "            return (pid is not None), (f\"yes: {why}\" if pid is not None else f\"no: {why}\")\n",
              "            return False, f\"no: {why}\"  # MUTANT B16\n")],
            ["AnswerTests.test_the_questions"]),
    "B17": (CAUGHT, "a move learned for a trifle (no margin over the weakest)",
            [(BATTLE, "    if new_worth > worth[weakest] * 1.15 + 5:\n", "    if new_worth > worth[weakest]:  # MUTANT B17\n")],
            ["LearnTests.test_fault_no_margin_churns_for_a_trifle"]),
    "B18": (CAUGHT, "an HM may be forgotten",
            [(BATTLE, "    forgettable = [n for n in known if n not in HM_MOVES]\n", "    forgettable = list(known)  # MUTANT B18\n")],
            ["LearnTests.test_an_hm_is_never_forgotten"]),
    "B19": (CAUGHT, "a double battle's move aimed at the last foe whatever it hurts most",
            [(BATTLE, "                candidates.append((value, foe.battler))\n",
              "                candidates.append((value, foes[-1].battler))  # MUTANT B19\n")],
            ["DoubleTests.test_the_move_is_aimed_at_the_foe_it_hurts_most"]),
    "B20": (CAUGHT, "a spread move not halved in a double battle",
            [(BATTLE, "                share = 1.0 if not spread else (0.5 if fact.target == \"BOTH\" else 0.75)\n",
              "                share = 1.0  # MUTANT B20\n")],
            ["DoubleTests.test_a_spread_move_is_halved"]),
    "B21": (CAUGHT, "a 2 x 2 grid's A pressed wherever the cursor is (not read)",
            [(FLEE, "        if ui.cursor == index:\n            yield from hands.pad.press(\"A\", why, f\"{kind} cursor on {index} ({names[index]})\")\n",
              "        if True:  # MUTANT B21\n            yield from hands.pad.press(\"A\", why, f\"{kind} cursor on {index} ({names[index]})\")\n")],
            ["SkillTests.test_fight_reads_both_grids"]),
    "B22": (CAUGHT, "the party menu's Pokemon chosen by the first slot, not its PID",
            [(SKILL, "    return (yield from choose(hands, \"party\", pids.index(pid), f\"{why}: {look.party[pids.index(pid)].species}\"))\n",
              "    return (yield from choose(hands, \"party\", 0, why))  # MUTANT B22\n")],
            ["SkillTests.test_a_switch_by_pid_through_shift"]),
    "B23": (CAUGHT, "the bag's pocket not switched to the item's (the open pocket used)",
            [(SKILL, "        if ui.pocket != pocket:\n", "        if False:  # MUTANT B23\n")],
            ["SkillTests.test_a_ball_from_the_ball_pocket"]),
    "B24": (CAUGHT, "the battle's yes/no always answered on YES (the answer not moved to)",
            [(SKILL, "            if not (yield from choose(hands, BATTLE_YES_NO, 0 if yes else 1, f\"{why}: {reason}\")):\n",
              "            if not (yield from choose(hands, BATTLE_YES_NO, 0, f\"{why}: {reason}\")):  # MUTANT B24\n")],
            ["SkillTests.test_the_questions_are_answered_on_the_option_wanted"]),
    "B25": (CAUGHT, "the party list taking input whatever task runs",
            [(SCREENS, "        accepts = \"Task_HandleChooseMonInput\" in tasks if raw.get(\"party_tasks_known\") else True\n",
              "        accepts = True  # MUTANT B25\n")],
            ["EyesTests.test_the_bag_list_and_the_party_take_input_only_while_their_task_runs"]),
    "B26": (CAUGHT, "the level-up stats box not a wait",
            [(SCREENS, "    0x6C: ((6, 8), \"battle level-up stats box (any key)\"),\n", "")],
            ["EyesTests.test_the_new_waits"]),
    "B27": (CAUGHT, "the caught Pokemon's Pokedex page not a wait",
            [(SCREENS, "    \"Task_HandleCaughtMonPageInput\": \"A or B\",  # src/pokedex.c\n", "")],
            ["EyesTests.test_the_new_waits"]),
    "B28": (CAUGHT, "a 2 x 2 grid's frames waiting for input counted against its presses (the step-4 fix reverted)",
            [(FLEE, "            waited += 1\n", "            presses += 1  # MUTANT B28\n")],
            ["SkillTests.test_a_ball_from_the_ball_pocket"]),
    "B29": (CAUGHT, "training goes on with its strongest Pokemon fainted",
            [(BATTLE, "    if strongest.hp <= 0:\n", "    if False:  # MUTANT B29\n")],
            ["LearnTests.test_needs_rest"]),
    "B30": (CAUGHT, "a dual type's second type ignored by the type chart",
            [(FACTS, "    for defend in dict.fromkeys(defender_types):\n",
              "    for defend in list(dict.fromkeys(defender_types))[:1]:  # MUTANT B30\n")],
            ["KnowledgeTests.test_the_type_chart"]),
    # ---- (the step-4 verifier's round) the field remembered through the party menu, the refusal read, the recoil's caps
    "B31": (CAUGHT, "the field not remembered: the replacement sees only the party menu's look (the step-4 bug)",
            [(BATTLE, "        if self.faults.forget_field or self.field is None:\n", "        if True:  # MUTANT B31\n")],
            ["FieldTests.test_a_double_battles_partner_faints_the_one_still_standing_is_not_sent",
             "FieldTests.test_a_single_battles_replacement_is_matched_against_the_remembered_foe",
             "SkillTests.test_the_partner_faints_the_field_is_remembered_through_the_party_menu"]),
    "B32": (CAUGHT, "the party menu's refusal not read (watched until the bound, the step-4 skill)",
            [(SKILL, "        if messages and look.screen.waits_for_button:\n", "        if False:  # MUTANT B32\n")],
            ["SkillTests.test_fault_forget_field_is_refused_and_read_and_another_goes_in",
             "SkillTests.test_a_battle_resumed_on_the_refusal_reads_it_and_sends_another"]),
    "B33": (CAUGHT, "the decider forgets whom it sent in since the turn began",
            [(BATTLE, "        out = set(standing) | self.sent_since | set(self.refused)\n",
              "        out = set(standing) | set(self.refused)  # MUTANT B33\n")],
            ["FieldTests.test_both_fell_the_second_choice_is_not_the_first",
             "SkillTests.test_both_fell_two_party_menus_two_different_pokemon"]),
    "B34": (CAUGHT, "the skill does not tell the decider whom it sent in",
            [(SKILL, "            mind.sent(pid)\n", "            pass  # MUTANT B34\n")],
            ["SkillTests.test_both_fell_two_party_menus_two_different_pokemon"]),
    "B35": (CAUGHT, "a refused member chosen again",
            [(BATTLE, "        out = set(standing) | self.sent_since | set(self.refused)\n",
              "        out = set(standing) | self.sent_since  # MUTANT B35\n")],
            ["FieldTests.test_a_refused_member_is_not_chosen_again_until_the_next_turn",
             "SkillTests.test_fault_forget_field_is_refused_and_read_and_another_goes_in"]),
    "B36": (CAUGHT, "the recoil charged on the whole hit though the foe has less HP left (no cap at what the hit can take)",
            [(BATTLE, "        landed = min(1.0, left / share)\n", "        landed = 1.0  # MUTANT B36\n")],
            ["RecordedRecoilTests.test_its_recoil_is_a_share_of_what_the_foe_has_left",
             "RecordedRecoilTests.test_fault_overkill_take_down_at_full_hp_and_at_20_percent_never_when_its_recoil_would_faint_it"]),
    "B37": (CAUGHT, "Jump Kick's miss recoil not capped at half the target's max HP",
            [(BATTLE, "            miss_capped = min(1.0, 1.0 / share)\n", "            miss_capped = 1.0  # MUTANT B37\n")],
            ["RecoilTests.test_jump_kicks_miss_recoil_is_capped_at_half_the_targets_max_hp"]),
    "B38": (CAUGHT, "a recoil that would knock the user out not charged as such",
            [(BATTLE, "    faints = user_battler.hp is not None and recoil_hp >= user_battler.hp\n",
              "    faints = False  # MUTANT B38\n")],
            ["RecoilTests.test_a_recoil_that_would_faint_the_user_costs_the_whole_worth",
             "RecordedRecoilTests.test_fault_overkill_take_down_at_full_hp_and_at_20_percent_never_when_its_recoil_would_faint_it"]),
    "B39": (CAUGHT, "a refusal on screen before any choice of its own: the member refused not told to the decider",
            [(SKILL, "                if kind == \"party\" and refused is not None:\n",
              "                if False:  # MUTANT B39\n")],
            ["SkillTests.test_a_battle_resumed_on_the_refusal_reads_it_and_sends_another"]),
    "B40": (CAUGHT, "the refusals and the sent-ins never forgotten at a new turn",
            [(BATTLE, "            self.sent_since, self.refused = set(), {}\n", "            pass  # MUTANT B40\n")],
            ["FieldTests.test_a_refused_member_is_not_chosen_again_until_the_next_turn"]),
    "B41": (CAUGHT, "the skill does not show the decider its looks (no field to remember)",
            [(SKILL, "        self.mind.see(look)\n", "        pass  # MUTANT B41\n")],
            ["SkillTests.test_the_partner_faints_the_field_is_remembered_through_the_party_menu"]),
    # ---- the step-4 verifier's second round (its weak proofs)
    "B42": (CAUGHT, "a refused SWITCH not closed with B: the party menu left open after the game refused the shift",
            [(SKILL, "            yield from hands.pad.press(\"B\", reason, f\"party cursor on {look.screen.ui.cursor}, the switch refused \"\n",
              "            (lambda *a: None)(\"B\", reason, f\"party cursor on {look.screen.ui.cursor}, the switch refused \"  # MUTANT B42\n")],
            ["SkillTests.test_a_refused_switch_goes_back_to_the_battles_menu_and_fights"]),
    "B43": (CAUGHT, "the type chart's sentence wrong: every choice said DECISIVE (the sweep's TYPE-DECISIONS would count "
                    "neutral choices as type decisions)",
            [(BATTLE, "        return bool(self.near) and self.blind not in self.near\n", "        return True  # MUTANT B43\n")],
            ["TypeTests.test_the_choice_says_what_the_type_chart_changed"]),
    # ---- step 4.1 (the step-4 verifier's and adversarial review's findings)
    "B44": (CAUGHT, "finding 1: the shift question answered about the foe on the field (the FAINTED one, step 4)",
            [(BATTLE, "            foe, said = incoming(f\"{context} {question}\", on_field)\n",
              "            foe, said = on_field, \"the foe on the field\"  # MUTANT B44\n")],
            ["ShiftTests.test_the_question_is_about_the_incoming_species_named_in_the_words",
             "SkillTests.test_the_shift_question_sends_the_member_decided_against_the_incoming_foe"]),
    "B45": (CAUGHT, "finding 1: the member chosen at the shift question NOT carried into the party menu (ranked by level, step 4)",
            [(BATTLE, "        if (chosen is not None and chosen not in out and not self.faults.shift_fainted\n",
              "        if (False  # MUTANT B45\n")],
            ["ShiftTests.test_a_yes_is_carried_into_the_party_menu",
             "SkillTests.test_the_shift_question_sends_the_member_decided_against_the_incoming_foe"]),
    "B46": (CAUGHT, "finding 2: a move the game refused not remembered for the turn (\"decide again\" picks it again)",
            [(BATTLE, "            self.unusable[self.last_chosen] = words\n", "            pass  # MUTANT B46\n")],
            ["UnusableTests.test_a_refused_move_is_out_until_the_next_turn",
             "SkillTests.test_a_refused_move_is_not_chosen_again_that_turn"]),
    "B47": (CAUGHT, "finding 2: the skill does not tell the decider the move grid came back",
            [(SKILL, "            refused = mind.cannot_use(words)\n", "            refused = None  # MUTANT B47\n")],
            ["SkillTests.test_a_refused_move_is_not_chosen_again_that_turn"]),
    "B48": (CAUGHT, "a Potion's target chosen as step 4 did: the party menu's message after it not read (the battle stuck)",
            [(SKILL, "            if not (yield from _give_item(hands, decision.target_pid, item, reason)):\n",
              "            if not (yield from _pick_member(hands, decision.target_pid, reason)):  # MUTANT B48\n")],
            ["SkillTests.test_a_potion_is_given_and_its_message_read"]),
    "B49": (CAUGHT, "finding 4: the foe's LIVE types (gBattleMons) used, not its species'",
            [(BATTLE, "    return fact.types if fact is not None else mon.types\n", "    return mon.types  # MUTANT B49\n")],
            ["HiddenInfoTests.test_the_foes_types_are_its_species_not_the_live_ones"]),
    "B50": (CAUGHT, "finding 4: a hit's damage from the exact formula, not a person's rough sense",
            [(BATTLE, "    return max(ROUGH_STEP / 2, round(share / ROUGH_STEP) * ROUGH_STEP)\n", "    return share  # MUTANT B50\n")],
            ["HiddenInfoTests.test_a_hit_is_a_rough_sense_not_the_exact_formula"]),
    "B51": (CAUGHT, "finding 4: the hidden catch rate back in the ball choice (step 4: a better ball under catch rate 100)",
            [(BATTLE, "        if mem.throws >= 2:\n            cues.append(f\"{mem.throws} missed\")\n",
              "        if mem.throws >= 2 or species_fact(foe.species).catch_rate < 100:  # MUTANT B51\n"
              "            cues.append(f\"{mem.throws} missed\")\n")],
            ["CatchTests.test_the_ball_by_what_a_person_sees_not_the_catch_rate"]),
    "B52": (CAUGHT, "finding 6: overkill valued again (a move that finishes the foe worth only its power)",
            [(BATTLE, "    finishes = ko_worth is not None and effectiveness > 0 and not faults.overkill\n",
              "    finishes = False  # MUTANT B52\n")],
            ["RecordedRecoilTests.test_overkill_every_move_finishes_it_so_take_down_never",
             "OverkillTests.test_moves_that_all_finish_it_compare_by_hit_chance_and_recoil"]),
    "B53": (CAUGHT, "finding 5: never an opening move (step 4)",
            [(BATTLE, "        if self.rng.random() >= self.temper.opener:\n", "        if True:  # MUTANT B53\n")],
            ["OpenerTests.test_an_opening_move_by_temperament_on_a_safe_first_turn"]),
    "B54": (CAUGHT, "finding 5: an opening status move whether or not it is safe",
            [(BATTLE, "        unsafe = self._safe_for_status(own, foe, hp_share, OPENER_HP)\n", "        unsafe = None  # MUTANT B54\n")],
            ["OpenerTests.test_never_a_status_move_when_it_is_not_safe"]),
    "B55": (CAUGHT, "finding 5: no sleep or paralysis move to help a catch",
            [(BATTLE, "        status = self._catch_status(own, foe, hp_share, values)\n", "        status = None  # MUTANT B55\n")],
            ["OpenerTests.test_a_sleep_or_paralysis_move_helps_a_catch"]),
    "B56": (CAUGHT, "finding 5: a catch's status move even when its own HP is low",
            [(BATTLE, "        unsafe = self._safe_for_status(own, foe, hp_share, CATCH_STATUS_HP, opener=False)\n",
              "        unsafe = None  # MUTANT B56\n")],
            ["OpenerTests.test_a_sleep_or_paralysis_move_helps_a_catch"]),
    "B57": (CAUGHT, "finding 5: Thunder Wave tried on a Ground type (no type check of a status move)",
            [(BATTLE, "            if fact.effect == \"PARALYZE\" and fact.type == \"Electric\" and \"Ground\" in types:\n                continue\n", "")],
            ["OpenerTests.test_a_sleep_or_paralysis_move_helps_a_catch"]),
    # ---- step 4.1 ROUND 2 (the step-4.1 verifier's findings)
    "B58": (CAUGHT, "the verifier's minor: the shift question's species read to the first '.' ('MR. MIME' -> 'MR': no species)",
            [(BATTLE, "    for cut in sorted({m.start() for m in re.finditer(r\"[.!?]\", rest)}, reverse=True):\n",
              "    for cut in sorted({m.start() for m in re.finditer(r\"[.!?]\", rest)})[:1]:  # MUTANT B58\n")],
            ["ShiftTests.test_a_species_whose_name_has_a_full_stop_or_a_sign_is_read_whole"]),
    "B59": (CAUGHT, "finding 5 (its verifier: the STATUS count): an opener the draw passed over not SAID (the sweep cannot "
                    "count the rule's chances)",
            [(BATTLE, "        if self.opener_passed:\n", "        if False:  # MUTANT B59\n")],
            ["OpenerTests.test_every_chance_of_an_opener_is_said_drawn_or_passed_over"]),
    # ---- step 4.1 ROUND 3 (the step-4.1 verifier's second round: "hidden information is still used")
    "B60": (CAUGHT, "the foe's SPECIES' base stats back in the damage estimate and its max HP (step 4.1 round 2: hidden "
                    "information)",
            [(BATTLE, "    defense = typical_stat(\"defense\" if physical else \"sp_defense\", foe.level)\n",
              "    _species = species_fact(foe.species)  # MUTANT B60\n"
              "    defense = estimate_stat(_species.defense if physical else _species.sp_defense, foe.level)\n"),
             (BATTLE, "    return typical_stat(\"hp\", foe.level)\n",
              "    return estimate_stat(species_fact(foe.species).hp, foe.level, hp=True)  # MUTANT B60\n")],
            ["HiddenInfoTests.test_the_foes_base_stats_are_not_used_every_foe_of_a_level_is_guessed_alike",
             "RecordedRecoilTests.test_its_recoil_is_a_share_of_what_the_foe_has_left"]),
    "B61": (CAUGHT, "the hits SEEN on this foe ignored: the typical guess never corrected",
            [(BATTLE, "        hit = self.memory.seen_hit\n", "        hit = None  # MUTANT B61\n")],
            ["HiddenInfoTests.test_a_seen_hit_corrects_the_guess"]),
    "B62": (CAUGHT, "the bar's drop after its move not remembered as a hit SEEN",
            [(BATTLE, "                mem.seen_hit = (mem.last_move, mem.observed[mem.last_move])\n",
              "                pass  # MUTANT B62\n")],
            ["HiddenInfoTests.test_the_hit_it_saw_is_the_bars_drop_after_its_move"]),
}

DRIVER = '''
import json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
from ai_player.gates import test_battle
suite = unittest.defaultTestLoader.loadTestsFromModule(test_battle)
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(suite)
bad = {t.id().split("test_battle.", 1)[1]: kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)) for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "module": test_battle.__file__}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_step4_mutant_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    for relative, old, new in edits:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    (root / "run_step4_tests.py").write_text(DRIVER, encoding="utf-8")
    return root


def run(root: Path) -> tuple[dict | None, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_step4_tests.py")], cwd=str(root), env=env, capture_output=True,
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
    out = ["AI PLAYER BUILD STEP 4 - MUTANT PROOF OF THE BATTLES (gates/revert_step4.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
           f"code: {provenance(REPO)}",
           "Each mutant breaks ONE rule of the real code in a copy; CAUGHT = its predicted tests of gates/test_battle.py fail; "
           "REDUNDANT = no test fails, and the reason the rule is redundant alone is stated.", ""]
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
                # a subTest's failure is named "<test> (<params>)" or "<test> [<message>]"
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
        path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step4-REVERT.txt"
        keep_earlier(path)  # (step 4.1 round 3) an earlier tree's file is archived, not written over
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
