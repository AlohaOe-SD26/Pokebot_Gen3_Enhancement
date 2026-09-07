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

#: Frames to let a TURN-IN-PLACE finish (~8 frames in Gen 3; bounded generously).
#: ‼ `#26-mossdeeppuzzlespeed` (USER REPORT 2026-08-26): a direction tap only TURNS the avatar when
#: it faces another way, and a turn changes neither the tile nor the script state — so
#: `_step_towards`' attempt 1 used to sit out its ENTIRE 600-frame timeout after every direction
#: change. MEASURED on the 2026-08-26 baseline log (`ACCEPTANCE: PASS` at f61988): ~60 turns x ~600
#: frames ≈ 36,000 of the 62,000-frame solve — 58% of the user's "it took forever". The pre-turn
#: below makes attempt 1 always be a WALK.
TURN_TIMEOUT_FRAMES = 32


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
        from modules.modes import BotModeError

        raise BotModeError(f"Mossdeep Gym: {target} is not adjacent to {start}")

    # --- PRE-TURN (#26-mossdeeppuzzlespeed): face the direction FIRST, so the main loop's press is
    # always a WALK. A 1-frame tap while facing another way is a turn-in-place (never a step), so
    # this cannot skip a tile — and every guard the main loop has is kept here verbatim, so if a
    # scene fires mid-turn (a trainer spotting us) or the tile somehow changes, we behave exactly as
    # the main loop would. If the wait times out, we simply fall through to the OLD behaviour.
    if get_player_avatar().facing_direction != direction:
        context.emulator.press_button(direction)
        for _ in range(TURN_TIMEOUT_FRAMES):
            script = get_global_script_context()
            if script is not None and script.is_active:
                return  # a scene took over; the caller rides it out and re-solves
            if _tile() != start or not _on_gym_map():
                yield from _wait_until_ready()
                return
            if get_player_avatar().facing_direction == direction and player_avatar_is_standing_still():
                break
            yield

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

    :raises BotModeError: if the gym is not solvable from where we stand, or if the simulated
        statue map drifts from the game. Both are conditions the caller must not paper over.
    """
    from modules.modes import BotModeError
    from modules.story.early_game import _ch14_say

    def say(message: str) -> None:
        if verbose:
            _ch14_say(message)

    def require_in_gym(context_note: str) -> None:
        """‼ THE MAP MUST BE RE-CHECKED, NOT CHECKED ONCE.

        Everything in this module reasons in the gym's LOCAL coordinates. A whiteout — the
        realistic outcome of losing one of the nine trainer battles this route walks through —
        deposits the player in front of a Pokémon Center, on a different map, whose local (x, y)
        is a perfectly valid-looking pair of numbers. Checking the map only at entry meant the
        replan loop would happily feed those coordinates to `solve_route` and either misdiagnose
        the failure ("the simulated statue map is wrong") or, worse, find a phantom route and
        start pressing buttons in the Pokémon Center — and if its local tile happened to collide
        with a switch tile, book a phantom rotation into the model.

        Raising `BotModeError` is what makes the recovery work: `do_mossdeep_gym_chapter` catches
        it, walks back in, and re-solves. Leaving the gym resets the puzzle, so re-solving from
        the start is not merely acceptable — it is the only correct thing to do."""
        if not _on_gym_map():
            # ‼ IF THE LATCH IS SET THIS IS THE WHITEOUT ITSELF, so raise the type the chapter
            # re-raises rather than a lookalike. `walk_to_the_leaders` contains no `_check_abort()`
            # of its own — this guard IS its whiteout detector — so without the distinction the
            # chapter's retry loop could not tell "we lost the fight" from "the route broke".
            from modules.story.early_game import StoryAbort, story_should_abort

            raise (StoryAbort if story_should_abort() else BotModeError)(
                f"Mossdeep Gym: no longer on the gym map ({context_note}) — almost certainly a "
                "WHITEOUT. ‼ Leaving the gym RESETS the statue puzzle, so recovery is to re-enter "
                "and solve all 117 steps again, not to walk back to where we were."
            )

    require_in_gym("at entry")

    # ‼ ANSWER THE GOAL QUESTION BEFORE THE START-STATE QUESTION. Standing at the leaders means
    # there is nothing to solve, and the statues are — correctly — NOT at their template positions
    # any more. Checking the start state first would abort the resume case ("resumed mid-puzzle")
    # on a save that is actually FINISHED with the puzzle, which is exactly the anchor this
    # chapter's battle leg is driven from.
    if _tile() in LEADER_APPROACH_TILES:
        return

    puzzle = build_puzzle_from_emulator()
    warps = read_internal_warps()
    state = puzzle.initial_state

    # ‼ START-STATE CONTROL. Entering the gym reloads every template from ROM, so a fresh arrival
    # must match `initial_state`. If it does not, we resumed part-way through somebody else's
    # puzzle and the honest fix is to leave and re-enter, not to guess where the statues are.
    drift = _state_disagreements(puzzle, state)
    if drift:
        raise BotModeError(
            "Mossdeep Gym: the statues are not in their starting positions, so this run resumed "
            f"mid-puzzle ({'; '.join(drift[:4])}). Leave the gym and re-enter — the door warp "
            "reloads every template from ROM and provably resets the puzzle."
        )

    for replan in range(MAX_REPLANS):
        require_in_gym(f"before plan #{replan + 1}")
        here = _tile()
        if here in LEADER_APPROACH_TILES:
            say(f"Story: Ch18 reached the leaders' tile {here}")
            return

        route = solve_route(puzzle, here, warps, state=state)
        if route is None:
            raise BotModeError(
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

            # ‼ A whiteout can fire at any step here — losing one of the nine trainer battles this
            # route walks through is the ordinary way it happens. Check the MAP before the tile
            # below is interpreted as a gym coordinate or used to book a switch press. Ordered
            # after the interruption ride on purpose: the whiteout sequence IS a scene, so ride it
            # out first and then ask where we ended up.
            require_in_gym(f"after stepping on {step.tile}")

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
                raise BotModeError(
                    f"Mossdeep Gym: the simulated statue map drifted from the game after stepping "
                    f"on {step.tile} ({'; '.join(drift[:4])}). Refusing to plan on it — a wrong "
                    "statue map fails dozens of steps later, far from its cause."
                )
        else:
            continue  # the whole route ran without interruption; the loop head re-checks the goal

    raise BotModeError(
        f"Mossdeep Gym: still not at the leaders after {MAX_REPLANS} plans. Each re-plan follows a "
        "real interruption, so this many means something is wrong rather than merely busy."
    )


BADGE_FLAG = "BADGE07_GET"

#: Tate & Liza refuse to battle unless the player has two Pokemon that can fight. The game's own
#: test (`GetMonsStateToDoubles`, `src/pokemon.c:4507`) is: a party count of exactly 1 fails
#: outright; otherwise it needs at least two party members that are non-egg and at HP > 0.
MINIMUM_USABLE_POKEMON = 2

#: Bounded ride for the double battle plus its whole aftermath (badge, TM, messages). Generous
#: because a double battle is long, but a BOUND - never `while True`.
BATTLE_TIMEOUT_FRAMES = 60_000

#: Consecutive frames off the gym map before we call it a whiteout. Debounced, because the map read
#: is transient across a battle's own screen transitions and ending a healthy fight over one odd
#: frame would be worse than the bug it guards. (The KI-51 lesson, applied at build time.)
OFF_MAP_FRAMES_BEFORE_WHITEOUT = 300


def _usable_pokemon() -> int:
    """Party members that could take part in a double battle: non-egg, non-empty, HP > 0."""
    from modules.pokemon_party import get_party

    return sum(
        1
        for mon in get_party()
        if mon is not None and not mon.is_egg and mon.species is not None and mon.current_hp > 0
    )


def fight_the_leaders() -> Generator:
    """Talk to Tate & Liza from an approach tile and ride the double battle out until the badge.

    THE TWO-POKEMON GATE IS CHECKED UP FRONT, NOT DISCOVERED. If the party cannot field two
    battlers the leaders simply deliver a message and no battle starts - so an A/B mash loop would
    spin for its entire timeout and then report "no badge" with no hint why. The game's own
    condition is cheap to evaluate, so evaluate it and say the real reason.

    A WHITEOUT HERE IS SPECIAL. Losing does not merely cost time: it teleports the player to a
    Pokemon Center, and LEAVING THE GYM RESETS THE STATUE PUZZLE (the door tiles are ordinary warps,
    so `LoadObjEventTemplatesFromHeader` re-copies every template from ROM). The whole 117-step
    solve has to be redone. So the loss is detected and reported precisely rather than being left to
    surface as a mysterious timeout - and `do_mossdeep_gym_chapter` is what re-solves.
    """
    from modules.memory import get_event_flag
    from modules.modes import BotModeError
    from modules.modes.util.walking import ensure_facing_direction
    from modules.story.early_game import _ch14_say, _check_abort, _wait_until_cutscene_over

    if get_event_flag(BADGE_FLAG):
        return  # resume-safe

    here = _tile()
    if not _on_gym_map() or here not in LEADER_APPROACH_TILES:
        raise BotModeError(
            f"Mossdeep Gym: cannot challenge the leaders from {here} - must be standing on one of "
            f"{sorted(LEADER_APPROACH_TILES)}. Tate and Liza stand on collision-1 tiles at "
            "(23,7)/(24,7), so those tiles can never be walked onto."
        )

    usable = _usable_pokemon()
    if usable < MINIMUM_USABLE_POKEMON:
        raise BotModeError(
            f"Mossdeep Gym: Tate & Liza are a DOUBLE battle and need {MINIMUM_USABLE_POKEMON} "
            f"Pokemon able to fight; the party has {usable}. They would only show "
            "'you need two Pokemon' and no battle would start. Heal before challenging them."
        )

    _ch14_say(f"Story: Ch18 challenging Tate & Liza from {here} ({usable} able to battle)...")
    yield from ensure_facing_direction("Up")
    yield

    frames = 0
    off_map = 0
    while not get_event_flag(BADGE_FLAG):
        _check_abort()
        if frames > BATTLE_TIMEOUT_FRAMES:
            raise BotModeError(
                f"Mossdeep Gym: {BADGE_FLAG} still unset after {frames} frames at {_tile()}. "
                f"Party able to battle: {_usable_pokemon()}."
            )
        try:
            on_gym = _on_gym_map()
        except Exception:  # noqa: BLE001 - an unreadable map must never end a healthy fight
            on_gym = True
        off_map = 0 if on_gym else off_map + 1
        if off_map > OFF_MAP_FRAMES_BEFORE_WHITEOUT:
            raise BotModeError(
                "Mossdeep Gym: left the gym during the Tate & Liza fight without the badge - "
                f"almost certainly a WHITEOUT ({frames} frames in). Leaving the gym RESETS the "
                "statue puzzle, so recovering means re-entering and solving all 117 steps again."
            )
        context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        yield

    _ch14_say(f"Story: Ch18 {BADGE_FLAG} set after {frames} frames - riding out the aftermath")
    # The badge is set MID-SCRIPT. Returning here would hand the ladder a `lockall`ed avatar and
    # the next chapter would fail somewhere unrelated - the `EventScript_ActivateStrength` trap.
    yield from _wait_until_cutscene_over("B")


#: The leaders' platform is an ELEVEN-TILE ISLAND. Measured, not assumed (`probe_ch19_hazards.py`):
#: `calculate_path((23,8) -> (7,35))` raises `PathFindingError`, while the control
#: `calculate_path((23,8) -> (21,6))` returns a 6-waypoint path. The only way off is the coord event
#: at (21,6), which `warpmossdeepgym`s the player to (7,30) in the entrance hall.
PLATFORM_EXIT_TILE = (21, 6)
PLATFORM_EXIT_LANDING = (7, 30)
GYM_DOOR_TILES = ((7, 35), (6, 35))


def leave_the_gym() -> Generator:
    """Get the player OUT of the gym after the badge, and back into Mossdeep City.

    ‼‼ WITHOUT THIS THE CHAPTER STRANDS THE RUN, and it would have passed its own acceptance test
    while doing so. §Ch18 graded itself on `BADGE07_GET` AND controllable — both true — but it left
    the avatar on `(23,8)`, an eleven-tile collision island. The next chapter's very first
    navigation call would have raised `PathFindingError` inside the gym, with zero city tiles
    walked and nothing to suggest the gym was the cause.

    ‼ THIS IS KI-56 HAPPENING A SECOND TIME. That entry's own prevention rule reads: *a chapter's
    test must include "and the bot can continue"*. It was written about §Ch15 leaving the run four
    floors deep in the Magma Hideout. The same mistake, in a new chapter, in the same session — so
    the acceptance test now ends outside the gym rather than on the winning tile.

    ‼ (21,6) IS NOT A TRAP HERE. KI-58 labelled it one, correctly, for a bot trying to REACH the
    leaders — stepping on it costs you the platform. After the badge that is precisely what we want,
    and it is the only cheap exit: it is a coord_event, not a warp event, so no warp-graph solver
    will ever offer it."""
    from modules.map_data import MapRSE
    from modules.modes import BotModeError
    from modules.story.early_game import (
        _ch14_say,
        _enter_warp_by_navigation,
        _navigate_riding_out,
        wait_until_truly_controllable,
    )

    if not _on_gym_map():
        return  # already out — resume-safe

    if _tile() in LEADER_APPROACH_TILES or _tile() == PLATFORM_EXIT_TILE:
        _ch14_say(f"Story: Ch18 leaving the leaders' platform via the {PLATFORM_EXIT_TILE} coord warp")
        # Stepping ON the tile is the whole action: the coord event fires and carries us away.
        yield from _navigate_riding_out(GYM, PLATFORM_EXIT_TILE, tries=6)
        yield from _wait_for_tile(PLATFORM_EXIT_LANDING, timeout=1200)
        yield from wait_until_truly_controllable()
        if _tile() != PLATFORM_EXIT_LANDING:
            raise BotModeError(
                f"Mossdeep Gym: stepped on {PLATFORM_EXIT_TILE} but landed on {_tile()}, not "
                f"{PLATFORM_EXIT_LANDING}. The platform exit did not fire."
            )
        _ch14_say(f"Story: Ch18 back in the entrance hall at {_tile()}")

    def outside() -> bool:
        return tuple(get_player_avatar().map_group_and_number) == MapRSE.MOSSDEEP_CITY.value

    last_error = ""
    for door in GYM_DOOR_TILES:
        try:
            yield from _enter_warp_by_navigation(outside, GYM, door, label=f"gym door {door}")
            yield from wait_until_truly_controllable()
            if outside():
                _ch14_say(f"Story: Ch18 out of the gym, in Mossdeep City at {_tile()}")
                return
        except BotModeError as error:  # noqa: BLE001 — NOT swallowed: two doors lead outside, so one
            # failing is an expected outcome of trying both. The reason is kept and raised below if
            # neither works.
            # ⛔⛔ KI-81 — THE SITE THAT PROVED THE CLASS WAS NEVER SWEPT. KI-67 guarded this file's
            # CHAPTER retry loop (`:534`) but not this INNER door loop, and `StoryAbort` is a
            # `BotModeError`. After a whiteout this used to try the second door on a dead run and
            # then raise "won the badge but could not get out of the gym" — a FABRICATED diagnosis
            # naming doors, when the player is standing outside a Pokémon Center. That is exactly
            # the laundering `reraise_if_aborting` exists to stop.
            from modules.story.early_game import reraise_if_aborting

            reraise_if_aborting(error)
            last_error = f"{door}: {str(error)[:120]}"

    raise BotModeError(
        f"Mossdeep Gym: won the badge but could not get out of the gym (tried {GYM_DOOR_TILES}; "
        f"{last_error}). ‼ Leaving the player inside would strand the run — the leaders' platform "
        "is an island and the entrance hall is the only part of the gym that touches the door."
    )


def do_mossdeep_gym_chapter() -> Generator:
    """Chapter 18 - the Mossdeep Gym, end to end: solve the statue puzzle, then beat the leaders.

    INTENT: set `BADGE07_GET` (the Mind Badge), which gates the rest of the story arc.
    STORY CONDITION: the player is in Mossdeep, or already inside the gym.
    GOAL/END STATE: the badge set AND the avatar controllable. Graded BINARY.

    THE RETRY LOOP IS NOT DEFENSIVE PADDING - it is whiteout recovery, and this gym needs it more
    than any other. A loss teleports the player out, and leaving the gym RESETS the puzzle, so
    recovery is not "walk back to the leader" but "solve the whole thing again". The loop re-enters
    and re-solves; `walk_to_the_leaders` is safe to call repeatedly because it verifies the statues
    are at their starting positions before planning anything.

    WHY THIS CHAPTER LIVES HERE AND NOT IN `early_game.py`. Every other chapter is in that file,
    which is already 8,700 lines. All of Ch18's logic - the puzzle model, the solver, the executor -
    is gym-specific and already in this module, so the chapter sits with the code it drives and
    `story_mode.py` imports it from here. Recorded in `06-DECISIONS-LOG.md`.
    """
    from modules.map_data import MapRSE
    from modules.memory import get_event_flag
    from modules.modes import BotModeError
    from modules.story.early_game import (
        StoryAbort,
        _ch14_say,
        _enter_warp_by_navigation,
        _navigate_riding_out,
        reraise_if_aborting,
        wait_until_truly_controllable,
    )

    if get_event_flag(BADGE_FLAG):
        # ⛔⛔ #24-mossdeepstrand — THIS READ `return  # resume-safe`, AND THE LABEL WAS THE BUG.
        # The one resume it is NOT safe for is the only one that matters: re-entering with the badge
        # already set while standing on the leaders' platform (23,8) — an ELEVEN-TILE COLLISION
        # ISLAND whose only exit is the (21,6) **coord_event**, which no warp-graph solver can ever
        # offer (`:460-461`). Returning there passes this chapter's own done-test and strands the
        # run — exactly the hazard the comment at the `leave_the_gym()` call below warns about.
        # ⇒ A "DONE" FLAG IS NOT A "TIDY" FLAG: `BADGE07_GET` answers *did we win?*, not *is there
        # nothing left to do?*, and the gap between those questions is this island.
        # ‼ `leave_the_gym()` no-ops off the gym map (`:471-472`), so this stays resume-safe for
        # every other position while fixing the one it was not.
        # ⛔ DO NOT make the same edit to the identical early-return in `fight_the_leaders()`
        # (`:382`): that one is a SUB-STEP and is correct as written — leaving is the CHAPTER's job,
        # and the fight is retried up to three times by the loop below.
        yield from leave_the_gym()
        return

    GYM_DOOR = (38, 9)  # MOSSDEEP_CITY warp 1 -> MOSSDEEP_CITY_GYM
    attempts = []

    for attempt in range(1, 4):
        if get_event_flag(BADGE_FLAG):
            return

        if not _on_gym_map():
            _ch14_say(f"Story: Ch18 attempt {attempt} - entering the Mossdeep Gym")
            yield from _navigate_riding_out(MapRSE.MOSSDEEP_CITY, (38, 10))
            yield from _enter_warp_by_navigation(
                _on_gym_map, MapRSE.MOSSDEEP_CITY, GYM_DOOR, label="Mossdeep Gym door"
            )
            yield from wait_until_truly_controllable()

        try:
            yield from walk_to_the_leaders()
            yield from fight_the_leaders()
        except StoryAbort:
            # ‼‼ THE WHITEOUT ABORT IS NOT THIS LOOP'S TO HANDLE (KI-67). Only `StoryMode.run`
            # clears the abort latch, so retrying in place here would hit the next `_check_abort()`
            # immediately: one loss would consume all three attempts in a handful of frames and
            # report three failures, two of them invented. Re-raising hands the retry to
            # `StoryMode.run`, which clears the latch, rides out the respawn and re-runs `_play()`
            # — and this chapter is resume-safe, so re-entering re-solves the puzzle correctly.
            # ‼ That matters MORE here than anywhere else: leaving the gym RESETS the statue
            # puzzle, so the recovery genuinely is "re-enter and solve all 117 steps again", which
            # is exactly what a fresh `_play()` does and what an in-place retry could not.
            raise
        except BotModeError as error:  # noqa: BLE001 - NOT swallowed. A whiteout is an EXPECTED
            # outcome of a gym fight, and the only recovery is to re-enter and re-solve. Every
            # attempt's reason is accumulated and raised together if all three fail.
            # ‼ The latch check catches a whiteout whose identity was lost to a conversion; the
            # `except StoryAbort` above catches it while the original object is still in flight.
            # Both are needed — see `reraise_if_aborting`.
            reraise_if_aborting(error)
            attempts.append(f"attempt {attempt}: {str(error)[:200]}")
            _ch14_say(f"Story: Ch18 attempt {attempt} failed - {str(error)[:120]}")
            continue

        if get_event_flag(BADGE_FLAG):
            # ‼ THE BADGE IS NOT THE END OF THE CHAPTER. Winning leaves the avatar on the
            # leaders' platform, an eleven-tile island; a chapter that returned here would pass its
            # own test and strand the run. See `leave_the_gym`.
            yield from leave_the_gym()
            _ch14_say("Story: Ch18 complete - the Mind Badge is won and the bot is out of the gym")
            return

    raise BotModeError(
        f"Mossdeep Gym: {BADGE_FLAG} still unset after 3 attempts. " + " | ".join(attempts)
    )
