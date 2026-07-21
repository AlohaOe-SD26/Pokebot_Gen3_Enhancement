from enum import Enum, auto
from typing import Generator

from modules.battle_state import battle_is_active, get_battle_state
from modules.battle_strategies import BattleStrategy
from modules.context import context
from modules.debug import debug
from modules.game import get_symbol
from modules.memory import read_symbol, unpack_uint32
from modules.memory import unpack_uint16
from modules.menu_parsers import get_party_menu_cursor_pos
from modules.pokemon import get_move_by_index
from modules.pokemon_party import get_party, get_party_size
from modules.tasks import task_is_active, get_task, Task, is_waiting_for_input


class LearnMoveState(Enum):
    Unknown = auto()
    DialogueNotActive = auto()
    AskWhetherToLearn = auto()
    ConfirmCancellation = auto()
    SelectMoveToReplace = auto()


def move_learn_text_showing() -> bool:
    """TEXT-DRIVEN check (ML-11 / design §DA): read what the game ACTUALLY shows.
    The task/script state for a move-learn flickers, so the on-screen battle text
    ("<mon> is trying to learn <move>", "Delete a move to make room for <move>?")
    is a more reliable signal that we're mid-move-learn than the state alone."""
    try:
        from modules.game import decode_string

        text = decode_string(read_symbol("gDisplayedStringBattle"))
        return any(
            phrase in text
            for phrase in ("trying to learn", "make room for", "Delete a move", "wants to learn")
        )
    except Exception:
        return False


def get_learn_move_state() -> LearnMoveState:
    """
    Determines what step of the move_learning process we're on.
    """
    move_selection_task = _get_evolution_task_name()

    if task_is_active("Task_EvolutionScene"):
        if task_is_active(move_selection_task):
            return LearnMoveState.SelectMoveToReplace

        task_evolution_scene = get_task("Task_EvolutionScene")
        is_in_move_learning_stage = task_evolution_scene.data_value(0) == get_move_learning_state_index()

        if is_in_move_learning_stage and _is_asking_whether_to_replace_move(task_evolution_scene):
            return LearnMoveState.AskWhetherToLearn

        if is_in_move_learning_stage and _is_asking_whether_to_cancel_learning_move(task_evolution_scene):
            return LearnMoveState.ConfirmCancellation

    elif task_is_active(move_selection_task):
        return LearnMoveState.SelectMoveToReplace

    elif task_is_active("Task_HandleReplaceMoveYesNoInput") or task_is_active("sub_806F390"):
        return LearnMoveState.AskWhetherToLearn

    elif task_is_active("Task_HandleStopLearningMoveYesNoInput") or task_is_active("StopTryingToTeachMove_806F6B4"):
        return LearnMoveState.ConfirmCancellation

    elif battle_is_active():
        ask_to_learn_move_script = get_symbol("BattleScript_AskToLearnMove")[0]
        script_length = get_symbol("BattleScript_ForgotAndLearnedNewMove")[0] - ask_to_learn_move_script
        current_script_instruction = unpack_uint32(read_symbol("gBattleScriptCurrInstr", size=4))

        if (
            current_script_instruction < ask_to_learn_move_script
            or current_script_instruction > ask_to_learn_move_script + script_length
        ):
            return LearnMoveState.DialogueNotActive
        elif task_is_active(move_selection_task):
            return LearnMoveState.SelectMoveToReplace
        elif current_script_instruction == ask_to_learn_move_script + 0x11:
            return LearnMoveState.AskWhetherToLearn
        elif current_script_instruction == ask_to_learn_move_script + 0x20:
            return LearnMoveState.ConfirmCancellation
        else:
            return LearnMoveState.Unknown

    return LearnMoveState.DialogueNotActive


@debug.track
def handle_move_replacement_dialogue(strategy: BattleStrategy) -> Generator:
    move_to_forget = 4
    last_offered_move_name = None
    frames_in_dialogue = 0
    while True:
        # SAFETY (ML-11 follow-up): the move-learn UI normally resolves in a few
        # hundred frames. If it STALLS far beyond that, back out with B so the bot
        # can NEVER hard-freeze on the "Delete which move?" screen (user-reported).
        # The Pokémon keeps its current moves (skips the new one) — far better than
        # a hang; a re-attempt or the story self-check (§SC) recovers from there.
        frames_in_dialogue += 1
        if frames_in_dialogue > 5000:
            escape = 0
            while get_learn_move_state() != LearnMoveState.DialogueNotActive and escape < 600:
                context.emulator.press_button("B")
                escape += 1
                yield
            return

        evolution_task = get_task("Task_EvolutionScene")
        if evolution_task is not None and evolution_task.data_value(0) != get_move_learning_state_index():
            yield
            break

        state = get_learn_move_state()
        if state == LearnMoveState.DialogueNotActive:
            # Only EXIT when the move-learn is truly over. If a move-learn message
            # is still on screen (state detection lags the text, ML-11), keep
            # advancing it with A instead of leaving the prompt unhandled.
            if move_learn_text_showing():
                context.emulator.press_button("A")
                yield
                continue
            yield
            break

        if state == LearnMoveState.AskWhetherToLearn:
            debug.action_stack.append("LearnMoveState.AskWhetherToLearn")
            # Read the move being offered RIGHT NOW. A Pokémon can learn MORE THAN
            # ONE move at a single level-up (offered one after another) — so we
            # re-run the decision whenever the offered move changes, instead of
            # locking in the first one (user-flagged multi-move case).
            if task_is_active("Task_HandleReplaceMoveYesNoInput") or task_is_active("sub_806F390"):
                party_menu_data = get_party_menu_cursor_pos(get_party_size())
                move_to_learn = get_move_by_index(party_menu_data["data1"])
                party_index = party_menu_data["slot_id"]
            else:
                move_to_learn = get_move_by_index(unpack_uint16(read_symbol("gMoveToLearn", size=2)))
                if context.rom.is_rs:
                    if evolution_task is not None:
                        party_index = evolution_task.data_value(12)
                    else:
                        party_index = context.emulator.read_bytes(0x02016018, length=1)[0]
                else:
                    party_index = read_symbol("gBattleStruct", 16, 1)[0]
                if context.rom.is_emerald or context.rom.is_frlg:
                    party_index = get_battle_state().map_battle_party_index(party_index)
            if move_to_learn.name != last_offered_move_name:
                pokemon = get_party()[party_index]
                move_to_forget = strategy.which_move_should_be_replaced(pokemon, move_to_learn)
                if context.bot_mode == "Manual":
                    return
                last_offered_move_name = move_to_learn.name

            # Answer directly — do NOT gate on is_waiting_for_input(): battle text
            # doesn't use the field text-printer it checks, so it's always False
            # here and gating would never press → HANG (ML-11, the real bug). The
            # AskWhetherToLearn state already means the Yes/No menu is up. YES (A)
            # to learn (cursor defaults to Yes); NO (B) to decline. We don't wait on
            # a fixed next-state — the outer loop follows whatever comes, so an odd
            # transition course-corrects (and multi-move re-decides above).
            context.emulator.press_button("A" if move_to_forget in (0, 1, 2, 3) else "B")
            yield
            debug.action_stack.pop()

        elif state == LearnMoveState.ConfirmCancellation:
            debug.action_stack.append("LearnMoveState.ConfirmCancellation")
            # "Stop trying to teach X?" — reached only when declining -> YES (A).
            context.emulator.press_button("A")
            yield
            debug.action_stack.pop()

        elif state == LearnMoveState.SelectMoveToReplace:
            debug.action_stack.append("LearnMoveState.SelectMoveToReplace")
            cursor = _get_move_selection_cursor()
            if cursor < move_to_forget:
                context.emulator.press_button("Down")
                yield
                yield
            elif cursor > move_to_forget:
                context.emulator.press_button("Up")
                yield
                yield
            else:
                # Cursor is on the move to forget — confirm with A. The outer loop
                # then follows whatever state comes next (no fixed-target wait).
                context.emulator.press_button("A")
                yield
            debug.action_stack.pop()

        else:
            # The "Unknown" state is the run of TEXT BOXES that precede the Yes/No
            # ("<mon> is trying to learn <move>", "But it already knows 4 moves",
            # "Delete a move to make room?"). Advance them with A ONLY when the
            # game is waiting for input. Blind spam here is the real bug (ML-11 /
            # user-reported): it answers the Yes/No the instant it appears, and a
            # stray B = NO = decline = hang. A premature A = YES = learn, which is
            # exactly what we want, so A is the safe button to advance text with.
            if is_waiting_for_input():
                context.emulator.press_button("A")
            yield


def get_move_learning_state_index() -> int:
    if context.rom.is_rs:
        return 21
    else:
        return 22


def _get_evolution_task_name() -> str:
    if context.rom.is_rs:
        return "sub_809E260"
    elif context.rom.is_emerald:
        return "Task_HandleReplaceMoveInput"
    else:
        return "Task_InputHandler_SelectOrForgetMove"


def _is_asking_whether_to_replace_move(evolution_task: Task) -> bool:
    if context.rom.is_rs:
        return (
            evolution_task.data_value(8) == 4
            and evolution_task.data_value(9) == 5
            and evolution_task.data_value(10) == 9
        )
    elif context.rom.is_emerald:
        return evolution_task.data_value(6) == 4 and evolution_task.data_value(7) == 5
    else:
        return (
            evolution_task.data_value(6) == 4
            and evolution_task.data_value(7) == 5
            and evolution_task.data_value(8) == 10
        )


def _is_asking_whether_to_cancel_learning_move(evolution_task: Task) -> bool:
    if context.rom.is_rs:
        return (
            evolution_task.data_value(8) == 4
            and evolution_task.data_value(9) == 10
            and evolution_task.data_value(10) == 0
        )
    elif context.rom.is_emerald:
        return evolution_task.data_value(6) == 4 and evolution_task.data_value(7) == 11
    else:
        return (
            evolution_task.data_value(6) == 4
            and evolution_task.data_value(7) == 11
            and evolution_task.data_value(8) == 0
        )


def _get_move_selection_cursor() -> int:
    if context.rom.is_emerald:
        pointer = unpack_uint32(read_symbol("sMonSummaryScreen")) + 0x40C6
        return context.emulator.read_bytes(pointer, 1)[0]
    elif context.rom.is_frlg:
        return read_symbol("sMoveSelectionCursorPos", size=1)[0]
    else:
        return read_symbol("gSharedMem", offset=0x18079, size=1)[0]
