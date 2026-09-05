"""§Ch24 — THE POKÉMON LEAGUE. The Elite Four gauntlet, and the healing that makes it survivable.

⛔⛔ WHAT MAKES THIS CHAPTER DIFFERENT FROM EVERY CHAPTER BEFORE IT (user directive 2026-09-04):
**five consecutive fights, ~25 opposing Pokémon, no nurse, and no way back.** Every backward warp in
the League interior sits on an `MB_NORMAL` tile, and all three warp paths in
`src/field_control_avatar.c` reject `MB_NORMAL` (step-on `:155`, arrow `:164`, door `:170`) — so
those warps are **destination-only and never fire.** ⇒ the moment the bot steps on lobby tile
(9,1) it is committed to all five battles or a white-out.
‼ A white-out is not a softlock — `EventScript_WhiteOut` calls `ResetEliteFour`, clearing all four
`FLAG_DEFEATED_ELITE_4_*` and `VAR_ELITE_4_STATE` — but it **forfeits the whole gauntlet and half the
money.** ⇒ §Ch24 is ALL-OR-NOTHING; there is no resumable mid-gauntlet state to checkpoint.

**THIS FILE'S FIRST JOB IS `heal_party_from_bag` (`#24-e4healing`), AND IT IS A SURVIVAL MECHANISM.**
§Ch23 leg 11 bought Hyper Potion ×30 / Full Restore ×3 / Full Heal ×8 / Revive ×3 — but
`modules/story/battle_items.py:85` filters on `param > 0`, and Full Heal / Revive / Antidote all
carry `parameter == 0`, so **11 of those 44 items were unusable by any code path we had.** Without
this function the bot cannot revive anything, cannot cure a status, and cannot top up between rooms.

⭐ THE DECISION LAYER IS SOMEWHERE ELSE ON PURPOSE. `modules/story/overworld_items.py` is a PURE
module (`plan_healing`) proven exhaustively by gate #36 `repro_overworld_items.py` without a ROM —
including a fault test that broke it FIVE ways — and the 5th arm exists because a LIVE DRIVE, not the gate, caught it. This file only DRIVES the plan. Keeping the two apart
is what let the policy be proven correct before a single button was pressed.

✅✅ **DRIVEN LIVE AND PASSING (2026-09-04, `--driver ch24heal`, `ACCEPTANCE: PASS`).** From a staged
party of *two fainted, one FROZEN and two badly hurt*, seven planned actions took it to
**147/147 · 48/48 · 139/139 · 226/226 · 144/144 · 103/103**, `heal_ready=True`, `whiteouts=0`. The
`POKEBOT_CH24_FAULT_NOHEAL=1` arm correctly prints `ACCEPTANCE: FAIL`.
‼ Every menu fact below is decomp-cited AND cross-checked against our own
`modules/data/symbols/pokeemerald.sym` — and now also OBSERVED, which is what the standing project
rule actually requires before code depends on it.

⛔⛔ TWO BUGS THE LIVE DRIVE CAUGHT THAT NO GATE DID, BOTH THE SAME SHAPE — *reading one field as if
it described itself*:
  1. **`parameter` is a UNION TYPE.** Filtering healers on `parameter > 0` selected **Repel**, whose
     parameter is **100 STEPS**, and the leg died at a party menu a no-target item never opens.
  2. **`field_use` is an ENUM, not a string.** `field_use == "healing"` is ALWAYS False
     (`modules/items.py:92`), so the allowlist came back EMPTY — and it **failed silently**, because
     the revive and status passes do not consult it. The run looked *nearly* right.
⇒ ⭐ **ASK WHAT A FIELD MEANS BEFORE TRUSTING WHAT IT SAYS**, and make an empty allowlist RAISE
rather than quietly plan nothing (it does now).
"""

from typing import Generator

from modules.context import context
from modules.items import Item, ItemFieldUse, get_item_bag, get_item_by_name
from modules.memory import GameState, get_game_state, read_symbol
from modules.menuing import StartMenuNavigator, is_fade_active
from modules.modes._interface import BotModeError
from modules.modes.util.items import scroll_to_item_in_bag
from modules.modes.util.sleep import wait_for_n_frames
from modules.modes.util.tasks_scripts import wait_for_task_to_start_and_finish
from modules.pokemon_party import get_party, get_party_size
from modules.story.early_game import wait_until_truly_controllable
from modules.story.overworld_items import Target, plan_healing, party_is_gauntlet_ready


def _take(report: dict, reading: str) -> None:
    """Record that a reading actually happened. ⛔ A grade must enumerate what OCCURRED."""
    report.setdefault("readings", set()).add(reading)
from modules.tasks import task_is_active

#: Frames to spend on one item use before giving up. A bound, not a preference — a menu that never
#: reaches the next state is a hung run, and this one runs where there is no escape.
ONE_USE_BUDGET = 900

#: ⛔ THE TASK THE PARTY MENU RUNS UNDER while asking "Use on which POKéMON?".
#: `CB2_ShowPartyMenuForItemUse` (`src/party_menu.c:4229-4272`) sets `sPartyMenuInternal->task` to
#: this, and `src/party_menu.c:505,663` create it. ⭐ This is the state our code had never driven.
CHOOSE_MON_TASK = "Task_HandleChooseMonInput"

#: The bag's context menu. Medicine has FOUR actions (USE/GIVE/TOSS/CANCEL — `src/item_menu.c:286`),
#: and `:1683-1688` picks the MultipleRows task when there are more than two. ⭐ The cursor starts on
#: index 0 = `ACTION_USE`, so a plain A selects "Use" with no navigation.
ITEM_CONTEXT_TASK = "Task_ItemContext_MultipleRows"


def _party_snapshot() -> "list[Target]":
    """Read the party into the PURE policy's primitives. ⛔ Read the game; never assume."""
    out: "list[Target]" = []
    for i, mon in enumerate(get_party()):
        if mon is None or getattr(mon, "species", None) is None:
            continue
        status = getattr(mon, "status_condition", None)
        name = getattr(status, "name", None) if status is not None else None
        if name in ("Healthy", "NONE", "None"):
            name = None
        out.append(Target(i, mon.species.name, mon.level, mon.current_hp, mon.total_hp, name))
    return out


def _slot_cursor() -> int:
    """Which party slot the menu cursor is on.

    ⭐ `gPartyMenu` offset 9 is `slotId` — derived from `include/party_menu.h` (exitCallback 4 +
    task 4 + the menuType/layout bitfield byte = 8, then `s8 slotId`). This is the same read
    `apply_rare_candy` already relies on, so it is a PROVEN offset, not a new one.
    """
    if context.rom.is_rs:
        return context.emulator.read_bytes(0x0202002F + get_party_size() * 136 + 3, length=1)[0]
    return read_symbol("gPartyMenu", offset=9, size=1)[0]


def use_item_on_party_member(item: Item, party_index: int) -> Generator:
    """Use one healing item on one party member, from the overworld.

    THE CHAIN, every step decomp-cited:
      bag open → `scroll_to_item_in_bag` (⚠ it does NOT press A) → `Task_ItemContext_MultipleRows`
      + A selects USE (`src/item_menu.c:267,286,1683`) → `ItemMenu_UseOutOfBattle` (`:1785`) →
      `ItemUseOutOfBattle_Medicine` (`src/item_use.c:742-745`) → `CB2_ShowPartyMenuForItemUse`
      (`src/party_menu.c:4229`) → **`Task_HandleChooseMonInput`** → D-pad to the slot → A →
      `ItemUseCB_Medicine` (`:4416`) → `Task_ClosePartyMenuAfterText` (`:4472`) → **the BAG**.

    ⛔⛔ YOU LAND BACK IN THE BAG, NOT THE OVERWORLD (`gPartyMenu.exitCallback = CB2_ReturnToBagMenu`,
    `src/party_menu.c:4230`) — and that is true of success, of a refusal, AND of pressing B. So
    "we are done" is `GameState.BAG_MENU`, never the overworld.
    ⚠ AND IT IS NOT `Task_DisplayHPRestoredMessage`: a Full Restore on a full-HP but STATUSED mon
    succeeds with **no HP-bar animation at all** (`src/party_menu.c:4410-4414,4443-4448`), and that
    symbol appears TWICE in `pokeemerald.sym`, so `task_is_active` on it cannot tell the battle copy
    from the field copy. Two independent reasons not to gate on it.
    """
    if get_item_bag().quantity_of(item) <= 0:
        raise BotModeError(f"§Ch24: asked to use {item.name} but the bag holds none.")

    if get_game_state() is not GameState.BAG_MENU:
        yield from StartMenuNavigator("BAG").step()
    yield from scroll_to_item_in_bag(item)

    # ---- open the context menu and take "Use" (cursor already sits on it) -------------------------
    yield from wait_for_task_to_start_and_finish(ITEM_CONTEXT_TASK, "A")

    # ---- the party menu. ⛔ THE STATE NOTHING IN THIS TREE HAD DRIVEN BEFORE ----------------------
    opened = False
    for _ in range(240):
        if task_is_active(CHOOSE_MON_TASK):
            opened = True
            break
        yield
    if not opened:
        raise BotModeError(
            f"§Ch24: used {item.name} but `{CHOOSE_MON_TASK}` never became active, so the "
            f'"Use on which POKéMON?" menu never opened. ⛔ Check the item is really '
            f"`apply_to_party_member` in items.json — a no-target item (Repel) never gets here."
        )

    # ---- walk the cursor to the target slot, bounded ---------------------------------------------
    for _ in range(60):
        cursor = _slot_cursor()
        if cursor == party_index:
            break
        context.emulator.press_button("Down" if cursor < party_index else "Up")
        yield
    else:
        raise BotModeError(
            f"§Ch24: could not move the party cursor to slot {party_index} in 60 presses "
            f"(it sits at {_slot_cursor()}). ⛔ Refusing to press A on the wrong Pokémon — using a "
            f"scarce Revive on the wrong member is worse than not using it."
        )

    context.emulator.press_button("A")
    yield

    # ---- wait to land back in the BAG (success, refusal and cancel all go there) ------------------
    for _ in range(ONE_USE_BUDGET):
        if get_game_state() is GameState.BAG_MENU and not is_fade_active():
            break
        context.emulator.press_button("A")   # advances the "restored HP" / "won't have any effect" text
        yield from wait_for_n_frames(4)
    else:
        raise BotModeError(
            f"§Ch24: after using {item.name} on slot {party_index} the game never returned to the "
            f"bag within {ONE_USE_BUDGET} frames."
        )


def heal_party_from_bag(report=None, *, max_actions: int | None = None) -> Generator:
    """`#24-e4healing` — bring the party to fighting shape using the bag, outside battle.

    ⛔ GRADES THE CONSEQUENCE, NOT THE CALL. Every action's effect is re-read from the party
    afterwards; "the menu closed" proves nothing. This is the leg-11 lesson applied one layer up —
    *"`buy_in_shop` returned" is not "the items are in the bag"*, and here *"the item was used" is
    not "the Pokémon is alive"*.

    ⭐ A NO-OP IS NOT AN ERROR. `plan_healing` returns an empty list for a healthy party, and the
    caller must treat that as success. It is the common case between easy rooms.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())

    parameters = {slot.item.name: getattr(slot.item, "parameter", 0) for slot in get_item_bag().items}
    bag = {slot.item.name: slot.quantity for slot in get_item_bag().items}
    # ⛔⛔ DERIVE WHAT COUNTS AS MEDICINE FROM THE ITEM DATA, NEVER FROM `parameter`.
    # MEASURED 2026-09-04 on the first live drive: filtering healers on `parameter > 0` selected
    # **Repel**, whose parameter is **100** — one hundred STEPS, not HP — and the leg died waiting
    # for a party menu that a no-target item never opens. ⇒ `parameter` is a UNION TYPE whose
    # meaning depends on the item, so the KIND has to come from somewhere else.
    # ‼‼ COMPARE THE ENUM, NOT A STRING. `Item.field_use` is an `ItemFieldUse` enum
    # (`modules/items.py:92-106`), so `field_use == "healing"` is ALWAYS False and the allowlist
    # comes back EMPTY. MEASURED 2026-09-04 on the second live drive, and it FAILED SILENTLY: the
    # revive and status passes do not consult the allowlist, so they still worked and only the HP
    # top-ups vanished. ⇒ the run looked *nearly* right, which is the worst way to be wrong.
    # ⭐ `ItemFieldUse.__str__` returns the value, so `str(...) == "healing"` also works — but
    # comparing the member itself is what makes a typo an AttributeError instead of a silent False.
    healing = {slot.item.name for slot in get_item_bag().items
               if slot.item.field_use is ItemFieldUse.Healing}
    # ⛔ AN EMPTY ALLOWLIST IS A BUG, NOT A STATE. It silently removed every HP top-up once.
    if not healing and any(q > 0 for q in bag.values()):
        raise BotModeError(
            f"§Ch24: the healing-item allowlist came back EMPTY while the bag holds "
            f"{sorted(n for n, q in bag.items() if q > 0)}. ⛔ That means  is not being "
            f"read correctly (it is an  ENUM, not a string) — and an empty allowlist "
            f"does not fail, it just silently plans no HP healing at all."
        )
    before = _party_snapshot()
    report["heal_before"] = [(t.name, t.current_hp, t.total_hp, t.status) for t in before]
    report["healing_items_seen"] = sorted(healing)

    kwargs = {} if max_actions is None else {"max_actions": max_actions}
    plan = plan_healing(before, bag, parameters, healing_items=healing, **kwargs)
    report["heal_plan"] = [(a.party_index, a.item_name, a.reason) for a in plan]
    if not plan:
        report["heal_actions"] = 0
        report["heal_ready"] = party_is_gauntlet_ready(before)
        return

    done = 0
    for action in plan:
        item = get_item_by_name(action.item_name)
        target_before = _party_snapshot()[action.party_index]
        yield from use_item_on_party_member(item, action.party_index)
        yield from wait_for_n_frames(8)
        target_after = _party_snapshot()[action.party_index]

        # ⛔ DID IT ACTUALLY DO ANYTHING? A refused use does NOT consume the item
        # (`RemoveBagItem` sits only in the success branch, `src/party_menu.c:4419-4435`), so a
        # no-op here means the PLAN was wrong — which is a policy bug worth failing loudly on,
        # not a hiccup to retry.
        changed = (
            target_after.current_hp > target_before.current_hp
            or (target_before.status is not None and target_after.status is None)
            or (target_before.fainted and not target_after.fainted)
        )
        if not changed:
            raise BotModeError(
                f"§Ch24: used {action.item_name} on {target_before.name} (slot "
                f"{action.party_index}) and NOTHING CHANGED — {target_before.current_hp}/"
                f"{target_before.total_hp} status={target_before.status} before, "
                f"{target_after.current_hp}/{target_after.total_hp} status={target_after.status} "
                f"after. ⛔ The game refuses a no-op without consuming the item, so this means the "
                f"PLAN was wrong ({action.reason}). Failing loudly rather than looping."
            )
        done += 1

    # ---- back to the overworld ---------------------------------------------------------------------
    if get_game_state() is GameState.BAG_MENU:
        yield from wait_for_task_to_start_and_finish("Task_ShowStartMenu", "B")

    after = _party_snapshot()
    report["heal_after"] = [(t.name, t.current_hp, t.total_hp, t.status) for t in after]
    report["heal_actions"] = done
    report["heal_ready"] = party_is_gauntlet_ready(after)
    report["readings"].add("R-HEALED")


#: The input task of the "which move should be forgotten?" screen ON THE FIELD PATH.
#: ⛔ IT IS NOT THE BATTLE PATH'S TASK. `battle_move_replacing._get_evolution_task_name()` returns
#: `Task_HandleReplaceMoveInput`, which is the BATTLE screen. Teaching a TM from the BAG opens the
#: SUMMARY screen, whose task greys out HM moves — hence the name. MEASURED by dumping live tasks:
#:   ACTIVE = ['Task_HandleInputCantForgetHMsMoves', 'Task_ShowPowerAccWindow',
#:             'Task_ShowAppealJamWindow', 'Task_DuckBGMForPokemonCry']
#: ‼‼ AND IT IS **BOTH**, AT DIFFERENT PHASES — measured with a per-iteration trace, after a
#: single-instant sample misled me. `Task_HandleInputCantForgetHMsMoves` is TRANSIENT (the opening
#: "can't forget HM moves" check); the steady-state input task is `Task_HandleReplaceMoveInput`,
#: which is exactly what `battle_move_replacing._get_evolution_task_name()` returns. The trace:
#:   [0, 0, ('notask', ['Task_HandleReplaceMoveInput', 'Task_DuckBGMForPokemonCry', ...]) x22]
#: ⇒ my cursor loop kept resetting because it only recognised the transient one.
#: ⭐ **THE LESSON: A ONE-FRAME SAMPLE OF A TASK LIST IS NOT A CONTRACT.** I measured once, caught a
#: transient, generalised from it, and wrote off upstream's task name as "the battle path" when it
#: was right all along. Watch a state OVER TIME before deciding what it is.
FORGET_MOVE_TASKS = ("Task_HandleReplaceMoveInput", "Task_HandleInputCantForgetHMsMoves")

#: Consecutive frames the forget-move cursor must report the SAME value before we act on it.
FORGET_CURSOR_STABLE_READS = 3


def teach_move_from_bag(item: Item, party_index: int, move_index_to_replace: int) -> Generator:
    """Teach a TM/HM to `party_index`, replacing EXACTLY `move_index_to_replace`.

    ⛔⛔ WHY THIS EXISTS INSTEAD OF `modules/modes/util/items.py::teach_hm_or_tm`.
    That helper is used by §Ch23 leg 1 and works there, but it has a MEASURED defect that only bites
    when the move to replace is not index 0. Its A-mashing loop runs until it sees
    `Task_DuckBGMForPokemonCry`, and **the move-selection screen can appear first** — so the next
    blind `press A` CONFIRMS WHATEVER THE CURSOR IS ON, which is the default, **index 0**. Its own
    cursor navigation (`for _ in range(move_index_to_replace): press Down`) then never runs.
    ‼ A per-iteration trace proved it: four teaches produced only TWO traces —
        target=3 reads=[0,0,0,1,1,2,2,3,3,3]   (Sceptile — steered, correct)
        target=0 reads=[0,0,0]                 (Swellow  — correct)
        (Mightyena and Zigzagoon: NO TRACE — the navigation block never executed)
    ⇒ Mightyena wanted index 0 and got index 0, so it **looked** correct. It was luck. Zigzagoon
    wanted index 1, got 0, and lost **Tackle** instead of Growl.
    ⭐ **A passing result from a code path that never ran is the most convincing kind of wrong.**
    ⛔ Upstream was left ALONE deliberately: it is a shared file every chapter depends on, it has
    several unbounded loops, and a partial fix destabilised it (a drive hung). Filed rather than
    half-fixed. This routine controls the whole flow instead, the same way `use_item_on_party_member`
    does for healing.

    ⛔ AND IT NEVER PRESSES A ON AN UNKNOWN CURSOR. Gen-3 TMs are single-use; a wrong pick is
    permanent, so this refuses rather than guesses.
    """
    from modules.battle_move_replacing import _get_move_selection_cursor
    from modules.modes.util.items import scroll_to_item_in_bag

    party = get_party()
    if len(party) <= party_index or party[party_index] is None:
        raise BotModeError(f"§Ch24 teach: no party member at slot {party_index}.")
    target = party[party_index]
    if get_item_bag().quantity_of(item) <= 0:
        raise BotModeError(f"§Ch24 teach: {item.name} is not in the bag.")
    if not target.species.can_learn_tm_hm(item):
        raise BotModeError(
            f"§Ch24 teach: {target.species.name} cannot learn {item.name}. ⛔ Refusing — a "
            f"single-use TM would be wasted."
        )

    yield from StartMenuNavigator("BAG").step()
    yield from scroll_to_item_in_bag(item)

    # ---- open the context menu and take "Use" ----------------------------------------------------
    yield from wait_for_task_to_start_and_finish(ITEM_CONTEXT_TASK, "A")

    # ---- the party menu: pick the recipient, closed-loop ------------------------------------------
    # ⛔ A TM DOES NOT REACH THE PARTY MENU THE WAY A POTION DOES. `use_item_on_party_member` waits
    # on `Task_HandleChooseMonInput` and that is correct for MEDICINE, whose "Use" goes straight to
    # `CB2_ShowPartyMenuForItemUse`. A TM needs additional A-presses first, and MEASURED 2026-09-04
    # that task never became active — the leg refused (correctly) rather than pressing blind.
    # ⭐ Upstream's proven wait is the GAME STATE, not a task, so use that and accept the task as a
    # secondary signal. *Take the contract from the screen you are actually on* — third time this
    # session that copying a sibling's SHAPE was right and copying its TASK NAME was wrong.
    opened = False
    for _ in range(600):
        if get_game_state() is GameState.PARTY_MENU or task_is_active(CHOOSE_MON_TASK):
            opened = True
            break
        context.emulator.press_button("A")
        yield from wait_for_n_frames(4)
    if not opened:
        raise BotModeError(
            f"§Ch24 teach: used {item.name} but the PARTY MENU never opened "
            f"(state={get_game_state()})."
        )
    yield from wait_for_n_frames(10)
    for _ in range(60):
        cursor = _slot_cursor()
        if cursor == party_index:
            break
        context.emulator.press_button("Down" if cursor < party_index else "Up")
        yield
    else:
        raise BotModeError(f"§Ch24 teach: could not reach party slot {party_index}.")
    context.emulator.press_button("A")
    yield

    # ---- ⛔ THE FORGET-MOVE SCREEN. Advance WITHOUT mashing past it. ------------------------------
    # A-presses here are gated on the screen NOT being up yet, which is exactly the guard the
    # upstream helper lacks.
    up = False
    for _ in range(600):
        if any(task_is_active(n) for n in FORGET_MOVE_TASKS):
            up = True
            break
        if get_game_state() is GameState.BAG_MENU:
            # It learned into an EMPTY slot (or was refused) and bounced back — no choice needed.
            return
        context.emulator.press_button("A")
        yield from wait_for_n_frames(4)
    if not up:
        raise BotModeError(
            f"§Ch24 teach: none of {FORGET_MOVE_TASKS} appeared for {target.species.name}."
        )

    # ---- navigate the move cursor, closed-loop AND stable -----------------------------------------
    stable, landed = 0, False
    for _ in range(240):
        if not any(task_is_active(n) for n in FORGET_MOVE_TASKS):
            stable = 0
            yield
            continue
        cursor = _get_move_selection_cursor()
        if cursor == move_index_to_replace:
            # ‼ Require the read to HOLD. `sMonSummaryScreen` is still initialising while the screen
            # animates in — the 2026-07-25 hazard in `battle_move_replacing`, where a stale read of
            # 4 once confirmed forgetting an HM.
            stable += 1
            if stable >= FORGET_CURSOR_STABLE_READS:
                landed = True
                break
            yield
            continue
        stable = 0
        context.emulator.press_button("Down" if cursor < move_index_to_replace else "Up")
        yield
        yield
    if not landed:
        raise BotModeError(
            f"§Ch24 teach: could not settle the forget-move cursor on index "
            f"{move_index_to_replace} for {target.species.name}. ⛔ Refusing to press A on an "
            f"unknown slot — a Gen-3 TM is single-use."
        )
    context.emulator.press_button("A")
    yield

    # ---- back out ---------------------------------------------------------------------------------
    for _ in range(600):
        if get_game_state() is GameState.OVERWORLD:
            return
        if get_game_state() is GameState.BAG_MENU and not is_fade_active():
            yield from wait_for_task_to_start_and_finish("Task_ShowStartMenu", "B")
            return
        context.emulator.press_button("A")
        yield from wait_for_n_frames(4)


# ==================================================================================================
# §Ch24 PREP — FLY OFF THE PLATEAU (`#24-dexcatch` prerequisite)
# ==================================================================================================
FLY_READINGS = ("R-FLYABLE", "R-FLOWN", "R-CONTINUE")


def fly_to_destination(destination, report=None) -> Generator:
    """Fly to `destination` and PROVE we arrived.

    ⛔⛔ WHY THIS IS A LEG AND NOT A ONE-LINER. `EVER_GRANDE_CITY (18,6)` is a CLOSED PLATEAU —
    measured with `calculate_path` from that exact tile: the League door and the Victory Road exit
    landing (36 wp) are reachable and **nothing else is**; the Poké Center, the Victory Road apron,
    the southern shore and every water tile all return `PathFindingError`. ⇒ **the bot cannot walk
    to a single wild encounter**, so the user's catching / Pokédex directive and both free TM
    pickups that win Drake are all on the far side of one Fly.

    ⭐ It reuses `higher_level_actions.fly_to`, which is already guarded (BADGE06 — a documented
    FORK fix, KI-7, because the stock check was FR/LG's BADGE03 — plus the destination's own
    visited-flag and a `first_pokemon_with_move("Fly")` lookup) and already has a proven caller in
    `modules/modes/roamer_reset.py`.

    ‼ IT GRADES ARRIVAL, NOT THE MOVE. "Swellow knows Fly" is not "the bot has flown" — the leg
    asserts the destination MAP, that the party is unchanged BY PID, and that a real path exists off
    the landing tile.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    from modules.modes.util.higher_level_actions import fly_to
    from modules.memory import get_event_flag
    from modules.player import get_player_avatar

    flyer = get_party().first_pokemon_with_move("Fly")
    report["fly_knower"] = None if flyer is None else (flyer.species.name, flyer.index)
    report["badge06"] = get_event_flag("BADGE06_GET")
    report["destination_available"] = get_event_flag(destination.get_flag_name())
    if flyer is None:
        raise BotModeError(
            "§Ch24 fly: no party member knows Fly. ⛔ Teach it first (`--driver ch24fly`) — Swellow "
            "is the only member of this party that CAN learn it."
        )
    if not report["badge06"]:
        raise BotModeError("§Ch24 fly: BADGE06 (Feather) is required for the Fly field move.")
    if not report["destination_available"]:
        raise BotModeError(
            f"§Ch24 fly: {destination.name} has never been visited, so it is not on the region map."
        )
    _take(report, "R-FLYABLE")

    before = get_player_avatar()
    report["origin"] = (before.map_group_and_number, before.local_coordinates)
    party_before = [(m.species.name, hex(m.personality_value)) for m in get_party()
                    if m is not None and getattr(m, "species", None) is not None]

    # ⛔ ANTI-VACUITY: the run must END somewhere it did not START, or it cannot distinguish a
    # successful flight from doing nothing. The origin is recorded here and compared after the
    # flight (`report["moved"]`), which is the same check without needing to know the destination's
    # map id up front — the enum carries region-map COORDINATES, not a map group/number.

    yield from fly_to(destination)
    yield from wait_until_truly_controllable()

    after = get_player_avatar()
    report["arrived"] = (after.map_group_and_number, after.local_coordinates)
    report["moved"] = report["arrived"] != report["origin"]
    _take(report, "R-FLOWN")
    if not report["moved"]:
        raise BotModeError(
            f"§Ch24 fly: still at {report['origin']} after flying to {destination.name}."
        )

    # ⛔ THE PARTY MUST BE UNTOUCHED — asserted BY PID, never by count.
    party_after = [(m.species.name, hex(m.personality_value)) for m in get_party()
                   if m is not None and getattr(m, "species", None) is not None]
    report["party_pids_stable"] = party_before == party_after
    if not report["party_pids_stable"]:
        raise BotModeError(
            f"§Ch24 fly: the party changed across the flight. "
            f"before={party_before} after={party_after}"
        )

    # ⭐ AND THE BOT CAN CONTINUE — a REAL path off the landing tile, not a `controllable` flag.
    from modules.modes.util.walking import calculate_path

    here = after.local_coordinates
    probes, reachable = [(here[0], here[1] + 1), (here[0] + 1, here[1]), (here[0], here[1] - 1),
                         (here[0] - 1, here[1])], 0
    for tile in probes:
        try:
            calculate_path((after.map_group_and_number, here), (after.map_group_and_number, tile))
            reachable += 1
        except Exception:  # noqa: BLE001 — a refusal is a reading, not an error
            pass
    report["neighbours_reachable"] = reachable
    _take(report, "R-CONTINUE")
    if reachable == 0:
        raise BotModeError(
            f"§Ch24 fly: landed on {report['arrived']} but NO neighbouring tile is reachable — the "
            f"bot cannot take a step. That is a landing, not an arrival."
        )


# ==================================================================================================
# §Ch24 PREP — THE MOVESET PLAN (`#24-e4moveset`)
# ==================================================================================================
#: ⭐⭐ FOUR CHANGES THAT COST NOTHING: every TM/HM here is ALREADY IN THE BAG and no travel is
#: needed. Compatibility was read from the decomp's `src/data/pokemon/tmhm_learnsets.h` **at two
#: revisions and diffed** (the macro form and the post-`912a80e27a40` bitfield form — identical for
#: all six species) and cross-checked against our own `modules/data/species.json`.
#: ⛔ GEN-3 TMs ARE SINGLE-USE. A wrong compatibility claim destroys one permanently, which is why
#: this list is decomp-sourced rather than reasoned from types.
#:
#: ‼ AND ONE ENTRY EXISTS BECAUSE I WAS WRONG. I had recorded Sceptile as carrying "Rock Smash AND
#: Strength — two dead slots". **`Slam` is 80 BP at 75%; `Strength` is 80 BP at 100%.** ⇒ Strength is
#: Sceptile's BETTER Normal move and **Slam** is the wasted slot. A field move is not automatically
#: a dead slot — check the numbers before calling one dead.
MOVESET_PLAN = (
    # (species, item, move to LEARN, move to REPLACE, why)
    ("Sceptile", "TM40", "Aerial Ace", "Slam",
     "never-misses, and FOUR opponents run Double Team (Shiftry, Sableye, Ludicolo, Glalie) plus "
     "Sand-Attack and Swagger. Also covers Grass-resists-Grass: Leaf Blade does 30%/25% to "
     "Cacturne/Shiftry where Aerial Ace does 59%/47%"),
    ("Swellow", "TM42", "Facade", "Peck",
     "Peck is 35 BP, the worst move on the team. Facade is 70 with STAB — and Wallace's Tentacruel "
     "AND Milotic both carry Toxic, after which Guts (x1.5) and Facade's doubling BOTH apply"),
    ("Mightyena", "HM04", "Strength", "Tackle",
     "35 BP -> 80 BP at 100%. HMs are REUSABLE, so Sceptile keeps its own copy"),
    ("Zigzagoon", "HM06", "Rock Smash", "Growl",
     "Growl is worthless, and Victory Road needs Rock Smash kept in the party if Sceptile's slot is "
     "ever freed for Dragon Claw"),
)

#: ⛔ NOT IN THE PLAN, ON PURPOSE — recorded so a future reader does not 'helpfully' add them:
#: TM34 Shock Wave (only Castform L36 and Zigzagoon L19 can learn it; Castform's does 21% to
#: Gyarados while Gyarados's Surf does 106% back), TM03 Water Pulse (Wailord already has Surf 95 and
#: Water Spout 150), TM39 Rock Tomb (20-31% at 80% accuracy).
#: ⛔ AND THREE ARE UNUSABLE BY ANYONE HERE: TM04 Calm Mind, TM08 Bulk Up, TM50 Overheat.

MOVESET_READINGS = ("R-PLAN", "R-TAUGHT", "R-VERIFIED")

#: ⭐⭐ THE TRAVEL PLAN — **FLY IS NOT AN OPTIMISATION HERE, IT IS THE ONLY WAY OFF THE PLATEAU.**
#: MEASURED 2026-09-05 from `post_moveset.ss1` at EVER_GRANDE_CITY (18,6), with `calculate_path`:
#:     League door apron (18,6)          OK 0 wp
#:     VictoryRoad exit landing (18,28)  OK 36 wp
#:     Poke Center door (27,48)          ⛔ PathFindingError
#:     VR apron (18,42)                  ⛔ PathFindingError
#:     southern shore (18,55) / water (18,60)  ⛔ PathFindingError
#: ⇒ **the bot cannot walk to a single wild encounter** — no grass, no water access. Everything the
#: user's catching/Pokédex directive needs, and both free TM pickups that win Drake (TM13 Ice Beam,
#: TM02 Dragon Claw), are on the far side of this.
#:
#: ⭐ SWELLOW IS THE ONLY MEMBER THAT CAN LEARN FLY — measured with `species.can_learn_tm_hm(HM02)`:
#: Sceptile False · Zigzagoon False · Swellow **True** · Wailord False · Mightyena False ·
#: Castform False. Badge gate is `BADGE03`; we hold all eight.
#:
#: ⛔ AND IT REPLACES **WING ATTACK**, WHICH IS STRICTLY DOMINATED. Swellow now knows Facade (Normal
#: STAB), Wing Attack (Flying 60/100%), Aerial Ace (Flying 60, NEVER MISSES) and Quick Attack
#: (priority). Wing Attack and Aerial Ace are the same type and power, and Aerial Ace cannot miss —
#: so Wing Attack contributes nothing that Aerial Ace does not do better. ‼ Fly itself is a 2-turn
#: move in battle and is NOT intended as an attack; it is bought for the overworld.
TRAVEL_PLAN = (
    ("Swellow", "HM02", "Fly", "Wing Attack",
     "Fly is the ONLY exit from the Ever Grande plateau (measured: every non-League tile is "
     "PathFindingError from (18,6)). Wing Attack is strictly dominated by the Aerial Ace Swellow "
     "already knows — same type, same 60 power, and Aerial Ace never misses"),
)


def _find_slot(species: str) -> "int | None":
    """Party index of `species`, or None if absent.

    ⛔ DERIVED AT RUN TIME, never hardcoded — a caught Pokémon or a faint-swap reorders the party,
    and this project has a filed bug (`#24-ch23wally`) from code that assumed slot order.
    ‼ RETURNS None RATHER THAN RAISING, deliberately: the caller treats "not in the party" as one
    REFUSAL REASON among several and reports them together. Raising here would have forced a
    `try/except` around it, and a swallowed exception in `modules/story` is exactly the debt
    `repro_no_silent_except.py` ratchets (it caught this at 124/123). ⇒ **when a caller only wants
    to know "is it there?", answering with an exception manufactures a swallow.**
    """
    for i, mon in enumerate(get_party()):
        if mon is not None and getattr(mon, "species", None) is not None and mon.species.name == species:
            return i
    return None


def _moves_of(index: int) -> "list[str]":
    mon = get_party()[index]
    return [m.move.name for m in mon.moves if m is not None and m.move is not None]


def apply_moveset_plan(report=None, plan=MOVESET_PLAN) -> Generator:
    """Teach the free in-bag moves for the Elite Four.

    ⛔ EVERY STEP IS DERIVED AND ASSERTED, NOT ASSUMED:
      * the party SLOT comes from the species name at run time;
      * the move INDEX to replace comes from that Pokémon's CURRENT moves;
      * a change is SKIPPED (not failed) if it is already applied — this leg must be re-runnable;
      * afterwards the Pokémon is re-read and must KNOW the new move and have LOST the old one.
    ‼ "the teach helper returned" is not "the move is known" — the leg-11 lesson, one layer up.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())


    bag = {slot.item.name: slot.quantity for slot in get_item_bag().tms_hms}
    report["tm_pocket_before"] = dict(bag)
    todo, skipped, missing = [], [], []
    for species, item_name, learn, replace, why in plan:
        idx = _find_slot(species)
        if idx is None:
            missing.append(
                f"{species} is not in the party "
                f"({[m.species.name for m in get_party() if m and m.species]})"
            )
            continue
        have = _moves_of(idx)
        if learn in have:
            skipped.append(f"{species} already knows {learn}")
            continue
        if replace not in have:
            # ⛔ REFUSE rather than replace something else. Burning a single-use TM over the wrong
            # move is unrecoverable, and "the slot I expected" is exactly the assumption that fails.
            missing.append(f"{species} does not know {replace} (has {have}) — refusing to guess")
            continue
        if bag.get(item_name, 0) <= 0:
            missing.append(f"{item_name} not in the TM/HM pocket")
            continue
        todo.append((species, idx, item_name, learn, replace, have.index(replace), why))

    report["plan_todo"] = [(s, i, it, l, r) for s, i, it, l, r, _, _ in todo]
    report["plan_skipped"] = skipped
    report["plan_refused"] = missing
    _take(report, "R-PLAN")
    if missing:
        raise BotModeError(
            f"§Ch24 moveset: refusing to proceed — {missing}. ⛔ Gen-3 TMs are SINGLE-USE; a wrong "
            f"target is permanent. Fix the plan or the party, do not let this pass."
        )
    if not todo:
        report["taught"] = []
        _take(report, "R-TAUGHT")
        _take(report, "R-VERIFIED")
        return

    taught = []
    for species, idx, item_name, learn, replace, move_index, why in todo:
        before = _moves_of(idx)
        yield from teach_move_from_bag(get_item_by_name(item_name), idx, move_index)
        yield from wait_for_n_frames(10)
        after = _moves_of(idx)
        # ⛔ GRADE THE CONSEQUENCE.
        if learn not in after:
            raise BotModeError(
                f"§Ch24 moveset: taught {learn} to {species} (slot {idx}, replacing {replace} at "
                f"index {move_index}) and it does NOT know it. before={before} after={after}. "
                f"⛔ A single-use TM may have been consumed for nothing."
            )
        if replace in after:
            raise BotModeError(
                f"§Ch24 moveset: {species} learned {learn} but STILL knows {replace} — the wrong "
                f"slot was replaced. before={before} after={after}."
            )
        taught.append((species, learn, replace, before, after))
    report["taught"] = taught
    _take(report, "R-TAUGHT")

    # ---- final re-read of the whole party ---------------------------------------------------------
    final = {}
    for species, _, _, learn, replace, _, _ in todo:
        idx = _find_slot(species)
        if idx is None:
            raise BotModeError(
                f"§Ch24 moveset: {species} vanished from the party between teaching and the final "
                f"re-read. ⛔ Something reordered or removed it mid-leg."
            )
        final[species] = _moves_of(idx)
    report["final_movesets"] = final
    report["tm_pocket_after"] = {slot.item.name: slot.quantity for slot in get_item_bag().tms_hms}
    _take(report, "R-VERIFIED")
