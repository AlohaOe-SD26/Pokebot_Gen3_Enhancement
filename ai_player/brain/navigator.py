"""The AI's NAVIGATOR (build step 3; design draft §2.3 "navigator", §10.4 "novelty only", §10.7 "the crop"): walking
from where the player stands to where it wants to be, over what it has SEEN, with its own hands. Framework-free.

WHAT IT PLANS OVER: the AI's own map memory (`ai_player/world/memory.py`), never the map's layout: a tile is known
only after the eyes showed it on screen. A* over that memory, where
  * a KNOWN tile costs 1 to enter, plus the personality's grass cost on tall grass while travelling;
  * an UNKNOWN tile is OPTIMISTIC BUT COSTLY (`UNKNOWN_COST`): the plan may cross it, so the AI walks toward what it
    has not seen, and the plan is redone at every step as the screen shows the truth;
  * a blocked tile, water, a tile LEARNED BLOCKED BY BUMPING and a tile someone stands on now are walls; a LEDGE is
    one way (entered only in its jump direction, landing one tile beyond it); a warp or a door is never walked
    THROUGH on the way somewhere: it is USED on purpose (`use_exit`) by standing next to it and pressing toward it,
    and, on an arrow mat, pressing on (a person tries the obvious way in: into the wall, through the door);
  * a seeded NOISE per target (+0 to +25 % per tile) varies the path between runs and targets (no perfect beeline
    every time), and now and then (`DETOUR_P`) a small DETOUR through a seen tile next to the way.

HOW IT WALKS: one tile at a time (`walk_step`), holding the D-pad in chunks of `CHUNK_FRAMES` and looking between them,
so the walk is continuous (back-to-back holds of the same button are one long hold) and every look can stop it:
the player moved (the save block's tile changed: measured 2026-10-08, 8 frames into a step, then every 16), a map
change began (a fade, the map loading), a battle or a scene started, or nothing moved for `STEP_HOLD_MAX` frames: a
BUMP. A bump next to a person is a person in the way (wait a little, walk round: never learned); otherwise the tile is
learned blocked and the plan goes round it from then on.

INTENTS (`Intent`, `Navigator.run`): every intent has a FRAME BUDGET that progress does NOT reset (design draft §10.4),
and its progress is NOVELTY only (`Novelty`: a tile or a map first seen during the intent, a new story flag, a new
Pokemon of the player's, more items, experience gained; every one that is not a place is TOLD with its particulars and
the clock it moved: `[AI-WORLD] novelty at f...`): walking back and forth through known places is not progress. It ends with what
happened: its goal reached, or "stuck:<reason>" (no novelty for `NOVELTY_WINDOW` frames; one warp used
`PINGPONG_USES` times with nothing new since its second use: a door ping-pong; nothing left to try; a trainer battle,
out of scope), or "budget:" when the frames ran out. It never hangs: every loop is bounded.

INTERRUPTIONS (`handle`): a wild battle is fled (`skills/flee.py`); a scene (a script runs, a text waits, the controls
are locked: Mom with the Running Shoes, Mom sending the player back upstairs) is read and moved on with A only on the
eyes' waits (`hands/dialogue.py` advance); a yes/no in a scene is answered NO (an explorer never agrees to what it does
not know); anything else stops the intent with a reason.
"""

from __future__ import annotations

import heapq
import random
from collections.abc import Callable, Generator
from dataclasses import dataclass, field

from ai_player.eyes.observation import Observation
from ai_player.hands.dialogue import advance, busy_reason, player_free
from ai_player.hands.menus import answer_yes_no
from ai_player.hands.pad import Hands
from ai_player.skills.flee import TRAINER_OUT_OF_SCOPE, flee, in_battle
from ai_player.world.memory import DIRECTIONS, MapMemory, WorldMemory, in_window, moved

__all__ = [
    "BUTTONS",
    "CHUNK_FRAMES",
    "DETOUR_P",
    "NOVELTY_WINDOW",
    "PINGPONG_USES",
    "SEARCH_MARGIN",
    "STEP_HOLD_MAX",
    "UNKNOWN_COST",
    "WARP_HOLD_MAX",
    "Intent",
    "Navigator",
    "Novelty",
    "StepResult",
    "Target",
    "astar",
    "distances",
    "nav_free",
    "step_from",
]

#: The pad's D-pad buttons by direction.
BUTTONS: dict[str, str] = {"up": "Up", "down": "Down", "left": "Left", "right": "Right"}
#: Frames held between two looks while walking (a step takes 16; the tile changes 8 frames in: measured 2026-10-08).
CHUNK_FRAMES = 8
#: Frames held toward a tile with the player not moving: then it was a bump (a step from standing takes 8 to change
#: the tile, one already under way at most 16 more).
STEP_HOLD_MAX = 32
#: Frames held toward an exit (a door opening, an arrow mat stepped on and pressed) before it is given up.
WARP_HOLD_MAX = 64
#: The cost of planning over a tile never seen: optimistic (it may be walkable) but dearer than a known one.
UNKNOWN_COST = 3.0
#: How far past the known tiles a plan may reach into the unknown.
SEARCH_MARGIN = 3
#: Frames (of the emulator) with nothing new before an intent is stuck (about 50 seconds of play).
NOVELTY_WINDOW = 3000
#: One warp used this often in an intent, with nothing new since its second use: a ping-pong, and the intent is stuck.
PINGPONG_USES = 3
#: The chance a target gets a small detour through a seen tile beside the way (seeded).
DETOUR_P = 0.15
#: Bounds.
SETTLE_BUDGET = 900  # frames a map change may take to settle
PERSON_WAIT = 90  # frames to let a person in the way move on
SCENE_TURNS = 8  # menus a scene may raise before it is given up
STILL_DECISIONS = 50  # decisions in a row with no frame passing: a dead end


def nav_free(look: Observation) -> bool:
    """The player can walk: on the map, nothing running, nothing on screen, no fade, a view to walk by."""
    return player_free(look) and not look.screen.fading and look.view is not None


def step_from(memory: MapMemory, xy: tuple[int, int], direction: str, walls: frozenset | set, grass_cost: float,
              allow_unknown: bool = True) -> tuple[tuple[int, int], float] | None:
    """Where one press of `direction` from `xy` leads, and its cost, as far as the AI knows; None if it knows it cannot.
    `walls`: tiles to treat as blocked now (people and things standing there)."""
    nxt = moved(xy, direction)
    if nxt in walls or nxt in memory.bumped:
        return None
    fact = memory.fact(nxt)
    if fact is None:
        return (nxt, UNKNOWN_COST) if allow_unknown else None
    if fact.ledge is not None:
        if fact.ledge != direction:
            return None
        land = moved(nxt, direction)  # a ledge is jumped: the player lands one tile beyond it
        landing = memory.fact(land)
        if land in walls or land in memory.bumped or (landing is not None and not landing.walkable):
            return None
        return land, 2.0
    if not fact.walkable:
        return None
    return nxt, 1.0 + (grass_cost if fact.grass else 0.0)


def _bounds(memory: MapMemory, start: tuple[int, int], goals: set | None = None) -> tuple[int, int, int, int]:
    """The box a plan may search: the known tiles, the start and the goals, plus `SEARCH_MARGIN` of the unknown."""
    xs = [x for x, _ in memory.tiles] + [start[0]] + [x for x, _ in goals or ()]
    ys = [y for _, y in memory.tiles] + [start[1]] + [y for _, y in goals or ()]
    return min(xs) - SEARCH_MARGIN, max(xs) + SEARCH_MARGIN, min(ys) - SEARCH_MARGIN, max(ys) + SEARCH_MARGIN


def astar(memory: MapMemory, start: tuple[int, int], goals: set[tuple[int, int]], walls: frozenset | set,
          grass_cost: float, noise: Callable[[tuple[int, int]], float] | None = None,
          allow_unknown: bool = True) -> list[str] | None:
    """The cheapest way (a list of directions) from `start` to any of `goals` over what the AI knows; None if none.
    `noise(tile)` (>= 0) varies the cost per tile; the heuristic (Manhattan, every step costs >= 1) stays admissible."""
    if start in goals:
        return []
    low_x, high_x, low_y, high_y = _bounds(memory, start, goals)

    def h(xy: tuple[int, int]) -> int:
        return min(abs(xy[0] - g[0]) + abs(xy[1] - g[1]) for g in goals)

    best: dict[tuple[int, int], float] = {start: 0.0}
    came: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}
    queue: list[tuple[float, int, tuple[int, int]]] = [(float(h(start)), 0, start)]
    order = 0
    while queue:
        _, _, here = heapq.heappop(queue)
        if here in goals:
            path = []
            while here != start:
                here, direction = came[here][0], came[here][1]
                path.append(direction)
            return path[::-1]
        for direction in ("up", "down", "left", "right"):
            step = step_from(memory, here, direction, walls, grass_cost, allow_unknown)
            if step is None:
                continue
            nxt, cost = step
            if not (low_x <= nxt[0] <= high_x and low_y <= nxt[1] <= high_y):
                continue
            if noise is not None:
                cost += noise(nxt)
            total = best[here] + cost
            if total < best.get(nxt, float("inf")):
                best[nxt] = total
                came[nxt] = (here, direction)
                order += 1
                heapq.heappush(queue, (total + h(nxt), order, nxt))
    return None


def distances(memory: MapMemory, start: tuple[int, int], walls: frozenset | set, grass_cost: float) -> dict[tuple[int, int], float]:
    """The cheapest cost from `start` to every tile it can reach (known or not, within the search bounds)."""
    low_x, high_x, low_y, high_y = _bounds(memory, start)
    best: dict[tuple[int, int], float] = {start: 0.0}
    queue: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    while queue:
        cost, here = heapq.heappop(queue)
        if cost > best.get(here, float("inf")):
            continue
        for direction in ("up", "down", "left", "right"):
            step = step_from(memory, here, direction, walls, grass_cost)
            if step is None:
                continue
            nxt, extra = step
            if not (low_x <= nxt[0] <= high_x and low_y <= nxt[1] <= high_y):
                continue
            total = cost + extra
            if total < best.get(nxt, float("inf")):
                best[nxt] = total
                heapq.heappush(queue, (total, nxt))
    return best


@dataclass(frozen=True)
class Target:
    """Where the AI decided to go, and why. `tile` is where it walks; for an exit (a warp, a door) `exit` is that tile
    and `direction` the press that uses it from `tile`; a ROAD (a tile past the map's edge) is walked onto."""

    kind: str  # frontier, road, door, back, route, grass, people, wander, goto
    tile: tuple[int, int]
    reason: str
    score: float = 0.0
    exit: tuple[int, int] | None = None
    direction: str | None = None

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.tile}:{self.exit}:{self.direction}"


@dataclass
class Intent:
    """One goal and its bounds. `choose(navigator, look)` names the next place to go (None: nothing left to try);
    `done(look)` says the goal is reached; `reached(target)` is told every target arrived at."""

    name: str
    budget: int
    choose: Callable[["Navigator", Observation], Target | None]
    done: Callable[[Observation], bool]
    reached: Callable[[Target], None] | None = None
    novelty_window: int = NOVELTY_WINDOW


@dataclass
class StepResult:
    kind: str  # moved, bumped, person, changed, battle, scene, lost
    frm: tuple[int, int] | None
    to: tuple[int, int] | None = None
    detail: str = ""


class Novelty:
    """PROGRESS = NOVELTY ONLY (design draft §10.4): a tile or a map first seen, a story flag newly set, a new Pokemon
    of the player's (a PID not seen before, in the party or a box), more items, EXPERIENCE gained (a party Pokemon's
    total experience rose: added after the step-3 verifier noted §10.4 lists XP and the counter did not). `last` is
    the emulator frame of the newest novelty; the intent is stuck when nothing new happened for its window.

    `notable` (since the step-3 verifier's second round): after each `update`, the novelty that is NOT a place (a
    flag, a Pokemon, items, experience) with its particulars (which flag, which PID, from what to what). The navigator
    TELLS it (`[AI-WORLD] novelty ...`, with the intent's clock before and after), so a live run shows WHICH novelty
    moved the clock: the verifier found an experience gain proven only by unit tests. Places (tiles, maps) are left
    out: they come at nearly every step of an exploration, and the memory's own lines already say them."""

    def __init__(self, world: WorldMemory, look: Observation) -> None:
        self.world = world
        self.tiles = world.tiles_learned
        self.maps = {key for key, memory in world.maps.items() if memory.visits}
        self.flags = self._flags(look) or set()
        self.pids = self._pids(look) or set()
        self.items = self._items(look)
        self.experience = self._experience(look) or {}
        self.last = look.frame
        self.events: list[tuple[int, str]] = []
        self.notable: list[str] = []

    @staticmethod
    def _flags(look: Observation) -> set[str] | None:
        return None if look.progress is None else {name for name, on in look.progress.flags if on}

    @staticmethod
    def _pids(look: Observation) -> set[int] | None:
        if look.party is None or look.storage is None:
            return None
        return {m.pid for m in look.party} | {m.pid for m in look.storage}

    @staticmethod
    def _items(look: Observation) -> int | None:
        if look.bag is None:
            return None
        return look.bag.ball_total + sum(quantity for _, quantity in look.bag.healing)

    @staticmethod
    def _experience(look: Observation) -> dict[int, int] | None:
        """Each party Pokemon's total experience, by IDENTITY (PID: CLAUDE.md rule 3), or None when the party was not
        read (a torn read is not a loss)."""
        if look.party is None:
            return None
        return {mon.pid: mon.experience for mon in look.party}

    def update(self, look: Observation) -> list[str]:
        new: list[str] = []
        self.notable = []
        if self.world.tiles_learned > self.tiles:
            new.append(f"{self.world.tiles_learned - self.tiles} new tiles")
            self.tiles = self.world.tiles_learned
        maps = {key for key, memory in self.world.maps.items() if memory.visits}
        if maps - self.maps:
            new.append(f"a new map {sorted(maps - self.maps)}")
            self.maps = maps
        flags = self._flags(look)
        if flags is not None:
            if flags - self.flags:
                new.append(f"a story flag {sorted(flags - self.flags)}")
                self.notable.append(new[-1])
            self.flags = flags
        pids = self._pids(look)
        if pids is not None:
            if pids - self.pids:
                new.append("a new Pokemon")
                self.notable.append(f"a new Pokemon (PID {', '.join(f'{pid:08x}' for pid in sorted(pids - self.pids))})")
            self.pids |= pids
        items = self._items(look)
        if items is not None:
            if self.items is not None and items > self.items:
                new.append("more items")
                self.notable.append(f"more items ({self.items} -> {items})")
            self.items = items
        experience = self._experience(look)
        if experience is not None:
            gained = sorted(pid for pid, value in experience.items() if value > self.experience.get(pid, value))
            if gained:
                new.append(f"experience gained ({len(gained)} Pokemon)")
                self.notable.append("experience gained (" + ", ".join(
                    f"PID {pid:08x}: {self.experience[pid]} -> {experience[pid]}" for pid in gained) + ")")
            self.experience.update(experience)
        if new:
            self.last = look.frame
            self.events.append((look.frame, ", ".join(new)))
        return new


@dataclass
class _Stats:
    steps: int = 0
    bumps: int = 0
    people: int = 0
    exits_used: int = 0
    battles: int = 0
    scenes: int = 0
    decisions: int = 0
    detours: int = 0


class Navigator:
    """Walks with `hands` over what `world` remembers. `grass_cost`: the personality's extra cost of tall grass when
    travelling; `rng`: the run's CHOICES stream (path noise, detours)."""

    def __init__(self, hands: Hands, world: WorldMemory, rng: random.Random, grass_cost: float = 0.0,
                 personality: str = "", on_map_change: Callable[[], None] | None = None) -> None:
        self.hands = hands
        self.world = world
        self.rng = rng
        self.grass_cost = grass_cost
        self.personality = personality
        self.on_map_change = on_map_change
        self.excluded: set[str] = set()  # "map|target key": targets that failed in the current intent (`exclude`)
        self.stats = _Stats()
        self.entry: dict[str, tuple[int, int]] = {}  # map -> where the AI came into it (the explorer's "away")
        self._noise: dict[str, tuple[float, dict[tuple[int, int], float]]] = {}
        self._seen_changes = len(world.transitions)

    # ------------------------------------------------------------------ telling
    def tell(self, line: str, extra: dict | None = None) -> None:
        self.hands.say(f"[AI-WORLD] {line}")
        self.hands.note("world", "say", line, extra)

    def summary(self) -> str:
        s = self.stats
        return (f"{s.steps} steps, {s.bumps} bumps, {s.people} people in the way, {s.exits_used} exits used, "
                f"{s.battles} battles, {s.scenes} scenes, {s.decisions} decisions ({s.detours} detours); "
                f"{len(self.world.maps)} maps, {self.world.tiles_learned} tiles learned")

    # ------------------------------------------------------------------ looking
    def where(self, look: Observation) -> tuple[MapMemory, tuple[int, int]] | None:
        memory = self.world.here()
        player = look.player
        if memory is None or player is None or player.x is None:
            return None
        return memory, (player.x, player.y)

    def walls(self, memory: MapMemory, here: tuple[int, int]) -> frozenset:
        return frozenset(memory.objects_now - {here})

    def exclude(self, target: Target) -> None:
        """`target` failed on the current map, for the rest of the intent (a tile is a tile of ONE map)."""
        self.excluded.add(f"{self.world.current}|{target.key}")

    def is_excluded(self, target: Target) -> bool:
        return f"{self.world.current}|{target.key}" in self.excluded

    def noise_for(self, target: Target) -> Callable[[tuple[int, int]], float]:
        """A seeded cost variation per tile, fixed for one target (so replanning every step keeps one way)."""
        if target.key not in self._noise:
            self._noise[target.key] = (self.rng.random(), {})
        seed, table = self._noise[target.key]

        def noise(xy: tuple[int, int]) -> float:
            if xy not in table:
                table[xy] = random.Random(f"{seed}:{xy}").uniform(0.0, 0.25)
            return table[xy]

        return noise

    def new_changes(self) -> list:
        changes = self.world.transitions[self._seen_changes:]
        self._seen_changes = len(self.world.transitions)
        return changes

    # ------------------------------------------------------------------ walking
    def walk_step(self, direction: str, why: str, gate: str) -> Generator[None, None, StepResult]:
        """One tile in `direction` (module docstring): hold in chunks, look between them. The world is told the AI is
        stepping (a map change during the step is the AI's own) and, once the step is over, that it no longer is (a
        map change later, in a scene, is the scene's)."""
        result = yield from self._walk(direction, why, gate)
        self.world.settle_intent()
        return result

    def _walk(self, direction: str, why: str, gate: str) -> Generator[None, None, StepResult]:
        hands, world = self.hands, self.world
        look = hands.look()
        found = self.where(look)
        if found is None:
            return StepResult("lost", None, detail="no position to step from")
        memory, frm = found
        key = world.current
        world.intend("step", direction)
        held = 0
        while held < STEP_HOLD_MAX:
            text = gate if held == 0 else f"keep walking {direction}: the step from {frm} has not begun ({held} frames held)"
            yield from hands.pad.hold(BUTTONS[direction], CHUNK_FRAMES, why, text)
            held += CHUNK_FRAMES
            look = hands.look()
            if in_battle(look):
                return StepResult("battle", frm, detail="a battle began")
            player = look.player
            if world.current != key or player is None or player.settling or look.screen.fading or look.view is None:
                look = yield from self.settle(why)
                if world.current != key:
                    return StepResult("changed", frm, world.position, detail="the map changed")
                if in_battle(look):
                    return StepResult("battle", frm)
            player = look.player
            if player is not None and player.x is not None and (player.x, player.y) != frm:
                self.stats.steps += 1
                return StepResult("moved", frm, (player.x, player.y))
            if not nav_free(look):
                return StepResult("scene", frm, detail=busy_reason(look))
        target = moved(frm, direction)
        near = [xy for xy in memory.objects_now if abs(xy[0] - target[0]) + abs(xy[1] - target[1]) <= 1]
        if near:
            self.stats.people += 1
            return StepResult("person", frm, target, detail=f"someone at {near[0]}")
        tile = world.learn_bump(frm, direction, look.frame)
        self.stats.bumps += 1
        fact = memory.fact(target)
        self.tell(f"BUMP: moving {direction} from {frm} on {memory.const or memory.key} did not move the player: {tile} "
                  f"is learned blocked (the eyes showed {fact.behavior if fact else 'an unseen tile'}"
                  f"{', elevation %d' % fact.elevation if fact else ''}; held {held} frames)",
                  {"bump": list(tile), "from": list(frm), "direction": direction, "map": memory.key})
        return StepResult("bumped", frm, tile)

    def settle(self, why: str) -> Generator[None, None, Observation]:
        """Watch a map change (or a fade) until the player can walk, the map HAS changed (a scene may start on arrival:
        that is the next decision's business, and the change must be told first), or something needs the hands
        (bounded)."""
        key = self.world.current
        look = self.hands.look()
        for _ in range(SETTLE_BUDGET):
            screen = look.screen
            if (in_battle(look) or nav_free(look) or screen.waits_for_button or screen.ui is not None
                    or self.world.current != key):
                break
            yield from self.hands.pad.busy(busy_reason(look))
            look = self.hands.look()
        return look

    def arrived(self, change, look: Observation) -> None:
        """A map change: say so, remember where the AI came in, save the memory."""
        self.entry.setdefault(change.target, change.arrival)
        memory = self.world.maps.get(change.target)
        self.tell(f"MAP {change.describe(self.world.names())}; {len(memory.tiles) if memory else 0} tiles of it known",
                  {"transition": [change.frame, change.source, change.target, change.how, change.by,
                                  list(change.tile) if change.tile else None, list(change.arrival), change.direction]})
        if self.on_map_change is not None:
            self.on_map_change()

    def use_exit(self, target: Target, why: str) -> Generator[None, None, str]:
        """Use the warp or door `target.exit` from `target.tile` by pressing `target.direction`: into a door, onto stairs,
        onto a mat and on (an arrow mat warps when pressed toward its arrow while standing on it). Returns "used",
        "battle", "scene", "strayed" (the press walked the player elsewhere) or "failed"."""
        result = yield from self._use(target, why)
        self.world.settle_intent()
        return result

    def _use(self, target: Target, why: str) -> Generator[None, None, str]:
        hands, world = self.hands, self.world
        look = hands.look()
        found = self.where(look)
        if found is None:
            return "failed"
        memory, frm = found
        key = world.current
        direction, exit_tile = target.direction, target.exit
        fact = memory.fact(exit_tile)
        what = "door" if fact is not None and fact.door else "warp"
        world.intend("warp", direction, exit_tile)
        held = 0
        while held < WARP_HOLD_MAX:
            here = (look.player.x, look.player.y) if look.player is not None and look.player.x is not None else None
            gate = (f"use the {what} at {exit_tile}: press {direction} from {here} (it was seen as {fact.behavior if fact else '?'}"
                    f"{', blocked' if fact is not None and fact.blocked else ''}), the player free")
            yield from hands.pad.hold(BUTTONS[direction], CHUNK_FRAMES, why, gate)
            held += CHUNK_FRAMES
            look = hands.look()
            if in_battle(look):
                return "battle"
            screen = look.screen
            if not nav_free(look) and not (screen.waits_for_button or screen.ui is not None):
                # the warp under way: a door opening (the controls locked while it plays), a fade, the map loading
                look = yield from self.settle(why)
            if world.current != key:
                self.stats.exits_used += 1
                return "used"
            if not nav_free(look):
                return "scene"
            player = look.player
            spot = (player.x, player.y) if player is not None and player.x is not None else None
            if spot not in (frm, exit_tile):
                return "strayed"  # stepped somewhere else: not this exit's way
        self.tell(f"the {what} at {exit_tile} did not take the player anywhere pressing {direction} from {frm} "
                  f"({held} frames): another way next time")
        return "failed"

    def take_changes(self) -> list:
        """Tell and return the map changes since the last call (for loops that do not go through `run`)."""
        changes = self.new_changes()
        for change in changes:
            self.arrived(change, self.hands.last)
        return changes

    # ------------------------------------------------------------------ interruptions
    def handle(self, look: Observation, why: str) -> Generator[None, None, str | None]:
        """The player cannot walk: a battle, a scene, a fade. None to carry on, or a reason to stop the intent."""
        self.world.settle_intent()  # whatever moves the player now, the AI's own step is over
        if in_battle(look):
            self.stats.battles += 1
            outcome = yield from flee(self.hands)
            self.tell(f"battle: {outcome}")
            if outcome == TRAINER_OUT_OF_SCOPE:
                return f"stuck: {outcome}"
            if outcome not in ("fled", "the battle ended"):
                return f"stuck: the battle: {outcome}"
            return None
        screen = look.screen
        if not (screen.script_running or screen.controls_locked or screen.waits_for_button or screen.text_box_open
                or screen.ui is not None):
            yield from self.settle(why)  # a fade or a map loading: nothing to press
            return None
        self.stats.scenes += 1
        for _ in range(SCENE_TURNS):
            outcome = yield from advance(self.hands, lambda l: nav_free(l) or in_battle(l), f"{why}: a scene")
            if outcome == "done":
                return None
            if outcome == "menu:yes_no":
                if not (yield from answer_yes_no(self.hands, False, f"{why}: a question in a scene: NO (an explorer agrees to nothing it does not know)")):
                    return "stuck: a yes/no in a scene could not be answered"
                continue
            if outcome.startswith("menu:"):
                return f"stuck: an unexpected {outcome[5:]} on screen"
            return f"stuck: a scene: {outcome}"
        return "stuck: a scene that did not end"

    # ------------------------------------------------------------------ going somewhere
    def toward(self, target: Target, look: Observation, why: str) -> Generator[None, None, str]:
        """One step toward `target` (or, at its tile, the exit it names). Returns "arrived", "used", "unreachable",
        "failed", or the step's kind."""
        found = self.where(look)
        if found is None:
            return "lost"
        memory, here = found
        if here == target.tile:
            if target.exit is None:
                return "arrived"
            return (yield from self.use_exit(target, why))
        walls = self.walls(memory, here)
        path = astar(memory, here, {target.tile}, walls, self.grass_cost, self.noise_for(target))
        if path is None:
            return "unreachable"
        direction = path[0]
        nxt = moved(here, direction)
        fact = memory.fact(nxt)
        seen = "unseen" if fact is None else f"seen {fact.behavior}{' (tall grass)' if fact.grass else ''}"
        gate = (f"walk {direction}: {here} -> {nxt} ({seen}), toward the {target.kind} at {target.tile}; the player free "
                f"(no script, no text, no menu, no fade)")
        result = yield from self.walk_step(direction, why, gate)
        if result.kind == "person":
            yield from self.hands.pad.idle(PERSON_WAIT // 3, f"someone is in the way at {result.detail}: letting them pass")
        return result.kind

    def run(self, intent: Intent, why: str) -> Generator[None, None, str]:
        """Pursue `intent` until it is done, stuck, or out of frames (module docstring)."""
        hands, world, pad = self.hands, self.world, self.hands.pad
        start = pad.frames
        first = hands.look()
        novelty = Novelty(world, first)
        self.excluded = set()
        self._seen_changes = len(world.transitions)
        uses: dict[str, list[int]] = {}
        target: Target | None = None
        detour: Target | None = None
        here_map = world.current
        if here_map is not None:
            self.entry.setdefault(here_map, world.position)
        self.tell(f"intent {intent.name!r}: budget {intent.budget} frames; on {self._map_name()} at {world.position}; "
                  f"{world.tiles_learned} tiles known on {len(world.maps)} maps")
        still, last_frames = 0, -1
        while True:
            if pad.frames - start >= intent.budget:
                return f"budget: {intent.budget} frames ran out ({self.summary()})"
            # never a loop that lets no frame pass: decisions that keep failing without a press are a dead end too
            still = still + 1 if pad.frames == last_frames else 0
            last_frames = pad.frames
            if still > STILL_DECISIONS:
                return f"stuck: {still} decisions in a row without a frame passing (every target fails at once) ({self.summary()})"
            look = hands.look()
            clock = novelty.last
            novel = novelty.update(look)
            if novelty.notable:
                self.tell(f"novelty at f{look.frame}: {'; '.join(novelty.notable)}: progress (the intent's clock f{clock} -> "
                          f"f{novelty.last})", {"novelty": list(novelty.notable), "clock": [clock, novelty.last]})
            for change in self.new_changes():
                self.arrived(change, look)
                if change.how == "warp" and change.tile is not None:
                    uses.setdefault(f"{change.source}|{change.tile[0]},{change.tile[1]}", []).append(change.frame)
                target = detour = None
            if novel and world.current != here_map:
                here_map = world.current
                memory = world.here()
                yield from pad.idle(pad.think_frames(), f"taking in a new place: {memory.const if memory else here_map}")
            if intent.done(look):
                return f"done: {intent.name} ({self.summary()})"
            if not nav_free(look):
                stop = yield from self.handle(look, why)
                if stop is not None:
                    return stop
                continue
            if look.frame - novelty.last >= intent.novelty_window:
                return (f"stuck: nothing new (no new tile, map, flag, Pokemon, item or experience) for {look.frame - novelty.last} "
                        f"frames, the last at f{novelty.last}: {novelty.events[-1][1] if novelty.events else 'none'} ({self.summary()})")
            for name, frames in uses.items():
                if len(frames) >= PINGPONG_USES and novelty.last <= frames[1]:
                    return (f"stuck: ping-pong: the warp {name} used {len(frames)} times (f{frames[0]}..f{frames[-1]}) "
                            f"with nothing new since its second use, f{frames[1]} ({self.summary()})")
            if target is None:
                target = intent.choose(self, look)
                if target is None:
                    return f"stuck: nothing left to try on {self._map_name()} (no frontier, no exit, no target) ({self.summary()})"
                if self.is_excluded(target):
                    return f"stuck: the {target.kind} at {target.tile} cannot be reached, and nothing else is wanted ({self.summary()})"
                detour = self._detour(target, look)
                self._decided(target, look, detour)
                yield from pad.idle(pad.think_frames(), f"deciding where to go: the {target.kind} at {target.tile} ({target.reason})")
                continue
            going = detour if detour is not None else target
            result = yield from self.toward(going, look, why)
            if going is detour and result in ("arrived", "unreachable"):
                detour = None
                continue
            if result in ("arrived", "used"):
                if intent.reached is not None:
                    intent.reached(target)
                target = None
            elif result in ("unreachable", "failed", "strayed"):
                self.exclude(target)
                self.tell(f"the {target.kind} at {target.tile} cannot be reached that way ({result}): another target")
                target = detour = None
            elif result == "lost":
                yield from pad.busy("finding the player's tile again")

    def _map_name(self) -> str:
        memory = self.world.here()
        return (memory.const or memory.name or memory.key) if memory is not None else "?"

    def _detour(self, target: Target, look: Observation) -> Target | None:
        """Now and then (`DETOUR_P`, seeded) a small detour through a seen tile beside the way."""
        found = self.where(look)
        if found is None or self.rng.random() >= DETOUR_P:
            return None
        memory, here = found
        path = astar(memory, here, {target.tile}, self.walls(memory, here), self.grass_cost, allow_unknown=False)
        if path is None or len(path) < 6:
            return None
        middle, tile = len(path) // 2, here
        for direction in path[:middle]:
            tile = moved(tile, direction)
        options = [moved(tile, d) for d in DIRECTIONS] + [moved(moved(tile, d), d) for d in DIRECTIONS]
        options = [xy for xy in options if memory.passable(xy) and xy != here]
        if not options:
            return None
        self.stats.detours += 1
        return Target("detour", self.rng.choice(sorted(options)), f"a small detour on the way to the {target.kind}")

    def go_to(self, tile: tuple[int, int], why: str, budget: int) -> Generator[None, None, str]:
        """Walk to `tile` of the current map (one target, its own bounded intent)."""
        goal = Target("goto", tile, f"walk to {tile}")
        reached: list[bool] = []
        intent = Intent(f"walk to {tile}", budget, lambda nav, look: None if reached else goal,
                        lambda look: bool(reached), lambda target: reached.append(True))
        return (yield from self.run(intent, why))

    def _decided(self, target: Target, look: Observation, detour: Target | None) -> None:
        found = self.where(look)
        memory, here = found if found is not None else (None, None)
        fact = memory.fact(target.tile) if memory is not None else None
        self.stats.decisions += 1
        extra = {"map": self.world.current, "player": list(here) if here else None, "target": list(target.tile),
                 "kind": target.kind, "exit": list(target.exit) if target.exit else None, "direction": target.direction,
                 "score": round(target.score, 2), "known": fact is not None,
                 "seen_from": list(fact.seen_from) if fact is not None else None,
                 "in_window": bool(here is not None and in_window(here, target.tile)),
                 "detour": list(detour.tile) if detour else None, "personality": self.personality}
        self.hands.note("decide", f"target {target.kind} {target.tile}", target.reason, extra)
        self.tell(f"go to the {target.kind} at {target.tile}{' then use it pressing ' + target.direction if target.exit else ''}"
                  f": {target.reason} (score {target.score:.1f}{'; a detour by ' + str(detour.tile) if detour else ''})")
