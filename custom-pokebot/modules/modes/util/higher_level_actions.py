from enum import Enum
from typing import Generator, Union, Callable

from modules.context import context
from modules.debug import debug
from modules.map_data import PokemonCenter
from modules.memory import get_event_flag, get_game_state_symbol, unpack_uint32, read_symbol, get_game_state, GameState
from modules.menu_parsers import CursorOptionEmerald, CursorOptionFRLG, CursorOptionRS
from modules.menuing import PokemonPartyMenuNavigator, StartMenuNavigator, is_fade_active
from modules.modes.util.sleep import wait_for_n_frames
from modules.player import (
    get_player_avatar,
    get_player,
    TileTransitionState,
    RunningState,
    player_avatar_is_standing_still,
    player_avatar_is_controllable,
    AvatarFlags,
)
from modules.pokemon_party import get_party
from modules.region_map import FlyDestinationFRLG, FlyDestinationRSE, get_map_cursor, get_map_region
from modules.tasks import get_task, task_is_active
from ._util_helper import isolate_inputs
from .items import scroll_to_item_in_bag, use_item_from_bag
from .tasks_scripts import (
    wait_for_task_to_start_and_finish,
    wait_for_yes_no_question,
    wait_until_script_is_active,
    wait_for_script_to_start_and_finish,
    wait_for_no_script_to_run,
    wait_until_task_is_active,
    wait_for_fade_to_finish,
)
from .walking import (
    navigate_to,
    ensure_facing_direction,
    wait_for_player_avatar_to_be_standing_still,
    wait_for_player_avatar_to_be_controllable,
)
from .._interface import BotModeError


from ...game import get_symbol_name_before
from ...items import Item, get_item_bag, ItemPocket, Pokeblock, get_pokeblocks
from ...map import get_map_objects, get_map_data_for_current_position
from ...map_path import calculate_path, PathFindingError, Direction
from ...mart import get_mart_buyable_items, get_mart_buy_menu_scroll_position, get_mart_main_menu_scroll_position
from ...pokeblock_feeder import get_active_pokeblock_feeder_for_location


def counter_withdraw_outcome(pids) -> "tuple[bool, str]":
    """Should the heal's counter-withdraw run, and what should it SAY? Pure, and therefore GATED.

    Returns `(should_withdraw, message)`.

    ‼ WHY THIS IS A FUNCTION AND NOT AN `if` INSIDE THE GENERATOR. The same lesson as
    `counter_hunt.catch_confirmed`, extracted the same week: *logic that decides an outcome must be
    reachable by a test.* Inside the generator this branch could only be argued about — and the
    argument would have been "it is obviously correct", which it IS. The bug was never the
    decision; it was that both answers looked identical from outside.

    ⛔ THE EMPTY CASE IS NOT AN ERROR AND MUST NOT READ AS ONE. Most heals have no hunted counter.
    But in the user-observed Slugma/Winona derail the set was empty *because the registration
    upstream had already failed*, so the message names that possibility explicitly — that is the
    sentence that turns a silent day-long hunt into a one-line diagnosis.
    """
    # ‼‼ THE DECISION IS `bool(pids)` AND NOTHING ELSE — byte-for-byte the `if _pids:` this
    # replaced. It must NEVER depend on `len()` succeeding: today `_hunted_counter_pids` is a
    # `set` (`story_mode.py:1201`) so `len` is safe, but a refactor that made the decision hinge
    # on a `len()` call would turn a TypeError into "do not withdraw" — silently skipping the
    # collection, which is the EXACT user-visible symptom this whole line of work exists to stop.
    # The count below is COSMETIC: it improves the message and can never change the outcome.
    if pids:
        try:
            count = len(pids)
        except Exception:  # noqa: BLE001 — ‼ WIDER THAN `TypeError` ON PURPOSE. The decision is
            # ALREADY MADE by the `if pids:` above; everything in here is cosmetic. Narrowing this
            # to TypeError leaves a pathological `__len__` free to raise something else, escape to
            # the caller's outer `except Exception`, and SKIP THE WITHDRAW — turning a message
            # detail into the exact user-visible symptom this function exists to prevent. Nothing
            # can hide here: `pids` was truthy, so we withdraw either way, and the message says the
            # count is unknown rather than inventing one. (Raised by adversarial review.)
            count = "an unknown number of"
        return True, f"starting for {count} hunted PID(s)"
    return False, (
        "SKIPPED — `_hunted_counter_pids` is empty. Normal when no counter was hunted; but if one "
        "WAS hunted, its registration upstream failed (the Slugma/Winona shape) and the counter is "
        "still sitting in the PC."
    )


#: `withdraw_from_box`'s verdict CODE -> the sentence the run log carries (`#24-orphans` (1)).
#: ⛔ THE TWO "no attempt" CODES MUST NOT READ AS FAILURES. Most heals have nothing to collect, and
#: a full party declining to thin itself is CORRECT behaviour (`#24-pc`'s regression) — wording
#: either of them as a failure would recreate, in the report, exactly the lie KI-79 removed from
#: the console. Only `did_not_land` and the error paths are failures.
#: ‼ Kept as a pure table, deliberately: `_withdraw_verdict_sentence` is gated, so the wording of
#: every branch is reachable by a test instead of only by a live PC trip.
_WITHDRAW_VERDICT_SENTENCES = {
    "landed": "landed — the counter is in the party and usable this fight",
    "not_in_box": "no attempt — nothing matching the hunted PIDs was in the box",
    "party_full_no_deposit": "no attempt — party full and nothing safe to deposit; it stays boxed",
    "did_not_land": "FAILED — attempted, but the counter is STILL BOXED and unusable this fight",
}


def withdraw_verdict_report(verdict) -> "tuple[bool | None, str]":
    """`withdraw_from_box`'s raw return -> `(landed, the line to report)`. PURE, and therefore GATED.

    ‼ WHY THIS IS A FUNCTION AND NOT AN `if` AT THE CALL SITE — the same house rule
    `counter_withdraw_outcome` was extracted under: *logic that decides an outcome must be reachable
    by a test.* Inside the generator's caller, every branch below would need a live PC trip to reach,
    which is exactly how the original defect survived: the decision was fine, but both answers looked
    identical from outside.

    ⛔ AN UNRECOGNISED OR MISSING VERDICT IS A FAILURE, NEVER A SHRUG. Two silences this refuses to
    reproduce: a shape this function has not heard of means the verdict contract changed and the
    reporting did not — the half-of-a-pair defect behind KI-79 and (P1) — and a bare `None` is the
    ORIGINAL bug wearing a new hat. Both say FAILED, because `_piggyback_report` routes on that word
    and these lines must reach the screen.

    ⛔ IT REPORTS. IT DOES NOT REACT. Deciding what production DOES about a failed withdraw is the
    USER's ruling and is blocked on an unmeasured heap offset (`06-DECISIONS-LOG.md`); returning a
    verdict must not quietly become a retry.
    """
    if not isinstance(verdict, tuple) or len(verdict) != 3:
        return None, ("FAILED — the withdraw returned NO usable verdict "
                      f"({verdict!r}); this is an instrumentation bug in `withdraw_from_box`, "
                      "not a PC failure")
    landed, code, detail = verdict
    if code in _WITHDRAW_VERDICT_SENTENCES:
        sentence = _WITHDRAW_VERDICT_SENTENCES[code]
    elif code == "error":
        sentence = "FAILED — the withdraw errored and the counter stays boxed"
    else:
        sentence = f"FAILED — unrecognised withdraw verdict {code!r}; the reporting table is stale"
    # ‼ The trailing `verdict:` clause is the MACHINE-READABLE half: it is what the two-armed A/B
    # greps for, so the proof reads the value the caller actually BOUND rather than a paraphrase.
    # ⛔⛔ NO SQUARE BRACKETS ANYWHERE IN THIS LINE. The first draft ended `[landed=True code=landed]`
    # and the live run showed the tail MISSING from the transcript: `_piggyback_report` prints
    # through `rich`, which parses `[...]` as a STYLE TAG and swallows it. The pure unit test passed
    # the whole time — it asserted the returned STRING, while the thing that reaches the log is what
    # a proof must read. (`CLAUDE.md` §7, in miniature: instrument what the run really emits.)
    # ‼ `detail` is the ONLY free-text field — the `error` code carries `repr(error)`, and an
    # exception message containing a bracket would reopen exactly that hole. Sanitised, not trusted;
    # an adversarial review flagged it, so the fix is at the choke point every code passes through.
    safe_detail = str(detail).replace("[", "(").replace("]", ")")
    return landed, f"{sentence} — {safe_detail} :: verdict landed={landed} code={code}"


def _piggyback_report(what: str, outcome: str, console_too: bool = False) -> None:
    """Announce the outcome of a PC action piggybacked onto a heal. NEVER raises.

    ‼ WHY THIS EXISTS. Three PC actions ride along with `heal_in_pokemon_center` — the rotation
    deposit, the KI-63 slot-freeing deposit, and the hunted-counter withdraw. All three were
    wrapped in `except Exception: pass` under the contract *"a PC hiccup must not destroy a heal
    that already succeeded"*. That contract is right; the SILENCE was not. It made three different
    states indistinguishable: *it worked*, *there was nothing to do*, and *it threw*.

    ⛔ That is not a theoretical objection. The user-observed Slugma/Winona derail (2026-08-14,
    `08-MISTAKES.md`) ran straight through the withdraw block, which skipped because its input set
    was empty — correct behaviour for a bug that had already happened upstream, and completely
    invisible. A single line saying *"skipped, no PIDs registered"* would have named the failure
    on sight instead of costing a day. This is the project's own recurring shape: *a guard that
    cannot tell "no" from "I broke" is worse than no guard* (`repro_no_silent_except.py`).

    `console_too=False` sends the line to the RUN LOG only. Most heals legitimately have no
    counter to collect, so routine skips on screen would be noise — and a noisy diagnostic is one
    that gets ignored, which puts us back where we started. Failures always go to both.
    """
    message = f"Story: PC — {what}: {outcome}"
    if console_too or "FAILED" in outcome:
        try:
            from modules.console import console

            colour = "yellow" if "FAILED" in outcome else "cyan"
            console.print(f"[{colour}]{message}[/]")
        except Exception:  # noqa: BLE001 — reporting a piggyback outcome must never itself become
            # the thing that breaks the heal. The run-log write below is attempted independently.
            pass
    try:
        from modules import debug_logger

        debug_logger.event(message, category="PC")
    except Exception:  # noqa: BLE001 — same contract; `debug_logger.event` is already a no-op when
        # logging is disabled, so a failure here costs a diagnostic line and nothing else.
        pass


@isolate_inputs
@debug.track
def fly_to(destination: Union[FlyDestinationRSE, FlyDestinationFRLG]) -> Generator:
    if context.rom.is_frlg:
        has_necessary_badge = get_event_flag("BADGE03_GET")
        menu_index = CursorOptionFRLG.FLY
    else:
        # FORK (2026-07-24, KI-7): in RSE the field move Fly needs the FEATHER
        # Badge (BADGE06, Winona) — the stock BADGE03 check was FR/LG's, and it
        # let fly_to run three badges early (the game then rejects the move).
        has_necessary_badge = get_event_flag("BADGE06_GET")
        if context.rom.is_rs:
            menu_index = CursorOptionRS.FLY
        else:
            menu_index = CursorOptionEmerald.FLY

    if not has_necessary_badge:
        raise BotModeError("Player does not have the badge required for flying.")

    if not get_event_flag(destination.get_flag_name()):
        raise BotModeError(f"Player cannot fly to {destination.name} because that location is not yet available.")

    flying_pokemon = get_party().first_pokemon_with_move("Fly")
    if flying_pokemon is None:
        raise BotModeError("Player does not have any Pokémon that knows Fly in their party.")

    # Select field move FLY
    yield from StartMenuNavigator("POKEMON").step()
    yield from PokemonPartyMenuNavigator(flying_pokemon.index, "", menu_index).step()

    # Wait for region map to load.
    while (
        get_game_state_symbol() not in ("CB2_FLYMAP", "CB2_REGIONMAP", "CB2_FLYREGIONMAP") or get_map_cursor() is None
    ):
        yield

    destination_region = destination.get_map_region()
    if get_map_region() != destination_region:
        raise BotModeError(f"Player cannot fly to {destination.name} because they are in the wrong region.")

    # Select destination on the region map
    x, y = destination.value
    while get_map_cursor() != (x, y):
        context.emulator.reset_held_buttons()
        if get_map_cursor()[0] < x:
            context.emulator.hold_button("Right")
        elif get_map_cursor()[0] > x:
            context.emulator.hold_button("Left")
        elif get_map_cursor()[1] < y:
            context.emulator.hold_button("Down")
        elif get_map_cursor()[1] > y:
            context.emulator.hold_button("Up")
        yield
    context.emulator.reset_held_buttons()

    # Wait for journey to finish
    if context.rom.is_rs:
        yield from wait_for_task_to_start_and_finish("Task_MapNamePopup", "A")
    else:
        yield from wait_for_task_to_start_and_finish("Task_FlyIntoMap", "A")

    yield


class TaskFishing(Enum):
    INIT = 0
    GET_ROD_OUT = 1
    WAIT_BEFORE_DOTS = 2
    INIT_DOTS = 3
    SHOW_DOTS = 4
    CHECK_FOR_BITE = 5
    GOT_BITE = 6
    WAIT_FOR_A = 7
    CHECK_MORE_DOTS = 8
    MON_ON_HOOK = 9
    START_ENCOUNTER = 10
    NOT_EVEN_NIBBLE = 11
    GOT_AWAY = 12
    NO_MON = 13
    PUT_ROD_AWAY = 14
    END_NO_MON = 15


@debug.track
def fish(stop_condition: Callable[[], bool] | None = None, loop: bool = False) -> Generator:
    """Handles both single fishing actions or continuous fishing loop."""

    while True:
        if stop_condition is not None and stop_condition():
            return

        task_fishing = get_task("Task_Fishing")
        if task_fishing is not None:
            match task_fishing.data[0]:
                case TaskFishing.WAIT_FOR_A.value | TaskFishing.END_NO_MON.value:
                    context.emulator.press_button("A")
                case TaskFishing.NOT_EVEN_NIBBLE.value:
                    context.emulator.press_button("B")
                case TaskFishing.START_ENCOUNTER.value:
                    context.emulator.press_button("A")
        else:
            context.emulator.press_button("Select")
        yield

        if not loop:
            break


@debug.track
def spin(stop_condition: Callable[[], bool] | None = None, counter_clockwise: bool = False):
    directions = ["Up", "Left", "Down", "Right"] if counter_clockwise else ["Up", "Right", "Down", "Left"]
    while True:
        avatar = get_player_avatar()
        if (
            get_game_state() == GameState.OVERWORLD
            and avatar.tile_transition_state == TileTransitionState.NOT_MOVING
            and avatar.running_state == RunningState.NOT_MOVING
        ):
            if stop_condition is not None and stop_condition():
                return

            direction_index = (directions.index(avatar.facing_direction) + 1) % len(directions)
            context.emulator.press_button(directions[direction_index])
        yield


@debug.track
def heal_in_pokemon_center(pokemon_center_door_location: PokemonCenter) -> Generator:
    # Walk to and enter the Pokémon centre.
    # FORK (2026-07-24, ch12_run3): WARP-AWARE — a post-derail resume can call this
    # from INSIDE a building (the Petalburg Gym), where the plain navigate_to raises
    # "not on connected maps" and the recovery loops to Manual. navigate_to_anywhere
    # walks out through warps first; for the common same-region case it degrades to
    # exactly the old navigate_to.
    from .global_navigation import navigate_to_anywhere

    yield from navigate_to_anywhere(pokemon_center_door_location.value[0], pokemon_center_door_location.value[1])

    if pokemon_center_door_location is PokemonCenter.PalletTown:
        # Player's house in Pallet Town, where Mum can heal us.
        yield from talk_to_npc(1)
        yield from wait_for_script_to_start_and_finish("PalletTown_PlayersHouse_1F_EventScript_MomHeal", "B")
        yield from wait_for_player_avatar_to_be_standing_still("B")
        yield from navigate_to(get_player_avatar().map_group_and_number, (4, 8))

    else:
        # Walk up to the nurse and talk to her
        yield from navigate_to(get_player_avatar().map_group_and_number, (7, 4))
        yield
        context.emulator.press_button("A")
        yield from wait_for_yes_no_question("Yes")
        yield from wait_for_no_script_to_run("B")
        yield from wait_for_player_avatar_to_be_standing_still("B")

        # ‼ #24-pc — PIGGYBACK THE PC ROTATION HERE, between the nurse and the exit.
        # A full party forbids catching a type counter, and that blocked the counter chain
        # outright 5 times in batch5 while 72% of that batch's non-finishes were the chain
        # stopping for want of an answer. This is the ONLY correct place for it: we are
        # already inside the centre for a heal that was happening anyway, so it costs a few
        # steps rather than a journey (`21-TEAM-POLICY-DESIGN.md` §4, "piggyback, do not
        # detour"). It no-ops unless `rotation_plan` says `worth_it`, and it never raises —
        # a PC hiccup must not destroy a heal that already succeeded.
        try:
            from modules.story.pc_trip import deposit_dead_weight_if_worth_it

            yield from deposit_dead_weight_if_worth_it()
        except Exception as error:  # noqa: BLE001 - the heal must survive a PC hiccup, but it may
            # not survive it SILENTLY: `_piggyback_report` announces the failure and the heal
            # then continues exactly as before. See that function for why this matters here.
            # ⛔ KI-81 — a WHITEOUT is not a "PC hiccup": the run is over and the player has
            # respawned elsewhere, so continuing the heal drives menus that are no longer on screen.
            # Latch-keyed, so it also catches an abort already laundered into a plain BotModeError.
            from modules.story.early_game import reraise_if_aborting  # local: early_game imports THIS module

            reraise_if_aborting(error)
            _piggyback_report("the rotation deposit", f"FAILED ({error!r})")

        # ‼ KI-63 — FREE ONE PARTY SLOT SO AN HM LEARNER CAN BE CAUGHT.
        # Same piggyback contract as the two blocks around it: we are already inside the centre
        # for a heal that was happening anyway, so this costs a few steps rather than a journey.
        # ‼ OPT-IN, and deliberately NOT gated on `POKEBOT_PC_ROTATION` — that flag is pinned 0
        # because it fires on EVERY heal and strips teams to the floor. This fires only when a
        # caller has explicitly asked for room, exactly like `_hunted_counter_pids` below.
        # ‼ IT IS THE CALLER'S JOB TO RE-CHECK: `deposit_one_dead_weight` returns a truthful
        # boolean, and "nothing was safe to deposit" is a legitimate answer.
        try:
            from modules.context import context as _ctx
            from modules.story.pc_trip import deposit_one_dead_weight

            if getattr(_ctx.bot_mode_instance, "_needs_party_slot", False):
                yield from deposit_one_dead_weight()
        except Exception as error:  # noqa: BLE001 - same contract as the block above: the heal
            # survives, but the failure is announced rather than swallowed.
            # ⛔ KI-81 — a WHITEOUT is not a "PC hiccup": the run is over and the player has
            # respawned elsewhere, so continuing the heal drives menus that are no longer on screen.
            # Latch-keyed, so it also catches an abort already laundered into a plain BotModeError.
            from modules.story.early_game import reraise_if_aborting  # local: early_game imports THIS module

            reraise_if_aborting(error)
            _piggyback_report("the KI-63 slot-freeing deposit", f"FAILED ({error!r})")

        # ‼ #24-pcoverflow — COLLECT A COUNTER THAT LANDED IN THE BOX.
        # `resource_blocker` no longer refuses a catch when the party is full, so a hunted
        # counter can now be caught straight into the PC. Without this it would STAY there —
        # caught, paid for with a cross-Hoenn journey, and unusable, which is strictly worse
        # than the old refusal. The two changes only make sense shipped together.
        # Same piggyback contract as the deposit above: we are already inside for a heal.
        # ‼‼ THIS IS THE EXACT BLOCK THAT DID NOTHING IN THE USER-OBSERVED SLUGMA/WINONA DERAIL
        # (2026-08-14, `08-MISTAKES.md`). `box_counter_pid` was type-only, so the hunt registered
        # no PID, `_pids` was empty, and this block skipped — CORRECTLY, given its input, and
        # therefore INVISIBLY. The bug was upstream and this was where it became unobservable.
        # ⇒ both outcomes now SAY which one happened. "Nothing to withdraw" and "the withdraw
        # exploded" used to be the same silence, and that silence is what cost a day.
        try:
            from modules.context import context as _ctx
            from modules.story.pc_trip import withdraw_from_box

            _pids = getattr(_ctx.bot_mode_instance, "_hunted_counter_pids", None)
            _should_withdraw, _why = counter_withdraw_outcome(_pids)
            # ‼ The SKIP goes to the run log only, not the console: most heals legitimately have no
            # hunted counter, so this on screen would be noise — and a noisy diagnostic is one that
            # gets ignored, which puts us right back where we started. In the transcript it is the
            # line that names the failure instantly.
            _piggyback_report("counter withdraw", _why, console_too=_should_withdraw)
            if _should_withdraw:
                # ⛔⛔ INSTRUMENT THE ACTION, NOT ITS INPUT (`CLAUDE.md` §7). `_should_withdraw`
                # above is the INPUT — a candidate, not an attempt. THIS is the value the caller
                # actually binds, and until 2026-08-17 it was `None` on EVERY path: success,
                # "nothing in the box", and a withdraw that was tried and failed were the same
                # value here, so nothing downstream could ever act on the difference.
                _verdict = yield from withdraw_from_box(_pids)
                # ‼ NORMALISED, NOT TRUSTED — and normalised by a PURE, GATED function, so every
                # branch (including "an exit path forgot its verdict") is reachable by a test
                # instead of only by a live PC trip.
                _landed, _line = withdraw_verdict_report(_verdict)
                _piggyback_report(
                    "counter withdraw result", _line,
                    # A real collection is worth the screen; the two NO-ATTEMPT codes are the
                    # routine case and stay in the run log. Failures route themselves — the helper
                    # sends anything containing "FAILED" to the console regardless of this flag.
                    console_too=bool(_landed),
                )
        except Exception as error:  # noqa: BLE001 - the heal must survive a PC hiccup, but a
            # swallowed failure here reproduces the user's symptom with no diagnostic at all.
            # ⛔ KI-81 — a WHITEOUT is not a "PC hiccup": the run is over and the player has
            # respawned elsewhere, so continuing the heal drives menus that are no longer on screen.
            # Latch-keyed, so it also catches an abort already laundered into a plain BotModeError.
            from modules.story.early_game import reraise_if_aborting  # local: early_game imports THIS module

            reraise_if_aborting(error)
            _piggyback_report("counter withdraw", f"FAILED ({error!r}) — the counter is STILL "
                                                  f"BOXED and the run will fight without it")

        # Get out — robustly. `navigate_to` onto the exit warp (7,8) can stop ON the
        # tile without firing it, leaving the player stuck in the doorway (ML-9,
        # user-reported). Walk to the tile ABOVE the door and step DOWN so the warp
        # fires from a fresh step; fall back to the plain navigate if we don't leave.
        current_map = get_player_avatar().map_group_and_number
        yield from navigate_to(current_map, (7, 7))
        exit_frames = 0
        while get_player_avatar().map_group_and_number == current_map and exit_frames < 150:
            context.emulator.press_button("Down")
            exit_frames += 1
            yield
        if get_player_avatar().map_group_and_number == current_map:
            yield from navigate_to(current_map, (7, 8))

        # Do not return until the overworld is STABLY controllable again. Right after
        # the exit warp the avatar is briefly non-controllable (the flag flickers),
        # and if we return here the caller's very next navigate_to() throws "player
        # avatar is currently not controllable" — which, in the story's heal→go-to-
        # rival flow, derailed and re-ran the heal, producing an endless
        # heal/leave-PC/re-enter-PC loop that finally dropped to Manual (user-seen).
        # Require it controllable for a sustained stretch (bounded so we never hang).
        stable = 0
        waited = 0
        while stable < 20 and waited < 300:
            if player_avatar_is_controllable():
                stable += 1
            else:
                stable = 0
            waited += 1
            yield


@debug.track
def change_lead_party_pokemon(slot: int) -> Generator:
    if context.rom.is_emerald:
        cursor_option_switch = CursorOptionEmerald.SWITCH
        party_menu_task = "Task_HandleChooseMonInput"
        switch_pokemon_task = "Task_HandleChooseMonInput"
        slide_animation_task = "Task_SlideSelectedSlotsOnscreen"
        start_menu_task = "Task_ShowStartMenu"
    elif context.rom.is_rs:
        cursor_option_switch = CursorOptionRS.SWITCH
        party_menu_task = "HandleDefaultPartyMenu"
        switch_pokemon_task = "HandlePartyMenuSwitchPokemonInput"
        slide_animation_task = "sub_806D198"
        start_menu_task = "sub_80712B4"
    else:
        cursor_option_switch = CursorOptionFRLG.SWITCH
        party_menu_task = "Task_HandleChooseMonInput"
        switch_pokemon_task = "Task_HandleChooseMonInput"
        slide_animation_task = "Task_SlideSelectedSlotsOnscreen"
        start_menu_task = "Task_StartMenuHandleInput"

    yield from StartMenuNavigator("POKEMON").step()
    yield from wait_until_task_is_active(party_menu_task)
    yield
    yield from wait_for_fade_to_finish()
    yield from PokemonPartyMenuNavigator(0, "", cursor_option_switch).step()
    yield from wait_until_task_is_active(switch_pokemon_task)
    match slot:
        case 1:
            context.emulator.press_button("Right")
            yield from wait_for_n_frames(4)
            context.emulator.press_button("A")
            yield from wait_for_n_frames(4)
        case _ if slot != 1:
            context.emulator.press_button("Right")
            yield from wait_for_n_frames(4)
            for _ in range(slot - 1):
                context.emulator.press_button("Down")
                yield from wait_for_n_frames(4)
            context.emulator.press_button("A")
            yield from wait_for_n_frames(4)

    yield from wait_for_task_to_start_and_finish(slide_animation_task, "A")
    yield from wait_for_task_to_start_and_finish(start_menu_task, "B")
    yield from wait_for_n_frames(10)


@debug.track
def save_the_game():
    """
    Uses the in-game save function.

    This expects the game to be in the overworld with the start menu _closed_. It will
    open the start menu itself.

    It will confirm everything, including when warned that there is already a different
    save file (after restarting the game.)
    """

    yield from StartMenuNavigator("SAVE").step()

    if context.rom.is_frlg:
        save_dialogue_callback_name = "sSaveDialogCB"
        overwrite_callback = "SaveDialogCB_AskOverwriteOrReplacePreviousFileHandleInput"
        start_menu_task = "Task_StartMenuHandleInput"
    elif context.rom.is_emerald:
        save_dialogue_callback_name = "sSaveDialogCallback"
        overwrite_callback = "SaveOverwriteInputCallback"
        start_menu_task = "Task_ShowStartMenu"
    else:
        save_dialogue_callback_name = "saveDialogCallback"
        overwrite_callback = "SaveDialogCB_ProcessOverwriteYesNoMenu"
        start_menu_task = "sub_80712B4"

    while True:
        save_callback = get_symbol_name_before(unpack_uint32(read_symbol(save_dialogue_callback_name)))
        if not task_is_active(start_menu_task):
            break
        elif save_callback != overwrite_callback:
            context.emulator.press_button("A")
            yield
        else:
            context.emulator.press_button("Up")
            yield
            yield
            context.emulator.press_button("A")
            yield
            yield

    yield


def leave_safari_zone():
    yield from StartMenuNavigator("RETIRE").step()
    if context.rom.is_frlg:
        exit_script = "FuchsiaCity_SafariZone_Entrance_EventScript_ExitWarpIn"
    elif context.rom.is_emerald:
        exit_script = "Route121_SafariZoneEntrance_EventScript_ExitSafariZone"
    else:
        exit_script = "Route121_SafariZoneEntrance_EventScript_15C333"
    yield from wait_for_script_to_start_and_finish(exit_script, "A")
    yield from wait_for_player_avatar_to_be_standing_still()


@debug.track
def buy_in_shop(shopping_list: list[tuple[Item, int]]):
    """
    This can be used to walk through the Mart's buying menu and purchase one or
    more items.

    It expects the _main menu_ of the Mart to be open (the one where it asks Buy/Sell/Leave.)

    Call it like this:
    ```python
    yield from buy_in_shop([
        (get_item_by_name("Poké Ball"), 10),
        (get_item_by_name("Potion"), 20),
    ])
    ```

    :param shopping_list: A list of tuples where the first entry is the item to by, and the
                          second entry is the quantity for that item (max. 99, if you need
                          more create several entries in the list.)
    """

    if context.rom.is_rs:
        shop_menu_task = "Task_DoBuySellMenu"
        buy_menu_cb2 = "MAINCB2"
        select_quantity_task = "Shop_PrintPrice"
        buy_menu_task = "Shop_DoCursorAction"
        return_task = "Task_ReturnToMartMenu"
    else:
        shop_menu_task = "Task_ShopMenu"
        buy_menu_cb2 = "CB2_BUYMENU"
        select_quantity_task = "Task_BuyHowManyDialogueHandleInput"
        buy_menu_task = "Task_BuyMenu"
        return_task = "Task_ReturnToShopMenu"

    if not task_is_active(shop_menu_task):
        raise BotModeError(f"Cannot buy things in mart because `{shop_menu_task}` is not active.")

    buyable_items = get_mart_buyable_items()
    total_cost = 0
    for item, quantity in shopping_list:
        if item not in buyable_items:
            raise BotModeError(f"Cannot buy item {item.name} at this shop.")
        if quantity < 0 or quantity > 99:
            raise BotModeError(f"Cannot by {quantity} items: Invalid quantity.")
        total_cost += quantity * item.price

    player_money = get_player().money
    if player_money < total_cost:
        raise BotModeError(f"This shopping list would total ${total_cost:,}, but player only has ${player_money:,}")

    # Scroll to the 'Buy' option
    while get_mart_main_menu_scroll_position() > 0:
        context.emulator.press_button("Up")
        yield

    # Wait for 'Buy' menu to open
    context.emulator.press_button("A")
    while get_game_state_symbol() != buy_menu_cb2:
        yield
    for _ in range(22):
        yield

    for item, quantity in shopping_list:
        slot = buyable_items.index(item)
        while get_mart_buy_menu_scroll_position() != slot:
            if get_mart_buy_menu_scroll_position() > slot:
                context.emulator.press_button("Up")
            else:
                context.emulator.press_button("Down")
            yield

        yield from wait_until_task_is_active(select_quantity_task, "A")

        reverse_scroll = quantity > 50
        if reverse_scroll:
            context.emulator.press_button("Down")
            yield
            yield
        while (current_quantity := get_task(select_quantity_task).data_value(1)) != quantity:
            if current_quantity <= quantity - 7:
                context.emulator.press_button("Right")
            elif current_quantity >= quantity + 7:
                context.emulator.press_button("Left")
            elif current_quantity < quantity:
                context.emulator.press_button("Up")
            elif current_quantity > quantity:
                context.emulator.press_button("Down")
            yield

        yield from wait_until_task_is_active(buy_menu_task, "A")
        yield
        yield

    yield from wait_for_task_to_start_and_finish(return_task, "B")
    yield from wait_until_task_is_active(shop_menu_task)
    yield


@debug.track
def sell_in_shop(items_to_sell: list[tuple[Item, int]]):
    """
    This can be used to walk through the Mart's selling menu and sell one or more
    items from the player's item bag.

    It expects the _main menu_ of the Mart to be open (the one where it asks Buy/Sell/Leave.)

    Call it like this:
    ```python
    yield from sell_in_shop([
        (get_item_by_name("Moon Stone"), 1),
        (get_item_by_name("Nugget"), 5),
    ])
    ```

    :param items_to_sell: A list of tuples where the first entry is the item to sell,
                          and the second one the quantity. If multiple stacks of this
                          item exist in the item menu, this function will automatically
                          go through as many stacks as necessary to reach the desired
                          quantity.
    """

    if context.rom.is_rs:
        shop_menu_task = "Task_DoBuySellMenu"
        sell_menu_cb2 = "SUB_80A3118"
        select_quantity_task = "Task_BuyHowManyDialogueHandleInput"
        select_quantity_index = 1
        sell_menu_task = "sub_80A50C8"
        return_task = "Task_ReturnToMartMenu"
    else:
        shop_menu_task = "Task_ShopMenu"
        sell_menu_cb2 = "CB2_BAGMENURUN"
        if context.rom.is_emerald:
            select_quantity_task = "Task_ChooseHowManyToSell"
        else:
            select_quantity_task = "Task_SelectQuantityToSell"
        select_quantity_index = 8
        sell_menu_task = "Task_BagMenu_HandleInput"
        return_task = "Task_ReturnToShopMenu"

    if not task_is_active(shop_menu_task):
        raise BotModeError(f"Cannot sell things in mart because `{shop_menu_task}` is not active.")

    player_items = get_item_bag()
    for item, quantity in items_to_sell:
        if player_items.quantity_of(item) < quantity:
            raise BotModeError(
                f"Cannot sell {quantity}× {item.name} because player only owns {player_items.quantity_of(item)}."
            )
        if item.pocket is ItemPocket.KeyItems:
            raise BotModeError(f"Cannot sell {item.name} because it is a key item.")
        if item.pocket is ItemPocket.TmsAndHms and item.name.startswith("HM"):
            raise BotModeError(f"Cannot sell {item.name} because it is an HM.")

    # Scroll to the 'Sell' option
    while get_mart_main_menu_scroll_position() != 1:
        if get_mart_main_menu_scroll_position() > 1:
            context.emulator.press_button("Up")
        else:
            context.emulator.press_button("Down")
        yield

    # Wait for Sell menu to open
    context.emulator.press_button("A")
    while get_game_state_symbol() != sell_menu_cb2:
        yield
    for _ in range(25):
        yield

    for item, quantity in items_to_sell:
        already_sold = 0
        while already_sold < quantity:
            pocket = get_item_bag().pocket_for(item)
            slot = get_item_bag().first_slot_index_for(item)
            slot_quantity = pocket[slot].quantity

            if slot_quantity > quantity - already_sold:
                to_sell = quantity - already_sold
            else:
                to_sell = slot_quantity

            yield from scroll_to_item_in_bag(item)
            if not context.rom.is_rs and slot_quantity == 1:
                # In FR/LG and Emerald, if there is only one item in a slot, the mart menu
                # will not use the regular quantity selection but instead just ask a yes/no
                # question.
                yield from wait_until_task_is_active("Task_CallYesOrNoCallback", "A")
            else:
                yield from wait_until_task_is_active(select_quantity_task, "A")
                reverse_scroll = to_sell > slot_quantity / 2
                if reverse_scroll:
                    context.emulator.press_button("Down")
                    yield
                    yield
                while (current_quantity := get_task(select_quantity_task).data_value(select_quantity_index)) != to_sell:
                    if current_quantity <= to_sell - 7:
                        context.emulator.press_button("Right")
                    elif current_quantity >= to_sell + 7:
                        context.emulator.press_button("Left")
                    elif current_quantity < to_sell:
                        context.emulator.press_button("Up")
                    elif current_quantity > to_sell:
                        context.emulator.press_button("Down")
                    yield
            yield from wait_until_task_is_active(sell_menu_task, "A")
            yield

            already_sold += to_sell

    yield from wait_for_task_to_start_and_finish(return_task, "B")
    yield from wait_until_task_is_active(shop_menu_task)
    yield


@debug.track
def talk_to_npc(local_object_id: int):
    def get_npc_location() -> tuple[int, int] | None:
        for map_object in get_map_objects():
            if map_object.local_id == local_object_id:
                return map_object.current_coords
        for object_template in get_map_data_for_current_position().objects:
            if object_template.local_id == local_object_id:
                return object_template.local_coordinates
        return None

    while True:
        npc_location = get_npc_location()
        if npc_location is None:
            raise BotModeError(f"Could not find local object #{local_object_id}")

        player_avatar = get_player_avatar()
        if player_avatar.map_location_in_front.local_position == npc_location:
            context.emulator.press_button("A")
            yield
            return

        neighbouring_tiles = {
            "Up": (player_avatar.map_group_and_number, (npc_location[0], npc_location[1] + 1)),
            "Down": (player_avatar.map_group_and_number, (npc_location[0], npc_location[1] - 1)),
            "Left": (player_avatar.map_group_and_number, (npc_location[0] + 1, npc_location[1])),
            "Right": (player_avatar.map_group_and_number, (npc_location[0] - 1, npc_location[1])),
        }

        nearest_tile: tuple[tuple[int, int], tuple[int, int]] | None = None
        nearest_tile_distance: int | None = None
        nearest_tile_facing: str = "Up"
        for direction in neighbouring_tiles:
            tile = neighbouring_tiles[direction]
            try:
                path = calculate_path(player_avatar.map_location, tile)
            except PathFindingError:
                continue

            if nearest_tile_distance is None or nearest_tile_distance > len(path):
                nearest_tile = tile
                nearest_tile_distance = len(path)
                nearest_tile_facing = direction

        if nearest_tile is None:
            raise BotModeError(f"Could not find an empty tile around local object #{local_object_id}")

        try:
            yield from navigate_to(*nearest_tile, final_facing_direction=Direction.from_string(nearest_tile_facing))
            yield from ensure_facing_direction(nearest_tile_facing)
        except PathFindingError:
            # ⛔⛔ DELIBERATELY *NOT* ROUTED THROUGH `reraise_if_aborting` — and the split is the
            # whole point (adversarial review, 2026-08-16, caught this as a REAL defect in the first
            # cut of the KI-81 guard). `PathFindingError` is a **`RuntimeError`**
            # (`map_path.py:611`), NOT a `BotModeError`, and `reraise_if_aborting` re-raises the
            # object it was GIVEN. `StoryMode.run()`'s recovery catches only `except BotModeError`
            # (`story_mode.py:2505`) ⇒ a re-raised `PathFindingError` would ESCAPE whiteout recovery
            # entirely, so `set_story_abort(False)` would never run and the module-global latch would
            # be left stuck TRUE. Every later `heal_in_pokemon_center` — including
            # `ev_train.py:191` and `pokecenter_loop.py:102`, non-Story modes with NO handling around
            # it — would then re-raise a perfectly benign PC hiccup, in a different mode, with no
            # visible connection to the whiteout. ‼ A guard that can leak a global is worse than the
            # silence it replaced.
            pass
        except BotModeError as error:
            # ⛔ KI-81 — a whiteout arrives here as a `BotModeError` (`StoryAbort` is one), which
            # `StoryMode.run()` DOES catch, so re-raising is safe and correct. Latch-keyed, so it
            # also catches an abort already laundered into a plain `BotModeError` by an inner loop.
            from modules.story.early_game import reraise_if_aborting  # local: early_game imports THIS module

            reraise_if_aborting(error)
        yield


@debug.track
def mount_bicycle():
    avatar = get_player_avatar()
    if avatar.is_on_bike or avatar.is_in_water:
        return

    registered_item = get_player().registered_item
    if registered_item is not None and registered_item.name in ("Bicycle", "Acro Bike", "Mach Bike"):
        context.emulator.press_button("Select")
        yield
        return

    for index, slot in enumerate(get_item_bag().key_items):
        if slot.item.name in ("Bicycle", "Acro Bike", "Mach Bike"):
            yield from use_item_from_bag(slot.item, False)
            while get_game_state() is not GameState.OVERWORLD or not player_avatar_is_standing_still():
                yield
            return

    raise BotModeError("Player does not own a bicycle.")


@debug.track
def unmount_bicycle():
    avatar = get_player_avatar()
    if not avatar.is_on_bike or avatar.is_in_water:
        return

    registered_item = get_player().registered_item
    if registered_item is not None and registered_item.name in ("Bicycle", "Acro Bike", "Mach Bike"):
        context.emulator.press_button("Select")
        yield
        return

    for index, slot in enumerate(get_item_bag().key_items):
        if slot.item.name in ("Bicycle", "Acro Bike", "Mach Bike"):
            yield from use_item_from_bag(slot.item, False)
            while get_game_state() is not GameState.OVERWORLD or not player_avatar_is_standing_still():
                yield
            return

    raise BotModeError("Player does not own a bicycle.")


def dive():
    if context.rom.is_frlg:
        raise BotModeError("The diving mechanic does not exist in FR/LG.")
    elif context.rom.is_rs:
        task_name = "Task_Dive"
    else:
        task_name = "Task_UseDive"

    if AvatarFlags.Underwater in get_player_avatar().flags:
        raise BotModeError("Cannot dive because the player is already underwater.")

    if get_map_data_for_current_position().tile_type not in (
        "Deep Water",
        "Interior Deep Water",
        "Semi-Deep Water",
        "Sootopolis Deep Water",
    ):
        raise BotModeError("Cannot dive because the player is not on a deep water tile.")

    yield from wait_for_task_to_start_and_finish(task_name, "A")
    yield from wait_for_player_avatar_to_be_standing_still()


def surface_from_dive():
    if context.rom.is_frlg:
        raise BotModeError("The diving mechanic does not exist in FR/LG.")
    elif context.rom.is_rs:
        script_name = "S_UseDiveUnderwater"
        task_name = "Task_Dive"
    else:
        script_name = "EventScript_UseDiveUnderwater"
        task_name = "Task_UseDive"

    if AvatarFlags.Underwater not in get_player_avatar().flags:
        raise BotModeError("Cannot surface from dive because the player is not underwater.")

    if get_map_data_for_current_position().tile_type in ("Underwater Blocked Above", "Seaweed No Surfacing"):
        raise BotModeError("This tile does not allow surfacing from a dive.")

    yield from wait_until_script_is_active(script_name, "B")
    yield from wait_for_task_to_start_and_finish(task_name, "A")
    yield from wait_for_player_avatar_to_be_standing_still()


def put_pokeblock_in_feeder(pokeblock: Pokeblock) -> Generator:
    if context.rom.is_frlg:
        raise BotModeError("There are no Pokéblocks in FR/LG.")
    elif context.rom.is_emerald:
        game_state_symbol = "CB2_POKEBLOCKMENU"
        script_name = "SafariZone_EventScript_PokeblockPlaced"
    else:
        game_state_symbol = "SUB_810B674"
        script_name = "EventScript_1C34A0"

    tile = get_player_avatar().map_location_in_front
    if tile.tile_type != "Pokeblock Feeder":
        raise BotModeError("The player is not facing a Pokéblock Feeder.")

    block_index = None
    for index, block in enumerate(get_pokeblocks()):
        if block == pokeblock:
            block_index = index
            break
    if block_index is None:
        raise BotModeError("Could not find this Pokéblock in the Pokéblock Case.")

    active_feeder = get_active_pokeblock_feeder_for_location()
    if active_feeder is not None:
        raise BotModeError(f"This feeder still contains a Pokéblock for another {active_feeder.step_counter} steps.")

    while get_game_state_symbol() != game_state_symbol or is_fade_active():
        context.emulator.press_button("A")
        yield

    while True:
        if context.rom.is_emerald:
            list_task = get_task("ListMenuDummyTask")
            if list_task is None:
                break
            current_index = list_task.data_value(12) + list_task.data_value(13)
        else:
            menu_data = read_symbol("gUnknown_02039248")
            current_index = menu_data[0] + menu_data[1]
        if current_index == block_index:
            break
        elif current_index < block_index:
            context.emulator.press_button("Down")
            yield
            yield
        else:
            context.emulator.press_button("Up")
            yield
            yield

    while get_game_state() is not GameState.OVERWORLD:
        context.emulator.press_button("A")
        yield

    yield from wait_for_script_to_start_and_finish(script_name, "A")
    yield from wait_for_player_avatar_to_be_controllable()
