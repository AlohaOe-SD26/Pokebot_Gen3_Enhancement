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
    # "HM moves can't be forgotten!" — the game REFUSING a move-select pick.
    # Added 2026-07-25 (#24-movelearn-recovery): without this the window was
    # misread as AskWhetherToLearn (the script offset still sits at +0x11), so
    # the bot answered a Yes/No that was not on screen and could never clear the
    # refusal. Killed 2 of the 5 night5 cold-start runs.
    CantForgetHM = auto()


# The Emerald task behind ShowCantForgetHMsWindow(). R/S/FRLG expose only the
# TEXT symbol, not a task, so `task_is_active` simply returns False there and
# behaviour on those ROMs is unchanged.
HM_REFUSAL_TASK = "Task_HandleInputCantForgetHMsMoves"


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

    # CHECKED FIRST (2026-07-25, #24-movelearn-recovery). The refusal window is a
    # distinct screen, but the battle script pointer stays parked at
    # BattleScript_AskToLearnMove+0x11 while it is up — so every offset-based
    # branch below would label it AskWhetherToLearn. It has to win here or the
    # caller can never tell "answer the prompt" from "the game rejected my pick".
    if task_is_active(HM_REFUSAL_TASK):
        return LearnMoveState.CantForgetHM

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


# Consecutive invocations of `handle_move_replacement_dialogue` that gave up via the
# 6000-frame safety valve. Module-level ON PURPOSE: the counter has to outlive a single
# invocation, because the bug it guards against is the caller re-invoking us fresh.
_STALLED_EXITS = 0


def _reset_stalled_exits() -> None:
    global _STALLED_EXITS
    _STALLED_EXITS = 0


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
    # #24-movelearn-recovery (2026-07-25). Slots the GAME ITSELF has refused, plus
    # the slot we most recently confirmed with A. The game is the authority on what
    # is forgettable — our own `tm_hm` veto is a prediction, this is the verdict —
    # so when it refuses, believe it and never offer that slot again this dialogue.
    hm_blocked: set[int] = set()
    last_confirmed_slot: int | None = None
    # ‼ KI-65 (2026-08-16). `party_index` used to be assigned ONLY at line 371, inside a
    # `try`. When `_read_offered_move` raised, the name stayed UNBOUND, and the two later
    # reads of it (the HM veto below, and the CantForgetHM re-pick) each raised
    # `UnboundLocalError` into a swallowing `except` — indistinguishable from success.
    # Binding it here turns "unbound" into an explicit `None` that can be TESTED.
    party_index: int | None = None
    # Consecutive frames parked on the summary screen with no recognised sub-state.
    summary_wait = 0

    while True:
        # SAFETY: the UI normally resolves in a few hundred frames. If it STALLS far
        # beyond that, back out with B so the bot can NEVER hard-freeze (the Pokémon
        # keeps its current moves; the story self-check §SC recovers from there).
        frames_in_dialogue += 1
        if frames_in_dialogue > 6000:
            # ‼ B ALONE IS NOT ENOUGH (2026-07-24 — two of three fresh runs died here).
            # The observed stall is `ml=Unknown`, `instr=BattleScript_AskToLearnMove`,
            # `bt='<MON> is trying to learn <MOVE>.'`, `wfi=True` (the game IS waiting for
            # input) — and 600 frames of pure B did not durably close it, so the caller
            # re-invoked us and the run eventually died. Evidence for the fix: the
            # match-call A/B/C/D experiment showed a stuck input-waiting prompt clears on
            # A, on B, or on alternating, but NOT on zero input; and the HM decline path
            # resolves in ~430 frames once it is actually answered. So escalate: mostly B
            # (B declines a YES/NO and advances text without confirming anything), with a
            # periodic A to satisfy a box that only accepts A — e.g. the "Stop learning
            # <MOVE>?" confirmation, which B can never dismiss. Widened to 1800 frames
            # since a real multi-part message chain can outlast 600.
            escape = 0
            while get_learn_move_state() != LearnMoveState.DialogueNotActive and escape < 1800:
                context.emulator.press_button("A" if escape % 4 == 3 else "B")
                escape += 1
                yield
            # ‼ THE VALVE MUST SURVIVE RE-ENTRY (2026-07-24 — proven live). This
            # bound is per-INVOCATION, but `battle_handler`'s outer
            # `while battle_is_active() or _learn_or_evo_pending()` loop re-invokes
            # this generator FRESH the moment we return — resetting
            # `frames_in_dialogue` to 0. So an offer we cannot resolve loops forever
            # in ~6,600-frame cycles while every individual invocation looks
            # correctly bounded. That is exactly what the user's run did until they
            # killed it by hand. Count STALLED exits across invocations and, once
            # backing out has demonstrably failed several times, raise so the mode's
            # derail-recovery takes over instead of spinning silently.
            global _STALLED_EXITS
            _STALLED_EXITS += 1
            if _STALLED_EXITS >= 3:
                _STALLED_EXITS = 0
                _reason = (
                    "Move-learn dialogue could not be resolved after 3 full attempts "
                    "(an offer we cannot answer — e.g. only HM slots available). "
                    "Backing out to recovery rather than looping."
                )
                # ‼ PREFER THE MODE'S OWN RECOVERY (#24-movelearn-recovery, 2026-07-25).
                # Raising here escapes to `main_loop` and drops the run to Manual,
                # because the battle handler is a SIBLING of the mode generator on the
                # controller stack, not nested inside it — StoryMode's derail recovery
                # never got the chance. Hand the fault to a mode that has declared it
                # can recover; only raise when nothing can (stock modes, unchanged).
                from modules.battle_fault import request_mode_recovery

                if not request_mode_recovery(_reason):
                    from modules.modes import BotModeError

                    raise BotModeError(_reason)
            return

        # Evolution scene that is NOT at its move-learn substate → hand back to the
        # evolution handler (it advances the scene; we only own the move-learn part).
        evolution_task = get_task("Task_EvolutionScene")
        if evolution_task is not None and evolution_task.data_value(0) != get_move_learning_state_index():
            # This hand-off to the evolution handler is a SUCCESSFUL exit, not a
            # failure — so it must clear the stall counter too. Missing it here meant
            # a stalled invocation could leave the counter elevated with no path to
            # clear it until the next clean DialogueNotActive exit, so unrelated
            # stalls could accumulate across a long run and eventually raise on a
            # healthy bot. EVERY non-stalled exit resets; only the 6000-frame valve
            # increments.
            _reset_stalled_exits()
            yield
            break

        state = get_learn_move_state()
        text = _current_battle_text()
        game_state = get_game_state()

        # (0) "HM moves can't be forgotten!" — the game REFUSED the slot we confirmed
        #     (#24-movelearn-recovery, 2026-07-25; reproduced from the night5 captures
        #     `saves/movelearn_hmwedge_*.ss1`). Two things must happen, and the old code
        #     did NEITHER: dismiss the window, and LEARN from the refusal. Without the
        #     second, dismissing just returns to the move list with the same doomed pick
        #     and the loop is infinite — which is exactly what the escape valve's blind
        #     A/B produced (an 8-frame ping-pong: A re-selects the HM, B dismisses).
        if state == LearnMoveState.CantForgetHM:
            debug.action_stack.append("move-learn: CantForgetHM")
            if last_confirmed_slot is not None:
                hm_blocked.add(last_confirmed_slot)
                last_confirmed_slot = None
                # Re-pick among slots the game has NOT refused, keeping the existing
                # expendability ranking (a dead 0-power move first, else the weakest).
                # If nothing is left to give up, declining is the only legal answer.
                if party_index is None:
                    # ‼ KI-65: we never learned WHICH party slot is learning, so there is
                    # nothing to re-pick FROM. The old code read the unbound name here and
                    # let `except` turn the crash into `move_to_forget = 4`, then printed
                    # "Nothing else can be given up" — a PROVABLE LIE whenever forgettable
                    # moves existed (reproduced with three of them). Decline for the honest
                    # reason instead, and SAY so.
                    move_to_forget = 4
                    context.message = (
                        "The game refused that slot (HM), but the move offer could not be "
                        "read, so I cannot verify which moves remain — declining rather "
                        "than guessing."
                    )
                else:
                    try:
                        _mv = get_party()[party_index].moves
                        _elig = [
                            i for i in range(len(_mv)) if _mv[i] is not None and i not in hm_blocked
                        ]
                        _zero = [i for i in _elig if _mv[i].move.base_power == 0]
                        move_to_forget = (
                            _zero[0]
                            if _zero
                            else (min(_elig, key=lambda i: _mv[i].move.base_power) if _elig else 4)
                        )
                    except Exception:
                        move_to_forget = 4  # can't read the party → decline, never loop
                    context.message = (
                        "The game refused that slot (HM). "
                        + (
                            f"Replacing slot {move_to_forget} instead."
                            if move_to_forget != 4
                            else "Nothing else can be given up — declining the new move."
                        )
                    )
            # Dismiss with A, then let the window actually close before acting again.
            # Pressing every frame would re-confirm the HM the moment the move list
            # comes back (the valve's bug); a press + short settle cannot.
            context.emulator.press_button("A")
            yield
            for _ in range(8):
                if get_learn_move_state() != LearnMoveState.CantForgetHM:
                    break
                yield
            debug.action_stack.pop()
            continue

        # (1) MOVE-SELECT menu — "Which move should be forgotten?". Detected by the
        #     RELIABLE input task or the summary screen. Checked FIRST because the
        #     "make room for X?" text lingers on-screen while this menu is up.
        if state == LearnMoveState.SelectMoveToReplace or task_is_active(move_selection_task):
            debug.action_stack.append("move-learn: SelectMoveToReplace")
            # ‼ ONLY act on a cursor we can TRUST (2026-07-25). The cursor lives in
            # sMonSummaryScreen, which is still being initialised while the screen
            # animates in — a stale read of 4 while the real cursor sat on slot 1
            # is how the night5 runs confirmed ROCK SMASH (an HM) despite having
            # decided to DECLINE. The input task being active is the game's own
            # signal that the screen is live and the cursor means something.
            if not task_is_active(move_selection_task):
                yield
                continue
            summary_wait = 0
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
                # Remember what we confirmed: if the game refuses it, branch (0)
                # needs to know WHICH slot to strike off.
                last_confirmed_slot = move_to_forget if move_to_forget in (0, 1, 2, 3) else None
                context.emulator.press_button("A")  # cursor on the move to forget → confirm
                yield
            debug.action_stack.pop()
            continue
        if game_state == GameState.POKEMON_SUMMARY_SCREEN:
            # Summary screen opening for the move-select, but the input task is not
            # registered yet — just wait a frame for it (don't press anything).
            # ‼ BOUNDED (2026-07-25). This was an UNBOUNDED wait, and it is where the
            # bot actually hung: with the HM-refusal window up it pressed NOTHING for
            # 6,000 straight frames (proven — zero inputs recorded before the valve),
            # because "screen up + sub-state unrecognised" looks identical to "screen
            # still opening". A genuine open takes ~20 frames. Past that, assume an
            # unrecognised screen is up and BACK OUT rather than press nothing forever.
            summary_wait += 1
            if summary_wait > 180:
                context.emulator.press_button("B")
                yield
                yield
                yield
                continue
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
                # ‼ KI-65 (2026-08-16) — this re-arms slot 0 on EVERY failing cycle, which
                # LOOKS like an infinite ping-pong and was written up as one. It is NOT,
                # and the difference matters: the HM VETO immediately below runs in the
                # SAME iteration, and when `party_index is None` it forces
                # `move_to_forget = 4` again BEFORE any button is pressed. ⛔ So the veto's
                # `is None` guard is what prevents the loop — do NOT "simplify" it away on
                # the assumption that something here covers it. MEASURED: a latch was added
                # here and then REMOVED after an isolated A/B showed the gate passes
                # identically without it (`fault_fired=87, lie_msg=0, honest_msg=1`).
                if move_to_forget == 4:
                    move_to_forget = 0
            # ‼ HM VETO — THE LAST LINE OF DEFENCE (2026-07-24, user run 15:13).
            # In Gen 3 an HM move CANNOT be forgotten; only the Move Deleter removes
            # one. If we answer YES and then pick an HM slot, the game refuses and
            # bounces straight back to this prompt — an infinite
            # AskWhetherToLearn -> SelectMoveToReplace -> AskWhetherToLearn loop
            # (reproduced live: 3 full cycles / 20,000 frames, moveset unchanged).
            # StoryMode's own policy already filters HMs on every branch, but this
            # layer is reached by EVERY strategy — the stock DefaultBattleStrategy,
            # the catch strategies that inherit it, and the `except` fallback right
            # above which blindly picks slot 0 without consulting any policy at all.
            # So enforce the GAME'S rule here, where nothing can route around it: if
            # the chosen slot holds an HM, decline instead. Declining resolves
            # cleanly (~430 frames, proven).
            if move_to_forget in (0, 1, 2, 3):
                if party_index is None:
                    # ‼ KI-65 (2026-08-16) — A VETO THAT CANNOT EVALUATE MUST FAIL CLOSED.
                    # This read used to raise `UnboundLocalError` straight into the bare
                    # `except: pass` below, which is the LOUDEST POSSIBLE SILENCE: it is
                    # indistinguishable from "the slot is not an HM, so the veto correctly
                    # did nothing". The path that leaves `party_index` unbound is the very
                    # `except` fallback named in the comment above — the one that "blindly
                    # picks slot 0 without consulting any policy at all" — so the last line
                    # of defence was structurally unable to defend against the one case it
                    # was written for. Confirming an unverifiable slot is exactly the
                    # infinite AskWhetherToLearn -> SelectMoveToReplace loop this block
                    # exists to prevent; declining resolves cleanly (~430 frames, proven).
                    context.message = (
                        "The move offer could not be read, so I cannot verify that the "
                        "slot I would give up is not an HM — declining rather than risking "
                        "the HM refusal loop."
                    )
                    move_to_forget = 4
                else:
                    try:
                        _mv = get_party()[party_index].moves

                        def _is_hm(_i):
                            _s = _mv[_i]
                            _m = _s.move if _s is not None else None
                            return _m is not None and _m.tm_hm is not None and _m.tm_hm.name.startswith("HM")

                        if _is_hm(move_to_forget):
                            # ‼ RE-PICK, DON'T JUST DECLINE (2026-07-24, user's design). The
                            # first cut of this veto turned an HM pick into DECLINE, which is
                            # safe but stunts the team — the mon keeps a weak move forever. HM
                            # slots are simply INELIGIBLE; among what remains, apply the same
                            # expendability ranking used by `teach_hm_move` (a zero-power move
                            # first, else the weakest) so the mon still gives up its least
                            # useful REAL move. Only when every slot is an HM is declining the
                            # correct — and only possible — answer.
                            _elig = [i for i in range(len(_mv)) if _mv[i] is not None and not _is_hm(i)]
                            _zero = [i for i in _elig if _mv[i].move.base_power == 0]
                            _pick = (
                                _zero[0]
                                if _zero
                                else (min(_elig, key=lambda i: _mv[i].move.base_power) if _elig else 4)
                            )
                            _hm_name = _mv[move_to_forget].move.name
                            if _pick == 4:
                                context.message = (
                                    f"Every move is an HM — declining {move_to_learn.name}."
                                    if move_to_learn is not None
                                    else "Every move is an HM — declining the new move."
                                )
                            else:
                                context.message = (
                                    f"{_hm_name} is an HM and cannot be forgotten — "
                                    f"replacing {_mv[_pick].move.name} instead."
                                )
                            move_to_forget = _pick
                    except Exception:
                        pass  # can't read the slots — fall through to the normal answer
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
            _reset_stalled_exits()  # a clean resolution clears the re-entry counter
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
