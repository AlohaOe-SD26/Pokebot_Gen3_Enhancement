"""UNIT PROOFS of boss preparation BP-1 (USER RULING 58, 2026-11-09): `brain/bossprep.py`, its wiring in `brain/goals.py`,
`brain/battle.py`'s `power` keyword and purpose "raise", `knowledge/seasoned.py` and `knowledge/atlas.py` boss_party.

    py -3.12 -B ai_player/gates/test_bossprep.py      (exit 0 = every test passed; offline, no emulator)

The spec is `PROJECT KNOWLEDGE/ai-research-notes/2026-11-08-BOSS-PREP-BP1-SPEC.md` (its tests T1-T11; T10 is driven live by
`gates/probe_bossprep.py --lead`, T12 is the A/B's). Every rule has a FAULT arm (the rule switched off through
`BossprepFaults`, a patched name, or the old rule called directly: the value it changes) beside its CONTROL (a value it must
NOT change), so no test passes vacuously. The mutant runner `gates/revert_bossprep.py` breaks each rule in a COPY.

THE SPEC'S NUMBERS AND THE BUILT ONES (`NameTieTests`): the spec's section 2 was computed by a scratch script whose boss
picked, among moves tied on points, the one with the greatest NAME (`max((points, name))`). The built verdict picks the
FASTER one (the worst case for the member, the spec's "a person's worst case"). Measured: with the name tie-break
(`BossprepFaults.name_tie`) the built code reproduces every section-2 number; with the shipped rule five cells move (Dustox
L16 vs MAKUHITA 0.38 -> 0.25, Wurmple's target 18 -> 19 at cost 352, Shroomish 24 -> 27, Poochyena never READY, C2's
MAKUHITA 0.35 -> 0.49). The tests below hold the SHIPPED numbers and pin the spec's beside them.

Fixtures are the spec's parties (section 2.2 and 2.5) with TYPICAL stats (no summary stats), and the real BRAWLY entry from
the knowledge (`boss_party`).

ROUND 2 (USER RULING 59, 2026-11-11; spec `ai-research-notes/2026-11-09-BOSS-PREP-BP1-RAISE-SPEC.md` section 5.1): R1
TraineeFloorTests (V-M1 reproduced through its FAULT arm, then fixed), R2 ExpModelTests (the gate-side model
`gates/exp_rule.py`), R3 RaiseTurnTests (switch-training, own fights, the rescue, the run, the replacement, "Use next"),
R4 FightSafeTests, R5 HealChoiceTests (a centre near, a Potion far), PartnerWornTests (the builder's addition: the raise
rests for a worn knock-out partner), R6 RaiseMapTests, R7 BudgetCountingTests (V-m3), R8 LeadAfterTests (V-m5), R9
OwnImmunityTests (V-m1). Two fixtures were moved from the spec's, by what the built rule computes (observed, then pinned):
R3b's own fight is Whismur L6 / Nincada L7, not Poochyena L7 (Confusion does nothing to a Dark type; Tackle alone needs 5
hits), and R3h's is Nincada L7 for the same reason.

ROUND 3 (2026-11-11; the round-2 verifier's V2-M1, V2-M2, V2-m3, the lead's design D1-D5): RescueTests (a refused run or
a trainee under its floor in a raise battle is rescued, R3n-R3s), PartnerLineTests (the rest line IS the battle's partner
line, against every wild Pokemon of the raise map), GuardTests and GuardRunnerTests (the trainee protected in every other
battle of an active plan, the boss fight left out), ShiftContextTests (the shift question's foe is in the screen's text),
LearnerKeptPageTests and SettleNotFirstTests (two of the verifier's REDUNDANT mutants given a test). Every rule a FAULT
arm beside its CONTROL; fixtures observed with s53/bp1r3/explore_fixtures.py, then pinned.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
import types
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.brain import bossprep as bp  # noqa: E402
from ai_player.brain import goals as goals_module  # noqa: E402
from ai_player.brain.battle import BattleMind, move_value, rough_share  # noqa: E402
from ai_player.brain.goals import Goal, GoalRunner, training_rest  # noqa: E402
from ai_player.eyes.observation import BattleMon, MenuView, MonSummary, MoveSlot  # noqa: E402
from ai_player.game_memory import goals_part, restore_goals  # noqa: E402
from ai_player.gates.test_battle import foe, look as battle_look, member, mon as battle_mon  # noqa: E402
from ai_player.gates.test_goals import ch_proofs, look, manager, world_with  # noqa: E402
from ai_player.knowledge import facts, seasoned  # noqa: E402
from ai_player.knowledge.atlas import BossMon, boss_party  # noqa: E402
from ai_player.knowledge.facts import move_fact, move_named, species_fact, species_named  # noqa: E402
from ai_player.knowledge.story import load_story  # noqa: E402
from ai_player.personality import ERRANDS  # noqa: E402

TEAM = boss_party("BRAWLY")
F = bp.BossprepFaults
#: (T1 CONTROL) the digest of move_value and rough_share over every move x every type set and every species, computed by
#: the PARENT commit 18c3d51b's battle.py (s53/bp1/power_digest.py, the same algorithm as `power_none_digest`)
PARENT_DIGEST = "574b054db6639a5228f10e7bb8294575fd8f661af9f933ad1d415eed17b915a2"
PID = {"Grovyle": 0x1001, "Poochyena": 0x1002, "Wurmple": 0x1003, "Seedot": 0x1004, "Shroomish": 0x1005, "Cascoon": 0x1006}


def m(pid, species, level, moves, max_hp) -> bp.Member:
    return bp.Member(pid, species, level, max_hp, max_hp, tuple(moves))


def c1() -> list[bp.Member]:
    """C1's party at the start (spec section 2.2: probe-C1, RUSTBORO)."""
    return [m(PID["Grovyle"], "Grovyle", 21, ("Pound", "Pursuit", "Absorb", "Quick Attack"), 57),
            m(PID["Poochyena"], "Poochyena", 6, ("Tackle", "Howl"), 21), m(PID["Wurmple"], "Wurmple", 3, ("Tackle", "String Shot"), 16),
            m(PID["Seedot"], "Seedot", 3, ("Bide", "Harden"), 16), m(PID["Shroomish"], "Shroomish", 5, ("Absorb", "Tackle"), 21),
            m(PID["Cascoon"], "Cascoon", 5, ("Harden",), 20)]


def c2(level: int = 23, hp: int = 69) -> list[bp.Member]:
    return [m(1, "Combusken", level, ("Scratch", "Ember", "Double Kick", "Peck"), hp), m(2, "Wurmple", 4, ("Tackle", "String Shot"), 18),
            m(3, "Poochyena", 3, ("Tackle",), 15), m(4, "Lotad", 4, ("Astonish", "Growl"), 18),
            m(5, "Zigzagoon", 4, ("Tackle", "Growl"), 17), m(6, "Seedot", 3, ("Bide", "Harden"), 15)]


def c3() -> list[bp.Member]:
    return [m(1, "Marshtomp", 25, ("Tackle", "Bide", "Mud Shot", "Water Gun"), 77), m(2, "Poochyena", 8, ("Tackle", "Howl"), 24),
            m(3, "Ralts", 4, ("Growl",), 17), m(4, "Wurmple", 3, ("Tackle", "String Shot"), 15),
            m(5, "Zigzagoon", 3, ("Tackle", "Growl"), 15), m(6, "Seedot", 3, ("Bide", "Harden"), 15)]


def duel(member_, boss, faults=bp.NO_FAULTS) -> bp.Verdict:
    return bp.verdict([member_], member_.pid, [boss], "Story", faults)


def options_of(party, faults=bp.NO_FAULTS, personality="Story"):
    found, said = bp.options(party, TEAM, personality, faults)
    return [(o.species, o.target, o.cost) for o in found], said


def projected(species_member: bp.Member, level: int, faults=bp.NO_FAULTS) -> list[bp.Member]:
    return bp.project(species_member, level, faults)


def worst_branch(member_: bp.Member, level: int, party: list[bp.Member], faults=bp.NO_FAULTS) -> bp.Member:
    """The branch the options judge by (the lower class, then the lower party left), the member leading."""
    index = next(i for i, x in enumerate(party) if x.pid == member_.pid)
    ranked = []
    for branch in bp.project(member_, level, faults):
        trial = list(party)
        trial[index] = branch
        result = bp.verdict(trial, branch.pid, TEAM, "Story", faults)
        ranked.append(((bp._RANK[result.cls], result.party_left), branch))
    return min(ranked, key=lambda item: item[0])[1]


def power_none_digest() -> str:
    """move_value and rough_share with `power` left out, over every move x every type set (move_value) and every species
    (rough_share): the same algorithm as s53/bp1/power_digest.py, which computed PARENT_DIGEST on the parent commit."""
    h = hashlib.sha256()
    kinds = list(facts._load("types.json")["types"])
    type_sets = [(t,) for t in kinds] + [(a, b) for i, a in enumerate(kinds) for b in kinds[i + 1:]]
    species = sorted(facts._load("species.json")["species"])
    user = BattleMon("Machop", 0, 20, None, None, 48, "", (), ())
    for name in sorted(facts._load("moves.json")["moves"]):
        fact = facts.move_fact(name)
        slot = MoveSlot(name, fact.type, fact.power, 10, 10)
        for foe_types in type_sets:
            h.update(repr((name, foe_types, move_value(0, slot, ("Normal",), 20, 0.6, foe_types))).encode())
        for kind in species:
            other = BattleMon(kind, 0, 18, None, None, 48, "", (), ())
            h.update(repr((name, kind, rough_share(slot, None, user, other))).encode())
    return h.hexdigest()


# ------------------------------------------------------------------------------------------- T1 the two halves
class TwoHalvesTests(unittest.TestCase):
    """T1: the attack half and the threat half are the battle brain's own `move_value` both ways (S1)."""

    def dustox18(self) -> bp.Member:
        return projected(c1()[5], 18)[0]

    def test_dustox_l18_against_brawly(self):
        dustox = self.dustox18()
        self.assertEqual((dustox.species, dustox.moves), ("Dustox", ("Harden", "Confusion", "Gust", "Protect")))
        a = bp.attack_half(dustox, TEAM[0])
        t = bp.threat_half(TEAM[0], dustox)
        self.assertEqual((a.name, round(a.value), a.effectiveness), ("Confusion", 100, 2.0))
        self.assertEqual((t.name, round(t.value)), ("Seismic Toss", 30))
        result = duel(dustox, TEAM[0])
        self.assertEqual(len(result.kos), 1)
        self.assertEqual(round(result.party_left * 53), 21)  # WIN with 21 of 53 (the spec's hand check, section 2.4)
        gust = bp.attack_half(dustox, TEAM[1])
        self.assertEqual((gust.name, round(gust.value), gust.effectiveness), ("Gust", 80, 2.0))

    def test_fault_types_only(self):
        """FAULT: the attack half valued with no types: Dustox L18 against MEDITITE picks Confusion at 50 (x1), and C2 at
        L23, CLOSE, falls to NOT READY (Combusken picks Scratch; MAKUHITA stands at 0.71 with the shipped tie-break)."""
        dustox = self.dustox18()
        a = bp.attack_half(dustox, TEAM[1], faults=F(types_only=True))
        self.assertEqual((a.name, round(a.value), a.effectiveness), ("Confusion", 50, 1.0))
        self.assertEqual(bp.verdict(c2(), 1, TEAM, "Catcher").cls, bp.CLOSE)
        broken = bp.verdict(c2(), 1, TEAM, "Catcher", F(types_only=True))
        self.assertEqual((broken.cls, broken.standing), (bp.NOT_READY, ("Makuhita", 0.7091)))
        self.assertIn("Combusken L23 (Scratch)", broken.line())

    def test_fault_moves_only(self):
        """FAULT: the threat half ignored (only fixed damage hurts): C2 L23 CLOSE -> READY 0.79, and C1's cheapest option
        is no longer Wurmple (Poochyena L10, cost 64)."""
        broken = bp.verdict(c2(), 1, TEAM, "Catcher", F(moves_only=True))
        self.assertEqual((broken.cls, round(broken.party_left, 2)), (bp.READY, 0.79))
        found, _ = options_of(c1(), F(moves_only=True))
        self.assertEqual(found[0], ("Poochyena", 10, 64))
        self.assertEqual(options_of(c1())[0][0], ("Wurmple", 19, 352))  # CONTROL: the shipped plan

    def test_fault_fp_always(self):
        """FAULT: Focus Punch never fails: Grovyle L21 against MEDITITE, a WIN at full HP, is a LOSS."""
        grovyle = c1()[0]
        self.assertEqual((len(duel(grovyle, TEAM[1]).kos), duel(grovyle, TEAM[1]).party_left), (1, 1.0))
        self.assertEqual(duel(grovyle, TEAM[1], F(fp_always=True)).kos, ())

    def test_control_grovyle_is_the_same_under_types_only(self):
        """CONTROL: Grovyle L21's Normal moves get no type and no STAB either way: its row does not move."""
        grovyle = c1()[0]
        for boss in TEAM:
            for faults in (bp.NO_FAULTS, F(types_only=True)):
                a = bp.attack_half(grovyle, boss, faults=faults)
                self.assertEqual((a.name, round(a.value), a.effectiveness), ("Pound", 40, 1.0), (boss, faults))
            self.assertEqual(duel(grovyle, boss).line(), duel(grovyle, boss, F(types_only=True)).line())

    def test_control_power_none_is_byte_identical_to_the_parent(self):
        """CONTROL: with `power` left out, move_value and rough_share give exactly the parent commit's values for every
        move against every type set and every species (today's callers are unchanged)."""
        self.assertEqual(power_none_digest(), PARENT_DIGEST)

    def test_the_verdict_powers(self):
        """Low Kick 60; Reversal by its user's HP share (FLAIL_TABLE); Arm Thrust x3; FAULT flail_flat: printed (1)."""
        self.assertEqual(bp.verdict_slot("Low Kick")[1], 60.0)
        self.assertEqual(bp.verdict_slot("Arm Thrust")[1], 45.0)
        self.assertEqual([bp.verdict_slot("Reversal", share)[1] for share in (1.0, 0.5, 0.3, 0.15, 0.05, 0.0)],
                         [20.0, 40.0, 80.0, 100.0, 150.0, 200.0])
        self.assertIsNone(bp.verdict_slot("Reversal", 0.05, F(flail_flat=True))[1])
        self.assertIsNone(bp.verdict_slot("Karate Chop")[1])


# ------------------------------------------------------------------------------------------- T2 fixed damage
class FixedDamageTests(unittest.TestCase):
    """T2 (M1): Seismic Toss does the user's LEVEL whatever the typing, and nothing to an immune type."""

    def test_seismic_toss_is_the_level(self):
        dustox = projected(c1()[5], 18)[0]
        shuppet = m(9, "Shuppet", 18, ("Night Shade",), 50)
        self.assertEqual(species_fact("Shuppet").types, ("Ghost",))
        for target, points in ((dustox, 16), (c1()[0], 16), (shuppet, 0)):
            self.assertEqual(bp.hit_points(TEAM[0], target, "Seismic Toss", 1.0, True, target.hp), points, target)
        self.assertEqual(bp.hit_points(TEAM[0], dustox, "Seismic Toss", 1.0, True, 53, F(fixed_resisted=True)), 4)
        self.assertEqual(bp.hit_points(TEAM[0], shuppet, "Seismic Toss", 1.0, True, 50, F(no_immunity=True)), 16)

    def test_fault_fixed_resisted_moves_the_plan(self):
        """FAULT: Seismic Toss scaled by the chart: Wurmple's target 19 -> 13 (its worst branch then Beautifly), and the
        cocoon's (were it eligible) 20 -> 13."""
        found = dict((s, t) for s, t, _ in options_of(c1())[0])
        self.assertEqual(found["Wurmple"], 19)
        broken = options_of(c1(), F(fixed_resisted=True))[0]
        self.assertEqual(dict((s, t) for s, t, _ in broken)["Wurmple"], 13)
        self.assertEqual(worst_branch(c1()[2], 13, c1(), F(fixed_resisted=True)).species, "Beautifly")
        cocoon = dict((s, t) for s, t, _ in options_of(c1(), F(eligible_cocoon=True))[0])["Cascoon"]
        cocoon_broken = dict((s, t) for s, t, _ in options_of(c1(), F(eligible_cocoon=True, fixed_resisted=True))[0])["Cascoon"]
        self.assertEqual((cocoon, cocoon_broken), (20, 13))

    def test_control_fixed_resisted_leaves_grovyle_and_c3(self):
        """CONTROL: Grovyle (Grass: x1 to Fighting) keeps its option at L30, and C3 its READY 0.58."""
        for faults in (bp.NO_FAULTS, F(fixed_resisted=True)):
            self.assertEqual(dict((s, t) for s, t, _ in options_of(c1(), faults)[0])["Grovyle"], 30)
            result = bp.verdict(c3(), 1, TEAM, "Trainer", faults)
            self.assertEqual((result.cls, round(result.party_left, 2)), (bp.READY, 0.58))


# ------------------------------------------------------------------------------------------- T3 the classes
class VerdictClassTests(unittest.TestCase):
    """T3 (section 2.5): the verdicts on the three runs' parties at their fights, and today's rule beside them."""

    def test_the_calibration_runs(self):
        at_fight = c1()
        at_fight[0] = m(PID["Grovyle"], "Grovyle", 22, at_fight[0].moves, 60)
        result = bp.verdict(at_fight, PID["Grovyle"], TEAM, "Story")
        self.assertEqual((result.cls, result.standing), (bp.NOT_READY, ("Machop", 0.25)))
        for level, hp in ((23, 69), (24, 71)):
            result = bp.verdict(c2(level, hp), 1, TEAM, "Catcher")
            self.assertEqual((result.cls, result.standing), (bp.CLOSE, ("Makuhita", 0.4909)), level)
        result = bp.verdict(c3(), 1, TEAM, "Trainer")
        self.assertEqual((result.cls, round(result.party_left, 2)), (bp.READY, 0.58))
        self.assertEqual([k[2] for k in result.kos], ["Marshtomp"] * 3)

    def test_fault_strongest_level_is_todays_rule(self):
        """FAULT: today's rule (the strongest level against the top level + the margin): C1 reads READY (22 >= 20)."""
        self.assertEqual(bp.verdict(c1(), PID["Grovyle"], TEAM, "Story").cls, bp.NOT_READY)
        self.assertEqual(bp.verdict(c1(), PID["Grovyle"], TEAM, "Story", F(strongest_level=True)).cls, bp.READY)

    def test_fault_no_sitrus(self):
        """FAULT: MAKUHITA's Sitrus Berry ignored: Dustox L18 against it 0.23 -> 0.60, C3 0.58 -> 0.69, Wurmple's target
        19 -> 18."""
        dustox = projected(c1()[5], 18)[0]
        self.assertEqual(round(duel(dustox, TEAM[2]).party_left, 2), 0.23)
        self.assertEqual(round(duel(dustox, TEAM[2], F(no_sitrus=True)).party_left, 2), 0.60)
        self.assertEqual(round(bp.verdict(c3(), 1, TEAM, "Trainer", F(no_sitrus=True)).party_left, 2), 0.69)
        self.assertEqual(options_of(c1(), F(no_sitrus=True))[0][0], ("Wurmple", 18, 315))

    def test_control_no_sitrus_leaves_c1(self):
        """CONTROL: C1 falls against MACHOP, the first: the berry never comes into it."""
        self.assertEqual(bp.verdict(c1(), PID["Grovyle"], TEAM, "Story").line(),
                         bp.verdict(c1(), PID["Grovyle"], TEAM, "Story", F(no_sitrus=True)).line())

    def test_fault_flail_flat(self):
        """FAULT: Reversal at its printed power 1: Dustox L18 against MAKUHITA 0.23 -> 0.34."""
        dustox = projected(c1()[5], 18)[0]
        self.assertEqual(round(duel(dustox, TEAM[2], F(flail_flat=True)).party_left, 2), 0.34)


class NameTieTests(unittest.TestCase):
    """The spec's section 2 numbers, reproduced with the spec script's tie-break (by NAME), beside the shipped rule."""

    def test_the_spec_numbers_with_the_name_tie_break(self):
        tie = F(name_tie=True)
        dustox16 = projected(c1()[5], 16)[0]
        self.assertEqual(round(duel(dustox16, TEAM[2], tie).party_left, 2), 0.38)
        self.assertEqual(round(duel(dustox16, TEAM[2]).party_left, 2), 0.25)
        self.assertEqual(options_of(c1(), tie)[0], [("Wurmple", 18, 315), ("Grovyle", 30, 459), ("Shroomish", 24, 551),
                                                    ("Poochyena", 30, 864)])
        self.assertEqual(bp.verdict(c2(), 1, TEAM, "Catcher", tie).standing, ("Makuhita", 0.3455))


# ------------------------------------------------------------------------------------------- T4 projection
class ProjectionTests(unittest.TestCase):
    """T4 (M3): a member is judged at the level it would REACH, with its evolutions and its level-up moves."""

    def test_wurmple_and_cascoon(self):
        branches = projected(c1()[2], 18)
        self.assertEqual(sorted(b.species for b in branches), ["Beautifly", "Dustox"])
        worst = worst_branch(c1()[2], 18, c1())
        self.assertEqual((worst.species, worst.moves), ("Dustox", ("Tackle", "Confusion", "Poison Sting", "Gust")))
        self.assertEqual(projected(c1()[5], 13)[0].moves, ("Harden", "Confusion", "Gust"))
        self.assertEqual(projected(c1()[5], 20)[0].moves, ("Moonlight", "Confusion", "Gust", "Protect"))  # Harden forgotten
        self.assertEqual(projected(c1()[0], 29)[0].moves, ("Pound", "Pursuit", "Leaf Blade", "Quick Attack"))

    def test_fault_no_projection(self):
        """FAULT: the member keeps its species and moves: Wurmple, Grovyle and Shroomish are never READY by L30."""
        found, said = options_of(c1(), F(no_projection=True))
        self.assertEqual(found, [])
        self.assertTrue(any(s.startswith("Wurmple L3: never READY") for s in said), said)
        self.assertTrue(any(s.startswith("Grovyle L21: never READY") for s in said), said)

    def test_control_its_own_level_is_itself(self):
        for member_ in c1():
            self.assertEqual(bp.project(member_, member_.level), [member_])
            self.assertEqual(bp.project(member_, member_.level, F(no_projection=True)), [member_])


# ------------------------------------------------------------------------------------------- T5 the plan
def summary(slot: int, species: str, level: int, moves, max_hp: int, hp: int | None = None, experience: int = 0,
            pid: int | None = None) -> MonSummary:
    fact = species_fact(species)
    slots = tuple(MoveSlot(n, move_fact(n).type, move_fact(n).power, 10, 10) for n in moves)
    return MonSummary(slot, species, fact.dex, level, max_hp if hp is None else hp, max_hp, "", fact.types, slots,
                      PID[species] if pid is None else pid, 1, False, experience, ())


def c1_party(**hp: int) -> list[MonSummary]:
    return [summary(i, x.species, x.level, x.moves, x.max_hp, hp.get(x.species)) for i, x in enumerate(c1())]


def c1_manager(personality: str = "Story", seed: int = 1):
    mgr = manager(personality, seed=seed)
    mgr.bossprep_rng = random.Random(f"{seed}:bossprep")
    return mgr


def at(milestone_id: str):
    story = load_story("BOY")
    index = story.index(milestone_id)
    return story.milestones[index], index


def c1_decide(mgr, party=None, const="ROUTE104", milestone_id="ch6_briney_house", world=None):
    milestone, index = at(milestone_id)
    world = world or world_with(const, current=const, grass=True)
    seen = look(ch_proofs(milestone_id), party=party if party is not None else c1_party(), const=const)
    return mgr.next_goal(seen, world, milestone, index), world


class PlanTests(unittest.TestCase):
    """T5 (section 1.6, 2.6): the options, the draw, the commit; the Trainer logs only."""

    def test_c1_options(self):
        found, said = options_of(c1())
        self.assertEqual(found, [("Wurmple", 19, 352), ("Grovyle", 30, 459), ("Shroomish", 27, 704)])
        self.assertIn("Cascoon L5: no damaging move to win its own battles (switch training: BP-2)", said)
        self.assertIn("Seedot L3: never READY by L30", said)

    def test_the_plan_is_wurmple_on_twenty_seeds(self):
        found, _ = bp.options(c1(), TEAM, "Story")
        for seed in range(20):
            choice, _ = bp.choose_plan(random.Random(f"{seed}:bossprep"), bp.near_best("Story"), found)
            self.assertEqual((choice.species, choice.target), ("Wurmple", 19), seed)

    def test_fault_eligible_cocoon(self):
        """FAULT: a member with no damaging move may be raised: Cascoon (375) joins the near-best set (<= 352 / 0.85)."""
        found, _ = bp.options(c1(), TEAM, "Story", F(eligible_cocoon=True))
        picks = {bp.choose_plan(random.Random(f"{seed}:bossprep"), 0.85, found)[0].species for seed in range(20)}
        self.assertEqual(picks, {"Wurmple", "Cascoon"})

    def test_fault_cost_by_level_gap(self):
        """FAULT: the cost by levels to gain, not their squares: Grovyle (9) beats Wurmple (16)."""
        found, _ = options_of(c1(), F(cost_by_level_gap=True))
        self.assertEqual(found[0], ("Grovyle", 30, 9))
        self.assertIn(("Wurmple", 19, 16), found)

    def test_the_story_run_gets_a_raise_goal(self):
        mgr = c1_manager()
        goal, _ = c1_decide(mgr)
        record = mgr.bp_record("ch7_brawly")
        # (round 2, BP1-L2) one cooldown key a raise map
        self.assertEqual((goal.kind, goal.map, goal.milestone, goal.key),
                         ("raise", "ROUTE104", "ch7_brawly", "raise:ROUTE104"))
        self.assertEqual((record["status"], record["trainee"], record["target"], record["plan"]),
                         ("active", PID["Wurmple"], 19, f"raise:{PID['Wurmple']:08x}:19"))

    def test_fault_rechoose_the_plan_is_committed(self):
        """The plan is stored ONCE (m10): a later change of the party (Grovyle a level up) runs the verdict again but
        draws and chooses nothing; FAULT (the record emptied, as a re-choice would): a second draw is made."""
        mgr = c1_manager()
        c1_decide(mgr)
        state = mgr.bossprep_rng.getstate()
        record = dict(mgr.bp_record("ch7_brawly"))
        party = c1_party()
        party[0] = replace(party[0], level=22)
        c1_decide(mgr, party)
        self.assertEqual(mgr.bossprep_rng.getstate(), state)
        self.assertEqual(mgr.bp_record("ch7_brawly")["plan"], record["plan"])
        mgr.bp_record("ch7_brawly")["status"] = "none"
        party[0] = replace(party[0], level=23)
        c1_decide(mgr, party)
        self.assertNotEqual(mgr.bossprep_rng.getstate(), state)

    def test_control_the_trainer_logs_and_plays_as_before(self):
        """CONTROL: a Trainer run on the same fixture gets no raise goal; its goal is the one it gets with no leader to act
        on (ACT_ON empty: the parent's behaviour), and the record says `logged` with the plan it would choose."""
        mgr = c1_manager("Trainer")
        goal, _ = c1_decide(mgr)
        record = mgr.bp_record("ch7_brawly")
        self.assertEqual((record["status"], record["trainee"]), ("logged", PID["Wurmple"]))
        with mock.patch.object(goals_module, "ACT_ON", frozenset()):
            parent, _ = c1_decide(c1_manager("Trainer"))
        self.assertNotEqual(goal.kind, "raise")
        self.assertEqual((goal.kind, goal.reason, goal.map), (parent.kind, parent.reason, parent.map))


# ------------------------------------------------------------------------------------------- T6 the trainee rule
class TraineeRuleTests(unittest.TestCase):
    """T6 (M4): the trainee's own state decides the rest, and a raise battle is the trainee's: no switch, no catch."""

    def test_the_rest_is_the_trainees(self):
        seen = look(party=c1_party(Wurmple=0))
        heal_below = ERRANDS["Story"].heal_below
        self.assertIn("has fainted", bp.trainee_rest(seen, PID["Wurmple"], heal_below, "Story"))
        self.assertIsNone(training_rest(seen, heal_below, "Story"))  # FAULT (today's rule): 135/151 = 89 %, Grovyle up
        self.assertIn("is low", bp.trainee_rest(look(party=c1_party(Wurmple=5)), PID["Wurmple"], heal_below, "Story"))
        healthy = look(party=c1_party())
        self.assertIsNone(bp.trainee_rest(healthy, PID["Wurmple"], heal_below, "Story"))  # CONTROL
        self.assertIsNone(training_rest(healthy, heal_below, "Story"))

    def switch_fixture(self):
        party = [member("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, 1), member("Grovyle", 16, ["Pound", "Absorb"], 40, 47, 2, 1)]
        return battle_look([battle_mon("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, pid=1)], [foe("Shroomish", 15)],
                           party=party, kind="wild", owned=(258, 285))

    def test_no_switch_while_raising(self):
        """Raise: it fights; CONTROL: the same battle trained switches to the much better Grovyle (the parent's rule)."""
        seen = self.switch_fixture()
        trained = BattleMind("Story", random.Random("1:battle"), "train").decide(seen)
        raised = BattleMind("Story", random.Random("1:battle"), "raise").decide(seen)
        self.assertEqual((trained.action, trained.switch_pid), ("switch", 2))
        self.assertEqual(raised.action, "fight")

    def test_no_catch_while_raising(self):
        """Raise: a wild species it has not caught is fought (the wish is still drawn: the stream does not shift);
        CONTROL: the Catcher training throws a ball at it."""
        seen = battle_look([battle_mon("Mudkip", 14, ["Tackle", "Water Gun"], 40, 42, pid=1)], [foe("Zigzagoon", 3, bar=20)],
                           owned=(258,))
        for purpose, action in (("train", "ball"), ("raise", "fight")):
            brain = BattleMind("Catcher", random.Random("1:battle"), purpose)
            brain.begin(seen)
            self.assertEqual(brain.decide(seen).action, action, purpose)
            self.assertEqual(brain.wishes, {"Zigzagoon": True}, purpose)

    def test_a_raise_runs_as_training_does(self):
        """`_run_or_not` treats raise as train: from a foe 6 levels up it runs; CONTROL: travelling, on a seed whose first
        draw is over the Story's run_travel (0.8), it fights (so the raise's run is the training rule, not the travel
        draw)."""
        seed = next(s for s in range(200) if random.Random(f"{s}:battle").random() >= 0.8)
        seen = battle_look([battle_mon("Wurmple", 3, ["Tackle", "String Shot"], 16, 16, pid=3)], [foe("Taillow", 9)])
        for purpose, action in (("raise", "run"), ("train", "run"), ("travel", "fight")):
            brain = BattleMind("Story", random.Random(f"{seed}:battle"), purpose)
            self.assertEqual(brain.decide(seen).action, action, purpose)

    def test_the_roam_hooks_install_the_trainee_rest(self):
        """The raise's roam asks the TRAINEE rule after each battle (with the watch first); a training roam asks today's."""
        from ai_player.gates.test_goals import RestTests

        nav = RestTests.navigator(RestTests(), [look(party=c1_party())])
        runner = GoalRunner(nav.hands, nav, manager("Story"), None, lambda line: None)
        fainted = look(party=c1_party(Wurmple=0))
        runner.roam_hooks()
        self.assertIsNone(nav.battle_rest(fainted))  # CONTROL: training looks at the strongest
        seen = []
        runner.roam_hooks(trainee=PID["Wurmple"], after_battle=lambda observation: seen.append(1))
        self.assertIn("has fainted", nav.battle_rest(fainted))
        self.assertEqual(seen, [1])
        runner.clear_roam_hooks()
        self.assertIsNone(nav.battle_rest)

    def runner(self):
        from ai_player.gates.test_goals import RestTests

        nav = RestTests.navigator(RestTests(), [look(party=c1_party())])
        mgr = c1_manager()
        record = mgr.prep(at("ch7_brawly")[0]).setdefault("bp", bp.new_record())
        record.update(status="active", trainee=PID["Wurmple"], target=19, plan=f"raise:{PID['Wurmple']:08x}:19")
        mind = types.SimpleNamespace(purpose="travel", trainee=None)
        return GoalRunner(nav.hands, nav, mgr, mind, lambda line: None), record

    def test_a_raise_goal_is_played_by_the_raise_with_its_purpose(self):
        """The runner plays a raise goal through `_raise`, with the battle purpose "raise"."""
        runner, _ = self.runner()
        seen = []

        def fake_raise(goal, moved_on):
            seen.append(runner.mind.purpose)
            yield
            return True, "roamed: fake"

        runner._raise = fake_raise
        milestone, index = at("ch6_briney_house")
        result = goals_module_drive(runner._pursue(Goal("raise", "r", "ch7_brawly", map="ROUTE104", steps=10, key="raise"),
                                                   milestone, index, lambda s: index))
        self.assertEqual((result, seen), ((True, "roamed: fake"), ["raise"]))

    def test_the_raise_puts_the_trainee_first_or_ends(self):
        """`_raise` asks the party-order hand FIRST; when the trainee cannot be put first it ends and counts a reorder
        failure (no walk, no roam)."""
        runner, record = self.runner()
        asked = []

        def no_lead(hands, pid, why):
            asked.append(pid)
            yield
            return False

        with mock.patch.object(goals_module, "lead_with", no_lead):
            result = goals_module_drive(runner._raise(Goal("raise", "r", "ch7_brawly", map="ROUTE104", steps=10, key="raise"),
                                                      lambda s: False))
        self.assertEqual(result, (False, "the trainee could not be put first"))
        self.assertEqual((asked, record["reorder_fails"], record["sessions"]), ([PID["Wurmple"]], 1, 1))

    def test_the_lead_goal_on_the_leaders_gym(self):
        """With the raise DONE, on the leader's gym map, a trainee not first is put back in the lead; CONTROL: elsewhere,
        or already first, no lead goal."""
        mgr = c1_manager()
        record = mgr.prep(at("ch7_brawly")[0]).setdefault("bp", bp.new_record())
        record.update(status="done", trainee=PID["Wurmple"], target=19, plan=f"raise:{PID['Wurmple']:08x}:19")
        goal, _ = c1_decide(mgr, milestone_id="ch7_brawly", const="DEWFORD_TOWN_GYM",
                            world=world_with("DEWFORD_TOWN_GYM", current="DEWFORD_TOWN_GYM"))
        self.assertEqual((goal.kind, goal.key), ("lead", "lead"))
        first = c1_party()
        first[0], first[2] = first[2], first[0]
        goal, _ = c1_decide(mgr, party=first, milestone_id="ch7_brawly", const="DEWFORD_TOWN_GYM",
                            world=world_with("DEWFORD_TOWN_GYM", current="DEWFORD_TOWN_GYM"))
        self.assertNotEqual(goal.kind, "lead")
        goal, _ = c1_decide(mgr, milestone_id="ch7_brawly", const="DEWFORD_TOWN",
                            world=world_with("DEWFORD_TOWN", current="DEWFORD_TOWN"))
        self.assertNotEqual(goal.kind, "lead")

    def test_the_raise_watch(self):
        """A battle not led by the trainee ends the roam and counts; a battle the trainee fainted in counts a leak. The
        lead is read at the first ACTION MENU: the looks before it may still show the LAST battle's battler (measured live,
        #112: Grovyle read as leading a battle Wurmple led). FAULT (the first look taken, the parent of this fix): the stale
        Grovyle reads as "not leading"; CONTROL: a real non-trainee at the action menu still does."""
        menu = MenuView(kind="battle_action", options=("FIGHT", "BAG", "POKéMON", "RUN"), cursor=0)
        grovyle = [battle_mon("Grovyle", 21, ["Pound"], 57, 57, pid=PID["Grovyle"])]
        wurmple = [battle_mon("Wurmple", 3, ["Tackle"], 16, 16, pid=PID["Wurmple"])]
        watch = bp.RaiseWatch(PID["Wurmple"], lambda line: None)
        watch(battle_look(grovyle, [foe("Taillow", 5)], ui=menu))
        self.assertEqual(watch.after(look(party=c1_party())), "the trainee is not leading")  # CONTROL
        watch(battle_look(grovyle, [foe("Taillow", 5)]))  # the stale first look: no menu yet
        watch(battle_look(wurmple, [foe("Taillow", 5)], ui=menu))
        self.assertIsNone(watch.after(look(party=c1_party(Wurmple=0))))
        self.assertEqual((watch.battles, watch.not_leading, watch.leaks), (2, 1, 1))
        stale = bp.RaiseWatch(PID["Wurmple"], lambda line: None)
        stale.first = battle_look(grovyle, [foe("Taillow", 5)]).battle.own[0].pid  # FAULT: the first look's battler
        self.assertEqual(stale.after(look(party=c1_party())), "the trainee is not leading")


# ------------------------------------------------------------------------------------------- T7 the budget
class BudgetTests(unittest.TestCase):
    """T7 (M5): ONE bounded budget per boss; its training is not run beside the raise."""

    def test_the_bounds(self):
        for key, bound in (("battles", 160), ("frames", 450_000), ("stalls", 12), ("reorder_fails", 3)):
            record = bp.new_record()
            record[key] = bound - 1
            self.assertIsNone(bp.spent_reason(record, "Story"), key)  # CONTROL: one short
            record[key] = bound
            self.assertTrue(bp.spent_reason(record, "Story").startswith(key), key)
        self.assertIsNone(bp.spent_reason({**bp.new_record(), "battles": 199}, "Catcher"))
        self.assertIsNone(bp.spent_reason({**bp.new_record(), "battles": 999}, "Trainer"))  # logs only

    def test_a_spent_budget_ends_the_raise(self):
        mgr = c1_manager()
        c1_decide(mgr)
        mgr.bp_record("ch7_brawly")["battles"] = 160
        goal, _ = c1_decide(mgr)
        self.assertNotEqual(goal.kind, "raise")
        self.assertEqual(mgr.bp_record("ch7_brawly")["status"], "spent")
        # (round 2, E1) spent through `spend`: its why kept and its lead SETTLED in the same decision (no raise session
        # ran, so no usual lead was recorded: nothing to restore, "done")
        self.assertEqual((mgr.bp_record("ch7_brawly")["spent_why"], mgr.bp_record("ch7_brawly")["settle"]),
                         ("battles 160 of at most 160", "done"))

    def brawly_goal(self, status: str):
        mgr = c1_manager()
        record = mgr.prep(at("ch7_brawly")[0]).setdefault("bp", bp.new_record())
        record.update(status=status, trainee=PID["Wurmple"], target=19, plan=f"raise:{PID['Wurmple']:08x}:19")
        # the raise put aside (round 2: every raise map's own key): what step 5 does then is the question
        for key in ("raise", "raise:ROUTE104"):
            mgr.memory.cooldown[key] = 10 ** 6
        goal, _ = c1_decide(mgr, milestone_id="ch7_brawly")
        return goal

    def test_no_training_beside_an_active_raise(self):
        """While the plan is ACTIVE, step 5's training for that fight is not chosen; CONTROL: spent, it trains as today."""
        self.assertNotEqual(self.brawly_goal("active").kind, "train")
        self.assertEqual(self.brawly_goal("spent").kind, "train")


# ------------------------------------------------------------------------------------------- T8 persistence, a loss
class PersistenceTests(unittest.TestCase):
    """T8 (m9): the record is game memory; a loss after a DONE plan chooses a different one."""

    def test_a_continue_keeps_the_record(self):
        mgr = c1_manager()
        c1_decide(mgr)
        part = json.loads(json.dumps(goals_part(mgr.memory)))
        fresh = c1_manager().memory
        restored = restore_goals(fresh, part)
        self.assertEqual(restored.fight_prep["ch7_brawly"]["bp"], mgr.bp_record("ch7_brawly"))
        self.assertEqual(restored.fight_prep["ch7_brawly"]["bp"]["status"], "active")

    def lost_after(self, status: str, party=None):
        mgr = c1_manager()
        record = mgr.prep(at("ch7_brawly")[0]).setdefault("bp", bp.new_record())
        record.update(status=status, trainee=PID["Wurmple"], target=19, plan=f"raise:{PID['Wurmple']:08x}:19")
        mgr.bp_boss = ("ch7_brawly", "BRAWLY", "DEWFORD_TOWN_GYM")
        mgr.boss_lost(look(party=party if party is not None else c1_party()))
        return mgr.bp_record("ch7_brawly")

    def test_a_loss_after_a_done_plan_chooses_another(self):
        """(the filter's unit check: the trainee is held at L3, so its own first READY level is the failed plan's again)"""
        record = self.lost_after("done")
        self.assertEqual(record["losses"], 1)
        self.assertEqual(record["failed"], [f"raise:{PID['Wurmple']:08x}:19"])
        self.assertEqual((record["status"], record["plan"]), ("active", f"raise:{PID['Grovyle']:08x}:30"))

    def test_control_a_spent_plan_is_not_replanned(self):
        record = self.lost_after("spent")
        self.assertEqual((record["losses"], record["status"], record["failed"]), (1, "spent", []))

    def test_a_loss_through_pursue(self):
        """The wiring: a goal begun on the leader's gym map that LOSES a battle reaches `boss_lost` (FAULT, a loss on
        another map: it does not)."""
        from ai_player.gates.test_goals import RestTests

        for const, losses in (("DEWFORD_TOWN_GYM", 1), ("DEWFORD_TOWN", 0)):
            nav = RestTests.navigator(RestTests(), [look(party=c1_party(), const=const)])
            nav.world = world_with(const, current=const)
            mgr = c1_manager()
            record = mgr.prep(at("ch7_brawly")[0]).setdefault("bp", bp.new_record())
            record.update(status="spent")
            mgr.bp_boss = ("ch7_brawly", "BRAWLY", "DEWFORD_TOWN_GYM")
            runner = GoalRunner(nav.hands, nav, mgr, types.SimpleNamespace(purpose="travel"), lambda line: None)

            def lose(goal, milestone, index, current):
                nav.battle_log.append((1, "trainer", "lost"))
                yield
                return False, "stuck: the battle was lost"

            runner._pursue = lose
            milestone, index = at("ch7_brawly")
            nav.hands.look()
            outcome = goals_module_drive(runner.pursue(Goal("talk", "BRAWLY", "ch7_brawly"), milestone, index, lambda s: index))
            self.assertEqual(outcome, (False, "stuck: the battle was lost"))
            self.assertEqual(record["losses"], losses, const)


def goals_module_drive(generator, budget: int = 1000):
    for _ in range(budget):
        try:
            next(generator)
        except StopIteration as done:
            return done.value
    raise AssertionError("the generator did not end within its budget")


# ------------------------------------------------------------------------------------------- T9 the next boss
class NextBossTests(unittest.TestCase):
    """T9: the next leader is the first NAMED fight ahead held in a gym; acted on only in ACT_ON."""

    def test_the_next_leader(self):
        story = load_story("BOY")
        for milestone_id, leader in (("ch6_briney_house", "BRAWLY"), ("ch7_brawly", "BRAWLY"), ("ch2_dad", "ROXANNE"),
                                     ("ch4_roxanne", "ROXANNE"), ("ch5_stolen_goods", "BRAWLY")):
            found = bp.next_boss(story.milestones, story.index(milestone_id))
            self.assertEqual(found[1], leader, milestone_id)
        self.assertIsNone(bp.next_boss(story.milestones, story.index("ch7_exp_share")))  # nothing past BRAWLY yet
        later = replace(story.milestones[story.index("ch7_brawly")], id="ch8_gym", maps=("MAUVILLE_CITY_GYM",))
        ahead = (*story.milestones, later)
        self.assertEqual(bp.next_boss(ahead, story.index("ch7_brawly") + 1)[1], "WATTSON")

    def test_fault_current_only(self):
        """FAULT (today's `fight_next`): only the current milestone: none at ch6_briney_house; CONTROL: BRAWLY at his own."""
        story = load_story("BOY")
        self.assertIsNone(bp.next_boss(story.milestones, story.index("ch6_briney_house"), F(current_only=True)))
        self.assertEqual(bp.next_boss(story.milestones, story.index("ch7_brawly"), F(current_only=True))[1], "BRAWLY")

    def test_chapter_5_plays_as_before(self):
        """In chapter 5 BRAWLY is the next LEADER but the rival's fight is the next NAMED fight: the verdict is logged and
        nothing is stored or done (chapters 1-5 unchanged by construction). FAULT (the rival's fight not named: BRAWLY's
        is the next named one) a raise goal in chapter 5."""
        mgr = c1_manager()
        goal, _ = c1_decide(mgr, milestone_id="ch5_stolen_goods")
        self.assertEqual(mgr.bp_boss[1], "BRAWLY")
        self.assertNotEqual(goal.kind, "raise")
        self.assertNotIn("ch7_brawly", mgr.memory.fight_prep)
        broken = c1_manager()
        milestones = list(broken.story.milestones)
        rival = broken.story.index("ch5_rival_meet")
        milestones[rival] = replace(milestones[rival], fight_named=False)
        broken.story.milestones = tuple(milestones)
        self.assertEqual(c1_decide(broken, milestone_id="ch5_stolen_goods")[0].kind, "raise")

    def roxanne(self, act_on):
        party = [summary(0, "Torchic", 10, ("Scratch", "Growl", "Focus Energy", "Ember"), 32, pid=0x2001)]
        mgr = c1_manager()
        with mock.patch.object(goals_module, "ACT_ON", act_on):
            goal, _ = c1_decide(mgr, party=party, milestone_id="ch2_dad", const="ROUTE102")
        return goal, mgr

    def test_act_on_all_would_raise_for_roxanne(self):
        """A NOT READY ROXANNE fixture (a lone Torchic L10): FAULT (ACT_ON every leader) a raise goal; CONTROL (as
        shipped) none: the verdict is only logged."""
        story = load_story("BOY")
        torchic = bp.Member(0x2001, "Torchic", 10, 32, 32, ("Scratch", "Growl", "Focus Energy", "Ember"))
        self.assertEqual(bp.verdict([torchic], 0x2001, boss_party("ROXANNE"), "Story").cls, bp.NOT_READY)
        self.assertEqual(self.roxanne(frozenset({"ROXANNE", "BRAWLY"}))[0].kind, "raise")
        goal, mgr = self.roxanne(bp.ACT_ON)
        self.assertNotEqual(goal.kind, "raise")
        self.assertNotIn("ch4_roxanne", mgr.memory.fight_prep)  # nothing stored for a leader not acted on
        self.assertEqual(story.milestones[story.index("ch4_roxanne")].maps, ("RUSTBORO_CITY_GYM",))


# ------------------------------------------------------------------------------------------- T11 loaders and fairness
class LoaderTests(unittest.TestCase):
    """T11: the loaders map every name, read nothing hidden, and the boss's team is the decomp's (RULING 44)."""

    def test_every_learnset_move_and_evolution_target_maps(self):
        unmapped = seasoned.unmapped()
        self.assertEqual((unmapped["moves"], unmapped["evolution_targets"]), ([], []))
        self.assertTrue(all(s.startswith("SPECIES_OLD_UNOWN") for s in unmapped["species"]), unmapped["species"])

    def test_fault_the_move_prefix_kept(self):
        """FAULT: a move symbol read with its MOVE_ prefix ("MOVE_TACKLE" is no move) leaves the moves unmapped. (The
        spec's `_`->space fault is no fault here: `move_named` folds every non-letter away; measured.)"""
        with mock.patch.object(seasoned, "_move", lambda symbol: move_named(str(symbol).replace("_", " "))):
            self.assertGreater(len(seasoned.unmapped()["moves"]), 300)
        self.assertEqual(move_named("KARATE_CHOP"), move_named("KARATE CHOP"))

    def test_brawlys_team(self):
        self.assertEqual(TEAM, (BossMon("Machop", 16, ("Karate Chop", "Low Kick", "Seismic Toss", "Bulk Up"), None),
                                BossMon("Meditite", 16, ("Focus Punch", "Light Screen", "Reflect", "Bulk Up"), None),
                                BossMon("Makuhita", 19, ("Arm Thrust", "Vital Throw", "Reversal", "Bulk Up"), "Sitrus Berry")))
        data = json.loads((REPO / "ai_player" / "knowledge" / "world" / "bosses.json").read_text(encoding="utf-8"))
        brawly = next(b for b in data["bosses"] if b["name"] == "BRAWLY")
        for mon_, entry in zip(TEAM, brawly["party"]):  # cross-check: the species' types are the file's
            self.assertEqual(tuple(t.capitalize() for t in dict.fromkeys(entry["types"])), bp.types_of(mon_.species))
        self.assertEqual(boss_party("NOBODY"), ())

    def test_the_berries(self):
        """`src/data/items.h` holdEffectParam: Sitrus 30, Oran 10 (read from the pinned decomp when it is present)."""
        self.assertEqual(bp.BERRY_HP, {"Sitrus Berry": 30, "Oran Berry": 10})
        decomp = os.environ.get("POKEBOT_DECOMP")
        if decomp and (Path(decomp) / "src" / "data" / "items.h").is_file():
            text = (Path(decomp) / "src" / "data" / "items.h").read_text(encoding="utf-8")
            for item, value in (("ITEM_ORAN_BERRY", 10), ("ITEM_SITRUS_BERRY", 30)):
                block = text.split(f"[{item}] =", 1)[1].split("},", 1)[0]
                self.assertIn(f".holdEffectParam = {value},", block)

    def test_the_land_levels(self):
        self.assertEqual([seasoned.land_levels(c) for c in ("ROUTE104", "PETALBURG_WOODS", "ROUTE116", "MAP_ROUTE116",
                                                           "RUSTBORO_CITY")], [(3, 5), (5, 6), (6, 8), (6, 8), None])

    def test_the_raise_map_rule(self):
        """(round 2) `raise_maps` by a CAP (the knock-out Pokemon's level less the margin; `RaiseMapTests` for the cap):
        the highest top under the cap first, then the rest by the lowest top; only maps a known way leads to."""
        mgr = manager()
        world = world_with("ROUTE104", "PETALBURG_WOODS", "ROUTE116", current="ROUTE104", grass=True)
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
            self.assertEqual([mgr.raise_maps(world, cap)[0] for cap in (5, 6, 7, 16, 1)],
                             ["ROUTE104", "PETALBURG_WOODS", "PETALBURG_WOODS", "ROUTE116", "ROUTE104"])
            self.assertEqual(mgr.raise_maps(world, 6), ["PETALBURG_WOODS", "ROUTE104", "ROUTE116"])
        self.assertEqual(mgr.raise_maps(world, 16), ["ROUTE104"])  # the others: no known way there
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: goals_module.UNREACHABLE):
            self.assertEqual(mgr.raise_maps(world, 3), [])

    def test_fairness_passes_and_a_hidden_read_fails(self):
        from ai_player.gates import check_fairness as cf

        ok, problems, _ = cf.check(REPO / "ai_player")
        self.assertTrue(ok, problems)

        def plant(text: str) -> list[str]:
            with tempfile.TemporaryDirectory() as tmp:
                pkg = Path(tmp) / "ai_player"
                shutil.copytree(REPO / "ai_player", pkg, ignore=shutil.ignore_patterns(
                    "__pycache__", "evidence", "gates", "*.ss1", "eyes", "host"))
                path = pkg / "knowledge" / "seasoned.py"
                path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
                return cf.check(pkg)[1]

        for key in ("catch_rate", "base_stats"):
            found = plant(f'\n\ndef leak(entry):\n    return entry["{key}"]\n')
            self.assertTrue(any(f.startswith("B2") and repr(key) in f for f in found), (key, found))
        self.assertEqual(plant('\n\ndef told():\n    """never entry["catch_rate"]"""\n    return 1\n'), [])  # CONTROL

    def test_no_box_and_no_hidden_name_in_bossprep(self):
        """(m5) The verdict never reads the PC boxes (`look.storage`) nor a hidden fact; FAULT: a planted read is seen."""
        def reads(source: str) -> set[str]:
            return {node.attr for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Attribute)}

        source = (REPO / "ai_player" / "brain" / "bossprep.py").read_text(encoding="utf-8")
        forbidden = {"storage", "catch_rate", "exp_yield", "growth", "attack", "defense", "sp_attack", "sp_defense", "speed"}
        self.assertEqual(reads(source) & forbidden, set())
        planted = source.replace("    for mon in look.party or ():\n", "    for mon in (look.party or ()) + look.storage:\n", 1)
        self.assertNotEqual(planted, source)
        self.assertIn("storage", reads(planted))


# =========================================================================================== ROUND 2 (USER RULING 59)
# The raise as a mix: switch-training, the trainee's own winnable fights, healing at a centre or with a Potion
# (`ai-research-notes/2026-11-09-BOSS-PREP-BP1-RAISE-SPEC.md` section 5.1: R1-R9). Each rule: a FAULT arm (a
# `BossprepFaults` / `BattleFaults` switch, or BP-1's rule) beside a CONTROL; `gates/revert_bossprep.py` breaks each in a copy.
W, G, P = PID["Wurmple"], PID["Grovyle"], PID["Poochyena"]
GROVYLE_MOVES = ["Pound", "Pursuit", "Absorb", "Quick Attack"]
DUSTOX_MOVES = ["Tackle", "Confusion", "Poison Sting", "Harden"]
SEVEN = ("ROUTE101", "ROUTE102", "ROUTE103", "ROUTE104", "PETALBURG_WOODS", "ROUTE116", "ROUTE115")


def party18(**hp: int) -> list[MonSummary]:
    """C1's party with the trainee as it was live at the stalls: Wurmple L4, max HP 18 (the rest full unless named)."""
    out = c1_party()
    out[2] = replace(out[2], level=4, max_hp=18, hp=18)
    return [replace(m, hp=hp[m.species]) if m.species in hp else m for m in out]


def decide2(mgr, party, world, milestone_id="ch6_briney_house", const="ROUTE104", healing=()):
    """A decision on C1's fixture with the bag's healing items pinned (`healing`: () is an EMPTY bag, the verifier's)."""
    from ai_player.eyes.observation import BagSummary

    milestone, index = at(milestone_id)
    seen = look(ch_proofs(milestone_id), party=party, const=const)
    seen = replace(seen, bag=BagSummary(seen.bag.balls, tuple(healing), seen.bag.ball_total))
    return mgr.next_goal(seen, world, milestone, index)


def planned(personality: str = "Story", faults=bp.NO_FAULTS):
    """A manager whose plan is made (active, Wurmple), and the world it was made on (ROUTE104 with grass)."""
    mgr = c1_manager(personality)
    mgr.bp_faults = faults
    world = world_with("ROUTE104", current="ROUTE104", grass=True)
    first = decide2(mgr, party18(), world)
    return mgr, world, first


def with_centre() -> object:
    return world_with("ROUTE104", "RUSTBORO_CITY", current="ROUTE104", grass=True, center_from="RUSTBORO_CITY")


def raise_mind(faults=None, bp_faults=None, personality="Story") -> BattleMind:
    from ai_player.brain.battle import BattleFaults

    mind = BattleMind(personality, random.Random("1:battle"), "raise", faults or BattleFaults())
    mind.trainee = W
    mind.bp_faults = bp_faults
    return mind


def battle_turn(mind, own, foe_, party, kind="wild", begin=True):
    seen = battle_look([own], [foe_], party=party, kind=kind)
    if begin:
        mind.begin(seen)
    return mind.decide(seen)


def grovyle_member(hp: int = 57):
    return member("Grovyle", 21, GROVYLE_MOVES, hp, 57, G, 1)


def poochyena_member(hp: int = 21, level: int = 6):
    return member("Poochyena", level, ["Tackle", "Howl"], hp, 21, P, 2)


class TraineeFloorTests(unittest.TestCase):
    """R1 (V-M1 reproduced, then fixed): the verifier's fixture, C1's plan active, the rest full, an EMPTY bag."""

    def test_r1a_r1b_under_the_floor_heals(self):
        for hp in (1, 5):
            for world, kind in ((None, "find_center"), (with_centre(), "heal")):
                mgr, made, first = planned()
                self.assertEqual(first.kind, "raise")
                goal = decide2(mgr, party18(Wurmple=hp), world or made)
                self.assertEqual(goal.kind, kind, (hp, goal.reason))
                self.assertIn(f"is low ({hp}/18)", goal.reason)

    def test_r1a_fault_trainee_floor_off(self):
        """FAULT (BP-1's `hurt`, and the raise's own guard off): R1a and R1b give `raise`: the loop reproduced. With the
        floor off alone the raise's guard still holds (no raise), but no heal either."""
        for hp in (1, 5):
            mgr, made, _ = planned(faults=F(trainee_floor_off=True, raise_guard_off=True))
            self.assertEqual(decide2(mgr, party18(Wurmple=hp), made).kind, "raise", hp)
            mgr, made, _ = planned(faults=F(trainee_floor_off=True))
            self.assertNotIn(decide2(mgr, party18(Wurmple=hp), made).kind, ("raise", "heal", "find_center"), hp)

    def test_r1c_control_fainted_heals_as_before(self):
        mgr, made, _ = planned()
        self.assertEqual(decide2(mgr, party18(Wurmple=0), made).kind, "find_center")
        mgr, made, _ = planned(faults=F(trainee_floor_off=True, raise_guard_off=True))
        self.assertEqual(decide2(mgr, party18(Wurmple=0), made).kind, "find_center")  # a faint was always danger

    def test_r1d_r1e_control_a_third_and_full_raise(self):
        for hp in (6, 18):  # 6/18 is exactly a third: not under it
            mgr, made, _ = planned()
            goal = decide2(mgr, party18(Wurmple=hp), made)
            self.assertEqual((goal.kind, goal.key), ("raise", "raise:ROUTE104"), hp)

    def test_r1f_the_raise_goal_waits_under_the_floor(self):
        mgr, made, _ = planned()
        plan = mgr.boss_prep(look(party=party18(Wurmple=5)), at("ch6_briney_house")[1])
        self.assertIsNone(mgr._raise_goal(look(party=party18(Wurmple=5)), made, plan))
        self.assertEqual(mgr._raise_goal(look(party=party18()), made, plan).kind, "raise")  # CONTROL
        mgr.bp_faults = F(raise_guard_off=True)
        self.assertEqual(mgr._raise_goal(look(party=party18(Wurmple=5)), made, plan).kind, "raise")  # FAULT

    def session(self, mgr, after_hp: int = 5, roam_line: str = "rest: the trainee Wurmple L4 is low (5/18)"):
        from ai_player.gates.test_goals import RestTests

        nav = RestTests.navigator(RestTests(), [look(party=party18()), look(party=party18(Wurmple=after_hp))])
        runner = GoalRunner(nav.hands, nav, mgr, types.SimpleNamespace(purpose="travel", trainee=None), lambda line: None)

        def fake_lead(hands, pid, why):
            yield
            return True

        def fake_roam(hands, nav_, steps, why):
            hands.look()
            yield
            return f"{roam_line}; roam: 3 training steps (3 pressed, 1 ran into a battle or a scene)"

        goal = Goal("raise", "r", "ch7_brawly", map=None, steps=10, key="raise:ROUTE104")
        with mock.patch.object(goals_module, "lead_with", fake_lead), mock.patch.object(goals_module, "roam_train", fake_roam):
            return goals_module_drive(runner._raise(goal, lambda s: False))

    def test_r1g_the_sequence(self):
        """Decision 1 is a raise; its session ends "the trainee ... is low (5/18)"; decision 2 must be a heal goal. FAULT
        (floor and guard off: BP-1): decision 2 is `raise` (the verifier's 3, 10 and 11 such sequences)."""
        for faults, expected in ((bp.NO_FAULTS, ("heal", "find_center")),
                                 (F(trainee_floor_off=True, raise_guard_off=True), ("raise",))):
            mgr, made, first = planned(faults=faults)
            self.assertEqual(first.kind, "raise")
            ended = self.session(mgr)
            self.assertTrue(ended[1].startswith("rest: the trainee"), ended)
            second = decide2(mgr, party18(Wurmple=5), made)
            self.assertIn(second.kind, expected, (faults, second.reason))


class ExpModelTests(unittest.TestCase):
    """R2 (the gate-side model, `gates/exp_rule.py`, never imported by the AI): `Cmd_getexp`'s split, by hand (spec 1.4)."""

    def test_the_hand_values(self):
        from ai_player.gates import exp_rule

        self.assertEqual(exp_rule.expected_gain(55, 6, (True, True)), [23, 23])  # Poochyena L6, 2 sent
        self.assertEqual(exp_rule.expected_gain(59, 8, (True, True)), [33, 33])  # Taillow L8
        self.assertEqual(exp_rule.expected_gain(55, 6, (True,)), [47])  # 1 sent: the full E
        self.assertEqual(exp_rule.expected_gain(55, 6, (False, True)), [0, 47])  # a fainted participant
        self.assertEqual(exp_rule.switch_share(73, 7), 36)  # Abra L7 (in practice 0: it teleports)

    def test_fault_count_fainted(self):
        """FAULT: the fainted participant counted: the survivor's share halves (P1's expectation guards it)."""
        from ai_player.gates import exp_rule

        self.assertEqual(exp_rule.expected_gain(55, 6, (False, True), count_fainted=True), [0, 23])

    def test_the_yields_are_the_decomps(self):
        """Read from the pinned decomp when present (`POKEBOT_DECOMP`): the spec's section 1.4 yields."""
        from ai_player.gates import exp_rule

        if exp_rule.decomp_yield("Poochyena") is None:
            self.skipTest("the pinned decomp is not here")
        self.assertEqual({s: exp_rule.decomp_yield(s) for s in ("Poochyena", "Whismur", "Nincada", "Abra", "Taillow",
                                                                  "Skitty")},
                         {"Poochyena": 55, "Whismur": 68, "Nincada": 65, "Abra": 73, "Taillow": 59, "Skitty": 65})


class RaiseTurnTests(unittest.TestCase):
    """R3: a raise battle's first decision and later turns (`BattleMind._raise_turn`), with test_battle's fixtures. The
    party in the game's order: the trainee first (the raise puts it first), Grovyle L21, Poochyena L6."""

    def party(self, trainee, grovyle_hp=57, **more):
        return [trainee, grovyle_member(grovyle_hp), poochyena_member(**more)]

    def wurmple(self, hp=18, level=4):
        return member("Wurmple", level, ["Tackle", "String Shot"], hp, 18 if level == 4 else 16, W, 0)

    def dustox(self, hp=38, max_hp=38):
        return member("Dustox", 12, DUSTOX_MOVES, hp, max_hp, W, 0)

    def own_wurmple(self, hp=18, level=4):
        return battle_mon("Wurmple", level, ["Tackle", "String Shot"], hp, 18 if level == 4 else 16, pid=W)

    def own_dustox(self, hp=38, max_hp=38):
        return battle_mon("Dustox", 12, DUSTOX_MOVES, hp, max_hp, pid=W)

    def test_r3a_switch_training(self):
        from ai_player.brain.battle import BattleFaults

        mind = raise_mind()
        decision = battle_turn(mind, self.own_wurmple(), foe("Poochyena", 6), self.party(self.wurmple()))
        self.assertEqual((decision.action, decision.switch_pid, mind.memory.raise_mode), ("switch", G, "switch"))
        self.assertIn("keeps its share", decision.reason)
        broken = raise_mind(BattleFaults(raise_never_switch=True))
        decision = battle_turn(broken, self.own_wurmple(), foe("Poochyena", 6), self.party(self.wurmple()))
        self.assertIn(decision.action, ("fight", "run"))  # FAULT: BP-1 neither switched nor had a partner

    def test_r3b_control_an_own_fight(self):
        """CONTROL: Dustox L12 full against a foe it beats safely fights (own). (The spec's fixture was Poochyena L7:
        built, Confusion does nothing to a Dark type and Tackle needs 5 hits, so that one is switch-trained; Whismur L6
        and Nincada L7 are the own fights.) FAULT `raise_always_switch`: switched."""
        from ai_player.brain.battle import BattleFaults

        for species, level in (("Whismur", 6), ("Nincada", 7)):
            mind = raise_mind()
            decision = battle_turn(mind, self.own_dustox(), foe(species, level), self.party(self.dustox()))
            self.assertEqual((decision.action, mind.memory.raise_mode), ("fight", "own"), species)
            broken = raise_mind(BattleFaults(raise_always_switch=True))
            decision = battle_turn(broken, self.own_dustox(), foe(species, level), self.party(self.dustox()))
            self.assertEqual(decision.action, "switch", species)

    def test_r3c_dustox_against_taillow_and_poochyena_l7(self):
        for species, level in (("Taillow", 8), ("Poochyena", 7)):
            mind = raise_mind()
            decision = battle_turn(mind, self.own_dustox(), foe(species, level), self.party(self.dustox()))
            self.assertEqual((decision.action, decision.switch_pid), ("switch", G), species)

    def test_r3d_the_rescue_once(self):
        mind = raise_mind()
        party = self.party(self.dustox())
        self.assertEqual(battle_turn(mind, self.own_dustox(), foe("Whismur", 6), party).action, "fight")
        low = self.party(self.dustox(hp=10))  # under a third of 38
        decision = battle_turn(mind, self.own_dustox(hp=10), foe("Whismur", 6, bar=30), low, begin=False)
        self.assertEqual((decision.action, decision.switch_pid, mind.memory.raise_mode, mind.raise_modes),
                         ("switch", G, "rescue", ["rescue"]))
        again = battle_turn(mind, self.own_dustox(hp=8), foe("Whismur", 6, bar=30), self.party(self.dustox(hp=8)),
                            begin=False)
        self.assertNotEqual(again.action, "switch")  # the one switch is made: never again
        mind = raise_mind()  # CONTROL: at a third, no rescue
        battle_turn(mind, self.own_dustox(), foe("Whismur", 6), party)
        self.assertNotEqual(battle_turn(mind, self.own_dustox(hp=13), foe("Whismur", 6, bar=30),
                                        self.party(self.dustox(hp=13)), begin=False).action, "switch")

    def test_r3e_no_partner_runs(self):
        """Grovyle at 20/57 and Poochyena at 10/21: nobody at half HP or more: run. CONTROL: Grovyle at 29/57 is one."""
        mind = raise_mind()
        decision = battle_turn(mind, self.own_wurmple(), foe("Poochyena", 6), self.party(self.wurmple(), grovyle_hp=20,
                                                                                          hp=10))
        self.assertEqual((decision.action, mind.memory.raise_mode, mind.raise_modes), ("run", "run", ["run"]))
        mind = raise_mind()
        decision = battle_turn(mind, self.own_wurmple(), foe("Poochyena", 6), self.party(self.wurmple(), grovyle_hp=29,
                                                                                          hp=10))
        self.assertEqual((decision.action, decision.switch_pid), ("switch", G))
        # a healthy member that would NOT win safely is no partner: Poochyena L6 full against a Taillow L8 (Grovyle worn)
        poochyena = poochyena_member()
        self.assertFalse(bp.fight_safe(bp.member_now(battle_look([self.own_wurmple()], [foe("Taillow", 8)],
                                                                 party=[poochyena]), P), "Taillow", 8, 1.0, 21)[0])
        mind = raise_mind()
        decision = battle_turn(mind, self.own_wurmple(), foe("Taillow", 8), self.party(self.wurmple(), grovyle_hp=20))
        self.assertEqual(decision.action, "run")

    def test_r3f_not_the_trainee(self):
        mind = raise_mind()
        own = battle_mon("Grovyle", 21, GROVYLE_MOVES, 57, 57, pid=G)
        decision = battle_turn(mind, own, foe("Poochyena", 6), [grovyle_member(), self.wurmple(), poochyena_member()])
        self.assertEqual((mind.memory.raise_mode, mind.raise_modes), ("not the trainee", ["not the trainee"]))
        self.assertEqual(decision.action, "fight")

    def test_r3g_a_trainer_battle(self):
        mind = raise_mind()
        battle_turn(mind, self.own_wurmple(), foe("Poochyena", 6), self.party(self.wurmple()), kind="trainer")
        self.assertIsNone(mind.memory.raise_mode)
        self.assertEqual(mind.raise_modes, [])

    def test_r3h_judged_at_its_hp_now(self):
        """Dustox L12 at 14/40 against Nincada L7 (safe at full HP): switch. FAULT `safe_full_hp`: fight."""
        mind = raise_mind()
        decision = battle_turn(mind, self.own_dustox(14, 40), foe("Nincada", 7), self.party(self.dustox(14, 40)))
        self.assertEqual(decision.action, "switch")
        mind = raise_mind(bp_faults=F(safe_full_hp=True))
        decision = battle_turn(mind, self.own_dustox(14, 40), foe("Nincada", 7), self.party(self.dustox(14, 40)))
        self.assertEqual(decision.action, "fight")

    def test_r3i_a_five_hit_fight_is_not_safe(self):
        dustox = next(d for d in bp.project(bp.Member(W, "Wurmple", 4, 18, 18, ("Tackle", "String Shot")), 12)
                      if d.species == "Dustox")
        safe, why = bp.fight_safe(dustox, "Abra", 7, 1.0, dustox.max_hp)
        self.assertFalse(safe)
        self.assertTrue(why.startswith("5 of its hits"), why)
        self.assertTrue(bp.fight_safe(dustox, "Abra", 7, 1.0, dustox.max_hp, faults=F(hits_unbounded=True))[0])
        mind = raise_mind(bp_faults=F(hits_unbounded=True))
        self.assertEqual(battle_turn(mind, self.own_dustox(), foe("Abra", 7), self.party(self.dustox())).action, "fight")

    def test_r3j_the_replacement_is_never_the_trainee_while_another_can_fight(self):
        from ai_player.brain.battle import BattleFaults

        fainted = battle_mon("Grovyle", 21, GROVYLE_MOVES, 0, 57, pid=G)
        party = [self.dustox(), grovyle_member(0), poochyena_member()]
        seen = battle_look([fainted], [foe("Whismur", 6)], party=party)
        self.assertEqual(raise_mind().replacement(seen)[0], P)
        # FAULT: the trainee, the better matched (its Confusion against a Normal type, five levels up)
        self.assertEqual(raise_mind(BattleFaults(replacement_trainee_ok=True)).replacement(seen)[0], W)
        only = battle_look([fainted], [foe("Whismur", 6)], party=[self.dustox(), grovyle_member(0), poochyena_member(0)])
        self.assertEqual(raise_mind().replacement(only)[0], W)  # CONTROL: the trainee when it is the only one left

    def test_r3k_the_raise_turn_before_the_run_rule(self):
        from ai_player.brain.battle import BattleFaults

        party = self.party(self.wurmple(16, 3))
        mind = raise_mind()
        self.assertEqual(battle_turn(mind, self.own_wurmple(16, 3), foe("Taillow", 9), party).action, "switch")
        broken = raise_mind(BattleFaults(run_first=True))
        self.assertEqual(battle_turn(broken, self.own_wurmple(16, 3), foe("Taillow", 9), party).action, "run")

    def test_r3l_use_next_with_only_the_trainee(self):
        from ai_player.brain.battle import BattleFaults

        fainted = battle_mon("Grovyle", 21, GROVYLE_MOVES, 0, 57, pid=G)
        alone = battle_look([fainted], [foe("Poochyena", 6)], party=[self.wurmple(), grovyle_member(0), poochyena_member(0)])
        self.assertFalse(raise_mind().answer("Use next POKéMON?", alone)[0])
        self.assertTrue(raise_mind(BattleFaults(trainee_sent_last=True)).answer("Use next POKéMON?", alone)[0])
        other = battle_look([fainted], [foe("Poochyena", 6)], party=[self.wurmple(), grovyle_member(0), poochyena_member()])
        self.assertTrue(raise_mind().answer("Use next POKéMON?", other)[0])  # CONTROL

    def test_r3m_no_second_switch(self):
        from ai_player.brain.battle import BattleFaults

        party = [self.wurmple(), grovyle_member(), member("Poochyena", 14, ["Tackle", "Howl", "Bite"], 40, 40, P, 2)]
        for faults, second in ((BattleFaults(), False), (BattleFaults(second_switch=True), True)):
            mind = raise_mind(faults)
            first = battle_turn(mind, self.own_wurmple(), foe("Taillow", 8), party)
            self.assertEqual(first.action, "switch")
            sent = next(m for m in party if m.pid == first.switch_pid)
            out = battle_mon(sent.species, sent.level, [s.name for s in sent.moves], sent.hp, sent.max_hp, pid=sent.pid)
            decision = battle_turn(mind, out, foe("Taillow", 8), party, begin=False)
            self.assertEqual(decision.action == "switch", second, (faults, decision.reason))

    def test_no_raise_turn_outside_a_raise(self):
        """CONTROL: purpose train (or no trainee) with the same battle: the ordinary rules (no switch-training)."""
        for purpose, trainee in (("train", W), ("raise", None)):
            mind = BattleMind("Story", random.Random("1:battle"), purpose)
            mind.trainee = trainee
            battle_turn(mind, self.own_wurmple(), foe("Poochyena", 6), self.party(self.wurmple()))
            self.assertIsNone(mind.memory.raise_mode, purpose)


class FightSafeTests(unittest.TestCase):
    """R4: `fight_safe`'s classes (spec section 2.2) on every ROUTE116 land slot, and the Pursuit check."""

    @staticmethod
    def route_slots(*maps: str) -> list[tuple[str, int, str]]:
        data = json.loads((REPO / "ai_player" / "knowledge" / "seasoned" / "encounters.json").read_text(encoding="utf-8"))
        out = set()
        for entry in data["maps"]:
            if str(entry.get("map") or "").removeprefix("MAP_") in maps and entry["availability"] == "normal":
                for slot_ in ((entry.get("methods") or {}).get("land") or {}).get("slots") or ():
                    for level in range(slot_["min_level"], slot_["max_level"] + 1):
                        out.add((species_named(slot_["species"].removeprefix("SPECIES_").replace("_", " ")), level,
                                 entry["map"]))
        return sorted(out)

    def trainee_at(self, level: int, species: str) -> bp.Member:
        return next(d for d in bp.project(bp.Member(W, "Wurmple", 4, 18, 18, ("Tackle", "String Shot")), level)
                    if d.species == species) if level > 4 else bp.Member(W, "Wurmple", 4, 18, 18, ("Tackle", "String Shot"))

    def test_r4a_r4b_wurmple_and_cascoon_never_safe(self):
        for who in (self.trainee_at(4, "Wurmple"), self.trainee_at(8, "Cascoon")):
            for species, level, _ in self.route_slots("ROUTE116"):
                self.assertFalse(bp.fight_safe(who, species, level, 1.0, who.max_hp)[0], (who.species, species, level))

    def test_r4c_r4d_dustox_l12(self):
        dustox = self.trainee_at(12, "Dustox")
        self.assertEqual(dustox.moves, tuple(DUSTOX_MOVES))
        verdicts = {(s, lv): bp.fight_safe(dustox, s, lv, 1.0, dustox.max_hp)[0] for s, lv, _ in self.route_slots("ROUTE116")}
        for key in (("Whismur", 6), ("Nincada", 6), ("Nincada", 7), ("Poochyena", 6)):
            self.assertTrue(verdicts[key], key)
        for key in (("Taillow", 7), ("Taillow", 8), ("Poochyena", 7), ("Poochyena", 8), ("Abra", 7)):
            self.assertFalse(verdicts[key], key)  # Taillow's Peck x2 on Bug; Poochyena (Dark) immune to Confusion

    def test_r4e_no_pursuit_near_rustboro(self):
        maps = ("ROUTE101", "ROUTE102", "ROUTE103", "ROUTE104", "PETALBURG_WOODS", "ROUTE115", "ROUTE116")
        found = [(s, lv, m) for s, lv, m in self.route_slots(*maps) if "Pursuit" in seasoned.wild_moves(s, lv)]
        self.assertEqual(found, [])
        self.assertGreater(len(self.route_slots(*maps)), 20)  # the scan reads the slots (an empty read passes nothing)
        self.assertEqual(seasoned.wild_moves("Poochyena", 5), ["Tackle", "Howl"])  # CONTROL
        self.assertIn("Pursuit", seasoned.wild_moves("Grovyle", 21))  # the scan can find it (C1's own Grovyle knows it)

    def test_the_initial_moveset_rule(self):
        """The last FOUR, the first forgotten (`GiveBoxMonInitialMoveset`); a move known already skipped."""
        self.assertEqual(seasoned.wild_moves("Taillow", 8), ["Peck", "Growl", "Focus Energy", "Quick Attack"])
        self.assertEqual(seasoned.wild_moves("Nobody", 8), [])


class HealChoiceTests(unittest.TestCase):
    """R5: the trainee at 5/18 and the plan active, unless said: a CENTRE when one is near, a POTION when it is far."""

    def choose(self, links=2, healing=(("Potion", 3),), faults=bp.NO_FAULTS, trainee_hp=5, grovyle_hp=57, cooldown=False):
        mgr, _, _ = planned(faults=faults)
        if cooldown:
            mgr.memory.cooldown["potion"] = 10 ** 6
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: links):
            return decide2(mgr, party18(Wurmple=trainee_hp, Grovyle=grovyle_hp), with_centre(), healing=healing)

    def test_r5a_a_centre_near(self):
        self.assertEqual(self.choose(2).kind, "heal")
        self.assertEqual(self.choose(2, faults=F(potion_always=True)).kind, "potion")  # FAULT

    def test_r5b_a_centre_far(self):
        goal = self.choose(3)
        self.assertEqual((goal.kind, goal.pid, goal.key, goal.milestone), ("potion", W, "potion", "ch7_brawly"))
        self.assertEqual(self.choose(3, faults=F(centre_always=True)).kind, "heal")  # FAULT

    def test_r5c_no_field_item(self):
        self.assertEqual(self.choose(3, healing=()).kind, "heal")
        self.assertEqual(self.choose(3, healing=(("Hyper Potion", 1), ("Potion", 0))).kind, "heal")

    def test_r5d_fainted(self):
        self.assertEqual(self.choose(3, trainee_hp=0).kind, "heal")
        self.assertEqual(self.choose(3, trainee_hp=0, faults=F(potion_revives=True)).kind, "potion")  # FAULT

    def test_r5e_another_needs_the_heal(self):
        self.assertEqual(self.choose(3, grovyle_hp=15).kind, "heal")

    def test_r5f_the_potion_put_aside(self):
        self.assertEqual(self.choose(3, cooldown=True).kind, "heal")

    def test_r5g_control_at_a_third(self):
        self.assertEqual(self.choose(3, trainee_hp=6).kind, "raise")

    def test_r5h_control_no_plan_in_chapter_5(self):
        """No plan (chapter 5: the rival's fight is the next named one), a member at 5/18: exactly the goal the parent's
        rules give (ACT_ON empty)."""
        party = party18(Wurmple=5)
        for healing in ((), (("Potion", 3),)):
            mgr = c1_manager()
            goal = decide2(mgr, party, with_centre(), milestone_id="ch5_stolen_goods", healing=healing)
            with mock.patch.object(goals_module, "ACT_ON", frozenset()):
                parent = decide2(c1_manager(), party, with_centre(), milestone_id="ch5_stolen_goods", healing=healing)
            self.assertEqual((goal.kind, goal.reason, goal.map, goal.key), (parent.kind, parent.reason, parent.map, parent.key))
            self.assertNotEqual(goal.kind, "potion")

    def test_the_potion_runner_calls_the_hand(self):
        """The runner plays a potion goal through `hands/field_item.py` use_on, for the goal's PID, and counts it."""
        from ai_player.gates.test_goals import RestTests

        mgr, _, _ = planned()
        nav = RestTests.navigator(RestTests(), [look(party=party18(Wurmple=5))])
        runner = GoalRunner(nav.hands, nav, mgr, types.SimpleNamespace(purpose="travel", trainee=None), lambda line: None)
        asked = []

        def fake_use(hands, pid, items, up_to, most, why):
            asked.append((pid, tuple(items), round(up_to, 3), most))
            yield
            return True, 2, "2 used"

        milestone, index = at("ch6_briney_house")
        with mock.patch.object(goals_module, "use_on", fake_use):
            result = goals_module_drive(runner._pursue(Goal("potion", "p", "ch7_brawly", key="potion", pid=W), milestone,
                                                       index, lambda s: index))
        self.assertEqual(result, (True, "2 used"))
        self.assertEqual(asked, [(W, ("Potion", "Super Potion"), 0.667, 2)])
        self.assertEqual(mgr.bp_record("ch7_brawly")["potions"], 2)


class PartnerWornTests(unittest.TestCase):
    """(the builder's addition to the spec) The raise's KNOCK-OUT partner under half its HP makes the raise rest: no member
    could take the trainee's place, so every battle would be run from (the partner's own V-M1)."""

    def test_a_worn_partner_heals(self):
        """(round 3) The fixture's raise map is ROUTE104 (the world holds only it): under half its HP Grovyle is no partner
        against its wild Pokemon (`bossprep.partner_fit`), so the party rests; the reason names the line."""
        mgr, made, _ = planned()
        goal = decide2(mgr, party18(Grovyle=27), made)
        self.assertEqual(goal.kind, "find_center")
        self.assertIn("(27/57) is not a safe partner against", goal.reason)
        self.assertIn("under half its HP", goal.reason)
        mgr, made, _ = planned(faults=F(partner_worn_off=True))
        self.assertEqual(decide2(mgr, party18(Grovyle=27), made).kind, "raise")  # FAULT

    def test_control_at_half_it_raises(self):
        mgr, made, _ = planned()
        self.assertEqual(decide2(mgr, party18(Grovyle=29), made).kind, "raise")

    def test_the_raise_roam_rests(self):
        from ai_player.gates.test_goals import RestTests

        nav = RestTests.navigator(RestTests(), [look(party=party18())])
        runner = GoalRunner(nav.hands, nav, c1_manager(), None, lambda line: None)
        runner.roam_hooks(trainee=W, after_battle=lambda observation: None)
        self.assertIn("is worn", nav.battle_rest(look(party=party18(Grovyle=27))))
        self.assertIsNone(nav.battle_rest(look(party=party18(Grovyle=40))))  # CONTROL

    def test_a_strong_trainee_has_no_partner_to_wear(self):
        strong = c1_party()
        self.assertIsNone(bp.raise_partner_of(strong, G))  # Grovyle L21 raised: the others are weaker
        self.assertEqual(bp.raise_partner_of(strong, W).pid, G)


class RaiseMapTests(unittest.TestCase):
    """R6 (BP1-L1, BP1-L2): the seven maps, all visited and reachable."""

    def goal(self, party, faults=bp.NO_FAULTS, mgr=None):
        mgr = mgr or c1_manager()
        mgr.bp_faults = faults
        world = world_with(*SEVEN, current="ROUTE104", grass=True)
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
            return decide2(mgr, party, world), mgr, world

    def test_r6a_the_partners_cap(self):
        from ai_player.brain.battle import OUTLEVELS

        self.assertEqual(bp.PARTNER_MARGIN, OUTLEVELS)  # the battle brain's own margin (spec section 2.1)
        self.assertEqual(self.goal(party18())[0].map, "ROUTE116")
        self.assertEqual(self.goal(party18(), F(map_by_trainee=True))[0].map, "PETALBURG_WOODS")  # FAULT: BP1-L1

    def test_r6b_r6c_r6d_the_caps(self):
        mgr = manager()
        world = world_with(*SEVEN, current="ROUTE104", grass=True)
        cases = (((4, 12), "PETALBURG_WOODS"), ((21, 5), "ROUTE116"), ((3, 5), "ROUTE101"))
        for (trainee_level, partner_level), expected in cases:
            party = [summary(0, "Wurmple", trainee_level, ("Tackle",), 18, pid=W),
                     summary(1, "Poochyena", partner_level, ("Tackle",), 30, pid=P)]
            cap, _ = mgr.raise_cap(look(party=party), party[0])
            with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
                self.assertEqual(mgr.raise_maps(world, cap)[0], expected, (trainee_level, partner_level, cap))

    def test_r6e_a_map_that_fails_twice_is_put_aside(self):
        for faults, then in ((bp.NO_FAULTS, "PETALBURG_WOODS"), (F(one_raise_key=True), None)):
            first, mgr, world = self.goal(party18(), faults)
            self.assertEqual(first.map, "ROUTE116")
            mgr.outcome(first, False)
            mgr.outcome(first, False)
            with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
                plan = mgr.boss_prep(look(party=party18()), at("ch6_briney_house")[1])
                after = mgr._raise_goal(look(party=party18()), world, plan)
            self.assertEqual(after.map if after is not None else None, then, faults)
            self.assertEqual(mgr.bp_record("ch7_brawly")["status"], "active")  # put aside is not spent


class BudgetCountingTests(unittest.TestCase):
    """R7 (V-m3): the raise runner's counting, on a fake session (lead and roam faked; the looks carry the EXP)."""

    def session(self, faults=bp.NO_FAULTS, exp=(100, 100), levels=(4, 4), frames=12345, modes=()):
        from ai_player.gates.test_goals import RestTests

        mgr, _, _ = planned(faults=faults)
        record = mgr.bp_record("ch7_brawly")
        before, after = party18(), party18()
        before[2] = replace(before[2], experience=exp[0], level=levels[0])
        after[2] = replace(after[2], experience=exp[1], level=levels[1])
        nav = RestTests.navigator(RestTests(), [look(party=before), look(party=after)])
        mind = types.SimpleNamespace(purpose="travel", trainee=None, raise_modes=[], say=None, bp_faults=None)
        runner = GoalRunner(nav.hands, nav, mgr, mind, lambda line: None)

        def fake_lead(hands, pid, why):
            yield
            return True

        def fake_roam(hands, nav_, steps, why):
            hands.look()
            hands.pad.frames += frames
            mind.raise_modes.extend(modes)
            yield
            return "roamed: 10 training steps"

        with mock.patch.object(goals_module, "lead_with", fake_lead), mock.patch.object(goals_module, "roam_train", fake_roam):
            goals_module_drive(runner._raise(Goal("raise", "r", "ch7_brawly", steps=10, key="raise:ROUTE104"),
                                             lambda s: False))
        return record

    def test_r7a_frames(self):
        self.assertEqual(self.session()["frames"], 12345)
        self.assertEqual(self.session(F(frames_uncounted=True))["frames"], 0)  # FAULT

    def test_r7b_r7c_r7d_stalls_by_exp(self):
        self.assertEqual(self.session(exp=(100, 100))["stalls"], 1)  # +0 EXP: a stall
        self.assertEqual(self.session(F(stalls_never=True), exp=(100, 100))["stalls"], 0)  # FAULT
        self.assertEqual(self.session(exp=(100, 160))["stalls"], 0)  # +EXP, no level: no stall
        self.assertEqual(self.session(F(stall_by_level=True), exp=(100, 160))["stalls"], 1)  # FAULT: BP-1's
        self.assertEqual(self.session(exp=(100, 160), levels=(4, 5))["stalls"], 0)  # +level

    def test_the_counters_and_lead_before(self):
        record = self.session(exp=(100, 146), modes=("switch", "own", "rescue", "run", "not the trainee"))
        self.assertEqual((record["own_fights"], record["switch_fights"], record["raise_runs"], record["exp_gained"]),
                         (1, 2, 1, 46))
        self.assertEqual(record["lead_before"], G)  # slot 0 before the first session (C1's order: Grovyle first)

    def test_r7e_twelve_stalls_spend(self):
        record = bp.new_record()
        record["stalls"] = 12
        self.assertEqual(bp.spent_reason(record, "Story"), "stalls 12 of at most 12")

    def heal_frames(self, faults=bp.NO_FAULTS, status="active"):
        from ai_player.gates.test_goals import RestTests

        mgr, _, _ = planned(faults=faults)
        mgr.bp_record("ch7_brawly")["status"] = status
        nav = RestTests.navigator(RestTests(), [look(party=party18(Wurmple=5))])
        runner = GoalRunner(nav.hands, nav, mgr, types.SimpleNamespace(purpose="travel", trainee=None), lambda line: None)

        def fake(goal, milestone, index, current):
            nav.hands.pad.frames += 777
            yield
            return True, "healed"

        runner._pursue = fake
        milestone, index = at("ch6_briney_house")
        before = mgr.bp_record("ch7_brawly")["frames"]
        goals_module_drive(runner.pursue(Goal("heal", "h", "ch6_briney_house", key="heal:x"), milestone, index,
                                         lambda s: index))
        return mgr.bp_record("ch7_brawly")["frames"] - before, mgr.bp_record("ch7_brawly")["heals"]

    def test_r7f_heal_frames_count_while_active(self):
        self.assertEqual(self.heal_frames(), (777, 1))
        self.assertEqual(self.heal_frames(status="spent"), (0, 0))  # CONTROL: no active plan
        self.assertEqual(self.heal_frames(F(heal_frames_uncounted=True)), (0, 0))  # FAULT

    def test_r7g_the_base_personality_decides(self):
        """`state.base` Story with `state.active` drifted to Trainer (6379): the plan is ACTED on, on Story's budget.
        FAULT `base_to_active`: only logged."""
        for faults, status in ((bp.NO_FAULTS, "active"), (F(base_to_active=True), "logged")):
            mgr = c1_manager("Story")
            mgr.bp_faults = faults
            mgr.state.active = "Trainer"
            decide2(mgr, party18(), world_with("ROUTE104", current="ROUTE104", grass=True))
            self.assertEqual(mgr.bp_record("ch7_brawly")["status"], status, faults)


class LeadAfterTests(unittest.TestCase):
    """R8 (V-m5): the lead when a plan ends, bounded."""

    def manager_with(self, status="spent", lead_before=G, trainee_first=True, faults=bp.NO_FAULTS, **record_fields):
        mgr = c1_manager()
        mgr.bp_faults = faults
        record = mgr.prep(at("ch7_brawly")[0]).setdefault("bp", bp.new_record())
        record.update(status=status, trainee=W, target=19, plan=f"raise:{W:08x}:19", boss="BRAWLY", lead_before=lead_before,
                      settle="pending" if status == "spent" else "none", **record_fields)
        party = party18()
        if trainee_first:
            party[0], party[2] = party[2], party[0]
        return mgr, record, party

    def test_r8a_the_usual_lead_restored(self):
        mgr, record, party = self.manager_with()
        goal = decide2(mgr, party, world_with("ROUTE104", current="ROUTE104", grass=True))
        self.assertEqual((goal.kind, goal.pid, goal.key), ("lead", G, "lead:settle"))
        mgr, record, party = self.manager_with(faults=F(restore_never=True))
        self.assertNotEqual(decide2(mgr, party, world_with("ROUTE104", current="ROUTE104", grass=True)).kind, "lead")

    def test_r8b_control_the_trainee_kept(self):
        """The verdict prefers the trainee (a Dustox L20 leading: READY, against Grovyle's NOT READY): no goal, kept.
        FAULT `restore_always`: the lead goal."""
        for faults, kind in ((bp.NO_FAULTS, None), (F(restore_always=True), "lead")):
            mgr, record, party = self.manager_with(faults=faults)
            party[0] = summary(0, "Dustox", 20, ("Confusion", "Gust", "Protect", "Moonlight"), 55, pid=W)
            goal = decide2(mgr, party, world_with("ROUTE104", current="ROUTE104", grass=True))
            self.assertEqual(goal.kind == "lead", kind == "lead", (faults, goal.kind))
            if kind is None:
                self.assertEqual(record["settle"], "kept")

    def test_r8c_relead_bounded(self):
        mgr, record, party = self.manager_with(relead_fails=2)
        self.assertNotEqual(decide2(mgr, party, world_with("ROUTE104", current="ROUTE104", grass=True)).kind, "lead")
        mgr, record, party = self.manager_with(relead_fails=2, faults=F(relead_unbounded=True))
        self.assertEqual(decide2(mgr, party, world_with("ROUTE104", current="ROUTE104", grass=True)).kind, "lead")

    def done_on_gym(self, faults=bp.NO_FAULTS, **fields):
        mgr, record, party = self.manager_with(status="done", trainee_first=False, faults=faults, **fields)
        gym = world_with("DEWFORD_TOWN_GYM", current="DEWFORD_TOWN_GYM")
        return decide2(mgr, party, gym, milestone_id="ch7_brawly", const="DEWFORD_TOWN_GYM")

    def test_r8d_the_done_plans_relead_is_bounded(self):
        goal = self.done_on_gym()
        self.assertEqual((goal.kind, goal.pid), ("lead", W))
        self.assertNotEqual(self.done_on_gym(reorder_fails=3).kind, "lead")
        self.assertNotEqual(self.done_on_gym(leads=6).kind, "lead")
        self.assertNotEqual(self.done_on_gym(relead_fails=2).kind, "lead")
        self.assertEqual(self.done_on_gym(F(relead_unbounded=True), relead_fails=2).kind, "lead")  # FAULT
        self.assertEqual(self.done_on_gym(F(lead_ignores_budget=True), reorder_fails=3).kind, "lead")  # FAULT (V4)

    def test_r8e_after_the_boss_is_beaten(self):
        mgr, record, party = self.manager_with(status="done")
        record["settle"] = "none"
        goal = decide2(mgr, party, world_with("ROUTE104", current="ROUTE104", grass=True), milestone_id="ch7_exp_share")
        self.assertEqual((goal.kind, goal.pid, goal.key), ("lead", G, "lead:after"))

    def test_r8f_no_usual_lead(self):
        mgr, record, party = self.manager_with(lead_before=None)
        self.assertNotEqual(decide2(mgr, party, world_with("ROUTE104", current="ROUTE104", grass=True)).kind, "lead")
        self.assertEqual(record["settle"], "done")

    def test_the_lead_runner_counts_and_settles(self):
        from ai_player.gates.test_goals import RestTests

        for ok, expected in ((True, ("done", 1, 0)), (False, ("pending", 1, 1))):
            mgr, record, party = self.manager_with()
            nav = RestTests.navigator(RestTests(), [look(party=party)])
            runner = GoalRunner(nav.hands, nav, mgr, types.SimpleNamespace(purpose="travel", trainee=None), lambda line: None)
            asked = []

            def fake_lead(hands, pid, why, ok=ok):
                asked.append(pid)
                yield
                return ok

            milestone, index = at("ch6_briney_house")
            with mock.patch.object(goals_module, "lead_with", fake_lead):
                goals_module_drive(runner._pursue(Goal("lead", "l", "ch7_brawly", key="lead:settle", pid=G), milestone,
                                                  index, lambda s: index))
            self.assertEqual((record["settle"], record["leads"], record["relead_fails"]), expected)
            self.assertEqual(asked, [G])


class LearnerTests(unittest.TestCase):
    """(round 2, the LIVE finding of ledger #118: all three raise runs stuck in one battle) A trainee that levels up while
    SWITCHED OUT is asked to learn a move with another Pokemon on the field: the battle skill (`skills/battle.py` _learn,
    _forget_choice) must name the learner, not the battler, and keep its answers consistent. Reproduced offline first
    (s53/bp1r2/repro_learn.py, predictions hashed): with the pages as the eyes showed them (one partial print a look) the
    40-page window lost "DUSTOX is trying to learn GUST.", the learner was taken to be Grovyle ("forget Absorb"), the forget
    screen kept Dustox's four, and "Stop learning GUST?" was answered NO: the game asked again, without end."""

    DUSTOX, GROVYLE = 0x55cfbff3, 0xd05408ff

    def seen(self, dustox_level: int = 13):
        party = [member("Dustox", dustox_level, DUSTOX_MOVES, 30, 43, self.DUSTOX, 0),
                 member("Grovyle", 22, GROVYLE_MOVES, 34, 60, self.GROVYLE, 2)]
        return battle_look([battle_mon("Grovyle", 22, GROVYLE_MOVES, 34, 60, pid=self.GROVYLE)], [foe("Poochyena", 6, bar=0)],
                           party=party)

    @staticmethod
    def pages_shown(*texts: str):
        from ai_player.skills import battle as skill

        pages = skill._Pages()
        for text in texts:
            for n in range(1, len(text) + 1):  # a page PRINTING is a new page at every look
                pages(types.SimpleNamespace(screen=types.SimpleNamespace(text=text[:n])))
        return pages

    def learn(self, pages, seen, faults=None):
        from ai_player.brain.battle import BattleFaults
        from ai_player.skills import battle as skill

        hands = types.SimpleNamespace(tell=lambda line: None, note=lambda *a, **k: None)
        return skill._learn(hands, seen, "GUST", pages, faults or BattleFaults())

    MESSAGES = ("DUSTOX is trying to learn GUST.", "But, DUSTOX can’t learn more than four moves.",
                "Delete a move to make room for GUST?")

    def test_the_learner_named_by_its_page(self):
        """The page kept apart names Dustox even after the window lost it. Dustox at L14 here, so the 'taught at its level
        now' rule cannot name it (Gust is Dustox's L13 move): the page alone does. FAULT `learner_by_battler`: Grovyle."""
        from ai_player.brain.battle import BattleFaults

        pages = self.pages_shown(*self.MESSAGES)
        self.assertFalse(any("is trying to learn" in p and p.endswith(".") for p in pages.pages))  # the window lost it
        self.assertEqual(self.learn(pages, self.seen(14)).forget, "Harden")
        self.assertEqual(self.learn(pages, self.seen(14), BattleFaults(learner_by_battler=True)).forget, "Absorb")

    def test_met_at_the_question(self):
        """A battle played from the question on (no page seen): the member the game teaches Gust NOW (Dustox L13); FAULT:
        the battler, Grovyle. CONTROL: at L14 (nobody is taught Gust now) the battler, as before."""
        from ai_player.brain.battle import BattleFaults

        fresh = self.pages_shown(self.MESSAGES[2])
        self.assertEqual(self.learn(fresh, self.seen(13)).forget, "Harden")
        self.assertEqual(self.learn(fresh, self.seen(13), BattleFaults(learner_by_battler=True)).forget, "Absorb")
        self.assertEqual(self.learn(self.pages_shown(self.MESSAGES[2]), self.seen(14)).forget, "Absorb")

    def test_the_forget_screen_rechecks(self):
        """The forget screen lists Dustox's four: a choice made for Grovyle ("forget Absorb") is made again for Dustox (row
        3, Harden), and it is the choice "Stop learning?" is answered by. FAULT `forget_unchecked`: the row of the new
        move (keep the four) while the choice still says LEARN: the live loop. CONTROL: a choice already Dustox's stands."""
        from ai_player.brain.battle import BattleFaults, LearnChoice
        from ai_player.skills import battle as skill

        hands = types.SimpleNamespace(tell=lambda line: None, note=lambda *a, **k: None)
        names = ["Tackle", "Confusion", "Poison Sting", "Harden", "Gust"]
        wrong = LearnChoice(True, "Absorb", "for Grovyle")
        index, _, learn = skill._forget_choice(hands, self.seen(13), names, wrong)
        self.assertEqual((index, learn.learn, learn.forget), (3, True, "Harden"))
        index, _, learn = skill._forget_choice(hands, self.seen(13), names, wrong, BattleFaults(forget_unchecked=True))
        self.assertEqual((index, learn.learn, learn.forget), (4, True, "Absorb"))
        right = LearnChoice(True, "Harden", "for Dustox")
        self.assertEqual(skill._forget_choice(hands, self.seen(13), names, right)[0::2], (3, right))


class OwnImmunityTests(unittest.TestCase):
    """R9 (V-m1): the party's fixed damage against a type immune to it."""

    def test_night_shade(self):
        sableye = bp.Member(9, "Sableye", 20, 58, 58, ("Night Shade",))
        normal = BossMon("Zigzagoon", 20, ("Tackle",), None)
        fighting = BossMon("Machop", 20, ("Karate Chop",), None)
        self.assertEqual(bp._own_points(sableye, normal, "Night Shade"), 0)
        self.assertEqual(bp.verdict([sableye], 9, [normal], "Story").cls, bp.NOT_READY)
        control = bp._own_points(sableye, fighting, "Night Shade")
        self.assertGreater(control, 0)  # CONTROL: the rough share of its 20 points
        self.assertEqual(bp._own_points(sableye, fighting, "Night Shade", F(no_immunity_own=True)), control)
        self.assertGreater(bp._own_points(sableye, normal, "Night Shade", F(no_immunity_own=True)), 0)  # FAULT
        self.assertEqual(bp.verdict([sableye], 9, [normal], "Story", F(no_immunity_own=True)).cls, bp.READY)


# ===================================================================================== ROUND 3 (2026-11-11)
# The trainee SAFE throughout an active plan: the round-2 verifier's V2-M1 (the raise's run mode kept a low trainee on the
# field) and V2-M2 (the trainee led every other battle of the plan), the lead's design D1-D5. Reproduced first on c5146e53
# (s53/bp1r3/repro_r3.py, predictions hashed, 10 of 10 held). Fixtures observed with s53/bp1r3/explore_fixtures.py, then
# pinned here.
CASCOON_MOVES = ["Tackle", "String Shot", "Poison Sting", "Harden"]


def cascoon_member(hp: int = 14):
    return member("Cascoon", 7, CASCOON_MOVES, hp, 26, W, 0)


def own_cascoon(hp: int = 14):
    return battle_mon("Cascoon", 7, CASCOON_MOVES, hp, 26, pid=W)


def guard_mind(faults=None, purpose: str = "travel", bp_faults=None) -> BattleMind:
    """A battle mind OUTSIDE a raise (a heal walk's "travel") told to protect the plan's trainee W (round 3, D2)."""
    from ai_player.brain.battle import BattleFaults

    mind = BattleMind("Story", random.Random("1:battle"), purpose, faults or BattleFaults())
    mind.guard = W
    mind.bp_faults = bp_faults
    return mind


class RescueTests(unittest.TestCase):
    """(round 3, V2-M1, design D1) A raise battle never keeps the trainee on the field under its floor while another member
    can come in: a refused run, or the trainee under its floor on any turn, is answered with the RESCUE (`BattleMind.
    rescue_member`: a member that CAN WIN, `fight_safe` keep 0; with none and the trainee under its floor, any member that
    can come in); only with nobody to come in does it run again, within `MAX_RUN_TRIES`. The live case (#120 6402): Cascoon
    L7 14/26 against Taillow L7, Grovyle at 32/57 (no PARTNER: it would not keep a third, 32 - 2 x 8 = 16 < 19, but it CAN
    WIN, 16 > 0), 4 runs refused, the trainee fainted."""

    def battle(self, faults=None, trainee_hp=14, later_hp=None, grovyle_hp=32, pooch_hp=21, foe_=("Taillow", 7)):
        mind = raise_mind(faults)
        party = [cascoon_member(trainee_hp), grovyle_member(grovyle_hp), poochyena_member(pooch_hp)]
        first = battle_turn(mind, own_cascoon(trainee_hp), foe(*foe_), party)
        hp = trainee_hp if later_hp is None else later_hp
        party = [cascoon_member(hp), grovyle_member(grovyle_hp), poochyena_member(pooch_hp)]
        second = battle_turn(mind, own_cascoon(hp), foe(*foe_), party, begin=False)
        return mind, first, second

    def test_r3n_a_refused_run_under_the_floor_is_rescued(self):
        """R3n (the verifier's): turn 1 runs (no partner), the run is refused, the trainee is at 3/26: the rescue to
        Grovyle, the battle counted "rescue". FAULT `run_no_rescue`: "run again" (round 2, the live faint). CONTROL: with
        nobody to come in (Grovyle and Poochyena fainted) it runs again."""
        from ai_player.brain.battle import BattleFaults

        mind, first, second = self.battle(later_hp=3)
        self.assertEqual((first.action, second.action, second.switch_pid, mind.memory.raise_mode, mind.raise_modes),
                         ("run", "switch", G, "rescue", ["rescue"]))
        mind, _, second = self.battle(BattleFaults(run_no_rescue=True), later_hp=3)
        self.assertEqual((second.action, mind.raise_modes), ("run", ["run"]))
        mind, _, second = self.battle(later_hp=3, grovyle_hp=0, pooch_hp=0)
        self.assertEqual((second.action, second.reason), ("run", "raising: still no member to knock it out: run again"))

    def test_r3o_a_refused_run_above_the_floor_goes_to_a_member_that_can_win(self):
        """The trainee still at 14/26 after the refusal: Grovyle at 32/57 CAN WIN (not a partner, which keeps a third):
        rescued. FAULT `rescue_needs_partner` (round 2's partner line for the rescue): run again."""
        from ai_player.brain.battle import BattleFaults

        mind, _, second = self.battle()
        self.assertEqual((second.action, second.switch_pid), ("switch", G))
        self.assertIn("can win it", second.reason)
        _, _, second = self.battle(BattleFaults(rescue_needs_partner=True))
        self.assertEqual(second.action, "run")

    def test_r3p_run_again_when_nobody_can_win(self):
        """(the verifier's REDUNDANT mutant `run_no_retry`) the trainee at 14/26 above its floor, Grovyle at 10/57 (it cannot
        win: 10 - 9 < 1) and Poochyena L6 (8 hits) against a Taillow L8: "run again", up to `MAX_RUN_TRIES`, then the
        ordinary rules (a fight). Without the retry the ordinary rules FIGHT at once (14/26 is above run_low, the foe 1
        level up)."""
        from ai_player.brain.battle import MAX_RUN_TRIES

        mind, first, second = self.battle(grovyle_hp=10, foe_=("Taillow", 8))
        self.assertEqual((first.action, second.action, second.reason),
                         ("run", "run", "raising: still no member to knock it out: run again"))
        party = [cascoon_member(14), grovyle_member(10), poochyena_member()]
        actions = [battle_turn(mind, own_cascoon(14), foe("Taillow", 8), party, begin=False).action
                   for _ in range(MAX_RUN_TRIES + 1)]
        self.assertEqual(actions.count("run"), MAX_RUN_TRIES - 2)  # 2 already made: the bound holds
        self.assertEqual(actions[-1], "fight")

    def test_r3r_under_the_floor_any_member_that_can_come_in(self):
        """Nobody can win (Grovyle 10/57, Poochyena L6 against a Taillow L8) and the trainee is at 3/26: the rescue goes to
        the member that can come in (Poochyena): a run the game refuses would leave the trainee on the field. FAULT
        `rescue_no_fallback`: run again. CONTROL (R3p): above its floor it runs again."""
        from ai_player.brain.battle import BattleFaults

        _, _, second = self.battle(later_hp=3, grovyle_hp=10, foe_=("Taillow", 8))
        self.assertEqual((second.action, second.switch_pid), ("switch", P))
        self.assertIn("no member is sure to win it", second.reason)
        _, _, second = self.battle(BattleFaults(rescue_no_fallback=True), later_hp=3, grovyle_hp=10, foe_=("Taillow", 8))
        self.assertEqual(second.action, "run")

    def test_r3s_under_the_floor_on_its_first_decision(self):
        """A raise battle met with the trainee at 5/26 (the walk to the grass): no partner (Grovyle 32/57), the rescue on
        turn 1, not a run. FAULT `run_no_rescue`: the run."""
        from ai_player.brain.battle import BattleFaults

        party = [cascoon_member(5), grovyle_member(32), poochyena_member()]
        mind = raise_mind()
        decision = battle_turn(mind, own_cascoon(5), foe("Taillow", 7), party)
        self.assertEqual((decision.action, decision.switch_pid, mind.raise_modes), ("switch", G, ["rescue"]))
        mind = raise_mind(BattleFaults(run_no_rescue=True))
        self.assertEqual(battle_turn(mind, own_cascoon(5), foe("Taillow", 7), party).action, "run")

    def test_the_own_fights_rescue_needs_only_a_win(self):
        """An own fight (Dustox L12 full against Nincada L7) gone badly (10/38, the foe's bar still full: its hits missed):
        Grovyle at 32/57 cannot keep a third (32 - 2 x 8) but can win: the rescue. FAULT `rescue_needs_partner`: no switch
        (round 2: the raise's run rule, the trainee left on the field). (A bar of 83% would make Grovyle a partner: one
        hit of its summary's 23 points, observed.)"""
        from ai_player.brain.battle import BattleFaults

        for faults, expected in ((None, "switch"), (BattleFaults(rescue_needs_partner=True), "run")):
            mind = raise_mind(faults)
            party = [member("Dustox", 12, DUSTOX_MOVES, 38, 38, W, 0), grovyle_member(32), poochyena_member()]
            first = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 38, 38, pid=W), foe("Nincada", 7), party)
            self.assertEqual(first.action, "fight")
            party = [member("Dustox", 12, DUSTOX_MOVES, 10, 38, W, 0), grovyle_member(32), poochyena_member()]
            second = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 10, 38, pid=W), foe("Nincada", 7), party,
                                 begin=False)
            self.assertEqual(second.action, expected, faults)

    def test_can_win_is_fight_safe_with_keep_zero(self):
        """`fight_safe(..., keep=0)` asks only that the member be STANDING (1 HP or more) after the worst case; the default
        keeps a third. Grovyle L21 against a Taillow L8 (2 hits, 9 a hit at worst): wins from 19, keeps a third from 37."""
        grovyle = bp.Member(G, "Grovyle", 21, 57, 57, tuple(GROVYLE_MOVES))
        self.assertEqual([hp for hp in range(1, 58) if bp.fight_safe(grovyle, "Taillow", 8, 1.0, hp, keep=0)[0]][0], 17)
        self.assertEqual([hp for hp in range(1, 58) if bp.fight_safe(grovyle, "Taillow", 8, 1.0, hp)[0]][0], 35)


class PartnerLineTests(unittest.TestCase):
    """(round 3, V2-M1, design D1) The rest line and the partner line agree: the raise rests when its knock-out partner is
    not a PARTNER (`bossprep.partner_fit`: half its HP and a safe win) against every wild Pokemon of the raise map, each
    at its highest level there (`seasoned.land_slots`), replacing round 2's flat half (FAULT `partner_half_line`)."""

    def party(self, grovyle_hp: int):
        return [member("Wurmple", 4, ["Tackle", "String Shot"], 18, 18, W, 0), grovyle_member(grovyle_hp)]

    def test_the_route116_slots(self):
        self.assertEqual(seasoned.land_slots("ROUTE116"), (("Abra", 7), ("Nincada", 7), ("Poochyena", 8), ("Skitty", 8),
                                                          ("Taillow", 8), ("Whismur", 6)))
        self.assertEqual(seasoned.land_slots("NOWHERE"), ())

    def test_the_rest_line_is_the_battles_partner_line(self):
        """For every HP of Grovyle L21 (1-57) on ROUTE116: the raise does not rest EXACTLY when the battle brain finds a
        partner against every wild Pokemon of the map (`BattleMind.raise_partner`). FAULT `partner_half_line`: they
        disagree at 29-34/57 (the live V2-M1 gap: "not worn" and "no partner" at once)."""
        def disagree(faults):
            out = []
            for hp in range(1, 58):
                seen = look(party=self.party(hp))
                rests = bp.partner_worn(seen, W, faults, "ROUTE116") is not None
                partners = all(raise_mind().raise_partner(battle_look([battle_mon("Wurmple", 4, ["Tackle"], 18, 18, pid=W)],
                                                                      [foe(species, level)], party=self.party(hp)),
                                                          foe(species, level)) is not None
                               for species, level in seasoned.land_slots("ROUTE116"))
                if rests == partners:
                    out.append(hp)
            return out

        self.assertEqual(disagree(bp.NO_FAULTS), [])
        self.assertEqual(disagree(F(partner_half_line=True)), list(range(29, 35)))

    def test_the_line_against_the_strongest_slot(self):
        """Grovyle at 32/57 rests on ROUTE116 (no safe partner against Nincada L7, Skitty L8 or Taillow L8), at 40/57 not;
        with no raise map known, round 2's half line (32 is not worn)."""
        said = bp.partner_worn(look(party=self.party(32)), W, bp.NO_FAULTS, "ROUTE116")
        self.assertIn("(32/57) is not a safe partner against Nincada L7 on ROUTE116", said)
        self.assertIsNone(bp.partner_worn(look(party=self.party(40)), W, bp.NO_FAULTS, "ROUTE116"))  # CONTROL
        self.assertIsNone(bp.partner_worn(look(party=self.party(32)), W, bp.NO_FAULTS, None))
        self.assertIsNone(bp.partner_worn(look(party=self.party(32)), W, F(partner_half_line=True), "ROUTE116"))  # FAULT

    def test_half_its_hp_is_part_of_the_line(self):
        """Against an Abra L7 (it knows only Teleport) Grovyle at 28/57 wins safely, but is under half: no partner (the
        battle brain's health rule for a member to switch to). CONTROL: at 29/57, one."""
        grovyle = bp.Member(G, "Grovyle", 21, 57, 57, tuple(GROVYLE_MOVES))
        self.assertTrue(bp.fight_safe(grovyle, "Abra", 7, 1.0, 28)[0])
        self.assertFalse(bp.partner_fit(grovyle, "Abra", 7, 1.0, 28)[0])
        self.assertTrue(bp.partner_fit(grovyle, "Abra", 7, 1.0, 29)[0])

    def goal(self, grovyle_hp: int, faults=bp.NO_FAULTS):
        mgr = c1_manager()
        mgr.bp_faults = faults
        world = world_with(*SEVEN, current="ROUTE104", grass=True)
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
            return decide2(mgr, party18(Grovyle=grovyle_hp), world)

    def test_the_party_rests_before_the_next_raise(self):
        """The next raise would go to ROUTE116: Grovyle at 32/57 makes the party rest (a heal goal, its reason the partner
        line). FAULT `partner_half_line`: the raise on ROUTE116 (round 2). CONTROL: at 40/57, the raise."""
        goal = self.goal(32)
        self.assertIn(goal.kind, ("heal", "find_center"))
        self.assertIn("not a safe partner against", goal.reason)
        self.assertEqual((self.goal(32, F(partner_half_line=True)).kind, self.goal(32, F(partner_half_line=True)).map),
                         ("raise", "ROUTE116"))
        self.assertEqual((self.goal(40).kind, self.goal(40).map), ("raise", "ROUTE116"))

    def test_the_raise_roam_rests_on_its_map(self):
        """The raise roam's rest after a battle asks the line against the map it roams (`roam_hooks(raise_map=...)`)."""
        from ai_player.gates.test_goals import RestTests

        nav = RestTests.navigator(RestTests(), [look(party=party18())])
        runner = GoalRunner(nav.hands, nav, c1_manager(), None, lambda line: None)
        runner.roam_hooks(trainee=W, after_battle=lambda observation: None, raise_map="ROUTE116")
        self.assertIn("not a safe partner", nav.battle_rest(look(party=party18(Grovyle=32))))
        self.assertIsNone(nav.battle_rest(look(party=party18(Grovyle=40))))  # CONTROL

    def test_the_raise_session_gives_its_map_to_the_rest(self):
        """A raise session on ROUTE116 (`GoalRunner._raise`, lead and roam faked): the rest its roam asks after a battle
        is the partner line on ROUTE116 (Grovyle at 32/57: rest). CONTROL: at 40/57, none."""
        from ai_player.gates.test_goals import RestTests

        for hp, rests in ((32, True), (40, False)):
            mgr, _, _ = planned()
            nav = RestTests.navigator(RestTests(), [look(party=party18()), look(party=party18())])
            mind = types.SimpleNamespace(purpose="travel", trainee=None, raise_modes=[], say=None, bp_faults=None)
            runner = GoalRunner(nav.hands, nav, mgr, mind, lambda line: None)
            said = []

            def fake_lead(hands, pid, why):
                yield
                return True

            def fake_roam(hands, nav_, steps, why, hp=hp):
                said.append(nav_.battle_rest(look(party=party18(Grovyle=hp))))
                yield
                return "roamed: 10 training steps"

            nav.world.here = lambda: types.SimpleNamespace(const="ROUTE116")  # already on the raise map: no walk
            with mock.patch.object(goals_module, "lead_with", fake_lead), \
                    mock.patch.object(goals_module, "roam_train", fake_roam):
                goals_module_drive(runner._raise(Goal("raise", "r", "ch7_brawly", map="ROUTE116", steps=10,
                                                      key="raise:ROUTE116"), lambda s: False))
            self.assertEqual(len(said), 1)
            self.assertEqual(said[0] is not None and "not a safe partner against" in said[0], rests, (hp, said))


class GuardTests(unittest.TestCase):
    """(round 3, V2-M2, design D2) Outside a raise battle an ACTIVE plan's trainee (`BattleMind.guard`) leading a battle is
    switched out on its first decision when it is under its floor, or (wild) would not win safely, to the member that
    takes its place (`rescue_member`); on a later turn under its floor, rescued, never "run again" while a member can
    come in. The live cases: #118 6397 (a heal walk, Wurmple at 3/21 led against a Poochyena L6, 2 runs refused, fainted),
    #120 6400 (Wurmple at 11/23 against a Taillow L6), 6401 (a pick-up at 18/18 against a Whismur L6)."""

    def wurmple(self, level=5, hp=3, max_hp=21):
        return member("Wurmple", level, ["Tackle", "String Shot"], hp, max_hp, W, 0)

    def own_wurmple(self, level=5, hp=3, max_hp=21):
        return battle_mon("Wurmple", level, ["Tackle", "String Shot"], hp, max_hp, pid=W)

    def party(self, trainee, grovyle_hp=57):
        return [trainee, grovyle_member(grovyle_hp), poochyena_member()]

    def test_g1_the_heal_walk(self):
        """Wurmple L5 at 3/21 leads a Poochyena L6 on the walk to heal it: the switch to Grovyle. FAULT `guard_off`: the
        travel rule's run (round 2). CONTROL: no guard (chapters 1-5): the run, as before."""
        from ai_player.brain.battle import BattleFaults

        mind = guard_mind()
        decision = battle_turn(mind, self.own_wurmple(), foe("Poochyena", 6), self.party(self.wurmple()))
        self.assertEqual((decision.action, decision.switch_pid, mind.memory.guard_mode), ("switch", G, "switch"))
        self.assertIn("is protected: it is under its floor", decision.reason)
        self.assertEqual(battle_turn(guard_mind(BattleFaults(guard_off=True)), self.own_wurmple(), foe("Poochyena", 6),
                                     self.party(self.wurmple())).action, "run")
        plain = BattleMind("Story", random.Random("1:battle"), "travel")
        self.assertEqual(battle_turn(plain, self.own_wurmple(), foe("Poochyena", 6), self.party(self.wurmple())).action,
                         "run")

    def test_g2_a_wild_fight_it_would_not_win_safely(self):
        """Wurmple L6 at 11/23 (above its floor) against a Taillow L6: it would not win safely: the switch. CONTROL: a
        Dustox L12 full against a Whismur L6 wins safely: no switch ("own": the ordinary rules decide)."""
        mind = guard_mind()
        decision = battle_turn(mind, self.own_wurmple(6, 11, 23), foe("Taillow", 6), self.party(self.wurmple(6, 11, 23)))
        self.assertEqual((decision.action, decision.switch_pid), ("switch", G))
        self.assertIn("would not win safely", decision.reason)
        mind = guard_mind()
        party = [member("Dustox", 12, DUSTOX_MOVES, 38, 38, W, 0), grovyle_member(), poochyena_member()]
        decision = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 38, 38, pid=W), foe("Whismur", 6), party)
        self.assertNotEqual(decision.action, "switch")
        self.assertEqual(mind.memory.guard_mode, "own")

    def test_g3_a_trainers_battle(self):
        """A trainer's battle: only the floor counts (its foes are not wild): at 21/21 it fights; at 5/21 the switch. FAULT
        `guard_off`: it fights at 5/21."""
        from ai_player.brain.battle import BattleFaults

        for hp, faults, expected in ((21, None, "fight"), (5, None, "switch"), (5, BattleFaults(guard_off=True), "fight")):
            mind = guard_mind(faults)
            decision = battle_turn(mind, self.own_wurmple(hp=hp), foe("Poochyena", 6), self.party(self.wurmple(hp=hp)),
                                   kind="trainer")
            self.assertEqual(decision.action, expected, (hp, faults))

    def test_g4_a_later_turn_under_the_floor(self):
        """An own fight (Dustox L12 full against a Whismur L6) at 10/38 a turn later: rescued, not the travel rule's run.
        FAULT `guard_turn1_only`: the run (a refused run would then be answered with "run again")."""
        from ai_player.brain.battle import BattleFaults

        for faults, expected in ((None, "switch"), (BattleFaults(guard_turn1_only=True), "run")):
            mind = guard_mind(faults)
            party = [member("Dustox", 12, DUSTOX_MOVES, 38, 38, W, 0), grovyle_member(), poochyena_member()]
            battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 38, 38, pid=W), foe("Whismur", 6), party)
            party = [member("Dustox", 12, DUSTOX_MOVES, 10, 38, W, 0), grovyle_member(), poochyena_member()]
            decision = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 10, 38, pid=W), foe("Whismur", 6, bar=40),
                                   party, begin=False)
            self.assertEqual(decision.action, expected, faults)
        self.assertEqual(mind.memory.guard_mode, "own")

    def test_g5_never_sent_in_while_another_can_fight(self):
        """The replacement after a faint is never the guarded trainee while another member can fight; "Use next POKéMON?"
        with only it left is NO. CONTROL (no guard): the trainee, the better matched, is sent in; YES."""
        fainted = battle_mon("Grovyle", 21, GROVYLE_MOVES, 0, 57, pid=G)
        party = [member("Dustox", 12, DUSTOX_MOVES, 38, 38, W, 0), grovyle_member(0), poochyena_member()]
        seen = battle_look([fainted], [foe("Whismur", 6)], party=party)
        self.assertEqual(guard_mind().replacement(seen)[0], P)
        self.assertEqual(BattleMind("Story", random.Random("1:battle"), "travel").replacement(seen)[0], W)  # CONTROL
        alone = battle_look([fainted], [foe("Poochyena", 6)],
                            party=[self.wurmple(hp=21), grovyle_member(0), poochyena_member(0)])
        self.assertFalse(guard_mind().answer("Use next POKéMON?", alone)[0])
        self.assertTrue(BattleMind("Story", random.Random("1:battle"), "travel").answer("Use next POKéMON?", alone)[0])

    def test_g6_never_switched_in_for_a_matchup(self):
        """A trainer's battle: Grovyle (badly matched against a Taillow's Peck) would switch to the guarded Dustox (Confusion,
        the better match) by the ordinary rule; guarded, it does not. CONTROL: no guard, the switch to it."""
        own = battle_mon("Poochyena", 14, ["Tackle", "Howl", "Bite"], 40, 40, pid=P)
        party = [member("Poochyena", 14, ["Tackle", "Howl", "Bite"], 40, 40, P, 0),
                 member("Dustox", 14, DUSTOX_MOVES, 40, 40, W, 1)]
        plain = BattleMind("Story", random.Random("1:battle"), "travel")
        foe_ = foe("Makuhita", 14)
        ordinary = plain.better_member(battle_look([own], [foe_], party=party, kind="trainer"), own, foe_)
        self.assertIsNotNone(ordinary)
        self.assertEqual(ordinary[0].pid, W)
        self.assertIsNone(guard_mind().better_member(battle_look([own], [foe_], party=party, kind="trainer"), own, foe_))

    def test_g7_only_the_guarded_trainee_and_never_in_a_raise(self):
        """None for another member on the field, and in a raise battle (its own rules): the guard is ignored there."""
        mind = guard_mind()
        own = battle_mon("Grovyle", 21, GROVYLE_MOVES, 57, 57, pid=G)
        battle_turn(mind, own, foe("Poochyena", 6), [grovyle_member(), self.wurmple(), poochyena_member()])
        self.assertIsNone(mind.memory.guard_mode)
        mind = guard_mind(purpose="raise")
        mind.trainee = W
        battle_turn(mind, self.own_wurmple(hp=21), foe("Poochyena", 6), self.party(self.wurmple(hp=21)))
        self.assertIsNone(mind.memory.guard_mode)
        self.assertEqual(mind.memory.raise_mode, "switch")


class GuardRunnerTests(unittest.TestCase):
    """(round 3, V2-M2, design D2) The goal runner tells the battle brain whom to protect, per goal (`_guard_for`): the
    ACTIVE plan's trainee in every goal but a raise and the boss fight itself (the story's own talk to the leader)."""

    def pursued(self, goal_kind="heal", faults=bp.NO_FAULTS, status="active"):
        from ai_player.gates.test_goals import RestTests

        mgr, _, _ = planned(faults=faults)
        mgr.bp_record("ch7_brawly")["status"] = status
        nav = RestTests.navigator(RestTests(), [look(party=party18(Wurmple=3))])
        mind = BattleMind("Story", random.Random("1:battle"), "travel")
        runner = GoalRunner(nav.hands, nav, mgr, mind, lambda line: None)
        seen = {}

        def fake_heal(goal):
            seen["guard"], seen["say"], seen["purpose"] = mind.guard, mind.say, mind.purpose
            yield
            return "healed"

        runner._heal = fake_heal
        milestone, index = at("ch6_briney_house")
        goals_module_drive(runner.pursue(Goal(goal_kind, "the trainee is low (3/18)", milestone.id, key="heal"),
                                         milestone, index, lambda s: index))
        return seen, mgr, runner

    def test_a_heal_walk_is_guarded(self):
        seen, _, _ = self.pursued()
        self.assertEqual((seen["guard"], seen["purpose"]), (W, "travel"))
        self.assertIsNotNone(seen["say"])
        self.assertIsNone(self.pursued(faults=F(guard_unset=True))[0]["guard"])  # FAULT: round 2
        self.assertIsNone(self.pursued(status="spent")[0]["guard"])  # CONTROL: no active plan

    def test_the_boss_fight_and_the_raise_are_left_out(self):
        _, mgr, runner = self.pursued()
        talk = Goal("talk", "BRAWLY", "ch7_brawly", look="brawly", key="talk:brawly")
        self.assertIsNone(runner._guard_for(talk))
        self.assertIsNone(runner._guard_for(Goal("raise", "r", "ch7_brawly", map="ROUTE116", key="raise:ROUTE116")))
        self.assertEqual(runner._guard_for(Goal("chat", "a chat", "ch7_brawly", key="chat:x")), W)  # CONTROL
        self.assertEqual(runner._guard_for(Goal("find", "BRAWLY", "ch7_brawly", look="brawly", key="find:brawly")), W)
        mgr.bp_faults = F(guard_in_boss_fight=True)
        self.assertEqual(runner._guard_for(talk), W)  # FAULT

    def test_chapter_5_has_no_guard(self):
        """No plan (chapters 1-5): no guard, whatever the goal."""
        from ai_player.gates.test_goals import RestTests

        mgr = c1_manager()
        nav = RestTests.navigator(RestTests(), [look(party=party18())])
        runner = GoalRunner(nav.hands, nav, mgr, BattleMind("Story", random.Random("1:battle"), "travel"), lambda l: None)
        self.assertIsNone(runner._guard_for(Goal("heal", "h", "ch5_rival_meet", key="heal")))


class ShiftContextTests(unittest.TestCase):
    """(round 3, design D5: the round-2 builder's new stop "the shift question's context rests on the same 40-page window
    that lost the learner's page") It does NOT: the shift question is ONE message whose first page names the next foe
    (`src/battle_message.c:369` sText_EnemyAboutToSwitchPkmn), and the eyes' text is that message from its start
    (`host/eyes.py` _text), so the context (`skills/battle.py` _shift_context) carries the foe in the screen's text. The
    window's last 4 pages are the question page printing, never the foe's page."""

    MESSAGE = "LEADER BRAWLY is about to use MAKUHITA.¶Will MILO change POKéMON?"

    def test_the_foe_is_in_the_screens_text_not_the_window(self):
        from ai_player.brain.battle import incoming
        from ai_player.skills import battle as skill

        pages = LearnerTests.pages_shown(self.MESSAGE)  # one partial print a look, as the eyes show it
        self.assertFalse(any("about to use" in page for page in pages.pages[-4:]))  # the window's last 4: the question
        own = battle_mon("Grovyle", 24, GROVYLE_MOVES, 40, 65, pid=G)
        seen = battle_look([own], [foe("Meditite", 16, bar=0)], party=[grovyle_member()], kind="trainer")
        seen = replace(seen, screen=replace(seen.screen, text=self.MESSAGE))
        context = skill._shift_context(pages, seen)
        self.assertEqual(incoming(context, None)[0].species, "Makuhita")
        self.assertIsNone(incoming(" ".join(pages.pages[-4:]), None)[0])  # CONTROL: the window alone names nobody
        yes, why = BattleMind("Story", random.Random("1:battle"), "travel").answer("Will MILO change POKéMON?", seen,
                                                                                 None, context)
        self.assertIn("MAKUHITA comes next", why)


class LearnerKeptPageTests(unittest.TestCase):
    """(round 3, design D3: the verifier's REDUNDANT mutant `learning_any_move`) The page kept apart is used only for the
    move it names: a kept "SHROOMISH is trying to learn MEGA DRAIN." does not make Shroomish the learner of GUST."""

    def test_a_kept_page_for_another_move(self):
        from ai_player.skills import battle as skill

        filler = tuple(f"Grovyle used POUND! ({n})" for n in range(45))  # the window loses every learn page
        pages = LearnerTests.pages_shown("SHROOMISH is trying to learn MEGA DRAIN.", *filler,
                                         *LearnerTests.MESSAGES[1:])
        self.assertEqual(pages.learning, ("shroomish", "mega drain"))
        self.assertFalse(any("is trying to learn" in page for page in pages.pages))
        party = [member("Dustox", 13, DUSTOX_MOVES, 30, 43, LearnerTests.DUSTOX, 0),
                 member("Shroomish", 10, ["Absorb", "Tackle", "Stun Spore", "Leech Seed"], 20, 30, 0x5150, 1),
                 member("Grovyle", 22, GROVYLE_MOVES, 34, 60, LearnerTests.GROVYLE, 2)]
        seen = battle_look([battle_mon("Grovyle", 22, GROVYLE_MOVES, 34, 60, pid=LearnerTests.GROVYLE)],
                           [foe("Poochyena", 6, bar=0)], party=party)
        hands = types.SimpleNamespace(tell=lambda line: None, note=lambda *a, **k: None)
        choice = skill._learn(hands, seen, "GUST", pages)
        self.assertEqual(choice.forget, "Harden")  # Dustox, the member taught Gust at L13 now


class SettleNotFirstTests(unittest.TestCase):
    """(round 3, design D3: the verifier's REDUNDANT mutant `settle_any_lead`) E1 with the trainee NOT first: nothing of the
    plan's to undo: no lead goal, the settle "done"."""

    def test_the_trainee_not_first(self):
        mgr = c1_manager()
        record = mgr.prep(at("ch7_brawly")[0]).setdefault("bp", bp.new_record())
        record.update(status="spent", trainee=W, target=19, plan=f"raise:{W:08x}:19", boss="BRAWLY", lead_before=P,
                      settle="pending")
        party = party18()  # Grovyle first, the trainee third; the usual lead (Poochyena) second
        goal = decide2(mgr, party, world_with("ROUTE104", current="ROUTE104", grass=True))
        self.assertNotEqual(goal.kind, "lead", goal.reason)
        self.assertEqual(record["settle"], "done")


if __name__ == "__main__":
    unittest.main(verbosity=2)
