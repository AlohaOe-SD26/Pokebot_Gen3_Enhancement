from typing import Generator

from modules.battle_move_replacing import (
    get_learn_move_state,
    LearnMoveState,
    handle_move_replacement_dialogue,
    get_move_learning_state_index,
)
from modules.battle_strategies import BattleStrategy
from modules.context import context
from modules.debug import debug
from modules.pokemon_party import get_party
from modules.tasks import get_task, task_is_active


@debug.track
def handle_evolution_scene(strategy: BattleStrategy, allow_evolution: bool | None = None) -> Generator:
    queried_stategy = False
    should_stop = True
    while context.bot_mode != "Manual":
        task = get_task("Task_EvolutionScene")
        if task is None:
            break

        task_state = task.data_value(0)
        if task_state == get_move_learning_state_index():
            # Advance into the move-learn prompt, then hand to the robust
            # text-driven handler. Break as soon as the move-learn UI is up by ANY
            # reliable signal — the AskWhetherToLearn STATE, the on-screen
            # "make room for X?" TEXT, or the move-select TASK. Waiting ONLY for
            # AskWhetherToLearn re-introduced the fragile-detection hang (ML-12):
            # when that state never resolves, this loop pressed A forever. A guard
            # bounds it so it can never spin here indefinitely either.
            from modules.battle_move_replacing import move_learn_text_showing, _get_evolution_task_name

            move_select_task = _get_evolution_task_name()
            guard = 0
            while task_is_active("Task_EvolutionScene") and guard < 900:
                st = get_learn_move_state()
                if (
                    st in (LearnMoveState.AskWhetherToLearn, LearnMoveState.SelectMoveToReplace)
                    or move_learn_text_showing()
                    or task_is_active(move_select_task)
                ):
                    break
                context.emulator.press_button("A")
                guard += 1
                yield
            yield from handle_move_replacement_dialogue(strategy)

        if not queried_stategy:
            if task_state >= 4:
                party_index = task.data_value(10)
                if allow_evolution is None:
                    should_stop = not strategy.should_allow_evolution(get_party()[party_index], party_index)
                else:
                    should_stop = not allow_evolution
                queried_stategy = True

        context.emulator.press_button("B" if should_stop else "A")
        yield
