from typing import Generator

from modules.battle_menuing import scroll_to_battle_action, scroll_to_move
from modules.battle_state import (
    BattleState,
    get_battle_state,
    battle_is_active,
    get_main_battle_callback,
    get_battle_controller_callback,
    get_current_battle_script_instruction,
)
from modules.battle_strategies import BattleStrategy, TurnAction, SafariTurnAction
from modules.context import context
from modules.debug import debug
from modules.items import Item, ItemBattleUse, get_pokeblocks
from modules.memory import read_symbol, unpack_uint32, get_game_state, GameState, get_game_state_symbol, unpack_uint16
from modules.menuing import scroll_to_item_in_bag, scroll_to_party_menu_index
import os as _os_ki96

from modules.pokemon_party import get_party, get_party_size
from modules.text_printer import TextPrinterState, get_text_printer

#: ⛔⛔ KI-93 — SELECTION REFUSALS, REMEMBERED ACROSS CALLS.
#: The game can REFUSE a chosen move at selection time and re-prompt WITHOUT consuming the turn
#: (`src/battle_util.c:999`). A deterministic chooser then answers identically for ever.
#: ‼ THIS IS MODULE-LEVEL BECAUSE A FUNCTION-LOCAL PROVABLY CANNOT WORK. The 2026-09-06 census
#: measured `handle_battle_action_selection` being RE-ENTERED five times inside one refusal episode
#: (the per-call counter restarts at 1 each time), so a local `set` is destroyed between every pick.
#: The documented "attempt 2" design assumed one call per selection phase and was refuted by that
#: drive — see `KI-93` in `05-KNOWN-ISSUES.md`.
#: Keyed by battler index; values are MOVE SLOTS the game refused this refusal-episode.
_ki93_refused_slots: dict[int, set[int]] = {}
#: The slot most recently COMMITTED per battler — a candidate is not an attempt, so this records
#: only what the handler actually acted on.
_ki93_last_committed: dict[int, int] = {}
#: ⛔⛔ WHICH POKEMON OWNS THE MEMORY ABOVE, by `personality_value`.
#: A battler index is a POSITION; the thing that earns a refusal is a POKEMON. Keyed by index alone,
#: the memory outlived its owner: MEASURED 2026-09-06 — Swellow was Tormented into
#: `refused={0: {0,1,3}}`, FAINTED, and Castform came in to the same slot and had three of its four
#: moves vetoed for two turns having been refused nothing, in the battle that then whited out.
#: `CLAUDE.md` SESSION DISCIPLINE #3 says this in capitals: *assert IDENTITY, never position.*
_ki93_owner: dict[int, int] = {}

#: Battle scripts that mean "the game rejected your SELECTION and is re-prompting". Torment is the
#: one the Elite Four guarantees; the others are the rest of the class from
#: `TrySetCantSelectMoveBattleScript` (`src/battle_util.c:976-1080`).
KI93_SELECTION_REFUSAL_SCRIPTS = (
    "BattleScript_SelectingTormentedMove",
    "BattleScript_SelectingDisabledMove",
    "BattleScript_SelectingTauntedMove",
    "BattleScript_SelectingImprisonedMove",
    "BattleScript_SelectingNotAllowedMoveChoiceItem",
    "BattleScript_SelectingMoveWithNoPP",
)


def _ki93_forget(battler_index: int | None = None) -> None:
    """Drop the refusal memory once the battle has moved on.

    ⛔ Scoped deliberately: a STALE entry costs at most one turn of second-best move choice, while a
    memory cleared too eagerly restores the livelock. It is cleared when an ORDINARY battle script is
    observed, i.e. the turn actually executed.
    """
    if battler_index is None:
        _ki93_refused_slots.clear()
        _ki93_last_committed.clear()
        _ki93_owner.clear()
    else:
        _ki93_refused_slots.pop(battler_index, None)
        _ki93_last_committed.pop(battler_index, None)
        _ki93_owner.pop(battler_index, None)


def _ki93_battler_for(battle_state, battler_index):
    """The `BattlePokemon` currently occupying `battler_index`, or None."""
    try:
        return (
            battle_state.own_side.left_battler
            if battler_index == 0
            else battle_state.own_side.right_battler
        )
    except Exception:  # noqa: BLE001 - `_ki93_battler_for` answers 'who is in this slot?'. Returning None means UNKNOWN, and every caller treats UNKNOWN as 'do not touch the refusal memory' — the safe direction.
        return None


def _ki93_check_owner(battle_state, battler_index) -> None:
    """⛔ DROP THE MEMORY IF THE POKEMON IN THIS SLOT IS NOT THE ONE THAT EARNED IT.

    Called before the memory is READ and before it is WRITTEN, so a faint, a switch, or a new battle
    can never let one Pokemon's vetoes apply to another's move list.
    """
    battler = _ki93_battler_for(battle_state, battler_index)
    try:
        pid = None if battler is None else battler.personality_value
    except Exception:  # noqa: BLE001 - identity check. If the PID cannot be read we keep the memory UNCHANGED rather than guess; a wrong DROP would only lose a veto (bounded), and a wrong KEEP is what the caller re-checks.
        pid = None
    if pid is None:
        return
    if _ki93_owner.get(battler_index) != pid:
        _ki93_refused_slots.pop(battler_index, None)
        _ki93_last_committed.pop(battler_index, None)
        _ki93_owner[battler_index] = pid



@debug.track
def handle_battle_action_selection(strategy: BattleStrategy) -> Generator:
    battle_state = get_battle_state()
    previous_battler_index = None
    #: ‼ KI-46 — CONSECUTIVE FRAMES SPENT WITHOUT RECOGNISING THE BATTLE STATE.
    #:
    #: The loop's own exit conditions are sound (battle over, or the main callback moves on),
    #: but if the battle stays ACTIVE in turn-action-selection while the CONTROLLER callback
    #: is something none of the branches below match, control falls to the bare
    #: `else: yield; continue` and spins there for ever.
    #:
    #: Measured batch10 (`x4-runs/20260803-164713`): lanes H2 and H8 both wedged here for ~59
    #: minutes; **H8 completed 0 runs in the whole 180-minute batch** and H2 managed 2 against
    #: 4-5 elsewhere. Their stacks stopped at `battle_action_selection.py:55` with **zero**
    #: `_select_in_menu` dumps, so this is NOT KI-45 — that fix was one instance of a pattern,
    #: and this is another.
    #:
    #: ‼ Both existing guards are structurally blind here, for the same reasons as KI-45: the
    #: global watchdog needs an UNCHANGED progress signature and a battle keeps changing it,
    #: and the per-run frame budget is KI-36's "cannot fire while a battle handler is on the
    #: stack". An unbounded wait on this path has no safety net but its own bound.
    #:
    #: 600 frames is ~10 seconds. Any legitimate wait here is a few frames of animation; the
    #: counter RESETS the moment a real decision is made, so a long multi-turn battle never
    #: accumulates toward it.
    _MAX_UNRECOGNISED_FRAMES = 600
    #: ⛔ KI-93 — press B on one frame in every N while a `\p` prompt is parked. N must be >1 so the
    #: other frames RELEASE the button and the next press is a genuine edge; and comfortably >1 so a
    #: single stale press cannot land on the re-opened menu before the printer state is re-read.
    _KI93_DISMISS_PERIOD = 12
    unrecognised = 0

    # ⛔⛔ KI-93 CENSUS — OBSERVE ONLY, env-gated, no behaviour change. Remove once KI-93 is closed.
    # ‼ `os` is NOT imported at module level in this file (checked, not assumed — an instrument that
    # raises on its first line substitutes the subject just as thoroughly as one that logs nothing).
    import os as _os

    _ki93 = _os.environ.get("POKEBOT_KI93_CENSUS", "").strip() == "1"
    _ki93_wait = 0            # consecutive frames inside the CompleteOnInactiveTextPrinter branch
    _ki93_recorded_park = False  # have we already banked a refusal for THIS park episode?
    _ki93_last_slot = None    # the slot we last COMMITTED (not what the strategy considered)
    _ki93_seen = {}           # branch -> count, so the alternation is visible

    def _ki93_log(message: str) -> None:
        # ‼ `debug_logger.event`, NOT `.log` — `.log` does not exist, and three KI-93 verdicts were
        # VOID because an AttributeError for exactly that was swallowed by a bare except.
        if not _ki93:
            return
        try:
            from modules import debug_logger

            debug_logger.event(message, category="BATTLE")
        except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
            pass

    # ⭐ THE CONTROL. Unconditional (given the env flag), before any branch is taken. A drive whose
    # log has no `[KI93-CTL]` line proves the logger never ran, and every other conclusion from that
    # drive must be discarded rather than believed.
    _ki93_log("[KI93-CTL] handle_battle_action_selection entered — census armed")

    while battle_is_active() and get_main_battle_callback() in ("HandleTurnActionSelectionState", "sub_8012324"):
        if unrecognised >= _MAX_UNRECOGNISED_FRAMES:
            # RAISE through the designed channel (see `modules/battle_fault`): one recoverable
            # derail for a mode that opted in, rather than an infinite lane. The reason names
            # the callbacks BECAUSE THAT IS THE DIAGNOSIS — the next reader needs to know
            # which unrecognised state the game was actually in.
            reason = (
                f"KI-46: battle action selection stuck for {unrecognised} frames — "
                f"main={get_main_battle_callback()!r} "
                f"controller0={get_battle_controller_callback(0)!r}"
            )
            # ‼ IMPORT BOTH LOCALLY. `BotModeError` is NOT imported at this module's top, and
            # a NameError here would be raised INSTEAD of the honest error — the same trap
            # that made `#24-leadcounter` silently dead for two batches (08-MISTAKES
            # 2026-08-03). Checked by `repro_ki46_action_selection_bound.py`, which drives
            # this branch for real rather than reading the source.
            from modules.battle_fault import request_mode_recovery
            from modules.modes import BotModeError

            if request_mode_recovery(reason):
                return
            raise BotModeError(reason)
        if get_battle_controller_callback(0) in ("HandleInputChooseAction", "sub_802C098", "bx_battle_menu_t6_2"):
            battler_index = 0
            if battle_state.is_safari_zone_encounter:
                action, index = strategy.decide_turn_in_safari_zone(battle_state)
            elif battle_state.is_double_battle:
                action, index = strategy.decide_turn_in_double_battle(battle_state, 0)
            else:
                action, index = strategy.decide_turn(battle_state)

        elif battle_state.is_double_battle and get_battle_controller_callback(2) in (
            "HandleInputChooseAction",
            "sub_802C098",
        ):
            battler_index = 2
            action, index = strategy.decide_turn_in_double_battle(battle_state, 1)

        elif get_battle_controller_callback(0) in (
            "HandleInputChooseMove",
            "HandleAction_ChooseMove",
        ) or (
            battle_state.is_double_battle
            and get_battle_controller_callback(2) in ("HandleInputChooseMove", "HandleAction_ChooseMove")
        ):
            # ⛔ KI-93 CENSUS — Q4. This branch backs out of an opened move menu with B. The
            # earlier census suggests the Torment cycle alternates between here and the wait
            # branch; this counts it rather than assuming it.
            # ⛔⛔ LIFETIME. Torment forbids the LAST MOVE USED (`src/battle_util.c:999`), and that
            # changes every time a turn actually executes — so a refusal is true only for the
            # selection episode that produced it. Seeing an ORDINARY battle script here means the
            # turn ran, which makes every banked veto stale. Previously the only clearing rule lived
            # in the parked-printer branch, which almost never coincides with an ordinary prompt, so
            # vetoes accumulated across turns and (before the identity fix) across Pokemon.
            try:
                _instr_cancel = get_current_battle_script_instruction() or ""
                if _instr_cancel and _instr_cancel not in KI93_SELECTION_REFUSAL_SCRIPTS:
                    _ki93_forget()
            except Exception:  # noqa: BLE001 - never let bookkeeping break the battle
                pass
            if _ki93:
                _ki93_seen["cancelB"] = _ki93_seen.get("cancelB", 0) + 1
                if _ki93_seen["cancelB"] in (1, 10, 50, 200, 1000):
                    try:
                        _instr = get_current_battle_script_instruction()
                    except Exception:  # noqa: BLE001 - reading the battle script for the census. `<unreadable>` is logged as itself, so a broken read can never be mistaken for a quiet one.
                        _instr = "<unreadable>"
                    _ki93_log(f"[KI93-CANCEL] n={_ki93_seen['cancelB']} instr={_instr!r} "
                              f"last_committed_slot={_ki93_last_slot}")
            context.emulator.press_button("B")
            yield
            unrecognised += 1
            continue

        elif get_battle_controller_callback(0) in (
            # ‼ KNOWN WAIT STATES — recognised, so they must NOT count toward the KI-46 bound.
            # Measured batch11 (`x4-runs/20260804-062303`): the KI-46 diagnostic named this
            # exact callback — `controller0='CompleteOnInactiveTextPrinter2'` at Norman — and
            # faulted a battle that was merely waiting for text to finish printing. That is
            # the bound doing its job (it reported the state instead of spinning) AND a real
            # gap in the branch list: the game IS progressing, we simply had no branch for it.
            #
            # Safe to wait rather than bound tightly, because the KI-47 net still backstops
            # this whole handler at ~50s if the printer genuinely never completes.
            "CompleteOnInactiveTextPrinter",
            "CompleteOnInactiveTextPrinter2",
        ):
            # ⛔⛔ KI-93 — THIS BRANCH USED TO BE A BARE `yield; continue`, AND THAT WAS THE HANG.
            # A battle message ending in `\p` (CHAR_PROMPT_CLEAR) parks the text printer in
            # `RENDER_STATE_CLEAR` waiting for an EDGE-TRIGGERED `JOY_NEW(A|B)`; outside link and
            # recorded battles `gTextFlags.autoScroll` is FALSE, so there is NO timeout and no
            # auto-advance — it waits for ever while we politely yield. 61 battle strings end in
            # `\p`, so this is a CLASS of hangs, not a Torment special case.
            _ki93_wait += 1
            if _ki93 and (_ki93_wait in (1, 30, 120, 600, 1800, 5000) or _ki93_wait % 10000 == 0):
                try:
                    _instr = get_current_battle_script_instruction()
                except Exception:  # noqa: BLE001 - reading the text printer. `_parked = False` means 'do not press', i.e. a failed read leaves the PRE-FIX behaviour rather than pressing B blindly into an unknown state.
                    _instr = "<unreadable>"
                _ki93_log(
                    f"[KI93-WAIT] frames={_ki93_wait} cb0={get_battle_controller_callback(0)!r} "
                    f"instr={_instr!r} last_committed_slot={_ki93_last_slot}"
                )

            # ---- KI-93 (a): DISMISS, GATED ON THE PRINTER'S OWN STATE --------------------------
            # ⭐ The discriminator between "parked waiting for a button" and "glyphs still printing"
            # is memory-readable: `sTextPrinters[0].state`. `modules/modes/_listeners.py:168-170`
            # already tests exactly this, so it is house style, not a new idea.
            # ⛔ NEVER gate this on a frame count. A press delivered while glyphs are printing is
            # consumed as a text SPEED-UP and is NOT the dismissal press, so a timer-driven press
            # would burn its edge and still hang.
            try:
                _printer = get_text_printer(0)
                _parked = _printer.active and _printer.state == TextPrinterState.WaitForButton
            except Exception:  # noqa: BLE001 - reading the printer must never break the battle
                _parked = False

            if _parked:
                _instr_now = ""
                try:
                    _instr_now = get_current_battle_script_instruction() or ""
                except Exception:  # noqa: BLE001 - reading the battle script at the dismiss site. Empty string means 'no refusal recognised', so a failed read skips the RECORD and the memory stays as it was.
                    _instr_now = ""

                # ⛔⛔ THE NESTING HERE IS LOAD-BEARING AND I GOT IT WRONG ONCE (2026-09-06).
                # Writing this as `if refusal and not recorded: … elif instr: forget()` meant that on
                # the frame AFTER banking a refusal the first test went False, the `elif` saw a
                # perfectly truthy `SelectingTormentedMove`, and `_ki93_forget()` WIPED the memory —
                # measured as `refused={}` on every line and `KI93-REPICK: 0`.
                # ⇒ the "turn moved on" test must be nested UNDER "the script is not a refusal",
                # never made the fall-through of a guard about something else.
                if _instr_now in KI93_SELECTION_REFUSAL_SCRIPTS:
                    if not _ki93_recorded_park:
                        # ---- KI-93 (b): REMEMBER THE REFUSED SLOT ------------------------------------
                        # ⛔ Dismissing ALONE only converts the hang into a livelock: the engine returns
                        # to STATE_WAIT_ACTION_CHOSEN and re-emits CHOOSEMOVE with the move cursor
                        # UNMOVED, so a deterministic chooser picks the same slot again — and each pass
                        # silently wipes Rollout / Fury Cutter / Outrage counters via
                        # `CancelMultiTurnMoves`. Both halves or neither.
                        # ⛔⛔ ONCE PER PARK EPISODE, NOT ONCE PER FRAME. MEASURED 2026-09-06: recording
                        # every frame filled the set with ALL FOUR SLOTS (`refused={0: {0,1,2,3}}`), the
                        # re-pick below then found no alternative, and the livelock returned. The cause is
                        # that `get_current_battle_script_instruction()` still reads
                        # `SelectingTormentedMove` during the NEXT park, so each freshly re-picked slot was
                        # marked refused although the game had never rejected it.
                        # ⇒ ‼ A STALE SIGNAL READ REPEATEDLY MANUFACTURES EVIDENCE. Sample a level once
                        # per edge, never continuously.
                        _ki93_recorded_park = True
                        for _bi in ((0, 2) if battle_state.is_double_battle else (0,)):
                            # ⛔ IDENTITY FIRST. If the mon in this slot changed, the old vetoes are
                            # not ours to keep.
                            _ki93_check_owner(battle_state, _bi)
                            _refused_for = _ki93_last_committed.get(_bi)
                            if _refused_for is None:
                                continue
                            _set = _ki93_refused_slots.setdefault(_bi, set())
                            _set.add(_refused_for)
                            # ⛔ A FULL SET IS DEFINITIONALLY WRONG. Torment forbids exactly ONE move (the
                            # last used), and the engine takes the Struggle path when nothing is usable —
                            # so it never opens the move menu with every slot blocked. If our set ever
                            # covers every move with PP, our bookkeeping is wrong, not the game: keep only
                            # the newest observation rather than paralysing the chooser.
                            try:
                                _bat = (
                                    battle_state.own_side.left_battler
                                    if _bi == 0
                                    else battle_state.own_side.right_battler
                                )
                                _usable = {
                                    _s for _s, _lm in enumerate(_bat.moves)
                                    if _lm is not None and _lm.pp > 0
                                } if _bat is not None else set()
                            except Exception:  # noqa: BLE001 - reading the mon's usable moves for the collapse guard. An empty set disables the collapse for this pass; the guard is a safety net, and skipping it is safer than collapsing on a half-read move list.
                                _usable = set()
                            if _usable and _usable.issubset(_set):
                                _ki93_log(f"[KI93-RESET] refusal set covered every usable slot "
                                          f"{sorted(_usable)} — collapsing to {{{_refused_for}}}")
                                _ki93_refused_slots[_bi] = {_refused_for}
                elif _instr_now:
                    # An ORDINARY prompt is on screen ⇒ the turn moved on ⇒ prior refusals are
                    # history. This is the memory's only clearing rule (see `_ki93_forget`).
                    _ki93_forget()

                # ⛔ GUARANTEE AN EDGE. `newKeys = keyInput & ~heldKeysRaw`, so a HELD button is
                # invisible — and the branch 20 lines above mashes B every frame on the move menu,
                # which means we can arrive here mid-hold. Pressing on ONE frame out of every
                # `_KI93_DISMISS_PERIOD` leaves the rest released, so each press is a true edge.
                # ⭐ B, NOT A: the move cursor is not reset, so a stray A would re-commit the very
                # move that was just refused; a stray B falls back to the action menu, where B is
                # inert in a single battle.
                if _ki93_wait % _KI93_DISMISS_PERIOD == 0:
                    context.emulator.press_button("B")
                    _ki93_log(f"[KI93-DISMISS] pressed B at frame {_ki93_wait} instr={_instr_now!r} "
                          f"owner={_ki93_owner.get(0)}")
            yield
            continue

        else:
            yield
            unrecognised += 1
            continue

        # A branch above assigned `battler_index`, i.e. the state was recognised and a real
        # decision was made. Clear the stall counter so a long multi-turn battle never
        # accumulates toward the KI-46 bound.
        unrecognised = 0

        # ⛔⛔ KI-93 (b) — DO NOT RE-SUBMIT A SLOT THE GAME HAS ALREADY REFUSED THIS EPISODE.
        # Without this the dismiss in the wait branch merely converts a hang into a livelock.
        # ⭐ Excluding slots is SAFE: if every move were unusable the engine would take the Struggle
        # path and never open the move menu at all, so this can never strand the turn.
        # ⛔ IDENTITY FIRST — see `_ki93_check_owner`. Without this a fainted mon's vetoes silently
        # apply to its replacement, which was MEASURED forcing Castform into Sunny Day twice.
        _ki93_check_owner(battle_state, battler_index)
        _ki93_refused = _ki93_refused_slots.get(battler_index)
        if (
            _ki93_refused
            and isinstance(index, int)
            and index in _ki93_refused
            and action in (
                TurnAction.UseMove,
                TurnAction.UseMoveAgainstRightSideOpponent,
                TurnAction.UseMoveAgainstPartner,
            )
        ):
            _ki93_battler = (
                battle_state.own_side.left_battler
                if battler_index == 0
                else battle_state.own_side.right_battler
            )
            _ki93_alt = None
            try:
                if _ki93_battler is not None:
                    for _slot, _learned in enumerate(_ki93_battler.moves):
                        if _learned is not None and _learned.pp > 0 and _slot not in _ki93_refused:
                            _ki93_alt = _slot
                            break
            except Exception:  # noqa: BLE001 - never let the re-pick break the battle
                _ki93_alt = None
            if _ki93_alt is not None:
                _ki93_log(f"[KI93-REPICK] battler={battler_index} owner={_ki93_owner.get(battler_index)} "
                          f"slot {index} was REFUSED -> {_ki93_alt}")
                index = _ki93_alt
            # ⛔ If no alternative exists, fall through with the original pick rather than inventing
            # one. The engine's Struggle path is the correct handler for "nothing is usable", and
            # second-guessing it here would be a worse bug than the one being fixed.

        # ⛔ KI-93 — record what the handler is about to ACT on (a candidate is not an attempt), in
        # MODULE-LEVEL state so it survives the re-entry the census measured.
        if isinstance(index, int):
            _ki93_last_committed[battler_index] = index

        if _ki93:
            if _ki93_wait:
                _ki93_log(f"[KI93-WAIT] ENDED after {_ki93_wait} frames -> a decision was reached")
            _ki93_last_slot = index if isinstance(index, int) else _ki93_last_slot
            _ki93_seen[f"decide@{battler_index}"] = _ki93_seen.get(f"decide@{battler_index}", 0) + 1
            _ki93_log(f"[KI93-COMMIT] battler={battler_index} owner={_ki93_owner.get(battler_index)} "
                      f"action={action!r} slot={index!r} census={_ki93_seen} "
                      f"refused={_ki93_refused_slots}")
        _ki93_wait = 0
        _ki93_recorded_park = False

        # ‼ `#24-bosstelemetry` (2026-08-09) — ONE LINE PER DECISION. This is the instrument the
        # project has been missing. Six `--driver normancounter` arms (a Fighting counter injected
        # at L18/22/26/40/55, plus a no-counter control) ALL lost to Norman's L28-31 team, and the
        # logs could not say WHY: they carry `[BATTLE] started/ended` and the faint-chooser, and
        # NOTHING about what was actually done on a turn. **79% of all non-finishing runs end on a
        # lost boss fight**, so "which move did we pick, against what, at what HP" is the
        # highest-value fact this bot does not record.
        #
        # ‼ INSTRUMENTATION MUST NEVER AFFECT THE BATTLE — the same contract as the faint-chooser
        # event: everything inside one try/except, no state mutated, and one line per DECISION
        # (not per frame), so even a long battle costs a handful of lines.
        try:
            from modules import debug_logger

            _me = (
                battle_state.own_side.left_battler
                if battler_index == 0
                else battle_state.own_side.right_battler
            )
            _foe = battle_state.opponent.left_battler
            _what = getattr(action, "name", str(action))
            if (
                action
                in (
                    TurnAction.UseMove,
                    TurnAction.UseMoveAgainstRightSideOpponent,
                    TurnAction.UseMoveAgainstPartner,
                )
                and _me is not None
            ):
                try:
                    _lm = _me.moves[index]
                    _what = f"{_what}:{_lm.move.name}(pp{_lm.pp})"
                except Exception:  # noqa: BLE001
                    _what = f"{_what}:idx{index}"

            def _status_of(mon) -> str:
                """Permanent + temporary status, compactly. '' when perfectly healthy.

                ‼‼ THIS IS NOT DECORATION — it is the field that decides `#24-bosstelemetry`'s
                LEAD 2, open since 2026-08-09 ("a 'selected but not executed' pattern also appears
                on NATURAL mons mid-battle"). Measured 2026-08-11 on the Maxie fight:

                    [TURN 3] Sceptile L44 122/122 -> UseMove:Slam(pp19)  vs Crobat L38 90/119
                    [TURN 4] Sceptile L44 110/122 -> UseMove:Slam(pp19)  vs Crobat L38 90/119
                    [TURN 6] Sceptile L44   4/122 -> UseMove:Slam(pp19)  vs Crobat L38 90/119

                PP frozen at 19 across three selections, the opponent untouched, and the party's
                best attacker dead. ‼ A MISS cannot explain frozen PP — a missed move still
                consumes it. But **sleep, freeze, full paralysis, flinch and a confusion self-hit
                do not consume PP either**, and Crobat learns Confuse Ray and Bite. Two causes,
                opposite fixes, and the turn line could not tell them apart because it printed
                species / level / HP and nothing else.

                Without this field every boss-loss post-mortem in the project has had to end in
                "either a bot bug or ordinary status". With it, the log answers.
                """
                try:
                    perm = getattr(getattr(mon, "status_permanent", None), "name", None)
                    parts = [perm] if perm and perm != "Healthy" else []
                    parts += [
                        getattr(t, "name", str(t))
                        for t in (getattr(mon, "status_temporary", None) or [])
                    ]
                    return "/".join(parts)
                except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
                    return "?"

            def _describe(mon) -> str:
                if mon is None:
                    return "?"
                status = _status_of(mon)
                return (
                    f"{getattr(getattr(mon, 'species', None), 'name', '?')}"
                    f" L{getattr(mon, 'level', '?')}"
                    f" {getattr(mon, 'current_hp', '?')}/{getattr(mon, 'total_hp', '?')}"
                    # Only printed when there IS something — a healthy mon must not gain noise on
                    # every one of the ~800 battle-level samples a batch produces.
                    + (f" [{status}]" if status else "")
                )

            debug_logger.event(
                f"[TURN {getattr(battle_state, 'current_turn', '?')}] "
                f"{_describe(_me)} -> {_what}  vs {_describe(_foe)}",
                category="BATTLE",
            )
        except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
            pass

        if context.bot_mode == "Manual":
            yield
            continue

        # FORK (2026-07-23, batch7 run03): if the game just bounced the previous pick
        # with "There's no PP left for this move!" (BattleScript_SelectingMoveWithNoPP),
        # do NOT resubmit the strategy's choice — some strategy paths re-pick the same
        # dead move forever (a 20k-frame hang in long training runs where PP drains).
        # Override with the first move that still has PP; the game auto-Struggles when
        # every slot is empty (that path never reaches this bounce).
        try:
            if action in (
                TurnAction.UseMove,
                TurnAction.UseMoveAgainstRightSideOpponent,
                TurnAction.UseMoveAgainstPartner,
            ) and get_current_battle_script_instruction() == "BattleScript_SelectingMoveWithNoPP":
                _battler = (
                    battle_state.own_side.left_battler
                    if battler_index == 0
                    else battle_state.own_side.right_battler
                )
                if _battler is not None:
                    for _i, _lm in enumerate(_battler.moves):
                        if _lm is not None and _lm.pp > 0:
                            index = _i
                            break
        except Exception:
            pass

        # In double battles, both player Pokémon will do their inputs in the same run. So the active
        # battler might change in the middle of this function. If we detect that, we update the battle
        # state as the previous Pokémon's actions might have changed it (e.g. by using potions.)
        if previous_battler_index != battler_index:
            battle_state = get_battle_state()
            previous_battler_index = battler_index

        match action:
            case TurnAction.UseMove | TurnAction.UseMoveAgainstRightSideOpponent | TurnAction.UseMoveAgainstPartner:
                yield from battle_action_use_move(action, battler_index, index, battle_state)

            case TurnAction.UseItem:
                if isinstance(index, tuple):
                    index, target_index = index
                else:
                    target_index = None

                if not isinstance(index, Item):
                    raise RuntimeError(f"`TurnAction.UseItem` needs an item object as its first argument.")
                if index.battle_use == ItemBattleUse.NotUsable:
                    raise RuntimeError(f"Item `{index.name}` cannot be used in battle.")
                if index.battle_use in (ItemBattleUse.Healing, ItemBattleUse.PpRecovery) and target_index is None:
                    raise RuntimeError(f"Item `{index.name}` needs a target Pokémon.")

                yield from battle_action_use_item(battle_state, index, target_index)

            case TurnAction.RotateLead:
                if index >= get_party_size():
                    raise RuntimeError(
                        f"Cannot switch in party slot #{index} because the party only has {get_party_size()} Pokémon."
                    )

                if index == battle_state.battling_pokemon[0].party_index or (
                    len(battle_state.battling_pokemon) > 2 and index == battle_state.battling_pokemon[2].party_index
                ):
                    raise RuntimeError(f"Cannot switch in {get_party()[index].name} because it is already in battle.")

                in_battle_index = battle_state.map_battle_party_index(index)

                # ⛔⛔ KI-96 CENSUS — OBSERVE ONLY, env-gated, NO behaviour change. Remove when KI-96
                # is closed. The loop below is an unbounded `while PARTY_MENU: press A` with no check
                # that the switch was ACCEPTED; it wedges §Ch23's chain with the L60 party. The
                # refusal REASON has never been measured, and KI-93 proved that guessing costs four
                # implement-drive-revert cycles.
                _ki96 = _os_ki96.environ.get("POKEBOT_KI96_CENSUS", "").strip() == "1"

                def _ki96_log(message: str) -> None:
                    # ‼ `debug_logger.event`, NOT `.log` — `.log` does not exist, and three KI-93
                    # verdicts were VOID because that AttributeError was swallowed.
                    if not _ki96:
                        return
                    try:
                        from modules import debug_logger

                        debug_logger.event(message, category="BATTLE")
                    except Exception:  # noqa: BLE001 - instrumentation must never affect the battle,
                        # and a failure here costs only a log line; the CONTROL below reveals it.
                        pass

                def _ki96_who(slot):
                    """species/PID/HP at a PARTY slot — the identity, never just the number."""
                    try:
                        mon = get_party()[slot]
                        if mon is None:
                            return f"slot{slot}=<empty>"
                        return (f"slot{slot}={mon.species.name}#{mon.personality_value:08X}"
                                f" L{mon.level} {mon.current_hp}/{mon.total_hp}")
                    except Exception:  # noqa: BLE001 - a failed read prints as unreadable, so a
                        # broken reader can never be mistaken for a healthy negative.
                        return f"slot{slot}=<unreadable>"

                # ⭐ THE CONTROL. Unconditional (given the flag), before anything is pressed.
                _ki96_log(f"[KI96-CTL] RotateLead arm entered — census armed")
                # ⭐⭐ Q1: THE TWO INDEX SPACES, SIDE BY SIDE, WITH IDENTITIES.
                _ki96_log(f"[KI96-INDEX] requested party index={index} -> mapped menu "
                          f"in_battle_index={in_battle_index}  |  {_ki96_who(index)}  |  "
                          f"party_size={get_party_size()}")
                # ⭐⭐ THE NAMED NEXT MEASUREMENT (`KI-96`): dump the RAW nibble-packed order the
                # mapping walks, decoded, beside the ACTIVE battler's own party index. This is what
                # decides between "the array is stale", "it is the wrong battler's", and "battle
                # position 0 is simply the active slot, so any mapping onto 0 is unusable".
                # ⛔ It is printed, never acted on — rule 10: measure a coordinate conversion's
                # DIRECTION before changing it.
                try:
                    _raw = bytes(battle_state._battler_party_order)
                    _decoded = []
                    for _i in range(6):
                        _b = _raw[_i // 2]
                        _decoded.append((_b >> 4) if _i % 2 == 0 else (_b & 0xF))
                    _active = battle_state.battling_pokemon[0].party_index
                    _ki96_log(f"[KI96-ORDER] raw={_raw.hex()} decoded_battleorder={_decoded} "
                              f"(battle_pos -> party_index)  active_battler_party_index={_active}  "
                              f"=> menu slot {in_battle_index} holds party "
                              f"{_decoded[in_battle_index] if in_battle_index < 6 else '?'}")
                except Exception as _e:  # noqa: BLE001 - a failed dump prints itself, so an
                    # unreadable order can never be mistaken for a benign one.
                    _ki96_log(f"[KI96-ORDER] <unreadable: {type(_e).__name__}: {_e}>")

                # ⛔ KI-96 STAGE TRACE — OBSERVE ONLY. The mapping is MEASURED CORRECT, so the fault
                # is somewhere in this four-step sequence. Log the state after EACH step, because
                # "the switch is refused" is a conclusion and these are the observations under it.
                def _ki96_state():
                    try:
                        return (f"state={get_game_state().name} "
                                f"actioncursor={read_symbol('gActionSelectionCursor')[0]}")
                    except Exception as _e:  # noqa: BLE001 - a failed read names itself, so it can
                        # never be mistaken for a healthy reading.
                        return f"<unreadable: {type(_e).__name__}>"

                # ⛔⛔ KI-96 — OBSERVE-ONLY. A REFUSAL USED TO LIVE HERE AND WAS WITHDRAWN.
                # It refused any rotation where `decoded_battleorder[0] != active party index`,
                # on the theory that this meant a STALE array. A decomp verification
                # (pret/pokeemerald @ 5eff7864) showed that inequality ALSO holds transiently on a
                # perfectly healthy switch — `switchhandleorder` rewrites the order BEFORE
                # `getswitchedmondata` advances `gBattlerPartyIndexes`
                # (`data/battle_scripts_1.s:3110-3112`) — so the guard would have REFUSED
                # LEGITIMATE ROTATIONS. A guard with false positives is worse than no guard.
                #
                # ⛔⛔ RETRACTION, 2026-09-07 — A "REFUTED" VERDICT THAT USED TO SIT HERE WAS WRONG.
                # This comment claimed the "stale leftover array" theory had been MEASURED FALSE,
                # citing `[KI96-REREAD] ... VERDICT=AGREE`. **The probe was VACUOUS.** Its frame
                # stamps show BOTH reads at f5864245 — five frames BEFORE the A press and 77 frames
                # before the party menu existed:
                #     f5864245 [KI96-STAGE] 1 after scroll_to_battle_action(2): state=BATTLE
                #     f5864245 [KI96-REREAD] ... VERDICT=AGREE
                #     f5864250 [KI96-STAGE] 2 at the A press
                #     f5864322 [KI96-STAGE] 3 ...: state=PARTY_MENU
                # `scroll_to_battle_action(2)` only moves the ACTION CURSOR; `PlayerHandleChoosePokemon`
                # is what refills `gBattlePartyCurrentOrder`, and it cannot run until after the A
                # press. ⇒ AGREE was two reads of the SAME pre-request value.
                # ⇒ **THE STALE-ARRAY THEORY IS UNTESTED, NOT REFUTED.** The probe now lives after
                # STAGE 3 and prints the state it was taken in.
                # ‼ THE RULE THIS BROKE IS THIS PROJECT'S OWN: *instrument the ACTION, not the INPUT
                # to it* — and the refutation was inside the very log line being quoted (`state=BATTLE`).
                #
                # ⛔ ALSO RETRACTED: "the state and the screen disagree". `get_game_state()` reads
                # `gMain.callback2` and caches per-frame (`modules/memory.py:245-272`), so it CANNOT
                # report PARTY_MENU while the action screen is up. What is stale is `bt=`
                # (`gDisplayedStringBattle`, written by `PlayerHandleChooseAction` and never cleared
                # when the menu opens) and `instr=` (`Cmd_end2` does not advance the script pointer).
                # ⇒ **The menu IS open and IS accepting every press — the game is actively REFUSING
                # the selection and bouncing back to the chooser.** The STUCK dump proves it:
                # `tasks=['Task_ReturnToChooseMonAfterText', 'Task_PrintAndWaitForText']`, which is
                # the `TrySwitchInPokemon() == FALSE` branch of `CursorCb_SendMon`.
                #
                # ⭐ TWO LIVE HYPOTHESES — `[KI96-WHY]`'s `action` byte separates them in one drive:
                #   (1) `gPartyMenu.action` is 2 (CANT_SWITCH: Wrap family/Mean Look/Ingrain) or 4
                #       (ABILITY_PREVENTS: Shadow Tag/Arena Trap/Magnet Pull). The engine sets these
                #       BEFORE the menu opens, and then NO slot can ever be accepted — the A-mash is
                #       unwinnable by construction and the 240-bound is exactly right.
                #   (2) `action` is 0/1 — an ordinary menu — so the refusal is PER-SLOT and the AIM is
                #       wrong. ‼ A STUCK dump taken at PARTY_MENU showed the party in FIELD order
                #       (Wailord, Zigzagoon, Mightyena, ...) while the aim assumed [2,0,1,3,4,5]; if
                #       the in-menu array is identity then menu slot 0 is the ACTIVE battler and the
                #       refusal is literally "DIVER is already in battle!".
                # ⛔ DO NOT PICK ONE FROM THE ARMCHAIR. Three published root causes for this KI have
                # been measured false, and a fourth was published on a probe that measured nothing.
                #
                # ‼ A RELATED DEFECT, WORTH FIXING WHATEVER THE ANSWER: this arm has NO precondition.
                # `battle_action_use_move` presses ONLY while `get_battle_controller_callback` is an
                # input-accepting callback and stops the instant it is not; `RotateLead` scrolls
                # blind, presses blind, then mashes on `state == PARTY_MENU` — which is true both
                # while the menu waits for you AND while it prints a refusal at you.
                #
                # ⛔ DO NOT "FIX" THIS BY MOVING THE MAPPING WITHOUT READING THE MEASUREMENT FIRST.
                # `08-MISTAKES.md` rule 10: an index-space conversion gets an observe-only probe
                # against a ground truth BEFORE it is applied. `handle_fainted_pokemon` has had
                # three index-space bugs, every one applied on reasoning that sounded this good.
                _ki96_pre = None
                try:
                    _ki96_pre = (bytes(battle_state._battler_party_order),
                                 battle_state.battling_pokemon[0].party_index,
                                 in_battle_index)
                except Exception:  # noqa: BLE001 - instrumentation must never affect the battle.
                    _ki96_pre = None

                _ki96_log(f"[KI96-STAGE] 0 before scroll_to_battle_action(2): {_ki96_state()}")
                yield from scroll_to_battle_action(2)
                _ki96_log(f"[KI96-STAGE] 1 after scroll_to_battle_action(2): {_ki96_state()}")
                # JP roms need a little delay
                for _ in range(5):
                    yield
                context.emulator.press_button("A")
                # ‼ NO EXTRA `yield` HERE. Adding one to "let the press land" would insert a FRAME and
                # this would stop being observe-only — an instrument that changes the subject is not an
                # instrument. Stage 2 is therefore read on the SAME frame as the press, i.e. it shows
                # the state the press was issued INTO. Compare it with stage 1, not with stage 3.
                _ki96_log(f"[KI96-STAGE] 2 at the A press (same frame): {_ki96_state()}")

                # ⭐⭐ KI-96 ROOT FIX — RECOMPUTE THE MENU SLOT NOW THE MENU EXISTS.
                # MEASURED 2026-09-07 (`post_grind_L60`, `--driver ch23chapter`):
                #     pre (raw=201345 decoded=[2,0,1,3,4,5]) -> aims at menu slot 0
                #     post(raw=012345 decoded=[0,1,2,3,4,5]) -> aims at menu slot 2   VERDICT=DIFFER
                #     [KI96-WHY] action=0 (an ORDINARY menu, not trapped), order_in_menu='012345',
                #                msg='DIVER is already in battle!'
                # `in_battle_index` was computed ~140 lines above, BEFORE the menu existed, from an
                # order array the game had not yet refilled. Under the REAL in-menu array (identity)
                # menu slot 0 is the ACTIVE battler — so the game refused for ever, which is the
                # whole of `KI-96`.
                # ⛔ `map_battle_party_index`'s ARITHMETIC IS CORRECT. Its INPUT was read too early.
                # Do not touch the mapping.
                # ‼ BOUNDED AND FALLING BACK: if the menu never appears we keep the pre-menu value
                # and the 240-press bound below still catches it. An unbounded wait here would be a
                # new hang, which is the one thing this arm must never grow.
                _ki96_wait = 0
                while get_game_state() != GameState.PARTY_MENU and _ki96_wait < 120:
                    _ki96_wait += 1
                    yield
                if get_game_state() == GameState.PARTY_MENU:
                    try:
                        _fresh = get_battle_state().map_battle_party_index(index)
                        if _fresh != in_battle_index:
                            _ki96_log(
                                f"[KI96-FIX] menu open after {_ki96_wait} frame(s): re-mapped party "
                                f"slot {index} from menu slot {in_battle_index} (pre-menu, STALE) "
                                f"to {_fresh} (in-menu). Aiming at {_fresh}."
                            )
                        in_battle_index = _fresh
                    except Exception as _e:  # noqa: BLE001 - an unreadable order is not a reason to
                        # abandon the rotation; keep the pre-menu value and let the bound catch it.
                        _ki96_log(f"[KI96-FIX] <re-map unreadable: {type(_e).__name__}> — keeping "
                                  f"the pre-menu slot {in_battle_index}")

                yield from scroll_to_party_menu_index(in_battle_index)
                _ki96_log(f"[KI96-STAGE] 3 after scroll_to_party_menu_index({in_battle_index}): "
                          f"{_ki96_state()}")
                # ⭐⭐ THE MEASUREMENT — AND IT LIVES **HERE**, NOT EARLIER. It used to sit
                # immediately after `scroll_to_battle_action(2)`, on the assumption that call opened
                # the party menu. It does not — it only moves the ACTION CURSOR, and STAGE 1's own
                # `state=BATTLE` said so. Both reads therefore landed BEFORE the A press, five frames
                # apart, 77 frames before the menu existed, and `VERDICT=AGREE` was two reads of the
                # same pre-request value. ⛔ It proved NOTHING, and the "stale leftover" theory it was
                # built to test is UNTESTED, not refuted.
                # ‼ THE RULE THIS BROKE IS MINE: *instrument the ACTION, not the INPUT to it.* The
                # refutation was inside the very log line I was quoting.
                # `PlayerHandleChoosePokemon` is what refills `gBattlePartyCurrentOrder`, and it
                # cannot run until after the A press — so the only honest place to re-read is after
                # the menu is OBSERVED open, which is what STAGE 3 reports.
                if _ki96 and _ki96_pre is not None:
                    try:
                        _post_state = get_battle_state()
                        _post_raw = bytes(_post_state._battler_party_order)
                        _post_slot = _post_state.map_battle_party_index(index)
                        _pre_raw, _pre_act, _pre_slot = _ki96_pre
                        _dec = lambda b: [(b[k // 2] >> 4) if k % 2 == 0 else (b[k // 2] & 0xF)
                                          for k in range(6)]
                        _ki96_log(
                            f"[KI96-REREAD] party_slot={index} state_now={get_game_state().name} "
                            f"pre(raw={_pre_raw.hex()} decoded={_dec(_pre_raw)} "
                            f"aims_at_menu_slot={_pre_slot} active_was={_pre_act}) "
                            f"post(raw={_post_raw.hex()} decoded={_dec(_post_raw)} "
                            f"aims_at_menu_slot={_post_slot} active_now="
                            f"{_post_state.battling_pokemon[0].party_index}) "
                            f"VERDICT={'AGREE' if _pre_slot == _post_slot else 'DIFFER'}"
                        )
                    except Exception as _e:  # noqa: BLE001 - a failed read NAMES itself so it can
                        # never be mistaken for a healthy AGREE.
                        _ki96_log(f"[KI96-REREAD] <unreadable: {type(_e).__name__}: {_e}>")
                #: ⛔ KI-96 — A CORRECT AIM IS NOT A BOUND. A rotation can still be refused (a mon
                #: that faints between the decision and the menu opening), and this loop had no exit
                #: at all: it relied on `KI-47`'s net stopping the whole run 3001 frames later.
                #: MEASURED: a healthy switch closes the menu in ~1-27 presses, so 240 is ~9x the
                #: worst observed and cannot fire on a working rotation.
                _KI96_MENU_BOUND = 240
                _ki96_spins = 0
                while get_game_state() == GameState.PARTY_MENU:
                    _ki96_spins += 1
                    if _ki96_spins > _KI96_MENU_BOUND:
                        # Back out with B — never A. On the move menu A re-commits; B cancels to the
                        # action menu, which this handler already recognises.
                        context.emulator.press_button("B")
                        yield
                        # ‼ Same sibling-boundary rule as the stale check above: recover, don't
                        # raise. A bound that converts a recoverable stall into a Manual park has
                        # made the run WORSE, not safer.
                        from modules.battle_fault import request_mode_recovery
                        from modules.modes import BotModeError

                        _ki96_reason = (
                            f"KI-96: the in-battle party menu would not accept party slot {index} "
                            f"(menu slot {in_battle_index}) after {_ki96_spins} A-presses. Backed out "
                            f"with B and refused rather than spinning until the KI-47 net fires."
                        )
                        if request_mode_recovery(_ki96_reason):
                            return
                        raise BotModeError(_ki96_reason)
                    if _ki96 and (_ki96_spins in (1, 5, 30, 120, 600, 1800)
                                  or _ki96_spins % 5000 == 0):
                        try:
                            # ‼ `get_battle_text()` DOES NOT EXIST — checked before writing this.
                            # The harness's own `bt=` field comes from this pair
                            # (`battle_handler.py:124`); `read_symbol` is already imported here,
                            # `decode_string` lives in `modules.game`.
                            from modules.game import decode_string

                            _bt = decode_string(read_symbol("gDisplayedStringBattle"))
                        except Exception:  # noqa: BLE001 - the message is the point of Q2; if it
                            # cannot be read, say so rather than printing an empty string.
                            _bt = "<unreadable>"
                        try:
                            _instr = get_current_battle_script_instruction()
                        except Exception:  # noqa: BLE001 - same reasoning as above.
                            _instr = "<unreadable>"
                        # ⭐⭐ THE ONE BYTE THAT SEPARATES THE TWO SURVIVING HYPOTHESES.
                        # `gPartyMenu.action` is byte 11 (exitCallback 0-3, task 4-7, packed
                        # menuType/layout 8, slotId 9, slotId2 10, action 11):
                        #   2 = PARTY_ACTION_CANT_SWITCH      -> TRAPPED (Wrap family/Mean Look/
                        #                                       Ingrain). NO slot can ever be
                        #                                       accepted; the A-mash is unwinnable
                        #                                       and the 240-bound is CORRECT.
                        #   4 = PARTY_ACTION_ABILITY_PREVENTS -> Shadow Tag/Arena Trap/Magnet Pull.
                        #                                       Same: unwinnable by construction.
                        #   0/1 = an ordinary menu            -> the refusal is PER-SLOT, i.e. the
                        #                                       AIM is wrong and the order array is.
                        # ‼ Also `slotId` (byte 9): `scroll_to_party_menu_index` can return early via
                        # `request_mode_recovery`, so STAGE 3 does NOT prove the cursor arrived.
                        def _ki96_read(label, fn):
                            """One handler for every diagnostic read. A failure NAMES itself, so an
                            unreadable value can never be mistaken for a healthy one — and one
                            helper keeps this file inside the `repro_no_silent_except` per-root
                            budget instead of adding four handlers' worth of debt."""
                            try:
                                return fn()
                            except Exception as _e:  # noqa: BLE001 - see docstring; never blank.
                                return f"<unreadable {label}: {type(_e).__name__}>"

                        from modules.game import decode_string as _ds

                        _pm = _ki96_read("gPartyMenu", lambda: read_symbol("gPartyMenu"))
                        _why = {
                            # ⭐ byte 11 = `action`; byte 9 = the cursor `slotId` the game HOLDS.
                            "action": _pm[11] if isinstance(_pm, (bytes, bytearray)) else _pm,
                            "cursor_slotId": _pm[9] if isinstance(_pm, (bytes, bytearray)) else _pm,
                            "order_in_menu": _ki96_read(
                                "order", lambda: read_symbol("gBattlePartyCurrentOrder",
                                                             size=0x03).hex()),
                            "msg": _ki96_read("gStringVar4",
                                              lambda: _ds(read_symbol("gStringVar4"))),
                            # PIDs, in the order the MENU sees them — settles whether
                            # `UpdatePartyToBattleOrder` permuted the party the way the aim assumed.
                            # ‼ IDENTITY, never slot indices.
                            "pids": _ki96_read(
                                "party", lambda: [f"{p.personality_value:08X}" if p else None
                                                  for p in get_party()]),
                        }
                        _ki96_log(f"[KI96-WHY] n={_ki96_spins} {_why}")
                        # ⭐ Q2/Q3/Q4 in one line: what the game SAYS, who the target IS, how long.
                        _ki96_log(f"[KI96-SPIN] n={_ki96_spins} instr={_instr!r} bt={_bt!r} "
                                  f"target={_ki96_who(index)}")
                    context.emulator.press_button("A")
                    yield
                _ki96_log(f"[KI96-DONE] the party menu closed after {_ki96_spins} press(es) — "
                          f"the switch was ACCEPTED")

            case TurnAction.RunAway | SafariTurnAction.RunAway:
                if battle_state.is_trainer_battle:
                    raise RuntimeError("Tried to run away from a trainer battle.")
                yield from scroll_to_battle_action(3)
                context.emulator.press_button("A")
                yield

            case SafariTurnAction.ThrowBall:
                yield from scroll_to_battle_action(0)
                context.emulator.press_button("A")
                yield

            case SafariTurnAction.GoNear:
                if context.rom.is_frlg:
                    raise RuntimeError("The 'Go Near' option is not available in FR/LG Safari battles.")

                yield from scroll_to_battle_action(2)
                context.emulator.press_button("A")
                yield

            case SafariTurnAction.Pokeblock:
                if context.rom.is_frlg:
                    raise RuntimeError("The 'Pokéblock' option is not available in FR/LG Safari battles.")

                yield from battle_action_use_pokeblock(index)
                break

            case SafariTurnAction.Bait:
                if context.rom.is_rse:
                    raise RuntimeError("The 'Bait' option is not available in R/S/E Safari battles.")

                yield from scroll_to_battle_action(1)
                context.emulator.press_button("A")
                yield

            case SafariTurnAction.Rock:
                if context.rom.is_rse:
                    raise RuntimeError("The 'Rock' option is not available in R/S/E Safari battles.")

                yield from scroll_to_battle_action(2)
                context.emulator.press_button("A")
                yield

            case TurnAction.SwitchToManual | SafariTurnAction.SwitchToManual:
                context.set_manual_mode()
                yield

            case _:
                raise RuntimeError(f"Invalid turn action: {action}")


@debug.track
def battle_action_use_item(battle_state: BattleState, item: Item, target_index: int = 0):
    # ‼ `#24-battleitems` INSTRUMENTATION (2026-08-09). This flow is SELECTED BUT DOES NOT
    # RELIABLY EXECUTE: measured 5 requests -> **1 potion actually consumed**, with `Hyper Potion`
    # chosen four times on one turn of the Norman fight and HP frozen at 23/120. Every failed
    # request costs a turn in the fight this feature exists for, so the flow needs to say WHERE it
    # loses the thread rather than failing silently. One line per stage, log-only, never raises.
    def _stage(name: str) -> None:
        try:
            from modules import debug_logger

            debug_logger.event(
                f"[ITEM-FLOW] {name} state={get_game_state_symbol()!r} item={item.name}",
                category="BATTLE",
            )
        except Exception:  # noqa: BLE001
            pass

    _stage("enter")
    yield from scroll_to_battle_action(1)
    # ⛔ `#26-battleitemwedge` (2026-08-26): this was ONE blind A + ONE yield, straight into
    # `scroll_to_item_in_bag` — whose first wait (`while get_game_state() != BAG_MENU: yield`,
    # menuing.py) is UNBOUNDED and presses NOTHING. A single eaten A froze batch lane L07 for
    # 3,001 frames at `BattleScript_MoveEnd` ([ITEM-FLOW] logged `opened-bag` then silence) until
    # KI-47 netted it and the derail cascade burned to Manual. Press, VERIFY the bag actually
    # opened, re-press bounded; if it still does not open, log the stage and RETURN — the strategy
    # re-decides next pass, and a re-decided turn beats a wedge. (The deeper item-flow
    # reliability work stays `#24-battleitems`; this closes only the HANG.)
    _bag_open = False
    for _attempt in range(3):
        context.emulator.press_button("A")
        for _ in range(30):
            yield
            if get_game_state() == GameState.BAG_MENU:
                _bag_open = True
                break
        if _bag_open:
            break
        _stage(f"bag-not-open-yet (attempt {_attempt + 1}/3)")
    if not _bag_open:
        _stage("bag-did-not-open after 3 bounded attempts — returning; the strategy will re-decide")
        return
    _stage("opened-bag")
    yield from scroll_to_item_in_bag(item)
    _stage("scrolled-to-item")
    context.emulator.press_button("A")
    for _ in range(4 if context.rom.is_rse else 5):
        yield
    context.emulator.press_button("A")
    yield
    _stage("confirmed-item")
    if target_index is not None:
        # ‼‼ INDEX-SPACE BUG (`#24-battleitems`, 2026-08-09) — THE KI-34 SHAPE, AGAIN.
        # This used to feed `map_battle_party_index(target_index)` — a BATTLE-order index — into
        # `scroll_to_party_menu_index`, which drives the PARTY MENU cursor. Those two spaces are
        # not the same, and KI-34 is the entry that documents exactly this class of bug
        # ("prove two integers share a coordinate system before comparing them").
        # Measured: the one item use that WORKED logged `target=0->0` (the spaces happened to
        # agree, hiding the bug); the four that silently did nothing logged `target=0->1` for the
        # very same Blaziken, so the cursor was sent to the wrong entry and the use was cancelled.
        # The menu is driven in PARTY order, so pass the party index straight through. Both
        # numbers stay in the log so a regression here is one grep away.
        in_battle_index = battle_state.map_battle_party_index(target_index)
        _stage(f"party-menu target={target_index} (battle-order would be {in_battle_index})")
        yield from scroll_to_party_menu_index(target_index)
        context.emulator.press_button("A")
        yield
        _stage("target-chosen")
        while get_game_state_symbol() != "BATTLEMAINCB2":
            context.emulator.press_button("B")
            yield
        _stage("returned-to-battle")


@debug.track
def battle_action_use_pokeblock(poke_block_index: int):
    yield from scroll_to_battle_action(1)
    while get_game_state_symbol() == "BATTLEMAINCB2":
        context.emulator.press_button("A")
        yield
    while get_game_state_symbol() not in ("CB2_POKEBLOCKMENU", "SUB_810B674"):
        yield
    for _ in range(22):
        yield

    if len(get_pokeblocks()) <= poke_block_index:
        raise RuntimeError(
            f"Cannot use Pokéblock with index '{poke_block_index}' because the Pokéblock Case only contains {len(get_pokeblocks())} blocks."
        )

    def _get_pokeblock_scroll_position() -> int:
        if context.rom.is_rs:
            data = read_symbol("gUnknown_02039248")
            position_offset = data[0]
            scroll_offset = data[1]
        else:
            data = read_symbol("sSavedPokeblockData")
            position_offset = unpack_uint16(data[4:6])
            scroll_offset = unpack_uint16(data[6:8])
        return position_offset + scroll_offset

    while _get_pokeblock_scroll_position() != poke_block_index:
        if _get_pokeblock_scroll_position() < poke_block_index:
            context.emulator.press_button("Down")
        else:
            context.emulator.press_button("Up")
        yield
        yield

    while get_game_state_symbol() in ("CB2_POKEBLOCKMENU", "SUB_810B674"):
        context.emulator.press_button("A")
        yield
    while get_game_state_symbol() != "BATTLEMAINCB2":
        context.emulator.press_button("B")
        yield
    while get_battle_controller_callback(0) == "CompleteWhenChosePokeblock":
        yield
    yield


@debug.track
def battle_action_use_move(
    action: TurnAction, battler_index: int, move_index: int, battle_state: BattleState
) -> Generator:
    if context.rom.is_rs:
        yield

    # Choose the 'Fight' option.
    if get_battle_controller_callback(battler_index) not in ("HandleInputChooseMove", "HandleAction_ChooseMove"):
        yield from scroll_to_battle_action(0)
        yield
        context.emulator.press_button("A")
    for _ in range(6 if context.rom.is_rse else 8):
        yield

    # It's possible the game does not actually offer the move list at this point, for example
    # if the Pokémon is completely out of PP. In that case we only get a message saying that
    # Struggle is being used. So we just want to confirm that message and then stop the further
    # execution of this function.
    if get_battle_controller_callback(battler_index) not in ("HandleInputChooseMove", "HandleAction_ChooseMove"):
        while get_main_battle_callback() in (
            "HandleTurnActionSelectionState",
            "sub_8012324",
        ) and get_battle_controller_callback(battler_index) not in ("HandleInputChooseMove", "HandleAction_ChooseMove"):
            context.emulator.press_button("A")
            yield
        return

    # Select move and target
    yield from scroll_to_move(move_index, battler_index > 1)
    while get_battle_controller_callback(battler_index) in ("HandleInputChooseMove", "HandleAction_ChooseMove"):
        context.emulator.press_button("A")
        yield
    if action is TurnAction.UseMove:
        target_index = 1
        if battle_state.opponent.left_battler is None:
            # ⛔⛔ `KI-90`. This branch used to be an unconditional `raise`, and it was UNRECOVERABLE:
            # `handle_battle` is only reached from `BattleListener`, a SIBLING controller, so EVERY
            # exception from here — `BotModeError` included — unwinds to `modules/main.py:151-158`,
            # sets Manual, and the run HANGS with nothing driving the battle. MEASURED 2026-09-05: the
            # first §Ch23 chain drive died exactly this way at f66693 and hung until the watchdog.
            #
            # ⭐ THE LEFT SLOT BEING ABSENT IS NORMAL, NOT AN ERROR. `gAbsentBattlerFlags` bit 1 can
            # only be set in a DOUBLE battle (`HasNoMonsToSwitch`, `src/battle_util.c:2271`), and it
            # means that trainer is out of switchable Pokémon — a PERSISTENT state for the rest of the
            # fight. Both the game and this very module already say what to do about it:
            #   * `src/battle_controller_player.c:535-536` defaults the cursor to OPPONENT_RIGHT;
            #   * `battle_state.active_battler` (`battle_state.py:418-429`) documents the identical
            #     rule — *"in double battles it will return the left side, unless that is absent in
            #     which case it will return the right side."*
            # ⇒ this is not new policy; it makes the checkpoint agree with its own module's selector.
            #
            # ‼ WHY NOT SIMPLY DELETE THE RAISE: `target_index` would stay 1, and the loop below
            # presses "Down" until the cursor REACHES it — but the cursor can never rest on an absent
            # slot, so it would press Down for ever. That converts a loud failure into a SILENT hang,
            # which is strictly worse. The re-aim is the fix; deleting is not.
            if battle_state.opponent.right_battler is None:
                # Both slots absent. Believed unreachable (the battle should already be over), so this
                # stays a raise rather than a guess. ⚠ It is still a hang if it ever fires — the
                # sibling-controller problem above is NOT solved here, only made unreachable on the
                # path that actually occurs. ‼ The wording deliberately avoids the substring gate #38
                # uses as a failure marker, so a future both-absent arm cannot false-fail.
                raise RuntimeError("Neither opponent slot is occupied, so there is nothing to target.")
            target_index = 3
    elif action is TurnAction.UseMoveAgainstRightSideOpponent:
        target_index = 3
        if battle_state.opponent.right_battler is None:
            raise RuntimeError("Cannot attack the right-side opponent Pokémon because there isn't one.")
    elif action is TurnAction.UseMoveAgainstPartner:
        target_index = 0 if battler_index == 2 else 2
        if (battler_index == 0 and battle_state.own_side.right_battler is None) or (
            battler_index == 2 and battle_state.own_side.left_battler is None
        ):
            raise RuntimeError("Cannot attack the partnering Pokémon because there isn't one.")
    else:
        target_index = 1
    while get_battle_controller_callback(battler_index) == "HandleInputChooseTarget":
        current_target = unpack_uint32(read_symbol("gMultiUsePlayerCursor"))
        if current_target == target_index:
            context.emulator.press_button("A")
            yield
        else:
            context.emulator.press_button("Down")
            yield
