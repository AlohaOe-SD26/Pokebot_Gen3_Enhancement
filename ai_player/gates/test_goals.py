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


def manager(personality: str = "Story", gender: str = "BOY", hints_off: bool = False, train_off: bool = False,
            seed: int = 1) -> GoalManager:
    state = PersonalityState(personality, random.Random(seed), drift_on=False)
    return GoalManager(load_story(gender), state, random.Random(seed), hints_off=hints_off, train_off=train_off)


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
        home = world_with("LITTLEROOT_TOWN", "ROUTE101", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", current="ROUTE101",
                          heard={"ROUTE 103"})
        _, goal = self.goal(hp=5, world=home)
        self.assertEqual((goal.kind, goal.map), ("heal", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F"))
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
        before = ch1_through("ch1_pokedex")
        _, early = self.goal("Catcher", balls=0, values=before, world=world(), const="OLDALE_TOWN", heard={"LAB"})
        self.assertNotEqual(early.kind, "shop")  # no POKé BALLS on sale before the adventure has started

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
    """The play loop's hands: every look is `screen` (its watchers told, as the real hands tell them)."""

    def __init__(self, screen: Observation) -> None:
        self.pad = _LoopPad()
        self.screen = screen
        self.last = screen
        self.watchers: list = []
        self.told: list[str] = []
        self.notes: list[tuple] = []

    def look(self) -> Observation:
        for watcher in list(self.watchers):
            watcher(self.screen)
        self.last = self.screen
        return self.screen

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
    PER_SCREEN = 5000  # frames a stand-in `play_out` takes on a screen that never frees

    def run_loop(self, screen: Observation, lose: bool = False, budget: int = 60_000):
        from ai_player import mode as mode_module

        world = world_with("LITTLEROOT_TOWN", "ROUTE101", current="ROUTE101")
        nav = types.SimpleNamespace(battle_log=[], take_changes=lambda: [], stats=types.SimpleNamespace(steps=0), world=world,
                                    battler=None, answer=None, on_menu=None)
        hands = _LoopHands(screen)
        pursued: list[str] = []
        screens: list[str] = []
        per_goal = self.PER_GOAL

        class Runner:
            def __init__(self, hands_, nav_, manager_, mind_, tell_) -> None:
                self.nav = nav_
                self.roams, self.heals, self.shopping, self.picked = [], [], [], []

            def pursue(self, goal, milestone, index, current):
                pursued.append(goal.kind)
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
                                              starter=None, clock=None)
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
        self.assertTrue(reason.startswith("stuck: no milestone for"), reason)
        self.assertEqual(report["losses"], 0)

    def test_patience_ends_a_screen_that_never_frees(self):
        base = self.free_screen()
        stuck = replace(base, screen=replace(base.screen, text_box_open=True, waits_for_button=True, script_running=True,
                                             text="..."))
        reason, hands, pursued, screens, _ = self.run_loop(stuck, budget=20_000)
        self.assertTrue(reason.startswith("stuck: no milestone for"), reason)
        frames = int(reason.split("no milestone for ", 1)[1].split(" ", 1)[0])
        self.assertGreater(frames, mode_module_patience())
        self.assertLessEqual(frames, mode_module_patience() + self.PER_SCREEN + 100)  # at the first pass past it
        self.assertEqual(pursued, [])  # never free: no goal was chosen
        # every pass played the screen out (and waited for it to settle) until the patience ran out: no more passes
        self.assertTrue(mode_module_patience() // (self.PER_SCREEN + 10) <= len(screens)
                        <= mode_module_patience() // self.PER_SCREEN + 1, len(screens))

    def test_patience_ends_goals_that_never_move_the_story(self):
        reason, hands, pursued, screens, _ = self.run_loop(self.free_screen())
        self.assertTrue(reason.startswith("stuck: no milestone for"), reason)
        self.assertIn("since Find the rival on ROUTE 103", reason)
        self.assertEqual(screens, [])
        self.assertGreaterEqual(len(pursued) * self.PER_GOAL, mode_module_patience())


def mode_module_patience() -> int:
    from ai_player.mode import STORY_PATIENCE
    return STORY_PATIENCE


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
