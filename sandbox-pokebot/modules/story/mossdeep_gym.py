"""§Ch18 — walk the Mossdeep Gym's statue puzzle and reach Tate & Liza.

This is the EXECUTOR. The model and the search live in `mossdeep_gym_puzzle.py` and are pure; this
file is the part that touches the emulator.

‼ IT RE-SOLVES RATHER THAN REPLAYS. The obvious design is to solve once and then walk 117 steps
blind, and it is the wrong one: this gym interrupts you. Nine trainers stand on the rotating pads,
and every rotation re-aims them — pressing yellow at (3,30) slides Maura to (4,30), directly beside
the player, facing them. Gym battles are therefore a CONSEQUENCE OF THE MECHANIC, not a derail, and
a blind replay desynchronises the moment one fires. So: solve, walk until something unexpected
happens, then solve again from where we actually are. The search costs a fraction of a second and
the plan is always current.

‼ THE SIMULATED STATE IS CROSS-CHECKED EVERY STEP, because it is the one thing that can drift
silently. `get_map_objects()` returns only the objects the game currently has LOADED, which is a
subset of the 36 templates — so the check covers what is visible and says how much that was. A
mismatch aborts loudly: a route planned on a wrong statue map walks into a wall 40 steps later,
somewhere unrelated to the cause, which is this project's most expensive bug shape.

‼ WHY WE CANNOT SIMPLY READ THE STATUE POSITIONS BACK. `MoveRotatingTileObjects` mutates
`gSaveBlock1Ptr->objectEventTemplates`, the RAM copy — but `MapLocation.objects` reads the map
header's event list in ROM, so it always returns the ORIGINAL positions. The only live view is
`get_map_objects()`, and it is partial. Hence: simulate forward, verify against what is visible.

‼ ENTERING THE GYM RESETS THE PUZZLE, which is what makes starting from the ROM templates correct.
`DoMossdeepGymWarp` sets `SKIP_OBJECT_EVENT_LOAD` so internal warps preserve statue positions, but
the two door tiles (6,35)/(7,35) are ordinary warps, so `LoadObjEventTemplatesFromHeader()` runs and
re-copies every template from ROM. That is also the recovery if the state is ever found desynced:
walk out of the gym and back in, and the puzzle is provably at its start again.
"""

from typing import Generator

from modules.context import context
from modules.map import get_map_objects
from modules.map_data import MapRSE
from modules.player import get_player_avatar, player_avatar_is_standing_still
from modules.tasks import get_global_script_context
from modules.story.mossdeep_gym_puzzle import (
    COLOUR_NAMES,
    LEADER_APPROACH_TILES,
    build_puzzle_from_emulator,
    read_internal_warps,
    solve_route,
)

GYM = MapRSE.MOSSDEEP_CITY_GYM

_DIRECTION_FOR_DELTA = {(1, 0): "Right", (-1, 0): "Left", (0, 1): "Down", (0, -1): "Up"}

#: How many times we may re-solve before giving up. Each re-solve follows a real interruption
#: (a battle, a surprise position), so a run that needs many of them is telling us something is
#: wrong rather than that the gym is busy. Bounded on purpose — never `while True`.
MAX_REPLANS = 40

#: Frames to let a single step finish. A step is ~16 frames; a step that starts a trainer intro
#: takes much longer, so this is generous and still bounded.
STEP_TIMEOUT_FRAMES = 600


def _tile() -> tuple[int, int]:
    return tuple(get_player_avatar().local_coordinates)


def _on_gym_map() -> bool:
    return tuple(get_player_avatar().map_group_and_number) == GYM.value


def _loaded_objects() -> dict[int, tuple[int, int]]:
    """local_id -> tile, for the objects the game currently has loaded."""
    return {
        obj.local_id: tuple(obj.current_coords)
        for obj in get_map_objects()
        if "isPlayer" not in obj.flags
    }


def _state_disagreements(puzzle, state) -> list[str]:
    """Where the simulated statue map disagrees with the objects we can actually see."""
    index_of = {obj.local_id: index for index, obj in enumerate(puzzle.objects)}
    problems = []
    for local_id, actual in _loaded_objects().items():
        if local_id in index_of and state[index_of[local_id]] != actual:
            problems.append(f"id {local_id}: game {actual}, simulated {state[index_of[local_id]]}")
    return problems


def _wait_until_ready(*, timeout: int = 1800) -> Generator:
    """Wait for the field to be quiet AND the avatar to be able to move.

    ‼ BOTH CONDITIONS, AND A MINIMUM. Landing on a switch leaves a window where the step has
    finished but the coord_event script has not yet taken hold: the avatar reads as ready, and the
    press that follows is swallowed by the script that starts a moment later. Waiting for the script
    to be inactive as well as the avatar to be standing still closes that hole; the settle count
    keeps a brief mid-script lull from being mistaken for the end."""
    stable = 0
    for _ in range(timeout):
        script = get_global_script_context()
        busy = script is not None and script.is_active
        if not busy and player_avatar_is_standing_still():
            stable += 1
            if stable >= 20:
                return
        else:
            stable = 0
        yield


def _wait_for_tile(target: tuple[int, int], *, timeout: int = 900) -> Generator:
    """Wait until the avatar is actually standing on `target`, then until it can move.

    ‼ THIS IS HOW A WARP IS CONFIRMED — by the destination, not by the avatar looking idle. Gen 3
    fades out, loads and fades in; through part of that the avatar reads as standing still with no
    script active, so any readiness-based wait returns early and the plan desynchronises by exactly
    one step. Bounded, so a warp that never happens fails here rather than hanging."""
    for _ in range(timeout):
        if _tile() == target:
            yield from _wait_until_ready()
            return
        yield


def _ride_out_interruption() -> Generator:
    """Press through whatever the gym just started — almost always a trainer battle.

    Deliberately delegates to the story module's own scene rider so gym battles are fought by the
    same machinery as every other trainer in the run, rather than a second implementation here."""
    from modules.story.early_game import _ride_out_all_scenes

    yield from _ride_out_all_scenes()


def _step_towards(target: tuple[int, int]) -> Generator:
    """Take exactly one step onto `target`, bounded, and stop early if a script takes over.

    ‼ NOT `walk_one_tile`. That helper loops `while position == start: yield` with no bound, so a
    trainer intro firing mid-step — which is routine here — parks the bot forever. Everything in
    this gym has to assume a script can start at any moment.

    ‼ PRESS, CHECK, PRESS AGAIN — never twice blind. A direction press turns the avatar in place
    when it is facing another way, so one press can be a turn rather than a step; but two blind
    presses move TWO tiles whenever the avatar already faced that way, which steps straight over a
    tile. In a room where nine tiles are switches, skipping one silently rotates a colour."""
    start = _tile()
    delta = (target[0] - start[0], target[1] - start[1])
    direction = _DIRECTION_FOR_DELTA.get(delta)
    if direction is None:
        raise RuntimeError(f"Mossdeep Gym: {target} is not adjacent to {start}")

    for attempt in range(2):
        context.emulator.press_button(direction)
        for _ in range(STEP_TIMEOUT_FRAMES):
            script = get_global_script_context()
            if script is not None and script.is_active:
                return  # a scene took over; the caller rides it out and re-solves
            if _tile() != start or not _on_gym_map():
                yield from _wait_until_ready()
                return
            yield
        yield


def walk_to_the_leaders(*, verbose: bool = True) -> Generator:
    """Solve the statue puzzle and end up standing on a tile that faces Tate & Liza.

    :raises RuntimeError: if the gym is not solvable from where we stand, or if the simulated
        statue map drifts from the game. Both are conditions the caller must not paper over.
    """
    from modules.story.early_game import _ch14_say

    def say(message: str) -> None:
        if verbose:
            _ch14_say(message)

    if not _on_gym_map():
        raise RuntimeError("Mossdeep Gym: walk_to_the_leaders called outside the gym")

    puzzle = build_puzzle_from_emulator()
    warps = read_internal_warps()
    state = puzzle.initial_state

    # ‼ START-STATE CONTROL. Entering the gym reloads every template from ROM, so a fresh arrival
    # must match `initial_state`. If it does not, we resumed part-way through somebody else's
    # puzzle and the honest fix is to leave and re-enter, not to guess where the statues are.
    drift = _state_disagreements(puzzle, state)
    if drift:
        raise RuntimeError(
            "Mossdeep Gym: the statues are not in their starting positions, so this run resumed "
            f"mid-puzzle ({'; '.join(drift[:4])}). Leave the gym and re-enter — the door warp "
            "reloads every template from ROM and provably resets the puzzle."
        )

    for replan in range(MAX_REPLANS):
        here = _tile()
        if here in LEADER_APPROACH_TILES:
            say(f"Story: Ch18 reached the leaders' tile {here}")
            return

        route = solve_route(puzzle, here, warps, state=state)
        if route is None:
            raise RuntimeError(
                f"Mossdeep Gym: no route to {sorted(LEADER_APPROACH_TILES)} from {here}. "
                "‼ Measured 2026-08-12: no reachable configuration is unsolvable (114,929 states, "
                "0 dead), so this means the simulated statue map is wrong, not that the gym is."
            )
        presses = sum(1 for step in route if step.kind == "switch")
        say(f"Story: Ch18 plan #{replan + 1} from {here} — {len(route)} steps, {presses} switch press(es)")

        for step in route:
            before = _tile()
            yield from _step_towards(step.tile)

            # ‼ A WARP COMPLETES A STEP LATE. Stepping onto a pad, the avatar reads as standing
            # still and script-free for a moment BEFORE the warp takes hold — the same window that
            # eats a button press on a switch tile. Measured: the first driven run reported
            # "expected (20,24) after stepping on (1,33), got (1,33)" and then arrived at (20,24)
            # during the NEXT step, desynchronising the plan every single time. So do not infer the
            # warp from readiness; wait for the destination tile itself.
            if step.kind == "warp":
                yield from _wait_for_tile(step.landed)

            script = get_global_script_context()
            interrupted = script is not None and script.is_active
            if interrupted:
                say(f"Story: Ch18 interrupted at {step.tile} ({script.stack[:1]}) — riding it out")
                yield from _ride_out_interruption()
                yield from _wait_until_ready()

            # ‼‼ UPDATE THE STATE FROM WHERE WE ACTUALLY ARE, NEVER FROM WHAT THE PLAN INTENDED.
            # The first driven run applied a purple press for a switch the bot never stood on: the
            # plan's next step was onto (23,21), a pending warp fired mid-step and carried us to
            # (9,18) instead, and the press was booked anyway. The game fires a coord_event when
            # the player LANDS on the tile, so that is the only thing worth reading — and it is
            # also correct when an interruption drops us somewhere unplanned.
            landed = _tile()
            if landed != before and landed in puzzle.switches:
                state = puzzle.press(state, puzzle.switches[landed])

            if interrupted:
                break  # a scene may have moved us; re-solve rather than assume

            if landed != step.landed:
                say(f"Story: Ch18 expected {step.landed} after stepping on {step.tile}, got {landed} — re-planning")
                break

            drift = _state_disagreements(puzzle, state)
            if drift:
                raise RuntimeError(
                    f"Mossdeep Gym: the simulated statue map drifted from the game after stepping "
                    f"on {step.tile} ({'; '.join(drift[:4])}). Refusing to plan on it — a wrong "
                    "statue map fails dozens of steps later, far from its cause."
                )
        else:
            continue  # the whole route ran without interruption; the loop head re-checks the goal

    raise RuntimeError(
        f"Mossdeep Gym: still not at the leaders after {MAX_REPLANS} plans. Each re-plan follows a "
        "real interruption, so this many means something is wrong rather than merely busy."
    )
