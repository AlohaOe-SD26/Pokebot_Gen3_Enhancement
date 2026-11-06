"""WHERE TO GO NEXT: frontier exploration with PERSONALITY weights (build step 3; HUMAN-PLAY-DESIGN pillars 1 and 4,
design draft §2.3 "goal manager + personality", RULING 37 Q6 "never idle"). Framework-free.

WHAT A PERSON DOES IN A NEW PLACE: walks toward what they have not seen yet, notices the doors and the roads out, and
goes where their taste pulls them. The AI does the same over ITS OWN memory (`ai_player/world/memory.py`, only what
the eyes showed): every candidate below is a tile it has SEEN, scored by
    VALUE_TILES x value(kind, personality) - the walk to it (the navigator's own costs, unknown tiles optimistic)
      + the personality's pull AWAY from where it came into this map (a traveller moves on) + a small seeded jitter
and the best one is the next target. The candidates:
  * FRONTIER: a seen walkable tile next to unseen ones (walking there shows more);
  * ROAD: a walkable tile seen PAST an edge the AI has SEEN crossed (build step 3.1: until a crossing is seen, a tile
    past an edge is just a tile, as on the screen, and counts as frontier): walking onto it leaves;
  * DOOR: a warp or door seen inside the map whose destination is unknown (used by pressing into it: `use_exit`);
  * BACK: an exit KNOWN to lead to a map already visited (the warp graph, or a road on a side whose connection is
    known): worth little, but it is how a dead end (a house) is left;
  * ROUTE: an exit known to lead, directly or through known links, to the intent's GOAL map;
  * GRASS (Catcher, Trainer): tall grass not walked yet; PEOPLE (Trainer): a person not met yet (trainers are people,
    and nothing on screen tells them apart until one engages): the seen tile beside where they stand, walked up to once
    (step 4.1 round 2: see "THE WALK, NOT THE LABELS" below).
The weights are TASTE, not a plan (`WEIGHTS`): Story favours exits toward unexplored maps (roads most), Catcher grass,
Trainer grass and people. NEVER IDLE: when nothing is left the explorer WANDERS to the least-visited seen tile (a
person looks around for what they missed); only when even that is gone does it return None (the intent is stuck).
A candidate that failed in this intent (`Navigator.excluded`) is not chosen again. Every candidate is a tile the AI has
SEEN, the stand tile of an exit included (build step 3.1, finding 8: `_approaches`). (The step-4 verifier's round) A way
BACK to a map seen all of is no option while another way out leads somewhere new or somewhere with something left to see
(`not_back_to_seen_all`: a person who has seen all of a house leaves by the front door rather than go upstairs again).

A WHIM AMONG EQUALS (`pick`, `CHOICE_MARGIN`): the next target is not always the top score. Every candidate within
`CHOICE_MARGIN` points of the best (a point is one tile of walking) is about as good, and a person picks among such
places on a whim: the run's CHOICES stream draws one, the better ones more often (weight 1 + its lead over the
margin's floor). WHY (the step-3 verifier, 2026-10-08): with only the score's small jitter, seeds 3 and 7 of the TOWN
walk chose the SAME seven targets in the same order; their paths differed only by the per-tile path noise. A clear
winner is still chosen every time: a known route to the goal is worth 100 points, far past any frontier (at most ~31).

NOT ON THE MOVE (build step 3.2, the step-3.1 review's MEDIUM finding 4: "the AI changes target almost every step: 22 of
23 dropped as stale", each one re-picked at random among equals). A whim is a decision made STANDING (at the start, at
a target reached). A target chosen WHILE WALKING (the last one dropped as stale: `Navigator.choosing_on_the_move`) keeps
the HEADING (`pick_on_the_move`): the best place AHEAD of the player (in the half of the map it is walking into), unless
another place beats it by more than `CHOICE_MARGIN`; no draw, no jitter (`candidates(jitter=False)`): a person who sees
there is nothing over there walks on toward the next thing ahead, not toward a coin toss.

ONE DECISION, NOT ONE PER STEP (build step 3.2, the step-4 verifier: "finding 4 ... is NOT fixed": 22 of 23 targets still
dropped as stale, SCENEX "decisions on the move 35 of 47", 28 of its 47 walks ONE step, the journeys 20 steps beyond the
shortest way). A frontier tile at the screen's edge is seen past as soon as the player steps toward it: the screen
scrolls, the tile beside it comes into view, and the target is "stale". Re-deciding there, even with the heading kept,
made a decision of every step. A person who decides "let us see what is up there" keeps walking up while the view opens;
the place they meant MOVES ON with the view. So a FRONTIER (or GRASS) target made stale by the walk is CARRIED ON
(`carry_on`): the decision stays the same, and its target becomes the place of the same kind that took the stale one's
place: the nearest to it within `CARRY_RADIUS` tiles, on its side of the player (never behind: `beyond`) and further the
way the unseen lay beside it (`opened`, `further`: a frontier that slides ALONG the screen's edge is another place); no
draw, no new decision, no thinking pause, and its plan stays uncharged (`Navigator.planned_for`). A new place is chosen,
on the move with the heading (`pick_on_the_move`), only when nothing of it is left there (the region is seen: a wall, the
map's end, a room's last corner) or when another place is worth more, from where the player now stands, than the carried one by more than
`CARRY_SWITCH_MARGIN` (one tile of walking: a person changes their mind for something better, not for nothing; with no
such margin at all, MEASURED, the decision held while the walk passed the road out of town). Every carry-on says where
the step-3.2 rule would have gone instead, when that is another place (`Navigator.carry_note`). Proven in
`gates/test_world.py` ChurnTests (FAULTS: no carry-on, the step-3.2 rule; no margin), mutants W79-W81, and live by
`gates/live_step3.py` CHURN bounds with the revert arm SCENEXC and the sweep's CHURN revert (`gates/rate_step3.py`).

THE WALK, NOT THE LABELS (step 4.1, the step-4 adversarial review's finding 7: "the churn fix mostly relabels decisions";
the decisions were carried on, but the journeys were no closer to the shortest known way: TOWN-Trainer's 0.46 of their
steps beyond it). STEP 4.1's first fix charged a place chosen on the move for what its journey would walk beyond the
shortest way from where the journey began; its verifier found it helped TOWN-Trainer and made TOWN-Catcher WORSE on both seed
sets (0.07 -> 0.09, 0.15 -> 0.22): measured seed by seed (2026-10-09), the charge was a pull away from where the journey
began, so it broke near-ties toward the far side of the start (the Catcher's (18, 8) at the town's east edge over (11, 8) on
its main street, then back across town), and it helped the Trainer only where "away from the lab" happened to be "toward
the exit". It is GONE. What the walk wasted was found instead, by cause:
  * the TRAINER'S PEOPLE PULL (its journeys 0.45 of their steps beyond the shortest known way; 0.09 with the pull off): the
    pull was a bonus on UNSEEN tiles near people, gone the moment the player came close enough to see them, so the Trainer
    walked toward someone, stopped short and turned back across town for the next. A person who wants to meet people walks
    UP to them: a PEOPLE place is the seen tile beside a person not met yet (`world/memory.py` persons, met), worth
    `Weights.people`, dropped once they are met (`brain/navigator.py` stale_reason) and after `navigator.MEET_TRIES` walks
    after one who keeps walking off;
  * a person stepping into the way, walked round backwards, and a detour two tiles aside and straight back: the navigator
    (`brain/navigator.py`, "STEP 4.1 ROUND 2").
Measured by the sweep's WALK A/B (`gates/rate_step3.py`: the step-4 explorer against this one on the same plans and seeds)
and `gates/test_world.py` PeopleTests, WaitTests, BendTests.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace

from ai_player.brain.navigator import (MEET_TRIES, Intent, Navigator, Target, distances, exit_press, in_map_walls,
                                       step_from)
from ai_player.eyes.observation import Observation
from ai_player.world.memory import DIRECTIONS, OPPOSITE, MapMemory, WorldMemory, moved, past_edge, road_side

__all__ = [
    "CARRY_RADIUS",
    "CHOICE_MARGIN",
    "JUST_COME_FROM",
    "ONWARD_KINDS",
    "PEOPLE_RECENT",
    "SEEN_ALL",
    "VALUE_TILES",
    "WEIGHTS",
    "Weights",
    "ahead",
    "beyond",
    "candidates",
    "carry_on",
    "choose_target",
    "further",
    "opened",
    "explore_intent",
    "goto_intent",
    "looks_like_exit",
    "map_walls",
    "not_back_to_seen_all",
    "pick",
    "pick_on_the_move",
    "region_hops",
    "ride_stands",
    "route_to",
    "standing_walls",
    "ways_from",
    "weights_for",
]

#: One unit of value is worth walking this many tiles for.
VALUE_TILES = 10.0
#: Candidates scored within this many points (tiles of walking) of the best are about as good: one is picked on a whim.
CHOICE_MARGIN = 4.0
#: (build step 3.2, the step-4 verifier's finding 4) How far (tiles, Manhattan) the place that took a stale target's place
#: may lie from it and still be the SAME place the decision was about (`carry_on`). The view moves one row or column a step,
#: so the frontier past a stale tile is usually 1 away; 3 lets it slide round a corner of what came into view.
CARRY_RADIUS = 3
#: The kinds of target a decision carries on when the walk made them stale (a frontier seen past, grass walked on).
CARRIED_KINDS = ("frontier", "grass")
#: (build step 3.2, the step-4 verifier's finding 4) A decision is carried on unless another place, from where the player
#: now stands, beats the carried place by more than this many points (one tile of walking): then a new decision is made, on
#: the move. MEASURED
#: 2026-10-09 (development sweeps, in-process, the clock pinned; TOWN, ROUTE, SCENE-EXPLORE, TOWN-Catcher, TOWN-Trainer):
#: at 0 (switch for anything better) the walks match the step-3.2 rule's (20 seeds: 5,923 steps against 5,948); at 1,
#: the same cost with fewer decisions; at 2 the Catcher and Trainer walks grew (709 / 632 and 1,253 / 1,042 steps); at
#: `CHOICE_MARGIN` (4), or carried on with no margin at all, the TOWN walk grew a third: it swept a whole street past the
#: road north (a decision held where a person would take the way out it walks past).
CARRY_SWITCH_MARGIN = 1.0
#: (step 4.1 round 2, finding 7) A person seen this recently (frames) is a PEOPLE place (they may have walked off since).
PEOPLE_RECENT = 600


@dataclass(frozen=True)
class Weights:
    frontier: float  # a seen tile next to unseen ones
    road: float  # a walkable tile past the map's edge (the next map)
    door: float  # an exit whose destination is unknown
    back: float  # an exit known to lead to a visited map
    grass: float  # tall grass not walked yet
    people: float  # a person not met yet, walked up to (step 4.1 round 2; it was: unseen tiles near people)
    away: float  # per tile away from where the AI came into this map (at most AWAY_CAP tiles)
    grass_cost: float  # the extra cost of a tall-grass tile when TRAVELLING (wild Pokemon there)


#: The three base personalities (USER RULING 37 Q8; `ai_player/personality.py`).
WEIGHTS: dict[str, Weights] = {
    "Story": Weights(frontier=1.0, road=4.0, door=0.8, back=0.15, grass=0.0, people=0.0, away=0.3, grass_cost=2.0),
    "Catcher": Weights(frontier=1.0, road=2.0, door=0.6, back=0.15, grass=3.0, people=0.0, away=0.1, grass_cost=0.0),
    "Trainer": Weights(frontier=1.0, road=2.0, door=0.8, back=0.15, grass=2.5, people=1.5, away=0.1, grass_cost=0.0),
}
AWAY_CAP = 20
ROUTE_VALUE = 10.0
WANDER_VALUE = 0.05
#: What an exit back to a visited map is worth on top of `Weights.back` while that map still has something unseen: the
#: whole of it once `PROMISE_FULL` things are left there, a share of it for fewer.
BACK_PROMISE = 0.5
PROMISE_FULL = 10
#: (build step 3.1) The kinds of place that are somewhere NEW on this map, and the reason's start that marks the exit
#: back the way the AI just came in (dropped while any new place is reachable: `candidates`). (Step 4.1 round 2) a person
#: not met yet is someone new.
ONWARD_KINDS = ("frontier", "road", "door", "route", "grass", "people")
JUST_COME_FROM = "it leads straight back to"
#: (the step-4 verifier's round) the reason's end that marks a way back to a map with nothing left to see (`candidates`)
SEEN_ALL = "seen all of"


def weights_for(personality: str) -> Weights:
    return WEIGHTS.get(personality, WEIGHTS["Story"])


def ways_from(world: WorldMemory, key: str) -> list[tuple[str, dict]]:
    """Every known way out of map `key` for a route: its links (`WorldMemory.links_from`: warps and connections) and
    (chapter 6 NS2, 2026-11-06) its RIDES (`WorldMemory.rides_from`: someone who took the player to another map when it
    said YES to their offer; `brain/rides.py`), as ("ride", the ride with its "name"). A memory with no rides: the links
    alone, exactly as before."""
    return world.links_from(key) + [("ride", {**ride, "name": name}) for name, ride in world.rides_from(key)]


def ride_stands(memory: MapMemory, ride: dict) -> list[tuple[int, int]]:
    """(chapter 6 NS2) The tiles from which a ride's person is talked to, as far as the AI knows: the walkable seen tiles
    beside the tile they stood on (`ride["tile"]`)."""
    tile = ride.get("tile")
    if not tile:
        return []
    x, y = int(tile[0]), int(tile[1])
    return [xy for xy in ((x, y + 1), (x - 1, y), (x + 1, y), (x, y - 1)) if memory.passable(xy)]


def route_to(world: WorldMemory, source: str, goal: Callable[[MapMemory | None, str], bool],
             at: tuple[int, int] | None = None, walls: frozenset | set = frozenset()) -> list[tuple[str, dict]] | None:
    """The known links (warps, connections) from map `source` to a map `goal(memory, key)` accepts, breadth first over
    what the AI has used or inferred; None when it knows no way.

    (KI-134, 2026-11-05) FROM WHERE THE PLAYER STANDS: with `at` (the player's tile on `source`; `walls`, the tiles not to
    step on there now) a place in the search is a map AND THE PART OF IT A WALK CAN GET TO from where the AI came in, not
    the map alone. WHY (the chapters 6-7 development probe, ledger #96, 0 of 3 runs reached MR. BRINEY's cottage): ROUTE
    104 is two parts that do not join on foot. The north strip (the RUSTBORO road, the woods' north door) never reaches the
    cottage's door (17, 50) in the south part; the woods' SOUTH doors do. Searched by maps, ROUTE 104 was one place, so the
    first known link "toward the cottage" from the woods was the north door it had just come through (the first in the
    warp graph's order), and from the north strip the cottage's own door, which no walk there gets to: 16, 43 and 47
    ping-pongs in the three runs. A person who has walked the woods knows the south path comes out by the cottage.
      * A part of a map is the navigator's own reach from a tile (`distances` round `walls`, never through the tiles seen
        past a crossed edge: `in_map_walls`, KI-129 Part A's "one rule for can it get there", `Navigator.cut_off`'s reach):
        unseen tiles optimistic within its search box, a ledge one way, a side bumped `BUMP_GIVE_UP` times shut, exactly
        as a walk is planned. `walls` given as one set are the source's: they count on every part of the source (they are
        its tiles); no others. (KI-134 V1, 2026-11-06) Given as a MAPPING (map key -> tiles: `map_walls`), each map's walls
        count on that map, whichever map the search starts on: a decision on ROUTE 104 and one in the woods then see the
        same parts of ROUTE 104 (with only the source's, a tile a scene sent the player back from on ROUTE 104 was a wall
        from ROUTE 104 and none from the woods, so the two decisions sent the player back and forth through the woods'
        north door: the KI-134 verifier's flip-flop on test_w1's own fixture).
      * A WARP is a way on from a part when one of its stand tiles (`_approaches`: seen, walkable, in the reach, the press
        its look asks for) is; it lands where its link records (`arrival`); a warp with none recorded is still a way TO
        the goal, never a way on.
      * A CONNECTION is a way on from a part when a seen walkable tile of it on that side steps straight across the edge
        it has seen crossed onto a seen walkable tile past it (`step_from`: a bumped side refused); it lands on that tile
        moved by the crossing's recorded `offset` (the other way for a connection known from its far side). A crossing
        with no offset is no way on (none in the probe's memories: all 88 recorded one).
      * An arrival inside a part of that map already searched from is not searched again (what it gets to, that part got
        to first), so the search ends; a route BACK onto the map it starts on is followed (out through the woods and in
        again by the south door).
    Without `at` (no position: the earlier callers and tests) the search is by maps, exactly as before; with it, a search by
    maps that finds no way ends the search at once (a way through parts of maps is a way through maps too): a goal on no
    map it knows, the commonest walk of all, costs what it did, and the map it stands on is never the goal of a route, as
    before (the search by maps never goes back to it; without this, out through the woods and in again would be a "route"
    to ROUTE 104 from ROUTE 104: mutant G478 fails KI134RegionTests test_c1 and test_e1)."""
    if at is not None and route_to(world, source, goal) is None:
        return None
    regions = _Regions(world, source, walls) if at is not None and world.maps.get(source) is not None else None
    start = (int(at[0]), int(at[1])) if regions is not None else None
    frontier: list[tuple[str, tuple[int, int] | None, list]] = [(source, start, [])]
    queued = {(source, start)}
    seen = {source}
    while frontier:
        key, entry, path = frontier.pop(0)
        reach = regions.part_from(key, entry) if regions is not None else None
        if regions is not None and reach is None:
            continue  # (KI-134) a part of the map already searched from, or a map it holds no memory of
        # (chapter 6 NS2) a RIDE is a link too (`ways_from`): walk up to the person, talk, say YES
        for kind, link in ways_from(world, key):
            if kind == "warp" and not looks_like_exit(world, key, link.get("tile")):
                # (build step 5) a "warp" whose tile does not LOOK like a way out is no way a person can take: a map change a
                # SCENE made from where the player stood (PROF. BIRCH taking the player from the grass of ROUTE 101 to his
                # lab), or a walk across a map's edge remembered as a warp. Measured 2026-10-14 (the play brain's first
                # chapter-1 run): heading back to the lab, the route ran through Birch's scene link from ROUTE 101, which no
                # target can use, and the walk went up and down between ROUTE 101 and OLDALE TOWN until its novelty window
                # ended it, three times; and the chapter-1 sweep's seed 7: a walk across ROUTE 101's edge into LITTLEROOT
                # with a fade between the two looks was remembered as a warp from (10, 19), a grass-side tile. A scene that
                # walked the player through a DOOR is that door, though: MOM walks the player in through the front door of
                # the new house, and until the step-5 verifier's round (2026-10-14) every scene link was refused, so the AI
                # knew no way HOME (it had never walked in by itself) and its walks home to heal ran out on ROUTE 101
                # (the development sweep step5dev7, seed 3: twice 9,000 frames, then a whiteout at 2/26 HP)
                continue
            target = link.get("to") if kind in ("warp", "ride") else link.get("target")
            if target is None or (regions is None and target in seen):
                continue
            arrivals = regions.landings(key, reach, kind, link) if regions is not None else []
            if arrivals is None:
                continue  # (KI-134) no walk from this part of the map gets to it
            step = path + [(kind, link)]
            if goal(world.maps.get(target), target):
                return step
            if regions is None:
                seen.add(target)
                frontier.append((target, None, step))
                continue
            for arrival in arrivals:
                if (target, arrival) not in queued:
                    queued.add((target, arrival))
                    frontier.append((target, arrival, step))
    return None


class _Regions:
    """(KI-134, 2026-11-05) What one `route_to` search knows of the PARTS of maps: per map, the reach of every entry
    searched from (`part_from`), and which links can be used from one of them, landing where (`landings`)."""

    def __init__(self, world: WorldMemory, source: str, walls: frozenset | set | Mapping) -> None:
        self.world = world
        self.source = source
        # (KI-134 V1) per map, the tiles a walk there goes round: a mapping as given (`map_walls`), or one set: the source's
        self.walls_by: dict[str, frozenset] = ({str(key): frozenset(tiles) for key, tiles in walls.items()}
                                               if isinstance(walls, Mapping) else {source: frozenset(walls)})
        self.walls = self.walls_by.get(source, frozenset())
        self.searched: dict[str, list[dict]] = {}
        self.blocked: dict[str, frozenset] = {}
        self.roads: dict[tuple[str, str], list[tuple[int, int]]] = {}
        self.landing: dict[tuple, list | None] = {}

    def walls_of(self, key: str, memory: MapMemory) -> frozenset:
        """What a walk on map `key` goes round (`route_to`): that map's walls (`walls_by`), and on every map the tiles seen
        past a crossed edge (`in_map_walls`), worked out once a search."""
        if key not in self.blocked:
            self.blocked[key] = in_map_walls(memory, self.walls_by.get(key, frozenset()), None)
        return self.blocked[key]

    def part_of(self, key: str, reach: dict) -> int | None:
        """(the KI-134 verifier's NIT V8) Which of map `key`'s searched parts `reach` is (its index in `searched`), by
        identity; None for a reach this search did not work out (then nothing is cached for it: a cache keyed by `id()`
        hit for a freed reach whose id was reused)."""
        return next((index for index, part in enumerate(self.searched.get(key, ())) if part is reach), None)

    def part_from(self, key: str, entry: tuple[int, int]) -> dict | None:
        """Where a walk from `entry` on map `key` can get to (the navigator's reach: `route_to`), or None when the map is
        not remembered or the parts already searched from get everywhere `entry` does: `entry` is in one, or it is no
        walkable tile (an arrival ON a door or a mat, never walked through, is in no reach) and every first step from it
        lands in one (what a tile of a reach gets to, that reach got to; a tile no walk stands on uses no link itself)."""
        memory = self.world.maps.get(key)
        if memory is None:
            return None
        known = self.searched.get(key, [])
        walls = self.walls_of(key, memory)
        if any(entry in part for part in known):
            return None
        if known and not memory.passable(entry) and all(
                step is None or any(step[0] in part for part in known)
                for step in (step_from(memory, entry, direction, walls, 0.0) for direction in DIRECTIONS)):
            return None
        found = distances(memory, entry, walls, 0.0)
        self.searched.setdefault(key, []).append(found)
        return found

    def landings(self, key: str, reach: dict, kind: str, link: dict) -> list[tuple[int, int]] | None:
        """The tiles a link of map `key` lands on, used from the part `reach`: a warp's recorded arrival ([] when none is
        recorded), every tile a crossing of a connection lands on; None when no walk in that part gets to it."""
        memory = self.world.maps[key]
        if kind == "warp":
            tile = link.get("tile")
            if tile is None or not _approaches(memory, (int(tile[0]), int(tile[1])), reach):
                return None
            arrival = link.get("arrival")
            return [(int(arrival[0]), int(arrival[1]))] if arrival else []
        if kind == "ride":
            # (chapter 6 NS2) a ride is taken from a part where a walk gets beside the person (`ride_stands`); it lands
            # where the controls came back
            if not any(stand in reach for stand in ride_stands(memory, link)):
                return None
            arrival = link.get("arrival")
            return [(int(arrival[0]), int(arrival[1]))] if arrival else []
        direction, offset = link.get("direction"), link.get("offset")
        if direction not in DIRECTIONS or not offset:
            return None
        sign = -1 if link.get("inferred") else 1  # known from its far side: the recorded offset taken back
        shift = (sign * int(offset[0]), sign * int(offset[1]))
        part = self.part_of(key, reach)
        cached = (key, part, direction, shift) if part is not None else None
        if cached is None or cached not in self.landing:
            walls = self.walls_by.get(key, frozenset())  # the tile past the edge is entered: no edge walls
            if (key, direction) not in self.roads:
                self.roads[(key, direction)] = [xy for xy in memory.roads() if past_edge(memory.edges, xy, direction)]
            out = set()
            for road in self.roads[(key, direction)]:
                inside = moved(road, OPPOSITE[direction])
                if inside not in reach or memory.outside(inside) or not memory.passable(inside):
                    continue
                crossed = step_from(memory, inside, direction, walls, 0.0, allow_unknown=False)
                if crossed is not None and crossed[0] == road:
                    out.add((road[0] + shift[0], road[1] + shift[1]))
            found = sorted(out) or None
            if cached is None:
                return found
            self.landing[cached] = found
        return self.landing[cached]


def standing_walls(world: WorldMemory) -> dict[str, frozenset]:
    """(KI-134 V1 and V3, 2026-11-06) Per map the AI remembers: the things it saw STANDING there on its last look of that
    map that are not people (an item ball, a boulder: `MapMemory.objects_now` less `people_now`; people walk on). What a
    walk there goes round as far as the AI knows, whichever map it decides on.
    (Round 3, 2026-11-06, the KI-134 follow-ups' verifier's V-N5) ONLY WHAT WAS SEEN IN THIS SESSION: `objects_now` is the
    last look of a map and is NOT saved with the memory (`MapMemory.to_dict`), so a run that starts from a saved memory
    knows no standing thing on any other map until it looks at that map again. Decided: kept so, not saved. A thing seen
    standing in an earlier session (an item ball since picked up, a boulder since pushed) is exactly what a person may find
    gone, and a saved one would be a wall that outlives what made it; within a session it is what the AI last saw."""
    out: dict[str, frozenset] = {}
    for key, memory in world.maps.items():
        things = memory.objects_now - memory.people_now
        if things:
            out[key] = frozenset(things)
    return out


def map_walls(nav: Navigator, memory: MapMemory, walls: frozenset) -> dict[str, frozenset]:
    """(KI-134 V1, 2026-11-06) What `route_to` goes round on EVERY map, for a decision on `memory` (`candidates`): this
    map's `walls` (`Navigator.walls`: what stands there now, the tiles a scene sent the player back from) less the people
    (they walk on); every other map's `standing_walls` and the tiles a scene sent the player back from THERE in this
    intent (`Navigator.scene_walls`, kept per map). A decision in the woods then sees ROUTE 104's scene wall exactly as a
    decision on ROUTE 104 does, and the two agree."""
    out = standing_walls(nav.world)
    for key, tiles in (getattr(nav, "scene_walls", None) or {}).items():
        if tiles and key != memory.key:
            out[key] = out.get(key, frozenset()) | frozenset(tiles)
    out[memory.key] = frozenset(walls - memory.people_now)
    return out


def region_hops(world: WorldMemory, source: str, at: tuple[int, int],
                walls: frozenset | set | Mapping = frozenset()) -> dict[str, int]:
    """(KI-134 V3, 2026-11-06) How many known links the route FROM WHERE THE PLAYER STANDS takes to each map it gets to:
    `route_to`'s search over the parts of maps a walk gets to (the same `_Regions`, the same rules for a warp and a road),
    run once for every map at once, breadth first, so each map's number is its shortest such route. The map the player
    stands on is 0; a map no walk from here is known to get to is left out (the caller decides what that means). WHY: the
    nearest POKéMON CENTER from ROUTE 104's north strip was PETALBURG's by maps (ROUTE 104 touches both towns), four links
    away through the woods, when RUSTBORO's is two (`goals.world_distance`)."""
    hops = {source: 0}
    if world.maps.get(source) is None:
        return hops
    regions = _Regions(world, source, walls)
    start = (int(at[0]), int(at[1]))
    frontier: list[tuple[str, tuple[int, int], int]] = [(source, start, 0)]
    queued = {(source, start)}
    while frontier:
        key, entry, depth = frontier.pop(0)
        reach = regions.part_from(key, entry)
        if reach is None:
            continue
        for kind, link in ways_from(world, key):  # (chapter 6 NS2) the rides too
            if kind == "warp" and not looks_like_exit(world, key, link.get("tile")):  # no way a person takes (`route_to`)
                continue
            target = link.get("to") if kind in ("warp", "ride") else link.get("target")
            if target is None:
                continue
            arrivals = regions.landings(key, reach, kind, link)
            if arrivals is None:
                continue
            hops.setdefault(target, depth + 1)
            for arrival in arrivals:
                if (target, arrival) not in queued:
                    queued.add((target, arrival))
                    frontier.append((target, arrival, depth + 1))
    return hops


def looks_like_exit(world: WorldMemory, key: str, tile) -> bool:
    """(build step 5) Does the tile a warp link starts from LOOK like a way out (a door, stairs, a mat: `TileFact.warp` or
    `.door`)? A tile not seen, or seen as anything else, is not one."""
    memory = world.maps.get(key)
    fact = memory.fact((int(tile[0]), int(tile[1]))) if memory is not None and tile is not None else None
    return fact is not None and (fact.warp or fact.door)


def _approaches(memory: MapMemory, exit_tile: tuple[int, int], reach: dict) -> list[tuple[tuple[int, int], str, float]]:
    """Where to stand and which way to press to use the exit: from each reachable SEEN neighbour, pressing toward the
    exit. The press its LOOK asks for when it asks for one (`navigator.exit_press`: an arrow mat's arrow, a door from
    below: build step 3.1); otherwise the press that goes INTO a wall or off the map through it first (stairs against
    the back wall). (Build step 3.1, the step-3 review's finding 8: the stand tile was taken from `reach`, which holds
    UNSEEN tiles too, so an exit's target could be a tile the AI had never seen. It must now be a known, walkable tile.)"""
    fact = memory.fact(exit_tile)
    asked = exit_press(fact.behavior) if fact is not None else None
    out = []
    for direction in DIRECTIONS:
        if asked is not None and direction != asked:
            continue
        stand = moved(exit_tile, OPPOSITE[direction])
        if stand not in reach or not memory.passable(stand):
            continue
        beyond = memory.fact(moved(exit_tile, direction))
        into_wall = beyond is None or beyond.blocked or memory.outside(moved(exit_tile, direction))
        out.append((stand, direction, reach[stand] + (0.0 if into_wall else 3.0)))
    return sorted(out, key=lambda item: item[2])


def candidates(nav: Navigator, look: Observation, weights: Weights, goal: Callable[[MapMemory | None, str], bool] | None = None,
               jitter_on: bool = True) -> list[Target]:
    """Every place worth going on this map, scored (module docstring). `jitter_on` False (build step 3.2: a choice ON THE
    MOVE): no seeded jitter, the scores are what the places are worth."""
    world = nav.world
    found = nav.where(look)
    if found is None:
        return []
    memory, here = found
    walls = nav.walls(memory, here)
    # (build step 3.1, finding 2) the walk to each place includes turning back on its first step (`turn_costs`)
    reach = distances(memory, here, walls, weights.grass_cost, nav.turn_costs())
    entry = nav.entry.get(memory.key, here)
    jitter = nav.rng
    out: list[Target] = []

    side_reach: dict[str, dict] = {}

    def road_walk(tile: tuple[int, int]) -> float | None:
        """(chapter 6, the crossing ping-pong, 2026-11-06) The walk to a tile past an edge, over this map and the tiles
        past THAT side only (`navigator.in_map_walls`, the planner's own rule): never through the map beyond another
        edge, which the walk would cross onto (from ROUTE 104's north strip, the road right was "reached" through
        RUSTBORO)."""
        side = road_side(memory, tile)
        if side not in side_reach:
            side_reach[side] = distances(memory, here, in_map_walls(memory, walls, tile), weights.grass_cost,
                                         nav.turn_costs())
        return side_reach[side].get(tile)

    def add(kind: str, tile: tuple[int, int], value: float, reason: str, exit_tile=None, direction=None, cost=None,
            who: int | None = None, ride: str | None = None) -> None:
        walk = reach.get(tile) if cost is None else cost
        if cost is None and exit_tile is None and memory.edges and memory.outside(tile):
            walk = road_walk(tile)
        if walk is None:
            return
        # the pull AWAY from where it came in is a traveller's: toward new ground (a frontier, a road), never back
        onward = kind in ("frontier", "road", "grass")
        away = weights.away * min(abs(tile[0] - entry[0]) + abs(tile[1] - entry[1]), AWAY_CAP) if onward else 0.0
        score = VALUE_TILES * value - walk + away + (jitter.uniform(0.0, 1.5) if jitter_on else 0.0)
        target = Target(kind, tile, reason, score, exit_tile, direction, who, ride)
        if nav.is_excluded(target):
            return
        # (KI-129 Part B, 2026-10-31) a tile past an edge that ended an earlier intent as a ping-pong, nothing new seen
        # since and its rest not over (`Navigator.edge_ponged`), is no option: someone who walked back and forth over the
        # same line for nothing looks elsewhere for a while. A known way toward the goal ("route") is always kept (the
        # critic's F6); a navigator without the rule (a test's stand-in) keeps everything, as before
        edge_ponged = getattr(nav, "edge_ponged", None)
        if (kind != "route" and exit_tile is None and memory.outside(tile) and edge_ponged is not None
                and edge_ponged(memory, tile, look.frame)):
            return
        out.append(target)

    # (KI-134, 2026-11-05) the route from WHERE THE PLAYER STANDS, over the parts of maps a walk gets to (`route_to`), round
    # what `Navigator.cut_off` walks round (never the people: they walk on); (KI-134 V1, 2026-11-06) round every map's walls,
    # not only this one's (`map_walls`), so decisions on two maps agree
    route = route_to(world, memory.key, goal, here, map_walls(nav, memory, walls)) if goal is not None else None
    first_hop = route[0] if route else None
    names = world.names()
    last = world.transitions[-1] if world.transitions else None
    came_from = last.source if last is not None and last.target == memory.key else None
    here_left = world.promise(memory.key)

    def back(target: str) -> tuple[float, str]:
        """An exit back to a visited map is worth more while that map still has something unseen, the more the more
        is left (a person leaves a house they have seen all of by the door to the town they have not); but NOT the way
        the AI just came in while this map still has something to see (a person who has just walked out of the lab
        does not walk straight back in: measured 2026-10-08, the seed sweep's Catcher seed 1 went lab -> town -> lab ->
        town for the lab's last unseen tile until the ping-pong rule stopped it)."""
        left = world.promise(target)
        name = names.get(target, target)
        if target == came_from and here_left:
            return weights.back, f"{JUST_COME_FROM} {name}, just come from, while {here_left} thing(s) are left to see here"
        if left:
            bonus = BACK_PROMISE * min(1.0, left / PROMISE_FULL)
            return weights.back + bonus, f"it leads back to {name}, where {left} thing(s) are left to see"
        return weights.back, f"it leads back to {name}, {SEEN_ALL}"

    # exits: warps and doors seen on this map
    for exit_tile in memory.exits():
        link = world.link_of(memory.key, exit_tile)
        if first_hop is not None and first_hop[0] == "warp" and tuple(first_hop[1]["tile"]) == exit_tile:
            kind, value, why = "route", ROUTE_VALUE, f"it leads toward the goal ({len(route)} link(s) known)"
        elif link is None:
            kind, value, why = "door", weights.door, "an exit not used yet: where does it go?"
        elif world.visited(link["to"]):
            kind = "back"
            value, why = back(link["to"])
        else:
            kind, value, why = "door", weights.door, "an exit to a map not visited yet"
        for stand, direction, cost in _approaches(memory, exit_tile, reach)[:1]:
            add(kind, stand, value, why, exit_tile, direction, cost)
    # (chapter 6 NS2, 2026-11-06) a RIDE from this map is the first link toward the goal: walk up beside the person (the
    # nearest tile beside where they stood), where the play brain talks to them (`Navigator.run`, `rider`)
    if first_hop is not None and first_hop[0] == "ride":
        ride = first_hop[1]
        stands = sorted((xy for xy in ride_stands(memory, ride) if xy in reach), key=lambda xy: (reach[xy], xy))
        for stand in stands[:1]:
            add("route", stand, ROUTE_VALUE, f"the ride toward the goal: the person at {tuple(ride.get('tile') or ())} "
                                             f"took it to {names.get(ride.get('to'), ride.get('to'))} for a YES to "
                                             f"{str(ride.get('words'))[:60]!r} ({len(route)} link(s) known)",
                ride=ride.get("name"))
    # roads: walkable tiles past the edge (a connection is known both ways)
    known_sides = {link["direction"]: link for kind, link in world.links_from(memory.key) if kind == "connection"}
    for tile in memory.roads():
        side = road_side(memory, tile)
        link = known_sides.get(side)
        if first_hop is not None and first_hop[0] == "connection" and first_hop[1].get("direction") == side:
            add("route", tile, ROUTE_VALUE, f"the road {side} leads toward the goal")
        elif link is not None and world.visited(link["target"]):
            value, why = back(link["target"])
            add("back", tile, value, f"the road {side}: {why}")
        else:
            add("road", tile, weights.road, f"a road leads {side}, off this map")
    # the frontier, with the personality's pull toward grass (step 4.1 round 2: no longer toward people: below)
    for tile in memory.frontier():
        unknown = memory.unknown_neighbours(tile)
        value = weights.frontier * (1.0 + unknown / 3.0)
        fact = memory.fact(tile)
        if fact is not None and fact.grass and not memory.visits.get(tile):
            value += weights.grass
        add("frontier", tile, value, f"{unknown} unseen tile(s) beside it")
    # grass for its own sake (Catcher, Trainer)
    if weights.grass > 0:
        for tile in memory.grass():
            # (build step 5) grass SEEN ACROSS an edge it has crossed is the next map's: walking to it leaves this map, and
            # on that map the way back here was the better place again. Measured 2026-10-14 (the play brain's chapter-1
            # sweep, seeds 3 and 6, Trainer and Catcher tastes): in OLDALE TOWN the grass of ROUTE 101 below its edge
            # scored over the road on, and the walk crossed that edge back and forth until the novelty window ended it,
            # nine times running
            if not memory.visits.get(tile) and not memory.outside(tile):
                add("grass", tile, weights.grass * 0.8, "tall grass not walked yet: wild Pokemon")
    # (step 4.1 round 2, the step-4 review's finding 7) PEOPLE (Trainer): a person seen lately and not met yet is walked UP
    # to: the seen walkable tile beside where they stand (the nearest), once (`navigator.MEET_TRIES` decisions at most),
    # worth the personality's taste for people (`Weights.people`: about what a frontier tile is worth, so a person is met
    # when they are about on the way, not by crossing town and back for each). It used to be that taste as a bonus on unseen
    # tiles near people, gone as soon as the player came close enough to see them: the Trainer turned back short of every
    # person (module docstring, "THE WALK, NOT THE LABELS"). MEASURED 2026-10-09 (TOWN-Trainer, seeds 1-10 and 101-110,
    # in-process, the clock pinned): the step-4 pull met 57 of the 80 people it saw in 1,043 steps, its journeys 0.43 of their
    # steps beyond the shortest known way; this place, worth `Weights.people` (1.5), met 69 of 80 in 816 steps, 0.27; worth
    # 1.75, 2.0 or 2.5 the Trainer crossed town for each person: 0.42, 0.44, 0.50
    if weights.people > 0:
        tries = getattr(nav, "people_tries", {})
        for who, (px, py, frame) in sorted(memory.persons.items()):
            if (look.frame - frame >= PEOPLE_RECENT or who in memory.met
                    or tries.get(f"{memory.key}|{who}", 0) >= MEET_TRIES):
                continue
            stands = [xy for xy in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1))
                      if xy in reach and memory.passable(xy) and xy not in memory.objects_now]
            if stands:
                stand = min(stands, key=lambda xy: (reach[xy], xy))
                add("people", stand, weights.people, f"someone not met yet, at {(px, py)}: a trainer would see the player "
                                                    f"from here", who=who)
    # (build step 3.1) the way JUST COME IN is no option at all while there is somewhere NEW to go on this map, however far:
    # measured 2026-10-08 (the step-3.1 sweep's TOWN-Catcher seed 8), once roads are no longer known from the coordinates
    # the far frontier north of Littleroot (16 tiles) scored below the house door one step away (worth `Weights.back`),
    # and the AI went house -> town -> house until the ping-pong rule stopped it. A person walks on to the unexplored
    # path rather than back into the house they have just seen all of.
    if any(t.kind in ONWARD_KINDS for t in out):
        out = [t for t in out if not (t.kind == "back" and JUST_COME_FROM in t.reason)]
    # (the step-4 verifier's round) and a way back to a map SEEN ALL OF is no option while a way out leads somewhere with
    # something left to see, or somewhere new: measured 2026-10-09 (the sweep's CROP seed 1, and the stair PING-PONGS of
    # SCENE-EXPLORE seeds 5 and 15 of the 20-seed development sweep), once a doormat counts as one way out the stairs up to a
    # floor seen all of, one step away, scored above the doormat to the town with things left to see, four steps away, and
    # the AI went up and down until the ping-pong rule ended the intent. A person who has seen all of a house leaves it by
    # the front door rather than go upstairs again.
    return not_back_to_seen_all(out)


def not_back_to_seen_all(found: list[Target]) -> list[Target]:
    """(the step-4 verifier's round) `found` without the ways back to a map SEEN ALL OF, when one of them leads somewhere
    new or somewhere with something left to see (`candidates`' last rule)."""
    if any(t.kind in ONWARD_KINDS or (t.kind == "back" and SEEN_ALL not in t.reason and JUST_COME_FROM not in t.reason)
           for t in found):
        return [t for t in found if not (t.kind == "back" and SEEN_ALL in t.reason)]
    return found


def pick(found: list[Target], rng) -> Target:
    """A WHIM AMONG EQUALS (module docstring): one of the candidates within `CHOICE_MARGIN` of the best score, drawn
    from `rng` with weight 1 + its lead over the margin's floor (in a fixed order, so a seed replays)."""
    best = max(target.score for target in found)
    floor = best - CHOICE_MARGIN
    near = sorted((t for t in found if t.score >= floor), key=lambda t: (-t.score, t.kind, t.tile))
    return rng.choices(near, weights=[1.0 + target.score - floor for target in near])[0]


def ahead(here: tuple[int, int], tile: tuple[int, int], heading: str | None) -> bool:
    """(build step 3.2) Is `tile` AHEAD of a player on `here` walking `heading`: in the half of the map it walks into
    (strictly: a place straight beside the player is not ahead)? False with no heading."""
    if heading not in DIRECTIONS:
        return False
    dx, dy = DIRECTIONS[heading]
    return (tile[0] - here[0]) * dx + (tile[1] - here[1]) * dy > 0


def pick_on_the_move(found: list[Target], here: tuple[int, int], heading: str | None) -> Target:
    """(build step 3.2, the step-3.1 review's finding 4) The choice made WHILE WALKING (module docstring): the best place
    AHEAD (`ahead`), unless the best of all beats it by more than `CHOICE_MARGIN` (then that one: it is clearly better);
    with nothing ahead, the best of all. No draw: the same places give the same choice, whatever the seed."""
    order = sorted(found, key=lambda t: (-t.score, t.kind, t.tile))
    best = order[0]
    forward = [t for t in order if ahead(here, t.tile, heading)]
    if not forward:
        return best
    keep = forward[0]
    return best if best.score - keep.score > CHOICE_MARGIN else keep


def beyond(here: tuple[int, int], old: tuple[int, int], tile: tuple[int, int]) -> bool:
    """(build step 3.2, the step-4 verifier's finding 4) Is `tile` on the stale target `old`'s side of a player on `here`:
    the way to it does not turn back from the way to `old` (their directions from `here` make an acute angle)? A tile
    the player stands on is not."""
    return (tile[0] - here[0]) * (old[0] - here[0]) + (tile[1] - here[1]) * (old[1] - here[1]) > 0


def opened(memory: MapMemory, tile: tuple[int, int], heading: str | None = None) -> list[str]:
    """(build step 3.2, the step-4 verifier's finding 4) Which way the unseen lay beside a frontier tile the walk has just
    seen past: the side(s) whose tile was seen LAST (the memory's own first-seen frames). A tile that never had an unseen
    side (grass walked on) answers the walk's heading."""
    frames = {d: memory.tiles[moved(tile, d)].seen_frame for d in DIRECTIONS if moved(tile, d) in memory.tiles}
    if not frames or len(frames) < len(DIRECTIONS):
        return [heading] if heading in DIRECTIONS else []
    last = max(frames.values())
    return [d for d, frame in frames.items() if frame == last]


def further(old: tuple[int, int], tile: tuple[int, int], sides: list[str]) -> bool:
    """(build step 3.2) Does `tile` lie at least one tile further than `old` toward one of `sides` (the way the unseen lay,
    the way the decision was going) and at most one tile aside of that line? A frontier that slides ALONG the screen's
    edge is another place, not this one (measured 2026-10-09: with two tiles aside allowed, a decision on Route 101 slid
    from (17, 4) to (15, 3) and its walk bent back 4 steps)."""
    for d in sides:
        dx, dy = DIRECTIONS[d]
        along = (tile[0] - old[0]) * dx + (tile[1] - old[1]) * dy
        aside = abs((tile[0] - old[0]) * dy - (tile[1] - old[1]) * dx)
        if along >= 1 and aside <= 1:
            return True
    return False


def carry_on(nav: Navigator, look: Observation, weights: Weights, old: Target,
             goal: Callable[[MapMemory | None, str], bool] | None = None) -> Target | None:
    """(build step 3.2, the step-4 verifier's finding 4) The SAME decision, carried on (module docstring "ONE DECISION,
    NOT ONE PER STEP"): `old`, a frontier or grass target the walk has made stale, is replaced by the place of the same kind
    nearest to it (within `CARRY_RADIUS` tiles, `beyond` the player: on its side, and `further` the way the unseen lay
    beside it: `opened`), the further along the way to it first, then the better scored. None (a new decision is then
    made on the move) when nothing of the kind is left there, or when another place is worth more, from where the player
    now stands (a place that came into view, or one the walk brought nearer), than the carried one by more than
    `CARRY_SWITCH_MARGIN` (a person changes their mind for something clearly better, not for a
    tile's worth). No draw: the same places give the same answer whatever the seed. Its reason names the place it carries
    on from. It leaves a note on the navigator (`Navigator.carry_note`): "refused" (why not) or "would" (the place the
    step-3.2 rule, a new choice on the move with the heading, would have gone to now, when that is another place: the
    counterfactual the live graders count)."""
    if old.kind not in CARRIED_KINDS:
        return None
    located = nav.where(look)
    if located is None:
        return None
    memory, here = located
    note = getattr(nav, "carry_note", None)
    note = note if isinstance(note, dict) else {}
    sides = opened(memory, old.tile, nav.heading()) if old.kind == "frontier" else ([nav.heading()] if nav.heading() else [])
    found = candidates(nav, look, weights, goal, jitter_on=False)
    same = [t for t in found
            if t.kind == old.kind and t.tile != here and beyond(here, old.tile, t.tile) and further(old.tile, t.tile, sides)
            and abs(t.tile[0] - old.tile[0]) + abs(t.tile[1] - old.tile[1]) <= CARRY_RADIUS]
    if not same:
        note["refused"] = f"nothing of it left within {CARRY_RADIUS} tiles beyond it {sides}"
        return None

    def order(t: Target):
        near = abs(t.tile[0] - old.tile[0]) + abs(t.tile[1] - old.tile[1])
        along = (t.tile[0] - here[0]) * (old.tile[0] - here[0]) + (t.tile[1] - here[1]) * (old.tile[1] - here[1])
        return near, -along, -t.score, t.tile

    nxt = min(same, key=order)
    best = min(found, key=lambda t: (-t.score, t.kind, t.tile))
    if best.score - nxt.score > CARRY_SWITCH_MARGIN:
        note["refused"] = (f"the {best.kind} at {best.tile} is worth {best.score:.1f} from here, clearly more than the "
                           f"{nxt.kind} at {nxt.tile} it would carry on to ({nxt.score:.1f})")
        return None
    step32 = pick_on_the_move(found, here, nav.heading())
    if step32.tile != nxt.tile:
        note["would"] = list(step32.tile)
    return replace(nxt, reason=f"carried on from {old.tile}: {nxt.reason}")


def choose_target(nav: Navigator, look: Observation, weights: Weights,
                  goal: Callable[[MapMemory | None, str], bool] | None = None) -> Target | None:
    """A candidate among the best (`pick`), or ON THE MOVE the one that keeps the heading (`pick_on_the_move`, build step
    3.2); when there is none, a WANDER to the least-visited seen tile (never idle); None when even that is gone."""
    moving = nav.choosing_on_the_move
    located = nav.where(look)
    found = candidates(nav, look, weights, goal, jitter_on=not moving)
    if found:
        if moving and located is not None:
            return pick_on_the_move(found, located[1], nav.heading())
        return pick(found, nav.rng)
    if located is None:
        return None
    memory, here = located
    reach = distances(memory, here, nav.walls(memory, here), weights.grass_cost, nav.turn_costs())
    spots =[xy for xy in reach if xy != here and memory.passable(xy) and not memory.outside(xy)
             and not nav.is_excluded(Target("wander", xy, ""))]
    if not spots:
        return None
    least = min(memory.visits.get(xy, 0) for xy in spots)
    spots = [xy for xy in spots if memory.visits.get(xy, 0) == least]
    # (build step 3.2) on the move no whim here either: the nearest, ahead first
    tile = min(spots, key=lambda xy: ((reach[xy] - (2.0 if ahead(here, xy, nav.heading()) else 0.0), xy) if moving
                                      else (reach[xy] - nav.rng.uniform(0.0, 3.0), xy)))
    return Target("wander", tile, "nothing new in sight: looking around for anything missed", WANDER_VALUE * VALUE_TILES - reach[tile])


def explore_intent(goal_map: str | None, personality: str, budget: int,
                   done: Callable[[Observation], bool] | None = None) -> Intent:
    """Explore with the personality's taste until the player stands on `goal_map` (a map constant as the eyes name it),
    or until `done(look)` when it is given, or until the budget runs out."""
    weights = weights_for(personality)
    finished = done

    def goal(memory: MapMemory | None, key: str) -> bool:
        return goal_map is not None and memory is not None and memory.const == goal_map

    def choose(nav: Navigator, look: Observation) -> Target | None:
        return choose_target(nav, look, weights, goal if goal_map else None)

    def carry(nav: Navigator, look: Observation, old: Target) -> Target | None:
        return carry_on(nav, look, weights, old, goal if goal_map else None)

    def done(look: Observation) -> bool:
        if finished is not None:
            return finished(look)
        if goal_map is None:
            return False
        memory = None
        player = look.player
        if player is not None and not player.settling and player.x is not None and look.screen.game_state == "OVERWORLD":
            memory = player.map_const
        return memory == goal_map

    name = f"explore to {goal_map}" if goal_map else "explore"
    return Intent(name, budget, choose, done, carry_on=carry)


def goto_intent(tiles: list[tuple[int, int]], budget: int) -> Intent:
    """Walk to each of `tiles` of the current map in turn (the BUMP arm's errands: "walk over to that corner")."""
    queue = list(tiles)

    def choose(nav: Navigator, look: Observation) -> Target | None:
        if not queue:
            return None
        return Target("goto", queue[0], f"errand {len(tiles) - len(queue) + 1} of {len(tiles)}: walk to {queue[0]}")

    def reached(target: Target) -> None:
        if queue and target.tile == queue[0]:
            queue.pop(0)

    return Intent(f"walk to {tiles}", budget, choose, lambda look: not queue, reached)
