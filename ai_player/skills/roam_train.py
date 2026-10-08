"""SKILL: TRAINING BY ROAMING (build step 3; HUMAN-PLAY-DESIGN pillar 3, design draft §2.3 "roaming, not spinning",
§6 criterion 9).

WHAT THE USER ASKED FOR: "not spinning in place but running through areas that spawn pokemon like grass, sand or
water". The story bot trains with `_story_spin` (`modules/story/early_game.py`), walking in place on one tile: the
counter-example. A person walks THROUGH a grass patch, covering it, turning at its edges, and meets wild Pokemon on
the way.

HOW: the roaming AREA is the tall grass the AI has SEEN (its own memory, `world/memory.py`) and the walkable rim
around it (where a person turns at the grass's edge); if it has seen none yet it explores, with a grass-loving taste,
until it has (bounded). It walks to the nearest grass tile (the navigator), then takes `steps` TRAINING STEPS, each one
tile, chosen among the walkable neighbours in the area by:
    - 2 x how often it has stood there (cover the patch: least visited first)
    + 1 if it is grass        + 0.8 if it keeps the direction (a person walks lines, not zigzags)
    + 0.3 x the ways on from it, - 3 if there is none (no walking into a corner it must come back out of)
    - 1.5 next to a person (they walk into the way)   + a seeded jitter < 1
and NEVER the tile it just came from, unless that is the only way (a dead end; when the only way on is a PERSON, it
first waits up to `PERSON_WAIT` frames for them to step aside: the seed sweep's only reversals on Route 101 were at
the corner where its boy wanders). When the best step is a tile it has
already stood on `HOP_VISITS` times (this part is walked through), it HOPS: it walks the shortest seen way to grass it
has not stood on yet (the other side of the meadow, another patch in sight). A wild battle met on the way is fled
(`skills/flee.py`, until step 4's battle decider) and the walk goes on from where it stood. Measured 2026-10-08 on
Route 101 (`route101_south.ss1`, seed 3): without the hop the walk stayed in one 20-tile patch (25 distinct tiles in
120 steps, 4 spins = 3.3%: dead ends and a person); with it, 84 distinct tiles in 150 steps, 1 spin.

THE METRICS (design draft §7, criterion 9), logged and returned:
  * TRAINING STEPS (`steps`): steps that MOVED the player, the ones that ran into a wild battle included (in Emerald
    the encounter is rolled on the tile just stepped onto, so the step is taken; the walk resolves it once the battle
    is fled, from where the player then stands). ATTEMPTS (`attempts`): every training step PRESSED, moved or not,
    interrupted or not: exactly the `roam ...` gates in the action log.
  * SPIN RATIO: SPINS (a training step that did not move the player: walking in place; or one that moved it back onto
    the tile it stood on two steps before: back and forth on the same 1-2 tiles) over TRAINING STEPS, the smaller
    denominator (the stricter ratio); `spin_ratio_of_attempts` is also reported. Must stay < 2%.
    Until the step-3 verifier (2026-10-08) a step that ran into a battle was left out of BOTH counts (150 steps, 163
    presses), and the walk's "the tile it came from" went stale across the battle.
  * DISTINCT TILES covered; the MOST-VISITED tile's count; encounters met and fled.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field

from ai_player.brain.explore import explore_intent
from ai_player.brain.navigator import Navigator, astar, nav_free
from ai_player.hands.pad import Hands
from ai_player.skills.flee import in_battle
from ai_player.world.memory import DIRECTIONS, MapMemory, moved

__all__ = ["FIND_GRASS_BUDGET", "HOP_VISITS", "PERSON_LOOK", "PERSON_WAIT", "RoamReport", "patch_of", "roam_train",
           "spin_count"]

#: Frames the skill may spend finding grass it has not seen yet.
FIND_GRASS_BUDGET = 6000
#: A tile stood on this often in this roam is walked through: the walk heads for grass not walked yet.
HOP_VISITS = 3
#: How long the walk waits for a person in its only way on to step aside (looking every PERSON_LOOK frames).
PERSON_WAIT = 120
PERSON_LOOK = 15


@dataclass
class RoamReport:
    steps: int = 0  # training steps taken (the player moved; a step that ran into a battle included)
    attempts: int = 0  # training steps pressed (moved or not, interrupted or not): the `roam ...` gates
    spins: int = 0
    distinct: int = 0
    most_visited: int = 0
    encounters: int = 0
    fled: int = 0
    interrupted: int = 0  # training steps a battle or a scene began on (resolved once the player was free again)
    path: list = field(default_factory=list)  # every tile stood on after a training step

    @property
    def spin_ratio(self) -> float:
        """Spins over TRAINING STEPS (the moved ones): the stricter of the two ratios."""
        return self.spins / self.steps if self.steps else 0.0

    @property
    def spin_ratio_of_attempts(self) -> float:
        return self.spins / self.attempts if self.attempts else 0.0

    def line(self) -> str:
        return (f"roam: {self.steps} training steps ({self.attempts} pressed, {self.interrupted} ran into a battle or a "
                f"scene), {self.distinct} distinct tiles, spin ratio {self.spin_ratio:.4f} ({self.spins} spins / "
                f"{self.steps} steps; {self.spin_ratio_of_attempts:.4f} of the {self.attempts} pressed), the most-visited "
                f"tile {self.most_visited} times, {self.encounters} wild encounters, {self.fled} fled")


def spin_count(path: list[tuple[int, int]], not_moved: int = 0) -> int:
    """SPINS in a walk: steps back onto the tile of two steps before (A -> B -> A), plus the steps that did not move."""
    return not_moved + sum(1 for i in range(2, len(path)) if path[i] == path[i - 2])


def patch_of(memory: MapMemory, start: tuple[int, int]) -> set[tuple[int, int]]:
    """The connected tall grass (4-neighbours) around `start`, as far as it has been seen."""
    if not (memory.fact(start) is not None and memory.fact(start).grass):
        return set()
    patch, queue = {start}, [start]
    while queue:
        here = queue.pop()
        for direction in DIRECTIONS:
            nxt = moved(here, direction)
            fact = memory.fact(nxt)
            if nxt not in patch and fact is not None and fact.grass and memory.passable(nxt):
                patch.add(nxt)
                queue.append(nxt)
    return patch


def _finish(report: RoamReport, visits: dict, not_moved: int) -> None:
    report.spins = spin_count(report.path, not_moved)
    report.distinct = len(set(report.path))
    report.most_visited = max(visits.values(), default=0)


def _area(memory: MapMemory, patch: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """The patch and the walkable rim around it (where a person turns at the patch's edge)."""
    rim = {moved(xy, d) for xy in patch for d in DIRECTIONS}
    return patch | {xy for xy in rim if memory.passable(xy) and not memory.outside(xy)}


def roam_train(hands: Hands, nav: Navigator, steps: int, why: str = "train by roaming through the grass") -> Generator[None, None, str]:
    """Take `steps` training steps through a grass patch (module docstring). Returns "roamed: <metrics>" or a reason."""
    world, pad = nav.world, hands.pad
    report = RoamReport()
    look = hands.look()
    # 1. grass it has seen; otherwise explore (a grass-loving taste) until it has
    memory = world.here()
    if memory is None or not memory.grass():
        hands.say("[AI-WORLD] roam: no tall grass seen yet: exploring for some")
        intent = explore_intent(None, "Catcher", FIND_GRASS_BUDGET,
                                done=lambda l: bool(world.here() is not None and world.here().grass()))
        outcome = yield from nav.run(intent, f"{why}: find grass")
        if not outcome.startswith("done"):
            return f"roam: no grass found: {outcome}"
    # 2. walk to the nearest grass tile
    look = hands.look()
    found = nav.where(look)
    if found is None:
        return "roam: the player's tile is not known"
    memory, here = found
    path = astar(memory, here, set(memory.grass()), nav.walls(memory, here), 0.0, allow_unknown=False)
    if path is None:
        return "roam: no seen grass can be reached"
    goal = here
    for direction in path:
        goal = moved(goal, direction)
    if goal != here:
        outcome = yield from nav.go_to(goal, f"{why}: to the grass at {goal}", FIND_GRASS_BUDGET)
        if not outcome.startswith("done"):
            return f"roam: could not reach the grass at {goal}: {outcome}"
    look = hands.look()
    memory, here = nav.where(look)
    patch = patch_of(memory, here)
    hands.say(f"[AI-WORLD] roam: in a grass patch of {len(patch)} seen tiles at {here} on {memory.const}; "
              f"{steps} training steps")
    hands.note("decide", f"roam {steps} steps", f"a grass patch of {len(patch)} tiles", {"patch": sorted(patch), "start": list(here)})
    # 3. the training steps
    previous: tuple[int, int] | None = None
    heading: str | None = None
    hop: tuple[int, int] | None = None
    waited = 0
    visits: dict[tuple[int, int], int] = {here: 1}
    report.path.append(here)
    not_moved = 0
    #: (map, the tile it was pressed from, its direction) of a training step a battle or a scene began on
    pending: tuple[str | None, tuple[int, int], str] | None = None
    for _ in range(4 * steps):
        if report.steps >= steps:
            break
        look = hands.look()
        nav.take_changes()
        if not nav_free(look):
            battle = in_battle(look)
            stop = yield from nav.handle(look, why)
            if battle:
                report.encounters += 1
                report.fled += 1 if stop is None else 0
            if stop is not None:
                _finish(report, visits, not_moved)
                return f"roam: {stop}; {report.line()}"
            continue
        found = nav.where(look)
        if found is None:
            yield from pad.busy("finding the player's tile again")
            continue
        memory, here = found
        if pending is not None:
            # the step a battle (or a scene) interrupted, resolved now the player is free: did it move the player?
            # (an encounter is rolled on the tile just stepped onto, so it normally did: a training step, and the tile
            # it was pressed from is the one not to step straight back to)
            frm_map, frm, frm_direction = pending
            pending = None
            if (nav.world.current, here) != (frm_map, frm):
                report.steps += 1
                waited = 0
                previous, heading = frm, frm_direction
                visits[here] = visits.get(here, 0) + 1
                report.path.append(here)
            continue
        grass = set(memory.grass())
        area = _area(memory, grass)
        walls = nav.walls(memory, here)
        options = []
        for direction in DIRECTIONS:
            nxt = moved(here, direction)
            if nxt not in area or nxt in walls or not memory.passable(nxt):
                continue
            onward = sum(1 for d in DIRECTIONS if moved(nxt, d) in area and moved(nxt, d) != here
                         and memory.passable(moved(nxt, d)) and moved(nxt, d) not in walls)
            near_person = any(abs(o[0] - nxt[0]) + abs(o[1] - nxt[1]) <= 2 for o in walls)
            fact = memory.fact(nxt)
            score = (-2.0 * visits.get(nxt, 0) + (1.0 if fact is not None and fact.grass else 0.0)
                     + (0.8 if direction == heading else 0.0) + 0.3 * onward - (3.0 if onward == 0 else 0.0)
                     - (1.5 if near_person else 0.0) + nav.rng.uniform(0.0, 1.0))
            options.append((score, direction, nxt))
        forward = [o for o in options if o[2] != previous]
        # A PERSON in the only way on (a child wandering in the grass): wait a moment for them to step aside rather than
        # turn straight back (measured 2026-10-08, the seed sweep: every reversal on Route 101 was at the corner where its
        # boy wanders, (2,13) / (4,13)); after PERSON_WAIT frames, turn back.
        blocked = [moved(here, d) for d in DIRECTIONS if moved(here, d) in area and moved(here, d) != previous
                   and moved(here, d) in walls and memory.passable(moved(here, d))]
        if not forward and blocked and waited < PERSON_WAIT:
            yield from pad.idle(PERSON_LOOK, f"someone stands in the way at {blocked[0]}: letting them pass")
            waited += PERSON_LOOK
            continue
        choice = max(forward or options, key=lambda o: (o[0], o[1])) if options else None
        # HOP: this part of the patch is walked through (the best step is a tile stood on HOP_VISITS times or more), or
        # the player stands outside it: head for grass not walked yet, as a person crosses to the other side of a meadow
        if hop is not None and (hop == here or visits.get(hop, 0) > 0 or hop not in grass):
            hop = None
        if hop is None and (choice is None or visits.get(choice[2], 0) >= HOP_VISITS):
            fresh = {xy for xy in grass if visits.get(xy, 0) == 0}
            way = astar(memory, here, fresh, walls, 0.0, allow_unknown=False) if fresh else None
            if way:
                hop = here
                for d in way:
                    hop = moved(hop, d)
        step = None
        if hop is not None:
            way = astar(memory, here, {hop}, walls, 0.0, allow_unknown=False)
            if way and moved(here, way[0]) != previous:
                step = (way[0], moved(here, way[0]), f"on the way to grass not walked yet at {hop}")
        if step is None and choice is not None:
            step = (choice[1], choice[2], "tall grass" if memory.fact(choice[2]).grass else "the edge of the grass")
        if step is None:
            _finish(report, visits, not_moved)
            return f"roam: nowhere to step from {here}; {report.line()}"
        direction, nxt, why_step = step
        gate = f"roam {direction}: {here} -> {nxt} ({why_step}, stood there {visits.get(nxt, 0)} times), the player free"
        key = nav.world.current
        result = yield from nav.walk_step(direction, why, gate)
        report.attempts += 1
        if result.kind in ("battle", "scene", "changed"):
            # handled at the top of the next loop, then resolved from where the player stands (`pending`)
            report.interrupted += 1
            pending = (key, here, direction)
            continue
        now = result.to if result.kind == "moved" else nav.world.position
        if now is not None and now != here:
            report.steps += 1
            waited = 0
            previous, heading = here, direction
            visits[now] = visits.get(now, 0) + 1
            report.path.append(now)
        else:
            # the player did not move and nothing else happened: walking in place (a bump, a person in the way)
            not_moved += 1
    _finish(report, visits, not_moved)
    hands.say(f"[AI-WORLD] {report.line()}")
    hands.note("roam", "metrics", report.line(), {"path": [list(xy) for xy in report.path], "spins": report.spins,
                                                  "attempts": report.attempts, "steps": report.steps,
                                                  "interrupted": report.interrupted, "not_moved": not_moved,
                                                  "spin_ratio": round(report.spin_ratio, 6),
                                                  "spin_ratio_of_attempts": round(report.spin_ratio_of_attempts, 6),
                                                  "distinct": report.distinct, "encounters": report.encounters,
                                                  "fled": report.fled, "most_visited": report.most_visited})
    return f"roamed: {report.line()}"
