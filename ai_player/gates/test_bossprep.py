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
from ai_player.knowledge.facts import move_fact, move_named, species_fact  # noqa: E402
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
        self.assertEqual((goal.kind, goal.map, goal.milestone, goal.key), ("raise", "ROUTE104", "ch7_brawly", "raise"))
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

    def brawly_goal(self, status: str):
        mgr = c1_manager()
        record = mgr.prep(at("ch7_brawly")[0]).setdefault("bp", bp.new_record())
        record.update(status=status, trainee=PID["Wurmple"], target=19, plan=f"raise:{PID['Wurmple']:08x}:19")
        mgr.memory.cooldown["raise"] = 10 ** 6  # the raise put aside: what step 5 does then is the question
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
        mgr = manager()
        world = world_with("ROUTE104", "PETALBURG_WOODS", "ROUTE116", current="ROUTE104", grass=True)
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: 1):
            self.assertEqual([mgr.raise_map(world, level) for level in (3, 4, 6, 18, 1)],
                             ["ROUTE104", "PETALBURG_WOODS", "ROUTE116", "ROUTE116", "ROUTE104"])
        self.assertEqual(mgr.raise_map(world, 18), "ROUTE104")  # the others: no known way there
        with mock.patch.object(goals_module, "world_distance", lambda world_, key: goals_module.UNREACHABLE):
            self.assertIsNone(mgr.raise_map(world, 3))

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
