"""Story-mode early game — Chapter 0 tail + Chapter 1 (the post-intro stretch).

Picks up where `intro.run_intro()` leaves off (controllable inside the moving
truck) and works toward the starter + first battle, one testable step at a time.

Like the intro, this is driven by observed game state (maps, coordinates,
script names, control-lock) rather than event flags, because this early stretch
is almost entirely scripted. Verified against a save state parked in the truck.
"""

from __future__ import annotations

import random
from typing import Generator

from modules.context import context
from modules.keyboard import get_naming_screen_data, type_in_naming_screen
from modules.map import get_map_data_for_current_position
from modules.map_data import MapRSE, PokemonCenter
from modules.map_path import Direction
from modules.memory import GameState, get_game_state
from modules.modes import BotModeError
from modules.modes.util.tasks_scripts import (
    wait_for_yes_no_question,
    wait_until_script_is_no_longer_active,
    wait_until_task_is_active,
)
from modules.modes.util.sleep import wait_for_n_frames
from modules.modes.util import spin
from modules.modes.util.global_navigation import navigate_to_anywhere
from modules.modes.util.higher_level_actions import heal_in_pokemon_center
from modules.modes.util.walking import (
    navigate_to,
    wait_for_player_avatar_to_be_controllable,
)
from modules.player import get_player_avatar, player_avatar_is_controllable
from modules.pokemon_party import get_party
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
    context.message = "Story: back outside the rival's house - rival intro done!"


# --- Route 101: help Birch, choose a starter, win the first battle ----------
LITTLEROOT_NORTH_APPROACH = (11, 3)   # walk here, then step North through the GoSaveBirch trigger
ROUTE101_BAG_FACE = (8, 14)           # stand here facing West; Birch's bag is at (7,14)
STARTER_BY_NAME = {"treecko": "Treecko", "torchic": "Torchic", "mudkip": "Mudkip"}


def _go_north_to_birch_rescue() -> Generator:
    """Leave Littleroot to the north to trigger Professor Birch's rescue.

    INTENT: get the player onto Route 101 and into the state where Birch's bag
    is interactable.
    STORY CONDITION: the player has met the rival but has no Pokémon yet, so the
    north edge of Littleroot fires `GoSaveBirch` (not the `NeedPokemon` block).
    HOW IT WORKS: walk to the north approach, then step North through the
    trigger at (11,1). The game crosses to Route 101 (0,16) and
    `Route101_EventScript_StartBirchRescue` AUTO-WALKS the player up the route
    (to ~(11,15)) while Birch yells, then returns control. We alternate Up (to
    keep walking north in town) with B (to advance dialogue), and stop once we
    are on Route 101, controllable, and no script is running for a sustained
    stretch - the moment free control is genuinely handed over near the bag."""
    context.message = "Story: heading north - Professor Birch needs help!"
    yield from navigate_to(MAP_LITTLEROOT_TOWN, LITTLEROOT_NORTH_APPROACH)

    # Keep walking North (advancing dialogue with B) until the Route 101 rescue
    # script actually FIRES. There is a brief window right after crossing the
    # border where the player is momentarily "free" at (11,19) but the rescue
    # hasn't triggered yet — we must NOT stop there, or we get boxed in before
    # the scene auto-walks us up to the bag.
    frames = 0
    while True:
        script = get_global_script_context()
        on_route_101 = _map_group_number() == MapRSE.ROUTE101.value
        rescue_firing = on_route_101 and any(
            "StartBirchRescue" in s for s in (script.stack or [])
        )
        if rescue_firing:
            break
        context.emulator.press_button("Up" if frames % 2 == 0 else "B")
        frames += 1
        if frames > 3000:
            raise BotModeError("Never triggered the Birch rescue on Route 101.")
        yield

    # Ride out the rescue: it auto-walks the player up the route and plays
    # Birch's dialogue, then hands back control near the bag (~(11,15)).
    yield from _wait_until_cutscene_over("B")


def _choose_starter(resolved_species: str) -> Generator:
    """Open Birch's bag and select the given starter, then confirm into battle.

    HOW IT WORKS (Emerald bag menu, `Task_HandleStarterChooseInput`): the three
    Poké Balls are laid out Treecko | Torchic | Mudkip with the cursor starting
    on the middle (Torchic). Left picks Treecko, Right picks Mudkip, no move
    keeps Torchic. Mashing A then confirms the "Do you choose this POKéMON?"
    prompt, which starts the battle vs the wild Pokémon attacking Birch."""
    context.message = f"Story: choosing {resolved_species}!"
    yield from wait_until_task_is_active("Task_HandleStarterChooseInput", "A")
    yield
    if resolved_species == "Treecko":
        context.emulator.press_button("Left")
        yield
    elif resolved_species == "Mudkip":
        context.emulator.press_button("Right")
        yield
    # else Torchic: leave the cursor on the middle ball.

    # Confirm through to the battle start (BATTLE_STARTING/BATTLE).
    frames = 0
    while get_game_state() not in (GameState.BATTLE, GameState.BATTLE_STARTING):
        context.emulator.press_button("A")
        frames += 1
        if frames > 600:
            raise BotModeError("Confirming the starter never started the first battle.")
        yield


def help_birch_and_choose_starter(starter: str = "random") -> Generator:
    """Chapter 1 core: rescue Birch on Route 101, choose a starter, win the
    first battle.

    INTENT: give the player their first Pokémon and clear the tutorial battle,
    the gate to the rest of the game.
    STORY CONDITION: begins outside in Littleroot after meeting the rival;
    the player still has an empty party.
    GOAL/END STATE: the chosen starter is in the party and the wild Pokémon has
    been defeated; the post-battle scene (Birch thanks you and warps you to his
    lab) has played out and control has returned.
    HOW IT WORKS: `_go_north_to_birch_rescue()` gets us to the bag; `_choose_
    starter()` picks the species (config: "random" or a specific one) and
    confirms into battle. The battle itself is fought by the bot's normal
    BattleListener (StoryMode.on_battle_started returns Fight), during which this
    generator is paused; when it resumes we ride out the post-battle Birch/lab
    transition until control returns.

    :param starter: "random" | "treecko" | "torchic" | "mudkip".
    """
    resolved = STARTER_BY_NAME.get(str(starter).strip().lower())
    if resolved is None:
        resolved = random.choice(list(STARTER_BY_NAME.values()))

    yield from _go_north_to_birch_rescue()
    yield from navigate_to(
        MapRSE.ROUTE101, ROUTE101_BAG_FACE,
        final_facing_direction=Direction.West,
        avoid_encounters=False, expecting_script=True,
    )
    yield from _choose_starter(resolved)

    # The battle is handled by the framework while this generator is paused.
    # When it resumes, the wild Pokémon is beaten and Birch's post-battle scene
    # plays: he thanks you and warps you to his lab. Advance that with B (which
    # also answers 'No' to any incidental Yes/No, e.g. a nickname prompt, which
    # matches the default of keeping the species name) until we arrive in the
    # lab. The lab conversation itself is handled by the next step.
    context.message = "Story: won the first battle! Birch is taking you to his lab..."
    lab = MapRSE.LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB.value
    frames = 0
    while _map_group_number() != lab:
        context.emulator.press_button("B")
        frames += 1
        if frames > 6000:
            raise BotModeError("Never arrived in Professor Birch's lab after the first battle.")
        yield
    yield from wait_for_n_frames(30)
    context.message = "Story: in Professor Birch's lab — got the starter, won the first battle!"


# A small pool of friendly nicknames for the "random" nickname option (nicer
# than random gibberish from the keyboard).
_RANDOM_NICKNAMES = [
    "Sparky", "Ziggy", "Bolt", "Blaze", "Coco", "Pip", "Nova", "Ace",
    "Fern", "Rocky", "Sunny", "Milo", "Kiki", "Turbo", "Gizmo", "Pixel",
]


def _resolve_nickname(nickname_mode: str) -> str:
    if nickname_mode == "random":
        return random.choice(_RANDOM_NICKNAMES)
    return str(nickname_mode)[:10]  # a literal nickname


def finish_birch_lab(nickname_mode: str = "none") -> Generator:
    """Finish Professor Birch's lab conversation after the first battle.

    INTENT: complete the "receive your starter officially" scene so the player
    is free to leave the lab and head toward the rival.
    STORY CONDITION: begins right after arriving in the lab (map 1,4) with the
    starter in the party; `GiveStarterEvent` is running.
    GOAL/END STATE: the lab conversation is fully closed and the player is
    controllable in the lab, free to walk out; the starter is nicknamed per the
    config (or keeps its species name).
    HOW IT WORKS: Birch asks "give a nickname?" (a `Std_MsgboxYesNo`). We answer
    via the proper Yes/No handler (B does NOT dismiss this menu). For "none" we
    answer No; otherwise Yes → the naming screen → type the nickname. The rest
    of Birch's speech is then advanced with B — importantly NOT A, because A
    while facing Birch re-opens his repeatable dialogue in a loop.

    :param nickname_mode: "none" | "random" | a literal nickname string.
    """
    context.message = "Story: Professor Birch is giving you your first Pokémon..."
    # NICKNAME: Birch asks "give a nickname?" (a Std_MsgboxYesNo).
    # For now we always keep the species name (answer No). The Yes → naming
    # path below reaches the keyboard and types, but the typed name does not
    # persist (a post-naming confirm subtlety still to be worked out), and the
    # user has deprioritised nicknames, so it is gated OFF until fixed. The
    # config (`starter_nickname`) and `_resolve_nickname()` remain in place for
    # when it is revisited. See design doc / punch list.
    if nickname_mode != "none":
        context.message = (
            "Story: (starter nickname not wired up yet - keeping the species "
            "name for now.)"
        )
    yield from wait_for_yes_no_question("No")

    # Advance the remainder of the give-starter script until it leaves the
    # stack. We mash A (B does not advance these message boxes), and this helper
    # stops the instant `GiveStarterEvent` ends — BEFORE another A could
    # re-open Birch's repeatable dialogue (A while facing him talks to him).
    context.message = "Story: finishing up in the lab..."
    yield from wait_until_script_is_no_longer_active(
        "LittlerootTown_ProfessorBirchsLab_EventScript_GiveStarterEvent", "A"
    )

    # Birch immediately follows with `GoSeeRival`: he asks you to go find his
    # kid (your rival) on Route 103 — a Yes/No ("will you go?"). Answer YES; No
    # just keeps you stuck in the lab. (The Pokédex is NOT given here; it comes
    # after the rival battle.) Then ride the closing lines out with B (never A —
    # A re-triggers Birch) until control returns and we can walk out.
    context.message = "Story: Birch asks you to go find the rival on Route 103..."
    yield from wait_for_yes_no_question("Yes")
    yield from _wait_until_cutscene_over("B")
    context.message = "Story: done with Birch — free to head north to the rival."


# --- Oldale / Route 103: train the starter, then battle the rival -----------
ROUTE103_GRASS_TILE = (5, 7)     # a tall-grass tile on Route 103 (spin here to train)
ROUTE103_RIVAL_TILE = (10, 3)    # the rival stands here
ROUTE103_RIVAL_APPROACH = (10, 4)  # stand here facing North to talk to the rival


def _lead_hp_pct() -> float:
    party = get_party()
    if not party:
        return 100.0
    try:
        return float(party[0].current_hp_percentage)
    except Exception:
        return 100.0


def _lead_level() -> int:
    party = get_party()
    return party[0].level if party else 0


def travel_to_route103() -> Generator:
    """Travel from Birch's lab up to Route 103 (where the rival is), fighting any
    wild encounters along the way (which starts training the starter). Uses the
    map-by-map chain because the one-shot global route loops on Route 101.

    STORY CONDITION: starts controllable in the lab (1,4) with the starter.
    END STATE: standing on a tall-grass tile on Route 103 (0,18)."""
    context.message = "Story: heading north to Route 103 (training on the way)..."
    yield from navigate_to_anywhere(MAP_LITTLEROOT_TOWN, (6, 9))  # out of the lab, into town
    yield from navigate_to(MapRSE.ROUTE101, (9, 9), avoid_encounters=False)
    yield from navigate_to(MapRSE.OLDALE_TOWN, (9, 9), avoid_encounters=False)
    yield from navigate_to(MapRSE.ROUTE103, ROUTE103_GRASS_TILE, avoid_encounters=False)


def train_lead_to_level(target_level: int) -> Generator:
    """Grind wild battles on Route 103 until the lead reaches ``target_level``,
    healing at the nearest Poké Center (Oldale) whenever HP drops near the
    battle-flee threshold.

    HOW IT WORKS: `spin()` on a grass tile triggers wild encounters, which the
    BattleListener fights with `LevelUpLeadBattleStrategy` (fights the strongest
    move, flees only when HP is low). We stop spinning when either the target
    level is hit or HP falls to the heal threshold; on low HP we walk to the
    Oldale Poké Center, heal, and return to the grass. Prevents the stall where
    a low-HP lead flees every battle and never gains XP."""
    heal_at = float(getattr(context.config.battle, "hp_threshold", 20)) + 8.0
    context.message = f"Story: training the starter to Lv {target_level}..."
    guard = 0
    while _lead_level() < target_level:
        guard += 1
        if guard > 200:
            raise BotModeError("Training did not reach the target level (too many rounds).")
        # Get onto the Route 103 grass (navigate_to_anywhere handles the cross-map
        # trip back from the Poké Center; the built-in find_closest_pokemon_center
        # is unreliable here, so we hard-target Oldale's centre below).
        yield from navigate_to_anywhere(MapRSE.ROUTE103, ROUTE103_GRASS_TILE, avoid_encounters=False)
        yield from spin(stop_condition=lambda: _lead_level() >= target_level or _lead_hp_pct() <= heal_at)
        if _lead_level() >= target_level:
            break
        # Low HP: heal at Oldale's Poké Center (the closest one), then loop back.
        context.message = "Story: starter is low on HP — healing at Oldale's Poké Center..."
        yield from heal_in_pokemon_center(PokemonCenter.OldaleTown)
    context.message = f"Story: trained to Lv {_lead_level()} — off to the rival!"


def fight_route103_rival() -> Generator:
    """Heal to full, then walk to the rival on Route 103 and start the battle
    (fought by the listener). Ends after the post-battle scene.

    WHY HEAL FIRST: the rival is a TRAINER battle, which cannot be fled. The
    LevelUpLead strategy tries to flee at low HP, and the framework raises if
    that happens in a trainer battle. Entering at full HP with a Lv 8-10 starter
    means the (Lv5) rival is beaten decisively without ever reaching the flee
    threshold."""
    # 1. Top up HP at Oldale's Poké Center so the trainer battle is safe.
    context.message = "Story: healing up before the rival..."
    yield from heal_in_pokemon_center(PokemonCenter.OldaleTown)

    # 2. Go to the rival on Route 103, face them, and talk to start the battle.
    context.message = "Story: challenging the rival..."
    yield from navigate_to_anywhere(MapRSE.ROUTE103, ROUTE103_RIVAL_APPROACH, avoid_encounters=False)
    context.emulator.press_button("Up")  # turn to face the rival at (10,3)
    yield
    yield from wait_for_n_frames(4)
    context.emulator.press_button("A")
    yield

    # 3. The rival battle is fought by the framework; when control returns, ride
    #    out the post-battle dialogue (the rival runs off to the lab).
    yield from _ride_out_scripted_scene("B", engage_timeout=1500)
    context.message = "Story: beat the rival! (End of the currently-built story.)"


# --- Return to Birch's lab, receive the Pokédex ------------------------------
def _navigate_through_scripts(dest_map, coordinates, *, avoid_encounters: bool = True,
                              max_rounds: int = 25) -> Generator:
    """navigate_to_anywhere, but ride out any scripted scene that interrupts the
    trip (e.g. the rival stopping you in Oldale after the Route 103 battle) and
    then continue, until the destination map is reached."""
    dest = dest_map.value if hasattr(dest_map, "value") else dest_map
    rounds = 0
    while _map_group_number() != dest:
        rounds += 1
        if rounds > max_rounds:
            raise BotModeError(f"Could not reach {dest} (too many scripted interruptions).")
        try:
            yield from navigate_to_anywhere(dest_map, coordinates, avoid_encounters=avoid_encounters)
        except BotModeError:
            # A scene fired mid-path (a one-shot story event) — ride it out, then retry.
            yield from _ride_out_scripted_scene("B")


def return_to_lab_and_get_pokedex() -> Generator:
    """After beating the rival, head back to Professor Birch's lab to receive the
    Pokédex (and Poké Balls). The rival intercepts you in Oldale on the way
    (`RivalFinish`) — that's ridden out automatically.

    STORY CONDITION: `DEFEATED_RIVAL_ROUTE103` is set; the player is on Route 103.
    GOAL/END STATE: `RECEIVED_POKEDEX_FROM_BIRCH` is set and the player is
    controllable, free to head off toward Petalburg."""
    context.message = "Story: heading back to Professor Birch's lab for the Pokédex..."
    yield from _navigate_through_scripts(
        MapRSE.LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB, (6, 8), avoid_encounters=True
    )

    # In the lab: Birch gives the Pokédex + Poké Balls. Advance the dialogue with
    # A until the Pokédex flag is set, then ride out the rest of the scene.
    context.message = "Story: Professor Birch is giving you the Pokédex..."
    frames = 0
    from modules.memory import get_event_flag

    while not get_event_flag("RECEIVED_POKEDEX_FROM_BIRCH"):
        context.emulator.press_button("A")
        frames += 1
        if frames > 6000:
            raise BotModeError("Never received the Pokédex in Birch's lab.")
        yield
    yield from _wait_until_cutscene_over("B")
    context.message = "Story: got the Pokédex! Time to start the journey to Petalburg."


def _navigate_leg(dest_map, coordinates, *, avoid_encounters: bool = True, max_rounds: int = 12) -> Generator:
    """One leg of a cross-region journey using `navigate_to` (which, unlike the
    global navigator, doesn't loop on Route 101), retrying around any scripted
    scene that interrupts it (running-shoes gift, city-entry events, etc.)."""
    dest = dest_map.value if hasattr(dest_map, "value") else dest_map
    rounds = 0
    while _map_group_number() != dest:
        rounds += 1
        if rounds > max_rounds:
            raise BotModeError(f"Stuck trying to reach {dest} (too many interruptions).")
        try:
            yield from navigate_to(dest_map, coordinates, avoid_encounters=avoid_encounters)
            return
        except BotModeError:
            yield from _ride_out_scripted_scene("B")


def travel_to_petalburg() -> Generator:
    """Journey from Birch's lab to Petalburg City: Littleroot -> Route 101 ->
    Oldale -> Route 102 -> Petalburg. Mom's Running-Shoes gift fires in
    Littleroot on the way and is ridden out automatically. Ends in Petalburg."""
    context.message = "Story: setting off for Petalburg City..."
    yield from navigate_to_anywhere(MAP_LITTLEROOT_TOWN, (6, 9))  # exit the lab into town
    yield from _navigate_leg(MapRSE.ROUTE101, (9, 9))
    yield from _navigate_leg(MapRSE.OLDALE_TOWN, (4, 9))
    yield from _navigate_leg(MapRSE.ROUTE102, (14, 8))
    yield from _navigate_leg(MapRSE.PETALBURG_CITY, (20, 18))
    context.message = "Story: arrived in Petalburg City."
