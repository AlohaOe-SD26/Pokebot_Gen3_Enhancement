"""The AI's GOAL MANAGER (build step 5; design draft §2.3 "goal manager", §5, §6; HUMAN-PLAY-DESIGN pillars 1-4; USER RULING
37: badge 1 in 4 chapters, "HUMAN pacing, but always goal-directed and never idle"). Framework-free.

WHAT IT DOES: at every decision it reads WHERE THE STORY IS from the eyes' milestone marks (`Progress.marks`: the flags and
vars `knowledge/milestones.json` names as each milestone's proof; `knowledge/story.py` Story.current), and chooses ONE goal,
with a reason that is logged. The story is the backbone; HUMAN ERRANDS are interleaved with it by the active personality's
weights (`personality.py` ERRANDS), the way a person plays (design draft §5: "never a speedrun: the goal manager always
interleaves explore, catch, item and train intents with story ones; even the Story personality takes them"):
  1. HEAL   the party is hurt (a Pokemon fainted, or its HP share under the personality's `heal_below`) or a known FIGHT is
            next and the party is not near full: walk to a POKéMON CENTER it KNOWS (one it has been in, or whose door it has
            SEEN: a door is recognised by its look, `looks.pokemon_center_door`) and talk to the nurse; with none known
            yet, home, once it KNOWS MOM heals (build step 5.1: her words or a heal seen, `home_heals`; step 5 used
            FLAG_RESCUED_BIRCH) (`data/scripts/players_house.inc` PlayersHouse_1F_EventScript_MomHealsParty); on the way, and
            on any walk while hurt (build step 5.1), it keeps out of the tall grass where it can (`HURT_GRASS_COST`);
  2. SHOP   POKé BALLS fewer than `balls_low` and the money for them: the MART it knows (in it, or its door seen),
            `balls_buy` balls (and a few POTIONS); (build step 5.1) a mart whose LIST showed no POKé BALLS (the Oldale
            Mart's, before the adventure has started: design draft §10.9) is remembered and tried again only once the story
            has moved on; step 5 waited for FLAG_ADVENTURE_STARTED, a flag no player sees;
  3. TRAIN  a FIGHT with known levels is next (the milestone's `fight`: the rival's L5, ROXANNE's 12-15; build step 5.1:
            only a fight the game NAMES, or levels SEEN, `fight_levels`) and the strongest
            Pokemon is under its level + `train_margin`, or the AI has roamed fewer than `train_min_steps` training steps
            since this milestone began: roam the grass (`skills/roam_train.py`, fighting what comes: purpose "train");
            Trainer most, Story least, never straight in (CLAIM pre-registered by `gates/live_step5.py`: steps and battles
            BEFORE the rival);
  4. ITEM   an item ball SEEN on this map, not tried yet: walk up to it and pick it up (pillar 4); (build step 5.1) before
            the party too, and one seen earlier on this map walked back to;
  5. CATCH  POKé BALLS in the bag and grass on this map not walked yet: by a seeded draw against the personality's
            `catch_seek` (Catcher most), roam it to meet new species (the battle decider catches a species the POKéDEX lacks
            by its temperament: `brain/battle.py` catch_new);
  6. CHAT   someone not talked to stands near: by a draw against `chat` (Trainer most), walk up and talk (people tell
            things: the hints come from them);
  7. EXPLORE (build step 5.1) a NEW outdoor map (new to it: its world memory, carried between sessions, had not stood
            there when this session began): by one draw against `look_around` (Story least), look around it for
            `look_frames`, keeping to it; not in danger, not where the story's own next thing is told and here;
  8. STORY  the current milestone's next STEP (`knowledge/story.py` Step): `go` to its map, `use` / `talk` to what LOOKS
            like what it names on that map, `ask` the people of a map until its words are heard, `follow` a scene; (build
            step 5.1) a `go` across an outdoor map may first be a DETOUR (one draw a map and milestone against `detour`): one
            place off the way, walked TO and stood on, for at most `detour_frames`; a story goal that failed `FAIL_LIMIT`
            times waits its cooldown (decisions or `STORY_ASIDE_FRAMES`, whichever first) and the decision LOOKS AROUND
            meanwhile, saying so (never idle, never without a goal); a walk whose budget its BATTLES ate walks on for the
            frames they took (`GO_BATTLE_EXTENSIONS`).
  (1b, build step 5.1) FIND A CENTRE: in danger with no place to heal known, it looks for a POKéMON CENTER's red roof.
  (build step 5.1) THE ORDER is now HEAL (or find a centre), SHOP, ITEM, EXPLORE, TRAIN, CATCH, CHAT, STORY: an item ball in
  view comes before training (a training roam stops for one, so training first ended every session at once) and looking
  round a new place before training and chatting (`next_goal`'s comments say what was measured).
HINTS ARE EARNED: a step's map is used only once the AI has READ the words that name it (the milestone's `hint.words`, as
WHOLE words, in the pages the world memory heard: `world/memory.py` heard; `heard_words`), and the goal's reason quotes
the page it READ (`heard_page`, never the milestone's stored line); before that, the step explores with no goal map, as a
person who has not been told. A hint with NO words (the truck's open door, a road sign the AI never read) names nothing a person
was told: its map is used only when the AI has BEEN there itself (its own world memory); otherwise it explores (`hint_known`,
the step-5 verifier, 2026-10-14). The FAULT switch `hints_off` (`AI_PLAYER_FAULT_NO_HINTS`) never uses a hint; `train_off`
(`AI_PLAYER_FAULT_NO_TRAINING`) never trains before a fight (the step-5 fault arms).
Every goal is bounded (its own frame budget), every outcome logged, and a goal that keeps failing is put aside for a while
(`FAIL_LIMIT`, `cooldown`): the next decision chooses another. A TRAINING (or catching) roam stops after a battle that left
the party under the personality's `heal_below` (`training_rest`, asked by the navigator after every battle: `battle_rest`),
so the next decision heals.

BUILD STEP 5.1 (the step-5 verifier and the step-5 adversarial review, 2026-10-14), each rule with its test in
`gates/test_goals.py` and a mutant in `gates/revert_step5.py`:
  * EXPLORE, DON'T BEELINE (review #1; RULINGS 32 and 37: "never a speedrun", detours for exploring, items): a seeded,
    personality-weighted LOOK-AROUND errand on every NEW OUTDOOR map (`Errands.look_around`, Story least; one draw a map;
    new to it: not a map its carried world memory knew when the session began, `known_before`; a draw that chose nothing
    is told too), a short DETOUR off the shortest way now and then while travelling (`Errands.detour`, one draw a map and
    milestone: a place at least `DETOUR_MIN_TILES` away, walked to and stood on), a
    walk that ARRIVES on an outdoor map never seen stops there so the next decision may look around (`NEW_MAP_STOP`), an
    item ball it REMEMBERS on this map walked back to, and item curiosity before the party too (the rival's POKé BALL is
    found by it, not by a scripted step). The fault switch `errands_off` (`AI_PLAYER_FAULT_NO_ERRANDS`) is the BEELINE
    control: none of these, no chat, no catching roam.
  * PERSON-FAIR (review #3, #4): every story STEP's map is unlocked by ITS OWN words (`Step.told`) or, for a wordless step,
    a visit (`step_known`), the `ask` step included; the training target comes only from fights the game NAMES (the rival,
    a gym leader: `Milestone.fight_named`, RULING 33 "train to the leader's level") or from levels SEEN in a trainer's
    battle on the milestone's maps (`seen_levels`); POKé BALLS are shopped for by what the mart's LIST shows (none on it:
    remembered, and that mart is tried again only once the story moved on, `no_balls`), never by a flag; MOM is a place to
    heal once the AI has HEARD it ("If anything happens, you can come home.", "I think you should rest a bit.") or SEEN her
    heal the party (`home_heals`), never by a flag.
  * LOOPS (review #5): a STORY goal that failed `FAIL_LIMIT` times is put aside like any other (`_allowed`), and the
    decision says so and looks around meanwhile; an OPTIONAL milestone (the gym's trainers) is never the current one.

BUILD STEP 5.1, THE VERIFIER'S SECOND ROUND (2026-10-14: the live CH2T arm, the Story player in chapter 2, under the
intent-mix floor, 16 % of its goals' frames on errands once a goal DROPPED for WALLY's scene no longer counted that scene):
  * A GYM is RECOGNISED by its door's look (`looks.gym_door`, METATILE_General_Door_Gym; `notice`, `door_of`), and a walk
    to it goes in by that door once seen (`GoalRunner._to_building`): CH2T had searched PETALBURG CITY door by door.
  * The NEAREST place to heal or shop, been in or its door seen (`_nearest_place`; step 5 took any place it had been in
    first: CH2T walked back to OLDALE past PETALBURG's); hurt in a TOWN whose centre it has not seen, it looks for it there
    first, once (`find_center` with `via`, `CENTER_LOOK_FRAMES`).
  * The BALANCE (`spent`, `owed`, `Errands.balance`): when this session's goal frames (and the scenes between them) went
    to errands less than the personality's share, the curiosity draws pass without the dice, a walk stops on arriving at
    another outdoor map (`OWED_STOP`) and, with no draw due, it looks round where it stands some more (`AGAIN_MAX`).
    (REPLACED by build step 5.2's boredom, below: the balance was a quota on nearly the graders' own quantity.)
  * Found by the round's development sweep: a door seen ACROSS a map's edge is not that map's, a door that cannot be walked
    into is forgotten (`DOOR_UNUSABLE`), a heal in danger is tried again at most `DANGER_RETRIES` times in a row, the
    story's own person is no "chat", and a look round while a story goal is put aside lasts only the breather left
    (`ASIDE_LOOK_MIN`).
  * Which personality judged a fight's training done is logged (`fight_prep` `judged_by`), for the graders' bound.

BUILD STEP 5.2, PRODUCTIVE CURIOSITY (the step-5.1 adversarial review, 2026-10-15: "it LOAFS, and every metric pays for it":
at OLDALE three errands in a row went nowhere, about 7,500 frames of walking into someone standing at the west exit, and
CH2M looked round PETALBURG twice for one new tile; the 5.1 metrics counted curiosity by its KIND and its TIME, and the
balance's quota aimed at nearly the graders' own quantity). Each rule has its test in `gates/test_goals.py`
(`ProductiveTests`) and a mutant in `gates/revert_step5.py` (G139 on):
  * CURIOSITY BY YIELD (`yield_snapshot`, `goal_yield`): a curiosity goal is PRODUCTIVE only by what it brought, as the AI
    saw it: at least `YIELD_TILES_MIN` new tiles seen, a map first stood on, an item, a catch, a species first seen, words
    never read before, a talk. Only a productive one resets the boredom clock (`after_goal`); one that brought nothing
    marks its place: a look round with nothing new EXHAUSTS that map for the milestone (`exhausted`), a detour that did not
    get there BLOCKS its place (`blocked`), and a place someone kept standing in the way of is blocked as it happens
    (`GoalRunner`'s `_PersonBlock`, `PERSON_BLOCK_HITS`): curiosity never chooses a blocked place again in the milestone
    (the blocked tiles are walls of the curiosity goals' walks, kept apart from the scene walls the story's walks carry).
  * BOREDOM, NOT A QUOTA (`curious_odds`): every curiosity draw (a look round, a detour, a chat, a catching roam, "some
    more") is a DICE throw whose odds rise SMOOTHLY from the personality's own with the frames since its last PRODUCTIVE
    curiosity, capped at `CURIOUS_ODDS_CAP` (`Errands.bored_frames`); never a draw skipped. At most `CURIOUS_ROW_MAX`
    curiosity goals in a row (`curious_ok`): then the story or a need comes first. Nothing here computes a share of frames,
    the quantity the graders' floor measures.
  * LOOKING ROUND ONLY WHERE SOMETHING IS LEFT (`look_round_intent`, `left_to_see`): a look round chooses only places that
    can show something new (a frontier, grass not walked, someone not met), never a wander among what it has seen; with
    none left it ends; it ends too after `CURIOUS_NOVELTY` frames with nothing new; "some more" only where a frontier is
    left that it can WALK to (known tiles, nobody in the way, not blocked) and the map is not exhausted.
  * DETOURS THAT ARRIVE (`GoalRunner._detour`): a place on this map that it can walk to over tiles it knows, nobody in the
    way, never past an edge it knows, never blocked; the outcome says "reached" or "not reached", and only a reached one
    is done; at a person it chose, it TALKS to them.
  * A known town is never "a new place" (`may_look_around`: a map it has LEFT is known, whatever the session's first
    decision knew); the `ask` step goes to its house only once it was told to go and see the rival (its own words).
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable, Generator
from dataclasses import dataclass, field, replace

from ai_player.brain.battle import BattleMind, needs_rest
from ai_player.brain.bossprep import (
    ACT_ON,
    ACTING,
    BUDGET,
    CLOSE,
    LEADS_MAX,
    NO_FAULTS,
    NOT_READY,
    PARTNER_MARGIN,
    READY,
    RELEAD_FAILS_MAX,
    TRAINEE_FLOOR,
    RaiseWatch,
    choose_plan,
    described,
    member_now,
    members_of,
    near_best,
    new_record,
    next_boss,
    out_of_pp,
    partner_line_full,
    partner_worn,
    raise_partner_of,
    rank_of,
    spend,
    spent_reason,
    team_line,
    trainee_rest,
    with_target,
)
from ai_player.brain.bossprep import options as raise_options
from ai_player.brain.bossprep import verdict as judge_party
from ai_player.brain.explore import (
    JUST_COME_FROM,
    ONWARD_KINDS,
    SEEN_ALL,
    candidates,
    carry_on,
    choose_target,
    looks_like_exit,
    map_walls,
    pick,
    pick_on_the_move,
    region_hops,
    route_to,
    standing_walls,
    ways_from,
    weights_for,
)
from ai_player.brain.navigator import Intent, Navigator, Target, distances, nav_free, step_from
from ai_player.brain.rides import RideWatch, folded, trip_offer
from ai_player.eyes.observation import Observation, SeenObject
from ai_player.eyes.screens import page_text
from ai_player.hands.dialogue import player_free
from ai_player.hands.field_item import use_on
from ai_player.hands.pad import Hands
from ai_player.hands.party_order import lead_with
from ai_player.knowledge.atlas import boss_party, entry_maps, gym_leaders, open_map, town_places
from ai_player.knowledge.seasoned import land_levels
from ai_player.knowledge.story import Milestone, Step, Story
from ai_player.personality import PersonalityState
from ai_player.world.memory import DIRECTIONS, moved
from ai_player.skills.roam_train import roam_train
from ai_player.skills.story import (
    NOT_FOR_SALE,
    answer_question,
    enter_door,
    heal_at_center,
    pick_up,
    play_out,
    shop_at_mart,
    talk_to,
    use_thing,
)

__all__ = [
    "AGAIN_MAX",
    "ASIDE",
    "ASIDE_LOOK_MIN",
    "BREAK_STOP",
    "CURIOUS_NOVELTY",
    "CURIOUS_ODDS_CAP",
    "CURIOUS_ROW_MAX",
    "DANGER_RETRIES",
    "DOOR_UNUSABLE",
    "ASK_ROUNDS",
    "CENTER_LOOK_FRAMES",
    "CENTER_SUFFIX",
    "CURIOSITY_KINDS",
    "GYM_SUFFIX",
    "DETOUR_KINDS",
    "DETOUR_MIN_TILES",
    "DETOUR_TRIES",
    "LOOK_DEBT",
    "ERRAND_KINDS",
    "FAIL_LIMIT",
    "GO_BATTLE_EXTENSIONS",
    "GO_BATTLE_MIN",
    "STORY_ASIDE_FRAMES",
    "LOOK_KINDS",
    "MOM_HEAL_WORDS",
    "NEW_MAP_STOP",
    "PERSON_BLOCK_HITS",
    "STORY_KINDS",
    "YIELD_TILES_MIN",
    "YIELD_TILE_RATE",
    "SEEING_KINDS",
    "HURT_GRASS_COST",
    "FACING_STEP",
    "HEARD_KINDS",
    "LOST_KEYS",
    "OUT_OF_IDEAS",
    "OWN_PERSON_KINDS",
    "PREP_WALK_KINDS",
    "SPOKE_REACH",
    "UNREACHABLE",
    "Goal",
    "GoalManager",
    "GoalRunner",
    "TravelSense",
    "grass_target",
    "in_place",
    "inside_grass",
    "town_of",
    "ITEM_STOP",
    "ITEM_TRIES",
    "LOOK_AROUND_FRAMES",
    "MART_SUFFIX",
    "ON_THE_MAP",
    "TRAIN_SESSIONS",
    "battles_lost",
    "goal_yield",
    "heard_page",
    "heard_words",
    "is_gym",
    "keeps_going",
    "lead_toward",
    "look_round_intent",
    "lost_intent",
    "lost_way",
    "marks_of",
    "part_hops",
    "party_share",
    "quote",
    "roam_numbers",
    "shut_in",
    "strongest_level",
    "training_rest",
    "travel_intent",
    "world_distance",
    "worth_going",
    "yield_snapshot",
]

#: Map constants of the interiors a person recognises by their sign (`include/constants/map_groups.h` names): a POKéMON
#: CENTER's ground floor and a MART.
CENTER_SUFFIX = "POKEMON_CENTER_1F"
MART_SUFFIX = "MART"
#: A goal that failed this many times in a row is put aside for `COOLDOWN_DECISIONS` decisions.
FAIL_LIMIT = 2
COOLDOWN_DECISIONS = 12
#: Training sessions before one fight at most (each `Errands.train_session` steps): never an endless grind.
TRAIN_SESSIONS = 8
#: The reason a roam stops for an item ball that came into view (`GoalRunner.pursue`; the chapter-2 development run of
#: 2026-10-14 roamed past two on ROUTE 102 for 120 steps at a time and picked up none)
ITEM_STOP = "an item ball came into view"
#: (build step 5.2, the round's development sweep step52dev4: catching roams that met only POKéMON it had seen ran on to
#: their steps' end, 8,136-16,867 frames with 4-7 battles and nothing new, two in one chapter-2 run) a CATCHING roam stops
#: after this many battles in a row that brought no species first seen and no catch: a person gives the hunt up there
HUNT_FRUITLESS = 3
HUNT_STOP = "the hunt brought nothing new"
#: How many walks to one item ball a battle or a scene may interrupt before it is given up.
ITEM_TRIES = 3
#: How often the people of a map are asked round before the AI gives the ask up.
ASK_ROUNDS = 2
#: Frames of looking around when nothing else is wanted (an explore intent).
LOOK_AROUND_FRAMES = 2400
#: Frame budgets of the goals that walk somewhere.
GO_FRAMES = 9000
FIND_FRAMES = 4000
#: Before a known fight, a party under this share of its HP heals first when a centre is known (a person does).
HEAL_BEFORE_FIGHT = 0.9
#: On the way to heal, the extra cost of a tall-grass tile in the navigator's plans (`GoalRunner._heal`): a person whose
#: Pokemon is hurt walks up to this many tiles round to keep out of one tile of grass (the personalities' own travelling
#: cost is 0 to 2: `brain/explore.py` WEIGHTS grass_cost).
HURT_GRASS_COST = 8.0
#: The prices a person reads in the Oldale Mart's list (`hands/menus.py` mart_buy checks the money against the listed one).
BALL_PRICE, POTION_PRICE = 200, 300
#: (build step 5.1, review #4) What MOM says that tells a person home is where the party rests (`data/maps/LittlerootTown/
#: scripts.inc` LittlerootTown_Text_ComeHomeIfAnythingHappens, with the RUNNING SHOES; `PlayersHouse_1F_Text_YouShouldRestABit`
#: when she heals): heard (whole words), home is a place to heal.
MOM_HEAL_WORDS = ("you can come home", "you should rest a bit")
#: (build step 5.1, review #1) A walk (go, look around) that ARRIVES on an outdoor map it had never been to ends there, so
#: the next decision may look around the new place (the look-around errand's draw is made per map).
NEW_MAP_STOP = "arrived somewhere it has not looked round"
#: (build step 5.1, review #5) The goal kinds that are the STORY's (every other kind is an errand), and the key prefix of a
#: story goal put aside after failing (the look around meanwhile is never put aside: never without a goal).
STORY_KINDS = ("intro", "go", "ask", "talk", "use", "follow", "find", "seek", "look_around")
#: (chapter 7 NS3, 2026-11-06) the goals whose walk is the walk TO someone, or a heal, a save or a scene: every other goal's
#: walk stops when the one the story's next step names comes into view on that step's map (`GoalRunner.story_in_view`)
OWN_PERSON_KINDS = ("talk", "use", "seek", "find", "heal", "find_center", "save", "intro", "follow")
#: (chapter 7 stops round 4, V3-3, 2026-11-06) the walks that PREPARE for a fight: while the story's next step is a fight,
#: they are not stopped when its person comes into view (a party short of the leader's levels, in his gym with him in
#: view, walks out to the grass to train; stopped at its first look, the goal failed and training was put aside). With a
#: talk next (STEVEN), they stop as every errand does
PREP_WALK_KINDS = ("train", "catch")
ASIDE = "aside:"
#: (build step 5.1) The ERRAND kinds (the intent mix the graders count: `gates/rate_step5.py`).
ERRAND_KINDS = ("heal", "find_center", "shop", "train", "catch", "pick_up", "chat", "explore", "detour")
#: (build step 5.1, the verifier's second round) the errands of CURIOSITY, not need (the graders' `CURIOSITY_KINDS`, the
#: same list: `gates/test_goals.py` checks they agree): a curiosity goal the story moved on in is the story's (`spent`)
CURIOSITY_KINDS = ("explore", "detour", "chat", "catch", "pick_up")
#: (build step 5.1) What a DETOUR looks at: a place on this map the explorer likes (`brain/explore.py` candidates), never
#: the way on (a road, a route to the goal), back, or in (a door: that is a building, not a look on the way).
DETOUR_KINDS = ("frontier", "grass", "people")
#: (build step 5.1, the verifier's round: MEASURED on the first round's graded sweep's kept logs, seeds 401-410, 11 of
#: the 12 detours of its CH1 runs, and 56 of 63 over all its plans, ended at once, most "stuck: 51 decisions in a row
#: without a frame passing (every target fails at once)": the frontier it chose was seen past after one step, and the
#: detour chose that same stale place again and again) a detour walks TO the
#: place it chose and stands there (a `wander` target there: never "seen past" on the way), at least `DETOUR_MIN_TILES`
#: tiles from where it began (a step away is no detour), and a place it cannot reach is swapped for another, at most
#: `DETOUR_TRIES` places in all.
DETOUR_MIN_TILES = 6
DETOUR_TRIES = 3
#: (build step 5.1, the verifier's round: "per-run curiosity can be almost zero", a Catcher with no look-around in a run;
#: MEASURED in the development sweep step51vdev1, seed 4, a Story player: its three look-around draws all chose nothing,
#: 212 frames of curiosity in the run) a person who has gone past this many NEW places in a row without a look round
#: looks round the next one without a draw (said so): a story-minded player still stops at the third new town.
LOOK_DEBT = 2
#: (build step 5.1, the verifier's round: "the story-goal cooldown counts DECISIONS": in the live CH2 arm ten looks round
#: ROUTE 102, about 32,000 frames, passed while the walk to PETALBURG CITY waited out its 12 decisions) a STORY goal put
#: aside is tried again after `COOLDOWN_DECISIONS` decisions OR this many frames, whichever comes first: two looks round
#: (`LOOK_AROUND_FRAMES` 2,400 each) and their walking, a person's breather before trying the way again.
STORY_ASIDE_FRAMES = 6000
#: (build step 5.1, the verifier's round: the two walks to PETALBURG CITY that were put aside had met 8 and 13 battles on
#: ROUTE 102, which ate their 9,000 frames: the walk was not failing, the battles were long) a `go` whose budget ran out
#: walks on for the frames its battles took (at most its own budget again), at most this many times, when they took at
#: least `GO_BATTLE_MIN` frames.
GO_BATTLE_EXTENSIONS = 2
GO_BATTLE_MIN = 600
#: (build step 5.1, the verifier's second round: the live CH2T arm searched PETALBURG CITY door by door for its GYM, about
#: 25,700 frames: four houses, the MART and both floors of the POKéMON CENTER) the map constants of a GYM (`include/
#: constants/map_groups.h`: "PETALBURG_CITY_GYM" is entered from PETALBURG CITY), whose door a person RECOGNISES by its look
#: (`looks.gym_door`: METATILE_General_Door_Gym, the same in every city: checked against the decomp by
#: `gates/extract_milestones.py --verify`)
GYM_SUFFIX = "GYM"


def is_gym(const: str | None) -> bool:
    """(build step 5.1, the verifier's second round) Is map `const` a town's GYM ("PETALBURG_CITY_GYM")?"""
    return bool(const) and const.endswith(f"_{GYM_SUFFIX}")
#: (build step 5.1, the verifier's second round: "CH2T walked back to OLDALE to heal, and to shop, though PETALBURG has
#: both") a person hurt in a TOWN whose POKéMON CENTER it has not seen yet looks round that town for one (a town has one)
#: before walking back to the one it knows, for at most this many frames (one look round)
CENTER_LOOK_FRAMES = 3000
#: (build step 5.1, the verifier's second round) at most this many looks round "some more" on one map in one milestone
#: (build step 5.2: and only where something is left that it can walk to, `GoalManager.left_to_see`)
AGAIN_MAX = 2
#: (build step 5.2, replacing 5.1's OWED_STOP) a walk that ARRIVES on another outdoor map stops there once a map and
#: milestone when a BOREDOM draw passes (`GoalManager.curious_odds`), so the next decision may take a break there
BREAK_STOP = "arrived where it takes a break from the story"
#: (build step 5.2, the step-5.1 review's finding 2: "errands are filled by a quota, not interleaved") the most a curiosity
#: draw's odds rise to with boredom (`GoalManager.curious_odds`): never certain, the dice are always thrown
CURIOUS_ODDS_CAP = 0.9
#: ... and at most this many CURIOSITY goals in a row (no story or need goal between): CH1M ran six (a look round some more,
#: two chats, a look round, a look round some more, a detour) when the quota was short
CURIOUS_ROW_MAX = 2
#: (build step 5.2, the review's finding 1: "it loafs") the fewest NEW tiles seen that make a curiosity goal productive by
#: its tiles alone (one step into the unseen shows a row of 11 to 15; CH1M's look round of 3,012 frames showed 1)
YIELD_TILES_MIN = 8
#: ... and, for a walk whose purpose is to SEE (a look round, a detour: `SEEING_KINDS`), at least this many new tiles per
#: 1,000 of its OWN frames (the battles met in it not counted): what it showed must be worth the time it took. (Build
#: step 5.2, the round's development sweep step52dev2: with the 8 tiles alone, the LOAF control, looking round among tiles
#: it had stood on, was productive in 80 % of its frames, its looks round 0-11 new tiles per 1,000 frames outside battles
#: but for a few short ones, 3,000 frames bringing 9 tiles; the real code's 14 and more)
YIELD_TILE_RATE = 20
SEEING_KINDS = ("explore", "detour")
#: (build step 5.2, the review's finding 1: "people in the way" went from 8 to 61 at OLDALE) a place someone stood in the
#: way of this many times, with no new tile seen since the first, is BLOCKED for curiosity (`GoalRunner._PersonBlock`)
PERSON_BLOCK_HITS = 3
#: (build step 5.2) a look round that has seen nothing new (no tile, map, flag, Pokemon, item or experience) this many
#: frames is over (the navigator's own window is `navigator.NOVELTY_WINDOW`, 3,000: CH1M's two looks round OLDALE ran it
#: out twice, one tile in 6,000 frames)
CURIOUS_NOVELTY = 1500
#: (build step 5.2) the places a LOOK ROUND chooses: only those that can show something new (`look_round_intent`); 5.1's
#: look round also WANDERED among what it had seen once nothing else was left (`brain/explore.py` choose_target)
LOOK_KINDS = ("frontier", "grass", "people")
#: (the round's development sweep step51wdev1) what `skills/story.py` enter_door says of a door that CANNOT be walked into
#: (its tile below unknown or not walkable, or it did not open): such a door it saw is forgotten (`GoalRunner._go_inside`)
DOOR_UNUSABLE = ("the tile below the door at", "the door at ")
#: (the same) in danger a heal put aside is tried again at once (step 5), at most this many times in a row (a place that
#: fails at once would otherwise be chosen until the patience ran out)
DANGER_RETRIES = 3
#: (the same: seed 32's third look round put aside, begun 617 frames before its breather's end, ran 6,444 frames among the
#: grass's battles) a look round while a story goal is put aside is given the frames LEFT of the breather; with fewer than
#: this many left the story goal is tried again at once
ASIDE_LOOK_MIN = 600
#: (build step 5.2, the verifier's round) how far straight ahead of the player someone who SPOKE stands (`notice`): the
#: nurse and the MART clerk across their counter (two tiles: measured in the graded sweep's logs, "npc(0,-2)" facing up
#: while "Hello, and welcome to the POKéMON CENTER." and "Welcome!" were on screen), OLDALE's footprints man face to face
#: ("npc(1,0)" facing right during "Aaaaah! Wait! Please don't come in here.")
SPOKE_REACH = 2
FACING_STEP = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
#: (the same; its development sweep step52vdev2: remembering EVERY speaker, a scene's too, cut the chats with new words by
#: half: PROF. BIRCH's "MAY? Gone home, I think." in his lab had been 18 chats of the graded sweep with new words, every one
#: of them, and the rival's parents' and the rival's own) the goals whose talk is the AI's OWN and the same every time: a
#: SERVICE (the nurse's heal, the clerk's shop) or a chat it walked up for (a detour's included). Only who speaks while one of
#: these is the goal is remembered (`_Memory.hearing`); a scene's speaker may be chatted with once, and then is in `talked`
HEARD_KINDS = ("heal", "shop", "chat", "detour")
#: (build step 5.2, the verifier's round) the story goals with NO LEAD (nothing the game said names where to go: an
#: exploring `go`, and the look round while one is put aside): the walks that are LOST (`travel_intent(lost=True)`)
LOST_KEYS = ("go:?", "aside:go:?")
#: (the same) what such a walk says when nothing is left on any map it knows that it could get to
OUT_OF_IDEAS = "out of ideas"
#: (boss preparation round 2, USER RULING 59, spec section 2.1) a heal place this many known links away or fewer is NEAR
#: (`world_distance`): the raise's trainee is healed there; farther, with a Potion in the bag, a Potion on the spot
CENTRE_NEAR_LINKS = 2
#: (round 2) the field items a potion goal uses, weakest first (a seasoned player knows they heal 20 and 50)
FIELD_POTIONS = ("Potion", "Super Potion")
#: (round 2) a potion goal stops once the trainee is at this share of its max HP, or after this many items
POTION_TO = 2 / 3
POTIONS_PER_GOAL = 2
#: (round 2, V-m3) the goals whose frames, begun while a raise plan is active, count in its budget (the walks to heal
#: between raise sessions: the first spec's section 3.3 intent; BP-1's build counted only the raise goal)
PLAN_HEAL_KINDS = ("heal", "find_center", "potion")


@dataclass(frozen=True)
class Goal:
    """One intent: what (`kind`), why (`reason`, logged), and what it needs."""

    kind: str  # intro, go, use, talk, ask, follow, heal, shop, train, catch, pick_up, chat, look_around
    reason: str
    milestone: str | None = None
    map: str | None = None
    target: SeenObject | None = None
    look: str | None = None
    tile: tuple[int, int] | None = None
    steps: int = 0
    key: str = ""
    #: (heal, shop) the map key a door seen but never used stands on (`tile` is that door); None: the place is a map known
    via: str | None = None
    #: (a go with no hint yet) the words whose reading ends the goal: the AI decides again, now told where to go
    words: str | None = None
    #: (boss preparation round 2) the Pokemon a goal is FOR, by PID: a potion's target, a lead goal's member
    pid: int | None = None


@dataclass
class _Memory:
    """What the goal manager remembers across decisions in one run."""

    talked: set[str] = field(default_factory=set)  # "map|local id" of people talked to
    tried_items: set[str] = field(default_factory=set)  # "map|x,y" of item balls tried (and done with)
    item_tries: dict[str, int] = field(default_factory=dict)  # "map|x,y" -> walks to it begun
    catch_maps: set[str] = field(default_factory=set)  # maps where the catch draw was made
    chat_drawn: set[str] = field(default_factory=set)  # "map|local id" whose chat draw was made
    fails: dict[str, int] = field(default_factory=dict)  # goal key -> failures in a row
    cooldown: dict[str, int] = field(default_factory=dict)  # goal key -> the decision it may be tried again
    decisions: int = 0
    asked_rounds: dict[str, int] = field(default_factory=dict)  # milestone id -> rounds of asking done
    #: (map key, (x, y)) -> "pokemon_center" / "mart": a door SEEN by its look (the landmarks a person notices)
    landmarks: dict[tuple[str, tuple[int, int]], str] = field(default_factory=dict)
    #: milestone id -> {"steps": training steps, "sessions": n, "wild": wild battles met training, "won": of them won,
    #: "rests": sessions a rest stopped, "ready": trained (or put aside), "why_ready"}
    fight_prep: dict[str, dict] = field(default_factory=dict)
    #: (a look's name, map key) -> (x, y, the frame): where someone or something it RECOGNISES was last seen (the rival on
    #: ROUTE 103, seen while training there before it was time to talk to her)
    sightings: dict[tuple[str, str], tuple[int, int, int]] = field(default_factory=dict)
    #: page -> the frame it was last on screen: the pages READ in this run (as `world/memory.py` hears them), so a reason
    #: quotes the page that told it (`heard_page`)
    pages: dict[str, int] = field(default_factory=dict)
    #: (build step 5.1) map keys whose look-around draw was made in this session (one draw a new outdoor map; the maps the
    #: carried world memory knew when the session began are `known_before`, never drawn)
    looked: set[str] = field(default_factory=set)
    #: (build step 5.1) "map key|milestone id" whose detour draw was made (one draw a map and milestone)
    detoured: set[str] = field(default_factory=set)
    #: (build step 5.1, review #4) map const -> the highest level SEEN in a trainer's battle there (a person learns how strong
    #: the trainers of a route are by meeting one)
    seen_levels: dict[str, int] = field(default_factory=dict)
    #: (build step 5.1) the outdoor map the player last stood on (a battle's look has no map)
    last_map: str | None = None
    #: (build step 5.1, review #4) mart const -> the milestone index at which its list showed NO POKé BALLS (tried again
    #: only once the story has moved past it: a person comes back later)
    no_balls: dict[str, int] = field(default_factory=dict)
    #: (build step 5.1, review #4) times MOM was SEEN to heal the party (the party full again right after talking to her)
    home_heals: int = 0
    #: (build step 5.1) milestone id -> map key -> the tiles a scene sent the player back from (`GoalRunner.pursue`)
    scene_walls: dict[str, dict[str, set]] = field(default_factory=dict)
    #: (build step 5.1, the verifier's round: a run that carried on from an earlier run's memory "looked round a new place,
    #: LITTLEROOT_TOWN", its home town) the maps its WORLD MEMORY had stood on when this session's first decision was made
    #: (the memory is carried between sessions, `AI_PLAYER_WORLD`; this goal manager's own memory is not): no new places
    known_before: set[str] | None = None
    #: (build step 5.1) story goal key -> the frame its aside began (`STORY_ASIDE_FRAMES`)
    aside_from: dict[str, int] = field(default_factory=dict)
    #: (build step 5.1, the verifier's round) new places gone past in a row without a look round (`LOOK_DEBT`)
    passed_new: int = 0
    #: (build step 5.1, the verifier's second round) this session's goal frames: "story" and "errand" (`spent`); since build
    #: step 5.2 a REPORT only (the end record): nothing decides by it (5.1's `owed` quota is gone)
    spent: dict[str, int] = field(default_factory=lambda: {"story": 0, "errand": 0, "curious": 0})
    #: (the same) "map key|milestone id" -> looks round "some more" made there (`AGAIN_MAX`)
    again: dict[str, int] = field(default_factory=dict)
    #: (build step 5.2) "map key|milestone id" where a walk's arrival made its boredom draw (`BREAK_STOP`, once each)
    break_stops: set[str] = field(default_factory=set)
    #: (build step 5.2) the frame of the last PRODUCTIVE curiosity goal's end (the boredom clock, `curious_odds`); None until
    #: this session's first decision, which starts the clock
    curious_since: int | None = None
    #: (build step 5.2) curiosity goals chosen in a row, no story or need goal between (`CURIOUS_ROW_MAX`)
    curious_row: int = 0
    #: (build step 5.2) "map key|milestone id" -> why: a look round there brought nothing new (no look round there again in
    #: the milestone)
    exhausted: dict[str, str] = field(default_factory=dict)
    #: (build step 5.2) milestone id -> map key -> {tile: why}: places a curiosity goal could not get to (someone kept
    #: standing in the way; a detour that did not arrive): never chosen by curiosity again in the milestone
    blocked: dict[str, dict[str, dict]] = field(default_factory=dict)
    #: (build step 5.2) curiosity goals that brought nothing, and their frames (reported in the end record)
    idle: dict[str, int] = field(default_factory=lambda: {"goals": 0, "frames": 0})
    #: (the same) town map keys whose own POKéMON CENTER was looked for (`CENTER_LOOK_FRAMES`, once each)
    center_looked: set[str] = field(default_factory=set)
    #: (the same) map keys it LOOKED ROUND (an explore goal chosen there): a town looked round whose centre was not seen
    #: has none to look for
    explored: set[str] = field(default_factory=set)
    #: (the same) the last goal was decided with a Pokemon in the party: only those goals count in the balance (before
    #: its first Pokemon a person follows the opening of the story; the errands open up with a party)
    decided_with_party: bool = False
    #: (the round's development sweep) heal goal key -> times in a row it was tried again in danger (`DANGER_RETRIES`)
    danger_again: dict[str, int] = field(default_factory=dict)
    #: (build step 5.2, the verifier's round) "map key|local id" of the people who have SPOKEN to the player in its own
    #: service talk or chat (`notice`: someone straight in front of it, `SPOKE_REACH` tiles at most, while words were on the
    #: overworld screen and the goal was one of `HEARD_KINDS`): never chatted with (again): the nurse right after a heal, the
    #: clerk after a shop, someone chatted with in chapter 1. The play brain hands it the WORLD memory's set
    #: (`WorldMemory.spoke`), so a later session remembers whom it met.
    spoke: set[str] = field(default_factory=set)
    #: (the same) the goal being pursued is one of `HEARD_KINDS` (`GoalRunner.pursue` sets it for the goal's time)
    hearing: bool = False
    #: (build step 5.2, the verifier's round) (milestone id, `Navigator.stamp`) when a walk with NO LEAD found nothing left
    #: on any map it knows that it could get to (`travel_intent(lost=True)`): the next decision gives the run up
    #: (`next_goal`, "out of ideas") if nothing new has been seen since
    lost_end: tuple | None = None
    #: (R1, `brain/saving.py` SavePolicy: its whole state lives here, so a continue restores it with the rest, D16) milestone
    #: id -> the frame of the map change onto the gym it saved before the leader for (one save per APPROACH; None: the run
    #: began on the gym map)
    saved_for: dict[str, int | None] = field(default_factory=dict)
    #: (R1) its last save: {"id", "play_time": [h, m], "frame", "why"} (the 3-game-minute gap, `SAVE_MIN_MINUTES`)
    last_save: dict | None = None
    #: (R1) the save that is DUE: {"kind": center / moment / leader, "why", "map", "milestone", "entered", "told"}; the newest
    #: reason wins, one save satisfies it (a per-process clock: RESET by a continue)
    save_due: dict | None = None


def marks_of(look: Observation) -> dict[str, int] | None:
    return None if look.progress is None or not look.progress.marks else dict(look.progress.marks)


def party_share(look: Observation) -> float | None:
    mons = [m for m in look.party or () if not m.is_egg]
    if not mons:
        return None
    return sum(max(0, m.hp) for m in mons) / max(1, sum(m.max_hp for m in mons))


def strongest_level(look: Observation) -> int:
    return max((m.level for m in look.party or () if not m.is_egg), default=0)


def training_rest(look: Observation, heal_below: float, personality: str) -> str | None:
    """Why a person stops ROAMING the grass now, asked after every battle of a training or catching roam (the navigator's
    `battle_rest`): the party under the personality's `heal_below` share of its HP, or `brain/battle.py` needs_rest (the
    strongest Pokemon fainted or under a third). None: roam on. (Measured 2026-10-14, the step-5 verifier: with the rule
    never asked, the Story arm fled 8 battles in a row at 5/23 HP and the Trainer arm whited out twice on the walk home.)"""
    share = party_share(look)
    if share is not None and share < heal_below:
        return f"the party is at {share:.0%} of its HP (under the {personality}'s {heal_below:.0%})"
    return needs_rest(look.party)


def battles_lost(battle_log) -> int:
    """Battles LOST (the party fainted: a whiteout) among every battle the battler played (`Navigator.battle_log`): the
    ones inside a goal and the ones a scene raised alike (the play brain's `MAX_LOSSES` counts these)."""
    return sum(1 for _, _, outcome in battle_log if outcome == "lost")


def yield_snapshot(look: Observation, world, runner, battle_frames: int = 0) -> dict:
    """(build step 5.2) What a curiosity goal's YIELD is counted by, as the AI saw it (`goal_yield`, before and after the
    goal): the tiles its world memory has learned, the maps it has stood on, the item balls it picked up, the POKéDEX's
    owned and seen counts, and the pages of words it has read on the overworld; and `battle_frames`, the frames a battle
    was on screen so far in the run (`hands/waiting.py` BattleClock): the goal's own time is its frames less those."""
    progress = look.progress
    return {"tiles": world.tiles_learned, "maps": sum(1 for memory in world.maps.values() if memory.visits),
            "items": len(getattr(runner, "picked", ()) or ()),
            "caught": progress.dex_owned if progress is not None else None,
            "species": progress.dex_seen if progress is not None else None, "pages": len(world.heard),
            "battle_frames": battle_frames}


def goal_yield(goal: "Goal", before: dict, after: dict, outcome: str, frames: int = 0) -> dict:
    """(build step 5.2, the step-5.1 review's finding 1) What one goal BROUGHT (`yield_snapshot` before and after it), and
    whether that makes a curiosity goal PRODUCTIVE: at least `YIELD_TILES_MIN` new tiles seen (for a look round or a
    detour, `SEEING_KINDS`, also `YIELD_TILE_RATE` per 1,000 of its `frames` outside battles), a map first stood on, an
    item, a catch, a species first seen, words never read before, or a talk (a chat that talked; a detour that talked to
    the person it chose) THAT TOLD IT SOMETHING: since the verifier's round a talk that read no new words is no yield
    (`talks` says a talk was had, `talked` that it told something). A DETOUR is productive only when it REACHED the place it chose (its outcome says so: "reached"): on the way it
    brought no credit. (5.1 counted a curiosity goal by its kind and its frames: CH1M's two looks round OLDALE, 6,000
    frames and one new tile, were curiosity like any other.)"""
    made: dict = {}
    for key, value in before.items():
        now = after.get(key)
        made[key] = max(0, now - value) if isinstance(value, int) and isinstance(now, int) else 0
    # a chat's outcome is the talk's own ("talked ..."); a detour's says it after its arrival ("reached ...; talked ...")
    talk = goal.kind in ("chat", "detour") and (outcome.startswith("talked") or "; talked" in outcome)
    # (build step 5.2, the verifier's round: 127 chats of the graded sweep's real plans heard NOTHING new and were credited
    # "a talk": 60 POKéMON CENTER nurses right after the heal that had just talked to them, the party full, 46 MART clerks
    # right after the shop, 21 times OLDALE's footprints man right after his own scene; 1,747-1,957 frames each for the
    # nurse) a talk is a yield only when it TOLD it something: words it had never read (the label alone is no yield: the
    # step-5.1 review's "grade the property, not the label" again)
    made["talked"] = bool(talk and made.get("pages"))
    made["talks"] = bool(talk)
    reached = goal.kind != "detour" or outcome.startswith("reached")
    made["reached"] = reached
    # (step52dev2) the goal's OWN time: its frames less the battles met in it (a look round in the grass meets them)
    walking = max(0, frames - made.get("battle_frames", 0))
    made["walking"] = walking
    seen = made["tiles"] >= YIELD_TILES_MIN and (goal.kind not in SEEING_KINDS
                                                 or made["tiles"] * 1000 >= YIELD_TILE_RATE * walking)
    made["productive"] = bool(reached and (seen or made["maps"] or made["items"] or made["caught"] or made["species"]
                                           or made["pages"] or made["talked"]))
    return made


#: (build step 5.2) how far round a place curiosity was turned back from is still "the same corner" (`_beside`): measured,
#: the detours that chose the place NEXT to one a look round had just given up at LITTLEROOT's twin were 1 tile from it in
#: step52dev2 (seeds 1002, 1010) and 2 tiles in step52dev3 (seed 1013: (5, -4) after (3, -3))
BESIDE = 2


#: (build step 5.2, the verifier's round) why a place was blocked for curiosity by a SCENE (`_scene_corners`)
SCENE_BLOCKS = ("a scene began here", "a scene stopped the way there")


def _scene_corners(places: dict) -> set:
    """(build step 5.2, the verifier's round; its development sweep step52vdev5, CH2 seed 1242: PETALBURG's "Hiya! Are you
    maybe... A rookie TRAINER?" turned a look round back at (8, 10) and (8, 12), and the detour after it walked round both into
    the same scene at (8, 13), 1,800 frames of it) the tiles BESIDE each place a scene blocked for curiosity (`SCENE_BLOCKS`):
    a scene's trigger is a line of tiles across a way, of which the AI has met only some; curiosity keeps out of the corner."""
    out: set = set()
    for (x, y), why in places.items():
        if str(why).startswith(SCENE_BLOCKS):
            out |= {(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)}
    return out


def _beside(tile: tuple[int, int], places) -> bool:
    """(build step 5.2) `tile` is one of `places` or within `BESIDE` tiles of one: the same corner of a map, for a person
    who was turned back from it."""
    return any(abs(tile[0] - x) <= BESIDE and abs(tile[1] - y) <= BESIDE for x, y in places)


def _known_reach(memory, start: tuple[int, int], walls) -> set[tuple[int, int]]:
    """(build step 5.2) Every tile the player can WALK to from `start` over tiles it KNOWS (`navigator.step_from` with no
    unknown tile), `walls` (people standing now, blocked places) left out: where a curious person can actually go."""
    seen, frontier = {start}, [start]
    while frontier:
        here = frontier.pop()
        for direction in DIRECTIONS:
            step = step_from(memory, here, direction, walls, 0.0, allow_unknown=False)
            if step is not None and step[0] not in seen:
                seen.add(step[0])
                frontier.append(step[0])
    return seen


#: A roam's report line (`skills/roam_train.py` RoamReport.line): its numbers, for a roam that STOPPED early (a rest, an
#: item ball): the roam skill writes its metrics record only when it runs its steps out. With a battler (build step 4 on)
#: the line also says how the battles ENDED (won, caught, lost); "fled" is then the battles RUN from (the step-5
#: verifier's round 2: it counted every battle that ended without a stop, so a roam that won 5 of 5 said "4 fled").
ROAM_LINE = re.compile(r"roam: (\d+) training steps \((\d+) pressed, (\d+) ran into a battle or a scene\).*?\((\d+) spins = "
                       r"(\d+) reversals \+ (\d+) in place.*?(\d+) wild encounters, (\d+) fled"
                       r"(?:, (\d+) won, (\d+) caught, (\d+) lost; (\d+) trainer battles)?")


def roam_numbers(outcome: str) -> dict | None:
    found = ROAM_LINE.search(outcome)
    if found is None:
        return None
    keys = ("steps", "attempts", "interrupted", "spins", "reversals", "in_place", "encounters", "fled", "won", "caught",
            "lost", "trainers")
    return {key: int(value) for key, value in zip(keys, found.groups()) if value is not None}


#: A map NAMED like a town, a city or a route, as opposed to an interior. (KI-128, 2026-10-31) This is a NAME pattern, and
#: it is narrower than "a map a person sees the name of when they walk onto it": PETALBURG_WOODS (a route by its map type,
#: a forest a person walks through) and EVER_GRANDE_CITY (the second underscore) fit that class and miss the pattern.
#: `open_way` is the predicate that matches the class; this pattern stays where a NAME is what counts (the errands: a
#: "town" whose centre is looked for, a new outdoor map to look round, the curiosity and detour rules).
OUTDOOR = re.compile(r"^(ROUTE\d+|[A-Z]+_(TOWN|CITY))$")


def open_way(const: str | None) -> bool:
    """(KI-128, 2026-10-31) Is map `const` OPEN COUNTRY, a place a person walks through on the way somewhere (a route, a
    town, a city, an ocean route, a forest such as PETALBURG WOODS), as opposed to an interior? Named like one (`OUTDOOR`),
    or so by its STATIC map type, which a person knows from the map-name popup, the look of the place and a guide's map
    (USER RULINGS 40 and 45: static game knowledge; `knowledge/atlas.py` open_map, None for a map the atlas does not hold,
    which then counts by its name alone). Used ONLY where the woods were measured to break the walk on (KI-128): where an
    open goal is looked for (`lead_toward`) and which ways back a walk may take (`keeps_going`). WHY: in all three A0 runs
    the AI never reached the woods' north half: `lead_toward` evicted it from the woods (no early return there, the woods
    no lead) and `keeps_going` refused the way back in, so it walked ROUTE 104's south and PETALBURG's edge for the rest of
    the run."""
    return bool(OUTDOOR.match(const or "")) or open_map(const) is True


#: (KI-134 V3) the last `region_hops` worked out (`part_hops`): (the world memory it was for, what for, the hops). ONE
#: entry, held by REFERENCE (never by `id()`, which the next object may reuse once one is freed: the verifier's NIT V8), so a
#: run's one world memory is searched once a decision, not once per place ranked
_PART_HOPS: list = [None]


def part_hops(world) -> dict[str, int] | None:
    """(KI-134 V3, 2026-11-06) The links from WHERE THE PLAYER STANDS to every map a walk from there is known to get to
    (`explore.region_hops`, round what stands on each map: `explore.standing_walls`); None when the player's tile or map
    is not known. Worked out once for each place the player stands and each new thing the memory has seen (its `stamp`,
    its links and their uses), and kept for that."""
    start, at = world.current, world.position
    if start is None or at is None or world.maps.get(start) is None:
        return None
    uses = sum(int(link.get("uses") or 0) for link in world.warps.values())
    asked = (start, tuple(at), world.stamp(), len(world.warps), len(world.connections), uses)
    kept = _PART_HOPS[0]
    if kept is not None and kept[0] is world and kept[1] == asked:
        return kept[2]
    hops = region_hops(world, start, at, standing_walls(world))
    _PART_HOPS[0] = (world, asked, hops)
    return hops


def world_distance(world, key: str) -> int:
    """How many known links (warps, connections) lie between the current map and map `key` (99 when no way is known).

    (KI-134 V3, 2026-11-06) FROM WHERE THE PLAYER STANDS, when its tile is known: the links of the route over the PARTS of
    maps a walk gets to (`part_hops`, `explore.region_hops`). WHY (the KI-134 verifier's K134-V3, on probe-C1's chapter-5
    memory): counted by maps, ROUTE 104 touches both PETALBURG and RUSTBORO, so from its north strip the two centres were
    equally near and the tie went to PETALBURG's (its name sorts first), four links away through the woods, when RUSTBORO's
    is two. The heal and shop places (`GoalRunner._nearest_place`), the open map to head for (`lead_toward`) and the grass
    to train in (`_grass_map`) all rank by this. A map no walk from here is known to get to (a door whose arrival was
    never recorded leads to no part: `route_to`) counts by maps, exactly as before."""
    start = world.current
    if start is None:
        return 99
    hops = part_hops(world)
    if hops is not None and key in hops:
        return hops[key]
    seen, frontier = {start}, [(start, 0)]
    while frontier:
        here, depth = frontier.pop(0)
        if here == key:
            return depth
        for kind, link in ways_from(world, here):  # (chapter 6 NS2) a ride counts as a link too
            if kind == "warp" and not looks_like_exit(world, here, link.get("tile")):
                continue  # a "warp" from a tile that is no way out (a scene's, from the grass) is no way to walk (route_to)
            target = link.get("to") if kind in ("warp", "ride") else link.get("target")
            if target is not None and target not in seen:
                seen.add(target)
                frontier.append((target, depth + 1))
    return 99


#: (chapter 7 NS4, 2026-11-06) `world_distance` for a map no known way leads to (no link, no ride)
UNREACHABLE = 99


def inside_grass(memory) -> list:
    """Tall grass tiles INSIDE map `memory` (none past its edges: those are the next map's)."""
    return [xy for xy in memory.grass() if xy[0] >= 0 and xy[1] >= 0 and not memory.outside(xy)]


def grass_target(world, fight_maps=()) -> tuple[str, str | None]:
    """Where a training (or catching) roam goes: ("here", None) when this map has grass of its own; ("there", map const)
    for the map with grass nearest by the known way, the fight's own maps (`fight_maps`) first; ("none", None) when it
    has seen no grass at all (the roam stays, as before); ("out of reach", None) when it has seen grass but no known way
    leads to any of it. (Chapter 7 NS4, 2026-11-06) grass no known way leads to (no link, no ride: `world_distance`
    `UNREACHABLE`) is no place to train: probe7 C1, on the island with no way back known, chose 16 train errands for the
    mainland's grass (`GoalManager.next_goal` chooses no training then)."""
    here = world.here()
    if here is not None and inside_grass(here):
        return "here", None
    options = []
    for key, memory in world.maps.items():
        if memory.visits and inside_grass(memory) and memory.const:
            first = 0 if memory.const in fight_maps else 1
            options.append((world_distance(world, key), first, memory.const))
    if not options:
        return "none", None
    options = [option for option in options if option[0] < UNREACHABLE]
    return ("there", min(options)[2]) if options else ("out of reach", None)


def lead_toward(world, goal_const: str | None) -> str | None:
    """Heading for a map it has NOT been to (`goal_const` unknown to its memory): the open map (`open_way`: a town, a route,
    the woods; KI-128) it HAS been to where the most is left to see (`WorldMemory.promise`: frontier, exits not used, roads), routes before towns, nearer first; None
    when the goal is known, or nothing promising is known. A person who is told "ROUTE 103" and has seen only Littleroot
    and part of ROUTE 101 walks on up ROUTE 101, not into the houses. (The chapter-5 search fix K1, 2026-11-13) A place
    that is no open country and whose name no town holds (a cave, a tunnel): the map a seasoned player knows it is entered
    from, where it has been (`entry_lead`)."""
    if goal_const is not None and any(memory.const == goal_const for memory in world.maps.values()):
        return None
    if goal_const is not None and not open_way(goal_const):
        # a building's room: found in its own TOWN (the name says which: "PETALBURG GYM" is in PETALBURG CITY), so a person
        # who has been to that town walks there first (measured 2026-10-14, the chapter-2 development run c2b: told of
        # the gym while catching on ROUTE 102, it explored ROUTE 102's grass for two 9000-frame budgets); found inside, by
        # its stairs, when the player is in that town or one of its buildings already (None)
        here = world.here()
        towns = [m.const for m in world.maps.values() if m.const and OUTDOOR.match(m.const) and m.visits
                 and goal_const.startswith(f"{m.const}_")]
        town = max(towns, key=len) if towns else None
        there = here is not None and (here.const == town or str(here.const or "").startswith(f"{town}_"))
        if town is None:
            # (K1) no town's name holds it: the map it is entered from, as a seasoned player knows (None as before when it
            # stands on one, has been to none, or knows no way to one)
            return entry_lead(world, goal_const)
        return town if town is not None and not there else None
    here = world.here()
    if here is not None and open_way(here.const) and world.promise(here.key) > 0:
        return None  # out in the open with something left to see here: look on from here
    options = []
    for key, memory in world.maps.items():
        const = memory.const or ""
        if not open_way(const) or not memory.visits or key == world.current:
            continue
        promise = world.promise(key)
        if promise <= 0:
            continue
        options.append((world_distance(world, key), -(1 if const.startswith("ROUTE") else 0), -promise, const))
    return min(options)[3] if options else None


class Lead(str):
    """(The chapter-5 search fix K1, 2026-11-13) A map `lead_toward` names, carrying WHY it is the lead (`why`), which
    `GoalRunner._travel_on` tells. A lead given as a plain string is where the most is left to see."""

    why = "where the most is left to see"


#: (K1) the words a seasoned player's lead gives (`entry_lead`), as `knows_gym`'s and `GYM_BACK`'s do
WAY_IN = "a seasoned player's knowledge"


def entry_lead(world, goal_const: str) -> Lead | None:
    """(The chapter-5 search fix K1, 2026-11-13) A SEASONED PLAYER'S LEAD toward a place never seen that is no open country
    and whose name no town holds (a cave, a tunnel: `lead_toward`'s building rule finds no town). Of the maps the place is
    entered from (`knowledge/atlas.py` entry_maps: a guide's map, USER RULING 40, "the maps and their connections"), the
    OPEN map (`open_way`) it HAS stood on that is nearest by the known way (`world_distance`). None while the player stands
    on one of them (the search there is the explorer's own taste), and None when it has stood on none of them or knows no
    way to any (a person heads only where they know the way): then the walk is as before.
    WHY (the E0 chapter 1-5 check, 2026-11-13, seeds 6481-6483): told of RUSTURF TUNNEL, the two runs that missed searched
    ROUTE 104 and PETALBURG WOODS for it, back and forth, until the frame budget or the patience ran out, while ROUTE 116,
    the tunnel's way in and a map they had walked, was never a lead (`lead_toward` gave None: the tunnel is no open country
    and no town's name holds it). A seasoned player knows the tunnel is on ROUTE 116, east of RUSTBORO.
    NOT A ROUTE PLANNER (KI-128's rejection, 06 2026-10-31): it names ONE MAP; the walk there is the AI's own explorer over
    the links it has walked itself, and on that map the search for the way in is its own: no tile of the warp is read (no
    beeline, RULING 40)."""
    entries = entry_maps(goal_const)
    here = world.here()
    if not entries or (here is not None and here.const in entries):
        return None
    options = []
    for key, memory in world.maps.items():
        if memory.const in entries and memory.visits and open_way(memory.const):
            hops = world_distance(world, key)
            if hops < UNREACHABLE:
                options.append((hops, memory.const))
    if not options:
        return None
    lead = Lead(min(options)[1])
    lead.why = f"{WAY_IN}: {lead} has a way into it"
    return lead


#: The places that keep the player ON the map it searches (`travel_intent(stay=True)`): no road, exit or way back off it.
ON_THE_MAP = ("frontier", "grass", "people", "wander")


def keeps_going(world, target: Target, goal_map: str | None, stay: bool = False) -> bool:
    """`travel_intent`'s rule: a way BACK into a building already visited (an interior, not open country, `open_way`: a
    town, a route, the woods; and not the goal itself) is no option for someone going somewhere; every other place is. `stay`: someone SEARCHING this map
    (for the rival on ROUTE 103, the nurse at the back of the centre) keeps to places on it."""
    if stay:
        return target.kind in ON_THE_MAP
    if target.kind != "back" or target.exit is None:
        return True
    link = world.link_of(world.current, target.exit)
    inside = world.maps.get(link.get("to")) if link else None
    return inside is None or open_way(inside.const) or inside.const == goal_map


def worth_going(target: Target) -> bool:
    """(build step 5.2, the verifier's round) Is `target` a place where something may be learned: somewhere new (a frontier,
    a road, a door, a route, grass, someone not met: `ONWARD_KINDS`) or a way back to a map with something left to see?
    Not a way back to a map seen all of, nor straight back the way it came."""
    return target.kind in ONWARD_KINDS or (target.kind == "back" and SEEN_ALL not in target.reason
                                           and JUST_COME_FROM not in target.reason)


def shut_in(world) -> bool:
    """(build step 5.2, the verifier's round; found by its first development sweep: the chapter-1 runs gave up inside the
    moving truck) Is the player on a map with NO way out it knows of: no exit tile seen, no road past an edge, no link (a
    warp or a connection) from it? Then it waits for something to open; it is not out of ideas."""
    here = world.here()
    return here is None or not (here.exits() or here.roads() or world.links_from(world.current))


def lost_way(nav: Navigator, look: Observation, weights, moving: bool) -> tuple[Target | None, list]:
    """(build step 5.2, the verifier's round) For a walk with NO LEAD on a map where nothing is worth going to: the way
    toward the nearest map it knows (by the known links, `explore.route_to`) where something is still left that it could
    get to (`WorldMemory.left_anywhere`), and that list. (None, []): nothing is left on any map it knows."""
    left = [(key, n) for key, n in nav.world.left_anywhere() if key != nav.world.current]
    if not left:
        return None, []
    keys = {key for key, _ in left}
    ways = [t for t in candidates(nav, look, weights, lambda memory, key: key in keys, jitter_on=not moving)
            if t.kind == "route"]
    if not ways:
        return None, left
    names = nav.world.names()
    best = max(ways, key=lambda t: t.score)
    return replace(best, reason=f"lost: {best.reason}: somewhere it knows something is left to see "
                                f"({', '.join(f'{names.get(k, k)} {n}' for k, n in left[:4])})"), left


#: (chapter 6 stops round 6, round 5's new stop P5-1) the reason a walk to the back of a gym gives (`gym_back`)
GYM_BACK = "the back of the gym, opposite its door: a gym's leader stands there (a seasoned player's knowledge)"


def gym_back(nav: Navigator, look: Observation, gym: str | None = None) -> Target | None:
    """(chapter 6 stops round 6, round 5's new stop P5-1) THE BACK OF A GYM: where a person who has come to FIGHT the
    leader walks to find them, through the gym and the trainers in the way. A seasoned player knows a gym's leader stands at
    its back, the side opposite its door (USER RULING 40: static knowledge of every gym; the AI is never told a tile). Of
    the known walkable tiles of this map a walk from here reaches (`navigator.distances`), the one farthest from the door it
    knows nearest to it (its `exits`) across the gym (by rows), the one nearest the door's column on a tie, then the nearer
    by the walk. None when no door, no player's tile, or no such tile is known. (Chapter 6 stops round 7, VR6-1) None, too,
    on a map that is not a gym, or not `gym` (the leader's gym the find was made for): a find whose back was excluded
    walked out to the TOWN and was offered "the back of the gym" there (the round-6 verifier's VT6-3).
    LIMIT (the round-6 verifier's VR6-2): "the farthest row from the door" is the leader's own tile in RUSTBORO's and
    DEWFORD's gyms (chapters 4 and 7, measured on the pinned layouts); MAUVILLE's, FORTREE's and PETALBURG's leaders do not
    stand there (rooms, side columns, intra-map doors), so a find there in the rare state this serves (the gym fully known,
    no sighting) is not proven: define the back by the gym's rooms before chapter 9."""
    found = nav.where(look)
    if found is None:
        return None
    memory, here = found
    if not is_gym(memory.const) or (gym is not None and memory.const != gym):
        return None
    doors = memory.exits()
    if not doors:
        return None
    door = min(doors, key=lambda xy: (abs(xy[0] - here[0]) + abs(xy[1] - here[1]), xy))
    reach = distances(memory, here, nav.walls(memory, here), 0.0)
    tiles = [xy for xy in reach if xy != here and xy not in doors and memory.passable(xy) and not memory.outside(xy)]
    if not tiles:
        return None
    tile = min(tiles, key=lambda xy: (-abs(xy[1] - door[1]), abs(xy[0] - door[0]), reach[xy], xy))
    return Target("goto", tile, f"{GYM_BACK}: {tile}")


def travel_intent(goal_map: str | None, personality: str, budget: int, done: Callable[[Observation], bool],
                  stay: bool = False, back: Callable[[Navigator, Observation], Target | None] | None = None) -> Intent:
    """`brain/explore.py` explore_intent's taste and walk, for a person who is GOING somewhere: the ways BACK into a building
    already visited (a house, the lab: an interior, not a town or a route) are no option (measured 2026-10-14, the play
    brain's first chapter-1 run: told "ROUTE 103" in the rival's house, the explorer went up and down its stairs for the
    unseen corners of the bedroom until its ping-pong rule stopped it, eight times). Everything else is the explorer's own
    (`candidates`, `pick`, `pick_on_the_move`, `carry_on`); with nothing left it falls back to `choose_target` (never
    idle). (Chapter 6 stops round 6, P5-1) `back`: where a search of this map goes when nothing on it is left to see,
    before that fallback (`gym_back`: the leader it has come to fight, at the back of the gym), until it is reached; the
    fallback's best place was the way back OUT (#108: 21 entries onto DEWFORD's gym a run, each find ended on the door's
    ping-pong)."""
    weights = weights_for(personality)
    backed: list = []  # (round 6, P5-1) the back of the gym, once reached

    def goal(memory, key: str) -> bool:
        return goal_map is not None and memory is not None and memory.const == goal_map

    def choose(nav: Navigator, look: Observation) -> Target | None:
        moving = nav.choosing_on_the_move
        found = [t for t in candidates(nav, look, weights, goal if goal_map else None, jitter_on=not moving)
                 if keeps_going(nav.world, t, goal_map, stay)]
        located = nav.where(look)
        if not found and back is not None and not backed and located is not None:
            target = back(nav, look)
            if target is not None and not nav.is_excluded(target):
                return target
        if not found or located is None:
            return choose_target(nav, look, weights, goal if goal_map else None)
        if moving:
            return pick_on_the_move(found, located[1], nav.heading())
        return pick(found, nav.rng)

    def carry(nav: Navigator, look: Observation, old: Target) -> Target | None:
        return carry_on(nav, look, weights, old, goal if goal_map else None)

    def reached(target: Target) -> None:
        if target.reason.startswith(GYM_BACK):
            backed.append(target.tile)

    return Intent(f"travel to {goal_map}" if goal_map else "look around", budget, choose, done,
                  reached=reached if back is not None else None, carry_on=carry)


def lost_intent(personality: str, budget: int, done: Callable[[Observation], bool], told: Callable[[str], None]) -> Intent:
    """(build step 5.2, the verifier's round: the graded NOHINTS runs, 20 of 20, pressed for 31,676-62,012 frames with nothing
    new: through OLDALE's house door and back for up to 98 goals in a row, each ended by the ping-pong rule and the next
    starting from none, or across OLDALE's bottom edge and back, "seen all of" both ways, until the story's patience) A
    walk with NO LEAD (`LOST_KEYS`: nothing the game said names where to go): `travel_intent(None)`'s taste and walk, but
      * never through a warp that ENDED an earlier intent as a ping-pong while nothing new has been seen anywhere since
        (`Navigator.ponged_now`), unless it is the only way left;
      * never to a frontier tile a walk found no way to, or stood on with its unseen side staying unseen, while the map
        shows nothing new (`WorldMemory.unreached`: seed 903 chose OLDALE's nine tiles past the footprints man 41 times
        each, every goal trying them again);
      * when nothing here is worth going to (`worth_going`), it heads for the nearest map it knows where something is left
        that it could get to (`lost_way`), not to a whim among what it has seen; and when NOTHING is left on any map it
        knows, it does not wander: it is done (None), and `told(why)`: the goal manager gives the run up (out of ideas)."""
    weights = weights_for(personality)

    def lost_choose(nav: Navigator, look: Observation) -> Target | None:
        moving = nav.choosing_on_the_move
        world = nav.world
        here = world.here()
        tiles = len(here.tiles) if here is not None else -1
        gone = world.unreached.get(world.current, {}) if here is not None else {}
        found = [t for t in candidates(nav, look, weights, None, jitter_on=not moving)
                 if keeps_going(world, t, None) and not (t.kind == "frontier" and gone.get(t.tile) == tiles)]
        found = [t for t in found if not nav.ponged_now(t)] or found
        located = nav.where(look)
        if located is not None and not any(worth_going(t) for t in found):
            # (step52vdev3, NOHINTS seed 1223: OLDALE <-> ROUTE 103 across the edge, each "where something is left" seen
            # from the other) nothing here is worth going to: what this map's promise counted cannot be had as things are
            world.mark_spent(world.current)
            way, left = lost_way(nav, look, weights, moving)
            if way is not None:
                return way
            # (the round's first development sweep, step52vdev1: three of four chapter-1 runs gave up INSIDE THE MOVING
            # TRUCK, 26 frames into their first goal, before its door had opened) a person SHUT IN, on a map with no way out
            # it knows of (no exit, no road, no link), is not out of ideas: something will open; it waits, as before
            if not left and not shut_in(world):
                told(f"{OUT_OF_IDEAS}: nothing is left to see that it could get to on any of the "
                     f"{sum(1 for memory in world.maps.values() if memory.visits)} maps it knows, and no hint it goes by "
                     f"names where to go")
                return None
        if not found or located is None:
            return choose_target(nav, look, weights, None)
        if moving:
            return pick_on_the_move(found, located[1], nav.heading())
        return pick(found, nav.rng)

    def lost_carry(nav: Navigator, look: Observation, old: Target) -> Target | None:
        return carry_on(nav, look, weights, old, None)

    return Intent("look around", budget, lost_choose, done, carry_on=lost_carry)


def look_round_intent(personality: str, budget: int, done: Callable[[Observation], bool],
                      blocked: Callable[[str | None], dict]) -> Intent:
    """(build step 5.2, the step-5.1 review's finding 1: "it loafs") LOOKING ROUND a place as a curious person does: only
    the places that can show something NEW (`LOOK_KINDS`: a frontier, grass not walked, someone not met), by the explorer's
    own taste and walk (`candidates`, `pick`, `pick_on_the_move`, `carry_on`), never a place curiosity found BLOCKED
    (`blocked(map key)`: someone kept standing in the way, a detour that did not arrive) and never carried on from one;
    with nothing new left it is DONE looking (`None`: the navigator's "nothing left to try"), never a wander among what it
    has seen (5.1's look round, `travel_intent(stay=True)`, fell back to `choose_target`'s wander: CH1M walked OLDALE for
    3,001 frames and saw nothing); and it ends after `CURIOUS_NOVELTY` frames with nothing new."""
    weights = weights_for(personality)

    def look_choose(nav: Navigator, look: Observation) -> Target | None:
        moving = nav.choosing_on_the_move
        avoid = blocked(nav.world.current)
        found = [t for t in candidates(nav, look, weights, None, jitter_on=not moving)
                 if t.kind in LOOK_KINDS and t.tile not in avoid]
        located = nav.where(look)
        if not found or located is None:
            return None
        if moving:
            return pick_on_the_move(found, located[1], nav.heading())
        return pick(found, nav.rng)

    def look_carry(nav: Navigator, look: Observation, old: Target) -> Target | None:
        if old.tile in blocked(nav.world.current):
            return None
        carried = carry_on(nav, look, weights, old, None)
        return carried if carried is None or carried.tile not in blocked(nav.world.current) else None

    return Intent("look round", budget, look_choose, done, carry_on=look_carry, novelty_window=CURIOUS_NOVELTY)


#: The characters a WORD is made of when a page is searched for a hint's words: letters (POKéMON's é included), digits and
#: the apostrophe ("o'clock" is one word, not "clock").
_WORD_CHARS = r"\w'’"


def _names(page: str, words: str) -> re.Match | None:
    """Where `page` says `words` as WHOLE words (case-insensitive, spaces normalised: a page's line breaks), or None.
    (The step-5 verifier's round 2, 2026-10-14: a substring test heard "LAB" in "not avaiLABle", "BAG" in "BAGgage" and
    "clock" in "o'clock".)"""
    want = re.escape(" ".join(words.split()).lower())
    return re.search(rf"(?<![{_WORD_CHARS}]){want}(?![{_WORD_CHARS}])", " ".join(page.split()).lower())


def heard_words(heard: set[str], words: str | None) -> bool:
    """Has the AI READ `words` on screen (`world/memory.py` heard: every page read on the overworld), as whole words?"""
    if not words:
        return True
    return any(_names(page, words) is not None for page in heard)


def heard_page(heard: set[str], words: str, recent: dict[str, int] | None = None) -> str | None:
    """The page the AI READ that says `words` (whole words), for a reason to QUOTE: the one read most recently in this
    run (`recent`: page -> the frame it was last on screen, `GoalManager.notice`), else (a page of an earlier run's
    memory) the first in order. None when no page says them. (The step-5 verifier's round 2: the reason quoted the
    milestone's stored line, "MAY: Well, it's time to head back to the LAB.", in a run whose rival was BRENDAN.)"""
    found = [page for page in heard if _names(page, words) is not None]
    if not found:
        return None
    recent = recent or {}
    return min(found, key=lambda page: (-recent.get(page, -1), page))


def quote(page: str, words: str, width: int = 110) -> str:
    """`page` as a reason quotes it: whole when short, else the part around `words`."""
    page = " ".join(page.split())
    if len(page) <= width:
        return page
    found = _names(page, words)
    start = max(0, (found.start() if found else 0) - width // 3)
    end = min(len(page), start + width)
    return ("..." if start else "") + page[start:end] + ("..." if end < len(page) else "")


class GoalManager:
    """Chooses the next goal (module docstring). `story` the milestones for this player; `state` the personality as it
    plays; `rng` its own seeded stream (`<seed>:goals`); `hints_off` / `train_off` the step-5 FAULT switches; `errands_off`
    (build step 5.1) the BEELINE control: no look-around, no detour, no new-map stop, no chat, no catching roam."""

    def __init__(self, story: Story, state: PersonalityState, rng: random.Random, hints_off: bool = False,
                 train_off: bool = False, errands_off: bool = False) -> None:
        self.story = story
        self.state = state
        self.rng = rng
        self.hints_off = hints_off
        self.train_off = train_off
        self.errands_off = errands_off
        self.memory = _Memory()
        #: (build step 5.1) where a draw that chose NO errand is told (the play brain sets its `tell`): a reason is logged
        #: for every draw, made or not, so the rates can be read from the log
        self.say: Callable[[str], None] | None = None
        #: (R1, build spec 2026-10-29 D2/D3) WHEN to save (`brain/saving.py` SavePolicy over this manager's memory) and the
        #: run's frames left; set by the play brain only when it keeps a memory file (D14), else None: no save goal ever
        self.saving = None
        self.frames_left: Callable[[], int] | None = None
        #: (boss preparation BP-1, 2026-11-09) the run's own `<seed>:bossprep` stream (the play brain sets it: no other
        #: stream moves), the signature of the last verdict run (party and boss: the verdict runs again only when it
        #: changes), and the next boss as (its milestone id, its leader's name, its gym map)
        self.bossprep_rng: random.Random | None = None
        self._bp_seen: tuple | None = None
        self.bp_boss: tuple[str, str, str | None] | None = None
        #: (round 2) the boss preparation's FAULT switches (test side, `brain/bossprep.py` BossprepFaults): none in play
        self.bp_faults = NO_FAULTS

    def _say(self, line: str) -> None:
        if self.say is not None:
            self.say(line)

    # ------------------------------------------------------------------ the story
    def milestone(self, look: Observation, visited: Callable[[str], bool]) -> tuple[int, Milestone | None]:
        """The current milestone: the first not proven by the marks; a WAYPOINT (a map no save flag records) counts as
        passed once the AI has stood on that map (`visited`); an OPTIONAL milestone (build step 5.1: the gym's trainers,
        whom the path to the leader may never meet) is never the current one."""
        marks = marks_of(look) or {}
        for number, milestone in enumerate(self.story.milestones):
            if milestone.optional:
                continue
            if milestone.done(marks) is True:
                continue
            if milestone.waypoint is not None and visited(milestone.waypoint):
                continue
            return number, milestone
        return len(self.story.milestones), None

    def may_look_around(self, look: Observation, world, step: Step | None) -> bool:
        """(build step 5.1) Is the LOOK-AROUND's draw due here: an outdoor map NEW TO IT (its world memory, carried between
        sessions, had not stood on it when this session began: `known_before`) whose draw is not made yet (one a map), not
        under the beeline control, the party not in danger (a person heals first), not the intro, and not where the story's
        own next thing is, told and HERE (it looked round ROUTE 101 while PROF. BIRCH cried "Help! In my BAG!"). A draw a
        danger, the intro or the story held back is made on a later decision there."""
        here = world.here()
        const = here.const if here is not None else None
        if (self.errands_off or here is None or not OUTDOOR.match(const or "") or world.current in self.memory.looked
                or world.current in (self.memory.known_before or ()) or (step is not None and step.do == "intro")):
            return False
        if self.left_before(world):
            # (build step 5.2, the step-5.1 review's finding 6: CH1M said "a new place, OLDALE_TOWN" after healing there
            # twice: `known_before` was frozen at the session's start) a map it has LEFT once is known: a later visit is no
            # new place, whether or not its draw was made on the first
            return False
        mons = [m for m in look.party or () if not m.is_egg]
        if mons and (any(m.hp <= 0 for m in mons) or needs_rest(look.party) is not None):
            return False
        return not self._story_here(step, world)

    def _story_here(self, step: Step | None, world) -> bool:
        """The story's own next thing is told and HERE (a `use`, `talk`, `ask` or `follow` on this map, its words heard):
        no look round now (PROF. BIRCH's "Help! In my BAG!")."""
        here = world.here()
        const = here.const if here is not None else None
        return (step is not None and step.map is not None and step.map == const and step.do != "go"
                and self.step_known(step, world.heard, world))

    # ------------------------------------------------------------------ the balance (build step 5.1, the verifier's 2nd round)
    def spent(self, goal: Goal, frames: int, story_moved: bool = False) -> None:
        """A finished goal's frames, into this session's count (`owed`): an ERRAND's (`ERRAND_KINDS`: needs and curiosity
        alike) or the story's; a curiosity goal in which the story moved on (the rival's POKé BALL picked up plays the
        rival's scene) is the story's, as the graders count it (`gates/rate_step5.py` intent_mix)."""
        if frames <= 0 or not self.memory.decided_with_party:
            return
        if goal.kind == "save":
            # (R1, build spec T4) a save is the player's bookkeeping, neither an errand nor the story's: counted apart
            self.memory.spent["save"] = self.memory.spent.get("save", 0) + frames
            return
        errand = goal.kind in ERRAND_KINDS and not (story_moved and goal.kind in CURIOSITY_KINDS)
        self.memory.spent["errand" if errand else "story"] += frames
        if errand and goal.kind in CURIOSITY_KINDS:
            self.memory.spent["curious"] = self.memory.spent.get("curious", 0) + frames

    # ------------------------------------------------------------------ curiosity (build step 5.2)
    def left_before(self, world) -> bool:
        """(build step 5.2, the review's finding 6) Has the player LEFT the map it stands on at least once (a map change
        from it, the AI's or a scene's, in its world memory)? Then it is a place it knows."""
        return any(change.source == world.current for change in getattr(world, "transitions", ()) or ())

    def curious_ok(self) -> bool:
        """(build step 5.2, the review's finding 2: CH1M ran six curiosity goals in a row once its quota was short) May the
        next goal be one of CURIOSITY? Not under the beeline control, and not after `CURIOUS_ROW_MAX` in a row: the story
        or a need comes between."""
        return not self.errands_off and self.memory.curious_row < CURIOUS_ROW_MAX

    def boredom(self, frame: int) -> tuple[float, int]:
        """(build step 5.2) How BORED of the story alone a person is at `frame`, 0 to 1, and the frames since its last
        curiosity that came to something (the clock starts at the session's first decision): `Errands.bored_frames` of
        them make it 1. Never a share of frames: the graders measure those."""
        since = max(0, frame - (self.memory.curious_since if self.memory.curious_since is not None else frame))
        return min(1.0, since / max(1, self.state.errands.bored_frames)), since

    def curious_odds(self, base: float, frame: int) -> tuple[float, str]:
        """(build step 5.2, the step-5.1 review's finding 2: "when the time quota is short, the dice are skipped") The odds
        of one curiosity draw: the personality's own `base`, raised SMOOTHLY by boredom toward `CURIOUS_ODDS_CAP` (never
        lowered, never certain), and why. 5.1's balance passed the draw without the dice when a share of the session's
        frames fell under a quota set just above the graders' floor: the AI aimed at the graders' own quantity."""
        bored, since = self.boredom(frame)
        top = max(base, CURIOUS_ODDS_CAP)
        odds = base + (top - base) * bored
        if odds <= base + 1e-9:
            return base, f"the {self.state.active}'s {base}"
        return odds, (f"the {self.state.active}'s {base}, raised to {odds:.2f}: {since} frames since its last curiosity "
                      f"that came to something")

    def blocked_on(self, milestone_id: str | None, key: str | None) -> dict:
        """(build step 5.2) The places curiosity found BLOCKED on map `key` in this milestone: {tile: why}."""
        return self.memory.blocked.setdefault(milestone_id or "", {}).setdefault(key or "", {})

    def left_to_see(self, look: Observation, world, milestone_id: str | None) -> str | None:
        """(build step 5.2, the step-5.1 review's finding 1: "the 'some more' look-round never checks that anything is left
        to see": CH2M looked round PETALBURG twice, 8,400 frames, tiles 8025 -> 8026 -> 8026) Why there is NOTHING left to
        see here that it can walk to, or None: a frontier tile (seen, walkable, beside unseen ones) it can reach over
        tiles it KNOWS with nobody standing in the way and no blocked place on the way (`world.promise` counts the
        frontier, the exits not used and the roads; only the frontier is looked round), and the map not EXHAUSTED by an
        earlier look round that brought nothing in this milestone."""
        here = world.here()
        player = look.player
        if here is None or player is None or player.x is None:
            return "it does not know where it stands"
        why = self.memory.exhausted.get(f"{world.current}|{milestone_id}")
        if why is not None:
            return why
        if world.promise(world.current) <= 0:
            return "it has seen all of this place"
        blocked = set(self.blocked_on(milestone_id, world.current))
        blocked |= _scene_corners(self.blocked_on(milestone_id, world.current))  # (the verifier's round)
        frontier = set(here.frontier()) - blocked
        if not frontier:
            return "nothing left to see here but the places blocked to it"
        reach = _known_reach(here, (player.x, player.y), frozenset(set(here.people_now) | blocked))
        if not reach & frontier:
            return "nothing left to see here that it can walk to"
        return None

    def after_goal(self, goal: Goal, made: dict, frame: int, milestone_id: str | None, story_moved: bool = False) -> str | None:
        """(build step 5.2) After a goal: the curiosity goals IN A ROW (a story or need goal ends the row; a curiosity goal
        the story moved on in, the rival's POKé BALL, is the story's), the BOREDOM clock (only a PRODUCTIVE curiosity goal,
        `goal_yield`, resets it), and what an UNPRODUCTIVE one marks so it is not tried again: a look round EXHAUSTS its
        map for the milestone, a detour that did not get there BLOCKS its place. What it brought is told (`say`); returns
        what was marked. (R1 + R2 follow-up, spec D6: the verification's V2-6) A SAVE neither ends nor joins a row: it is
        bookkeeping, "neither an errand nor the story's step" (spec T4), so curiosity, save, curiosity is one row."""
        if goal.kind == "save":
            # (D6) transparent: a reset by bookkeeping would let C C save C C through CURIOUS_ROW_MAX
            return None
        if goal.kind not in CURIOSITY_KINDS or story_moved:
            self.memory.curious_row = 0
            return None
        self.memory.curious_row += 1
        brought = ", ".join([f"{key} {made[key]}" for key in ("tiles", "maps", "items", "caught", "species", "pages")
                             if made.get(key)] + (["a talk"] if made.get("talked") else [])
                            + (["a talk that told it nothing new"] if made.get("talks") and not made.get("talked") else [])
                            ) or "nothing new"
        if made.get("productive"):
            self.memory.curious_since = frame
            self._say(f"[AI-GOALS] its {goal.kind} brought {brought}")
            return None
        self.memory.idle["goals"] += 1
        self.memory.idle["frames"] += int(made.get("frames") or 0)
        marked = None
        if goal.kind == "explore" and goal.via is not None:
            why = f"a look round there brought nothing new (f{frame})"
            self.memory.exhausted[f"{goal.via}|{milestone_id}"] = why
            marked = f"{goal.via} is exhausted for this milestone: {why}"
        place = made.get("place")
        if goal.kind == "detour" and place and not made.get("reached"):
            tile = (int(place[1]), int(place[2]))
            self.blocked_on(milestone_id, place[0])[tile] = f"a detour did not get there (f{frame})"
            marked = f"the place at {tile} on {place[0]} is blocked for curiosity: the detour did not get there"
        self._say(f"[AI-GOALS] its {goal.kind} brought {brought}: NOT productive{'; ' + marked if marked else ''}")
        return marked

    def hurt(self, look: Observation) -> bool:
        """(build step 5.1) The party is HURT as this personality sees it: a Pokemon fainted, the strongest under a third
        (`needs_rest`), or the party under its `heal_below` share of HP."""
        mons = [m for m in look.party or () if not m.is_egg]
        if not mons:
            return False
        share = party_share(look)
        return (any(m.hp <= 0 for m in mons) or needs_rest(look.party) is not None
                or (share is not None and share < self.state.errands.heal_below))

    @staticmethod
    def been_to(world, place: str | None) -> bool:
        """Has the AI stood on map `place` (its own world memory)?"""
        return (world is not None and place is not None
                and any(memory.const == place and memory.visits for memory in world.maps.values()))

    def step_known(self, step: Step, heard: set[str], world=None) -> bool:
        """(build step 5.1, review #3: one word heard for a milestone unlocked EVERY step's map) May the AI head for this
        STEP's map? Only once it has READ the step's OWN words (`Step.told`, whole words); a step with no words names
        nothing it was told, so only a place it has BEEN to is headed for. (Step 5 asked the MILESTONE's words for every
        step, and its `ask` step went to its map with no check at all.)"""
        if self.hints_off:
            return False
        if step.told:
            return heard_words(heard, step.told) or self.knows_gym(step, world)
        return self.been_to(world, step.map)

    def knows_gym(self, step: Step, world) -> bool:
        """(chapter 7 NS4, 2026-11-06) May the AI head for this step's map without its words? Yes when the words it waits
        for NAME A GYM LEADER whom the AI knows to hold the step's map (`knowledge/atlas.py` gym_leaders: a seasoned
        player knows each town's leader, USER RULING 40) AND it has stood inside that gym itself (its own world memory):
        a person who has been in DEWFORD's gym knows it is BRAWLY's. WHY (probe7 C1, ledger #101): after STEVEN, BRAWLY's
        step waited for the words 'BRAWLY' (the gym sign's) and made 36 "where to? nobody has said yet" goals over
        502,847 frames, although it had been inside DEWFORD_TOWN_GYM. Being inside is asked so that a chapter whose
        leader's words come first (ROXANNE's sign, read before her gym is entered) is as it was."""
        leader = gym_leaders().get((step.told or "").strip().upper())
        return leader is not None and leader == step.map and self.been_to(world, step.map)

    # ------------------------------------------------------------------ the landmarks a person notices
    def notice(self, look: Observation) -> None:
        """A hands watcher: a door that LOOKS like a POKéMON CENTER's or a MART's, seen on screen, is remembered; so is
        someone it recognises, where they stood; and every page READ on the overworld, when (the condition and the
        normalising are `world/memory.py` `_news`'s, so these pages are the world memory's `heard`)."""
        screen = look.screen
        if screen.waits_for_button and screen.text and not screen.in_battle and screen.game_state == "OVERWORLD":
            page = " ".join((page_text(screen.text) or "").split())
            if page:
                self.memory.pages[page] = look.frame
        battle = look.battle
        if battle is not None and battle.kind == "trainer" and battle.foe and self.memory.last_map is not None:
            # (build step 5.1, review #4) how strong a trainer here is: SEEN on its Pokemon's bar in the battle
            top = max(mon.level for mon in battle.foe)
            if top > self.memory.seen_levels.get(self.memory.last_map, 0):
                self.memory.seen_levels[self.memory.last_map] = top
        if look.view is None or look.player is None or look.player.settling:
            return
        if look.player.map_const:
            self.memory.last_map = look.player.map_const
        key = f"{look.player.map_group}:{look.player.map_number}"
        if (self.memory.hearing and screen.waits_for_button and screen.text and not screen.in_battle
                and screen.game_state == "OVERWORLD"):
            # (build step 5.2, the verifier's round) who SPOKE in its own service talk or chat: the person straight in front
            # of the player while words are on screen (the nurse and the clerk across their counter, two tiles ahead)
            ahead = FACING_STEP.get(look.player.facing or "")
            for seen in look.view.objects:
                if (ahead is not None and seen.source == "object" and seen.kind == "npc"
                        and (seen.dx, seen.dy) in [(ahead[0] * n, ahead[1] * n) for n in range(1, SPOKE_REACH + 1)]):
                    self.memory.spoke.add(f"{key}|{seen.local_id}")
        center = self.story.looks.get("pokemon_center_door")
        mart = self.story.looks.get("mart_door")
        gym = self.story.looks.get("gym_door")
        for row in look.view.rows:
            for tile in row:
                # a door seen ACROSS a map's edge belongs to the next map (its coordinates here are past this map's): it is
                # remembered when the AI stands on that map and sees it again; a tile in the dark (round 7, N6-1) is unseen
                if tile is None or not tile.door or tile.x < 0 or tile.y < 0:
                    continue
                if center is not None and tile.metatile in center.metatile:
                    self.memory.landmarks.setdefault((key, (tile.x, tile.y)), "pokemon_center")
                elif mart is not None and tile.metatile in mart.metatile:
                    self.memory.landmarks.setdefault((key, (tile.x, tile.y)), "mart")
                elif gym is not None and tile.metatile in gym.metatile:
                    # (build step 5.1, the verifier's second round) a GYM's door, by its look (`GYM_SUFFIX`)
                    self.memory.landmarks.setdefault((key, (tile.x, tile.y)), "gym")
        for seen in look.view.objects:
            if seen.source != "object" or seen.x < 0 or seen.y < 0:
                continue
            for name, known in self.story.looks.items():
                if seen.graphics_id in known.gfx:
                    self.memory.sightings[(name, key)] = (seen.x, seen.y, look.frame)

    # ------------------------------------------------------------------ choosing
    def next_goal(self, look: Observation, world, milestone: Milestone, index: int) -> Goal:
        """The next goal (module docstring's order); never None."""
        self.memory.decisions += 1
        if self.memory.known_before is None:
            # (build step 5.1) this session's first decision: what the world memory knew already is no new place
            self.memory.known_before = {key for key, memory in world.maps.items() if memory.visits}
        if self.memory.curious_since is None:
            # (build step 5.2) the boredom clock starts at this session's first decision
            self.memory.curious_since = look.frame
        here = world.here()
        here_const = here.const if here is not None else None
        errands = self.state.errands
        has_party = bool([m for m in look.party or () if not m.is_egg])
        self.memory.decided_with_party = has_party
        step = self.story_step(look, world, milestone)
        levels, levels_from = self.fight_levels(milestone)
        fight_next = bool(levels) and has_party and step is not None and step.do in ("go", "talk")
        share = party_share(look)
        fainted = any(m.hp <= 0 for m in look.party or () if not m.is_egg)
        # (boss preparation BP-1) the readiness verdict for the next gym leader: run when the party or the boss changed,
        # logged; for a leader in `ACT_ON` it may make (or re-judge) the plan this run commits to. (Round 2) decided
        # BEFORE the danger below, which reads the plan's trainee; it reads nothing the danger lines set
        bp_plan = self.boss_prep(look, index) if has_party else None
        # (round 4, the round-3 verifier's V3-M1; the lead's design E1) the plan's BUDGET (and grass to raise on) is checked
        # BEFORE any rest is decided for it: a plan over its budget is spent here, so it never heals for the plan (round 3
        # checked it inside the raise goal, which the heal step below returned before: with a heal loop, never). FAULT
        # `budget_after_rest`: round 3's order
        if bp_plan is not None and not self.bp_faults.budget_after_rest:
            self._spend_if_over(look, world, bp_plan)
        # (round 2, the verifier's V-M1) THE TRAINEE'S FLOOR: an active plan's trainee fainted or under `TRAINEE_FLOOR`
        # (and, the builder's addition, its knock-out partner worn, `bossprep.partner_worn`) is a party that must rest. The
        # danger was keyed on the STRONGEST (`needs_rest`) and the party's share: a Wurmple at 1/18 left the party at 89 %,
        # the raise was chosen again, it ran from every battle and 12 sessions of +0 EXP spent the plan (6378, 6379).
        # Always None in chapters 1-5, where no plan is active
        trainee_low = self._trainee_low(look, bp_plan)
        worn = self._partner_worn(look, bp_plan, world)
        if self.bp_faults.trainee_floor_off:
            trainee_low = worn = None
        # the party in real danger (a Pokemon fainted, the strongest under a third: `needs_rest`): healing is then the only
        # sensible errand, so a heal put aside after failing (`FAIL_LIMIT`) is tried again at once (the development sweep
        # step5dev7, seed 3: two walks home ran out, the heal was put aside, and the AI trained, then walked to the rival, at
        # 2/26 HP, and whited out)
        must_rest = has_party and (fainted or needs_rest(look.party) is not None or trainee_low is not None
                                   or worn is not None)
        hurt = has_party and share is not None and (must_rest or share < errands.heal_below)
        # (chapter 7 NS3, 2026-11-06) THE STORY'S OWN PERSON, HERE AND IN VIEW: the story's next step talks to (or uses)
        # someone it recognises, on that step's map, on the screen now, and no fight is next. Then a walk OFF this map for
        # an errand (a heal while not in danger, a shop) waits: a person carrying a letter for STEVEN who stands in his
        # room hands it over first (probe7 C2 left the room on a shop errand). Curiosity here keeps its place
        story_here = (step is not None and step.do in ("talk", "use") and bool(step.look) and here_const == step.map
                      and not fight_next and self.looks_like(look, step.look) is not None)
        # 1. HEAL
        if has_party and share is not None and not (story_here and not must_rest):
            # ready for the fight: trained (`prep` ready), or, under the no-training FAULT, at once (the fault removes the
            # TRAINING only; healing before the fight stays, so the fault arm measures training alone: the step-5
            # verifier, 2026-10-14, found it removed both)
            ready = self.train_off or bool(self.prep(milestone).get("ready"))
            # (chapter 7 stops round 4, V3-1, 2026-11-06) TRAINED and READY FOR THE FIGHT are two things. A party that
            # cannot train where it stands (it has seen grass, but no known way leads to any: `grass_target` "out of
            # reach", the island before a way back is known) is as ready as it will get, so it tops up before the fight
            # all the same; `prep["ready"]` (trained, or training put aside) is NOT set by this. MEASURED (probe #104):
            # with the heal tied to `prep["ready"]` alone, C3 talked to BRAWLY at 77% of its HP and C2 at 89.9%
            cannot_train = (fight_next and share < HEAL_BEFORE_FIGHT and not ready
                            and grass_target(world, milestone.maps)[0] == "out of reach")
            before_fight = fight_next and share < HEAL_BEFORE_FIGHT and (ready or cannot_train)
            if hurt or before_fight:
                # (chapter 6 stops round 5, the round-4 verifier's VR4-2) V3-1's TOP-UP where it cannot train (the party
                # neither in danger nor under its heal line) goes only to a centre a known way leads to, as the shop does
                # (NS4): a party at 75% in DEWFORD's gym knowing only RUSTBORO's centre, no way back known, headed there
                # twice per cooldown (the verifier's VT-R1, VT-R2). A heal for the party's own state (under its heal line,
                # or in danger) and the TRAINED party's heal before the fight (step 5's, chapters 1-5: ErrandTests
                # test_the_no_training_fault_still_heals_before_the_fight, TunnelGruntTests test_c8, unlinked worlds, pin
                # it; this round's first version also held it to a known way, and both failed) keep every centre it knows
                topup = cannot_train and not hurt
                # (chapter 6 stops round 6, the round-5 verifier's V5-1) the LOOK for a town's own centre is decided on
                # every centre it knows (`known`), as before round 5; only the walk to a centre is held to a known way
                # (`where`). Round 5 decided both on `where`, so a top-up in a town whose centre it had not seen, knowing
                # only an unreachable one, looked for none and walked to BRAWLY at 75% (the verifier's VT5-1)
                known = self.heal_place(world)
                where = self.heal_place(world, reachable=True) if topup else known
                why = ("a Pokemon has fainted" if fainted else f"the party is at {share:.0%} of its HP"
                       + (f" (under {errands.heal_below:.0%})" if share < errands.heal_below else "")
                       + ("; a known fight is next" if before_fight else "")
                       + (" (it cannot train here: no known way leads to grass)" if before_fight and cannot_train
                          else ""))
                if not fainted and (trainee_low is not None or worn is not None):
                    # (round 2) the raise's own reason to rest, said: the trainee under its floor, or its partner worn
                    why = (f"{self._raise_name(look, bp_plan)} is {trainee_low}" if trainee_low is not None else worn)
                    why += f" (the party at {share:.0%} of its HP)"
                potion = self._potion_goal(look, world, milestone, bp_plan, trainee_low, worn, fainted, share)
                if potion is not None:
                    return potion
                town_key, town = ((world.current, here_const) if here_const and OUTDOOR.match(here_const)
                                  and not here_const.startswith("ROUTE") else (None, None))
                if town is None and topup:
                    # (chapter 6 stops round 7, the round-6 verifier's VR6-4) a TOP-UP that starts INSIDE a building of a
                    # town (its gym) looks for that town's centre as it would outdoors: the town its door leads to
                    # (`_building_town`). Before, the look needed an outdoor town map, so in DEWFORD's gym, knowing only
                    # an unreachable centre, it neither looked nor healed. Only the top-up: a heal for the party's own
                    # state from a building keeps the nearest centre it knows (Round5HealTests r2, chapters 1-5)
                    town_key, town = self._building_town(world)
                if (known is not None and town is not None and self._place_key(world, known) not in (None, town_key)
                        and town_key not in self.memory.center_looked
                        # (the graded sweep on 701-720, seed 706: a look round of PETALBURG did not pass its centre, and
                        # the AI took the town for one with none) only a town SEEN ALL OF (nothing left to see there) and
                        # looked round has no centre to look for
                        and not (town_key in self.memory.explored and world.promise(town_key) <= 0)):
                    # (build step 5.1, the verifier's second round: CH2T, hurt on arriving in PETALBURG CITY, walked back
                    # to OLDALE's centre, the one it knew) in a TOWN whose own centre it has not seen, a person looks for
                    # it here first (a town has one), once; then the nearest it knows
                    self.memory.center_looked.add(town_key)
                    back = (f"before walking back to {where[3]}" if where is not None else
                            f"first: no known way leads back to {known[3]}")
                    here_said = "here" if town_key == world.current else f"in {town}, out of this building,"
                    return Goal("find_center", f"{why}: it has not seen {town}'s POKéMON CENTER yet; a town has one, so it "
                                               f"looks {here_said} {back}", milestone.id, map=town,
                                via=town_key, key=f"find_center:{town_key}")
                allowed = self._allowed(f"heal:{where[0]}") if where is not None else False
                retries = self.memory.danger_again.get(f"heal:{where[0]}", 0) if where is not None else 0
                if where is not None and (allowed or (must_rest and retries < DANGER_RETRIES)):
                    if not allowed:
                        # (the round's development sweep) in danger, again: at most DANGER_RETRIES times in a row
                        self.memory.danger_again[f"heal:{where[0]}"] = retries + 1
                    again = "" if allowed else (f" (put aside after failing, but the party is in danger: again, "
                                                f"{retries + 1} of at most {DANGER_RETRIES})")
                    return Goal("heal", f"{why}: {where[3]}{again}", milestone.id, map=where[0], via=where[1], tile=where[2],
                                key=f"heal:{where[0]}")
                if where is None and must_rest and self._allowed("find_center"):
                    # (build step 5.1: home is no longer known by a flag, and the development sweep's Trainers walked on at
                    # 1-5 HP knowing nowhere to heal, three whiteouts in nine) a person in danger who knows no place to
                    # heal LOOKS for one: a POKéMON CENTER's red roof, out of the tall grass
                    return Goal("find_center", f"{why}: it knows no place to heal yet: looking for a POKéMON CENTER (its "
                                               f"red roof), out of the tall grass", milestone.id, key="find_center")
        # 1b. SAVE (R1, USER RULING 51; build spec 2026-10-29 D2, D3): a save DUE after a heal at a POKéMON CENTER or a big
        # story moment, once it MAY save (`brain/saving.py`: the play time read, 3 game minutes since its last save, frames
        # left, a free screen); a person heals at the centre first, then saves there (never while hurt: the due waits). Only
        # with a memory file (D14)
        saving = None if hurt else self._save_goal(look, here_const, milestone)
        if saving is not None:
            return saving
        # 2. SHOP: by what the mart's LIST showed (build step 5.1, review #4: step 5 shopped once FLAG_ADVENTURE_STARTED was
        # set, a flag no player sees): a mart whose list had no POKé BALLS is tried again only once the story moved on
        balls = look.bag.ball_total if look.bag is not None else 0
        money = look.progress.money if look.progress is not None else 0
        if (has_party and balls < errands.balls_low and money >= BALL_PRICE * min(errands.balls_buy, 5)
                and not story_here):
            where = self._mart_place(world, index)
            if where is not None and self._allowed(f"shop:{where[0]}"):
                return Goal("shop", f"{balls} POKé BALLS left (fewer than {errands.balls_low}) and {money} money: "
                                    f"{where[3]}", milestone.id, map=where[0], via=where[1], tile=where[2],
                            key=f"shop:{where[0]}")
        # (build step 5.2, the step-5.1 review's finding 2: CH1M ran six curiosity goals in a row) at most CURIOUS_ROW_MAX
        # curiosity goals in a row: then the story or a need first (every curiosity choice below asks; a draw it holds back
        # is made on a later decision)
        curious = self.curious_ok()
        # 3. ITEM: a ball on screen, or one it saw earlier on this map (build step 5.1: before the party too, so the rival's
        # POKé BALL on the floor of the rival's room is found by curiosity, review #3, not by a scripted step; and before
        # training: a training roam STOPS for a ball in view, so with training first each session ended at once); (build
        # step 5.2) under the row cap like all curiosity, and under the beeline control too, as in 5.1 (the rival's POKé BALL
        # is how its chapter 1 goes on: the development sweep step52dev2's beeline, with no item balls, stuck in 12 of 12)
        items = self.memory.curious_row < CURIOUS_ROW_MAX
        ball = self._item_ball(look, world) if items else None
        if ball is not None:
            return Goal("pick_up", f"an item ball on the ground at {(ball.x, ball.y)}: a person picks it up", milestone.id,
                        target=ball, key=f"item:{world.current}|{ball.x},{ball.y}")
        remembered = self._remembered_ball(look, world) if items else None
        if remembered is not None and self._allowed(f"item:{world.current}|{remembered[0]},{remembered[1]}"):
            return Goal("pick_up", f"an item ball it saw on {here_const} at {remembered}: back over to it", milestone.id,
                        tile=remembered, key=f"item:{world.current}|{remembered[0]},{remembered[1]}")
        # 4. LOOK AROUND a new outdoor place (build step 5.1, review #1: step 5 looked around only when it did not know where
        # to go, so once a route was known it walked straight there): one seeded draw a map, by the personality's taste
        # (Story least), never in danger (a person heals first); before training and chatting (measured 2026-10-14, the
        # development sweeps step51dev2 and dev3: drawn after them, and only when not hurt, most draws waited for a decision
        # that never came on that map, and the errand time barely differed from the beeline control's)
        # (and not where the story's own next thing is, told and here: measured 2026-10-14, the step-5.1 development sweep:
        # it looked round ROUTE 101 while PROF. BIRCH cried "Help! In my BAG!", and he cried "Don't leave me like this!";
        # the draw waits for a later decision there)
        # (build step 5.2, the step-5.1 review's finding 2) every curiosity draw below is a DICE throw at the personality's
        # own odds raised by boredom (`curious_odds`): 5.1's balance passed them WITHOUT the dice when a share of the
        # session's frames fell under a quota, the quantity the graders' floor measures
        if curious and self.may_look_around(look, world, step):
            self.memory.looked.add(world.current)
            draw = self.rng.random()
            odds, odds_why = self.curious_odds(errands.look_around, look.frame)
            if self.memory.passed_new >= LOOK_DEBT:
                # (build step 5.1's look-around debt, as ODDS since build step 5.2: raised to the cap, never certain)
                odds = max(odds, CURIOUS_ODDS_CAP)
                odds_why = (f"it has gone past {self.memory.passed_new} new places in a row without a look: the odds "
                            f"raised to {odds:.2f}")
            if draw < odds:
                self.memory.passed_new = 0
                self.memory.explored.add(world.current)
                return Goal("explore", f"a new place, {here_const}: a person looks around it (draw {draw:.2f} < "
                                       f"{odds_why}) before going on", milestone.id, steps=errands.look_frames,
                            key=f"explore:{world.current}", via=world.current)
            self.memory.passed_new += 1
            self._say(f"[AI-GOALS] a new place, {here_const}: it goes on without looking round (draw {draw:.2f} >= "
                      f"{odds:.2f}, {odds_why}; {self.memory.passed_new} in a row)")
        # 5a. (boss preparation BP-1, spec section 3.1) RAISE the plan's trainee for the next leader: in the place of step 5,
        # never while hurt, NOT tied to `fight_next` (the plan is made where the grass is, before the trip to the gym);
        # and on the leader's own gym map, with the raise done, the trainee is put back in the lead first
        if bp_plan is not None and not hurt:
            raised = self._raise_goal(look, world, bp_plan)
            if raised is not None:
                return raised
            relead = self._lead_goal(look, here_const, bp_plan)
            if relead is not None:
                return relead
        # (round 2, V-m5 E1 and E3) at step 5a's place on EVERY decision, whatever the plan: a plan that ended (spent before
        # its boss, or its boss beaten) gives the lead back as it was before the plan, after a re-judge; nothing to do (no
        # record, chapters 1-5) is None at once
        settle = self._settle_goal(look, index) if has_party and not hurt else None
        if settle is not None:
            return settle
        # 5. TRAIN before a fight it KNOWS of (never while hurt: a person heals first, and a roam begun hurt stops at its first
        # battle, `training_rest`, burning a session of `TRAIN_SESSIONS` for nothing: step5dev7, seed 3, six in a row).
        # (BP-1, m11: ONE budget) never while a raise plan is active for this very fight
        if fight_next and not self.train_off and not hurt and not self.raising_for(milestone.id):
            prep = self.prep(milestone)
            target = self.training_target(levels)
            level = strongest_level(look)
            short = level < target or prep["steps"] < errands.train_min_steps
            # (chapter 7 NS4, 2026-11-06) never toward grass no known way leads to (`grass_target`: no link, no ride)
            out_of_reach = short and grass_target(world, milestone.maps)[0] == "out of reach"
            if short and prep["sessions"] < TRAIN_SESSIONS and self._allowed("train") and not out_of_reach:
                why = (f"the next fight ({milestone.title}) has levels {list(levels)} ({levels_from}): its strongest "
                       f"Pokemon is L{level}, the {self.state.active}'s target L{target}; {prep['steps']} of at least "
                       f"{errands.train_min_steps} training steps roamed in {prep['sessions']} of at most "
                       f"{TRAIN_SESSIONS} sessions")
                return Goal("train", why, milestone.id, steps=errands.train_session, key="train")
            if not prep["ready"] and not (out_of_reach and prep["sessions"] < TRAIN_SESSIONS):
                prep["ready"] = True
                prep["why_ready"] = ("trained" if not short else f"{TRAIN_SESSIONS} sessions roamed: no endless grind"
                                     if prep["sessions"] >= TRAIN_SESSIONS else "training put aside for a while")
                # (build step 5.1, the verifier's second round: "which personality judged the run 'trained' is not
                # logged") whose rule said so, and its minimum: the graders take the run's bound from it
                prep["judged_by"] = self.state.active
                prep["min_steps"] = errands.train_min_steps
        # 6. CATCH: balls in hand, grass not walked on this map
        if (has_party and balls > 0 and here is not None and here.grass() and world.current not in self.memory.catch_maps
                and not fight_next and curious):
            self.memory.catch_maps.add(world.current)
            fresh = [xy for xy in here.grass() if not here.visits.get(xy)]
            draw = self.rng.random()
            odds, odds_why = self.curious_odds(errands.catch_seek, look.frame)
            # (the round's development sweep step51wdev1: a Story player went through chapter 2 with its first five POKé
            # BALLS and caught nothing) a POKéDEX that holds only its first Pokemon and balls just in hand: a person tries
            # them, whatever its taste (PROF. BIRCH's "fill the POKéDEX", the rival's "catch POKéMON with these")
            first = look.progress is not None and look.progress.dex_owned <= 1
            if fresh and (draw < odds or first) and self._allowed(f"catch:{world.current}"):
                why = (f"draw {draw:.2f} < {odds_why}" if draw < odds
                       else f"draw {draw:.2f}, but its POKéDEX holds only its first Pokemon and it has its first POKé "
                            f"BALLS: it tries them")
                return Goal("catch", f"{len(fresh)} grass tiles not walked on {here_const} and {balls} POKé BALLS ({why}): "
                                     f"looking for POKéMON it has not caught", milestone.id, steps=errands.catch_roam_steps,
                            key=f"catch:{world.current}")
        # 7. CHAT with someone near (never the person the story's own step names: the round's development sweep chose DAD as a
        # "chat", seeds 37 and 39, a story-owned goal under an errand's name; the story's goal talks to him)
        own = self.story.looks.get(step.look) if step is not None and step.look else None
        chat = self._chat_person(look, world, look.frame, own.gfx if own is not None else ()) if curious else None
        if chat is not None:
            person, why = chat
            return Goal("chat", f"someone stands near at {(person.x, person.y)}: a person says hello now and then{why}",
                        milestone.id, target=person, key=f"chat:{world.current}|{person.local_id}")
        # 7b. (build step 5.1, the verifier's second round; build step 5.2: by BOREDOM's dice, not a quota, and only where
        # something is left that it can walk to, the step-5.1 review's finding 1) it looks round where it stands some more
        # (an outdoor map, not where the story's own next thing is told and here; `AGAIN_MAX` a map and milestone)
        again = f"{world.current}|{milestone.id}"
        if (curious and here is not None and OUTDOOR.match(here_const or "") and not must_rest and step is not None
                and step.do != "intro" and not self._story_here(step, world)
                and self.memory.again.get(again, 0) < AGAIN_MAX):
            bored, since = self.boredom(look.frame)
            odds = CURIOUS_ODDS_CAP * bored
            nothing = self.left_to_see(look, world, milestone.id) if odds > 0 else None
            if odds > 0 and nothing is None:
                draw = self.rng.random()
                if draw < odds:
                    self.memory.again[again] = self.memory.again.get(again, 0) + 1
                    self.memory.explored.add(world.current)
                    return Goal("explore", f"{here_const} some more (draw {draw:.2f} < {odds:.2f}: {since} frames since its "
                                           f"last curiosity that came to something): a break from the story, looking round "
                                           f"where something is left to see ({self.memory.again[again]} of at most "
                                           f"{AGAIN_MAX} here)", milestone.id, steps=errands.look_frames,
                                key=f"explore:{world.current}:again", via=world.current)
        # 8. STORY (and now and then a DETOUR off the way while travelling)
        goal = self._story_goal(look, world, milestone, step)
        if (goal.key.startswith(LOST_KEYS) and self.memory.lost_end is not None
                and self.memory.lost_end == (milestone.id, world.stamp())):
            # (build step 5.2, the verifier's round: the graded NOHINTS runs, told nothing they would use, pressed for
            # 31,676-62,012 frames with nothing new, goal after goal, until the story's 120,000-frame patience) OUT OF
            # IDEAS: its last walk with no lead found nothing left to see that it could get to on any map it knows, nothing
            # new has been seen since, and nothing it has heard says where to go: a person stuck like that puts the game
            # down rather than walk the same streets for half an hour
            return Goal("give_up", f"{milestone.title}: {OUT_OF_IDEAS}: its last walk with no lead found nothing left to "
                                   f"see that it could get to on any of the "
                                   f"{sum(1 for memory in world.maps.values() if memory.visits)} maps it knows, nothing "
                                   f"new since, and no hint it goes by names where to go", milestone.id, key="give_up")
        # (R1, finding m2) RIGHT BEFORE A GYM LEADER: the story goal is the talk to a leader the game names, on that step's
        # gym map, and no save was made in this approach to the gym: a save goal in its place (`brain/saving.py`)
        leader = self._leader_save(look, world, milestone, step, goal)
        if leader is not None:
            return leader
        if (goal.kind == "go" and goal.map is not None and curious and here is not None
                and OUTDOOR.match(here_const or "") and f"{world.current}|{milestone.id}" not in self.memory.detoured
                and goal.key.startswith("go:") and not must_rest):
            self.memory.detoured.add(f"{world.current}|{milestone.id}")
            draw = self.rng.random()
            odds, odds_why = self.curious_odds(errands.detour, look.frame)
            if draw < odds:
                return Goal("detour", f"on the way to {goal.map}: a look at something off the way on {here_const} (draw "
                                      f"{draw:.2f} < {odds_why})", milestone.id, steps=errands.detour_frames,
                            key=f"detour:{world.current}", via=world.current)
            self._say(f"[AI-GOALS] on the way to {goal.map}: no detour on {here_const} this time (draw {draw:.2f} >= "
                      f"{odds:.2f}, {odds_why})")
        return goal

    def _run_frames_left(self) -> int:
        """(R1) The run's frames left, as the play brain counts them (`frames_left`); unbounded when it is not told."""
        return self.frames_left() if self.frames_left is not None else 10 ** 9

    def _save_goal(self, look: Observation, here_const: str | None, milestone: Milestone) -> Goal | None:
        """(R1) Block 1b: a `save` goal for a centre's or a big moment's due, when the policy may save now (None without a
        memory file, `saving`); a save that failed `FAIL_LIMIT` times waits `COOLDOWN_DECISIONS` like any goal."""
        if self.saving is None:
            return None
        choice = self.saving.next_save(look, here_const, self._run_frames_left())
        if choice is None or not self._allowed(choice.key):
            return None
        return Goal("save", choice.reason, milestone.id, key=choice.key)

    def _leader_save(self, look: Observation, world, milestone: Milestone, step: Step | None, goal: Goal) -> Goal | None:
        """(R1) Block 8: a `save` goal in the story goal's place, right before the talk to a gym leader (`before_leader`)."""
        if self.saving is None:
            return None
        choice = self.saving.before_leader(look, world, milestone, step, goal, self._run_frames_left())
        if choice is None or not self._allowed(choice.key):
            return None
        return Goal("save", choice.reason, milestone.id, key=choice.key)

    def story_step(self, look: Observation, world, milestone: Milestone) -> Step | None:
        """The milestone's step to do now: the first whose work is not visibly done (`ask`: its words heard; `go`: the
        player on its map, or a later step's map is this one); None when every step is done (the scene's turn)."""
        here = world.here()
        const = here.const if here is not None else None
        steps = milestone.steps
        for number, step in enumerate(steps):
            later_maps = {s.map for s in steps[number + 1:] if s.map is not None}
            if step.do == "intro":
                return step
            if step.do == "ask":
                rounds = self.memory.asked_rounds.get(milestone.id, 0)
                if heard_words(world.heard, step.words) or self.hints_off or rounds >= ASK_ROUNDS:
                    continue
                return step
            if step.do == "go":
                if const == step.map or const in later_maps:
                    continue
                return step
            if step.do in ("use", "talk"):
                return step
            if step.do == "follow":
                return step
        return None

    def _story_goal(self, look: Observation, world, milestone: Milestone, step: Step | None) -> Goal:
        """The STORY goal (`_story_step_goal`), put aside like any other goal once it failed `FAIL_LIMIT` times in a row
        (build step 5.1, review #5: only `seek` was, so a `go`, `find`, `use` or `talk` that kept failing was chosen again
        and again until `STORY_PATIENCE`, the "next decision chooses another" of this module's docstring untrue for the
        story): meanwhile it looks around, and says which goal waits and until when (never without a goal). (Build step
        5.1, the verifier's round) the aside ends after `COOLDOWN_DECISIONS` decisions OR `STORY_ASIDE_FRAMES` frames,
        whichever comes first: a person goes back to the story after a breather, not after ten looks round."""
        goal = self._story_step_goal(look, world, milestone, step)
        if goal.kind == "intro" or self._allowed(goal.key):
            self.memory.aside_from.pop(goal.key, None)
            return goal
        began = self.memory.aside_from.setdefault(goal.key, look.frame)
        left = STORY_ASIDE_FRAMES - (look.frame - began)
        if left < ASIDE_LOOK_MIN:
            # (the round's development sweep: a look round begun 617 frames before the breather's end ran 6,444 frames)
            # too little of the breather is left for a look round: the story goal again now
            self.memory.cooldown.pop(goal.key, None)
            self.memory.aside_from.pop(goal.key, None)
            return replace(goal, reason=f"{goal.reason}; tried again after {look.frame - began} frames put aside (at most "
                                        f"{STORY_ASIDE_FRAMES})")
        until = self.memory.cooldown.get(goal.key, 0)
        return Goal("look_around", f"{milestone.title}: the {goal.kind} goal ({goal.key}) failed {FAIL_LIMIT} times in a "
                                   f"row: put aside until decision {until} (this is {self.memory.decisions}) or frame "
                                   f"{began + STORY_ASIDE_FRAMES}, whichever comes first; looking around meanwhile, for "
                                   f"the {min(LOOK_AROUND_FRAMES, left)} frames left of the breather",
                    milestone.id, steps=min(LOOK_AROUND_FRAMES, left), key=f"{ASIDE}{goal.key}")

    def _story_step_goal(self, look: Observation, world, milestone: Milestone, step: Step | None) -> Goal:
        here = world.here()
        const = here.const if here is not None else None
        if step is None:
            return Goal("look_around", f"{milestone.title}: every step of it done; looking around for what comes next",
                        milestone.id, key="look_around")
        if step.do == "intro":
            return Goal("intro", f"{milestone.title}: a New Game", milestone.id, key="intro")
        if step.do == "follow":
            return Goal("follow", f"{milestone.title}: it plays by itself; looking around meanwhile", milestone.id,
                        key=f"follow:{milestone.id}")
        if step.do == "go":
            if self.step_known(step, world.heard, world):
                return Goal("go", f"{milestone.title}: to {step.map} ({self._told(step, world)})", milestone.id,
                            map=step.map, key=f"go:{step.map}")
            why = (f"nobody has said yet (words {step.told!r} not heard)" if step.told
                   else "nothing the game said names it, and it has not been there")
            return Goal("go", f"{milestone.title}: where to? {why}: exploring", milestone.id, map=None,
                        key=f"go:?{milestone.id}", words=None if self.hints_off else step.told)
        if step.do == "ask":
            if const != step.map:
                # (build step 5.1, review #3: step 5 went to ask there with no check at all) only a place it has BEEN to:
                # a person asks where they know people (the rival's house, visited for the rival's milestone); (build step
                # 5.2, the step-5.1 review's finding 6: "it walks to the step's own house with 'nothing was said'") and only
                # once the step's OWN words were read (PROF. BIRCH's "Get MAY to teach you what it means to be a TRAINER.":
                # a person told to go and see the rival goes to the rival's house)
                told = self.step_known(step, world.heard, world)
                if told and self.been_to(world, step.map):
                    return Goal("go", f"{milestone.title}: to ask at {step.map} where to go ({self._told(step, world)})",
                                milestone.id, map=step.map, key=f"go:{step.map}")
                why = (f"it has not been to {step.map}" if told
                       else f"nobody has told it whom to see (words {step.told!r} not heard)" if step.told
                       else f"it has not been to {step.map}")
                return Goal("go", f"{milestone.title}: who would know where to go? {why}: exploring", milestone.id,
                            map=None, key=f"go:?{milestone.id}", words=None if self.hints_off else step.words)
            person = self._ask_person(look, world)
            if person is None:
                self.memory.asked_rounds[milestone.id] = self.memory.asked_rounds.get(milestone.id, 0) + 1
                for key in [k for k in self.memory.talked if k.startswith(f"{world.current}|")]:
                    self.memory.talked.discard(key)
                return Goal("look_around", f"{milestone.title}: nobody here left to ask (round "
                                           f"{self.memory.asked_rounds[milestone.id]} of {ASK_ROUNDS})", milestone.id,
                            key=f"ask:{milestone.id}")
            return Goal("talk", f"{milestone.title}: asking the people here ({step.words!r} not heard yet)", milestone.id,
                        target=person, key=f"ask:{world.current}|{person.local_id}")
        # use / talk: on its map, find what LOOKS like what it names
        if const != step.map and step.map is not None:
            known = self.step_known(step, world.heard, world)
            return Goal("go", f"{milestone.title}: to {step.map}" + (f" ({self._told(step, world)})" if known
                                                                      else " (by looking around: not told yet)"),
                        milestone.id, map=step.map if known else None, key=f"go:{step.map}" if known
                        else f"go:?{milestone.id}", words=None if known or self.hints_off else step.told)
        target = self.looks_like(look, step.look)
        if target is None:
            seen = self.memory.sightings.get((step.look, world.current))
            if seen is not None and self._allowed(f"seek:{step.look}"):
                return Goal("seek", f"{milestone.title}: {self.story.looks[step.look].what} was at {seen[:2]} when last seen "
                                    f"(f{seen[2]}): back there", milestone.id, look=step.look, tile=seen[:2],
                            key=f"seek:{step.look}")
            return Goal("find", f"{milestone.title}: looking for {self.story.looks[step.look].what} on {const}",
                        milestone.id, look=step.look, key=f"find:{step.look}")
        return Goal(step.do, f"{milestone.title}: {self.story.looks[step.look].what} at {(target.x, target.y)}",
                    milestone.id, target=target, look=step.look, key=f"{step.do}:{step.look}")

    def _told(self, step: Step, world) -> str:
        """Why the AI may head for this step's map, as a reason says it: the page it READ that says the step's own words
        (the most recent: never the milestone's stored line, the step-5 verifier's round 2), or a place it has been."""
        page = heard_page(world.heard, step.told, self.memory.pages) if step.told else None
        if page is None and step.told and self.knows_gym(step, world):
            # (chapter 7 NS4) the leader it waits to hear of is one it KNOWS: it has been inside their gym
            return f"it knows {step.told} holds {step.map} (a seasoned player's knowledge) and it has been inside it"
        return f"the game said: {quote(page, step.told)!r}" if page is not None else "a place it has been to; nothing was said"

    # ------------------------------------------------------------------ the fight ahead
    def fight_levels(self, milestone: Milestone) -> tuple[tuple[int, ...], str]:
        """(build step 5.1, review #4) The levels of the milestone's fight AS A PERSON KNOWS THEM, and how: a fight the game
        NAMES to the player (the rival, a gym leader: `Milestone.fight_named`; RULING 33 "train to the leader's level") by
        its levels; any other (a route's trainers, the woods' grunt, a gym's trainers) only by the levels SEEN in a
        trainer's battle on the milestone's maps (`seen_levels`); nothing seen: no levels (no training for it, and no heal
        before it)."""
        if not milestone.fight_levels:
            return (), ""
        if milestone.fight_named:
            return milestone.fight_levels, "a fight the game names"
        seen = [self.memory.seen_levels[name] for name in milestone.maps if name in self.memory.seen_levels]
        if seen:
            return (max(seen),), "the strongest SEEN in a trainer's battle here"
        return (), ""

    def training_target(self, levels: tuple[int, ...]) -> int:
        """The level a person trains to before a fight with `levels`: its STRONGEST Pokemon's level plus the personality's
        margin (Trainer +3, Catcher +2, Story +1: `Errands.train_margin`)."""
        return max(levels) + self.state.errands.train_margin

    # ------------------------------------------------------------------ what it sees
    def looks_like(self, look: Observation, name: str | None) -> SeenObject | None:
        if name is None or look.view is None:
            return None
        want = self.story.looks.get(name)
        if want is None:
            return None
        for seen in sorted(look.view.objects, key=lambda o: (abs(o.dx) + abs(o.dy), o.x, o.y)):
            if seen.source == "object" and seen.graphics_id in want.gfx:
                return seen
            if want.metatile and seen.kind == "sign":
                tile = look.view.tile(seen.dx, seen.dy)
                if tile is not None and tile.metatile in want.metatile:
                    return seen
        return None

    def item_ball_in_view(self, look: Observation, world) -> SeenObject | None:
        """An item ball on screen now, on this map, not tried yet (the travel goals stop for one: `GoalRunner.pursue`)."""
        return self._item_ball(look, world)

    def _item_ball(self, look: Observation, world) -> SeenObject | None:
        if look.view is None:
            return None
        balls = [o for o in look.view.objects if o.kind == "item_ball" and o.source == "object" and o.x >= 0 and o.y >= 0
                 and f"{world.current}|{o.x},{o.y}" not in self.memory.tried_items]
        return min(balls, key=lambda o: (abs(o.dx) + abs(o.dy), o.x, o.y)) if balls else None

    def _remembered_ball(self, look: Observation, world) -> tuple[int, int] | None:
        """(build step 5.1, review #1) An item ball it SAW earlier on this map (`MapMemory.items`), not tried yet and not on
        screen now: a person who noticed one walks back over to it. The nearest by the map's coordinates."""
        here = world.here()
        if here is None or not here.items or look.player is None or look.player.x is None:
            return None
        on_screen = {(o.x, o.y) for o in (look.view.objects if look.view else ()) if o.kind == "item_ball"}
        at = (look.player.x, look.player.y)
        left = [xy for xy in here.items if xy not in on_screen and xy[0] >= 0 and xy[1] >= 0
                and f"{world.current}|{xy[0]},{xy[1]}" not in self.memory.tried_items]
        return min(left, key=lambda xy: (abs(xy[0] - at[0]) + abs(xy[1] - at[1]), xy)) if left else None

    def _people(self, look: Observation) -> list[SeenObject]:
        return sorted((o for o in (look.view.objects if look.view else ()) if o.kind == "npc" and o.source == "object"),
                      key=lambda o: (abs(o.dx) + abs(o.dy), o.local_id))

    def _ask_person(self, look: Observation, world) -> SeenObject | None:
        for person in self._people(look):
            if f"{world.current}|{person.local_id}" not in self.memory.talked:
                return person
        return None

    def _chat_person(self, look: Observation, world, frame: int | None = None,
                     story_gfx: tuple[int, ...] = ()) -> tuple[SeenObject, str] | None:
        """Someone near to say hello to, and what the reason adds: one draw a person against `chat`, (build step 5.2) its
        odds raised by boredom at `frame` (`curious_odds`; 5.1's owed break passed the draw without the dice); never
        someone who LOOKS like the person the story's own step names (`story_gfx`), nor (the verifier's round) someone who
        has already SPOKEN to it (`_Memory.spoke`)."""
        for person in self._people(look):
            key = f"{world.current}|{person.local_id}"
            if (key in self.memory.talked or key in self.memory.chat_drawn or abs(person.dx) + abs(person.dy) > 4
                    or person.graphics_id in story_gfx):
                continue
            if key in self.memory.spoke:
                # (build step 5.2, the verifier's round) never someone who has SPOKEN to it (`notice`): the nurse right
                # after the heal, the clerk after the shop, the footprints man after his scene (127 chats of the graded
                # sweep heard nothing new, the nurse's 1,747-1,957 frames each)
                continue
            self.memory.chat_drawn.add(key)
            draw = self.rng.random()
            odds, odds_why = self.curious_odds(self.state.errands.chat, look.frame if frame is None else frame)
            if draw < odds:
                return person, (f" (draw {draw:.2f} < {odds_why})" if odds > self.state.errands.chat else "")
        return None

    # ------------------------------------------------------------------ where to heal and shop
    def _known_interiors(self, world, suffix: str) -> list[tuple[str, str]]:
        """(the interior's map const, the town map key it is entered from) of every interior with `suffix` the AI has been
        in (a warp link to it is known)."""
        out = []
        for name, link in world.warps.items():
            source = name.split("|")[0]
            target = world.maps.get(link.get("to"))
            if target is not None and (target.const or "").endswith(suffix) and not link.get("inferred"):
                out.append((target.const, source))
        return out

    def home_heals(self, world) -> str | None:
        """(build step 5.1, review #4: step 5 went home to heal once FLAG_RESCUED_BIRCH was set, a flag no player sees) Why
        a person knows home is a place to heal, or None: MOM SAID so (`MOM_HEAL_WORDS`, read as whole words: "If anything
        happens, you can come home.", "I think you should rest a bit."), or it SAW her heal the party (`home_heals`)."""
        for words in MOM_HEAL_WORDS:
            page = heard_page(world.heard, words, self.memory.pages)
            if page is not None:
                return f"MOM said {quote(page, words)!r}"
        if self.memory.home_heals:
            return f"it saw MOM heal the party ({self.memory.home_heals} time(s))"
        return None

    def _nearest_place(self, world, suffix: str, landmark: str, name: str, keep=lambda const: True,
                       reachable: bool = False) -> tuple | None:
        """(build step 5.1, the verifier's second round: CH2T walked back to OLDALE's centre and mart, the ones it had been
        IN, past PETALBURG's, whose doors it had seen) The NEAREST place of a kind by the known way (`world_distance`): one
        it has been in (`suffix`) or one whose door it has SEEN (`landmark`), the one it has been in on a tie; `keep`
        filters by the interior's map constant. Step 5 took any place it had been in before any door it had seen.
        (chapter 7 NS4, 2026-11-06) `reachable` (the SHOP): only a place a known way leads to (`UNREACHABLE`)."""
        options = []
        for const, source in self._known_interiors(world, suffix):
            if keep(const):
                options.append((world_distance(world, source), 0, const, (const, None, None, f"the {name} it knows ({const})")))
        for (key, tile), kind in sorted(self.memory.landmarks.items()):
            if kind != landmark or key not in world.maps or world.maps[key].outside(tile):
                # (the round's development sweep step51wdev1, seeds 33, 36, 37, 38: OLDALE's centre door seen from ROUTE
                # 102 across its right edge was kept on ROUTE 102 at (56, 16), and as the NEAREST place it was a door
                # nobody could reach) a door past an edge the AI has seen crossed is the next map's, not this one's
                continue
            const = f"{world.maps[key].const}_{suffix}"
            if not keep(const) or any(option[2] == const for option in options):
                continue  # its inside is known already: that is the same place
            options.append((world_distance(world, key), 1, const,
                            (const, key, tile, f"the {name} door it saw on {world.maps[key].const} at {tile}")))
        # (chapter 7 NS4, 2026-11-06) a MART no known way leads to from here (`world_distance` 99: no link, no ride) is no
        # place to go: probe7 C1, on the island with no way back known, chose 7 shop errands for the mainland's marts. (A
        # HEAL keeps every place it knows: a party in danger tries the nearest it knows, as before)
        if reachable:
            options = [option for option in options if option[0] < UNREACHABLE]
        return min(options, key=lambda option: option[:3])[3] if options else None

    def _place_key(self, world, where: tuple) -> str | None:
        """The map key of the town a heal or shop place (`heal_place`, `_mart_place`) is entered from: its door's map, or
        the town a known interior's warp leads from; None when it is not known (home: the player's house)."""
        if where[1] is not None:
            return where[1]
        return next((source for const, source in self._known_interiors(world, CENTER_SUFFIX)
                     + self._known_interiors(world, MART_SUFFIX) if const == where[0]), None)

    @staticmethod
    def _building_town(world) -> tuple[str | None, str | None]:
        """(chapter 6 stops round 7, VR6-4) The TOWN of the building the player is in, as (its map key, its map const): the
        town a known way out of this map leads to (the world memory's warps and edges: the door it came in by), else, for a
        GYM, the town its name carries (static map data, `door_of`'s rule: "DEWFORD_TOWN_GYM" is DEWFORD_TOWN's) when the AI
        knows that town's map. (None, None) outdoors, or for a building whose town it does not know."""
        here = world.here()
        if here is None or not here.const or open_way(here.const):
            return None, None
        for kind, link in world.links_from(world.current):
            key = link.get("to") if kind == "warp" else link.get("target")
            memory = world.maps.get(key)
            if memory is not None and memory.const and OUTDOOR.match(memory.const) and not memory.const.startswith("ROUTE"):
                return key, memory.const
        if is_gym(here.const):
            name = here.const[: -len(GYM_SUFFIX) - 1]
            keys = sorted(key for key, memory in world.maps.items() if memory.const == name)
            if keys:
                return keys[0], name
        return None, None

    def center_seen_on(self, key: str | None) -> bool:
        """(build step 5.1, the verifier's second round) A POKéMON CENTER's door seen on map `key`."""
        return any(kind == "pokemon_center" and where == key for (where, _), kind in self.memory.landmarks.items())

    def door_of(self, world, target_map: str | None) -> tuple[str, tuple[int, int]] | None:
        """(build step 5.1, the verifier's second round) The door a person RECOGNISES as `target_map`'s: a GYM's
        (`GYM_SUFFIX`), seen on the town whose name the gym's carries ("PETALBURG_CITY_GYM" on PETALBURG CITY): (that map's
        key, the door), or None."""
        if not is_gym(target_map):
            return None
        town = target_map[: -len(GYM_SUFFIX) - 1]
        doors = sorted((key, tile) for (key, tile), kind in self.memory.landmarks.items()
                       if kind == "gym" and key in world.maps and world.maps[key].const == town)
        return doors[0] if doors else None

    def heal_place(self, world, reachable: bool = False) -> tuple | None:
        """Where it would heal: (the map to be in, the map key of a door seen but never used or None, that door or None,
        how it knows): the NEAREST centre it has been in or whose door it has seen (`_nearest_place`; build step 5.1);
        home, once it KNOWS MOM heals (`home_heals`), when no centre is known. (Chapter 6 stops round 5, VR4-2)
        `reachable` (V3-1's TOP-UP before a fight where it cannot train, the party neither in danger nor under its heal
        line): only a place a known way leads to, as the SHOP (`_nearest_place`); home too only when a known way leads
        there; else None (no heal)."""
        here = world.here()
        if here is not None and (here.const or "").endswith(CENTER_SUFFIX):
            return here.const, None, None, "in a POKéMON CENTER: the nurse"
        nearest = self._nearest_place(world, CENTER_SUFFIX, "pokemon_center", "POKéMON CENTER", reachable=reachable)
        if nearest is not None:
            return nearest
        why = self.home_heals(world)
        if why is not None:
            home = self.story.resolve("<player_house_1f>")
            homes = [key for key, memory in world.maps.items() if memory.const == home]
            if reachable and homes and min(world_distance(world, key) for key in homes) >= UNREACHABLE:
                return None  # (round 5, VR4-2) a top-up does not head home when no known way leads there
            if homes:
                return home, None, None, f"no POKéMON CENTER known yet: home, where MOM heals ({why})"
        return None

    def _mart_place(self, world, index: int = 0) -> tuple | None:
        """Where it would shop: a MART it is in, has been in, or whose door it saw; never one whose LIST had no POKé BALLS
        while the story has not moved on since (`no_balls`: a person comes back later)."""

        def stocked(const: str) -> bool:
            return self.memory.no_balls.get(const, -1) < index

        here = world.here()
        if here is not None and (here.const or "").endswith(MART_SUFFIX) and stocked(here.const):
            return here.const, None, None, "in a MART"
        # (build step 5.1, the verifier's second round) the NEAREST stocked mart, been in or its door seen
        return self._nearest_place(world, MART_SUFFIX, "mart", "MART", keep=stocked, reachable=True)

    # ------------------------------------------------------------------ bookkeeping
    def prep(self, milestone: Milestone) -> dict:
        return self.memory.fight_prep.setdefault(milestone.id, {"steps": 0, "sessions": 0, "wild": 0, "won": 0,
                                                                "rests": 0, "ready": False})

    # ------------------------------------------------------------------ (BP-1) boss preparation
    def bp_record(self, milestone_id: str | None) -> dict | None:
        """The boss-preparation record of the fight `milestone_id` (`fight_prep[...]["bp"]`, game memory: a continue keeps
        it), or None."""
        prep = self.memory.fight_prep.get(milestone_id or "")
        return prep.get("bp") if prep else None

    def raising_for(self, milestone_id: str) -> bool:
        """(m11) A raise plan is ACTIVE for this fight: its step-5 training is not chosen (one budget per boss)."""
        record = self.bp_record(milestone_id)
        return record is not None and record.get("status") == "active"

    def boss_prep(self, look: Observation, index: int) -> tuple | None:
        """(BP-1, spec sections 1 and 1.6) The readiness verdict for the NEXT gym leader (`next_boss`), run when
        the party's signature (PID, species, level, max HP, moves) or the boss changed since the last run, and logged
        (`[AI-BOSSPREP]`); no RNG drawn but the plan's own draw (`bossprep_rng`). For a leader in `ACT_ON` only:
        a NOT READY verdict with no plan yet makes ONE plan (Story, Catcher: `active`; Trainer: `logged`, the in-run
        control), stored once (m10); an active plan whose trainee reached its target is re-judged (READY or CLOSE: done;
        else the target one higher). Returns (the boss milestone id, the leader's name, its gym, the record) for a leader
        in ACT_ON, else None."""
        found = next_boss(self.story.milestones, index)
        if found is None:
            self.bp_boss = None
            return None
        boss_ms, name = found
        gym = gym_leaders().get(name)
        self.bp_boss = (boss_ms.id, name, gym)
        party = members_of(look)
        team = boss_party(name)
        if not party or not team:
            return None
        # acted on only for a leader in ACT_ON whose fight is the NEXT NAMED FIGHT ahead: in chapter 5 the rival's fight
        # (`ch5_rival_meet`) comes first, so BRAWLY's plan waits for chapter 6 and chapters 1-5 play exactly as before
        # (the spec's scope guard, section 0: "chapters 1-5 unchanged by construction"; its "next boss" alone looks
        # past the rival)
        named = next((m for m in self.story.milestones[max(0, index):] if not m.optional and m.fight_named), None)
        acts = name in ACT_ON and named is boss_ms
        record = self.prep(boss_ms).setdefault("bp", new_record()) if acts else None
        if record is not None and record.get("boss") is None:
            record["boss"] = name  # (round 2) who the record is for: a plan settled after its boss is beaten (E3)
        # the run's BASE personality decides the plan and its budget (round 2, V-m3: the active one drifts mid-raise, 6379;
        # FAULT `base_to_active`)
        personality = self.state.active if self.bp_faults.base_to_active else self.state.base
        signature = (name, tuple((m.pid, m.species, m.level, m.max_hp, m.moves) for m in party))
        if signature != self._bp_seen:
            self._bp_seen = signature
            self._judge(boss_ms.id, name, party, team, personality, record)
        return (boss_ms.id, name, gym, record) if acts else None

    def _judge(self, boss_id: str, name: str, party: list, team, personality: str, record: dict | None) -> None:
        """One verdict run (`boss_prep`): logged; the plan made or re-judged for a leader in ACT_ON."""
        active = record is not None and record["status"] == "active"
        lead = record["trainee"] if active else party[0].pid
        verdict = judge_party(party, lead, team, personality)
        self._say(f"[AI-BOSSPREP] {name} ({boss_id}): team {team_line(team)}; party "
                  f"{described(party)}; verdict for the {personality}: {verdict.line()}"
                  + (f"; plan {record['plan'] or '-'} ({record['status']})" if record is not None else
                     " (not acted on in BP-1: logged)"))
        if record is None:
            return
        if active:
            trainee = next((m for m in party if m.pid == record["trainee"]), None)
            if trainee is None:
                spend(record, "the trainee is no longer in the party")
                self._say(f"[AI-BOSSPREP] {name}: the trainee {record['trainee']:08x} is no longer in the party: the plan "
                          f"is given up")
            elif trainee.level >= record["target"]:
                if verdict.cls in (READY, CLOSE):
                    record["status"] = "done"
                    self._say(f"[AI-BOSSPREP] {name}: the trainee {trainee.species} reached L{trainee.level} (target "
                              f"{record['target']}): {verdict.cls}: the raise is done")
                else:
                    record.update(with_target(record, record["target"] + 1))
                    self._say(f"[AI-BOSSPREP] {name}: the trainee {trainee.species} reached L{trainee.level} and the "
                              f"verdict still reads NOT READY: the target is now L{record['target']} (within the budget)")
            return
        if record["status"] != "none" or verdict.cls != NOT_READY:
            return
        self._plan(name, party, team, personality, record)

    def _plan(self, name: str, party: list, team, personality: str, record: dict) -> None:
        """Make the ONE plan (spec section 1.6): the options, one draw among the near-best from `bossprep_rng`."""
        found, said = raise_options(party, team, personality)
        rng = self.bossprep_rng if self.bossprep_rng is not None else random.Random(0)
        choice, how = choose_plan(rng, near_best(personality), found, record["failed"])
        self._say(f"[AI-BOSSPREP] {name}: options "
                  f"{[f'{o.species} L{o.level} -> L{o.target} ({o.projected}, cost {o.cost}, left {o.party_left:.2f})' for o in found]}"
                  f"; {'; '.join(said) or 'every member has one'}")
        if choice is None:
            self._say(f"[AI-BOSSPREP] {name}: no plan ({how}): it fights as it is")
            return
        record.update(plan=choice.plan, trainee=choice.pid, target=choice.target)
        record["status"] = "active" if personality in ACTING else "logged"
        self._say(f"[AI-BOSSPREP] {name}: the plan: raise {choice.species} ({choice.pid:08x}) from L{choice.level} to "
                  f"L{choice.target} as the one who leads ({choice.projected}); {how}; "
                  + ("it acts on it" if record["status"] == "active" else
                     f"the {personality} only logs it (it trains as it always has)"))

    def raise_maps(self, world, cap: int) -> list[str]:
        """(round 2, spec section 2.5, BP1-L1) Where to raise, RANKED: among the maps it has visited with grass of their own
        and a known way there, whose wild land levels a guide lists (`knowledge/seasoned.py` land_levels), first those
        whose top level is at most `cap` (the strongest map the party's knock-out Pokemon clears with room to spare), by
        the highest top (higher-level foes give more experience: the RULE a seasoned player knows, never a yield), then the
        nearer, then the name; then every other one by the lowest top. [] when none is."""
        found = []
        for key, memory in world.maps.items():
            if not (memory.visits and memory.const and inside_grass(memory)):
                continue
            levels = land_levels(memory.const)
            if levels is None:
                continue
            distance = world_distance(world, key)
            if distance >= UNREACHABLE:
                continue
            found.append((levels[1], distance, memory.const))
        fit = sorted((item for item in found if item[0] <= cap), key=lambda item: (-item[0], item[1], item[2]))
        rest = sorted((item for item in found if item[0] > cap), key=lambda item: (item[0], item[1], item[2]))
        out: list[str] = []
        for item in fit + rest:
            if item[2] not in out:
                out.append(item[2])
        return out

    def raise_cap(self, look: Observation, trainee) -> tuple[int, str]:
        """(round 2, spec section 2.5) The raise map's cap and why: the stronger of the trainee and its partner (the
        strongest other member by (level, max HP), no eggs) less `PARTNER_MARGIN`; the trainee's level counts only when it
        is the stronger (a strong trainee fights its own battles). FAULT `map_by_trainee`: BP-1's rule (the trainee + 2)."""
        if self.bp_faults.map_by_trainee:
            return trainee.level + 2, f"FAULT map_by_trainee: the trainee's L{trainee.level} + 2"
        others = [m for m in look.party or () if not m.is_egg and m.pid != trainee.pid]
        partner = max(others, key=lambda m: (m.level, m.max_hp), default=None)
        top = max(trainee.level, partner.level if partner is not None else 0)
        who = (f"its {partner.species} L{partner.level}" if partner is not None and partner.level > trainee.level
               else f"the trainee's own L{trainee.level}")
        return top - PARTNER_MARGIN, f"{who} less {PARTNER_MARGIN}"

    def _trainee_low(self, look: Observation, bp_plan: tuple | None) -> str | None:
        """(round 2, spec section 2.4, V-M1) "fainted" or "low (<hp>/<max>)" when the plan's record is ACTIVE, its trainee
        is in the party, and its HP is 0 or under `TRAINEE_FLOOR` of its max; (round 4, V3-m3, the lead's E5) "out of PP"
        when every move it has that hurts is at 0 PP (`bossprep.out_of_pp`: a heal at a POKéMON CENTER restores PP; a
        Potion does not, so `_potion_goal` takes only "low"); None otherwise (always in chapters 1-5). FAULT `pp_ignored`:
        PP not asked (round 3)."""
        record = bp_plan[3] if bp_plan is not None else None
        if record is None or record.get("status") != "active":
            return None
        trainee = next((m for m in look.party or () if m.pid == record.get("trainee") and not m.is_egg), None)
        if trainee is None:
            return None
        if trainee.hp <= 0:
            return "fainted"
        if trainee.hp < trainee.max_hp * TRAINEE_FLOOR:
            return f"low ({trainee.hp}/{trainee.max_hp})"
        if not self.bp_faults.pp_ignored and out_of_pp(member_now(look, trainee.pid)):
            return "out of PP (no PP left in any move that hurts)"
        return None

    def _partner_worn(self, look: Observation, bp_plan: tuple | None, world=None) -> str | None:
        """(round 2, the builder's addition) An ACTIVE plan's knock-out partner fainted or (round 3, V2-M1) not a partner
        against the wild Pokemon of the map the next raise goes to (`_raise_place`; `bossprep.partner_worn`): no member
        could then take the trainee's place and the raise battle would be run from. (Round 4, E1) never on a map where it
        fails the line even healed: the trainee raises there by its own fights only (`mode_on`)."""
        record = bp_plan[3] if bp_plan is not None else None
        if record is None or record.get("status") != "active" or record.get("trainee") is None:
            return None
        place = self._raise_place(look, world, record) if world is not None else None
        return partner_worn(look, int(record["trainee"]), self.bp_faults, place)

    def _raise_key(self, place: str) -> str:
        """(BP1-L2) A raise map's own cooldown key. FAULT `one_raise_key`: one key for every map."""
        return "raise" if self.bp_faults.one_raise_key else f"raise:{place}"

    def _raise_place(self, look: Observation, world, record: dict) -> str | None:
        """(round 3) The map the next raise session goes to, as `_raise_goal` chooses it, or None. (Round 4, the round-3
        verifier's V3-m4 and the lead's E6) THE SAME choice, `_raise_choice`, for both: round 3 repeated the rule here, and
        a mutant that let this copy ignore a map put aside left every test green."""
        choice = self._raise_choice(look, world, record)
        return choice[0] if choice is not None else None

    def mode_on(self, look: Observation, place: str | None, trainee: int) -> tuple[str, str]:
        """(round 4, the round-3 verifier's V3-M1; the lead's design E1) HOW the trainee is raised on `place`: "mix" (USER
        RULING 59's mix: switch-training to the knock-out partner, its own winnable fights, and the party resting when the
        partner is worn) when the partner, HEALED, is a partner against every wild Pokemon of that map
        (`bossprep.partner_line_full`), or when there is no knock-out partner (a strong trainee fights its own battles);
        "own" (its own winnable fights ONLY: no switch-training, and no rest for the partner) when the partner fails the
        line there even healed: no heal could make it fit, so a rest for it would never end (the heal loop). Returns (mode,
        why). FAULT `partner_full_unchecked`: always "mix" (round 3)."""
        if self.bp_faults.partner_full_unchecked:
            return "mix", "FAULT partner_full_unchecked"
        healed = partner_line_full(look, trainee, place, self.bp_faults)
        if healed is None or healed[0]:
            return "mix", "its knock-out partner is fit there once healed" if healed is not None else "no knock-out partner"
        partner = raise_partner_of(look.party, trainee)
        return "own", (f"its knock-out Pokemon {partner.species} L{partner.level} is no partner on {place} even healed "
                       f"({healed[1]}): its own winnable fights only")

    def _raise_choice(self, look: Observation, world, record: dict) -> tuple | None:
        """(round 4, E1 and E6) WHERE and HOW the next raise session goes, the ONE rule `_raise_goal` and `_raise_place`
        both read: among the ranked maps (`raise_maps`, under the partner's cap first) that are not put aside, the first
        map UNDER THE CAP where the healed partner is fit (`mode_on` "mix"); with none, the first map not put aside, in
        "own" mode (the trainee's own winnable fights only). Returns (place, mode, why, maps, cap, cap_why), or None when the
        trainee is not in the party or every map is put aside."""
        trainee = next((m for m in look.party or () if m.pid == record.get("trainee")), None)
        if trainee is None:
            return None
        cap, cap_why = self.raise_cap(look, trainee)
        maps = self.raise_maps(world, cap)
        allowed = [place for place in maps if self._allowed(self._raise_key(place))]
        if not allowed:
            return None
        for place in allowed:
            levels = land_levels(place)
            if levels is None or levels[1] > cap:
                continue
            mode, why = self.mode_on(look, place, trainee.pid)
            if mode == "mix":
                return place, mode, why, maps, cap, cap_why
        mode, why = self.mode_on(look, allowed[0], trainee.pid)
        return allowed[0], mode, why, maps, cap, cap_why

    def _plan_spent(self, look: Observation, world, record: dict, personality: str) -> str | None:
        """(round 4, E1) Why an ACTIVE plan is SPENT now, or None: the first bound of its one budget reached
        (`spent_reason`, M5), or no grass within reach to raise on. Read by the decision BEFORE any rest
        (`_spend_if_over`) and, as before, by `_raise_goal`."""
        spent = spent_reason(record, personality)
        if spent is not None:
            return spent
        trainee = next((m for m in look.party or () if m.pid == record.get("trainee")), None)
        if trainee is not None and not self.raise_maps(world, self.raise_cap(look, trainee)[0]):
            return "no grass within reach for the raise"
        return None

    def _spend_if_over(self, look: Observation, world, plan: tuple) -> None:
        """(round 4, the round-3 verifier's V3-M1; the lead's design E1) An ACTIVE plan over its budget is spent at the
        START of the decision, before the heal step: a spent plan never heals for the plan (round 3 checked the budget only
        in `_raise_goal`, after the heal step; with the partner failing its line even at full HP every decision was a heal
        and the budget was never read: frames at 10**7, still active)."""
        _boss_id, name, _gym, record = plan
        if record is None or record.get("status") != "active":
            return
        personality = self.state.active if self.bp_faults.base_to_active else self.state.base
        spent = self._plan_spent(look, world, record, personality)
        if spent is not None:
            self._spend(record, name, spent)

    @staticmethod
    def _raise_name(look: Observation, bp_plan: tuple | None) -> str:
        record = bp_plan[3] if bp_plan is not None else None
        trainee = next((m for m in look.party or () if record is not None and m.pid == record.get("trainee")), None)
        return f"the raise's trainee {trainee.species} L{trainee.level}" if trainee is not None else "the raise's trainee"

    def _potion_goal(self, look: Observation, world, milestone: Milestone, bp_plan: tuple | None, trainee_low: str | None,
                     worn: str | None, fainted: bool, share: float) -> Goal | None:
        """(round 2, spec section 2.4 point 4, USER RULING 59) A POTION on the spot for the raise's trainee, when ALL hold:
        (a) it is LOW, not fainted (a Potion revives nothing); (b) nothing else needs the heal (no other member fainted,
        the strongest not in danger, the party at its heal line or above, the partner not worn: Potions are for the
        trainee alone); (c) the nearest heal place it can get to is NOT near (more than `CENTRE_NEAR_LINKS` known links,
        or none); (d) the bag holds a `FIELD_POTIONS` item; (e) the potion goal is not put aside. Otherwise None and the
        heal step's own goal stands (a centre when one is near, the trainee fainted, or the bag holds nothing). FAULTS
        `potion_always` (c ignored), `centre_always` (never), `potion_revives` (a ignored)."""
        faults = self.bp_faults
        if trainee_low is None or faults.centre_always:
            return None
        if not trainee_low.startswith("low") and not (faults.potion_revives and trainee_low == "fainted"):
            return None
        boss_id, _name, _gym, record = bp_plan
        trainee_pid = int(record["trainee"])
        others_fainted = any(m.hp <= 0 for m in look.party or () if not m.is_egg and m.pid != trainee_pid)
        if (others_fainted or (fainted and not faults.potion_revives) or needs_rest(look.party) is not None
                or share < self.state.errands.heal_below or worn is not None):
            return None
        where = self.heal_place(world, reachable=True)
        key = self._place_key(world, where) if where is not None else None
        links = world_distance(world, key) if key is not None else UNREACHABLE
        near = where is not None and key is not None and links <= CENTRE_NEAR_LINKS
        if near and not faults.potion_always:
            return None
        items = [(name, count) for name, count in (look.bag.healing if look.bag is not None else ())
                 if count > 0 and name in FIELD_POTIONS]
        if not items or not self._allowed("potion"):
            return None
        trainee = next(m for m in look.party or () if m.pid == trainee_pid)
        place = (f"the nearest POKéMON CENTER it can get to is {links} links away" if where is not None and key is not None
                 else "it knows no POKéMON CENTER it can get to")
        return Goal("potion", f"{trainee.species} is low ({trainee.hp}/{trainee.max_hp}) and {place}: a "
                              f"{sorted(items, key=lambda i: FIELD_POTIONS.index(i[0]))[0][0]} here", boss_id,
                    key="potion", pid=trainee_pid)

    def _raise_goal(self, look: Observation, world, plan: tuple) -> Goal | None:
        """(BP-1; round 2) The RAISE goal while the plan is active (spec section 3.1), or None; the budget spent (M5) or no
        grass within reach ends the plan ("spent": `spend`, the boss is then fought as today). (Round 2, V-M1's second
        guard) never begun with the trainee under its floor (or its partner worn), even when no heal goal could be made:
        "the raise waits". (BP1-L1, BP1-L2) the map from `raise_maps` under the partner's cap, one cooldown key a map
        (`raise:<map>`): a map that fails twice is put aside and the next one tried; every one put aside: the raise waits
        (counted nowhere). FAULTS `raise_guard_off`, `one_raise_key`. (Round 4, E1 and E6) the map and the MODE from
        `_raise_choice`, the one rule `_raise_place` reads too: a map where the healed knock-out partner fails its line is
        no switch-training map ("own": the trainee's own winnable fights only), said in the goal's reason."""
        boss_id, name, _gym, record = plan
        if record is None or record["status"] != "active":
            return None
        personality = self.state.active if self.bp_faults.base_to_active else self.state.base
        trainee = next((m for m in look.party or () if m.pid == record["trainee"]), None)
        spent = self._plan_spent(look, world, record, personality) if trainee is not None else spent_reason(record,
                                                                                                             personality)
        if spent is None and trainee is None:
            spent = "no grass within reach for the raise"
        if spent is not None:
            self._spend(record, name, spent)
            return None
        low = self._trainee_low(look, plan) or self._partner_worn(look, plan, world)
        if low is not None and not self.bp_faults.raise_guard_off:
            self._say(f"[AI-BOSSPREP] {name}: the raise waits: the trainee is low ({low})")
            return None
        choice = self._raise_choice(look, world, record)
        if choice is None:
            cap, _ = self.raise_cap(look, trainee)
            self._say(f"[AI-BOSSPREP] {name}: the raise waits: every raise map is put aside for now "
                      f"({self.raise_maps(world, cap)})")
            return None
        where, mode, mode_why, _maps, cap, cap_why = choice
        levels = land_levels(where)
        how = "" if mode == "mix" else f"; OWN FIGHTS ONLY: {mode_why}"
        return Goal("raise", f"the plan for {name}: raise {trainee.species} L{trainee.level} ({trainee.pid:08x}) to "
                             f"L{record['target']}, leading, on {where} (wild L{levels[0]}-{levels[1]}; the cap L{cap}: "
                             f"{cap_why}){how}; {record['battles']} battles, {record['frames']} frames, "
                             f"{record['sessions']} sessions so far",
                    boss_id, map=where, steps=self.state.errands.train_session, key=self._raise_key(where))

    def _spend(self, record: dict, name: str, why: str) -> None:
        """(round 2, E1) The plan SPENT (`bossprep.spend`: its lead left to settle), said."""
        spend(record, why)
        self._say(f"[AI-BOSSPREP] {name}: the raise ends, budget spent ({why}): no endless grind; it fights as it is")

    def _lead_goal(self, look: Observation, here_const: str | None, plan: tuple) -> Goal | None:
        """(spec section 3.1) On the leader's own gym map with the raise DONE: the trainee back in the lead (a battle can
        leave the order changed), when it is not first and has HP. (Round 2, V-m5 E2) bounded: none once the plan's
        `reorder_fails` reached its budget, `relead_fails` reached `RELEAD_FAILS_MAX`, or `leads` reached `LEADS_MAX` (the
        verifier's V4: with `reorder_fails` at 99 it still made one). FAULTS `lead_ignores_budget`, `relead_unbounded`."""
        boss_id, name, gym, record = plan
        if record is None or record["status"] != "done" or here_const != gym or not self._allowed("lead"):
            return None
        faults = self.bp_faults
        bounds = BUDGET.get(self.state.base) or BUDGET["Story"]
        if not faults.lead_ignores_budget and (record.get("reorder_fails", 0) >= bounds["reorder_fails"]
                                               or record.get("leads", 0) >= LEADS_MAX):
            return None
        if not faults.relead_unbounded and not faults.lead_ignores_budget and record.get("relead_fails", 0) >= RELEAD_FAILS_MAX:
            return None
        party = [m for m in look.party or () if not m.is_egg]
        trainee = next((m for m in party if m.pid == record["trainee"]), None)
        if trainee is None or trainee.hp <= 0 or not party or party[0].pid == trainee.pid:
            return None
        return Goal("lead", f"before {name}: its raised {trainee.species} L{trainee.level} ({trainee.pid:08x}) leads, as "
                            f"the plan judged", boss_id, key="lead", pid=trainee.pid)

    def _settle_goal(self, look: Observation, index: int) -> Goal | None:
        """(round 2, spec section 3, V-m5) The LEAD when a plan has ENDED, on every decision, whatever the plan now:
          E1, a plan SPENT before its boss (`settle` pending): the verdict is run with the usual lead (`lead_before`) and
              with the trainee leading; the trainee is KEPT first only when its verdict is strictly better (the class, then
              the party's HP left: a counter that fell short may still beat the usual lead on paper), else the usual lead
              is restored;
          E3, the boss BEATEN (its milestone behind the story) with the plan done or spent and the trainee still first:
              the usual lead is restored (`settle_after`): the plan's change ends with the fight it was for.
        No restore (the settle is "done", no press) when there is no usual lead, it is the trainee, it has left the party
        or fainted, or the trainee is not first (nothing of the plan's to undo). FAULTS `restore_never`, `restore_always`."""
        faults = self.bp_faults
        party = [m for m in look.party or () if not m.is_egg]
        if not party:
            return None
        for boss_id, prep in sorted(self.memory.fight_prep.items()):
            record = prep.get("bp") if isinstance(prep, dict) else None
            if not isinstance(record, dict) or record.get("trainee") is None:
                continue
            try:
                behind = self.story.index(boss_id) < index
            except (KeyError, ValueError):
                behind = False
            if record.get("settle") == "pending" and not behind:
                field, which = "settle", "E1"
            elif (behind and record.get("status") in ("done", "spent")
                  and record.get("settle_after", "none") not in ("done", "kept", "gave up")):
                field, which = "settle_after", "E3"
            else:
                continue
            goal = self._settle_one(look, party, boss_id, record, field, which, faults)
            if goal is not None:
                return goal
        return None

    def _settle_one(self, look: Observation, party: list, boss_id: str, record: dict, field: str, which: str,
                    faults) -> Goal | None:
        name = record.get("boss") or boss_id
        trainee = int(record["trainee"])
        before = record.get("lead_before")
        usual = next((m for m in party if before is not None and m.pid == before), None)
        if faults.restore_never or before is None or before == trainee or usual is None or usual.hp <= 0 \
                or party[0].pid != trainee:
            record[field] = "done"
            self._say(f"[AI-BOSSPREP] {name}: the raise is over ({which}): the lead stays as it is (nothing to restore)")
            return None
        if which == "E1" and not faults.restore_always:
            team = boss_party(name)
            members = members_of(look)
            personality = self.state.base
            if team and members:
                kept = judge_party(members, trainee, team, personality)
                usual_verdict = judge_party(members, before, team, personality)
                if rank_of(kept) > rank_of(usual_verdict):
                    record[field] = "kept"
                    self._say(f"[AI-BOSSPREP] {name}: the raise is over ({record.get('spent_why') or 'spent'}): the "
                              f"trainee stays first: its verdict {kept.cls} ({kept.party_left:.2f}) beats the usual lead's "
                              f"{usual_verdict.cls} ({usual_verdict.party_left:.2f})")
                    return None
        if record.get("relead_fails", 0) >= RELEAD_FAILS_MAX and not faults.relead_unbounded:
            record[field] = "gave up"
            return None
        key = "lead:settle" if field == "settle" else "lead:after"
        if not self._allowed(key):
            return None
        why = record.get("spent_why") or ("the boss is beaten" if which == "E3" else "spent")
        return Goal("lead", f"{name}: the raise is over ({why}): {usual.species} leads again, as before the plan", boss_id,
                    key=key, pid=before)

    def boss_lost(self, look: Observation) -> None:
        """(spec section 3.3, after a loss to the boss) A battle LOST on the boss's gym map: `losses` + 1; a DONE plan was
        too optimistic: it joins `failed` and ONE new plan is chosen among the options not failed, within the budget left
        (a raise map is checked when the goal is chosen); otherwise it fights as today. `MAX_LOSSES` stays the run's stop."""
        if self.bp_boss is None:
            return
        boss_id, name, _gym = self.bp_boss
        record = self.bp_record(boss_id)
        if record is None:
            return
        record["losses"] += 1
        self._bp_seen = None
        state = record["status"]
        self._say(f"[AI-BOSSPREP] {name}: a battle lost on the gym map ({record['losses']} so far; the plan was {state})")
        if state != "done":
            return
        record["failed"].append(record["plan"])
        party = members_of(look)
        team = boss_party(name)
        personality = self.state.base
        if not party or not team or spent_reason(record, personality) is not None:
            spend(record, "a loss after the plan was done, and no new plan (budget or party)")
            self._say(f"[AI-BOSSPREP] {name}: no new plan (budget or party): it fights as it is")
            return
        record["status"] = "none"
        self._plan(name, party, team, personality, record)
        if record["status"] == "none":
            spend(record, "a loss after the plan was done, and no other plan")

    def _allowed(self, key: str) -> bool:
        return self.memory.cooldown.get(key, -1) <= self.memory.decisions

    def outcome(self, goal: Goal, ok: bool) -> None:
        """A goal's result: a success clears its failures; FAIL_LIMIT failures in a row put it aside for a while."""
        if not goal.key:
            return
        if ok:
            self.memory.fails.pop(goal.key, None)
            self.memory.danger_again.pop(goal.key, None)
            return
        fails = self.memory.fails.get(goal.key, 0) + 1
        self.memory.fails[goal.key] = fails
        if fails >= FAIL_LIMIT:
            self.memory.cooldown[goal.key] = self.memory.decisions + COOLDOWN_DECISIONS
            self.memory.fails[goal.key] = 0


def in_place(const: str | None, place: str | None) -> bool:
    """(chapter 6 NS1) Is map `const` the town `place` (a map const) or one of its buildings ("DEWFORD_TOWN_GYM" is in
    "DEWFORD_TOWN")?"""
    return bool(const) and bool(place) and (const == place or const.startswith(f"{place}_"))


def town_of(const: str | None) -> str | None:
    """(chapter 6 NS1) The town or city map `const` is in (itself, or the town its name begins with), or None."""
    towns = [town for town in town_places().values() if in_place(const, town)]
    return max(towns, key=len) if towns else None


class TravelSense:
    """(chapter 6 NS1 and NS2, 2026-11-06) The play brain's answer to a scene's yes/no (`Navigator.answer`): a question
    whose words OFFER A TRIP to a named town (`brain/rides.py` trip_offer) is judged the way a person judges it; every
    other question is answered exactly as before (`skills/story.py` answer_question). A YES to a trip is told to the
    ride watch (`RideWatch.offered`), which keeps what follows as a RIDE if the trip happens.

    THE RULE (USER RULING 40: the words are on the screen; the story's places are what a seasoned player knows): YES only
    when the AI's current goal is reached THROUGH the offered place, or cannot be reached from where it stands:
      0. the RIDE it is taking now (`riding`, `GoalRunner.ride`) offers the trip it is known for: YES;
      1. its goal (`goal_places`: the map its walk is heading for, or else the maps of the milestone it is playing and of
         the next one it needs) is the offered town or a building of it: YES (the first sail: "We'll set sail for
         DEWFORD", with DEWFORD TOWN the next milestone's);
      2. its goal is where it stands (the map, or the town it is in): NO ("sail back to PETALBURG?" in DEWFORD, with the
         letter for STEVEN in DEWFORD: probe8 C1 and C2 said YES and sailed off the island, NS1);
      3. a known way from where it stands to its goal (`brain/explore.py` route_to, the rides counted): YES only when that
         way's first link is a ride to the offered town; otherwise NO, it knows a way without the trip;
      4. no known way: YES when nothing is left it could get to from here on any map (`WorldMemory.left_anywhere`, by the
         region route from where it stands): its goal cannot be reached from here; otherwise NO, it looks round first."""

    def __init__(self, manager: "GoalManager", runner: "GoalRunner", watch: RideWatch | None = None,
                 visited: Callable[[str], bool] | None = None) -> None:
        self.manager = manager
        self.runner = runner
        self.watch = watch
        self.visited = visited or (lambda const: False)
        #: the ride the navigator is taking now (`GoalRunner.ride`), or None
        self.riding: dict | None = None
        #: (frame, the offered place, yes, why) of the last trip judged (for the log and the tests)
        self.last: tuple | None = None

    def answer(self, look: Observation) -> tuple[bool, str]:
        words = folded(look.screen.text)
        place = trip_offer(words)
        if place is None:
            return answer_question(look)
        yes, why = self.judge(look, place)
        self.last = (look.frame, place, yes, why)
        if yes and self.watch is not None:
            self.watch.offered(look, place, words)
        return yes, f"a trip offered to {place} ({words[:60]!r}): {'YES' if yes else 'NO'}, {why}"

    def goal_places(self, look: Observation) -> dict[str, str]:
        """{map const: why} of what the AI takes for its goal now (the class docstring's rule 1)."""
        heading = getattr(self.runner, "heading", None)
        if heading:
            return {heading: "the map its walk is on its way to"}
        story = self.manager.story
        milestone = getattr(self.runner, "milestone_now", None)
        if milestone is None:
            milestone = self.manager.milestone(look, self.visited)[1]
        if milestone is None:
            return {}
        out: dict[str, str] = {}
        index = story.index(milestone.id)
        following = next((m for m in story.milestones[index + 1:] if not m.optional), None)
        for owner in (milestone, following):
            if owner is None:
                continue
            consts = list(owner.maps) + [step.map for step in owner.steps if step.map] + [owner.hint_map]
            for const in consts:
                if const:
                    out.setdefault(const, f"the story: {owner.title}")
        return out

    def judge(self, look: Observation, place: str) -> tuple[bool, str]:
        """(yes, why) for a trip offered to the town `place` (the class docstring's rules 0-4)."""
        ride = self.riding
        if ride is not None and ride.get("place") == place:
            return True, (f"the ride it is taking toward its goal (it went to {ride.get('to')} for this YES before)")
        world = self.runner.nav.world
        goals = self.goal_places(look)
        if not goals:
            return True, "it has no goal it could name: a person goes along with what the game asks"
        there = next((const for const in sorted(goals) if in_place(const, place)), None)
        if there is not None:
            return True, f"its goal is there: {there} ({goals[there]})"
        here = world.here()
        here_const = here.const if here is not None else None
        area = town_of(here_const)
        at_goal = next((const for const in sorted(goals) if const == here_const or (area and in_place(const, area))),
                       None)
        if at_goal is not None:
            return False, f"its goal is here, not there: {at_goal} ({goals[at_goal]}); a person does not leave it behind"
        nav = self.runner.nav
        found = nav.where(look) if hasattr(nav, "where") else None
        if found is not None:
            memory, at = found
            walls = map_walls(nav, memory, nav.walls(memory, at)) if hasattr(nav, "walls") else frozenset()
            route = route_to(world, memory.key, lambda m, key: m is not None and m.const in goals, at, walls)
            if route is not None:
                first = route[0]
                if first[0] == "ride" and first[1].get("place") == place:
                    return True, f"the way it knows to its goal begins with this trip ({len(route)} link(s))"
                return False, f"it knows a way to its goal from here without the trip ({len(route)} link(s))"
            reachable = region_hops(world, memory.key, at, standing_walls(world))
            left = [key for key, _ in world.left_anywhere() if key in reachable]
            if not left:
                return True, "its goal cannot be reached from where it stands: nothing is left it could get to here"
            names = world.names()
            return False, (f"its goal ({', '.join(sorted(goals)[:3])}) is not there, and it has not looked round all it "
                           f"can get to here yet ({', '.join(names.get(key, key) for key in left[:3])})")
        return False, f"its goal ({', '.join(sorted(goals)[:3])}) is not there"


class _BattleClock:
    """(build step 5.1) A hands watcher: the frames the screen showed a BATTLE, look to look (`_walk_on_after_battles`)."""

    def __init__(self) -> None:
        self.frames = 0
        self._last: tuple[int, bool] | None = None

    def __call__(self, look: Observation) -> None:
        last = self._last
        if last is not None and last[1] and look.frame > last[0]:
            self.frames += look.frame - last[0]
        self._last = (look.frame, bool(look.screen.in_battle))


#: (build step 5.2) the goal kinds that LOOK ROUND a place (curiosity's walks among a map's places): someone who keeps
#: standing in the way is watched for in them (`_PersonBlock`), and the places curiosity found blocked are their walls
ROUND_KINDS = ("explore", "detour", "look_around")


class _PersonBlock:
    """(build step 5.2, the step-5.1 review's finding 1: at OLDALE "people in the way" went from 8 to 61 over three errands,
    about 1,160 presses moving the player 377 steps, all toward frontiers past the west exit someone stood in) A hands
    watcher while curiosity looks round: every time the navigator meets someone in the way (its `stats.people` count rises:
    a step into a person, or a wait for one on the way) it is counted for the PLACE being walked to (the end of the plan
    followed); once that place has met `PERSON_BLOCK_HITS` with no new tile seen since the first, `on_block(map key,
    tile, why)` is told: the place is a wall of this walk at once (the navigator plans round it, so the target is out of
    reach and another is chosen) and blocked for curiosity in the milestone. It presses nothing."""

    def __init__(self, nav, on_block: Callable[[str, tuple[int, int], str], None]) -> None:
        self.nav = nav
        self.on_block = on_block
        self.people = nav.stats.people
        #: (map key, tile) -> [people met there, tiles learned at the first, its frame]
        self.hits: dict[tuple, list] = {}

    def __call__(self, look: Observation) -> None:
        nav = self.nav
        people = nav.stats.people
        if people <= self.people:
            return
        new, self.people = people - self.people, people
        plan = nav.plan
        if plan is None or plan.map != nav.world.current:
            return
        tile = plan.at
        for direction in plan.path:
            tile = moved(tile, direction)
        hit = self.hits.get((plan.map, tile))
        if hit is None or nav.world.tiles_learned > hit[1]:
            hit = self.hits[(plan.map, tile)] = [0, nav.world.tiles_learned, look.frame]
        hit[0] += new
        if hit[0] >= PERSON_BLOCK_HITS:
            self.on_block(plan.map, tile, f"someone stood in the way {hit[0]} times since f{hit[2]}, nothing new seen")
            del self.hits[(plan.map, tile)]


class GoalRunner:
    """Plays one goal with the AI's own skills (the play brain, `ai_player/mode.py`, calls `pursue`). Returns (ok, what
    happened). `mind` is the battle decider (its PURPOSE set per goal: "train" while training or catching, "travel"
    otherwise); `marks` reads the milestone marks of a look (for the story goals' end)."""

    def __init__(self, hands: Hands, nav: Navigator, manager: GoalManager, mind: BattleMind,
                 tell: Callable[[str], None]) -> None:
        self.hands = hands
        self.nav = nav
        self.manager = manager
        self.mind = mind
        self.tell = tell
        #: every roaming session's report line (the training and the spin ratio graders read the action log too)
        self.roams: list[str] = []
        self.picked: list[str] = []
        self.heals: list[str] = []
        self.shopping: list[str] = []
        #: (R1) how a `save` goal is played: the play brain's own save (`mode.py` HandsBrain._save, which owns the memory
        #: file): a generator of the save's outcome; None (no memory file) and no save goal is ever chosen
        self.saver: Callable[[Goal], Generator[None, None, str]] | None = None
        #: (chapter 6 NS1, 2026-11-06) the map a walk of this runner is on its way to now (`_travel`), and the milestone
        #: of the goal being played (`pursue`): what the travel answer (`TravelSense`) takes for "its goal"
        self.heading: str | None = None
        self.milestone_now: Milestone | None = None
        #: (chapter 6 NS2) the travel answer that knows which ride is being taken (`ride`); set by the play brain
        self.travel: TravelSense | None = None
        #: (chapter 6 stops round 5, VR4-1) how many field menus nobody asked for the AI has backed out of so far
        #: (`skills/instructed.py` Instructed.backouts); set by the play brain. A talk that backed out of one failed
        self.backed_out: Callable[[], int] | None = None

    def pursue(self, goal: Goal, milestone: Milestone, index: int, current: Callable[[Observation], int]) -> Generator[None, None, tuple[bool, str]]:
        """`_pursue` the goal; (build step 5.1) a person whose Pokemon is HURT keeps out of the tall grass on ANY walk, not
        only the walk to heal (`HURT_GRASS_COST`; never while training or catching, which ARE the grass), its own taste
        restored after."""
        if goal.kind == "save":
            # (R1, build spec 2026-10-29 section 3 (d)) the save goal is the play brain's (it owns the memory file): "saved"
            # only on the game's SAVED page; a "stuck:" outcome ends the run (the play loop's own check)
            if self.saver is None:
                return False, "no way to save: the run keeps no memory file"
            outcome = yield from self.saver(goal)
            return outcome.startswith("saved"), outcome
        nav = self.nav
        own = getattr(nav, "grass_cost", None)
        hurt = (own is not None and goal.kind not in ("train", "catch", "heal", "raise")
                and self.manager.hurt(self.hands.look()))
        if hurt:
            nav.grass_cost = max(own, HURT_GRASS_COST)
        # (build step 5.1) the tiles a scene sent the player back from, carried from goal to goal within this milestone: a
        # person told twice by LITTLEROOT's twin that it is dangerous without a Pokemon does not try her road with every new
        # errand (measured 2026-10-14, the development sweep step51dev5, seeds 2, 3 and 9: after looking round LITTLEROOT the
        # AI's walks to the rival's house chose the frontier past the twin, met her twice per walk, and ran out its patience)
        walls = self.manager.memory.scene_walls.setdefault(milestone.id, {}) if hasattr(nav, "carried_scene_walls") else None
        # (build step 5.2, the step-5.1 review's finding 1: "keep person-blocked targets across goals") a walk that LOOKS
        # ROUND (`ROUND_KINDS`) also walls the places curiosity found blocked in this milestone, and watches for someone
        # who keeps standing in the way (`_PersonBlock`); those places are never handed to the story's walks
        blocked = self.manager.memory.blocked.setdefault(milestone.id, {}) if goal.kind in ROUND_KINDS else None
        # (build step 5.2, the verifier's round) the corners round the places a scene blocked are curiosity's walls too
        # (`_scene_corners`), and never join the story's: the ones that were not the milestone's walls already
        corners = ({key: _scene_corners(places) - set((walls or {}).get(key, set())) for key, places in blocked.items()}
                   if blocked is not None else {})
        if walls is not None:
            nav.carried_scene_walls = walls if blocked is None else {
                key: set(walls.get(key, set())) | set(blocked.get(key, {})) | corners.get(key, set())
                for key in set(walls) | set(blocked)}
            # (build step 5.2, found by the round's development sweep step52dev2, seed 1010, by the new pushing property:
            # 114,121 frames pressing with nothing new) every goal STARTS from this milestone's walls: a goal that runs no
            # intent (a talk to someone at hand) left the LAST intent's walls in the navigator, and the merge below carried
            # them into this milestone (PROF. BIRCH's "Don't leave me like this!" walls on ROUTE 101, kept into the rival's
            # milestone: every walk north from LITTLEROOT planned round them, back across the edge, until the patience ran out)
            nav.scene_walls = {key: set(tiles) for key, tiles in nav.carried_scene_walls.items()}
        watch = None
        watchers = getattr(self.hands, "watchers", None)
        if blocked is not None and watchers is not None and hasattr(nav, "stats"):
            watch = _PersonBlock(nav, lambda key, tile, why: self._blocked(milestone, key, tile, why))
            watchers.append(watch)
        given_up = getattr(nav, "scene_given_up", None)
        given_from = len(given_up) if given_up is not None else 0
        turned = getattr(nav, "scene_turned", None) or []
        turned_from = len(turned)
        # (build step 5.2, the verifier's round) who speaks in a service talk or a chat is remembered (`notice`)
        self.manager.memory.hearing = goal.kind in HEARD_KINDS
        self.milestone_now = milestone
        # (chapter 7 NS3, 2026-11-06) any walk that is not the story's own (an errand, a look round, a go) STOPS when the
        # one its story's next step names comes into view on that step's map (`story_in_view`): a person carrying a
        # letter for STEVEN who walks into his room speaks to him (probe7 C2 walked into STEVEN's room on a shop errand
        # and out again 198 frames later; C1 did it under a go goal that looked round)
        stops = goal.kind not in OWN_PERSON_KINDS and hasattr(nav, "stop_for")
        # (chapter 7 stops round 4, V3-3) never a walk that prepares for the fight the story's next step is
        # (`PREP_WALK_KINDS`): with BRAWLY in view in his gym, a training walk out to the grass goes on
        if stops and goal.kind in PREP_WALK_KINDS and self.manager.fight_levels(milestone)[0]:
            stops = False
        if goal.kind == "raise":
            stops = False  # (BP-1) a committed raise for the next leader goes on, as a training walk before a known fight
        if stops:
            nav.stop_for = lambda look: self.story_in_view(look, milestone)
        # (BP-1, spec section 3.3) a battle LOST in a goal begun on (or headed for) the next leader's gym map is a loss to
        # that leader: the boss-preparation record learns it
        world_now = getattr(nav, "world", None)
        start = world_now.here() if hasattr(world_now, "here") else None
        start_const = getattr(start, "const", None)
        lost_before = battles_lost(getattr(nav, "battle_log", None) or ())
        # (boss preparation round 2, V-m3, spec section 2.6) a heal, a look for a centre or a potion BEGUN while a raise plan
        # is active is part of that plan's ONE budget: its frames are counted into the plan's (the first spec's 3.3 intent)
        plan_record = self._plan_heal_record(goal)
        plan_began = self.hands.pad.frames if plan_record is not None else 0
        try:
            result = yield from self._pursue(goal, milestone, index, current)
            boss = self.manager.bp_boss
            if (boss is not None and boss[2] is not None and boss[2] in (start_const, goal.map)
                    and self.manager.bp_record(boss[0]) is not None
                    and battles_lost(getattr(nav, "battle_log", None) or ()) > lost_before):
                # the last look the hands took (no new look: nothing else is told of this check)
                self.manager.boss_lost(self.hands.last if self.hands.last is not None else self.hands.look())
            return result
        finally:
            # (round 4, V3-m2, the lead's E4) the goal's purpose and guard end with it: the battles until the next goal
            # take the plan's own state (`between_goals`)
            self.between_goals(goal)
            if plan_record is not None:
                plan_record["frames"] = plan_record.get("frames", 0) + self.hands.pad.frames - plan_began
                if goal.kind in ("heal", "find_center"):
                    plan_record["heals"] = plan_record.get("heals", 0) + 1
            if stops:
                nav.stop_for = None
            self.manager.memory.hearing = False
            if watch is not None and watch in watchers:
                watchers.remove(watch)
            if hurt:
                nav.grass_cost = own
            if blocked is not None and given_up is not None:
                # (build step 5.2, the round's development sweep step52dev2: in 4 of the 7 detours that did not arrive, a
                # look round had just given up a place past LITTLEROOT's twin, and the detour after it chose the same place,
                # or the one beside it, and met her twice more) a place a scene turned a look round back from is blocked for
                # curiosity in the milestone, as one someone stood in the way of is; (the verifier's round, step52vdev2, CH1
                # seed 1209: a detour ended at the footprints man's first word, and the look round after it walked OLDALE
                # 2,003 frames toward his corner) and so is the tile where a scene BEGAN and turned it back, after ONE
                # meeting: a person told "please don't come in here" does not try that way again for curiosity's sake
                for key, tile, why in given_up[given_from:] + turned[turned_from:]:
                    self._blocked(milestone, key, tuple(tile), why)
            if blocked is None:
                # (the verifier's round, step52vdev5, NOHINTS seed 1245: the STORY's walk had met the footprints man, and a
                # look round "some more" later in the milestone walked into his scene twice, 2,320 frames) a scene that
                # turned ANY walk back is blocked for curiosity in the milestone; the story's own walks keep their walls
                for key, tile, why in turned[turned_from:]:
                    self.manager.blocked_on(milestone.id, key)[tuple(tile)] = why
            if walls is not None:
                for key, tiles in (getattr(nav, "scene_walls", None) or {}).items():
                    walls.setdefault(key, set()).update(set(tiles) - set((blocked or {}).get(key, {})))
                    walls[key] -= corners.get(key, set())
                nav.carried_scene_walls = None

    def _guard_for(self, goal: Goal) -> int | None:
        """(round 3, the round-2 verifier's V2-M2; the lead's design D2) Whom the battle brain protects in this goal's
        battles: the trainee of the next boss's plan while that plan is ACTIVE, in every goal but a raise (the raise
        battle's own rules) and the BOSS FIGHT itself (the story's own talk to the leader: `talk:<look>` in the boss's
        milestone; a plan done or spent is not active, and its trainee may lead the boss on purpose). The trainee stays
        FIRST between raise sessions (the spec; the rejected alternative, restoring the lead each session, costs a reorder
        a session and loses the trainee's share of the walks' battles). WHY: round 2 told the battle brain nothing outside a
        raise, and the trainee led the walks to heal it, the pick-ups and the travel: 5 faints in 6 live runs, one from
        3/21 on the walk to the POKéMON CENTER. FAULTS `guard_unset` (never: round 2), `guard_in_boss_fight` (the boss
        fight not left out). (Round 4) the plan's trainee and the boss fight are read by `_plan_trainee` and `_boss_fight`,
        which the battles BETWEEN goals read too (`between_goals`)."""
        if goal.kind == "raise" or self._boss_fight(goal):
            return None
        return self._plan_trainee()

    def _plan_trainee(self) -> int | None:
        """(round 3; round 4, E4) The PLAN's own state: the trainee of the next boss's plan while that plan is ACTIVE, else
        None (always in chapters 1-5). FAULT `guard_unset`: None (round 2)."""
        manager = self.manager
        if manager.bp_faults.guard_unset or manager.bp_boss is None:
            return None
        record = manager.bp_record(manager.bp_boss[0])
        if record is None or record.get("status") != "active" or record.get("trainee") is None:
            return None
        return int(record["trainee"])

    def _boss_fight(self, goal: Goal) -> bool:
        """(round 3) The BOSS FIGHT itself: the story's own talk to (or use of) the leader in the next boss's milestone
        (`talk:<look>`). FAULT `guard_in_boss_fight`: never."""
        manager = self.manager
        if manager.bp_faults.guard_in_boss_fight or manager.bp_boss is None:
            return False
        return (goal.milestone == manager.bp_boss[0] and goal.kind in ("talk", "use") and goal.look is not None
                and goal.key == f"{goal.kind}:{goal.look}")

    def between_goals(self, goal: Goal | None = None) -> None:
        """(round 4, the round-3 verifier's V3-m2; the lead's design E4) The battle brain as a goal ENDS (`pursue`): a
        battle between goals (a scene that begins while the next goal is decided, or one a goal hands back mid-screen) is
        fought with the guard of the PLAN's state, never the last goal's: the active plan's trainee is guarded whenever no
        raise goal runs (`_plan_trainee`), and a raise's purpose "raise" and trainee end with it ("travel", the play brain's
        own between goals). WHY: round 3 set them per goal and reset nothing, so after a raise goal a scene's battle had
        purpose "raise" with no trainee and no guard: no protection and no switch (4 such battles in 6 live runs, Grovyle at
        28/68 fighting on with Struggle). After the BOSS FIGHT's own talk the guard stays off (its battle may still be on
        screen). Only a raise's purpose is reset: a story battle a talk hands back is fought, not run from ("train", the
        purpose `_pursue` gives talks), as in chapters 1-5. FAULT `seam_kept`: nothing reset (round 3)."""
        mind, manager = self.mind, self.manager
        if mind is None or manager.bp_faults.seam_kept:
            return
        if getattr(mind, "purpose", None) == "raise":
            mind.purpose = "travel"
            mind.trainee = None
        guard = None if goal is not None and self._boss_fight(goal) else self._plan_trainee()
        mind.guard = guard
        mind.say = self.tell if guard is not None else None
        if guard is not None:
            mind.bp_faults = manager.bp_faults

    def _plan_heal_record(self, goal: Goal) -> dict | None:
        """(round 2) The ACTIVE raise plan's record a goal of `PLAN_HEAL_KINDS` counts into (the next boss's, by
        `bp_boss`, its status read at the goal's START), or None (FAULT `heal_frames_uncounted`: always None)."""
        manager = self.manager
        if goal.kind not in PLAN_HEAL_KINDS or manager.bp_boss is None or manager.bp_faults.heal_frames_uncounted:
            return None
        record = manager.bp_record(manager.bp_boss[0])
        return record if record is not None and record.get("status") == "active" else None

    def _blocked(self, milestone: Milestone, key: str, tile: tuple[int, int], why: str) -> None:
        """(build step 5.2) `_PersonBlock` found a place blocked: a wall of this walk now (the navigator plans round it and
        chooses another place), and blocked for curiosity in the milestone (`GoalManager.blocked_on`)."""
        self.manager.blocked_on(milestone.id, key)[tile] = why
        walls = getattr(self.nav, "scene_walls", None)
        if walls is not None:
            walls.setdefault(key, set()).add(tile)
        name = getattr(self.nav.world.maps.get(key), "const", None) or key
        self.tell(f"[AI-GOALS] the place at {tile} on {name}: {why}: given up, and kept from curiosity in this milestone")

    def story_in_view(self, look: Observation, milestone: Milestone) -> str | None:
        """(chapter 7 NS3, 2026-11-06) Why a walk that is not the story's own stops here, or None: the milestone's next
        step is a talk (or a use) of someone (something) it RECOGNISES by their look, the player stands on that step's
        map, and they are on the screen now (`GoalManager.looks_like`): what the screen shows, nothing else."""
        player = look.player
        if player is None or player.settling or look.screen.game_state != "OVERWORLD" or look.view is None:
            return None
        manager = self.manager
        step = manager.story_step(look, self.nav.world, milestone)
        if step is None or step.do not in ("talk", "use") or not step.look or step.map != player.map_const:
            return None
        seen = manager.looks_like(look, step.look)
        if seen is None:
            return None
        return (f"{manager.story.looks[step.look].what}, whom its story's next step names, is in view on {step.map} at "
                f"{(seen.x, seen.y)}")

    def ride(self, target: Target) -> Generator[None, None, str]:
        """(chapter 6 NS2, 2026-11-06) TAKE A RIDE (`Navigator.rider`): the walk has arrived beside where the ride's person
        stood (`Target.ride`, `WorldMemory.rides`). The person is found on the screen by their id and figure, talked to
        (`skills/story.py` talk_to, which meets a walker the way it does), and the travel answer says YES to the trip the
        ride is known for (`TravelSense.riding`); a person who asks something else is answered by the ordinary rules.
        Returns "rode ..." once the controls are back on another map, or why not; a ride not taken (the person not on
        the screen, or the talk ended on the map it began on, free or held there by a menu left open) is put aside until
        there is news (`WorldMemory.close_ride`). (Chapter 7 stops round 4, V3-4, 2026-11-06) "rode" is said only once
        the map has changed: with the screen still held on the same map (MR. BRINEY's multichoice once both deliveries are
        done, `data/maps/Route104_MrBrineysHouse/scripts.inc`), the base said "rode" and put nothing aside."""
        world, hands = self.nav.world, self.hands
        name = target.ride
        ride = world.rides.get(name) if name is not None else None
        if ride is None:
            return "not taken: no such ride is known"
        look = hands.look()
        seen = next((o for o in (look.view.objects if look.view is not None else ())
                     if o.source == "object" and o.kind == "npc" and o.local_id == ride.get("who")
                     and o.graphics_id == ride.get("gfx")), None)
        if seen is None:
            world.close_ride(name, "the person was not on the screen", look.frame)
            return f"not taken: the person who took it (id {ride.get('who')}) is not on the screen here"
        began = world.current
        why = (f"the ride to {world.names().get(ride.get('to'), ride.get('to'))}: the person at {(seen.x, seen.y)} took it "
               f"there for a YES to {str(ride.get('words'))[:60]!r}")
        if self.travel is not None:
            self.travel.riding = ride
        try:
            outcome = yield from talk_to(hands, self.nav, seen, why)
        finally:
            if self.travel is not None:
                self.travel.riding = None
        if world.current == began:
            held = "" if nav_free(hands.look()) else " (the screen still held there)"
            world.close_ride(name, f"talked ({outcome}) and was not carried off{held}",
                             hands.last.frame if hands.last else 0)
            return f"not taken: {outcome}; still on {world.names().get(began, began)}{held}"
        return f"rode: {outcome}; now on {world.names().get(world.current, world.current)}"

    def _out_of_ideas(self, milestone: Milestone, why: str, said: list[str]) -> None:
        """(build step 5.2, the verifier's round) A walk with NO LEAD found nothing left on any map it knows that it could
        get to (`lost_intent`): remembered with what the world memory had seen then (`WorldMemory.stamp`), so the next
        decision gives the run up if nothing new has been seen since (`GoalManager.next_goal`); `why` is the walk's word."""
        said.append(why)
        self.manager.memory.lost_end = (milestone.id, self.nav.world.stamp())

    def _pursue(self, goal: Goal, milestone: Milestone, index: int, current: Callable[[Observation], int]) -> Generator[None, None, tuple[bool, str]]:
        hands, nav, manager = self.hands, self.nav, self.manager
        moved_on = lambda look: current(look) != index  # noqa: E731 - the milestone changed: the story moved on
        # a battle the STORY starts (PROF. BIRCH's bag, a talk) is fought, not run from (measured 2026-10-14: the play brain's
        # first chapter-1 run tried RUN in PROF. BIRCH's battle, which the game refuses); training and catching fight too
        self.mind.purpose = ("raise" if goal.kind == "raise" else
                             "train" if goal.kind in ("train", "catch", "use", "talk", "follow") else "travel")
        # (boss preparation round 3, the round-2 verifier's V2-M2) an ACTIVE plan's trainee is protected in every battle of
        # this goal (`_guard_for`): the battle brain is told whom (`BattleMind.guard`, its line through `say`). None in
        # chapters 1-5 (no plan), in a raise (its own rules) and in the boss fight itself
        guard = self._guard_for(goal)
        self.mind.guard = guard
        if goal.kind != "raise":
            self.mind.say = self.tell if guard is not None else None
            if guard is not None:
                self.mind.bp_faults = manager.bp_faults
        if goal.kind in ("go", "look_around", "follow", "find", "explore"):
            target_map = goal.map if goal.kind == "go" else None
            look_for = goal.look
            # (build step 5.1, review #1) a walk that ARRIVES on an outdoor map whose look-around draw is due stops there: the
            # next decision may look around the place (not the beeline control's, `errands_off`; not a search of one map).
            # MEASURED 2026-10-14 (the development sweeps step51dev2 to dev4): stopping only on maps NEVER visited, the draw was
            # due on few decisions (a goal ends in a centre, a mart, a house, and the next walk crossed the towns and routes
            # without a decision there), and the look-around was played in 2 to 3 runs of 9
            stop_new = goal.kind in ("go", "look_around") and not manager.errands_off
            arrived: list[str] = []
            began_on = nav.world.current

            # (build step 5.2) its own name: a call-site census by name must not take every other `done` for this one
            def walk_done(look: Observation) -> bool:
                if moved_on(look):
                    return True
                if goal.words and heard_words(nav.world.heard, goal.words):
                    return True  # told where to go now: decide again
                if manager.item_ball_in_view(look, nav.world) is not None:
                    return True  # an item ball came into view on the way: a person stops to pick it up (pillar 4)
                player = look.player
                if target_map is not None and player is not None and player.map_const == target_map \
                        and not player.settling and look.screen.game_state == "OVERWORLD":
                    return True
                if (stop_new and player is not None and not player.settling and look.screen.game_state == "OVERWORLD"
                        and player.map_const != target_map and OUTDOOR.match(player.map_const or "")
                        and player.map_const == getattr(nav.world.here(), "const", None)):
                    if (nav.world.current not in manager.memory.looked
                            and manager.may_look_around(look, nav.world, manager.story_step(look, nav.world, milestone))):
                        arrived.append(f"{NEW_MAP_STOP}: {player.map_const}")
                        return True
                    # (build step 5.1, the verifier's second round; build step 5.2: by BOREDOM's dice, not a quota) a walk
                    # that ARRIVES on another outdoor map makes one draw there a milestone; when it passes, the walk stops
                    # so the next decision may take a break from the story there
                    stop = f"{nav.world.current}|{milestone.id}"
                    if (nav.world.current != began_on and stop not in manager.memory.break_stops and not manager.hurt(look)
                            and manager.curious_ok()):
                        manager.memory.break_stops.add(stop)
                        bored, since = manager.boredom(look.frame)
                        draw = manager.rng.random()
                        if draw < CURIOUS_ODDS_CAP * bored:
                            arrived.append(f"{BREAK_STOP}: {player.map_const} (draw {draw:.2f} < "
                                           f"{CURIOUS_ODDS_CAP * bored:.2f}: {since} frames since its last curiosity that "
                                           f"came to something)")
                            return True
                if goal.kind == "go" and stop_new and walk_battle_break(look):
                    return True
                return look_for is not None and manager.looks_like(look, look_for) is not None

            battles_at = [len(getattr(nav, "battle_log", None) or ())]

            def walk_battle_break(look: Observation) -> bool:
                """(build step 5.2, the round's development sweep step52dev3: the Trainer's chapter 2, seed 1017, walked
                25,408 frames on ROUTE 102, met 17 battles and stopped for nothing, the walk's only stops being a map's
                arrival; the review's finding 2: errands not INTERLEAVED) a battle won on the walk is a moment to stop too:
                once the player is free again on an outdoor map, one boredom draw per battle."""
                count = len(getattr(nav, "battle_log", None) or ())
                player = look.player
                if (count <= battles_at[0] or player is None or player.settling or look.screen.game_state != "OVERWORLD"
                        or not OUTDOOR.match(player.map_const or "") or not player_free(look)):
                    return False
                battles_at[0] = count
                if manager.hurt(look) or not manager.curious_ok():
                    return False
                bored, since = manager.boredom(look.frame)
                draw = manager.rng.random()
                if draw >= CURIOUS_ODDS_CAP * bored:
                    return False
                arrived.append(f"{BREAK_STOP}: after a battle on {player.map_const} (draw {draw:.2f} < "
                               f"{CURIOUS_ODDS_CAP * bored:.2f}: {since} frames since its last curiosity that came to "
                               f"something)")
                return True

            budget = (GO_FRAMES if goal.kind == "go" else FIND_FRAMES if goal.kind == "find"
                      else goal.steps if goal.kind == "explore" else goal.steps or LOOK_AROUND_FRAMES)
            if goal.kind == "go" and is_gym(target_map):
                # (build step 5.1, the verifier's second round) a GYM is RECOGNISED by its door's look: walked into once seen
                outcome = yield from self._to_building(goal, target_map, budget, walk_done)
                if arrived:
                    outcome = f"{outcome}; {arrived[0]}"
                return outcome.startswith(("done", "entered")), outcome
            if goal.kind == "go" and target_map is not None:
                outcome = yield from self._walk_on_after_battles(target_map, goal.reason, budget, walk_done)
            else:
                # looking for someone on THIS map keeps to it (a person searching ROUTE 103 for the rival does not go back
                # to OLDALE); looking around for what comes next may go anywhere; (build step 5.2, the step-5.1 review's
                # finding 1) a LOOK ROUND (`explore`) chooses only places that can show something new, never one curiosity
                # found blocked here, and is over once none is left (5.1 wandered among what it had seen: CH1M's look round
                # of OLDALE, 3,001 frames, nothing new)
                # (build step 5.2, the verifier's round) a walk with NO LEAD (`LOST_KEYS`: nothing the game said names where
                # to go) heads for what is left anywhere it knows, and says when nothing is: "out of ideas" (`lost_intent`)
                lost_why: list[str] = []
                seen_clock: list = [None, 0]

                def look_saw_nothing(look: Observation) -> bool:
                    """(build step 5.2, the verifier's round; its development sweep step52vdev3, CH2 seed 1220: a look round
                    of ROUTE 102's grass ran its 4,200 frames through 21 battles and showed 9 new tiles, the experience
                    each battle gave resetting its novelty window) a look round is a walk to SEE: it is over once it has
                    seen nothing new (no tile, no map) for `CURIOUS_NOVELTY` frames, the battles met in it included; and
                    at every stop of the walk (`walk_done`)."""
                    if walk_done(look):
                        return True
                    now = (nav.world.tiles_learned, sum(1 for memory in nav.world.maps.values() if memory.visits))
                    if seen_clock[0] != now:
                        seen_clock[0], seen_clock[1] = now, look.frame
                        return False
                    return look.frame - seen_clock[1] >= CURIOUS_NOVELTY

                intent = (look_round_intent(manager.state.active, budget, look_saw_nothing,
                                            lambda key: manager.blocked_on(milestone.id, key))
                          if goal.kind == "explore"
                          else lost_intent(manager.state.active, budget, walk_done,
                                           lambda why: self._out_of_ideas(milestone, why, lost_why))
                          if goal.kind in ("go", "look_around") and goal.key.startswith(LOST_KEYS)
                          else travel_intent(None, manager.state.active, budget, walk_done, stay=goal.kind == "find",
                                             back=self._leader_back(goal, milestone)))
                outcome = yield from nav.run(intent, goal.reason)
                if lost_why:
                    outcome = f"{lost_why[-1]} ({outcome})"
            if arrived:
                outcome = f"{outcome}; {arrived[0]}"
            if goal.kind == "explore":
                # looking around is its own end: a look round that ran its time, or found nothing more to look at, ended
                # as it should (build step 5.2: whether it BROUGHT anything is its yield, `goal_yield`, judged by the play
                # loop: an unproductive look round is "not done" there and exhausts the map for the milestone)
                return outcome.startswith(("done", "budget", "stuck: nothing")), outcome
            return outcome.startswith("done"), outcome
        if goal.kind == "detour":
            # (build step 5.2, the step-5.1 review's finding 3: "detours are cosmetic") only a detour that REACHED its place
            # is done ("reached ..."); one that did not is "not reached ..." and no curiosity
            outcome = yield from self._detour(goal, milestone)
            return outcome.startswith("reached"), outcome
        if goal.kind == "find_center" and goal.via is not None:
            # (build step 5.1, the verifier's second round) THIS town's own centre: looked for here, keeping to the town,
            # until its door is seen (the next decision heals at the nearest place it knows: that door, now)
            walked = ""
            if nav.world.current != goal.via and goal.map:
                # (chapter 6 stops round 7, VR6-4) looked for from a building of the town (its gym): out to the town first,
                # as `_go_inside` walks back to a door's town
                outcome = yield from self._travel(goal.map, f"{goal.reason}: out to {goal.map}", CENTER_LOOK_FRAMES,
                                                  lambda look: moved_on(look) or manager.center_seen_on(goal.via)
                                                  or (look.player is not None and look.player.map_const == goal.map))
                if nav.world.current != goal.via or manager.center_seen_on(goal.via) or moved_on(self.hands.look()):
                    seen = manager.center_seen_on(goal.via)
                    return seen, outcome + (f"; its door seen on {goal.map}" if seen else
                                            f"; did not get out to {goal.map} to look")
                walked = f"out to {goal.map}: {outcome}; "
            outcome = yield from nav.run(travel_intent(None, manager.state.active, CENTER_LOOK_FRAMES,
                                                       lambda look: moved_on(look) or manager.center_seen_on(goal.via),
                                                       stay=True), goal.reason)
            seen = manager.center_seen_on(goal.via)
            return seen, walked + outcome + (f"; its door seen on {goal.map}" if seen else
                                             f"; no POKéMON CENTER seen on {goal.map}")
        if goal.kind == "find_center":
            outcome = yield from nav.run(travel_intent(None, manager.state.active, FIND_FRAMES * 2,
                                                       lambda look: moved_on(look) or manager.heal_place(nav.world) is not None),
                                         goal.reason)
            found = manager.heal_place(nav.world)
            return found is not None, outcome + (f"; found: {found[3]}" if found is not None else "")
        if goal.kind == "seek":
            # back to where it last saw who it looks for: the seen tile beside that spot nearest by the known way
            found = nav.where(hands.look())
            if found is None:
                return False, "the player's tile is not known"
            memory, here = found
            spots = [moved(goal.tile, d) for d in DIRECTIONS if memory.passable(moved(goal.tile, d))]
            spots.sort(key=lambda xy: (abs(xy[0] - here[0]) + abs(xy[1] - here[1]), xy))
            for spot in spots[:3]:
                outcome = yield from nav.go_to(spot, goal.reason, FIND_FRAMES)
                if manager.looks_like(hands.look(), goal.look) is not None:
                    return True, f"seen again near {goal.tile}"
                if moved_on(hands.look()):
                    return True, outcome
            return False, f"not seen again near {goal.tile}"
        if goal.kind in ("use", "talk", "chat"):
            if goal.target is None:
                return False, "nobody to talk to"
            key = f"{nav.world.current}|{goal.target.local_id}"
            manager.memory.talked.add(key)
            before = party_share(hands.look())
            backed = self.backed_out() if self.backed_out is not None else 0
            if goal.kind == "use":
                outcome = yield from use_thing(hands, nav, goal.target, goal.reason)
            else:
                outcome = yield from talk_to(hands, nav, goal.target, goal.reason)
            self._saw_mom_heal(goal.target, before)
            if self.backed_out is not None and self.backed_out() > backed:
                # (chapter 6 stops round 5, VR4-1) the talk opened a field menu nobody asked it to choose from (MR.
                # BRINEY's PETALBURG/SLATEPORT/EXIT on DEWFORD's dock after a curiosity chat, #106 arm A) and the AI backed
                # out of it: the talk did not do what it was for, so it FAILED, as any failed chat (`GoalManager.outcome`
                # counts it toward `FAIL_LIMIT`; the person is in `talked`, never chatted with again)
                return False, f"{outcome}; it backed out of a menu nobody asked it to choose from"
            return outcome.startswith("talked"), outcome
        if goal.kind == "pick_up" and goal.target is None and goal.tile is not None:
            outcome = yield from self._back_to_ball(goal, milestone, index, current)
            return outcome.startswith("picked up"), outcome
        if goal.kind == "pick_up":
            ball = goal.target
            key = f"{nav.world.current}|{ball.x},{ball.y}"
            tries = manager.memory.item_tries.get(key, 0) + 1
            manager.memory.item_tries[key] = tries
            battles = len(nav.battle_log)
            outcome = yield from pick_up(hands, nav, ball, goal.reason)
            # a walk a battle or a scene interrupted is tried again (a person walks back over to it), up to `ITEM_TRIES`
            # times (measured 2026-10-14, the chapter-2 development run c2c: its one item ball on ROUTE 102 was given up
            # after a wild battle stopped the walk to it, and the run picked up none). A battle met on the walk counts as an
            # interruption however the walk then ended (the step-5 verifier's round, the graded CH2 arm: a ROUTE 102
            # trainer's battle took the walk's 4,000 frames, the walk ended "unreachable", and the ball was given up)
            interrupted = outcome.startswith("not picked up: interrupted") or (
                len(nav.battle_log) > battles and not outcome.startswith("picked up"))
            if not interrupted or tries >= ITEM_TRIES:
                manager.memory.tried_items.add(key)
            if outcome.startswith("picked up"):
                self.picked.append(f"{nav.world.here().const if nav.world.here() else '?'} {(ball.x, ball.y)}: {outcome}")
            return outcome.startswith("picked up"), outcome
        if goal.kind == "raise":
            return (yield from self._raise(goal, moved_on))
        if goal.kind == "lead":
            return (yield from self._lead(goal))
        if goal.kind == "potion":
            return (yield from self._potion(goal))
        if goal.kind in ("train", "catch"):
            where = self._grass_map(milestone)
            if where is not None:
                went = yield from self._travel(where, f"{goal.reason}: to the grass of {where}", GO_FRAMES,
                                               lambda look: moved_on(look) or (look.player is not None
                                                                                and look.player.map_const == where))
                if nav.world.here() is None or nav.world.here().const != where:
                    return False, f"could not get to the grass of {where}: {went}"
            self.roam_hooks(hunt=goal.kind == "catch")
            before = len(nav.battle_log)
            try:
                outcome = yield from roam_train(hands, nav, goal.steps, goal.reason)
            finally:
                self.clear_roam_hooks()
            self.roams.append(outcome)
            numbers = roam_numbers(outcome)
            if numbers is not None and not outcome.startswith("roamed"):
                # a roam that STOPPED (a rest, an item ball): its numbers recorded too, as the roam skill records a
                # finished one (the graders count training steps and spins from these records)
                hands.note("roam", "metrics", outcome[:300], {**numbers, "stopped": outcome.split(";", 1)[0][:160]})
            met = nav.battle_log[before:]
            wild = sum(1 for _, kind, _ in met if kind == "wild")
            won = sum(1 for _, kind, result in met if kind == "wild" and result == "won")
            if goal.kind == "train":
                prep = manager.prep(milestone)
                prep["steps"] += numbers["steps"] if numbers else 0
                prep["sessions"] += 1
                prep["wild"] += wild
                prep["won"] += won
                prep["rests"] += 1 if "rest:" in outcome else 0
            return ("roamed" in outcome or "rest:" in outcome or ITEM_STOP in outcome or HUNT_STOP in outcome), outcome
        if goal.kind == "heal":
            outcome = yield from self._heal(goal)
            self.heals.append(outcome)
            return outcome == "healed", outcome
        if goal.kind == "shop":
            outcome = yield from self._shop(goal, index)
            self.shopping.append(outcome)
            return "bought" in outcome, outcome
        return False, f"no way to pursue a {goal.kind} goal"

    def _saw_mom_heal(self, target: SeenObject | None, before: float | None) -> None:
        """(build step 5.1, review #4) A person learns that MOM heals by SEEING it: the party, hurt before talking to someone
        who LOOKS like MOM, is whole right after (`GoalManager.home_heals`)."""
        manager = self.manager
        mom = manager.story.looks.get("mom")
        if target is None or mom is None or target.graphics_id not in mom.gfx or before is None or before >= 0.999:
            return
        after = party_share(self.hands.look())
        if after is not None and after >= 0.999:
            manager.memory.home_heals += 1
            self.tell(f"[AI-GOALS] it saw MOM heal the party ({before:.0%} -> {after:.0%}): home is a place to heal")

    def _back_to_ball(self, goal: Goal, milestone: Milestone, index: int,
                      current: Callable[[Observation], int]) -> Generator[None, None, str]:
        """(build step 5.1, review #1) Back over to an item ball it SAW on this map earlier: a seen tile beside it, nearest by
        the map's coordinates, until the ball is on screen; then picked up like one in view. Gone from where it lay
        (picked up already, or never a ball): given up."""
        nav, hands, manager = self.nav, self.hands, self.manager
        key = f"{nav.world.current}|{goal.tile[0]},{goal.tile[1]}"
        found = nav.where(hands.look())
        if found is None:
            manager.memory.tried_items.add(key)
            return "not picked up: the player's tile is not known"
        memory, here = found
        spots = sorted((moved(goal.tile, d) for d in DIRECTIONS if memory.passable(moved(goal.tile, d))),
                       key=lambda xy: (abs(xy[0] - here[0]) + abs(xy[1] - here[1]), xy))
        for spot in spots[:2]:
            ball = manager.item_ball_in_view(hands.look(), nav.world)
            if ball is not None and (ball.x, ball.y) == goal.tile:
                break
            yield from nav.go_to(spot, goal.reason, FIND_FRAMES)
            if current(hands.look()) != index:
                return "not picked up: the story moved on on the way"
        ball = manager.item_ball_in_view(hands.look(), nav.world)
        if ball is None or (ball.x, ball.y) != goal.tile:
            manager.memory.tried_items.add(key)
            return f"not picked up: no item ball where it lay at {goal.tile} any more"
        outcome = yield from self.pursue(replace(goal, target=ball, tile=None), milestone, index, current)
        return outcome[1]

    def _raise(self, goal: Goal, moved_on: Callable[[Observation], bool]) -> Generator[None, None, tuple[bool, str]]:
        """(BP-1, spec sections 3.1 and 3.2) One RAISE session for the plan of `goal.milestone`: the trainee put FIRST
        (`hands/party_order.py` lead_with) before anything, the trainee rule on every battle from then on (its rest, M4), the
        walk to the raise map, the roam; the battles fought with purpose "raise" (no switch, no catch) and the trainee as
        the battle mind's `trainee`. Counted into the ONE budget (M5): wild battles begun, the goal's frames, sessions,
        stalls (no level gained), reorder failures, leaked battles (the trainee fainted and another finished it). The
        EXPERIENCE is measured: the trainee's and the strongest other member's summary EXP at the start and the end."""
        hands, nav, manager = self.hands, self.nav, self.manager
        record = manager.bp_record(goal.milestone)
        if record is None or record.get("trainee") is None:
            return False, "no raise plan"
        pid = int(record["trainee"])
        faults = manager.bp_faults
        began = hands.pad.frames
        look = hands.look()
        start_level = next((m.level for m in look.party or () if m.pid == pid), None)
        start_hp = next((f"{m.hp}/{m.max_hp}" for m in look.party or () if m.pid == pid), "?")
        exp_before = self._raise_exp(look, pid)
        watch = RaiseWatch(pid, self.tell)
        before = len(nav.battle_log)
        outcome = "the raise did not begin"
        mind = self.mind
        if getattr(mind, "raise_modes", None) is not None:
            mind.raise_modes.clear()
        if record.get("lead_before") is None and not record.get("sessions"):
            # (round 2, V-m5) the lead BEFORE the plan, set ONCE, at its first raise session, before the trainee is put
            # first: the lead a plan that ends gives back (`GoalManager._settle_goal`)
            first = next((m for m in look.party or () if not m.is_egg), None)
            record["lead_before"] = first.pid if first is not None else None
        try:
            if not (yield from lead_with(hands, pid, f"{goal.reason}: the trainee first")):
                record["reorder_fails"] += 1
                outcome = "the trainee could not be put first"
                return False, outcome
            self.mind.trainee = pid
            if hasattr(mind, "say"):
                mind.say = self.tell  # (round 2) the raise battle's one line a battle
            if hasattr(mind, "bp_faults"):
                mind.bp_faults = faults
            # (round 4, V3-M1, the lead's E1) HOW this map is raised on (`GoalManager.mode_on`, the rule its choice
            # read): "own", the knock-out partner unfit here even healed, means no switch-training in its battles
            mode, mode_why = manager.mode_on(hands.last if hands.last is not None else look, goal.map, pid)
            if hasattr(mind, "raise_switch"):
                mind.raise_switch = mode == "mix"
            if mode != "mix":
                self.tell(f"[AI-BOSSPREP] raise session on {goal.map}: {mode_why}")
            hands.watchers.append(watch)
            self.roam_hooks(trainee=pid, after_battle=watch.after, raise_map=goal.map)
            where = goal.map
            if where is not None and (nav.world.here() is None or nav.world.here().const != where):
                went = yield from self._travel(where, f"{goal.reason}: to the grass of {where}", GO_FRAMES,
                                               lambda seen: moved_on(seen) or (seen.player is not None
                                                                                and seen.player.map_const == where))
                if nav.world.here() is None or nav.world.here().const != where:
                    outcome = f"could not get to the grass of {where}: {went}"
                    return False, outcome
            outcome = yield from roam_train(hands, nav, goal.steps, goal.reason)
            self.roams.append(outcome)
            numbers = roam_numbers(outcome)
            if numbers is not None and not outcome.startswith("roamed"):
                hands.note("roam", "metrics", outcome[:300], {**numbers, "stopped": outcome.split(";", 1)[0][:160]})
            return ("roamed" in outcome or "rest:" in outcome or ITEM_STOP in outcome), outcome
        finally:
            self.clear_roam_hooks()
            if watch in hands.watchers:
                hands.watchers.remove(watch)
            self.mind.trainee = None
            if hasattr(mind, "raise_switch"):
                mind.raise_switch = True  # (round 4, E1) switch-training is the raise's default ("mix")
            if hasattr(mind, "say"):
                mind.say = None
            modes = list(getattr(mind, "raise_modes", None) or ())
            if getattr(mind, "raise_modes", None) is not None:
                mind.raise_modes.clear()
            met = nav.battle_log[before:]
            record["battles"] += sum(1 for _, kind, _ in met if kind == "wild")
            if not faults.frames_uncounted:
                record["frames"] += hands.pad.frames - began
            record["sessions"] += 1
            record["leak_battles"] += watch.leaks
            record["reorder_fails"] += watch.not_leading
            own = modes.count("own")
            switched = modes.count("switch") + modes.count("rescue")
            runs = modes.count("run")
            record["own_fights"] = record.get("own_fights", 0) + own
            record["switch_fights"] = record.get("switch_fights", 0) + switched
            record["raise_runs"] = record.get("raise_runs", 0) + runs
            last = hands.last if hands.last is not None else look
            end_level = next((m.level for m in last.party or () if m.pid == pid), None)
            exp_after = self._raise_exp(last, pid)
            gained_exp = exp_after[0] - exp_before[0]
            record["exp_gained"] = record.get("exp_gained", 0) + max(0, gained_exp)
            record["partner_exp"] = record.get("partner_exp", 0) + max(0, exp_after[1] - exp_before[1])
            # (round 2, spec section 2.6, V-m3) a STALL is a session in which the trainee's summary EXP did not rise (BP-1
            # counted "no level gained": at L15 and up a session of 7-10 battles gains 300-450 EXP of the 721-1,141 a level
            # needs, so honest progress read as a stall). FAULTS `stall_by_level` (BP-1's), `stalls_never`
            if faults.stall_by_level:
                gained = start_level is not None and end_level is not None and end_level > start_level
            else:
                gained = gained_exp > 0
            record["stalls"] = 0 if (gained or faults.stalls_never) else record["stalls"] + 1
            self.tell(f"[AI-BOSSPREP] raise exp: trainee +{gained_exp}, others +"
                      f"{exp_after[1] - exp_before[1]} ({exp_before[2]}); L{start_level} -> L{end_level}; "
                      f"{len(met)} battles ({watch.leaks} leaked, {watch.not_leading} not led by the trainee); own {own}, "
                      f"switch-trained {switched}, run {runs}; trainee {start_hp} at start; stalls {record['stalls']}; "
                      f"{outcome[:120]}")

    def _lead(self, goal: Goal) -> Generator[None, None, tuple[bool, str]]:
        """(BP-1; round 2, spec section 3) A LEAD goal: the member `goal.pid` (the trainee when none is named) put first by
        the party-order hand. Every run counts in the plan's `leads`; a failure in `relead_fails` and `reorder_fails`; at
        `RELEAD_FAILS_MAX` failures the settle it was for is "gave up" (the lead stays as it is); a success settles it."""
        record = self.manager.bp_record(goal.milestone)
        pid = goal.pid if goal.pid is not None else (record.get("trainee") if record is not None else None)
        ok = pid is not None and (yield from lead_with(self.hands, int(pid), f"{goal.reason}: put first"))
        field = {"lead:settle": "settle", "lead:after": "settle_after"}.get(goal.key)
        if record is not None:
            record["leads"] = record.get("leads", 0) + 1
            if not ok:
                record["relead_fails"] = record.get("relead_fails", 0) + 1
                record["reorder_fails"] = record.get("reorder_fails", 0) + 1
                if field is not None and record["relead_fails"] >= RELEAD_FAILS_MAX and not self.manager.bp_faults.relead_unbounded:
                    record[field] = "gave up"
                    self.tell(f"[AI-BOSSPREP] {record.get('boss') or goal.milestone}: the lead could not be restored "
                              f"({record['relead_fails']} failures): the lead stays as it is")
            elif field is not None:
                record[field] = "done"
        if pid is None:
            return False, "nobody to put first"
        return bool(ok), (f"{int(pid):08x} leads" if ok else f"{int(pid):08x} could not be put first")

    def _potion(self, goal: Goal) -> Generator[None, None, tuple[bool, str]]:
        """(round 2, spec section 2.4 points 7-8, USER RULING 59) A POTION goal: the field item hand (`hands/field_item.py`
        use_on) gives the trainee `FIELD_POTIONS`, weakest first, until it is at `POTION_TO` of its max HP or
        `POTIONS_PER_GOAL` are used. Counted in the plan's `potions`. A failure counts toward `FAIL_LIMIT` as any goal."""
        if goal.pid is None:
            return False, "no Pokemon to give a Potion to"
        ok, used, why = yield from use_on(self.hands, goal.pid, FIELD_POTIONS, POTION_TO, POTIONS_PER_GOAL, goal.reason)
        record = self.manager.bp_record(goal.milestone)
        if record is not None:
            record["potions"] = record.get("potions", 0) + used
        return ok, why

    @staticmethod
    def _raise_exp(look: Observation, pid: int) -> tuple[int, int, str]:
        """(M4, point 6) The summary EXP of the trainee and of the strongest OTHER member (by level), and who that is."""
        mons = [m for m in look.party or () if not m.is_egg]
        trainee = next((m for m in mons if m.pid == pid), None)
        others = [m for m in mons if m.pid != pid]
        strongest = max(others, key=lambda m: (m.level, m.max_hp), default=None)
        return ((trainee.experience if trainee is not None else 0), (strongest.experience if strongest is not None else 0),
                f"the strongest other: {strongest.species} L{strongest.level}" if strongest is not None else "no other")

    def roam_hooks(self, hunt: bool = False, trainee: int | None = None,
                   after_battle: Callable[[Observation], str | None] | None = None, raise_map: str | None = None) -> None:
        """What a TRAINING or CATCHING roam asks (set for the roam only, `clear_roam_hooks` after): after every battle, a
        reason to stop and heal (`training_rest`: under the personality's `heal_below`; the navigator asks it with no battle
        limit set: until the step-5 verifier's round of 2026-10-14 it asked only WITH one, so the rule never fired and a run
        roamed on at 22 % HP); on every free look, an item ball come into view (a person walks over to it, then roams on);
        and (build step 5.2) for a CATCHING roam (`hunt`), `HUNT_FRUITLESS` battles in a row that brought nothing new to its
        POKéDEX (`hunt_fruitless`)."""
        nav, manager = self.nav, self.manager
        heal_below, active = manager.state.errands.heal_below, manager.state.active
        nav.battle_limit = None
        nav.battle_rest = lambda look: training_rest(look, heal_below, active)
        if trainee is not None:
            # (BP-1, M4) a RAISE: the trainee's own state decides the rest (fainted, or under a third), not the strongest's;
            # and a battle it did not lead ends the roam (`RaiseWatch`)
            def raise_rest(look: Observation) -> str | None:
                stop = after_battle(look) if after_battle is not None else None
                # (round 2, the builder's addition) and its knock-out partner worn: no member could take the trainee's
                # place, so the roam would run from every battle (`bossprep.partner_worn`; round 3, V2-M1: the partner
                # line against the wild Pokemon of the map it roams, `raise_map`)
                # (round 4, V3-m3, E5) and the trainee out of PP in every move that hurts (`bossprep.trainee_rest`)
                return (stop or trainee_rest(look, trainee, heal_below, active, manager.bp_faults)
                        or partner_worn(look, trainee, manager.bp_faults, raise_map))

            nav.battle_rest = raise_rest
        since = {"battles": len(getattr(nav, "battle_log", None) or ()), "dex": None}

        def hunt_fruitless(look: Observation) -> str | None:
            """The POKéDEX's seen and owned counts as the eyes show them: a change starts the count again."""
            progress = look.progress
            dex = (progress.dex_seen, progress.dex_owned) if progress is not None else None
            if dex != since["dex"]:
                since["dex"], since["battles"] = dex, len(nav.battle_log)
                return None
            fought = len(nav.battle_log) - since["battles"]
            if fought < HUNT_FRUITLESS:
                return None
            return f"{HUNT_STOP}: {fought} battles in a row with no POKéMON first seen and none caught"

        nav.roam_stop = lambda look: (ITEM_STOP if look.party and manager.item_ball_in_view(look, nav.world) is not None
                                      else hunt_fruitless(look) if hunt else None)

    def clear_roam_hooks(self) -> None:
        self.nav.battle_rest = None
        self.nav.roam_stop = None

    # ------------------------------------------------------------------ going somewhere
    def _fights_its_leader(self, goal: Goal, milestone: Milestone) -> bool:
        """(chapter 6 stops round 6, P5-1) Is this a FIND for the gym leader the AI has come to FIGHT (a fight next:
        `GoalManager.fight_levels`), on that leader's own gym (`knowledge/atlas.py` gym_leaders: a seasoned player knows
        each gym's leader)? Then, nothing on the map left to see, the back of the gym is where to look (`gym_back`). Not a
        talk with no fight: chapter 2's NORMAN, whom a script stands in his gym's FRONT room. (Chapter 6 stops round 7,
        VR6-5) The fight next must be with THAT leader (`Milestone.fight_trainers`, milestones.json `fight.trainers`:
        "BRAWLY_1"), not merely some fight: a find for ROXANNE in her gym while BRAWLY's fight is next is not one."""
        if goal.kind != "find" or not goal.look:
            return False
        here = self.nav.world.here()
        const = here.const if here is not None else None
        leader = goal.look.upper()
        return (is_gym(const) and gym_leaders().get(leader) == const
                and any(name == leader or name.startswith(f"{leader}_") for name in milestone.fight_trainers)
                and bool(self.manager.fight_levels(milestone)[0]))

    def _leader_back(self, goal: Goal, milestone: Milestone) -> Callable[[Navigator, Observation], Target | None] | None:
        """(chapter 6 stops round 7, VR6-1) The `back` of a find for the leader it has come to fight (`_fights_its_leader`):
        `gym_back` bound to THAT leader's gym (the map the find began on), so it is offered there and nowhere else; None
        for any other walk."""
        if not self._fights_its_leader(goal, milestone):
            return None
        gym = self.nav.world.here().const

        def back(nav: Navigator, look: Observation) -> Target | None:
            return gym_back(nav, look, gym)

        return back

    def _to_building(self, goal: Goal, target_map: str, budget: int,
                     done: Callable[[Observation], bool]) -> Generator[None, None, str]:
        """(build step 5.1, the verifier's second round: the live CH2T arm searched PETALBURG CITY door by door for its GYM,
        about 25,700 frames, through four houses, the MART and both floors of the POKéMON CENTER) To a building a person
        RECOGNISES by its look (a GYM, `GoalManager.door_of`): its door seen, to its town and in (`_go_inside`); not seen
        yet, walked as to any map (`_walk_on_after_battles`), the walk ending as soon as the door is SEEN, then in. A walk
        that `done` stopped for its own reason (an item ball, the story moved on, a stop to decide) ends there."""
        nav, manager = self.nav, self.manager
        door = manager.door_of(nav.world, target_map)
        if door is not None and nav.world.current != door[0]:
            # (the graded sweep on 701-720, seed 706: the door known, the walk went straight from OLDALE's centre into the
            # gym through `_go_inside`, past every stop a break owed would have made, and chapter 2 ended at 28.7 %) the way
            # to the gym's TOWN is a walk like any other: its stops hold (an item ball, a break owed); then in by the door
            town = nav.world.maps[door[0]].const
            outcome = yield from self._walk_on_after_battles(
                town, goal.reason, budget,
                lambda look: done(look) or (look.player is not None and look.player.map_const == town))
            if nav.world.current != door[0] or done(self.hands.look()):
                return outcome
        if door is None:
            outcome = yield from self._walk_on_after_battles(
                target_map, goal.reason, budget, lambda look: done(look) or manager.door_of(nav.world, target_map) is not None)
            door = manager.door_of(nav.world, target_map)
            here = nav.world.here()
            if door is None or (here is not None and here.const == target_map) or done(self.hands.look()):
                return outcome
        self.tell(f"[AI-GOALS] {target_map}'s door, by its look, at {door[1]} on {nav.world.maps[door[0]].const}: in")
        entered = yield from self._go_inside(replace(goal, map=target_map, via=door[0], tile=door[1]))
        here = nav.world.here()
        if here is not None and here.const == target_map:
            return f"entered {target_map} by its door, recognised by its look"
        return f"not entered: {entered}"

    def _walk_on_after_battles(self, target_map: str, why: str, budget: int,
                               done: Callable[[Observation], bool]) -> Generator[None, None, str]:
        """(build step 5.1, the verifier's round) `_travel`, and when its budget ran out while BATTLES took `GO_BATTLE_MIN`
        frames or more of it (`_BattleClock`), on again for the frames they took (at most `budget`), at most
        `GO_BATTLE_EXTENSIONS` times: a walk that met long fights is not a walk that failed (the live CH2 arm's two walks to
        PETALBURG CITY met 8 and 13 battles on ROUTE 102 and were put aside as failing)."""
        clock = _BattleClock()
        watchers = getattr(self.hands, "watchers", None)
        if watchers is not None:
            watchers.append(clock)
        try:
            outcome = yield from self._travel(target_map, why, budget, done)
            for _ in range(GO_BATTLE_EXTENSIONS):
                took, clock.frames = clock.frames, 0
                if not outcome.startswith("budget") or took < GO_BATTLE_MIN:
                    break
                more = min(took, budget)
                self.tell(f"[AI-GOALS] the walk to {target_map} ran out of frames, but its battles took {took} of them: it "
                          f"walks on for {more} more")
                outcome = yield from self._travel(target_map, why, more, done)
                outcome = f"{outcome}; walked on {more} frames after its battles"
        finally:
            if watchers is not None and clock in watchers:
                watchers.remove(clock)
        return outcome

    def _travel(self, target_map: str, why: str, budget: int, done: Callable[[Observation], bool]) -> Generator[None, None, str]:
        """To `target_map`: straight there when the way is known or the map is; when it is not, first to the outdoor map
        with the most left to see (`lead_toward`: a person heads out, not into the houses), then on from there."""
        # (chapter 6 NS1) where this walk goes is "its goal" to the travel answer while it walks (`TravelSense`)
        heading, self.heading = self.heading, target_map
        try:
            return (yield from self._travel_on(target_map, why, budget, done))
        finally:
            self.heading = heading

    def _travel_on(self, target_map: str, why: str, budget: int, done: Callable[[Observation], bool]) -> Generator[None, None, str]:
        nav, active = self.nav, self.manager.state.active
        lead = lead_toward(nav.world, target_map)
        if lead is not None:
            # (the chapter-5 search fix K1, 2026-11-13) the lead says why it is the lead (`Lead`): a seasoned player's lead
            # says what it knows (`entry_lead`)
            because = lead.why if isinstance(lead, Lead) else Lead.why
            self.tell(f"[AI-GOALS] {target_map} is somewhere it has not been: first to {lead}, {because}")
            outcome = yield from nav.run(travel_intent(lead, active, budget // 2,
                                                       lambda look: done(look) or (look.player is not None
                                                                                   and look.player.map_const == lead)),
                                         f"{why}: on through {lead}")
            look = self.hands.look()
            if done(look):
                return outcome
        return (yield from nav.run(travel_intent(target_map, active, budget, done), why))

    def _grass_map(self, milestone: Milestone) -> str | None:
        """Where to roam: None to stay (this map has grass of its own: tiles inside it); otherwise the map with grass
        nearest by the known way, the fight's own map first (`grass_target`)."""
        return grass_target(self.nav.world, milestone.maps)[1]  # "out of reach" is never chosen (`next_goal`)

    def _go_inside(self, goal: Goal) -> Generator[None, None, str]:
        """Into the place of `goal` (a heal or a shop): a map it knows (the way to it known), or a door it SAW on the map
        `goal.via`, walked to and into."""
        nav = self.nav
        if goal.via is not None and goal.tile is not None:
            if nav.world.current != goal.via:
                town = nav.world.maps[goal.via].const
                outcome = yield from self._travel(town, f"{goal.reason}: to {town}", GO_FRAMES,
                                                  lambda look: look.player is not None and look.player.map_const == town)
                if nav.world.current != goal.via:
                    return f"could not get back to {town}: {outcome}"
            outcome = yield from enter_door(self.hands, nav, goal.tile, goal.reason)
            if outcome.startswith(DOOR_UNUSABLE):
                # (the round's development sweep: a door nobody could reach stayed the nearest place, and a party in danger
                # tried it again and again, a goal of 20-40 frames each, until the patience ran out) a door it cannot walk
                # into is forgotten: the next decision chooses another place
                kind = self.manager.memory.landmarks.pop((goal.via, goal.tile), None)
                if kind is not None:
                    self.tell(f"[AI-GOALS] the {kind} door it saw at {goal.tile} cannot be walked into ({outcome}): "
                              f"forgotten")
            return outcome
        here = nav.world.here()
        if here is not None and here.const == goal.map:
            return "entered"
        outcome = yield from self._travel(goal.map, f"{goal.reason}: to {goal.map}", GO_FRAMES,
                                          lambda look: look.player is not None and look.player.map_const == goal.map)
        here = nav.world.here()
        return "entered" if here is not None and here.const == goal.map else f"could not get to {goal.map}: {outcome}"

    def _see(self, look_name: str, why: str) -> Generator[None, None, None]:
        """Inside a building, walk in until the one who LOOKS like `look_name` is on screen (the nurse stands at the back
        of a POKéMON CENTER, six rows from its door: past the screen's five). Bounded (`FIND_FRAMES`)."""
        if self.manager.looks_like(self.hands.look(), look_name) is not None:
            return
        yield from self.nav.run(travel_intent(None, self.manager.state.active, FIND_FRAMES,
                                              lambda look: self.manager.looks_like(look, look_name) is not None, stay=True),
                                why)

    def _heal(self, goal: Goal) -> Generator[None, None, str]:
        """To the place it heals at and the nurse (or MOM). On the way a person whose Pokemon is hurt keeps out of the tall
        grass where it can (`HURT_GRASS_COST` per grass tile in the navigator's plans, its own taste restored after):
        measured 2026-10-14 (the development sweep step5dev6, seeds 1-9), every CH1 whiteout was a wild battle on the walk
        home to heal, begun at 2/24 to 5/26 HP, by a personality that walks through grass at no extra cost."""
        nav = self.nav
        own = nav.grass_cost
        nav.grass_cost = max(own, HURT_GRASS_COST)
        try:
            return (yield from self._heal_there(goal))
        finally:
            nav.grass_cost = own

    def _heal_there(self, goal: Goal) -> Generator[None, None, str]:
        nav, hands = self.nav, self.hands
        entered = yield from self._go_inside(goal)
        if entered != "entered":
            return entered
        here = nav.world.here()
        if here is not None and (here.const or "").endswith(CENTER_SUFFIX):
            yield from self._see("nurse", f"{goal.reason}: the nurse is at the counter at the back")
            return (yield from heal_at_center(hands, nav, goal.reason))
        # home: MOM heals (she stands in the ground floor; talking to her heals the party after PROF. BIRCH was rescued)
        mom = self.manager.looks_like(hands.look(), "mom") if "mom" in self.manager.story.looks else None
        if mom is None:
            mom = next((o for o in (hands.look().view.objects if hands.look().view else ()) if o.kind == "npc"), None)
        if mom is None:
            return "no one at home to talk to"
        before = party_share(hands.look()) or 0.0
        outcome = yield from talk_to(hands, nav, mom, f"{goal.reason}: MOM")
        after = party_share(hands.look()) or 0.0
        return "healed" if after >= 0.999 and after > before - 1e-9 else f"talked to MOM ({outcome}); the party at {after:.0%}"

    def _shop(self, goal: Goal, index: int = 0) -> Generator[None, None, str]:
        nav, hands = self.nav, self.hands
        entered = yield from self._go_inside(goal)
        if entered != "entered":
            return entered
        errands = self.manager.state.errands
        yield from self._see("clerk", f"{goal.reason}: the clerk is behind the counter")
        look = hands.look()
        money = look.progress.money if look.progress is not None else 0
        balls = min(errands.balls_buy, max(1, money // BALL_PRICE))
        wants = [("POKé BALL", balls)]
        if money - balls * BALL_PRICE >= POTION_PRICE * errands.potions_buy and errands.potions_buy > 0:
            wants.append(("POTION", errands.potions_buy))
        outcomes = yield from shop_at_mart(hands, nav, wants, goal.reason)
        here = nav.world.here()
        if outcomes and outcomes[0].startswith("POKé BALL") and NOT_FOR_SALE in outcomes[0] and here is not None:
            # (build step 5.1, review #4) the LIST it read had no POKé BALLS: remembered, and this mart is tried again only
            # once the story has moved on (a person comes back later); step 5 knew it by FLAG_ADVENTURE_STARTED
            self.manager.memory.no_balls[here.const] = index
            self.tell(f"[AI-GOALS] no POKé BALLS on {here.const}'s list: it will come back once the story has moved on")
        return "; ".join(outcomes)

    def _detour(self, goal: Goal, milestone: Milestone | None = None) -> Generator[None, None, str]:
        """(build step 5.1, review #1: "an occasional detour that is not the shortest way") A short look at something OFF
        the way on this map before travelling on: one place the explorer would like here (a frontier, grass, someone not
        met: never the way on to the goal, never back, never into a building), chosen on a whim among the about-equal
        ones, walked to within `goal.steps` frames. (Build step 5.1, the verifier's round) it walks TO that place and stands
        there (a `wander` target on its tile, which the walk never makes stale: the chosen frontier was "seen past" after one
        step, and the detour chose it again and again with no frame passing: 11 of the 12 detours of the first round's
        graded CH1 runs ended at once), at least
        `DETOUR_MIN_TILES` tiles away; a place it cannot reach is swapped for another, at most `DETOUR_TRIES` in all.
        (Build step 5.2, the step-5.1 review's finding 3: "detours are cosmetic": "looked at the frontier at (-7, 15)" was
        printed for a place never reached, CH1C and CH1M both chose it, past OLDALE's west exit someone stood in, and
        nothing happened on arrival) the place is one it can WALK to over tiles it KNOWS, nobody standing in the way and
        no place curiosity found blocked on the way (`_known_reach`), never past an edge it knows (`MapMemory.outside`),
        never a blocked place itself; the detour is over when it stands there, when the walk leaves this map, or at its
        budget, and its outcome SAYS which: "reached ..." or "not reached ..."; at a PERSON it chose, it talks to them.
        The place is kept for the play loop's yield (`detour_place`: map key, x, y, kind)."""
        nav, manager, hands = self.nav, self.manager, self.hands
        weights = weights_for(manager.state.active)
        began_on = nav.world.current
        avoid = manager.blocked_on(milestone.id if milestone is not None else None, began_on)
        chosen: list[Target] = []
        kinds: list[str] = []
        whos: list[int | None] = []
        reached: list[bool] = []
        self.detour_place = None

        def detour_choose(navigator: Navigator, look: Observation) -> Target | None:
            if reached or navigator.world.current != began_on:
                return None
            if chosen and not navigator.is_excluded(chosen[-1]) and chosen[-1].tile not in avoid:
                return chosen[-1]  # the same place (a battle met on the way to it)
            if len(chosen) >= DETOUR_TRIES:
                return None
            located = navigator.where(look)
            if located is None:
                return None
            memory, at = located
            # (build step 5.2, step52dev2) the walk plans round the tiles a scene sent the player back from, so the reach does
            walled = getattr(navigator, "scene_walls", None) or {}
            reach = _known_reach(memory, at, frozenset(set(memory.people_now) | set(avoid) | set(walled.get(memory.key, ()))))
            # (build step 5.2, step52dev2: a detour chose the tile BESIDE a place a scene had just turned it back from, the same
            # corner past LITTLEROOT's twin) never a place at or beside a blocked one, nor beside one tried in this detour
            found = [t for t in candidates(navigator, look, weights, None, jitter_on=True) if t.kind in DETOUR_KINDS
                     and not _beside(t.tile, [old.tile for old in chosen])
                     and abs(t.tile[0] - at[0]) + abs(t.tile[1] - at[1]) >= DETOUR_MIN_TILES
                     and t.tile in reach and not _beside(t.tile, avoid) and not memory.outside(t.tile)]
            if not found:
                return None
            place = pick(found, navigator.rng)
            kinds.append(place.kind)
            whos.append(place.who)
            chosen.append(Target("wander", place.tile, f"a detour: a look at the {place.kind} at {place.tile} "
                                                       f"({place.reason})", place.score))
            return chosen[-1]

        turned: list[bool] = []

        def detour_turned_back(look: Observation) -> bool:
            """(build step 5.2, the round's development sweeps: four of the seven detours that did not arrive in step52dev2,
            and both in step52dev3, about 2,200 frames each, met LITTLEROOT's twin twice on the way to a place past her)
            a detour is a look on the way, not a push: the first SCENE that stops the way to its place ends it."""
            if chosen and getattr(nav, "scene_hits", {}).get(f"{nav.world.current}|{chosen[-1].key}"):
                turned.append(True)
                return True
            return False

        intent = Intent(f"a detour ({goal.reason[:40]})", goal.steps, detour_choose,
                        lambda look: bool(reached) or nav.world.current != began_on or detour_turned_back(look),
                        lambda target: reached.append(True))
        outcome = yield from nav.run(intent, goal.reason)
        if not chosen:
            return f"not reached: nothing off the way here that it can walk to ({outcome})"
        tile, kind = chosen[-1].tile, kinds[-1]
        self.detour_place = [began_on, tile[0], tile[1], kind]
        tried = f" ({len(chosen) - 1} place(s) before it could not be reached)" if len(chosen) > 1 else ""
        if not reached:
            why = ("the walk left the map" if nav.world.current != began_on
                   else "a scene stopped the way there" if turned else outcome)
            return f"not reached: the {kind} at {tile} ({why}){tried}"
        said = ""
        if kind == "people" and whos[-1] is not None:
            # (build step 5.2, the review's finding 3: "nothing happens on arrival, not even a talk with the people it
            # chose") a person walks over to someone to TALK to them
            look = hands.look()
            person = next((o for o in (look.view.objects if look.view is not None else ()) if o.kind == "npc"
                           and o.source == "object" and o.local_id == whos[-1]), None)
            if person is None:
                said = "; the person it walked over to is not on screen any more"
            else:
                manager.memory.talked.add(f"{nav.world.current}|{person.local_id}")
                talk = yield from talk_to(hands, nav, person, f"{goal.reason}: hello to the person it walked over to")
                said = f"; {talk}"
        return f"reached the {kind} at {tile} ({outcome}){said}{tried}"

