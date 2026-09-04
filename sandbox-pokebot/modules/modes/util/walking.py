from typing import Generator, Iterable, Callable

from modules.context import context
from modules.debug import debug
from modules.map import get_map_data, get_map_data_for_current_position, get_player_map_object
from modules.map_data import MapFRLG, MapRSE
from modules.map_path import calculate_path, Waypoint, PathFindingError, Direction, WaypointAction
from modules.memory import GameState, get_game_state
from modules.roms import ROMLanguage
from modules.player import (
    RunningState,
    AcroBikeState,
    TileTransitionState,
    get_player_avatar,
    player_avatar_is_controllable,
    player_avatar_is_standing_still,
    player_is_at,
    get_player_location,
    AvatarFlags,
    PlayerAvatar,
)
from modules.tasks import get_global_script_context, is_waiting_for_input, task_is_active
from .sleep import wait_for_n_frames
from .._interface import BotModeError
from ...items import get_item_bag, get_item_by_name


@debug.track
def walk_to(destination_coordinates: tuple[int, int], run: bool = True) -> Generator:
    """
    Moves the player to a set of coordinates on the same map. Does absolutely no
    collision checking and _will_ get stuck all the time.
    This returns control back to the calling functions _while the player is still moving_.
    To prevent this, you might want to use the `follow_path()` utility function instead.
    :param destination_coordinates: Tuple (x, y) of map-local coordinates of the destination
    :param run: Whether the player should run (hold down B)
    """

    if get_game_state() != GameState.OVERWORLD:
        raise BotModeError("Game is not currently in overworld mode. Cannot walk.")

    context.emulator.reset_held_buttons()

    initial_map = get_player_avatar().map_group_and_number
    while True:
        context.emulator.reset_held_buttons()
        if run:
            context.emulator.hold_button("B")

        avatar = get_player_avatar()
        if avatar.local_coordinates == destination_coordinates:
            break
        if avatar.map_group_and_number != initial_map:
            while get_game_state() != GameState.OVERWORLD:
                yield
            break

        if (avatar.running_state == RunningState.NOT_MOVING and avatar.acro_bike_state == AcroBikeState.NORMAL) or (
            context.rom.is_frlg
            and avatar.tile_transition_state in [TileTransitionState.CENTERING, TileTransitionState.NOT_MOVING]
            and "Std_MsgboxSign" in get_global_script_context().stack
        ):
            if destination_coordinates[0] < avatar.local_coordinates[0]:
                context.emulator.hold_button("Left")
            elif destination_coordinates[0] > avatar.local_coordinates[0]:
                context.emulator.hold_button("Right")
            elif destination_coordinates[1] < avatar.local_coordinates[1]:
                context.emulator.hold_button("Up")
            elif destination_coordinates[1] > avatar.local_coordinates[1]:
                context.emulator.hold_button("Down")

        yield

    context.emulator.reset_held_buttons()


@debug.track
def follow_path(waypoints: Iterable[tuple[int, int]], run: bool = True) -> Generator:
    """
    Moves the player along a given path.

    There is no collision checking, so the path needs to be chosen carefully to ensure it
    doesn't get stuck.

    :param waypoints: List of tuples (x, y) of map-local coordinates of the destination
    :param run: Whether the player should run (hold down B)
    """
    if get_game_state() != GameState.OVERWORLD:
        raise RuntimeError("The game is currently not in the overworld. Cannot navigate.")

    # Make sure that the player avatar can actually be controlled/moved right now.
    if not player_avatar_is_controllable():
        raise RuntimeError("The player avatar is currently not controllable. Cannot navigate.")

    for waypoint in waypoints:
        yield from walk_to(waypoint, run)

    # Wait for player to come to a full stop.
    while not player_avatar_is_standing_still() or get_player_avatar().running_state != RunningState.NOT_MOVING:
        yield


class TimedOutTryingToReachWaypointError(BotModeError):
    def __init__(self, waypoint: Waypoint):
        self.waypoint = waypoint
        if context.rom.is_rse:
            map_name = MapRSE(waypoint.map).name
        else:
            map_name = MapFRLG(waypoint.map).name
        message = f"Did not reach waypoint ({waypoint.coordinates}) @ {map_name} in time."
        super().__init__(message)


class NavigationStuckError(BotModeError):
    """FORK (2026-07-23, KI-15): navigate_to made no NET progress across many
    consecutive re-paths.

    Distinct from TimedOutTryingToReachWaypointError (a single missed leg, which
    navigate_to normally recovers from by re-pathing). This is raised when the
    re-path loop itself can't advance — e.g. an inline battle interrupts story
    navigation and the post-battle ReturnFromBattleToOverworld transition leaves
    the avatar bouncing between two adjacent tiles (the real ROUTE 104
    (5,6)<->(5,7) hang) or frozen in place. A dedicated type lets the caller's
    recovery abort the wedge in a bounded number of frames instead of spinning
    until a story watchdog trips ~20k frames later."""

    def __init__(self, destination_map, destination_coordinates, stuck_position):
        self.destination_map = destination_map
        self.destination_coordinates = destination_coordinates
        self.stuck_position = stuck_position
        super().__init__(
            f"Navigation to {destination_coordinates} @ {destination_map} made no progress "
            f"(avatar stuck near {stuck_position}). Aborting so the caller can recover."
        )


# KI-15 tuning. A healthy navigate_to re-paths only a handful of times (an NPC
# steps into the way, an overshoot on the Mach Bike). Making no NET progress —
# only re-visiting a tiny set of recently-seen tiles — for this many consecutive
# re-paths means the avatar is wedged (post-battle bounce/freeze), not merely
# blocked, so we bail. Kept generous so a slow-but-advancing nav is never
# mistaken for stuck.
_NAVIGATE_NO_PROGRESS_REPATHS = 8
# After a re-path timeout with no active script, wait (pressing nothing) for the
# avatar to be stably standing-still + controllable before re-pathing. This lets
# a mid-navigation battle's return transition finish instead of re-pathing into
# it. Costs ~nothing on a mundane NPC block (the avatar is already stopped).
_NAVIGATE_SETTLE_STABLE_FRAMES = 20
_NAVIGATE_SETTLE_TIMEOUT_FRAMES = 300


@debug.track
def follow_waypoints(
    path: Iterable[Waypoint | None], run: bool = True, final_facing_direction: Direction | None = None
) -> Generator:
    """
    Follows a given set of waypoints.

    Since the `path` parameter can also be a generator function, this function can be used to follow
    looping or dynamically calculated paths.

    This function does not check for obstacles, but if it takes too long to reach a waypoint it will
    fire a `TimedOutTryingToReachWaypointError` exception (which is a child class of `BotModeError`,
    so if unhandled it will just show as a message and put the bot back into manual mode.)

    :param path: A list (or generator) of waypoints to follow.
    :param run: Whether to run (hold `B`.) This is ignored when on a bicycle, since it would be either
                meaningless or actively detrimental (Acro Bike, where it would initiate wheelie mode.)
    :param final_facing_direction: A direction that the player avatar should face after reaching its
                                   destination. This can be useful to make it bump into an obstacle with
                                   the Mach Bike.
    """

    if get_game_state() != GameState.OVERWORLD:
        raise BotModeError("The game is currently not in the overworld. Cannot navigate.")

    # Make sure that the player avatar can actually be controlled/moved right now.
    if not player_avatar_is_controllable():
        raise BotModeError("The player avatar is currently not controllable. Cannot navigate.")

    # 'Running' means holding B, which on the Acro Bike leads to doing a Wheelie which is actually
    # slower than normal riding. On other bikes it just doesn't do anything, so if we are riding one,
    # this flag will just be ignored.
    # Similarly, running is not possible when surfing or swimming underwater, but pressing B can
    # cause the game to try and dive/emerge which we don't want.
    if run and get_player_avatar().is_on_bike:
        run = False

    # For each waypoint (i.e. each step of the path) we set a timeout. If the player avatar does not reach the
    # expected location within that time, we stop the walking. The calling code could use that event to
    # recalculate a new path.
    #
    # Regular steps usually take 16 frames, so the 20-frame timeout should be enough. For warps (walking into doors
    # etc.) a 'step' may take a bit longer due to the map transition. Which is why there is an extra allowance for
    # those cases.
    timeout_in_frames = 20
    extra_timeout_in_frames_for_warps = 280

    current_position = get_map_data_for_current_position()
    last_waypoint = None
    for waypoint in path:
        if waypoint is None:
            yield
            continue

        # For the first waypoint it is possible that the player avatar is not facing the same way as it needs to
        # walk. This leads to the first navigation step to actually become two: Turning around, then doing the step.
        # When in tall grass, that could lead to an encounter starting mid-step which messes up the battle handling.
        # So for the first step, we will add an explicit additional turning step.
        if last_waypoint is None:
            current_facing_direction = Direction.from_string(get_player_avatar().facing_direction)
            if waypoint.direction != current_facing_direction:
                yield from ensure_facing_direction(waypoint.direction)

        last_waypoint = waypoint
        field_effect_is_active = False
        not_finished_frames = 0  # KI-15 family: consecutive frames without heldMovementFinished
        frames_remaining_until_timeout = timeout_in_frames
        if waypoint.is_warp:
            frames_remaining_until_timeout += extra_timeout_in_frames_for_warps
        if waypoint.action is WaypointAction.Surf:
            if context.rom.language == ROMLanguage.Japanese:
                frames_remaining_until_timeout += 400
            else:
                frames_remaining_until_timeout += 300
        elif waypoint.action is WaypointAction.Waterfall:
            # ⛔⛔ `[1][1]`, NOT `[0][1]` — FIXED 2026-09-04 (`#24-waterfalltimeout`).
            # `get_player_location()` returns **(map_enum, (x, y))** (`modules/player.py:291`), and
            # `MapRSE.__getitem__` makes `map_enum[1]` the MAP NUMBER. So the original `[0][1]`
            # scaled this timeout by the map number instead of by how far the climb is.
            # ⭐ MEASURED before touching it (observe-only, `--driver ch23b1fprobe`, standing on
            # VICTORY_ROAD_B1F (8,3)): `[0][1]` = **44** (the map number), `[1][1]` = **3** (the y),
            # ground truth coords (8,3). ‼ This project has shipped THREE backwards index/coordinate
            # "fixes" (KI-18, KI-34, KI-66), so the direction is measured, never reasoned out.
            # ⇒ the old line was wrong in BOTH directions depending on the map: Ever Grande is map
            # num 8, so a climb to y=59 gave 195 + (8 - 59) * 42 = **-1947** frames (a NEGATIVE
            # allowance, i.e. the timeout expires immediately), while VICTORY_ROAD_B2F is map
            # num 45 against a waypoint y of 14, giving 195 + (45 - 14) * 42 = **+1497** where
            # the correct value is 195 + (11 - 14) * 42 = **+69** — 1,428 frames of false slack.
            # ‼ THIS COMMENT FIRST SAID "+1428" AS THE TOTAL. That was the SLACK, computed
            # from the wrong waypoint y and without the base term — a wrong illustrative number
            # baked into production code on exactly the line-class this project has broken on
            # three times. A Tier 1 reviewer caught it. ⇒ recompute an illustrative number from
            # the committed evidence, never retype it from memory of the filing.
            # It stayed latent only because our story legs hand-drive waterfall climbs rather than
            # letting the planner emit a Waterfall waypoint.
            frames_remaining_until_timeout += 195 + (get_player_location()[1][1] - waypoint.coordinates[1]) * 42

        _fw_trace_n = 0
        while not player_is_at(waypoint.map, waypoint.coordinates) or field_effect_is_active:
            player_object = get_player_map_object()

            # --- KI-15 TRACE (env-gated, logging only; REMOVE after repro) ---
            _fw_trace_n += 1
            if _fw_trace_n % 200 == 0:
                import os as _os_fw

                _fw = _os_fw.environ.get("FW_TRACE")
                if _fw:
                    try:
                        from modules.player import get_player_avatar as _gpa_fw

                        with open(_fw, "a", encoding="utf-8") as _f:
                            _f.write(
                                f"[fw] n={_fw_trace_n} gs={get_game_state()} "
                                f"rem={frames_remaining_until_timeout} wp={waypoint.coordinates} "
                                f"warp={waypoint.is_warp} pos={tuple(_gpa_fw().local_coordinates)} "
                                f"flags={getattr(player_object, 'flags', None)}\n"
                            )
                    except Exception:
                        pass
            # -----------------------------------------------------------------
            if get_game_state() == GameState.OVERWORLD:
                frames_remaining_until_timeout -= 1

            if frames_remaining_until_timeout <= 0:
                if player_is_at(current_position.map_group_and_number, current_position.local_position):
                    context.emulator.reset_held_buttons()
                    yield from wait_for_n_frames(16)
                    raise TimedOutTryingToReachWaypointError(waypoint)
                else:
                    current_position = get_map_data_for_current_position()
                    frames_remaining_until_timeout += timeout_in_frames

            # Only pressing the direction keys during the frame where movement is actually registered can help
            # preventing weird overshoot issues in cases where a listener handles an event (like a battle, PokeNav
            # call, ...)
            # FORK (2026-07-24, ch12 gym-door wedge): a mid-navigation battle can
            # return the avatar with heldMovementFinished PERMANENTLY absent while
            # fully controllable — and since this loop only presses when that flag is
            # present, the bot then presses NOTHING, which is exactly what keeps the
            # state parked (probed live: any input jolts it awake instantly; zero
            # input left it frozen 20k frames). During genuine walking the flag is
            # only absent for the few frames of each step, so a long consecutive
            # absence means the wedge — jolt the walk direction to re-engage the
            # movement machinery.
            if player_object is not None and "heldMovementFinished" not in player_object.flags:
                not_finished_frames += 1
                if not_finished_frames > 90 and not_finished_frames % 10 == 0 and get_game_state() == GameState.OVERWORLD:
                    context.emulator.press_button(waypoint.walking_direction)
            else:
                not_finished_frames = 0
            if player_object is not None and "heldMovementFinished" in player_object.flags:
                if waypoint.action is WaypointAction.Surf:
                    surf_task = "Task_SurfFieldEffect" if not context.rom.is_rs else "sub_8088954"
                    yield from ensure_facing_direction(waypoint.direction)
                    if not field_effect_is_active:
                        if task_is_active(surf_task):
                            field_effect_is_active = True
                        else:
                            context.emulator.press_button("A")
                    elif not task_is_active(surf_task):
                        field_effect_is_active = False
                elif waypoint.action is WaypointAction.Waterfall:
                    waterfall_task = "Task_UseWaterfall" if not context.rom.is_rs else "sub_8086F64"
                    yield from ensure_facing_direction(waypoint.direction)
                    if not field_effect_is_active:
                        if task_is_active(waterfall_task):
                            field_effect_is_active = True
                        else:
                            context.emulator.press_button("A")
                    elif not task_is_active(waterfall_task):
                        field_effect_is_active = False
                elif waypoint.action is WaypointAction.MachBikeSlope:
                    from .higher_level_actions import mount_bicycle, unmount_bicycle

                    if AvatarFlags.OnMachBike not in get_player_avatar().flags:
                        yield from mount_bicycle()

                    last_known_location = get_player_location()
                    context.emulator.hold_button("Up")
                    while True:
                        player_location = get_player_location()
                        if last_known_location != player_location:
                            tile_to_north = get_map_data(
                                player_location[0], (player_location[1][0], player_location[1][1] - 1)
                            )
                            if tile_to_north.tile_type != "Muddy Slope":
                                break
                        yield
                    context.emulator.release_button("Up")
                    while get_player_avatar().running_state is not RunningState.NOT_MOVING:
                        yield
                    yield from unmount_bicycle()
                    yield
                elif (
                    waypoint.action is WaypointAction.MachBikeMount
                    and AvatarFlags.OnMachBike not in get_player_avatar().flags
                ):
                    from .higher_level_actions import mount_bicycle

                    yield from mount_bicycle()
                elif (
                    waypoint.action is WaypointAction.AcroBikeMount
                    and AvatarFlags.OnAcroBike not in get_player_avatar().flags
                ):
                    from .higher_level_actions import mount_bicycle

                    yield from mount_bicycle()
                elif waypoint.action is WaypointAction.AcroBikeSideJump:
                    context.emulator.press_button(waypoint.walking_direction)
                    context.emulator.press_button("B")
                elif waypoint.action is WaypointAction.AcroBikeBunnyHop:
                    from .higher_level_actions import mount_bicycle

                    yield from mount_bicycle()
                    if get_player_avatar().acro_bike_state is not AcroBikeState.HOPPING_WHEELIE:
                        context.emulator.release_button("B")
                        yield
                        context.emulator.hold_button("B")
                        while get_player_avatar().acro_bike_state is not AcroBikeState.HOPPING_WHEELIE:
                            yield
                    context.emulator.hold_button(waypoint.walking_direction)
                else:
                    context.emulator.hold_button(waypoint.walking_direction)
                    if (
                        run
                        and not waypoint.is_water_tile
                        and not AvatarFlags.OnAcroBike in get_player_avatar().flags
                        and not AvatarFlags.Underwater in get_player_avatar().flags
                    ):
                        context.emulator.hold_button("B")
            else:
                context.emulator.reset_held_buttons()
                if waypoint.action is WaypointAction.AcroBikeBunnyHop:
                    context.emulator.hold_button("B")

            yield

    if final_facing_direction is not None:
        context.emulator.reset_held_buttons()
        while get_player_avatar().facing_direction != final_facing_direction.button_name:
            context.emulator.hold_button(final_facing_direction.button_name)
            yield

    # Wait for player to come to a full stop.
    context.emulator.reset_held_buttons()
    while not player_avatar_is_standing_still() or get_player_avatar().running_state != RunningState.NOT_MOVING:
        # If we reached the destination tile and the script context is enabled, that probably means
        # that a script has triggered at our destination. In that case, we cease control back to the
        # bot mode immediately.
        if last_waypoint is None or player_is_at(last_waypoint.map, last_waypoint.coordinates):
            if get_global_script_context().is_active:
                break
        yield


@debug.track
def navigate_to(
    map: tuple[int, int] | MapFRLG | MapRSE,
    coordinates: tuple[int, int],
    run: bool = True,
    avoid_encounters: bool = True,
    avoid_scripted_events: bool = True,
    expecting_script: bool = False,
    final_facing_direction: Direction | None = None,
) -> Generator:
    """
    Tries to walk the player to a given location while circumventing obstacles.

    It works across different maps, but only if they are directly connected. Warps (doors, cave entrances, ...) will not
    be used automatically -- but a door can be used as a destination.

    It will also not attempt to start or stop surfing, i.e. transitions between land and water need to be handled
    separately.

    :param map: Destination map. This can either be a `MapFRLG`/`MapRSE` instance, or a map group/number tuple.
    :param coordinates: Local coordinates on the destination map that should be navigated to.
    :param run: Whether to sprint (hold B.) This is ignored when riding a bicycle.
    :param avoid_encounters: Prefer navigating via tiles that do not have encounters (i.e. try to avoid tall grass etc.)
                             This will still navigate via tiles with encounters if there is no other option.
                             It will also not avoid the activation range of unbattled trainers.
    :param avoid_scripted_events: Try to avoid tiles that would trigger a scripted event when moving onto them. It will
                                  still navigate via those tiles of there is no other option.
    :param expecting_script: This will accept if a script is triggered during navigation (presumably at the destination)
                             and will not show an error about that.
    :param final_facing_direction: A direction that the player avatar should face after reaching its
                                   destination. This can be useful to make it bump into an obstacle with
                                   the Mach Bike.
    """

    def waypoint_generator():
        destination_map = map
        destination_coordinates = coordinates

        while not player_is_at(destination_map, destination_coordinates):
            try:
                waypoints = calculate_path(
                    get_player_location(),
                    (map, coordinates),
                    avoid_encounters=avoid_encounters,
                    avoid_scripted_events=avoid_scripted_events,
                    has_acro_bike=get_item_bag().quantity_of(get_item_by_name("Acro Bike")) > 0,
                    has_mach_bike=get_item_bag().quantity_of(get_item_by_name("Mach Bike")) > 0,
                )
            except PathFindingError as e:
                raise BotModeError(str(e))

            if len(waypoints) == 0:
                return

            # If the final destination turns out to be a warp, we are not going to end up in the place specified by
            # the `map` and `coordinates` parameters, but rather on another map. Because that would lead to this
            # function thinking we've missed the target, we will override the destination with the warp destination
            # in those cases.
            if waypoints[-1].is_warp:
                destination_map = waypoints[-1].map
                destination_coordinates = waypoints[-1].coordinates

            yield from waypoints

    # KI-15 no-progress tracking (see NavigationStuckError). A window of the
    # most recent timeout positions distinguishes a genuinely-advancing nav (it
    # keeps reaching NEW tiles) from a wedge (it only re-hits a tiny set — a
    # (5,6)<->(5,7) bounce or a total freeze).
    recent_stuck_positions: list = []
    no_progress_repaths = 0
    while True:
        try:
            yield from follow_waypoints(waypoint_generator(), run, final_facing_direction=final_facing_direction)
            break
        except TimedOutTryingToReachWaypointError:
            # If we run into a timeout while trying to follow the waypoints, this is likely because of either of
            # these reasons:
            #
            # (a) For some weird reason the player avatar moved to an unexpected location (for example due to forced
            #     movement, or due to overshooting on the Mach Bike.)
            # (b) Since the path is calculated in the beginning and then just followed, there's a chance that an NPC
            #     moves and gets in our way, in which case we would just keep running into them until they finally move
            #     out of the way again.
            # (c) We have moved over a tile that triggered a script which froze the player avatar.
            #
            # In these cases, the `follow_waypoints()` function will trigger this timeout exception.
            #
            # In the first two  cases, We will just calculate a new path (from the new location, taking into account
            # the new location of obstacles) and try pathing again.
            #
            # In the third case, we consider that an unexpected event and will abort the navigation.
            if get_global_script_context().is_active:
                if expecting_script:
                    return
                else:
                    raise BotModeError(
                        f"We unexpectedly triggered a scripted event while trying to reach {coordinates} @ {map}.\nSwitching to manual mode."
                    )

            # FORK (2026-07-23, KI-15): before re-pathing, let any in-flight
            # transition settle. An inline battle can fire mid-navigation; when it
            # ends, control returns HERE with the post-battle
            # ReturnFromBattleToOverworld transition still completing, and
            # re-pathing into that unsettled state makes the avatar bounce between
            # two tiles forever. Waiting for a stably standing-still, controllable
            # avatar lets the transition finish. Bounded so it can never hang here.
            # ‼ JOLT (2026-07-24, ch12 gym-door wedge): one post-battle variant
            # leaves the avatar controllable but with heldMovementFinished
            # PERMANENTLY absent — and every polite layer (this wait, the walk
            # loop, ensure_facing_direction) presses nothing at it, which is
            # exactly what keeps it parked (probed live: any direction input
            # revives it instantly; zero input left it frozen 20k frames). After a
            # patient stretch with no stillness, tap direction keys to re-engage
            # the movement machinery; a step in a wrong direction is harmless —
            # we re-path right after.
            settle = 0
            settle_waited = 0
            _jolt_dirs = ("Down", "Up", "Left", "Right")
            while settle < _NAVIGATE_SETTLE_STABLE_FRAMES and settle_waited < _NAVIGATE_SETTLE_TIMEOUT_FRAMES:
                if player_avatar_is_controllable() and player_avatar_is_standing_still():
                    settle += 1
                else:
                    settle = 0
                settle_waited += 1
                if settle_waited > 90 and settle_waited % 15 == 0 and get_game_state() == GameState.OVERWORLD:
                    context.emulator.press_button(_jolt_dirs[(settle_waited // 15) % 4])
                yield

            # Hard backstop: if we keep timing out without reaching any NEW tile
            # (the transition never completes, or a true wedge), abort in a bounded
            # number of frames so the caller's recovery runs — instead of spinning
            # until a story watchdog trips ~20k frames later.
            try:
                here = get_player_location()
            except Exception:
                here = None
            if here is not None and here in recent_stuck_positions:
                no_progress_repaths += 1
            else:
                no_progress_repaths = 0
                if here is not None:
                    recent_stuck_positions.append(here)
                    if len(recent_stuck_positions) > 6:
                        recent_stuck_positions.pop(0)
            if no_progress_repaths >= _NAVIGATE_NO_PROGRESS_REPATHS:
                raise NavigationStuckError(map, coordinates, here)


@debug.track
def walk_one_tile(direction: str, run: bool = True) -> Generator:
    """
    Moves the player one tile in a given direction, and then waiting for the movement
    to finish and any map transitions to complete before returning.

    Note that this will not check whether the destination tile is actually accessible
    so making sure of that is the responsibility of the calling code. It will create
    an endless loop if trying to run into a wall because the player's coordinates will
    never change.

    :param direction: One of "Up", "Down", "Left", "Right"
    :param run: Whether the player should run (hold down B)
    """
    if direction not in ("Up", "Down", "Left", "Right"):
        raise ValueError(f"'{direction}' is not a valid direction.")

    if run:
        context.emulator.hold_button("B")

    starting_position = get_player_avatar().local_coordinates
    context.emulator.hold_button(direction)
    while get_player_avatar().local_coordinates == starting_position:
        yield
    context.emulator.release_button(direction)
    context.emulator.release_button("B")

    # Wait for player to come to a full stop.
    while (
        not player_avatar_is_standing_still()
        or get_player_avatar().running_state != RunningState.NOT_MOVING
        or get_player_avatar().tile_transition_state != TileTransitionState.NOT_MOVING
    ):
        yield


@debug.track
def ensure_facing_direction(facing_direction: str | Direction | tuple[int, int]) -> Generator:
    """
    If the player avatar is not already facing a certain direction this will make it turn
    around, so that afterwards it definitely faces the desired direction.
    :param facing_direction: One of "Up", "Down", "Left", or "Right"
    """
    if isinstance(facing_direction, tuple):
        x, y = get_player_avatar().local_coordinates
        if (x - 1, y) == facing_direction:
            facing_direction = "Left"
        elif (x + 1, y) == facing_direction:
            facing_direction = "Right"
        elif (x, y - 1) == facing_direction:
            facing_direction = "Up"
        elif (x, y + 1) == facing_direction:
            facing_direction = "Down"
        else:
            raise BotModeError(f"Tile ({x}, {y}) is not adjacent to the player.")

    if isinstance(facing_direction, Direction):
        facing_direction = facing_direction.button_name

    scene_frames = 0
    starved_frames = 0
    total_frames = 0
    phantom_frames = 0
    script_gate_disabled = False
    while True:
        avatar = get_player_avatar()
        if avatar.facing_direction == facing_direction:
            return

        # ‼ ABSOLUTE BOUND (2026-07-24, starter-run torchic f1638181 — R111 (18,99), the
        # SAME tile as batch2 run04). The two guards below are both branch-local and a
        # post-battle state exists that reaches NEITHER: the avatar reads perfectly
        # settled (OVERWORLD + NOT_MOVING + NOT_MOVING), so we take the "press the
        # direction" branch, which RESETS starved_frames to 0 every frame — while the
        # press never actually lands and facing_direction never changes. Result: an
        # infinite press loop that no branch counter can see, running until the 20k
        # story watchdog. A turn is a sub-second action; anything past a few seconds is
        # a wedge no matter which branch we are in, so bound the WHOLE loop and let the
        # caller's recovery re-path.
        #
        # ‼ CORRECTION (same day, caught reviewing the phantom-escape diff): this counter
        # originally incremented HERE, at the very top, so it also counted frames spent
        # legitimately riding out a field script below — silently shrinking that branch's
        # own 4800-frame tolerance to 1800 and making its bound dead code. A real cutscene
        # lasting 30-80 seconds would have started raising instead of being ridden out. The
        # bug this bound exists for is the PRESS loop (a turn that never lands), so it must
        # count only frames on the pressing path. The script branch keeps its own 4800
        # bound and `continue`s before reaching here.
        if not get_global_script_context().is_active or script_gate_disabled:
            total_frames += 1
            if total_frames > 1800:
                from modules.modes import BotModeError

                raise BotModeError(
                    f"ensure_facing_direction: could not face {facing_direction} after "
                    f"{total_frames} pressing frames (input not landing — stale-reader wedge?)."
                )

        # FORK (2026-07-22, story-bot hardening): a field script can fire the very
        # moment we start turning — on real hardware a Route 116 trainer's sight-line
        # intro (EventScript_ShowTrainerIntroMsg) opened its msgbox mid-turn and this
        # stock loop pressed direction keys at a script-locked avatar for 85,000+
        # frames. While a script holds the field, advance IT (B) instead of turning —
        # a trainer intro then proceeds to its battle (which the battle listener
        # handles) and the turn resumes afterwards. Bounded so a scene that never
        # ends surfaces as a BotModeError for the caller's recovery instead of a hang.
        if not script_gate_disabled and get_global_script_context().is_active:
            # PHANTOM-SCRIPT ESCAPE (2026-07-24, Route 111 (18,99) — the
            # EventScript_SmashRock-parked-forever hang, KI-15/16 family): Rock
            # Smash's wild-encounter roll can battle-interrupt the field script and
            # leave get_global_script_context().is_active reading True for the REST
            # OF THE RUN while the game is fully playable — probed live on the
            # captured wedge state: the avatar is controllable and pressing the
            # actual direction turns/walks it INSTANTLY even though gsc.is_active
            # never clears (25000 frames, zero input). It is a stale reader, not a
            # real lock. Mashing B at a parked context does nothing, so this branch
            # used to burn the whole `total_frames` budget every call and raise
            # "input not landing" on repeat forever (StoryMode.run <-> raise loop).
            # A real scene either locks the avatar (controllable=False) or opens a
            # waiting-for-input prompt (is_waiting_for_input()=True) — neither of
            # which persists this way. After a bounded stretch of playable-but-
            # active, stop deferring to the script gate for the REST OF THIS CALL
            # and fall through to actually turning/walking.
            if player_avatar_is_controllable() and not is_waiting_for_input():
                phantom_frames += 1
                if phantom_frames >= 600:
                    script_gate_disabled = True
                    continue
            else:
                phantom_frames = 0
            scene_frames += 1
            if scene_frames > 4800:
                from modules.modes import BotModeError

                raise BotModeError("ensure_facing_direction: a field script never released the avatar.")
            context.emulator.press_button("B")
            yield
            continue

        if (
            get_game_state() == GameState.OVERWORLD
            and avatar.tile_transition_state == TileTransitionState.NOT_MOVING
            and avatar.running_state == RunningState.NOT_MOVING
        ):
            context.emulator.press_button(facing_direction)
            starved_frames = 0
        else:
            # FORK (2026-07-24, KI-15 family — the third starving limb): a battle
            # that ends mid-navigation can leave the avatar with its movement state
            # PERMANENTLY not-NOT_MOVING while no script runs — and this branch then
            # pressed NOTHING forever (batch2 run04: 20k frames parked right here at
            # R111 (18,99)). Zero input is exactly what keeps that state parked
            # (probed: any direction press revives it). After a patient stretch,
            # press the turn direction anyway; bound the whole starve so the caller's
            # recovery gets the wheel if even that can't move it.
            starved_frames += 1
            if starved_frames > 120 and starved_frames % 10 == 0:
                context.emulator.press_button(facing_direction)
            if starved_frames > 3000:
                from modules.modes import BotModeError

                raise BotModeError(
                    "ensure_facing_direction: the avatar's movement state never settled "
                    "(post-battle freeze?)."
                )

        yield


@debug.track
def run_in_circle(
    on_map: tuple[int, int] | MapRSE | MapFRLG,
    bottom_left: tuple[int, int],
    top_right: tuple[int, int],
    clockwise: bool = True,
    exit_condition: Callable[[], bool] | None = None,
):
    """
    Function name is lying: This actually makes the character run in a _square_

    The entirety of the circle (or, uh, square) needs to be within one map and must
    be free of obstructions.

    :param on_map: Map to run on
    :param bottom_left: Bottom-left (south-west) corner of the circle/square.
    :param top_right: Top-right (north-east) corner of the circle/square.
    :param clockwise: Which direction to run (True = clockwise, False = anti-clockwise)
    :param exit_condition: If set, the running will stop once this callback returns True.
                           Otherwise, it will never stop unless interrupted from the
                           outside.
    """

    if bottom_left[0] >= top_right[0]:
        raise RuntimeError(
            f"Bottom-left corner ({bottom_left}) must be to the west of the top-right corner ({top_right})"
        )

    if bottom_left[1] <= top_right[1]:
        raise RuntimeError(
            f"Bottom-left corner ({bottom_left}) must be to the south of the top-right corner ({top_right})"
        )

    def circle_waypoints_generator():
        if isinstance(on_map, MapRSE) or isinstance(on_map, MapFRLG):
            waypoint_map = on_map.value
        else:
            waypoint_map = on_map

        width = top_right[0] - bottom_left[0]
        height = bottom_left[1] - top_right[1]
        current_location = bottom_left[0], bottom_left[1]

        def north():
            nonlocal current_location
            for _ in range(height):
                current_location = (current_location[0], current_location[1] - 1)
                yield Waypoint(Direction.North, waypoint_map, current_location, False)

        def east():
            nonlocal current_location
            for _ in range(width):
                current_location = (current_location[0] + 1, current_location[1])
                yield Waypoint(Direction.East, waypoint_map, current_location, False)

        def south():
            nonlocal current_location
            for _ in range(height):
                current_location = (current_location[0], current_location[1] + 1)
                yield Waypoint(Direction.South, waypoint_map, current_location, False)

        def west():
            nonlocal current_location
            for _ in range(width):
                current_location = (current_location[0] - 1, current_location[1])
                yield Waypoint(Direction.West, waypoint_map, current_location, False)

        if clockwise:
            waypoint_list = [*north(), *east(), *south(), *west()]
        else:
            waypoint_list = [*east(), *north(), *west(), *south()]

        yield from calculate_path(get_map_data_for_current_position(), (on_map, bottom_left))
        while True:
            for waypoint in waypoint_list:
                if exit_condition is not None and exit_condition():
                    return
                yield waypoint

    yield from follow_waypoints(circle_waypoints_generator())


@debug.track
def wait_for_player_avatar_to_be_controllable(button_to_press: str | None = None) -> Generator:
    while not player_avatar_is_controllable():
        if button_to_press is not None:
            context.emulator.press_button(button_to_press)
        yield


@debug.track
def wait_for_player_avatar_to_be_standing_still(button_to_press: str | None = None) -> Generator:
    # FORK (2026-07-24, KI-15 family): a post-battle freeze can leave the avatar
    # permanently "moving" while nothing presses at it — the exact input-starved
    # state that only an input edge revives. After a patient stretch, tap a
    # direction (a step is harmless — callers re-check position/paths anyway);
    # bound the whole wait so no caller can silently spin 20k frames here.
    starved = 0
    _jolt_dirs = ("Down", "Up", "Left", "Right")
    while not player_avatar_is_standing_still():
        if button_to_press is not None:
            context.emulator.press_button(button_to_press)
        starved += 1
        if button_to_press is None and starved > 240 and starved % 15 == 0:
            context.emulator.press_button(_jolt_dirs[(starved // 15) % 4])
        if starved > 3000:
            from modules.modes import BotModeError

            raise BotModeError(
                "wait_for_player_avatar_to_be_standing_still: the avatar never settled "
                "(post-battle freeze?)."
            )
        yield
