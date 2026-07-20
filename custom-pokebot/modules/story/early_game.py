"""Story-mode early game — Chapter 0 tail + Chapter 1 (the post-intro stretch).

Picks up where `intro.run_intro()` leaves off (controllable inside the moving
truck) and works toward the starter + first battle, one testable step at a time.

Like the intro, this is driven by observed game state (maps, coordinates,
script names, control-lock) rather than event flags, because this early stretch
is almost entirely scripted. Verified against a save state parked in the truck.
"""

from __future__ import annotations

from typing import Generator

from modules.context import context
from modules.map import get_map_data_for_current_position
from modules.map_path import Direction
from modules.modes import BotModeError
from modules.modes.util.tasks_scripts import wait_until_task_is_active
from modules.modes.util.sleep import wait_for_n_frames
from modules.modes.util.walking import (
    navigate_to,
    wait_for_player_avatar_to_be_controllable,
)
from modules.player import player_avatar_is_controllable
from modules.tasks import get_global_script_context, task_is_active

MAP_INSIDE_OF_TRUCK = "INSIDE OF TRUCK"
# Map group/number constants (map_name reads stale across warps; use these).
MAP_PLAYERS_HOUSE_1F = (1, 0)
MAP_PLAYERS_HOUSE_2F = (1, 1)
MAP_LITTLEROOT_TOWN = (0, 9)
HOUSE_1F_STAIRS = (8, 2)          # 1F warp up to 2F
CLOCK_FACE_TILE = (5, 2)          # stand here facing North to use the wall clock at (5,1)
HOUSE_2F_STAIRS_DOWN = (7, 1)     # 2F warp down to 1F
HOUSE_1F_DOOR_APPROACH = (8, 7)   # tile above the front door; step South to exit


def _map_group_number() -> tuple[int, int] | None:
    try:
        md = get_map_data_for_current_position()
        return (md.map_group, md.map_number)
    except Exception:
        return None


def _walk_through_warp(direction: str, from_map: tuple[int, int], *, timeout_frames: int = 240) -> Generator:
    """Step in ``direction`` until the current map changes (i.e. a warp/door was
    used). Used for doors that can't be a pathfinding destination."""
    frames = 0
    while _map_group_number() == from_map:
        context.emulator.press_button(direction)
        frames += 1
        if frames > timeout_frames:
            raise BotModeError(f"Did not pass through the {direction} warp from map {from_map}.")
        yield


def _ride_out_scripted_scene(button: str = "B", *, engage_timeout: int = 240) -> Generator:
    """Wait for a scripted scene to ENGAGE (bounded) then ride it out until
    control returns. Waiting for engagement first avoids treating the calm
    moment before a scene as 'already over'."""
    frames = 0
    while not get_global_script_context().is_active:
        frames += 1
        if frames > engage_timeout:
            break  # no scene fired; nothing to ride out
        yield
    yield from _wait_until_cutscene_over(button)


def _wait_for_task(task_name: str, button: str | None = None, *, timeout_frames: int = 1200) -> Generator:
    """Bounded wait for a task to become active (raises on timeout)."""
    frames = 0
    while not task_is_active(task_name):
        if button is not None:
            context.emulator.press_button(button)
        frames += 1
        if frames > timeout_frames:
            raise BotModeError(f"Timed out waiting for task '{task_name}'.")
        yield


def _current_map_name() -> str:
    try:
        return get_map_data_for_current_position().map_name
    except Exception:
        return ""


def _wait_until_cutscene_over(button: str = "B", *, stable_frames: int = 15,
                              timeout_frames: int = 8000) -> Generator:
    """Mash ``button`` until the player is controllable AND no script is running,
    held for ``stable_frames`` consecutive frames.

    A single-frame check is not enough during these arrival cutscenes: there are
    brief windows where the script is 'active' but the avatar isn't locked yet
    (start of a script) or the avatar is locked while no script runs (a warp in
    between scripts). Requiring both conditions to hold for a short stretch means
    we only stop once control has genuinely returned."""
    stable = 0
    frames = 0
    while stable < stable_frames:
        free = player_avatar_is_controllable() and not get_global_script_context().is_active
        stable = stable + 1 if free else 0
        if not free:
            context.emulator.press_button(button)
        frames += 1
        if frames > timeout_frames:
            raise BotModeError(
                f"Cutscene did not end after {timeout_frames} frames "
                f"(controllable={player_avatar_is_controllable()}, "
                f"script_active={get_global_script_context().is_active})."
            )
        yield


def walk_off_truck_and_into_house() -> Generator:
    """From inside the moving truck, step out into Littleroot; Professor Birch's
    town greeting (Mom) auto-plays and walks the player into their house. Ends
    with the player controllable on the ground floor of their house.

    Observed flow (from the truck-parked base state): walk east onto the exit
    warp -> LITTLEROOT TOWN -> `LittlerootTown_EventScript_StepOffTruckMale` /
    `GoInsideWithMom` (Mom escorts you) -> warp into `PlayersHouse_1F` -> Mom's
    "set the clock upstairs" speech -> control returns inside the house.
    """
    # 1. Walk east onto the truck's exit warp (player starts at local (2,2),
    #    warps are the column at x=4). Bounded so a missed warp doesn't hang.
    context.message = "Story: stepping off the truck..."
    frames = 0
    while _current_map_name() == MAP_INSIDE_OF_TRUCK:
        context.emulator.press_button("Right")
        frames += 1
        if frames > 300:
            raise BotModeError("Could not step off the truck (still INSIDE OF TRUCK).")
        yield

    # 2. Ride the whole Mom cutscene (escort + warp into the house + her speech)
    #    until control genuinely returns. Requiring controllable-AND-no-script
    #    for a sustained stretch avoids stopping in the brief window where Mom's
    #    script has started but hasn't locked the avatar yet.
    context.message = "Story: Mom's welcome (heading into the house)..."
    yield from _wait_until_cutscene_over("B")

    context.message = "Story: inside the house — next, set the clock upstairs."


def go_upstairs_and_set_clock() -> Generator:
    """From the ground floor of the player's house, go up to the bedroom and set
    the wall clock, accepting whatever time it defaults to (no adjustment).

    Clock flow (Emerald `Task_SetClock_*`): interact -> `HandleInput` (the
    time-set UI) -> press A to accept the shown time -> `HandleConfirmInput`
    (Yes/No, whose cursor DEFAULTS TO NO) -> move Up to Yes + A -> done. Ends
    with the player controllable in the 2F bedroom."""
    # 1. Up the stairs (a warp) to the 2F bedroom.
    context.message = "Story: heading upstairs to the bedroom..."
    yield from navigate_to(MAP_PLAYERS_HOUSE_1F, HOUSE_1F_STAIRS)

    # 2. Stand below the wall clock, facing it.
    yield from navigate_to(
        MAP_PLAYERS_HOUSE_2F, CLOCK_FACE_TILE,
        final_facing_direction=Direction.North, expecting_script=True,
    )

    # 3. Interact and advance the intro dialogue to the time-set UI.
    context.message = "Story: setting the clock (accepting the default time)..."
    context.emulator.press_button("A")
    yield
    yield from _wait_for_task("Task_SetClock_HandleInput", "A")
    yield from wait_for_n_frames(40)  # let the clock UI finish fading in

    # 4. Accept the shown time -> opens the Yes/No confirm.
    context.emulator.press_button("A")
    yield
    yield from _wait_for_task("Task_SetClock_HandleConfirmInput")

    # 5. Select YES (cursor defaults to No, so move Up first), then confirm.
    context.emulator.press_button("Up")
    yield
    yield from wait_for_n_frames(6)
    context.emulator.press_button("A")
    yield

    # 6. Ride out the closing dialogue until control returns in the bedroom.
    yield from wait_for_player_avatar_to_be_controllable("B")
    context.message = "Story: clock set — bedroom done."


def descend_and_leave_players_house() -> Generator:
    """After the clock: Mom comes upstairs to talk (triggered by moving); go
    back down, where the Petalburg-Gym TV report scene auto-plays (walks you to
    the TV, Mom comments on your dad); then leave through the front door into
    Littleroot Town. Ends controllable outside the player's house."""
    # 1. Nudge to trigger Mom coming upstairs, then ride out her chat.
    context.message = "Story: Mom's chat, then downstairs..."
    frames = 0
    while not get_global_script_context().is_active:
        context.emulator.press_button("Down")
        frames += 1
        if frames > 180:
            break  # no Mom event (revision differences) — proceed anyway
        yield
    yield from _wait_until_cutscene_over("B")

    # 2. Down the stairs to the ground floor.
    yield from navigate_to(MAP_PLAYERS_HOUSE_2F, HOUSE_2F_STAIRS_DOWN)

    # 3. The Petalburg-Gym TV scene auto-plays on arrival (it walks the player to
    #    the TV at (4,5)). Ride it out — do NOT navigate during it or the moving
    #    player fights the pathfinder.
    context.message = "Story: watching the Gym report on TV..."
    yield from _ride_out_scripted_scene("B")

    # 4. Out the front door into Littleroot Town.
    context.message = "Story: heading outside..."
    yield from navigate_to(MAP_PLAYERS_HOUSE_1F, HOUSE_1F_DOOR_APPROACH)
    yield from _walk_through_warp("Down", MAP_PLAYERS_HOUSE_1F)
    yield from wait_for_player_avatar_to_be_controllable("B")
    context.message = "Story: outside — heading to the rival's house."


RIVAL_HOUSE_DOOR_TOWN = (14, 8)     # Littleroot warp into the rival's house
MAP_RIVAL_HOUSE_1F = (1, 2)
MAP_RIVAL_HOUSE_2F = (1, 3)
RIVAL_1F_STAIRS = (2, 2)            # 1F warp up to 2F
RIVAL_2F_STAIRS_DOWN = (1, 1)       # 2F warp down to 1F
RIVAL_POKEBALL_FACE = (5, 5)        # stand here facing North; the Poké Ball is at (5,4)
RIVAL_1F_DOOR_APPROACH = (2, 7)     # tile above the rival-house door; step South to exit


def visit_rivals_house() -> Generator:
    """Go next door to the rival's house: the rival's mom greets you on entry
    (automatic), then upstairs, touch the Poké Ball to trigger the rival's
    introduction, and come back out. Ends controllable outside in Littleroot —
    the end of this chunk (next up: Route 101, help Birch, choose a starter)."""
    # 1. Enter the rival's house (walk onto the door warp).
    context.message = "Story: going to the rival's house..."
    yield from navigate_to(MAP_LITTLEROOT_TOWN, RIVAL_HOUSE_DOOR_TOWN, expecting_script=True)

    # 2. The rival's mom greets you automatically on entry — ride it out.
    context.message = "Story: the neighbor's mom says hello..."
    yield from _ride_out_scripted_scene("B")

    # 3. Upstairs to the rival's room.
    yield from navigate_to(MAP_RIVAL_HOUSE_1F, RIVAL_1F_STAIRS, expecting_script=True)

    # 4. Touch the Poké Ball -> the rival rushes in and introduces themselves.
    context.message = "Story: meeting the rival..."
    yield from navigate_to(
        MAP_RIVAL_HOUSE_2F, RIVAL_POKEBALL_FACE,
        final_facing_direction=Direction.North, expecting_script=True,
    )
    context.emulator.press_button("A")
    yield
    yield from _ride_out_scripted_scene("B")

    # 5. Back downstairs.
    context.message = "Story: heading back out..."
    yield from navigate_to(MAP_RIVAL_HOUSE_2F, RIVAL_2F_STAIRS_DOWN, expecting_script=True)

    # 6. Out the front door into Littleroot.
    yield from navigate_to(MAP_RIVAL_HOUSE_1F, RIVAL_1F_DOOR_APPROACH)
    yield from _walk_through_warp("Down", MAP_RIVAL_HOUSE_1F)
    yield from wait_for_player_avatar_to_be_controllable("B")
    context.message = "Story: back outside the rival's house — chunk complete!"
