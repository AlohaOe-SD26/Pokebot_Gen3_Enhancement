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
import json
import os
import random
import re
import sys
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
from ai_player.brain.navigator import Navigator  # noqa: E402
from ai_player.eyes.observation import (  # noqa: E402
    BagSummary, BattleView, MonSummary, Observation, PlayerState, Progress, ScreenState, SeenObject, Tile, View,
)
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
        goal = self.rival_goal()
        self.assertEqual((goal.kind, goal.map), ("go", "LITTLEROOT_TOWN_MAYS_HOUSE_1F"))

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
    loop must end on STORY_PATIENCE); goals that never move the story (the same)."""

    PER_GOAL = 1000  # frames a stand-in goal takes
    PER_TRAIN = 20_000  # (build step 5.1) frames a stand-in training session takes
    PER_SCREEN = 5000  # frames a stand-in `play_out` takes on a screen that never frees

    def run_loop(self, screen, lose: bool = False, budget: int = 60_000, heard=(), win_training: bool = False,
                 arrived_at: int | None = None):
        from ai_player import mode as mode_module
        from ai_player.world.memory import Transition

        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101", heard=heard)
        if arrived_at is not None:  # (build step 5.1) a map change landed at this frame (a scene's, say)
            world.transitions.append(Transition(arrived_at, "0:1", "0:2", "warp", "scene", (7, 15), (6, 5), None))
        nav = types.SimpleNamespace(battle_log=[], take_changes=lambda: [], stats=types.SimpleNamespace(steps=0), world=world,
                                    battler=None, answer=None, on_menu=None)
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

            def pursue(self, goal, milestone, index, current):
                pursued.append(goal.kind)
                hands.starts.append(hands.pad.frames)
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
            hands.pad.frames += self.PER_SCREEN
            yield
            return "stuck: a screen that does not end"

        brain = HandsBrain.__new__(HandsBrain)
        brain.options = types.SimpleNamespace(target="ch1_pokedex", fault_no_hints=False, fault_no_training=False,
                                              fault_no_errands=False, starter=None, clock=None)
        brain.navigator, brain.world, brain.seed, brain._say, brain.play_report = nav, world, 5, (lambda line: None), None
        with mock.patch.object(mode_module, "GoalRunner", Runner), mock.patch.object(mode_module, "play_out", play_out):
            reason = drive(brain._play(hands, types.SimpleNamespace(name="Story")), budget)
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
            world = world_with(*places, current="LITTLEROOT_TOWN")
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
        self.assertTrue(all("draw " in line and ">= the Story's" in line for line in quiet))

    def test_after_passing_new_places_it_looks_round_the_next(self):
        """The verifier: "per-run curiosity can be almost zero" (and the development sweep step51vdev1's Story seed 4: all
        three look-around draws chose nothing). After LOOK_DEBT new places gone past in a row, the next one is looked round
        without a draw, said so; a failed draw counts one more, a look round starts the count again."""
        from ai_player.brain.goals import LOOK_DEBT
        forced = drawn = 0
        for seed in range(100):
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
                    self.assertEqual(mgr.memory.passed_new, 0)
                    if "gone past" in goal.reason:
                        self.assertIn(f"gone past {LOOK_DEBT} new places in a row", goal.reason)
                else:
                    drawn += goal.kind == "explore"
                    self.assertEqual(mgr.memory.passed_new, 0 if goal.kind == "explore" else 1)
        self.assertEqual(forced, 100)
        self.assertLess(drawn, 75)  # FAULT half: without the debt the Story's draw passes some new places by

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
        fake_nav = types.SimpleNamespace(rng=random.Random(1), is_excluded=lambda t: t.tile in excluded,
                                         where=lambda seen: (None, (10, 10)))
        nav = types.SimpleNamespace(run=run, world=world_with("ROUTE101", current="ROUTE101"))
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
            return next(ok for ok, text in step51_verdicts({"LOSE3": rows}) if text.startswith("LOSE3"))

        self.assertTrue(verdict(reached + [short]))  # FAULT half: graded as before, the short run failed it
        self.assertFalse(verdict([row(1, "play: stopped: not finished", 3, 1000, 1000 + STOP_WITHIN + 1)] + reached))
        self.assertFalse(verdict(reached[:1] + [short, short, short]))  # the arm must reach a third loss


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
        from ai_player.brain.goals import OWED_STOP, Goal, GoalRunner
        world = petalburg_world("OLDALE_TOWN")
        mgr = self.owed_manager()
        mgr.memory.looked = _Everything()  # no look-around draw is due: only the balance can stop the walk
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
        self.assertEqual(insides, [])  # stopped on the way: a break owed
        self.assertIn(OWED_STOP, outcome)
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

    # ---- the BALANCE
    def owed_manager(self, personality: str = "Story", story: int = 20_000, errand: int = 2_000, curious: int | None = None,
                     **kwargs) -> GoalManager:
        mgr = manager(personality, quiet=False, train_off=True, **kwargs)
        mgr.memory.spent = {"story": story, "errand": errand, "curious": errand if curious is None else curious}
        return mgr

    def test_the_balance_owes_a_break_from_the_story(self):
        from ai_player.brain.goals import BALANCE_MIN_FRAMES, Goal
        self.assertIn(f"under the Story's {ERRANDS['Story'].balance:.0%}", self.owed_manager().owed())
        self.assertIsNone(self.owed_manager(errand=18_000).owed())  # 47 %: kept
        self.assertIsNone(self.owed_manager(story=BALANCE_MIN_FRAMES - 1, errand=0).owed())  # too soon to judge
        self.assertIsNone(self.owed_manager(errands_off=True).owed())  # the beeline control never owes one
        self.assertGreater(ERRANDS["Catcher"].balance, ERRANDS["Story"].balance)
        self.assertGreaterEqual(min(e.balance for e in ERRANDS.values()), 0.30)  # every one above the graders' floor
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

    def test_the_balance_keeps_some_of_it_for_curiosity(self):
        """(the round's development sweep step51wdev2: chapter 1's TRAINING kept the errands' share at 50-74 % while its
        curiosity was 4 % in some runs, and the time to the POKéDEX fell within the beeline's noise) Errands enough, but
        curiosity under the personality's `curious_min`: a break is owed all the same."""
        needs_only = self.owed_manager(story=20_000, errand=20_000, curious=1_000)  # 50 % errands, 2.5 % curiosity
        self.assertIn(f"went to curiosity, under the Story's {ERRANDS['Story'].curious_min:.0%}", needs_only.owed())
        self.assertIsNone(self.owed_manager(story=20_000, errand=20_000, curious=5_000).owed())  # 12.5 %: kept
        self.assertGreaterEqual(ERRANDS["Catcher"].curious_min, ERRANDS["Story"].curious_min)

    def oldale(self, mgr: GoalManager) -> Goal:
        mgr.rng = _Draws(0.99)  # every draw the dice would NOT pass
        world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", "LITTLEROOT_TOWN_MAYS_HOUSE_1F",
                           current="OLDALE_TOWN", heard={"Oh, MAY went out to ROUTE 103 just a little while ago."})
        mgr.memory.asked_rounds["ch1_rival_route103"] = ASK_ROUNDS
        observation = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN")
        index, milestone = mgr.milestone(observation, visited_in(world))
        return mgr.next_goal(observation, world, milestone, index)

    def test_an_owed_break_passes_the_draws(self):
        goal = self.oldale(self.owed_manager())
        self.assertEqual(goal.kind, "explore")
        self.assertIn("a new place, OLDALE_TOWN", goal.reason)
        self.assertIn("a break from the story", goal.reason)
        self.assertNotEqual(self.oldale(self.owed_manager(errand=20_000)).kind, "explore")  # FAULT half: the dice said no

    def test_with_no_draw_due_an_owed_break_looks_round_here_some_more(self):
        from ai_player.brain.goals import AGAIN_MAX
        mgr = self.owed_manager()
        mgr.memory.looked, mgr.memory.detoured = _Everything(), _Everything()  # this map's draws were made
        kinds = [self.oldale(mgr) for _ in range(AGAIN_MAX + 1)]
        self.assertEqual([g.kind for g in kinds], ["explore"] * AGAIN_MAX + ["go"])  # FAULT halves: none, or no bound
        self.assertIn("some more", kinds[0].reason)
        self.assertNotIn("a new place", kinds[0].reason)  # (`live_step5` "a new place is new" reads new places only)
        self.assertEqual(self.oldale(self.owed_manager(errand=20_000)).kind, "go")

    def test_a_walk_stops_where_the_owed_break_can_be_taken(self):
        """A `go` that arrives on ANOTHER outdoor map while the balance is owed stops there once a map and milestone (the
        next decision takes the break there); not when nothing is owed, nor on the map the walk began on."""
        from ai_player.brain.goals import OWED_STOP, Goal, GoalRunner
        for owed, began_there, want in ((True, False, True), (False, False, False), (True, True, False)):
            world = world_with("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN", current="OLDALE_TOWN" if began_there else
                               "ROUTE101")
            arrive = look(ch1_through("ch1_rival_route103"), party=[mon(9)], const="OLDALE_TOWN", map_number=3)
            stopped = []

            def run(intent, why, world=world, arrive=arrive, stopped=stopped):
                world._last.key = "0:3"  # noqa: SLF001
                stopped.append(intent.done(arrive))
                yield
                return "done: travel" if stopped[-1] else "budget: ran out"

            mgr = self.owed_manager(errand=2_000 if owed else 20_000)
            mgr.memory.looked = _Everything()  # its look-around draw was made: only the balance can stop the walk
            nav = types.SimpleNamespace(world=world, run=run, battle_log=[])
            runner = GoalRunner(types.SimpleNamespace(look=lambda arrive=arrive: arrive), nav, mgr,
                                types.SimpleNamespace(purpose=""), lambda line: None)
            runner._travel = lambda target, why, budget, done, run=run: run(types.SimpleNamespace(done=done), why)  # noqa: SLF001
            ok, outcome = drive(runner.pursue(Goal("go", "to ROUTE 103", map="ROUTE103"), mgr.story.milestones[8], 8,
                                              lambda seen: 8))
            self.assertEqual(stopped, [want], (owed, began_there))
            self.assertEqual(OWED_STOP in outcome, want, outcome)

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

    def test_the_graders_curiosity_is_the_goal_managers(self):
        from ai_player.brain.goals import CURIOSITY_KINDS as BRAIN
        from ai_player.gates.rate_step5 import CURIOSITY_KINDS as GRADER
        self.assertEqual(BRAIN, GRADER)

    def test_the_chapter2_checks(self):
        """The sweep's chapter 2 (`rate_step5.chapter2_verdicts`): the floor in EVERY run, the beeline under it."""
        from ai_player.gates.rate_step5 import BOUNDS, chapter2_verdicts

        def row(seed, share, free=0.1, wally=True, plan="CH2"):
            return {"plan": plan, "seed": seed, "personality": "Story", "wally": wally, "frames": 90000,
                    "reason": "play: done", "mix": {"errand_share": share, "free_share": free}, "old_places": [],
                    "place_draws": 2, "losses_game": 0, "time_wally": {"outside_nb": 50000 if plan == "CH2" else 40000}}

        def verdict(rows, start):
            return next(ok for ok, text in chapter2_verdicts(rows) if text.startswith(start))

        good = {"CH2": [row(1, 0.4), row(2, 0.35)], "CH2_OFF": [row(1, 0.1, 0.0, plan="CH2_OFF"),
                                                                 row(2, 0.2, 0.0, plan="CH2_OFF")]}
        self.assertTrue(verdict(good, "CH2: THE INTENT MIX"))
        self.assertFalse(verdict({**good, "CH2": [row(1, 0.4), row(2, BOUNDS["MIX_MIN"] - 0.01)]}, "CH2: THE INTENT MIX"))
        self.assertTrue(verdict(good, "CH2_OFF"))
        self.assertFalse(verdict({**good, "CH2_OFF": [row(1, 0.5, 0.0, plan="CH2_OFF")] * 2}, "CH2_OFF"))
        self.assertTrue(verdict(good, "CH2: NO SPEEDRUN"))
        self.assertFalse(verdict({**good, "CH2": [row(1, 0.4, wally=False)] * 2}, "CH2: WALLY"))


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


def _unused_tile() -> Tile:  # keeps the builder import honest (a Tile is what View rows hold)
    return Tile(0, 0, 0, 0, 0, 0, "NORMAL", 0, 3, False, False, None, False, None, False, False, False)


if __name__ == "__main__":
    unittest.main(verbosity=1)
