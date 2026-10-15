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
  * Found by the round's development sweep: a door seen ACROSS a map's edge is not that map's, a door that cannot be walked
    into is forgotten (`DOOR_UNUSABLE`), a heal in danger is tried again at most `DANGER_RETRIES` times in a row, the
    story's own person is no "chat", and a look round while a story goal is put aside lasts only the breather left
    (`ASIDE_LOOK_MIN`).
  * Which personality judged a fight's training done is logged (`fight_prep` `judged_by`), for the graders' bound.
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable, Generator
from dataclasses import dataclass, field, replace

from ai_player.brain.battle import BattleMind, needs_rest
from ai_player.brain.explore import (
    candidates,
    carry_on,
    choose_target,
    looks_like_exit,
    pick,
    pick_on_the_move,
    weights_for,
)
from ai_player.brain.navigator import Intent, Navigator, Target
from ai_player.eyes.observation import Observation, SeenObject
from ai_player.eyes.screens import page_text
from ai_player.hands.pad import Hands
from ai_player.knowledge.story import Milestone, Step, Story
from ai_player.personality import PersonalityState
from ai_player.world.memory import DIRECTIONS, moved
from ai_player.skills.roam_train import roam_train
from ai_player.skills.story import (
    NOT_FOR_SALE,
    enter_door,
    heal_at_center,
    pick_up,
    shop_at_mart,
    talk_to,
    use_thing,
)

__all__ = [
    "AGAIN_MAX",
    "ASIDE",
    "ASIDE_LOOK_MIN",
    "DANGER_RETRIES",
    "DOOR_UNUSABLE",
    "ASK_ROUNDS",
    "BALANCE_MIN_FRAMES",
    "CENTER_LOOK_FRAMES",
    "CENTER_SUFFIX",
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
    "MOM_HEAL_WORDS",
    "NEW_MAP_STOP",
    "OWED_STOP",
    "STORY_KINDS",
    "HURT_GRASS_COST",
    "Goal",
    "GoalManager",
    "GoalRunner",
    "ITEM_STOP",
    "ITEM_TRIES",
    "LOOK_AROUND_FRAMES",
    "MART_SUFFIX",
    "ON_THE_MAP",
    "TRAIN_SESSIONS",
    "battles_lost",
    "heard_page",
    "heard_words",
    "is_gym",
    "keeps_going",
    "lead_toward",
    "marks_of",
    "party_share",
    "quote",
    "roam_numbers",
    "strongest_level",
    "training_rest",
    "travel_intent",
    "world_distance",
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
#: (build step 5.1, the verifier's second round: the live arm CH2T, the Story player in chapter 2, spent 16 % of its goals'
#: frames on errands once the WALLY scene played inside a dropped goal was no longer counted as one) A person keeps a
#: BALANCE: when the share of this session's goal frames spent on errands (its own count, `GoalManager.spent`: needs and
#: curiosity alike, a curiosity goal the story moved on in counted as the story's) falls under its personality's
#: `Errands.balance`, the curiosity draws pass without the dice and, with none due, it looks round where it stands some
#: more (`owed`). Not judged before this many frames of goals in the session (a session's first goals are no proportion).
BALANCE_MIN_FRAMES = 12_000
#: ... and at most this many looks round "some more" on one map in one milestone (the balance is kept on the way, not by
#: wandering one place for ever)
AGAIN_MAX = 2
#: ... and a walk that ARRIVES on another outdoor map while the balance is owed stops there (once a map and milestone),
#: so the next decision may take the break there; its outcome says so
OWED_STOP = "arrived where it takes a break from the story"
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
    #: (build step 5.1, the verifier's second round) this session's goal frames: "story" and "errand" (`spent`, `owed`)
    spent: dict[str, int] = field(default_factory=lambda: {"story": 0, "errand": 0, "curious": 0})
    #: (the same) "map key|milestone id" -> looks round "some more" made there (`AGAIN_MAX`)
    again: dict[str, int] = field(default_factory=dict)
    #: (the same) "map key|milestone id" where a walk stopped because the balance was owed (once each)
    owed_stops: set[str] = field(default_factory=set)
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


#: A map a person sees the NAME of when they walk onto it (a town, a city, a route: the map-name popup), as opposed to an
#: interior: where a person looks for a way on to somewhere they have not been.
OUTDOOR = re.compile(r"^(ROUTE\d+|[A-Z]+_(TOWN|CITY))$")


def world_distance(world, key: str) -> int:
    """How many known links (warps, connections) lie between the current map and map `key` (99 when no way is known)."""
    start = world.current
    if start is None:
        return 99
    seen, frontier = {start}, [(start, 0)]
    while frontier:
        here, depth = frontier.pop(0)
        if here == key:
            return depth
        for kind, link in world.links_from(here):
            if kind == "warp" and not looks_like_exit(world, here, link.get("tile")):
                continue  # a "warp" from a tile that is no way out (a scene's, from the grass) is no way to walk (route_to)
            target = link.get("to") if kind == "warp" else link.get("target")
            if target is not None and target not in seen:
                seen.add(target)
                frontier.append((target, depth + 1))
    return 99


def lead_toward(world, goal_const: str | None) -> str | None:
    """Heading for a map it has NOT been to (`goal_const` unknown to its memory): the outdoor map it HAS been to where the
    most is left to see (`WorldMemory.promise`: frontier, exits not used, roads), routes before towns, nearer first; None
    when the goal is known, or nothing promising is known. A person who is told "ROUTE 103" and has seen only Littleroot
    and part of ROUTE 101 walks on up ROUTE 101, not into the houses."""
    if goal_const is not None and any(memory.const == goal_const for memory in world.maps.values()):
        return None
    if goal_const is not None and not OUTDOOR.match(goal_const):
        # a building's room: found in its own TOWN (the name says which: "PETALBURG GYM" is in PETALBURG CITY), so a person
        # who has been to that town walks there first (measured 2026-10-14, the chapter-2 development run c2b: told of
        # the gym while catching on ROUTE 102, it explored ROUTE 102's grass for two 9000-frame budgets); found inside, by
        # its stairs, when the player is in that town or one of its buildings already (None)
        here = world.here()
        towns = [m.const for m in world.maps.values() if m.const and OUTDOOR.match(m.const) and m.visits
                 and goal_const.startswith(f"{m.const}_")]
        town = max(towns, key=len) if towns else None
        there = here is not None and (here.const == town or str(here.const or "").startswith(f"{town}_"))
        return town if town is not None and not there else None
    here = world.here()
    if here is not None and OUTDOOR.match(here.const or "") and world.promise(here.key) > 0:
        return None  # out in the open with something left to see here: look on from here
    options = []
    for key, memory in world.maps.items():
        const = memory.const or ""
        if not OUTDOOR.match(const) or not memory.visits or key == world.current:
            continue
        promise = world.promise(key)
        if promise <= 0:
            continue
        options.append((world_distance(world, key), -(1 if const.startswith("ROUTE") else 0), -promise, const))
    return min(options)[3] if options else None


#: The places that keep the player ON the map it searches (`travel_intent(stay=True)`): no road, exit or way back off it.
ON_THE_MAP = ("frontier", "grass", "people", "wander")


def keeps_going(world, target: Target, goal_map: str | None, stay: bool = False) -> bool:
    """`travel_intent`'s rule: a way BACK into a building already visited (an interior, not a town or a route, and not
    the goal itself) is no option for someone going somewhere; every other place is. `stay`: someone SEARCHING this map
    (for the rival on ROUTE 103, the nurse at the back of the centre) keeps to places on it."""
    if stay:
        return target.kind in ON_THE_MAP
    if target.kind != "back" or target.exit is None:
        return True
    link = world.link_of(world.current, target.exit)
    inside = world.maps.get(link.get("to")) if link else None
    return inside is None or bool(OUTDOOR.match(inside.const or "")) or inside.const == goal_map


def travel_intent(goal_map: str | None, personality: str, budget: int, done: Callable[[Observation], bool],
                  stay: bool = False) -> Intent:
    """`brain/explore.py` explore_intent's taste and walk, for a person who is GOING somewhere: the ways BACK into a building
    already visited (a house, the lab: an interior, not a town or a route) are no option (measured 2026-10-14, the play
    brain's first chapter-1 run: told "ROUTE 103" in the rival's house, the explorer went up and down its stairs for the
    unseen corners of the bedroom until its ping-pong rule stopped it, eight times). Everything else is the explorer's own
    (`candidates`, `pick`, `pick_on_the_move`, `carry_on`); with nothing left it falls back to `choose_target` (never
    idle)."""
    weights = weights_for(personality)

    def goal(memory, key: str) -> bool:
        return goal_map is not None and memory is not None and memory.const == goal_map

    def choose(nav: Navigator, look: Observation) -> Target | None:
        moving = nav.choosing_on_the_move
        found = [t for t in candidates(nav, look, weights, goal if goal_map else None, jitter_on=not moving)
                 if keeps_going(nav.world, t, goal_map, stay)]
        located = nav.where(look)
        if not found or located is None:
            return choose_target(nav, look, weights, goal if goal_map else None)
        if moving:
            return pick_on_the_move(found, located[1], nav.heading())
        return pick(found, nav.rng)

    def carry(nav: Navigator, look: Observation, old: Target) -> Target | None:
        return carry_on(nav, look, weights, old, goal if goal_map else None)

    return Intent(f"travel to {goal_map}" if goal_map else "look around", budget, choose, done, carry_on=carry)


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
        errand = goal.kind in ERRAND_KINDS and not (story_moved and goal.kind in CURIOSITY_KINDS)
        self.memory.spent["errand" if errand else "story"] += frames
        if errand and goal.kind in CURIOSITY_KINDS:
            self.memory.spent["curious"] = self.memory.spent.get("curious", 0) + frames

    def owed(self) -> str | None:
        """Why a person would take a break from the story now, or None: this session's time (its goals and the scenes
        between them), `BALANCE_MIN_FRAMES` at least, went to errands less than the active personality's
        `Errands.balance`, or to CURIOSITY (the errands no need asks for) less than its `Errands.curious_min` (the round's
        development sweep: chapter 1's training kept the errands' share high while the curiosity stayed at 4 %); never
        under the beeline control."""
        if self.errands_off:
            return None
        story, errand = self.memory.spent["story"], self.memory.spent["errand"]
        curious = self.memory.spent.get("curious", 0)
        total = story + errand
        errands = self.state.errands
        if total < BALANCE_MIN_FRAMES:
            return None
        if errand < errands.balance * total:
            return (f"{errand / total:.0%} of this session's {total} goal frames went to errands, under the "
                    f"{self.state.active}'s {errands.balance:.0%}")
        if curious < errands.curious_min * total:
            return (f"{curious / total:.0%} of this session's {total} goal frames went to curiosity, under the "
                    f"{self.state.active}'s {errands.curious_min:.0%}")
        return None

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
            return heard_words(heard, step.told)
        return self.been_to(world, step.map)

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
        center = self.story.looks.get("pokemon_center_door")
        mart = self.story.looks.get("mart_door")
        gym = self.story.looks.get("gym_door")
        for row in look.view.rows:
            for tile in row:
                # a door seen ACROSS a map's edge belongs to the next map (its coordinates here are past this map's): it is
                # remembered when the AI stands on that map and sees it again
                if not tile.door or tile.x < 0 or tile.y < 0:
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
        # the party in real danger (a Pokemon fainted, the strongest under a third: `needs_rest`): healing is then the only
        # sensible errand, so a heal put aside after failing (`FAIL_LIMIT`) is tried again at once (the development sweep
        # step5dev7, seed 3: two walks home ran out, the heal was put aside, and the AI trained, then walked to the rival, at
        # 2/26 HP, and whited out)
        must_rest = has_party and (fainted or needs_rest(look.party) is not None)
        hurt = has_party and share is not None and (must_rest or share < errands.heal_below)
        # 1. HEAL
        if has_party and share is not None:
            # ready for the fight: trained (`prep` ready), or, under the no-training FAULT, at once (the fault removes the
            # TRAINING only; healing before the fight stays, so the fault arm measures training alone: the step-5
            # verifier, 2026-10-14, found it removed both)
            ready = self.train_off or bool(self.prep(milestone).get("ready"))
            before_fight = fight_next and share < HEAL_BEFORE_FIGHT and ready
            if hurt or before_fight:
                where = self.heal_place(world)
                why = ("a Pokemon has fainted" if fainted else f"the party is at {share:.0%} of its HP"
                       + (f" (under {errands.heal_below:.0%})" if share < errands.heal_below else "")
                       + ("; a known fight is next" if before_fight else ""))
                town = here_const if here_const and OUTDOOR.match(here_const) and not here_const.startswith("ROUTE") \
                    else None
                if (where is not None and town is not None and self._place_key(world, where) not in (None, world.current)
                        and world.current not in self.memory.center_looked
                        # (the graded sweep on 701-720, seed 706: a look round of PETALBURG did not pass its centre, and
                        # the AI took the town for one with none) only a town SEEN ALL OF (nothing left to see there) and
                        # looked round has no centre to look for
                        and not (world.current in self.memory.explored and world.promise(world.current) <= 0)):
                    # (build step 5.1, the verifier's second round: CH2T, hurt on arriving in PETALBURG CITY, walked back
                    # to OLDALE's centre, the one it knew) in a TOWN whose own centre it has not seen, a person looks for
                    # it here first (a town has one), once; then the nearest it knows
                    self.memory.center_looked.add(world.current)
                    return Goal("find_center", f"{why}: it has not seen {town}'s POKéMON CENTER yet; a town has one, so it "
                                               f"looks here before walking back to {where[3]}", milestone.id, map=town,
                                via=world.current, key=f"find_center:{world.current}")
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
        # 2. SHOP: by what the mart's LIST showed (build step 5.1, review #4: step 5 shopped once FLAG_ADVENTURE_STARTED was
        # set, a flag no player sees): a mart whose list had no POKé BALLS is tried again only once the story moved on
        balls = look.bag.ball_total if look.bag is not None else 0
        money = look.progress.money if look.progress is not None else 0
        if has_party and balls < errands.balls_low and money >= BALL_PRICE * min(errands.balls_buy, 5):
            where = self._mart_place(world, index)
            if where is not None and self._allowed(f"shop:{where[0]}"):
                return Goal("shop", f"{balls} POKé BALLS left (fewer than {errands.balls_low}) and {money} money: "
                                    f"{where[3]}", milestone.id, map=where[0], via=where[1], tile=where[2],
                            key=f"shop:{where[0]}")
        # 3. ITEM: a ball on screen, or one it saw earlier on this map (build step 5.1: before the party too, so the rival's
        # POKé BALL on the floor of the rival's room is found by curiosity, review #3, not by a scripted step; and before
        # training: a training roam STOPS for a ball in view, so with training first each session ended at once)
        ball = self._item_ball(look, world)
        if ball is not None:
            return Goal("pick_up", f"an item ball on the ground at {(ball.x, ball.y)}: a person picks it up", milestone.id,
                        target=ball, key=f"item:{world.current}|{ball.x},{ball.y}")
        remembered = self._remembered_ball(look, world)
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
        # (build step 5.1, the verifier's second round) the BALANCE: a break from the story owed (`owed`), never while hurt
        owed = self.owed() if not hurt else None
        if self.may_look_around(look, world, step):
            self.memory.looked.add(world.current)
            draw = self.rng.random()
            if draw < errands.look_around or self.memory.passed_new >= LOOK_DEBT or owed:
                why = (f"draw {draw:.2f} < the {self.state.active}'s {errands.look_around}" if draw < errands.look_around
                       else f"it has gone past {self.memory.passed_new} new places in a row without a look: this time it "
                            f"looks (draw {draw:.2f})" if self.memory.passed_new >= LOOK_DEBT
                       else f"draw {draw:.2f}, but {owed}: a break from the story")
                self.memory.passed_new = 0
                self.memory.explored.add(world.current)
                return Goal("explore", f"a new place, {here_const}: a person looks around it ({why}) before going on",
                            milestone.id, steps=errands.look_frames, key=f"explore:{world.current}")
            self.memory.passed_new += 1
            self._say(f"[AI-GOALS] a new place, {here_const}: it goes on without looking round (draw {draw:.2f} >= the "
                      f"{self.state.active}'s {errands.look_around}; {self.memory.passed_new} in a row)")
        # 5. TRAIN before a fight it KNOWS of (never while hurt: a person heals first, and a roam begun hurt stops at its first
        # battle, `training_rest`, burning a session of `TRAIN_SESSIONS` for nothing: step5dev7, seed 3, six in a row)
        if fight_next and not self.train_off and not hurt:
            prep = self.prep(milestone)
            target = self.training_target(levels)
            level = strongest_level(look)
            short = level < target or prep["steps"] < errands.train_min_steps
            if short and prep["sessions"] < TRAIN_SESSIONS and self._allowed("train"):
                why = (f"the next fight ({milestone.title}) has levels {list(levels)} ({levels_from}): its strongest "
                       f"Pokemon is L{level}, the {self.state.active}'s target L{target}; {prep['steps']} of at least "
                       f"{errands.train_min_steps} training steps roamed in {prep['sessions']} of at most "
                       f"{TRAIN_SESSIONS} sessions")
                return Goal("train", why, milestone.id, steps=errands.train_session, key="train")
            if not prep["ready"]:
                prep["ready"] = True
                prep["why_ready"] = ("trained" if not short else f"{TRAIN_SESSIONS} sessions roamed: no endless grind"
                                     if prep["sessions"] >= TRAIN_SESSIONS else "training put aside for a while")
                # (build step 5.1, the verifier's second round: "which personality judged the run 'trained' is not
                # logged") whose rule said so, and its minimum: the graders take the run's bound from it
                prep["judged_by"] = self.state.active
                prep["min_steps"] = errands.train_min_steps
        # 6. CATCH: balls in hand, grass not walked on this map
        if (has_party and balls > 0 and here is not None and here.grass() and world.current not in self.memory.catch_maps
                and not fight_next and not self.errands_off):
            self.memory.catch_maps.add(world.current)
            fresh = [xy for xy in here.grass() if not here.visits.get(xy)]
            draw = self.rng.random()
            # (the round's development sweep step51wdev1: a Story player went through chapter 2 with its first five POKé
            # BALLS and caught nothing) a POKéDEX that holds only its first Pokemon and balls just in hand: a person tries
            # them, whatever its taste (PROF. BIRCH's "fill the POKéDEX", the rival's "catch POKéMON with these")
            first = look.progress is not None and look.progress.dex_owned <= 1
            if fresh and (draw < errands.catch_seek or owed or first) and self._allowed(f"catch:{world.current}"):
                why = (f"draw {draw:.2f} < the {self.state.active}'s {errands.catch_seek}" if draw < errands.catch_seek
                       else f"draw {draw:.2f}, but {owed}: a break from the story" if owed
                       else f"draw {draw:.2f}, but its POKéDEX holds only its first Pokemon and it has its first POKé "
                            f"BALLS: it tries them")
                return Goal("catch", f"{len(fresh)} grass tiles not walked on {here_const} and {balls} POKé BALLS ({why}): "
                                     f"looking for POKéMON it has not caught", milestone.id, steps=errands.catch_roam_steps,
                            key=f"catch:{world.current}")
        # 7. CHAT with someone near (never the person the story's own step names: the round's development sweep chose DAD as a
        # "chat", seeds 37 and 39, a story-owned goal under an errand's name; the story's goal talks to him)
        own = self.story.looks.get(step.look) if step is not None and step.look else None
        chat = self._chat_person(look, world, owed, own.gfx if own is not None else ()) if not self.errands_off else None
        if chat is not None:
            person, why = chat
            return Goal("chat", f"someone stands near at {(person.x, person.y)}: a person says hello now and then{why}",
                        milestone.id, target=person, key=f"chat:{world.current}|{person.local_id}")
        # 7b. (build step 5.1, the verifier's second round) the BALANCE owed and no draw due here: it looks round where it
        # stands some more (an outdoor map, not where the story's own next thing is told and here; `AGAIN_MAX` a map and
        # milestone)
        again = f"{world.current}|{milestone.id}"
        if (owed and here is not None and OUTDOOR.match(here_const or "") and not must_rest and step is not None
                and step.do != "intro" and not self._story_here(step, world)
                and self.memory.again.get(again, 0) < AGAIN_MAX):
            self.memory.again[again] = self.memory.again.get(again, 0) + 1
            self.memory.explored.add(world.current)
            return Goal("explore", f"{here_const} some more ({owed}): a break from the story, looking round where it is "
                                   f"({self.memory.again[again]} of at most {AGAIN_MAX} here)", milestone.id,
                        steps=errands.look_frames, key=f"explore:{world.current}:again")
        # 8. STORY (and now and then a DETOUR off the way while travelling)
        goal = self._story_goal(look, world, milestone, step)
        if (goal.kind == "go" and goal.map is not None and not self.errands_off and here is not None
                and OUTDOOR.match(here_const or "") and f"{world.current}|{milestone.id}" not in self.memory.detoured
                and goal.key.startswith("go:") and not must_rest):
            self.memory.detoured.add(f"{world.current}|{milestone.id}")
            draw = self.rng.random()
            if draw < errands.detour or owed:
                why = (f"draw {draw:.2f} < the {self.state.active}'s {errands.detour}" if draw < errands.detour
                       else f"draw {draw:.2f}, but {owed}: a break from the story")
                return Goal("detour", f"on the way to {goal.map}: a look at something off the way on {here_const} ({why})",
                            milestone.id, steps=errands.detour_frames, key=f"detour:{world.current}")
            self._say(f"[AI-GOALS] on the way to {goal.map}: no detour on {here_const} this time (draw {draw:.2f} >= the "
                      f"{self.state.active}'s {errands.detour})")
        return goal

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
                # a person asks where they know people (the rival's house, visited for the rival's milestone)
                if self.step_known(step, world.heard, world):
                    return Goal("go", f"{milestone.title}: to ask at {step.map} where to go ({self._told(step, world)})",
                                milestone.id, map=step.map, key=f"go:{step.map}")
                return Goal("go", f"{milestone.title}: who would know where to go? It has not been to {step.map}: "
                                  f"exploring", milestone.id, map=None, key=f"go:?{milestone.id}",
                            words=None if self.hints_off else step.words)
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

    def _chat_person(self, look: Observation, world, owed: str | None = None,
                     story_gfx: tuple[int, ...] = ()) -> tuple[SeenObject, str] | None:
        """Someone near to say hello to, and what the reason adds: one draw a person against `chat`; (build step 5.1, the
        verifier's second round) a break from the story owed passes the draw (`owed`); never someone who LOOKS like the
        person the story's own step names (`story_gfx`)."""
        for person in self._people(look):
            key = f"{world.current}|{person.local_id}"
            if (key in self.memory.talked or key in self.memory.chat_drawn or abs(person.dx) + abs(person.dy) > 4
                    or person.graphics_id in story_gfx):
                continue
            self.memory.chat_drawn.add(key)
            draw = self.rng.random()
            if draw < self.state.errands.chat:
                return person, ""
            if owed:
                return person, f" (draw {draw:.2f}, but {owed}: a break from the story)"
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

    def _nearest_place(self, world, suffix: str, landmark: str, name: str, keep=lambda const: True) -> tuple | None:
        """(build step 5.1, the verifier's second round: CH2T walked back to OLDALE's centre and mart, the ones it had been
        IN, past PETALBURG's, whose doors it had seen) The NEAREST place of a kind by the known way (`world_distance`): one
        it has been in (`suffix`) or one whose door it has SEEN (`landmark`), the one it has been in on a tie; `keep`
        filters by the interior's map constant. Step 5 took any place it had been in before any door it had seen."""
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
        return min(options, key=lambda option: option[:3])[3] if options else None

    def _place_key(self, world, where: tuple) -> str | None:
        """The map key of the town a heal or shop place (`heal_place`, `_mart_place`) is entered from: its door's map, or
        the town a known interior's warp leads from; None when it is not known (home: the player's house)."""
        if where[1] is not None:
            return where[1]
        return next((source for const, source in self._known_interiors(world, CENTER_SUFFIX)
                     + self._known_interiors(world, MART_SUFFIX) if const == where[0]), None)

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

    def heal_place(self, world) -> tuple | None:
        """Where it would heal: (the map to be in, the map key of a door seen but never used or None, that door or None,
        how it knows): the NEAREST centre it has been in or whose door it has seen (`_nearest_place`; build step 5.1);
        home, once it KNOWS MOM heals (`home_heals`), when no centre is known."""
        here = world.here()
        if here is not None and (here.const or "").endswith(CENTER_SUFFIX):
            return here.const, None, None, "in a POKéMON CENTER: the nurse"
        nearest = self._nearest_place(world, CENTER_SUFFIX, "pokemon_center", "POKéMON CENTER")
        if nearest is not None:
            return nearest
        why = self.home_heals(world)
        if why is not None:
            home = self.story.resolve("<player_house_1f>")
            if any(memory.const == home for memory in world.maps.values()):
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
        return self._nearest_place(world, MART_SUFFIX, "mart", "MART", keep=stocked)

    # ------------------------------------------------------------------ bookkeeping
    def prep(self, milestone: Milestone) -> dict:
        return self.memory.fight_prep.setdefault(milestone.id, {"steps": 0, "sessions": 0, "wild": 0, "won": 0,
                                                                "rests": 0, "ready": False})

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

    def pursue(self, goal: Goal, milestone: Milestone, index: int, current: Callable[[Observation], int]) -> Generator[None, None, tuple[bool, str]]:
        """`_pursue` the goal; (build step 5.1) a person whose Pokemon is HURT keeps out of the tall grass on ANY walk, not
        only the walk to heal (`HURT_GRASS_COST`; never while training or catching, which ARE the grass), its own taste
        restored after."""
        nav = self.nav
        own = getattr(nav, "grass_cost", None)
        hurt = (own is not None and goal.kind not in ("train", "catch", "heal")
                and self.manager.hurt(self.hands.look()))
        if hurt:
            nav.grass_cost = max(own, HURT_GRASS_COST)
        # (build step 5.1) the tiles a scene sent the player back from, carried from goal to goal within this milestone: a
        # person told twice by LITTLEROOT's twin that it is dangerous without a Pokemon does not try her road with every new
        # errand (measured 2026-10-14, the development sweep step51dev5, seeds 2, 3 and 9: after looking round LITTLEROOT the
        # AI's walks to the rival's house chose the frontier past the twin, met her twice per walk, and ran out its patience)
        walls = self.manager.memory.scene_walls.setdefault(milestone.id, {}) if hasattr(nav, "carried_scene_walls") else None
        if walls is not None:
            nav.carried_scene_walls = walls
        try:
            return (yield from self._pursue(goal, milestone, index, current))
        finally:
            if hurt:
                nav.grass_cost = own
            if walls is not None:
                for key, tiles in (getattr(nav, "scene_walls", None) or {}).items():
                    walls.setdefault(key, set()).update(tiles)
                nav.carried_scene_walls = None

    def _pursue(self, goal: Goal, milestone: Milestone, index: int, current: Callable[[Observation], int]) -> Generator[None, None, tuple[bool, str]]:
        hands, nav, manager = self.hands, self.nav, self.manager
        moved_on = lambda look: current(look) != index  # noqa: E731 - the milestone changed: the story moved on
        # a battle the STORY starts (PROF. BIRCH's bag, a talk) is fought, not run from (measured 2026-10-14: the play brain's
        # first chapter-1 run tried RUN in PROF. BIRCH's battle, which the game refuses); training and catching fight too
        self.mind.purpose = "train" if goal.kind in ("train", "catch", "use", "talk", "follow") else "travel"
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

            def done(look: Observation) -> bool:
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
                    # (build step 5.1, the verifier's second round) the BALANCE owed: a walk that ARRIVES on another outdoor
                    # map stops there once a milestone, so the next decision may take its break from the story there
                    stop = f"{nav.world.current}|{milestone.id}"
                    if (nav.world.current != began_on and stop not in manager.memory.owed_stops and not manager.hurt(look)
                            and manager.owed()):
                        manager.memory.owed_stops.add(stop)
                        arrived.append(f"{OWED_STOP}: {player.map_const} ({manager.owed()})")
                        return True
                return look_for is not None and manager.looks_like(look, look_for) is not None

            budget = (GO_FRAMES if goal.kind == "go" else FIND_FRAMES if goal.kind == "find"
                      else goal.steps if goal.kind == "explore" else goal.steps or LOOK_AROUND_FRAMES)
            if goal.kind == "go" and is_gym(target_map):
                # (build step 5.1, the verifier's second round) a GYM is RECOGNISED by its door's look: walked into once seen
                outcome = yield from self._to_building(goal, target_map, budget, done)
                if arrived:
                    outcome = f"{outcome}; {arrived[0]}"
                return outcome.startswith(("done", "entered")), outcome
            if goal.kind == "go" and target_map is not None:
                outcome = yield from self._walk_on_after_battles(target_map, goal.reason, budget, done)
            else:
                # looking for someone on THIS map keeps to it (a person searching ROUTE 103 for the rival does not go back
                # to OLDALE), and so does looking around a new place (build step 5.1); looking around for what comes next
                # may go anywhere
                outcome = yield from nav.run(travel_intent(None, manager.state.active, budget, done,
                                                           stay=goal.kind in ("find", "explore")), goal.reason)
            if arrived:
                outcome = f"{outcome}; {arrived[0]}"
            if goal.kind == "explore":
                # looking around is its own end: the time spent IS the errand (a budget that ran out is done)
                return outcome.startswith(("done", "budget")), outcome
            return outcome.startswith("done"), outcome
        if goal.kind == "detour":
            outcome = yield from self._detour(goal)
            return outcome.startswith(("done", "budget")), outcome
        if goal.kind == "find_center" and goal.via is not None:
            # (build step 5.1, the verifier's second round) THIS town's own centre: looked for here, keeping to the town,
            # until its door is seen (the next decision heals at the nearest place it knows: that door, now)
            outcome = yield from nav.run(travel_intent(None, manager.state.active, CENTER_LOOK_FRAMES,
                                                       lambda look: moved_on(look) or manager.center_seen_on(goal.via),
                                                       stay=True), goal.reason)
            seen = manager.center_seen_on(goal.via)
            return seen, outcome + (f"; its door seen on {goal.map}" if seen else f"; no POKéMON CENTER seen on {goal.map}")
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
            if goal.kind == "use":
                outcome = yield from use_thing(hands, nav, goal.target, goal.reason)
            else:
                outcome = yield from talk_to(hands, nav, goal.target, goal.reason)
            self._saw_mom_heal(goal.target, before)
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
        if goal.kind in ("train", "catch"):
            where = self._grass_map(milestone)
            if where is not None:
                went = yield from self._travel(where, f"{goal.reason}: to the grass of {where}", GO_FRAMES,
                                               lambda look: moved_on(look) or (look.player is not None
                                                                                and look.player.map_const == where))
                if nav.world.here() is None or nav.world.here().const != where:
                    return False, f"could not get to the grass of {where}: {went}"
            self.roam_hooks()
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
            return ("roamed" in outcome or "rest:" in outcome or ITEM_STOP in outcome), outcome
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

    def roam_hooks(self) -> None:
        """What a TRAINING or CATCHING roam asks (set for the roam only, `clear_roam_hooks` after): after every battle, a
        reason to stop and heal (`training_rest`: under the personality's `heal_below`; the navigator asks it with no battle
        limit set: until the step-5 verifier's round of 2026-10-14 it asked only WITH one, so the rule never fired and a run
        roamed on at 22 % HP); on every free look, an item ball come into view (a person walks over to it, then roams on)."""
        nav, manager = self.nav, self.manager
        heal_below, active = manager.state.errands.heal_below, manager.state.active
        nav.battle_limit = None
        nav.battle_rest = lambda look: training_rest(look, heal_below, active)
        nav.roam_stop = lambda look: (ITEM_STOP if look.party and manager.item_ball_in_view(look, nav.world) is not None
                                      else None)

    def clear_roam_hooks(self) -> None:
        self.nav.battle_rest = None
        self.nav.roam_stop = None

    # ------------------------------------------------------------------ going somewhere
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
        nav, active = self.nav, self.manager.state.active
        lead = lead_toward(nav.world, target_map)
        if lead is not None:
            self.tell(f"[AI-GOALS] {target_map} is somewhere it has not been: first to {lead}, where the most is left to see")
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
        nearest by the known way, the fight's own map first."""
        world = self.nav.world
        here = world.here()

        def inside_grass(memory) -> list:
            return [xy for xy in memory.grass() if xy[0] >= 0 and xy[1] >= 0 and not memory.outside(xy)]

        if here is not None and inside_grass(here):
            return None
        options = []
        for key, memory in world.maps.items():
            if memory.visits and inside_grass(memory) and memory.const:
                first = 0 if memory.const in milestone.maps else 1
                options.append((world_distance(world, key), first, memory.const))
        return min(options)[2] if options else None

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

    def _detour(self, goal: Goal) -> Generator[None, None, str]:
        """(build step 5.1, review #1: "an occasional detour that is not the shortest way") A short look at something OFF
        the way on this map before travelling on: one place the explorer would like here (a frontier, grass, someone not
        met: never the way on to the goal, never back, never into a building), chosen on a whim among the about-equal
        ones, walked to within `goal.steps` frames. (Build step 5.1, the verifier's round) it walks TO that place and stands
        there (a `wander` target on its tile, which the walk never makes stale: the chosen frontier was "seen past" after one
        step, and the detour chose it again and again with no frame passing: 11 of the 12 detours of the first round's
        graded CH1 runs ended at once), at least
        `DETOUR_MIN_TILES` tiles away; a place it cannot reach is swapped for another, at most `DETOUR_TRIES` in all."""
        nav, manager = self.nav, self.manager
        weights = weights_for(manager.state.active)
        chosen: list[Target] = []
        kinds: list[str] = []
        reached: list[bool] = []

        def choose(navigator: Navigator, look: Observation) -> Target | None:
            if reached:
                return None
            if chosen and not navigator.is_excluded(chosen[-1]):
                return chosen[-1]  # the same place (a scene or a battle met on the way to it)
            if len(chosen) >= DETOUR_TRIES:
                return None
            located = navigator.where(look)
            at = located[1] if located is not None else None
            found = [t for t in candidates(navigator, look, weights, None, jitter_on=True) if t.kind in DETOUR_KINDS
                     and all(t.tile != old.tile for old in chosen)
                     and (at is None or abs(t.tile[0] - at[0]) + abs(t.tile[1] - at[1]) >= DETOUR_MIN_TILES)]
            if not found:
                return None
            place = pick(found, navigator.rng)
            kinds.append(place.kind)
            chosen.append(Target("wander", place.tile, f"a detour: a look at the {place.kind} at {place.tile} "
                                                       f"({place.reason})", place.score))
            return chosen[-1]

        intent = Intent(f"a detour ({goal.reason[:40]})", goal.steps, choose, lambda look: bool(reached),
                        lambda target: reached.append(True))
        outcome = yield from nav.run(intent, goal.reason)
        if not chosen:
            return f"nothing off the way to look at here: {outcome}"
        return f"{outcome}; looked at the {kinds[-1]} at {chosen[-1].tile}" + (
            f" ({len(chosen) - 1} place(s) before it could not be reached)" if len(chosen) > 1 else "")

