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
HOUSE_1F_STAIRS = (8, 2)   # warp up to 2F
CLOCK_FACE_TILE = (5, 2)   # stand here facing North to use the wall clock at (5,1)


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
