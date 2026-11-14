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

ROUND 4 (2026-11-11; the round-3 verifier's V3-M1, V3-M2, V3-m1 to V3-m4, the lead's design E1-E6): FullPartnerTests (a heal
only when it can change the decision: the partner line judged healed, once per map; the budget before any rest; the
verifier's H1-H6), LastResortTests (no member sure to win: the trainee's own sure win, a run, and only then a member that
cannot win; the live 6413 battle 106), TrainerGuardTests (trainer battles judged as wild ones; a raise goal's trainer
battles guarded), SeamTests (the guard and the purpose reset at each goal's end), PPTests (a move at 0 PP is no move; a
session ends and the party heals out of PP), CoverageTests (the verifier's REDUNDANT mutants given a test). Reproduced
first on 975964c7 (s53/bp1r4/repro_r4.py, 17 of 17 held); fixtures observed with s53/bp1r4/explore_fixtures_r4.py.

ROUND 4, THE CLOSING PASS (2026-11-12; the round-4 verifier's V4-m4): ClosingTests, four round-4 rules the verifier's
mutants broke with every test green (the raise map's cap, an unread PP, the order of "low" and "out of PP", the last
resort's run bound). The gap was shown first on d4794135's tests (s53/bp1r4c/gap_run.py: each of the four mutants passed
all 825 tests of test_bossprep, test_hands, test_goals and test_battle); fixtures observed with s53/bp1r4c/c2a_explore.py
and c2cd_measure.py, then pinned. No play code changed.
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
from ai_player.gates.test_battle import foe, look as battle_look, member, mon as battle_mon, slot  # noqa: E402
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
        """A trainer's battle: (round 4, V3-m1, the lead's E3) the SAME test as a wild one: at 21/21 Wurmple L5 would not
        win safely against a Poochyena L6 (8 of its hits), so the switch; at 5/21 (under its floor) the switch. FAULT
        `guard_wild_only` (round 3: only the floor in a trainer's battle): it fights at 21/21. FAULT `guard_off`: it fights
        at 5/21."""
        from ai_player.brain.battle import BattleFaults

        for hp, faults, expected in ((21, None, "switch"), (21, BattleFaults(guard_wild_only=True), "fight"),
                                     (5, None, "switch"), (5, BattleFaults(guard_off=True), "fight")):
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
            seen["bp_faults"] = mind.bp_faults  # (round 4, E6) the faults a guarded goal hands the battle brain
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


# ===================================================================================== ROUND 4 (2026-11-11)
# The round-3 verifier's V3-M1 (a heal loop when the partner fails its line even at full HP), V3-M2 (the guard's fallback
# sent a member that cannot win), V3-m1 (trainer battles), V3-m2 (the seam between goals), V3-m3 (PP), V3-m4 (coverage); the
# lead's design E1-E6 (`06-DECISIONS-LOG.md`, 2026-11-11, "The fix round after BP-1 round 3 and P11-1"). Reproduced first on
# 975964c7 (s53/bp1r4/repro_r4.py, predictions hashed, 17 of 17 held); fixtures observed with s53/bp1r4/explore_fixtures_r4.py,
# then pinned.
CB = 0x1007
COMBUSKEN_MOVES = ["Scratch", "Ember", "Double Kick", "Peck"]
WURMPLE_MOVES = ["Tackle", "String Shot"]


def grovyle17(hp: int = 46) -> list[MonSummary]:
    """C1's party (`party18`) with the verifier's partner: a Grovyle L17, max HP 46 (its typical), at `hp`."""
    out = party18()
    out[0] = replace(out[0], level=17, max_hp=46, hp=hp)
    return out


def seven_and_a_centre():
    return world_with(*SEVEN, "RUSTBORO_CITY", current="ROUTE104", grass=True, center_from="RUSTBORO_CITY")


def decide_on(mgr, party, world):
    with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
        return decide2(mgr, party, world)


def planned_on(party, faults=bp.NO_FAULTS, world=None):
    """A manager whose plan is made on `party` (the Wurmple plan: seed 1 draws it on this fixture), on SEVEN maps with a
    centre known from RUSTBORO; (manager, world, the first goal)."""
    mgr = c1_manager()
    mgr.bp_faults = faults
    world = world or seven_and_a_centre()
    first = decide_on(mgr, party, world)
    assert mgr.bp_record("ch7_brawly")["trainee"] == W, mgr.bp_record("ch7_brawly")
    return mgr, world, first


class FullPartnerTests(unittest.TestCase):
    """(round 4, V3-M1, the lead's E1) A HEAL ONLY WHEN IT CAN CHANGE THE DECISION. The partner line is judged on the
    partner as a heal leaves it (`bossprep.partner_line_full`, once per map); a map where it fails even healed is no
    switch-training map (`GoalManager.mode_on` "own"), and the raise picks another map under its cap where it passes
    (`_raise_choice`); the budget is checked BEFORE any rest (`_spend_if_over`). The verifier's H1-H6, as tests."""

    def test_h1_a_full_partner_unfit_on_route116_never_heals(self):
        """H1: Grovyle L17 46/46, the whole party full, the Wurmple plan: 5 decisions, never a heal; each a raise on
        PETALBURG_WOODS (the first map under the cap L12 where Grovyle, healed, is a partner: ROUTE116's Taillow L8 is
        not). FAULT `partner_full_unchecked` (round 3): heal on 5 of 5, each "not a safe partner against Taillow L8 on
        ROUTE116" (the loop, reproduced)."""
        mgr, world, first = planned_on(grovyle17())
        goals = [first] + [decide_on(mgr, grovyle17(), world) for _ in range(4)]
        self.assertEqual({(g.kind, g.map) for g in goals}, {("raise", "PETALBURG_WOODS")}, [g.reason for g in goals])
        mgr, world, first = planned_on(grovyle17(), F(partner_full_unchecked=True))
        goals = [first] + [decide_on(mgr, grovyle17(), world) for _ in range(4)]
        self.assertEqual({g.kind for g in goals}, {"heal"})
        self.assertTrue(all("not a safe partner against Taillow L8 on ROUTE116" in g.reason for g in goals))

    def test_h2_an_exceeded_budget_spends_before_any_rest(self):
        """H2: the same with the plan's frames over the budget: the plan is SPENT, with no heal for it. FAULTS
        `partner_full_unchecked` + `budget_after_rest` (round 3): heal, the plan still active (the verifier's H2)."""
        mgr, world, _ = planned_on(grovyle17())
        mgr.bp_record("ch7_brawly")["frames"] = 10 ** 7
        goal = decide_on(mgr, grovyle17(), world)
        self.assertNotIn(goal.kind, ("heal", "find_center", "raise"), goal.reason)
        self.assertEqual(mgr.bp_record("ch7_brawly")["status"], "spent")
        self.assertIn("frames", mgr.bp_record("ch7_brawly")["spent_why"])
        mgr, world, _ = planned_on(grovyle17(), F(partner_full_unchecked=True, budget_after_rest=True))
        mgr.bp_record("ch7_brawly")["frames"] = 10 ** 7
        self.assertEqual(decide_on(mgr, grovyle17(), world).kind, "heal")
        self.assertEqual(mgr.bp_record("ch7_brawly")["status"], "active")

    def test_an_exceeded_budget_while_worn_spends_the_plan(self):
        """Grovyle L21 at 32/57 is WORN on ROUTE116 (no partner against Nincada L7; healed it is one): within the budget the
        party rests (a heal that changes the decision: CONTROL). Over the budget the plan is spent and no heal is chosen
        for it. FAULT `budget_after_rest`: the heal first, the plan left active."""
        for frames, faults, kind, status in ((0, bp.NO_FAULTS, "heal", "active"), (10 ** 7, bp.NO_FAULTS, None, "spent"),
                                             (10 ** 7, F(budget_after_rest=True), "heal", "active")):
            mgr, world, _ = planned_on(party18(), faults)
            mgr.bp_record("ch7_brawly")["frames"] = frames
            goal = decide_on(mgr, party18(Grovyle=32), world)
            if kind is None:
                self.assertNotIn(goal.kind, ("heal", "find_center", "raise"), goal.reason)
            else:
                self.assertEqual(goal.kind, kind, (frames, faults, goal.reason))
            self.assertEqual(mgr.bp_record("ch7_brawly")["status"], status, (frames, faults))

    def test_no_grass_spends_before_any_rest(self):
        """No grass within reach (the world knows ROUTE104 with no grass) and the partner worn (Grovyle at 27/57): the
        plan is SPENT first ("no grass within reach for the raise"), so no heal for it. CONTROL (the grass known): the
        rest."""
        mgr, _, _ = planned_on(party18())
        goal = decide_on(mgr, party18(Grovyle=27), world_with("ROUTE104", current="ROUTE104"))
        self.assertNotIn(goal.kind, ("heal", "find_center"), goal.reason)
        self.assertEqual((mgr.bp_record("ch7_brawly")["status"], mgr.bp_record("ch7_brawly")["spent_why"]),
                         ("spent", "no grass within reach for the raise"))
        mgr, world, _ = planned_on(party18())
        self.assertIn(decide_on(mgr, party18(Grovyle=27), world).kind, ("heal", "find_center"))

    def test_the_raise_goal_checks_the_budget_too(self):
        """The raise goal itself still spends a plan over its budget (the backstop, and round 3's only check: FAULT
        `budget_after_rest` leaves it to `_raise_goal`): asked directly, no goal and the plan spent."""
        for faults in (bp.NO_FAULTS, F(budget_after_rest=True)):
            mgr, world, _ = planned_on(party18(), faults)
            mgr.bp_record("ch7_brawly")["battles"] = 160
            plan = mgr.boss_prep(look(party=party18()), at("ch6_briney_house")[1])
            with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
                self.assertIsNone(mgr._raise_goal(look(party=party18()), world, plan))
            self.assertEqual(mgr.bp_record("ch7_brawly")["status"], "spent", faults)

    def test_h3_control_a_fit_partner_raises_on_route116(self):
        """H3 (CONTROL): Grovyle L21 57/57: the raise on ROUTE116, switch-training ("mix": nothing said of own fights)."""
        mgr, world, first = planned_on(party18())
        self.assertEqual((first.kind, first.map), ("raise", "ROUTE116"))
        self.assertNotIn("OWN FIGHTS ONLY", first.reason)
        self.assertEqual(mgr.mode_on(look(party=party18()), "ROUTE116", W)[0], "mix")

    def test_the_healed_line_per_map(self):
        """Grovyle L17: healed, no partner on ROUTE116 (Taillow L8: 3 hits, Taillow's worst 12 a hit leaves 10/46), one on
        PETALBURG_WOODS and ROUTE104; at 20/46 it is still one HEALED (the heal is what the line asks). Judged ONCE per map
        and partner: a second ask calls `partner_fit` no more."""
        seen = look(party=grovyle17())
        fits, why = bp.partner_line_full(seen, W, "ROUTE116")
        self.assertFalse(fits)
        self.assertIn("Taillow L8: 3 of its hits (14 points each against about 29); Taillow's worst 12", why)
        self.assertEqual(bp.partner_line_full(seen, W, "PETALBURG_WOODS"), (True, ""))
        self.assertEqual(bp.partner_line_full(look(party=grovyle17(20)), W, "PETALBURG_WOODS"), (True, ""))
        self.assertIsNone(bp.partner_line_full(seen, G, "ROUTE116"))  # no partner: Grovyle is the strongest
        self.assertIsNone(bp.partner_line_full(seen, W, "NOWHERE"))
        bp._full_line.cache_clear()
        with mock.patch.object(bp, "partner_fit", wraps=bp.partner_fit) as asked:
            bp.partner_line_full(seen, W, "PETALBURG_WOODS")
            first = asked.call_count
            bp.partner_line_full(seen, W, "PETALBURG_WOODS")
            # the same partner worn, out of PP, with more EXP points: healed it is the same: no new judgement
            worn = grovyle17(20)
            worn[0] = replace(worn[0], experience=999, moves=tuple(replace(m, pp=0) for m in worn[0].moves))
            bp.partner_line_full(look(party=worn), W, "PETALBURG_WOODS")
            self.assertEqual((first, asked.call_count), (len(seasoned.land_slots("PETALBURG_WOODS")),) * 2)
            level_up = grovyle17()
            level_up[0] = replace(level_up[0], level=18)  # CONTROL: a new level is a new partner: judged again
            bp.partner_line_full(look(party=level_up), W, "PETALBURG_WOODS")
            self.assertGreater(asked.call_count, first)

    def test_no_rest_for_a_partner_a_heal_cannot_make_fit(self):
        """Grovyle L17 at 20/46: on ROUTE116 (unfit even healed) no rest; on PETALBURG_WOODS (fit once healed) the rest.
        FAULT `partner_full_unchecked`: the rest on ROUTE116 too (round 3: the heal loop's rest)."""
        seen = look(party=grovyle17(20))
        self.assertIsNone(bp.partner_worn(seen, W, bp.NO_FAULTS, "ROUTE116"))
        self.assertIn("under half its HP", bp.partner_worn(seen, W, bp.NO_FAULTS, "PETALBURG_WOODS"))
        self.assertIn("is not a safe partner against", bp.partner_worn(seen, W, F(partner_full_unchecked=True), "ROUTE116"))

    def test_a_worn_partner_rests_before_the_mix_map(self):
        """(E1 with E6) Grovyle L17 at 20/46: the next raise goes to PETALBURG_WOODS (mix), where it is worn: the party
        RESTS (the heal makes it fit there). The decision's rest line asks the map `_raise_goal` goes to, not ROUTE116."""
        mgr, world, _ = planned_on(grovyle17())
        goal = decide_on(mgr, grovyle17(20), world)
        self.assertEqual(goal.kind, "heal", goal.reason)
        self.assertIn("on PETALBURG_WOODS", goal.reason)
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
            self.assertEqual(mgr._raise_place(look(party=grovyle17(20)), world, mgr.bp_record("ch7_brawly")),
                             "PETALBURG_WOODS")

    def test_raise_mode_and_the_own_map(self):
        """A partner unfit on EVERY map under its cap (Seedot L10 [Bide, Harden], nothing it knows hurts: cap L5): the
        raise goes to the first map, ROUTE104, OWN FIGHTS ONLY. No partner (the Grovyle plan): "mix" (round 3)."""
        party = [summary(0, "Wurmple", 4, ("Tackle", "String Shot"), 18, pid=W),
                 summary(1, "Seedot", 10, ("Bide", "Harden"), 30, pid=PID["Seedot"])]
        mgr = c1_manager()
        world = seven_and_a_centre()
        record = bp.new_record()
        record.update(status="active", trainee=W, target=19, plan=f"raise:{W:08x}:19", boss="BRAWLY")
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
            choice = mgr._raise_choice(look(party=party), world, record)
        self.assertEqual(choice[:2], ("ROUTE104", "own"))
        self.assertIn("no partner on ROUTE104 even healed", choice[2])
        self.assertEqual(mgr.mode_on(look(party=party18()), "ROUTE116", G), ("mix", "no knock-out partner"))
        self.assertEqual(mgr.mode_on(look(party=grovyle17()), "ROUTE116", W)[0], "own")
        mgr.bp_faults = F(partner_full_unchecked=True)
        self.assertEqual(mgr.mode_on(look(party=grovyle17()), "ROUTE116", W)[0], "mix")  # FAULT: round 3

    def own_map_battle(self, raise_switch: bool, faults=None):
        """A raise battle against a Whismur L6 (Wurmple L4 cannot win it; Grovyle L21 57/57 is a partner against it)."""
        mind = raise_mind(faults)
        mind.raise_switch = raise_switch
        party = [member("Wurmple", 4, WURMPLE_MOVES, 18, 18, W, 0), grovyle_member(), poochyena_member()]
        return mind, battle_turn(mind, battle_mon("Wurmple", 4, WURMPLE_MOVES, 18, 18, pid=W), foe("Whismur", 6), party)

    def test_own_mode_has_no_switch_training(self):
        """An "own" map (`raise_switch` False): the trainee that cannot win RUNS (its own winnable fights only), said.
        CONTROL ("mix"): the switch to Grovyle. FAULT `own_map_switches`: the switch on the own map."""
        from ai_player.brain.battle import BattleFaults

        mind, decision = self.own_map_battle(True)
        self.assertEqual((decision.action, decision.switch_pid, mind.raise_modes), ("switch", G, ["switch"]))
        mind, decision = self.own_map_battle(False)
        self.assertEqual((decision.action, mind.raise_modes), ("run", ["run"]))
        self.assertIn("no switch-training on this map", decision.reason)
        mind, decision = self.own_map_battle(False, BattleFaults(own_map_switches=True))
        self.assertEqual(decision.action, "switch")

    def test_the_raise_session_takes_its_mode_from_the_map(self):
        """`GoalRunner._raise` sets the battle brain's `raise_switch` from `mode_on` on its map, and restores it after:
        Grovyle L17 on ROUTE116 (own) False, on PETALBURG_WOODS (mix) True."""
        from ai_player.gates.test_goals import RestTests

        for place, expected in (("ROUTE116", False), ("PETALBURG_WOODS", True)):
            mgr, _, _ = planned_on(grovyle17())
            nav = RestTests.navigator(RestTests(), [look(party=grovyle17()), look(party=grovyle17())])
            mind = BattleMind("Story", random.Random("1:battle"), "travel")
            runner = GoalRunner(nav.hands, nav, mgr, mind, lambda line: None)
            seen = []

            def fake_lead(hands, pid, why):
                yield
                return True

            def fake_roam(hands, nav_, steps, why):
                seen.append(mind.raise_switch)
                yield
                return "roamed: 10 training steps"

            nav.world.here = lambda place=place: types.SimpleNamespace(const=place)
            with mock.patch.object(goals_module, "lead_with", fake_lead), \
                    mock.patch.object(goals_module, "roam_train", fake_roam):
                goals_module_drive(runner._raise(Goal("raise", "r", "ch7_brawly", map=place, steps=10,
                                                      key=f"raise:{place}"), lambda s: False))
            self.assertEqual((seen, mind.raise_switch), ([expected], True), place)


class LastResortTests(unittest.TestCase):
    """(round 4, V3-M2, the lead's E2) When the protected trainee must be protected and NO member is sure to win: (a) it
    fights if it wins still standing (`fight_safe` keep 0, its own sure win); (b) in a wild battle it runs; (c) only then a
    member that cannot win is sent (any that can come in). The same order wherever round 3 sent "any member that can come
    in": the guard's turn 1, its later-turn rescue, and the raise's rescue after a refused run ((b) spent)."""

    def party6413(self):
        S, SH, C = PID["Seedot"], PID["Shroomish"], PID["Cascoon"]
        return [member("Grovyle", 25, GROVYLE_MOVES, 21, 68, G, 0), member("Poochyena", 6, ["Tackle", "Howl"], 21, 21, P, 1),
                member("Wurmple", 3, WURMPLE_MOVES, 16, 16, W, 2), member("Seedot", 3, ["Bide", "Harden"], 16, 16, S, 3),
                member("Shroomish", 5, ["Absorb", "Tackle"], 21, 21, SH, 4), member("Cascoon", 5, ["Harden"], 20, 20, C, 5)]

    def test_the_6413_fixture_fights(self):
        """The live 6413 battle 106: Grovyle L25 at 21/68 (31%, under its floor) against a wild Taillow L6, the live party:
        no member is sure to win (Poochyena L6: 8 hits), the trainee wins in one hit keeping 12/68: it FIGHTS, no switch.
        FAULT `fallback_first` (round 3's order): the switch to Poochyena, "no member is sure to win it"."""
        from ai_player.brain.battle import BattleFaults

        mind = guard_mind()
        mind.guard = G
        decision = battle_turn(mind, battle_mon("Grovyle", 25, GROVYLE_MOVES, 21, 68, pid=G), foe("Taillow", 6),
                               self.party6413())
        self.assertEqual((decision.action, mind.memory.guard_mode), ("fight", "fight"))
        self.assertIn("it wins it itself, still standing", decision.reason)
        mind = guard_mind(BattleFaults(fallback_first=True))
        mind.guard = G
        decision = battle_turn(mind, battle_mon("Grovyle", 25, GROVYLE_MOVES, 21, 68, pid=G), foe("Taillow", 6),
                               self.party6413())
        self.assertEqual((decision.action, decision.switch_pid), ("switch", P))
        self.assertIn("no member is sure to win it", decision.reason)

    def wurmple_turn(self, grovyle_hp=57, kind="wild", faults=None, hp=3):
        mind = guard_mind(faults)
        party = [member("Wurmple", 5, WURMPLE_MOVES, hp, 21, W, 0), grovyle_member(grovyle_hp), poochyena_member()]
        own = battle_mon("Wurmple", 5, WURMPLE_MOVES, hp, 21, pid=W)
        return mind, party, own, battle_turn(mind, own, foe("Poochyena", 6), party, kind=kind)

    def test_control_a_member_that_wins_still_switches(self):
        mind, _, _, decision = self.wurmple_turn()
        self.assertEqual((decision.action, decision.switch_pid, mind.memory.guard_mode), ("switch", G, "switch"))

    def test_with_none_that_wins_a_wild_battle_runs(self):
        """Wurmple L5 at 3/21 against a wild Poochyena L6, Grovyle fainted, Poochyena L6 cannot win: (a) no (8 hits), (b)
        the RUN. A turn later (the run refused, (b) spent): (c) the switch to Poochyena. FAULT `fallback_first`: the switch
        on turn 1 (round 3)."""
        from ai_player.brain.battle import BattleFaults

        mind, party, own, decision = self.wurmple_turn(grovyle_hp=0)
        self.assertEqual((decision.action, mind.memory.guard_mode), ("run", "run"))
        again = battle_turn(mind, own, foe("Poochyena", 6), party, begin=False)
        self.assertEqual((again.action, again.switch_pid, mind.memory.guard_mode), ("switch", P, "rescue"))
        _, _, _, decision = self.wurmple_turn(grovyle_hp=0, faults=BattleFaults(fallback_first=True))
        self.assertEqual((decision.action, decision.switch_pid), ("switch", P))

    def test_a_trainer_battle_goes_to_the_member_that_can_come_in(self):
        """The same in a TRAINER battle: no run, so (c): the switch to Poochyena (under its floor)."""
        mind, _, _, decision = self.wurmple_turn(grovyle_hp=0, kind="trainer")
        self.assertEqual((decision.action, decision.switch_pid), ("switch", P))

    def test_the_floor_boundary(self):
        """(the verifier's REDUNDANT `v_guard_floor_inclusive`) A trainer battle, no member that wins: at 7/21, exactly a
        third, the trainee is NOT under its floor, so no member that cannot win is sent ("none": the ordinary rules, a
        fight); at 6/21 it is, (c): the switch to Poochyena."""
        mind, _, _, decision = self.wurmple_turn(grovyle_hp=0, kind="trainer", hp=7)
        self.assertEqual((decision.action, mind.memory.guard_mode), ("fight", "none"))
        mind, _, _, decision = self.wurmple_turn(grovyle_hp=0, kind="trainer", hp=6)
        self.assertEqual((decision.action, decision.switch_pid), ("switch", P))

    def test_a_later_turn_its_own_sure_win(self):
        """An own fight (Dustox L12 full against a wild Whismur L6) at 10/38 a turn later, the Whismur at 10 of 48 pixels,
        Grovyle fainted, Poochyena at 2/21 (it cannot win): (a) Dustox wins it itself in one hit (5/38 left): it fights.
        FAULT `fallback_first`: the switch to Poochyena (round 3: any member that can come in)."""
        from ai_player.brain.battle import BattleFaults

        for faults, expected in ((None, ("fight", None)), (BattleFaults(fallback_first=True), ("switch", P))):
            mind = guard_mind(faults)
            party = [member("Dustox", 12, DUSTOX_MOVES, 38, 38, W, 0), grovyle_member(0), poochyena_member(2)]
            battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 38, 38, pid=W), foe("Whismur", 6), party)
            party = [member("Dustox", 12, DUSTOX_MOVES, 10, 38, W, 0), grovyle_member(0), poochyena_member(2)]
            decision = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 10, 38, pid=W), foe("Whismur", 6, bar=10),
                                   party, begin=False)
            self.assertEqual((decision.action, decision.switch_pid), expected, faults)

    def raise_turn(self, faults=None, grovyle_hp=0, pooch_hp=2, bar=10):
        mind = raise_mind(faults)
        party = [member("Dustox", 12, DUSTOX_MOVES, 10, 38, W, 0), grovyle_member(grovyle_hp), poochyena_member(pooch_hp)]
        return mind, battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 10, 38, pid=W), foe("Whismur", 6, bar=bar),
                                 party)

    def test_a_raise_battle_under_its_floor_its_own_sure_win(self):
        """A raise battle met with the trainee under its floor (Dustox L12 at 10/38, the Whismur L6 at 10 of 48 pixels),
        nobody that wins (Grovyle fainted, Poochyena at 2/21): (a) it fights, counted an own fight. CONTROL: Poochyena
        full can win it: the rescue to it. FAULT `fallback_first`: the rescue to Poochyena at 2/21 (round 3)."""
        from ai_player.brain.battle import BattleFaults

        mind, decision = self.raise_turn()
        self.assertEqual((decision.action, mind.raise_modes), ("fight", ["own"]))
        mind, decision = self.raise_turn(pooch_hp=21)
        self.assertEqual((decision.action, decision.switch_pid, mind.raise_modes), ("switch", P, ["rescue"]))
        mind, decision = self.raise_turn(BattleFaults(fallback_first=True))
        self.assertEqual((decision.action, decision.switch_pid, mind.raise_modes), ("switch", P, ["rescue"]))

    def test_an_own_raise_fight_gone_badly_with_no_winner(self):
        """An own raise fight (Dustox L12 full against a Whismur L6) at 12/38 a turn later (under its floor, above the
        Story's run line of 30%, so the ordinary rules would fight on), the Whismur at 40 of 48 pixels, Grovyle fainted
        and Poochyena at 2/21 (neither wins), the trainee cannot win it itself: (b) the RUN; that run refused, (c): the
        rescue to Poochyena. That rescue is made by the RUN branch (the own branch's run set the battle's mode to "run",
        so the turn after is the run branch's last resort: its reason says "the run was refused"); the own branch's own
        rescue is reached only by a fight that became an own fight AFTER a refused run: the next test. CONTROL: the
        Whismur at 10 pixels, (a): it fights on."""
        for bar, expected in ((40, ("run", "switch")), (10, ("fight", "fight"))):
            mind = raise_mind()
            party = [member("Dustox", 12, DUSTOX_MOVES, 38, 38, W, 0), grovyle_member(0), poochyena_member(2)]
            first = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 38, 38, pid=W), foe("Whismur", 6), party)
            self.assertEqual((first.action, mind.raise_modes), ("fight", ["own"]))
            party = [member("Dustox", 12, DUSTOX_MOVES, 12, 38, W, 0), grovyle_member(0), poochyena_member(2)]
            own = battle_mon("Dustox", 12, DUSTOX_MOVES, 12, 38, pid=W)
            second = battle_turn(mind, own, foe("Whismur", 6, bar=bar), party, begin=False)
            third = battle_turn(mind, own, foe("Whismur", 6, bar=bar), party, begin=False)
            self.assertEqual((second.action, third.action), expected, bar)
            if bar == 40:
                self.assertEqual((third.switch_pid, mind.raise_modes), (P, ["rescue"]))
                self.assertIn("rescue (the run was refused)", third.reason)

    def test_an_own_fight_begun_after_a_refused_run_gone_badly(self):
        """(round 4, mutant run 1's missed prediction `own_fallback_unmade`) The OWN branch's rescue after a refused run:
        Dustox L12 at 20/38 against a wild Whismur L6, Grovyle fainted and Poochyena at 2/21 (no partner, and not a safe
        own fight at its floor): turn 1 the RUN. The run refused, turn 2: it wins it itself, still standing ((a)): an own
        fight, with one run spent. Turn 3 at 5/38 (under its floor), the Whismur at 40 of 48 pixels: it no longer wins
        itself, nobody wins, (b) is spent: (c) the rescue to Poochyena, made by the own branch ("an own fight went badly,
        and a run was refused"). CONTROL: turn 3 at 12/38, the Whismur at 10 pixels: (a), it fights on."""
        for hp, bar, expected in ((5, 40, ("switch", P)), (12, 10, ("fight", None))):
            mind = raise_mind()
            party = [member("Dustox", 12, DUSTOX_MOVES, 20, 38, W, 0), grovyle_member(0), poochyena_member(2)]
            own = battle_mon("Dustox", 12, DUSTOX_MOVES, 20, 38, pid=W)
            first = battle_turn(mind, own, foe("Whismur", 6), party)
            self.assertEqual((first.action, mind.memory.raise_mode, mind.memory.runs), ("run", "run", 1))
            second = battle_turn(mind, own, foe("Whismur", 6), party, begin=False)
            self.assertEqual((second.action, mind.memory.raise_mode, mind.memory.runs), ("fight", "own", 1))
            party = [member("Dustox", 12, DUSTOX_MOVES, hp, 38, W, 0), grovyle_member(0), poochyena_member(2)]
            third = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, hp, 38, pid=W), foe("Whismur", 6, bar=bar),
                                party, begin=False)
            self.assertEqual((third.action, third.switch_pid), expected, (hp, bar))
            if hp == 5:
                self.assertIn("rescue (an own fight went badly, and a run was refused)", third.reason)
                self.assertEqual(mind.raise_modes, ["rescue"])
            else:
                self.assertIn("it wins it itself, still standing", third.reason)

    def test_a_refused_raise_run_its_own_sure_win_first(self):
        """(R3n's fixture) Cascoon L7 runs on turn 1 (no partner), the run is refused, the trainee at 3/26: nobody wins
        (Grovyle fainted, Poochyena L6 8 hits), it cannot win itself: (c) the rescue to Poochyena ((b) spent). CONTROL:
        Grovyle at 32/57 can win it: the rescue to Grovyle (R3n)."""
        rescue = RescueTests()
        mind, first, second = rescue.battle(later_hp=3, grovyle_hp=0)
        self.assertEqual((first.action, second.action, second.switch_pid, mind.raise_modes),
                         ("run", "switch", P, ["rescue"]))
        mind, _, second = rescue.battle(later_hp=3)
        self.assertEqual((second.action, second.switch_pid), ("switch", G))


class TrainerGuardTests(unittest.TestCase):
    """(round 4, V3-m1, the lead's E3) The turn-1 protection asks the SAME question in a trainer battle as in a wild one:
    under its floor, or the fight not safe for it against the foe on the field, from static knowledge only (`fight_safe`:
    the foe's species' level-up moves at its level, and the moves seen). A RAISE goal's trainer battles get the guard's
    rules too (`BattleMind._guard_whom`)."""

    def wurmple(self, hp=21):
        return member("Wurmple", 5, ["Tackle", "String Shot", "Poison Sting"], hp, 21, W, 0)

    def own(self, hp=21):
        return battle_mon("Wurmple", 5, ["Tackle", "String Shot", "Poison Sting"], hp, 21, pid=W)

    def test_g6_a_trainer_battle_outside_a_raise_switches(self):
        """The verifier's G6: Wurmple L5 21/21 against a trainer's Zigzagoon L12 (its worst hit 25 against the trainee's
        21): the switch to Grovyle, judged from the species' moves at L12 (nothing read of the live foe). FAULT
        `guard_wild_only`: it fights (round 3)."""
        from ai_player.brain.battle import BattleFaults

        party = [self.wurmple(), grovyle_member(), poochyena_member()]
        decision = battle_turn(guard_mind(), self.own(), foe("Zigzagoon", 12), party, kind="trainer")
        self.assertEqual((decision.action, decision.switch_pid), ("switch", G))
        why = bp.fight_safe(bp.member_now(battle_look([self.own()], [foe("Zigzagoon", 12)], party=party, kind="trainer"),
                                          W), "Zigzagoon", 12, 1.0, 21)[1]
        self.assertIn(why, decision.reason)  # the judgement is fight_safe's own: wild_moves at the foe's level
        decision = battle_turn(guard_mind(BattleFaults(guard_wild_only=True)), self.own(), foe("Zigzagoon", 12), party,
                               kind="trainer")
        self.assertEqual(decision.action, "fight")

    def test_control_a_trainer_battle_it_wins_safely(self):
        """CONTROL: Dustox L12 full against a trainer's Whismur L6: it wins safely: no switch ("own"), outside a raise and
        inside one."""
        party = [member("Dustox", 12, DUSTOX_MOVES, 38, 38, W, 0), grovyle_member(), poochyena_member()]
        for mind in (guard_mind(), raise_mind()):
            decision = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 38, 38, pid=W), foe("Whismur", 6), party,
                                   kind="trainer")
            self.assertEqual((decision.action, mind.memory.guard_mode), ("fight", "own"), mind.purpose)

    def test_g8_a_raise_goals_trainer_battle(self):
        """The verifier's G8: during a RAISE goal (purpose "raise", trainee W), the same trainer battle: the switch to
        Grovyle. FAULT `guard_not_in_raise`: it fights (round 3: the raise's turn is wild only, `_switch` off)."""
        from ai_player.brain.battle import BattleFaults

        party = [self.wurmple(), grovyle_member(), poochyena_member()]
        mind = raise_mind()
        decision = battle_turn(mind, self.own(), foe("Zigzagoon", 12), party, kind="trainer")
        self.assertEqual((decision.action, decision.switch_pid, mind.raise_modes), ("switch", G, []))
        decision = battle_turn(raise_mind(BattleFaults(guard_not_in_raise=True)), self.own(), foe("Zigzagoon", 12), party,
                               kind="trainer")
        self.assertEqual(decision.action, "fight")

    def test_g9_a_raise_goals_trainer_battle_later_turn(self):
        """The verifier's G9: in a raise goal's trainer battle that began "own" (Dustox L12 full against a trainer's Whismur
        L6), a later turn at 10/38: the rescue to Grovyle. FAULT `guard_not_in_raise`: it fights on (round 3)."""
        from ai_player.brain.battle import BattleFaults

        for faults, expected in ((None, "switch"), (BattleFaults(guard_not_in_raise=True), "fight")):
            mind = raise_mind(faults)
            party = [member("Dustox", 12, DUSTOX_MOVES, 38, 38, W, 0), grovyle_member(), poochyena_member()]
            battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 38, 38, pid=W), foe("Whismur", 6), party,
                        kind="trainer")
            party = [member("Dustox", 12, DUSTOX_MOVES, 10, 38, W, 0), grovyle_member(), poochyena_member()]
            decision = battle_turn(mind, battle_mon("Dustox", 12, DUSTOX_MOVES, 10, 38, pid=W), foe("Whismur", 6, bar=40),
                                   party, kind="trainer", begin=False)
            self.assertEqual(decision.action, expected, faults)

    def test_a_wild_raise_battle_is_still_the_raises(self):
        """CONTROL: in a WILD raise battle the guard stays out (`_raise_turn` decides: switch-training)."""
        mind = raise_mind()
        party = [self.wurmple(), grovyle_member(), poochyena_member()]
        decision = battle_turn(mind, self.own(), foe("Zigzagoon", 5), party)
        self.assertIsNone(mind.memory.guard_mode)
        self.assertEqual((decision.action, mind.raise_modes), ("switch", ["switch"]))


class SeamTests(unittest.TestCase):
    """(round 4, V3-m2, the lead's E4) The guard and the purpose RESET at each goal's end (`GoalRunner.between_goals`): a
    battle between goals takes its guard from the PLAN's state (the active plan's trainee whenever no raise goal runs), and
    a raise's purpose "raise" ends with it."""

    def after(self, goal, faults=bp.NO_FAULTS, during=None):
        from ai_player.gates.test_goals import RestTests

        mgr, _, _ = planned(faults=faults)
        nav = RestTests.navigator(RestTests(), [look(party=party18()), look(party=party18())])
        nav.world.here = lambda: types.SimpleNamespace(const="ROUTE116")
        mind = BattleMind("Story", random.Random("1:battle"), "travel")
        runner = GoalRunner(nav.hands, nav, mgr, mind, lambda line: None)

        def fake_lead(hands, pid, why):
            yield
            return True

        def fake_roam(hands, nav_, steps, why):
            yield
            return "roamed: 10 training steps"

        def fake_heal(goal_):
            if during is not None:
                during(mgr)
            yield
            return "healed"

        def fake_talk(goal_, milestone_, index_, current_):
            yield
            return True, "talked"

        runner._heal = fake_heal
        milestone, index = at("ch6_briney_house")
        with mock.patch.object(goals_module, "lead_with", fake_lead), mock.patch.object(goals_module, "roam_train", fake_roam):
            if goal.kind == "talk":
                real = runner._pursue
                runner._pursue = fake_talk
                goals_module_drive(runner.pursue(goal, milestone, index, lambda s: index))
                runner._pursue = real
            else:
                goals_module_drive(runner.pursue(goal, milestone, index, lambda s: index))
        party = [member("Wurmple", 5, WURMPLE_MOVES, 3, 21, W, 0), grovyle_member(), poochyena_member()]
        decision = battle_turn(mind, battle_mon("Wurmple", 5, WURMPLE_MOVES, 3, 21, pid=W), foe("Zigzagoon", 5), party,
                               kind="trainer")
        return mind, decision

    RAISE = Goal("raise", "r", "ch7_brawly", map="ROUTE116", steps=10, key="raise:ROUTE116")
    HEAL = Goal("heal", "h", "ch6_briney_house", key="heal")

    def test_a_scene_battle_right_after_a_raise_goal(self):
        """After a raise goal (the plan active): purpose "travel", no trainee, the guard the plan's trainee: a trainer's
        battle then, the trainee at 3/21 leading: the switch to Grovyle. FAULT `seam_kept` (round 3): purpose "raise", no
        guard: it fights on at 3/21."""
        mind, decision = self.after(self.RAISE)
        self.assertEqual((mind.purpose, mind.trainee, mind.guard), ("travel", None, W))
        self.assertEqual((decision.action, decision.switch_pid), ("switch", G))
        mind, decision = self.after(self.RAISE, F(seam_kept=True))
        self.assertEqual((mind.purpose, mind.guard, decision.action), ("raise", None, "fight"))

    def test_a_scene_battle_right_after_a_heal_goal(self):
        """After a heal goal, the plan still active: guarded (the switch). CONTROL: the plan spent during the heal: the
        guard follows the PLAN's state, not the goal's: none (the ordinary rules: it fights). FAULT `seam_kept`: the heal's
        guard left on (the switch)."""
        mind, decision = self.after(self.HEAL)
        self.assertEqual((mind.guard, decision.action, decision.switch_pid), (W, "switch", G))

        def spent(mgr):
            mgr.bp_record("ch7_brawly")["status"] = "spent"

        mind, decision = self.after(self.HEAL, during=spent)
        self.assertEqual((mind.guard, mind.say, decision.action), (None, None, "fight"))
        mind, decision = self.after(self.HEAL, F(seam_kept=True), during=spent)
        self.assertEqual((mind.guard, decision.action), (W, "switch"))

    def test_after_the_boss_fight_the_guard_stays_off(self):
        """The boss fight's own talk (`talk:brawly` in its milestone) is left out, and so is a battle it hands back: after
        it, no guard. CONTROL: after another talk in that milestone, the plan's trainee."""
        mind, _ = self.after(Goal("talk", "BRAWLY", "ch7_brawly", look="brawly", key="talk:brawly"))
        self.assertIsNone(mind.guard)
        mind, _ = self.after(Goal("talk", "a trainer", "ch7_brawly", look="gym_guide", key="talk:gym_guide#2"))
        self.assertEqual(mind.guard, W)

    def test_chapter_5_is_unchanged(self):
        """No plan (chapters 1-5): after any goal the guard and its line stay off, and a talk's purpose "train" (a story
        battle a talk hands back is fought) is kept."""
        from ai_player.gates.test_goals import RestTests

        mgr = c1_manager()
        nav = RestTests.navigator(RestTests(), [look(party=party18())])
        mind = BattleMind("Story", random.Random("1:battle"), "travel")
        runner = GoalRunner(nav.hands, nav, mgr, mind, lambda line: None)

        def fake(goal_, milestone_, index_, current_):
            mind.purpose = "train"
            yield
            return True, "talked"

        runner._pursue = fake
        milestone, index = at("ch5_rival_meet")
        goals_module_drive(runner.pursue(Goal("talk", "t", milestone.id, look="x", key="talk:x"), milestone, index,
                                         lambda s: index))
        self.assertEqual((mind.purpose, mind.guard, mind.say, mind.trainee), ("train", None, None, None))


class PPTests(unittest.TestCase):
    """(round 4, V3-m3, the lead's E5) The raise counts PP, which the player sees: a move at 0 PP is not a move it can use
    (`fight_safe`); the raise session ends, and the party heals, when every move of the trainee that hurts is out of PP."""

    def grovyle(self, pp=0, only=None, hp=68):
        return replace(member("Grovyle", 25, GROVYLE_MOVES, hp, 68, G, 0),
                       moves=tuple(slot(m, pp if only is None or m == only else 20) for m in GROVYLE_MOVES))

    def test_fight_safe_counts_pp(self):
        """Grovyle L25 full against a Taillow L6: every move at 0 PP: not safe, said; one move out (Absorb): still safe by
        the others (CONTROL); full PP: safe. FAULT `pp_ignored`: safe at 0 PP (round 3)."""
        def safe(mon, faults=bp.NO_FAULTS):
            return bp.fight_safe(bp.member_now(look(party=[mon]), G), "Taillow", 6, 1.0, 68, faults=faults)

        self.assertEqual(safe(self.grovyle())[0], False)
        self.assertIn("no PP left: Pound, Pursuit, Absorb, Quick Attack", safe(self.grovyle())[1])
        self.assertTrue(safe(self.grovyle(only="Absorb"))[0])
        self.assertTrue(safe(self.grovyle(pp=20))[0])
        self.assertTrue(safe(self.grovyle(), F(pp_ignored=True))[0])

    def test_out_of_pp(self):
        seen = look(party=[self.grovyle(), self.grovyle(pp=20, hp=60)])
        self.assertTrue(bp.out_of_pp(bp.member_now(seen, G)))
        self.assertFalse(bp.out_of_pp(bp.member_now(look(party=[self.grovyle(only="Absorb")]), G)))  # 3 moves left
        cocoon = member("Cascoon", 5, ["Harden"], 20, 20, W, 0)
        cocoon = replace(cocoon, moves=(slot("Harden", 0),))
        self.assertFalse(bp.out_of_pp(bp.member_now(look(party=[cocoon]), W)))  # no move that hurts: PP cannot help
        self.assertFalse(bp.out_of_pp(None))
        self.assertFalse(bp.out_of_pp(bp.Member(G, "Grovyle", 25, 68, 68, tuple(GROVYLE_MOVES))))  # PP unknown

    def test_the_raise_session_ends_out_of_pp(self):
        """The raise roam's rest after a battle (`trainee_rest`, the raise's `roam_hooks`): the trainee out of PP stops it.
        CONTROL: with PP, no stop. FAULT `pp_ignored`: no stop."""
        party = [self.grovyle(), member("Poochyena", 6, ["Tackle", "Howl"], 21, 21, P, 1)]
        heal_below = ERRANDS["Story"].heal_below
        self.assertIn("has no PP left in any move that hurts", bp.trainee_rest(look(party=party), G, heal_below, "Story"))
        self.assertIsNone(bp.trainee_rest(look(party=[self.grovyle(pp=20), party[1]]), G, heal_below, "Story"))
        self.assertIsNone(bp.trainee_rest(look(party=party), G, heal_below, "Story", F(pp_ignored=True)))
        from ai_player.gates.test_goals import RestTests

        nav = RestTests.navigator(RestTests(), [look(party=party)])
        runner = GoalRunner(nav.hands, nav, c1_manager(), None, lambda line: None)
        runner.roam_hooks(trainee=G, after_battle=lambda observation: None, raise_map="ROUTE116")
        self.assertIn("no PP left", nav.battle_rest(look(party=party)))

    def grovyle_plan(self, faults=bp.NO_FAULTS):
        """The GROVYLE plan (the trainee is the strongest: no partner), active, on SEVEN maps with a centre."""
        mgr = c1_manager()
        mgr.bp_faults = faults
        world = seven_and_a_centre()
        decide_on(mgr, party18(), world)
        record = mgr.bp_record("ch7_brawly")
        record.update(trainee=G, target=30, plan=f"raise:{G:08x}:30")
        return mgr, world

    def c1_out_of_pp(self, pp=0):
        out = party18()
        out[0] = replace(out[0], moves=tuple(slot(m, pp) for m in GROVYLE_MOVES))
        return out

    def test_the_party_heals_out_of_pp(self):
        """The Grovyle plan, its trainee at full HP and out of PP: a HEAL (a centre restores PP), said; never a Potion
        (one restores no PP), even with the centre far and Potions in the bag. CONTROL: with PP, the raise. FAULT
        `pp_ignored`: the raise (round 3: it fought on with Struggle)."""
        mgr, world = self.grovyle_plan()
        goal = decide_on(mgr, self.c1_out_of_pp(), world)
        self.assertEqual(goal.kind, "heal", goal.reason)
        self.assertIn("out of PP", goal.reason)
        mgr, world = self.grovyle_plan()
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: 5):
            far = decide2(mgr, self.c1_out_of_pp(), world, healing=(("Potion", 3),))
        self.assertEqual(far.kind, "heal")
        mgr, world = self.grovyle_plan()
        self.assertEqual(decide_on(mgr, self.c1_out_of_pp(20), world).kind, "raise")
        mgr, world = self.grovyle_plan(F(pp_ignored=True))
        self.assertEqual(decide_on(mgr, self.c1_out_of_pp(), world).kind, "raise")

    def test_the_own_fight_judgement_counts_pp(self):
        """A raise battle of the Grovyle plan against a Whismur L6: with PP, its own fight ("own"); out of PP, no own fight
        (nobody else is a partner: it runs). FAULT `pp_ignored`: "own" (round 3: it fought with Struggle)."""
        def first(pp, bp_faults=None):
            mind = raise_mind(bp_faults=bp_faults)
            mind.trainee = G
            party = [replace(member("Grovyle", 25, GROVYLE_MOVES, 68, 68, G, 0),
                             moves=tuple(slot(m, pp) for m in GROVYLE_MOVES)), poochyena_member()]
            own = battle_mon("Grovyle", 25, GROVYLE_MOVES, 68, 68, pid=G, pps=[pp] * 4)
            decision = battle_turn(mind, own, foe("Whismur", 6), party)
            return decision.action, mind.raise_modes

        self.assertEqual(first(20), ("fight", ["own"]))
        self.assertEqual(first(0), ("run", ["run"]))
        self.assertEqual(first(0, F(pp_ignored=True))[1], ["own"])

    def test_a_partner_out_of_pp_rests_the_raise(self):
        """Grovyle L21 57/57 with every move at 0 PP is no partner on ROUTE116 now (nothing it can still use hurts), but one
        once healed: the raise rests (a heal at a centre restores its PP)."""
        g0 = replace(grovyle_member(57), moves=tuple(slot(m, 0) for m in GROVYLE_MOVES))
        seen = look(party=[member("Wurmple", 4, WURMPLE_MOVES, 18, 18, W, 0), g0])
        self.assertIn("no PP left", bp.partner_worn(seen, W, bp.NO_FAULTS, "ROUTE116"))
        self.assertEqual(bp.partner_line_full(seen, W, "ROUTE116"), (True, ""))


class CoverageTests(unittest.TestCase):
    """(round 4, V3-m4, the lead's E6) The round-3 rules the verifier's mutants broke with every test green: `_raise_place`
    against a map put aside, the guard's one switch, the rescue's healthiest-first order and its sent-this-turn skip, and
    (cheap) the guard's line without a guard, its faults' hand-off, the boss fight's key, a double battle."""

    def test_the_rest_line_asks_the_map_the_raise_goes_to(self):
        """ROUTE116 put aside (two failures): the next raise goes to PETALBURG_WOODS, and the decision's rest line asks
        PETALBURG_WOODS too (`_raise_place` and `_raise_goal` read ONE rule, `_raise_choice`): Grovyle at 32/57, worn on
        ROUTE116 but a partner on PETALBURG_WOODS, gives the raise there, no heal. CONTROL: nothing put aside: the rest."""
        for aside, kind, where in ((False, "heal", None), (True, "raise", "PETALBURG_WOODS")):
            mgr, world, first = planned_on(party18())
            self.assertEqual(first.map, "ROUTE116")
            if aside:
                mgr.outcome(first, False)
                mgr.outcome(first, False)
            goal = decide_on(mgr, party18(Grovyle=32), world)
            self.assertEqual(goal.kind, kind, (aside, goal.reason))
            if where is not None:
                self.assertEqual(goal.map, where)
                with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
                    self.assertEqual(mgr._raise_place(look(party=party18(Grovyle=32)), world,
                                                      mgr.bp_record("ch7_brawly")), where)

    def test_the_guard_switches_once_a_battle(self):
        """(the verifier's REDUNDANT `v_guard_switch_unbounded`) After the protective switch, the trainee back on the field
        under its floor (the only one left, sent in by force): no second protective switch."""
        mind = guard_mind()
        party = [member("Wurmple", 5, WURMPLE_MOVES, 3, 21, W, 0), grovyle_member(), poochyena_member()]
        own = battle_mon("Wurmple", 5, WURMPLE_MOVES, 3, 21, pid=W)
        self.assertEqual(battle_turn(mind, own, foe("Poochyena", 6), party, kind="trainer").action, "switch")
        party = [member("Wurmple", 5, WURMPLE_MOVES, 3, 21, W, 0), grovyle_member(0), poochyena_member()]
        again = battle_turn(mind, own, foe("Poochyena", 6), party, kind="trainer", begin=False)
        self.assertNotEqual(again.action, "switch", again.reason)
        self.assertEqual(mind.memory.guard_mode, "switch")

    def test_the_rescue_takes_the_healthiest_winner(self):
        """(the verifier's REDUNDANT `v_rescue_matchup_first`) Two members can win against a Poochyena L6: Grovyle at
        57/57 and Combusken at 30/60 (the better match, Double Kick against a Dark type): the HEALTHIEST, Grovyle. CONTROL:
        Grovyle at 30/57, Combusken 60/60: Combusken."""
        for g_hp, c_hp, expected in ((57, 30, G), (30, 60, CB)):
            party = [member("Wurmple", 5, WURMPLE_MOVES, 3, 21, W, 0), member("Grovyle", 21, GROVYLE_MOVES, g_hp, 57, G, 1),
                     member("Combusken", 20, COMBUSKEN_MOVES, c_hp, 60, CB, 2)]
            decision = battle_turn(guard_mind(), battle_mon("Wurmple", 5, WURMPLE_MOVES, 3, 21, pid=W), foe("Poochyena", 6),
                                   party)
            self.assertEqual((decision.action, decision.switch_pid), ("switch", expected), (g_hp, c_hp))

    def test_the_rescue_skips_a_member_sent_this_turn(self):
        """(the verifier's REDUNDANT `v_rescue_sent_since`) Grovyle was sent in this turn (not yet seen on the field): the
        rescue names Combusken, the other that can win; with Grovyle not sent, Grovyle (the healthiest)."""
        party = [member("Wurmple", 5, WURMPLE_MOVES, 3, 21, W, 0), member("Grovyle", 21, GROVYLE_MOVES, 57, 57, G, 1),
                 member("Combusken", 20, COMBUSKEN_MOVES, 30, 60, CB, 2)]
        seen = battle_look([battle_mon("Wurmple", 5, WURMPLE_MOVES, 3, 21, pid=W)], [foe("Poochyena", 6)], party=party)
        mind = guard_mind()
        self.assertEqual(mind.rescue_member(seen, foe("Poochyena", 6), desperate=False)[0].pid, G)
        mind.sent(G)
        self.assertEqual(mind.rescue_member(seen, foe("Poochyena", 6), desperate=False)[0].pid, CB)

    def test_the_guards_line_and_faults_only_with_a_guard(self):
        """(the verifier's REDUNDANT `v_say_always`, `v_no_bp_faults_for_guard`) A guarded goal hands the battle brain the
        guard's line and the boss preparation's faults; a goal with no active plan, no line."""
        runner_tests = GuardRunnerTests()
        seen, mgr, _ = runner_tests.pursued()
        self.assertIsNotNone(seen["say"])
        self.assertIs(seen["bp_faults"], mgr.bp_faults)
        seen, _, _ = runner_tests.pursued(status="spent")
        self.assertIsNone(seen["say"])

    def test_the_boss_fights_own_key(self):
        """(the verifier's REDUNDANT `v_boss_fight_any_talk`) Only the story's own talk to the leader (`talk:<look>`) is the
        boss fight: another talk in the boss's milestone (its key not `talk:<look>`) is guarded."""
        _, _, runner = GuardRunnerTests().pursued()
        other = Goal("talk", "a gym trainer", "ch7_brawly", look="gym_guide", key="talk:gym_guide#2")
        self.assertEqual(runner._guard_for(other), W)
        self.assertIsNone(runner._guard_for(Goal("talk", "BRAWLY", "ch7_brawly", look="brawly", key="talk:brawly")))

    def test_no_guard_in_a_double_battle(self):
        """(the verifier's REDUNDANT `v_guard_doubles`) A double battle with one foe in view, the guarded trainee at 3/21:
        the guard does not act (the battle brain does not switch in a double battle)."""
        party = [member("Wurmple", 5, WURMPLE_MOVES, 3, 21, W, 0), grovyle_member(), poochyena_member()]
        seen = battle_look([battle_mon("Wurmple", 5, WURMPLE_MOVES, 3, 21, pid=W)], [foe("Poochyena", 6)], party=party,
                           double=True, kind="trainer")
        mind = guard_mind()
        mind.begin(seen)
        self.assertNotEqual(mind.decide(seen).action, "switch")
        self.assertIsNone(mind.memory.guard_mode)

    def test_the_fallback_takes_the_best_matched(self):
        """(the verifier's REDUNDANT `v_fallback_hp_only`) The member sent when NONE is sure to win is the best matched,
        weighed by its HP (matchup x (half + half its HP share)), not the healthiest and not the best matched alone. A
        trainer battle, the guarded Wurmple L5 at 3/21, Torchic L10 at 5/30 (Scratch, Growl, Focus Energy, Ember) and
        Poochyena L6 full; nobody wins either battle. A Zigzagoon L12: Torchic (45.6 x 0.58 = 26.6 against Poochyena's
        11.8; by HP alone it would be Poochyena). CONTROL, a Wingull L8 (it resists Ember): Poochyena (21.6 against
        Torchic's 28.0 x 0.58 = 16.3; by matchup alone it would be Torchic)."""
        torchic = 0x1008
        moves = ["Scratch", "Growl", "Focus Energy", "Ember"]
        for species, level, expected in (("Zigzagoon", 12, torchic), ("Wingull", 8, P)):
            party = [member("Wurmple", 5, WURMPLE_MOVES, 3, 21, W, 0), member("Torchic", 10, moves, 5, 30, torchic, 1),
                     poochyena_member()]
            seen = battle_look([battle_mon("Wurmple", 5, WURMPLE_MOVES, 3, 21, pid=W)], [foe(species, level)], party=party,
                               kind="trainer")
            for pid, hp in ((W, 3), (torchic, 5), (P, 21)):
                self.assertFalse(bp.fight_safe(bp.member_now(seen, pid), species, level, 1.0, hp, keep=0)[0], (species, pid))
            mind = guard_mind()
            mind.begin(seen)
            decision = mind.decide(seen)
            self.assertEqual((decision.action, decision.switch_pid), ("switch", expected), species)
            self.assertIn("no member is sure to win it", decision.reason)

    def test_land_slots_reads_normal_play_only(self):
        """(the verifier's REDUNDANT `v_land_slots_any_availability`) The Altering Cave has ONE land table a player meets
        in normal play (Zubat, up to L16) and eight a Mystery Gift event would swap in (Mareep, Pineco, Houndour,
        Teddiursa, Aipom, Shuckle, Stantler, Smeargle): the partner line reads the first only."""
        self.assertEqual(seasoned.land_slots("ALTERING_CAVE"), (("Zubat", 16),))


class ClosingTests(unittest.TestCase):
    """(round 4's closing pass, the round-4 verifier's V4-m4) Four round-4 rules the verifier's mutants broke with every
    test green (`v4_choice_ignores_cap`, `v4_pp_none_unusable`, `v4_pp_before_low`, `v4_last_resort_run_unbounded`), each
    pinned with its CONTROL; `gates/revert_bossprep.py` breaks each in a copy."""

    KIRLIA = 0x1009
    KIRLIA_MOVES = ("Growl", "Confusion", "Double Team", "Teleport")

    def kirlia_choice(self, level: int):
        """The Wurmple L4 trainee of an active plan beside a Kirlia partner at `level` (max HP 48 at L20, 50 at L21; the
        same four moves, Confusion the only one that hurts), on a world of ROUTE116 and ROUTE112 with a centre known from
        RUSTBORO. Returns (manager, the observation, `_raise_choice`'s answer)."""
        party = [summary(0, "Wurmple", 4, WURMPLE_MOVES, 18, pid=W),
                 summary(1, "Kirlia", level, self.KIRLIA_MOVES, {20: 48, 21: 50}[level], pid=self.KIRLIA)]
        mgr = c1_manager()
        world = world_with("ROUTE116", "ROUTE112", "RUSTBORO_CITY", current="ROUTE116", grass=True,
                           center_from="RUSTBORO_CITY")
        record = bp.new_record()
        record.update(status="active", trainee=W, target=19, plan=f"raise:{W:08x}:19", boss="BRAWLY")
        seen = look(party=party)
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
            return mgr, seen, mgr._raise_choice(seen, world, record)

    def test_the_raise_stays_under_the_cap(self):
        """(the verifier's REDUNDANT `v4_choice_ignores_cap`; E1's "another map UNDER ITS CAP") Kirlia L20 is the
        knock-out partner: the cap is L15 (L20 less 5). ROUTE116 (top L8, under the cap) fails the partner's line even
        healed (Poochyena is a Dark type: Confusion does nothing to it). ROUTE112 (top L16, OVER the cap) passes it
        healed. The raise stays on ROUTE116, its own fights only: the cap keeps the raise where the partner clears the
        wild Pokemon with room to spare, so a map over it is never switch-training's, however fit the partner looks.
        CONTROL: Kirlia L21 (cap L16): ROUTE112, AT its cap (a top of at most the cap counts as under it), is chosen, with
        switch-training ("mix")."""
        mgr, seen, choice = self.kirlia_choice(20)
        self.assertEqual(choice[3:5], (["ROUTE116", "ROUTE112"], 15))
        self.assertEqual(mgr.mode_on(seen, "ROUTE112", W)[0], "mix")  # fit there healed: only the cap keeps it out
        self.assertEqual(choice[:2], ("ROUTE116", "own"))
        self.assertIn("Poochyena L8: nothing it knows hurts Poochyena", choice[2])
        mgr, seen, choice = self.kirlia_choice(21)
        self.assertEqual(choice[3:5], (["ROUTE112", "ROUTE116"], 16))
        self.assertEqual(choice[:2], ("ROUTE112", "mix"))

    def test_an_unread_pp_is_still_a_move(self):
        """(the verifier's REDUNDANT `v4_pp_none_unusable`; the lead's call) A move whose PP was NOT READ (None in its
        summary slot) is still a move; only a PP READ as 0 is no move. Treating "not read" as empty would end a raise
        session, and send the party to heal, on missing information. Grovyle L25 at full HP, every move's PP unread:
        each move usable, not out of PP, safe against a Taillow L6, and the raise session's rest does not stop it.
        CONTROL, every move read at 0: none usable, out of PP, not safe, and the session stops."""
        unread = replace(member("Grovyle", 25, GROVYLE_MOVES, 68, 68, G, 0),
                         moves=tuple(slot(name, None) for name in GROVYLE_MOVES))
        empty = replace(unread, moves=tuple(slot(name, 0) for name in GROVYLE_MOVES))
        heal_below = ERRANDS["Story"].heal_below
        for mon, usable in ((unread, True), (empty, False)):
            seen = look(party=[mon, member("Poochyena", 6, ["Tackle", "Howl"], 21, 21, P, 1)])
            grovyle = bp.member_now(seen, G)
            self.assertIsNotNone(grovyle.summary)  # the summary is there: only its PP slots are unread
            self.assertEqual([bp._pp_left(grovyle, name) for name in GROVYLE_MOVES], [usable] * 4)
            self.assertEqual(bp.out_of_pp(grovyle), not usable)
            self.assertEqual(bp.fight_safe(grovyle, "Taillow", 6, 1.0, 68)[0], usable)
            rest = bp.trainee_rest(seen, G, heal_below, "Story")
            if usable:
                self.assertIsNone(rest)
            else:
                self.assertIn("has no PP left in any move that hurts", rest)

    @staticmethod
    def wurmple_party(hp: int, tackle_pp: int):
        """C1's party (`party18`) with the trainee Wurmple L4 at `hp`/18, Tackle (its only move that hurts) at `tackle_pp`."""
        out = party18()
        out[2] = replace(out[2], hp=hp, moves=(slot("Tackle", tackle_pp), slot("String Shot", 20)))
        return out

    def next_goal(self, party, links: int, healing=()):
        mgr, world, first = planned_on(party18())
        self.assertEqual(first.kind, "raise")
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: links):
            return mgr, decide2(mgr, party, world, healing=healing)

    def test_a_low_trainee_out_of_pp_gets_a_potion_first(self):
        """(the verifier's REDUNDANT `v4_pp_before_low`; the lead's call: the order the code has) The Wurmple plan, its
        trainee Wurmple L4 at 5/18 (under its floor) AND out of PP (Tackle at 0). `_trainee_low` asks "low" FIRST. So,
        with the centre 5 links away and Potions in the bag: a POTION on the spot (a Potion answers "low" only); then,
        at 18/18 and still out of PP, the centre. WHY THE ORDER MATTERS: asked the other way ("out of PP" first), the
        same state sends the trainee on the 5-link walk to the centre at 5/18, under its floor, and the Potion in the bag
        is never used; "low" first, it walks there at 18/18. With the centre NEAR (1 link) both orders go to the centre,
        and the reason names "low". CONTROL with PP (Tackle 20) at 5/18, far, Potions: the Potion as well."""
        party = self.wurmple_party(5, 0)
        mgr, _, _ = planned_on(party18())
        plan = mgr.boss_prep(look(party=party), at("ch6_briney_house")[1])
        self.assertEqual(mgr._trainee_low(look(party=party), plan), "low (5/18)")
        _, goal = self.next_goal(party, 5, (("Potion", 3),))
        self.assertEqual((goal.kind, goal.pid), ("potion", W), goal.reason)
        _, goal = self.next_goal(self.wurmple_party(18, 0), 5, (("Potion", 3),))
        self.assertEqual(goal.kind, "heal", goal.reason)
        self.assertIn("is out of PP (no PP left in any move that hurts)", goal.reason)
        _, goal = self.next_goal(party, 1)
        self.assertEqual(goal.kind, "heal", goal.reason)
        self.assertIn("is low (5/18)", goal.reason)
        _, goal = self.next_goal(self.wurmple_party(5, 20), 5, (("Potion", 3),))
        self.assertEqual((goal.kind, goal.pid), ("potion", W), goal.reason)

    def test_the_last_resort_run_is_bounded(self):
        """(the verifier's REDUNDANT `v4_last_resort_run_unbounded`; the lead's call: every loop is bounded where it loops)
        `BattleMind._last_resort` asked DIRECTLY, `run_ok` True: a wild battle, the guarded Wurmple L5 at 3/21 against a
        Poochyena L6 it cannot win, Grovyle fainted, Poochyena L6 full (it cannot win either). With MAX_RUN_TRIES - 1 runs
        made: a run, its count then MAX_RUN_TRIES. At MAX_RUN_TRIES: no run; under its floor ("desperate") the member that
        can come in, otherwise none. Every caller today passes `run_ok` True only with no run made in the battle, so in
        play the callers' own bound binds first; this proves the last resort's own bound where it is."""
        from ai_player.brain.battle import MAX_RUN_TRIES

        cases = ((MAX_RUN_TRIES - 1, False, "run"), (MAX_RUN_TRIES - 1, True, "run"), (MAX_RUN_TRIES, False, "none"),
                 (MAX_RUN_TRIES, True, "fallback"))
        for runs, desperate, expected in cases:
            mind = guard_mind()
            party = [member("Wurmple", 5, WURMPLE_MOVES, 3, 21, W, 0), grovyle_member(0), poochyena_member()]
            own = battle_mon("Wurmple", 5, WURMPLE_MOVES, 3, 21, pid=W)
            seen = battle_look([own], [foe("Poochyena", 6)], party=party)
            mind.begin(seen)
            mind.memory.runs = runs
            last, out = mind._last_resort(seen, own, foe("Poochyena", 6), "the test", desperate=desperate, run_ok=True)
            self.assertEqual(last, expected, (runs, desperate))
            if expected == "run":
                self.assertEqual((out.action, mind.memory.runs), ("run", MAX_RUN_TRIES))
                self.assertIn("no member is sure to win it, and it would not win it itself: run", out.reason)
            elif expected == "fallback":
                self.assertEqual((out[0].pid, mind.memory.runs), (P, MAX_RUN_TRIES))
            else:
                self.assertEqual((out, mind.memory.runs), (None, MAX_RUN_TRIES))


if __name__ == "__main__":
    unittest.main(verbosity=2)
