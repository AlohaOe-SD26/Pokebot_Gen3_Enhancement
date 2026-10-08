"""WHERE TO GO NEXT: frontier exploration with PERSONALITY weights (build step 3; HUMAN-PLAY-DESIGN pillars 1 and 4,
design draft §2.3 "goal manager + personality", RULING 37 Q6 "never idle"). Framework-free.

WHAT A PERSON DOES IN A NEW PLACE: walks toward what they have not seen yet, notices the doors and the roads out, and
goes where their taste pulls them. The AI does the same over ITS OWN memory (`ai_player/world/memory.py`, only what
the eyes showed): every candidate below is a tile it has SEEN, scored by
    VALUE_TILES x value(kind, personality) - the walk to it (the navigator's own costs, unknown tiles optimistic)
      + the personality's pull AWAY from where it came into this map (a traveller moves on) + a small seeded jitter
and the best one is the next target. The candidates:
  * FRONTIER: a seen walkable tile next to unseen ones (walking there shows more);
  * ROAD: a walkable tile seen PAST the map's edge (the screen shows the next map there): walking onto it leaves;
  * DOOR: a warp or door seen inside the map whose destination is unknown (used by pressing into it: `use_exit`);
  * BACK: an exit KNOWN to lead to a map already visited (the warp graph, or a road on a side whose connection is
    known): worth little, but it is how a dead end (a house) is left;
  * ROUTE: an exit known to lead, directly or through known links, to the intent's GOAL map;
  * GRASS (Catcher, Trainer): tall grass not walked yet; PEOPLE (Trainer): tiles near people (trainers are people,
    and nothing on screen tells them apart until one engages).
The weights are TASTE, not a plan (`WEIGHTS`): Story favours exits toward unexplored maps (roads most), Catcher grass,
Trainer grass and people. NEVER IDLE: when nothing is left the explorer WANDERS to the least-visited seen tile (a
person looks around for what they missed); only when even that is gone does it return None (the intent is stuck).
A candidate that failed in this intent (`Navigator.excluded`) is not chosen again.

A WHIM AMONG EQUALS (`pick`, `CHOICE_MARGIN`): the next target is not always the top score. Every candidate within
`CHOICE_MARGIN` points of the best (a point is one tile of walking) is about as good, and a person picks among such
places on a whim: the run's CHOICES stream draws one, the better ones more often (weight 1 + its lead over the
margin's floor). WHY (the step-3 verifier, 2026-10-08): with only the score's small jitter, seeds 3 and 7 of the TOWN
walk chose the SAME seven targets in the same order; their paths differed only by the per-tile path noise. A clear
winner is still chosen every time: a known route to the goal is worth 100 points, far past any frontier (at most ~31).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ai_player.brain.navigator import Intent, Navigator, Target, distances
from ai_player.eyes.observation import Observation
from ai_player.world.memory import DIRECTIONS, OPPOSITE, MapMemory, WorldMemory, moved, road_side

__all__ = [
    "CHOICE_MARGIN",
    "VALUE_TILES",
    "WEIGHTS",
    "Weights",
    "candidates",
    "choose_target",
    "explore_intent",
    "goto_intent",
    "pick",
    "route_to",
    "weights_for",
]

#: One unit of value is worth walking this many tiles for.
VALUE_TILES = 10.0
#: Candidates scored within this many points (tiles of walking) of the best are about as good: one is picked on a whim.
CHOICE_MARGIN = 4.0


@dataclass(frozen=True)
class Weights:
    frontier: float  # a seen tile next to unseen ones
    road: float  # a walkable tile past the map's edge (the next map)
    door: float  # an exit whose destination is unknown
    back: float  # an exit known to lead to a visited map
    grass: float  # tall grass not walked yet
    people: float  # near people
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


def weights_for(personality: str) -> Weights:
    return WEIGHTS.get(personality, WEIGHTS["Story"])


def route_to(world: WorldMemory, source: str, goal: Callable[[MapMemory | None, str], bool]) -> list[tuple[str, dict]] | None:
    """The known links (warps, connections) from map `source` to a map `goal(memory, key)` accepts, breadth first over
    what the AI has used or inferred; None when it knows no way."""
    frontier: list[tuple[str, list]] = [(source, [])]
    seen = {source}
    while frontier:
        key, path = frontier.pop(0)
        for kind, link in world.links_from(key):
            target = link.get("to") if kind == "warp" else link.get("target")
            if target is None or target in seen:
                continue
            step = path + [(kind, link)]
            if goal(world.maps.get(target), target):
                return step
            seen.add(target)
            frontier.append((target, step))
    return None


def _approaches(memory: MapMemory, exit_tile: tuple[int, int], reach: dict) -> list[tuple[tuple[int, int], str, float]]:
    """Where to stand and which way to press to use the exit: from each reachable seen neighbour, pressing toward the
    exit; the press that goes INTO a wall or off the map through it first (a door in a front wall, a mat at the
    bottom of a room, stairs against the back wall)."""
    out = []
    for direction in DIRECTIONS:
        stand = moved(exit_tile, OPPOSITE[direction])
        if stand not in reach:
            continue
        beyond = memory.fact(moved(exit_tile, direction))
        into_wall = beyond is None or beyond.blocked or memory.outside(moved(exit_tile, direction))
        out.append((stand, direction, reach[stand] + (0.0 if into_wall else 3.0)))
    return sorted(out, key=lambda item: item[2])


def candidates(nav: Navigator, look: Observation, weights: Weights, goal: Callable[[MapMemory | None, str], bool] | None = None) -> list[Target]:
    """Every place worth going on this map, scored (module docstring)."""
    world = nav.world
    found = nav.where(look)
    if found is None:
        return []
    memory, here = found
    reach = distances(memory, here, nav.walls(memory, here), weights.grass_cost)
    entry = nav.entry.get(memory.key, here)
    jitter = nav.rng
    out: list[Target] = []

    def add(kind: str, tile: tuple[int, int], value: float, reason: str, exit_tile=None, direction=None, cost=None) -> None:
        walk = reach.get(tile) if cost is None else cost
        if walk is None:
            return
        # the pull AWAY from where it came in is a traveller's: toward new ground (a frontier, a road), never back
        onward = kind in ("frontier", "road", "grass")
        away = weights.away * min(abs(tile[0] - entry[0]) + abs(tile[1] - entry[1]), AWAY_CAP) if onward else 0.0
        score = VALUE_TILES * value - walk + away + jitter.uniform(0.0, 1.5)
        target = Target(kind, tile, reason, score, exit_tile, direction)
        if not nav.is_excluded(target):
            out.append(target)

    route = route_to(world, memory.key, goal) if goal is not None else None
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
            return weights.back, f"it leads back to {name}, just come from, while {here_left} thing(s) are left to see here"
        if left:
            bonus = BACK_PROMISE * min(1.0, left / PROMISE_FULL)
            return weights.back + bonus, f"it leads back to {name}, where {left} thing(s) are left to see"
        return weights.back, f"it leads back to {name}, seen all of"

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
    # the frontier, with the personality's pulls
    people = [xy for xy, frame in memory.people.items() if look.frame - frame < 600]
    for tile in memory.frontier():
        unknown = memory.unknown_neighbours(tile)
        value = weights.frontier * (1.0 + unknown / 3.0)
        fact = memory.fact(tile)
        if fact is not None and fact.grass and not memory.visits.get(tile):
            value += weights.grass
        if people and min(abs(tile[0] - p[0]) + abs(tile[1] - p[1]) for p in people) <= 3:
            value += weights.people
        add("frontier", tile, value, f"{unknown} unseen tile(s) beside it")
    # grass for its own sake (Catcher, Trainer)
    if weights.grass > 0:
        for tile in memory.grass():
            if not memory.visits.get(tile):
                add("grass", tile, weights.grass * 0.8, "tall grass not walked yet: wild Pokemon")
    return out


def pick(found: list[Target], rng) -> Target:
    """A WHIM AMONG EQUALS (module docstring): one of the candidates within `CHOICE_MARGIN` of the best score, drawn
    from `rng` with weight 1 + its lead over the margin's floor (in a fixed order, so a seed replays)."""
    best = max(target.score for target in found)
    floor = best - CHOICE_MARGIN
    near = sorted((t for t in found if t.score >= floor), key=lambda t: (-t.score, t.kind, t.tile))
    return rng.choices(near, weights=[1.0 + target.score - floor for target in near])[0]


def choose_target(nav: Navigator, look: Observation, weights: Weights,
                  goal: Callable[[MapMemory | None, str], bool] | None = None) -> Target | None:
    """A candidate among the best (`pick`); when there is none, a WANDER to the least-visited seen tile (never idle);
    None when even that is gone."""
    found = candidates(nav, look, weights, goal)
    if found:
        return pick(found, nav.rng)
    located = nav.where(look)
    if located is None:
        return None
    memory, here = located
    reach = distances(memory, here, nav.walls(memory, here), weights.grass_cost)
    spots = [xy for xy in reach if xy != here and memory.passable(xy) and not memory.outside(xy)
             and not nav.is_excluded(Target("wander", xy, ""))]
    if not spots:
        return None
    least = min(memory.visits.get(xy, 0) for xy in spots)
    spots = [xy for xy in spots if memory.visits.get(xy, 0) == least]
    tile = min(spots, key=lambda xy: (reach[xy] - nav.rng.uniform(0.0, 3.0), xy))
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
    return Intent(name, budget, choose, done)


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
