"""TEST SIDE (build step 5): unit proofs of the STORY player's decisions, each with its fault half.

    py -3.12 ai_player/gates/test_goals.py        # ~1 s

  TableTests       the eyes' milestone marks (`eyes/view.py` MILESTONE_FLAGS / MILESTONE_VARS) are exactly the milestones'
                   proofs, number by number (`knowledge/milestones.json`, decomp-checked by `extract_milestones.py --verify`)
  MilestoneTests   the current milestone read from the marks, in order; a proof NOT READ is never progress; a waypoint
                   passes on its map; the player's gender resolves "your house" and "next door"
  HintTests        a hint's map is used only after its WORDS were read; `hints_off` never uses one; the rival's steps:
                   ask at the rival's house until "ROUTE 103" is heard, then go, then talk to the rival there
  ErrandTests      the errand priorities by PERSONALITY: training targets from the fight's levels (Trainer most, Story least,
                   never far below), `train_off`; healing at a known centre, at home with MOM, or not at all; shopping by
                   each personality's ball threshold; an item ball before the story; chatting rates by personality
  BossLevelTests   the fights' levels are the decomp's (Roxanne 12/12/15 = ai-agent/knowledge.py BOSS_LEVELS and the
                   VERIFIED human-reference note), and the training target follows from them
  DriftTests       drift only every DRIFT_EVERY steps, for DRIFT_STEPS, always back to the base, logged; none when off
  ChoiceTests      the favourite is a wild species; the starter named or drawn; the questions answered by their words
"""

from __future__ import annotations

import ast
import contextlib
import json
import os
import random
import re
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

from ai_player.brain.goals import (  # noqa: E402
    ASK_ROUNDS, TRAIN_SESSIONS, GoalManager, battles_lost, heard_words, roam_numbers, training_rest,
)
from ai_player.brain.navigator import Navigator, Target  # noqa: E402
from ai_player.eyes.observation import (  # noqa: E402
    BagSummary, BattleView, MonSummary, Observation, PlayerState, Progress, ScreenState, SeenObject, Tile, View,
)
from ai_player.hands.dialogue import busy_reason  # noqa: E402
from ai_player.hands.pad import Hands  # noqa: E402
from ai_player.mode import MAX_LOSSES, HandsBrain  # noqa: E402
from ai_player.eyes.view import MILESTONE_FLAGS, MILESTONE_VARS, milestone_marks  # noqa: E402
from ai_player.knowledge.story import load_story  # noqa: E402
from ai_player.personality import (  # noqa: E402
    DRIFT_CHANCE, DRIFT_EVERY, DRIFT_STEPS, ERRANDS, PersonalityState, choose_favourite, choose_starter, wild_species,
)
from ai_player.skills.story import answer_question  # noqa: E402
from ai_player.world.memory import MapMemory, TileFact, WorldMemory  # noqa: E402

KNOWLEDGE = json.loads((REPO / "ai_player" / "knowledge" / "milestones.json").read_text(encoding="utf-8"))
#: (build step 5.2) the page PROF. BIRCH's lab scene shows after "go see MAY?" (the `ask` step's own words)
BIRCH_GO_SEE = "Get MAY to teach you what it means to be a TRAINER."
CH1 = ["ch1_intro", "ch1_truck", "ch1_mom", "ch1_clock", "ch1_rival_house", "ch1_birch", "ch1_starter", "ch1_lab",
       "ch1_rival_route103", "ch1_pokedex"]


# ------------------------------------------------------------------------------------------------ builders
def marks(**set_to: int) -> tuple[tuple[str, int], ...]:
    names = [name for name, _ in MILESTONE_FLAGS] + [name for name, _ in MILESTONE_VARS]
    unknown = set(set_to) - set(names)
    if unknown:
        raise KeyError(f"not a mark: {sorted(unknown)}")
    return tuple((name, int(set_to.get(name, 0))) for name in names)


def ch1_through(milestone_id: str) -> dict[str, int]:
    """Marks with every chapter-1 milestone up to `milestone_id` (excluded) proven."""
    proofs = [  # each milestone and what proves it, in order
        ("ch1_intro", {"LITTLEROOT_INTRO_STATE": 1}), ("ch1_truck", {"VISITED_LITTLEROOT_TOWN": 1}),
        ("ch1_mom", {"LITTLEROOT_INTRO_STATE": 4}), ("ch1_clock", {"SET_WALL_CLOCK": 1}),
        ("ch1_rival_house", {"LITTLEROOT_RIVAL_STATE": 3}), ("ch1_birch", {"RESCUED_BIRCH": 1}),
        ("ch1_starter", {"SYS_POKEMON_GET": 1, "BIRCH_LAB_STATE": 2}), ("ch1_lab", {"BIRCH_LAB_STATE": 3}),
        ("ch1_rival_route103", {"DEFEATED_RIVAL_ROUTE103": 1}),
        ("ch1_pokedex", {"RECEIVED_POKEDEX_FROM_BIRCH": 1, "SYS_POKEDEX_GET": 1, "ADVENTURE_STARTED": 1}),
        ("ch2_oldale", {}),
    ]
    out: dict[str, int] = {}
    for key, values in proofs:
        if key == milestone_id:
            return out
        out.update(values)
    raise KeyError(milestone_id)


def mon(level: int = 6, hp: int = 20, max_hp: int = 20, pid: int = 1, species: str = "Mudkip") -> MonSummary:
    return MonSummary(slot=0, species=species, dex=258, level=level, hp=hp, max_hp=max_hp, status="", types=("Water",),
                      moves=(), pid=pid, ot_id=1, is_egg=False)


def look(mark_values: dict[str, int] | None = None, party=(), balls: int = 0, money: int = 3000, const: str = "ROUTE101",
         objects=(), gender: str = "BOY", frame: int = 1000, tiles=(), map_number: int = 16) -> Observation:
    screen = ScreenState(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False, waits_for_button=False,
                         in_battle=False)
    player = PlayerState(map_group=0, map_number=map_number, map_name=const, map_const=const, x=10, y=10, facing="down",
                         movement="walking", elevation=3, avatar_flags=1, trainer_id=1, gender=gender)
    rows = (tuple(tiles),) if tiles else ()
    view = View(left=7, right=7, up=5, down=5, rows=rows, objects=tuple(objects), cropped=True)
    progress = Progress(money=money, badges=(), dex_owned=1, dex_seen=1, owned_dex=(258,), flags=(),
                        marks=marks(**(mark_values or {})))
    bag = BagSummary(balls=(("Poké Ball", balls),) if balls else (), healing=(), ball_total=balls)
    return Observation(frame=frame, screen=screen, player=player, view=view, party=tuple(party), bag=bag, progress=progress,
                       battle=None, last_battle_outcome=0, problems=(), cost_ms=0.0)


def person(x: int = 11, y: int = 10, gfx: int = 1, local_id: int = 3, kind: str = "npc") -> SeenObject:
    return SeenObject(kind=kind, x=x, y=y, dx=x - 10, dy=y - 10, local_id=local_id, graphics_id=gfx, facing="down",
                      elevation=3, source="object")


def world_with(*consts: str, current: str | None = None, heard=(), center_from: str | None = None,
               mart_from: str | None = None, grass: bool = False) -> WorldMemory:
    """A world memory that has VISITED each map in `consts` (keys 0:1, 0:2, ...), standing on `current`; an optional
    known POKéMON CENTER / MART entered from the map `center_from` / `mart_from`."""
    world = WorldMemory()
    keys = {}
    for number, const in enumerate(consts, 1):
        key = f"0:{number}"
        memory = MapMemory(key, const, const)
        memory.visits[(1, 1)] = 1
        if grass:
            for x in range(5):
                memory.tiles[(x, 5)] = TileFact(False, False, True, True, None, False, False, 3, "TALL_GRASS", 0, (0, 0))
        world.maps[key] = memory
        keys[const] = key
    for interior, source in ((f"{center_from}_POKEMON_CENTER_1F", center_from), (f"{mart_from}_MART", mart_from)):
        if source is None:
            continue
        key = f"9:{len(world.maps)}"
        world.maps[key] = MapMemory(key, interior, interior)
        world.warps[f"{keys[source]}|5,5"] = {"to": key, "arrival": [3, 8], "uses": 1, "inferred": False}
    world.heard = set(heard)
    if current is not None:
        world._last.key = keys[current]  # noqa: SLF001 - test side: where the player stands
        world._last.xy = (10, 10)  # noqa: SLF001
    return world


class _Everything(set):
    """(build step 5.1) A set that holds everything: a goal manager whose look-around and detour draws are all MADE (the
    step-5 tests ask about other rules; `ExploreTests` ask about these)."""

    def __contains__(self, item) -> bool:
        return True


def manager(personality: str = "Story", gender: str = "BOY", hints_off: bool = False, train_off: bool = False,
            seed: int = 1, quiet: bool = True, errands_off: bool = False, resumed: bool = False) -> GoalManager:
    """A goal manager whose session began with an EMPTY world memory (a New Game: the test's `world_with` maps were all
    stood on in this session), or, `resumed`, one whose first decision reads the maps already known from the world it is
    given (build step 5.1: a run carried on from an earlier run's memory)."""
    state = PersonalityState(personality, random.Random(seed), drift_on=False)
    mgr = GoalManager(load_story(gender), state, random.Random(seed), hints_off=hints_off, train_off=train_off,
                      errands_off=errands_off)
    if not resumed:
        mgr.memory.known_before = set()
    if quiet:
        mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()
    return mgr


def visited_in(world: WorldMemory):
    return lambda const: any(m.const == const and m.visits for m in world.maps.values())


# ------------------------------------------------------------------------------------------------ the tests
class TableTests(unittest.TestCase):
    def test_the_eyes_read_exactly_the_milestones_proofs_number_by_number(self):
        flags, variables = {}, {}
        for milestone in KNOWLEDGE["milestones"]:
            flags.update(milestone["done"]["flags"])
            flags.update({f"TRAINER_{n}": v for n, v in milestone["done"]["trainers"].items()})
            variables.update({n: info["number"] for n, info in milestone["done"]["variables"].items()})
        self.assertEqual(dict(MILESTONE_FLAGS), flags)
        self.assertEqual(dict(MILESTONE_VARS), variables)

    def test_marks_decode_bits_and_u16s(self):
        flag_bytes = bytearray(300)
        flag_bytes[0x51 // 8] |= 1 << (0x51 % 8)  # SET_WALL_CLOCK
        var_bytes = bytearray(0x200)
        index = 2 * (0x4084 - 0x4000)  # BIRCH_LAB_STATE
        var_bytes[index:index + 2] = (3).to_bytes(2, "little")
        got = dict(milestone_marks(bytes(flag_bytes), bytes(var_bytes)))
        self.assertEqual(got["SET_WALL_CLOCK"], 1)
        self.assertEqual(got["RESCUED_BIRCH"], 0)  # the next bit (0x52): FAULT half of the bit arithmetic
        self.assertEqual(got["BIRCH_LAB_STATE"], 3)
        self.assertEqual(got["PETALBURG_GYM_STATE"], 0)


class MilestoneTests(unittest.TestCase):
    def test_chapter_1_in_order_from_the_marks(self):
        story = load_story("BOY")
        world = world_with("INSIDE_OF_TRUCK")
        mgr = manager()
        for milestone_id in CH1[1:]:
            _, current = mgr.milestone(look(ch1_through(milestone_id)), visited_in(world))
            self.assertEqual(current.id, milestone_id)
        self.assertEqual([m.id for m in story.milestones[:10]], CH1)

    def test_the_intro_is_passed_by_its_waypoint_the_truck(self):
        mgr = manager()
        _, at_title = mgr.milestone(look({}), visited_in(WorldMemory()))
        _, in_truck = mgr.milestone(look({}), visited_in(world_with("INSIDE_OF_TRUCK")))
        self.assertEqual(at_title.id, "ch1_intro")
        self.assertEqual(in_truck.id, "ch1_truck")

    def test_a_proof_not_read_is_never_progress(self):
        story = load_story("BOY")
        clock = story.milestones[story.index("ch1_clock")]
        self.assertTrue(clock.done({"SET_WALL_CLOCK": 1}))
        self.assertIsNone(clock.done({}))  # FAULT half: no marks read -> not "done"
        self.assertEqual(story.current({})[1].id, "ch1_intro")

    def test_vars_count_at_least(self):
        story = load_story("BOY")
        lab = story.milestones[story.index("ch1_lab")]
        self.assertFalse(lab.done({"BIRCH_LAB_STATE": 2}))
        self.assertTrue(lab.done({"BIRCH_LAB_STATE": 5}))

    def test_the_route102_waypoint_passes_on_its_map(self):
        mgr = manager()
        values = {**ch1_through("ch2_oldale"), "VISITED_OLDALE_TOWN": 1}
        _, before = mgr.milestone(look(values), visited_in(world_with("OLDALE_TOWN")))
        _, after = mgr.milestone(look(values), visited_in(world_with("OLDALE_TOWN", "ROUTE102")))
        self.assertEqual((before.id, after.id), ("ch2_route102", "ch2_petalburg"))

    def test_the_players_gender_swaps_the_houses(self):
        boy, girl = load_story("BOY"), load_story("GIRL")
        self.assertEqual(boy.resolve("<player_house_2f>"), "LITTLEROOT_TOWN_BRENDANS_HOUSE_2F")
        self.assertEqual(girl.resolve("<player_house_2f>"), "LITTLEROOT_TOWN_MAYS_HOUSE_2F")
        self.assertEqual(boy.resolve("<rival_house_1f>"), girl.resolve("<player_house_1f>"))
        rival = boy.milestones[boy.index("ch1_rival_route103")]
        self.assertEqual(rival.steps[0].map, "LITTLEROOT_TOWN_MAYS_HOUSE_1F")


class HintTests(unittest.TestCase):
    def rival_goal(self, heard=(), const="LITTLEROOT_TOWN", hints_off=False, objects=(), seed=1):
        mgr = manager(hints_off=hints_off, train_off=True, seed=seed)
        mgr.state.errands  # noqa: B018
        world = world_with("LITTLEROOT_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F", "ROUTE103", current=const, heard=heard)
        values = ch1_through("ch1_rival_route103")
        observation = look(values, party=[mon(6)], const=const, objects=objects)
        index, milestone = mgr.milestone(observation, visited_in(world))
        mgr.memory.chat_drawn.update({f"{world.current}|{o.local_id}" for o in objects})  # no chat draws in these tests
        return mgr.next_goal(observation, world, milestone, index)

    def test_heard_words_is_case_and_space_blind_and_needs_the_words(self):
        self.assertTrue(heard_words({"Oh, MAY went out to ROUTE 103 just a little while ago."}, "ROUTE 103"))
        self.assertTrue(heard_words({"went out to route  103".replace(" ", " ")}, "ROUTE 103"))
        self.assertFalse(heard_words({"MAY went out to ROUTE 101"}, "ROUTE 103"))
        self.assertTrue(heard_words(set(), None))

    def test_heard_words_match_whole_words(self):
        """(the step-5 verifier's round 2, 2026-10-14: a substring test heard "LAB" in "not avaiLABle", "BAG" in "BAGgage"
        and "clock" in "o'clock") A hint's words are read only as WHOLE words; their own pages still match."""
        self.assertFalse(heard_words({"This item is not available."}, "LAB"))
        self.assertFalse(heard_words({"Your baggage is heavy"}, "BAG"))
        self.assertFalse(heard_words({"It's 10 o'clock."}, "clock"))
        self.assertFalse(heard_words({"MAY went out to ROUTE 1030"}, "ROUTE 103"))
        # FAULT half: the pages that DO say them (the game's own lines, `knowledge/milestones.json`)
        self.assertTrue(heard_words({"PROF. BIRCH: come by my POKéMON LAB later."}, "LAB"))
        self.assertTrue(heard_words({"Please! Help! In my BAG! There's a POKé BALL!"}, "BAG"))
        self.assertTrue(heard_words({"DAD bought you a new clock to mark our move here."}, "clock"))
        self.assertTrue(heard_words({"Oh, MAY went out to ROUTE\n103 just a little while ago."}, "ROUTE 103"))
        self.assertTrue(heard_words({"It's PETALBURG GYM!"}, "PETALBURG"))
        self.assertTrue(heard_words({"lives right NEXT  DOOR, so"}, "next door"))

    def test_the_reason_quotes_the_page_it_read(self):
        """(the step-5 verifier's round 2: a BRENDAN run's reason said 'the game said: "MAY: Well, it's time to head back to
        the LAB."', the milestone's stored line, never shown in that run) The `go` reason quotes the page the AI READ that
        says the words; of two, the one read most recently in this run."""
        mgr = manager(gender="GIRL")
        brendan = "BRENDAN: We should head back to the LAB."
        birch = "PROF. BIRCH: come by my POKéMON LAB later."
        world = world_with("LITTLEROOT_TOWN", "ROUTE103", current="ROUTE103", heard={brendan, birch, "Hi there!"})
        mgr.memory.pages.update({birch: 3000, brendan: 9000})
        observation = look(ch1_through("ch1_pokedex"), party=[mon(9)], const="ROUTE103", gender="GIRL")
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertEqual(milestone.id, "ch1_pokedex")
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.map), ("go", "LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB"))
        self.assertIn(repr(brendan), goal.reason)
        self.assertNotIn(milestone.hint_said[:30], goal.reason)  # FAULT half: never the stored line
        mgr.memory.pages[birch] = 9500  # read again since: now it is the most recent
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertIn(repr(birch), goal.reason)

    def test_notice_keeps_the_pages_read_on_the_overworld(self):
        mgr = manager()
        base = look(frame=700)
        page = "Oh, MAY went out to ROUTE 103 just a little while ago."
        talking = replace(base, screen=replace(base.screen, waits_for_button=True, text_box_open=True, text=page))
        mgr.notice(talking)
        battle = replace(talking, frame=800, screen=replace(talking.screen, in_battle=True, text="Wild ZIGZAGOON appeared!"))
        mgr.notice(battle)  # FAULT half: a battle's lines are not pages heard (as `world/memory.py` hears them)
        self.assertEqual(mgr.memory.pages, {page: 700})

    def test_before_the_words_it_goes_to_ask_at_the_rivals_house(self):
        """(build step 5.2, the step-5.1 review's finding 6: "it walks to the step's own house with 'nothing was said'") once
        PROF. BIRCH has said "Get MAY to teach you what it means to be a TRAINER." it goes to ask at the rival's house, and
        its reason quotes that page; before it, nobody has told it whom to see: it explores (no walk to the very house
        where the answer is)."""
        goal = self.rival_goal(heard={BIRCH_GO_SEE})
        self.assertEqual((goal.kind, goal.map), ("go", "LITTLEROOT_TOWN_MAYS_HOUSE_1F"))
        self.assertIn("to teach you what it means", goal.reason)
        self.assertNotIn("nothing was said", goal.reason)
        goal = self.rival_goal()
        self.assertEqual((goal.kind, goal.map), ("go", None))  # FAULT half: the walk to the house with nothing said
        self.assertIn("nobody has told it whom to see", goal.reason)

    def test_in_the_rivals_house_it_asks_the_people_there(self):
        goal = self.rival_goal(const="LITTLEROOT_TOWN_MAYS_HOUSE_1F", objects=[person(12, 10, gfx=22, local_id=4)])
        self.assertEqual(goal.kind, "talk")
        self.assertEqual(goal.target.local_id, 4)

    def test_after_the_words_it_goes_to_route_103_with_the_map(self):
        goal = self.rival_goal(heard={"Oh, MAY went out to ROUTE 103 just a little while ago."})
        self.assertEqual((goal.kind, goal.map), ("go", "ROUTE103"))

    def test_on_route_103_it_talks_to_the_one_who_looks_like_the_rival(self):
        may = person(12, 6, gfx=105, local_id=2)
        boy = person(11, 10, gfx=17, local_id=9)
        goal = self.rival_goal(heard={"went out to ROUTE 103"}, const="ROUTE103", objects=[boy, may])
        self.assertEqual((goal.kind, goal.target.graphics_id), ("talk", 105))
        goal = self.rival_goal(heard={"went out to ROUTE 103"}, const="ROUTE103", objects=[boy])
        self.assertEqual(goal.kind, "find")  # FAULT half: nobody who looks like her: it looks for her

    def test_the_rival_seen_earlier_on_this_map_is_sought_where_she_stood(self):
        """(the chapter-1 sweep of 2026-10-14, seeds 1, 4, 6, 9: the AI had walked past MAY on ROUTE 103 while training,
        then, told to find her, looked everywhere but there.) A person remembers where they saw someone."""
        values = ch1_through("ch1_rival_route103")
        for noticed in (True, False):
            mgr = manager(train_off=True)
            world = world_with("LITTLEROOT_TOWN", "ROUTE103", current="ROUTE103", heard={"went out to ROUTE 103"})
            if noticed:  # on the world's ROUTE103, key 0:2
                mgr.notice(look(values, party=[mon(6)], const="ROUTE103", frame=500, map_number=2,
                                objects=[person(12, 3, gfx=105, local_id=2)]))
            observation = look(values, party=[mon(6)], const="ROUTE103", frame=900)
            index, milestone = mgr.milestone(observation, visited_in(world))
            goal = mgr.next_goal(observation, world, milestone, index)
            if noticed:
                self.assertEqual((goal.kind, goal.tile), ("seek", (12, 3)))
            else:  # FAULT half: never seen here: it looks for her
                self.assertEqual(goal.kind, "find")

    def test_hints_off_never_uses_the_words(self):
        goal = self.rival_goal(heard={"went out to ROUTE 103"}, hints_off=True)
        self.assertEqual((goal.kind, goal.map), ("go", None))

    def test_a_go_whose_words_are_unheard_explores_with_no_map(self):
        """(the step-5 verifier, 2026-10-14: the words rule was proven only through the `ask` step) The rival's house was
        asked round and nobody said where she went: the `go ROUTE103` step comes, and without the words it has no map; it
        explores until the words are read, which end the goal."""
        for heard, want in (((), (None, "ROUTE 103")), ({"Oh, MAY went out to ROUTE 103."}, ("ROUTE103", None))):
            mgr = manager(train_off=True)
            mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS  # asked out: the ask step is passed
            world = world_with("LITTLEROOT_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F", "ROUTE103", current="LITTLEROOT_TOWN",
                               heard=heard)
            observation = look(ch1_through("ch1_rival_route103"), party=[mon(6)], const="LITTLEROOT_TOWN")
            index, milestone = mgr.milestone(observation, visited_in(world))
            goal = mgr.next_goal(observation, world, milestone, index)
            self.assertEqual((goal.kind, goal.map, goal.words), ("go", *want), heard)

    def test_a_wordless_hint_heads_only_for_a_place_it_has_been(self):
        """A hint with no words (the ROUTE 101 sign it never read) names nothing a person was told: OLDALE TOWN is headed
        for only once the AI has been there itself; before that it explores."""
        values = ch1_through("ch2_oldale")
        for places, want in ((("LITTLEROOT_TOWN", "ROUTE101"), None), (("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN"),
                                                                       "OLDALE_TOWN")):
            mgr = manager()
            world = world_with(*places, current="LITTLEROOT_TOWN", heard={"back to the LAB"})
            observation = look(values, party=[mon(9)], const="LITTLEROOT_TOWN")
            index, milestone = mgr.milestone(observation, visited_in(world))
            self.assertEqual(milestone.id, "ch2_oldale")
            goal = mgr.next_goal(observation, world, milestone, index)
            self.assertEqual((goal.kind, goal.map), ("go", want), places)

    def test_every_hint_map_is_named_by_what_the_game_says(self):
        """(the step-5 verifier, 2026-10-14: ROUTE 102 was a hint's map though the game never says it) Every hint's words
        are in what is said; its map is NAMED there (a route by its number, a town by its name, a building by what it is,
        the houses by "upstairs" and "next door") or is the map whose own script says the words (heard there); every `go`
        of the milestone heads for that map or another floor of the same building."""
        def place_words(name: str) -> list[str]:
            gendered = {"<player_house_2f>": ["upstairs"], "<rival_house_1f>": ["next door"]}
            if name in gendered:
                return gendered[name]
            route = re.fullmatch(r"ROUTE(\d+)", name)
            if route:
                return [f"ROUTE {route.group(1)}"]
            town = re.fullmatch(r"([A-Z]+)_(TOWN|CITY)", name)
            if town:
                return [town.group(1)]
            inside = re.fullmatch(r"([A-Z]+)_(TOWN|CITY)_(.+)", name)
            return [inside.group(3).split("_")[-1]] if inside else [name]

        def script_map(path: str | None) -> str | None:
            found = re.fullmatch(r"data/maps/(\w+)/scripts\.inc", path or "")
            return None if found is None else re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", found.group(1)).upper()

        def building(name: str | None) -> str:
            return re.sub(r"_\d+F$|_\d+f>$", "", name or "")

        checked = 0
        for raw in KNOWLEDGE["milestones"]:
            hint = raw["hint"]
            if not hint.get("map") or not hint.get("words"):
                continue
            checked += 1
            said = hint["said"].lower()
            self.assertIn(hint["words"].lower(), said, raw["id"])
            named = all(word.lower() in said for word in place_words(hint["map"]))
            self.assertTrue(named or script_map(hint.get("file")) == hint["map"],
                            f"{raw['id']}: its map {hint['map']} is not named in {hint['said']!r}")
            for step in raw["steps"]:
                if step["do"] == "go":
                    self.assertEqual(building(step["map"]), building(hint["map"]), f"{raw['id']}: go {step['map']}")
        self.assertGreaterEqual(checked, 12)


class ErrandTests(unittest.TestCase):
    def goal(self, personality="Story", level=6, hp=20, balls=0, money=3000, heard=(), values=None, const="ROUTE101",
             objects=(), world=None, train_off=False, seed=1):
        mgr = manager(personality, train_off=train_off, seed=seed)
        world = world or world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F",
                                    current=const, heard=heard or {"went out to ROUTE 103"})
        observation = look(values if values is not None else ch1_through("ch1_rival_route103"),
                           party=[mon(level, hp=hp)], balls=balls, money=money, const=const, objects=objects)
        index, milestone = mgr.milestone(observation, visited_in(world))
        mgr.memory.chat_drawn.update({f"{world.current}|{o.local_id}" for o in objects})
        return mgr, mgr.next_goal(observation, world, milestone, index)

    def test_training_targets_by_personality_before_the_rival(self):
        # the rival's L5: Story trains to L6, Catcher to L7, Trainer to L8 (`personality.py` ERRANDS train_margin)
        for personality, margin in (("Story", 1), ("Catcher", 2), ("Trainer", 3)):
            self.assertEqual(ERRANDS[personality].train_margin, margin)
            _, below = self.goal(personality, level=5 + margin - 1)
            self.assertEqual(below.kind, "train", personality)
            self.assertIn(f"target L{5 + margin}", below.reason)
        self.assertLess(ERRANDS["Story"].train_margin, ERRANDS["Catcher"].train_margin)
        self.assertLess(ERRANDS["Catcher"].train_margin, ERRANDS["Trainer"].train_margin)

    def test_it_trains_its_minimum_steps_even_above_the_target(self):
        mgr, goal = self.goal("Story", level=9)
        self.assertEqual(goal.kind, "train")  # never straight in: train_min_steps first
        mgr.memory.fight_prep["ch1_rival_route103"]["steps"] = ERRANDS["Story"].train_min_steps
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", heard={"went out to ROUTE 103"})
        observation = look(ch1_through("ch1_rival_route103"), party=[mon(9)])
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertEqual(mgr.next_goal(observation, world, milestone, index).kind, "go")

    def test_train_off_never_trains(self):
        _, goal = self.goal("Trainer", level=5, train_off=True)
        self.assertEqual(goal.kind, "go")

    def test_training_is_bounded_by_its_sessions(self):
        """(the step-5 verifier, 2026-10-14: the bound existed and nothing checked it) Under the target after
        TRAIN_SESSIONS sessions, it trains no more: no endless grind; it is ready, and says why."""
        for sessions, want in ((TRAIN_SESSIONS - 1, "train"), (TRAIN_SESSIONS, "go")):
            mgr = manager("Trainer")
            mgr.memory.fight_prep["ch1_rival_route103"] = {"steps": 0, "sessions": sessions, "wild": 0, "won": 0,
                                                            "rests": 0, "ready": False}
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", heard={"went out to ROUTE 103"})
            observation = look(ch1_through("ch1_rival_route103"), party=[mon(5)])
            index, milestone = mgr.milestone(observation, visited_in(world))
            goal = mgr.next_goal(observation, world, milestone, index)
            self.assertEqual(goal.kind, want, sessions)
            prep = mgr.memory.fight_prep["ch1_rival_route103"]
            self.assertEqual(prep["ready"], want == "go")
            if want == "go":
                self.assertIn("sessions roamed", prep["why_ready"])

    def test_the_no_training_fault_still_heals_before_the_fight(self):
        """(the step-5 verifier, 2026-10-14: the fault removed the heal before the fight too, so the NOTRAIN arm's HP effect
        was confounded) Under `train_off` the party at 75 % (above the Trainer's 45 %, under HEAL_BEFORE_FIGHT) heals
        before the rival; without the fault the same party trains first (not ready yet)."""
        center = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="ROUTE101", heard={"ROUTE 103"},
                            center_from="OLDALE_TOWN")
        _, faulted = self.goal("Trainer", level=5, hp=15, world=center, train_off=True)
        self.assertEqual(faulted.kind, "heal")
        self.assertIn("a known fight is next", faulted.reason)
        center = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="ROUTE101", heard={"ROUTE 103"},
                            center_from="OLDALE_TOWN")
        _, real = self.goal("Trainer", level=5, hp=15, world=center)
        self.assertEqual(real.kind, "train")

    def test_no_fight_no_training(self):
        _, goal = self.goal("Trainer", level=5, values=ch1_through("ch1_pokedex"), heard={"back to the LAB"})
        self.assertNotEqual(goal.kind, "train")

    def test_hurt_heals_at_a_known_centre_else_at_home_else_not(self):
        center = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", current="ROUTE101",
                            heard={"ROUTE 103"}, center_from="OLDALE_TOWN")
        _, goal = self.goal(hp=5, world=center)
        self.assertEqual((goal.kind, goal.map), ("heal", "OLDALE_TOWN_POKEMON_CENTER_1F"))
        # home once MOM has SAID so (build step 5.1: never by FLAG_RESCUED_BIRCH, which every mark here sets)
        home = world_with("LITTLEROOT_TOWN", "ROUTE101", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", current="ROUTE101",
                          heard={"ROUTE 103", "…But please be careful. If anything happens, you can come home."})
        _, goal = self.goal(hp=5, world=home)
        self.assertEqual((goal.kind, goal.map), ("heal", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F"))
        self.assertIn("MOM said", goal.reason)
        nowhere = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", heard={"ROUTE 103"})
        _, goal = self.goal(hp=5, world=nowhere)
        self.assertNotEqual(goal.kind, "heal")  # FAULT half: no place known, no heal goal
        _, goal = self.goal(hp=20, world=center)
        self.assertNotEqual(goal.kind, "heal")  # full HP: no heal

    def test_a_party_in_danger_heals_again_and_nobody_trains_hurt(self):
        """(the development sweep step5dev7, seed 3) Two walks to heal had failed, so the heal was put aside: in danger
        (under a third) it heals again at once; merely under its heal_below it does not train hurt (the story goes on)."""
        def hurt_goal(hp: int):
            center = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="ROUTE101", heard={"ROUTE 103"},
                                center_from="OLDALE_TOWN")
            mgr = manager("Story")
            mgr.memory.cooldown["heal:OLDALE_TOWN_POKEMON_CENTER_1F"] = 10 ** 6  # put aside after failing
            observation = look(ch1_through("ch1_rival_route103"), party=[mon(5, hp=hp)])
            index, milestone = mgr.milestone(observation, visited_in(center))
            return mgr.next_goal(observation, center, milestone, index)

        danger = hurt_goal(5)  # 25 %: under a third
        self.assertEqual(danger.kind, "heal")
        self.assertIn("in danger: again", danger.reason)
        moderate = hurt_goal(11)  # 55 %: under the Story's 60 %, not in danger
        self.assertNotIn(moderate.kind, ("heal", "train"))

    def test_heal_thresholds_by_personality(self):
        center = lambda: world_with("ROUTE101", "OLDALE_TOWN", current="ROUTE101", heard={"ROUTE 103"},  # noqa: E731
                                    center_from="OLDALE_TOWN")
        # at 11/20 (55 %): Story (heal_below 0.6) heals; Trainer (0.45) goes on
        _, story = self.goal("Story", hp=11, world=center(), level=9)
        _, trainer = self.goal("Trainer", hp=11, world=center(), level=9)
        self.assertEqual(story.kind, "heal")
        self.assertNotEqual(trainer.kind, "heal")

    def test_shopping_by_each_personalitys_ball_threshold(self):
        values = {**ch1_through("ch2_oldale"), "VISITED_OLDALE_TOWN": 1}
        world = lambda: world_with("OLDALE_TOWN", "ROUTE101", current="OLDALE_TOWN", mart_from="OLDALE_TOWN")  # noqa: E731
        _, catcher = self.goal("Catcher", balls=5, values=values, world=world(), const="OLDALE_TOWN")
        _, story = self.goal("Story", balls=5, values=values, world=world(), const="OLDALE_TOWN")
        self.assertEqual(catcher.kind, "shop")  # 5 < Catcher's 8
        self.assertNotEqual(story.kind, "shop")  # 5 >= Story's 4
        _, poor = self.goal("Catcher", balls=0, money=100, values=values, world=world(), const="OLDALE_TOWN")
        self.assertNotEqual(poor.kind, "shop")  # FAULT half: no money, no shopping

    def test_an_item_ball_comes_before_the_story(self):
        ball = person(12, 10, gfx=59, local_id=7, kind="item_ball")
        _, goal = self.goal(level=9, objects=[ball], values=ch1_through("ch1_pokedex"), heard={"LAB"})
        self.assertEqual((goal.kind, goal.target.local_id), ("pick_up", 7))

    def test_chatting_rates_by_personality(self):
        rates = {}
        for personality in ("Catcher", "Trainer"):
            hits = 0
            for seed in range(400):
                mgr = manager(personality, seed=seed)
                world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
                observation = look(ch1_through("ch1_pokedex"), party=[mon(9)], const="OLDALE_TOWN",
                                   objects=[person(12, 10, gfx=22, local_id=4)])
                index, milestone = mgr.milestone(observation, visited_in(world))
                hits += mgr.next_goal(observation, world, milestone, index).kind == "chat"
            rates[personality] = hits / 400
        self.assertLess(abs(rates["Catcher"] - ERRANDS["Catcher"].chat), 0.07)
        self.assertLess(abs(rates["Trainer"] - ERRANDS["Trainer"].chat), 0.07)
        self.assertGreater(rates["Trainer"], rates["Catcher"])


class _FakeEyes:
    def __init__(self, looks: list[Observation]) -> None:
        self.looks = list(looks)

    def look(self) -> Observation:
        return self.looks.pop(0) if len(self.looks) > 1 else self.looks[0]


def battle_look(frame: int, kind: str | None, hp: int = 20) -> Observation:
    """A look during a battle: on its FIRST frame the eyes have no battle view yet (`kind` None)."""
    screen = ScreenState(game_state="BATTLE", screen="battle", menu=None, text_box_open=False, waits_for_button=False,
                         in_battle=True)
    view = None if kind is None else BattleView(kind=kind, double=False, type_flags=0 if kind == "wild" else 8,
                                                opponent_trainer_id=None, own=(), foe=())
    return Observation(frame=frame, screen=screen, player=None, view=None, party=(mon(6, hp=hp),), bag=None,
                       progress=None, battle=view, last_battle_outcome=0, problems=(), cost_ms=0.0)


def drive(generator, budget: int = 1000):
    for _ in range(budget):
        try:
            next(generator)
        except StopIteration as done:
            return done.value
    raise AssertionError("the generator did not end within its budget")


class RestTests(unittest.TestCase):
    """(the step-5 verifier, 2026-10-14) THE TRAINING ROAM'S REST: asked after every battle with no battle limit set (it
    was asked only WITH one, so the rule was dead), stopping under the personality's `heal_below`; and the battle's KIND
    as the eyes first show it during the battle (it was read on the battle's first frame, before the view exists)."""

    def navigator(self, looks: list[Observation], outcome: str = "won") -> Navigator:
        hands = Hands(_FakeEyes(looks), None, random.Random(1), random.Random(1), None, lambda line: None)
        nav = Navigator(hands, WorldMemory(), random.Random(1))

        def battler():
            hands.look()  # the battle's own looks: the battle view is on screen now
            yield
            return outcome

        nav.battler = battler
        return nav

    def test_the_training_rest_stops_under_each_personalitys_heal_below(self):
        at_55 = look(party=[mon(6, hp=11)])
        self.assertIn("under the Story's 60%", training_rest(at_55, ERRANDS["Story"].heal_below, "Story"))
        self.assertIsNone(training_rest(at_55, ERRANDS["Trainer"].heal_below, "Trainer"))  # 55 % > the Trainer's 45 %
        at_40 = look(party=[mon(6, hp=8)])
        self.assertIn("under the Trainer's 45%", training_rest(at_40, ERRANDS["Trainer"].heal_below, "Trainer"))
        self.assertIsNone(training_rest(look(party=[mon(6, hp=20)]), ERRANDS["Story"].heal_below, "Story"))

    def test_a_training_roam_installs_the_rest_and_clears_it(self):
        from ai_player.brain.goals import GoalRunner
        for personality, hp, stops in (("Story", 11, True), ("Trainer", 11, False), ("Trainer", 8, True)):
            nav = self.navigator([battle_look(130, "wild")])
            nav.battle_limit = 3  # a limit left by someone else is not the play brain's: training has none
            runner = GoalRunner(nav.hands, nav, manager(personality), None, lambda line: None)
            runner.roam_hooks()
            self.assertIsNone(nav.battle_limit)
            said = nav.battle_rest(look(party=[mon(6, hp=hp)]))
            self.assertEqual(said is not None, stops, (personality, hp, said))
            runner.clear_roam_hooks()
            self.assertIsNone(nav.battle_rest)
            self.assertIsNone(nav.roam_stop)

    def test_the_walk_to_heal_keeps_out_of_the_grass_and_restores_the_taste(self):
        """(the development sweep step5dev6: every CH1 whiteout was a wild battle on the walk home to heal, by a personality
        that walks through grass at no extra cost) While healing, a grass tile costs HURT_GRASS_COST in its plans."""
        from ai_player.brain.goals import HURT_GRASS_COST, Goal, GoalRunner
        nav = self.navigator([battle_look(130, "wild")])
        nav.grass_cost = 0.0
        runner = GoalRunner(nav.hands, nav, manager("Trainer"), None, lambda line: None)
        seen: list[float] = []

        def there(goal):
            seen.append(nav.grass_cost)
            yield
            return "healed"

        runner._heal_there = there  # noqa: SLF001 - test side: the walk itself is the navigator's
        self.assertEqual(drive(runner._heal(Goal("heal", "hurt"))), "healed")  # noqa: SLF001
        self.assertEqual((seen, nav.grass_cost), ([HURT_GRASS_COST], 0.0))

    def test_an_item_walk_a_battle_ate_is_tried_again(self):
        """(the step-5 verifier's round, the graded CH2 arm) A ROUTE 102 trainer's battle took the walk to an item ball and
        its budget: the walk ended "unreachable", and the ball was given up at once. A battle on the walk is an
        interruption: tried again, up to ITEM_TRIES walks; a walk with no battle that failed is given up."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import ITEM_TRIES, Goal, GoalRunner
        ball = person(12, 10, gfx=59, local_id=7, kind="item_ball")
        for battled, want_tries in ((True, ITEM_TRIES), (False, 1)):
            nav = self.navigator([battle_look(130, "wild")])
            mgr = manager("Catcher")
            runner = GoalRunner(nav.hands, nav, mgr, types.SimpleNamespace(purpose="travel"), lambda line: None)
            walks = []

            def fake_pick_up(hands, navigator, target, why):
                walks.append(why)
                if battled:
                    navigator.battle_log.append((len(walks), "trainer", "won"))
                yield
                return "not picked up: unreachable: no tile from which the item_ball at (12, 10) can be talked to was reached"

            real = goals_module.pick_up
            goals_module.pick_up = fake_pick_up
            try:
                for _ in range(ITEM_TRIES + 1):
                    if f"{nav.world.current}|12,10" in mgr.memory.tried_items:
                        break
                    drive(runner.pursue(Goal("pick_up", "an item ball", target=ball), mgr.story.milestones[0], 0,
                                        lambda seen: 0))
            finally:
                goals_module.pick_up = real
            self.assertEqual(len(walks), want_tries, battled)
            self.assertIn(f"{nav.world.current}|12,10", mgr.memory.tried_items)

    def test_the_navigator_asks_the_rest_with_no_battle_limit(self):
        for rest, want in ((lambda seen: "the party is at 30% of its HP", "rest: the party is at 30% of its HP"),
                           (None, None)):
            nav = self.navigator([battle_look(130, "wild")])
            self.assertIsNone(nav.battle_limit)
            nav.battle_rest = rest
            stop = drive(nav.handle(battle_look(100, None), "training"))
            if want is None:
                self.assertIsNone(stop)
            else:
                self.assertTrue(str(stop).startswith(want), stop)

    def test_the_battles_kind_is_the_one_shown_during_the_battle(self):
        for kind in ("wild", "trainer"):
            nav = self.navigator([battle_look(130, kind)])  # the handle is given the battle's FIRST frame: no view yet
            drive(nav.handle(battle_look(100, None), "training"))
            self.assertEqual(nav.battle_log, [(100, kind, "won")])

    def test_a_stopped_roams_numbers_are_read_from_its_line(self):
        from ai_player.skills.roam_train import RoamReport
        line = RoamReport(steps=37, attempts=41, spins=2, reversals=1, in_place=1, encounters=4, fled=3,
                          interrupted=4).line()
        got = roam_numbers(f"roam: rest: the party is at 40% of its HP: a person stops; {line}")
        self.assertEqual((got["steps"], got["spins"], got["attempts"], got["encounters"]), (37, 2, 41, 4))
        self.assertNotIn("won", got)  # no battler (build step 3): the line is unchanged
        fought = RoamReport(steps=60, attempts=66, encounters=5, fled=1, fought=6, won=3, caught=1, lost=0, trainers=1,
                            interrupted=6).line()
        got = roam_numbers(f"roam: rest: the party is at 40% of its HP: a person stops; {fought}")
        self.assertEqual({k: got[k] for k in ("encounters", "fled", "won", "caught", "lost", "trainers")},
                         {"encounters": 5, "fled": 1, "won": 3, "caught": 1, "lost": 0, "trainers": 1})
        self.assertIsNone(roam_numbers("roam: no grass found: stuck"))

    def test_a_roam_with_a_battler_counts_how_its_battles_ended(self):
        """(the step-5 verifier's round 2: a CH1T roam logged "5 wild encounters, 4 fled" for 5 battles WON) With a battler
        "fled" is the battles RUN from, and the report says how the others ended, by the navigator's record of each; on
        `test_world.EncounterGame` (a wild battle every 5th step onto grass), the battler's outcomes in turn."""
        from ai_player.gates.test_world import EncounterGame, drive as drive_world, rig
        from ai_player.skills.roam_train import roam_train
        rows = ["##############"] + ['#' + '"' * 12 + '#' for _ in range(6)] + ["##############"]
        game = EncounterGame({"MEADOW": rows}, ("MEADOW", (1, 1)), every=5)
        hands, nav, world, notes, lines = rig(game, seed=2, personality="Catcher")
        outcomes = ["won", "ran", "won", "caught", "won"]

        def battler():
            hands.look()  # the battle on screen: its kind
            game.battle.after = 2  # it ends by itself
            yield from hands.pad.idle(4, "the battle plays")
            return outcomes[(len(nav.battle_log)) % len(outcomes)]

        nav.battler = battler
        outcome = drive_world(roam_train(hands, nav, 60), budget=200_000)
        self.assertTrue(outcome.startswith("roamed"), outcome)
        m = next(r["extra"] for r in notes.records if r["decision"] == "roam")
        played = [o for _, _, o in nav.battle_log]
        self.assertGreaterEqual(len(played), 5, played)
        self.assertEqual((m["encounters"], m["fought"], m["trainers"]), (len(played), len(played), 0))
        self.assertEqual((m["fled"], m["won"], m["caught"], m["lost"]),
                         (played.count("ran"), played.count("won"), played.count("caught"), 0))
        self.assertLess(m["fled"], m["encounters"])  # FAULT half: not every battle that ended with no stop was fled
        self.assertIn(f"{played.count('won')} won", outcome)


class LossTests(unittest.TestCase):
    """(the step-5 verifier, 2026-10-14) Every battle LOST counts, the ones inside a goal too (only a scene's were), and
    MAX_LOSSES ends the run."""

    class _Hands:
        def __init__(self) -> None:
            self.told: list[str] = []

        def tell(self, line: str) -> None:
            self.told.append(line)

    class _Nav:
        def __init__(self, outcomes: list[str]) -> None:
            self.battle_log = [(n, "wild", outcome) for n, outcome in enumerate(outcomes)]

    def test_losses_inside_goals_count_and_end_the_run(self):
        self.assertEqual(battles_lost([(1, "wild", "lost"), (2, "trainer", "won"), (3, "trainer", "lost")]), 2)
        hands, report = self._Hands(), {"losses": 0}
        self.assertIsNone(HandsBrain._count_losses(hands, self._Nav(["won", "lost", "ran", "lost"]), report))
        self.assertEqual((report["losses"], len(hands.told)), (2, 2))
        outcomes = ["lost"] * MAX_LOSSES
        stop = HandsBrain._count_losses(hands, self._Nav(outcomes), report)
        self.assertEqual(report["losses"], MAX_LOSSES)
        self.assertIn(f"{MAX_LOSSES} battles lost", stop)


class _LoopPad:
    """The play loop's pad: its frame count and its waits (each frame one `yield`)."""

    def __init__(self) -> None:
        self.frames = 0
        self.presses = 0
        self.history: list[dict] = []

    def think_frames(self) -> int:
        return 3

    def idle(self, frames: int, reason: str):
        for _ in range(frames):
            self.frames += 1
            yield

    def busy(self, reason: str):
        yield from self.idle(10, reason)

    def finish(self) -> None:
        pass


class _LoopHands:
    """The play loop's hands: every look is `screen` (its watchers told, as the real hands tell them); (build step 5.1)
    `screen` may be a function of the pad's frames (a screen that changes as time passes)."""

    def __init__(self, screen) -> None:
        self.pad = _LoopPad()
        self.screen = screen
        self.last = screen if isinstance(screen, Observation) else None
        self.watchers: list = []
        self.told: list[str] = []
        self.notes: list[tuple] = []

    def look(self) -> Observation:
        seen = self.screen if isinstance(self.screen, Observation) else self.screen(self.pad.frames)
        for watcher in list(self.watchers):
            watcher(seen)
        self.last = seen
        return seen

    def tell(self, line: str) -> None:
        self.told.append(line)

    def note(self, decision: str, action: str, reason: str, extra: dict | None = None) -> None:
        self.notes.append((decision, action, reason, extra))

    def say(self, line: str) -> None:
        pass


class PlayLoopTests(unittest.TestCase):
    """(the step-5 verifier's round 2, 2026-10-14: its mutant V6, the loop's `_count_losses` call replaced by None, and V4,
    `STORY_PATIENCE` checked only when the player is free, both passed every test, because no test drove the play loop)
    The REAL `HandsBrain._play` loop, its goal manager real, with a goal runner and a screen that stand in for the game:
    every pursued goal loses a battle (the loop must end at MAX_LOSSES, each loss told); a screen that never frees (the
    loop must end on STORY_PATIENCE); goals that never move the story (the same). (R5, 2026-10-28) And how a run ENDS
    "done": on a free screen, what was on screen played out first (`test_r5_*`; `run_loop`'s `settle` stands in for
    `play_out`, and (R5's fix round) its `frames` drives the loop through the brain's REAL frame bound, `_bounded`)."""

    PER_GOAL = 1000  # frames a stand-in goal takes
    PER_TRAIN = 20_000  # (build step 5.1) frames a stand-in training session takes
    PER_SCREEN = 5000  # frames a stand-in `play_out` takes on a screen that never frees

    def run_loop(self, screen, lose: bool = False, budget: int = 60_000, heard=(), win_training: bool = False,
                 arrived_at: int | None = None, effect=None, personality: str = "Story", settle=None,
                 frames: int | None = None, setup=None, play_kwargs: dict | None = None, patches: dict | None = None,
                 world=None):
        from ai_player import mode as mode_module
        from ai_player.world.memory import Transition

        world = world if world is not None else world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", heard=heard)
        if arrived_at is not None:  # (build step 5.1) a map change landed at this frame (a scene's, say)
            world.transitions.append(Transition(arrived_at, "0:1", "0:2", "warp", "scene", (7, 15), (6, 5), None))
        nav = types.SimpleNamespace(battle_log=[], take_changes=lambda: [], stats=types.SimpleNamespace(steps=0), world=world,
                                    battler=None, answer=None, on_menu=None)
        # (build step 5.2, the verifier's round) the navigator's own `story_moved`, recorded: the loop asks it at every
        # milestone change
        nav.moved = []
        nav.story_moved = lambda: (nav.moved.append(hands.pad.frames), "nothing to forget")[1]
        hands = _LoopHands(screen)
        hands.starts = []  # the pad's frames at which each goal was pursued
        pursued: list[str] = []
        screens: list[str] = []
        per_goal, per_train = self.PER_GOAL, self.PER_TRAIN

        class Runner:
            def __init__(self, hands_, nav_, manager_, mind_, tell_) -> None:
                self.nav = nav_
                self.manager = manager_
                self.roams, self.heals, self.shopping, self.picked = [], [], [], []
                self.saver = None  # (R1) set by the play brain when it keeps a memory file, as on the real GoalRunner

            def pursue(self, goal, milestone, index, current):
                pursued.append(goal.kind)
                hands.starts.append(hands.pad.frames)
                if goal.kind == "save" and self.saver is not None:
                    # (R1) the real GoalRunner's save branch (`brain/goals.py` pursue): the play brain's own save
                    outcome = yield from self.saver(goal)
                    return outcome.startswith("saved"), outcome
                if effect is not None:  # (build step 5.2) what the goal brings, as the world memory sees it
                    result = effect(goal, world, self)
                    if result is not None:  # the goal's own (ok, outcome)
                        hands.pad.frames += per_goal
                        hands.pad.presses += 5  # it walked: pressed, with nothing new unless `effect` brought it
                        yield
                        return result
                if goal.kind == "train" and win_training:
                    # a training session that WINS a battle (the real runner's own bookkeeping of the session)
                    hands.pad.frames += per_train
                    self.manager.prep(milestone)["sessions"] += 1
                    nav.battle_log.append((hands.pad.frames, "wild", "won"))
                    yield
                    return True, "roamed: 1 wild battle won"
                hands.pad.frames += per_goal
                yield
                if lose:
                    nav.battle_log.append((hands.pad.frames, "wild", "lost"))
                    return False, "not done: the battle was lost"
                return False, "not done: nothing came of it"

        def play_out(hands_, nav_, why):
            screens.append(why)
            if settle is not None:
                # (R5) the test's own stand-in (hands, nav, why): it may free the screen, lose a battle, or stop with the
                # screen still up
                return (yield from settle(hands, nav, why))
            hands.pad.frames += self.PER_SCREEN
            yield
            return "stuck: a screen that does not end"

        brain = HandsBrain.__new__(HandsBrain)
        brain.options = types.SimpleNamespace(target="ch1_pokedex", fault_no_hints=False, fault_no_training=False,
                                              fault_no_errands=False, starter=None, clock=None,
                                              # (chapter 5) the instructed-choice skill's faults, off
                                              fault_no_instructed=False, fault_instructed_misstep=False)
        brain.navigator, brain.world, brain.seed, brain._say, brain.play_report = nav, world, 5, (lambda line: None), None
        # (R5's fix round, R5-F1) the run's frame budget: with `frames`, the loop is driven through the brain's REAL bound
        # (`HandsBrain._bounded`, as `play` drives `_skill`), one frame per `yield`; without it, a budget no test reaches
        brain.settings = types.SimpleNamespace(frames=frames if frames is not None else 10 ** 9)
        if setup is not None:  # (R1) the brain's memory file and what else a test sets before the loop
            setup(brain, hands)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(mode_module, "GoalRunner", Runner))
            stack.enter_context(mock.patch.object(mode_module, "play_out", play_out))
            for name, value in (patches or {}).items():
                stack.enter_context(mock.patch.object(mode_module, name, value))
            game = brain._play(hands, types.SimpleNamespace(name=personality), **(play_kwargs or {}))
            reason = drive(game if frames is None else brain._bounded(game, hands), budget)
        self.last_brain = brain
        return reason, hands, pursued, screens, brain.play_report

    def free_screen(self) -> Observation:
        return look(ch1_through("ch1_rival_route103"), party=[mon(6)], const="ROUTE101")

    def test_battles_lost_inside_goals_end_the_play_loop(self):
        reason, hands, pursued, screens, report = self.run_loop(self.free_screen(), lose=True)
        self.assertEqual(reason, f"stuck: {MAX_LOSSES} battles lost (MAX_LOSSES {MAX_LOSSES})")
        self.assertEqual(len(pursued), MAX_LOSSES)  # it ended at the pass after the last loss, not later
        told = [line for line in hands.told if line.startswith("a battle was LOST")]
        self.assertEqual([line.split(" (", 1)[1].split(")", 1)[0] for line in told],
                         [f"{n} of at most {MAX_LOSSES}" for n in range(1, MAX_LOSSES + 1)])
        self.assertEqual(report["losses"], MAX_LOSSES)
        self.assertFalse(any("the loop counted" in line for line in hands.told))  # the end agrees with the loop
        # FAULT half: the same goals WON nothing and lost nothing: the loop goes on to its patience
        reason, hands, pursued, _, report = self.run_loop(self.free_screen(), lose=False)
        self.assertTrue(reason.startswith("stuck: no progress for"), reason)
        self.assertEqual(report["losses"], 0)

    def test_patience_ends_a_screen_that_never_frees(self):
        base = self.free_screen()
        stuck = replace(base, screen=replace(base.screen, text_box_open=True, waits_for_button=True, script_running=True,
                                             text="..."))
        reason, hands, pursued, screens, _ = self.run_loop(stuck, budget=20_000)
        self.assertTrue(reason.startswith("stuck: no progress for"), reason)
        frames = int(reason.split("no progress for ", 1)[1].split(" ", 1)[0])
        self.assertGreater(frames, mode_module_patience())
        self.assertLessEqual(frames, mode_module_patience() + self.PER_SCREEN + 100)  # at the first pass past it
        self.assertEqual(pursued, [])  # never free: no goal was chosen
        # every pass played the screen out (and waited for it to settle) until the patience ran out: no more passes
        self.assertTrue(mode_module_patience() // (self.PER_SCREEN + 10) <= len(screens)
                        <= mode_module_patience() // self.PER_SCREEN + 1, len(screens))

    def test_patience_ends_goals_that_never_move_the_story(self):
        reason, hands, pursued, screens, report = self.run_loop(self.free_screen())
        self.assertTrue(reason.startswith("stuck: no progress for"), reason)
        self.assertIn("since Find the rival on ROUTE 103", reason)
        self.assertEqual(screens, [])
        self.assertGreaterEqual(len(pursued) * self.PER_GOAL, mode_module_patience())
        self.assertEqual(report["progress"], [])  # goals that keep FAILING are no progress (build step 5.1)

    def test_progress_while_training_keeps_the_patience(self):
        """(build step 5.1, the step-5 review's finding 2: `changed_at` was reset only by a milestone, so a long training
        stint toward a higher target, ROXANNE's, would end as "stuck") Through the REAL loop: every training session WINS a
        battle (`PER_TRAIN` frames each, all `TRAIN_SESSIONS` of them together longer than `STORY_PATIENCE`): the loop
        trains every session and is not stopped while it does; the goals after it, which make no progress, still are."""
        from ai_player.brain.goals import TRAIN_SESSIONS
        told = "Oh, MAY went out to ROUTE 103 just a little while ago."
        reason, hands, pursued, _, report = self.run_loop(self.free_screen(), heard={told}, win_training=True,
                                                          budget=200_000)
        self.assertGreater(TRAIN_SESSIONS * self.PER_TRAIN, mode_module_patience())  # the stint outlasts the old patience
        self.assertEqual(pursued.count("train"), TRAIN_SESSIONS, pursued)  # FAULT half: the old rule stops it at 6
        self.assertEqual(len(report["progress"]), TRAIN_SESSIONS)
        self.assertTrue(all("battles won while training" in " ".join(p["what"]) for p in report["progress"]))
        self.assertTrue(reason.startswith("stuck: no progress for"), reason)  # and failing goals still end the run
        frames = int(reason.split("no progress for ", 1)[1].split(" ", 1)[0])
        self.assertLessEqual(frames, mode_module_patience() + self.PER_GOAL + 100)
        last = report["progress"][-1]["pad_frames"]
        self.assertGreater(hands.pad.frames - last, mode_module_patience())

    def test_progress_counts_a_heal_at_most_a_few_times_a_milestone(self):
        """(build step 5.1) A heal is progress, but heal, get hurt, heal again is not: `HEAL_RESETS_MAX` a milestone; the
        other kinds, each by its own measure, a step up from the snapshot before."""
        from ai_player.mode import HEAL_RESETS_MAX
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101")
        runner = types.SimpleNamespace(heals=[], picked=[], shopping=[])
        report = {"won_training": 0}
        seen: dict = {}
        base = look(ch1_through("ch1_rival_route103"), party=[mon(6)])
        self.assertEqual(HandsBrain._progress(base, world, runner, report, seen), [])  # the first call: the snapshot
        counted = 0
        for _ in range(HEAL_RESETS_MAX + 3):
            runner.heals.append("healed")
            counted += bool(HandsBrain._progress(base, world, runner, report, seen))
        self.assertEqual(counted, HEAL_RESETS_MAX)
        for change, what in ((lambda: report.update(won_training=1), "battles won while training"),
                             (lambda: None, None),
                             (lambda: runner.picked.append("an item"), "an item"),
                             (lambda: runner.shopping.append("POKé BALL x5: bought"), "an item"),
                             (lambda: world.maps.update({"0:9": MapMemory("0:9", "ROUTE103", "ROUTE103")}), "a map")):
            change()
            moved = HandsBrain._progress(base, world, runner, report, seen)
            if what is None:
                self.assertEqual(moved, [])  # FAULT half: nothing changed, nothing counted
            else:
                self.assertTrue(any(what in m for m in moved), moved)
        moved = HandsBrain._progress(look(ch1_through("ch1_rival_route103"), party=[mon(7)]), world, runner, report, seen)
        self.assertTrue(any("a level gained" in m for m in moved), moved)


    # ---- build step 5.1: PACING, the step-5 verifier's FAILURE (b), through the real loop
    def test_the_screen_settles_after_a_map_change_before_a_goal(self):
        """A goal chosen on the frame a scene's map change landed (live arm CH1M: 'goal chat' 2 frames after PROF. BIRCH's
        scene put the player in his lab) met the scene's text and waited 1,200 frames: the screen must stay free
        `SETTLE_FREE` frames after a map change before a goal is chosen."""
        from ai_player.mode import SETTLE_FREE
        free = self.free_screen()
        reason, hands, pursued, _, _ = self.run_loop(lambda frames: replace(free, frame=free.frame + frames),
                                                     arrived_at=free.frame, budget=20_000)
        self.assertTrue(pursued, reason)
        self.assertGreaterEqual(hands.starts[0], SETTLE_FREE)  # FAULT half: with no settle the first goal starts at f3

    def test_a_goal_waits_when_a_scene_began_while_it_decided(self):
        """The scene began during the decision's thinking pause: the goal is not pursued (`dropped`), the scene is played
        first (`play_out`), and the next decision is made after it."""
        free = self.free_screen()
        scene = replace(free, screen=replace(free.screen, text_box_open=True, waits_for_button=True, script_running=True,
                                             text="PROF. BIRCH: So, Milo."))

        def screen(frames: int) -> Observation:
            return scene if 2 <= frames < 5003 else free  # free to decide at f0, a scene from f2 (inside the pause)

        reason, hands, pursued, screens, report = self.run_loop(screen, budget=20_000)
        dropped = [g for g in report["goals"] if g.get("ok") is None and "dropped" in str(g.get("outcome"))]
        self.assertEqual(len(dropped), 1, report["goals"][:3])  # FAULT half: without the check it is pursued at once
        self.assertTrue(screens, "the scene was played")
        self.assertGreater(hands.starts[0], 5000)  # the first goal pursued is decided after the scene
        # (the step-5.1 verifier's second round) the dropped goal's END is recorded where it was dropped: the scene after
        # it is no goal's frames (`rate_step5.goal_spans`)
        ends = [n for n in hands.notes if n[0] == "goal_end"]
        self.assertEqual(ends[0][2], "dropped: a scene began while it decided")
        self.assertLess(ends[0][3]["frames"], 100)

    def test_a_scene_soon_after_a_map_change_comes_before_any_goal(self):
        """(the step-5.1 verifier's second round: its mutant V9, SETTLE_FREE 30 -> 1, was caught by no test: the test above
        asks only that the first goal starts at SETTLE_FREE or later, which any value meets) A scene that begins
        SETTLE_FREE - 10 frames after the map change (PROF. BIRCH's lab began within 25) is played BEFORE any goal is
        chosen: no goal is dropped for it, and the first goal is pursued after it."""
        from ai_player.mode import SETTLE_FREE
        free = self.free_screen()
        scene = replace(free, screen=replace(free.screen, text_box_open=True, waits_for_button=True, script_running=True,
                                             text="PROF. BIRCH: So, Milo."))
        begins = SETTLE_FREE - 10

        def screen(frames: int) -> Observation:
            seen = scene if begins <= frames < 5000 else free
            return replace(seen, frame=free.frame + frames)

        reason, hands, pursued, screens, report = self.run_loop(screen, arrived_at=free.frame, budget=20_000)
        self.assertGreater(begins, 0)
        self.assertTrue(screens, "the scene was played")
        dropped = [g for g in report["goals"] if g.get("ok") is None]
        self.assertEqual(dropped, [])  # FAULT half (SETTLE_FREE 1): a goal chosen at f10, then dropped or pursued
        self.assertGreater(hands.starts[0], 5000)

    # ---- (R5, backlog item R5 "a FREE-SCREEN precondition", 2026-10-28) "done" waits for a free screen, through the real
    # loop: before R5 the run ended "done" on the pass's look, whatever was on screen (`mode.py` `_settle_before_done`,
    # `_end_screen`; mutants G347-G351). (R5's fix round, 2026-10-28: the adversarial review's findings R5-F1, F2, F4, F5,
    # F6 and the independent sweep's 13 survivors S04-S56, each asserted below; mutants G352-G371)
    R5_WHY = "ch1_pokedex reached: what is on screen first"

    def r5_looks(self) -> tuple[Observation, Observation]:
        """A look PAST the target (every chapter-1 proof holds: ch1_pokedex reached) on a FREE screen, and the same look
        with a TEXT BOX up (a script runs and waits for A: MOM's upstairs line after FLAG_SET_WALL_CLOCK)."""
        free = look(ch1_through("ch2_oldale"), party=[mon(9)], const="ROUTE101")
        boxed = replace(free, screen=replace(free.screen, text_box_open=True, waits_for_button=True, script_running=True,
                                             text="MOM: How do you like your new room?"))
        return free, boxed

    @staticmethod
    def r5_notes(hands, decision: str) -> list[tuple]:
        return [note for note in hands.notes if note[0] == decision]

    @staticmethod
    def r5_end_line(hands) -> str:
        return [line for line in hands.told if line.startswith("[AI-GOALS] the end (")][0]

    @staticmethod
    def r5_boxed(seen: Observation) -> Observation:
        return replace(seen, screen=replace(seen.screen, text_box_open=True, waits_for_button=True, script_running=True,
                                            text="a scene's text"))

    def test_r5_done_plays_out_the_screen_first(self):
        """U1 FAULT: the target's proof holds on a look with a TEXT BOX up: what is on screen is played out (`play_out`)
        BEFORE the run ends, the end is on a free screen, and the reason is EXACTLY "done: <target> reached" (the string
        `gates/live_step5.py`'s HONESTY check compares); the end record says free and played out. FAULT half (G347, the
        settle's call deleted; G352, its play-out deleted): `play_out` is never called and the run ends with the box up.
        (R5's fix round, the sweep's S26 and S45) the settle's frames, the play-out's and the pause's, are in its record
        and in the end record."""
        free, boxed = self.r5_looks()
        state = {"freed": False}

        def settle(hands, nav, why):  # play_out's stand-in: presses through the box (200 frames), then the screen is free
            hands.pad.frames += 200
            yield
            state["freed"] = True
            return None

        reason, hands, pursued, screens, report = self.run_loop(lambda frames: free if state["freed"] else boxed,
                                                               budget=5000, settle=settle)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual(screens, [self.R5_WHY])  # played out once, before the end
        self.assertEqual(pursued, [])  # and no goal: the target was reached
        end = report["end_screen"]
        self.assertEqual((end["free"], end["held_by"], end["played_out"], end["settle_stop"]), (True, None, True, None))
        pause = hands.pad.think_frames()
        self.assertEqual(hands.pad.frames, 200 + pause)  # REACH: the play-out and one pause, nothing else
        self.assertEqual((report["settle"]["frames"], end["settle_frames"]), (200 + pause, 200 + pause))  # S26, S45
        self.assertEqual(self.r5_notes(hands, "end")[-1][3]["end_screen"], end)  # in the end note too
        self.assertEqual(self.r5_notes(hands, "end_screen"), [])  # a settled end has nothing to SAY
        self.assertIn("the screen at the end free (played out first", self.r5_end_line(hands))

    def test_r5_done_on_a_free_screen_plays_nothing_out(self):
        """U1 CONTROL: the target's proof holds on a FREE look that stays free: "done" with the same exact reason, `play_out`
        NOT called, no press, and nothing but the decision's pause passes (the pad's frames ARE the pause: the look before
        stopping, `test_r5_one_free_look_before_an_arrival_scene_is_not_a_free_screen` says why); `played_out` False. (The
        spec's "no frame passes" became "only the pause passes": the deviation is in the R5 build report.) (R5's fix
        round, the sweep's S46) the pause is in the end record."""
        free, _ = self.r5_looks()

        def never(hands, nav, why):
            raise AssertionError(f"play_out on a free screen: {why}")
            yield  # noqa: unreachable - a generator, as play_out is

        reason, hands, pursued, screens, report = self.run_loop(free, budget=2000, settle=never)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual((screens, pursued, hands.pad.presses), ([], [], 0))
        pause = hands.pad.think_frames()
        self.assertEqual(hands.pad.frames, pause)  # the one pause, nothing else
        self.assertEqual((report["settle"]["played"], report["settle"]["paused"], report["settle"]["frames"]),
                         (0, pause, pause))
        end = report["end_screen"]
        self.assertEqual((end["free"], end["held_by"], end["played_out"], end["paused"], end["passed"]),
                         (True, None, False, pause, []))  # S46: the pause in the end record

    def test_r5_a_screen_that_will_not_free_still_ends_done_and_says_so(self):
        """U2 FAULT: `play_out` stops with the box still up (its own bound reached): the run STILL ends with exactly "done:
        <target> reached" (the game's proof holds; "stuck" over a proof that holds is a lie, `live_step5.py` HONESTY), the
        screen is played out ONCE (a stop is not retried: LESSONS PL-3), and the unsettled end is SAID: one told line with
        the stop and what holds the screen, one "end_screen" note with them (and its target, frame and play-outs), the
        settle's record and the end record NOT free with what holds it, and the end line naming it. FAULT half (G347:
        no play-out, nothing said; G353: nothing said). (R5's fix round, the sweep's S27, S35, S53 and S55)"""
        _, boxed = self.r5_looks()
        stop = f"stuck: 12 scenes and battles in a row after {self.R5_WHY}"

        def stays(hands, nav, why):
            hands.pad.frames += 300
            yield
            return stop

        reason, hands, pursued, screens, report = self.run_loop(boxed, budget=5000, settle=stays)
        self.assertEqual(reason, "done: ch1_pokedex reached")  # never "stuck"
        self.assertEqual(screens, [self.R5_WHY])
        held = busy_reason(boxed)
        self.assertTrue(held)  # REACH FLOOR: the box is held by something the hands can name
        said = [line for line in hands.told if "reached, but the screen did not free" in line]
        self.assertEqual(len(said), 1, hands.told[-5:])
        self.assertIn(stop, said[0])
        self.assertTrue(said[0].endswith(f"held by: {held}"), said[0])  # S35: what holds it, said
        noted = self.r5_notes(hands, "end_screen")
        self.assertEqual([(note[1], note[2], note[3]["stop"]) for note in noted], [("not free", held, stop)])  # S35
        extra = noted[0][3]
        self.assertEqual((extra.get("target"), extra.get("frame"), extra.get("played")), ("ch1_pokedex", boxed.frame, 1))
        self.assertIs(report["settle"]["free"], False)  # S27
        end = report["end_screen"]
        self.assertEqual((end["free"], end["played_out"], end["settle_stop"]), (False, True, stop))
        self.assertEqual(end["held_by"], held)  # what holds it, in the hands' own words
        self.assertIn(f"the screen at the end NOT free ({held})", self.r5_end_line(hands))  # S55

    def test_r5_one_free_look_before_an_arrival_scene_is_not_a_free_screen(self):
        """(R5, the MEASURED case: the R5 fixture probe's ch2_dad runs, development seeds 5301 and 5302, on the tree before
        R5) the target's proof holds on a look that is free for ONE frame (a warp's exit releases the player), and a scene
        locks the screen on the next (WALLY's tutorial, PETALBURG CITY's ON_FRAME script): the decision's pause sees it
        begin, the scene is played out, the pause after it finds the screen free, and the run ends "done" there. FAULT half
        (G349, the pause and its look deleted): "done" on the one free look, the scene never played."""
        free, boxed = self.r5_looks()
        state = {"freed": False}

        def screen(frames: int) -> Observation:
            return free if frames == 0 or state["freed"] else boxed  # free on the end frame only, then the scene

        def settle(hands, nav, why):
            hands.pad.frames += 3000  # the tutorial, played through
            yield
            state["freed"] = True
            return None

        reason, hands, pursued, screens, report = self.run_loop(screen, budget=5000, settle=settle)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual(screens, [self.R5_WHY])
        pause = hands.pad.think_frames()
        self.assertEqual((report["settle"]["played"], report["settle"]["paused"]), (1, 2 * pause))  # before and after
        end = report["end_screen"]
        self.assertEqual((end["free"], end["played_out"]), (True, True))

    def test_r5_the_measured_ch2_dad_chain_takes_three_rounds(self):
        """(R5's fix round, the review's R5-F2 and the sweep's S23) the MEASURED chain (every R5 A/B run on the held-out
        ch2_dad seeds took THREE pauses, `review/settle_rounds.out`): the target's proof holds on a look free for ONE frame
        (DAD's warp exit); WALLY's tutorial begins on the next (the first pause finds it) and is played out; its own warp
        back frees the player for one frame and the gym's return scene begins (the second pause finds it) and is played
        out; the third pause finds the gym free. Three rounds, two play-outs, the end FREE. FAULT half (G354,
        `DONE_SETTLE_ROUNDS` 2, which every other test allowed): the settle ends after the second pause, "done" on a screen
        NOT free, the failure the A/B graded the OLD arm on."""
        free, boxed = self.r5_looks()
        state = {"outs": 0, "free_at": 0}

        def screen(frames: int) -> Observation:
            if state["outs"] == 0:
                return free if frames == 0 else boxed  # the warp's exit, then WALLY's tutorial
            if state["outs"] == 1:
                return free if frames == state["free_at"] else boxed  # the warp back to the gym, then its return scene
            return free

        def settle(hands, nav, why):
            hands.pad.frames += 1000
            yield
            state["outs"] += 1
            state["free_at"] = hands.pad.frames
            return None

        reason, hands, pursued, screens, report = self.run_loop(screen, budget=10_000, settle=settle)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        pause = hands.pad.think_frames()
        self.assertEqual(screens, [self.R5_WHY, self.R5_WHY])  # both scenes played out
        self.assertEqual((report["settle"]["played"], report["settle"]["paused"]), (2, 3 * pause))  # three rounds
        self.assertTrue(report["end_screen"]["free"], report["end_screen"])  # FAULT half (2 rounds): NOT free
        self.assertEqual(self.r5_notes(hands, "end_screen"), [])

    def test_r5_the_settle_is_bounded(self):
        """(R5, LESSONS PL-4) a screen that frees after each play-out and is busy again after each pause (a chain of scenes
        that never ends) ends the settle after `DONE_SETTLE_ROUNDS` play-outs: the run still ends "done" (the proof holds),
        on a screen NOT free, and says so. FAULT half (G351, the bound removed): the settle never ends (the drive's budget
        runs out). (R5's fix round, the sweep's S54) no play-out STOPPED here (each returned None), so the told line says
        why the screen is not free in its own words: "(a scene still plays)"."""
        from ai_player.mode import DONE_SETTLE_ROUNDS
        free, boxed = self.r5_looks()
        state = {"free_at": None}

        def screen(frames: int) -> Observation:
            return free if state["free_at"] == frames else boxed  # free only on the frame a play-out ended

        def settle(hands, nav, why):
            hands.pad.frames += 100
            yield
            state["free_at"] = hands.pad.frames
            return None

        reason, hands, pursued, screens, report = self.run_loop(screen, budget=5000, settle=settle)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual(len(screens), DONE_SETTLE_ROUNDS)
        self.assertEqual(report["settle"]["played"], DONE_SETTLE_ROUNDS)
        self.assertIsNone(report["settle"]["stop"])  # REACH: no play-out stopped
        self.assertFalse(report["end_screen"]["free"])
        self.assertEqual(len(self.r5_notes(hands, "end_screen")), 1)
        said = [line for line in hands.told if "reached, but the screen did not free" in line]
        self.assertEqual(len(said), 1)
        self.assertIn("(a scene still plays)", said[0])  # S54 (with the fallback gone it says "(None)")

    def test_r5_every_milestone_passed_a_box_is_played_out_first(self):
        """(R5's fix round, the sweep's S04) the OTHER half of the settle's condition: past the LAST required milestone
        (ch4_roxanne's badge) the goal manager reads NO milestone (`brain/goals.py` milestone returns (len, None)), and a run
        ends through `milestone is None`: a box up there is played out first just the same. FAULT half (G355, the settle
        skipped when no milestone is read): "done" at once with the box up."""
        every = {name: 1 for name, _ in MILESTONE_FLAGS}
        every.update({name: 0xFFFF for name, _ in MILESTONE_VARS})
        free = look(every, party=[mon(9)], const="ROUTE101")
        index, milestone = manager().milestone(free, visited_in(world_with("LITTLEROOT_TOWN", "ROUTE101",
                                                                           current="ROUTE101")))
        self.assertIsNone(milestone, f"reach floor: milestone {getattr(milestone, 'id', None)} at index {index}")
        boxed = self.r5_boxed(free)
        state = {"freed": False}

        def settle(hands, nav, why):
            hands.pad.frames += 200
            yield
            state["freed"] = True
            return None

        reason, hands, pursued, screens, report = self.run_loop(lambda frames: free if state["freed"] else boxed,
                                                               budget=5000, settle=settle)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual(screens, [self.R5_WHY])  # played out first
        self.assertEqual((report["end_screen"]["free"], report["end_screen"]["played_out"]), (True, True))

    @staticmethod
    def r5_long_scene(frames_long: int, state: dict):
        """play_out's stand-in for the frame budget's tests: ONE frame per `yield`, as the real pad hands them on (and as
        `_bounded` counts them), then the screen is free."""
        def settle(hands, nav, why):
            for _ in range(frames_long):
                hands.pad.frames += 1
                yield
            state["freed"] = True
            return None
        return settle

    def test_r5_the_frame_budget_never_cuts_a_reached_target_short_of_its_end(self):
        """(R5's fix round, the review's R5-F1, through the brain's REAL bound `_bounded`) the target's proof holds with a
        box up and what is on screen takes LONGER than the frames the run's budget has left: the settle stops while
        `DONE_BUDGET_MARGIN` frames are left, SAYS so (a told line, an "end_screen" note "budget") and the run ends with
        exactly "done: <target> reached" and its end record, NOT free with what holds it. FAULT half (G356, the play-out
        handed on with no budget guard, the R5 build's code): the bound cuts it and the run ends "stopped: not finished
        within 500 frames" with no end record, no end note and no line saying the target was reached, which live_step5's
        HONESTY check reads as a lie (the review's probe, `review/probe_budget_settle.out`); G371: the cut not said.
        CONTROL: the same play-out with room in the budget plays out to its end, free, and says nothing of a budget."""
        from ai_player.mode import DONE_BUDGET_MARGIN
        free, boxed = self.r5_looks()
        state = {"freed": False}
        reason, hands, _, screens, report = self.run_loop(lambda frames: free if state["freed"] else boxed, budget=20_000,
                                                          settle=self.r5_long_scene(2000, state), frames=500)
        self.assertEqual(reason, "done: ch1_pokedex reached")  # FAULT half: "stopped: not finished within 500 frames"
        self.assertEqual(screens, [self.R5_WHY])  # REACH: the play-out began ...
        self.assertFalse(state["freed"])  # ... and was cut, not finished
        self.assertEqual(hands.pad.frames, 500 - DONE_BUDGET_MARGIN)
        self.assertFalse(any("did not finish" in line for line in hands.told))  # the brain's own bound never fired
        record, end = report["settle"], report["end_screen"]
        self.assertEqual((record["budget"], record["played"], record["paused"]), (True, 1, 0))
        self.assertIn("frame budget ran out", record["stop"])
        self.assertEqual((end["free"], end["held_by"], end["settle_stop"]), (False, busy_reason(boxed), record["stop"]))
        said = [line for line in hands.told if "but the run's frame budget ran out" in line]
        self.assertEqual(len(said), 1, hands.told[-4:])
        self.assertIn(f"held by: {busy_reason(boxed)}", said[0])
        self.assertEqual([note[1] for note in self.r5_notes(hands, "end_screen")], ["budget"])
        self.assertEqual(self.r5_notes(hands, "end")[-1][1:3], ("done", "ch1_pokedex reached"))
        # CONTROL: room in the budget: played out to its end, free, no budget said
        state = {"freed": False}
        reason, hands, _, screens, report = self.run_loop(lambda frames: free if state["freed"] else boxed, budget=20_000,
                                                          settle=self.r5_long_scene(2000, state), frames=5000)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertTrue(state["freed"])
        self.assertEqual((report["settle"]["budget"], report["settle"]["stop"], report["end_screen"]["free"]),
                         (False, None, True))
        self.assertEqual(hands.pad.frames, 2000 + hands.pad.think_frames())
        self.assertEqual(self.r5_notes(hands, "end_screen"), [])
        self.assertFalse(any("frame budget" in line for line in hands.told))

    def test_r5_the_frame_budget_cuts_the_decisions_pause_too(self):
        """(R5's fix round, R5-F1, through `_bounded`) the play-out ends with ONE frame of the budget's room left and the
        screen free, and the budget ends inside the decision's pause: the pause is cut, the run ends exactly "done", on a
        free screen, and the cut is said. FAULT half (G357, the pause handed on with no budget guard): "stopped: not
        finished within 2003 frames"."""
        from ai_player.mode import DONE_BUDGET_MARGIN
        free, boxed = self.r5_looks()
        state = {"freed": False}
        limit = 2001  # the play-out's 2000 frames, then one of the pause
        reason, hands, _, screens, report = self.run_loop(lambda frames: free if state["freed"] else boxed, budget=20_000,
                                                          settle=self.r5_long_scene(2000, state),
                                                          frames=limit + DONE_BUDGET_MARGIN)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertTrue(state["freed"])  # REACH: the play-out finished ...
        self.assertEqual((report["settle"]["budget"], report["settle"]["paused"]), (True, limit - 2000))  # ... the pause cut
        self.assertEqual(hands.pad.frames, limit)
        self.assertTrue(report["end_screen"]["free"])
        said = [line for line in hands.told if "but the run's frame budget ran out" in line]
        self.assertEqual(len(said), 1, hands.told[-4:])
        self.assertIn("on a screen that is free", said[0])
        self.assertEqual([(note[1], note[2]) for note in self.r5_notes(hands, "end_screen")], [("budget", "free")])

    def test_r5_a_box_before_the_target_is_the_loops_own_and_the_loop_goes_on(self):
        """U3 CONTROL (R5's second call site, before a goal is chosen after a milestone, holds already: the spec's D7): the
        story moved to the TARGET's milestone, not past it, on a look with a box up: the loop's own path plays it out
        (`play_out` with ITS reason, "<milestone>: what is on screen"), the next goal is chosen only after it, no settle runs
        and the run does not end "done". FAULT half: a settle that also ran short of the target would play it out with
        R5's reason instead."""
        _, boxed = self.r5_looks()
        before = look(ch1_through("ch1_pokedex"), party=[mon(9)], const="ROUTE101")
        boxed_before = replace(before, screen=boxed.screen)
        state = {"freed_at": None}

        def settle(hands, nav, why):
            hands.pad.frames += 200
            yield
            state["freed_at"] = hands.pad.frames
            return None

        reason, hands, pursued, screens, report = self.run_loop(
            lambda frames: before if state["freed_at"] is not None else boxed_before, budget=60_000, settle=settle)
        self.assertEqual(len(screens), 1, screens)
        self.assertTrue(screens[0].endswith(": what is on screen"), screens)  # the loop's own play-out ...
        self.assertNotEqual(screens[0], self.R5_WHY)  # ... not R5's
        self.assertTrue(pursued, reason)  # the loop went on to its goals,
        self.assertGreater(hands.starts[0], state["freed_at"])  # chosen only after the screen was played out
        self.assertNotIn("settle", report)
        self.assertFalse(reason.startswith("done"), reason)

    def test_r5_every_end_records_its_screen(self):
        """U5: a "stuck" end records the screen it ends on too: the patience's end on a screen that never frees reads NOT
        free with what holds it (and no settle fields: the settle is "done"'s), in the report and the end note; CONTROL:
        the MAX_LOSSES end on a free screen reads free. FAULT half (G348, the record's call deleted): no record."""
        base = self.free_screen()
        stuck = replace(base, screen=replace(base.screen, text_box_open=True, waits_for_button=True, script_running=True,
                                             text="..."))
        reason, hands, _, _, report = self.run_loop(stuck, budget=20_000)
        self.assertTrue(reason.startswith("stuck: no progress for"), reason)
        end = report["end_screen"]
        self.assertEqual((end["free"], end["held_by"]), (False, busy_reason(stuck)))
        self.assertNotIn("played_out", end)
        self.assertEqual(self.r5_notes(hands, "end")[-1][3]["end_screen"], end)
        reason, hands, _, _, report = self.run_loop(self.free_screen(), lose=True)
        self.assertTrue(reason.startswith(f"stuck: {MAX_LOSSES} battles lost"), reason)
        self.assertEqual((report["end_screen"]["free"], report["end_screen"]["held_by"]), (True, None))

    def test_r5_a_stuck_end_reads_the_screen_as_it_is_at_the_end(self):
        """(R5's fix round, the sweep's S37) the end record takes a FRESH look: a play-out (the loop's own, short of the
        target) loses the run's last allowed battle and the whiteout frees the screen; the run ends at MAX_LOSSES on the
        next pass, and its end record reads the screen as it is THEN (free), not as the loop's last look saw it before the
        play-out (the box). FAULT half (G360, `_end_screen` reads `hands.last`): NOT free. (Here the stand-in play-out
        takes no look of its own; live, `play_out`'s own looks narrow the gap: not measured.)"""
        base = self.free_screen()  # short of the target: the loop's own play-out path
        boxed = self.r5_boxed(base)
        state = {"freed": False}

        def lose_all(hands, nav, why):
            hands.pad.frames += 100
            yield
            nav.battle_log.extend((hands.pad.frames, "trainer", "lost") for _ in range(MAX_LOSSES))
            state["freed"] = True  # the whiteout ends the scene: the screen is FREE at the end
            return "stuck: the battle was lost (the party fainted: the player whited out)"

        reason, hands, _, screens, report = self.run_loop(lambda frames: base if state["freed"] else boxed, budget=5000,
                                                          settle=lose_all)
        self.assertTrue(reason.startswith(f"stuck: {MAX_LOSSES} battles lost"), reason)
        self.assertEqual(len(screens), 1)  # REACH: the loop's own play-out ran once and brought the losses
        self.assertNotEqual(screens[0], self.R5_WHY)
        self.assertEqual((report["end_screen"]["free"], report["end_screen"]["held_by"]), (True, None))

    def test_r5_the_end_record_carries_the_end_frame(self):
        """(R5's fix round, the sweep's S40) the end record's frame is the END look's: on a screen whose frame moves with
        the pad's frames, a "done" end after the pause records 1000 + the pad's frames at the end. FAULT half (G365, the
        frame dropped): None."""
        free, _ = self.r5_looks()
        reason, hands, _, _, report = self.run_loop(lambda frames: replace(free, frame=1000 + frames), budget=2000)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertGreater(hands.pad.frames, 0)  # REACH: the pause moved the frame
        self.assertEqual(report["end_screen"]["frame"], 1000 + hands.pad.frames)

    def test_r5_the_end_look_closes_the_wait_record(self):
        """(R5's fix round, the sweep's S56: the ORDER R5 chose, now pinned) the end look comes BEFORE the wait watcher
        closes its stretch, so frames that passed after the loop's last look with a box waiting for a press reach the wait
        record: the loop's own play-out waits 100 frames with the box up and no press, then loses the run's last allowed
        battle; the run ends at MAX_LOSSES and its wait record holds the 100 frames. FAULT half (G361, the end record read
        after the watchers close): the stretch closes at the last look, 0. CONTROL: on a "done" end the settle's last look
        is at the end's frame, so there the end look adds nothing (a play-out of 300 frames that stops with the box up:
        the wait is the play-out's 300, in either order)."""
        base = self.free_screen()
        boxed = self.r5_boxed(base)

        def lose_all(hands, nav, why):  # 100 frames with the box up and no press, then MAX_LOSSES: the run ends
            hands.pad.frames += 100
            yield
            nav.battle_log.extend((hands.pad.frames, "trainer", "lost") for _ in range(MAX_LOSSES))
            return "stuck: the battle was lost (the party fainted: the player whited out)"

        reason, hands, _, screens, report = self.run_loop(lambda frames: replace(boxed, frame=1000 + frames), budget=5000,
                                                          settle=lose_all)
        self.assertTrue(reason.startswith(f"stuck: {MAX_LOSSES} battles lost"), reason)  # REACH
        self.assertEqual(report["end_screen"]["frame"], 1100)  # the end look, 100 frames after the pass's
        self.assertEqual(report["waits"]["longest"], 100)  # FAULT half: 0
        # CONTROL: a "done" end whose settle stopped with the box up: its last look IS the end's frame
        _, past = self.r5_looks()

        def stays(hands, nav, why):
            hands.pad.frames += 300
            yield
            return "stuck: a stand-in stop"

        reason, hands, _, _, report = self.run_loop(lambda frames: replace(past, frame=1000 + frames), budget=5000,
                                                    settle=stays)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual((report["end_screen"]["frame"], report["waits"]["longest"]), (1300, 300))

    def test_r5_a_battle_the_settle_lost_is_counted(self):
        """(R5) the settle before "done" can play a battle (a trainer's, a scene's): a loss there is counted as the loop
        counts its own (`_count_losses`: told, in the report), so the end record agrees with the battle log; the run still
        ends "done" (the proof holds). FAULT half (G350, the settle's count deleted): the end tells "the loop counted 0
        battles lost, but the battle log holds 1". (R5's fix round) It is also the CONTROL of
        `test_r5_the_last_allowed_loss_inside_the_settle_ends_it`: one loss, under MAX_LOSSES, and the settle goes on to
        its pause."""
        free, boxed = self.r5_looks()
        state = {"freed": False}

        def lose(hands, nav, why):
            hands.pad.frames += 2000
            yield
            nav.battle_log.append((hands.pad.frames, "trainer", "lost"))
            state["freed"] = True
            return "stuck: the battle was lost (the party fainted: the player whited out)"

        reason, hands, _, screens, report = self.run_loop(lambda frames: free if state["freed"] else boxed, budget=5000,
                                                          settle=lose)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual(report["losses"], 1)
        self.assertTrue(any(line.startswith(f"a battle was LOST (1 of at most {MAX_LOSSES})") for line in hands.told))
        self.assertFalse(any("the loop counted" in line for line in hands.told), hands.told[-4:])
        self.assertEqual(report["settle"]["paused"], hands.pad.think_frames())  # CONTROL (R5-F5): the settle went on

    def test_r5_the_last_allowed_loss_inside_the_settle_ends_it(self):
        """(R5's fix round, the review's R5-F5) a play-out inside the settle loses the run's LAST allowed battle (the
        whiteout frees the screen for a moment, then words follow: MOM's, the nurse's): the settle ends AT ONCE, no pause
        and no second play-out (the run fights no battle past MAX_LOSSES: rate_step5's R5.LOSE3, "no game loss past it"),
        its stop the loop's own MAX_LOSSES reason, the losses counted and told; and the run still ends exactly "done:
        <target> reached" (the proof holds: a stop reason over it is the lie the spec's D3 rejects). FAULT half (G358, the
        settle deaf to the MAX_LOSSES stop, the R5 build's code): it pauses, finds the words and plays them out, again and
        again to its bound. CONTROL: `test_r5_a_battle_the_settle_lost_is_counted` (one loss, under the limit)."""
        free, boxed = self.r5_looks()
        state = {"outs": 0, "free_at": None}

        def screen(frames: int) -> Observation:
            if state["outs"] == 0:
                return boxed  # the battle's scene
            return free if frames == state["free_at"] else boxed  # free for a moment after the whiteout, then words

        def lose_all(hands, nav, why):
            hands.pad.frames += 2000
            yield
            if state["outs"] == 0:
                nav.battle_log.extend((hands.pad.frames, "trainer", "lost") for _ in range(MAX_LOSSES))
            state["outs"] += 1
            state["free_at"] = hands.pad.frames
            return "stuck: the battle was lost (the party fainted: the player whited out)" if state["outs"] == 1 else None

        reason, hands, _, screens, report = self.run_loop(screen, budget=10_000, settle=lose_all)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual(report["losses"], MAX_LOSSES)
        self.assertEqual(sum(1 for line in hands.told if line.startswith("a battle was LOST (")), MAX_LOSSES)
        self.assertEqual(screens, [self.R5_WHY])  # FAULT half: a second play-out after the pause found the words
        record = report["settle"]
        self.assertEqual((record["played"], record["paused"]), (1, 0))
        self.assertEqual(record["stop"], f"{MAX_LOSSES} battles lost (MAX_LOSSES {MAX_LOSSES})")
        self.assertEqual(report["end_screen"]["settle_stop"], record["stop"])
        self.assertTrue(report["end_screen"]["free"])  # the whiteout's free moment: nothing left to say
        self.assertFalse(any("the loop counted" in line for line in hands.told))

    def test_r5_the_settle_names_the_milestones_its_screens_passed(self):
        """(R5's fix round, the review's R5-F6) what is played out after the target can carry the story further (the R5
        A/B's held-out ch2_dad runs ended past ch2_wally: WALLY's tutorial sets its proof): the milestones passed meanwhile
        are named, told, in the settle's record, the end record and the end line, while the loop's own milestone record
        (`report["milestones"]` and the MILESTONE lines, which the graders read) is left as the loop made it. FAULT half
        (G359, the passed milestones not read): an empty list. CONTROL: a settle that passes nothing names nothing (U1
        CONTROL's `passed` [])."""
        _, boxed = self.r5_looks()  # the story AT ch2_oldale, past the target ch1_pokedex
        later = look({**ch1_through("ch2_oldale"), "VISITED_OLDALE_TOWN": 1}, party=[mon(9)], const="ROUTE101")
        state = {"freed": False}

        def settle(hands, nav, why):
            hands.pad.frames += 500
            yield
            state["freed"] = True
            return None

        reason, hands, _, screens, report = self.run_loop(lambda frames: later if state["freed"] else boxed, budget=5000,
                                                          settle=settle)
        self.assertEqual(reason, "done: ch1_pokedex reached")
        self.assertEqual(screens, [self.R5_WHY])  # REACH: the screen was played out, and the story moved meanwhile
        self.assertEqual((report["settle"]["passed"], report["end_screen"]["passed"]), (["ch2_oldale"], ["ch2_oldale"]))
        self.assertIn("the story passed ch2_oldale meanwhile", self.r5_end_line(hands))
        self.assertTrue(any("it passed ch2_oldale while it was played out" in line for line in hands.told))
        self.assertNotIn("ch2_oldale", [m["id"] for m in report["milestones"]])  # the loop's own record, untouched
        self.assertFalse(any(line.startswith("[AI-GOALS] MILESTONE ch2_oldale") for line in hands.told))

    # ---- (R1 + R2, build stage 4: build spec 2026-10-29 sections 3 (c)-(d), 4) THE SAVE WIRING, through the REAL loop:
    # `save_game` stands in for the game's dialog (`r1_saver`: the write's first look calls `on_writing`, 400 frames, then
    # `on_saved`); the memory file is REAL (`game_memory.py`, in a temporary folder). Mutants G374-G392 (revert_step5).
    def r1_setup(self, folder: Path, saving: bool = True, cart: str = "empty", writer=None):
        """The brain's memory file, as `_open_memory` sets it for a run that keeps one (D14); `saving` False is the
        no-save CONTROL's state (`AI_PLAYER_FAULT_NO_SAVE`)."""
        def setup(brain, hands) -> None:
            brain.options.cart, brain.options.host, brain.options.run_dir = cart, "harness", None
            brain._memory_path = folder / "ai_player" / "memory.jsonl"
            brain._saving = saving
            if writer is not None:
                brain._writer = writer(brain)
        return setup

    @staticmethod
    def r1_timed(seen: Observation, play_time) -> Observation:
        return replace(seen, progress=replace(seen.progress, play_time=play_time))

    @staticmethod
    def r1_saver(calls: list):
        def fake_save_game(hands, why, cart_is_own, frames_left, on_writing, on_saved):
            seen = hands.look()
            calls.append({"why": why, "own": cart_is_own, "left": frames_left(), "pad": hands.pad.frames})
            written = on_writing(seen.progress.play_time, seen)
            hands.pad.frames += 400
            yield
            on_saved(hands.look())
            hands.pad.presses += 3
            return "saved" if written is not False else "stuck: the memory of this save could not be written (the game saved)"
        return fake_save_game

    def r1_moment_looks(self) -> tuple[Observation, Observation]:
        """The story AT ch1_lab (play time 0:10), then past it (0:20): ch1_lab, a big story moment, is passed."""
        before = self.r1_timed(look(ch1_through("ch1_lab"), party=[mon(6)], const="ROUTE101"), (0, 10))
        after = self.r1_timed(look(ch1_through("ch1_rival_route103"), party=[mon(6)], const="ROUTE101"), (0, 20))
        return before, after

    def test_r1_a_save_goal_after_a_big_moment(self):
        """D3 through the loop: ch1_lab passed (`_milestone_line` -> `after_milestones`, ids only) makes a save due; the
        next decision's block 1b chooses a `save` goal; the runner plays it through the brain's `_save`; the save's line is
        in the memory file (its header and session line first), stamped with the SAVING look's play time, and the policy
        records it (no second save). FAULT half (the no-save CONTROL's state): no save goal, no file."""
        from ai_player.game_memory import read_book

        before, after = self.r1_moment_looks()
        with tempfile.TemporaryDirectory(prefix="ai_r1_loop_") as tmp:
            folder = Path(tmp)
            calls: list = []
            reason, hands, pursued, _, report = self.run_loop(lambda frames: before if frames < 1500 else after,
                                                              budget=20_000, setup=self.r1_setup(folder),
                                                              patches={"save_game": self.r1_saver(calls)})
            self.assertEqual(pursued.count("save"), 1, pursued)
            self.assertEqual(len(calls), 1)
            self.assertIn("ch1_lab", calls[0]["why"])
            self.assertTrue(calls[0]["own"])  # an `empty` cart is this game's own (D17)
            self.assertIsInstance(calls[0]["left"], int)  # the run's frames left, for the skill's commit check
            self.assertGreater(calls[0]["left"], 10 ** 8)
            book = read_book(folder / "ai_player" / "memory.jsonl")
            self.assertEqual([line["kind"] for line in book.lines], ["header", "session", "save", "saved"])
            save = book.saves()[0]
            self.assertEqual((save["id"], save["play_time"], save["full"]), (1, [0, 20], True))
            self.assertEqual(save["party"], [{"pid": "00000001", "species": "Mudkip"}])
            self.assertEqual(save["where"], {"map": "ROUTE101", "tile": [10, 10]})
            # the payload's parts (D16): the goal manager's KEEP fields, the personality, the battle mind
            memory = save["memory"]
            self.assertEqual(sorted(memory["world"]["maps"]), ["0:1", "0:2"])  # the world memory, by its maps
            self.assertIn("talked", memory["goals"])
            self.assertEqual(memory["personality"]["base"], "Story")
            self.assertEqual(set(memory["battle"]), {"wishes", "met", "wild_met"})
            self.assertTrue(book.header_line["game"].startswith(f"{folder.name}|"), book.header_line)
            # L3 (a)-(b): the registry, filled by the brain's watcher, is in the payload: the party's PID, its species
            self.assertEqual({pid: (entry["species"], entry["how"]) for pid, entry in save["memory"]["mons"].items()},
                             {"00000001": ("Mudkip", "starter")})
            self.assertEqual(report["saves"][0]["outcome"], "saved")
            self.assertEqual(self.last_brain._policy.goal_memory.last_save["id"], 1)
            # a save is counted apart (T4): its decision's pause and its 400 frames
            self.assertEqual(report["spent"].get("save"), hands.pad.think_frames() + 400)
            self.assertTrue(reason.startswith("stuck: no progress"), reason)
        with tempfile.TemporaryDirectory(prefix="ai_r1_loop_") as tmp:
            calls = []
            _, _, pursued, _, report = self.run_loop(lambda frames: before if frames < 1500 else after, budget=20_000,
                                                     setup=self.r1_setup(Path(tmp), saving=False),
                                                     patches={"save_game": self.r1_saver(calls)})
            self.assertNotIn("save", pursued)
            self.assertEqual(calls, [])
            self.assertFalse((Path(tmp) / "ai_player" / "memory.jsonl").exists())
            self.assertNotIn("saves", report)

    def test_r1_a_save_goal_after_a_center_heal(self):
        """D3 through the loop: a heal goal that HEALED at a POKéMON CENTER (`_after_heal` -> the policy) makes a save due,
        and the next decision, on the centre's map with the party healed, saves there. FAULT half: a heal goal that did
        NOT heal (the party healed some other way meanwhile) makes no due and no save."""
        hurt = self.r1_timed(look(ch1_through("ch1_rival_route103"), party=[mon(6, hp=2)], const="ROUTE101"), (0, 10))
        healthy = self.r1_timed(look(ch1_through("ch1_rival_route103"), party=[mon(6)], const="ROUTE101"), (0, 20))
        for center, saves in ((True, 1), (False, 0)):
            with self.subTest(center=center), tempfile.TemporaryDirectory(prefix="ai_r1_heal_") as tmp:
                world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", center_from="ROUTE101")
                inside = next(key for key, memory in world.maps.items() if memory.const.endswith("POKEMON_CENTER_1F"))
                state = {"healed": False}

                def effect(goal, world_, runner, center=center):
                    if goal.kind != "heal":
                        return None
                    world_._last.key = inside  # noqa: SLF001 - test side: it walked into the place it heals at
                    state["healed"] = True
                    return (True, "healed") if center else (False, "the nurse was not reached")

                calls: list = []
                _, _, pursued, _, _ = self.run_loop(lambda frames: healthy if state["healed"] else hurt, budget=20_000,
                                                    effect=effect, world=world, setup=self.r1_setup(Path(tmp)),
                                                    patches={"save_game": self.r1_saver(calls)})
                self.assertEqual(pursued[0], "heal", pursued[:3])
                self.assertEqual(len(calls), saves, pursued[:5])
                if saves:
                    self.assertEqual(pursued[1], "save")  # the decision right after the heal, in the centre
                    self.assertIn("POKéMON CENTER", calls[0]["why"])

    def test_r1_fault_no_save_is_the_old_loop(self):
        """D14's A/B at the loop: the no-save CONTROL with a memory file plays EXACTLY the pre-R1 loop (no memory file):
        the same goals, the same frames, the same lines; with saving on, the same story differs by its save."""
        before, after = self.r1_moment_looks()
        script = lambda frames: before if frames < 1500 else after  # noqa: E731
        runs = []
        for setup in (None, "control", "saving"):
            with tempfile.TemporaryDirectory(prefix="ai_r1_ab_") as tmp:
                chosen = None if setup is None else self.r1_setup(Path(tmp), saving=setup == "saving")
                reason, hands, pursued, _, _ = self.run_loop(script, budget=20_000, setup=chosen,
                                                             patches={"save_game": self.r1_saver([])})
                runs.append((reason, pursued, hands.pad.frames, [l for l in hands.told if "MILESTONE" not in l]))
        self.assertEqual(runs[0], runs[1])
        self.assertNotEqual(runs[0][1], runs[2][1])

    def test_r1_no_save_goal_while_hurt(self):
        """Block 1b waits while the party is hurt (a person heals first); healthy, the same due is a save goal. The hurt
        party is at 40% (under every personality's `heal_below`, above `needs_rest`'s third) with no place to heal known:
        block 1 returns NO heal goal, so only the hurt guard keeps the save back (G375)."""
        from ai_player.brain.saving import SavePolicy

        mgr = manager()
        mgr.saving, mgr.frames_left = SavePolicy(mgr.memory), lambda: 10 ** 6
        mgr.saving.after_milestones(["ch1_lab"])
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101")
        healthy = self.r1_timed(look(ch1_through("ch1_rival_route103"), party=[mon(6)]), (0, 20))
        hurt = replace(healthy, party=(mon(6, hp=8),))
        index, milestone = mgr.milestone(healthy, visited_in(world))
        self.assertTrue(mgr.hurt(hurt))
        self.assertNotIn(mgr.next_goal(hurt, world, milestone, index).kind, ("save", "heal", "find_center"))
        goal = mgr.next_goal(healthy, world, milestone, index)
        self.assertEqual((goal.kind, goal.key), ("save", "save:moment"))
        # CONTROL: without a save policy (no memory file) the healthy decision is never a save
        plain = manager()
        self.assertNotEqual(plain.next_goal(healthy, world, milestone, index).kind, "save")

    def test_r1_a_save_before_the_leader_takes_the_story_goals_place(self):
        """Block 8's wiring: when the story goal is the TALK, the policy is asked (`before_leader`, with the story goal)
        and its save goal comes in the talk's place; any other story goal is returned as it is."""
        from ai_player.brain.goals import Goal
        from ai_player.brain.saving import SaveChoice

        asked: list = []

        class Policy:
            def next_save(self, look_, here, left):
                return None

            def before_leader(self, look_, world_, milestone_, step, story_goal, left):
                asked.append((story_goal.kind, left))
                return SaveChoice("leader", "a save: right before the leader", "save:leader:ch4_roxanne", "ch4_roxanne") \
                    if story_goal.kind == "talk" else None

        mgr = manager()
        mgr.saving, mgr.frames_left = Policy(), lambda: 4321
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101")
        seen = self.r1_timed(look(ch1_through("ch1_rival_route103"), party=[mon(6)]), (0, 20))
        index, milestone = mgr.milestone(seen, visited_in(world))
        for kind, expect in (("talk", "save"), ("go", "go")):
            with mock.patch.object(mgr, "_story_goal", lambda *a, kind=kind: Goal(kind, "the story", milestone.id,
                                                                                  key=f"{kind}:x")):
                self.assertEqual(mgr.next_goal(seen, world, milestone, index).kind, expect)
        self.assertEqual(asked, [("talk", 4321), ("go", 4321)])  # with the run's frames left

    def test_r1_the_end_save_when_due(self):
        """T8: the target (ch1_pokedex, a big moment) reached: after the settle, the due save is made before "done"; the
        end record says `saved_at_end`. CONTROL (too few frames left in the run's budget): no save, SAID, still "done"."""
        from ai_player.game_memory import read_book

        at_target = self.r1_timed(look(ch1_through("ch1_pokedex"), party=[mon(9)], const="ROUTE101"), (0, 10))
        past = self.r1_timed(look(ch1_through("ch2_oldale"), party=[mon(9)], const="ROUTE101"), (0, 20))
        script = lambda frames: at_target if frames < 1500 else past  # noqa: E731
        with tempfile.TemporaryDirectory(prefix="ai_r1_end_") as tmp:
            calls: list = []
            reason, hands, pursued, _, report = self.run_loop(script, budget=20_000, setup=self.r1_setup(Path(tmp)),
                                                              patches={"save_game": self.r1_saver(calls)})
            self.assertEqual(reason, "done: ch1_pokedex reached")
            self.assertEqual(len(calls), 1)
            self.assertNotIn("save", pursued)  # the end save, not a goal
            self.assertIn("ch1_pokedex", calls[0]["why"])
            self.assertTrue(report["end_save"]["saved"])
            self.assertTrue(report["end_screen"]["saved_at_end"])
            self.assertGreaterEqual(calls[0]["pad"], report["settle"]["frames"])  # after the settle's pause
            self.assertEqual(len(read_book(Path(tmp) / "ai_player" / "memory.jsonl").saves()), 1)
        with tempfile.TemporaryDirectory(prefix="ai_r1_end_") as tmp:
            calls = []
            reason, hands, _, _, report = self.run_loop(script, budget=20_000, setup=self.r1_setup(Path(tmp)),
                                                        patches={"save_game": self.r1_saver(calls)}, frames=4000)
            self.assertEqual(reason, "done: ch1_pokedex reached")
            self.assertEqual(calls, [])
            self.assertFalse(report["end_save"]["saved"])
            self.assertFalse(report["end_screen"]["saved_at_end"])
            self.assertTrue(any("no save before putting the game down" in line for line in hands.told), hands.told[-5:])

    def test_r1_an_unwritten_save_line_ends_the_run(self):
        """Section 3 (c): a save line that did not reach the file ends the run "stuck" right after the save (a save the
        memory does not know would stop the next continue). CONTROL: the line reached it, the run goes on."""
        from ai_player.game_memory import MemoryWriter

        before, after = self.r1_moment_looks()

        def broken(brain):
            writer = MemoryWriter(brain._memory_path, None, header={"game": "t", "identity": {}},
                                  session=brain._session("new game", "empty"))
            writer.records = types.SimpleNamespace(written=0, append=lambda record: None, path=brain._memory_path)
            return writer

        with tempfile.TemporaryDirectory(prefix="ai_r1_unwritten_") as tmp:
            reason, _, pursued, _, _ = self.run_loop(lambda frames: before if frames < 1500 else after, budget=20_000,
                                                     setup=self.r1_setup(Path(tmp), writer=broken),
                                                     patches={"save_game": self.r1_saver([])})
            self.assertEqual(reason, "stuck: the memory of this save could not be written (the game saved)")
            self.assertEqual(pursued[-1], "save")

    def test_r1_the_loss_count_is_restored_and_each_loss_is_a_line(self):
        """T5 and D12 (e): a continue whose save had 2 battles lost ends at the FIRST new loss (MAX_LOSSES 3), and each
        loss is a `lost` line. FAULT half: with no restore the same loop loses MAX_LOSSES battles of its own."""
        from ai_player.brain.goals import _Memory
        from ai_player.game_memory import MemoryWriter, MonRegistry, goals_part, read_book

        restored = types.SimpleNamespace(personality={"base": "Story", "favourite": "ZIGZAGOON", "history": [], "draws": 3},
                                         battle={"wishes": {}, "met": {"MAY": 1}, "wild_met": 5}, mons=MonRegistry(),
                                         goals=goals_part(_Memory(talked={"0:1|9"})), losses=2)
        with tempfile.TemporaryDirectory(prefix="ai_r1_losses_") as tmp:
            def writer(brain):
                made = MemoryWriter(brain._memory_path, None, header={"game": "t", "identity": {}},
                                    session=brain._session("new game", "empty"))
                made.write_save(play_time=(0, 5), frame=1, where={"map": "ROUTE101", "tile": [10, 10]}, party=[],
                                why="a test", payload={"world": {}, "losses": 2})
                return made

            reason, hands, pursued, _, report = self.run_loop(self.r1_timed(self.free_screen(), (0, 30)), lose=True,
                                                              setup=self.r1_setup(Path(tmp), writer=writer),
                                                              play_kwargs={"restored": restored})
            self.assertEqual(reason, f"stuck: {MAX_LOSSES} battles lost (MAX_LOSSES {MAX_LOSSES})")
            self.assertEqual(len(pursued), 1)
            self.assertEqual(report["losses"], MAX_LOSSES)
            self.assertFalse(any("the loop counted" in line for line in hands.told))
            lost = [line for line in read_book(Path(tmp) / "ai_player" / "memory.jsonl").lines if line["kind"] == "lost"]
            self.assertEqual([(line["after_save"], line["play_time"]) for line in lost], [(1, [0, 30])])
            # D16: what it remembers, its personality and its battle mind, as of the save
            kept_manager, kept_state, kept_mind = self.last_brain._kept
            self.assertIn("0:1|9", kept_manager.memory.talked)
            self.assertEqual((kept_state.draws, kept_state.favourite), (3, "ZIGZAGOON"))
            self.assertEqual((kept_mind.wild_met, kept_mind.met), (5, {"MAY": 1}))
            self.assertIs(self.last_brain._registry, restored.mons)
        reason, _, pursued, _, _ = self.run_loop(self.free_screen(), lose=True)
        self.assertEqual(len(pursued), MAX_LOSSES)

    def test_r1_continue_mode_never_plays_the_intro(self):
        """Section 3 (e): a CONTINUED game that meets the title never plays the New Game intro: the run ends "stuck".
        FAULT half: the same title in a new game plays the intro."""
        title = replace(look(), player=None, progress=None)
        intro: list = []

        def fake_intro(hands, personality):
            intro.append(hands.pad.frames)
            hands.pad.frames += 10
            yield
            return "the intro did not finish"

        reason, *_ = self.run_loop(title, budget=2000, patches={"play_intro": fake_intro},
                                   setup=lambda brain, hands: setattr(brain, "_continued", object()))
        self.assertEqual(intro, [])
        self.assertIn("never starts a New Game", reason)
        reason, *_ = self.run_loop(title, budget=2000, patches={"play_intro": fake_intro})
        self.assertEqual(len(intro), 1)

    def test_the_play_brain_reads_along_for_its_instructed_menus(self):
        """(chapter 5, 2026-11-05) `_play` makes the instructed-choice skill (`skills/instructed.py`) and puts its reader on
        EVERY look: the instruction is what was read since the player was last free, so a reader that is not on the looks
        reads nothing (the dispatch alone is `InstructedTests`). Here the loop's free screens reached it."""
        reason, hands, *_ = self.run_loop(self.free_screen(), budget=3000)
        skill = self.last_brain._instructed
        self.assertIsNotNone(skill)
        self.assertIn(skill.read_along, hands.watchers)
        self.assertTrue(skill.free_seen)

    def r1_menu_hands(self, script):
        """Hands whose pad also PRESSES (recorded), for `_story_menu`'s save screens."""
        hands = _LoopHands(script)
        hands.pressed = []

        def press(button, why, gate):
            hands.pressed.append((button, gate))
            hands.pad.frames += 2
            yield
            yield

        hands.pad.press = press
        return hands

    def test_r1_a_save_dialog_met_by_the_loop_gets_no_press(self):
        """D13 (finding F6): a save page the loop meets (`on_menu` -> `_story_menu`) is waited out with NO press: 400 still
        frames of a write and the run goes on once it has gone (True); one that never goes is left unhandled after
        `SAVE_PAGE_WAIT` frames (False), still with no press. CONTROL: an unknown menu is not the loop's (False at once)."""
        from ai_player.eyes.observation import MenuView
        from ai_player.mode import SAVE_PAGE_WAIT

        page = replace(self.free_screen(), screen=replace(self.free_screen().screen,
                                                          ui=MenuView("save_dialog", accepts_input=False),
                                                         text="SAVING… DON'T TURN OFF THE POWER."))
        brain = HandsBrain.__new__(HandsBrain)
        hands = self.r1_menu_hands(lambda frames: page if frames < 400 else self.free_screen())
        self.assertTrue(drive(brain._story_menu(hands, "save_dialog", "a scene", "MUDKIP"), 1000))
        self.assertEqual(hands.pressed, [])
        self.assertGreaterEqual(hands.pad.frames, 400)
        hands = self.r1_menu_hands(page)
        self.assertFalse(drive(brain._story_menu(hands, "save_dialog", "a scene", "MUDKIP"), 5000))
        self.assertEqual(hands.pressed, [])
        self.assertGreaterEqual(hands.pad.frames, SAVE_PAGE_WAIT)
        self.assertFalse(drive(brain._story_menu(self.r1_menu_hands(page), "a_menu_nobody_knows", "x", "MUDKIP")))

    def test_r1_a_start_menu_left_open_is_closed(self):
        """D13: a START menu (or a save question) left open and TAKING INPUT is closed with ONE B, told. CONTROL: one
        that does not take input (being built) gets no press."""
        from ai_player.eyes.observation import MenuView

        base = self.free_screen()
        for kind in ("start_menu", "save_yes_no"):
            with self.subTest(kind):
                menu = replace(base, screen=replace(base.screen, ui=MenuView(kind, ("YES", "NO"), 0, True)))
                hands = self.r1_menu_hands(menu)
                brain = HandsBrain.__new__(HandsBrain)
                self.assertTrue(drive(brain._story_menu(hands, kind, "a scene", "MUDKIP")))
                self.assertEqual([button for button, _ in hands.pressed], ["B"])
                self.assertTrue(any("B" in line for line in hands.told))
        building = replace(base, screen=replace(base.screen, ui=MenuView("start_menu", ("SAVE",), 0, False)))
        hands = self.r1_menu_hands(building)
        self.assertTrue(drive(HandsBrain.__new__(HandsBrain)._story_menu(hands, "start_menu", "a scene", "MUDKIP")))
        self.assertEqual(hands.pressed, [])

    def test_r1_the_runner_plays_a_save_goal_through_its_saver(self):
        """`GoalRunner.pursue`'s save branch: the play brain's saver plays it; "saved" is done, anything else not; with no
        saver (no memory file) no save is played."""
        from ai_player.brain.goals import Goal, GoalRunner

        runner = GoalRunner(None, None, None, None, lambda line: None)
        goal = Goal("save", "a save: a test", "ch1_lab", key="save:moment")
        self.assertEqual(drive(runner.pursue(goal, None, 0, None)), (False, "no way to save: the run keeps no memory file"))
        played: list = []

        def saver(outcome):
            def play(given):
                played.append(given)
                yield
                return outcome
            return play

        runner.saver = saver("saved")
        self.assertEqual(drive(runner.pursue(goal, None, 0, None)), (True, "saved"))
        runner.saver = saver("not saved: a saved file it does not know")
        self.assertEqual(drive(runner.pursue(goal, None, 0, None))[0], False)
        self.assertEqual(played, [goal, goal])

    def test_r1_a_continue_from_a_leader_save_makes_no_second_save_before_the_talk(self):
        """(R1 fix round, review R-1) The save right before ROXANNE is made by the REAL `HandsBrain._save` (its memory line
        written at the START of the write, the policy's record on the SAVED page; `save_game` stands in for the dialog),
        then CONTINUED: the memory as of that save (`game_memory.restore`, `restore_goals`) remembers THAT save as its last
        (`last_save` id 1, equal to the live one) and the approach as saved for, so the goal manager's block 8 returns the
        TALK, not a second save, at once (the 3-minute rule) and 30 game minutes later (D3: once per approach). FAULT (the
        code before the fix): the line held the save before it (none here) and no `saved_for`, so the continued game saved
        again at once. CONTROL: a NEW approach (it left the gym and came back) does save again, so the rule is live."""
        from ai_player import mode as mode_module
        from ai_player.brain.goals import Goal, GoalManager
        from ai_player.brain.saving import SavePolicy
        from ai_player.game_memory import MemoryWriter, MonRegistry, read_book, restore, restore_goals
        from ai_player.world.memory import Transition

        def gym(world: WorldMemory, entries) -> WorldMemory:
            world.transitions = [Transition(frame, "0:1", "0:2", "warp", "ai", (5, 5), (5, 10), None) for frame in entries]
            world._last.key, world._last.xy = "0:2", (5, 10)  # noqa: SLF001 - test side: it stands in the gym
            return world

        def decide(mgr: GoalManager, world: WorldMemory, play_time) -> str:
            seen = self.r1_timed(look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="RUSTBORO_CITY_GYM",
                                      frame=9000), play_time)
            milestone = next(m for m in mgr.story.milestones if m.id == "ch4_roxanne")
            talk = Goal("talk", "talk to the leader of RUSTBORO_CITY_GYM", milestone.id, map="RUSTBORO_CITY_GYM",
                        key="talk:ch4_roxanne")
            with mock.patch.object(mgr, "_story_goal", lambda *a: talk):
                return mgr.next_goal(seen, world, milestone, mgr.story.milestones.index(milestone)).kind

        def policy_for(mgr: GoalManager) -> None:
            mgr.saving, mgr.frames_left = SavePolicy(mgr.memory), lambda: 10 ** 6

        live = manager(errands_off=True, train_off=True, hints_off=True)
        policy_for(live)
        world = gym(world_with("RUSTBORO_CITY", "RUSTBORO_CITY_GYM"), (5000,))
        self.assertEqual(decide(live, world, (1, 0)), "save")  # REACH: the save right before the leader is chosen
        with tempfile.TemporaryDirectory(prefix="ai_r1_leader_") as tmp:
            path = Path(tmp) / "game" / "ai_player" / "memory.jsonl"
            brain = HandsBrain.__new__(HandsBrain)
            brain.options, brain.settings, brain.world = types.SimpleNamespace(cart="empty"), types.SimpleNamespace(
                frames=10 ** 9), world
            brain._registry, brain._policy = MonRegistry(), live.saving
            brain._kept = (live, types.SimpleNamespace(base="Story", favourite="X", history=[], draws=0),
                           types.SimpleNamespace(wishes={}, met={}, wild_met=0))
            brain._writer = MemoryWriter(path, None, header={"game": "t", "identity": {}},
                                         session={"how": "new game", "host": "harness", "run_dir": None, "cart": "empty"})
            hands = _LoopHands(self.r1_timed(look(ch1_through("ch1_rival_route103"), party=[mon(9)],
                                                  const="RUSTBORO_CITY_GYM", frame=9000), (1, 0)))
            calls: list = []
            with mock.patch.object(mode_module, "save_game", self.r1_saver(calls)):
                outcome = drive(brain._save(hands, "a save: right before the leader", {"losses": 0}))
            self.assertEqual((outcome, len(calls)), ("saved", 1))
            self.assertEqual(decide(live, world, (1, 1)), "talk")  # the live game: saved for this approach
            book = read_book(path)
            restored = restore(book, 1)
            again = manager(errands_off=True, train_off=True, hints_off=True)
            again.memory = restore_goals(again.memory, restored.goals)
            policy_for(again)
            continued = gym(WorldMemory.from_dict(restored.world), (5000,))
            self.assertEqual([t.frame for t in continued.transitions], [5000])  # the approach, as of the save
            self.assertEqual(decide(again, continued, (1, 0)), "talk")  # FAULT (before the fix): "save", at once
            self.assertEqual(decide(again, continued, (1, 30)), "talk")  # D3: once per approach
            self.assertEqual(again.memory.last_save, live.memory.last_save)  # the memory AS OF save 1 knows save 1
            self.assertEqual(again.memory.last_save["id"], book.saves()[-1]["id"])
            self.assertEqual(again.memory.last_save["frame"], book.saves()[-1]["frame"])
            self.assertEqual(again.memory.saved_for, {"ch4_roxanne": 5000})
            self.assertEqual(decide(again, gym(continued, (5000, 12000)), (1, 30)), "save")  # CONTROL: a new approach


class _StepEyes:
    """Eyes for `HandsBrain.play`: `seen` at a frame that rises by one per look (the emulator's counter)."""

    def __init__(self, seen: Observation) -> None:
        self.seen = seen
        self.looks = 0

    def look(self) -> Observation:
        self.looks += 1
        return replace(self.seen, frame=self.seen.frame + self.looks)


class R1PlayTests(unittest.TestCase):
    """(R1 + R2, build stage 4: build spec 2026-10-29 sections 3 (c), (e)) `HandsBrain.play` with a memory file, its
    skill stood in (`_skill`, `_play`, `continue_game` patched) and the memory file REAL: a newer file refuses the run
    byte-identical; a new game on a game that has a memory file is refused; the no-save CONTROL never reads it; the `end`
    line says chosen / budget / at_save; a CONTINUE restores the memory AS OF its save, writes the restore record (the
    session line, the world snapshot) BEFORE the play loop's first look, plays on the restored world, and its eyes carry
    the FRAME BASE (D7); a continue that stops ends "stuck" with its session line and a chosen end line."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ai_r1_play_"))
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        self.memory_file = self.tmp / "game" / "ai_player" / "memory.jsonl"
        self.seen = replace(look(ch1_through("ch1_rival_route103"), party=[mon(6)], const="ROUTE101"), frame=100)

    def options(self, **extra):
        from ai_player.options import HandsOptions

        base = dict(brain="play", run_dir=self.tmp / "run", seed=7, personality="Story", mart_item="x", mart_count=1,
                    clock=None, fault_ungated_a=False, fault_blind_count=False, memory_file=self.memory_file, cart="empty",
                    host="harness")
        base.update(extra)
        return HandsOptions(**base)

    def play(self, eyes=None, frames: int = 5000, **extra) -> tuple[str, HandsBrain, list[str]]:
        from ai_player.mode import BrainSettings

        told: list[str] = []
        brain = HandsBrain(BrainSettings(frames=frames), told.append, self.options(**extra))
        reason = drive(brain.play(_Controls(), eyes or _StepEyes(self.seen)), 20_000)
        return reason, brain, told

    def a_game(self, losses: int = 0) -> dict:
        """A memory file of one new game with one save (world, goals, losses), as a run writes it."""
        from ai_player.brain.goals import _Memory
        from ai_player.game_memory import MemoryWriter, build_payload, goals_part

        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101")
        payload = build_payload(world=world.to_dict(), goals=goals_part(_Memory(talked={"0:1|3"})),
                                personality={"base": "Story", "favourite": "ZIGZAGOON", "history": [], "draws": 2},
                                battle={"wishes": {}, "met": {"MAY": 1}, "wild_met": 4}, mons={}, losses=losses)
        writer = MemoryWriter(self.memory_file, None,
                              header={"game": "t|x", "identity": {"seed": 7, "personality": "Trainer", "favourite": "X",
                                                                  "starter": "MUDKIP", "gender": "BOY", "name": None}},
                              session={"how": "new game", "host": "harness", "run_dir": None, "cart": "empty"})
        written = writer.write_save(play_time=(0, 20), frame=5000, where={"map": "ROUTE101", "tile": [10, 10]},
                                    party=[{"pid": "00000001", "species": "Mudkip"}], why="a test save", payload=payload)
        self.assertTrue(written.reached)
        return payload

    def test_r1_a_newer_memory_file_refuses_the_run_byte_identical(self):
        self.a_game()
        text = self.memory_file.read_bytes().replace(b'"schema_version":1', b'"schema_version":2', 1)
        self.memory_file.write_bytes(text)
        with mock.patch.object(HandsBrain, "_skill", side_effect=AssertionError("the skill must not run")):
            reason, _, _ = self.play()
        self.assertTrue(reason.startswith("play: stuck: the memory file was written by a newer program"), reason)
        self.assertEqual(self.memory_file.read_bytes(), text)
        with mock.patch.object(HandsBrain, "_skill", side_effect=AssertionError("the skill must not run")):
            reason, _, _ = self.play(continue_game=True, cart="continued")
        self.assertIn("newer program", reason)
        self.assertEqual(self.memory_file.read_bytes(), text)

    def fake_skill(self, press_after: bool = False, outcome: str = "done: ch1_pokedex reached"):
        def skill(brain, hands, personality):
            from ai_player.game_memory import MemoryWriter

            brain._writer = MemoryWriter(brain._memory_path, None, header={"game": "t", "identity": {}},
                                         session=brain._session("new game", "empty"))
            brain._writer.write_save(play_time=(0, 9), frame=hands.look().frame, where={"map": "R", "tile": [1, 1]},
                                     party=[], why="x", payload={"world": {}})
            brain._at_save_presses = hands.pad.presses
            if press_after:
                yield from hands.pad.press("B", "after the save", "a test")
            yield from hands.pad.idle(2, "a test")
            return outcome
        return skill

    def test_r1_the_end_line_says_chosen_budget_and_at_save(self):
        from ai_player.game_memory import read_book

        with mock.patch.object(HandsBrain, "_skill", self.fake_skill()):
            reason, brain, _ = self.play()
        self.assertEqual(reason, "play: done: ch1_pokedex reached")
        self.assertIsNotNone(brain.world)  # a new game's world memory is started before its skill (not a continue)
        end = read_book(self.memory_file).end_of(1)
        self.assertEqual((end["chosen"], end["budget"], end["at_save"]), (True, False, True))
        self.memory_file.unlink()
        with mock.patch.object(HandsBrain, "_skill", self.fake_skill(press_after=True,
                                                                     outcome="stopped: not finished within 5000 frames")):
            self.play()
        end = read_book(self.memory_file).end_of(1)
        self.assertEqual((end["chosen"], end["budget"], end["at_save"]), (False, True, False))  # a press after the save

    def test_r1_a_new_game_on_an_existing_memory_is_refused(self):
        self.a_game()
        text = self.memory_file.read_bytes()
        with mock.patch.object(HandsBrain, "_skill", side_effect=AssertionError("the skill must not run")):
            reason, _, _ = self.play()
        self.assertIn("already has a memory file", reason)
        self.assertEqual(self.memory_file.read_bytes(), text)
        # CONTROL: the no-save CONTROL never even reads it (the pre-R1 loop): the skill runs
        with mock.patch.object(HandsBrain, "_skill", self.fake_skill_plain()):
            reason, brain, _ = self.play(fault_no_save=True)
        self.assertEqual(reason, "play: done: x")
        self.assertEqual((brain._saving, brain._book, brain._writer), (False, None, None))
        self.assertEqual(self.memory_file.read_bytes(), text)

    @staticmethod
    def fake_skill_plain():
        def skill(brain, hands, personality):
            yield from hands.pad.idle(2, "a test")
            return "done: x"
        return skill

    def test_r1_a_continue_restores_as_of_its_save_before_the_first_look(self):
        from ai_player.game_memory import read_book
        from ai_player.skills.saving import ContinueResult
        from ai_player import mode as mode_module

        payload = self.a_game(losses=1)
        book_before = read_book(self.memory_file)
        base = book_before.frame_base()
        seen: dict = {}

        def fake_continue(hands, book, why):
            seen["frame"] = hands.look().frame
            yield from hands.pad.idle(2, "the title")
            return ContinueResult("continued", "continued the save of 0:20", record=book.save(1), newest=True,
                                  arrival={"where": {"map": "ROUTE101", "tile": [10, 10]}, "party": []})

        def fake_play(brain, hands, personality, restored=None, stop=None):
            seen["restored"], seen["stop"] = restored, stop
            seen["kinds"] = [line["kind"] for line in read_book(brain._memory_path).lines]
            seen["world_lines"] = len((brain.options.run_dir / "world.jsonl").read_text(encoding="utf-8").splitlines())
            seen["maps"] = sorted(brain.world.maps)
            seen["looks"] = hands.looks
            yield from hands.pad.idle(2, "a test")
            return "stopped: a test"

        eyes = _StepEyes(self.seen)
        with mock.patch.object(mode_module, "continue_game", fake_continue), \
                mock.patch.object(HandsBrain, "_play", fake_play):
            reason, brain, told = self.play(eyes=eyes, continue_game=True, cart="continued", personality=None)
        self.assertEqual(reason, "play: stopped: a test")
        self.assertGreaterEqual(seen["frame"], base + 1)  # D7: the emulator's frame plus the base
        self.assertEqual(base, 5001)
        self.assertIsNone(seen["stop"])
        self.assertEqual(seen["restored"].losses, 1)
        self.assertEqual(seen["restored"].goals["talked"], payload["goals"]["talked"])
        self.assertEqual(seen["kinds"], ["header", "session", "save", "session"])  # the restore record, before the loop
        self.assertEqual(seen["world_lines"], 1)  # the "restored from save 1" snapshot
        self.assertEqual(seen["maps"], sorted(payload["world"]["maps"]))  # the restored world, not a new one
        book = read_book(self.memory_file)
        session = book.last_session()
        self.assertEqual((session["how"], session["continued_from"], session["frame_base"], session["losses"]),
                         ("continue", 1, base, 1))
        self.assertEqual(session["restored_maps"], sorted(payload["world"]["maps"]))
        self.assertEqual(book.end_of(session["n"])["budget"], True)
        # the restore's own record in the action log: the save and the maps it restored
        actions = [json.loads(line) for line in (self.tmp / "run" / "actions.jsonl").read_text(encoding="utf-8").splitlines()]
        restore_note = next(r for r in actions if r.get("decision") == "restore")
        self.assertEqual((restore_note["extra"]["save"], restore_note["extra"]["maps"]), (1, sorted(payload["world"]["maps"])))
        self.assertTrue(any("personality=Trainer" in line for line in told))  # the header's personality (a continue)

    def test_u2_the_ais_continue_tells_the_drop_and_no_map(self):
        """(U2 spec 2026-10-30 D13: USER RULING 53) The continued session's line records what the continue told it
        drops: `dropped` = the skill's `ContinueResult.dropped` (the memory file's frames after the save, or None "not
        recorded", and the battles undone). FAULT (mutant D4m): the session line without it. No play time and no map in
        it (D19, ruling 40). CONTROL: a continue with nothing after the save records 0 frames."""
        from ai_player.game_memory import read_book
        from ai_player.skills.saving import ContinueResult
        from ai_player import mode as mode_module

        for dropped in ({"frames": 700, "lost": 1}, {"frames": None, "lost": 0}, {"frames": 0, "lost": 0}):
            with self.subTest(dropped=dropped):
                if self.memory_file.exists():
                    self.memory_file.unlink()
                self.a_game()

                def fake_continue(hands, book, why, dropped=dropped):
                    yield from hands.pad.idle(2, "the title")
                    return ContinueResult("continued", "continued the save of 0:20", record=book.save(1), newest=True,
                                          arrival={"where": {"map": "ROUTE101", "tile": [10, 10]}, "party": []},
                                          dropped=dict(dropped))

                def fake_play(brain, hands, personality, restored=None, stop=None):
                    yield from hands.pad.idle(2, "a test")
                    return "stopped: a test"

                with mock.patch.object(mode_module, "continue_game", fake_continue), \
                        mock.patch.object(HandsBrain, "_play", fake_play):
                    self.play(continue_game=True, cart="continued", personality=None)
                session = read_book(self.memory_file).last_session()
                self.assertEqual(session["dropped"], dropped)
                self.assertEqual(set(session["dropped"]), {"frames", "lost"})  # never a play time or a map

    def test_r1_a_continue_whose_restore_record_is_not_written_ends_stuck(self):
        from ai_player.game_memory import MemoryWriter
        from ai_player.skills.saving import ContinueResult
        from ai_player import mode as mode_module

        self.a_game()

        def fake_continue(hands, book, why):
            yield from hands.pad.idle(2, "the title")
            return ContinueResult("continued", "continued", record=book.save(1), newest=True, arrival={})

        def fake_play(brain, hands, personality, restored=None, stop=None):
            yield from hands.pad.idle(2, "a test")
            return f"stuck: {stop}" if stop else "stopped: played on"

        with mock.patch.object(mode_module, "continue_game", fake_continue), \
                mock.patch.object(HandsBrain, "_play", fake_play), \
                mock.patch.object(MemoryWriter, "write_session", lambda writer, **updates: False):
            reason, _, _ = self.play(continue_game=True, cart="continued")
        self.assertEqual(reason, "play: stuck: the memory of this continue could not be written")

    def test_r1_a_continue_that_stops_ends_stuck_with_a_chosen_end(self):
        from ai_player.game_memory import read_book
        from ai_player.skills.saving import ContinueResult
        from ai_player import mode as mode_module

        self.a_game()

        def fake_continue(hands, book, why):
            yield from hands.pad.idle(2, "the title")
            return ContinueResult("stopped", "the save is gone: the main menu offers no CONTINUE")

        with mock.patch.object(mode_module, "continue_game", fake_continue):
            reason, brain, _ = self.play(continue_game=True, cart="continued")
        self.assertEqual(reason, "play: stuck: the continue stopped: the save is gone: the main menu offers no CONTINUE")
        book = read_book(self.memory_file)
        self.assertEqual((book.last_session()["how"], book.last_session()["continued_from"]), ("continue", None))
        end = book.end_of(book.last_session()["n"])
        self.assertEqual((end["chosen"], end["at_save"]), (True, False))  # so no later continue (D12 (a))
        # the stop's session line is written when the continue stops, before the play loop runs
        seen: list = []

        def fake_play(brain, hands, personality, restored=None, stop=None):
            seen.append([line["kind"] for line in read_book(brain._memory_path).lines])
            yield from hands.pad.idle(2, "a test")
            return f"stuck: {stop}"

        self.memory_file.unlink()
        self.a_game()
        with mock.patch.object(mode_module, "continue_game", fake_continue), mock.patch.object(HandsBrain, "_play", fake_play):
            self.play(continue_game=True, cart="continued")
        self.assertEqual(seen, [["header", "session", "save", "session"]])

    def test_r1_a_continue_that_stops_on_a_bound_is_not_a_chosen_end(self):
        """(R1 fix round, review R-2) A continue that STOPS on a bound or a failed read (`may_retry`: here no main menu in
        time) restored and played nothing: it still ends "stuck" through the loop's own end, but its `end` line says
        `stopped_before_restore` and is NOT chosen, so the launcher may let a later continue try again (it looks through
        to the session before: a harness session with no end line, killed). FAULT half: the spec's own stop (the save
        gone, not retryable) stays a CHOSEN end and the launcher refuses the next continue."""
        from ai_player.game_memory import read_book
        from ai_player.host.launcher import judge_end
        from ai_player.skills.saving import ContinueResult
        from ai_player import mode as mode_module

        for why, retry, chosen, allowed in (
                ("the main menu did not come within 1700 frames of power-on", True, False, True),
                ("the save is gone: the main menu offers no CONTINUE", False, True, False)):
            with self.subTest(why):
                self.memory_file.unlink(missing_ok=True)
                self.a_game()

                def fake_continue(hands, book, why_, why=why, retry=retry):
                    yield from hands.pad.idle(2, "the title")
                    return ContinueResult("stopped", why, may_retry=retry)

                with mock.patch.object(mode_module, "continue_game", fake_continue):
                    reason, _, _ = self.play(continue_game=True, cart="continued")
                self.assertEqual(reason, f"play: stuck: the continue stopped: {why}")
                book = read_book(self.memory_file)
                end = book.end_of(book.last_session()["n"])
                self.assertEqual((end["chosen"], end["stopped_before_restore"], end["at_save"]), (chosen, retry, False))
                judgement = judge_end(book, [])
                self.assertEqual(judgement.allowed, allowed, judgement.words)


def mode_module_patience() -> int:
    from ai_player.mode import STORY_PATIENCE
    return STORY_PATIENCE


class _Controls:
    """The brain's `Controls` for a unit test: every action only lets its frames pass."""

    def wait(self, frames: int):
        for _ in range(frames):
            yield

    def tap(self, button: str):
        yield
        yield

    def hold(self, button: str, frames: int):
        for _ in range(frames):
            yield


class _ScriptEyes:
    """Eyes whose look is `script(frame)` (the frames the pad has let pass), and the hands that hold them."""

    def __init__(self, script) -> None:
        self.script = script
        self.hands = None

    def look(self) -> Observation:
        return self.script(self.hands.pad.frames)


def script_hands(script) -> Hands:
    eyes = _ScriptEyes(script)
    hands = Hands(eyes, _Controls(), random.Random(1), random.Random(1), None, lambda line: None)
    eyes.hands = hands
    return hands


def screen_look(frame: int = 0, ui=None, waits: bool = False, text: str | None = None, state: str = "OVERWORLD",
                script: bool = False, party=(), objects=()) -> Observation:
    base = look(ch1_through("ch1_lab"), party=party, objects=objects)
    screen = ScreenState(game_state=state, screen="overworld", menu=None, text_box_open=waits, waits_for_button=waits,
                         in_battle=False, wait_reason="text printer 0 CLEAR" if waits else None, ui=ui, text=text,
                         script_running=script, controls_locked=script)
    return replace(base, frame=frame, screen=screen)


class PacingTests(unittest.TestCase):
    """(build step 5.1, the step-5 verifier's FAILURE: "never idle", RULING 37 Q6) No screen that waits for a press is
    watched with no press: the starter bag's question handed back at once (a), a scene's text never waited out by `talk`
    (b), and the instrument that grades it (`hands/waiting.py`)."""

    def bag(self, cursor: int = 1, accepts: bool = True):
        from ai_player.eyes.observation import MenuView
        from ai_player.eyes.screens import STARTER_OPTIONS
        return MenuView(kind="choose_starter", options=STARTER_OPTIONS, cursor=cursor, accepts_input=accepts)

    def yes_no(self):
        from ai_player.eyes.observation import MenuView
        return MenuView(kind="yes_no", options=("YES", "NO"), cursor=0, accepts_input=True)

    def test_the_bag_hands_its_question_back_at_once(self):
        """(a) After the A on a ball the bag shows busy while the ball opens; the yes/no ("Do you choose this POKéMON?")
        follows. Handed the bag again, the skill returns at once when the question is up (it watched for the bag alone
        for 600 frames, 20 of 40 sweep runs)."""
        from ai_player.skills.story import choose_starter

        def script(frames: int) -> Observation:
            if frames < 20:
                return screen_look(frames, ui=self.bag(2, accepts=False), state="CHOOSE_STARTER")
            return screen_look(frames, ui=self.yes_no(), state="CHOOSE_STARTER", text="Do you choose this POKéMON?")

        hands = script_hands(script)
        self.assertTrue(drive(choose_starter(hands, "MUDKIP", "the bag"), budget=5000))
        self.assertLess(hands.pad.frames, 40, hands.pad.frames)  # FAULT half: the old wait stood 600 frames
        self.assertEqual(hands.pad.presses, 0)  # the question is the scene's to answer, not the bag's

    def test_the_bag_is_still_chosen_from(self):
        from ai_player.skills.story import choose_starter
        state = {"cursor": 1, "chosen": False}

        def script(frames: int) -> Observation:
            if state["chosen"]:
                return screen_look(frames, ui=self.bag(state["cursor"], accepts=False), state="CHOOSE_STARTER")
            return screen_look(frames, ui=self.bag(state["cursor"]), state="CHOOSE_STARTER")

        hands = script_hands(script)
        real_press = hands.pad.press

        def press(button, why, gate, hold=None):
            if button == "Right":
                state["cursor"] += 1
            if button == "A":
                state["chosen"] = True
            return real_press(button, why, gate, hold)

        hands.pad.press = press
        self.assertTrue(drive(choose_starter(hands, "MUDKIP", "the bag"), budget=5000))
        self.assertEqual([h["button"] for h in hands.pad.history], ["Right", "A"])

    def test_talk_gives_a_scene_its_screen_back(self):
        """(b) While `talk` waits for the player to be free, a text that WAITS FOR A (a scene began) is not waited out:
        with `give_way` it returns at once; the step-2 default still waits (its callers unchanged)."""
        from ai_player.hands.dialogue import FREE_BUDGET, talk
        scene = screen_look(0, waits=True, script=True, text="PROF. BIRCH: So, Milo.")
        target = person(10, 9, gfx=1, local_id=3)
        for give_way, want_max in ((True, 5), (False, FREE_BUDGET)):
            hands = script_hands(lambda frames: replace(scene, frame=frames))
            self.assertFalse(drive(talk(hands, target, "chat", give_way=give_way), budget=FREE_BUDGET + 50))
            if give_way:
                self.assertLessEqual(hands.pad.frames, want_max)
            else:
                self.assertGreaterEqual(hands.pad.frames, want_max)

    def test_talk_to_plays_the_scene_that_began(self):
        """(b) `talk_to` hands such a scene to `play_out` and says so, instead of 'did not answer'."""
        from ai_player.skills import story as story_skill
        scene = screen_look(0, waits=True, script=True, text="PROF. BIRCH: So, Milo.")
        target = person(10, 9, gfx=1, local_id=3)
        hands = script_hands(lambda frames: replace(scene, frame=frames))
        played = []

        def fake_play_out(hands_, nav_, why):
            played.append(why)
            yield
            return None

        def fake_approach(hands_, nav_, target_, why, budget=0):
            yield
            return "reached"

        with mock.patch.object(story_skill, "play_out", fake_play_out), mock.patch.object(story_skill, "approach",
                                                                                          fake_approach):
            outcome = drive(story_skill.talk_to(hands, types.SimpleNamespace(), target, "chat"))
        self.assertTrue(outcome.startswith("interrupted before it could talk"), outcome)
        self.assertEqual(len(played), 1)

    def test_a_scene_that_begins_while_it_turns_to_talk_is_played(self):
        """(b) The player is free when `talk_to` begins and turns to face the person; the scene begins during the turn:
        it is played at once (`give_way`), never watched for `FREE_BUDGET` frames."""
        from ai_player.hands.dialogue import FREE_BUDGET
        from ai_player.skills import story as story_skill
        free = screen_look(0)
        scene = screen_look(0, waits=True, script=True, text="PROF. BIRCH: So, Milo.")
        target = person(10, 9, gfx=1, local_id=3)
        free = replace(free, view=replace(free.view, objects=(target,)))  # the person in view, above the player
        hands = script_hands(lambda frames: replace(free if frames < 3 else scene, frame=frames))
        played = []

        def fake_play_out(hands_, nav_, why):
            played.append(hands_.pad.frames)
            yield
            return None

        def fake_approach(hands_, nav_, target_, why, budget=0):
            return "reached"
            yield  # noqa: unreachable - a generator that takes no frame

        with mock.patch.object(story_skill, "play_out", fake_play_out), mock.patch.object(story_skill, "approach",
                                                                                          fake_approach):
            outcome = drive(story_skill.talk_to(hands, types.SimpleNamespace(), target, "chat"), budget=FREE_BUDGET * 4)
        self.assertTrue(outcome.startswith("interrupted before it could talk"), outcome)
        self.assertEqual(len(played), 1)
        self.assertLess(played[0], 200)  # FAULT half: without give_way, `talk` watched the scene's text 1,200 frames

    def test_the_wait_watch_measures_every_stretch_whatever_the_reason(self):
        """THE INSTRUMENT (`hands/waiting.py`): a stretch begins at the first look that waits for a press after the last
        press and ends at the next press or the first look that does not wait; the busy reason plays no part."""
        from ai_player.hands.waiting import NOTE_FRAMES, WaitWatch
        presses = {"n": 0}
        notes = []
        watch = WaitWatch(lambda: presses["n"], lambda *a: notes.append(a), lambda: "waiting for the choose_starter")
        waiting = screen_look(0, ui=self.yes_no())
        free = screen_look(0)
        for frame in range(0, 600, 10):  # 590 frames on a yes/no, no press (the starter stall)
            watch(replace(waiting, frame=frame))
        presses["n"] += 1
        for frame in range(600, 700, 10):  # a press, then the yes/no again for 90 frames
            watch(replace(waiting, frame=frame))
        watch(replace(free, frame=700))
        for frame in range(710, 750, 10):  # a text waits 30 frames (under NOTE_FRAMES: counted, not written)
            watch(replace(screen_look(frame, waits=True, text="Hi!"), frame=frame))
        watch.finish()
        self.assertEqual([n[3]["frames"] for n in notes], [590, 90])  # FAULT half: a press closes the stretch
        self.assertEqual(watch.summary()["longest"], 590)
        self.assertEqual(watch.summary()["stretches"], 3)
        self.assertEqual(notes[0][0], "await")
        self.assertIn("waiting for the choose_starter", notes[0][2])
        self.assertGreaterEqual(min(n[3]["frames"] for n in notes), NOTE_FRAMES)

    def test_the_graders_read_the_stretches(self):
        from ai_player.gates.rate_step5 import BOUNDS, await_stretches
        records = [{"decision": "await", "extra": {"frames": 643, "first": 34499, "what": "the yes_no takes input",
                                                   "doing": "waiting for the choose_starter to open"}},
                   {"decision": "watch", "action": "busy 600f", "reason": "waiting for the choose_starter to open"}]
        found = await_stretches(records)
        self.assertEqual([a["frames"] for a in found], [643])
        self.assertGreater(643, BOUNDS["AWAIT_MAX"])  # the measured stall is over the bound: the grader fails it


class ExploreTests(unittest.TestCase):
    """(build step 5.1, the step-5 review's finding 1: "it plays like a speedrun") Looking around new places, detours off
    the way, item curiosity: seeded, personality-weighted, bounded; none of them under the beeline control."""

    def outdoor_goal(self, personality: str, seed: int, errands_off: bool = False, heard=("ROUTE 103",)):
        mgr = manager(personality, seed=seed, quiet=False, errands_off=errands_off, train_off=True)
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F",
                           current="OLDALE_TOWN", heard={f"Oh, MAY went out to {w} just a little while ago." for w in heard})
        mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
        observation = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
        index, milestone = mgr.milestone(observation, visited_in(world))
        return mgr, mgr.next_goal(observation, world, milestone, index)

    def test_looking_around_a_new_place_by_personality(self):
        from ai_player.personality import ERRANDS
        rates = {}
        for personality in ("Story", "Catcher", "Trainer"):
            hits = sum(self.outdoor_goal(personality, seed)[1].kind == "explore" for seed in range(300))
            rates[personality] = hits / 300
            self.assertLess(abs(rates[personality] - ERRANDS[personality].look_around), 0.08, rates)
        self.assertGreater(rates["Story"], 0.0)  # the Story personality looks around too, less
        self.assertLess(rates["Story"], min(rates["Catcher"], rates["Trainer"]))
        mgr, goal = self.outdoor_goal("Catcher", 1)
        self.assertEqual((goal.kind, goal.steps), ("explore", ERRANDS["Catcher"].look_frames))
        self.assertIn("a new place, OLDALE_TOWN", goal.reason)

    def test_one_draw_a_map_and_none_under_the_beeline_control(self):
        mgr, first = self.outdoor_goal("Catcher", 3)
        self.assertIn("0:3", mgr.memory.looked)
        for seed in range(40):
            self.assertNotIn(self.outdoor_goal("Catcher", seed, errands_off=True)[1].kind, ("explore", "detour", "chat"))

    def test_a_detour_now_and_then_while_travelling(self):
        from ai_player.personality import ERRANDS
        hits = 0
        for seed in range(300):
            mgr = manager("Trainer", seed=seed, quiet=False, train_off=True)
            mgr.memory.looked = _Everything()
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", "ROUTE103", current="OLDALE_TOWN",
                               heard={"Oh, MAY went out to ROUTE 103."})
            mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
            observation = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
            index, milestone = mgr.milestone(observation, visited_in(world))
            goal = mgr.next_goal(observation, world, milestone, index)
            hits += goal.kind == "detour"
            if goal.kind == "detour":
                self.assertEqual(goal.steps, ERRANDS["Trainer"].detour_frames)
                again = mgr.next_goal(observation, world, milestone, index)
                self.assertEqual((again.kind, again.map), ("go", "ROUTE103"))  # one draw a map and milestone
        self.assertLess(abs(hits / 300 - ERRANDS["Trainer"].detour), 0.08)

    def test_curiosity_finds_an_item_ball_before_the_party(self):
        """(review #3) No step says "use the POKé BALL on the floor": the rival's room's ball is found by curiosity, before
        the AI has a party (step 5 picked up item balls only with a party)."""
        mgr = manager("Story")
        world = world_with("LITTLEROOT_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F", "LITTLEROOT_TOWN_MAYS_HOUSE_2F",
                           current="LITTLEROOT_TOWN_MAYS_HOUSE_2F", heard={"Our daughter is upstairs, I think.",
                                                                          "He lives right next door, so you should"})
        ball = person(12, 10, gfx=59, local_id=1, kind="item_ball")
        observation = look(ch1_through("ch1_rival_house"), party=[], objects=[ball],
                           const="LITTLEROOT_TOWN_MAYS_HOUSE_2F")
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertEqual(milestone.id, "ch1_rival_house")
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.target.local_id), ("pick_up", 1))
        self.assertFalse(any(s.look == "rivals_poke_ball" for m in mgr.story.milestones for s in m.steps))

    def test_an_item_ball_seen_earlier_is_walked_back_to(self):
        mgr = manager("Catcher")
        world = world_with("ROUTE102", "OLDALE_TOWN", current="ROUTE102")
        world.maps["0:1"].items[(20, 5)] = 900  # seen at f900, not on screen now
        observation = look(ch1_through("ch2_oldale"), party=[mon(9)], const="ROUTE102")
        index, milestone = mgr.milestone(observation, visited_in(world))
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.tile, goal.target), ("pick_up", (20, 5), None))
        mgr.memory.tried_items.add("0:1|20,5")
        self.assertNotEqual(mgr.next_goal(observation, world, milestone, index).kind, "pick_up")  # FAULT half: tried

    def test_a_walk_that_arrives_somewhere_new_stops_to_decide(self):
        """The new-map stop: a `go` that arrives on an outdoor map whose look-around draw is due ends there ("arrived
        somewhere it has not looked round"), so the next decision may look around; not under the beeline control, and not
        on a map whose draw is made (FAULT halves)."""
        from ai_player.brain.goals import NEW_MAP_STOP, Goal, GoalRunner
        for errands_off, drawn, want, before in ((False, False, True, False), (True, False, False, False),
                                                 (False, True, False, False), (False, False, True, True)):
            # (the last case: OLDALE visited BEFORE the walk, its draw not made: it stops there too; step51dev2-4 stopped
            # only on maps never visited, and the draw was rarely due)
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101")
            if before:
                world.maps["0:7"] = MapMemory("0:7", "OLDALE_TOWN", "OLDALE_TOWN")
                world.maps["0:7"].visits[(1, 1)] = 1
            arrive = replace(look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN", map_number=7))
            stopped = []

            def run(intent, why):
                world.maps["0:7"] = MapMemory("0:7", "OLDALE_TOWN", "OLDALE_TOWN")
                world.maps["0:7"].visits[(1, 1)] = 1
                world._last.key = "0:7"  # noqa: SLF001
                stopped.append(intent.done(arrive))
                yield
                return "done: travel" if stopped[-1] else "budget: ran out"

            mgr = manager("Story", errands_off=errands_off, quiet=False)
            if drawn:
                mgr.memory.looked.add("0:7")
            nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
            runner = GoalRunner(types.SimpleNamespace(look=lambda: arrive), nav, mgr, types.SimpleNamespace(purpose=""),
                                lambda line: None)
            runner._travel = lambda target, why, budget, done: run(types.SimpleNamespace(done=done), why)  # noqa: SLF001
            ok, outcome = drive(runner.pursue(Goal("go", "to ROUTE 103", map="ROUTE103"), mgr.story.milestones[8], 8,
                                              lambda seen: 8))
            self.assertEqual(stopped, [want])
            self.assertEqual(NEW_MAP_STOP in outcome, want, outcome)


class PersonFairTests(unittest.TestCase):
    """(build step 5.1, the step-5 review's findings 3 and 4) Only what a person was TOLD or has SEEN: each step's own
    words, fights the game names, the mart's list, MOM's words."""

    def test_each_step_needs_its_own_words(self):
        """One word heard for a milestone ("next door") no longer opens every step's map: upstairs in the rival's house
        needs the rival's mom's own words."""
        mgr = manager("Story")
        heard = {"He lives right next door, so you should go over and introduce yourself."}
        world = world_with("LITTLEROOT_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F", current="LITTLEROOT_TOWN_MAYS_HOUSE_1F",
                           heard=heard)
        observation = look(ch1_through("ch1_rival_house"), const="LITTLEROOT_TOWN_MAYS_HOUSE_1F")
        index, milestone = mgr.milestone(observation, visited_in(world))
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.map, goal.words), ("go", None, "is upstairs, I think"))
        world.heard.add("Our daughter is upstairs, I think.")
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.map), ("go", "LITTLEROOT_TOWN_MAYS_HOUSE_2F"))
        self.assertIn("is upstairs, I think", goal.reason)

    def test_asking_goes_only_where_it_has_been(self):
        mgr = manager("Story", train_off=True)
        for places, want in ((("LITTLEROOT_TOWN", "ROUTE101"), None),
                             (("LITTLEROOT_TOWN", "ROUTE101", "LITTLEROOT_TOWN_MAYS_HOUSE_1F"), "LITTLEROOT_TOWN_MAYS_HOUSE_1F")):
            world = world_with(*places, current="LITTLEROOT_TOWN", heard={BIRCH_GO_SEE})
            observation = look(ch1_through("ch1_rival_route103"), party=[mon(6)], const="LITTLEROOT_TOWN")
            index, milestone = mgr.milestone(observation, visited_in(world))
            goal = mgr.next_goal(observation, world, milestone, index)
            self.assertEqual((goal.kind, goal.map), ("go", want), places)

    def test_only_a_named_fight_is_trained_for_before_it_is_seen(self):
        """ROUTE 102's trainers are named by nobody: no levels, no training, until one is SEEN in a battle there; the
        rival and ROXANNE are named, and the target is the STRONGEST level plus the margin (asked of the goal manager:
        the step-5 verifier's min() mutant passed every test)."""
        mgr = manager("Trainer")
        story = mgr.story
        route102 = story.milestones[story.index("ch2_route102")]
        roxanne = story.milestones[story.index("ch4_roxanne")]
        self.assertEqual(mgr.fight_levels(route102), ((), ""))
        mgr.notice(replace(look(const="ROUTE102", map_number=5)))  # where it stands
        battle = BattleView(kind="trainer", double=False, type_flags=8, opponent_trainer_id=318, own=(),
                            foe=(types.SimpleNamespace(level=5),))
        mgr.notice(replace(battle_look(200, None), battle=battle))
        self.assertEqual(mgr.fight_levels(route102)[0], (5,))
        self.assertEqual(mgr.fight_levels(roxanne)[0], (12, 15))
        self.assertEqual(mgr.training_target(mgr.fight_levels(roxanne)[0]), 15 + ERRANDS["Trainer"].train_margin)

    def test_the_training_goal_names_the_strongest_level(self):
        values = {name: 1 for name, _ in MILESTONE_FLAGS if name in (
            "VISITED_LITTLEROOT_TOWN", "SET_WALL_CLOCK", "RESCUED_BIRCH", "SYS_POKEMON_GET", "DEFEATED_RIVAL_ROUTE103",
            "RECEIVED_POKEDEX_FROM_BIRCH", "SYS_POKEDEX_GET", "ADVENTURE_STARTED", "VISITED_OLDALE_TOWN",
            "VISITED_PETALBURG_CITY", "HIDE_PETALBURG_CITY_WALLYS_MOM", "VISITED_RUSTBORO_CITY")}
        values.update({"LITTLEROOT_INTRO_STATE": 7, "LITTLEROOT_RIVAL_STATE": 4, "BIRCH_LAB_STATE": 5,
                       "PETALBURG_GYM_STATE": 6, "PETALBURG_WOODS_STATE": 2})
        mgr = manager("Trainer")
        world = world_with("RUSTBORO_CITY", "RUSTBORO_CITY_GYM", current="RUSTBORO_CITY",
                           heard={"There, you should challenge the GYM LEADER, ROXANNE."}, grass=True)
        observation = look(values, party=[mon(13)], const="RUSTBORO_CITY")
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertEqual(milestone.id, "ch4_roxanne")  # the gym's trainers are optional: never the current one
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual(goal.kind, "train")
        self.assertIn(f"target L{15 + ERRANDS['Trainer'].train_margin}", goal.reason)  # max(12, 15), never min

    def test_roxanne_is_proven_by_the_badge_alone(self):
        story = load_story("BOY")
        marks_now = {**{name: 1 for name, _ in MILESTONE_FLAGS}, **{name: 9 for name, _ in MILESTONE_VARS}}
        marks_now.update({"TRAINER_JOSH": 0, "TRAINER_TOMMY": 0})
        self.assertEqual(story.current(marks_now), (len(story.milestones), None))
        mgr = manager()
        self.assertEqual(mgr.milestone(look(), visited_in(WorldMemory()))[1].id, "ch1_intro")
        values = {name: value for name, value in marks_now.items() if name in dict(MILESTONE_FLAGS) or name in dict(MILESTONE_VARS)}
        observation = replace(look(), progress=replace(look().progress, marks=tuple(values.items())))
        self.assertEqual(mgr.milestone(observation, visited_in(WorldMemory())), (len(story.milestones), None))

    def test_the_mart_is_shopped_by_its_list(self):
        """No flag says when POKé BALLS are sold: a mart is tried; when its LIST had none, it is tried again only once the
        story has moved on (a person comes back later)."""
        world = world_with("OLDALE_TOWN", "ROUTE101", current="OLDALE_TOWN", mart_from="OLDALE_TOWN")
        mgr = manager("Catcher")
        before = look(ch1_through("ch1_rival_route103"), party=[mon(6)], balls=0, const="OLDALE_TOWN")
        index, milestone = mgr.milestone(before, visited_in(world))
        self.assertEqual(mgr.next_goal(before, world, milestone, index).kind, "shop")  # no flag stops it
        mgr.memory.no_balls["OLDALE_TOWN_MART"] = index
        self.assertNotEqual(mgr.next_goal(before, world, milestone, index).kind, "shop")
        self.assertEqual(mgr.next_goal(before, world, milestone, index + 1).kind, "shop")  # the story moved on

    def test_home_heals_once_mom_said_so_or_it_saw_her(self):
        """(review #4: step 5 went home to heal on FLAG_RESCUED_BIRCH) Home is a place to heal once MOM SAID so, or once it
        SAW her heal the party; the flag alone (every mark here sets it) is not enough."""
        def heal(heard=(), seen=0):
            mgr = manager("Story")
            mgr.memory.home_heals = seen
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", current="ROUTE101",
                               heard={"ROUTE 103", *heard})
            observation = look(ch1_through("ch1_rival_route103"), party=[mon(6, hp=5)])
            index, milestone = mgr.milestone(observation, visited_in(world))
            return mgr.next_goal(observation, world, milestone, index)

        self.assertNotEqual(heal().kind, "heal")
        self.assertEqual(heal(heard={"MOM: How are you doing? You look a little tired. I think you should rest a bit."}).kind,
                         "heal")
        self.assertEqual(heal(seen=1).kind, "heal")

    def test_in_danger_with_nowhere_known_it_looks_for_a_center(self):
        """(the step-5.1 development sweep: home is no longer known by a flag, and three Trainers walked on at 1-5 HP of 22
        and whited out) In danger and knowing no place to heal, it LOOKS for a POKéMON CENTER; merely under its heal_below
        it goes on (FAULT half); once a centre door is seen, it heals there."""
        mgr = manager("Trainer")
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", heard={"ROUTE 103"})
        observation = look(ch1_through("ch1_rival_route103"), party=[mon(6, hp=1, max_hp=23)])
        index, milestone = mgr.milestone(observation, visited_in(world))
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual(goal.kind, "find_center")
        moderate = look(ch1_through("ch1_rival_route103"), party=[mon(6, hp=9, max_hp=23)])  # 39 %: under 45 %, no danger
        self.assertNotEqual(mgr.next_goal(moderate, world, milestone, index).kind, "find_center")
        mgr.memory.landmarks[("0:2", (6, 16))] = "pokemon_center"
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual(goal.kind, "heal")

    def test_travelling_low_it_runs_whatever_its_temperament(self):
        """(the same sweep) A Trainer travelling at 1/22 HP fought a wild Wurmple (a travel's run was a temperament's draw
        on the first turn only): low, it runs, on any turn; with its HP up it is the temperament's draw again."""
        from ai_player.brain.battle import BattleFaults, BattleMind
        from ai_player.eyes.observation import BattleMon
        own = BattleMon(species="Torchic", dex=255, level=7, hp=1, max_hp=23, hp_bar=2, status="", types=("Fire",),
                        moves=(), pid=1, battler=0)
        foe = BattleMon(species="Wurmple", dex=265, level=2, hp=None, max_hp=None, hp_bar=48, status="", types=("Bug",),
                        moves=(), battler=1)
        for hp, runs in ((1, True), (23, None)):
            mind = BattleMind("Trainer", random.Random(4), "travel", BattleFaults())
            mind.memory.turns = 3  # not the first turn: the temperament's draw is the first turn's only
            decision = mind._run_or_not(replace(own, hp=hp), foe, hp / 23)  # noqa: SLF001
            if runs:
                self.assertEqual(decision.action, "run")
                self.assertIn("low", decision.reason)
            else:
                self.assertIsNone(decision)

    def test_a_hurt_walk_keeps_out_of_the_grass(self):
        """A person whose Pokemon is hurt keeps out of the tall grass on ANY walk (not only to heal); training is the grass."""
        from ai_player.brain.goals import HURT_GRASS_COST, Goal, GoalRunner
        for hp, kind, want in ((5, "go", HURT_GRASS_COST), (20, "go", 0.0), (5, "train", 0.0)):
            mgr = manager("Trainer")
            seen_costs = []
            nav = types.SimpleNamespace(grass_cost=0.0)
            runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(6, hp=hp)])), nav, mgr,
                                types.SimpleNamespace(purpose=""), lambda line: None)

            def inner(goal, milestone, index, current):
                seen_costs.append(nav.grass_cost)
                yield
                return True, "done"

            runner._pursue = inner  # noqa: SLF001
            drive(runner.pursue(Goal(kind, "a walk"), mgr.story.milestones[8], 8, lambda seen: 8))
            self.assertEqual((seen_costs, nav.grass_cost), ([want], 0.0), (hp, kind))

    def test_no_look_around_where_the_story_calls(self):
        """PROF. BIRCH cries for help on ROUTE 101: the story's thing is here and told, so the look-around waits (the
        sweep's AI walked away and he cried "Don't leave me like this!"); the draw is made later, not lost."""
        hits = 0
        for seed in range(60):
            mgr = manager("Catcher", seed=seed, quiet=False)
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", heard={"In my BAG! There's a POKé BALL!"})
            observation = look(ch1_through("ch1_birch"), const="ROUTE101", objects=[person(12, 10, gfx=97, local_id=5)])
            index, milestone = mgr.milestone(observation, visited_in(world))
            goal = mgr.next_goal(observation, world, milestone, index)
            hits += goal.kind == "explore"
            self.assertNotIn("0:2", mgr.memory.looked)
        self.assertEqual(hits, 0)

    def test_it_learns_that_mom_heals_by_seeing_it(self):
        from ai_player.brain.goals import GoalRunner
        mgr = manager("Story")
        mom = person(11, 10, gfx=mgr.story.looks["mom"].gfx[0], local_id=1)
        after = look(party=[mon(6, hp=20)])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: after), None, mgr, None, lambda line: None)
        runner._saw_mom_heal(mom, 0.25)  # noqa: SLF001
        self.assertEqual(mgr.memory.home_heals, 1)
        runner._saw_mom_heal(person(11, 10, gfx=22, local_id=2), 0.25)  # noqa: SLF001 - FAULT half: not MOM
        runner._saw_mom_heal(mom, 1.0)  # noqa: SLF001 - FAULT half: not hurt before
        self.assertEqual(mgr.memory.home_heals, 1)


class LoopGoalTests(unittest.TestCase):
    """(build step 5.1, the step-5 review's finding 5) A STORY goal that keeps failing is put aside like any other."""

    def test_a_failing_story_goal_yields_with_a_reason(self):
        from ai_player.brain.goals import ASIDE, COOLDOWN_DECISIONS, FAIL_LIMIT
        mgr = manager("Story", train_off=True)
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "ROUTE103", current="ROUTE101", heard={"went out to ROUTE 103"})
        mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
        observation = look(ch1_through("ch1_rival_route103"), party=[mon(9)])
        index, milestone = mgr.milestone(observation, visited_in(world))
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.key), ("go", "go:ROUTE103"))
        for _ in range(FAIL_LIMIT):
            mgr.outcome(goal, False)
        aside = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual(aside.kind, "look_around")
        self.assertEqual(aside.key, f"{ASIDE}go:ROUTE103")
        self.assertIn("put aside until decision", aside.reason)
        for _ in range(COOLDOWN_DECISIONS):
            aside = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual(aside.key, "go:ROUTE103")  # tried again after the cooldown


class SceneWallTests(unittest.TestCase):
    """(build step 5.1, the development sweep step51dev5: after looking round LITTLEROOT, every walk to the rival's house
    chose the frontier past the twin and met her twice per walk, until the patience ran out) The tiles a scene sent the
    player back from are carried from goal to goal WITHIN a milestone; a new milestone starts with none."""

    def test_scene_walls_carry_within_a_milestone(self):
        from ai_player.brain.goals import Goal, GoalRunner
        mgr = manager("Catcher")
        nav = types.SimpleNamespace(grass_cost=0.0, carried_scene_walls=None, scene_walls={})
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(6)])), nav, mgr,
                            types.SimpleNamespace(purpose=""), lambda line: None)
        seen = []

        def inner(goal, milestone, index, current):
            seen.append({k: set(v) for k, v in (nav.carried_scene_walls or {}).items()})
            nav.scene_walls = {**{k: set(v) for k, v in (nav.carried_scene_walls or {}).items()}}
            if goal.reason == "meets the twin":
                nav.scene_walls.setdefault("0:9", set()).update({(10, 1), (11, 1)})
            yield
            return False, "stuck: nothing new"

        runner._pursue = inner  # noqa: SLF001
        house = mgr.story.milestones[mgr.story.index("ch1_rival_house")]
        birch = mgr.story.milestones[mgr.story.index("ch1_birch")]
        for reason, milestone in (("meets the twin", house), ("again", house), ("the story moved on", birch)):
            drive(runner.pursue(Goal("go", reason), milestone, 4, lambda s: 4))
        self.assertEqual(seen[0], {})
        self.assertEqual(seen[1], {"0:9": {(10, 1), (11, 1)}})  # FAULT half: each walk started with none
        self.assertEqual(seen[2], {})  # a new milestone: the twin may let it pass now
        self.assertIsNone(nav.carried_scene_walls)

    def test_the_navigator_starts_from_the_walls_it_is_handed(self):
        from ai_player.brain.navigator import Intent
        for carried, want in (({"0:9": {(10, 1)}}, {"0:9": {(10, 1)}}), (None, {})):
            hands = Hands(_FakeEyes([look()]), _Controls(), random.Random(1), random.Random(1), None, lambda line: None)
            nav = Navigator(hands, WorldMemory(), random.Random(1))
            nav.carried_scene_walls = carried
            drive(nav.run(Intent("nothing", 0, lambda n, l: None, lambda l: False), "test"))
            self.assertEqual(nav.scene_walls, want)
            if carried:
                self.assertIsNot(nav.scene_walls["0:9"], carried["0:9"])  # a copy: the intent's own changes stay its own


class SmallTests(unittest.TestCase):
    """(build step 5.1, the step-5 verifier's small items)"""

    def test_milestone_lines_say_how_a_milestone_passed(self):
        story = load_story("BOY")
        hands = types.SimpleNamespace(told=[], pad=types.SimpleNamespace(frames=5), note=lambda *a, **k: None)
        hands.tell = hands.told.append
        report = {"milestones": []}
        brain = HandsBrain.__new__(HandsBrain)
        observation = look({}, frame=900)
        world = world_with("INSIDE_OF_TRUCK")
        brain._milestone_line(hands, observation, story, [0, story.milestones[0]], 1, story.milestones[1], report,  # noqa: SLF001
                              visited_in(world))
        line = next(t for t in hands.told if "MILESTONE ch1_intro" in t)
        self.assertIn("passed as a WAYPOINT", line)  # FAULT half: "done" quoting VAR_LITTLEROOT_INTRO_STATE=0
        self.assertNotIn(" done at", line)
        self.assertEqual(report["milestones"][0]["how"], "passed as a WAYPOINT")

    def test_a_battle_line_says_no_ball_when_there_is_none(self):
        from ai_player.brain.battle import BattleFaults, BattleMind
        from ai_player.eyes.observation import BattleMon
        foe = BattleMon(species="Zigzagoon", dex=263, level=2, hp=None, max_hp=None, hp_bar=48, status="",
                        types=("Normal",), moves=(), battler=1)
        battle = BattleView(kind="wild", double=False, type_flags=0, opponent_trainer_id=None, own=(), foe=(foe,))
        for balls, want, never in ((0, "it has no POKé BALL", "it WANTS it"), (5, "it WANTS it", "no POKé BALL")):
            mind = BattleMind("Catcher", random.Random(1), "travel", BattleFaults())
            seen = replace(battle_look(100, None), battle=battle,
                           bag=BagSummary(balls=(("Poké Ball", balls),) if balls else (), healing=(), ball_total=balls),
                           progress=look().progress)
            line = mind.begin(seen)
            self.assertIn(want, line)
            self.assertNotIn(never, line)

    def test_the_step5_regexes_with_both_cases(self):
        """Every regex added in step 5, printed, with a case it must match and one it must not."""
        from ai_player.brain.goals import OUTDOOR, ROAM_LINE, _WORD_CHARS
        from ai_player.gates.rate_step5 import told_before
        print(f"\n  ROAM_LINE = {ROAM_LINE.pattern!r}\n  OUTDOOR = {OUTDOOR.pattern!r}\n  _names word chars = {_WORD_CHARS!r}")
        roam = ("roam: 37 training steps (41 pressed, 4 ran into a battle or a scene); (2 spins = 1 reversals + 1 in place) "
                "4 wild encounters, 3 fled, 1 won, 0 caught, 0 lost; 0 trainer battles")
        self.assertIsNotNone(ROAM_LINE.search(roam))
        self.assertIsNone(ROAM_LINE.search("roam: no grass found: stuck"))
        for name in ("ROUTE101", "OLDALE_TOWN", "PETALBURG_CITY"):
            self.assertIsNotNone(OUTDOOR.match(name), name)
        for name in ("LITTLEROOT_TOWN_MAYS_HOUSE_1F", "OLDALE_TOWN_MART", "ROUTE104_PRETTY_PETAL_FLOWER_SHOP", "INSIDE_OF_TRUCK"):
            self.assertIsNone(OUTDOOR.match(name), name)
        self.assertTrue(heard_words({"MAY went out to ROUTE 103."}, "ROUTE 103"))
        self.assertFalse(heard_words({"MAY went out to ROUTE 1030."}, "ROUTE 103"))
        records = [{"decision": "read", "frame": 10, "reason": "Oh, MAY went out to ROUTE 103 just a little while ago."},
                   {"decision": "goal", "action": "go", "frame": 20, "extra": {"map": "ROUTE103"},
                    "reason": "Find the rival: to ROUTE103 (the game said: 'Oh, MAY went out to ROUTE 103 just a little "
                              "while ago.')"}]
        self.assertEqual(told_before(records), [])
        self.assertEqual(len(told_before([records[1], records[0]])), 1)  # FAULT half: the goal before the page


class VerifierRoundTests(unittest.TestCase):
    """(build step 5.1, the step-5.1 verifier's round, 2026-10-14) Two documented rules no test covered (its mutants MY3,
    MY4), the look-around's "new place" in a run that carries on, the detours that failed at once, the story aside counted
    in decisions only, the walk a battle ate, and the told draws."""

    def test_no_look_around_while_in_danger(self):
        """README B: "never in danger" (the verifier's MY3, not caught): a party with a Pokemon fainted, or its strongest
        under a third, is not looked round with: the draw waits (it is NOT used up), and a healthy party draws."""
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN")
        mgr = manager("Catcher", quiet=False)
        step = None
        for party, want in (([mon(9, hp=0, max_hp=30), mon(5, hp=20, max_hp=20, pid=2)], False),
                            ([mon(9, hp=5, max_hp=30)], False), ([mon(9, hp=30, max_hp=30)], True)):
            seen = look(ch1_through("ch1_rival_route103"), party=party, const="OLDALE_TOWN")
            self.assertEqual(mgr.may_look_around(seen, world, step), want, party)
        hurt = look(ch1_through("ch1_rival_route103"), party=[mon(9, hp=0, max_hp=30)], const="OLDALE_TOWN")
        index, milestone = mgr.milestone(hurt, visited_in(world))
        mgr.next_goal(hurt, world, milestone, index)
        self.assertNotIn("0:3", mgr.memory.looked)  # the draw waits for a healthy decision there

    def test_the_bag_gone_is_handed_back_at_once(self):
        """`bag_or_its_question` returns at once when the bag is GONE (the verifier's MY4, not caught: the branch fired in
        none of the graded runs, so only a unit test can carry it): with that return removed it watches the empty screen
        for its whole `STARTER_WAIT` and reports the bag took no input."""
        from ai_player.skills.story import STARTER_WAIT, bag_or_its_question
        hands = script_hands(lambda frames: screen_look(frames, ui=None, state="OVERWORLD", script=True))
        result = drive(bag_or_its_question(hands, "the bag"), budget=STARTER_WAIT + 50)
        self.assertIsNotNone(result)
        self.assertEqual(result.screen.game_state, "OVERWORLD")
        self.assertLess(hands.pad.frames, 5, hands.pad.frames)
        # FAULT half: the bag still on screen and busy (a ball opening): it waits, and gives up after STARTER_WAIT
        from ai_player.eyes.observation import MenuView
        from ai_player.eyes.screens import STARTER_OPTIONS
        busy = MenuView(kind="choose_starter", options=STARTER_OPTIONS, cursor=1, accepts_input=False)
        hands = script_hands(lambda frames: screen_look(frames, ui=busy, state="CHOOSE_STARTER"))
        self.assertIsNone(drive(bag_or_its_question(hands, "the bag"), budget=STARTER_WAIT + 50))
        self.assertGreaterEqual(hands.pad.frames, STARTER_WAIT)

    def test_a_resumed_run_looks_round_only_new_places(self):
        """The verifier: a run that carried on from an earlier run's memory "looked round a new place, LITTLEROOT_TOWN",
        its home town. The maps its world memory had stood on when the session's FIRST decision was made are no new places;
        a map first stood on later in the session is."""
        hits_old = hits_new = 0
        for seed in range(80):
            mgr = manager("Catcher", seed=seed, quiet=False, train_off=True, resumed=True)
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN",
                               heard={"Oh, MAY went out to ROUTE 103 just a little while ago."})
            mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
            seen = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
            index, milestone = mgr.milestone(seen, visited_in(world))
            hits_old += mgr.next_goal(seen, world, milestone, index).kind == "explore"
            self.assertEqual(mgr.memory.known_before, {"0:1", "0:2", "0:3"})
            # first stood on in THIS session (ROUTE 102: not where the rival is, so the story does not hold the draw)
            world.maps["0:9"] = MapMemory("0:9", "ROUTE102", "ROUTE102")
            world.maps["0:9"].visits[(1, 1)] = 1
            world._last.key = "0:9"  # noqa: SLF001
            there = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="ROUTE102")
            goal = mgr.next_goal(there, world, milestone, index)
            hits_new += goal.kind == "explore"
            if goal.kind == "explore":
                self.assertIn("a new place, ROUTE102", goal.reason)
        self.assertEqual(hits_old, 0)  # FAULT half: before the fix OLDALE (known from the earlier run) was "new"
        self.assertGreater(hits_new, 40)

    def test_a_draw_that_chooses_nothing_is_told(self):
        told = []
        explored = 0
        for seed in range(60):
            mgr = manager("Story", seed=seed, quiet=False, train_off=True)
            mgr.say = told.append
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN",
                               heard={"Oh, MAY went out to ROUTE 103 just a little while ago."})
            mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
            seen = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
            index, milestone = mgr.milestone(seen, visited_in(world))
            explored += mgr.next_goal(seen, world, milestone, index).kind == "explore"
        quiet = [line for line in told if "it goes on without looking round" in line]
        self.assertEqual(len(quiet) + explored, 60)  # every draw is in the log: a goal, or a told line
        self.assertTrue(all("draw " in line and ">= 0.55, the Story's 0.55" in line for line in quiet), quiet[:2])

    def test_after_passing_new_places_it_looks_round_the_next(self):
        """The verifier: "per-run curiosity can be almost zero" (and the development sweep step51vdev1's Story seed 4: all
        three look-around draws chose nothing). After LOOK_DEBT new places gone past in a row, the next one's odds are
        raised to CURIOUS_ODDS_CAP (build step 5.2: a dice throw, never certain; 5.1 looked without a draw), said so; a
        failed draw counts one more, a look round starts the count again."""
        from ai_player.brain.goals import CURIOUS_ODDS_CAP, LOOK_DEBT
        forced = drawn = 0
        for seed in range(200):
            for debt in (LOOK_DEBT, 0):
                mgr = manager("Story", seed=seed, quiet=False, train_off=True)
                mgr.memory.passed_new = debt
                world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN",
                                   heard={"Oh, MAY went out to ROUTE 103 just a little while ago."})
                mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
                seen = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
                index, milestone = mgr.milestone(seen, visited_in(world))
                goal = mgr.next_goal(seen, world, milestone, index)
                if debt:
                    forced += goal.kind == "explore"
                    self.assertEqual(mgr.memory.passed_new, 0 if goal.kind == "explore" else LOOK_DEBT + 1)
                    if goal.kind == "explore":
                        self.assertIn(f"gone past {LOOK_DEBT} new places in a row", goal.reason)
                else:
                    drawn += goal.kind == "explore"
                    self.assertEqual(mgr.memory.passed_new, 0 if goal.kind == "explore" else 1)
        self.assertLess(abs(forced / 200 - CURIOUS_ODDS_CAP), 0.06)  # the dice, at the cap: never 200 of 200
        self.assertLess(forced, 200)
        self.assertLess(drawn, 150)  # FAULT half: without the debt the Story's draw passes some new places by
        self.assertGreater(forced, drawn + 20)

    def detour_runner(self, places, excluded=()):
        from ai_player.brain.goals import Goal, GoalRunner
        from ai_player.brain.navigator import Target, stale_reason
        mgr = manager("Trainer")
        intents = []

        def run(intent, why):
            intents.append(intent)
            yield
            return "budget: 1500 frames ran out"

        excluded = set(excluded)
        world = world_with("ROUTE101", current="ROUTE101")
        memory = world.maps["0:1"]
        for x in range(0, 21):  # (build step 5.2) ROUTE 101 seen round the player at (10, 10): every place can be walked to
            for y in range(0, 21):
                memory.tiles[(x, y)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (10, 10))
        fake_nav = types.SimpleNamespace(rng=random.Random(1), is_excluded=lambda t: t.tile in excluded,
                                         where=lambda seen: (memory, (10, 10)), world=world)
        nav = types.SimpleNamespace(run=run, world=world)
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look()), nav, mgr, types.SimpleNamespace(purpose=""),
                            lambda line: None)
        targets = [Target(kind, tile, f"a {kind}") for kind, tile in places]
        from ai_player.brain import goals as goals_module
        with mock.patch.object(goals_module, "candidates", lambda *a, **k: list(targets)), \
                mock.patch.object(goals_module, "pick", lambda found, rng: found[0]):
            drive(runner._detour(Goal("detour", "on the way", steps=1500)))  # noqa: SLF001
            choose = intents[0].choose
            return choose, fake_nav, excluded, stale_reason

    def test_a_detour_walks_to_a_place_off_the_way_and_swaps_one_it_cannot_reach(self):
        """The verifier's round: 11 of the 12 detours of the first round's graded CH1 runs (56 of 63 over all its plans)
        ended at once (the frontier chosen was seen past
        after one step, and the detour chose that stale place again and again, "51 decisions in a row without a frame
        passing"). Now: a WANDER target on the chosen place's tile (never stale), at least DETOUR_MIN_TILES away (a road is
        no detour), the same place while it can be reached, another once it cannot, at most DETOUR_TRIES."""
        from ai_player.brain.goals import DETOUR_MIN_TILES, DETOUR_TRIES
        from ai_player.brain import goals as goals_module
        places = [("frontier", (11, 10)), ("road", (16, 10)), ("frontier", (16, 10)), ("grass", (10, 18)),
                  ("people", (3, 10)), ("frontier", (10, 4))]
        choose, fake_nav, excluded, stale_reason = self.detour_runner(places)
        targets = [goals_module.Target(kind, tile, f"a {kind}") for kind, tile in places]
        with mock.patch.object(goals_module, "candidates", lambda *a, **k: list(targets)), \
                mock.patch.object(goals_module, "pick", lambda found, rng: found[0]):
            first = choose(fake_nav, look())
            self.assertEqual((first.kind, first.tile), ("wander", (16, 10)))  # not the frontier a step away, not a road
            self.assertGreaterEqual(abs(first.tile[0] - 10) + abs(first.tile[1] - 10), DETOUR_MIN_TILES)
            memory = MapMemory("0:1", "ROUTE101", "ROUTE101")
            memory.tiles[(16, 10)] = TileFact(True, True, False, False, None, False, False, 3, "NORMAL", 0, (0, 0))
            self.assertIsNone(stale_reason(memory, first))  # FAULT half: as a frontier it went stale once seen past
            self.assertIs(choose(fake_nav, look()), first)  # the same place while it can be reached
            excluded.add((16, 10))
            second = choose(fake_nav, look())
            self.assertEqual(second.tile, (10, 18))  # another place once that one cannot be reached
            excluded.add((10, 18))
            third = choose(fake_nav, look())
            self.assertEqual(third.tile, (3, 10))
            excluded.add((3, 10))
            self.assertIsNone(choose(fake_nav, look()))  # DETOUR_TRIES places at most
            self.assertEqual(DETOUR_TRIES, 3)

    def test_a_story_goal_put_aside_comes_back_after_its_frames(self):
        """The verifier: "the story-goal cooldown counts DECISIONS" (ten looks round, about 32,000 frames, in the live CH2
        arm). The aside ends after COOLDOWN_DECISIONS decisions OR STORY_ASIDE_FRAMES frames, whichever comes first."""
        from ai_player.brain.goals import ASIDE, COOLDOWN_DECISIONS, FAIL_LIMIT, STORY_ASIDE_FRAMES
        mgr = manager("Story", train_off=True)
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "ROUTE103", current="ROUTE101", heard={"went out to ROUTE 103"})
        mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
        seen = look(ch1_through("ch1_rival_route103"), party=[mon(9)], frame=10_000)
        index, milestone = mgr.milestone(seen, visited_in(world))
        goal = mgr.next_goal(seen, world, milestone, index)
        for _ in range(FAIL_LIMIT):
            mgr.outcome(goal, False)
        kinds = []
        for step in range(4):  # four decisions, far fewer than COOLDOWN_DECISIONS, spread over the frames
            frame = 10_000 + step * (STORY_ASIDE_FRAMES // 3 + 10)
            kinds.append(mgr.next_goal(replace(seen, frame=frame), world, milestone, index))
        self.assertLess(4, COOLDOWN_DECISIONS)
        self.assertEqual([g.key for g in kinds[:3]], [f"{ASIDE}go:ROUTE103"] * 3)
        self.assertIn("or frame", kinds[0].reason)
        self.assertEqual(kinds[3].key, "go:ROUTE103")  # FAULT half: by decisions alone it would wait 12 decisions
        self.assertIn("tried again after", kinds[3].reason)

    def test_a_walk_whose_battles_ate_its_budget_walks_on(self):
        """The verifier: the live CH2 arm's two walks to PETALBURG CITY met 8 and 13 battles on ROUTE 102, ran out their
        9,000 frames and were put aside as FAILING. A walk walks on for the frames its battles took (at most its own budget
        again, at most GO_BATTLE_EXTENSIONS times); a walk that simply ran out, with no long battle, does not."""
        from ai_player.brain.goals import GO_BATTLE_EXTENSIONS, GO_FRAMES, Goal, GoalRunner
        for battle_frames, want_calls in ((3000, 2), (200, 1)):
            mgr = manager("Catcher")
            hands = types.SimpleNamespace(look=lambda: look(party=[mon(9)]), watchers=[])
            calls = []

            def travel(target, why, budget, done, battle_frames=battle_frames, hands=hands):
                calls.append(budget)
                if len(calls) == 1:  # the first walk: a battle of `battle_frames` frames, then the budget ran out
                    base = look(party=[mon(9)])
                    fight = replace(base, screen=replace(base.screen, in_battle=True, game_state="BATTLE"))
                    for watcher in list(hands.watchers):
                        watcher(replace(fight, frame=100))
                        watcher(replace(base, frame=100 + battle_frames))
                    yield
                    return "budget: 9000 frames ran out"
                yield
                return "done: travel to ROUTE103"

            runner = GoalRunner(hands, types.SimpleNamespace(world=world_with("ROUTE101", current="ROUTE101"),
                                                             battle_log=[]), mgr, types.SimpleNamespace(purpose=""),
                                lambda line: None)
            runner._travel = travel  # noqa: SLF001
            ok, outcome = drive(runner.pursue(Goal("go", "to ROUTE 103", map="ROUTE103", key="go:ROUTE103"),
                                              mgr.story.milestones[8], 8, lambda seen: 8))
            self.assertEqual(len(calls), want_calls, (battle_frames, calls))
            if want_calls == 2:
                self.assertEqual(calls, [GO_FRAMES, 3000])
                self.assertTrue(ok, outcome)
                self.assertIn("walked on 3000 frames after its battles", outcome)
            else:
                self.assertFalse(ok)  # FAULT half: a short battle is no reason to walk on
            self.assertEqual(hands.watchers, [])  # the battle clock is removed after the walk
        self.assertGreaterEqual(GO_BATTLE_EXTENSIONS, 1)

    def test_the_grader_counts_curiosity_the_story_did_not_need(self):
        """The verifier: "the pick_up is the rival's POKé BALL, a step the story requires; it counts as curiosity in BOTH
        arms". A curiosity goal in which a milestone passed is the story's own (`intent_mix` free_share)."""
        from ai_player.gates.rate_step5 import intent_mix
        records = [{"decision": "goal", "action": "go", "frame": 0},
                   {"decision": "goal", "action": "pick_up", "frame": 100},
                   {"decision": "tell", "frame": 400, "reason": "[AI-GOALS] goal pick_up not done"},
                   {"decision": "milestone", "frame": 400, "action": "ch1_birch"},
                   {"decision": "goal", "action": "explore", "frame": 400},
                   {"decision": "goal", "action": "go", "frame": 1000},
                   {"decision": "watch", "frame": 2000}]
        mix = intent_mix(records)
        self.assertEqual(mix["frames"], {"explore": 600, "go": 1100, "pick_up": 300})
        self.assertEqual(mix["story_own"], [(100, "pick_up", 300)])
        self.assertEqual(mix["free_frames"], 600)  # FAULT half: the rival's ball counted as curiosity, 900
        self.assertAlmostEqual(mix["free_share"], 0.3)
        self.assertAlmostEqual(mix["curiosity_share"], 0.45)

    def test_the_grader_finds_where_no_beeline_went(self):
        """`off_beeline`: the tiles a run stood on that NO control run stood on; a control run against the OTHER control
        runs (its own spread); and how those tiles differ between runs of one personality."""
        from ai_player.gates.rate_step5 import off_beeline
        control = [{"seed": 1, "personality": "Story", "_tiles": {"A 1,1", "A 1,2"}},
                   {"seed": 2, "personality": "Story", "_tiles": {"A 1,1", "A 9,9"}}]
        runs = [{"seed": 1, "personality": "Story", "_tiles": {"A 1,1", "A 5,5", "A 5,6"}},
                {"seed": 2, "personality": "Story", "_tiles": {"A 1,2", "A 7,7"}}]
        found = off_beeline(runs, control)
        self.assertEqual(found["runs"], {1: 2, 2: 1})  # FAULT half: "A 1,2" is on the corridor, not off it
        self.assertEqual(found["control"], {1: 1, 2: 1})  # each control run's own tile no other stood on
        self.assertEqual(found["corridor"], 3)
        self.assertEqual(found["pairs_mean"], 1.0)  # no off-beeline tile shared
        same = off_beeline([runs[0], {**runs[0], "seed": 3}], control)
        self.assertEqual(same["pairs_mean"], 0.0)  # a fixed side trip: identical off-beeline tiles

    def test_the_grader_measures_a_streak_of_asides(self):
        """`aside_streaks`: the streak of goals put aside for one story goal, from the first aside to the next goal that is
        not that aside (the verifier's CH2 case: 10 in a row, about 32,000 frames)."""
        from ai_player.brain.goals import ASIDE
        from ai_player.gates.rate_step5 import BOUNDS, aside_streaks
        aside = {"key": f"{ASIDE}go:PETALBURG_CITY"}
        records = [{"decision": "goal", "action": "go", "frame": 0, "extra": {"key": "go:PETALBURG_CITY"}}]
        records += [{"decision": "goal", "action": "look_around", "frame": 9000 + 3200 * i, "extra": aside} for i in range(10)]
        records += [{"decision": "goal", "action": "go", "frame": 41000, "extra": {"key": "go:PETALBURG_CITY"}},
                    {"decision": "watch", "frame": 42000}]
        self.assertEqual(aside_streaks(records), [("go:PETALBURG_CITY", 9000, 32000, 10)])
        self.assertGreater(32000, BOUNDS["ASIDE_STREAK_MAX"])  # the verifier's case is over the bound: it would fail

    def test_the_grader_takes_the_battles_out_of_the_time(self):
        """`time_to_dex`: the way to the POKéDEX in the AI's frames, its NEEDS goals' frames, and the frames a battle was on
        screen OUTSIDE them (the grass's dice); `outside_nb` is what is left: the AI's own walking, talking and looking."""
        from ai_player.gates.rate_step5 import time_to_dex
        records = [{"decision": "goal", "action": "go", "frame": 0, "digest": "f0 overworld"},
                   {"decision": "x", "frame": 100, "digest": "f100 battle wild"},  # a battle on the walk: 300 frames
                   {"decision": "x", "frame": 400, "digest": "f400 overworld"},
                   {"decision": "goal", "action": "train", "frame": 1000, "digest": "f1000 overworld"},
                   {"decision": "x", "frame": 1200, "digest": "f1200 battle wild"},  # inside the needs: not counted twice
                   {"decision": "x", "frame": 1500, "digest": "f1500 overworld"},
                   {"decision": "goal", "action": "go", "frame": 2000, "digest": "f2000 overworld"},
                   {"decision": "tell", "frame": 5000, "reason": "[AI-GOALS] MILESTONE ch1_pokedex done at f5000 (Back)",
                    "digest": "f5000 overworld"}]
        found = time_to_dex(records)
        self.assertEqual(found, {"end": 5000, "begin": 0, "needs": 1000, "battles": 300, "outside": 4000,
                                 "outside_nb": 3700})
        self.assertIsNone(time_to_dex(records[:-1]))  # never reached
        # (the second round) a chapter-2 run is timed from its own first record, where its chapter 1 stopped
        later = [{**r, "frame": r["frame"] + 100_000,
                  "reason": str(r.get("reason", "")).replace("f5000", "f105000").replace("ch1_pokedex", "ch2_wally")}
                 for r in records]
        found = time_to_dex(later, "ch2_wally", since_start=True)
        self.assertEqual((found["begin"], found["outside"], found["outside_nb"]), (100_000, 4000, 3700))

    def test_the_training_bound_is_rederived_by_personality(self):
        """The verifier: "the training bounds (60 steps, 3 won) were carried over, not re-derived". The steps bound is now
        the personality's own `train_min_steps` times CH1_TRAIN_STEPS_SHARE (Story 72, Catcher 90, Trainer 135)."""
        from ai_player.gates.rate_step5 import train_steps_min, trained_by_game
        self.assertEqual({p: train_steps_min(p) for p in ("Story", "Catcher", "Trainer")},
                         {"Story": 72, "Catcher": 90, "Trainer": 135})
        self.assertFalse(trained_by_game({"personality": "Trainer", "game_train_steps": 100, "game_train_won": 6}))
        self.assertTrue(trained_by_game({"personality": "Trainer", "game_train_steps": 135, "game_train_won": 3}))
        self.assertFalse(trained_by_game({"personality": "Story", "game_train_steps": 200, "game_train_won": 2}))

    def test_the_training_bound_follows_the_personality_it_played_as(self):
        """(Corrected after the graded sweep on 501-520 failed it in 2 of 20: seeds 506 and 516 had DRIFTED into the Story
        personality during the rival's milestone, and trained to the Story's minimum.) The bound is the lowest minimum
        among the personalities a run played AS there (`rival_actives`), the base's when none is recorded."""
        from ai_player.gates.rate_step5 import train_steps_min_run, trained_by_game
        drifted = {"personality": "Trainer", "rival_actives": ["Story", "Trainer"], "game_train_steps": 83,
                   "game_train_won": 4}
        self.assertEqual(train_steps_min_run(drifted), 72)
        self.assertTrue(trained_by_game(drifted))  # FAULT half: by the base Trainer's 135 it failed
        steady = {"personality": "Trainer", "rival_actives": ["Trainer"], "game_train_steps": 83, "game_train_won": 4}
        self.assertEqual(train_steps_min_run(steady), 135)
        self.assertFalse(trained_by_game(steady))
        self.assertEqual(train_steps_min_run({"personality": "Catcher"}), 90)

    def test_the_lose3_check_grades_the_runs_that_reached_a_third_loss(self):
        """(Corrected after the graded sweep on 501-520: seed 503 lost twice and ended on its patience, testing nothing of
        the stop.) Every run the GAME recorded a third loss in must end at MAX_LOSSES; the arm must reach one in at least
        LOSE3_REACH_MIN of its runs."""
        from ai_player.gates.rate_step5 import STOP_WITHIN, step51_verdicts
        from ai_player.mode import MAX_LOSSES
        stop = f"play: stuck: {MAX_LOSSES} battles lost (MAX_LOSSES {MAX_LOSSES})"

        def row(seed, reason, losses, last, end):
            return {"plan": "LOSE3", "seed": seed, "reason": reason, "losses_ai": losses, "losses_told": losses,
                    "losses_game": losses, "last_loss_f": last, "frames": end, "await_ai_max": 0, "await_game_max": 0}

        reached = [row(s, stop, 3, 1000, 1600) for s in (1, 2, 3, 4)]
        short = row(5, "play: stuck: no progress for 161095 frames", 2, 900, 245000)

        def verdict(rows):
            # (build step 5.3, A1-4) by its check ID, no longer by a text prefix; each row carries the MAX_LOSSES the
            # harness recorded the run playing with (`play_harness.play`), which LOSE3 grades by since A1-2
            return check_by_id(step51_verdicts({"LOSE3": [{**r, "max_losses": MAX_LOSSES} for r in rows]}),
                               "R5.LOSE3").status == "PASS"

        self.assertTrue(verdict(reached + [short]))  # FAULT half: graded as before, the short run failed it
        self.assertFalse(verdict([row(1, "play: stopped: not finished", 3, 1000, 1000 + STOP_WITHIN + 1)] + reached))
        self.assertFalse(verdict(reached[:1] + [short, short, short]))  # the arm must reach a third loss


def check_by_id(results, check_id: str):
    """(Build step 5.3, A1-4) the ONE typed check `check_id` among a grader's results (`grader_checks.Check`): the tests
    find a check by its stable id, no longer by the start of its text (a reworded line moved no test before, and a
    rewording that matched two checks picked the first)."""
    found = [check for check in results if getattr(check, "id", None) == check_id]
    if len(found) != 1:
        raise AssertionError(f"{check_id}: {len(found)} checks with this id among {[getattr(c, 'id', c) for c in results]}")
    return found[0]


class _Draws:
    """A goal manager's seeded stream that always draws `value` (a draw the dice would not pass)."""

    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


def ch2_dad_marks() -> dict[str, int]:
    """Marks at DAD's milestone (chapter 2: PETALBURG CITY visited, DAD not met yet)."""
    return {**ch1_through("ch2_oldale"), "VISITED_OLDALE_TOWN": 1, "VISITED_PETALBURG_CITY": 1}


def petalburg_world(current: str = "PETALBURG_CITY") -> WorldMemory:
    """OLDALE (its POKéMON CENTER and MART been in), ROUTE 102 and PETALBURG CITY, joined by their edges (OLDALE <- ROUTE
    102 <- PETALBURG): keys 0:1, 0:2, 0:3."""
    world = world_with("OLDALE_TOWN", "ROUTE102", "PETALBURG_CITY", current=current, center_from="OLDALE_TOWN",
                       heard={"INTERVIEWER: …We brought you this report from in front of PETALBURG GYM."})
    world.maps["9:9"] = MapMemory("9:9", "OLDALE_TOWN_MART", "OLDALE_TOWN_MART")
    world.warps["0:1|14,6"] = {"to": "9:9", "arrival": [3, 7], "uses": 1, "inferred": False}
    world.connections = [{"source": "0:1", "target": "0:2", "direction": "left"},
                         {"source": "0:2", "target": "0:3", "direction": "left"}]
    return world


class SecondRoundTests(unittest.TestCase):
    """(the step-5.1 verifier's SECOND round, 2026-10-14) Its failure: the live CH2T arm, the Story player in chapter 2,
    under the intent-mix floor (16 % once a DROPPED goal no longer counted the WALLY scene after it as an errand), because
    it searched PETALBURG CITY door by door for the GYM and walked back to OLDALE to heal and to shop; its two mutants no
    test caught (V3: the walk on once instead of twice; V9: SETTLE_FREE 1, in `PlayLoopTests`); and its weak proofs (a
    level counted by the party's sum; which personality judged the run trained; the graders' errand share counting the
    story's own curiosity). Each rule here has its mutant in `revert_step5.py` (G107-G123)."""

    def door(self, x: int, y: int, metatile: int) -> Tile:
        return Tile(x=x, y=y, dx=x - 10, dy=y - 10, metatile=metatile, behavior=0x69, behavior_name="ANIMATED_DOOR",
                    collision=1, elevation=3, blocked=True, water=False, encounter=None, tall_grass=False, ledge=None,
                    door=True, warp=True, half_visible=False)

    # ---- the gym by its look
    def test_a_gym_door_is_recognised_by_its_look(self):
        world = world_with("ROUTE102", "PETALBURG_CITY", current="PETALBURG_CITY")
        mgr = manager()
        mgr.memory.landmarks = world.landmarks
        gym, center = mgr.story.looks["gym_door"].metatile[0], mgr.story.looks["pokemon_center_door"].metatile[0]
        self.assertEqual(gym, 0x1CD)  # METATILE_General_Door_Gym (`extract_milestones.py --verify`)
        mgr.notice(look(const="PETALBURG_CITY", map_number=2, tiles=[self.door(15, 8, gym), self.door(20, 16, center)]))
        self.assertEqual(world.landmarks, {("0:2", (15, 8)): "gym", ("0:2", (20, 16)): "pokemon_center"})  # FAULT: no gym
        self.assertEqual(mgr.door_of(world, "PETALBURG_CITY_GYM"), ("0:2", (15, 8)))
        self.assertIsNone(mgr.door_of(world, "RUSTBORO_CITY_GYM"))  # another town's gym: not this door
        self.assertIsNone(mgr.door_of(world, "PETALBURG_CITY_MART"))  # not a gym

    def test_a_walk_to_a_gym_goes_in_by_its_door_once_seen(self):
        """Its door known: straight to it and in. Not known yet: walked as to any map, the walk ending as soon as the door
        is SEEN, then in (CH2T searched four houses, the MART and the POKéMON CENTER's two floors first)."""
        from ai_player.brain.goals import Goal, GoalRunner
        for known_first in (True, False):
            world = petalburg_world()
            mgr = manager("Story")
            arrive = look(ch2_dad_marks(), party=[mon(9)], const="PETALBURG_CITY", map_number=3)
            walks, insides, stopped = [], [], []

            def walk(target, why, budget, done, mgr=mgr, walks=walks, stopped=stopped, arrive=arrive):
                walks.append(target)
                stopped.append(done(arrive))  # before the door is seen the walk goes on
                mgr.memory.landmarks[("0:3", (15, 8))] = "gym"  # the door comes into view on the way
                stopped.append(done(arrive))
                yield
                return "done: travel to PETALBURG_CITY_GYM"

            def inside(goal, world=world, insides=insides):
                insides.append((goal.map, goal.via, goal.tile))
                world.maps["0:4"] = MapMemory("0:4", "PETALBURG_CITY_GYM", "PETALBURG_CITY_GYM")
                world.maps["0:4"].visits[(1, 1)] = 1
                world._last.key = "0:4"  # noqa: SLF001
                yield
                return "entered"

            if known_first:
                mgr.memory.landmarks[("0:3", (15, 8))] = "gym"
            nav = types.SimpleNamespace(world=world, battle_log=[])
            runner = GoalRunner(types.SimpleNamespace(look=lambda arrive=arrive: arrive), nav, mgr,
                                types.SimpleNamespace(purpose=""), lambda line: None)
            runner._walk_on_after_battles = walk  # noqa: SLF001
            runner._go_inside = inside  # noqa: SLF001
            index = mgr.story.index("ch2_dad")
            ok, outcome = drive(runner.pursue(Goal("go", "DAD", map="PETALBURG_CITY_GYM", key="go:PETALBURG_CITY_GYM"),
                                              mgr.story.milestones[index], index, lambda seen, index=index: index))
            self.assertTrue(ok, outcome)
            self.assertIn("recognised by its look", outcome)
            self.assertEqual(insides, [("PETALBURG_CITY_GYM", "0:3", (15, 8))])  # FAULT half: a walk like any other
            self.assertEqual(walks, [] if known_first else ["PETALBURG_CITY_GYM"])
            self.assertEqual(stopped, [] if known_first else [False, True])

    # ---- the nearest place, and a town's own centre
    def test_the_nearest_place_to_heal_and_to_shop(self):
        world = petalburg_world()
        mgr = manager("Story")
        self.assertEqual(mgr.heal_place(world)[0], "OLDALE_TOWN_POKEMON_CENTER_1F")  # the only one known
        mgr.memory.landmarks[("0:3", (20, 16))] = "pokemon_center"
        mgr.memory.landmarks[("0:3", (25, 12))] = "mart"
        # FAULT half (step 5's rule): the one it had been IN, two maps back, before the door it saw here
        self.assertEqual(mgr.heal_place(world)[:3], ("PETALBURG_CITY_POKEMON_CENTER_1F", "0:3", (20, 16)))
        self.assertEqual(mgr._mart_place(world, 12)[:3], ("PETALBURG_CITY_MART", "0:3", (25, 12)))  # noqa: SLF001
        world._last.key = "0:1"  # noqa: SLF001 - in OLDALE its own is the nearest
        self.assertEqual(mgr.heal_place(world)[:2], ("OLDALE_TOWN_POKEMON_CENTER_1F", None))
        self.assertEqual(mgr._mart_place(world, 12)[:2], ("OLDALE_TOWN_MART", None))  # noqa: SLF001

    def test_a_towns_own_centre_is_looked_for_before_walking_back(self):
        """Hurt in a TOWN whose POKéMON CENTER it has not seen, it looks for it there first (once a town); on a route, or a
        town looked round already, it heals at the nearest it knows."""
        def decide(mgr, world, const, number):
            observation = look(ch2_dad_marks(), party=[mon(9, hp=8, max_hp=20)], const=const, map_number=number)
            index, milestone = mgr.milestone(observation, visited_in(world))
            self.assertEqual(milestone.id, "ch2_dad")
            return mgr.next_goal(observation, world, milestone, index)

        mgr, world = manager("Story"), petalburg_world()
        goal = decide(mgr, world, "PETALBURG_CITY", 3)
        self.assertEqual((goal.kind, goal.via, goal.map), ("find_center", "0:3", "PETALBURG_CITY"))  # FAULT half: heal
        self.assertIn("before walking back to the POKéMON CENTER it knows (OLDALE_TOWN_POKEMON_CENTER_1F)", goal.reason)
        self.assertEqual((decide(mgr, world, "PETALBURG_CITY", 3).kind), "heal")  # once a town
        route = petalburg_world("ROUTE102")
        self.assertEqual(decide(manager("Story"), route, "ROUTE102", 2).kind, "heal")  # a route: no town to look in
        looked = manager("Story")
        looked.memory.explored.add("0:3")
        self.assertEqual(decide(looked, petalburg_world(), "PETALBURG_CITY", 3).kind, "heal")  # looked round: none here
        # (the graded sweep on 701-720, seed 706: it had looked round PETALBURG for 5,012 frames without seeing its centre
        # and walked back to OLDALE's) looked round, but with something left to see there: it still looks, once
        partly = manager("Story")
        partly.memory.explored.add("0:3")
        world = petalburg_world()
        world.maps["0:3"].tiles[(5, 5)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (5, 5))
        self.assertGreater(world.promise("0:3"), 0)
        self.assertEqual(decide(partly, world, "PETALBURG_CITY", 3).kind, "find_center")  # FAULT half: heal at OLDALE

    def test_a_walk_to_a_known_gym_door_keeps_the_gos_own_stops(self):
        """(the graded sweep on 701-720, seed 706: the gym's door known, the walk went straight from OLDALE's centre into the
        gym, past every stop a break owed would have made: chapter 2 ended at 28.7 %, under the floor) The way to the gym's
        town is a walk like any other: its stops hold (an item ball, a break owed); then in by the door."""
        from ai_player.brain.goals import BREAK_STOP, Goal, GoalRunner
        world = petalburg_world("OLDALE_TOWN")
        mgr = self.bored_manager()
        mgr.rng = _Draws(0.0)  # the arrival's boredom draw passes
        mgr.memory.looked = _Everything()  # no look-around draw is due: only boredom can stop the walk
        mgr.memory.landmarks[("0:3", (15, 8))] = "gym"
        arrive = look(ch2_dad_marks(), party=[mon(9)], const="ROUTE102", map_number=2)
        walks, insides = [], []

        def walk(target, why, budget, done):
            walks.append(target)
            world._last.key = "0:2"  # noqa: SLF001 - on ROUTE 102, on the way
            stopped = done(arrive)
            yield
            return "done: travel" if stopped else "budget: ran out"

        def inside(goal):
            insides.append(goal.tile)
            yield
            return "entered"

        runner = GoalRunner(types.SimpleNamespace(look=lambda: arrive), types.SimpleNamespace(world=world, battle_log=[]),
                            mgr, types.SimpleNamespace(purpose=""), lambda line: None)
        runner._walk_on_after_battles = walk  # noqa: SLF001
        runner._go_inside = inside  # noqa: SLF001
        index = mgr.story.index("ch2_dad")
        ok, outcome = drive(runner.pursue(Goal("go", "DAD", map="PETALBURG_CITY_GYM", key="go:PETALBURG_CITY_GYM"),
                                          mgr.story.milestones[index], index, lambda seen: index))
        self.assertEqual(walks, ["PETALBURG_CITY"])  # FAULT half: no walk of its own, straight in
        self.assertEqual(insides, [])  # stopped on the way: a break taken
        self.assertIn(BREAK_STOP, outcome)
        self.assertTrue(ok, outcome)

    def test_looking_for_a_towns_centre_ends_when_its_door_is_seen(self):
        from ai_player.brain.goals import CENTER_LOOK_FRAMES, Goal, GoalRunner
        world, mgr = petalburg_world(), manager("Story")
        arrive = look(ch2_dad_marks(), party=[mon(9, hp=8, max_hp=20)], const="PETALBURG_CITY", map_number=3)
        seen: list = []

        def run(intent, why):
            before = intent.done(arrive)
            mgr.memory.landmarks[("0:3", (20, 16))] = "pokemon_center"  # its red roof comes into view
            seen.append((intent.budget, before, intent.done(arrive)))
            yield
            return "done: looked round"

        nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: arrive), nav, mgr, types.SimpleNamespace(purpose=""),
                            lambda line: None)
        index = mgr.story.index("ch2_dad")
        ok, outcome = drive(runner.pursue(Goal("find_center", "hurt", map="PETALBURG_CITY", via="0:3",
                                               key="find_center:0:3"), mgr.story.milestones[index], index,
                                          lambda observation: index))
        self.assertEqual(seen, [(CENTER_LOOK_FRAMES, False, True)])  # FAULT half: the look goes on past the door
        self.assertTrue(ok, outcome)
        self.assertIn("its door seen on PETALBURG_CITY", outcome)

    # ---- BOREDOM (build step 5.2: the step-5.1 review's finding 2 replaced the 5.1 BALANCE, a quota on nearly the graders'
    # own quantity whose shortfall skipped the dice)
    def bored_manager(self, personality: str = "Story", since: int | None = None, **kwargs) -> GoalManager:
        """A goal manager `since` frames past its last productive curiosity at the tests' look frame (1000); by default
        fully bored (its personality's `bored_frames`)."""
        mgr = manager(personality, quiet=False, train_off=True, **kwargs)
        mgr.memory.curious_since = 1000 - (ERRANDS[personality].bored_frames if since is None else since)
        return mgr

    def test_boredom_raises_the_odds_smoothly_and_capped(self):
        """The odds of a curiosity draw: the personality's own at first, rising LINEARLY with the frames since its last
        productive curiosity to `CURIOUS_ODDS_CAP` at `Errands.bored_frames`, never above it, never below the base."""
        from ai_player.brain.goals import CURIOUS_ODDS_CAP
        base = ERRANDS["Story"].look_around
        bored = ERRANDS["Story"].bored_frames
        self.assertEqual(self.bored_manager(since=0).curious_odds(base, 1000)[0], base)
        half = self.bored_manager(since=bored // 2).curious_odds(base, 1000)[0]
        self.assertAlmostEqual(half, base + (CURIOUS_ODDS_CAP - base) / 2, places=3)  # FAULT half: a step, not smooth
        self.assertAlmostEqual(self.bored_manager().curious_odds(base, 1000)[0], CURIOUS_ODDS_CAP)
        self.assertAlmostEqual(self.bored_manager(since=10 * bored).curious_odds(base, 1000)[0], CURIOUS_ODDS_CAP)
        self.assertEqual(self.bored_manager().curious_odds(0.95, 1000)[0], 0.95)  # a base above the cap is kept
        self.assertLess(CURIOUS_ODDS_CAP, 1.0)  # never certain: the dice are thrown
        self.assertLess(ERRANDS["Catcher"].bored_frames, ERRANDS["Trainer"].bored_frames)
        self.assertLess(ERRANDS["Trainer"].bored_frames, ERRANDS["Story"].bored_frames)
        self.assertIn("raised to", self.bored_manager().curious_odds(base, 1000)[1])
        self.assertFalse(manager("Story", errands_off=True).curious_ok())  # the beeline control: no curiosity

    def test_only_productive_curiosity_resets_the_boredom_clock(self):
        """`after_goal`: a PRODUCTIVE curiosity goal resets the clock; one that brought nothing does not (5.1 counted every
        curiosity frame, CH1M's 6,000 frames of looking round OLDALE for one tile among them); a story or need goal ends a
        row of curiosity; a curiosity goal the story moved on in is the story's."""
        from ai_player.brain.goals import Goal
        mgr = self.bored_manager(since=5000)
        mgr.after_goal(Goal("chat", "x"), {"productive": False, "frames": 300}, 2000, "ch1_rival_route103")
        self.assertEqual((mgr.memory.curious_since, mgr.memory.curious_row), (1000 - 5000, 1))  # FAULT half: reset
        self.assertEqual(mgr.memory.idle, {"goals": 1, "frames": 300})
        mgr.after_goal(Goal("chat", "x"), {"productive": True, "frames": 300}, 2500, "ch1_rival_route103")
        self.assertEqual((mgr.memory.curious_since, mgr.memory.curious_row), (2500, 2))
        mgr.after_goal(Goal("go", "x"), {"productive": False}, 3000, "ch1_rival_route103")
        self.assertEqual(mgr.memory.curious_row, 0)
        mgr.after_goal(Goal("pick_up", "x"), {"productive": True}, 3500, "ch1_rival_house", story_moved=True)
        self.assertEqual((mgr.memory.curious_row, mgr.memory.curious_since), (0, 2500))  # the rival's POKé BALL: the story's

    def test_a_save_neither_ends_nor_joins_a_curiosity_row(self):
        """(R1 + R2 follow-up, spec D6: the verification's V2-6; T4: a save is "neither an errand nor the story's step")
        FAULT (mutant V6a; the old code): curiosity, curiosity, SAVE leaves the row at 2, so the next goal may not be one of
        curiosity (`curious_ok()` False); the old code reset it to 0 (True), letting C C save C C through `CURIOUS_ROW_MAX`.
        CONTROL: curiosity, curiosity, a story goal resets the row to 0 (unchanged); a save after it leaves 0."""
        from ai_player.brain.goals import CURIOUS_ROW_MAX, Goal
        self.assertEqual(CURIOUS_ROW_MAX, 2)  # the case below is built on a row of two
        mgr = self.bored_manager(since=5000)
        mgr.after_goal(Goal("chat", "x"), {"productive": False, "frames": 300}, 2000, "ch1_rival_route103")
        mgr.after_goal(Goal("explore", "x"), {"productive": False, "frames": 300}, 2500, "ch1_rival_route103")
        self.assertEqual((mgr.memory.curious_row, mgr.curious_ok()), (2, False))
        self.assertIsNone(mgr.after_goal(Goal("save", "a heal at a POKéMON CENTER"), {"frames": 300}, 3000,
                                         "ch1_rival_route103"))
        self.assertEqual((mgr.memory.curious_row, mgr.curious_ok()), (2, False))  # FAULT half: (0, True)
        # CONTROL: a story goal ends the row; a save after it leaves it ended
        mgr = self.bored_manager(since=5000)
        mgr.after_goal(Goal("chat", "x"), {"productive": False, "frames": 300}, 2000, "ch1_rival_route103")
        mgr.after_goal(Goal("explore", "x"), {"productive": False, "frames": 300}, 2500, "ch1_rival_route103")
        mgr.after_goal(Goal("go", "x"), {"productive": False}, 3000, "ch1_rival_route103")
        self.assertEqual((mgr.memory.curious_row, mgr.curious_ok()), (0, True))
        mgr.after_goal(Goal("save", "a heal at a POKéMON CENTER"), {"frames": 300}, 3500, "ch1_rival_route103")
        self.assertEqual(mgr.memory.curious_row, 0)

    def oldale(self, mgr: GoalManager, draw: float = 0.99, frontier: bool = True, people=()) -> Goal:
        mgr.rng = _Draws(draw)
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F",
                           current="OLDALE_TOWN", heard={"Oh, MAY went out to ROUTE 103 just a little while ago."})
        if frontier:  # a patch of OLDALE seen round the player at (10, 10): its border lies beside unseen tiles
            oldale = world.maps["0:3"]
            for x in range(6, 15):
                for y in range(6, 15):
                    oldale.tiles[(x, y)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (10, 10))
            oldale.people_now = frozenset(people)
        mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
        observation = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
        index, milestone = mgr.milestone(observation, visited_in(world))
        return mgr.next_goal(observation, world, milestone, index)

    def test_boredom_never_skips_the_dice(self):
        """A draw at 0.99 is over the cap: however bored, the look round is NOT chosen (5.1's owed break passed it without
        the dice); a draw at 0.85 passes for a bored person and not for one who has just been curious."""
        self.assertNotEqual(self.oldale(self.bored_manager(), 0.99).kind, "explore")  # FAULT half: the quota's bypass
        goal = self.oldale(self.bored_manager(), 0.85)
        self.assertEqual(goal.kind, "explore")
        self.assertIn("a new place, OLDALE_TOWN", goal.reason)
        self.assertIn("raised to 0.90", goal.reason)
        self.assertNotEqual(self.oldale(self.bored_manager(since=0), 0.85).kind, "explore")  # its own 0.55

    def test_some_more_only_where_something_is_left_to_walk_to(self):
        """(the review's finding 1: CH2M looked round PETALBURG twice, 8,400 frames, tiles 8025 -> 8026 -> 8026) "Some
        more" by boredom's dice, at most AGAIN_MAX a map and milestone, and only where a frontier is left that it can WALK
        to: not on a map seen all of, not with someone standing in every way, not on a map a look round EXHAUSTED."""
        from ai_player.brain.goals import AGAIN_MAX
        mgr = self.bored_manager()
        mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()  # this map's draws were made
        kinds = [self.oldale(mgr, 0.0) for _ in range(AGAIN_MAX + 1)]
        self.assertEqual([g.kind for g in kinds], ["explore"] * AGAIN_MAX + ["go"])  # FAULT: none, or no bound
        self.assertIn("some more", kinds[0].reason)
        self.assertNotIn("a new place", kinds[0].reason)  # (`live_step5` "a new place is new" reads new places only)
        self.assertEqual(kinds[0].via, "0:3")
        for case, mgr, frontier, people in (
                ("seen all of", self.bored_manager(), False, ()),
                ("nobody lets it through", self.bored_manager(), True, ((9, 10), (11, 10), (10, 9), (10, 11))),
                ("not bored", self.bored_manager(since=0), True, ())):
            mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()
            self.assertEqual(self.oldale(mgr, 0.0, frontier, people).kind, "go", case)  # FAULT halves: loafing there
        exhausted = self.bored_manager()
        exhausted.memory.looked, exhausted.memory.detoured = _Everything(), _Everything()
        exhausted.memory.exhausted["0:3|ch1_rival_route103"] = "a look round there brought nothing new"
        self.assertEqual(self.oldale(exhausted, 0.0).kind, "go")

    def test_at_most_two_curiosity_goals_in_a_row(self):
        """(the review's finding 2: CH1M ran six curiosity goals in a row) After CURIOUS_ROW_MAX in a row, the story or a
        need comes first: here the look round a draw at 0.0 would choose waits, its draw not made."""
        from ai_player.brain.goals import CURIOUS_ROW_MAX
        mgr = self.bored_manager()
        mgr.memory.curious_row = CURIOUS_ROW_MAX
        goal = self.oldale(mgr, 0.0)
        self.assertEqual(goal.kind, "go")  # FAULT half: a third curiosity goal
        self.assertNotIn("0:3", mgr.memory.looked)  # the draw waits for a later decision there
        mgr.memory.curious_row = CURIOUS_ROW_MAX - 1
        self.assertEqual(self.oldale(mgr, 0.0).kind, "explore")

    def test_a_walk_stops_where_a_bored_break_can_be_taken(self):
        """A `go` that arrives on ANOTHER outdoor map makes one boredom draw there a map and milestone; when it passes the
        walk stops (the next decision may take a break there); not when it fails, nor on the map the walk began on."""
        from ai_player.brain.goals import BREAK_STOP, Goal, GoalRunner
        for since, began_there, want in ((None, False, True), (0, False, False), (None, True, False)):
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN" if began_there else
                               "ROUTE101")
            arrive = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN", map_number=3)
            stopped = []

            def run(intent, why, world=world, arrive=arrive, stopped=stopped):
                world._last.key = "0:3"  # noqa: SLF001
                stopped.append(intent.done(arrive))
                yield
                return "done: travel" if stopped[-1] else "budget: ran out"

            mgr = self.bored_manager(since=since)
            mgr.rng = _Draws(0.5)  # passes 0.9 x boredom when bored, fails at boredom 0
            mgr.memory.looked = _Everything()  # its look-around draw was made: only boredom can stop the walk
            nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
            runner = GoalRunner(types.SimpleNamespace(look=lambda arrive=arrive: arrive), nav, mgr,
                                types.SimpleNamespace(purpose=""), lambda line: None)
            runner._travel = lambda target, why, budget, done, run=run: run(types.SimpleNamespace(done=done), why)  # noqa: SLF001
            ok, outcome = drive(runner.pursue(Goal("go", "to ROUTE 103", map="ROUTE103"), mgr.story.milestones[8], 8,
                                              lambda seen: 8))
            self.assertEqual(stopped, [want], (since, began_there))
            self.assertEqual(BREAK_STOP in outcome, want, outcome)

    def test_a_walk_may_stop_for_a_break_after_a_battle(self):
        """(step52dev3: the Trainer's chapter 2, seed 1017, walked 25,408 frames on ROUTE 102 and met 17 battles with no
        decision between) a battle won on a `go` walk is a moment for one boredom draw, once the player is free on an
        outdoor map: bored, the walk stops for the next decision; not bored, it walks on; one draw per battle."""
        from ai_player.brain.goals import BREAK_STOP, CURIOUS_ROW_MAX, Goal, GoalRunner
        for since, battles, want, row in ((None, 1, [False, True], 0), (0, 1, [False, False], 0),
                                          (None, 0, [False, False], 0), (None, 1, [False, False], CURIOUS_ROW_MAX)):
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101")
            free = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="ROUTE101", map_number=2)
            stopped = []
            draws = _Draws(0.5)  # passes 0.9 x boredom when bored, fails at boredom 0

            def run(intent, why, free=free, stopped=stopped, battles=battles):
                stopped.append(intent.done(free))  # no battle yet: walks on
                nav.battle_log.extend([(900, "wild", "won")] * battles)
                stopped.append(intent.done(free))
                yield
                return "done: travel" if stopped[-1] else "budget: ran out"

            mgr = self.bored_manager(since=since)
            mgr.rng = draws
            mgr.memory.curious_row = row  # at the row cap: no break (FAULT half: the cap not asked)
            mgr.memory.looked = _Everything()
            mgr.memory.break_stops = _Everything()  # its arrival draws were made: only a battle can stop the walk
            nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
            runner = GoalRunner(types.SimpleNamespace(look=lambda free=free: free), nav, mgr,
                                types.SimpleNamespace(purpose=""), lambda line: None)
            runner._travel = lambda target, why, budget, done, run=run: run(types.SimpleNamespace(done=done), why)  # noqa: SLF001
            ok, outcome = drive(runner.pursue(Goal("go", "to ROUTE 103", map="ROUTE103"), mgr.story.milestones[8], 8,
                                              lambda seen: 8))
            self.assertEqual(stopped, want, (since, battles, row))  # FAULT half: a battle never stops the walk
            self.assertEqual(f"{BREAK_STOP}: after a battle" in outcome, want[-1], outcome)
        # one draw per battle: a draw that failed is not thrown again at the next look (FAULT half: thrown every look)
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101")
        free = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="ROUTE101", map_number=2)
        stream = [0.95, 0.1, 0.1]
        stopped = []

        def again(intent, why):
            nav.battle_log.append((900, "wild", "won"))
            stopped.extend([intent.done(free), intent.done(free)])
            yield
            return "budget: ran out"

        mgr = self.bored_manager()
        mgr.rng = types.SimpleNamespace(random=lambda: stream.pop(0))
        mgr.memory.looked = _Everything()
        mgr.memory.break_stops = _Everything()
        nav = types.SimpleNamespace(world=world, run=again, battle_log=[])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: free), nav, mgr, types.SimpleNamespace(purpose=""),
                            lambda line: None)
        runner._travel = lambda target, why, budget, done: again(types.SimpleNamespace(done=done), why)  # noqa: SLF001
        drive(runner.pursue(Goal("go", "to ROUTE 103", map="ROUTE103"), mgr.story.milestones[8], 8, lambda seen: 8))
        self.assertEqual(stopped, [False, False])

    # ---- the verifier's V3: the walk walks on TWICE
    def test_a_walk_walks_on_twice_when_its_battles_ate_it_twice(self):
        """(the verifier's V3, `range(1)` for `range(GO_BATTLE_EXTENSIONS)`, caught by no test: the test above exercises one
        extension, yet the live CH2T walked on twice, 9,000 then 8,581 frames, before it arrived)"""
        from ai_player.brain.goals import GO_BATTLE_EXTENSIONS, GO_FRAMES, Goal, GoalRunner
        self.assertEqual(GO_BATTLE_EXTENSIONS, 2)
        mgr = manager("Story")
        hands = types.SimpleNamespace(look=lambda: look(party=[mon(9)]), watchers=[])
        calls = []

        def travel(target, why, budget, done):
            calls.append(budget)
            if len(calls) <= 2:  # the first walk and the first walk-on: each met a battle of 3,000 frames and ran out
                base = look(party=[mon(9)])
                fight = replace(base, screen=replace(base.screen, in_battle=True, game_state="BATTLE"))
                for watcher in list(hands.watchers):
                    watcher(replace(fight, frame=100 * len(calls)))
                    watcher(replace(base, frame=100 * len(calls) + 3000))
                yield
                return "budget: 9000 frames ran out"
            yield
            return "done: travel to PETALBURG_CITY"

        runner = GoalRunner(hands, types.SimpleNamespace(world=world_with("ROUTE102", current="ROUTE102"), battle_log=[]),
                            mgr, types.SimpleNamespace(purpose=""), lambda line: None)
        runner._travel = travel  # noqa: SLF001
        ok, outcome = drive(runner.pursue(Goal("go", "to PETALBURG", map="PETALBURG_CITY", key="go:PETALBURG_CITY"),
                                          mgr.story.milestones[mgr.story.index("ch2_petalburg")],
                                          mgr.story.index("ch2_petalburg"), lambda seen: mgr.story.index("ch2_petalburg")))
        self.assertEqual(calls, [GO_FRAMES, 3000, 3000])  # FAULT half (V3): it gives up after one walk-on
        self.assertTrue(ok, outcome)

    # ---- a level gained by one Pokemon
    def test_a_level_is_gained_by_one_pokemon_not_by_the_partys_sum(self):
        """(the verifier: the party read Zigzagoon:L7 + Poochyena:L3 during WALLY's tutorial, then Treecko:L12 + Poochyena:L3
        again, and the log said "a level gained (10 -> 15)", resetting the patience) A level is gained by one Pokemon, by
        its PID, above the highest it was seen at."""
        world = world_with("PETALBURG_CITY", current="PETALBURG_CITY")
        runner = types.SimpleNamespace(heals=[], picked=[], shopping=[])
        report, seen = {"won_training": 0}, {}
        treecko, poochyena = mon(12, pid=0xA, species="Treecko"), mon(3, pid=0xB, species="Poochyena")
        lent = mon(7, pid=0xC, species="Zigzagoon")

        def progress(*party):
            return HandsBrain._progress(look(party=list(party)), world, runner, report, seen)

        self.assertEqual(progress(treecko, poochyena), [])  # the first look: the snapshot
        self.assertEqual(progress(lent, poochyena), [])
        self.assertEqual(progress(treecko, poochyena), [])  # FAULT half (the party's sum): "a level gained (10 -> 15)"
        self.assertTrue(any("a level gained" in m for m in progress(mon(13, pid=0xA, species="Treecko"), poochyena)))

    # ---- which personality judged the run trained
    def test_whose_rule_judged_the_run_trained_is_logged(self):
        mgr = manager("Trainer")
        mgr.state.active = "Story"  # drifted into the Story personality
        mgr.memory.fight_prep["ch1_rival_route103"] = {"steps": ERRANDS["Story"].train_min_steps, "sessions": 1, "wild": 3,
                                                        "won": 3, "rests": 0, "ready": False}
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", heard={"went out to ROUTE 103"})
        observation = look(ch1_through("ch1_rival_route103"), party=[mon(9)])
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertNotEqual(mgr.next_goal(observation, world, milestone, index).kind, "train")
        prep = mgr.memory.fight_prep["ch1_rival_route103"]
        self.assertEqual((prep["ready"], prep["judged_by"], prep["min_steps"]),
                         (True, "Story", ERRANDS["Story"].train_min_steps))  # FAULT half: not logged

    def test_the_training_bound_is_the_judges_own(self):
        from ai_player.gates.rate_step5 import train_steps_min_run
        row = {"personality": "Trainer", "rival_actives": ["Story", "Trainer"], "rival_judge": "Trainer"}
        self.assertEqual(train_steps_min_run(row), 135)  # FAULT half: the lowest it played as, 72
        self.assertEqual(train_steps_min_run({**row, "rival_judge": "Story"}), 72)
        self.assertEqual(train_steps_min_run({**row, "rival_judge": None}), 72)  # a log without it: the older reading

    # ---- the graders' honest errand share
    def test_the_grader_ends_a_goal_at_its_end_record(self):
        """A goal's frames end at its END record: the WALLY scene after a DROPPED chat (CH2T: 11,019 frames) is no goal's;
        a curiosity goal the story moved on in counts as the story's in the ERRAND share too."""
        from ai_player.gates.rate_step5 import intent_mix
        records = [{"decision": "goal", "action": "go", "frame": 0},
                   {"decision": "goal_end", "action": "go", "frame": 900},
                   {"decision": "goal", "action": "chat", "frame": 1000},
                   {"decision": "goal_end", "action": "chat", "frame": 1030, "reason": "dropped: a scene began"},
                   {"decision": "milestone", "action": "ch2_wally", "frame": 5000},  # in the scene, after the chat ended
                   {"decision": "goal", "action": "explore", "frame": 12000},
                   {"decision": "goal_end", "action": "explore", "frame": 15000},
                   {"decision": "goal", "action": "pick_up", "frame": 15000},
                   {"decision": "goal_end", "action": "pick_up", "frame": 15500},
                   # the loop's NEXT pass writes the milestone the goal passed, with no frame passing (the rival's scene)
                   {"decision": "milestone", "action": "ch1_rival_house", "frame": 15500},
                   {"decision": "watch", "frame": 16000}]
        mix = intent_mix(records)
        self.assertEqual(mix["frames"], {"chat": 30, "explore": 3000, "go": 900, "pick_up": 500})  # FAULT: chat 11,000
        self.assertEqual(mix["between_goals"], 100 + 10970 + 500)
        self.assertEqual(mix["story_own"], [(15000, "pick_up", 500)])  # the chat is not the story's: it ended first
        self.assertEqual(mix["errand_frames"], 3030)  # FAULT half: the pick_up the story moved on in, 3530
        self.assertAlmostEqual(mix["errand_share"], round(3030 / 4430, 4))
        old = [r for r in records if r["decision"] != "goal_end"]  # a log without end records: to the next goal
        self.assertEqual(intent_mix(old)["frames"]["chat"], 11000)
        # (found by the development sweep step51wdev1: the beeline control's rival POKé BALL counted as free curiosity, its
        # milestone written after the goal's end record) a milestone within END_SLACK of the end is the goal's; later, not
        from ai_player.gates.rate_step5 import END_SLACK
        late = [dict(r, frame=15500 + END_SLACK + 1) if r["decision"] == "milestone" and r["frame"] == 15500 else r
                for r in records]
        self.assertEqual(intent_mix(late)["story_own"], [])

    def test_a_save_goal_is_out_of_the_errand_share(self):
        """(R1 + R2, build spec section 7 T4; the fix round's review R-4) A SAVE goal is the player's bookkeeping, neither an
        errand nor the story's step: its frames leave the intent mix's TOTAL and are reported apart (`save_frames`,
        `save_goals`). FAULT half (the save left in the total): the errand share would fall from 0.5 to 0.3333 with no
        change in the errands. CONTROL: the same goals with no save give the same share, and `save_frames` 0."""
        from ai_player.gates.rate_step5 import SAVE_KIND, intent_mix

        base = [{"decision": "goal", "action": "go", "frame": 0}, {"decision": "goal_end", "action": "go", "frame": 1000},
                {"decision": "goal", "action": "chat", "frame": 1000},
                {"decision": "goal_end", "action": "chat", "frame": 2000}]
        plain = intent_mix(base + [{"decision": "watch", "frame": 2000}])
        saved = intent_mix(base + [{"decision": "goal", "action": SAVE_KIND, "frame": 2000},
                                   {"decision": "goal_end", "action": SAVE_KIND, "frame": 3000},
                                   {"decision": "watch", "frame": 3400}])
        self.assertEqual(SAVE_KIND, "save")
        self.assertEqual((plain["errand_share"], plain["save_frames"], plain["save_goals"]), (0.5, 0, 0))
        self.assertEqual((saved["errand_share"], saved["total_frames"], saved["goals"]), (0.5, 2000, 2))
        self.assertEqual((saved["save_frames"], saved["save_goals"]), (1000, 1))
        self.assertNotIn(SAVE_KIND, saved["frames"])
        self.assertEqual(saved["between_goals"], 400)  # what the loop played after the save is still between goals

    # ---- found by the round's development sweep (step51wdev1, seeds 31-39)
    def test_a_door_seen_across_a_maps_edge_is_not_that_maps(self):
        """(seeds 33, 36, 37, 38: OLDALE's POKéMON CENTER door, seen from ROUTE 102 across its right edge, was remembered on
        ROUTE 102 at (56, 16); as the NEAREST place it was a door nobody could reach, and a party in danger tried it again
        and again until the patience ran out: two runs stopped "no progress for 120,000 frames") A door past an edge the AI
        has seen crossed is not on that map."""
        world = petalburg_world("ROUTE102")
        world.maps["0:2"].edges["right"] = 50  # crossed from OLDALE: x 50 and on is past it
        mgr = manager("Story")
        mgr.memory.landmarks[("0:2", (56, 16))] = "pokemon_center"
        self.assertEqual(mgr.heal_place(world)[:2], ("OLDALE_TOWN_POKEMON_CENTER_1F", None))  # FAULT half: (56, 16)

    def test_a_door_that_cannot_be_walked_into_is_forgotten(self):
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import Goal, GoalRunner
        world, mgr = petalburg_world("ROUTE102"), manager("Story")
        mgr.memory.landmarks[("0:2", (56, 16))] = "pokemon_center"
        told: list[str] = []

        def no_door(hands, nav, door, why):
            yield
            return f"the tile below the door at {door} is not a known walkable tile"

        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(9)])),
                            types.SimpleNamespace(world=world, battle_log=[]), mgr, types.SimpleNamespace(purpose=""),
                            told.append)
        with mock.patch.object(goals_module, "enter_door", no_door):
            outcome = drive(runner._go_inside(Goal("heal", "hurt", map="ROUTE102_POKEMON_CENTER_1F", via="0:2",  # noqa: SLF001
                                                   tile=(56, 16))))
        self.assertIn("not a known walkable tile", outcome)
        self.assertNotIn(("0:2", (56, 16)), mgr.memory.landmarks)  # FAULT half: it stays the nearest place, for ever
        self.assertTrue(any("forgotten" in line for line in told), told)

    def test_a_heal_in_danger_is_tried_again_only_a_few_times(self):
        """In danger a heal put aside is tried again at once (step 5's rule), but at most DANGER_RETRIES times in a row: a
        place that keeps failing at once would otherwise be chosen until the patience ran out."""
        from ai_player.brain.goals import DANGER_RETRIES
        center = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="ROUTE101", heard={"ROUTE 103"},
                            center_from="OLDALE_TOWN")
        mgr = manager("Story")
        mgr.memory.cooldown["heal:OLDALE_TOWN_POKEMON_CENTER_1F"] = 10 ** 6  # put aside after failing
        observation = look(ch1_through("ch1_rival_route103"), party=[mon(5, hp=5)])  # 25 %: in danger
        index, milestone = mgr.milestone(observation, visited_in(center))
        kinds = [mgr.next_goal(observation, center, milestone, index).kind for _ in range(DANGER_RETRIES + 1)]
        self.assertEqual(kinds[:DANGER_RETRIES], ["heal"] * DANGER_RETRIES)
        self.assertNotEqual(kinds[-1], "heal")  # FAULT half: heal again, for ever

    def test_the_storys_own_person_is_no_chat(self):
        """(seeds 37, 39: "chat: someone stands near at (4, 107)": DAD, whom the story's own step talks to, chosen as a chat,
        a story-owned goal under an errand's name) The person the story's step names is talked to by the story's goal."""
        mgr = manager("Story")
        mgr.rng = _Draws(0.0)  # every draw passes: a chat with anyone near
        world = world_with("PETALBURG_CITY", "PETALBURG_CITY_GYM", current="PETALBURG_CITY_GYM",
                           heard={"INTERVIEWER: …We brought you this report from in front of PETALBURG GYM."})
        norman = person(11, 10, gfx=mgr.story.looks["norman"].gfx[0], local_id=1)
        observation = look(ch2_dad_marks(), party=[mon(12)], const="PETALBURG_CITY_GYM", map_number=2, objects=[norman])
        index, milestone = mgr.milestone(observation, visited_in(world))
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.target.local_id), ("talk", 1))  # FAULT half: a chat with DAD
        stranger = person(12, 10, gfx=1, local_id=2)
        other = mgr.next_goal(replace(observation, view=replace(observation.view, objects=(norman, stranger))), world,
                              milestone, index)
        self.assertEqual((other.kind, other.target.local_id), ("chat", 2))  # anyone else is still a chat

    def test_an_aside_lasts_the_breather_not_longer(self):
        """(seed 32: three looks round put aside for the walk to PETALBURG, the third begun 617 frames before the breather's
        end, ran 6,444 frames among the grass's battles: a streak of 11,827, over ASIDE_STREAK_MAX) A look round meanwhile
        is given the frames LEFT of the breather; with under ASIDE_LOOK_MIN left the story goal is tried again at once."""
        from ai_player.brain.goals import ASIDE, ASIDE_LOOK_MIN, FAIL_LIMIT, STORY_ASIDE_FRAMES
        mgr = manager("Catcher")
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN",
                           heard={"Oh, MAY went out to ROUTE 103 just a little while ago."})
        mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
        seen = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
        index, milestone = mgr.milestone(seen, visited_in(world))
        mgr.train_off = True
        from ai_player.brain.goals import Goal
        for _ in range(FAIL_LIMIT):
            mgr.outcome(Goal("go", "x", key="go:ROUTE103"), False)
        first = mgr.next_goal(replace(seen, frame=10_000), world, milestone, index)
        self.assertEqual(first.key, f"{ASIDE}go:ROUTE103")
        later = mgr.next_goal(replace(seen, frame=10_000 + STORY_ASIDE_FRAMES - 2000), world, milestone, index)
        self.assertEqual((later.key, later.steps), (f"{ASIDE}go:ROUTE103", 2000))  # FAULT half: a full look round
        last = mgr.next_goal(replace(seen, frame=10_000 + STORY_ASIDE_FRAMES - ASIDE_LOOK_MIN + 1), world, milestone, index)
        self.assertEqual(last.key, "go:ROUTE103")  # too little of the breather left for a look round: the story again

    def test_a_scene_between_goals_is_the_storys_time_in_the_balance(self):
        """What the loop played BETWEEN two goals (a scene) is the story's time in the AI's own balance (`spent`): a person
        who has just watched WALLY's tutorial has had plenty of story."""
        loop = PlayLoopTests()
        free = loop.free_screen()
        scene = replace(free, screen=replace(free.screen, text_box_open=True, waits_for_button=True, script_running=True,
                                             text="PROF. BIRCH: So, Milo."))

        def screen(frames: int) -> Observation:
            return scene if 2 <= frames < 5003 else free

        reason, hands, pursued, screens, report = loop.run_loop(screen, budget=20_000)
        self.assertTrue(screens)
        goals = sum(goal["frames"] for goal in report["goals"])
        counted = report["spent"]["story"] + report["spent"]["errand"]
        self.assertGreaterEqual(counted - goals, loop.PER_SCREEN)  # FAULT half: only the goals' own frames are counted

    def test_the_nurse_and_the_clerk_give_way_to_a_waiting_screen(self):
        """(seed 42: the poison's "TREECKO fainted…" came up as the AI reached the nurse, and `nurse_heal`'s talk stood 1,203
        frames waiting for the player to be free) With `give_way` (the story's skills) a screen that waits for a press is
        handed back at once (`GAVE_WAY`); the step-2 default still waits it out."""
        from ai_player.hands.menus import GAVE_WAY, MART_CLERK_GFX, NURSE_GFX, mart_buy, nurse_heal
        for gfx, skill in ((NURSE_GFX, lambda hands, **kw: nurse_heal(hands, "heal", **kw)),
                           (MART_CLERK_GFX, lambda hands, **kw: mart_buy(hands, "POKé BALL", 5, "shop", **kw))):
            waiting = screen_look(waits=True, text="TREECKO fainted…", party=[mon(9, hp=0)],
                                  objects=[person(10, 9, gfx=gfx, local_id=1)])
            hands = script_hands(lambda frames, waiting=waiting: replace(waiting, frame=frames))
            self.assertEqual(drive(skill(hands, give_way=True), 200), GAVE_WAY)
            self.assertLess(hands.pad.frames, 50)  # at once: FAULT half, the 1,200-frame wait
            hands = script_hands(lambda frames, waiting=waiting: replace(waiting, frame=frames))
            self.assertNotEqual(drive(skill(hands), 20_000), GAVE_WAY)  # the step-2 default waits it out
            self.assertGreaterEqual(hands.pad.frames, 1000)

    def test_its_first_poke_balls_are_tried(self):
        """(seed 31: a Story player went through chapter 2 with its first five POKé BALLS and caught nothing) A POKéDEX that
        holds only its first Pokemon, balls in hand and grass not walked: the catch draw passes; with two owned it is the
        taste's draw again."""
        def route102(owned: int) -> Goal:
            mgr = manager("Story")
            mgr.rng = _Draws(0.99)
            world = world_with("OLDALE_TOWN", "ROUTE102", current="ROUTE102", grass=True)
            observation = look({**ch1_through("ch2_oldale"), "VISITED_OLDALE_TOWN": 1}, party=[mon(9)], balls=5,
                               const="ROUTE102", map_number=2)
            observation = replace(observation, progress=replace(observation.progress, dex_owned=owned))
            index, milestone = mgr.milestone(observation, visited_in(world))
            return mgr.next_goal(observation, world, milestone, index)

        from ai_player.brain.goals import Goal  # noqa: F401 - the annotation's name
        goal = route102(1)
        self.assertEqual(goal.kind, "catch")  # FAULT half: the Story's 0.3 draw said no
        self.assertIn("its first POKé BALLS", goal.reason)
        self.assertNotEqual(route102(2).kind, "catch")

    def test_the_chapter2_checks(self):
        """The sweep's chapter 2 (`rate_step5.chapter2_verdicts`): the floor in EVERY run, the beeline under it."""
        from ai_player.gates.rate_step5 import BOUNDS, chapter2_verdicts

        def row(seed, share, free=0.1, wally=True, plan="CH2"):
            return {"plan": plan, "seed": seed, "personality": "Story", "wally": wally, "frames": 90000,
                    "reason": "play: done", "mix": {"errand_share": share, "free_share": free}, "old_places": [],
                    "place_draws": 2, "losses_game": 0, "time_wally": {"outside_nb": 50000 if plan == "CH2" else 40000},
                    # (build step 5.3, the re-sourcing fix round, item 5) the GAME's frames to WALLY less its battles,
                    # which R5.CH2_NOBATTLE now reads (`time_wally`, the AI's own digests, is no longer read)
                    "wally_game": {"frame": 60000, "no_battle": 50000 if plan == "CH2" else 40000, "at_end": False}}

        def verdict(rows, check_id):
            # (build step 5.3, A1-4) by its check ID; the check's OWN outcome (a REPORTED share's: its old bound's)
            return check_by_id(chapter2_verdicts(rows), check_id).status == "PASS"

        good = {"CH2": [row(1, 0.4), row(2, 0.35)], "CH2_OFF": [row(1, 0.1, 0.0, plan="CH2_OFF"),
                                                                 row(2, 0.2, 0.0, plan="CH2_OFF")]}
        self.assertTrue(verdict(good, "R5.CH2_INTENT_MIX"))
        self.assertFalse(verdict({**good, "CH2": [row(1, 0.4), row(2, BOUNDS["MIX_MIN"] - 0.01)]}, "R5.CH2_INTENT_MIX"))
        self.assertTrue(verdict(good, "R5.CH2_OFF_UNDER"))
        self.assertFalse(verdict({**good, "CH2_OFF": [row(1, 0.5, 0.0, plan="CH2_OFF")] * 2}, "R5.CH2_OFF_UNDER"))
        self.assertTrue(verdict(good, "R5.CH2_NOBATTLE"))  # CONTROL: the game's frames, CH2 1.25 x CH2_OFF
        # (build step 5.3, the re-sourcing fix round, item 5: replaces nothing; the old line above held only the AI form's
        # PASS on `time_wally`) FAULT: the GAME says CH2 was no slower than the beeline, whatever the AI's own digests say
        beeline = {**good, "CH2": [{**r, "wally_game": dict(o["wally_game"])} for r, o in zip(good["CH2"], good["CH2_OFF"])]}
        self.assertFalse(verdict(beeline, "R5.CH2_NOBATTLE"))
        ai_only = {plan: [{**r, "wally_game": None} for r in rows] for plan, rows in good.items()}
        self.assertEqual(check_by_id(chapter2_verdicts(ai_only), "R5.CH2_NOBATTLE").status, "VACUOUS")  # no game read
        self.assertFalse(verdict({**good, "CH2": [row(1, 0.4, wally=False)] * 2}, "R5.CH2_WALLY"))

    def test_the_shares_of_frames_are_reported_not_graded(self):
        """(build step 5.2, P2: "grade YIELD and SPACING, not share of frames") the sweep's verdicts REPORT every check of a
        share of frames (`rate_step5.P2_REPORTED`), saying whether its old bound held; any other check stays graded."""
        from ai_player.gates import grader_checks, rate_step5
        # (build step 5.3, A1-4) the sub-verdicts are TYPED checks found by id: "reported" is a KIND, no longer a prefix
        made = [grader_checks.grade("R5.CH2_INTENT_MIX", False, "CH2: THE INTENT MIX, a FLOOR in EVERY chapter-2 run ...", 2),
                grader_checks.grade("R5.CH2_WALLY", False, "CH2: WALLY's tutorial ...", 2, 1),
                grader_checks.grade("R5.CH1_INTENT_MIX", True, "THE INTENT MIX (CH1): the share ...", 2),
                grader_checks.grade("R5.BEELINE_FAILS_FREE", False, "THE BEELINE FAILS THE CURIOSITY BOUND: ...", 2)]
        with mock.patch.object(rate_step5, "stop_verdicts", lambda rows, forced=True: []), \
                mock.patch.object(rate_step5, "step51_verdicts", lambda rows: made[2:]), \
                mock.patch.object(rate_step5, "chapter2_verdicts", lambda rows: made[:2]), \
                mock.patch.object(rate_step5, "step52_verdicts", lambda rows: []):
            results = rate_step5.verdicts({}, {})

        def by(check_id: str):
            return check_by_id(results, check_id)

        self.assertEqual(by("R5.CH2_INTENT_MIX")[0], True)  # FAULT half: graded, and the run FAILS
        self.assertEqual(by("R5.CH2_INTENT_MIX").kind, grader_checks.REPORTED)
        self.assertIn("the old bound did NOT hold", by("R5.CH2_INTENT_MIX")[1])
        self.assertIn("the old bound HELD", by("R5.CH1_INTENT_MIX")[1])
        self.assertEqual(by("R5.CH2_WALLY")[0], False)  # graded as before
        self.assertTrue(by("R5.BEELINE_FAILS_FREE")[0])
        self.assertEqual(grader_checks.verdict(results), "FAIL")  # WALLY's failure alone fails the sweep
        # P2_REPORTED is exactly the REPORTED checks that keep their 5.2 bound's verdict, all seven
        self.assertEqual(set(rate_step5.P2_REPORTED), {key for key, spec in grader_checks.CHECKS.items()
                                                        if spec.kind == grader_checks.REPORTED and spec.old_bound})
        self.assertEqual(len(rate_step5.P2_REPORTED), 7)


class WayTests(unittest.TestCase):
    """Going somewhere: a SCENE's map change is no way to walk; a map never seen is looked for out in the open; a house
    already seen is not walked back into on the way."""

    def littleroot(self, scene_link: bool = True) -> WorldMemory:
        world = world_with("ROUTE101", "LITTLEROOT_TOWN", "LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB", "OLDALE_TOWN",
                           current="OLDALE_TOWN")
        # keys: ROUTE101 0:1, LITTLEROOT 0:2, LAB 0:3, OLDALE 0:4
        world.connections.append({"source": "0:4", "target": "0:1", "direction": "down", "from": [10, 19],
                                  "arrival": [10, 0], "by": "ai", "frame": 1})
        world.connections.append({"source": "0:1", "target": "0:2", "direction": "down", "from": [10, 19],
                                  "arrival": [10, 0], "by": "ai", "frame": 2})
        world.warps["0:2|6,12"] = {"to": "0:3", "arrival": [6, 12], "uses": 0, "by": "inferred", "inferred": True}
        world.maps["0:2"].tiles[(6, 12)] = TileFact(True, False, False, False, None, True, True, 3, "ANIMATED_DOOR", 0, (6, 14))
        if scene_link:  # PROF. BIRCH's scene took the player from ROUTE 101 to the lab
            world.warps["0:1|7,14"] = {"to": "0:3", "arrival": [6, 5], "uses": 1, "by": "scene", "inferred": False}
            world.maps["0:1"].tiles[(7, 14)] = TileFact(False, False, True, True, None, False, False, 3, "TALL_GRASS", 0, (7, 14))
        return world

    def test_a_scenes_map_change_is_no_way_to_walk(self):
        from ai_player.brain.explore import route_to
        world = self.littleroot()
        route = route_to(world, "0:1", lambda memory, key: key == "0:3")
        self.assertEqual([kind for kind, _ in route], ["connection", "warp"])  # down to Littleroot, then the lab's door
        self.assertEqual(route[1][1]["tile"], [6, 12])
        world.warps["0:1|7,14"]["by"] = "ai"  # a "warp" made by the AI's own step but from a tile that is no exit (grass):
        route = route_to(world, "0:1", lambda memory, key: key == "0:3")  # still no way (seed 7's edge-crossing "warp")
        self.assertEqual([kind for kind, _ in route], ["connection", "warp"])
        world.maps["0:1"].tiles[(7, 14)] = TileFact(True, False, False, False, None, True, True, 3, "ANIMATED_DOOR", 0, (7, 15))
        # FAULT half: had the player walked through a DOOR there, it would be the way
        self.assertEqual([kind for kind, _ in route_to(world, "0:1", lambda memory, key: key == "0:3")], ["warp"])

    def test_a_door_a_scene_walked_the_player_through_is_a_way(self):
        """(the development sweep step5dev7, seed 3) MOM walks the player into the new house through its front door: a
        SCENE's map change, but from a DOOR, so it is the way home; until this round every scene link was refused, the AI
        knew no way home, and two walks home to heal ran out on ROUTE 101 before a whiteout at 2/26 HP."""
        from ai_player.brain.explore import route_to
        from ai_player.brain.goals import world_distance
        world = world_with("ROUTE101", "LITTLEROOT_TOWN", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", current="ROUTE101")
        world.connections.append({"source": "0:1", "target": "0:2", "direction": "down", "from": [10, 19],
                                  "arrival": [10, 0], "by": "ai", "frame": 2})
        world.warps["0:2|5,8"] = {"to": "0:3", "arrival": [8, 8], "uses": 1, "by": "scene", "inferred": False}
        home = lambda memory, key: key == "0:3"  # noqa: E731
        world.maps["0:2"].tiles[(5, 8)] = TileFact(True, False, False, False, None, True, True, 0, "ANIMATED_DOOR", 0, (3, 10))
        self.assertEqual([kind for kind, _ in route_to(world, "0:1", home)], ["connection", "warp"])
        self.assertEqual(world_distance(world, "0:3"), 2)
        # FAULT half: had the scene taken the player from where they stood (no door there), it would be no way
        world.maps["0:2"].tiles[(5, 8)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (5, 8))
        self.assertIsNone(route_to(world, "0:1", home))
        self.assertEqual(world_distance(world, "0:3"), 99)

    def test_the_doors_it_recognised_are_kept_with_the_world_memory(self):
        """(the chapter-2 development run of 2026-10-14 started from chapter 1's memory without them and went home to MOM
        to heal, past OLDALE's centre) A person remembers where the POKéMON CENTER was."""
        world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
        mgr = manager()
        mgr.memory.landmarks = world.landmarks
        tiles = [Tile(x=6, y=16, dx=-4, dy=6, metatile=mgr.story.looks["pokemon_center_door"].metatile[0], behavior=0x69,
                      behavior_name="ANIMATED_DOOR", collision=1, elevation=3, blocked=True, water=False, encounter=None,
                      tall_grass=False, ledge=None, door=True, warp=True, half_visible=False)]
        mgr.notice(look(const="OLDALE_TOWN", map_number=1, tiles=tiles))
        self.assertEqual(world.landmarks, {("0:1", (6, 16)): "pokemon_center"})
        again = WorldMemory.from_dict(world.to_dict())
        self.assertEqual(again.landmarks, world.landmarks)
        self.assertNotIn("landmarks", WorldMemory().to_dict())  # the earlier brains' snapshots are unchanged

    def test_a_map_never_seen_is_looked_for_out_in_the_open(self):
        from ai_player.brain.goals import lead_toward
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "LITTLEROOT_TOWN_MAYS_HOUSE_1F", current="LITTLEROOT_TOWN_MAYS_HOUSE_1F")
        world.maps["0:2"].tiles[(9, 0)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (9, 5))
        self.assertEqual(lead_toward(world, "ROUTE103"), "ROUTE101")  # routes first, where something is left to see
        self.assertIsNone(lead_toward(world, "LITTLEROOT_TOWN_MAYS_HOUSE_2F"))  # upstairs: found inside, by the stairs
        self.assertIsNone(lead_toward(world, "ROUTE101"))  # a map it knows: straight there

    def test_a_building_never_seen_is_looked_for_in_its_own_town(self):
        """(the chapter-2 development run c2b, 2026-10-14: told of the PETALBURG GYM while on ROUTE 102, it explored ROUTE
        102's grass for two budgets) A building is in the town its name says."""
        from ai_player.brain.goals import lead_toward
        world = world_with("PETALBURG_CITY", "ROUTE102", "OLDALE_TOWN_POKEMON_CENTER_1F", current="ROUTE102")
        self.assertEqual(lead_toward(world, "PETALBURG_CITY_GYM"), "PETALBURG_CITY")
        world._last.key = "0:3"  # noqa: SLF001 - in another town's building: still to that town first
        self.assertEqual(lead_toward(world, "PETALBURG_CITY_GYM"), "PETALBURG_CITY")
        world._last.key = "0:1"  # noqa: SLF001 - in the town itself: looked for here (None)
        self.assertIsNone(lead_toward(world, "PETALBURG_CITY_GYM"))
        # FAULT half: a building of a town never visited has no town to head for
        self.assertIsNone(lead_toward(world, "RUSTBORO_CITY_GYM"))

    def test_a_house_already_seen_is_not_walked_back_into_on_the_way(self):
        from ai_player.brain.goals import keeps_going
        from ai_player.brain.navigator import Target
        world = world_with("LITTLEROOT_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F", current="LITTLEROOT_TOWN")
        world.warps["0:1|14,8"] = {"to": "0:2", "arrival": [2, 8], "uses": 1, "by": "ai", "inferred": False}
        house = Target("back", (14, 9), "it leads back to the house", exit=(14, 8), direction="up")
        road = Target("road", (10, -1), "a road leads up")
        self.assertFalse(keeps_going(world, house, "ROUTE103"))
        self.assertTrue(keeps_going(world, house, "LITTLEROOT_TOWN_MAYS_HOUSE_1F"))  # unless that house is the goal
        self.assertTrue(keeps_going(world, road, "ROUTE103"))


class BossLevelTests(unittest.TestCase):
    def boss_levels(self) -> dict:
        support = Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO)
        tree = ast.parse((support / "ai-agent" / "knowledge.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "BOSS_LEVELS" for t in node.targets):
                return ast.literal_eval(node.value)
        raise AssertionError("no BOSS_LEVELS")

    def test_roxannes_levels_are_the_verified_boss_table(self):
        story = load_story("BOY")
        roxanne = story.milestones[story.index("ch4_roxanne")]
        self.assertEqual(sorted(roxanne.fight_levels), sorted(set(self.boss_levels()["ROXANNE"])))
        self.assertEqual(story.trainer_levels["ROXANNE_1"], (12, 12, 15))

    def test_the_rival_is_level_5_and_the_target_follows(self):
        story = load_story("BOY")
        rival = story.milestones[story.index("ch1_rival_route103")]
        self.assertEqual(rival.fight_levels, (5,))
        roxanne = story.milestones[story.index("ch4_roxanne")]
        self.assertEqual(max(roxanne.fight_levels) + ERRANDS["Trainer"].train_margin, 18)


class DriftTests(unittest.TestCase):
    def walk(self, seed: int, steps: int = 40_000, drift_on: bool = True) -> PersonalityState:
        state = PersonalityState("Story", random.Random(seed), drift_on=drift_on)
        for step in range(0, steps, 7):
            state.step(step)
        return state

    def test_drifts_are_bounded_and_always_come_back(self):
        lengths, drifts = [], 0
        for seed in range(30):
            state = self.walk(seed)
            history = state.history
            for drift, back in zip(history[::2], history[1::2]):
                self.assertEqual(drift["kind"], "drift")
                self.assertEqual(back["kind"], "back")
                self.assertEqual(back["active"], "Story")
                self.assertNotEqual(drift["active"], "Story")
                self.assertEqual(drift["step"] % DRIFT_EVERY < 7 or drift["step"] >= DRIFT_EVERY, True)
                lengths.append(back["step"] - drift["step"])
                drifts += 1
        self.assertGreater(drifts, 0)
        self.assertTrue(all(DRIFT_STEPS[0] <= n <= DRIFT_STEPS[1] + 7 for n in lengths), lengths)

    def test_the_drift_rate_follows_its_chance(self):
        opportunities = drifts = 0
        for seed in range(60):
            state = self.walk(seed)
            drifts += sum(1 for h in state.history if h["kind"] == "drift")
            opportunities += state.draws
            # a draw only at its base and at most one per DRIFT_EVERY steps walked (plus one right after each drift)
            self.assertLessEqual(state.draws, 40_000 // DRIFT_EVERY + len(state.history))
        rate = drifts / opportunities
        self.assertLess(abs(rate - DRIFT_CHANCE), 0.06, f"{drifts} drifts in {opportunities} draws: {rate:.3f}")

    def test_no_drift_when_off(self):
        self.assertEqual(self.walk(3, drift_on=False).history, [])


class ChoiceTests(unittest.TestCase):
    def test_the_favourite_is_a_wild_species_and_varies(self):
        favourites = {choose_favourite(random.Random(seed)) for seed in range(50)}
        self.assertTrue(favourites <= set(wild_species()))
        self.assertGreater(len(favourites), 20)
        self.assertNotIn("Treecko", wild_species())  # a starter is no wild species: FAULT half of the extraction

    def test_the_starter_named_or_drawn(self):
        self.assertEqual(choose_starter(random.Random(1), "Story", "mudkip")[0], "MUDKIP")
        drawn = {choose_starter(random.Random(seed), "Story")[0] for seed in range(40)}
        self.assertEqual(drawn, {"TREECKO", "TORCHIC", "MUDKIP"})
        with self.assertRaises(ValueError):
            choose_starter(random.Random(1), "Story", "PIKACHU")

    def test_questions_by_their_words(self):
        def ask(words, state="OVERWORLD"):
            screen = ScreenState(game_state=state, screen="text", menu="yes_no", text_box_open=True, waits_for_button=False,
                                 in_battle=False, text=words)
            return answer_question(Observation(frame=1, screen=screen, player=None, view=None, party=(), bag=None,
                                               progress=None, battle=None, last_battle_outcome=0, problems=(), cost_ms=0.0))
        self.assertFalse(ask("Why don't you give a nickname to the MUDKIP you received?")[0])
        self.assertTrue(ask("don't you think it might be a good idea to go see MAY?")[0])
        self.assertTrue(ask("Do you choose this POKéMON?", "CHOOSE_STARTER")[0])
        self.assertTrue(ask("Would you like to rest your POKéMON?")[0])


class ProductiveTests(unittest.TestCase):
    """(build step 5.2, PRODUCTIVE CURIOSITY: the step-5.1 adversarial review, 2026-10-15, "it LOAFS, and every metric pays
    for it") Curiosity counted by what it BROUGHT; what brought nothing marked so it is not tried again; places someone
    keeps standing in the way of blocked; detours that say whether they arrived and talk to the person they chose; a look
    round only among new things; a known town no new place; and the instrument that sees pressing with nothing new."""

    def test_a_curiosity_goal_counts_by_what_it_brought(self):
        from ai_player.brain.goals import YIELD_TILES_MIN, Goal, goal_yield
        base = {"tiles": 100, "maps": 3, "items": 0, "caught": 1, "species": 2, "pages": 10}

        def made(kind: str, outcome: str = "done", **more) -> dict:
            return goal_yield(Goal(kind, "x"), base, {**base, **{k: base[k] + v for k, v in more.items()}}, outcome)

        self.assertFalse(made("explore", tiles=1)["productive"])  # CH1M's look round of OLDALE: one new tile
        self.assertFalse(made("explore", tiles=YIELD_TILES_MIN - 1)["productive"])
        self.assertTrue(made("explore", tiles=YIELD_TILES_MIN)["productive"])
        for key in ("maps", "items", "caught", "species", "pages"):
            self.assertTrue(made("catch", **{key: 1})["productive"], key)
        self.assertTrue(made("chat", outcome="talked", pages=1)["productive"])
        # (the verifier's round: 60 nurses, 46 clerks and 21 footprints men chatted with straight after they had spoken,
        # every one hearing nothing new) a talk that told it NOTHING NEW is no yield (FAULT half: credited by its label)
        heard_nothing = made("chat", outcome="talked")
        self.assertFalse(heard_nothing["productive"])
        self.assertEqual((heard_nothing["talks"], heard_nothing["talked"]), (True, False))
        self.assertFalse(made("chat", outcome="unreachable: no tile from which the npc can be talked to")["productive"])
        # a DETOUR only when it reached its place: the tiles seen on the way are no credit (FAULT half: 40 tiles count)
        self.assertFalse(made("detour", outcome="not reached: the frontier at (-7, 15) (budget: ran out)", tiles=40)
                         ["productive"])
        self.assertTrue(made("detour", outcome="reached the frontier at (3, 3) (done: a detour)", tiles=9)["productive"])
        self.assertTrue(made("detour", outcome="reached the people at (3, 3) (done: a detour); talked", pages=2)
                        ["productive"])
        self.assertFalse(made("detour", outcome="reached the people at (3, 3) (done: a detour); talked")["productive"])
        self.assertFalse(made("detour", outcome="reached the grass at (3, 3) (done: a detour)")["productive"])

    def test_a_look_round_is_worth_only_what_it_showed_for_its_time(self):
        """(the round's development sweep step52dev2: with the 8 tiles alone, the LOAF control's looks round among tiles it
        had stood on, 0-11 new tiles per 1,000 frames, were productive in 80 % of their frames) a look round or a detour
        must show `YIELD_TILE_RATE` new tiles per 1,000 of its frames; another kind keeps its own measure (a catching roam,
        its catch)."""
        from ai_player.brain.goals import YIELD_TILE_RATE, Goal, goal_yield
        base = {"tiles": 100, "maps": 3, "items": 0, "caught": 1, "species": 2, "pages": 10}

        def made(kind: str, tiles: int, frames: int, outcome: str = "budget: ran out") -> bool:
            return goal_yield(Goal(kind, "x"), base, {**base, "tiles": 100 + tiles}, outcome, frames)["productive"]

        self.assertEqual(YIELD_TILE_RATE, 20)
        self.assertFalse(made("explore", 9, 3000))  # FAULT half: 9 tiles in 3,000 frames counted
        self.assertTrue(made("explore", 9, 300))
        self.assertTrue(made("explore", 60, 3000))
        self.assertFalse(made("detour", 20, 1500, "reached the frontier at (3, 3)"))
        self.assertTrue(made("detour", 30, 1500, "reached the frontier at (3, 3)"))
        self.assertTrue(made("catch", 9, 13000))  # a roam's tiles as before: its measure is its catch
        # its OWN time: the battles met in it are not (a look round of ROUTE 101 that met 12 battles walked 1,561 of 5,703)
        fought = goal_yield(Goal("explore", "x"), {**base, "battle_frames": 1000},
                            {**base, "tiles": 130, "battle_frames": 3000}, "budget: ran out", 3000)
        self.assertEqual(fought["walking"], 1000)
        self.assertTrue(fought["productive"])  # FAULT half: 30 tiles in 3,000 frames, the 2,000 of battles counted

    def test_the_battle_clock_counts_the_frames_a_battle_was_on_screen(self):
        """`hands/waiting.py` BattleClock: from one look in a battle to the next (the game state's battle phases too, as
        `skills/flee.py` in_battle reads them), never across a look out of one."""
        from dataclasses import replace
        from ai_player.hands.waiting import BattleClock
        clock = BattleClock()

        def seen(frame: int, state: str = "OVERWORLD", in_battle: bool = False) -> Observation:
            plain = look(frame=frame)
            return replace(plain, screen=replace(plain.screen, game_state=state, in_battle=in_battle))

        for observation in (seen(100), seen(110, "BATTLE", True), seen(150, "BATTLE", True), seen(200, "BATTLE", True),
                            seen(210), seen(300, "BATTLE_STARTING"), seen(320, "BATTLE_STARTING"), seen(330)):
            clock(observation)
        # FAULT halves: 90 with the battle's opening (BATTLE_STARTING, not yet `in_battle`) missed; 210 counted across
        # the look out of the battle at f210
        self.assertEqual(clock.battle_frames, 90 + 20)

    def test_the_play_loop_judges_a_curiosity_goal_by_its_yield(self):
        """The REAL play loop: a look round whose walk showed 20 new tiles is productive; one that showed none is NOT
        (reported "not done", told so, its map exhausted, the end record's idle count); a chat that talked is productive."""
        from ai_player import mode as mode_module
        from ai_player.brain.goals import Goal
        scripted = ["explore", "explore", "chat", "chat"]
        explores: list[int] = []
        chats: list[int] = []

        class Scripted(mode_module.GoalManager):
            def next_goal(self, look_, world, milestone, index):
                if scripted:
                    kind = scripted.pop(0)
                    self.memory.decisions += 1
                    return Goal(kind, f"scripted {kind}", milestone.id, key=f"{kind}:{world.current}", via=world.current)
                return super().next_goal(look_, world, milestone, index)

        def effect(goal, world, runner):
            if goal.kind == "explore":
                explores.append(1)
                if len(explores) == 1:
                    world.tiles_learned += 60  # the first look round showed 60 new tiles, the second none
                return True, "budget: 3000 frames ran out"  # both ran their time: 5.1 called both "done"
            if goal.kind == "chat":
                chats.append(1)
                if len(chats) == 1:
                    world.heard.add("Hello there!")  # the first chat told it something; the second heard nothing new
                return True, "talked"
            return None

        loop = PlayLoopTests()
        original = loop.run_loop

        def run(**kwargs):
            with mock.patch.object(mode_module, "GoalManager", Scripted):
                return original(**kwargs)

        reason, hands, pursued, _, report = run(screen=loop.free_screen(), budget=20_000, effect=effect)
        self.assertEqual(pursued[:4], ["explore", "explore", "chat", "chat"])
        ends = [extra for decision, _, _, extra in hands.notes if decision == "goal_end"][:4]
        # FAULT halves: all by their kind; (the verifier's round) the talk that heard nothing new credited by its label
        self.assertEqual([e["yield"]["productive"] for e in ends], [True, False, True, False])
        self.assertEqual([e["ok"] for e in ends], [True, False, True, False])  # the empty look round is NOT done (5.1: done)
        self.assertEqual([g["ok"] for g in report["goals"][:4]], [True, False, True, False])
        brought = [line for line in hands.told if line.startswith("[AI-GOALS] its ")]
        self.assertIn("its explore brought tiles 60", brought[0])
        self.assertIn("NOT productive", brought[1])
        self.assertIn("is exhausted for this milestone", brought[1])  # FAULT half: no mark, tried again
        self.assertIn("its chat brought pages 1, a talk", brought[2])
        self.assertIn("its chat brought a talk that told it nothing new: NOT productive", brought[3])
        end = next(extra for decision, _, _, extra in hands.notes if decision == "end")
        self.assertGreaterEqual(end["idle"]["goals"], 1)
        self.assertTrue(end["exhausted"])

    def test_what_brought_nothing_is_marked_and_not_tried_again(self):
        """`after_goal`: a look round that brought nothing EXHAUSTS its map for the milestone (no "some more" there); a
        detour that did not get there BLOCKS its place for curiosity."""
        from ai_player.brain.goals import Goal
        mgr = manager("Catcher")
        told = mgr.after_goal(Goal("explore", "x", via="0:3"), {"productive": False, "frames": 3000}, 5000, "ch1_lab")
        self.assertEqual(mgr.memory.exhausted, {"0:3|ch1_lab": "a look round there brought nothing new (f5000)"})
        self.assertIn("exhausted", told)
        mgr.after_goal(Goal("detour", "x", via="0:3"), {"productive": False, "reached": False,
                                                        "place": ["0:3", -7, 15, "frontier"]}, 6000, "ch1_lab")
        self.assertIn((-7, 15), mgr.blocked_on("ch1_lab", "0:3"))
        self.assertEqual(mgr.blocked_on("ch1_pokedex", "0:3"), {})  # another milestone: tried again (the man moves on)
        fresh = manager("Catcher")
        fresh.after_goal(Goal("explore", "x", via="0:3"), {"productive": True}, 5000, "ch1_lab")
        self.assertEqual(fresh.memory.exhausted, {})  # FAULT half: a productive look round marks nothing

    def detour(self, places, people=(), current_changes=False, reach_it=True, objects=()):
        """`GoalRunner._detour` with a stand-in navigator: ROUTE 101 seen round the player at (10, 10), `places` the
        explorer's candidates (kind, tile, who), the walk reaching the chosen place (or not, or leaving the map)."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import Goal, GoalRunner
        from ai_player.brain.navigator import Target
        mgr = manager("Trainer")
        world = world_with("ROUTE101", "OLDALE_TOWN", current="ROUTE101")
        memory = world.maps["0:1"]
        for x in range(0, 21):
            for y in range(0, 21):
                memory.tiles[(x, y)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (10, 10))
        memory.people_now = frozenset(people)
        chosen: list = []

        def run(intent, why):
            target = intent.choose(nav, look())
            chosen.append(target)
            if target is not None and current_changes:
                world._last.key = "0:2"  # noqa: SLF001 - the walk crossed onto OLDALE
            elif target is not None and reach_it:
                intent.reached(target)
            yield
            return "done: a detour" if intent.done(look()) else "budget: 1500 frames ran out"

        nav = types.SimpleNamespace(run=run, world=world, rng=random.Random(1), is_excluded=lambda t: False,
                                    where=lambda seen: (memory, (10, 10)))
        targets = [Target(kind, tile, f"a {kind}", who=who) for kind, tile, who in places]
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(objects=objects)), nav, mgr,
                            types.SimpleNamespace(purpose=""), lambda line: None)
        talks = []

        def talk_to(hands, nav_, person_, why):
            talks.append(person_.local_id)
            yield
            return "talked"

        with mock.patch.object(goals_module, "candidates", lambda *a, **k: list(targets)), \
                mock.patch.object(goals_module, "pick", lambda found, rng: found[0]), \
                mock.patch.object(goals_module, "talk_to", talk_to):
            ok, outcome = drive(runner.pursue(Goal("detour", "on the way", steps=1500, via="0:1"), mgr.story.milestones[8],
                                              8, lambda seen: 8))
        return ok, outcome, chosen, runner, mgr, talks

    def test_a_detour_says_whether_it_arrived(self):
        """(the review's finding 3: "looked at the frontier at (-7, 15)" for a place never reached) the outcome is "reached
        ..." or "not reached ...", and only a reached detour is done; the place is kept for the yield."""
        ok, outcome, chosen, runner, _, _ = self.detour([("frontier", (16, 10), None)])
        self.assertTrue(ok, outcome)
        self.assertTrue(outcome.startswith("reached the frontier at (16, 10)"), outcome)
        self.assertEqual(runner.detour_place, ["0:1", 16, 10, "frontier"])
        ok, outcome, _, _, _, _ = self.detour([("frontier", (16, 10), None)], reach_it=False)
        self.assertFalse(ok)  # FAULT half (5.1): "budget ... looked at the frontier" counted as done
        self.assertTrue(outcome.startswith("not reached: the frontier at (16, 10)"), outcome)
        ok, outcome, _, _, _, _ = self.detour([("frontier", (16, 10), None)], current_changes=True)
        self.assertFalse(ok)
        self.assertIn("the walk left the map", outcome)

    def test_a_detour_to_a_person_talks_to_them(self):
        """(the review's finding 3: "nothing happens on arrival, not even a talk with the people it chose")"""
        stranger = person(16, 9, gfx=1, local_id=7)
        ok, outcome, _, _, mgr, talks = self.detour([("people", (16, 10), 7)], objects=[stranger])
        self.assertTrue(ok, outcome)
        self.assertEqual(talks, [7])  # FAULT half: no talk on arrival
        self.assertIn("talked", outcome)
        self.assertIn("0:1|7", mgr.memory.talked)
        _, outcome, _, _, _, talks = self.detour([("people", (16, 10), 7)], objects=[])
        self.assertEqual(talks, [])
        self.assertIn("not on screen any more", outcome)

    def test_a_detour_chooses_only_a_place_it_can_walk_to(self):
        """(the review's finding 3: CH1C and CH1M both chose (-7, 15), past OLDALE's west exit someone stood in; CH2M a tile
        its own log called unreachable) never a place behind someone standing in every way to it, past an edge it has seen
        crossed, or blocked for curiosity; a place it can walk to over known tiles is chosen."""
        places = [("frontier", (30, 10), None), ("frontier", (16, 10), None)]
        _, _, chosen, _, _, _ = self.detour(places)
        self.assertEqual(chosen[0].tile, (16, 10))  # (30, 10) is past the tiles it knows: no known way there
        boxed = ((9, 10), (11, 10), (10, 9), (10, 11))
        ok, outcome, chosen, _, _, _ = self.detour([("frontier", (16, 10), None)], people=boxed)
        self.assertEqual(chosen, [None])  # someone stands in every way out: FAULT half, chosen and pushed against
        self.assertTrue(outcome.startswith("not reached: nothing off the way here that it can walk to"), outcome)
        self.assertFalse(ok)

    def test_a_detour_never_chooses_a_blocked_place_or_one_past_a_known_edge(self):
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import Goal, GoalRunner
        from ai_player.brain.navigator import Target
        for case in ("blocked", "edge"):
            mgr = manager("Trainer")
            world = world_with("ROUTE101", current="ROUTE101")
            memory = world.maps["0:1"]
            for x in range(0, 21):
                for y in range(0, 21):
                    memory.tiles[(x, y)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (10, 10))
            if case == "blocked":
                mgr.blocked_on(mgr.story.milestones[8].id, "0:1")[(16, 10)] = "someone stood in the way"
            else:
                memory.edges["right"] = 15  # crossed at x 15: x >= 15 is the next map
            seen = []

            def run(intent, why, seen=seen):
                seen.append(intent.choose(nav, look()))
                yield
                return "budget: ran out"

            nav = types.SimpleNamespace(run=run, world=world, rng=random.Random(1), is_excluded=lambda t: False,
                                        where=lambda look_, memory=memory: (memory, (10, 10)))
            targets = [Target("frontier", (16, 10), "east"), Target("grass", (10, 18), "south")]
            runner = GoalRunner(types.SimpleNamespace(look=lambda: look()), nav, mgr, types.SimpleNamespace(purpose=""),
                                lambda line: None)
            with mock.patch.object(goals_module, "candidates", lambda *a, **k: list(targets)), \
                    mock.patch.object(goals_module, "pick", lambda found, rng: found[0]):
                drive(runner._detour(Goal("detour", "x", steps=1500), mgr.story.milestones[8]))  # noqa: SLF001
            self.assertEqual(seen[0].tile, (10, 18), case)  # FAULT half: the east frontier first

    def detour_seen(self, case, blocked=(17, 9)):
        """One detour's choices on ROUTE 101 (all seen, the player at (10, 10)), with `case` set up: the places it chose,
        whether its intent was done after a scene on the way ("scene"), and its outcome."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import Goal, GoalRunner
        from ai_player.brain.navigator import Target
        mgr = manager("Trainer")
        world = world_with("ROUTE101", current="ROUTE101")
        memory = world.maps["0:1"]
        for x in range(0, 21):
            for y in range(0, 21):
                memory.tiles[(x, y)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (10, 10))
        excluded: set = set()
        nav = types.SimpleNamespace(world=world, rng=random.Random(1), is_excluded=lambda t: t.tile in excluded,
                                    where=lambda look_: (memory, (10, 10)), scene_walls={}, scene_hits={})
        if case == "beside":
            mgr.blocked_on(mgr.story.milestones[8].id, "0:1")[blocked] = "a scene stopped the way there 2 times"
        elif case == "walled":
            nav.scene_walls = {"0:1": {(9, 10), (11, 10), (10, 9), (10, 11)}}  # a scene sent it back from every way out
        seen, dones = [], []

        def run(intent, why):
            seen.append(intent.choose(nav, look()))
            dones.append(intent.done(look()))
            if case == "scene" and seen[-1] is not None:
                nav.scene_hits[f"0:1|{seen[-1].key}"] = [500]  # a scene stopped the way there, once
                dones.append(intent.done(look()))
            if case == "unreachable" and seen[-1] is not None:
                excluded.add(seen[-1].tile)  # the navigator found no way there
                seen.append(intent.choose(nav, look()))
            yield
            return "done: a detour" if dones[-1] else "budget: ran out"

        nav.run = run
        targets = [Target("frontier", (16, 10), "east"), Target("grass", (10, 18), "south")]
        if case == "unreachable":  # the tile beside the place it could not reach: the same corner
            targets.insert(1, Target("frontier", (16, 11), "east, a step south"))
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look()), nav, mgr, types.SimpleNamespace(purpose=""),
                            lambda line: None)
        with mock.patch.object(goals_module, "candidates", lambda *a, **k: list(targets)), \
                mock.patch.object(goals_module, "pick", lambda found, rng: found[0]):
            outcome = drive(runner._detour(Goal("detour", "x", steps=1500), mgr.story.milestones[8]))  # noqa: SLF001
        return [None if t is None else t.tile for t in seen], dones, outcome

    def test_a_detour_never_chooses_a_place_beside_a_blocked_one(self):
        """(the round's development sweeps: a detour chose (2, -3) beside the (3, -4) a look round had just been turned back
        from by LITTLEROOT's twin, step52dev2, and (5, -4) two tiles from (3, -3), step52dev3, and met her twice more) the
        same corner of the map, `BESIDE` tiles round, is not chosen."""
        from ai_player.brain.goals import BESIDE
        self.assertEqual(BESIDE, 2)
        self.assertEqual(self.detour_seen("none")[0][0], (16, 10))
        self.assertEqual(self.detour_seen("beside")[0][0], (10, 18))  # FAULT half: (16, 10), beside the blocked (17, 9)
        self.assertEqual(self.detour_seen("beside", (18, 8))[0][0], (10, 18))  # 2 tiles: FAULT half, a radius of 1
        self.assertEqual(self.detour_seen("beside", (19, 10))[0][0], (16, 10))  # 3 tiles: another corner

    def test_a_detour_ends_at_the_first_scene_on_the_way(self):
        """(step52dev2 and step52dev3: every detour stopped by a scene met it TWICE, about 2,200 frames, because a scene
        does not make the navigator choose again) the first scene that stops the way to its place ENDS the detour, which
        says so; a detour with no scene on the way is not done."""
        tiles, dones, outcome = self.detour_seen("scene")
        self.assertEqual(tiles, [(16, 10)])
        self.assertEqual(dones, [False, True])  # FAULT half: walked on to meet it again
        self.assertTrue(outcome.startswith("not reached: the frontier at (16, 10) (a scene stopped the way there)"), outcome)

    def test_a_detour_swaps_a_place_it_cannot_reach_for_another_corner(self):
        """A place the navigator cannot reach is swapped for another, never the one beside it (the same corner)."""
        self.assertEqual(self.detour_seen("unreachable")[0], [(16, 10), (10, 18)])  # FAULT half: (16, 11)

    def test_a_detour_reaches_round_the_tiles_a_scene_sent_it_back_from(self):
        """The walk plans round the scene walls, so the reach does: walled in, nothing is chosen (FAULT half: a place)."""
        self.assertEqual(self.detour_seen("walled")[0], [None])

    def test_a_catching_roam_gives_the_hunt_up_after_fruitless_battles(self):
        """(step52dev4: catching roams that met only POKéMON it had seen ran 8,136-16,867 frames, 4-7 battles, nothing new)
        `GoalRunner.roam_hooks(hunt=True)`: HUNT_FRUITLESS battles in a row with the POKéDEX's seen and owned counts
        unchanged stop the roam; a species first seen starts the count again; a TRAINING roam never stops for it."""
        from ai_player.brain.goals import HUNT_FRUITLESS, HUNT_STOP, GoalRunner
        world = world_with("ROUTE101", current="ROUTE101")

        def seen(dex_seen: int) -> Observation:
            plain = look(party=[mon(9)])
            return replace(plain, progress=replace(plain.progress, dex_seen=dex_seen))

        for hunt in (True, False):
            nav = types.SimpleNamespace(world=world, battle_log=[], battle_limit=None, battle_rest=None, roam_stop=None)
            runner = GoalRunner(types.SimpleNamespace(look=lambda: look()), nav, manager("Catcher"),
                                types.SimpleNamespace(purpose=""), lambda line: None)
            runner.roam_hooks(hunt=hunt)
            stops = [nav.roam_stop(seen(3))]
            for _ in range(HUNT_FRUITLESS - 1):
                nav.battle_log.append((1, "wild", "won"))
                stops.append(nav.roam_stop(seen(3)))
            nav.battle_log.append((1, "wild", "won"))
            stops.append(nav.roam_stop(seen(4)))  # a species first seen in that battle: the count starts again
            for _ in range(HUNT_FRUITLESS):
                nav.battle_log.append((1, "wild", "won"))
                stops.append(nav.roam_stop(seen(4)))
            if hunt:
                self.assertEqual(stops[:-1], [None] * (len(stops) - 1))  # FAULT half: stopped at the third battle
                self.assertTrue(str(stops[-1]).startswith(HUNT_STOP), stops[-1])  # FAULT half: the hunt roams on
            else:
                self.assertEqual(stops, [None] * len(stops))

    def test_a_catch_goal_asks_the_hunt_rule_and_training_does_not(self):
        """`GoalRunner._pursue` hands a CATCH goal's roam the hunt rule (a TRAIN goal's roam never)."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import HUNT_FRUITLESS, HUNT_STOP, Goal, GoalRunner
        asked = []

        def roam(hands, nav, steps, why):
            nav.roam_stop(look(party=[mon(9)]))  # the roam's first free look
            nav.battle_log.extend([(1, "wild", "won")] * HUNT_FRUITLESS)
            asked.append(nav.roam_stop(look(party=[mon(9)])))
            yield
            return "roamed: roam: 10 training steps"

        for kind in ("catch", "train"):
            mgr = manager("Catcher")
            world = world_with("ROUTE101", current="ROUTE101", grass=True)
            nav = types.SimpleNamespace(world=world, battle_log=[], battle_limit=None, battle_rest=None, roam_stop=None)
            runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(9)]), note=lambda *a: None), nav, mgr,
                                types.SimpleNamespace(purpose=""), lambda line: None)
            runner._grass_map = lambda milestone: None  # noqa: SLF001 - it stands in the grass already
            with mock.patch.object(goals_module, "roam_train", roam):
                drive(runner._pursue(Goal(kind, "x", steps=10), mgr.story.milestones[8], 8, lambda s: 8))  # noqa: SLF001
        self.assertTrue(str(asked[0]).startswith(HUNT_STOP), asked)  # FAULT half: the catch never asked
        self.assertIsNone(asked[1])

    GAP = {"A": ["##.##", "#...#", "#...#", "#...#", "#####"], "B": ['#"""#', '#"""#']}
    GAP_LINKS = {("A", "up"): ("B", (0, 2)), ("B", "down"): ("A", (0, -2))}

    def test_a_walk_to_a_tile_ends_when_it_leaves_the_map(self):
        """(found by the pushing property, step52dev6, seed 1049: a walk to grass seen past OLDALE's bottom edge crossed
        onto ROUTE 101, where the same coordinates lie past ITS edge, then onto LITTLEROOT and back, 3,313 frames)
        `Navigator.go_to`: a tile is a tile of the map it was chosen on; the walk ends when it leaves that map, and says
        so."""
        from ai_player.gates.test_world import GridGame, drive as drive_world, rig
        game = GridGame(self.GAP, ("A", (2, 3)), links=self.GAP_LINKS)
        hands, nav, world, _, _ = rig(game)
        drive_world(nav.go_to((2, 1), "to the gap", 600))
        self.assertIn((2, -1), world.here().tiles)  # seen past the top edge
        outcome = drive_world(nav.go_to((2, -1), "past the edge", 600))
        self.assertEqual(game.map, "B")
        # FAULT halves: on B, (2, -1) walked on for (the walk ends stuck, not done); nothing said of the map it left
        self.assertTrue(outcome.startswith("left the map: A for B (done"), outcome)

    def test_a_roam_walks_on_to_the_grass_of_the_map_it_crossed_onto(self):
        """`skills/roam_train.py`: the nearest grass was seen past the map's edge; the walk to it ends on the next map
        (`go_to` "left the map"), and the roam walks once more, to that map's own grass, and roams there."""
        from ai_player.gates.test_world import GridGame, drive as drive_world, rig
        from ai_player.skills.roam_train import roam_train
        game = GridGame(self.GAP, ("A", (2, 3)), links=self.GAP_LINKS)
        hands, nav, world, _, _ = rig(game, personality="Catcher")
        drive_world(nav.go_to((2, 1), "to the gap", 600))
        outcome = drive_world(roam_train(hands, nav, 10), budget=200_000)
        self.assertEqual(game.map, "B")
        self.assertTrue(outcome.startswith("roamed"), outcome)  # FAULT half: "could not reach the grass"

    def test_a_tile_of_this_map_is_walked_to_over_tiles_of_this_map(self):
        """(found by the pushing property, step52dev4, chapter-2 seed 1026: ROUTE 103's frontier at (25, 15) was planned
        through OLDALE's tiles seen below the edge, 3,372 frames of crossing back and forth) `Navigator._next_step`: with
        the bottom edge crossed (y >= 6 is the next map), the way from (2, 5) to (8, 5) goes round the wall at x 5 INSIDE the
        map, not through the next map's row below; a target past the edge (a road) is still walked to across it."""
        from ai_player.brain.navigator import Navigator, Target
        from ai_player.hands.pad import Hands
        from ai_player.world.memory import WorldMemory
        world = WorldMemory()
        memory = MapMemory("0:1", "ROUTE103", "ROUTE103")
        for x in range(0, 10):
            for y in range(0, 9):
                wall = x == 5 and 1 <= y <= 5  # a wall down to the edge: inside, the way round is through y 0
                memory.tiles[(x, y)] = TileFact(wall, False, False, False, None, False, False, 3, "NORMAL", 0, (2, 5))
        memory.edges["down"] = 6
        nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world, random.Random(1))
        first = nav._next_step(memory, (2, 5), Target("frontier", (8, 5), "east"), frozenset())  # noqa: SLF001
        self.assertNotEqual(first, "down")  # FAULT half: the short way through the next map's row
        self.assertEqual(first, "up")
        nav.plan, nav.planned_for = None, None
        self.assertEqual(nav._next_step(memory, (2, 5), Target("road", (2, 7), "the road down"), frozenset()),  # noqa: SLF001
                         "down")

    def test_a_frontier_it_found_no_way_to_is_not_left_to_see(self):
        """(found by the pushing property, step52dev6, the beeline's chapter 2 of seed 1050: ROUTE 103's one frontier it
        could not reach kept "1 thing left to see" there, and OLDALE's explorer went back for it, 186 crossings) a frontier
        a walk found NO way to (the navigator's "unreachable") is marked in the world memory and left out of the map's
        `promise` until the map shows something new."""
        from ai_player.brain.navigator import Intent, Target
        from ai_player.gates.test_world import GridGame, drive as drive_world, rig
        rows = ["#" * 30] + ["#" + "." * 8 + "#" + "." * 19 + "#" for _ in range(9)] + ["#" * 30]
        game = GridGame({"SPLIT": rows}, ("SPLIT", (3, 5)))  # a wall at x 9; the screen shows x 10, not x 11
        hands, nav, world, _, _ = rig(game)
        world.observe(game.look())
        key = world.current
        self.assertEqual(world.promise(key), 9)  # x 10, y 1-9, beside the unseen x 11: frontier, across the wall
        tried: list = []

        def choose(navigator, look_):  # a walk that tries the frontier at (10, 5) once
            if tried:
                return None
            tried.append(1)
            return Target("frontier", (10, 5), "across the wall")

        outcome = drive_world(nav.run(Intent("try it", 2000, choose, lambda look_: False), "try"))
        self.assertTrue(outcome.startswith("stuck"), outcome)
        self.assertIn((10, 5), world.unreached.get(key, {}))  # FAULT half: no mark
        self.assertEqual(world.promise(key), 8)  # FAULT half: the mark not asked by `promise`
        # the map shows something new (a tile learned): the frontier counts again (a way may be known now)
        world.maps[key].tiles[(40, 40)] = TileFact(True, False, False, False, None, False, False, 3, "NORMAL", 0, (3, 5))
        self.assertEqual(world.promise(key), 9)

    def test_the_navigator_keeps_the_places_a_scene_made_it_give_up(self):
        """`Navigator._scene_met`: a target given up because a scene stopped the way there is kept in `scene_given_up`
        (map key, tile, why), over every intent, for the goal runner to read."""
        from ai_player.brain.navigator import Navigator, Target
        from ai_player.hands.pad import Hands
        from ai_player.world.memory import WorldMemory
        world = WorldMemory()
        nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world, random.Random(1))
        world._last.key = "0:9"  # noqa: SLF001
        target = Target("frontier", (3, -4), "x")
        still = mock.Mock(last=80, last_progress=80)
        self.assertFalse(nav._scene_met(f"0:9|{target.key}", target, 90, still))  # noqa: SLF001
        self.assertEqual(nav.scene_given_up, [])
        self.assertTrue(nav._scene_met(f"0:9|{target.key}", target, 300, still))  # noqa: SLF001
        self.assertEqual([(key, tile) for key, tile, _ in nav.scene_given_up], [("0:9", (3, -4))])  # FAULT half: none

    def test_a_place_a_scene_turned_a_look_round_back_from_is_blocked_for_curiosity(self):
        """(step52dev2: in 4 of the 7 detours that did not arrive, a look round had just given up a place past LITTLEROOT's
        twin) `GoalRunner.pursue`: the targets the navigator gave up because of a scene during a walk that looks round are
        blocked for curiosity in the milestone; a story walk's are not (the navigator keeps those to its own walk)."""
        from ai_player.brain.goals import Goal, GoalRunner
        for kind, expect in (("explore", {(3, -4): "a scene stopped the way there 2 times"}), ("go", {})):
            mgr = manager("Catcher")
            milestone = mgr.story.milestones[8]
            world = world_with("LITTLEROOT_TOWN", current="LITTLEROOT_TOWN")
            nav = types.SimpleNamespace(world=world, carried_scene_walls=None, scene_walls={}, battle_log=[],
                                        scene_given_up=[("0:9", (1, 1), "an earlier goal's")])

            def pursue(goal, milestone_, index, current, nav=nav):
                nav.scene_given_up.append(("0:9", (3, -4), "a scene stopped the way there 2 times"))
                yield
                return True, "stuck: nothing new"

            runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(9)])), nav, mgr,
                                types.SimpleNamespace(purpose=""), lambda line: None)
            runner._pursue = pursue  # noqa: SLF001
            drive(runner.pursue(Goal(kind, "x", via="0:9"), milestone, 8, lambda s: 8))
            self.assertEqual(dict(mgr.memory.blocked.get(milestone.id, {}).get("0:9", {})), expect, kind)
            self.assertNotIn((3, -4), mgr.memory.scene_walls[milestone.id].get("0:9", set()), kind)

    def test_someone_in_the_way_again_and_again_blocks_the_place(self):
        """`_PersonBlock`: PERSON_BLOCK_HITS people in the way on the walk to one place, with no new tile seen since the
        first, block it (once); a new tile seen in between starts the count again."""
        from ai_player.brain.goals import PERSON_BLOCK_HITS, _PersonBlock
        from ai_player.brain.navigator import Plan
        world = types.SimpleNamespace(current="0:3", tiles_learned=500)
        nav = types.SimpleNamespace(stats=types.SimpleNamespace(people=8), world=world,
                                    plan=Plan("frontier:(-7, 10)", "0:3", (2, 10), ["left"] * 9, True))
        blocked = []
        watch = _PersonBlock(nav, lambda key, tile, why: blocked.append((key, tile, why)))
        for frame in range(PERSON_BLOCK_HITS - 1):
            nav.stats.people += 1
            watch(look(frame=1000 + frame))
        self.assertEqual(blocked, [])
        world.tiles_learned += 15  # something new came into view: the count starts again
        nav.stats.people += 1
        watch(look(frame=1100))
        self.assertEqual(blocked, [])  # FAULT half: blocked although the walk brought new tiles
        for frame in range(PERSON_BLOCK_HITS - 1):
            nav.stats.people += 1
            nav.plan = Plan("frontier:(-7, 10)", "0:3", (3, 10), ["left"] * 10, True)  # the same place, a step on
            watch(look(frame=1200 + frame))
        self.assertEqual([(key, tile) for key, tile, _ in blocked], [("0:3", (-7, 10))])
        self.assertIn(f"someone stood in the way {PERSON_BLOCK_HITS} times", blocked[0][2])
        watch(look(frame=1300))  # no one met since: nothing more
        self.assertEqual(len(blocked), 1)

    def test_blocked_places_wall_curiosity_walks_only(self):
        """`GoalRunner.pursue`: a walk that looks round carries the milestone's blocked places as walls (with the scene
        walls) and watches for someone in the way; the story's walks carry the scene walls only, and a place blocked
        during a look round never joins the scene walls."""
        from ai_player.brain.goals import Goal, GoalRunner, _PersonBlock
        mgr = manager("Catcher")
        milestone = mgr.story.milestones[8]
        mgr.memory.scene_walls[milestone.id] = {"0:3": {(5, 5)}}
        mgr.blocked_on(milestone.id, "0:3")[(-7, 10)] = "someone stood in the way"
        world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
        nav = types.SimpleNamespace(world=world, carried_scene_walls=None, scene_walls={}, stats=types.SimpleNamespace(people=0),
                                    plan=None, battle_log=[])
        hands = types.SimpleNamespace(look=lambda: look(party=[mon(9)]), watchers=[])
        runner = GoalRunner(hands, nav, mgr, types.SimpleNamespace(purpose=""), lambda line: None)
        seen = []

        def pursue(goal, milestone_, index, current):
            seen.append(({k: set(v) for k, v in nav.carried_scene_walls.items()},
                         [type(w).__name__ for w in hands.watchers]))
            nav.scene_walls = {"0:3": {(5, 5), (-7, 10), (9, 9)}}  # (9, 9): a scene wall met in this walk
            yield
            return False, "stuck: nothing left to try"

        runner._pursue = pursue  # noqa: SLF001
        drive(runner.pursue(Goal("explore", "x", via="0:3"), milestone, 8, lambda s: 8))
        self.assertEqual(seen[0], ({"0:3": {(5, 5), (-7, 10)}}, [_PersonBlock.__name__]))  # FAULT half: no wall, no watch
        self.assertEqual(hands.watchers, [])  # the watch is removed after the walk
        self.assertEqual(mgr.memory.scene_walls[milestone.id]["0:3"], {(5, 5), (9, 9)})  # the blocked place stays apart
        drive(runner.pursue(Goal("go", "x", map="ROUTE103"), milestone, 8, lambda s: 8))
        self.assertEqual(seen[1], ({"0:3": {(5, 5), (9, 9)}}, []))  # the story's walk: scene walls only

    def test_a_look_round_chooses_only_new_things_and_ends_when_none_is_left(self):
        """`look_round_intent`: a frontier, grass not walked, someone not met; never a wander among what it has seen (5.1's
        look round fell back to one), never a blocked place, never carried on from one; its own novelty window."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import CURIOUS_NOVELTY, look_round_intent
        from ai_player.brain.navigator import Target
        blocked = {(3, 3): "someone stood in the way"}
        intent = look_round_intent("Catcher", 3000, lambda seen: False, lambda key: blocked)
        self.assertEqual(intent.novelty_window, CURIOUS_NOVELTY)
        nav = types.SimpleNamespace(choosing_on_the_move=False, world=types.SimpleNamespace(current="0:3"),
                                    rng=random.Random(1), where=lambda seen: (None, (10, 10)), heading=lambda: None)
        for targets, want in (([Target("wander", (1, 1), "least visited"), Target("back", (2, 2), "the way back")], None),
                              ([Target("frontier", (3, 3), "blocked")], None),
                              ([Target("frontier", (3, 3), "blocked"), Target("grass", (4, 4), "grass")], (4, 4))):
            with mock.patch.object(goals_module, "candidates", lambda *a, targets=targets, **k: list(targets)), \
                    mock.patch.object(goals_module, "pick", lambda found, rng: found[0]):
                chosen = intent.choose(nav, look())
            self.assertEqual(chosen.tile if chosen is not None else None, want)  # FAULT half: the wander, the blocked
        self.assertIsNone(intent.carry_on(nav, look(), Target("frontier", (3, 3), "blocked")))

    def test_a_known_town_is_no_new_place(self):
        """(the review's finding 6: CH1M said "a new place, OLDALE_TOWN" after healing there twice) a map it has LEFT once
        is known, though the session's first decision did not know it and its draw was never made there."""
        from ai_player.world.memory import Transition
        mgr = manager("Catcher", quiet=False)
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN")
        seen = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
        step = mgr.story_step(seen, world, mgr.story.milestones[8])
        self.assertTrue(mgr.may_look_around(seen, world, step))  # its first stay: a new place
        world.transitions.append(Transition(900, "0:3", "9:9", "warp", "ai", (6, 16), (7, 8), "up"))  # into its centre
        self.assertFalse(mgr.may_look_around(seen, world, step))  # FAULT half: "a new place" again on coming back

    def test_the_push_watch_measures_pressing_that_brings_nothing_new(self):
        """`hands/waiting.py` PushWatch: free frames with presses and nothing new (no tile seen, no map stood on, no battle)
        make a stretch; something new ends it; a text or a scene PAUSES it (neither counts nor ends it); a battle ends it;
        a stretch with no press is no pushing; stretches of PUSH_NOTE frames or more are written to the action log."""
        from ai_player.hands.waiting import PUSH_NOTE, PushWatch
        state = {"presses": 0, "novelty": (100, 3)}
        notes = []
        watch = PushWatch(lambda: state["presses"], lambda *a: notes.append(a), lambda: state["novelty"])
        free = look(ch1_through("ch1_lab"))
        text = screen_look(waits=True, text="Hiya! Are you maybe… A rookie TRAINER?")
        battle = replace(free, screen=replace(free.screen, in_battle=True, game_state="BATTLE"))
        frame = 0
        for _ in range(100):  # 800 free frames, pressing: nothing new
            frame += 8
            state["presses"] += 1
            watch(replace(free, frame=frame))
        for _ in range(50):  # 400 frames of the same text: a pause, not more pushing and not the end
            frame += 8
            watch(replace(text, frame=frame))
        for _ in range(10):
            frame += 8
            state["presses"] += 1
            watch(replace(free, frame=frame))
        state["novelty"] = (101, 3)  # a new tile: the stretch is over
        frame += 8
        watch(replace(free, frame=frame))
        self.assertEqual(watch.longest["frames"], 792 + 72)  # FAULT half (no pause): the text's 400 frames counted
        closed = [note for note in notes if not note[3].get("open")]
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0][0], "push")
        self.assertGreaterEqual(closed[0][3]["frames"], PUSH_NOTE)
        self.assertEqual([note[3]["frames"] for note in notes if note[3].get("open")], [600])  # told while it went on
        for _ in range(10):  # a short stretch, then a battle ends it
            frame += 8
            state["presses"] += 1
            watch(replace(free, frame=frame))
        watch(replace(battle, frame=frame + 8))
        self.assertEqual(watch.stretches, 2)
        for _ in range(200):  # standing free with NO press: not pushing (the stall property's business)
            frame += 8
            watch(replace(free, frame=frame))
        watch.wind_up()
        self.assertEqual(watch.stretches, 2)
        self.assertEqual(watch.push_report()["longest"], 864)

    def test_the_push_watch_tells_a_stretch_that_is_still_going_on(self):
        """(step52dev3: the BLOCKED control pushed for 136,370-244,940 free frames by the game's second path while the AI's
        record said 0-1,758: a run its frame budget cut off never ENDED its last stretch, and nothing of it was written)
        an OPEN stretch is written each time it grows by PUSH_NOTE frames; the graders read it (`rate_step5.push_ai`)."""
        from ai_player.gates.rate_step5 import push_ai
        from ai_player.hands.waiting import PUSH_NOTE, PushWatch
        state = {"presses": 0}
        notes = []
        watch = PushWatch(lambda: state["presses"], lambda *a: notes.append(a), lambda: (100, 3))
        free = look(ch1_through("ch1_lab"))
        for frame in range(0, 2 * PUSH_NOTE + 100, 10):  # pushing on, never ended (the run is cut off here)
            state["presses"] += 1
            watch(replace(free, frame=frame))
        told = [note[3]["frames"] for note in notes if note[0] == "push"]
        self.assertEqual(told, [PUSH_NOTE, 2 * PUSH_NOTE])  # FAULT half: nothing, the stretch never ended
        records = [{"decision": "push", "extra": note[3]} for note in notes]
        self.assertEqual(push_ai(records), 2 * PUSH_NOTE)


class ProductiveWiringTests(unittest.TestCase):
    """(build step 5.2) Each new rule is ASKED where it acts (CLAUDE.md lessons PF-2: a mutant deletes its CALL, not only its
    body): every curiosity draw raised by boredom, the walk's break stop under the row cap, "some more" past a blocked
    frontier, the explore goal's look round, the blocked place made a wall at once and kept, someone in the way blocked
    through `pursue`, the push watch's last stretch, the play loop's push report, the play brain's entry, the walk back to
    a ball through `pursue`, and the goal manager's report of its frames."""

    def bored(self, personality: str = "Story", since: int | None = None) -> GoalManager:
        return SecondRoundTests().bored_manager(personality, since)

    def test_boredom_raises_every_curiosity_draw(self):
        """A draw at 0.85 passes a bored Story player's catch (its own 0.3), chat (0.18) and detour (0.35), not a fresh
        one's: each draw asks `curious_odds` (FAULT halves: a draw at its base)."""
        def route102(mgr):  # a catching roam's draw: grass not walked, balls in hand, two species owned
            mgr.rng = _Draws(0.85)
            world = world_with("OLDALE_TOWN", "ROUTE102", current="ROUTE102", grass=True)
            seen = look({**ch1_through("ch2_oldale"), "VISITED_OLDALE_TOWN": 1}, party=[mon(9)], balls=5, const="ROUTE102",
                        map_number=2)
            seen = replace(seen, progress=replace(seen.progress, dex_owned=2))
            mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()
            index, milestone = mgr.milestone(seen, visited_in(world))
            return mgr.next_goal(seen, world, milestone, index)

        self.assertEqual(route102(self.bored()).kind, "catch")
        self.assertNotEqual(route102(self.bored(since=0)).kind, "catch")

        def chat(mgr):
            mgr.rng = _Draws(0.85)
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN",
                               heard={"Oh, MAY went out to ROUTE 103 just a little while ago."})
            mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
            mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()
            seen = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN",
                        objects=[person(11, 10, gfx=1, local_id=5)])
            index, milestone = mgr.milestone(seen, visited_in(world))
            return mgr.next_goal(seen, world, milestone, index)

        self.assertEqual(chat(self.bored()).kind, "chat")
        self.assertNotEqual(chat(self.bored(since=0)).kind, "chat")
        detour = SecondRoundTests()

        def walk(mgr):
            mgr.memory.looked = _Everything()  # no look-around draw: the walk's detour draw is next
            return detour.oldale(mgr, 0.85, frontier=False)

        self.assertEqual(walk(self.bored()).kind, "detour")
        self.assertEqual(walk(self.bored(since=0)).kind, "go")

    def test_no_break_stop_after_two_curiosity_goals_in_a_row(self):
        from ai_player.brain.goals import BREAK_STOP, CURIOUS_ROW_MAX, Goal, GoalRunner
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="ROUTE101")
        arrive = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN", map_number=3)
        stopped = []

        def run(intent, why):
            world._last.key = "0:3"  # noqa: SLF001
            stopped.append(intent.done(arrive))
            yield
            return "done: travel" if stopped[-1] else "budget: ran out"

        mgr = self.bored()
        mgr.rng = _Draws(0.0)
        mgr.memory.looked = _Everything()
        mgr.memory.curious_row = CURIOUS_ROW_MAX
        runner = GoalRunner(types.SimpleNamespace(look=lambda: arrive), types.SimpleNamespace(world=world, run=run,
                                                                                               battle_log=[]),
                            mgr, types.SimpleNamespace(purpose=""), lambda line: None)
        runner._travel = lambda target, why, budget, done: run(types.SimpleNamespace(done=done), why)  # noqa: SLF001
        ok, outcome = drive(runner.pursue(Goal("go", "to ROUTE 103", map="ROUTE103"), mgr.story.milestones[8], 8,
                                          lambda seen: 8))
        self.assertEqual(stopped, [False])  # FAULT half: a third curiosity stop
        self.assertNotIn(BREAK_STOP, outcome)

    def test_no_look_round_some_more_past_a_blocked_frontier(self):
        """The only frontier left is behind a place curiosity found blocked: nothing left to see that it can walk to."""
        helper = SecondRoundTests()
        mgr = self.bored()
        mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()
        blocked = mgr.blocked_on("ch1_rival_route103", "0:3")
        for x in range(6, 15):  # every border tile of the seen patch round the player
            for y in range(6, 15):
                if x in (6, 14) or y in (6, 14):
                    blocked[(x, y)] = "someone stood in the way"
        self.assertEqual(helper.oldale(mgr, 0.0).kind, "go")  # FAULT half: "some more" at a blocked frontier

    def test_an_explore_goal_looks_round_with_the_look_round_intent(self):
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import CURIOUS_NOVELTY, Goal, GoalRunner
        from ai_player.brain.navigator import Target
        mgr = manager("Catcher")
        mgr.blocked_on(mgr.story.milestones[8].id, "0:1")[(3, 3)] = "someone stood in the way"
        intents = []

        def run(intent, why):
            intents.append(intent)
            yield
            return "stuck: nothing left to try on OLDALE_TOWN"

        world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
        nav = types.SimpleNamespace(world=world, run=run, battle_log=[], choosing_on_the_move=False, rng=random.Random(1),
                                    where=lambda seen: (None, (10, 10)), heading=lambda: None)
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look()), nav, mgr, types.SimpleNamespace(purpose=""),
                            lambda line: None)
        ok, outcome = drive(runner.pursue(Goal("explore", "a new place", steps=3000, via="0:1"), mgr.story.milestones[8], 8,
                                          lambda seen: 8))
        self.assertTrue(ok, outcome)  # nothing more to look at: a look round that ended as it should
        self.assertEqual((intents[0].name, intents[0].novelty_window), ("look round", CURIOUS_NOVELTY))  # FAULT: 5.1's
        targets = [Target("frontier", (3, 3), "blocked"), Target("grass", (4, 4), "grass")]
        with mock.patch.object(goals_module, "candidates", lambda *a, **k: list(targets)), \
                mock.patch.object(goals_module, "pick", lambda found, rng: found[0]):
            self.assertEqual(intents[0].choose(nav, look()).tile, (4, 4))  # the milestone's blocked place is not chosen
        ball = person(12, 10, gfx=59, local_id=1, kind="item_ball")
        self.assertTrue(intents[0].done(look(const="OLDALE_TOWN", objects=[ball])))  # the walk's own stops: an item ball

    def test_a_look_around_walk_stops_for_an_item_ball(self):
        from ai_player.brain.goals import Goal, GoalRunner
        mgr = manager("Catcher")
        intents = []

        def run(intent, why):
            intents.append(intent)
            yield
            return "budget: ran out"

        world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
        nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look()), nav, mgr, types.SimpleNamespace(purpose=""),
                            lambda line: None)
        drive(runner.pursue(Goal("look_around", "every step done", key="look_around"), mgr.story.milestones[8], 8,
                            lambda seen: 8))
        ball = person(12, 10, gfx=59, local_id=1, kind="item_ball")
        self.assertTrue(intents[0].done(look(const="OLDALE_TOWN", objects=[ball])))  # FAULT half: walks past the ball
        self.assertFalse(intents[0].done(look(const="OLDALE_TOWN")))

    def test_the_play_loop_ends_when_its_target_is_reached(self):
        loop = PlayLoopTests()
        past = look(ch1_through("ch2_oldale"), party=[mon(9)], const="ROUTE101")
        reason, hands, pursued, _, report = loop.run_loop(past, budget=2000)
        self.assertEqual(reason, "done: ch1_pokedex reached")  # FAULT half: it plays on past its target
        self.assertEqual(pursued, [])

    def test_a_blocked_place_is_a_wall_at_once_and_kept(self):
        from ai_player.brain.goals import GoalRunner
        mgr = manager("Catcher")
        told = []
        world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
        nav = types.SimpleNamespace(world=world, scene_walls={})
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look()), nav, mgr, types.SimpleNamespace(purpose=""),
                            told.append)
        runner._blocked(mgr.story.milestones[8], "0:1", (-7, 10), "someone stood in the way 3 times")  # noqa: SLF001
        self.assertEqual(nav.scene_walls, {"0:1": {(-7, 10)}})  # FAULT half: walked into again in this walk
        self.assertIn((-7, 10), mgr.blocked_on(mgr.story.milestones[8].id, "0:1"))  # FAULT half: tried by the next goal
        self.assertTrue(any("given up, and kept from curiosity" in line for line in told))

    def test_someone_in_the_way_is_blocked_through_pursue(self):
        """`pursue` installs the watch and hands it `_blocked`: three people in the way of one place, nothing new, inside a
        look round, and the place is blocked for the milestone."""
        from ai_player.brain.goals import PERSON_BLOCK_HITS, Goal, GoalRunner
        from ai_player.brain.navigator import Plan
        mgr = manager("Catcher")
        world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
        nav = types.SimpleNamespace(world=world, carried_scene_walls=None, scene_walls={},
                                    stats=types.SimpleNamespace(people=0), battle_log=[],
                                    plan=Plan("frontier:(-7, 10)", "0:1", (2, 10), ["left"] * 9, True))
        hands = types.SimpleNamespace(look=lambda: look(party=[mon(9)]), watchers=[])
        runner = GoalRunner(hands, nav, mgr, types.SimpleNamespace(purpose=""), lambda line: None)

        def pursue(goal, milestone_, index, current):
            for frame in range(PERSON_BLOCK_HITS):
                nav.stats.people += 1
                for watcher in list(hands.watchers):
                    watcher(look(frame=2000 + frame))
            yield
            return False, "stuck: nothing new"

        runner._pursue = pursue  # noqa: SLF001
        drive(runner.pursue(Goal("explore", "x", via="0:1"), mgr.story.milestones[8], 8, lambda s: 8))
        self.assertIn((-7, 10), mgr.blocked_on(mgr.story.milestones[8].id, "0:1"))  # FAULT half: never blocked

    def test_the_push_watch_closes_its_last_stretch_when_wound_up(self):
        from ai_player.hands.waiting import PushWatch
        state = {"presses": 0}
        watch = PushWatch(lambda: state["presses"], lambda *a: None, lambda: (1, 1))
        free = look(ch1_through("ch1_lab"))
        for frame in range(8, 800, 8):
            state["presses"] += 1
            watch(replace(free, frame=frame))
        self.assertIsNone(watch.longest)  # open: nothing new ended it
        watch.wind_up()
        self.assertEqual(watch.push_report()["longest"], 784)  # FAULT half: the run's last stretch lost

    def test_the_play_loop_reports_pressing_that_brought_nothing(self):
        """The REAL play loop installs the push watch and reports its longest stretch at the end: goals that press and
        bring nothing new make one stretch of the whole run."""
        loop = PlayLoopTests()
        free = loop.free_screen()
        reason, hands, pursued, _, report = loop.run_loop(lambda frames: replace(free, frame=frames), budget=20_000,
                                                          effect=lambda goal, world, runner: (False, "nothing"))
        self.assertIsNotNone(report["pushes"])  # FAULT half: no watch, or no report
        self.assertGreater(report["pushes"]["longest"], 0)
        end = next(extra for decision, _, _, extra in hands.notes if decision == "end")
        self.assertEqual(end["pushes"], report["pushes"])

    def test_the_play_brain_is_played_through_its_skill(self):
        from ai_player.mode import HandsBrain
        brain = HandsBrain.__new__(HandsBrain)
        brain.options = types.SimpleNamespace(brain="play", intent_frames=1000)
        brain.settings = types.SimpleNamespace(frames=10_000)
        calls = []

        def play(hands, personality):
            calls.append(personality)
            yield
            return "play: done"

        brain._play = play  # noqa: SLF001
        brain.world = None
        result = drive(brain._skill(types.SimpleNamespace(), "Story"))  # noqa: SLF001
        self.assertEqual((result, calls), ("play: done", ["Story"]))  # FAULT half: the play brain never runs

    def test_a_ball_seen_earlier_is_picked_up_through_pursue(self):
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import Goal, GoalRunner
        mgr = manager("Catcher")
        world = world_with("ROUTE102", current="ROUTE102")
        memory = world.maps["0:1"]
        for x in range(15, 25):
            for y in range(0, 10):
                memory.tiles[(x, y)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (20, 5))
        ball = person(20, 5, gfx=59, local_id=4, kind="item_ball")
        picked = []

        def pick_up(hands, nav, target, why):
            picked.append((target.x, target.y))
            yield
            return "picked up: POTION"

        def go_to(tile, why, budget):
            yield
            return "done"

        nav = types.SimpleNamespace(world=world, where=lambda seen: (memory, (16, 5)), go_to=go_to, battle_log=[])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(objects=[ball], const="ROUTE102")), nav, mgr,
                            types.SimpleNamespace(purpose=""), lambda line: None)
        with mock.patch.object(goals_module, "pick_up", pick_up):
            ok, outcome = drive(runner.pursue(Goal("pick_up", "back to it", tile=(20, 5)), mgr.story.milestones[11], 11,
                                              lambda seen: 11))
        self.assertEqual(picked, [(20, 5)])  # FAULT half: walked back, never picked up
        self.assertTrue(ok, outcome)

    def test_the_play_loop_judges_a_look_round_by_its_length(self):
        """The REAL play loop hands the yield the goal's frames: two looks round of the stand-in's 1,000 frames, 30 new
        tiles (productive) and 9 (8 or more, but under `YIELD_TILE_RATE` per 1,000 frames: NOT)."""
        from ai_player import mode as mode_module
        from ai_player.brain.goals import Goal
        scripted = ["explore", "explore"]
        shown = [30, 9]

        class Scripted(mode_module.GoalManager):
            def next_goal(self, look_, world, milestone, index):
                if scripted:
                    kind = scripted.pop(0)
                    self.memory.decisions += 1
                    return Goal(kind, f"scripted {kind}", milestone.id, key=f"{kind}:{world.current}", via=world.current)
                return super().next_goal(look_, world, milestone, index)

        def effect(goal, world, runner):
            if goal.kind == "explore" and shown:
                world.tiles_learned += shown.pop(0)
                return True, "budget: 3000 frames ran out"
            return None

        loop = PlayLoopTests()
        with mock.patch.object(mode_module, "GoalManager", Scripted):
            _, hands, pursued, _, _ = loop.run_loop(screen=loop.free_screen(), budget=10_000, effect=effect)
        self.assertEqual(pursued[:2], ["explore", "explore"])
        ends = [extra for decision, _, _, extra in hands.notes if decision == "goal_end"][:2]
        self.assertEqual([e["yield"]["tiles"] for e in ends], [30, 9])
        self.assertEqual([e["yield"]["productive"] for e in ends], [True, False])  # FAULT half: 9 tiles in 1,000 frames

    def test_the_play_loop_installs_its_battle_clock(self):
        """The REAL play loop tells its battle clock every look (`hands.watchers`)."""
        from ai_player.hands.waiting import BattleClock
        loop = PlayLoopTests()
        _, hands, _, _, _ = loop.run_loop(screen=loop.free_screen(), budget=3_000)
        self.assertEqual(sum(isinstance(w, BattleClock) for w in hands.watchers), 1)  # FAULT half: never told a look

    def test_the_play_loop_takes_the_battles_out_of_a_look_rounds_time(self):
        """The REAL play loop reads its battle clock before and after each goal: three looks round of the stand-in's 1,000
        frames, the clock saying 300 battle frames in the second and 600 in the third; 9 new tiles each but the first's 30:
        the second walked 700 (NOT productive), the third 400 (productive)."""
        from ai_player import mode as mode_module
        from ai_player.brain.goals import Goal
        scripted = ["explore", "explore", "explore"]
        shown = [30, 9, 9]
        readings = [0, 0, 0, 300, 300, 900]

        class Clock:  # stands in for `hands/waiting.py` BattleClock: its reading at each look of the play loop
            def __call__(self, look_) -> None:
                pass

            @property
            def battle_frames(self) -> int:
                return readings.pop(0) if readings else 900

        class Scripted(mode_module.GoalManager):
            def next_goal(self, look_, world, milestone, index):
                if scripted:
                    kind = scripted.pop(0)
                    self.memory.decisions += 1
                    return Goal(kind, f"scripted {kind}", milestone.id, key=f"{kind}:{world.current}", via=world.current)
                return super().next_goal(look_, world, milestone, index)

        def effect(goal, world, runner):
            if goal.kind == "explore" and shown:
                world.tiles_learned += shown.pop(0)
                return True, "budget: 3000 frames ran out"
            return None

        loop = PlayLoopTests()
        with mock.patch.object(mode_module, "GoalManager", Scripted), mock.patch.object(mode_module, "BattleClock", Clock):
            _, hands, pursued, _, _ = loop.run_loop(screen=loop.free_screen(), budget=10_000, effect=effect)
        self.assertEqual(pursued[:3], ["explore", "explore", "explore"])
        ends = [extra for decision, _, _, extra in hands.notes if decision == "goal_end"][:3]
        self.assertEqual([e["yield"]["battle_frames"] for e in ends], [0, 300, 600])
        # FAULT halves: the before-reading lost (the second walked 400: productive), the after-reading lost (the third
        # walked 1,000: not)
        self.assertEqual([e["yield"]["productive"] for e in ends], [True, False, True])

    def test_a_goal_starts_from_its_milestones_walls_not_the_last_intents(self):
        """(found by the development sweep step52dev2, seed 1010, by the new pushing property: 114,121 frames of pressing with
        nothing new) PROF. BIRCH's "Don't leave me like this!" walls on ROUTE 101, left in the navigator by the last intent
        of his milestone, were merged into the RIVAL's milestone after a goal that ran no intent (a talk at hand), and every
        walk north from LITTLEROOT planned round them, back across the edge. Every goal starts from its own milestone's."""
        from ai_player.brain.goals import Goal, GoalRunner
        mgr = manager("Catcher")
        milestone = mgr.story.milestones[8]
        world = world_with("ROUTE101", current="ROUTE101")
        nav = types.SimpleNamespace(world=world, carried_scene_walls=None, scene_walls={"0:1": {(10, 18), (11, 18)}},
                                    battle_log=[])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(9)])), nav, mgr,
                            types.SimpleNamespace(purpose=""), lambda line: None)

        def pursue(goal, milestone_, index, current):  # a goal that runs no intent: someone at hand talked to
            yield
            return True, "talked"

        runner._pursue = pursue  # noqa: SLF001
        drive(runner.pursue(Goal("chat", "x"), milestone, 8, lambda s: 8))
        self.assertEqual(mgr.memory.scene_walls[milestone.id], {})  # FAULT half: the earlier milestone's walls carried

    def test_the_beeline_still_picks_up_an_item_ball(self):
        """The beeline control keeps item balls, as 5.1's did: the rival's POKé BALL is how its chapter 1 goes on (the
        development sweep step52dev2's beeline, with none, stuck in 12 runs of 12)."""
        mgr = manager("Story", errands_off=True)
        world = world_with("LITTLEROOT_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F", "LITTLEROOT_TOWN_MAYS_HOUSE_2F",
                           current="LITTLEROOT_TOWN_MAYS_HOUSE_2F", heard={"Our daughter is upstairs, I think.",
                                                                          "He lives right next door, so you should"})
        ball = person(12, 10, gfx=59, local_id=1, kind="item_ball")
        observation = look(ch1_through("ch1_rival_house"), party=[], objects=[ball], const="LITTLEROOT_TOWN_MAYS_HOUSE_2F")
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertEqual(mgr.next_goal(observation, world, milestone, index).kind, "pick_up")  # FAULT half: stuck

    def test_the_goal_managers_report_of_its_frames(self):
        """`spent` (a REPORT since build step 5.2: nothing decides by it): needs and curiosity are errands, a curiosity goal
        the story moved on in is the story's, nothing counts before the first Pokemon."""
        from ai_player.brain.goals import Goal
        mgr = manager("Story")
        mgr.memory.decided_with_party = True
        mgr.spent(Goal("heal", "x"), 1000)
        mgr.spent(Goal("pick_up", "x"), 500, story_moved=True)  # the rival's POKé BALL: the story's
        mgr.spent(Goal("go", "x"), 700)
        mgr.spent(Goal("explore", "x"), 300)
        self.assertEqual(mgr.memory.spent, {"story": 1200, "errand": 1300, "curious": 300})
        mgr.memory.decided_with_party = False
        mgr.spent(Goal("explore", "x"), 999)
        self.assertEqual(mgr.memory.spent["errand"], 1300)  # before its first Pokemon nothing counts


class GraderYieldTests(unittest.TestCase):
    """(build step 5.2) The sweep's grader of productive curiosity, unit by unit: the intent mix by yield, the game's yield
    of a span, the detours' truth, the streaks, the pushing by both paths, the BLOCKED arm's reach, a known place called new
    by the game's stays, the verdicts with their controls; and the game-side recorder of places."""

    def test_the_intent_mix_counts_curiosity_that_brought_nothing_as_idle(self):
        from ai_player.gates.rate_step5 import intent_mix
        records = [{"decision": "goal", "action": "go", "frame": 0}, {"decision": "goal_end", "action": "go", "frame": 1000},
                   {"decision": "goal", "action": "explore", "frame": 1000},
                   {"decision": "goal_end", "action": "explore", "frame": 4000},
                   {"decision": "goal", "action": "chat", "frame": 4000},
                   {"decision": "goal_end", "action": "chat", "frame": 4500}, {"decision": "watch", "frame": 5000}]
        honest = intent_mix(records, {1000})
        self.assertEqual((honest["idle_frames"], honest["free_frames"], honest["errand_frames"]), (3000, 500, 500))
        self.assertEqual(intent_mix(records)["free_frames"], 3500)  # FAULT half: by kind, the loaf counted

    def test_the_game_says_what_a_span_brought(self):
        from ai_player.gates.rate_step5 import YIELD_TILES, game_yield
        places = {"new_tiles": [[100, 3], [150, YIELD_TILES]], "stays": [[0, "0:9"], [300, "0:10"], [500, "0:9"]],
                  "texts": [[50, 90, True], [420, 460, True], [900, 940, False], [960, 990]]}
        story = {"captures": [[0, 1], [700, 2]], "item_flags": [[0, 0], [800, 1]]}
        self.assertTrue(game_yield(places, story, 120, 200)["productive"])  # 8 tiles
        self.assertFalse(game_yield(places, story, 60, 110)["productive"])  # 3 tiles, a text begun before it
        self.assertTrue(game_yield(places, story, 250, 350)["maps"])  # 0:10 first stood on
        self.assertFalse(game_yield(places, story, 480, 520)["maps"])  # 0:9 again: no new map
        self.assertTrue(game_yield(places, story, 400, 430)["talked"])
        # (the verifier's round: the nurse's welcome right after a heal, a scripted stop met again) a message the game had
        # shown before is no talk (FAULT half: any text begun in the span), nor a record that does not say
        self.assertFalse(game_yield(places, story, 880, 950)["talked"])
        self.assertFalse(game_yield(places, story, 950, 1000)["talked"])
        self.assertEqual(game_yield(places, story, 650, 750)["caught"], 1)
        self.assertEqual(game_yield(places, story, 790, 820)["items"], 1)
        self.assertFalse(game_yield(places, story, 1000, 1100)["productive"])
        self.assertEqual(YIELD_TILES, 8)

    def test_the_game_judges_a_look_round_by_its_length(self):
        """(step52dev2: the LOAF control was productive in 80 % of its curiosity frames by the 8 tiles alone) a look round or
        a detour's span must show the graders' `YIELD_TILE_RATE` new tiles per 1,000 frames; another kind does not; and the
        grader hands each span its kind."""
        from ai_player.gates.rate_step5 import YIELD_TILE_RATE, curiosity_rows, game_yield
        places = {"new_tiles": [[1500, 9]]}
        self.assertEqual(YIELD_TILE_RATE, 20)
        self.assertFalse(game_yield(places, {}, 1000, 4000, "explore")["productive"])  # FAULT half: 9 tiles in 3,000
        self.assertTrue(game_yield(places, {}, 1400, 1700, "explore")["productive"])
        self.assertTrue(game_yield(places, {}, 1000, 4000, "catch")["productive"])
        # the span's own time: the game's battles in it are not (2,560 of its 3,000 frames: it walked 440)
        fought = game_yield({**places, "battles": [[1050, 3600]], "every": 10}, {}, 1000, 4000, "explore")
        self.assertEqual(fought["walking"], 440)
        self.assertTrue(fought["productive"])  # FAULT half: the battles counted as its time
        records = [{"decision": "goal", "action": "explore", "frame": 1000},
                   {"decision": "goal_end", "action": "explore", "frame": 4000, "reason": "budget: ran out",
                    "extra": {"yield": {"productive": True}}}, {"decision": "watch", "frame": 4000}]
        rows = curiosity_rows(records, {"places": places}, 0)
        self.assertEqual([r["game"] for r in rows], [False])  # FAULT half: judged without its kind

    def test_loafing_is_the_own_time_of_curiosity_that_brought_nothing(self):
        """(step52dev4: catching roams that met only known POKéMON were 80-87 % battles) `loafing_frames`: the curiosity
        goals the game says brought nothing, counted by their time OUTSIDE the game's battles (`curiosity_rows` walking)."""
        from ai_player.gates.rate_step5 import curiosity_rows, loafing_frames
        records = [{"decision": "goal", "action": "catch", "frame": 1000},
                   {"decision": "goal_end", "action": "catch", "frame": 9000, "reason": "roam: the hunt brought nothing new",
                    "extra": {"yield": {"productive": False, "walking": 1500}}}, {"decision": "watch", "frame": 9000}]
        places = {"battles": [[2000, 4990], [5000, 7990]], "every": 10}  # 6,000 of its 8,000 frames in two battles
        rows = curiosity_rows(records, {"places": places}, 0)
        self.assertEqual((rows[0]["walking"], rows[0]["walking_ai"]), (2000, 1500))
        self.assertEqual(loafing_frames(rows), 2000)  # FAULT half: 8,000, the battles counted as loafing

    def test_the_grader_checks_a_detours_word_against_the_game(self):
        from ai_player.gates.rate_step5 import curiosity_rows
        records = [{"decision": "goal", "action": "detour", "frame": 1000},
                   {"decision": "goal_end", "action": "detour", "frame": 1500, "reason": "reached the frontier at (5, 5)",
                    "extra": {"yield": {"productive": True, "place": ["0:9", 5, 5, "frontier"]}}},
                   {"decision": "goal", "action": "detour", "frame": 2000},
                   {"decision": "goal_end", "action": "detour", "frame": 2500, "reason": "reached the frontier at (7, 7)",
                    "extra": {"yield": {"productive": True, "place": ["0:9", 7, 7, "frontier"]}}},
                   {"decision": "watch", "frame": 3000}]
        data = {"places": {"moves": [[900, "0:9", 1, 1], [1400, "0:9", 5, 5], [2400, "0:9", 6, 7]],
                           "new_tiles": [[1200, 20], [2200, 20]]}}
        rows = curiosity_rows(records, data, 0)
        self.assertEqual([(r["said_reached"], r["game_reached"]) for r in rows], [(True, True), (True, False)])
        self.assertEqual([r["game"] for r in rows], [True, False])  # FAULT half: the AI's word believed

    def test_the_two_paths_on_the_talks_are_put_side_by_side(self):
        """(build step 5.2, THE VERIFIER'S SECOND ROUND: the README said the footprints man's chat was "counted by both
        paths" while the game's path credited all 20 and the AI's none, and no line put the two verdicts side by side)
        `curiosity_rows` keeps each path's word on a chat's talk; `step52_verdicts` reports the talks they disagree on."""
        from ai_player.gates.rate_step5 import curiosity_rows, step52_verdicts
        records = [{"decision": "goal", "action": "chat", "frame": 1000},
                   {"decision": "goal_end", "action": "chat", "frame": 1700, "reason": "talked to someone",
                    "extra": {"yield": {"productive": False, "talks": True, "talked": False}}},
                   {"decision": "goal", "action": "chat", "frame": 2000},
                   {"decision": "goal_end", "action": "chat", "frame": 2600, "reason": "talked to someone",
                    "extra": {"yield": {"productive": True, "talks": True, "talked": True}}},
                   {"decision": "watch", "frame": 3000}]
        data = {"places": {"texts": [[1100, 1300, True], [2100, 2300, True]]}}
        rows = curiosity_rows(records, data, 0)
        self.assertEqual([(r["talks_ai"], r["talked_ai"], r["talked_game"]) for r in rows],
                         [(True, False, True), (True, True, True)])
        real = {"CH1": [self.row("CH1", 1, talks_ai=2, talks_apart=[(1000, "cha", 0, 1)])], "CH2": [self.row("CH2", 1)]}
        line = check_by_id(step52_verdicts(real), "R5.TALKS_PATHS").text  # (build step 5.3, A1-4) by its id
        self.assertIn("in 1 of 2", line)
        self.assertIn("('CH1', 1, 1000, 'cha', 0, 1)", line)  # FAULT half: nothing reported apart

    def test_the_grader_finds_curiosity_streaks(self):
        from ai_player.gates.rate_step5 import curiosity_streaks
        kinds = ["go", "chat", "explore", "detour", "go", "chat", "heal", "explore"]
        records = [{"decision": "goal", "action": k, "frame": 1000 * i} for i, k in enumerate(kinds)]
        records.append({"decision": "watch", "frame": 9000})
        self.assertEqual(curiosity_streaks(records), [(1000, 3, 3000), (5000, 1, 1000), (7000, 1, 2000)])

    def test_a_save_neither_ends_nor_joins_a_grader_streak(self):
        """(R1 + R2 follow-up, spec D6; T4) The grader treats a SAVE as the AI does: transparent. FAULT (mutants V6b, V6c):
        chat, explore, SAVE, detour, chat is ONE curiosity streak of 4 (the save's frames inside its span), not two of 2;
        aside, aside, SAVE, aside is ONE aside streak of 3, not two. CONTROL: a STORY goal between still makes two
        curiosity streaks."""
        from ai_player.brain.goals import ASIDE
        from ai_player.gates.rate_step5 import aside_streaks, curiosity_streaks

        def goals(kinds):
            records = [{"decision": "goal", "action": k, "frame": 1000 * i} for i, k in enumerate(kinds)]
            return records + [{"decision": "watch", "frame": 1000 * len(kinds)}]

        self.assertEqual(curiosity_streaks(goals(["go", "chat", "explore", "save", "detour", "chat", "go"])),
                         [(1000, 4, 5000)])  # FAULT half: [(1000, 2, 2000), (4000, 2, 2000)]
        self.assertEqual(curiosity_streaks(goals(["go", "chat", "explore", "go", "detour", "chat", "go"])),
                         [(1000, 2, 2000), (4000, 2, 2000)])  # CONTROL
        aside = {"key": f"{ASIDE}go:PETALBURG_CITY"}
        records = [{"decision": "goal", "action": "go", "frame": 0, "extra": {"key": "go:PETALBURG_CITY"}},
                   {"decision": "goal", "action": "look_around", "frame": 1000, "extra": aside},
                   {"decision": "goal", "action": "look_around", "frame": 2000, "extra": aside},
                   {"decision": "goal", "action": "save", "frame": 3000, "extra": {"key": "save:a heal"}},
                   {"decision": "goal", "action": "look_around", "frame": 4000, "extra": aside},
                   {"decision": "goal", "action": "go", "frame": 5000, "extra": {"key": "go:PETALBURG_CITY"}},
                   {"decision": "watch", "frame": 6000}]
        self.assertEqual(aside_streaks(records), [("go:PETALBURG_CITY", 1000, 4000, 3)])  # FAULT half: two streaks

    def test_the_grader_reads_pushing_and_person_blocks(self):
        from ai_player.gates.rate_step5 import person_blocks, push_ai
        records = [{"decision": "push", "frame": 100, "extra": {"frames": 900}},
                   {"decision": "goal", "action": "explore", "frame": 200},
                   {"decision": "idle", "frame": 210, "reason": "someone stands in the way on the next steps toward the "
                                                               "frontier at (-7, 10): letting them pass"},
                   {"decision": "idle", "frame": 230, "reason": "someone is in the way at someone at (-6, 10): letting them"},
                   {"decision": "idle", "frame": 250, "reason": "someone stands in the way on the next steps"},
                   {"decision": "goal", "action": "go", "frame": 300},
                   {"decision": "idle", "frame": 310, "reason": "someone stands in the way on the next steps"},
                   {"decision": "end", "frame": 400, "extra": {"pushes": {"longest": 1200}}}]
        self.assertEqual(push_ai(records), 1200)
        self.assertEqual(push_ai(records[:-1]), 900)
        self.assertEqual(person_blocks(records), 3)  # the story's walk's wait is not counted

    def test_a_place_left_before_called_new_by_the_games_stays(self):
        from ai_player.gates.rate_step5 import new_place_left_before
        records = [{"decision": "goal", "action": "explore", "frame": 100, "reason": "a new place, OLDALE_TOWN: a person"},
                   {"decision": "goal", "action": "explore", "frame": 900, "reason": "a new place, OLDALE_TOWN: a person"}]
        data = {"places": {"stays": [[0, "0:16"], [50, "0:9"], [400, "0:16"], [800, "0:9"]]}}
        # (build step 5.3, A1-2/A1-4) the keys are the framework's map table (`map_keys(MAP_DATA)`), no world file
        with mock.patch("ai_player.gates.rate_step5.map_keys", lambda source=None: {"OLDALE_TOWN": "0:9"}):
            self.assertEqual(new_place_left_before(records, data, 0), [(900, "OLDALE_TOWN")])  # its second stay

    def row(self, plan, seed, **more):
        base = {"plan": plan, "seed": seed, "personality": "Story", "curious": [], "curious_frames": 4000,
                "productive_frames": 3600, "loaf_frames": 400, "seeing_frames": 3000, "seeing_productive": 2600,
                "yield_agree": 0, "detours": [(1, ["0:9", 1, 1, "f"], 1, 1)],
                "streak_goals": 2, "streak_frames": 3000, "push_ai": 900, "push_game": 950, "push_game_at": [0, 0],
                "person_blocks": 0, "left_called_new": [], "ask_nothing_said": 0, "places_samples": 100,
                # (build step 5.3, A1-4) the draws #61 judged: its sample count (none judged is VACUOUS)
                "left_judged": 1, "left_skipped": 0}
        return {**base, **more}

    def test_the_step52_verdicts_and_their_controls(self):
        from ai_player.gates.rate_step5 import BOUNDS, step52_verdicts
        real = {"CH1": [self.row("CH1", s) for s in (1, 2)], "CH2": [self.row("CH2", s) for s in (1, 2)]}
        # (build step 5.3, the re-sourcing fix round, items 8 and 9) LOAF fails R5.NO_LOAFING by the GAME's push (both paths
        # over the loafing bound, so they agree); its AI-windowed loafing and yield are no longer read
        loafed = {"push_ai": BOUNDS["LOAF_FRAMES_MAX"] + 50, "push_game": BOUNDS["LOAF_FRAMES_MAX"] + 60}
        controls = {"LOAF": [self.row("LOAF", s, loaf_frames=BOUNDS["LOAF_FRAMES_MAX"] + 1, productive_frames=100,
                                      seeing_productive=600, **loafed) for s in (1, 2)],
                    "GREEDY": [self.row("GREEDY", s, streak_goals=BOUNDS["SPACING_ROW_MAX"] + 2) for s in (1, 2)],
                    "BLOCKED": [self.row("BLOCKED", 1, person_blocks=5, push_ai=BOUNDS["PUSH_MAX"] + 9,
                                         push_game=BOUNDS["PUSH_MAX"] + 9), self.row("BLOCKED", 2)]}

        def check(rows, check_id: str) -> bool:
            # (build step 5.3, A1-4) the check by its ID, its OWN outcome (PASS), whatever its kind
            return check_by_id(step52_verdicts(rows), check_id).status == "PASS"

        results = step52_verdicts({**real, **controls})
        self.assertTrue(all(c.status == "PASS" for c in results), [c.text[:120] for c in results if c.status != "PASS"])
        # (re-sourcing fix round, item 9) REPLACES "CH1 loaf_frames=7500 FAILS R5.NO_LOAFING" (the AI's windows): FAULT, the
        # GAME's push at the bound fails it; CONTROL, CH2 1311's shape (AI-windowed 4,430 over, game push 760) PASSES
        self.assertFalse(check({**real, "CH1": [self.row("CH1", 1, push_ai=BOUNDS["LOAF_FRAMES_MAX"],
                                                         push_game=BOUNDS["LOAF_FRAMES_MAX"])], **controls}, "R5.NO_LOAFING"))
        self.assertTrue(check({**real, "CH2": [self.row("CH2", 1311, loaf_frames=4430, push_ai=760, push_game=760)],
                               **controls}, "R5.NO_LOAFING"))
        self.assertFalse(check({**real, **controls, "LOAF": [self.row("LOAF", 1)]}, "R5.LOAF"))  # a control that holds
        self.assertFalse(check({**real, "CH2": [self.row("CH2", 1, streak_goals=6)], **controls}, "R5.SPACED"))
        self.assertFalse(check({**real, "CH1": [self.row("CH1", 1, detours=[(1, ["0:9", 1, 1, "f"], 1, 0)])], **controls},
                               "R5.DETOUR_WORD"))
        # (re-sourcing fix round, item 8) REPLACES "AI at the bound, game 10 FAILS R5.PUSHING": PUSHING reads the GAME alone,
        # so that row PASSES it and FAILS the HONESTY agreement (far from the bound: a real split); the game at the bound
        # FAILS PUSHING (FAULT)
        pushed = {**real, "CH1": [self.row("CH1", 1, push_ai=BOUNDS["PUSH_MAX"], push_game=10)], **controls}
        self.assertTrue(check(pushed, "R5.PUSHING"))
        self.assertFalse(check(pushed, "R5.PUSH_PATHS_AGREE"))
        game_pushed = {**real, "CH1": [self.row("CH1", 1, push_ai=BOUNDS["PUSH_MAX"], push_game=BOUNDS["PUSH_MAX"])],
                       **controls}
        self.assertFalse(check(game_pushed, "R5.PUSHING"))
        self.assertTrue(check(game_pushed, "R5.PUSH_PATHS_AGREE"))
        self.assertFalse(check({**real, **controls, "BLOCKED": [self.row("BLOCKED", 1)]}, "R5.BLOCKED"))  # never reached
        # (re-sourcing fix round, item 8) the arm is graded on the GAME's push alone: met nobody (the reach, now the
        # DIAGNOSTIC R5.BLOCKED_REACH) but over by the game PASSES; over by the AI's record alone FAILS
        self.assertTrue(check({**real, **controls, "BLOCKED": [self.row("BLOCKED", 1, push_game=BOUNDS["PUSH_MAX"] + 9)]},
                              "R5.BLOCKED"))
        self.assertFalse(check({**real, **controls, "BLOCKED": [self.row("BLOCKED", 1, person_blocks=5,
                                                                         push_ai=BOUNDS["PUSH_MAX"] + 9)]}, "R5.BLOCKED"))
        self.assertFalse(check({**real, "CH1": [self.row("CH1", 1, seeing_frames=4000, seeing_productive=1000)],
                                "CH2": real["CH2"], **controls}, "R5.CH1_YIELD"))
        # (build step 5.3, A1-4) #61 by the draws it JUDGED: none judged is VACUOUS (it saw nothing), not a PASS
        self.assertEqual(check_by_id(step52_verdicts({**real, **controls}), "R5.LEFT_NOT_NEW").status, "PASS")
        unjudged = {plan: [{**r, "left_judged": 0} for r in rows] for plan, rows in {**real, **controls}.items()}
        self.assertEqual(check_by_id(step52_verdicts(unjudged), "R5.LEFT_NOT_NEW").status, "VACUOUS")
        # (step52dev3) the arrival share counts the detours that CHOSE a place: one that found none walked nowhere (FAULT
        # halves: counted as failures to arrive, 3 of 7; and a run whose placed detours did not arrive passes)
        nowhere = [(1, None, 0, 0), (2, None, 0, 0), (4, None, 0, 0), (5, None, 0, 0), (3, ["0:9", 1, 1, "f"], 1, 1)]
        self.assertTrue(check({**real, "CH1": [self.row("CH1", 1, detours=nowhere)], "CH2": real["CH2"], **controls},
                              "R5.DETOURS_ARRIVE"))
        short = [(1, ["0:9", 1, 1, "f"], 0, 0), (2, ["0:9", 2, 2, "f"], 0, 0), (3, ["0:9", 3, 3, "f"], 1, 1)]
        self.assertFalse(check({**real, "CH1": [self.row("CH1", 1, detours=short)], "CH2": [self.row("CH2", 1, detours=[])],
                                **controls}, "R5.DETOURS_ARRIVE"))
        # (step52dev2) graded on the curiosity that SEES: a run whose looks loafed while its chats talked FAILS it
        self.assertFalse(check({**real, "CH1": [self.row("CH1", 1, seeing_productive=500)], "CH2": real["CH2"],
                                **controls}, "R5.CH1_YIELD"))
        # (re-sourcing fix round, item 9) REPLACES "LOAF whose looks brought something does not fail its check" (the yield
        # inside the AI's windows): LOAF whose AI-windowed loafing is over the bound but whose GAME push is under does not
        # count as failing NO_LOAFING (FAULT: R5.LOAF FAILS); one LOAF run over by the game is enough (CONTROL)
        self.assertFalse(check({**real, **controls, "LOAF": [self.row("LOAF", s, loaf_frames=BOUNDS["LOAF_FRAMES_MAX"] + 1)
                                                             for s in (1, 2)]}, "R5.LOAF"))
        self.assertTrue(check({**real, **controls, "LOAF": [self.row("LOAF", 1, **loafed), self.row("LOAF", 2)]}, "R5.LOAF"))

    def test_the_game_side_recorder_of_places(self):
        """`play_harness.PlaceRecorder` (the framework's reads stood in for by `place_now`): new tiles of the screen's
        window, a new map, a talk, and the pushing stretches: free time only, ended by something new or a battle, paused
        by a text, counted only with presses."""
        from ai_player.gates import play_harness
        samples = []
        controls = types.SimpleNamespace(presses=0)
        recorder = play_harness.PlaceRecorder(controls, every=1, pages={"Thank you for waiting."})
        shown = [["Hello, and welcome to the POKéMON CENTER."]]

        def feed(sample, presses=1):
            samples.append(sample)
            controls.presses += presses
            recorder.after_frame()

        def pages_now() -> list[str]:
            if shown[-1] is None:
                raise RuntimeError("a read between screens")
            return shown[-1]

        with mock.patch.object(play_harness, "place_now", lambda: samples[-1]), \
                mock.patch.object(play_harness, "shown_pages", pages_now):
            feed(("OVERWORLD", (0, 9, 10, 10), True, False))  # a new map: the OPENING window, 165 tiles, no goal's yield
            for _ in range(50):
                feed(("OVERWORLD", (0, 9, 10, 10), True, False))  # pressing, nothing new: 50 free frames
            for _ in range(30):
                feed(("OVERWORLD", (0, 9, 10, 10), False, True))  # a text waits: a pause, and a talk
            for _ in range(20):
                feed(("OVERWORLD", (0, 9, 10, 10), True, False))
            feed(("OVERWORLD", (0, 9, 11, 10), True, False))  # a step east: a new column of tiles ends the stretch
            feed(("BATTLE", None, False, False), presses=0)
            for _ in range(10):
                feed(("OVERWORLD", (0, 9, 11, 10), True, False), presses=0)  # free, no press: no pushing
            # (the verifier's round) the same message again, one the run it goes on from showed, a new one, an unread one,
            # (its second round) a buffer with no page, read as unread
            for message in (["Hello, and welcome to the POKéMON CENTER."], ["Thank you for waiting."],
                            ["We hope to see you again!"], None, []):
                shown.append(message)
                feed(("OVERWORLD", (0, 9, 11, 10), False, True), presses=0)
                feed(("OVERWORLD", (0, 9, 11, 10), True, False), presses=0)
        result = recorder.result()
        self.assertEqual(result["stays"], [[1, "0:9"]])
        # (the verifier's second round) FAULT half: the opening window credited to the first goal (the truck chats)
        self.assertEqual(result["new_tiles"], [[102, 11]])
        self.assertEqual(result["opening"], 165)
        # FAULT halves: every text new (the label), the earlier run's messages forgotten
        self.assertEqual(result["texts"], [[52, 81, True], [114, 114, False], [116, 116, False], [118, 118, True],
                                           [120, 120, True], [122, 122, True]])
        self.assertEqual(result["text_errors"], 2)  # the unread one and the empty one: counted, each text counted new
        self.assertEqual(result["battles"], [[103, 103]])  # (step52dev2) FAULT half: no battle recorded
        self.assertEqual(result["push"]["longest"][2], 69)  # FAULT halves: the text's 30 counted; no end at the new tiles
        self.assertEqual(result["push"]["stretches"], 1)

    #: pret/pokeemerald data/maps/OldaleTown/scripts.inc (read 2026-10-16): the footprints man's scene and his talk
    FOOTPRINTS_SCENE = ["Aaaaah! Wait! Please don't come in here.", "I just discovered the footprints of a rare POKéMON!",
                        "Wait until I finish sketching them, okay?"]

    def test_a_talk_is_new_only_with_a_page_never_shown(self):
        """(build step 5.2, THE VERIFIER'S SECOND ROUND: "PlaceRecorder compares WHOLE messages", so OLDALE's footprints
        man's talk, the last two pages of his own scene, was a new message 20 times in the graded sweep, game 1 and AI 0)
        `PlaceRecorder`: a text is NEW only when it shows a page the game never showed before in the run (or in the run it
        goes on from); a talk with one new page among old ones is new."""
        from ai_player.gates import play_harness
        samples = []
        controls = types.SimpleNamespace(presses=0)
        recorder = play_harness.PlaceRecorder(controls, every=1, pages={"Thank you for waiting."})
        shown: list = []
        scene = self.FOOTPRINTS_SCENE
        with mock.patch.object(play_harness, "place_now", lambda: samples[-1]), \
                mock.patch.object(play_harness, "shown_pages", lambda: shown[-1]):
            for pages in (scene, scene[1:], [scene[1], "I finished sketching the footprints of a rare POKéMON."],
                          ["Thank you for waiting.", scene[2]], list(reversed(scene))):
                shown.append(pages)
                samples.append(("OVERWORLD", (0, 10, 1, 11), False, True))
                recorder.after_frame()
                samples.append(("OVERWORLD", (0, 10, 1, 11), True, False))
                recorder.after_frame()
        # FAULT half (whole messages compared): the talk after the scene, a message of its own, was NEW
        self.assertEqual([text[2] for text in recorder.result()["texts"]], [True, False, True, False, False])
        self.assertEqual(recorder.result()["text_errors"], 0)

    def test_a_message_is_cut_into_pages_where_the_box_waits_for_a_press(self):
        """`play_harness.split_pages`: the bytes up to the string's end (0xFF: what lies past it is an older message's),
        cut at a page's clear (0xFB) and at a scroll (0xFA), each piece decoded; a newline (0xFE) stays inside its page; a
        control code's argument bytes are never read as a break (0xFC 0x01 0xFB: a text colour 0xFB); empty pieces are
        left out."""
        from ai_player.gates.play_harness import split_pages
        letters = {chr(ord("a") + n): 0x10 + n for n in range(26)} | {" ": 0x00, "!": 0x50}
        decoded: list[bytes] = []

        def encode(text: str) -> bytes:
            return bytes(letters[c] for c in text)

        def decode(raw: bytes) -> str:  # the framework's rules for the codes used here: 0xFE a space, 0xFC + 1 + its byte,
            decoded.append(raw)        # 0xFA and 0xFB dropped (`modules.game.decode_string`)
            out, at = "", 0
            while at < len(raw) and raw[at] != 0xFF:
                byte = raw[at]
                at += 1
                if byte == 0xFE:
                    out += " "
                elif byte == 0xFC:
                    at += 2
                elif byte in (0xFA, 0xFB):
                    continue
                else:
                    out += next(c for c, b in letters.items() if b == byte)
            return out

        raw = (encode("aaaaah!") + b"\xfe" + encode("wait") + b"\xfb" + encode("i just") + b"\xfe" + encode("found ")
               + b"\xfc\x01\xfb" + encode("them") + b"\xfa" + encode("so") + b"\xfb\xfb"
               + b"\xff" + encode("old") + b"\xfb" + encode("page") + b"\xff")
        # FAULT halves: no cut at the scroll ("i just found them so"); the colour's 0xFB read as a break ("i just found",
        # "them"); past the end read on (an extra page "page")
        self.assertEqual(split_pages(raw, decode), ["aaaaah! wait", "i just found them", "so"])
        self.assertTrue(all(piece.endswith(b"\xff") for piece in decoded))  # each piece handed on as a whole string
        self.assertEqual(split_pages(b"\xff" + encode("stale"), decode), [])  # nothing before the end: no page
        self.assertEqual(split_pages(encode("no end"), decode), ["no end"])

    def test_a_script_waits_only_while_it_runs_its_wait(self):
        """(build step 5.2, THE VERIFIER'S SECOND ROUND, its weak proof "NOHINTS 938's explore at f70318 is 0 tiles by the
        game, 50 by the AI": a diagnostic replay measured the player WALKING while the framework's read said a text waited)
        `play_harness.text_waits`: a script waits for A/B only while its context RUNS WaitForAorBPress (mode Native); the
        pointer a finished script leaves behind (mode Stopped, or Bytecode after the press) is no wait; a printer waits while
        active in state 2 or 3."""
        from ai_player.gates.play_harness import text_waits
        self.assertTrue(text_waits("Native", "WaitForAorBPress", (0, 0)))  # a sign's last wait: no printer, the script waits
        self.assertFalse(text_waits("Stopped", "WaitForAorBPress", (0, 0)))  # FAULT half: the leftover (the replay's walk)
        self.assertFalse(text_waits("Bytecode", "WaitForAorBPress", (0, 0)))  # the script went on after the press
        self.assertFalse(text_waits("Native", "IsFieldMessageBoxHidden", (0, 0)))
        self.assertTrue(text_waits("Stopped", "WaitForAorBPress", (1, 2)))  # a page waits in the printer
        self.assertTrue(text_waits("Bytecode", None, (1, 3)))
        self.assertFalse(text_waits("Stopped", None, (1, 0)))  # printing, not waiting

    def test_both_recorders_read_a_wait_by_the_harness_s_own_rule(self):
        """The overworld reads of both second paths (`waits_now`, the stall's; `place_now`, the places') CALL
        `text_waits_now`, never the framework's `is_waiting_for_input`, and `text_waits_now` calls `text_waits` (by AST:
        a mention in a docstring or a comment is no call)."""
        from ai_player.gates import play_harness
        tree = ast.parse(Path(play_harness.__file__).read_text(encoding="utf-8"))
        calls: dict[str, set] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ("waits_now", "place_now", "text_waits_now"):
                calls[node.name] = {getattr(call.func, "id", getattr(call.func, "attr", None))
                                    for call in ast.walk(node) if isinstance(call, ast.Call)}
        for name in ("waits_now", "place_now"):
            self.assertIn("text_waits_now", calls[name], name)
            self.assertNotIn("is_waiting_for_input", calls[name], name)
        self.assertIn("text_waits", calls["text_waits_now"])
        self.assertNotIn("is_waiting_for_input", calls["text_waits_now"])


class VerifierRound52Tests(unittest.TestCase):
    """(build step 5.2, THE VERIFIER'S ROUND, 2026-10-15) Its two FAILURES, each rule with its fault half and a mutant in
    `gates/revert_step5.py` (G277-G313):
      * LOAFING CREDITED AS A TALK (60 nurses re-healing a full party, 46 MART clerks, 21 times OLDALE's footprints man,
        straight after they had spoken, every one hearing nothing new, "a talk" by both paths): someone who SPOKE (straight
        ahead, at most `SPOKE_REACH` tiles, words on the overworld screen) is never chatted with, and is kept with the
        world memory; a talk is a yield only when it told something new (`goal_yield`; the game's `game_yield` by a message
        the game never showed before: `GraderYieldTests`);
      * THE NOHINTS PUSHING (20 of 20 graded runs, 31,676-62,012 frames by the AI's record: OLDALE's house door used for up
        to 98 goals in a row, each ended by the ping-pong rule, or OLDALE's edge crossed both ways "seen all of"): a warp's
        ping-pong is kept past its intent; what the navigator's reach shows no way to is out of a map's promise; a frontier
        stood on whose unseen side stays unseen is given up; a walk with NO LEAD heads for what is left anywhere it knows,
        and with nothing left anywhere it gives the run up ("out of ideas") instead of pressing for nothing."""

    NURSE_WORDS = "Hello, and welcome to the POKéMON CENTER."

    def speaking(self, objects, facing: str = "up", waits: bool = True, in_battle: bool = False,
                 text: str = NURSE_WORDS) -> Observation:
        seen = look(objects=objects, map_number=1)
        return replace(seen, player=replace(seen.player, facing=facing),
                       screen=replace(seen.screen, waits_for_button=waits, text=text if waits else None,
                                      in_battle=in_battle))

    def test_someone_who_spoke_is_remembered_and_never_chatted_with(self):
        """`GoalManager.notice`: the person straight in front of the player, at most two tiles away (the nurse across her
        counter), while words wait on the overworld screen, has SPOKEN; nobody beside it, nobody three tiles ahead, nobody
        when no words are on screen or in a battle. `_chat_person` never chooses someone who spoke."""
        from ai_player.brain.goals import SPOKE_REACH
        self.assertEqual(SPOKE_REACH, 2)
        nurse, beside, far = person(10, 8, local_id=1), person(11, 10, local_id=2), person(10, 7, local_id=3)
        mgr = manager("Catcher")
        mgr.memory.hearing = True  # a service talk or a chat is the goal (`GoalRunner.pursue`)
        mgr.notice(self.speaking([nurse, beside, far]))
        self.assertEqual(mgr.memory.spoke, {"0:1|1"})  # FAULT halves: anyone near (beside, far); one tile only (none)
        quiet = manager("Catcher")
        quiet.memory.hearing = True
        quiet.notice(self.speaking([nurse], waits=False))
        quiet.notice(self.speaking([nurse], in_battle=True))
        self.assertEqual(quiet.memory.spoke, set())
        mgr.notice(self.speaking([person(11, 10, local_id=4)], facing="right", text="Hello there!"))
        self.assertIn("0:1|4", mgr.memory.spoke)  # face to face
        # (step52vdev2: remembering a SCENE's speakers too cut the chats with new words by half, PROF. BIRCH's 18 of the
        # graded sweep among them) someone who speaks in a scene, no service talk or chat the goal, is not remembered
        scene = manager("Catcher")
        scene.notice(self.speaking([nurse], text="PROF. BIRCH: So, you're NOVA?"))
        self.assertEqual(scene.memory.spoke, set())  # FAULT half: every speaker remembered
        world = world_with("OLDALE_TOWN_POKEMON_CENTER_1F", current="OLDALE_TOWN_POKEMON_CENTER_1F")
        other = person(12, 10, local_id=5)
        for chooser, want in ((mgr, 5), (manager("Catcher"), 1)):  # FAULT half: the nurse who just healed it, chatted with
            chooser.rng = types.SimpleNamespace(random=lambda: 0.0)
            chosen = chooser._chat_person(look(objects=[nurse, other], map_number=1), world, 1000)  # noqa: SLF001
            self.assertEqual(chosen[0].local_id if chosen else None, want)

    def test_a_service_talk_or_a_chat_is_heard_and_other_goals_are_not(self):
        """`GoalRunner.pursue`: while the goal is a heal, a shop, a chat or a detour (`HEARD_KINDS`) the goal manager is
        `hearing` (its `notice` remembers who speaks); for every other goal, and after the goal, it is not."""
        from ai_player.brain.goals import HEARD_KINDS, Goal, GoalRunner
        self.assertEqual(HEARD_KINDS, ("heal", "shop", "chat", "detour"))
        mgr = manager("Catcher")
        milestone = mgr.story.milestones[8]
        nav = types.SimpleNamespace(world=world_with("OLDALE_TOWN", current="OLDALE_TOWN"), battle_log=[])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(9)])), nav, mgr,
                            types.SimpleNamespace(purpose=""), lambda line: None)
        heard: list = []

        def pursue(goal, milestone_, index, current):
            heard.append((goal.kind, mgr.memory.hearing))
            yield
            return True, "done"

        runner._pursue = pursue  # noqa: SLF001
        for kind in ("heal", "shop", "chat", "detour", "go", "talk", "explore"):
            drive(runner.pursue(Goal(kind, "x"), milestone, 8, lambda s: 8))
        self.assertEqual(heard, [("heal", True), ("shop", True), ("chat", True), ("detour", True), ("go", False),
                                 ("talk", False), ("explore", False)])  # FAULT half: never hearing (nobody remembered)
        self.assertFalse(mgr.memory.hearing)

    def test_a_scene_that_turned_a_curiosity_walk_back_once_blocks_its_tile(self):
        """(step52vdev2, CH1 seed 1209: a detour ended at the footprints man's first "Wait! Please don't come in here.", and
        the look round "some more" after it walked OLDALE for 2,003 frames toward his corner) the navigator keeps every tile
        a scene BEGAN on and turned the player back from (`scene_turned`, over all intents); `GoalRunner.pursue` blocks the
        ones a CURIOSITY walk met for curiosity in the milestone after ONE meeting; a story walk's are not."""
        from ai_player.brain.goals import Goal, GoalRunner
        from ai_player.brain.navigator import Navigator
        from ai_player.hands.pad import Hands
        world = WorldMemory()
        nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world, random.Random(1))
        world._last.key = "0:10"  # noqa: SLF001
        still = mock.Mock(last=80, last_progress=80)
        nav._scene_met("0:10|frontier:(-3, 11)", Target("frontier", (-3, 11), "x"), 93007, still, "0:10", (0, 10), (1, 10))  # noqa: SLF001
        self.assertEqual([(key, tile) for key, tile, _ in nav.scene_turned], [("0:10", (0, 10))])  # FAULT half: not kept
        nav._scene_met("0:10|frontier:(-3, 9)", Target("frontier", (-3, 9), "x"), 93500, still, "0:10", (2, 2), (2, 2))  # noqa: SLF001
        self.assertEqual(len(nav.scene_turned), 1)  # a scene that left it where it stood turned nothing back
        # (step52vdev5, NOHINTS seed 1245: the STORY's walk had met the footprints man, and a look round "some more" later
        # walked into his scene twice) a story walk's too: blocked for CURIOSITY, never one of the story's own walls
        for kind, expect in (("detour", {(0, 10)}), ("explore", {(0, 10)}), ("go", {(0, 10)})):
            mgr = manager("Catcher")
            milestone = mgr.story.milestones[9]
            stub = types.SimpleNamespace(world=world_with("OLDALE_TOWN", current="OLDALE_TOWN"), carried_scene_walls=None,
                                         scene_walls={}, battle_log=[], scene_given_up=[],
                                         scene_turned=[("0:1", (5, 5), "an earlier goal's")])

            def pursue(goal, milestone_, index, current, stub=stub):
                stub.scene_turned.append(("0:1", (0, 10), "a scene began here and turned it back (f93007)"))
                yield
                return False, "not reached: the frontier at (-3, 11) (a scene stopped the way there)"

            runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(9)])), stub, mgr,
                                types.SimpleNamespace(purpose=""), lambda line: None)
            runner._pursue = pursue  # noqa: SLF001
            drive(runner.pursue(Goal(kind, "x", via="0:1"), milestone, 9, lambda s: 9))
            self.assertEqual(set(mgr.memory.blocked.get(milestone.id, {}).get("0:1", {})), expect, kind)  # FAULT: none
            self.assertNotIn((0, 10), mgr.memory.scene_walls.get(milestone.id, {}).get("0:1", set()), kind)

    def test_a_look_round_is_over_when_it_has_seen_nothing_new_battles_or_not(self):
        """(step52vdev3, CH2 seed 1220: a look round of ROUTE 102's grass ran its 4,200 frames through 21 battles, 9 new
        tiles, each battle's experience resetting its novelty window) `GoalRunner._pursue`'s look round ends once it has
        SEEN nothing new (no tile, no map) for `CURIOUS_NOVELTY` frames, whatever else happened; and at once at a stop of
        the walk (`walk_done`: here the story moving on)."""
        from ai_player.brain.goals import CURIOUS_NOVELTY, Goal, GoalRunner
        for story_moves, want in ((False, 1500 + CURIOUS_NOVELTY), (True, 1000)):
            mgr = manager("Catcher")
            milestone = mgr.story.milestones[8]
            world = world_with("ROUTE102", current="ROUTE102")
            ended: list = []

            def run(intent, why, world=world, ended=ended):
                for frame in range(1000, 12000, 100):
                    if frame == 1500:
                        world.tiles_learned += 20  # something new seen at f1500, then nothing (battles or not)
                    if intent.done(look(frame=frame)):
                        ended.append(frame)
                        break
                    yield
                return "done: look round" if ended else "budget: ran out"

            nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
            runner = GoalRunner(types.SimpleNamespace(look=lambda: look()), nav, mgr, types.SimpleNamespace(purpose=""),
                                lambda line: None)
            drive(runner._pursue(Goal("explore", "x", milestone.id, steps=9000, via="0:1"), milestone, 8,  # noqa: SLF001
                                 (lambda seen: 9) if story_moves else (lambda seen: 8)))
            self.assertEqual(ended, [want], story_moves)  # FAULT halves: never over (the budget); the walk's stops lost

    def test_curiosity_keeps_out_of_the_corner_a_scene_turned_it_back_from(self):
        """(step52vdev5, CH2 seed 1242: PETALBURG's "Hiya! Are you maybe... A rookie TRAINER?" turned a look round back at
        (8, 10) and (8, 12), and the detour after it walked round both into the same scene at (8, 13)) `_scene_corners`: the
        tiles beside a place a SCENE blocked for curiosity (not one someone stood in the way of) are curiosity's walls too:
        a curiosity walk carries them, "some more" counts nothing past them (`left_to_see`), and the story's own walls never
        get them."""
        from ai_player.brain.goals import Goal, GoalRunner, _scene_corners
        places = {(8, 12): "a scene began here and turned it back (f296679)", (5, 5): "someone stood in the way 3 times"}
        self.assertEqual(_scene_corners(places), {(9, 12), (7, 12), (8, 13), (8, 11)})  # FAULT half: the person's too
        mgr = manager("Catcher")
        milestone = mgr.story.milestones[9]
        mgr.blocked_on(milestone.id, "0:1").update(places)
        stub = types.SimpleNamespace(world=world_with("PETALBURG_CITY", current="PETALBURG_CITY"), carried_scene_walls=None,
                                     scene_walls={}, battle_log=[], scene_given_up=[], scene_turned=[])
        carried: list = []

        def pursue(goal, milestone_, index, current):
            carried.append({key: set(tiles) for key, tiles in stub.carried_scene_walls.items()})
            yield
            return False, "budget: ran out"

        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(9)])), stub, mgr,
                            types.SimpleNamespace(purpose=""), lambda line: None)
        runner._pursue = pursue  # noqa: SLF001
        drive(runner.pursue(Goal("detour", "x", via="0:1"), milestone, 9, lambda s: 9))
        self.assertIn((8, 13), carried[0]["0:1"])  # FAULT half: the walk round into the same scene
        self.assertNotIn((8, 13), mgr.memory.scene_walls[milestone.id].get("0:1", set()))  # the story's walls: never
        # "some more" counts no frontier past the corner: a corridor at y 10, its end (10, 10) beside the unseen
        world = world_with("ROUTE102", current="ROUTE102")
        here = world.here()
        for x in range(0, 11):
            here.tiles[(x, 10)] = TileFact(x == 0, False, False, False, None, False, False, 3, "NORMAL", 0, (1, 10))
            for y in (9, 11):
                here.tiles[(x, y)] = TileFact(True, False, False, False, None, False, False, 3, "NORMAL", 0, (1, 10))
        seen = replace(look(), player=replace(look().player, x=1, y=10))
        quiet = manager("Catcher")
        self.assertIsNone(quiet.left_to_see(seen, world, milestone.id))  # the end of the corridor is left to see
        quiet.blocked_on(milestone.id, world.current)[(6, 9)] = "a scene began here and turned it back (f1)"
        self.assertEqual(quiet.left_to_see(seen, world, milestone.id), "nothing left to see here that it can walk to")

    def test_whom_it_met_is_kept_with_the_world_memory(self):
        """`WorldMemory.spoke` is written with the memory only when it holds someone (the earlier brains' snapshots are
        unchanged) and read back, so a later session (chapter 2) does not chat with chapter 1's speakers again."""
        world = WorldMemory()
        self.assertNotIn("spoke", world.to_dict())
        world.spoke.add("2:2|1")
        back = WorldMemory.from_dict(json.loads(world.snapshot()))
        self.assertEqual(back.spoke, {"2:2|1"})  # FAULT halves: not written, not read

    def test_the_play_brain_turns_the_new_rules_on(self):
        """The REAL play loop: the goal manager's `spoke` IS the world memory's set, its `notice` watches every look, and
        the navigator keeps ping-pongs past an intent (`ponged`) and marks what its reach shows no way to (`mark_cut`)."""
        from ai_player.brain.goals import GoalManager as RealManager
        seen: list = []

        def effect(goal, world, runner):
            seen.append((runner.manager.memory.spoke is world.spoke, runner.nav.ponged, runner.nav.mark_cut))
            return None

        loop = PlayLoopTests()
        _, hands, _, _, _ = loop.run_loop(screen=loop.free_screen(), budget=5000, effect=effect)
        self.assertEqual(seen[0], (True, {}, True))  # FAULT halves: a set of its own, the rules off
        self.assertTrue(any(getattr(w, "__func__", None) is RealManager.notice for w in hands.watchers))

    SPLIT_ROWS = ["#" * 10 + "D" + "#" * 19] + ["#" + "." * 8 + "#" + "." * 19 + "#" for _ in range(9)] + ["#" * 30]

    def test_what_its_reach_shows_no_way_to_is_not_left_to_see(self):
        """`Navigator.cut_off` (OLDALE_TOWN_HOUSE1's two tiles no walk from its door can get to were "2 things left to see"
        for ever): the frontier tiles and unused exits the reach from where the player stands shows no way to are marked
        (`WorldMemory.mark_cut_off`) and out of the map's `promise` until it shows something new; the people standing in
        the way are no wall of it (they walk on); off for the earlier brains."""
        from ai_player.gates.test_world import GridGame, rig
        game = GridGame({"SPLIT": self.SPLIT_ROWS}, ("SPLIT", (3, 5)))  # a wall at x 9; the screen shows x 10, not x 11
        hands, nav, world, _, _ = rig(game)
        world.observe(game.look())
        key = world.current
        self.assertIn((10, 0), world.here().exits())
        self.assertEqual(world.promise(key), 10)  # x 10, y 1-9 beside the unseen x 11, and the door above (10, 1)
        self.assertEqual(nav.cut_off(game.look()), [])  # the earlier brains: as before
        nav.mark_cut = True
        cut = nav.cut_off(game.look())
        self.assertEqual(sorted(cut), sorted([(10, y) for y in range(1, 10)] + [(10, 0)]))
        self.assertEqual(world.promise(key), 0)  # FAULT halves: not marked; marked and `promise` blind to it
        world.maps[key].tiles[(40, 40)] = TileFact(True, False, False, False, None, False, False, 3, "NORMAL", 0, (3, 5))
        self.assertEqual(world.promise(key), 10)  # the map showed something new: counted again
        gap = [row[:9] + "." + row[10:] if y == 5 else row for y, row in enumerate(self.SPLIT_ROWS)]
        game = GridGame({"SPLIT": gap}, ("SPLIT", (3, 5)), people={"SPLIT": {(9, 5)}})  # someone stands in the gap
        hands, nav, world, _, _ = rig(game)
        world.observe(game.look())
        nav.mark_cut = True
        self.assertIn((9, 5), nav.walls(world.here(), (3, 5)))
        self.assertEqual(nav.cut_off(game.look()), [])  # FAULT half: the person a wall, all ten cut off

    def test_the_navigator_marks_what_it_cannot_get_to_before_it_chooses(self):
        """`Navigator.run` asks `cut_off` at every decision (before the intent chooses)."""
        from ai_player.brain.navigator import Intent
        from ai_player.gates.test_world import GridGame, drive as drive_world, rig
        game = GridGame({"SPLIT": self.SPLIT_ROWS}, ("SPLIT", (3, 5)))
        hands, nav, world, _, _ = rig(game)
        nav.mark_cut = True
        drive_world(nav.run(Intent("nothing", 500, lambda navigator, look_: None, lambda look_: False), "nothing"))
        self.assertEqual(len(world.cut_off[world.current][1]), 10)  # FAULT half: the call deleted, nothing marked

    def test_a_ping_pong_is_kept_past_its_intent(self):
        """(OLDALE's house door used for up to 98 goals in a row) `Navigator._remember_pingpong`: the warp that ended an
        intent as a ping-pong is kept (`ponged`) with the world memory's `stamp`; `ponged_now` says a target through it is
        one while nothing new has been seen anywhere since; the earlier brains keep none."""
        from ai_player.brain.navigator import Target
        from ai_player.gates.test_world import ExitTests, drive as drive_world, rig
        from ai_player.brain.explore import explore_intent
        for keep in (False, True):
            game = ExitTests().house(scene=True)
            hands, nav, world, _, _ = rig(game)
            if keep:
                nav.ponged = {}
            outcome = drive_world(nav.run(explore_intent("TOWN", "Story", 20000), "leave the house"))
            self.assertTrue(outcome.startswith("stuck: ping-pong: the warp "), outcome)  # (KI-129 B: not the edge's)
            if not keep:
                self.assertIsNone(nav.ponged)  # the earlier brains: as before
                continue
            self.assertEqual(len(nav.ponged), 1)  # FAULT half: nothing kept (the call deleted)
            name, stamp = next(iter(nav.ponged.items()))
            self.assertEqual(stamp, world.stamp())
            source, _, where = name.partition("|")
            world._last.key = source  # noqa: SLF001 - test side: standing on the warp's map
            exit_tile = tuple(int(v) for v in where.split(","))
            through = Target("back", (0, 0), "the stairs", exit=exit_tile)
            self.assertTrue(nav.ponged_now(through))  # FAULT halves: the stamp not kept, not compared
            self.assertFalse(nav.ponged_now(Target("back", (0, 0), "elsewhere", exit=(99, 99))))
            world.tiles_learned += 1  # something new seen anywhere: the warp is worth a try again
            self.assertFalse(nav.ponged_now(through))

    def lost(self, targets, routes=(), left=(("0:2", 3),), ponged=(), dead=(), personality: str = "Catcher",
             way_out: bool = True):
        """`lost_intent`'s choice on OLDALE with the explorer's candidates stood in for: `targets` (goal None), `routes`
        (toward a map in `left`), the warps `ponged`, the frontier tiles `dead` (a walk found no way there); `way_out`:
        OLDALE has a known way out (its MART's door), else the player is shut in."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import lost_intent
        world = world_with("OLDALE_TOWN", "ROUTE101", current="OLDALE_TOWN", mart_from="OLDALE_TOWN" if way_out else None)
        here = world.here()
        world.unreached[world.current] = {tile: len(here.tiles) for tile in dead}
        world.left_anywhere = lambda: list(left)
        nav = types.SimpleNamespace(choosing_on_the_move=False, world=world, rng=random.Random(1), heading=lambda: None,
                                    where=lambda seen: (here, (10, 10)), ponged_now=lambda t: t.exit in ponged)
        told: list[str] = []
        intent = lost_intent(personality, 2400, lambda seen: False, told.append)
        with mock.patch.object(goals_module, "candidates",
                               lambda nav_, look_, weights, goal=None, jitter_on=True: list(routes if goal else targets)), \
                mock.patch.object(goals_module, "pick", lambda found, rng: found[0]), \
                mock.patch.object(goals_module, "choose_target", lambda *a, **k: Target("wander", (1, 1), "wander")):
            chosen = intent.choose(nav, look(const="OLDALE_TOWN"))
        return chosen, told

    def test_a_walk_with_no_lead_heads_for_what_is_left_and_else_is_out_of_ideas(self):
        """`lost_intent` (seed 903: OLDALE's bottom edge crossed back and forth, "seen all of" both ways, until the
        patience): nothing here worth going to -> the way toward the nearest map with something left (`lost_way`); nothing
        left on ANY map it knows -> no target, and it says it is out of ideas; something new here -> that, as always."""
        from ai_player.brain.goals import OUT_OF_IDEAS, travel_intent
        from ai_player.brain import goals as goals_module
        seen_all = [Target("back", (8, 20), "the road down: it leads back to ROUTE101, seen all of")]
        route = [Target("route", (14, 7), "it leads toward the goal (1 link(s) known)", score=50.0, exit=(14, 6))]
        chosen, told = self.lost(seen_all, route)
        self.assertEqual((chosen.kind, chosen.tile), ("route", (14, 7)))  # FAULT half: the road back, seen all of
        self.assertTrue(chosen.reason.startswith("lost: "), chosen.reason)
        self.assertEqual(told, [])
        chosen, told = self.lost(seen_all, route, left=())
        self.assertIsNone(chosen)  # FAULT half: a wander among what it has seen, the push of the NOHINTS runs
        self.assertEqual(len(told), 1)
        self.assertTrue(told[0].startswith(OUT_OF_IDEAS), told)
        # (step52vdev1: three of four chapter-1 runs gave up inside the moving truck) SHUT IN, no way out known: it waits,
        # as before (FAULT half: out of ideas 26 frames into the game)
        chosen, told = self.lost([], route, left=(), way_out=False)
        self.assertEqual((chosen.kind if chosen else None, told), ("wander", []))
        frontier = [Target("frontier", (3, 3), "2 unseen tile(s) beside it")]
        chosen, told = self.lost(frontier + seen_all, route, left=())
        self.assertEqual((chosen.kind, told), ("frontier", []))
        # a frontier a walk found no way to is no option (seed 903 tried OLDALE's nine past the footprints man 41 times)
        chosen, told = self.lost(frontier + seen_all, route, dead=[(3, 3)])
        self.assertEqual(chosen.kind, "route")  # FAULT half: the dead frontier again
        # the old walk (`travel_intent`), the same candidates: the road back, seen all of
        world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
        nav = types.SimpleNamespace(choosing_on_the_move=False, world=world, rng=random.Random(1), heading=lambda: None,
                                    where=lambda seen: (world.here(), (10, 10)))
        with mock.patch.object(goals_module, "candidates", lambda *a, **k: list(seen_all)), \
                mock.patch.object(goals_module, "pick", lambda found, rng: found[0]):
            self.assertEqual(travel_intent(None, "Catcher", 2400, lambda s: False).choose(nav, look()).kind, "back")

    def test_a_map_a_lost_walk_found_nothing_worth_going_to_on_is_spent(self):
        """(step52vdev3, NOHINTS seed 1223: OLDALE <-> ROUTE 103 across the edge for 3,395 frames, each map "where something
        is left" seen from the other, nothing worth going to on either) a walk with no lead that stands on a map and finds
        nothing there worth going to marks it SPENT (`WorldMemory.mark_spent`): its `promise` is 0 until it shows something
        new, or the story moves on (`forget_marks`)."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import lost_intent
        world = world_with("OLDALE_TOWN", "ROUTE103", current="OLDALE_TOWN", mart_from="OLDALE_TOWN")
        here = world.here()
        for x in range(3):  # a frontier on OLDALE: something left to see there, as far as `promise` knows
            here.tiles[(x, 0)] = TileFact(False, False, False, True, None, False, False, 3, "NORMAL", 0, (0, 0))
        key = world.current
        before = world.promise(key)
        self.assertGreater(before, 0)
        nav = types.SimpleNamespace(choosing_on_the_move=False, world=world, rng=random.Random(1), heading=lambda: None,
                                    where=lambda seen: (here, (1, 1)), ponged_now=lambda t: False)
        seen_all = [Target("back", (8, 20), "the road down: it leads back to ROUTE101, seen all of")]
        with mock.patch.object(goals_module, "candidates", lambda *a, **k: list(seen_all)), \
                mock.patch.object(goals_module, "pick", lambda found, rng: found[0]):
            lost_intent("Catcher", 2400, lambda seen: False, lambda why: None).choose(nav, look(const="OLDALE_TOWN"))
        self.assertEqual(world.promise(key), 0)  # FAULT halves: not marked; marked and `promise` blind to it
        here.tiles[(9, 9)] = TileFact(True, False, False, False, None, False, False, 3, "NORMAL", 0, (0, 0))
        self.assertGreater(world.promise(key), 0)  # it showed something new: counted again
        world.mark_spent(key)
        world.forget_marks()
        self.assertGreater(world.promise(key), 0)  # the story moved on: counted again (FAULT half: kept)

    def test_a_lost_walk_never_goes_back_through_a_ping_pong_door_unless_it_is_the_only_way(self):
        doors = [Target("door", (5, 8), "an exit not used yet: where does it go?", exit=(5, 7)),
                 Target("door", (9, 8), "an exit not used yet: where does it go?", exit=(9, 7))]
        chosen, _ = self.lost(doors, ponged=[(5, 7)])
        self.assertEqual(chosen.exit, (9, 7))  # FAULT half: the door of the ping-pong again
        chosen, _ = self.lost(doors, ponged=[(5, 7), (9, 7)])
        self.assertEqual(chosen.exit, (5, 7))  # the only ways left: kept (FAULT half: none, a wander)

    def test_a_frontier_stood_on_whose_unseen_side_stays_unseen_is_given_up(self):
        """`Navigator._seen_out` (OLDALE's MART: two frontier tiles whose unseen side the screen never shows): a walk that
        ARRIVED on a frontier tile that is still one marks it like one no walk found a way to (out of `promise`) and gives
        it up for the intent; the earlier brains as before."""
        from ai_player.brain.navigator import Intent
        from ai_player.gates.test_world import GridGame, drive as drive_world, rig
        rows = ["#" * 30] + ["#" + "." * 28 + "#" for _ in range(9)] + ["#" * 30]
        for on in (False, True):
            game = GridGame({"OPEN": rows}, ("OPEN", (3, 5)))
            plain = game.view
            game.view = lambda plain=plain: replace(plain(), rows=tuple(tuple(t for t in row if t.x < 11)
                                                                        for row in plain().rows))  # x 11+ never shown
            hands, nav, world, _, _ = rig(game)
            nav.mark_cut = on
            tried: list = []

            def choose(navigator, look_):
                if tried:
                    return None
                tried.append(1)
                return Target("frontier", (10, 5), "1 unseen tile(s) beside it")

            drive_world(nav.run(Intent("to the edge", 3000, choose, lambda look_: False), "to the edge"))
            self.assertEqual(game.pos, (10, 5))  # it stood there
            key = world.current
            self.assertIn((10, 5), world.here().frontier())  # and the unseen beside it stayed unseen
            marked = (10, 5) in world.unreached.get(key, {})
            self.assertEqual(marked, on)  # FAULT halves: the call deleted, the mark deleted
            given_up = any(why.startswith("arrived: the unseen beside it stayed unseen") for why in nav.excluded.values())
            self.assertEqual(given_up, on)  # FAULT half: not given up for the intent

    def test_out_of_ideas_gives_the_run_up(self):
        """`GoalManager.next_goal`: a story goal with NO LEAD whose last walk found nothing left on any map it knows
        (`lost_end`), nothing new seen since: the run is given up ("give_up"); something new seen since, or a goal with a
        lead: not."""
        mgr = manager("Catcher", hints_off=True)
        milestone = mgr.story.milestones[8]
        mgr.prep(milestone)["steps"] = 1000
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN")
        seen = look(ch1_through("ch1_rival_route103"), party=[mon(20)], const="OLDALE_TOWN", money=0)
        goal = mgr.next_goal(seen, world, milestone, 8)
        self.assertEqual((goal.kind, goal.key), ("go", "go:?ch1_rival_route103"))
        mgr.memory.lost_end = (milestone.id, world.stamp())
        given = mgr.next_goal(seen, world, milestone, 8)
        self.assertEqual(given.kind, "give_up")  # FAULT halves: never asked; the stamp not compared
        self.assertIn("out of ideas", given.reason)
        world.tiles_learned += 5  # something new since: not out of ideas
        self.assertEqual(mgr.next_goal(seen, world, milestone, 8).kind, "go")
        led = manager("Catcher")  # hints on, the step's words read: a lead
        led.prep(milestone)["steps"] = 1000
        told = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN",
                          heard={"Your POKéMON may be a match for my friend on ROUTE 103."})
        led.memory.lost_end = (milestone.id, told.stamp())
        self.assertEqual(led.next_goal(seen, told, milestone, 8).key, "go:ROUTE103")

    def test_the_story_moving_on_forgets_what_it_could_not_get_to(self):
        """(step52vdev1, chapter-1 seed 1201: "out of ideas" at the start of PROF. BIRCH's milestone, in the rival's bedroom,
        LITTLEROOT's road north still marked from the twin's scene of the milestone before) `Navigator.story_moved` drops the
        ping-pongs kept and the world memory's marks (`forget_marks`); the REAL play loop asks it when the milestone
        changes."""
        from ai_player.brain.navigator import Navigator
        from ai_player.hands.pad import Hands
        world = world_with("LITTLEROOT_TOWN", current="LITTLEROOT_TOWN")
        nav = Navigator(Hands(None, None, random.Random(1), random.Random(1), None, lambda line: None), world, random.Random(1))
        nav.ponged = {"0:1|5,8": world.stamp()}
        world.unreached["0:1"] = {(8, -1): 0}
        world.cut_off["0:1"] = (0, frozenset({(9, -1), (10, -1)}))
        said = nav.story_moved()
        self.assertEqual((nav.ponged, world.unreached, world.cut_off), ({}, {}, {}))  # FAULT half: kept into the milestone
        self.assertIn("1 ping-pong(s) and 3 place(s)", said)
        asked: list = []

        def effect(goal, world_, runner):
            asked.append(list(runner.nav.moved))
            return None

        loop = PlayLoopTests()
        loop.run_loop(screen=loop.free_screen(), budget=5000, effect=effect)
        self.assertEqual(len(asked[0]), 1)  # asked once, at the first milestone read (FAULT half: never asked)

    def test_the_play_loop_ends_a_run_given_up(self):
        from ai_player import mode as mode_module
        from ai_player.brain.goals import Goal

        class GivesUp(mode_module.GoalManager):
            def next_goal(self, look_, world, milestone, index):
                self.memory.decisions += 1
                return Goal("give_up", f"{milestone.title}: out of ideas: nothing left", milestone.id, key="give_up")

        loop = PlayLoopTests()
        with mock.patch.object(mode_module, "GoalManager", GivesUp):
            reason, _, pursued, _, _ = loop.run_loop(screen=loop.free_screen(), budget=20_000)
        self.assertTrue(reason.startswith("stuck: ") and "out of ideas: nothing left" in reason, reason)
        self.assertEqual(pursued, [])  # FAULT half: pursued as a goal (none can), the run going on

    def test_a_walk_with_no_lead_uses_the_lost_walk(self):
        """`GoalRunner._pursue`: an exploring `go` with no lead and its look round put aside (`LOST_KEYS`) walk with
        `lost_intent`; when it is out of ideas the outcome says so and `lost_end` holds the milestone and the stamp; a led
        walk, the look round of a milestone whose steps are done and a search keep `travel_intent`."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import Goal, GoalRunner
        from ai_player.brain.navigator import Intent
        mgr = manager("Catcher", hints_off=True)
        milestone = mgr.story.milestones[8]
        world = world_with("OLDALE_TOWN", current="OLDALE_TOWN")
        lost_made: list = []

        def fake_lost(personality, budget, done, told):
            lost_made.append(told)
            return Intent("look around", budget, lambda nav_, look_: None, done)

        def run(intent, why):
            if lost_made:
                lost_made[-1]("out of ideas: nothing left (test)")
            yield
            return "stuck: nothing left to try on OLDALE_TOWN"

        nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(20)])), nav, mgr,
                            types.SimpleNamespace(purpose=""), lambda line: None)
        for kind, key, lost in (("go", "go:?ch1_rival_route103", True), ("look_around", "aside:go:?ch1_rival_route103", True),
                                ("look_around", "look_around", False), ("find", "find:rival", False)):
            lost_made.clear()
            mgr.memory.lost_end = None
            with mock.patch.object(goals_module, "lost_intent", fake_lost):
                ok, outcome = drive(runner._pursue(Goal(kind, "x", milestone.id, key=key, look="rival" if kind == "find"  # noqa: SLF001
                                                        else None), milestone, 8, lambda seen: 8))
            self.assertEqual(bool(lost_made), lost, key)  # FAULT half: the old walk, which wanders
            if lost:
                self.assertTrue(outcome.startswith("out of ideas: nothing left (test)"), outcome)
                self.assertEqual(mgr.memory.lost_end, (milestone.id, world.stamp()))  # FAULT half: no stamp kept


def _open_tile() -> TileFact:
    """A walkable tile (no wall, no water, no ledge, no exit)."""
    return TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (0, 0))


def _left_to_see(world: WorldMemory, const: str, at: tuple[int, int] = (1, 1)) -> None:
    """Give the map `const` one frontier tile (a walkable tile beside unseen ones): its `promise` is then above 0."""
    memory = next(m for m in world.maps.values() if m.const == const)
    memory.tiles[at] = _open_tile()


@contextlib.contextmanager
def _atlas_types(**override: str):
    """(KI-128) The atlas with some maps TYPED otherwise (`MAP_TYPE_INDOOR` for the woods): the fault arm that shows the
    map TYPE carries a rule, not the map's name."""
    from ai_player.knowledge import atlas
    types_now = {**atlas._types(), **override}  # noqa: SLF001 - test side
    with mock.patch.dict(atlas._CACHE, {"types": types_now}):  # noqa: SLF001
        yield


#: (KI-128, K-C3) every map const the six r1base chapter 1-2 runs (2026-10-30, ai-step5-play: CH1T, CH1C, CH1M, CH2, CH2T,
#: CH2M) stood on, from each world.jsonl's last line (s53/fix/build/r1base_consts.py; no map was known and not stood on)
R1BASE_CONSTS = ("INSIDE_OF_TRUCK", "LITTLEROOT_TOWN", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", "LITTLEROOT_TOWN_BRENDANS_HOUSE_2F",
                 "LITTLEROOT_TOWN_MAYS_HOUSE_1F", "LITTLEROOT_TOWN_MAYS_HOUSE_2F", "LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB",
                 "OLDALE_TOWN", "OLDALE_TOWN_HOUSE1", "OLDALE_TOWN_HOUSE2", "OLDALE_TOWN_MART", "OLDALE_TOWN_POKEMON_CENTER_1F",
                 "PETALBURG_CITY", "PETALBURG_CITY_GYM", "PETALBURG_CITY_HOUSE2", "PETALBURG_CITY_POKEMON_CENTER_1F",
                 "PETALBURG_CITY_POKEMON_CENTER_2F", "ROUTE101", "ROUTE102", "ROUTE103")


class KI128Tests(unittest.TestCase):
    """(KI-128, 2026-10-31: the woods are a road) In all three A0 runs (ledger #68) the AI never reached PETALBURG WOODS'
    north half: `lead_toward` evicted it from the woods (no "look on from here" there, and the woods no lead) and
    `keeps_going` refused the way back in, both because the woods are not NAMED like a route (`OUTDOOR`). `open_way` asks
    the atlas's STATIC map type too (`knowledge/atlas.py`; USER RULINGS 40, 45). FAULT arms type the woods INDOOR in the
    atlas: the predicate carries each rule, not a map's name. Mutants: `revert_step5.py` G407-G412."""

    def test_k_f1_in_the_woods_with_something_left_it_looks_on_from_there(self):
        from ai_player.brain.goals import lead_toward
        world = world_with("ROUTE104", "PETALBURG_WOODS", current="PETALBURG_WOODS")
        _left_to_see(world, "ROUTE104")
        _left_to_see(world, "PETALBURG_WOODS")
        self.assertEqual((world.promise("0:1"), world.promise("0:2")), (1, 1))
        self.assertIsNone(lead_toward(world, "RUSTBORO_CITY"))  # FAULT (818d3706): "ROUTE104", the logged eviction
        with _atlas_types(PETALBURG_WOODS="MAP_TYPE_INDOOR"):
            self.assertEqual(lead_toward(world, "RUSTBORO_CITY"), "ROUTE104")  # the TYPE carries it

    def test_k_f2_the_way_back_into_the_woods_is_kept_on_the_way(self):
        from ai_player.brain.goals import keeps_going
        world = world_with("ROUTE104", "PETALBURG_WOODS", current="ROUTE104")
        world.warps["0:1|11,38"] = {"to": "0:2", "arrival": [17, 38], "uses": 1, "by": "ai", "inferred": False}
        back = Target("back", (11, 39), "back to PETALBURG_WOODS", exit=(11, 38), direction="up")
        self.assertTrue(keeps_going(world, back, "RUSTBORO_CITY"))  # FAULT (818d3706): False, the way back refused
        with _atlas_types(PETALBURG_WOODS="MAP_TYPE_INDOOR"):
            self.assertFalse(keeps_going(world, back, "RUSTBORO_CITY"))

    def test_k_f6_told_of_the_woods_it_looks_out_in_the_open_not_in_a_building(self):
        """(KI-128, the fourth `open_way` site) A goal map never seen that is OPEN COUNTRY (the woods) is looked for out
        in the open, where the most is left to see, not as a building's room in its town (`lead_toward`'s first rule)."""
        from ai_player.brain.goals import lead_toward
        world = world_with("PETALBURG_CITY", "ROUTE104", current="PETALBURG_CITY")
        _left_to_see(world, "ROUTE104")
        self.assertEqual(lead_toward(world, "PETALBURG_WOODS"), "ROUTE104")  # FAULT (818d3706): None, a "building"
        self.assertIsNone(lead_toward(world, "PETALBURG_CITY_GYM"))  # CONTROL: a room of the town it stands in

    def test_k_f7_a_walk_to_a_map_never_seen_heads_first_for_the_woods(self):
        """(the call-site census: `lead_toward`'s one site, `GoalRunner._travel`) Told of RUSTBORO from ROUTE 104 with
        nothing left to see there and the woods unseen in part, the go walks FIRST to the woods (the lead), then on."""
        from ai_player.brain.goals import GoalRunner
        world = world_with("ROUTE104", "PETALBURG_WOODS", current="ROUTE104")
        _left_to_see(world, "PETALBURG_WOODS")
        walks: list[str] = []

        def run(intent, why):
            walks.append(intent.name)
            yield
            return "done (test)"

        nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
        runner = GoalRunner(types.SimpleNamespace(look=lambda: look(party=[mon(20)], const="ROUTE104")), nav,
                            manager("Catcher"), types.SimpleNamespace(purpose=""), lambda line: None)
        drive(runner._travel("RUSTBORO_CITY", "to RUSTBORO_CITY", 9000, lambda seen: False))  # noqa: SLF001
        self.assertEqual(walks, ["travel to PETALBURG_WOODS", "travel to RUSTBORO_CITY"])  # FAULT (818d3706): no lead

    def test_k_f8_the_walk_takes_the_way_back_into_the_woods_and_refuses_a_house(self):
        """(the census: `keeps_going`'s site in `travel_intent.choose`) Going to RUSTBORO, the walk's own choice keeps the
        way back into the woods and refuses the way back into a house it has been in."""
        from ai_player.brain import goals as goals_module
        from ai_player.brain.goals import travel_intent
        world = world_with("ROUTE104", "PETALBURG_WOODS", "ROUTE104_MR_BRINEYS_HOUSE", current="ROUTE104")
        world.warps["0:1|11,38"] = {"to": "0:2", "arrival": [17, 38], "uses": 1, "by": "ai", "inferred": False}
        world.warps["0:1|17,50"] = {"to": "0:3", "arrival": [5, 8], "uses": 1, "by": "ai", "inferred": False}
        house = Target("back", (17, 51), "it leads back to ROUTE104_MR_BRINEYS_HOUSE", exit=(17, 50), score=9.0)
        woods = Target("back", (11, 39), "it leads back to PETALBURG_WOODS", exit=(11, 38), score=5.0)
        nav = types.SimpleNamespace(choosing_on_the_move=False, world=world, rng=random.Random(1), heading=lambda: None,
                                    where=lambda seen: (world.here(), (10, 10)))
        with mock.patch.object(goals_module, "candidates", lambda *a, **k: [house, woods]), \
                mock.patch.object(goals_module, "pick", lambda found, rng: max(found, key=lambda t: t.score)), \
                mock.patch.object(goals_module, "choose_target", lambda *a, **k: Target("wander", (1, 1), "wander")):
            chosen = travel_intent("RUSTBORO_CITY", "Catcher", 2400, lambda s: False).choose(nav, look(const="ROUTE104"))
        self.assertEqual((chosen.kind, chosen.exit), ("back", (11, 38)))  # FAULT (818d3706): the fallback's wander

    def test_k_f9_a_lost_walk_refuses_a_way_back_into_a_house(self):
        """(the census: `keeps_going`'s site in `lost_intent`) A walk with no lead never goes back into a building it has
        been in: with the house's door the only thing here, it heads for the map where something is left."""
        route = [Target("route", (14, 7), "it leads toward the goal (1 link(s) known)", score=50.0, exit=(14, 6))]
        house = [Target("back", (5, 6), "it leads back to OLDALE_TOWN_MART, where 2 thing(s) are left to see", exit=(5, 5))]
        chosen, told = VerifierRound52Tests().lost(house, route)
        self.assertEqual((chosen.kind, chosen.tile), ("route", (14, 7)))  # FAULT (the call deleted): back into the MART
        self.assertEqual(told, [])

    def test_k_f4_without_part_a_a_phantom_on_route104_still_wins_from_petalburg(self):
        """(F2's case) A DOCUMENTED EXPECTATION, not a pass condition of KI-128: ROUTE 104's phantom (1 thing "left to
        see" that no walk can get to) keeps it the lead from PETALBURG, routes before the woods. Why KI-128 never ships
        without KI-129 Part A; `KI129PartATests.test_p_f2_*` asserts the flip."""
        from ai_player.brain.goals import lead_toward
        world = world_with("PETALBURG_CITY", "ROUTE104", "PETALBURG_WOODS", current="PETALBURG_CITY")
        _left_to_see(world, "ROUTE104")
        _left_to_see(world, "PETALBURG_WOODS")
        self.assertEqual(world.promise("0:1"), 0)
        self.assertEqual(lead_toward(world, "RUSTBORO_CITY"), "ROUTE104")

    def test_k_c1_interiors_stay_refused_on_the_way(self):
        from ai_player.brain.goals import keeps_going
        for interior in ("ROUTE104_MR_BRINEYS_HOUSE", "PETALBURG_CITY_POKEMON_CENTER_1F"):
            world = world_with("ROUTE104", interior, current="ROUTE104")
            world.warps["0:1|17,50"] = {"to": "0:2", "arrival": [5, 8], "uses": 1, "by": "ai", "inferred": False}
            back = Target("back", (17, 51), f"back to {interior}", exit=(17, 50), direction="up")
            self.assertFalse(keeps_going(world, back, "RUSTBORO_CITY"), interior)
            self.assertTrue(keeps_going(world, back, interior), interior)  # unless it is the goal

    def test_k_c2_a_shop_and_the_truck_are_not_open_country(self):
        from ai_player.brain.goals import open_way
        from ai_player.knowledge.atlas import open_map
        for const in ("ROUTE104_PRETTY_PETAL_FLOWER_SHOP", "INSIDE_OF_TRUCK"):
            self.assertIs(open_map(const), False, const)  # the atlas holds it, and says no (not a fallback)
            self.assertFalse(open_way(const), const)
        for const in ("PETALBURG_WOODS", "ROUTE104", "RUSTBORO_CITY", "EVER_GRANDE_CITY"):
            self.assertIs(open_map(const), True, const)
            self.assertTrue(open_way(const), const)

    def test_k_c3_chapters_1_and_2_are_inert(self):
        from ai_player.brain.goals import OUTDOOR, open_way
        self.assertEqual(len(R1BASE_CONSTS), 20)
        for const in R1BASE_CONSTS:
            self.assertEqual(open_way(const), bool(OUTDOOR.match(const)), const)

    def test_k_c4_a_map_the_atlas_does_not_hold_counts_by_its_name(self):
        from ai_player.brain.goals import open_way
        from ai_player.knowledge.atlas import open_map
        for const, named_open in (("ROUTE999", True), ("NOWHERE_TOWN", True), ("SOMEWHERE_NEW", False), ("", False),
                                  (None, False)):
            self.assertIsNone(open_map(const), const)
            self.assertEqual(open_way(const), named_open, const)

    def test_k_c5_hurt_in_the_woods_it_looks_for_no_town_centre_there(self):
        """The heal errand's "a town has a POKéMON CENTER" still asks the NAME (`OUTDOOR`): the woods are open country but
        no town, so a hurt party there heals at the centre it knows."""
        def decide(mgr, world, const, number):
            observation = look(ch2_dad_marks(), party=[mon(9, hp=8, max_hp=20)], const=const, map_number=number)
            index, milestone = mgr.milestone(observation, visited_in(world))
            return mgr.next_goal(observation, world, milestone, index)

        world = petalburg_world()
        world.maps["0:4"] = MapMemory("0:4", "PETALBURG_WOODS", "PETALBURG_WOODS")
        world.maps["0:4"].visits[(1, 1)] = 1
        world._last.key = "0:4"  # noqa: SLF001
        goal = decide(manager("Story"), world, "PETALBURG_WOODS", 11)
        self.assertNotEqual(goal.kind, "find_center", goal.reason)
        self.assertEqual(goal.kind, "heal", goal.reason)
        control = petalburg_world()  # CONTROL: in a town whose centre it has not seen, it looks there (as before)
        self.assertEqual(decide(manager("Story"), control, "PETALBURG_CITY", 3).kind, "find_center")


#: (KI-129 Part A, P-F1) the AI's REAL ROUTE 104 memory at the end of the A0-1 run (`make_ki129_fixture.py`)
ROUTE104_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "route104_a01.world.jsonl"
#: the strip behind the ledge on ROUTE 104 (x 32-33, y 42-47): seen from below, reachable only round through PETALBURG
STRIP = [(32, 42), (33, 43), (33, 44), (33, 45), (33, 46), (33, 47)]


class KI129PartATests(unittest.TestCase):
    """(KI-129 Part A, 2026-10-31: one reach for "can it get there?") `Navigator.cut_off`'s reach went round through the
    tiles seen past a crossed edge (PETALBURG's), which the planner that walks never does (`in_map_walls`), so ROUTE 104
    kept a strip behind a ledge as "left to see" for ever and the walk crossed the PETALBURG edge back and forth. The reach
    now uses the planner's own rule. Mutant: `revert_step5.py` G413."""

    def fixture_world(self) -> WorldMemory:
        return WorldMemory.from_dict(json.loads(ROUTE104_FIXTURE.read_text(encoding="utf-8")))

    def cut_from(self, world: WorldMemory, tile: tuple[int, int]) -> list:
        world._last.key, world._last.xy = "0:19", tile  # noqa: SLF001
        memory = world.maps["0:19"]
        nav = Navigator(None, world, random.Random(1), 2.0, "Catcher")
        nav.where = lambda look_: (memory, tile)
        nav.mark_cut = True
        return nav.cut_off(types.SimpleNamespace(frame=1))

    def test_p_f1_the_strip_behind_the_ledge_is_not_left_to_see_from_below(self):
        world = self.fixture_world()
        memory = world.maps["0:19"]
        self.assertEqual((memory.const, memory.edges), ("ROUTE104", {"right": 40}))
        self.assertEqual(len(memory.frontier()), 5)
        self.assertEqual([xy for xy in memory.exits() if world.link_of("0:19", xy) is None], [(32, 42)])
        self.assertEqual(world.promise("0:19"), 6)
        self.assertEqual(sorted(self.cut_from(world, (39, 63))), STRIP)  # FAULT (818d3706): nothing cut
        self.assertEqual(world.promise("0:19"), 0)

    def test_p_c1_from_inside_the_strip_its_frontier_is_not_cut(self):
        world = self.fixture_world()
        self.assertEqual(self.cut_from(world, (33, 45)), [])
        self.assertEqual(world.promise("0:19"), 6)

    def test_p_f2_with_ki128_and_part_a_the_woods_are_the_lead(self):
        """(F2/F3) KI-128 and Part A TOGETHER: from PETALBURG and from ROUTE 104 (39, 63), with ROUTE 104's strip cut, the
        lead toward RUSTBORO is the woods. The Part-A-removed arm (no cut): "ROUTE104" from PETALBURG, None (look on
        from here) on ROUTE 104: the loop A0 walked."""
        from ai_player.brain.goals import lead_toward
        for start in ("PETALBURG_CITY", "ROUTE104"):
            world = self.fixture_world()
            world.maps["0:0"] = MapMemory("0:0", "PETALBURG_CITY", "PETALBURG_CITY")
            world.maps["0:0"].visits[(0, 13)] = 1
            world.maps["24:11"] = MapMemory("24:11", "PETALBURG_WOODS", "PETALBURG_WOODS")
            world.maps["24:11"].visits[(16, 38)] = 1
            _left_to_see(world, "PETALBURG_WOODS", (16, 30))
            self.assertGreater(world.promise("24:11"), 0)
            world._last.key = "0:0" if start == "PETALBURG_CITY" else "0:19"  # noqa: SLF001
            self.assertEqual(lead_toward(world, "RUSTBORO_CITY"), "ROUTE104" if start == "PETALBURG_CITY" else None,
                             start)  # the Part-A-removed arm
            self.cut_from(world, (39, 63))
            world._last.key = "0:0" if start == "PETALBURG_CITY" else "0:19"  # noqa: SLF001
            self.assertEqual(lead_toward(world, "RUSTBORO_CITY"), "PETALBURG_WOODS", start)  # FAULT (818d3706): None


#: (KI-129 Part B) `test_world.py` ExitTests.test_a_road_is_a_connection_with_its_offset_and_edges's town and route: both
#: seen whole from anywhere on them, so once both are walked nothing is left to see, and every walk goes "back ..., seen
#: all of" across their one edge
PONG_MAPS = {"TOWN": ["####..####", "#........#", "#........#", "##########"], "ROUTE": ["#..#", "#..#", "#..#"]}
PONG_LINKS = {("TOWN", "up"): ("ROUTE", (-3, 3)), ("ROUTE", "down"): ("TOWN", (3, -3))}


class KI129PartBTests(unittest.TestCase):
    """(KI-129 Part B, 2026-10-31: an edge ping-pong is a ping-pong) The ping-pong rule counted only WARP uses, so a walk
    with nothing left on either side of an edge crossed it until the novelty window ended the intent (A0's chapter-3 runs:
    194-196 crossings of one edge in 10,000 frames), and the next intent began again. For the play brain (`ponged` set)
    an edge crossed `PINGPONG_USES` times from one side, nothing new since the crossing before the last (a SLIDING
    window, the verifier's V2-1; the warps keep "since the second"), ends the intent; both sides are
    kept (`_remember_edge_pingpong`) and the later intents drop the roads past it (`edge_ponged`, `explore.candidates`)
    while nothing new is seen and `PONG_REST` frames have not passed; a known route toward the goal is kept. The earlier
    brains (`ponged` None) are unchanged. Mutants: `revert_step5.py` G419-G429."""

    def pong(self, seed: int = 1, ponged: bool = True, brain: str = "travel", crop: bool = True):
        """B-F1's walk. `crop` False (`test_world.py`'s CROP fault: the eyes show the whole map and 7 tiles round it,
        the same rectangle wherever the player stands): each map is seen whole at its first look, so after both are
        walked NOTHING new can be seen anywhere, which the later-intent tests need (with the crop a wander to a corner
        shows new tiles of the border round the map: news, and the rule rightly lets the edge be tried again)."""
        from ai_player.brain.explore import explore_intent
        from ai_player.brain.goals import travel_intent
        from ai_player.gates.test_world import GridGame, drive as drive_world, rig
        game = GridGame(PONG_MAPS, ("TOWN", (2, 2)), links=PONG_LINKS, crop=crop)
        hands, nav, world, notes, _ = rig(game, seed=seed)
        nav.mark_cut = True
        if ponged:
            nav.ponged = {}
        intent = (travel_intent(None, "Story", 20000, lambda look_: False) if brain == "travel"
                  else explore_intent(None, "Story", 20000))
        outcome = drive_world(nav.run(intent, "the edge"), 200_000)
        return game, nav, world, notes, outcome

    @staticmethod
    def crossings(world, since: int = 0) -> list:
        return [t for t in world.transitions[since:] if t.how == "connection"]

    def test_b_f1_an_edge_crossed_back_and_forth_for_nothing_ends_the_intent(self):
        """B-F1. FAULT (17ed7794): "stuck: nothing new" after 72 / 84 crossings (seeds 1 / 2)."""
        from ai_player.world.memory import OPPOSITE
        for seed in (1, 2):
            with self.subTest(seed=seed):
                game, nav, world, _, outcome = self.pong(seed)
                self.assertTrue(outcome.startswith("stuck: ping-pong: the edge "), outcome)
                crossed = self.crossings(world)
                self.assertLessEqual(len(crossed), 5)
                first = crossed[0]
                sides = {f"{first.source}|edge:{first.direction}", f"{first.target}|edge:{OPPOSITE[first.direction]}"}
                self.assertEqual(set(nav.ponged), sides)  # FAULT half (only the source side kept): one key
                self.assertEqual({v[0] for v in nav.ponged.values()}, {world.stamp()})
                self.assertEqual({v[1] for v in nav.ponged.values()}, {game.frame})

    def test_b_f1_news_after_the_second_crossing_does_not_free_the_edge_for_the_intent(self):
        """B-F1's corner, CHANGED ON PURPOSE by the verifier's V2-1 (2026-10-31): seed 3's first intent sees new tiles
        AFTER its second crossing (the last at f649). With the warps' fixed window (`frames[1]`) that intent could never
        stop on the edge: it ran to the novelty window, 84 crossings. The edge's window now SLIDES (nothing new since the
        crossing before the last), so it stops a few crossings after the news, and the next intent, with nothing new,
        stops too. FAULT: the worktree before V2-1, "stuck: nothing new" after 84 crossings; 17ed7794, the same."""
        from ai_player.brain.goals import travel_intent
        from ai_player.gates.test_world import drive as drive_world
        game, nav, world, _, outcome = self.pong(3)
        self.assertTrue(outcome.startswith("stuck: ping-pong: the edge "), outcome)  # FAULT: stuck: nothing new
        crossed = self.crossings(world)
        self.assertGreater(crossed[1].frame, 0)
        self.assertLessEqual(len(crossed), 7)  # FAULT: 84
        self.assertIn("f649", outcome)  # non-vacuous: the news after the 2nd crossing is the window's start
        since = len(world.transitions)
        outcome = drive_world(nav.run(travel_intent(None, "Story", 20000, lambda look_: False), "again"), 200_000)
        self.assertTrue(outcome.startswith("stuck: ping-pong: the edge "), outcome)
        self.assertLessEqual(len(self.crossings(world, since)), 5)

    def wide_walk(self, plan: list, ponged=True):
        """V2-1's walk: B-C1's town and route wider than the view, the walk sent across their edge at the x of `plan` in
        turn (the town's top edge, or the route's bottom). Returns (outcome, crossings, learned: frame -> tiles learned
        by the look at that frame, the plan left)."""
        from ai_player.brain.navigator import Intent
        from ai_player.gates.test_world import GridGame, drive as drive_world, rig
        wide = {"TOWN": ["#" + "." * 38 + "#"] * 3 + ["#" * 40], "ROUTE": ["#" * 40] + ["#" + "." * 38 + "#"] * 2}
        links = {("TOWN", "up"): ("ROUTE", (0, 3)), ("ROUTE", "down"): ("TOWN", (0, -3))}
        game = GridGame(wide, ("TOWN", (3, 1)), links=links)
        hands, nav, world, notes, _ = rig(game)
        nav.ponged = {} if ponged else None
        learned: dict[int, int] = {}
        hands.watchers.append(lambda look_: learned.__setitem__(look_.frame, world.tiles_learned))
        plan = list(plan)
        home: list = []  # where the first walk on the map stood on began

        def choose(navigator, look_):
            if not plan:
                return None
            x = plan.pop(0)
            if x is None:  # a walk on the map stood on, to a tile already walked: nothing new
                home.append(game.pos)
                return Target("wander", (home[0][0] - 2, home[0][1]) if len(home) % 2 else home[0], "a walked tile")
            return Target("road", (x, -1) if game.map == "TOWN" else (x, 3), "across")

        outcome = drive_world(nav.run(Intent("across", 20000, choose, lambda look_: False), "across"), 400_000)
        return outcome, self.crossings(world), learned, plan, nav

    @staticmethod
    def last_news(learned: dict) -> int:
        """The frame of the last look at which the tiles learned grew."""
        frames = sorted(learned)
        return max(f for prev, f in zip(frames, frames[1:]) if learned[f] > learned[prev])

    def test_b_f1_news_after_the_third_crossing_then_crossings_with_nothing_new_stop(self):
        """V2-1's FAULT (the verifier's): new tiles are seen between the crossings up to the tenth (x 3, 12, 21, 30, 37:
        the town's top edge crossed from below 3 times, then back and forth at x 37), then the walk is sent across at x 37
        twelve more times with NOTHING new. The intent must stop as an edge ping-pong within 5 crossings after the last
        news, and both sides are kept. FAULT: the worktree before V2-1 (`frames[1]`: news after the 2nd crossing frees
        the edge for the whole intent) crosses all 17 and ends "nothing left to try"; 17ed7794 the same."""
        outcome, crossed, learned, plan, nav = self.wide_walk([3, 12, 21, 30, 37] + [37] * 12)
        news = self.last_news(learned)
        town_up = [t.frame for t in crossed if t.direction == "up"]
        self.assertGreater(news, town_up[2])  # non-vacuous: the news came AFTER the 3rd same-side crossing ...
        self.assertTrue(outcome.startswith("stuck: ping-pong: the edge "), outcome)  # FAULT: nothing left to try
        after = [t for t in crossed if t.frame >= news]
        self.assertLessEqual(len(after), 5, (news, [t.frame for t in crossed]))  # FAULT: 8 (17 crossed in all)
        self.assertTrue(plan, "the walk crossed every planned time")  # ... and 5 or more were left to cross for nothing
        self.assertEqual(len(nav.ponged), 2)

    def test_b_c1b_a_walk_on_its_own_map_with_nothing_new_after_crossings_with_news_is_no_ping_pong(self):
        """V2-1's CONTROL (and the verifier's mutant VM7, the window keyed on the LAST crossing): B-C1's five crossings
        with news between, then walks on the map stood on to tiles already seen, NOTHING new and no crossing: the edge
        rule must not fire (an edge ping-pong is crossings, not time); the intent ends "nothing left to try", and with
        `ponged` None (the earlier brains) the same."""
        runs = [self.wide_walk([3, 12, 21, 30, 37, None, None, None], ponged) for ponged in (True, False)]
        (outcome, crossed, learned, plan, nav), (plain, crossed2, _, _, _) = runs
        self.assertTrue(outcome.startswith("stuck: nothing left to try"), outcome)  # VM7: stuck: ping-pong
        self.assertEqual(len(crossed), 5)
        self.assertEqual(plan, [])  # non-vacuous: the walks on the map were made ...
        self.assertLessEqual(self.last_news(learned), crossed[-1].frame)  # ... and saw nothing new after the last crossing
        self.assertGreater(max(learned) - crossed[-1].frame, 30)  # ... for a while
        self.assertEqual((outcome, [(t.source, t.direction, t.frame) for t in crossed]),
                         (plain, [(t.source, t.direction, t.frame) for t in crossed2]))
        self.assertEqual(nav.ponged, {})

    def test_b_f2_the_next_intent_crosses_it_from_neither_side_until_news_or_rest(self):
        """B-F2. The next walk from where B-F1 ended crosses the edge from NEITHER side: it wanders the map it stands on.
        After something new anywhere (`stamp`), or `PONG_REST` frames, the edge is an option again."""
        from ai_player.brain.explore import candidates
        from ai_player.brain.goals import travel_intent
        from ai_player.gates.test_world import drive as drive_world
        from ai_player.brain.explore import WEIGHTS
        game, nav, world, notes, outcome = self.pong(1, crop=False)
        self.assertTrue(outcome.startswith("stuck: ping-pong: the edge "), outcome)
        stopped, stamp = game.frame, world.stamp()
        since, decided = len(world.transitions), len(notes.records)
        again = drive_world(nav.run(travel_intent(None, "Story", 20000, lambda look_: False), "again"), 200_000)
        self.assertTrue(again.startswith("stuck: nothing new"), again)
        self.assertEqual(world.stamp(), stamp)  # nothing new seen anywhere: the arm is what it claims
        self.assertEqual(self.crossings(world, since), [])  # FAULT (17ed7794): back and forth again
        kinds = {r["extra"].get("kind") for r in notes.records[decided:] if r["decision"] == "decide"}
        self.assertIn("wander", kinds)
        self.assertNotIn("back", kinds)
        from ai_player.brain.navigator import PONG_REST  # (imported here: the FAULT arm, 17ed7794, has none)
        nav.excluded = {}
        look = replace(game.look(), frame=stopped + 1)
        weights = WEIGHTS["Story"]

        def over_the_edge(seen) -> list:
            memory = world.here()
            return [t for t in candidates(nav, seen, weights) if t.exit is None and memory.outside(t.tile)]

        self.assertEqual(over_the_edge(look), [])
        self.assertEqual(over_the_edge(replace(look, frame=stopped + PONG_REST - 1)), [])
        self.assertNotEqual(over_the_edge(replace(look, frame=stopped + PONG_REST)), [])  # FAULT half: no rest kept
        world.tiles_learned += 1
        self.assertNotEqual(over_the_edge(look), [])  # something new seen anywhere: worth a try again
        world.tiles_learned -= 1
        nav.story_moved()
        self.assertEqual(nav.ponged, {})  # the story moved on: forgotten with the warps'

    def test_b_f3_with_the_edge_ponged_the_fallback_takes_a_refused_way_back_else_wanders(self):
        """B-F3 (the critic's F1, the fallback NAMED, not changed): with the edge ponged, a walk going somewhere has
        nothing it keeps (`keeps_going` refuses the way back into a house), so `travel_intent` falls back to
        `choose_target`, which re-runs the candidates (the edge still dropped) WITHOUT `keeps_going`: it takes the way back
        into the house where something is left, before it would wander. Without the house: a wander.
        Which half discriminates, MEASURED (revert_step5 G420-G422, G426): without the house the walk takes the road back
        across the edge, "seen all of" (the FAULT half); WITH the house it takes the house under those mutants too, because
        `candidates`' step-4 rule (`not_back_to_seen_all`) already drops a way back to a map seen all of while a way back
        leads somewhere with something left. The house half is therefore the named fallback pinned, not a test of the
        drop. At 17ed7794 both halves fail at the setup (no stop: "stuck: nothing new")."""
        from dataclasses import replace as replace_fact
        from ai_player.brain.goals import travel_intent
        for house in (True, False):
            with self.subTest(house=house):
                game, nav, world, _, outcome = self.pong(1)
                self.assertTrue(outcome.startswith("stuck: ping-pong: the edge "), outcome)
                memory, key = world.here(), world.current
                door = None
                if house:
                    door = next(xy for xy, fact in sorted(memory.tiles.items()) if fact.blocked and not memory.outside(xy)
                                and memory.passable((xy[0], xy[1] + 1)) and not memory.outside((xy[0], xy[1] + 1)))
                    memory.tiles[door] = replace_fact(memory.tiles[door], door=True)
                    inside = MapMemory("9:9", "TOWN_HOUSE", "TOWN_HOUSE")
                    inside.visits[(1, 1)] = 1
                    inside.tiles[(1, 1)] = TileFact(False, False, False, False, None, False, False, 3, "NORMAL", 0, (1, 1))
                    world.maps["9:9"] = inside
                    world.warps[f"{key}|{door[0]},{door[1]}"] = {"to": "9:9", "arrival": [1, 1], "direction": "up",
                                                                 "uses": 1, "by": "ai", "first": 1, "last": 1}
                    self.assertGreater(world.promise("9:9"), 0)
                    for name, (_, frame) in list(nav.ponged.items()):  # still ponged: the house is the fixture's, not news
                        nav.ponged[name] = (world.stamp(), frame)
                nav.excluded = {}
                chosen = travel_intent(None, "Story", 2400, lambda look_: False).choose(nav, game.look())
                if house:
                    self.assertEqual((chosen.kind, chosen.exit), ("back", door), chosen)
                else:
                    self.assertEqual(chosen.kind, "wander", chosen)

    def test_b_c1_crossings_with_news_between_are_no_ping_pong(self):
        """B-C1 (the critic's F9, non-vacuous): a town and a route wider than the view, the walk sent across their edge at
        x 3, 12, 21, 30 and 37 in turn: the town's top edge is crossed 3 times, with new tiles seen between its second and
        third crossing. No stop, and the walk is the earlier brains' (`ponged` None) step for step."""
        from ai_player.brain.navigator import Intent
        from ai_player.gates.test_world import GridGame, drive as drive_world, rig
        wide = {"TOWN": ["#" + "." * 38 + "#"] * 3 + ["#" * 40], "ROUTE": ["#" * 40] + ["#" + "." * 38 + "#"] * 2}
        links = {("TOWN", "up"): ("ROUTE", (0, 3)), ("ROUTE", "down"): ("TOWN", (0, -3))}
        runs = []
        for ponged in (None, {}):
            game = GridGame(wide, ("TOWN", (3, 1)), links=links)
            hands, nav, world, notes, _ = rig(game)
            nav.ponged = ponged
            learned: dict[int, int] = {}  # frame -> tiles learned by then (the novelty a new tile is)
            hands.watchers.append(lambda look_, world=world, learned=learned: learned.__setitem__(look_.frame,
                                                                                                  world.tiles_learned))
            plan = [3, 12, 21, 30, 37]

            def choose(navigator, look_, plan=plan, game=game):
                if not plan:
                    return None
                x = plan.pop(0)
                return Target("road", (x, -1) if game.map == "TOWN" else (x, 3), "across")

            outcome = drive_world(nav.run(Intent("across", 20000, choose, lambda look_: False), "across"), 200_000)
            runs.append((outcome, list(game.trail), [(t.source, t.direction, t.frame) for t in self.crossings(world)],
                         learned))
        (plain, trail, crossed, learned), (kept, trail2, crossed2, _) = runs
        self.assertTrue(plain.startswith("stuck: nothing left to try"), plain)
        self.assertEqual((kept, trail2, crossed2), (plain, trail, crossed))  # FAULT (a stop that ignores news): stopped
        town_up = [frame for source, direction, frame in crossed if direction == "up"]
        self.assertEqual(len(town_up), 3)  # non-vacuous: the same edge from the same side 3 times ...
        before_third = max(frame for frame in learned if frame < town_up[2])
        self.assertGreater(learned[before_third], learned[town_up[1]], (town_up, learned[town_up[1]]))  # ... news between

    def test_b_c2_the_earlier_brains_are_unchanged(self):
        """B-C2. `ponged` None (every brain before the play brain): B-F1's fixture as at 17ed7794, measured there with the
        session's bf1_probe.py: "stuck: nothing new" after 72 crossings (seed 1) and 84 (seed 3), nothing kept."""
        for seed, crossings in ((1, 72), (3, 84)):
            for brain in ("explore", "travel"):
                with self.subTest(seed=seed, brain=brain):
                    _, nav, world, _, outcome = self.pong(seed, ponged=False, brain=brain)
                    self.assertTrue(outcome.startswith("stuck: nothing new"), outcome)
                    self.assertEqual(len(self.crossings(world)), crossings)
                    self.assertIsNone(nav.ponged)

    def test_b_c3_a_ponged_edge_on_a_known_route_to_the_goal_is_still_taken(self):
        """B-C3 (the critic's F6): the roads past a ponged edge are dropped, but when that edge is the first hop of a known
        route toward the goal, its "route" target is kept: a known way toward the goal is always an option."""
        from ai_player.brain.explore import WEIGHTS, candidates
        game, nav, world, _, outcome = self.pong(1)
        self.assertTrue(outcome.startswith("stuck: ping-pong: the edge "), outcome)
        other = self.crossings(world)[-1].source
        nav.excluded = {}
        look = game.look()
        memory = world.here()
        roads = [t for t in candidates(nav, look, WEIGHTS["Story"]) if memory.outside(t.tile)]
        self.assertEqual(roads, [])
        toward = [t for t in candidates(nav, look, WEIGHTS["Story"], lambda memory_, key: key == other)
                  if memory.outside(t.tile)]
        self.assertTrue(toward and {t.kind for t in toward} == {"route"}, toward)  # FAULT half: routes dropped too


def ch_proofs(upto_id: str | None, skip_optional: bool = True) -> dict[str, int]:
    """(chapter 5, 2026-11-01) The marks of a story played up to `upto_id` (EXCLUDED; None: every milestone): each earlier
    milestone's flags 1, trainers' defeated flags 1, vars at their `at_least`, read from `milestones.json`; every other
    mark 0 (the whole table, as the eyes report it). An optional milestone's proofs are left out unless asked."""
    out = {name: 0 for name, _ in MILESTONE_FLAGS}
    out.update({name: 0 for name, _ in MILESTONE_VARS})
    for raw in KNOWLEDGE["milestones"]:
        if raw["id"] == upto_id:
            return out
        if raw["optional"] and skip_optional:
            continue
        out.update({name: 1 for name in raw["done"]["flags"]})
        out.update({f"TRAINER_{name}": 1 for name in raw["done"]["trainers"]})
        for name, info in raw["done"]["variables"].items():
            out[name] = max(out[name], info["at_least"])
    if upto_id is not None:
        raise KeyError(upto_id)
    return out


class Chapter5Tests(unittest.TestCase):
    """(2026-11-01) CHAPTER 5, RUSTBORO after the badge (`knowledge/milestones.json` entries 20-27, `gates/extract_milestones.py`):
    each rule has a FAULT half (the proof or step missing / the old shape) and a CONTROL half (the real data)."""

    CH5 = ["ch5_stolen_goods", "ch5_goods_employee", "ch5_rusturf_grunt", "ch5_return_goods", "ch5_devon_corp",
           "ch5_pokenav_tutorial", "ch5_rival_meet", "ch5_rival_battle"]
    OPTIONAL = {"ch5_goods_employee", "ch5_rival_battle"}

    def test_the_eight_follow_the_badge_in_this_order(self):
        story = load_story("BOY")
        self.assertEqual([m.id for m in story.milestones[20:]], self.CH5)
        self.assertEqual({m.id for m in story.milestones[20:] if m.optional}, self.OPTIONAL)
        self.assertEqual({m.chapter for m in story.milestones[20:]}, {5})
        self.assertEqual(story.milestones[19].id, "ch4_roxanne")  # chapters 1-4 stay where they were

    def test_the_story_walks_through_the_required_ones_and_skips_the_optional(self):
        story = load_story("BOY")
        required = [i for i in self.CH5 if i not in self.OPTIONAL]
        for milestone_id in required:
            with self.subTest(milestone=milestone_id):
                self.assertEqual(story.current(ch_proofs(milestone_id))[1].id, milestone_id)
        # every required one proven: no milestone is current (the optional two are never required)
        self.assertEqual(story.current(ch_proofs(None)), (len(story.milestones), None))
        # the optional ones are never the current one, even when their own proof is the only one missing
        self.assertEqual(story.current(ch_proofs("ch5_rusturf_grunt"))[1].id, "ch5_rusturf_grunt")  # not ch5_goods_employee
        # FAULT half: the state after the badge alone is ch5_stolen_goods (the first), not the end
        self.assertEqual(story.current(ch_proofs("ch5_stolen_goods"))[1].id, "ch5_stolen_goods")

    def test_a_later_proof_never_makes_up_for_an_earlier_one(self):
        story = load_story("BOY")
        everything = ch_proofs(None)
        broken = dict(everything, RETURNED_DEVON_GOODS=0)  # the goods were never handed back; everything after is set
        self.assertEqual(story.current(broken)[1].id, "ch5_return_goods")
        self.assertEqual(story.current(everything), (len(story.milestones), None))  # CONTROL
        unread = {k: v for k, v in everything.items() if k != "RETURNED_DEVON_GOODS"}  # the mark was not READ at all
        self.assertEqual(story.current(unread)[1].id, "ch5_return_goods")  # an unread proof is never progress

    def test_the_grunt_is_proven_by_his_defeated_flag_too(self):
        story = load_story("BOY")
        grunt = story.milestones[story.index("ch5_rusturf_grunt")]
        self.assertEqual(grunt.trainers, ("GRUNT_RUSTURF_TUNNEL",))
        everything = ch_proofs(None)
        self.assertEqual(story.current(dict(everything, TRAINER_GRUNT_RUSTURF_TUNNEL=0))[1].id, "ch5_rusturf_grunt")  # FAULT
        self.assertEqual(story.current(everything), (len(story.milestones), None))  # CONTROL
        self.assertEqual(story.trainer_levels["GRUNT_RUSTURF_TUNNEL"], (11,))

    def test_stolen_goods_is_proven_by_the_two_states_never_the_flag_that_flips_back(self):
        story = load_story("BOY")
        stolen = story.milestones[story.index("ch5_stolen_goods")]
        self.assertEqual(stolen.flags, ())  # FLAG_DEVON_GOODS_STOLEN is cleared again in RusturfTunnel: no proof
        self.assertEqual(dict(stolen.variables), {"RUSTBORO_CITY_STATE": 2, "RUSTURF_TUNNEL_STATE": 2})
        after = ch_proofs("ch5_stolen_goods")
        self.assertFalse(stolen.done(after))
        self.assertFalse(stolen.done(dict(after, RUSTBORO_CITY_STATE=2)))  # one of the two is not enough
        self.assertTrue(stolen.done(dict(after, RUSTBORO_CITY_STATE=2, RUSTURF_TUNNEL_STATE=2)))

    def test_the_pokenav_scene_is_not_passed_by_the_flags_set_before_its_menu(self):
        """The scientist's script sets HAS_MATCH_CALL and ADDED_MATCH_CALL_TO_POKENAV BEFORE the forced START menu and
        ROUTE104_STATE 1 at its very start; only VAR_RUSTBORO_CITY_STATE 7 (after the PokeNAV was used) proves it."""
        story = load_story("BOY")
        before_menu = dict(ch_proofs("ch5_pokenav_tutorial"), RUSTBORO_CITY_STATE=6, HAS_MATCH_CALL=1,
                           ADDED_MATCH_CALL_TO_POKENAV=1, ROUTE104_STATE=1)
        self.assertEqual(story.current(before_menu)[1].id, "ch5_pokenav_tutorial")  # FAULT: flags without the state
        self.assertEqual(story.current(dict(before_menu, RUSTBORO_CITY_STATE=7))[1].id, "ch5_rival_meet")  # CONTROL
        pokenav = story.milestones[story.index("ch5_pokenav_tutorial")]
        self.assertIn("INTERACTIVE", json.dumps(KNOWLEDGE["milestones"][story.index("ch5_pokenav_tutorial")]["note"]))
        # the forced menus are played by the SCREEN's skill (`skills/instructed.py`, 2026-11-05), never by a step of the story
        self.assertEqual([s.do for s in pokenav.steps], ["follow"])

    def test_the_rival_is_met_on_either_road_the_route_104_variant_included(self):
        """Rustboro's RivalTrigger0-7 set MET_RIVAL_RUSTBORO, ENABLE_RIVAL_MATCH_CALL and STATE 8; Route 104's second chance
        (a different script) sets ENABLE_RIVAL_MATCH_CALL and STATE 8 and never MET_RIVAL_RUSTBORO. FAULT: the draft's proof
        (with that flag) would never fire on the Route 104 road; CONTROL: the real proof fires on both."""
        story = load_story("BOY")
        meet = story.milestones[story.index("ch5_rival_meet")]
        before = ch_proofs("ch5_rival_meet")
        route104_road = dict(before, ENABLE_RIVAL_MATCH_CALL=1, RUSTBORO_CITY_STATE=8)
        self.assertTrue(meet.done(route104_road))
        self.assertEqual(story.current(route104_road), (len(story.milestones), None))
        drafted = replace(meet, flags=(*meet.flags, "MET_RIVAL_RUSTBORO"))
        self.assertFalse(drafted.done({**route104_road, "MET_RIVAL_RUSTBORO": 0}))  # FAULT: stuck for good
        self.assertTrue(meet.done({**route104_road, "MET_RIVAL_RUSTBORO": 1}))  # the Rustboro road passes too
        self.assertFalse(meet.done(dict(before, RUSTBORO_CITY_STATE=8)))  # the state alone: not met (no match call flag)
        self.assertFalse(meet.done(dict(before, ENABLE_RIVAL_MATCH_CALL=1, RUSTBORO_CITY_STATE=7)))

    def test_the_rival_battle_is_optional_and_its_trainers_have_their_levels(self):
        story = load_story("BOY")
        battle = story.milestones[story.index("ch5_rival_battle")]
        meet = story.milestones[story.index("ch5_rival_meet")]
        self.assertTrue(battle.optional and not meet.optional)
        for name in ("MAY", "BRENDAN"):
            for starter in ("TREECKO", "TORCHIC", "MUDKIP"):
                self.assertEqual(story.trainer_levels[f"{name}_RUSTBORO_{starter}"], (13, 15))
        self.assertEqual((meet.fight_levels, battle.fight_levels), ((13, 15), (13, 15)))
        self.assertTrue(meet.fight_named and battle.fight_named)

    def rival_goal(self, level: int, train_off: bool = False, known=("RUSTBORO_CITY", "ROUTE104"), prep_steps=None):
        mgr = manager("Story", train_off=train_off)
        world = world_with(*known, current="RUSTBORO_CITY")
        observation = look(ch_proofs("ch5_rival_meet"), party=[mon(level, hp=40, max_hp=40)], const="RUSTBORO_CITY")
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertEqual(milestone.id, "ch5_rival_meet")
        if prep_steps is not None:
            mgr.next_goal(observation, world, milestone, index)
            mgr.memory.fight_prep["ch5_rival_meet"]["steps"] = prep_steps
        return mgr.next_goal(observation, world, milestone, index)

    def test_it_trains_for_the_rival_before_it_crosses_the_trigger_row(self):
        """F8's decision: the named fight sits on ch5_rival_meet (the scene starts there), so the train-before-a-fight errand
        applies, as it does for the first rival. FAULT: under train_off it goes straight; CONTROL: a fresh party trains."""
        trains = self.rival_goal(level=9)
        self.assertEqual(trains.kind, "train")
        self.assertIn(f"target L{15 + ERRANDS['Story'].train_margin}", trains.reason)
        self.assertEqual(self.rival_goal(level=9, train_off=True).kind, "go")
        ready = self.rival_goal(level=20, prep_steps=ERRANDS["Story"].train_min_steps)
        self.assertEqual((ready.kind, ready.map), ("go", "ROUTE104"))

    def test_the_way_south_is_a_place_it_has_been_to_never_a_guess(self):
        """`go ROUTE104` has no `told` words: only a map the AI has BEEN to is headed for (it came from there in chapter 3).
        FAULT: not been there -> it explores, never walks to a map it was not told of."""
        known = self.rival_goal(level=20, train_off=True)
        self.assertEqual((known.kind, known.map), ("go", "ROUTE104"))
        unknown = self.rival_goal(level=20, train_off=True, known=("RUSTBORO_CITY",))
        self.assertEqual((unknown.kind, unknown.map), ("go", None))

    def test_the_tunnel_is_only_walked_to_once_it_is_said(self):
        mgr = manager("Story", train_off=True)
        world = world_with("RUSTBORO_CITY", "ROUTE116", current="RUSTBORO_CITY")
        observation = look(ch_proofs("ch5_rusturf_grunt"), party=[mon(15, hp=40, max_hp=40)], const="RUSTBORO_CITY")
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertEqual(milestone.id, "ch5_rusturf_grunt")
        self.assertEqual(mgr.next_goal(observation, world, milestone, index).map, None)  # nobody said 'tunnel': explores
        world.heard = {"That shady character, I think he took off towards the tunnel over there."}
        mgr = manager("Story", train_off=True)
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.map), ("go", "RUSTURF_TUNNEL"))

    def test_chapters_1_to_4_are_untouched(self):
        """The first 20 entries, the gendered maps, the looks and the first 14 trainers are what they were before chapter 5:
        their digests were measured on 39b2612f (the commit before chapter 5; the same digests of the 28-milestone file
        match). A deliberate change to chapters 1-4 updates these two constants, in the open."""
        import hashlib

        def digest(parts) -> str:
            return hashlib.sha256(json.dumps(parts, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

        self.assertEqual(digest(KNOWLEDGE["milestones"][:20]),
                         "24ce2d9509b8e2d1c73b9c4b5e7b73324e847f32c2e40a455d3e4a01d9ebd2bd")
        # (2026-11-05, the tunnel grunt's step) chapter 5 added a 13th look (`aqua_member`, appended): the pin digests the
        # TWELVE looks chapters 1-4 had, BY NAME, so it still says those are what they were (the same digest as before)
        old_looks = {name: KNOWLEDGE["looks"][name] for name in OLD_LOOKS}
        self.assertEqual(digest([KNOWLEDGE["gendered_maps"], old_looks, list(KNOWLEDGE["trainers"].items())[:14]]),
                         "de26718a062c5f1e5a47b2ffe3b90f78fbe7fe90388c533899690b6b9d23e302")
        self.assertNotEqual(digest(KNOWLEDGE["milestones"][:21]), "24ce2d9509b8e2d1c73b9c4b5e7b73324e847f32c2e40a455d3e4a01d9ebd2bd")  # FAULT half: the digest does see a 21st entry
        # FAULT half of the looks' pin: the whole looks block (13 since the grunt's step) no longer gives that digest
        self.assertNotEqual(digest([KNOWLEDGE["gendered_maps"], KNOWLEDGE["looks"], list(KNOWLEDGE["trainers"].items())[:14]]),
                            "de26718a062c5f1e5a47b2ffe3b90f78fbe7fe90388c533899690b6b9d23e302")


#: (2026-11-05) The twelve looks of chapters 1-4, in the order the file had them (`test_chapters_1_to_4_are_untouched`).
OLD_LOOKS = ("clock", "pokemon_center_door", "mart_door", "gym_door", "nurse", "clerk", "birchs_bag", "rival",
             "rivals_poke_ball", "norman", "mom", "roxanne")
#: The page the DEVON employee says (`RustboroCity_Text_ShadyCharacterTookOffTowardsTunnel`): the step's own word 'tunnel'.
TUNNEL_LINE = "That shady character, I think he took off towards the tunnel over there."


def _grunt_data(talk_step: bool) -> dict:
    """The milestones as the file has them (`talk_step`, today's) or as e70a8469 had them (the step `follow`, no Aqua look):
    the FAULT halves run the real goal manager on the old data."""
    import copy

    data = copy.deepcopy(KNOWLEDGE)
    if not talk_step:
        data["looks"].pop("aqua_member", None)
        grunt = next(m for m in data["milestones"] if m["id"] == "ch5_rusturf_grunt")
        grunt["steps"] = [{"do": "go", "map": "RUSTURF_TUNNEL", "told": "tunnel"}, {"do": "follow"}]
    return data


class TunnelGruntTests(unittest.TestCase):
    """(2026-11-05) The chapter-5 probe's second stop: `ch5_rusturf_grunt`'s `follow` step steered nowhere, and 2 of 3 runs
    stood beside the TEAM AQUA grunt in RUSTURF TUNNEL and never talked to him. The step is now `talk` to a person who LOOKS
    like a TEAM AQUA member (`looks.aqua_member`, gfx 117/118), the general mechanism the rival, NORMAN and ROXANNE use. No
    AI-player code changed: each FAULT half runs the SAME goal manager on e70a8469's data (`_grunt_data(False)`)."""

    GRUNT = person(x=14, y=10, gfx=117, local_id=6)  # 4 tiles east of the player (the grunt at (14,5) from (10,5))
    PEEKO = person(x=14, y=9, gfx=211, local_id=7)  # PEEKO, the WINGULL, above him
    THIEF = person(x=12, y=10, gfx=117, local_id=5)  # an Aqua figure on RUSTBORO CITY (the look counts on its step's map only)

    def goal(self, data, const="RUSTURF_TUNNEL", objects=(), heard=(TUNNEL_LINE,), sighting=None, hp=79,
             personality="Trainer", errands_off=True):
        from ai_player.knowledge.story import Story

        state = PersonalityState(personality, random.Random(1), drift_on=False)
        mgr = GoalManager(Story(data, "BOY"), state, random.Random(1), errands_off=errands_off)
        mgr.memory.known_before = set()
        mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()
        world = world_with("RUSTBORO_CITY", "ROUTE116", "RUSTURF_TUNNEL", current=const, heard=heard)
        if sighting is not None:
            mgr.memory.sightings[("aqua_member", world.current)] = sighting
        observation = look(ch_proofs("ch5_rusturf_grunt"), party=[mon(26, hp=hp, max_hp=79)], const=const, objects=objects)
        index, milestone = mgr.milestone(observation, visited_in(world))
        self.assertEqual(milestone.id, "ch5_rusturf_grunt")
        return mgr.next_goal(observation, world, milestone, index), mgr, world, observation, milestone

    def test_f1_the_step_is_talk_to_the_aqua_member(self):
        grunt = next(m for m in KNOWLEDGE["milestones"] if m["id"] == "ch5_rusturf_grunt")
        self.assertEqual([(s["do"], s.get("look")) for s in grunt["steps"]], [("go", None), ("talk", "aqua_member")])
        self.assertEqual(load_story("BOY").looks["aqua_member"].gfx, (117, 118))
        old = next(m for m in _grunt_data(False)["milestones"] if m["id"] == "ch5_rusturf_grunt")
        self.assertEqual([s["do"] for s in old["steps"]], ["go", "follow"])  # FAULT half: the old shape

    def test_f2_in_the_tunnel_the_grunt_on_screen_is_talked_to(self):
        goal = self.goal(KNOWLEDGE, objects=(self.GRUNT, self.PEEKO))[0]
        self.assertEqual((goal.kind, goal.key, goal.target.local_id, goal.target.graphics_id),
                         ("talk", "talk:aqua_member", 6, 117))
        self.assertIn("TEAM AQUA member", goal.reason)
        self.assertEqual(self.goal(_grunt_data(False), objects=(self.GRUNT, self.PEEKO))[0].kind, "follow")  # FAULT half

    def test_f3_nobody_on_screen_it_finds_him_on_this_map(self):
        goal = self.goal(KNOWLEDGE)[0]
        self.assertEqual((goal.kind, goal.key), ("find", "find:aqua_member"))
        self.assertEqual(self.goal(_grunt_data(False))[0].kind, "follow")  # FAULT half

    def test_f4_a_remembered_sighting_is_sought(self):
        goal = self.goal(KNOWLEDGE, sighting=(14, 5, 900))[0]
        self.assertEqual((goal.kind, goal.key, goal.tile), ("seek", "seek:aqua_member", (14, 5)))
        self.assertEqual(self.goal(_grunt_data(False), sighting=(14, 5, 900))[0].kind, "follow")  # FAULT half

    def test_f5_chat_never_picks_the_story_person(self):
        """The chat errand leaves alone whoever LOOKS like the current step's person (`story_gfx`). FAULT half: on the old
        data the step owns nobody and chat picks the grunt."""
        from ai_player.knowledge.story import Story

        picks = {}
        for label, data in (("now", KNOWLEDGE), ("old", _grunt_data(False))):
            mgr = GoalManager(Story(data, "BOY"), PersonalityState("Trainer", random.Random(1), drift_on=False),
                              random.Random(1))  # fresh: no decision drew a chat yet
            world = world_with("RUSTBORO_CITY", "ROUTE116", "RUSTURF_TUNNEL", current="RUSTURF_TUNNEL", heard=(TUNNEL_LINE,))
            observation = look(ch_proofs("ch5_rusturf_grunt"), party=[mon(26, hp=79, max_hp=79)], const="RUSTURF_TUNNEL",
                               objects=(self.GRUNT,))
            milestone = mgr.milestone(observation, visited_in(world))[1]
            step = mgr.story_step(observation, world, milestone)
            own = mgr.story.looks.get(step.look) if step is not None and step.look else None
            mgr.memory.curious_since = -10 ** 7  # boredom saturated: the chat's odds at their cap
            pick = mgr._chat_person(observation, world, observation.frame, own.gfx if own is not None else ())
            picks[label] = None if pick is None else (pick[0].local_id, pick[0].graphics_id)
        self.assertEqual(picks, {"now": None, "old": (6, 117)})

    def test_f5b_the_decision_hands_the_steps_look_to_the_chat(self):
        """F5 through `next_goal` (errands on, boredom at its cap, the grunt beside the player, seed 1): the story's talk,
        never a chat with him. The call-site mutant (the chat asked with no story gfx) chats with him on this seed
        (measured offline: s53/ch5stops/f5b_probe.py, seed 1)."""
        from ai_player.knowledge.story import Story

        mgr = GoalManager(Story(KNOWLEDGE, "BOY"), PersonalityState("Trainer", random.Random(1), drift_on=False),
                          random.Random(1))
        mgr.memory.known_before = set()
        mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()
        mgr.memory.curious_since = -10 ** 7
        world = world_with("RUSTBORO_CITY", "ROUTE116", "RUSTURF_TUNNEL", current="RUSTURF_TUNNEL", heard=(TUNNEL_LINE,))
        observation = look(ch_proofs("ch5_rusturf_grunt"), party=[mon(26, hp=79, max_hp=79)], const="RUSTURF_TUNNEL",
                           objects=(person(x=11, y=10, gfx=117, local_id=6),))
        index, milestone = mgr.milestone(observation, visited_in(world))
        goal = mgr.next_goal(observation, world, milestone, index)
        self.assertEqual((goal.kind, goal.key), ("talk", "talk:aqua_member"))

    def test_c1_a_wingull_is_never_the_aqua_member(self):
        goal = self.goal(KNOWLEDGE, objects=(self.PEEKO,))[0]
        self.assertEqual((goal.kind, goal.key), ("find", "find:aqua_member"))

    def test_c2_the_look_counts_on_its_steps_map_only(self):
        for data in (KNOWLEDGE, _grunt_data(False)):
            goal = self.goal(data, const="RUSTBORO_CITY", objects=(self.THIEF,))[0]
            self.assertEqual((goal.kind, goal.map), ("go", "RUSTURF_TUNNEL"))

    def test_c3_c4_seeing_him_is_enough_and_the_word_keeps_it_in_the_tunnel(self):
        goal, mgr, world, observation, milestone = self.goal(KNOWLEDGE, objects=(self.GRUNT, self.PEEKO), heard=())
        self.assertEqual(goal.kind, "talk")  # C3: never told 'tunnel', but he is on screen
        self.assertFalse(mgr._story_here(mgr.story_step(observation, world, milestone), world))
        _, mgr, world, observation, milestone = self.goal(KNOWLEDGE)
        self.assertTrue(mgr._story_here(mgr.story_step(observation, world, milestone), world))  # C4: 'tunnel' heard

    def test_c8_a_hurt_party_heals_before_the_talk_a_healthy_one_talks(self):
        """The behaviour change the design names: a known fight is next INSIDE the tunnel now, so the heal before it
        applies there (as the go phase's did). The grunt's level is known only from a trainer SEEN on the milestone's maps
        (ROUTE 116, L9), training done, a POKéMON CENTER known in RUSTBORO. Pinned both ways (85 % heals, 95 % talks); the
        old data never heals here (its `follow` is no fight step)."""
        from ai_player.knowledge.story import Story

        kinds = {}
        for label, data in (("now", KNOWLEDGE), ("old", _grunt_data(False))):
            for share in (85, 95):
                state = PersonalityState("Trainer", random.Random(1), drift_on=False)
                mgr = GoalManager(Story(data, "BOY"), state, random.Random(1), errands_off=True)
                mgr.memory.known_before = set()
                mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()
                world = world_with("RUSTBORO_CITY", "ROUTE116", "RUSTURF_TUNNEL", current="RUSTURF_TUNNEL",
                                   heard=(TUNNEL_LINE,), center_from="RUSTBORO_CITY")
                mgr.memory.seen_levels["ROUTE116"] = 9
                observation = look(ch_proofs("ch5_rusturf_grunt"), party=[mon(26, hp=share, max_hp=100)],
                                   const="RUSTURF_TUNNEL", objects=(self.GRUNT,))
                index, milestone = mgr.milestone(observation, visited_in(world))
                mgr.memory.fight_prep[milestone.id] = {"ready": True, "steps": 999, "sessions": 1}
                kinds[(label, share)] = mgr.next_goal(observation, world, milestone, index).kind
        self.assertEqual(kinds, {("now", 85): "heal", ("now", 95): "talk", ("old", 85): "follow", ("old", 95): "follow"})


# ------------------------------------------------------------------------------------------------ the instructed choice
#: (2026-11-05) Rustboro's MATCH CALL tutorial as the eyes read it live (the C1 probe's end state and the recon of
#: s53/ch5stops/menu): the scientist's pages (`data/maps/RustboroCity/scripts.inc`), the forced START menu, the POKéNAV's
#: main menu, MR. STONE's call (`data/text/match_call.inc` MatchCall_Text_MrStone1), the loop's page and the page after.
SCENE = ["I’ve been developing an added feature for the POKéNAV…", "And it turned out great!",
         "Milo, may I see that POKéNAV? The one our PRESIDENT gave you?", "There you go, Milo!",
         "I added a new feature named MATCH CALL to your POKéNAV.",
         "Using the MATCH CALL feature, you can chat with people who have been registered in your POKéNAV.",
         "Milo, our PRESIDENT STONE should be registered in your POKéNAV.", "Test it out. Please give our PRESIDENT a call."]
FORCED_START = ("POKéDEX", "POKéMON", "BAG", "POKéNAV", "", "SAVE", "OPTION", "EXIT")
POKENAV_MAIN = ("HOENN MAP", "CONDITION", "MATCH CALL", "SWITCH OFF")
CALL_PAGES = ["MR. STONE: Oh? Milo!", "Since you called me, the POKéNAV must be working properly!",
              "Other people will be registered, so try calling them up, too!", "Good! Good! You seem to be quite happy!",
              "Hm… How could I know that?", "It’s because I’m looking down at you from my office window!",
              "Wahahaha! See you again!"]
PLEASE_SELECT = "Please select the POKéNAV."
BACK_TO_WORK = "Okay, I’d better get back to work. Please take care, Milo!"


class _Tutorial:
    """The tutorial, screen by screen, as the decomp plays it: the forced START menu (every choice but POKéNAV, and B, loop
    back under "Please select the POKéNAV."), the POKéNAV opening, its main menu (A only on MATCH CALL, B refused until MR.
    STONE was called), the MATCH CALL list (B refused until then), the entry's CALL / CANCEL, the call's pages, the call-exit
    wait, then back out and "Okay, I'd better get back to work.". `app_in_field` (FAULT G3's discriminator): the call's
    pages read as FIELD pages. `call_pages`: what MR. STONE says. Every press moves it as `press` says; frames tick it."""

    OPEN_FRAMES = 30

    def __init__(self, scene=tuple(SCENE), call_pages=tuple(CALL_PAGES), app_in_field=False, accepts=True, bounce=False,
                 loop_always=False, stuck_opening=False, deaf=False):
        self.state, self.cursor, self.page, self.index = "forced", 0, None, 0
        self.buffer = "¶".join(scene)
        self.call_pages, self.app_in_field, self.accepts = list(call_pages), app_in_field, accepts
        self.after_call, self.calls, self.wait, self.chosen = False, 0, 0, []
        # the bounds' fixtures: a B that sends the list and the menu back and forth (`bounce`), a forced menu that loops
        # back whatever is chosen (`loop_always`), a POKéNAV that never finishes opening (`stuck_opening`), a main menu
        # that ignores A (`deaf`)
        self.bounce, self.loop_always, self.stuck_opening, self.deaf = bounce, loop_always, stuck_opening, deaf

    def press(self, button: str) -> None:
        state = self.state
        if state == "forced":
            if button in ("Down", "Up"):
                self.cursor = max(0, min(len(FORCED_START) - 1, self.cursor + (1 if button == "Down" else -1)))
            elif button in ("A", "B"):
                self.chosen.append(("forced", FORCED_START[self.cursor] if button == "A" else "B"))
                if button == "A" and self.cursor == 3 and not self.loop_always:
                    self.state, self.wait = "opening", self.OPEN_FRAMES
                else:
                    self.state, self.page, self.buffer = "field_page", PLEASE_SELECT, PLEASE_SELECT
        elif state == "field_page" and button == "A":
            self.state, self.cursor = ("forced", 0) if self.page == PLEASE_SELECT else ("free", 0)
        elif state == "menu" and self.bounce and button == "B":
            self.state, self.cursor = "list", 0
        elif state == "list" and self.bounce and button == "B":
            self.state, self.cursor = "menu", 0
        elif state == "menu" and self.accepts:
            if button in ("Down", "Up"):
                self.cursor = max(0, min(3, self.cursor + (1 if button == "Down" else -1)))
            elif button == "A" and self.deaf:
                pass
            elif button == "A" and POKENAV_MAIN[self.cursor] == "MATCH CALL":
                self.chosen.append(("menu", "MATCH CALL"))
                self.state, self.wait = "opening_list", self.OPEN_FRAMES
            elif (button == "B" or (button == "A" and self.cursor == 3)) and self.after_call:
                self.chosen.append(("menu", "B" if button == "B" else "SWITCH OFF"))
                self.state, self.wait = "leaving", self.OPEN_FRAMES
        elif state == "list":
            if button == "A":
                self.chosen.append(("list", "MR. STONE"))
                self.state, self.cursor = "options", 0
            elif button == "B" and self.after_call:
                self.chosen.append(("list", "B"))
                self.state, self.cursor = "menu", 2
        elif state == "options":
            if button in ("Down", "Up"):
                self.cursor = max(0, min(1, self.cursor + (1 if button == "Down" else -1)))
            elif button == "A" and self.cursor == 0:
                self.chosen.append(("options", "CALL"))
                self.state, self.index = "call", 0
                self.calls += 1
            elif button in ("A", "B"):
                self.state, self.cursor = "list", 0
        elif state == "call" and button == "A":
            self.index += 1
            if self.index >= len(self.call_pages):
                self.state = "call_end"
        elif state == "call_end" and button in ("A", "B"):
            self.state, self.cursor, self.after_call = "list", 0, True

    def tick(self) -> None:
        if self.wait > 0 and not (self.stuck_opening and self.state == "opening"):
            self.wait -= 1
            if self.wait == 0:
                if self.state == "opening":
                    self.state, self.cursor = "menu", 0
                elif self.state == "opening_list":
                    self.state, self.cursor = "list", 0
                elif self.state == "leaving":
                    self.state, self.page = "field_page", BACK_TO_WORK

    def look(self, frame: int) -> Observation:
        from ai_player.eyes.observation import MenuView

        base = look(ch_proofs("ch5_pokenav_tutorial"), const="RUSTBORO_CITY", frame=frame)
        base = replace(base, player=replace(base.player, name="Milo"))
        state, ui, text, waits, game, scene = self.state, None, None, False, "UNKNOWN", "the POKéNAV"
        if state == "forced":
            ui, text, game, scene = MenuView("multichoice", FORCED_START, self.cursor, True), self.buffer, "OVERWORLD", None
        elif state == "field_page":
            text, waits, game, scene = self.page, True, "OVERWORLD", None
        elif state == "menu":
            ui = MenuView("pokenav_menu", POKENAV_MAIN, self.cursor, self.accepts)
        elif state == "list":
            ui = MenuView("pokenav_list", ("MR. STONE",), 0, True)
        elif state == "options":
            ui = MenuView("pokenav_options", ("CALL", "CANCEL"), self.cursor, True)
        elif state == "call":
            text, waits = self.call_pages[self.index], True
            game = "OVERWORLD" if self.app_in_field else "UNKNOWN"
        elif state == "call_end":
            waits = True
        elif state == "free":
            game, scene = "OVERWORLD", None
        script = state != "free"
        screen = ScreenState(game_state=game, screen="overworld", menu=None, text_box_open=waits, waits_for_button=waits,
                             in_battle=False, wait_reason="text printer 0 CLEAR" if waits else None, ui=ui, text=text,
                             script_running=script, controls_locked=script, scene=scene)
        return replace(base, screen=screen)


class _TutorialControls(_Controls):
    """The brain's `Controls` on `_Tutorial`: a press reaches the game on its first frame; every frame ticks it."""

    def __init__(self, game: _Tutorial) -> None:
        self.game = game

    def wait(self, frames: int):
        for _ in range(frames):
            self.game.tick()
            yield

    def hold(self, button: str, frames: int):
        self.game.press(button)
        for _ in range(frames):
            self.game.tick()
            yield


def tutorial_hands(game, fault_no_instructed=False, misstep=False):
    """Hands on `_Tutorial`, and the play brain's `_story_menu` with its instructed-choice skill watching every look."""
    from ai_player.skills.instructed import Instructed

    eyes = _ScriptEyes(game.look)
    hands = Hands(eyes, _TutorialControls(game), random.Random(1), random.Random(1), None, lambda line: None)
    eyes.hands = hands
    hands.told = []
    hands.say = hands.told.append
    brain = HandsBrain.__new__(HandsBrain)
    brain.options = types.SimpleNamespace(fault_no_instructed=fault_no_instructed)
    brain._instructed = Instructed(misstep=misstep)
    hands.watchers.append(brain._instructed.read_along)
    return hands, brain


def play_scene(hands, brain, rounds: int = 12):
    """What `Navigator.handle` does with a scene (advance; a menu to `on_menu`; a stop said), until the player is free."""
    from ai_player.hands.dialogue import advance, player_free

    for _ in range(rounds):
        outcome = yield from advance(hands, player_free, "a scene")
        if outcome == "done":
            return "free"
        if outcome.startswith("menu:"):
            if (yield from brain._story_menu(hands, outcome[5:], "a scene", "MUDKIP")):
                continue
            return f"stuck: an unexpected {outcome[5:]} on screen"
        return f"stuck: a scene: {outcome}"
    return "rounds"


def buttons(hands) -> list[str]:
    return [entry["button"] for entry in hands.pad.history]


class InstructedTests(unittest.TestCase):
    """(2026-11-05) THE INSTRUCTED CHOICE (`skills/instructed.py`), the chapter-5 probe's first stop: a menu a scene FORCES
    is chosen by the words read. U1 (the dispatch), U5 (the rule on the tutorial's menus), U6 (the bounds), the guards
    G1-G7 each with a FAULT and a CONTROL half (a guard whose FAULT needs the code changed is carried by
    `revert_step5.py`'s mutants), and C1-C3 (the menus chapters 1-4 meet go where they went)."""

    def test_u1_the_forced_menu_and_the_pokenav_are_played_by_the_words(self):
        game = _Tutorial()
        hands, brain = tutorial_hands(game)
        self.assertEqual(drive(play_scene(hands, brain), 200_000), "free")
        self.assertEqual(game.chosen, [("forced", "POKéNAV"), ("menu", "MATCH CALL"), ("list", "MR. STONE"),
                                       ("options", "CALL"), ("list", "B"), ("menu", "B")])
        self.assertEqual(game.calls, 1)
        self.assertEqual(buttons(hands), ["Down", "Down", "Down", "A", "Down", "Down", "A", "A", "A"] + ["A"] * 7
                         + ["A", "B", "B", "A"])
        self.assertTrue(any("'POKéNAV' is named by" in line for line in hands.told))
        # FAULT half: today's code (`_story_menu` returns False on a multichoice): the same stop as the probe, no press
        game = _Tutorial()
        hands, brain = tutorial_hands(game, fault_no_instructed=True)
        self.assertEqual(drive(play_scene(hands, brain), 200_000), "stuck: an unexpected multichoice on screen")
        self.assertEqual((buttons(hands), game.chosen), ([], []))

    def test_u5_the_rule_on_the_tutorials_menus(self):
        from ai_player.skills.instructed import named_option

        def name(options, pages, used=(), own="Milo"):
            index, _ = named_option(options, list(pages), set(used), own)
            return None if index is None else options[index]

        self.assertEqual(name(FORCED_START, SCENE), "POKéNAV")
        self.assertEqual(name(FORCED_START, SCENE + [PLEASE_SELECT]), "POKéNAV")
        self.assertEqual(name(POKENAV_MAIN, SCENE), "MATCH CALL")
        self.assertEqual(name(("MR. STONE",), SCENE), "MR. STONE")
        self.assertEqual(name(("CALL", "CANCEL"), SCENE), "CALL")
        self.assertIsNone(name(("MR. STONE",), SCENE, used={"MR. STONE"}))
        self.assertIsNone(name(POKENAV_MAIN, SCENE, used={"MATCH CALL"}))
        # whole words (a substring rule would find 'call' in "called"; it is REDUNDANT on this scene: a synthetic pair)
        self.assertIsNone(name(("CALL", "CANCEL"), ["Since you called me, it works."]))
        # newest first: the newest page that names something decides (REDUNDANT on this scene: a synthetic pair)
        self.assertEqual(name(("SAVE", "EXIT"), ["Please EXIT now.", "No, SAVE first."]), "SAVE")

    def test_menu1_the_loop_appends_and_the_pokenav_is_still_named(self):
        """Critic MENU-1: a forced menu that comes back under "Please select the POKéNAV." keeps the pages before it, so
        MATCH CALL is still named inside the POKéNAV and the call is made. The live arm L4 is this with the misstep fault.
        FAULT half (the design's replace rule): the single page names nothing on the POKéNAV's main menu."""
        from ai_player.skills.instructed import named_option

        game = _Tutorial()
        hands, brain = tutorial_hands(game, misstep=True)
        self.assertEqual(drive(play_scene(hands, brain), 200_000), "free")
        self.assertEqual(game.chosen[:3], [("forced", "SAVE"), ("forced", "POKéNAV"), ("menu", "MATCH CALL")])
        self.assertEqual(game.calls, 1)
        self.assertEqual(named_option(POKENAV_MAIN, [PLEASE_SELECT], set(), "Milo")[0], None)  # FAULT: replace
        self.assertEqual(named_option(POKENAV_MAIN, SCENE + [PLEASE_SELECT], set(), "Milo")[0], 2)  # CONTROL: append

    def test_menu4_a_stale_message_is_no_instruction_once_the_player_was_free(self):
        """Critic MENU-4: the forced menu stands AFTER `closemessage`, so its words come from the message buffer only for a
        run that began inside the scene. CONTROL: once the player has been free and nothing was read since, the same buffer
        names nothing (no press). FAULT half: the run that began there (no free look) reads it and chooses POKéNAV."""
        from ai_player.skills.instructed import Instructed

        game = _Tutorial()
        hands, brain = tutorial_hands(game)
        free = replace(game.look(0), screen=ScreenState(game_state="OVERWORLD", screen="overworld", menu=None,
                                                        text_box_open=False, waits_for_button=False, in_battle=False))
        brain._instructed.read_along(free)
        self.assertFalse(drive(brain._story_menu(hands, "multichoice", "a scene", "MUDKIP"), 10_000))
        self.assertEqual(buttons(hands), [])
        hands, brain = tutorial_hands(_Tutorial())
        self.assertIsInstance(brain._instructed, Instructed)
        self.assertTrue(drive(brain._story_menu(hands, "multichoice", "a scene", "MUDKIP"), 200_000))
        self.assertEqual(buttons(hands)[:4], ["Down", "Down", "Down", "A"])

    def test_the_transcript_is_the_field_pages_read_since_the_player_was_free(self):
        """The pages the player READ (each once it waits for a press) since the player was last free, in order; cleared
        when the player is free; a page inside an app never (G3's CONTROL); the same page in the field is (its FAULT
        half: what the eyes report decides, so an app whose pages read as the field's would be captured)."""
        from ai_player.skills.instructed import Instructed

        game = _Tutorial()
        skill = Instructed()
        page = game.look(0)
        for text in SCENE[:3]:
            skill.read_along(replace(page, screen=replace(page.screen, ui=None, waits_for_button=True, text=text)))
            skill.read_along(replace(page, screen=replace(page.screen, ui=None, waits_for_button=True, text=text)))
        self.assertEqual(skill.pages, SCENE[:3])
        app = replace(page, screen=replace(page.screen, game_state="UNKNOWN", ui=None, waits_for_button=True,
                                           text="MR. STONE: Oh? Milo!"))
        skill.read_along(app)
        self.assertEqual(skill.pages, SCENE[:3])  # CONTROL: never an app's page
        skill.read_along(replace(app, screen=replace(app.screen, game_state="OVERWORLD")))
        self.assertEqual(skill.pages[-1], "MR. STONE: Oh? Milo!")  # FAULT half: the same page read as the field's
        free = replace(page, screen=ScreenState(game_state="OVERWORLD", screen="overworld", menu=None, text_box_open=False,
                                                waits_for_button=False, in_battle=False))
        skill.read_along(free)
        self.assertEqual((skill.pages, skill.free_seen), ([], True))

    def test_g3_a_page_inside_the_app_never_names_a_menu(self):
        """G3: a call page that names an option of the POKéNAV's main menu ("the HOENN MAP") is conversation: after the call
        the main menu is backed out of (B). FAULT half: the call's pages read as field pages: HOENN MAP is chosen."""
        pages = CALL_PAGES[:-1] + ["Do look at the HOENN MAP sometime!", CALL_PAGES[-1]]
        game = _Tutorial(call_pages=pages)
        hands, brain = tutorial_hands(game)
        self.assertEqual(drive(play_scene(hands, brain), 200_000), "free")
        self.assertNotIn(("menu", "HOENN MAP"), game.chosen)
        self.assertEqual(game.chosen[-1], ("menu", "B"))
        game = _Tutorial(call_pages=pages, app_in_field=True)
        hands, brain = tutorial_hands(game)
        drive(play_scene(hands, brain), 200_000)
        self.assertTrue(any("'HOENN MAP' is named by" in line for line in hands.told))

    def test_g4_each_named_option_is_followed_once(self):
        """G4: after the call, MR. STONE (followed) is named by no NEW option: the list is backed out of, one call made.
        FAULT half: with nothing remembered as followed, the same pages name MR. STONE again (a second call)."""
        from ai_player.skills.instructed import named_option

        self.assertEqual(named_option(("MR. STONE",), SCENE, set(), "Milo")[0], 0)  # FAULT: named again
        self.assertIsNone(named_option(("MR. STONE",), SCENE, {"MR. STONE"}, "Milo")[0])  # CONTROL
        game = _Tutorial()
        hands, brain = tutorial_hands(game)
        drive(play_scene(hands, brain), 200_000)
        self.assertEqual((game.calls, game.chosen.count(("list", "MR. STONE"))), (1, 1))

    def test_g2_the_players_own_name_never_names_an_option(self):
        from ai_player.skills.instructed import named_option

        options = ("SOMEONE'S PC", "MILO'S PC", "LOG OFF")
        pages = ["Milo booted up the PC.", "Which PC should be accessed?"]
        self.assertIsNone(named_option(options, pages, set(), "Milo")[0])  # CONTROL
        self.assertEqual(named_option(options, pages, set(), None)[0], 1)  # FAULT half: the name unknown: MILO'S PC

    def test_g1_g5_a_blank_label_is_never_named_and_two_named_choose_nothing(self):
        from ai_player.skills.instructed import label_words, named_option

        self.assertEqual(label_words("", "Milo"), ())
        self.assertEqual(label_words("MR.", "Milo"), ())
        self.assertEqual(named_option(FORCED_START, ["Test it out. Please give our PRESIDENT a call."], set(), "Milo"),
                         (None, "nothing on it is named by the instruction"))
        index, why = named_option(("MATCH CALL", "HOENN MAP"), ["Use the MATCH CALL or the HOENN MAP."], set(), "Milo")
        self.assertIsNone(index)
        self.assertIn("ambiguous", why)
        self.assertEqual(named_option(("MATCH CALL", "HOENN MAP"), ["Use the MATCH CALL."], set(), "Milo")[0], 0)

    def test_g6_a_grid_is_refused_with_no_press(self):
        """G6 (the eyes' E7: `Task_HandleMultichoiceGridInput` is `multichoice_grid`): a grid is refused, said, no press,
        even when a page names one of its options. FAULT half (E7 reverted: the grid read as a 1-D `multichoice`): the
        named option is walked to with Up/Down on a 2-D cursor."""
        from ai_player.eyes.observation import MenuView

        def grid(kind):
            game = _Tutorial(scene=("The blackboard lists status changes.", "Which topic do you want to read? PSN?"))
            hands, brain = tutorial_hands(game)
            board = MenuView(kind, ("PSN", "PAR", "SLP", "BRN", "FRZ", "EXIT"), 0, True)
            hands.eyes.script = lambda frame: replace(game.look(frame), screen=replace(game.look(frame).screen, ui=board))
            return hands, brain

        hands, brain = grid("multichoice_grid")
        self.assertFalse(drive(brain._story_menu(hands, "multichoice_grid", "a scene", "MUDKIP"), 10_000))
        self.assertEqual(buttons(hands), [])
        self.assertTrue(any("GRID" in line for line in hands.told))
        hands, brain = grid("multichoice")
        drive(brain._story_menu(hands, "multichoice", "a scene", "MUDKIP"), 10_000)
        self.assertIn("A", buttons(hands))  # FAULT half: chosen on a grid

    def test_g7_u6_a_b_the_screen_ignores_ends_the_episode_in_its_bounds(self):
        """G7 / U6: a POKéNAV menu that nothing names and that ignores B (the tutorial's, under an instruction that never
        names MATCH CALL) gets exactly `B_REFUSALS` B presses, then the episode stops, said, well inside its frame budget. A
        menu that never takes input stops at `EPISODE_BUDGET`."""
        from ai_player.skills.instructed import B_REFUSALS, EPISODE_BUDGET

        game = _Tutorial(scene=("Please choose the POKéNAV.",))
        hands, brain = tutorial_hands(game)
        self.assertTrue(drive(play_scene(hands, brain, rounds=1), 200_000).startswith("stuck: an unexpected"))
        self.assertEqual(buttons(hands).count("B"), B_REFUSALS)
        self.assertLess(hands.pad.frames, EPISODE_BUDGET)
        self.assertTrue(any("ignored B" in line for line in hands.told))
        game = _Tutorial(accepts=False)
        hands, brain = tutorial_hands(game)
        self.assertNotEqual(drive(play_scene(hands, brain, rounds=1), 400_000), "free")
        self.assertLessEqual(hands.pad.frames, EPISODE_BUDGET + 600)
        self.assertTrue(any(f"more than {EPISODE_BUDGET} frames" in line for line in hands.told))

    def test_the_other_bounds_each_end_the_episode_said(self):
        """Every bound of `follow` stops it, told, with no press past it: MAX_DECISIONS (a B that sends the list and the
        menu back and forth), FIELD_CHOICES_MAX (a forced menu that loops back whatever is chosen), a screen between the
        menus that never changes (the stall detector's stop), and a menu that does not take the choice named."""
        from ai_player.skills.instructed import FIELD_CHOICES_MAX, MAX_DECISIONS

        game = _Tutorial(scene=("Please choose the POKéNAV.",), bounce=True)
        hands, brain = tutorial_hands(game)
        drive(play_scene(hands, brain, rounds=1), 200_000)
        self.assertEqual(buttons(hands).count("B"), MAX_DECISIONS - 1)  # the POKéNAV choice, then the B's
        self.assertTrue(any("MAX_DECISIONS" in line for line in hands.told))
        game = _Tutorial(loop_always=True)
        hands, brain = tutorial_hands(game)
        drive(play_scene(hands, brain), 200_000)
        self.assertEqual(game.chosen.count(("forced", "POKéNAV")), FIELD_CHOICES_MAX)
        self.assertTrue(any("FIELD_CHOICES_MAX" in line for line in hands.told))
        game = _Tutorial(stuck_opening=True)
        hands, brain = tutorial_hands(game)
        drive(play_scene(hands, brain, rounds=1), 200_000)
        self.assertTrue(any("between the menus: stuck:" in line for line in hands.told))
        self.assertLess(hands.pad.frames, 2_000)
        game = _Tutorial(deaf=True)
        hands, brain = tutorial_hands(game)
        drive(play_scene(hands, brain, rounds=1), 200_000)
        self.assertTrue(any("did not take 'MATCH CALL'" in line for line in hands.told))
        self.assertEqual(game.chosen, [("forced", "POKéNAV")])

    def test_a_loop_that_lets_no_frame_pass_is_bounded(self):
        """The episode never spins: a pass that presses nothing and waits for nothing (here: an `advance` that answers at
        once while the POKéNAV is still opening) is counted, and `STILL_PASSES_MAX` of them in a row stop it, told. CONTROL:
        the real `advance` waits the opening out and the tutorial is played (U1)."""
        import ai_player.skills.instructed as instructed
        from ai_player.skills.instructed import STILL_PASSES_MAX

        def answers_at_once(*_args, **_kwargs):
            return "done"
            yield  # a generator that lets no frame pass

        game = _Tutorial()
        hands, brain = tutorial_hands(game)
        looks = hands.look

        def counted():
            # a loop that yields no frame never returns to `drive`: the test's own bound is on the looks it takes
            counted.n += 1
            if counted.n > 5_000:
                raise AssertionError("5,000 looks and the episode still spins: no bound on passes that let no frame pass")
            return looks()

        counted.n = 0
        hands.look = counted
        with mock.patch.object(instructed, "advance", answers_at_once):
            self.assertFalse(drive(brain._story_menu(hands, "multichoice", "a scene", "MUDKIP"), 50_000))
        self.assertTrue(any(f"{STILL_PASSES_MAX + 1} passes in a row let no frame pass" in line for line in hands.told))
        self.assertEqual(game.chosen, [("forced", "POKéNAV")])

    def test_the_eyes_report_the_kinds_the_skill_plays(self):
        """The skill's kinds are the eyes' (`eyes/screens.py` read_ui): the POKéNAV's three views and a script's multichoice
        are INSTRUCTED kinds, a grid is the refused GRID kind (E7). FAULT half: without `Task_Pokenav` the eyes report no
        menu at all (what they reported before chapter 5)."""
        from ai_player.eyes.screens import read_ui
        from ai_player.skills.instructed import GRID_KIND, INSTRUCTED_KINDS

        state = bytes([3, 0]) + bytes(30)
        views = [
            {"menu": {"type": 1, "cursor": 0, "handler": "HANDLEMAINMENUINPUTTUTORIAL"}},
            {"mc": {"handler": "CB2_HANDLEMATCHCALLINPUT", "entries": ["MR. STONE"], "list_cursor": 0, "options": []}},
            {"mc": {"handler": "CB2_HANDLEMATCHCALLOPTIONSINPUT", "entries": ["MR. STONE"], "list_cursor": 0,
                    "option_cursor": 0, "options": [0, 2]}},
        ]
        kinds = [read_ui("UNKNOWN", {"Task_Pokenav": state}, {"pokenav": {"state": 3, **raw}}).kind for raw in views]
        self.assertEqual(kinds, ["pokenav_menu", "pokenav_list", "pokenav_options"])
        self.assertTrue(set(kinds) <= INSTRUCTED_KINDS)
        menu = bytes([0, 0, 0, 0, 2]) + bytes(7)
        raw = {"menu": menu, "multichoice_options": ["A1", "B1", "C1"], "multichoice_delay": 0}
        self.assertEqual(read_ui("OVERWORLD", {"Task_HandleMultichoiceInput": bytes(32)}, raw).kind, "multichoice")
        self.assertEqual(read_ui("OVERWORLD", {"Task_HandleMultichoiceGridInput": bytes(32)}, raw).kind, GRID_KIND)
        self.assertIsNone(read_ui("UNKNOWN", {}, {"pokenav": {"state": 3, **views[0]}}))  # FAULT half: no Task_Pokenav

    def test_c3_a_field_menu_nothing_names_is_still_the_stop_it_was(self):
        """C3: the field multichoices chapters 1-4 (and later) meet, under their own words: nothing is named, no press, the
        stop is the same as before (False). Each built as the eyes would read it, after the player was free."""
        from ai_player.eyes.observation import MenuView

        cases = {
            "PC": (("SOMEONE'S PC", "MILO'S PC", "LOG OFF"), ["Milo booted up the PC.", "Which PC should be accessed?"]),
            "Briney": (("DEWFORD", "EXIT"), ["MR. BRINEY: Ahoy! For you, I’ll go out to sea anytime!",
                                             "Now, my friend, where are we bound?"]),
            "fossil": (("CLAW FOSSIL", "ROOT FOSSIL", "EXIT"),
                       ["Oh, now that’s a surprise! You have not one, but two, fossils?",
                        "Unfortunately, my machine can only regenerate one POKéMON at a time.",
                        "Would you like to pick one of your fossils for regeneration?"]),
            "fishing": (("EXCELLENT!", "NOT SO GOOD"), ["Yo! How’s your fishing?"]),
        }
        for name, (options, pages) in cases.items():
            with self.subTest(name):
                game = _Tutorial()
                hands, brain = tutorial_hands(game)
                base = game.look(0)
                free = replace(base, screen=ScreenState(game_state="OVERWORLD", screen="overworld", menu=None,
                                                        text_box_open=False, waits_for_button=False, in_battle=False))
                brain._instructed.read_along(free)
                for text in pages:
                    brain._instructed.read_along(replace(base, screen=replace(base.screen, ui=None, waits_for_button=True,
                                                                         text=text)))
                menu = MenuView("multichoice", options, 0, True)
                hands.eyes.script = lambda frame, m=menu: replace(base, screen=replace(base.screen, ui=m, text=pages[-1]))
                self.assertFalse(drive(brain._story_menu(hands, "multichoice", "a scene", "MUDKIP"), 10_000))
                self.assertEqual(buttons(hands), [])

    def test_c1_c2_the_menus_chapters_1_to_4_meet_go_where_they_went(self):
        """C1: a starter's bag, the clock, a mart and the save screens reach their own handlers, never the skill; an unknown
        kind and a yes/no (C2: the navigator answers it by its words before `on_menu`) are not the skill's either."""
        import ai_player.mode as mode_module

        def handler(*_args, **_kwargs):
            yield
            return True

        def left(*_args, **_kwargs):
            yield
            return "left"

        game = _Tutorial()
        hands, brain = tutorial_hands(game)
        brain.options.clock = (10, 0)
        brain.navigator = None
        with mock.patch.object(type(brain._instructed), "follow", side_effect=AssertionError("the skill was called")), \
                mock.patch.object(mode_module, "choose_starter_in_bag", handler), \
                mock.patch.object(mode_module, "set_clock", handler), \
                mock.patch.object(mode_module, "leave_shop", left), \
                mock.patch.object(HandsBrain, "_save_screen", lambda self, h, k, w: handler()):
            for kind in ("choose_starter", "clock", "mart_buy", "mart_menu", "start_menu", "save_yes_no", "save_dialog"):
                with self.subTest(kind):
                    self.assertTrue(drive(brain._story_menu(hands, kind, "a scene", "MUDKIP")))
            for kind in ("yes_no", "a_menu_nobody_knows"):
                with self.subTest(kind):
                    self.assertFalse(drive(brain._story_menu(hands, kind, "a scene", "MUDKIP")))


def _unused_tile() -> Tile:  # keeps the builder import honest (a Tile is what View rows hold)
    return Tile(0, 0, 0, 0, 0, 0, "NORMAL", 0, 3, False, False, None, False, None, False, False, False)


if __name__ == "__main__":
    unittest.main(verbosity=1)
