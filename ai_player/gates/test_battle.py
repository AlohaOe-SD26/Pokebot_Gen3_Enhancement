"""UNIT PROOFS of AI-player build step 4 (the AI's OWN BATTLES: the decider, the battle skill, the knowledge). Test side.

    py -3.12 ai_player/gates/test_battle.py        (exit 0 = every test passed)

Every rule is tested with its FAULT half (the rule broken, the test fails or the behaviour visibly changes), and the
mutants of `gates/revert_step4.py` break each rule in a copy of the real package and run THIS file there.

  FrameworkFreeTests  the step-4 files import nothing from the framework or the host; FAULT: a planted import is caught;
                      the decider imports none of the bot's battle code (RULING 35).
  KnowledgeTests      the knowledge files answer the facts the decider uses (Water x2 on Rock and Ground, Ground x0 on
                      Flying, Normal x0 on Ghost; Take Down's recoil 1/4, Double-Edge's 1/3, Jump Kick's miss recoil; a
                      species' types), each file carries its provenance; FAULT: a chart without a row is neutral.
  ValueTests          a move's worth = type x STAB x power x hit chance; a status move is worth 0; no PP, no move.
  TypeTests           Grovyle against a Geodude (the TYPE arm's battle): Absorb (weakest by power, x4) is chosen every
                      time over 40 seeds; FAULT (types ignored): Absorb never, Quick Attack and Pursuit both drawn.
  RecoilTests         the penalty grows as the user's HP falls; a Marshtomp against a Flying foe takes TAKE DOWN at full
                      HP and Water Gun at 20 %; FAULT (recoil ignored): Take Down at 20 % too. Jump Kick's miss recoil
                      and Explosion's faint are charged. (The step-4 verifier's round) against a sturdy foe the whole
                      hit lands; Jump Kick's miss recoil is capped at half the target's max HP (FAULT `uncapped_recoil`:
                      the whole); a recoil that would knock the user out costs the move's whole worth.
  RecordedRecoilTests on the RECORDED look of a real battle (a 15-HP Poochyena), through the decider's own valuation: the
                      recoil is a quarter of what the hit can take (3.75 HP, the game's own 74 -> 71): Take Down at full HP
                      and at 20 %, never at 3 HP (its recoil would faint it); FAULTS: the step-4 rule never at 20 %, the
                      recoil ignored at 3 HP.
  FieldTests          (the step-4 verifier's round) WHO GOES IN on the look the live party menu gives (no battle view): the
                      field REMEMBERED (`BattleMind.see`): a double battle's partner falls and the Grovyle still standing
                      is not sent (FAULT `forget_field`: it is, the verifier's bug); a single battle's replacement is
                      ranked against the remembered foe (Taillow against Shroomish; FAULT: Nincada by level and HP); both
                      fell: the second choice is not the first (`sent`); a refused member is not chosen again until the
                      next turn.
  ChoiceTests         a status move is never chosen while something that hurts has PP (FAULT: a status move valued like a
                      damaging one is drawn); about-equal moves are both drawn across seeds, a clear winner always.
  CatchTests          a new species the personality wants: a move that cannot knock it out first (its best roll leaves the
                      bar above KO_MARGIN), then a ball once the bar is at half; every move that could knock it out ->
                      throw at once; a Great Ball for a hard catch; at most MAX_THROWS balls; an owned species is
                      fought; Catcher always wants a new one, the others by a seeded draw.
  SwitchTests         badly matched and a much better healthy member -> switch (by PID); not when it far outlevels the foe,
                      not in a double battle, not twice against one foe; the replacement after a faint is the best
                      healthy member, never one that fainted or is already out.
  RunTests            training: run when its Pokemon is low and the foe is not, or the foe is far stronger; travelling, by
                      temperament; never in a trainer battle.
  HealTests           a trainer battle, its Pokemon low, a potion in the bag -> heal (target by PID); not in a wild battle,
                      not when the foe is about to fall.
  AnswerTests         "Use next POKéMON?" yes while one can fight; a nickname no; learning by `learn_choice`; an unknown
                      question no.
  LearnTests          Bide (an equivalent 40) replaces Growl (a status move); four damaging moves keep out a status move;
                      Mud Shot replaces Mud-slap on a Marshtomp; an HM is never forgotten; `needs_rest`.
  DoubleTests         a double battle's move is aimed at a foe (the effective one), a spread move is halved.
  SkillTests          the battle skill on a SCREEN MODEL (the real menus' rules: the 2 x 2 grids, the lists, the battle's
                      yes/no, the bag's pockets, the party's action list, the forget-a-move list): FIGHT then the move
                      by reading the grid; a ball from the poke_balls pocket reached with Right; a switch to a PID through
                      the party and SHIFT; the answers pressed on the option wanted only; every A on a wait, a menu
                      showing the option, never blind; FAULT (the grid's cursor not read): a wrong move. (The step-4
                      verifier's round) the party menu after a faint, with no battle view: the field remembered through
                      it (nothing refused); FAULT forget_field: the game REFUSES ("GROVYLE is already in battle!", printer
                      6, a WAIT), the skill reads it, A on its wait, and another goes in; FAULTS forget_field +
                      ignore_refusal (the step-4 code): "no Pokemon could be sent in"; both fell: two menus, two different
                      Pokemon; a battle resumed ON the refusal (`ki17_partymenu_wedge.ss1`'s shape): read, the cursor's
                      member refused, the other sent (FAULT ignore_refusal: "neither took input nor closed").
"""

from __future__ import annotations

import ast
import os
import random
import sys
import unittest
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUPPORT = Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO)
for entry in (str(REPO), str(SUPPORT / "sandbox-pokebot")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from ai_player.brain import battle as battle_module  # noqa: E402
from ai_player.brain.battle import (  # noqa: E402
    KO_MARGIN,
    MAX_THROWS,
    BattleFaults,
    BattleMind,
    learn_choice,
    matchup,
    move_value,
    needs_rest,
    recoil_penalty,
    recoil_risk,
)
from ai_player.eyes.observation import (  # noqa: E402
    BagSummary,
    BattleMon,
    BattleView,
    MenuView,
    MonSummary,
    MoveSlot,
    Observation,
    PlayerState,
    Progress,
    ScreenState,
)
from ai_player.eyes.screens import BATTLE_ACTIONS, YES_NO  # noqa: E402
from ai_player.hands.pad import Faults, Hands, Pacing  # noqa: E402
from ai_player.knowledge.facts import move_fact, move_named, provenance, species_fact, type_multiplier  # noqa: E402
from ai_player.skills import battle as skill_module  # noqa: E402
from ai_player.skills.battle import play_battle  # noqa: E402

PACKAGE = (Path(os.environ["AI_PLAYER_TEST_PACKAGE"]) if os.environ.get("AI_PLAYER_TEST_PACKAGE") else REPO / "ai_player")
STEP4_FILES = ("brain/battle.py", "skills/battle.py", "knowledge/facts.py", "knowledge/__init__.py")
#: The bot's battle code the AI may only LEARN from (RULING 35): no AI file names it.
BOT_BATTLE_CODE = ("battle_strategies", "battle_handler", "battle_action_selection", "battle_move_replacing",
                   "battle_menuing", "faint_chooser", "modules.story", "modules.encounter")


def slot(name: str, pp: int | None = 20) -> MoveSlot:
    fact = move_fact(name)
    return MoveSlot(name, fact.type, fact.power, pp, 30 if pp is not None else None)


def mon(species: str, level: int, moves: list[str], hp: int | None = 40, max_hp: int | None = 40, pid: int | None = 1,
        battler: int | None = 0, bar: int | None = None, pps: list[int] | None = None) -> BattleMon:
    fact = species_fact(species)
    bar = bar if bar is not None else (48 if hp is None else max(0, round(48 * hp / max_hp)))
    pps = pps or [20] * len(moves)
    return BattleMon(species, fact.dex, level, hp, max_hp, bar, "ok", fact.types,
                     tuple(slot(m, pp) for m, pp in zip(moves, pps)), pid, battler)


def foe(species: str, level: int, bar: int = 48, battler: int = 1, used: tuple[str, ...] = ()) -> BattleMon:
    fact = species_fact(species)
    return BattleMon(species, fact.dex, level, None, None, bar, "ok", fact.types, tuple(slot(m, None) for m in used), None,
                     battler)


def stats(species: str, level: int) -> tuple[int, ...]:
    """The summary's five stats for an average Pokemon of this species and level (`estimate_stat`)."""
    fact = species_fact(species)
    return tuple(battle_module.estimate_stat(b, level) for b in (fact.attack, fact.defense, fact.speed, fact.sp_attack,
                                                                  fact.sp_defense))


def member(species: str, level: int, moves: list[str], hp: int, max_hp: int, pid: int, slot_: int = 0) -> MonSummary:
    fact = species_fact(species)
    return MonSummary(slot_, species, fact.dex, level, hp, max_hp, "ok", fact.types, tuple(slot(m) for m in moves), pid,
                      12345, False, 0, stats(species, level))


def look(own: list[BattleMon], foes: list[BattleMon], party: list[MonSummary] | None = None, kind: str = "wild",
         balls: tuple = (("Poké Ball", 5),), healing: tuple = (), owned: tuple = (258,), double: bool = False,
         ui: MenuView | None = None) -> Observation:
    screen = ScreenState("BATTLE", "battle", None, False, False, True, ui=ui, scene="a battle")
    battle = BattleView(kind, double, 4 if kind == "wild" else 12, None if kind == "wild" else 1, tuple(own), tuple(foes))
    party = party if party is not None else [MonSummary(0, m.species, m.dex, m.level, m.hp, m.max_hp, "ok", m.types,
                                                         m.moves, m.pid, 12345, False, 0, stats(m.species, m.level)) for m in own]
    progress = Progress(3000, (), len(owned), len(owned), owned, ())
    return Observation(100, screen, None, None, tuple(party), BagSummary(balls, healing, sum(c for _, c in balls)), progress,
                       battle, 0, (), 0.0)


def mind(personality: str = "Story", seed: int = 1, faults: BattleFaults = BattleFaults(), purpose: str = "train") -> BattleMind:
    return BattleMind(personality, random.Random(f"{seed}:battle"), purpose, faults)


# ------------------------------------------------------------------------------------------- the files
class FrameworkFreeTests(unittest.TestCase):
    @staticmethod
    def foreign(source: str) -> list[str]:
        found = []
        for node in ast.walk(ast.parse(source)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            found += [n for n in names if n.split(".")[0] in ("modules", "plugins", "mgba") or n.startswith("ai_player.host")]
        return found

    def test_step4_files_import_no_framework_and_no_host(self) -> None:
        for relative in STEP4_FILES:
            with self.subTest(file=relative):
                self.assertEqual(self.foreign((PACKAGE / relative).read_text(encoding="utf-8")), [])

    def test_fault_a_planted_import_is_caught(self) -> None:
        planted = (PACKAGE / "brain/battle.py").read_text(encoding="utf-8") + "\nfrom modules.battle_strategies.default import DefaultBattleStrategy\n"
        self.assertEqual(self.foreign(planted), ["modules.battle_strategies.default"])

    def test_no_ai_file_names_the_bots_battle_code(self) -> None:
        """RULING 35: the bot's battle code is teaching material only (the purity gate refuses the imports; this checks
        the step-4 files do not even name it in code: strings and docstrings may cite it as teaching)."""
        for relative in STEP4_FILES:
            tree = ast.parse((PACKAGE / relative).read_text(encoding="utf-8"))
            names = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)] + \
                    [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
            with self.subTest(file=relative):
                self.assertFalse([n for n in names if n and any(b in n for b in BOT_BATTLE_CODE)])


# ------------------------------------------------------------------------------------------- the eyes' new menus
class EyesTests(unittest.TestCase):
    """`eyes/screens.py` read_ui on the bytes the host reads for the step-4 menus (each rule's decomp source is in that
    file's docstring); the host's reads themselves are proven live (`live_step4.py`: every A pressed on these menus is
    classified by its look, and the decisions are graded by the game's second path)."""

    def read(self, game_state: str, tasks: dict, raw: dict):
        from ai_player.eyes.screens import read_ui

        return read_ui(game_state, tasks, raw)

    def test_the_move_grid_and_whose_it_is(self) -> None:
        ui = self.read("BATTLE", {}, {"battle_move": {"choosing": True, "cursor": 2, "moves": GROVYLE, "battler": 2}})
        self.assertEqual((ui.kind, ui.options, ui.cursor, ui.battler), ("battle_move", tuple(GROVYLE), 2, 2))

    def test_the_target_cursor_is_a_battler_position(self) -> None:
        ui = self.read("BATTLE", {}, {"battle_target": {"choosing": True, "cursor": 3,
                                                        "names": ["Grovyle", "Geodude", "Nincada", "Shroomish"], "battler": 0}})
        self.assertEqual((ui.kind, ui.cursor, ui.options[ui.cursor]), ("battle_target", 3, "Shroomish"))

    def test_the_battles_yes_no(self) -> None:
        ui = self.read("BATTLE", {}, {"battle_yes_no": {"open": True, "cursor": 1, "accepts": True}})
        self.assertEqual((ui.kind, ui.options, ui.cursor), ("battle_yes_no", ("YES", "NO"), 1))
        closed = self.read("BATTLE", {}, {"battle_yes_no": {"open": False}})
        self.assertIsNone(closed)
        fading = self.read("BATTLE", {}, {"battle_yes_no": {"open": True, "cursor": 0, "accepts": True}, "fading": True})
        self.assertFalse(fading.accepts_input, "nothing takes input while a fade runs")

    def test_the_forget_a_move_list(self) -> None:
        ui = self.read("POKEMON_SUMMARY_SCREEN", {"Task_HandleReplaceMoveInput": bytes(32)},
                       {"move_forget": {"moves": ["Tackle", "Growl", "Mud-slap", "Water Gun", "Bide"], "cursor": 1}})
        self.assertEqual((ui.kind, ui.options[ui.cursor], len(ui.options)), ("move_forget", "Growl", 5))

    def test_the_party_and_bag_action_lists(self) -> None:
        menu = bytes([0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0])  # sMenu: cursorPos 1
        ui = self.read("PARTY_MENU", {"Task_HandleSelectionMenuInput": bytes(32)},
                       {"party_slot": 2, "party_tasks_known": True, "menu": menu, "party_action": {"actions": [10, 0, 2]}})
        self.assertEqual((ui.kind, ui.options, ui.cursor), ("party_action", ("SHIFT", "SUMMARY", "CANCEL"), 1))
        ui = self.read("BAG_MENU", {"Task_ItemContext_SingleRow": bytes(32)},
                       {"bag": {"pocket": 1, "cursor": 0, "scroll": 0, "items": ["Poké Ball"]}, "menu": bytes(12),
                        "bag_action": {"actions": [5, 4]}})
        self.assertEqual((ui.kind, ui.options, ui.cursor), ("bag_action", ("USE", "CANCEL"), 0))

    def test_the_bag_list_and_the_party_take_input_only_while_their_task_runs(self) -> None:
        bag = {"bag": {"pocket": 1, "cursor": 1, "scroll": 0, "items": ["Poké Ball", "Great Ball"]}}
        on = self.read("BAG_MENU", {"Task_BagMenu_HandleInput": bytes(32)}, bag)
        self.assertEqual((on.options, on.cursor, on.pocket, on.accepts_input),
                         (("Poké Ball", "Great Ball", "CLOSE BAG"), 1, "poke_balls", True))
        self.assertFalse(self.read("BAG_MENU", {"Task_SwitchBagPocket": bytes(32)}, bag).accepts_input)
        self.assertTrue(self.read("PARTY_MENU", {"Task_HandleChooseMonInput": bytes(32)},
                                  {"party_slot": 0, "party_tasks_known": True}).accepts_input)
        self.assertFalse(self.read("PARTY_MENU", {}, {"party_slot": 0, "party_tasks_known": True}).accepts_input)
        # an earlier reader (no task list: step 1's) sees the party as it did
        self.assertTrue(self.read("PARTY_MENU", {}, {"party_slot": 0}).accepts_input)

    def test_the_new_waits(self) -> None:
        from ai_player.eyes.screens import BATTLE_SCRIPT_WAITS, task_wait

        self.assertEqual(task_wait({"Task_HandleCaughtMonPageInput"}), "task Task_HandleCaughtMonPageInput (A or B)")
        self.assertEqual(BATTLE_SCRIPT_WAITS[0x6C], ((6, 8), "battle level-up stats box (any key)"))


# ------------------------------------------------------------------------------------------- the knowledge
class KnowledgeTests(unittest.TestCase):
    def test_the_type_chart(self) -> None:
        self.assertEqual(type_multiplier("Water", ("Rock", "Ground")), 4.0)
        self.assertEqual(type_multiplier("Grass", ("Rock", "Ground")), 4.0)
        self.assertEqual(type_multiplier("Ground", ("Normal", "Flying")), 0.0)
        self.assertEqual(type_multiplier("Normal", ("Ghost",)), 0.0)
        self.assertEqual(type_multiplier("Normal", ("Rock", "Ground")), 0.5)
        self.assertEqual(type_multiplier("Fire", ("Water", "Water")), 0.5, "a single type stored twice counts once")
        self.assertEqual(type_multiplier("Psychic", ("Dark",)), 0.0)

    def test_fault_a_type_the_chart_does_not_know_is_neutral(self) -> None:
        self.assertEqual(type_multiplier("Nonsense", ("Rock",)), 1.0)

    def test_recoil_facts(self) -> None:
        take_down, double_edge, jump_kick = move_fact("Take Down"), move_fact("Double-edge"), move_fact("Jump Kick")
        self.assertEqual((take_down.recoil_kind, take_down.recoil_fraction), ("of_damage_dealt", 0.25))
        self.assertEqual(double_edge.recoil_kind, "of_damage_dealt")
        self.assertAlmostEqual(double_edge.recoil_fraction, 1 / 3)
        self.assertEqual((jump_kick.recoil_kind, jump_kick.recoil_fraction), ("if_it_misses", 0.5))
        self.assertTrue(move_fact("Explosion").self_ko)
        self.assertIsNone(move_fact("Tackle").recoil_kind)
        self.assertEqual((move_fact("Absorb").category, move_fact("Quick Attack").category, move_fact("Growl").category),
                         ("special", "physical", "status"))

    def test_species_and_names(self) -> None:
        self.assertEqual(set(species_fact("Geodude").types), {"Rock", "Ground"})
        self.assertEqual(species_fact("Zigzagoon").catch_rate, 255)
        self.assertEqual(move_named("MUD-SLAP"), "Mud-slap")
        self.assertEqual(move_named("DOUBLE-EDGE"), "Double-edge")
        self.assertIsNone(move_named("NOT A MOVE"))

    def test_each_file_names_its_source(self) -> None:
        for name, block in provenance().items():
            with self.subTest(file=name):
                self.assertIn("sandbox-pokebot/modules/data", block["source"])
                self.assertEqual(len(block["source_sha256"]), 64)


# ------------------------------------------------------------------------------------------- values
class ValueTests(unittest.TestCase):
    def test_worth_is_type_stab_power_and_hit(self) -> None:
        value = move_value(0, slot("Water Gun"), ("Water",), 13, 1.0, ("Rock", "Ground"))
        self.assertEqual((value.effectiveness, value.stab, value.power, value.hit_chance, value.value), (4.0, 1.5, 40, 1.0, 240.0))
        tackle = move_value(0, slot("Tackle"), ("Water",), 13, 1.0, ("Rock", "Ground"))
        self.assertAlmostEqual(tackle.value, 0.5 * 35 * 0.95)

    def test_a_status_move_is_worth_nothing_in_a_fight(self) -> None:
        self.assertEqual(move_value(0, slot("Growl"), ("Water",), 13, 1.0, ("Normal",)).value, 0.0)

    def test_no_pp_no_move(self) -> None:
        self.assertIsNone(move_value(0, slot("Tackle", pp=0), ("Water",), 13, 1.0, ("Normal",)))

    def test_fault_ignoring_types_flattens_the_worth(self) -> None:
        value = move_value(0, slot("Water Gun"), ("Water",), 13, 1.0, ("Rock", "Ground"), BattleFaults(ignore_types=True))
        self.assertEqual(value.value, 40.0)


# ------------------------------------------------------------------------------------------- types
GROVYLE = ["Fury Cutter", "Pursuit", "Absorb", "Quick Attack"]


class TypeTests(unittest.TestCase):
    """The TYPE arm's battle (`fixtures/geodude_grovyle.ss1`): Grovyle L17 against a hiker's Geodude L8."""

    def picks(self, faults: BattleFaults, seeds: int = 40) -> list[str]:
        out = []
        for seed in range(seeds):
            decision = mind("Story", seed, faults).decide(look([mon("Grovyle", 17, GROVYLE, 37, 49)], [foe("Geodude", 8)], kind="trainer"))
            out.append(decision.move_name)
        return out

    def test_the_effective_move_is_chosen(self) -> None:
        self.assertEqual(set(self.picks(BattleFaults())), {"Absorb"})

    def test_fault_types_ignored_never_choose_it(self) -> None:
        picks = self.picks(BattleFaults(ignore_types=True))
        self.assertNotIn("Absorb", picks)
        self.assertEqual(set(picks), {"Quick Attack", "Pursuit"}, "the two about-equal moves are both drawn")

    def test_the_choice_says_what_the_type_chart_changed(self) -> None:
        """(the step-4 verifier's round: "TYPE 'rate across seeds' is not a rate") Every choice of the best move tells what
        the chart changed (`TypeSay`, the sweep's TYPE-DECISIONS): against the Geodude the near-best set with the chart is
        Absorb alone and the type-blind best is another move: DECISIVE; against a Zigzagoon (Normal) nothing the chart does
        moves the type-blind best out of the set: not decisive. Under the FAULT `ignore_types` the same sentence is the
        chart's counterfactual (the move chosen is not in it). A catch's weakening hit says nothing (not a best-move choice).
        FAULT (mutant B43: `decisive` always true)."""
        geodude = mind().decide(look([mon("Grovyle", 17, GROVYLE, 37, 49)], [foe("Geodude", 8)], kind="trainer"))
        self.assertEqual((geodude.types.near, geodude.types.decisive), (("Absorb",), True), geodude.types)
        self.assertIn(geodude.types.blind, ("Quick Attack", "Pursuit"))
        self.assertEqual(geodude.types.hurting, 4)
        normal = mind().decide(look([mon("Grovyle", 17, GROVYLE, 37, 49)], [foe("Zigzagoon", 8)], kind="trainer"))
        self.assertFalse(normal.types.decisive, normal.types)
        blind = mind(faults=BattleFaults(ignore_types=True)).decide(
            look([mon("Grovyle", 17, GROVYLE, 37, 49)], [foe("Geodude", 8)], kind="trainer"))
        self.assertEqual((blind.types.near, blind.types.decisive), (("Absorb",), True))
        self.assertNotIn(blind.move_name, blind.types.near, "the type-blind decider's move is not the chart's")
        catcher = mind("Catcher")
        wild = look([mon("Mudkip", 8, ["Tackle", "Growl", "Mud-slap"], 19, 28)], [foe("Wurmple", 2)], owned=())
        catcher.begin(wild)
        weaken = catcher.decide(wild)
        self.assertTrue(weaken.reason.startswith("to CATCH") and weaken.types is None, (weaken.reason, weaken.types))


# ------------------------------------------------------------------------------------------- recoil
MARSHTOMP = ["Tackle", "Rock Smash", "Take Down", "Water Gun"]


class RecoilTests(unittest.TestCase):
    def test_the_penalty_grows_as_hp_falls(self) -> None:
        fact = move_fact("Take Down")
        full, low = recoil_penalty(fact, 76.5, 1.0), recoil_penalty(fact, 76.5, 0.2)
        self.assertAlmostEqual(full, 76.5 * 0.25 * 0.5)
        self.assertAlmostEqual(low, 76.5 * 0.25 * 2.5)
        self.assertGreater(low, full)

    def test_take_down_at_full_hp_water_gun_when_low(self) -> None:
        """Against a Taillow (Normal/Flying: Ground is useless), Marshtomp's Take Down (90, 85 %) is worth most at full
        HP; at 20 % HP the recoil would cost too much and Water Gun is chosen."""
        def pick(hp: int, faults: BattleFaults = BattleFaults()) -> str:
            own = mon("Marshtomp", 32, MARSHTOMP, hp, 99)
            return mind("Trainer", 1, faults).decide(look([own], [foe("Taillow", 30)], kind="trainer")).move_name

        self.assertEqual(pick(99), "Take Down")
        self.assertEqual(pick(20), "Water Gun")

    def test_fault_recoil_ignored_takes_it_down_at_low_hp(self) -> None:
        own = mon("Marshtomp", 32, MARSHTOMP, 20, 99)
        decision = mind("Trainer", 1, BattleFaults(ignore_recoil=True)).decide(look([own], [foe("Taillow", 30)], kind="trainer"))
        self.assertEqual(decision.move_name, "Take Down")

    def test_miss_recoil_and_self_ko_are_charged(self) -> None:
        jump = move_value(0, slot("Jump Kick"), ("Fighting",), 30, 0.3, ("Normal",))
        self.assertGreater(jump.recoil, 0)
        self.assertAlmostEqual(jump.recoil, 70 * 2 * 1.5 * 0.05 * 0.5 * (0.5 + 2.5 * 0.7))
        boom = move_value(0, slot("Explosion"), ("Rock", "Ground"), 30, 1.0, ("Normal",))
        self.assertEqual(boom.value, 0.0, "fainting itself is its whole worth while healthy")

    def test_against_a_sturdy_foe_the_whole_hit_lands(self) -> None:
        """(the step-4 verifier's round) Against a Taillow L30 a Marshtomp L32's Take Down takes most of its HP but not
        all (about 0.84 of it): every point of it lands, so the recoil is a quarter of the whole hit (and at 20 % HP still
        too dear: `test_take_down_at_full_hp_water_gun_when_low`)."""
        own = mon("Marshtomp", 32, MARSHTOMP, 99, 99)
        risk = recoil_risk(own.moves[2], None, own, foe("Taillow", 30))
        self.assertEqual(risk.landed, 1.0, risk)
        self.assertFalse(risk.faints_user)

    def test_jump_kicks_miss_recoil_is_capped_at_half_the_targets_max_hp(self) -> None:
        """Jump Kick from a strong Hitmonlee against a weak foe: the damage it would have dealt is several times the
        foe's max HP, so its miss recoil (half of it, at most half the foe's max HP) counts that capped share; FAULT
        `uncapped_recoil` charges the whole."""
        own = mon("Hitmonlee", 50, ["Jump Kick"], 120, 120)
        weak = foe("Zigzagoon", 5)
        risk = recoil_risk(own.moves[0], None, own, weak)
        self.assertLess(risk.miss_capped, 0.5, risk)
        capped = move_value(0, own.moves[0], own.types, own.level, 1.0, weak.types, BattleFaults(), risk)
        whole = move_value(0, own.moves[0], own.types, own.level, 1.0, weak.types, BattleFaults(uncapped_recoil=True), risk)
        self.assertLess(capped.recoil, whole.recoil * 0.5)

    def test_a_recoil_that_would_faint_the_user_costs_the_whole_worth(self) -> None:
        own = mon("Marshtomp", 32, MARSHTOMP, 5, 99)
        risk = recoil_risk(own.moves[2], None, own, foe("Taillow", 30))
        self.assertTrue(risk.faints_user, risk)
        value = move_value(2, own.moves[2], own.types, own.level, 5 / 99, ("Normal", "Flying"), BattleFaults(), risk)
        self.assertEqual(value.value, 0.0)


RECORDED_RECOIL = REPO / "ai_player" / "gates" / "fixtures" / "recoil_r102.look.json"


def recorded_look(hp: int | None = None) -> Observation:
    """The AI's own Observation at the action menu of a REAL battle (`fixtures/recoil_r102.look.json`, recorded by
    `make_step4_fixtures.py --only recoil` from `ch13_r119_wedge.ss1`: Marshtomp L32 74/99, Tackle, Rock Smash, TAKE DOWN,
    Water Gun, against a wild Poochyena L3). `hp`: the same look with the Marshtomp's HP set (a counterfactual on the
    recorded look: the eyes' values, one number changed)."""
    import json

    data = json.loads(RECORDED_RECOIL.read_text(encoding="utf-8"))

    def battler(entry: dict) -> BattleMon:
        moves = tuple(MoveSlot(**m) for m in entry["moves"])
        return BattleMon(**{**entry, "types": tuple(entry["types"]), "moves": moves})

    own = [battler(e) for e in data["battle"]["own"]]
    if hp is not None:
        own[0] = replace(own[0], hp=hp)
    foes = [battler(e) for e in data["battle"]["foe"]]
    party = [MonSummary(**{**m, "types": tuple(m["types"]), "moves": tuple(MoveSlot(**s) for s in m["moves"]),
                           "stats": tuple(m["stats"])}) for m in data["party"]]
    return look(own, foes, party=party, owned=tuple(data["owned_dex"]))


class RecordedRecoilTests(unittest.TestCase):
    """RECOIL on a RECORDED look (above), through the decider's own valuation (`BattleMind._values`: the damage estimate
    and the recoil it would really cost, `recoil_risk`). The foe is a 15-HP Poochyena L3: Take Down takes all it has and
    its recoil is a quarter of THAT (the game's own: the Marshtomp went 74 -> 71 when it was used, the step-4 verifier's
    per-frame read), so it is the move worth most at full HP and at 20 % alike; at 3 HP its recoil (about 3.75) would knock
    the Marshtomp out and it is NEVER chosen. FAULTS: `uncapped_recoil` (the step-4 rule: the recoil of its whole worth):
    never at 20 % (the over-charge the verifier found); `ignore_recoil`: chosen even at 3 HP."""

    def picks(self, hp: int, faults: BattleFaults = BattleFaults()) -> list[str]:
        """The MOVE the decider picks on the recorded look (its move choice: in a wild battle at low HP the decider would
        rather RUN, `RunTests`, so the choice is asked of `choose_move` over the decider's own move values)."""
        recorded = recorded_look(hp)
        own, foe_ = recorded.battle.own[0], recorded.battle.foe[0]
        values = mind("Story", 0, faults)._values(own, foe_, own.hp / own.max_hp, recorded)
        return [mind("Story", seed, faults).choose_move(values)[0].name for seed in range(40)]

    def test_the_recorded_look_is_the_battle_named(self) -> None:
        recorded = recorded_look()
        own, foe_ = recorded.battle.own[0], recorded.battle.foe[0]
        self.assertEqual((own.species, own.hp, own.max_hp, foe_.species), ("Marshtomp", 74, 99, "Poochyena"))
        self.assertIn("Take Down", [m.name for m in own.moves])

    def test_its_recoil_is_a_share_of_what_the_foe_has_left(self) -> None:
        recorded = recorded_look()
        own, foe_ = recorded.battle.own[0], recorded.battle.foe[0]
        user = next(m for m in recorded.party if m.pid == own.pid)
        risk = recoil_risk(next(m for m in own.moves if m.name == "Take Down"), user, own, foe_)
        self.assertLess(risk.landed, 0.2, "one hit is many times the Poochyena's HP")
        self.assertAlmostEqual(risk.recoil_hp, 15 / 4, delta=0.01)  # its max HP guessed 15 (L3, base 35): 3.75
        self.assertFalse(risk.faints_user)

    def test_take_down_at_full_hp_and_at_20_percent_never_when_its_recoil_would_faint_it(self) -> None:
        full, low, brink = self.picks(99), self.picks(20), self.picks(3)
        self.assertEqual(set(full), {"Take Down"}, full)
        self.assertEqual(set(low), {"Take Down"}, low)
        self.assertEqual(set(brink), {"Water Gun"}, brink)

    def test_fault_the_step4_rule_overcharges_it_at_20_percent(self) -> None:
        self.assertEqual(set(self.picks(20, BattleFaults(uncapped_recoil=True))), {"Water Gun"})

    def test_fault_recoil_ignored_takes_it_at_3_hp(self) -> None:
        self.assertEqual(set(self.picks(3, BattleFaults(ignore_recoil=True))), {"Take Down"})


# ------------------------------------------------------------------------------------------- choices
class ChoiceTests(unittest.TestCase):
    def test_never_a_status_move_by_habit(self) -> None:
        for seed in range(30):
            own = mon("Mudkip", 8, ["Tackle", "Growl", "Mud-slap"], 19, 28)
            decision = mind("Catcher", seed).decide(look([own], [foe("Zigzagoon", 3)], owned=(258, 263)))
            self.assertNotEqual(decision.move_name, "Growl")

    def test_a_status_move_only_when_nothing_else_has_pp(self) -> None:
        own = mon("Mudkip", 8, ["Tackle", "Growl"], 19, 28, pps=[0, 30])
        decision = mind().decide(look([own], [foe("Zigzagoon", 3)], owned=(258, 263)))
        self.assertEqual(decision.move_name, "Growl")

    def test_fault_a_status_move_valued_like_a_damaging_one_is_drawn(self) -> None:
        original = battle_module.move_value

        def flat(slot_, move, *args, **kwargs):
            value = original(slot_, move, *args, **kwargs)
            if value is not None and value.status:
                return replace(value, value=33.0, status=False)
            return value

        battle_module.move_value = flat
        try:
            picks = {mind("Catcher", seed).decide(look([mon("Mudkip", 8, ["Tackle", "Growl", "Mud-slap"], 19, 28)],
                                                         [foe("Zigzagoon", 3)], owned=(258, 263))).move_name for seed in range(30)}
        finally:
            battle_module.move_value = original
        self.assertIn("Growl", picks)

    def test_about_equal_moves_are_both_drawn_a_clear_winner_always(self) -> None:
        equal = {mind("Story", s).decide(look([mon("Grovyle", 16, GROVYLE, 46, 47)], [foe("Zigzagoon", 9)], owned=(253, 263))).move_name
                 for s in range(30)}
        self.assertEqual(equal, {"Pursuit", "Quick Attack"})
        clear = {mind("Story", s).decide(look([mon("Grovyle", 16, GROVYLE, 46, 47)], [foe("Machop", 9)], kind="trainer")).move_name
                 for s in range(30)}
        self.assertEqual(clear, {"Quick Attack"})


# ------------------------------------------------------------------------------------------- catching
class CatchTests(unittest.TestCase):
    def test_weaken_first_with_a_move_that_cannot_knock_it_out(self) -> None:
        brain = mind("Catcher")
        observation = look([mon("Mudkip", 8, ["Tackle", "Growl", "Mud-slap"], 19, 28)], [foe("Wurmple", 2)])
        brain.begin(observation)
        decision = brain.decide(observation)
        self.assertEqual((decision.action, decision.move_name), ("fight", "Tackle"))
        self.assertIn("cannot knock it out", decision.reason)

    def test_throw_once_the_bar_is_at_half(self) -> None:
        brain = mind("Catcher")
        observation = look([mon("Mudkip", 8, ["Tackle", "Growl", "Mud-slap"], 19, 28)], [foe("Wurmple", 2, bar=20)])
        brain.begin(observation)
        decision = brain.decide(observation)
        self.assertEqual((decision.action, decision.ball), ("ball", "Poké Ball"))

    def test_every_move_could_knock_it_out_so_throw_at_once(self) -> None:
        brain = mind("Catcher")
        observation = look([mon("Grovyle", 30, GROVYLE, 80, 80)], [foe("Wurmple", 2, bar=40)])
        brain.begin(observation)
        decision = brain.decide(observation)
        self.assertEqual(decision.action, "ball")
        self.assertIn("every move could knock it out", decision.reason)

    def test_fault_no_ko_check_attacks_into_a_ko(self) -> None:
        original = battle_module.KO_MARGIN
        battle_module.KO_MARGIN = -10.0  # every move "safe"
        try:
            brain = mind("Catcher")
            observation = look([mon("Grovyle", 30, GROVYLE, 80, 80)], [foe("Wurmple", 2, bar=40)])
            brain.begin(observation)
            self.assertEqual(brain.decide(observation).action, "fight")
        finally:
            battle_module.KO_MARGIN = original

    def test_a_great_ball_for_a_hard_catch(self) -> None:
        brain = mind("Catcher")
        observation = look([mon("Mudkip", 8, ["Tackle"], 19, 28)], [foe("Sableye", 6, bar=20)],
                           balls=(("Poké Ball", 5), ("Great Ball", 1)))  # Sableye's catch rate is 45
        brain.begin(observation)
        self.assertEqual(brain.decide(observation).ball, "Great Ball")

    def test_at_most_max_throws(self) -> None:
        brain = mind("Catcher")
        observation = look([mon("Mudkip", 8, ["Tackle"], 19, 28)], [foe("Wurmple", 2, bar=10)], balls=(("Poké Ball", 99),))
        brain.begin(observation)
        actions = [brain.decide(observation).action for _ in range(MAX_THROWS + 3)]
        self.assertEqual(actions.count("ball"), MAX_THROWS)

    def test_an_owned_species_is_fought(self) -> None:
        brain = mind("Catcher")
        observation = look([mon("Mudkip", 8, ["Tackle"], 19, 28)], [foe("Wurmple", 2)], owned=(258, 265))
        self.assertIn("a wild battle", brain.begin(observation))
        self.assertEqual(brain.decide(observation).action, "fight")
        self.assertFalse(brain.memory.want_catch)

    def test_catch_wishes_by_personality(self) -> None:
        """One seeded draw per species and run: Catcher always (1.0), Story 0.6, Trainer 0.75 (200 seeds each)."""
        counts = {}
        for name in ("Catcher", "Story", "Trainer"):
            wanted = 0
            for s in range(200):
                brain = mind(name, s)
                brain.begin(look([mon("Mudkip", 8, ["Tackle"], 19, 28)], [foe("Wurmple", 2)]))
                wanted += brain.memory.want_catch
            counts[name] = wanted
        self.assertEqual(counts["Catcher"], 200)
        self.assertTrue(90 <= counts["Story"] <= 150, counts)
        self.assertTrue(120 <= counts["Trainer"] <= 180, counts)


# ------------------------------------------------------------------------------------------- switching
class SwitchTests(unittest.TestCase):
    def party(self):
        return [member("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, 1),
                member("Grovyle", 16, GROVYLE, 40, 47, 2, 1)]

    def test_badly_matched_and_a_much_better_member(self) -> None:
        """Mudkip (Water) against a Lotad... no: against a Shroomish (Grass hits it x2, its moves x0.5): Grovyle, two
        levels up and resisting, is much better."""
        decision = mind().decide(look([mon("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, pid=1)], [foe("Shroomish", 15)],
                                      party=self.party(), kind="trainer"))
        self.assertEqual((decision.action, decision.switch_pid), ("switch", 2))

    def test_not_when_it_far_outlevels_the_foe(self) -> None:
        decision = mind().decide(look([mon("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, pid=1)], [foe("Shroomish", 7)],
                                      party=self.party(), kind="trainer"))
        self.assertEqual(decision.action, "fight")

    def test_fault_no_level_guard_switches_against_a_weak_foe(self) -> None:
        original = battle_module.OUTLEVELS
        battle_module.OUTLEVELS = 99
        try:
            decision = mind().decide(look([mon("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, pid=1)], [foe("Shroomish", 7)],
                                          party=self.party(), kind="trainer"))
        finally:
            battle_module.OUTLEVELS = original
        self.assertEqual(decision.action, "switch")

    def test_not_twice_against_one_foe_and_not_in_a_double_battle(self) -> None:
        brain = mind()
        observation = look([mon("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, pid=1)], [foe("Shroomish", 15)],
                           party=self.party(), kind="trainer")
        self.assertEqual(brain.decide(observation).action, "switch")
        self.assertEqual(brain.decide(observation).action, "fight")
        double = look([mon("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, pid=1)], [foe("Shroomish", 15)],
                      party=self.party(), kind="trainer", double=True)
        self.assertEqual(mind().decide(double).action, "fight")

    def test_the_replacement_is_the_best_healthy_member_by_pid(self) -> None:
        party = [member("Mudkip", 14, ["Tackle", "Water Gun"], 0, 42, 1), member("Poochyena", 4, ["Tackle"], 16, 17, 3, 1),
                 member("Grovyle", 16, GROVYLE, 40, 47, 2, 2)]
        pid, reason = mind().replacement(look([], [foe("Geodude", 8)], party=party, kind="trainer"))
        self.assertEqual(pid, 2, reason)
        party[2] = replace(party[2], hp=0)
        pid, reason = mind().replacement(look([], [foe("Geodude", 8)], party=party, kind="trainer"))
        self.assertEqual(pid, 3, reason)
        party[1] = replace(party[1], hp=0)
        self.assertEqual(mind().replacement(look([], [foe("Geodude", 8)], party=party, kind="trainer"))[0], None)


def party_menu(party: list[MonSummary]) -> Observation:
    """The look at the battle's PARTY MENU as the eyes report it (the step-4 verifier's finding): the menu fills the screen
    and the look carries NO battle view (`host/eyes.py` reads one only in game state BATTLE): `menu=party ui=party[0]`."""
    screen = ScreenState("PARTY_MENU", "menu", "party", False, False, True, ui=MenuView("party", (), 0, True),
                         scene="the party menu")
    return Observation(100, screen, None, None, tuple(party), BagSummary((), (), 0), Progress(3000, (), 1, 1, (258,), ()),
                       None, 0, (), 0.0)


class FieldTests(unittest.TestCase):
    """(the step-4 verifier's round) WHO GOES IN after a faint, on the look the live party menu actually gives (no battle
    view): the decider REMEMBERS the field from its last look at the battle (`BattleMind.see`). FAULT `forget_field` (the
    step-4 code): the party-menu look alone."""

    #: rate_step4's TYPE-FAULT seed 6, as the verifier found it: the PARTNER Nincada fainted; Grovyle still stands
    GROVYLE_PID, NINCADA_PID, WHISMUR_PID, SKITTY_PID = 0x550A9BE6, 0x8FFFC144, 0xA9226D5C, 0x7F7652D1

    def double_party(self) -> list[MonSummary]:
        return [member("Grovyle", 17, GROVYLE, 37, 49, self.GROVYLE_PID, 0),
                member("Nincada", 6, ["Scratch", "Harden", "Leech Life"], 0, 21, self.NINCADA_PID, 1),
                member("Whismur", 6, ["Pound", "Uproar"], 25, 25, self.WHISMUR_PID, 2),
                member("Skitty", 8, ["Growl", "Tackle", "Tail Whip", "Attract"], 27, 27, self.SKITTY_PID, 3)]

    def double_field(self) -> Observation:
        """The last look at the battle before the party menu: Grovyle at position 0 (Nincada fainted: absent), the
        Geodude and the Lotad."""
        own = [mon("Grovyle", 17, GROVYLE, 37, 49, pid=self.GROVYLE_PID, battler=0)]
        return look(own, [foe("Geodude", 8, battler=1), foe("Lotad", 9, battler=3)], party=self.double_party(),
                    kind="trainer", double=True)

    def test_a_double_battles_partner_faints_the_one_still_standing_is_not_sent(self) -> None:
        brain = mind()
        brain.see(self.double_field())
        pid, reason = brain.replacement(party_menu(self.double_party()))
        self.assertIn(pid, (self.WHISMUR_PID, self.SKITTY_PID), reason)
        self.assertIn("REMEMBERED", reason)
        self.assertIn("against Geodude and Lotad", reason)
        self.assertIn("Grovyle on the field", reason)

    def test_fault_forget_field_sends_the_one_still_standing(self) -> None:
        """The step-4 code, as the verifier reproduced it: 'Grovyle L17 (37/49 HP) is the best left'."""
        brain = mind(faults=BattleFaults(forget_field=True))
        brain.see(self.double_field())
        pid, reason = brain.replacement(party_menu(self.double_party()))
        self.assertEqual(pid, self.GROVYLE_PID, reason)

    def faint_party(self) -> list[MonSummary]:
        """Arm FAINT's party at its party menu (the verifier's `faint_choice_unit.py`): the Mudkip fainted against Karen's
        Shroomish."""
        return [member("Mudkip", 14, ["Tackle", "Growl", "Mud-slap", "Water Gun"], 0, 42, 0x550A9BE6, 0),
                member("Poochyena", 4, ["Tackle"], 16, 17, 0x5815089E, 1),
                member("Nincada", 6, ["Scratch", "Harden", "Leech Life"], 20, 20, 0x4457D0FB, 2),
                member("Whismur", 6, ["Pound", "Uproar"], 23, 23, 0x7E9BB3BA, 3),
                member("Taillow", 6, ["Peck", "Growl", "Focus Energy"], 11, 21, 0xAE39815D, 4)]

    def test_a_single_battles_replacement_is_matched_against_the_remembered_foe(self) -> None:
        """A Flying Taillow at half HP against a Grass Shroomish beats a full Nincada (Grass hits Bug x0.5 but Ground
        x2); without the field in mind only level and HP are left, and the Nincada goes in."""
        party = self.faint_party()
        field = look([mon("Mudkip", 14, ["Tackle", "Growl", "Mud-slap", "Water Gun"], 0, 42, pid=0x550A9BE6)],
                     [foe("Shroomish", 9)], party=party, kind="trainer")
        brain = mind()
        brain.see(field)
        pid, reason = brain.replacement(party_menu(party))
        self.assertEqual(pid, 0xAE39815D, reason)
        self.assertIn("against Shroomish", reason)
        forgetful = mind(faults=BattleFaults(forget_field=True))
        forgetful.see(field)
        pid, reason = forgetful.replacement(party_menu(party))
        self.assertEqual(pid, 0x4457D0FB, reason)
        self.assertIn("no foe standing", reason)

    def test_both_fell_the_second_choice_is_not_the_first(self) -> None:
        """Both of a double battle's battlers fainted: two party menus, and no look at the field between them shows the
        first one sent in; it is remembered as sent (`sent`), and the second choice is another."""
        party = self.double_party()
        party[0] = replace(party[0], hp=0)
        field = look([], [foe("Geodude", 8, battler=1), foe("Lotad", 9, battler=3)], party=party, kind="trainer",
                     double=True)
        brain = mind()
        brain.see(field)
        first, _ = brain.replacement(party_menu(party))
        brain.sent(first)
        second, reason = brain.replacement(party_menu(party))
        self.assertIsNotNone(second)
        self.assertNotEqual(first, second, reason)
        self.assertIn("sent in", reason)

    def test_a_refused_member_is_not_chosen_again_until_the_next_turn(self) -> None:
        party = self.double_party()
        brain = mind(faults=BattleFaults(forget_field=True))
        brain.refuse(self.GROVYLE_PID, "GROVYLE is already in battle!")
        pid, reason = brain.replacement(party_menu(party))
        self.assertNotEqual(pid, self.GROVYLE_PID, reason)
        turn = self.double_field()
        turn = replace(turn, screen=replace(turn.screen, ui=MenuView("battle_action", BATTLE_ACTIONS, 0, True, battler=0)))
        brain.see(turn)
        self.assertEqual(brain.refused, {}, "a new turn: the refusals are forgotten")


# ------------------------------------------------------------------------------------------- running, healing
class RunTests(unittest.TestCase):
    def test_training_runs_when_low_or_outmatched(self) -> None:
        low = mind("Story").decide(look([mon("Mudkip", 8, ["Tackle"], 5, 28)], [foe("Zigzagoon", 3)], owned=(258, 263)))
        self.assertEqual(low.action, "run")
        strong = mind("Story").decide(look([mon("Mudkip", 8, ["Tackle"], 28, 28)], [foe("Zigzagoon", 15)], owned=(258, 263)))
        self.assertEqual(strong.action, "run")
        fine = mind("Story").decide(look([mon("Mudkip", 8, ["Tackle"], 28, 28)], [foe("Zigzagoon", 3)], owned=(258, 263)))
        self.assertEqual(fine.action, "fight")

    def test_travelling_runs_by_temperament(self) -> None:
        runs = {name: sum(mind(name, s, purpose="travel").decide(look([mon("Mudkip", 8, ["Tackle"], 28, 28)],
                                                                      [foe("Zigzagoon", 3)], owned=(258, 263))).action == "run"
                          for s in range(100)) for name in ("Story", "Trainer")}
        self.assertGreater(runs["Story"], runs["Trainer"] + 30, runs)

    def test_never_runs_from_a_trainer(self) -> None:
        decision = mind("Story").decide(look([mon("Mudkip", 8, ["Tackle"], 5, 28)], [foe("Zigzagoon", 3)], kind="trainer"))
        self.assertNotEqual(decision.action, "run")


class HealTests(unittest.TestCase):
    def test_a_trainer_battle_low_hp_a_potion(self) -> None:
        decision = mind("Story").decide(look([mon("Mudkip", 14, ["Tackle"], 6, 42, pid=7)], [foe("Zigzagoon", 12)],
                                             kind="trainer", healing=(("Potion", 2),)))
        self.assertEqual((decision.action, decision.item, decision.target_pid), ("item", "Potion", 7))

    def test_not_in_a_wild_battle_nor_when_the_foe_is_about_to_fall(self) -> None:
        # the foe's bar at 27 % (13 of 48 pixels): low enough that training does not run (`_run_or_not`: only while the
        # foe's bar is over 30 %) and high enough that it is not "about to fall" (20 %): only the battle's KIND keeps
        # the Potion in the bag (revert_step4 B15: with the trainer-only rule gone, this wild battle healed)
        wild = mind("Story").decide(look([mon("Mudkip", 14, ["Tackle"], 6, 42)], [foe("Zigzagoon", 12, bar=13)],
                                         healing=(("Potion", 2),), owned=(258, 263)))
        self.assertEqual(wild.action, "fight", wild.reason)
        trainer = mind("Story").decide(look([mon("Mudkip", 14, ["Tackle"], 6, 42)], [foe("Zigzagoon", 12, bar=13)],
                                            kind="trainer", healing=(("Potion", 2),)))
        self.assertEqual(trainer.action, "item", "the same battle, a trainer's: it heals (the wild arm is not vacuous)")
        falling = mind("Story").decide(look([mon("Mudkip", 14, ["Tackle"], 6, 42)], [foe("Zigzagoon", 12, bar=5)],
                                            kind="trainer", healing=(("Potion", 2),)))
        self.assertEqual(falling.action, "fight")


# ------------------------------------------------------------------------------------------- questions, learning
class AnswerTests(unittest.TestCase):
    def test_the_questions(self) -> None:
        party = [member("Mudkip", 8, ["Tackle"], 0, 28, 1), member("Poochyena", 4, ["Tackle"], 16, 17, 2, 1)]
        observation = look([], [foe("Zigzagoon", 3)], party=party)
        self.assertTrue(mind().answer("Use next POKéMON?", observation)[0])
        dead = [replace(party[0]), replace(party[1], hp=0)]
        self.assertFalse(mind().answer("Use next POKéMON?", look([], [foe("Zigzagoon", 3)], party=dead))[0])
        self.assertFalse(mind().answer("Give a nickname to the captured ZIGZAGOON?", observation)[0])
        self.assertFalse(mind().answer("Would you like to save the game?", observation)[0])

    def test_learning_follows_learn_choice(self) -> None:
        mudkip = member("Mudkip", 15, ["Tackle", "Growl", "Mud-slap", "Water Gun"], 30, 46, 1)
        choice = learn_choice(mudkip, "Bide")
        self.assertTrue(mind().answer("Delete a move to make room for BIDE?", look([], []), choice)[0])
        self.assertFalse(mind().answer("Stop learning BIDE?", look([], []), choice)[0])
        keep = learn_choice(member("Grovyle", 23, ["Pursuit", "Absorb", "Quick Attack", "Fury Cutter"], 50, 60, 2), "Screech")
        self.assertFalse(mind().answer("Delete a move to make room for SCREECH?", look([], []), keep)[0])
        self.assertTrue(mind().answer("Stop learning SCREECH?", look([], []), keep)[0])


class LearnTests(unittest.TestCase):
    def test_bide_replaces_growl(self) -> None:
        choice = learn_choice(member("Mudkip", 15, ["Tackle", "Growl", "Mud-slap", "Water Gun"], 30, 46, 1), "Bide")
        self.assertEqual((choice.learn, choice.forget), (True, "Growl"), choice.reason)

    def test_four_damaging_moves_keep_out_a_status_move(self) -> None:
        choice = learn_choice(member("Grovyle", 23, ["Pursuit", "Absorb", "Quick Attack", "Fury Cutter"], 50, 60, 2), "Screech")
        self.assertFalse(choice.learn, choice.reason)

    def test_mud_shot_replaces_mud_slap_on_a_marshtomp(self) -> None:
        choice = learn_choice(member("Marshtomp", 16, ["Tackle", "Bide", "Mud-slap", "Water Gun"], 50, 50, 1), "Mud Shot")
        self.assertEqual((choice.learn, choice.forget), (True, "Mud-slap"), choice.reason)

    def test_an_hm_is_never_forgotten(self) -> None:
        choice = learn_choice(member("Zigzagoon", 20, ["Cut", "Surf", "Strength", "Rock Smash"], 50, 50, 1), "Headbutt")
        self.assertFalse(choice.learn, choice.reason)
        choice = learn_choice(member("Zigzagoon", 20, ["Cut", "Growl", "Surf", "Strength"], 50, 50, 1), "Headbutt")
        self.assertEqual(choice.forget, "Growl")

    def test_fault_no_margin_churns_for_a_trifle(self) -> None:
        """The margin is what keeps a moveset: Pound (40) for Tackle (35 x .95) is a trifle."""
        self.assertFalse(learn_choice(member("Zigzagoon", 20, ["Tackle", "Headbutt", "Surf", "Strength"], 50, 50, 1), "Pound").learn)

    def test_needs_rest(self) -> None:
        self.assertIsNone(needs_rest((member("Mudkip", 14, ["Tackle"], 30, 42, 1), member("Poochyena", 4, ["Tackle"], 2, 17, 2))))
        self.assertIn("fainted", needs_rest((member("Mudkip", 14, ["Tackle"], 0, 42, 1), member("Poochyena", 4, ["Tackle"], 17, 17, 2))))
        self.assertIn("low", needs_rest((member("Mudkip", 14, ["Tackle"], 10, 42, 1),)))


class DoubleTests(unittest.TestCase):
    def test_the_move_is_aimed_at_the_foe_it_hurts_most(self) -> None:
        own = [mon("Grovyle", 17, GROVYLE, 37, 49, battler=0), mon("Nincada", 6, ["Scratch", "Leech Life"], 20, 20, pid=2, battler=2)]
        foes = [foe("Geodude", 8, battler=1), foe("Shroomish", 8, battler=3)]
        decision = mind().decide(look(own, foes, kind="trainer", double=True), 0)
        self.assertEqual((decision.move_name, decision.target), ("Absorb", 1))

    def test_a_spread_move_is_halved(self) -> None:
        own = [mon("Wailord", 47, ["Surf", "Tackle"], 200, 226, battler=0)]
        foes = [foe("Geodude", 30, battler=1), foe("Geodude", 30, battler=3)]
        decision = mind().decide(look(own, foes, kind="trainer", double=True), 0)
        surf = next(line for line in decision.values if line.startswith("Surf"))
        self.assertIn(f"{(95 * 1.5 * 4) * 2 * 0.5:.1f}", surf)


# ------------------------------------------------------------------------------------------- the skill on a screen model
class ScreenModel:
    """The battle's screens as the real menus behave (each rule names its decomp source), one frame per tick:
      * the action menu and the move grid: 2 x 2 cursors (bit 0 the column, bit 1 the row; HandleInputChooseAction /
        HandleInputChooseMove: a move slot with no move is skipped);
      * a text that WAITS for A (a printer's arrow) before the next screen;
      * the bag: pockets switched by Left / Right (`src/item_menu.c` GetSwitchBagPocketDirection), a list cursor
        (Up / Down), A opens USE / CANCEL (Task_ItemContext_SingleRow, `sMenu`);
      * the party list (Up / Down), A opens SHIFT / SUMMARY / CANCEL, which closes after a few frames not taking input;
      * the battle's yes/no (Up / Down; A answers).
    `plan` is the order of screens the battle shows; every press is recorded with what was under the cursor."""

    def __init__(self, battle: BattleView, party: list[MonSummary], plan: list[tuple], bag: dict | None = None,
                 balls: tuple = (("Poké Ball", 5),), on_field: set | None = None) -> None:
        self.battle, self.party, self.plan, self.frame = battle, party, list(plan), 0
        self.bag = bag or {"items": ["Potion"], "poke_balls": ["Poké Ball", "Great Ball"], "tms_hms": [], "berries": [],
                           "key_items": []}
        self.balls = balls
        self.pressed: list[tuple] = []
        self.state: dict = {}
        self.chosen: list = []
        self.outcome = 0
        #: (the step-4 verifier's round) the PIDs standing on the field: the party menu REFUSES them (`src/party_menu.c`
        #: "{STR_VAR_1} is already in battle!", printer 6, a WAIT) and takes input again after A
        self.on_field = set(on_field if on_field is not None else (m.pid for m in battle.own if m.hp))
        self.sent_out: list[int] = []
        self._next()

    def _next(self) -> None:
        if not self.plan:
            self.state = {"kind": "over"}
            return
        step = self.plan.pop(0)
        kind = step[0]
        self.state = {"kind": kind, "cursor": 0, "busy": 6, "arg": step[1] if len(step) > 1 else None}
        if kind == "bag":
            self.state.update(pocket="items")
        if kind == "yes_no":
            self.state["cursor"] = step[2] if len(step) > 2 else 0
        if kind == "faint":
            # the party menu the game opens after a faint (`OpenPartyMenuInBattle`, PARTY_ACTION_SEND_OUT)
            self.state = {"kind": "party", "cursor": 0, "busy": 6, "faint": True}
        if kind == "refusal":
            # a battle resumed on the party menu's refusal (`ki17_partymenu_wedge.ss1`): the words wait for A, the
            # cursor on the member refused
            self.state = {"kind": "party_message", "cursor": step[2], "busy": 2, "faint": True, "text": step[1]}
        if kind == "outcome":
            self.outcome = step[1]
            self._next()

    def tick(self, button: str | None, new: bool) -> None:
        self.frame += 1
        s = self.state
        if s.get("busy"):
            s["busy"] -= 1
            return
        if not new or button is None:
            return
        kind = s["kind"]
        self.pressed.append((button, kind, s.get("cursor"), s.get("pocket")))
        if kind == "text":
            if button == "A":
                self._next()
            return
        if kind in ("action", "move"):
            count = 4 if kind == "action" else len(self.battle.own[0].moves)
            c = s["cursor"]
            if button == "Right" and not c & 1 and (c ^ 1) < count:
                s["cursor"] ^= 1
            elif button == "Left" and c & 1:
                s["cursor"] ^= 1
            elif button == "Down" and not c & 2 and (c ^ 2) < count:
                s["cursor"] ^= 2
            elif button == "Up" and c & 2:
                s["cursor"] ^= 2
            elif button == "A":
                self.chosen.append((kind, c))
                self._next()
            return
        if kind == "bag":
            pockets = ["items", "poke_balls", "tms_hms", "berries", "key_items"]
            if button in ("Left", "Right"):
                i = pockets.index(s["pocket"])
                s["pocket"] = pockets[(i + (1 if button == "Right" else -1)) % 5]
                s["cursor"], s["busy"] = 0, 4
            elif button in ("Up", "Down"):
                length = len(self.bag[s["pocket"]]) + 1
                s["cursor"] = max(0, min(length - 1, s["cursor"] + (1 if button == "Down" else -1)))
            elif button == "A":
                self.chosen.append(("bag", s["pocket"], (self.bag[s["pocket"]] + ["CLOSE BAG"])[s["cursor"]]))
                self.state = {"kind": "bag_action", "cursor": 0, "busy": 3}
            return
        if kind in ("bag_action", "party_action"):
            options = ["USE", "CANCEL"] if kind == "bag_action" else self.party_options(s)
            if button in ("Up", "Down"):
                s["cursor"] = max(0, min(len(options) - 1, s["cursor"] + (1 if button == "Down" else -1)))
            elif button == "A":
                self.chosen.append((kind, options[s["cursor"]]))
                if kind == "party_action":
                    member = next(m for m in self.party if m.pid == s["pid"])
                    if s["pid"] in self.on_field or member.hp <= 0:
                        words = (f"{member.species.upper()} is already in battle!" if member.hp > 0
                                 else f"{member.species.upper()} has no energy left to battle!")
                        self.state = {"kind": "party_message", "cursor": s["row"], "busy": 4, "faint": s.get("faint"),
                                      "text": words}
                    else:
                        self.on_field.add(s["pid"])
                        self.sent_out.append(s["pid"])
                        self.state = {"kind": "party", "closing": 5, "cursor": s["row"], "busy": 5}
                else:
                    self._next()
            return
        if kind == "party_message":
            if button == "A":
                self.chosen.append(("message", s["text"]))
                self.state = {"kind": "party", "cursor": s["cursor"], "busy": 3, "faint": s.get("faint")}
            return
        if kind == "party":
            if button in ("Up", "Down"):
                s["cursor"] = max(0, min(len(self.party) - 1, s["cursor"] + (1 if button == "Down" else -1)))
            elif button == "B" and not s.get("faint"):
                # (the step-4 verifier's round) B closes a party menu opened from the action menu: back to the battle's
                # menu (`src/party_menu.c` HandleChooseMonCancel); after a faint the game's menu cannot be closed so
                self.chosen.append(("party", "B"))
                self._next()
            elif button == "A":
                self.chosen.append(("party", self.party[s["cursor"]].pid))
                self.state = {"kind": "party_action", "cursor": 0, "busy": 3, "pid": self.party[s["cursor"]].pid,
                              "row": s["cursor"], "faint": s.get("faint")}
            return
        if kind == "yes_no":
            if button == "Up":
                s["cursor"] = 0
            elif button == "Down":
                s["cursor"] = 1
            elif button == "A":
                self.chosen.append(("yes_no", s["cursor"]))
                self._next()

    @staticmethod
    def party_options(state: dict) -> list[str]:
        return ["SEND OUT", "SUMMARY", "CANCEL"] if state.get("faint") else ["SHIFT", "SUMMARY", "CANCEL"]

    def look(self) -> Observation:
        s = self.state
        kind = s["kind"]
        if kind == "party" and s.get("closing") is not None and not s.get("busy"):
            self._next()
            s, kind = self.state, self.state["kind"]
        if kind == "over":
            screen = ScreenState("OVERWORLD", "overworld", None, False, False, False)
            player = PlayerState(0, 16, "ROUTE 101", "ROUTE101", 5, 5, "down", "walking", 3, 0, 1)
            return Observation(self.frame, screen, player, None, tuple(self.party), None, None, None, self.outcome, (), 0.0)
        ui, waits, state = None, False, "BATTLE"
        accepts = not s.get("busy")
        if kind == "text":
            waits = True
        elif kind == "action":
            ui = MenuView("battle_action", BATTLE_ACTIONS, s["cursor"], accepts, battler=0)
        elif kind == "move":
            ui = MenuView("battle_move", tuple(m.name for m in self.battle.own[0].moves), s["cursor"], accepts, battler=0)
        elif kind == "yes_no":
            ui = MenuView("battle_yes_no", YES_NO, s["cursor"], accepts)
        elif kind == "bag":
            state = "BAG_MENU"
            ui = MenuView("bag", tuple(self.bag[s["pocket"]]) + ("CLOSE BAG",), s["cursor"], accepts, pocket=s["pocket"])
        elif kind == "bag_action":
            state = "BAG_MENU"
            ui = MenuView("bag_action", ("USE", "CANCEL"), s["cursor"], accepts)
        elif kind == "party":
            state = "PARTY_MENU"
            ui = MenuView("party", (), s.get("cursor") or 0, accepts and s.get("closing") is None)
        elif kind == "party_action":
            state = "PARTY_MENU"
            ui = MenuView("party_action", tuple(self.party_options(s)), s["cursor"], accepts)
        elif kind == "party_message":
            # the refusal: the party list stays, not taking input; printer 6 WAITS for A (`eyes/view.py`)
            state, waits = "PARTY_MENU", True
            ui = MenuView("party", (), s["cursor"], False)
        text = s["arg"] if kind in ("text", "yes_no") else s.get("text") if kind == "party_message" else None
        reason = "text printer 6 WAIT" if kind == "party_message" else "text printer 0 CLEAR"
        screen = ScreenState(state, "battle", None, False, waits and accepts, True, wait_reason=reason if waits else None,
                             ui=ui, text=text, scene="a battle")
        battle = self.battle if state == "BATTLE" else None
        bag = BagSummary(self.balls, (), sum(c for _, c in self.balls))
        progress = Progress(3000, (), 1, 1, (258,), ())
        return Observation(self.frame, screen, None, None, tuple(self.party), bag, progress, battle, 0, (), 0.0)


class _Controls:
    def __init__(self, model: ScreenModel) -> None:
        self.model, self.last = model, None

    def wait(self, frames: int):
        for _ in range(frames):
            self.last = None
            self.model.tick(None, False)
            yield

    def tap(self, button: str):
        yield from self.hold(button, 1)
        yield from self.wait(1)

    def hold(self, button: str, frames: int):
        for _ in range(frames):
            new = button != self.last
            self.last = button
            self.model.tick(button, new)
            yield


class _Eyes:
    def __init__(self, model: ScreenModel) -> None:
        self.model = model

    def look(self) -> Observation:
        return self.model.look()


class _Notes:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, look, decision: str, action: str, reason: str, extra: dict | None = None) -> None:
        self.records.append({"decision": decision, "action": action, "reason": reason})


FAST = Pacing(press=(3, 3), gap=(8, 8), think=(2, 2), read_base=2, read_per_char=0.0, read_max=2)


def play(model: ScreenModel, brain: BattleMind, faults: Faults = Faults()):
    notes = _Notes()
    hands = Hands(_Eyes(model), _Controls(model), random.Random("1:pacing"), random.Random("1:choices"), notes,
                  lambda line: None, faults, FAST)
    generator = play_battle(hands, brain, "test")
    for _ in range(200_000):
        try:
            next(generator)
        except StopIteration as done:
            return done.value, hands, notes
    raise AssertionError("the battle skill did not end")


class SkillTests(unittest.TestCase):
    def battle(self, moves=GROVYLE, foe_species="Geodude"):
        return BattleView("trainer", False, 12, 1, (mon("Grovyle", 17, moves, 37, 49, pid=2),), (foe(foe_species, 8),))

    def test_fight_reads_both_grids(self) -> None:
        model = ScreenModel(self.battle(), [member("Grovyle", 17, GROVYLE, 37, 49, 2)],
                            [("text", "HIKER CLARK sent out GEODUDE!"), ("action",), ("move",), ("text", "GROVYLE used ABSORB!"),
                             ("outcome", 1)])
        outcome, hands, _ = play(model, mind())
        self.assertEqual(outcome, "won")
        self.assertEqual(model.chosen, [("action", 0), ("move", 2)], "FIGHT, then Absorb (slot 2: one Down)")
        self.assertEqual([p[0] for p in model.pressed if p[1] == "move"], ["Down", "A"])
        for press in hands.pad.history:
            self.assertTrue(press["gate"] and "NONE" not in press["gate"], press)

    def test_fault_a_blind_grid_picks_the_wrong_move(self) -> None:
        """The same battle with the grid's cursor NOT read (the driver presses Down from wherever it believes the cursor
        is, while the game's cursor stayed on the last move used: Quick Attack, slot 3): Absorb is missed."""
        model = ScreenModel(self.battle(), [member("Grovyle", 17, GROVYLE, 37, 49, 2)],
                            [("action",), ("move",), ("outcome", 1)])
        model.plan[0:0] = []
        original = skill_module.choose_in_grid

        def blind(hands, kind, index, why):
            if kind != "battle_move":
                return (yield from original(hands, kind, index, why))
            for _ in range(index // 2):
                yield from hands.pad.press("Down", why, "NONE (FAULT blind)")
            yield from hands.pad.press("A", why, "NONE (FAULT blind)")
            return True

        skill_module.choose_in_grid = blind
        try:
            model.state["cursor"] = 0
            original_next = model._next

            def start_on_slot_3():
                original_next()
                if model.state["kind"] == "move":
                    model.state["cursor"] = 3

            model._next = start_on_slot_3
            play(model, mind())
        finally:
            skill_module.choose_in_grid = original
        self.assertNotEqual(model.chosen[-1], ("move", 2))

    def test_a_ball_from_the_ball_pocket(self) -> None:
        battle = BattleView("wild", False, 4, None, (mon("Mudkip", 8, ["Tackle", "Growl", "Mud-slap"], 19, 28),),
                            (foe("Wurmple", 2, bar=20),))
        model = ScreenModel(battle, [member("Mudkip", 8, ["Tackle", "Growl", "Mud-slap"], 19, 28, 1)],
                            [("action",), ("bag",), ("text", "Gotcha! WURMPLE was caught!"), ("outcome", 7)])
        brain = mind("Catcher")
        outcome, _, _ = play(model, brain)
        self.assertEqual(outcome, "caught")
        self.assertIn(("bag", "poke_balls", "Poké Ball"), model.chosen)
        self.assertIn(("bag_action", "USE"), model.chosen)
        self.assertIn(("Right", "bag", 0, "items"), model.pressed, "the pocket reached with Right, read")

    def test_a_switch_by_pid_through_shift(self) -> None:
        party = [member("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, 1), member("Grovyle", 16, GROVYLE, 40, 47, 2, 1)]
        battle = BattleView("trainer", False, 12, 1, (mon("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, pid=1),),
                            (foe("Shroomish", 15),))
        model = ScreenModel(battle, party, [("action",), ("party",), ("text", "Go! GROVYLE!"), ("outcome", 1)])
        play(model, mind())
        self.assertEqual(model.chosen[:3], [("action", 2), ("party", 2), ("party_action", "SHIFT")])

    def test_a_refused_switch_goes_back_to_the_battles_menu_and_fights(self) -> None:
        """(the step-4 verifier's weak proof: "the refused-SWITCH B path ... has no live arm"; the README: "no unit test or
        live arm reaches it") The decider switches the badly matched Mudkip for the Grovyle; the GAME refuses the shift (the
        model's party menu: "GROVYLE is already in battle!", printer 6, a WAIT); the skill reads the words (A on the wait),
        tells the decider, closes the party menu with B on its look, and back at the action menu the decider, the Grovyle
        refused, FIGHTS. FAULT `ignore_refusal` (the step-4 skill): the message watched until its bound, the switch fails."""
        party = [member("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, 1), member("Grovyle", 16, GROVYLE, 40, 47, 2, 1)]
        battle = BattleView("trainer", False, 12, 1, (mon("Mudkip", 14, ["Tackle", "Water Gun"], 30, 42, pid=1),),
                            (foe("Shroomish", 15),))
        plan = [("action",), ("party",), ("action",), ("move",), ("text", "MUDKIP used TACKLE!"), ("outcome", 1)]
        model = ScreenModel(battle, party, list(plan), on_field={1, 2})
        outcome, hands, _ = play(model, mind())
        self.assertEqual(outcome, "won")
        self.assertEqual(model.chosen[:5], [("action", 2), ("party", 2), ("party_action", "SHIFT"),
                                            ("message", "GROVYLE is already in battle!"), ("party", "B")])
        self.assertEqual(model.chosen[5], ("action", 0), "back at the battle's menu: FIGHT, the switch not tried again")
        b_press = [p for p in hands.pad.history if p["button"] == "B"]
        self.assertTrue(b_press and "the switch refused" in b_press[0]["gate"], "B pressed on its look, saying why")
        faulty = ScreenModel(battle, party, list(plan), on_field={1, 2})
        self.assertEqual(play(faulty, mind(faults=BattleFaults(ignore_refusal=True)))[0], "the battle: SHIFT could not be chosen")

    # ---------------------------------------------------- (the step-4 verifier's round) the field and the refusal
    def double(self) -> tuple[BattleView, list[MonSummary]]:
        party = FieldTests().double_party()
        own = (mon("Grovyle", 17, GROVYLE, 37, 49, pid=FieldTests.GROVYLE_PID, battler=0),)
        return BattleView("trainer", True, 0x8000 | 12, 1, own, (foe("Geodude", 8, battler=1), foe("Lotad", 9, battler=3))), party

    def test_the_partner_faints_the_field_is_remembered_through_the_party_menu(self) -> None:
        """The battle's text (a look AT the battle: Grovyle standing) then the party menu (no battle view): the one sent in
        is not Grovyle, and the game refuses nothing."""
        battle, party = self.double()
        model = ScreenModel(battle, party, [("text", "NINCADA fainted!"), ("faint",), ("text", "Go! WHISMUR!"), ("outcome", 1)])
        outcome, hands, _ = play(model, mind())
        self.assertEqual(outcome, "won")
        self.assertEqual(len(model.sent_out), 1)
        self.assertNotEqual(model.sent_out[0], FieldTests.GROVYLE_PID)
        self.assertNotIn("message", [c[0] for c in model.chosen], "nothing refused")

    def test_fault_forget_field_is_refused_and_read_and_another_goes_in(self) -> None:
        """FAULT `forget_field` (step 4's replacement): Grovyle is chosen and the game REFUSES it; the skill reads the
        words, presses A on their WAIT, and the next choice goes in (the second layer works on its own)."""
        battle, party = self.double()
        model = ScreenModel(battle, party, [("text", "NINCADA fainted!"), ("faint",), ("text", "Go! SKITTY!"), ("outcome", 1)])
        outcome, hands, _ = play(model, mind(faults=BattleFaults(forget_field=True)))
        self.assertEqual(outcome, "won")
        self.assertIn(("message", "GROVYLE is already in battle!"), model.chosen)
        self.assertEqual(len(model.sent_out), 1)
        self.assertNotEqual(model.sent_out[0], FieldTests.GROVYLE_PID)
        gates = [p["gate"] for p in hands.pad.history if p["button"] == "A"]
        self.assertIn("text printer 6 WAIT", gates, "the refusal's A is pressed on its wait")

    def test_fault_both_layers_off_is_the_verifiers_stuck_battle(self) -> None:
        """FAULTS `forget_field` + `ignore_refusal` (the step-4 code): Grovyle sent, the refusal watched until the bound:
        'the battle: no Pokemon could be sent in', as the verifier reproduced it live."""
        battle, party = self.double()
        model = ScreenModel(battle, party, [("text", "NINCADA fainted!"), ("faint",), ("outcome", 1)])
        outcome, _, _ = play(model, mind(faults=BattleFaults(forget_field=True, ignore_refusal=True)))
        self.assertEqual(outcome, "the battle: no Pokemon could be sent in")
        self.assertEqual(model.sent_out, [])

    def test_both_fell_two_party_menus_two_different_pokemon(self) -> None:
        """Both of a double battle's battlers fainted: the game opens the party menu twice; the battle's look between
        them does not show the first one on the field yet (the model's field stays empty); the skill tells the decider
        whom it sent (`BattleMind.sent`), so the second choice is another and the game refuses nothing."""
        battle, party = self.double()
        party[0] = replace(party[0], hp=0)
        battle = replace(battle, own=())
        model = ScreenModel(battle, party, [("text", "GROVYLE fainted!"), ("faint",), ("text", "Go! SKITTY!"), ("faint",),
                                            ("text", "Go! WHISMUR!"), ("outcome", 1)], on_field=set())
        outcome, _, _ = play(model, mind())
        self.assertEqual(outcome, "won")
        self.assertEqual(len(set(model.sent_out)), 2, model.sent_out)
        self.assertNotIn("message", [c[0] for c in model.chosen], "nothing refused")

    def test_a_battle_resumed_on_the_refusal_reads_it_and_sends_another(self) -> None:
        """The shape of `ki17_partymenu_wedge.ss1`: the party menu's 'SKITTY is already in battle!' on screen at the start,
        the cursor on Skitty, no look at the battle yet: the words are read (A on the wait), Skitty is the member refused
        (the cursor's, and the name agrees), and the other healthy one goes in."""
        # the Skitty at full HP here (the save's is 40/52): by level it would be the one chosen, so only the refusal it
        # was told about keeps it out (revert_step4 B39)
        skitty, taillow, grovyle, mightyena = 0x111, 0x222, 0x333, 0x444
        party = [member("Skitty", 21, ["Tackle", "Assist"], 52, 52, skitty, 0), member("Taillow", 21, ["Peck"], 0, 53, taillow, 1),
                 member("Grovyle", 24, GROVYLE, 0, 59, grovyle, 2), member("Mightyena", 20, ["Bite", "Tackle"], 60, 60, mightyena, 3)]
        battle = BattleView("trainer", True, 0x8000, 1, (mon("Skitty", 21, ["Tackle"], 52, 52, pid=skitty),), (foe("Magnemite", 22),))
        model = ScreenModel(battle, party, [("refusal", "SKITTY is already in battle!", 0), ("text", "Go! MIGHTYENA!"), ("outcome", 1)])
        outcome, hands, _ = play(model, mind())
        self.assertEqual(outcome, "won")
        self.assertEqual([c for c in model.chosen if c[0] == "message"], [("message", "SKITTY is already in battle!")],
                         "the refusal on screen names Skitty: it is not chosen again (one message only)")
        self.assertEqual(model.sent_out, [mightyena])
        faulty = ScreenModel(battle, party, [("refusal", "SKITTY is already in battle!", 0), ("outcome", 1)])
        self.assertEqual(play(faulty, mind(faults=BattleFaults(ignore_refusal=True)))[0],
                         "the battle: the party on screen neither took input nor closed")

    def test_the_questions_are_answered_on_the_option_wanted(self) -> None:
        battle = BattleView("wild", False, 4, None, (mon("Mudkip", 8, ["Tackle"], 19, 28),), (foe("Wurmple", 2),))
        model = ScreenModel(battle, [member("Mudkip", 8, ["Tackle"], 19, 28, 1)],
                            [("yes_no", "Give a nickname to the captured WURMPLE?", 0), ("outcome", 7)])
        outcome, _, _ = play(model, mind())
        self.assertEqual(model.chosen, [("yes_no", 1)], "NO, the cursor moved down first")
        self.assertEqual([p[0] for p in model.pressed], ["Down", "A"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
