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
from modules.pokemon_party import get_party, get_party_size


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
    unrecognised = 0

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

                yield from scroll_to_battle_action(2)
                # JP roms need a little delay
                for _ in range(5):
                    yield
                context.emulator.press_button("A")
                yield from scroll_to_party_menu_index(in_battle_index)
                while get_game_state() == GameState.PARTY_MENU:
                    context.emulator.press_button("A")
                    yield

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
            raise RuntimeError("Cannot attack the left-side opponent Pokémon because there isn't one.")
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
