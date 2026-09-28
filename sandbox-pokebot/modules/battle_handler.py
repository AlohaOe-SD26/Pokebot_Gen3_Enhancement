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
from modules.menu_parsers import get_party_menu_cursor_pos
from modules.menuing import scroll_to_party_menu_index
from modules.player import get_player
from modules.plugins import plugin_should_nickname_pokemon
from modules.pokemon import StatusCondition
from modules.pokemon_party import get_party, get_party_size, PartyPokemon
from modules.tasks import task_is_active, get_task

if TYPE_CHECKING:
    from modules.encounter import EncounterInfo


_last_handled_battle_result: HandledBattleResult | None = None

#: Consecutive `handle_fainted_pokemon` give-ups within ONE battle (KI-34). The handler's own
#: `if frames > 6000: return` bounds a single INVOCATION, but the dispatcher re-enters it
#: immediately — measured at ~35 re-entries / 210,000 frames in one battle, and 3,975 give-ups
#: across a single overnight lane. Bounding the OUTCOME needs state that survives the call.
_faint_chooser_giveups: int = 0

#: Give-ups in one battle before we stop trying and hand the run a recoverable derail.
#: Each give-up is one 6,000-frame invocation, so the limit is a frame budget in disguise:
#: worst case ≈ LIMIT × 6,000 frames inside a single battle.
#:
#: ‼ RAISED 3 → 20 (2026-07-30) AS AN INTERIM MITIGATION FOR KI-38/KI-40. READ THIS BEFORE
#: TUNING IT AGAIN.
#:
#: The limit itself is correct and must stay finite — see "why not unbounded" below. What was
#: wrong is that 3 is far too tight for a chooser that still mis-selects, and giving up
#: ABANDONS AN ACTIVE BATTLE: the after-faint party menu is left open, the mode is handed a
#: fault its recovery cannot act on (B-ride / re-orient cannot answer an in-battle menu), and
#: recovery re-enters the same step and wedges again — derail #2, #3, #5 on the identical step.
#:
#: MEASURED (A/B, 2026-07-30, `05-KNOWN-ISSUES` KI-40):
#:   21b587f1  no limit, WITH the index bug     0.4 watchdog/h   **48% of runs finished**
#:   d7d493d8  limit 3, index bug FIXED        ~20 watchdog/h    **0 of 2 finished**
#:   ffb062ce  limit 3, index bug FIXED        ~29 watchdog/h    **0 of 30 finished**
#: `GAVE UP` runs at ~22/h on both limited builds and `NO ELIGIBLE REPLACEMENT` is **0** —
#: the chooser always had a living, valid target and still failed to select it. So the bound
#: converted a slow leak (spin inside one battle, often eventually succeeding) into a hard
#: stop. The pre-fix livelock measured ~35 re-entries in one battle; 20 restores most of that
#: tolerance while still terminating.
#:
#: ‼ WHY NOT UNBOUNDED (do not "simplify" this away): KI-36 — the per-run frame budget is a
#: GENERATOR WRAPPER and cannot fire while a battle handler sits on the flat controller stack.
#: An unbounded chooser is therefore bounded only by `debug_logger`'s 60,000-frame stall net,
#: which exists only while debug logging is ON. Finite here is what makes the failure bounded
#: with logging OFF.
#:
#: ‼ THIS IS A MITIGATION, NOT A FIX. The real fix is `#24-menutext` — read the party-menu
#: TEXT so the bot knows what the cursor is actually on, instead of inferring from indices.
#: KI-38's evidence (`presses={'Down': 3, 'A': 273}`, `cursors_seen=[0,2,3,7]` in a 4-mon
#: party, where 7 is probably CANCEL) says the cursor MODEL is wrong, and no number of retries
#: fixes a wrong model. Do not let a restored finish rate be mistaken for a solved bug.
#:
#: Tunable without a code edit, because the right number is empirical and this file lives on a
#: machine that pulls: `POKEBOT_FAINT_GIVEUP_LIMIT=<n>`.
#: Hard ceiling on the tunable above. ‼ CLAMPED, not merely validated: the first version
#: accepted any positive integer, so `POKEBOT_FAINT_GIVEUP_LIMIT=99999999999999999999` — one
#: fat-fingered env var on the batch machine — produced an EFFECTIVELY UNBOUNDED chooser and
#: silently reintroduced the exact KI-36 hazard the finite limit exists to prevent. Caught by
#: `repro_faint_giveup_limit.py` before it shipped. 200 × 6,000 ≈ 1.2M frames, ~24% of the 5M
#: per-run budget: far more tolerance than any real chooser should need, still terminating.
FAINT_CHOOSER_GIVEUP_MAX = 200


def _faint_giveup_limit_default() -> int:
    import os

    try:
        value = int(os.environ.get("POKEBOT_FAINT_GIVEUP_LIMIT", "20"))
    except Exception:  # noqa: BLE001 - a bad env value must never break battles
        return 20
    if value < 1:
        return 20
    return min(value, FAINT_CHOOSER_GIVEUP_MAX)


FAINT_CHOOSER_GIVEUP_LIMIT = _faint_giveup_limit_default()


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


#: ‼ KI-47 last-resort net for battle SUB-handlers (see `_watch`). ~50 s at 1x —
#: deliberately generous, because this sits BEHIND the specific bounds (KI-45's 60
#: cursor steps, KI-46's 600 unrecognised frames) rather than replacing them. A
#: specific bound gives a specific diagnosis; this one only reports that the battle
#: stopped progressing at all.
_SUBHANDLER_STALL_FRAMES = 3000


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
    global _faint_chooser_giveups
    _faint_chooser_giveups = 0  # per-battle: see FAINT_CHOOSER_GIVEUP_LIMIT (KI-34)

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

    def _progress_sig():
        """The battle's progress fingerprint. Shared by the outer watchdog and `_watch`."""
        try:
            from modules.battle_move_replacing import get_learn_move_state

            return (
                get_current_battle_script_instruction(),
                get_main_battle_callback(),
                str(get_learn_move_state()),
                sum(getattr(p, "total_exp", 0) for p in get_party()),
            )
        except Exception:  # noqa: BLE001
            return None

    def _watch(subgen, label):
        """‼ KI-47 — the ONE net that covers every loop inside a battle sub-handler.

        The ML-11 watchdog above is correct but STARVED: it only runs between iterations of
        THIS loop, and a sub-generator that yields for ever consumes the frames on its behalf,
        so the outer counter never increments. That is why it caught neither KI-45
        (`_select_in_menu`) nor KI-46 (`handle_battle_action_selection`) — the same
        starvation shape as KI-37.

        An audit on 2026-08-04 found **32 unbounded `while` loops** on the battle path.
        Bounding all 32 individually would be 32 chances to get a bound wrong, and most of
        them legitimately wait for the game to move on. Counting frames HERE — where they are
        actually consumed — covers all of them at once, including ones not yet written.

        Bound is deliberately generous (~50 s): this is a LAST-RESORT net behind the specific
        bounds, not a replacement for them. A specific bound gives a specific diagnosis; this
        one only says "the battle stopped progressing", which is why it names the sub-handler
        and the frozen signature.
        """
        stale = 0
        last = None
        while True:
            try:
                value = next(subgen)
            except StopIteration as stop:
                return stop.value
            sig = _progress_sig()
            if sig is not None and sig == last:
                stale += 1
                if stale > _SUBHANDLER_STALL_FRAMES:
                    reason = (
                        f"KI-47: battle sub-handler '{label}' ran {stale} frames with no "
                        f"battle progress (frozen at {sig!r})"
                    )
                    from modules.battle_fault import request_mode_recovery
                    from modules.modes import BotModeError

                    if request_mode_recovery(reason):
                        # KI-107 (2026-09-27): SAY it. This park left no line at all in run P1r2, so a 6.27M-frame idle
                        # had to be reconstructed from timing. `event` is a no-op when debug logging is off.
                        from modules import debug_logger as _dl_park

                        _dl_park.event(f"KI-47 PARK: {reason} — handed to the mode as a recoverable fault")
                        return None
                    raise BotModeError(reason)
            else:
                stale = 0
                last = sig
            yield value

    while (battle_is_active() or _learn_or_evo_pending()) and context.bot_mode != "Manual":
        # A sub-handler has given up and handed a recoverable fault to the mode
        # (#24-movelearn-recovery). Stop driving immediately: re-invoking the handler
        # that just failed is precisely the loop the fault was raised to escape.
        from modules.battle_fault import battle_fault_pending

        if battle_fault_pending():
            break
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
            yield from _watch(handle_move_replacement_dialogue(strategy), "handle_move_replacement_dialogue")
        elif _evolution_animating():
            # Evolution scene in progress (not at its move-learn substate) — let
            # the evolution handler advance it; never the move-dialogue (ML-11).
            yield from _watch(handle_evolution_scene(strategy), "handle_evolution_scene")
        elif get_main_battle_callback() in ("HandleTurnActionSelectionState", "sub_8012324"):
            yield from _watch(handle_battle_action_selection(strategy), "handle_battle_action_selection")
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
            yield from _watch(handle_evolution_scene(strategy), "handle_evolution_scene")
        elif (
            (
                # FORK (2026-07-22, Ch9 hang): the script pointer can already have ADVANCED
                # past HandleFaintedMon to FaintedMonTryChoose by the time this loop regains
                # control (the faint surfaced while a sub-handler held the generator). The
                # stock condition then matches NOTHING and the default branch B-spams a
                # forced choose-mon menu — which cannot be cancelled — forever. Same flow,
                # same handler; just recognize the later script step too.
                instruction in ("BattleScript_HandleFaintedMon", "BattleScript_FaintedMonTryChoose")
                or task_is_active("Task_HandleChooseMonInput")
            )
            and get_battle_state().own_side.is_fainted
            and len(get_party().non_fainted_pokemon) > 0
        ):
            yield from _watch(handle_fainted_pokemon(strategy), "handle_fainted_pokemon")
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
    # `#27-ki47range` STEP 0 — OBSERVE ONLY (rule 10: measure an index conversion's direction before changing it).
    # The raw `gBattlePartyCurrentOrder` bytes this SNAPSHOT holds. The decomp says the game copies the PLAYER's
    # order back only when the choose-a-mon menu opens, so here it can still hold the ENEMY's order.
    try:
        from modules import debug_logger as _dl_ki47

        _dl_ki47.event(f"[KI47-OBS] snapshot order={bytes(battle_state._battler_party_order).hex()} "
                       f"party={get_party_size()}", category="BATTLE")
    except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
        pass
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

    # FORK (2026-07-22, story-bot hardening): the strategy's chooser can return None when
    # it finds no "capable" battler on a weak bench — the stock code then CRASHED on the
    # `< 0` comparison (TypeError), dropping to Manual MID-BATTLE (a permanent wedge; the
    # KI-12 repro hit it with a L3 lead + L4 bench at Roxanne). ANY living non-egg mon
    # beats crashing: the game will accept it, and the battle plays out to win-or-lose,
    # which the whiteout recovery handles.
    if new_lead_index is None:
        for _i, _mon in enumerate(get_party()):
            if _mon is not None and not _mon.is_egg and _mon.current_hp > 0:
                new_lead_index = _i
                break
    if new_lead_index is None:
        # Nothing alive at all — the battle is ending in a loss on its own; just ride it.
        while battle_is_active() and get_game_state() != GameState.PARTY_MENU:
            context.emulator.press_button("B")
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

    # FORK (2026-07-22, batch run02): the battle→party mapping itself can return an
    # OUT-OF-RANGE slot (returned 4 in a 4-mon party) — the guards above only checked
    # the raw index, so the scroll raised RuntimeError and killed the mode mid-battle
    # (an uncatchable wedge: forced party menu + no controller). Validate the MAPPED
    # index too; any living non-egg mon beats crashing, and the state-aware sweep
    # below self-corrects the cursor from there.
    _party_now = get_party()
    if (
        not (0 <= new_lead_index < len(_party_now))
        or _party_now[new_lead_index] is None
        or _party_now[new_lead_index].is_egg
        or _party_now[new_lead_index].current_hp <= 0
    ):
        for _i, _mon in enumerate(_party_now):
            if _mon is not None and not _mon.is_egg and _mon.current_hp > 0:
                new_lead_index = _i
                break

    yield from scroll_to_party_menu_index(new_lead_index)
    # FORK (2026-07-22, story-bot hardening; REWRITTEN same day after the Ch9 wedge): the
    # stock loop pressed A UNBOUNDED, and the first bounded replacement still spammed A
    # blindly — with the cursor parked on a fainted mon (and slot 1 ALSO fainted, so a
    # single Down wasn't enough) the A-spam just cycled popup -> "no energy left" ->
    # list -> popup on the same slot forever, because the rare corrective Down landed
    # during message/popup states where it is swallowed. Deterministically reproduced
    # (Ch9 Route 110 wild battle, Marshtomp+Dustox both down) and the recipe below was
    # proven on the live wedge state: read WHERE the menu actually is each step and
    # press the one button that advances it, with release gaps so every press registers.
    party_in_menu = get_party()
    # ‼ EXCLUDE MONS ALREADY ON THE FIELD (2026-07-25, user's DOUBLE-battle report, KI-18).
    # This gate used to be raw `current_hp > 0` only. In a DOUBLE battle the partner is
    # alive AND on the field, so it passed the filter — and the party menu REFUSES to
    # select an already-active mon. With the cursor parked on that slot the sweep below
    # pressed A on it forever: fault-injected repro measured 1500 A-presses over the
    # 6000-frame cap with ZERO escape, versus 8 frames to resolve when the cursor lands on
    # a real bench mon. Single battles cannot hit it (no `right_battler` slot exists), which
    # is why this only ever showed up in doubles. `choose_new_lead_after_faint` already
    # performs this exclusion (level_up.py) — the driver simply never mirrored it.
    _on_field = set()
    try:
        # ‼ Do NOT re-import get_battle_state here. It is already imported at module
        # scope, and a function-local `from ... import` makes the name local for the
        # WHOLE function — which left the EARLIER call at the top of handle_fainted_pokemon
        # referencing an unbound local (`UnboundLocalError`, caught immediately by this
        # repro's control arm). Just call the module-level one.
        _bs = get_battle_state()
        for _side in (_bs.own_side.left_battler, _bs.own_side.right_battler):
            if _side is not None and getattr(_side, "party_index", None) is not None:
                # ‼ TRANSLATE INTO THE SAME INDEX SPACE AS `party_in_menu` (KI-66, 2026-08-17).
                # THE THIRD index-space bug in this one function, after KI-18 and KI-34, and the
                # same shape both times: `party_index` comes from `gBattlerPartyIndexes`, which is
                # in FIELD order, while `party_in_menu = get_party()` is read AFTER the menu opened
                # and `UpdatePartyToBattleOrder` has permuted it into BATTLE-SLOT order. Comparing
                # them raw excluded the WRONG slot.
                # MEASURED in the Steven multi battle (`--driver ki66faint`), both faints:
                #   faint 1  raw=[0,3] -> mapped=[0,1]   truth = Sceptile(0) fainted + Metang(1)
                #   faint 2  raw=[1,3] -> mapped=[0,1]   truth = Mightyena(0) fainted + Metang(1)
                # i.e. RAW excluded Swellow, which was on the BENCH (proven by its send-out at
                # f21009) and was the only legal replacement — so the sweep's candidate set held
                # only slots the ROM refuses, costing 1263 frames against 59 on a clean faint.
                # ‼ `alive_slots` three blocks below ALREADY maps for exactly this reason
                # (`_to_menu_order`); this filter simply never mirrored it.
                try:
                    _on_field.add(_bs.map_battle_party_index(_side.party_index))
                except Exception:  # noqa: BLE001 - mapping absent: the raw index is the best hint
                    _on_field.add(_side.party_index)
    except Exception:
        _on_field = set()  # can't read it — fall back to the old, looser filter
    alive_slots = [
        i for i, mon in enumerate(party_in_menu)
        if mon is not None and not mon.is_egg and mon.current_hp > 0 and i not in _on_field
    ]
    # ‼ RECORD THE FILTER'S OWN DECISION (KI-34, 2026-07-29). The STUCK dumps for the P2
    # livelock in bundle `20260729-172342` captured tasks and party but NOT `alive_slots` or
    # `_on_field` — and those are the ONLY things that distinguish the two candidate causes:
    #   (a) `alive_slots` is EMPTY, because the KI-18 on-field exclusion removed the only
    #       living mons (a DOUBLE battle whose two actives are the survivors), so A is never
    #       pressed and the cursor walks for ever; versus
    #   (b) the printer-task branch starving the cursor-walk branch.
    # They need OPPOSITE fixes, so guessing was refused. One log line settles it.
    # An EMPTY `alive_slots` is called out explicitly: it means this handler has been asked to
    # choose a replacement it believes does not exist, which cannot succeed however long it
    # spins.
    try:
        from modules import debug_logger

        debug_logger.event(
            f"[FAINT-CHOOSER] alive_slots={alive_slots} on_field={sorted(_on_field)} "
            f"party={[(i, getattr(m.species, 'name', '?'), m.current_hp) for i, m in enumerate(party_in_menu) if m is not None]}"
            + ("  ‼ NO ELIGIBLE REPLACEMENT — cannot succeed" if not alive_slots else ""),
            category="BATTLE",
        )
    except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
        pass
    # ‼ TRANSLATE INTO THE CURSOR'S INDEX SPACE BEFORE COMPARING (KI-34, 2026-07-30).
    #
    # `alive_slots` above is in REGULAR party order (`get_party()`). The cursor read below
    # comes from `gPartyMenu.slotId`, which is the IN-BATTLE party-menu order — and the two
    # DIVERGE once mons have been switched in and out, which is exactly what a double battle
    # after a faint looks like. `BattleState.map_battle_party_index()` exists solely to convert
    # between them; its docstring says so outright.
    #
    # Comparing them raw made `cursor in alive_slots` TRUE for a mon that was ON THE FIELD, so
    # the sweep pressed A on a selection the game REFUSES, which re-armed
    # `Task_PrintAndWaitForText` and restarted the loop. Measured in bundle `20260730-062818`:
    # `presses={'A': 289}` with a STATIC cursor, 3,975 give-ups in P3 alone, ~23.9M frames
    # (~7.8 complete runs) burned in one night. The user diagnosed it by WATCHING THE SCREEN;
    # the instrumentation could not, because it logged the values without their units.
    #
    # ‼ This function's PRIMARY path already maps (see `index_needs_mapping` above). Only this
    # recovery sweep never mirrored it — the same shape as the KI-18 note one layer up.
    def _to_menu_order(regular_index: int) -> int:
        try:
            return battle_state.map_battle_party_index(regular_index)
        except Exception:  # noqa: BLE001 - no battle state / index absent: assume identity
            return regular_index

    global _faint_chooser_giveups
    alive_slots_menu = {_to_menu_order(i) for i in alive_slots}
    # `#27-ki47range` STEP 0 — OBSERVE ONLY: the order the menu actually uses (read FRESH, now that it is open), and
    # the candidate set each reading of it would produce. The chooser ACTS on `alive_slots_menu` (the stale snapshot).
    try:
        from modules import debug_logger as _dl_ki47

        _fresh = get_battle_state()
        _fresh_map = set()
        for _i in alive_slots:
            try:
                _fresh_map.add(_fresh.map_battle_party_index(_i))
            except Exception:  # noqa: BLE001 - a missing index is itself the observation
                _fresh_map.add(-1)
        _dl_ki47.event(f"[KI47-OBS] menu-open fresh order={bytes(_fresh._battler_party_order).hex()} "
                       f"party_in_menu={len(party_in_menu)} alive_slots={sorted(alive_slots)} "
                       f"acted_on={sorted(alive_slots_menu)} fresh_mapped={sorted(_fresh_map)} "
                       f"out_of_range={sorted(i for i in alive_slots_menu if i >= len(party_in_menu))}",
                       category="BATTLE")
    except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
        pass
    try:
        from modules import debug_logger

        debug_logger.event(
            f"[FAINT-CHOOSER] index spaces: alive_slots={alive_slots}(party-order) -> "
            f"{sorted(alive_slots_menu)}(menu-order) on_field={sorted(_on_field)}(party-order)"
            + ("  [orders DIVERGE]" if alive_slots_menu != set(alive_slots) else "  [orders agree]"),
            category="BATTLE",
        )
    except Exception:  # noqa: BLE001
        pass

    import collections as _collections

    _presses: "_collections.Counter" = _collections.Counter()
    _cursors: set = set()
    frames = 0
    # ‼ LEARN WHAT THE GAME REFUSES, INSTEAD OF TRUSTING THE INDEX MODEL (KI-38, 2026-07-30).
    #
    # THE BUG THIS FIXES. Below, `A` is pressed whenever `cursor in alive_slots_menu` and
    # `Down` ONLY when it is not. So if the game REFUSES that selection, the cursor never
    # moves, the refusal re-arms `Task_PrintAndWaitForText`, we dismiss it, land on the same
    # cursor, and press A again — for ever. That is exactly KI-38's signature
    # (`presses={'Down': 3, 'A': 273}` with a near-static cursor) and it hung 11 of 12 runs in
    # batch A on this box, always at `BattleScript_FaintedMonTryChoose` with healthy mons
    # available.
    #
    # WHY NOT "FIX THE INDEX MAPPING". Because the mapping is the thing in doubt, and it has
    # now been wrong twice in two different ways (KI-18's on-field filter, KI-34's index
    # space). A third correction would be another guess. Refusal is OBSERVABLE: press A, and
    # if we are still in the party menu with the printer re-armed, that slot is not selectable
    # — whatever the model believes. So the model becomes a HINT and the game gets the vote.
    #
    # WHY THIS TERMINATES (the property that matters): every A-press either leaves the menu
    # (done) or eliminates one slot for good. There are at most `len(party_in_menu)` slots
    # plus CANCEL, so the loop cannot revisit a dead slot and cannot spin.
    _refused: set = set()
    _last_a_cursor = None
    while get_game_state() == GameState.PARTY_MENU:
        try:
            cursor = get_party_menu_cursor_pos(len(party_in_menu))["slot_id"]
        except Exception:
            cursor = None
        # A refusal shows up as: we pressed A on a slot, and we are STILL in the party menu
        # with the text printer armed again. Detected structurally rather than by matching the
        # refusal string, so it needs no decomp lookup and cannot break on a text change.
        if _last_a_cursor is not None and (
            task_is_active("Task_PrintAndWaitForText") or task_is_active("Task_ReturnToChooseMonAfterText")
        ):
            _refused.add(_last_a_cursor)
            _last_a_cursor = None
        # Candidates: what the model believes, minus what the game has actually refused. If
        # that empties, the MODEL is wrong rather than the party being unusable — fall back to
        # every slot we have not yet had refused, which is what makes this robust to an index
        # model that is simply incorrect.
        _candidates = alive_slots_menu - _refused
        if not _candidates:
            _candidates = {i for i in range(len(party_in_menu))} - _refused
        # KI-17 (2026-07-24, decomp-confirmed race): selecting a living mon while the
        # "X has no energy left!" printer tasks are still winding down can exit the
        # party menu WITHOUT destroying the printer — its orphaned DMA request then
        # deadlocks ReshowBattleScreenAfterMenu's IsDma3ManagerBusyWithBgCopy() wait
        # forever (the CB2_SETUPRESHOWBATTLESCREENAFTERMENU freeze, 2/5 lanes).
        # Rules from the analysis: after dismissing the error text, IDLE long enough
        # for the task tree to revert to Task_HandleChooseMonInput before ANY further
        # input; and never blind-press A when the cursor can't be read.
        post_gap = 6
        if task_is_active("Task_PrintAndWaitForText") or task_is_active("Task_ReturnToChooseMonAfterText"):
            button = "A"   # dismiss "X has no energy left to battle!"
            post_gap = 24  # ... then give the task tree time to revert (KI-17)
        elif task_is_active("Task_HandleSelectionMenuInput"):
            # Shift/Summary/Cancel popup: SHIFT is first, so A on a living mon sends
            # it out; on a fainted mon the popup is useless — close it.
            # ‼ `cursor` is MENU-order, so it must be tested against the MENU-order set.
            button = "A" if cursor in _candidates else "B"
        elif cursor is not None and cursor not in _candidates:
            button = "Down"  # walk to a slot that is still worth trying
        elif cursor is not None:
            # Cursor is on a candidate the game has not yet refused — confirm, and REMEMBER
            # that we did, so the next iteration can tell acceptance from refusal.
            button = "A"
            _last_a_cursor = cursor
            # `#27-ki47range` STEP 0 — OBSERVE ONLY (rule 7: log the value the code ACTS on): the menu slot we
            # confirm and the PID it holds in the menu's own order.
            try:
                from modules import debug_logger as _dl_ki47

                _tgt = party_in_menu[cursor] if 0 <= cursor < len(party_in_menu) else None
                _dl_ki47.event(f"[KI47-OBS] A at cursor={cursor} pid="
                               f"{'-' if _tgt is None else f'{_tgt.personality_value:08X}'} "
                               f"sp={getattr(getattr(_tgt, 'species', None), 'name', '-')} frames={frames}",
                               category="BATTLE")
            except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
                pass
        else:
            button = None    # cursor unreadable: wait, never gamble an A (KI-17)
        # ‼ COUNT WHAT WE PRESS AND WHERE THE CURSOR WAS (KI-34). Playbook §7: "pressing the
        # wrong thing" and "pressing nothing" look IDENTICAL from a state trace but need
        # opposite fixes — only the button ratio separates them. Counted here, emitted once
        # when the loop gives up, so it costs nothing per frame and cannot flood the log.
        _presses[button if button is not None else "(none)"] += 1
        if cursor is not None:
            _cursors.add(cursor)
        if button is not None:
            for _ in range(2):
                context.emulator.press_button(button)
                yield
        else:
            for _ in range(2):
                yield
        for _ in range(post_gap):
            yield
        frames += 2 + post_gap
        if frames > 6000:
            # ‼ THIS RETURN DOES NOT END ANYTHING. The dispatcher re-enters this handler with
            # `frames = 0`, so the 6,000-frame bound is per-invocation, not per-wedge: the P2
            # livelock (KI-34) survived ~35 re-entries over 210,000 frames. Bounding the
            # OUTCOME rather than the frames is the real fix and is NOT attempted here — it
            # needs the cause below settled first. Until then, at least say so out loud, so a
            # log reader sees a repeating give-up instead of silence.
            try:
                from modules import debug_logger

                # ‼ CAPTURE WHAT THE SCREEN ACTUALLY SAYS (#24-menutext groundwork, 2026-07-30).
                # KI-38's data proves the chooser's CURSOR MODEL is wrong, not its patience:
                # `cursors_seen=[0,2,3,7]` in a 4-mon party (7 is almost certainly CANCEL) with
                # 273 A-presses and a living target available every time. Indices alone cannot
                # tell us what went wrong, because indices are the thing in doubt — so record
                # the TEXT, which is ground truth. This is exactly the move that cracked the
                # move-learn hang (ML-11: "read what the game ACTUALLY says").
                #
                # DECOMP-VERIFIED action-menu strings (src/strings.c, fetched 2026-07-30 —
                # never write these from memory): SEND OUT (gText_SendOut), SHIFT (gText_Shift),
                # SWITCH (gText_Switch2), SUMMARY (gText_Summary5), CANCEL (gText_Cancel),
                # ENTER (gText_Enter). "Do what with this {PKMN}?" (gText_DoWhatWithPokemon) is
                # the prompt shown when the ACTION menu is open over a chosen mon.
                #
                # DIAGNOSTIC ONLY — it must never change battle behaviour, hence the try/except
                # and no branching on the result. The next batch's logs are what make the real
                # text-driven chooser buildable.
                _screen = {}
                try:
                    from modules.game import decode_string

                    _screen["battle"] = decode_string(read_symbol("gDisplayedStringBattle")).strip()
                    _screen["field"] = decode_string(read_symbol("gStringVar4")).strip()
                except Exception:  # noqa: BLE001
                    pass

                debug_logger.event(
                    f"[FAINT-CHOOSER] GAVE UP after {frames} frames without sending a mon out "
                    f"— presses={dict(_presses)} cursors_seen={sorted(_cursors)}(menu-order) "
                    f"alive_slots={alive_slots}(party-order) -> {sorted(alive_slots_menu)}(menu-order). "
                    f"give-up {_faint_chooser_giveups + 1}/{FAINT_CHOOSER_GIVEUP_LIMIT} this battle. "
                    f"refused={sorted(_refused)}(menu-order) "
                    f"[#24-menutext] on-screen battle_text={_screen.get('battle', '?')!r} "
                    f"field_text={_screen.get('field', '?')!r}",
                    category="BATTLE",
                )
            except Exception:  # noqa: BLE001
                pass
            # ‼ BOUND THE OUTCOME, NOT THE FRAMES. Returning here only ends this INVOCATION;
            # the dispatcher re-enters immediately, which is why the 6,000-frame bound produced
            # a 210,000-frame livelock. After a few honest attempts, hand the run a RECOVERABLE
            # derail through the designed channel: `request_mode_recovery` makes `handle_battle`
            # and `BattleListener` short-circuit, the mode claims the fault on its next frame
            # (`story_mode.py` `take_pending_fault`) and derails cleanly, and the endless loop
            # starts the next run instead of burning the night.
            # ‼ NEVER `raise` here — battle code is a SIBLING of the mode on a FLAT controller
            # stack, so a BotModeError would reach `main_loop` and drop straight to Manual
            # (see modules/battle_fault.py's module docstring).
            _faint_chooser_giveups += 1
            if _faint_chooser_giveups >= FAINT_CHOOSER_GIVEUP_LIMIT:
                try:
                    from modules.battle_fault import request_mode_recovery

                    _reason = (
                        f"after-faint chooser could not send a mon out after "
                        f"{_faint_chooser_giveups} attempts (KI-34): "
                        f"alive_slots={alive_slots}(party-order) -> {sorted(alive_slots_menu)}"
                        f"(menu-order), cursor stuck at {sorted(_cursors)}, presses={dict(_presses)}"
                    )
                    if request_mode_recovery(_reason):
                        try:
                            from modules import debug_logger

                            debug_logger.event(
                                f"[FAINT-CHOOSER] handing a recoverable derail to the mode: {_reason}",
                                category="BATTLE",
                            )
                        except Exception:  # noqa: BLE001
                            pass
                except Exception:  # noqa: BLE001 - never let recovery signalling break a battle
                    pass
            return


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
