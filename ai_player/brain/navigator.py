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

BUILD STEP 3.1 (the step-3 adversarial review), each rule with its proof in `gates/test_world.py` and a mutant in
`gates/revert_step3.py`:
  * A STALE TARGET IS DROPPED (finding 2): a frontier target with nothing unseen beside it any more (the walk there
    showed it), or tall grass already walked, is given up AT ONCE and the next place chosen from where the player
    stands, on the move (no thinking pause: a person who sees there is nothing over there just turns). It used to be
    kept until it was reached, which walked the player onto a spot it no longer needed and straight back (TOWN
    "(11,7) -> (12,7) -> (12,6) -> (11,6)", ROUTE "(17,9) -> (18,9) -> (17,9)").
  * A SCENE THAT KEEPS INTERRUPTING ONE TARGET (finding 3): every scene met on the way to a target is counted for that
    target; at `SCENE_REPEATS` with nothing new since the first, the target is given up (Littleroot's twin pushes a
    player with no Pokemon back from the road every time: the same scene again and again until the novelty window, ~50 s).
    AND (the step-3.1 verifier: the rule was proven on a scripted errand only; on targets the EXPLORER chose, measured
    2026-10-08 from `littleroot_twin.ss1`, it gave one frontier tile up after two scenes, then chose the next tile behind
    the same twin, and the novelty window ended it, 3 to 5 scenes on): a scene is also counted for the TILE it began on
    when it put the player somewhere else (a push back). At `SCENE_REPEATS` such scenes on one tile, nothing new since the
    first, that tile is not stepped on again in the intent (`scene_walls`: a person who has been sent back from a spot
    twice stops walking onto it), so every target behind it is out of reach and the explorer looks elsewhere. "Nothing
    new" here is PROGRESS only (`Novelty.last_progress`: a story flag, a Pokemon, items, experience): a tile that came on
    screen while the scene pushed the player back is no reason to walk into it again (the measured seed 4 met the twin
    4 times for ONE target that way). Progress during the intent lifts every such tile (the twin lets a trainer pass).
    AND (the step-3.1 verifier's second round: "the twin guards two tiles, so the explorer meets her 4 times in total
    before it gives up the road north"): a scene is known by its WORDS (`scene_words`: the first page it waited on, as
    the eyes read it), the way a person knows "the same girl said the same thing again". `SCENE_REPEATS` scenes with the
    same words on one map that each put the player elsewhere, nothing new since the first, and EVERY tile that scene
    began on is not stepped on again in the intent (`scene_words` -> `scene_walls`). Measured on the twin (live arm
    SCENEX, seed 3): twice on (10, 1), then once on (11, 1), where the same words close both: 3 meetings in all, where
    counting per tile took 4 (twice a tile). The third is the side-step a person makes to the next tile of the road; a
    tile the scene never began on is not guessed at. A scene with no words (nothing waited for a press) is still
    counted per tile.
  * A BUMP BELONGS TO ONE SIDE (finding 4): `step_from` refuses a tile only from the side it was bumped from
    (`BUMP_GIVE_UP` bumps), after one bump it costs `BUMP_RETRY_COST` more from that side (tried again only when every
    other way is dearer), and it is open from the others: a one-way tile is crossed the way it lets the player through.
  * AN EXIT IS USED THE WAY IT LOOKS (finding 5): an arrow mat by pressing its arrow, a door by walking into it from
    below (`exit_press`); one that takes the player nowhere when used so is remembered CLOSED (`WorldMemory.close_exit`).

BUILD STEP 3.2 (the step-3.1 adversarial review: human-likeness regressions its metrics could not see), each rule with its
proof in `gates/test_world.py` and a mutant in `gates/revert_step3.py`:
  * THE TURN-BACK COST ONCE PER DECISION, THEN THE PLAN IS FOLLOWED (its HIGH finding 1): `TURN_BACK_COST` was charged on
    EVERY replan, so each step forward made going back dearer again and the AI walked LAPS (SCENEX: 10 steps round the
    corner of Littleroot where 2 would do; measured 2026-10-08 with the memory of that moment: at (6, 18) heading left,
    the plan to the door's stand tile (7, 17) was down, right, up, up (4 steps, the 2-step way charged +4), and at the
    next tile, charged again, left, up, right, right, up). Now turning round is charged once, by the DECISION: in WHERE
    to go (the explorer's scores, `TURN_BACK_COST`; on the move also the heading: `brain/explore.py`), and in the first
    plan made for that target (`Plan.charged`), there only `TURN_ROUND_COST`, a tie-breaker between about-equal ways
    (a 4-tile charge in the plan bought its way round: measured, `TURN_ROUND_COST`). That plan is FOLLOWED
    (`Navigator._next_step`): redone only when the memory says it no longer goes (a wall seen, a bump, someone standing
    on it, the player not where it expected), uncharged, and dropped for a fresh one only when that is clearly better
    (`PLAN_SWITCH_MARGIN` tiles cheaper: a shortcut that came into view). A target behind is reached the short way: a
    person who has decided to go back turns round.
  * A BUMP IS FORGOTTEN WHEN THE WAY OPENS (its MEDIUM finding 3): a step that moves the player into a tile going `d`
    deletes that tile's bump for `d` (`WorldMemory.forget_bump`, told); a tile whose look changes drops its bumps
    (`MapMemory.absorb`).
  * NO RANDOM PICK ON THE MOVE (its MEDIUM finding 4): a target chosen while walking (one dropped as stale) is chosen
    with the HEADING (`heading`, `choosing_on_the_move`: `brain/explore.py` pick_on_the_move), not on a whim.
  * ONE DECISION, NOT ONE PER STEP (the step-4 verifier's FAILURE: finding 4 "is NOT fixed", the targets still churned: a
    frontier at the screen's edge is seen past at the next step, and each such stale target was a new decision): a stale
    target is CARRIED ON by the same decision (`Intent.carry_on`, `brain/explore.py` carry_on: the place it meant moved on
    with the view), told with where the step-3.2 rule would have gone instead (`carry_note`); a new decision on the move
    only when nothing of it is left there or something clearly better came into view. Its plan stays uncharged
    (`planned_for` is kept: the same decision).

STEP 4.1 ROUND 2 (the step-4 review's finding 7: "the churn fix mostly relabels decisions ... FIX the re-targeting so the
walk itself gets closer to the shortest known way"; its verifier: the first fix, a charge on a place chosen on the move for
what its journey walked beyond the shortest way from where it began, helped TOWN-Trainer and made TOWN-Catcher worse on
both seed sets, because it was a pull AWAY FROM WHERE THE JOURNEY BEGAN that only happened to point at Littleroot's exit; it
is gone). The walk's own waste was measured instead, seed by seed (development sweeps of 2026-10-09, seeds 1-10 and
101-110), and each cause is fixed where it arises, with its proof in `gates/test_world.py` and a mutant in
`gates/revert_step3.py`:
  * THE TRAINER WALKS UP TO PEOPLE (`brain/explore.py`: the explorer's PEOPLE place; `Target.who`, `stale_reason`): the
    pull toward people used to be a bonus on UNSEEN tiles near them, which vanished as soon as the player came close
    enough to see those tiles, so the Trainer walked toward someone, stopped short and turned back across town for the next
    one (with the pull off, its journeys were 0.09 of their steps beyond the shortest known way instead of 0.45: the pull
    WAS the waste). A person who wants to meet people walks up to them, once: met (`world/memory.py` MEET_RADIUS), a
    person is no place to go any more; `MEET_TRIES` walks after one who keeps walking off, then they are left alone.
  * A PERSON IN THE WAY IS WAITED FOR, NOT WALKED ROUND BACKWARDS (`_next_step`, `PERSON_AHEAD`, `PERSON_PLAN_WAITS`):
    someone standing on the plan being followed FURTHER ON than `PERSON_AHEAD` steps does not break it (people walk on);
    someone on the next steps is waited for, at most `PERSON_PLAN_WAITS` times a plan, before the plan is redone. MEASURED:
    the sweep's TOWN seed 102 stepped straight back twice for a person who had stepped into the way (14, 18) -> (13, 18),
    (16, 10) -> (16, 9): 3 reversals in a run where the bound is 2.
  * A DETOUR BENDS THE WAY, IT DOES NOT GO OUT AND BACK (`_detour`, `DETOUR_EXTRA`): the detour's tile lies on a way at
    most `DETOUR_EXTRA` steps longer than the plan (it was any tile 1 or 2 from the way's middle: TOWN seed 102 went 2
    tiles aside and straight back, (13, 9) -> (12, 9) -> (13, 9)).
"""

from __future__ import annotations

import heapq
import random
from collections.abc import Callable, Generator
from dataclasses import dataclass, field

from ai_player.eyes.observation import Observation
from ai_player.eyes.screens import page_text
from ai_player.hands.dialogue import advance, busy_reason, player_free
from ai_player.hands.menus import answer_yes_no
from ai_player.hands.pad import Hands
from ai_player.skills.flee import TRAINER_OUT_OF_SCOPE, flee, in_battle
from ai_player.world.memory import BUMP_GIVE_UP, DIRECTIONS, OPPOSITE, MapMemory, WorldMemory, in_window, moved

__all__ = [
    "BUMP_RETRY_COST",
    "BUTTONS",
    "CHUNK_FRAMES",
    "DETOUR_EXTRA",
    "DETOUR_P",
    "EXIT_PRESS",
    "MEET_TRIES",
    "PERSON_AHEAD",
    "PERSON_PLAN_WAITS",
    "NOVELTY_WINDOW",
    "PINGPONG_USES",
    "PLAN_SWITCH_MARGIN",
    "SCENE_REPEATS",
    "SEARCH_MARGIN",
    "STEP_HOLD_MAX",
    "TURN_BACK_COST",
    "TURN_ROUND_COST",
    "UNKNOWN_COST",
    "WARP_HOLD_MAX",
    "Intent",
    "Navigator",
    "Novelty",
    "Plan",
    "StepResult",
    "Target",
    "astar",
    "distances",
    "exit_press",
    "is_scene",
    "nav_free",
    "path_cost",
    "scene_words",
    "stale_reason",
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
#: (step 4.1 round 2, finding 7) A detour's tile lies on a way at most this many steps longer than the plan (Manhattan:
#: here -> the tile -> the target): one tile aside of the way and on, never two aside and straight back.
DETOUR_EXTRA = 2
#: (step 4.1 round 2, finding 7) Someone standing on the plan being followed further on than this many steps does not
#: break it (people walk on: the plan is looked at again as the player comes up); someone on the next steps does.
PERSON_AHEAD = 2
#: (step 4.1 round 2) How often a plan waits for someone standing on its next steps (`PERSON_WAIT` // 3 frames each)
#: before it is redone round them.
PERSON_PLAN_WAITS = 2
#: (step 4.1 round 2) How many decisions to walk up to ONE person (`brain/explore.py` PEOPLE places) before that person is
#: left alone for the rest of the intent (someone who keeps walking off).
MEET_TRIES = 2
#: (step 4.1 round 2) What `_next_step` answers when the way is free but for someone on its next steps: wait for them.
WAIT = "wait"
#: (build step 3.1, finding 4) What entering a tile from a side it was bumped from once costs on top (in tiles of
#: walking): a way round up to this much longer is taken first; the side is refused at `BUMP_GIVE_UP` bumps.
BUMP_RETRY_COST = 10.0
#: (build step 3.1, finding 3) Scenes met on the way to ONE target, with nothing new since the first, before it is given up;
#: and (the step-3.1 verifier's round) scenes that began on ONE tile and put the player elsewhere before that tile is not
#: stepped on again in the intent.
SCENE_REPEATS = 2
#: (build step 3.1, finding 2) What turning BACK costs on the first step of a plan (in tiles of walking): straight back
#: the way the last step came, or back the way of the step before when that one was a turn (the third step of a
#: U-turn). A person keeps going rather than turn round, and turns round when the way ahead is clearly worse. MEASURED
#: 2026-10-08 on the grid model's town (`gates/test_world.py` ReversalTests, 12 seeds): dropping stale targets alone
#: re-decided on the move toward places behind as often as ahead (28 reversals in 677 steps, against 12 in 788 before).
TURN_BACK_COST = 4.0
#: (build step 3.2, the step-3.1 review's finding 1) What turning round costs in a DECISION'S PLAN (in tiles of walking):
#: one tile, a TIE-BREAKER between about-equal ways (step on, then up, rather than up, then on), never a reason to walk
#: further. MEASURED 2026-10-08 (in-process, pinned clock, seeds 1-10 of HOUSE, TOWN, ROUTE, SCENEX): with the plan
#: charged `TURN_BACK_COST` (4) once per decision, the plan still bought its way round the charge: a U round one tile
#: where turning back was 2 steps (SCENEX seed 3, Brendan's 1F (6,3) -> (5,3) -> (5,2) -> (6,2)), and a step FORWARD and
#: straight back (Birch's lab (6,6) -> (6,5) -> (6,6), a charge on the first step only): SCENEX 70 steps beyond the
#: shortest ways in 10 seeds. Where to GO is still chosen with `TURN_BACK_COST` (the explorer's scores) and, on the move,
#: with the heading (`brain/explore.py` pick_on_the_move).
TURN_ROUND_COST = 1.0
#: (build step 3.2, the step-3.1 review's finding 1) How much cheaper (in tiles of walking) a fresh plan must be than what
#: is left of the plan being followed before the AI changes its way on the move: a shortcut that came into view (unseen
#: tiles that turn out to be floor) is taken; a way about as good is not (no dithering between equal ways).
PLAN_SWITCH_MARGIN = TURN_BACK_COST
#: (build step 3.1, finding 5) The press an exit's LOOK asks for (`eyes/view.py` behaviour names): an arrow mat warps when
#: its arrow is pressed while stood on (`src/field_control_avatar.c` IsArrowWarpMetatileBehavior), an animated door only
#: when walked into going north (TryDoorWarp). Stairs, ladders, escalators and holes warp when stepped on: any side.
EXIT_PRESS: dict[str, str] = {
    "SOUTH_ARROW_WARP": "down", "WATER_SOUTH_ARROW_WARP": "down", "SHOAL_CAVE_ENTRANCE": "down",
    "NORTH_ARROW_WARP": "up", "EAST_ARROW_WARP": "right", "WEST_ARROW_WARP": "left",
    "ANIMATED_DOOR": "up", "PETALBURG_GYM_DOOR": "up",
}
#: Bounds.
SETTLE_BUDGET = 900  # frames a map change may take to settle
PERSON_WAIT = 90  # frames to let a person in the way move on
SCENE_TURNS = 8  # menus a scene may raise before it is given up
STILL_DECISIONS = 50  # decisions in a row with no frame passing: a dead end


def nav_free(look: Observation) -> bool:
    """The player can walk: on the map, nothing running, nothing on screen, no fade, a view to walk by."""
    return player_free(look) and not look.screen.fading and look.view is not None


def _party_hp(look: Observation | None) -> list[int] | None:
    """(build step 5) [HP, max HP] of the party as the eyes show it (eggs left out), for a battle's record; None unread."""
    if look is None or look.party is None:
        return None
    mons = [m for m in look.party if not m.is_egg]
    return [sum(max(0, m.hp) for m in mons), sum(m.max_hp for m in mons)]


def is_scene(look: Observation) -> bool:
    """Something on screen holds the player: a script runs, the controls are locked, a text or a menu is up (not a
    battle, not a fade alone)."""
    screen = look.screen
    return (screen.script_running or screen.controls_locked or screen.waits_for_button or screen.text_box_open
            or screen.ui is not None)


def scene_words(pages: list[str | None]) -> str | None:
    """(the step-3.1 verifier's second round) What a person remembers a scene by: its WORDS, the first page it waited on
    for a press (`eyes/screens.py` page_text, whitespace folded), or None when nothing on screen waited (a scene with no
    text is remembered by the tile it began on only)."""
    for page in pages:
        words = " ".join((page_text(page) or "").split())
        if words:
            return words
    return None


def exit_press(behavior: str) -> str | None:
    """The one press an exit's look asks for (`EXIT_PRESS`), or None: any side (stepped onto)."""
    return EXIT_PRESS.get(behavior)


def stale_reason(memory: MapMemory, target: "Target") -> str | None:
    """Why a chosen target is no longer worth walking to, by what the AI has seen since it chose it (build step 3.1,
    finding 2), or None: a FRONTIER tile with nothing unseen beside it any more, TALL GRASS already walked, (step 4.1 round
    2) a PERSON already met."""
    if target.kind == "frontier" and memory.known(target.tile) and not memory.unknown_neighbours(target.tile):
        return "everything beside it has been seen on the way"
    if target.kind == "grass" and memory.visits.get(target.tile):
        return "it has been walked already"
    # (step 4.1 round 2, finding 7) a person walked up to: met on the way (`world/memory.py` MEET_RADIUS)
    if target.kind == "people" and target.who is not None and target.who in memory.met:
        return "the player has been beside them: met"
    return None


def step_from(memory: MapMemory, xy: tuple[int, int], direction: str, walls: frozenset | set, grass_cost: float,
              allow_unknown: bool = True) -> tuple[tuple[int, int], float] | None:
    """Where one press of `direction` from `xy` leads, and its cost, as far as the AI knows; None if it knows it cannot.
    `walls`: tiles to treat as blocked now (people and things standing there). A tile bumped from THIS side costs
    `BUMP_RETRY_COST` more after one bump and is refused after `BUMP_GIVE_UP` (build step 3.1): other sides are open."""
    nxt = moved(xy, direction)
    if nxt in walls:
        return None
    tried = memory.bumps(nxt, direction)
    if tried >= BUMP_GIVE_UP:
        return None
    retry = BUMP_RETRY_COST if tried else 0.0
    fact = memory.fact(nxt)
    if fact is None:
        return (nxt, UNKNOWN_COST + retry) if allow_unknown else None
    if fact.ledge is not None:
        if fact.ledge != direction:
            return None
        land = moved(nxt, direction)  # a ledge is jumped: the player lands one tile beyond it
        landing = memory.fact(land)
        if land in walls or memory.bumps(land, direction) >= BUMP_GIVE_UP or (landing is not None and not landing.walkable):
            return None
        return land, 2.0 + retry
    if not fact.walkable:
        return None
    return nxt, 1.0 + (grass_cost if fact.grass else 0.0) + retry


def _bounds(memory: MapMemory, start: tuple[int, int], goals: set | None = None) -> tuple[int, int, int, int]:
    """The box a plan may search: the known tiles, the start and the goals, plus `SEARCH_MARGIN` of the unknown."""
    xs = [x for x, _ in memory.tiles] + [start[0]] + [x for x, _ in goals or ()]
    ys = [y for _, y in memory.tiles] + [start[1]] + [y for _, y in goals or ()]
    return min(xs) - SEARCH_MARGIN, max(xs) + SEARCH_MARGIN, min(ys) - SEARCH_MARGIN, max(ys) + SEARCH_MARGIN


def _turn_extra(first: dict | None, phase, direction: str) -> float:
    """The turning-round charge of one step of a plan (`Navigator.turn_costs`): `phase` "start" for its first step (a
    direction key), a direction for its second step (the pair (first, second): a U-turn the plan completes itself),
    None beyond (build step 3.2)."""
    if not first or phase is None:
        return 0.0
    return float(first.get(direction if phase == "start" else (phase, direction), 0.0))


def _next_phase(first: dict | None, phase, direction: str):
    """(build step 3.2) Where a plan stands in its first steps after one more (only a charged plan keeps track)."""
    if not first:
        return None
    return direction if phase == "start" else None


def astar(memory: MapMemory, start: tuple[int, int], goals: set[tuple[int, int]], walls: frozenset | set,
          grass_cost: float, noise: Callable[[tuple[int, int]], float] | None = None,
          allow_unknown: bool = True, first: dict | None = None) -> list[str] | None:
    """The cheapest way (a list of directions) from `start` to any of `goals` over what the AI knows; None if none.
    `noise(tile)` (>= 0) varies the cost per tile; the heuristic (Manhattan, every step costs >= 1) stays admissible.
    `first`: the charge for TURNING ROUND on the plan's first steps (`Navigator.turn_costs`): per direction for the
    first step, and (build step 3.2) per (first, second) direction pair for the second (a U-turn the plan completes
    itself: the old rule charged it at the next REPLAN, which it no longer is). A search node is a tile and how far
    into its first steps the plan is (`_next_phase`), so a cheaper way to a tile that turned round is not mistaken for
    one that did not."""
    if start in goals:
        return []
    low_x, high_x, low_y, high_y = _bounds(memory, start, goals)

    def h(xy: tuple[int, int]) -> int:
        return min(abs(xy[0] - g[0]) + abs(xy[1] - g[1]) for g in goals)

    origin = (start, "start" if first else None)
    best: dict = {origin: 0.0}
    came: dict = {}
    queue: list = [(float(h(start)), 0, origin)]
    order = 0
    while queue:
        _, _, node = heapq.heappop(queue)
        here, phase = node
        if here in goals:
            path = []
            while node != origin:
                node, direction = came[node]
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
            cost += _turn_extra(first, phase, direction)
            total = best[node] + cost
            after = (nxt, _next_phase(first, phase, direction))
            if total < best.get(after, float("inf")):
                best[after] = total
                came[after] = (node, direction)
                order += 1
                heapq.heappush(queue, (total + h(nxt), order, after))
    return None


def distances(memory: MapMemory, start: tuple[int, int], walls: frozenset | set, grass_cost: float,
              first: dict | None = None) -> dict[tuple[int, int], float]:
    """The cheapest cost from `start` to every tile it can reach (known or not, within the search bounds). `first`: as
    `astar`'s (the charge for turning round on the first steps)."""
    low_x, high_x, low_y, high_y = _bounds(memory, start)
    origin = (start, "start" if first else None)
    best: dict = {origin: 0.0}
    queue: list = [(0.0, 0, origin)]
    order = 0
    while queue:
        cost, _, node = heapq.heappop(queue)
        if cost > best.get(node, float("inf")):
            continue
        here, phase = node
        for direction in ("up", "down", "left", "right"):
            step = step_from(memory, here, direction, walls, grass_cost)
            if step is None:
                continue
            nxt, extra = step
            if not (low_x <= nxt[0] <= high_x and low_y <= nxt[1] <= high_y):
                continue
            extra += _turn_extra(first, phase, direction)
            total = cost + extra
            after = (nxt, _next_phase(first, phase, direction))
            if total < best.get(after, float("inf")):
                best[after] = total
                order += 1
                heapq.heappush(queue, (total, order, after))
    out: dict[tuple[int, int], float] = {}
    for (xy, _), value in best.items():
        if value < out.get(xy, float("inf")):
            out[xy] = value
    return out


def in_map_walls(memory: MapMemory, walls: frozenset, target_tile: tuple[int, int] | None) -> frozenset:
    """(build step 5.2; KI-129 Part A, 2026-10-31, factored out of `Navigator._next_step` with no change) A tile of THIS
    map is walked to over tiles of this map: once an edge has been seen crossed (`memory.edges`), the tiles SEEN past it
    are the next map's, and a walk through them crosses onto it. So for a target on this map (`target_tile` not past an
    edge, or None: any tile of this map, `Navigator.cut_off`'s reach) they are walls; a target past an edge (a road)
    still crosses it. ONE rule for "can it get there?": the planner that walks and the reach that says what is left to
    see (`WorldMemory.promise`) agree."""
    if memory.edges and (target_tile is None or not memory.outside(target_tile)):
        walls = walls | frozenset(xy for xy in memory.tiles if memory.outside(xy))
    return walls


def path_cost(memory: MapMemory, start: tuple[int, int], path: list[str] | None, walls: frozenset | set, grass_cost: float,
              noise: Callable[[tuple[int, int]], float] | None = None) -> float | None:
    """(build step 3.2) What walking `path` from `start` costs as far as the AI knows NOW (the costs `astar` plans with, no
    turn-back charge), or None when the memory says it no longer goes (a wall seen, a side bumped twice, someone
    standing on it)."""
    if path is None:
        return None
    here, total = start, 0.0
    for direction in path:
        step = step_from(memory, here, direction, walls, grass_cost)
        if step is None:
            return None
        here, cost = step
        total += cost + (noise(here) if noise is not None else 0.0)
    return total


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
    #: (step 4.1 round 2, finding 7) a PEOPLE place: who it is for (the person's id on this map, `MapMemory.persons`)
    who: int | None = None

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.tile}:{self.exit}:{self.direction}"


@dataclass
class Plan:
    """(build step 3.2) The way the AI decided to walk to one target: the steps left (`path`), from the tile `at` on map
    `map`; `charged`: the plan was made with the turn-back cost (the decision's own plan, the only one that is)."""

    key: str
    map: str | None
    at: tuple[int, int]
    path: list[str]
    charged: bool
    #: (step 4.1 round 2) how often it has waited for someone standing on its next steps (`PERSON_PLAN_WAITS`)
    waits: int = 0


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
    #: (build step 3.2, the step-4 verifier's finding 4) `carry_on(navigator, look, stale)`: the same decision carried on
    #: past a target the walk made stale (`brain/explore.py` carry_on), or None: a new decision is made on the move
    carry_on: Callable[["Navigator", Observation, Target], Target | None] | None = None


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
        #: (the step-3.1 verifier's round) the frame of the newest novelty that is NOT a place (a story flag, a Pokemon,
        #: items, experience): what a scene must have brought to be "something new" (`Navigator._scene_met`)
        self.last_progress = look.frame
        self.events: list[tuple[int, str]] = []
        self.notable: list[str] = []
        #: (the step-3.1 verifier's second round) the WORDS of every scene heard in the intent (`scene_words`, `heard`)
        self.words: set[str] = set()

    def heard(self, words: str | None, frame: int) -> bool:
        """(the step-3.1 verifier's second round) A scene whose WORDS were never heard before in the intent is PROGRESS,
        dated at the frame the scene began: a person who is told something new has learned something (May's "Who are
        you?" in her house: the story moved on, and the road the twin guarded may be open now; measured 2026-10-08 from
        `littleroot_twin.ss1`: meeting May sets no flag the eyes call a story flag, so the explorer never tried the twin
        again and stopped in May's house "nothing new"). The same words again are not progress (the twin's second
        "Um, um, um!"). The navigator asks only for a scene that left the player where it found them: a scene that SENT
        the player back or away is an obstacle, not news (a second person's new words at the next tile do not make the
        first one let the player pass). True when they were new."""
        if not words or words in self.words:
            return False
        self.words.add(words)
        self.last = max(self.last, frame)
        self.last_progress = max(self.last_progress, frame)
        self.events.append((frame, f"new words heard: {words[:40]!r}"))
        return True

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
        if self.notable:
            self.last_progress = look.frame
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
    #: (build step 3.2) plans redone because the memory said the plan no longer went, and fresh plans taken because they
    #: were clearly better (`Navigator._next_step`)
    replans: int = 0
    switches: int = 0
    #: (build step 3.2, the step-4 verifier's finding 4) stale targets CARRIED ON by the same decision (`Intent.carry_on`)
    carried: int = 0


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
        #: "map|target key" -> why: targets that failed in the current intent (`exclude`)
        self.excluded: dict[str, str] = {}
        #: "map|target key" -> the frames of the scenes met on the way to it, in the current intent (build step 3.1)
        self.scene_hits: dict[str, list[int]] = {}
        #: (the step-3.1 verifier's round) "map|x,y" -> the frames of the scenes that began on that tile and put the player
        #: elsewhere, and map -> the tiles not stepped on again in the current intent because of them (`walls`)
        self.scene_spots: dict[str, list[int]] = {}
        self.scene_walls: dict[str, set[tuple[int, int]]] = {}
        #: (the step-3.1 verifier's second round) "map|words" -> the frames of the scenes with those WORDS that put the
        #: player elsewhere, and the tiles they began on (`scene_words`; every one walled at `SCENE_REPEATS`)
        self.scene_said: dict[str, dict] = {}
        #: (build step 5.2) every target given up because a scene stopped the way there, as (map key, tile, why), over ALL
        #: intents (never reset: the goal runner reads the ones its goal added, `GoalRunner.pursue`)
        self.scene_given_up: list[tuple[str, tuple[int, int], str]] = []
        #: (build step 5.2, the verifier's round; its development sweep step52vdev2, CH1 seed 1209: a detour past OLDALE's
        #: footprints man ended at his "Wait! Please don't come in here.", and the look round "some more" that followed walked
        #: OLDALE for 2,003 frames toward the same corner, nothing new) every tile a scene BEGAN on that put the player
        #: elsewhere, as (map key, tile, why), over ALL intents (never reset): the goal runner blocks the ones a curiosity
        #: walk met for curiosity in the milestone (`GoalRunner.pursue`)
        self.scene_turned: list[tuple[str, tuple[int, int], str]] = []
        self.stats = _Stats()
        self.entry: dict[str, tuple[int, int]] = {}  # map -> where the AI came into it (the explorer's "away")
        #: (build step 3.1) the AI's own last steps that moved the player, as (map, direction): the HEADING a plan's
        #: first step is measured against (`turn_costs`)
        self.recent: list[tuple[str | None, str]] = []
        #: (build step 3.2, the step-3.1 review's finding 1) the plan being followed, and the key of the target (or detour)
        #: the current DECISION's plans were made for (None: a decision not yet planned: its first plan pays the turn-back
        #: cost, every later one of the same decision does not)
        self.plan: Plan | None = None
        self.planned_for: str | None = None
        #: (build step 3.2, its finding 4) True while the intent chooses a target ON THE MOVE (a target dropped as stale):
        #: the explorer then keeps the heading and picks no whim (`brain/explore.py` pick_on_the_move)
        self.choosing_on_the_move = False
        #: (build step 3.2, the step-4 verifier's finding 4) places the current decision has carried on to, and what the last
        #: carry-on said (`brain/explore.py` carry_on: "refused" why not, or "would": where the step-3.2 rule would have gone)
        self.carries = 0
        self.carry_note: dict = {}
        #: (step 4.1 round 2, finding 7) "map|person id" -> the decisions made to walk up to that person in the current
        #: intent (`MEET_TRIES`)
        self.people_tries: dict[str, int] = {}
        self._noise: dict[str, tuple[float, dict[tuple[int, int], float]]] = {}
        self._seen_changes = len(world.transitions)
        #: BUILD STEP 4: who plays a battle met on the way. None (the step-3 world brains): a wild battle is FLED
        #: (`skills/flee.py`) and a trainer's ends the intent. The battle brain sets a callable that plays it with the
        #: decider (`skills/battle.py` play_battle) and returns the game's outcome.
        self.battler: Callable[[], Generator[None, None, str]] | None = None
        #: BUILD STEP 4: the battles the battler played, by outcome; and after how many the intent is DONE (None: never)
        self.battle_outcomes: list[str] = []
        self.battle_limit: int | None = None
        #: BUILD STEP 4: asked after each battle the battler played, whenever it is set: a reason to stop training now (the
        #: party needs a Pokemon Center: `brain/battle.py` needs_rest), or None. The battle brain sets it together with
        #: the limit (its training); since build step 5 (the step-5 verifier, 2026-10-14) it is asked with NO limit too:
        #: the play brain's training roam sets it alone, and until then the rule was never asked there (a dead fix).
        self.battle_rest: Callable[[Observation], str | None] | None = None
        #: BUILD STEP 5 (the play brain, `ai_player/mode.py`): who ANSWERS a yes/no in a scene, `answer(look) -> (yes, why)`
        #: (`skills/story.py` answer_question: by its words, as a person goes along with the story). None (the step-3 and
        #: step-4 brains): NO, "an explorer agrees to nothing it does not know", exactly as before.
        self.answer: Callable[[Observation], tuple[bool, str]] | None = None
        #: BUILD STEP 5: who plays ANOTHER menu a scene raises, `on_menu(kind, why)` -> a generator returning True when it
        #: was played (PROF. BIRCH's bag: `choose_starter`). None (the earlier brains): the intent stops, as before.
        self.on_menu: Callable[[str, str], Generator[None, None, bool]] | None = None
        #: BUILD STEP 5.1: tiles a scene sent the player back from in EARLIER intents (map key -> tiles), which an intent
        #: starts from instead of nothing (`run`): the play brain carries them from goal to goal within one milestone
        #: (`brain/goals.py` GoalRunner.pursue). None (every earlier brain): each intent starts with none, as before.
        self.carried_scene_walls: dict[str, set[tuple[int, int]]] | None = None
        #: BUILD STEP 5: every battle the battler played, as (the frame it began, its kind "wild" / "trainer" as the eyes
        #: first showed it DURING the battle, its outcome): what the goal manager counts as training and the play brain as
        #: battles lost (`brain/goals.py` battles_lost)
        self.battle_log: list[tuple[int, str, str]] = []
        #: BUILD STEP 5: asked on every free look while roaming (`skills/roam_train.py`): a reason to stop the roam now (an
        #: item ball came into view: a person walks over to it), or None. None (the earlier brains): roam as before.
        self.roam_stop: Callable[[Observation], str | None] | None = None
        #: BUILD STEP 5.2 (the verifier's round: the graded NOHINTS runs, 20 of 20, went through OLDALE's house door for up
        #: to 98 goals in a row, each ended by the ping-pong rule, which counts the uses of ONE intent: the next goal's
        #: intent started from none) "map key|x,y" of a warp that ENDED an intent as a ping-pong -> the world's `stamp`
        #: then: while nothing new has been seen anywhere since, no later intent goes through it again unless it is the only
        #: way left (`brain/explore.py` candidates, `ponged_now`). None (every earlier brain): each intent on its own, as
        #: before; the play brain sets {}.
        self.ponged: dict[str, tuple] | None = None
        #: BUILD STEP 5.2 (the verifier's round) at every decision, the frontier tiles and unused exits of the map that the
        #: reach from where the player stands shows no way to are marked in the world memory (`cut_off`), so a map's
        #: `promise` holds only what it could get to (OLDALE_TOWN_HOUSE1's two unreachable tiles were "2 things left to see"
        #: for ever). False (every earlier brain): as before; the play brain sets True.
        self.mark_cut = False

    # ------------------------------------------------------------------ telling
    def tell(self, line: str, extra: dict | None = None) -> None:
        self.hands.say(f"[AI-WORLD] {line}")
        self.hands.note("world", "say", line, extra)

    def summary(self) -> str:
        s = self.stats
        return (f"{s.steps} steps, {s.bumps} bumps, {s.people} people in the way, {s.exits_used} exits used, "
                f"{s.battles} battles, {s.scenes} scenes, {s.decisions} decisions ({s.detours} detours, {s.carried} carried on); "
                f"{len(self.world.maps)} maps, {self.world.tiles_learned} tiles learned")

    # ------------------------------------------------------------------ looking
    def where(self, look: Observation) -> tuple[MapMemory, tuple[int, int]] | None:
        memory = self.world.here()
        player = look.player
        if memory is None or player is None or player.x is None:
            return None
        return memory, (player.x, player.y)

    def walls(self, memory: MapMemory, here: tuple[int, int]) -> frozenset:
        """Tiles not to step on now: where someone stands, and (the step-3.1 verifier's round) a tile a repeating scene
        sent the player back from in this intent (`scene_walls`)."""
        return frozenset((memory.objects_now | self.scene_walls.get(memory.key, set())) - {here})

    def ponged_now(self, target: Target) -> bool:
        """(build step 5.2, the verifier's round) Does `target` go through a warp that ended an earlier intent as a ping-pong,
        with nothing new seen anywhere since (`ponged`, `WorldMemory.stamp`)?"""
        if self.ponged is None or target.exit is None:
            return False
        return self.ponged.get(f"{self.world.current}|{target.exit[0]},{target.exit[1]}") == self.world.stamp()

    def story_moved(self) -> str:
        """(build step 5.2, the verifier's round; step52vdev1, chapter-1 seed 1201: given up at the start of a milestone over
        a road the milestone before had cut off) The play brain's milestone changed: the ping-pongs kept (`ponged`) and the
        world memory's marks of what it could not get to (`WorldMemory.forget_marks`) are forgotten, so the new milestone
        looks again. Told, and returned."""
        pongs = len(self.ponged or {})
        if self.ponged is not None:
            self.ponged.clear()
        marks = self.world.forget_marks()
        said = f"the story moved on: {pongs} ping-pong(s) and {marks} place(s) it could not get to forgotten"
        self.tell(said)
        return said

    def _remember_pingpong(self, name: str) -> None:
        """(build step 5.2, the verifier's round) The warp `name` ended this intent as a ping-pong: kept past it (`ponged`),
        with what the world memory had seen then, so no later intent goes through it again while nothing new is seen
        anywhere (`ponged_now`). Off for the earlier brains (`ponged` None)."""
        if self.ponged is not None:
            self.ponged[name] = self.world.stamp()

    def _seen_out(self, target: Target, result: str) -> None:
        """(build step 5.2, the verifier's round: OLDALE's MART kept two frontier tiles whose unseen side the screen never
        shows, "2 things left to see" for ever) a walk ARRIVED on a frontier tile and the unseen beside it stayed unseen:
        nothing more is to be seen from it while the map shows nothing new: marked like a frontier no walk found a way to
        (`WorldMemory.mark_unreached`: out of `promise`; `brain/goals.py` lost_intent leaves it out) and given up for the
        intent. Off for the earlier brains (`mark_cut`)."""
        memory = self.world.here()
        if (self.mark_cut and result == "arrived" and target.kind == "frontier" and memory is not None
                and target.tile in memory.frontier()):
            self.world.mark_unreached(memory.key, target.tile)
            self.exclude(target, "arrived: the unseen beside it stayed unseen")

    def cut_off(self, look: Observation) -> list[tuple[int, int]]:
        """(build step 5.2, the verifier's round) The frontier tiles and unused exits of the map the player stands on that
        its reach shows NO way to (the navigator's own `distances`, over known and unknown tiles, round the scene walls and
        what lies on the ground; never round the people, who walk on; and, KI-129 Part A, never through the tiles seen past
        a crossed edge, the planner's own rule, `in_map_walls`), marked in the world memory (`mark_cut_off`) so the
        map's `promise` is only what it could get to. Off unless `mark_cut` (the earlier brains)."""
        if not self.mark_cut:
            return []
        found = self.where(look)
        if found is None:
            return []
        memory, here = found
        # (KI-129 Part A, 2026-10-31) the reach goes over tiles of THIS map only, by the planner's own rule
        # (`in_map_walls`): the frontier and the exits are inside the map by definition, and the planner that walks to
        # one never plans through the tiles seen past a crossed edge. Measured on the A0-1 end memory from (39, 63) on
        # ROUTE 104: the old reach went round through PETALBURG's tiles to the strip behind the ledge at x 32-33, y 42-47,
        # so nothing was cut, ROUTE 104 kept "something left to see" that no walk could get to, and the walk crossed the
        # PETALBURG edge back and forth for the rest of the run
        walls = in_map_walls(memory, self.walls(memory, here) - memory.people_now, None)
        reach = distances(memory, here, walls, self.grass_cost)
        cut = [xy for xy in memory.frontier() if xy not in reach]
        for xy in memory.exits():
            if self.world.link_of(memory.key, xy) is None and not any(
                    moved(xy, direction) in reach and memory.passable(moved(xy, direction)) for direction in DIRECTIONS):
                cut.append(xy)
        self.world.mark_cut_off(memory.key, cut)
        return cut

    def exclude(self, target: Target, why: str = "") -> None:
        """`target` failed on the current map, for the rest of the intent (a tile is a tile of ONE map)."""
        self.excluded[f"{self.world.current}|{target.key}"] = why

    def is_excluded(self, target: Target) -> bool:
        return f"{self.world.current}|{target.key}" in self.excluded

    def why_excluded(self, target: Target) -> str:
        return self.excluded.get(f"{self.world.current}|{target.key}") or "unreachable"

    def turn_costs(self, cost: float | None = None) -> dict:
        """(build step 3.1, finding 2) The charge for TURNING ROUND on a way's first steps, `cost` each: a FIRST step
        straight back the way the last step came, or back the way of the step before when the last step was a turn (a
        U-turn's third step); and (build step 3.2) a SECOND step that completes a U-turn the way begins itself (keyed by
        the pair (first, second): a step aside, then back against the heading). Only steps on the current map count (a
        map change starts afresh). Charged once per DECISION (build step 3.2): `TURN_BACK_COST` in where to go (the
        explorer's scores), `TURN_ROUND_COST` in the decision's first plan (`_next_step`)."""
        steps = [direction for key, direction in self.recent if key == self.world.current]
        if not steps:
            return {}
        cost = TURN_BACK_COST if cost is None else cost
        out: dict = {OPPOSITE[steps[-1]]: cost}
        if len(steps) >= 2 and steps[-2] not in (steps[-1], OPPOSITE[steps[-1]]):
            out.setdefault(OPPOSITE[steps[-2]], cost)
        for aside in DIRECTIONS:
            if aside not in (steps[-1], OPPOSITE[steps[-1]]):
                out[(aside, OPPOSITE[steps[-1]])] = cost
        return out

    def heading(self) -> str | None:
        """(build step 3.2) The way the player is walking: the direction of its last step on the current map (None: it
        has not stepped here yet, or it stopped at a target: arriving clears the heading, `run`)."""
        steps = [direction for key, direction in self.recent if key == self.world.current]
        return steps[-1] if steps else None

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
        key = self.world.current
        result = yield from self._walk(direction, why, gate)
        self.world.settle_intent()
        if result.kind == "moved":
            self.recent = (self.recent + [(key, direction)])[-2:]
            # (build step 3.2, the step-3.1 review's finding 3: "a bump is never forgotten after walking through that way")
            # the way into this tile going `direction` let the player through: a bump learned there that way is forgotten
            entered = [moved(result.frm, direction)]
            if result.to is not None and result.to not in entered:
                entered.append(result.to)  # a ledge: the tile jumped and the tile landed on
            for tile in entered:
                info = self.world.forget_bump(key, tile, direction)
                if info is not None:
                    self.tell(f"the way into {tile} moving {direction}, learned blocked by {info.get('bumps')} bump(s) "
                              f"(f{info.get('first')}..f{info.get('last')}), let the player through now: forgotten",
                              {"forgot_bump": list(tile), "direction": direction, "map": key, "info": info})
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
        count = memory.bumps(tile, direction) if tile is not None else 0
        self.tell(f"BUMP: moving {direction} from {frm} on {memory.const or memory.key} did not move the player: {tile} "
                  f"is learned blocked moving {direction} (bump {count} from this side: "
                  f"{'refused from now on' if count >= BUMP_GIVE_UP else 'dear from now on, tried again only if every other way is dearer'}; "
                  f"the other sides stay open) (the eyes showed {fact.behavior if fact else 'an unseen tile'}"
                  f"{', elevation %d' % fact.elevation if fact else ''}; held {held} frames)",
                  {"bump": list(tile), "from": list(frm), "direction": direction, "map": memory.key, "count": count})
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
        asked = exit_press(fact.behavior) if fact is not None else None
        if asked is None or asked == direction:
            # used the way it looks (its arrow, a door from below, stairs stepped onto) and nothing happened: a person
            # remembers a door that does not open (build step 3.1, finding 5: learned by using it)
            world.close_exit(exit_tile, f"pressed {direction} from {frm} for {held} frames", look.frame)
            self.tell(f"the {what} at {exit_tile} did not take the player anywhere pressing {direction} from {frm} "
                      f"({held} frames), the way it looks to be used: remembered CLOSED")
        else:
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
            if self.battler is not None:  # BUILD STEP 4: the battle brain fights it
                # BUILD STEP 5 (the step-5 verifier, 2026-10-14): the battle's KIND as the eyes first show it during the
                # battle. On its first frame the battle view does not exist yet, so a kind read here alone was "?" for
                # every battle (and the goal manager's count of wild battles in training was always 0): a watcher on the
                # hands' looks takes the first battle view the battler's own looks show. It presses nothing.
                kinds: list[str] = [look.battle.kind] if look.battle is not None else []
                start_party = _party_hp(look)

                def watch(seen: Observation) -> None:
                    if not kinds and seen.battle is not None:
                        kinds.append(seen.battle.kind)

                self.hands.watchers.append(watch)
                try:
                    outcome = yield from self.battler()
                finally:
                    self.hands.watchers.remove(watch)
                kind = kinds[0] if kinds else "?"
                self.battle_outcomes.append(outcome)
                self.battle_log.append((look.frame, kind, outcome))
                self.tell(f"battle {len(self.battle_outcomes)}: {outcome}",
                          {"battle": len(self.battle_outcomes), "kind": kind, "outcome": outcome, "began": look.frame,
                           "party_hp_start": start_party, "party_hp_end": _party_hp(self.hands.last)})
                if outcome == "lost":
                    return "stuck: the battle was lost (the party fainted: the player whited out)"
                if outcome.startswith("the battle") or outcome.startswith("stuck"):
                    return f"stuck: {outcome}"
                if self.battle_limit is not None and len(self.battle_outcomes) >= self.battle_limit:
                    return f"done: {len(self.battle_outcomes)} battle(s) played: {self.battle_outcomes}"
                rest = self.battle_rest(self.hands.look()) if self.battle_rest is not None else None
                if rest is not None:
                    return f"rest: {rest}: a person stops training here and looks for a Pokemon Center"
                return None
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
                if self.answer is not None:  # BUILD STEP 5: the play brain answers by the question's words
                    yes, because = self.answer(self.hands.last)
                    answered = yield from answer_yes_no(self.hands, yes, f"{why}: {because}")
                else:
                    answered = yield from answer_yes_no(self.hands, False, f"{why}: a question in a scene: NO (an explorer agrees to nothing it does not know)")
                if not answered:
                    return "stuck: a yes/no in a scene could not be answered"
                continue
            if outcome.startswith("menu:"):
                if self.on_menu is not None and (yield from self.on_menu(outcome[5:], why)):
                    continue  # BUILD STEP 5: a menu the play brain knows (PROF. BIRCH's bag)
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
            self.plan = None
            if target.exit is None:
                return "arrived"
            return (yield from self.use_exit(target, why))
        walls = self.walls(memory, here)
        direction = self._next_step(memory, here, target, walls)
        if direction is None:
            return "unreachable"
        if direction == WAIT:
            # (step 4.1 round 2, finding 7) someone stands on the next steps of the way being followed: let them pass
            self.stats.people += 1
            yield from self.hands.pad.idle(PERSON_WAIT // 3, f"someone stands in the way on the next steps toward the "
                                                             f"{target.kind} at {target.tile}: letting them pass")
            return "person"
        nxt = moved(here, direction)
        expected = step_from(memory, here, direction, walls, self.grass_cost)
        fact = memory.fact(nxt)
        seen = "unseen" if fact is None else f"seen {fact.behavior}{' (tall grass)' if fact.grass else ''}"
        gate = (f"walk {direction}: {here} -> {nxt} ({seen}), toward the {target.kind} at {target.tile}; the player free "
                f"(no script, no text, no menu, no fade)")
        result = yield from self.walk_step(direction, why, gate)
        plan = self.plan
        if plan is not None and plan.key == target.key and result.kind == "moved":
            if expected is not None and result.to == expected[0] and plan.path and plan.path[0] == direction:
                plan.path.pop(0)
                plan.at = result.to
            else:
                self.plan = None  # the step took the player somewhere the plan did not expect: plan again (uncharged)
        if result.kind == "person":
            yield from self.hands.pad.idle(PERSON_WAIT // 3, f"someone is in the way at {result.detail}: letting them pass")
        return result.kind

    def _next_step(self, memory: MapMemory, here: tuple[int, int], target: Target, walls: frozenset) -> str | None:
        """(build step 3.2, the step-3.1 review's finding 1) The next press toward `target`: the plan being FOLLOWED while
        the memory says it still goes from where the player stands, unless a fresh plan is clearly better
        (`PLAN_SWITCH_MARGIN` cheaper: a shortcut came into view); otherwise a new plan. Only the FIRST plan of a decision
        (`planned_for` None: a target just chosen, its detour included) pays the turn-back cost: a person who decides on
        the move where to go may keep going round rather than turn back, but does not decide it again at every step (the
        old rule did: each step forward made turning back dearer again, and the AI walked laps). None: no way known.
        (Step 4.1 round 2, finding 7) PEOPLE ON THE WAY: someone standing on the followed plan further on than
        `PERSON_AHEAD` steps does not break it (they walk on); someone on its next steps, with the way otherwise free, is
        waited for (`WAIT`), at most `PERSON_PLAN_WAITS` times a plan, before it is redone round them."""
        noise = self.noise_for(target)
        plan, current = self.plan, self.world.current
        # (build step 5.2, found by the pushing property in the round's development sweep step52dev4, chapter-2 seed 1026:
        # 3,372 frames of pressing with nothing new, 30 and more crossings of OLDALE's top edge) a tile of THIS map is walked
        # to over tiles of this map: the tiles SEEN past an edge it has crossed are the next map's, and a plan through them
        # crosses onto it (the frontier at (25, 15) on ROUTE 103 was planned through OLDALE's tiles below the edge; on
        # OLDALE the explorer chose "the road up, back to ROUTE 103", and round again). A target past an edge (a road)
        # still crosses it. (KI-129 Part A) the rule is `in_map_walls`, shared with `cut_off`'s reach.
        walls = in_map_walls(memory, walls, target.tile)
        if plan is not None and plan.key == target.key and plan.map == current and plan.at == here and plan.path:
            near, tile = set(), here
            for direction in plan.path[:PERSON_AHEAD]:
                tile = moved(tile, direction)
                if tile in memory.people_now:
                    near.add(tile)
            kept = self.scene_walls.get(memory.key, set())
            further = memory.people_now - near - kept
            left = path_cost(memory, here, plan.path, walls - further, self.grass_cost, noise)
            if (left is None and near and plan.waits < PERSON_PLAN_WAITS
                    and path_cost(memory, here, plan.path, walls - (memory.people_now - kept), self.grass_cost, noise) is not None):
                plan.waits += 1
                return WAIT
            if left is not None:
                fresh = astar(memory, here, {target.tile}, walls, self.grass_cost, noise)
                better = path_cost(memory, here, fresh, walls, self.grass_cost, noise)
                if better is None or better + PLAN_SWITCH_MARGIN >= left:
                    return plan.path[0]
                self.stats.switches += 1
                self.plan = Plan(target.key, current, here, list(fresh), False)
                return fresh[0]
            self.stats.replans += 1
        charged = self.planned_for is None
        path = astar(memory, here, {target.tile}, walls, self.grass_cost, noise,
                     first=self.turn_costs(TURN_ROUND_COST) if charged else None)
        self.planned_for = target.key
        if not path:
            self.plan = None
            return None
        self.plan = Plan(target.key, current, here, list(path), charged)
        return path[0]

    def run(self, intent: Intent, why: str) -> Generator[None, None, str]:
        """Pursue `intent` until it is done, stuck, or out of frames (module docstring)."""
        hands, world, pad = self.hands, self.world, self.hands.pad
        start = pad.frames
        first = hands.look()
        novelty = Novelty(world, first)
        self.excluded = {}
        self.scene_hits = {}
        self.scene_spots, self.scene_walls, self.scene_said = {}, {}, {}
        if self.carried_scene_walls:
            self.scene_walls = {key: set(tiles) for key, tiles in self.carried_scene_walls.items()}
        self.plan, self.planned_for = None, None
        self.carries = 0
        self.people_tries = {}
        on_the_move = False  # a target just dropped as stale: the next one is chosen without a thinking pause
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
                # (the step-3.1 verifier's round) progress: a scene that sent the player back may let it pass now
                self._lift_scene_walls(novelty.last_progress)
            for frame, key, xy, why in world.take_reopened():
                self.tell(f"the door-looking tile {xy} on {self.world.names().get(key, key)}, found closed before, is worth a "
                          f"try again: {why}", {"reopened": list(xy), "map": key})
            # (build step 3.2, the step-3.1 review's finding 3) a tile whose look changed: what was learned by bumping it
            # was about the old tile
            for frame, key, xy, sides in world.take_dropped_bumps():
                self.tell(f"the tile {xy} on {self.world.names().get(key, key)} looks different now (f{frame}): the bumps "
                          f"learned there ({', '.join(sides)}) are forgotten", {"dropped_bumps": list(xy), "map": key,
                                                                               "directions": list(sides)})
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
                # (build step 3.1, finding 3) a scene met on the way to a target is counted for THAT target, and (the
                # step-3.1 verifier's round) for the tile it began on, when it puts the player somewhere else
                scene_key = (f"{world.current}|{target.key}" if target is not None and not in_battle(look) and is_scene(look)
                             else None)
                scene_map, player = world.current, look.player
                began = (player.x, player.y) if scene_key is not None and player is not None and player.x is not None else None
                # (the step-3.1 verifier's second round) the pages ANY scene waited on, as the eyes read them: its WORDS
                pages: list[str | None] = []

                def listen(seen: Observation) -> None:
                    if seen.screen.waits_for_button and seen.screen.text:
                        pages.append(seen.screen.text)

                hands.watchers.append(listen)
                try:
                    stop = yield from self.handle(look, why)
                finally:
                    hands.watchers.remove(listen)
                if stop is not None:
                    return stop
                after = world.position if world.current == scene_map else None
                words = scene_words(pages) if not in_battle(look) else None
                at = (player.x, player.y) if player is not None and player.x is not None else None
                # news, not an obstacle: a scene that sent the player back or away (the twin, Mom upstairs) is no progress
                stayed = at is not None and after == at
                ended = hands.last.frame if hands.last is not None else look.frame
                clock = novelty.last
                if stayed and novelty.heard(words, ended):
                    # new words are PROGRESS (`Novelty.heard`, dated when the scene ENDED: May's scene alone runs 3,500
                    # frames, longer than the novelty window): told like every novelty that is not a place, and a scene
                    # that sent the player back may let it pass now
                    self.tell(f"novelty at f{ended}: new words heard ({words[:60]!r}): progress (the intent's clock "
                              f"f{clock} -> f{novelty.last})", {"novelty": [f"new words heard: {words}"],
                                                                 "clock": [clock, novelty.last], "words": words})
                    self._lift_scene_walls(novelty.last_progress)
                if scene_key is not None and self._scene_met(scene_key, target, look.frame, novelty, scene_map, began, after,
                                                             words):
                    target = detour = None
                continue
            if look.frame - novelty.last >= intent.novelty_window:
                return (f"stuck: nothing new (no new tile, map, flag, Pokemon, item or experience) for {look.frame - novelty.last} "
                        f"frames, the last at f{novelty.last}: {novelty.events[-1][1] if novelty.events else 'none'} ({self.summary()})")
            for name, frames in uses.items():
                if len(frames) >= PINGPONG_USES and novelty.last <= frames[1]:
                    self._remember_pingpong(name)
                    return (f"stuck: ping-pong: the warp {name} used {len(frames)} times (f{frames[0]}..f{frames[-1]}) "
                            f"with nothing new since its second use, f{frames[1]} ({self.summary()})")
            if target is not None:
                # (build step 3.1, finding 2) a target the walk has made worthless is dropped at once, not walked onto
                memory = world.here()
                stale = stale_reason(memory, target) if memory is not None else None
                # (build step 3.2, the step-4 verifier's finding 4) the SAME decision carried on past it, when the place it
                # meant moved on with the view (`Intent.carry_on`); a new decision on the move only when nothing of it is left
                # there or something clearly better came into view (`carry_note` says which)
                self.carry_note = {}
                carried = intent.carry_on(self, look, target) if stale is not None and intent.carry_on is not None else None
                if carried is not None:
                    self.stats.carried += 1
                    self.carries += 1
                    would = self.carry_note.get("would")
                    self.tell(f"the {target.kind} at {target.tile} is seen past now ({stale}): the same decision carries on to "
                              f"the {carried.kind} at {carried.tile}, {abs(carried.tile[0] - target.tile[0]) + abs(carried.tile[1] - target.tile[1])} "
                              f"tile(s) on (no new choice; carried {self.carries} time(s)"
                              + (f"; the step-3.2 rule would have gone to {tuple(would)} now)" if would else ")"),
                              {"carry_on": list(carried.tile), "from": list(target.tile), "kind": carried.kind, "map": world.current,
                               "stale": stale, "carries": self.carries, "step32_would": would})
                    target = carried
                elif stale is not None:
                    why_not = self.carry_note.get("refused")
                    self.tell(f"the {target.kind} at {target.tile} is not worth going to any more: {stale}"
                              f"{'; ' + why_not if why_not else ''}; choosing again on the move",
                              {"stale": list(target.tile), "kind": target.kind, "map": world.current, "refused": why_not,
                               "carries": self.carries})
                    target = detour = None
                    on_the_move = True
            if target is None:
                # (build step 3.2, the step-3.1 review's finding 4) chosen ON THE MOVE: the heading kept, no whim
                self.choosing_on_the_move = on_the_move
                # (build step 5.2, the verifier's round) what this map holds that it cannot get to, before choosing
                self.cut_off(look)
                try:
                    target = intent.choose(self, look)
                finally:
                    self.choosing_on_the_move = False
                if target is None:
                    return f"stuck: nothing left to try on {self._map_name()} (no frontier, no exit, no target) ({self.summary()})"
                if self.is_excluded(target):
                    return (f"stuck: the {target.kind} at {target.tile} cannot be reached ({self.why_excluded(target)}), and "
                            f"nothing else is wanted ({self.summary()})")
                # (build step 3.2, its finding 1) a new DECISION: its first plan pays the turn-back cost, once
                self.plan, self.planned_for = None, None
                self.carries = 0
                detour = self._detour(target, look)
                self._decided(target, look, detour, on_the_move)
                if on_the_move:
                    on_the_move = False  # decided while walking: a person who sees there is nothing there just turns
                else:
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
                self._seen_out(target, result)
                target = None
                # arrived and stopping to decide: a person turns round freely there (an errand behind, a dead end); the
                # turn-back cost is for a plan changed ON THE MOVE (build step 3.1, finding 2)
                self.recent = []
            elif result in ("unreachable", "failed", "strayed"):
                self.exclude(target, result)
                if result == "unreachable" and target.kind == "frontier":
                    # (build step 5.2) no way known to it at all: not "left to see" on this map until it shows more
                    world.mark_unreached(world.current, target.tile)
                self.tell(f"the {target.kind} at {target.tile} cannot be reached that way ({result}): another target")
                target = detour = None
            elif result == "lost":
                yield from pad.busy("finding the player's tile again")

    def _lift_scene_walls(self, progress: int) -> None:
        """PROGRESS at frame `progress` (a story flag, a Pokemon, items, experience, or since the step-3.1 verifier's second
        round new words heard): a scene that sent the player back may let it pass now, so the tiles given up because of
        scenes are worth a try again, and so are the targets given up because of them (a scene stopped the way, or none
        could be reached once those tiles were walls: the second round, measured from `littleroot_twin.ss1`: every target
        past the twin was excluded, so lifting the tiles alone sent the explorer nowhere new). A scene known by its WORDS
        is not forgotten: met ONCE more with the same words and nothing new since this progress, every tile it began on is
        given up again at once (a person tries the road once after the news, not twice a tile: `_scene_met`)."""
        if not (self.scene_walls or self.scene_spots or any(said["frames"] for said in self.scene_said.values())):
            return
        lifted = {key: why for key, why in self.excluded.items() if why.startswith("a scene stopped") or why == "unreachable"}
        self.tell(f"progress: the tiles a scene sent the player back from are worth a try again "
                  f"({ {key: sorted(tiles) for key, tiles in self.scene_walls.items()} }), and {len(lifted)} target(s) given up "
                  f"because of them", {"lifted": {key: sorted(tiles) for key, tiles in self.scene_walls.items()},
                                       "targets": sorted(lifted), "progress": progress})
        self.scene_spots, self.scene_walls = {}, {}
        for said in self.scene_said.values():
            said["frames"], said["lifted"] = [], progress
        self.excluded = {key: why for key, why in self.excluded.items() if key not in lifted}

    def _scene_met(self, key: str, target: Target, frame: int, novelty: "Novelty", scene_map: str | None = None,
                   began: tuple[int, int] | None = None, after: tuple[int, int] | None = None,
                   words: str | None = None) -> bool:
        """A scene met on the way to `target` (its key on the map it was chosen on): counted; at `SCENE_REPEATS` with
        nothing new since the first, the target is given up (build step 3.1, finding 3). True when it was.
        (The step-3.1 verifier's round) `began`: the tile the player stood on when the scene began, `after`: where it
        left the player on the same map. A scene that put the player elsewhere is also counted for the tile it began on,
        and at `SCENE_REPEATS` such scenes there, nothing new since the first, that tile is not stepped on again in the
        intent (`scene_walls`). "Nothing new" is PROGRESS (`Novelty.last_progress`), not a tile seen in passing.
        (The step-3.1 verifier's second round) `words`: what the scene SAID (`scene_words`). Scenes with the same words on
        one map that put the player elsewhere are ONE scene met again, whichever tile each began on: at `SCENE_REPEATS`,
        nothing new since the first, every tile it began on is not stepped on again (a girl who guards a road two tiles
        wide is met at most 3 times in all, not twice a tile)."""
        hits = self.scene_hits.setdefault(key, [])
        hits.append(frame)
        self.tell(f"a scene stopped the way to the {target.kind} at {target.tile} (time {len(hits)} for this target)",
                  {"scene_for": list(target.tile), "kind": target.kind, "hits": list(hits), "began": list(began) if began else None,
                   "after": list(after) if after else None, "words": words})
        if began is not None and after is not None and after != began and scene_map is not None:
            spots = self.scene_spots.setdefault(f"{scene_map}|{began[0]},{began[1]}", [])
            spots.append(frame)
            self.scene_turned.append((scene_map, began, f"a scene began here and turned it back (f{frame})"))
            walled = self.scene_walls.setdefault(scene_map, set())
            if len(spots) >= SCENE_REPEATS and novelty.last_progress <= spots[0] and began not in walled:
                walled.add(began)
                self.tell(f"the tile {began} on {self.world.names().get(scene_map, scene_map)}: a scene there sent the player "
                          f"back {len(spots)} times (f{spots[0]}..f{spots[-1]}, to {after}) with nothing new since the first: "
                          f"not stepped on again in this intent", {"scene_wall": list(began), "map": scene_map,
                                                                   "scenes": list(spots)})
            if words is not None:
                said = self.scene_said.setdefault(f"{scene_map}|{words}", {"frames": [], "tiles": [], "lifted": None})
                said["frames"].append(frame)
                if began not in said["tiles"]:
                    said["tiles"].append(began)
                fresh = [tile for tile in said["tiles"] if tile not in walled]
                twice = len(said["frames"]) >= SCENE_REPEATS and novelty.last_progress <= said["frames"][0]
                # met again after the news that lifted it, and nothing new since that news: once is enough
                again = said["lifted"] is not None and novelty.last_progress <= said["lifted"]
                if fresh and (twice or again):
                    walled.update(fresh)
                    for tile in fresh:
                        self.tell(f"the tile {tile} on {self.world.names().get(scene_map, scene_map)}: the same scene "
                                  f"({words[:60]!r}) sent the player back "
                                  + (f"again after the news of f{said['lifted']}, nothing new since" if again and not twice
                                     else f"{len(said['frames'])} times (f{said['frames'][0]}..f{said['frames'][-1]}, from "
                                          f"{sorted(said['tiles'])}) with nothing new since the first")
                                  + ": not stepped on again in this intent",
                                  {"scene_wall": list(tile), "map": scene_map, "scenes": list(said["frames"]),
                                   "words": words, "same_scene_tiles": [list(t) for t in said["tiles"]],
                                   "after_news": said["lifted"] if again and not twice else None})
        if len(hits) >= SCENE_REPEATS and novelty.last_progress <= hits[0]:
            why = (f"a scene stopped the way there {len(hits)} times (f{hits[0]}..f{hits[-1]}) with nothing new since the "
                   f"first")
            self.excluded[key] = why
            self.scene_given_up.append((key.split("|", 1)[0], target.tile, why))
            self.tell(f"the {target.kind} at {target.tile}: {why}: given up", {"given_up": list(target.tile), "why": why})
            return True
        return False

    def _map_name(self) -> str:
        memory = self.world.here()
        return (memory.const or memory.name or memory.key) if memory is not None else "?"

    def _detour(self, target: Target, look: Observation) -> Target | None:
        """Now and then (`DETOUR_P`, seeded) a small detour through a seen tile beside the way. (Step 4.1 round 2, finding
        7) The tile bends the way: here -> it -> the target is at most `DETOUR_EXTRA` steps longer than the plan
        (Manhattan), so a detour is never two tiles aside and straight back."""
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
        goal = target.tile
        options = [xy for xy in options if memory.passable(xy) and xy != here
                   and abs(xy[0] - here[0]) + abs(xy[1] - here[1]) + abs(xy[0] - goal[0]) + abs(xy[1] - goal[1])
                   <= len(path) + DETOUR_EXTRA]
        if not options:
            return None
        self.stats.detours += 1
        return Target("detour", self.rng.choice(sorted(options)), f"a small detour on the way to the {target.kind}")

    def go_to(self, tile: tuple[int, int], why: str, budget: int) -> Generator[None, None, str]:
        """Walk to `tile` of the current map (one target, its own bounded intent). (Build step 5.2, found by the pushing
        property in the round's development sweep step52dev6, seed 1049: a training roam's walk to grass seen past OLDALE's
        bottom edge, (5, 23), crossed onto ROUTE 101, where (5, 23) lies past ITS bottom edge, then onto LITTLEROOT and back,
        3,313 frames of pressing with nothing new: a tile is a tile of the map it was chosen on) the walk ENDS when it
        leaves that map, and says so: "left the map"."""
        goal = Target("goto", tile, f"walk to {tile}")
        reached: list[bool] = []
        began: list[str | None] = [self.world.current]

        def left_the_map(look: Observation) -> bool:
            if began[0] is None:  # the world memory had no map yet: the walk's first look names it
                began[0] = self.world.current
            return began[0] is not None and self.world.current != began[0]

        intent = Intent(f"walk to {tile}", budget, lambda nav, look: None if reached else goal,
                        lambda look: bool(reached) or left_the_map(look), lambda target: reached.append(True))
        outcome = yield from self.run(intent, why)
        if not reached and began[0] is not None and self.world.current != began[0]:
            return f"left the map: {self.world.names().get(began[0], began[0])} for {self._map_name()} ({outcome})"
        return outcome

    def _decided(self, target: Target, look: Observation, detour: Target | None, on_the_move: bool = False) -> None:
        found = self.where(look)
        memory, here = found if found is not None else (None, None)
        fact = memory.fact(target.tile) if memory is not None else None
        self.stats.decisions += 1
        if target.kind == "people" and target.who is not None:
            # (step 4.1 round 2, finding 7) one more walk up to this person (`MEET_TRIES`)
            key = f"{self.world.current}|{target.who}"
            self.people_tries[key] = self.people_tries.get(key, 0) + 1
        extra = {"map": self.world.current, "player": list(here) if here else None, "target": list(target.tile),
                 "kind": target.kind, "exit": list(target.exit) if target.exit else None, "direction": target.direction,
                 "score": round(target.score, 2), "known": fact is not None,
                 "seen_from": list(fact.seen_from) if fact is not None else None,
                 "in_window": bool(here is not None and in_window(here, target.tile)),
                 "detour": list(detour.tile) if detour else None, "personality": self.personality,
                 # (build step 3.2) chosen while walking (a target dropped as stale), and the heading then
                 "on_the_move": bool(on_the_move), "heading": self.heading(),
                 # (step 4.1 round 2) a person to walk up to: who
                 "who": target.who}
        self.hands.note("decide", f"target {target.kind} {target.tile}", target.reason, extra)
        self.tell(f"go to the {target.kind} at {target.tile}{' then use it pressing ' + target.direction if target.exit else ''}"
                  f": {target.reason} (score {target.score:.1f}{'; a detour by ' + str(detour.tile) if detour else ''})")
