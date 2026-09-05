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
from modules.story.overworld_items import Target, plan_healing, party_is_gauntlet_ready
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
