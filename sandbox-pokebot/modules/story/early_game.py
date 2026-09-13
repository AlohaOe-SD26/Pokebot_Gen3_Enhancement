"""Story-mode early game — Chapter 0 tail + Chapter 1 (the post-intro stretch).

Picks up where `intro.run_intro()` leaves off (controllable inside the moving
truck) and works toward the starter + first battle, one testable step at a time.

Like the intro, this is driven by observed game state (maps, coordinates,
script names, control-lock) rather than event flags, because this early stretch
is almost entirely scripted. Verified against a save state parked in the truck.
"""

from __future__ import annotations

import os
import random
from typing import Generator

from modules.context import context
from modules.keyboard import get_naming_screen_data, type_in_naming_screen
from modules.map import get_map_data_for_current_position
from modules.map_data import MapRSE, PokemonCenter
from modules.map_path import Direction
from modules.memory import GameState, get_game_state
from modules.modes import BotModeError


class UnreachableDestinationError(BotModeError):
    """A destination TILE could not be reached from where we are standing.

    A SUBCLASS of BotModeError on purpose: every existing `except BotModeError`
    (StoryMode's derail recovery above all) keeps handling it exactly as before. It
    exists so a caller that made an OPTIONAL choice — "relocate to a better training
    ground" — can tell "that place is not reachable from here" apart from "training
    itself went wrong", and drop that option instead of retrying it forever.

    ‼ Added 2026-07-25 (#24-regionreach) after a live batch killed 2 of 5 runs on it.
    `_training_area_allowed`'s own docstring argued that a wrong YES from `region_reach`
    "costs ONE wasted walk, which navigation then fails RECOVERABLY and loudly" — the
    batch proved that wrong. The picker is DETERMINISTIC, so every derail re-ran `_play`,
    re-picked the same unreachable Route 111 tile, and failed identically until the derail
    budget dropped the run to Manual. A wrong YES cost the RUN, not a walk. Recognising
    this failure by TYPE is what lets the caller make the docstring's claim true.
    """
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
    ensure_facing_direction,
    navigate_to,
    wait_for_player_avatar_to_be_controllable,
    wait_for_player_avatar_to_be_standing_still,
)
from modules.player import get_player_avatar, player_avatar_is_controllable
from modules.pokemon_party import get_party
from modules.tasks import (
    get_global_script_context,
    get_tasks,
    get_immediate_script_context,
    is_waiting_for_input,
    task_is_active,
)

MAP_INSIDE_OF_TRUCK = "INSIDE OF TRUCK"
# Map group/number constants (map_name reads stale across warps; use these).
MAP_PLAYERS_HOUSE_1F = (1, 0)
MAP_PLAYERS_HOUSE_2F = (1, 1)
MAP_LITTLEROOT_TOWN = (0, 9)
HOUSE_1F_STAIRS = (8, 2)          # 1F warp up to 2F
CLOCK_FACE_TILE = (5, 2)          # stand here facing North to use the wall clock at (5,1)
HOUSE_2F_STAIRS_DOWN = (7, 1)     # 2F warp down to 1F
HOUSE_1F_DOOR_APPROACH = (8, 7)   # tile above the front door; step South to exit


# --- Whiteout / abort signalling (defeat-recovery, user directive 2026-07-21) ----
# StoryMode.on_whiteout() flips this so the currently-running segment bails out of
# its wait loops PROMPTLY (instead of mashing a button until a slow guard fires),
# letting StoryMode.run() catch the abort and restart the segmented resume from the
# respawn point. run() clears it at the start of each attempt.
_STORY_ABORT = False


def set_story_abort(value: bool) -> None:
    global _STORY_ABORT
    _STORY_ABORT = bool(value)


def story_should_abort() -> bool:
    return _STORY_ABORT


# SWAP-TRAINING flag (user directive 2026-07-21): while set, StoryMode.on_battle_started
# hands wild battles to SwapTrainBattleStrategy (switch the under-levelled lead out to a
# stronger team-mate turn 1 so it shares XP without fainting). Set only around
# `train_team` so it never affects the rival/gym fights.
_SWAP_TRAIN = False


def set_swap_train(value: bool) -> None:
    global _SWAP_TRAIN
    _SWAP_TRAIN = bool(value)


def swap_train_active() -> bool:
    return _SWAP_TRAIN


class StoryAbort(BotModeError):
    """The whiteout unwind signal — a `BotModeError` so nothing that already catches one breaks.

    ‼‼ IT NEEDS ITS OWN TYPE BECAUSE CHAPTER RETRY LOOPS WERE SWALLOWING IT (KI-67). Chapters like
    `do_space_center_chapter` and `do_mossdeep_gym_chapter` wrap their attempts in
    `except BotModeError` — deliberately, because losing a gym fight IS an expected outcome and the
    recovery is "re-enter and re-solve". But the abort latch is only ever cleared by
    `StoryMode.run`, so a chapter that caught the abort and retried IN PLACE ran straight into the
    next `_check_abort()` and died instantly. One whiteout therefore burned all three attempts in a
    handful of frames and the chapter reported three failures, two of them fabricated.

    ‼ RE-RAISING IS NOT "GIVING UP ON THE RETRY" — it hands the retry to the only layer that can
    perform it. `StoryMode.run` catches this, clears the latch, waits for the respawn, steps out of
    the Pokémon Center and re-runs `_play()`, which re-enters the chapter from wherever the player
    actually is (every chapter is resume-safe). That recovery is BOUNDED at 40 in a row.

    Subclassing `BotModeError` is the whole point: every existing `except BotModeError` in the tree
    keeps catching this exactly as before, so the only behaviour that changes is at the call sites
    that explicitly opt to re-raise it."""


def _check_abort() -> None:
    """Raise inside a segment's wait loop to unwind it for whiteout recovery."""
    if _STORY_ABORT:
        raise StoryAbort("Story: aborting the current step to recover from a whiteout.")


def reraise_if_aborting(error: BaseException) -> None:
    """First statement of any `except` that could swallow a whiteout unwind. KEYED ON THE LATCH.

    ‼‼ WHY THE EXCEPTION TYPE IS NOT ENOUGH, and this predicate is. `StoryAbort` identifies the
    abort only while the ORIGINAL object is in flight. Our retry loops routinely catch an error and
    raise a BRAND-NEW one describing what they were trying to do — and that new error is an ordinary
    `BotModeError`, with the abort's identity gone. Measured in our own code
    (`space_center.py:191-214`): the six cutscene tiles are tried in a loop that catches per tile,
    and if none succeeds the function raises *"the Team Magma NPCs are therefore still standing on
    the only land bridge"*. After a whiteout that sentence is **a fabricated diagnosis** — the NPCs
    are irrelevant, the player is standing outside a Pokémon Center. The same shape sits behind
    "cannot reach the stair grunt" and "cannot reach Steven".

    ‼ A LAUNDERED ABORT IS WORSE THAN A SWALLOWED ONE. A swallowed abort costs a retry budget; a
    laundered one hands the next agent a confident, plausible, WRONG cause — and this project has
    already lost multi-day investigations to exactly that (the reachability failures behind
    KI-59/KI-60). Reading the latch survives every conversion, because the latch is the fact.

    ‼ RE-RAISES THE ERROR IT WAS GIVEN, not a synthesized one. If a genuine navigation failure
    happens on the same frame as a whiteout, the message will name the navigation failure — which is
    fine: `StoryMode.run` branches on `_whiteout_pending`, not on the text, and recovers either way.
    Do not "fix" that later by substituting a synthetic error; the original is more informative."""
    if _STORY_ABORT:
        raise error


#: Overworld frames of NO party-EXP gain before `_story_spin` bails so the caller
#: re-navigates to the grass and retries (a training spin that can't trigger encounters
#: must self-heal, not walk in place forever). ~40s at 60fps — well beyond the gap between
#: normal wild encounters, so it only fires on a genuine stall.
_STORY_SPIN_NO_PROGRESS_FRAMES = 2400


def _story_spin(stop_condition) -> Generator:
    """`spin()` that ALSO stops the instant a whiteout abort is flagged, then raises so
    the current segment unwinds into StoryMode.run()'s recovery.

    EVERY story grind/training spin MUST go through this. A raw `spin()` whose
    stop-condition omits the abort check keeps spinning even after a mid-training
    whiteout — the game respawns you (fully healed) at the Poké Center, but the spin's
    own conditions (level still < target, HP now full) never fire, so the bot just
    spins in place at the respawn point forever (user-seen at the Oldale PC while
    training before the rival). The trailing `_check_abort()` turns the flag into the
    BotModeError run() expects, so the whiteout recovery re-orients and resumes.

    NO-PROGRESS WATCHDOG (user directive 2026-07-21 "never hang"): the raw `spin()` walks in
    grass to trigger wild battles, but if it ends up somewhere it can't trigger encounters
    (walked out of grass, a trainer's line-of-sight blocks the tile, a bad respawn spot) it
    walks in place FOREVER — the level never reaches the target and the stop-condition never
    fires (harness-seen at Route 116, training stuck with no EXP for 20k+ frames). So we also
    stop the spin when the party gains NO EXP for `no_progress_frames` consecutive OVERWORLD
    frames; the caller (e.g. `train_team`'s loop) then RE-NAVIGATES to the grass and retries,
    which un-sticks it. We only count overworld frames so a long single battle never
    false-triggers (EXP jumps when it's won, resetting the counter)."""
    from modules.memory import get_game_state, GameState

    _wd = {"last_xp": None, "stuck": 0}

    def _total_party_xp() -> int:
        try:
            return sum(p.total_exp for p in get_party() if p is not None and not p.is_egg)
        except Exception:
            return -1

    def _watchdog_stop() -> bool:
        if story_should_abort() or stop_condition():
            return True
        # Only judge "no progress" while free in the overworld — not during a battle/menu.
        try:
            if get_game_state() is not GameState.OVERWORLD:
                return False
        except Exception:
            return False
        xp = _total_party_xp()
        if xp != _wd["last_xp"]:
            _wd["last_xp"] = xp
            _wd["stuck"] = 0
        else:
            _wd["stuck"] += 1
            if _wd["stuck"] >= _STORY_SPIN_NO_PROGRESS_FRAMES:
                return True  # stalled — bail so the caller re-navigates to grass and retries
        return False

    yield from spin(stop_condition=_watchdog_stop)
    _check_abort()
    # PHANTOM-SCRIPT CLEAR (batch run05 / evostall root cause, 2026-07-22): an evolution
    # can leave a script context ACTIVE after its battle ends, and an active script
    # SUPPRESSES wild encounter generation — so the spin turns forever with zero
    # encounters, the no-progress bail fires, the caller re-navigates, and the cycle
    # repeats invisibly (deterministic fresh-run repro hung at f210622 on exactly this).
    # When the spin bails with a script still engaged, B-ride it out (bounded) so the
    # next spin round actually gets encounters again.
    if _wd["stuck"] >= _STORY_SPIN_NO_PROGRESS_FRAMES and get_global_script_context().is_active:
        context.message = "Story: clearing a leftover scene that was blocking encounters..."
        yield from _ride_out_scripted_scene("B")
        yield from wait_until_truly_controllable()


def _navigate_riding_out(dest_map, dest_tile, *, avoid_encounters: bool = True, tries: int = 10) -> Generator:
    """`navigate_to_anywhere` that rides out any scripted scene (a trainer sight-line,
    a cutscene) that aborts the path, then retries — instead of hard-failing to Manual.
    Used by training/catching where the grass route can cross a trainer's line."""
    last_error = None
    last_where = None
    #: Obstacle tiles already cleared on THIS trip. ‼ Rock-Smash rocks RESPAWN on map
    #: reload, so without this a respawn turns the retry loop into an endless
    #: smash-and-retry — and a bounded loop re-entered by its dispatcher is still infinite
    #: (KI-34 burned 23.9M frames exactly that way).
    cleared_obstacles: set = set()
    #: The map an empty obstacle search was last performed on, or None to search now.
    #:
    #: ‼ THIS USED TO BE A PLAIN `obstacle_search_exhausted` LATCH, AND THE LATCH WAS WRONG.
    #: Its stated premise was "riding out a scene cannot create new rocks, so one empty
    #: answer is final for this trip". That is true for scenes and false for JOURNEYS: a
    #: long trip crosses many maps, and what is reachable — and therefore what counts as a
    #: clearable obstacle — changes completely with every one. Measured 2026-07-31: a
    #: Petalburg -> Fiery Path run searched once in PETALBURG (correctly empty, the rock is
    #: seven maps away), latched, and then walked all the way to **ROUTE111 (31,114)** —
    #: standing on the very map whose rock at (18,101) seals the corridor — with obstacle
    #: clearing permanently switched off. It stopped there.
    #:
    #: The reason the latch exists is still real: the search is SYNCHRONOUS, running several
    #: `calculate_path` calls without yielding, so the emulator is frozen throughout and
    #: re-running it on every retry costs seconds per failed navigation. Keying it to the
    #: MAP keeps that saving (no repeat searches while stuck in one place) without the bug
    #: (a new map always gets a fresh look).
    obstacle_search_done_on = None
    for _ in range(tries):
        _check_abort()
        try:
            yield from navigate_to_anywhere(
                dest_map, dest_tile, avoid_encounters=avoid_encounters, avoid_scripted_events=False
            )
            return
        except BotModeError as e:
            last_error = e
            # ‼ #24-smashroute / KI-41 — TRY THIS **BEFORE** THE FAIL-FAST BELOW. A
            # FIELD-MOVE OBSTACLE seals some corridors, and neither retrying nor riding out
            # a scene can ever help with one: measured 2026-07-31, a Rock Smash rock at
            # ROUTE111 (18,101) makes ROUTE112 score **0 of 76** reachable tiles from
            # Mauville, which is why FIERY_PATH — and so the Machop the `#24-counters`
            # ladder names for Norman — was out of reach. The fail-fast guard below is
            # right that "the field is idle and we have not moved, so retrying cannot
            # change the result" — but SMASHING THE ROCK CHANGES THE WORLD, which is
            # exactly the premise the guard tests for. So this must run first, and only
            # once per obstacle.
            #
            # `find_obstacle_on_route` returns None unless the party has the move AND the
            # badge AND the approach tile is reachable right now, so a "no" costs one cheap
            # search on a path that was already failing.
            obstacle = None
            here_map = _map_group_number()
            if obstacle_search_done_on != here_map:
                try:
                    from modules.story.obstacle_clearing import clear_obstacle, find_obstacle_on_route

                    obstacle = find_obstacle_on_route(
                        here_map,
                        dest_map.value if hasattr(dest_map, "value") else dest_map,
                        prefer_toward=dest_tile,
                    )
                except Exception:  # noqa: BLE001 - a search must never end a trip
                    obstacle = None
                if obstacle is None or obstacle.tile in cleared_obstacles:
                    # Nothing to do HERE. Remember the map, not a boolean — moving to a new
                    # map must get a fresh search (see the note above the declaration).
                    obstacle_search_done_on = here_map
            if obstacle is not None and obstacle.tile not in cleared_obstacles:
                cleared_obstacles.add(obstacle.tile)
                context.message = f"Story: clearing the way — {obstacle.describe()}"
                yield from clear_obstacle(obstacle)
                # The world changed, so the fail-fast's "nothing can differ" premise no
                # longer holds — forget where we failed from and let the next try plan
                # against the newly-open corridor.
                last_where = None
                continue
            # ‼ FAIL FAST ON A HOPELESS RETRY (2026-07-24, user log 12:39 + my treecko
            # run — BOTH died here). This retry loop only helps when a SCENE aborted the
            # path, because riding the scene out changes the world. If the field is idle
            # (no active script, player controllable) AND we are standing on the exact
            # tile we failed from last time, then nothing about the attempt can differ:
            # the planner will fail identically, forever. Retrying anyway costs
            # `_ride_out_scripted_scene`'s 240-frame engage wait PER TRY, and callers
            # wrap this in their own retry loop — get_devon_scope's is 10 rounds × 6
            # tries ≈ 14,400 frames of pure churn, which is what let the 18k global
            # watchdog kill two otherwise-healthy runs instead of surfacing the real
            # error. Bail immediately with the planner's own message so the caller (and
            # the log) sees WHY, not "after N tries".
            where = None
            try:
                if not get_global_script_context().is_active and player_avatar_is_controllable():
                    where = (_map_group_number(), tuple(get_player_avatar().local_coordinates))
            except Exception:
                where = None
            if where is not None and where == last_where:
                raise UnreachableDestinationError(
                    f"Could not reach {dest_tile} on {dest_map}: the field is idle and we are "
                    f"still at {where[1]}, so retrying cannot change the result "
                    f"({last_error})."
                )
            last_where = where
            yield from _ride_out_scripted_scene("B")
    # Surface the REAL last error: runs 11-13 each burned all retries on instant
    # PLAN failures (an unreachable tile) while this message blamed "scene
    # interruptions" — two full validation runs were misdiagnosed off it.
    raise UnreachableDestinationError(
        f"Could not reach {dest_tile} on {dest_map} after {tries} tries (last error: {last_error})."
    )


# Exit warp of every Emerald Poké Center 1F (same interior layout everywhere).
POKEMON_CENTER_1F_EXIT = (7, 8)


def exit_building_after_whiteout() -> Generator:
    """Step out to the overworld if we are standing inside a Poké Center.

    ⛔⛔ THIS DOCSTRING USED TO SAY "After a whiteout the player respawns INSIDE a Poké Center
    (its healing spot)". **THAT IS FALSE IN EMERALD, decomp-verified 2026-09-08.**
    `src/data/heal_locations.json` puts every Center's heal location on the **OUTDOOR town map**
    at the door tile (PETALBURG_CITY 20,17; OLDALE_TOWN 6,17; MOSSDEEP_CITY 28,17 — one tile below
    the PC door at 28,16), and because `warpId` is `WARP_ID_NONE` the raw coords are used verbatim
    (`src/overworld.c:611`). The only indoor heal locations are the two Littleroot bedrooms.
    ⇒ **after a whiteout this function's own guard can never pass**, so on the path it was written
    for it is INERT.

    ⭐ IT IS KEPT, NOT DELETED, AND THE DISTINCTION MATTERS: the GUARD is correct even though the
    PREMISE was not. If the bot is ever genuinely inside a Center (a resume from a save made there,
    a mid-heal derail), stepping out is still the right move and still works. Removing it would be a
    BEHAVIOUR change justified by an argument rather than a measurement.
    ‼ What is now known to be wrong is the STORY the comment told about why it runs — and a reader
    who believed it would conclude the post-whiteout interior case is handled when nothing handles
    it, because nothing needs to.

    ⇒ If you are reasoning about where a whiteout lands, READ IT: `get_last_heal_location()`
    (`modules/save_data.py:14`, SaveBlock1 +0x1C), already wrapped as `respawn_reading()` /
    `respawn_is_armed()` (`victory_road.py:666`, `:680`). Never infer it from a map proxy."""
    from modules.map import get_map_data_for_current_position

    try:
        from modules.map_data import get_map_enum

        enum_name = get_map_enum(get_map_data_for_current_position()).name
    except Exception:
        enum_name = ""
    cur = _map_group_number()
    if cur is None or "POKEMON_CENTER" not in enum_name:
        return
    context.message = "Story: stepping out of the Poké Center after the whiteout…"
    # Walk to the tile just ABOVE an exit warp, then step DOWN onto it so the warp
    # fires from a fresh step (navigate_to alone can stop ON the warp without it
    # firing — ML-9). Try both exit columns (7 and 6).
    for above in ((7, 7), (6, 7)):
        _check_abort()
        if _map_group_number() != cur:
            break
        try:
            yield from navigate_to(cur, above)
            yield from _walk_through_warp("Down", cur, timeout_frames=120)
        except Exception:
            pass


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


def _pass_through_door(door_tile: tuple[int, int], from_map: tuple[int, int]) -> Generator:
    """Robustly warp through a door/warp tile by making it a NAVIGATION target.

    A warp fires on a genuine *step onto* the tile. `navigate_to(map, door_tile)`
    triggers it (this is exactly how `heal_in_pokemon_center` enters the Poké
    Center door) — whereas stopping SHORT of the door and hand-stepping onto it
    was flaky (the Petalburg-Woods stall, ML-9: map reads flicker during the warp
    fade, and single-frame presses don't complete a tile step). If a prior
    navigate left us standing ON the door without warping, step one tile south
    first so the next navigate makes a fresh step onto it."""
    x, y = door_tile
    # If we're already sitting on the door (a previous navigate walked over it
    # without warping), step off it (south) so navigate_to re-enters it cleanly.
    if _map_group_number() == from_map and tuple(get_player_avatar().local_coordinates) == (x, y):
        yield from navigate_to(from_map, (x, y + 1))
    # Walk onto the door tile as the destination — navigate_to fires the warp.
    if _map_group_number() == from_map:
        yield from navigate_to(from_map, door_tile)


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


def _ride_out_all_scenes(*, quiet_frames: int = 600, max_frames: int = 12000) -> Generator:
    """B-ride EVERY scene part until the field has been script-free for `quiet_frames`
    STRAIGHT. Multi-part aftermaths (Wally defeat → uncle → exit walk → Scott approach →
    PokéNav registration) pause BETWEEN parts, so a single cutscene-ride returns during
    a pause and the next part then interrupts whatever the story does next — run 11
    burned all of the training navigation's scene-interruption retries on exactly this
    and bailed to Manual just as the chain finished. Bounded: after `max_frames` we
    proceed anyway and let the callers' own riding cope."""
    total = 0
    quiet = 0
    phantom = 0
    while quiet < quiet_frames:
        if total > max_frames:
            break
        if get_global_script_context().is_active:
            quiet = 0
            # PHANTOM-SCRIPT ESCAPE (ported from _wait_until_cutscene_over, KI-15
            # family): a battle spawned/interrupted mid-scene can leave the field
            # script reading active FOREVER while the game is fully playable — a
            # parked trainer/wild post-battle script (Route 120 trainer, run 10:
            # gsc active + controllable + no text + no menu, 20k frames). A real
            # scene locks the avatar, prints text, or ends; 10s of "playable but
            # script-active" means parked, not running — treat the scene as over.
            if (
                player_avatar_is_controllable()
                and not is_waiting_for_input()
                and not _menu_task_active()
            ):
                phantom += 1
                if phantom >= 600:
                    return
            else:
                phantom = 0
                context.emulator.press_button("B")
        else:
            quiet += 1
            phantom = 0
        total += 1
        yield


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


# Menu tasks that hold the overworld non-controllable WITHOUT any script running.
# game_state stays OVERWORLD while these are up (the start menu is an overworld
# state!), so "state == OVERWORLD" alone never proves the menus are closed (KI-14).
_MENU_TASK_MARKERS = ("Task_ShowStartMenu", "ListMenuDummyTask", "Task_HandleChooseMonInput")


def _menu_task_active() -> bool:
    try:
        return any(
            any(marker in task.symbol for marker in _MENU_TASK_MARKERS) for task in get_tasks()
        )
    except Exception:
        return False


def normalize_to_overworld(*, timeout_frames: int = 3600) -> Generator:
    """RESUME-FROM-ANYWHERE failsafe (user directive 2026-07-23): bring the game to a
    STABLE, controllable overworld by COMPLETING whatever is currently on screen —
    before any story segment tries to navigate. A Story mode can be entered in any
    state: a milestone save loaded mid-menu (the rocksmash_taught checkpoint), an
    active battle, an open dialogue/Yes-No, a cutscene. Without this, the segment
    logic would drive a navigator under an open menu / into a dialogue and wedge.

    Strategy — press B on a cadence until settled:
      * BATTLE → a listener owns it; wait it out (press nothing).
      * OVERWORLD + controllable + no script + no menu → done (require it STABLE).
      * anything else (menu, message, Yes-No, cutscene, transition) → B. B advances
        and dismisses dialogue, closes menus, and answers Yes-No as NO/CANCEL — all of
        which move TOWARD the overworld and can never start a new conversation or take
        a destructive action (A could). We deliberately do NOT try to make progress
        here; segments do that once we hand them a clean overworld.
    Bounded; a no-op when already controllable. Safe to call unconditionally."""
    from modules.memory import GameState, game_has_started, get_game_state
    from modules.player import player_avatar_is_controllable

    if get_game_state() is GameState.TITLE_SCREEN or not game_has_started():
        return  # the intro path owns the title screen / pre-game

    stable = 0
    for _f in range(timeout_frames):
        _check_abort()
        state = get_game_state()
        if state is GameState.BATTLE:
            stable = 0
            yield  # the battle listener drives; just let it finish
            continue
        try:
            script_active = get_global_script_context().is_active or get_immediate_script_context().is_active
        except Exception:
            script_active = False
        settled = (
            state is GameState.OVERWORLD
            and player_avatar_is_controllable()
            and not script_active
            and not _menu_task_active()
        )
        if settled:
            stable += 1
            if stable >= 15:  # a quarter-second of genuine control — transitions settled
                return
            yield
            continue
        stable = 0
        context.emulator.press_button("B")
        yield
    # Timed out — hand back anyway; the caller's own guards/derail recovery cope.
    context.emulator.reset_held_buttons()


def _int_env(name: str, default: int = 0) -> int:
    """Read a small non-negative int from the environment, defaulting when absent or malformed.

    ‼ `str.isdigit()`, NOT `try: int(...) except ValueError: pass` — a bare swallow here is
    exactly the shape `repro_no_silent_except` ratchets, and it caught this author writing one
    on 2026-09-12. A malformed value is a typo in an experiment flag, so the safe reading is
    "behave as if unset" (production default), never "crash a 12-hour batch"."""
    raw = os.environ.get(name, "")
    return int(raw) if raw.isdigit() else default


def _yes_no_menu_is_open() -> bool:
    """Is a Gen-3 yes/no (or multichoice) CHOICE BOX genuinely on screen right now?

    ‼ WHY THIS IS A SEPARATE PREDICATE FROM `_dialogue_button` (2026-09-13). That helper answers
    *"which button is safe to advance a SCENE with"* and downgrades A→B. This one answers
    *"is a CHOICE pending"* so a caller can refuse to let B ANSWER it — B advances plain dialogue
    harmlessly, but at a choice box `Task_HandleYesNoInput` reads `MENU_B_PRESSED` and falls
    through to `gSpecialVar_Result = 0`, i.e. **NO**. Same task symbols, opposite question.

    ⛔ Returns False on any read failure, and that direction is deliberate: False means "press
    what you were going to press", i.e. UNCHANGED legacy behaviour. A True on a bad read would
    silently convert every B in a mash loop into an A, which near an NPC RE-OPENS conversations
    (the Slateport museum greeter loop, 2026-07-23). Fail toward the old behaviour, never toward
    a new one."""
    try:
        return any("YesNo" in t.symbol or "Multichoice" in t.symbol for t in get_tasks())
    except Exception:  # noqa: BLE001 — justified above: a failed read must not change behaviour
        return False


def _dialogue_button(button: str) -> str:
    """Resolve the button to actually press this frame when riding out a scene.

    ‼ Callers ask for "A" because a scene MIGHT contain a Yes/No they must accept (the
    museum's 50 entry fee, Briney's sail confirmation). But A next to an NPC is not
    just "advance text" — it STARTS a conversation. So A-mashing a plain message while
    standing beside the speaker dismisses it and immediately re-opens it, forever: the
    Slateport museum greeter loop the user hit on real hardware (2026-07-23), where the
    attendant had already been paid and was cheerfully repeating "Please enjoy
    yourself." until the ride-out timed out and derailed the story.

    B advances and dismisses dialogue exactly like A but can never initiate one. So we
    press A ONLY while a Yes/No or multichoice menu is genuinely on screen, and B for
    everything else. Requests for B (the common case) pass straight through."""
    if button != "A":
        return button
    # ‼ ONE predicate, two questions (2026-09-13). This used to inline its own copy of the
    # task scan; `_yes_no_menu_is_open` now owns it so the two callers cannot DRIFT apart —
    # a choice box that this function stopped recognising would silently start B-mashing
    # "NO" into it, which is precisely the `#24-wallydecline` failure. Behaviour is
    # unchanged: same symbols, same fail-to-"B" direction.
    return "A" if _yes_no_menu_is_open() else "B"


def _wait_until_cutscene_over(button: str = "B", *, stable_frames: int = 15,
                              timeout_frames: int = 8000) -> Generator:
    """Mash ``button`` until the player is controllable AND no script is running,
    held for ``stable_frames`` consecutive frames.

    A single-frame check is not enough during these arrival cutscenes: there are
    brief windows where the script is 'active' but the avatar isn't locked yet
    (start of a script) or the avatar is locked while no script runs (a warp in
    between scripts). Requiring both conditions to hold for a short stretch means
    we only stop once control has genuinely returned.

    ‼ We press ONLY when there is genuinely something to advance (a script running,
    or a text printer waiting on A/B). Mashing through the non-controllable TAIL of a
    dialogue re-opens it when we happen to be facing an NPC: the script ends, control
    has not settled, we press A, and the greeter starts talking again — forever, until
    this helper times out and throws. That is the Slateport museum "stuck looping at
    the greeter" the user reported on real hardware (2026-07-23). Waiting out the tail
    in silence costs nothing and cannot re-trigger anyone."""
    stable = 0
    frames = 0
    phantom = 0
    # --- KI-15 TRACE (env-gated, logging-only; REMOVE after repro) ---
    import os as _os15
    _ki15w = _os15.environ.get("KI15_TRACE")
    def _w15(msg):
        if _ki15w:
            try:
                with open(_ki15w, "a", encoding="utf-8") as _f:
                    _f.write(msg + "\n")
            except Exception:
                pass
    # -----------------------------------------------------------------
    while stable < stable_frames:
        script_running = get_global_script_context().is_active or get_immediate_script_context().is_active
        # KI-15 NOTE: a wild battle fled DURING a scene ride can leave stale BATTLE
        # text ("Got away safely!") waiting for input with NO script running — and
        # that state reads IDENTICALLY to a field dialogue's parked WaitForAorBPress
        # tail (museum greeter) on every reader AND ignores B just the same (probed
        # on captured states; two rider-side discriminators failed and were
        # reverted — see 08-MISTAKES 2026-07-24). The rider therefore treats both
        # as FREE and returns (correct for the tail; the old, museum-green
        # behavior). The battle-text wedge — whose ONE unique property is that it
        # BLOCKS ALL MOVEMENT — is cleared by StoryMode.run's position-frozen
        # persistence nudge instead (story_mode.py), the only seam that can see
        # "nothing has moved for seconds".
        free = player_avatar_is_controllable() and not script_running
        # --- KI-15 TRACE: sample the reader profile periodically ---
        if _ki15w and (frames % 200 == 0 or frames > timeout_frames - 5):
            try:
                from modules.battle_state import get_current_battle_script_instruction as _gcbsi
                _instr = _gcbsi()
            except Exception as _e:
                _instr = f"<err {_e}>"
            try:
                _gc = get_global_script_context()
                _sptr = f"mode={_gc.mode} bc={hex(_gc.bytecode_pointer)} nat={hex(_gc.native_pointer)} depth={_gc.stack_depth}"
            except Exception as _e:
                _sptr = f"<sptr err {_e}>"
            _w15(f"[cutscene] f={frames} controllable={player_avatar_is_controllable()} "
                 f"script_running={script_running} waiting_input={is_waiting_for_input()} "
                 f"menu={_menu_task_active()} phantom={phantom} instr={_instr} {_sptr}")
        # -----------------------------------------------------------
        stable = stable + 1 if free else 0
        # PHANTOM-SCRIPT ESCAPE (user's 2026-07-23 Route 111 hang): when a field
        # script is interrupted by a battle it spawned (Rock Smash's wild-encounter
        # roll), the script context can READ active forever while the game is in
        # fact fully playable — the avatar controllable, no text, no menu. A real
        # cutscene never idles like that: it either locks the avatar, prints text,
        # or ends. Ten straight seconds of "playable but script-active" means the
        # context is parked, not running — treat the scene as over instead of
        # timing out at 8000 frames and derailing in a loop.
        if (
            script_running
            and player_avatar_is_controllable()
            and not is_waiting_for_input()
            and not _menu_task_active()
        ):
            phantom += 1
            if phantom >= 600:
                context.message = "Story: parked script context detected — treating the scene as over."
                _w15(f"[cutscene] PHANTOM-ESCAPE fired at f={frames} (controllable=True parked script)")
                return
        else:
            phantom = 0
        if not free:
            if script_running or is_waiting_for_input():
                context.emulator.press_button(_dialogue_button(button))
            elif _menu_task_active():
                # KI-14: a stray menu (start menu / bag) freezes the avatar with NO
                # script and NO waiting text — the conditions above never press and
                # this helper would sit out its whole timeout. B closes menus and
                # cannot start a conversation, so it is always safe here.
                context.emulator.press_button("B")
        frames += 1
        if frames > timeout_frames:
            _w15(f"[cutscene] TIMEOUT-RAISE at f={frames} controllable={player_avatar_is_controllable()} "
                 f"script_active={get_global_script_context().is_active} phantom={phantom} "
                 f"waiting_input={is_waiting_for_input()} menu={_menu_task_active()} "
                 f"— KI-15 HANG STATE (would raise+retry-loop)")
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

#: The species actually chosen on THIS run — set by `help_birch_and_choose_starter()` at
#: the moment it resolves the config. Exists because a lane configured `starter: random`
#: is otherwise indistinguishable from a lane pinned to whatever it happened to roll:
#: ENDLESS LOOP x4's P4 lane is `random`, and when it rolls Treecko it looks exactly like
#: the pinned-Treecko P3 lane (user report 2026-07-26). The x4 tile reads this across the
#: process boundary so the label can say `random -> Treecko`.
LAST_CHOSEN_STARTER: str | None = None


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
    global LAST_CHOSEN_STARTER

    resolved = STARTER_BY_NAME.get(str(starter).strip().lower())
    if resolved is None:
        resolved = random.choice(list(STARTER_BY_NAME.values()))
    LAST_CHOSEN_STARTER = resolved
    # Say it in the log too: "which starter did THIS run actually play?" is the first
    # question asked of any batch, and `random` in story.yml does not answer it.
    try:
        from modules.console import console

        console.print(f"[bold cyan]STARTER: config={starter!r} -> playing {resolved}[/]")
    except Exception:
        pass

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


def _min_battler_hp_pct() -> float:
    """Lowest HP% across the (non-egg) team. During SWAP-training the mon actually
    taking hits is the strong team-mate we switch IN, not the slot-0 lead we're
    levelling — so heal off the whole team's lowest HP, else the fighter faints
    while the untouched lead sits at full HP and never triggers a heal."""
    try:
        pcts = []
        for p in get_party():
            if p is None or getattr(p, "is_egg", False):
                continue
            try:
                pcts.append(float(p.current_hp_percentage))
            except Exception:
                continue
        return min(pcts) if pcts else 100.0
    except Exception:
        return 100.0


def _lead_level() -> int:
    party = get_party()
    return party[0].level if party else 0


def _team_is_out_of_pp() -> bool:
    """True when NO (non-egg) battler still has a damaging move with PP left.

    ‼ THE HEAL TRIGGER CANNOT BE HP-ONLY (user's real-HW log, 2026-07-26). HP and PP do
    not deplete together: a starter that WINS without being hit keeps full HP while its
    only attacking move drains. When the last damaging PP goes, the stock
    `LevelUpLeadBattleStrategy.decide_turn` finds no usable move, takes the
    `lead_cannot_battle_action` branch (default **flee**) — and fleeing takes no damage,
    so HP stays pinned at 100% and the HP-gated heal can NEVER fire.
    Measured cost of that livelock in one run: **3,011 consecutive flees**, Treecko stuck
    at L6 21/21 HP on the Route 103 training tile, ~2.9 MILLION frames burned without a
    single level gained, until the run budget expired.
    A Poké Center heal restores PP as well as HP, so routing this into the SAME heal the
    HP path already uses fixes it — no new mechanism needed.
    Fails SAFE: any read error returns False (assume we still have PP) so a bad read can
    never cause an endless heal loop; the HP trigger is unaffected either way.
    """
    try:
        for p in get_party():
            if p is None or getattr(p, "is_egg", False):
                continue
            for learned in getattr(p, "moves", []) or []:
                if learned is None:
                    continue
                try:
                    if learned.move.base_power > 0 and learned.pp > 0:
                        return False
                except Exception:
                    continue
        return True
    except Exception:
        return False


def travel_to_route103() -> Generator:
    """Travel from Birch's lab up to Route 103 (where the rival is), fighting any
    wild encounters along the way (which starts training the starter). Uses the
    map-by-map chain because the one-shot global route loops on Route 101.

    STORY CONDITION: starts controllable in the lab (1,4) with the starter.
    END STATE: standing on a tall-grass tile on Route 103 (0,18)."""
    context.message = "Story: heading north to Route 103 (training on the way)..."
    yield from navigate_to_anywhere(MAP_LITTLEROOT_TOWN, (6, 9))  # out of the lab, into town
    # ⛔ `_navigate_leg`, NOT a bare `navigate_to` (2026-09-11). These three hops run while the SIX
    # running-shoes coord-events are armed (`VAR_LITTLEROOT_TOWN_STATE == 3`), and a bare
    # `navigate_to` is exposed on BOTH counts:
    #   · it keeps `avoid_scripted_events=True`, so the planner pays +10000/armed tile and laps the
    #     house — MEASURED 23 waypoints vs 13 on `pokedex_done.ss1`; and
    #   · it has NO ride-out, so the moment the scene DOES fire (it always does — the only north
    #     exit is armed too) `walking.py:499-505` raises "Switching to manual mode".
    # `_navigate_leg` fixes both: it passes the flag and catches/rides out the scene, which is what
    # this leg has needed since it was written.
    yield from _navigate_leg(MapRSE.ROUTE101, (9, 9), avoid_encounters=False)
    yield from _navigate_leg(MapRSE.OLDALE_TOWN, (9, 9), avoid_encounters=False)
    yield from _navigate_leg(MapRSE.ROUTE103, ROUTE103_GRASS_TILE, avoid_encounters=False)


def wait_until_truly_controllable(*, stable_frames: int = 30, timeout_frames: int = 1800) -> Generator:
    """Wait for a STABLE controllable overworld after a battle before navigating.

    player_avatar_is_controllable() FLICKERS true/false during the battle→overworld
    return transition, so a single true reading is unreliable — the very next
    navigate_to() can still throw "player avatar is currently not controllable". We
    require it true for `stable_frames` CONSECUTIVE frames (the transition is truly
    finished) before returning. We press NOTHING while waiting: the transition
    self-completes on its own, and probing showed that mashing inputs at it only
    prolongs the flicker. Bounded by `timeout_frames` so we can never hang here.

    Addresses the user-seen training freeze: the battle that REACHES the target
    level strands its return transition; for a non-terminal level-up the next spin
    rides it out, but at the target we stop spinning, so without waiting here the
    caller's next navigate chokes and the bot derails toward Manual."""
    stable = 0
    waited = 0
    while stable < stable_frames and waited < timeout_frames:
        if player_avatar_is_controllable():
            stable += 1
        else:
            stable = 0
        waited += 1
        yield


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
    # Heal EARLY (big margin): the swap-train finisher heals only BETWEEN battles, so too
    # small a margin lets an unlucky hit faint it mid-battle and strand the bot on the
    # "choose your next Pokémon" menu (user 2026-07-21: all battles must survive failure).
    heal_at = float(getattr(context.config.battle, "hp_threshold", 20)) + 22.0
    context.message = f"Story: training the starter to Lv {target_level}..."
    guard = 0
    while _lead_level() < target_level:
        _check_abort()  # bail immediately if a whiteout was flagged between rounds
        guard += 1
        if guard > 200:
            raise BotModeError("Training did not reach the target level (too many rounds).")
        # Get onto the Route 103 grass (navigate_to_anywhere handles the cross-map
        # trip back from the Poké Center; the built-in find_closest_pokemon_center
        # is unreliable here, so we hard-target Oldale's centre below).
        yield from navigate_to_anywhere(MapRSE.ROUTE103, ROUTE103_GRASS_TILE, avoid_encounters=False)
        # Whiteout-aware spin: a mid-training defeat unwinds this for recovery instead
        # of leaving the bot spinning at the respawn Poké Center (user-seen).
        yield from _story_spin(lambda: _lead_level() >= target_level or _lead_hp_pct() <= heal_at)
        # After spin() returns, the LAST battle's overworld-return transition may
        # still be settling (the controllable flag flickers); wait it out patiently
        # before the next navigate (heal trip or the caller's post-training move) so
        # it doesn't choke. This is the user-seen training freeze.
        yield from wait_until_truly_controllable()
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
        _check_abort()
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
        _check_abort()
        rounds += 1
        if rounds > max_rounds:
            raise BotModeError(f"Stuck trying to reach {dest} (too many interruptions).")
        try:
            # ⛔⛔ `avoid_scripted_events=False` IS LOAD-BEARING, NOT A TIDY-UP (2026-09-11).
            # `calculate_path` charges **+10000 per ARMED coord-event tile** (`map_path.py:1034-1037`)
            # against a base step cost of 1 (`:974`) — so ONE armed tile buys up to ten thousand
            # steps of detour. After the Pokédex, `VAR_LITTLEROOT_TOWN_STATE == 3` arms all SIX
            # running-shoes triggers — (8,9) (9,9) (10,9) (11,9) across the main street and
            # (10,2) (11,2) at the north exit — and the y=9 row IS the whole southern approach.
            # MEASURED with `probe_path_dump.py` on `pokedex_done.ss1`, Littleroot (6,9) -> (11,1):
            #     avoid_scripted_events=True  -> **23 waypoints** (the lap around the house)
            #     avoid_scripted_events=False -> **13 waypoints** (straight up the street)
            # ⭐ AND THE DETOUR BUYS NOTHING: the only north exit is the x=10,11 corridor, whose
            # tiles are ALSO armed, so the scene fires either way. It merely moved WHERE Mom
            # catches us, for ten extra steps.
            # ‼ THIS IS SAFE *HERE* AND NOT EVERYWHERE. Walking onto an armed trigger freezes the
            # avatar mid-navigation and `walking.py:499-505` raises "We unexpectedly triggered a
            # scripted event … Switching to manual mode" unless the caller expects it. THIS
            # function already catches that and rides the scene out (below) — which is exactly why
            # the flag belongs on THIS call and not on a bare `navigate_to` elsewhere.
            # ⇒ the docstring above already promised this behaviour ("retrying around any scripted
            # scene … running-shoes gift"); only the cost side was missing.
            yield from navigate_to(dest_map, coordinates, avoid_encounters=avoid_encounters,
                                   avoid_scripted_events=False)
            return
        except BotModeError:
            yield from _ride_out_scripted_scene("B")


def travel_to_petalburg() -> Generator:
    """Journey from Birch's lab to Petalburg City: Littleroot -> Route 101 ->
    Oldale -> Route 102 -> Petalburg. Mom's Running-Shoes gift fires in
    Littleroot on the way and is ridden out automatically. Ends in Petalburg."""
    context.message = "Story: setting off for Petalburg City..."
    # Exit the lab and get north to Oldale with per-leg navigate_to (the global
    # navigator LOOPS on Route 101). Mom's Running-Shoes gift fires in Littleroot
    # and is ridden out by _navigate_leg.
    yield from navigate_to_anywhere(MAP_LITTLEROOT_TOWN, (6, 9))
    yield from _navigate_leg(MapRSE.ROUTE101, (9, 9))
    yield from _navigate_leg(MapRSE.OLDALE_TOWN, (6, 9))
    # From Oldale (past the Route 101 loop) the global navigator reliably routes
    # Oldale -> Route 102 -> Petalburg.
    yield from navigate_to_anywhere(MapRSE.PETALBURG_CITY, (20, 18))
    context.message = "Story: arrived in Petalburg City."


# --- Chapter 2: Petalburg Gym (Dad/Norman) + Wally catching tutorial --------
PETALBURG_GYM_NORMAN_TRIGGER_APPROACH = (4, 110)  # enter the gym here; step Up to fire the Norman scene


def do_petalburg_gym_and_wally_tutorial() -> Generator:
    """Enter the Petalburg Gym to meet Dad (Norman), then ride out the Wally
    catching tutorial.

    INTENT: clear the mandatory Petalburg beat so the player can head north.
    STORY CONDITION: begins in Petalburg City with the Pokédex, gym not yet
    visited (`THANKED_FOR_PLAYING_WITH_WALLY` unset).
    HOW IT WORKS: enter the gym near the entrance and step Up until the Norman
    coord-trigger at (4,108) fires (it only fires when stepped onto from the
    entrance, not when navigation drops you there). From there the whole
    sequence is AUTO-SCRIPTED — Norman addresses you, `ExitGymWithWally` walks
    you out, `WallyTutorial` auto-walks you and Wally to Route 102 where Wally
    catches a Ralts, then back. We just ride it out (advancing with B) until
    control genuinely returns.
    GOAL/END STATE: `THANKED_FOR_PLAYING_WITH_WALLY` set, controllable."""
    context.message = "Story: heading into the Petalburg Gym to see Dad..."
    yield from navigate_to_anywhere(MapRSE.PETALBURG_CITY_GYM, PETALBURG_GYM_NORMAN_TRIGGER_APPROACH)

    # Step up toward the Norman coord-trigger tile (4,108) (you get blocked
    # there), then ride out the whole Dad + Wally tutorial by alternating A/B.
    # The Norman scene engages once we start pressing A/B at the trigger tile,
    # and the tutorial then AUTO-WALKS the player to Route 102 for the Ralts
    # catch and back. This scene has mid-scene pauses where control briefly
    # returns, so the generic "controllable + no script" check stops too early —
    # ride until the completion flag `THANKED_FOR_PLAYING_WITH_WALLY` is set.
    from modules.memory import get_event_flag

    # Step up toward the Norman coord-trigger tile (breaking if the scene fires
    # early), matching the observed trigger sequence.
    for _ in range(45):
        if get_global_script_context().is_active:
            break
        context.emulator.press_button("Up")
        yield

    # Ride out the whole Dad + Wally tutorial with B (advances the message boxes
    # without re-triggering Norman's repeatable dialogue the way A does), until
    # the completion flag `THANKED_FOR_PLAYING_WITH_WALLY` is set. The tutorial
    # auto-walks the player to Route 102 for the Ralts catch and back.
    # The tutorial auto-walks the player out of the gym, across Petalburg, to
    # Route 102 (for the Ralts catch), and back into the gym for Norman's closing
    # words. It is DONE once we are back in the gym and controllable AFTER having
    # visited Route 102. We advance dialogue with A/B while a script runs (and to
    # fire the initial Norman scene), but press NOTHING once genuinely free at
    # the end — otherwise A re-triggers Norman's repeatable dialogue and loops.
    context.message = "Story: Dad and the Wally catching tutorial (Route 102)..."
    gym = MapRSE.PETALBURG_CITY_GYM.value
    visited_route_102 = False
    stable = 0
    frames = 0
    while True:
        here = _map_group_number()
        if here == MapRSE.ROUTE102.value:
            visited_route_102 = True
        free = player_avatar_is_controllable() and not get_global_script_context().is_active
        if visited_route_102 and here == gym and free:
            stable += 1
            if stable >= 45:
                break
        else:
            stable = 0
        # Press A/B to advance dialogue / fire the initial scene; but once free
        # after the tutorial (back in the gym) press nothing.
        if not free or not visited_route_102:
            context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 70000:
            raise BotModeError("The Wally catching tutorial never completed.")
        yield
    context.message = "Story: finished the Wally tutorial in Petalburg."


# --- Chapter 3: Petalburg -> Route 104 -> Petalburg Woods -> Rustboro --------
# Petalburg's ONLY west-edge opening to Route 104 is row y=12/13 (the rest of the
# west edge is fenced). A safe approach tile on that row, just EAST of the Scott
# coord-trigger at (4,12):
PETALBURG_WEST_EXIT_ROW = (6, 12)
# On Route 104, the Petalburg Woods SOUTH door is at (10-11,38) ('Non-Animated
# Door'). Navigate must stop BELOW it — stopping ON the door tile suppresses the
# warp — so we target the walkable tile two south of it and step up by hand.
ROUTE104_WOODS_SOUTH_DOOR_APPROACH = (11, 40)


def travel_to_petalburg_woods() -> Generator:
    """Heal at Petalburg, cross WEST to Route 104, beat the route trainer, and
    enter Petalburg Woods (south door).

    INTENT: first stretch of the Petalburg -> Rustboro journey (Chapter 3).
    STORY CONDITION: begins controllable in Petalburg (post-Wally tutorial),
    possibly still inside the gym.
    HOW IT WORKS:
      * Exit into Petalburg City and HEAL at its Poké Center. The party is a
        SINGLE Pokémon here, which can neither flee NOR rotate out of the
        Route 104 trainer battle, so it must go in at full HP (see
        `LevelUpTravelBattleStrategy` / ML-8).
      * Cross Petalburg's only west opening (row y=12/13). Walking there fires a
        ONE-TIME cutscene `PetalburgCity_EventScript_Scott` at (4,12) (Scott, the
        Frontier scout). The global navigator ABORTS on that script, so we route
        to a safe approach tile and hand-walk west, advancing Scott's dialogue
        with B, off the edge onto Route 104 (south/beach half).
      * Head for the Woods south door (10-11,38). A Route 104 trainer's sight
        line catches us en route; `avoid_scripted_events=False` lets the battle
        happen and the no-flee travel strategy wins it.
      * Enter the door with DISCRETE up-steps (a held direction won't cleanly
        enter it, and navigate must stop below the door, not on it).
    GOAL/END STATE: standing inside Petalburg Woods (24,11)."""
    route104 = MapRSE.ROUTE104.value
    woods = MapRSE.PETALBURG_WOODS.value

    # Exit the gym into the city (a no-op if already outside), then heal to full.
    context.message = "Story: healing at Petalburg before heading west..."
    yield from navigate_to_anywhere(MapRSE.PETALBURG_CITY, (15, 12))
    yield from heal_in_pokemon_center(PokemonCenter.PetalburgCity)

    # Cross west onto Route 104, riding out the one-time Scott cutscene. The
    # navigator can't cross it (it aborts on the script), so hand-walk west and
    # advance Scott's dialogue with B whenever a script/dialogue is up.
    context.message = "Story: leaving Petalburg to the west (Route 104)..."
    yield from navigate_to_anywhere(MapRSE.PETALBURG_CITY, PETALBURG_WEST_EXIT_ROW)
    tap = False
    frames = 0
    while _map_group_number() != route104:
        if get_global_script_context().is_active or get_game_state() is not GameState.OVERWORLD:
            if tap:
                context.emulator.press_button("B")
            tap = not tap
        else:
            context.emulator.press_button("Left")
        frames += 1
        if frames > 4000:
            raise BotModeError("Could not cross west from Petalburg to Route 104 (Scott scene?).")
        yield
    # Settle fully onto Route 104's grid before pathing (we cross mid-warp).
    for _ in range(8):
        context.emulator.press_button("Left")
        yield
    yield from wait_for_player_avatar_to_be_standing_still()

    # Cross Route 104 to the Woods south door, fighting the route trainer on the
    # way (avoid_scripted_events=False lets the trainer approach -> battle, which
    # the no-flee travel strategy wins).
    context.message = "Story: crossing Route 104 to Petalburg Woods..."
    yield from navigate_to_anywhere(
        MapRSE.ROUTE104,
        ROUTE104_WOODS_SOUTH_DOOR_APPROACH,
        avoid_encounters=True,
        avoid_scripted_events=False,
    )
    yield from wait_for_player_avatar_to_be_standing_still()

    # Walk UP through the Woods south door (row 38). Robust to navigate stopping
    # ON the door tile without warping (see _pass_through_door_going_up / ML-9).
    yield from _pass_through_door((11, 38), route104)
    if _map_group_number() != woods:
        raise BotModeError("Reached the Petalburg Woods south door but did not enter.")
    context.message = "Story: entered Petalburg Woods."


def cross_petalburg_woods() -> Generator:
    """Cross Petalburg Woods (south -> north), past the mandatory Team-Aqua /
    Devon-researcher scene, and exit the north door onto Route 104 (north half).

    INTENT: second stretch of the Petalburg -> Rustboro journey (Chapter 3).
    STORY CONDITION: begins just inside the Woods south entrance (arrived from
    Route 104 south via `travel_to_petalburg_woods`), party healed, no-flee
    travel strategy active.
    HOW IT WORKS: the Woods is a small maze holding ~3 Bug-Catcher TRAINERS and a
    MANDATORY cutscene `PetalburgWoods_EventScript_DevonResearcherRight` — a Team
    Aqua grunt robbing a Devon researcher battles you (via
    `EventScript_DoNoIntroTrainerBattle`), flees, and the researcher gives a Great
    Ball. We navigate toward the north exit door (14-15,5): route trainers are
    fought inline (`avoid_scripted_events=False`), and any cutscene that ABORTS
    navigation (the Devon scene, a trainer's "register in PokeNav?" prompt) is
    ridden out with B — its grunt battle handled by the battle listener — then
    navigation retries. Walking onto the north warp (15,5) exits the Woods; if
    navigation stops just short, we step UP through it with discrete steps.
    GOAL/END STATE: standing on Route 104 (0,19), north half (toward Rustboro)."""
    context.message = "Story: crossing Petalburg Woods..."
    yield from wait_for_player_avatar_to_be_controllable()
    woods = MapRSE.PETALBURG_WOODS.value
    rounds = 0
    while _map_group_number() == woods:
        _check_abort()
        rounds += 1
        if rounds > 15:
            raise BotModeError("Stuck crossing Petalburg Woods (too many scene interruptions).")
        try:
            yield from navigate_to_anywhere(
                MapRSE.PETALBURG_WOODS,
                (15, 6),
                avoid_encounters=True,
                avoid_scripted_events=False,
            )
            break
        except BotModeError:
            # The Devon/Aqua cutscene (or a post-battle PokeNav-register prompt)
            # fired and aborted navigation — ride it out (its grunt battle is
            # handled by the battle listener), then retry the path.
            yield from _ride_out_scripted_scene("B")

    # Exit UP through the north warp (row 5). Robust to navigate stopping ON the
    # warp tile without triggering it (see _pass_through_door_going_up / ML-9).
    yield from wait_for_player_avatar_to_be_standing_still()
    yield from _pass_through_door((15, 5), woods)
    if _map_group_number() == woods:
        raise BotModeError("Reached the Petalburg Woods north door but did not exit.")
    # Settle onto Route 104 north.
    yield from wait_for_player_avatar_to_be_controllable()
    context.message = "Story: exited Petalburg Woods to Route 104 (north)."


# A reachable central tile in Rustboro City (from mapdump; the gym is at warp
# (27,19), the Poké Center at (16,38)):
RUSTBORO_ARRIVAL_TILE = (20, 42)


def travel_route104_north_to_rustboro() -> Generator:
    """Route 104 (north half) -> Rustboro City.

    INTENT: final travel leg of Chapter 3 (Petalburg -> Rustboro).
    STORY CONDITION: standing on Route 104 north (having exited Petalburg Woods
    via `cross_petalburg_woods`), no-flee travel strategy active.
    HOW IT WORKS: Route 104's north half connects DIRECTLY to Rustboro (no warp
    split), so the global navigator can route it in one shot. We head for a
    central Rustboro tile, fighting any Route 104 north trainers inline
    (`avoid_scripted_events=False`) and riding out any cutscene that aborts the
    path, until we're standing in Rustboro City.
    GOAL/END STATE: standing in Rustboro City (0,3)."""
    context.message = "Story: heading up Route 104 to Rustboro City..."
    rustboro = MapRSE.RUSTBORO_CITY.value
    rounds = 0
    while _map_group_number() != rustboro:
        _check_abort()
        rounds += 1
        if rounds > 15:
            raise BotModeError("Stuck reaching Rustboro from Route 104 north.")
        try:
            yield from navigate_to_anywhere(
                MapRSE.RUSTBORO_CITY,
                RUSTBORO_ARRIVAL_TILE,
                avoid_encounters=True,
                avoid_scripted_events=False,
            )
            break
        except BotModeError:
            yield from _ride_out_scripted_scene("B")
    yield from wait_for_player_avatar_to_be_controllable()
    context.message = "Story: arrived in Rustboro City."


# Roxanne (the Rustboro gym leader) stands at gym tile (5,2); the challenge tile
# right below her is (5,3), approached from (5,4):
RUSTBORO_GYM_ROXANNE_APPROACH = (5, 4)


def _yield_bounded(gen, max_frames: int) -> Generator:
    """Drive a sub-generator with a HARD frame cap; returns True if it finished, False if
    it timed out (the sub-generator is then closed). WHY: stock menu navigators
    (StartMenuNavigator.open_start_menu etc.) wait UNBOUNDED for their menu to appear —
    but a field script (a trainer's sight-line firing in the grass, a leftover
    evolution/battle scene) LOCKS input, so the menu can never open and the wait wedges
    FOREVER (real-HW: a 110k-frame stall mid-training next to Youngster Joey,
    2026-07-22; same family as the evostall batch hang). Every menu-driven sub-action
    the story calls must be bounded."""
    for _ in range(max_frames):
        try:
            next(gen)
        except StopIteration:
            return True
        yield
    try:
        gen.close()
    except Exception:
        pass
    return False


def _rotate_lead_safely(target_slot: int, *, attempts: int = 3) -> Generator:
    """`change_lead_party_pokemon` with INTERRUPT AWARENESS (user directive 2026-07-22:
    "ensure the interrupt logic works — know when a trainer interrupts anything").

    Never starts (or keeps driving) the Start-menu party rotation while a field script
    is active, and BOUNDS the menu drive so a script that fires mid-menu can't wedge it.
    On interruption: close any half-open menu, ride the scene out (the battle listener
    fights any resulting trainer battle), then retry. Bounded attempts; gives up
    gracefully — the rotation is an optimization, training/gyms still work without it."""
    from modules.modes.util.higher_level_actions import change_lead_party_pokemon

    for _ in range(attempts):
        _check_abort()
        # Don't even open the menu while a script is engaged / control is shaky.
        if get_global_script_context().is_active:
            yield from _ride_out_scripted_scene("B")
            yield from wait_until_truly_controllable()
        try:
            ok = yield from _yield_bounded(change_lead_party_pokemon(target_slot), 3000)
        except Exception:
            ok = False
        if ok:
            return
        # Timed out / errored — likely a script fired mid-menu (trainer approach).
        # Close any half-open menu, ride the scene out, retry.
        for _ in range(12):
            context.emulator.press_button("B")
            yield
        yield from _ride_out_scripted_scene("B")
        yield from wait_until_truly_controllable()
    context.message = "Story: lead rotation kept getting interrupted — continuing without it."


def _lead_strongest_battler() -> Generator:
    """Put the highest-level CAPABLE battler in slot 0 before a gym / major fight.
    Swap-training rotates a weak trainee into the lead, so without this the gym would
    send that weak mon out first (it faints, then the strong mon takes over — messy
    and risky). Leading with our best mon wins cleanly."""
    party = get_party()
    slots = _battler_slots()
    if not slots:
        return
    best = max(slots, key=lambda i: party[i].level)
    if best != 0:
        yield from _rotate_lead_safely(best)


def _lead_best_matchup(foe_type_names, *, min_incoming_only: bool = True,
                       hunted_pids=None) -> Generator:
    """Put the CAPABLE battler that best resists the foe's ace type(s) in slot 0 — used
    before a TYPE-COUNTERED trainer where "lead strongest" is a trap. (Rustboro rival:
    if we started Mudkip, the rival leads a grass Grovyle, and our Marshtomp — Water/Ground
    — is 4× weak to Grass, so leading it feeds a super-effective sweep.)

    Picks the battler minimizing the foe's WORST-CASE STAB multiplier against it, breaking
    ties by higher level; leaves slot 0 unchanged if it's already the best. `foe_type_names`
    is a list like ["Grass"]."""
    from modules.modes.util.higher_level_actions import change_lead_party_pokemon
    from modules.pokemon import get_type_by_name

    party = get_party()
    slots = _battler_slots()
    if not slots:
        return
    try:
        foe_types = [get_type_by_name(n) for n in foe_type_names]
    except Exception:
        foe_types = []

    def _incoming(mon) -> float:
        """Worst-case STAB multiplier the foe can hit `mon` for (defensive)."""
        try:
            mon_types = mon.species.types
        except Exception:
            try:
                mon_types = mon.types
            except Exception:
                return 1.0
        if not foe_types:
            return 1.0
        worst = 0.0
        for ft in foe_types:
            m = 1.0
            for t in mon_types:
                m *= ft.get_effectiveness_against(t)
            worst = max(worst, m)
        return worst

    def _can_attack(mon) -> bool:
        """Does `mon` have a DAMAGING move that is at least neutral on the foe? (#24-leadpolicy
        option (a).) A lead that cannot hurt the foe cannot win — it only stalls until PP runs
        out. Unknown/unreadable movepools return True so this can never bench a mon on a
        read failure."""
        if not foe_types:
            return True
        try:
            learned = list(getattr(mon, "moves", []) or [])
        except Exception:
            return True
        saw_move = False
        for lm in learned:
            if lm is None:
                continue
            mv = getattr(lm, "move", None)
            if mv is None or getattr(mv, "base_power", 0) <= 0:
                continue
            saw_move = True
            try:
                mult = 1.0
                for ft in foe_types:
                    mult *= mv.type.get_effectiveness_against(ft)
            except Exception:
                return True
            if mult >= 1.0:
                return True
        return not saw_move  # no readable damaging moves at all -> don't penalise

    def _glass_wonder_guard(mon) -> bool:
        """Wonder Guard on a 1-HP body (Shedinja) — `#24-leadpolicy` option (c).

        ‼ NOW OFF BY DEFAULT, AND THE MEASUREMENT SAYS WHY. I added (c) on the strength of a
        SINGLE observed loss (P4's Shedinja dying to Slaking's Faint Attack) and never checked
        how often it WON. `BADGE:` lines only print on a win, and the answer was in the logs
        the whole time:

            batch5 (before (c)):  Shedinja appears 12x — ALL 12 as a WINNING lead,
                                  including 9 of the 23 Norman victories (39%).
            batch7 (after (c)):   Shedinja appears 6x — 0 winning leads.
                                  Balance Badges 23 -> 18; finish rate 47.1% -> 26.9%.

        Wonder Guard makes Shedinja immune to Norman's ENTIRE Normal STAB, which is a genuinely
        strong lead there; Faint Attack is the exception, not the rule. Demoting it removed a
        lead that was winning.

        ‼ This is a HYPOTHESIS under test, not a settled fact — batch7 carried five changes and
        correlation is not causation. The flag exists so the A/B can be run instead of argued.
        `POKEBOT_LEAD_DEMOTE_WONDER_GUARD=1` restores the batch7 behaviour.
        """
        import os

        if os.environ.get("POKEBOT_LEAD_DEMOTE_WONDER_GUARD", "0").strip() not in ("1", "true", "yes"):
            return False
        try:
            return getattr(mon.ability, "name", "") == "Wonder Guard"
        except Exception:
            return False

    # #24-leadpolicy (user ruling A+C). The ordering keeps `incoming` ahead of the level
    # tie-break, so the proven Rustboro-rival behaviour is unchanged; (a) and (c) only
    # reorder mons the old rule treated as equivalent, plus the Wonder Guard trap it
    # treated as ideal. Ruling (b) — weight the level gap — was NOT selected.
    def _is_hunted_counter(mon) -> bool:
        """Did the counter chain catch this exact mon for THIS boss? (`#24-leadcounter`.)

        ‼ Matched by PERSONALITY VALUE, never by party slot. A slot goes stale the moment
        anything reorders or deposits — and since `#24-pc` the bot now deposits mid-run, so a
        slot-based identity would silently point at a different Pokémon. PID is immutable.
        """
        if not hunted_pids:
            return False
        try:
            return mon.personality_value in hunted_pids
        except Exception:  # noqa: BLE001 - an unreadable PID simply is not a counter
            return False

    from modules.story.team_policy import lead_rank_key

    best = min(
        slots,
        key=lambda i: lead_rank_key(
            incoming=_incoming(party[i]),
            can_attack=_can_attack(party[i]),
            glass_wonder_guard=_glass_wonder_guard(party[i]),
            level=party[i].level,
            is_hunted_counter=_is_hunted_counter(party[i]),
        ),
    )

    # ‼ LOG THE DECISION AND ITS INPUTS (added 2026-08-03). `#24-leadcounter` shipped without
    # this and batch7 could not be diagnosed: 6 runs caught AND trained a Machop to L29 and
    # every one of them still led something else into Norman, with nothing in the log saying
    # whether `hunted_pids` was empty, whether the mon was a candidate, or how it scored. A
    # decision with no trace is a decision nobody can debug — the same lesson as the KI-31
    # relocation, which was `console.print`-only and made its own A/B unevaluable.
    try:
        from modules.console import console

        _tag = lambda i: (  # noqa: E731
            f"{getattr(party[i].species, 'name', '?')}L{party[i].level}"
            f"[in={_incoming(party[i]):g}"
            f"{',atk' if _can_attack(party[i]) else ',NOATK'}"
            f"{',WG' if _glass_wonder_guard(party[i]) else ''}"
            f"{',COUNTER' if _is_hunted_counter(party[i]) else ''}]"
        )
        console.print(
            f"[dim]Story: lead vs {'/'.join(foe_type_names)} -> {_tag(best)} "
            f"(from {' '.join(_tag(i) for i in slots)}; "
            f"hunted_pids={len(hunted_pids or ())})[/]"
        )
    except Exception:  # noqa: BLE001 - logging must never affect the choice
        pass
    if best != 0:
        yield from _rotate_lead_safely(best)


def do_rustboro_gym() -> Generator:
    """Rustboro Gym — beat Roxanne for the Stone Badge (BADGE01, Gym 1).

    INTENT: clear the first gym.
    STORY CONDITION: in Rustboro City with a starter strong enough to win.
    Mudkip/Treecko are favourable (Mudkip's Water Gun is 4x on Roxanne's
    Rock/Ground Geodudes and 2x on Nosepass); TORCHIC is Fire = weak to Rock and
    has no super-effective move here, so a Torchic run may need extra training or
    a caught helper (TODO — see design notes / punch list).
    HOW IT WORKS: heal at the Rustboro Poké Center first (full-HP buffer for the
    un-fleeable gym-trainer + leader battles — a lone starter can't rotate),
    enter the gym, navigate up to the challenge tile below Roxanne (fighting the
    two gym Youngsters inline with the no-flee travel strategy), then face up and
    press A to challenge Roxanne. Advance dialogue until BADGE01_GET is set (the
    battle itself is driven by the battle listener / on_battle_started).
    GOAL/END STATE: BADGE01_GET set (Stone Badge earned), gym cleared."""
    from modules.memory import get_event_flag

    context.message = "Story: healing before challenging Rustboro Gym (Roxanne)..."
    yield from heal_in_pokemon_center(PokemonCenter.RustboroCity)

    # Lead with our strongest mon (training may have left a weak trainee in slot 0).
    yield from _lead_strongest_battler()

    context.message = "Story: entering Rustboro Gym to challenge Roxanne..."
    yield from navigate_to_anywhere(
        MapRSE.RUSTBORO_CITY_GYM,
        RUSTBORO_GYM_ROXANNE_APPROACH,
        avoid_encounters=True,
        avoid_scripted_events=False,
    )

    # Step up to the challenge tile (5,3) directly below Roxanne (5,2). Stop early
    # if a battle/script already engaged (a gym trainer's sight line, or Roxanne).
    for _ in range(40):
        if get_event_flag("BADGE01_GET") or get_global_script_context().is_active:
            break
        context.emulator.press_button("Up")
        yield

    # Challenge Roxanne (face up + A) and ride out the whole battle + dialogue
    # until the Stone Badge flag is set. The battle listener fights it (no-flee).
    frames = 0
    while not get_event_flag("BADGE01_GET"):
        _check_abort()  # bail fast if we whited out mid-gym (defeat recovery)
        context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 12000:
            raise BotModeError("Did not earn the Stone Badge from Roxanne.")
        yield
    yield from _wait_until_cutscene_over("B")
    context.message = "Story: earned the STONE BADGE — Gym 1 cleared!"


# Grass training spot near Rustboro (Route 116, directly east — 101 grass tiles,
# reachable straight from the city). Used for the pre-gym threshold + defeat retrain.
RUSTBORO_TRAINING_GRASS = (MapRSE.ROUTE116, (11, 7))


def _battler_slots() -> list[int]:
    """Party slots (0-based) that can actually battle: not an egg, has a damaging move."""
    slots = []
    for i, p in enumerate(get_party()):
        if p is None or p.is_egg:
            continue
        if any(lm is not None and lm.move.base_power > 0 for lm in p.moves):
            slots.append(i)
    return slots


#: Caves usable as training / counter-hunting grounds, and the warp tile that leads back
#: OUT to a route. Every entry is ROM-verified (`get_map_data(...).warps`), not guessed.
#:
#: ‼ WHY A TABLE AND NOT ONE HARDCODED CAVE (2026-07-26, #24-counters blocker #1). The
#: global navigator cannot cross warp levels, so ANY target outside a cave plan-fails
#: from within it ("not on connected maps") — that is what dropped two real-HW runs to
#: Manual on 2026-07-22. This helper existed but knew only Granite Cave, so the moment a
#: SECOND cave became a training ground the same stranding would ship again. The
#: two-way sweep proved exactly that: FIERY_PATH (18,19) is reachable OUT from Lavaridge,
#: but the return leg failed *inside the cave* — the tile could not be promoted until
#: this table existed.
#:
#: ‼‼ THE PARAGRAPH ABOVE IS HISTORY — IT STOPPED BEING TRUE ON 2026-07-31. `#24-journey`
#: made `navigate_to_anywhere` a multi-hop, self-replanning, live-validated warp navigator,
#: and `_navigate_riding_out` wraps it. MEASURED 2026-08-05 (`--driver cavethread`), with
#: NO table involved in either direction:
#:     IN  DEWFORD_TOWN -> ROUTE106 -> GRANITE_CAVE_1F -> B1F -> **B2F**  (3 warps)
#:     OUT GRANITE_CAVE_B1F -> GRANITE_CAVE_1F -> ROUTE106 -> **DEWFORD_TOWN**
#: So these two tables are now REDUNDANT, not load-bearing. They are kept because they are
#: harmless and cheap (a pre-step that threads one door via `_enter_warp_by_navigation`,
#: which handles warp tiles correctly) — but do NOT build a deeper "chain table" on the
#: premise above. `#24-cavethread` was scoped that way and the premise was already stale.
#:
#: ‼ THE ONE REAL GOTCHA, demonstrated twice: **NEVER pass a WARP TILE as a navigation
#: destination.** Walking onto a warp FIRES it, so the trip ends one map PAST the target and
#: the navigator reports success. Both probe runs hit this — a B2F ladder bounced the bot up
#: to B1F, and a Dewford door put it inside DEWFORD_TOWN_HOUSE1. Target a plain walkable tile.
_CAVE_EXITS: dict = {
    # -> ROUTE106. The Dewford-arc training spot; verified 2026-07-22.
    MapRSE.GRANITE_CAVE_1F: (37, 12),
    # -> ROUTE112. Fiery Path has exactly TWO warps, (26,36) south and (26,4) north, and
    # BOTH land on Route 112. South is the correct exit: Route 112's heal centre is
    # Lavaridge (`_training_area_heal_map`), which sits at the southern end, and it is
    # also the side the bot enters from (2 hops from Lavaridge). Leaving by the north
    # warp would surface it on the Route 111 side, further from any Poké Center.
    MapRSE.FIERY_PATH: (26, 36),
}


def _exit_training_cave_if_inside() -> Generator:
    """If standing inside a known training CAVE, thread its mouth back out to the route.

    The global navigator can NOT cross warp levels, so a heal that targets a town PC from
    inside a cave plan-fails ('not on connected maps') — two real-HW runs dropped to
    Manual on exactly that (2026-07-22, both at the Granite Cave (35,11) training spot
    with a hurt trainee). A cheap no-op anywhere that is not in `_CAVE_EXITS`."""
    here = _map_group_number()
    for cave_map, exit_tile in _CAVE_EXITS.items():
        _check_abort()
        if here == cave_map.value:
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() != cave_map.value,
                cave_map,
                exit_tile,
                label=f"{cave_map.name} exit (training heal)",
            )
            yield from wait_until_truly_controllable()
            return


#: The OUTSIDE approach for each cave in `_CAVE_EXITS`: the route map + the warp tile on
#: it that leads IN. The mirror of `_CAVE_EXITS`, used when the training/hunting ground
#: lives inside a cave and we are currently outside it. ROM-verified warps.
_CAVE_ENTRANCES: dict = {
    MapRSE.GRANITE_CAVE_1F: (MapRSE.ROUTE106, (48, 16)),
    # Route 112's SOUTH Fiery Path door — ROM-verified, and it PAIRS with the (26,36)
    # exit above: Route112 (11,36) is warp_id 0, which is exactly Fiery Path's (26,36).
    # (The other pair is Route112 (22,10) <-> Fiery Path (26,4), the north side.) So the
    # bot goes in and comes back out on the Lavaridge side it heals at.
    MapRSE.FIERY_PATH: (MapRSE.ROUTE112, (11, 36)),
}


def _goto_training_area(grass_map, grass_tile) -> Generator:
    """Navigate to the training spin tile, threading the CAVE door first when the area
    lives inside a cave and we're currently outside it — the counterpart of
    `_exit_training_cave_if_inside` for the return trip after a heal.

    Table-driven (2026-07-26) for the same reason as `_CAVE_EXITS`: it knew only Granite
    Cave, so a second in-cave ground would have failed to enter at all."""
    approach = _CAVE_ENTRANCES.get(grass_map)
    if approach is not None and _map_group_number() != grass_map.value:
        outside_map, door_tile = approach
        yield from _enter_warp_by_navigation(
            lambda: _map_group_number() == grass_map.value,
            outside_map,
            door_tile,
            label=f"{grass_map.name} entrance (training)",
        )
        yield from wait_until_truly_controllable()
    yield from _navigate_riding_out(grass_map, grass_tile, avoid_encounters=False)


def train_team(
    target_level: int,
    scope: str = "whole",
    grass: tuple = RUSTBORO_TRAINING_GRASS,
    heal_center: "PokemonCenter" = PokemonCenter.RustboroCity,
    slots: "set[int] | None" = None,
) -> Generator:
    """Grind wild battles until the team reaches ``target_level`` (defeat retrain /
    pre-fight threshold, user directive 2026-07-21).

    ``scope`` 'whole' trains every battler (rotating the lowest to the lead); 'lead'
    trains only the current lead. Heals at ``heal_center`` when HP dips near the
    flee threshold. A whiteout mid-training is caught and recovered by
    ``StoryMode.run()`` (the abort check bails us out promptly)."""
    from modules.modes.util.higher_level_actions import change_lead_party_pokemon

    grass_map, grass_tile = grass
    # Heal EARLY (big margin): the swap-train finisher heals only BETWEEN battles, so too
    # small a margin lets an unlucky hit faint it mid-battle and strand the bot on the
    # "choose your next Pokémon" menu (user 2026-07-21: all battles must survive failure).
    heal_at = float(getattr(context.config.battle, "hp_threshold", 20)) + 22.0
    guard = 0
    # SWAP-TRAIN (user directive 2026-07-21): hand wild battles to
    # SwapTrainBattleStrategy — an under-levelled lead is switched to a stronger
    # team-mate turn 1, so it shares XP without taking damage or fainting (no more
    # fight-faint-heal loop with a very low catch like a Lv2 Poochyena). Because the
    # mon actually FIGHTING is now the stronger team-mate, heal off the TEAM's lowest
    # HP, not the untouched slot-0 lead (which would sit at full HP and never heal).
    set_swap_train(True)
    try:
        while True:
            _check_abort()
            guard += 1
            if guard > 500:
                raise BotModeError("Training did not reach the target level (too many rounds).")

            party = get_party()
            if slots is not None:
                # Train ONLY the given slots (the caller's chosen battlers) — used to
                # ready the gym battlers without grinding fresh far-below catches.
                need = [i for i in _battler_slots() if i in slots and party[i].level < target_level]
            elif scope == "lead":
                need = [0] if party and not party[0].is_egg and party[0].level < target_level else []
            else:
                need = [i for i in _battler_slots() if party[i].level < target_level]
            if not need:
                break

            # Put the lowest-level needy battler in the lead so it shares the XP.
            # INTERRUPT-SAFE (the 110k-frame Joey stall): a trainer sight-line firing
            # right as the Start menu opens must abort-and-retry, never wedge.
            target_slot = min(need, key=lambda i: party[i].level)
            if target_slot != 0:
                yield from _rotate_lead_safely(target_slot)

            context.message = f"Story: training the team to Lv {target_level} in the grass…"
            yield from _goto_training_area(grass_map, grass_tile)

            # ‼ STOP SPINNING FOR PP TOO, NOT JUST HP (2026-07-26). Out of PP the bot
            # flees every encounter, gains nothing, and — because fleeing takes no
            # damage — never trips the HP trigger. See `_team_is_out_of_pp`.
            yield from _story_spin(
                lambda: _lead_level() >= target_level
                or _min_battler_hp_pct() <= heal_at
                or _team_is_out_of_pp()
            )
            _dry = _team_is_out_of_pp()
            if _dry:
                # ‼ SAY SO. A fix you cannot see fire cannot be validated — the whole
                # reason this bug survived ~2.9M frames is that nothing logged the
                # difference between "training" and "fleeing everything". A distinct
                # message makes the PP path observable in run logs and batch summaries.
                # ‼ LOCAL IMPORT REQUIRED: `early_game.py` has NO module-level `console`
                # (it is imported locally in three other functions only), so a bare
                # `console.print` here is a NameError — and this sits inside train_team's
                # try/finally, which does NOT swallow it, so every PP exhaustion would
                # CRASH instead of healing. Third time this shadowing/scope trap has bitten
                # in one day; see 08-MISTAKES 2026-07-26.
                from modules.console import console

                console.print(
                    "[bold yellow]Story: out of PP — healing at the Poké Center "
                    "(a heal restores PP, which is what lets training continue).[/]"
                )
            if (_min_battler_hp_pct() <= heal_at or _dry) and _lead_level() < target_level:
                # CAVE-AWARE HEAL (2× real-HW Manual drops 2026-07-22): healing from INSIDE
                # Granite Cave targeted the Dewford PC across warp levels — the global
                # navigator can't do that ("not on connected maps"). Exit the cave first.
                yield from _exit_training_cave_if_inside()
                yield from heal_in_pokemon_center(heal_center)

        # ‼ RESTORE THE STRONGEST LEAD BEFORE LEAVING THE GRIND.
        #
        # Swap-training deliberately rotates the LOWEST-level trainee into slot 0 so it
        # shares XP. Nothing used to put the good mon back, so the bot walked away from
        # training with its weakest battler leading — and the next trainer sight-line it
        # crossed opened with that mon.
        #
        # LIVE COST (user batch 20260726-201838, lane P2): **19 losses and 44 whiteouts**,
        # every single one at the SAME tile, ROUTE 110 (34,56), with the same party every
        # time — lead Dustox **L13** while Marshtomp **L21** sat in slot 2. KO one of
        # theirs, lose, white out to Slateport, walk back, lose again. Forever.
        #
        # ‼ Survival mode cannot save this: it is scoped to WILD battles
        # (`story_mode.py:1531`, `encounter is not None`) precisely because a TRAINER
        # battle cannot be fled. So the only fix is to not walk into it weak.
        #
        # `_lead_strongest_battler()`'s own docstring already described this hazard — it
        # was simply only ever applied before GYMS, never before travel.
        #
        # Placed after the loop rather than in `finally` on purpose: a `yield` inside a
        # finally block raises if the generator is being closed, and on the exception path
        # the run derails and resets anyway, so the lead does not survive to matter.
        yield from _lead_strongest_battler()
    finally:
        set_swap_train(False)


def _total_poke_balls() -> int:
    try:
        from modules.items import get_item_bag

        return sum(slot.quantity for slot in get_item_bag().poke_balls)
    except Exception:
        return 0


def _ball_count(name: str) -> int:
    """Quantity of a specific ball (e.g. 'Premier Ball', 'Poké Ball') in the bag."""
    try:
        from modules.items import get_item_bag

        return sum(slot.quantity for slot in get_item_bag().poke_balls if slot.item.name == name)
    except Exception:
        return 0


def _money() -> int:
    try:
        from modules.player import get_player

        return get_player().money
    except Exception:
        return 0


# --- Mart buying (planning doc §4). Poké Ball is item index 0 in every "basic" mart
# list (verified live: Rustboro basic = Poké Ball, Potion, Super Potion, …). ---
POKE_BALL_PRICE = 200
MONEY_RESERVE = 500      # never spend below this — keep a buffer for later needs
MAX_BALLS_PER_TRIP = 30  # "buy as many as it can", capped so we don't blow all money
# (mart map enum, counter-front tile, facing) — the player talks across the counter.
RUSTBORO_MART = (MapRSE.RUSTBORO_CITY_MART, (3, 3), "Left")


def affordable_poke_balls() -> int:
    """How many Poké Balls we can buy right now without dipping below the reserve."""
    return max(0, (_money() - MONEY_RESERVE) // POKE_BALL_PRICE)


def _mart_item_row(item_name: str) -> int | None:
    """Row (0-based cursor index) of ``item_name`` in the CURRENTLY-open mart's buy
    list, or None if this shop doesn't stock it. Reads sMartInfo's item array so we
    work at ANY mart regardless of its stock/order (shops differ — user note
    2026-07-21). Only valid while a shop menu is open."""
    try:
        from modules.memory import read_symbol, unpack_uint16, unpack_uint32
        from modules.pokemon import get_item_by_index

        info = read_symbol("sMartInfo")
        item_list_ptr = unpack_uint32(info[8:12])
        item_count = unpack_uint16(info[12:14])
        if not (0x08000000 <= item_list_ptr < 0x0A000000) or not (0 < item_count < 60):
            return None
        raw = context.emulator.read_bytes(item_list_ptr, length=item_count * 2)
        for i in range(item_count):
            iid = unpack_uint16(raw[i * 2 : i * 2 + 2])
            try:
                if get_item_by_index(iid).name == item_name:
                    return i
            except Exception:
                pass
    except Exception:
        pass
    return None


def buy_poke_balls(count: int, mart: tuple = RUSTBORO_MART) -> Generator:
    """Buy `count` Poké Balls at a mart. Poké Ball is item index 0 (cursor default),
    so the flow is: talk → BUY → select item 0 → set quantity → confirm → exit. Fully
    task-driven with bounded guards so it can never hang (planning doc §3/§4)."""
    from modules.tasks import task_is_active
    from modules.console import console

    mart_map, approach, face = mart
    if count <= 0:
        return
    context.message = f"Story: buying {count} Poké Balls at the mart…"
    yield from _navigate_riding_out(mart_map, approach)
    context.emulator.press_button(face)
    yield
    yield from wait_for_n_frames(6)

    from modules.modes.util.tasks_scripts import wait_until_task_is_not_active

    balls_before = _total_poke_balls()
    # Phase 1: advance the clerk dialogue until the Buy/Sell menu is up.
    guard = 0
    while not (task_is_active("Task_GoToBuyOrSellMenu") or task_is_active("Task_BuyMenu")) and guard < 60:
        context.emulator.press_button("A")
        guard += 1
        yield from wait_for_n_frames(10)
    # Phase 2: select BUY (cursor default). wait_until_task_is_not_active presses A
    # EVERY frame until the menu responds — single-frame presses don't register in
    # these list menus (the working pattern from wait_for_multiple_choice_question).
    if task_is_active("Task_GoToBuyOrSellMenu"):
        yield from wait_until_task_is_not_active("Task_GoToBuyOrSellMenu", "A")
    guard = 0
    while not task_is_active("Task_BuyMenu") and guard < 60:
        yield
        guard += 1
    if not task_is_active("Task_BuyMenu"):
        raise BotModeError("Mart: could not open the Buy list.")
    # Phase 3: item list. Find Poké Ball's ROW in THIS shop's stock (order differs per
    # mart — user note) and move the cursor down to it, then confirm (this ends
    # Task_BuyMenu and shows a "How many?" message), then advance that message with A
    # until the quantity selector opens.
    yield from wait_for_n_frames(10)
    row = _mart_item_row("Poké Ball")
    if row is None:
        raise BotModeError("Mart: this shop doesn't stock Poké Balls.")
    for _ in range(row):
        context.emulator.press_button("Down")
        yield from wait_for_n_frames(3)
    yield from wait_until_task_is_not_active("Task_BuyMenu", "A")
    guard = 0
    while not task_is_active("Task_BuyHowManyDialogueHandleInput") and guard < 60:
        context.emulator.press_button("A")
        guard += 1
        yield from wait_for_n_frames(6)
    if not task_is_active("Task_BuyHowManyDialogueHandleInput"):
        raise BotModeError("Mart: quantity selector didn't open.")
    # Phase 4: raise the quantity to `count` (starts at 1; caps at max affordable),
    # then confirm — the confirm advances to the "That'll be ¥X. OK?" Yes/No.
    yield from wait_for_n_frames(8)
    for _ in range(count - 1):
        context.emulator.press_button("Up")
        yield from wait_for_n_frames(4)
    yield from wait_for_n_frames(6)
    yield from wait_until_task_is_not_active("Task_BuyHowManyDialogueHandleInput", "A")
    # Phase 5: confirming the quantity shows "That'll be ¥X. OK?" — advance it with A
    # to the Yes/No, then confirm Yes (cursor default).
    guard = 0
    while not task_is_active("Task_CallYesOrNoCallback") and guard < 60:
        context.emulator.press_button("A")
        guard += 1
        yield from wait_for_n_frames(6)
    if task_is_active("Task_CallYesOrNoCallback"):
        yield from wait_until_task_is_not_active("Task_CallYesOrNoCallback", "A")
    yield from wait_for_n_frames(45)  # "Thank you!" + bag update
    console.print(f"[green]Story: bought Poké Balls ({balls_before} → {_total_poke_balls()}).[/]")
    # Phase 6: back out of the shop to the overworld.
    guard = 0
    while (
        task_is_active("Task_BuyMenu")
        or task_is_active("Task_GoToBuyOrSellMenu")
        or task_is_active("Task_ShopMenu")
    ) and guard < 200:
        context.emulator.press_button("B")
        guard += 1
        yield from wait_for_n_frames(4)
    settle = 0
    while settle < 300 and not player_avatar_is_controllable():
        context.emulator.press_button("B")
        settle += 1
        yield
    context.message = f"Story: bought Poké Balls (now have {_total_poke_balls()})."


def buy_poke_balls_in_tens(total: int, mart: tuple = RUSTBORO_MART) -> Generator:
    """Buy ``total`` Poké Balls, but as SEPARATE purchases of 10 (plus a remainder) to
    maximize free Premier Balls (user directive 2026-07-21).

    The mart gives exactly ONE Premier Ball per purchase of **10 or more** regular Poké
    Balls — so a single 30-ball purchase yields 1 Premier, but three 10-ball purchases
    yield 3. Total money spent is identical (Premier Balls are free), so buying in tens is
    strictly better. Any remainder (< 10) is bought last in one go (no Premier for it).

    Uses the tested single-purchase `buy_poke_balls` for each batch (it re-opens the shop
    at the counter each time — cheap, and far less risky than looping inside the shop UI)."""
    if total <= 0:
        return
    tens = total // 10
    remainder = total % 10
    premier_before = _ball_count("Premier Ball")
    balls_before = _ball_count("Poké Ball")
    context.message = (
        f"Story: buying {total} Poké Balls in {tens}×10"
        + (f" + {remainder}" if remainder else "")
        + " for free Premier Balls…"
    )
    for i in range(tens):
        yield from buy_poke_balls(10, mart)
    if remainder:
        yield from buy_poke_balls(remainder, mart)
    try:
        from modules.console import console

        console.print(
            f"[green]Story: bought {total} Poké Balls in {tens + (1 if remainder else 0)} purchase(s) "
            f"→ Poké Balls {balls_before}→{_ball_count('Poké Ball')}, "
            f"Premier Balls {premier_before}→{_ball_count('Premier Ball')} "
            f"(+{_ball_count('Premier Ball') - premier_before} free).[/]"
        )
    except Exception:
        pass


def provision_poke_balls(mart: tuple = RUSTBORO_MART) -> Generator:
    """Restock Poké Balls if we can afford it (out-of-balls contingency). Buys as many
    as affordable (capped), keeping a money reserve. Returns having bought or not; the
    caller checks the ball count and falls back (skip catching) if still empty."""
    want = min(MAX_BALLS_PER_TRIP, affordable_poke_balls())
    if want <= 0:
        context.message = "Story: too low on money to restock Poké Balls — skipping catching for now."
        return
    # A mart-menu hiccup must NEVER break catching — on failure, proceed with what we
    # have (the caller then falls back to skip). Re-raise a whiteout abort, though.
    # Buy in batches of 10 to collect the free Premier Ball each purchase gives (user
    # directive 2026-07-21) instead of one big purchase (which yields only one).
    try:
        yield from buy_poke_balls_in_tens(want, mart)
    except BotModeError as error:
        if story_should_abort():
            raise
        from modules.console import console

        console.print(f"[yellow]Story: mart restock hiccup ({error}) — proceeding with current balls.[/]")


def _party_size() -> int:
    return len([p for p in get_party() if p is not None and not p.is_egg])


def catch_starter_team(
    target_size: int = 4,
    grass: tuple = RUSTBORO_TRAINING_GRASS,
    heal_center: "PokemonCenter" = PokemonCenter.RustboroCity,
) -> Generator:
    """Spin in grass catching NEW species until the party reaches ``target_size``
    (organic team-building before the first gym, user directive 2026-07-21).
    ‼ ``target_size`` was raised 4 -> 6 on 2026-08-05 (`#24-partycap`) and REVERTED the same
    day — it cost 36 points of finish rate by crowding out the party's HM runway. Read
    ``StoryMode._catch_team_target`` before touching it. The
    catch-vs-fight decision per encounter is made by ``StoryMode.on_battle_started``
    (only NEW species, never a dup, never a shiny). Stops early if we run low on
    Poké Balls or hit a safety guard; a whiteout is handled by run()."""
    grass_map, grass_tile = grass
    # Heal EARLY (big margin): the swap-train finisher heals only BETWEEN battles, so too
    # small a margin lets an unlucky hit faint it mid-battle and strand the bot on the
    # "choose your next Pokémon" menu (user 2026-07-21: all battles must survive failure).
    heal_at = float(getattr(context.config.battle, "hp_threshold", 20)) + 22.0
    guard = 0
    if _party_size() < target_size and _total_poke_balls() > 1:
        context.message = "Story: catching a team before the first gym…"
    while _party_size() < target_size:
        _check_abort()
        guard += 1
        if guard > 250:
            break
        if _total_poke_balls() <= 1:
            # OUT-OF-BALLS CONTINGENCY (planning doc §3): try to restock at the mart;
            # if we can't afford it, stop catching and proceed with the team we have.
            yield from provision_poke_balls(mart=RUSTBORO_MART)
            if _total_poke_balls() <= 1:
                break
        yield from _navigate_riding_out(grass_map, grass_tile, avoid_encounters=False)

        yield from _story_spin(
            lambda: _party_size() >= target_size or _total_poke_balls() <= 1 or _lead_hp_pct() <= heal_at
        )
        if _lead_hp_pct() <= heal_at and _party_size() < target_size:
            yield from heal_in_pokemon_center(heal_center)


# Chapter 5 (Devon Goods errand) constants — all verified live 2026-07-21 via the
# mapdump tool + the ch5 recon harness (see design §Ch5 "BUILD PROGRESS"):
RUSTBORO_THEFT_WALK_TILE = (18, 20)      # walking here (west) after the gym fires the theft
ROUTE116_WEST_TILE = (5, 9)              # a walkable tile just inside Route 116 (west edge)
ROUTE116_TUNNEL_DOOR_APPROACH = (47, 9)  # stand here; the tunnel door is (47,8) directly north
RUSTURF_TUNNEL_DOOR_ON_ROUTE116 = (47, 8)
RUSTURF_GRUNT_APPROACH = (12, 5)         # adjacent-west of the grunt (13,5) / Mr. Briney (13,4)


def recover_devon_goods() -> Generator:
    """Chapter 5a — after Gym 1 the Devon Goods are stolen; chase the thief to
    Rusturf Tunnel and beat them to recover the goods (and free Peeko).

    INTENT: first half of the Devon errand (Chapter 5).
    STORY CONDITION: just beat Roxanne (starts inside the Rustboro Gym, or anywhere
    in Rustboro if resumed), no-flee travel strategy active.
    HOW IT WORKS (each step live-verified, design §Ch5):
      1. Walk west through Rustboro City (the gym-exit warp routes us out first) —
         this fires `RustboroCity_EventScript_StolenGoodsScene`. Anchor on the FLAG
         **DEVON_GOODS_STOLEN** (the scene has mid-scene controllable windows that
         fool the generic ride-out), riding out on any navigation abort.
      2. Chase EAST onto Route 116 (target its walkable WEST edge — the far tiles have
         no path through Route 116's ledges), then across to the tunnel-door approach
         (47,9). Wild encounters en route are fought by the listener (the starter may
         level/evolve — handled cleanly).
      3. Enter Rusturf Tunnel through the west door (Route116 (47,8), stepped into
         from below) via `_pass_through_door`.
      4. Approach the grunt at (13,5) from the west (it BLOCKS the corridor, so we
         can't pathfind past it — stop adjacent at (12,5)) and ENGAGE WITH A (not B —
         B skips the challenge). The grunt battle is fought by the listener; on the
         win the goods are recovered and Mr. Briney frees Peeko.
    GOAL/END STATE: **RECOVERED_DEVON_GOODS** set."""
    from modules.memory import get_event_flag

    route116 = MapRSE.ROUTE116.value
    tunnel = MapRSE.RUSTURF_TUNNEL.value

    # 1. Trigger the theft (exit the gym en route; anchor on the flag).
    context.message = "Story: leaving the gym — the Devon Goods get stolen…"
    rounds = 0
    while not get_event_flag("DEVON_GOODS_STOLEN"):
        _check_abort()
        rounds += 1
        if rounds > 20:
            raise BotModeError("The Devon-Goods theft scene (DEVON_GOODS_STOLEN) never fired.")
        try:
            yield from navigate_to_anywhere(
                MapRSE.RUSTBORO_CITY, RUSTBORO_THEFT_WALK_TILE,
                avoid_encounters=True, avoid_scripted_events=False,
            )
        except BotModeError:
            yield from _ride_out_scripted_scene("B")
    yield from _ride_out_scripted_scene("B")  # finish the tail of the theft scene

    # 2. Chase east: onto Route 116 (west edge), then across to the door approach.
    context.message = "Story: chasing the thief east to Rusturf Tunnel…"
    rounds = 0
    while _map_group_number() != route116:
        _check_abort()
        rounds += 1
        if rounds > 25:
            raise BotModeError("Could not reach Route 116 to chase the thief.")
        try:
            yield from navigate_to_anywhere(
                MapRSE.ROUTE116, ROUTE116_WEST_TILE,
                avoid_encounters=True, avoid_scripted_events=False,
            )
            break
        except BotModeError:
            yield from _ride_out_scripted_scene("B")
    rounds = 0
    while _map_group_number() == route116:
        _check_abort()
        rounds += 1
        if rounds > 12:
            raise BotModeError("Could not cross Route 116 to the Rusturf Tunnel door.")
        try:
            yield from navigate_to_anywhere(
                MapRSE.ROUTE116, ROUTE116_TUNNEL_DOOR_APPROACH,
                avoid_encounters=True, avoid_scripted_events=False,
            )
            # 3. Step north through the door (47,8) into the tunnel.
            yield from _pass_through_door(RUSTURF_TUNNEL_DOOR_ON_ROUTE116, route116)
            break
        except BotModeError:
            yield from _ride_out_scripted_scene("B")
    if _map_group_number() != tunnel:
        raise BotModeError("Did not enter Rusturf Tunnel from Route 116.")

    # 4. Approach the grunt (adjacent-west) and engage with A → battle → recover.
    context.message = "Story: cornering the thief in Rusturf Tunnel…"
    try:
        yield from navigate_to_anywhere(
            MapRSE.RUSTURF_TUNNEL, RUSTURF_GRUNT_APPROACH,
            avoid_encounters=True, avoid_scripted_events=False,
        )
    except BotModeError:
        # The grunt's line of sight can abort the approach — that's fine, engage below.
        yield from _ride_out_scripted_scene("B")
    frames = 0
    while not get_event_flag("RECOVERED_DEVON_GOODS"):
        _check_abort()  # bail fast if we whited out (defeat recovery)
        # Face/approach the grunt (Right) and advance the challenge + battle with A.
        # The battle listener fights the grunt; after the win the goods are recovered
        # and Mr. Briney's dialogue (freeing Peeko) plays out — A advances all of it.
        context.emulator.press_button("Right" if frames % 5 == 0 else "A")
        frames += 1
        if frames > 6000:
            raise BotModeError("Did not recover the Devon Goods from the tunnel grunt.")
        yield
    yield from _wait_until_cutscene_over("A")  # ride out the Briney/Peeko thank-you tail
    context.message = "Story: recovered the Devon Goods and freed Peeko!"


# --- Chapter 5b: return the Devon Goods → PokéNav + Steven's Letter → Rustboro rival ---
# Tiles reconned from ROM map data (design §Ch5b Atlas):
DEVON_CORP_3F = MapRSE.RUSTBORO_CITY_DEVON_CORP_3F
MRSTONE_APPROACH = (15, 6)          # stand below Mr. Stone (15,5), face North, talk
RUSTBORO_RIVAL_APPROACH = (16, 52)  # staging tile just N of the y=53 rival-trigger row; step Down to arm it


def return_devon_goods_and_get_pokenav() -> Generator:
    """Take the recovered Devon Goods back to Mr. Stone (Devon Corp 3F) — he returns
    them, hands over the PokéNav and Steven's Letter (RECEIVED_POKENAV).

    STORY CONDITION: RECOVERED_DEVON_GOODS set (we're in/near Rusturf Tunnel).
    GOAL/END: RECEIVED_POKENAV set; controllable back in Rustboro City."""
    from modules.memory import get_event_flag

    context.message = "Story: taking the Devon Goods back to Mr. Stone at Devon Corp..."
    # Ride out any lingering Rusturf recovery scene, then let the overworld settle.
    yield from _ride_out_scripted_scene("B")
    yield from wait_until_truly_controllable()
    # Route to Mr. Stone on Devon Corp 3F — navigate_to_anywhere threads the floors via
    # the stairs; the 1F guard lets us up now the goods are recovered. Rides out any
    # scripted greeting on the way.
    yield from _navigate_through_scripts(DEVON_CORP_3F, MRSTONE_APPROACH, avoid_encounters=True)
    yield from wait_until_truly_controllable()
    context.emulator.press_button("Up")  # face Mr. Stone (15,5) from (15,6)
    yield
    yield from wait_for_n_frames(4)
    # Advance the return + PokéNav + Letter dialogue until the PokéNav is received.
    frames = 0
    while not get_event_flag("RECEIVED_POKENAV"):
        _check_abort()
        context.emulator.press_button("A")
        frames += 1
        if frames > 8000:
            raise BotModeError("Never received the PokéNav from Mr. Stone.")
        yield
    yield from _wait_until_cutscene_over("B")
    context.message = "Story: got the PokéNav and Steven's Letter!"


def skip_pokenav_match_call_tutorial() -> Generator:
    """Neutralize the FORCED PokéNav Match-Call tutorial that the Rustboro Scientist
    (`RustboroCity_EventScript_ScientistAddMatchCall`) runs the instant you step into the
    city after getting the PokéNav — it fires from the map's ON_FRAME table while
    `VAR_RUSTBORO_CITY_STATE == 6`.

    WHY A STATE-WRITE INSTEAD OF PLAYING IT THROUGH: the tutorial opens the PokéNav in
    `POKENAV_MODE_FORCE_CALL_READY` and only ends once you actually place a Match Call to
    Mr. Stone through the full PokéNav app UI. That app is graphics-driven and does NOT
    advance in our faithful (video-off) harness — verified empirically: ~150 A-presses
    across 1500 frames produced zero progress, the PokéNav sat on `Task_Pokenav`/
    `Task_RunLoopedTask` the entire time. So a UI-navigation solution (a) could not be
    proven with our reproduce/fault-inject methodology and (b) would hang EVERY full-flow
    harness run at this point. Match Call has no bearing on story progress toward the
    Elite Four.

    WHAT THIS DOES: writes the EXACT world-state the tutorial itself leaves on completion,
    so the resulting save is indistinguishable from having watched it —
    `VAR_RUSTBORO_CITY_STATE = 7` (the value that disables the ON_FRAME trigger),
    `VAR_ROUTE104_STATE = 1`, and flags `HAS_MATCH_CALL` /
    `ADDED_MATCH_CALL_TO_POKENAV` / `HIDE_RUSTBORO_CITY_SCIENTIST` set (the exact
    setvar/setflag list from the decompiled script). Call it while still on Devon Corp 3F
    (before stepping into the city trigger).

    STORY CONDITION: `RECEIVED_POKENAV` set. GOAL/END: the Scientist trigger is disabled;
    the rival (gated only by `MET`/`DEFEATED_RIVAL_RUSTBORO`, no var) still fires normally.

    NOTE: This is an intentional, documented divergence — a targeted state-write that
    reproduces vanilla's end-state — logged in DIVERGENCE-LOG and design §Ch5b."""
    from modules.memory import get_event_var, set_event_var, set_event_flag

    if get_event_var("RUSTBORO_CITY_STATE") >= 7:
        return  # already past the tutorial — resume-safe, do nothing
    context.message = "Story: clearing the forced PokéNav Match-Call tutorial (state-write to vanilla end-state)..."
    set_event_var("RUSTBORO_CITY_STATE", 7)   # what the tutorial sets last; disables the ON_FRAME trigger
    set_event_var("ROUTE104_STATE", 1)        # ScientistAddMatchCall sets this at its start
    for flag in ("HAS_MATCH_CALL", "ADDED_MATCH_CALL_TO_POKENAV", "HIDE_RUSTBORO_CITY_SCIENTIST"):
        set_event_flag(flag, True)            # returns False (no-op) if absent in this ROM's table
    yield  # let the overworld pick up the new state for a frame


def handle_pokenav_match_call_tutorial() -> Generator:
    """FAITHFULLY clear the forced PokéNav Match-Call tutorial by actually placing the
    Match Call to Mr. Stone through the PokéNav app (then backing out) — the way a player
    would. Falls back to the state-write (`skip_pokenav_match_call_tutorial`) when the app
    can't be driven (headless) or the nav stalls, so the bot is never stuck either way.

    Harness-verified sequence (RENDERER ON): step into the city → the Scientist runs the
    tutorial (2 intro msgboxes → start-menu multichoice) → pick **POKéNAV (index 3)** →
    PokéNav main menu (cursor starts on HOENN MAP) → **Down,Down** → MATCH CALL → **A**
    (open the call list; cursor on MR. STONE) → **A** (CALL/CANCEL submenu; cursor on CALL)
    → **A** (place the call) → advance Mr. Stone's call with **A** → **B** out of the
    PokéNav → the tutorial script resumes and sets `VAR_RUSTBORO_CITY_STATE=7` → controllable.

    RENDERER REQUIRED + FALLBACK: the PokéNav app's looped tasks (`Task_Pokenav` /
    `Task_RunLoopedTask`) only advance when the BG/OBJ renderer is enabled (video on) —
    proven: with video off, ~150 A-presses = zero progress. So on a headless run, or if the
    faithful nav doesn't reach state 7 within budget, we FALL BACK to
    `skip_pokenav_match_call_tutorial()` (writes the same vanilla end-state). Either way the
    tutorial ends and the rival trigger (gated on `VAR_RUSTBORO_CITY_STATE==7`) is armed.

    STORY CONDITION: `RECEIVED_POKENAV` set, controllable in Rustboro City just after the
    PokéNav. GOAL/END: `VAR_RUSTBORO_CITY_STATE==7`."""
    from modules.memory import get_event_var
    from modules.modes.util.tasks_scripts import wait_for_multiple_choice_question
    from modules.tasks import task_is_active, get_global_script_context
    from modules.player import player_avatar_is_controllable

    if get_event_var("RUSTBORO_CITY_STATE") >= 7:
        return  # already past the tutorial — resume-safe

    # Headless (renderer off) → the PokéNav app can't advance; use the state-write end-state.
    if not context.emulator.get_video_enabled():
        context.message = "Story: PokéNav tutorial (headless, no renderer) — writing the vanilla end-state..."
        yield from skip_pokenav_match_call_tutorial()
        return

    def _tut_active():
        sc = get_global_script_context()
        in_script = sc.is_active and any(
            "ScientistAddMatchCall" in f or "MatchCallTutorial" in f for f in sc.stack
        )
        return in_script or task_is_active("Task_HandleMultichoiceInput")

    context.message = "Story: doing the PokéNav Match-Call tutorial (calling Mr. Stone)..."
    # 0) Trigger the tutorial: it fires from the map ON_FRAME table as you move through the
    #    city. Navigate toward the south exit (well north of the y=53 rival row) — the
    #    Scientist fires within a step or two and locks the player. (Proven: raw Down-presses
    #    don't reliably trigger it; the pathing walk does.)
    from modules.modes.util.global_navigation import navigate_to_anywhere

    triggered = False
    for _ in range(10):
        _check_abort()
        if _tut_active():
            triggered = True
            break
        try:
            yield from navigate_to_anywhere(
                MapRSE.RUSTBORO_CITY, (16, 40), avoid_encounters=True, avoid_scripted_events=False
            )
        except BotModeError:
            pass  # a scripted event (the tutorial) interrupted the walk — expected
        for _ in range(20):
            if _tut_active():
                triggered = True
                break
            yield
        if triggered:
            break
    if not triggered:
        # Couldn't provoke the tutorial — don't hang; write the vanilla end-state instead.
        yield from skip_pokenav_match_call_tutorial()
        return

    # 1) Advance the Scientist's intro msgboxes and select POKéNAV (index 3) from the menu.
    yield from wait_for_multiple_choice_question(3)

    # 2) Wait for the PokéNav main menu to be interactive (glowing cursor).
    for _ in range(600):
        if task_is_active("Task_CurrentMenuOptionGlow"):
            break
        yield
    yield from wait_for_n_frames(20)

    # 3) Main menu cursor starts on HOENN MAP; Down,Down → MATCH CALL.
    for _ in range(2):
        context.emulator.press_button("Down")
        yield
        yield from wait_for_n_frames(12)
    # 4) A: open the Match Call list (MR. STONE) → A: CALL submenu → A: place the call.
    for _ in range(3):
        context.emulator.press_button("A")
        yield
        yield from wait_for_n_frames(24)
    # 5) Advance Mr. Stone's call dialogue briefly.
    for _ in range(4):
        context.emulator.press_button("A")
        yield
        yield from wait_for_n_frames(12)
    # 6) B out of the PokéNav → the tutorial script resumes and sets STATE=7.
    deadline = 1500
    while deadline > 0 and get_event_var("RUSTBORO_CITY_STATE") < 7:
        deadline -= 1
        context.emulator.press_button("B")
        yield
    # Settle to controllable.
    for _ in range(600):
        if player_avatar_is_controllable():
            break
        context.emulator.press_button("B")
        yield

    # Safety net: if the faithful nav didn't complete, force the vanilla end-state so the
    # bot never hangs here.
    if get_event_var("RUSTBORO_CITY_STATE") < 7:
        context.message = "Story: PokéNav tutorial nav stalled — falling back to the state-write end-state..."
        yield from skip_pokenav_match_call_tutorial()
    else:
        context.message = "Story: PokéNav Match-Call tutorial done (called Mr. Stone)."


def fight_rustboro_rival() -> Generator:
    """The rival (May/Brendan) challenges you at the SOUTH exit of Rustboro on the way to
    Route 104. The battle is fired by a row of coord-triggers at y=53 (x 12–19), gated on
    `VAR_RUSTBORO_CITY_STATE == 7` — the exact value `skip_pokenav_match_call_tutorial`
    leaves, so the skip both clears the tutorial AND arms this trigger. Lead with our best
    mon, walk south across the trigger row, and win. GOAL/END: `DEFEATED_RIVAL_RUSTBORO`.

    PREREQUISITE: the PokéNav Match-Call tutorial must already be cleared (call
    `skip_pokenav_match_call_tutorial()` first) — otherwise the Scientist tutorial fires
    on the first step south. This rival hits harder than the gym: the caller should TRAIN
    the team first (see StoryMode `_play` §5b) or a weak team whites out (harness-observed).

    Harness-proven approach: navigate to the staging tile (16,52) just NORTH of the row,
    then step Down across y=53 to arm a trigger (`_navigate_riding_out` straight to a
    trigger tile can be refused as a scripted-event tile)."""
    from modules.memory import get_event_flag
    from modules.battle_state import battle_is_active
    from modules.tasks import get_global_script_context

    if get_event_flag("DEFEATED_RIVAL_RUSTBORO"):
        return
    context.message = "Story: heading south — the rival is waiting in Rustboro..."

    def _rival_engaging() -> bool:
        """The rival is engaging when a battle has started OR the rival coord-script is
        running (it locks the player). We must NOT key off MET_RIVAL_RUSTBORO — that flag
        STAYS set after a loss, so on a retry it would make us think we've engaged while
        still standing at the staging tile, and we'd never step onto the trigger (this was
        the 'stuck below the rival after a failed battle' bug)."""
        if battle_is_active():
            return True
        sc = get_global_script_context()
        return sc.is_active and any(
            any(k in f for k in ("RivalTrigger", "MayEncounter", "MayAskToBattle", "MayBattle",
                                 "MayFight", "BrendanEncounter", "BrendanAskToBattle",
                                 "BrendanBattle", "BrendanFight"))
            for f in sc.stack
        )

    # NOTE: the CALLER sets the battle lead (this rival is type-countered, so we want a
    # matchup-based lead via `_lead_best_matchup`, NOT lead-strongest). We don't touch it here.
    # Stage just north of the y=53 rival-trigger row, then walk Down onto it. This works on
    # the FIRST attempt AND on post-whiteout RETRIES (the trigger re-fires while not DEFEATED).
    yield from _navigate_riding_out(
        MapRSE.RUSTBORO_CITY, RUSTBORO_RIVAL_APPROACH, avoid_encounters=False
    )
    for _ in range(14):
        if _rival_engaging():
            break
        _check_abort()
        context.emulator.press_button("Down")
        yield
        yield from wait_for_n_frames(16)
    if not _rival_engaging():
        # The trigger row (RivalTrigger0-7 at (12-19,53)) requires VAR_RUSTBORO_CITY_STATE
        # == 7, and the MEETING sets it to 8 — so once the rival has been met (which can
        # happen ORGANICALLY mid-navigation: any southbound walk across the row after the
        # var reaches 7 fires the scene) the row is PERMANENTLY dead. VANILLA TRUTH: win
        # or lose, there is NO rematch (her talk script is only the Briney hint), and the
        # story does not require the win — so a met-and-lost state is RESOLVED, not a
        # failure (two batch runs burned their attempt caps on this, 2026-07-22).
        if get_event_flag("MET_RIVAL_RUSTBORO") and not get_event_flag("DEFEATED_RIVAL_RUSTBORO"):
            context.message = (
                "Story: the Rustboro rival was already met (and lost to) — vanilla offers "
                "no rematch; moving on."
            )
            return
        # Never met and still no engagement — derail so StoryMode re-localises and retries.
        raise BotModeError("Rustboro rival did not engage from the staging tile.")
    yield from _ride_out_scripted_scene("B", engage_timeout=2000)
    frames = 0
    while not get_event_flag("DEFEATED_RIVAL_RUSTBORO"):
        _check_abort()  # a LOSS whites out -> abort -> StoryMode whiteout recovery -> retry
        context.emulator.press_button("A")
        frames += 1
        if frames > 8000:
            break  # already handled / different completion — don't hang
        yield
    if not get_event_flag("DEFEATED_RIVAL_RUSTBORO"):
        # Neither won nor whited out within budget (unexpected) — derail so the caller retries.
        raise BotModeError("Rustboro rival battle ended without a win or a whiteout.")
    yield from wait_until_truly_controllable()
    context.message = "Story: beat the Rustboro rival — off toward Dewford."


def _talk_to_wandering_npc(
    map_enum, local_id: int, *, attempts: int = 8, approach_hint=None, known_spot=None
) -> Generator:
    """Engage a WANDERING (patrolling) NPC in conversation on the current small indoor map.

    WHY THE OBVIOUS APPROACHES FAIL (all live-proven in Mr. Briney's cottage):
    - A static approach-tile + face-press: a patrolling NPC is almost never on its spawn
      tile — and a face-tap toward an EMPTY tile STEPS onto it if already facing that way.
    - Navigating a full path to a tile adjacent to his CURRENT position: he has always
      moved on by the time the multi-frame navigate lands (circled the cottage 30× without
      engaging).
    - A greedy step-by-step chase: walk-sequence NPCs patrol a fixed ring (Briney laps the
      cottage's central table); a tail-chase around a ring never catches him, and bumping
      into a blocker while standing ON the NPCs' route tiles can freeze the whole room
      solid (three-body deadlock: walk-sequence NPCs wait forever for their exact next
      route tile, they never re-route).

    - Parking ON one of his route tiles to block him into stopping next to us: with TWO
      walkers lapping the SAME ring in the same direction (Peeko runs ahead of Briney),
      the WRONG one always queues against us first and the target freezes two tiles back,
      out of talking reach.

    HOW (observe → park beside → talk on transit):
    1. OBSERVE ~one patrol lap, recording every tile each walker visits (their fixed
       routes). Talk immediately if the target happens to pass adjacent; if the walkers
       freeze mid-observation, WE are standing on a route tile — step off it.
    2. Pick an ambush tile BESIDE his route: statically walkable, on NOBODY's recorded
       route (blocks no one — no queues, no deadlocks), not a warp tile, orthogonally
       adjacent to a tile he visits.
    3. Park there and stand still. Every lap he transits the adjacent route tile (walkers
       dwell ~30+ frames per tile): face-tap toward him (his tile is occupied, so the tap
       can only turn/bump, never step), verify he is still there, press A, and confirm the
       script context actually ENGAGED.

    Raises BotModeError if the NPC is absent or never engages within `attempts` rounds."""
    import os

    from modules.map import get_map_data, get_map_objects

    def _npc_coords() -> tuple[int, int] | None:
        try:
            for o in get_map_objects():
                if o.local_id == local_id:
                    return tuple(o.current_coords)
        except Exception:
            pass
        return None

    _dbg = bool(os.environ.get("STORY_TALK_DEBUG"))
    _FACE = {(0, -1): "Up", (0, 1): "Down", (-1, 0): "Left", (1, 0): "Right"}
    _DELTA = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
    try:
        _warp_tiles = {tuple(w.local_coordinates) for w in get_map_data_for_current_position().warps}
    except Exception:
        _warp_tiles = set()

    def _try_talk_if_adjacent() -> Generator:
        """If the target NPC is adjacent RIGHT NOW, face him and press A. Yields; the
        engagement result is read by the caller via get_global_script_context()."""
        c = _npc_coords()
        if c is None:
            return
        px, py = get_player_avatar().local_coordinates
        dx, dy = c[0] - px, c[1] - py
        if abs(dx) + abs(dy) != 1:
            return
        face = _FACE[(dx, dy)]
        context.emulator.press_button(face)  # bump-safe: his tile is occupied
        yield
        yield from wait_for_n_frames(4)
        if _npc_coords() != c:
            return  # stepped away as we turned — don't talk to air
        context.emulator.press_button("A")
        yield
        for _ in range(60):
            if get_global_script_context().is_active:
                return
            yield

    def _step_to(spot) -> Generator:
        """Greedy single-step walk to `spot` (NOT navigate_to: the pathfinder marks every
        walker's current AND previous tile blocked, so in a tiny room two patrolling NPCs
        seal every corridor at plan time and it reports "no path" to plainly walkable
        tiles). Perpendicular/reverse fallbacks when the direct step is blocked; talks
        opportunistically if the target happens to pass right next to us en route."""
        for _ in range(30):
            _check_abort()
            yield from _try_talk_if_adjacent()
            if get_global_script_context().is_active:
                return
            px, py = get_player_avatar().local_coordinates
            if (px, py) == spot:
                return
            dx, dy = spot[0] - px, spot[1] - py
            prefs = []
            if dx:
                prefs.append("Right" if dx > 0 else "Left")
            if dy:
                prefs.append("Down" if dy > 0 else "Up")
            if abs(dy) > abs(dx):
                prefs.reverse()
            for d in ("Up", "Down", "Left", "Right"):
                if d not in prefs:
                    prefs.append(d)
            moved = False
            for d in prefs:
                ddx, ddy = _DELTA[d]
                if (px + ddx, py + ddy) in _warp_tiles:
                    continue  # never step onto a door/warp — that would leave the map
                start = (px, py)
                for _ in range(24):
                    context.emulator.press_button(d)
                    yield
                    if tuple(get_player_avatar().local_coordinates) != start:
                        moved = True
                        break
                if moved:
                    break
            if not moved:
                yield from wait_for_n_frames(16)  # momentarily boxed in — let walkers shift

    cur_map_md = get_map_data_for_current_position()
    _gnum = (cur_map_md.map_group, cur_map_md.map_number)

    def _walkable(t: tuple[int, int]) -> bool:
        try:
            return get_map_data(_gnum, t).collision == 0
        except Exception:
            return False

    for _round in range(attempts):
        _check_abort()
        if get_global_script_context().is_active:
            return  # engaged
        yield from _try_talk_if_adjacent()
        if get_global_script_context().is_active:
            if _dbg:
                print(f"[talk] ENGAGED opportunistically (round {_round})")
            return

        # PHASE 0 — make sure the object is LOADED. The GBA engine only materializes
        # object events near the camera, so on a big map (a town) the target simply
        # isn't in RAM until we walk toward it (live-hit: Briney's dock object was
        # "absent" from across Dewford after a PC heal). `approach_hint` = a walkable
        # tile near the NPC's spawn to navigate to first.
        if _npc_coords() is None and approach_hint is not None:
            yield from _navigate_riding_out(map_enum, approach_hint)
            yield from wait_for_n_frames(30)

        # PHASE 0.5 — KNOWN-SPOT FAST PATH (user directive 2026-07-22): when a validated
        # ambush tile is known for this NPC, go STRAIGHT there and wait roughly a patrol
        # lap for the target to transit adjacent — the observe lap plus trial parking
        # read as "arbitrary wandering" on real hardware (user-observed at BOTH Briney
        # talks). The adaptive observe-then-park procedure below stays as the fallback
        # if the fast path doesn't engage within the wait.
        if known_spot is not None and _round == 0:
            # PATHFINDER FIRST, greedy stepping only as the fallback. `_step_to` takes
            # single greedy steps with no route planning, so any wall between us and the
            # spot sends it wandering into whatever pocket the fallbacks lead to — on
            # real hardware (2026-07-23) that walked the bot from Dewford's Poké Center
            # to the dead-end south-east of the dock (the wall band at y=10, x=10-13)
            # and it loitered there for thousands of frames. The pathfinder handles a
            # town fine; `_step_to` is only needed in tiny rooms where patrolling
            # walkers make `calculate_path` report "no path" to plainly walkable tiles.
            try:
                yield from _navigate_riding_out(map_enum, known_spot, tries=3)
            except BotModeError as error:
                reraise_if_aborting(error)  # `#24-abortrecoveryresiduals` (c) — PRE-EXISTING swallower. Latch-keyed:
                # with no whiteout pending it does nothing; with one, the unwind escapes instead of being
                # absorbed here. This handler predates `#24-loopheadabort`.
                pass
            if tuple(get_player_avatar().local_coordinates) != tuple(known_spot):
                yield from _step_to(known_spot)
            for _f in range(900):
                _check_abort()
                yield from _try_talk_if_adjacent()
                if get_global_script_context().is_active:
                    if _dbg:
                        print("[talk] ENGAGED via known_spot fast path")
                    return
                yield

        # PHASE 1 — OBSERVE one full patrol lap: record every tile each walker visits.
        # (Also talk instantly if the target passes adjacent, and un-block the room if
        # everyone froze — frozen walkers mean WE are standing on someone's route tile.)
        target_route: set[tuple[int, int]] = set()
        other_route: set[tuple[int, int]] = set()
        last_snapshot = None
        still_frames = 0
        for _f in range(700):
            _check_abort()
            try:
                objs = {o.local_id: tuple(o.current_coords) for o in get_map_objects() if o.local_id != 255}
            except Exception:
                objs = {}
            if local_id in objs:
                target_route.add(objs[local_id])
            for k, v in objs.items():
                if k != local_id:
                    other_route.add(v)
            c = objs.get(local_id)
            if c is not None:
                px, py = get_player_avatar().local_coordinates
                if abs(c[0] - px) + abs(c[1] - py) == 1:
                    yield from _try_talk_if_adjacent()
                    if get_global_script_context().is_active:
                        if _dbg:
                            print(f"[talk] ENGAGED during observation (round {_round})")
                        return
            if objs == last_snapshot:
                still_frames += 1
            else:
                still_frames = 0
                last_snapshot = objs
            if still_frames > 180:
                # The walkers are frozen → we are blocking a route tile. Step somewhere
                # that is NOT a recorded route tile to let the patrol flow again.
                px, py = get_player_avatar().local_coordinates
                for d, (ddx, ddy) in _DELTA.items():
                    t = (px + ddx, py + ddy)
                    if t in _warp_tiles or t in target_route or t in other_route or not _walkable(t):
                        continue
                    for _ in range(24):
                        context.emulator.press_button(d)
                        yield
                        if tuple(get_player_avatar().local_coordinates) != (px, py):
                            break
                    break
                still_frames = 0
            yield
        if not target_route:
            raise BotModeError(f"NPC local_id={local_id} is not present on map {map_enum}.")

        # PHASE 2 — pick an ambush tile BESIDE his route: walkable, NOT on either walker's
        # route (blocking a route tile only queues the LEAD walker against us — with two
        # walkers lapping the same ring the wrong one always arrives first and the target
        # freezes two tiles back; live-proven), not a warp, adjacent to a tile he visits.
        px, py = get_player_avatar().local_coordinates
        candidates: list[tuple[int, int]] = []
        for t in target_route:
            for ddx, ddy in _DELTA.values():
                p = (t[0] + ddx, t[1] + ddy)
                if p in target_route or p in other_route or p in _warp_tiles:
                    continue
                if not _walkable(p):
                    continue
                candidates.append(p)
        candidates = sorted(set(candidates), key=lambda p: abs(p[0] - px) + abs(p[1] - py))
        if _dbg:
            print(f"[talk] round {_round}: route={sorted(target_route)} beside-candidates={candidates[:6]}")
        if not candidates:
            yield from wait_for_n_frames(60)
            continue

        # PHASE 3 — park beside the route and press A whenever HE transits the adjacent
        # route tile (walkers dwell ≥~30 frames per tile — a wide window; and he passes
        # us every lap, so a miss just waits for the next lap).
        yield from _step_to(candidates[0])
        if get_global_script_context().is_active:
            return
        for _wait in range(1500):
            _check_abort()
            c = _npc_coords()
            px, py = get_player_avatar().local_coordinates
            if c is not None and abs(c[0] - px) + abs(c[1] - py) == 1:
                yield from _try_talk_if_adjacent()
                if get_global_script_context().is_active:
                    if _dbg:
                        print(f"[talk] ENGAGED from beside-route ambush at ({px},{py})")
                    return
            yield
        if _dbg:
            print(f"[talk] beside-route ambush timed out (round {_round}) — re-observing")
    raise BotModeError(f"Could not engage NPC local_id={local_id} on map {map_enum} in conversation.")


# Warp geometry for the sail leg (doorprobe-verified 2026-07-22; see §Ch6):
# Route 104 is river-split — the ONLY north↔south path is through Petalburg Woods.
#   Woods NORTH doors:  Route104 (10,30)/(11,30) ↔ inside Woods (14,5)/(15,5)
#   Woods SOUTH doors:  inside Woods (16,38)/(17,38) ↔ Route104 (10,38)/(11,38)
#   Mr. Briney's door:  Route104 (17,50) ↔ house interior (5,8); Briney NPC at (5,3)
WOODS_NORTH_DOOR_ROUTE104 = (11, 30)   # step onto this from the north strip → Woods (15,5)
WOODS_NORTH_DOOR_STAGING = (11, 29)    # tile directly above the north door (route104_north checkpoint)
WOODS_SOUTH_DOOR_INSIDE = (17, 38)     # step onto this inside the Woods → Route104 (11,38) south half
WOODS_SOUTH_DOOR_STAGING = (17, 37)    # tile directly above the inside-south door
BRINEY_DOOR_ROUTE104 = (17, 50)        # cottage door on the south beach → interior (5,8)
BRINEY_LOCAL_ID = 1                    # Briney's object slot in his cottage (Peeko = 2); he PATROLS
                                       # a walk-sequence loop, so talk via _talk_to_wandering_npc


def sail_to_dewford() -> Generator:
    """After the Rustboro rival, travel Rustboro → Mr. Briney's cottage and sail to Dewford.

    INTENT: Chapter 6 — the sail leg toward Gym 2. The player carries Steven's Letter (got
    with the PokéNav) and the rival is beaten, so Briney offers the Dewford sail.
    ROUTE (§Ch6, every warp doorprobe-verified): Rustboro (post-rival (16,53)) → walk Down
    across the south connection onto ROUTE104 (16,0) — the NORTH strip. Route 104 is
    RIVER-SPLIT, so the south beach is reachable only back THROUGH Petalburg Woods:
    north door Route104 (11,30) → Woods (15,5) → cross the Woods southbound → inside door
    (17,38) → Route104 (11,38) on the SOUTH beach → Briney's cottage door (17,50) →
    interior (5,8) → talk to Briney (5,3) from (5,4).
    THE SAIL (✓ script-verified from the decomp): the FIRST sail is a YES/NO ("We'll set
    sail for DEWFORD" — A-through picks YES, the cursor default); later sails show the
    MULTI_BRINEY_OFF_DEWFORD multichoice (Dewford = index 0) — both are handled. On YES the
    game warps the player to the boat at ROUTE104 (13,51) and the sail cutscene crosses the
    sea; we ride it out until the map is DEWFORD_TOWN.
    GOAL/END STATE: controllable in Dewford Town. Idempotent + resume-safe: every leg is
    keyed off the LIVE map (§SC), so a resume from any point picks up mid-route.
    STORY CONDITION: `DEFEATED_RIVAL_RUSTBORO` set (the Route 104 rival NPC at (17,50) only
    appears when the Rustboro meeting was SKIPPED — MET flag unset — so our door is clear)."""
    from modules.modes.util.tasks_scripts import wait_for_multiple_choice_question

    DEWFORD = MapRSE.DEWFORD_TOWN.value
    ROUTE104 = MapRSE.ROUTE104.value
    WOODS = MapRSE.PETALBURG_WOODS.value
    RUSTBORO = MapRSE.RUSTBORO_CITY.value
    BRINEY_HOUSE = MapRSE.ROUTE104_MR_BRINEYS_HOUSE.value

    if _map_group_number() == DEWFORD:
        return
    context.message = "Story: heading to Mr. Briney's cottage to sail to Dewford..."
    yield from wait_until_truly_controllable()

    # --- Leg 0: Rustboro → Route 104 north strip. The global navigator can't one-shot
    #     this connection (ML-7 family); from the south edge, walking Down crosses onto
    #     ROUTE104 (16,0). VALIDATED 2026-07-21. ---
    if _map_group_number() == RUSTBORO:
        yield from _navigate_riding_out(MapRSE.RUSTBORO_CITY, (16, 53))
        steps = 0
        while _map_group_number() == RUSTBORO:
            _check_abort()
            if steps > 45:
                raise BotModeError("Sail: could not cross Rustboro's south edge onto Route 104.")
            context.emulator.press_button("Down")
            yield
            yield from wait_for_n_frames(12)
            steps += 1
        yield from wait_until_truly_controllable()

    # --- Leg 1: Route 104 NORTH strip → into Petalburg Woods through the north door.
    #     (On the north strip = y ≤ 30; the split river blocks everything south.) ---
    if _map_group_number() == ROUTE104 and get_player_avatar().local_coordinates[1] <= 30:
        yield from _navigate_riding_out(MapRSE.ROUTE104, WOODS_NORTH_DOOR_STAGING)
        yield from wait_for_player_avatar_to_be_standing_still()
        yield from _pass_through_door(WOODS_NORTH_DOOR_ROUTE104, ROUTE104)
        if _map_group_number() != WOODS:
            raise BotModeError("Sail: stepped onto the Woods north door but did not enter the Woods.")
        yield from wait_until_truly_controllable()

    # --- Leg 2: cross Petalburg Woods NORTH→SOUTH (reverse of cross_petalburg_woods).
    #     The mandatory Devon-researcher scene is long done (Ch3) and the route trainers
    #     were beaten northbound, but ride out anything that still aborts the path. ---
    if _map_group_number() == WOODS:
        rounds = 0
        while _map_group_number() == WOODS:
            _check_abort()
            rounds += 1
            if rounds > 15:
                raise BotModeError("Sail: stuck crossing Petalburg Woods southbound.")
            try:
                yield from navigate_to_anywhere(
                    MapRSE.PETALBURG_WOODS,
                    WOODS_SOUTH_DOOR_STAGING,
                    avoid_encounters=True,
                    avoid_scripted_events=False,
                )
                break
            except BotModeError:
                yield from _ride_out_scripted_scene("B")
        yield from wait_for_player_avatar_to_be_standing_still()
        yield from _pass_through_door(WOODS_SOUTH_DOOR_INSIDE, WOODS)
        if _map_group_number() != ROUTE104:
            raise BotModeError("Sail: stepped onto the Woods south door but did not exit to Route 104.")
        yield from wait_until_truly_controllable()

    # --- Leg 3: Route 104 SOUTH beach → Briney's cottage. The door tile IS the navigation
    #     target (a genuine step onto it fires the warp, ML-9); navigate_to_anywhere may
    #     raise as the warp yanks the map out from under it, so success = the map changed. ---
    if _map_group_number() == ROUTE104:
        for _ in range(10):
            _check_abort()
            if _map_group_number() != ROUTE104:
                break
            try:
                yield from navigate_to_anywhere(
                    MapRSE.ROUTE104, BRINEY_DOOR_ROUTE104, avoid_encounters=True, avoid_scripted_events=False
                )
            except BotModeError:
                if _map_group_number() != ROUTE104:
                    break  # the warp fired mid-navigate — we're inside
                yield from _ride_out_scripted_scene("B")
    if _map_group_number() not in (BRINEY_HOUSE, DEWFORD):
        raise BotModeError("Sail: never reached the inside of Mr. Briney's cottage.")

    # --- Leg 4: talk to Briney and set sail. He PATROLS the cottage (live-probed: he is
    #     almost never on his (5,3) spawn tile), so engage him via his LIVE object position.
    #     Then A-through the dialogue; the FIRST sail's YES/NO confirms on A (cursor
    #     defaults to YES); a repeat sail's multichoice picks Dewford = index 0. Confirming
    #     warps us OUT of the house onto the boat (ROUTE104 (13,51)) — leaving the house
    #     map is the signal the sail was accepted. ---
    if _map_group_number() == BRINEY_HOUSE:
        yield from wait_until_truly_controllable()
        # known_spot (6,2): validated ambush tile beside Briney's table ring — the talk
        # engaged there on real hardware (user log 2026-07-22); fast path skips the
        # observe lap, the adaptive procedure remains the fallback.
        yield from _talk_to_wandering_npc(
            MapRSE.ROUTE104_MR_BRINEYS_HOUSE, BRINEY_LOCAL_ID, known_spot=(6, 2)
        )
        presses = 0
        while _map_group_number() == BRINEY_HOUSE:
            _check_abort()
            if presses > 900:
                raise BotModeError("Sail: talked to Briney but the sail never started.")
            if task_is_active("Task_HandleMultichoiceInput"):
                yield from wait_for_multiple_choice_question(0)  # repeat-sail menu: Dewford = index 0
                continue
            context.emulator.press_button("A")
            presses += 1
            yield
            yield from wait_for_n_frames(6)

    # --- Leg 5: ride out the sail cutscene (boat crosses the sea) until Dewford. ---
    frames = 0
    while _map_group_number() != DEWFORD:
        _check_abort()
        context.emulator.press_button("B")
        frames += 1
        if frames > 12000:
            raise BotModeError("Sail: never arrived in Dewford after setting sail.")
        yield
    # RIDE OUT the arrival dialogue before waiting for control: Briney's post-sail
    # "deliver the Letter" reminder (Route104_EventScript_DeliverLetterReminder) stays
    # OPEN on arrival, and wait_until_truly_controllable presses NOTHING by design —
    # the real-hardware run 2026-07-22 sat at the dock deriling forever on that open
    # textbox. _ride_out_scripted_scene B-advances any active script first.
    yield from _ride_out_scripted_scene("B")
    yield from wait_until_truly_controllable()
    context.message = "Story: arrived in Dewford Town!"


# ---- Chapter 7: Granite Cave (Steven's Letter) + Dewford Gym 2 (Brawly) ----
# Static recon 2026-07-22 (ch7 doorprobe): Dewford PC door = town (2,10) → PC (7,8);
# Gym door = town (8,17) → gym (5,27)/(6,27). Dewford's North connection → Route 106
# (offset -60: Dewford x ↔ Route106 x+60 on its south edge). Granite Cave entrance =
# ROUTE106 (48,16) → 1F (37,12). ‼ STEVEN'S ROOM HANGS OFF 1F: warp (5,10) → room (7,3)
# — NOT off B1F as the first atlas said ((12,3) is the B1F↔B2F ladder pair). Steven
# stands at (7,8) (static). Route 106 beach trainers: Elliot (51,14), Ned (65,14);
# 1F Hiker at (36,9). NO training grass anywhere around Dewford pre-Surf (Route 106 is
# surf-only; Granite Cave wilds are L6-10).
GRANITE_CAVE_DOOR_ROUTE106 = (48, 16)   # step onto it → GRANITE_CAVE_1F (37,12)
STEVENS_ROOM_DOOR_1F = (5, 10)          # step onto it → STEVENS_ROOM (7,3)
STEVEN_APPROACH = (7, 7)                # stand above Steven (7,8), face Down, talk
DEWFORD_GYM_BRAWLY_APPROACH = (4, 4)    # challenge tile directly below Brawly (4,3)
# Loss-escalation training spot (⚠ only used after ≥2 Brawly losses; wilds are L6-10 so
# it's slow XP — but it is the ONLY wild source reachable from Dewford before Surf):
GRANITE_CAVE_TRAINING_SPOT = (MapRSE.GRANITE_CAVE_1F, (35, 11))


def _enter_warp_by_navigation(dest_reached, map_enum, door_tile, *, tries: int = 10, label: str = "") -> Generator:
    """Navigate onto ``door_tile`` on ``map_enum`` until ``dest_reached()`` is True.
    The door tile IS the navigation target (a genuine step onto it fires the warp,
    ML-9); navigate_to_anywhere may raise as the warp yanks the map away mid-path, so
    success is judged by ``dest_reached()``, and scripted interruptions (a trainer's
    sight-line, a scene) are ridden out between tries."""
    last_error: BotModeError | None = None
    for _ in range(tries):
        _check_abort()
        if dest_reached():
            return
        # ‼ ALREADY STANDING ON THE DOOR TILE (ch12_run1, 2026-07-24): a warp fires on
        # STEPPING onto it — a battle that ends with the avatar parked on the tile (or
        # a resume that loads there) leaves the warp dormant, and navigating "to" the
        # tile we're on moves zero steps, so every try times out to Manual. Step OFF
        # one tile (any direction that moves us), then let the normal navigation step
        # back ON to trigger it.
        try:
            _mgn = _map_group_number()
            _pos = tuple(get_player_avatar().local_coordinates)
        except Exception:
            _mgn, _pos = None, None
        if _mgn == (map_enum.value if hasattr(map_enum, "value") else map_enum) and _pos == tuple(door_tile):
            for _dir in ("Down", "Up", "Left", "Right"):
                context.emulator.press_button(_dir)
                yield from wait_for_n_frames(20)
                try:
                    if tuple(get_player_avatar().local_coordinates) != tuple(door_tile):
                        break
                except Exception:
                    break
            yield from wait_for_player_avatar_to_be_standing_still()
        try:
            yield from navigate_to_anywhere(map_enum, door_tile, avoid_encounters=True, avoid_scripted_events=False)
        except BotModeError as e:
            if dest_reached():
                return
            last_error = e
            yield from _ride_out_scripted_scene("B")
    if not dest_reached():
        raise BotModeError(
            f"Could not enter the warp at {door_tile} on {map_enum} ({label}). Last navigation error: {last_error}"
        )


def deliver_stevens_letter() -> Generator:
    """Chapter 7a — deliver Steven's Letter in Granite Cave (gets TM47 Steel Wing).

    INTENT: the Letter (received with the PokéNav from Mr. Stone) is bound for Steven in
    Granite Cave; delivering it sets `DELIVERED_STEVEN_LETTER`, registers Steven in the
    PokéNav and yields TM47. It also unlocks nothing else — but it is the story reason we
    sailed to Dewford, and Mr. Briney waits for it before offering the Slateport leg.
    ROUTE (every within-floor hop verified via the pathfinder, 2026-07-22): Dewford →
    Route 106 beach → Granite Cave door (48,16) → then the FIVE-WARP LADDER CHAIN — the
    cave floors are all split into disconnected sections, and the true route (matching
    vanilla) dips through B2F: 1F (17,11) ↓ B1F (4,21) → (28,21) ↓ B2F (28,21) → (29,13)
    ↑ B1F (29,13) → (25,13) ↑ 1F (35,3) → Steven's door (5,10) → room (7,3) → Steven at
    (7,8): talk from (7,7) facing Down, A-through (✓ script-verified: no choices; Letter
    taken, TM47 given, flag set, Steven departs and despawns) → the exact reverse chain →
    Dewford.
    GOAL/END STATE: `DELIVERED_STEVEN_LETTER` set, controllable back in Dewford Town.
    STORY CONDITION: in/around Dewford with the Letter in the bag. Resume-safe: the chain
    walker locates the current position by LIVE pathability (a floor appears twice in the
    chain — which occurrence we're at is decided by which warp is reachable from here)."""
    from modules.memory import get_event_flag
    from modules.map_path import calculate_path

    DEWFORD = MapRSE.DEWFORD_TOWN.value
    ROUTE106 = MapRSE.ROUTE106.value
    CAVE_1F = MapRSE.GRANITE_CAVE_1F.value
    CAVE_B1F = MapRSE.GRANITE_CAVE_B1F.value
    CAVE_B2F = MapRSE.GRANITE_CAVE_B2F.value
    STEVENS_ROOM = MapRSE.GRANITE_CAVE_STEVENS_ROOM.value

    def _delivered() -> bool:
        try:
            return bool(get_event_flag("DELIVERED_STEVEN_LETTER"))
        except Exception:
            return False

    def _pathable(tile: tuple[int, int]) -> bool:
        """Can the pathfinder reach `tile` on the CURRENT map from where we stand? Used to
        pick the right chain step on a floor that appears twice (split sections)."""
        try:
            cur = _map_group_number()
            pos = tuple(get_player_avatar().local_coordinates)
            calculate_path((cur, pos), (cur, tile))
            return True
        except Exception:
            return False

    def _walk_warp_chain(chain, done_check, label: str) -> Generator:
        """Walk a multi-floor warp chain: at each hop, pick the FURTHEST-ALONG chain step
        for the CURRENT map whose warp tile is actually pathable from here, enter it,
        repeat. Floors appear multiple times in a chain (their split sections are told
        apart by live reachability), and picking the FIRST pathable match loops: Granite
        Cave 1F has a ONE-WAY LEDGE from the north section down to the entrance section,
        so from (35,3) the early (17,11) ladder reads as "reachable" and a first-match
        scan rides it straight back down (live-hit: 9 hops of ping-pong). Furthest-along
        both breaks that loop and takes the player's natural ledge-jump shortcut on the
        way out. Bounded."""
        for _hop in range(len(chain) + 4):
            _check_abort()
            if done_check():
                return
            cur = _map_group_number()
            step = None
            for m_enum, tile, dest in chain:  # keep scanning — LAST match wins
                if m_enum.value == cur and _pathable(tile):
                    step = (m_enum, tile, dest)
            if step is None:
                raise BotModeError(f"{label}: no chain warp is reachable from map {cur} (lost?).")
            m_enum, tile, dest = step
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == dest or done_check(),
                m_enum,
                tile,
                label=f"{label} hop {tile}",
            )
            yield from wait_until_truly_controllable()
        if not done_check():
            raise BotModeError(f"{label}: warp chain did not reach its destination.")

    # The Granite Cave ladder chains (within-floor hops all pathfinder-verified):
    _TO_STEVEN = [
        (MapRSE.GRANITE_CAVE_1F, (17, 11), CAVE_B1F),       # 1F entrance section ↓
        (MapRSE.GRANITE_CAVE_B1F, (28, 21), CAVE_B2F),      # B1F south section ↓
        (MapRSE.GRANITE_CAVE_B2F, (29, 13), CAVE_B1F),      # B2F crossing ↑
        (MapRSE.GRANITE_CAVE_B1F, (25, 13), CAVE_1F),       # B1F north-east pocket ↑ (lands (35,3))
        (MapRSE.GRANITE_CAVE_1F, STEVENS_ROOM_DOOR_1F, STEVENS_ROOM),  # 1F north-west section
    ]
    _FROM_STEVEN = [
        (MapRSE.GRANITE_CAVE_STEVENS_ROOM, (7, 3), CAVE_1F),  # room exit (lands (5,10))
        (MapRSE.GRANITE_CAVE_1F, (35, 3), CAVE_B1F),
        (MapRSE.GRANITE_CAVE_B1F, (29, 13), CAVE_B2F),
        (MapRSE.GRANITE_CAVE_B2F, (28, 21), CAVE_B1F),
        (MapRSE.GRANITE_CAVE_B1F, (4, 21), CAVE_1F),          # lands (17,11), entrance section
        (MapRSE.GRANITE_CAVE_1F, (37, 12), ROUTE106),         # out the cave mouth
    ]

    if not _delivered():
        context.message = "Story: taking Steven's Letter to Granite Cave..."
        yield from wait_until_truly_controllable()

        # Heal first when starting from town: faithful player behavior before a cave trip,
        # and it moves the whiteout respawn to DEWFORD's Poké Center — after the first sail
        # Briney is no longer in his cottage, so respawning on the mainland would strand
        # the run (see known-issues).
        if _map_group_number() == DEWFORD:
            yield from heal_in_pokemon_center(PokemonCenter.DewfordTown)

        # --- Leg 1: Dewford → Route 106 → into Granite Cave (door (48,16)). The global
        #     navigator crosses the north connection; beach trainers are fought inline. ---
        if _map_group_number() in (DEWFORD, ROUTE106):
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() in (CAVE_1F, CAVE_B1F, CAVE_B2F, STEVENS_ROOM),
                MapRSE.ROUTE106,
                GRANITE_CAVE_DOOR_ROUTE106,
                label="Granite Cave entrance",
            )
            yield from wait_until_truly_controllable()

        # --- Leg 2: the ladder chain down-across-up to Steven's Room. ---
        if _map_group_number() in (CAVE_1F, CAVE_B1F, CAVE_B2F):
            yield from _walk_warp_chain(
                _TO_STEVEN, lambda: _map_group_number() == STEVENS_ROOM, "Granite Cave → Steven"
            )

        # --- Leg 3: talk to Steven (static at (7,8)) and hand over the Letter. ---
        if _map_group_number() != STEVENS_ROOM:
            raise BotModeError("Steven's Letter: never reached Steven's Room.")
        yield from _navigate_riding_out(MapRSE.GRANITE_CAVE_STEVENS_ROOM, STEVEN_APPROACH)
        context.emulator.press_button("Down")  # face Steven at (7,8) from (7,7)
        yield
        yield from wait_for_n_frames(4)
        frames = 0
        while not _delivered():
            _check_abort()
            context.emulator.press_button("A")
            frames += 1
            if frames > 8000:
                raise BotModeError("Steven's Letter: talked to Steven but the flag never set.")
            yield
        # Ride out his thanks + departure walk (he despawns at the end).
        yield from _wait_until_cutscene_over("B")
        context.message = "Story: delivered Steven's Letter (got TM47 Steel Wing)!"

    # --- Leg 4: back out to Dewford — the exact reverse ladder chain, then the beach. ---
    if _map_group_number() in (STEVENS_ROOM, CAVE_1F, CAVE_B1F, CAVE_B2F):
        yield from _walk_warp_chain(
            _FROM_STEVEN, lambda: _map_group_number() in (ROUTE106, DEWFORD), "Granite Cave → out"
        )
    # Finish by healing at the Dewford PC: heal_in_pokemon_center's own navigation
    # crosses the Route 106 → Dewford connection reliably (a bare navigate_to_anywhere
    # to a town tile derailed here once — live 2026-07-22), it's what a player does
    # after a cave trip, and it leaves the team topped up for the gym right after.
    yield from wait_until_truly_controllable()
    yield from heal_in_pokemon_center(PokemonCenter.DewfordTown)
    yield from wait_until_truly_controllable()
    if _map_group_number() != DEWFORD:
        raise BotModeError("Steven's Letter: expected to finish at the Dewford Poké Center.")
    context.message = "Story: back in Dewford Town."


# ---- Chapter 8a: sail Dewford → Slateport (Route 109) ----
# Static recon 2026-07-22 (ch8 probe): dock Briney = DEWFORD_TOWN local_id 2 at (12,9)
# (his boat = id 4 at (12,8)). ✓ script-verified (DewfordTown decomp): with
# FLAG_DELIVERED_STEVEN_LETTER set his dock menu is `multichoicedefault ...
# MULTI_BRINEY_ON_DEWFORD, 2` — Petalburg=0 / SLATEPORT=1 / Cancel=2, and the CURSOR
# STARTS ON 2 (Cancel), so the deterministic pick for Slateport is UP ×1 then A (the
# stock wait_for_multiple_choice_question presses Down from wherever the cursor is and
# would wrap onto Petalburg — do NOT use it here). Choosing Slateport hides the Dewford
# boat, un-hides Briney+boat on ROUTE 109 (he lands you on the beach near (21,24)), and
# Route 109 runs North straight into SLATEPORT_CITY (a long trainer-gauntlet beach).
DEWFORD_DOCK_BRINEY_LOCAL_ID = 2
# Briney stands STATIC at the Dewford dock (12,9); (11,9) is the tile beside him.
# Route from the Poké Center: (2,10) -> y=11 east to x=5 -> north to y=9 -> east.
# Never route along y=11 past x=7 (the Woman patrols (7,12)) or into the y=10 wall
# band at x=10-13, which is the pocket the old greedy walker fell into.
DEWFORD_DOCK_TALK_TILE = (11, 9)


def sail_to_slateport() -> Generator:
    """Chapter 8a — sail from the Dewford dock to Route 109 and walk into Slateport.

    INTENT: after the Letter (and the badge), the Devon Goods are still in the bag for
    Captain Stern — Slateport is the next story stop. Briney ferries us from the Dewford
    dock; he lands on Route 109's beach, which connects North directly into Slateport.
    ROUTE: (from the gym or anywhere in Dewford) → Dewford PC heal → talk to Briney at the
    dock (12,9) → his multichoice: UP ×1 → A picks SLATEPORT (index 1; cursor defaults to
    Cancel — see the recon note above) → ride out the sail → land ROUTE 109 → navigate
    North into SLATEPORT_CITY (beach trainers fought inline) → heal at the Slateport PC
    (also anchors the whiteout respawn in Slateport, same reasoning as KI-10).
    GOAL/END STATE: controllable in Slateport City, team healed.
    STORY CONDITION: `DELIVERED_STEVEN_LETTER` set (without it Briney only offers
    Petalburg). Idempotent + resume-safe: legs are keyed off the LIVE map."""
    from modules.modes.util.sleep import wait_for_n_frames as _wfn  # noqa: F401  (clarity)

    DEWFORD = MapRSE.DEWFORD_TOWN.value
    GYM = MapRSE.DEWFORD_TOWN_GYM.value
    ROUTE109 = MapRSE.ROUTE109.value
    SLATEPORT = MapRSE.SLATEPORT_CITY.value

    if _map_group_number() == SLATEPORT:
        return
    context.message = "Story: sailing from Dewford to Slateport..."
    yield from wait_until_truly_controllable()

    # --- Leg 0: step out of the gym if that's where we are (brawly_done resumes here). ---
    if _map_group_number() == GYM:
        yield from _enter_warp_by_navigation(
            lambda: _map_group_number() == DEWFORD, MapRSE.DEWFORD_TOWN_GYM, (5, 27), label="Dewford Gym exit"
        )
        yield from wait_until_truly_controllable()

    if _map_group_number() == DEWFORD:
        # Heal before the trip (fresh off the gym fight; faithful player behavior).
        yield from heal_in_pokemon_center(PokemonCenter.DewfordTown)
        yield from wait_until_truly_controllable()

        # --- Leg 1: talk to Briney at the dock and pick SLATEPORT. Briney (local_id 2)
        #     stands STATIC at (12,9) in this story state (probed live, 3600-frame
        #     observation — he does not patrol here); known_spot (11,9) parks beside him
        #     without ever crossing the townsperson patrolling the (11-13,14) row (the
        #     "erratic movement right of the gym" the user watched was the old adaptive
        #     dance fighting through exactly that walker's wall). approach_hint loads
        #     the object when approaching from across town. ---
        # Briney is STATIC at the dock (12,9) in this story state — object id 2, probed
        # live over 3600 frames and confirmed again from the ROM's object table. So walk
        # STRAIGHT to the dock and talk; there is nothing to observe or ambush here.
        # (User report, real hardware 2026-07-23: the bot was taking the scenic route
        # east of the gym and loitering by the townsfolk. It does not need to go there.)
        # The wandering-NPC procedure stays as the fallback for the case where he has
        # moved or the object hasn't loaded.
        engaged = False
        for _try in range(3):
            _check_abort()
            try:
                yield from _navigate_riding_out(MapRSE.DEWFORD_TOWN, DEWFORD_DOCK_TALK_TILE, tries=3)
            except BotModeError as error:
                reraise_if_aborting(error)  # `#24-abortrecoveryresiduals` (c) — PRE-EXISTING swallower. Latch-keyed:
                # with no whiteout pending it does nothing; with one, the unwind escapes instead of being
                # absorbed here. This handler predates `#24-loopheadabort`.
                break
            if tuple(get_player_avatar().local_coordinates) != DEWFORD_DOCK_TALK_TILE:
                continue
            yield from wait_for_player_avatar_to_be_standing_still()
            yield from ensure_facing_direction("Right")  # Briney is one tile east
            for _f in range(120):
                _check_abort()
                if get_global_script_context().is_active:
                    engaged = True
                    break
                context.emulator.press_button("A")
                yield
                yield from wait_for_n_frames(6)
            if engaged:
                break
        if not engaged:
            yield from _talk_to_wandering_npc(
                MapRSE.DEWFORD_TOWN, DEWFORD_DOCK_BRINEY_LOCAL_ID,
                approach_hint=DEWFORD_DOCK_TALK_TILE, known_spot=DEWFORD_DOCK_TALK_TILE,
            )
        presses = 0
        while _map_group_number() == DEWFORD:
            _check_abort()
            if presses > 900:
                raise BotModeError("Sail to Slateport: talked to Briney but the sail never started.")
            if task_is_active("Task_HandleMultichoiceInput"):
                # Cursor starts on Cancel (2): Up once → Slateport (1), then confirm.
                yield from wait_for_n_frames(4)
                context.emulator.press_button("Up")
                yield
                yield from wait_for_n_frames(4)
                while task_is_active("Task_HandleMultichoiceInput"):
                    context.emulator.press_button("A")
                    yield
                    yield from wait_for_n_frames(2)
                continue
            context.emulator.press_button("A")
            presses += 1
            yield
            yield from wait_for_n_frames(6)

    # --- Leg 2: ride out the sail until we're standing on Route 109. ---
    frames = 0
    while _map_group_number() not in (ROUTE109, SLATEPORT):
        _check_abort()
        context.emulator.press_button("B")
        frames += 1
        if frames > 12000:
            raise BotModeError("Sail to Slateport: never arrived on Route 109.")
        yield
    # Same arrival-dialogue hazard as the Dewford sail (see there): B-ride any open
    # post-sail script before waiting for control.
    yield from _ride_out_scripted_scene("B")
    yield from wait_until_truly_controllable()

    # --- Leg 3: Route 109 → North into Slateport (the beach is a trainer gauntlet —
    #     fought inline by the listeners; ride out anything that aborts the path). ---
    if _map_group_number() == ROUTE109:
        rounds = 0
        while _map_group_number() != SLATEPORT:
            _check_abort()
            rounds += 1
            if rounds > 20:
                raise BotModeError("Sail to Slateport: stuck crossing Route 109 into Slateport.")
            try:
                yield from navigate_to_anywhere(
                    MapRSE.SLATEPORT_CITY, (19, 21), avoid_encounters=True, avoid_scripted_events=False
                )
                break
            except BotModeError:
                yield from _ride_out_scripted_scene("B")

    # --- Leg 4: heal at the Slateport PC (respawn anchor + fresh team for the city arc). ---
    # ‼ THE RIDE-OUT LIVES IN `heal_in_pokemon_center` NOW (`#26-healnavbare`, 2026-09-11), not here.
    # A wrapper WAS added around this one call site first, and the very next batch reproduced the
    # derail 3 times — because the `(19,19)` failure is reached from `train_team`'s mid-grind heal
    # (`:2116`), not from this leg. ⇒ fixing one caller could never fix a defect that lives in the
    # helper, and keeping a second mechanism here would only imply it does something.
    yield from wait_until_truly_controllable()
    yield from heal_in_pokemon_center(PokemonCenter.SlateportCity)
    yield from wait_until_truly_controllable()
    if _map_group_number() != SLATEPORT:
        raise BotModeError("Sail to Slateport: expected to finish at the Slateport Poké Center.")
    context.message = "Story: arrived in Slateport City!"


# ---- Chapter 8b: Devon Goods → Capt. Stern (Oceanic Museum) ----
# Recon 2026-07-22 (museumprobe + decomp, all ✓ script-verified): city doors
# (30,26)/(31,26) ↔ MUSEUM_1F (9,8)/(10,8); the outside Aqua queue leaves a gap at
# (27,27) so the doors stay reachable. 1F (20×9): entrance attendants (7,7)/(12,7)
# charge ¥50 via a YES/NO (broke + goods undelivered → free entry anyway); the
# Rusturf "familiar grunt" (9,4) hands over TM46 Thief; stairs (6,1) ↔ 2F (6,1).
# 2F: CAPT. STERN at (13,6). Talking to him runs the whole beat: two BACK-TO-BACK
# un-fleeable Aqua grunt battles (TRAINER_GRUNT_MUSEUM_1/2 — the attack-through
# trainer strategy's exact case) → Archie's speech → the Goods are handed over →
# FLAG_DELIVERED_DEVON_GOODS + HealPlayerParty (the script heals us!) + Stern
# despawns + the Route 110 Aqua blockade is removed (unblocks Ch9).
MUSEUM_DOOR_CITY = (30, 26)
MUSEUM_STAIRS_1F = (6, 1)
STERN_LOCAL_ID_2F = 1
STERN_APPROACH_2F = (13, 5)   # Stern (13,6) is walled below (13,7)=collision; talk from ABOVE
STERN_FACE = "Down"           # (13,5) → face Down toward Stern
# Ch8b GATING (walkthrough + decomp-verified 2026-07-22, KI-11 resolved): the Oceanic
# Museum's outside Team Aqua crowd (hide-flag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA / 882,
# unset by default) SEALS the doors until you visit STERN'S SHIPYARD and talk to DOCK.
# `SlateportCity_SternsShipyard_1F_EventScript_Dock` (before delivery) runs
# `setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` + `FLAG_DOCK_REJECTED_DEVON_GOODS` —
# the grunts go inside, the entrance clears. Shipyard 1F door = city (26,38); Dock at (5,5).
SHIPYARD_DOOR_CITY = (26, 38)
DOCK_LOCAL_ID_1F = 1
DOCK_APPROACH_1F = (4, 5)   # Dock (5,5) is walled below (5,6)=collision; talk from his LEFT
DOCK_FACE = "Right"          # (4,5) → face Right toward Dock


def deliver_devon_goods_to_stern() -> Generator:
    """Chapter 8b — deliver the Devon Goods to Capt. Stern in the Oceanic Museum.

    INTENT: the second half of Mr. Stone's errand (the Letter was half one). This is the
    Slateport story beat: it clears the museum of Team Aqua, removes the Route 110
    blockade (required for Ch9 → Mauville), and finishes the Devon delivery questline.
    ROUTE (walkthrough + decomp-verified): Slateport → STERN'S SHIPYARD (city door
    (26,38)) → talk to DOCK (5,5): he reports Stern missing and sends the Aqua grunts into
    the museum (`setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` — the entrance-clearing step,
    KI-11) → back to the city → museum door (30,26), now unsealed → pay the ¥50 entry
    (A-through answers the YES/NO; ride-outs use A so the fee can't be declined) → 1F →
    stairs (6,1) → 2F → talk to Stern (13,6) → ride the scene (two un-fleeable grunt
    battles fought by the battle listener, Archie speech) until `DELIVERED_DEVON_GOODS` →
    back out. The scene heals the party.
    GOAL/END STATE: `DELIVERED_DEVON_GOODS` set, controllable in Slateport City.
    STORY CONDITION: Devon Goods in the bag (carried since Rusturf). Resume-safe: legs
    are keyed off the LIVE map + the grunt-clear flag."""
    from modules.memory import get_event_flag

    SLATEPORT = MapRSE.SLATEPORT_CITY.value
    SHIPYARD = MapRSE.SLATEPORT_CITY_STERNS_SHIPYARD_1F.value
    M1F = MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_1F.value
    M2F = MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_2F.value

    def _delivered() -> bool:
        try:
            return bool(get_event_flag("DELIVERED_DEVON_GOODS"))
        except Exception:
            return False

    def _grunts_cleared() -> bool:
        # The Dock visit sets this; it's what unseals the museum entrance.
        try:
            return bool(get_event_flag("HIDE_SLATEPORT_CITY_TEAM_AQUA"))
        except Exception:
            return False

    if not _delivered():
        context.message = "Story: taking the Devon Goods to Capt. Stern at the Oceanic Museum..."
        yield from wait_until_truly_controllable()

        # --- Leg 0: if the museum is still grunt-sealed, visit Stern's Shipyard and talk
        #     to Dock to clear the entrance (KI-11 sequencing). Skipped once the flag is
        #     set (idempotent / resume-safe). ---
        if not _grunts_cleared():
            if _map_group_number() == SLATEPORT:
                yield from _enter_warp_by_navigation(
                    lambda: _map_group_number() == SHIPYARD,
                    MapRSE.SLATEPORT_CITY,
                    SHIPYARD_DOOR_CITY,
                    label="Stern's Shipyard entrance",
                )
                yield from wait_until_truly_controllable()
            if _map_group_number() == SHIPYARD:
                # Dock (5,5) is a STATIONARY NPC; approach from his LEFT (4,5) and face
                # Right (he's walled below). Advance his dialogue until the grunt-clear
                # flag actually sets — the true completion signal, robust to exact facing.
                yield from _navigate_riding_out(MapRSE.SLATEPORT_CITY_STERNS_SHIPYARD_1F, DOCK_APPROACH_1F)
                context.emulator.press_button(DOCK_FACE)
                yield
                yield from wait_for_n_frames(4)
                frames = 0
                while not _grunts_cleared():
                    _check_abort()
                    context.emulator.press_button("A")
                    frames += 1
                    if frames > 4000:
                        raise BotModeError("Devon Goods: talked to Dock but the museum grunts never cleared.")
                    yield
                # Close Dock's remaining dialogue with a short bounded B-settle (a full
                # _wait_until_cutscene_over here can stall 8000f on a lingering field
                # script — derail-hit run6 2026-07-22).
                for _ in range(60):
                    if not get_global_script_context().is_active:
                        break
                    context.emulator.press_button("B")
                    yield
                # Back out to the city.
                yield from _enter_warp_by_navigation(
                    lambda: _map_group_number() == SLATEPORT,
                    MapRSE.SLATEPORT_CITY_STERNS_SHIPYARD_1F,
                    (2, 14),
                    label="Shipyard exit",
                )
                yield from wait_until_truly_controllable()

        # --- Leg 1: city → the museum's SLIDING DOORS (now unsealed). ‼ This door type is
        #     SOLID to the pathfinder (the door tile can't be a nav destination), so walk
        #     it the player way: navigate to (30,28) below the left door, then WALK UP
        #     through (30,27) into the door. (With the grunts cleared, (30,27) is free.) ---
        if _map_group_number() == SLATEPORT:
            yield from _navigate_riding_out(MapRSE.SLATEPORT_CITY, (30, 28))
            yield from wait_for_player_avatar_to_be_standing_still()
            yield from _walk_through_warp("Up", SLATEPORT, timeout_frames=360)
            yield from wait_until_truly_controllable()

        # --- Leg 2: pay the ¥50 fee + cross 1F to the 2F stairs. The fee YES/NO (and
        #     possibly the TM46 grunt scene) interrupts navigation — ride out with A
        #     (A answers YES on the default cursor; B would DECLINE the fee and bounce
        #     us out). If the stairs tile also refuses to be a path destination, fall
        #     back to walking INTO it from (6,2). ---
        if _map_group_number() == M1F:
            rounds = 0
            while _map_group_number() == M1F:
                _check_abort()
                rounds += 1
                if rounds > 8:
                    try:
                        yield from navigate_to_anywhere(
                            MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_1F, (6, 2),
                            avoid_encounters=True, avoid_scripted_events=False,
                        )
                    except BotModeError:
                        pass
                    if _map_group_number() == M1F:
                        yield from _walk_through_warp("Up", M1F)
                    break
                try:
                    yield from navigate_to_anywhere(
                        MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_1F,
                        MUSEUM_STAIRS_1F,
                        avoid_encounters=True,
                        avoid_scripted_events=False,
                    )
                except BotModeError:
                    if _map_group_number() != M1F:
                        break
                    yield from _ride_out_scripted_scene("A")
            yield from wait_until_truly_controllable()

        # --- Leg 3: 2F — talk to Stern (stationary at (13,6); approach from ABOVE (13,5)
        #     facing Down — he's walled below) and ride the whole scene (two un-fleeable
        #     grunt battles handled by the battle listener, then Archie) until the flag
        #     sets. Keyed on DELIVERED_DEVON_GOODS, robust to exact facing. ---
        if _map_group_number() != M2F:
            raise BotModeError("Devon Goods: never reached the museum's 2F.")
        yield from _navigate_riding_out(MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_2F, STERN_APPROACH_2F)
        context.emulator.press_button(STERN_FACE)
        yield
        yield from wait_for_n_frames(4)
        frames = 0
        while not _delivered():
            _check_abort()  # a lost grunt battle whites out → recovery re-enters here
            context.emulator.press_button("B" if frames % 3 else "A")
            frames += 1
            if frames > 30000:
                raise BotModeError("Devon Goods: the Stern scene never set DELIVERED_DEVON_GOODS.")
            yield
        yield from _wait_until_cutscene_over("B")
        context.message = "Story: Devon Goods delivered — Slateport's museum is Aqua-free (party healed by the scene)!"

    # --- Leg 4: back out to the city (2F → 1F → doors), with walk-into fallbacks for
    #     the same solid-to-pathfinding door/stair tiles as on the way in. ---
    if _map_group_number() == M2F:
        try:
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == M1F,
                MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_2F,
                (6, 1),
                tries=3,
                label="Museum 2F stairs down",
            )
        except BotModeError as error:
            # ‼ `#24-abortrecoveryresiduals` (b). This fallback used to swallow a whiteout unwind. It was
            # correct only BY ACCIDENT — the call below happens to re-raise — and accidental correctness is
            # what this project's KI-67/KI-81 family is made of. `reraise_if_aborting` is LATCH-keyed, so
            # with no whiteout pending it changes nothing at all.
            reraise_if_aborting(error)
            yield from _navigate_riding_out(MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_2F, (6, 2))
            yield from _walk_through_warp("Up", M2F)
    if _map_group_number() == M1F:
        try:
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == SLATEPORT,
                MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_1F,
                (9, 8),
                tries=3,
                label="Museum exit",
            )
        except BotModeError as error:
            # ‼ `#24-abortrecoveryresiduals` (b). This fallback used to swallow a whiteout unwind. It was
            # correct only BY ACCIDENT — the call below happens to re-raise — and accidental correctness is
            # what this project's KI-67/KI-81 family is made of. `reraise_if_aborting` is LATCH-keyed, so
            # with no whiteout pending it changes nothing at all.
            reraise_if_aborting(error)
            yield from _navigate_riding_out(MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_1F, (9, 7))
            yield from _walk_through_warp("Down", M1F)
    yield from wait_until_truly_controllable()
    context.message = "Story: back on the Slateport streets."


# ---- Chapter 9: Route 110 → Mauville → Gym 3 (Wattson) ----
# Recon 2026-07-22 (§Ch9, probes + decomp + verified external research): the RIVAL
# trigger row is ROUTE110 (33,56)/(34,56)/(35,56), armed while VAR_ROUTE110_STATE==0;
# winning sets state=1 + FLAG_RECEIVED_ITEMFINDER (+DEFEATED_RIVAL_ROUTE_110). Post-
# rival BIRCH scene triggers arm at (7-10,85) for state==1 (west path — ride-outs
# handle it if crossed). Mauville: WALLY (8,6) + uncle (9,6) flank the GYM DOOR (8,5);
# talking to Wally forces TRAINER_WALLY_MAUVILLE (Ralts ~L16) → FLAG_DEFEATED_WALLY_
# MAUVILLE + the Scott scene. The gym (10×21): Wattson at (5,2); FLOOR SWITCHES at
# (0,15)/(4,12)/(3,9)/(8,9) toggle the electric barriers — the barriers ARE collision
# and change live, so the puzzle is solved ADAPTIVELY (try Wattson; else step the
# nearest reachable unvisited switch; re-plan). Win → FLAG_BADGE03_GET (+TM34).
ROUTE110_RIVAL_STAGING = (34, 57)      # just south of the trigger row; step Up to arm it
MAUVILLE_WALLY_APPROACH = (8, 7)       # below Wally (8,6); face Up to talk
# Route 117's south-central grass field — the ONLY grass two-way pathable from the
# Mauville-side road (full 162-tile sweep from entry tile (55,6), 2026-07-22). The
# northern strips ((51,1) etc.) sit on a ledge shelf the road can't return from, and
# Route 110's grass is Cycling-Road-walled / ledge-one-way — runs 11-13 each burned
# all navigation retries plan-failing before this was swept properly. Prevention rule:
# training tiles must be probed for TWO-WAY pathability FROM THE REAL ENTRY TILE.
ROUTE117_TRAINING_GRASS = (MapRSE.ROUTE117, (31, 16))
# Ch12 (Norman): Route 102's west grass — two-way swept from the Petalburg PC door
# (20,16) 2026-07-24 (ch12 recon). Wilds are L3-4 fodder; the boss-training mode's
# KO-telemetry logic is expected to carry the real levelling (Norman re-attempts).
PETALBURG_TRAINING_GRASS = (MapRSE.ROUTE102, (9, 2))
MAUVILLE_GYM_DOOR_CITY = (8, 5)        # city door → gym (4-5,20)
MAUVILLE_GYM_SWITCHES = [(0, 15), (4, 12), (3, 9), (8, 9)]
MAUVILLE_GYM_WATTSON_APPROACH = (5, 3)  # below Wattson (5,2)


def route110_rival_beaten() -> bool:
    """Decomp-truth completion signal for the Route 110 rival (validated 2026-07-22):
    Route110_EventScript_RivalExit runs `setvar VAR_ROUTE110_STATE, 1` and that is the
    ONLY durable signal — vanilla sets NO named event flag for this battle.
    (FLAG_DEFEATED_RIVAL_ROUTE_110 does not exist in the flag table; get_event_flag
    silently returns False for unknown names, and that phantom name is exactly how
    Ch9a's guard could never pass — run 5 derail-looped to Manual on it.)
    Majority-of-3 read: save-block reads resolve the moving gSaveBlock1Ptr per call
    and can TEAR around battle/map transitions (single-frame flag/var flickers were
    observed in the logs), so one read is never trusted alone."""
    from modules.memory import get_event_var

    votes = 0
    for _ in range(3):
        try:
            if get_event_var("ROUTE110_STATE") >= 1:
                votes += 1
        except Exception:
            pass
    return votes >= 2


def travel_route110_and_fight_rival() -> Generator:
    """Chapter 9a — walk Route 110 north from Slateport and beat the rival.

    INTENT: the mandatory Route 110 rival choke-point; winning is what advances
    VAR_ROUTE110_STATE (clearing the road) and awards the Itemfinder.
    HOW: Slateport → north connection → the east dirt path to the staging tile (34,57)
    → step UP into the 3-tile trigger row → the rival scene runs (bike entrance,
    dialogue) → the battle is fought by the listener (caller preps lead/heal) → ride
    the aftermath (Itemfinder gift) until VAR_ROUTE110_STATE ≥ 1.
    GOAL/END: route110_rival_beaten() (VAR_ROUTE110_STATE ≥ 1); controllable on Route 110."""
    ROUTE110 = MapRSE.ROUTE110.value

    if route110_rival_beaten():
        return
    context.message = "Story: heading up Route 110 — the rival is waiting..."
    yield from wait_until_truly_controllable()
    yield from _navigate_riding_out(MapRSE.ROUTE110, ROUTE110_RIVAL_STAGING)
    yield from wait_for_player_avatar_to_be_standing_still()
    # Step up into the trigger row and ride the whole scene + battle + aftermath.
    # The exit demands a 5-frame streak: this loop polls tens of thousands of times,
    # so a single torn read WILL eventually flip a one-shot check (run 5 "won" the
    # rival without ever fighting him that way).
    frames = 0
    beaten_streak = 0
    while beaten_streak < 5:
        beaten_streak = beaten_streak + 1 if route110_rival_beaten() else 0
        _check_abort()  # a loss whites out → recovery re-enters (segment attempt-cap)
        if frames % 8 == 0 and not get_global_script_context().is_active:
            context.emulator.press_button("Up")
        else:
            context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 30000:
            raise BotModeError("Route 110: the rival battle never resolved.")
        yield
    yield from _wait_until_cutscene_over("B")
    # The rival aftermath also chains (Itemfinder gift → dialogue tails) — ride it all.
    yield from _ride_out_all_scenes()
    context.message = "Story: beat the rival on Route 110 (got the Itemfinder)!"


def fight_wally_mauville() -> Generator:
    """Chapter 9b — Mauville: Wally's battle unblocks the gym door.

    Wally + his uncle physically flank the gym entrance; talking to Wally forces the
    (single Ralts ~L16) battle. Winning sets FLAG_DEFEATED_WALLY_MAUVILLE, they leave,
    and Scott's walk-up scene plays — all ridden out on the completion flag."""
    from modules.memory import get_event_flag

    def _done() -> bool:
        try:
            return bool(get_event_flag("DEFEATED_WALLY_MAUVILLE"))
        except Exception:
            return False

    if _done():
        return
    context.message = "Story: Wally wants a battle at the Mauville Gym door..."
    yield from wait_until_truly_controllable()
    yield from _navigate_riding_out(MapRSE.MAUVILLE_CITY, MAUVILLE_WALLY_APPROACH)
    context.emulator.press_button("Up")  # face Wally at (8,6)
    yield
    yield from wait_for_n_frames(4)
    #: ⛔ PHASE OFFSET — an EXPERIMENT HOOK, not a feature (`#24-wallydecline`, 2026-09-13).
    #: The decline below is PHASE-LOCKED, not random, so a single run proves nothing: whichever
    #: of A/B lands on the frame the yes/no reads input lands there for the WHOLE run. This lets
    #: `probe_wally_phase_sweep.py` walk the phase and show the bug is unreachable at EVERY
    #: offset, instead of "it passed once". Unset in production ⇒ 0 ⇒ byte-identical behaviour.
    frames = _int_env("POKEBOT_WALLY_PHASE", 0)
    while not _done():
        _check_abort()
        button = "B" if frames % 3 else "A"
        # ⛔⛔ NEVER PRESS B WHILE A YES/NO IS OPEN — B *IS* "NO" (`#24-wallydecline`, 2026-09-13).
        # `src/script_menu.c Task_HandleYesNoInput`: `case MENU_B_PRESSED:` FALLS THROUGH to
        # `gSpecialVar_Result = 0`, i.e. NO. This loop mashed B on 2 of every 3 frames straight
        # into `msgbox MauvilleCity_Text_WallyWillYouBattleMe, MSGBOX_YESNO`.
        # ‼ AND DECLINING IS NOT A RETRYABLE MISTAKE — IT IS TERMINAL FOR THE RUN:
        #   · `DeclineWallyBattle` sets FLAG_DECLINED_WALLY_BATTLE_MAUVILLE, which **nothing in
        #     the decomp ever clears** (one `setflag`, two `goto_if_set`, zero `clearflag`);
        #   · every later talk then routes to `WallyRequestBattleAgain` → the SAME yes/no → the
        #     same locked phase → NO again. A fixed point, not a race we eventually win;
        #   · Wally is `removeobject`'d ONLY on the win path, and he stands on **(8,6) — the one
        #     tile the gym door (8,5) can be entered from** ((7,5)/(9,5) are collision-1 wall).
        #   ⇒ no Wally → no Wattson → no BADGE03 → `EventScript_CantSmashRock` → Route 111 and
        #     Rusturf Tunnel never open. MEASURED: 124 of 143 ended runs died here, and every one
        #     of those 124 sat on the SAME final state (`DeclineWallyBattle` + `Std_MsgboxDefault`,
        #     held_buttons=[]). Runs that reached the door: 12% got past it.
        # ⭐ The cursor defaults to YES (`DisplayYesNoMenuDefaultYes`), so A alone accepts. We keep
        # the A/B alternation because B is what safely ADVANCES the three plain msgboxes without
        # re-initiating the conversation — we only refuse to let B answer the CHOICE.
        # FAULT ARMS live HERE, in production, never in the driver — a fix demonstrated only by
        # driver-side code is not demonstrated at all (playbook §0c).
        #   `=mash`    restore the pre-fix blind masher (phase-locked; may or may not decline).
        #   `=decline` FORCE B at the choice box, i.e. deliberately answer NO.
        # ‼ WHY `decline` EXISTS AND `mash` WAS NOT ENOUGH — MEASURED 2026-09-13. `mash` is a
        # PHASE-LOCKED arm, and on a fixture parked near Wally it declined at NO swept phase
        # (all 3 phases × both arms: 6/6 beat him). The offset cannot reach the bug there because consecutive
        # identical presses cancel in `libmgba.press_button`, so a cycle emits `A, B, nothing`,
        # and shifting the phase ALSO shifts how fast the three msgboxes advance — the box's open
        # frame co-moves and the offset partly cancels itself. ⇒ an arm whose firing depends on
        # luck is not an arm. `decline` fires deterministically and answers the actual causal
        # question: *does a B at this box produce the terminal state 124/124 dead runs sat on?*
        fault = os.environ.get("POKEBOT_WALLY_FAULT", "")
        if _yes_no_menu_is_open():
            if fault == "decline":
                button = "B"          # ARM ONLY — must reproduce the run-killing decline
            elif fault != "mash":
                button = "A"          # ⭐ THE FIX — never let B answer the choice
        context.emulator.press_button(button)
        frames += 1
        if frames > 30000:
            raise BotModeError("Mauville: the Wally battle never resolved.")
        yield
    # Ride out the WHOLE aftermath chain (defeat text → uncle → exit walk → Scott's
    # approach → any registration) until the field stays quiet — a single ride returns
    # in a between-parts pause and the leak killed run 11's training navigation.
    yield from _wait_until_cutscene_over("B")
    yield from _ride_out_all_scenes()
    context.message = "Story: beat Wally — the gym door is clear!"


def do_mauville_gym() -> Generator:
    """Chapter 9c — Mauville Gym: solve the switch puzzle, beat Wattson (Dynamo Badge).

    The electric barriers ARE collision and TOGGLE when a floor switch is stepped on
    (coord_events — walking over them fires; no A needed), so the maze is solved
    ADAPTIVELY: try to path to Wattson's approach tile; when no path exists, step the
    nearest reachable un-stepped switch (which re-shapes the maze) and re-plan. Gym
    trainers en route are fought inline. Then face Up + A to Wattson until BADGE03."""
    from modules.memory import get_event_flag
    from modules.map import get_map_data
    from modules.map_path import calculate_path

    GYM = MapRSE.MAUVILLE_CITY_GYM.value

    if get_event_flag("BADGE03_GET"):
        return
    context.message = "Story: entering Mauville Gym to challenge Wattson..."
    yield from wait_until_truly_controllable()
    # Enter via the city door (walk-in door type unknown — try navigation-entry with the
    # walk-into fallback, the museum pattern).
    if _map_group_number() != GYM:
        try:
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == GYM, MapRSE.MAUVILLE_CITY, MAUVILLE_GYM_DOOR_CITY,
                tries=4, label="Mauville Gym door",
            )
        except BotModeError as error:
            # ‼ `#24-abortrecoveryresiduals` (b). This fallback used to swallow a whiteout unwind. It was
            # correct only BY ACCIDENT — the call below happens to re-raise — and accidental correctness is
            # what this project's KI-67/KI-81 family is made of. `reraise_if_aborting` is LATCH-keyed, so
            # with no whiteout pending it changes nothing at all.
            reraise_if_aborting(error)
            yield from _navigate_riding_out(MapRSE.MAUVILLE_CITY, (8, 6))
            yield from _walk_through_warp("Up", MapRSE.MAUVILLE_CITY.value)
        yield from wait_until_truly_controllable()

    # MAZE MECHANICS (decomp + live probes, 2026-07-22 — hard-won): there are exactly TWO
    # barrier configurations — FLAG_MAUVILLE_GYM_BARRIERS_STATE flips on every switch
    # press, and a switch only fires if it is NOT the last one pressed
    # (VAR_MAUVILLE_GYM_STATE remembers that). CRITICALLY, the toggled beams exist ONLY
    # in the engine's LIVE grid (gBackupMapLayout, rewritten by setmetatile): our
    # get_map_data/calculate_path read the ROM's STATIC default layout and are blind to
    # every toggle — a "pathable" static plan walks the player into a live beam and bumps
    # forever (runs 6-9; proven by a live-vs-static grid diff plus a held-Up test on the
    # captured wedge state saves/mauville_wedge.ss1). So inside the maze the solver
    # trusts ONLY the live grid: it snapshots the live passable set under each flag
    # state it sees, BFS-plans over the combined (tile, config, last-switch) graph
    # (stepping a switch mid-route IS the plan), and walks each leg itself with held
    # directions judged by arrival.
    from collections import deque
    from modules.map import get_map_objects
    from modules.memory import get_event_var, read_symbol, unpack_uint32, get_game_state, GameState

    W, H = get_map_data(GYM, (0, 0)).map_size
    switch_tiles = {i + 1: tuple(t) for i, t in enumerate(MAUVILLE_GYM_SWITCHES)}
    tile_to_switch = {v: k for k, v in switch_tiles.items()}
    layers: dict = {}
    rounds = 0

    def _flag_state() -> bool:
        try:
            return bool(get_event_flag("MAUVILLE_GYM_BARRIERS_STATE"))
        except Exception:
            return False

    def _last_switch() -> int:
        try:
            return int(get_event_var("MAUVILLE_GYM_STATE"))
        except Exception:
            return 0

    def _live_passable() -> frozenset:
        """The ENGINE's current walkability (gBackupMapLayout) — the only truthful
        source for this map. Valid only while the gym is the loaded map."""
        raw = read_symbol("gBackupMapLayout")
        grid_w = int.from_bytes(raw[0:4], "little", signed=True)
        grid_h = int.from_bytes(raw[4:8], "little", signed=True)
        map_ptr = unpack_uint32(raw[8:12])
        data = context.emulator.read_bytes(map_ptr, grid_w * grid_h * 2)
        out = set()
        for y in range(H):
            base = (y + 7) * grid_w
            for x in range(W):
                v = int.from_bytes(data[(base + x + 7) * 2 : (base + x + 7) * 2 + 2], "little")
                if (v >> 10) & 3 == 0:
                    out.add((x, y))
        return frozenset(out)

    def _object_tiles() -> frozenset:
        try:
            me = tuple(get_player_avatar().local_coordinates)
            tiles = set()
            for o in get_map_objects():
                for c in (getattr(o, "current_coords", None), getattr(o, "previous_coords", None)):
                    if c is not None and tuple(c) != me:
                        tiles.add(tuple(c))
            return frozenset(tiles)
        except Exception:
            return frozenset()

    def _plan_tiles():
        """Full BFS over (tile, config, last_switch) on the LEARNED live layers;
        returns the complete tile path to the Wattson approach, or None."""
        if len(layers) < 2:
            return None
        blocked = _object_tiles()
        start = (tuple(get_player_avatar().local_coordinates), _flag_state(), _last_switch())
        prev = {start: None}
        queue = deque([start])
        found = None
        while queue:
            node = queue.popleft()
            if node[0] == MAUVILLE_GYM_WATTSON_APPROACH:
                found = node
                break
            (x, y), fl, last = node
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nxy = (x + dx, y + dy)
                if nxy in layers.get(fl, frozenset()) and nxy not in blocked:
                    sw = tile_to_switch.get(nxy)
                    nb = (nxy, not fl, sw) if (sw is not None and sw != last) else (nxy, fl, last)
                    if nb not in prev:
                        prev[nb] = node
                        queue.append(nb)
        if found is None:
            return None
        tiles = []
        node = found
        while node is not None:
            tiles.append(node[0])
            node = prev[node]
        tiles.reverse()
        return tiles[1:]  # drop the start tile

    def _single_layer_path(target) -> list | None:
        """BFS a tile path within the CURRENT live config only."""
        passable = layers.get(_flag_state(), frozenset())
        blocked = _object_tiles()
        start = tuple(get_player_avatar().local_coordinates)
        prev = {start: None}
        queue = deque([start])
        found = None
        while queue:
            t = queue.popleft()
            if t == tuple(target):
                found = t
                break
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                n = (t[0] + dx, t[1] + dy)
                if n in passable and n not in blocked and n not in prev:
                    prev[n] = t
                    queue.append(n)
        if found is None:
            return None
        tiles = []
        while found is not None:
            tiles.append(found)
            found = prev[found]
        tiles.reverse()
        return tiles[1:]

    def _walk_tiles(tiles) -> Generator:
        """Walk a BFS tile path with held directions, judged by arrival. Returns True
        if the whole path was walked; False on any interruption (battle, script,
        blocked step) — the caller re-reads the live grid and re-plans."""
        for nxt in tiles:
            px, py = get_player_avatar().local_coordinates
            d = (nxt[0] - px, nxt[1] - py)
            button = {(0, -1): "Up", (0, 1): "Down", (-1, 0): "Left", (1, 0): "Right"}.get(d)
            if button is None:
                context.emulator.reset_held_buttons()
                return False  # drifted off-path (battle knock-on) — re-plan
            arrived = False
            for _ in range(120):
                if get_game_state() is not GameState.OVERWORLD or get_global_script_context().is_active:
                    context.emulator.reset_held_buttons()
                    return False  # trainer battle / switch script — handled outside
                context.emulator.hold_button(button)
                yield
                if tuple(get_player_avatar().local_coordinates) == tuple(nxt):
                    arrived = True
                    break
            context.emulator.reset_held_buttons()
            if not arrived:
                return False  # live wall where the plan expected floor — re-learn
        return True

    def _at(tile) -> bool:
        try:
            return tuple(get_player_avatar().local_coordinates) == tuple(tile)
        except Exception:
            return False

    while not get_event_flag("BADGE03_GET"):
        _check_abort()
        rounds += 1
        if rounds > 60:
            raise BotModeError("Mauville Gym: could not solve the switch maze to reach Wattson.")
        if _map_group_number() != GYM:
            raise BotModeError("Mauville Gym: left the gym mid-maze — segment retry will re-enter.")
        # A battle/scene may still be winding down from the previous leg.
        if get_global_script_context().is_active:
            yield from _ride_out_scripted_scene("B")
        yield from wait_until_truly_controllable()

        layers[_flag_state()] = _live_passable()  # learn/refresh the current config

        path = _plan_tiles()
        if path is not None:
            context.message = "Story: Mauville maze — walking the planned solve..."
        else:
            wattson_leg = _single_layer_path(MAUVILLE_GYM_WATTSON_APPROACH)
            if wattson_leg is not None:
                path = wattson_leg
                context.message = "Story: Mauville maze — path to Wattson is open..."
            else:
                # Still learning: step a reachable switch that isn't the last-pressed
                # one — any press flips the maze and teaches us the other config.
                last = _last_switch()
                legs = []
                for i, t in switch_tiles.items():
                    if i == last:
                        continue
                    leg = _single_layer_path(t)
                    if leg is not None:
                        legs.append(leg)
                if not legs:
                    yield from wait_for_n_frames(30)
                    continue
                path = min(legs, key=len)
                context.message = f"Story: Mauville maze — flipping the switch at {path[-1]}..."

        yield from _walk_tiles(path)
        yield from _ride_out_scripted_scene("B")  # switch press script (sound + redraw)

        if _at(MAUVILLE_GYM_WATTSON_APPROACH):
            # Challenge Wattson: face Up + A/B ride until the badge.
            context.emulator.press_button("Up")
            yield
            frames = 0
            while not get_event_flag("BADGE03_GET"):
                _check_abort()
                context.emulator.press_button("B" if frames % 3 else "A")
                frames += 1
                if frames > 40000:
                    raise BotModeError("Mauville Gym: the Wattson challenge never resolved to a badge.")
                yield
            break
    yield from _wait_until_cutscene_over("B")
    context.message = "Story: DYNAMO BADGE earned — Gym 3 (Wattson) beaten!"


# ---------------------------------------------------------------------------
# Chapter 10 — Mauville → Fallarbor (HM06 Rock Smash → Route 111 south →
# Route 112 → Fiery Path → Route 113). Route spec: design doc §Ch10 (decomp-
# verified map.json sweep 2026-07-22).
# ---------------------------------------------------------------------------

MAUVILLE_ROCKSMASH_HOUSE_DOOR = (32, 14)  # city door → MAUVILLE_CITY_HOUSE1 (10,2)


def _exit_mauville_gym_live() -> Generator:
    """Leave the Mauville Gym on the LIVE grid. Post-badge the game deactivates the
    barrier puzzle in the LIVE map only (MauvilleGymDeactivatePuzzle) — the ROM's
    static layout still shows the maze sealed, so the static planner can't path from
    Wattson's platform to the door (Ch10a run 1: 'no path (5,3) → (4,20)'). Same
    static-vs-live rule as the maze solve. A no-op when not inside the gym."""
    from collections import deque

    from modules.map import get_map_data
    from modules.memory import read_symbol, unpack_uint32

    GYM = MapRSE.MAUVILLE_CITY_GYM.value
    if _map_group_number() != GYM:
        return
    W, H = get_map_data(GYM, (0, 0)).map_size
    raw = read_symbol("gBackupMapLayout")
    grid_w = int.from_bytes(raw[0:4], "little", signed=True)
    map_ptr = unpack_uint32(raw[8:12])
    data = context.emulator.read_bytes(map_ptr, grid_w * (H + 15) * 2)
    passable = set()
    for y in range(H):
        base = (y + 7) * grid_w
        for x in range(W):
            v = int.from_bytes(data[(base + x + 7) * 2 : (base + x + 7) * 2 + 2], "little")
            if (v >> 10) & 3 == 0:
                passable.add((x, y))
    start = tuple(get_player_avatar().local_coordinates)
    # Objects (Wattson, gym trainers) are walls too — run 2 walked into one.
    try:
        from modules.map import get_map_objects

        for o in get_map_objects():
            for c in (getattr(o, "current_coords", None), getattr(o, "previous_coords", None)):
                if c is not None and tuple(c) != start:
                    passable.discard(tuple(c))
    except Exception:
        pass
    targets = {(4, 19), (5, 19)}  # just above the entrance warp row (4,20)/(5,20)
    prev = {start: None}
    queue = deque([start])
    found = None
    while queue:
        t = queue.popleft()
        if t in targets:
            found = t
            break
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            n = (t[0] + dx, t[1] + dy)
            if n in passable and n not in prev:
                prev[n] = t
                queue.append(n)
    if found is None:
        raise BotModeError("Mauville Gym exit: no live path to the door.")
    tiles = []
    node = found
    while node is not None:
        tiles.append(node)
        node = prev[node]
    tiles.reverse()
    for nxt in tiles[1:]:
        px, py = get_player_avatar().local_coordinates
        d = {(0, -1): "Up", (0, 1): "Down", (-1, 0): "Left", (1, 0): "Right"}.get((nxt[0] - px, nxt[1] - py))
        if d is None:
            raise BotModeError("Mauville Gym exit: drifted off the live path.")
        arrived = False
        for _ in range(120):
            _check_abort()
            context.emulator.hold_button(d)
            yield
            if tuple(get_player_avatar().local_coordinates) == tuple(nxt):
                arrived = True
                break
        context.emulator.reset_held_buttons()
        if not arrived:
            raise BotModeError("Mauville Gym exit: a live wall blocked the doorward walk.")
    yield from _walk_through_warp("Down", GYM)
    yield from wait_until_truly_controllable()


def _exit_small_interior() -> Generator:
    """Exit a one-room interior (house/shop) through its bottom-edge door warp:
    navigate to the tile ABOVE a warp, then step Down through it. Generic — reads
    the current map's warps live; a no-op if already outside gets handled by the
    caller checking the map first."""
    from modules.map import get_map_data_for_current_position

    cur = _map_group_number()
    md = get_map_data_for_current_position()
    warps = sorted(
        (tuple(w.local_coordinates) for w in md.warps),
        key=lambda t: -t[1],  # bottom-most first (interior exits sit on the south edge)
    )
    for wx, wy in warps:
        _check_abort()
        if _map_group_number() != cur:
            return
        try:
            yield from navigate_to(cur, (wx, wy - 1))
            yield from _walk_through_warp("Down", cur, timeout_frames=180)
        except Exception:
            continue
    if _map_group_number() == cur:
        raise BotModeError("Could not exit the interior through any of its door warps.")


# --- HM learner selection + acquisition (user directive 2026-07-23) ----------------
# The Ch10b mule used to be "the highest-level mon", which loops in the teach menu the
# moment the top mon can't learn the HM (the party menu just says NOT ABLE). The party
# must be VALIDATED for compatibility first, and when nobody qualifies the bot must
# know which accessible wild species can learn the move and go catch one. This is the
# seed of the future HM-slave logic (#24-hm-slaves).

# Species dex numbers the story's catch branch should catch ON SIGHT right now (an
# HM-learner hunt in progress). Read by StoryMode.on_battle_started; empty = inactive.
HM_CATCH_TARGET_DEX: set[int] = set()


def hm_learner_slot(item) -> int | None:
    """The party slot best suited to learn `item`'s HM/TM move: prefers a mon that
    ALREADY knows it (idempotent re-runs), else the highest-level compatible mon.
    None if nobody in the party can learn it."""
    move = item.tm_hm_move()
    best, best_level = None, -1
    for i, mon in enumerate(get_party()):
        if mon is None or mon.is_egg:
            continue
        if move is not None and any(
            l is not None and l.move.name == move.name for l in mon.moves
        ):
            return i
        if mon.species.can_learn_tm_hm(item) and mon.level > best_level:
            best, best_level = i, mon.level
    return best


def whiteout_budget(recoveries, last_key, key, cap=40):
    """PURE. Advance the whiteout budget, resetting it when the run has MOVED ON.

    Returns `(new_recoveries, should_stop, reset)`.

    ⛔⛔ WHY THIS EXISTS — `#24-whiteoutloop`, the batch's #1 failure class (14 of 53 ended runs, 26%).
    `recoveries` was a LIFETIME total with **no reset site anywhere** — five references in a 4,500-line
    file: init, increment, log, cap, message — while its own error text said *"too many whiteout
    recoveries IN A ROW"*. It described behaviour the code did not implement.

    **MEASURED over `x4-runs/20260907-113851`, all 14 killed runs, recomputed locally:**
        every killed run reached exactly recovery #41 (the `> 40` cap)
        distinct respawn maps per killed run : median 13
        TERMINAL same-location streak        : median 2.5, max 20, min 1
        longest same-location streak ANYWHERE: max 20  (the cap is 40)
        ⇒ keying the budget to CONSECUTIVE whiteouts at one location would have saved 14 of 14.
    One run hit #41 after a SINGLE whiteout at its terminal location; its other 40 were spread over a
    dozen towns. Killed runs were winning 86-96% of their battles, one of them 866 of 907 with an L51
    lead. ⇒ **it was a fuse on run LENGTH, not a diagnosis.** `MAX_FRAMES_PER_RUN` (5,000,000) is the
    real length backstop and was never reached by ANY of the 61 runs.

    ⛔⛔ THE TRAP THIS FUNCTION EXISTS TO AVOID — DO NOT "SIMPLIFY" IT TO USE `_progress_sig()`.
    The sibling `_derails` counter resets on `_progress_sig()` change and it is tempting to mirror it
    sixty lines away. `_progress_sig()` is `(party_size, lead_level, total_exp)`. Between whiteout N
    and N+1 the bot walks back to the fight through wild grass, so **`total_exp` ALWAYS grows** — the
    reset would fire every single time and SILENTLY DELETE THE GUARD. `_progress_sig` is correct for
    derails (which fire in bursts with no battles between) and wrong for whiteouts.

    ‼ THE SAFETY DIRECTION IS DELIBERATE, AND IT IS WHY `None` DOES NOT RESET. A genuinely stuck run
    whites out at the SAME Poké Center every time, so its streak still climbs to 41 and it is still
    stopped — the guard survives, it just stops firing on runs that are winning. If the location is
    unreadable we do NOT reset: the counter keeps climbing, i.e. an unreadable position makes the
    guard STRICTER, never laxer. Being wrong in that direction is safe; the other way is a hang.
    """
    if key is not None and last_key is not None and key != last_key:
        return 1, 1 > cap, True
    return recoveries + 1, recoveries + 1 > cap, False


def pick_land_hm_slot(party, item, hm07, default_slot):
    """PURE. Which slot should learn a LAND HM, preferring a mon that cannot carry HM07?

    `party` is a sequence of mon-likes (or None); `item`/`hm07` are Items; `default_slot` is what
    `hm_learner_slot(item)` already chose. Returns a slot index, or `default_slot` unchanged.

    ⭐⭐ WHY THIS EXISTS — `#24-hm07funnel`, and the reason is in the DATA, not in a preference.
    Derived over all 412 species in `modules/data/species.json`: **101 species can learn Surf, 74 can
    learn Waterfall, 76 can learn Dive — and ZERO Waterfall- or Dive-capable species are
    Surf-incapable.** Both pools are strict SUBSETS of Surf's. ⇒ the highest-level Surf learner is
    ALWAYS also the Dive and Waterfall candidate, so `hm_learner_slot`'s level ranking hands that one
    mon every HM it is offered.
    On a Mudkip line that mon is the ONLY Waterfall carrier (6 of 6 measured 8-badge parties), so it
    MUST hold Surf + Dive + Waterfall = 3 of 4 slots. Adding both land HMs makes five HMs for four
    slots, and Waterfall — acquired last, in §Ch21 — is the one left out. HMs cannot be forgotten in
    Gen 3 (see `teach_hm_move`), so the ONLY moment this can be prevented is the original teach.
    MEASURED in the live batch: 27 "teaching Strength to Swampert" against 5 Blaziken and 3 Breloom.

    ‼ PREFERENCE, NOT A REQUIREMENT. If no incapable learner exists the default stands, so a party is
    never left worse off than today — the change can only ever move a land HM OFF the water mon.
    ⛔ Never used for Surf or Dive: those MUST go to the water mon, and `hm_learner_slot` keeps them.
    """
    if default_slot is None or item is None or hm07 is None:
        return default_slot
    # ‼ IDEMPOTENCE FIRST. If the default already knows this move, re-picking would teach it twice
    # and burn a second slot — the exact waste this function exists to prevent.
    move = item.tm_hm_move()
    try:
        cur = party[default_slot]
    except Exception:  # noqa: BLE001 - an unindexable party is not a reason to re-pick blindly.
        return default_slot
    if cur is not None and move is not None and any(
        l is not None and l.move.name == move.name for l in cur.moves
    ):
        return default_slot

    best, best_level = None, -1
    for i, mon in enumerate(party):
        if mon is None or getattr(mon, "is_egg", False):
            continue
        try:
            if not mon.species.can_learn_tm_hm(item):
                continue
            if mon.species.can_learn_tm_hm(hm07):
                continue          # this one is a Waterfall carrier — leave its slots alone
            if mon.level > best_level:
                best, best_level = i, mon.level
        except Exception:  # noqa: BLE001 - an unreadable mon is simply not a candidate.
            continue
    return best if best is not None else default_slot


def land_hm_learner_slot(item) -> int | None:
    """`hm_learner_slot`, but for a LAND HM: prefer a learner that cannot also carry HM07.

    ⛔ THIN WRAPPER ON PURPOSE. Everything decidable lives in `pick_land_hm_slot`, which is pure and
    therefore reachable by a test; this half only fetches world state. `get_item_by_name` reads the
    static item TABLE (`modules/items.py:529-530`), NOT the bag — verified — so this works at
    Segment 10b, long before HM07 is obtained in §Ch21.
    """
    from modules.items import get_item_by_name

    try:
        hm07 = get_item_by_name("HM07")
    except Exception:  # noqa: BLE001 - if HM07 cannot be resolved, behave exactly as today.
        hm07 = None
    return pick_land_hm_slot(get_party(), item, hm07, hm_learner_slot(item))


def _hm_hunting_grounds(item) -> list[tuple]:
    """Training-grass areas whose LAND encounter table contains at least one species
    that can learn `item`'s move — fully data-driven (ROM encounter tables + the
    per-species TM/HM learnsets), so it stays correct for every future HM. Returns
    [(map_enum, spin_tile, [species names]), ...] in TRAINING_GRASS order (all entries
    there are two-way swept — the standing prevention rule)."""
    from modules.map import get_wild_encounters_for_map
    from modules.story.training_areas import TRAINING_GRASS

    grounds = []
    for map_enum, tile, _band in TRAINING_GRASS:
        if tile is None:
            continue
        try:
            enc = get_wild_encounters_for_map(*map_enum.value)
        except Exception:
            continue
        if enc is None:
            continue
        names = sorted(
            {
                e.species.name
                for e in enc.land_encounters
                if e.species is not None and e.species.can_learn_tm_hm(item)
            }
        )
        if names:
            grounds.append((map_enum, tile, names))
    return grounds


def ensure_hm_learner(item) -> Generator:
    """Return a party slot that can learn `item`'s move, CATCHING a compatible wild
    if the current party has none: provision balls, walk to the nearest swept grass
    hosting a learner species, and spin with the catch branch targeting exactly those
    species until one joins the party. Bounded and truthful — a full party or an
    unreachable learner raises instead of looping."""
    global HM_CATCH_TARGET_DEX

    from modules.items import get_item_bag

    move = item.tm_hm_move()
    slot = hm_learner_slot(item)
    if slot is not None:
        return slot

    party_count = len([m for m in get_party() if m is not None])
    if party_count >= 6:
        # A catch would go to the PC, not the party — box management is #24-pc.
        raise BotModeError(
            f"No party mon can learn {move.name} and the party is full — "
            f"needs PC box management (#24-pc) or a manual swap."
        )

    grounds = _hm_hunting_grounds(item)
    if not grounds:
        raise BotModeError(
            f"No party mon can learn {move.name} and no swept training grass hosts "
            f"a learner species — extend training_areas.TRAINING_GRASS first."
        )
    # ‼ Prefer a REACHABLE ground (batch3 run01, 2026-07-24): the furthest-progressed
    # area can be warp-locked from here — after Norman the pick was Route 117, which
    # sits across the Rusturf Tunnel from Petalburg; the warp graph treats them as
    # one region, the plain planner can't cross, and ten failed navigations dropped a
    # NORMAN-BEATING run to Manual. Statically test each candidate from where we
    # stand (furthest-progressed first) and take the first that paths; if none does,
    # keep the old pick and let the riding navigation try its luck.
    from modules.map_path import calculate_path as _cp, PathFindingError as _pfe

    ordered = list(reversed(grounds))  # furthest-progressed first
    chosen = None
    try:
        _here = (get_map_data_for_current_position().map_group_and_number,
                 tuple(get_player_avatar().local_coordinates))
        for cand in ordered:
            try:
                _cp(_here, (cand[0], cand[1]), avoid_encounters=False, avoid_scripted_events=False)
                chosen = cand
                break
            except _pfe:
                continue
            except Exception:
                continue
    except Exception:
        pass
    # ⛔ FALLBACK DIRECTION FLIPPED 2026-08-26 (`#26-surfteachchain` audit): when NOTHING statically
    # paths, the old pick was `grounds[-1]` — the FURTHEST-progressed ground, which is precisely the
    # one most likely to be gated behind the very HM being hunted. MEASURED incident: batch
    # 20260731-105549/L01 f2493651 — seconds after "HM03 Surf incoming", the hunt announced
    # "hunting Linoone/Zigzagoon on ROUTE119", a SURF-GATED ground, for the SURF hunt. Circular.
    # `grounds[0]` is the earliest-game ground (for HM03: Route 101/102 grass on Petalburg's
    # doorstep), by construction the least gated and the most likely for the riding navigation to
    # actually reach. ⚠ HONEST LIMIT: this branch fires only when no candidate paths — an abnormal
    # state no driver reproduces yet — so the flip is proven by the measured incident's geometry,
    # not by a live A/B of the branch itself.
    map_enum, tile, names = chosen if chosen is not None else grounds[0]
    context.message = f"Story: nobody can learn {move.name} — hunting {'/'.join(names)} on {map_enum.name}..."

    if sum(s.quantity for s in get_item_bag().poke_balls) <= 1:
        yield from provision_poke_balls()
        if sum(s.quantity for s in get_item_bag().poke_balls) <= 1:
            raise BotModeError(f"Cannot hunt a {move.name} learner: no Poké Balls and no money to buy any.")

    yield from _navigate_riding_out(map_enum, tile)

    from modules.pokemon import get_species_by_name

    HM_CATCH_TARGET_DEX = {get_species_by_name(n).national_dex_number for n in names}
    try:
        before = party_count
        deadline = 40000  # ~11 min of spinning; grass hosts the target at common slots
        frames = 0

        def _caught() -> bool:
            return hm_learner_slot(item) is not None

        def _stop() -> bool:
            nonlocal frames
            frames += 1
            if frames > deadline:
                return True
            return _caught() or len([m for m in get_party() if m is not None]) > before

        yield from _story_spin(_stop)
    finally:
        HM_CATCH_TARGET_DEX = set()

    slot = hm_learner_slot(item)
    if slot is None:
        raise BotModeError(f"Hunted for a {move.name} learner but never caught one (timeout/balls).")
    # ‼ The spin stops the FRAME the catch registers — the catch AFTERMATH (nickname
    # YES/NO, "caught!" / dex messages) is still on screen. Hand back a CLEAN overworld
    # so the caller's next menu action can actually open (ch13_run1 f9931: the teach flow
    # opened the bag under the nickname prompt and wedged). B declines the nickname.
    yield from normalize_to_overworld()
    yield from wait_until_truly_controllable()
    context.message = f"Story: caught a {move.name} learner — {get_party()[slot].species.name}!"
    return slot


def ensure_hm_learner_making_room(item, heal_centers=()) -> Generator:
    """`ensure_hm_learner`, but if the ONLY blocker is a FULL PARTY, free one slot and retry once.

    ‼ THIS IS THE WIRING KI-63 WAS MISSING. `deposit_one_dead_weight` and the
    `_needs_party_slot` piggyback in `heal_in_pokemon_center` were built, driven to a PASS and
    PROMOTED — but **nothing in production ever set the flag**, so in a real run the piggyback
    never fired and `ensure_hm_learner` still derailed the whole run. The two production call
    sites (`story_mode.py`, Rock Smash and Surf) have **no local error handling at all**: a
    `BotModeError` there goes straight to the mode handler and ends the run in Manual.

    ‼ ORDER: TRY FIRST, DEPOSIT ONLY ON THE SPECIFIC FAILURE. `ensure_hm_learner` checks
    `hm_learner_slot` *before* the party-full check, so an unconditional deposit would cost a PC
    trip and a team member even when no catch was ever needed.

    ‼ AND IT REFUSES TO DEPOSIT FOR ANY OTHER FAILURE. "No huntable ground", "no balls and no
    money" and "never caught one" are all real, different problems; boxing a team member to
    "fix" one of them leaves the run strictly worse off than the honest derail it replaced.

    :param heal_centers: candidate Poké Centres, NEAREST FIRST, tried in order and skipped on
        failure — the `SLATEPORT_ROUTE_HEALS` pattern. ‼ The ORDER is a judgement call taken
        from what each calling segment already heals at, **not** a measured distance.
    """
    from modules.console import console
    from modules.context import context as _ctx
    from modules.modes.util.higher_level_actions import heal_in_pokemon_center

    def _party_size():
        return len([m for m in get_party() if m is not None])

    try:
        return (yield from ensure_hm_learner(item))
    except BotModeError as error:
        # ‼ FIRST STATEMENT, ALWAYS (KI-67): a whiteout unwind must never be swallowed here.
        reraise_if_aborting(error)
        if "party is full" not in str(error):
            raise
        original = error

    console.print(
        f"[cyan]Story: no HM learner and the party is full — freeing ONE slot, then retrying "
        f"(candidates: {[getattr(c, 'name', c) for c in heal_centers]}).[/]"
    )
    before = _party_size()
    mode = _ctx.bot_mode_instance
    healed = False
    try:
        setattr(mode, "_needs_party_slot", True)
        for centre in heal_centers:
            _check_abort()
            try:
                yield from heal_in_pokemon_center(centre)
                healed = True
                break
            except Exception as error:  # noqa: BLE001 - try the next centre, like SLATEPORT_ROUTE_HEALS
                reraise_if_aborting(error)
                console.print(
                    f"[yellow]Story: could not heal at {getattr(centre, 'name', centre)} "
                    f"({error!r}) — trying the next centre.[/]"
                )
    finally:
        # ‼ NEVER LEAVE THE HOOK ARMED. It fires on EVERY heal while set, and a stray deposit on
        # an unrelated later heal is exactly the measured harm that keeps POKEBOT_PC_ROTATION
        # pinned at 0 (~1 team member/run).
        setattr(mode, "_needs_party_slot", False)

    after = _party_size()
    if after >= before:
        # ‼ RE-RAISE THE ORIGINAL, not a new message. The blocker really is still "the party is
        # full", and inventing a fresh sentence here would send the next reader after the PC code
        # when the honest answer is that nothing was safe to deposit (every mon is a sole HM
        # carrier / a favourite / not dead weight) or that no centre could be reached.
        console.print(
            f"[yellow]Story: the party is still {after} (healed={healed}) — no slot was freed.[/]"
        )
        raise original

    console.print(f"[green]Story: freed a slot ({before} -> {after}); retrying the HM hunt.[/]")
    # ‼ EXACTLY ONE RETRY. If it fails again the error is genuinely something else, and a loop
    # here would deposit a second team member on the next pass.
    return (yield from ensure_hm_learner(item))


def teach_hm_move(item, party_index: int, replace_slot: int | None = None) -> Generator:
    """Teach an HM (or TM) from the bag to a party mon — the OVERWORLD flow, state-
    driven off the live-probed task chain (2026-07-22): open bag → item context (USE is
    the first entry) → 'Booted up an HM.' prints (Task_ContinueTaskAfterMessagePrints)
    → teach YES/NO (Task_CallYesOrNoCallback) → party menu (Task_HandleChooseMonInput,
    cursor NOT guaranteed at slot 0 — scroll!) → replace YES/NO (Task_ReplaceMoveYesNo)
    → summary move-select (Task_HandleReplaceMoveInput) → '1, 2, and... Poof!' → party
    menu → B out. `replace_slot=None` picks the mon's most expendable slot (a 0-power
    move first, else the lowest base power). Verifies the mon actually knows the move."""
    from modules.menuing import StartMenuNavigator, scroll_to_item_in_bag, scroll_to_party_menu_index
    from modules.battle_move_replacing import _get_move_selection_cursor

    target_move = item.tm_hm_move()
    if target_move is None:
        raise BotModeError(f"{item.name} does not teach a move.")

    def _mon():
        return get_party()[party_index]

    if any(l is not None and l.move.name == target_move.name for l in _mon().moves):
        return  # already knows it

    # ‼ COMPATIBILITY GUARD (user report 2026-07-23): the party menu shows an
    # incompatible mon as "NOT ABLE" and refuses the selection, which an A-mash
    # experiences as an endless teach loop. Callers should pick the target with
    # `hm_learner_slot()` / `ensure_hm_learner()`; this guard makes the failure
    # truthful if they didn't.
    if not _mon().species.can_learn_tm_hm(item):
        raise BotModeError(
            f"Teach flow: {_mon().species.name} cannot learn {target_move.name} — "
            f"pick a compatible mon (hm_learner_slot/ensure_hm_learner)."
        )

    if replace_slot is None:
        moves = _mon().moves
        # ‼ HM SLOTS ARE NOT ELIGIBLE (2026-07-24, user's design — and this picker is the
        # ROOT CAUSE of their original Surf/Rock-Smash report, which I could not reproduce
        # from the level-up path all day because it was never the level-up path).
        # An HM move CANNOT be forgotten in Gen 3 (Move Deleter only), and this "most
        # expendable slot" heuristic walked straight into them:
        #   * FLASH has base_power 0, so the zero-power rule picked it FIRST;
        #   * ROCK SMASH has base_power 20 — the lowest of any HM and lower than nearly
        #     any real attacking move — so the lowest-power rule picked it.
        # The game then refuses and the teach flow loops. Exclude every HM from
        # eligibility, then apply the SAME expendability ranking to what remains
        # (zero-power first, then weakest), so the mon still gives up its least useful
        # real move rather than declining to learn anything.
        def _is_hm_slot(learned) -> bool:
            try:
                m = learned.move
                return m.tm_hm is not None and m.tm_hm.name.startswith("HM")
            except Exception:
                return False

        eligible = [i for i, l in enumerate(moves) if l is not None and not _is_hm_slot(l)]
        empty = [i for i, l in enumerate(moves) if l is None]
        if empty:
            # Fewer than 4 moves: the game just learns it, no replacement needed.
            replace_slot = empty[0]
        elif not eligible:
            # Every slot is an HM (e.g. Surf/Cut/Strength/Rock Smash). NOTHING can be
            # replaced — the game will refuse whatever we pick, so don't start a teach we
            # provably cannot finish. Fail loudly for the caller's recovery instead of
            # feeding the dialogue a doomed choice.
            raise BotModeError(
                f"teach_hm_move: {_mon().species.name} knows only HM moves "
                f"({[l.move.name for l in moves if l is not None]}) — none can be "
                f"forgotten, so {target_move.name} cannot be taught to it. "
                f"Pick a different learner."
            )
        else:
            zero = [i for i in eligible if moves[i].move.base_power == 0]
            if zero:
                replace_slot = zero[0]
            else:
                replace_slot = min(eligible, key=lambda i: moves[i].move.base_power)

    context.message = f"Story: teaching {target_move.name} to {_mon().species.name}..."
    # ‼ NORMALIZE FIRST (user's Surf report + ch13_run1 f9931): the caller may hand us a
    # state with a dialogue STILL OPEN — most often `ensure_hm_learner`, which returns the
    # instant the catch registers while "Give a nickname to the captured X?" is still on
    # screen. `wait_until_truly_controllable` presses NOTHING by design, so the avatar
    # reads controllable, we open the BAG on top of the pending prompt, and the whole
    # teach wedges in BAG_MENU until the watchdog (the KI-14 menu-under-a-script class).
    # normalize_to_overworld B-rides any menu/dialogue/scene to a clean overworld first —
    # B also answers the nickname prompt "no", which is what we want, and B can never
    # start an NPC conversation. Applies to EVERY HM/TM teach, not just Surf.
    yield from normalize_to_overworld()
    yield from wait_until_truly_controllable()
    yield from StartMenuNavigator("BAG").step()
    yield from scroll_to_item_in_bag(item)

    def _tasks() -> set:
        try:
            return {t.symbol for t in get_tasks()}
        except Exception:
            return set()

    # ‼ `#24-hmteachloop` INSTRUMENTATION (2026-08-07). Four budget configurations were batched
    # (7 / 8 / 9 / 4 failures) and NONE of them could say WHICH of this flow's exits fired,
    # because only the SUCCESS path emitted an event (`TEACH OK`). Every hypothesis about the
    # cause was therefore unfalsifiable, and the budget was tuned four times on a number that
    # governs only failures. This emits one `TEACH EXIT` line per non-success exit, carrying the
    # frame, the live task set, the learn-move state and the target's moves — enough to tell a
    # stall-misfire from a genuine wedge from a never-appeared task WITHOUT another batch.
    # It changes no control flow: read it, diagnose, then fix.
    def _teach_exit(reason: str, frame: int | None = None) -> None:
        try:
            from modules import debug_logger
            from modules.battle_move_replacing import get_learn_move_state as _lms

            try:
                _state = str(_lms())
            except Exception:  # noqa: BLE001
                _state = "<unreadable>"
            try:
                _moves = [l.move.name for l in _mon().moves if l is not None]
            except Exception:  # noqa: BLE001
                _moves = ["<unreadable>"]
            debug_logger.event(
                f"TEACH EXIT reason={reason} move={target_move.name} "
                f"slot={party_index} replace_slot={replace_slot} frame={frame} "
                f"tasks={sorted(_tasks())} learn_state={_state} moves={_moves}"
            )
        except Exception:  # noqa: BLE001 - telemetry must never break the teach
            pass

    # ‼‼ `#24-teachmsgstall` FRAME TRACE (2026-08-11), env-gated by `TEACH_TRACE=1`, OFF by
    # default and changing NO control flow. Four rounds of this bug were argued from `TEACH EXIT`
    # alone — three summary records taken at the three EXITS — and every hypothesis drawn from
    # them was refuted (parked battle script, normalize-settle, teach parameters). The reason is
    # structural: `TEACH EXIT` reports the state where the flow GAVE UP, and the failing run is
    # **cycling, not frozen** (`stall_peak=61` against a 900 threshold), so the give-up state is
    # a random phase of the cycle. That is exactly why "the point of failure MOVES" across runs
    # — the three observed task sets are three phases of one loop, not three different bugs.
    #
    # This emits ONE LINE PER OBSERVABLE CHANGE (phase + game state + task set + learn state +
    # does-the-mon-know-it), carrying **the buttons WE pressed since the previous line**. That
    # last field is the whole point: a bag↔party ping-pong that our own A-mash is driving looks
    # identical, in a per-frame task dump, to one the game is driving by itself. Pair the cause
    # with the effect on the same line or the trace answers nothing.
    import os as _os_trace

    _TEACH_TRACE = _os_trace.environ.get("TEACH_TRACE", "0") == "1"
    _trace_press: list[str] = []
    _trace_sig: list = [None, 0]  # [last signature, lines emitted] — list so the closure can write

    def _press(btn: str) -> None:
        """Press, and RECORD it for the trace. Every button in this flow goes through here."""
        _trace_press.append(btn)
        context.emulator.press_button(btn)

    def _trace(phase: str) -> None:
        if not _TEACH_TRACE or _trace_sig[1] >= 4000:
            return
        try:
            from modules import debug_logger
            from modules.battle_move_replacing import get_learn_move_state as _lms2

            try:
                _ls = str(_lms2()).replace("LearnMoveState.", "")
            except Exception:  # noqa: BLE001
                _ls = "?"
            _kn = any(
                l is not None and l.move.name == target_move.name for l in _mon().moves
            )
            _sig = (phase, str(get_game_state()), tuple(sorted(_tasks())), _ls, _kn)
            if _sig == _trace_sig[0]:
                return
            _trace_sig[0] = _sig
            _trace_sig[1] += 1
            _p = "".join(_trace_press)
            _trace_press.clear()
            debug_logger.event(
                f"TEACH TRACE phase={phase} state={_sig[1]} learn={_ls} knows={_kn} "
                f"pressed_since={_p or '-'} tasks={list(_sig[2])}"
            )
        except Exception:  # noqa: BLE001 — telemetry must never break the teach
            pass

    def _wait_for(
        task_name: str, *, press: str | None = None, cap: int = 900, required: bool = True
    ) -> Generator:
        """Wait for `task_name`. Returns True if it appeared, False only when `required=False`.

        ‼ `required=False` is for callers that have a SAFE fallback (the ride loop). Every
        other caller keeps the raise: a teach that silently gave up on a menu step is the
        `#24-hmteachloop` shape, and the loud failure is the only in-flow detector there is.
        """
        for _f in range(cap):
            _trace(f"wait:{task_name}")
            if task_name in _tasks():
                return True
            if press and _f % 12 == 0:
                _press(press)
            yield
        _teach_exit(f"never-appeared:{task_name}", cap)
        if not required:
            return False
        raise BotModeError(f"Teach flow: {task_name} never appeared.")

    from modules.tasks import get_tasks

    _trace("bag-open")
    _press("A")  # item context menu
    yield from wait_for_n_frames(20)
    _trace("item-menu")
    _press("A")  # USE
    yield from wait_for_n_frames(20)
    yield from _wait_for("Task_CallYesOrNoCallback", press="A")   # ride 'Booted up an HM.'
    _trace("teach-yesno")
    _press("A")  # YES, teach it
    # The bag→party transition fades through a task-less state; keep tapping A like
    # the probe did or the party menu can take >600 frames to materialize.
    yield from _wait_for("Task_HandleChooseMonInput", press="A", cap=1200)
    _trace("party-menu-up")
    yield from scroll_to_party_menu_index(party_index)
    _trace("party-scrolled")
    _press("A")
    yield from wait_for_n_frames(30)
    # Either it learns instantly (<4 moves) or the replace YES/NO comes up.
    #
    # ‼‼ `#24-teachpathrace`, FIXED 2026-08-07 — a SECOND teach bug, caught by the `TEACH EXIT`
    # telemetry in its very first batch (4 of 37 teaches, ~11%, all fatal):
    #     TEACH EXIT reason=ride:hard-cap post_select=instant-learn move=Surf frame=8999
    #                tasks=['ListMenuDummyTask', 'Task_BagMenu_HandleInput', …]
    #                moves=['Take Down', 'Mud Shot', 'Rock Smash', 'Muddy Water']
    # **`instant-learn` on a mon with FOUR moves is a contradiction, and that is the whole
    # diagnosis.** `Task_HandleChooseMonInput` is STILL UP for a while after the mon is chosen,
    # so on a slow frame it wins this race before `Task_ReplaceMoveYesNo` appears. The loop then
    # declared the instant-learn path, the guarded `if "Task_ReplaceMoveYesNo" in _tasks():`
    # block below was skipped entirely, the replace prompt was never answered, and the flow rode
    # out the whole 9,000-frame cap stuck in the BAG without learning the move.
    #
    # ‼ THE RULE: **a task that is present on BOTH paths cannot discriminate between them.**
    # The instant-learn exit now requires POSITIVE evidence — a genuinely free move slot, or the
    # move already known. With four moves there is no instant-learn path to take, so the only
    # legitimate exits are the replace prompt or the move being learned.
    _free_slots = [i for i, l in enumerate(_mon().moves) if l is None]
    _may_instant_learn = bool(_free_slots)

    def _knows() -> bool:
        return any(l is not None and l.move.name == target_move.name for l in _mon().moves)

    # ‼‼ `#24-teachmsgstall` — ROOT CAUSE, FOUND 2026-08-11 BY FRAME TRACE, DECOMP-CONFIRMED.
    #
    # THE OLD EXIT TEST HAD A **ONE-FRAME WINDOW**, and this is the whole bug. Measured
    # (`TEACH_TRACE=1`, `magma_door.ss1`, HM02 → Swellow):
    #     f3232735  tasks=['Task_ReplaceMoveYesNo']            <- the ONLY frame it is visible
    #     f3232736  tasks=['Task_HandleReplaceMoveYesNoInput'] <- gone, and it never returns
    # `src/party_menu.c`:
    #     Task_ReplaceMoveYesNo: if (!IsPartyMenuTextPrinterActive()) {
    #                                PartyMenuDisplayYesNoMenu();
    #                                func = Task_HandleReplaceMoveYesNoInput; }
    # So `Task_ReplaceMoveYesNo` **swaps itself out on the very frame it becomes answerable** —
    # which is precisely the frame the old condition (`in t` AND no text printer) first became
    # true. One missed yield and the prompt is unobservable for ever.
    #
    # WHAT HAPPENED WHEN IT WAS MISSED — every symptom this bug ever showed, in one road. The
    # loop kept mashing A every 12 frames, and `Task_HandleStopLearningMoveYesNoInput` reads
    # **A as YES = ABANDON THE TEACH** (decomp: case 0 → "did not learn X" →
    # `Task_ClosePartyMenuAfterText`). The A-mash therefore walked the flow through
    # YES-replace → summary screen (`Task_ClosePartyMenuAndSetCB2`) → "Stop trying to teach?"
    # → **YES** → `Task_ClosePartyMenuAfterText` → back to the bag → and the same mash re-armed
    # the whole teach from the item. ‼ THE THREE "DIFFERENT" FAILURE POINTS RECORDED ACROSS
    # RUNS ARE THREE PHASES OF THAT ONE ROAD:
    #     `Task_ClosePartyMenuAndSetCB2`                       (summary-screen handoff)
    #     `Task_ClosePartyMenuAfterText` + `Task_PrintAndWaitForText`  ("did not learn FLY")
    #     `ListMenuDummyTask` + `Task_BagMenu_HandleInput`     (back in the bag, re-arming)
    # "A single broken menu step cannot move like that" was right — it was never one step.
    #
    # ‼ AND THIS IS WHY IT LOOKED DETERMINISTIC *AND* INTERMITTENT AT THE SAME TIME, which is
    # what made it unfalsifiable for four rounds. A `.ss1` replays identical frame timing, so a
    # save that misses the window misses it on EVERY replay (0 of 3 from the old
    # `magma_door.ss1`); live runs land on a random phase, so they hit it rarely (38 of 42 in
    # batch `20260810-082509` ≈ 90%). Same bug, both readings.
    #
    # THE FIX IS TO STOP DEPENDING ON ONE FRAME, in three parts:
    #   1. `Task_HandleReplaceMoveYesNoInput` is the SAME prompt one task later — and it is the
    #      one that actually reads input, so it is up for as long as the prompt is answerable.
    #      Accept it. This alone turns a 1-frame window into an open-ended one.
    #   2. If the flow has already advanced PAST the prompt, say so (`already-advanced`) and
    #      pick the flow up there instead of hunting a prompt that is gone.
    #   3. **Never blind-mash A at a live yes/no.** `Task_StopLearningMoveYesNo` gets B — NO,
    #      never give up — which the decomp routes straight back to `Task_ReplaceMoveYesNo` for
    #      another attempt. The ride loop already did exactly this; this loop did not, and it is
    #      the loop that runs first.
    #
    # ‼ A is still pressed to advance TEXT — that is what carries "…can't learn more than four
    # moves…" to its end (41 A presses over 489 frames on the passing trace). Removing it would
    # trade this bug for a stall.
    _PROMPT_TASKS = ("Task_ReplaceMoveYesNo", "Task_HandleReplaceMoveYesNoInput")
    _ADVANCED_TASKS = (
        "Task_ShowSummaryScreenToForgetMove",
        "Task_SetHandleReplaceMoveInput",
        "Task_HandleReplaceMoveInput",
        "Task_ReturnToPartyMenuWhileLearningMove",
    )
    _STOP_TASKS = ("Task_StopLearningMoveYesNo", "Task_HandleStopLearningMoveYesNoInput")

    # FAULT INJECTION, both default-off, so this bug can be re-measured without reverting code:
    #   `TEACH_MISS_WINDOW=1`     — model the real-world miss: ignore the 1-frame
    #                               `Task_ReplaceMoveYesNo` sighting, exactly as a mistimed
    #                               frame does. This is the REPRO, and it is faithful because
    #                               the game state is untouched — only our observation of it.
    #   `POKEBOT_TEACHWINDOW_A=1` — restore the pre-fix loop (OLD arm of the A/B).
    #   `TEACH_CANCEL_FORGET=1` — cancel the forget-move screen once, which is what a mistimed
    #                             press does for real. Per the decomp that routes to
    #                             `StopLearningMovePrompt` — the prompt where A means GIVE UP —
    #                             so this injection lands the flow on the exact tile the real
    #                             failures ended on. THIS is the arm that discriminates.
    # ‼ `TEACH_MISS_WINDOW` alone was measured NOT to be enough: with the pre-fix loop it exits
    # `post_select=exhausted` and the ride loop's ladder still recovers it (`ride:learned`,
    # 323f). Missing the window is NECESSARY BUT NOT SUFFICIENT — where the blind A-mash then
    # lands is what decides whether the teach survives, which is precisely why the recorded
    # failure point moved between runs. Keep both injections; they test different halves.
    _MISS_WINDOW = _os_trace.environ.get("TEACH_MISS_WINDOW", "0") == "1"
    _CANCEL_FORGET = _os_trace.environ.get("TEACH_CANCEL_FORGET", "0") == "1"
    _injected = [False]  # one-shot latch for _CANCEL_FORGET (list so the closure can write)
    _WINDOW_A = _os_trace.environ.get("POKEBOT_TEACHWINDOW_A", "0") == "1"
    # The pre-fix arm must restore the pre-fix RIDE ladder too, or the OLD arm quietly enjoys
    # half the fix and the A/B measures nothing.
    _PROMPT_MATCH = ("Task_ReplaceMoveYesNo",) if _WINDOW_A else _PROMPT_TASKS
    _STOP_MATCH = ("Task_StopLearningMoveYesNo",) if _WINDOW_A else _STOP_TASKS

    _post_select_exit = "exhausted"
    for _f in range(900):
        _trace("post-select")
        t = _tasks()
        if not _WINDOW_A and any(x in t for x in _ADVANCED_TASKS):
            # Someone already answered the replace prompt (our own text-advancing A, most
            # likely). The prompt is gone and will not come back — pick the flow up here.
            _post_select_exit = "already-advanced"
            break
        if "Task_ReplaceMoveYesNo" in t and "Task_PrintAndWaitForText" not in t:
            if not _MISS_WINDOW:
                _post_select_exit = "replace-prompt"
                break
        elif not _WINDOW_A and "Task_HandleReplaceMoveYesNoInput" in t:
            _post_select_exit = "replace-prompt"
            break
        if _knows():
            _post_select_exit = "instant-learn"
            break  # the move is on the mon — this really was the free-slot path
        if _may_instant_learn and (
            "Task_PartyMenuReplaceMove" in t or "Task_HandleChooseMonInput" in t
        ):
            _post_select_exit = "instant-learn-freeslot"
            break
        if not _WINDOW_A and any(x in t for x in _STOP_TASKS):
            _press("B")  # NO — never abandon the teach. A here means YES, give up.
        elif _f % 12 == 0 and (
            get_game_state() is not GameState.OVERWORLD
            or _menu_task_active()
            or is_waiting_for_input()
        ):
            # ⛔ GATED 2026-08-26 (`#26-surfteachchain` D2) — same museum-greeter shape as the ride
            # loop's blind A, smaller window. This loop is also the recorded source of the open
            # `#24-teachmsgstall` residue (post_select=exhausted, 8/85): an A that lands at the
            # open overworld can only start a conversation, never advance a teach.
            _press("A")
        yield
    if _post_select_exit == "exhausted":
        # ‼ This falls through SILENTLY into the ride loop, so a teach that never reached
        # either branch has always looked identical to one that did. Not raising here is
        # deliberate (the ride loop can still recover it) — but it must be visible.
        _teach_exit("post-select-900-exhausted", 900)

    def _select_forget_slot() -> Generator:
        # The overworld summary move-select CURSOR STARTS AT SLOT 0 (probed) — press
        # Down exactly replace_slot times, then A. (_get_move_selection_cursor reads
        # the battle/evolution variant and returns garbage here; trusting it walked
        # the cursor onto CANCEL and bounced the flow into 'Stop trying to teach?'.)
        yield from wait_for_n_frames(45)
        _trace("forget-menu")
        for _ in range(replace_slot):
            _press("Down")
            yield from wait_for_n_frames(8)
        _trace("forget-cursor")
        if _CANCEL_FORGET and not _injected[0]:
            # FAULT INJECTION ONLY, and **ONCE**. Cancelling here is what a single mistimed
            # press does for real; the decomp then runs
            # `Task_ReturnToPartyMenuWhileLearningMove` ->
            # `GetMoveSlotToReplace() == MAX_MON_MOVES` -> `StopLearningMovePrompt`, i.e. the
            # prompt where A means GIVE UP. The recovery under test is "say NO and come back",
            # so the injection MUST NOT repeat — a fault that re-fires on every retry can never
            # be satisfied, and the fixed arm then looks broken for doing the right thing.
            # (Measured: the always-on version made the NEW arm loop replace-prompt -> cancel
            # -> stop-prompt -> NO -> replace-prompt until the cap. That was the injection, not
            # the fix.)
            _injected[0] = True
            _press("B")
        else:
            _press("A")
        yield from wait_for_n_frames(30)

    # ‼ THE PROMPT HAS TWO SPELLINGS AND MAY ALREADY BE ANSWERED (`#24-teachmsgstall`, above).
    # The old test named only `Task_ReplaceMoveYesNo` — the task that exists for ONE frame — so
    # whenever the loop exited on the later `Task_HandleReplaceMoveYesNoInput`, or after our own
    # A had already answered it, this whole block was skipped and the flow fell into the ride
    # loop with the forget-move screen still waiting for a move to be chosen. Answer it if it is
    # live; pick it up where it stands if it is not.
    _prompt_live = any(x in _tasks() for x in _PROMPT_TASKS)
    if _prompt_live or _post_select_exit == "already-advanced":
        if _prompt_live:
            _trace("replace-yesno")
            _press("A")  # YES, replace a move
        # ‼ NON-FATAL ON THE `already-advanced` PATH. The prompt path has always been allowed to
        # raise here and that is kept; but `already-advanced` is a NEW way into this block, and
        # making it raise would create a fresh run-ending class where the old code merely fell
        # through. If the forget-move input never materialises, hand over to the ride loop —
        # whose ladder already handles every task on this road, including B on "stop learning?".
        if (yield from _wait_for(
            "Task_HandleReplaceMoveInput",
            press="A",
            required=_post_select_exit != "already-advanced",
        )):
            yield from _select_forget_slot()
    # Ride the 'Poof!'/learned messages out STATE-AWARE (a blind A/B mash re-answers
    # the yes/no prompts in a loop — run 3 ping-ponged between 'wants to learn' and
    # 'Stop trying to teach?' until the frame cap died).
    #
    # ‼‼ THE BUDGET IS PROGRESS-AWARE, NOT FLAT (`#24-hmteachloop`, fixed 2026-08-06).
    # It was `range(3000)`, and that expired while the teach was STILL PROGRESSING —
    # measured on batch `20260806-055947`: **7 of 19 Surf teaches** raised
    # "Teach flow finished but <mon> does not know Surf", and the move was then learned
    # **1,867-1,878 frames later** (σ≈4) in every single case. The raise derailed the run,
    # which restarts `_play()` from the top of the chapter ladder — that reprint of the
    # whole "already done" litany is what the user saw as "it loops after teaching an HM".
    #
    # WHY THOSE 7 AND NOT THE OTHER 35: all 7 start with the NORMAN BATTLE TAIL still
    # resident (`callback=ReturnFromBattleToOverworld`), which stretches the dialogue chain
    # past 3,000 frames. Rock Smash (23/23 clean) ends on a quiet map; the Zigzagoon Surf
    # path (12/12 clean) burns 10-19k frames hunting first AND an L3 mon has a free slot,
    # so there is no replace dialogue at all.
    #
    # ‼ A SETTLE-AND-RECHECK WOULD HAVE FIXED 0 OF 7 — they needed ~1,872 frames, not 300.
    #
    # ‼‼ THE STALL DETECTOR IS BACK, AND REMOVING IT WAS MY ERROR. Three configurations have
    # now been batched, and the failure count is FLAT while the finish rate is not:
    #     flat 3000, no stall      -> 7 failures, finish 37.5%  (`20260806-055947`)
    #     9000 cap + 900 stall     -> 8 failures, finish 52.0%  (`20260806-103811`)  <-- BEST
    #     9000 cap, NO stall       -> 9 failures, finish 30.8%, watchdog 20 -> 68 (`20260806-142418`)
    #
    # 7 / 8 / 9 is noise; I read the 7 -> 8 as "the stall detector made it worse" and removed
    # it. It did not. What it actually did was make each FAILURE CHEAP.
    #
    # WHY THAT MATTERS, from this batch's own data: every SUCCESSFUL teach exits in **35-86
    # frames** (n=42). So the budget is irrelevant to successes and governs only failures —
    # and without the stall break a failure burns the FULL 9,000 frames instead of ~900.
    # That is ~8,100 wasted frames per failure, which is exactly the shape that feeds the
    # 18,000-frame global watchdog.
    #
    # ‼‼ RESOLVED 2026-08-07 — AND TWO OF THE MEASUREMENTS ABOVE ARE WRONG. Read this before
    # trusting any figure in this comment block.
    #
    # THE BUG: after the move was learned, the button ladder below fell through to a blind
    # `A`-every-third-frame, and Gen 3 ends a bag teach on "teach it to another POKéMON?" —
    # where A means YES. We re-armed the teach cycle ourselves until the cap expired. Full
    # detail at the `if _knows()` branch below; `repro_hmteach_postlearn.py` pins it.
    #
    # ‼ "every SUCCESSFUL teach exits in 35-86 frames (n=42)" IS NOT THE RIDE. That figure came
    # from `TEACH OK … in {_f} frames`, and `_f` had already been REBOUND by the menus-closed
    # loop — it was measuring menu closing. The ride's real cost, once measured properly, was
    # **8,999 frames — the entire cap — on a teach that had already succeeded.** The inference
    # "the budget is irrelevant to successes and governs only failures" was drawn from the
    # wrong loop, and the four tuning rounds followed from it.
    #
    # ‼ "7 / 8 / 9 is noise" was right for the wrong reason. Every config burned the whole cap
    # after success; the stall detector could not help because the ping-pong keeps the state
    # changing (`stall_peak=171` against a 900 threshold). Changing the cap only changed how
    # much was wasted, never whether it was wasted — which is why four rounds moved nothing.
    #
    # A/B (`--driver teachfull`, `POKEBOT_HMTEACH_POSTLEARN_A`):
    #     OLD  ride_exit=hard-cap  ride_frames=8999   learned=True
    #     NEW  ride_exit=learned   ride_frames=479    learned=True
    #
    # `_TEACH_RIDE_HARD_CAP` stays ABSOLUTE: never "loop until progress", because this
    # generator is re-entered by the derail dispatcher and an unbounded-while-progressing loop
    # is the KI-34 shape that burned 23.9M frames.
    from modules.battle_move_replacing import get_learn_move_state

    # FAULT INJECTION for the `#24-hmteachloop` A/B (see the `_knows()` branch below).
    # `POKEBOT_HMTEACH_POSTLEARN_A=1` restores the pre-fix behaviour — keep A-mashing after the
    # move is learned — so the OLD arm can be measured on demand without reverting code.
    # Default 0 = fixed. It exists because "the error stopped" is not proof a fix worked; an
    # arm that reproduces the bug on request is.
    import os as _os

    _POSTLEARN_A = _os.environ.get("POKEBOT_HMTEACH_POSTLEARN_A", "0") == "1"

    _TEACH_RIDE_HARD_CAP = 9000      # 1.85x the worst LEGITIMATE observed path (4,875)
    _TEACH_RIDE_STALL_FRAMES = 900   # observable state frozen this long => wedged, stop cheaply
    _stall = 0
    _last_sig = None
    _fail_stable = 0  # `#26-surfteachchain` D1b: consecutive stable-overworld frames with no learn
    _ride_exit = "hard-cap"
    _stall_peak = 0
    for _f in range(_TEACH_RIDE_HARD_CAP):
        _trace("ride")
        if _knows() and get_game_state() is GameState.OVERWORLD and player_avatar_is_controllable():
            _ride_exit = "learned"
            break
        t = _tasks()
        # Progress signature: task set + learn-state + the target's own moves.
        try:
            _sig = (tuple(sorted(t)), str(get_learn_move_state()),
                    tuple(l.move.name for l in _mon().moves if l is not None))
        except Exception:  # noqa: BLE001 — an unreadable signature must never end the teach
            _sig = None
        if _sig is not None and _sig == _last_sig:
            _stall += 1
            _stall_peak = max(_stall_peak, _stall)
            if _stall >= _TEACH_RIDE_STALL_FRAMES:
                _ride_exit = "stall"
                break  # frozen => fall through to the menus-closed guarantee, cheaply
        else:
            _stall = 0
            _last_sig = _sig
        if _knows() and not _POSTLEARN_A:
            # ‼‼ THE `#24-hmteachloop` BUG, FOUND 2026-08-07. THIS IS THE USER'S REPORT
            # VERBATIM: "it still loops trying to teach/get out of the teaching cycle AFTER it
            # teaches an hm."
            #
            # Once the move IS learned, both replace branches below switch themselves off via
            # `and not _knows()` — so every remaining frame fell through to the blind
            # `_f % 3 == 0 -> A, else B` policy. But Gen 3 follows a bag teach with
            # **"Do you want to teach <MOVE> to another POKéMON?"** (`Task_CallYesOrNoCallback`),
            # and **A on that prompt means YES**: it reopens the party menu and re-enters the
            # teach cycle, which the A-mash then drives again. The loop is not stuck — it is
            # being actively re-armed, one frame in three, by our own buttons.
            #
            # Measured (`--driver teachfull`, Mightyena with 4 moves, the replace path):
            #     TEACH EXIT reason=ride:hard-cap stall_peak=171 frame=8999
            #                tasks=['ListMenuDummyTask', 'Task_CallYesOrNoCallback']
            #                moves=[... 'Rock Smash' ...]   <- learned LONG before frame 8999
            # It burned the FULL 9,000-frame cap on a teach that had already succeeded.
            #
            # ‼ THIS IS WHY FOUR BUDGET ROUNDS FAILED (7/8/9/4). The cap only ever decided how
            # long to churn AFTER success, and the stall detector could never fire because the
            # ping-pong keeps the state changing — `stall_peak=171` against a 900 threshold.
            # The budget was never the knob, exactly as `03-PUNCH-LIST.md` insisted.
            #
            # After the move is learned there is nothing left to accept, so the only safe
            # button is B: it declines "teach another", backs out of the bag, and cannot start
            # an NPC conversation. The `_knows()` success test at the top of the loop then
            # exits as soon as the overworld is genuinely back.
            _press("B")
        elif any(x in t for x in _STOP_MATCH):
            # ‼ BOTH SPELLINGS (`#24-teachmsgstall`, 2026-08-11). `Task_StopLearningMoveYesNo`
            # swaps itself out for `Task_HandleStopLearningMoveYesNoInput` on the frame the
            # menu becomes answerable (same decomp pattern as the replace prompt), so naming
            # only the first meant this branch pressed B at a prompt that could not yet read
            # it, and the *answerable* frames fell through to the blind `_f % 3` policy — which
            # presses A one frame in three, and A here is YES, ABANDON THE TEACH.
            _press("B")  # NO — never give up on the teach
        elif any(x in t for x in _PROMPT_MATCH) and not _knows():
            _press("A")  # YES — replace
        elif "Task_HandleReplaceMoveInput" in t and not _knows():
            yield from _select_forget_slot()
            continue
        elif _f % 3 == 0 and (
            get_game_state() is not GameState.OVERWORLD
            or _menu_task_active()
            or is_waiting_for_input()
        ):
            # ⛔ THE A IS GATED NOW (`#26-surfteachchain` D1, USER REPORT 2026-08-26). This branch
            # used to press A one frame in three UNCONDITIONALLY — the museum-greeter shape,
            # verbatim, in the one seam that arms it: a FAILED teach unwinds to the open overworld
            # INSIDE WALLY'S HOUSE, next to Wally's dad, and the blind A re-opened his dialogue
            # every third frame. The dialogue's task churn kept the progress signature changing, so
            # the stall detector could never fire (its own measurement above: stall_peak=171 vs a
            # 900 threshold) and the loop burned its full 9,000-frame cap TALKING TO THE NPC — then
            # raised, and the derail re-ran the teach, which is the user's "loops talking to the
            # npc ... loops a bunch attempting to teach". A is now pressed only where an accept
            # can land: in a menu, in text, or when a printer is actually waiting for input.
            _press("A")
        else:
            _press("B")

        # ⛔ FAILURE-PHASE EXIT (`#26-surfteachchain` D1b): a teach that reaches a STABLE open
        # overworld WITHOUT the move learned can never succeed by pressing more buttons — every
        # menu is gone. Break and let the honest "does not know" raise at the bottom fire ~8,000
        # frames sooner, without ever touching the NPC. 30 stable frames ≈ two input windows,
        # long enough to be sure no task is mid-transition (the same debounce reasoning as
        # `wait_until_truly_controllable`).
        if (
            not _knows()
            and get_game_state() is GameState.OVERWORLD
            and player_avatar_is_controllable()
            and not _menu_task_active()
            and not is_waiting_for_input()
        ):
            _fail_stable += 1
            if _fail_stable >= 30:
                _ride_exit = "failed-overworld"
                break
        else:
            _fail_stable = 0
        yield
    # ‼ THE LINE THAT FOUR BUDGET ROUNDS WERE MISSING. `_ride_exit` distinguishes the three
    # ways out of the ride, which demand OPPOSITE fixes and were indistinguishable before:
    #   learned    — success (also logged as `TEACH OK` below; recorded here for the frame/peak)
    #   stall      — the signature froze for 900f. ‼ If `_stall_peak` is ~900 on a teach that
    #                LATER succeeds, the stall detector is MISFIRING on a slow-but-legitimate
    #                scene (the signature cannot see text scrolling), and the fix is a better
    #                signature — NOT a bigger budget.
    #   hard-cap   — 9,000 frames of mashing with the state still changing = a genuine
    #                ping-pong, and the button policy is the thing to fix.
    # ‼‼ CAPTURE THE RIDE'S FRAME COUNT *HERE*, BEFORE ANY OTHER LOOP REBINDS `_f`.
    # Python leaks a `for` variable into the enclosing scope, and the menus-closed loop below
    # is ALSO `for _f in range(...)`. The success event at the end of this function reads `_f`
    # — so `TEACH OK … in {_f} frames` has always reported the MENUS-CLOSED loop's iteration
    # count, never the ride's. That is where "every SUCCESSFUL teach exits in 35-86 frames
    # (n=42)" came from, and that figure is what justified "the budget governs only failures"
    # and four rounds of budget tuning. **The ride duration was never actually measured.**
    _ride_frames = _f
    _teach_exit(
        f"ride:{_ride_exit} stall_peak={_stall_peak} post_select={_post_select_exit}",
        _ride_frames,
    )
    # HARD menus-closed guarantee: the ride above can expire with the BAG still open
    # (seen on a 5-mon roll, batch run02) — and neither the derail recovery nor the
    # global watchdog can close a bag (they ride SCRIPTS; a menu isn't one). B out
    # until the overworld is truly back, bounded.
    # ‼ KI-14: "back to the overworld" is NOT `game_state == OVERWORLD` — the START
    # MENU (which the bag closes back into) already reads as OVERWORLD, so the old
    # check exited with the menu still open and the avatar frozen; the conservative
    # cutscene rider then rightly refused to mash at a menu and the next travel leg
    # wedged to Manual (user's 2026-07-23 fresh run). Menu-free means: OVERWORLD
    # state AND no menu task up AND the avatar actually controllable.
    for _f in range(1200):
        _trace("close")
        if (
            get_game_state() is GameState.OVERWORLD
            and not _menu_task_active()
            and player_avatar_is_controllable()
        ):
            break
        _press("B")
        yield
        yield
    yield from wait_until_truly_controllable()
    if get_game_state() is not GameState.OVERWORLD or _menu_task_active():
        _teach_exit("menus-never-closed", 1200)
        raise BotModeError("Teach flow: could not close the menus back to the overworld.")
    if not _knows():
        _teach_exit(f"not-learned-after-ride:{_ride_exit} stall_peak={_stall_peak}", _ride_frames)
        # ‼ KEPT ON PURPOSE (`#24-hmteachloop`, 2026-08-06). The bug was the BUDGET, not this
        # raise — it is the only in-flow detector of a genuinely failed teach, and it names the
        # mon and the move. `_guard("Teach Surf (Ch12c)")` would still catch a real failure one
        # segment later, but with no diagnostic. Deleting a guard because its failure was loud
        # is the pattern behind three reverts in one week.
        raise BotModeError(f"Teach flow finished but {_mon().species.name} does not know {target_move.name}.")
    context.message = f"Story: {_mon().species.name} learned {target_move.name}!"
    # ‼ THE `context.message` ABOVE IS UNOBSERVABLE AND CANNOT BE THE PROOF. `[STEP]` only
    # fires when the message CHANGES, and the next segment overwrites it immediately —
    # measured: `[STEP] '…learned…'` appears **0** times against 42 real teaches (positive
    # control: `got HM06 Rock Smash!` is also 0 on that surface). Without this event line the
    # fix has no success counter, only the absence of a failure counter — and "the error
    # stopped" is exactly how a suppressed feature looks identical to a working one.
    # ‼ `from modules import debug_logger` — the module is `modules/debug_logger.py` with a
    # module-level `event()`. I first wrote `from modules.debug import debug_logger`, which is
    # wrong, and the `except` below would have swallowed the ImportError and silently produced
    # no telemetry at all — the SECOND time in this one function that a bare except nearly hid
    # a broken import. Idiom copied from `story_mode.py:666`, which does it correctly.
    from modules import debug_logger

    # ‼ `ride_frames` is the RIDE loop's count (captured before the menus loop rebound `_f`);
    # `close_frames` is the menus-closed loop's. The old line printed the latter and called it
    # the former — see the capture note above. Both are reported now so the two can never be
    # confused again, and so the ride budget finally has a real distribution behind it.
    debug_logger.event(
        f"TEACH OK {_mon().species.name} learned {target_move.name} "
        f"ride_frames={_ride_frames} ride_exit={_ride_exit} stall_peak={_stall_peak} "
        f"post_select={_post_select_exit} close_frames={_f}"
    )


def get_rock_smash_hm() -> Generator:
    """Chapter 10a — HM06 Rock Smash from the Rock Smash Guy.

    INTENT: Route 111 south is HARD-gated by two breakable rocks at (18,101)/(19,100);
    HM06 unlocks the whole northern arc (Fiery Path → Fallarbor → Meteor Falls).
    HOW: Mauville SE house (city door (32,14) → MAUVILLE_CITY_HOUSE1); the Rock Smash
    Guy is STATIC — the wandering-talk helper degenerates to park-adjacent-and-talk.
    Receiving is gated only on RECEIVED_HM_ROCK_SMASH not being set (decomp-verified);
    field USE additionally needs BADGE03, which Ch9 already earned.
    GOAL/END: RECEIVED_HM_ROCK_SMASH set; back outside in Mauville."""
    from modules.memory import get_event_flag

    HOUSE = MapRSE.MAUVILLE_CITY_HOUSE1.value

    def _have() -> bool:
        try:
            return bool(get_event_flag("RECEIVED_HM_ROCK_SMASH"))
        except Exception:
            return False

    if _have():
        return
    context.message = "Story: getting HM06 Rock Smash in Mauville..."
    yield from wait_until_truly_controllable()
    yield from _exit_mauville_gym_live()  # resuming inside the gym (wattson_done) needs the live-grid exit
    if _map_group_number() != HOUSE:
        try:
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == HOUSE,
                MapRSE.MAUVILLE_CITY, MAUVILLE_ROCKSMASH_HOUSE_DOOR,
                tries=4, label="Rock Smash house",
            )
        except BotModeError as error:
            # ‼ `#24-abortrecoveryresiduals` (b). This fallback used to swallow a whiteout unwind. It was
            # correct only BY ACCIDENT — the call below happens to re-raise — and accidental correctness is
            # what this project's KI-67/KI-81 family is made of. `reraise_if_aborting` is LATCH-keyed, so
            # with no whiteout pending it changes nothing at all.
            reraise_if_aborting(error)
            yield from _navigate_riding_out(MapRSE.MAUVILLE_CITY, (32, 15))
            yield from _walk_through_warp("Up", MapRSE.MAUVILLE_CITY.value)
        yield from wait_until_truly_controllable()
    yield from _talk_to_wandering_npc(MapRSE.MAUVILLE_CITY_HOUSE1, 1, attempts=4)
    frames = 0
    while not _have():
        _check_abort()
        context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 6000:
            raise BotModeError("Rock Smash house: talked, but the HM was never received.")
        yield
    yield from _wait_until_cutscene_over("B")
    yield from _ride_out_all_scenes(quiet_frames=240)
    yield from _exit_small_interior()
    context.message = "Story: got HM06 Rock Smash!"


def _smash_rock(map_enum, approach_tile, face_dir: str) -> Generator:
    """Stand beside a breakable rock, face it, and Rock-Smash it — IDEMPOTENT and
    judged by the WORLD, not the script (user's 2026-07-23 hang + the batch-8 wedge,
    same signature): success is "the rock OBJECT is gone", checked live. The old
    A-ride waited for the smash script to end — but Rock Smash rolls a WILD
    ENCOUNTER (Geodude), and a battle-interrupted field script can leave the script
    context reading active forever, wedging every script-gated wait downstream.
    Also: a derail recovery re-runs the travel leg, so re-smashing an ALREADY-gone
    rock must be a no-op, not an A-press into whatever stands beyond it.
    Requires a party mon knowing Rock Smash + BADGE03 (Segments 9c/10b)."""
    from modules.map import get_map_objects

    dx, dy = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}[face_dir]
    rock_tile = (approach_tile[0] + dx, approach_tile[1] + dy)

    def _rock_present() -> bool:
        try:
            return any(
                tuple(o.current_coords) == rock_tile for o in get_map_objects()
            )
        except Exception:
            return True  # can't read objects — assume it's still there and try

    yield from _navigate_riding_out(map_enum, approach_tile)
    yield from wait_for_player_avatar_to_be_standing_still()
    if not _rock_present():
        return  # already smashed (recovery re-entry) — nothing to do
    for _attempt in range(3):
        _check_abort()
        context.emulator.press_button(face_dir)
        yield
        yield from wait_for_n_frames(6)
        # Watch the WORLD: the rock disappearing = success. A wild battle spawned by
        # the smash pauses this generator (the battle listener's controller runs on
        # top of us); when we resume, the judgment below still holds. Press A on a
        # FAST cadence: A opens 'This rock is breakable / Use ROCK SMASH?', answers
        # YES (default cursor), and advances the smash messages. ‼ Do NOT gate on
        # "script inactive" — the YES/NO prompt IS an active script, so gating there
        # meant A never answered it and each rock idled ~3800 frames (user's
        # 2026-07-23 slow-smash report). Extra A presses here are harmless: after the
        # rock breaks the tile is empty (no NPC to re-trigger).
        for _f in range(1200):
            _check_abort()
            if not _rock_present():
                # ‼ KI-16: EventScript_SmashRock's WaitForMovementFinish runs AFTER the
                # rock OBJECT is removed. Returning the instant the object is gone lets
                # the caller's next navigation start moving the player, which CANCELS
                # the crumble movement and strands the smash script active forever (the
                # deterministic wattson_done→Fiery-Path wedge). So wait for the field
                # SCRIPT to fully clear — pressing NOTHING, so we don't interrupt the
                # movement it's waiting on — before handing control back.
                for _s in range(600):
                    if not get_global_script_context().is_active:
                        break
                    yield
                yield from wait_for_n_frames(10)
                yield from wait_until_truly_controllable()
                return
            if _f % 10 == 0:
                context.emulator.press_button("A")
            yield
    raise BotModeError(f"Rock Smash: the rock at {rock_tile} never broke after 3 attempts.")


def travel_to_fallarbor() -> Generator:
    """Chapter 10c — Mauville → Fallarbor via Route 111 south, Fiery Path, Route 113.

    INTENT: open the northern arc (Fallarbor → Meteor Falls → Mt. Chimney next).
    HOW (§Ch10 route spec, decomp map.json sweep): Route 111 south to the staging tile
    below the twin rocks → smash (18,101) then (19,100) → north to the Route 112
    junction → Fiery Path south door at R112 (11,36) → tunnel (no trainers; the
    Strength boulders only gate side alcoves) → north exit → Route 112 north → Route
    113 west across the ash (Winstrate Victor, the Tori&Tia DOUBLE, and buried ninjas
    are on-path — the battle listener fights them inline) → Fallarbor, ending HEALED
    at its PC. R111-south's static plans can be walker-sealed at 1-wide chokes, so
    every leg is a riding navigation that retries around scenes.
    GOAL/END: healed in Fallarbor Town (checkpoint `fallarbor.ss1`)."""
    FALLARBOR = MapRSE.FALLARBOR_TOWN.value

    if _map_group_number() == FALLARBOR:
        return
    context.message = "Story: heading north — Route 111, Fiery Path, then Fallarbor..."
    yield from wait_until_truly_controllable()
    # Leg 1: to the staging tile below the twin rocks (crosses Victor's sight-line).
    yield from _navigate_riding_out(MapRSE.ROUTE111, (18, 102))
    # Leg 2: the rocks — (18,101) from below, then (19,100) from (19,101).
    yield from _smash_rock(MapRSE.ROUTE111, (18, 102), "Up")
    yield from _smash_rock(MapRSE.ROUTE111, (19, 101), "Up")
    # Leg 3: through the opened gap and west into Route 112, into the Fiery Path.
    yield from _navigate_riding_out(MapRSE.ROUTE111, (18, 99))
    yield from _enter_warp_by_navigation(
        lambda: _map_group_number() == MapRSE.FIERY_PATH.value,
        MapRSE.ROUTE112, (11, 36), tries=6, label="Fiery Path south door",
    )
    yield from wait_until_truly_controllable()
    # Leg 4: the tunnel, exiting the north door back onto upper Route 112.
    yield from _enter_warp_by_navigation(
        lambda: _map_group_number() == MapRSE.ROUTE112.value,
        MapRSE.FIERY_PATH, (26, 4), tries=6, label="Fiery Path north exit",
    )
    yield from wait_until_truly_controllable()
    # Leg 5: north to Route 113, then west across the ash to Fallarbor.
    yield from _navigate_riding_out(MapRSE.ROUTE113, (30, 8))
    yield from _navigate_riding_out(MapRSE.FALLARBOR_TOWN, (20, 10))
    context.message = "Story: reached Fallarbor Town!"
    yield from heal_in_pokemon_center(PokemonCenter.FallarborTown)


def do_meteor_falls_scene() -> Generator:
    """Chapter 11a — the Meteor Falls Magma-steals-the-meteorite CUTSCENE (no battle
    in Emerald; Archie cameos). Sets FLAG_HIDE_ROUTE_112_TEAM_MAGMA — which clears the
    grunts blocking the Mt. Chimney Cable Car — and VAR_METEOR_FALLS_STATE=1.

    HOW (§Ch11, decomp): Fallarbor → Route 114 west/south → the falls door at R114
    (8,63) → land inside at (27,18) → walk WEST along the ledge to the single trigger
    tile (14,18) (fires while VAR_METEOR_FALLS_STATE==0) → ride the scene out → back
    outside. Completion: the HIDE flag (tear-resistant majority read)."""
    from modules.memory import get_event_flag

    def _scene_done() -> bool:
        votes = 0
        for _ in range(3):
            try:
                if get_event_flag("HIDE_ROUTE_112_TEAM_MAGMA"):
                    votes += 1
            except Exception:
                pass
        return votes >= 2

    if _scene_done():
        return
    context.message = "Story: to Meteor Falls — Team Magma is up to something..."
    yield from wait_until_truly_controllable()
    if _map_group_number() != MapRSE.METEOR_FALLS_1F_1R.value:
        # (8,64) = the swept two-way staging tile directly below the falls door (8,63)
        # (the first pick (10,62) was unswept and unreachable — rule: sweep from the
        # REAL entry, here Route 114's Fallarbor-side edge (39,10)).
        yield from _navigate_riding_out(MapRSE.ROUTE114, (8, 64))
        yield from _walk_through_warp("Up", MapRSE.ROUTE114.value)
        yield from wait_until_truly_controllable()
    yield from _navigate_riding_out(MapRSE.METEOR_FALLS_1F_1R, (15, 18))
    # One step further west arms the (14,18) trigger; then ride the whole scene chain.
    frames = 0
    while not _scene_done():
        _check_abort()
        if get_global_script_context().is_active:
            yield from _wait_until_cutscene_over("B")
            yield from _ride_out_all_scenes(quiet_frames=300)
        else:
            context.emulator.press_button("Left")
            yield
        frames += 1
        if frames > 9000:
            raise BotModeError("Meteor Falls: the Magma scene never fired/completed.")
    context.message = "Story: Magma stole the meteorite — the Cable Car road is clear."
    # Leave the falls (back out the Route 114 door east of the trigger).
    yield from _enter_warp_by_navigation(
        lambda: _map_group_number() == MapRSE.ROUTE114.value,
        MapRSE.METEOR_FALLS_1F_1R, (27, 18), tries=6, label="Meteor Falls exit",
    )
    yield from wait_until_truly_controllable()


def ride_cable_car_to_summit() -> Generator:
    """Route to the Route 112 Cable Car station (from the Fallarbor side or already at
    the station) and ride UP to the Mt. Chimney summit station. Reusable: Segment 11b
    boards here to reach Maxie, and Segment 11c re-boards here to recover when a
    whiteout mid-descent respawns the team below the mountain (the cable car is a
    permanent transit — the attendant still rides you up after Magma is beaten).
    No-op if already on the summit side. Raises if boarding never succeeds."""
    STATION = MapRSE.ROUTE112_CABLE_CAR_STATION.value
    SUMMIT = MapRSE.MT_CHIMNEY_CABLE_CAR_STATION.value
    CHIM = MapRSE.MT_CHIMNEY.value

    if _map_group_number() in (CHIM, SUMMIT):
        return
    yield from wait_until_truly_controllable()
    if _map_group_number() != STATION:
        # EXPLICIT route from the Fallarbor side: R113 → R112 north → back SOUTH through
        # the Fiery Path tunnel → lower R112 → the station. Never let the planner take
        # the "short" Route 111 desert — it is Go-Goggles-gated by a script the
        # collision map can't see (overnight run: plan-failed at (11,44)).
        if _map_group_number() in (
            MapRSE.FALLARBOR_TOWN.value,
            MapRSE.FALLARBOR_TOWN_POKEMON_CENTER_1F.value,
            MapRSE.ROUTE114.value,
            MapRSE.ROUTE113.value,
        ):
            yield from _navigate_riding_out(MapRSE.ROUTE112, (22, 11))
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == MapRSE.FIERY_PATH.value,
                MapRSE.ROUTE112, (22, 10), tries=6, label="Fiery Path north door",
            )
            yield from wait_until_truly_controllable()
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == MapRSE.ROUTE112.value,
                MapRSE.FIERY_PATH, (26, 36), tries=6, label="Fiery Path south exit",
            )
            yield from wait_until_truly_controllable()
        yield from _navigate_riding_out(MapRSE.ROUTE112, (28, 28))
        yield from _walk_through_warp("Up", MapRSE.ROUTE112.value)
        yield from wait_until_truly_controllable()
    # BOARD: the attendant is at (6,6) (probed live — the old code approached (6,8) and
    # faced the EMPTY tile (6,7), so A hit nothing and boarding never fired: the user's
    # 2026-07-23 wedge). Talk from (6,7) facing Up; retry the whole approach a few times
    # because a wild encounter can fire on the walk up and leave us mid-station.
    boarded = False
    for _board_try in range(6):
        _check_abort()
        if _map_group_number() == SUMMIT:
            boarded = True
            break
        if _map_group_number() != STATION:
            yield from wait_until_truly_controllable()
            continue
        yield from _navigate_riding_out(STATION, (6, 7))
        yield from wait_for_player_avatar_to_be_standing_still()
        if tuple(get_player_avatar().local_coordinates) != (6, 7):
            continue  # a scene bumped us — re-approach
        context.emulator.press_button("Up")
        yield
        yield from wait_for_n_frames(6)
        context.emulator.press_button("A")
        yield
        for _f in range(3000):
            _check_abort()
            if _map_group_number() == SUMMIT:
                boarded = True
                break
            if _f % 3 == 0:
                context.emulator.press_button("A")  # ride YES + the CableCar special
            yield
        if boarded:
            break
    if not boarded:
        raise BotModeError("Cable Car: could not board / never arrived at the summit station.")
    yield from wait_until_truly_controllable()
    yield from _exit_small_interior()  # step out of the summit station onto Mt. Chimney
    yield from wait_until_truly_controllable()


def do_mt_chimney() -> Generator:
    """Chapter 11b — Cable Car up Mt. Chimney, beat the Magma chain, take the meteorite.

    HOW (§Ch11, decomp + in-state sweeps): R112 station door (28,27) [the pre-scene
    Magma blockers are HIDDEN once Ch11a's flag is set — sweeps must run from story
    states] → attendant at (6,6), talk from (6,7) facing Up, YES → the CableCar special rides up
    → summit station → out onto MT_CHIMNEY (17-18,36) → north through Grunt1 (13,16) /
    Grunt2 (9,16) sight-lines → Tabitha (12,11) → talk to MAXIE at (13,6) from (13,7)
    (trainerbattle_no_intro; Mightyena 24 / Zubat 24 / Camerupt 25 — water lead) →
    aftermath → TAKE THE METEORITE from the machine at (14,6) (authentic pickup;
    needed for TM27 later).
    GOAL/END: DEFEATED_EVIL_TEAM_MT_CHIMNEY (+ RECEIVED_METEORITE), controllable on
    the summit."""
    from modules.memory import get_event_flag

    CHIM = MapRSE.MT_CHIMNEY.value

    def _magma_beaten() -> bool:
        votes = 0
        for _ in range(3):
            try:
                if get_event_flag("DEFEATED_EVIL_TEAM_MT_CHIMNEY"):
                    votes += 1
            except Exception:
                pass
        return votes >= 2

    if _magma_beaten():
        return
    context.message = "Story: taking the Cable Car up Mt. Chimney..."
    yield from ride_cable_car_to_summit()
    # The Magma chain: navigating north crosses the grunt sight-lines (fought inline).
    yield from _navigate_riding_out(MapRSE.MT_CHIMNEY, (13, 17))
    yield from _navigate_riding_out(MapRSE.MT_CHIMNEY, (12, 12))
    yield from _navigate_riding_out(MapRSE.MT_CHIMNEY, (13, 7))
    context.emulator.press_button("Up")  # face Maxie (13,6)
    yield
    yield from wait_for_n_frames(6)
    frames = 0
    while not _magma_beaten():
        _check_abort()  # a loss whites out → recovery re-enters this segment
        context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 40000:
            raise BotModeError("Mt. Chimney: the Maxie battle never resolved.")
        yield
    yield from _wait_until_cutscene_over("B")
    yield from _ride_out_all_scenes()
    # The meteorite: machine at (14,6) — stand (14,7), face Up, take it.
    try:
        yield from _navigate_riding_out(MapRSE.MT_CHIMNEY, (14, 7))
        context.emulator.press_button("Up")
        yield
        yield from wait_for_n_frames(6)
        context.emulator.press_button("A")
        yield
        yield from _ride_out_scripted_scene("A", engage_timeout=180)
    except BotModeError as error:
        # ⛔ KI-81 / `#24-abortswallow`: a whiteout arrives here as a `BotModeError`
        # (`StoryAbort` is one) through `_navigate_riding_out`'s `_check_abort()` (`:266`).
        # Swallowing it makes `do_mt_chimney` RETURN AS IF IT SUCCEEDED, so the segment is
        # marked complete on a run that whited out. Latch-keyed, so it also catches an abort
        # already laundered into a plain `BotModeError` by an inner loop.
        reraise_if_aborting(error)
        pass  # the meteorite is a bonus — never fail the chapter on it
    context.message = "Story: Maxie beaten at Mt. Chimney (and the meteorite is ours)!"


def do_jagged_descent() -> Generator:
    """Chapter 11c — down Jagged Pass to Lavaridge Town, ending healed at its PC.

    HOW: summit south area (24,20) → the Jagged warps at (20-21,41) (ledge-hop descent
    — one-way SOUTH, our direction; in-state sweep OK) → Jagged Pass top (13-14,5) →
    descend the pass (trainers en route fought inline; ledges hop down) → bottom warps
    (14-15,40) → R112 lower-west (6-7,46) → WEST connection → LAVARIDGE_TOWN → PC.
    GOAL/END: healed in Lavaridge (checkpoint `lavaridge.ss1`)."""
    LAVA = MapRSE.LAVARIDGE_TOWN.value
    ON_MOUNTAIN = (
        MapRSE.MT_CHIMNEY.value,
        MapRSE.MT_CHIMNEY_CABLE_CAR_STATION.value,
        MapRSE.JAGGED_PASS.value,
    )

    if _map_group_number() == LAVA:
        return
    context.message = "Story: descending Jagged Pass to Lavaridge..."
    yield from wait_until_truly_controllable()
    # RECOVERY (user's 2026-07-23 run): a whiteout on a Jagged Pass trainer respawns
    # the team at Fallarbor — BELOW the one-way descent, with no way back up except the
    # cable car. Re-ride it to the summit, then descend as normal. (Jagged Pass is
    # one-way south, so we can never climb back to the top on foot.)
    if _map_group_number() not in ON_MOUNTAIN:
        yield from ride_cable_car_to_summit()
        yield from wait_until_truly_controllable()
    if _map_group_number() == MapRSE.MT_CHIMNEY.value:
        yield from _navigate_riding_out(MapRSE.MT_CHIMNEY, (21, 40))
        yield from _walk_through_warp("Down", MapRSE.MT_CHIMNEY.value)
        yield from wait_until_truly_controllable()
    if _map_group_number() == MapRSE.JAGGED_PASS.value:
        yield from _navigate_riding_out(MapRSE.JAGGED_PASS, (14, 39))
        yield from _walk_through_warp("Down", MapRSE.JAGGED_PASS.value)
        yield from wait_until_truly_controllable()
    yield from _navigate_riding_out(MapRSE.LAVARIDGE_TOWN, (9, 7))
    context.message = "Story: reached Lavaridge Town!"
    yield from heal_in_pokemon_center(PokemonCenter.LavaridgeTown)


def do_lavaridge_gym() -> Generator:
    """Chapter 11d — the Lavaridge trapdoor gym: fall through the right holes to
    Flannery, win the Heat Badge (BADGE04).

    HOW: the maze is SOLVED from the ROM's own map data, not explored. Each floor is
    scanned for holes (1F behaviour 104), geysers (B1F behaviour 41) and jump-south
    ledges (behaviour 59 — the hops that join the chambers); that yields a room graph
    whose edges are "fall through hole H, walk to geyser G". A backward BFS from
    Flannery's chamber gives the next move from wherever we actually are, so a battle
    knock-off or a surprise landing just re-plans. From the entrance the chain is four
    falls: (8,9)→(0,17), (0,10)→(0,6), (2,3)→(7,2), (10,6)→(12,12). Buried gym trainers
    pop en route and are fought inline. At Flannery's approach (13,10): face
    Up + A-ride until BADGE04_GET (Numel 24 / Slugma 24 / Camerupt 26 / Torkoal 29 —
    the caller preps a WATER lead; everything she has is 2× to Water)."""
    from collections import deque

    from modules.map import get_map_data
    from modules.memory import get_event_flag

    GYM1F = MapRSE.LAVARIDGE_TOWN_GYM_1F.value
    GYMB1F = MapRSE.LAVARIDGE_TOWN_GYM_B1F.value
    FLANNERY_APPROACH = (13, 10)  # below Flannery (13,9)

    def _badge() -> bool:
        votes = 0
        for _ in range(3):
            try:
                if get_event_flag("BADGE04_GET"):
                    votes += 1
            except Exception:
                pass
        return votes >= 2

    if _badge():
        return
    context.message = "Story: entering the Lavaridge Gym (mind the trapdoors)..."
    yield from wait_until_truly_controllable()
    if _map_group_number() not in (GYM1F, GYMB1F):
        # Town gym door = (5,15) (probed warp table); approach from below.
        yield from _navigate_riding_out(MapRSE.LAVARIDGE_TOWN, (5, 16))
        yield from _walk_through_warp("Up", MapRSE.LAVARIDGE_TOWN.value)
        yield from wait_until_truly_controllable()

    # THE MAZE, SOLVED FROM THE ROM'S OWN DATA (2026-07-23). Three facts, each
    # verified against the warp/metatile dump (tools/story-dev/lavaridge_gym_probe.py)
    # and the live trace in ch11d_run8.log:
    #   * 1F behaviour 104 (MB_LAVARIDGE_GYM_1F_WARP) = a HOLE; falling lands you on
    #     B1F at the SAME coordinate (every warp pair in this gym is same-coord).
    #   * B1F behaviour 41 (MB_LAVARIDGE_GYM_B1F_WARP) = a GEYSER; stepping on it
    #     launches you to 1F at the same coordinate. A warp tile whose behaviour is
    #     neither is INERT — it is only a landing pad, which is why landings never
    #     re-trigger.
    #   * ‼ Behaviour 59 (MB_JUMP_SOUTH) is a LEDGE: collision=1, but you hop it
    #     DOWNWARD onto the tile two below. The ledges are what join the chambers.
    #     The previous explorer treated them as walls, so it judged whole rooms
    #     exit-less and oscillated between two inert tiles until it ran out of rounds
    #     (ch11d_run9: wedged in the B1F (5,6)/(5,9) chamber, whose only way on is the
    #     y=11 ledge). With hops modelled, no chamber is a dead end and the chain to
    #     Flannery is 4 falls: (8,9)->(0,17), (0,10)->(0,6), (2,3)->(7,2), (10,6)->(12,12).
    # We DERIVE the plan live rather than hardcoding it, so a wrong turn (a battle
    # knock-off, an unexpected landing) simply re-plans from wherever we ended up.
    HOLE_MB, GEYSER_MB, LEDGE_MB = 104, 41, 59

    def _scan(gnum):
        md = get_map_data(gnum, (0, 0))
        w, h = md.map_size
        passable, behav, ledges = set(), {}, set()
        for y in range(h):
            for x in range(w):
                t = get_map_data(gnum, (x, y))
                mb = t._metatile_attributes[0] & 0x1FF  # high bits are the layer type
                behav[(x, y)] = mb
                if not t.collision:
                    passable.add((x, y))
                elif mb == LEDGE_MB:
                    ledges.add((x, y))
        return passable, behav, ledges

    def _steps(t, passable, ledges):
        """Walkable moves from `t`: the four neighbours, plus the one-way ledge hop
        (step Down onto a jump-south tile and land two tiles below)."""
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            n = (t[0] + dx, t[1] + dy)
            if n in passable:
                yield n
        landing = (t[0], t[1] + 2)
        if (t[0], t[1] + 1) in ledges and landing in passable:
            yield landing

    def _rooms(passable, ledges):
        """Chambers (no hops) + the set of tiles reachable FROM each chamber (hops
        included). Hops are one-way, so reachability is directed."""
        rooms, room_of = [], {}
        for start in sorted(passable):
            if start in room_of:
                continue
            comp, q = {start}, deque([start])
            while q:
                t = q.popleft()
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    n = (t[0] + dx, t[1] + dy)
                    if n in passable and n not in comp:
                        comp.add(n)
                        q.append(n)
            for t in comp:
                room_of[t] = len(rooms)
            rooms.append(comp)
        reach = {}
        for i, comp in enumerate(rooms):
            seen, q = set(comp), deque(comp)
            while q:
                t = q.popleft()
                for n in _steps(t, passable, ledges):
                    if n not in seen:
                        seen.add(n)
                        q.append(n)
            reach[i] = seen
        return rooms, room_of, reach

    pass1, behav1, ledge1 = _scan(GYM1F)
    passB, behavB, ledgeB = _scan(GYMB1F)
    rooms1, roomof1, reach1 = _rooms(pass1, ledge1)
    roomsB, roomofB, reachB = _rooms(passB, ledgeB)
    town_exits = {(13, 18), (14, 18)}
    holes = {t for t, mb in behav1.items() if mb == HOLE_MB and t not in town_exits}
    geysers = {t for t, mb in behavB.items() if mb == GEYSER_MB}

    def _room1_of(tile):
        """1F chamber a geyser lands you in. A couple of landing tiles read as
        collision (e.g. (4,16), elevation 0) — attribute those to a neighbour."""
        r = roomof1.get(tile)
        if r is not None:
            return r
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            r = roomof1.get((tile[0] + dx, tile[1] + dy))
            if r is not None:
                return r
        return None

    goal_room = _room1_of(FLANNERY_APPROACH)

    def _occupied():
        """Tiles held by an NPC (the gym guide, popped buried trainers). Four B1F
        geysers are the buried trainers' own tiles — never plan through those."""
        busy = set()
        try:
            from modules.map import get_map_objects as _gmo

            me = tuple(get_player_avatar().local_coordinates)
            for o in _gmo():
                for c in (getattr(o, "current_coords", None), getattr(o, "previous_coords", None)):
                    if c is not None and tuple(c) != me:
                        busy.add(tuple(c))
        except Exception:
            pass
        return busy

    def _room_distances(busy):
        """Backward BFS over the room graph: how many falls from each 1F chamber to
        Flannery's. Edge = fall through a reachable hole, walk to a reachable geyser."""
        edges = {}
        for r in range(len(rooms1)):
            outs = set()
            for hole in holes & reach1[r]:
                if hole in busy:
                    continue
                broom = roomofB.get(hole)
                if broom is None:
                    continue
                for g in geysers & reachB[broom]:
                    if g in busy:
                        continue
                    nr = _room1_of(g)
                    if nr is not None:
                        outs.add((nr, hole, g))
            edges[r] = outs
        dist = {goal_room: 0}
        changed = True
        while changed:  # tiny graph (7 rooms) — relax until stable
            changed = False
            for r, outs in edges.items():
                best = min((dist[nr] + 1 for nr, _h, _g in outs if nr in dist), default=None)
                if best is not None and best < dist.get(r, 1 << 30):
                    dist[r] = best
                    changed = True
        return dist, edges

    def _hold_walk_to(gnum, target, passable, ledges, avoid) -> Generator:
        """Walk to `target` with HELD input along a hop-aware BFS path, never stepping
        on a hazard tile in `avoid` (another hole/geyser would fire en route and throw
        the plan away). The standard navigator idles in this gym post-warp (the same
        latent upstream quirk as the post-badge Mauville exit), hence raw held input.
        Returns True on arrival OR on any map change (a hole/geyser fired)."""
        from modules.memory import GameState as _GS
        from modules.memory import get_game_state as _ggs

        target = tuple(target)
        start = tuple(get_player_avatar().local_coordinates)
        # NPCs are walls: the gym guide stands at (12,16), squarely on the shortest
        # path from the entrance to the first hole (run 10 stalled there), and the
        # buried trainers pop onto B1F tiles as you go.
        walkable = (passable - avoid - _occupied()) | {target}
        walkable.add(start)
        prev = {start: None}
        q = deque([start])
        while q:
            t = q.popleft()
            if t == target:
                break
            for n in _steps(t, walkable, ledges):
                if n not in prev:
                    prev[n] = t
                    q.append(n)
        if target not in prev:
            return False
        path, n = [], target
        while n is not None:
            path.append(n)
            n = prev[n]
        path.reverse()
        for nxt in path[1:]:
            if _map_group_number() != gnum:
                return True  # transitioned mid-walk
            px, py = get_player_avatar().local_coordinates
            delta = (nxt[0] - px, nxt[1] - py)
            # (0,2) is the ledge hop — same held direction, the avatar clears two tiles.
            d = {(0, -1): "Up", (0, 1): "Down", (0, 2): "Down", (-1, 0): "Left", (1, 0): "Right"}.get(delta)
            if d is None:
                return False  # drifted (battle knock-on) — the outer loop re-plans
            arrived = False
            for _f in range(150):
                _check_abort()
                if _ggs() is not _GS.OVERWORLD or get_global_script_context().is_active:
                    context.emulator.reset_held_buttons()
                    return False  # battle/scene — handled outside
                context.emulator.hold_button(d)
                yield
                if _map_group_number() != gnum:
                    context.emulator.reset_held_buttons()
                    return True
                if tuple(get_player_avatar().local_coordinates) == nxt:
                    arrived = True
                    break
            context.emulator.reset_held_buttons()
            if not arrived:
                return False
        return True

    def _recover() -> Generator:
        """A leg failed. Ride out a scene only if one is ACTUALLY running — run 10
        wedged for 18k frames B-riding a scene that never existed (the walk had merely
        been blocked by the gym guide), so an unconditional ride is a hang, not a
        recovery. Otherwise just settle and let the outer loop re-plan."""
        if get_global_script_context().is_active:
            yield from _ride_out_scripted_scene("B")
        else:
            yield from wait_for_n_frames(30)

    rounds = 0
    stalls = 0
    while not _badge():
        _check_abort()
        rounds += 1
        if rounds > 80:
            raise BotModeError("Lavaridge Gym: could not solve the trapdoor maze.")
        if stalls > 12:
            raise BotModeError("Lavaridge Gym: repeatedly could not walk the planned leg.")
        if get_global_script_context().is_active:
            yield from _ride_out_scripted_scene("B")
            continue
        yield from wait_until_truly_controllable()
        cur_floor = _map_group_number()
        if cur_floor not in (GYM1F, GYMB1F):
            yield from wait_for_n_frames(30)
            continue
        busy = _occupied()
        dist, edges = _room_distances(busy)
        here = tuple(get_player_avatar().local_coordinates)

        if cur_floor == GYM1F:
            room = _room1_of(here)
            if room == goal_room or FLANNERY_APPROACH in reach1.get(room, ()):
                # On (or able to walk onto) Flannery's platform — challenge her.
                walked = yield from _hold_walk_to(
                    GYM1F, FLANNERY_APPROACH, pass1, ledge1, holes - {FLANNERY_APPROACH}
                )
                if not walked or tuple(get_player_avatar().local_coordinates) != FLANNERY_APPROACH:
                    stalls += 1
                    yield from _recover()
                    continue
                context.emulator.press_button("Up")
                yield
                frames = 0
                while not _badge():
                    _check_abort()
                    context.emulator.press_button("B" if frames % 3 else "A")
                    frames += 1
                    if frames > 40000:
                        raise BotModeError("Lavaridge Gym: the Flannery challenge never resolved.")
                    yield
                break
            # Otherwise fall through the hole that gets us a room closer.
            options = [e for e in edges.get(room, ()) if e[0] in dist and dist[e[0]] < dist.get(room, 1 << 30)]
            if not options:
                yield from wait_for_n_frames(30)
                continue
            target = min(options, key=lambda e: dist[e[0]])[1]
            avoid = (holes | {t for t in behav1 if behav1[t] == GEYSER_MB}) - {target}
            context.message = f"Story: Lavaridge maze — dropping through the hole at {target}..."
            walked = yield from _hold_walk_to(GYM1F, target, pass1, ledge1, avoid)
        else:
            # B1F: ride the reachable geyser that lands us in the best 1F chamber.
            broom = roomofB.get(here)
            cands = []
            for g in geysers & reachB.get(broom, set()):
                if g in busy or g == here:
                    continue  # `here` is our landing tile — re-entering it just undoes the fall
                nr = _room1_of(g)
                if nr is not None and nr in dist:
                    cands.append((dist[nr], abs(g[0] - here[0]) + abs(g[1] - here[1]), g))
            if not cands:
                yield from wait_for_n_frames(30)
                continue
            target = min(cands)[2]
            context.message = f"Story: Lavaridge maze — riding the geyser at {target}..."
            walked = yield from _hold_walk_to(GYMB1F, target, passB, ledgeB, geysers - {target})
        if not walked:
            stalls += 1
            yield from _recover()
            continue
        stalls = 0
        if _map_group_number() == cur_floor:
            # Arrived but nothing fired yet — a geyser erupts a beat after you land on
            # it (and some cycle slowly), so give it a generous window before re-planning.
            for _f in range(900):
                _check_abort()
                yield
                if _map_group_number() != cur_floor:
                    break
        yield from wait_for_n_frames(45)  # let the fall / landing settle
    yield from _wait_until_cutscene_over("B")
    context.message = "Story: HEAT BADGE earned — Gym 4 (Flannery) beaten!"


def travel_lavaridge_to_petalburg() -> Generator:
    """Chapter 12 travel — the long overland backtrack from Lavaridge to Petalburg for
    Norman (Gym 5).

    ROUTE (static-probed 2026-07-24, ch12_static_recon*.py — CORRECTS the 2026-07-23
    "must go via the Fiery Path" note, which misread the door topology: the Fiery
    tunnel connects lower Route 112 to the ROUTE-113-side section, so it is useless
    for southbound travel; and the direct corridor is fine): Lavaridge → Route 112
    (descend the one-way ledges SOUTH — our direction; course y47–51) → Route 111 at
    the west junction (y67–99 — the SAME corridor Ch10's travel_to_fallarbor walked
    northbound at ground truth, so the Go-Goggles desert, which seals y≈61–88 further
    NORTH, never touches it) → smash the twin-rocks choke from the NORTH side (rocks
    RESPAWN on map reload, so Ch10's smash is gone; column 18 needs only the (18,101)
    rock: stage (18,100), face Down; _smash_rock is idempotent if it's already open)
    → Route 111 south (y102–139) → Mauville. Then: Route 117 (forced doubles — the
    listener attack-throughs) → Verdanturf → Rusturf Tunnel (warp-linked (8,1)↔(4,10);
    Ch10's boulders also respawn — the tunnel legs ride _enter_warp_by_navigation and
    the interior needs no boulder removal for the through-path) → Route 116 → Rustboro
    → Route 104 north → Petalburg Woods (N→S, no Cut) → Route 104 south → Petalburg.
    Progress-gated + idempotent legs; GOAL/END: in Petalburg City."""
    PETALBURG = MapRSE.PETALBURG_CITY.value

    if _map_group_number() == PETALBURG:
        return
    context.message = "Story: heading to Petalburg — the long road to Norman..."
    yield from wait_until_truly_controllable()

    # Leg 1 (only when starting from the Lavaridge side): descend to Route 111 above
    # the twin rocks, re-smash the (18,101) rock from the north, and continue south.
    # Gated by map so a mid-route resume (Mauville onward) skips it entirely.
    if _map_group_number() in (
        MapRSE.LAVARIDGE_TOWN.value,
        MapRSE.ROUTE112.value,
        MapRSE.ROUTE111.value,
    ):
        context.message = "Story: to Petalburg — down Route 112's ledges to Route 111..."
        yield from _navigate_riding_out(MapRSE.ROUTE111, (18, 99))
        yield from _smash_rock(MapRSE.ROUTE111, (18, 100), "Down")

    # The remaining legs, in order: (target map, a SAFE interior tile — never a
    # warp/ledge tile). A leg is skipped once we are already past it (idempotent
    # resume): we only run a leg while we are on an EARLIER map than its target.
    LEGS = [
        (MapRSE.MAUVILLE_CITY, (19, 6), "Mauville City"),
        (MapRSE.ROUTE117, (30, 8), "Route 117"),
        (MapRSE.VERDANTURF_TOWN, (16, 9), "Verdanturf Town"),
    ]
    # ‼ EVERY overworld corridor map must be ranked (ch12_run1, 2026-07-24): a derail
    # in Petalburg Woods resumed with _rank(WOODS) == -1 ("not past anything") and the
    # travel re-ran the MAUVILLE leg BACKWARDS from the Woods until Manual. Unknown
    # maps (interiors) still rank -1 = run all legs, which is right for whiteout
    # respawns at earlier towns' Poké Centers.
    order = [
        MapRSE.LAVARIDGE_TOWN.value, MapRSE.ROUTE112.value, MapRSE.ROUTE111.value,
        MapRSE.MAUVILLE_CITY.value, MapRSE.ROUTE117.value, MapRSE.VERDANTURF_TOWN.value,
        MapRSE.RUSTURF_TUNNEL.value, MapRSE.ROUTE116.value, MapRSE.RUSTBORO_CITY.value,
        MapRSE.ROUTE104.value, MapRSE.PETALBURG_WOODS.value, MapRSE.PETALBURG_CITY.value,
    ]

    def _rank(gnum) -> int:
        return order.index(gnum) if gnum in order else -1

    for map_enum, tile, label in LEGS:
        _check_abort()
        if _rank(_map_group_number()) >= _rank(map_enum.value) and _map_group_number() != MapRSE.LAVARIDGE_TOWN.value:
            continue  # already past this leg (resume)
        context.message = f"Story: to Petalburg — {label}..."
        yield from _navigate_riding_out(map_enum, tile, tries=8)
        yield from wait_until_truly_controllable()

    # Verdanturf → Rusturf Tunnel → Route 116 (warp-linked, not edge connections).
    if _map_group_number() == MapRSE.VERDANTURF_TOWN.value:
        context.message = "Story: to Petalburg — through Rusturf Tunnel..."
        yield from _enter_warp_by_navigation(
            lambda: _map_group_number() == MapRSE.RUSTURF_TUNNEL.value,
            MapRSE.VERDANTURF_TOWN, (8, 1), tries=6, label="Rusturf Tunnel (Verdanturf door)",
        )
        yield from wait_until_truly_controllable()
    if _map_group_number() == MapRSE.RUSTURF_TUNNEL.value:
        # The WANDA-QUEST rock wall (probed 2026-07-24): two breakable rocks at
        # (24,5)/(24,4) seal the tunnel's middle until the reunion quest opens it
        # (their flags 931/932 are PERMANENT — once smashed, open forever; a resume
        # after the quest skips both smashes via _smash_rock's idempotence). Wanda
        # (25,4) and her boyfriend (23,5) flank the wall — smash row 5 first from
        # (25,5) (open), ride out the reunion scene, then row 4 if it still blocks.
        context.message = "Story: to Petalburg — opening the Rusturf wall (Wanda's quest)..."
        yield from _smash_rock(MapRSE.RUSTURF_TUNNEL, (25, 5), "Left")
        yield from _ride_out_all_scenes(quiet_frames=300)  # the couple's reunion
        try:
            yield from _smash_rock(MapRSE.RUSTURF_TUNNEL, (24, 5), "Up")  # (24,4) from below
        except BotModeError as error:
            # ⛔⛔ KI-81 / `#24-abortswallow` — THE TEXTBOOK LAUNDERED DIAGNOSIS. This handler
            # INTERPRETS any failure as "the rock is gone"; after a whiteout that reading is
            # fabricated, and the run then walks into a still-sealed wall and raises "cannot
            # reach Route 116" — a confident, plausible, WRONG cause. `_smash_rock` reaches
            # `_check_abort()` via `_navigate_riding_out`, so the abort genuinely arrives here.
            reraise_if_aborting(error)
            pass  # row 4 already open (scene cleared it / rock gone) — continue
        yield from _enter_warp_by_navigation(
            lambda: _map_group_number() == MapRSE.ROUTE116.value,
            MapRSE.RUSTURF_TUNNEL, (4, 10), tries=6, label="Rusturf Tunnel (Route 116 door)",
        )
        yield from wait_until_truly_controllable()

    # Route 116 → Rustboro → Route 104 north.
    if _map_group_number() == MapRSE.ROUTE116.value:
        context.message = "Story: to Petalburg — Route 116 → Rustboro..."
        # ⛔⛔ (23,55) WAS A TILE INSIDE RUSTBORO'S FENCED SOUTH-EAST DEAD-END LANE (fixed
        # 2026-09-11, user-reported as a visible detour). That lane has NO entrance from Rustboro:
        # its only door is `ROUTE104 (33,0) -> RUSTBORO (33,59)`. So the planner, behaving
        # perfectly correctly, walked us OUT of the city at (19,59), EAST along Route 104's top
        # row, back UP into Rustboro at (33,59), and west into the lane — then the very next
        # statement below walked all the way back out again.
        # MEASURED with `probe_path_dump.py` on `rustboro.ss1`, from (20,42):
        #     -> (23,55)  **52 waypoints, 15 of them on ROUTE104** (it leaves the city)
        #     -> (19,58)  **17 waypoints, 0 on ROUTE104**, and it never enters the lane box
        # ‼ The X Defend item ball sits at the lane's terminus (36,51), ~16 steps further on —
        # which is exactly why this looked like "it goes for the item and backtracks". It never
        # wanted the item; it was sent to a tile that only that lane contains.
        # ⇒ (19,58) is the south-exit approach this hop actually needs: on the direct way to the
        # next waypoint (ROUTE104 (24,12)), inside the city, no excursion.
        yield from _navigate_riding_out(MapRSE.RUSTBORO_CITY, (19, 58), tries=8)
        yield from wait_until_truly_controllable()
    if _map_group_number() == MapRSE.RUSTBORO_CITY.value:
        yield from _navigate_riding_out(MapRSE.ROUTE104, (24, 12), tries=8)
        yield from wait_until_truly_controllable()

    # Route 104 north → Petalburg Woods → Route 104 south-east → Petalburg.
    # Route 104 is ONE map split by the Woods band (rows 31-37 are solid wall; door
    # pairs at y30 north / y38+y42 south — mapfacts 2026-07-24), so which half we are
    # on is decided by y (< 38 = north side, the wall rows being unstandable).
    if (
        _map_group_number() == MapRSE.ROUTE104.value
        and get_player_avatar().local_coordinates[1] < 38
    ):
        context.message = "Story: to Petalburg — through Petalburg Woods..."
        yield from _navigate_riding_out(MapRSE.PETALBURG_WOODS, (26, 5), tries=8)
        yield from wait_until_truly_controllable()
    if _map_group_number() == MapRSE.PETALBURG_WOODS.value:
        # ‼ Exit via the SOUTH-EAST door (36,38) EXPLICITLY (ch12_run2): the warp
        # graph is region-blind on the split Route 104 — asked for "Route 104" it
        # exited the NORTH door back onto the sealed Rustboro half. The SE door
        # lands at R104 (32,42), the Petalburg-side section (probed pathable to the
        # city). Interior southbound is one-way-ledge but statically pathable from
        # the north-door landing to every south door.
        yield from _enter_warp_by_navigation(
            lambda: (
                _map_group_number() == MapRSE.ROUTE104.value
                and get_player_avatar().local_coordinates[1] >= 39
            ),
            MapRSE.PETALBURG_WOODS, (36, 38), tries=8, label="Petalburg Woods SE exit",
        )
        yield from wait_until_truly_controllable()
    if _map_group_number() == MapRSE.ROUTE104.value:
        yield from _navigate_riding_out(MapRSE.PETALBURG_CITY, (15, 10), tries=8)
        yield from wait_until_truly_controllable()

    context.message = "Story: reached Petalburg City — Norman's gym awaits."


# The Petalburg Gym left-door speedrun chain (static warp table, ch12 recon
# 2026-07-24 — ch12_static_recon*.py / petalburg_gym_probe.py). Each step:
# (room trainer tile or None, internal door tile to step on, landing tile).
# Doors are VAR_PETALBURG_GYM_STATE-gated: a room's doors open only after its
# trainer is beaten, so a closed door = "engage the trainer first".
PETALBURG_GYM_CHAIN = [
    (None, (1, 105), (7, 85)),     # entrance room (no trainer) → Randall's room
    ((4, 81), (1, 79), (7, 46)),   # beat Randall → Parker's room
    ((4, 42), (7, 40), (1, 20)),   # beat Parker → Jody's room
    ((4, 16), (7, 14), (1, 7)),    # beat Jody → Norman's room
]


def do_petalburg_gym() -> Generator:
    """Chapter 12b — Petalburg Gym: beat NORMAN for the Balance Badge (BADGE05) and
    collect HM03 Surf via the Wally's-dad handoff.

    INTENT: clear Gym 5 and unlock the Surf arc (Ch13+).
    STORY CONDITION: in Petalburg City with 4 badges (the gym only opens then).
    HOW IT WORKS: enter via the city door (15,8) → walk the LEFT-DOOR speedrun chain
    (PETALBURG_GYM_CHAIN; three trainers — Randall/Parker/Jody, ~L26-27 — engaged
    via sight-line or a direct talk when their door stays shut) → challenge Norman
    (4,2) from (4,3) (Spinda27/Vigoroth27/Linoone29/Slaking31 — Slaking's TRUANT
    loafs every other turn; the attack-through strategy rides it) → BADGE05_GET +
    TM42 → then STEP DOWN in Norman's room: the VAR_PETALBURG_GYM_STATE==6 coord
    trigger walks Wally's Dad in and WARPS us to Wally's house, whose auto-script
    hands over HM03 Surf (RECEIVED_HM_SURF). ‼ Never leave the gym any other way
    after the badge — skipping the trigger soft-locks Surf.
    GOAL/END STATE: BADGE05_GET + RECEIVED_HM_SURF (in Wally's house)."""
    from modules.memory import get_event_flag

    GYM = MapRSE.PETALBURG_CITY_GYM

    if get_event_flag("RECEIVED_HM_SURF"):
        return
    context.message = "Story: entering Petalburg Gym to challenge Norman..."
    if _map_group_number() != GYM.value:
        yield from _enter_warp_by_navigation(
            lambda: _map_group_number() == GYM.value,
            MapRSE.PETALBURG_CITY, (15, 8), tries=6, label="Petalburg Gym door",
        )
        yield from wait_until_truly_controllable()

    # Walk the door chain bottom→top. ‼ The doors are NOT walk-through tiles: each
    # is a collision-blocked SIGN script (decomp: PetalburgCity_Gym_EventScript_
    # *RoomDoor) — face it, press A, answer YES to its "go through?" prompt, and the
    # script WARPDOORs you to the landing. Later doors answer "locked" until their
    # gating trainer is beaten (Confusion←Randall, LeftStrength←Parker, GymLeaders←
    # Jody); the entrance pair needs only VAR_PETALBURG_GYM_STATE ≥ 6 (4 badges).
    # Idempotent on resume: a step is skipped when we are already at/above its
    # landing row (y decreases while ascending); beaten trainers stay beaten.
    if not get_event_flag("BADGE05_GET"):
        for trainer_tile, door, landing in PETALBURG_GYM_CHAIN:
            _check_abort()
            if _map_group_number() == GYM.value and get_player_avatar().local_coordinates[1] <= landing[1]:
                continue  # already past this wall
            rounds = 0
            while not (
                _map_group_number() == GYM.value
                and get_player_avatar().local_coordinates[1] <= landing[1]
            ):
                _check_abort()
                rounds += 1
                if rounds > 12:
                    raise BotModeError(f"Petalburg Gym: never got through the door at {door}.")
                if trainer_tile is not None and rounds >= 2:
                    # The door answered "locked" → the room's trainer isn't beaten
                    # yet. Stand below them and talk — the battle listener fights it.
                    try:
                        yield from navigate_to_anywhere(
                            GYM, (trainer_tile[0], trainer_tile[1] + 1),
                            avoid_encounters=True, avoid_scripted_events=False,
                        )
                        yield from ensure_facing_direction("Up")
                        context.emulator.press_button("A")
                        yield from wait_for_n_frames(30)
                    except BotModeError:
                        pass  # their sight-line battle interrupted the walk — fine
                    yield from _ride_out_all_scenes(quiet_frames=240)
                    yield from wait_until_truly_controllable()
                # Approach the tile BELOW the door sign and interact.
                try:
                    yield from navigate_to_anywhere(
                        GYM, (door[0], door[1] + 1),
                        avoid_encounters=True, avoid_scripted_events=False,
                    )
                except BotModeError:
                    # A sight-line battle interrupted the approach — ride and retry.
                    yield from _ride_out_scripted_scene("B")
                    yield from wait_until_truly_controllable()
                    continue
                yield from wait_until_truly_controllable()
                if tuple(get_player_avatar().local_coordinates) != (door[0], door[1] + 1):
                    continue  # got bumped — re-approach
                yield from ensure_facing_direction("Up")
                # A opens the sign's msgbox; A again advances it; the YES/NO cursor
                # defaults to YES, so A confirms and the warpdoor fires. Bounded
                # ride: judge by ARRIVAL at/above the landing row (a "locked"
                # answer leaves us in place → the loop engages the trainer next).
                for _f in range(600):
                    _check_abort()
                    if get_player_avatar().local_coordinates[1] <= landing[1]:
                        break
                    if _f % 10 == 0:
                        context.emulator.press_button("A")
                    yield
                yield from wait_until_truly_controllable()

        # Challenge Norman from (4,3), facing up; ride the whole battle + badge chat.
        context.message = "Story: challenging NORMAN (Gym 5)..."
        rounds = 0
        while tuple(get_player_avatar().local_coordinates) != (4, 3) or _map_group_number() != GYM.value:
            _check_abort()
            rounds += 1
            if rounds > 10:
                raise BotModeError("Petalburg Gym: could not reach the challenge tile below Norman.")
            try:
                yield from navigate_to_anywhere(GYM, (4, 3), avoid_encounters=True, avoid_scripted_events=False)
            except BotModeError:
                yield from _ride_out_scripted_scene("B")
        yield from ensure_facing_direction("Up")
        frames = 0
        while not get_event_flag("BADGE05_GET"):
            _check_abort()  # a whiteout unwinds to the defeat recovery
            context.emulator.press_button("B" if frames % 3 else "A")
            frames += 1
            if frames > 40000:
                raise BotModeError("Petalburg Gym: the Norman challenge never resolved to a badge.")
            yield
        yield from _wait_until_cutscene_over("B")
        context.message = "Story: BALANCE BADGE earned — Gym 5 (Norman) beaten!"

    # HM03 Surf handoff (decomp-verified 2026-07-24): FULLY AUTOMATIC — the Norman
    # defeat script itself walks Wally's Dad in, warps us out of the gym, leads to
    # Wally's house, and hands over HM03 (RECEIVED_HM_SURF). Nothing to trigger;
    # just ride the whole scripted chain out. B in the brief controllable gaps
    # advances any lingering text and can never move us onto a stray warp.
    context.message = "Story: riding the Wally's-dad scene — HM03 Surf incoming..."
    frames = 0
    while not get_event_flag("RECEIVED_HM_SURF"):
        _check_abort()
        if get_global_script_context().is_active or not player_avatar_is_controllable():
            yield from _wait_until_cutscene_over("B")
        else:
            context.emulator.press_button("B")
            yield
        frames += 1
        if frames > 15000:
            raise BotModeError("Petalburg Gym: the Surf handoff (Wally's dad) never fired.")
    yield from _wait_until_cutscene_over("B")
    yield from wait_until_truly_controllable()
    context.message = "Story: HM03 Surf received!"


def travel_to_fortree() -> Generator:
    """Chapter 13a travel — Mauville → Route 118 (SURF the river) → Route 119 north →
    Fortree City, healing at its PC. ‼ Requires Surf taught (Segment 12c) — the
    pathfinder plans water legs natively once BADGE05 + a Surf mon hold (§Ch13 spec,
    flags audited 2026-07-24). ⚠ SURF CROSSING NOT YET LIVE-VALIDATED — first run
    from a post-Surf save must watch the R118 east-bank Steven scene (ride it) and
    the crossing itself.

    Progress-gated riding legs (the Ch12a pattern): a leg is skipped once we are on
    a LATER map. Route 119's mid-route content (Weather Institute, bridge grunts,
    rival) is handled by the FOLLOWING segments — this travel stops at Fortree only
    if the road is already clear; otherwise the institute/rival segments run first
    from wherever the navigation was interrupted (they gate on their own flags)."""
    FORTREE = MapRSE.FORTREE_CITY.value

    if _map_group_number() == FORTREE:
        return
    context.message = "Story: the Surf arc — east to Route 118, then north to Fortree..."
    yield from wait_until_truly_controllable()

    # ‼ EVERY Fortree-side map must be ranked at/after FORTREE (the Ch12a Woods
    # lesson, re-learned on ROUTE120 in the r8 replay: an unranked map = rank -1 =
    # "run every leg" = a backwards march to Mauville and a NO-PATH Manual).
    order = [
        MapRSE.PETALBURG_CITY.value, MapRSE.ROUTE102.value, MapRSE.ROUTE110.value,
        MapRSE.MAUVILLE_CITY.value, MapRSE.ROUTE118.value, MapRSE.ROUTE119.value,
        MapRSE.FORTREE_CITY.value,
        MapRSE.FORTREE_CITY_POKEMON_CENTER_1F.value, MapRSE.FORTREE_CITY_GYM.value,
        MapRSE.ROUTE120.value,
    ]
    LEGS = [
        (MapRSE.MAUVILLE_CITY, (19, 6), "Mauville City"),
        (MapRSE.ROUTE118, (20, 10), "Route 118 (west bank)"),
        (MapRSE.ROUTE118, (49, 8), "Route 118 (across the water)"),
        (MapRSE.ROUTE119, (25, 125), "Route 119 (south)"),
        # (6,33) = the Weather Institute door row — statically pathable from the south
        # leg with Surf (probed 2026-07-24 on the live wedge state; the earlier (8,30)
        # pick was an unreachable pocket and cost run 1 a Manual).
        (MapRSE.ROUTE119, (6, 33), "Route 119 (Weather Institute)"),
        (MapRSE.FORTREE_CITY, (5, 7), "Fortree City"),
    ]

    def _rank(gnum) -> int:
        return order.index(gnum) if gnum in order else -1

    from modules.memory import get_event_flag

    def _bridge_open() -> bool:
        try:
            return bool(get_event_flag("HIDE_ROUTE_119_TEAM_AQUA"))
        except Exception:
            return False

    for map_enum, tile, label in LEGS:
        _check_abort()
        # ‼ The road past the Weather Institute is STORY-BLOCKED until Shelly is
        # beaten (the bridge grunts (13,33-34) despawn with the HIDE flag) — the
        # Fortree leg must yield to the institute segment instead of burning its
        # retries into a Manual (ch13_run2). Stop at the institute row; _play's
        # Segment 13b owns the next step and re-calls this travel afterwards.
        if map_enum.value == MapRSE.FORTREE_CITY.value and not _bridge_open():
            context.message = "Story: the bridge ahead is blocked — the Weather Institute first."
            return
        cur_rank = _rank(_map_group_number())
        tgt_rank = _rank(map_enum.value)
        if cur_rank > tgt_rank:
            continue  # already past this leg (resume)
        if cur_rank == tgt_rank and map_enum.value != MapRSE.ROUTE118.value and map_enum.value != MapRSE.ROUTE119.value:
            continue  # same non-split map — the next leg handles the move onward
        context.message = f"Story: to Fortree — {label}..."
        yield from _navigate_riding_out(map_enum, tile, tries=8)
        yield from wait_until_truly_controllable()

    if _map_group_number() == FORTREE:
        context.message = "Story: reached Fortree City!"
        yield from heal_in_pokemon_center(PokemonCenter.FortreeCity)


def do_weather_institute() -> Generator:
    """Chapter 13b — clear the Weather Institute (Shelly) and accept Castform.

    STORY CONDITION: on Route 119 with the institute unclear. Door at R119 (6,32);
    interior grunts + SHELLY (Carvanha/Mightyena L28) are fought inline by the
    listener while navigating to the top floor. Completion:
    `HIDE_ROUTE_119_TEAM_AQUA` (also despawns the bridge grunts (13,33-34)).
    Castform is offered afterwards (`RECEIVED_CASTFORM`) — accepted if a party slot
    is free, politely declined (B) otherwise. ⚠ interior tiles are build-time
    leads — validate on the first post-Surf run."""
    from modules.memory import get_event_flag

    def _cleared() -> bool:
        try:
            return bool(get_event_flag("HIDE_ROUTE_119_TEAM_AQUA"))
        except Exception:
            return False

    if _cleared():
        return
    context.message = "Story: Team Aqua is squatting in the Weather Institute — evicting them..."
    yield from wait_until_truly_controllable()
    # Enter via the R119 door (6,32) → interior 1F (9,12).
    yield from _enter_warp_by_navigation(
        lambda: _map_group_number() not in (MapRSE.ROUTE119.value,),
        MapRSE.ROUTE119, (6, 32), tries=6, label="Weather Institute door",
    )
    yield from wait_until_truly_controllable()
    # Interior sweep (structure probed 2026-07-24 after run 3 wandered 1F for 130k
    # frames): 1F stairs at (17,1) → 2F (17,1); SHELLY at 2F (4,6), grunts at 1F
    # (15,3)/(10,5) and 2F (15,6)/(10,8)/(19,6) — all flag-890 (they despawn with
    # the clear). Walk 1F → stairs → 2F → stand beside Shelly (5,6) → talk; the
    # listener fights every engagement; ride everything until the HIDE flag sets.
    frames = 0
    while not _cleared():
        _check_abort()
        if get_global_script_context().is_active or not player_avatar_is_controllable():
            yield from _wait_until_cutscene_over("B")
            frames += 100
            continue
        cur = _map_group_number()
        try:
            if cur == MapRSE.ROUTE119_WEATHER_INSTITUTE_1F.value:
                # Up the stairs — the on-path grunts engage inline.
                yield from navigate_to_anywhere(
                    MapRSE.ROUTE119_WEATHER_INSTITUTE_1F, (17, 1),
                    avoid_encounters=True, avoid_scripted_events=False,
                )
            elif cur == MapRSE.ROUTE119_WEATHER_INSTITUTE_2F.value:
                yield from navigate_to_anywhere(
                    MapRSE.ROUTE119_WEATHER_INSTITUTE_2F, (5, 6),
                    avoid_encounters=True, avoid_scripted_events=False,
                )
                yield from ensure_facing_direction("Left")
                context.emulator.press_button("A")
                yield from wait_for_n_frames(30)
                yield from _ride_out_all_scenes(quiet_frames=300)
            else:
                # Bumped back outside (whiteout respawn / recovery) — re-enter.
                yield from _enter_warp_by_navigation(
                    lambda: _map_group_number() in (
                        MapRSE.ROUTE119_WEATHER_INSTITUTE_1F.value,
                        MapRSE.ROUTE119_WEATHER_INSTITUTE_2F.value,
                    ),
                    MapRSE.ROUTE119, (6, 32), tries=6, label="Weather Institute door",
                )
        except BotModeError as error:
            # ‼ `#24-abortrecoveryresiduals` (b). This fallback used to swallow a whiteout unwind. It was
            # correct only BY ACCIDENT — the call below happens to re-raise — and accidental correctness is
            # what this project's KI-67/KI-81 family is made of. `reraise_if_aborting` is LATCH-keyed, so
            # with no whiteout pending it changes nothing at all.
            reraise_if_aborting(error)
            yield from _ride_out_scripted_scene("B")
        frames += 200
        if frames > 80000:
            raise BotModeError("Weather Institute: never cleared (Shelly not beaten?).")
    context.message = "Story: Weather Institute cleared!"
    # Castform offer rides on the aftermath dialogue — the rider answers YES-shaped
    # prompts with A only when a real choice box is up (party-full = B declines).
    yield from _ride_out_all_scenes(quiet_frames=300)
    # Leave the building (back out the entrance door).
    yield from normalize_to_overworld()


def _clear_stale_battle_message() -> Generator:
    """A mid-navigation battle can leave its last message ('X gained EXP', 'got $N',
    'Got away safely!') PARKED on screen — input-blocking, A-only-dismissable (the
    KI-15 wedge family). Before any talk ritual (face + A at an NPC), clear it:
    press A only while a message is genuinely waiting with NO field script running —
    a state in which A cannot start a conversation because the message consumes it.
    Bounded; a no-op when nothing is parked."""
    for _try in range(3):
        if not (
            is_waiting_for_input()
            and not get_global_script_context().is_active
            and not get_immediate_script_context().is_active
        ):
            return
        context.emulator.press_button("A")
        yield
        yield from wait_for_n_frames(20)


def _hold_walk_route(steps, *, stop_on_script: bool = True, per_leg_bound: int = 900) -> Generator:
    """Walk a fixed route with HELD input: `steps` = [(direction, (x,y)), ...] — hold
    each direction until the tile is reached. For tiles the planner is blind to
    (BRIDGES: their dual-elevation reads as walls statically — Route 119's spans,
    2026-07-24 — same family as the Lavaridge gym's post-warp idling). Breaks (and
    releases input) the moment a field script fires when ``stop_on_script`` — walking
    INTO a coord trigger is often the goal. Bounded per leg."""
    try:
        for direction, tgt in steps:
            # release the PREVIOUS leg's held direction — two directions held at
            # once make the game keep the first (run 7: Up stayed held, so the
            # Right leg bumped Up into the river for 300k frames).
            context.emulator.reset_held_buttons()
            tgt = tuple(tgt)
            frames = 0
            while tuple(get_player_avatar().local_coordinates) != tgt:
                _check_abort()
                if stop_on_script and get_global_script_context().is_active:
                    return
                context.emulator.hold_button(direction)
                yield
                frames += 1
                if frames > per_leg_bound:
                    raise BotModeError(f"held walk: never reached {tgt} heading {direction}.")
    finally:
        context.emulator.reset_held_buttons()


def fight_route119_rival_and_get_fly() -> Generator:
    """Chapter 13c — the Route 119 rival (bridge, ~(17,33)) → HM02 Fly.

    STORY CONDITION: institute cleared (the bridge grunts are gone). Walk the bridge
    north; the rival engages (L29/29/31). After the win the scene hands over HM02.
    Completion: `RECEIVED_HM_FLY` (+ `HIDE_ROUTE_119_RIVAL` when they leave).
    ‼ The phantom flag "DEFEATED_RIVAL_ROUTE_119" does NOT exist — never gate on it."""
    from modules.memory import get_event_flag

    def _done_here() -> bool:
        try:
            return bool(get_event_flag("RECEIVED_HM_FLY"))
        except Exception:
            return False

    if _done_here():
        return
    context.message = "Story: the rival waits on the Route 119 bridge..."
    yield from wait_until_truly_controllable()
    frames = 0
    while not _done_here():
        _check_abort()
        if get_global_script_context().is_active or not player_avatar_is_controllable():
            yield from _wait_until_cutscene_over("B")
            frames += 100
            continue
        try:
            # ‼ DECOMP TRUTH (corrects runs 4-6): the encounter is a COORD TRIGGER
            # at (25,31)/(26,31) (fires while VAR_ROUTE119_STATE==0); the walking
            # rival waits at (25,32); x17's object is just the on-bike PROP. And the
            # BRIDGE tiles are planner-blind (dual elevation reads as walls — run 6
            # NO-PATHed everything), so: navigate to the pathable west staging, then
            # HELD-INPUT walk the span east and step up into the trigger (probed
            # live: (17,33)→hold Right→(29,33) walks fine).
            yield from _navigate_riding_out(MapRSE.ROUTE119, (17, 34), tries=6)
            yield from _hold_walk_route([
                ("Up", (17, 33)),
                ("Right", (25, 33)),
                ("Up", (25, 31)),   # ← the trigger row; the scene fires mid-hold
            ])
            yield from _ride_out_all_scenes(quiet_frames=300)
        except BotModeError as error:
            # The trigger firing mid-step aborts navigation — that IS the encounter
            # starting; ride it.
            reraise_if_aborting(error)  # `#24-abortrecoveryresiduals` (c) — PRE-EXISTING swallower. Latch-keyed:
            # with no whiteout pending it does nothing; with one, the unwind escapes instead of being
            # absorbed here. This handler predates `#24-loopheadabort`.
            yield from _ride_out_scripted_scene("B")
            yield from _ride_out_all_scenes(quiet_frames=300)
        frames += 200
        if frames > 40000:
            raise BotModeError("Route 119: the rival fight / HM02 Fly never resolved.")
    context.message = "Story: HM02 Fly received!"


def _leave_route120_north_bridge() -> Generator:
    """Steven's Devon-Scope scene strands the avatar on the Route 120 NORTH BRIDGE at
    (13,16) — an ISOLATED tile the planner can't leave (probed: every direction snaps
    to (13,15), calculate_path NO-PATHs everywhere from it). HELD-INPUT west to (5,15),
    from which the planner reaches Fortree. No-op unless we're stranded up there. Made
    a shared helper so a resume/derail that lands on the bridge (not only the in-line
    get_devon_scope flow) recovers too."""
    # ‼ THE GUARD MUST MATCH THE STRAND, NOT HALF THE MAP (2026-07-24, proven by
    # tools/story-dev/repro_route120_bridge_guard_fault.py). The old guard was
    # `y <= 16` alone, which is true of the whole WESTERN half of Route 120 —
    # including (5,15), this very helper's own DESTINATION. So after the first
    # crossing succeeded, a later mid-route battle + StoryMode restart re-entered
    # here from (5,15) and re-ran "hold Up until (13,15)" — geometrically impossible
    # from x=5, since holding Up only changes y. It burned the 900-frame per-leg
    # bound and raised "held walk: never reached (13, 15) heading Up" every time.
    # A/B: from (13,16) the identical generator returns cleanly in 359 frames; from
    # (5,15) it raises after 1101. The strand is the x>=12 column, so gate on it.
    # (Also ruled out by probe: (13,15) is collision=0, unoccupied — Steven's
    # template flag 972 is already flushed — so this was never an NPC or terrain bug.)
    if _map_group_number() == MapRSE.ROUTE120.value:
        x, y = tuple(get_player_avatar().local_coordinates)
        if y <= 16 and x >= 12:
            yield from _clear_stale_battle_message()
            yield from _ride_out_all_scenes(quiet_frames=200)
            yield from _hold_walk_route([("Up", (13, 15)), ("Left", (5, 15))], stop_on_script=False)
            yield from wait_until_truly_controllable()


def get_devon_scope() -> Generator:
    """Chapter 13d — Steven's Devon Scope + flushing Fortree's gym-path Kecleon.

    STORY CONDITION: at/around Fortree with the gym still Kecleon-blocked.
    HOW (probed 2026-07-24): Route 120 north bridge — STEVEN at (13,15) beside the
    invisible BridgeKecleon (12,16). Approach from the Fortree side, talk to Steven
    (A), ride the scene → a forced Kecleon battle (L30) → he hands over the DEVON
    SCOPE (`RECEIVED_DEVON_SCOPE`) and leaves. Then back into Fortree: the gym-path
    Kecleon at (25,8) (flag 969) is flushed by facing it and pressing A with the
    Scope (one more L30 battle) — after which the gym door (22,11) is reachable.
    ⚠ SKELETON — first-run-validate the approach tiles + scene rides."""
    from modules.memory import get_event_flag

    def _have_scope() -> bool:
        try:
            return bool(get_event_flag("RECEIVED_DEVON_SCOPE"))
        except Exception:
            return False

    if not _have_scope():
        context.message = "Story: Steven needs a hand on Route 120 (Devon Scope)..."
        yield from wait_until_truly_controllable()
        frames = 0
        while not _have_scope():
            _check_abort()
            if get_global_script_context().is_active or not player_avatar_is_controllable():
                yield from _wait_until_cutscene_over("B")
                frames += 100
                continue
            try:
                # Stand beside Steven (13,15): approach (14,15), face Left, talk.
                yield from _navigate_riding_out(MapRSE.ROUTE120, (14, 15), tries=6)
                # a route-trainer battle en route can park its last message —
                # A-only, input-blocking (run 8 wedged 20k frames on it here)
                yield from _clear_stale_battle_message()
                yield from ensure_facing_direction("Left")
                context.emulator.press_button("A")
                yield from wait_for_n_frames(30)
                # ‼ Steven's scene contains a YES/NO ("battle the Kecleon?") — ride
                # with the CHOICE-AWARE rider (A only at genuine choice boxes, B
                # otherwise); raw-B riding declined it in a loop (run 9).
                yield from _wait_until_cutscene_over("A")
                yield from _ride_out_all_scenes(quiet_frames=300)
            except BotModeError as error:
                reraise_if_aborting(error)  # `#24-abortrecoveryresiduals` (c) — PRE-EXISTING swallower. Latch-keyed:
                # with no whiteout pending it does nothing; with one, the unwind escapes instead of being
                # absorbed here. This handler predates `#24-loopheadabort`.
                yield from _ride_out_scripted_scene("B")
            frames += 300
            if frames > 40000:
                raise BotModeError("Route 120: the Steven/Devon-Scope scene never resolved.")
        context.message = "Story: DEVON SCOPE received!"

    # Off the Route 120 north bridge that Steven's scene strands us on (see helper).
    yield from _leave_route120_north_bridge()

    # Flush the Fortree gym-path Kecleon (city object (25,8), flag 969) if it still
    # stands. Idempotent: skip when the object is gone.
    from modules.map import get_map_objects

    def _city_kecleon_present() -> bool:
        try:
            if _map_group_number() != MapRSE.FORTREE_CITY.value:
                return True  # can't see it from elsewhere — go look
            return any(tuple(o.current_coords) == (25, 8) for o in get_map_objects())
        except Exception:
            return True

    context.message = "Story: flushing the invisible thing on Fortree's bridge..."
    rounds = 0
    while _city_kecleon_present():
        _check_abort()
        rounds += 1
        if rounds > 10:
            raise BotModeError("Fortree: the gym-path Kecleon never flushed.")
        try:
            # ‼ APPROACH FROM THE NORTH, NOT THE WEST (probed 2026-07-24, after this
            # exact line killed a user run AND my treecko run). The old target (24,8)
            # is UNREACHABLE BY DESIGN: it is a hard-collision WALL tile on the ground
            # BENEATH the tree-bridge (collision=1, elevation=0,
            # accessible_from_direction=[False]*4). The Kecleon at (25,8) stands on the
            # ELEVATED walkway, which is the x=25 column at elevation 3 — so the only
            # way to stand next to it is along that column. (25,7) is one tile north of
            # it on the same walkway and plans from ROUTE120 (5,15) in a single hop.
            # Control that makes this diagnosis trustworthy: FORTREE_CITY (5,6) IS
            # reachable from the same start, so neither calculate_path nor the
            # ROUTE120<->FORTREE_CITY connection was ever broken — only this tile was.
            yield from _navigate_riding_out(MapRSE.FORTREE_CITY, (25, 7), tries=6)
            yield from _clear_stale_battle_message()
            yield from ensure_facing_direction("Down")
            context.emulator.press_button("A")
            yield from wait_for_n_frames(30)
            # the Scope prompt is a YES/NO — choice-aware ride (the run-9 lesson)
            yield from _wait_until_cutscene_over("A")
            yield from _ride_out_all_scenes(quiet_frames=300)
        except BotModeError as error:
            reraise_if_aborting(error)  # `#24-abortrecoveryresiduals` (c) — PRE-EXISTING swallower. Latch-keyed:
            # with no whiteout pending it does nothing; with one, the unwind escapes instead of being
            # absorbed here. This handler predates `#24-loopheadabort`.
            yield from _ride_out_scripted_scene("B")
        yield from wait_until_truly_controllable()


def _fortree_walk_one_tile(direction: str, *, max_frames: int = 3000) -> Generator:
    """Drive `walking.walk_one_tile()` for a single Fortree-gym step with an
    added frame bound.

    ‼ (2026-07-24, live-driven acceptance check for punch-list #24-fortreegates)
    `walk_one_tile`'s hold-direction-until-the-tile-changes phase is
    UNBOUNDED BY DESIGN (walking.py, out of scope here; its own docstring:
    "will create an endless loop if trying to run into a wall"). Live-drove
    `do_fortree_gym()` through the real listener stack (BattleListener /
    TrainerApproachListener, same as production) from the
    `fortree_gym_wedge.ss1` save: a mid-climb trainer battle resolved
    normally, but its NPC sprite remained standing on the very tile `solve()`
    had planned to step onto next. `fortree_gates.try_move()` faithfully
    ports the decomp's gate/collision model (STATIC collision + gate arms
    only, per the reference solver -- it was never asked to, and does not,
    track other live objects), so it correctly predicted that tile as open;
    the live game correctly blocks it anyway because the trainer's sprite is
    physically standing there. `walk_one_tile` then held the direction
    forever, waiting for a tile change that would never come, straight
    through the outer per-round frame check (which only runs BETWEEN
    moves). Bounding this call (not `walking.py` or the ported solver) and
    raising is the fix: it turns an unresolvable local block into a bounded
    `BotModeError` for the story mode's derail recovery to own, instead of an
    infinite hang."""
    from modules.modes.util.walking import walk_one_tile

    gen = walk_one_tile(direction)
    frames = 0
    try:
        while True:
            next(gen)
            frames += 1
            if frames > max_frames:
                raise BotModeError(
                    f"Fortree Gym: step {direction} never completed after {frames} frames "
                    f"(blocked by something the gate model doesn't track, e.g. an NPC?)."
                )
            yield
    except StopIteration:
        pass


def do_fortree_gym() -> Generator:
    """Chapter 13e — Fortree Gym: WINONA for the Feather Badge (BADGE06).

    HOW (probed 2026-07-24): door at city (22,11) → interior (15,24). Winona at
    (15,2), challenge from (15,3). Trainers en route engage inline.
    Completion: BADGE06_GET.

    ‼ THE TURNSTILE MODEL IN THIS DOCSTRING WAS WRONG (corrected 2026-07-24 from the
    decomp, `src/rotating_gate.c`). It claimed the gates are runtime metatiles whose
    state persists across exits, and that a sealed path is solved by "pushing into the
    blocking turnstile". Both are false, and together they are why the greedy
    `push = "Up" if y > 3 else ...` fallback below fails 100% of the time (measured:
    the avatar never moved one tile across 30 rounds — it was pushing plain wall):
      * STATIC collision never changes. A gate is `(x, y, shape, orientation)`, and the
        game only consults gate logic for a step onto a tile whose static collision is
        ALREADY OPEN. A blocked tile is ordinary scenery and never reaches gate code, so
        there is no such thing as pushing a blocking gate.
      * State does NOT persist — `MAP_SCRIPT_ON_TRANSITION` resets all orientations on
        every warp in, so a plan from the entrance is valid on every attempt.
      * Orientation IS live-readable: gate bytes are overlaid on VAR_TEMP_0..3, i.e.
        `(get_event_var(f"TEMP_{i//2}") >> (8 * (i % 2))) & 0xFF` for gates 0-7.
    The correct solver ports the decomp's arm-layout + rotation tables and BFSes from the
    OBSERVED state to (15,3) — see `tools/story-dev/fortree/fortree_gate_solver.py`, which
    finds a legal 97-move route over the real collision grid.
    WIRED IN (2026-07-24, punch-list #24-fortreegates): the climb below now reads live gate
    orientations and re-plans with `modules.story.fortree_gates.solve()` one tile at a time
    instead of the greedy push — see that module's docstring for the 4/4 live validation."""
    from modules.memory import get_event_flag

    GYM = MapRSE.FORTREE_CITY_GYM

    if get_event_flag("BADGE06_GET"):
        return
    # A resume with the Scope already set skips get_devon_scope, so recover the
    # bridge-strand here too before anything navigates.
    yield from _leave_route120_north_bridge()
    context.message = "Story: entering Fortree Gym to challenge Winona..."
    if _map_group_number() != GYM.value:
        yield from _enter_warp_by_navigation(
            lambda: _map_group_number() == GYM.value,
            MapRSE.FORTREE_CITY, (22, 11), tries=6, label="Fortree Gym door",
        )
        yield from wait_until_truly_controllable()

    # ‼ navigate_to_anywhere / calculate_path do NOT model the rotating gates and
    # will happily hand back a route whose first step crosses a gate arm (live-
    # probed 2026-07-24: the planner returned a 35-waypoint "route" the real
    # navigator could not walk at all) — they are not used for movement in this
    # room. Instead: read the live gate orientations off VAR_TEMP_0..3
    # (`fortree_gates.read_orientations`) and BFS a legal route over the real
    # collision grid (`fortree_gates.solve`, ported from the decomp's
    # `rotating_gate.c` — see that module's docstring for the live 4/4
    # validation). One tile is walked at a time and the state is re-read before
    # every re-plan, so a trainer interrupt or an unexpected result self-corrects
    # instead of blindly finishing a stale multi-move plan.
    from modules.story.fortree_gates import read_orientations, solve
    from modules.map import get_map_objects

    _FORTREE_MAX_ROUNDS = 600  # bounds the outer replan loop (optimal solve is 97 moves)
    _FORTREE_MAX_MOVES = 600  # bounds total tiles walked across the whole climb
    _FORTREE_MAX_RESET_CYCLES = 2  # bounds "solve() found nothing -> leave & re-enter" cycles
    # A wandering NPC steps aside within a second or two; a DEFEATED TRAINER never moves.
    # After this many 30-frame waits, stop waiting and take the exit-and-re-enter reset,
    # which (user mechanic, 2026-07-24) resets NPC positions as well as gate orientations.
    _FORTREE_MAX_NPC_WAITS = 4
    _FORTREE_MAX_TOTAL_FRAMES = 150_000  # hard backstop independent of the above counters
    rounds = 0
    moves_executed = 0
    reset_cycles = 0
    npc_wait_rounds = 0
    start_frame = context.emulator.get_frame_count()
    while not (
        _map_group_number() == GYM.value
        and tuple(get_player_avatar().local_coordinates) == (15, 3)
    ):
        _check_abort()
        if get_event_flag("BADGE06_GET"):
            return
        rounds += 1
        if rounds > _FORTREE_MAX_ROUNDS:
            raise BotModeError("Fortree Gym: could not reach the challenge tile below Winona.")
        if context.emulator.get_frame_count() - start_frame > _FORTREE_MAX_TOTAL_FRAMES:
            raise BotModeError("Fortree Gym: exceeded the frame budget trying to reach Winona.")

        # A trainer's sight-line (or any other scripted interruption) can fire
        # mid-climb — ride it out, then re-read state and re-plan from scratch.
        if get_global_script_context().is_active or not player_avatar_is_controllable():
            yield from _ride_out_scripted_scene("B")
            yield from wait_until_truly_controllable()
            continue

        x, y = get_player_avatar().local_coordinates
        orientations = read_orientations()
        # Live objects (NPCs -- e.g. a just-fought trainer's sprite left standing
        # where it was) are NOT part of the ported gate/collision model (the
        # decomp only ever consults static collision + gate arms) but DO
        # physically block a step in the live game -- probed live 2026-07-24: a
        # defeated trainer's sprite parked on the model's predicted-open next
        # tile hung the whole climb. Feed live object tiles in as `blocked` so
        # the planner routes around them; exclude the player's own object, or
        # every plan would fail immediately.
        # ‼ `get_map_objects()` IS NOT A ROOM INVENTORY (decomp-verified 2026-07-25).
        # `TrySpawnObjectEvents` only spawns objects inside a CAMERA WINDOW, so this set is
        # systematically INCOMPLETE right after entering at (15,24) — distant trainers simply
        # do not exist in `gObjectEvents` yet. That is survivable here ONLY because we re-plan
        # every single tile, so an NPC is picked up as soon as it spawns into view. Never treat
        # an empty/small object list as "the room is clear", and never precompute a whole route
        # from one snapshot of it.
        blocked_tiles = frozenset(
            tuple(o.current_coords) for o in get_map_objects() if "isPlayer" not in o.flags
        )
        plan = solve((x, y), orientations, goal_xy=(15, 3), blocked=blocked_tiles)
        if plan is None:
            # Blocking every live object can, in principle, remove EVERY route
            # (an NPC standing in a genuine chokepoint, or transiently on the
            # goal tile) even when a route exists ignoring it. Retry once
            # without NPC-blocking before concluding the GATE CONFIGURATION
            # itself is unsolvable -- these are different failure modes, and
            # only the second one should trigger the reset-and-re-enter path.
            plan_ignoring_npcs = solve((x, y), orientations, goal_xy=(15, 3))
            if plan_ignoring_npcs is not None and npc_wait_rounds < _FORTREE_MAX_NPC_WAITS:
                # A WANDERING npc will step aside on its own, so wait briefly and
                # re-plan. But a DEFEATED TRAINER does not wander — its sprite stays
                # parked wherever the approach left it, so waiting is futile and this
                # branch would spin until the round/frame bounds fired.
                # ‼ USER MECHANIC (2026-07-24): leaving and re-entering the gym resets
                # NPC POSITIONS as well as the gate orientations. So the reset below is a
                # FULL puzzle reset, not just a gate reset — which makes it the correct
                # escape for a permanently-parked trainer too, not only for an unsolvable
                # gate configuration. Bound the waiting, then fall through to it.
                npc_wait_rounds += 1
                context.message = (
                    "Story: Fortree Gym — a live object is blocking every route to Winona "
                    f"from here; waiting for it to move ({npc_wait_rounds}/"
                    f"{_FORTREE_MAX_NPC_WAITS})..."
                )
                yield from wait_for_n_frames(30)
                continue
            # else: genuinely unsolvable from this exact gate configuration,
            # NPCs aside -- fall through to the reset-and-re-enter path below.
            # No sequence of pushes reaches the goal from this exact gate
            # configuration. Orientations reset on every warp IN
            # (MAP_SCRIPT_ON_TRANSITION), so leave through the entrance warp
            # and re-enter for a clean slate — bounded to 2 cycles.
            reset_cycles += 1
            if reset_cycles > _FORTREE_MAX_RESET_CYCLES:
                raise BotModeError(
                    "Fortree Gym: the gate solver found no route to the challenge tile even "
                    "after resetting the gate orientations twice."
                )
            exit_plan = solve((x, y), orientations, goal_xy=(15, 24), blocked=blocked_tiles)
            if exit_plan is None:
                exit_plan = solve((x, y), orientations, goal_xy=(16, 24), blocked=blocked_tiles)
            if exit_plan is None:
                exit_plan = solve((x, y), orientations, goal_xy=(15, 24))
            if exit_plan is None:
                exit_plan = solve((x, y), orientations, goal_xy=(16, 24))
            if exit_plan is not None:
                for step in exit_plan:
                    if get_global_script_context().is_active or not player_avatar_is_controllable():
                        break
                    yield from _fortree_walk_one_tile(step)
                    moves_executed += 1
                    if moves_executed > _FORTREE_MAX_MOVES:
                        raise BotModeError("Fortree Gym: exceeded the movement budget trying to reach Winona.")
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == GYM.value,
                MapRSE.FORTREE_CITY, (22, 11), tries=6, label="Fortree Gym door (gate reset)",
            )
            yield from wait_until_truly_controllable()
            continue

        if len(plan) == 0:
            continue

        # Execute a single move, then loop back to re-read state + re-plan.
        # ‼ RESET THE NPC-WAIT COUNTER ON PROGRESS. It is a CONSECUTIVE-stall counter, not
        # a lifetime tally: a 97-move climb past several trainers can legitimately wait for
        # a wandering NPC more than `_FORTREE_MAX_NPC_WAITS` times in total, and without
        # this reset those unrelated waits would accumulate and trigger a pointless
        # exit-and-re-enter deep into a healthy climb. (Same shape as the move-learn valve
        # bug found earlier today — a counter that only ever increments eventually fires on
        # a perfectly healthy run.)
        npc_wait_rounds = 0
        yield from _fortree_walk_one_tile(plan[0])
        moves_executed += 1
        if moves_executed > _FORTREE_MAX_MOVES:
            raise BotModeError("Fortree Gym: exceeded the movement budget trying to reach Winona.")

    # Challenge Winona (face up + A), ride the battle + badge dialogue out.
    yield from ensure_facing_direction("Up")
    frames = 0
    while not get_event_flag("BADGE06_GET"):
        _check_abort()
        context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 40000:
            raise BotModeError("Fortree Gym: the Winona challenge never resolved to a badge.")
        yield
    yield from _wait_until_cutscene_over("B")
    context.message = "Story: FEATHER BADGE earned — Gym 6 (Winona) beaten!"


def do_dewford_gym() -> Generator:
    """Chapter 7b — Dewford Gym: beat Brawly for the Knuckle Badge (BADGE02, Gym 2).

    INTENT: clear the second gym.
    STORY CONDITION: in Dewford Town. Brawly runs Fighting (Machop 16 / Meditite 16 /
    Makuhita 19 in Emerald) — the caller should heal + pick a Fighting-resistant lead
    first (`_lead_best_matchup(["Fighting"])`: Taillow resists and Wing Attack hits 2×;
    never lead a Normal mon here). The gym is DARK (no Flash needed — darkness is visual
    only; navigation and battles work normally).
    HOW IT WORKS: enter via the town door (8,17), navigate bottom→top to the challenge
    tile (4,4) below Brawly (4,3) — gym trainers en route are fought inline by the
    battle listener — then face Up + A to challenge, riding out battle + dialogue until
    `BADGE02_GET` sets.
    GOAL/END STATE: BADGE02_GET (Knuckle Badge)."""
    from modules.memory import get_event_flag

    context.message = "Story: entering Dewford Gym to challenge Brawly..."
    gym = MapRSE.DEWFORD_TOWN_GYM.value
    rounds = 0
    while _map_group_number() != gym or tuple(get_player_avatar().local_coordinates) != DEWFORD_GYM_BRAWLY_APPROACH:
        _check_abort()
        rounds += 1
        if rounds > 15:
            raise BotModeError("Dewford Gym: could not reach the challenge tile below Brawly.")
        if get_event_flag("BADGE02_GET"):
            return
        try:
            yield from navigate_to_anywhere(
                MapRSE.DEWFORD_TOWN_GYM,
                DEWFORD_GYM_BRAWLY_APPROACH,
                avoid_encounters=True,
                avoid_scripted_events=False,
            )
        except BotModeError:
            # A gym trainer's sight-line (or Brawly himself) engaged — the battle
            # listener fights it; ride the aftermath out and re-path.
            yield from _ride_out_scripted_scene("B")

    # Challenge Brawly (face up + A) and ride out the whole battle + badge dialogue.
    frames = 0
    while not get_event_flag("BADGE02_GET"):
        _check_abort()  # bail fast if we whited out mid-gym (defeat recovery)
        context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 30000:
            raise BotModeError("Dewford Gym: the Brawly challenge never resolved to a badge.")
        yield
    yield from _wait_until_cutscene_over("B")
    context.message = "Story: KNUCKLE BADGE earned — Gym 2 (Brawly) beaten!"


# ---------------------------------------------------------------------------
# Chapter 14 - Mt. Pyre: the Route 121 Aqua gate, then the summit (Magma Emblem)
#
# ‼ EVERY constant here is ROM- or decomp-verified (design §Ch14-PRE + §Ch14a,
# 2026-08-05). Nothing is recalled. Re-derive with:
#     PROBE_MAPS=ROUTE121,ROUTE122,MT_PYRE_SUMMIT py -3.12 tools/story-dev/mapfacts.py
#     gh api repos/pret/pokeemerald/contents/data/maps/Route121/map.json
# ---------------------------------------------------------------------------

#: `Route121_EventScript_AquaGruntsMoveOut` fires here (coord_event, VAR_ROUTE121_STATE == 0).
#: Three Team Aqua grunts at (30,7)/(31,7)/(30,8) seal Route 121's ONLY corridor south
#: (x=30-31); the script walks them off, `removeobject`s all three and sets the var to 1.
#: ‼ Until it fires, `calculate_path` cannot reach Route 121's south edge, the corridor, or
#: ANY Route 122 tile - measured 2026-08-05, WITH surf available. This is a STORY gate, and
#: hours were spent debugging the navigator before that was measured (08-MISTAKES).
ROUTE121_AQUA_GATE_TRIGGER = (25, 5)

#: The plain walkable tile DIRECTLY BELOW Mt. Pyre's door on Route 122 (the door is (22,29)).
#: ‼ NEVER navigate to the door itself: walking onto a warp FIRES it, so a warp tile is only
#: ever an implicit destination. Targeting one ends the trip a map further on - and reports
#: success (08-MISTAKES 2026-08-05, hit twice).
ROUTE122_MT_PYRE_DOOR_APPROACH = (22, 30)

#: `MtPyre_Summit_EventScript_TeamAquaExits` fires here (coord_event, VAR_MT_PYRE_STATE == 0).
#: It removes Archie + 4 grunts, walks the Old Lady over UNPROMPTED, `giveitem
#: ITEM_MAGMA_EMBLEM`, and sets FLAG_HIDE_JAGGED_PASS_MAGMA_GUARD - which is what opens the
#: Magma Hideout. The bot never talks to anyone. A clean vertical corridor runs x=23 from the
#: summit entrance (23,31) up to y=7.
MT_PYRE_SUMMIT_TRIGGER = (23, 7)



def _ch14_say(message: str) -> None:
    """Set the status message AND print it.

    ‼ WHY BOTH (batch `20260806-055947`). These milestones were `context.message` only, which
    the GUI shows but which NEVER reaches a headless lane's stdout. The batch proved Segment 14
    worked, but every progress line read 0 — so if it had failed mid-way there would have been a
    guard error and no trace of HOW FAR it got. A chapter's milestones are its only in-flight
    diagnostic; print them."""
    from modules.console import console

    context.message = message
    console.print(f"[cyan]{message}[/]")


def _route121_gate_open() -> bool:
    """Have the Route 121 Team Aqua grunts moved out? (`VAR_ROUTE121_STATE >= 1`)

    ‼ Name verified present in `modules/data/event_vars/emerald.txt:117` - `get_event_var`
    returns **-1** for an unknown name, which would make this guard silently never fire."""
    from modules.memory import get_event_var

    return get_event_var("ROUTE121_STATE") >= 1


def _mt_pyre_summit_done() -> bool:
    """Has the summit scene run? (`VAR_MT_PYRE_STATE >= 1`; name verified at line 186.)

    ‼ Deliberately NOT `HIDE_MT_PYRE_SUMMIT_MAXIE` (856): this project already recorded that
    flag reading True on a save nowhere near Mt. Pyre, and the decomp explains why - 856 hides
    an object that is only POSITIONED at state 2, a different visit."""
    from modules.memory import get_event_var

    return get_event_var("MT_PYRE_STATE") >= 1


def open_route121_aqua_gate() -> Generator:
    """Chapter 14a - walk onto the Route 121 trigger so the Team Aqua grunts move out.

    INTENT: unseal the only corridor from Route 121's north band to its south band, which is
    the sole land route toward Route 122 and Mt. Pyre.
    STORY CONDITION: post-Winona, standing anywhere that can reach ROUTE121.
    HOW IT WORKS: a COORD TRIGGER, not a conversation - step on (25,5) and the game runs
    `Route121_EventScript_AquaGruntsMoveOut` itself.
    GOAL/END STATE: `VAR_ROUTE121_STATE >= 1`, grunts gone, controllable."""
    if _route121_gate_open():
        return  # resume-safe: already done this run or a previous one

    _ch14_say("Story: Mt. Pyre - clearing the Team Aqua grunts on Route 121...")
    yield from _navigate_riding_out(MapRSE.ROUTE121, ROUTE121_AQUA_GATE_TRIGGER)
    # The trigger fires ON the step, so control is taken immediately; ride the scene out.
    yield from _ride_out_scripted_scene("B")
    yield from wait_until_truly_controllable()

    if not _route121_gate_open():
        # ‼ Guard, never assume. A silent "no" here is indistinguishable from "the feature
        # isn't running", which has cost this project time three times (KI-24, KI-39, KI-42).
        raise BotModeError(
            "Route 121: stepped on the Aqua-gate trigger at "
            f"{ROUTE121_AQUA_GATE_TRIGGER} but ROUTE121_STATE is still 0 - "
            "the grunts did not move out."
        )
    _ch14_say("Story: Route 121 is open - the Aqua grunts have moved out.")


def do_mt_pyre_summit() -> Generator:
    """Chapter 14b - climb Mt. Pyre's exterior to the summit and take the Magma Emblem.

    INTENT: run the summit scene, which yields the Magma Emblem and sets
    `FLAG_HIDE_JAGGED_PASS_MAGMA_GUARD` - the gate on the Magma Hideout (§Ch14).
    STORY CONDITION: the Route 121 gate is open (`open_route121_aqua_gate` ran).
    HOW IT WORKS: EXPLICIT SHORT LEGS rather than one generic
    `navigate_to_anywhere(MT_PYRE_SUMMIT, ...)`. The route is
    ROUTE122 -> MT_PYRE_1F -> EXTERIOR -> SUMMIT.

    ‼ WHY SHORT LEGS - and note the reason is NOT what I first wrote. `calculate_path` DOES
    span several connected maps (this chapter proves it: leg 1 runs Fortree -> ROUTE120 ->
    ROUTE121 in one call). The 2026-08-05 failures that looked like a "two connections away"
    limit were actually the Route 121 Team Aqua grunts BLOCKING the corridor - a blocked path,
    not a topology limit. **The two errors are different strings and they mean different
    things:** "are not on connected maps (note that warps don't count.)" = genuinely
    unreachable; "Could not find a path from X to Y" = connected, but something is in the way.
    Short legs are still right here because each one FAILS WHERE IT BROKE, naming the map that
    is blocked, instead of reporting one opaque failure for a seven-map journey.
    ‼ The interior tower (2F-6F) is a SKIPPABLE side dungeon and is deliberately not entered.
    GOAL/END STATE: `VAR_MT_PYRE_STATE >= 1`, Magma Emblem in the bag, controllable."""
    if _mt_pyre_summit_done():
        return  # resume-safe

    _ch14_say("Story: heading for Mt. Pyre...")
    # Leg 1 - Route 122, standing BELOW the door (never on it; a warp tile fires on contact).
    yield from _navigate_riding_out(MapRSE.ROUTE122, ROUTE122_MT_PYRE_DOOR_APPROACH)

    # Leg 2 - in through the door, then out onto the exterior, then up to the summit. Each hop
    # is one warp, entered by NAVIGATING ONTO its tile (which is how a warp is meant to be
    # taken); `_enter_warp_by_navigation` handles the already-standing-on-it case and rides
    # out interruptions. Paired doorways are ROM-verified: 1F<->R122 (17,18)+(18,18),
    # 1F<->EXTERIOR (3,6)+(4,6), EXTERIOR<->SUMMIT (19,10)+(20,10).
    yield from _enter_warp_by_navigation(
        lambda: _map_group_number() == MapRSE.MT_PYRE_1F.value,
        MapRSE.ROUTE122,
        (22, 29),
        label="Mt. Pyre door (Route 122)",
    )
    yield from wait_until_truly_controllable()

    yield from _enter_warp_by_navigation(
        lambda: _map_group_number() == MapRSE.MT_PYRE_EXTERIOR.value,
        MapRSE.MT_PYRE_1F,
        (3, 6),
        label="Mt. Pyre 1F to exterior",
    )
    yield from wait_until_truly_controllable()

    yield from _enter_warp_by_navigation(
        lambda: _map_group_number() == MapRSE.MT_PYRE_SUMMIT.value,
        MapRSE.MT_PYRE_EXTERIOR,
        (19, 10),
        label="Mt. Pyre exterior to summit",
    )
    yield from wait_until_truly_controllable()

    # Leg 3 - walk the summit corridor (x=23) up to the trigger. ‼ The four Aqua grunts stand
    # IN this corridor at (21,15)/(21,11)/(25,18)/(25,11), so expect sight-lines: this is a
    # fight-through leg, which `_navigate_riding_out` handles by riding out and retrying.
    _ch14_say("Story: Mt. Pyre summit - climbing to the orb chamber...")
    yield from _navigate_riding_out(MapRSE.MT_PYRE_SUMMIT, MT_PYRE_SUMMIT_TRIGGER)
    yield from _ride_out_scripted_scene("B")
    yield from wait_until_truly_controllable()

    if not _mt_pyre_summit_done():
        raise BotModeError(
            f"Mt. Pyre: reached the summit trigger at {MT_PYRE_SUMMIT_TRIGGER} but "
            "MT_PYRE_STATE is still 0 - the Team Aqua scene did not run."
        )
    _ch14_say("Story: MAGMA EMBLEM obtained - Mt. Pyre summit complete.")


# ---------------------------------------------------------------------------
# Chapter 15 - the Magma Hideout (Jagged Pass). INCREMENT 1: reach the pass and OPEN the door.
#
# ‼ EVERY constant here is decomp- or probe-verified (design §Ch15, 2026-08-10). Re-derive:
#     cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_magma_anchor.py   (the era gate)
#     cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch15_travel.py    (the route)
#     gh api repos/pret/pokeemerald/contents/data/maps/JaggedPass/scripts.inc
# ---------------------------------------------------------------------------

#: `JAGGED_PASS (16,18)` -> `MAGMA_HIDEOUT_1F` (warp id 4, unconditional in `map.json`).
#: ‼ This is a WARP TILE and is therefore NEVER a navigation destination - walking onto one
#: FIRES it, so the trip ends a map further on and reports success (08-MISTAKES 2026-08-05).
MAGMA_HIDEOUT_DOOR = (16, 18)

#: The plain walkable tile below the door column, and the tile every reachability measurement
#: for this chapter was taken from.
MAGMA_HIDEOUT_DOOR_APPROACH = (16, 20)

#: ‼‼ THE DOOR IS WALLED SHUT UNTIL A STEP TRIGGER OPENS IT, AND THIS IS THE FACT THAT
#: INVALIDATES EVERY EARLIER "the door is unreachable" READING OF THIS MAP.
#: `JaggedPass_OnLoad` runs `JaggedPass_EventScript_ConcealHideoutEntrance`, which
#: `setmetatile`s (16,17) and (16,18) to `METATILE_Lavaridge_RockWall` while
#: `VAR_JAGGED_PASS_STATE <= 1`. The opening scene is a COORD EVENT on one of five tiles,
#: gated on `VAR_JAGGED_PASS_STATE == 1`:
#:     (21,15) (22,20) (21,20) (14,15) (13,15)  ->  JaggedPass_EventScript_OpenMagmaHideout
#: which shakes the camera twice, prints "the boulder is shaking in response to the emblem",
#: `setmetatile`s the entrance open and sets `VAR_JAGGED_PASS_STATE = 2`.
#: The var reaches 1 BY ITSELF: `JaggedPass_OnResume` checks `ITEM_MAGMA_EMBLEM` on every map
#: load and sets it. So the Emblem is the gate, and the trigger walk is the ACTION.
#: ‼ `(13,15)` is chosen because it is NEAREST THE DESCENT: 8-10 waypoints from every arrival
#: tile below the top warps, against 15-23 for the (21,*)/(22,*) trio (measured 2026-08-10).
JAGGED_PASS_HIDEOUT_TRIGGER = (13, 15)
JAGGED_PASS_HIDEOUT_TRIGGERS = ((13, 15), (14, 15), (21, 20), (22, 20), (21, 15))

#: Mt. Chimney's south edge, above the warp into Jagged Pass. `do_jagged_descent()` (Ch11c)
#: has walked this exact tile since 2026-07 and then stepped Down through the warp.
MT_CHIMNEY_JAGGED_DESCENT = (21, 40)

#: The staging heal. Lavaridge sits one connection west of Route 112's cable-car station
#: (66 waypoints, measured), so healing HERE puts a full-health party on the mountain.
MAGMA_STAGING_CENTER = PokemonCenter.LavaridgeTown

#: ‼ THE TWO EN-ROUTE HEALS, AND WHY THEY EXIST - THIS IS A MEASURED FIX, NOT A PRECAUTION.
#: Ch14 hands over a WRECKED party: `saves/post_mtpyre.ss1`, captured from a real run, is
#: **3 of 6 fainted** with the survivors at 21/117 and 18/109 and the lead's best move at 0 PP.
#: The first build of this leg healed only at Lavaridge, five maps away, and the live run
#: (2026-08-10) whited out on ROUTE123 at f23674 - two maps in - and respawned at Fortree.
#: ‼ And note WHICH direction killed it: Route 121/122 back toward Lilycove is ground Ch14
#: already cleared, so its trainers are beaten; ROUTE123/118 westward are FRESH trainers.
#: So heal FIRST (Lilycove, back over beaten ground) and again at the western midpoint.
MAGMA_ROUTE_HEALS = (
    (PokemonCenter.LilycoveCity, (24, 15)),
    (PokemonCenter.MauvilleCity, (22, 6)),
)

#: Every map inside the hideout - used only to make the travel leg RESUME-SAFE (if a previous
#: attempt already got in, do not walk back out to the door and in again).
_MAGMA_HIDEOUT_MAPS = (
    MapRSE.MAGMA_HIDEOUT_1F.value,
    MapRSE.MAGMA_HIDEOUT_2F_1R.value,
    MapRSE.MAGMA_HIDEOUT_2F_2R.value,
    MapRSE.MAGMA_HIDEOUT_2F_3R.value,
    MapRSE.MAGMA_HIDEOUT_3F_1R.value,
    MapRSE.MAGMA_HIDEOUT_3F_2R.value,
    MapRSE.MAGMA_HIDEOUT_3F_3R.value,
    MapRSE.MAGMA_HIDEOUT_4F.value,
)

#: The Mt. Pyre maps the chapter can START on, since Ch14 ends standing on the summit.
_MT_PYRE_MAPS = (
    MapRSE.MT_PYRE_SUMMIT.value,
    MapRSE.MT_PYRE_EXTERIOR.value,
    MapRSE.MT_PYRE_1F.value,
)

#: The mountain side of the one-way descent - reachable only by cable car, never on foot.
_MAGMA_ON_MOUNTAIN = (
    MapRSE.MT_CHIMNEY.value,
    MapRSE.MT_CHIMNEY_CABLE_CAR_STATION.value,
    MapRSE.JAGGED_PASS.value,
)

#: The mountain, PLUS Route 112 - i.e. everywhere that means "the overland haul is done".
#: ROUTE112 (28,28) is the cable-car station's own approach tile, so standing anywhere on
#: Route 112 means the long trip across Hoenn has already succeeded and must not be re-walked.
_MAGMA_PAST_HAUL = _MAGMA_ON_MOUNTAIN + (MapRSE.ROUTE112.value,)


def _magma_guard_gone() -> bool:
    """Is the Team Magma guard off `(16,19)`, the door column's only entry? (flag 847)

    ‼ Name verified present in `modules.memory._event_flags` by `probe_magma_anchor.py`
    (NAME CONTROL PASS, 2026-08-10). `get_event_flag` returns **False** for an unknown flag
    name, silently - so a phantom name here would read exactly like a guard still standing
    there, and the chapter would refuse forever with a plausible-looking reason."""
    from modules.memory import get_event_flag

    return get_event_flag("HIDE_JAGGED_PASS_MAGMA_GUARD")


def _hideout_entrance_open() -> bool:
    """Has `JaggedPass_EventScript_OpenMagmaHideout` run? (`VAR_JAGGED_PASS_STATE == 2`)

    ‼ Name verified present in `modules/data/event_vars/emerald.txt`; `get_event_var` returns
    **-1** for an unknown name, which would make this guard silently never fire. The values
    are the decomp's own: 0 = no Emblem yet, 1 = Emblem held and the trigger armed, 2 = the
    entrance metatiles have been opened."""
    from modules.memory import get_event_var

    return get_event_var("JAGGED_PASS_STATE") >= 2


def _inside_magma_hideout() -> bool:
    return _map_group_number() in _MAGMA_HIDEOUT_MAPS


def _at_magma_door_approach() -> bool:
    if _map_group_number() != MapRSE.JAGGED_PASS.value:
        return False
    return tuple(get_player_avatar().local_coordinates) == MAGMA_HIDEOUT_DOOR_APPROACH


def open_magma_hideout_entrance() -> Generator:
    """Chapter 15b - walk onto a Jagged Pass trigger tile so the hideout entrance opens.

    INTENT: turn `VAR_JAGGED_PASS_STATE` from 1 to 2, which is what physically removes the
    `METATILE_Lavaridge_RockWall` pair covering (16,17)/(16,18). Until that happens the warp
    at (16,18) exists in `map.json` but cannot be walked onto.
    STORY CONDITION: standing on JAGGED_PASS with the Magma Emblem in the bag.
    HOW IT WORKS: navigate to `(13,15)` - the nearest of the five trigger tiles to the descent
    - and ride out the scene, which is two `ShakeCamera` specials and one `msgbox`. Falls back
    through the other four tiles, because a trainer or a ledge can leave us on the wrong side
    of any one of them and they are equivalent for this purpose.
    GOAL/END STATE: `VAR_JAGGED_PASS_STATE >= 2`."""
    if _hideout_entrance_open():
        return  # resume-safe

    tried: list[str] = []
    for trigger in JAGGED_PASS_HIDEOUT_TRIGGERS:
        _check_abort()
        try:
            yield from _navigate_riding_out(MapRSE.JAGGED_PASS, trigger)
        except BotModeError as error:
            reraise_if_aborting(error)  # `#24-abortrecoveryresiduals` (c) — PRE-EXISTING swallower. Latch-keyed:
            # with no whiteout pending it does nothing; with one, the unwind escapes instead of being
            # absorbed here. This handler predates `#24-loopheadabort`.
            tried.append(f"{trigger}: unreachable ({str(error)[:60]})")
            continue
        # The trigger fires ON the step, so control is taken immediately; ride the scene out.
        yield from _ride_out_scripted_scene("B")
        yield from wait_until_truly_controllable()
        if _hideout_entrance_open():
            _ch14_say("Story: the Magma Hideout entrance has opened.")
            return
        tried.append(f"{trigger}: stepped, but JAGGED_PASS_STATE is still "
                     f"{_jagged_pass_state()}")

    raise BotModeError(
        "Magma Hideout: could not open the entrance - none of the five trigger tiles "
        f"{JAGGED_PASS_HIDEOUT_TRIGGERS} fired `JaggedPass_EventScript_OpenMagmaHideout`. "
        f"Attempts: {tried}. ‼ The trigger is gated on VAR_JAGGED_PASS_STATE == 1, which "
        "`JaggedPass_OnResume` sets only when ITEM_MAGMA_EMBLEM is in the bag."
    )


def _jagged_pass_state() -> int:
    from modules.memory import get_event_var

    return get_event_var("JAGGED_PASS_STATE")


def travel_to_magma_hideout_door() -> Generator:
    """Chapter 15a - cross to Jagged Pass, OPEN the hideout entrance, and stand beside it.

    INTENT: get the party from Mt. Pyre to the Magma Hideout door ALIVE, healed, and with the
    entrance actually open. This is deliberately a separate increment from going IN, because
    it is the only part of §Ch15 with measured failures against it - two of them now.

    STORY CONDITION: the Mt. Pyre summit scene has run, so the Magma Emblem is in the bag and
    flag 847 has cleared the guard off `(16,19)`. Checked, not assumed.

    HOW IT WORKS - EXPLICIT SHORT LEGS, each failing where it broke (the §Ch14a pattern):
      1. OFF MT. PYRE. Ch14 ends on the summit; three warps put us back on Route 122.
      2. HEAL, TWICE, BEFORE THE HAUL. See `MAGMA_ROUTE_HEALS` - this is the fix for a
         measured whiteout, not a precaution.
      3. LAVARIDGE. One `_navigate_riding_out` call spans ROUTE122 -> ROUTE123 -> ROUTE118 ->
         MAUVILLE -> ROUTE111 -> ROUTE112 (all connection edges). ‼ It is BLOCKED statically
         (measured: Mauville -> Route 112 FAILs to both targets) by the `#24-smashroute` Rock
         Smash rock at ROUTE111 (18,101) - and clearing that rock is exactly what
         `_navigate_riding_out` does on a failed leg, proven live 2026-07-31. A plain
         `navigate_to` would simply fail here.
      4. THE CABLE CAR. Jagged Pass descends by ONE-WAY LEDGES, so the door at y=18 cannot be
         reached from the Route 112 entrance at y=40 - the pass must be entered from the TOP.
      5. DOWN INTO THE PASS, reusing Ch11c's proven Chimney (21,40) -> warp Down leg.
      6. OPEN THE ENTRANCE, then walk to `(16,20)`.

    ‼ WHY STEP 6 IS TWO THINGS AND NOT ONE, AND WHY EVERY EARLIER READING OF THIS MAP WAS
    WRONG. The door is covered by a rock-wall metatile until a coord trigger opens it
    (see `JAGGED_PASS_HIDEOUT_TRIGGER`). A STATIC probe cannot see that: `get_map_data` reads
    the ROM's layout, where (16,18) is already a cave entrance, so `calculate_path` happily
    reports "(16,20) -> (16,18), 2 waypoints" for a tile the game has walled off. That static
    YES is what made the door look reachable; the pre-Emblem driven run that pressed Up twelve
    times and did not move was reading the WALL, and wrote it down as "a real south-facing
    ledge". Neither the ledge nor (only) the guard was the obstacle.

    GOAL/END STATE: `VAR_JAGGED_PASS_STATE >= 2` and standing on `JAGGED_PASS (16,20)`,
    controllable. Grade it BINARY."""
    if _inside_magma_hideout():
        _ch14_say("Story: already inside the Magma Hideout - skipping the approach.")
        return

    if not _magma_guard_gone():
        # ‼ Guard, never assume. A trip that ends at a tile the bot cannot leave is far worse
        # than a refusal that names its own reason - and this exact gate is what made three
        # weeks of "the door is unreachable" look like a terrain bug.
        raise BotModeError(
            "Magma Hideout: HIDE_JAGGED_PASS_MAGMA_GUARD is not set, so a Team Magma guard "
            "still stands on (16,19) - the door column's only entry. The Mt. Pyre summit "
            "scene must run first (VAR_MT_PYRE_STATE >= 1)."
        )

    yield from wait_until_truly_controllable()

    # --- Leg 1: off Mt. Pyre and back onto Route 122 --------------------------------------
    if _map_group_number() in _MT_PYRE_MAPS:
        _ch14_say("Story: leaving Mt. Pyre for the Magma Hideout...")
        if _map_group_number() == MapRSE.MT_PYRE_SUMMIT.value:
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == MapRSE.MT_PYRE_EXTERIOR.value,
                MapRSE.MT_PYRE_SUMMIT,
                (23, 31),
                label="Mt. Pyre summit to exterior",
            )
            yield from wait_until_truly_controllable()
        if _map_group_number() == MapRSE.MT_PYRE_EXTERIOR.value:
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == MapRSE.MT_PYRE_1F.value,
                MapRSE.MT_PYRE_EXTERIOR,
                (10, 42),
                label="Mt. Pyre exterior to 1F",
            )
            yield from wait_until_truly_controllable()
        if _map_group_number() == MapRSE.MT_PYRE_1F.value:
            yield from _enter_warp_by_navigation(
                lambda: _map_group_number() == MapRSE.ROUTE122.value,
                MapRSE.MT_PYRE_1F,
                (17, 18),
                label="Mt. Pyre 1F to Route 122",
            )
            yield from wait_until_truly_controllable()

    # ‼ Skip the whole overland section once we are PAST IT. `_MAGMA_PAST_HAUL` includes
    # ROUTE112 as well as the mountain, because ROUTE112 (28,28) IS the cable-car station
    # approach: arriving there means the haul succeeded. Without this the driver's retry loop
    # walked all the way back to Lilycove from the station on every attempt (measured, run 3).
    if _map_group_number() not in _MAGMA_PAST_HAUL:
        # --- Leg 2: heal on the way, before the fresh-trainer half of the haul ------------
        for center, door_approach in MAGMA_ROUTE_HEALS:
            _check_abort()
            city = center.value[0]
            if _map_group_number() in _MAGMA_PAST_HAUL:
                break
            try:
                _ch14_say(f"Story: healing at {city.name} before the Magma Hideout haul...")
                yield from _navigate_riding_out(city, door_approach)
                yield from heal_in_pokemon_center(center)
                yield from wait_until_truly_controllable()
                # ‼‼ TEACH STRENGTH **HERE**, AT A HEAL STOP — AND THE PLACEMENT IS THE POINT.
                # 1F is sealed by Strength boulders, so this chapter needs a teach; but the
                # obvious place (inside the hideout, where the need arises) is the WORST
                # possible one. `#24-teachmsgstall` wedges a teach performed just after a won
                # battle, and a dungeon is nothing but won battles: measured 0 of 3 from
                # committed post-battle saves, against **38 of 42 in the live batch
                # `20260810-082509`** where teaches happen at ordinary moments.
                # Coming out of a Pokémon Centre is the calmest state a run ever reaches, so the
                # teach is piggybacked on the heal exactly as `#24-pc` piggybacks the PC
                # rotation — "piggyback, do not detour" (`21-TEAM-POLICY-DESIGN.md` §4).
                # ‼ It never raises: a failed teach here must not destroy a heal that worked,
                # and `open_magma_hideout_1f` calls `ensure_strength_learner()` again anyway.
                # This is a DODGE, not a fix — `#24-teachmsgstall` is still the real blocker.
                try:
                    yield from ensure_strength_learner()
                except BotModeError as error:
                    # ⛔ KI-81 / `#24-abortswallow`. ‼ WEAKER THAN THE OTHER SEVEN, AND SAY SO:
                    # neither `ensure_strength_learner` nor `teach_hm_move` contains a
                    # `_check_abort()`, so NO DIRECT `StoryAbort` object arrives here (verified,
                    # after an adversarial review asked). What this catches is a LAUNDERED abort —
                    # a plain `BotModeError` raised by the teach while the latch is set — which is
                    # exactly what latch-keying exists for, and it still stops ONE whiteout from
                    # printing TWO fabricated lines (this one, then the enclosing heal's "SKIPPED").
                    reraise_if_aborting(error)
                    _ch14_say(f"Story: teaching Strength at {city.name} SKIPPED - {str(error)[:120]}")
            except BotModeError as error:
                # ‼ BEST EFFORT, AND SAID OUT LOUD. These are opportunistic top-ups; failing
                # one must not end a chapter that could still succeed. But a silently skipped
                # heal is exactly how a later whiteout gets misattributed to the route, so it
                # is never silent.
                # ⛔⛔ KI-81 / `#24-abortswallow` — THIS HANDLER WAS UNDOING THE 2026-08-16 GUARD.
                # `heal_in_pokemon_center` deliberately RE-RAISES on the latch
                # (`higher_level_actions.py:364/388/437`); catching it here threw that away one
                # frame later, and the chapter then continued on a dead run. Latch-keyed.
                reraise_if_aborting(error)
                _ch14_say(f"Story: en-route heal at {city.name} SKIPPED - {str(error)[:120]}")

    # --- Leg 3: up the cable car ----------------------------------------------------------
    # ‼ `ride_cable_car_to_summit()` does the haul itself - it navigates to ROUTE112 (28,28)
    # with `_navigate_riding_out`, which is what clears the `#24-smashroute` rock at
    # ROUTE111 (18,101) that seals the Mauville corridor. It no-ops if already up top.
    if _map_group_number() not in _MAGMA_ON_MOUNTAIN:
        # ‼ THE STAGING HEAL IS BEST-EFFORT, AND THIS IS A MEASURED DECISION, not caution.
        # Lavaridge is one connection west of the station and `calculate_path` scores it at 66
        # waypoints - but the LIVE navigator refuses it: run 3 reached ROUTE112 (28,28) and
        # then failed three times with "Cannot reach LAVARIDGE_TOWN: it is not walkable from
        # ROUTE112". Two instruments, two answers; the live one governs. The chapter is not
        # allowed to die on a nice-to-have, so the Mauville heal above is the real one.
        try:
            _ch14_say("Story: topping up at Lavaridge before the mountain...")
            yield from _navigate_riding_out(MapRSE.LAVARIDGE_TOWN, (9, 7), tries=3)
            yield from heal_in_pokemon_center(MAGMA_STAGING_CENTER)
            yield from wait_until_truly_controllable()
        except BotModeError as error:
            # ⛔⛔ KI-81 / `#24-abortswallow` — THIS HANDLER WAS UNDOING THE 2026-08-16 GUARD.
            # `heal_in_pokemon_center` deliberately RE-RAISES on the latch
            # (`higher_level_actions.py:364/388/437`); catching it here threw that away one
            # frame later, and the chapter then continued on a dead run. Latch-keyed.
            reraise_if_aborting(error)
            _ch14_say(f"Story: Lavaridge staging heal SKIPPED - {str(error)[:120]}")

        _ch14_say("Story: riding the cable car up to Mt. Chimney...")
        yield from ride_cable_car_to_summit()
        yield from wait_until_truly_controllable()

    # --- Leg 5: down into Jagged Pass -----------------------------------------------------
    if _map_group_number() == MapRSE.MT_CHIMNEY.value:
        _ch14_say("Story: descending into Jagged Pass...")
        yield from _navigate_riding_out(MapRSE.MT_CHIMNEY, MT_CHIMNEY_JAGGED_DESCENT)
        yield from _walk_through_warp("Down", MapRSE.MT_CHIMNEY.value)
        yield from wait_until_truly_controllable()

    if _map_group_number() != MapRSE.JAGGED_PASS.value:
        raise BotModeError(
            "Magma Hideout: the approach never reached JAGGED_PASS (we are on "
            f"{_map_group_number()}). The cable car / Mt. Chimney descent is the only way in - "
            "the pass cannot be climbed from the Route 112 end."
        )

    # --- Leg 6: open the entrance, then stand beside it ------------------------------------
    yield from open_magma_hideout_entrance()

    _ch14_say("Story: walking to the Magma Hideout door...")
    yield from _navigate_riding_out(MapRSE.JAGGED_PASS, MAGMA_HIDEOUT_DOOR_APPROACH)
    yield from wait_until_truly_controllable()

    if not _at_magma_door_approach():
        where = tuple(get_player_avatar().local_coordinates)
        raise BotModeError(
            f"Magma Hideout: ended the approach at JAGGED_PASS {where}, not "
            f"{MAGMA_HIDEOUT_DOOR_APPROACH}. The door is 2 waypoints from there and this is "
            "the tile every reachability measurement was taken from."
        )
    _ch14_say("Story: standing at the Magma Hideout door, and it is OPEN.")


# --- Chapter 15, increments 2 and 3: inside the hideout -----------------------------------

#: The route to 4F, as (map we are on, its warp tile, the map that warp leads to). THREE warps.
#:
#: ‼‼ THIS IS THE `2F_1R` BRANCH, AND THE "SHORTEST ROUTE" IN §Ch15 WAS WRONG. That route began
#: `1F (20,22) -> 2F_3R`, which is unreachable from the hideout entrance: a plain COLLISION flood
#: of 1F (no elevation, no pathfinder) finds **three separate components** —
#:     #0  299 tiles  holds the entrance (10,34) AND (25,34) -> 2F_1R
#:     #1   70 tiles  holds (31,3) -> 2F_2R
#:     #2  ‼ 9 tiles  holds (20,22) -> 2F_3R
#: so `(20,22)` sits on a NINE-TILE ISLAND and is an EXIT from 2F_3R, never an entrance to it.
#: Measured 2026-08-10; every leg below is in one connected component with its arrival tile
#: (2F_1R 383 tiles, 3F_1R 154, 4F 293).
MAGMA_HIDEOUT_ROUTE = (
    (MapRSE.MAGMA_HIDEOUT_1F, (25, 34), MapRSE.MAGMA_HIDEOUT_2F_1R),
    (MapRSE.MAGMA_HIDEOUT_2F_1R, (17, 33), MapRSE.MAGMA_HIDEOUT_3F_1R),
    (MapRSE.MAGMA_HIDEOUT_3F_1R, (7, 21), MapRSE.MAGMA_HIDEOUT_4F),
)

#: Maxie stands at 4F `(16,21)` facing up. ‼ There is NO coord trigger anywhere in the hideout -
#: `MagmaHideout_4F_EventScript_Maxie` runs only when he is TALKED to, so this chapter cannot be
#: completed by walking onto a tile the way Ch14 was.
#: We arrive on 4F at its warp `(20,21)`; `(17,21)` is 3 waypoints away and the ONLY one of his
#: four neighbours the planner can reach ((16,22)/(15,21)/(16,20) all FAIL) - measured
#: `probe_ch15_interior.py` 2026-08-10.
MAXIE_TILE = (16, 21)
#: Every neighbour of Maxie with the direction to face from it, tried in order at runtime.
#: ‼ NOT a single hard-coded tile - which side is reachable depends on live state, and the
#: static and live readings disagreed (see the comment at the use site).
MAXIE_APPROACHES = (
    ((17, 21), "Left"),
    ((15, 21), "Right"),
    ((16, 22), "Up"),
    ((16, 20), "Down"),
)
MAXIE_APPROACH = MAXIE_APPROACHES[0][0]  # kept for the probe's reporting
MAXIE_FACING = MAXIE_APPROACHES[0][1]

#: `trainerbattle_no_intro TRAINER_MAXIE_MAGMA_HIDEOUT` - Mightyena 37 / Crobat 38 / Camerupt 39.
#: On defeat the script sets `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT` (111), which is the chapter's
#: completion test and is ALREADY referenced by `modules/story/chapters.py:200`.
MAXIE_PARTY_NOTE = "Mightyena 37 / Crobat 38 / Camerupt 39"


def _groudon_awakened() -> bool:
    """Has Maxie been beaten on 4F? (`FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT`, 111)

    ‼ Name verified present in `modules/data/event_flags/emerald.txt:60` (2026-08-10);
    `get_event_flag` returns **False** for an unknown name, so a phantom would make this
    chapter never finish while looking like an honest "not done yet"."""
    from modules.memory import get_event_flag

    return get_event_flag("GROUDON_AWAKENED_MAGMA_HIDEOUT")


def enter_magma_hideout() -> Generator:
    """Chapter 15c - step through the opened door into `MAGMA_HIDEOUT_1F`.

    STORY CONDITION: `VAR_JAGGED_PASS_STATE >= 2`, i.e. the entrance metatiles are open.
    Refuses otherwise, because before that the door tile is `METATILE_Lavaridge_RockWall` and
    walking at it does nothing at all - which is exactly what an earlier driven probe recorded
    and misread as a ledge."""
    if _inside_magma_hideout():
        return  # resume-safe

    if not _hideout_entrance_open():
        raise BotModeError(
            "Magma Hideout: refusing to enter - VAR_JAGGED_PASS_STATE is "
            f"{_jagged_pass_state()}, so the entrance at (16,18) is still a rock wall. "
            "`open_magma_hideout_entrance()` must run first."
        )

    _ch14_say("Story: entering the Magma Hideout...")
    yield from _enter_warp_by_navigation(
        lambda: _map_group_number() == MapRSE.MAGMA_HIDEOUT_1F.value,
        MapRSE.JAGGED_PASS,
        MAGMA_HIDEOUT_DOOR,
        label="Magma Hideout door (Jagged Pass)",
    )
    yield from wait_until_truly_controllable()

    if _map_group_number() != MapRSE.MAGMA_HIDEOUT_1F.value:
        raise BotModeError(
            "Magma Hideout: stepped onto the open door at "
            f"{MAGMA_HIDEOUT_DOOR} but we are not on MAGMA_HIDEOUT_1F."
        )
    _ch14_say("Story: inside the Magma Hideout (1F).")


def do_magma_hideout() -> Generator:
    """Chapter 15d - descend to 4F and beat Maxie, awakening Groudon.

    INTENT: set `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT`, the chapter's completion condition and
    the gate on the following beat (the script also opens Slateport: it clears
    `HIDE_SLATEPORT_CITY_CAPTAIN_STERN` / `..._GABBY_AND_TY` and sets `SLATEPORT_CITY_STATE`
    and `SLATEPORT_HARBOR_STATE` to 1).
    STORY CONDITION: standing inside the hideout.
    HOW IT WORKS: three warps, each taken with `_enter_warp_by_navigation` so the success test
    is THE MAP CHANGING rather than "we are standing on the tile" - the only correct test for a
    warp, since walking onto one fires it. Then talk to Maxie.
    ‼ The floors hold `TRAINER_TABITHA_MAGMA_HIDEOUT` and the numbered grunts, all ordinary
    trainer battles with sight-lines across the corridors; treat every leg as fight-through,
    which is what `_enter_warp_by_navigation` already does by riding out and retrying.

    ‼‼ BLOCKED ON 1F, AND THE CAUSE IS **STRENGTH** - MEASURED, NOT SUSPECTED (2026-08-10).
    A driven run (`--driver magmahideout` from `saves/magma_door.ss1`) entered 1F cleanly and then
    could not path off it: `floors=['MAGMA_HIDEOUT_1F']`, stopped at the arrival tile (10,34).
    The cause is exact. `calculate_path` reaches **44** of the entrance component's 299 tiles, and
    the boundary between the two is **three edges, every one of them into a Strength boulder**:
        (7,23)->(7,22)   (7,23)->(6,23)   (8,22)->(7,22)
    - i.e. the boulders at (5,22)/(7,22)/(6,23) are not "off to the west", they ARE the gate out
    of the entrance pocket. ‼ An earlier note in this file said they were off-route; that was
    read off their coordinates rather than measured, and it was wrong.
    **`obstacle_clearing.KNOWN_BUT_UNSUPPORTED` excludes `EventScript_StrengthBoulder` on
    purpose** ("a boulder is PUSHED, not removed; the success test cannot see it"), and no party
    member on the anchor knows Strength. So this chapter cannot complete until Strength support
    exists - tracked as `#24-strength`. Everything past 1F is already proven connected.

    GOAL/END STATE: `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT` set. Grade it BINARY - no batch."""
    if _groudon_awakened():
        return  # resume-safe

    if not _inside_magma_hideout():
        raise BotModeError(
            "Magma Hideout: do_magma_hideout() called from outside the hideout "
            f"(map {_map_group_number()}). `enter_magma_hideout()` must run first."
        )

    # ‼ 1F IS SEALED BY STRENGTH BOULDERS AND MUST BE OPENED BEFORE THE ROUTE CAN BE WALKED.
    # Without this the very first leg fails: measured live, the bot entered 1F and stopped at
    # the arrival tile with `floors=['MAGMA_HIDEOUT_1F']`. See `open_magma_hideout_1f`.
    if _map_group_number() == MapRSE.MAGMA_HIDEOUT_1F.value:
        yield from open_magma_hideout_1f()

    for from_map, warp_tile, to_map in MAGMA_HIDEOUT_ROUTE:
        _check_abort()
        if _map_group_number() != from_map.value:
            continue  # resume-safe: we are already deeper in
        _ch14_say(f"Story: Magma Hideout - {from_map.name} to {to_map.name}...")
        yield from _enter_warp_by_navigation(
            lambda expected=to_map: _map_group_number() == expected.value,
            from_map,
            warp_tile,
            label=f"Magma Hideout {from_map.name} -> {to_map.name}",
        )
        yield from wait_until_truly_controllable()

    if _map_group_number() != MapRSE.MAGMA_HIDEOUT_4F.value:
        raise BotModeError(
            "Magma Hideout: never reached 4F - stopped on map "
            f"{_map_group_number()}. The route is 1F (20,22) -> 2F_3R (16,13) -> "
            "3F_3R (16,21) -> 4F."
        )

    # --- Maxie -------------------------------------------------------------------------
    # ‼‼ TRY EVERY NEIGHBOUR, DO NOT HARD-CODE ONE. A static probe of 4F from the map's default
    # state said `(17,21)` was the only reachable neighbour and `(15,21)` was not; the LIVE
    # arrival measured the exact opposite - from the real arrival tile `(46,8)`, `(15,21)`
    # plans and `(17,21)` does not. Which side is open depends on live state the static read
    # cannot see, and this chapter has now been bitten three times by trusting a static answer
    # about this dungeon. So ask the planner at the moment it matters, and take what it gives.
    _ch14_say(f"Story: Magma Hideout 4F - challenging Maxie ({MAXIE_PARTY_NOTE})...")
    standing_on = None
    facing = None
    tried: list[str] = []
    for candidate, candidate_facing in MAXIE_APPROACHES:
        _check_abort()
        try:
            yield from _navigate_riding_out(MapRSE.MAGMA_HIDEOUT_4F, candidate, tries=4)
        except BotModeError as error:
            reraise_if_aborting(error)  # `#24-abortrecoveryresiduals` (c) — PRE-EXISTING swallower. Latch-keyed:
            # with no whiteout pending it does nothing; with one, the unwind escapes instead of being
            # absorbed here. This handler predates `#24-loopheadabort`.
            tried.append(f"{candidate}: {str(error)[:60]}")
            continue
        yield from wait_for_player_avatar_to_be_standing_still()
        if tuple(get_player_avatar().local_coordinates) == candidate:
            standing_on, facing = candidate, candidate_facing
            break
        tried.append(f"{candidate}: arrived at {tuple(get_player_avatar().local_coordinates)}")

    if standing_on is None:
        raise BotModeError(
            f"Magma Hideout: could not stand on ANY tile beside Maxie {MAXIE_TILE}. "
            f"Tried {MAXIE_APPROACHES}: {tried}"
        )
    _ch14_say(f"Story: at {standing_on}, facing {facing} at Maxie {MAXIE_TILE}.")

    # Face him, then A-ride the conversation and the battle. ‼ Alternate A and B the way the
    # Flannery challenge does: A advances and confirms, B clears the message chain, and a
    # pure-A loop can re-open a menu it just closed.
    yield from ensure_facing_direction(facing)
    yield
    frames = 0
    off_map = 0
    while not _groudon_awakened():
        _check_abort()
        # ‼‼ A WHITEOUT MOVES THE PLAYER TWO TOWNS AWAY AND `_groudon_awakened()` CANNOT SEE IT.
        # MEASURED 2026-08-11 (`--profile mh-anchor`): this run LOST to Maxie, whited out to
        # MAUVILLE_CITY (22,6), and this loop went on mashing A/B at an empty overworld — 13
        # STUCK dumps and 18,300+ frames of "no progress" with the step message frozen at
        # "at (15, 21), facing Right at Maxie (16, 21)" while the avatar was two towns away.
        # The 60,000-frame bound would eventually have fired, but its message names the wrong
        # thing entirely ("the Maxie challenge never resolved"), which is the exact failure this
        # project has a standing rule about: **a failure message must report STATE, not a
        # HYPOTHESIS** (`08-MISTAKES` 2026-08-10 — "check the destination is walkable" on three
        # runs where it always was).
        #
        # ‼ DEBOUNCED, not instant. The map read can be transient across the battle's own screen
        # transitions, and ending a HEALTHY Maxie fight because of one odd frame would be a far
        # worse bug than the one being fixed. 300 frames (~5s) is longer than any transition here
        # and still ~200x cheaper than riding the full bound out.
        try:
            _on_4f = (
                get_map_data_for_current_position().map_group_and_number
                == MapRSE.MAGMA_HIDEOUT_4F.value
            )
        except Exception:  # noqa: BLE001 - an unreadable map must never end the fight
            _on_4f = True
        off_map = 0 if _on_4f else off_map + 1
        if off_map > 300:
            try:
                _where = get_map_data_for_current_position().map_group_and_number
                _tile = tuple(get_player_avatar().local_coordinates)
                _alive = sum(1 for m in get_party() if m is not None and m.current_hp > 0)
                _state = f"map={_where} tile={_tile} party_alive={_alive}/{len(get_party())}"
            except Exception as _error:  # noqa: BLE001
                _state = f"<state unreadable: {type(_error).__name__}>"
            raise BotModeError(
                "Magma Hideout: left MAGMA_HIDEOUT_4F during the Maxie challenge without "
                f"Groudon awakening — almost certainly a WHITEOUT. {_state} "
                f"(was standing {standing_on} facing {facing} at Maxie {MAXIE_TILE}, "
                f"{frames} frames in). The chapter cannot continue from here; the caller's "
                "whiteout recovery should re-run the segment."
            )
        context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 60000:
            raise BotModeError(
                "Magma Hideout: the Maxie challenge never resolved in 60,000 frames "
                f"(standing {standing_on} facing {facing} at Maxie {MAXIE_TILE}, still on 4F)."
            )
        yield

    yield from wait_until_truly_controllable()
    _ch14_say("Story: MAXIE BEATEN - Groudon is awake. Magma Hideout complete.")


def do_magma_hideout_chapter() -> Generator:
    """Chapter 15 end to end: travel -> open the entrance -> enter -> beat Maxie -> GET OUT.

    The increments stay separate functions because each has its own binary acceptance and its
    own driver, which is what let the travel leg's two failures be diagnosed as a party problem
    and a driver problem rather than as "the chapter does not work".

    ‼‼ THE CHAPTER IS NOT OVER WHEN `GROUDON_AWAKENED_MAGMA_HIDEOUT` IS SET. That flag fires the
    moment Maxie falls, four floors underground, and for one whole session this function returned
    successfully on runs that were **permanently stranded** (KI-56) - the boulder puzzle that let
    the bot in reseals behind it on map reload, and no walk-out exists. So the acceptance is BOTH
    halves: the flag AND being outside and controllable. `leave_magma_hideout()` is deliberately
    OUTSIDE the flag guard, so a run resumed after the flag was set still finishes the exit."""
    if not _groudon_awakened():
        yield from travel_to_magma_hideout_door()
        yield from enter_magma_hideout()
        yield from do_magma_hideout()
    yield from leave_magma_hideout()


# ---------------------------------------------------------------------------
# `#24-strength` — Strength boulders. THE FIELD MOVE `obstacle_clearing` CANNOT EXPRESS.
#
# ‼ WHY THIS IS NOT IN `obstacle_clearing.py` WITH Rock Smash and Cut. That framework's
# success test is "the obstacle OBJECT IS GONE", and its own `KNOWN_BUT_UNSUPPORTED` entry
# says exactly why Strength cannot use it: *"a boulder is PUSHED, not destroyed: the object
# still exists afterwards, one tile over."* So the test here is the opposite shape — **the
# boulder MOVED**, checked on both tiles — and that is the entire reason this lives apart.
# ---------------------------------------------------------------------------

#: `FLAG_SYS_USE_STRENGTH` (2185, `modules/data/event_flags/emerald.txt:1064`; decomp
#: `include/constants/flags.h:1399`). Set by `EventScript_ActivateStrength`.
#:
#: ⛔⛔ **CORRECTED 2026-08-13 — MEASURED LIVE. THIS COMMENT USED TO SAY THE FLAG IS "NEVER
#: CLEARED … switched on ONCE PER SAVE, not once per map". THAT IS FALSE.** It is cleared on
#: **EVERY WARP**: `ClearTempFieldEventData()` (`src/event_data.c:39-48`) calls
#: `FlagClear(FLAG_SYS_USE_STRENGTH)`, and it is invoked from `LoadMapFromWarp`
#: (`src/overworld.c:848`) — plus on Fly/Teleport/Dig/white-out.
#: **Proof, not argument:** `--driver ch20room2` read the flag immediately after warping
#: `SEAFLOOR_CAVERN_ROOM1 → ROOM2`, having just activated Strength in Room 1, and got **False**.
#: ‼ **WHY THE OLD CLAIM SURVIVED:** it rested on "a decomp-wide search for `clearflag`" — the
#: SCRIPT MACRO. This is the C function `FlagClear`, so a macro-only search could never have
#: found it. *A search proves absence only within the vocabulary it searched.*
#: ✅ **THE CODE BELOW WAS ALWAYS SAFE** — it re-checks `_strength_active()` on every call and
#: re-activates — which is exactly why the wrong comment went unnoticed for so long. ⛔ **Do NOT
#: "optimise" that re-check away on the strength of a once-per-save assumption**: every room
#: after the first would then walk into its boulder, get a plain wall collision, and retry with
#: no message and no error. (Upstream's solver re-arms Strength in every room —
#: `puzzle_solver.py:373, 399, 429, 440` — which is only sensible if the flag does NOT persist.)
#:
#: `TryPushBoulder` (`src/field_player_avatar.c:754`) pushes
#: any `OBJ_EVENT_GFX_PUSHABLE_BOULDER` you walk into, one tile, and does NOTHING AT ALL if the
#: destination is blocked — no message, no failure signal. That silence is why the test below
#: has to watch the world.
_STRENGTH_FLAG = "SYS_USE_STRENGTH"

#: face direction -> (dx, dy). Matches `_smash_rock`'s and `obstacle_clearing._STEP`'s tables.
_STRENGTH_STEP = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}


def _strength_active() -> bool:
    """Is the Strength field move switched on right now?

    ‼ Name verified present in `modules/data/event_flags/emerald.txt:1064`. `get_event_flag`
    returns **False** for an unknown name, so a phantom here would look exactly like "not
    activated yet" and would make the activation loop run its whole budget every time."""
    from modules.memory import get_event_flag

    return get_event_flag(_STRENGTH_FLAG)


def _party_knows_strength() -> bool:
    return any(
        learned is not None and learned.move.name == "Strength"
        for mon in get_party()
        if mon is not None
        for learned in mon.moves
    )


def ensure_strength_learner() -> Generator:
    """Make sure SOMEBODY in the party knows Strength, teaching HM04 from the bag if not.

    ‼ MEASURED, AND IT IS NOT THE CHEAP TEACH IT FIRST LOOKED LIKE (2026-08-10, on
    `saves/magma_door.ss1`). HM04 is already in the bag and BADGE04 is held, so no fetch quest —
    but `can_learn_tm_hm(HM04)` is **False for Zigzagoon**, the established HM slave with a free
    move slot. Only **Mightyena L43 and Sceptile L43** can learn it and **both are full**, so the
    teach COSTS A MOVE SLOT ON A FIGHTER. `hm_learner_slot` breaks the level tie toward slot 0
    (Mightyena) and the expendable-slot picker takes **Taunt** — base power 0, a status move, so
    the damaging-move count does not drop. That is the good outcome, and it is asserted below
    rather than assumed."""
    if _party_knows_strength():
        return

    from modules.items import get_item_bag

    hm04 = next((slot.item for slot in get_item_bag().tms_hms if slot.item.name == "HM04"), None)
    if hm04 is None:
        raise BotModeError(
            "Strength: HM04 is not in the bag, so nobody can be taught Strength. It is obtained "
            "in Rusturf Tunnel; every save this chapter was built against already had it."
        )

    # ⭐ `#24-hm07funnel` — prefer a learner that cannot carry HM07. Preference only; falls
    # back to `hm_learner_slot` when no such mon exists, so no party is left worse off.
    slot = land_hm_learner_slot(hm04)
    if slot is None:
        raise BotModeError(
            "Strength: no party member can learn HM04. ‼ Note Zigzagoon CANNOT (measured) - "
            "the usual HM slave is not an option for this one."
        )

    learner = get_party()[slot]
    before = [learned.move.name for learned in learner.moves if learned is not None]
    _ch14_say(f"Story: teaching Strength to {learner.species.name} (slot {slot})...")
    yield from teach_hm_move(hm04, slot)

    if not _party_knows_strength():
        raise BotModeError(
            f"Strength: taught HM04 to {learner.species.name} (slot {slot}) but no party member "
            "knows Strength afterwards."
        )
    after = [learned.move.name for learned in get_party()[slot].moves if learned is not None]
    lost = [name for name in before if name not in after]
    # ‼ SAY WHAT IT COST. A silent move replacement on a front-line fighter is the kind of
    # change that shows up three batches later as "the lead got worse" with no trace of why.
    _ch14_say(
        f"Story: {get_party()[slot].species.name} learned Strength"
        + (f" (lost {', '.join(lost)})" if lost else "")
    )


def strength_push(map_enum, approach_tile, face_dir: str, *, tries: int = 8) -> Generator:
    """Stand beside a Strength boulder, face it, and push it ONE tile in `face_dir`.

    IDEMPOTENT and judged by the WORLD, following `_smash_rock`'s pattern - but with the
    opposite success test, because a boulder is not destroyed:

        SUCCESS = the boulder is NO LONGER on its tile **and** IS on the destination tile.

    ‼ Checking only "it left its tile" would call a push successful when the object was merely
    re-read badly, and checking only "something is on the destination" would be fooled by an NPC.
    Both halves are required.

    ‼ A push into a blocked tile FAILS SILENTLY IN-GAME - the boulder simply does not move and no
    message is printed. So this bounds its attempts and raises with the tiles named, rather than
    pressing a direction forever. (KI-34: a bounded loop re-entered by its dispatcher is still
    infinite; the caller must not retry a raise from here in a loop of its own.)

    Requires a party member that knows Strength (`ensure_strength_learner`) and BADGE04."""
    from modules.map import get_map_objects

    if face_dir not in _STRENGTH_STEP:
        raise BotModeError(f"strength_push: bad direction {face_dir!r}")
    dx, dy = _STRENGTH_STEP[face_dir]
    boulder_tile = (approach_tile[0] + dx, approach_tile[1] + dy)
    dest_tile = (boulder_tile[0] + dx, boulder_tile[1] + dy)

    def _object_on(tile):
        """The map object standing on `tile`, or None."""
        try:
            for obj in get_map_objects():
                if tuple(obj.current_coords) == tile:
                    return obj
        except Exception:  # noqa: BLE001 - cannot read objects; report "unknown" as absent
            return None
        return None

    #: ‼ THE BOULDER IS TRACKED BY `local_id`, NOT BY "is anything on that tile".
    #: A push moves the PLAYER TOO - onto the tile the boulder just left - so a test of the
    #: shape "nothing is on the old tile any more" reads FALSE on a push that worked perfectly,
    #: because the player is standing right there. That is the same family as the `#24-battleitems`
    #: bug where an HP comparison spanned a Pokémon switch: state sampled from a moving frame of
    #: reference needs its subject pinned. Pin it by identity.
    boulder_id: int | None = None

    def _boulder_now():
        """Where the TRACKED boulder is right now, or None if it cannot be read."""
        if boulder_id is None:
            return None
        try:
            for obj in get_map_objects():
                if getattr(obj, "local_id", None) == boulder_id:
                    return tuple(obj.current_coords)
        except Exception:  # noqa: BLE001
            return None
        return None

    def _pushed() -> bool:
        return _boulder_now() == dest_tile

    yield from _navigate_riding_out(map_enum, approach_tile)
    yield from wait_for_player_avatar_to_be_standing_still()

    # ‼ IDEMPOTENCY IS CHECKED ON THE TILES, NOT ON THE TRACKED ID - the id can only be read
    # while the boulder is still on its ORIGINAL tile, so a resume after a successful push has
    # nothing to track. "Something on the destination and nothing on the source" is the only
    # question answerable from a cold re-entry.
    if _object_on(dest_tile) is not None and _object_on(boulder_tile) is None:
        return  # already pushed on an earlier attempt - a recovery re-entry must be a no-op

    boulder = _object_on(boulder_tile)
    if boulder is None:
        raise BotModeError(
            f"Strength: no object on {boulder_tile} to push (standing {approach_tile} facing "
            f"{face_dir}). Either the map state is not what this plan assumed, or the boulder "
            "was already moved somewhere other than the expected destination."
        )
    boulder_id = getattr(boulder, "local_id", None)

    # --- 1. Switch the field move ON (‼ ONCE PER MAP - the flag is cleared by EVERY WARP) ----
    # ‼ CORRECTED 2026-08-13, MEASURED: this line used to say "once per SAVE - the flag is never
    # cleared". `ClearTempFieldEventData` clears it inside `LoadMapFromWarp`, so the guard below
    # is LOAD-BEARING on every room, not a cheap idempotency nicety. See `_STRENGTH_FLAG`.
    # `EventScript_StrengthBoulder`: interacting with the boulder opens "Would you like to use
    # STRENGTH?"; A advances the messages and takes the default YES, and
    # `EventScript_ActivateStrength` sets the flag. Judged by the FLAG, never by "the script
    # finished" - the YES/NO prompt IS an active script, and a field script interrupted by
    # anything can leave the script context reading active forever (the wedge `_smash_rock`
    # documents, and the reason `puzzle_solver.use_strength`'s
    # `wait_for_script_to_start_and_finish` gating is not reused here).
    # ‼ FACE FIRST, AND PRESS ONLY A IN THIS LOOP. Once the flag is set, a direction press
    # PUSHES - so a loop that mashes the direction to "make sure we are facing" would shove the
    # boulder an unknown number of tiles before the push phase ever runs, and this puzzle's
    # destinations are one tile wide.
    yield from ensure_facing_direction(face_dir)
    if not _strength_active():
        _ch14_say("Story: switching on Strength...")
        for _frame in range(1200):
            _check_abort()
            if _strength_active():
                break
            context.emulator.press_button("A")
            yield
            yield from wait_for_n_frames(3)
        if not _strength_active():
            raise BotModeError(
                f"Strength: could not switch the field move on at {boulder_tile} "
                f"(standing {approach_tile} facing {face_dir}). A party member knows Strength "
                "and BADGE04 is held, so the boulder prompt did not appear as expected."
            )
        # ‼‼ THE FLAG IS SET *MID-SCRIPT*, AND THAT COST TWO RUNS. `EventScript_ActivateStrength`
        # does `setflag FLAG_SYS_USE_STRENGTH` and then keeps going - field-move animation,
        # "STRENGTH made it possible to move boulders around", `releaseall`. The activation loop
        # above exits the instant the flag flips, which is while the player is still LOCKED by
        # `lockall`. Every push then pressed a direction at a locked avatar and did nothing, and
        # the failure looked exactly like "the destination is blocked" - with strength_active
        # True, the boulder present and the destination clear, which is what made it so
        # confusing. Ride the rest of the scene out before touching the D-pad.
        # ‼ GENERAL RULE: a flag set by a script is NOT the end of that script.
        yield from _ride_out_scripted_scene("B")
        yield from wait_until_truly_controllable()

    # --- 2. Push ---------------------------------------------------------------------------
    # ‼ A PUSH IS A WALK, AND A ONE-FRAME `press_button` IS NOT A WALK. The first build pressed
    # the direction once per attempt and waited: 8 attempts, the boulder never moved, and the
    # error said "check that the destination is walkable" — which was a red herring, because
    # (6,23)->(5,23) is collision 0 and elevation 3 on BOTH tiles (measured). The avatar simply
    # never took a step. `walk_one_tile` holds the direction until the tile actually changes,
    # which is what the game needs; it is UNBOUNDED by design (its own docstring: "will create
    # an endless loop if trying to run into a wall"), so it is bounded here — the same fix, and
    # the same reason, as `_fortree_walk_one_tile`.
    from modules.modes.util.walking import walk_one_tile

    for _attempt in range(tries):
        _check_abort()
        stepper = walk_one_tile(face_dir)
        frames = 0
        try:
            while True:
                next(stepper)
                frames += 1
                if frames > 600:
                    break  # blocked: the push did not take. The world test below decides.
                yield
        except StopIteration:
            pass
        finally:
            # ‼ `walk_one_tile` HOLDS the direction and B and only releases them once the tile
            # changes - so abandoning it early leaves BOTH STUCK DOWN, and every later attempt
            # in this loop then runs with a jammed D-pad. Releasing here is not tidiness; it is
            # what makes the retry loop mean anything.
            context.emulator.release_button(face_dir)
            context.emulator.release_button("B")
        yield from wait_for_n_frames(12)
        if _pushed():
            _ch14_say(f"Story: pushed the boulder {boulder_tile} -> {dest_tile}.")
            yield from wait_for_player_avatar_to_be_standing_still()
            return

    # ‼ A FAILED PUSH MUST REPORT THE WORLD, NOT JUST THE INTENT. The first two failures here
    # cost a run each because the message named a hypothesis ("check the destination is
    # walkable") instead of the state - and the destination WAS walkable both times. Dump what
    # the game actually shows: the flag, where we ended up, and every object with its id and
    # graphics, so the next failure is diagnosed from the log rather than from another run.
    try:
        where = tuple(get_player_avatar().local_coordinates)
    except Exception:  # noqa: BLE001
        where = None
    objects = []
    try:
        for obj in get_map_objects():
            objects.append(
                f"id={getattr(obj, 'local_id', '?')}@{tuple(obj.current_coords)}"
                f"/{getattr(obj, 'graphics_id', '?')}"
            )
    except Exception as error:  # noqa: BLE001
        objects.append(f"<unreadable: {type(error).__name__}>")
    raise BotModeError(
        f"Strength: the boulder at {boulder_tile} did not move to {dest_tile} in {tries} "
        f"pushes (standing {approach_tile} facing {face_dir}; we are now at {where}). "
        f"strength_active={_strength_active()} tracked_id={boulder_id} "
        f"boulder_now={_boulder_now()} objects={objects}"
    )


#: The MAGMA_HIDEOUT_1F boulder puzzle, as (approach tile, push direction).
#:
#: ‼ DERIVED FROM A MEASURED SIMULATION, NOT FROM LOOKING AT THE MAP (2026-08-10). A plain
#: collision flood of 1F (boulders treated as walls) was run over every subset of the three
#: boulders, and only these connect the entrance `(10,34)` to `(25,34)`:
#:      move (5,22) + (6,23) -> 298 tiles reachable, GOAL True
#:      move (5,22) + (7,22) -> 298 tiles reachable, GOAL True
#:      move (5,22) alone    ->  44 tiles, GOAL False   <- it is BEHIND the other two
#:      move either other alone -> 46-49 tiles, GOAL False
#: so **two pushes are the minimum** and `(5,22)` must be one of them.
#:
#: This plan was then validated step by step against its own END STATE - each approach tile
#: reachable at the moment it is needed, each destination walkable and empty - finishing with
#: boulders at `[(4,22), (5,23), (7,22)]`, **295 tiles reachable and `(25,34)` among them**.
#: ‼ That last check matters: a pushed boulder still exists, so a plan can open one corridor
#: and seal another. Simulating "the boulder is gone" would have missed it.
MAGMA_HIDEOUT_1F_PUSHES = (
    ((7, 23), "Left"),   # boulder (6,23) -> (5,23), opening the way to (6,22)
    ((6, 22), "Left"),   # boulder (5,22) -> (4,22), opening the northward corridor at x=5
)


#: 1F's only onward warp inside the entrance's collision component: `(25,34)` -> 2F_1R.
#: (`(20,22)` -> 2F_3R sits on a NINE-TILE ISLAND and `(31,3)` -> 2F_2R in a 70-tile one.)
MAGMA_HIDEOUT_1F_ONWARD = (25, 34)


def open_magma_hideout_1f() -> Generator:
    """Clear the Strength boulders that seal MAGMA_HIDEOUT_1F's entrance pocket.

    INTENT: make `1F (25,34)` - the warp to 2F_1R, and the only onward warp in the entrance's
    collision component - reachable. Until this runs, the bot can walk 44 of 1F's tiles and the
    chapter cannot proceed; this was measured live (`floors=['MAGMA_HIDEOUT_1F']`).
    GOAL/END STATE: `calculate_path` reaches `(25,34)`."""
    from modules.map import get_map_data
    from modules.map_path import calculate_path

    if _map_group_number() != MapRSE.MAGMA_HIDEOUT_1F.value:
        raise BotModeError(
            f"Magma Hideout: open_magma_hideout_1f() called on map {_map_group_number()}, "
            "not MAGMA_HIDEOUT_1F."
        )

    def _route_open() -> bool:
        """Can we path to the onward warp yet? The one test that matters."""
        try:
            here = get_map_data(MapRSE.MAGMA_HIDEOUT_1F, tuple(get_player_avatar().local_coordinates))
            calculate_path(here, get_map_data(MapRSE.MAGMA_HIDEOUT_1F, MAGMA_HIDEOUT_1F_ONWARD))
            return True
        except Exception:  # noqa: BLE001 - any planner refusal means "not open"
            return False

    if _route_open():
        return  # resume-safe: a previous visit already cleared it

    yield from ensure_strength_learner()

    for approach_tile, face_dir in MAGMA_HIDEOUT_1F_PUSHES:
        _check_abort()
        yield from strength_push(MapRSE.MAGMA_HIDEOUT_1F, approach_tile, face_dir)

    if not _route_open():
        raise BotModeError(
            "Magma Hideout 1F: both Strength pushes reported success but "
            f"{MAGMA_HIDEOUT_1F_ONWARD} is still unreachable. The push plan opens the route in "
            "simulation, so the live map state differs from the one it was derived from."
        )
    _ch14_say("Story: Magma Hideout 1F is open - the route to 2F_1R is clear.")


# ---------------------------------------------------------------------------
# §Ch15 EXIT - LEAVING the Magma Hideout (KI-56).
#
# ‼ WHY A CHAPTER NEEDS AN EXIT LEG AT ALL. Ch15 was graded BINARY on
# `GROUDON_AWAKENED_MAGMA_HIDEOUT`, which the game sets the instant Maxie falls - four floors
# deep. It therefore PASSED ITS OWN TEST on runs that ended permanently stuck. 1F's 44-tile
# entrance pocket is joined to the rest of the floor only by the two Strength pushes
# `MAGMA_HIDEOUT_1F_PUSHES` performs, and **boulder positions RESET when the map reloads**
# (KI-56, measured: the boulders read back at their ORIGINAL tiles). Walking back down, the bot
# arrives at `1F (25,34)` on the far side of that wall, and both push-from tiles - `(7,23)` and
# `(6,22)` - are inside the pocket it can no longer reach, so it cannot even re-push.
#
# MEASURED, with three controls (`tools/story-dev/probe_hideout_warp_graph.py`): from the return
# tile, a BFS over the whole eight-map warp graph reaches **18 of 20 nodes**, and the only two it
# misses are the exit warp `1F (10,34)` and `JAGGED_PASS` itself. **There is no walk-out.** A
# return-route study and a re-push are both closed off; the way out cannot be walked at all.
#
# ‼ SO THE DUNGEON SUPPLIES ITS OWN ESCAPE - which is almost certainly why a one-way boulder
# puzzle could be shipped here in the first place. `MagmaHideout_3F_3R/map.json` places an
# **Escape Rope item ball at `(9,19)`**, and 3F_3R is reachable even from the stranded tile.
# ---------------------------------------------------------------------------

#: The Escape Rope item ball, decomp `data/maps/MagmaHideout_3F_3R/map.json`.
HIDEOUT_ESCAPE_ROPE_MAP = MapRSE.MAGMA_HIDEOUT_3F_3R
HIDEOUT_ESCAPE_ROPE_TILE = (9, 19)

#: ‼ `(9,20)` IS THE ONLY APPROACH. An item ball is an object event, so it is reached by
#: standing beside it and pressing A - and of the four neighbours, `calculate_path` reaches
#: ONLY the one below it. `(9,18)`, `(8,19)` and `(10,19)` are all unreachable from both of
#: 3F_3R's warp arrival tiles (measured, `probe_hideout_warp_graph.py`). Facing is Up.
HIDEOUT_ESCAPE_ROPE_APPROACH = (9, 20)
HIDEOUT_ESCAPE_ROPE_FACING = "Up"

#: ‼‼ THE DECOMP MISSPELLS THIS FLAG - "ECAPE", not "ESCAPE" - and
#: `modules/data/event_flags/emerald.txt` carries the typo through as flag 1059. The
#: correctly-spelled name **does not exist**, and `get_event_flag` returns False **silently**
#: for an unknown name, which is indistinguishable from "the ball is still there". Spelled the
#: sensible way, this check would be a permanent, invisible lie. Do not "fix" it.
HIDEOUT_ESCAPE_ROPE_FLAG = "ITEM_MAGMA_HIDEOUT_3F_3R_ECAPE_ROPE"

#: 4F's OTHER warp. The route in is `1F (25,34) -> 2F_1R (17,33) -> 3F_1R (7,21) -> 4F`
#: (`MAGMA_HIDEOUT_ROUTE`), which never touches 3F_3R - so collecting the rope is a deliberate
#: one-warp detour off 4F after Maxie, not something the inbound route passes.
HIDEOUT_4F_TO_3F_3R = (20, 21)

#: Where an Escape Rope actually puts us. ‼ The hideout has NO `setescapewarp` in any of its
#: four map scripts, so this is not read off a script: `UpdateEscapeWarp` (decomp
#: `src/overworld.c:677`, called from `src/field_control_avatar.c:826`) stamps
#: `gSaveBlock1Ptr->escapeWarp` on EVERY warp step where the map being left is outdoors and the
#: map being entered is not - so walking Jagged Pass -> 1F sets it automatically. Read live out
#: of the save block on the stranded state: `JAGGED_PASS (16,19)`, collision 0
#: (`probe_escape_warp.py`, which also checks the pre-entry NEGATIVE ARM reads `ROUTE112`).
HIDEOUT_ESCAPE_LANDING = MapRSE.JAGGED_PASS


def _held_quantity(item_name: str) -> int:
    """How many of `item_name` are in the bag."""
    from modules.items import get_item_bag, get_item_by_name

    return get_item_bag().quantity_of(get_item_by_name(item_name))


def _escape_ropes_held() -> int:
    """How many Escape Ropes are in the bag."""
    return _held_quantity("Escape Rope")


def collect_item_ball(
    map_enum, ball_tile, approach, facing, flag_name: str, item_name: str, *, label: str = ""
) -> Generator:
    """Walk to a visible ITEM BALL and pick it up. Returns True if we hold the item afterwards.

    `#24-grounditems`. This is the generalisation of the Magma Hideout's Escape Rope pickup, which
    was the only instance in the codebase; both callers now share it rather than diverging.

    ‼‼ GRADED ON THE BAG, NOT ON THE FLAG, and that is not a style choice. `finditem` branches to
    `Common_EventScript_ShowBagIsFull` when the pocket is full: it gives **no item AND sets no
    flag**. A flag-based success test therefore hangs for its whole bound on a ball that can never
    be collected, and then reports "the ball is still there" - which is true and useless. The bag
    delta is the only signal that separates "collected" from "could not collect".

    ‼ AN ITEM BALL IS AN OBJECT, NOT A TILE. You stand BESIDE it and press A. Not every neighbour
    is reachable - the Magma Hideout's Escape Rope had exactly one usable approach out of four -
    so the caller passes the approach and facing it measured, rather than this helper guessing.

    ‼ AND THE BALL VANISHES WHEN TAKEN, freeing its tile. That is load-bearing for the Aqua
    Hideout's Master Ball, which is only reachable by standing where the Nugget used to be.

    :param flag_name: the ball's `FLAG_ITEM_...` (no `FLAG_` prefix). Set means already taken.
    :param item_name: the bag item name, e.g. "Master Ball" - what success is measured on.
    """
    from modules.memory import _event_flags, get_event_flag

    what = label or item_name

    # ‼ NAME CONTROL. `get_event_flag` returns False for an unknown name WITHOUT raising, so a
    # typo would read as "the ball is still there" for ever and we would walk to an empty tile
    # on every visit.
    if flag_name not in _event_flags:
        raise BotModeError(
            f"collect_item_ball({what}): unknown flag name {flag_name!r}. It reads False "
            "SILENTLY, so 'already taken' could never be detected. Fix the name."
        )

    if get_event_flag(flag_name):
        # Someone already took it - this run, an earlier run, or the player. Not an error here;
        # the caller decides whether holding the item matters.
        return _held_quantity(item_name) > 0

    before = _held_quantity(item_name)

    yield from _navigate_riding_out(map_enum, approach)
    yield from wait_for_player_avatar_to_be_standing_still()
    yield from ensure_facing_direction(facing)
    yield

    # `finditem` prints a message chain ("You found a MASTER BALL!" / "put away in the ... POCKET"),
    # so A-ride it rather than pressing once.
    for _frame in range(1200):
        _check_abort()
        if _held_quantity(item_name) > before:
            break
        context.emulator.press_button("A")
        yield
        yield from wait_for_n_frames(3)

    if _held_quantity(item_name) <= before:
        where = _map_group_number()
        try:
            tile = tuple(get_player_avatar().local_coordinates)
        except Exception as error:  # noqa: BLE001 — this IS the failure report; an unreadable
            # avatar must not replace the diagnosis with a crash from the diagnostic.
            tile = f"<unreadable: {type(error).__name__}>"
        raise BotModeError(
            f"collect_item_ball({what}): pressed A at {ball_tile} for 1200 frames and the bag "
            f"still holds {before} (standing {tile} on map {where}, facing {facing}; "
            f"{flag_name}={get_event_flag(flag_name)}). ‼ A SET flag with no bag change means the "
            "items pocket was FULL; an UNSET flag means we were not facing the ball."
        )

    # ‼ A flag set by a script is NOT the end of that script (the Strength lesson) - ride the rest
    # of the message chain out before anything else touches the D-pad.
    yield from _ride_out_scripted_scene("B")
    _ch14_say(f"Story: collected {what} at {map_enum.name} {ball_tile}.")
    return True


def collect_hideout_escape_rope() -> Generator:
    """Pick up the Escape Rope the Magma Hideout provides, on 3F_3R `(9,19)`.

    INTENT: put an Escape Rope in the bag so the chapter can LEAVE. Nothing else in this era
    supplies one - the bag reads **0 ropes on every anchor save**, and ‼ Lavaridge Mart (the
    nearest to the Jagged Pass approach) does **not stock them**; the closest marts that do are
    Fallarbor, Slateport, Rustboro, Petalburg and Lilycove, all a long detour off a leg that has
    already produced a measured whiteout.
    STORY CONDITION: inside the hideout, on 4F (post-Maxie) or already on 3F_3R.
    GOAL/END STATE: `_escape_ropes_held() > 0`. Graded on THE BAG, never on the flag - see below.
    """
    if _escape_ropes_held() > 0:
        return  # resume-safe: a previous attempt already collected it

    if _map_group_number() == MapRSE.MAGMA_HIDEOUT_4F.value:
        _ch14_say("Story: Magma Hideout - detouring to 3F_3R for the Escape Rope...")
        yield from _enter_warp_by_navigation(
            lambda: _map_group_number() == HIDEOUT_ESCAPE_ROPE_MAP.value,
            MapRSE.MAGMA_HIDEOUT_4F,
            HIDEOUT_4F_TO_3F_3R,
            label="Magma Hideout 4F -> 3F_3R (Escape Rope)",
        )
        yield from wait_until_truly_controllable()

    if _map_group_number() != HIDEOUT_ESCAPE_ROPE_MAP.value:
        raise BotModeError(
            "Magma Hideout: cannot collect the Escape Rope from map "
            f"{_map_group_number()} - this leg starts on MAGMA_HIDEOUT_4F (warping via "
            f"{HIDEOUT_4F_TO_3F_3R}) or on {HIDEOUT_ESCAPE_ROPE_MAP.name} itself."
        )

    # ‼ THE BALL CAN ONLY BE TAKEN ONCE. If the flag is set and the bag is still empty, the rope
    # was collected on some earlier run and then used or tossed - there is no second one, and this
    # chapter cannot leave the hideout on foot (KI-56), so that IS fatal here even though
    # `collect_item_ball` treats it as merely "nothing to do".
    held = yield from collect_item_ball(
        HIDEOUT_ESCAPE_ROPE_MAP,
        HIDEOUT_ESCAPE_ROPE_TILE,
        HIDEOUT_ESCAPE_ROPE_APPROACH,
        HIDEOUT_ESCAPE_ROPE_FACING,
        HIDEOUT_ESCAPE_ROPE_FLAG,
        "Escape Rope",
        label="the Magma Hideout Escape Rope",
    )
    if not held:
        raise BotModeError(
            f"Magma Hideout: the Escape Rope ball at {HIDEOUT_ESCAPE_ROPE_TILE} has already "
            f"been taken ({HIDEOUT_ESCAPE_ROPE_FLAG} is set) but the bag holds none. This run "
            "cannot leave the hideout on foot (KI-56) and has no rope to leave with."
        )


def use_escape_rope_to_leave_hideout() -> Generator:
    """Use an Escape Rope and confirm we are OUT, on Jagged Pass.

    INTENT: end §Ch15 standing outside the dungeon and able to continue - the half the old
    binary acceptance test never asked about.
    GOAL/END STATE: not on any hideout map, standing on `JAGGED_PASS`, truly controllable."""
    from modules.items import get_item_by_name
    from modules.modes.util.items import use_item_from_bag

    if not _inside_magma_hideout():
        return  # resume-safe: already out

    if _escape_ropes_held() == 0:
        raise BotModeError(
            "Magma Hideout: use_escape_rope_to_leave_hideout() called with no Escape Rope in "
            "the bag. `collect_hideout_escape_rope()` must run first."
        )

    _ch14_say("Story: using the Escape Rope to leave the Magma Hideout...")
    # ‼ `wait_for_start_menu_to_reappear=False`: using an Escape Rope closes the menus and warps,
    # so the start menu never comes back and waiting for it would burn that helper's own bound.
    yield from use_item_from_bag(get_item_by_name("Escape Rope"), wait_for_start_menu_to_reappear=False)

    # ‼‼ THE MESSAGE MUST BE DISMISSED OR THE WARP NEVER HAPPENS - MEASURED, NOT GUESSED.
    # The first driven run consumed the rope and then sat on the same tile for 1800 frames with
    # `controllable=False`. The harness's no-progress dump named the cause exactly:
    # **`Task_ContinueTaskAfterMessagePrints` was active.** `ItemUseOnFieldCB_EscapeRope`
    # (decomp `src/item_use.c:903`) calls `DisplayItemMessageOnField(taskId, gStringVar4,
    # Task_UseDigEscapeRopeOnField)`, and `StartEscapeRopeFieldEffect()` only runs from that
    # CALLBACK - which fires when the message is dismissed. A wait loop that merely yields waits
    # forever on a text box. This is the same shape as the Strength lesson recorded above: an
    # item being consumed is NOT the end of the script that consumes it.
    # ‼ B, NEVER A. B dismisses a message and interacts with nothing; a stray A on the far side
    # of the warp would talk to whoever is standing on Jagged Pass.
    for _frame in range(1800):
        _check_abort()
        if not _inside_magma_hideout():
            break
        if _frame % 4 == 0:
            context.emulator.press_button("B")
        yield

    if _inside_magma_hideout():
        # Report the WORLD, not a hypothesis: a rope that was consumed but did not warp is a
        # completely different bug from one the game refused, and the count separates them.
        raise BotModeError(
            "Magma Hideout: used an Escape Rope and 1800 frames later we are still inside "
            f"(map {_map_group_number()}, tile {tuple(get_player_avatar().local_coordinates)}, "
            f"{_escape_ropes_held()} rope(s) left, "
            f"controllable={player_avatar_is_controllable()}). "
            "`MagmaHideout_1F/map.json` has allow_escaping=true, so the item is legal here. "
            "‼ If the rope count went DOWN, the item was accepted and the warp is what stalled - "
            "check for `Task_ContinueTaskAfterMessagePrints`, i.e. an undismissed message box."
        )

    yield from wait_until_truly_controllable()

    where = _map_group_number()
    if where != HIDEOUT_ESCAPE_LANDING.value:
        # Not fatal to the escape itself - we ARE out - but it means the landing tile this
        # chapter was built on is not where the game put us, and the caller should know.
        raise BotModeError(
            f"Magma Hideout: the Escape Rope landed us on map {where}, not "
            f"{HIDEOUT_ESCAPE_LANDING.name}. `escapeWarp` was measured as "
            "JAGGED_PASS (16,19) on this anchor; it is stamped on the way IN, so a run that "
            "entered the hideout by some other route would land somewhere else."
        )

    _ch14_say(f"Story: OUT of the Magma Hideout - standing on {HIDEOUT_ESCAPE_LANDING.name}.")


def leave_magma_hideout() -> Generator:
    """§Ch15's exit: get the Escape Rope, use it, be outside. No-op when already out."""
    if not _inside_magma_hideout():
        return
    yield from collect_hideout_escape_rope()
    yield from use_escape_rope_to_leave_hideout()


# ---------------------------------------------------------------------------
# Chapter 16 - the SLATEPORT HARBOR submarine theft (§Ch16).
#
# ‼ EVERY constant here is decomp-verified (design §Ch16, 2026-08-11). Re-derive:
#     gh api repos/pret/pokeemerald/contents/data/maps/SlateportCity_Harbor/scripts.inc
#     gh api repos/pret/pokeemerald/contents/data/maps/SlateportCity_Harbor/map.json
#     cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch16_anchor.py   (the era gate)
#     cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch16_travel.py   (the route, static)
# ---------------------------------------------------------------------------

#: `SLATEPORT_CITY (28,12)` -> `SLATEPORT_CITY_HARBOR` (warp id 8, lands at harbor (11,14)).
#: ‼ A WARP TILE: stepping onto it FIRES it, so it is an `_enter_warp_by_navigation` target,
#: never a plain `navigate_to` destination (ML-9).
SLATEPORT_HARBOR_DOOR = (28, 12)

#: The plain walkable tile below the door - and the harbor's own `setescapewarp` return tile,
#: so it is guaranteed to exist and be standable.
SLATEPORT_HARBOR_DOOR_APPROACH = (28, 13)

#: ‼ THE TRIGGER. Four coord events fire `SlateportCity_Harbor_EventScript_AquaEscapeTrigger0..3`,
#: all gated on `VAR_SLATEPORT_HARBOR_STATE == 1`, at x=8, y=11..14 (elevation 3).
#: **Trigger 3 (8,14) is chosen deliberately**: it is the only one that `applymovement`s the
#: player UP into the scene itself, so the walk-in is scripted rather than something we must get
#: right. It is also the closest to the landing tile (3 waypoints, static).
HARBOR_AQUA_TRIGGER = (8, 14)

#: ‼ CAPT. STERN, AND HE IS THE WAY IN - NOT AN OBSTACLE (KI-57).
#: `SlateportCity_OnTransition` -> `MovePeopleForSternInterview` does
#: `setobjectxyperm LOCALID_SLATEPORT_CAPT_STERN, 28, 13` whenever `VAR_SLATEPORT_CITY_STATE == 1`
#: - a var **Ch15's own Maxie script sets**. `(28,13)` is the ONLY tile touching the harbor door
#: `(28,12)`, which is set into a solid wall (measured tile-by-tile,
#: `tools/story-dev/probe_slateport_harbor_map.py`). Talking to him warps the player inside.
SLATEPORT_STERN_TILE = (28, 13)

#: ‼ `(27,13)` IS THE ONLY APPROACH, and it is not a preference. Stern's four neighbours are
#: `(28,12)` the door itself (a wall tile from this side), `(28,14)` Gabby and `(29,13)` Ty -
#: both `setobjectxyperm`ed there by the same script - and `(27,13)`. Measured reachable in
#: 19 waypoints from the Slateport Pokémon Center doorstep. Face RIGHT to look east at him.
SLATEPORT_STERN_APPROACH = (27, 13)
SLATEPORT_STERN_FACING = "Right"

#: ‼‼ HEAL BEFORE THE HAUL. THIS IS A FIX FOR A MEASURED WHITEOUT, NOT A PRECAUTION - the same
#: sentence `MAGMA_ROUTE_HEALS` carries, for the same reason, one chapter later.
#:
#: MEASURED on `post_maxie.ss1`, the anchor this chapter starts from: the party is at
#: **47/534 HP = 8.8%**, with **five of six members at 0 HP** and only Swellow (47/112) standing.
#: That is what the Magma Hideout hands over - Ch15 ends four floors deep having fought Tabitha,
#: the grunts and Maxie, and nothing heals in between. Leg 1 then walks Jagged Pass -> Route 112
#: -> Route 111 -> Mauville -> Route 110 -> Slateport on one damaged Pokémon, and every driven
#: run so far lost a fight and whited out (`whiteouts=1`, three for three).
#:
#: ‼ AND THE WHITEOUT WAS HIDING THE BUG, because a whiteout HEALS: the chapter still reached
#: `harbor_state=2` and `post_harbor.ss1` reads 100% party HP - so the acceptance test passed
#: **because** the run failed. A green chapter that only works via an accidental full heal is
#: one unlucky fight away from a real failure, and nothing in the result said so.
#:
#: ‼ ORDER IS NEAREST-FIRST, AND THAT IS THE WHOLE POINT - MEASURED. The first version of this
#: list started at Mauville, and the run was **frame-identical** to the unhealed one up to
#: `f14345`: the route to Mauville is a strict PREFIX of the route to Slateport, so the same
#: encounters happened at the same frames and the whiteout landed **before** the first heal.
#: Both heals then ran (log: "healing at MAUVILLE_CITY", "healing at SLATEPORT_CITY") and the
#: chapter passed - with `whiteouts=1` unchanged. A heal stop that the party cannot REACH alive
#: is not a fix, and the identical frame number is what proved it rather than a hunch.
#:
#: ‼ LAVARIDGE IS FIRST DESPITE §Ch15 CALLING IT UNREACHABLE, because Ch15's measurement was
#: taken somewhere else. Its three failures - *"Cannot reach LAVARIDGE_TOWN: it is not walkable
#: from ROUTE112"* - were from `ROUTE112 (28,28)`, the **cable-car station on Route 112 NORTH**.
#: This chapter comes DOWN Jagged Pass and leaves it at the *south* end (Ch15's own note: "the
#: door at y=18 cannot be reached from the Route 112 entrance at y=40"), which is the side
#: Lavaridge connects to. Same map name, different component - so Ch15's result does not
#: transfer, and it is tried here best-effort rather than assumed either way.
#:
#: Slateport's own centre is the last stop: it is in the destination city anyway, and it makes
#: the post-Ch16 anchor healthy BY DESIGN rather than by accidental whiteout.
SLATEPORT_ROUTE_HEALS = (
    (PokemonCenter.LavaridgeTown, (9, 7)),
    (PokemonCenter.MauvilleCity, (22, 6)),
    (PokemonCenter.SlateportCity, (19, 20)),
)

#: Being on either of these means the haul is done and the heal stops must not walk backwards.
_SLATEPORT_PAST_HAUL = (MapRSE.SLATEPORT_CITY_HARBOR.value,)


def _city_state() -> int:
    """`VAR_SLATEPORT_CITY_STATE`, or -1 if unreadable.

    0 = before the museum beat, **1 = the Stern interview is staged and Stern is standing in the
    harbor doorway**, 2 = the interview scene has run, Stern is `removeobject`ed and the doorway
    is clear. This is the var that decides whether Ch16 talks its way in or walks in.

    ‼ NO `VAR_` PREFIX - same trap as `_harbor_state()`: `get_event_var` returns **-1** for an
    unknown name without raising, and a -1 here would silently take the "already done" branch.
    """
    from modules.memory import get_event_var

    try:
        return int(get_event_var("SLATEPORT_CITY_STATE"))
    except Exception as error:  # noqa: BLE001 - an unreadable var is reported as -1, not a crash,
        # because this runs inside a chapter whose failure message must name the STATE it saw.
        _ch14_say(f"Story: Ch16 could not read SLATEPORT_CITY_STATE ({type(error).__name__})")
        return -1


def _harbor_state() -> int:
    """`VAR_SLATEPORT_HARBOR_STATE`, or -1 if unreadable.

    ‼ NO `VAR_` PREFIX - the reader's table is keyed `SLATEPORT_HARBOR_STATE`, and
    `get_event_var` returns **-1** for an unknown name *without raising*. A `VAR_`-prefixed read
    silently cost an anchor capture on 2026-08-11 (see `27-INJECTION-SURFACE.md` section 2.2).
    """
    from modules.memory import get_event_var

    try:
        return int(get_event_var("SLATEPORT_HARBOR_STATE"))
    except Exception as error:  # noqa: BLE001 - a probe reports, it does not crash the chapter
        _ch14_say(f"Story: could not read SLATEPORT_HARBOR_STATE ({type(error).__name__})")
        return -1


def do_slateport_harbor_theft() -> Generator:
    """Chapter 16 - watch Team Aqua steal the submarine at Slateport Harbor.

    INTENT: the beat Maxie's defeat opens. Archie takes Captain Stern's submarine and names
    Lilycove as Aqua's base; the scene clears the two grunts blocking the Aqua Hideout entrance,
    which is the NEXT chapter's door.

    STORY CONDITION: `VAR_SLATEPORT_HARBOR_STATE == 1`. Maxie's defeat sets it
    (`MagmaHideout_4F_EventScript_Maxie`), so Ch15 is the prerequisite and nothing else is.
    Checked, not assumed.

    ‼ THERE IS NO BATTLE IN THIS CHAPTER. It is a coord-trigger cutscene, which makes it the
    cheapest remaining beat and its acceptance test binary.

    HOW IT WORKS - EXPLICIT SHORT LEGS, each failing where it broke (the Ch14a/Ch15 pattern):
      1. Cross to SLATEPORT_CITY and stand beside the harbor door.
      2. Step onto the door tile to warp in.
      3. Walk west along row 14 to trigger 3.
      4. Ride the scene out and WAIT FOR CONTROL.

    ‼‼ THE TRAP, AND IT HAS COST THIS PROJECT TWO RUNS BEFORE. `setvar VAR_SLATEPORT_HARBOR_STATE,
    2` runs roughly HALFWAY through the script - Stern's approach, a second `msgbox`, two
    `setflag`s and `releaseall` all follow it. Exiting the wait the instant the var flips leaves
    the avatar `lockall`ed and every later button press does nothing. That is exactly the
    `EventScript_ActivateStrength` failure of 2026-08-10.
    => **Grade on the var; WAIT FOR CONTROL.** Both halves, in that order.

    ‼ KNOWN RISK - KI-53. Static `calculate_path` FAILS for `ROUTE110 -> SLATEPORT_CITY` while the
    exact reverse plans in 30 waypoints. That is why leg 1 is its own leg: if it breaks, it names
    itself instead of arriving as "the chapter does not work". ‼ A static FAIL is NOT a verdict -
    `navigate_to_anywhere` routes through the WARP GRAPH and re-plans after every warp, and Ch15's
    Mauville -> Route 112 leg succeeded while planning statically as FAIL.

    GOAL/END STATE: `VAR_SLATEPORT_HARBOR_STATE == 2` AND the avatar controllable. Grade it BINARY.
    """
    if _harbor_state() >= 2:
        _ch14_say("Story: the Slateport submarine scene has already run - skipping.")
        return

    # ‼ GUARD, NEVER ASSUME. A wrong-era save reads 0 here and the coord triggers are simply
    # inert - the bot would walk to the tile, nothing would happen, and the failure would look
    # like a navigation bug. Seven probes were spent on exactly that confusion on 2026-08-10.
    state = _harbor_state()
    if state != 1:
        raise BotModeError(
            f"Slateport Harbor: SLATEPORT_HARBOR_STATE is {state}, not 1, so the Aqua-escape "
            f"coord triggers are inert. "
            + (
                "It reads -1, which means the VAR NAME is wrong, not that the era is. "
                if state == -1
                else "Beat Maxie in the Magma Hideout first (Ch15 sets this var). "
            )
            + "Run probe_ch16_anchor.py before building on this save."
        )

    def _in_harbor() -> bool:
        try:
            return (
                get_map_data_for_current_position().map_group_and_number
                == MapRSE.SLATEPORT_CITY_HARBOR.value
            )
        except Exception as error:  # noqa: BLE001 - an unreadable map means "not there yet"
            _ch14_say(f"Story: Ch16 map read failed ({type(error).__name__})")
            return False

    # --- Legs 1+2: TALK TO CAPT. STERN. He is not an obstacle, he is the door. ---------------
    #
    # ‼‼ THIS IS NOT "WALK TO THE HARBOR DOOR", AND THE FIRST VERSION THAT WAS COST A RUN (KI-57).
    # `SlateportCity_OnTransition` runs `MovePeopleForSternInterview` whenever
    # `VAR_SLATEPORT_CITY_STATE == 1`, whose first line is
    #       setobjectxyperm LOCALID_SLATEPORT_CAPT_STERN, 28, 13
    # and `(28,13)` is the ONLY tile touching the harbor door `(28,12)` - the door is set into a
    # solid wall, measured tile by tile (`probe_slateport_harbor_map.py`). ‼ And **§Ch15 is what
    # sets that var**: `MagmaHideout_4F/scripts.inc` does `clearflag
    # FLAG_HIDE_SLATEPORT_CITY_CAPTAIN_STERN` / `setvar VAR_SLATEPORT_CITY_STATE, 1`. So
    # completing the previous chapter is precisely what puts Stern in the doorway.
    #
    # ‼ THE DOOR IS NOT MEANT TO BE WALKED THROUGH IN THIS ERA. `SlateportCity_EventScript_
    # CaptStern` - i.e. TALKING to him - plays the interview and the Team Aqua announcement and
    # ends with:
    #       removeobject LOCALID_SLATEPORT_CAPT_STERN
    #       setvar       VAR_SLATEPORT_CITY_STATE, 2
    #       warp         MAP_SLATEPORT_CITY_HARBOR, 11, 14
    # **The script carries the player in.** `(11,14)` is the same tile the door warp lands on, so
    # leg 3 is unchanged. This is also the faithful reading: a human here talks to the man being
    # interviewed, they do not shove past him.
    # --- Leg 0: HEAL. ‼ MEASURED, NOT PRECAUTIONARY - see `SLATEPORT_ROUTE_HEALS`. -----------
    # The anchor hands this chapter a party at 8.8% HP with five of six fainted, and every run
    # before this existed whited out on the haul. A heal stop is allowed to FAIL without killing
    # the chapter (a PC we cannot route to is a lost nice-to-have, not a lost run) - but it is
    # always REPORTED, never swallowed, so "we healed" and "we could not" never look alike.
    if _map_group_number() not in _SLATEPORT_PAST_HAUL:
        for center, door_approach in SLATEPORT_ROUTE_HEALS:
            _check_abort()
            if _map_group_number() in _SLATEPORT_PAST_HAUL:
                break
            city = center.value[0]
            try:
                _ch14_say(f"Story: healing at {city.name} before the Slateport haul...")
                yield from _navigate_riding_out(city, door_approach)
                yield from heal_in_pokemon_center(center)
                yield from wait_until_truly_controllable()
            except BotModeError as error:
                # ⛔⛔ KI-81 / `#24-abortswallow` — THIS HANDLER WAS UNDOING THE 2026-08-16 GUARD.
                # `heal_in_pokemon_center` deliberately RE-RAISES on the latch
                # (`higher_level_actions.py:364/388/437`); catching it here threw that away one
                # frame later, and the chapter then continued on a dead run. Latch-keyed.
                reraise_if_aborting(error)
                _ch14_say(f"Story: heal stop at {city.name} SKIPPED - {str(error)[:120]}")

    if _city_state() < 2:
        _ch14_say("Story: Ch16 - crossing to Slateport to talk to Capt. Stern...")
        yield from _navigate_riding_out(MapRSE.SLATEPORT_CITY, SLATEPORT_STERN_APPROACH)
        yield from wait_until_truly_controllable()
        yield from ensure_facing_direction(SLATEPORT_STERN_FACING)
        yield

        # A-ride the scene. It is a long chain of MSGBOX_DEFAULT plus applymovements, and it ends
        # in a `warp`, so the success test is THE MAP CHANGING (or the var reaching 2) - never
        # "the script finished", which is true mid-scene while the avatar is still `lockall`ed.
        # ‼ Alternate A and B as the Maxie and Flannery loops do: A advances and confirms, B
        # clears the message chain, and a pure-A loop can re-open a menu it just closed.
        _ch14_say(f"Story: Ch16 - talking to Capt. Stern at {SLATEPORT_STERN_TILE}...")
        frames = 0
        while not _in_harbor() and _city_state() < 2:
            _check_abort()
            context.emulator.press_button("B" if frames % 3 else "A")
            frames += 1
            if frames > 30000:
                raise BotModeError(
                    "Slateport: talked at Capt. Stern for 30,000 frames and neither reached the "
                    f"harbor nor moved SLATEPORT_CITY_STATE off {_city_state()} (standing "
                    f"{tuple(get_player_avatar().local_coordinates)} on map "
                    f"{_map_group_number()}, facing {SLATEPORT_STERN_FACING}). ‼ Check we are "
                    f"actually adjacent to {SLATEPORT_STERN_TILE} and that he is still there - "
                    "if VAR_SLATEPORT_CITY_STATE is not 1, OnTransition never placed him."
                )
            yield

        # The `warp` at the end of the scene is the last thing it does; ride out the rest.
        yield from _ride_out_scripted_scene("B")
        yield from wait_until_truly_controllable()
    else:
        # RESUME PATH ONLY. Once the scene has run, `VAR_SLATEPORT_CITY_STATE` is 2, Stern has
        # been `removeobject`ed and the doorway is clear - so a re-entry walks in through the
        # door like any other building. This branch is unreachable on a first pass.
        _ch14_say("Story: Ch16 - the Stern scene has already run; entering the harbour by door.")
        yield from _navigate_riding_out(MapRSE.SLATEPORT_CITY, SLATEPORT_HARBOR_DOOR_APPROACH)
        yield from wait_until_truly_controllable()
        yield from _enter_warp_by_navigation(
            _in_harbor, MapRSE.SLATEPORT_CITY, SLATEPORT_HARBOR_DOOR, label="Slateport Harbor door"
        )
        yield from wait_until_truly_controllable()

    if not _in_harbor():
        raise BotModeError(
            f"Slateport Harbor: expected to be inside the harbour but we are on map "
            f"{_map_group_number()} at {tuple(get_player_avatar().local_coordinates)} "
            f"(SLATEPORT_CITY_STATE={_city_state()}). The Stern scene ends in a `warp` to "
            "SLATEPORT_CITY_HARBOR (11,14), so reaching state 2 without the map changing means "
            "the scene was interrupted."
        )

    # --- Leg 3: walk to trigger 3 -----------------------------------------------------------
    # ‼ `OnTransition` REWRITES THIS MAP: it hides the patrons and moves Capt. Stern to (12,13)
    # when the era is right, so `map.json`'s object list is NOT what is standing here. Do not
    # derive walkability around objects from the static file (design Ch16).
    _ch14_say("Story: Ch16 - walking to the Aqua trigger...")
    yield from _navigate_riding_out(MapRSE.SLATEPORT_CITY_HARBOR, HARBOR_AQUA_TRIGGER)

    # --- Leg 4: ride the scene out, then WAIT FOR CONTROL ------------------------------------
    yield from _ride_out_scripted_scene("B")
    yield from wait_until_truly_controllable()

    if _harbor_state() < 2:
        raise BotModeError(
            f"Slateport Harbor: reached the trigger at {HARBOR_AQUA_TRIGGER} but "
            f"SLATEPORT_HARBOR_STATE is {_harbor_state()}, not 2 - the Aqua escape scene did "
            f"not run. ‼ Check that the trigger tile was actually STEPPED ON (a coord event "
            f"fires on entry, not on standing)."
        )
    _ch14_say("Story: SUBMARINE STOLEN - Slateport Harbor complete. Aqua's hideout is open.")


# ---------------------------------------------------------------------------
# Chapter 17 - the LILYCOVE AQUA HIDEOUT (§Ch17).
#
# ‼ EVERY constant here is decomp-verified and GRAPH-SOLVED, not eyeballed. Re-derive with:
#     cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_aqua_hideout_graph.py
#
# THE BEAT: `AquaHideout_B2F_EventScript_Matt` -> `TRAINER_MATT` -> on defeat
# `AquaHideout_B2F_EventScript_SubmarineEscape` sets **`FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE`**
# (and `FLAG_HIDE_LILYCOVE_CITY_AQUA_GRUNTS`). That flag is the whole acceptance.
#
# ‼‼ WHY THIS CHAPTER CANNOT USE A PLANNER, AND WHY IT LOOKS NOTHING LIKE THE OTHERS.
# B1F is a **WARP-PANEL MAZE**: **21 of its 25 warps lead back to B1F itself** (including a 3x4
# panel grid at x=42/45/48, y=3..17), and B2F carries six more same-map panels.
# `calculate_path` "is not able to use warps" (its own docstring), so no planner can cross these
# floors - the same shape that made KI-56 look like a strand. The route below was solved by BFS
# over the ROM warp table and bounces **B1F -> B2F -> B1F -> B2F**; that is not the search being
# silly, it is how the dungeon is built.
# ---------------------------------------------------------------------------

#: `LILYCOVE_CITY (70,5)` -> `AQUA_HIDEOUT_1F` (arrive `(13,27)`). A WARP TILE: stepping on it
#: fires it, so it is an `_enter_warp_by_navigation` target, never a `navigate_to` destination.
AQUA_HIDEOUT_DOOR = (70, 5)

#: ‼ THE ERA GATE. Ch16's harbor scene **SETS** these two - a HIDE flag SET means the grunt is
#: gone. Checked, never assumed: an unknown flag name reads False silently, which would look
#: exactly like "still blocked".
AQUA_ENTRANCE_FLAGS = (
    "HIDE_AQUA_HIDEOUT_1F_GRUNT_1_BLOCKING_ENTRANCE",
    "HIDE_AQUA_HIDEOUT_1F_GRUNT_2_BLOCKING_ENTRANCE",
)

#: The maze, as `(map we stand on, warp tile to step on, expected map, expected arrival tile)`.
#: Solved by `probe_aqua_hideout_graph.py`; every destination is the ROM warp table's own answer.
#:
#: ‼ SPLIT IN TWO BY THE MASTER BALL DETOUR (`#24-masterball`). Leg A ends at `B1F (23,10)`, the
#: staging node for the treasure room; leg B rejoins and runs on to Matt. The two legs share the
#: prefix `(29,1) -> (27,4) -> (3,15)` with the direct route, and diverge there.
AQUA_HIDEOUT_ROUTE_TO_TREASURE = (
    (MapRSE.AQUA_HIDEOUT_1F, (22, 1), MapRSE.AQUA_HIDEOUT_B1F, (29, 1)),
    (MapRSE.AQUA_HIDEOUT_B1F, (27, 4), MapRSE.AQUA_HIDEOUT_B1F, (3, 15)),
    # --- into the 3x4 warp-panel grid at x=42/45/48: THIS is what guards the Master Ball ---
    (MapRSE.AQUA_HIDEOUT_B1F, (3, 20), MapRSE.AQUA_HIDEOUT_B1F, (45, 3)),
    (MapRSE.AQUA_HIDEOUT_B1F, (42, 5), MapRSE.AQUA_HIDEOUT_B1F, (48, 9)),
    (MapRSE.AQUA_HIDEOUT_B1F, (45, 9), MapRSE.AQUA_HIDEOUT_B1F, (45, 13)),
    (MapRSE.AQUA_HIDEOUT_B1F, (42, 13), MapRSE.AQUA_HIDEOUT_B1F, (48, 17)),
    (MapRSE.AQUA_HIDEOUT_B1F, (42, 17), MapRSE.AQUA_HIDEOUT_B1F, (23, 10)),
)

#: Leg B: back out of the treasure room and on to Matt.
#: ‼ The first hop steps on `(23,10)` — the tile we ARRIVE on. `_enter_warp_by_navigation` handles
#: that case explicitly (step off one tile, then back on to fire it); it is not an oversight.
#:
#: ‼‼ THIS LEG WAS RE-DERIVED AFTER A DRIVEN FAILURE, and the reason is the maze's defining hazard.
#: The first version walked `(42,13) -> (48,13)` — straight through `(45,13)`, which is ITSELF a
#: panel — so the bot was teleported to `(45,9)` mid-leg and the next hop failed with "Could not
#: find a path from (45/9)". `probe_aqua_hideout_graph.py`'s `can_walk` now rejects any walk whose
#: intermediate waypoints land on a warp tile, and this is the panel-safe route it returns.
#: ‼ `Waypoint.is_warp` could NOT be used for that check: `map_path.unroll_path` only sets it on
#: the FINAL waypoint, so intermediate panels read as ordinary ground. The check compares
#: COORDINATES against the ROM warp table instead.
AQUA_HIDEOUT_ROUTE_TO_MATT = (
    (MapRSE.AQUA_HIDEOUT_B1F, (23, 10), MapRSE.AQUA_HIDEOUT_B1F, (42, 17)),
    (MapRSE.AQUA_HIDEOUT_B1F, (45, 17), MapRSE.AQUA_HIDEOUT_B1F, (45, 9)),
    (MapRSE.AQUA_HIDEOUT_B1F, (48, 9), MapRSE.AQUA_HIDEOUT_B1F, (42, 5)),
    (MapRSE.AQUA_HIDEOUT_B1F, (45, 3), MapRSE.AQUA_HIDEOUT_B1F, (3, 20)),
    (MapRSE.AQUA_HIDEOUT_B1F, (32, 19), MapRSE.AQUA_HIDEOUT_B1F, (20, 4)),
    (MapRSE.AQUA_HIDEOUT_B1F, (18, 1), MapRSE.AQUA_HIDEOUT_B2F, (18, 1)),
    (MapRSE.AQUA_HIDEOUT_B2F, (31, 8), MapRSE.AQUA_HIDEOUT_B2F, (5, 8)),
    (MapRSE.AQUA_HIDEOUT_B2F, (3, 3), MapRSE.AQUA_HIDEOUT_B1F, (3, 3)),
    (MapRSE.AQUA_HIDEOUT_B1F, (12, 1), MapRSE.AQUA_HIDEOUT_B2F, (12, 1)),
    (MapRSE.AQUA_HIDEOUT_B2F, (8, 8), MapRSE.AQUA_HIDEOUT_B2F, (31, 17)),
)

# ‼‼ THE TREASURE ROOM, AND WHY THE ORDER IS NOT NEGOTIABLE (`#24-masterball`).
# Four objects sit in a 2x2 block on B1F:
#       (15,9)  MASTER BALL      (16,9)  ELECTRODE 1  (disguised as an item ball)
#       (15,10) Nugget           (16,10) ELECTRODE 2  (disguised as an item ball)
# MEASURED (`probe_aqua_hideout_graph.py`): **both of the Master Ball's free neighbours, `(14,9)`
# and `(15,8)`, are unreachable** - the only walkable approach into the block is `(15,11)`, below
# the Nugget. So the Master Ball cannot be taken directly at all.
# ‼ THE WAY IN IS THROUGH THE NUGGET: an item ball is an OBJECT that DISAPPEARS when collected, so
# taking the Nugget frees `(15,10)`, and from there the Master Ball is directly above.
# ‼ AND NO ELECTRODE NEEDS TO BE FOUGHT. Facing Up from `(15,11)` targets `(15,10)`, and facing Up
# from `(15,10)` targets `(15,9)` - never `(16,9)`/`(16,10)`. Their hide flags are re-cleared by
# `AquaHideout_B1F_OnResume`, so fleeing one would only bring it back; we simply never face them.
AQUA_NUGGET_TILE = (15, 10)
AQUA_NUGGET_APPROACH = (15, 11)
AQUA_MASTERBALL_TILE = (15, 9)
#: ‼ standable ONLY after the Nugget above has been collected - see the block comment.
AQUA_MASTERBALL_APPROACH = (15, 10)
AQUA_TREASURE_FACING = "Up"
AQUA_NUGGET_FLAG = "ITEM_AQUA_HIDEOUT_B1F_NUGGET"
AQUA_MASTERBALL_FLAG = "ITEM_AQUA_HIDEOUT_B1F_MASTER_BALL"

#: Matt, and every neighbour with the direction to face from it. ‼ The graph could reach ONLY
#: `(24,19)` - but they are ALL tried at runtime, in that order, because §Ch15 was bitten by
#: exactly this: a static probe named one reachable neighbour of Maxie and the LIVE arrival
#: measured the opposite. Ask the planner at the moment it matters and take what it gives.
AQUA_MATT_TILE = (23, 19)
AQUA_MATT_APPROACHES = (
    ((24, 19), "Left"),
    ((22, 19), "Right"),
    ((23, 18), "Down"),
    ((23, 20), "Up"),
)

_AQUA_HIDEOUT_MAPS = (
    MapRSE.AQUA_HIDEOUT_1F.value,
    MapRSE.AQUA_HIDEOUT_B1F.value,
    MapRSE.AQUA_HIDEOUT_B2F.value,
)


def _aqua_escaped() -> bool:
    """`FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE` - §Ch17's completion condition."""
    from modules.memory import get_event_flag

    return get_event_flag("TEAM_AQUA_ESCAPED_IN_SUBMARINE")


def _inside_aqua_hideout() -> bool:
    return _map_group_number() in _AQUA_HIDEOUT_MAPS


def _aqua_at(dest_map, dest_tile) -> bool:
    """Are we standing at (or beside) `dest_tile` on `dest_map`?

    ‼‼ THE TOLERANCE IS ONE TILE, AND IT IS NOT SLOPPINESS - IT IS WHAT THE GAME DOES. MEASURED
    on the first driven run: the ROM warp table says `1F (22,1)` arrives at `B1F (29,1)`, and the
    bot arrived at **`B1F (29,2)`**, one tile south. A warp table entry gives the coordinates of
    the destination WARP; for door-type warps Gen 3 then places the player on the tile in FRONT
    of it, while ladders and stair warps land exactly on it. An exact-match test therefore fails
    on every door - which is what the first run's `Could not enter the warp at (22,1)` was,
    despite the warp having worked perfectly.
    ‼ Still unambiguous for this maze: B1F's panels are three or more tiles apart, so "within one
    tile" cannot confuse two of them."""
    if _map_group_number() != dest_map.value:
        return False
    try:
        here = tuple(get_player_avatar().local_coordinates)
    except Exception as error:  # noqa: BLE001 — an unreadable avatar means "not there yet". This
        # is a success TEST, and answering "yes" on a failed read is the worst possible default
        # in a maze that navigates onward from the answer.
        _ch14_say(f"Story: Ch17 position read failed ({type(error).__name__})")
        return False
    return abs(here[0] - dest_tile[0]) <= 1 and abs(here[1] - dest_tile[1]) <= 1


def _aqua_hop(from_map, warp_tile, dest_map, dest_tile, label: str) -> Generator:
    """Take ONE warp panel and PROVE where it put us.

    ‼‼ GRADED ON THE TILE, NOT ON THE MAP - and that is the whole difference from §Ch15.
    `MAGMA_HIDEOUT_ROUTE`'s hops each crossed a floor, so "did the map change?" was a correct
    success test there. Here **most hops are `B1F -> B1F`**: a panel that dumped us in the wrong
    corner would pass a map-level test, and the next leg would then navigate from a false position
    and fail somewhere unrelated.
    ‼ It is also the detector for this maze's other hazard: `calculate_path` treats a warp panel as
    ordinary walkable ground, so a plotted walk can cross one and teleport us mid-leg. An
    unexpected position is exactly what that looks like.
    See `_aqua_at` for why the test allows one tile of slack rather than an exact match."""

    def arrived() -> bool:
        return _aqua_at(dest_map, dest_tile)

    yield from _enter_warp_by_navigation(arrived, from_map, warp_tile, label=label)
    yield from wait_until_truly_controllable()
    if not arrived():
        where = _map_group_number()
        try:
            tile = tuple(get_player_avatar().local_coordinates)
        except Exception as error:  # noqa: BLE001 — report the world, not a hypothesis, even
            # when part of the world will not read.
            tile = f"<unreadable: {type(error).__name__}>"
        raise BotModeError(
            f"Aqua Hideout: {label} - stepped on {warp_tile} but landed on map {where} at {tile}, "
            f"not {dest_map.name} {dest_tile}. ‼ In this maze that usually means a WARP PANEL was "
            "crossed on the way to the target: the planner treats panels as ordinary ground."
        )


def do_aqua_hideout_chapter() -> Generator:
    """Chapter 17 - the Lilycove Aqua Hideout, end to end.

    INTENT: set `FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE` by beating `TRAINER_MATT` on B2F, which
    opens the following beat (Team Aqua flees to the Seafloor Cavern).
    STORY CONDITION: Ch16 has run, so both `HIDE_AQUA_HIDEOUT_1F_GRUNT_*_BLOCKING_ENTRANCE` are
    SET and the entrance is clear. Checked, not assumed.
    GOAL/END STATE: the flag set AND the avatar controllable. Grade it BINARY - no batch.

    ‼ HEAL FIRST. The measured lesson from §Ch16 (2026-08-11): anchors in this project are
    routinely captured with wiped parties, and a chapter that walks into a dungeon on a damaged
    team whites out and then PASSES anyway, because a whiteout heals. Lilycove's centre is on the
    doorstep, so there is no excuse for entering hurt."""
    from modules.memory import _event_flags

    if _aqua_escaped():
        return  # resume-safe

    # ‼ NAME CONTROL, IN PRODUCTION. `get_event_flag` returns False for an unknown name without
    # raising, so a typo here would read as "the entrance is still blocked" for ever and the
    # chapter would refuse to start with a message naming the wrong cause.
    missing = [name for name in AQUA_ENTRANCE_FLAGS if name not in _event_flags]
    if missing:
        raise BotModeError(
            f"Aqua Hideout: unknown flag name(s) {missing}. These read False SILENTLY, so the "
            "era gate below cannot be trusted. Fix the name before running this chapter."
        )

    from modules.memory import get_event_flag

    if not _inside_aqua_hideout():
        blocked = [name for name in AQUA_ENTRANCE_FLAGS if not get_event_flag(name)]
        if blocked:
            raise BotModeError(
                f"Aqua Hideout: the entrance is still blocked - {blocked} not set. Ch16's harbor "
                "scene sets these; run §Ch16 (`do_slateport_harbor_theft`) first."
            )

        _ch14_say("Story: Ch17 - healing at Lilycove before the Aqua Hideout...")
        try:
            yield from _navigate_riding_out(MapRSE.LILYCOVE_CITY, (24, 15))
            yield from heal_in_pokemon_center(PokemonCenter.LilycoveCity)
            yield from wait_until_truly_controllable()
        except BotModeError as error:
            # ⛔⛔ KI-81 / `#24-abortswallow` — THIS HANDLER WAS UNDOING THE 2026-08-16 GUARD.
            # `heal_in_pokemon_center` deliberately RE-RAISES on the latch
            # (`higher_level_actions.py:364/388/437`); catching it here threw that away one
            # frame later, and the chapter then continued on a dead run. Latch-keyed.
            reraise_if_aborting(error)
            _ch14_say(f"Story: Lilycove heal SKIPPED - {str(error)[:120]}")

        _ch14_say("Story: Ch17 - entering the Aqua Hideout...")
        yield from _enter_warp_by_navigation(
            _inside_aqua_hideout,
            MapRSE.LILYCOVE_CITY,
            AQUA_HIDEOUT_DOOR,
            label="Aqua Hideout entrance",
        )
        yield from wait_until_truly_controllable()

    # --- the maze, leg A: in as far as the treasure room ------------------------------------
    yield from _aqua_run_route(AQUA_HIDEOUT_ROUTE_TO_TREASURE)

    # --- the MASTER BALL (`#24-masterball`) --------------------------------------------------
    # ‼ ORDER MATTERS: the Nugget first, because its tile is the only way to stand next to the
    # Master Ball. See the block comment on `AQUA_NUGGET_TILE`.
    _ch14_say("Story: Aqua Hideout - the treasure room. Nugget first, it is the stepping stone.")
    yield from collect_item_ball(
        MapRSE.AQUA_HIDEOUT_B1F, AQUA_NUGGET_TILE, AQUA_NUGGET_APPROACH,
        AQUA_TREASURE_FACING, AQUA_NUGGET_FLAG, "Nugget", label="the Aqua Hideout Nugget",
    )
    yield from collect_item_ball(
        MapRSE.AQUA_HIDEOUT_B1F, AQUA_MASTERBALL_TILE, AQUA_MASTERBALL_APPROACH,
        AQUA_TREASURE_FACING, AQUA_MASTERBALL_FLAG, "Master Ball",
        label="the MASTER BALL",
    )
    if _held_quantity("Master Ball") < 1:
        raise BotModeError(
            "Aqua Hideout: finished the treasure room without a Master Ball in the bag. "
            f"({AQUA_MASTERBALL_FLAG} decides whether the ball is still there; the BAG decides "
            "whether we got it, and they disagree only when the items pocket is full.)"
        )
    _ch14_say("Story: ‼ MASTER BALL COLLECTED.")

    # --- the maze, leg B: back out and on to Matt --------------------------------------------
    yield from _aqua_run_route(AQUA_HIDEOUT_ROUTE_TO_MATT)

    if _map_group_number() != MapRSE.AQUA_HIDEOUT_B2F.value:
        raise BotModeError(
            f"Aqua Hideout: the maze never reached B2F - stopped on map {_map_group_number()}. "
            "Re-derive the route with `probe_aqua_hideout_graph.py`."
        )

    yield from _aqua_challenge_matt()


def _aqua_run_route(route) -> Generator:
    """Walk one leg of the warp maze, hop by hop, proving each landing."""
    for from_map, warp_tile, dest_map, dest_tile in route:
        _check_abort()
        # Resume-safe, and unambiguous BECAUSE the test is (map, tile): the route revisits both
        # floors, so a map-only check could not tell hop 2 from hop 7. `_aqua_at` also carries
        # the one-tile door tolerance — see its docstring.
        if _aqua_at(dest_map, dest_tile):
            continue  # this hop is already done
        label = f"{from_map.name} {warp_tile} -> {dest_map.name} {dest_tile}"
        _ch14_say(f"Story: Aqua Hideout - {label}")
        yield from _aqua_hop(from_map, warp_tile, dest_map, dest_tile, label)


def _aqua_challenge_matt() -> Generator:
    """Stand beside Matt, face him, and ride the fight out until the submarine flag flips."""
    _ch14_say("Story: Aqua Hideout B2F - challenging Matt...")
    standing_on = None
    facing = None
    tried: list[str] = []
    for candidate, candidate_facing in AQUA_MATT_APPROACHES:
        _check_abort()
        try:
            yield from _navigate_riding_out(MapRSE.AQUA_HIDEOUT_B2F, candidate, tries=4)
        except BotModeError as error:  # noqa: BLE001 — NOT swallowed: this loop is a deliberate
            # try-every-neighbour search, so one candidate failing is an EXPECTED outcome. Every
            # reason is accumulated into `tried` and raised together if all four fail.
            reraise_if_aborting(error)  # `#24-abortrecoveryresiduals` (c) — PRE-EXISTING swallower. Latch-keyed:
            # with no whiteout pending it does nothing; with one, the unwind escapes instead of being
            # absorbed here. This handler predates `#24-loopheadabort`.
            tried.append(f"{candidate}: {str(error)[:60]}")
            continue
        yield from wait_for_player_avatar_to_be_standing_still()
        if tuple(get_player_avatar().local_coordinates) == candidate:
            standing_on, facing = candidate, candidate_facing
            break
        tried.append(f"{candidate}: arrived at {tuple(get_player_avatar().local_coordinates)}")

    if standing_on is None:
        raise BotModeError(
            f"Aqua Hideout: could not stand on ANY tile beside Matt {AQUA_MATT_TILE}. "
            f"Tried {[c for c, _ in AQUA_MATT_APPROACHES]}: {tried}"
        )

    yield from ensure_facing_direction(facing)
    yield
    frames = 0
    off_map = 0
    while not _aqua_escaped():
        _check_abort()
        # ‼ A WHITEOUT MOVES THE PLAYER TWO TOWNS AWAY AND THE FLAG CANNOT SEE IT - the KI-51
        # lesson, applied at build time instead of after a 60,000-frame ride. Debounced, because
        # the map read is transient across the battle's own screen transitions and ending a
        # HEALTHY fight over one odd frame would be worse than the bug.
        try:
            _on_b2f = _map_group_number() == MapRSE.AQUA_HIDEOUT_B2F.value
        except Exception:  # noqa: BLE001 — an unreadable map must never end the fight
            _on_b2f = True
        off_map = 0 if _on_b2f else off_map + 1
        if off_map > 300:
            try:
                _alive = sum(1 for m in get_party() if m is not None and m.current_hp > 0)
                _state = (f"map={_map_group_number()} tile={tuple(get_player_avatar().local_coordinates)} "
                          f"party_alive={_alive}/{len(get_party())}")
            except Exception as _error:  # noqa: BLE001 — say what could not be read, not nothing
                _state = f"<state unreadable: {type(_error).__name__}>"
            raise BotModeError(
                "Aqua Hideout: left B2F during the Matt fight without the submarine flag - "
                f"almost certainly a WHITEOUT. {_state} (was standing {standing_on} facing "
                f"{facing}, {frames} frames in)."
            )
        context.emulator.press_button("B" if frames % 3 else "A")
        frames += 1
        if frames > 60000:
            raise BotModeError(
                "Aqua Hideout: the Matt challenge never resolved in 60,000 frames "
                f"(standing {standing_on} facing {facing} at Matt {AQUA_MATT_TILE}, still on B2F)."
            )
        yield

    yield from wait_until_truly_controllable()
    _ch14_say("Story: MATT BEATEN - Team Aqua has fled in the submarine. Aqua Hideout complete.")
