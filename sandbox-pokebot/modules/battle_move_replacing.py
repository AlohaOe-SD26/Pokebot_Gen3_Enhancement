from enum import Enum, auto
from typing import Generator

from modules.battle_state import battle_is_active, get_battle_state
from modules.battle_strategies import BattleStrategy
from modules.context import context
from modules.debug import debug
from modules.game import get_symbol
from modules.memory import read_symbol, unpack_uint32
from modules.memory import unpack_uint16
from modules.memory import get_game_state, GameState
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


# On-screen phrases that identify each move-learn sub-screen. These are the
# ROBUST signal (design §DA): the Emerald battle Yes/No has NO task backing it,
# so the internal state is detected only by a fragile script-offset that can
# stay "Unknown" forever — at which point the bot froze on the prompt (ML-12,
# the real user hang). Reading the text instead never misses the prompt.
_YESNO_PHRASES = ("make room for", "Delete a move", "should a move be forgotten", "Forget a move")
_STOP_PHRASES = ("Stop trying to teach", "Stop learning", "give up on learning", "Please tell me")


def _current_battle_text() -> str:
    try:
        from modules.game import decode_string

        return decode_string(read_symbol("gDisplayedStringBattle"))
    except Exception:
        return ""


def _read_offered_move(evolution_task):
    """Read the move currently being offered + the party index of the learner.
    Works whether the offer is task-backed (RS / evolution) or script-only
    (Emerald battle, via ``gMoveToLearn``)."""
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
    return move_to_learn, party_index


@debug.track
def handle_move_replacement_dialogue(strategy: BattleStrategy) -> Generator:
    """Drive the level-up / evolution move-learn UI to completion.

    TEXT-DRIVEN (design §DA, ML-12). The whole flow is decided from what the game
    is SHOWING plus the reliable menu TASKS — never from the fragile script-offset
    state or ``is_waiting_for_input()`` (which reads the FIELD text-printer and is
    unreliable in battle). This is what makes it hang-proof: even when the internal
    state never resolves past "Unknown", the on-screen "Delete a move to make room
    for X?" text is detected and answered directly. Universal — it reads the offered
    move dynamically and matches generic phrases, so it works for ANY move / level /
    Pokémon."""
    move_to_forget = 4
    last_offered_move_name = None
    frames_in_dialogue = 0
    move_selection_task = _get_evolution_task_name()

    while True:
        # SAFETY: the UI normally resolves in a few hundred frames. If it STALLS far
        # beyond that, back out with B so the bot can NEVER hard-freeze (the Pokémon
        # keeps its current moves; the story self-check §SC recovers from there).
        frames_in_dialogue += 1
        if frames_in_dialogue > 6000:
            escape = 0
            while get_learn_move_state() != LearnMoveState.DialogueNotActive and escape < 600:
                context.emulator.press_button("B")
                escape += 1
                yield
            return

        # Evolution scene that is NOT at its move-learn substate → hand back to the
        # evolution handler (it advances the scene; we only own the move-learn part).
        evolution_task = get_task("Task_EvolutionScene")
        if evolution_task is not None and evolution_task.data_value(0) != get_move_learning_state_index():
            yield
            break

        state = get_learn_move_state()
        text = _current_battle_text()
        game_state = get_game_state()

        # (1) MOVE-SELECT menu — "Which move should be forgotten?". Detected by the
        #     RELIABLE input task or the summary screen. Checked FIRST because the
        #     "make room for X?" text lingers on-screen while this menu is up.
        if state == LearnMoveState.SelectMoveToReplace or task_is_active(move_selection_task):
            debug.action_stack.append("move-learn: SelectMoveToReplace")
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
                context.emulator.press_button("A")  # cursor on the move to forget → confirm
                yield
            debug.action_stack.pop()
            continue
        if game_state == GameState.POKEMON_SUMMARY_SCREEN:
            # Summary screen opening for the move-select, but the input task is not
            # registered yet — just wait a frame for it (don't press anything).
            yield
            continue

        # (2) "Delete a move to make room for X?" YES/NO. Detected by state OR TEXT —
        #     the text is what makes this hang-proof (the Emerald prompt has no task
        #     and the offset-state can stay Unknown, ML-12). A Pokémon can learn MORE
        #     THAN ONE move per level-up (offered one after another), so RE-DECIDE
        #     whenever the offered move changes rather than locking the first choice.
        if state == LearnMoveState.AskWhetherToLearn or any(p in text for p in _YESNO_PHRASES):
            debug.action_stack.append("move-learn: AskWhetherToLearn")
            try:
                move_to_learn, party_index = _read_offered_move(evolution_task)
                if move_to_learn is not None and move_to_learn.name != last_offered_move_name:
                    move_to_forget = strategy.which_move_should_be_replaced(get_party()[party_index], move_to_learn)
                    if context.bot_mode == "Manual":
                        return
                    last_offered_move_name = move_to_learn.name
            except Exception:
                # If the read fails for any reason, still ANSWER (default: learn) so
                # we never stall on the prompt. Learning is the safe default.
                if move_to_forget == 4:
                    move_to_forget = 0
            # YES (A) to open the move-select and learn; NO (B) to decline. The
            # cursor defaults to Yes. Pressing every frame is safe: extra A presses
            # during the open animation are ignored until branch (1) takes over.
            context.emulator.press_button("A" if move_to_forget in (0, 1, 2, 3) else "B")
            yield
            debug.action_stack.pop()
            continue

        # (3) "Stop trying to teach X?" — only reached when DECLINING → confirm YES.
        if state == LearnMoveState.ConfirmCancellation or any(p in text for p in _STOP_PHRASES):
            context.emulator.press_button("A")
            yield
            continue

        # (4) Truly finished: no move-learn state AND no move-learn text on screen.
        if state == LearnMoveState.DialogueNotActive and not move_learn_text_showing():
            yield
            break

        # (5) Any other move-learn TEXT box ("<mon> is trying to learn <move>", "can't
        #     learn more than four moves", "1, 2 and... Poof!", "forgot <move>",
        #     "learned <move>!"). Advance DIRECTLY with A — do NOT gate on
        #     is_waiting_for_input() (it reads the field printer, unreliable in battle,
        #     and gating there is what left the bot pressing nothing → HANG, ML-12).
        #     A premature A on the upcoming Yes/No = YES = learn, which is the safe
        #     default; the real decision is still made by branch (2) above.
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
