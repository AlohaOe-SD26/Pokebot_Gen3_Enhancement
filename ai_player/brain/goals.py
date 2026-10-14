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
            yet and PROF. BIRCH rescued, go home: MOM heals (`data/scripts/players_house.inc` PlayersHouse_1F_EventScript_
            MomHealsParty); on the way it keeps out of the tall grass where it can (`HURT_GRASS_COST`);
  2. SHOP   once FLAG_ADVENTURE_STARTED (the Oldale Mart sells POKé BALLS only after it, design draft §10.9), POKé BALLS
            fewer than `balls_low` and the money for them: the MART it knows (in it, or its door seen), `balls_buy` balls
            (and a few POTIONS);
  3. TRAIN  a FIGHT with known levels is next (the milestone's `fight`: the rival's L5, ROXANNE's 12-15) and the strongest
            Pokemon is under its level + `train_margin`, or the AI has roamed fewer than `train_min_steps` training steps
            since this milestone began: roam the grass (`skills/roam_train.py`, fighting what comes: purpose "train");
            Trainer most, Story least, never straight in (CLAIM pre-registered by `gates/live_step5.py`: steps and battles
            BEFORE the rival);
  4. ITEM   an item ball SEEN on this map, not tried yet: walk up to it and pick it up (pillar 4);
  5. CATCH  POKé BALLS in the bag and grass on this map not walked yet: by a seeded draw against the personality's
            `catch_seek` (Catcher most), roam it to meet new species (the battle decider catches a species the POKéDEX lacks
            by its temperament: `brain/battle.py` catch_new);
  6. CHAT   someone not talked to stands near: by a draw against `chat` (Trainer most), walk up and talk (people tell
            things: the hints come from them);
  7. STORY  the current milestone's next STEP (`knowledge/story.py` Step): `go` to its map, `use` / `talk` to what LOOKS
            like what it names on that map, `ask` the people of a map until its words are heard, `follow` a scene;
  8. LOOK AROUND  nothing else: explore with the personality's taste (never idle).
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
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable, Generator
from dataclasses import dataclass, field

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
    enter_door,
    heal_at_center,
    pick_up,
    shop_at_mart,
    talk_to,
    use_thing,
)

__all__ = [
    "ASK_ROUNDS",
    "CENTER_SUFFIX",
    "FAIL_LIMIT",
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
    plays; `rng` its own seeded stream (`<seed>:goals`); `hints_off` / `train_off` the step-5 FAULT switches."""

    def __init__(self, story: Story, state: PersonalityState, rng: random.Random, hints_off: bool = False,
                 train_off: bool = False) -> None:
        self.story = story
        self.state = state
        self.rng = rng
        self.hints_off = hints_off
        self.train_off = train_off
        self.memory = _Memory()

    # ------------------------------------------------------------------ the story
    def milestone(self, look: Observation, visited: Callable[[str], bool]) -> tuple[int, Milestone | None]:
        """The current milestone: the first not proven by the marks; a WAYPOINT (a map no save flag records) counts as
        passed once the AI has stood on that map (`visited`)."""
        marks = marks_of(look) or {}
        for number, milestone in enumerate(self.story.milestones):
            if milestone.done(marks) is True:
                continue
            if milestone.waypoint is not None and visited(milestone.waypoint):
                continue
            return number, milestone
        return len(self.story.milestones), None

    def hint_known(self, milestone: Milestone, heard: set[str], world=None, place: str | None = None) -> bool:
        """May the AI head for the milestone's map `place`? Only once it has READ the words that name it; a hint with no
        words names nothing it was told, so only a place it has BEEN to (its own memory: `world`) is headed for."""
        if self.hints_off:
            return False
        if milestone.hint_words:
            return heard_words(heard, milestone.hint_words)
        place = place or milestone.hint_map
        return (world is not None and place is not None
                and any(memory.const == place and memory.visits for memory in world.maps.values()))

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
        if look.view is None or look.player is None or look.player.settling:
            return
        key = f"{look.player.map_group}:{look.player.map_number}"
        center = self.story.looks.get("pokemon_center_door")
        mart = self.story.looks.get("mart_door")
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
        here = world.here()
        here_const = here.const if here is not None else None
        errands = self.state.errands
        marks = marks_of(look) or {}
        has_party = bool([m for m in look.party or () if not m.is_egg])
        step = self.story_step(look, world, milestone)
        fight_next = bool(milestone.fight_levels) and has_party and step is not None and step.do in ("go", "talk")
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
                where = self._heal_place(world, marks)
                why = ("a Pokemon has fainted" if fainted else f"the party is at {share:.0%} of its HP"
                       + (f" (under {errands.heal_below:.0%})" if share < errands.heal_below else "")
                       + ("; a known fight is next" if before_fight else ""))
                allowed = self._allowed(f"heal:{where[0]}") if where is not None else False
                if where is not None and (allowed or must_rest):
                    again = "" if allowed else " (put aside after failing, but the party is in danger: again)"
                    return Goal("heal", f"{why}: {where[3]}{again}", milestone.id, map=where[0], via=where[1], tile=where[2],
                                key=f"heal:{where[0]}")
        # 2. SHOP
        balls = look.bag.ball_total if look.bag is not None else 0
        money = look.progress.money if look.progress is not None else 0
        if (has_party and marks.get("ADVENTURE_STARTED") and balls < errands.balls_low
                and money >= BALL_PRICE * min(errands.balls_buy, 5)):
            where = self._mart_place(world)
            if where is not None and self._allowed(f"shop:{where[0]}"):
                return Goal("shop", f"{balls} POKé BALLS left (fewer than {errands.balls_low}) and {money} money: "
                                    f"{where[3]}", milestone.id, map=where[0], via=where[1], tile=where[2],
                            key=f"shop:{where[0]}")
        # 3. TRAIN before a known fight (never while hurt: a person heals first, and a roam begun hurt stops at its first
        # battle, `training_rest`, burning a session of `TRAIN_SESSIONS` for nothing: step5dev7, seed 3, six in a row)
        if fight_next and not self.train_off and not hurt:
            prep = self.prep(milestone)
            target = max(milestone.fight_levels) + errands.train_margin
            level = strongest_level(look)
            short = level < target or prep["steps"] < errands.train_min_steps
            if short and prep["sessions"] < TRAIN_SESSIONS and self._allowed("train"):
                why = (f"the next fight ({milestone.title}) has levels {list(milestone.fight_levels)}: its strongest "
                       f"Pokemon is L{level}, the {self.state.active}'s target L{target}; {prep['steps']} of at least "
                       f"{errands.train_min_steps} training steps roamed in {prep['sessions']} of at most "
                       f"{TRAIN_SESSIONS} sessions")
                return Goal("train", why, milestone.id, steps=errands.train_session, key="train")
            if not prep["ready"]:
                prep["ready"] = True
                prep["why_ready"] = ("trained" if not short else f"{TRAIN_SESSIONS} sessions roamed: no endless grind"
                                     if prep["sessions"] >= TRAIN_SESSIONS else "training put aside for a while")
        # 4. ITEM: a ball seen on this map
        ball = self._item_ball(look, world)
        if ball is not None and has_party:
            return Goal("pick_up", f"an item ball on the ground at {(ball.x, ball.y)}: a person picks it up", milestone.id,
                        target=ball, key=f"item:{world.current}|{ball.x},{ball.y}")
        # 5. CATCH: balls in hand, grass not walked on this map
        if (has_party and balls > 0 and here is not None and here.grass() and world.current not in self.memory.catch_maps
                and not fight_next):
            self.memory.catch_maps.add(world.current)
            fresh = [xy for xy in here.grass() if not here.visits.get(xy)]
            draw = self.rng.random()
            if fresh and draw < errands.catch_seek and self._allowed(f"catch:{world.current}"):
                return Goal("catch", f"{len(fresh)} grass tiles not walked on {here_const} and {balls} POKé BALLS (draw "
                                     f"{draw:.2f} < the {self.state.active}'s {errands.catch_seek}): looking for POKéMON it "
                                     f"has not caught", milestone.id, steps=errands.catch_roam_steps,
                            key=f"catch:{world.current}")
        # 6. CHAT with someone near
        person = self._chat_person(look, world)
        if person is not None:
            return Goal("chat", f"someone stands near at {(person.x, person.y)}: a person says hello now and then",
                        milestone.id, target=person, key=f"chat:{world.current}|{person.local_id}")
        # 7. STORY
        return self._story_goal(look, world, milestone, step)

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
            known = self.hint_known(milestone, world.heard, world, step.map)
            if known:
                # the page the AI READ (never the milestone's stored line: the step-5 verifier's round 2)
                page = heard_page(world.heard, milestone.hint_words, self.memory.pages) if milestone.hint_words else None
                said = (f"the game said: {quote(page, milestone.hint_words)!r}" if page is not None
                        else "a place it has been to; nothing was said")
                return Goal("go", f"{milestone.title}: to {step.map} ({said})", milestone.id, map=step.map,
                            key=f"go:{step.map}")
            why = (f"nobody has said yet (words {milestone.hint_words!r} not heard)" if milestone.hint_words
                   else "nothing the game said names it, and it has not been there")
            return Goal("go", f"{milestone.title}: where to? {why}: exploring", milestone.id, map=None,
                        key=f"go:?{milestone.id}", words=None if self.hints_off else milestone.hint_words)
        if step.do == "ask":
            if const != step.map:
                return Goal("go", f"{milestone.title}: to ask at {step.map} where to go", milestone.id, map=step.map,
                            key=f"go:{step.map}")
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
            known = self.hint_known(milestone, world.heard, world, step.map)
            return Goal("go", f"{milestone.title}: to {step.map}" + ("" if known else " (by looking around: not told yet)"),
                        milestone.id, map=step.map if known else None, key=f"go:{step.map}")
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

    def _people(self, look: Observation) -> list[SeenObject]:
        return sorted((o for o in (look.view.objects if look.view else ()) if o.kind == "npc" and o.source == "object"),
                      key=lambda o: (abs(o.dx) + abs(o.dy), o.local_id))

    def _ask_person(self, look: Observation, world) -> SeenObject | None:
        for person in self._people(look):
            if f"{world.current}|{person.local_id}" not in self.memory.talked:
                return person
        return None

    def _chat_person(self, look: Observation, world) -> SeenObject | None:
        for person in self._people(look):
            key = f"{world.current}|{person.local_id}"
            if key in self.memory.talked or key in self.memory.chat_drawn or abs(person.dx) + abs(person.dy) > 4:
                continue
            self.memory.chat_drawn.add(key)
            draw = self.rng.random()
            if draw < self.state.errands.chat:
                return person
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

    def _heal_place(self, world, marks: dict[str, int]) -> tuple | None:
        """Where it would heal: (the map to be in, the map key of a door seen but never used or None, that door or None,
        how it knows): a centre it has been in; a centre door it has seen; home, once PROF. BIRCH was rescued (MOM
        heals). The nearest of each kind by the known way (`world_distance`)."""
        here = world.here()
        if here is not None and (here.const or "").endswith(CENTER_SUFFIX):
            return here.const, None, None, "in a POKéMON CENTER: the nurse"
        known = self._known_interiors(world, CENTER_SUFFIX)
        if known:
            const, _ = min(known, key=lambda item: (world_distance(world, item[1]), item[0]))
            return const, None, None, f"the POKéMON CENTER it knows ({const})"
        seen = [(key, tile) for (key, tile), kind in self.memory.landmarks.items() if kind == "pokemon_center"
                and key in world.maps]
        if seen:
            key, tile = min(seen, key=lambda item: (world_distance(world, item[0]), item[1]))
            return (f"{world.maps[key].const}_{CENTER_SUFFIX}", key, tile,
                    f"the POKéMON CENTER door it saw on {world.maps[key].const} at {tile}")
        if marks.get("RESCUED_BIRCH"):
            home = self.story.resolve("<player_house_1f>")
            if any(memory.const == home for memory in world.maps.values()):
                return home, None, None, "no POKéMON CENTER known yet: home, where MOM heals"
        return None

    def _mart_place(self, world) -> tuple | None:
        here = world.here()
        if here is not None and (here.const or "").endswith(MART_SUFFIX):
            return here.const, None, None, "in a MART"
        known = self._known_interiors(world, MART_SUFFIX)
        if known:
            const, _ = min(known, key=lambda item: (world_distance(world, item[1]), item[0]))
            return const, None, None, f"the MART it knows ({const})"
        seen = [(key, tile) for (key, tile), kind in self.memory.landmarks.items() if kind == "mart" and key in world.maps]
        if seen:
            key, tile = min(seen, key=lambda item: (world_distance(world, item[0]), item[1]))
            return f"{world.maps[key].const}_{MART_SUFFIX}", key, tile, f"the MART door it saw on {world.maps[key].const} at {tile}"
        return None

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
            return
        fails = self.memory.fails.get(goal.key, 0) + 1
        self.memory.fails[goal.key] = fails
        if fails >= FAIL_LIMIT:
            self.memory.cooldown[goal.key] = self.memory.decisions + COOLDOWN_DECISIONS
            self.memory.fails[goal.key] = 0


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
        hands, nav, manager = self.hands, self.nav, self.manager
        moved_on = lambda look: current(look) != index  # noqa: E731 - the milestone changed: the story moved on
        # a battle the STORY starts (PROF. BIRCH's bag, a talk) is fought, not run from (measured 2026-10-14: the play brain's
        # first chapter-1 run tried RUN in PROF. BIRCH's battle, which the game refuses); training and catching fight too
        self.mind.purpose = "train" if goal.kind in ("train", "catch", "use", "talk", "follow") else "travel"
        if goal.kind in ("go", "look_around", "follow", "find"):
            target_map = goal.map if goal.kind == "go" else None
            look_for = goal.look

            def done(look: Observation) -> bool:
                if moved_on(look):
                    return True
                if goal.words and heard_words(nav.world.heard, goal.words):
                    return True  # told where to go now: decide again
                if look.party and manager.item_ball_in_view(look, nav.world) is not None:
                    return True  # an item ball came into view on the way: a person stops to pick it up (pillar 4)
                if target_map is not None and look.player is not None and look.player.map_const == target_map \
                        and not look.player.settling and look.screen.game_state == "OVERWORLD":
                    return True
                return look_for is not None and manager.looks_like(look, look_for) is not None

            budget = GO_FRAMES if goal.kind == "go" else (FIND_FRAMES if goal.kind == "find" else LOOK_AROUND_FRAMES)
            if goal.kind == "go" and target_map is not None:
                outcome = yield from self._travel(target_map, goal.reason, budget, done)
            else:
                # looking for someone on THIS map keeps to it (a person searching ROUTE 103 for the rival does not go back
                # to OLDALE); looking around may go anywhere
                outcome = yield from nav.run(travel_intent(None, manager.state.active, budget, done,
                                                           stay=goal.kind == "find"), goal.reason)
            return outcome.startswith("done"), outcome
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
            if goal.kind == "use":
                outcome = yield from use_thing(hands, nav, goal.target, goal.reason)
            else:
                outcome = yield from talk_to(hands, nav, goal.target, goal.reason)
            return outcome.startswith("talked"), outcome
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
            outcome = yield from self._shop(goal)
            self.shopping.append(outcome)
            return "bought" in outcome, outcome
        return False, f"no way to pursue a {goal.kind} goal"

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
            return (yield from enter_door(self.hands, nav, goal.tile, goal.reason))
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

    def _shop(self, goal: Goal) -> Generator[None, None, str]:
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
        return "; ".join(outcomes)

