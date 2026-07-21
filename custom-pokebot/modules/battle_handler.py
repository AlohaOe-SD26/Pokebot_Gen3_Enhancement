from typing import Generator, TYPE_CHECKING

from modules.battle_action_selection import handle_battle_action_selection
from modules.battle_evolution_scene import handle_evolution_scene
from modules.battle_move_replacing import handle_move_replacement_dialogue
from modules.battle_state import (
    battle_is_active,
    get_main_battle_callback,
    get_current_battle_script_instruction,
    BattlePokemon,
    get_battle_state,
    get_encounter_type,
    get_last_battle_outcome,
    HandledBattleResult,
)
from modules.battle_strategies import BattleStrategy
from modules.context import context
from modules.debug import debug
from modules.items import Item, get_item_by_index
from modules.keyboard import handle_naming_screen
from modules.memory import get_game_state, GameState, read_symbol, unpack_uint16
from modules.menuing import scroll_to_party_menu_index
from modules.player import get_player
from modules.plugins import plugin_should_nickname_pokemon
from modules.pokemon import StatusCondition
from modules.pokemon_party import get_party, get_party_size, PartyPokemon
from modules.tasks import task_is_active, get_task

if TYPE_CHECKING:
    from modules.encounter import EncounterInfo


_last_handled_battle_result: HandledBattleResult | None = None


def _dump_battle_stall_diagnostic() -> None:
    """Snapshot the live frame when the in-battle no-progress watchdog fires.

    The move-learn / evolution hang has repeatedly survived offline harnesses
    while still freezing the real bot (the unexplained harness-vs-real gap,
    ML-11). This records EXACTLY what the game was showing at the stall — the
    on-screen battle and field text, the script instruction, the main callback,
    the move-learn state, and the active menu tasks — to both the console and a
    ``battle_stall.log`` file under the profile. When the user hits a freeze,
    that file is the precise report we've been missing (design §DA)."""
    try:
        from modules.console import console
        from modules.game import decode_string
        from modules.battle_move_replacing import get_learn_move_state

        def _safe(fn, default=""):
            try:
                return fn()
            except Exception:
                return default

        battle_text = _safe(lambda: decode_string(read_symbol("gDisplayedStringBattle")))
        field_text = _safe(lambda: decode_string(read_symbol("gStringVar4")))
        instruction = _safe(get_current_battle_script_instruction)
        callback = _safe(get_main_battle_callback)
        learn_state = _safe(lambda: str(get_learn_move_state()))
        active_tasks = _safe(
            lambda: [
                t
                for t in (
                    "Task_HandleReplaceMoveYesNoInput",
                    "Task_HandleReplaceMoveInput",
                    "Task_HandleStopLearningMoveYesNoInput",
                    "Task_EvolutionScene",
                    "Task_HandleChooseMonInput",
                )
                if task_is_active(t)
            ],
            [],
        )

        lines = [
            "==== BATTLE STALL DIAGNOSTIC (no progress ~100s) ====",
            f"  battle text : {battle_text!r}",
            f"  field text  : {field_text!r}",
            f"  instruction : {instruction}",
            f"  callback    : {callback}",
            f"  learn state : {learn_state}",
            f"  active tasks: {active_tasks}",
            "=====================================================",
        ]
        report = "\n".join(lines)
        console.print(f"[bold red]{report}[/]")
        try:
            log_path = context.profile.path / "battle_stall.log"
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(report + "\n")
        except Exception:
            pass
    except Exception:
        pass


@debug.track
def handle_battle(strategy: BattleStrategy) -> Generator[None, None, HandledBattleResult]:
    """
    This is the main battle-handling function that will attempt to finish the
    battle, calling the battle strategy's callbacks whenever a decision is
    needed.
    :param strategy: The battle strategy that should be queried each time there
                     is a decision to make.
    :return: A data class structure listing some things that have changed
             during the battle.
    """
    before_cash = get_player().money
    before_party = get_party()
    encounter_type = get_encounter_type()

    stolen_items: list[tuple[int, Item]] = []
    items_before_pickup: list[Item | None] | None = None

    def _move_learn_text_showing() -> bool:
        # TEXT-DRIVEN detection (ML-11): read what the game ACTUALLY says. The
        # internal task/script state for the move-learn is flaky (it flickers), so
        # also detect the move-learn from the on-screen battle text. This means we
        # can never miss it and fall through to a stray B-press that mis-answers
        # the "Delete a move?" Yes/No as NO. See design §DA.
        try:
            from modules.game import decode_string
            from modules.memory import read_symbol

            text = decode_string(read_symbol("gDisplayedStringBattle"))
            return any(
                phrase in text
                for phrase in ("trying to learn", "make room for", "Delete a move", "wants to learn")
            )
        except Exception:
            return False

    def _move_learn_dialogue_active() -> bool:
        try:
            from modules.battle_move_replacing import get_learn_move_state, LearnMoveState

            if get_learn_move_state() != LearnMoveState.DialogueNotActive:
                return True
        except Exception:
            pass
        return _move_learn_text_showing()

    def _learn_or_evo_pending() -> bool:
        # A level-up move-learn or an evolution can surface as the battle is
        # ENDING (common in TRAINER battles). If the loop condition were only
        # `battle_is_active()`, we'd exit and leave that prompt unhandled — the
        # bot then hangs on the "Delete which move?" screen (all starters at
        # Lv16 hit this; not evolution-specific — ML-11). Keep looping so we
        # finish the dialogue.
        return _move_learn_dialogue_active() or task_is_active("Task_EvolutionScene")

    def _evolution_animating() -> bool:
        # An evolution task that is NOT at its move-learning substate. Route these
        # to the EVOLUTION handler (which ADVANCES the scene), never the
        # move-replacement handler — the latter breaks out while an evolution task
        # lingers, so re-dispatching to it would spin forever (ML-11 follow-up:
        # the evolution+move-learn overlap at Lv16).
        task = get_task("Task_EvolutionScene")
        if task is None:
            return False
        try:
            from modules.battle_move_replacing import get_move_learning_state_index

            return task.data_value(0) != get_move_learning_state_index()
        except Exception:
            return False

    # NO-PROGRESS WATCHDOG (ML-11): guarantees the bot can never HARD-FREEZE inside
    # a battle. If nothing meaningful changes for a long time — the move-learn /
    # evolution edge cases have shown flaky, hard-to-reproduce spins — bail out so
    # control returns to the mode (whose §SC self-check then recovers). The
    # progress signature includes party EXP, so the (legitimately long) GiveExp
    # bar-fill animation never false-triggers it.
    _no_progress = 0
    _last_progress_sig = None

    while (battle_is_active() or _learn_or_evo_pending()) and context.bot_mode != "Manual":
        try:
            from modules.battle_move_replacing import get_learn_move_state

            _sig = (
                get_current_battle_script_instruction(),
                get_main_battle_callback(),
                str(get_learn_move_state()),
                sum(getattr(p, "total_exp", 0) for p in get_party()),
            )
        except Exception:
            _sig = None
        if _sig is not None and _sig == _last_progress_sig:
            _no_progress += 1
        else:
            _no_progress = 0
            _last_progress_sig = _sig
        if _no_progress > 6000:
            # ~100s at 1x: a genuine stall. Before escaping, CAPTURE exactly what
            # is on screen — the move-learn hang has repeatedly passed offline
            # harnesses yet frozen the real bot, so a diagnostic of the real
            # frame is the only way to close that gap (§DA). Logs the exact
            # battle/field text + script/callback/state to console and a file so
            # the user can report precisely where it stuck.
            try:
                from modules.battle_handler import _dump_battle_stall_diagnostic

                _dump_battle_stall_diagnostic()
            except Exception:
                pass
            # Escape any lingering menu, then bail.
            for _ in range(180):
                context.emulator.press_button("B")
                yield
            break

        instruction = get_current_battle_script_instruction()
        # PRIORITY (ML-11, the real harness-vs-real gap): a move-learn or evolution
        # must be dispatched BEFORE the action-selection check. The main battle
        # callback can still read "HandleTurnActionSelectionState" while the
        # post-battle "Delete a move to make room for X?" prompt is up; if that
        # check ran first it would swallow the frame in action-selection and the
        # move-learn prompt would NEVER be handled — the exact hang the user hit.
        if instruction == "BattleScript_AskToLearnMove" or _move_learn_dialogue_active():
            yield from handle_move_replacement_dialogue(strategy)
        elif _evolution_animating():
            # Evolution scene in progress (not at its move-learn substate) — let
            # the evolution handler advance it; never the move-dialogue (ML-11).
            yield from handle_evolution_scene(strategy)
        elif get_main_battle_callback() in ("HandleTurnActionSelectionState", "sub_8012324"):
            yield from handle_battle_action_selection(strategy)
        elif get_current_battle_script_instruction() == "BattleScript_ItemSteal":
            result = yield from handle_item_stealing()
            if result is not None:
                stolen_items.append(result)
        elif (
            get_current_battle_script_instruction() == "BattleScript_PayDayMoneyAndPickUpItems"
            and items_before_pickup is None
        ):
            items_before_pickup = [pokemon.held_item for pokemon in get_party()]
            yield
        elif task_is_active("Task_EvolutionScene"):
            yield from handle_evolution_scene(strategy)
        elif (
            (instruction == "BattleScript_HandleFaintedMon" or task_is_active("Task_HandleChooseMonInput"))
            and get_battle_state().own_side.is_fainted
            and len(get_party().non_fainted_pokemon) > 0
        ):
            yield from handle_fainted_pokemon(strategy)
        elif instruction in ("BattleScript_TryNicknameCaughtMon", "BattleScript_CaughtPokemonSkipNewDex"):
            yield from handle_nickname_caught_pokemon(context.stats.last_encounter)
        else:
            context.emulator.press_button("B")
            yield

    outcome = get_last_battle_outcome()
    party_indices_with_picked_up_items = []
    party_indices_that_took_damage_or_changed_status = []
    party_indices_that_gained_exp = []
    party_indices_that_evolved = []

    after_party = get_party()
    for index in range(len(after_party)):
        if len(before_party) <= index:
            break

        before: PartyPokemon = before_party[index]
        after: PartyPokemon = after_party[index]

        if before.current_hp > after.current_hp or (
            before.status_condition is StatusCondition.Healthy and after.status_condition is not StatusCondition.Healthy
        ):
            party_indices_that_took_damage_or_changed_status.append(index)

        if before.total_exp < after.total_exp:
            party_indices_that_gained_exp.append(index)

            if before.species.name != after.species.name:
                party_indices_that_evolved.append(index)

        if items_before_pickup is not None and index < len(items_before_pickup):
            if after.held_item is not items_before_pickup[index] and after.held_item is not None:
                party_indices_with_picked_up_items.append(index)

    party_indices_with_stolen_items = set()
    for party_index, item in stolen_items:
        after: PartyPokemon = after_party[party_index]
        if after.held_item is item:
            party_indices_with_stolen_items.add(party_index)

    result = HandledBattleResult(
        outcome,
        encounter_type,
        get_player().money - before_cash,
        list(party_indices_with_stolen_items),
        party_indices_with_picked_up_items,
        party_indices_that_took_damage_or_changed_status,
        party_indices_that_gained_exp,
        party_indices_that_evolved,
    )

    global _last_handled_battle_result
    _last_handled_battle_result = result

    return result


@debug.track
def handle_item_stealing() -> Generator[None, None, tuple[int, Item] | None]:
    item_index = unpack_uint16(read_symbol("gLastUsedItem"))
    if read_symbol("gBattlerAttacker")[0] == 0:
        stolen_by = get_battle_state().own_side.left_battler.party_index
    elif read_symbol("gBattlerAttacker")[0] == 2:
        stolen_by = get_battle_state().own_side.right_battler.party_index
    else:
        stolen_by = None

    while get_current_battle_script_instruction() == "BattleScript_ItemSteal":
        context.emulator.press_button("B")
        yield

    if stolen_by is not None:
        return stolen_by, get_item_by_index(item_index)


@debug.track
def handle_fainted_pokemon(strategy: BattleStrategy):
    fainted_pokemon: BattlePokemon | None = None
    battle_state = get_battle_state()
    if battle_state.own_side.left_battler is None or battle_state.own_side.left_battler.current_hp == 0:
        fainted_pokemon = battle_state.own_side.left_battler
    elif battle_state.is_double_battle and (
        battle_state.own_side.right_battler is None or battle_state.own_side.right_battler.current_hp == 0
    ):
        fainted_pokemon = battle_state.own_side.right_battler

    if fainted_pokemon is None:
        # I can't remember how this could ever happen, but I'll leave this check in here for now.
        context.message = "fainted_pokemon was None"
        context.debug_stepping_mode()
        # context.emulator.press_button("B")
        # for _ in range(180):
        #     yield
        return

    if not battle_state.is_trainer_battle:
        if strategy.should_flee_after_faint(battle_state):
            if context.bot_mode != "Manual":
                while (
                    battle_is_active()
                    and get_current_battle_script_instruction() != "BattleScript_FaintedMonEnd"
                    and get_game_state() != GameState.PARTY_MENU
                    and get_main_battle_callback() != "HandleEndTurn_FinishBattle"
                ):
                    context.emulator.press_button("B")
                    yield

                if battle_is_active() and get_main_battle_callback() == "HandleEndTurn_FinishBattle":
                    while get_main_battle_callback() == "HandleEndTurn_FinishBattle":
                        context.emulator.press_button("B")
                        yield
                    return

    new_lead_index = strategy.choose_new_lead_after_faint(battle_state)

    # If `choose_new_lead_after_faint()` has been called while NOT being in the party selection screen,
    # `get_party()` still contains the 'original' (overworld) party order. Thus, we have to map the new
    # index to the in-battle party index (because that's what we're going to select later) but only after
    # all the sanity checks have been done.
    # On the other hand, if this function was called IN the party menu, `get_party()` already returns the
    # in-battle order and no mapping is needed.
    #
    # In practice, this function will be called OUTSIDE the party menu if the battle strategy chose to
    # send out the next Pokémon (without trying to escape) because then the call happens during the
    # dialogue.
    # Whereas the function will be called IN the party menu if the strategy tried to escape and failed,
    # because then the game automatically opens the party menu.
    index_needs_mapping = get_game_state() != GameState.PARTY_MENU

    if context.bot_mode == "Manual":
        yield
        return

    if new_lead_index < 0 or new_lead_index >= get_party_size():
        raise RuntimeError(f"Cannot send out party index #{new_lead_index} because that does not exist.")

    new_lead = get_party()[new_lead_index]
    if new_lead.is_egg:
        raise RuntimeError(f"Cannot send out party index #{new_lead_index} because it is an egg.")
    if new_lead.current_hp <= 0:
        raise RuntimeError(f"Cannot send out {new_lead.name} (#{new_lead_index}) because it has 0 HP.")

    while (
        battle_is_active()
        and get_current_battle_script_instruction() != "BattleScript_FaintedMonEnd"
        and not task_is_active("Task_HandleChooseMonInput")
        and not task_is_active("HandleBattlePartyMenu")
    ):
        context.emulator.press_button("A")
        yield

    # This will trigger if a battle ends at the same time as the player's Pokémon faints.
    # That happens if the player uses moves like Explosion or Self Destruct, or receives
    # fatal recoil damage during the finishing blow.
    # In this case, the game obviously never asks to choose a new lead and ends the battle
    # instead.
    if get_current_battle_script_instruction() == "BattleScript_FaintedMonEnd":
        return

    if index_needs_mapping:
        new_lead_index = battle_state.map_battle_party_index(new_lead_index)

    yield from scroll_to_party_menu_index(new_lead_index)
    while get_game_state() == GameState.PARTY_MENU:
        context.emulator.press_button("A")
        yield


@debug.track
def handle_nickname_caught_pokemon(encounter: "EncounterInfo"):
    nickname_choice = plugin_should_nickname_pokemon(encounter)
    if nickname_choice:
        yield from handle_naming_screen(nickname_choice)

    # Skip the nicknaming dialogue.
    while get_current_battle_script_instruction() in (
        "BattleScript_TryNicknameCaughtMon",
        "BattleScript_CaughtPokemonSkipNewDex",
    ):
        context.emulator.press_button("B")
        yield


def get_last_handled_battle_result() -> HandledBattleResult | None:
    return _last_handled_battle_result
